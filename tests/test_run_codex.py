"""Unit tests for the portable Codex runtime wrapper."""

import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts import run_codex


HELP = "Usage: codex exec --sandbox MODE --skip-git-repo-check --ask-for-approval"


class FakeProcess:
    def __init__(self, stdout=b"", stderr=b"", returncode=0, timeout=False):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.timeout = timeout
        self.killed = False

    def wait(self, timeout=None):
        if self.timeout and not self.killed:
            raise subprocess.TimeoutExpired("codex", timeout)
        return self.returncode

    def kill(self):
        self.killed = True


class RunCodexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = {"CODEX_API_KEY": "test-key", "RUNNER_TEMP": self.temp.name}

    def run_main(self, extra_env=None):
        env = dict(self.env)
        env.update(extra_env or {})
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(b"prompt\x00exact\n")
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(sys, "stdin", stdin), \
                mock.patch.object(run_codex, "_inspect", side_effect=["1.2.3", HELP]), \
                mock.patch.object(run_codex, "execute", return_value=(0, "")) as execute:
            status = run_codex.main([])
        return status, execute

    def test_missing_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(run_codex.EX_CONFIG, run_codex.main([]))

    def test_optional_model_is_omitted(self):
        status, execute = self.run_main()
        self.assertEqual(0, status)
        self.assertNotIn("--model", execute.call_args.args[0])

    def test_model_override_is_passed(self):
        _, execute = self.run_main({"CODEX_MODEL": "optional-model"})
        command = execute.call_args.args[0]
        self.assertEqual("optional-model", command[command.index("--model") + 1])

    def test_capability_detection_includes_future_flags(self):
        capabilities = run_codex.detect_capabilities(
            "--sandbox <MODE> --future-safe-flag, --skip-git-repo-check"
        )
        self.assertEqual(
            {"--sandbox", "--future-safe-flag", "--skip-git-repo-check"},
            capabilities,
        )

    def test_stdin_forwarding_is_exact(self):
        _, execute = self.run_main()
        self.assertEqual(b"prompt\x00exact\n", execute.call_args.args[1])

    def test_stdout_streaming_and_diagnostic_capture(self):
        process = FakeProcess(stdout=b"first\nsecond\n")
        output = io.StringIO()
        with mock.patch.object(subprocess, "Popen", return_value=process), \
                mock.patch.object(sys, "stdout", output):
            status, _ = run_codex.execute(["codex"], b"input", self.env, 10)
        self.assertEqual(0, status)
        self.assertEqual("first\nsecond\n", output.getvalue())
        logs = list(Path(self.temp.name).glob("codex-stdout-*.log"))
        self.assertEqual(b"first\nsecond\n", logs[0].read_bytes())

    def test_stderr_is_sanitized(self):
        process = FakeProcess(stderr=b"Authorization: Bearer secret\nsk-abcdefghijk\n")
        output = io.StringIO()
        with mock.patch.object(subprocess, "Popen", return_value=process), \
                mock.patch.object(sys, "stderr", output):
            _, diagnostic = run_codex.execute(["codex"], b"", self.env, 10)
        self.assertNotIn("secret", diagnostic)
        self.assertNotIn("sk-abcdefghijk", output.getvalue())
        self.assertIn("[REDACTED]", diagnostic)

    def test_exit_code_preservation(self):
        process = FakeProcess(stderr=b"bad\n", returncode=23)
        with mock.patch.object(subprocess, "Popen", return_value=process):
            status, _ = run_codex.execute(["codex"], b"", self.env, 10)
        self.assertEqual(23, status)

    def test_timeout(self):
        process = FakeProcess(timeout=True)
        with mock.patch.object(subprocess, "Popen", return_value=process):
            status, diagnostic = run_codex.execute(["codex"], b"", self.env, 0.01)
        self.assertEqual(124, status)
        self.assertTrue(process.killed)
        self.assertIn("timed out", diagnostic)

    def test_subprocess_failure(self):
        with mock.patch.object(subprocess, "Popen", side_effect=FileNotFoundError("missing")):
            status, diagnostic = run_codex.execute(["codex"], b"", self.env, 10)
        self.assertEqual(127, status)
        self.assertIn("missing", diagnostic)

    def test_model_deprecation_detection(self):
        self.assertEqual("deprecated model", run_codex.classify_failure(
            "The requested model has been deprecated"))

    def test_authentication_detection(self):
        self.assertEqual("authentication failure", run_codex.classify_failure(
            "401 invalid API key"))

    def test_network_detection(self):
        self.assertEqual("network failure", run_codex.classify_failure(
            "connection refused"))

    def test_wrapper_returns_original_exit_code(self):
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(b"prompt")
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch.object(sys, "stdin", stdin), \
                mock.patch.object(run_codex, "_inspect", side_effect=["1", HELP]), \
                mock.patch.object(run_codex, "execute", return_value=(37, "unknown")):
            self.assertEqual(37, run_codex.main([]))


if __name__ == "__main__":
    unittest.main()
