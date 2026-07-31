"""Secure, version-adaptive runtime wrapper for ``codex exec``."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import BinaryIO, cast

EX_CONFIG = 78
EX_USAGE = 64
NO_CHANGES_EXIT = 3
TIMEOUT_EXIT = 124
DEFAULT_TIMEOUT = 2400.0
RESULT_FILENAME = "codex-result.json"
SUPPORTED_RESULT_STATUSES = frozenset({"changed", "already_satisfied", "failed"})
LOGGER = logging.getLogger("run-codex")
MAX_CONSOLE_DIAGNOSTIC_CHARS = 12_000

RETRY_INSTRUCTION = b"""\
\n--------------------------------------------------

Your previous attempt exited successfully but produced no repository changes and did
not provide a valid structured already_satisfied result.

Continue the autonomous execution without asking for confirmation. Implement any
missing behavior by editing the repository, or, if every acceptance criterion was
already satisfied, validate it and write the required structured result with concrete
criterion-by-criterion evidence. Never create an artificial change.

Do not only analyze, inspect files, or describe proposed changes.

Run any requested validation.

Before finishing, ensure:

git status --porcelain=v1 --untracked-files=all

agrees with the structured status: real task changes for changed, or a clean tree for
already_satisfied.

If implementation is genuinely impossible, write a failed structured result and stop
with a non-zero exit code.

Do not describe hypothetical or intended changes as completed work.

