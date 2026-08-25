# Interface Requirements — target repositories

## Adapter contract and separation of authority

Every conforming target owns one `.github/workflows/codex-execute.yml` entry point. The
organization router invokes it only after source approval and router admission. A target cannot
approve portfolio work, bypass the router, change activation, or acquire source-system authority.
This separation still applies when `portfolio-tasks` is both source owner and selected target.

The target validates exact local copies of the approved
`execution-input.schema.json` and `execution-result.schema.json` from
`Young-Consultations/.github@e27b8a541afbd27b4be5606a19ffa43637ad312a`. Git blob identities
in the conformance pin prove byte equality. These copies are compatibility inputs, not local schema
ownership or permission to extend the closed contract.

## Exact target invocation

The entry point is `workflow_dispatch`, not `workflow_call`, and declares exactly two inputs:

| Input | Contract |
| --- | --- |
| `execution_input_json` | Required string containing the complete canonical `execution-input/v2` JSON. |
| `concurrency_group` | Required transport identity that exactly matches the canonical payload. |

No artifact ID, run ID, alternate input name, compatibility alias, or direct router-return value is
supported. The target sends its result separately through
`codex-result-receiver.yml@ai-sdlc-v2.3.2`.

## Capability and activation boundary

The immutable compatibility registry owns target workflow identity, contract version, allowed task
types and modes, draft-only policy, concurrency, delivery/ownership semantics, environment name,
and result behavior. Mutable enabled/disabled state remains organization control-plane state
enforced before dispatch.

The portfolio target permits `automation`, `backlog-governance`, `ci-cd`, `documentation`,
and `repository-maintenance`; `verify` and `implement`; `draft_pr_only: true`; and
`max_parallel: 1`. It uses the `portfolio-tasks-codex-production` environment boundary.
A routed request repeats all immutable local checks. It MUST NOT recreate or alter activation.

## Required target behavior

- Authenticate the dispatch caller against a target-owned allowlist before side effects.
- Validate exact schema, repository identity, capability, mode, draft-only request, concurrency,
  delivery identity, requested branch, and payload digest.
- Derive the only managed branch from `delivery_id` and bind the draft with
  `ai-sdlc-delivery-id` plus the canonical payload SHA-256.
- Before Codex, observe both canonical branch existence and every PR on that branch. Reuse only one
  matching open draft. Reject an orphan branch, digest mismatch, non-draft, multiple PRs, or any
  inconsistent ownership as `ambiguous-rejected`.
- After a push/PR create race, repeat the same branch-plus-PR reconciliation. Never rerun Codex or
  force/adopt/overwrite an unverified publication.
- In `verify` mode, run validation without Codex or publication. In `implement` mode, give Codex
  only the AI credential and a workspace-write repository; give publication credentials only to
  the trusted publication adapter.
- Validate the candidate before committing. Publish no more than one branch and draft PR. Never
  self-approve, mark ready, merge, release, deploy, or perform production operations.
- Emit an exact canonical result for success and every safe failure category.
- Send only `execution_result`, `source_issue`, and `CODEX_RESULT_TOKEN` to the organization
  receiver. Never supply journal trust policy or a portfolio projection token.

## Deterministic conformance

A conforming target executes all 29 organization-owned `TC-MVP-CI-001` scenarios through the real
adapter seam with explicit traps for Codex, branch, commit, push, PR, merge, release, deployment,
production, and secret-output effects. Its report, pin, exact adapter files, and eventual immutable
adapter tag must bind without a recursive commit self-reference.

The portfolio report is accepted immutable evidence for the published `ai-sdlc-v2.3.2` unit. It
does not claim mutable activation, a successful controlled live receiver run, or production readiness.
