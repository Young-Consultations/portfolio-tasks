# Architectural Decision Records

Status for each record is **Proposed normative architecture** until the architecture baseline is
approved. A superseding decision must cite impacted vision/requirements and migration evidence.

## ADR-001 — Issues are authoritative; Projects are projections

**Context:** One execution authority is required; Projects provide planning value but can drift.
**Decision:** Canonical executable state and approval live in one issue. Project data is derived and
cannot authorize. **Alternatives:** Project authority; dual-master synchronization; separate
database authority. **Tradeoffs:** Leverages human workflow and auditability but platform limits
must be validated. **Consequences:** Drift/freshness are explicit; correction resolves toward the
issue. **Open questions:** GitHub audit/retention/tier and Project freshness feasibility.

## ADR-002 — Hexagonal modular architecture

**Context:** Current and future transports/automation must evolve without redefining policy.
**Decision:** Domain policies sit inside application orchestration and ports/adapters.
**Alternatives:** workflow-script-centered design; service-per-function microservices.
**Tradeoffs:** More explicit interfaces and mapping, substantially better testability and
portability. **Consequences:** Domain has no GitHub imports; topology remains deployer choice.
**Open questions:** Approved module ownership and deployment cadence.

## ADR-003 — Explicit lifecycle and revision-bound approval

**Context:** Creation, priority and stale consent must not execute work. **Decision:** A transition
policy governs states; human approval binds actor evidence to revision and material-field digest;
material changes invalidate it. **Alternatives:** approval label, prose, Project field, time-only
approval. **Tradeoffs:** Safe and auditable, with additional reapproval friction. **Consequences:**
Edits require materiality evaluation and compare-and-set. **Open questions:** approver registry,
separation of duties, material-field policy and expiry.

## ADR-004 — Immutable self-sufficient versioned task envelopes

**Context:** Targets cannot assume cross-repository access. **Decision:** Construct a bounded
immutable envelope with complete permitted context, identity, approval and policy evidence.
**Alternatives:** target fetches issue; links-only payload; shared mutable database. **Tradeoffs:**
Payload size and copied-data governance versus isolation and reproducibility. **Consequences:**
Redaction, digests, size limits and version compatibility are required. **Open questions:** external
schema/limits/authentication and whether secure reference resolution is ever needed.

## ADR-005 — Organization routing remains external

**Context:** The `.github` repository owns organization contracts and routing. **Decision:** This
repository initiates via a port and consumes correlated facts; it never implements shared routing.
**Alternatives:** direct target dispatch; duplicate router here. **Tradeoffs:** External dependency
but coherent ownership. **Consequences:** Integrations stay disabled without validated conformance.
**Open questions:** all control-plane protocol and SLO details.

## ADR-006 — Idempotent saga and reconciliation over distributed transactions

**Context:** Cross-repository effects can time out, replay or arrive out of order. **Decision:** Use
stable identities/digests, durable effect intent, at-least-once-safe consumers and explicit
reconciliation. **Alternatives:** exactly-once transport claims; best-effort retries; distributed
transaction. **Tradeoffs:** Operational state/queues in return for recoverability. **Consequences:**
Ambiguity blocks blind retry; divergent replay conflicts. **Open questions:** external status-query
guarantees and approved RTO/RPO.

## ADR-007 — Target sovereignty and draft-only automation

**Context:** Portfolio approval cannot replace target engineering authority. **Decision:** Targets
independently validate and own execution/evidence; automation may publish no more than one draft.
Humans own readiness, merge, release and deploy. **Alternatives:** central execution/merge; implicit
target acceptance. **Tradeoffs:** Additional local onboarding with safer boundaries.
**Consequences:** Each target passes conformance and declares policy/capability. **Open questions:**
Per-target support, cancellation, evidence, concurrency and escalation.

## ADR-008 — Fail closed and preserve evidence

**Context:** Sensitive, ambiguous, unauthorized and incompatible inputs create material risk.
**Decision:** Block/quarantine them with actionable diagnostics; all authority/effects are auditable
and telemetry is redacted. **Alternatives:** best-effort inference; permissive fallback.
**Tradeoffs:** Reduced automation throughput during uncertainty. **Consequences:** Security-critical
dependencies are hard gates and require human resolution. **Open questions:** classification,
retention, legal hold and incident policies.

## ADR-009 — Separate portfolio and local target roles

**Context:** This repository both initiates portfolio work and can be a target for its own changes.
**Decision:** Model roles as separate components, ports, permissions and audit domains, independently
deployable where practical. **Alternatives:** one privileged workflow/service. **Tradeoffs:** Some
duplication of bootstrapping, less privilege confusion. **Consequences:** Target execution never
confers portfolio authority. **Open questions:** deployment identity and credential arrangement.

## ADR-010 — Versioned configuration and conformance-driven extensions

**Context:** Taxonomy, targets, executors and policies evolve. **Decision:** Validate/version policy
snapshots; extensions use ports and pass provider/consumer and invariant suites.
**Alternatives:** hard-coded labels; runtime discovery without governance. **Tradeoffs:** Release
discipline versus safe independent evolution. **Consequences:** rollback/deprecation and policy
version evidence are mandatory. **Open questions:** configuration owners and approval workflow.


## ADR-011 — Approval evidence, not labels, carries authorization

**Context:** Blueprint workflows route `status:approved`, add `status:queued`, then remove the
approval label, while targets may recheck either label. That creates a mutable-label race.
**Decision:** Immutable human approval evidence bound to revision/material digest, target, executor,
and policy is authoritative. Labels only project lifecycle. Queued/accepted work remains authorized
by that evidence; label replacement neither revokes nor grants authority. Material edits invalidate
unaccepted approval. Revocation before acceptance stops dispatch; afterward it requests contracted
cancellation without rewriting history. **Alternatives:** require approval label forever; transfer
authority to a queued label; target rereads current labels. **Tradeoffs:** durable evidence and
target validation are more complex but remove race-dependent authorization. **Consequences:**
existing workflow behavior is migration evidence only; consumer fixtures must prove
label-independent checks. **Open questions:** evidence representation and cancellation semantics
require `.github` confirmation.

## ADR-012 — Next-MVP interface lifecycle is simulated continuously

**Context:** Cross-repository drift can break the approved-issue-to-draft-PR path, while normal CI
must not invoke Codex or publish. **Decision:** `FR-CIV-01` defines a deterministic full-lifecycle
consumer suite using contract fixtures and side-effect-free adapters. It asserts at-least-once
delivery with idempotent visible effects, target/branch/draft/correlation/result identity, negative
gates, recovery, and zero Codex/branch/PR effects. **Alternatives:** unit tests only; live Codex/PR
smoke tests; exactly-once claims. **Tradeoffs:** fixtures require owner-pinned maintenance but make
drift safe and reproducible. **Consequences:** provider fixture or lifecycle drift fails CI; live
enablement still requires external conformance. **Open questions:** organization contract version,
transport, lifecycle ordering, result path, and four target enablements.
