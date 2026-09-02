"""Workflow, source-boundary, and single-path security regression tests."""

import re
from pathlib import Path

WORKFLOWS = Path(".github/workflows")
TARGET = WORKFLOWS / "codex-execute.yml"
ROUTE = WORKFLOWS / "route-approved-task.yml"
PROJECTION = WORKFLOWS / "project-execution-result.yml"


def test_exactly_one_active_target_path_and_four_expected_workflows() -> None:
    workflows = tuple(sorted(WORKFLOWS.glob("*.yml")))
    assert workflows == (
        WORKFLOWS / "ci.yml",
        TARGET,
        PROJECTION,
        ROUTE,
    )
    for obsolete in (
        Path("portfolio_tasks/target_adapter.py"),
        Path("portfolio_tasks/conformance.py"),
        Path("portfolio_tasks/runtime_validation.py"),
        Path("portfolio_tasks/codex_subprocess.py"),
        Path("conformance/reports/tc-mvp-ci-001-v2.json"),
    ):
        assert not obsolete.exists()


def test_target_exposes_exact_two_input_dispatch_and_pinned_receiver() -> None:
    text = TARGET.read_text(encoding="utf-8")
    trigger = text.split("on:", 1)[1].split("permissions:", 1)[0]
    inputs = trigger.split("inputs:", 1)[1]
    assert "workflow_dispatch:" in trigger
    assert "workflow_call:" not in text
    assert inputs.count("execution_input_json:") == 1
    assert inputs.count("concurrency_group:") == 1
    assert re.findall(r"^      ([a-z_]+):$", inputs, re.MULTILINE) == [
        "execution_input_json",
        "concurrency_group",
    ]
    assert "codex-result-receiver.yml@ai-sdlc-v2.3.2" in text
    assert "CODEX_TRUSTED_JOURNAL_AUTHORS" not in text
    assert "secrets: inherit" not in text
    receiver = text.split("  report:", 1)[1]
    assert receiver.count("CODEX_RESULT_TOKEN:") == 1


def test_target_has_least_privilege_and_credential_separation() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in text
    assert "persist-credentials: false" in text
    assert "fetch-depth: 0" in text
    assert "environment: portfolio-tasks-codex-production" in text
    assert "@openai/codex@0.63.0" in text
    assert "CODEX_TARGET_TRUSTED_CALLERS" in text
    assert "TARGET_PUBLICATION_TOKEN" in text
    assert "OPENAI_API_KEY" in text
    assert "gh pr merge" not in text
    assert "git push origin main" not in text
    references = re.findall(r"(?:uses: )\S+@(\S+)", text)
    commit_references = [ref for ref in references if not ref.startswith("ai-sdlc-")]
    assert commit_references and all(
        re.fullmatch(r"[0-9a-f]{40}", ref) for ref in commit_references
    )


def test_source_route_has_required_caller_permission_and_exact_construction() -> None:
    text = ROUTE.read_text(encoding="utf-8")
    assert "permissions:\n  actions: read\n  contents: read\n  issues: write" in text
    assert "codex-router.yml@ai-sdlc-v2.4.1" in text
    assert "contracts/task-contract.schema.json" in text
    assert "Draft202012Validator" in text
    assert "normalize_task_type" in text
    for field in (
        '"project"',
        '"priority"',
        '"task_type"',
        '"parallel_safe"',
        '"risk"',
        '"scope"',
        '"instructions"',
        '"created_by"',
    ):
        assert field in text
    assert "lower().replace" not in text
    assert "c6090e5bbadcc2102a1cb91875466e9decdada1e" not in text


def test_admission_rereads_current_revision_and_delegates_journal_ownership() -> None:
    text = ROUTE.read_text(encoding="utf-8")
    construct = text[text.index("      - name: Construct and validate") :]
    assert 'gh api "repos/$GITHUB_REPOSITORY/issues/$ISSUE"' in construct
    assert "current-issue.json" in construct
    assert "event_revision.task_id != current_revision.task_id" in construct
    assert '"status:approved" not in labels' in construct
    assert 'status="approved"' in construct
    assert "toJSON(github.event.issue)" not in construct
    assert 'open(os.environ["GITHUB_EVENT_PATH"]' in construct
    assert "issues/$ISSUE/events?per_page=100" in construct
    assert 'latest_approval.get("created_at") != event_issue.get("updated_at")' in construct
    assert 'latest_actor.get("login") != os.environ["GITHUB_ACTOR"]' in construct
    assert "EVENT_UPDATED_AT" not in text
    assert "Execution status" not in text
    assert "<!-- ai-sdlc-admission:v2 " not in text
    assert "issues/$ISSUE/comments" not in text


def test_result_projection_slurps_all_comment_pages() -> None:
    text = PROJECTION.read_text(encoding="utf-8")
    assert "gh api --paginate --slurp" in text
    assert "jq -c 'add'" in text


def test_result_projection_accepts_only_authenticated_receiver_dispatch() -> None:
    text = PROJECTION.read_text(encoding="utf-8")
    assert "repository_dispatch:" in text
    assert "types: [ai-sdlc-execution-result-v2]" in text
    assert "workflow_call:" not in text
    assert "PORTFOLIO_RESULT_SENDERS" in text
    assert "secrets:" not in text
    assert 'set(payload) != {"source_issue", "execution_result"}' in text
    assert "contracts/execution-result.schema.json" in text
    assert "Draft202012Validator" in text
    assert "TERMINAL_STATUSES" in text
    assert "matching_admission_count" in text
    assert 'json.loads(os.environ["ADMISSION_BINDING"])' in text
    assert 'jq --arg marker "$ADMISSION_MARKER"' not in text
    assert '"ADMISSION_BINDING"' in text
    assert "<!-- ai-sdlc-source-result:v2 " in text
    assert "status:result-quarantined" in text


def test_normal_ci_has_no_codex_or_publication_effect() -> None:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "openai_api_key",
        "target_publication_token",
        "codex exec",
        "git checkout -b",
        "git push",
        "gh pr create",
        "gh pr merge",
        "gh release",
        "environment:",
        "secrets.",
    ):
        assert forbidden not in text
    assert "python scripts/run_tc_mvp_ci_001.py" in text
    assert "git diff --exit-code -- .ai-sdlc/conformance/tc-mvp-ci-001.json" in text
