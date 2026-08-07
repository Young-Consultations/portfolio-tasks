# Functional Requirements

## Requirement format

Priorities are **Must** (baseline release), **Should** (needed unless formally deferred), and **May**
(valuable option). Each acceptance criterion has a durable `AC-<requirement>-<number>` identifier.

## Intake and provenance

### FR-INT-01 — Capture structured portfolio work

**Description.** The product SHALL create one canonical portfolio record containing the request's
objective, rationale, work type, scope, required behavior, acceptance criteria, evidence needs,
constraints, target, executor preference, priority, risk, dependencies, sensitivity declaration,
and provenance. **Rationale:** complete structured intent enables governance and isolated execution.
**Priority:** Must. **Dependencies:** BR-01, taxonomy configuration. **Inputs:** human or authorized
producer submission and actor identity. **Outputs:** canonical record in proposed state plus stable
record reference. **Preconditions:** authenticated submitter; supported intake channel.
**Postconditions:** creation is auditable and does not approve or route work.

* **AC-FR-INT-01-1:** Given all required valid data, one proposed authoritative record is created
  and its identifier and provenance are visible.
* **AC-FR-INT-01-2:** Missing or invalid required data identifies every correctable field and
  creates no executable authorization.
* **AC-FR-INT-01-3:** Creation alone produces no routing request.

**Related vision goals:** structured intake, one authoritative issue, traceability.

### FR-INT-02 — Preserve provenance and revisions

**Description.** The product MUST preserve actor, source, time, prior value, and reason where
required for all governed content and state changes. **Rationale:** auditors and reviewers need an
accountable history. **Priority:** Must. **Dependencies:** FR-INT-01, NFR-AUD-01. **Inputs:** create,
edit, transition, or external update. **Outputs:** human-readable current state and immutable audit
event. **Preconditions:** canonical record exists. **Postconditions:** history remains correlated.

* **AC-FR-INT-02-1:** A reviewer can determine who or what changed each governed value, when, from
  what, to what, and through which source.
* **AC-FR-INT-02-2:** An edit does not erase an earlier approval, result, or disposition event.

**Related vision goals:** provenance, decision authority, auditability.

### FR-INT-03 — Detect sensitive or prohibited content

**Description.** Before automated routing, the product SHALL require a sensitivity declaration and
MUST stop and flag work that is declared sensitive, violates policy, or cannot be confidently
classified. It SHALL support authorized redaction or quarantine without concealing the audit event.
**Rationale:** cross-boundary execution must not leak protected data. **Priority:** Must.
**Dependencies:** security policy, FR-GOV-02. **Inputs:** task content and policy. **Outputs:** safe,
blocked, or review-required decision. **Preconditions:** content exists. **Postconditions:** only
safe, permitted context can advance.

* **AC-FR-INT-03-1:** Known prohibited test content is not included in a handoff and the record is
  blocked with a safe explanation.
* **AC-FR-INT-03-2:** An indeterminate classification requires an authorized human decision.

**Related vision goals:** sensitive-data handling, fail closed, least privilege.

## Classification, hierarchy, and backlog health

### FR-CLS-01 — Classify and validate metadata

**Description.** The product SHALL support governed values for work type, priority, risk, estimated
scope, lifecycle, executor, target, and parallel-safety, and SHALL reject unrecognized values at an
execution boundary. **Rationale:** consistent metadata enables governance and reporting.
**Priority:** Must. **Dependencies:** BR-20, configuration owner. **Inputs:** field changes and active
taxonomy version. **Outputs:** validated metadata or actionable violations. **Preconditions:** actor
may edit the field. **Postconditions:** current values and taxonomy version are traceable.

* **AC-FR-CLS-01-1:** Each configured valid value round-trips without changing its meaning.
* **AC-FR-CLS-01-2:** Deprecated or unknown values cannot silently pass readiness validation.

**Related vision goals:** classification, machine-verifiable routing, reporting.

### FR-CLS-02 — Relate and decompose work

