from portfolio_tasks.models import Issue
from portfolio_tasks.routing import route_decision


def task(*, target: str, labels: tuple[str, ...]) -> Issue:
    return Issue(
        number=42,
        title="Approved work",
        body=f"### Target repository\n\n{target}",
        state="open",
        labels=labels,
    )


APPROVED = ("chatgpt-task", "executor:codex", "status:approved")


def test_approved_portfolio_task_routes() -> None:
    assert route_decision(task(target="Young-Consultations/portfolio-tasks", labels=APPROVED)).route


def test_approved_slugger_task_routes() -> None:
    assert route_decision(task(target="Young-Consultations/slugger", labels=APPROVED)).route


def test_non_approved_task_is_skipped() -> None:
    assert not route_decision(task(target="Young-Consultations/portfolio-tasks", labels=APPROVED[:-1])).route


def test_non_approval_status_label_is_skipped() -> None:
    labels = ("chatgpt-task", "executor:codex", "status:running")
    assert not route_decision(task(target="Young-Consultations/portfolio-tasks", labels=labels)).route


def test_duplicate_queued_task_is_skipped() -> None:
    assert not route_decision(task(target="Young-Consultations/portfolio-tasks", labels=APPROVED + ("status:queued",))).route


def test_approval_routes_once_with_duplicate_label_entries() -> None:
    duplicated = APPROVED + ("status:approved",)
    decision = route_decision(task(target="Young-Consultations/portfolio-tasks", labels=duplicated))
    assert decision.route
    assert decision.reason == "approved"


def test_sensitive_task_is_skipped() -> None:
    assert not route_decision(task(target="Young-Consultations/portfolio-tasks", labels=APPROVED + ("sensitive",))).route
