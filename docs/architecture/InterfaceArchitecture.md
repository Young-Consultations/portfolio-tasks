# Interface Architecture

## Universal contract rules

Every machine interface shall declare owner, semantic/schema version, identity and correlation,
authentication context, timestamps, size limits, validation rules and outcome categories. Inputs
are untrusted. Validation covers syntax, semantics, authority, revision, compatibility, sensitivity
and target policy. Additive compatible changes use a minor version; breaking semantic/schema
changes use a major version with an owner-published overlap and deprecation plan. Unknown major
versions fail closed.

Retries are bounded with backoff/jitter and only for explicitly transient outcomes. The same retry
uses the same idempotency identity and semantic digest. `accepted`, `rejected`, `conflict`,
`duplicate`, `transient-failure`, `permanent-failure`, and `ambiguous` are distinguishable; no raw
exception is a contract.

## Interface catalogue

| Interface / owner | Responsibilities and contract | Inputs → outputs | Failure, retry, idempotency |
| --- | --- | --- | --- |
| Structured Intake / portfolio | Capture intent, provenance and initial non-approved state | actor, source, rationale, scope, target, criteria, metadata → work ID/revision/violations | invalid/unsafe quarantined; client request ID deduplicates; no automatic retry of user corrections |
| Work Amendment / portfolio | Apply patch against expected issue revision and invalidate stale approval | work ID, revision, actor, patch → revision/materiality/violations | revision conflict requires reread; identical request replay is no-op |
| Governance Command / portfolio | Priority, approve, revoke, close/reopen/supersede by authorized human | actor authority, work/revision, decision, reason → evidence/state | deny unknown actor/stale revision; never retry with changed content; decision ID idempotent |
| Readiness Query / portfolio | Explain every current gate | work/revision, viewer → violations, next actions, policy version | pure/repeatable for snapshot; staleness explicit |
| Project Projection / portfolio↔GitHub | Write declared issue-owned fields; read drift/freshness | issue snapshot + mapping version → no-op/updated/drift/error | bounded quota-aware retry; identity is issue+project+mapping+revision; Project input cannot approve |
| Canonical Routing Submission / **control-plane owner** | Accept versioned self-sufficient task for registered route | envelope described below → authenticated receipt/rejection/ambiguity | stable delivery ID+digest; query before retry after uncertainty; divergent replay conflicts |
| Routing Status Query / **control-plane owner** | Resolve known delivery/correlation without starting work | delivery/correlation ID → authoritative known/unknown/status/retry-safety | read retry allowed; `unknown` is not proof no effect occurred unless contract guarantees it |
| Execution Event Ingress / **control-plane owner produces; portfolio consumes** | Deliver acceptance, ordered status, terminal result and optional disposition | authenticated event envelope → portfolio acknowledgement | event ID+digest dedup; invalid/unknown quarantined; out-of-order policy explicit |
| Target Execution / **target owner** | Independently validate and execute a routed task | routed canonical task → accept/reject, status, evidence/result, max one draft reference | target policy controls safe retry/concurrency; same delivery cannot cause duplicate publication |
| Optional Slugger Mirror / jointly validated, Slugger owns target | Non-authoritative managed copy with provenance | source/revision, managed fields, lifecycle intent → mirror ref/sync result | at most one active mirror; conflicts fail closed; failure never changes approval/execution |
| Optional Consulting Reference / playbook owner | Resolve approved non-sensitive method content if integration is enabled | stable versioned reference → authorized excerpt/metadata | unavailable/withdrawn reference blocks dependent readiness; no content invented |
| Reporting Query/Export / portfolio | Authorized accessible portfolio insight and audit drill-down | filters, period, viewer, page → measures + definitions + freshness | throttled/paginated; unknown differs from zero; request identity for long exports |
| Operations/Admin / portfolio | Reconcile, activate config, inspect quarantine without bypassing policy | authorized command + reason → auditable outcome | privileged, separation-of-duty configurable; repeat operation idempotent |
| Local Target Workflow / portfolio-tasks target owner | Apply shared plus local policy for this repository | control-plane task → status/result/draft reference | logically separate credentials; never implies portfolio approval |

## Frozen next-MVP interface profile

The authoritative schemas and workflows are consumed directly from
`Young-Consultations/.github@c6090e5bbadcc2102a1cb91875466e9decdada1e` as detailed in
[`../requirements/Interface-OrganizationControlPlane.md`](../requirements/Interface-OrganizationControlPlane.md).
The router accepts required `task_payload`, explicitly supplied `execution_mode`, and
`CODEX_ROUTER_TOKEN`; its outputs are `execution_result`, `correlation_id`, `delivery_id`,
`failure_category`, `diagnostic_summary`, and `concurrency_group`. The target adapter accepts only
`execution_input_json` and `concurrency_group`. The separate result receiver accepts
`execution_result`, `source_issue`, and `CODEX_RESULT_TOKEN`, and exposes `accepted`, `delivery_id`,
`correlation_id`, `execution_status`, `failure_category`, and `diagnostic_summary`.

Canonical field completeness is defined only by the three pinned closed schemas. Architecture
summaries do not recreate or extend them. Only `status: approved` can cross router admission;
`queued` is a post-admission projection. Rich approval provenance stays internal. Material edits
create a new `task_id` and require new approval.

## Event/result minimum contract

Events contain event identity/type/version, delivery/task/attempt correlation, producer identity,
target, monotonic ordering information, producer time and authenticated integrity evidence. A
terminal result includes outcome, target revision/branch when applicable, checks actually run and
their outcomes, safe diagnostics, evidence references, retry-safety, timestamps and zero or one
draft publication reference. Missing evidence is `not supplied`, never success.

## Ownership and validation register

Release `2.2.0`, payload version `ai-sdlc-contract/v2`, target capability semantics, workflow
signatures, schema locations, result-receiver contract, and complete executable fixture oracle are
frozen at the compatibility SHA. Current target activation is separate mutable control-plane state
that the router enforces before dispatch; it is not target-side compatibility policy. Normal CI
uses the organization fixtures with deterministic local doubles and asserts no Codex call, real
branch, or real PR.
