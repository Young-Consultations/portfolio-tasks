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
CONTROL_PLANE_RELEASE = "ai-sdlc-v3.0.1"
TRUSTED_ADMISSION_AUTHORS = frozenset({"mightyjoe909"})
SOURCE_WORKFLOW_AUTHOR = "github-actions[bot]"


def marker_comment(body: str, author: str) -> dict[str, object]:
    return {"body": body, "user": {"login": author}}


def comments(
    *extra: str,
    admission_author: str = "mightyjoe909",
    target_repository: str = TARGET,
    control_plane_release: str = CONTROL_PLANE_RELEASE,
) -> list[dict[str, object]]:
    admission = {
        "activation_revision": "3efbe6227a93fa23020ca807387e310f026a1528",
        "activation_sha256": "d1ade8bf193022e72a35738f5baf61528d98441bee28285c5e65a4c7e1dbd9aa",
        "contract_version": "ai-sdlc-contract/v2",
        "control_plane_release": control_plane_release,
        "correlation_id": DELIVERY,
        "delivery_id": DELIVERY,
        "source_issue": SOURCE,
        "target_repository": target_repository,
    }
    marker = (
        "<!-- ai-sdlc-admission:v2 "
        + json.dumps(admission, sort_keys=True, separators=(",", ":"))
        + " -->"
    )
    return [
        marker_comment(marker, admission_author),
        *(marker_comment(body, SOURCE_WORKFLOW_AUTHOR) for body in extra),
    ]


def issue(*labels: str) -> dict[str, object]:
    return {"state": "open", "labels": [{"name": label} for label in labels]}


def target_run(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": 36441714913,
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "failure",
        "html_url": f"https://github.com/{TARGET}/actions/runs/36441714913",
        "path": ".github/workflows/codex-execute.yml",
        "head_branch": "codex-adapter-v3.0.0",
        "repository": {"full_name": TARGET},
    }
    value.update(changes)
    return value


def target_log(**changes: object) -> str:
    payload: dict[str, object] = {
        "concurrency_group": "codex-young-consultations-consulting-playbook-real",
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": DELIVERY,
        "delivery_id": DELIVERY,
        "source_issue": SOURCE,
        "target_repository": TARGET,
    }
    payload.update(changes)
    return (
        "2026-09-28T15:11:55Z   EXECUTION_INPUT_JSON: "
        + json.dumps(payload, separators=(",", ":"), sort_keys=True)
        + "\n"
    )


def decide(
    *,
    issue_value: dict[str, object] | None = None,
    comment_values: list[dict[str, object]] | None = None,
    run: dict[str, object] | None = None,
    run_log: str | None = None,
):
    return decide_missing_result_reconciliation(
        issue=issue_value or issue("status:queued"),
        comments=comment_values or comments(),
        source_issue=SOURCE,
        delivery_id=DELIVERY,
        target_run=run or target_run(),
        target_run_log=run_log or target_log(),
        trusted_admission_authors=TRUSTED_ADMISSION_AUTHORS,
        expected_control_plane_release=CONTROL_PLANE_RELEASE,
    )


def test_live_pre_adapter_failure_enters_reconciliation_without_terminal_result() -> None:
    decision = decide(issue_value=issue("chatgpt-task", "status:queued"))
    assert decision.action == "apply"
    assert decision.target_repository == TARGET
    assert "reconciliation-required" in decision.marker
    assert "codex-adapter-v3.0.0" in decision.marker
    assert ".github/workflows/codex-execute.yml" in decision.marker
    assert "does **not** infer a target execution result" in decision.comment
    assert "ai-sdlc-source-result" not in decision.comment


def test_reconciliation_is_idempotent_for_same_delivery_and_target_run() -> None:
    first = decide()
    repeated = decide(
        issue_value=issue(),
        comment_values=comments(first.comment),
    )
    assert repeated.action == "no-op"
    assert repeated.marker == first.marker


@pytest.mark.parametrize(
    "run_change",
    [
        {"repository": {"full_name": "Young-Consultations/slugger"}},
        {"path": ".github/workflows/other.yml"},
        {"head_branch": "main"},
        {"event": "push"},
        {"status": "in_progress", "conclusion": None},
        {"conclusion": "success"},
        {"html_url": "https://github.com/Young-Consultations/slugger/actions/runs/1"},
    ],
)
def test_target_run_must_be_exact_completed_failed_evidence(run_change: dict[str, object]) -> None:
    with pytest.raises(ReconciliationError):
        decide(run=target_run(**run_change))


@pytest.mark.parametrize(
    "log_change",
    [
        {"delivery_id": "task-other"},
        {"correlation_id": "task-other"},
        {"source_issue": "Young-Consultations/portfolio-tasks#158"},
        {"target_repository": "Young-Consultations/slugger"},
    ],
)
def test_target_run_log_must_bind_exact_delivery(log_change: dict[str, object]) -> None:
    with pytest.raises(ReconciliationError, match="logs do not bind"):
        decide(run_log=target_log(**log_change))


def test_untrusted_admission_author_cannot_authorize_reconciliation() -> None:
    with pytest.raises(ReconciliationError, match="trusted admission"):
        decide(comment_values=comments(admission_author="attacker"))


def test_stale_control_plane_release_cannot_authorize_reconciliation() -> None:
    with pytest.raises(ReconciliationError, match="trusted admission"):
        decide(comment_values=comments(control_plane_release="ai-sdlc-v2.4.5"))


def test_malformed_target_repository_is_rejected_before_api_use() -> None:
    with pytest.raises(ReconciliationError, match="trusted admission"):
        decide(comment_values=comments(target_repository="Young-Consultations/../slugger"))


def test_existing_trusted_terminal_result_blocks_reconciliation() -> None:
    result = (
        "<!-- ai-sdlc-source-result:v2 "
        + json.dumps(
            {"delivery_id": DELIVERY, "result_sha256": "a" * 64},
            sort_keys=True,
            separators=(",", ":"),
        )
        + " -->"
    )
    with pytest.raises(ReconciliationError, match="terminal result"):
        decide(comment_values=comments(result))


def test_untrusted_terminal_marker_does_not_block_reconciliation() -> None:
    result = (
        "<!-- ai-sdlc-source-result:v2 "
        + json.dumps(
            {"delivery_id": DELIVERY, "result_sha256": "a" * 64},
            sort_keys=True,
            separators=(",", ":"),
        )
        + " -->"
    )
    values = comments()
    values.append(marker_comment(result, "attacker"))
    assert decide(comment_values=values).action == "apply"


def test_missing_or_duplicate_admission_fails_closed() -> None:
    with pytest.raises(ReconciliationError, match="exactly one"):
        admission_binding(
            [],
            source_issue=SOURCE,
            delivery_id=DELIVERY,
            trusted_admission_authors=TRUSTED_ADMISSION_AUTHORS,
            expected_control_plane_release=CONTROL_PLANE_RELEASE,
        )
    duplicated = comments()
    duplicated.append(duplicated[0].copy())
    with pytest.raises(ReconciliationError, match="exactly one"):
        admission_binding(
            duplicated,
            source_issue=SOURCE,
            delivery_id=DELIVERY,
            trusted_admission_authors=TRUSTED_ADMISSION_AUTHORS,
            expected_control_plane_release=CONTROL_PLANE_RELEASE,
        )


def test_first_reconciliation_requires_open_queued_source() -> None:
    with pytest.raises(ReconciliationError, match="open queued"):
        decide(issue_value=issue("chatgpt-task"))
