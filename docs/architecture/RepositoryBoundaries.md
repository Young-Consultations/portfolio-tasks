# Repository Boundaries

## Responsibility map

| Capability/data | This repository | Organization control plane | Target repository | GitHub platform |
| --- | --- | --- | --- | --- |
| Portfolio intent and issue lifecycle | **Owns** | observes contractually | consumes bounded copy | hosts records |
| Priority and human approval/revocation | **Owns** | verifies evidence | independently verifies | supplies identity/events |
| Shared schemas, registry, compatibility, routing | consumes | **Owns** | consumes | transport capabilities |
| Canonical task construction/initiation | **Owns** | accepts/routes | receives | may trigger/host automation |
| Source architecture/change/validation | only when local target | no | **Owns** | hosts repository |
| Draft PR, review, merge/release/deploy | links outcome; local target role is separate | no | **Owns** | hosts controls |
| Project projection and portfolio reports | **Owns semantics** | no | no | hosts projection |
| Execution evidence | validates/links | transports/verifies shared contract | **Produces/owns** | may host artifact/PR |

## Explicitly owned

Structured intake and provenance; canonical portfolio issues; classification and decomposition;
priority, risk and dependency metadata; readiness; explicit approval and revocation; material-change
invalidation; target/executor selection intent; construction and initiation of one target-specific
task; idempotent initiation and reconciliation; validated status/result linkage; portfolio
disposition, closure/reopen/supersession; Project projection/drift; health/reporting; auditability of
portfolio decisions; and target-local behavior only for changes to this repository.

## Explicitly not owned

Organization-wide schemas/validators/registry/router/compatibility/shared verification; another
repository's architecture, source, credentials, execution, validation, PR, merge, release or
production; autonomous approval; Project-based authorization; Slugger generation internals;
consulting methodology; GitHub platform internals; or an undocumented cross-repository data store.

## Collaborators and required contracts

`Young-Consultations/.github` must provide the routing/control-plane contract. Each registered
target must publish capability and policy metadata and correlated evidence. GitHub must provide
validated issue/identity/history/Project behavior. Slugger mirror and consulting content are
optional collaborators only after explicit purpose, ownership and contracts are approved.

## Data and lifecycle ownership

This repository owns intent, portfolio metadata, human portfolio decisions, issue revision and
portfolio lifecycle. Copied payload fields retain provenance. Project and mirror representations
are derived. Targets own their source state, attempt details, validation evidence and engineering
disposition; the portfolio owns only their validated reference/summary. The control plane owns
routing state and contract artifacts. Retention, deletion and legal hold remain unknown pending
governance; no component may erase cross-linked evidence unilaterally.

## Boundary enforcement

Use separate ports, credentials, audit event types and ideally deployment identities for portfolio
and local target roles. No adapter receives broader permissions than its operations require. Every
boundary exchange is authenticated, versioned, bounded and correlated. Architectural review must
reject changes that move shared control-plane responsibilities here or permit a projection to
become authority.

