# Low-Level Design

## Logical module map

| Module | Public responsibility | Internal collaborators |
| --- | --- | --- |
| `intake` | Capture and amend structured requests | provenance, normalization, sensitivity policy |
| `catalog` | Resolve governed taxonomy, target, executor and contract capabilities | configuration, registries |
| `portfolio` | Load/save the Portfolio Work aggregate | hierarchy and dependency policies |
| `governance` | Evaluate readiness; record priority, approval, revocation | actor policy, revision digest, clock |
| `tasking` | Build/validate canonical task envelopes | catalog, contract codec, redactor |
| `routing` | Initiate and correlate a controlled handoff | idempotency, control-plane port, audit |
| `outcomes` | Ingest acceptance/status/result/disposition | ordering, signature/identity validation |
| `reconciliation` | Resolve uncertain, duplicate, stale and conflicting facts | task records, external status query |
| `projects` | Project authoritative fields and repair drift | mapping policy, GitHub Project port |
| `reporting` | Query health, flow, outcome and governance measures | read model, metric definitions |
| `target_gateway` | Enforce this repository's target-local execution contract | executor port, evidence validator |
| `assurance` | Audit events, telemetry, health and diagnostic export | redaction and correlation |

Names are conceptual namespaces, not required package names.

## Application interfaces

Commands express intent and return a decision/result object; they do not expose adapter exceptions.

| Use case | Required input | Result |
| --- | --- | --- |
| CaptureWork | actor, provenance, structured intent, request ID | work identity, revision, violations |
| AmendWork | identity, expected revision, patch, actor | new revision, approval impact, violations |
| EvaluateReadiness | identity/revision | deterministic violations and required actions |
| RecordApproval / RevokeApproval | actor, current task identity, reason | recorded decision or denial |
| InitiateRouting | identity, expected revision, request ID | accepted/rejected/ambiguous plus correlation |
| ApplyExecutionEvent | authenticated envelope | applied/duplicate/stale/conflict/quarantined |
| ReconcileHandoff | correlation or work identity | verified state and permitted next action |
| SynchronizeProjection | identity/version | updated/no-op/drift/conflict |
| QueryPortfolio | filters, pagination, viewer | accessible read model with freshness |

## Domain policies and internal interfaces

* `ReadinessPolicy` returns all violations for completeness, dependency, sensitivity, target,
  executor, contract, approval eligibility, and bounded scope.
* `MaterialChangePolicy` classifies a change and invalidates approval before any later effect.
* `AuthorizationPolicy` evaluates attributable actor capability and optional separation of duties.
* `TaskIdentityPolicy` derives stable task, attempt, delivery and correlation identities.
* `TransitionPolicy` is the sole authority for lifecycle transitions.
* `EventOrderingPolicy` rejects impossible transitions, ignores exact duplicates, and quarantines
  divergent payloads or unknown identities.
* `ProjectionMappingPolicy` maps only declared issue-owned fields and never maps Project approval
  into the aggregate.

Policies accept value objects and configuration snapshots and return explicit decisions. They have
no I/O, ambient time, global state, or hidden network calls.

## Ports

| Port | Semantic operations |
| --- | --- |
| WorkRecord | read at revision; compare-and-set transition; history/provenance |
| Identity & Authorization | authenticate actor/service; evaluate governed role evidence |
| Clock & ID | deterministic/testable time and stable identifiers |
| Contract Catalog | supported versions, target/executor capabilities; validate envelope |
| Routing | submit command; query by identity; receive verified receipt/status/result |
| Idempotency | reserve identity+digest; read outcome; finalize/mark uncertain |
| Project Projection | read/apply mapping; report drift/freshness |
| Evidence | append immutable decision/effect record; retrieve with access controls |
| Telemetry | structured events, metrics, trace context and health |
| Local Executor | validate, execute within workspace, collect evidence, publish draft once |

## Transaction and concurrency boundaries

A portfolio transition atomically updates the authoritative record and appends an outbox/audit
intent, or leaves both unchanged. If GitHub cannot provide that atomicity, the adapter must expose
the gap and reconciliation must close it; it must not report success prematurely. Stable identity
plus semantic payload digest prevents divergent replays. A lock or compare-and-set boundary is per
task and effect type; locks must expire safely and be observable.

## Extension points

New intake channels, taxonomy versions, Project mappings, contract codecs, reporting exporters,
targets, and executors implement ports and pass conformance suites. Extensions cannot add a second
approval source, bypass sensitivity/readiness, require target access back to the portfolio, or
publish beyond draft.

## Test seams

Every policy supports table-driven unit tests. Each adapter has consumer/provider contract tests.
Workflow tests inject clocks, identities, duplicate/out-of-order events, transient failures and
payload conflicts. End-to-end tests prove authority separation, draft-only publication,
reconciliation, accessibility and redaction.

