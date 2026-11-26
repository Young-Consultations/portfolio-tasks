"""Offline tests of the proposed one-use maintenance authorization boundary."""

import hashlib
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
        "GITHUB_WORKFLOW_SHA": MAIN,
        "GITHUB_WORKFLOW_REF": smoke.WORKFLOW_REF,
    }
    return issue, env


def run_evidence(issue):
    revision = revision_from(issue, SOURCE)
    return {
        "id": 123,
        "run_attempt": 1,
        "path": smoke.WORKFLOW_PATH,
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": MAIN,
        "repository": {"full_name": smoke.REPO},
        "head_repository": {"full_name": smoke.REPO},
        "actor": {"login": smoke.OWNER},
        "triggering_actor": {"login": smoke.OWNER},
        "display_title": smoke.run_title(revision, MAIN),
    }


def job_evidence():
    return {
        "total_count": 1,
        "jobs": [{
            "name": "prepare", "run_id": 123, "head_sha": MAIN,
            "status": "completed", "conclusion": "success",
            "steps": [{
                "name": "Validate owner-bound issue and consume one-shot reservation",
                "status": "completed", "conclusion": "success",
            }],
        }],
    }


RUN_PATH = f"repos/{smoke.REPO}/actions/runs/123"
JOBS_PATH = RUN_PATH + "/attempts/1/jobs?per_page=100"


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
        self.run = run_evidence(issue)
        self.jobs = job_evidence()

    def read(self):
        return deepcopy((self.issue, self.comments))

    def api(self, path):
        if path == RUN_PATH:
            return deepcopy(self.run)
        if path == JOBS_PATH:
            return deepcopy(self.jobs)
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
    assert smoke.reservation_record(api.comments, revision_from(issue, SOURCE)) is not None
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
        ("GITHUB_WORKFLOW_SHA", "b" * 40),
        ("GITHUB_WORKFLOW_REF", "foreign"),
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
    # Independent literal receiver vector; do not call the new validator
    # to construct the test's expected effect.
    effect_class = "managed-draft" if status == "draft-pr-created" else status
    effect = {
        "contract_version": result["contract_version"],
        "correlation_id": identity,
        "delivery_id": identity,
        "target_repository": smoke.TARGET,
        "effect_class": effect_class,
        "branch_name": result["branch_name"],
        "pull_request_url": result["pull_request_url"],
        "validation_result": result["validation_result"],
        "test_result": result["test_result"],
        "failure_category": result["failure_category"],
    }
    receipt = {
        **binding,
        "result_sha256": digest(result),
        "effect_sha256": hashlib.sha256(
            json.dumps(effect, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "effect_class": effect_class,
    }
    writer = "ai-sdlc-result-writer[bot]"
    comments = [
        {
            "body": smoke.reservation(revision_from(issue, SOURCE), "123", MAIN),
            "user": {"login": "github-actions[bot]"},
        },
        comment("admission", {**binding, "control_plane_release": smoke.RELEASE}, smoke.OWNER),
        comment("result-receipt", receipt, writer),
        comment("result-forwarded", receipt, writer),
    ]
    api = Fake(issue, comments)
    evidence = Memory(issue)
    api.api = evidence.api
    api.evidence = evidence
    api.trust = lambda _: {
        "policy_format_version": 2,
        "trusted_admission_authors": [smoke.OWNER],
        "trusted_result_authors": [writer],
    }
    return api, identity, result


def test_reserved_v5_verify_result_projects_once_without_labels():
    api, identity, result = result_fixture()
    assert apply(api, SOURCE, identity, "result", result, reviewed_sha=MAIN)["terminal"] == "verified"
    assert api.effects == ["comment"]
    assert api.issue["labels"] == []
    apply(api, SOURCE, identity, "result", result, reviewed_sha=MAIN)
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
        apply(api, SOURCE, identity, mode, result, reviewed_sha=MAIN)
    assert api.effects == []


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("id", 124),
        ("run_attempt", 2),
        ("path", ".github/workflows/other.yml"),
        ("event", "push"),
        ("head_branch", "feature"),
        ("head_sha", "b" * 40),
        ("repository", {"full_name": "other/repo"}),
        ("head_repository", {"full_name": "other/repo"}),
        ("actor", {"login": "foreign"}),
        ("triggering_actor", {"login": "foreign"}),
        ("display_title", "other issue or task"),
    ],
)
def test_wrong_run_provenance_denies_preparation_and_projection(key, value):
    issue, env = inputs()
    memory = Memory(issue)
    memory.run[key] = value
    with pytest.raises(ValueError):
        smoke.prepare(memory, env, NOW, SCHEMA)
    assert memory.writes == 0
    api, identity, result = result_fixture()
    api.evidence.run[key] = value
    with pytest.raises(ValueError):
        apply(api, SOURCE, identity, "result", result, reviewed_sha=MAIN)
    assert not api.effects


