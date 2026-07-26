from portfolio_tasks.validation import validate_dispatch

BODY = """### Project
slugger

### Priority
P1

### Executor
codex

### Execution status
approved

### Target repository
Young-Consultations/slugger

### Parallel-safe
yes

### Dependency issue references
none

### Risk
medium

### Estimated scope
small

### Objective
Ship it

### Required behavior
Validate

### Acceptance criteria
Pass

### Testing requirements
Test

### Security and safety constraints
No secrets
"""


def test_valid_dispatch() -> None:
    result = validate_dispatch({"body": BODY, "labels": [{"name": "project:slugger"}, {"name": "priority:P1"}]})
    assert result.ok


def test_malformed_and_unapproved_dispatch() -> None:
    result = validate_dispatch({"body": BODY.replace("approved", "proposed").replace("Young-Consultations/slugger", "bad repo"), "labels": []})
    assert not result.ok
    assert "Codex dispatch requires Execution status to be approved" in result.errors
