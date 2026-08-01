from pathlib import Path
from typing import Any

import pytest

from portfolio_tasks import projects_sync
from portfolio_tasks.models import Issue


def phase2_body(**changes: str) -> str:
    values = {
        "Project": "slugger",
        "Priority": "P1",
        "Executor": "codex",
        "Execution status": "approved",
        "Target repository": "Young-Consultations/slugger",
        "Parallel-safe": "no",
        "Dependency issue references": "#9, Young-Consultations/slugger#7",
        "Risk": "medium",
        "Estimated scope": "small",
        "Task type": "Feature",
    }
    values.update(changes)
    return "\n\n".join(f"### {name}\n\n{value}" for name, value in values.items())


def source_issue(**changes: object) -> Issue:
    values = {
        "number": 42,
        "title": "Sync me",
        "body": phase2_body(),
        "state": "open",
        "labels": ("chatgpt-task",),
        "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/42",
    }
    values.update(changes)
    return Issue(**values)  # type: ignore[arg-type]


def definitions() -> dict[str, projects_sync.ProjectFieldDefinition]:
    return {
        "Project": projects_sync.ProjectFieldDefinition(
            field_id="f-project",
            name="Project",
            kind="single-select",
            options={"slugger": "o-project-slugger", "consulting": "o-project-consulting"},
        ),
        "Priority": projects_sync.ProjectFieldDefinition(
            field_id="f-priority",
            name="Priority",
            kind="single-select",
            options={"P0": "o-p0", "P1": "o-p1", "P2": "o-p2", "P3": "o-p3"},
        ),
        "Executor": projects_sync.ProjectFieldDefinition(
            field_id="f-executor",
            name="Executor",
            kind="single-select",
            options={
                "codex": "o-executor-codex",
                "human": "o-executor-human",
                "chatgpt-planning": "o-executor-chatgpt-planning",
            },
        ),
        "Execution status": projects_sync.ProjectFieldDefinition(
            field_id="f-status",
            name="Execution status",
            kind="single-select",
            options={
                "proposed": "o-status-proposed",
                "approved": "o-status-approved",
                "queued": "o-status-queued",
                "running": "o-status-running",
                "draft-pr": "o-status-draft-pr",
                "blocked": "o-status-blocked",
                "done": "o-status-done",
            },
        ),
        "Target repository": projects_sync.ProjectFieldDefinition(
            field_id="f-target-repository",
            name="Target repository",
            kind="text",
            options={},
        ),
        "Parallel-safe": projects_sync.ProjectFieldDefinition(
            field_id="f-parallel",
            name="Parallel-safe",
            kind="single-select",
            options={"yes": "o-parallel-yes", "no": "o-parallel-no"},
        ),
        "Dependency issue references": projects_sync.ProjectFieldDefinition(
            field_id="f-dependencies",
            name="Dependency issue references",
            kind="text",
            options={},
        ),
        "Risk": projects_sync.ProjectFieldDefinition(
            field_id="f-risk",
            name="Risk",
            kind="single-select",
            options={"low": "o-risk-low", "medium": "o-risk-medium", "high": "o-risk-high"},
        ),
        "Estimated scope": projects_sync.ProjectFieldDefinition(
            field_id="f-scope",
            name="Estimated scope",
            kind="single-select",
            options={
                "small": "o-scope-small",
                "medium": "o-scope-medium",
                "large": "o-scope-large",
            },
        ),
        "Task type": projects_sync.ProjectFieldDefinition(
            field_id="f-task-type",
            name="Task type",
            kind="single-select",
            options={
                "Bug fix": "o-type-bug-fix",
                "Feature": "o-type-feature",
                "Refactor": "o-type-refactor",
                "CI/CD": "o-type-ci-cd",
                "Documentation": "o-type-documentation",
                "Security": "o-type-security",
                "Repository governance": "o-type-repository-governance",
                "Automation": "o-type-automation",
                "Investigation": "o-type-investigation",
            },
        ),
    }


def test_desired_field_values_normalize_dependencies() -> None:
    desired, errors = projects_sync.desired_field_values(source_issue())
    assert not errors
    assert desired["Dependency issue references"] == "#9 Young-Consultations/slugger#7"


