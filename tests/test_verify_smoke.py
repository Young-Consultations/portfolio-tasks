"""Offline tests of the proposed one-use maintenance authorization boundary."""

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from portfolio_tasks import verify_smoke as smoke
from portfolio_tasks.terminal_projection import apply, revision_from
from tests.test_terminal_projection import Fake, comment, fixture

NOW = datetime(2026, 11, 25, 23, 0, tzinfo=UTC)
MAIN = "a" * 40
SOURCE = smoke.REPO + "#42"
SCHEMA = json.loads(Path("contracts/task-contract.schema.json").read_text())


def inputs():
    issue = {
        "number": 42,
        "title": smoke.TITLE,
        "state": "open",
        "user": {"login": smoke.OWNER},
        "body": smoke.BODY,
        "labels": [],
        "comments": 0,
        "created_at": NOW.isoformat(),
    }
    identity = revision_from(issue, SOURCE).task_id
    env = {
        "GITHUB_REPOSITORY": smoke.REPO,
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_ACTOR": smoke.OWNER,
        "GITHUB_TRIGGERING_ACTOR": smoke.OWNER,
        "APPROVERS": smoke.OWNER,
        "CONFIRMATION": "verify-v5-once",
        "ISSUE_NUMBER": "42",
        "GITHUB_RUN_ID": "123",
        "EXPECTED_TASK_ID": identity,
        "EXPECTED_MAIN_SHA": MAIN,
        "GITHUB_SHA": MAIN,
    }
    return issue, env


class Memory:
    path = f"repos/{smoke.REPO}/issues/42"

    def __init__(self, issue):
        self.issue = deepcopy(issue)
        self.comments = []
        self.events = []
        self.writes = 0
        self.main = MAIN
        self.tag = smoke.CONTROL_SHA
        self.bad_readback = False

    def read(self):
        return deepcopy((self.issue, self.comments))

    def api(self, path):
        if path == self.path + "/events?per_page=1":
            return deepcopy(self.events)
        if path == f"repos/{smoke.REPO}/commits/main":
            return {"sha": self.main}
        if path.endswith("/git/ref/tags/" + smoke.RELEASE):
            return {"object": {"type": "commit", "sha": self.tag}}
        raise AssertionError("unexpected API endpoint")

    def comment(self, body):
        self.writes += 1
        self.comments.append(
            {
                "body": body,
                "user": {"login": "foreign" if self.bad_readback else "github-actions[bot]"},
            }
        )
        self.issue["comments"] += 1


@pytest.fixture(autouse=True)
def no_real_effects():
    with (
        patch("subprocess.run", side_effect=AssertionError("external process")),
        patch("socket.create_connection", side_effect=AssertionError("external socket")),
    ):
        yield


def test_exact_owner_bound_payload_and_consumed_reservation():
    issue, env = inputs()
    api = Memory(issue)
    payload = smoke.prepare(api, env, NOW, SCHEMA)
    assert payload["target_repository"] == smoke.TARGET
    assert payload["task_id"] == env["EXPECTED_TASK_ID"]
    assert payload["status"] == "approved"
    assert api.writes == 1 and api.issue["labels"] == []
    assert smoke.reservation_matches(api.comments, revision_from(issue, SOURCE))
    # New workflow run ID must not reopen the same issue.
    env["GITHUB_RUN_ID"] = "124"
    with pytest.raises(ValueError):
        smoke.prepare(api, env, NOW, SCHEMA)
    assert api.writes == 1


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("GITHUB_REPOSITORY", "other/repo"),
        ("GITHUB_REF", "refs/heads/feature"),
        ("GITHUB_EVENT_NAME", "pull_request"),
        ("GITHUB_RUN_ATTEMPT", "2"),
        ("GITHUB_ACTOR", "foreign"),
        ("GITHUB_TRIGGERING_ACTOR", "foreign"),
        ("APPROVERS", "foreign"),
        ("CONFIRMATION", "implement"),
        ("ISSUE_NUMBER", "0"),
        ("EXPECTED_TASK_ID", "task-" + "b" * 32),
        ("EXPECTED_MAIN_SHA", "b" * 40),
    ],
)
def test_invalid_dispatch_never_reserves(key, value):
    issue, env = inputs()
    env[key] = value
    api = Memory(issue)
    with pytest.raises(ValueError):
        smoke.prepare(api, env, NOW, SCHEMA)
    assert api.writes == 0


