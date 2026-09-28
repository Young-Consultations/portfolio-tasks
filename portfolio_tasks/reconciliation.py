"""Source-owned reconciliation for admitted deliveries missing a terminal result."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_ISSUE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}#[1-9][0-9]*$"
)
_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_ADMISSION = re.compile(
    r"^[ \t]*<!-- ai-sdlc-admission:v2 (?P<payload>\{[^\r\n]*\}) -->[ \t]*\r?$",
    re.MULTILINE,
)
_SOURCE_RESULT = re.compile(
    r"^[ \t]*<!-- ai-sdlc-source-result:v2 (?P<payload>\{[^\r\n]*\}) -->[ \t]*\r?$",
    re.MULTILINE,
)
_RECONCILIATION = re.compile(
    r"^[ \t]*<!-- ai-sdlc-reconciliation:v1 (?P<payload>\{[^\r\n]*\}) -->[ \t]*\r?$",
    re.MULTILINE,
)
_ADMISSION_FIELDS = {
    "contract_version",
    "delivery_id",
    "correlation_id",
    "source_issue",
    "target_repository",
}
_ALLOWED_CONCLUSIONS = {"failure", "cancelled", "timed_out"}


class ReconciliationError(ValueError):
    """The supplied recovery evidence is absent, ambiguous, or contradictory."""


@dataclass(frozen=True)
class ReconciliationDecision:
    action: str
    marker: str
    comment: str
    target_repository: str


def _comment_bodies(comments: object) -> list[str]:
    if not isinstance(comments, list):
        raise ReconciliationError("issue comments are not a list")
    return [
        str(comment["body"])
        for comment in comments
        if isinstance(comment, Mapping) and isinstance(comment.get("body"), str)
    ]


def _marker_payloads(pattern: re.Pattern[str], comments: object) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for body in _comment_bodies(comments):
        for match in pattern.finditer(body):
            try:
                payload = json.loads(match.group("payload"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                values.append(payload)
    return values


def admission_binding(
    comments: object, *, source_issue: str, delivery_id: str
) -> dict[str, str]:
    """Return the unique durable admission binding for one logical delivery."""
    if _ISSUE.fullmatch(source_issue) is None or _IDENTITY.fullmatch(delivery_id) is None:
        raise ReconciliationError("source or delivery identity is invalid")
    matches: list[dict[str, str]] = []
    for payload in _marker_payloads(_ADMISSION, comments):
        if payload.get("delivery_id") != delivery_id or payload.get("source_issue") != source_issue:
            continue
        if not _ADMISSION_FIELDS <= set(payload):
            continue
        binding = {field: payload[field] for field in _ADMISSION_FIELDS}
        if not all(isinstance(value, str) and value for value in binding.values()):
            continue
        matches.append(binding)
    if len(matches) != 1:
        raise ReconciliationError("delivery does not have exactly one valid admission binding")
    return matches[0]


def _has_terminal_result(comments: object, delivery_id: str) -> bool:
    return any(
        payload.get("delivery_id") == delivery_id
        for payload in _marker_payloads(_SOURCE_RESULT, comments)
    )


def _labels(issue: Mapping[str, Any]) -> set[str]:
    labels = issue.get("labels")
    if not isinstance(labels, list):
        return set()
    return {
        str(item["name"])
        for item in labels
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }


def decide_missing_result_reconciliation(
    *,
    issue: Mapping[str, Any],
    comments: object,
    source_issue: str,
    delivery_id: str,
    target_run: Mapping[str, Any],
) -> ReconciliationDecision:
    """Validate failed workflow evidence without inventing a target execution result."""
    binding = admission_binding(comments, source_issue=source_issue, delivery_id=delivery_id)
    if binding["contract_version"] != "ai-sdlc-contract/v2":
        raise ReconciliationError("admission uses an unsupported contract")
    if _has_terminal_result(comments, delivery_id):
        raise ReconciliationError("delivery already has a receiver-validated terminal result")

    run_id = target_run.get("id")
    target = binding["target_repository"]
    repository = target_run.get("repository")
    run_repo = repository.get("full_name") if isinstance(repository, Mapping) else None
    if not isinstance(run_id, int) or run_id < 1 or run_repo != target:
        raise ReconciliationError("target workflow run is not bound to the admitted target")
    if target_run.get("event") != "workflow_dispatch" or target_run.get("status") != "completed":
        raise ReconciliationError("target workflow run is not a completed admitted dispatch")
    conclusion = target_run.get("conclusion")
    if conclusion not in _ALLOWED_CONCLUSIONS:
        raise ReconciliationError("target workflow run does not prove a failed transport attempt")
    run_url = target_run.get("html_url")
    expected_url = f"https://github.com/{target}/actions/runs/{run_id}"
    if run_url != expected_url:
        raise ReconciliationError("target workflow run URL does not match its repository and id")

    evidence = {
        "contract_version": binding["contract_version"],
        "correlation_id": binding["correlation_id"],
        "delivery_id": delivery_id,
        "recovery_status": "reconciliation-required",
        "source_issue": source_issue,
        "target_repository": target,
        "target_run_conclusion": conclusion,
        "target_run_id": run_id,
        "target_run_url": run_url,
    }
    marker = "<!-- ai-sdlc-reconciliation:v1 " + json.dumps(
        evidence, sort_keys=True, separators=(",", ":")
    ) + " -->"

    prior = _marker_payloads(_RECONCILIATION, comments)
    if any(item == evidence for item in prior):
        return ReconciliationDecision("no-op", marker, "", target)
    if any(
        item.get("delivery_id") == delivery_id and item.get("target_run_id") == run_id
        for item in prior
    ):
        raise ReconciliationError("conflicting reconciliation evidence exists for this target run")

    if issue.get("state") != "open" or "status:queued" not in _labels(issue):
        raise ReconciliationError("source is not an open queued delivery")

    comment = marker + "\n" + """### Execution reconciliation required

The admitted delivery has no receiver-validated terminal result. The cited target workflow completed unsuccessfully, so the queued projection is being cleared for human reconciliation. This record does **not** infer a target execution result.

Repair the failed prerequisite, review the evidence, and explicitly authorize any unchanged retry. Preserve the existing delivery and correlation identity; do not create a replacement delivery merely to escape the failed attempt.
"""
    return ReconciliationDecision("apply", marker, comment, target)
