#!/usr/bin/env bash
set -euo pipefail

SOURCE_REPO="Young-Consultations/portfolio-tasks"
TARGET_REPO="Young-Consultations/slugger"
SOURCE_LABEL="chatgpt-task"
TARGET_MANAGED_LABEL="portfolio-task"
MARKER_PREFIX="<!-- portfolio-task-source: "
API_TIMEOUT="${API_TIMEOUT:-20}"
SUMMARY_FILE="${GITHUB_STEP_SUMMARY:-/dev/null}"
DRY_RUN="${DRY_RUN:-true}"
EVENT_NAME="${GITHUB_EVENT_NAME:-workflow_dispatch}"
EVENT_ACTION="${GITHUB_EVENT_ACTION:-}"
SOURCE_ISSUE_NUMBER="${SOURCE_ISSUE_NUMBER:-}"
EVENT_PATH="${GITHUB_EVENT_PATH:-}"

TARGET_ISSUE_NUMBER=""
TARGET_ISSUE_STATE=""
TARGET_ISSUE_JSON="null"
ACTION="no-op"
RESULT="success"
VALIDATION_ERRORS=()
API_FAILURES=()
LABELS_APPLIED=()
LABELS_SKIPPED=()
ASSIGNEES_APPLIED=()
ASSIGNEES_SKIPPED=()
WRITES=()

