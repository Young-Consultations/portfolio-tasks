"""Regression tests for concise runtime validation reporting."""

import io
import json
import subprocess
from pathlib import Path
from unittest import mock

from portfolio_tasks import runtime_validation


def test_success_is_concise_and_full_output_stays_in_log(tmp_path: Path) -> None:
    noisy = "detail\n" * 1000
    completed = subprocess.CompletedProcess([], 0, stdout=noisy, stderr="")
    console = io.StringIO()
    with mock.patch.object(runtime_validation.shutil, "which", return_value="/bin/tool"), \
            mock.patch.object(runtime_validation.subprocess, "run", return_value=completed), \
            mock.patch("sys.stdout", console):
        status = runtime_validation.run_validations(tmp_path / "validation.log")

    assert status == 0
    assert noisy not in console.getvalue()
    assert console.getvalue().count("PASS ") == len(runtime_validation.COMMANDS)
    assert noisy in (tmp_path / "validation.log").read_text(encoding="utf-8")


def test_failure_prints_stderr_and_updates_result(tmp_path: Path) -> None:
    result = tmp_path / "codex-result.json"
    result.write_text(json.dumps({"status": "changed"}), encoding="utf-8")
    completed = subprocess.CompletedProcess([], 1, stdout="", stderr="workflow is invalid")
    console = io.StringIO()
    with mock.patch.object(runtime_validation.shutil, "which", return_value="/bin/tool"), \
            mock.patch.object(runtime_validation.subprocess, "run", return_value=completed), \
            mock.patch("sys.stdout", console):
        status = runtime_validation.run_validations(
            tmp_path / "validation.log", result
        )

    assert status == 1
    assert "FAIL python -m pytest" in console.getvalue()
    assert "workflow is invalid" in console.getvalue()
    value = json.loads(result.read_text(encoding="utf-8"))
    assert value["validation"][0]["status"] == "failed"
    assert value["log_artifact"] == "codex-trace.log"
    assert value["diff_artifact"] == "git-diff.patch"


def test_missing_actionlint_is_an_infrastructure_failure(tmp_path: Path) -> None:
    successes = iter([
        subprocess.CompletedProcess([], 0, stdout="", stderr="")
        for _ in range(4)
    ])

    def available(name: str) -> str | None:
        return None if name == "actionlint" else f"/bin/{name}"

    console = io.StringIO()
    with mock.patch.object(runtime_validation.shutil, "which", side_effect=available), \
            mock.patch.object(runtime_validation.subprocess, "run", side_effect=successes), \
            mock.patch("sys.stdout", console):
        status = runtime_validation.run_validations(tmp_path / "validation.log")

    assert status == runtime_validation.INFRASTRUCTURE_EXIT
    assert "FAIL actionlint" in console.getvalue()
    assert "required validation tool is unavailable" in console.getvalue()


def test_actionlint_failure_fails_validation(tmp_path: Path) -> None:
    outcomes = [subprocess.CompletedProcess([], 0, stdout="", stderr="") for _ in range(4)]
    outcomes.append(subprocess.CompletedProcess([], 1, stdout="", stderr="bad workflow"))
    with mock.patch.object(runtime_validation.shutil, "which", return_value="/bin/tool"), \
            mock.patch.object(runtime_validation.subprocess, "run", side_effect=outcomes):
        status = runtime_validation.run_validations(tmp_path / "validation.log")
    assert status == 1
