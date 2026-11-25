"""Source-only terminal evidence and lifecycle reconciliation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker

from portfolio_tasks.issue_parser import IssueFormParser, TargetRepositoryParser
from portfolio_tasks.source_lifecycle import (
    CONTRACT,
    TERMINAL_STATUSES,
    LifecycleError,
    SourceRevision,
    normalize_task_type,
)

REPOSITORY = "Young-Consultations/portfolio-tasks"
CONTROL = "Young-Consultations/.github"
TRUST = {
    "ai-sdlc-v3.0.3": "f3229bfa4a06da963cae7c390c6075b4f6c12f7b",
    "ai-sdlc-v4.0.0": "6e51f058bf828b0732cb1b773ba1835acaa1d5cd",
}
SOURCE_AUTHOR = "github-actions[bot]"
KINDS = {
    "admission": "ai-sdlc-admission:v2",
    "receipt": "ai-sdlc-result-receipt:v2",
    "forwarded": "ai-sdlc-result-forwarded:v2",
    "source": "ai-sdlc-source-result:v2",
}
SCHEMA = Path(__file__).resolve().parents[1] / "contracts/execution-result.schema.json"
ACTIVE = {"status:queued", "status:approved"}
FIELDS = ("contract_version", "delivery_id", "correlation_id", "target_repository", "source_issue")


def require(ok: object, message: str) -> None:
    if not ok:
        raise LifecycleError(message)


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def decode(raw: str) -> Any:
    def nonfinite(_: str) -> Any:
        raise LifecycleError("nonfinite JSON")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def revision_from(issue: Mapping[str, Any], source: str) -> SourceRevision:
    body = issue["body"]
    require(isinstance(body, str), "source body unavailable")
    form = IssueFormParser(body)
    return SourceRevision(
        source_issue=source,
        material={
            "project": form.value("Project").strip(),
            "priority": form.value("Priority").strip().casefold(),
            "task_type": normalize_task_type(form.value("Task type")),
            "parallel_safe": form.value("Parallel-safe").strip().casefold() == "yes",
            "risk": form.value("Risk").strip().casefold(),
            "scope": form.value("Estimated scope").strip().casefold(),
            "instructions": body,
            "created_by": str(issue["user"]["login"]),
        },
        status="approved",
        target_repository=TargetRepositoryParser.parse(form.value("Target repository")) or "",
        execution_mode=form.value("Execution mode"),
        executor=form.value("Executor"),
        dependencies=()
        if form.value("Dependency issue references").strip().casefold() == "none"
        else ("unresolved",),
        sensitivity=form.value("Sensitivity declaration"),
    )


def markers(comments: Any, kind: str) -> list[tuple[str, dict[str, Any], str]]:
    require(isinstance(comments, list), "comments unavailable")
    prefix = "<!-- " + KINDS[kind] + " "
    rows = []
    for comment in comments:
        body = comment["body"]
        require(isinstance(body, str), "comment unavailable")
        if KINDS[kind] not in body:
            continue
        lines = [line for line in body.splitlines() if KINDS[kind] in line]
        require(len(lines) == 1, "ambiguous marker")
        line = lines[0]
        require(line.startswith(prefix) and line.endswith(" -->"), "malformed marker")
        value = decode(line[len(prefix) : -4])
        require(isinstance(value, dict), "invalid marker")
        rows.append((comment["user"]["login"], value, body))
    return rows


def trusted(trust: Mapping[str, Any], field: str, author: str) -> bool:
    values = trust.get(field)
    return (
        trust.get("policy_format_version") == 2
        and isinstance(values, list)
        and bool(values)
        and all(isinstance(v, str) and v for v in values)
        and author in values
    )


def validate(result: Any, binding: Mapping[str, Any]) -> dict[str, Any]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    require(
        isinstance(result, dict)
        and Draft202012Validator(schema, format_checker=FormatChecker()).is_valid(result),
        "invalid result schema",
    )
    require(
        result["execution_status"] in TERMINAL_STATUSES
        and all(result[k] == binding[k] for k in FIELDS if k != "source_issue"),
        "terminal binding mismatch",
    )
    return cast(dict[str, Any], result)


def receipt_digest(
    comments: Any, binding: Mapping[str, Any], trust: Mapping[str, Any], historical: bool
) -> str | None:
    receipts = markers(comments, "receipt")
    forwards = markers(comments, "forwarded")
    if not receipts and not forwards:
        return None
    require(len(receipts) == 1 and len(forwards) <= 1, "ambiguous receipt")
    author, receipt, _ = receipts[0]
    require(
        trusted(trust, "trusted_result_authors", author)
        and all(receipt.get(k) == binding[k] for k in FIELDS)
        and isinstance(receipt.get("result_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", receipt["result_sha256"])
        and isinstance(receipt.get("effect_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", receipt["effect_sha256"]),
        "untrusted or mismatched receipt",
    )
    # Forwarded is written after dispatch; only historical plans require it.
    require(not historical or len(forwards) == 1, "forwarding evidence missing")
    if forwards:
        author, forward, _ = forwards[0]
        require(
            trusted(trust, "trusted_result_authors", author)
            and all(
                forward.get(k) == receipt[k]
                for k in (*FIELDS, "result_sha256", "effect_sha256", "effect_class")
            ),
            "conflicting forwarding evidence",
        )
    return str(receipt["result_sha256"])


def projection_body(result: dict[str, Any]) -> str:
    marker = {"delivery_id": result["delivery_id"], "result_sha256": digest(result)}
    return (
        "<!-- ai-sdlc-source-result:v2 "
        + json.dumps(marker, sort_keys=True, separators=(",", ":"))
        + " -->\n### Receiver-validated execution result\n\n"
        + "\x60\x60\x60json\n"
        + json.dumps(result, indent=2, sort_keys=True)
        + "\n\x60\x60\x60\n"
    )


def labels(issue: Mapping[str, Any]) -> set[str]:
    require(isinstance(issue.get("labels"), list), "labels unavailable")
    return {item["name"] for item in issue["labels"]}


def decide(
    issue: Mapping[str, Any],
    comments: Any,
    trust: Mapping[str, Any],
    source: str,
    identity: str,
    mode: str,
    incoming: Any = None,
) -> dict[str, Any]:
    require(mode in {"result", "queued", "plan"}, "unknown mode")
    require(source == f"{REPOSITORY}#{issue['number']}", "source mismatch")
    require(re.fullmatch(r"task-[0-9a-f]{32}", identity), "invalid identity")
    revision = revision_from(issue, source)
    require(revision.task_id == identity, "current material revision differs")
    admissions = markers(comments, "admission")
    require(len(admissions) == 1, "not exactly one admission")
    author, binding, _ = admissions[0]
    require(
        trusted(trust, "trusted_admission_authors", author)
        and binding.get("contract_version") == CONTRACT
        and binding.get("source_issue") == source
        and binding.get("delivery_id") == identity
        and binding.get("correlation_id") == identity
        and binding.get("target_repository") == revision.target_repository
        and binding.get("control_plane_release") in TRUST,
        "untrusted admission or binding mismatch",
    )
    receipt = receipt_digest(comments, binding, trust, mode == "plan")
    existing = markers(comments, "source")
    require(len(existing) <= 1, "ambiguous source result")
    result = None
    if existing:
        author, marker, body = existing[0]
        require(author == SOURCE_AUTHOR, "untrusted source author")
        match = re.fullmatch(
            r"<!-- ai-sdlc-source-result:v2 [^\n]+ -->\n"
            r"### Receiver-validated execution result\n\n\x60\x60\x60json\n"
            r"([\s\S]+)\n\x60\x60\x60\n?",
            body,
        )
        require(match is not None, "malformed source projection")
        assert match is not None
        result = validate(decode(match.group(1)), binding)
        require(
            marker == {"delivery_id": identity, "result_sha256": digest(result)}
            and receipt == digest(result),
            "source projection digest mismatch",
        )
    if mode == "result":
        incoming = validate(incoming, binding)
        require(receipt == digest(incoming), "result lacks matching trusted receipt")
        require(result is None or result == incoming, "conflicting result")
        result = incoming
    if mode == "plan":
        require(result is not None, "historical terminal projection missing")
    current = labels(issue)
    require(issue.get("state") == "open", "closed issue; preserve disposition")
    require(
        not any(label.startswith("status:") and label not in ACTIVE for label in current),
        "human or unknown lifecycle disposition; reconcile manually",
    )
    if result is None:
        require(mode == "queued" and receipt is None, "terminal receipt awaits projection")
        require("status:approved" in current, "approval no longer current")
        return {
            "comment": None,
            "add": ["status:queued"] if "status:queued" not in current else [],
            "remove": ["status:approved"],
            "terminal": None,
        }
    return {
        "comment": projection_body(result) if not existing else None,
        "add": [],
        "remove": sorted(current & ACTIVE),
        "terminal": result["execution_status"],
    }


class GitHub:
    """Bounded source-only transport; no dispatch, merge or publication."""

    def __init__(self, number: str) -> None:
        require(re.fullmatch(r"[1-9][0-9]*", number), "invalid issue number")
        self.path = f"repos/{REPOSITORY}/issues/{number}"

    def api(self, *args: str, data: object = None) -> Any:
        command = ["gh", "api", *args]
        if data is not None:
            command += ["--input", "-"]
        raw = subprocess.run(
            command,
            input=json.dumps(data) if data is not None else None,
            text=True,
            capture_output=True,
            timeout=30,
            check=True,
        ).stdout
        return decode(raw) if raw.strip() else None

    def read(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        issue = self.api(self.path)
        pages = self.api("--paginate", "--slurp", self.path + "/comments?per_page=100")
        require(
            isinstance(pages, list) and all(isinstance(p, list) for p in pages),
            "comment pagination unavailable",
        )
        return issue, [c for page in pages for c in page]

    def trust(self, comments: Any) -> dict[str, Any]:
        rows = markers(comments, "admission")
        require(len(rows) == 1, "not exactly one admission")
        release = rows[0][1].get("control_plane_release")
        require(isinstance(release, str) and release in TRUST, "unsupported trust release")
        assert isinstance(release, str)
        return cast(
            dict[str, Any],
            self.api(
                "-H",
                "Accept: application/vnd.github.raw+json",
                f"repos/{CONTROL}/contents/config/codex-result-trust.json?ref={TRUST[release]}",
            ),
        )

    def comment(self, body: str) -> None:
        self.api("--method", "POST", self.path + "/comments", data={"body": body})

    def add(self, label: str) -> None:
        require(label == "status:queued", "unexpected label add")
        self.api("--method", "POST", self.path + "/labels", data={"labels": [label]})

    def remove(self, label: str) -> None:
        require(label in ACTIVE, "unexpected label removal")
        self.api("--method", "DELETE", self.path + "/labels/" + label.replace(":", "%3A"))


def snapshot(issue: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        issue["number"],
        issue["state"],
        issue["body"],
        issue["user"]["login"],
        frozenset(labels(issue)),
    )


def apply(api: Any, source: str, identity: str, mode: str, incoming: Any = None) -> dict[str, Any]:
    issue, comments = api.read()
    trust = api.trust(comments)
    decision = decide(issue, comments, trust, source, identity, mode, incoming)
    if mode == "plan":
        return {
            **decision,
            "source": source,
            "delivery_id": identity,
            "issue_body_sha256": hashlib.sha256(issue["body"].encode()).hexdigest(),
            "current_labels": sorted(labels(issue)),
            "mutation_authorized": False,
        }
    before, latest = api.read()
    require(snapshot(before) == snapshot(issue), "source changed")
    # Re-evaluate authority rather than comparing all comments byte-for-byte:
    # a matching forwarded marker may arrive between the two reads.
    require(markers(latest, "admission") == markers(comments, "admission"), "admission changed")
    require(
        decide(before, latest, trust, source, identity, mode, incoming) == decision,
        "projection decision changed",
    )
    if decision["comment"] is not None:
        api.comment(decision["comment"])
        before, latest = api.read()
        require(snapshot(before) == snapshot(issue), "source changed after comment")
        require(markers(latest, "admission") == markers(comments, "admission"), "admission changed")
        decision = decide(before, latest, trust, source, identity, mode, incoming)
        require(decision["comment"] is None, "source comment not verified")
    for label in decision["add"]:
        api.add(label)
    for label in decision["remove"]:
        api.remove(label)
    final, latest = api.read()
    require(
        final["body"] == issue["body"] and final["state"] == issue["state"],
        "source changed during projection",
    )
    expected = (labels(issue) | set(decision["add"])) - set(decision["remove"])
    require(labels(final) == expected, "label projection incomplete")
    require(markers(latest, "admission") == markers(comments, "admission"), "admission changed")
    if decision["terminal"] is None:
        require(
            not markers(latest, "receipt")
            and not markers(latest, "forwarded")
            and not markers(latest, "source"),
            "terminal evidence arrived during queued projection; reconcile",
        )
    else:
        proof = decide(final, latest, trust, source, identity, mode, incoming)
        require(not proof["comment"] and not proof["remove"], "terminal readback incomplete")
    return decision


def main() -> int:
    try:
        number = os.environ["ISSUE_NUMBER"]
        mode = os.environ["PROJECTION_MODE"]
        source = f"{REPOSITORY}#{number}"
        incoming = None
        if mode == "result":
            payload = decode(os.environ["CLIENT_PAYLOAD"])
            require(
                set(payload) == {"source_issue", "execution_result"}
                and payload["source_issue"] == source,
                "invalid dispatch",
            )
            incoming = payload["execution_result"]
            identity = incoming["delivery_id"]
        else:
            identity = os.environ["DELIVERY_ID"]
        result = apply(GitHub(number), source, identity, mode, incoming)
        print(json.dumps({k: v for k, v in result.items() if k != "comment"}, sort_keys=True))
        return 0
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError):
        print("SOURCE_PROJECTION_BLOCKED: conflicting or incomplete evidence; inspect source")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
