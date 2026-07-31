from pathlib import Path

CONTRACT_PATH = Path("docs/github-projects-phase1-contract.md")


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_projects_phase1_contract_defines_responsibility_split() -> None:
    text = _contract_text()
    assert "## Responsibility split" in text
    for scope in (
        "Issues in `Young-Consultations/portfolio-tasks`",
        "GitHub Projects (organization project)",
        "Router and dispatch workflows (`route-approved-task.yml`, `codex-execute.yml`)",
        "Target repositories (for example `Young-Consultations/slugger`)",
    ):
        assert scope in text
    assert "issue form body and" in text
    assert "deterministic labels in `Young-Consultations/portfolio-tasks` are authoritative" in text


def test_projects_phase1_contract_keeps_deterministic_field_mapping() -> None:
    text = _contract_text()
    expected = {
        "`Project`": "`slugger`, `consulting`, `portfolio-backlog-schema`",
        "`Priority`": "`P0`, `P1`, `P2`, `P3`",
        "`Executor`": "`codex`, `human`, `chatgpt-planning`",
        "`Execution status`": "`proposed`, `approved`, `queued`, `running`, `draft-pr`, `blocked`, `done`",
        "`Target repository`": "`owner/repository`",
        "`Parallel-safe`": "`yes`, `no`",
        "`Dependency issue references`": "`none`, `#123`, `owner/repository#123`",
        "`Risk`": "`low`, `medium`, `high`",
        "`Estimated scope`": "`small`, `medium`, `large`",
        "`Task type`": "`Bug fix`, `Feature`, `Refactor`, `CI/CD`",
    }
    for field_name, allowed_values in expected.items():
        assert field_name in text
        assert allowed_values in text


def test_projects_phase1_contract_documents_four_required_views() -> None:
    text = _contract_text()
    for view_name in (
        "`01 Intake and triage`",
        "`02 Ready for router dispatch`",
        "`03 Execution in progress`",
        "`04 Done and archive`",
    ):
        assert view_name in text
    assert "`Execution status in {queued, running, draft-pr, blocked}`" in text
    assert "Group by `Execution status`" in text
    assert "Sort by `Priority` (high to low)" in text


def test_projects_phase1_contract_has_reproducible_manual_setup_without_sync() -> None:
    text = _contract_text()
    for expected_step in (
        "Open `https://github.com/orgs/Young-Consultations/projects`",
        "Create a new organization project named `Portfolio Tasks - Phase 1`",
        "Add repository access for `Young-Consultations/portfolio-tasks`",
        "Create the four required views with the exact filters, grouping, and sorting",
        "Confirm no project workflow automation is required",
    ):
        assert expected_step in text
    assert "## Phase 1 operating notes (no synchronization automation)" in text


def test_projects_phase1_contract_documents_required_identifiers_and_workflow_inputs() -> None:
    text = _contract_text()
    for identifier in (
        "`Young-Consultations`",
        "`Young-Consultations/portfolio-tasks`",
        "`Young-Consultations/slugger`",
        "`AI_SDLC_CONTRACTS_COMMIT_SHA`",
        "`CODEX_MODEL`",
        "`SLUGGER_GITHUB_TOKEN`",
        "`OPENAI_API_KEY`",
        "`SLUGGER_ISSUES_TOKEN`",
    ):
        assert identifier in text
    assert "do not create, rotate," in text
    assert "or change them as part of this contract definition task" in text
