# Nonfunctional Requirements

Unless a stricter external or organizational policy applies, the following are baseline service
objectives. Measurement excludes announced GitHub-wide outages only when reports show both raw and
excluded results. Threshold changes require governed baseline revision.

## Performance and scalability

| ID | Requirement and verification measure |
| --- | --- |
| NFR-PER-01 | For at least 95% of events in a calendar month, the product SHALL record receipt and an initial accepted/rejected/blocked/duplicate decision within 60 seconds of event availability; 99% SHALL complete within 5 minutes, excluding external throttling separately reported. |
| NFR-PER-02 | Issue-to-Project projections SHALL reach consistency within 5 minutes for 95% and 30 minutes for 99% of eligible changes; drift older than 30 minutes SHALL alert an operator. |
| NFR-PER-03 | Interactive validation feedback SHOULD be available within 3 seconds at the 95th percentile when external checks are not needed, and within 10 seconds when dependencies respond within their objectives. |
| NFR-SCL-01 | The product SHALL sustain 10,000 open portfolio items, 100,000 archived items, 1,000 intake/update events per hour, and 100 simultaneous routing candidates without data loss, authority violation, or duplicate logical delivery. |
| NFR-SCL-02 | Capacity limits, external quotas, and queue age SHALL be observable before exhaustion; overload SHALL defer safely rather than bypass validation. |

## Availability, reliability, and recoverability

| ID | Requirement and verification measure |
| --- | --- |
| NFR-AVL-01 | Governance, intake, and routing-initiation automation SHOULD achieve 99.5% monthly availability, measured at supported entry points; authoritative issue history SHALL remain usable during automation outage to the extent GitHub is available. |
| NFR-REL-01 | Across replay, timeout, and concurrent-delivery tests, 100% of identical requests SHALL produce at most one logical routing/publication effect; conflicts SHALL fail closed. |
| NFR-REL-02 | A failed transition SHALL never leave a more advanced success state than confirmed evidence supports, and all partial failures SHALL expose correlation and recovery status. |
| NFR-REL-03 | Event processing SHALL tolerate at-least-once delivery, out-of-order events, and a 24-hour delayed redelivery without state regression or duplicate effect. |
| NFR-REC-01 | Durable governed state SHALL have a recovery point objective of zero acknowledged governance decisions lost; derived projections MAY be rebuilt from authority. |
| NFR-REC-02 | After service restoration, queued/reconcilable work SHOULD resume within 60 minutes; ambiguous operations SHALL remain stopped until evidence or human resolution exists. |
| NFR-REC-03 | Recovery procedures SHALL be exercised at least twice yearly and after material boundary changes, with evidence of restoration, reconciliation, and unresolved gaps. |

## Security, privacy, and compliance

| ID | Requirement and verification measure |
| --- | --- |
| NFR-SEC-01 | All human and automation actions SHALL be authenticated; authorization SHALL apply least privilege and deny by default at intake administration, approval, routing, result ingestion, configuration, and audit access boundaries. |
| NFR-SEC-02 | Approval SHALL require a human identity from the configured approver set; tests SHALL demonstrate that issue authorship, labels, bots, Project state, and executor identities cannot substitute. |
| NFR-SEC-03 | Secrets SHALL NOT appear in issues, canonical tasks, logs, telemetry, artifacts, reports, or error messages; secret scanning and representative prohibited-data tests SHALL block handoff and redact output. |
| NFR-SEC-04 | Data SHALL be protected in transit and at rest using organization-approved GitHub/platform controls; credentials SHALL be scoped, short-lived where supported, rotatable, and never supplied to a target beyond its need. |
| NFR-SEC-05 | Untrusted issue content SHALL be treated as data, not authority or executable policy; prompt-injection and command-injection tests SHALL show it cannot widen target, permissions, tools, publication state, or acceptance. |
| NFR-SEC-06 | Dependencies and automation components SHALL be pinned or otherwise integrity-verifiable, reviewed on a defined cadence, and block use when authenticity or required compatibility cannot be established. |
| NFR-CMP-01 | Before production use, owners SHALL approve applicable retention, deletion, privacy, client-confidentiality, export-control, accessibility, and audit obligations; absent a decision, restricted-data automation SHALL remain disabled. |
| NFR-CMP-02 | Retention and deletion SHALL preserve mandatory audit evidence while honoring approved minimization and legal obligations; policy, exception, actor, and completion evidence SHALL be reportable. |

## Auditability and observability

| ID | Requirement and verification measure |
| --- | --- |
| NFR-AUD-01 | 100% of intake, material edits, readiness results, approvals/revocations, handoffs, external acknowledgments, retries, results, reconciliation, disposition, configuration, and privileged access events SHALL record actor/source, UTC time, correlation, action, outcome, and relevant before/after identity. |
| NFR-AUD-02 | Audit records SHALL be tamper-evident under approved platform controls, access-restricted, searchable by issue and correlation ID, and retained for the approved period. |
| NFR-OBS-01 | Operations SHALL expose counts, rates, latency distributions, queue age, validation failures by reason, stale approvals, blocked tasks, duplicate/conflict attempts, synchronization drift, contract incompatibility, result failures, and end-to-end trace completeness. |
| NFR-OBS-02 | Every cross-boundary operation SHALL carry a non-secret correlation ID through logs, evidence, status, and result; 100% of sampled routed tasks SHALL be reconstructable end to end. |
| NFR-OBS-03 | Alerts SHALL identify affected boundary, impact, first occurrence, correlation examples, and a documented response; alerts SHALL contain no task-sensitive content. |

