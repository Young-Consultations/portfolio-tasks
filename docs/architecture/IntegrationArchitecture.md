# Integration Architecture

## Certainty model

* **Known:** established by Vision/Requirements for this repository.
* **Assumed:** working premise explicitly requiring owner validation.
* **Unknown:** no implementation, protocol, schema, or behavior may be inferred.

| Integration | Known | Assumed | Unknown / validation required |
| --- | --- | --- | --- |
| GitHub Issues | Authoritative executable portfolio record; issue actions alone do not approve | Identity/history may satisfy attribution | tier, audit retention, event ordering/delivery, permissions, quotas, legal retention |
| GitHub Projects | Derivative planning/reporting projection only | freshness targets are feasible | field IDs, limits, conflict UX, service objectives, exact sync trigger |
| `Young-Consultations/.github` control plane | Externally owns schemas, registry, router, compatibility/shared verification | versioned route and correlated result are supported | transport, schema, auth, status/cancel/retry, limits, SLOs, incident owner; conformance evidence |
| Target repositories | Own architecture, policy, validation, draft PR and disposition | one active execution per task/target suffices | per-target entry point, executor/version, concurrency, evidence, retention, escalation |
| Slugger | May be target; optional mirror must remain derivative | mirroring might provide value | whether mirror remains, fields/direction/identity, permissions, target capabilities |
| Consulting playbook | Externally owns methods/content | integration only if approved | reference/version, licensing/confidentiality, withdrawal and feedback contract |

## Workflow boundaries

The portfolio submits a command to the organization control plane and consumes facts from it. It
does not address a target directly for governed execution. Targets do not fetch required task
context from the portfolio. Project synchronization is isolated so its outage cannot block
canonical issue maintenance or mutate approval. Optional mirroring is a separately versioned
projection, never an execution handoff.

## Synchronization and messaging expectations

Cross-boundary delivery is treated as at least once and asynchronous even if a transport appears
synchronous. Producers retain stable IDs; consumers authenticate, validate, deduplicate and expose
ordering conflict. A receipt means only what the external contract explicitly defines. Status and
result consumers tolerate delayed exact duplicates, not semantically divergent ones. Backoff,
quota handling and dead-letter/quarantine paths are bounded and observable.

Issue→Project mapping is one-way for authoritative semantics. Bidirectional user-managed planning
fields are permitted only when field ownership and conflict rules are explicit and none influences
approval. Drift correction preserves human-owned fields.

## External enablement gate

Before enabling any repository or integration, record: accountable owner/contact; purpose and data
classification; contract versions and deprecation; authentication/authorization; target/executor
registration; inputs/outputs and limits; idempotency, concurrency, retry and cancellation;
evidence and retention; SLO/incident/escalation; threat/privacy review; provider/consumer contract
tests; rollback/disable plan. Any safety-critical unknown blocks enablement.

## Failure isolation

An external outage cannot silently promote lifecycle state. Control-plane uncertainty yields
`handoff-uncertain`; target rejection yields a governed non-success outcome; Project failure yields
projection drift; mirror failure yields mirror drift only; reporting failure never alters work.
Circuit breaking and backpressure protect dependencies, while reconciliation preserves work.

