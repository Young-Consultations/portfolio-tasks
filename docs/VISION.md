# Young Consultations AI-SDLC Vision

## Organization Vision

Young Consultations is building a governed AI-assisted software development operating system that turns human intent into approved, traceable, and reviewable software delivery. GitHub serves as the system of record for portfolio decisions, engineering work, execution evidence, and human approval. Specialized repositories collaborate through explicit versioned contracts so that planning, governance, AI execution, product generation, and consulting knowledge can evolve independently without sacrificing safety, accountability, or architectural coherence.

This system increases the leverage of a software leader, consultant, or small engineering team
throughout the professional software development lifecycle. Human intent becomes structured and
governed before AI execution. GitHub Issues are the authoritative records for executable portfolio
work; GitHub Projects may organize and report that work but cannot silently become another
execution control plane. AI may analyze and implement approved work, while humans retain priority,
approval, review, merge, and production authority. Repositories collaborate through explicit
contracts, not implicit shared state.

## Desired Organization Workflow

The desired end-to-end flow is:

> Human intent
> → structured portfolio task
> → prioritization and governance metadata
> → explicit approval
> → canonical task construction
> → organization routing
> → bounded target-repository execution
> → validation and evidence
> → draft pull request
> → human review and merge
> → portfolio outcome reporting

Each transition must preserve provenance and decision authority. In particular, intake and
prioritization do not imply approval, routing does not imply permission to merge, and execution
does not transfer engineering ownership away from the target repository.

## Organization Repository Model

The following definitions are architectural context for this vision. They are not assertions based
on inspection of repositories other than `portfolio-tasks`.

* **`Young-Consultations/.github`** owns organization-wide contracts, schemas, repository
  registration, routing, compatibility policy, and shared verification.
* **`Young-Consultations/portfolio-tasks`** owns structured portfolio intake, backlog governance,
  prioritization metadata, approval state, planning visibility, and initiation of approved
  execution.
* **`Young-Consultations/slugger`** owns the AI Software Factory product and controlled
  software-project generation.
* **`Young-Consultations/consulting-playbook`** owns reusable consulting methods, assessments,
  decision frameworks, and delivery playbooks.

These boundaries permit independent evolution without moving shared routing or contract ownership
into this repository.

## Vision for portfolio-tasks

Young-Consultations/portfolio-tasks is the governed portfolio front door for the organization’s AI-assisted software development lifecycle. It converts human intent into structured, prioritized, traceable work; preserves explicit human approval; and initiates authorized execution without owning shared cross-repository contracts. It may also be an execution target through a separately bounded adapter that has no approval or router-bypass authority.

Its long-term direction is the organization’s portfolio operating layer: a dependable system for
backlog health, strategic alignment, work decomposition, approval, routing readiness, execution
visibility, and outcome learning. It must not become a second organization control plane or a
substitute for target-repository engineering ownership.

## Repository Purpose

The repository exists to help the organization decide what work should be done, why it matters,
where it belongs, who or what may execute it, and whether execution has been explicitly approved.

A software leader or consultant should be able to capture a business need, product idea, defect,
technical risk, or consulting recommendation as structured portfolio work. The repository should
make that work understandable, governable, prioritizable, routable, and traceable through
completion. This is a desired experience, not a claim that every capability is implemented today.

## Primary Users and Stakeholders

The vision serves these roles without presuming unsupported personas or research findings:

* **Organization owner:** sets organizational direction and retains ultimate governance authority.
* **Software engineering lead:** assesses engineering value, feasibility, risk, and sequencing.
* **Consultant:** translates client or advisory needs into appropriately contextualized work.
* **Portfolio or product manager:** organizes demand, priority, dependencies, and outcomes.
* **Repository maintainer:** safeguards this repository's intake, governance, and initiation
  mechanisms.
* **Task author:** records human intent and supplies the context needed for governance.
* **Human approver:** makes and, when necessary, revokes explicit execution decisions.
* **Target-repository owner:** retains authority over target architecture, review, merge, and
  delivery.
* **Bounded AI executor:** implements only authorized work within the target repository and supplied
  context.
* **Reviewer or auditor:** evaluates decisions, evidence, traceability, and policy conformance.

One person may perform several roles, but the associated decisions and authorities remain distinct.

## Portfolio Work Model

Requirements development may refine this vision-level hierarchy:

> Strategic objective
> → epic or major outcome
> → feature or capability
> → story, task, defect, risk, or research item
> → approved executable task
> → execution result
> → delivered outcome

The hierarchy connects intent to delivery while allowing work to be decomposed until an executable
task is bounded, target-specific, and sufficiently contextualized. GitHub issue and sub-issue
capabilities may represent this model, but this vision does not mandate a particular implementation
for every hierarchy level. An approved executable task has one authoritative issue record; higher
or lower levels may require different representations after requirements analysis.

