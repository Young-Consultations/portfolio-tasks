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


def test_phase2_documentation_covers_prerequisite_and_operations() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "Phase 1 issue `#17` must be complete and merged" in text
    assert "PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE=true" in text
    assert "PROJECTS_PHASE2_SYNC_ENABLED=true" in text
    assert "PROJECTS_PHASE2_PROJECT_ID" in text
    assert "PROJECTS_PHASE2_TOKEN" in text
    assert "Least-privilege boundary" in text
    for section in ("Enable:", "Disable:", "Rollback:", "Operation:", "Troubleshooting:"):
        assert section in text


def test_phase2_workflow_is_optional_and_least_privilege() -> None:
    workflow = _workflow()
    triggers = _triggers(workflow)
    assert set(triggers) == {"issues", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read", "issues": "read"}

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    sync = jobs["sync-projects-phase2"]
    assert isinstance(sync, dict)
    env = sync["env"]
    assert isinstance(env, dict)
    assert env["PROJECTS_PHASE2_SYNC_ENABLED"] == "${{ vars.PROJECTS_PHASE2_SYNC_ENABLED || 'false' }}"
    assert (
        env["PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE"]
        == "${{ vars.PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE || 'false' }}"
    )
    assert env["PROJECTS_PHASE2_PROJECT_ID"] == "${{ vars.PROJECTS_PHASE2_PROJECT_ID || '' }}"
    assert env["PROJECTS_PHASE2_TOKEN"] == "${{ secrets.PROJECTS_PHASE2_TOKEN }}"

    steps = sync["steps"]
    assert isinstance(steps, list)
    run_commands = [step["run"] for step in steps if isinstance(step, dict) and "run" in step]
    assert "python -m portfolio_tasks.cli sync-projects-phase2" in run_commands


def test_phase2_sync_does_not_modify_execution_or_router_workflows() -> None:
    route_text = Path(".github/workflows/route-approved-task.yml").read_text(encoding="utf-8")
    execute_text = Path(".github/workflows/codex-execute.yml").read_text(encoding="utf-8")

    assert "sync-projects-phase2" not in route_text
    assert "PROJECTS_PHASE2_SYNC_ENABLED" not in route_text
    assert "sync-projects-phase2" not in execute_text
    assert "PROJECTS_PHASE2_SYNC_ENABLED" not in execute_text
