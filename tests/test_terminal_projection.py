"""Offline terminal lifecycle regression tests."""

import json
from copy import deepcopy
from unittest.mock import patch

import pytest

from portfolio_tasks.source_lifecycle import CONTRACT, TERMINAL_STATUSES, LifecycleError
from portfolio_tasks.terminal_projection import (
    REPOSITORY,
    GitHub,
    apply,
    digest,
    projection_body,
    revision_from,
    verify_v5_effect,
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


def fixture(status="failed", release="ai-sdlc-v5.0.0"):
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
        {**binding, "source_issue": SOURCE, "control_plane_release": release},
        OWNER,
    )
    effect_class = "managed-draft" if managed else status
    effect = {
        **binding,
        "effect_class": effect_class,
        "branch_name": result["branch_name"],
        "pull_request_url": result["pull_request_url"],
        "validation_result": result["validation_result"],
        "test_result": result["test_result"],
        "failure_category": result["failure_category"],
    }
    receipt = {
        **binding,
        "source_issue": SOURCE,
        "result_sha256": digest(result),
        "effect_sha256": digest(effect) if release == "ai-sdlc-v5.0.0" else "a" * 64,
        "effect_class": effect_class,
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
        patch("subprocess.run", side_effect=AssertionError("external process")) as process,
        patch("socket.create_connection", side_effect=AssertionError("real socket")) as network,
        patch("socket.socket.connect", side_effect=AssertionError("real socket")) as connect,
    ):
        yield
        process.assert_not_called()
        network.assert_not_called()
        connect.assert_not_called()


@pytest.mark.parametrize("release", ["ai-sdlc-v3.0.3", "ai-sdlc-v4.0.0", "ai-sdlc-v5.0.0"])
@pytest.mark.parametrize("status", sorted(TERMINAL_STATUSES))
def test_all_terminal_outcomes_clear_queue_not_accept_task(status, release):
    issue, identity, result, comments = fixture(status, release)
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


@pytest.mark.parametrize("release", ["ai-sdlc-v3.0.3", "ai-sdlc-v4.0.0", "ai-sdlc-v5.0.0"])
def test_historical_plan_is_read_only_and_requires_forwarding(release):
    issue, identity, result, comments = fixture(release=release)
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


def test_queued_projection_retries_as_no_op_after_readback_failure():
    issue, identity, _, comments = fixture()
    issue["labels"][-1]["name"] = "status:approved"

    class ReadbackFailure(Fake):
        reads = 0

        def read(self):
            self.reads += 1
            if self.reads == 3:
                raise LifecycleError("simulated readback failure")
            return super().read()

    api = ReadbackFailure(issue, comments[:1])
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "queued")
    assert api.effects == ["add", "remove"]
    result = apply(api, SOURCE, identity, "queued")
    assert result["add"] == result["remove"] == []
    assert api.effects == ["add", "remove"]
    assert api.issue["labels"][-1]["name"] == "status:queued"


def test_queued_projection_repairs_partial_approval_removal():
    issue, identity, _, comments = fixture()
    issue["labels"].append({"name": "status:approved"})
    api = Fake(issue, comments[:1])
    apply(api, SOURCE, identity, "queued")
    assert api.effects == ["remove"]
    apply(api, SOURCE, identity, "queued")
    assert api.effects == ["remove"]


def test_queued_retry_requires_active_state_and_unchanged_revision():
    issue, identity, _, comments = fixture()
    api = Fake(issue, comments[:1])
    api.issue["labels"] = [{"name": "chatgpt-task"}]
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "queued")
    api.issue["labels"].append({"name": "status:queued"})
    api.issue["body"] += "\nnew material"
    with pytest.raises(LifecycleError):
        apply(api, SOURCE, identity, "queued")
    assert not api.effects


@pytest.mark.parametrize("status", ["draft-pr-created", "duplicate-reused", "failed", "verified"])
@pytest.mark.parametrize("fault", ["effect_class", "effect_sha256"])
def test_v5_matching_but_false_effect_receipt_and_forward_are_denied(status, fault):
    issue, identity, result, comments = fixture(status)
    for i, kind in ((1, "result-receipt"), (2, "result-forwarded")):
        value = json.loads(comments[i]["body"].split(":v2 ", 1)[1][:-4])
        value[fault] = "b" * 64 if fault == "effect_sha256" else "false-effect"
        comments[i] = comment(kind, value, WRITER)
    api = Fake(issue, comments)
    with pytest.raises(LifecycleError, match="v5 receiver effect mismatch"):
        apply(api, SOURCE, identity, "result", result)
    assert not api.effects


def test_v5_managed_draft_equivalence_does_not_replace_exact_result_receipt():
    issue, identity, result, comments = fixture("draft-pr-created")
    _, _, duplicate, duplicate_comments = fixture("duplicate-reused")
    receipt = json.loads(comments[1]["body"].split(":v2 ", 1)[1][:-4])
    other_receipt = json.loads(duplicate_comments[1]["body"].split(":v2 ", 1)[1][:-4])
    assert receipt["effect_class"] == other_receipt["effect_class"] == "managed-draft"
    assert receipt["effect_sha256"] == other_receipt["effect_sha256"]
    assert digest(result) != digest(duplicate)
    api = Fake(issue, comments)
    with pytest.raises(LifecycleError, match="matching trusted receipt"):
        apply(api, SOURCE, identity, "result", duplicate)
    assert not api.effects


@pytest.mark.parametrize("mode", ["result", "queued", "plan"])
@pytest.mark.parametrize("retired", ["issue", "reservation"])
def test_retired_smoke_cannot_be_processed(mode, retired):
    issue, identity, result, comments = fixture()
    source = SOURCE
    if retired == "issue":
        issue["number"] = 176
        source = REPOSITORY + "#176"
    else:
        comments.append(comment("v5-smoke-reservation", {}, OWNER))
    api = Fake(issue, comments)
    with patch.object(api, "trust", side_effect=AssertionError("trust must not be read")) as trust:
        with pytest.raises(LifecycleError, match="retired maintenance"):
            apply(api, source, identity, mode, result)
        trust.assert_not_called()
    assert not api.effects


def test_v5_trust_read_uses_exact_commit_not_tag_or_main():
    _, _, _, comments = fixture()
    api = GitHub("42")
    with patch.object(api, "api", return_value=TRUST) as read:
        assert api.trust(comments) == TRUST
    read.assert_called_once_with(
        "-H",
        "Accept: application/vnd.github.raw+json",
        "repos/Young-Consultations/.github/contents/config/codex-result-trust.json"
        "?ref=3cce887fc393fa80ed8f79308ca9b9c7241ce622",
    )


def test_v5_effect_matches_immutable_receiver_known_verify_vector():
    # Recorded V5.7 effect vector; no API, issue mutation or replay.
    identity = "task-4ce3c7676172f2956ecb0ac3a0167cec"
    result = {
        "contract_version": CONTRACT,
        "correlation_id": identity,
        "delivery_id": identity,
        "target_repository": TARGET,
        "execution_status": "verified",
        "branch_name": None,
        "pull_request_url": None,
        "validation_result": "passed",
        "test_result": "passed",
        "failure_category": "none",
    }
    receipt = {
        "effect_class": "verified",
        "effect_sha256": "24315715feb466a11d09cc7e56d13d850e37b11a023de5b7d1d106cab9f28110",
    }
    verify_v5_effect([comment("result-receipt", receipt, WRITER)], result)
