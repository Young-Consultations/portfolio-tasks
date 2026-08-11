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
`f2491872976a4dcc1633997954c03c07cbc4fced`. Organization schemas, fixtures, registry, router,
and result receiver remain organization-owned and are not copied into this repository.

No live routing or target-execution workflow is enabled in this repository yet. The former
workflows used a pre-baseline tag, an undocumented package/checkout transport, mutable live-label
authorization, and local result publication. Keeping those workflows active could cause a second
execution or publication outside the selected contract, so they were removed rather than described
as supported. A conforming implementation must use the pinned router and separate result receiver,
consume schemas directly at the compatibility SHA, accept only the documented v2 interface, and
fail closed while the organization receiver remains unable to accept successful live results.

The retained Python code is limited to deterministic intake parsing and target-side implementation
utilities (prompt rendering, trusted validation, and the Codex subprocess boundary). These
utilities are not an alternate router, contract, approval mechanism, or publication path.

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
request, route cross-repository work, or require organization-owned fixtures that have not been
published.

## External blockers

Live next-MVP enablement remains blocked by the organization-owned result receiver's approved
fail-closed skeleton, publication of complete executable `TC-MVP-CI-001` fixtures, and any required
target enablement. The declared release tag is also not yet created; consumers must use the full
compatibility SHA regardless. These dependencies must be resolved by their owners and must not be
reimplemented locally.
