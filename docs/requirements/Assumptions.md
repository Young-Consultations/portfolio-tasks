# Assumptions and Open Questions

Open items are discovery inputs, not permission to invent behavior. A question that affects safety,
authority, or contract validity SHALL block the affected automation until resolved.

## Confirmed assumptions from the vision

| ID | Confirmed assumption |
| --- | --- |
| CA-01 | GitHub Issues in `portfolio-tasks` are authoritative for executable portfolio work. |
| CA-02 | GitHub Projects are projections and cannot authorize execution. |
| CA-03 | Approval is explicit, human, and separate from intake and priority. |
| CA-04 | Target repositories own architecture, changes, validation, review, merge, and delivery. |
| CA-05 | One authorization targets one repository; cross-repository outcomes are decomposed. |
| CA-06 | Target execution cannot assume portfolio or sibling-repository access. |
| CA-07 | Automated publication is draft-only; humans control readiness, merge, and production. |
| CA-08 | Organization contracts, registration, routing, compatibility, and shared verification are owned outside this repository. |
| CA-09 | Sensitive, ambiguous, unauthorized, or incompatible work fails closed. |

## Working assumptions requiring validation

| ID | Assumption | Impact if false | Validation owner/method |
| --- | --- | --- | --- |
| WA-01 | GitHub supplies sufficient identity/history/audit capability for required attribution. | Additional governed evidence store or reduced capability needed. | Organization administrator; platform capability review. |
| WA-02 | Authorized approvers and target owners can be enumerated by policy. | Approval cannot be reliably enforced. | Organization owner; role/identity workshop. |
| WA-03 | The control plane supports versioned routing and correlated results. | Handoff/result requirements need external capability work. | `.github` owner; contract review and conformance test. |
| WA-04 | One active execution per task/target satisfies legitimate use cases. | Authorization unit and concurrency model need revision. | Portfolio and target owners; scenario review. |
| WA-05 | A target can receive all permissible task context in a bounded payload. | Secure reference-resolution contract is needed. | Security and target owners; representative task exercise. |
| WA-06 | Project freshness targets are feasible within quotas. | Objectives or projection design require approved change. | GitHub administrator; load/quota test. |
| WA-07 | Slugger mirroring provides continuing business value. | Retire mirror interaction and simplify authority model. | Product and Slugger owners; value/process review. |
| WA-08 | Initial scale and service objectives in NFRs cover three-year demand. | Capacity baseline requires revision. | Product/operations; forecast and load test. |
| WA-09 | The expected `.github/docs/releases/next-mvp.md` selects a contract version and lifecycle compatible with this repository baseline. | Contract construction and every live route remain disabled. | `.github` owner; baseline review plus owner-pinned consumer/provider fixture. |
| WA-10 | The organization contract supplies an authenticated result transport that can correlate a terminal result and draft link to the source issue. | Portfolio cannot reach `Completed`; reconciliation remains blocked. | `.github` owner; result conformance and timeout/ambiguity exercise. |
| WA-11 | `.github`, `portfolio-tasks`, `slugger`, and `consulting-playbook` will each be explicitly enabled as Codex targets for the selected contract. | The affected target cannot participate; listing it does not enable it. | `.github` and each target owner; registry evidence and target conformance fixture. |
| WA-12 | Targets can validate immutable revision-bound approval evidence without requiring a current approval label. | Mutable-label races could deny valid queued work or accept stale work. | `.github` and target owners; label-removal and material-edit conformance cases. |

## Unknowns and questions requiring clarification

### Product and governance

1. Who is the product owner, taxonomy owner, data owner, security owner, and operational on-call?
2. Which identities may author, prioritize, approve, revoke, reconcile, close, and administer?
3. Is separation of duties mandatory for any risk class, client, or target?
4. What counts as a material versus nonmaterial change beyond the mandatory examples?
5. What lifecycle transition table, cancellation semantics, and exception process are approved?
6. What strategy/value scoring, severity, service class, ownership, due-date, and outcome fields are
   required beyond the present baseline?
7. What stale/oversized/blockage thresholds and reporting periods reflect business needs?
8. What constitutes delivered outcome when a PR is unnecessary, rejected, or externally delivered?

### Data, security, compliance, and accessibility

9. Which privacy, client confidentiality, records, export-control, legal-hold, and regulatory rules
   apply, and what are the retention/deletion periods?
10. Which data classifications may be stored in Issues, Projects, logs, artifacts, and AI tasks?
11. What redaction/quarantine and incident process applies after accidental secret disclosure?
12. Which audit users require export, and what platform tier supports tamper evidence and retention?
13. Which user research, assistive technologies, languages, and accessibility exceptions apply?

### Operations and metrics

14. What are approved availability/support hours, incident severities, escalation paths, RTO/RPO,
    external-outage exclusions, and notification expectations?
15. What GitHub quotas, Project sizes, repository counts, workload forecast, and artifact limits
    apply?
16. Where are reconciliation queues and metric definitions reviewed, and who owns remediation?
17. Which success targets are leading indicators versus contractual objectives?

## Dependencies on inaccessible external repositories

### Young-Consultations/.github

Required: contract schemas/versions, validators, target/executor registry, routing and result
interfaces, authentication, release/deprecation policy, approver evidence, idempotency/correlation,
status ordering, retry/cancellation, size limits, service objectives, and incident ownership.

### Young-Consultations/slugger

Required: confirmation of mirror purpose and field ownership; target registration; supported
contracts/executors; local policy; evidence/result behavior; concurrency; draft publication;
permissions; retention; and escalation.

### Young-Consultations/consulting-playbook

Required only if integration is desired: stable references and versions, authorized excerpts,
confidentiality/licensing, provenance, change/withdrawal events, and feedback expectations.

### Other target repositories

For each: owner, registration, supported contract/executor/version, target policy, validation,
sensitivity, concurrency, retry/cancellation, evidence, result path, service objectives, and
incident contact. No target SHALL be enabled before these are validated.
