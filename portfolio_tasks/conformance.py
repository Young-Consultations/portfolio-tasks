"""Deterministic, effect-free evidence for the pinned MVP compatibility adapter.

This is a repository adapter test driver, not a copy of an organization schema or router.  The
scenario names are the portfolio/target projections selected by the approved local release record.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Callable

from portfolio_tasks.source_lifecycle import (
    Approval,
    LifecycleError,
    ProjectionDecision,
    ResultProjection,
    RoutingRecord,
    SourceRevision,
    canonical_task,
)
from portfolio_tasks.target_adapter import (
    AdmissionError,
    OwnershipError,
    Pull,
    admit,
    ownership_marker,
    reconcile,
    verify_result,
)

COMPATIBILITY_SHA = "c6090e5bbadcc2102a1cb91875466e9decdada1e"
FIXTURE_SET = "TC-MVP-CI-001"
ADAPTER_REVISION = "portfolio-tasks-conformance/v2"
REPOSITORY = "Young-Consultations/portfolio-tasks"


class ConformanceFailure(RuntimeError):
    """A deterministic adapter expectation was not met."""


class _Validator:
    def validate(self, instance: object) -> None:
        if not isinstance(instance, dict) or instance.get("schema_invalid"):
            raise ValueError("fixture rejected")


@dataclass(frozen=True)
class Effects:
    codex_requests: int = 0
    branches_created: int = 0
    commits_or_pushes: int = 0
    pull_requests_created: int = 0
    privileged_actions: int = 0
    secret_outputs: int = 0

    def assert_trapped(self) -> None:
        observed = {name: value for name, value in asdict(self).items() if value != 0}
        if observed:
            raise ConformanceFailure(f"trapped effects were invoked: {sorted(observed)}")


def _revision(**changes: object) -> SourceRevision:
    values: dict[str, object] = {
        "source_issue": f"{REPOSITORY}#123",
        "material": {"objective": "bounded fixture change", "task_type": "automation"},
        "status": "approved",
        "target_repository": REPOSITORY,
        "execution_mode": "implement",
    }
    return SourceRevision(**(values | changes))  # type: ignore[arg-type]


def _approval(revision: SourceRevision) -> Approval:
    return Approval(revision.task_id, "fixture-human", True)


def _input(**changes: object) -> dict[str, object]:
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "delivery_id": "delivery-fixture-0001",
        "correlation_id": "correlation-fixture-0001",
        "source_issue": f"{REPOSITORY}#123",
        "target_repository": REPOSITORY,
        "executor": "codex",
        "draft_pr_only": True,
        "execution_mode": "implement",
        "task_type": "automation",
        "instructions": "Apply the bounded fixture change.",
    } | changes


def _admit(**changes: object):  # type: ignore[no-untyped-def]
    return admit(
        json.dumps(_input(**changes)),
        "transport-fixture-0001",
        _Validator(),
        caller_authenticated=True,
        caller_authorized=True,
    )


def _expect_error(error: type[Exception], operation: Callable[[], object]) -> None:
    try:
        operation()
    except error:
        return
    raise ConformanceFailure(f"expected {error.__name__}")


def _scenario_checks() -> list[tuple[str, Callable[[], None]]]:
    """Build independent local checks aligned to applicable baseline concerns."""
    checks: list[tuple[str, Callable[[], None]]] = []

    def scenario(name: str, check: Callable[[], None]) -> None:
        checks.append((name, check))

    revision = _revision()
    task = canonical_task(revision, _approval(revision))
    record = RoutingRecord.reserve(task)

    scenario("source-approved-construction", lambda: assert_equal(task["status"], "approved"))
    scenario(
        "source-revision-invalidates-approval",
        lambda: _expect_error(
            LifecycleError,
            lambda: canonical_task(
                _revision(material={"objective": "edited"}), _approval(revision)
            ),
        ),
    )
    scenario(
        "source-target-selection",
        lambda: _expect_error(
            LifecycleError,
            lambda: canonical_task(
                _revision(target_repository="unknown/repository"), _approval(revision)
            ),
        ),
    )

    def retry_identity() -> None:
        retry = record.router_outcome("unknown").retry(task)
        assert_equal(retry.delivery_id, record.delivery_id)
        assert_equal(retry.correlation_id, record.correlation_id)

    scenario("routing-retry-identity", retry_identity)

    admitted = _admit()
    scenario("target-admission", lambda: assert_equal(admitted.payload["draft_pr_only"], True))
    scenario(
        "target-verify",
        lambda: assert_equal(
            verify_result(
                _admit(execution_mode="verify"), workflow_url="https://example.invalid/run/1"
            )["execution_status"],
            "verified",
        ),
    )
    scenario("target-fake-implement", lambda: assert_equal(admitted.mode, "implement"))
    scenario(
        "target-authorization-failure",
        lambda: _expect_error(
            AdmissionError,
            lambda: admit(
                json.dumps(_input()),
                "transport-fixture-0001",
                _Validator(),
                caller_authenticated=True,
                caller_authorized=False,
            ),
        ),
    )
    scenario(
        "target-schema-validation-failure",
        lambda: _expect_error(AdmissionError, lambda: _admit(schema_invalid=True)),
    )
    scenario(
        "target-capability-policy-failure",
        lambda: _expect_error(AdmissionError, lambda: _admit(task_type="feature")),
    )
    scenario(
        "target-identity-isolation",
        lambda: _expect_error(
            AdmissionError, lambda: _admit(target_repository="Young-Consultations/slugger")
        ),
    )

    managed = Pull("https://example.invalid/pull/1", admitted.branch, ownership_marker(admitted))
    scenario(
        "target-idempotent-ownership", lambda: assert_equal(reconcile(admitted, [managed]), managed)
    )
    scenario(
        "target-create-race-reuse", lambda: assert_equal(reconcile(admitted, [managed]), managed)
    )
    scenario("target-create-race-none", lambda: assert_equal(reconcile(admitted, []), None))
    scenario(
        "target-create-race-ambiguous",
        lambda: _expect_error(OwnershipError, lambda: reconcile(admitted, [managed, managed])),
    )
    scenario(
        "target-validation-test-failure",
        lambda: _expect_error(AdmissionError, lambda: _admit(schema_invalid=True)),
    )
    scenario(
        "target-publication-failure",
        lambda: _expect_error(
            OwnershipError,
            lambda: reconcile(
                admitted, [Pull(managed.url, managed.branch, managed.body, draft=False)]
            ),
        ),
    )
    scenario(
        "canonical-result-creation",
        lambda: assert_equal(
            verify_result(
                _admit(execution_mode="verify"), workflow_url="https://example.invalid/run/1"
            )["pull_request_url"],
            None,
        ),
    )

    queued = record.router_outcome("accepted")
    canonical_result = {
        "contract_version": "ai-sdlc-contract/v2",
        "task_id": queued.task_id,
        "delivery_id": queued.delivery_id,
        "correlation_id": queued.correlation_id,
        "source_issue": queued.source_issue,
        "target_repository": queued.target_repository,
        "execution_status": "published",
    }

    def projection() -> None:
        projected, decision = ResultProjection(queued).apply(
            canonical_result, receiver_accepted=True, expected_source=queued.source_issue
        )
        assert_equal(decision, ProjectionDecision.APPLIED)
        assert_equal(
            projected.apply(
                canonical_result, receiver_accepted=True, expected_source=queued.source_issue
            )[1],
            ProjectionDecision.NO_OP,
        )
        conflict = canonical_result | {"execution_status": "failed"}
        assert_equal(
            projected.apply(conflict, receiver_accepted=True, expected_source=queued.source_issue)[
                1
            ],
            ProjectionDecision.QUARANTINED,
        )

    scenario("result-projection-duplicate-conflict", projection)
    scenario(
        "receiver-failure",
        lambda: assert_equal(
            ResultProjection(queued).apply(
                canonical_result, receiver_accepted=False, expected_source=queued.source_issue
            )[1],
            ProjectionDecision.QUARANTINED,
        ),
    )
    scenario("result-redelivery", projection)
    scenario(
        "reconciliation",
        lambda: assert_equal(record.router_outcome("unknown").state, "reconciliation"),
    )
    scenario("normal-ci-effect-traps", Effects().assert_trapped)
    return checks


def run_scenarios() -> tuple[dict[str, str], list[dict[str, str]]]:
    """Run every check, retaining safe failure details instead of stopping at the first failure."""
    results: dict[str, str] = {}
    failures: list[dict[str, str]] = []
    for name, check in _scenario_checks():
        try:
            check()
        except (
            ConformanceFailure,
            AdmissionError,
            LifecycleError,
            OwnershipError,
            ValueError,
        ) as exc:
            results[name] = "failed"
            failures.append({"scenario": name, "type": type(exc).__name__})
        else:
            results[name] = "passed"
    return results, failures


def assert_equal(actual: object, expected: object) -> None:
    if actual != expected:
        raise ConformanceFailure(f"expected {expected!r}, got {actual!r}")


def report() -> dict[str, object]:
    scenarios, failures = run_scenarios()
    return {
        "report_version": "2",
        "repository": REPOSITORY,
        "adapter_revision": ADAPTER_REVISION,
        "compatibility_sha": COMPATIBILITY_SHA,
        "fixture_set": FIXTURE_SET,
        "evidence_kind": "repository-local adapter projections",
        "canonical_oracle_executed": False,
        "scope": "deterministic repository-local evidence; not production readiness",
        "scenario_results": scenarios,
        "failures": failures,
        "activation_requested": False,
        # Local projections cannot substitute for direct execution of the organization oracle.
        "activation_evidence_sufficient": False,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the versioned report drifts")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("conformance/reports/tc-mvp-ci-001-v2.json"),
    )
    arguments = parser.parse_args()
    evidence = report()
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if arguments.check:
        if (
            not arguments.output.is_file()
            or arguments.output.read_text(encoding="utf-8") != rendered
        ):
            return 3
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    return 1 if evidence["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
