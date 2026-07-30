"""Static compatibility checks for the canonical target workflow boundary."""

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/codex-execute.yml")
ROUTING_WORKFLOW = Path(".github/workflows/route-approved-task.yml")
WORKFLOWS = tuple(Path(".github/workflows").glob("*.y*ml"))
CANONICAL_INPUTS = {
    "execution_input_json",
    "execution_input_artifact",
    "execution_input_run_id",
    "concurrency_group",
}
CONTRACT_FIELDS = {
    "contract_version",
    "source_issue",
    "task_type",
    "execution_mode",
    "priority",
    "executor",
    "instructions",
}


def test_canonical_workflow_dispatch_interface() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    input_block = text[text.index("    inputs:\n") : text.index("\npermissions:\n")]
    names = set(re.findall(r"^      ([a-z_]+):$", input_block, re.MULTILINE))

    assert names == CANONICAL_INPUTS
    assert not CONTRACT_FIELDS.intersection(names)
    required: dict[str, str] = {}
    for name in names:
        block = input_block[input_block.index(f"      {name}:\n") :]
        match = re.search(r"^        required: (true|false)$", block, re.MULTILINE)
        assert match is not None
        required[name] = match.group(1)
    assert required["concurrency_group"] == "true"
    for name in CANONICAL_INPUTS - {"concurrency_group"}:
        assert required[name] == "false"


