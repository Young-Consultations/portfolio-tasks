"""Command-line entry points for portfolio automation."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Sequence

from .github_api import GitHubApi, GitHubApiError
from .issue_sync import (MANAGED_LABEL, SOURCE_LABEL, SOURCE_REPO, TARGET_REPO,
                         MirrorLocator, SyncExecutor, SyncPlanner)
from .models import Issue
from .validation import validate_dispatch

LOGGER = logging.getLogger("portfolio-tasks")


def _api(dry_run: bool = False) -> GitHubApi:
    mock = os.getenv("GH_MOCK_DIR")
    return GitHubApi(os.getenv("GH_TOKEN"), float(os.getenv("API_TIMEOUT", "20")),
                     mock_dir=Path(mock) if mock else None, dry_run=dry_run)


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
            targets = api.request(
                "GET", f"repos/{TARGET_REPO}/issues?state=all&per_page=100"
            )
        except GitHubApiError:
            failures.append("Could not search target issues")
            raise
        target = MirrorLocator.locate((Issue.from_json(item) for item in targets), source.number)
        removed = (os.getenv("GITHUB_EVENT_ACTION") == "unlabeled"
                   and event.get("label", {}).get("name") == SOURCE_LABEL)
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
    skipped = [f"{label} (optional source label skipped)" for label in labels if label != SOURCE_LABEL]
    lines = ["## Slugger Issue Synchronization", f"- Source repository: `{SOURCE_REPO}`",
             f"- Source issue number: `{number}`", f"- Source issue title: {title}",
             f"- chatgpt-task present: `{str(SOURCE_LABEL in labels).lower()}`",
             f"- Target repository: `{TARGET_REPO}`",
             f"- Matching target issue number: `{target.number if target else 'none'}`",
             f"- Planned/completed action: `{action}`", f"- Dry run: `{str(dry_run).lower()}`",
             f"- Labels applied: {MANAGED_LABEL if action not in ('no-op', 'skipped', 'disable-sync') else 'none'}",
             f"- Labels skipped: {' '.join(skipped) or 'none'}", "- Assignees applied: none",
             "- Assignees skipped: none", f"- Validation errors: {' '.join(errors) or 'none'}",
             f"- API failures: {' '.join(failures) or 'none'}",
             f"- Final synchronization result: `{'failed' if errors or failures else 'success'}`"]
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


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sync")
    validate = commands.add_parser("validate-dispatch")
    validate.add_argument("issue_json", type=Path)
    validate.add_argument("--mock-open-issues", type=Path)
    args = parser.parse_args(argv)
    return sync() if args.command == "sync" else dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
