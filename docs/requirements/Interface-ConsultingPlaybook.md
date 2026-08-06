# Interface Requirements — Young-Consultations/consulting-playbook

## Purpose and responsibilities

`consulting-playbook` is expected to own reusable consulting methods, assessments, decision
frameworks, and delivery playbooks. `portfolio-tasks` MAY capture a consulting recommendation or
reference as portfolio intent, but SHALL NOT copy, redefine, or claim ownership of playbook content.
No current automated integration is assumed.

## Expected inputs and outputs

If an interaction is approved, an inbound recommendation MUST provide a stable source reference,
content/version identity, recommendation summary, business context permitted for portfolio use,
author/provenance, applicability constraints, confidentiality classification, and requested outcome.
Portfolio output MAY provide a canonical issue reference and status summary that reveals only
authorized information. A reference MUST remain meaningful when repositories are inaccessible to
one another; required execution context therefore MUST be lawfully embedded in the approved task,
not merely linked.

Possible semantic events are recommendation published/revised/withdrawn, portfolio item created,
and outcome/disposition available. Transport and automation are intentionally unspecified.

## Contract behavior

* Import MUST be deliberate, authenticated, version-aware, and idempotent by stable source identity.
* Revised or withdrawn guidance MUST NOT silently rewrite an approved task; it SHALL flag potential
  stale context and invoke material-change review.
* Confidential or unknown-classification material MUST NOT cross the boundary automatically.
* A missing/unavailable playbook MUST NOT be invented or inferred; the task SHALL identify the
  external dependency and request authorized context.
* Retry is allowed only for transient retrieval/delivery failure with the same identity; conflicts
  require human reconciliation.

## Ownership, assumptions, and unknowns

Playbook owners govern method meaning, version, access, and confidentiality. Portfolio owners
govern derived work and shall preserve attribution. Unknowns include whether any integration is
desired, reference format, licensing/confidentiality, version semantics, event support, status
feedback, retention, and authorized audiences. These MUST be validated with the external owner;
until then, this is a boundary requirement and external dependency, not an API commitment.
