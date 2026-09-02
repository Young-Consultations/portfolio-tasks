import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from portfolio_tasks.source_lifecycle import (
    TASK_MATERIAL_FIELDS,
    Approval,
    LifecycleError,
    ProjectionDecision,
    ResultProjection,
    RoutingRecord,
    SourceRevision,
    canonical_task,
    matching_admission_count,
    normalize_task_type,
)


def material(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "project": "portfolio-tasks",
        "priority": "p0",
        "task_type": "automation",
        "parallel_safe": False,
        "risk": "medium",
        "scope": "small",
        "instructions": "Make one bounded repository change.",
        "created_by": "octocat",
    }
    return values | changes


def revision(**changes: object) -> SourceRevision:
    values: dict[str, object] = {
        "source_issue": "Young-Consultations/portfolio-tasks#42",
        "material": material(),
        "status": "approved",
        "target_repository": "Young-Consultations/portfolio-tasks",
        "execution_mode": "implement",
    }
    return SourceRevision(**(values | changes))  # type: ignore[arg-type]


def approved(value: SourceRevision) -> Approval:
    return Approval(value.task_id, "human-reviewer", True)


def test_projection_matches_release_enriched_admission_marker_by_stable_binding() -> None:
    binding = {
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": "task-af9b0ed1cfbe6f88d671da896603fabf",
        "delivery_id": "task-af9b0ed1cfbe6f88d671da896603fabf",
        "source_issue": "Young-Consultations/portfolio-tasks#139",
        "target_repository": "Young-Consultations/consulting-playbook",
    }
    enriched = {
        "activation_revision": "ef7f9ab664b8be4fffc29161caaad5f9a26ef8e9",
        "activation_sha256": "d1ade8bf193022e72a35738f5baf61528d98441bee28285c5e65a4c7e1dbd9aa",
        **binding,
        "control_plane_release": "ai-sdlc-v2.4.1",
    }
    marker = (
        "<!-- ai-sdlc-admission:v2 "
        + json.dumps(enriched, sort_keys=True, separators=(",", ":"))
        + " -->"
    )

    assert matching_admission_count([{"body": marker}], binding) == 1
    assert (
        matching_admission_count([{"body": marker}], binding | {"delivery_id": "task-conflict"})
        == 0
    )
    assert matching_admission_count([{"body": marker + "\n" + marker}], binding) == 2


def test_approved_task_is_exact_schema_valid_and_uses_safe_identity() -> None:
    value = revision()
    task = canonical_task(value, approved(value))
    schema = json.loads(Path("contracts/task-contract.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(task)
    assert set(value.material) == TASK_MATERIAL_FIELDS
    assert task["status"] == "approved"
    assert str(task["task_id"]).startswith("task-")
    assert "/" not in str(task["task_id"]) and "#" not in str(task["task_id"])


@pytest.mark.parametrize(
    "change",
    [
        {"material": material(instructions="materially changed")},
        {"target_repository": "Young-Consultations/slugger"},
        {"execution_mode": "verify"},
        {"sensitivity": "sensitive"},
        {"dependencies": ("Young-Consultations/portfolio-tasks#1",)},
    ],
)
def test_every_authoritative_change_requires_fresh_approval(change: dict[str, object]) -> None:
    first = revision()
    edited = revision(**change)
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


def test_source_accepts_syntactically_valid_target_and_router_owns_membership() -> None:
    value = revision(target_repository="Young-Consultations/future-target")
    assert (
        canonical_task(value, approved(value))["target_repository"]
        == "Young-Consultations/future-target"
    )


@pytest.mark.parametrize("target", ["", "two targets", "owner/"])
def test_malformed_target_fails_closed(target: str) -> None:
    value = revision(target_repository=target)
    with pytest.raises(LifecycleError, match="target"):
        canonical_task(value, approved(value))


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Automation", "automation"),
        ("Backlog governance", "backlog-governance"),
        ("Bug fix", "bug-fix"),
        ("CI/CD", "ci-cd"),
        ("Documentation", "documentation"),
        ("Feature", "feature"),
        ("Repository maintenance", "repository-maintenance"),
        ("Security", "security"),
        ("Testing", "testing"),
    ],
)
def test_issue_form_task_type_vocabulary_is_explicit(label: str, expected: str) -> None:
    assert normalize_task_type(label) == expected


@pytest.mark.parametrize("label", ["Refactor", "Repository governance", "Investigation", ""])
def test_obsolete_or_unknown_task_type_fails_closed(label: str) -> None:
    with pytest.raises(LifecycleError, match="task type"):
        normalize_task_type(label)


@pytest.mark.parametrize(
    "bad_material",
    [
        material(scope=None),
        material(task_type="refactor"),
        material(extra="not-closed"),
        {key: value for key, value in material().items() if key != "risk"},
    ],
)
def test_incomplete_or_open_ended_task_material_fails_closed(
    bad_material: dict[str, object],
) -> None:
    value = revision(material=bad_material)
    with pytest.raises(LifecycleError, match="contract|scope|task type"):
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
        uncertain.retry(task | {"instructions": "conflict"})


def result(record: RoutingRecord, **changes: object) -> dict[str, object]:
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "delivery_id": record.delivery_id,
        "correlation_id": record.correlation_id,
        "target_repository": "Young-Consultations/portfolio-tasks",
        "execution_status": "draft-pr-created",
        "validation_result": "passed",
        "test_result": "passed",
        "failure_category": "none",
        "failure_message": None,
        "branch_name": f"codex/{record.delivery_id}",
        "pull_request_url": "https://github.com/Young-Consultations/portfolio-tasks/pull/1",
        "workflow_url": "https://github.com/Young-Consultations/portfolio-tasks/actions/runs/1",
        "started_at": "2026-08-14T00:00:00Z",
        "completed_at": "2026-08-14T00:01:00Z",
    } | changes


def test_valid_duplicate_conflicting_and_receiver_rejected_result_projection() -> None:
    source = "Young-Consultations/portfolio-tasks#42"
    value = revision()
    record = RoutingRecord.reserve(canonical_task(value, approved(value))).router_outcome(
        "accepted"
    )
    projection = ResultProjection(record)
    applied, decision = projection.apply(
        result(record), receiver_accepted=True, expected_source=source
    )
    assert decision is ProjectionDecision.APPLIED
    assert (
        applied.apply(result(record), receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.NO_OP
    )
    conflict = result(
        record,
        execution_status="failed",
        failure_category="tests",
        failure_message="Tests failed.",
        branch_name=None,
        pull_request_url=None,
    )
    assert (
        applied.apply(conflict, receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
    assert (
        projection.apply(result(record), receiver_accepted=False, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )


def test_result_binding_and_terminal_transition_fail_closed() -> None:
    source = "Young-Consultations/portfolio-tasks#42"
    value = revision()
    pending = RoutingRecord.reserve(canonical_task(value, approved(value)))
    projection = ResultProjection(pending)
    assert (
        projection.apply(result(pending), receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
    queued = ResultProjection(pending.router_outcome("accepted"))
    wrong = result(queued.record, correlation_id="correlation-wrong")
    assert (
        queued.apply(wrong, receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
    nonterminal = result(queued.record, execution_status="running")
    assert (
        queued.apply(nonterminal, receiver_accepted=True, expected_source=source)[1]
        is ProjectionDecision.QUARANTINED
    )
