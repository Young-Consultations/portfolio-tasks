import json
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


class SequencedIssueApi:
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        self.calls = 0

    def request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> Any:
        assert method == "GET"
        assert endpoint.startswith("repos/Young-Consultations/portfolio-tasks/issues/")
        assert payload is None
        if self.calls >= len(self.issues):
            return self.issues[-1]
        response = self.issues[self.calls]
        self.calls += 1
        return response


class UnexpectedApi:
    def request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> Any:
        raise AssertionError(
            f"unexpected API call: method={method}, endpoint={endpoint}, payload={payload}"
        )


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
        "action": "labeled",
        "label": {"name": "status:approved"},
        "issue": {
            "number": 42,
            "title": "Approved work",
            "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
            "state": "open",
            "labels": [{"name": "chatgpt-task"}, {"name": "executor:codex"}, {"name": "status:approved"}],
        }
    }
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_DELIVERY", "delivery-1")
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))

    assert cli.main(["route-check", str(event_file)]) == 0
    first = capsys.readouterr().out
    assert "route=true" in first

    assert cli.main(["route-check", str(event_file)]) == 0
    second = capsys.readouterr().out
    assert "route=false" in second
    assert "reason=duplicate-delivery" in second


def test_route_check_approval_label_routes_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    event = {
        "action": "labeled",
        "label": {"name": "status:approved"},
        "issue": {
            "number": 42,
            "title": "Approved work",
            "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
            "state": "open",
            "labels": [
                {"name": "chatgpt-task"},
                {"name": "executor:codex"},
                {"name": "status:approved"},
            ],
        },
    }
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event), encoding="utf-8")
    live_issue = {
        "number": 42,
        "title": "Approved work",
        "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
        "state": "open",
        "labels": [
            {"name": "chatgpt-task"},
            {"name": "executor:codex"},
            {"name": "status:approved"},
        ],
    }
    queued_issue = {
        "number": 42,
        "title": "Approved work",
        "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
        "state": "open",
        "labels": [
            {"name": "chatgpt-task"},
            {"name": "executor:codex"},
            {"name": "status:approved"},
            {"name": "status:queued"},
        ],
    }
    monkeypatch.setenv("GITHUB_REPOSITORY", "Young-Consultations/portfolio-tasks")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    api = SequencedIssueApi([live_issue, queued_issue])
    monkeypatch.setattr(cli, "_api", lambda dry_run=False: api)

    assert cli.main(["route-check", str(event_file)]) == 0
    first = capsys.readouterr().out
    assert "route=true" in first
    assert "reason=approved" in first

    assert cli.main(["route-check", str(event_file)]) == 0
    second = capsys.readouterr().out
    assert "route=false" in second
    assert "reason=already-dispatched" in second


def test_route_check_non_approval_label_does_not_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    event = {
        "action": "labeled",
        "label": {"name": "priority:P1"},
        "issue": {
            "number": 42,
            "title": "Approved work",
            "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
            "state": "open",
            "labels": [
                {"name": "chatgpt-task"},
                {"name": "executor:codex"},
                {"name": "status:approved"},
                {"name": "priority:P1"},
            ],
        },
    }
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Young-Consultations/portfolio-tasks")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(cli, "_api", lambda dry_run=False: UnexpectedApi())

    assert cli.main(["route-check", str(event_file)]) == 0
    output = capsys.readouterr().out
    assert "route=false" in output
    assert "reason=non-approval-label" in output


def test_route_check_queued_issue_does_not_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    event = {
        "action": "reopened",
        "issue": {
            "number": 42,
            "title": "Approved work",
            "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
            "state": "open",
            "labels": [
                {"name": "chatgpt-task"},
                {"name": "executor:codex"},
                {"name": "status:approved"},
            ],
        },
    }
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event), encoding="utf-8")
    queued_issue = {
        "number": 42,
        "title": "Approved work",
        "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
        "state": "open",
        "labels": [
            {"name": "chatgpt-task"},
            {"name": "executor:codex"},
            {"name": "status:approved"},
            {"name": "status:queued"},
        ],
    }
    monkeypatch.setenv("GITHUB_REPOSITORY", "Young-Consultations/portfolio-tasks")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(cli, "_api", lambda dry_run=False: SequencedIssueApi([queued_issue]))

    assert cli.main(["route-check", str(event_file)]) == 0
    output = capsys.readouterr().out
    assert "route=false" in output
    assert "reason=already-dispatched" in output


def test_route_check_edited_issue_invalidates_approval_without_routing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    event = {
        "action": "edited",
        "issue": {
            "number": 42,
            "title": "Approved work",
            "body": "### Target repository\n\nYoung-Consultations/portfolio-tasks",
            "state": "open",
            "labels": [
                {"name": "chatgpt-task"},
                {"name": "executor:codex"},
                {"name": "status:approved"},
            ],
        },
    }
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Young-Consultations/portfolio-tasks")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(cli, "_api", lambda dry_run=False: UnexpectedApi())

    assert cli.main(["route-check", str(event_file)]) == 0
    output = capsys.readouterr().out
    assert "route=false" in output
    assert "reason=edited-approval-invalidated" in output
