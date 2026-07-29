from pathlib import Path
from typing import Any

import pytest

from portfolio_tasks import cli
from portfolio_tasks.github_api import GitHubApiError
from tests.helpers import SLUGGER_ISSUE_BODY


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
                "body": SLUGGER_ISSUE_BODY,
                "state": "open",
                "labels": [{"name": "chatgpt-task"}],
                "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/42",
            }
        return []


class RecordingApi:
    def __init__(self, body: str) -> None:
        self.body = body
        self.calls: list[tuple[str, str]] = []

    def request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> Any:
        self.calls.append((method, endpoint))
        if len(self.calls) == 1:
            return {
                "number": 42,
                "title": "Task",
                "body": self.body,
                "state": "open",
                "labels": [{"name": "chatgpt-task"}],
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


@pytest.mark.parametrize(
    "body",
    [
        SLUGGER_ISSUE_BODY.replace(
            "Young-Consultations/slugger", "Young-Consultations/portfolio-tasks"
        ),
        SLUGGER_ISSUE_BODY.replace(
            "Young-Consultations/slugger", "Young-Consultations/consulting-playbook"
        ),
        "No target field",
        SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", "`bad target`"),
    ],
    ids=["portfolio-tasks", "consulting-playbook", "missing", "malformed"],
)
def test_sync_skips_non_slugger_target_without_target_api_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, body: str
) -> None:
    summary = tmp_path / "summary.md"
    api = RecordingApi(body)
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cli, "_api", lambda dry_run: api)

    assert cli.sync() == 0
    assert api.calls == [("GET", "repos/Young-Consultations/portfolio-tasks/issues/42")]
    assert "- Planned/completed action: `skipped-target-repository`" in summary.read_text(
        encoding="utf-8"
    )


def test_route_check_duplicate_delivery_is_noop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    event = {
        "issue": {
            "number": 42,
            "title": "Approved work",
            "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
            "state": "open",
            "labels": [{"name": "chatgpt-task"}, {"name": "executor:codex"}, {"name": "status:approved"}],
        }
    }
    event_file = tmp_path / "event.json"
    event_file.write_text(__import__("json").dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_DELIVERY", "delivery-1")
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))

    assert cli.main(["route-check", str(event_file)]) == 0
    first = capsys.readouterr().out
    assert "route=true" in first

    assert cli.main(["route-check", str(event_file)]) == 0
    second = capsys.readouterr().out
    assert "route=false" in second
    assert "reason=duplicate-delivery" in second
