"""Thin repository-policy adapter for the shared AI-SDLC contracts package.

Schema ownership and validation deliberately remain in ``ai_sdlc_contracts``.  This
module only applies portfolio-tasks policy and formats workflow output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request

from .codex_subprocess import run_checked

TARGET_REPOSITORY = "Young-Consultations/portfolio-tasks"
SOURCE_ISSUE = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#([1-9][0-9]*)$")
CANONICAL_EXECUTION_STATUSES = frozenset(
    {"verified", "draft-pr-created", "no-changes", "blocked", "failed"}
)
PREFLIGHT_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def publication_identity(repository: str, branch: str) -> str:
    """Return the deterministic publication identity used by executor preflight."""
    return f"{repository}:{branch}"


def publication_preflight_decision(
    *,
    publication_key: str,
    pulls: Sequence[dict[str, Any]],
    branch_exists: bool,
) -> dict[str, str]:
    """Decide whether executor publication may continue before running Codex."""
    open_pulls = [pull for pull in pulls if pull.get("state") == "open"]
    if len(open_pulls) > 1:
        raise ValueError(
            "Refusing to execute Codex: found "
            f"{len(open_pulls)} open pull requests for publication identity {publication_key}."
        )
    if len(open_pulls) == 1:
        pull = open_pulls[0]
        draft = pull.get("draft")
        if draft is not True:
            if draft is False:
                raise ValueError(
                    "Refusing to execute Codex: existing open pull request "
                    f"for publication identity {publication_key} is not a draft."
                )
            raise ValueError(
                "Refusing to execute Codex: existing open pull request "
                f"for publication identity {publication_key} has invalid draft state."
            )
        pr_url = pull.get("html_url")
        if not isinstance(pr_url, str) or not pr_url.strip():
            raise ValueError(
                "Refusing to execute Codex: existing draft pull request for "
                f"publication identity {publication_key} is missing html_url."
            )
        return {
            "should_run_codex": "false",
            "reuse_open_draft": "true",
            "publish_ok": "true",
            "pr_url": pr_url,
        }
    if pulls:
        raise ValueError(
            "Refusing to execute Codex: a closed or merged pull request already exists "
            f"for publication identity {publication_key}."
        )
    if branch_exists:
        raise ValueError(
            "Refusing to execute Codex: publication branch exists without an open draft pull "
            f"request for publication identity {publication_key}."
        )
    return {
        "should_run_codex": "true",
        "reuse_open_draft": "false",
        "publish_ok": "false",
        "pr_url": "",
    }


def _github_get_json(
    *, api_root: str, token: str, path: str, query: dict[str, str] | None = None
) -> tuple[int, Any]:
    if not api_root.startswith("https://"):
        raise ValueError("api_root must use https")
    url = f"{api_root.rstrip('/')}{path}"
    if query:
        url += f"?{url_parse.urlencode(query)}"
    request = url_request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with url_request.urlopen(request) as response:
            body = response.read()
            status = response.status
    except url_error.HTTPError as error:
        if error.code == 404:
            return 404, None
        raise RuntimeError(f"GitHub API request failed with status {error.code}.") from error
    except OSError as error:
        raise RuntimeError("GitHub API request failed before receiving a response.") from error
    try:
        return status, json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError("GitHub API response was not valid JSON.") from error


def _list_publication_pulls(
    *, repository: str, branch: str, api_root: str, token: str
) -> list[dict[str, Any]]:
    owner = repository.split("/", 1)[0]
    _, payload = _github_get_json(
        api_root=api_root,
        token=token,
        path=f"/repos/{repository}/pulls",
        query={"state": "all", "head": f"{owner}:{branch}"},
    )
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise RuntimeError("GitHub pull-request query returned an invalid payload.")
    return list(payload)


def _publication_branch_exists(*, repository: str, branch: str, api_root: str, token: str) -> bool:
    escaped_branch = url_parse.quote(branch, safe="")
    status, payload = _github_get_json(
        api_root=api_root,
        token=token,
        path=f"/repos/{repository}/branches/{escaped_branch}",
    )
    if status == 404:
        return False
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError("GitHub branch lookup returned an invalid payload.")
    return True


def publication_preflight_outputs(*, repository: str, branch: str, api_root: str) -> dict[str, str]:
    """Return deterministic executor preflight outputs for GitHub Actions."""
    if PREFLIGHT_REPO.fullmatch(repository) is None:
        raise ValueError("repository must be owner/repository")
    if not branch.strip():
        raise ValueError("branch must be non-empty")
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        raise ValueError("GH_TOKEN must be set")
    key = publication_identity(repository, branch)
    pulls = _list_publication_pulls(
        repository=repository,
        branch=branch,
        api_root=api_root,
        token=token,
    )
    branch_exists = _publication_branch_exists(
        repository=repository,
        branch=branch,
        api_root=api_root,
        token=token,
    )
    return {
        "publication_identity": key,
        **publication_preflight_decision(
            publication_key=key,
            pulls=pulls,
            branch_exists=branch_exists,
        ),
    }


def canonical_execution_status(
    *,
    mode: str,
    authorization_ok: bool,
    validation_ok: bool,
    publish_ok: bool,
    pr_url: str | None,
    no_changes: bool,
) -> str:
    """Map workflow outcomes to the execution-result v2 status vocabulary."""
    if mode not in {"verify", "implement"}:
        raise ValueError("mode must be verify or implement")
    if not authorization_ok:
        return "blocked"
    if no_changes and validation_ok:
        return "verified"
    if not validation_ok:
        return "failed"
    if mode == "verify":
        return "verified"
    if publish_ok and pr_url:
        return "draft-pr-created"
    return "failed"


def load_execution_input(path: Path) -> dict[str, Any]:
    """Validate with the shared package, then enforce target repository policy."""
    run_checked(
        [sys.executable, "-m", "ai_sdlc_contracts", "validate-input", str(path)],
        stdout=subprocess.DEVNULL,
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("execution input must be an object")
    if value.get("target_repository") != TARGET_REPOSITORY:
        raise ValueError("execution input targets another repository")
    if value.get("executor") != "codex" or value.get("draft_pr_only") is not True:
        raise ValueError("execution input violates executor or draft-PR policy")
    mode = value.get("execution_mode")
    if mode not in {"verify", "implement"}:
        raise ValueError("execution_mode must be verify or implement")
    source = value.get("source_issue")
    match = SOURCE_ISSUE.fullmatch(source) if isinstance(source, str) else None
    if match is None or match.group(1) != TARGET_REPOSITORY:
        raise ValueError("source_issue is not a canonical portfolio-tasks issue")
    return value


def workflow_outputs(value: dict[str, Any]) -> dict[str, str]:
    """Return the small set of trusted values needed by workflow orchestration."""
    match = SOURCE_ISSUE.fullmatch(str(value["source_issue"]))
    assert match is not None  # load_execution_input establishes this invariant
    return {
        "source_repository": match.group(1),
        "issue": match.group(2),
        "correlation": str(value["correlation_id"]),
        "execution_mode": str(value["execution_mode"]),
        "branch": str(value["requested_branch"]),
    }


def validate_result(path: Path) -> None:
    """Delegate execution-result validation to the canonical package."""
    run_checked(
        [sys.executable, "-m", "ai_sdlc_contracts", "validate-result", str(path)],
        stdout=subprocess.DEVNULL,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("publication-preflight")
    preflight_parser.add_argument("--repository", required=True)
    preflight_parser.add_argument("--branch", required=True)
    preflight_parser.add_argument("--api-root", required=True)
    for command in ("inspect-input", "validate-result"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("path", type=Path)
    status_parser = subparsers.add_parser("execution-status")
    status_parser.add_argument("--mode", required=True, choices=("verify", "implement"))
    status_parser.add_argument("--authorization-ok", action="store_true")
    status_parser.add_argument("--validation-ok", action="store_true")
    status_parser.add_argument("--publish-ok", action="store_true")
    status_parser.add_argument("--pr-url")
    status_parser.add_argument("--no-changes", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "execution-status":
        print(
            canonical_execution_status(
                mode=args.mode,
                authorization_ok=args.authorization_ok,
                validation_ok=args.validation_ok,
                publish_ok=args.publish_ok,
                pr_url=args.pr_url,
                no_changes=args.no_changes,
            )
        )
        return 0
    if args.command == "publication-preflight":
        for key, value in publication_preflight_outputs(
            repository=args.repository,
            branch=args.branch,
            api_root=args.api_root,
        ).items():
            print(f"{key}={value}")
        return 0
    if args.command == "validate-result":
        validate_result(args.path)
        return 0
    for key, value in workflow_outputs(load_execution_input(args.path)).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