**Description.** The product SHALL relate strategy, outcomes, capabilities, work items, executable
tasks, results, and delivered outcomes; SHALL support decomposition; and MUST prevent one
authorization from spanning multiple targets. **Rationale:** decomposition makes work governable
and target-specific. **Priority:** Must. **Dependencies:** FR-INT-01. **Inputs:** relationship and
decomposition decisions. **Outputs:** typed, navigable links. **Preconditions:** referenced items
exist or are explicitly external. **Postconditions:** child tasks retain parent rationale.

* **AC-FR-CLS-02-1:** From an executable task, a reviewer can navigate to its reason and result.
* **AC-FR-CLS-02-2:** A multi-target request is blocked from execution until separately targetable
  tasks exist with their own approval.

**Related vision goals:** work hierarchy, strategic alignment, bounded execution.

### FR-CLS-03 — Govern dependencies

**Description.** The product MUST record typed dependencies, detect invalid/self/cyclic references
where determinable, determine blocking state at readiness time, and re-evaluate it before handoff.
**Rationale:** unresolved prerequisites make execution unsafe or wasteful. **Priority:** Must.
**Dependencies:** external reference visibility. **Inputs:** references and current dependency
states. **Outputs:** resolved, blocked, unknown, or invalid. **Preconditions:** task exists.
**Postconditions:** unresolved or unknowable blocking dependencies prevent routing.

* **AC-FR-CLS-03-1:** Any open blocking dependency prevents handoff and is identified.
* **AC-FR-CLS-03-2:** `none` is distinguishable from missing or unreadable dependency data.

**Related vision goals:** backlog health, routing readiness, failure safety.

### FR-CLS-04 — Assess backlog health

**Description.** The product SHOULD identify incomplete, stale, oversized, unowned, blocked,
duplicate, weakly decomposed, dependency-bound, and outcome-missing work against configurable,
published thresholds. **Rationale:** portfolio leaders need actionable health signals.
**Priority:** Should. **Dependencies:** FR-CLS-01–03, NFR-OBS-01. **Inputs:** authoritative portfolio
state and thresholds. **Outputs:** item and aggregate health indicators. **Preconditions:** readable
records. **Postconditions:** indicators do not autonomously reprioritize or approve.

* **AC-FR-CLS-04-1:** A report explains the rule and evidence behind every unhealthy indicator.
* **AC-FR-CLS-04-2:** Threshold changes are versioned and do not rewrite historical reports.

**Related vision goals:** backlog health, outcome learning.

## Prioritization and governance

### FR-GOV-01 — Support human prioritization

**Description.** Authorized humans SHALL set and order priority using documented decision inputs;
the product MUST keep priority separate from approval. **Rationale:** value decisions require human
accountability. **Priority:** Must. **Dependencies:** role policy, FR-CLS-01. **Inputs:** priority,
rationale, actor. **Outputs:** auditable portfolio priority. **Preconditions:** authorized actor.
**Postconditions:** routing eligibility is unchanged unless separately approved.

* **AC-FR-GOV-01-1:** Raising priority to its highest value does not authorize or initiate routing.
* **AC-FR-GOV-01-2:** Unauthorized priority changes are rejected or visibly excluded from
  authoritative state.

**Related vision goals:** humans retain priority; priority differs from authorization.

### FR-GOV-02 — Validate readiness

**Description.** Before approval and again before handoff, the product SHALL evaluate completeness,
scope, target, executor, registration, dependencies, sensitivity, risk, contract compatibility,
and applicable policy, returning all actionable violations. **Rationale:** authorization must be
based on a safe, executable snapshot. **Priority:** Must. **Dependencies:** FR-INT-03, FR-CLS-03,
external registration contract. **Inputs:** authoritative snapshot and policy. **Outputs:** pass or
fail plus reasons. **Preconditions:** task is an executable candidate. **Postconditions:** validation
result and assessed revision are auditable.

* **AC-FR-GOV-02-1:** A task with any mandatory violation cannot route.
* **AC-FR-GOV-02-2:** A valid task identifies the exact content revision assessed.

**Related vision goals:** routing readiness, self-sufficient context, fail closed.

### FR-GOV-03 — Record explicit approval and revocation

**Description.** The product MUST accept approval or revocation only from a currently authorized
human, attribute the decision, bind it to the current material task content and target/executor, and make the
state visible. **Rationale:** execution needs accountable human consent. **Priority:** Must.
**Dependencies:** identity/role policy, FR-GOV-02. **Inputs:** decision, actor, current task identity, optional rationale. **Outputs:** approved or revoked decision event. **Preconditions:** approver authorized;
approval requires readiness pass. **Postconditions:** approval may enable but does not itself prove
routing acceptance; revocation stops future progress where control remains possible.

