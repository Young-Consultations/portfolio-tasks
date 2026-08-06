# Observability Architecture

## Goals

Operators and auditors must determine what happened, why, under whose authority, at which revision,
across which boundary, and what action is safe—without exposing task secrets. Observability data
supports operations; authoritative decisions remain in governed records/evidence.

## Correlation and event model

Propagate work ID, issue revision, delivery ID, attempt ID, event ID, correlation/trace ID, target,
contract/policy/config version and outcome category. Structured events use stable names and schemas.
Never use sensitive body text, credentials or untrusted raw diagnostics as labels.

## Signals

| Signal | Required examples |
| --- | --- |
| Audit facts | intake/revision, readiness, approval/revoke, gate denial, route intent/receipt, reconciliation, result/disposition, config and privileged operations |
| Logs | structured transition/effect summary, redacted violation/error code, correlation, retry decision |
| Metrics | intake completeness, readiness/approval/routing flow, latency percentiles, duplicate/conflict/uncertain counts, reconciliation age, result/disposition coverage |
| Dependency metrics | control-plane failures/latency, GitHub quota/rate, Project freshness/drift, queue depth/age, target outcomes |
| Security metrics | authorization denial, quarantine, signature/auth failure, secret detection, privileged access |
| Traces | intake validation, task build, routing saga, event application, projection sync; cross-boundary context where contracted |
| Health | liveness, readiness, config/catalog validity, durable state, dependency/circuit and worker progress |

Metric definitions state numerator, denominator, time window, exclusions, dimensions and owner;
unknown is never reported as zero. High-cardinality identities belong in logs/traces, not metric
labels. Dashboards provide accessible text/table alternatives and source freshness.

## Alerts and diagnostics

Alert on sustained SLO breach, oldest reconciliation item, stuck accepted execution, incompatible
contract, divergent replay, forged/unknown event, audit write failure, projection drift/freshness,
quota exhaustion and failed recovery. Alerts identify severity, affected boundary, safe next action,
runbook and owner; they deduplicate and avoid raw content.

Diagnostic bundles contain configuration/contract versions, state history, redacted event headers,
dependency outcomes and evidence references. Collection and access are authorized/audited.

## Retention and assurance

Telemetry retention and access may differ from business evidence and require approved privacy,
records and legal-hold policy. Periodically test trace continuity, redaction, metric accuracy, alert
routing, dashboard accessibility and reconstruction of representative tasks. Operational SLO
thresholds remain open until owners validate NFR targets and external exclusions.

