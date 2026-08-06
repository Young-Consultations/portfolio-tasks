# AI Context: portfolio-tasks

This file is a navigation index for AI agents. It links to canonical sources and does not replace repository contracts, issue metadata, or workflow definitions.

## Vision

`portfolio-tasks` is the portfolio backlog repository. It owns structured intake, governance metadata, and dispatch gating for approved work across project repositories.

Canonical reference:

- [Young Consultations AI-SDLC vision](docs/VISION.md) — authoritative for organizational intent
  and this repository's purpose and boundaries
- [Repository overview and governance contract](README.md)

The issue form, workflows, and applicable contracts remain authoritative for implemented behavior.

## Current project state

GitHub Issues in `Young-Consultations/portfolio-tasks` are the source of truth for backlog state and execution approval. They use structured issue-form fields plus deterministic labels.

Approval for Codex dispatch is explicit and manual:

- `Executor` must be `codex`.
- `Execution status` must be `approved`.

Canonical references:

- [ChatGPT task issue form](.github/ISSUE_TEMPLATE/chatgpt-task.yml)
- [Backlog governance and approval rules](README.md)
- [GitHub Projects Phase 1 contract](docs/github-projects-phase1-contract.md)
- [GitHub Projects synchronization contract](docs/github-projects-sync.md)

## Architecture

The repository enforces intake and approval contracts, then routes approved tasks. Issue creation or editing alone is not execution authorization.

Repository components and canonical references:

- [Python package (`portfolio_tasks`)](portfolio_tasks)
- [Automations and helper scripts](scripts)
- [Repository tests](tests)
- [GitHub workflows](.github/workflows)
- [Additional documentation](docs)
- [Approval router workflow](.github/workflows/route-approved-task.yml)
- [Trusted Codex execution workflow](.github/workflows/codex-execute.yml)

## Coding standards

- Follow the existing Python and workflow conventions in nearby files.
- Keep changes narrowly scoped and avoid unrelated refactors.
- Do not include secrets, private URLs, tokens, or credentials in code or documentation.
- Treat this file as an index; update the linked canonical document when behavior changes.

Canonical validation is defined by the [CI workflow](.github/workflows/ci.yml). Local checks include `python -m pytest`, `ruff check .`, `mypy portfolio_tasks`, `git diff --check`, and `actionlint`.

## ADRs

The repository does not currently maintain a dedicated ADR collection. Until one is added, use these documents as the canonical record of architectural and synchronization decisions:

- [Primary repository documentation](README.md)
- [GitHub Projects Phase 1 contract](docs/github-projects-phase1-contract.md)
- [GitHub Projects synchronization contract](docs/github-projects-sync.md)

## Development workflow

Start from the structured backlog issue, preserve the manual approval gate, implement the scoped change, and run the repository-standard validation before proposing it for review. Changes to routing or execution must remain consistent with:

- [Approval router workflow](.github/workflows/route-approved-task.yml)
- [Trusted Codex execution workflow](.github/workflows/codex-execute.yml)
- [CI workflow](.github/workflows/ci.yml)

## Prompt rules

Execution prompts must follow the [execution prompt contract template](portfolio_tasks/prompts/execution.md). Do not treat issue creation or edits as approval, and do not weaken the explicit executor and execution-status gates described above.

## Open issues

No unresolved context-documentation gaps are currently known. When a required canonical source is unavailable, record the gap here with a clear owner and remediation path rather than inventing or duplicating a contract.
