"""Compatibility tests for the shared-contract execution boundary."""

import json
import subprocess
from pathlib import Path

import pytest

from portfolio_tasks.execution import (
    CANONICAL_EXECUTION_STATUSES,
    canonical_execution_status,
    load_execution_input,
    validate_result,
    workflow_outputs,
)

RESULT_FIELDS = {
    "contract_version",
    "correlation_id",
    "execution_status",
    "target_repository",
    "branch_name",
    "pull_request_url",
    "workflow_url",
    "validation_result",
    "test_result",
    "failure_category",
    "failure_message",
    "started_at",
    "completed_at",
}


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
        f"""import json, sys
value = json.load(open(sys.argv[2]))
valid = value.get('contract_version') == 'ai-sdlc-contract/v2'
if sys.argv[1] == 'validate-input':
    valid = valid and value.get('execution_mode') in {{'verify', 'implement'}}
elif sys.argv[1] == 'validate-result':
    valid = valid and set(value) == {RESULT_FIELDS!r}
    valid = valid and value.get('execution_status') in {{'verified', 'draft-pr-created', 'no-changes', 'blocked', 'failed'}}
else:
    valid = False
raise SystemExit(0 if valid else 1)
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))


@pytest.mark.parametrize("mode", ["verify", "implement"])
def test_valid_execution_modes(tmp_path: Path, shared_contracts: None, mode: str) -> None:
    path = tmp_path / "execution-input.json"
    path.write_text(json.dumps(payload(mode)), encoding="utf-8")
    value = load_execution_input(path)
    assert workflow_outputs(value)["execution_mode"] == mode


def result_payload(*, status: str = "verified") -> dict[str, object]:
    """Return the exact result used by the end-to-end router smoke scenario."""
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": "router-smoke-42",
        "execution_status": status,
        "target_repository": "Young-Consultations/portfolio-tasks",
        "branch_name": None,
        "pull_request_url": None,
        "workflow_url": (
            "https://github.com/Young-Consultations/portfolio-tasks/actions/runs/123456"
        ),
        "validation_result": "failed" if status == "failed" else "passed",
        "test_result": "not_run" if status in {"failed", "blocked"} else "passed",
        "failure_category": "validation_failed" if status == "failed" else None,
        "failure_message": None,
        "started_at": "2026-07-28T12:00:00Z",
        "completed_at": "2026-07-28T12:01:00Z",
    }


def write_result(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "execution-result.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_successful_verify_smoke_result_is_canonical(
    tmp_path: Path, shared_contracts: None
) -> None:
    result = result_payload()
    validate_result(write_result(tmp_path, result))

    assert "execution_mode" not in result
    assert result["branch_name"] is None
    assert result["pull_request_url"] is None
    assert result["execution_status"] == "verified"


def test_failure_result_remains_canonical(tmp_path: Path, shared_contracts: None) -> None:
    validate_result(write_result(tmp_path, result_payload(status="failed")))


@pytest.mark.parametrize("mode", ["verify", "implement"])
def test_workflow_result_does_not_copy_execution_mode(mode: str) -> None:
    text = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")
    result_expression = next(
        line for line in text.splitlines() if "{contract_version:$version" in line
    )

    assert mode in {"verify", "implement"}
    assert "execution_mode" not in result_expression


def test_unknown_result_field_is_rejected(tmp_path: Path, shared_contracts: None) -> None:
    result = result_payload()
    result["unexpected"] = True

    with pytest.raises(subprocess.CalledProcessError):
        validate_result(write_result(tmp_path, result))


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
    assert '"$AUTHORIZATION_OUTCOME" != success' in text
    assert '"$VALIDATION_OUTCOME" != success' in text
    assert "validation_result:$validation,test_result:$tests" in text
    assert 'validation_result:"passed",test_result:"passed"' not in text


def test_repository_has_no_local_contract_or_schema_copy() -> None:
    assert not any(Path("contracts").glob("**/*"))
    assert not any(Path("schemas").glob("**/*"))
    assert not any(Path("scripts").glob("*contract*"))
    assert not Path(".github/workflows/portfolio-dispatch-contract.yml").exists()


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ({"mode": "verify", "authorization_ok": True, "validation_ok": True}, "verified"),
        (
            {
                "mode": "implement",
                "authorization_ok": True,
                "validation_ok": True,
                "publish_ok": True,
                "pr_url": "https://github.com/Young-Consultations/portfolio-tasks/pull/43",
            },
            "draft-pr-created",
        ),
        (
            {
                "mode": "implement",
                "authorization_ok": True,
                "validation_ok": True,
                "no_changes": True,
            },
            "no-changes",
        ),
        ({"mode": "verify", "authorization_ok": True, "validation_ok": False}, "failed"),
        ({"mode": "verify", "authorization_ok": False}, "blocked"),
    ],
)
def test_outcomes_map_to_canonical_statuses(arguments: dict[str, object], expected: str) -> None:
    defaults: dict[str, object] = {
        "validation_ok": False,
        "publish_ok": False,
        "pr_url": None,
        "no_changes": False,
    }
    status = canonical_execution_status(**(defaults | arguments))  # type: ignore[arg-type]
    assert status == expected
    assert status in CANONICAL_EXECUTION_STATUSES


@pytest.mark.parametrize("status", sorted(CANONICAL_EXECUTION_STATUSES))
def test_every_emitted_status_validates(
    tmp_path: Path, shared_contracts: None, status: str
) -> None:
    validate_result(write_result(tmp_path, result_payload(status=status)))


def test_unknown_status_fails_validation(tmp_path: Path, shared_contracts: None) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        validate_result(write_result(tmp_path, result_payload(status="unknown")))


@pytest.mark.parametrize(
    ("fixture_name", "expected_status"),
    [("verify-result.json", "verified"), ("implement-result.json", "draft-pr-created")],
)
def test_exact_result_fixture_validates(
    shared_contracts: None, fixture_name: str, expected_status: str
) -> None:
    fixture = Path("tests/fixtures") / fixture_name
    validate_result(fixture)
    assert json.loads(fixture.read_text(encoding="utf-8"))["execution_status"] == expected_status


def test_active_result_generation_does_not_use_legacy_status() -> None:
    workflow = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")
    execution = Path("portfolio_tasks/execution.py").read_text(encoding="utf-8")
    legacy = "succeed" + "ed"
    assert legacy not in workflow
    assert legacy not in execution
