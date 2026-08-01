# GitHub Projects Phase 2 synchronization contract

This document defines the optional Phase 2 automation that mirrors canonical
issue metadata from `Young-Consultations/portfolio-tasks` into an organization
GitHub Project item.

Phase 2 remains disabled by default and should stay in `proposed` operating
status until the organization-owned project identifier and least-privilege
credentials are available.

## Prerequisite gate

Before enabling Phase 2, confirm the Phase 1 governance prerequisite is merged
and adopted:

- Phase 1 issue `#17` must be complete and merged.
- The manual Phase 1 contract in `docs/github-projects-phase1-contract.md`
  remains the source of truth for field names, allowed values, and governance.
- Set repository variable `PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE=true` only
  after that verification is complete.

If the prerequisite variable is not true, Phase 2 exits fail-closed without
performing project mutations.

## Contract scope and source of truth

Phase 2 synchronization follows the Phase 1 deterministic field mapping
exactly. These issue-form sections are synchronized to same-named project
fields in deterministic order:

- `Project`
- `Priority`
- `Executor`
- `Execution status`
- `Target repository`
- `Parallel-safe`
- `Dependency issue references`
- `Risk`
- `Estimated scope`
- `Task type`

Issue form values in `Young-Consultations/portfolio-tasks` remain canonical.
Project fields are synchronized outputs and never become dispatch authorization.

## Configuration and least privilege

Workflow: `.github/workflows/sync-github-projects-phase2.yml`

Required configuration when enabling synchronization:

- Repository variable `PROJECTS_PHASE2_SYNC_ENABLED=true`
- Repository variable `PROJECTS_PHASE2_PROJECT_ID=<organization-project-node-id>`
- Repository variable `PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE=true`
- Repository secret `PROJECTS_PHASE2_TOKEN=<least-privilege token>`

Least-privilege boundary for `PROJECTS_PHASE2_TOKEN`:

- Read access to `Young-Consultations/portfolio-tasks` issues.
- Read/write access only to the target organization GitHub Project used for
  portfolio governance updates.
- No permissions for repository contents write, pull-request publication,
  workflow dispatch, or unrelated organization resources.

## Safe behavior and failure modes

The synchronization command `python -m portfolio_tasks.cli sync-projects-phase2`
is fail-closed and non-destructive under missing configuration:

- If `PROJECTS_PHASE2_SYNC_ENABLED` is not true, outcome is `disabled` and no
  API mutation is attempted.
- If enabled but prerequisite, project ID, or token is missing, outcome is
  `failed` with clear summary errors and no API mutation.
- If required project fields or single-select options are missing, outcome is
  `failed` before any update mutation.
- If issue metadata already matches project field values, outcome is `no-op`.

Updates are deterministic and idempotent: rerunning with unchanged input yields
`no-op` and does not alter unrelated project data.

## Operations

Enable:

1. Verify Phase 1 issue `#17` is merged and adopted.
2. Configure `PROJECTS_PHASE2_PROJECT_ID` with the organization project node ID.
3. Create `PROJECTS_PHASE2_TOKEN` with least privilege.
4. Set `PROJECTS_PHASE2_PHASE1_ISSUE_17_COMPLETE=true`.
5. Set `PROJECTS_PHASE2_SYNC_ENABLED=true`.
6. Run a manual workflow dispatch with `dry_run=true` first.

Disable:

- Set `PROJECTS_PHASE2_SYNC_ENABLED=false` (or unset it).

Rollback:

1. Disable synchronization (`PROJECTS_PHASE2_SYNC_ENABLED=false`).
2. Revert any unwanted project field values manually in GitHub Projects.
3. Keep issue metadata authoritative in `portfolio-tasks`; do not rewrite issue
   history for rollback.

Operation:

- Trigger automatically on issue open/edit/label/unlabel/reopen/close events.
- Manual `workflow_dispatch` supports explicit `source_issue_number` and
  defaults to `dry_run=true`.

Troubleshooting:

- `PROJECTS_PHASE2_PROJECT_ID is not a ProjectV2`: verify the project node ID.
- `Project is missing required field`: add missing field using exact Phase 1
  field name.
- `Project field option missing`: add the missing single-select option exactly.
- `Pull requests are not synchronized`: provide an issue number, not a PR.
- Token or permission failures: verify `PROJECTS_PHASE2_TOKEN` exists and has
  only the required issue-read plus project-read/write permissions.
