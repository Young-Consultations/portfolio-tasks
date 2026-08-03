"""Tests for deterministic executor publication preflight decisions."""

import pytest

from portfolio_tasks import execution

PR_URL = "https://github.com/Young-Consultations/portfolio-tasks/pull/42"


def test_open_draft_pr_is_reused_without_running_codex() -> None:
    result = execution.publication_preflight_decision(
        publication_key="Young-Consultations/portfolio-tasks:codex/task-42",
        pulls=[{"state": "open", "draft": True, "html_url": PR_URL}],
        branch_exists=True,
    )
    assert result == {
        "should_run_codex": "false",
        "reuse_open_draft": "true",
        "publish_ok": "true",
        "pr_url": PR_URL,
    }


def test_open_non_draft_pr_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a draft"):
        execution.publication_preflight_decision(
            publication_key="Young-Consultations/portfolio-tasks:codex/task-42",
            pulls=[{"state": "open", "draft": False, "html_url": PR_URL}],
            branch_exists=True,
        )


def test_multiple_open_prs_are_rejected() -> None:
    with pytest.raises(ValueError, match="found 2 open pull requests"):
        execution.publication_preflight_decision(
            publication_key="Young-Consultations/portfolio-tasks:codex/task-42",
            pulls=[
                {"state": "open", "draft": True, "html_url": PR_URL},
                {"state": "open", "draft": True, "html_url": f"{PR_URL}0"},
            ],
            branch_exists=True,
        )


def test_closed_or_merged_pr_blocks_reexecution() -> None:
    with pytest.raises(ValueError, match="closed or merged"):
        execution.publication_preflight_decision(
            publication_key="Young-Consultations/portfolio-tasks:codex/task-42",
            pulls=[{"state": "closed", "draft": False, "html_url": PR_URL}],
            branch_exists=True,
        )


def test_existing_branch_without_pr_is_blocked() -> None:
    with pytest.raises(ValueError, match="branch exists without an open draft"):
        execution.publication_preflight_decision(
            publication_key="Young-Consultations/portfolio-tasks:codex/task-42",
            pulls=[],
            branch_exists=True,
        )


def test_preflight_allows_codex_for_new_publication_identity() -> None:
    assert execution.publication_preflight_decision(
        publication_key="Young-Consultations/portfolio-tasks:codex/task-42",
        pulls=[],
        branch_exists=False,
    ) == {
        "should_run_codex": "true",
        "reuse_open_draft": "false",
        "publish_ok": "false",
        "pr_url": "",
    }


def test_preflight_outputs_require_github_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    with pytest.raises(ValueError, match="GH_TOKEN must be set"):
        execution.publication_preflight_outputs(
            repository="Young-Consultations/portfolio-tasks",
            branch="codex/task-42",
            api_root="https://api.github.com",
        )


def test_preflight_outputs_include_publication_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(
        execution,
        "_list_publication_pulls",
        lambda **_: [{"state": "open", "draft": True, "html_url": PR_URL}],
    )
    monkeypatch.setattr(execution, "_publication_branch_exists", lambda **_: True)
    outputs = execution.publication_preflight_outputs(
        repository="Young-Consultations/portfolio-tasks",
        branch="codex/task-42",
        api_root="https://api.github.com",
    )
    assert outputs["publication_identity"] == "Young-Consultations/portfolio-tasks:codex/task-42"
    assert outputs["reuse_open_draft"] == "true"
    assert outputs["pr_url"] == PR_URL

