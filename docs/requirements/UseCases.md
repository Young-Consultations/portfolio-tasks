# Use Cases

## Actors

Task author, consultant, portfolio manager, engineering lead, human approver, repository maintainer,
organization control plane, target repository/owner, bounded AI executor, reviewer, auditor, GitHub,
and Project consumer.

## UC-01 — Capture and triage intent

**Actors:** task author, portfolio manager. **Precondition:** authenticated author.
**Primary flow:** author supplies structured intent and provenance; system validates it, creates one
proposed issue, reports missing readiness data, and portfolio manager classifies, relates,
decomposes, and prioritizes it. **Alternative:** valid human-only or planning-only work remains
non-executable. **Failure:** invalid or sensitive content is rejected/blocked with safe corrective
guidance; platform failure produces no false record. **Outcome:** governable backlog item, not
approval. **Business value:** reduces incomplete demand and makes work discoverable.

## UC-02 — Decompose a cross-repository outcome

**Actors:** portfolio manager, target owners. **Primary flow:** identify multiple targets; retain a
parent outcome; create one bounded child per target; carry rationale; define dependency order;
obtain independent readiness and approval. **Alternative:** discovery/research item precedes task
creation. **Failure:** undecomposed multi-target item remains blocked. **Outcome:** traceable,
independently reviewable tasks. **Business value:** reduces ambiguous authority and delivery risk.

## UC-03 — Prioritize without authorizing

**Actors:** organization owner, engineering lead, portfolio manager. **Primary flow:** inspect
decision inputs, set priority and rationale, and view ordered backlog. **Alternative:** defer or
reclassify. **Failure:** unauthorized update is rejected/audited. **Outcome:** transparent ordering
with unchanged execution authorization. **Business value:** focuses capacity while retaining safety.

## UC-04 — Approve or revoke an executable task

**Actors:** human approver. **Primary flow:** system presents current revision, material context,
readiness evidence and boundaries; authorized human approves; system binds decision to revision,
target, executor, time and policy. **Alternative:** approver rejects, requests edits, or revokes.
**Failure:** unauthorized/automated approval, failed readiness, unknown sensitivity, or unresolved
dependency fails closed. **Outcome:** attributable current decision. **Business value:** preserves
human accountability.

## UC-05 — Change approved work

**Actors:** task author, approver. **Primary flow:** user edits material content; system records the
diff, invalidates eligibility, and requires readiness and reapproval. **Alternative:** governed
nonmaterial edit is recorded without invalidation. **Failure:** stale event or concurrent edit is
reconciled, never routed under old consent. **Outcome:** execution matches reviewed intent.
**Business value:** prevents authorization drift.

## UC-06 — Route an approved task

**Actors:** portfolio system, control plane. **Primary flow:** revalidate; build self-sufficient
canonical task; assign stable identity; submit; validate correlated acceptance; show queued state.
**Alternative:** duplicate returns existing outcome. **Failure:** rejection shows action; timeout is
indeterminate and reconciled; incompatibility or conflict stops. **Outcome:** exactly one controlled
handoff or honest non-handoff. **Business value:** safely converts decision into action.

## UC-07 — Execute in a target repository

**Actors:** target, bounded executor, target owner. **Primary flow:** target validates contract and
local policy; executor performs bounded work; target validates output; one draft PR and correlated
evidence are produced; human reviews. **Alternative:** already satisfied result contains evidence
and no fabricated change. **Failure:** validation/execution failure preserves safe diagnostics and
draft-only boundary; invalid request causes no effects. **Outcome:** reviewable evidence, not
automatic delivery. **Business value:** gains AI leverage without surrendering ownership.

## UC-08 — Ingest results and record disposition

**Actors:** control plane, portfolio system, reviewer/target owner. **Primary flow:** validate result
identity/version/order; link evidence and draft output; reviewer accepts, rejects, cancels, or
supersedes; record final disposition/outcome. **Alternative:** blocked work returns to governed
backlog. **Failure:** forged/stale/unknown result is quarantined. **Outcome:** trace from request to
human disposition. **Business value:** closes feedback loop and enables learning.

## UC-09 — Synchronize Project visibility

**Actors:** portfolio manager, Project consumer. **Primary flow:** authoritative issue changes;
configured fields project; freshness is monitored. **Alternative:** no Project configured leaves
issue operation intact. **Failure:** drift is displayed and reconciled toward issue; Project edits
cannot authorize. **Outcome:** reliable planning view. **Business value:** visibility without a
second control plane.

## UC-10 — Recover from partial failure or replay

**Actors:** maintainer, control plane, target owner. **Primary flow:** locate correlation; inspect
confirmed states; query external evidence; safely retry with same identity or reconcile; document
resolution. **Alternative:** require manual cancellation or owner decision. **Failure:** absence of
evidence remains ambiguous/blocked. **Outcome:** no duplicate effect and an auditable recovery.
**Business value:** trustworthy automation under real distributed-system failure.

## UC-11 — Assess portfolio health and audit a task

**Actors:** portfolio manager, owner, auditor. **Primary flow:** select period; inspect freshness,
flow, blockage, completeness and outcomes; trace a sample through decisions and evidence; export
permitted data. **Alternative:** unknown values are reported explicitly. **Failure:** access denial
or incomplete trace creates a governance exception. **Outcome:** actionable health and audit
evidence. **Business value:** improves decisions and demonstrates control effectiveness.

## UC-12 — Close, reopen, or supersede work

**Actors:** portfolio manager, target owner. **Primary flow:** record final disposition and evidence;
close/archive; later reopen or create a linked successor; require fresh authorization for new
execution. **Alternative:** cancelled work records why no outcome exists. **Failure:** attempt to
reuse stale approval is rejected. **Outcome:** durable history and correct lifecycle.
**Business value:** preserves institutional knowledge.
