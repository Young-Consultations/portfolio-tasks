# Interface Requirements — target repositories

## Adapter contract and separation of authority

Every eventual target adapter is `.github/workflows/codex-execute.yml`. It is reached only through
the organization router; it cannot admit portfolio work directly, approve its own work, or bypass
the router. This applies when `Young-Consultations/portfolio-tasks` acts as both the source-system
owner and, through a separately bounded target adapter, the selected execution target.

The target consumes the canonical execution input validated against
`contracts/execution-input.schema.json@c6090e5bbadcc2102a1cb91875466e9decdada1e` and produces a
separately transported result validated against
`contracts/execution-result.schema.json@c6090e5bbadcc2102a1cb91875466e9decdada1e`. These direct,
immutable files are authoritative; this repository MUST NOT invent fields, copy schemas, or assume
a published contract package.

## Exact reusable-workflow inputs

| Input | Contract |
| --- | --- |
| `execution_input_json` | Required string containing the complete canonical `execution-input/v2` JSON. |
| `concurrency_group` | Required concurrency value supplied by the routing transport. |

The obsolete name `execution_input` MUST NOT be used. The target sends its canonical result
separately through the pinned result receiver and does not return the result directly to the
router.

## Capability and activation boundary

The pinned compatibility unit owns immutable target capabilities such as the supported contract,
workflow interface, task types and modes, draft-only policy, concurrency, delivery and ownership
semantics, and result behavior. Current enabled or disabled state is separate mutable `.github`
control-plane activation state. The organization router enforces that state before dispatch.

The target MUST NOT consume historical activation from the pinned compatibility unit, reject a
request solely because its compatibility revision predates activation, or alter activation. An
authenticated router call does not waive target-local validation of caller authority, exact target
identity, schema and format, immutable capabilities, draft-only policy, transport concurrency,
delivery identity, payload digest, idempotency, or publication ownership.

## Required target behavior

* Validate the shared input and target-local policy before side effects.
* Require the routed target identity, permitted task type, `draft_pr_only: true`, and router-supplied
  concurrency group; treat task and AI content as untrusted.
* Use `delivery_id` as branch identity and idempotency key, preserve it on retries, mark ownership
  with `ai-sdlc-delivery-id`, and report terminal reuse as `duplicate-reused`.
* Before publication, query deterministic branch identity and the ownership marker. If branch or PR
  creation reports an already-existing resource, conflict, timeout, or ambiguous response, requery
  both identities before retrying. Reuse only exactly one matching open draft PR; no match enters
  reconciliation, and multiple or conflicting matches are ambiguous and fail closed. A create race
  MUST NOT create a second PR or overwrite, close, or adopt an unverified publication.
* Create or reuse at most one draft PR and report validation/tests honestly. Never approve, mark
  ready, merge, release, deploy, or perform production operations.
* Send the canonical result through the organization result receiver with `source_issue`; do not
  treat transport acknowledgement as final success.
* Fail closed on wrong target, invalid schema or format, prohibited task type or mode, incompatible
  version, unauthorized caller, invalid concurrency or delivery identity, conflicting replay,
  sensitive or ambiguous request, or non-draft publication request. Operational inactivity and
  unknown route selection are router-side failures and do not create target-side activation policy.

These are consumer requirements and do not claim that any sibling repository implements or
conforms to the adapter.
