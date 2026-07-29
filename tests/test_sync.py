from portfolio_tasks.issue_sync import MirrorLocator, SyncPlanner
from portfolio_tasks.models import Issue, SyncAction
from tests.helpers import SLUGGER_ISSUE_BODY


def issue(**changes: object) -> Issue:
    values = {
        "number": 1,
        "title": "T",
        "body": SLUGGER_ISSUE_BODY,
        "state": "open",
        "labels": ("chatgpt-task",),
        "html_url": "https://github.com/Young-Consultations/portfolio-tasks/issues/1",
    }
    values.update(changes)
    return Issue(**values)  # type: ignore[arg-type]


def test_create_skip_and_disable_actions() -> None:
    assert SyncPlanner.plan(issue(), None).action is SyncAction.CREATE
    assert SyncPlanner.plan(issue(labels=()), None).action is SyncAction.SKIPPED
    assert SyncPlanner.plan(issue(labels=()), issue(number=9), True).action is SyncAction.DISABLE_SYNC


def test_slugger_target_is_synchronized() -> None:
    assert SyncPlanner.plan(issue(), None).action is SyncAction.CREATE


def test_non_slugger_targets_are_skipped() -> None:
    for repository in (
        "Young-Consultations/portfolio-tasks",
        "Young-Consultations/consulting-playbook",
    ):
        source = issue(body=SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", repository))
        assert SyncPlanner.plan(source, None).action is SyncAction.SKIPPED_TARGET_REPOSITORY


def test_missing_target_is_skipped_safely() -> None:
    assert SyncPlanner.plan(issue(body="No structured target"), None).action is (
        SyncAction.SKIPPED_TARGET_REPOSITORY
    )


def test_malformed_target_is_skipped_safely() -> None:
    source = issue(body=SLUGGER_ISSUE_BODY.replace("Young-Consultations/slugger", "bad target"))
    assert SyncPlanner.plan(source, None).action is SyncAction.SKIPPED_TARGET_REPOSITORY


def test_close_reopen_and_noop() -> None:
    source = issue()
    desired = SyncPlanner.desired(source, None)
    target = issue(number=9, title=desired["title"], body=desired["body"], labels=("portfolio-task",))
    assert SyncPlanner.plan(source, target).action is SyncAction.NO_OP
    assert SyncPlanner.plan(issue(state="closed"), target).action is SyncAction.CLOSE
    assert SyncPlanner.plan(source, issue(number=9, state="closed")).action is SyncAction.REOPEN


def test_locator_uses_terminal_marker_and_migrates_legacy_namespace() -> None:
    real = issue(number=9, body="x\n## Portfolio Task Metadata\ny\n<!-- portfolio-task-source: mightyjoe909/portfolio-tasks#1 -->")
    copied = issue(number=8, body="x <!-- portfolio-task-source: Young-Consultations/portfolio-tasks#1 --> copied")
    assert MirrorLocator.locate([copied, real], 1) == real


def test_markers_in_source_are_sanitized() -> None:
    source = issue(body="copied <!-- portfolio-task-source: owner/repo#2 --> marker")
    body = SyncPlanner.body(source)
    assert "owner/repo#2" not in body
    assert "[removed portfolio-task-source marker]" in body