@pytest.mark.parametrize(
    "fault",
    [
        "wrong-body",
        "wrong-title",
        "foreign-creator",
        "closed",
        "approved-label",
        "old-issue",
        "past-events",
        "prior-comment",
        "changed-main",
        "changed-tag",
    ],
)
def test_unsafe_issue_or_binding_never_reserves(fault):
    issue, env = inputs()
    api = Memory(issue)
    if fault == "wrong-body":
        api.issue["body"] = smoke.BODY.replace("verify", "implement")
    elif fault == "wrong-title":
        api.issue["title"] += " changed"
    elif fault == "foreign-creator":
        api.issue["user"]["login"] = "foreign"
    elif fault == "closed":
        api.issue["state"] = "closed"
    elif fault == "approved-label":
        api.issue["labels"] = [{"name": "status:approved"}]
    elif fault == "old-issue":
        api.issue["created_at"] = (NOW - timedelta(days=2)).isoformat()
    elif fault == "past-events":
        api.events = [{"event": "labeled"}]
    elif fault == "prior-comment":
        api.comments = [{"body": "already used"}]
        api.issue["comments"] = 1
    elif fault == "changed-main":
        api.main = "b" * 40
    elif fault == "changed-tag":
        api.tag = "b" * 40
    with pytest.raises(ValueError):
        smoke.prepare(api, env, NOW, SCHEMA)
    assert api.writes == 0


def test_ambiguous_reservation_readback_stops_before_router():
    issue, env = inputs()
    api = Memory(issue)
    api.bad_readback = True
    with pytest.raises(ValueError):
        smoke.prepare(api, env, NOW, SCHEMA)
    assert api.writes == 1


def result_fixture(status="verified"):
    issue, env = inputs()
    _, _, result, _ = fixture(status)
    identity = env["EXPECTED_TASK_ID"]
    result.update(delivery_id=identity, correlation_id=identity)
    from portfolio_tasks.terminal_projection import digest

    binding = {
        "contract_version": result["contract_version"],
        "delivery_id": identity,
        "correlation_id": identity,
        "target_repository": smoke.TARGET,
        "source_issue": SOURCE,
    }
    receipt = {
        **binding,
        "result_sha256": digest(result),
        "effect_sha256": "a" * 64,
        "effect_class": status,
    }
    writer = "ai-sdlc-result-writer[bot]"
    comments = [
        {
            "body": smoke.reservation(revision_from(issue, SOURCE), "123"),
            "user": {"login": "github-actions[bot]"},
        },
        comment("admission", {**binding, "control_plane_release": smoke.RELEASE}, smoke.OWNER),
        comment("result-receipt", receipt, writer),
        comment("result-forwarded", receipt, writer),
    ]
    api = Fake(issue, comments)
    api.trust = lambda _: {
        "policy_format_version": 2,
        "trusted_admission_authors": [smoke.OWNER],
        "trusted_result_authors": [writer],
    }
    return api, identity, result


def test_reserved_v5_verify_result_projects_once_without_labels():
    api, identity, result = result_fixture()
    assert apply(api, SOURCE, identity, "result", result)["terminal"] == "verified"
    assert api.effects == ["comment"]
    assert api.issue["labels"] == []
    apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["comment"]


@pytest.mark.parametrize(
    "fault", ["missing", "forged", "duplicate", "queue", "label", "changed", "publication"]
)
def test_v5_projection_denies_non_smoke_or_untrusted_reservation(fault):
    api, identity, result = result_fixture(
        "draft-pr-created" if fault == "publication" else "verified"
    )
    mode = "result"
    if fault == "missing":
        api.comments.pop(0)
    elif fault == "forged":
        api.comments[0]["user"]["login"] = "foreign"
    elif fault == "duplicate":
        api.comments.append(deepcopy(api.comments[0]))
    elif fault == "queue":
        mode = "queued"
    elif fault == "label":
        api.issue["labels"] = [{"name": "status:approved"}]
    elif fault == "changed":
        api.issue["body"] += "\nchanged"
    with pytest.raises(ValueError):
        apply(api, SOURCE, identity, mode, result)
    assert api.effects == []


def test_workflow_has_only_manual_trigger_and_literal_verify():
    text = Path(".github/workflows/verify-v5-smoke.yml").read_text()
    workflow = yaml.load(text, Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert set(workflow["on"]["workflow_dispatch"]["inputs"]) == {
        "issue_number",
        "expected_task_id",
        "expected_main_sha",
        "confirmation",
    }
    route = workflow["jobs"]["route"]
    assert route["needs"] == "prepare"
    assert route["with"]["execution_mode"] == "verify"
    assert route["uses"].endswith("@ai-sdlc-v5.0.0")
    assert set(route["secrets"]) == {"CODEX_ROUTER_TOKEN"}
    assert "status:approved" not in text
    assert "OPENAI_API_KEY" not in text
    assert "TARGET_PUBLICATION_TOKEN" not in text
    assert "github.run_attempt == 1" in text