append_summary() { printf '%s\n' "$*" >> "$SUMMARY_FILE"; }
contains_label() { jq -e --arg n "$1" 'any(.labels[]?.name; . == $n)' >/dev/null; }
json_array_lines() { jq -r '.[]? // empty'; }
require_constant_repos() {
  [[ "$SOURCE_REPO" == "Young-Consultations/portfolio-tasks" ]] || VALIDATION_ERRORS+=("Invalid source repository constant")
  [[ "$TARGET_REPO" == "Young-Consultations/slugger" ]] || VALIDATION_ERRORS+=("Invalid target repository constant")
}
api() {
  if [[ -n "${GH_MOCK_DIR:-}" ]]; then
    local method="GET" endpoint="" out=""
    while (($#)); do
      case "$1" in --method) method="$2"; shift 2;; -*) shift 2 || true;; *) endpoint="$1"; shift;; esac
    done
    local key; key=$(printf '%s_%s' "$method" "$endpoint" | tr '/?' '__' | tr -cd '[:alnum:]_.-')
    out="$GH_MOCK_DIR/$key.json"
    [[ -f "$out" ]] || { echo "mock missing: $key" >&2; return 44; }
    cat "$out"; return 0
  fi
  timeout "$API_TIMEOUT" gh api "$@"
}
api_write() {
  local method="$1" endpoint="$2" payload="$3"
  if [[ "$DRY_RUN" == "true" ]]; then WRITES+=("$method $endpoint"); echo '{}'; return 0; fi
  [[ -n "${GH_TOKEN:-}" ]] || { API_FAILURES+=("Missing SLUGGER_ISSUES_TOKEN/GH_TOKEN for write operation"); return 40; }
  if [[ -n "${GH_MOCK_DIR:-}" ]]; then echo "${payload}" >> "$GH_MOCK_DIR/writes.log"; WRITES+=("$method $endpoint"); echo '{}'; return 0; fi
  timeout "$API_TIMEOUT" gh api --method "$method" "$endpoint" --input - <<<"$payload"
}
load_source_issue() {
  if [[ "$EVENT_NAME" == "issues" && -n "$EVENT_PATH" && -f "$EVENT_PATH" ]]; then
    SOURCE_ISSUE_NUMBER=$(jq -r '.issue.number // empty' "$EVENT_PATH")
  fi
  [[ "$SOURCE_ISSUE_NUMBER" =~ ^[0-9]+$ ]] || { VALIDATION_ERRORS+=("source_issue_number must be numeric"); return; }
  SOURCE_JSON=$(api "repos/$SOURCE_REPO/issues/$SOURCE_ISSUE_NUMBER") || { VALIDATION_ERRORS+=("Source issue could not be read"); return; }
}
validate_source() {
  require_constant_repos
  [[ "$(jq -r '.number // empty' <<<"$SOURCE_JSON")" == "$SOURCE_ISSUE_NUMBER" ]] || VALIDATION_ERRORS+=("Source issue number mismatch")
  [[ "$(jq -r 'has("pull_request")' <<<"$SOURCE_JSON")" == "false" ]] || VALIDATION_ERRORS+=("Pull requests are not synchronized")
  local title; title=$(jq -r '.title // empty' <<<"$SOURCE_JSON")
  [[ -n "$title" ]] || VALIDATION_ERRORS+=("Issue title is required")
  ((${#title} <= 256)) || VALIDATION_ERRORS+=("Issue title exceeds 256 characters")
  local body_len; body_len=$(jq -r '(.body // "") | length' <<<"$SOURCE_JSON")
  ((body_len <= 65000)) || VALIDATION_ERRORS+=("Issue body exceeds safe synchronization length")
}
build_body() {
  local managed="$1" body state url
  body=$(jq -r '(.body // "") | gsub("<!-- portfolio-task-source: [^>]*-->"; "[removed portfolio-task-source marker]")' <<<"$SOURCE_JSON")
  state=$(jq -r '.state' <<<"$SOURCE_JSON")
  url=$(jq -r '.html_url' <<<"$SOURCE_JSON")
  jq -nr --arg body "$body" --arg sr "$SOURCE_REPO" --arg n "$SOURCE_ISSUE_NUMBER" --arg url "$url" --arg state "$state" --arg managed "$managed" '
    $body + "\n\n---\n## Portfolio Task Metadata\n- Source repository: `" + $sr + "`\n- Source issue: `#" + $n + "`\n- Source URL: `" + $url + "`\n- Source state: `" + $state + "`\n- Managed automatically: " + $managed + "\n<!-- portfolio-task-source: " + $sr + "#" + $n + " -->"'
}
find_target() {
  local marker issues
  marker="${MARKER_PREFIX}${SOURCE_REPO}#${SOURCE_ISSUE_NUMBER} -->"
  issues=$(api --method GET "repos/$TARGET_REPO/issues" -f state=all -f per_page=100) || { API_FAILURES+=("Could not search target issues"); return 1; }
  TARGET_ISSUE_JSON=$(jq --arg marker "$marker" '[.[] | select((.pull_request? | not) and ((.body // "") | endswith($marker)) and ((.body // "") | contains("\n## Portfolio Task Metadata\n")))] | sort_by(.number) | first // null' <<<"$issues")
  TARGET_ISSUE_NUMBER=$(jq -r '.number // empty' <<<"$TARGET_ISSUE_JSON")
  TARGET_ISSUE_STATE=$(jq -r '.state // empty' <<<"$TARGET_ISSUE_JSON")
}
managed_labels() {
  if [[ -n "$TARGET_ISSUE_NUMBER" ]]; then
    jq -r --arg source "$SOURCE_LABEL" --arg managed "$TARGET_MANAGED_LABEL" '([.labels[]?.name | select(. != $source)] + [$managed]) | unique | .[]' <<<"$TARGET_ISSUE_JSON"
  else
    printf '%s\n' "$TARGET_MANAGED_LABEL"
  fi
}
desired_json() {
  local managed="$1" title body state labels assignees
  title="[PORTFOLIO-TASK #${SOURCE_ISSUE_NUMBER}] $(jq -r '.title' <<<"$SOURCE_JSON")"
  body=$(build_body "$managed")
  state=$(jq -r '.state' <<<"$SOURCE_JSON")
  [[ "$managed" == "No - chatgpt-task label removed" ]] && state="$TARGET_ISSUE_STATE"
  labels=$(managed_labels | jq -R . | jq -s .)
  assignees=$(jq '[.assignees[]?.login]' <<<"$SOURCE_JSON")
  jq -n --arg title "$title" --arg body "$body" --arg state "$state" --argjson labels "$labels" --argjson assignees "$assignees" '{title:$title, body:$body, state:$state, labels:$labels, assignees:$assignees}'
}
existing_subset() {
  jq '{title:(.title // ""), body:(.body // ""), state:(.state // ""), labels:([.labels[]?.name] | sort), assignees:([.assignees[]?.login] | sort)}' <<<"$TARGET_ISSUE_JSON"
}
plan_action() {
  local has_label removed desired existing
  has_label=false; contains_label "$SOURCE_LABEL" <<<"$SOURCE_JSON" && has_label=true
  removed=false; [[ "$EVENT_ACTION" == "unlabeled" && -n "$EVENT_PATH" && -f "$EVENT_PATH" ]] && [[ "$(jq -r '.label.name // empty' "$EVENT_PATH")" == "$SOURCE_LABEL" ]] && removed=true
  if [[ "$removed" == "true" ]]; then
    [[ -n "$TARGET_ISSUE_NUMBER" ]] && ACTION="disable-sync" || ACTION="no-op"; return
  fi
  if [[ "$has_label" != "true" ]]; then ACTION="skipped"; return; fi
  desired=$(desired_json "Yes")
  if [[ -z "$TARGET_ISSUE_NUMBER" ]]; then ACTION="create"; return; fi
  existing=$(existing_subset)
  if [[ "$(jq -S '.labels|=sort|.assignees|=sort' <<<"$desired")" == "$(jq -S . <<<"$existing")" ]]; then ACTION="no-op"; return; fi
  case "$(jq -r '.state' <<<"$SOURCE_JSON"):$TARGET_ISSUE_STATE" in closed:open) ACTION="close";; open:closed) ACTION="reopen";; *) ACTION="update";; esac
}
apply_action() {
  local payload desired endpoint
  [[ "$ACTION" =~ ^(skipped|no-op)$ ]] && return 0
  if [[ "$ACTION" == "disable-sync" ]]; then
    payload=$(desired_json "No - chatgpt-task label removed" | jq 'del(.assignees) | .labels = ((.labels - ["portfolio-task"]) | sort)')
    api_write PATCH "repos/$TARGET_REPO/issues/$TARGET_ISSUE_NUMBER" "$payload" >/dev/null || return 1; return 0
  fi
  desired=$(desired_json "Yes")
  LABELS_APPLIED+=("$TARGET_MANAGED_LABEL")
  while IFS= read -r l; do [[ -n "$l" ]] && LABELS_SKIPPED+=("$l (optional source label skipped)"); done < <(jq -r --arg source "$SOURCE_LABEL" '.labels[]?.name | select(. != $source)' <<<"$SOURCE_JSON")
  for a in $(jq -r '.assignees[]' <<<"$desired"); do ASSIGNEES_APPLIED+=("$a (requested if assignable)"); done
  if [[ "$ACTION" == "create" ]]; then endpoint="repos/$TARGET_REPO/issues"; api_write POST "$endpoint" "$desired" >/dev/null || return 1; else endpoint="repos/$TARGET_REPO/issues/$TARGET_ISSUE_NUMBER"; api_write PATCH "$endpoint" "$desired" >/dev/null || return 1; fi
}
write_summary() {
  local title has_label summary_source
  summary_source="${SOURCE_JSON:-}"
  [[ -n "$summary_source" ]] || summary_source='{}'
  title=$(jq -r '.title // ""' <<<"$summary_source")
  has_label=false; [[ -n "${SOURCE_JSON:-}" ]] && contains_label "$SOURCE_LABEL" <<<"$SOURCE_JSON" && has_label=true
  append_summary "## Slugger Issue Synchronization"
  append_summary "- Source repository: \`$SOURCE_REPO\`"
  append_summary "- Source issue number: \`$SOURCE_ISSUE_NUMBER\`"
  append_summary "- Source issue title: ${title}"
  append_summary "- chatgpt-task present: \`$has_label\`"
  append_summary "- Target repository: \`$TARGET_REPO\`"
  append_summary "- Matching target issue number: \`${TARGET_ISSUE_NUMBER:-none}\`"
  append_summary "- Planned/completed action: \`$ACTION\`"
  append_summary "- Dry run: \`$DRY_RUN\`"
  append_summary "- Labels applied: ${LABELS_APPLIED[*]:-none}"
  append_summary "- Labels skipped: ${LABELS_SKIPPED[*]:-none}"
  append_summary "- Assignees applied: ${ASSIGNEES_APPLIED[*]:-none}"
  append_summary "- Assignees skipped: ${ASSIGNEES_SKIPPED[*]:-none}"
  append_summary "- Validation errors: ${VALIDATION_ERRORS[*]:-none}"
  append_summary "- API failures: ${API_FAILURES[*]:-none}"
  append_summary "- Final synchronization result: \`$RESULT\`"
}
main() {
  load_source_issue
  [[ ${#VALIDATION_ERRORS[@]} -eq 0 ]] && validate_source
  if [[ "$EVENT_NAME" == "workflow_dispatch" && "$DRY_RUN" != "true" && -z "${GH_TOKEN:-}" ]]; then API_FAILURES+=("Missing SLUGGER_ISSUES_TOKEN/GH_TOKEN for non-dry-run manual write"); fi
  if [[ ${#VALIDATION_ERRORS[@]} -eq 0 && ${#API_FAILURES[@]} -eq 0 ]]; then find_target && plan_action && apply_action || RESULT="failed"; fi
  [[ ${#VALIDATION_ERRORS[@]} -eq 0 && ${#API_FAILURES[@]} -eq 0 && "$RESULT" != "failed" ]] || RESULT="failed"
  write_summary
  [[ "$RESULT" == "success" ]]
}
main "$@"
