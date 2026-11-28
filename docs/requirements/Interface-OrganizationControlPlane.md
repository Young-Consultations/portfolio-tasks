# Interface Requirements — organization control plane

## Compatibility recovery boundary

The selected payload is `ai-sdlc-contract/v2`. The approved 2.3.2 compatibility
evidence retains its schema and fixture baseline derived from
corrected recovery commit `e27b8a541afbd27b4be5606a19ffa43637ad312a`. Historical commit
`c6090e5bbadcc2102a1cb91875466e9decdada1e` remains immutable 2.3.0 evidence and MUST NOT be
amended or retagged.

Exact closed schemas and shared fixtures are vendored here only for deterministic validation and
bound by their approved Git blob identities. The organization remains their owner.
The V5.10 source router migration selects the published immutable
`ai-sdlc-v5.0.0` tag at `3cce887fc393fa80ed8f79308ca9b9c7241ce622` after separately
reviewed merge. Absence of the selected immutable tag fails closed; a mutable
`main` fallback is forbidden. Prior 4.0.0 attestation remains historical.
The portfolio repository's **disabled** local target still retains its
separately pinned historical 2.3.2 compatibility receiver; that local target
is not a second enabled dispatch path. This source pin change does not
constitute deployed Runtime Preflight or REAL acceptance.

## Router

Reusable workflow:
`Young-Consultations/.github/.github/workflows/codex-router.yml@ai-sdlc-v5.0.0`.

| Kind | Name | Contract |
| --- | --- | --- |
| input | `task_payload` | Required string containing complete canonical `task-contract/v2` JSON. |
| input | `execution_mode` | Explicit `verify` or `implement`; the source always supplies it. |
| secret | `CODEX_ROUTER_TOKEN` | Router credential with no target publication authority. |
| output | `correlation_id` | End-to-end observability identity. |
| output | `delivery_id` | At-least-once idempotency identity. |
| output | `failure_category` | Safe failure category. |
| output | `diagnostic_summary` | Sanitized diagnostic summary. |
| output | `concurrency_group` | Routing transport concurrency value. |

The caller MUST grant `actions: read` because the reusable router requests that permission.
The source validates its constructed object against the exact local copy of the approved task
schema before calling the router. Only `status: approved`, `executor: codex`, no unresolved
dependencies, safe sensitivity, and exactly one known target are source-admissible. The router
revalidates the schema and current mutable activation before dispatch. `queued` is a source
projection after successful admission and can never authorize a route.

Delivery is at least once with idempotent visible effects. The same logical retry preserves
`delivery_id`; uncertainty requires reconciliation rather than blind redispatch. Router success
is admission, not target acceptance, result validation, or execution success.

## Admission journal

After successful routing, the source writes a canonical marker:

`<!-- ai-sdlc-admission:v2 {canonical JSON} -->`

The JSON contains exactly `contract_version`, `delivery_id`, `correlation_id`,
`source_issue`, and `target_repository`. The source accepts an identical retry as a no-op and
fails closed on a conflicting binding. The organization receiver recognizes markers only from its
immutable trusted-journal-author policy.

## Result receiver

Reusable workflow:
`Young-Consultations/.github/.github/workflows/codex-result-receiver.yml@ai-sdlc-v2.3.2`.

| Kind | Name | Contract |
| --- | --- | --- |
| input | `execution_result` | Required canonical `execution-result/v2` JSON string. |
| input | `source_issue` | Required `owner/repository#number` binding. |
| secret | `CODEX_RESULT_TOKEN` | Result-only source-repository credential. |
| output | `accepted` | Receiver acceptance, never execution-success authority. |
| output | `delivery_id` | Validated delivery identity. |
| output | `correlation_id` | Validated correlation identity. |
| output | `execution_status` | Canonical target outcome. |
| output | `failure_category` | Safe failure category. |
| output | `diagnostic_summary` | Sanitized diagnostic summary. |

Trusted journal-author policy is immutable organization-owned configuration. A target MUST NOT
define, inherit, or supply it. After validating schema, caller/target identity, the unique admission
binding, and replay state, the receiver forwards exactly
`{"source_issue": ..., "execution_result": ...}` to the source repository using
`repository_dispatch` event `ai-sdlc-execution-result-v2`.

The source authenticates the receiver dispatch identity, repeats exact result-schema and
admission-binding validation, projects identical results once, and quarantines conflicts. For the
5.0.0 source path, repository variable `PORTFOLIO_RESULT_SENDERS` must
exactly authorize the immutable organization result-writer identity
`ai-sdlc-result-writer[bot]`. After the source PR is merged, the
organization's deployed Runtime Preflight shall independently verify the
actual `portfolio-tasks@main` router-job pin equals `ai-sdlc-v5.0.0`,
the registered target, secret metadata and the result sender binding.
This source migration does **not** claim preflight has already passed. The target never directly invokes source
projection and never receives a portfolio result-write token.


The source-owned missing-result reconciliation workflow loads the exact
immutable V5 trust policy and retains reviewed historical admissions
`ai-sdlc-v3.0.1`, `ai-sdlc-v3.0.2`, `ai-sdlc-v3.0.3`, `ai-sdlc-v3.1.0`,
`ai-sdlc-v4.0.0`, adding `ai-sdlc-v5.0.0`. Historical source recovery is
separate from the V5 receiver's V5-only admission compatibility. V5 recovery
requires exact consulting adapter ref and commit, correlated failed-run evidence,
and no trusted terminal receipt or forwarding evidence. Reconciliation cannot
replay a terminal delivery or authorize new cost-bearing execution. The allowlist is static
source policy, not an operator input; unreviewed releases fail closed.

## Approval data boundary

`portfolio-tasks` owns human approval truth and may retain richer internal audit evidence. The
closed v2 inter-repository task contains only schema-declared fields. The schema-safe `task_id`
binds all authoritative source material, target, mode, executor, dependencies, and sensitivity.
Every such change creates a new identity and requires new human approval.

V5 source projection recomputes the immutable receiver visible effect and requires
an exact trusted receipt. Managed-draft equivalence does not replace exact receipt
validation. Retired maintenance issue #176 and smoke reservations are denied.
