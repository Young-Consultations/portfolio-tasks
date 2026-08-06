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
