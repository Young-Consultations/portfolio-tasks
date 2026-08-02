import re
from pathlib import Path

AI_CONTEXT_PATH = Path("AI_CONTEXT.md")


def _ai_context_text() -> str:
    return AI_CONTEXT_PATH.read_text(encoding="utf-8")


def test_ai_context_has_required_sections_in_order() -> None:
    text = _ai_context_text()
    sections = [
        "## 1. Repository mission",
        "## 2. Backlog and approval source of truth",
        "## 3. Execution gate and routing boundaries",
        "## 4. Canonical contract documents",
        "## 5. Repository map for contributors",
        "## 6. Validation and documentation checks",
        "## 7. Safety and change constraints",
        "## 8. Documented gaps",
    ]

    cursor = 0
    for section in sections:
        index = text.find(section, cursor)
        assert index != -1, f"Missing required section: {section}"
        cursor = index + len(section)


def test_ai_context_states_portfolio_tasks_as_backlog_and_approval_source() -> None:
    text = _ai_context_text()
    assert "Young-Consultations/portfolio-tasks" in text
    assert "source of truth" in text
    assert "`Executor` must be `codex`" in text
    assert "`Execution status` must be `approved`" in text


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
