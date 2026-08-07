# portfolio-tasks next-MVP baseline

**Status:** repository baseline for approval; external enablement blocked pending organization
confirmation. **Organization baseline expected at:**
`Young-Consultations/.github/docs/releases/next-mvp.md` (not inspected). The prompt-supplied objective
is the working organization baseline. This document does not copy an organization-owned schema.

## Outcome and repository contribution

The MVP carries one eligible `portfolio-tasks` issue, approved by an authorized human for one
immutable revision, through organization routing to exactly one enabled target:
`Young-Consultations/.github`, `Young-Consultations/portfolio-tasks`,
`Young-Consultations/slugger`, or `Young-Consultations/consulting-playbook`. The target invokes Codex,
performs its own validation, and creates or reuses exactly one draft pull request. A validated
terminal result and draft-PR link are projected onto the source issue. Merge, release, deployment,
production operation, and any claim of production readiness remain human-controlled and outside
this MVP.

`portfolio-tasks` owns work intake; source-issue identity; eligibility evaluation; authoritative
human approval truth and provenance; revision/digest binding; selection of exactly one target;
canonical task construction; routing initiation; portfolio execution-state projection; result
consumption/correlation; and user-visible status, failures, and recovery guidance. It does **not**
own the organization target registry or shared contracts, target-local authorization, Codex
implementation semantics, target validation policy, PR review/merge, release, or deployment.
When this repository is the target, its target gateway is a distinct responsibility, identity, and
audit boundary from portfolio approval and dispatch.

## Selected requirements

MVP selection is deliberate; priority `Must` does not by itself imply inclusion.

**Included:** `FR-INT-01`, `FR-INT-02`, `FR-INT-03`, `FR-CLS-01`, `FR-CLS-02`, `FR-CLS-03`,
`FR-GOV-02`, `FR-GOV-03`, `FR-GOV-04`, `FR-RTE-01`, `FR-RTE-02`, `FR-RTE-03`, `FR-RTE-04`,
`FR-OUT-01`, `FR-TGT-01`, `FR-TGT-02`, `NFR-REL-01`, `NFR-REL-02`, `NFR-REL-03`,
`NFR-SEC-01`, `NFR-SEC-02`, `NFR-SEC-05`, `NFR-AUD-01`, `NFR-OBS-02`, `NFR-MNT-01`,
`NFR-MNT-02`, `NFR-INT-01`, `NFR-INT-02`, `NFR-USA-02`, `NFR-TST-01`, `NFR-TST-02`,
`NFR-AUT-01`, `NFR-AI-01`, and `NFR-AI-02`.

**Deferred from this MVP:** `FR-CLS-04`, `FR-GOV-01`, `FR-OUT-02`, `FR-OUT-03`,
`FR-PRJ-01`, `FR-PRJ-02`, and `FR-RPT-01`. They remain baseline requirements, but portfolio
prioritization, Projects synchronization/reporting, post-draft human disposition, archival, reopen,
and delivery-outcome analytics are not needed to prove this MVP. Unlisted NFRs remain quality
constraints for later releases or evidence plans; they are not silently satisfied or waived.

## Authoritative lifecycle and authorization

| State | Meaning and permitted transition |
| --- | --- |
| Proposed | Intake exists; it is neither eligible nor authorized. |
| Ready for approval | Current revision passes eligibility/readiness; no approval exists. |
| Approved | Authorized human evidence binds the target, executor, policy version, issue revision and material-content digest. |
| Pending routing | A dispatch intent with stable correlation/delivery identity is durable; acceptance is not yet proven. |
| Queued / accepted | The control plane and then target have acknowledged the same authorized delivery. Queued work remains authorized by immutable approval evidence, not by a label. |
| Executing | The target reports bounded execution in progress. |
| Draft PR available | A validated result identifies exactly one created or reused open draft PR. This is the MVP success state, not merge or delivery. |
| Completed | Portfolio processing of an authenticated terminal result is complete and the source issue visibly contains its correlation, result, and draft link (or an allowed terminal no-change result). |
| Failed / blocked | Progress stopped with confirmed failure or unresolved prerequisite, owner, correlation, and recovery action; unknown is not failure. |
| Withdrawn / cancelled | A human withdrew pre-dispatch authority, or an externally confirmed cancellation stopped accepted work. |
| Superseded | A replacement issue is linked; old approval never transfers. |

Approval is an append-only decision record, not a mutable label. The record identifies the human
and authority basis, UTC time, decision, issue revision, material digest, one target, executor, and
policy version. `status:approved`, `status:queued`, or similar labels are replaceable UI projections.
Adding, removing, or replacing a label cannot create or revoke authorization. Router acceptance may
replace an approval label with a queued label while the bound evidence remains valid. A target must
validate that evidence rather than require a racing label read.

A material edit to objective, behavior, scope/non-scope, acceptance evidence, constraints, target,
executor, risk, sensitivity, or dependencies creates a new digest and invalidates unaccepted
authorization. A policy-classified cosmetic edit may retain it only with an audited classification.
Pre-acceptance revocation prevents dispatch or causes the pending intent to terminate. After
control-plane or target acceptance, revocation becomes a cancellation request; state remains
authorized-but-cancellation-pending until the externally owned contract confirms stopped,
completed, or unable-to-cancel. It never rewrites history or claims that already occurring work was
unauthorized.