--------------------------------------------------
"""

SECRET_PATTERNS = (
    (re.compile(r"(?i)(authorization\s*:\s*)(?:bearer\s+)?\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)((?:CODEX|OPENAI)_API_KEY\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_-]+"), "[REDACTED]"),
    (re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://)[^/@\s]+@"), r"\1[REDACTED]@"),
    (
        re.compile(
            r"(?i)([?&](?:access[_-]?token|api[_-]?key|auth|password|secret|token)=)"
            r"[^&#\s]+"
        ),
        r"\1[REDACTED]",
    ),
    (re.compile(r"(?i)(session(?:[_ -]?id)?\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
)

FAILURES = (
    ("authentication failure", ("authentication", "invalid api key", "unauthorized", "401")),
    ("authorization failure", ("permission denied", "forbidden", "not authorized", "403")),
    ("deprecated model", ("deprecated model", "model is deprecated", "model has been deprecated")),
    (
        "model unavailable",
        (
            "model_not_found",
            "model not found",
            "model unavailable",
            "does not have access to model",
        ),
    ),
    ("rate limit", ("rate limit", "too many requests", "429")),
    ("TLS failure", ("tls handshake", "ssl error", "certificate verify", "unknown ca")),
    ("DNS failure", ("could not resolve", "name resolution", "dns error", "dns lookup")),
    ("timeout", ("timed out", "timeout", "etimedout")),
    (
        "network failure",
        ("connection refused", "econnrefused", "network is unreachable", "connection reset"),
    ),
    ("Codex internal exception", ("traceback", "internal exception", "internal error", "panic")),
)


def sanitize(value: str) -> str:
    """Return text with common credential and session representations removed."""
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def classify_failure(diagnostic: str) -> str:
    """Map a Codex diagnostic to a stable operational category."""
    lowered = diagnostic.lower()
    for category, indicators in FAILURES:
        if any(indicator in lowered for indicator in indicators):
            return category
    return "unknown failure"


def detect_capabilities(help_text: str) -> set[str]:
    """Discover long options advertised by the installed CLI."""
    return set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", help_text))


def _inspect(command: Sequence[str], env: Mapping[str, str]) -> str:
    result = subprocess.run(command, check=False, capture_output=True, env=dict(env), shell=False)
    output = result.stdout + result.stderr
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command, output=output)
    return output.decode("utf-8", errors="replace").strip()


def repository_has_changes(env: Mapping[str, str]) -> bool:
    """Return whether Git reports tracked or untracked repository changes."""
    result = subprocess.run(
        (
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            ".",
            f":(exclude){RESULT_FILENAME}",
        ),
        check=False,
        capture_output=True,
        env=dict(env),
        shell=False,
    )
    if result.returncode:
        raise subprocess.CalledProcessError(
            result.returncode, result.args, output=result.stdout, stderr=result.stderr
        )
    return bool(result.stdout)


def result_path(env: Mapping[str, str]) -> Path:
    """Return the structured result path inside the writable task worktree."""
    return Path.cwd() / RESULT_FILENAME


def clear_result(env: Mapping[str, str]) -> None:
    """Remove a result from an earlier attempt so it cannot authorize this one."""
    result_path(env).unlink(missing_ok=True)


def validate_completion_result(path: Path, *, repository_changed: bool) -> tuple[bool, str]:
    """Validate versioned or unambiguous legacy results and tree consistency."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "missing or invalid structured result"
    if not isinstance(value, dict) or value.get("status") not in SUPPORTED_RESULT_STATUSES:
        return False, "unsupported structured result status"
    status = str(value["status"])
    if status == "failed":
        return False, status
    objective, criteria = value.get("objective"), value.get("acceptance_criteria")
    files, unresolved = value.get("files_changed"), value.get("unresolved_items")
    if not isinstance(objective, str) or not objective.strip():
        return False, "missing objective"
    if not isinstance(criteria, list) or not criteria:
        return False, "missing acceptance-criterion evidence"
    version = value.get("schema_version")
    criterion_status = "passed" if version == "1" else "satisfied"
    if any(
        not isinstance(item, dict)
        or item.get("status") != criterion_status
        or not isinstance(item.get("criterion"), str)
        or not item["criterion"].strip()
        or not isinstance(item.get("evidence"), str)
        or not item["evidence"].strip()
        for item in criteria
    ):
        return False, "acceptance criteria are unresolved or lack evidence"
    validation = value.get("validation")
    if version == "1":
        if value.get("implementation_status") != "passed":
            return False, "implementation did not pass"
        if (
            not isinstance(validation, dict)
            or validation.get("task_scoped") != "passed"
            or validation.get("repository_baseline") not in {"passed", "has_pre_existing_failures"}
        ):
            return False, "validation did not pass"
        failures = value.get("pre_existing_failures")
        if not isinstance(failures, list):
            return False, "invalid pre-existing failure evidence"
        if validation["repository_baseline"] == "has_pre_existing_failures" and not failures:
            return False, "missing pre-existing failure evidence"
        postconditions = value.get("workflow_postconditions")
        if not isinstance(postconditions, list) or any(
            not isinstance(item, dict)
            or item.get("status") != "pending_workflow"
            or item.get("owner") != "github_actions"
            or not isinstance(item.get("condition"), str)
            or not item["condition"].strip()
            for item in postconditions
        ):
            return False, "invalid workflow postconditions"
    else:
        if (
            not isinstance(validation, list)
            or not validation
            or any(
                not isinstance(item, dict)
                or item.get("status") != "passed"
                or not isinstance(item.get("command"), str)
                or not item["command"].strip()
                for item in validation
            )
        ):
            return False, "validation did not pass"
    if unresolved != [] or not isinstance(files, list):
        return False, "unresolved items or invalid files_changed"
    if repository_changed:
        if status != "changed" or not files:
            return False, "changed repository requires a changed result with files"
    elif status != "already_satisfied" or files:
        return False, "clean repository requires an already_satisfied result"
    return True, status


def enrich_completion_result(path: Path) -> list[str]:
    """Add diagnostic artifact metadata and return the reported changed files."""
    if not path.exists():
        # Unit-test doubles may validate a synthetic result without materializing it.
        return []
    result = json.loads(path.read_text(encoding="utf-8"))
    result["log_artifact"] = "codex-trace.log"
    result["diff_artifact"] = "git-diff.patch"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    files = result.get("files_changed", [])
    return [str(file) for file in files] if isinstance(files, list) else []


