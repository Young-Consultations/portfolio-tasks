"""Durable delivery and publication idempotency helpers.

The organization contract remains authoritative.  This module stores and validates
repository-local ownership markers around the canonical delivery identity.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Literal

SOURCE_REPO = "Young-Consultations/portfolio-tasks"
TARGET_REPO = "Young-Consultations/portfolio-tasks"
MARKER_BEGIN = "<!-- portfolio-task-dispatch-marker:v1"
MARKER_END = "portfolio-task-dispatch-marker:end -->"
PUBLICATION_BEGIN = "<!-- portfolio-task-publication-marker:v1"
PUBLICATION_END = "portfolio-task-publication-marker:end -->"
CONTRACT_VERSION = "ai-sdlc-contract/v2"
DELIVERY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/#-]{7,160}$")
SOURCE_ISSUE_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
STATE = Literal["dispatching", "queued", "executing", "completed", "failed", "blocked", "ambiguous"]
PREFLIGHT_OUTCOME = Literal[
    "new-delivery",
    "resume-incomplete-delivery",
    "reuse-completed-delivery",
    "ambiguous",
    "blocked",
]


@dataclass(frozen=True)
class DeliveryIdentity:
    contract_version: str
    source_issue: str
    task_id: str
    delivery_id: str
    target_repository: str
    requested_branch: str


def stable_task_id(*, source_issue: str, issue_title: str, issue_body: str) -> str:
    payload = json.dumps(
        {"source_issue": source_issue, "title": issue_title, "body": issue_body},
        sort_keys=True,
        separators=(",", ":"),
    )
    return "task-" + hashlib.sha256(payload.encode()).hexdigest()[:24]


def fallback_delivery_id(task_id: str) -> str:
    return f"portfolio-delivery/{task_id}"


def deterministic_branch(delivery_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", delivery_id).strip(".-_").lower()
    digest = hashlib.sha256(delivery_id.encode()).hexdigest()[:12]
    return f"codex/delivery-{slug[:40]}-{digest}"


def _extract(text: str, begin: str, end: str) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    start = 0
    while True:
        i = text.find(begin, start)
        if i == -1:
            return markers
        j = text.find(end, i)
        if j == -1:
            raise ValueError("unterminated managed marker")
        raw = text[i + len(begin) : j].strip()
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("managed marker is not valid JSON") from exc
        if not isinstance(value, dict):
            raise TypeError("managed marker must be a JSON object")
        markers.append(value)
        start = j + len(end)


def parse_dispatch_markers(text: str) -> list[dict[str, Any]]:
    return _extract(text, MARKER_BEGIN, MARKER_END)


def parse_publication_markers(text: str) -> list[dict[str, Any]]:
    return _extract(text, PUBLICATION_BEGIN, PUBLICATION_END)


def validate_delivery_identity(value: dict[str, Any]) -> DeliveryIdentity:
    identity = DeliveryIdentity(
        contract_version=str(value.get("contract_version") or ""),
        source_issue=str(value.get("source_issue") or ""),
        task_id=str(value.get("task_id") or value.get("correlation_id") or ""),
        delivery_id=str(value.get("delivery_id") or value.get("idempotency_key") or ""),
        target_repository=str(value.get("target_repository") or ""),
        requested_branch=str(value.get("requested_branch") or ""),
    )
    if identity.contract_version != CONTRACT_VERSION:
        raise ValueError("unsupported contract_version")
    if SOURCE_ISSUE_RE.fullmatch(identity.source_issue) is None:
        raise ValueError("source_issue must be owner/repository#number")
    if identity.target_repository != TARGET_REPO:
        raise ValueError("target_repository mismatch")
    if not identity.task_id:
        raise ValueError("task_id is required")
    if DELIVERY_RE.fullmatch(identity.delivery_id) is None:
        raise ValueError("delivery_id is required and must be stable")
    expected = deterministic_branch(identity.delivery_id)
    if identity.requested_branch != expected:
        raise ValueError(f"requested_branch must equal deterministic delivery branch {expected}")
    return identity


def dispatch_marker(identity: DeliveryIdentity, state: STATE, router_run_url: str = "") -> str:
    value = {
        "contract_version": identity.contract_version,
        "source_issue": identity.source_issue,
        "task_id": identity.task_id,
        "delivery_id": identity.delivery_id,
        "target_repository": identity.target_repository,
        "requested_branch": identity.requested_branch,
        "dispatch_state": state,
        "router_workflow_run_url": router_run_url,
    }
    return f"{MARKER_BEGIN}\n{json.dumps(value, sort_keys=True)}\n{MARKER_END}"


def publication_marker(identity: DeliveryIdentity, state: str) -> str:
    value = {
        "contract_version": identity.contract_version,
        "source_issue": identity.source_issue,
        "delivery_id": identity.delivery_id,
        "target_repository": identity.target_repository,
        "requested_branch": identity.requested_branch,
        "publication_state": state,
    }
    return f"{PUBLICATION_BEGIN}\n{json.dumps(value, sort_keys=True)}\n{PUBLICATION_END}"


def marker_matches(marker: dict[str, Any], identity: DeliveryIdentity) -> bool:
    return all(
        str(marker.get(key) or "") == expected
        for key, expected in {
            "contract_version": identity.contract_version,
            "source_issue": identity.source_issue,
            "delivery_id": identity.delivery_id,
            "target_repository": identity.target_repository,
        }.items()
    )


def terminal_source_update(identity: DeliveryIdentity, state: STATE, pr_url: str = "") -> str:
    safe = {
        "contract_version": identity.contract_version,
        "source_issue": identity.source_issue,
        "task_id": identity.task_id,
        "delivery_id": identity.delivery_id,
        "target_repository": identity.target_repository,
        "requested_branch": identity.requested_branch,
        "dispatch_state": state,
        "pull_request_url": pr_url,
    }
    return f"{MARKER_BEGIN}\n{json.dumps(safe, sort_keys=True)}\n{MARKER_END}"
