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
diagnostic_dir=$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/codex-diagnostics.XXXXXX")
trap 'rm -rf "$diagnostic_dir"' EXIT
stdout_file=$diagnostic_dir/stdout
stderr_file=$diagnostic_dir/stderr

sanitize_stderr() {
  sed -E \
    -e 's#([[:alpha:]][[:alnum:]+.-]*://)[^/@[:space:]]+@#\1[REDACTED]@#g' \
    -e 's/([Aa][Uu][Tt][Hh][Oo][Rr][Ii][Zz][Aa][Tt][Ii][Oo][Nn][[:space:]]*:[[:space:]]*)[^[:space:]]+([[:space:]]+[^[:space:]]+)?/\1[REDACTED]/g' \
    -e 's/([Bb][Ee][Aa][Rr][Ee][Rr][[:space:]]+)[^[:space:],;]+/\1[REDACTED]/g' \
    -e 's/([Aa][Pp][Ii][_-]?[Kk][Ee][Yy][[:space:]]*[:=][[:space:]]*)[^[:space:],;]+/\1[REDACTED]/g' \
    -e 's/(sk-[[:alnum:]_-]{8})[[:alnum:]_-]*/\1[REDACTED]/g'
}

classify_failure() {
  local diagnostic=$1
  case "$diagnostic" in
    *'could not resolve host'*|*'name or service not known'*|*'temporary failure in name resolution'*|*'nodename nor servname provided'*|*'dns error'*|*'dns lookup failed'*) echo dns-failure ;;
    *'certificate verify failed'*|*'certificate validation'*|*'tls handshake'*|*'ssl error'*|*'ssl_connect'*|*'unknown ca'*|*'certificate has expired'*) echo tls-failure ;;
    *'connection refused'*|*'econnrefused'*) echo connection-refused ;;
    *'connection timed out'*|*'connect timeout'*|*'connection timeout'*|*'etimedout'*) echo connection-timeout ;;
    *'model_not_found'*|*'model not found'*|*'model access'*|*'does not have access to model'*|*'do not have access to model'*|*'not have access to model'*) echo model-access-error ;;
    *'http status'*|*'http error'*|*'http 4'*|*'http 5'*|*'status code: 4'*|*'status code: 5'*|*'status: 4'*|*'status: 5'*) echo http-error ;;
    *) echo cli-internal-error ;;
  esac
}

# Codex CLI 0.63.0 reads this standard credential name. Keep CODEX_API_KEY as
# the workflow-facing interface and translate it only in this wrapper's process.
export OPENAI_API_KEY="$CODEX_API_KEY"
if "${command[@]}" >"$stdout_file" 2>"$stderr_file"; then
  exit 0
else
  status=$?
  diagnostic=$(tr '[:upper:]' '[:lower:]' < "$stderr_file")
  category=$(classify_failure "$diagnostic")
  echo "run-codex: Codex CLI failed (${category}, exit code ${status})." >&2
  if [[ -s "$stderr_file" ]]; then
    echo 'run-codex: last 20 sanitized stderr lines:' >&2
    tail -n 20 "$stderr_file" | sanitize_stderr >&2
  fi
  exit "$status"
fi
