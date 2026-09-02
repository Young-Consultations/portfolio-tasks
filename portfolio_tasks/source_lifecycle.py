"""Fail-closed portfolio-side policies for the v2 execution lifecycle.

This module contains no GitHub or router client. It constructs the exact task
payload owned by the portfolio and returns decisions that workflow adapters can
persist before and after the organization control-plane boundary.
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
SUPPORTED_MODES = frozenset({"verify", "implement"})
TASK_TYPES = frozenset(
    {
        "automation",
        "backlog-governance",
        "ci-cd",
        "documentation",
        "repository-maintenance",
        "feature",
        "bug-fix",
        "testing",
        "security",
    }
)
TASK_TYPE_LABELS = {
    "automation": "automation",
    "backlog governance": "backlog-governance",
    "bug fix": "bug-fix",
    "ci/cd": "ci-cd",
    "documentation": "documentation",
    "feature": "feature",
    "repository maintenance": "repository-maintenance",
    "security": "security",
    "testing": "testing",
}
TASK_MATERIAL_FIELDS = frozenset(
    {
        "project",
        "priority",
        "task_type",
        "parallel_safe",
        "risk",
        "scope",
        "instructions",
        "created_by",
    }
)
TERMINAL_STATUSES = frozenset(
    {
        "rejected",
        "verified",
        "no-changes",
        "draft-pr-created",
        "blocked",
        "failed",
        "duplicate-reused",
        "ambiguous-rejected",
    }
)
_ISSUE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}#[1-9][0-9]*$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}$")
_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_ADMISSION_MARKER = re.compile(
    r"^<!-- ai-sdlc-admission:v2 (?P<payload>\\{[^\\r\\n]*\\}) -->$", re.MULTILINE
)
ADMISSION_BINDING_FIELDS = frozenset(
    {
        "contract_version",
        "delivery_id",
        "correlation_id",
        "source_issue",
        "target_repository",
    }
)


class LifecycleError(ValueError):
    """An untrusted or contradictory lifecycle operation was denied."""


class ProjectionDecision(str, Enum):
    APPLIED = "applied"
    NO_OP = "no-op"
    QUARANTINED = "quarantined"


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def normalize_task_type(label: str) -> str:
    """Map the issue-form display vocabulary to the exact contract vocabulary."""
    normalized = TASK_TYPE_LABELS.get(" ".join(label.split()).casefold())
    if normalized is None:
        raise LifecycleError("task type is unsupported")
    return normalized


def matching_admission_count(comments: object, expected_binding: Mapping[str, object]) -> int:
    """Count v2 markers whose required binding matches the receiver result.

    Admission records may carry control-plane release and activation evidence in
    addition to the stable source binding. Those additive fields are preserved
    and ignored here; every required binding field must still match exactly.
    """
    if set(expected_binding) != ADMISSION_BINDING_FIELDS:
        raise LifecycleError("expected admission binding does not match the closed contract")
    if not isinstance(comments, list):
        raise LifecycleError("issue comments are not a list")

    count = 0
    for comment in comments:
        if not isinstance(comment, Mapping) or not isinstance(comment.get("body"), str):
            continue
        for marker in _ADMISSION_MARKER.finditer(comment["body"]):
            try:
                payload = json.loads(marker.group("payload"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and all(
                payload.get(field) == expected_binding[field] for field in ADMISSION_BINDING_FIELDS
            ):
                count += 1
    return count


def task_id(source_issue: str, authority: Mapping[str, object]) -> str:
    """Create a schema-safe identity for one complete authoritative source revision."""
    if _ISSUE.fullmatch(source_issue) is None:
        raise LifecycleError("invalid source issue binding")
    return f"task-{canonical_digest({'source_issue': source_issue, 'authority': authority})[:32]}"


def delivery_id(current_task_id: str) -> str:
    """Derive the logical delivery; retry and transport attempts are excluded."""
    if _IDENTITY.fullmatch(current_task_id) is None:
        raise LifecycleError("invalid canonical task identity")
    return f"delivery-{hashlib.sha256(current_task_id.encode()).hexdigest()[:32]}"


def correlation_id(current_task_id: str) -> str:
    if _IDENTITY.fullmatch(current_task_id) is None:
        raise LifecycleError("invalid canonical task identity")
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
    def authority(self) -> dict[str, object]:
        return {
            "material": dict(self.material),
            "target_repository": self.target_repository,
            "execution_mode": self.execution_mode,
            "executor": self.executor,
            "dependencies": list(self.dependencies),
            "sensitivity": self.sensitivity,
        }

    @property
    def task_id(self) -> str:
        return task_id(self.source_issue, self.authority)


def _validate_material(material: Mapping[str, object]) -> list[str]:
    violations: list[str] = []
    if set(material) != TASK_MATERIAL_FIELDS:
        violations.append("task material does not match the closed contract")
        return violations
    if not isinstance(material["project"], str) or not str(material["project"]).strip():
        violations.append("project is missing")
    if material["priority"] not in {"p0", "p1", "p2", "p3"}:
        violations.append("priority is unsupported")
    if material["task_type"] not in TASK_TYPES:
        violations.append("task type is unsupported")
    if type(material["parallel_safe"]) is not bool:
        violations.append("parallel-safe must be boolean")
    if material["risk"] not in {"low", "medium", "high"}:
        violations.append("risk is unsupported")
    if material["scope"] not in {"small", "medium", "large"}:
        violations.append("scope is unsupported")
    if not isinstance(material["instructions"], str) or not str(material["instructions"]).strip():
        violations.append("instructions are missing")
    if not isinstance(material["created_by"], str) or not str(material["created_by"]).strip():
        violations.append("creator is missing")
    return violations


def canonical_task(revision: SourceRevision, approval: Approval) -> dict[str, object]:
    """Build the exact task-contract/v2 object after validating current authority."""
    violations = _validate_material(revision.material)
    if revision.status != "approved":
        violations.append("only approved is admissible")
    if revision.executor != "codex":
        violations.append("executor must be codex")
    if _REPOSITORY.fullmatch(revision.target_repository) is None:
        violations.append("target repository syntax is invalid")
    if revision.execution_mode not in SUPPORTED_MODES:
        violations.append("execution mode is unsupported")
    if revision.dependencies:
        violations.append("dependencies are unresolved")
    if revision.sensitivity != "not-sensitive":
        violations.append("sensitivity is not safely classified")
    if not approval.actor.strip() or not approval.human_authorized or approval.revoked:
        violations.append("current human approval is absent or revoked")
    if approval.task_id != revision.task_id:
        violations.append("approval is stale for the authoritative revision")
    if violations:
        raise LifecycleError("; ".join(violations))

    payload = {
        "contract_version": CONTRACT,
        "task_id": revision.task_id,
        "source_issue": revision.source_issue,
        "status": "approved",
        "executor": "codex",
        "project": revision.material["project"],
        "priority": revision.material["priority"],
        "task_type": revision.material["task_type"],
        "target_repository": revision.target_repository,
        "parallel_safe": revision.material["parallel_safe"],
        "dependencies": [],
        "risk": revision.material["risk"],
        "scope": revision.material["scope"],
        "instructions": revision.material["instructions"],
        "created_by": revision.material["created_by"],
    }
    if set(payload) != {
        "contract_version",
        "task_id",
        "source_issue",
        "status",
        "executor",
        "project",
        "priority",
        "task_type",
        "target_repository",
        "parallel_safe",
        "dependencies",
        "risk",
        "scope",
        "instructions",
        "created_by",
    }:
        raise LifecycleError("canonical task construction is incomplete")
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
        source = task.get("source_issue")
        target = task.get("target_repository")
        if not isinstance(identity, str) or _IDENTITY.fullmatch(identity) is None:
            raise LifecycleError("canonical task identity is missing or invalid")
        if not isinstance(source, str) or _ISSUE.fullmatch(source) is None:
            raise LifecycleError("canonical source binding is missing or invalid")
        if not isinstance(target, str) or _REPOSITORY.fullmatch(target) is None:
            raise LifecycleError("canonical target binding is missing or invalid")
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
            and result.get("delivery_id") == self.record.delivery_id
            and result.get("correlation_id") == self.record.correlation_id
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
