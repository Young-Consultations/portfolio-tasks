"""Render prompts used by the task execution boundary."""

from __future__ import annotations
import re
from importlib import resources

_PROFILE_TEMPLATES = {
    "implementation": "execution.md",
}

_WORKFLOW_POSTCONDITION = re.compile(
    r"""(?:
        (?:one|a|an|the)?\s*(?:focused\s+)?draft\s+(?:pull\s+request|pr)\s+
            (?:is|will\s+be|must\s+be|should\s+be)\s+(?:opened|created|published)\b.*
        |(?:open|create|publish)\s+(?:one|a|an|the)?\s*(?:focused\s+)?draft\s+
            (?:pull\s+request|pr)\b.*
        |(?:changes|commits)\s+(?:are|will\s+be|must\s+be|should\s+be)\s+pushed\b.*
        |push\s+(?:the\s+)?(?:changes|commits)\b.*
        |(?:one|a|an|the)?\s*(?:task|feature|implementation)\s+branch\s+
            (?:is|will\s+be|must\s+be|should\s+be)\s+(?:created|pushed)\b.*
        |(?:the\s+)?source\s+issue\s+(?:is|will\s+be|must\s+be|should\s+be)\s+
            (?:updated|posted\s+to)\b.*(?:workflow\s+url|pull\s+request|draft\s+pr)\b.*
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def _separate_responsibilities(task: str) -> tuple[str, str]:
    """Move publication bullets out of the criteria Codex must satisfy."""
    implementation: list[str] = []
    postconditions: list[str] = []
    for line in task.splitlines():
        indentation = line[: len(line) - len(line.lstrip())]
        content = line.strip()
        bullet = ""
        if content.startswith(("- ", "* ")):
            bullet, content = content[:2], content[2:]

        implementation_clauses: list[str] = []
        for clause in (item.strip() for item in content.split(";")):
            if clause and _WORKFLOW_POSTCONDITION.fullmatch(clause):
                postconditions.append(clause)
            elif clause:
                implementation_clauses.append(clause)

        if implementation_clauses:
            implementation.append(f"{indentation}{bullet}{'; '.join(implementation_clauses)}")
        elif not content:
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