@pytest.mark.parametrize("fault", ["missing", "duplicate", "count", "sha", "run", "failed", "step"])
def test_preparation_job_proof_required(fault):
    api, identity, result = result_fixture()
    jobs = api.evidence.jobs
    job = jobs["jobs"][0]
    if fault == "missing":
        jobs["jobs"] = []
        jobs["total_count"] = 0
    elif fault == "duplicate":
        jobs["jobs"].append(deepcopy(job))
        jobs["total_count"] = 2
    elif fault == "count":
        jobs["total_count"] = 2
    elif fault == "sha":
        job["head_sha"] = "b" * 40
    elif fault == "run":
        job["run_id"] = 124
    elif fault == "failed":
        job["conclusion"] = "failure"
    elif fault == "step":
        job["steps"][0]["conclusion"] = "failure"
    with pytest.raises(ValueError):
        apply(api, SOURCE, identity, "result", result, reviewed_sha=MAIN)
    assert not api.effects


@pytest.mark.parametrize("sha", ["", "b" * 40])
def test_projection_sha_must_match_reserved_workflow(sha):
    api, identity, result = result_fixture()
    with pytest.raises(ValueError):
        apply(api, SOURCE, identity, "result", result, reviewed_sha=sha)
    assert not api.effects


@pytest.mark.parametrize("field", ["effect_sha256", "effect_class"])
@pytest.mark.parametrize("scope", ["receipt", "forwarded", "both"])
def test_contradictory_effect_evidence_denied(field, scope):
    api, identity, result = result_fixture()
    for index, kind in [(2, "receipt"), (3, "forwarded")]:
        if scope not in (kind, "both"):
            continue
        row = api.comments[index]
        prefix, raw = row["body"].split(" ", 2)[1:]
        record = json.loads(raw[:-4])
        record[field] = "b" * 64 if field == "effect_sha256" else "managed-draft"
        row["body"] = "<!-- " + prefix + " " + json.dumps(record) + " -->"
    with pytest.raises(ValueError):
        apply(api, SOURCE, identity, "result", result, reviewed_sha=MAIN)
    assert not api.effects


def test_forwarding_may_arrive_after_receipt():
    api, identity, result = result_fixture()
    api.comments.pop()
    assert apply(api, SOURCE, identity, "result", result, reviewed_sha=MAIN)["terminal"] == "verified"
    assert api.effects == ["comment"]


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
    assert "inputs.issue_number" in workflow["run-name"]
    assert "inputs.expected_task_id" in workflow["run-name"]
    assert "inputs.expected_main_sha" in workflow["run-name"]
    assert workflow["jobs"]["prepare"]["permissions"]["actions"] == "read"
    route = workflow["jobs"]["route"]
    assert route["needs"] == "prepare"
    assert "github.run_attempt == 1" in route["if"]
    assert "github.triggering_actor" in route["if"]
    assert route["with"]["execution_mode"] == "verify"
    assert route["uses"].endswith("@ai-sdlc-v5.0.0")
    assert set(route["secrets"]) == {"CODEX_ROUTER_TOKEN"}
    assert "status:approved" not in text
    assert "OPENAI_API_KEY" not in text
    assert "TARGET_PUBLICATION_TOKEN" not in text
    assert "github.run_attempt == 1" in text
