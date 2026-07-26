"""Parsers for GitHub issue-form Markdown."""

from __future__ import annotations

import re


class IssueFormParser:
    """Parse level-three issue-form headings without executing their content."""

    _heading = re.compile(r"^### (.+)$")

    def __init__(self, body: str) -> None:
        self.sections = self._parse(body)

    @classmethod
    def _parse(cls, body: str) -> dict[str, str]:
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for raw_line in body.splitlines():
            match = cls._heading.fullmatch(raw_line.rstrip("\r"))
            if match:
                current = match.group(1)
                sections.setdefault(current, [])
            elif current is not None:
                sections[current].append(raw_line.rstrip("\r"))
        return {key: "\n".join(lines).strip("\n") for key, lines in sections.items()}

    def value(self, label: str) -> str:
        return self.sections.get(label, "")


class TargetRepositoryParser:
    _repository = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")

    @classmethod
    def parse(cls, value: str) -> str | None:
        cleaned = value.removeprefix("- ").removeprefix("`").removesuffix("`")
        return cleaned if cls._repository.fullmatch(cleaned) else None
