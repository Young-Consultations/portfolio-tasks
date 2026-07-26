from portfolio_tasks.validation import validate_dispatch
from tests.test_validation import BODY


def test_closed_dependency_is_actionable() -> None:
    issue = {"body": BODY.replace("none", "#99"), "labels": ["project:slugger", "priority:P1"]}
    assert "Dependency reference is unresolved or closed: #99" in validate_dispatch(issue, {"#1"}).errors
