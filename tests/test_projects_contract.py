from pathlib import Path

import yaml

DOC_PATH = Path("docs/github-projects-sync.md")
WORKFLOW_PATH = Path(".github/workflows/sync-github-projects.yml")


def _workflow() -> dict[object, object]:
    value = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _triggers(workflow: dict[object, object]) -> dict[object, object]:
    value = workflow.get("on", workflow.get(True))
    assert isinstance(value, dict)
    return value


def test_intake_documentation_covers_credentials_and_permissions() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    for required in (
        "PROJECT_ROUTER_APP_ID",
        "PROJECT_ROUTER_APP_PRIVATE_KEY",
        "Issues: Read-only",
        "Projects: Read and write",
        "Portfolio Tasks - Phase 1",
        "already in the project",
    ):
        assert required in text


def test_intake_workflow_uses_exact_label_trigger_and_least_privilege() -> None:
    workflow = _workflow()
    triggers = _triggers(workflow)
    assert set(triggers) == {"issues"}
    assert triggers["issues"] == {"types": ["labeled"]}
    assert workflow["permissions"] == {"contents": "read"}

    route = workflow["jobs"]["route"]
    assert route["if"] == "github.event.label.name == 'chatgpt-task'"
    token_step = next(step for step in route["steps"] if step.get("id") == "app-token")
    assert token_step["with"]["permission-issues"] == "read"
    assert token_step["with"]["permission-organization-projects"] == "write"
    assert token_step["with"]["repositories"] == "portfolio-tasks"
    assert route["steps"][-1]["run"] == "python -m portfolio_tasks.project_intake"


def test_project_router_does_not_modify_execution_or_router_workflows() -> None:
    route_text = Path(".github/workflows/route-approved-task.yml").read_text(encoding="utf-8")
    execute_text = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")

    assert "project_intake" not in route_text
    assert "PROJECT_ROUTER_APP_ID" not in route_text
    assert "project_intake" not in execute_text
    assert "PROJECT_ROUTER_APP_ID" not in execute_text
