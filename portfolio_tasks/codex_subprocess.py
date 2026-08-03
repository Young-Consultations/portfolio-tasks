"""Small trusted subprocess helpers for Codex executor orchestration."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence


def run_checked(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    stdout: int | None = None,
) -> None:
    """Run a command with ``shell=False`` and raise on non-zero exits."""
    subprocess.run(
        tuple(command),
        check=True,
        env=dict(env) if env is not None else None,
        stdout=stdout,
        shell=False,
    )
