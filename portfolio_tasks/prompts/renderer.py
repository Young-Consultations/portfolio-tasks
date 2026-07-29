"""Render prompts used by the task execution boundary."""

from __future__ import annotations

from importlib import resources

_EXECUTION_TEMPLATE = "execution.md"


def _load_execution_template() -> str:
    """Load the packaged execution prompt template."""
    return resources.files(__package__).joinpath(_EXECUTION_TEMPLATE).read_text(encoding="utf-8")


def render_execution_prompt(
    *,
    task_instructions: str,
    repository_context: str,
    validation_commands: list[str],
) -> str:
    """Render an execution prompt by replacing every supported placeholder."""
    replacements = {
        "{{repository_context}}": repository_context,
        "{{task_instructions}}": task_instructions,
        "{{validation_commands}}": "\n".join(validation_commands),
    }
    rendered = _load_execution_template()
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered
