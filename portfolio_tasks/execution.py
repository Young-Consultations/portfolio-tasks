"""Thin repository-policy adapter for the shared AI-SDLC contracts package.

Schema ownership and validation deliberately remain in ``ai_sdlc_contracts``.  This
module only applies portfolio-tasks policy and formats workflow output.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

TARGET_REPOSITORY = "Young-Consultations/portfolio-tasks"
SOURCE_ISSUE = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#([1-9][0-9]*)$")
CANONICAL_EXECUTION_STATUSES = frozenset(
    {"verified", "draft-pr-created", "no-changes", "blocked", "failed"}
)


def canonical_execution_status(
    *,
    mode: str,
    authorization_ok: bool,
    validation_ok: bool,
    publish_ok: bool,
    pr_url: str | None,
    no_changes: bool,
) -> str:
    """Map workflow outcomes to the execution-result v2 status vocabulary."""
    if mode not in {"verify", "implement"}:
        raise ValueError("mode must be verify or implement")
    if not authorization_ok:
        return "blocked"
    if no_changes:
        return "verified" if mode == "verify" else "failed"
    if not validation_ok:
        return "failed"
    if mode == "verify":
        return "verified"
    if publish_ok and pr_url:
        return "draft-pr-created"
    return "failed"


def load_execution_input(path: Path) -> dict[str, Any]:
    """Validate with the shared package, then enforce target repository policy."""
    subprocess.run(
        [sys.executable, "-m", "ai_sdlc_contracts", "validate-input", str(path)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("execution input must be an object")
    if value.get("target_repository") != TARGET_REPOSITORY:
        raise ValueError("execution input targets another repository")
    if value.get("executor") != "codex" or value.get("draft_pr_only") is not True:
        raise ValueError("execution input violates executor or draft-PR policy")
    mode = value.get("execution_mode")
    if mode not in {"verify", "implement"}:
        raise ValueError("execution_mode must be verify or implement")
    source = value.get("source_issue")
    match = SOURCE_ISSUE.fullmatch(source) if isinstance(source, str) else None
    if match is None or match.group(1) != TARGET_REPOSITORY:
        raise ValueError("source_issue is not a canonical portfolio-tasks issue")
    return value


def workflow_outputs(value: dict[str, Any]) -> dict[str, str]:
    """Return the small set of trusted values needed by workflow orchestration."""
    match = SOURCE_ISSUE.fullmatch(str(value["source_issue"]))
    assert match is not None  # load_execution_input establishes this invariant
    return {
        "source_repository": match.group(1),
        "issue": match.group(2),
        "correlation": str(value["correlation_id"]),
        "execution_mode": str(value["execution_mode"]),
        "branch": str(value["requested_branch"]),
    }


def validate_result(path: Path) -> None:
    """Delegate execution-result validation to the canonical package."""
    subprocess.run(
        [sys.executable, "-m", "ai_sdlc_contracts", "validate-result", str(path)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect-input", "validate-result"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("path", type=Path)
    status_parser = subparsers.add_parser("execution-status")
    status_parser.add_argument("--mode", required=True, choices=("verify", "implement"))
    status_parser.add_argument("--authorization-ok", action="store_true")
    status_parser.add_argument("--validation-ok", action="store_true")
    status_parser.add_argument("--publish-ok", action="store_true")
    status_parser.add_argument("--pr-url")
    status_parser.add_argument("--no-changes", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "execution-status":
        print(
            canonical_execution_status(
                mode=args.mode,
                authorization_ok=args.authorization_ok,
                validation_ok=args.validation_ok,
                publish_ok=args.publish_ok,
                pr_url=args.pr_url,
                no_changes=args.no_changes,
            )
        )
        return 0
    if args.command == "validate-result":
        validate_result(args.path)
        return 0
    for key, value in workflow_outputs(load_execution_input(args.path)).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
