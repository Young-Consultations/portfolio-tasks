#!/usr/bin/env bash
# Shared, deliberately small issue-form parsing and normalization helpers.

set -euo pipefail

readonly CONTRACT_VERSION='ai-sdlc-contract/v1'

section_value() {
  local heading=$1 file=$2
  awk -v wanted="$heading" '
    $0 == "### " wanted { found=1; next }
    found && /^### / { exit }
    found { sub(/\r$/, ""); lines[++count]=$0 }
    END {
      first=1; last=count
      while (first <= last && lines[first] ~ /^[[:space:]]*$/) first++
      while (last >= first && lines[last] ~ /^[[:space:]]*$/) last--
      for (i=first; i<=last; i++) print lines[i]
    }
  ' "$file"
}

single_label_value() {
  local prefix=$1 issue=$2
  mapfile -t matches < <(jq -r --arg prefix "$prefix" '
    [.labels[]? | if type == "object" then .name else . end]
    | .[] | select(startswith($prefix)) | ltrimstr($prefix)
  ' "$issue")
  ((${#matches[@]} == 1)) || fail "exactly one ${prefix}* label is required"
  printf '%s' "${matches[0]}"
}

fail() {
  printf 'task contract: %s\n' "$*" >&2
  exit 1
}

normalize_task_type() {
  case "$1" in
    bug-fix|'Bug fix') printf bug-fix ;;
    feature|Feature) printf feature ;;
    refactor|Refactor) printf refactor ;;
    ci-cd|'CI/CD') printf ci-cd ;;
    documentation|Documentation) printf documentation ;;
    security|Security) printf security ;;
    repository-governance|'Repository governance') printf repository-governance ;;
    automation|Automation) printf automation ;;
    investigation|Investigation) printf investigation ;;
    *) fail "unsupported task type: $1" ;;
  esac
}

normalize_status() {
  case "$1" in
    proposed|approved|queued|running|draft-pr|blocked|done) printf '%s' "$1" ;;
    ready) printf approved ;; # documented legacy value
    *) fail "unsupported status: $1" ;;
  esac
}

normalize_priority() {
  case "$1" in
    P0|P1|P2|P3) printf '%s' "$1" ;;
    p0|p1|p2|p3) printf '%s' "${1^^}" ;;
    *) fail "unsupported priority: $1" ;;
  esac
}