def test_desired_field_values_reject_invalid_project() -> None:
    desired, errors = projects_sync.desired_field_values(source_issue(body=phase2_body(Project="Slugger")))
    assert desired["Project"] == "Slugger"
    assert errors == ("Project must be a lowercase project key",)


def test_plan_updates_is_deterministic_and_idempotent() -> None:
    desired, errors = projects_sync.desired_field_values(source_issue())
    assert not errors

    no_changes, plan_errors = projects_sync.plan_updates(desired, desired, definitions())
    assert not plan_errors
    assert no_changes == ()

    current = dict(desired)
    current["Priority"] = "P2"
    current["Risk"] = "low"
    current["Task type"] = "Refactor"
    updates, plan_errors = projects_sync.plan_updates(desired, current, definitions())
    assert not plan_errors
    assert [item.field_name for item in updates] == ["Priority", "Risk", "Task type"]


def test_sync_projects_phase2_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")

    monkeypatch.setattr(
        projects_sync,
        "_build_rest_api",
        lambda token, dry_run: (_ for _ in ()).throw(AssertionError("rest API should not be used")),
    )

    assert projects_sync.sync_projects_phase2() == 0
    output = summary.read_text(encoding="utf-8")
    assert "- Planned/completed action: `disabled`" in output
    assert "- Final synchronization result: `success`" in output


def test_sync_projects_phase2_enabled_requires_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("PROJECTS_PHASE2_SYNC_ENABLED", "true")
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")

    monkeypatch.setattr(
        projects_sync,
        "_build_rest_api",
        lambda token, dry_run: (_ for _ in ()).throw(AssertionError("rest API should not be used")),
    )

    assert projects_sync.sync_projects_phase2() == 1
    output = summary.read_text(encoding="utf-8")
    assert "PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE must be true" in output
    assert "PROJECTS_PHASE2_PROJECT_ID is required" in output
    assert "PROJECTS_PHASE2_TOKEN is required" in output


def test_sync_projects_phase2_noop_is_idempotent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class FakeRestApi:
        def request(
            self, method: str, endpoint: str, payload: dict[str, Any] | None = None
        ) -> dict[str, Any]:
            assert method == "GET"
            assert endpoint == "repos/Young-Consultations/portfolio-tasks/issues/42"
            assert payload is None
            return {
                "number": 42,
                "title": "Sync me",
                "body": phase2_body(),
                "state": "open",
                "labels": [{"name": "chatgpt-task"}],
                "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/42",
            }

    class FakeProjectsApi:
        def __init__(self) -> None:
            self.writes: list[str] = []

        def project_fields(self, project_id: str) -> dict[str, projects_sync.ProjectFieldDefinition]:
            assert project_id == "project-id"
            return definitions()

        def issue_snapshot(
            self, project_id: str, repository: str, number: int
        ) -> projects_sync.ProjectItemSnapshot:
            assert project_id == "project-id"
            assert repository == "Young-Consultations/portfolio-tasks"
            assert number == 42
            desired, errors = projects_sync.desired_field_values(source_issue())
            assert not errors
            return projects_sync.ProjectItemSnapshot(
                issue_node_id="I_42", item_id="ITEM_42", field_values=desired
            )

        def add_item(self, project_id: str, issue_node_id: str) -> str:
            raise AssertionError("add_item should not be called for idempotent no-op")

        def update_item_field(
            self, project_id: str, item_id: str, update: projects_sync.ProjectFieldUpdate
        ) -> None:
            self.writes.append(update.field_name)

    summary = tmp_path / "summary.md"
    fake_projects = FakeProjectsApi()
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("PROJECTS_PHASE2_SYNC_ENABLED", "true")
    monkeypatch.setenv("PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE", "true")
    monkeypatch.setenv("PROJECTS_PHASE2_PROJECT_ID", "project-id")
    monkeypatch.setenv("PROJECTS_PHASE2_TOKEN", "token")
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")

    monkeypatch.setattr(projects_sync, "_build_rest_api", lambda token, dry_run: FakeRestApi())
    monkeypatch.setattr(
        projects_sync,
        "_build_projects_api",
        lambda token, dry_run: fake_projects,
    )

    assert projects_sync.sync_projects_phase2() == 0
    assert fake_projects.writes == []
    output = summary.read_text(encoding="utf-8")
    assert "- Planned/completed action: `no-op`" in output

