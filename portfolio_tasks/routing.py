"""Policy gates for routing approved portfolio issues.

Contract parsing and construction intentionally live in ``ai_sdlc_contracts``;
this module only decides whether an issue event is authorized to reach it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Issue

REQUIRED_LABELS = frozenset({"chatgpt-task", "executor:codex", "status:approved"})
TERMINAL_ROUTING_LABELS = frozenset(
    {"status:queued", "status:running", "status:draft-pr", "status:done"}
)


@dataclass(frozen=True)
class RouteDecision:
    route: bool
    reason: str


def route_decision(issue: Issue) -> RouteDecision:
    """Apply the fail-closed, idempotent approval gate for the central router."""
    labels = frozenset(issue.labels)
    if issue.state != "open":
        return RouteDecision(False, "source-not-open")
    if issue.is_pull_request:
        return RouteDecision(False, "source-is-pull-request")
    if "sensitive" in labels:
        return RouteDecision(False, "sensitive")
    if labels & TERMINAL_ROUTING_LABELS:
        return RouteDecision(False, "already-dispatched")
    if not REQUIRED_LABELS <= labels:
        return RouteDecision(False, "not-approved")
    return RouteDecision(True, "approved")
