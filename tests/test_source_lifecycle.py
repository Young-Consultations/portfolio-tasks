import pytest

from portfolio_tasks.source_lifecycle import (
    Approval,
    LifecycleError,
    ProjectionDecision,
    ResultProjection,
    RoutingRecord,
    SourceRevision,
    canonical_task,
)


def revision(**changes: object) -> SourceRevision:
    values: dict[str, object] = {
        "source_issue": "Young-Consultations/portfolio-tasks#42",
        "material": {"objective": "bounded change", "task_type": "automation"},
        "status": "approved",
        "target_repository": "Young-Consultations/portfolio-tasks",
        "execution_mode": "implement",
    }
    return SourceRevision(**(values | changes))  # type: ignore[arg-type]


def approved(value: SourceRevision) -> Approval:
    return Approval(value.task_id, "octocat", True)


def test_approved_admission_and_material_edit_requires_reapproval() -> None:
    first = revision()
    assert canonical_task(first, approved(first))["status"] == "approved"
    edited = revision(material={"objective": "materially changed", "task_type": "automation"})
    assert edited.task_id != first.task_id
    with pytest.raises(LifecycleError, match="stale"):
        canonical_task(edited, approved(first))


@pytest.mark.parametrize("state", ["proposed", "queued", "withdrawn", "cancelled", "superseded"])
def test_only_approved_is_fresh_authority(state: str) -> None:
    value = revision(status=state)
    with pytest.raises(LifecycleError, match="only approved"):
        canonical_task(value, approved(value))


@pytest.mark.parametrize(
    "target",
    [
        "Young-Consultations/.github",
        "Young-Consultations/consulting-playbook",
        "Young-Consultations/portfolio-tasks",
        "Young-Consultations/slugger",
    ],
)
def test_all_four_target_selections(target: str) -> None:
    value = revision(target_repository=target)
    assert canonical_task(value, approved(value))["target_repository"] == target


@pytest.mark.parametrize("target", ["Young-Consultations/unknown", "", "two targets"])
def test_unknown_or_malformed_target_fails_closed(target: str) -> None:
    value = revision(target_repository=target)
    with pytest.raises(LifecycleError, match="target"):
        canonical_task(value, approved(value))


def test_retry_preserves_delivery_and_rejects_blind_or_conflicting_retry() -> None:
    value = revision()
    task = canonical_task(value, approved(value))
    record = RoutingRecord.reserve(task)
    with pytest.raises(LifecycleError, match="reconciliation"):
        record.retry(task)
    uncertain = record.router_outcome("unknown")
    retried = uncertain.retry(task)
    assert retried.delivery_id == record.delivery_id
    assert retried.correlation_id == record.correlation_id
    with pytest.raises(LifecycleError, match="different content"):
        uncertain.retry(task | {"objective": "conflict"})


def result(record: RoutingRecord, source: str, **changes: object) -> dict[str, object]:
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "task_id": record.task_id,
        "delivery_id": record.delivery_id,
        "correlation_id": record.correlation_id,
        "source_issue": source,
        "target_repository": "Young-Consultations/portfolio-tasks",
        "execution_status": "published",
        "validation_result": "passed",
        "failure_category": None,
        "diagnostic_summary": None,
        "pull_request_url": "https://github.com/Young-Consultations/portfolio-tasks/pull/1",
    } | changes


def test_valid_duplicate_conflicting_and_receiver_rejected_result_projection() -> None:
    source = "Young-Consultations/portfolio-tasks#42"
    value = revision()
    record = RoutingRecord.reserve(canonical_task(value, approved(value))).router_outcome(
        "accepted"
    )
    projection = ResultProjection(record)
    applied, decision = projection.apply(
        result(record, source), receiver_accepted=True, expected_source=source
    )
    assert decision is ProjectionDecision.APPLIED
    assert (
        applied.apply(result(record, source), receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.NO_OP
    )
    conflict = result(record, source, execution_status="failed")
    assert (
        applied.apply(conflict, receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
    assert (
        projection.apply(result(record, source), receiver_accepted=False, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )


def test_result_binding_and_terminal_transition_fail_closed() -> None:
    source = "Young-Consultations/portfolio-tasks#42"
    value = revision()
    pending = RoutingRecord.reserve(canonical_task(value, approved(value)))
    projection = ResultProjection(pending)
    assert (
        projection.apply(result(pending, source), receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
    queued = ResultProjection(pending.router_outcome("accepted"))
    wrong = result(queued.record, source, correlation_id="correlation-wrong")
    assert (
        queued.apply(wrong, receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
