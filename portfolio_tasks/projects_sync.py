"""Optional GitHub Projects Phase 2 synchronization."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .github_api import GitHubApi, GitHubApiError
from .issue_parser import IssueFormParser, TargetRepositoryParser
from .issue_sync import SOURCE_LABEL, SOURCE_REPO
from .models import Issue

PROJECTS_PHASE2_SYNC_ENABLED = "PROJECTS_PHASE2_SYNC_ENABLED"
PROJECTS_PHASE2_PHASE1_ISSUE17_COMPLETE = "PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE"
PROJECTS_PHASE2_PROJECT_ID = "PROJECTS_PHASE2_PROJECT_ID"
PROJECTS_PHASE2_TOKEN = "PROJECTS_PHASE2_TOKEN"

DEPENDENCY_REFERENCE = re.compile(r"(?:#[0-9]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+)")
PROJECT_KEY = re.compile(r"[a-z0-9][a-z0-9-]*")

SINGLE_SELECT_FIELDS = {
    "Priority": ("P0", "P1", "P2", "P3"),
    "Executor": ("codex", "human", "chatgpt-planning"),
    "Execution status": ("proposed", "approved", "queued", "running", "draft-pr", "blocked", "done"),
    "Parallel-safe": ("yes", "no"),
    "Risk": ("low", "medium", "high"),
    "Estimated scope": ("small", "medium", "large"),
    "Task type": (
        "Bug fix",
        "Feature",
        "Refactor",
        "CI/CD",
        "Documentation",
        "Security",
        "Repository governance",
        "Automation",
        "Investigation",
    ),
}
SINGLE_SELECT_FIELD_NAMES = frozenset(("Project", *SINGLE_SELECT_FIELDS))
TEXT_FIELDS = ("Target repository", "Dependency issue references")
FIELD_ORDER = (
    "Project",
    "Priority",
    "Executor",
    "Execution status",
    "Target repository",
    "Parallel-safe",
    "Dependency issue references",
    "Risk",
    "Estimated scope",
    "Task type",
)


class ProjectsSyncApiError(RuntimeError):
    """A sanitized Projects GraphQL failure."""


@dataclass(frozen=True)
class ProjectFieldDefinition:
    field_id: str
    name: str
    kind: str
    options: Mapping[str, str]


@dataclass(frozen=True)
class ProjectItemSnapshot:
    issue_node_id: str
    item_id: str | None
    field_values: Mapping[str, str]


@dataclass(frozen=True)
class ProjectFieldUpdate:
    field_name: str
    field_id: str
    kind: str
    value: str
    option_id: str | None = None


@dataclass
class ProjectsSyncOutcome:
    action: str = "disabled"
    number: str = ""
    enabled: bool = False
    dry_run: bool = True
    source: Issue | None = None
    item_id: str | None = None
    updated_fields: tuple[str, ...] = ()
    errors: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


PROJECT_FIELDS_QUERY = """
query($project: ID!) {
  node(id: $project) {
    __typename
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          __typename
          ... on ProjectV2Field {
            id
            name
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""

PROJECT_ITEM_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      id
      projectItems(first: 20) {
        nodes {
          id
          project {
            id
          }
          fieldValues(first: 50) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field {
                  ... on ProjectV2Field {
                    name
                  }
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field {
                  ... on ProjectV2Field {
                    name
                  }
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

ADD_ITEM_MUTATION = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
    item {
      id
    }
  }
}
"""

UPDATE_TEXT_MUTATION = """
mutation($project: ID!, $item: ID!, $field: ID!, $text: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $project
      itemId: $item
      fieldId: $field
      value: {text: $text}
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

UPDATE_SINGLE_SELECT_MUTATION = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $project
      itemId: $item
      fieldId: $field
      value: {singleSelectOptionId: $option}
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""


def _is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def _split_repository(repository: str) -> tuple[str, str] | None:
    parts = repository.split("/", 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def desired_field_values(source: Issue) -> tuple[dict[str, str], tuple[str, ...]]:
    parser = IssueFormParser(source.body)
    errors: list[str] = []
    desired: dict[str, str] = {}
    for name in FIELD_ORDER:
        value = parser.value(name).strip()
        if not value:
            errors.append(f"Missing required issue-form field: {name}")
            continue
        desired[name] = value

    project_value = desired.get("Project", "")
    if project_value and not PROJECT_KEY.fullmatch(project_value):
        errors.append("Project must be a lowercase project key")

    for name, allowed in SINGLE_SELECT_FIELDS.items():
        selected = desired.get(name)
        if selected and selected not in allowed:
            errors.append(f"{name} must be one of: {', '.join(allowed)}")

    target_repository = desired.get("Target repository")
    if target_repository:
        parsed = TargetRepositoryParser.parse(target_repository)
        if parsed is None:
            errors.append("Target repository must use owner/repository format")
        else:
            desired["Target repository"] = parsed

    dependencies = desired.get("Dependency issue references")
    if dependencies:
        if dependencies.lower() == "none":
            desired["Dependency issue references"] = "none"
        else:
            parts = [part for part in re.split(r"[,\s]+", dependencies) if part]
            bad = [part for part in parts if not DEPENDENCY_REFERENCE.fullmatch(part)]
            if bad:
                errors.append(
                    "Dependency issue references contains malformed values: " + ", ".join(bad)
                )
            desired["Dependency issue references"] = " ".join(parts)

    return desired, tuple(errors)


def plan_updates(
    desired: Mapping[str, str],
    current: Mapping[str, str],
    definitions: Mapping[str, ProjectFieldDefinition],
) -> tuple[tuple[ProjectFieldUpdate, ...], tuple[str, ...]]:
    errors: list[str] = []
    updates: list[ProjectFieldUpdate] = []
    for field_name in FIELD_ORDER:
        definition = definitions.get(field_name)
        if definition is None:
            errors.append(f"Project is missing required field: {field_name}")
            continue
        expected_kind = "single-select" if field_name in SINGLE_SELECT_FIELD_NAMES else "text"
        if definition.kind != expected_kind:
            errors.append(
                f"Project field has wrong type for {field_name}: expected {expected_kind}, got {definition.kind}"
            )
            continue
        desired_value = desired[field_name]
        if definition.kind == "single-select":
            option_id = definition.options.get(desired_value)
            if option_id is None:
                errors.append(
                    f"Project field option missing for {field_name}: {desired_value}"
                )
                continue
        else:
            option_id = None
        if current.get(field_name, "") == desired_value:
            continue
        updates.append(
            ProjectFieldUpdate(
                field_name=field_name,
                field_id=definition.field_id,
                kind=definition.kind,
                value=desired_value,
                option_id=option_id,
            )
        )
    return tuple(updates), tuple(errors)


def _field_name(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    name = value.get("name")
    return str(name) if isinstance(name, str) else ""


class ProjectsGraphQLApi:
    def __init__(self, token: str | None, timeout: float = 20, *, dry_run: bool = False) -> None:
        self.token = token
        self.timeout = timeout
        self.dry_run = dry_run

    def _request(self, query: str, variables: Mapping[str, object]) -> Mapping[str, Any]:
        if not self.token:
            raise ProjectsSyncApiError("GitHub token is required")
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = Request(
            "https://api.github.com/graphql",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                value = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise ProjectsSyncApiError(
                f"GitHub Projects API request failed ({type(error).__name__})"
            ) from error
        if not isinstance(value, dict):
            raise ProjectsSyncApiError("GitHub Projects API returned an invalid payload")
        errors = value.get("errors")
        if isinstance(errors, list) and errors:
            message = errors[0].get("message") if isinstance(errors[0], dict) else "unknown"
            raise ProjectsSyncApiError(f"GitHub Projects API rejected request: {message}")
        data = value.get("data")
        if not isinstance(data, dict):
            raise ProjectsSyncApiError("GitHub Projects API response did not include data")
        return data

    def project_fields(self, project_id: str) -> Mapping[str, ProjectFieldDefinition]:
        data = self._request(PROJECT_FIELDS_QUERY, {"project": project_id})
        node = data.get("node")
        if not isinstance(node, dict) or node.get("__typename") != "ProjectV2":
            raise ProjectsSyncApiError("PROJECTS_PHASE2_PROJECT_ID is not a ProjectV2")
        fields = node.get("fields")
        if not isinstance(fields, dict):
            raise ProjectsSyncApiError("Project fields response is malformed")
        nodes = fields.get("nodes")
        if not isinstance(nodes, list):
            raise ProjectsSyncApiError("Project fields list is malformed")

        definitions: dict[str, ProjectFieldDefinition] = {}
        for node_item in nodes:
            if not isinstance(node_item, dict):
                continue
            typename = node_item.get("__typename")
            field_id = str(node_item.get("id") or "")
            name = str(node_item.get("name") or "")
            if not field_id or not name:
                continue
            if typename == "ProjectV2SingleSelectField":
                options_raw = node_item.get("options")
                options: dict[str, str] = {}
                if isinstance(options_raw, list):
                    for option in options_raw:
                        if isinstance(option, dict):
                            option_name = str(option.get("name") or "")
                            option_id = str(option.get("id") or "")
                            if option_name and option_id:
                                options[option_name] = option_id
                definitions[name] = ProjectFieldDefinition(
                    field_id=field_id,
                    name=name,
                    kind="single-select",
                    options=options,
                )
            elif typename == "ProjectV2Field":
                definitions[name] = ProjectFieldDefinition(
                    field_id=field_id,
                    name=name,
                    kind="text",
                    options={},
                )
        return definitions

    def issue_snapshot(self, project_id: str, repository: str, number: int) -> ProjectItemSnapshot:
        owner_repository = _split_repository(repository)
        if owner_repository is None:
            raise ProjectsSyncApiError("Source repository must use owner/repository format")
        owner, repo = owner_repository
        data = self._request(
            PROJECT_ITEM_QUERY,
            {"owner": owner, "repo": repo, "number": number},
        )
        repository_data = data.get("repository")
        if not isinstance(repository_data, dict):
            raise ProjectsSyncApiError("Repository lookup failed")
        issue_data = repository_data.get("issue")
        if not isinstance(issue_data, dict):
            raise ProjectsSyncApiError("Source issue was not found")
        issue_node_id = str(issue_data.get("id") or "")
        if not issue_node_id:
            raise ProjectsSyncApiError("Source issue node ID is missing")

        item_id: str | None = None
        values: dict[str, str] = {}
        items = issue_data.get("projectItems")
        if isinstance(items, dict):
            nodes = items.get("nodes")
            if isinstance(nodes, list):
                for item in nodes:
                    if not isinstance(item, dict):
                        continue
                    project = item.get("project")
                    if not isinstance(project, dict) or project.get("id") != project_id:
                        continue
                    item_id = str(item.get("id") or "") or None
                    raw_values = item.get("fieldValues")
                    if isinstance(raw_values, dict):
                        value_nodes = raw_values.get("nodes")
                        if isinstance(value_nodes, list):
                            for entry in value_nodes:
                                if not isinstance(entry, dict):
                                    continue
                                typename = entry.get("__typename")
                                field_name = _field_name(entry.get("field"))
                                if not field_name:
                                    continue
                                if typename == "ProjectV2ItemFieldSingleSelectValue":
                                    name = entry.get("name")
                                    values[field_name] = str(name) if isinstance(name, str) else ""
                                elif typename == "ProjectV2ItemFieldTextValue":
                                    text = entry.get("text")
                                    values[field_name] = str(text) if isinstance(text, str) else ""
                    break
        return ProjectItemSnapshot(issue_node_id=issue_node_id, item_id=item_id, field_values=values)

    def add_item(self, project_id: str, issue_node_id: str) -> str:
        if self.dry_run:
            return "dry-run-item"
        data = self._request(ADD_ITEM_MUTATION, {"project": project_id, "content": issue_node_id})
        add_item = data.get("addProjectV2ItemById")
        if not isinstance(add_item, dict):
            raise ProjectsSyncApiError("Project item create response is malformed")
        item = add_item.get("item")
        if not isinstance(item, dict) or not item.get("id"):
            raise ProjectsSyncApiError("Project item create response did not return an item ID")
        return str(item["id"])

    def update_item_field(self, project_id: str, item_id: str, update: ProjectFieldUpdate) -> None:
        if self.dry_run:
            return
        if update.kind == "single-select":
            assert update.option_id is not None
            self._request(
                UPDATE_SINGLE_SELECT_MUTATION,
                {
                    "project": project_id,
                    "item": item_id,
                    "field": update.field_id,
                    "option": update.option_id,
                },
            )
            return
        self._request(
            UPDATE_TEXT_MUTATION,
            {
                "project": project_id,
                "item": item_id,
                "field": update.field_id,
                "text": update.value,
            },
        )


def _build_rest_api(token: str | None, dry_run: bool) -> GitHubApi:
    mock = os.getenv("GH_MOCK_DIR")
    return GitHubApi(
        token,
        float(os.getenv("API_TIMEOUT", "20")),
        mock_dir=Path(mock) if mock else None,
        dry_run=dry_run,
    )


def _build_projects_api(token: str | None, dry_run: bool) -> ProjectsGraphQLApi:
    return ProjectsGraphQLApi(token, float(os.getenv("API_TIMEOUT", "20")), dry_run=dry_run)


def _summary_lines(outcome: ProjectsSyncOutcome, project_id_configured: bool) -> Sequence[str]:
    source = outcome.source
    labels = source.labels if source else ()
    return (
        "## GitHub Projects Phase 2 Synchronization",
        f"- Source repository: `{SOURCE_REPO}`",
        f"- Source issue number: `{outcome.number}`",
        f"- Source issue title: {source.title if source else ''}",
        f"- chatgpt-task present: `{str(SOURCE_LABEL in labels).lower()}`",
        f"- Phase 2 enabled: `{str(outcome.enabled).lower()}`",
        f"- Phase 1 issue #17 prerequisite confirmed: `{str(_is_true(os.getenv(PROJECTS_PHASE2_PHASE1_ISSUE17_COMPLETE, 'false'))).lower()}`",
        f"- Organization project ID configured: `{str(project_id_configured).lower()}`",
        f"- Matching project item ID: `{outcome.item_id or 'none'}`",
        f"- Planned/completed action: `{outcome.action}`",
        f"- Updated fields: {', '.join(outcome.updated_fields) if outcome.updated_fields else 'none'}",
        f"- Dry run: `{str(outcome.dry_run).lower()}`",
        f"- Validation errors: {' '.join(outcome.errors or []) or 'none'}",
        f"- API failures: {' '.join(outcome.failures or []) or 'none'}",
        f"- Final synchronization result: `{'failed' if (outcome.errors or outcome.failures) else 'success'}`",
    )


def sync_projects_phase2() -> int:
    dry_run = _is_true(os.getenv("DRY_RUN", "true"))
    summary_path = Path(os.getenv("GITHUB_STEP_SUMMARY", os.devnull))
    enabled = _is_true(os.getenv(PROJECTS_PHASE2_SYNC_ENABLED, "false"))
    project_id = os.getenv(PROJECTS_PHASE2_PROJECT_ID, "").strip()
    token = os.getenv(PROJECTS_PHASE2_TOKEN)
    number = os.getenv("SOURCE_ISSUE_NUMBER", "")
    event_path = Path(os.getenv("GITHUB_EVENT_PATH", ""))
    outcome = ProjectsSyncOutcome(number=number, enabled=enabled, dry_run=dry_run)

    event: dict[str, Any] = {}
    if event_path.is_file():
        try:
            loaded = json.loads(event_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                event = loaded
        except json.JSONDecodeError:
            outcome.errors.append("GITHUB_EVENT_PATH did not contain valid JSON")

    if os.getenv("GITHUB_EVENT_NAME") == "issues":
        issue_number = event.get("issue", {}).get("number") if isinstance(event.get("issue"), dict) else ""
        outcome.number = str(issue_number or "")

    if not enabled:
        outcome.action = "disabled"
    elif not _is_true(os.getenv(PROJECTS_PHASE2_PHASE1_ISSUE17_COMPLETE, "false")):
        outcome.errors.append(
            f"{PROJECTS_PHASE2_PHASE1_ISSUE17_COMPLETE} must be true before enabling Phase 2 synchronization"
        )
    if enabled and not project_id:
        outcome.errors.append(
            f"{PROJECTS_PHASE2_PROJECT_ID} is required when {PROJECTS_PHASE2_SYNC_ENABLED}=true"
        )
    if enabled and not token:
        outcome.errors.append(
            f"{PROJECTS_PHASE2_TOKEN} is required when {PROJECTS_PHASE2_SYNC_ENABLED}=true"
        )

    if enabled and not outcome.errors:
        if not outcome.number.isdigit():
            outcome.errors.append("source_issue_number must be numeric")
        else:
            rest_api = _build_rest_api(token, dry_run)
            projects_api = _build_projects_api(token, dry_run)
            try:
                source_data = rest_api.request("GET", f"repos/{SOURCE_REPO}/issues/{outcome.number}")
                source = Issue.from_json(source_data)
                outcome.source = source
                if source.is_pull_request:
                    outcome.errors.append("Pull requests are not synchronized")
                if SOURCE_LABEL not in source.labels:
                    outcome.action = "skipped"
                if not outcome.errors and outcome.action != "skipped":
                    desired, validation_errors = desired_field_values(source)
                    if validation_errors:
                        outcome.errors.extend(validation_errors)
                    else:
                        definitions = projects_api.project_fields(project_id)
                        snapshot = projects_api.issue_snapshot(
                            project_id,
                            SOURCE_REPO,
                            int(outcome.number),
                        )
                        updates, planning_errors = plan_updates(
                            desired,
                            snapshot.field_values,
                            definitions,
                        )
                        if planning_errors:
                            outcome.errors.extend(planning_errors)
                        else:
                            item_id = snapshot.item_id
                            if item_id is None:
                                item_id = projects_api.add_item(project_id, snapshot.issue_node_id)
                                outcome.action = "create-item"
                            if updates:
                                if outcome.action != "create-item":
                                    outcome.action = "update"
                                for update in updates:
                                    projects_api.update_item_field(project_id, item_id, update)
                                outcome.updated_fields = tuple(update.field_name for update in updates)
                            elif outcome.action != "create-item":
                                outcome.action = "no-op"
                            outcome.item_id = item_id
            except (GitHubApiError, ProjectsSyncApiError) as error:
                outcome.failures.append(str(error))
                if outcome.action not in {"disabled", "skipped"}:
                    outcome.action = "failed"

    lines = _summary_lines(outcome, bool(project_id))
    with summary_path.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return 1 if outcome.errors or outcome.failures else 0
