"""Typed GitHub domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SyncAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    NO_OP = "no-op"
    CLOSE = "close"
    REOPEN = "reopen"
    DISABLE_SYNC = "disable-sync"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    state: str
    labels: tuple[str, ...] = field(default_factory=tuple)
    assignees: tuple[str, ...] = field(default_factory=tuple)
    html_url: str = ""
    is_pull_request: bool = False

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> Issue:
        def names(key: str, name: str) -> tuple[str, ...]:
            return tuple(
                str(item.get(name, "") if isinstance(item, dict) else item)
                for item in value.get(key, [])
            )

        return cls(
            number=int(value.get("number", 0)), title=str(value.get("title") or ""),
            body=str(value.get("body") or ""), state=str(value.get("state") or ""),
            labels=names("labels", "name"), assignees=names("assignees", "login"),
            html_url=str(value.get("html_url") or ""),
            is_pull_request="pull_request" in value,
        )
