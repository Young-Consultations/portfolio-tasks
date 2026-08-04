# portfolio-tasks

This repository owns portfolio-level planning issues and can hand qualifying work to the Slugger implementation backlog.

## Shared AI-SDLC execution contract

This repository is an execution target, not a contract owner. The organization router produces
the sole canonical input, `execution-input.json`; the target workflow installs the pinned
`ai_sdlc_contracts` distribution from `Young-Consultations/.github` and delegates input and result
validation to its CLI. No schemas, contract builders, version constants, or validators are copied
into this repository.

`.github/workflows/codex-execute.yml` applies only target policy after shared validation: the
repository must be `Young-Consultations/portfolio-tasks`, the executor must be Codex, the source
must be an open approved non-sensitive issue in this repository, and publication must remain a
draft PR. `execution_mode: verify` validates the contract, routing authorization, repository, and
tests without running Codex or creating a branch or PR. `execution_mode: implement` continues
through Codex and controlled draft-PR publication. Both modes emit a shared-contract-validated
`execution-result.json` artifact.

Implementation changes are committed and safely pushed before the workflow reports validation
failure. Publication creates or updates one deterministic **draft** pull request, records the
trusted command classifications in its body, and applies either `codex:validation-passed` or
`codex:validation-failed`; it never marks the pull request ready or merges it. A failure still
fails the Actions run after preservation. The only automatic repair is one `ruff format` pass over
changed Python files when formatting is the sole failure, followed by the complete validation
suite. Executor publication preflight checks the deterministic publication identity before Codex
runs: replays reuse an existing open draft pull request without rerunning Codex, while an existing
branch without a pull request and any closed or merged pull request for that identity fail closed
for explicit manual intervention.

`portfolio_tasks.execution` is deliberately a small policy adapter. It invokes
`python -m ai_sdlc_contracts` for schema validation and exposes only validated workflow outputs;
it does not load or interpret shared schemas itself.

### Shared router release

