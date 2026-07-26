from pathlib import Path

from portfolio_tasks.run_codex import sanitize


def test_token_redaction() -> None:
    assert "SECRET" not in sanitize("Authorization: Bearer SECRET")
    assert "sk-secret" not in sanitize("failure sk-secret")


def test_no_owned_shell_scripts() -> None:
    assert not list(Path("scripts").glob("*.sh")) if Path("scripts").exists() else True
    assert not list(Path("tests").glob("*.sh"))
