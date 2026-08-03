"""Regression tests for repeatable task-branch and pull-request publication."""

import json
import os
import subprocess
from pathlib import Path

import pytest

PUBLISH = Path("scripts/publish-draft-pr").resolve()
PREPARE = Path("scripts/prepare-task-branch").resolve()
PR_URL = "https://github.com/Young-Consultations/portfolio-tasks/pull/42"


def install_fakes(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "curl").write_text(
        """#!/usr/bin/env bash
printf 'curl %s\\n' "$*" >> "$CALL_LOG"
if [[ " $* " == *" -X POST "* ]]; then cat "$POST_RESPONSE"; else cat "$PULLS_RESPONSE"; fi
""",
        encoding="utf-8",
    )
    (bin_dir / "git").write_text(
        """#!/usr/bin/env bash
printf 'git %s\\n' "$*" >> "$CALL_LOG"
case " $* " in
  *" ls-remote --exit-code "*) exit "${LS_REMOTE_STATUS:-2}" ;;
  *" status --porcelain=v1 "*) [[ "${HAS_CHANGES:-true}" == true ]] && printf ' M fixture\\n' ;;
  *" diff --cached "*) [[ "${HAS_CHANGES:-true}" == true ]] && exit 1 || exit 0 ;;
esac
""",
        encoding="utf-8",
    )
    for executable in bin_dir.iterdir():
        executable.chmod(0o755)
    return bin_dir


def environment(
    tmp_path: Path,
    pulls: list[dict[str, object]],
    *,
    remote_exists: bool = False,
    has_changes: bool = True,
) -> tuple[dict[str, str], Path, Path]:
    bin_dir = install_fakes(tmp_path)
    call_log = tmp_path / "calls.log"
    pulls_response = tmp_path / "pulls.json"
    post_response = tmp_path / "post.json"
    validation_summary = tmp_path / "validation-summary.json"
    output = tmp_path / "output"
    pulls_response.write_text(json.dumps(pulls), encoding="utf-8")
    post_response.write_text(
        json.dumps({"state": "open", "draft": True, "html_url": PR_URL}),
        encoding="utf-8",
    )
    validation_summary.write_text(
        json.dumps({"commands": [{"command": "python -m pytest", "classification": "passed"}]}),
        encoding="utf-8",
    )
    env = os.environ | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "CALL_LOG": str(call_log),
        "PULLS_RESPONSE": str(pulls_response),
        "POST_RESPONSE": str(post_response),
        "LS_REMOTE_STATUS": "0" if remote_exists else "2",
        "HAS_CHANGES": str(has_changes).lower(),
        "GH_TOKEN": "test-token",
        "API_ROOT": "https://api.github.test",
        "REPOSITORY": "Young-Consultations/portfolio-tasks",
        "BRANCH": "codex/fixture-task-42",
        "BASE_REVISION": "base-sha",
        "ISSUE_NUMBER": "42",
        "GITHUB_OUTPUT": str(output),
        "RUNNER_TEMP": str(tmp_path),
        "TASK_WORKTREE": str(tmp_path / "task-worktree"),
        "VALIDATION_RESULT": "passed",
        "VALIDATION_SUMMARY": str(validation_summary),
    }
    return env, call_log, output


