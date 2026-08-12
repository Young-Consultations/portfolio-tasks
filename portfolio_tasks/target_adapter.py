"""Policy and idempotency core for the canonical v2 target adapter.

The organization owns the JSON schemas and transport.  Callers therefore provide the
pinned schemas to this module; no local schema is treated as authoritative.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

TARGET = "Young-Consultations/portfolio-tasks"
CONTRACT = "ai-sdlc-contract/v2"
ALLOWED_TASK_TYPES = frozenset(
    {"automation", "backlog-governance", "ci-cd", "documentation", "repository-maintenance"}
)
DELIVERY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/#-]{7,160}$")
CONCURRENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/#-]{7,200}$")
MARKER = "ai-sdlc-delivery-id"


class AdmissionError(ValueError):
    """An untrusted delivery failed schema, authorization, or local policy."""


class OwnershipError(RuntimeError):
    """Publication ownership is absent, contradictory, or ambiguous."""


class SchemaValidator(Protocol):
    def validate(self, instance: object) -> None: ...


def canonical_digest(value: object) -> str:
    """Digest the immutable canonical JSON representation, not transport metadata."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def branch_for(delivery_id: str) -> str:
    """Derive a bounded deterministic branch solely from delivery identity."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", delivery_id).strip(".-_").lower()
    return f"codex/delivery-{slug[:40]}-{hashlib.sha256(delivery_id.encode()).hexdigest()[:12]}"


@dataclass(frozen=True)
class Admitted:
    payload: dict[str, Any]
    digest: str
    delivery_id: str
    correlation_id: str
    mode: str
    source_issue: str
    branch: str


def admit(
    raw: str,
    concurrency_group: str,
    validator: SchemaValidator,
    *,
    caller_authenticated: bool,
    caller_authorized: bool,
) -> Admitted:
    """Validate the shared schema and every target-local gate before effects."""
    if not caller_authenticated or not caller_authorized:
        raise AdmissionError("organization router caller is not authenticated and authorized")
    if CONCURRENCY.fullmatch(concurrency_group) is None:
        raise AdmissionError("invalid transport concurrency group")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdmissionError("execution input is malformed JSON") from exc
    try:
        validator.validate(value)
    except Exception as exc:
        raise AdmissionError("execution input does not match the pinned schema") from exc
    if not isinstance(value, dict):
        raise AdmissionError("execution input must be an object")
    if value.get("contract_version") != CONTRACT:
        raise AdmissionError("unsupported contract version")
    if value.get("target_repository") != TARGET:
        raise AdmissionError("delivery targets another repository")
    if value.get("executor") != "codex" or value.get("draft_pr_only") is not True:
        raise AdmissionError("executor or draft-only policy conflict")
    mode = value.get("execution_mode")
    if mode not in {"verify", "implement"}:
        raise AdmissionError("unsupported execution mode")
    task_type = value.get("task_type")
    if task_type not in ALLOWED_TASK_TYPES:
        raise AdmissionError("task type is not enabled for this target")
    delivery_id = value.get("delivery_id")
    if not isinstance(delivery_id, str) or DELIVERY.fullmatch(delivery_id) is None:
        raise AdmissionError("invalid delivery identity")
    correlation_id = value.get("correlation_id")
    source_issue = value.get("source_issue")
    if not isinstance(correlation_id, str) or not correlation_id:
        raise AdmissionError("missing correlation identity")
    if not isinstance(source_issue, str) or not source_issue:
        raise AdmissionError("missing source issue")
    return Admitted(
        value,
        canonical_digest(value),
        delivery_id,
        correlation_id,
        mode,
        source_issue,
        branch_for(delivery_id),
    )


@dataclass(frozen=True)
class Pull:
    url: str
    branch: str
    body: str
    open: bool = True
    draft: bool = True


def ownership_marker(delivery: Admitted) -> str:
    return f"<!-- {MARKER}: {delivery.delivery_id}; payload-sha256: {delivery.digest} -->"


def reconcile(delivery: Admitted, pulls: list[Pull]) -> Pull | None:
    """Return the one reusable managed draft, or fail closed on any conflict."""
    branch = delivery.branch
    delivery_token = f"{MARKER}: {delivery.delivery_id};"
    digest_token = f"payload-sha256: {delivery.digest}"
    candidates = [p for p in pulls if p.branch == branch or delivery_token in p.body]
    if not candidates:
        return None
    if len(candidates) != 1:
        raise OwnershipError("ambiguous publication ownership")
    pull = candidates[0]
    if (
        pull.branch != branch
        or delivery_token not in pull.body
        or digest_token not in pull.body
        or not pull.open
        or not pull.draft
    ):
        raise OwnershipError("conflicting publication ownership or payload digest")
    return pull


def result_base(delivery: Admitted, *, workflow_url: str) -> dict[str, Any]:
    """Build identity fields that every canonical terminal result must preserve."""
    return {
        "contract_version": CONTRACT,
        "delivery_id": delivery.delivery_id,
        "correlation_id": delivery.correlation_id,
        "target_repository": TARGET,
        "workflow_url": workflow_url,
    }


def verify_result(delivery: Admitted, *, workflow_url: str) -> dict[str, Any]:
    """Construct the side-effect-free verified result fields."""
    return result_base(delivery, workflow_url=workflow_url) | {
        "execution_status": "verified",
        "branch_name": None,
        "pull_request_url": None,
        "validation_result": "passed",
        "test_result": "passed",
        "failure_category": None,
        "failure_message": None,
    }


def execution_result_from_environment() -> dict[str, Any]:
    """Build the terminal contract result from trusted job outcomes and admitted input."""
    raw = os.environ["EXECUTION_INPUT_JSON"]
    payload = json.loads(raw)
    delivery = Admitted(
        payload=payload,
        digest=canonical_digest(payload),
        delivery_id=str(payload["delivery_id"]),
        correlation_id=str(payload["correlation_id"]),
        mode=str(payload["execution_mode"]),
        source_issue=str(payload["source_issue"]),
        branch=branch_for(str(payload["delivery_id"])),
    )
    workflow_url = os.environ["WORKFLOW_URL"]
    if delivery.mode == "verify" and os.environ.get("VERIFY_RESULT") == "success":
        return verify_result(delivery, workflow_url=workflow_url)

    implement = os.environ.get("IMPLEMENT_RESULT")
    publication = os.environ.get("PUBLISH_RESULT")
    if delivery.mode == "implement" and implement == publication == "success":
        return result_base(delivery, workflow_url=workflow_url) | {
            "execution_status": os.environ["PUBLICATION_STATUS"],
            "branch_name": os.environ["BRANCH_NAME"],
            "pull_request_url": os.environ["PULL_REQUEST_URL"],
            "validation_result": "passed",
            "test_result": "passed",
            "failure_category": None,
            "failure_message": None,
        }

    failed_stage = (
        "verification"
        if delivery.mode == "verify"
        else ("publication" if implement == "success" else "implementation")
    )
    return result_base(delivery, workflow_url=workflow_url) | {
        "execution_status": "failed",
        "branch_name": None,
        "pull_request_url": None,
        "validation_result": "failed",
        "test_result": "failed",
        "failure_category": f"{failed_stage}-failed",
        "failure_message": f"Trusted {failed_stage} job did not complete successfully.",
    }


def main() -> int:
    """Validate admission using schemas fetched from the pinned compatibility SHA."""
    from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

    if len(sys.argv) == 3 and sys.argv[1] == "result":
        schema = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        result = execution_result_from_environment()
        try:
            validator.validate(result)
        except Exception as exc:
            print(f"canonical execution result is invalid: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if len(sys.argv) != 5 or sys.argv[1] != "admit":
        print(
            "usage: target_adapter admit INPUT SCHEMA CONCURRENCY_GROUP | result SCHEMA",
            file=sys.stderr,
        )
        return 64
    input_path, schema_path, group = sys.argv[2:]
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    try:
        admitted = admit(
            Path(input_path).read_text(encoding="utf-8"),
            group,
            validator,
            caller_authenticated=True,
            caller_authorized=True,
        )
    except AdmissionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        json.dumps(
            admitted.__dict__ | {"ownership_marker": ownership_marker(admitted)},
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
