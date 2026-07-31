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

HELP = "Usage: codex exec --sandbox MODE --skip-git-repo-check --ask-for-approval --config"
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

    def run_main(
        self,
        extra_env=None,
        *,
        executions=((0, ""),),
        changes=(True,),
        help_text=HELP,
        results=((True, "changed"),),
    ):
        env = dict(self.env)
        env.update(extra_env or {})
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(b"prompt\x00exact\n")
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(sys, "stdin", stdin),
            mock.patch.object(run_codex, "_inspect", side_effect=["1.2.3", help_text]),
            mock.patch.object(run_codex, "execute", side_effect=executions) as execute,
            mock.patch.object(
                run_codex, "repository_has_changes", side_effect=changes
            ) as git_status,
            mock.patch.object(run_codex, "validate_completion_result", side_effect=results),
        ):
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

    def test_supported_reasoning_configuration_is_passed(self):
        _, execute, _ = self.run_main()
        command = execute.call_args.args[0]
        self.assertEqual('model_reasoning_effort="high"', command[command.index("--config") + 1])

    def test_reasoning_configuration_is_omitted_when_cli_lacks_capability(self):
        _, execute, _ = self.run_main(help_text=HELP.replace(" --config", ""))
        self.assertNotIn("--config", execute.call_args.args[0])

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
            executions=((0, ""), (0, "")),
            changes=(False, True),
            results=((False, "missing"), (True, "changed")),
        )
        self.assertEqual(0, status)
        self.assertEqual(2, execute.call_count)
        self.assertEqual(2, git_status.call_count)
        self.assertEqual(execute.call_args_list[0].args[0], execute.call_args_list[1].args[0])
        self.assertEqual(execute.call_args_list[0].args[2], execute.call_args_list[1].args[2])
        self.assertLessEqual(execute.call_args_list[1].args[3], execute.call_args_list[0].args[3])
        retry_prompt = execute.call_args_list[1].args[1]
        self.assertTrue(retry_prompt.startswith(b"prompt\x00exact\n"))
        self.assertIn(run_codex.RETRY_INSTRUCTION, retry_prompt)

    def test_retry_uses_remaining_shared_timeout(self):
        with mock.patch.object(run_codex.time, "monotonic", side_effect=[100.0, 125.0]):
            status, execute, _ = self.run_main(
                executions=((0, ""), (0, "")),
                changes=(False, True),
                results=((False, "missing"), (True, "changed")),
            )

        self.assertEqual(0, status)
        self.assertEqual(2400.0, execute.call_args_list[0].args[3])
        self.assertEqual(2375.0, execute.call_args_list[1].args[3])

    def test_exhausted_budget_does_not_start_retry(self):
        with mock.patch.object(run_codex.time, "monotonic", side_effect=[100.0, 2500.0]):
            status, execute, git_status = self.run_main(
                changes=(False,), results=((False, "missing"),)
            )

        self.assertEqual(run_codex.TIMEOUT_EXIT, status)
        execute.assert_called_once()
        git_status.assert_called_once()

    def test_noop_twice_returns_distinct_outcome_without_infinite_retry(self):
        with mock.patch.object(run_codex, "print_repository_diagnostics") as diagnostics:
            status, execute, git_status = self.run_main(
                executions=((0, "implemented"), (0, "implemented")),
                changes=(False, False),
                results=((False, "missing"), (False, "missing")),
            )
        self.assertEqual(run_codex.NO_CHANGES_EXIT, status)
        self.assertEqual(2, execute.call_count)
        self.assertEqual(2, git_status.call_count)
        diagnostics.assert_called_once()

    def test_permission_request_with_no_changes_is_rejected(self):
        status, execute, _ = self.run_main(
            executions=((0, "If you want, I'll proceed now."), (0, "May I continue?")),
            changes=(False, False),
            results=((False, "missing"), (False, "missing")),
        )
        self.assertEqual(run_codex.NO_CHANGES_EXIT, status)
        self.assertEqual(2, execute.call_count)

    def test_no_change_diagnostics_use_objective_git_commands(self):
        completed = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        with mock.patch.object(subprocess, "run", return_value=completed) as run:
            run_codex.print_repository_diagnostics(self.env)

        self.assertEqual(
            [
                ("git", "status", "--porcelain=v1", "--untracked-files=all"),
                ("git", "diff", "--stat"),
                ("git", "diff", "--name-only"),
                ("git", "diff", "--cached", "--name-only"),
            ],
            [call.args[0] for call in run.call_args_list],
        )

    def test_retry_prompt_requires_changes_and_honest_failure(self):
        instruction = run_codex.RETRY_INSTRUCTION.decode()
        self.assertIn("autonomous execution", instruction)
        self.assertIn("structured already_satisfied", instruction)
        self.assertIn("non-zero exit code", instruction)
        self.assertIn("hypothetical or intended changes", instruction)

    def test_nonzero_codex_exit_is_not_retried(self):
        status, execute, git_status = self.run_main(executions=((23, "bad"),))
        self.assertEqual(23, status)
        execute.assert_called_once()
        git_status.assert_not_called()

    def test_retry_nonzero_exit_is_preserved(self):
        status, execute, git_status = self.run_main(
            executions=((0, ""), (17, "blocked")), changes=(False,), results=((False, "missing"),)
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
        self.assertEqual(
            expected + ("--", ".", ":(exclude)codex-result.json"), run.call_args_list[0].args[0]
        )

    def test_stdout_is_captured_without_console_noise(self):
        process = FakeProcess(stdout=b"first\nsecond\n")
        output = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stdout", output),
        ):
            status, _ = run_codex.execute(["codex"], b"input", self.env, 10)
        self.assertEqual(0, status)
        self.assertEqual("", output.getvalue())
        trace = Path(self.temp.name) / "codex-trace.log"
        self.assertIn(b"first\nsecond\n", trace.read_bytes())
        self.assertIn(b"Rendered prompt", trace.read_bytes())

    def test_stdout_only_failure_is_emitted_and_returned(self):
        process = FakeProcess(stdout=b"model_not_found: unavailable\n", returncode=1)
        output = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stderr", output),
        ):
            status, diagnostic = run_codex.execute(["codex"], b"task", self.env, 10)
        self.assertEqual(1, status)
        self.assertEqual("model_not_found: unavailable\n", diagnostic)
        self.assertEqual(diagnostic, output.getvalue())
        self.assertEqual("model unavailable", run_codex.classify_failure(diagnostic))

    def test_stderr_only_failure_is_emitted_and_returned(self):
        process = FakeProcess(stderr=b"401 invalid API key: sk-test-secret\n", returncode=1)
        output = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stderr", output),
        ):
            status, diagnostic = run_codex.execute(["codex"], b"task", self.env, 10)
        self.assertEqual(1, status)
        self.assertIn("401 invalid API key", diagnostic)
        self.assertNotIn("sk-test-secret", diagnostic)
        self.assertEqual(diagnostic, output.getvalue())
        self.assertEqual("authentication failure", run_codex.classify_failure(diagnostic))

    def test_both_failure_channels_are_combined_without_duplication(self):
        process = FakeProcess(stdout=b"request failed\n", stderr=b"403 forbidden\n", returncode=1)
        output = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stderr", output),
        ):
            _, diagnostic = run_codex.execute(["codex"], b"task", self.env, 10)
        self.assertIn("=== stdout ===\nrequest failed", diagnostic)
        self.assertIn("=== stderr ===\n403 forbidden", diagnostic)
        self.assertEqual("authorization failure", run_codex.classify_failure(diagnostic))
        self.assertEqual(1, output.getvalue().count("request failed"))

    def test_identical_failure_channels_are_not_duplicated(self):
        process = FakeProcess(stdout=b"internal error\n", stderr=b"internal error\n", returncode=1)
        with mock.patch.object(subprocess, "Popen", return_value=process):
            _, diagnostic = run_codex.execute(["codex"], b"", self.env, 10)
        self.assertEqual("internal error\n", diagnostic)

    def test_failure_diagnostics_and_trace_are_sanitized(self):
        secret = "sk-abcdefghijk"
        output_text = (
            f"Authorization: Bearer top-secret\n{secret}\n"
            "https://user:password@example.test/path?access_token=url-secret\n"
            "session_id=session-secret\n"
        )
        process = FakeProcess(stdout=output_text.encode(), returncode=1)
        console = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stderr", console),
        ):
            _, diagnostic = run_codex.execute(["codex"], f"prompt {secret}".encode(), self.env, 10)
        trace = (Path(self.temp.name) / "codex-trace.log").read_text()
        for unsafe in (secret, "top-secret", "user:password", "url-secret", "session-secret"):
            self.assertNotIn(unsafe, console.getvalue())
            self.assertNotIn(unsafe, diagnostic)
            self.assertNotIn(unsafe, trace)
        self.assertIn("[REDACTED]", trace)

    def test_large_failure_diagnostic_console_is_bounded_but_trace_is_complete(self):
        large = ("early-marker\n" + "x" * 20_000 + "\ntail-marker\n").encode()
        process = FakeProcess(stdout=large, returncode=1)
        console = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stderr", console),
        ):
            _, diagnostic = run_codex.execute(["codex"], b"", self.env, 10)
        self.assertLessEqual(len(console.getvalue()), run_codex.MAX_CONSOLE_DIAGNOSTIC_CHARS + 200)
        self.assertNotIn("early-marker", console.getvalue())
        self.assertIn("tail-marker", console.getvalue())
        self.assertIn("early-marker", diagnostic)
        self.assertIn("early-marker", (Path(self.temp.name) / "codex-trace.log").read_text())

    def test_stderr_is_sanitized(self):
        process = FakeProcess(stderr=b"Authorization: Bearer secret\nsk-abcdefghijk\n")
        output = io.StringIO()
        with (
            mock.patch.object(subprocess, "Popen", return_value=process),
            mock.patch.object(sys, "stderr", output),
        ):
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
        with (
            mock.patch.object(subprocess, "Popen", return_value=process) as popen,
            mock.patch.object(os, "killpg") as killpg,
        ):
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
            ("import subprocess, time; subprocess.Popen(['sleep', '30']); time.sleep(30)"),
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
        self.assertEqual(
            "deprecated model",
            run_codex.classify_failure("The requested model has been deprecated"),
        )

    def test_authentication_detection(self):
        self.assertEqual(
            "authentication failure", run_codex.classify_failure("401 invalid API key")
        )

    def test_authorization_detection(self):
        self.assertEqual("authorization failure", run_codex.classify_failure("403 forbidden"))

    def test_network_detection(self):
        self.assertEqual("network failure", run_codex.classify_failure("connection refused"))

    def test_wrapper_returns_original_exit_code(self):
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(b"prompt")
        with (
            mock.patch.dict(os.environ, self.env, clear=True),
            mock.patch.object(sys, "stdin", stdin),
            mock.patch.object(run_codex, "_inspect", side_effect=["1", HELP]),
            mock.patch.object(run_codex, "execute", return_value=(37, "unknown")),
            mock.patch.object(run_codex, "repository_has_changes") as git_status,
        ):
            self.assertEqual(37, run_codex.main([]))
        git_status.assert_not_called()

    def test_valid_already_satisfied_result_accepts_clean_tree(self):
        path = Path(self.temp.name) / run_codex.RESULT_FILENAME
        path.write_text(self._result("already_satisfied", []), encoding="utf-8")
        self.assertEqual(
            (True, "already_satisfied"),
            run_codex.validate_completion_result(path, repository_changed=False),
        )

    def test_result_path_is_inside_current_worktree(self):
        with mock.patch.object(Path, "cwd", return_value=Path(self.temp.name)):
            self.assertEqual(
                Path(self.temp.name) / run_codex.RESULT_FILENAME,
                run_codex.result_path(self.env),
            )

    def test_missing_criterion_evidence_rejects_clean_tree(self):
        path = Path(self.temp.name) / run_codex.RESULT_FILENAME
        path.write_text(self._result("already_satisfied", [], evidence=""), encoding="utf-8")
        valid, _ = run_codex.validate_completion_result(path, repository_changed=False)
        self.assertFalse(valid)

    def test_changed_tree_requires_successful_structured_result(self):
        path = Path(self.temp.name) / run_codex.RESULT_FILENAME
        path.write_text(self._result("changed", ["module.py"]), encoding="utf-8")
        self.assertEqual(
            (True, "changed"), run_codex.validate_completion_result(path, repository_changed=True)
        )

    @staticmethod
    def _result(status, files, evidence="test passed"):
        import json

        return json.dumps(
            {
                "status": status,
                "objective": "Do the task",
                "files_changed": files,
                "acceptance_criteria": [
                    {"criterion": "requested behavior", "status": "satisfied", "evidence": evidence}
                ],
                "validation": [{"command": "pytest", "status": "passed"}],
                "unresolved_items": [],
            }
        )


