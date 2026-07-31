#!/usr/bin/env python3
"""Deterministic, offline replacement for the external Codex CLI."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


HELP = "--sandbox --ask-for-approval --skip-git-repo-check --full-auto --config --model"


def valid_result(status: str, changed: bool) -> dict[str, object]:
    return {
        "status": status,
        "objective": "Exercise the complete offline execution path.",
        "acceptance_criteria": [
            {
                "criterion": "The deterministic fixture completed.",
                "status": "satisfied",
                "evidence": "The fake executable recorded and applied its scenario.",
            }
        ],
        "validation": [{"command": "git status --porcelain=v1", "status": "passed"}],
        "unresolved_items": [],
        "files_changed": ["task.txt"] if changed else [],
    }


def main() -> int:
    if sys.argv[1:] == ["--version"]:
        print("fake-codex 1.0 (offline)")
        return 0
    if sys.argv[1:] == ["exec", "--help"]:
        print(HELP)
        return 0

    prompt = sys.stdin.read()
    scenario = os.environ.get("FAKE_CODEX_SCENARIO", "success_changed")
    metadata = Path(os.environ.get("FAKE_CODEX_METADATA", "fake-codex-invocation.json"))
    metadata.write_text(
        json.dumps(
            {
                "argv": sys.argv[1:],
                "cwd": str(Path.cwd()),
                "prompt_length": len(prompt),
                "prompt_sha256_recorded": True,
                "credentials_present": any(
                    os.environ.get(key) for key in ("CODEX_API_KEY", "OPENAI_API_KEY")
                ),
            }
        ),
        encoding="utf-8",
    )

    if scenario == "stdout_failure":
        print("fake stdout failure: model_not_found")
        return 21
    if scenario == "stderr_failure":
        print("fake stderr failure: permission denied", file=sys.stderr)
        return 22
    if scenario == "mixed_failure":
        print("fake stdout context")
        print("fake stderr context", file=sys.stderr)
        return 23
    if scenario == "secret_failure":
        print("Authorization: Bearer test-secret sk-offline-secret", file=sys.stderr)
        return 24
    if scenario == "timeout":
        subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        time.sleep(60)
        return 0
    if scenario in {"success_changed", "already_satisfied_with_tree_change"}:
        Path("task.txt").write_text("changed by deterministic fake\n", encoding="utf-8")
    if scenario == "missing_result":
        return 0
    if scenario == "invalid_result_json":
        Path("codex-result.json").write_text("{not json", encoding="utf-8")
        return 0
    if scenario == "invalid_result_schema":
        Path("codex-result.json").write_text('{"status":"changed"}', encoding="utf-8")
        return 0

    status = {
        "success_already_satisfied": "already_satisfied",
        "already_satisfied_with_tree_change": "already_satisfied",
    }.get(scenario, "changed")
    changed = scenario in {"success_changed", "already_satisfied_with_tree_change"}
    Path("codex-result.json").write_text(
        json.dumps(valid_result(status, changed)) + "\n", encoding="utf-8"
    )
    print("fake Codex completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
