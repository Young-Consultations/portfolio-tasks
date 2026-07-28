import json
import os
import subprocess
from pathlib import Path

import pytest

BODY = """### Execution status

approved

### Target repository

{target}

### Task type

{task_type}

### Dependency issue references

{dependencies}

### Objective

Deliver the requested change.

### Required behavior

Keep every downstream path on the canonical payload.
"""


def issue(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "number": 42,
        "state": "open",
        "body": BODY.format(
            target="Young-Consultations/portfolio-tasks",
            task_type="Automation",
            dependencies="none",
        ),
        "labels": [
            "status:approved", "executor:codex", "priority:P1", "project:portfolio-tasks",
            "parallel-safe",
        ],
    }
    value.update(changes)
    return value


def build(tmp_path: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    source = tmp_path / "issue.json"
    output = tmp_path / "contract.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    env = os.environ | {"SOURCE_REPOSITORY": "Young-Consultations/portfolio-tasks", "GITHUB_RUN_ATTEMPT": "3"}
    return subprocess.run(
        ["scripts/build-task-contract.sh", str(source), str(output)],
        text=True, capture_output=True, env=env, check=False,
    )


def test_schema_uses_standard_json_schema_keywords() -> None:
    schema = json.loads(Path("schemas/task-contract.schema.json").read_text(encoding="utf-8"))
    assert "const" not in schema
    assert "enum" not in schema
    assert "required_top_level" not in schema
    assert schema["properties"]["schema_version"]["const"] == "ai-sdlc-contract/v1"
    assert isinstance(schema["properties"]["status"]["enum"], list)


@pytest.mark.parametrize(
    ("target", "project"),
    [
        ("Young-Consultations/portfolio-tasks", "portfolio-tasks"),
        ("Young-Consultations/consulting-playbook", "consulting-playbook"),
        ("Young-Consultations/slugger", "slugger"),
    ],
)
def test_valid_execution_paths_and_artifact(tmp_path: Path, target: str, project: str) -> None:
    payload = issue(
        body=BODY.format(target=target, task_type="Automation", dependencies="none"),
        labels=["status:approved", "executor:codex", "priority:P1", f"project:{project}"],
    )
    result = build(tmp_path, payload)
    assert result.returncode == 0, result.stderr
    artifact = json.loads((tmp_path / "contract.json").read_text())
    assert artifact["schema_version"] == "ai-sdlc-contract/v1"
    assert artifact["target_repository"] == target
    assert artifact["correlation_id"] == "Young-Consultations/portfolio-tasks#42@3"
    assert subprocess.run(
        ["scripts/validate-task-contract.sh", str(tmp_path / "contract.json")], check=False
    ).returncode == 0


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"body": BODY.format(target="Young-Consultations/portfolio-tasks", task_type="Automation", dependencies="none").replace("approved", "proposed", 1)}, "status conflict"),
        ({"body": BODY.format(target="Young-Consultations/portfolio-tasks", task_type="Epic", dependencies="none")}, "unsupported task type"),
        ({"body": BODY.format(target="", task_type="Automation", dependencies="none")}, "target repository"),
        ({"labels": ["status:approved", "priority:P1", "project:p"]}, "executor"),
        ({"labels": ["status:approved", "executor:codex", "project:p"]}, "priority"),
        ({"body": BODY.format(target="Young-Consultations/portfolio-tasks", task_type="Automation", dependencies="issue 1")}, "malformed dependency"),
        ({"state": "closed"}, "closed"),
        ({"pull_request": {"url": "x"}}, "pull request"),
        ({"labels": ["status:approved", "executor:codex", "priority:P1", "project:p", "sensitive"]}, "sensitive"),
    ],
)
def test_malformed_sources_fail(tmp_path: Path, changes: dict[str, object], message: str) -> None:
    result = build(tmp_path, issue(**changes))
    assert result.returncode != 0
    assert message in result.stderr


def test_approved_legacy_normalization_is_explicit(tmp_path: Path) -> None:
    payload = issue(
        body=BODY.format(target="Young-Consultations/portfolio-tasks", task_type="CI/CD", dependencies="#9"),
        labels=["status:approved", "executor:codex", "priority:p2", "project:legacy"],
    )
    result = build(tmp_path, payload)
    assert result.returncode == 0, result.stderr
    contract = json.loads((tmp_path / "contract.json").read_text())
    assert contract["task_type"] == "ci-cd"
    assert contract["priority"] == "P2"
    assert contract["dependencies"] == ["#9"]
