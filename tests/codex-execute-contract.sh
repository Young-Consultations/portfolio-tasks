#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WORKFLOW="$ROOT/.github/workflows/codex-execute.yml"
pass=0

issue_validator=$(awk '
  /^          state=\$\(jq / { capture=1 }
  /^          labels=\$\(jq / { capture=0 }
  capture { sub(/^          /, ""); print }
' "$WORKFLOW")

validate_issue() {
  local fixture=$1 temp
  temp=$(mktemp -d)
  if [[ -n "$fixture" ]]; then
    printf '%s\n' "$fixture" > "$temp/source-issue.json"
  fi
  RUNNER_TEMP=$temp REPOSITORY=Young-Consultations/portfolio-tasks \
    bash -c "set -euo pipefail
$issue_validator" >/dev/null 2>&1
  local result=$?
  rm -rf "$temp"
  return "$result"
}

accepts_issue() {
  local description=$1 fixture=$2
  if validate_issue "$fixture"; then
    printf 'ok - %s\n' "$description"
    pass=$((pass + 1))
  else
    printf 'not ok - %s\n' "$description" >&2
    return 1
  fi
}

rejects_issue() {
  local description=$1 fixture=$2
  if validate_issue "$fixture"; then
    printf 'not ok - %s\n' "$description" >&2
    return 1
  fi
  printf 'ok - %s\n' "$description"
  pass=$((pass + 1))
}

parser=$(awk '
  /^          if \[\[ "\$SOURCE_ISSUE" =~/ { capture=1 }
  capture { end=($0 == "          fi"); sub(/^          /, ""); print; if (end) exit }
' "$WORKFLOW")

parse_source_issue() {
  SOURCE_ISSUE=$1 bash -c "set -euo pipefail
$parser
printf '%s\\n' \"\$issue_number\""
}

accepts_source_issue() {
  local value=$1 expected=$2 actual
  if actual=$(parse_source_issue "$value" 2>/dev/null) && [[ "$actual" == "$expected" ]]; then
    printf 'ok - source_issue accepts %s\n' "$value"
    pass=$((pass + 1))
  else
    printf 'not ok - source_issue should accept %s\n' "$value" >&2
    return 1
  fi
}

rejects_source_issue() {
  local description=$1 value=$2
  if parse_source_issue "$value" >/dev/null 2>&1; then
    printf 'not ok - source_issue accepts %s\n' "$description" >&2
    return 1
  fi
  printf 'ok - source_issue rejects %s\n' "$description"
  pass=$((pass + 1))
}

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
check 'dependencies gate execution' "none\|satisfied\|waived"
check 'target is pinned to this repository' "Young-Consultations/portfolio-tasks"
check 'cross-repository targets are rejected' "Cross-repository execution is forbidden"
check 'tracked and untracked changes are detected' "status --porcelain=v1 --untracked-files=all"
check 'test success is recorded only after commands' "result=passed"
check 'publication is draft only' "draft:true"
check 'Codex execution uses compatibility wrapper' 'scripts/run-codex\.sh < "\$RUNNER_TEMP/instructions\.md"'
check 'checkout action is pinned to a full SHA' 'actions/checkout@[0-9a-f]{40}'
check 'Codex execution receives CODEX_API_KEY' 'CODEX_API_KEY: \$\{\{ secrets\.OPENAI_API_KEY \}\}'
check 'Responses preflight posts to the Responses API' 'https://api\.openai\.com/v1/responses'
check 'Responses preflight uses CODEX_API_KEY' 'Authorization: Bearer \$CODEX_API_KEY'
check 'Responses preflight does not emit the response body' '--output "\$preflight_response"'
if grep -Eq '(echo|printf)[^\n]*\$\{?CODEX_API_KEY' "$WORKFLOW"; then
  echo 'not ok - workflow prints CODEX_API_KEY' >&2
  exit 1
fi
echo 'ok - workflow never prints CODEX_API_KEY'
pass=$((pass + 1))

preflight=$(awk '
  /^          if \[\[ -z "\$\{CODEX_API_KEY:-\}" \]\]; then/ { capture=1 }
  capture { done=($0 == "          trap - EXIT"); sub(/^          /, ""); print; if (done) exit }
' "$WORKFLOW")

exercise_preflight() {
  local code=$1 body=$2 temp output status
  temp=$(mktemp -d)
  cat > "$temp/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
while (($#)); do
  if [[ "$1" == --output ]]; then output=$2; shift 2; else shift; fi
done
printf '%s' "$MOCK_RESPONSE_BODY" > "$output"
printf '%s' "$MOCK_RESPONSE_CODE"
EOF
  chmod +x "$temp/curl"
  set +e
  output=$(PATH="$temp:$PATH" RUNNER_TEMP="$temp" CODEX_API_KEY=test-key \
    CODEX_MODEL=gpt-5.1-codex MOCK_RESPONSE_CODE="$code" MOCK_RESPONSE_BODY="$body" \
    bash -c "set -euo pipefail; set +x; $preflight; echo codex-permitted" 2>&1)
  status=$?
  set -e
  rm -rf "$temp"
  printf '%s\n%s' "$status" "$output"
}

result=$(exercise_preflight 200 '{}')
[[ ${result%%$'\n'*} == 0 && "$result" == *codex-permitted* ]] || {
  echo 'not ok - a successful Responses preflight does not permit Codex execution' >&2; exit 1;
}
echo 'ok - a 200 Responses preflight permits Codex execution'
pass=$((pass + 1))

for code in 401 403 429; do
  secret_body="raw-sensitive-message-${code}"
  result=$(exercise_preflight "$code" "{\"error\":{\"type\":\"auth_error\",\"message\":\"$secret_body\"}}")
  [[ ${result%%$'\n'*} != 0 ]] || { echo "not ok - HTTP $code preflight succeeds" >&2; exit 1; }
  [[ "$result" == *"HTTP $code, type auth_error"* ]] || { echo "not ok - HTTP $code lacks sanitized diagnostic" >&2; exit 1; }
  [[ "$result" != *"$secret_body"* ]] || { echo "not ok - HTTP $code emits the raw API response" >&2; exit 1; }
  echo "ok - HTTP $code fails with a sanitized diagnostic"
  pass=$((pass + 1))
done

accepts_issue 'open issue passes validation' '{"number":13,"state":"open"}'
rejects_issue 'closed issue fails validation' '{"number":13,"state":"closed"}'
rejects_issue 'pull request fails validation' '{"number":13,"state":"open","pull_request":{}}'
rejects_issue 'missing issue fails validation' ''

accepts_source_issue '13' '13'
accepts_source_issue 'Young-Consultations/portfolio-tasks#13' '13'
accepts_source_issue 'https://github.com/Young-Consultations/portfolio-tasks/issues/13' '13'

rejects_source_issue 'another repository' 'Young-Consultations/slugger#13'
rejects_source_issue 'another organization' 'another-owner/portfolio-tasks#13'
rejects_source_issue 'a pull-request URL' 'https://github.com/Young-Consultations/portfolio-tasks/pull/13'
rejects_source_issue 'a missing issue number' 'Young-Consultations/portfolio-tasks#'
rejects_source_issue 'a nonnumeric issue number' 'Young-Consultations/portfolio-tasks#abc'
rejects_source_issue 'an issue number with a suffix' 'Young-Consultations/portfolio-tasks#13-extra'
rejects_source_issue 'leading whitespace' ' Young-Consultations/portfolio-tasks#13'
rejects_source_issue 'trailing whitespace' 'Young-Consultations/portfolio-tasks#13 '
rejects_source_issue 'a URL query string' 'https://github.com/Young-Consultations/portfolio-tasks/issues/13?source=router'
rejects_source_issue 'a URL fragment' 'https://github.com/Young-Consultations/portfolio-tasks/issues/13#issuecomment-1'

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
if grep -Eq '^[[:space:]]+codex exec([[:space:]]|$)' "$WORKFLOW"; then
  echo 'not ok - workflow must not invoke codex exec directly' >&2
  exit 1
fi
echo "ok - prohibited publication triggers are absent"
pass=$((pass + 1))

printf '%s contract checks passed\n' "$pass"
