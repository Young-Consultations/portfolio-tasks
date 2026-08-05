import pytest

from portfolio_tasks.idempotency import (
    CONTRACT_VERSION,
    DeliveryIdentity,
    deterministic_branch,
    dispatch_marker,
    fallback_delivery_id,
    marker_matches,
    parse_dispatch_markers,
    publication_marker,
    stable_task_id,
    terminal_source_update,
    validate_delivery_identity,
)


def identity() -> DeliveryIdentity:
    task_id = stable_task_id(
        source_issue="Young-Consultations/portfolio-tasks#42",
        issue_title="Title",
        issue_body="Body",
    )
    delivery_id = fallback_delivery_id(task_id)
    return DeliveryIdentity(
        contract_version=CONTRACT_VERSION,
        source_issue="Young-Consultations/portfolio-tasks#42",
        task_id=task_id,
        delivery_id=delivery_id,
        target_repository="Young-Consultations/portfolio-tasks",
        requested_branch=deterministic_branch(delivery_id),
    )


def test_dispatch_marker_round_trips_and_validates_owner() -> None:
    ident = identity()
    [marker] = parse_dispatch_markers(dispatch_marker(ident, "dispatching"))
    assert marker_matches(marker, ident)
    assert marker["dispatch_state"] == "dispatching"


def test_delivery_identity_rejects_branch_conflict() -> None:
    ident = identity()
    with pytest.raises(ValueError, match="requested_branch"):
        validate_delivery_identity({**ident.__dict__, "requested_branch": "codex/other"})


def test_publication_marker_contains_no_prompt_or_secret() -> None:
    ident = identity()
    text = publication_marker(ident, "completed") + terminal_source_update(
        ident, "completed", "https://example.invalid/pr/1"
    )
    assert "instructions" not in text
    assert "token" not in text.lower()
    assert ident.delivery_id in text