* **AC-FR-GOV-03-1:** An automated identity or unauthorized human cannot approve.
* **AC-FR-GOV-03-2:** The repository can audit the human decision internally; no undeclared rich approval fields are transported in v2.
* **AC-FR-GOV-03-3:** Revocation is visible and prevents a not-yet-accepted handoff.

**Related vision goals:** explicit approval, revocation, human authority.

### FR-GOV-04 — Invalidate stale approval

**Description.** Any material change after approval SHALL create a new `task_id` and invalidate execution eligibility until a
new readiness assessment and approval; nonmaterial changes MUST be defined and audited.
**Rationale:** consent must match executed intent. **Priority:** Must. **Dependencies:** FR-INT-02,
FR-GOV-03, material-change policy. **Inputs:** edit event. **Outputs:** retained approval history and
current stale/unapproved status. **Preconditions:** previously approved task. **Postconditions:** old
approval cannot authorize changed work.

* **AC-FR-GOV-04-1:** Changing target, required behavior, acceptance criteria, risk, dependency,
  executor, scope, or security constraint invalidates approval before routing.
* **AC-FR-GOV-04-2:** A cosmetic change classified nonmaterial retains eligibility only when the
  classification and actor are recorded.

**Related vision goals:** approval freshness, unauthorized edit protection.

## Task construction and routing

### FR-RTE-01 — Construct a canonical task

**Description.** The product SHALL construct a complete, target-specific, immutable-at-handoff task
from the authoritative approved revision, including identity, provenance, objective, rationale,
scope, requirements, constraints, acceptance/evidence needs, dependencies, sensitivity decision,
target, executor, schema-declared authorization state, and contract version. It MUST NOT require target access to
portfolio or sibling repositories. **Rationale:** isolated execution needs self-contained context.
**Priority:** Must. **Dependencies:** FR-GOV-02–04, organization contract. **Inputs:** approved
snapshot. **Outputs:** canonical task or validation failure. **Preconditions:** current approval.
**Postconditions:** content digest/version is correlated to authorization.

* **AC-FR-RTE-01-1:** An authorized reviewer can verify each task value against its source revision.
* **AC-FR-RTE-01-2:** Removing target access to sibling repositories does not make supplied task
  context incomplete.

**Related vision goals:** canonical task construction, self-sufficient boundary.

### FR-RTE-02 — Initiate organization routing

**Description.** The product SHALL submit a valid canonical task to the organization-owned routing
interface only after all gates pass and SHALL distinguish requested, accepted, rejected, and
unknown outcomes. **Rationale:** portfolio owns initiation, not shared routing. **Priority:** Must.
**Dependencies:** FR-RTE-01, Interface-OrganizationControlPlane. **Inputs:** canonical task and
authorized routing identity. **Outputs:** correlated routing request and outcome. **Preconditions:**
current approval and compatible route. **Postconditions:** issue reflects confirmed outcome only.

* **AC-FR-RTE-02-1:** No request is emitted when any gate fails.
* **AC-FR-RTE-02-2:** Timeout or ambiguous acknowledgment is recorded as unknown/reconciliation
  required rather than accepted or failed execution.

**Related vision goals:** controlled handoff, explicit contracts, repository boundary.

### FR-RTE-03 — Ensure idempotent, concurrency-safe initiation

**Description.** The product MUST assign stable delivery/correlation identity, detect replay and
conflict, serialize non-parallel-safe target work, and ensure repeated initiation cannot create a
second conflicting business effect. **Rationale:** event redelivery is normal and must be safe.
**Priority:** Must. **Dependencies:** external idempotency contract, BR-12–14. **Inputs:** task
identity and prior attempt evidence. **Outputs:** new request, existing outcome, in-progress,
conflict, or reconciliation-required. **Preconditions:** routing attempted. **Postconditions:** one
logical delivery has one consistent active publication path.

* **AC-FR-RTE-03-1:** Replaying the same approved revision 100 times yields at most one logical
  accepted delivery.
