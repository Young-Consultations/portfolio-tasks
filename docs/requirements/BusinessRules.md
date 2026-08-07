# Business Rules

| ID | Rule |
| --- | --- |
| BR-01 | One executable task SHALL have exactly one authoritative issue and one target per active authorization. |
| BR-02 | Issue creation, edit, priority, labels alone, Project placement, or card movement SHALL NOT confer approval. |
| BR-03 | Only a currently authorized human SHALL approve or revoke; automation SHALL NOT approve itself. |
| BR-04 | A material change SHALL invalidate approval, create a new `task_id`, and require renewed human review. |
| BR-05 | Approved work SHALL NOT route while a blocking dependency is unresolved. |
| BR-06 | A cross-target outcome SHALL be decomposed into separately approved, linked target tasks. |
| BR-07 | An executable task SHALL be self-sufficient for a target with no sibling-repository access. |
| BR-08 | Target and executor SHALL be registered/allowed under the externally owned organization contract before handoff. |
| BR-09 | Sensitive, ambiguous, unauthorized, malformed, or incompatible work SHALL fail closed. |
| BR-10 | Priority and ordering SHALL remain human-owned and distinct from execution status. |
| BR-11 | GitHub Project state SHALL be a projection; issue state wins and disagreement SHALL be surfaced. |
| BR-12 | Each routing authorization SHALL have stable correlation and idempotency identities across retries. |
| BR-13 | A repeated delivery SHALL reuse or report the existing outcome and SHALL NOT create conflicting execution or publication. |
| BR-14 | Non-parallel-safe work for the same target SHALL be serialized; parallel-safe declaration does not override target policy. |
| BR-15 | Automated code publication SHALL remain draft-only and SHALL NOT be marked ready, approved, merged, released, or deployed by the executor. |
| BR-16 | Results SHALL be authenticated, contract-valid, correlated, and from an expected source before portfolio state changes. |
| BR-17 | Failure SHALL retain the last authoritative state, evidence, and an actionable recovery path; it SHALL NOT imply success. |
| BR-18 | Closure SHALL record a final disposition or an explicit reason that no delivered outcome exists. |
| BR-19 | Reopened or superseding work SHALL preserve historical identity and links rather than rewrite history. |
| BR-20 | Taxonomy values and lifecycle transitions SHALL be governed, documented, and migration-safe. |
| BR-21 | Human-only and planning-only items MAY remain in the backlog but SHALL NOT pass an AI execution gate. |
| BR-22 | Approver, task author, executor, reviewer, and target owner authorities SHALL remain distinguishable even if one person holds multiple roles. |
| BR-23 | Mirrored external issues SHALL identify their source, managed fields, synchronization direction, and authority. |
| BR-24 | Retention, redaction, and audit access SHALL follow approved organizational policy; absence of policy blocks sensitive-data automation. |
| BR-25 | Only a canonical v2 task with `status: approved` is router authorization. `queued` is a post-admission UI projection and SHALL be rejected at admission; rich approval provenance remains internal and is not added to the closed v2 payload. |
| BR-26 | Pre-acceptance revocation SHALL prevent routing; post-acceptance revocation SHALL request cancellation and preserve the accepted authorization history until an external terminal fact is confirmed. |
| BR-27 | Delivery SHALL be at least once with idempotent visible effects; no issue event, routing delivery, target result, or publication replay may create a second logical effect. |
| BR-28 | Portfolio completion SHALL require consumption of a validated correlated terminal result and visible source-issue evidence; a draft link or missing/ambiguous result alone is insufficient. |

## Validation and lifecycle policy

Readiness requires a reason, objective, type, target, executor, risk, scope, dependencies,
constraints, required behavior, acceptance criteria, evidence expectations, sensitivity decision,
and provenance. Valid states and transitions SHALL distinguish at minimum proposed, approved,
queued, executing, blocked/failed, draft output, done, cancelled, and superseded. Exact labels and
representations are configuration, not product semantics. Invalid transitions SHALL be rejected
with current state, violated rule, and permitted human action.

## Governance and synchronization policy

Changes to authority, required fields, state semantics, routing eligibility, or external contracts
require designated owner review and migration impact assessment. Synchronization SHALL declare
field-level direction: authoritative-to-projection, externally authoritative result-to-portfolio,
or human reconciliation. Last-write-wins SHALL NOT resolve authority conflicts.