def print_repository_diagnostics(env: Mapping[str, str]) -> None:
    """Print objective, non-payload Git diagnostics for a no-change outcome."""
    commands = (
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        ("git", "diff", "--stat"),
        ("git", "diff", "--name-only"),
        ("git", "diff", "--cached", "--name-only"),
    )
    for command in commands:
        print(f"$ {' '.join(command)}", flush=True)
        result = subprocess.run(
            command, check=False, capture_output=True, env=dict(env), shell=False
        )
        output = sanitize((result.stdout + result.stderr).decode("utf-8", errors="replace"))
        if output:
            print(output, end="" if output.endswith("\n") else "\n", flush=True)
        if result.returncode:
            raise subprocess.CalledProcessError(
                result.returncode, result.args, output=result.stdout, stderr=result.stderr
            )


def _stream(source: BinaryIO, capture: BinaryIO, collected: list[str]) -> None:
    """Capture one subprocess channel without flooding the user console."""
    while True:
        chunk = source.readline()
        if not chunk:
            break
        safe = sanitize(chunk.decode("utf-8", errors="replace"))
        encoded = safe.encode("utf-8")
        capture.write(encoded)
        capture.flush()
        collected.append(safe)


def _forward_stdin(destination: BinaryIO, prompt: bytes) -> None:
    """Forward the already-read prompt without decoding or transforming it."""
    try:
        destination.write(prompt)
        destination.flush()
    except BrokenPipeError:
        # Codex may exit before consuming input; its exit code is authoritative.
        pass
    finally:
        destination.close()


def _diagnostic_file(runner_temp: Path, channel: str) -> BinaryIO:
    runner_temp.mkdir(parents=True, exist_ok=True)
    return cast(
        BinaryIO,
        tempfile.NamedTemporaryFile(
            mode="w+b", prefix=f"codex-{channel}-", suffix=".log", dir=runner_temp, delete=False
        ),
    )


def _combined_diagnostic(stdout_text: str, stderr_text: str) -> str:
    """Combine channels for classification while avoiding identical duplicates."""
    if stdout_text and stderr_text:
        if stdout_text == stderr_text:
            return stdout_text
        return f"=== stdout ===\n{stdout_text}\n=== stderr ===\n{stderr_text}"
    return stdout_text or stderr_text


def _diagnostic_excerpt(diagnostic: str) -> str:
    """Return a bounded tail suitable for the Actions console."""
    if len(diagnostic) <= MAX_CONSOLE_DIAGNOSTIC_CHARS:
        return diagnostic
    omitted = len(diagnostic) - MAX_CONSOLE_DIAGNOSTIC_CHARS
    return (
        f"[... {omitted} earlier diagnostic characters omitted; full output is in "
        f"codex-trace.log ...]\n{diagnostic[-MAX_CONSOLE_DIAGNOSTIC_CHARS:]}"
    )