* **AC-FR-RTE-03-2:** A mismatched payload reusing an identity is rejected as a conflict.
* **AC-FR-RTE-03-3:** Concurrent unsafe tasks for one target are not active simultaneously.

**Related vision goals:** duplicate prevention, execution identity, safe concurrency.

### FR-RTE-04 — Reconcile uncertain handoffs

**Description.** The product SHALL support authorized reconciliation of timed-out, partial, or
ambiguous routing attempts without inventing downstream state. **Rationale:** failures span system
boundaries. **Priority:** Must. **Dependencies:** FR-RTE-02–03, external status capability.
**Inputs:** correlation identity and evidence. **Outputs:** reconciled state, safe retry decision,
or human intervention. **Preconditions:** uncertain attempt. **Postconditions:** resolution is
auditable; duplicates remain prevented.

* **AC-FR-RTE-04-1:** An operator can determine whether retry is safe or why human action is needed.
* **AC-FR-RTE-04-2:** Reconciliation never marks execution complete without validated evidence.

**Related vision goals:** failure recovery, evidence, idempotency.

## Status, results, review, and closure

The next-MVP adds the cross-cutting CI requirement `FR-CIV-01`, normatively specified in
[`../releases/next-mvp.md`](../releases/next-mvp.md). Its durable acceptance criteria
`AC-FR-CIV-01-1..5` validate the complete lifecycle without Codex or real publication.

### FR-OUT-01 — Ingest execution status and result

**Description.** The product SHALL receive or retrieve authenticated, version-compatible,
correlated status and terminal results; validate source, identity, sequence, and allowed transition;
and apply only portfolio-owned representations. **Rationale:** outcomes must feed portfolio truth
without trusting arbitrary input. **Priority:** Must. **Dependencies:** Interface-TargetRepositories,
organization result contract. **Inputs:** status/result envelope. **Outputs:** validated portfolio
status, evidence links, or quarantine. **Preconditions:** known delivery. **Postconditions:** raw
provenance and validation result retained.

* **AC-FR-OUT-01-1:** Forged, unknown, incompatible, stale, or out-of-order terminal input cannot
  advance portfolio state and is visible for review.
* **AC-FR-OUT-01-2:** A valid result links source issue, target, attempt, evidence, and any draft PR.

**Related vision goals:** result ingestion, traceability, contract validation.

### FR-OUT-02 — Preserve human review and disposition

**Description.** The product MUST show that automated publication is draft and SHALL allow an
authorized human to record review and final disposition without granting the executor merge or
production authority. **Rationale:** target owners retain engineering control. **Priority:** Must.
**Dependencies:** FR-OUT-01, target evidence. **Inputs:** result and human disposition. **Outputs:**
review-visible status and disposition. **Preconditions:** result exists or work is cancelled.
**Postconditions:** portfolio state distinguishes execution success from acceptance/delivery.

* **AC-FR-OUT-02-1:** A draft PR result does not automatically become done/delivered.
* **AC-FR-OUT-02-2:** Merge, rejection, cancellation, and supersession are distinguishable and
  attributable.

**Related vision goals:** human review/merge authority, outcome reporting.

### FR-OUT-03 — Close, archive, reopen, and supersede

**Description.** The product SHALL preserve final disposition and traceability through closure and
archival, and SHALL support reopening or supersession without reusing stale approval or erasing
history. **Rationale:** lifecycle history is needed for governance and learning. **Priority:** Must.
**Dependencies:** retention policy, FR-OUT-02. **Inputs:** authorized lifecycle decision. **Outputs:**
closed/archived/reopened/superseded record and links. **Preconditions:** allowed transition.
**Postconditions:** reopened executable work requires fresh readiness and approval.

* **AC-FR-OUT-03-1:** Reopening completed work does not reactivate old authorization.
* **AC-FR-OUT-03-2:** A superseded item identifies its successor and remains discoverable.

**Related vision goals:** archival and closure, historical traceability.

## Project synchronization and reporting

### FR-PRJ-01 — Project authoritative state

