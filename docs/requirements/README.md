# portfolio-tasks requirements baseline

This directory is the authoritative product requirements baseline for `portfolio-tasks`. The
documents define required outcomes and externally observable behavior, not an implementation.
Where these requirements conflict with current code or operational documentation, the vision and
this approved baseline govern future design; current behavior remains relevant only for migration.

## Document set and precedence

1. [`ProjectRequirements.md`](ProjectRequirements.md) establishes product intent and scope.
2. [`SoftwareRequirementsSpecification.md`](SoftwareRequirementsSpecification.md) is the system
   specification and requirement index.
3. [`FunctionalRequirements.md`](FunctionalRequirements.md) and
   [`NonFunctionalRequirements.md`](NonFunctionalRequirements.md) contain the normative, testable
   requirements.
4. `Interface-*.md` files define boundary contracts that require external-owner validation.
5. The remaining documents provide context, scenarios, rules, terminology, assumptions, and
   traceability.

Normative terms **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, and
**MAY** are interpreted as described by RFC 2119. Requirement IDs are durable: changed meaning
requires a new ID, while editorial clarification may retain the ID. Open questions are not
requirements until resolved through governed change control.

## Baseline governance

Changes to product authority, approval semantics, repository boundaries, or external contracts
require review by the organization owner, portfolio owner, and affected repository owner. Every
approved change shall update impacted requirements, acceptance criteria, interfaces, glossary,
and traceability in the same change set.

## Next-MVP selection

[`../releases/next-mvp.md`](../releases/next-mvp.md) is the repository-level release selection. It
lists the exact included and deferred requirement IDs, lifecycle/authorization decisions,
continuous interface-validation requirement `FR-CIV-01`, acceptance scenario, external blockers,
and exit criteria. The selected payload is `ai-sdlc-contract/v2`; the published compatibility unit is `ai-sdlc-v2.3.2`. It supersedes the incompatible historical
2.3.0 commit `c6090e5bbadcc2102a1cb91875466e9decdada1e` and the 2.3.1 recovery derived
from `e27b8a541afbd27b4be5606a19ffa43637ad312a`. The release baseline records exact interfaces,
schema/fixture blob identities, immutable target capabilities, complete shared-oracle evidence,
and the organization-owned receiver trust boundary. Mutable target activation remains separately
owned and enforced by the organization router. A `Must` priority outside the selected list is not
automatically MVP scope.
