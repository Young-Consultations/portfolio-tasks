# Interface Requirements — Young-Consultations/slugger

## Purpose and responsibilities

Slugger is expected to own its AI Software Factory product, product-generation internals,
architecture, target validation, review artifacts, and delivery disposition. `portfolio-tasks` owns
portfolio intent, approval, and outcome linkage. The organization control plane owns the shared
execution route. A direct backlog projection MAY exist, but it MUST NOT become a second executable
authority or be confused with a routed canonical task.

## Required interaction modes

### Governed execution handoff

When Slugger is a target, the organization contract in
[Interface-OrganizationControlPlane.md](Interface-OrganizationControlPlane.md) applies. Slugger
MUST accept only registered, authenticated, version-compatible, target-specific tasks; enforce its
own policy; operate without portfolio-repository access; produce validated correlated results; and
reserve readiness, merge, and production decisions for its owner.

### Optional backlog projection

If portfolio work is mirrored into a Slugger issue, input MUST include source repository/issue,
source revision, managed/unmanaged indicator, non-sensitive title/body context, and lifecycle
intent. Output MUST include a stable mirror reference and synchronization outcome. The mirror MUST
display provenance and authority, MUST NOT independently approve/route work, and MUST preserve
Slugger-owned discussion or fields during managed updates.

Required semantic events are source eligible/ineligible, source edited/closed/reopened, mirror
created/updated/closed/reopened, drift/conflict, route accepted, target status, result, and target
disposition where available. Specific event delivery is not assumed.

## Contract, failure, retry, and idempotency expectations

The mapping SHALL identify every managed field, authority, synchronization direction, label/state
translation, and close/reopen behavior. One source SHALL map to at most one active managed mirror;
replay SHALL find or update that mirror. Multiple candidates, missing provenance, destructive
conflict, permission denial, incompatible versions, and sensitivity uncertainty SHALL fail closed
and require reconciliation. Transient failures MAY retry with stable identity and bounded backoff;
permanent validation or authorization errors MUST surface to the source owner. A mirror failure
MUST NOT change approval or claim execution failure.

Version changes SHALL follow explicit compatibility and migration rules. Direct mirror contracts
and organization execution contracts MUST be distinguishable and independently versioned.

## Data and ownership

The portfolio issue owns intent, approval, priority, and portfolio lifecycle. Slugger owns its
architecture, internal generation state, source, validation, PRs, and delivery decisions. Copied
data retains provenance; target results are externally owned evidence represented in the portfolio
only after validation.

## Assumptions, unknowns, and future validation

Current repository material suggests Slugger can be a target and that an issue mirror has been
used, but this specification does not assert Slugger behavior. Unknowns include whether mirroring
remains desired, allowed repositories/labels, managed fields, identity lookup, target entry point,
contract versions, executor support, result transport, state mapping, permissions, quotas, service
objectives, retention, cancellation, and owner escalation. The Slugger and control-plane owners
MUST validate these before enabling either interaction. If mirroring has no approved business
purpose, it SHOULD be retired rather than preserved as accidental architecture.