**Description.** The product SHALL project configured issue metadata and lifecycle values into
GitHub Projects for planning/reporting and MUST NOT treat a Project field, view, card movement, or
automation as approval. **Rationale:** Projects organize; issues authorize. **Priority:** Must.
**Dependencies:** GitHub Project access and mapping configuration. **Inputs:** authoritative issue
change. **Outputs:** correlated projection or visible sync failure. **Preconditions:** configured
Project. **Postconditions:** authority remains with issue.

* **AC-FR-PRJ-01-1:** Project-only approval-like changes cannot initiate routing.
* **AC-FR-PRJ-01-2:** Each projected field has a documented source and mapping.

**Related vision goals:** Projects relationship, planning visibility.

### FR-PRJ-02 — Detect and reconcile projection drift

**Description.** The product SHALL detect issue/Project disagreement within the configured
freshness objective, report direction and values, and reconcile toward the issue unless explicit
human resolution is required. **Rationale:** silent drift creates competing truth. **Priority:**
Must. **Dependencies:** FR-PRJ-01, NFR-PER-02. **Inputs:** issue and Project snapshots. **Outputs:**
in-sync, drifted, reconciled, or blocked. **Preconditions:** readable projection. **Postconditions:**
no last-write-wins authority transfer.

* **AC-FR-PRJ-02-1:** Injected Project drift is detected and never authorizes execution.
* **AC-FR-PRJ-02-2:** Failed correction identifies impacted item, fields, age, and recovery action.

**Related vision goals:** accurate views, conflict handling, error visibility.

### FR-RPT-01 — Provide portfolio reporting

**Description.** The product SHOULD report demand, priority, age, readiness, approval latency,
blockage, flow, execution outcomes, disposition, governance exceptions, and trace completeness by
time period and permitted dimensions. It MUST distinguish unknown from zero and proposal from
delivery. **Rationale:** leaders need evidence for decisions and learning. **Priority:** Should.
**Dependencies:** FR-CLS-04, FR-OUT-03, metric definitions. **Inputs:** authoritative records and
reporting period. **Outputs:** accessible report and export with calculation metadata.
**Preconditions:** authorized viewer. **Postconditions:** reporting cannot alter authority.

* **AC-FR-RPT-01-1:** Every measure discloses definition, period, exclusions, freshness, and source.
* **AC-FR-RPT-01-2:** Users can trace an aggregate to permitted underlying records.

**Related vision goals:** portfolio reporting, backlog health, outcome learning.

## Target-side behavior for portfolio-tasks

### FR-TGT-01 — Enforce target-local authorization

**Description.** When `portfolio-tasks` is the target, it SHALL independently validate the shared
contract, target identity, executor permission, schema-declared approval state, sensitivity, and
draft-only constraint before execution. **Rationale:** targets retain policy authority.
**Priority:** Must. **Dependencies:** organization contract, FR-RTE-01. **Inputs:** canonical
execution request. **Outputs:** accepted for bounded execution or rejected with safe reason.
**Preconditions:** registered target entry point. **Postconditions:** invalid requests cause no
source changes.

* **AC-FR-TGT-01-1:** Wrong target, unapproved source, prohibited executor, sensitive work, or
  non-draft publication request fails closed.
* **AC-FR-TGT-01-2:** Shared validation and target-policy validation are separately evidenced.

**Related vision goals:** target ownership, least privilege, fail closed.

### FR-TGT-02 — Validate and publish bounded evidence

**Description.** When this repository's authorized execution changes content, it SHALL apply its
own required validation, preserve evidence even on failure, and permit automation to create or
update only one correlated draft pull request. It MUST NOT self-approve, mark ready, merge, release,
or deploy. **Rationale:** automated change remains reviewable and human-controlled. **Priority:**
Must. **Dependencies:** FR-TGT-01, repository validation policy. **Inputs:** bounded execution
output. **Outputs:** validated result and optional draft PR. **Preconditions:** target request
accepted. **Postconditions:** result correlates to source and identifies success/failure honestly.

* **AC-FR-TGT-02-1:** Validation failure retains safe diagnostic evidence and does not report pass.
* **AC-FR-TGT-02-2:** Repeated publication updates or reports the same draft outcome and never
  creates a second conflicting PR.
* **AC-FR-TGT-02-3:** No automated path reaches ready, merged, released, or deployed state.

**Related vision goals:** draft-only publication, target validation, execution evidence.
