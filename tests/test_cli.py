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

    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
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

    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
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


class SyncApi:
    def __init__(
        self,
        source_body: str,
        source_labels: tuple[str, ...] = ("chatgpt-task",),
        targets: list[dict[str, Any]] | None = None,
    ) -> None:
        self.source_body = source_body
        self.source_labels = source_labels
        self.targets = targets or []
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append((method, endpoint, payload))
        if method == "GET" and endpoint == "repos/Young-Consultations/portfolio-tasks/issues/42":
            return {
                "number": 42,
                "title": "Task",
                "body": self.source_body,
                "state": "open",
                "labels": [{"name": label} for label in self.source_labels],
                "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/42",
            }
        if (
            method == "GET"
            and endpoint == "repos/Young-Consultations/slugger/issues?state=all&per_page=100"
        ):
            return self.targets
        if method in {"POST", "PATCH"} and endpoint.startswith(
            "repos/Young-Consultations/slugger/issues"
        ):
            return {}
        raise AssertionError(
            f"unexpected API call: method={method}, endpoint={endpoint}, payload={payload}"
        )


def mirrored_target_issue(
    number: int = 9, state: str = "open", labels: tuple[str, ...] = ("portfolio-task",)
) -> dict[str, Any]:
    return {
        "number": number,
        "title": "Legacy mirror",
        "body": (
            "Legacy mirror\n\n## Portfolio Task Metadata\n- Source issue: `#42`\n"
            "<!-- portfolio-task-source: Young-Consultations/portfolio-tasks#42 -->"
        ),
        "state": state,
        "labels": [{"name": label} for label in labels],
    }


class SequencedIssueApi:
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        self.calls = 0

    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        assert method == "GET"
        assert endpoint.startswith("repos/Young-Consultations/portfolio-tasks/issues/")
        assert payload is None
        if self.calls >= len(self.issues):
            return self.issues[-1]
        response = self.issues[self.calls]
        self.calls += 1
        return response


class UnexpectedApi:
    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        raise AssertionError(
            f"unexpected API call: method={method}, endpoint={endpoint}, payload={payload}"
        )


def test_main_routes_sync_projects_phase2(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"value": False}

    def _sync_projects_phase2() -> int:
        called["value"] = True
        return 0

    monkeypatch.setattr(cli, "sync_projects_phase2", _sync_projects_phase2)

    assert cli.main(["sync-projects-phase2"]) == 0
    assert called["value"]


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
        SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", "Young-Consultations/.github"),
        SLUGGER_ISSUE_BODY.replace(
            "Young-Consultations/slugger", "Young-Consultations/portfolio-tasks"
        ),
        SLUGGER_ISSUE_BODY.replace(
            "Young-Consultations/slugger", "Young-Consultations/consulting-playbook"
        ),
        SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", "Young-Consultations/sandbox"),
        SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", "Young-Consultations/unknown"),
        "No target field",
        SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", "`bad target`"),
    ],
    ids=[
        ".github",
        "portfolio-tasks",
        "consulting-playbook",
        "sandbox",
        "unknown",
        "missing",
        "malformed",
    ],
)
def test_sync_skips_non_slugger_target_without_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, body: str
) -> None:
    summary = tmp_path / "summary.md"
    api = RecordingApi(body)
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cli, "_api", lambda dry_run: api)

    assert cli.sync() == 0
    assert api.calls == [
        ("GET", "repos/Young-Consultations/portfolio-tasks/issues/42"),
        ("GET", "repos/Young-Consultations/slugger/issues?state=all&per_page=100"),
    ]
    assert "- Planned/completed action: `skipped-target-repository`" in summary.read_text(
        encoding="utf-8"
    )


