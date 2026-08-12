# portfolio-tasks next-MVP baseline

**Status:** documentation and interface baseline; ready for repository implementation planning.

## Immutable organization compatibility unit

This repository consumes release `2.2.0` and payload version `ai-sdlc-contract/v2` from
`Young-Consultations/.github` at the immutable reference
`c6090e5bbadcc2102a1cb91875466e9decdada1e` (the **compatibility SHA**). The compatibility unit is:

* `release/release-manifest.json`
* `docs/interfaces/mvp-v2-compatibility.md`
* `docs/releases/next-mvp.md`
* `config/codex-repositories.json` as the immutable target capability registry, excluding mutable
  operational activation
* `contracts/task-contract.schema.json`
* `contracts/execution-input.schema.json`
* `contracts/execution-result.schema.json`
* `tests/fixtures/mvp-v2/manifest.json` (fixture set `TC-MVP-CI-001`)
* `.github/workflows/codex-router.yml`
* `.github/workflows/codex-result-receiver.yml`

Every workflow reference and direct schema-file fetch MUST use the full compatibility SHA. Mutable
`main`, the uncreated `ai-sdlc-v2.2.0` tag, an assumed `ai-sdlc-contracts` package, and local copies
or extensions of the closed schemas are not dependencies. Direct immutable schema-file consumption
is the MVP dependency unless publication of an artifact is independently confirmed.

This consumer alignment does not establish sibling-repository conformance or executable
cross-repository conformance.

## Outcome and responsibility boundary

The MVP ends with one validated draft PR and one correlated canonical result projected on its
source issue. Merge, release, deployment, production operation, and production-readiness decisions
remain human-controlled.

`portfolio-tasks` owns source issue identity, intake and eligibility, human approval truth,
material-change detection, creation of a new `task_id` after a material change, exactly-one-target
selection, canonical task construction, explicit execution-mode selection, router invocation,
post-admission lifecycle projection, and result consumption/presentation. It is also one possible
execution target through the separately bounded `.github/workflows/codex-execute.yml` adapter.
That target role applies only target policy: it cannot approve its own work, bypass the router, or
gain portfolio authority.

## Exact included and deferred requirements

MVP inclusion is deliberate; a `Must` priority alone does not imply inclusion.

**Included:** `FR-INT-01`, `FR-INT-02`, `FR-INT-03`, `FR-CLS-01`, `FR-CLS-02`, `FR-CLS-03`,
`FR-GOV-02`, `FR-GOV-03`, `FR-GOV-04`, `FR-RTE-01`, `FR-RTE-02`, `FR-RTE-03`, `FR-RTE-04`,
`FR-OUT-01`, `FR-TGT-01`, `FR-TGT-02`, `FR-CIV-01`, `NFR-REL-01`, `NFR-REL-02`,
`NFR-REL-03`, `NFR-SEC-01`, `NFR-SEC-02`, `NFR-SEC-05`, `NFR-AUD-01`, `NFR-OBS-02`,
`NFR-MNT-01`, `NFR-MNT-02`, `NFR-INT-01`, `NFR-INT-02`, `NFR-USA-02`, `NFR-TST-01`,
`NFR-TST-02`, `NFR-AUT-01`, `NFR-AI-01`, and `NFR-AI-02`.

**Deferred:** `FR-CLS-04`, `FR-GOV-01`, `FR-OUT-02`, `FR-OUT-03`, `FR-PRJ-01`,
`FR-PRJ-02`, and `FR-RPT-01`. Unlisted NFRs remain later-release quality constraints and are not
claimed satisfied or waived.

## Canonical task and approval lifecycle

The complete field set and validation rules come only from
`contracts/task-contract.schema.json@c6090e5bbadcc2102a1cb91875466e9decdada1e`. The subordinate
MVP dispatch summary is: `contract_version` is `ai-sdlc-contract/v2`, `status` is `approved`,
`executor` is `codex`, `dependencies` is `[]`, and `target_repository` is exactly one target whose
current activation the organization router authorizes before dispatch.

1. A human approves the current material task content.
2. `portfolio-tasks` constructs the canonical task with `status: approved`.
3. It explicitly selects `verify` or `implement`.
4. It calls the router pinned to the compatibility SHA.
5. Only successful router admission permits the source projection `queued`.
6. `queued` is never submitted as authorization.
7. A material edit invalidates the executable identity, creates a new `task_id`, and requires new
   human approval.
8. Duplicate dispatch of the same logical delivery preserves `delivery_id`.
9. Missing, delayed, rejected, or ambiguous results enter reconciliation; they do not authorize a
   blind redispatch.
10. Withdrawal before execution prevents new side effects; cancellation after execution begins is
    best effort.
11. A transport acknowledgement is never presented as execution success.

Approval ID, revision digest, approver, approval timestamp, revocation record, and freshness
metadata are deferred to v3. Repository-internal audit records MAY retain richer approval
information, but it MUST NOT be added as undeclared v2 inter-repository payload fields.

## Target capabilities and operational activation

The compatibility unit freezes target capability semantics, including supported contract version,
target workflow interface, permitted task types and modes, `draft_pr_only: true`, concurrency
semantics, `delivery_id` branch and ownership semantics, and result behavior. Those immutable
capabilities are consumer requirements and target-side defense-in-depth gates.

