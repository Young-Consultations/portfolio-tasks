# Configuration Architecture

## Configuration domains

| Domain | Examples | Owner required |
| --- | --- | --- |
| Taxonomy | work type, priority, risk, lifecycle and deprecation mappings | portfolio/product owner |
| Governance | material fields, readiness, approver roles, separation/expiry rules | governance/security owners |
| Integration | endpoint references, supported contract overlap, target/executor capability snapshots | control-plane/target owners; consumed here |
| Projection | project identity, field ownership/mapping, freshness and drift thresholds | portfolio/Project owner |
| Operations | retry budgets, concurrency, queue/alert thresholds, reporting periods | operations owner |
| Security/data | classifications, permitted destinations, redaction, retention references | security/data owner |
| Target-local | validation/evidence/publication and tool limits for this repository | repository target owner |

Secrets are references resolved at runtime through a secret facility, never configuration values.
Business work state, approval, routing receipt and result are data, not configuration.

## Ownership, precedence and activation

Precedence from highest to lowest is: immutable safety constraints and compatible external contract;
approved environment policy; repository versioned baseline; explicitly allowed per-target override;
safe documented default. Runtime flags may disable capability but may not bypass approval,
sensitivity, contract or draft-only rules. Issue/Project content cannot override policy.

Every active snapshot has schema and semantic version, owner, effective time, provenance, digest and
environment. Load into a typed model, validate syntax, cross-field semantics, compatibility,
references, permissions and safety before atomic activation. Dry-run impact identifies affected
work and approvals. Activation and rollback are human-authorized and audited.

## Defaults and failure behavior

Defaults are explicit, documented and conservative. No default may invent approver authority,
target registration, executor support, data permission, cancellation safety or compatibility.
Unknown values and deprecated values with no active migration are violations. On invalid startup
configuration, do not serve affected mutations. On failed update, retain the last known safe
snapshot only when still valid; otherwise disable the capability and alert.

## Evolution and testing

Compatible additions preserve old interpretation. Breaking taxonomy/digest/materiality/state
changes require migration, approval invalidation analysis, overlap or coordinated release,
traceability and rollback. Validate configurations in CI, contract conformance, nonproduction and
startup. Test precedence, missing/unknown values, unsafe overrides, secrets leakage, downgrade,
rollback and reproducibility of a historical decision using its recorded version.

