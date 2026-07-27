#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=scripts/task-contract-lib.sh
source "$root/scripts/task-contract-lib.sh"

usage() { echo "usage: $0 ISSUE.json OUTPUT.json" >&2; exit 2; }
[[ $# == 2 ]] || usage
issue=$1 output=$2
jq -e 'type == "object"' "$issue" >/dev/null || fail 'source issue is not JSON object'

[[ $(jq -r '.state // ""' "$issue") == open ]] || fail 'source issue is closed'
jq -e 'has("pull_request") | not' "$issue" >/dev/null || fail 'source is a pull request'
jq -e '[.labels[]? | if type == "object" then .name else . end] | index("sensitive") == null' "$issue" >/dev/null || fail 'source issue has sensitive label'

body_file=$(mktemp)
trap 'rm -f "$body_file" "$output.tmp"' EXIT
jq -r '.body // ""' "$issue" > "$body_file"

status=$(normalize_status "$(single_label_value 'status:' "$issue")")
executor=$(single_label_value 'executor:' "$issue")
priority=$(normalize_priority "$(single_label_value 'priority:' "$issue")")
project=$(single_label_value 'project:' "$issue")
[[ -n $executor ]] || fail 'executor is missing'
[[ $executor =~ ^(codex|human|chatgpt-planning)$ ]] || fail "unsupported executor: $executor"
[[ -n $project ]] || fail 'project is missing'

body_status=$(section_value 'Execution status' "$body_file")
if [[ -n $body_status ]]; then
  normalized_body_status=$(normalize_status "$body_status")
  [[ $normalized_body_status == "$status" ]] || fail "body/label status conflict: body=$body_status label=$status"
fi

target=$(section_value 'Target repository' "$body_file")
target=${target#- }; target=${target#\`}; target=${target%\`}
[[ $target =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail 'target repository is missing or malformed'
task_type=$(normalize_task_type "$(section_value 'Task type' "$body_file")")

raw_dependencies=$(section_value 'Dependency issue references' "$body_file")
dependencies=()
if [[ ${raw_dependencies,,} != none ]]; then
  [[ -n $raw_dependencies ]] || fail 'dependency references are missing'
  while IFS= read -r dependency; do
    [[ $dependency =~ ^(#[1-9][0-9]*|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*)$ ]] || fail "malformed dependency reference: $dependency"
    dependencies+=("$dependency")
  done < <(tr ',[:space:]' '\n' <<< "$raw_dependencies" | sed '/^$/d')
fi

parallel_safe=false
jq -e '[.labels[]? | if type == "object" then .name else . end] | index("parallel-safe") != null' "$issue" >/dev/null && parallel_safe=true
objective=$(section_value 'Objective' "$body_file")
required=$(section_value 'Required behavior' "$body_file")
[[ -n $objective && -n $required ]] || fail 'objective and required behavior are required'
instructions=$(printf '%s\n\n%s' "$objective" "$required")

source_repo=${SOURCE_REPOSITORY:-${GITHUB_REPOSITORY:-Young-Consultations/portfolio-tasks}}
issue_number=$(jq -r '.number // empty' "$issue")
[[ $issue_number =~ ^[1-9][0-9]*$ ]] || fail 'source issue number is missing'
attempt=${GITHUB_RUN_ATTEMPT:-1}
[[ $attempt =~ ^[1-9][0-9]*$ ]] || fail 'workflow run attempt is malformed'
correlation_id="${source_repo}#${issue_number}@${attempt}"

dependencies_json=$(printf '%s\n' "${dependencies[@]-}" | jq -Rsc 'split("\n") | map(select(length > 0))')
jq -n \
  --arg schema_version "$CONTRACT_VERSION" --arg correlation_id "$correlation_id" \
  --arg source_repository "$source_repo" --argjson source_issue_number "$issue_number" \
  --arg status "$status" --arg executor "$executor" --arg priority "$priority" --arg project "$project" \
  --argjson parallel_safe "$parallel_safe" --arg target_repository "$target" --arg task_type "$task_type" \
  --argjson dependencies "$dependencies_json" --arg instructions "$instructions" \
  '{schema_version:$schema_version,correlation_id:$correlation_id,
    source:{repository:$source_repository,issue_number:$source_issue_number},status:$status,
    executor:$executor,priority:$priority,project:$project,parallel_safe:$parallel_safe,
    target_repository:$target_repository,task_type:$task_type,dependencies:$dependencies,
    instructions:$instructions}' > "$output.tmp"
mv "$output.tmp" "$output"
