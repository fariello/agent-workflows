"""Behavioral tests: unattended agent turns export AW_NONINTERACTIVE=1 and never block on PTY prompts."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_run, git_commit_helper, term


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )


class AgentChildEnvNonInteractiveTests(unittest.TestCase):
    def test_export_agent_child_env_sets_aw_noninteractive_even_over_falsy_value(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env: dict[str, str] = {"AW_NONINTERACTIVE": "0"}
            out = git_commit_helper.export_agent_child_env(
                env,
                repo,
                model="gemini-4-neon-high",
                runner=git_commit_helper.RUNNER_AGY_RUN,
            )
            self.assertEqual(out.get("AW_NONINTERACTIVE"), "1")
            self.assertTrue(term.is_forced_noninteractive(out))
            self.assertFalse(term.is_interactive(environ=out))

    def test_offer_commit_under_real_pty_does_not_prompt_when_agent_child_env_set(
        self,
    ) -> None:
        if os.name == "nt":
            self.skipTest("PTY test requires POSIX pty module")
        import pty

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            _init_git_repo(repo)
            target = repo / "sample.txt"
            target.write_text("v1\n", encoding="utf-8")
            subprocess.run(["git", "add", "sample.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            # Dirty the tracked file so offer_commit has a real path-scoped change to offer.
            target.write_text("v2\n", encoding="utf-8")

            child_env = dict(os.environ)
            child_env.pop("CI", None)
            child_env.pop("AW_NONINTERACTIVE", None)
            git_commit_helper.export_agent_child_env(
                child_env,
                repo,
                model="gemini-4-neon-high",
                runner=git_commit_helper.RUNNER_AGY_RUN,
            )

            script = (
                "import sys; "
                "from pathlib import Path; "
                "from agent_workflows import git_commit_helper as g; "
                "assert sys.stdin.isatty() and sys.stdout.isatty(), 'expected PTY'; "
                "res = g.offer_commit(Path('.'), ['sample.txt'], message='update sample'); "
                "print('OUTCOME=' + res.status)"
            )
            master_fd, slave_fd = pty.openpty()
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-c", script],
                    cwd=repo,
                    env=child_env,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    close_fds=True,
                )
            finally:
                os.close(slave_fd)

            chunks: list[bytes] = []
            try:
                proc.wait(timeout=10.0)
                while True:
                    try:
                        data = os.read(master_fd, 4096)
                    except OSError:
                        break
                    if not data:
                        break
                    chunks.append(data)
            finally:
                os.close(master_fd)

            output = b"".join(chunks).decode("utf-8", errors="replace")
            self.assertEqual(proc.returncode, 0, output)
            self.assertIn("OUTCOME=skipped", output)
            self.assertNotIn("Commit these path-scoped changes?", output)

    def test_agy_exec_run_turn_passes_aw_noninteractive_and_devnull_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            captured: dict[str, object] = {}

            class _FakeProc:
                def __init__(self, *args: object, **kwargs: object) -> None:
                    captured["env"] = kwargs.get("env")
                    captured["stdin"] = kwargs.get("stdin")
                    self.stdout = iter(
                        [
                            '{"event":"result","result":{"status":"SUCCESS","response":"ok","conversation_id":"c1"}}\n'
                        ]
                    )

                def wait(self) -> int:
                    return 0

            with (
                mock.patch.dict(os.environ, {}, clear=False),
                mock.patch.object(agy_run.subprocess, "Popen", side_effect=_FakeProc),
            ):
                os.environ.pop("AW_NONINTERACTIVE", None)
                agy_run.run_agy(
                    executable="agy",
                    root=repo,
                    prompt="test",
                    phase="exec",
                    model=None,
                    timeout="5m",
                    session_id=None,
                    use_continue=False,
                    skip_permissions=True,
                )

            env = captured.get("env")
            self.assertIsInstance(env, dict)
            assert isinstance(env, dict)
            self.assertEqual(env.get("AW_NONINTERACTIVE"), "1")
            self.assertEqual(captured.get("stdin"), subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
