"""Security and scope checks for the sole active GitHub Actions workflow."""

import re
from pathlib import Path

WORKFLOW_DIRECTORY = Path(".github/workflows")
CI_WORKFLOW = WORKFLOW_DIRECTORY / "ci.yml"


def test_ci_is_the_only_active_workflow() -> None:
    assert tuple(WORKFLOW_DIRECTORY.glob("*.yml")) == (CI_WORKFLOW,)


def test_ci_has_no_execution_or_cross_repository_side_effects() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in text
    assert "pull_request_target" not in text
    for forbidden in (
        "workflow_dispatch",
        "repository_dispatch",
        "@openai/codex",
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "SLUGGER_",
        "gh api",
        "git push",
    ):
        assert forbidden not in text


def test_actions_are_pinned_and_checkout_does_not_persist_credentials() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    references = re.findall(r"^\s*- uses: ([^\s#]+)", text, re.MULTILINE)
    assert references
    for uses in references:
        _, separator, reference = uses.rpartition("@")
        assert separator and re.fullmatch(r"[0-9a-f]{40}", reference)
    assert text.count("actions/checkout@") == text.count("persist-credentials: false")
