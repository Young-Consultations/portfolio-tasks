#!/usr/bin/env bash
# Portable helpers for the shared execution input/result contracts.
set -euo pipefail
readonly TARGET_REPOSITORY='Young-Consultations/portfolio-tasks'
readonly INPUT_VERSION='ai-sdlc-execution-input/v1'
readonly RESULT_VERSION='ai-sdlc-execution-result/v1'

contract_fail() { printf 'execution contract: %s\n' "$*" >&2; return 1; }

validate_execution_input() {
  local file=$1
  jq -e --arg v "$INPUT_VERSION" --arg target "$TARGET_REPOSITORY" '
    type == "object" and
    (.contract_version == $v) and
    (.correlation_id | type == "string" and length > 0 and (test("[\\r\\n]") | not)) and
    (.source_issue | type == "object") and
    (.source_issue.repository == $target) and
    (.source_issue.number | type == "number" and . >= 1 and floor == .) and
    (.target_repository == $target) and (.executor == "codex") and
    (.draft_pr_only == true) and
    (.instructions | type == "string" and length > 0)
  ' "$file" >/dev/null || contract_fail 'invalid execution input'
}

write_execution_result() {
  local output=$1 status=$2 correlation=$3 branch=$4 pr_url=$5 workflow_url=$6
  local validation=$7 tests=$8 category=$9 message=${10} started=${11} completed=${12}
  [[ "$status" == succeeded || "$status" == failed ]] || contract_fail 'invalid result status'
  jq -n --arg version "$RESULT_VERSION" --arg correlation "$correlation" --arg status "$status" \
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
    write-result) write_execution_result "$@" ;;
    comment) result_comment "$@" ;;
    *) contract_fail 'usage: execution-contract.sh validate-input|write-result|comment ...' ;;
  esac
fi
