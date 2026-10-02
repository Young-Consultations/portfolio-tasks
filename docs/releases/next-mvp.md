# portfolio-tasks next-MVP baseline

**Status:** approved MVP scope with current source routing on published
`ai-sdlc-v3.0.3`. The 2.3.2 recovery/compatibility sequence below is
historical target evidence. Initial live-path verification completed on 2.4.5
through fresh issue #154; issue #156 exposed result-writer defect #83; issue
#159 then exposed DEF-0073 at the receiver and DEF-0086 when an unchanged retry
could not reuse its preserved 3.0.1 admission. Published 3.0.3 passed deployed
Runtime Preflight run 36867504568 and immutable REAL readiness preflight run
36867939797 before source cutover. Fresh #159 then completed full REAL
acceptance: the first delivery produced one managed draft PR #82 and one source
terminal projection, and the unchanged second delivery returned
`duplicate-reused` for the same delivery/branch/PR before Codex with no second
receiver/source visible effect. The current source router selection is governed
by the [3.0.3 consumer record](3.0.3.md) and
[organization control-plane interface](../requirements/Interface-OrganizationControlPlane.md).
The selected v2 payload, requirement scope, and immutable schema/fixture
identities remain in force.

## Immutable compatibility baseline

The selected payload remains `ai-sdlc-contract/v2`. The 2.3.2 compatibility unit is immutable in `Young-Consultations/.github`, pointing to commit `5738ace3ee90dde11336f8f8099e64e5645f7139`.

The historical reviewed baseline `c6090e5bbadcc2102a1cb91875466e9decdada1e` is rejected 2.3.0-era evidence and MUST NOT be restored as the active baseline. The 2.3.1 recovery commit `e27b8a541afbd27b4be5606a19ffa43637ad312a` is also historical. The 2.3.2 patch records corrected immutable compatibility evidence bindings for all four core repositories.

The local non-recursive conformance pin binds:

- the approved compatibility and fixture identity;
- exact Git blob identities for the three closed schemas and three shared fixture files;
- exact Git blob identities for the target workflow, real adapter, executable harness, validator, and required contract-test files; and
- an adapter revision derived from the canonical pin without recursively embedding its containing commit SHA.

The authoritative local record is [`config/mvp-conformance-pin.json`](../../config/mvp-conformance-pin.json). Vendored schemas and fixtures remain byte-for-byte, digest-pinned offline compatibility inputs only. Their presence does not transfer organization contract ownership or permit local extension.

The organization registry now records immutable adapter tags/commits and committed report digests for all four core targets with `status: pass` and `activation_evidence_sufficient: true`. Current enabled/disabled state remains separate mutable `.github` control-plane state and is not part of target-side compatibility semantics.

Mutable target activation is separate organization control-plane state. The reviewed current state
enables only `Young-Consultations/consulting-playbook`; `.github`,
`portfolio-tasks`, and `slugger` remain disabled as targets. Activation changes do not require
repinning source consumers solely because an enabled/disabled boolean changes.

## Included and deferred requirements

**Included:** `FR-INT-01`, `FR-INT-02`, `FR-INT-03`, `FR-CLS-01`, `FR-CLS-02`,
`FR-CLS-03`, `FR-GOV-02`, `FR-GOV-03`, `FR-GOV-04`, `FR-RTE-01`, `FR-RTE-02`,
`FR-RTE-03`, `FR-RTE-04`, `FR-OUT-01`, `FR-TGT-01`, `FR-TGT-02`, `FR-CIV-01`,
`NFR-REL-01`, `NFR-REL-02`, `NFR-REL-03`, `NFR-SEC-01`, `NFR-SEC-02`,
`NFR-SEC-05`, `NFR-AUD-01`, `NFR-OBS-02`, `NFR-MNT-01`, `NFR-MNT-02`,
`NFR-INT-01`, `NFR-INT-02`, `NFR-USA-02`, `NFR-TST-01`, `NFR-TST-02`,
`NFR-AUT-01`, `NFR-AI-01`, and `NFR-AI-02`.

**Deferred:** `FR-CLS-04`, `FR-GOV-01`, `FR-OUT-02`, `FR-OUT-03`, `FR-PRJ-01`,
`FR-PRJ-02`, and `FR-RPT-01`. Unlisted NFRs remain later-release constraints and are not waived or claimed satisfied.

## Source-owned approval and admission

`portfolio-tasks` owns source issue identity, intake, human approval truth, material-change invalidation, exact canonical task construction, explicit mode selection, routing initiation, admission journaling, result projection, and reconciliation.

