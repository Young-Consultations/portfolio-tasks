# AI Context: portfolio-tasks

This file is a navigation index for AI agents. It links to canonical sources and does not replace repository contracts, issue metadata, or workflow definitions.

## 1. Repository mission

`portfolio-tasks` is the portfolio backlog repository. It owns structured intake, governance metadata, and dispatch gating for approved work across project repositories.

Canonical reference:

- [Repository overview and governance contract](README.md)

## 2. Backlog and approval source of truth

The source of truth for backlog state and execution approval is GitHub Issues in `Young-Consultations/portfolio-tasks`, using the structured issue form fields plus deterministic labels.

Approval for Codex dispatch is explicit and manual:

- `Executor` must be `codex`
- `Execution status` must be `approved`

Canonical references:

- [ChatGPT task issue form](.github/ISSUE_TEMPLATE/chatgpt-task.yml)
- [Backlog governance and approval rules](README.md)

## 3. Execution gate and routing boundaries

This repository enforces intake and approval contracts, then routes approved tasks. It does not treat issue creation or edits as automatic execution authorization.

Canonical references:

- [Approval router workflow](.github/workflows/route-approved-task.yml)
- [Trusted Codex execution workflow](.github/workflows/codex-execute.yml)
- [Execution prompt contract template](portfolio_tasks/prompts/execution.md)

## 4. Canonical contract documents

Use these documents as the source for process behavior and project synchronization contracts:

- [Primary repository documentation](README.md)
- [GitHub Projects Phase 1 contract](docs/github-projects-phase1-contract.md)
- [GitHub Projects synchronization contract](docs/github-projects-sync.md)

## 5. Repository map for contributors

- [Python package (`portfolio_tasks`)](portfolio_tasks)
- [Automations and helper scripts](scripts)
- [Repository tests](tests)
- [GitHub workflows](.github/workflows)
- [Additional documentation](docs)

## 6. Validation and documentation checks

Use repository-standard validation, then confirm documentation integrity.

Canonical references:

- [CI workflow checks](.github/workflows/ci.yml)
- [Action workflow linting checks](.github/workflows/ci.yml)

Local validation commands used by this repository include `python -m pytest`, `ruff check .`, `mypy portfolio_tasks`, `git diff --check`, and `actionlint`.

## 7. Safety and change constraints

- Treat this file as an index; update linked canonical docs when behavior changes.
- Do not include secrets, private URLs, tokens, or credentials in documentation.
- Keep task scope tight: avoid unrelated refactors when fulfilling backlog issues.

Canonical reference:

- [Security and execution guardrails](README.md)

## 8. Documented gaps

No unresolved link gaps are currently documented for this index. Add gaps here only when a required canonical document is unavailable, and include a clear owner and remediation path.
