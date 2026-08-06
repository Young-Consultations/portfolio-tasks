# Repository Context

## Purpose and ownership

`portfolio-tasks` owns the portfolio-facing record and governance of proposed and authorized work.
The organization owner owns product direction; the portfolio owner owns taxonomy and lifecycle;
repository maintainers own this repository's operability; designated approvers own execution
decisions; each target owner retains engineering and disposition authority.

## Responsibilities

The product SHALL provide intake, canonical issue state, portfolio metadata, hierarchy and
dependencies, prioritization, approval state, task assembly, controlled routing initiation,
portfolio projections, result correlation, outcome visibility, backlog health, and audit evidence.
When it is itself the target, it SHALL also enforce target-local validation and draft publication
policy without claiming organization-router ownership.

## Boundaries

The repository decides **whether a portfolio task is ready and authorized to be handed off**. The
organization control plane decides **whether and how a registered cross-repository route is
accepted**. A target repository decides **how authorized work fits its architecture and whether its
output is accepted**. An executor performs only the bounded request. GitHub hosts authoritative
records and projections but does not change those responsibility boundaries.

## Internal capabilities

* Intake and field validation.
* Lifecycle, priority, risk, dependency, target, and executor governance.
* Approval freshness and authority checks.
* Canonical task construction and routing request initiation.
* Stable correlation, replay detection, and status/result application.
* GitHub Project projection and drift reporting.
* Portfolio reporting, archival, and audit export.
* Target-local policy enforcement when this repository receives execution.

## Data ownership

| Data | Authoritative owner |
| --- | --- |
| Intent, portfolio metadata, approval, portfolio lifecycle, hierarchy | `portfolio-tasks` canonical issue and its governed history |
| Organization schemas, registrations, routing decisions, compatibility | `Young-Consultations/.github` owner |
| Target source, architecture, validation, PR disposition, delivery | Target repository owner |
| Project fields and views | Projection only; source issue wins |
| Execution evidence | Originating system owns raw evidence; portfolio stores or links a validated correlated representation |
| Consulting methods | `consulting-playbook`; portfolio stores only task-relevant, permitted context or references |

The product SHALL minimize copied external data, identify provenance and authority for every copy,
and never silently promote a mirror into a source of truth.

## External consumers and dependencies

Consumers include organization routing, registered targets, Slugger, Project reporting, reviewers,
auditors, and approved AI executors. Dependencies and required contracts are detailed in the
interface specifications. Access to any sibling repository SHALL NOT be presumed.

## Repository lifecycle responsibilities

The repository owns capture, triage, decomposition, prioritization, authorization, handoff,
portfolio status updates, outcome capture, closure, archival, reopening, supersession, retention
of required traceability, and reconciliation after partial failure. It does not own downstream
implementation, merge, release, deployment, or external contract lifecycle.
