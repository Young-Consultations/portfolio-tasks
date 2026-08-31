import re
from pathlib import Path


def test_chatgpt_issue_form_contract() -> None:
    text = Path(".github/ISSUE_TEMPLATE/chatgpt-task.yml").read_text(encoding="utf-8")
    ids = set(re.findall(r"^\s+-?\s*id:\s*([a-z][a-z0-9_]*)\s*$", text, re.MULTILINE))
    required = {
        "project",
        "priority",
        "executor",
        "target_repository",
        "execution_mode",
        "sensitivity",
        "parallel_safe",
        "dependency_issue_references",
        "risk",
        "estimated_scope",
        "objective",
        "task_type",
        "required_behavior",
        "acceptance_criteria",
        "testing_requirements",
        "security_constraints",
    }
    assert required <= ids
    assert "execution_status" not in ids
    assert "Execution status" not in text
    assert re.search(r"^labels:\s*\n\s*-\s*chatgpt-task\s*$", text, re.MULTILINE)
    assert not re.search(r"^\s*-\s*codex-ready\s*$", text, re.MULTILINE)
    assert text.count("required: true") >= len(required)


def test_task_type_options_use_only_exact_contract_vocabulary() -> None:
    text = Path(".github/ISSUE_TEMPLATE/chatgpt-task.yml").read_text(encoding="utf-8")
    task_type = text.split("    id: task_type", 1)[1].split("    validations:", 1)[0]
    for option in (
        "Automation",
        "Backlog governance",
        "Bug fix",
        "CI/CD",
        "Documentation",
        "Feature",
        "Repository maintenance",
        "Security",
        "Testing",
    ):
        assert f"        - {option}\n" in task_type
    for obsolete in ("Refactor", "Repository governance", "Investigation"):
        assert f"        - {obsolete}\n" not in task_type
