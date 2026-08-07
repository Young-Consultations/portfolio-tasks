# Interface Requirements — organization control plane

## Frozen compatibility boundary

The next MVP consumes `Young-Consultations/.github` release `2.2.0`, payload version
`ai-sdlc-contract/v2`, at the full immutable SHA
`f2491872976a4dcc1633997954c03c07cbc4fced`. All workflow `uses:` references and direct schema-file
consumption MUST use that SHA. The compatibility-unit file list and registry snapshot are recorded
in [`../releases/next-mvp.md`](../releases/next-mvp.md). This repository consumes but does not copy,
extend, or claim ownership of the closed organization schemas.

## Router

Reusable workflow:
`Young-Consultations/.github/.github/workflows/codex-router.yml@f2491872976a4dcc1633997954c03c07cbc4fced`.

| Kind | Name | Contract |
| --- | --- | --- |
| input | `task_payload` | Required string containing complete canonical `task-contract/v2` JSON. |
| input | `execution_mode` | Workflow-optional `verify` or `implement`, default `implement`; `portfolio-tasks` MUST always supply it explicitly. |
| secret | `CODEX_ROUTER_TOKEN` | Router credential. |
| output | `execution_result` | Router workflow output. |
| output | `correlation_id` | End-to-end observability identity. |
| output | `delivery_id` | At-least-once idempotency key. |
| output | `failure_category` | Safe failure category. |
| output | `diagnostic_summary` | Sanitized diagnostic summary. |
| output | `concurrency_group` | Routing transport concurrency value. |

The complete canonical task is validated directly against
`contracts/task-contract.schema.json@f2491872976a4dcc1633997954c03c07cbc4fced`. Only
`status: approved` is admissible. `queued` is a post-admission source projection and MUST be
rejected if submitted to the router. At minimum, dispatch also requires
`contract_version: ai-sdlc-contract/v2`, `executor: codex`, `dependencies: []`, and exactly one
enabled registry target. Summaries here are subordinate to the schema.

Delivery is at least once with idempotent visible effects. `delivery_id` is the idempotency key and
MUST remain stable on retry; `correlation_id` is the end-to-end observability identity. Router
admission is not target acceptance, result validation, or execution success. Rejection, timeout,
and ambiguity retain the last proven state and enter reconciliation rather than blind redispatch.

## Result receiver

Reusable workflow:
`Young-Consultations/.github/.github/workflows/codex-result-receiver.yml@f2491872976a4dcc1633997954c03c07cbc4fced`.

| Kind | Name | Contract |
| --- | --- | --- |
| input | `execution_result` | Required canonical `execution-result/v2` JSON string. |
| input | `source_issue` | Required `owner/repository#number` binding. |
| secret | `CODEX_RESULT_TOKEN` | Result transport credential. |
| output | `accepted` | Receiver validation decision. |
| output | `delivery_id` | Validated delivery identity. |
| output | `correlation_id` | Validated correlation identity. |
| output | `execution_status` | Canonical execution status. |
| output | `failure_category` | Safe failure category. |
| output | `diagnostic_summary` | Sanitized diagnostic summary. |

The checked-in receiver is an approved, fail-closed interface skeleton; it does not accept live
results. Consumer documentation and implementation planning MAY depend on this frozen interface,
but a successful live result-return test is currently impossible. Receiver implementation remains
an organization-owned external dependency. `portfolio-tasks` MUST NOT redesign or locally replace
it, and its current fail-closed behavior is not interpreted as consumer-contract incompatibility.

After receiver validation, `portfolio-tasks` owns source-issue projection as specified in the MVP
release baseline. Identical duplicate results are no-ops; conflicting duplicates are quarantined;
missing or delayed results require reconciliation.

## Approval data boundary

`portfolio-tasks` owns human approval truth and may keep rich internal audit evidence. The closed v2
inter-repository payload MUST contain only schema-declared fields. Approval ID, revision digest,
approver, approval timestamp, revocation record, and freshness metadata are deferred to v3 and MUST
NOT be injected as v2 extensions. Every material change creates a new `task_id` and requires new
human approval.
