# Execution Contract

Implement only the approved task. Do not push, create a PR, or access secrets.

## Repository Context

{{repository_context}}

Use the repository context to understand existing conventions, boundaries, and architecture. Preserve the repository's current architecture and established patterns. Keep the change set minimal and scoped to the task: do not perform broad refactoring or unrelated cleanup.

## Task

{{task_instructions}}

Treat the task instructions above as the canonical task instructions. Before editing code:

1. Restate the objective in your own words.
2. Identify the root problem that must be solved. Solve the root problem rather than its symptoms.
3. Extract every acceptance criterion from the task, including explicitly stated requirements and constraints. Do not skip any acceptance criterion.
4. Map every acceptance criterion to one or more planned code or test changes.
5. Identify the files expected to change and explain why each is necessary.

## Implementation Requirements

- Execute the plan with the smallest coherent set of changes that solves the root problem.
- Preserve repository architecture, public behavior outside the task's scope, and existing conventions.
- Do not broaden the task into refactoring or cleanup that is not required by an acceptance criterion.
- Add or update tests for each behavior changed by the implementation.
- Revisit the plan if implementation reveals that a criterion is not covered; never silently skip it.

## Validation

Run the following validation commands in the listed order after implementation:

{{validation_commands}}

Report each command and its result. If a command cannot run or fails, explain why and do not claim successful validation.

## Final Acceptance-Criteria Review

Before completion, review every extracted acceptance criterion against the implemented changes and validation results. Confirm each criterion is satisfied, or identify it as unresolved with a specific reason. Do not declare the task complete while an acceptance criterion is skipped or implicitly assumed.

## Completion Report

Provide a concise implementation summary containing:

- **Objective:** the objective completed.
- **Files changed:** each changed file and its purpose.
- **Tests:** tests added or updated, plus validation commands and results.
- **Acceptance criteria satisfied:** an explicit criterion-by-criterion confirmation.
- **Unresolved items:** remaining issues or `None`.
