"""Command-line entry points for portfolio automation."""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .github_api import GitHubApi, GitHubApiError
from .idempotency import (
    CONTRACT_VERSION,
    DeliveryIdentity,
    deterministic_branch,
    dispatch_marker,
    fallback_delivery_id,
    parse_dispatch_markers,
    stable_task_id,
)
from .issue_sync import (
    MANAGED_LABEL,
    SOURCE_LABEL,
    SOURCE_REPO,
    TARGET_REPO,
    MirrorLocator,
    SyncExecutor,
    SyncPlanner,
)
from .models import Issue
from .projects_sync import sync_projects_phase2
from .routing import route_decision
from .validation import validate_dispatch

LOGGER = logging.getLogger("portfolio-tasks")
APPROVAL_LABEL = "status:approved"


def _api(dry_run: bool = False) -> GitHubApi:
    mock = os.getenv("GH_MOCK_DIR")
    return GitHubApi(
        os.getenv("GH_TOKEN"),
        float(os.getenv("API_TIMEOUT", "20")),
        mock_dir=Path(mock) if mock else None,
        dry_run=dry_run,
    )


def sync() -> int:
    dry_run = os.getenv("DRY_RUN", "true") == "true"
    summary_path = Path(os.getenv("GITHUB_STEP_SUMMARY", os.devnull))
    errors: list[str] = []
    failures: list[str] = []
    action = "no-op"
    target: Issue | None = None
    source: Issue | None = None
    number = os.getenv("SOURCE_ISSUE_NUMBER", "")
    event_path = Path(os.getenv("GITHUB_EVENT_PATH", ""))
    try:
        event = json.loads(event_path.read_text()) if event_path.is_file() else {}
        if os.getenv("GITHUB_EVENT_NAME") == "issues":
            number = str(event.get("issue", {}).get("number", ""))
        if not number.isdigit():
            errors.append("source_issue_number must be numeric")
            raise ValueError
        api = _api(dry_run)
        source = Issue.from_json(api.request("GET", f"repos/{SOURCE_REPO}/issues/{number}"))
        if source.number != int(number):
            errors.append("Source issue number mismatch")
        if source.is_pull_request:
            errors.append("Pull requests are not synchronized")
        if not source.title:
            errors.append("Issue title is required")
        if len(source.title) > 256:
            errors.append("Issue title exceeds 256 characters")
        if len(source.body) > 65000:
            errors.append("Issue body exceeds safe synchronization length")
        if errors:
            raise ValueError
        try:
            targets = api.request("GET", f"repos/{TARGET_REPO}/issues?state=all&per_page=100")
        except GitHubApiError:
            failures.append("Could not search target issues")
            raise
        target = MirrorLocator.locate((Issue.from_json(item) for item in targets), source.number)
        removed = (
            os.getenv("GITHUB_EVENT_ACTION") == "unlabeled"
            and event.get("label", {}).get("name") == SOURCE_LABEL
        )
        plan = SyncPlanner.plan(source, target, removed)
        action = plan.action.value
        SyncExecutor(api).execute(plan)
    except ValueError:
        pass
    except GitHubApiError:
        if not failures:
            failures.append("GitHub API request failed")
    title = source.title if source else ""
    labels = source.labels if source else ()
    skipped = [
        f"{label} (optional source label skipped)" for label in labels if label != SOURCE_LABEL
    ]
    lines = [
        "## Slugger Issue Synchronization",
        f"- Source repository: `{SOURCE_REPO}`",
        f"- Source issue number: `{number}`",
        f"- Source issue title: {title}",
        f"- chatgpt-task present: `{str(SOURCE_LABEL in labels).lower()}`",
        f"- Target repository: `{TARGET_REPO}`",
        f"- Matching target issue number: `{target.number if target else 'none'}`",
        f"- Planned/completed action: `{action}`",
        f"- Dry run: `{str(dry_run).lower()}`",
        f"- Labels applied: {MANAGED_LABEL if action not in ('no-op', 'skipped', 'disable-sync') else 'none'}",
        f"- Labels skipped: {' '.join(skipped) or 'none'}",
        "- Assignees applied: none",
        "- Assignees skipped: none",
        f"- Validation errors: {' '.join(errors) or 'none'}",
        f"- API failures: {' '.join(failures) or 'none'}",
        f"- Final synchronization result: `{'failed' if errors or failures else 'success'}`",
    ]
    with summary_path.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return 1 if errors or failures else 0


