from portfolio_tasks.issue_parser import IssueFormParser, TargetRepositoryParser


def test_sections_stop_at_next_heading() -> None:
    parser = IssueFormParser("### Project\nslugger\n\n### Priority\nP1\n")
    assert parser.value("Project") == "slugger"
    assert parser.value("Priority") == "P1"


def test_target_repository_rejects_injection() -> None:
    assert TargetRepositoryParser.parse("Young-Consultations/slugger") == "Young-Consultations/slugger"
    assert TargetRepositoryParser.parse("repo; touch /tmp/pwned") is None
