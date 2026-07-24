#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SCRIPT="$ROOT/scripts/validate-portfolio-dispatch.sh"
pass=0; fail=0
TMPROOT=$(mktemp -d); trap 'rm -rf "$TMPROOT"' EXIT
valid_labels='["chatgpt-task","project:slugger","priority:P1"]'

body(){ cat <<'BODY'
### Project
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
Ship one reviewable backlog task.

### Required behavior
Validate dispatch gates.

### Acceptance criteria
Validation passes.

### Testing requirements
Run contract tests.

### Security and safety constraints
Do not expose secrets.
BODY
}
issue(){ jq -n --arg body "$1" --argjson labels "$2" '{number:1,title:"T",body:$body,labels:($labels|map({name:.}))}'; }
run_json(){ local name="$1" expected="$2" json="$3"; local f="$TMPROOT/$name.json"; echo "$json" > "$f"; set +e; "$SCRIPT" "$f" >"$TMPROOT/$name.out" 2>"$TMPROOT/$name.err"; rc=$?; set -e; if [[ "$expected" == pass ]]; then [[ $rc -eq 0 ]]; else [[ $rc -ne 0 ]] && grep -q "$expected" "$TMPROOT/$name.out"; fi; }
case_ok(){ local n="$1"; shift; if "$@"; then echo "ok - $n"; pass=$((pass+1)); else echo "not ok - $n"; cat "$TMPROOT"/*.out "$TMPROOT"/*.err 2>/dev/null || true; fail=$((fail+1)); fi }

case_ok "valid approved codex task passes" run_json valid pass "$(issue "$(body)" "$valid_labels")"
b=$(body | sed "/### Risk/,+2d")
case_ok "missing field fails actionably" run_json missing "Missing required metadata field: Risk" "$(issue "$b" "$valid_labels")"
b=$(body | sed "s/approved/proposed/")
case_ok "unapproved task is rejected" run_json unapproved "Codex dispatch requires Execution status to be approved" "$(issue "$b" "$valid_labels")"
b=$(body | sed "s/codex/human/")
case_ok "human executor remains backlog only" run_json human "Codex dispatch requires Executor to be codex" "$(issue "$b" "$valid_labels")"
b=$(body | sed "s/none/#99/"); f=$TMPROOT/open.txt; echo "#1" > "$f"; j=$TMPROOT/dep.json; issue "$b" "$valid_labels" > "$j"
case_ok "dependency-blocked task is rejected" bash -c 'set +e; "$0" "$1" --mock-open-issues "$2" > "$3"; rc=$?; set -e; [[ $rc -ne 0 ]] && grep -q "Dependency reference is unresolved or closed: #99" "$3"' "$SCRIPT" "$j" "$f" "$TMPROOT/dep.out"
b=$(body | sed "s#Young-Consultations/slugger#not a repo#")
case_ok "malformed target repository is rejected" run_json repo "Target repository must use owner/repository format" "$(issue "$b" "$valid_labels")"

echo "$pass passed, $fail failed"
[[ $fail -eq 0 ]]
