import re
from pathlib import Path


def test_chatgpt_issue_form_contract() -> None:
    text = Path(".github/ISSUE_TEMPLATE/chatgpt-task.yml").read_text(encoding="utf-8")
    ids = set(re.findall(r"^\s+-?\s*id:\s*([a-z][a-z0-9_]*)\s*$", text, re.MULTILINE))
    required = {
        "project", "priority", "executor", "execution_status", "target_repository",
        "parallel_safe", "dependency_issue_references", "risk", "estimated_scope",
        "objective", "task_type", "required_behavior", "acceptance_criteria",
        "testing_requirements", "security_constraints",
    }
    assert required <= ids
    assert re.search(r"^labels:\s*\n\s*-\s*chatgpt-task\s*$", text, re.MULTILINE)
    assert not re.search(r"^\s*-\s*codex-ready\s*$", text, re.MULTILINE)
    assert text.count("required: true") >= len(required)
