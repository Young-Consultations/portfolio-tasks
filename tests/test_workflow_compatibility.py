"""Static compatibility checks for the canonical target workflow boundary."""

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/codex-execute.yml")
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
            if not re.fullmatch(r"[^@]+@[0-9a-fA-F]{40}", reference):
                unpinned.append(f"{workflow}: {reference}")
    assert not unpinned, "unpinned third-party actions:\n" + "\n".join(unpinned)


def test_execution_modes_remain_isolated_and_emit_canonical_results() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    implement_guard = "if: steps.input.outputs.execution_mode == 'implement'"

    assert text.count(implement_guard) == 2
    assert text.index(implement_guard) < text.index("python -m portfolio_tasks.run_codex")
    assert text.index(implement_guard, text.index("Create task branch"))
    assert '[[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]' in text
    assert "if: always() && steps.input.outcome == 'success'" in text
    assert '[[ "$MODE" == verify || "$PUBLISH_OUTCOME" == success ]]' in text
    assert 'target_repository:"Young-Consultations/portfolio-tasks"' in text


def test_workflow_validation_avoids_unquoted_command_substitution() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    validation = text[text.index("- name: Validate target repository") :]
    yaml_validation = next(
        line for line in validation.splitlines() if "YAML.safe_load_file" in line
    )

    assert "$(find " not in yaml_validation
    assert 'Dir.glob(".github/**/*.{yml,yaml}")' in yaml_validation

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
