"""Planning and execution for portfolio issue mirroring."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .github_api import GitHubApi
from .models import Issue, SyncAction

SOURCE_REPO = "Young-Consultations/portfolio-tasks"
LEGACY_SOURCE_REPO = "mightyjoe909/portfolio-tasks"
TARGET_REPO = "Young-Consultations/slugger"
SOURCE_LABEL = "chatgpt-task"
MANAGED_LABEL = "portfolio-task"
MARKER = "<!-- portfolio-task-source: {repository}#{number} -->"


class MirrorLocator:
    @staticmethod
    def locate(issues: Iterable[Issue], source_number: int) -> Issue | None:
        markers = tuple(MARKER.format(repository=repo, number=source_number)
                        for repo in (SOURCE_REPO, LEGACY_SOURCE_REPO))
        matches = [issue for issue in issues if not issue.is_pull_request
                   and issue.body.endswith(markers)
                   and "\n## Portfolio Task Metadata\n" in issue.body]
        return min(matches, key=lambda issue: issue.number, default=None)


@dataclass(frozen=True)
class SyncPlan:
    action: SyncAction
    payload: dict[str, Any] | None
    target: Issue | None


class SyncPlanner:
    @staticmethod
    def body(source: Issue, managed: str = "Yes") -> str:
        body = re.sub(r"<!-- portfolio-task-source: [^>]*-->",
                      "[removed portfolio-task-source marker]", source.body)
        return (f"{body}\n\n---\n## Portfolio Task Metadata\n"
                f"- Source repository: `{SOURCE_REPO}`\n- Source issue: `#{source.number}`\n"
                f"- Source URL: `{source.html_url}`\n- Source state: `{source.state}`\n"
                f"- Managed automatically: {managed}\n"
                f"{MARKER.format(repository=SOURCE_REPO, number=source.number)}")

    @classmethod
    def desired(cls, source: Issue, target: Issue | None, managed: str = "Yes") -> dict[str, Any]:
        labels = sorted(set(target.labels if target else ()) - {SOURCE_LABEL} | {MANAGED_LABEL})
        state = target.state if managed != "Yes" and target else source.state
        return {"title": f"[PORTFOLIO-TASK #{source.number}] {source.title}",
                "body": cls.body(source, managed), "state": state,
                "labels": labels, "assignees": list(source.assignees)}

    @classmethod
    def plan(cls, source: Issue, target: Issue | None, label_removed: bool = False) -> SyncPlan:
        if label_removed:
            if target is None:
                return SyncPlan(SyncAction.NO_OP, None, None)
            payload = cls.desired(source, target, "No - chatgpt-task label removed")
            payload.pop("assignees")
            payload["labels"] = sorted(set(payload["labels"]) - {MANAGED_LABEL})
            return SyncPlan(SyncAction.DISABLE_SYNC, payload, target)
        if SOURCE_LABEL not in source.labels:
            return SyncPlan(SyncAction.SKIPPED, None, target)
        desired = cls.desired(source, target)
        if target is None:
            return SyncPlan(SyncAction.CREATE, desired, None)
        existing = {"title": target.title, "body": target.body, "state": target.state,
                    "labels": sorted(target.labels), "assignees": sorted(target.assignees)}
        comparable = {**desired, "labels": sorted(desired["labels"]),
                      "assignees": sorted(desired["assignees"])}
        if comparable == existing:
            action = SyncAction.NO_OP
        elif source.state == "closed" and target.state == "open":
            action = SyncAction.CLOSE
        elif source.state == "open" and target.state == "closed":
            action = SyncAction.REOPEN
        else:
            action = SyncAction.UPDATE
        return SyncPlan(action, desired, target)


class SyncExecutor:
    def __init__(self, api: GitHubApi) -> None:
        self.api = api

    def execute(self, plan: SyncPlan) -> None:
        if plan.payload is None:
            return
        if plan.action is SyncAction.CREATE:
            self.api.request("POST", f"repos/{TARGET_REPO}/issues", plan.payload)
        else:
            assert plan.target is not None
            self.api.request("PATCH", f"repos/{TARGET_REPO}/issues/{plan.target.number}", plan.payload)