def run_script(
    script: Path, env: dict[str, str], log: Path
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    result = subprocess.run([str(script)], env=env, text=True, capture_output=True, check=False)
    return result, log.read_text(encoding="utf-8").splitlines()


def test_new_branch_is_prepared_from_base(tmp_path: Path) -> None:
    env, log, _ = environment(tmp_path, [])
    result, calls = run_script(PREPARE, env, log)
    assert result.returncode == 0
    assert any("worktree add -b codex/fixture-task-42" in call for call in calls)
    assert any("task-worktree base-sha" in call for call in calls)
    assert not any(call.startswith("git fetch") for call in calls)


def test_existing_branch_is_fetched_and_checked_out_before_codex(tmp_path: Path) -> None:
    env, log, _ = environment(tmp_path, [], remote_exists=True)
    result, calls = run_script(PREPARE, env, log)
    assert result.returncode == 0
    assert calls.index(next(call for call in calls if call.startswith("git fetch"))) < calls.index(
        next(call for call in calls if "worktree add" in call)
    )
    assert any(
        "refs/heads/codex/fixture-task-42:refs/remotes/origin/codex/fixture-task-42" in call
        for call in calls
    )
    assert any(
        "worktree add --force -B codex/fixture-task-42" in call
        and "origin/codex/fixture-task-42" in call
        for call in calls
    )


def run_publish(tmp_path: Path, pulls: list[dict[str, object]], *, has_changes: bool = True):
    env, log, output = environment(tmp_path, pulls, has_changes=has_changes)
    result, calls = run_script(PUBLISH, env, log)
    return result, calls, output.read_text(encoding="utf-8") if output.exists() else ""


def test_first_publication_commits_pushes_and_creates_one_draft_pr(tmp_path: Path) -> None:
    result, calls, output = run_publish(tmp_path, [])
    assert result.returncode == 0
    assert output == f"url={PR_URL}\n"
    assert sum(" commit " in f" {call} " for call in calls) == 1
    assert sum(" push " in f" {call} " for call in calls) == 1
    assert all(
        " -C " in f" {call} "
        for call in calls
        if any(
            operation in f" {call} "
            for operation in (" status ", " config ", " add ", " diff ", " commit ", " push ")
        )
    )
    assert sum("/pulls -d" in call and " -X POST " in f" {call} " for call in calls) == 1


def test_repeated_publication_pushes_commit_and_reuses_open_draft_pr(tmp_path: Path) -> None:
    existing = [{"state": "open", "draft": True, "html_url": PR_URL}]
    result, calls, output = run_publish(tmp_path, existing)
    assert result.returncode == 0
    assert output == f"url={PR_URL}\n"
    commit = next(call for call in calls if " commit " in f" {call} ")
    push = next(call for call in calls if " push " in f" {call} ")
    query = next(call for call in calls if call.startswith("curl "))
    assert calls.index(commit) < calls.index(push) < calls.index(query)
    assert "HEAD:refs/heads/codex/fixture-task-42" in push
    assert not any("/pulls -d" in call and " -X POST " in f" {call} " for call in calls)


def test_existing_non_draft_pr_is_rejected(tmp_path: Path) -> None:
    existing = [{"state": "open", "draft": False, "html_url": PR_URL}]
    result, _, _ = run_publish(tmp_path, existing)
    assert result.returncode != 0
    assert "not a draft" in result.stderr


def test_existing_pr_with_no_changes_is_explicit_no_change(tmp_path: Path) -> None:
    existing = [{"state": "open", "draft": True, "html_url": PR_URL}]
    result, calls, output = run_publish(tmp_path, existing, has_changes=False)
    assert result.returncode == 0
    assert output == f"url={PR_URL}\nno_changes=true\n"
    assert "No changes" in result.stdout
    assert not any(
        operation in f" {call} " for call in calls for operation in (" commit ", " push ")
    )
    assert not any("/pulls -d" in call and " -X POST " in f" {call} " for call in calls)


def test_multiple_open_prs_fail_safely(tmp_path: Path) -> None:
    existing = [
        {"state": "open", "draft": True, "html_url": PR_URL},
        {"state": "open", "draft": True, "html_url": f"{PR_URL}0"},
    ]
    result, calls, _ = run_publish(tmp_path, existing)
    assert result.returncode != 0
    assert "found 2 open pull requests" in result.stderr
    assert not any(" -X POST " in f" {call} " for call in calls)


def test_existing_remote_branch_without_pr_gets_a_new_draft_pr(tmp_path: Path) -> None:
    result, calls, output = run_publish(tmp_path, [])
    assert result.returncode == 0
    assert output == f"url={PR_URL}\n"
    assert any(" push " in f" {call} " for call in calls)
    assert sum("/pulls -d" in call and " -X POST " in f" {call} " for call in calls) == 1


@pytest.mark.parametrize("merged_at", [None, "2026-01-01"])
def test_historical_pr_policy_still_blocks_reopening_branch(
    tmp_path: Path, merged_at: str | None
) -> None:
    historical = [{"state": "closed", "merged_at": merged_at}]
    result, calls, output = run_publish(tmp_path, historical)
    assert result.returncode != 0
    assert output == ""
    assert "closed or merged" in result.stderr
    assert not any(" -X POST " in f" {call} " for call in calls)


def test_two_executions_add_two_commits_to_the_same_branch(tmp_path: Path) -> None:
    existing = [{"state": "open", "draft": True, "html_url": PR_URL}]
    all_calls: list[str] = []
    for name in ("first", "second"):
        result, calls, _ = run_publish(tmp_path / name, existing)
        assert result.returncode == 0
        all_calls.extend(calls)
    assert sum(" commit " in f" {call} " for call in all_calls) == 2
    assert sum("HEAD:refs/heads/codex/fixture-task-42" in call for call in all_calls) == 2