def test_every_third_party_action_is_pinned_to_a_commit() -> None:
    unpinned: list[str] = []
    for workflow in Path(".github/workflows").glob("*.y*ml"):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*uses:\s*([^\s#]+)", line)
            if not match:
                continue
            reference = match.group(1)
            if reference.startswith("./"):
                continue
            if reference == (
                "Young-Consultations/.github/.github/workflows/codex-router.yml@main"
            ):
                # The central router is deliberately consumed from its policy branch.
                continue
            if not re.fullmatch(r"[^@]+@[0-9a-fA-F]{40}", reference):
                unpinned.append(f"{workflow}: {reference}")
    assert not unpinned, "unpinned third-party actions:\n" + "\n".join(unpinned)


def test_checkout_never_persists_github_credentials() -> None:
    unsafe_checkouts: list[str] = []
    for workflow in WORKFLOWS:
        lines = workflow.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not re.match(r"\s*uses:\s*actions/checkout@", line):
                continue
            step = "\n".join(lines[index + 1 : index + 4])
            if "persist-credentials: false" not in step:
                unsafe_checkouts.append(str(workflow))

    assert not unsafe_checkouts, (
        "checkout persists the workflow token: " + ", ".join(unsafe_checkouts)
    )


def test_execution_modes_remain_isolated_and_emit_canonical_results() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    implement_guard = "if: steps.input.outputs.execution_mode == 'implement'"

    assert text.count(implement_guard) == 2
    assert text.index(implement_guard) < text.index("python -m portfolio_tasks.run_codex")
    assert text.index(implement_guard, text.index("Create task branch"))
    assert "codex_status=$?" in text
    assert "codex_status != 0" in text
    assert 'codex_outcome=$(jq -r .status "$TASK_WORKTREE/codex-result.json")' in text
    assert 'rm -- "$TASK_WORKTREE/codex-result.json"' in text
    assert (
        '[[ -z "$(git -C "$TASK_WORKTREE" status '
        '--porcelain=v1 --untracked-files=all)" ]]' in text
    )
    assert "if: always() && steps.input.outcome == 'success'" in text
    assert "python -m portfolio_tasks.execution execution-status" in text
    assert 'target_repository:"Young-Consultations/portfolio-tasks"' in text


def test_already_satisfied_implementation_is_validated_without_publication() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    validation = text[text.index("- name: Validate target repository") :]
    publication = text[text.index("- name: Create task branch and draft PR") :]
    emit = text.index("- name: Emit canonical execution result")
    upload = text.index("- name: Upload canonical execution result")
    assert "steps.codex.outcome == 'success'" in validation.split("id: validation", 1)[0]
    assert "steps.codex.outputs.outcome == 'changed'" in publication.split("id: publish", 1)[0]
    assert "already_satisfied" in text
    assert '[[ "$MODE" == verify || "$NO_CHANGES" == true ]]' in text
    assert emit < upload
    assert "if: always()" in text[upload:]


def test_publication_uses_helper_from_trusted_commit() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    publication = text[text.index("- name: Create task branch and draft PR") :]
    publication = publication.split("- name: Emit canonical execution result", 1)[0]

    assert "export PATH=/usr/bin:/bin" in publication
    assert 'GIT_NO_REPLACE_OBJECTS=1 /usr/bin/git show \\' in publication
    assert '"$GITHUB_SHA:scripts/publish-draft-pr"' in publication
    assert '"$RUNNER_TEMP/publish-draft-pr"' in publication
    assert '/usr/bin/bash "$trusted_publish"' in publication
    assert "scripts/publish-draft-pr\n" not in publication


def test_trusted_runtime_and_mutable_task_worktree_are_isolated() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "ref: ${{ github.sha }}" in text
    assert 'TASK_WORKTREE=%s\\n' in text
    assert 'git worktree add' in Path("scripts/prepare-task-branch").read_text(encoding="utf-8")
    assert "git switch" not in Path("scripts/prepare-task-branch").read_text(encoding="utf-8")
    assert 'export PYTHONPATH="$GITHUB_WORKSPACE"' in text
    assert 'python -c "from portfolio_tasks.prompts import render_execution_prompt"' in text
    assert text.index("Trusted runtime preflight failed") < text.index("npm install --global")
    assert '--working-directory "$TASK_WORKTREE"' in text
    assert 'git -C "$TASK_WORKTREE" status' in text
    validation = text[text.index("- name: Validate target repository") :]
    validation = validation.split("- name: Create task branch", 1)[0]
    assert 'cd "$GITHUB_WORKSPACE"' in validation
    assert 'export PYTHONPATH="$GITHUB_WORKSPACE"' in validation
    assert '--working-directory "$TARGET_WORKTREE"' in validation
    assert 'cd "$TARGET_WORKTREE"' not in validation


def test_publication_git_operations_are_scoped_to_task_worktree() -> None:
    script = Path("scripts/publish-draft-pr").read_text(encoding="utf-8")
    for operation in ("status", "config", "add", "diff", "commit", "push"):
        assert f'git -C "$TASK_WORKTREE" {operation}' in script


def test_workflow_validation_avoids_unquoted_command_substitution() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    validation = text[text.index("- name: Validate target repository") :]
    assert "$(find " not in validation

    unsafe_yaml_checks = [
        str(workflow)
        for workflow in WORKFLOWS
        if "YAML.safe_load_file" in workflow.read_text(encoding="utf-8")
        and "$(find " in workflow.read_text(encoding="utf-8")
    ]
    assert not unsafe_yaml_checks, (
        "workflow YAML validation uses an unquoted find substitution: "
        + ", ".join(unsafe_yaml_checks)
    )


def test_actionlint_is_independent_of_runner_shellcheck() -> None:
    invocations = []
    for workflow in WORKFLOWS:
        invocations.extend(
            line.strip()
            for line in workflow.read_text(encoding="utf-8").splitlines()
            if 'bin/actionlint"' in line
        )

    assert invocations
    assert all(invocation.endswith(" -shellcheck=") for invocation in invocations)


def test_actionlint_is_installed_before_codex_and_not_during_validation() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    install = text.index("- name: Install pinned actionlint before Codex execution")
    codex = text.index("- name: Install and execute Codex")
    validation = text[text.index("- name: Validate target repository") :]

    assert install < codex
    assert "@v1.7.7" not in validation
    assert "go install" not in validation
    assert "python -m portfolio_tasks.runtime_validation" in validation


def test_diagnostics_upload_is_failure_or_debug_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    diagnostics = text[text.index("- name: Upload full execution diagnostics") :]

    assert "if: failure() || vars.CODEX_DEBUG_LOGGING == 'true'" in diagnostics
    for artifact in (
        "codex-trace.log", "codex-result.json", "validation.log", "git-diff.patch"
    ):
        assert artifact in diagnostics


def test_execution_authorization_accepts_router_queued_status() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    authorization = text[text.index("- name: Verify router authorization") :]

    assert 'index("status:approved") != null or index("status:queued") != null' in authorization


def test_approved_task_router_uses_shared_workflow_contract() -> None:
    text = ROUTING_WORKFLOW.read_text(encoding="utf-8")
    route_job = text[text.index("  route:\n") : text.index("\n  mark-queued:\n")]

    assert "needs: prepare" in route_job
    assert "if: needs.prepare.outputs.route == 'true'" in route_job
    assert (
        "uses: Young-Consultations/.github/.github/workflows/codex-router.yml@main"
        in route_job
    )
    assert "task_payload: ${{ needs.prepare.outputs.task_contract_json }}" in route_job
    assert "execution_mode: implement" in route_job
    assert "CODEX_ROUTER_TOKEN: ${{ secrets.SLUGGER_GITHUB_TOKEN }}" in route_job
    assert "task_contract_json:" not in route_job
    assert "router_token:" not in route_job


def test_approved_task_router_uses_canonical_contract_cli_commands() -> None:
    text = ROUTING_WORKFLOW.read_text(encoding="utf-8")
    contract_step = text[text.index("- name: Build and validate canonical task contract") :]

    assert "python -m ai_sdlc_contracts build-task-contract" in contract_step
    assert "python -m ai_sdlc_contracts validate-task " in contract_step
    assert "python -m ai_sdlc_contracts validate-task-contract" not in contract_step


def test_issue_edits_invalidate_approval_without_routing() -> None:
    text = ROUTING_WORKFLOW.read_text(encoding="utf-8")

    assert "invalidate-edited-approval:" in text
    assert "if: github.event.action == 'edited'" in text
    assert "labels/status%3Aapproved" in text
    assert "prepare:\n    if: github.event.action != 'edited'" in text
