"""Baseline-aware repository and task-scoped validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

INFRASTRUCTURE_EXIT = 78


@dataclass(frozen=True)
class ValidationCommand:
    label: str
    argv: tuple[str, ...]


COMMANDS = (
    ValidationCommand("python -m pytest", (sys.executable, "-m", "pytest")),
    ValidationCommand("ruff check .", ("ruff", "check", ".")),
    ValidationCommand("mypy portfolio_tasks", ("mypy", "portfolio_tasks")),
    ValidationCommand("git diff --check", ("git", "diff", "--check")),
    ValidationCommand("actionlint", ("actionlint", "-shellcheck=")),
)


def _diagnostic_digest(output: str) -> str:
    """Fingerprint substantive diagnostics while excluding volatile timing text."""
    normalized = re.sub(r"\b\d+(?:\.\d+)?s\b", "<duration>", output)
    normalized = re.sub(r"/tmp/[^\s:]+", "<temporary-path>", normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _outcome(command: ValidationCommand, cwd: Path) -> dict[str, str | int]:
    if shutil.which(command.argv[0]) is None:
        return {
            "command": command.label,
            "status": "infrastructure_failure",
            "detail": f"required validation tool is unavailable: {command.argv[0]}",
        }
    result = subprocess.run(
        command.argv, cwd=cwd, check=False, capture_output=True, text=True, env=os.environ.copy()
    )
    output = result.stdout + result.stderr
    return {
        "command": command.label,
        "status": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "digest": _diagnostic_digest(output),
        "detail": output,
    }


def capture_baseline(path: Path, working_directory: Path) -> int:
    """Capture trusted pre-change repository-wide command outcomes."""
    outcomes = [_outcome(command, working_directory) for command in COMMANDS]
    path.write_text(json.dumps({"schema_version": "1", "commands": outcomes}, indent=2) + "\n")
    return (
        INFRASTRUCTURE_EXIT if any(o["status"] == "infrastructure_failure" for o in outcomes) else 0
    )


def _changed_python_files(cwd: Path) -> list[str]:
    result = subprocess.run(
        ("git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD", "--", "*.py"),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _update_result(
    path: Path | None, task_passed: bool, classifications: list[dict[str, str]]
) -> None:
    if path is None or not path.exists():
        return
    value = json.loads(path.read_text())
    debt = [item for item in classifications if item["classification"] == "pre_existing_unchanged"]
    value["validation"] = {
        "task_scoped": "passed" if task_passed else "failed",
        "repository_baseline": "has_pre_existing_failures" if debt else "passed",
    }
    value["pre_existing_failures"] = debt
    value["validation_classifications"] = classifications
    value["log_artifact"], value["diff_artifact"] = "codex-trace.log", "git-diff.patch"
    path.write_text(json.dumps(value, indent=2) + "\n")


def run_validations(
    log_path: Path,
    result_path: Path | None = None,
    working_directory: Path | None = None,
    baseline_path: Path | None = None,
) -> int:
    """Compare required checks with a trusted baseline and check changed Python formatting."""
    cwd = working_directory or Path.cwd()
    if baseline_path is None or not baseline_path.exists():
        print("FAIL baseline\nReason:\ntrusted validation baseline is unavailable")
        return INFRASTRUCTURE_EXIT
    try:
        baseline = json.loads(baseline_path.read_text())["commands"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        print("FAIL baseline\nReason:\ntrusted validation baseline is invalid")
        return INFRASTRUCTURE_EXIT
    before = {item["command"]: item for item in baseline}
    classifications: list[dict[str, str]] = []
    failed = False
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("Validation")
    with log_path.open("w") as log:
        for command in COMMANDS:
            after = _outcome(command, cwd)
            prior = before.get(command.label)
            log.write(f"$ {command.label}\n{after.get('detail', '')}")
            if (
                prior is None
                or prior.get("status") == "infrastructure_failure"
                or after["status"] == "infrastructure_failure"
            ):
                classification = "infrastructure_failure"
                failed = True
            elif after["status"] == "passed":
                classification = (
                    "pre_existing_improved" if prior["status"] == "failed" else "passed"
                )
            elif prior["status"] == "failed" and prior.get("digest") == after.get("digest"):
                classification = "pre_existing_unchanged"
            else:
                classification = "introduced_by_task"
                failed = True
            classifications.append({"command": command.label, "classification": classification})
            print(
                (
                    "FAIL"
                    if classification in {"introduced_by_task", "infrastructure_failure"}
                    else "PASS"
                ),
                command.label,
                f"({classification})",
            )
        python_files = _changed_python_files(cwd)
        if python_files:
            formatting = _outcome(
                ValidationCommand(
                    "ruff format changed Python files", ("ruff", "format", "--check", *python_files)
                ),
                cwd,
            )
            log.write(
                f"$ ruff format --check {' '.join(python_files)}\n{formatting.get('detail', '')}"
            )
            classification = (
                "passed"
                if formatting["status"] == "passed"
                else (
                    "infrastructure_failure"
                    if formatting["status"] == "infrastructure_failure"
                    else "introduced_by_task"
                )
            )
            classifications.append(
                {"command": "ruff format changed Python files", "classification": classification}
            )
            if classification != "passed":
                failed = True
            print(
                "PASS" if classification == "passed" else "FAIL",
                "ruff format changed Python files",
                f"({classification})",
            )
    _update_result(result_path, not failed, classifications)
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--working-directory", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--capture-baseline", action="store_true")
    args = parser.parse_args()
    if args.capture_baseline:
        return capture_baseline(args.baseline, args.working_directory)
    if args.log is None:
        parser.error("--log is required unless capturing a baseline")
    return run_validations(args.log, args.result, args.working_directory, args.baseline)


if __name__ == "__main__":
    raise SystemExit(main())
