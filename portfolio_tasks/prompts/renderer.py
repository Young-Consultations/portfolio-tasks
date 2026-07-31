"""Render prompts used by the task execution boundary."""

from __future__ import annotations

from importlib import resources
import re

_PROFILE_TEMPLATES = {
    "implementation": "execution.md",
}

_WORKFLOW_POSTCONDITION = re.compile(
    r"(?:\b(?:open(?:ed)?|create(?:d)?|push(?:ed)?|publish(?:ed)?|post(?:ed)?|update(?:d)?)\b.*\b(?:draft\s+)?(?:pull request|pr|branch|source issue|workflow url)\b|\b(?:draft\s+)?(?:pull request|pr|branch)\b.*\b(?:open(?:ed)?|create(?:d)?|push(?:ed)?|publish(?:ed)?)\b)",
    re.IGNORECASE,
)


def _separate_responsibilities(task: str) -> tuple[str, str]:
    """Move publication bullets out of the criteria Codex must satisfy."""
    implementation: list[str] = []
    postconditions: list[str] = []
    for line in task.splitlines():
        if _WORKFLOW_POSTCONDITION.search(line):
            postconditions.append(line.strip().lstrip("-* "))
        else:
            implementation.append(line)
    rendered = "\n".join(f"- {item}" for item in postconditions)
    return "\n".join(implementation).strip(), rendered or "- None specified."


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
    implementation, postconditions = _separate_responsibilities(task_instructions)
    replacements = {
        "{{repository_context}}": repository_context,
        "{{task_instructions}}": implementation,
        "{{workflow_postconditions}}": postconditions,
        "{{validation_commands}}": "\n".join(validation_commands),
    }
    rendered = _load_execution_template(profile)
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered
