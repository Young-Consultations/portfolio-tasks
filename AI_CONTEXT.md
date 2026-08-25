# AI Context: `portfolio-tasks`

## Purpose and usage

This is the ordered entry point and standing implementation policy for AI agents in this
repository. Read it completely before proposing or making a change, then follow the applicable
reading path. It indexes canonical sources rather than duplicating their requirements, decisions,
contracts, or acceptance criteria. Use only local evidence: sibling-repository references document
dependencies and ownership, not access to or conformance by those repositories.

## Authority hierarchy

Apply this order, highest authority first:

1. The approved [vision](docs/VISION.md) defines direction, purpose, outcomes, scope, and boundaries.
2. The approved [requirements baseline](docs/requirements/README.md) defines required behavior,
   constraints, interfaces, and acceptance conditions.
3. Approved architecture, design documentation, and ADRs define structure, responsibility
   allocation, security boundaries, and architectural decisions.
4. The approved [next-MVP release baseline](docs/releases/next-mvp.md) selects the requirements,
   compatibility unit, interface lifecycle, target registry state, validation evidence, and
   external blockers for the implementation increment. It narrows scope without overriding the
   vision, requirements, or approved architecture.
5. Versioned organization and repository interface documentation present in this repository
   defines cross-repository interactions and ownership boundaries.
6. Code, workflows, schemas, tests, fixtures, packages, examples, and other implementation artifacts
   are blueprints and evidence only.

An existing or operating artifact never overrides a higher-authority source. Once deliberately
aligned, an artifact may enforce that source executably; a later conflict must be reported and
resolved, not allowed to redefine the requirement silently. Preserve every draft, proposed,
superseded, or unapproved status. If authoritative sources conflict or materially leave ownership
undecided, stop affected work, name the sources and identifiers under [Open issues](#open-issues),
and do not infer a resolution from implementation. Authority, approval, boundary, and contract
changes require the governed review in the [requirements baseline](docs/requirements/README.md).

## Vision

`portfolio-tasks` is Young Consultations' governed portfolio front door for its AI-assisted SDLC.
It turns human intent into structured, prioritized, traceable work, preserves explicit human
approval, and initiates authorized execution without owning the organization control plane. GitHub
Issues are authoritative executable portfolio records; Projects are projections and cannot
authorize execution. Read the [vision](docs/VISION.md) first for purpose and boundaries.

## Current project state

This repository owns source issue identity and governed portfolio state: intake/provenance,
classification/decomposition, readiness, priority/risk/dependencies, human approval and
invalidation, exactly-one-target task construction, routing initiation, lifecycle/result
projection, reconciliation, and portfolio audit evidence. When it is the selected target, a
separately bounded adapter enforces target policy and draft-only publication; that role cannot
approve work or bypass the router.

GitHub Issues in `Young-Consultations/portfolio-tasks` are the source of truth for executable
portfolio state. At the single current contract boundary, `Executor` must be `codex` and
`Execution status` must be `approved`; those values do not replace the richer human-approval and
material-revision checks required by the approved baseline.

It does **not** own organization schemas, registry, compatibility, shared routing/result transport;
other repositories' architecture, source, credentials, validation, PRs, or delivery; autonomous
approval; merge, release, deployment, or production decisions; Slugger internals; consulting
methodology; or GitHub internals. The control plane, GitHub, registered targets, Slugger, and
consulting-playbook are documented dependencies or optional collaborators whose availability and
conformance are not presumed. The project is pre-production with one current user; this does not
relax any security or approval boundary.

Exact organization schemas and fixture files may be vendored solely as byte-for-byte,
digest-pinned offline compatibility inputs. Their presence never transfers contract ownership,
permits local extension, proves a release/tag exists, or authorizes activation.

## Architecture

Follow this ordered reading path after the vision:

1. [Requirements precedence](docs/requirements/README.md), [project scope](docs/requirements/ProjectRequirements.md),
   and the [SRS](docs/requirements/SoftwareRequirementsSpecification.md).
2. [Functional requirements](docs/requirements/FunctionalRequirements.md), [nonfunctional requirements](docs/requirements/NonFunctionalRequirements.md),
   [business rules](docs/requirements/BusinessRules.md), and [glossary](docs/requirements/Glossary.md).
3. [Requirements traceability](docs/requirements/RequirementsTraceability.md) and the exact
   [next-MVP selection](docs/releases/next-mvp.md). A `Must` priority alone is not MVP inclusion.
4. [Repository context](docs/requirements/RepositoryContext.md) and [repository boundaries](docs/architecture/RepositoryBoundaries.md)
   before ownership, authority, routing, data, or target changes.
5. [Software architecture](docs/architecture/SoftwareArchitecture.md), [high-level design](docs/architecture/HighLevelDesign.md),
   [component design](docs/architecture/ComponentDesign.md), [low-level design](docs/architecture/LowLevelDesign.md),
   and [architecture traceability](docs/architecture/ArchitectureTraceability.md) before structural
   work; consult other [`docs/architecture`](docs/architecture) views for their affected concerns.
6. [Interface architecture](docs/architecture/InterfaceArchitecture.md), [control-plane interface](docs/requirements/Interface-OrganizationControlPlane.md),
   [target interface](docs/requirements/Interface-TargetRepositories.md), and relevant
   [GitHub](docs/requirements/Interface-GitHub.md), [Slugger](docs/requirements/Interface-Slugger.md),
   or [consulting-playbook](docs/requirements/Interface-ConsultingPlaybook.md) interface before
   boundary work. Local records neither grant sibling access nor prove sibling conformance.
7. [Security architecture](docs/architecture/SecurityArchitecture.md) before identity, approval,
   credentials, untrusted input, logging, AI execution, or publication work.
8. [README](README.md), [branch protection](docs/branch-protection.md), and relevant artifacts only
   for operational evidence after higher-authority sources establish intended behavior.

## Coding standards

- Treat issues, events, payloads, and AI output as untrusted. Validate identity, schema, authority,
  target policy, sensitivity, and correlation at every boundary; ambiguity fails closed.
- Preserve explicit human, revision-bound approval. Intake, priority, Projects, or bot activity
  cannot authorize. Keep portfolio and target roles, credentials, and audit domains distinct.
- Use deny-by-default, repository- and operation-scoped least privilege. Target execution cannot
  assume portfolio or sibling access.
- Keep credentials only in approved platform secret facilities. Never place secrets, tokens,
  private or credential-bearing URLs, or prohibited data in issues, config, payloads, prompts,
  logs, artifacts, fixtures, documentation, or patches. Redact diagnostics.
- Automation may create or reuse at most one **draft** PR. It may never self-approve, mark ready,
  merge, release, deploy, or interpret transport acknowledgement as success.
- Make focused, traceable changes; pre-production status and user count weaken no boundary.

## ADRs

The [ADR collection](docs/architecture/ADR.md) covers issue authority, revision-bound approval,
external routing, reconciliation, target sovereignty, fail-closed behavior, and separated
portfolio/target roles. Every ADR is explicitly **Proposed normative architecture** until the
architecture baseline is approved; do not present it as approved. Frozen next-MVP decisions are
recorded by the [release baseline](docs/releases/next-mvp.md) and approved requirement/interface
sources.

## Implementation authority and compatibility policy

- For implementation decisions, the vision, approved requirements, approved architecture/design,
  approved ADRs, applicable versioned interfaces, and approved next-MVP selection are the only
  product and architectural authorities. Preserve the documented status of each source: a proposed
  ADR is guidance at its recorded status, not an approved decision.
- This project is pre-production and currently has **no backward-compatibility requirement**.
- Existing source code, workflows, tests, fixtures, schemas, and operational examples are
  implementation blueprints, not requirements or architectural authority. Reuse them only when
  they conform to the authoritative sources.
- Later tasks may modify, replace, or remove conflicting, duplicated, obsolete, or out-of-scope
  code, workflows, schemas, tests, fixtures, packages, and examples. Git history is the recovery
  mechanism for removed implementation and historical behavior.
- The repository must converge on **one supported MVP contract and one active implementation path
  for each responsibility**. The local recovery baseline selects payload
  `ai-sdlc-contract/v2` and the published `ai-sdlc-v2.3.2` compatibility unit. Its
  schema and fixture baseline derives from the corrected recovery commit
  `Young-Consultations/.github@e27b8a541afbd27b4be5606a19ffa43637ad312a`.
  Historical `c6090e5bbadcc2102a1cb91875466e9decdada1e` remains immutable 2.3.0
  evidence and must never be amended or retagged.
- Do not preserve backward compatibility, deprecated execution paths, duplicate contracts,
  wrappers, aliases, transitional structures, migration layers, dual-schema validation, obsolete
  workflow inputs, or fallbacks unless an authoritative requirement explicitly requires them. A
  version/discriminator may identify the one current payload without requiring earlier-version
  support.
- Never infer behavior, compatibility, access, readiness, or authority from a sibling repository.
  A cross-repository assumption is usable only when an explicit, applicable, versioned interface or
  release document in this repository states it. If implementation needs an external dependency
  or fact that those local documents do not establish, fail closed and report a blocker; do not
  invent the missing requirement or architecture.
- Legacy-looking files are not automatically disposable; trace their disposition during the
  relevant implementation task.
- Recovery changes must preserve one active source path, one active target path, and one result
  projection path; Git history is the recovery mechanism for removed duplicate implementations.

## MVP boundaries

The exact [next-MVP inclusion list](docs/releases/next-mvp.md) is authoritative. In summary: one
revision-bound human-approved issue; exact closed task construction and routing to exactly one
router-activated target; idempotent initiation/reconciliation; local authorization when this
repository is the target; at most one created or reused draft PR; authenticated receiver-to-source
result projection; and complete deterministic shared-oracle validation through the real adapter
seam with all external effects trapped.

`FR-CLS-04`, `FR-GOV-01`, `FR-OUT-02`, `FR-OUT-03`, `FR-PRJ-01`, `FR-PRJ-02`, and `FR-RPT-01` are
deferred. Unlisted NFRs are later-release constraints, not waived or satisfied. Merge, release,
deployment, production operations, production-readiness claims, automatic merge, autonomous
approval, and sibling implementation are out of scope. Immutable compatibility records target
capabilities but not current enabled or disabled state. Mutable activation is owned and enforced by
the `.github` router before dispatch; target adapters neither read historical activation nor change
it. Unknown or inactive selections fail closed at the router, while a dispatched target repeats its
local identity, contract, schema, capability, draft-only, concurrency, delivery, and ownership
checks.

## Development workflow

The [README](README.md) supports Python 3.12 setup with `python -m pip install -e '.[dev]'`. The
[CI workflow](.github/workflows/ci.yml) supports these root-level checks; select focused checks while
iterating and run the full applicable suite before completion:

```bash
ruff check .
ruff format --check portfolio_tasks scripts tests
mypy portfolio_tasks
python -m pytest
python scripts/test_codex_execute_contract.py
python scripts/run_tc_mvp_ci_001.py
$(go env GOPATH)/bin/actionlint -shellcheck=
git diff --check
```

Do not invent or silently skip a required validator.

## Prompt rules

Before every implementation task, load and read this file completely, then follow its ordered
document reading path and repository boundaries before inspecting implementation blueprints or
proposing changes. Every future AI task must identify applicable approved requirement IDs,
architecture/design sources, ADR status, interfaces, security constraints, and MVP selection, and
evaluate implementation only as blueprints. Never silently change approved requirements,
architecture, security boundaries, or the active contract. Report material contradictions rather
than resolving them from code.

Before removing or replacing an artifact, the implementing agent must:

1. Identify its active, obsolete, duplicated, or deferred behavior.
2. Trace that behavior to requirements, architecture, interface documentation, or ADRs.
3. Search for and address all references and dependencies.
4. Preserve behavior required by an active requirement.
5. Update affected tests and documentation consistently.
6. Verify no orphaned imports, links, workflow/schema references, fixtures, or package dependencies.
7. Run the full applicable validation suite.
8. Report each material removal or replacement and its reason.

## Open issues

No material contradiction among approved repository-owned next-MVP sources was identified. Preserve
these statuses and gaps rather than inventing solutions:

- [ADR.md](docs/architecture/ADR.md) remains **Proposed normative architecture**, not approved.
- The portfolio adapter has complete accepted `TC-MVP-CI-001` evidence: 29 scenarios pass, 22
  invoke the real adapter seam, and all prohibited-effect counters are zero. The published
  `ai-sdlc-v2.3.2` compatibility unit and immutable registry evidence cover all four core targets;
  this does not prove mutable activation or that a controlled live forwarding run succeeds.
- Current target activation is mutable organization control-plane state. This repository neither
  records it as immutable compatibility nor changes or bypasses it.
- All four targets remain disabled. Issue #117 owns deliberate first-target activation; reviewed
  receiver identities and the controlled live acceptance run remain external gates.
- Security/governance owners, role membership, separation-of-duty classes, data classification,
  retention/legal hold, incident handling, and operational objectives remain open in
  [Assumptions and Open Questions](docs/requirements/Assumptions.md). A safety-, authority-, or
  contract-affecting unknown blocks affected automation.

The previous context incorrectly elevated issue forms, workflows, and contracts together as
implemented-behavior authority and treated checked-in routing as the governing path. This replaces
that rule: approved documentation governs the product; existing workflows are nonconforming
pre-baseline blueprints where the [release baseline](docs/releases/next-mvp.md) says so.

## Maintenance rule

Update this file when authoritative files move, approval status changes, ownership boundaries
change, or current interface policy changes. Recheck links and commands in the same change. Keep
historical behavior in Git history, release records, or ADRs rather than multiple active policies
or execution paths here.
