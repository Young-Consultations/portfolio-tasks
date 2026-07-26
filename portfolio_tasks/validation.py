"""Portfolio dispatch and execution authorization validation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Collection

from .issue_parser import IssueFormParser, TargetRepositoryParser

REQUIRED_FIELDS = (
    "Project", "Priority", "Executor", "Execution status", "Target repository",
    "Parallel-safe", "Dependency issue references", "Risk", "Estimated scope",
    "Objective", "Required behavior", "Acceptance criteria", "Testing requirements",
    "Security and safety constraints",
)
ALLOWED = {
    "Priority": ("P0", "P1", "P2", "P3"),
    "Executor": ("codex", "human", "chatgpt-planning"),
    "Execution status": ("proposed", "approved", "queued", "running", "draft-pr", "blocked", "done"),
    "Parallel-safe": ("yes", "no"), "Risk": ("low", "medium", "high"),
    "Estimated scope": ("small", "medium", "large"),
}
DEPENDENCY = re.compile(r"(?:#[0-9]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+)")


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def comment(self) -> str:
        if self.ok:
            return "Portfolio dispatch validation passed. This issue is eligible for Codex dispatch."
        return "Portfolio dispatch validation failed. Fix these items before Codex dispatch:\n" + "".join(
            f"- {error}\n" for error in self.errors)


def validate_dispatch(issue: dict[str, Any], open_dependencies: Collection[str] | None = None) -> ValidationResult:
    parser = IssueFormParser(str(issue.get("body") or ""))
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        value = parser.value(field)
        if not value or re.fullmatch(r"_[Nn]o response_", value):
            errors.append(f"Missing required metadata field: {field}")
    for field, allowed in ALLOWED.items():
        value = parser.value(field)
        if value and value not in allowed:
            errors.append(f"{field} must be one of: {', '.join(allowed)}")
    target = parser.value("Target repository")
    if target and TargetRepositoryParser.parse(target) is None:
        errors.append("Target repository must use owner/repository format with GitHub-safe characters")
    if parser.value("Executor") != "codex":
        errors.append("Codex dispatch requires Executor to be codex")
    if parser.value("Execution status") != "approved":
        errors.append("Codex dispatch requires Execution status to be approved")
    dependencies = parser.value("Dependency issue references")
    if dependencies and dependencies.lower() != "none":
        for reference in re.split(r"[,\s]+", dependencies):
            if not reference:
                continue
            if not DEPENDENCY.fullmatch(reference):
                errors.append(f"Dependency reference is malformed: {reference}")
            elif open_dependencies is not None and reference not in open_dependencies:
                errors.append(f"Dependency reference is unresolved or closed: {reference}")
    labels = {str(label.get("name", "") if isinstance(label, dict) else label)
              for label in issue.get("labels", [])}
    for field, prefix in (("Project", "project"), ("Priority", "priority")):
        value = parser.value(field)
        if value and f"{prefix}:{value}" not in labels:
            errors.append(f"Missing deterministic {prefix} label: {prefix}:{value}")
    return ValidationResult(tuple(errors))


def parse_source_issue(value: str) -> int:
    patterns = (r"([0-9]+)", r"Young-Consultations/portfolio-tasks#([0-9]+)",
                r"https://github\.com/Young-Consultations/portfolio-tasks/issues/([0-9]+)")
    for pattern in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            return int(match.group(1))
    raise ValueError("source_issue must identify an issue in Young-Consultations/portfolio-tasks")
