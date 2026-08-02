import pytest

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
    assert not route_decision(
        task(target="Young-Consultations/portfolio-tasks", labels=APPROVED[:-1])
    ).route


@pytest.mark.parametrize(
    "terminal_label",
    ["status:queued", "status:running", "status:draft-pr", "status:done"],
)
def test_terminal_task_state_is_skipped(terminal_label: str) -> None:
    assert not route_decision(
        task(target="Young-Consultations/portfolio-tasks", labels=APPROVED + (terminal_label,))
    ).route


def test_sensitive_task_is_skipped() -> None:
    assert not route_decision(
        task(target="Young-Consultations/portfolio-tasks", labels=APPROVED + ("sensitive",))
    ).route


def test_non_approval_label_does_not_route() -> None:
    labels = ("chatgpt-task", "executor:codex", "status:proposed")
    assert not route_decision(
        task(target="Young-Consultations/portfolio-tasks", labels=labels)
    ).route
