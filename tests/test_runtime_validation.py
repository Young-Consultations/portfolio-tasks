"""Regression tests for baseline-aware runtime validation."""

import json
from pathlib import Path
from unittest import mock

from portfolio_tasks import runtime_validation


def outcome(command, status="passed", digest="ok", detail=""):
    return {
        "command": command.label,
        "status": status,
        "digest": digest,
        "exit_code": 0 if status == "passed" else 1,
        "detail": detail,
    }


def baseline(path: Path, values: list[dict]) -> None:
    path.write_text(json.dumps({"schema_version": "1", "commands": values}))


def test_unchanged_pre_existing_failure_is_reported_and_allowed(tmp_path: Path) -> None:
    base = tmp_path / "baseline.json"
    values = [outcome(c) for c in runtime_validation.COMMANDS]
    values[1] = outcome(runtime_validation.COMMANDS[1], "failed", "existing")
    baseline(base, values)
    post = list(values)
    result = tmp_path / "result.json"
    result.write_text(json.dumps({"status": "changed"}))
    with (
        mock.patch.object(runtime_validation, "_outcome", side_effect=post),
        mock.patch.object(runtime_validation, "_changed_python_files", return_value=[]),
    ):
        code = runtime_validation.run_validations(tmp_path / "log", result, tmp_path, base)
    assert code == 0
    payload = json.loads(result.read_text())
    assert payload["validation"]["repository_baseline"] == "has_pre_existing_failures"
    assert payload["pre_existing_failures"] == [
        {"command": "ruff check .", "classification": "pre_existing_unchanged"}
    ]


def test_new_failure_introduced_by_task_fails(tmp_path: Path) -> None:
    base = tmp_path / "baseline.json"
    values = [outcome(c) for c in runtime_validation.COMMANDS]
    baseline(base, values)
    post = list(values)
    post[0] = outcome(runtime_validation.COMMANDS[0], "failed", "new")
    with (
        mock.patch.object(runtime_validation, "_outcome", side_effect=post),
        mock.patch.object(runtime_validation, "_changed_python_files", return_value=[]),
    ):
        assert (
            runtime_validation.run_validations(
                tmp_path / "log", working_directory=tmp_path, baseline_path=base
            )
            == 1
        )


def test_changed_file_formatting_failure_is_task_scoped_and_fails(tmp_path: Path) -> None:
    base = tmp_path / "baseline.json"
    values = [outcome(c) for c in runtime_validation.COMMANDS]
    baseline(base, values)
    formatting = {
        "command": "ruff format changed Python files",
        "status": "failed",
        "detail": "bad",
        "digest": "x",
    }
    with (
        mock.patch.object(runtime_validation, "_outcome", side_effect=[*values, formatting]) as run,
        mock.patch.object(runtime_validation, "_changed_python_files", return_value=["changed.py"]),
    ):
        assert (
            runtime_validation.run_validations(
                tmp_path / "log", working_directory=tmp_path, baseline_path=base
            )
            == 1
        )
    assert run.call_args_list[-1].args[0].argv == ("ruff", "format", "--check", "changed.py")


def test_infrastructure_is_not_pre_existing_debt(tmp_path: Path) -> None:
    base = tmp_path / "baseline.json"
    values = [outcome(c) for c in runtime_validation.COMMANDS]
    baseline(base, values)
    post = list(values)
    post[-1] = outcome(runtime_validation.COMMANDS[-1], "infrastructure_failure")
    with (
        mock.patch.object(runtime_validation, "_outcome", side_effect=post),
        mock.patch.object(runtime_validation, "_changed_python_files", return_value=[]),
    ):
        assert (
            runtime_validation.run_validations(
                tmp_path / "log", working_directory=tmp_path, baseline_path=base
            )
            == 1
        )


def test_missing_or_invalid_baseline_is_infrastructure_failure(tmp_path: Path) -> None:
    assert (
        runtime_validation.run_validations(tmp_path / "log", baseline_path=tmp_path / "missing")
        == runtime_validation.INFRASTRUCTURE_EXIT
    )


def test_capture_baseline_records_all_commands(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    with mock.patch.object(
        runtime_validation,
        "_outcome",
        side_effect=[outcome(c) for c in runtime_validation.COMMANDS],
    ):
        assert runtime_validation.capture_baseline(path, tmp_path) == 0
    assert len(json.loads(path.read_text())["commands"]) == len(runtime_validation.COMMANDS)
