# Interface Requirements — Target Repositories

## Purpose and responsibilities

This contract describes any registered repository targeted by portfolio work, including
`portfolio-tasks` in its separate target-side role. The portfolio authorizes a task and initiates
routing; the control plane routes; the target owns architecture, source changes, local validation,
review, merge, release, deployment, and final engineering disposition; an executor acts only within
the target's delegated boundary.

## Required inputs

Through the organization-owned contract, the target MUST receive a self-sufficient canonical task
with stable identities, source/provenance, target, executor, approval evidence, objective/rationale,
bounded requirements and scope, constraints, acceptance criteria, required validation/evidence,
dependency snapshot, sensitivity decision, draft-only policy, and contract version. It MUST NOT
need read access to portfolio or sibling repositories to interpret required behavior.

## Required outputs and events

The target MUST provide authenticated correlated acceptance/rejection, status sufficient to
distinguish queued/executing/blocked/terminal conditions, and a terminal result containing outcome,
attempt identity, target revision/branch where applicable, validation and test evidence, safe
failure details, timestamps, and at most one draft publication reference. It SHOULD provide target
owner disposition when contractually available. Exact transport belongs to the control plane.

## Required behavior

* Independently validate shared contract and target-local policy before effects.
* Reject wrong target, unsupported executor/version, stale/invalid authority, sensitive or
  ambiguous request, and any request for non-draft automated publication.
* Treat task content and AI output as untrusted; enforce least privilege and target validation.
* Preserve one logical execution/publication outcome for stable delivery identity; payload mismatch
  is a conflict, not an update.
* Never let automation approve, mark ready, merge, release, or deploy.
* Preserve diagnostic evidence on failure without exposing secrets and never report unrun checks
  as passed.
* Accept bounded retry only with the same identity; state whether an uncertain attempt is safe to
  retry. Support compatibility and deprecation rules owned by the organization contract.

## Ownership and onboarding

Each target owner SHALL publish registration, supported contract versions/executors, permissions,
validation expectations, sensitive-data limits, concurrency policy, publication policy, service
objectives, result capability, and escalation contact to the external control-plane owner. Target
registration SHALL pass conformance tests before enablement and after material changes.

## Assumptions, unknowns, and validation

No target implementation is assumed. For every target, entry point, authentication, supported
versions, size limits, executor availability, validation policy, concurrency, retry, cancellation,
evidence format, result transport, retention, and incident response are external dependencies and
MUST be validated before routing is enabled.


## Next-MVP target enablement gate

The only candidate targets are `Young-Consultations/.github`,
`Young-Consultations/portfolio-tasks`, `Young-Consultations/slugger`, and
`Young-Consultations/consulting-playbook`. Inclusion is not enablement. Each target owner and the
`.github` contract owner MUST confirm registration, supported contract/executor,
revision-bound approval validation independent of current labels, local validation, deterministic
branch/publication reuse, result transport, and cancellation behavior. Each SHALL supply provider
conformance evidence usable by the portfolio consumer fixture. Missing evidence is release-blocking
for that target and SHALL fail closed, not cause invented field names or behavior.
