"""Process-level, offline tests for the complete Codex wrapper boundary."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from portfolio_tasks.prompts import render_execution_prompt
from portfolio_tasks.run_codex import validate_completion_result

ROOT = Path(__file__).parents[1]
FAKE = ROOT / "tests/fixtures/fake_codex.py"


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, text=True, capture_output=True
    ).stdout


def prepare(tmp_path: Path) -> tuple[Path, Path, str]:
    repository = tmp_path / "repository"
    worktree = tmp_path / "task-worktree"
    repository.mkdir()
    git("init", "-b", "main", cwd=repository)
    git("config", "user.email", "tests@example.invalid", cwd=repository)
    git("config", "user.name", "Offline Test", cwd=repository)
    (repository / "task.txt").write_text("trusted initial state\n", encoding="utf-8")
    git("add", "task.txt", cwd=repository)
    git("commit", "-m", "trusted initial state", cwd=repository)
    git("worktree", "add", "-b", "codex/test", str(worktree), "HEAD", cwd=repository)
    execution_input = {
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": "offline-e2e",
        "source_issue": "Young-Consultations/portfolio-tasks#1",
        "target_repository": "Young-Consultations/portfolio-tasks",
        "executor": "codex",
        "draft_pr_only": True,
        "execution_mode": "implement",
        "requested_branch": "codex/test",
        "instructions": "Change task.txt using the deterministic test fixture.",
    }
    input_path = tmp_path / "execution-input.json"
    input_path.write_text(json.dumps(execution_input), encoding="utf-8")
    prompt = render_execution_prompt(
        task_instructions=execution_input["instructions"],
        repository_context="",
        validation_commands=[],
    )
    (tmp_path / "instructions.md").write_text(prompt, encoding="utf-8")
    return repository, worktree, prompt


def invoke(
    tmp_path: Path, scenario: str, *, timeout: float = 5
) -> tuple[subprocess.CompletedProcess[str], Path]:
    _, worktree, prompt = prepare(tmp_path)
    sentinel = tmp_path / "sentinel-bin"
    sentinel.mkdir()
    marker = tmp_path / "REAL_CODEX_WAS_CALLED"
    (sentinel / "codex").write_text(f"#!/bin/sh\ntouch {marker!s}\nexit 99\n", encoding="utf-8")
    (sentinel / "codex").chmod(0o755)
    FAKE.chmod(0o755)
    env = os.environ.copy()
    env.pop("CODEX_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    env.update(
        {
            "PATH": f"{sentinel}{os.pathsep}{env['PATH']}",
            "PYTHONPATH": str(ROOT),
            "RUNNER_TEMP": str(tmp_path / "runner-temp"),
            "FAKE_CODEX_SCENARIO": scenario,
            "FAKE_CODEX_METADATA": str(tmp_path / "invocation.json"),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "portfolio_tasks.run_codex",
            "--codex-executable",
            str(FAKE),
            "--working-directory",
            str(worktree),
            "--timeout",
            str(timeout),
        ],
        input=prompt,
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
        timeout=10,
        check=False,
    )
    assert not marker.exists(), "the real-name Codex sentinel was invoked"
    return result, worktree


def test_complete_stubbed_execution_path(tmp_path: Path) -> None:
    result, worktree = invoke(tmp_path, "success_changed")
    assert result.returncode == 0, result.stderr
    assert (worktree / "task.txt").read_text() == "changed by deterministic fake\n"
    payload = json.loads((worktree / "codex-result.json").read_text())
    assert payload["status"] == "changed"
    assert validate_completion_result(worktree / "codex-result.json", repository_changed=True) == (
        True,
        "changed",
    )
    assert git(
        "status", "--porcelain=v1", "--", ".", ":(exclude)codex-result.json", cwd=worktree
    ).strip()
    metadata = json.loads((tmp_path / "invocation.json").read_text())
    assert metadata["cwd"] == str(worktree)
    assert metadata["credentials_present"] is False
    assert metadata["prompt_length"] > 100
    assert "Change task.txt" not in result.stdout + result.stderr
    assert len(result.stdout + result.stderr) < 1_000


@pytest.mark.parametrize(
    ("scenario", "code", "message"),
    [
        ("stdout_failure", 21, "fake stdout failure"),
        ("stderr_failure", 22, "fake stderr failure"),
        ("mixed_failure", 23, "fake stdout context"),
    ],
)
def test_nonzero_failures_are_visible_and_propagated(
    tmp_path: Path, scenario: str, code: int, message: str
) -> None:
    result, _ = invoke(tmp_path, scenario)
    assert result.returncode == code
    assert message in result.stderr
    if scenario == "mixed_failure":
        assert result.stderr.count("fake stdout context") == 1
        assert "fake stderr context" in result.stderr


@pytest.mark.parametrize(
    "scenario",
    [
        "missing_result",
        "invalid_result_json",
        "invalid_result_schema",
        "changed_without_tree_change",
    ],
)
def test_invalid_or_missing_results_fail(tmp_path: Path, scenario: str) -> None:
    result, _ = invoke(tmp_path, scenario)
    assert result.returncode != 0


def test_already_satisfied_with_tree_change_fails(tmp_path: Path) -> None:
    result, _ = invoke(tmp_path, "already_satisfied_with_tree_change")
    assert result.returncode == 1
    assert "Invalid Codex result" in result.stderr


def test_already_satisfied_clean_tree_succeeds(tmp_path: Path) -> None:
    result, worktree = invoke(tmp_path, "success_already_satisfied")
    assert result.returncode == 0
    assert json.loads((worktree / "codex-result.json").read_text())["status"] == "already_satisfied"


def test_timeout_kills_process_group_with_bounded_duration(tmp_path: Path) -> None:
    started = time.monotonic()
    result, _ = invoke(tmp_path, "timeout", timeout=0.2)
    assert result.returncode == 124
    assert time.monotonic() - started < 3
    assert "timed out" in result.stderr


def test_process_level_diagnostics_redact_secrets(tmp_path: Path) -> None:
    result, _ = invoke(tmp_path, "secret_failure")
    assert result.returncode == 24
    assert "test-secret" not in result.stderr
    assert "sk-offline-secret" not in result.stderr
    assert "[REDACTED]" in result.stderr
