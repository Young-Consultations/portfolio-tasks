#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WRAPPER="$ROOT/scripts/run-codex.sh"
WORKFLOW="$ROOT/.github/workflows/codex-execute.yml"
TEMP=$(mktemp -d)
trap 'rm -rf "$TEMP"' EXIT

fail() {
  printf 'not ok - %s\n' "$1" >&2
  exit 1
}

make_codex() {
  local help_text=$1 exit_code=${2:-0}
  cat > "$TEMP/codex" <<EOF
#!/usr/bin/env bash
if [[ "\${1:-}" == --version ]]; then
  echo 'codex-cli 1.2.3'
elif [[ "\${1:-}" == exec && "\${2:-}" == --help ]]; then
  cat <<'HELP'
$help_text
HELP
elif [[ "\${1:-}" == exec ]]; then
  printf '%s\\n' "\$*" > "\$CODEX_TEST_ARGS"
  cat > "\$CODEX_TEST_STDIN"
  exit $exit_code
else
  exit 2
fi
EOF
  chmod +x "$TEMP/codex"
}

run_wrapper() {
  PATH="$TEMP:$PATH" CODEX_TEST_ARGS="$TEMP/args" CODEX_TEST_STDIN="$TEMP/stdin" \
    OPENAI_API_KEY='contract-test-secret-that-must-not-appear' \
    "$WRAPPER" > "$TEMP/output"
}

make_codex 'Usage: codex exec --sandbox <MODE> --ask-for-approval <POLICY> --skip-git-repo-check [PROMPT]'
printf 'keep this prompt byte-for-byte\n' | run_wrapper || fail 'wrapper exits cleanly when Codex exists'
grep -Fq 'Codex version: codex-cli 1.2.3' "$TEMP/output" || fail 'wrapper reports version'
grep -Fq 'Detected capabilities: --sandbox --ask-for-approval --skip-git-repo-check' "$TEMP/output" || fail 'wrapper detects capabilities'
cmp -s <(printf 'keep this prompt byte-for-byte\n') "$TEMP/stdin" || fail 'wrapper preserves stdin'
grep -Fq 'exec --sandbox workspace-write --ask-for-approval never --skip-git-repo-check -' "$TEMP/args" || fail 'wrapper uses supported options'
! grep -Fq 'contract-test-secret-that-must-not-appear' "$TEMP/output" || fail 'wrapper exposes OPENAI_API_KEY'
echo 'ok - supported CLI contract and secret-safe logging'

make_codex 'Usage: codex exec --sandbox <MODE> [PROMPT]'
printf 'older prompt\n' | run_wrapper || fail 'wrapper supports older Codex CLI'
grep -Fq 'Using compatibility mode:' "$TEMP/output" || fail 'wrapper reports compatibility mode'
grep -Fq 'exec --sandbox workspace-write -' "$TEMP/args" || fail 'wrapper omits unsupported options'
! grep -Fq -- '--ask-for-approval' "$TEMP/args" || fail 'wrapper passes unsupported approval option'
! grep -Fq -- '--skip-git-repo-check' "$TEMP/args" || fail 'wrapper passes unsupported repository option'
echo 'ok - older CLI compatibility contract'

make_codex 'Usage: codex exec [PROMPT]' 23
set +e
printf 'failing prompt\n' | run_wrapper
status=$?
set -e
[[ $status -eq 23 ]] || fail 'wrapper does not return Codex exit code unchanged'
echo 'ok - Codex exit code is unchanged'

grep -Fq 'scripts/run-codex.sh < "$RUNNER_TEMP/instructions.md"' "$WORKFLOW" || fail 'workflow does not invoke wrapper'
if grep -Eq '^[[:space:]]+codex exec([[:space:]]|$)' "$WORKFLOW"; then
  fail 'workflow invokes codex exec directly'
fi
echo 'ok - workflow delegates Codex execution to wrapper'