def test_sync_edited_event_disables_and_closes_legacy_mismatch_mirror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    summary = tmp_path / "summary.md"
    api = SyncApi(
        source_body=SLUGGER_ISSUE_BODY.replace(
            "Young-Consultations/slugger", "Young-Consultations/consulting-playbook"
        ),
        targets=[mirrored_target_issue(labels=("portfolio-task", "manual"))],
    )
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")
    monkeypatch.setenv("GITHUB_EVENT_ACTION", "edited")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cli, "_api", lambda dry_run: api)

    assert cli.sync() == 0
    patch = [call for call in api.calls if call[0] == "PATCH"]
    assert patch
    payload = patch[0][2]
    assert payload is not None
    assert payload["state"] == "closed"
    assert payload["labels"] == ["manual"]
    assert "assignees" not in payload
    assert "Managed automatically: No - non-slugger target repository" in payload["body"]
    contents = summary.read_text(encoding="utf-8")
    assert "- Planned/completed action: `disable-sync`" in contents


def test_sync_unlabeled_chatgpt_event_disables_existing_slugger_mirror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    summary = tmp_path / "summary.md"
    event_file = tmp_path / "event.json"
    event_file.write_text(
        json.dumps({"issue": {"number": 42}, "label": {"name": "chatgpt-task"}}),
        encoding="utf-8",
    )
    api = SyncApi(
        source_body=SLUGGER_ISSUE_BODY,
        source_labels=(),
        targets=[mirrored_target_issue(labels=("portfolio-task", "manual"))],
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issues")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
    monkeypatch.setenv("GITHUB_EVENT_ACTION", "unlabeled")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cli, "_api", lambda dry_run: api)

    assert cli.sync() == 0
    patch = [call for call in api.calls if call[0] == "PATCH"]
    assert patch
    payload = patch[0][2]
    assert payload is not None
    assert payload["state"] == "open"
    assert payload["labels"] == ["manual"]
    assert "Managed automatically: No - chatgpt-task label removed" in payload["body"]
    assert "- Planned/completed action: `disable-sync`" in summary.read_text(encoding="utf-8")


def test_sync_dry_run_does_not_write_when_create_would_be_needed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    summary = tmp_path / "summary.md"
    mock_dir = tmp_path / "mock"
    mock_dir.mkdir()
    source = {
        "number": 42,
        "title": "Task",
        "body": SLUGGER_ISSUE_BODY,
        "state": "open",
        "labels": [{"name": "chatgpt-task"}],
        "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/42",
    }
    (mock_dir / "GET_repos_Young-Consultations_portfolio-tasks_issues_42.json").write_text(
        json.dumps(source), encoding="utf-8"
    )
    (mock_dir / "GET_repos_Young-Consultations_slugger_issues.json").write_text(
        "[]", encoding="utf-8"
    )
    monkeypatch.setenv("GH_MOCK_DIR", str(mock_dir))
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "true")

    assert cli.sync() == 0
    assert not (mock_dir / "writes.log").exists()
    contents = summary.read_text(encoding="utf-8")
    assert "- Planned/completed action: `create`" in contents
    assert "- Dry run: `true`" in contents


def test_sync_api_failure_summary_does_not_leak_secret_like_tokens(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class LeakyApi:
        def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
            raise GitHubApiError("Authorization: Bearer SECRET sk-secret-value")

    summary = tmp_path / "summary.md"
    monkeypatch.setenv("SOURCE_ISSUE_NUMBER", "42")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cli, "_api", lambda dry_run: LeakyApi())

    assert cli.sync() == 1
    contents = summary.read_text(encoding="utf-8")
    assert "GitHub API request failed" in contents
    assert "SECRET" not in contents
    assert "sk-secret" not in contents


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


def test_route_check_non_approval_event_does_not_route(
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
    monkeypatch.setenv("GITHUB_REPOSITORY", "Young-Consultations/portfolio-tasks")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(cli, "_api", lambda dry_run=False: UnexpectedApi())

    assert cli.main(["route-check", str(event_file)]) == 0
    output = capsys.readouterr().out
    assert "route=false" in output
    assert "reason=non-approval-event" in output


def test_route_check_queued_issue_does_not_route(
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


def test_route_check_requires_live_issue_snapshot(
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
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(cli, "_api", lambda dry_run=False: UnexpectedApi())

    assert cli.main(["route-check", str(event_file)]) == 0
    output = capsys.readouterr().out
    assert "route=false" in output
    assert "reason=live-issue-fetch-not-configured" in output


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
