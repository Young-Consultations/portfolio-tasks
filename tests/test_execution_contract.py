"""Contract tests for the controlled canonical execution workflow."""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path("scripts/execution-contract.sh")
WORKFLOW = Path(".github/workflows/codex-execute.yml")

ROUTER_SMOKE_PAYLOAD: dict[str, object] = {
    "concurrency_group": (
        "codex-young-consultations-portfolio-tasks-young-consultations-"
        "portfolio-tasks-17-parallel-router-smoke-002"
    ),
    "contract_version": "ai-sdlc-contract/v1",
    "correlation_id": "router-smoke-002",
    "draft_pr_only": True,
    "executor": "codex",
    "instructions": "Perform a non-production router smoke test.",
    "parallel_safe": True,
    "priority": "p1",
    "project": "portfolio",
    "requested_branch": "codex/router-smoke-002",
    "source_issue": "Young-Consultations/portfolio-tasks#17",
    "target_repository": "Young-Consultations/portfolio-tasks",
    "task_type": "documentation",
    "timeout_minutes": 60,
}


@pytest.fixture
def contract_environment(tmp_path: Path) -> dict[str, str]:
    """Provide a test double for the separately distributed shared validator."""
    package = tmp_path / "ai_sdlc_contracts"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "__main__.py").write_text(
        """import json, sys
p = json.load(open(sys.argv[2]))
command = sys.argv[1]
valid = p.get('contract_version') == 'ai-sdlc-contract/v1'
if command == 'validate-input':
    valid &= isinstance(p.get('source_issue'), str)
    valid &= p.get('target_repository') == 'Young-Consultations/portfolio-tasks'
    valid &= p.get('executor') == 'codex' and p.get('draft_pr_only') is True
elif command == 'validate-result':
    valid &= p.get('execution_status') in ('succeeded', 'failed')
    valid &= p.get('validation_result') in ('passed', 'failed', 'not_run')
    valid &= p.get('test_result') in ('passed', 'failed', 'not_run')
else:
    valid = False
raise SystemExit(0 if valid else 1)
"""
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    return env


def run_contract(
    tmp_path: Path,
    contract_environment: dict[str, str],
    payload: dict[str, object],
    command: str = "validate-input",
) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload))
    return subprocess.run(
        ["bash", str(SCRIPT), command, str(path)],
        check=False,
        text=True,
        capture_output=True,
        env=contract_environment,
    )


def test_exact_router_smoke_payload_is_accepted(
    tmp_path: Path, contract_environment: dict[str, str]
) -> None:
    assert run_contract(tmp_path, contract_environment, ROUTER_SMOKE_PAYLOAD).returncode == 0


def test_canonical_source_issue_is_parsed(
    tmp_path: Path, contract_environment: dict[str, str]
) -> None:
    result = run_contract(
        tmp_path, contract_environment, ROUTER_SMOKE_PAYLOAD, "parse-source-issue"
    )
    assert result.returncode == 0
    assert result.stdout == "source_repository=Young-Consultations/portfolio-tasks\nissue=17\n"


@pytest.mark.parametrize(
    "source_issue",
    [
        {"repository": "Young-Consultations/portfolio-tasks", "number": 17},
        "Young-Consultations/another-repository#17",
        "Young-Consultations/portfolio-tasks#0",
        "Young-Consultations/portfolio-tasks#17?x=1",
        "Young-Consultations/portfolio-tasks#17#fragment",
        "https://github.com/Young-Consultations/portfolio-tasks/issues/17",
        "Young-Consultations/portfolio-tasks #17",
    ],
)
def test_rejects_noncanonical_source_issue(
    tmp_path: Path, contract_environment: dict[str, str], source_issue: object
) -> None:
    payload = dict(ROUTER_SMOKE_PAYLOAD, source_issue=source_issue)
    assert run_contract(tmp_path, contract_environment, payload).returncode != 0


def test_rejects_obsolete_contract_version(
    tmp_path: Path, contract_environment: dict[str, str]
) -> None:
    payload = dict(ROUTER_SMOKE_PAYLOAD, contract_version="ai-sdlc-execution-input/v1")
    assert run_contract(tmp_path, contract_environment, payload).returncode != 0


def test_result_is_accepted_by_shared_validator(
    tmp_path: Path, contract_environment: dict[str, str]
) -> None:
    result = tmp_path / "result.json"
    command = [
        "bash", str(SCRIPT), "write-result", str(result), "failed", "correlation-1", "", "",
        "https://github.com/Young-Consultations/portfolio-tasks/actions/runs/1",
        "failed", "not_run", "validation_failed", "Repository validation failed.",
        "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z",
    ]
    subprocess.run(command, check=True, env=contract_environment)
    payload = json.loads(result.read_text())
    assert payload["contract_version"] == "ai-sdlc-contract/v1"
    comment = subprocess.run(
        ["bash", str(SCRIPT), "comment", str(result)],
        check=True,
        text=True,
        capture_output=True,
        env=contract_environment,
    ).stdout
    assert "<!-- codex-execution-result:correlation-1 -->" in comment
    assert "Validation: failed" in comment
    assert "Repository validation failed" not in comment


def test_workflow_uses_shared_validator_and_preserves_security_gates() -> None:
    text = WORKFLOW.read_text()
    script = SCRIPT.read_text()
    assert "ai-sdlc-contracts==1.0.0" not in text
    assert "vars.AI_SDLC_CONTRACTS_COMMIT_SHA" in text
    assert re.search(r'CONTRACTS_COMMIT_SHA.*\^\[0-9a-f\]\{40\}\$', text)
    assert (
        'git+https://github.com/Young-Consultations/.github.git@${CONTRACTS_COMMIT_SHA}'
        in text
    )
    assert "git+https://x-access-token:" not in text
    assert "python -m ai_sdlc_contracts --help" in text
    assert "python -m ai_sdlc_contracts validate-input" in text
    assert "version('ai-sdlc-contracts') == '1.0.0'" in text
    assert "python -m ai_sdlc_contracts validate-input" in script
    assert ".source_issue.number" not in text and ".source_issue.repository" not in text
    assert "pull_request_target:" not in text
    assert "executor:codex" in text and "status:approved" in text
    assert '.state == "open"' in text and 'has("pull_request")' in text
    assert 'index("sensitive") == null' in text
    assert "draft:true" in text
    assert "merge" not in {line.strip() for line in text.splitlines()}


def test_obsolete_contract_constants_and_local_schema_copies_are_absent() -> None:
    repository_text = "\n".join(
        path.read_text() for path in [SCRIPT, WORKFLOW, Path("pyproject.toml")]
    )
    assert "ai-sdlc-execution-input/v1" not in repository_text
    assert "ai-sdlc-execution-result/v1" not in repository_text
    assert not Path("schemas/execution-input.schema.json").exists()
    assert not Path("schemas/execution-result.schema.json").exists()
