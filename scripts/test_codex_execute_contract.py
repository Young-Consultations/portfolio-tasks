"""Offline contract, adapter, evidence, and security regression checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codex_target_adapter import (
    TARGET,
    AdapterError,
    Ownership,
    canonical_digest,
    run_adapter,
)
from run_tc_mvp_ci_001 import EXPECTED_COMPATIBILITY_BLOBS, git_blob_sha1, validate_pin

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/codex-execute.yml").read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def payload(**changes: Any) -> dict[str, Any]:
    delivery_id = "delivery-42"
    value = {
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": "correlation-42",
        "delivery_id": delivery_id,
        "source_issue": "Young-Consultations/portfolio-tasks#135",
        "target_repository": TARGET,
        "task_type": "documentation",
        "execution_mode": "implement",
        "project": "portfolio-tasks",
        "priority": "p0",
        "executor": "codex",
        "parallel_safe": False,
        "draft_pr_only": True,
        "instructions": "Update the approved portfolio artifact.",
        "requested_branch": f"codex/{delivery_id}",
        "concurrency_group": "ai-sdlc.portfolio.delivery-42",
        "timeout_minutes": 40,
    }
    value.update(changes)
    return value


class FakeEffects:
    def __init__(
        self,
        *,
        found: list[dict[str, Any]] | None = None,
        race: list[dict[str, Any]] | None = None,
        publish_failure: str | None = None,
        branch_exists: bool | None = None,
        race_branch_exists: bool | None = None,
        validation_result: tuple[bool, str] = (True, "passed"),
    ) -> None:
        self.found = found or []
        self.race = race
        self.publish_failure = publish_failure
        self.validation_result = validation_result
        self.branch_exists = bool(self.found) if branch_exists is None else branch_exists
        self.race_branch_exists = bool(race) if race_branch_exists is None else race_branch_exists
        self.discoveries = 0
        self.codex_calls = 0
        self.publish_calls = 0
        self.validation_calls = 0

    def discover(self, *_: Any) -> Ownership:
        self.discoveries += 1
        if self.discoveries > 1 and self.race is not None:
            return Ownership(self.race_branch_exists, self.race)
        return Ownership(self.branch_exists, self.found)

    def codex(self, *_: Any) -> None:
        self.codex_calls += 1

    def validate_candidate(self, *_: Any) -> tuple[bool, str]:
        self.validation_calls += 1
        return self.validation_result

    def publish(self, *_: Any) -> str:
        self.publish_calls += 1
        if self.publish_failure:
            raise AdapterError("publication", self.publish_failure, "failed")
        return "https://github.com/Young-Consultations/portfolio-tasks/pull/7"


def execute(value: dict[str, Any], effects: FakeEffects | None = None) -> dict[str, Any]:
    return run_adapter(
        json.dumps(value),
        value["concurrency_group"],
        "router-app",
        {"router-app"},
        effects or FakeEffects(),
    ).result


def managed(value: dict[str, Any], *, digest: str | None = None) -> dict[str, Any]:
    return {
        "url": "https://github.com/Young-Consultations/portfolio-tasks/pull/7",
        "state": "OPEN",
        "draft": True,
        "digest": digest or canonical_digest(value),
    }


def test_exact_dispatch_and_receiver_boundary() -> None:
    trigger = WORKFLOW.split("on:", 1)[1].split("permissions:", 1)[0]
    inputs = trigger.split("inputs:", 1)[1]
    require(
        "workflow_dispatch:" in trigger and "workflow_call:" not in WORKFLOW,
        "target must expose only workflow_dispatch",
    )
    require(
        inputs.count("execution_input_json:") == 1 and inputs.count("concurrency_group:") == 1,
        "target inputs differ",
    )
    require(
        "codex-result-receiver.yml@ai-sdlc-v2.3.2" in WORKFLOW, "receiver is not immutably pinned"
    )
    require(
        "CODEX_TRUSTED_JOURNAL_AUTHORS" not in WORKFLOW,
        "target supplies control-plane trust policy",
    )
    require("secrets: inherit" not in WORKFLOW, "workflow broadly inherits secrets")
    receiver = WORKFLOW.split("  report:", 1)[1]
    require(
        receiver.count("CODEX_RESULT_TOKEN:") == 1, "receiver must receive only its delivery token"
    )


def test_security_and_publication_guards() -> None:
    require("persist-credentials: false" in WORKFLOW, "checkout persists credentials")
    require(
        "permissions:\n  contents: read" in WORKFLOW,
        "workflow permissions are broader than read-only",
    )
    require(
        "environment: portfolio-tasks-codex-production" in WORKFLOW,
        "target environment boundary is missing",
    )
    require(
        "gh pr merge" not in WORKFLOW and "git push origin main" not in WORKFLOW,
        "workflow can bypass draft review",
    )
    require("CODEX_TARGET_TRUSTED_CALLERS" in WORKFLOW, "dispatch caller allowlist is missing")


def test_canonical_policy_and_result() -> None:
    verify_effects = FakeEffects()
    result = execute(payload(execution_mode="verify"), verify_effects)
    require(result["execution_status"] == "verified", "verify mode did not complete canonically")
    require(
        result["branch_name"] is None and result["pull_request_url"] is None,
        "verify mode published state",
    )
    require(
        result["validation_result"] == "passed" and result["test_result"] == "passed",
        "verify evidence is incomplete",
    )
    require(verify_effects.validation_calls == 1, "verify mode skipped repository validation")
    failed = execute(
        payload(execution_mode="verify"),
        FakeEffects(validation_result=(False, "tests")),
    )
    require(
        failed["execution_status"] == "failed"
        and failed["failure_category"] == "tests"
        and failed["validation_result"] == "passed"
        and failed["test_result"] == "failed",
        "verify mode reported success after repository tests failed",
    )
    rejected = execute(payload(target_repository="Young-Consultations/slugger"))
    require(
        rejected["execution_status"] == "rejected"
        and rejected["failure_category"] == "repository-routing",
        "wrong target was admitted",
    )
    old_shape = payload(task_id="TASK-42")
    require(
        execute(old_shape)["failure_category"] == "contract-validation",
        "obsolete input field was admitted",
    )


def test_rejected_source_issue_is_not_exposed() -> None:
    value = payload(
        source_issue="bad\nexecution_result=forged\nsource_issue=Young-Consultations/x#1"
    )
    outcome = run_adapter(
        json.dumps(value),
        value["concurrency_group"],
        "router-app",
        {"router-app"},
        FakeEffects(),
    )
    require(
        outcome.result["failure_category"] == "contract-validation", "invalid issue was admitted"
    )
    require(outcome.source_issue is None, "rejected issue was exposed as a workflow output")


def test_idempotency_and_create_race() -> None:
    value = payload()
    reused = execute(value, FakeEffects(found=[managed(value)]))
    require(reused["execution_status"] == "duplicate-reused", "managed draft was not reused")
    conflict = execute(value, FakeEffects(found=[managed(value, digest="0" * 64)]))
    require(
        conflict["execution_status"] == "ambiguous-rejected",
        "ownership conflict did not fail closed",
    )
    orphan_effects = FakeEffects(branch_exists=True)
    orphan = execute(value, orphan_effects)
    require(orphan["execution_status"] == "ambiguous-rejected", "orphan branch did not fail closed")
    require(
        orphan_effects.codex_calls == 0 and orphan_effects.publish_calls == 0,
        "orphan branch reached executor or publication",
    )
    race = execute(
        value,
        FakeEffects(
            publish_failure="create-race",
            race=[managed(value), managed(value)],
        ),
    )
    require(
        race["execution_status"] == "ambiguous-rejected",
        "ambiguous create race did not fail closed",
    )


def test_exact_shared_blobs_and_evidence() -> None:
    pin = json.loads((ROOT / "config/mvp-conformance-pin.json").read_text(encoding="utf-8"))
    require(validate_pin(pin) == [], "conformance pin is invalid")
    for relative, expected in EXPECTED_COMPATIBILITY_BLOBS.items():
        require(
            git_blob_sha1((ROOT / relative).read_bytes()) == expected,
            f"shared file differs: {relative}",
        )
    report = json.loads(
        (ROOT / ".ai-sdlc/conformance/tc-mvp-ci-001.json").read_text(encoding="utf-8")
    )
    require(
        report["adapter_revision"] == pin["adapter_revision"], "report and pin revisions differ"
    )
    require(len(report["scenario_results"]) == 29, "report does not contain the complete oracle")
    require(
        all(row["result"] == "pass" for row in report["scenario_results"]),
        "report contains a failed scenario",
    )
    require(
        all(value == 0 for value in report["effect_traps"].values()),
        "report records a prohibited effect",
    )


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"passed {len(tests)} target-adapter checks")
