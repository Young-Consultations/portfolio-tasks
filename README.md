# portfolio-tasks

This repository owns portfolio-level planning issues and can hand qualifying work to the Slugger implementation backlog.

## Slugger issue synchronization

The workflow `.github/workflows/sync-slugger-issues.yml` synchronizes qualifying issues from `Young-Consultations/portfolio-tasks` to `Young-Consultations/slugger`.

### Eligibility

A source item qualifies only when it is a GitHub issue, not a pull request, and currently has the `chatgpt-task` label. The equivalent GitHub search expression is:

```text
is:issue label:chatgpt-task
```

`is:issue` is a GitHub search qualifier, not a label to create.

### Mapping and idempotency

Each synchronized Slugger issue is titled:

```text
[PORTFOLIO-TASK #<source-issue-number>] <source issue title>
```

The target body contains the portfolio issue body plus generated metadata. The hidden metadata marker is the authoritative idempotency key and is used to find existing open or closed Slugger issues:

```html
<!-- portfolio-task-source: Young-Consultations/portfolio-tasks#<source-issue-number> -->
```

The workflow does not rely only on the issue title, so reruns update the same target issue instead of creating duplicates.

### Trigger behavior

The workflow runs for portfolio issue `opened`, `edited`, `labeled`, `unlabeled`, `reopened`, and `closed` events, plus manual `workflow_dispatch` runs. Event-triggered runs synchronize only issues that currently have `chatgpt-task`, except that removing `chatgpt-task` updates the existing target metadata to show synchronization is disabled.

Closing an eligible portfolio issue updates and closes the corresponding Slugger issue. Reopening an eligible portfolio issue updates and reopens the corresponding Slugger issue. Removing `chatgpt-task` never deletes or automatically closes the Slugger issue.

### Labels and assignees

The workflow always manages the `portfolio-task` target label. Optional source labels, including `chatgpt-task`, are not copied for the MVP; missing optional labels are skipped and reported in the job summary. Existing manual labels on the Slugger issue are preserved. When synchronization is disabled by removing `chatgpt-task`, the workflow removes only the automation-managed `portfolio-task` label from the desired target label set.

Source assignees are included in create or update payloads. If GitHub rejects an assignee because the user cannot be assigned in `Young-Consultations/slugger`, the workflow reports the failure without printing credentials.

### Dry-run mode

Manual runs default to `dry_run=true`. A dry run reads the source issue, validates `is:issue label:chatgpt-task`, searches Slugger for the metadata marker, determines the planned action (`create`, `update`, `close`, `reopen`, `disable-sync`, `no-op`, or `skipped`), writes a safe job summary, and performs no writes.

To perform a manual dry run:

1. Open Actions → **Sync Portfolio Tasks to Slugger Issues** in `Young-Consultations/portfolio-tasks`.
2. Select **Run workflow** on the target branch.
3. Enter an existing portfolio issue number in `source_issue_number`.
4. Leave `dry_run` set to `true`.
5. Review the job summary for the matching Slugger issue and planned action.
6. Confirm no Slugger issue was created or modified.

To perform a live test:

1. Create or choose a non-pull-request issue in `Young-Consultations/portfolio-tasks`.
2. Add the `chatgpt-task` label.
3. Run the workflow manually with that issue number and `dry_run=false`, or allow the label event to run it automatically.
4. Confirm exactly one issue exists in `Young-Consultations/slugger` with the `[PORTFOLIO-TASK #<source-issue-number>]` title prefix.
5. Confirm the Slugger issue body contains the `Young-Consultations/portfolio-tasks` idempotency marker.
6. Rerun the workflow and confirm it updates the same Slugger issue instead of creating a duplicate.

### Secret configuration and token permissions

Cross-repository access uses only the `SLUGGER_ISSUES_TOKEN` repository secret, exposed as `GH_TOKEN` to the workflow. The default `GITHUB_TOKEN` is not assumed to have write access to Slugger.

Use a fine-grained personal access token or GitHub App installation token limited to these repositories and permissions:

- `Young-Consultations/portfolio-tasks`: Metadata read, Issues read.
- `Young-Consultations/slugger`: Metadata read, Issues read and write.

The token should not have broader organization or repository access than those two repositories, and workflow logs must be reviewed without copying or printing the token value. Do not create, rotate, or modify secrets as part of ordinary dry-run validation; only confirm that the `SLUGGER_ISSUES_TOKEN` secret exists when live synchronization is expected.

### Manual GitHub setup

1. Create the `chatgpt-task` label in `Young-Consultations/portfolio-tasks`.
2. Create the `portfolio-task` label in `Young-Consultations/slugger`; if it is missing, label application may be skipped or reported by GitHub.
3. Create a fine-grained personal access token or GitHub App token.
4. Limit token repository access to `Young-Consultations/portfolio-tasks` and `Young-Consultations/slugger`.
5. Grant Portfolio Tasks metadata read, Portfolio Tasks issues read, Slugger metadata read, and Slugger issues read/write.
6. In `portfolio-tasks`, open Settings → Secrets and variables → Actions.
7. Add the secret named `SLUGGER_ISSUES_TOKEN`.
8. Run the workflow manually with one existing issue number and `dry_run=true`.
9. Review the job summary.
10. Add `chatgpt-task` to one test issue.
11. Confirm exactly one corresponding Slugger issue is created.

### Troubleshooting

- If manual dispatch fails, confirm `source_issue_number` is numeric and references an issue, not a pull request.
- If writes fail, confirm `SLUGGER_ISSUES_TOKEN` exists and has Slugger Issues read/write permission.
- If a target issue is not found, confirm its body contains the metadata marker exactly.
- If labels are skipped, create the `portfolio-task` label in Slugger and rerun.
- If an assignee is skipped or rejected, confirm the user has permission to be assigned in Slugger.

### Known limitations

- The MVP skips optional source labels instead of creating missing Slugger labels.
- The target issue search reads the first page of open and closed Slugger issues from the REST issues endpoint; repositories with more than 100 synchronized issues may need pagination enhancement.
- The workflow preserves comments and unrelated labels but does not synchronize comments.
