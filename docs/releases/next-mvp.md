# portfolio-tasks next-MVP recovery baseline

**Status:** issue 135 implementation baseline. Local source, target, and zero-effect conformance
work is complete; immutable publication, receiver deployment identity, and activation remain gated.

## Immutable compatibility recovery

The selected payload is `ai-sdlc-contract/v2`. The corrected organization compatibility candidate
is `Young-Consultations/.github@e27b8a541afbd27b4be5606a19ffa43637ad312a`, planned as patch
release `2.3.1`. The incompatible reviewed baseline
`c6090e5bbadcc2102a1cb91875466e9decdada1e` is preserved as historical 2.3.0 evidence; it MUST
NOT be amended or retagged.

The local non-recursive conformance pin binds:

- the candidate compatibility commit and fixture identity;
- exact Git blob identities for the three closed schemas and three shared fixture files;
- exact Git blob identities for the target workflow, real adapter, and executable harness; and
- an adapter revision derived from the canonical pin with `adapter_revision` set to null.

The authoritative record is
[`config/mvp-conformance-pin.json`](../../config/mvp-conformance-pin.json). Vendored schemas and
fixtures are byte-for-byte compatibility inputs for offline CI, not local contract ownership,
extensions, or alternate truth.

References to the organization router and receiver use the planned immutable tag
`ai-sdlc-v2.3.1`. That tag and the corrected compatibility release do not yet exist; this
repository MUST stay disabled until reviewed evidence permits their publication and live
verification.

## Included and deferred requirements

**Included:** `FR-INT-01`, `FR-INT-02`, `FR-INT-03`, `FR-CLS-01`, `FR-CLS-02`,
`FR-CLS-03`, `FR-GOV-02`, `FR-GOV-03`, `FR-GOV-04`, `FR-RTE-01`, `FR-RTE-02`,
`FR-RTE-03`, `FR-RTE-04`, `FR-OUT-01`, `FR-TGT-01`, `FR-TGT-02`, `FR-CIV-01`,
`NFR-REL-01`, `NFR-REL-02`, `NFR-REL-03`, `NFR-SEC-01`, `NFR-SEC-02`,
`NFR-SEC-05`, `NFR-AUD-01`, `NFR-OBS-02`, `NFR-MNT-01`, `NFR-MNT-02`,
`NFR-INT-01`, `NFR-INT-02`, `NFR-USA-02`, `NFR-TST-01`, `NFR-TST-02`,
`NFR-AUT-01`, `NFR-AI-01`, and `NFR-AI-02`.

**Deferred:** `FR-CLS-04`, `FR-GOV-01`, `FR-OUT-02`, `FR-OUT-03`, `FR-PRJ-01`,
`FR-PRJ-02`, and `FR-RPT-01`. Unlisted NFRs remain later-release constraints and are not
waived or claimed satisfied.

## Source-owned approval and admission

`portfolio-tasks` owns source issue identity, intake, human approval truth, material-change
invalidation, exact canonical task construction, explicit mode selection, routing initiation,
admission journaling, result projection, and reconciliation.

The source constructs exactly the fields declared by `task-contract/v2`:
`contract_version`, `task_id`, `source_issue`, `status`, `executor`, `project`,
`priority`, `task_type`, `target_repository`, `parallel_safe`, `dependencies`, `risk`,
`scope`, `instructions`, and `created_by`. Unknown, missing, or extra fields fail closed.

The schema-safe `task_id` binds the source issue and the complete authoritative revision:
task material, target, execution mode, executor, dependencies, and sensitivity. Therefore any
material routing-authority change requires a new task identity and fresh human approval.
Only `status: approved`, `executor: codex`, no unresolved dependencies, and
`not-sensitive` are admissible. Issue-form task types are explicitly mapped to the canonical
vocabulary; obsolete or inferred values fail closed.

The source workflow grants `actions: read` because the called organization router requests that
permission. A successful router result is journaled as exactly one unique
`ai-sdlc-admission:v2` JSON binding containing contract, delivery, correlation, source issue, and
target. Only after that durable record is the source projected to queued.

## Target-owned execution

The sole target entry point is `workflow_dispatch` with exactly two string inputs:
`execution_input_json` and `concurrency_group`. `workflow_call`, artifact/run-ID transport,
old aliases, and the former duplicate Python adapter/conformance paths are not supported.

The target independently validates the exact execution schema, authenticated caller, portfolio
repository identity, allowed task types, mode, draft-only policy, concurrency, delivery branch, and
payload digest. It reconciles both the canonical branch and matching managed pull requests before
Codex and after any create race. Only exactly one matching open draft can be reused; an orphan
branch, mismatched digest, non-draft PR, multiple owners, or uncertain race is rejected as
ambiguous before paid execution or another publication.

The AI runtime receives only task instructions, repository context, and validation policy. It has
no publication or result credential. The workflow validates the candidate, then separately uses a
publication credential to create at most one branch and draft PR. It cannot approve, mark ready,
merge, release, deploy, or perform production operations.

## Receiver and source projection

The target passes only `execution_result`, `source_issue`, and `CODEX_RESULT_TOKEN` to the
organization receiver. Trusted journal-author policy is immutable organization configuration and
MUST NOT be supplied by a target.

After schema, caller, admission, and replay validation, the organization receiver forwards
`{"source_issue": ..., "execution_result": ...}` to the source repository using
`repository_dispatch` event `ai-sdlc-execution-result-v2`. The source authenticates that
dispatch identity, repeats exact result-schema and admission-binding validation, projects an
identical result once, and quarantines conflicting evidence. The target never directly invokes the
source projection workflow and never receives a portfolio result-write credential. Receiver
acceptance is transport evidence, not execution success.

## Deterministic evidence

`scripts/run_tc_mvp_ci_001.py` executes the complete organization-owned 2.3.0 fixture oracle
against the real repository adapter seam. The checked report records:

- 29 of 29 scenarios passing;
- 22 scenarios invoking the portfolio adapter;
- exact compatibility and target-file pin bindings; and
- zero real Codex, branch, commit, push, pull-request, merge, release, deployment, production, or
  secret-output effects.

The report is
[`.ai-sdlc/conformance/tc-mvp-ci-001.json`](../../.ai-sdlc/conformance/tc-mvp-ci-001.json).
Normal CI regenerates it and fails on drift. This establishes deterministic adapter compatibility,
not tag existence, receiver deployment, activation, or production readiness.

## Remaining gated sequence

1. Review and merge this portfolio recovery without enabling the target.
2. Apply and review the same canonical adapter and complete oracle evidence in Slugger.
3. Record reviewed receiver deployment identities and prove live receiver forwarding.
4. Publish one immutable adapter tag for each conforming target.
5. Bind exact tag-to-commit and report-to-pin identities in the corrected registry.
6. Publish the corrected 2.3.1 compatibility release.
7. Run one-at-a-time review-state compatibility checks.
8. Only then return to issue 117 and change mutable activation for one low-blast-radius target.

No local green check may skip or replace these gates.
