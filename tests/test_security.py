from pathlib import Path

from portfolio_tasks.run_codex import sanitize


def test_token_redaction() -> None:
    assert "SECRET" not in sanitize("Authorization: Bearer SECRET")
    assert "sk-secret" not in sanitize("failure sk-secret")


def test_contract_shell_scripts_are_the_only_owned_shell_scripts() -> None:
    assert {path.name for path in Path("scripts").glob("*.sh")} == {
        "build-task-contract.sh", "task-contract-lib.sh", "validate-task-contract.sh"
    }
    assert not list(Path("tests").glob("*.sh"))
