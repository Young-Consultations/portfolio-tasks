# Error Handling Strategy

## Error taxonomy

| Category | Examples | Response |
| --- | --- | --- |
| Validation | missing field, invalid dependency, oversize payload | reject without effect; all actionable violations |
| Authorization/security | wrong actor/target, stale approval, sensitivity uncertainty | fail closed, audit, quarantine/escalate as appropriate; no automatic retry |
| Compatibility | unknown contract/config/taxonomy version | permanent block until compatible version or governed migration |
| Concurrency/conflict | issue revision race, same ID/different digest, multiple mirrors | no overwrite; reread or human reconciliation |
| Transient dependency | rate limit, temporary unavailable | bounded retry with backoff/jitter and same identity if safe |
| Ambiguous handoff | timeout after possible acceptance | mark uncertain; query/reconcile; never blind retry |
| Ordering/data integrity | stale/impossible/forged external event | duplicate no-op, stale audit-only, invalid/divergent quarantine |
| Target execution | local validation/test/tool failure | correlated result with checks actually run and safe diagnostics; no false success |
| Projection/reporting | Project write failure, stale read model | isolate from authority; show freshness/drift and reconcile |
| Internal defect | violated invariant/unclassified exception | stop affected unit, preserve safe evidence, alert; do not expose stack trace |

## Error contract and propagation

Application errors contain stable code, category, safe message, correlation, affected revision,
retryability, next action and optional evidence reference. Adapters translate provider failures at
the boundary. Domain policies return decisions/violations rather than throwing transport errors.
User views explain what can be corrected and by whom. Detailed diagnostics remain access-controlled.

## Recovery and retry

Retry only explicitly transient, idempotent operations. Respect provider retry guidance, exponential
backoff, jitter, attempt/time budgets and circuit breakers. Preserve the original delivery/event
identity and payload digest. Do not retry authorization, validation, incompatibility or divergent
conflict. After budget exhaustion create a durable reconciliation item with owner and next action.

For uncertain side effects, query external status. Retry is permitted only when the contract proves
the effect absent and safe. Compensating actions cannot erase history or revoke a target effect
without contract authority; they create new audited transitions.

## Fault isolation

Project, reporting and optional mirror faults never alter or block safe canonical issue updates.
One poison event is quarantined without halting unrelated partitions. One task's execution is
isolated from another. Identity, evidence or policy failure blocks authority-changing work because
continuation would be unsafe. Backpressure preserves data rather than bypassing controls.

## Verification

Fault-injection suites cover pre/post-acceptance timeout, duplicate and divergent replay,
out-of-order results, stale revision, audit failure, quota/rate limits, restart/recovery and poison
messages. Each test proves no duplicate execution/publication, no state regression, no secret leak,
and a deterministic recovery path.

