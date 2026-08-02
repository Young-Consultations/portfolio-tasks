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
        "SLUGGER_GITHUB_TOKEN",
        "read access to issues",
        "read and write access to organization Projects",
        "Portfolio Tasks - Phase 1",
        "Young-Consultations/portfolio-tasks",
        "Young-Consultations/slugger",
        "already in the project",
    ):
        assert required in text


def test_intake_workflow_uses_exact_label_trigger_and_router_token() -> None:
    workflow = _workflow()
    triggers = _triggers(workflow)
    assert set(triggers) == {"issues"}
    assert triggers["issues"] == {"types": ["labeled"]}
    assert workflow["permissions"] == {"contents": "read"}

    route = workflow["jobs"]["route"]
    assert route["if"] == "github.event.label.name == 'chatgpt-task'"
    validation_step = route["steps"][0]
    assert validation_step["env"] == {"GH_TOKEN": "${{ secrets.SLUGGER_GITHUB_TOKEN }}"}
    assert "SLUGGER_GITHUB_TOKEN is unavailable" in validation_step["run"]
    intake_step = route["steps"][-1]
    assert intake_step["env"] == {"GH_TOKEN": "${{ secrets.SLUGGER_GITHUB_TOKEN }}"}
    assert intake_step["run"] == "python -m portfolio_tasks.project_intake"
    assert len(route["steps"]) == 3
    assert [step.get("uses") for step in route["steps"] if "uses" in step] == [
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
    ]


def test_project_router_does_not_modify_execution_or_router_workflows() -> None:
    route_text = Path(".github/workflows/route-approved-task.yml").read_text(encoding="utf-8")
    execute_text = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")

    assert "project_intake" not in route_text
    assert "project_intake" not in execute_text
