"""Offline terminal lifecycle regression tests."""

import json
from copy import deepcopy
from unittest.mock import patch

import pytest

from portfolio_tasks.source_lifecycle import CONTRACT, TERMINAL_STATUSES, LifecycleError
from portfolio_tasks.terminal_projection import (
    REPOSITORY,
    apply,
    digest,
    projection_body,
    revision_from,
)

SOURCE = REPOSITORY + "#42"
TARGET = "Young-Consultations/consulting-playbook"
OWNER = "synthetic-owner"
WRITER = "synthetic-writer"
TRUST = {
    "policy_format_version": 2,
    "trusted_admission_authors": [OWNER],
    "trusted_result_authors": [WRITER],
}


def comment(kind, value, author):
    return {
        "body": "<!-- ai-sdlc-" + kind + ":v2 " + json.dumps(value) + " -->",
        "user": {"login": author},
    }


def fixture(status="failed"):
    fields = {
        "Project": "test",
        "Priority": "P2",
        "Task type": "Documentation",
        "Parallel-safe": "no",
        "Risk": "low",
        "Estimated scope": "small",
        "Target repository": TARGET,
        "Execution mode": "implement",
        "Executor": "codex",
        "Dependency issue references": "None",
        "Sensitivity declaration": "not-sensitive",
    }
    issue = {
        "number": 42,
        "state": "open",
        "user": {"login": OWNER},
        "body": "\n\n".join("### " + k + "\n" + v for k, v in fields.items()),
        "labels": [{"name": "chatgpt-task"}, {"name": "status:queued"}],
    }
    identity = revision_from(issue, SOURCE).task_id
    binding = {
        "contract_version": CONTRACT,
        "delivery_id": identity,
        "correlation_id": identity,
        "target_repository": TARGET,
    }
    managed = status in {"draft-pr-created", "duplicate-reused"}
    result = {
        **binding,
        "execution_status": status,
        "branch_name": "codex/example" if managed else None,
        "pull_request_url": "https://github.com/" + TARGET + "/pull/1" if managed else None,
        "workflow_url": "https://github.com/" + TARGET + "/actions/runs/1",
        "validation_result": "passed",
        "test_result": "passed",
        "failure_category": "codex-runtime" if status == "failed" else "none",
        "failure_message": "synthetic failure" if status == "failed" else None,
        "started_at": "2026-10-15T05:02:26Z",
        "completed_at": "2026-10-15T05:02:43Z",
    }
    admission = comment(
        "admission",
        {**binding, "source_issue": SOURCE, "control_plane_release": "ai-sdlc-v4.0.0"},
        OWNER,
    )
    receipt = {
        **binding,
        "source_issue": SOURCE,
        "result_sha256": digest(result),
        "effect_sha256": "a" * 64,
        "effect_class": status,
    }
    return (
        issue,
        identity,
        result,
        [
            admission,
            comment("result-receipt", receipt, WRITER),
            comment("result-forwarded", receipt, WRITER),
        ],
    )


class Fake:
    def __init__(self, issue, comments):
        self.issue, self.comments = deepcopy(issue), deepcopy(comments)
        self.effects = []
        self.fail_remove = False

    def read(self):
        return deepcopy((self.issue, self.comments))

    def trust(self, _):
        return TRUST

    def comment(self, body):
        self.effects.append("comment")
        self.comments.append({"body": body, "user": {"login": "github-actions[bot]"}})

    def add(self, label):
        assert label == "status:queued"
        self.effects.append("add")
        self.issue["labels"].append({"name": label})

    def remove(self, label):
        if self.fail_remove:
            raise LifecycleError("simulated removal failure")
        self.effects.append("remove")
        self.issue["labels"] = [x for x in self.issue["labels"] if x["name"] != label]


@pytest.fixture(autouse=True)
def trap_external_effects():
    with (
        patch("subprocess.run", side_effect=AssertionError("external process")),
        patch("socket.create_connection", side_effect=AssertionError("real socket")),
    ):
        yield


@pytest.mark.parametrize("status", sorted(TERMINAL_STATUSES))
def test_all_terminal_outcomes_clear_queue_not_accept_task(status):
    issue, identity, result, comments = fixture(status)
    api = Fake(issue, comments)
    outcome = apply(api, SOURCE, identity, "result", result)
    assert outcome["terminal"] == status
    assert api.effects == ["comment", "remove"]
    assert api.issue["state"] == "open"
    assert api.issue["labels"] == [{"name": "chatgpt-task"}]
    apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["comment", "remove"]


