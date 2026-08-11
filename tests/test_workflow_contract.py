"""Contract and security tests for the sole canonical target adapter."""

import json
import re
from pathlib import Path

import pytest

from portfolio_tasks.target_adapter import (
    AdmissionError,
    OwnershipError,
    Pull,
    ResultLedger,
    admit,
    branch_for,
    canonical_digest,
    ownership_marker,
    reconcile,
    verify_result,
)


class Validator:
    def validate(self, instance: object) -> None:
        if not isinstance(instance, dict) or instance.get("malformed"):
            raise ValueError("schema")


def payload(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "contract_version": "ai-sdlc-contract/v2",
        "delivery_id": "delivery-fixture-0001",
        "correlation_id": "correlation-fixture-0001",
        "source_issue": "Young-Consultations/portfolio-tasks#123",
        "target_repository": "Young-Consultations/portfolio-tasks",
        "executor": "codex",
        "draft_pr_only": True,
        "execution_mode": "implement",
        "task_type": "automation",
        "instructions": "Make one bounded change.",
    }
    return value | changes


def accepted(**changes: object):  # type: ignore[no-untyped-def]
    return admit(
        json.dumps(payload(**changes)),
        "transport-group-0001",
        Validator(),
        caller_authenticated=True,
        caller_authorized=True,
    )


@pytest.mark.parametrize("mode", ["verify", "implement"])
def test_valid_modes(mode: str) -> None:
    assert accepted(execution_mode=mode).mode == mode


@pytest.mark.parametrize(
    ("change", "kwargs"),
    [
        ({"target_repository": "Young-Consultations/slugger"}, {}),
        ({"contract_version": "ai-sdlc-contract/v1"}, {}),
        ({"malformed": True}, {}),
        ({"task_type": "feature"}, {}),
        ({"draft_pr_only": False}, {}),
        ({}, {"enabled": False}),
        ({}, {"caller_authorized": False}),
    ],
)
def test_admission_failures(change: dict[str, object], kwargs: dict[str, object]) -> None:
    options = {"caller_authenticated": True, "caller_authorized": True, "enabled": True} | kwargs
    with pytest.raises(AdmissionError):
        admit(json.dumps(payload(**change)), "transport-group-0001", Validator(), **options)  # type: ignore[arg-type]


@pytest.mark.parametrize("raw,group", [("{", "transport-group-0001"), ("{}", "bad group")])
def test_malformed_input_and_invalid_concurrency(raw: str, group: str) -> None:
    with pytest.raises(AdmissionError):
        admit(raw, group, Validator(), caller_authenticated=True, caller_authorized=True)


def test_delivery_not_transport_identity_drives_branch_and_digest() -> None:
    first = accepted()
    second = admit(
        json.dumps(payload()),
        "entirely-different-transport-group",
        Validator(),
        caller_authenticated=True,
        caller_authorized=True,
    )
    assert first.branch == second.branch == branch_for(first.delivery_id)
    assert first.digest == second.digest
    assert first.branch != branch_for(first.correlation_id)


def test_duplicate_and_changed_payload_ownership() -> None:
    delivery = accepted()
    managed = Pull("https://example.test/pr/1", delivery.branch, ownership_marker(delivery))
    assert reconcile(delivery, [managed]) == managed
    changed = accepted(instructions="changed under the same delivery")
    with pytest.raises(OwnershipError):
        reconcile(changed, [managed])


def test_matching_ambiguous_and_conflicting_draft_ownership() -> None:
    delivery = accepted()
    managed = Pull("https://example.test/pr/1", delivery.branch, ownership_marker(delivery))
    assert reconcile(delivery, []) is None
    assert reconcile(delivery, [managed]) == managed
    with pytest.raises(OwnershipError):
        reconcile(delivery, [managed, managed])
    with pytest.raises(OwnershipError):
        reconcile(delivery, [Pull(managed.url, managed.branch, managed.body, draft=False)])


def test_create_race_requery_converges_only_to_unique_managed_draft() -> None:
    delivery = accepted()
    winner = Pull("https://example.test/pr/1", delivery.branch, ownership_marker(delivery))
    assert reconcile(delivery, [winner]).url == winner.url  # type: ignore[union-attr]
    with pytest.raises(OwnershipError):
        reconcile(delivery, [winner, winner])


def test_verify_result_is_side_effect_free_and_preserves_identity() -> None:
    delivery = accepted(execution_mode="verify")
    result = verify_result(delivery, workflow_url="https://example.test/runs/1")
    assert result["branch_name"] is None and result["pull_request_url"] is None
    assert result["delivery_id"] == delivery.delivery_id
    assert result["correlation_id"] == delivery.correlation_id
    assert result["target_repository"] == delivery.payload["target_repository"]


def test_identical_and_conflicting_result_redelivery() -> None:
    result = verify_result(accepted(execution_mode="verify"), workflow_url="https://x.test/r/1")
    ledger = ResultLedger()
    assert ledger.deliver(result, Validator())
    assert ledger.deliver(dict(result), Validator())
    with pytest.raises(OwnershipError):
        ledger.deliver(result | {"execution_status": "failed"}, Validator())


def test_digest_is_canonical_and_diagnostics_are_not_identity() -> None:
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})


def test_one_active_target_workflow_is_pinned_and_credential_separated() -> None:
    workflows = tuple(sorted(Path(".github/workflows").glob("*.yml")))
    assert workflows == (
        Path(".github/workflows/ci.yml"),
        Path(".github/workflows/codex-execute.yml"),
    )
    text = workflows[1].read_text(encoding="utf-8")
    assert "execution_input_json:" in text and "execution_input:" not in text
    assert "concurrency_group:" in text
    assert "f2491872976a4dcc1633997954c03c07cbc4fced" in text
    assert "ai-sdlc-delivery-id" not in text  # trusted Python owns marker semantics
    assert "pull_request_target" not in text
    references = re.findall(r"(?:uses: )[^\s]+@([^\s]+)", text)
    assert references and all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in references)
    codex_job = text[text.index("  implement:") : text.index("  result:")]
    assert "TARGET_PUBLICATION_TOKEN" not in codex_job
    assert "CODEX_RESULT_TOKEN" not in codex_job


def test_normal_ci_has_no_codex_or_publication_effect() -> None:
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    for forbidden in ("OPENAI_API_KEY", "git push", "gh pr create", "codex exec"):
        assert forbidden not in text
