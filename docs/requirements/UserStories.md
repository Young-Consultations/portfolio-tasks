# User Stories

## Intake and portfolio structure

### US-INT-01 — Complete request
**Role:** task author. **Goal:** capture intent, context, constraints, acceptance evidence, and
provenance in one guided record. **Benefit:** reviewers can govern it without reconstructing my
intent. **Priority:** Must. **Dependencies:** FR-INT-01. **Acceptance criteria:** required omissions
are identified; valid submission creates one proposed issue; submission does not approve or route.

### US-INT-02 — Consulting recommendation
**Role:** consultant. **Goal:** translate an authorized, non-sensitive recommendation into linked
portfolio work. **Benefit:** advisory value becomes traceable delivery demand. **Priority:** Should.
**Dependencies:** FR-INT-02, Interface-ConsultingPlaybook. **Acceptance criteria:** source/version
and permitted context are attributed; unavailable context is an explicit dependency; sensitive
content does not cross automatically.

### US-CLS-01 — Decompose outcomes
**Role:** portfolio manager. **Goal:** connect strategic need to separately targetable work.
**Benefit:** teams can sequence and approve bounded units. **Priority:** Must. **Dependencies:**
FR-CLS-02–03. **Acceptance criteria:** parent rationale remains navigable; each executable child has
one target; blocking dependencies stop routing.

### US-CLS-02 — Understand backlog health
**Role:** portfolio manager. **Goal:** find stale, incomplete, blocked, oversized, and outcome-less
items. **Benefit:** I can improve flow and quality. **Priority:** Should. **Dependencies:** FR-CLS-04.
**Acceptance criteria:** each indicator names its rule/evidence; thresholds and freshness are shown;
health does not autonomously approve or reprioritize.

## Governance and authorization

### US-GOV-01 — Prioritize transparently
**Role:** engineering lead. **Goal:** rank work with rationale while keeping authorization separate.
**Benefit:** capacity follows accountable priorities without unsafe execution. **Priority:** Must.
**Dependencies:** FR-GOV-01. **Acceptance criteria:** priority has actor/rationale/history; highest
priority alone cannot route.

### US-GOV-02 — Approve informed work
**Role:** human approver. **Goal:** see the exact validated revision and boundaries before approving.
**Benefit:** my authorization is informed and attributable. **Priority:** Must. **Dependencies:**
FR-GOV-02–03. **Acceptance criteria:** readiness violations block approval; evidence includes actor,
revision, target, executor, policy, and time; bots cannot approve.

### US-GOV-03 — Revoke or require renewed consent
**Role:** human approver. **Goal:** revoke authorization and have material edits invalidate it.
**Benefit:** changed or unsafe work cannot execute under stale consent. **Priority:** Must.
**Dependencies:** FR-GOV-04. **Acceptance criteria:** material edits remove eligibility; revocation
stops unaccepted routing; history remains.

## Routing, execution, and outcome

### US-RTE-01 — Handoff a self-sufficient task
**Role:** target owner. **Goal:** receive one bounded, approved task without needing sibling access.
**Benefit:** my repository remains autonomous and secure. **Priority:** Must. **Dependencies:**
FR-RTE-01–02. **Acceptance criteria:** task contains required context/provenance; wrong or incomplete
target data fails closed; acceptance is correlated.

### US-RTE-02 — Safe redelivery
**Role:** repository maintainer. **Goal:** retry uncertain work without duplicate execution or PRs.
**Benefit:** automation is reliable under redelivery. **Priority:** Must. **Dependencies:**
FR-RTE-03–04. **Acceptance criteria:** stable replay has one logical effect; mismatched reuse is a
conflict; indeterminate state is reconciled before new effects.

### US-TGT-01 — Bounded AI execution
**Role:** bounded AI executor. **Goal:** receive explicit permissions, constraints, and evidence
expectations. **Benefit:** I can act deterministically without exceeding authority. **Priority:**
Must. **Dependencies:** FR-TGT-01–02. **Acceptance criteria:** target validates request and output;
untrusted content cannot widen permissions; publication remains one draft PR.

### US-OUT-01 — Review, decide, and learn
**Role:** target owner/reviewer. **Goal:** review validated draft evidence and record disposition.
**Benefit:** delivery remains human-owned and portfolio outcomes become accurate. **Priority:** Must.
**Dependencies:** FR-OUT-01–02. **Acceptance criteria:** execution and delivery are distinct; result
is authenticated/correlated; merge/reject/cancel/supersede decisions are attributable.

## Visibility, operations, and assurance

### US-PRJ-01 — Trust planning views
**Role:** Project consumer. **Goal:** see timely issue-derived portfolio fields and drift warnings.
**Benefit:** planning views are useful without becoming authority. **Priority:** Must. **Dependencies:**
FR-PRJ-01–02. **Acceptance criteria:** source mapping is visible; issue wins conflicts; Project-only
changes cannot route.

### US-OPS-01 — Recover safely
**Role:** maintainer. **Goal:** diagnose partial failure using correlation and perform an approved
recovery. **Benefit:** service resumes without corrupting authority. **Priority:** Must.
**Dependencies:** FR-RTE-04, NFR-REC-*. **Acceptance criteria:** confirmed versus unknown state is
clear; retry classification is explicit; resolution is audited.

### US-AUD-01 — Reconstruct decisions
**Role:** auditor. **Goal:** trace need, revisions, priority, approval, handoff, evidence, and final
disposition. **Benefit:** I can verify governance and policy conformance. **Priority:** Must.
**Dependencies:** FR-INT-02, NFR-AUD-*. **Acceptance criteria:** trace is searchable by issue and
correlation; actor/time/policy are present; access and export obey policy.
