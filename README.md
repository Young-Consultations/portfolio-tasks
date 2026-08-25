# portfolio-tasks

`portfolio-tasks` is Young Consultations' governed portfolio front door for AI-assisted software
delivery. GitHub Issues are the authoritative executable portfolio records; Projects are
projections only. This repository owns portfolio approval and source projection, not the
organization router or sibling-repository execution.

Read [`AI_CONTEXT.md`](AI_CONTEXT.md) first. The authority order is:

1. [`docs/VISION.md`](docs/VISION.md)
2. [`docs/requirements/README.md`](docs/requirements/README.md)
3. approved architecture and interface documents
4. [`docs/releases/next-mvp.md`](docs/releases/next-mvp.md)

## Issue 135 recovery state

The current published compatibility unit is `ai-sdlc-v2.3.2` in `Young-Consultations/.github`,
pointing to immutable commit `5738ace3ee90dde11336f8f8099e64e5645f7139`. Its schema and fixture
baseline derives from corrected recovery commit
`e27b8a541afbd27b4be5606a19ffa43637ad312a`. Historical commit
`c6090e5bbadcc2102a1cb91875466e9decdada1e` remains immutable 2.3.0 evidence and is never
amended or retagged.

The exact shared v2 schemas and `TC-MVP-CI-001` fixture files are vendored only for deterministic,
offline compatibility validation. Their approved Git blob identities are bound in
[`config/mvp-conformance-pin.json`](config/mvp-conformance-pin.json); they are not
repository-owned extensions or alternate contracts.

The one target entry point is
[`.github/workflows/codex-execute.yml`](.github/workflows/codex-execute.yml). It exposes
`workflow_dispatch` with exactly `execution_input_json` and `concurrency_group`, validates the
closed execution schema and portfolio target policy, reconciles the canonical branch and managed
draft before Codex, and sends a canonical result through the published
`ai-sdlc-v2.3.2` organization receiver. Codex receives neither publication nor result credentials.
Only the workflow may create one delivery-owned branch and draft PR; it cannot merge, release, or
deploy.

The portfolio source path constructs the exact closed task schema, binds approval to every
authoritative routing field, and grants the reusable router its required `actions: read`
permission. Successful router admission writes the receiver-compatible
`ai-sdlc-admission:v2` journal marker. Receiver-validated results return through authenticated
`repository_dispatch`; the target never directly invokes source projection or supplies a source
write token.

## Evidence and safety state

[`.ai-sdlc/conformance/tc-mvp-ci-001.json`](.ai-sdlc/conformance/tc-mvp-ci-001.json) records all
29 shared scenarios passing through the real portfolio adapter seam, including 22 adapter
invocations, with all prohibited Codex, branch, commit, push, PR, merge, release, deployment,
production, and secret-output counters at zero.

This evidence is compatibility evidence, not activation or production readiness. The portfolio
target remains disabled. The published `ai-sdlc-v2.3.2` unit and accepted immutable evidence cover all four core targets.
Mutable activation remains disabled; reviewed receiver identities and a controlled live acceptance
run are still required.

GitHub Projects synchronization and Slugger issue mirroring remain outside the selected MVP. No
workflow here mutates a Project or a sibling repository.

## Development

Use Python 3.12:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check portfolio_tasks scripts tests
mypy portfolio_tasks
python -m pytest
python scripts/test_codex_execute_contract.py
python scripts/run_tc_mvp_ci_001.py
$(go env GOPATH)/bin/actionlint -shellcheck=
git diff --check
```

Normal CI is deterministic and has no Codex, routing, branch, push, PR, receiver, tag, release,
deployment, or production effect.
