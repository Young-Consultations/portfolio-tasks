# High-Level Project Requirements

## Vision and mission

`portfolio-tasks` is Young Consultations' governed portfolio front door for its AI-assisted SDLC.
Its mission is to turn human intent into structured, prioritized, approval-controlled, routable,
and traceable portfolio work while keeping GitHub Issues authoritative and human beings in control
of priority, authorization, review, merge, and production decisions.

## Business objectives

| ID | Objective | Intended measure |
| --- | --- | --- |
| BO-01 | Make demand understandable and governable before execution. | At least 95% of active executable candidates pass completeness checks; 100% pass before routing. |
| BO-02 | Preserve accountable human decision authority. | 100% of routed tasks have a current, attributable approval; zero executions are authorized by priority or Project state alone. |
| BO-03 | Connect strategy, work, execution evidence, and disposition. | 100% of routed tasks retain a trace from need to target and result; at least 95% of completed tasks record final disposition. |
| BO-04 | Enable safe, bounded AI delivery across repositories. | 100% of handoffs are target-specific, version-compatible, validated, and draft-only when automation publishes changes. |
| BO-05 | Improve portfolio health and learning. | Health, flow, failure, and outcome measures are available for each reporting period; stale and blocked items are visible. |
| BO-06 | Allow repositories and automation to evolve independently. | All cross-repository exchanges use owned, versioned contracts with compatibility and deprecation rules. |

Targets are initial product acceptance targets and SHALL be reviewed after two reporting periods;
changing them requires baseline governance rather than silent operational redefinition.

## Product goals

* Capture requests, provenance, rationale, scope, constraints, risk, dependencies, and outcomes.
* Classify and decompose work into independently governable, target-specific executable units.
* Distinguish prioritization, approval, routing, execution, publication, and final disposition.
* Construct a self-sufficient canonical task for isolated target-repository execution.
* Initiate—not own—organization routing and ingest correlated status and results.
* Project authoritative issue state into planning and reporting views without transferring authority.
* Detect ambiguity, drift, duplication, sensitive content, stale approval, and failed handoffs.

## Users and stakeholders

Primary users are organization owners, software engineering leads, consultants, portfolio/product
managers, repository maintainers, task authors, human approvers, and target-repository owners.
Secondary participants are bounded AI executors, reviewers, auditors, operations/security
stakeholders, and contract owners. A person may hold multiple roles, but role-specific authorities
remain distinct and auditable.

## Business value

The product reduces incomplete demand, unsafe automation, duplicate execution, coordination cost,
and decision ambiguity. It increases leadership leverage, backlog transparency, repeatability,
cross-repository autonomy, audit readiness, and the ability to learn from delivery outcomes.

## Scope

### In scope

Structured intake; canonical issue records; provenance; work classification and hierarchy;
prioritization metadata; target and executor selection; dependency and backlog-health management;
approval, invalidation, and revocation; task construction; routing initiation; execution identity;
result/status ingestion; Project projection and reconciliation; review/disposition visibility;
sensitive-data safeguards; audit history; recovery; reporting; closure, archival, reopening, and
supersession. Target-side execution policy for changes to this repository is in scope only because
`portfolio-tasks` is itself a possible target.

### Out of scope

Organization-wide schema and router ownership; implementation inside other repositories; target
architecture or source ownership; consulting-method content; Slugger generation internals;
autonomous approval; automated readiness, merge, release, or production deployment; replacement
of GitHub Issues as authoritative executable records; and a second organization control plane.

## Success criteria

1. Every routed task has a unique authoritative issue, business or engineering reason, explicit
   target, bounded scope, acceptance evidence expectations, current approval, and correlation ID.
2. Unauthorized edits, absent dependencies, unsafe sensitivity, ambiguity, and incompatible
   contracts fail closed with actionable human-visible explanations.
3. Redelivery neither creates conflicting execution nor multiple publication outcomes.
4. Project drift and result-ingestion failures are detectable and reconcilable.
5. Automated output cannot bypass human review or target-owner authority.
6. Portfolio reporting exposes completeness, age, blockage, flow, outcome, and governance quality.

## Product principles

One authoritative issue; human authority by default; priority is not permission; Projects organize
but do not authorize; structured machine-verifiable metadata; isolated self-sufficient handoffs;
least privilege; fail closed; draft-only automated publication; end-to-end provenance; target-owner
sovereignty; explicit versioned contracts; accessible and actionable human experiences.

## Constraints

* GitHub Issues SHALL remain authoritative for executable work.
* One execution authorization SHALL cover one task and one target repository at a time.
* Cross-repository work SHALL be decomposed and linked.
* Target execution SHALL NOT assume access to portfolio or sibling repositories.
* External contracts, registration, routing, compatibility, and shared verification are owned by
  `Young-Consultations/.github`.
* Automation SHALL NOT approve itself, mark its output ready, merge, or deploy.

## Assumptions

GitHub provides issue, identity, event, Project, and audit primitives; authorized humans and target
owners can be identified; external contract owners will publish compatible contracts; portfolio
work may be retained long enough for audit; and stakeholders will define reporting periods,
retention, service objectives, and regulated-data obligations before production enforcement.

## Risks

| Risk | Product response |
| --- | --- |
| Approval spoofing or stale approval | Structured authority, attribution, invalidation on material change, fail-closed validation. |
| Sensitive information in task context | Prevention guidance, detection, redaction/quarantine, least privilege, incident path. |
| Duplicate or conflicting automation | Stable identity, idempotency, concurrency controls, reconciliation. |
| Project/issue drift | Issue-wins conflict rule, drift visibility, bounded reconciliation. |
| External contract or repository change | Version negotiation, compatibility policy, explicit unknowns, owner validation. |
| Overlarge or cross-target work | Health checks, decomposition, separate approvals, dependency links. |
| Metric gaming | Balanced outcome/governance measures and periodic human review. |
| Platform outage or rate limiting | Durable state, bounded retry, recovery queue, manual intervention. |

## External dependencies

GitHub and GitHub Projects; `Young-Consultations/.github` as contract/control-plane owner;
`Young-Consultations/slugger` as product-generation target/consumer; target repositories and their
owners; `Young-Consultations/consulting-playbook` when consulting knowledge is referenced; approved
AI execution services; identity, secret, and policy administration. Unverified interfaces are
specified in the interface documents and remain external validation dependencies.