if __name__ == "__main__":
    unittest.main()


class StructuredResultV1Tests(unittest.TestCase):
    def write_result(self, directory, **updates):
        value = {
            "schema_version": "1",
            "status": "changed",
            "implementation_status": "passed",
            "objective": "implemented",
            "files_changed": ["task.py"],
            "acceptance_criteria": [
                {"criterion": "behavior", "status": "passed", "evidence": "test"}
            ],
            "workflow_postconditions": [
                {
                    "condition": "Open draft PR",
                    "status": "pending_workflow",
                    "owner": "github_actions",
                }
            ],
            "validation": {"task_scoped": "passed", "repository_baseline": "passed"},
            "pre_existing_failures": [],
            "unresolved_items": [],
        }
        value.update(updates)
        path = Path(directory) / "codex-result.json"
        path.write_text(__import__("json").dumps(value))
        return path

    def test_pending_workflow_postcondition_allows_changed_result(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                (True, "changed"),
                run_codex.validate_completion_result(
                    self.write_result(directory), repository_changed=True
                ),
            )

    def test_workflow_postcondition_cannot_be_completed_by_codex(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_result(
                directory,
                workflow_postconditions=[
                    {"condition": "Open draft PR", "status": "completed", "owner": "github_actions"}
                ],
            )
            self.assertEqual(
                "invalid workflow postconditions",
                run_codex.validate_completion_result(path, repository_changed=True)[1],
            )

    def test_missing_implementation_evidence_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_result(directory, acceptance_criteria=[])
            self.assertFalse(run_codex.validate_completion_result(path, repository_changed=True)[0])

    def test_already_satisfied_clean_tree_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_result(directory, status="already_satisfied", files_changed=[])
            self.assertEqual(
                (True, "already_satisfied"),
                run_codex.validate_completion_result(path, repository_changed=False),
            )
