"""Fail-closed portfolio-side policies for the v2 execution lifecycle.

This module deliberately contains no GitHub or router client.  It constructs the payload owned by
the portfolio and returns decisions which adapters can persist before/after the external boundary.
The organization-owned schema remains the final validator at dispatch.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

CONTRACT = "ai-sdlc-contract/v2"
SUPPORTED_TARGETS = frozenset(
    {
        "Young-Consultations/.github",
        "Young-Consultations/consulting-playbook",
        "Young-Consultations/portfolio-tasks",
        "Young-Consultations/slugger",
    }
)
SUPPORTED_MODES = frozenset({"verify", "implement"})
TERMINAL_STATUSES = frozenset({"verified", "published", "duplicate-reused", "failed"})
_ISSUE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/#-]{7,160}$")


class LifecycleError(ValueError):
    """An untrusted or contradictory lifecycle operation was denied."""


class ProjectionDecision(str, Enum):
    APPLIED = "applied"
    NO_OP = "no-op"
    QUARANTINED = "quarantined"


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def task_id(source_issue: str, material: Mapping[str, object]) -> str:
    """Create one stable identity for one source issue material revision."""
    if _ISSUE.fullmatch(source_issue) is None:
        raise LifecycleError("invalid source issue binding")
    return f"{source_issue}@{canonical_digest(material)[:20]}"


def delivery_id(current_task_id: str) -> str:
    """Derive the logical delivery; retry/transport attempt data is intentionally excluded."""
    return f"delivery-{hashlib.sha256(current_task_id.encode()).hexdigest()[:32]}"


def correlation_id(current_task_id: str) -> str:
    return f"correlation-{hashlib.sha256(('correlation:' + current_task_id).encode()).hexdigest()[:32]}"


@dataclass(frozen=True)
class Approval:
    task_id: str
    actor: str
    human_authorized: bool
    revoked: bool = False


@dataclass(frozen=True)
class SourceRevision:
    source_issue: str
    material: Mapping[str, object]
    status: str
    target_repository: str
    execution_mode: str
    executor: str = "codex"
    dependencies: tuple[str, ...] = ()
    sensitivity: str = "not-sensitive"

    @property
    def task_id(self) -> str:
        return task_id(self.source_issue, self.material)


def canonical_task(revision: SourceRevision, approval: Approval) -> dict[str, object]:
    """Build the closed-contract candidate; admission still validates it with the pinned schema."""
    violations: list[str] = []
    if revision.status != "approved":
        violations.append("only approved is admissible")
    if revision.executor != "codex":
        violations.append("executor must be codex")
    if revision.target_repository not in SUPPORTED_TARGETS:
        violations.append("target is unknown")
    if revision.execution_mode not in SUPPORTED_MODES:
        violations.append("execution mode is unsupported")
    if revision.dependencies:
        violations.append("dependencies are unresolved")
    if revision.sensitivity != "not-sensitive":
        violations.append("sensitivity is not safely classified")
    if not approval.human_authorized or approval.revoked:
        violations.append("current human approval is absent or revoked")
    if approval.task_id != revision.task_id:
        violations.append("approval is stale for the material revision")
    if violations:
        raise LifecycleError("; ".join(violations))

    # These are the repository-owned fields of task-contract/v2. Rich approval evidence and
    # delivery/attempt transport fields must not be added to the closed task payload.
    payload = dict(revision.material)
    payload.update(
        {
            "contract_version": CONTRACT,
            "task_id": revision.task_id,
            "source_issue": revision.source_issue,
            "status": "approved",
            "executor": "codex",
            "target_repository": revision.target_repository,
            "dependencies": [],
        }
    )
    return payload


@dataclass(frozen=True)
class RoutingRecord:
    task_id: str
    delivery_id: str
    correlation_id: str
    payload_digest: str
    source_issue: str
    target_repository: str
    state: str = "pending-routing"
    attempt: int = 1

    @classmethod
    def reserve(cls, task: Mapping[str, object]) -> RoutingRecord:
        identity = task.get("task_id")
        if not isinstance(identity, str):
            raise LifecycleError("canonical task identity is missing")
        source = task.get("source_issue")
        target = task.get("target_repository")
        if not isinstance(source, str) or not isinstance(target, str):
            raise LifecycleError("canonical source or target binding is missing")
        return cls(
            identity,
            delivery_id(identity),
            correlation_id(identity),
            canonical_digest(task),
            source,
            target,
        )

    def retry(self, task: Mapping[str, object]) -> RoutingRecord:
        if canonical_digest(task) != self.payload_digest or task.get("task_id") != self.task_id:
            raise LifecycleError("delivery identity cannot be reused for different content")
        if self.state not in {"reconciliation", "rejected-retryable"}:
            raise LifecycleError("authoritative reconciliation evidence is required before retry")
        return replace(self, attempt=self.attempt + 1, state="pending-routing")

    def router_outcome(self, outcome: str) -> RoutingRecord:
        states = {"accepted": "queued", "rejected": "router-rejected", "unknown": "reconciliation"}
        if outcome not in states:
            raise LifecycleError("unknown router outcome")
        return replace(self, state=states[outcome])


@dataclass(frozen=True)
class ResultProjection:
    record: RoutingRecord
    result_digest: str | None = None
    terminal_status: str | None = None
    quarantined: bool = False

    def apply(
        self, result: Mapping[str, Any], *, receiver_accepted: bool, expected_source: str
    ) -> tuple[ResultProjection, ProjectionDecision]:
        digest = canonical_digest(result)
        if self.result_digest == digest:
            return self, ProjectionDecision.NO_OP
        if self.result_digest is not None:
            return replace(self, quarantined=True), ProjectionDecision.QUARANTINED
        bindings = (
            result.get("contract_version") == CONTRACT
            and result.get("task_id", self.record.task_id) == self.record.task_id
            and result.get("delivery_id") == self.record.delivery_id
            and result.get("correlation_id") == self.record.correlation_id
            and result.get("source_issue") == expected_source
            and expected_source == self.record.source_issue
            and result.get("target_repository") == self.record.target_repository
        )
        status = result.get("execution_status")
        if not receiver_accepted or not bindings or status not in TERMINAL_STATUSES:
            return replace(self, quarantined=True), ProjectionDecision.QUARANTINED
        if self.record.state not in {"queued", "executing", "result-transport", "reconciliation"}:
            return replace(self, quarantined=True), ProjectionDecision.QUARANTINED
        return (
            replace(self, result_digest=digest, terminal_status=str(status)),
            ProjectionDecision.APPLIED,
        )
