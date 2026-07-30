"""Render prompts used by the task execution boundary."""

from __future__ import annotations

from importlib import resources

_PROFILE_TEMPLATES = {
    "implementation": "execution.md",
}


def _load_execution_template(profile: str) -> str:
    """Load the packaged execution prompt template for a supported profile."""
    try:
        template = _PROFILE_TEMPLATES[profile]
    except KeyError as error:
        raise ValueError(f"Unsupported execution profile: {profile}") from error
    return resources.files(__package__).joinpath(template).read_text(encoding="utf-8")


def render_execution_prompt(
    *,
    profile: str = "implementation",
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
    rendered = _load_execution_template(profile)
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered
