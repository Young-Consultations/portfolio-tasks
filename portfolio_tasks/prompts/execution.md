# Autonomous Execution Contract

This is a fully autonomous, noninteractive execution. Do not ask the user for permission, confirmation, clarification, or approval, and do not wait for another message. Perform planning internally; do not present a plan and pause. After planning, immediately edit the repository, add or update tests, run validation, and inspect the resulting diff. Do not end after restating the objective or describing intended changes.

Implement only the approved task. Do not push, create a PR, or access secrets.

## Repository Context

{{repository_context}}

Use the repository context to understand existing conventions, boundaries, and architecture. Preserve the repository's architecture and established patterns. Keep changes minimal and scoped to the task; do not perform broad refactoring or unrelated cleanup.

## Task

{{task_instructions}}

Treat these as the canonical instructions. Internally identify the root problem, extract every acceptance criterion and constraint, and map each criterion to implementation and test work. Planning is not a terminal outcome and must not be presented as a prerequisite to editing.

## Required Execution Sequence

Continue working without pausing until a defined terminal outcome is reached:

1. Inspect the repository.
2. Determine the current behavior.
3. Compare the current behavior to every acceptance criterion.
4. Implement all missing behavior.
5. Add or update tests.
6. Run validation.
7. Inspect `git status --porcelain=v1 --untracked-files=all` and the complete diff.
8. Write the structured result and produce the completion report.

Do not claim "implemented", "completed", or equivalent unless repository changes exist and validation has run. A textual claim is never evidence.

## Existing Implementation

If all requested behavior is already present, do not create artificial formatting, comment, or unrelated changes. Run the required targeted tests and validation, gather concrete criterion-by-criterion evidence, and return the structured `already_satisfied` result. A clean tree without that validated evidence is an unexplained no-change failure.

## Validation

Run the following validation commands in the listed order after implementation:

{{validation_commands}}

Also run the targeted tests needed to prove each criterion. Report every command and its result. A command that fails or is unavailable cannot support a successful outcome.

## Structured Result

Before the completion report, write `$RUNNER_TEMP/codex-result.json` as valid JSON:

```json
{
  "status": "changed | already_satisfied | failed",
  "objective": "objective addressed",
  "files_changed": ["relative/path"],
  "acceptance_criteria": [
    {"criterion": "criterion text", "status": "satisfied | unresolved", "evidence": "file, diff, test, or command evidence"}
  ],
  "validation": [
    {"command": "exact command", "status": "passed | failed | unavailable"}
  ],
  "unresolved_items": []
}
```

Use `changed` only when the repository has real task changes. Use `already_satisfied` only when the tree is clean, every criterion has concrete evidence, and all required validation passed. Use `failed` when work or validation remains unresolved. Continue until exactly one of these terminal outcomes is accurate.

## Completion Report

After inspecting status and diff, concisely report the objective, files changed, tests and validation, criterion-by-criterion evidence, terminal status, and unresolved items. The report must agree with the structured result and repository state.