## Repository Responsibilities

The repository owns the portfolio-facing responsibility for:

* structured work intake;
* canonical portfolio issue records;
* business and engineering context for requested work;
* target-repository selection;
* priority, severity, type, and lifecycle metadata;
* decomposition into epics, features, stories, tasks, defects, or risks;
* human approval state;
* executor selection;
* initiation of approved routing;
* portfolio reporting and synchronization;
* visibility into execution outcomes; and
* backlog health and traceability.

Ownership here defines the intended portfolio boundary. Proposed or partially implemented
capabilities remain subject to requirements, contract compatibility, and verified implementation.

## Explicit Non-Responsibilities

The repository does not own:

* organization-wide contract schemas;
* shared router implementation;
* target-repository source changes;
* autonomous approval;
* direct merging;
* product-specific architecture;
* consulting methodology content; or
* Slugger's software-generation internals.

It initiates authorized routing but does not absorb organization routing responsibilities, execute
another repository's changes, or supersede a target-repository owner's decisions.

## Guiding Principles

* **One authoritative issue record for executable work.** Mirrors, views, artifacts, and pull
  requests must retain a clear link to that record and must not compete with it.
* **Human approval is explicit and separate from issue creation.** Capturing intent is not execution
  authorization.
* **Prioritization and execution authorization are different decisions.** High priority alone cannot
  dispatch work.
* **Projects organize; issues authorize.** GitHub Projects report and organize authoritative work
  but do not independently authorize execution.
* **Routing metadata is structured and machine-verifiable.** Authorization cannot depend on
  inference from arbitrary prose or project-card placement.
* **Tasks are self-sufficient at the execution boundary.** Context must be sufficient for a target
  repository that lacks cross-repository access.
* **Sensitive or ambiguous work fails closed.** Missing authority, uncertain scope, or unsafe
  content stops automated progress pending human resolution.
* **Automated changes remain draft-only.** Humans decide whether changes advance to merge and
  production.
* **Portfolio state is traceable to execution evidence.** Results and final disposition remain
  connected to their approved source.
* **Backlog structure supports strategy and healthy decomposition.** Work should connect to a need
  and be decomposed into governable, target-specific units.

## Measures of Vision Success

The vision is successful when these outcomes are observable:

* work can be traced to a strategic, customer, consulting, operational, or engineering need;
* approved tasks contain enough context for isolated target execution;
* unauthorized issue edits cannot trigger execution;
* portfolio and project views accurately reflect authoritative issue state;
* duplicate or conflicting execution is prevented or visibly detected;
* task outcomes feed back into portfolio state;
* backlog health can be assessed from structured metadata;
* requirements can be derived without redefining repository purpose; and
* every executable task has sufficient context, a known business or engineering reason, an explicit
  target, clear governance metadata, a human approval decision, and traceability through execution
  result and final disposition.

These are outcome statements. Detailed measures, thresholds, and acceptance criteria belong to
requirements and verification work.

For the next MVP, vision success is narrowed to one revision-bound, human-approved issue routed to
exactly one of the four candidate targets, followed by target validation, exactly one created or
reused draft PR, and a correlated terminal result visible on the source issue. Continuous CI must
prove the same lifecycle with deterministic substitutes and no Codex invocation, real branch, or
real pull request. The repository release selection and external blockers are defined in
[`releases/next-mvp.md`](releases/next-mvp.md).

## Constraints and Guardrails

* Humans retain priority, approval, review, merge, and production authority.
* Issue creation, editing, priority, or project placement cannot alone authorize execution.
* Organization-wide schemas, registration, shared routing, compatibility policy, and shared
  verification remain outside this repository.
* A target repository owns its architecture, source changes, validation policy, and disposition of
  its pull requests.
* Cross-repository interactions use explicit, versioned contracts and least-privilege boundaries;
  target execution cannot assume access to portfolio or sibling repositories.
* Execution must fail closed when approval, identity, target, context, sensitivity, or contract
  validity is uncertain.
* Automation may publish a draft pull request and evidence, never approve itself, mark work ready,
  merge, or deploy to production.
* Proposed future capabilities in this document are not statements of present behavior. The issue
  form, workflows, and applicable contracts remain authoritative for implemented behavior.

The present repository contains both portfolio initiation mechanisms and a target-side Codex
workflow for changes to `portfolio-tasks` itself. That target-side role does not make this repository
the organization router or the executor for other repositories. It is an implementation-boundary
distinction to preserve during requirements development.

## Relationship to GitHub Projects

GitHub Issues in `portfolio-tasks` are the authoritative portfolio and executable-task records.
GitHub Projects are projections that organize and report those records for triage, prioritization,
planning, execution visibility, and outcome review. Project fields may mirror authoritative issue
metadata, and automation may synchronize them, but project values, views, card movement, and
project automation must not independently authorize routing or execution.

