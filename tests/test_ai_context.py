import re
from pathlib import Path

AI_CONTEXT_PATH = Path("AI_CONTEXT.md")


def _ai_context_text() -> str:
    return AI_CONTEXT_PATH.read_text(encoding="utf-8")


def test_ai_context_has_required_sections_exactly_once_in_order() -> None:
    text = _ai_context_text()
    sections = [
        "## Vision",
        "## Current project state",
        "## Architecture",
        "## Coding standards",
        "## ADRs",
        "## Development workflow",
        "## Prompt rules",
        "## Open issues",
    ]

    positions = []
    for section in sections:
        matches = list(re.finditer(rf"^{re.escape(section)}$", text, re.MULTILINE))
        assert len(matches) == 1, f"Expected exactly one section: {section}"
        positions.append(matches[0].start())

    assert positions == sorted(positions), "Required sections are out of order"


def test_ai_context_states_portfolio_tasks_as_backlog_and_approval_source() -> None:
    text = _ai_context_text()
    assert "Young-Consultations/portfolio-tasks" in text
    assert "source of truth" in text
    assert "`Executor` must be `codex`" in text
    assert "adding `status:approved` is the only approval action" in text
    assert "issue body contains no second execution-status authority" in text


def test_ai_context_relative_links_resolve_or_gap_is_declared() -> None:
    text = _ai_context_text()
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert links

    for link in links:
        if link.startswith(("http://", "https://", "mailto:")):
            continue

        target = link.split("#", 1)[0]
        if not target:
            continue

        assert Path(target).exists(), f"Broken relative link: {link}"
