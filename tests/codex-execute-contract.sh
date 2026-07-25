#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WORKFLOW="$ROOT/.github/workflows/codex-execute.yml"
pass=0

check() {
  local description=$1 pattern=$2
  if grep -Eq -- "$pattern" "$WORKFLOW"; then
    printf 'ok - %s\n' "$description"
    pass=$((pass + 1))
  else
    printf 'not ok - %s\n' "$description" >&2
    return 1
  fi
}

check 'authorization requires codex executor' "executor:codex"
check 'authorization requires approved status' "status:approved"
check 'sensitive issues are rejected' "Issues marked sensitive cannot be sent to Codex"
check 'closed issues are rejected' "\.state.*== open"
check 'dependencies gate execution' "none\|satisfied\|waived"
check 'target is pinned to this repository' "Young-Consultations/portfolio-tasks"
check 'cross-repository targets are rejected' "Cross-repository execution is forbidden"
check 'tracked and untracked changes are detected' "status --porcelain=v1 --untracked-files=all"
check 'test success is recorded only after commands' "result=passed"
check 'publication is draft only' "draft:true"
check 'Codex uses workspace-write sandbox' "--sandbox workspace-write"
check 'checkout action is pinned to a full SHA' 'actions/checkout@[0-9a-f]{40}'

job_env=$(awk '
  /^    env:$/ { in_job_env=1; next }
  in_job_env && /^    [^ ]/ { exit }
  in_job_env { print }
' "$WORKFLOW")
if grep -Fq 'GH_TOKEN:' <<< "$job_env"; then
  echo 'not ok - GitHub publication token must not be available at job scope' >&2
  exit 1
fi
echo 'ok - GitHub publication token is absent from job scope'
pass=$((pass + 1))

if grep -Eq 'uses: .+@(main|master|v[0-9]+)([[:space:]#]|$)' "$WORKFLOW"; then
  echo 'not ok - every action must be pinned to a full commit SHA' >&2
  exit 1
fi
if grep -Eq '(^|[[:space:]])pull_request_target:|gh pr merge|/merges(["/[:space:]]|$)' "$WORKFLOW"; then
  echo 'not ok - automatic merge and pull_request_target are forbidden' >&2
  exit 1
fi
echo "ok - prohibited publication triggers are absent"
pass=$((pass + 1))

printf '%s contract checks passed\n' "$pass"
