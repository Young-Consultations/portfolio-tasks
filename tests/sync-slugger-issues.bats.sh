#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SCRIPT="$ROOT/scripts/sync-slugger-issues.sh"
pass=0; fail=0
TMPROOT=$(mktemp -d); trap 'rm -rf "$TMPROOT"' EXIT

make_issue(){ jq -n --argjson n "$1" --arg title "$2" --arg body "$3" --arg state "$4" --argjson labels "$5" --argjson assignees "${6:-[]}" --arg url "https://github.com/mightyjoe909/portfolio-tasks/issues/$1" '{number:$n,title:$title,body:$body,state:$state,labels:($labels|map({name:.})),assignees:($assignees|map({login:.})),html_url:$url}'; }
make_target(){ jq -n --argjson n "$1" --arg title "$2" --arg body "$3" --arg state "$4" --argjson labels "$5" --argjson assignees "${6:-[]}" '{number:$n,title:$title,body:$body,state:$state,labels:($labels|map({name:.})),assignees:($assignees|map({login:.}))}'; }
body_for(){ local n=$1 title=$2 body=$3 state=$4; printf '%s\n\n---\n## Portfolio Task Metadata\n- Source repository: `mightyjoe909/portfolio-tasks`\n- Source issue: `#%s`\n- Source URL: `https://github.com/mightyjoe909/portfolio-tasks/issues/%s`\n- Source state: `%s`\n- Managed automatically: Yes\n<!-- portfolio-task-source: mightyjoe909/portfolio-tasks#%s -->' "$body" "$n" "$n" "$state" "$n"; }
setup_mock(){ local d="$TMPROOT/$1"; mkdir -p "$d"; echo "$d"; }
run_case(){ local name="$1" expected="$2" dir="$3" dry="${4:-true}" event="${5:-workflow_dispatch}" action="${6:-}"; local summary="$dir/summary.md"; set +e; GH_MOCK_DIR="$dir" GITHUB_STEP_SUMMARY="$summary" SOURCE_ISSUE_NUMBER=1 DRY_RUN="$dry" GITHUB_EVENT_NAME="$event" GITHUB_EVENT_ACTION="$action" "$SCRIPT" >/tmp/out 2>/tmp/err; rc=$?; set -e; if [[ "$expected" == rc:* ]]; then [[ "$rc" == "${expected#rc:}" ]]; else grep -q "Planned/completed action: .*${expected}" "$summary" && [[ $rc -eq 0 ]]; fi; }
case_ok(){ local n="$1"; shift; if "$@"; then echo "ok - $n"; pass=$((pass+1)); else echo "not ok - $n"; cat /tmp/err 2>/dev/null || true; fail=$((fail+1)); fi }
write_common(){ local d=$1 source=$2 targets=$3; echo "$source" > "$d/GET_repos_mightyjoe909_portfolio-tasks_issues_1.json"; echo "$targets" > "$d/GET_repos_mightyjoe909_slugger_issues.json"; }
export ROOT SCRIPT TMPROOT
export -f make_issue make_target body_for setup_mock run_case write_common