## Maintainability, extensibility, and configuration

| ID | Requirement and verification measure |
| --- | --- |
| NFR-MNT-01 | Product rules, external contracts, and target-local policy SHALL remain separately owned and independently changeable; architecture review SHALL find no copied organization schema asserted as authoritative here. |
| NFR-MNT-02 | Every normative requirement SHALL map to acceptance criteria and planned tests; changed semantics SHALL update traceability and affected interface specifications in the same approved baseline. |
| NFR-MNT-03 | Supported taxonomy, state, interface, and policy versions SHALL have an owner, changelog, compatibility declaration, migration plan, and deprecation notice of at least 90 days unless a documented security exception applies. |
| NFR-EXT-01 | A newly registered target or executor SHOULD require only governed configuration and contract conformance, not a change to core portfolio semantics; conformance tests SHALL verify this property. |
| NFR-CFG-01 | Environment-specific identities, targets, Projects, thresholds, feature controls, taxonomy mappings, and policy references SHALL be externally configurable, schema-validated before activation, and contain no secret values in non-secret configuration. |
| NFR-CFG-02 | Configuration changes SHALL be versioned, attributable, reviewable, reversible, and validated in a non-production context; invalid or missing safety-critical configuration SHALL fail closed. |

## Deployment independence, portability, and interoperability

| ID | Requirement and verification measure |
| --- | --- |
| NFR-DPL-01 | `portfolio-tasks`, organization routing, and target repositories SHALL be deployable and releasable independently while supported contract versions overlap. |
| NFR-DPL-02 | Failure or upgrade of one target SHALL NOT prevent intake/governance for unrelated targets; target-specific routing MAY be blocked explicitly. |
| NFR-PRT-01 | Product requirements SHALL remain independent of a particular programming language, runner image, AI vendor, or target implementation; GitHub Issues as authority and required GitHub capabilities are explicit product constraints. |
| NFR-INT-01 | External payloads SHALL use documented, versioned, machine-validatable contracts with defined encoding, required/optional fields, size/time semantics, identity, errors, and compatibility behavior. |
| NFR-INT-02 | Unknown major versions, invalid signatures/identity, or semantically incompatible inputs SHALL be rejected without portfolio advancement; supported older versions SHALL retain their declared meaning. |

## Usability and accessibility

| ID | Requirement and verification measure |
| --- | --- |
| NFR-USA-01 | A first-time task author SHOULD complete a valid routine intake in 10 minutes or less in moderated testing, and at least 90% of representative users SHALL correctly distinguish proposal, priority, approval, execution, and delivery. |
| NFR-USA-02 | Validation and failure messages SHALL state what failed, why it matters, what remains safe, who can act, and the next action, without exposing sensitive data. |
| NFR-ACC-01 | Human-facing forms, reports, status, and documentation SHALL conform to WCAG 2.2 AA where the product controls presentation; meaning SHALL NOT rely only on color, position, or icons. |
| NFR-ACC-02 | Supported workflows SHALL be keyboard operable, screen-reader understandable, use programmatically associated labels, and provide text alternatives for meaningful visual evidence. |

## Documentation, testability, automation readiness, and AI compatibility

| ID | Requirement and verification measure |
| --- | --- |
| NFR-DOC-01 | User, approver, operator, auditor, target-onboarding, recovery, data-handling, interface, and configuration documentation SHALL be current, versioned, linked to its owner, and reviewed at least every six months. |
| NFR-TST-01 | Every Must requirement SHALL have automated contract/unit/integration verification where technically feasible and a documented human verification otherwise; critical authority, security, idempotency, and state-transition paths SHALL have automated negative tests. |
| NFR-TST-02 | Tests SHALL use non-sensitive deterministic fixtures, isolate external side effects, cover retry/concurrency/out-of-order behavior, and make pass/fail evidence reproducible. |
| NFR-AUT-01 | Machine-consumed state SHALL be structured, schema-validatable, deterministically interpretable, and accompanied by stable IDs and explicit state; automation SHALL NOT infer authorization from prose. |
| NFR-AI-01 | Canonical tasks supplied to AI SHALL state objective, boundaries, permitted target, acceptance evidence, security constraints, human authority limits, and untrusted-content treatment in a deterministic structure. |
| NFR-AI-02 | AI output SHALL be treated as untrusted until target validation and human review; model confidence or claims SHALL NOT replace evidence, approval, or tests. |
| NFR-AI-03 | Executor/model changes SHALL undergo conformance, safety, regression, and output-boundary evaluation before enablement; task/result trace SHALL identify executor class and applicable policy version without requiring disclosure of private reasoning. |
