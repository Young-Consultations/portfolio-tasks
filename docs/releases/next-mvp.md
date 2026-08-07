# portfolio-tasks next-MVP baseline

**Status:** documentation and interface baseline; ready for repository implementation planning.

## Immutable organization compatibility unit

This repository consumes release `2.2.0` and payload version `ai-sdlc-contract/v2` from
`Young-Consultations/.github` at the immutable reference
`f2491872976a4dcc1633997954c03c07cbc4fced` (the **compatibility SHA**). The compatibility unit is:

* `release/release-manifest.json`
* `docs/interfaces/mvp-v2-compatibility.md`
* `docs/releases/next-mvp.md`
* `config/codex-repositories.json`
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
`contracts/task-contract.schema.json@f2491872976a4dcc1633997954c03c07cbc4fced`. The subordinate
MVP dispatch summary is: `contract_version` is `ai-sdlc-contract/v2`, `status` is `approved`,
`executor` is `codex`, `dependencies` is `[]`, and `target_repository` is exactly one enabled
registry target.

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

## Registry snapshot

| Target | Enabled | Permitted task types |
| --- | --- | --- |
| `Young-Consultations/.github` | No | `ci-cd`, `documentation`, `repository-maintenance`, `testing` |
| `Young-Consultations/portfolio-tasks` | Yes | `automation`, `backlog-governance`, `ci-cd`, `documentation`, `repository-maintenance` |
| `Young-Consultations/slugger` | No | `automation`, `bug-fix`, `documentation`, `feature`, `testing` |
| `Young-Consultations/consulting-playbook` | No | `automation`, `documentation`, `feature`, `testing` |

All entries use `contract_version: ai-sdlc-contract/v2`, `draft_pr_only: true`,
`branch_identity: delivery_id`, `ownership_marker: ai-sdlc-delivery-id`, and
`terminal_reuse_status: duplicate-reused`. Disabled and unknown targets fail closed. Only an
organization-controlled decision can enable a disabled target.

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
| `PT-MVP-TARGETS` | exercise all four selections; only the enabled registry entry can admit | FR-CLS-03, FR-RTE-02 |
| `PT-MVP-DISABLED`, `PT-MVP-UNKNOWN` | disabled and unknown targets fail closed | FR-RTE-02, NFR-INT-02 |
| `PT-MVP-DUP-DISPATCH`, `PT-MVP-RETRY-ID` | duplicate has one visible effect and retry preserves delivery ID | FR-RTE-03/04, NFR-REL-01/03 |
| `PT-MVP-RESULT`, `PT-MVP-RESULT-DUP`, `PT-MVP-RESULT-CONFLICT` | valid projection; identical duplicate no-op; conflicting duplicate quarantined | FR-OUT-01 |
| `PT-MVP-RESULT-DELAY`, `PT-MVP-ROUTER-REJECT`, `PT-MVP-RECEIVER-CLOSED` | reconcile missing/delayed result; safely project router rejection; expect receiver fail-closed response | FR-RTE-04, FR-OUT-01 |
| `PT-MVP-NOEFFECT` | no Codex call, real branch, or real pull request | FR-CIV-01, NFR-TST-02, NFR-AI-02 |

The cases align to the scenario list in
`tests/fixtures/mvp-v2/manifest.json@f2491872976a4dcc1633997954c03c07cbc4fced` (`TC-MVP-CI-001`).
That release does not contain executable input and expected-output files for every failure,
duplicate, timeout, and ambiguity scenario. Local fixtures may be implemented but are not
organization-owned canonical fixtures; full shared-fixture conformance is not claimed.

## External dependencies and readiness

The frozen result-receiver interface is safe to plan against, but its current implementation is an
approved fail-closed skeleton and cannot accept a successful live return. Its implementation is an
organization-owned external dependency, not a reason to redesign or locally replace it and not an
incompatibility in this consumer contract. Other external dependencies are publication of complete
executable expected-output fixtures for `TC-MVP-CI-001`, creation of the declared immutable release
tag, and organization-controlled enablement of disabled targets. None blocks this repository's
documentation alignment or implementation of its local consumer responsibilities. Live
end-to-end enablement remains dependent on the receiver and applicable target enablement.

No new repository-owned requirement or architecture decision remains before implementation can
begin. Cross-repository compatibility and successful live result return remain unproven.
