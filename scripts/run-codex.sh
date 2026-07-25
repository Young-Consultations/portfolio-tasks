#!/usr/bin/env bash
set -euo pipefail

# Do not enable shell tracing here: the Codex process inherits authentication
# from its environment, and this wrapper must never render that environment.
set +x

if [[ -z "${CODEX_API_KEY:-}" ]]; then
  echo 'run-codex: CODEX_API_KEY is required; refusing to use an interactive or cached login.' >&2
  exit 78
fi

if ! command -v codex >/dev/null 2>&1; then
  echo 'run-codex: codex executable was not found in PATH.' >&2
  exit 127
fi

codex_version=$(codex --version 2>&1) || {
  status=$?
  echo 'run-codex: unable to determine the Codex version.' >&2
  exit "$status"
}

exec_help=$(codex exec --help 2>&1) || {
  status=$?
  echo 'run-codex: unable to inspect Codex exec capabilities.' >&2
  exit "$status"
}

supports_option() {
  grep -Eq -- "(^|[[:space:],])$1([=[:space:]<[]|$)" <<< "$exec_help"
}

command=(codex exec)
capabilities=()
compatibility=()

if supports_option '--sandbox'; then
  command+=(--sandbox workspace-write)
  capabilities+=(--sandbox)
else
  echo 'run-codex: installed Codex CLI does not support the required --sandbox workspace-write policy.' >&2
  exit 64
fi

if supports_option '--ask-for-approval'; then
  command+=(--ask-for-approval never)
  capabilities+=(--ask-for-approval)
else
  compatibility+=('approval option unavailable')
fi

if supports_option '--skip-git-repo-check'; then
  command+=(--skip-git-repo-check)
  capabilities+=(--skip-git-repo-check)
else
  compatibility+=('Git repository check managed by installed CLI')
fi

printf 'Codex version: %s\n' "$codex_version"
if ((${#capabilities[@]})); then
  printf 'Detected capabilities: %s\n' "${capabilities[*]}"
else
  printf 'Detected capabilities: none of the optional wrapper flags\n'
fi
if ((${#compatibility[@]})); then
  printf 'Using compatibility mode: %s\n' "$(IFS='; '; echo "${compatibility[*]}")"
else
  printf 'Using compatibility mode: all optional wrapper flags supported\n'
fi

# A prompt of "-" tells compatible Codex exec versions to consume the prompt
# from stdin. Do not use exec here: a sanitized diagnostic is required on failure.
command+=(-)
diagnostic_file=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/codex-diagnostic.XXXXXX")
trap 'rm -f "$diagnostic_file"' EXIT
if "${command[@]}" 2>"$diagnostic_file"; then
  exit 0
else
  status=$?
  diagnostic=$(tr '[:upper:]' '[:lower:]' < "$diagnostic_file")
  case "$diagnostic" in
    *'401'*|*'invalid api key'*|*'incorrect api key'*|*'authentication'*|*'unauthorized'*) category=authentication-failure ;;
    *'403'*|*'model access'*|*'permission denied'*|*'forbidden'*) category=authorization-or-model-access-failure ;;
    *'429'*|*'rate limit'*|*'too many requests'*) category=rate-limit ;;
    *'network'*|*'connection'*|*'timed out'*|*'timeout'*|*'service unavailable'*|*'502'*|*'503'*|*'504'*) category=network-or-service-failure ;;
    *) category=cli-runtime-failure ;;
  esac
  echo "run-codex: Codex CLI failed (${category}, exit code ${status})." >&2
  exit "$status"
fi
