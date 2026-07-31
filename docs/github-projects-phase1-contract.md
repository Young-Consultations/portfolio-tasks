# GitHub Projects Phase 1 portfolio contract

This contract defines the manual Phase 1 operating model for the organization
portfolio backlog in GitHub Projects. Phase 1 is intentionally usable without
synchronization or mutation automation: maintainers can triage, approve, route,
and track work using issue metadata plus manual project updates.

## Responsibility split

| System | Primary responsibility | Not responsible for |
| --- | --- | --- |
| Issues in `Young-Consultations/portfolio-tasks` | Canonical task contract (objective, requirements, acceptance criteria) and canonical governance metadata (project, priority, executor, status, repository, dependencies, risk, scope, type). | Automatic execution authorization or automatic project synchronization. |
| GitHub Projects (organization project) | Portfolio dashboard and manual planning views across issues. Stores manually mirrored fields for deterministic filtering and prioritization. | Dispatch authorization, workflow routing decisions, or source-of-truth governance values. |
| Router and dispatch workflows (`route-approved-task.yml`, `codex-execute.yml`) | Enforce execution gate and shared-contract validation before trusted Codex execution. Read issue metadata and labels as the execution source of truth. | Portfolio dashboard ownership, manual triage decisions, or project view curation. |
| Target repositories (for example `Young-Consultations/slugger`) | Implement approved work and receive synchronized or routed execution outcomes. | Intake governance ownership for portfolio backlog metadata. |

If project fields and issue metadata diverge, the issue form body and
deterministic labels in `Young-Consultations/portfolio-tasks` are authoritative.
Project values must be corrected manually to match the issue contract.

## Deterministic field mapping

Use the exact field names below in the organization project. Values must map
directly to the issue form contract and label taxonomy in `README.md`.

| Issue form field (source of truth) | Allowed values / format | Project field name | Label or routing mapping |
| --- | --- | --- | --- |
| `Project` | Existing keys: `slugger`, `consulting`, `portfolio-backlog-schema`; future lowercase portfolio keys allowed | `Project` (single select) | `project:<value>` |
| `Priority` | `P0`, `P1`, `P2`, `P3` | `Priority` (single select) | `priority:<value>` |
| `Executor` | `codex`, `human`, `chatgpt-planning` | `Executor` (single select) | `executor:<value>` |
| `Execution status` | `proposed`, `approved`, `queued`, `running`, `draft-pr`, `blocked`, `done` | `Execution status` (single select) | `status:<value>` |
| `Target repository` | `owner/repository` | `Target repository` (text) | Routing metadata only |
| `Parallel-safe` | `yes`, `no` | `Parallel-safe` (single select) | `parallel-safe:<value>` |
| `Dependency issue references` | `none`, `#123`, `owner/repository#123`, or space/comma-separated list of those references | `Dependency issue references` (text) | Dispatch prerequisite metadata |
| `Risk` | `low`, `medium`, `high` | `Risk` (single select) | `risk:<value>` |
| `Estimated scope` | `small`, `medium`, `large` | `Estimated scope` (single select) | `scope:<value>` |
| `Task type` | `Bug fix`, `Feature`, `Refactor`, `CI/CD`, `Documentation`, `Security`, `Repository governance`, `Automation`, `Investigation` | `Task type` (single select) | `type:<normalized-value>` |

## Required Phase 1 views

Create these four views exactly. They are sufficient to operate Phase 1 without
automation.

| View name | Filters | Grouping | Sorting | Intended use |
| --- | --- | --- | --- | --- |
| `01 Intake and triage` | `is:open`, `label:chatgpt-task`, `Execution status = proposed` | Group by `Project` | Sort by `Priority` (high to low), then `Updated` (oldest first) | Review newly submitted intake tasks, confirm metadata completeness, and prepare approval decisions. |
| `02 Ready for router dispatch` | `is:open`, `label:chatgpt-task`, `Executor = codex`, `Execution status = approved` | Group by `Priority` | Sort by `Updated` (oldest first) | Maintain the approved Codex queue before routing. |
| `03 Execution in progress` | `is:open`, `label:chatgpt-task`, `Executor = codex`, `Execution status in {queued, running, draft-pr, blocked}` | Group by `Execution status` | Sort by `Updated` (newest first) | Track actively routed work and blocked items through implementation review. |
| `04 Done and archive` | `label:chatgpt-task`, `Execution status = done` or `is:closed` | Group by `Project` | Sort by `Updated` (newest first) | Review completions, closed outcomes, and historical throughput. |

## Manual organization-owner setup

1. Open `https://github.com/orgs/Young-Consultations/projects` as an organization owner.
2. Create a new organization project named `Portfolio Tasks - Phase 1`.
3. Add repository access for `Young-Consultations/portfolio-tasks`.
4. Add all custom project fields from the deterministic field mapping table with the exact names and options.
5. Keep issue metadata authoritative: when triaging, copy issue-form values into project fields exactly.
6. Create the four required views with the exact filters, grouping, and sorting specified above.
7. Add at least one known `chatgpt-task` issue to the project and confirm it appears in `01 Intake and triage` or the expected status view.
8. Manually update one issue from `proposed` to `approved`, then verify it moves to `02 Ready for router dispatch` after project fields are mirrored.
9. Confirm no project workflow automation is required for those transitions; the board remains usable with manual updates only.

## Phase 1 operating notes (no synchronization automation)

- Do not depend on project automation, webhooks, API mutation scripts, or bidirectional sync for Phase 1.
- Route eligibility remains enforced by issue metadata and labels, not by project-card position.
- A maintainer can run the complete lifecycle manually by editing issue fields/labels and mirroring those values into project fields.

## Required identifiers, variables, and secrets

Document and verify these identifiers and workflow inputs; do not create, rotate,
or change them as part of this contract definition task.

| Type | Name | Required by | Notes |
| --- | --- | --- | --- |
| Organization identifier | `Young-Consultations` | Phase 1 project ownership | Organization that hosts the portfolio project. |
| Source backlog repository | `Young-Consultations/portfolio-tasks` | Intake, routing, and execution gate | Canonical source of issue metadata. |
| Initial target repository | `Young-Consultations/slugger` | Current synchronization scope | First implementation repository synchronized from the portfolio backlog. |
| Organization project identifier | `Portfolio Tasks - Phase 1` (record resulting project number and URL after creation) | Manual dashboard operations | Project number and URL are environment-specific and must be captured by maintainers after setup. |
| Repository variable | `AI_SDLC_CONTRACTS_COMMIT_SHA` | `route-approved-task.yml`, `codex-execute.yml` | Pins shared contract package source commit. |
| Repository variable | `CODEX_MODEL` | `codex-execute.yml` | Optional model override; workflow defaults when unset. |
| Repository secret | `SLUGGER_GITHUB_TOKEN` | `route-approved-task.yml`, `codex-execute.yml` | Token used for routing, issue label updates, and trusted execution workflow API access. |
| Repository secret | `OPENAI_API_KEY` | `codex-execute.yml` | Passed to Codex execution wrapper as the API credential. |
| Repository secret | `SLUGGER_ISSUES_TOKEN` | `sync-slugger-issues.yml` | Token used only for Slugger issue synchronization workflow. |
