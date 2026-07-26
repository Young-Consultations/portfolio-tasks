#!/usr/bin/env python3
"""Secure, version-adaptive runtime wrapper for ``codex exec``."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
from typing import BinaryIO, Mapping, Sequence, TextIO


EX_CONFIG = 78
EX_USAGE = 64
TIMEOUT_EXIT = 124
DEFAULT_TIMEOUT = 2400.0
LOGGER = logging.getLogger("run-codex")

SECRET_PATTERNS = (
    (re.compile(r"(?i)(authorization\s*:\s*)(?:bearer\s+)?\S+"),
     r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)((?:CODEX|OPENAI)_API_KEY\s*[:=]\s*)[^\s,;]+"),
     r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"),
     r"\1[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_-]+"), "[REDACTED]"),
    (re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://)[^/@\s]+@"),
     r"\1[REDACTED]@"),
    (re.compile(r"(?i)(session(?:[_ -]?id)?\s*[:=]\s*)[^\s,;]+"),
     r"\1[REDACTED]"),
)

FAILURES = (
    ("authentication failure", ("authentication", "invalid api key", "unauthorized", "401")),
    ("authorization failure", ("permission denied", "forbidden", "not authorized", "403")),
    ("deprecated model", ("deprecated model", "model is deprecated", "model has been deprecated")),
    ("model unavailable", ("model_not_found", "model not found", "model unavailable", "does not have access to model")),
    ("rate limit", ("rate limit", "too many requests", "429")),
    ("TLS failure", ("tls handshake", "ssl error", "certificate verify", "unknown ca")),
    ("DNS failure", ("could not resolve", "name resolution", "dns error", "dns lookup")),
    ("timeout", ("timed out", "timeout", "etimedout")),
    ("network failure", ("connection refused", "econnrefused", "network is unreachable", "connection reset")),
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
    result = subprocess.run(
        command, check=False, capture_output=True, env=dict(env), shell=False
    )
    output = result.stdout + result.stderr
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command, output=output)
    return output.decode("utf-8", errors="replace").strip()


def _stream(
    source: BinaryIO, destination: TextIO, capture: BinaryIO, collected: list[str]
) -> None:
    """Stream one subprocess channel while redacting and capturing it."""
    while True:
        chunk = source.readline()
        if not chunk:
            break
        safe = sanitize(chunk.decode("utf-8", errors="replace"))
        encoded = safe.encode("utf-8")
        capture.write(encoded)
        capture.flush()
        collected.append(safe)
        destination.write(safe)
        destination.flush()


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
    return tempfile.NamedTemporaryFile(
        mode="w+b", prefix=f"codex-{channel}-", suffix=".log",
        dir=runner_temp, delete=False
    )


def execute(
    command: Sequence[str], prompt: bytes, env: Mapping[str, str], timeout: float
) -> tuple[int, str]:
    """Execute Codex, forwarding input and streaming sanitized output."""
    runner_temp = Path(env.get("RUNNER_TEMP", tempfile.gettempdir()))
    stderr_parts: list[str] = []
    stdout_parts: list[str] = []
    with _diagnostic_file(runner_temp, "stdout") as stdout_capture, \
            _diagnostic_file(runner_temp, "stderr") as stderr_capture:
        try:
            process = subprocess.Popen(
                list(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env=dict(env), shell=False
            )
        except OSError as error:
            diagnostic = sanitize(str(error))
            LOGGER.error("::error title=Codex subprocess failure::%s", diagnostic)
            return 127, diagnostic

        assert process.stdin and process.stdout and process.stderr
        readers = (
            threading.Thread(target=_stream, args=(process.stdout, sys.stdout,
                                                   stdout_capture, stdout_parts)),
            threading.Thread(target=_stream, args=(process.stderr, sys.stderr,
                                                   stderr_capture, stderr_parts)),
        )
        writer = threading.Thread(target=_forward_stdin,
                                  args=(process.stdin, prompt))
        for reader in readers:
            reader.start()
        writer.start()
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return_code = TIMEOUT_EXIT
            stderr_parts.append(f"Codex execution timed out after {timeout:g} seconds.")
        finally:
            writer.join()
            for reader in readers:
                reader.join()

    return return_code, "".join(stderr_parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout", type=float,
        default=float(os.environ.get("CODEX_TIMEOUT_SECONDS", DEFAULT_TIMEOUT)),
        help="maximum execution time in seconds (default: %(default)s)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        LOGGER.error("::error title=Invalid Codex timeout::Timeout must be positive.")
        return EX_USAGE

    api_key = os.environ.get("CODEX_API_KEY")
    if not api_key:
        LOGGER.error("::error title=Codex authentication::CODEX_API_KEY is required.")
        return EX_CONFIG

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = api_key
    try:
        version = _inspect(("codex", "--version"), env)
        help_text = _inspect(("codex", "exec", "--help"), env)
    except FileNotFoundError:
        LOGGER.error("::error title=Codex unavailable::codex was not found in PATH.")
        return 127
    except (OSError, subprocess.CalledProcessError) as error:
        LOGGER.error("::error title=Codex inspection failed::%s", sanitize(str(error)))
        return getattr(error, "returncode", 1)

    capabilities = detect_capabilities(help_text)
    print(f"Codex version: {sanitize(version)}", flush=True)
    print("Detected capabilities: " +
          (" ".join(sorted(capabilities)) if capabilities else "none"), flush=True)

    if "--sandbox" not in capabilities:
        LOGGER.error("::error title=Unsupported Codex CLI::The required --sandbox "
                     "workspace-write capability is unavailable.")
        return EX_USAGE

    command = ["codex", "exec", "--sandbox", "workspace-write"]
    compatibility: list[str] = []
    if "--ask-for-approval" in capabilities:
        command.extend(("--ask-for-approval", "never"))
    else:
        compatibility.append("approval option unavailable")
    if "--skip-git-repo-check" in capabilities:
        command.append("--skip-git-repo-check")
    else:
        compatibility.append("Git repository check managed by installed CLI")
    model = os.environ.get("CODEX_MODEL")
    if model:
        command.extend(("--model", model))
    command.append("-")
    mode = "; ".join(compatibility) if compatibility else "all wrapper flags supported"
    print(f"Compatibility mode: {mode}", flush=True)

    prompt = sys.stdin.buffer.read()
    return_code, diagnostic = execute(command, prompt, env, args.timeout)
    if return_code:
        category = "timeout" if return_code == TIMEOUT_EXIT else classify_failure(diagnostic)
        LOGGER.error("::error title=Codex %s::Codex CLI failed with exit code %d.",
                     category, return_code)
    return return_code


if __name__ == "__main__":
    sys.exit(main())
