#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo 'Usage: validate-portfolio-dispatch.sh <issue-json-file> [--mock-open-issues <refs-file>]' >&2
  exit 2
}

[[ $# -ge 1 ]] || usage
ISSUE_PATH=$1
shift
MOCK_OPEN_ISSUES=""
while (($#)); do
  case "$1" in
    --mock-open-issues)
      [[ $# -ge 2 ]] || usage
      MOCK_OPEN_ISSUES=$2
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ -f "$ISSUE_PATH" ]] || { echo "Issue JSON not found: $ISSUE_PATH" >&2; exit 2; }

BODY=$(jq -r '.body // ""' "$ISSUE_PATH")
ERRORS=()

section_value() {
  local label=$1
  awk -v label="$label" '
    $0 == "### " label {capture=1; next}
    /^### / && capture {exit}
    capture {print}
  ' <<<"$BODY" | sed -e '1{/^$/d;}' -e '${/^$/d;}'
}

add_error() { ERRORS+=("$1"); }
contains_value() {
  local needle=$1; shift
  local item
  for item in "$@"; do [[ "$item" == "$needle" ]] && return 0; done
  return 1
}

REQUIRED=(
  'Project'
  'Priority'
  'Executor'
  'Execution status'
  'Target repository'
  'Parallel-safe'
  'Dependency issue references'
  'Risk'
  'Estimated scope'
  'Objective'
  'Required behavior'
  'Acceptance criteria'
  'Testing requirements'
  'Security and safety constraints'
)

for field in "${REQUIRED[@]}"; do
  value=$(section_value "$field")
  if [[ -z "$value" || "$value" =~ ^_[Nn]o[[:space:]]response_$ ]]; then
    add_error "Missing required metadata field: $field"
  fi
done

check_allowed() {
  local field=$1; shift
  local value
  value=$(section_value "$field")
  if [[ -n "$value" ]] && ! contains_value "$value" "$@"; then
    local joined
    printf -v joined '%s, ' "$@"
    joined=${joined%, }
    add_error "$field must be one of: $joined"
  fi
}

check_allowed 'Priority' P0 P1 P2 P3
check_allowed 'Executor' codex human chatgpt-planning
check_allowed 'Execution status' proposed approved queued running draft-pr blocked done
check_allowed 'Parallel-safe' yes no
check_allowed 'Risk' low medium high
check_allowed 'Estimated scope' small medium large

TARGET_REPOSITORY=$(section_value 'Target repository')
if [[ -n "$TARGET_REPOSITORY" && ! "$TARGET_REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  add_error 'Target repository must use owner/repository format with GitHub-safe characters'
fi

EXECUTOR=$(section_value 'Executor')
EXECUTION_STATUS=$(section_value 'Execution status')
[[ "$EXECUTOR" == codex ]] || add_error 'Codex dispatch requires Executor to be codex'
[[ "$EXECUTION_STATUS" == approved ]] || add_error 'Codex dispatch requires Execution status to be approved'

DEPENDENCIES=$(section_value 'Dependency issue references')
if [[ -n "$DEPENDENCIES" && "$(tr '[:upper:]' '[:lower:]' <<<"$DEPENDENCIES")" != none ]]; then
  readarray -t DEP_REFS < <(tr ',[:space:]' '\n' <<<"$DEPENDENCIES" | sed '/^$/d')
  for ref in "${DEP_REFS[@]}"; do
    if [[ ! "$ref" =~ ^(#[0-9]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+)$ ]]; then
      add_error "Dependency reference is malformed: $ref"
    elif [[ -n "$MOCK_OPEN_ISSUES" ]] && ! grep -Fxq -- "$ref" "$MOCK_OPEN_ISSUES"; then
      add_error "Dependency reference is unresolved or closed: $ref"
    fi
  done
fi

PROJECT=$(section_value 'Project')
PRIORITY=$(section_value 'Priority')
LABELS=$(jq -r '.labels[]? | if type == "string" then . else .name // empty end' "$ISSUE_PATH")
if [[ -n "$PROJECT" ]] && ! grep -Fxq -- "project:$PROJECT" <<<"$LABELS"; then
  add_error "Missing deterministic project label: project:$PROJECT"
fi
if [[ -n "$PRIORITY" ]] && ! grep -Fxq -- "priority:$PRIORITY" <<<"$LABELS"; then
  add_error "Missing deterministic priority label: priority:$PRIORITY"
fi

if ((${#ERRORS[@]} == 0)); then
  jq -n '{ok:true, errors:[], comment:"Portfolio dispatch validation passed. This issue is eligible for Codex dispatch."}'
  exit 0
fi

ERROR_JSON=$(printf '%s\n' "${ERRORS[@]}" | jq -R . | jq -s .)
COMMENT=$(printf 'Portfolio dispatch validation failed. Fix these items before Codex dispatch:\n'; printf -- '- %s\n' "${ERRORS[@]}")
jq -n --argjson errors "$ERROR_JSON" --arg comment "$COMMENT" '{ok:false, errors:$errors, comment:$comment}'
exit 1
