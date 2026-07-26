import pytest
from portfolio_tasks.validation import parse_source_issue


@pytest.mark.parametrize("value", ["13", "Young-Consultations/portfolio-tasks#13", "https://github.com/Young-Consultations/portfolio-tasks/issues/13"])
def test_source_routes(value: str) -> None:
    assert parse_source_issue(value) == 13


@pytest.mark.parametrize("value", [" Young-Consultations/portfolio-tasks#13", "Young-Consultations/slugger#13", "https://github.com/Young-Consultations/portfolio-tasks/pull/13", "13;echo"])
def test_invalid_source_routes(value: str) -> None:
    with pytest.raises(ValueError):
        parse_source_issue(value)