Current documentation describes both manual Phase 1 mirroring and optional or event-driven
synchronization mechanisms. That operational variation does not alter the authority boundary:
disagreement must be surfaced and reconciled to the issue rather than silently treating a Project
value as execution truth. Requirements development must clarify synchronization direction,
freshness, conflict handling, and operating-phase terminology without turning Projects into an
alternate control plane.

## Transition to Requirements Development

The next phase will define detailed requirements; this document intentionally does not define
shall-statements, user stories, schemas, acceptance criteria, or implementation designs. Traceability
will follow this hierarchy:

> Organization vision
> → portfolio capabilities
> → repository constraints
> → functional requirements
> → non-functional requirements
> → external interface requirements
> → data and metadata requirements
> → workflow-state requirements
> → verification criteria
> → backlog implementation work

Requirements development will cover these capability areas:

| Capability area | Scope for requirements analysis |
| --- | --- |
| Work intake | Ways to capture intent, context, provenance, and an initial governance state. |
| Work classification | Consistent portfolio types, lifecycle categories, risks, and other classification dimensions. |
| Hierarchy and decomposition | Relationships from strategic intent to bounded executable work and delivered outcomes. |
| Prioritization | Decision inputs, ordering, ownership, and distinction from execution authorization. |
| Backlog health | Completeness, age, dependencies, decomposition quality, and actionable-state visibility. |
| Target-repository selection | Valid target identification, ownership checks, and target-specific boundaries. |
| Executor selection | Allowed executor identities, suitability, authority, and human-only paths. |
| Approval and revocation | Explicit human decisions, freshness, edit invalidation, revocation, and authority. |
| Canonical task construction | Assembly of complete, bounded, target-usable instructions from authoritative context. |
| Routing initiation | Preconditions and the controlled handoff from portfolio approval to organization routing. |
| Execution identity and idempotency | Stable identities, replay behavior, concurrency boundaries, and duplicate detection. |
| Status and result ingestion | Contracted receipt, correlation, validation, and portfolio application of execution evidence. |
| GitHub Projects synchronization | Issue-to-Project projection, freshness, error visibility, and conflict behavior. |
| Human review workflow | Review, disposition, merge authority, rejection, and feedback to portfolio state. |
| Sensitive-data handling | Identification, redaction, access boundaries, retention, and fail-closed handling. |
| Auditability | Durable provenance for intent, metadata, approval, routing, execution, and disposition. |
| Failure recovery | Safe retry, reconciliation, revocation, partial-failure handling, and manual intervention. |
| Reporting and metrics | Portfolio flow, outcome, health, traceability, and governance reporting needs. |
| Archival and closure | Final disposition, retention, reopened work, supersession, and historical traceability. |

The requirements phase must reconcile current intake fields, deterministic labels, workflow state,
Project synchronization, Slugger issue mirroring, shared execution contracts, and target-side
execution behavior against this vision. Existing implementation informs that analysis but cannot
redefine the purpose or repository boundaries stated here.

## Vision Assumptions Requiring Validation

These assumptions guide requirements discovery; none is a substitute for validated requirements or
cross-repository verification.

| Assumption | Architectural impact | Requirements-phase validation method |
| --- | --- | --- |
| GitHub Issues remain the source of truth for executable portfolio work. | Preserves one canonical task and governance record and determines where conflicts are resolved. | Review stakeholder authority decisions and trace current in-repository state transitions from intake through result. |
| GitHub Projects are projections of issue state. | Keeps planning and reporting separate from authorization and requires detectable synchronization drift. | Map each Project field and automation to its issue source; define and review conflict and freshness scenarios. |
| Approval requires explicit structured state. | Prevents creation, prose, priority, or project placement from implicitly authorizing execution. | Identify authorized approvers and decision events; exercise edit, revocation, and stale-approval scenarios against current gates. |
| Target repositories execute their own changes. | Keeps source, architecture, validation, and publication within the owning repository boundary. | Validate the intended handoff and responsibility model with target owners through organization contract and interface review. |
| One task targets one repository execution at a time. | Provides a bounded authorization, concurrency, and idempotency unit. | Model retry and concurrency cases and review whether any legitimate task requires simultaneous multi-target authorization. |
| Cross-repository tasks are decomposed into separate target-specific tasks. | Allows isolated context, approval, evidence, and ownership for each target while preserving parent traceability. | Walk representative cross-repository scenarios with stakeholders and assess decomposition and dependency links. |
| Draft pull requests are the automated publication boundary. | Reserves readiness, merge, and production decisions for humans. | Review publication states and exception scenarios with repository owners and verify target policy expectations. |
| Execution results are returned through organization contracts. | Requires versioned result identity, evidence, compatibility, and portfolio ingestion interfaces. | Review the applicable organization interface contracts with their owners during requirements work and test representative result lifecycles. |
