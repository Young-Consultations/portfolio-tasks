import json
from pathlib import Path

from portfolio_tasks.conformance import (
    COMPATIBILITY_SHA,
    Effects,
    report,
    run_scenarios,
)


def test_complete_applicable_conformance_matrix_passes_without_effects() -> None:
    results = run_scenarios()
    assert len(results) == 23
    assert set(results.values()) == {"passed"}
    Effects().assert_trapped()


def test_versioned_report_is_current_and_does_not_claim_production_readiness() -> None:
    expected = report()
    checked_in = json.loads(
        Path("conformance/reports/tc-mvp-ci-001-v1.json").read_text(encoding="utf-8")
    )
    assert checked_in == expected
    assert checked_in["compatibility_sha"] == COMPATIBILITY_SHA
    assert "not production readiness" in checked_in["scope"]
    assert checked_in["activation_requested"] is False


def test_normal_ci_cannot_reach_external_or_privileged_effects_or_emit_secrets() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8").lower()
    forbidden = (
        "openai_api_key",
        "codex exec",
        "git checkout -b",
        "git switch -c",
        "git commit",
        "git push",
        "gh pr create",
        "gh pr merge",
        "gh release",
        "deploy",
        "environment:",
        "secrets.",
        "set -x",
    )
    assert not {token for token in forbidden if token in workflow}
    assert "permissions:\n  contents: read" in workflow
