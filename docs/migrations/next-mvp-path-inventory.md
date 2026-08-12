# Next-MVP implementation-path inventory

This inventory records the reconciliation against the approved requirements and the next-MVP
release selection. Git history, rather than active files, preserves removed blueprints.

| Candidate | Decision | Disposition and authority |
| --- | --- | --- |
| Structured GitHub issue intake and deterministic parser | KEEP | `FR-INT-01..03` and `FR-CLS-01..03` are selected. Issues remain authoritative; intake does not approve or execute. |
| Codex subprocess, prompt renderer, and deterministic repository validation utilities | KEEP | They are target-side utilities supporting `FR-TGT-01..02`, `NFR-AI-01..02`, and `NFR-TST-01..02`; without a workflow they cannot route, execute, or publish. |
| `route-approved-task.yml` | REMOVE | The release baseline explicitly identifies its tag/package consumption, live-label recheck, and result handling as nonconforming. Its event trigger could initiate an obsolete second execution path. |
| `codex-execute.yml` | REMOVE | Its artifact input, control-plane package checkout, queued-label authorization alias, local source update, and artifact result path conflict with the one v2 target interface and separate receiver. |
| Slugger issue synchronization workflow and Python mirror stack | REMOVE | Direct sibling mirroring is not a selected MVP responsibility; Slugger is disabled, and target/control-plane ownership must not be absorbed here. |
| GitHub Projects intake/synchronization workflows, implementation, tests, and operating contracts | REMOVE | `FR-PRJ-01` and `FR-PRJ-02` are expressly deferred. Projects cannot become an execution authority. |
| Legacy dispatch validator, router gate, marker implementation, publication scripts, and tests | REMOVE | These existed only for the removed pre-baseline workflows and encoded local aliases/transport not required by the closed v2 contract. |
| Organization schemas, registry, and shared fixtures | REMOVE / do not add | The control plane owns them. The release baseline requires direct immutable consumption and forbids a duplicate local authority. None is checked in. |
| Proposed ADR collection | KEEP | It remains architectural guidance with its recorded **Proposed normative architecture** status; it is not represented as approved. |
| Reporting, automated Project projection, merge/release/deploy, and target activation | DEFER | These are deferred, later-release, human-controlled, or organization control-plane responsibilities and are not implemented by this cleanup. |

## Supported state after migration

There is one documented contract selection: release `2.2.0`, payload `ai-sdlc-contract/v2`, at
`c6090e5bbadcc2102a1cb91875466e9decdada1e`. The sole replacement target workflow is
`.github/workflows/codex-execute.yml`; the removed aliases and transports remain unsupported. Normal
CI and retained source-side utilities have no Codex, branch, pull-request, Project, sibling-write,
router, or result-publication side effect.

## External dependencies

The result receiver contract and complete executable `TC-MVP-CI-001` fixture oracle are available
at the compatibility SHA. Current activation, credentials, and live operational readiness remain
organization-owned external state and decisions. They do not authorize a local contract copy,
activation check, result receiver, or substitute workflow.