case_ok "opened issue without chatgpt-task is skipped" bash -c 'd=$(setup_mock c1); write_common "$d" "$(make_issue 1 T B open "[]")" "[]"; run_case c1 skipped "$d"'
case_ok "opened issue with chatgpt-task produces create" bash -c 'd=$(setup_mock c2); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[]"; run_case c2 create "$d"'
case_ok "labeling existing issue produces update" bash -c 'd=$(setup_mock c3); old=$(body_for 1 T old open); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$old" open "[\"portfolio-task\"]")]"; run_case c3 update "$d" true issues labeled'
case_ok "edited eligible issue produces update" bash -c 'd=$(setup_mock c4); old=$(body_for 1 T old open); write_common "$d" "$(make_issue 1 T new open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$old" open "[\"portfolio-task\"]")]"; run_case c4 update "$d"'
case_ok "unchanged eligible issue produces no-op" bash -c 'd=$(setup_mock c5); b=$(body_for 1 T B open); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" open "[\"portfolio-task\"]")]"; run_case c5 no-op "$d"'
case_ok "closed eligible issue produces close" bash -c 'd=$(setup_mock c6); b=$(body_for 1 T B open); write_common "$d" "$(make_issue 1 T B closed "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" open "[\"portfolio-task\"]")]"; run_case c6 close "$d"'
case_ok "reopened eligible issue produces reopen" bash -c 'd=$(setup_mock c7); b=$(body_for 1 T B closed); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" closed "[\"portfolio-task\"]")]"; run_case c7 reopen "$d"'
case_ok "removed chatgpt-task produces disable-sync" bash -c 'd=$(setup_mock c8); event=$d/event.json; jq -n "{label:{name:\"chatgpt-task\"}, issue:{number:1}}" > "$event"; b=$(body_for 1 T B open); write_common "$d" "$(make_issue 1 T B open "[]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" open "[\"portfolio-task\",\"manual\"]")]"; GITHUB_EVENT_PATH="$event" run_case c8 disable-sync "$d" true issues unlabeled'
case_ok "existing closed Slugger issue is found" bash -c 'd=$(setup_mock c9); b=$(body_for 1 T B closed); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" closed "[\"portfolio-task\"]")]"; run_case c9 reopen "$d"'
case_ok "duplicate target issue is not created" bash -c 'd=$(setup_mock c10); b=$(body_for 1 T B open); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" open "[\"portfolio-task\"]")]"; run_case c10 no-op "$d"'
case_ok "pull requests are rejected" bash -c 'd=$(setup_mock c11); s=$(make_issue 1 T B open "[\"chatgpt-task\"]" | jq ".pull_request={}"); write_common "$d" "$s" "[]"; run_case c11 rc:1 "$d"'
case_ok "manual dry-run performs no writes" bash -c 'd=$(setup_mock c12); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[]"; run_case c12 create "$d" true; [[ ! -f "$d/writes.log" ]]'
case_ok "source title and body cannot execute shell commands" bash -c 'd=$(setup_mock c13); inj="\$(touch $d/pwned)"; write_common "$d" "$(make_issue 1 "$inj" "$inj" open "[\"chatgpt-task\"]")" "[]"; run_case c13 create "$d" true; [[ ! -e "$d/pwned" ]]'
case_ok "manually added Slugger labels are preserved" bash -c 'd=$(setup_mock c14); b=$(body_for 1 T B open); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 9 "[PORTFOLIO-TASK #1] T" "$b" open "[\"portfolio-task\",\"manual\"]")]"; run_case c14 no-op "$d"'
case_ok "missing optional labels do not fail synchronization" bash -c 'd=$(setup_mock c15); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\",\"optional\"]")" "[]"; run_case c15 create "$d" true; grep -q "Labels skipped: optional" "$d/summary.md"'
case_ok "missing authentication fails safely for write operations" bash -c 'd=$(setup_mock c16); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[]"; run_case c16 rc:1 "$d" false'
case_ok "token values never appear in logs" bash -c 'd=$(setup_mock c17); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[]"; GH_TOKEN=SECRET_TOKEN run_case c17 create "$d" true; ! grep -R "SECRET_TOKEN" "$d" /tmp/out /tmp/err'

case_ok "target matching ignores copied source markers" bash -c 'd=$(setup_mock c18); real=$(body_for 1 T B open); impersonator=$(body_for 99 wrong "copied <!-- portfolio-task-source: mightyjoe909/portfolio-tasks#1 --> marker" open); write_common "$d" "$(make_issue 1 T B open "[\"chatgpt-task\"]")" "[$(make_target 8 "wrong" "$impersonator" open "[\"portfolio-task\"]"),$(make_target 9 "[PORTFOLIO-TASK #1] T" "$real" open "[\"portfolio-task\"]")]"; run_case c18 no-op "$d"; grep -Fq "Matching target issue number: \`9\`" "$d/summary.md"'
case_ok "target search failure aborts before writes" bash -c 'd=$(setup_mock c19); echo "$(make_issue 1 T B open "[\"chatgpt-task\"]")" > "$d/GET_repos_mightyjoe909_portfolio-tasks_issues_1.json"; GH_TOKEN=SECRET run_case c19 rc:1 "$d" false; [[ ! -f "$d/writes.log" ]]; grep -q "API failures: Could not search target issues" "$d/summary.md"'
case_ok "source marker comments are stripped from synchronized bodies" bash -c 'd=$(setup_mock c20); write_common "$d" "$(make_issue 1 T "copied <!-- portfolio-task-source: mightyjoe909/portfolio-tasks#2 --> marker" open "[\"chatgpt-task\"]")" "[]"; GH_TOKEN=SECRET run_case c20 create "$d" false; grep -q "removed portfolio-task-source marker" "$d/writes.log"; ! grep -q "portfolio-tasks#2" "$d/writes.log"'

echo "$pass passed, $fail failed"
[[ $fail -eq 0 ]]
