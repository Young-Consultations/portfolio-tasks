# Requirements Traceability Matrix

## Vision goal identifiers

| ID | Vision goal |
| --- | --- |
| VG-01 | Structured, complete, traceable intake and canonical records. |
| VG-02 | Healthy hierarchy, decomposition, prioritization, and backlog visibility. |
| VG-03 | Explicit current human approval separate from intake, priority, and Projects. |
| VG-04 | Self-sufficient canonical tasks and controlled organization routing. |
| VG-05 | Stable identity, idempotency, concurrency safety, and failure recovery. |
| VG-06 | Target sovereignty, least privilege, validated draft-only AI execution. |
| VG-07 | Correlated status, evidence, human disposition, and outcome learning. |
| VG-08 | GitHub Project visibility without a second authority. |
| VG-09 | Versioned interoperable contracts and independent repository evolution. |
| VG-10 | Sensitive-data protection, auditability, accessibility, and governance. |

## Matrix

Future test IDs describe verification intent and SHALL become executable test specifications during
design. `ALL` for acceptance criteria means every `AC-<FR>-*` criterion under that requirement.

| Vision | Business objective | Functional requirement | Principal NFRs | Acceptance criteria | Future tests |
| --- | --- | --- | --- | --- | --- |
| VG-01 | BO-01, BO-03 | FR-INT-01 | NFR-USA-01, NFR-AUT-01, NFR-ACC-01 | ALL | TC-INT-001 valid intake; TC-INT-002 omissions; TC-INT-003 no implicit route; TC-UX-001 first-use study |
| VG-01, VG-10 | BO-03 | FR-INT-02 | NFR-AUD-01–02, NFR-OBS-02 | ALL | TC-AUD-001 revision trace; TC-AUD-002 retained decisions; TC-AUD-003 access control |
| VG-10 | BO-02, BO-04 | FR-INT-03 | NFR-SEC-03–05, NFR-CMP-01 | ALL | TC-SEC-001 prohibited fixture; TC-SEC-002 uncertain classification; TC-SEC-003 redacted telemetry |
| VG-01, VG-02 | BO-01, BO-05 | FR-CLS-01 | NFR-CFG-01–02, NFR-MNT-03 | ALL | TC-CLS-001 taxonomy round-trip; TC-CLS-002 unknown/deprecated value; TC-CFG-001 rollback |
| VG-01, VG-02 | BO-01, BO-03 | FR-CLS-02 | NFR-AUT-01 | ALL | TC-HIER-001 end-to-end navigation; TC-HIER-002 multi-target block; TC-HIER-003 child rationale |
| VG-02, VG-04 | BO-01, BO-04 | FR-CLS-03 | NFR-REL-02–03 | ALL | TC-DEP-001 open blocker; TC-DEP-002 none/missing/unknown; TC-DEP-003 cycle/self reference |
| VG-02, VG-07 | BO-05 | FR-CLS-04 | NFR-OBS-01, NFR-SCL-01 | ALL | TC-HLT-001 health rules; TC-HLT-002 historical thresholds; TC-HLT-003 scale report |
| VG-02, VG-03 | BO-01, BO-02 | FR-GOV-01 | NFR-SEC-01–02, NFR-AUD-01 | ALL | TC-PRI-001 priority-not-permission; TC-PRI-002 unauthorized actor |
| VG-03, VG-04, VG-10 | BO-01, BO-02, BO-04 | FR-GOV-02 | NFR-PER-03, NFR-SEC-01, NFR-AUT-01 | ALL | TC-RDY-001 violation matrix; TC-RDY-002 revision binding; TC-RDY-003 actionable errors |
| VG-03 | BO-02 | FR-GOV-03 | NFR-SEC-01–02, NFR-AUD-01 | ALL | TC-APR-001 human authorization; TC-APR-002 bot/unauthorized denial; TC-APR-003 revoke before accept |
| VG-03 | BO-02 | FR-GOV-04 | NFR-REL-03, NFR-AUD-01 | ALL | TC-APR-004 material field matrix; TC-APR-005 nonmaterial audit; TC-APR-006 stale event |
| VG-01, VG-04 | BO-03, BO-04 | FR-RTE-01 | NFR-INT-01–02, NFR-AI-01 | ALL | TC-TASK-001 source equivalence; TC-TASK-002 isolated target; TC-TASK-003 payload validation |
| VG-04, VG-09 | BO-04, BO-06 | FR-RTE-02 | NFR-PER-01, NFR-DPL-01–02, NFR-INT-01–02 | ALL | TC-RTE-001 gates; TC-RTE-002 outcome categories; TC-RTE-003 timeout ambiguity; TC-RTE-004 incompatible version |
| VG-05 | BO-04 | FR-RTE-03 | NFR-REL-01–03, NFR-SCL-01 | ALL | TC-IDEM-001 100 replays; TC-IDEM-002 payload conflict; TC-CON-001 unsafe serialization; TC-CON-002 parallel target policy |
| VG-05 | BO-04, BO-05 | FR-RTE-04 | NFR-REC-01–03, NFR-OBS-02–03 | ALL | TC-REC-001 timeout-after-accept; TC-REC-002 safe retry; TC-REC-003 no-evidence hold; TC-REC-004 exercise |
| VG-07, VG-09 | BO-03, BO-05, BO-06 | FR-OUT-01 | NFR-SEC-01, NFR-INT-02, NFR-AUD-01 | ALL | TC-RES-001 valid result; TC-RES-002 forged/unknown; TC-RES-003 out-of-order; TC-RES-004 evidence linkage |
| VG-06, VG-07 | BO-02, BO-03, BO-04 | FR-OUT-02 | NFR-SEC-02, NFR-AI-02 | ALL | TC-DSP-001 draft-not-done; TC-DSP-002 disposition matrix; TC-DSP-003 no automated merge |
| VG-07 | BO-03, BO-05 | FR-OUT-03 | NFR-CMP-02, NFR-AUD-02 | ALL | TC-LIFE-001 close/archive; TC-LIFE-002 reopen freshness; TC-LIFE-003 supersession |
| VG-03, VG-08 | BO-02, BO-05 | FR-PRJ-01 | NFR-PER-02, NFR-DPL-02 | ALL | TC-PRJ-001 mapping; TC-PRJ-002 Project cannot approve; TC-PRJ-003 unavailable Project isolation |
| VG-08 | BO-05 | FR-PRJ-02 | NFR-PER-02, NFR-OBS-01, NFR-REL-02 | ALL | TC-PRJ-004 drift injection; TC-PRJ-005 correction failure; TC-PRJ-006 freshness alert |
| VG-02, VG-07 | BO-03, BO-05 | FR-RPT-01 | NFR-OBS-01, NFR-ACC-01–02, NFR-CMP-02 | ALL | TC-RPT-001 metric definitions; TC-RPT-002 unknown vs zero; TC-RPT-003 accessible drill-down |
| VG-06, VG-09, VG-10 | BO-02, BO-04, BO-06 | FR-TGT-01 | NFR-SEC-01–06, NFR-INT-01–02 | ALL | TC-TGT-001 wrong boundary matrix; TC-TGT-002 shared/local evidence; TC-TGT-003 injection test |
| VG-05, VG-06, VG-07 | BO-02, BO-03, BO-04 | FR-TGT-02 | NFR-REL-01–02, NFR-TST-01–02, NFR-AI-02–03 | ALL | TC-TGT-004 validation evidence; TC-TGT-005 draft idempotency; TC-TGT-006 prohibited states; TC-AI-001 executor evaluation |