The approval workflow consumes the organization router at the immutable
`ai-sdlc-v2.1.0` release tag. Upgrading that pin requires a separate, reviewed consumer pull
request. If a rollback is necessary, pin the tag named by the release manifest's
`previous_known_good` value; published release tags must never be moved or replaced. See the
[authoritative AI-SDLC release documentation](https://github.com/Young-Consultations/.github/pull/17)
for the organization release policy and manifest.

## Python architecture and developer workflow

Synchronization and Codex process-boundary rules are implemented in the Python 3.12+
`portfolio_tasks` package. Canonical executable-task parsing is the explicit shell exception
described above; workflows otherwise contain orchestration and environment wiring.

The package is divided by responsibility:

- `models.py` contains immutable typed issue models and synchronization actions.
- `github_api.py` provides the reusable, token-safe GitHub REST boundary.
- `issue_parser.py` and `validation.py` retain non-executable intake compatibility checks; they
  are not used by dispatch, routing, or Codex execution.
- `issue_sync.py` separates mirror location, action planning, and write execution.
- `cli.py` exposes the `sync` and `validate-dispatch` automation commands.
- `run_codex.py` is the secure, version-adaptive Codex subprocess boundary.

Create a development environment and run all checks with:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
ruff check .
mypy portfolio_tasks
git diff --check
```

To preview issue synchronization, provide the same environment variables as Actions—at minimum
`SOURCE_ISSUE_NUMBER`, `GH_TOKEN`, and `DRY_RUN=true`—then run
`python -m portfolio_tasks.cli sync`. `GH_MOCK_DIR` selects deterministic JSON
fixtures instead of the network for regression testing.

When troubleshooting, inspect the JSON validation result or the synchronization
job summary first. API errors deliberately omit response bodies and credentials;
confirm token presence and least-privilege repository access separately. Run the
parser and planner unit tests before debugging Actions because they exercise the
same production code without network or workflow interpolation.

## Codex CLI compatibility wrapper

GitHub Actions invokes `python -m portfolio_tasks.run_codex` instead of calling `codex exec`
directly. This boundary prevents workflow definitions from depending on one
Codex CLI release: the wrapper verifies the executable, reports its version,
inspects `codex exec --help`, and supplies only the sandbox, approval, and Git
repository options that the installed version advertises. The prompt is read
byte-for-byte from standard input and forwarded to a `shell=False` subprocess;
Codex output streams while its exit status reaches the workflow unchanged.

`CODEX_API_KEY` is required and is translated to the CLI's `OPENAI_API_KEY`
only in the child environment. `CODEX_MODEL` is optional: when set, it becomes
the `--model` override, and when absent the installed CLI chooses its default.
The execution timeout defaults to 2,400 seconds and may be changed with
`CODEX_TIMEOUT_SECONDS` or `--timeout`.

The wrapper never logs environment variables or credentials. It redacts API
keys, authorization and bearer values, credential-bearing URLs, and session
identifiers from streamed diagnostics and from the diagnostic files retained
in `RUNNER_TEMP` for the workflow to upload. Failures receive concise GitHub
annotations classified as authentication, authorization, unavailable or
deprecated model, rate limit, network, TLS, DNS, timeout, Codex internal
exception, or unknown failure. The mandatory `workspace-write` sandbox fails
closed when unsupported; optional approval and Git-repository flags are used
only when capability discovery reports them.

The wrapper contains no repository names, paths, issue metadata, or other
repository-specific configuration. To reuse this AI-SDLC execution boundary in
`slugger`, `consulting-playbook`, `.github`, or another repository, copy the
script and call it from the repository checkout:

```bash
python -m portfolio_tasks.run_codex < "$RUNNER_TEMP/instructions.md"
```

Keep prompt construction, CLI installation/version pinning, credentials, and
repository policy in the consuming workflow. Future optional Codex flags should
be added only after detecting their exact names in `codex exec --help`, with a
contract-test fixture for both supported and unsupported CLI output.

## Slugger issue synchronization

The workflow `.github/workflows/sync-slugger-issues.yml` synchronizes qualifying issues from `Young-Consultations/portfolio-tasks` to `Young-Consultations/slugger`.

### Eligibility

A source item qualifies only when it is a GitHub issue, not a pull request, currently has the `chatgpt-task` label, and its structured **Target repository** field has the exact value `Young-Consultations/slugger`. The equivalent GitHub search expression for the issue and label portion is:

```text
is:issue label:chatgpt-task
```

`is:issue` is a GitHub search qualifier, not a label to create.

Issues that omit **Target repository**, contain a malformed value, or name any other repository (including `Young-Consultations/.github`, `Young-Consultations/portfolio-tasks`, `Young-Consultations/consulting-playbook`, sandbox repositories, or unknown targets) never create new Slugger mirrors. For these non-Slugger targets, the workflow still checks for an existing marker-matched legacy Slugger mirror and, when found, disables synchronization metadata and closes that mirror to retire duplicate state safely. When no mirror exists, the job summary reports `skipped-target-repository`.

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

Manual runs default to `dry_run=true`. A dry run reads the source issue, checks the structured target and `is:issue label:chatgpt-task` eligibility, searches Slugger for the metadata marker to either synchronize eligible Slugger-targeted work or retire any existing mismatched mirror, determines the planned action (`create`, `update`, `close`, `reopen`, `disable-sync`, `no-op`, `skipped`, or `skipped-target-repository`), writes a safe job summary, and performs no writes.

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

## ChatGPT task intake contract

The issue form `.github/ISSUE_TEMPLATE/chatgpt-task.yml` is the structured intake contract for tasks authored by ChatGPT or by humans using ChatGPT-generated requirements. It captures enough context for deterministic triage, optional synchronization to Slugger, and later human approval before any implementation agent runs.

The form is an intake artifact only. Submitting it does not authorize execution, does not grant Codex access to any repository, and does not replace repository-owner approval. Codex execution remains controlled by a separate approval gate: the issue metadata must state `Executor: codex` and `Execution status: approved` after maintainer review.

### Verification success

Documentation verification for this task completed successfully. The repository was updated by editing `README.md` only, and validation checks passed for the submitted change.

### How ChatGPT should populate the issue

When ChatGPT prepares a portfolio task, it should:

1. Use the **ChatGPT Automation Task** issue form.
2. Write the target repository exactly as `owner/repository`.
3. Select one primary task type from the dropdown.
4. Prefer concise, testable bullets for requirements and acceptance criteria.
5. Separate files that are in scope from files that are explicitly out of scope.
6. Include validation commands that a reviewer or implementation agent should run.
7. State security and architectural constraints even when the task seems low risk.
8. Redact sensitive information and replace private details with neutral descriptions.
9. Avoid implying that the request is approved for Codex execution; new intake should normally start with `Execution status: proposed`.

### Label meaning and approval flow

- `chatgpt-task` marks an issue as a structured ChatGPT task intake record. In this repository, that label also makes the issue eligible for the existing Slugger synchronization workflow when the workflow conditions are met.
- `executor:codex` plus `status:approved` is the canonical manual approval signal for Codex dispatch. The ChatGPT task form must not apply legacy `codex-ready` automatically, and maintainers should approve only after reviewing authorization, scope, safety, dependencies, and readiness for execution.
- Routing is exactly-once at the source gate: only the `issues.labeled` event for `status:approved` is eligible to dispatch. Other label events do not dispatch, and issue edits invalidate approval without dispatching.
- After the router accepts a task, execution labels `status:queued`, `status:running`, `status:draft-pr`, and `status:done` are treated as terminal dispatch markers and block rerouting of duplicate deliveries.

### Required field descriptions

The form requires these fields because downstream automation and reviewers need stable, machine-friendly sections:

- **Objective**: the business or engineering outcome to achieve.
- **Project, priority, executor, execution status, parallel safety, dependencies, risk, and estimated scope**: portfolio governance metadata used for deterministic triage and dispatch validation.
- **Target repository**: the intended repository in `owner/repository` format; this is a routing hint, not execution authorization.
- **Task type**: the primary category, selected from a deterministic dropdown.
- **Required behavior**: the desired end state or behavior that must be implemented or verified.
- **Acceptance criteria**: measurable completion checks for reviewers and implementation agents.
- **Testing requirements**: required automated checks, static validations, and manual verification steps.
- **Security and safety constraints**: boundaries for data handling, credentials, permissions, unsafe actions, and other safety-sensitive requirements.

Optional fields capture current behavior, project/component, functional requirements, in-scope and out-of-scope files, architectural constraints, prerequisites, and additional context.

### Example completed issue

```markdown
Title: [ChatGPT Task]: Add repository governance validation for issue templates

Objective
Add a lightweight validation check that protects the structured ChatGPT task issue form from accidental breaking changes.

Target repository
Young-Consultations/portfolio-tasks

Project or component name
Repository governance

Task type
Repository governance

Current behavior or problem
The repository has automation for Slugger synchronization, but the structured task intake form needs a guardrail so required fields and labels are not removed accidentally.

Required behavior
A repository validation script should confirm the ChatGPT task issue form exists, keeps required field IDs, applies `chatgpt-task`, does not apply `codex-ready`, and contains no example credentials.

Functional requirements
- Validate the issue form YAML syntax.
- Check stable required field IDs.
- Fail when `codex-ready` is configured by the form.
- Fail when obvious token, private key, or credential examples appear in the template.

Acceptance criteria
- The validation script exits successfully for the current form.
- Removing a required field ID causes the validation script to fail.
- Adding `codex-ready` to form labels causes the validation script to fail.

Files or components in scope
- .github/ISSUE_TEMPLATE/chatgpt-task.yml
- tests/validate-chatgpt-task-form.sh
- README.md

Files or components out of scope
- Slugger synchronization write behavior
- Repository secrets
- Codex execution workflows

Testing requirements
- Run `git diff --check`.
- Run the issue-form validation script.
- Run existing repository governance or template tests.

Security and safety constraints
Do not include credentials, API keys, private keys, client secrets, passwords, tokens, export-controlled information, or private customer data. Do not trigger Codex or grant repository access.

Architectural constraints
Keep GitHub Issues as the source of truth for task intake. Do not introduce a second repository or a parser for issue bodies.

Dependencies or prerequisites
The `chatgpt-task` label must exist in this repository for GitHub to apply it automatically.

Additional context
This issue is an intake contract only and requires separate maintainer approval before implementation automation can run.
```

### Data sensitivity and prohibited content

Do not place sensitive data in task issues, issue templates, examples, logs, screenshots, or validation fixtures. Prohibited content includes:

- Credentials, passwords, tokens, API keys, private keys, and client secrets.
- Unredacted production configuration or privileged repository settings.
- Personal data that is not necessary to understand the task.
- Client confidential material that is not approved for issue tracking.
- Export-controlled information or instructions that would require special handling.
- Exploit instructions, destructive commands, or secret-recovery steps that are not necessary for safe defensive work.

If sensitive context is required, reference the approved secure system where authorized reviewers can access it. The GitHub issue should contain only a redacted summary.

### Execution authorization boundary

Creating a ChatGPT task issue records a request. It does not mean the requested repository is authorized for Codex execution, does not prove the requester has permission to change the target repository, and does not permit automation to run. A maintainer must separately review the request, confirm repository authorization and safety constraints, and apply any required approval labels or repository settings before execution can occur.

### Issue-form validation

Run the lightweight validation script before changing the task contract:

```bash
tests/validate-chatgpt-task-form.sh
```

The check confirms that the form exists, required machine-friendly field IDs and governance dropdown options remain stable, `chatgpt-task` remains configured, `codex-ready` is not configured, and obvious secrets or example credentials are not present in the template.

## Portfolio backlog governance contract

`portfolio-tasks` is the authoritative backlog for Slugger, consulting, and future repositories. Each issue should represent one independently reviewable issue or feature. Large efforts should be split before Codex dispatch so each issue has its own approval, dependency, risk, scope, and acceptance criteria.

The GitHub Projects Phase 1 portfolio dashboard contract is defined in
`docs/github-projects-phase1-contract.md`. It documents the responsibility
split between issues, Projects, router workflows, and target repositories,
the deterministic field mapping, four required views, reproducible
organization-owner setup, and required identifiers, variables, and secrets.

Optional GitHub Projects Phase 2 synchronization is defined in
`docs/github-projects-sync.md`. Phase 2 mirrors the canonical issue
metadata into organization project fields only when explicitly enabled and
correctly configured with least-privilege credentials. It is disabled by
default and fails closed when prerequisite or configuration gates are missing.

### Canonical metadata fields

The `ChatGPT Automation Task` issue form captures these required governance fields before the detailed requirements sections:

| Field | Allowed values or format | Label mapping |
| --- | --- | --- |
| Project | Stable lowercase portfolio key such as `slugger`, `consulting`, or `portfolio-backlog-schema` | `project:<value>` |
| Priority | `P0`, `P1`, `P2`, `P3` | `priority:<value>` |
| Executor | `codex`, `human`, `chatgpt-planning` | `executor:<value>` |
| Execution status | `proposed`, `approved`, `queued`, `running`, `draft-pr`, `blocked`, `done` | `status:<value>` |
| Target repository | `owner/repository` | none; validated as routing metadata |
| Parallel-safe | `yes`, `no` | `parallel-safe:<value>` |
| Dependency issue references | `none`, `#123`, or `owner/repository#123` | none; validated before dispatch |
| Risk | `low`, `medium`, `high` | `risk:<value>` |
| Estimated scope | `small`, `medium`, `large` | `scope:<value>` |
| Task type | Form dropdown values such as `Feature`, `Security`, or `Repository governance` | `type:<normalized-value>` |

The form still preserves detailed fields for objective, current behavior, required behavior, functional requirements, acceptance criteria, in-scope and out-of-scope files, testing requirements, security constraints, architectural constraints, dependencies or prerequisites, and additional context.

### Lifecycle and approval gate

1. **Proposed**: ChatGPT or a human opens an issue with `execution status: proposed`. This is intake only.
2. **Triage**: Maintainers review target repository, scope, risk, dependencies, and parallel safety. Human-only and planning-only issues stay visible in the backlog with `executor: human` or `executor: chatgpt-planning`.
3. **Approved**: A maintainer explicitly changes `executor` to `codex` and `execution status` to `approved` when Codex may execute the task.
4. **Queued/running**: External execution automation may claim the approved task. This repository validates the contract; target-repository execution implementation belongs outside this repository.
5. **Draft PR**: When an implementation agent opens a draft pull request, move the issue to `execution status: draft-pr` and link the PR.
6. **Blocked/done**: Use `blocked` when dependencies, approvals, or safety concerns prevent progress. Use `done` only after review and completion.

Only issues with `Executor` exactly `codex` and `Execution status` exactly `approved` can pass the dispatch contract. Creating or editing an issue never grants execution approval by itself.

### Validation and actionable failures

The workflow `.github/workflows/portfolio-dispatch-contract.yml` validates a selected issue before Codex dispatch. It rejects dispatch when required metadata is missing, the executor is not Codex, the status is not approved, the target repository is malformed, deterministic project or priority labels are missing, or dependency references are malformed or unresolved by the supplied validation context. On failure, the workflow posts an actionable issue comment that lists the fields to fix and does not include credentials or token values.

Local contract checks are available with:

```bash
tests/validate-chatgpt-task-form.sh
tests/portfolio-dispatch-contract.bats.sh
```

### Label taxonomy setup

Create and maintain these label families deterministically:

- `project:slugger`, `project:consulting`, `project:portfolio-backlog-schema`, and future `project:<key>` labels.
- `priority:P0`, `priority:P1`, `priority:P2`, `priority:P3`.
- `executor:codex`, `executor:human`, `executor:chatgpt-planning`.
- `status:proposed`, `status:approved`, `status:queued`, `status:running`, `status:draft-pr`, `status:blocked`, `status:done`.
- `type:bug-fix`, `type:feature`, `type:refactor`, `type:ci-cd`, `type:documentation`, `type:security`, `type:repository-governance`, `type:automation`, `type:investigation`.
- `parallel-safe:yes`, `parallel-safe:no`.
- Optional risk and scope labels: `risk:low`, `risk:medium`, `risk:high`, `scope:small`, `scope:medium`, `scope:large`.

### Compatibility and migration

Existing `chatgpt-task` issues remain valid backlog records, but they cannot pass Codex dispatch until the new required metadata is added. To migrate an older issue, edit the issue body to add the missing GitHub issue-form sections, apply deterministic `project:*` and `priority:*` labels, confirm dependencies are resolved, and set `Executor: codex` plus `Execution status: approved` only after human approval.

### Examples

Slugger implementation backlog example:

```markdown
Project: slugger
Priority: P1
Executor: codex
Execution status: approved
Target repository: Young-Consultations/slugger
Parallel-safe: no
Dependency issue references: #42
Risk: medium
Estimated scope: small
Task type: Feature
Objective: Add one independently reviewable scoring report enhancement.
```

Consulting planning example that must not dispatch:

```markdown
Project: consulting
Priority: P2
Executor: human
Execution status: proposed
Target repository: Young-Consultations/portfolio-tasks
Parallel-safe: yes
Dependency issue references: none
Risk: low
Estimated scope: small
Task type: Investigation
Objective: Draft a client-safe implementation plan without changing code.
```
