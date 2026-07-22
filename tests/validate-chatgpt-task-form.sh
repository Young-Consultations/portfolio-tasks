#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
FORM="$ROOT/.github/ISSUE_TEMPLATE/chatgpt-task.yml"

[[ -f "$FORM" ]] || { echo "Missing issue form: $FORM" >&2; exit 1; }

ruby -ryaml - "$FORM" <<'RUBY'
path = ARGV.fetch(0)
text = File.read(path, encoding: "UTF-8")
data = YAML.safe_load(text)

required_ids = %w[
  objective
  target_repository
  task_type
  required_behavior
  acceptance_criteria
  testing_requirements
  security_constraints
]

fields = data.fetch("body", [])
  .select { |item| item.is_a?(Hash) && item["id"] }
  .to_h { |item| [item.fetch("id"), item] }

missing = required_ids - fields.keys
abort("Missing required field IDs: #{missing.join(', ')}") unless missing.empty?

not_required = required_ids.reject do |field_id|
  fields.fetch(field_id).fetch("validations", {})["required"] == true
end
abort("Fields must remain required: #{not_required.join(', ')}") unless not_required.empty?

labels = data.fetch("labels", [])
abort("chatgpt-task label metadata is not configured") unless labels.include?("chatgpt-task")
abort("codex-ready must not be configured by this intake form") if labels.include?("codex-ready")

unstable_ids = fields.keys.reject { |field_id| field_id.match?(/\A[a-z][a-z0-9_]*\z/) }
abort("Field IDs must use stable snake_case: #{unstable_ids.sort.join(', ')}") unless unstable_ids.empty?

secret_patterns = [
  /ghp_[A-Za-z0-9_]{20,}/,
  /github_pat_[A-Za-z0-9_]{20,}/,
  /AKIA[0-9A-Z]{16}/,
  /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/,
  /(?:password|api[_ -]?key|client[_ -]?secret|token)\s*[:=]\s*['"]?[A-Za-z0-9_.\/=+-]{8,}/i,
]

secret_patterns.each do |pattern|
  abort("Potential secret or example credential found by pattern: #{pattern.inspect}") if text.match?(pattern)
end

puts "chatgpt-task issue form validation passed"
RUBY