Delivery is **at least once with idempotent visible effects**. Same identity and digest returns the
recorded outcome; same identity with a different digest is a conflict. Duplicate issue events,
router delivery, target result, or publication request cannot create another logical execution,
branch, PR, terminal comment, or state advance. Results correlate by source issue, approved digest,
target, delivery/correlation identity, and attempt identity; precise identity relationships await
the organization contract. Missing, conflicting, or ambiguous results enter reconciliation and
cannot become `Completed`. MVP completion requires a validated terminal result visibly correlated
on the source issue; draft availability alone is insufficient until consumption succeeds.

## Required organization and target decisions

The following are release-blocking until the `.github` owner publishes evidence: exact contract
version; request and result transports; authentication; approval-evidence representation and
validation; correlation/delivery/attempt relationships; ordered lifecycle semantics; duplicate,
query, timeout and cancellation behavior; target registry entries; and enablement of all four
targets. Portfolio-owned expectations are semantic only and do not invent field names.

| Boundary | External owner | Required evidence | Status and consumer check |
| --- | --- | --- | --- |
| Organization control plane and `.github` as target | `.github` owner | Published baseline, supported version, request/result transport, approver validation, registry and target conformance evidence | **Blocking**; portfolio consumer fixtures validate accept/reject/duplicate/conflict/timeout/result semantics. |
| `portfolio-tasks` as target | repository target owner plus `.github` owner | Separate target identity/policy, supported version, local validation and publication/result conformance | **Blocking**; local target fixture proves no portfolio privilege and one draft. |
| Slugger | Slugger owner plus `.github` owner | Enabled registration, supported contract/executor, local authorization/validation, result and draft-publication evidence | **Blocking**; consumer fixture uses only confirmed semantics. |
| Consulting Playbook | playbook owner plus `.github` owner | Enabled registration, supported contract/executor, local authorization/validation, result and draft-publication evidence | **Blocking**; consumer fixture uses only confirmed semantics. |
| GitHub platform | organization administrator | Identity/permission, event/redelivery, draft-PR and nonproduction test-environment evidence | **Blocking for live enablement**; mocked adapter in normal CI, separately approved platform conformance evidence. |

## CI interface-validation requirement (`FR-CIV-01`)

Normal CI SHALL run a deterministic, hermetic consumer lifecycle suite using fixtures, mocks,
stubs, or test adapters in place of Codex, GitHub branch/PR writes, and external transports. It
SHALL simulate, in order: eligible issue creation; authorized approval of a revision/digest;
canonical construction; dispatch request; routing acceptance; target acceptance; stub execution;
stub validation; simulated draft-PR result; and result consumption/source-issue update.

* `AC-FR-CIV-01-1`: the happy-path fixture asserts the chosen one of four targets, deterministic
  branch identity, draft flag/title/link metadata, correlation/delivery identity, ordered states,
  exactly one logical draft publication, and the correlated terminal source-issue representation.
* `AC-FR-CIV-01-2`: process/network assertions prove no Codex executable/API is invoked, no remote
  mutation occurs, and no real branch, commit push, or pull request is created in normal CI.
* `AC-FR-CIV-01-3`: table-driven negative fixtures cover missing approval, unauthorized approver,
  material edit after approval, pre-acceptance withdrawal, invalid target, disabled target,
  malformed/incompatible contract, target rejection, execution failure, and validation failure;
  each fails closed at the expected state with safe recovery guidance.
* `AC-FR-CIV-01-4`: recovery fixtures cover withdrawal after acceptance, duplicate dispatch,
  duplicate target result, existing draft PR reuse, result timeout, ambiguous status, stale and
  out-of-order results; each asserts at-least-once handling and idempotent visible effects.
* `AC-FR-CIV-01-5`: schemas/fixtures assert the portfolio-owned semantic expectations while an
  owner-pinned provider fixture supplies external details. Any incompatible contract, lifecycle,
  target enablement, branch/publication, or result-correlation drift fails CI rather than updating
  snapshots automatically.

`FR-CIV-01` traces forward to `NFR-REL-01..03`, `NFR-SEC-01..02`, `NFR-INT-01..02`,
`NFR-TST-01..02`, and `NFR-AUT-01`; test obligations are `TC-MVP-E2E-001`,
`TC-MVP-NEG-001`, `TC-MVP-REC-001`, and `TC-MVP-NOEFFECT-001`.

## Acceptance scenario and repository-local exit criteria

Given an eligible issue whose approved digest selects one enabled target, when a duplicate-capable
transport delivers its canonical task, then the target validates authorization, stub execution and
validation succeed, one deterministic draft PR is simulated or reused, and a compatible terminal
result updates the same source issue to `Completed` with correlation and draft link. No merge,
release, deployment, Codex call, real branch, or real PR occurs in this acceptance test.

Repository-local exit requires: (1) all included acceptance criteria and the four MVP suites pass;
(2) lifecycle terms and bidirectional traceability contain no contradiction; (3) each failure has
an owner and recovery action; (4) source representation proves a correlated terminal result;
(5) normal CI proves zero Codex/publication side effects; and (6) the organization and each target
provide the blocking conformance evidence above. Until item 6 is confirmed, documentation may be
approved but live MVP routing is **not ready for enablement**.
