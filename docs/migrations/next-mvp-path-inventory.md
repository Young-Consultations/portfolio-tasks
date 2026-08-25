# Next-MVP implementation-path inventory

This inventory records the issue 135 reconciliation against the approved requirements and recovery
baseline. Git history, rather than active aliases, preserves removed blueprints.

| Candidate | Decision | Disposition and authority |
| --- | --- | --- |
| Structured issue intake and deterministic parser | KEEP / CORRECT | Issues remain authoritative. Task-type options now map explicitly to the exact v2 vocabulary; intake alone never approves or executes. |
| Source lifecycle policy | KEEP / CORRECT | Exact closed task construction, schema-safe identity, complete authority binding, current-issue reread, and fresh human approval implement `FR-GOV-03..04` and `FR-RTE-01`. |
| `route-approved-task.yml` | KEEP / REPLACE | One source route remains. It grants the router-required `actions: read`, uses the published 2.3.2 router, validates the exact task schema, and writes the canonical v2 admission journal. |
| `codex-execute.yml` | KEEP / REPLACE | One exact two-input `workflow_dispatch` wrapper remains. Artifact/run-ID transport, `workflow_call`-only entry, local activation, and direct source projection are removed. |
| `scripts/codex_target_adapter.py` | ADD AS SOLE ADAPTER | It owns target admission, branch+PR reconciliation, bounded AI execution, validation, draft publication, canonical results, and receiver handoff. |
| Codex runtime and prompt renderer | KEEP AS ADAPTER DEPENDENCIES | They provide autonomous workspace execution and structured completion without publication or result credentials. |
| Historical `portfolio_tasks.target_adapter` and local conformance module | REMOVE | They were parallel contract/adapter paths with obsolete shapes and incomplete evidence. |
| Historical runtime-validation and subprocess helper modules | REMOVE | They were unreferenced after consolidation and would preserve a second orchestration policy. |
| `project-execution-result.yml` | KEEP / REPLACE | It now consumes only authenticated organization-receiver `repository_dispatch`, repeats exact schema/binding checks, and idempotently projects or quarantines. |
| Exact organization schemas and shared fixtures | ADD AS PINNED INPUTS | The control plane remains owner. Byte-exact Git blob identities allow deterministic offline validation and cannot be extended locally. |
| Executable `TC-MVP-CI-001` harness and report | ADD | All 29 shared scenarios run through the real adapter seam with ten explicit prohibited-effect traps. |
| Slugger mirroring and GitHub Projects synchronization | DEFER / ABSENT | These remain outside the selected MVP and cannot become execution authority. |
| Merge, release, deploy, target activation, and receiver trust configuration | DEFER / EXTERNAL | These are human or organization control-plane decisions and are not effects of this recovery change. |

## Supported state after migration

There is one selected payload, one source route, one target adapter, and one source result
projection. The current organization compatibility unit is the published `ai-sdlc-v2.3.2`; its schema and
fixture baseline derives from
`Young-Consultations/.github@e27b8a541afbd27b4be5606a19ffa43637ad312a`. Historical
`c6090e5bbadcc2102a1cb91875466e9decdada1e` remains preserved evidence, not an active consumer
pin.

Normal CI executes exact schema tests, source/target boundary tests, and all 29 shared oracle
scenarios. It has no real Codex, branch, commit, push, PR, receiver, merge, tag, release, deployment,
production, or secret-output effect.

## External gates

The portfolio adapter report is sufficient local compatibility evidence but not activation
evidence. The immutable adapter tags, release, registry bindings, and evidence are published for all four
core targets. Reviewed receiver identities, controlled live verification, and one-at-a-time
review-state activation remain owner-controlled gates for issues #117 and #119.
