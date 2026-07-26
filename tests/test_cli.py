from pathlib import Path
from typing import Any

import pytest

from portfolio_tasks import cli
from portfolio_tasks.github_api import GitHubApiError


class FailingApi:
    def __init__(self, fail_on: int) -> None:
        self.fail_on = fail_on
        self.calls = 0

    def request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> Any:
        self.calls += 1
        if self.calls == self.fail_on:
            raise GitHubApiError("request rejected")
        if self.calls == 1:
            return {
                "number": 42,
                "title": "Task",
                "body": "Details",
                "state": "open",
                "labels": [{"name": "chatgpt-task"}],
                "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/42",
            }
        return []


@pytest.mark.parametrize("fail_on", [1, 3], ids=["source-get", "create-request"])
def test_sync_reports_api_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fail_on: int
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cli, "_api", lambda dry_run: FailingApi(fail_on))

    assert cli.sync() == 1
    contents = summary.read_text(encoding="utf-8")
    assert "- API failures: GitHub API request failed" in contents
    assert "- Final synchronization result: `failed`" in contents
