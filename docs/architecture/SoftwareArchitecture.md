# Software Architecture Overview

## Executive summary

`portfolio-tasks` is the governed portfolio front door for the Young Consultations AI-assisted
SDLC. It owns the authoritative portfolio issue, structured intent, prioritization metadata,
approval state, routing initiation, outcome linkage, and planning projections. It deliberately
does **not** own organization contracts or routing, target implementation, merge, release, or
production. This architecture defines the desired system; `docs/VISION.md`, then the requirements
baseline, take precedence over it, and all three take precedence over current code.

## Architectural vision and goals

Human intent becomes a complete, target-specific, explicitly approved command whose provenance can
be followed through execution evidence and human disposition. The system shall:

1. keep one issue authoritative and Projects derivative;
2. separate prioritization, approval, routing, execution, and disposition authorities;
3. fail closed on ambiguity, stale consent, sensitivity, identity, or compatibility;
4. make retries deterministic and reconciliation explicit;
5. allow targets and the organization control plane to evolve through versioned contracts; and
6. give humans and AI agents complete, machine-readable context and actionable diagnostics.

## Design principles

| Principle | Architectural consequence |
| --- | --- |
| Clean boundaries | Domain policy has no dependency on transport, GitHub, storage, or executor. |
| Authority before automation | Every effect is gated by current issue revision and attributable human approval. |
| Commands, not shared state | Cross-repository work uses immutable, versioned payloads and correlated results. |
| At-least-once safe | Stable identity, payload digest, idempotency records, and reconciliation absorb replay. |
| Target sovereignty | Target policy independently authorizes execution and humans own PR disposition. |
| Evidence over assertion | State changes cite actor, time, source revision, contract, and evidence. |
| Accessible transparency | Human views explain state, blockers, authority, and next action without color alone. |
| Configuration as policy | Taxonomy and rules are versioned, validated, reviewable, and fail closed. |

## Guiding constraints

GitHub Issues are the system of record; Projects cannot authorize. One authorization addresses one
target repository. Targets require no read access to this repository. Automation can create at
most a draft publication and cannot approve itself, mark ready, merge, release, or deploy.
Organization contracts, registries, router, compatibility, and shared verification remain owned by
`Young-Consultations/.github`. Unknown external behavior is a validation dependency, not a design
license.

## Quality attributes

| Attribute | Design response |
| --- | --- |
| Security | Least privilege, explicit trust boundaries, authenticated actors/messages, redaction, fail-closed gates. |
| Reliability | Durable transitions, idempotency, ordering rules, bounded retry, reconciliation and recovery queues. |
| Maintainability | Ports/adapters, cohesive policy services, versioned contracts, ADRs and traceability. |
| Testability | Pure policy decisions, contract fixtures, clocks/identities as ports, conformance suites. |
| Scalability | Stateless processors, partitioning by canonical task, quotas, backpressure and batch projections. |
| Observability | Correlation IDs, structured audit events, metrics, traces, safe diagnostics and health signals. |
| Interoperability | Canonical semantic model, explicit versions, capability negotiation and deprecation windows. |
| Usability/accessibility | Actionable validation, progressive intake, keyboard/assistive access, nonvisual status cues. |

## Architectural style

The desired design is a modular system using hexagonal/clean architecture and event-informed
workflow orchestration. A domain core expresses portfolio invariants. Application use cases
coordinate ports. Adapters integrate GitHub and the external control plane. Read models provide
projections and reports. Durable workflow state is logically distinct from the canonical issue but
never supersedes it.

## System and repository responsibilities

Owned: intake, canonical portfolio records, provenance, taxonomy, decomposition, readiness,
priority, approval/revocation, canonical task construction, routing initiation, reconciliation,
validated result application, Project projection, health/reporting, and this repository's own
target-side workflow. Not owned: shared schemas/router/registry, other repositories' source and
policy, consulting content, Slugger internals, approval inference, merge, or production.

## Major components

| Component | Responsibility |
| --- | --- |
| Intake & Classification | Capture, normalize, classify sensitivity, validate and preserve provenance. |
| Portfolio Domain | Aggregate rules for hierarchy, dependency, lifecycle and authority. |
| Governance | Readiness, prioritization, approval, revocation and revision binding. |
| Task Builder | Produce self-sufficient immutable canonical task envelopes. |
| Routing Initiator | Validate final gates and submit once through the control-plane port. |
| Result & Reconciliation | Order and authenticate outcomes; resolve uncertain handoffs safely. |
| Projection & Reporting | Maintain non-authoritative Projects/read models and expose drift/health. |
| Target-Side Execution Gateway | For this repository only: local policy, bounded execution evidence and draft publication. |
| Audit & Observability | Correlated decision records, telemetry and operational diagnostics. |

## Architectural decisions

The decision set in `ADR.md` establishes authoritative Issues, clean boundaries, explicit state
machines, revision-bound approval, immutable versioned envelopes, idempotent effects, derivative
projections, target sovereignty, and fail-closed security. These decisions are normative unless a
superseding ADR updates requirements traceability.

## Risks and technical debt assessment

| Risk/debt | Impact | Required treatment |
| --- | --- | --- |
| External contracts and identities are unverified | Unsafe routing | Disable integration until owner conformance evidence exists. |
| Current labels/forms/workflows may encode policy implicitly | Drift and unauthorized transitions | Move semantic policy behind validated ports; migrate with parity tests. |
| Current Project/manual sync variants | Conflicting state | Declare issue authority, measure drift, reconcile explicitly. |
| Local implementation combines portfolio and target roles | Privilege confusion | Separate deployment identities, ports, audit categories, and ownership. |
| GitHub history/retention capability is uncertain | Incomplete audit | Validate WA-01; add a governed evidence store only if approved. |
| Slugger mirror value and contract are uncertain | Accidental coupling | Keep optional and disabled until WA-07 and ownership mapping are approved. |
| Business/security/operations owners and thresholds unknown | Incomplete policy | Treat affected features as configuration blocked, not silently defaulted. |

## Future evolution strategy

Deliver in capability slices: (1) canonical model and governance parity, (2) revision-bound
approval and deterministic task building, (3) contracted routing/result reconciliation, (4)
Projects drift management and reporting, and (5) independently validated target onboarding.
Each slice requires contract tests, migration/reversal, audit coverage, threat review, accessibility
evidence, and traceability updates. New transports, targets, executors, taxonomies, and reporting
sinks enter through ports; none may weaken issue authority or human decision gates.

