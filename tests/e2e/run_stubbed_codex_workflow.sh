#!/usr/bin/env bash
# Offline simulation of the significant local steps in codex-execute.yml.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
temporary=$(mktemp -d)
trap 'git -C "$temporary/repository" worktree remove --force "$temporary/worktree" 2>/dev/null || true; rm -rf "$temporary"' EXIT

repo="$temporary/repository"
worktree="$temporary/worktree"
mkdir -p "$repo" "$temporary/sentinel"
git -C "$repo" init -q -b main
git -C "$repo" config user.email tests@example.invalid
git -C "$repo" config user.name 'Offline Workflow Test'
printf 'trusted initial state\n' > "$repo/task.txt"
git -C "$repo" add task.txt
git -C "$repo" commit -qm 'trusted initial state'
git -C "$repo" worktree add -q -b codex/test "$worktree" HEAD

cat > "$temporary/execution-input.json" <<'JSON'
{"contract_version":"ai-sdlc-contract/v2","correlation_id":"offline-shell-e2e","source_issue":"Young-Consultations/portfolio-tasks#1","target_repository":"Young-Consultations/portfolio-tasks","executor":"codex","draft_pr_only":true,"execution_mode":"implement","requested_branch":"codex/test","instructions":"Change task.txt using the deterministic offline fixture."}
JSON
PYTHONPATH="$root" python - "$temporary" <<'PY'
import json, sys
from pathlib import Path
from portfolio_tasks.prompts import render_execution_prompt
directory = Path(sys.argv[1])
value = json.loads((directory / "execution-input.json").read_text())
(directory / "instructions.md").write_text(render_execution_prompt(
    task_instructions=value["instructions"], repository_context="", validation_commands=[]))
PY

cat > "$temporary/sentinel/codex" <<EOF
#!/bin/sh
touch "$temporary/REAL_CODEX_WAS_CALLED"
exit 99
EOF
chmod +x "$temporary/sentinel/codex" "$root/tests/fixtures/fake_codex.py"
env -u CODEX_API_KEY -u OPENAI_API_KEY \
  PATH="$temporary/sentinel:$PATH" PYTHONPATH="$root" RUNNER_TEMP="$temporary/runner" \
  FAKE_CODEX_SCENARIO=success_changed FAKE_CODEX_METADATA="$temporary/invocation.json" \
  python -m portfolio_tasks.run_codex --codex-executable "$root/tests/fixtures/fake_codex.py" \
  --working-directory "$worktree" < "$temporary/instructions.md"
test ! -e "$temporary/REAL_CODEX_WAS_CALLED"

outcome=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' \
  "$worktree/codex-result.json")
rm "$worktree/codex-result.json"
tree_changed=false
test -z "$(git -C "$worktree" status --porcelain=v1 --untracked-files=all)" || tree_changed=true
test "$outcome" = changed
test "$tree_changed" = true
no_changes=false
printf 'outcome=%s\nno_changes=%s\n' "$outcome" "$no_changes"