## Cross-cutting NFR verification

| NFR area | Vision/business coverage | Future test or evidence suite |
| --- | --- | --- |
| Performance/scalability (`NFR-PER-*`, `NFR-SCL-*`) | VG-02, VG-04, VG-08 / BO-01, BO-05 | TC-NFR-PER-001 latency load; TC-NFR-SCL-001 capacity; TC-NFR-SCL-002 overload/quota |
| Availability/recovery (`NFR-AVL-*`, `NFR-REC-*`) | VG-05 / BO-04, BO-05 | TC-NFR-AVL-001 monthly SLI; TC-NFR-REC-001 state restore; TC-NFR-REC-002 semiannual exercise |
| Security/compliance (`NFR-SEC-*`, `NFR-CMP-*`) | VG-03, VG-06, VG-10 / BO-02, BO-04 | TC-NFR-SEC-001 threat suite; TC-NFR-SEC-002 credential rotation; EV-CMP-001 policy approval; EV-CMP-002 retention audit |
| Audit/observability (`NFR-AUD-*`, `NFR-OBS-*`) | VG-05, VG-07, VG-10 / BO-03, BO-05 | TC-NFR-AUD-001 event completeness; TC-NFR-OBS-001 trace sample; TC-NFR-OBS-002 alert safety |
| Maintainability/configuration (`NFR-MNT-*`, `NFR-EXT-*`, `NFR-CFG-*`) | VG-09 / BO-06 | EV-ARCH-001 ownership review; TC-NFR-CFG-001 invalid config; TC-NFR-EXT-001 target onboarding; EV-DOC-001 change audit |
| Deployment/interoperability (`NFR-DPL-*`, `NFR-PRT-*`, `NFR-INT-*`) | VG-04, VG-09 / BO-04, BO-06 | TC-NFR-DPL-001 independent upgrade; TC-NFR-INT-001 version matrix; EV-PRT-001 implementation-neutral review |
| Usability/accessibility (`NFR-USA-*`, `NFR-ACC-*`) | VG-01, VG-03, VG-10 / BO-01, BO-02 | TC-UX-001 timed intake; TC-UX-002 state comprehension; TC-A11Y-001 WCAG audit; TC-A11Y-002 assistive technology |
| Documentation/test/AI (`NFR-DOC-*`, `NFR-TST-*`, `NFR-AUT-*`, `NFR-AI-*`) | All / all objectives | EV-DOC-002 six-month review; EV-TST-001 coverage trace; TC-AUT-001 deterministic parsing; TC-AI-001 model change evaluation |

## Change-control rule

A vision or business-objective change SHALL identify affected requirement IDs. A functional or
nonfunctional change SHALL update its acceptance criteria, future tests, stories/use cases,
interfaces, assumptions, and this matrix. A requirement SHALL NOT be marked verified unless its
evidence is reproducible and all dependent external contracts have been validated by their owners.
