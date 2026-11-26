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
WORKFLOW_PATH = ".github/workflows/verify-v5-smoke.yml"
WORKFLOW_REF = f"{REPO}/{WORKFLOW_PATH}@refs/heads/main"
MARKER = "<!-- ai-sdlc-v5-smoke-reservation:v2 "
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
        and env.get("GITHUB_WORKFLOW_SHA") == env.get("EXPECTED_MAIN_SHA")
        and env.get("GITHUB_WORKFLOW_REF") == WORKFLOW_REF
    )


def reservation(revision: SourceRevision, run_id: str, sha: str) -> str:
    require(re.fullmatch(r"[1-9][0-9]*", run_id))
    require(re.fullmatch(r"[0-9a-f]{40}", sha))
    record = {
        "owner": OWNER,
        "source_issue": revision.source_issue,
        "task_id": revision.task_id,
        "mode": "verify",
        "release": RELEASE,
        "run_id": run_id,
        "attempt": "1",
        "workflow_ref": WORKFLOW_REF,
        "workflow_sha": sha,
    }
    return MARKER + json.dumps(record, sort_keys=True, separators=(",", ":")) + " -->"


def reservation_record(comments: Any, revision: SourceRevision) -> dict[str, Any] | None:
    if not isinstance(comments, list):
        return None
    try:
        rows = [row for row in comments if "ai-sdlc-v5-smoke-reservation:" in row["body"]]
        if len(rows) != 1:
            return None
        row = rows[0]
        body = row["body"]
        if (
            row["user"]["login"] != "github-actions[bot]"
            or not isinstance(body, str)
            or not body.startswith(MARKER)
        ):
            return None
        record = json.loads(body[len(MARKER) : -4])
        if not isinstance(record, dict):
            return None
        if body != reservation(revision, record["run_id"], record["workflow_sha"]):
            return None
        return record
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def run_title(revision: SourceRevision, sha: str) -> str:
    return f"v5 verify smoke {revision.source_issue} {revision.task_id} @{sha}"


def prove_run(
    api: Any,
    revision: SourceRevision,
    record: Mapping[str, Any],
    sha: str,
    *,
    prepared: bool,
) -> None:
    """Bind the bot marker to GitHub's first-attempt run and exact dispatch identity."""
    require(re.fullmatch(r"[0-9a-f]{40}", sha))
    require(record["workflow_sha"] == sha and record["workflow_ref"] == WORKFLOW_REF)
    run_id = record["run_id"]
    require(re.fullmatch(r"[1-9][0-9]*", run_id))
    path = f"repos/{REPO}/actions/runs/{run_id}"
    run = api.api(path)
    require(
        type(run.get("id")) is int
        and str(run["id"]) == run_id
        and type(run.get("run_attempt")) is int
        and run["run_attempt"] == 1
        and run.get("path") == WORKFLOW_PATH
        and run.get("event") == "workflow_dispatch"
        and run.get("head_branch") == "main"
        and run.get("head_sha") == sha
        and run.get("repository", {}).get("full_name") == REPO
        and run.get("head_repository", {}).get("full_name") == REPO
        and run.get("actor", {}).get("login") == OWNER
        and run.get("triggering_actor", {}).get("login") == OWNER
        and run.get("display_title") == run_title(revision, sha)
    )
    if prepared:
        # The receiver may forward while the route job is still running.
        # Do not require the whole source run to have completed.
        evidence = api.api(path + "/attempts/1/jobs?per_page=100")
        jobs = evidence.get("jobs")
        require(
            isinstance(jobs, list)
            and type(evidence.get("total_count")) is int
            and evidence["total_count"] == len(jobs)
        )
        candidates = [job for job in jobs if job.get("name") == "prepare"]
        require(len(candidates) == 1)
        job = candidates[0]
        require(
            job.get("run_id") == int(run_id)
            and job.get("head_sha") == sha
            and job.get("status") == "completed"
            and job.get("conclusion") == "success"
        )
        steps = [
            step
            for step in job.get("steps", [])
            if step.get("name") == "Validate owner-bound issue and consume one-shot reservation"
        ]
        require(
            len(steps) == 1
            and steps[0].get("status") == "completed"
            and steps[0].get("conclusion") == "success"
        )


def prove_reservation(
    api: Any,
    issue: Mapping[str, Any],
    comments: Any,
    revision: SourceRevision,
    sha: str,
) -> dict[str, Any]:
    issue_policy(issue, revision)
    record = reservation_record(comments, revision)
    require(record is not None)
    assert record is not None
    prove_run(api, revision, record, sha, prepared=True)
    return record


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
    sha = env["EXPECTED_MAIN_SHA"]
    marker = reservation(revision, env["GITHUB_RUN_ID"], sha)
    record = json.loads(marker[len(MARKER) : -4])
    prove_run(api, revision, record, sha, prepared=False)
    api.comment(marker)
    after, journal = api.read()
    issue_policy(after, revision)
    require(after.get("comments") == 1 and len(journal) == 1)
    require(reservation_record(journal, revision) == record and journal[0]["body"] == marker)
    prove_run(api, revision, record, sha, prepared=False)
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
