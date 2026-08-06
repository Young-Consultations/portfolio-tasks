# Interface Requirements — Young-Consultations/.github

## Purpose and responsibility boundary

This required contract connects portfolio authorization to the organization control plane. The
external repository is expected to own organization schemas, repository/executor registration,
routing, compatibility policy, shared validation, and routing/result contract releases.
`portfolio-tasks` owns authoritative intent, readiness, approval, canonical task construction, and
routing initiation. It SHALL consume, not copy or redefine, the control plane's contracts.

No implementation or current availability is assumed; owner validation is a release dependency.
The next-MVP organization baseline is expected at
`Young-Consultations/.github/docs/releases/next-mvp.md` and has not been inspected. Its exact
contract version, result transport, lifecycle semantics, and target enablements are therefore
release-blocking unknowns; the portfolio expectation below is consumer-owned semantics only.

## Required inputs from portfolio-tasks

A routing request MUST convey, under a machine-validatable versioned contract:

* contract version and stable request, task, delivery, correlation, and source-issue identities;
* authoritative source repository and issue revision/content digest;
* target repository and requested executor identity/class;
* objective, business/engineering rationale, bounded required behavior, in/out scope, constraints,
  acceptance criteria, and required test/evidence outcomes;
* dependency resolution snapshot, risk, sensitivity decision, and parallel-safety declaration;
* attributable approval evidence, approval policy/version, and approval time;
* draft-only publication constraint and permitted operation boundary;
* provenance sufficient to validate without target access to the portfolio repository.

The precise field names, encoding, transport, signing/authentication mechanism, maximum sizes, and
identity relationships are owned externally and MUST be validated before integration.
Approval MUST be validated from revision/digest-bound evidence. Mutable labels may be projected
for people, but router acceptance and replacement of an approval label with a queued label MUST
NOT revoke authority or force a target to race a label read.

## Required outputs and events

The control plane MUST return a correlated outcome of accepted, rejected, duplicate/existing,
conflict, or indeterminate. Acceptance MUST identify the contract version and routing identity; a
rejection MUST provide safe machine category and actionable explanation. It MUST provide or
mediate authenticated, correlated lifecycle statuses and one terminal execution result, including
target, executor, attempt, outcome, validation/test evidence, publication reference if any,
timestamps, and failure category. Portfolio receipt MUST be possible without granting the target
write access to portfolio authority.

Required semantic events are routing accepted/rejected, execution queued/started/blocked/failed/
completed, publication produced (draft only), and result finalized. The owner MAY select event,
request/response, polling, or artifact transport if ordering, authentication, replay, and recovery
requirements are met.

## Contract behavior

* Both parties MUST validate syntax, semantics, version, identity, authorization, and correlation.
* A stable request replay MUST cause at most one logical route; reused identity with changed
  authorized content MUST be a conflict.
* Status sequence MUST NOT regress; duplicates MUST be harmless; late/unknown events MUST be
  quarantined or reconciled.
* Transient errors MAY be retried with bounded backoff and the same identity. Authorization,
  validation, incompatibility, sensitivity, and conflict errors MUST NOT be blindly retried.
* Timeout without durable acceptance evidence is indeterminate, not permission to create a new ID.
* Supported major versions MUST have explicit compatibility; unknown majors fail closed. Minor
  evolution MUST preserve old required meaning or negotiate support. Deprecation follows
  `NFR-MNT-03`.
* Revocation after acceptance MUST be communicated when externally supported, but inability to
  stop irreversible work MUST be reported honestly and handled by target-owner review.

## Ownership and assurance

The control-plane owner owns schema publication, validators, registration, routing authorization,
compatibility, and shared conformance tests. The portfolio owner owns source truth and approval.
Each side owns its credentials, logs, retries, and evidence. Joint tests MUST cover forged
approval, wrong target, incompatible version, replay, payload conflict, timeout after acceptance,
out-of-order result, revocation, and least privilege.

## Assumptions, unknowns, and validation required

Working assumptions: a registered portfolio source and target directory exist; the control plane
can validate human approval evidence; and a result path exists. Unknown: supported versions,
transport/events, release pinning, schema fields, payload limits, delivery/correlation relationship,
authentication and signing, approver registry, cancellation semantics, retry windows, status
ordering, evidence retention, service objectives, and incident ownership. All MUST be agreed with
the `.github` repository owner before production routing.


## Next-MVP conformance gate

The external owner SHALL provide an owner-pinned provider fixture or conformance artifact for
accepted, rejected, duplicate, conflict, timeout/query, ordered status, cancellation, and terminal
result semantics. `portfolio-tasks` SHALL run it against `FR-CIV-01`; absent or incompatible
evidence blocks all live routes, including `.github` when it acts as a target.
