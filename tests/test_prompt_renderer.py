"""Focused tests for execution prompt rendering."""

from pathlib import Path

import pytest

from portfolio_tasks.prompts import renderer


def test_replaces_all_placeholders(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        renderer,
        "_load_execution_template",
        lambda: "{{repository_context}}|{{task_instructions}}|{{validation_commands}}",
    )

    result = renderer.render_execution_prompt(
        task_instructions="implement it",
        repository_context="repository details",
        validation_commands=["ruff check .", "pytest"],
    )

    assert result == "repository details|implement it|ruff check .\npytest"
    assert "{{" not in result


def test_renders_multiline_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        renderer,
        "_load_execution_template",
        lambda: "Context:\n{{repository_context}}\nTask:\n{{task_instructions}}",
    )

    result = renderer.render_execution_prompt(
        task_instructions="first step\nsecond step",
        repository_context="line one\nline two",
        validation_commands=[],
    )

    assert result == (
        "Context:\nline one\nline two\nTask:\nfirst step\nsecond step"
    )


def test_empty_repository_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        renderer,
        "_load_execution_template",
        lambda: "before{{repository_context}}after",
    )

    assert renderer.render_execution_prompt(
        task_instructions="",
        repository_context="",
        validation_commands=[],
    ) == "beforeafter"


def test_validation_commands_preserve_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        renderer,
        "_load_execution_template",
        lambda: "{{validation_commands}}",
    )

    result = renderer.render_execution_prompt(
        task_instructions="",
        repository_context="",
        validation_commands=["ruff check .", "mypy portfolio_tasks", "pytest"],
    )

    assert result == "ruff check .\nmypy portfolio_tasks\npytest"


def test_rendering_is_deterministic() -> None:
    arguments = {
        "task_instructions": "Do the task.",
        "repository_context": "",
        "validation_commands": [],
    }

    assert renderer.render_execution_prompt(**arguments) == renderer.render_execution_prompt(
        **arguments
    )


def test_rendered_prompt_contains_required_sections() -> None:
    result = renderer.render_execution_prompt(
        task_instructions="Canonical task instructions.",
        repository_context="Repository details.",
        validation_commands=["ruff check .", "pytest"],
    )

    required_sections = [
        "# Execution Contract",
        "## Repository Context",
        "## Task",
        "## Implementation Requirements",
        "## Validation",
        "## Final Acceptance-Criteria Review",
        "## Completion Report",
    ]
    for section in required_sections:
        assert section in result


def test_rendered_prompt_contains_execution_requirements() -> None:
    task_instructions = "Canonical task instructions."

    result = renderer.render_execution_prompt(
        task_instructions=task_instructions,
        repository_context="Repository details.",
        validation_commands=["pytest"],
    )

    required_language = [
        "Restate the objective",
        "Identify the root problem",
        "Extract every acceptance criterion",
        "Map every acceptance criterion",
        "Identify the files expected to change",
        "smallest coherent set of changes",
        "Preserve repository architecture",
        "Add or update tests",
        "Run the following validation commands",
        "review every extracted acceptance criterion",
        "broad refactoring",
        "unrelated cleanup",
        "symptoms",
        "Do not skip any acceptance criterion",
        "**Objective:**",
        "**Files changed:**",
        "**Tests:**",
        "**Acceptance criteria satisfied:**",
        "**Unresolved items:**",
    ]
    for requirement in required_language:
        assert requirement in result
    assert result.count(task_instructions) == 1


def test_template_loading_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class MissingTemplate:
        def joinpath(self, filename: str) -> Path:
            return Path("/template-does-not-exist") / filename

    monkeypatch.setattr(renderer.resources, "files", lambda package: MissingTemplate())

    with pytest.raises(FileNotFoundError):
        renderer.render_execution_prompt(
            task_instructions="task",
            repository_context="context",
            validation_commands=[],
        )