def dispatch(args: argparse.Namespace) -> int:
    issue = json.loads(args.issue_json.read_text(encoding="utf-8"))
    dependencies = None
    if args.mock_open_issues:
        dependencies = set(args.mock_open_issues.read_text(encoding="utf-8").splitlines())
    result = validate_dispatch(issue, dependencies)
    print(json.dumps({"ok": result.ok, "errors": list(result.errors), "comment": result.comment}))
    return 0 if result.ok else 1


def _route_event_gate(event: dict[str, Any]) -> tuple[bool, str]:
    action = str(event.get("action") or "")
    if action == "edited":
        return False, "edited-approval-invalidated"
    if action != "labeled":
        return False, "non-approval-event"
    label = event.get("label")
    label_name = str(label.get("name") if isinstance(label, dict) else "")
    if label_name != APPROVAL_LABEL:
        return False, "non-approval-label"
    return True, ""


def _route_issue_snapshot(issue: Issue) -> tuple[Issue | None, str]:
    repository = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GH_TOKEN")
    if issue.number <= 0:
        return None, "invalid-issue"
    if not repository or not token:
        return None, "live-issue-fetch-not-configured"
    try:
        current = _api().request("GET", f"repos/{repository}/issues/{issue.number}")
    except GitHubApiError:
        return None, "live-issue-fetch-failed"
    return Issue.from_json(current), ""


def prepare_dispatch(args: argparse.Namespace) -> int:
    """Persist/reuse a durable dispatch marker for an approved issue."""
    event = json.loads(args.event_json.read_text(encoding="utf-8"))
    issue = Issue.from_json(event.get("issue", {}))
    repo = os.getenv("GITHUB_REPOSITORY", SOURCE_REPO)
    source_issue = f"{repo}#{issue.number}"
    task_id = stable_task_id(
        source_issue=source_issue, issue_title=issue.title, issue_body=issue.body
    )
    delivery_id = fallback_delivery_id(task_id)
    identity = DeliveryIdentity(
        contract_version=CONTRACT_VERSION,
        source_issue=source_issue,
        task_id=task_id,
        delivery_id=delivery_id,
        target_repository=repo,
        requested_branch=deterministic_branch(delivery_id),
    )
    existing = [
        m for m in parse_dispatch_markers(issue.body) if m.get("source_issue") == source_issue
    ]
    if existing and any(str(m.get("delivery_id")) != delivery_id for m in existing):
        raise SystemExit("conflicting dispatch marker for source issue")
    print(f"task_id={task_id}")
    print(f"delivery_id={delivery_id}")
    print(f"requested_branch={identity.requested_branch}")
    marker_path = Path(os.getenv("RUNNER_TEMP", ".")) / "dispatch-marker.md"
    marker_path.write_text(dispatch_marker(identity, "dispatching") + "\n", encoding="utf-8")
    print(f"marker_path={marker_path}")
    return 0


def route_check(args: argparse.Namespace) -> int:
    """Emit only non-sensitive routing outputs for a GitHub issue event."""
    event = json.loads(args.event_json.read_text(encoding="utf-8"))
    issue = Issue.from_json(event.get("issue", {}))
    event_allowed, gate_reason = _route_event_gate(event)
    if not event_allowed:
        print("route=false")
        print(f"reason={gate_reason}")
        print(f"issue_number={issue.number}")
        return 0
    issue_snapshot, snapshot_reason = _route_issue_snapshot(issue)
    if issue_snapshot is None:
        print("route=false")
        print(f"reason={snapshot_reason}")
        print(f"issue_number={issue.number}")
        return 0
    issue = issue_snapshot
    decision = route_decision(issue)
    print(f"route={str(decision.route).lower()}")
    print(f"reason={decision.reason}")
    print(f"issue_number={issue.number}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sync")
    commands.add_parser("sync-projects-phase2")
    validate = commands.add_parser("validate-dispatch")
    validate.add_argument("issue_json", type=Path)
    validate.add_argument("--mock-open-issues", type=Path)
    route = commands.add_parser("route-check")
    route.add_argument("event_json", type=Path)
    prepare_route = commands.add_parser("prepare-dispatch")
    prepare_route.add_argument("event_json", type=Path)
    args = parser.parse_args(argv)
    if args.command == "sync":
        return sync()
    if args.command == "sync-projects-phase2":
        return sync_projects_phase2()
    if args.command == "route-check":
        return route_check(args)
    if args.command == "prepare-dispatch":
        return prepare_dispatch(args)
    return dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
