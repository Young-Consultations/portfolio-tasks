"""Unit tests for the portable Codex runtime wrapper."""

import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from portfolio_tasks import run_codex

HELP = "Usage: codex exec --sandbox MODE --skip-git-repo-check --ask-for-approval"
FULL_AUTO_HELP = HELP + " --full-auto"


class FakeProcess:
    def __init__(self, stdout=b"", stderr=b"", returncode=0, timeout=False):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.timeout = timeout
        self.pid = 12345
        self.wait_calls = 0

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.timeout and self.wait_calls == 1:
            raise subprocess.TimeoutExpired("codex", timeout)
        return self.returncode

class RunCodexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = {"CODEX_API_KEY": "test-key", "RUNNER_TEMP": self.temp.name}

    def run_main(self, extra_env=None, *, executions=((0, ""),), changes=(True,),
                 help_text=HELP):
        env = dict(self.env)
        env.update(extra_env or {})
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(b"prompt\x00exact\n")
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(sys, "stdin", stdin), \
                mock.patch.object(run_codex, "_inspect", side_effect=["1.2.3", help_text]), \
                mock.patch.object(run_codex, "execute", side_effect=executions) as execute, \
                mock.patch.object(run_codex, "repository_has_changes",
                                  side_effect=changes) as git_status:
            status = run_codex.main([])
        return status, execute, git_status

    def test_missing_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(run_codex.EX_CONFIG, run_codex.main([]))

    def test_optional_model_is_omitted(self):
        status, execute, _ = self.run_main()
        self.assertEqual(0, status)
        self.assertNotIn("--model", execute.call_args.args[0])

    def test_model_override_is_passed(self):
        _, execute, _ = self.run_main({"CODEX_MODEL": "optional-model"})
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
        _, execute, _ = self.run_main()
        self.assertEqual(b"prompt\x00exact\n", execute.call_args.args[1])

    def test_successful_edit_does_not_retry(self):
        status, execute, git_status = self.run_main()
        self.assertEqual(0, status)
        execute.assert_called_once()
        git_status.assert_called_once()

    def test_noop_retries_successfully_once(self):
        status, execute, git_status = self.run_main(
            executions=((0, ""), (0, "")), changes=(False, True)
        )
        self.assertEqual(0, status)
        self.assertEqual(2, execute.call_count)
        self.assertEqual(2, git_status.call_count)
        self.assertEqual(execute.call_args_list[0].args[0],
                         execute.call_args_list[1].args[0])
        self.assertEqual(execute.call_args_list[0].args[2],
                         execute.call_args_list[1].args[2])
        self.assertLessEqual(execute.call_args_list[1].args[3],
                             execute.call_args_list[0].args[3])
        retry_prompt = execute.call_args_list[1].args[1]
        self.assertTrue(retry_prompt.startswith(b"prompt\x00exact\n"))
        self.assertIn(run_codex.RETRY_INSTRUCTION, retry_prompt)

    def test_retry_uses_remaining_shared_timeout(self):
        with mock.patch.object(run_codex.time, "monotonic",
                               side_effect=[100.0, 125.0]):
            status, execute, _ = self.run_main(
                executions=((0, ""), (0, "")), changes=(False, True)
            )

        self.assertEqual(0, status)
        self.assertEqual(2400.0, execute.call_args_list[0].args[3])
        self.assertEqual(2375.0, execute.call_args_list[1].args[3])

    def test_exhausted_budget_does_not_start_retry(self):
        with mock.patch.object(run_codex.time, "monotonic",
                               side_effect=[100.0, 2500.0]):
            status, execute, git_status = self.run_main(changes=(False,))

        self.assertEqual(run_codex.TIMEOUT_EXIT, status)
        execute.assert_called_once()
        git_status.assert_called_once()

    def test_noop_twice_fails_without_infinite_retry(self):
        status, execute, git_status = self.run_main(
            executions=((0, ""), (0, "")), changes=(False, False)
        )
        self.assertNotEqual(0, status)
        self.assertEqual(2, execute.call_count)
        self.assertEqual(2, git_status.call_count)

    def test_nonzero_codex_exit_is_not_retried(self):
        status, execute, git_status = self.run_main(executions=((23, "bad"),))
        self.assertEqual(23, status)
        execute.assert_called_once()
        git_status.assert_not_called()

    def test_retry_nonzero_exit_is_preserved(self):
        status, execute, git_status = self.run_main(
            executions=((0, ""), (17, "blocked")), changes=(False,)
        )
        self.assertEqual(17, status)
        self.assertEqual(2, execute.call_count)
        git_status.assert_called_once()

    def test_full_auto_is_added_only_when_supported(self):
        _, supported, _ = self.run_main(help_text=FULL_AUTO_HELP)
        _, unsupported, _ = self.run_main(help_text=HELP)
        self.assertIn("--full-auto", supported.call_args.args[0])
        self.assertNotIn("--full-auto", unsupported.call_args.args[0])

    def test_git_status_detection(self):
        clean = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        dirty = subprocess.CompletedProcess([], 0, stdout=b"?? new.py\n", stderr=b"")
        with mock.patch.object(subprocess, "run", side_effect=[clean, dirty]) as run:
            self.assertFalse(run_codex.repository_has_changes(self.env))
            self.assertTrue(run_codex.repository_has_changes(self.env))
        expected = ("git", "status", "--porcelain=v1", "--untracked-files=all")
        self.assertEqual(expected, run.call_args_list[0].args[0])

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
        with mock.patch.object(subprocess, "Popen", return_value=process) as popen, \
                mock.patch.object(os, "killpg") as killpg:
            status, diagnostic = run_codex.execute(["codex"], b"", self.env, 0.01)
        self.assertEqual(124, status)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        killpg.assert_called_once_with(process.pid, run_codex.signal.SIGKILL)
        self.assertIn("timed out", diagnostic)

    @unittest.skipUnless(hasattr(os, "killpg"), "requires POSIX process groups")
    def test_timeout_kills_descendants_holding_output_pipes(self):
        command = [
            sys.executable,
            "-c",
            "import subprocess, time; "
            "subprocess.Popen(['sleep', '30']); time.sleep(30)",
        ]
        started = time.monotonic()
        status, diagnostic = run_codex.execute(command, b"", self.env, 0.1)
        elapsed = time.monotonic() - started

        self.assertEqual(124, status)
        self.assertLess(elapsed, 2)
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
                mock.patch.object(run_codex, "execute", return_value=(37, "unknown")), \
                mock.patch.object(run_codex, "repository_has_changes") as git_status:
            self.assertEqual(37, run_codex.main([]))
        git_status.assert_not_called()


if __name__ == "__main__":
    unittest.main()
