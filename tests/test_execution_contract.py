"""Compatibility tests for the shared-contract execution boundary."""

import json
import subprocess
from pathlib import Path

import pytest

from portfolio_tasks.execution import load_execution_input, workflow_outputs


def payload(mode: str = "implement") -> dict[str, object]:
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": "fixture-task-42",
        "source_issue": "Young-Consultations/portfolio-tasks#42",
        "target_repository": "Young-Consultations/portfolio-tasks",
        "executor": "codex",
        "draft_pr_only": True,
        "execution_mode": mode,
        "requested_branch": "codex/fixture-task-42",
        "instructions": "Make the approved change.",
    }


@pytest.fixture
def shared_contracts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package = tmp_path / "ai_sdlc_contracts"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "__main__.py").write_text(
        """import json, sys
value = json.load(open(sys.argv[2]))
valid = value.get('contract_version') == 'ai-sdlc-contract/v2'
if sys.argv[1] == 'validate-input':
    valid = valid and value.get('execution_mode') in {'verify', 'implement'}
elif sys.argv[1] != 'validate-result':
    valid = False
raise SystemExit(0 if valid else 1)
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))


@pytest.mark.parametrize("mode", ["verify", "implement"])
def test_valid_execution_modes(
    tmp_path: Path, shared_contracts: None, mode: str
) -> None:
    path = tmp_path / "execution-input.json"
    path.write_text(json.dumps(payload(mode)), encoding="utf-8")
    value = load_execution_input(path)
    assert workflow_outputs(value)["execution_mode"] == mode


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("contract_version", "ai-sdlc-contract/v1"),
        ("execution_mode", "plan"),
        ("target_repository", "Young-Consultations/other"),
        ("source_issue", "Young-Consultations/other#42"),
        ("executor", "human"),
        ("draft_pr_only", False),
    ],
)
def test_invalid_execution_input_is_rejected(
    tmp_path: Path, shared_contracts: None, field: str, value: object
) -> None:
    path = tmp_path / "execution-input.json"
    path.write_text(json.dumps(payload() | {field: value}), encoding="utf-8")
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        load_execution_input(path)


def test_workflow_is_a_thin_secure_execution_target() -> None:
    text = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")
    assert "execution-input.json" in text
    assert "Version(version('ai-sdlc-contracts')) >= Version('1.0.1')" in text
    assert "load_contract_version() == 'ai-sdlc-contract/v2'" in text
    assert "python -m portfolio_tasks.execution inspect-input" in text
    assert "steps.input.outputs.execution_mode == 'implement'" in text
    assert "draft:true" in text
    assert "persist-credentials: false" in text
    assert "pull_request_target:" not in text
    assert "schemas/" not in text


def test_workflow_validates_codex_changes_and_reports_real_outcomes() -> None:
    text = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")
    codex = text.index("- name: Install and execute Codex")
    validation = text.index("- name: Validate target repository")
    publication = text.index("- name: Create task branch and draft PR")

    assert codex < validation < publication
    assert '"$AUTHORIZATION_OUTCOME" == success' in text
    assert '"$VALIDATION_OUTCOME" == success' in text
    assert "validation_result:$validation,test_result:$tests" in text
    assert 'validation_result:"passed",test_result:"passed"' not in text


def test_repository_has_no_local_contract_or_schema_copy() -> None:
    assert not any(Path("contracts").glob("**/*"))
    assert not any(Path("schemas").glob("**/*"))
    assert not any(Path("scripts").glob("*contract*"))
    assert not Path(".github/workflows/portfolio-dispatch-contract.yml").exists()
