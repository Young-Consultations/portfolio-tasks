# Architecture Traceability Matrix

## Trace model

```mermaid
flowchart LR
  V[Vision goals VG] --> B[Business objectives BO]
  B --> R[Functional/NFR requirements]
  R --> A[Architecture decisions and views]
  A --> C[Components]
  C --> I[Interfaces]
  I --> F[Future implementation and evidence]
```

Vision and requirements identifiers are defined in `docs/requirements/RequirementsTraceability.md`.
`SoftwareArchitecture.md` defines component names; `ADR.md` defines decisions; interface names are
from `InterfaceArchitecture.md`. Future implementation labels are verification obligations, not
claims about current code.

## End-to-end functional traceability

| Vision / business | Requirements | Architectural response | Components / interfaces | Future implementation evidence |
| --- | --- | --- | --- | --- |
| VG-01 / BO-01,03 | FR-INT-01, FR-INT-02 | ADR-001/002; authoritative revision/provenance aggregate | Intake Gateway; Structured Intake, Work Amendment | Intake omissions/no implicit route; revision/audit reconstruction; accessible first-use tests |
| VG-10 / BO-02,04 | FR-INT-03 | ADR-008; classify/minimize/quarantine before effects | Intake, Governance, Audit; intake/task interfaces | prohibited/uncertain fixtures, redaction and incident tests |
| VG-01,02 / BO-01,03,05 | FR-CLS-01..04 | Versioned taxonomy; hierarchy/dependency invariants; read models | Portfolio Aggregate, Config, Reporting | taxonomy round-trip, target decomposition, cycle/blocker and scale/health tests |
| VG-02,03 / BO-01,02 | FR-GOV-01,02 | ADR-003; priority distinct from approval; deterministic readiness | Governance; Readiness and Governance interfaces | priority-not-permission, violation matrix, actor/role and revision tests |
| VG-03 / BO-02 | FR-GOV-03,04 | Revision/digest-bound human approval; material-change invalidation | Governance, Work Record; approve/revoke/amend | bot denial, revoke, stale event and material-field matrix |
| VG-01,04,09 / BO-03,04,06 | FR-RTE-01,02 | ADR-004/005; self-sufficient versioned task through external router | Task Builder, Routing Coordinator; submission/status | isolated-target equivalence, gates, incompatible version and timeout tests |
| VG-05 / BO-04,05 | FR-RTE-03,04 | ADR-006; durable identity/digest saga and reconciliation | Routing, Idempotency, Reconciler | 100 replays, divergent payload, concurrency, timeout-after-accept and recovery exercise |
| VG-07,09 / BO-03,05,06 | FR-OUT-01 | Authenticated/correlated/ordered fact ingestion | Result Ingestor; Execution Event Ingress | forged/unknown/out-of-order/result evidence tests |
| VG-06,07 / BO-02,03,04 | FR-OUT-02,03 | ADR-007; draft is not done; disposition and historical lifecycle | Outcomes, Reporting; Target Execution/Event ingress | disposition matrix, no automated merge, close/reopen/supersession |
| VG-03,08 / BO-02,05 | FR-PRJ-01,02 | ADR-001; issue-to-Project authority and drift states | Projector; Project Projection | mapping, Project-cannot-approve, outage/drift/freshness tests |
| VG-02,07 / BO-03,05 | FR-RPT-01 | Defined accessible measures with drill-down/freshness | Reporting Query/Export | definition, unknown-vs-zero, accessible drill-down tests |
| VG-06,09,10 / BO-02,04,06 | FR-TGT-01,02 | ADR-007/008/009; independent local gate, isolated executor, evidence and draft-only guard | Local Target Gateway; Target Execution/Local Target Workflow | wrong-boundary/injection, validation evidence, draft idempotency, prohibited state and model evaluation |

## Cross-cutting traceability

| NFR families | Architecture documents / mechanisms | Required future evidence |
| --- | --- | --- |
| NFR-PER, NFR-SCL | HLD partitioning; component statelessness; Deployment scaling/backpressure | latency/capacity/quota tests against approved three-year baseline |
| NFR-AVL, NFR-REL, NFR-REC | idempotent saga, State Models, Error Handling, recovery checkpoints | availability SLI, restart/fault injection, state restore and semiannual recovery |
| NFR-SEC, NFR-CMP | Security trust boundaries, fail-closed gates, data minimization/secrets | threat suite, credential rotation, policy/retention approval and audits |
| NFR-AUD, NFR-OBS | evidence port and Observability correlation/signals | event completeness, task reconstruction, trace/alert/redaction tests |
| NFR-MNT, NFR-EXT, NFR-CFG | clean modules, ports, Configuration and Extension architecture | ownership review, invalid config/rollback and target onboarding conformance |
| NFR-DPL, NFR-PRT, NFR-INT | external router boundary, semantic model, version overlap | independent-upgrade/version matrix and implementation-neutral review |
| NFR-USA, NFR-ACC | actionable violations, accessible status/report alternatives | timed comprehension studies and WCAG/assistive-technology audit |
| NFR-DOC, NFR-TST, NFR-AUT, NFR-AI | this baseline, test seams, deterministic schemas/fixtures, model evaluation | documentation audit, trace coverage, deterministic parsing and executor evaluation |

## Future implementation gate

Every backlog change shall identify requirement IDs, affected ADR/component/interface, positive and
negative tests, security/observability impact, migration/rollback and external validation. A
requirement is not verified by unit tests alone when provider-owned behavior remains unknown.
Changes to Vision or Requirements update this matrix before architecture or implementation.

## Known traceability gaps

The following prevent full implementation authorization: named product/data/security/operations
owners; approver and separation-of-duty policy; material-change and lifecycle/cancellation rules;
data classification/retention/legal hold; approved SLO/RTO/RPO and scale; control-plane schema,
authentication and status guarantees; target registrations/capabilities; and the business decision
on Slugger mirroring. These map to `docs/requirements/Assumptions.md` and must remain visible as
blocked validation work, never resolved by architectural invention.


## Next-MVP architecture trace

`FR-CIV-01` traces from VG-03/04/05/06/07/09 and BO-02/03/04/06 through ADR-011/012, the
approval/routing/target/result state and sequence views, and deterministic adapters for every
external port to `TC-MVP-E2E-001`, `TC-MVP-NEG-001`, `TC-MVP-REC-001`, and
`TC-MVP-NOEFFECT-001`. Those tests trace back respectively to lifecycle success, fail-closed human
authority, at-least-once replay/reconciliation, and absence of live Codex/branch/PR effects.
