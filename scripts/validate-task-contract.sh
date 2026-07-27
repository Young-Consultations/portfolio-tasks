#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
schema=${TASK_CONTRACT_SCHEMA:-$root/schemas/task-contract.schema.json}
[[ $# == 1 ]] || { echo "usage: $0 CONTRACT.json" >&2; exit 2; }
[[ -r $schema ]] || { echo "task contract schema is unavailable: $schema" >&2; exit 1; }

# This jq expression implements the closed, non-coercing validation rules in the
# canonical schema. Keeping it here avoids a network-installed validator in the gate.
jq -e --slurpfile schema "$schema" '
  . as $c | $schema[0] as $s |
  ($s.properties.schema_version.const == "ai-sdlc-contract/v1") and
  (keys | sort == ($s.required | sort)) and
  (.schema_version == $s.properties.schema_version.const) and
  (.correlation_id | type == "string" and test("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*@[1-9][0-9]*$")) and
  (.source | type == "object" and (keys | sort == ["issue_number","repository"]) and
    (.repository | test("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")) and
    (.issue_number | type == "number" and . > 0 and floor == .)) and
  ([.status] - $s.properties.status.enum | length == 0) and
  ([.executor] - $s.properties.executor.enum | length == 0) and
  ([.priority] - $s.properties.priority.enum | length == 0) and
  ([.task_type] - $s.properties.task_type.enum | length == 0) and
  (.project | type == "string" and length > 0) and
  (.parallel_safe | type == "boolean") and
  (.target_repository | type == "string" and test("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")) and
  (.dependencies | type == "array" and all(.[]; type == "string" and test("^(#[1-9][0-9]*|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*)$"))) and
  (.instructions | type == "string" and length > 0)
' "$1" >/dev/null || { echo 'task contract does not conform to task-contract.schema.json' >&2; exit 1; }
