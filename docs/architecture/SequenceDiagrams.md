# Sequence Diagrams

## Intake, remediation and approval

```mermaid
sequenceDiagram
  actor A as Task author
  participant P as Portfolio application
  participant I as Authoritative issue
  participant G as Governance policies
  actor H as Human approver
  A->>P: Submit structured intent + provenance
  P->>G: Validate classification/sensitivity/completeness
  alt invalid or uncertain
    G-->>P: Violations / quarantine reason
    P-->>A: Actionable remediation (not approved)
  else valid candidate
    P->>I: Create initial revision (not approved)
    I-->>P: Work ID + revision
    H->>P: Approve work ID + observed revision + reason
    P->>G: Verify authority/readiness and compute digest
    G-->>P: Eligible
    P->>I: Compare-and-set approval evidence
    I-->>H: Approved revision or revision conflict
  end
```

## Material edit after approval (alternate flow)

```mermaid
sequenceDiagram
  actor E as Editor
  participant P as Portfolio application
  participant I as Issue
  participant M as Material-change policy
  E->>P: Patch with expected revision
  P->>M: Classify delta
  M-->>P: Material
  P->>I: Atomically apply revision + invalidate approval
  I-->>P: New revision, approval stale
  P-->>E: Revalidation and fresh human approval required
```

## Successful routing and outcome

```mermaid
sequenceDiagram
  actor H as Authorized human
  participant P as Portfolio
  participant D as Idempotency/evidence
  participant C as Control plane
  participant T as Target
  actor R as Target reviewer
  H->>P: Initiate approved task
  P->>P: Recheck revision, approval, dependency, sensitivity, compatibility
  P->>D: Reserve delivery ID + semantic digest
  P->>C: Canonical task
  C-->>P: Authenticated accepted receipt
  C->>T: Routed target task
  T->>T: Shared + target-local validation
  T-->>C: accepted / executing
  T-->>C: terminal result + evidence + draft reference
  C-->>P: Correlated ordered events
  P->>D: Deduplicate and preserve audit
  P->>P: Link result; await human disposition
  R->>T: Review / merge or reject decision
  T-->>C: Disposition (when contracted)
  C-->>P: Disposition evidence
```

## Timeout, replay and reconciliation failure flow

```mermaid
sequenceDiagram
  participant P as Portfolio
  participant D as Idempotency record
  participant C as Control plane
  P->>D: Reserve delivery-7 + digest-A
  P->>C: Submit delivery-7
  C--xP: Timeout after possible acceptance
  P->>D: Mark handoff-uncertain
  P->>C: Query delivery-7
  alt found
    C-->>P: Authenticated accepted/status
    P->>D: Finalize without resubmission
  else contract proves never accepted and retry safe
    C-->>P: Not found + retry-safe
    P->>C: Retry same delivery-7 + digest-A
  else no conclusive evidence
    C-->>P: Unknown/Unavailable
    P->>D: Keep blocked; alert human reconciliation owner
  end
  Note over P,C: A replay with digest-B is a conflict, never an update.
```

## Invalid or out-of-order result

```mermaid
sequenceDiagram
  participant C as External producer
  participant P as Result ingestor
  participant Q as Quarantine
  participant I as Issue
  C->>P: Result event
  P->>P: Authenticate, validate schema/version/correlation/order
  alt exact duplicate
    P-->>C: Acknowledge duplicate/no-op
  else stale but valid
    P->>Q: Retain audit; no state regression
  else forged, divergent, unknown or impossible
    P->>Q: Quarantine + alert
    P-->>C: Rejected/conflict
  else valid
    P->>I: Apply compared transition/result link
  end
```

## Project drift

```mermaid
sequenceDiagram
  participant I as Issue
  participant P as Projector
  participant G as GitHub Project
  I-->>P: Authoritative revision
  P->>G: Read projected item
  alt no drift
    P-->>I: Record freshness only
  else issue-owned field drift
    P->>G: Correct using revision/mapping identity
    G-->>P: Updated or quota/permission error
  else human-owned field conflict
    P-->>P: Preserve value and create reconciliation item
  end
  Note over G,I: Project state never grants approval.
```

