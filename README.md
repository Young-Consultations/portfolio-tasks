# portfolio-tasks

`portfolio-tasks` is Young Consultations' governed portfolio front door for AI-assisted software
delivery. GitHub Issues are the authoritative executable portfolio records; Projects are
projections only, and this repository does not own organization contracts, shared routing, or
sibling-repository execution.

Read [`AI_CONTEXT.md`](AI_CONTEXT.md) first. The authority order is:

1. [`docs/VISION.md`](docs/VISION.md)
2. [`docs/requirements/README.md`](docs/requirements/README.md)
3. approved architecture and interface documents
4. [`docs/releases/next-mvp.md`](docs/releases/next-mvp.md)

## Current next-MVP path

The one selected interface is organization release `2.2.0`, payload
`ai-sdlc-contract/v2`, pinned at
`c6090e5bbadcc2102a1cb91875466e9decdada1e`. Organization schemas, fixtures, target capabilities,
router, and result receiver remain organization-owned and are not copied into this repository.

The sole reusable target adapter is [`.github/workflows/codex-execute.yml`](.github/workflows/codex-execute.yml).
It accepts only `execution_input_json` and the router's `concurrency_group`, consumes immutable
schemas and target capabilities directly at the compatibility SHA, independently gates the
organization caller, and keeps
Codex isolated from publication and result credentials. The prior dispatch, artifact-input,
mutable-label, and local-result paths remain removed; there is no supported alias.

The target policy core validates local admission, derives publication ownership solely from
`delivery_id`, binds that identity to the canonical payload digest, and fails closed on ambiguous
draft ownership or conflicting result replay. It is not an alternate router, contract owner,
approval mechanism, or sibling publication path.

GitHub Projects synchronization and Slugger issue mirroring are not part of the selected MVP:
`FR-PRJ-01` and `FR-PRJ-02` are deferred, and direct sibling synchronization conflicts with the
control-plane and target ownership boundaries. No workflow in this repository currently mutates a
Project or a sibling repository.

## Development

Use Python 3.12:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
mypy portfolio_tasks
python -m pytest
$(go env GOPATH)/bin/actionlint -shellcheck=
git diff --check
```

CI uses deterministic local tests and does not invoke Codex, create a branch, publish a pull
request, or route cross-repository work. The complete organization-owned `TC-MVP-CI-001` fixture
oracle at the compatibility SHA is the required shared conformance source.

## External blockers

The merged result receiver contract and complete executable `TC-MVP-CI-001` oracle are consumed
from the compatibility SHA. Current target activation is separate mutable `.github` control-plane
state enforced by the router; this repository neither pins nor changes it. Administrators must
configure the router actor allowlist and separately scoped contract, Codex, publication, and result
credentials before a live call. Operational readiness and activation remain owner decisions and
must not be inferred from, or reimplemented alongside, immutable compatibility artifacts.
