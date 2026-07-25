#!/usr/bin/env bash
set -euo pipefail

# Do not enable shell tracing here: the Codex process inherits authentication
# from its environment, and this wrapper must never render that environment.
set +x

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
  compatibility+=('sandbox option unavailable')
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
# from stdin. exec replaces this process so Codex's status is returned unchanged.
command+=(-)
exec "${command[@]}"
