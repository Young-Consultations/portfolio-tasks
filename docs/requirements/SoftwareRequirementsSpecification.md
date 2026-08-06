# Software Requirements Specification

## 1. Introduction

### 1.1 Purpose

This SRS defines the externally observable product requirements for `portfolio-tasks` so that
architecture, UX, data, API, testing, AI-agent, migration, and rewrite work can proceed without
depending on the current implementation. Normative details reside in the linked requirement and
interface documents.

### 1.2 Definitions and conventions

Terms are authoritative in [Glossary.md](Glossary.md). RFC 2119 terms are normative. A requirement
is satisfied only when every listed acceptance criterion and linked mandatory nonfunctional
requirement is verified. The vision takes precedence over current code and legacy operations.

### 1.3 Scope

The system is a portfolio operating layer spanning intake through outcome reporting. It governs
whether work is ready and approved, initiates a controlled handoff, observes outcomes, and
preserves authority. It is not the organization router and does not implement or accept changes on
behalf of target owners.

## 2. Product overview

The system receives human intent, creates a canonical issue, supports classification,
decomposition and prioritization, validates readiness, records explicit approval, constructs a
self-sufficient task, initiates organization routing, ingests evidence, synchronizes reporting
projections, and records human disposition. Trust boundaries exist between humans and automation,
issue authority and Project projections, portfolio and control plane, control plane and target,
executor and target owner, and raw external evidence and portfolio state.

### 2.1 User classes

| Class | Needs and authority |
| --- | --- |
| Task author / consultant | Clear intake, context capture, validation feedback; no implicit approval. |
| Portfolio/product manager | Classification, decomposition, ordering, dependencies, health, reporting. |
| Organization owner / engineering lead | Strategy, governance policy, exception and risk oversight. |
| Human approver | Readiness evidence, diff of material content, approve/revoke controls. |
| Repository maintainer | Product operation, configuration, recovery, target-local policy. |
| Target owner / reviewer | Self-sufficient task, evidence, architecture/review/disposition authority. |
| Bounded AI executor | Machine-clear authorized task and limits; no approval/merge authority. |
| Auditor / security reviewer | Complete trace, policy version, evidence, restricted read access. |
| External control plane | Valid versioned routing request and stable identity. |

### 2.2 Operating environment

GitHub Issues are the authoritative record and GitHub Projects are projections. GitHub identity,
events, access control, and audit capabilities are required external services. Processing MAY run
in any approved environment that meets these requirements. Target repositories and executors are
independently operated and SHALL interact only through validated contracts.

### 2.3 Product constraints and assumptions

See [ProjectRequirements.md](ProjectRequirements.md) and [Assumptions.md](Assumptions.md). Most
notably, target execution cannot assume sibling access, external contracts remain externally owned,
and uncertainty stops automation.

## 3. Functional requirements

The normative requirements are grouped in [FunctionalRequirements.md](FunctionalRequirements.md):

* `FR-INT-*`: intake, provenance, and sensitive-content handling.
* `FR-CLS-*`: classification, hierarchy, dependencies, and backlog health.
* `FR-GOV-*`: human priority, readiness, approval, revocation, and freshness.
* `FR-RTE-*`: canonical construction, routing initiation, idempotency, and reconciliation.
* `FR-OUT-*`: status/result validation, review, disposition, and lifecycle completion.
* `FR-PRJ-*` and `FR-RPT-*`: Project projection, drift, and portfolio reporting.
* `FR-TGT-*`: target-local obligations only when this repository is the execution target.

Business semantics and scenario detail are in [BusinessRules.md](BusinessRules.md),
[UseCases.md](UseCases.md), and [UserStories.md](UserStories.md).

## 4. External interface requirements

All cross-boundary exchanges SHALL provide explicit identity, version, provenance, correlation,
validation, error semantics, retry rules, idempotency, and ownership. Required contracts are:

* [Interface-OrganizationControlPlane.md](Interface-OrganizationControlPlane.md)
* [Interface-Slugger.md](Interface-Slugger.md)
* [Interface-ConsultingPlaybook.md](Interface-ConsultingPlaybook.md)
* [Interface-TargetRepositories.md](Interface-TargetRepositories.md)
* [Interface-GitHub.md](Interface-GitHub.md)

These specifications state required behavior, not an assertion that an external repository already
implements it. Unknowns block reliance until owners validate them.

## 5. Nonfunctional requirements

[NonFunctionalRequirements.md](NonFunctionalRequirements.md) normatively specifies performance,
scalability, availability, reliability, recovery, security, privacy, compliance, auditability,
observability, maintainability, extensibility, configuration, independent deployment, portability,
interoperability, usability, accessibility, documentation, testability, automation, and AI safety.

### 5.1 Error handling

Errors SHALL be categorized as validation, authorization, compatibility, dependency, conflict,
duplicate, throttling, transient external, permanent external, sensitive-data, or unknown. The
system SHALL fail closed; retain last confirmed authority; correlate the failure; avoid sensitive
content; distinguish retryable from human-action-required; and present safe, actionable guidance.
An unknown outcome SHALL never be represented as success or safe failure-to-retry.

### 5.2 Logging and telemetry

Logs SHALL be structured, correlated, access-controlled, retained under policy, and free of
secrets. Telemetry SHALL measure service health and product outcomes without copying unnecessary
task content or private data. Metrics SHALL disclose definitions, denominators, exclusions,
freshness, and the difference between proposed, executed, accepted, and delivered work.

### 5.3 Configuration

Taxonomy, states, roles, targets, executors, Projects, mappings, thresholds, policy references,
contract compatibility, and feature activation SHALL be governed configuration. Secrets SHALL be
managed separately. Safety-critical missing/invalid configuration SHALL stop automation.

## 6. System acceptance criteria

The baseline is acceptable when:

1. Every Must functional acceptance criterion is verified and traceable to a future test.
2. Every Must nonfunctional threshold is measured or has an approved pre-production evidence plan.
3. Representative happy, alternative, failure, retry, concurrency, stale-approval, malicious-input,
   drift, recovery, closure, and accessibility scenarios pass.
4. External owners validate supported contract versions, identity, transport/event, payload,
   status/result, idempotency, and operational responsibilities.
5. A security review confirms least privilege, sensitive-data controls, trust boundaries, and that
   automation cannot approve, merge, release, or deploy.
6. An operations exercise demonstrates observability, ambiguous-handoff reconciliation, Project
   drift repair, and recovery without losing acknowledged governance decisions.
7. Users can distinguish lifecycle states and complete routine intake/approval tasks within the
   usability thresholds.

## 7. Traceability

[RequirementsTraceability.md](RequirementsTraceability.md) connects vision goals to business
objectives, requirements, acceptance criteria, and planned test cases. IDs SHALL remain stable and
the matrix SHALL change atomically with requirement meaning.

## 8. Future considerations

Potential future scope includes richer strategy scoring, outcome experiments, capacity forecasting,
multi-portfolio federation, additional executor types, alternative planning projections, policy as
portable organization contracts, and analytics-assisted decomposition. None may weaken issue
authority, human approval, one-target authorization, draft-only automation, fail-closed behavior,
or target-owner control. Each requires discovery, privacy/security analysis, measurable
requirements, and baseline approval before implementation.