The source constructs exactly the fields declared by `task-contract/v2`: `contract_version`, `task_id`, `source_issue`, `status`, `executor`, `project`, `priority`, `task_type`, `target_repository`, `parallel_safe`, `dependencies`, `risk`, `scope`, `instructions`, and `created_by`. Unknown, missing, or extra fields fail closed.

The schema-safe `task_id` binds the source issue and complete authoritative revision: task material, target, execution mode, executor, dependencies, and sensitivity. Any material routing-authority change requires a new task identity and fresh human approval. Only `status: approved`, `executor: codex`, no unresolved dependencies, and `not-sensitive` are admissible.

The source workflow grants the least privilege required by the pinned organization router. A successful router result is journaled as one unique `ai-sdlc-admission:v2` JSON binding containing contract, delivery, correlation, source issue, and target. Only after that durable record is the source projected to queued.

## Target-owned execution

The sole target entry point is `workflow_dispatch` with exactly two string inputs: `execution_input_json` and `concurrency_group`. `workflow_call`, artifact/run-ID transport, old aliases, and duplicate legacy adapter/conformance paths are not supported.

The target independently validates the exact execution schema, authenticated caller, portfolio repository identity, allowed task types, mode, draft-only policy, concurrency, delivery branch, and payload digest. It reconciles both the canonical branch and matching managed pull requests before Codex and after create races. Only exactly one matching owned open draft may be reused. Orphan branches, mismatched digests, non-draft PRs, multiple owners, or uncertain races fail closed before paid execution or a second publication effect.

The AI runtime receives task instructions, repository context, and validation policy but no publication or result credential. Validation completes before a separately scoped publication credential can create at most one branch and draft PR. Automation cannot approve, mark ready, merge, release generated work, deploy, or perform production operations.

## Receiver and source projection

The target passes only the bounded result payload/source identity and result-delivery credential required by the organization receiver. Trusted journal-author policy is immutable organization-owned configuration and MUST NOT be supplied by a target.

After schema, caller, admission, and replay validation, the organization receiver forwards the bounded canonical result to the source repository. The source authenticates the receiver event, repeats exact result-schema and admission-binding validation, projects an identical result once, and quarantines conflicting evidence. Receiver acceptance is transport evidence, not execution success.

## Deterministic evidence

`scripts/run_tc_mvp_ci_001.py` executes the complete organization-owned `TC-MVP-CI-001` fixture oracle version `2.3.0` against the real repository adapter seam. The current accepted report records:

- 29 of 29 scenarios passing;
- 22 scenarios invoking the portfolio adapter;
- exact compatibility, shared-file, workflow, adapter, harness, validator, and required contract-test bindings; and
- zero real Codex, branch, commit, push, pull-request, merge, release, deployment, production, or secret-output effects.

The report is [`.ai-sdlc/conformance/tc-mvp-ci-001.json`](../../.ai-sdlc/conformance/tc-mvp-ci-001.json). Normal CI regenerates/validates the evidence and fails on drift. This proves deterministic adapter compatibility, not target activation or organization MVP acceptance.

## Historical recovery sequence and current completion state

The former 2.3.x recovery sequence led to the 2.4.5 initial-live path and is retained
only as history. Current disposition:

1. Issue #135 recovery is complete and its older release identities remain immutable evidence.
2. Issue #117 completed the first-target activation decision; only `consulting-playbook` is enabled.
3. Issue #119's production-shaped path was exercised by fresh issue #154 on published 2.4.5,
   producing one managed draft PR and accepted receiver/source projection.
4. Same-delivery issue #156 exposed organization control-plane defect #83; published 3.0.1
   repaired the result-writer identity/preflight path.
5. Issue #159 then exposed DEF-0073 at the receiver; published 3.0.2 repaired
   that split-release compatibility boundary.
6. The preserved 3.0.1 admission on unchanged #159 retry then exposed DEF-0086.
   Published 3.0.3 and immutable `codex-adapter-v3.0.3` repair cross-release
   admission reuse. Deployed Runtime Preflight run 36867504568 and immutable
   REAL readiness preflight run 36867939797 passed before this source cutover.
7. Issue #120 completed final authority/context reconciliation across the four repositories.
8. Fresh #159 completed corrected terminal delivery and unchanged same-delivery
   redelivery/idempotency evidence: first source route 36911277900, target/receiver
   36911342397, source projection 36911478182, second source route 36913373900,
   and second target/receiver 36913463403.
9. Issue #121 remains open only for disposition of any remaining unacceptable
   MVP-risk defects and the final human MVP acceptance decision.

No local green check may substitute for the remaining human #121 decision. Historical 2.3.0/2.3.1/2.3.2 records remain
evidence, not current source execution instructions.
