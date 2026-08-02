from typing import Any

import pytest

from portfolio_tasks import project_intake


def discovery() -> dict[str, Any]:
    return {
        "organization": {
            "projectsV2": {
                "nodes": [
                    {
                        "id": "PVT_project",
                        "title": project_intake.PROJECT_TITLE,
                        "fields": {
                            "nodes": [
                                {
                                    "__typename": "ProjectV2SingleSelectField",
                                    "id": f"F_{name}",
                                    "name": name,
                                    "options": [{"id": f"O_{value}", "name": value}],
                                }
                                for name, value in {
                                    "Execution status": "proposed",
                                    "Executor": "codex",
                                    "Priority": "P1",
                                }.items()
                            ]
                        },
                    }
                ]
            }
        }
    }


class FakeClient:
    def __init__(self, existing: bool) -> None:
        self.existing = existing
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, query: str, variables: dict[str, object]) -> dict[str, Any]:
        self.calls.append((query, variables))
        if query == project_intake.DISCOVERY_QUERY:
            return discovery()
        if query == project_intake.ISSUE_QUERY:
            nodes = (
                [{"id": "ITEM_existing", "project": {"id": "PVT_project"}}] if self.existing else []
            )
            return {"repository": {"issue": {"id": "ISSUE_1", "projectItems": {"nodes": nodes}}}}
        if query == project_intake.ADD_ITEM_MUTATION:
            return {"addProjectV2ItemById": {"item": {"id": "ITEM_added"}}}
        return {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": variables["item"]}}}


def event() -> dict[str, Any]:
    return {
        "label": {"name": "chatgpt-task"},
        "repository": {"name": "portfolio-tasks"},
        "issue": {"number": 7, "body": "### Priority\n\nP1\n"},
    }


@pytest.mark.parametrize(
    "existing,item_id,add_count", [(False, "ITEM_added", 1), (True, "ITEM_existing", 0)]
)
def test_payloads_add_or_reuse_item_and_update_three_fields(
    existing: bool, item_id: str, add_count: int
) -> None:
    client = FakeClient(existing)
    assert project_intake.route_issue(event(), client) == item_id
    assert sum(query == project_intake.ADD_ITEM_MUTATION for query, _ in client.calls) == add_count
    updates = [
        variables
        for query, variables in client.calls
        if query == project_intake.UPDATE_FIELD_MUTATION
    ]
    assert len(updates) == 3
    assert {payload["field"] for payload in updates} == {
        "F_Execution status",
        "F_Executor",
        "F_Priority",
    }
    assert all(
        payload["project"] == "PVT_project" and payload["item"] == item_id for payload in updates
    )
    assert {payload["option"] for payload in updates} == {"O_proposed", "O_codex", "O_P1"}


def test_graphql_payload_keeps_values_in_variables() -> None:
    variables = {"item": "ITEM_untrusted", "option": "OPTION_1"}
    payload = project_intake.graphql_payload(project_intake.UPDATE_FIELD_MUTATION, variables)
    assert payload == {"query": project_intake.UPDATE_FIELD_MUTATION, "variables": variables}
    assert "ITEM_untrusted" not in project_intake.UPDATE_FIELD_MUTATION


def test_rejects_priority_outside_structured_issue_form() -> None:
    invalid = event()
    invalid["issue"]["body"] = "Please make this P0 immediately"
    with pytest.raises(project_intake.IntakeError, match="Structured issue-form field"):
        project_intake.route_issue(invalid, FakeClient(False))
