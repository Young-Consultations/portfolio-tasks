import json

import pytest

from portfolio_tasks.reconciliation import (
    ReconciliationError,
    admission_binding,
    decide_missing_result_reconciliation,
)

SOURCE = "Young-Consultations/portfolio-tasks#159"
DELIVERY = "task-b72eaf2503fc3d27c82f8921e8cfbfff"
TARGET = "Young-Consultations/consulting-playbook"


def comments(*extra: str) -> list[dict[str, str]]:
    admission = {
        "activation_revision": "3efbe6227a93fa23020ca807387e310f026a1528",
        "activation_sha256": "d1ade8bf193022e72a35738f5baf61528d98441bee28285c5e65a4c7e1dbd9aa",
        "contract_version": "ai-sdlc-contract/v2",
        "control_plane_release": "ai-sdlc-v3.0.1",
        "correlation_id": DELIVERY,
        "delivery_id": DELIVERY,
        "source_issue": SOURCE,
        "target_repository": TARGET,
    }
    marker = "<!-- ai-sdlc-admission:v2 " + json.dumps(
        admission, sort_keys=True, separators=(",", ":")
    ) + " -->"
    return [{"body": marker}, *({"body": body} for body in extra)]


def issue(*labels: str) -> dict[str, object]:
    return {"state": "open", "labels": [{"name": label} for label in labels]}


def target_run(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": 36441714913,
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "failure",
        "html_url": f"https://github.com/{TARGET}/actions/runs/36441714913",
        "repository": {"full_name": TARGET},
    }
    value.update(changes)
    return value


def test_live_pre_adapter_failure_enters_reconciliation_without_terminal_result() -> None:
    decision = decide_missing_result_reconciliation(
        issue=issue("chatgpt-task", "status:queued"),
        comments=comments(),
        source_issue=SOURCE,
        delivery_id=DELIVERY,
        target_run=target_run(),
    )
    assert decision.action == "apply"
    assert decision.target_repository == TARGET
    assert "reconciliation-required" in decision.marker
    assert "does **not** infer a target execution result" in decision.comment
    assert "ai-sdlc-source-result" not in decision.comment


def test_reconciliation_is_idempotent_for_same_delivery_and_target_run() -> None:
    first = decide_missing_result_reconciliation(
        issue=issue("status:queued"),
        comments=comments(),
        source_issue=SOURCE,
        delivery_id=DELIVERY,
        target_run=target_run(),
    )
    repeated = decide_missing_result_reconciliation(
        issue=issue(),
        comments=comments(first.comment),
        source_issue=SOURCE,
        delivery_id=DELIVERY,
        target_run=target_run(),
    )
    assert repeated.action == "no-op"
    assert repeated.marker == first.marker


@pytest.mark.parametrize(
    "run_change",
    [
        {"repository": {"full_name": "Young-Consultations/slugger"}},
        {"event": "push"},
        {"status": "in_progress", "conclusion": None},
        {"conclusion": "success"},
        {"html_url": "https://github.com/Young-Consultations/slugger/actions/runs/1"},
    ],
)
def test_target_run_must_be_completed_failed_evidence(run_change: dict[str, object]) -> None:
    with pytest.raises(ReconciliationError):
        decide_missing_result_reconciliation(
            issue=issue("status:queued"),
            comments=comments(),
            source_issue=SOURCE,
            delivery_id=DELIVERY,
            target_run=target_run(**run_change),
        )


def test_existing_terminal_result_blocks_reconciliation() -> None:
    result = "<!-- ai-sdlc-source-result:v2 " + json.dumps(
        {"delivery_id": DELIVERY, "result_sha256": "a" * 64},
        sort_keys=True,
        separators=(",", ":"),
    ) + " -->"
    with pytest.raises(ReconciliationError, match="terminal result"):
        decide_missing_result_reconciliation(
            issue=issue("status:queued"),
            comments=comments(result),
            source_issue=SOURCE,
            delivery_id=DELIVERY,
            target_run=target_run(),
        )


def test_missing_or_duplicate_admission_fails_closed() -> None:
    with pytest.raises(ReconciliationError, match="exactly one"):
        admission_binding([], source_issue=SOURCE, delivery_id=DELIVERY)
    duplicated = comments()
    duplicated.append(duplicated[0].copy())
    with pytest.raises(ReconciliationError, match="exactly one"):
        admission_binding(duplicated, source_issue=SOURCE, delivery_id=DELIVERY)


def test_first_reconciliation_requires_open_queued_source() -> None:
    with pytest.raises(ReconciliationError, match="open queued"):
        decide_missing_result_reconciliation(
            issue=issue("chatgpt-task"),
            comments=comments(),
            source_issue=SOURCE,
            delivery_id=DELIVERY,
            target_run=target_run(),
        )
