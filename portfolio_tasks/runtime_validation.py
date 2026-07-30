"""Run the fixed Codex validation contract with concise console reporting."""

from __future__ import annotations

import argparse
import json
import os
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
    ValidationCommand("ruff", ("ruff", "check", ".")),
    ValidationCommand("mypy", ("mypy", "portfolio_tasks")),
    ValidationCommand("git diff --check", ("git", "diff", "--check")),
    ValidationCommand("actionlint", ("actionlint", "-shellcheck=")),
)


def _update_result(path: Path | None, validation: list[dict[str, str]]) -> None:
    if path is None or not path.exists():
        return
    value = json.loads(path.read_text(encoding="utf-8"))
    value["validation"] = validation
    value["log_artifact"] = "codex-trace.log"
    value["diff_artifact"] = "git-diff.patch"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_validations(
    log_path: Path, result_path: Path | None = None, working_directory: Path | None = None
) -> int:
    """Run every command, keeping successful output in the diagnostic log only."""
    command_directory = working_directory or Path.cwd()
    validation: list[dict[str, str]] = []
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("Validation")
    with log_path.open("w", encoding="utf-8") as log:
        for command in COMMANDS:
            executable = command.argv[0]
            if shutil.which(executable) is None:
                reason = f"required validation tool is unavailable: {executable}"
                print(f"FAIL {command.label}\nReason:\n{reason}\nExit code:\n{INFRASTRUCTURE_EXIT}")
                log.write(f"$ {' '.join(command.argv)}\n{reason}\n")
                validation.append({"command": command.label, "status": "infrastructure_error"})
                _update_result(result_path, validation)
                return INFRASTRUCTURE_EXIT
            completed = subprocess.run(
                command.argv,
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=command_directory,
            )
            log.write(f"$ {' '.join(command.argv)}\n{completed.stdout}{completed.stderr}")
            status = "passed" if completed.returncode == 0 else "failed"
            validation.append({"command": command.label, "status": status})
            if completed.returncode == 0:
                print(f"PASS {command.label}")
                continue
            reason = completed.stderr or completed.stdout or "command produced no diagnostic output"
            print(
                f"FAIL {command.label}\nReason:\n{reason.rstrip()}\n"
                f"Exit code:\n{completed.returncode}"
            )
            _update_result(result_path, validation)
            return completed.returncode or 1
    _update_result(result_path, validation)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--working-directory", type=Path, required=True)
    args = parser.parse_args()
    return run_validations(args.log, args.result, args.working_directory)


if __name__ == "__main__":
    raise SystemExit(main())
