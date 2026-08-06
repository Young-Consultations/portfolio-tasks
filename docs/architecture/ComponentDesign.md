# Component Design

## Component catalogue

All ownership defaults to the `portfolio-tasks` maintainers unless explicitly external.

| Component | Purpose / responsibilities | Inputs → outputs | Dependencies | Lifecycle / failure / scale |
| --- | --- | --- | --- | --- |
| Intake Gateway | Authenticate channel, preserve provenance, parse and validate structured intent; never approve | request/event → normalized candidate and violations | identity, WorkRecord, sensitivity | Per request; reject/quarantine unsafe input; stateless horizontal scale |
| Portfolio Aggregate Service | Enforce hierarchy, dependency, revision and lifecycle invariants | command + current aggregate → decision/new aggregate | pure policies, clock | Per command; optimistic conflict is explicit; partition by work ID |
| Governance Service | Readiness, priority, human approval/revocation, material-change invalidation | actor + revision + policy → decision evidence | authorization, catalog, audit | Human-decision lifecycle; fail closed on missing authority; cache only versioned policy |
| Canonical Task Builder | Assemble immutable, bounded, redacted and self-sufficient envelope | approved snapshot → task + digest | contract catalog, codec | Deterministic; invalid/oversize data blocks; CPU/stateless scaling |
| Routing Coordinator | Reserve idempotency, recheck gates, submit and record outcome | canonical task + delivery ID → acceptance/rejection/ambiguous | routing, idempotency, audit | Durable saga; bounded retries; serialize same identity |
| Result Ingestor | Authenticate, correlate, order and apply external events | event envelope → applied/duplicate/stale/conflict | identity, contract, WorkRecord | Event-driven; quarantine poison/conflict; partition by task |
| Reconciler | Resolve timeout, incomplete outbox, unknown acceptance and projection drift | unresolved record → verified outcome/action | status query, evidence, projections | Scheduled/on-demand; backoff and operator queue; horizontally shardable |
| Projector | Map issue-owned state to Projects/read models | authoritative revision → projection outcome | GitHub Project port, mapping config | Eventually consistent; no effect on approval; batch and rate-limit aware |
| Reporting Service | Define and expose health, flow, outcome and governance measures | authorized query → drill-down/read model + freshness | projections, metric catalog | Read-only; degraded views state staleness; cache safely by access scope |
| Audit Recorder | Preserve attributable decisions/effects without secret leakage | structured audit fact → durable evidence reference | evidence store, redaction | Append-only semantics; failure blocks authority-changing effects where evidence is mandatory |
| Configuration Manager | Load, validate and activate versioned policy snapshots | candidate config → active/rejected snapshot | configuration source, audit | Staged activation/rollback; invalid config keeps last known safe version or disables feature |
| Local Target Gateway | Independently verify tasks targeting this repo, invoke bounded executor, validate evidence, publish once as draft | routed task → acceptance/status/result/draft reference | external contract, local policy/executor | Separate trust role; isolate attempt; no unsafe retry; capacity by target policy |

## Interface shape

Each component exposes typed commands/queries/events through interfaces in
`InterfaceArchitecture.md`. Responses contain outcome category, correlation, current revision,
violations and retry guidance. No component returns raw credentials, adapter stack traces, or
unverified success claims.

## Dependency rules

Experience and adapters depend on application interfaces; application orchestration depends on
domain and ports; domain depends on neither. Projection/reporting may consume emitted facts but may
not call governance to mutate state. The target gateway shares contract semantics, not portfolio
privileges. External components are addressed only through organization-owned contracts.

## Availability and degradation

Intake may remain available when Projects or routing are unavailable. Projection failure cannot
alter canonical state. Routing outage leaves an approved task pending/ambiguous, never falsely
accepted. Audit/identity/contract unavailability blocks security-sensitive transitions. Reporting
may serve labeled stale data. Every degraded condition is observable and reconcilable.

