"""Security and coverage contracts for GitHub Actions workflows."""

from pathlib import Path

import yaml

PR_WORKFLOW = Path(".github/workflows/ci.yml")
EXECUTION_WORKFLOW = Path(".github/workflows/codex-execute.yml")


def load(path: Path) -> dict[object, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def triggers(workflow: dict[object, object]) -> dict[object, object]:
    # YAML 1.1 parsers interpret the Actions key `on` as boolean true.
    value = workflow.get("on", workflow.get(True))
    assert isinstance(value, dict)
    return value


def test_pr_trigger_runs_for_every_path() -> None:
    workflow = load(PR_WORKFLOW)
    event = triggers(workflow)
    assert "pull_request" in event
    assert "pull_request_target" not in event
    assert event["pull_request"] is None


def test_pr_ci_is_offline_and_runs_every_required_check() -> None:
    text = PR_WORKFLOW.read_text(encoding="utf-8")
    workflow = load(PR_WORKFLOW)
    jobs = workflow["jobs"]
    assert set(jobs) >= {
        "python-tests",
        "workflow-contracts",
        "actionlint",
        "wrapper-integration",
        "stubbed-e2e",
    }
    for command in (
        "ruff check .",
        "ruff format --check ",
        "python -m pytest",
        "bash -n",
        "actionlint",
        "tests/e2e/run_stubbed_codex_workflow.sh",
    ):
        assert command in text
    assert "@openai/codex" not in text
    assert "secrets.OPENAI_API_KEY" not in text
    assert "secrets.CODEX_API_KEY" not in text
    assert "pull_request_target" not in text


def test_actionlint_and_shell_validation_commands_are_yaml_safe_and_scoped() -> None:
    workflow = load(PR_WORKFLOW)
    steps = workflow["jobs"]["actionlint"]["steps"]
    commands = [step["run"].strip() for step in steps if "run" in step]
    assert '"$(go env GOPATH)/bin/actionlint" -shellcheck=' in commands
    shell_validation = next(command for command in commands if command.startswith("find "))
    assert "-name '*.sh'" in shell_validation
    assert "-path 'scripts/prepare-task-branch'" in shell_validation
    assert "-path 'scripts/publish-draft-pr'" in shell_validation
    assert shell_validation.endswith("-print0 | xargs -0 -r -n1 bash -n")
    assert "-path 'scripts/*'" not in shell_validation


def test_wrapper_unit_tests_do_not_receive_a_global_fixture_override() -> None:
    workflow = load(PR_WORKFLOW)
    steps = workflow["jobs"]["wrapper-integration"]["steps"]
    pytest_step = next(step for step in steps if step.get("run", "").startswith("python -m pytest"))
    assert "env" not in pytest_step


def test_trusted_execution_workflow_contract() -> None:
    text = EXECUTION_WORKFLOW.read_text(encoding="utf-8")
    workflow = load(EXECUTION_WORKFLOW)
    assert set(triggers(workflow)) == {"workflow_dispatch"}
    assert "Verify router authorization" in text
    assert "Executor publication preflight" in text
    assert "python -m portfolio_tasks.execution publication-preflight" in text
    assert 'index("status:approved")' in text
    assert "continue-on-error" not in text
    assert "- name: Prepare full execution diagnostics\n        if: always()" in text
    assert "validate_completion_result" not in text  # validation occurs in the wrapper
    assert "tree_changed=false" in text
    assert '"$codex_outcome" == changed && "$tree_changed" == true' in text
    assert "python -m portfolio_tasks.run_codex" in text
