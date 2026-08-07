# Interface Requirements — GitHub Platform and GitHub Projects

## Purpose and boundary

GitHub provides issue records, identity, events, access control, audit facilities, pull requests,
automation, and Project projections. GitHub Issues in `portfolio-tasks` are the authoritative
executable records. Projects, comments, labels, workflow runs, artifacts, and pull requests are
supporting representations/evidence and SHALL NOT silently replace issue authority.

## Required platform inputs and outputs

The product requires authenticated issue create/read/update/event data; actor and repository
identity; durable issue references and history; permission enforcement; Project item and field
read/write; automation status; and, for this repository as a target, draft pull-request and evidence
publication. Product outputs include structured issue content/state, attributable comments or
checks, Project projections, audit events, and draft-only target evidence.

## Required behavior

* Events SHALL be authenticated or obtained through an authenticated authoritative read before a
  governed transition. Event payload alone SHALL NOT be assumed current.
* Delivery/event identity and canonical issue revision SHALL support replay and stale-event checks.
* API pagination, rate limits, conditional updates, partial failure, permission loss, and eventual
  consistency SHALL be handled without authority loss or silent omission.
* Project mappings SHALL declare authoritative source and reconcile toward the issue; Project-only
  changes cannot approve or route.
* Pull request publication by automation SHALL be draft, correlated, idempotent, and target-owned.
* Transient/rate-limit responses MAY retry with bounded backoff; permission, validation, not-found,
  and conflict outcomes require classification and possibly human action.
* Platform/API version changes SHALL be compatibility-tested before adoption.

## Data contracts

Stable issue, repository, actor, event/delivery, Project/item/field, workflow/run, artifact, branch,
commit, and pull-request identities MUST be retained where relevant. Timestamps SHALL be UTC and
ordering assumptions SHALL be explicit. Structured product semantics MUST NOT depend solely on
free-form prose, display names, field positions, or view placement.

## Ownership, assumptions, and unknowns

GitHub owns platform availability and API semantics; organization administrators own identities,
repositories, permissions, Projects, secrets, protection, and audit configuration; portfolio and
target owners own their records and policies. Unknown production tier, quotas, retention, audit
features, token model, identity federation, Project field limits, and outage commitments MUST be
validated. Platform unavailability SHALL preserve safe pending state and invoke `NFR-REC-*`.

## Next-MVP CI boundary

Normal CI SHALL replace GitHub mutation with a deterministic adapter that records intended target,
branch, draft metadata, correlation, and result update. The test identity SHALL have no path that
creates a real branch or pull request. Live-platform enablement separately requires organization
administrator evidence for identity, permissions, event redelivery, and draft-only publication;
mock success is not platform conformance.
