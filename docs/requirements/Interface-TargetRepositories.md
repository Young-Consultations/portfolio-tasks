# Interface Requirements — target repositories

## Adapter contract and separation of authority

Every eventual target adapter is `.github/workflows/codex-execute.yml`. It is reached only through
the organization router; it cannot admit portfolio work directly, approve its own work, or bypass
the router. This applies when `Young-Consultations/portfolio-tasks` acts as both the source-system
owner and, through a separately bounded target adapter, the selected execution target.

The target consumes the canonical execution input validated against
`contracts/execution-input.schema.json@f2491872976a4dcc1633997954c03c07cbc4fced` and produces a
separately transported result validated against
`contracts/execution-result.schema.json@f2491872976a4dcc1633997954c03c07cbc4fced`. These direct,
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

## Registry behavior

The authoritative four-entry registry snapshot, task-type permissions, common policy values, and
enabled states are in [`../releases/next-mvp.md`](../releases/next-mvp.md). The only currently
enabled target is `Young-Consultations/portfolio-tasks`; `.github`, `slugger`, and
`consulting-playbook` fail closed until enabled by an organization-controlled decision. Unknown
targets also fail closed. Merely documenting or selecting a disabled target does not enable it.

## Required target behavior

* Validate the shared input and target-local policy before side effects.
* Require the routed target identity, permitted task type, `draft_pr_only: true`, and router-supplied
  concurrency group; treat task and AI content as untrusted.
* Use `delivery_id` as branch identity and idempotency key, preserve it on retries, mark ownership
  with `ai-sdlc-delivery-id`, and report terminal reuse as `duplicate-reused`.
* Create or reuse at most one draft PR and report validation/tests honestly. Never approve, mark
  ready, merge, release, deploy, or perform production operations.
* Send the canonical result through the organization result receiver with `source_issue`; do not
  treat transport acknowledgement as final success.
* Fail closed on wrong target, invalid schema, prohibited task type, incompatible version, unknown
  or disabled target, conflict, sensitive/ambiguous request, or non-draft publication request.

These are consumer requirements and do not claim that any sibling repository implements or
conforms to the adapter.
