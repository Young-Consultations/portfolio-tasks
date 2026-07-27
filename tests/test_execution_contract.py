"""Contract tests for the controlled canonical execution workflow."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path("scripts/execution-contract.sh")
WORKFLOW = Path(".github/workflows/codex-execute.yml")


def valid_input() -> dict[str, object]:
    return {
        "contract_version": "ai-sdlc-execution-input/v1",
        "correlation_id": "Young-Consultations/portfolio-tasks#42@7",
        "source_issue": {"repository": "Young-Consultations/portfolio-tasks", "number": 42},
        "target_repository": "Young-Consultations/portfolio-tasks",
        "executor": "codex",
        "draft_pr_only": True,
        "instructions": "Make a harmless documentation correction.",
    }


def validate(tmp_path: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload))
    return subprocess.run(
        ["bash", str(SCRIPT), "validate-input", str(path)],
        check=False,
        text=True,
        capture_output=True,
    )


def test_valid_execution_input(tmp_path: Path) -> None:
    assert validate(tmp_path, valid_input()).returncode == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("contract_version", "ai-sdlc-execution-input/v0"),
        ("target_repository", "Young-Consultations/another-repository"),
        ("draft_pr_only", False),
    ],
)
def test_rejects_invalid_contract_version_target_and_draft_only(
    tmp_path: Path, field: str, value: object
) -> None:
    payload = valid_input()
    payload[field] = value
    assert validate(tmp_path, payload).returncode != 0


def test_rejects_source_issue_from_another_repository(tmp_path: Path) -> None:
    payload = valid_input()
    payload["source_issue"] = {
        "repository": "Young-Consultations/another-repository",
        "number": 42,
    }
    assert validate(tmp_path, payload).returncode != 0


@pytest.mark.parametrize("correlation_id", ["correlation\nissue=999", "correlation\rissue=999"])
def test_rejects_multiline_correlation_id(tmp_path: Path, correlation_id: str) -> None:
    payload = valid_input()
    payload["correlation_id"] = correlation_id
    assert validate(tmp_path, payload).returncode != 0


def test_canonical_result_artifact_and_comment(tmp_path: Path) -> None:
    result = tmp_path / "result.json"
    command = [
        "bash", str(SCRIPT), "write-result", str(result), "failed", "correlation-1", "", "",
        "https://github.com/Young-Consultations/portfolio-tasks/actions/runs/1",
        "failed", "not_run", "validation_failed", "Repository validation failed.",
        "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z",
    ]
    subprocess.run(command, check=True)
    payload = json.loads(result.read_text())
    assert set(payload) == {
        "contract_version", "correlation_id", "execution_status", "target_repository",
        "branch_name", "pull_request_url", "workflow_url", "validation_result", "test_result",
        "failure_category", "failure_message", "started_at", "completed_at",
    }
    comment = subprocess.run(
        ["bash", str(SCRIPT), "comment", str(result)], check=True, text=True, capture_output=True
    ).stdout
    assert "<!-- codex-execution-result:correlation-1 -->" in comment
    assert "Validation: failed" in comment
    assert "Repository validation failed" not in comment


def test_workflow_security_and_failure_scenarios() -> None:
    text = WORKFLOW.read_text()
    assert "pull_request_target:" not in text
    assert "python -m portfolio_tasks.run_codex" in text
    assert "status:approved" in text and 'state == \\"open\\"' not in text
    assert '.state == "open"' in text  # unapproved/closed issues are rejected immediately before Codex
    assert "no_changes" in text  # the wrapper's exhausted retry is categorized canonically
    assert "validation_failed" in text and "tests_failed" in text
    assert "draft:true" in text
    assert "pulls?state=all&head=" in text  # duplicate PR prevention precedes publication
    assert "actions/upload-artifact@v4" in text
    assert "/comments" in text
    assert "merge" not in {line.strip() for line in text.splitlines()}
    assert "EXECUTION_INPUT_ARTIFACT: ${{ inputs.execution_input_artifact }}" in text
    assert '[[ -z "$EXECUTION_INPUT_ARTIFACT" ]]' in text
    assert '[[ -z "${{ inputs.execution_input_artifact }}" ]]' not in text
