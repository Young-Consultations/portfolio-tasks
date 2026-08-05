from dataclasses import dataclass, field

from portfolio_tasks.execution import publication_preflight_decision
from portfolio_tasks.idempotency import (
    CONTRACT_VERSION,
    DeliveryIdentity,
    deterministic_branch,
    publication_marker,
)


@dataclass
class FakeSystem:
    router_invocations: int = 0
    target_dispatches: int = 0
    codex_invocations: int = 0
    branch_writes: int = 0
    pr_creations: int = 0
    terminal_source_updates: int = 0
    markers: dict[str, DeliveryIdentity] = field(default_factory=dict)
    branches: set[str] = field(default_factory=set)
    prs: list[dict[str, object]] = field(default_factory=list)

    def identity(
        self, issue: int = 42, delivery_id: str = "portfolio-delivery/task-redeliver01"
    ) -> DeliveryIdentity:
        return DeliveryIdentity(
            contract_version=CONTRACT_VERSION,
            source_issue=f"Young-Consultations/portfolio-tasks#{issue}",
            task_id="task-redeliver01",
            delivery_id=delivery_id,
            target_repository="Young-Consultations/portfolio-tasks",
            requested_branch=deterministic_branch(delivery_id),
        )

    def route(self, ident: DeliveryIdentity, lose_ack: bool = False) -> None:
        self.markers.setdefault(ident.source_issue, ident)
        self.router_invocations += 1
        self.target_dispatches += 1
        self.target(ident)
        if not lose_ack:
            self.terminal_source_updates += 1

    def target(self, ident: DeliveryIdentity) -> str:
        pulls = [pr for pr in self.prs if pr["head"] == ident.requested_branch]
        decision = publication_preflight_decision(
            publication_key=f"{ident.target_repository}:{ident.requested_branch}",
            pulls=pulls,
            branch_exists=ident.requested_branch in self.branches,
            identity=ident,
        )
        if decision["preflight_outcome"] == "reuse-completed-delivery":
            self.terminal_source_updates += 1
            return "reused"
        self.codex_invocations += 1
        self.branches.add(ident.requested_branch)
        self.branch_writes += 1
        self.prs.append(
            {
                "state": "open",
                "draft": True,
                "html_url": "https://github.com/Young-Consultations/portfolio-tasks/pull/1",
                "head": ident.requested_branch,
                "body": publication_marker(ident, "completed"),
            }
        )
        self.pr_creations += 1
        self.terminal_source_updates += 1
        return "created"


def test_duplicate_and_lost_ack_redelivery_create_one_publication() -> None:
    fake = FakeSystem()
    ident = fake.identity()
    fake.route(ident, lose_ack=True)
    fake.route(ident)
    fake.route(ident)
    assert fake.target_dispatches == 3
    assert fake.codex_invocations == 1
    assert fake.branch_writes == 1
    assert fake.pr_creations == 1
    assert len(fake.branches) == 1
    assert fake.terminal_source_updates >= 1


def test_payload_conflict_and_ambiguous_state_fail_before_codex() -> None:
    fake = FakeSystem()
    ident = fake.identity()
    fake.prs = [
        {
            "state": "open",
            "draft": True,
            "html_url": "u1",
            "head": ident.requested_branch,
            "body": publication_marker(ident, "completed"),
        },
        {
            "state": "open",
            "draft": True,
            "html_url": "u2",
            "head": ident.requested_branch,
            "body": publication_marker(ident, "completed"),
        },
    ]
    try:
        fake.target(ident)
    except ValueError as exc:
        assert "found 2 open pull requests" in str(exc)
    assert fake.codex_invocations == 0
    assert fake.pr_creations == 0
