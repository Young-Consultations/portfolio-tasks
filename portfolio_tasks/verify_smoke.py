"""Proposed one-shot v5 maintenance verification boundary; never implement."""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from portfolio_tasks.source_lifecycle import Approval, SourceRevision, canonical_task

REPO = "Young-Consultations/portfolio-tasks"
TARGET = "Young-Consultations/consulting-playbook"
OWNER = "mightyjoe909"
RELEASE = "ai-sdlc-v5.0.0"
CONTROL_SHA = "3cce887fc393fa80ed8f79308ca9b9c7241ce622"
TITLE = "[Maintenance] v5 verify-only smoke"
RESULT_STATUSES = {"verified", "rejected", "failed", "blocked", "ambiguous-rejected"}
MARKER = "<!-- ai-sdlc-v5-smoke-reservation:v1 "
BODY = "\n\n".join(
    "### " + key + "\n" + value
    for key, value in (
        ("Project", "AI-SDLC"),
        ("Priority", "P2"),
        ("Task type", "Testing"),
        ("Parallel-safe", "no"),
        ("Risk", "low"),
        ("Estimated scope", "small"),
        ("Target repository", TARGET),
        ("Execution mode", "verify"),
        ("Executor", "codex"),
        ("Dependency issue references", "None"),
        ("Sensitivity declaration", "not-sensitive"),
    )
)


def require(ok: object) -> None:
    if not ok:
        raise ValueError("v5 smoke authorization or evidence mismatch")


def issue_policy(issue: Mapping[str, Any], revision: SourceRevision) -> None:
    require(
        type(issue.get("number")) is int
        and issue["number"] > 0
        and "pull_request" not in issue
        and issue.get("state") == "open"
        and issue.get("title") == TITLE
        and issue.get("body") == BODY
        and issue.get("user", {}).get("login") == OWNER
        and issue.get("labels") == []
        and revision.source_issue == f"{REPO}#{issue['number']}"
        and revision.execution_mode == "verify"
        and revision.target_repository == TARGET
        and revision.executor == "codex"
        and revision.dependencies == ()
        and revision.sensitivity == "not-sensitive"
    )


def dispatch_policy(env: Mapping[str, str]) -> None:
    require(
        env.get("GITHUB_REPOSITORY") == REPO
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and env.get("GITHUB_ACTOR") == OWNER
        and env.get("GITHUB_TRIGGERING_ACTOR") == OWNER
        and OWNER in {item.strip() for item in env.get("APPROVERS", "").split(",")}
        and env.get("CONFIRMATION") == "verify-v5-once"
        and re.fullmatch(r"[1-9][0-9]*", env.get("ISSUE_NUMBER", ""))
        and re.fullmatch(r"[1-9][0-9]*", env.get("GITHUB_RUN_ID", ""))
        and re.fullmatch(r"task-[0-9a-f]{32}", env.get("EXPECTED_TASK_ID", ""))
        and re.fullmatch(r"[0-9a-f]{40}", env.get("EXPECTED_MAIN_SHA", ""))
        and env.get("GITHUB_SHA") == env.get("EXPECTED_MAIN_SHA")
    )


def reservation(revision: SourceRevision, run_id: str) -> str:
    require(re.fullmatch(r"[1-9][0-9]*", run_id))
    record = {
        "owner": OWNER,
        "source_issue": revision.source_issue,
        "task_id": revision.task_id,
        "mode": "verify",
        "release": RELEASE,
        "run_id": run_id,
        "attempt": "1",
    }
    return MARKER + json.dumps(record, sort_keys=True, separators=(",", ":")) + " -->"


def reservation_matches(comments: Any, revision: SourceRevision) -> bool:
    if not isinstance(comments, list):
        return False
    try:
        rows = [row for row in comments if "ai-sdlc-v5-smoke-reservation:" in row["body"]]
        if len(rows) != 1:
            return False
        row = rows[0]
        body = row["body"]
        if (
            row["user"]["login"] != "github-actions[bot]"
            or not isinstance(body, str)
            or not body.startswith(MARKER)
        ):
            return False
        record = json.loads(body[len(MARKER) : -4])
        return body == reservation(revision, record["run_id"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def prepare(
    api: Any, env: Mapping[str, str], now: datetime, schema: Mapping[str, Any]
) -> dict[str, object]:
    # Import lazily: the existing projector shares this narrow policy.
    from portfolio_tasks.terminal_projection import revision_from

    dispatch_policy(env)
    issue, comments = api.read()
    source = f"{REPO}#{env['ISSUE_NUMBER']}"
    revision = revision_from(issue, source)
    issue_policy(issue, revision)
    created = datetime.fromisoformat(issue["created_at"])
    require(timedelta(0) <= now - created <= timedelta(hours=24))
    require(issue.get("comments") == 0 and comments == [])
    require(api.api(api.path + "/events?per_page=1") == [])
    require(revision.task_id == env["EXPECTED_TASK_ID"])
    require(api.api(f"repos/{REPO}/commits/main")["sha"] == env["EXPECTED_MAIN_SHA"])
    tag = api.api(f"repos/Young-Consultations/.github/git/ref/tags/{RELEASE}")["object"]
    require(tag["type"] == "commit" and tag["sha"] == CONTROL_SHA)
    payload = canonical_task(revision, Approval(revision.task_id, OWNER, True))
    require(Draft202012Validator(schema).is_valid(payload))
    # Write a consumed reservation BEFORE allowing the reusable router to run.
    # A failed/ambiguous write stops. Never erase or reuse the reservation.
    marker = reservation(revision, env["GITHUB_RUN_ID"])
    api.comment(marker)
    after, journal = api.read()
    issue_policy(after, revision)
    require(after.get("comments") == 1 and len(journal) == 1)
    require(reservation_matches(journal, revision) and journal[0]["body"] == marker)
    require(api.api(api.path + "/events?per_page=1") == [])
    require(api.api(f"repos/{REPO}/commits/main")["sha"] == env["EXPECTED_MAIN_SHA"])
    return payload


def main() -> int:
    from portfolio_tasks.terminal_projection import GitHub

    try:
        dispatch_policy(os.environ)
        schema = json.loads(Path("contracts/task-contract.schema.json").read_text())
        payload = prepare(GitHub(os.environ["ISSUE_NUMBER"]), os.environ, datetime.now(UTC), schema)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("task_payload=" + json.dumps(payload, separators=(",", ":")) + "\n")
        print("V5_SMOKE_RESERVATION_VERIFIED; dispatch is not terminal acceptance")
        return 0
    except (KeyError, TypeError, ValueError, OSError, AttributeError, subprocess.SubprocessError):
        print("V5_SMOKE_BLOCKED: authorization or evidence unavailable; do not retry")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
