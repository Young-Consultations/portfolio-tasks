"""Route newly labelled intake issues into the Phase 1 organization project."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .issue_parser import IssueFormParser

ORGANIZATION = "Young-Consultations"
PROJECT_TITLE = "Portfolio Tasks - Phase 1"
FIELD_VALUES = {"Execution status": "proposed", "Executor": "codex"}

DISCOVERY_QUERY = """
query($organization: String!) {
  organization(login: $organization) {
    projectsV2(first: 100) {
      nodes {
        id
        title
        fields(first: 100) {
          nodes {
            __typename
            ... on ProjectV2SingleSelectField {
              id
              name
              options { id name }
            }
          }
        }
      }
    }
  }
}
"""

ISSUE_QUERY = """
query($owner: String!, $repository: String!, $number: Int!) {
  repository(owner: $owner, name: $repository) {
    issue(number: $number) {
      id
      projectItems(first: 100) { nodes { id project { id } } }
    }
  }
}
"""

ADD_ITEM_MUTATION = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
    item { id }
  }
}
"""

UPDATE_FIELD_MUTATION = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project
    itemId: $item
    fieldId: $field
    value: {singleSelectOptionId: $option}
  }) { projectV2Item { id } }
}
"""


class IntakeError(RuntimeError):
    """An actionable, token-safe routing failure."""


@dataclass(frozen=True)
class SelectField:
    field_id: str
    options: dict[str, str]


def graphql_payload(query: str, variables: dict[str, object]) -> dict[str, object]:
    """Build a GraphQL request body without interpolating untrusted values."""
    return {"query": query, "variables": variables}


class GraphQLClient:
    def __init__(self, token: str) -> None:
        self.token = token

    def execute(self, query: str, variables: dict[str, object]) -> dict[str, Any]:
        request = Request(
            "https://api.github.com/graphql",
            data=json.dumps(graphql_payload(query, variables)).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                result = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise IntakeError(
                f"GitHub GraphQL request failed ({type(error).__name__}); "
                "check GitHub App installation and permissions"
            ) from error
        errors = result.get("errors", [])
        if errors:
            messages = "; ".join(str(error.get("message", "unknown error")) for error in errors)
            raise IntakeError(f"GitHub GraphQL returned errors: {messages}")
        data = result.get("data")
        if not isinstance(data, dict):
            raise IntakeError("GitHub GraphQL response did not contain data")
        return data


def discover_project(data: dict[str, Any]) -> tuple[str, dict[str, SelectField]]:
    organization = data.get("organization")
    if not organization:
        raise IntakeError(f"Organization {ORGANIZATION!r} is unavailable to the GitHub App")
    projects = organization.get("projectsV2", {}).get("nodes", [])
    project = next((node for node in projects if node.get("title") == PROJECT_TITLE), None)
    if project is None:
        raise IntakeError(
            f"Organization project {PROJECT_TITLE!r} was not found in the first 100 projects"
        )
    fields: dict[str, SelectField] = {}
    for node in project.get("fields", {}).get("nodes", []):
        if node.get("__typename") == "ProjectV2SingleSelectField":
            fields[node["name"]] = SelectField(
                node["id"], {option["name"]: option["id"] for option in node.get("options", [])}
            )
    return project["id"], fields


def required_option(fields: dict[str, SelectField], name: str, value: str) -> tuple[str, str]:
    field = fields.get(name)
    if field is None:
        raise IntakeError(f"Project is missing single-select field {name!r}")
    option = field.options.get(value)
    if option is None:
        raise IntakeError(f"Project field {name!r} is missing option {value!r}")
    return field.field_id, option


def route_issue(event: dict[str, Any], client: GraphQLClient) -> str:
    label = event.get("label", {}).get("name")
    if label != "chatgpt-task":
        raise IntakeError("This router only accepts a labeled event for 'chatgpt-task'")
    issue = event.get("issue", {})
    priority = IssueFormParser(str(issue.get("body") or "")).value("Priority").strip()
    if priority not in {"P0", "P1", "P2", "P3"}:
        raise IntakeError("Structured issue-form field 'Priority' must be P0, P1, P2, or P3")

    discovery = client.execute(DISCOVERY_QUERY, {"organization": ORGANIZATION})
    project_id, fields = discover_project(discovery)
    desired = {**FIELD_VALUES, "Priority": priority}
    resolved = {name: required_option(fields, name, value) for name, value in desired.items()}

    repository = event.get("repository", {}).get("name")
    number = issue.get("number")
    snapshot = (
        client.execute(
            ISSUE_QUERY, {"owner": ORGANIZATION, "repository": repository, "number": number}
        )
        .get("repository", {})
        .get("issue")
    )
    if not snapshot:
        raise IntakeError("The triggering issue was not returned by GitHub GraphQL")
    existing = next(
        (item for item in snapshot["projectItems"]["nodes"] if item["project"]["id"] == project_id),
        None,
    )
    if existing:
        item_id = existing["id"]
        print(f"Issue is already in the project; using Project item ID {item_id}")
    else:
        added = client.execute(
            ADD_ITEM_MUTATION, {"project": project_id, "content": snapshot["id"]}
        )
        item_id = added["addProjectV2ItemById"]["item"]["id"]
        print(f"Added issue to project; captured Project item ID {item_id}")

    if not isinstance(item_id, str) or not item_id:
        raise IntakeError("GitHub did not return a valid Project item ID")

    for name, value in desired.items():
        field_id, option_id = resolved[name]
        client.execute(
            UPDATE_FIELD_MUTATION,
            {"project": project_id, "item": item_id, "field": field_id, "option": option_id},
        )
        print(f"Set {name} = {value}")
    return item_id


def main() -> int:
    try:
        token = os.environ.get("PROJECT_ROUTER_TOKEN", "")
        event_path = os.environ.get("GITHUB_EVENT_PATH", "")
        if not token:
            raise IntakeError("PROJECT_ROUTER_TOKEN is missing; verify GitHub App credentials")
        if not event_path:
            raise IntakeError("GITHUB_EVENT_PATH is missing")
        with open(event_path, encoding="utf-8") as stream:
            event = json.load(stream)
        route_issue(event, GraphQLClient(token))
        return 0
    except (IntakeError, OSError, json.JSONDecodeError) as error:
        print(f"::error title=Project intake routing failed::{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
