"""Focused tests for idempotent draft pull-request publication."""

import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path("scripts/publish-draft-pr").resolve()
PR_URL = "https://github.com/Young-Consultations/portfolio-tasks/pull/42"


def install_fakes(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "curl").write_text(
        """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CALL_LOG"
if [[ " $* " == *" -X POST "* ]]; then
  cat "$POST_RESPONSE"
else
  cat "$PULLS_RESPONSE"
fi
""",
        encoding="utf-8",
    )
    (bin_dir / "git").write_text(
        """#!/usr/bin/env bash
printf 'git %s\\n' "$*" >> "$CALL_LOG"
if [[ "$1" == ls-remote ]]; then exit "${LS_REMOTE_STATUS:-2}"; fi
""",
        encoding="utf-8",
    )
    for executable in bin_dir.iterdir():
        executable.chmod(0o755)
    return bin_dir


def run_publish(
    tmp_path: Path,
    pulls: list[dict[str, object]],
    *,
    remote_status: int = 2,
) -> tuple[subprocess.CompletedProcess[str], list[str], str]:
    bin_dir = install_fakes(tmp_path)
    call_log = tmp_path / "calls.log"
    pulls_response = tmp_path / "pulls.json"
    post_response = tmp_path / "post.json"
    output = tmp_path / "output"
    pulls_response.write_text(json.dumps(pulls), encoding="utf-8")
    post_response.write_text(
        json.dumps({"state": "open", "draft": True, "html_url": PR_URL}),
        encoding="utf-8",
    )
    env = os.environ | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "CALL_LOG": str(call_log),
        "PULLS_RESPONSE": str(pulls_response),
        "POST_RESPONSE": str(post_response),
        "LS_REMOTE_STATUS": str(remote_status),
        "GH_TOKEN": "test-token",
        "API_ROOT": "https://api.github.test",
        "REPOSITORY": "Young-Consultations/portfolio-tasks",
        "BRANCH": "codex/fixture-task-42",
        "ISSUE_NUMBER": "42",
        "GITHUB_OUTPUT": str(output),
        "RUNNER_TEMP": str(tmp_path),
    }
    result = subprocess.run(
        [str(SCRIPT)], env=env, text=True, capture_output=True, check=False
    )
    calls = call_log.read_text(encoding="utf-8").splitlines()
    return result, calls, output.read_text(encoding="utf-8") if output.exists() else ""


def test_existing_draft_pr_is_an_idempotent_success(tmp_path: Path) -> None:
    existing = [{"state": "open", "draft": True, "html_url": PR_URL}]

    first, first_calls, first_output = run_publish(tmp_path / "first", existing)
    second, second_calls, second_output = run_publish(tmp_path / "second", existing)

    assert first.returncode == second.returncode == 0
    assert first_output == second_output == f"url={PR_URL}\n"
    for calls in (first_calls, second_calls):
        assert not any(call.startswith("git switch") for call in calls)
        assert not any(call.startswith("git commit") for call in calls)
        assert not any(call.startswith("git push") for call in calls)
        assert not any(" -X POST " in f" {call} " for call in calls)
        assert len(calls) == 1


def test_no_existing_pr_performs_normal_publication(tmp_path: Path) -> None:
    result, calls, output = run_publish(tmp_path, [])

    assert result.returncode == 0
    assert output == f"url={PR_URL}\n"
    assert sum(call.startswith("git switch -c ") for call in calls) == 1
    assert sum(call.startswith("git commit ") for call in calls) == 1
    assert sum(call.startswith("git push ") for call in calls) == 1
    assert sum(" -X POST " in f" {call} " for call in calls) == 1


def test_existing_open_non_draft_pr_is_reused(tmp_path: Path) -> None:
    existing = [{"state": "open", "draft": False, "html_url": PR_URL}]
    result, calls, output = run_publish(tmp_path, existing)

    assert result.returncode == 0
    assert output == f"url={PR_URL}\n"
    assert len(calls) == 1


@pytest.mark.parametrize("state", ["closed", "merged"])
def test_historical_pr_blocks_duplicate_publication(tmp_path: Path, state: str) -> None:
    existing = [{"state": "closed", "merged_at": "2026-01-01" if state == "merged" else None}]
    result, calls, output = run_publish(tmp_path, existing)

    assert result.returncode != 0
    assert output == ""
    assert len(calls) == 1
    assert "closed or merged" in result.stderr


def test_remote_branch_without_pr_blocks_duplicate_publication(tmp_path: Path) -> None:
    result, calls, output = run_publish(tmp_path, [], remote_status=0)

    assert result.returncode != 0
    assert output == ""
    assert sum(call.startswith("git ls-remote ") for call in calls) == 1
    assert not any(call.startswith("git switch") for call in calls)
    assert not any(" -X POST " in f" {call} " for call in calls)
