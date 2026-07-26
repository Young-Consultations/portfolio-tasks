"""Small, reusable GitHub REST client."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class GitHubApiError(RuntimeError):
    """A sanitized GitHub API failure."""


@dataclass
class GitHubApi:
    token: str | None
    timeout: float = 20
    api_root: str = "https://api.github.com"
    mock_dir: Path | None = None
    dry_run: bool = False

    def request(self, method: str, endpoint: str,
                payload: dict[str, Any] | None = None) -> Any:
        if self.dry_run and method != "GET":
            return {}
        if self.mock_dir is not None:
            if method != "GET":
                with (self.mock_dir / "writes.log").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(payload, separators=(",", ":")) + "\n")
                return {}
            mock_endpoint = endpoint.split("?", 1)[0]
            key = re.sub(r"[^A-Za-z0-9_.-]", "", f"{method}_{mock_endpoint.replace('/', '_')}")
            path = self.mock_dir / f"{key}.json"
            if not path.is_file():
                raise GitHubApiError(f"mock missing: {key}")
            return json.loads(path.read_text(encoding="utf-8"))
        if not self.token:
            raise GitHubApiError("GitHub token is required")
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(f"{self.api_root}/{endpoint}", data=data, method=method,
                          headers={"Authorization": f"Bearer {self.token}",
                                   "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise GitHubApiError(f"GitHub API request failed ({type(error).__name__})") from error
