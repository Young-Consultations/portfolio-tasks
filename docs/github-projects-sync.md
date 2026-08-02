# Phase 1 project intake routing

`.github/workflows/sync-github-projects.yml` runs only when an issue receives the
`chatgpt-task` label. It adds that issue to the `Young-Consultations`
organization project named **Portfolio Tasks - Phase 1** and initializes these
single-select fields:

| Project field | Source |
| --- | --- |
| `Execution status` | Fixed intake metadata: `proposed` |
| `Executor` | Fixed intake metadata: `codex` |
| `Priority` | The issue form's required `Priority` section (`P0`-`P3`) |

The router does not infer priority, executor, or status from arbitrary prose.
Project, field, and option node IDs are discovered with GraphQL by their
configured names. The add mutation's returned item ID is used for field
updates. If the issue is already in the project, its existing item ID is used
instead, making reruns safe.

## Required secret and token permissions

Configure the repository Actions secret `SLUGGER_GITHUB_TOKEN`. The workflow
provides it to GitHub CLI and Project GraphQL operations only through the
`GH_TOKEN` environment variable; it is not written to outputs, artifacts, or
logs.

The token must have access to:

- the `Young-Consultations/portfolio-tasks` repository;
- the `Young-Consultations` organization Project **Portfolio Tasks - Phase 1**;
- every destination repository used by later router steps, including
  `Young-Consultations/slugger`;
- read access to issues;
- read and write access to organization Projects; and
- any additional issue write permissions required by later routing steps, such
  as creating or updating destination issues and changing source issue labels.

Grant no unrelated scopes. The workflow's built-in `GITHUB_TOKEN` has only
`contents: read`, is used to check out the trusted router, and is not used for
issue or Project GraphQL operations. Token lifetime depends on the credential
stored in `SLUGGER_GITHUB_TOKEN`; rotate it before it expires and update the
secret without logging its value.

## Project configuration

The organization project must have single-select fields named exactly
`Execution status`, `Executor`, and `Priority`, with options `proposed`, `codex`,
and `P0` through `P3`, respectively. The project lookup currently searches the
first 100 organization projects, and field lookup searches its first 100
fields. Missing projects, fields, options, event data, credentials, or API
permissions stop the workflow with an Actions error annotation explaining the
configuration to fix. Successful logs state whether the item was added or
reused, show the captured Project item ID, and list each initialized field.

The workflow deliberately reacts only to the `labeled` issue event and has an
additional job guard requiring the event's added label to equal
`chatgpt-task`. Removing or editing the label does not route an issue.

## Validation

`tests/test_project_intake.py` validates GraphQL request construction, dynamic
field/option resolution, both new and already-present project items, all three
field-update payloads, and rejection of priority mentioned only in prose.
