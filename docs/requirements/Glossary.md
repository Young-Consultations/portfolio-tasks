# Authoritative Glossary

| Term | Definition |
| --- | --- |
| Approval | An explicit, attributable, current human decision permitting one bounded task to be routed; not priority, creation, editing, or Project placement. |
| Approval freshness | Whether approval still applies to the current material content, target, executor, dependencies, risk, and constraints. |
| Authoritative issue | The single `portfolio-tasks` GitHub Issue that governs an executable task. |
| Bounded AI executor | An automation identity permitted to act only on an approved canonical task within the target and authority supplied. |
| Canonical task | The complete, immutable-at-handoff representation of approved intent and context supplied to routing. |
| Contract owner | Party responsible for a shared interface's schema, versions, validation, and compatibility policy. |
| Correlation ID | Stable identifier connecting authorization, handoff, execution attempts, evidence, publication, and result. |
| Delivery ID | Contract-defined stable identity for a routed unit of delivery; its relationship to correlation ID requires external validation. |
| Disposition | Human-owned final decision such as accepted/merged, rejected, cancelled, superseded, or delivered. |
| Drift | A detectable disagreement between authoritative issue state and a projection or external representation. |
| Executable task | A decomposed, target-specific item that meets readiness requirements and can receive approval. |
| Execution | Target-bounded performance of authorized work; it does not include approval, merge, or deployment authority. |
| Execution result | Versioned, validated evidence describing the outcome of an execution attempt. |
| Fail closed | Stop automated progress when validity, authority, identity, sensitivity, scope, or compatibility is uncertain. |
| Human approver | Authorized person who grants or revokes execution approval and cannot be replaced by automation. |
| Idempotency | Repetition of an event or request produces no conflicting or duplicate business effect. |
| Material change | A change that can affect authorization, intended outcome, scope, target, executor, risk, dependencies, constraints, or acceptance criteria. |
| Portfolio item | Any governed unit in the strategy-to-outcome hierarchy; not every item is executable. |
| Priority | Human-owned relative importance or urgency; never execution authorization. |
| Project projection | GitHub Project representation used for organization/reporting, subordinate to the issue. |
| Provenance | Evidence of where content and decisions originated, who/what changed them, and when. |
| Routing initiation | Portfolio request to the organization control plane to route an approved canonical task. |
| Routing acceptance | External control-plane acknowledgment that a valid request has been accepted; not proof of execution or delivery. |
| Sensitive data | Credentials, secrets, regulated, client-restricted, export-controlled, personal, or other policy-restricted information. |
| Source of truth | Record whose value governs resolution of disagreement for a defined datum. |
| Target repository | Exactly one repository authorized to receive an executable task. |
| Target owner | Human authority for target architecture, validation, review, merge, release, and production. |
| Work hierarchy | Strategic objective → epic/outcome → feature/capability → work item → executable task → result → delivered outcome. |