def test_fresh_dispatch_precedes_forward_marker():
    issue, identity, result, comments = fixture()
    api = Fake(issue, comments[:2])
    apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["comment", "remove"]


def test_partial_label_failure_and_duplicate_repair():
    issue, identity, result, comments = fixture()
    api = Fake(issue, comments)
    api.fail_remove = True
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["comment"]
    api.fail_remove = False
    apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["comment", "remove"]


def test_route_first_then_terminal():
    issue, identity, result, comments = fixture()
    issue["labels"][-1]["name"] = "status:approved"
    api = Fake(issue, comments[:1])
    apply(api, SOURCE, identity, "queued")
    api.comments.extend(comments[1:])
    apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["add", "remove", "comment", "remove"]


def test_terminal_first_then_late_route_never_queues():
    issue, identity, result, comments = fixture()
    issue["labels"][-1]["name"] = "status:approved"
    api = Fake(issue, comments)
    apply(api, SOURCE, identity, "result", result)
    apply(api, SOURCE, identity, "queued")
    assert api.effects == ["comment", "remove"]


def test_receipt_without_projection_blocks_late_queue():
    issue, identity, _, comments = fixture()
    api = Fake(issue, comments)
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "queued")
    assert not api.effects


@pytest.mark.parametrize(
    "fault",
    [
        "forged-admission",
        "forged-receipt",
        "forged-forward",
        "forged-source",
        "duplicate",
        "conflict",
        "missing",
        "revision",
        "newer-delivery",
        "human",
        "closed",
    ],
)
def test_unsafe_evidence_denied(fault):
    issue, identity, result, comments = fixture()
    if fault.startswith("forged-"):
        kind = fault.split("-")[1]
        if kind == "source":
            comments.append({"body": projection_body(result), "user": {"login": "foreign"}})
        else:
            comments[{"admission": 0, "receipt": 1, "forward": 2}[kind]]["user"]["login"] = (
                "foreign"
            )
    elif fault == "duplicate":
        comments.append(deepcopy(comments[1]))
    elif fault == "conflict":
        result["failure_message"] = "other result"
    elif fault == "missing":
        comments = comments[:1]
    elif fault == "revision":
        issue["body"] += "\nnew material"
    elif fault == "newer-delivery":
        comments.append(deepcopy(comments[0]))
    elif fault == "human":
        issue["labels"].append({"name": "status:done"})
    elif fault == "closed":
        issue["state"] = "closed"
    api = Fake(issue, comments)
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "result", result)
    assert not api.effects


def test_historical_plan_is_read_only_and_requires_forwarding():
    issue, identity, result, comments = fixture()
    comments.append({"body": projection_body(result), "user": {"login": "github-actions[bot]"}})
    api = Fake(issue, comments)
    plan = apply(api, SOURCE, identity, "plan")
    assert plan["remove"] == ["status:queued"]
    assert plan["terminal"] == "failed"
    assert not plan["mutation_authorized"] and not api.effects
    del api.comments[2]
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "plan")
    assert not api.effects


def test_forward_marker_arrives_between_initial_and_final_validation():
    issue, identity, result, comments = fixture()

    class Arrival(Fake):
        reads = 0

        def read(self):
            self.reads += 1
            if self.reads == 2:
                self.comments.append(comments[2])
            return super().read()

    api = Arrival(issue, comments[:2])
    apply(api, SOURCE, identity, "result", result)
    assert api.effects == ["comment", "remove"]


def test_terminal_receipt_arrives_before_queued_write():
    issue, identity, _, comments = fixture()
    issue["labels"][-1]["name"] = "status:approved"

    class Arrival(Fake):
        reads = 0

        def read(self):
            self.reads += 1
            if self.reads == 2:
                self.comments.extend(comments[1:])
            return super().read()

    api = Arrival(issue, comments[:1])
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "queued")
    assert not api.effects


def test_source_state_changed_before_mutation():
    issue, identity, result, comments = fixture()

    class Change(Fake):
        reads = 0

        def read(self):
            self.reads += 1
            if self.reads == 2:
                self.issue["labels"].append({"name": "status:done"})
            return super().read()

    api = Change(issue, comments)
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "result", result)
    assert not api.effects