Current enabled or disabled state is not part of the immutable compatibility unit. It is mutable
organization control-plane activation state owned and enforced by the `.github` router before
dispatch. A target adapter MUST NOT read historical activation from the pinned capability revision,
reject a routed request because that revision predates activation, or change activation. It still
fails closed on an unauthenticated or unauthorized caller, wrong target identity, incompatible
contract or schema, unsupported capability, invalid concurrency or delivery identity, non-draft
publication request, replay conflict, or ambiguous ownership.

## Result projection

After organization receiver validation, the source-issue projection records source issue, task ID
or locally bound approved-task identity, correlation ID, delivery ID, target, execution status,
validation result, test result, draft-PR URL when present, sanitized failure category/message,
safe workflow URL, completion time, duplicate-reuse status, and ambiguous-result status. It
distinguishes router admission, delivery acceptance, target execution, result transport, receiver
validation, and final execution outcome.

## `FR-CIV-01` — repository-local, no-Codex conformance plan

Normal interface CI SHALL use deterministic local doubles and no organization-owned fixture files
beyond those actually published. Planned cases are:

| Local case | Required assertion | Trace |
| --- | --- | --- |
| `PT-MVP-APPROVED`, `PT-MVP-NONAPPROVED`, `PT-MVP-QUEUED` | construct an approved canonical task; reject every non-approved status; specifically reject queued admission | FR-GOV-03, FR-RTE-01/02 |
| `PT-MVP-MATERIAL-EDIT` | material edit produces a new task ID and requires new approval | FR-GOV-04 |
| `PT-MVP-VERIFY`, `PT-MVP-IMPLEMENT` | router call explicitly supplies each execution mode | FR-RTE-02 |
| `PT-MVP-TARGETS` | exercise target selections; the router enforces current activation and a dispatched target validates its exact identity and immutable capabilities | FR-CLS-03, FR-RTE-02 |
| `PT-MVP-DISABLED`, `PT-MVP-UNKNOWN` | router-side inactive and unknown selections fail closed without dispatch; target tests do not recreate activation policy | FR-RTE-02, NFR-INT-02 |
| `PT-MVP-DUP-DISPATCH`, `PT-MVP-RETRY-ID` | duplicate has one visible effect and retry preserves delivery ID | FR-RTE-03/04, NFR-REL-01/03 |
| `PT-MVP-OWNERSHIP`, `PT-MVP-CREATE-RACE` | lookup uses deterministic branch identity plus `ai-sdlc-delivery-id`; a create conflict requeries and uniquely reuses one owned open draft PR | FR-TGT-02, FR-RTE-03, NFR-REL-01/03 |
| `PT-MVP-CREATE-RACE-NONE`, `PT-MVP-CREATE-RACE-AMBIGUOUS` | post-conflict requery with no conclusive owner enters reconciliation; multiple/conflicting owners quarantine without another create or mutation | FR-TGT-02, FR-RTE-03/04, NFR-REL-01/03 |
| `PT-MVP-RESULT`, `PT-MVP-RESULT-DUP`, `PT-MVP-RESULT-CONFLICT` | valid projection; identical duplicate no-op; conflicting duplicate quarantined | FR-OUT-01 |
| `PT-MVP-RESULT-DELAY`, `PT-MVP-ROUTER-REJECT`, `PT-MVP-RECEIVER-FAILURE` | reconcile missing/delayed result; safely project router rejection and receiver transport failure without treating acknowledgement as execution success | FR-RTE-04, FR-OUT-01 |
| `PT-MVP-NOEFFECT` | no Codex call, real branch, or real pull request | FR-CIV-01, NFR-TST-02, NFR-AI-02 |

The cases align to the scenario list in
`tests/fixtures/mvp-v2/manifest.json@c6090e5bbadcc2102a1cb91875466e9decdada1e` (`TC-MVP-CI-001`).
That compatibility baseline contains the complete executable input and expected-output fixture
oracle. Consumer CI must execute it without locally redefining its schema, status vocabulary,
activation behavior, result semantics, or expected outcomes and without real Codex or GitHub
publication effects.

## External dependencies and readiness

The result receiver contract and complete executable `TC-MVP-CI-001` oracle are organization-owned
parts of the merged compatibility baseline. They are consumed directly and are not redesigned or
reimplemented here. Mutable target activation, credentials, and any live operational readiness
decision remain organization-owned external concerns; documentation or compatibility pinning does
not enable a target. None blocks implementation or deterministic conformance testing of this
repository's local consumer responsibilities.

No new repository-owned requirement or architecture decision remains before implementation can
begin. Cross-repository compatibility and successful live result return remain unproven.

The checked-in `route-approved-task.yml` and `codex-execute.yml` predate this baseline and are
nonconforming implementation inputs to the first implementation issue, not normative compatibility
evidence. In particular, their legacy tag/package consumption, artifact transport inputs, live
label recheck, and result handling MUST NOT be copied forward. Readiness here means the replacement
can be implemented without choosing a new interface or lifecycle rule; it does not claim that the
current workflows already conform.