def execute(
    command: Sequence[str], prompt: bytes, env: Mapping[str, str], timeout: float
) -> tuple[int, str]:
    """Execute Codex, capturing a full trace and printing output only on failure."""
    runner_temp = Path(env.get("RUNNER_TEMP", tempfile.gettempdir()))
    trace_path = runner_temp / "codex-trace.log"
    runner_temp.mkdir(parents=True, exist_ok=True)
    with trace_path.open("ab") as trace:
        trace.write(b"=== Rendered prompt ===\n")
        trace.write(sanitize(prompt.decode("utf-8", errors="replace")).encode())
        trace.write(b"\n=== Codex output ===\n")
    stderr_parts: list[str] = []
    stdout_parts: list[str] = []
    with (
        _diagnostic_file(runner_temp, "stdout") as stdout_capture,
        _diagnostic_file(runner_temp, "stderr") as stderr_capture,
    ):
        try:
            process = subprocess.Popen(
                list(command),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(env),
                shell=False,
                start_new_session=True,
            )
        except OSError as error:
            diagnostic = sanitize(str(error))
            with trace_path.open("ab") as trace:
                trace.write(diagnostic.encode())
            LOGGER.error("::error title=Codex subprocess failure::%s", diagnostic)
            return 127, diagnostic

        assert process.stdin and process.stdout and process.stderr
        readers = (
            threading.Thread(target=_stream, args=(process.stdout, stdout_capture, stdout_parts)),
            threading.Thread(target=_stream, args=(process.stderr, stderr_capture, stderr_parts)),
        )
        writer = threading.Thread(target=_forward_stdin, args=(process.stdin, prompt))
        for reader in readers:
            reader.start()
        writer.start()
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Descendants can inherit the output pipes. Killing only the Codex
            # parent would leave the reader threads blocked until those
            # descendants exit, so terminate the isolated process group.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                # The group may have exited between wait() and killpg().
                pass
            process.wait()
            return_code = TIMEOUT_EXIT
            stderr_parts.append(f"Codex execution timed out after {timeout:g} seconds.")
        finally:
            writer.join()
            for reader in readers:
                reader.join()
            process.stdout.close()
            process.stderr.close()

    stdout_text = "".join(stdout_parts)
    stderr_text = "".join(stderr_parts)
    with trace_path.open("ab") as trace:
        trace.write(b"=== stdout ===\n")
        trace.write(stdout_text.encode())
        trace.write(b"\n=== stderr ===\n")
        trace.write(stderr_text.encode())
    diagnostic = _combined_diagnostic(stdout_text, stderr_text)
    if return_code and diagnostic:
        excerpt = _diagnostic_excerpt(diagnostic)
        print(excerpt, end="" if excerpt.endswith("\n") else "\n", file=sys.stderr)
    return return_code, diagnostic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("CODEX_TIMEOUT_SECONDS", DEFAULT_TIMEOUT)),
        help="maximum execution time in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--working-directory",
        type=Path,
        help="repository worktree in which Codex and Git commands must run",
    )
    parser.add_argument(
        "--codex-executable",
        default=os.environ.get("CODEX_EXECUTABLE", "codex"),
        help="Codex executable path or name (default: CODEX_EXECUTABLE or codex)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        LOGGER.error("::error title=Invalid Codex timeout::Timeout must be positive.")
        return EX_USAGE
    if args.working_directory is not None:
        try:
            os.chdir(args.working_directory)
        except OSError as error:
            LOGGER.error("::error title=Invalid task worktree::%s", sanitize(str(error)))
            return EX_USAGE

    executable = args.codex_executable
    if not executable or any(character.isspace() for character in executable):
        LOGGER.error("::error title=Invalid Codex executable::Expected one path or name.")
        return EX_USAGE
    api_key = os.environ.get("CODEX_API_KEY")
    if executable == "codex" and not api_key:
        LOGGER.error("::error title=Codex authentication::CODEX_API_KEY is required.")
        return EX_CONFIG

    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key
    try:
        version = _inspect((executable, "--version"), env)
        help_text = _inspect((executable, "exec", "--help"), env)
    except FileNotFoundError:
        LOGGER.error("::error title=Codex unavailable::codex was not found in PATH.")
        return 127
    except (OSError, subprocess.CalledProcessError) as error:
        LOGGER.error("::error title=Codex inspection failed::%s", sanitize(str(error)))
        return getattr(error, "returncode", 1)

    capabilities = detect_capabilities(help_text)
    print("Stage: Codex preflight", flush=True)
    print(f"Codex version: {sanitize(version)}", flush=True)
    print(f"Codex model: {sanitize(os.environ.get('CODEX_MODEL', 'default'))}", flush=True)
    print(f"Working directory: {Path.cwd()}", flush=True)

    if "--sandbox" not in capabilities:
        LOGGER.error(
            "::error title=Unsupported Codex CLI::The required --sandbox "
            "workspace-write capability is unavailable."
        )
        return EX_USAGE

    command = [executable, "exec", "--sandbox", "workspace-write"]
    compatibility: list[str] = []
    if "--ask-for-approval" in capabilities:
        command.extend(("--ask-for-approval", "never"))
    else:
        compatibility.append("approval option unavailable")
    if "--skip-git-repo-check" in capabilities:
        command.append("--skip-git-repo-check")
    else:
        compatibility.append("Git repository check managed by installed CLI")
    if "--full-auto" in capabilities:
        command.append("--full-auto")
    if "--config" in capabilities:
        effort = os.environ.get("CODEX_REASONING_EFFORT", "high")
        if effort not in {"minimal", "low", "medium", "high"}:
            LOGGER.error(
                "::error title=Invalid reasoning effort::Unsupported value %s.", sanitize(effort)
            )
            return EX_CONFIG
        command.extend(("--config", f'model_reasoning_effort="{effort}"'))
    else:
        compatibility.append("reasoning configuration unavailable")
    model = os.environ.get("CODEX_MODEL")
    if model:
        command.extend(("--model", model))
    command.append("-")
    mode = "; ".join(compatibility) if compatibility else "all wrapper flags supported"
    LOGGER.debug("Compatibility mode: %s", mode)

    prompt = sys.stdin.buffer.read()
    # Treat --timeout as one shared execution budget.  In particular, a no-op
    # first attempt must not give its retry another full timeout and overrun the
    # enclosing workflow deadline.
    deadline = time.monotonic() + args.timeout
    clear_result(env)
    return_code, diagnostic = execute(command, prompt, env, args.timeout)
    if return_code:
        category = "timeout" if return_code == TIMEOUT_EXIT else classify_failure(diagnostic)
        LOGGER.error(
            "::error title=Codex %s::category=%s; exit_code=%d; "
            "see the bounded diagnostic above and codex-trace.log artifact.",
            category,
            category,
            return_code,
        )
        return return_code

    try:
        changed = repository_has_changes(env)
    except (OSError, subprocess.CalledProcessError) as error:
        LOGGER.error("::error title=Git status failed::%s", sanitize(str(error)))
        return getattr(error, "returncode", 1)

    valid, outcome = validate_completion_result(result_path(env), repository_changed=changed)
    if valid:
        files = enrich_completion_result(result_path(env))
        print("Files modified: " + (", ".join(files) if files else "none"), flush=True)
        LOGGER.info("::notice::Codex terminal outcome: %s", outcome)
        return 0
    if changed:
        LOGGER.error("::error title=Invalid Codex result::%s", outcome)
        return 1

    LOGGER.info("::notice::Codex produced unexplained no changes (%s); retrying once.", outcome)
    retry_timeout = deadline - time.monotonic()
    if retry_timeout <= 0:
        LOGGER.error(
            "::error title=Codex timeout::Codex execution budget was exhausted before retry."
        )
        return TIMEOUT_EXIT
    clear_result(env)
    return_code, diagnostic = execute(command, prompt + RETRY_INSTRUCTION, env, retry_timeout)
    if return_code:
        category = "timeout" if return_code == TIMEOUT_EXIT else classify_failure(diagnostic)
        LOGGER.error(
            "::error title=Codex %s::Codex CLI failed with exit code %d.", category, return_code
        )
        return return_code

    try:
        changed = repository_has_changes(env)
    except (OSError, subprocess.CalledProcessError) as error:
        LOGGER.error("::error title=Git status failed::%s", sanitize(str(error)))
        return getattr(error, "returncode", 1)

    valid, outcome = validate_completion_result(result_path(env), repository_changed=changed)
    if valid:
        files = enrich_completion_result(result_path(env))
        print("Files modified: " + (", ".join(files) if files else "none"), flush=True)
        LOGGER.info("::notice::Codex terminal outcome: %s", outcome)
        return 0
    if changed:
        LOGGER.error("::error title=Invalid Codex result::%s", outcome)
        return 1
    LOGGER.error(
        "::error title=Codex produced no changes::Retry produced unexplained "
        "no repository changes (%s).",
        outcome,
    )
    try:
        print_repository_diagnostics(env)
    except (OSError, subprocess.CalledProcessError) as error:
        LOGGER.error("::error title=Git diagnostics failed::%s", sanitize(str(error)))
    return NO_CHANGES_EXIT


if __name__ == "__main__":
    sys.exit(main())
