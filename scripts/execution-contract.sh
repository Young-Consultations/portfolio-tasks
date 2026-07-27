#!/usr/bin/env bash
# Portable helpers for the shared execution input/result contracts.
set -euo pipefail
readonly TARGET_REPOSITORY='Young-Consultations/portfolio-tasks'

contract_fail() { printf 'execution contract: %s\n' "$*" >&2; return 1; }

validate_execution_input() {
  local file=$1
  python -m ai_sdlc_contracts validate-input "$file" >/dev/null ||
    contract_fail 'invalid execution input'
  parse_source_issue "$file" >/dev/null
  [[ $(jq -r '.target_repository' "$file") == "$TARGET_REPOSITORY" ]] ||
    contract_fail 'target repository is not this repository'
}

parse_source_issue() {
  local file=$1 source_issue source_repository issue
  source_issue=$(jq -er '.source_issue | select(type == "string")' "$file") ||
    contract_fail 'invalid canonical source_issue'
  if [[ $source_issue =~ ^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#([1-9][0-9]*)$ ]]; then
    source_repository=${BASH_REMATCH[1]}
    issue=${BASH_REMATCH[2]}
  else
    contract_fail 'invalid canonical source_issue'
    return 1
  fi
  [[ $source_repository == "$TARGET_REPOSITORY" ]] ||
    contract_fail 'source issue is not in this repository'
  printf 'source_repository=%s\nissue=%s\n' "$source_repository" "$issue"
}

write_execution_result() {
  local output=$1 status=$2 correlation=$3 branch=$4 pr_url=$5 workflow_url=$6
  local validation=$7 tests=$8 category=$9 message=${10} started=${11} completed=${12}
  [[ "$status" == succeeded || "$status" == failed ]] || contract_fail 'invalid result status'
  jq -n --arg version 'ai-sdlc-contract/v1' --arg correlation "$correlation" --arg status "$status" \
    --arg target "$TARGET_REPOSITORY" --arg branch "$branch" --arg pr "$pr_url" \
    --arg workflow "$workflow_url" --arg validation "$validation" --arg tests "$tests" \
    --arg category "$category" --arg message "${message:0:500}" --arg started "$started" --arg completed "$completed" '
    {contract_version:$version,correlation_id:$correlation,execution_status:$status,
     target_repository:$target,branch_name:(if $branch=="" then null else $branch end),
     pull_request_url:(if $pr=="" then null else $pr end),workflow_url:$workflow,
     validation_result:$validation,test_result:$tests,
     failure_category:(if $category=="" then null else $category end),
     failure_message:(if $message=="" then null else $message end),started_at:$started,completed_at:$completed}
  ' > "$output"
  python -m ai_sdlc_contracts validate-result "$output" >/dev/null || {
    rm -f "$output"
    contract_fail 'invalid execution result'
  }
}

result_comment() {
  local file=$1
  jq -r '"<!-- codex-execution-result:" + .correlation_id + " -->\n" +
    "Codex execution **" + .execution_status + "**.\n\n" +
    "- Branch: " + (.branch_name // "not created") + "\n" +
    "- Draft PR: " + (.pull_request_url // "not created") + "\n" +
    "- Validation: " + .validation_result + "\n" +
    "- Tests: " + .test_result + "\n" +
    "- Failure category: " + (.failure_category // "none") + "\n" +
    "- Workflow: " + .workflow_url' "$file"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  command=${1:-}; shift || true
  case "$command" in
    validate-input) validate_execution_input "$@" ;;
    parse-source-issue) parse_source_issue "$@" ;;
    write-result) write_execution_result "$@" ;;
    comment) result_comment "$@" ;;
    *) contract_fail 'usage: execution-contract.sh validate-input|parse-source-issue|write-result|comment ...' ;;
  esac
fi
