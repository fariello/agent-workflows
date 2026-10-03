"""Tests verifying that run directory parent directories are guaranteed by their writers.

Pins the guarantee by outcome on run directories that deliberately have no subdirectories
pre-created, verifying:
  (a) write_prompt guarantees prompts/ exists on a bare run directory
  (b) write_prompt is idempotent when prompts/ already exists and preserves siblings
  (c) attempt_log_path is a pure path helper and creates nothing on disk
  (d) oc_runipd.run_opencode guarantees sessions/ exists on a bare run directory
  (e) agy_runipd.run_agy_turn guarantees sessions/ exists on a bare run directory
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest
from typing import Any

from agent_workflows import agy_runipd as _agy
from agent_workflows import oc_runipd as _oc
from agent_workflows import runner_shared


class RunDirParentsGuaranteedByWritersTests(unittest.TestCase):
    """Behavioral tests verifying writers create their parent directories."""

    def test_write_prompt_creates_parent_in_bare_run_dir(self) -> None:
        """(a) write_prompt into a bare run directory creates prompts/ and writes content."""
        with tempfile.TemporaryDirectory() as temp:
            run_dir = pathlib.Path(temp) / "run"
            run_dir.mkdir()
            self.assertFalse((run_dir / "prompts").exists())

            item = {"position": 1, "id6": "abc123", "action": "exec"}
            prompt_content = "# Prompt title\n\nExecution instructions."
            prompt_path = runner_shared.write_prompt(
                run_dir, item, prompt_content, attempt_no=1
            )

            self.assertTrue((run_dir / "prompts").is_dir())
            self.assertTrue(prompt_path.is_file())
            self.assertEqual(prompt_path.read_text(encoding="utf-8"), prompt_content)

    def test_write_prompt_idempotent_when_parent_exists(self) -> None:
        """(b) write_prompt is idempotent when prompts/ exists and does not touch siblings."""
        with tempfile.TemporaryDirectory() as temp:
            run_dir = pathlib.Path(temp) / "run"
            prompts_dir = run_dir / "prompts"
            prompts_dir.mkdir(parents=True)
            sibling = prompts_dir / "sibling.txt"
            sibling.write_text("existing sibling content", encoding="utf-8")

            item = {"position": 2, "id6": "def456", "action": "review"}
            prompt_content = "# Review prompt\nReview instructions."
            prompt_path = runner_shared.write_prompt(
                run_dir, item, prompt_content, attempt_no=1
            )

            self.assertTrue(prompt_path.is_file())
            self.assertEqual(prompt_path.read_text(encoding="utf-8"), prompt_content)
            self.assertEqual(
                sibling.read_text(encoding="utf-8"), "existing sibling content"
            )

    def test_attempt_log_path_is_pure_and_creates_nothing(self) -> None:
        """(c) attempt_log_path is a pure accessor and does not create directories or files."""
        with tempfile.TemporaryDirectory() as temp:
            run_dir = pathlib.Path(temp) / "run"
            run_dir.mkdir()
            item = {"position": 1, "id6": "probe1", "action": "exec"}

            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no=1)

            self.assertEqual(log_path.name, "01-probe1-attempt-1.jsonl")
            self.assertFalse(log_path.exists())
            self.assertFalse((run_dir / "sessions").exists())
            self.assertFalse((run_dir / "prompts").exists())

    def test_oc_run_opencode_guarantees_sessions_dir(self) -> None:
        """(d) oc_runipd.run_opencode creates sessions/ on a bare run directory and reaches launch."""
        real_popen = subprocess.Popen

        def fake_popen(argv: Any, **kw: Any) -> Any:
            cmd = list(argv) if isinstance(argv, (list, tuple)) else [str(argv)]
            if cmd and cmd[0] in ("git", sys.executable, "bwrap"):
                return real_popen(argv, **kw)
            raise RuntimeError("stop-before-launch")

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            run_dir = root / "run"
            run_dir.mkdir()
            prompt = root / "prompt.md"
            prompt.write_text("probe\n", encoding="utf-8")
            plan = repo / "plan.ipd.md"
            plan.write_text("- Id: probe1\n", encoding="utf-8")
            state = {
                "run_id": "run-probe",
                "repo": str(repo),
                "set_sessions": {},
                "session_turn_counts": {},
                "options": {"opencode": "/bin/false", "agy_executable": "/bin/false"},
                "queue": [],
            }
            item = {
                "id6": "probe1",
                "setid": "probe",
                "position": 1,
                "action": "execute",
            }

            subprocess.Popen = fake_popen  # type: ignore[assignment]
            exc: BaseException | None = None
            try:
                _oc.run_opencode(
                    state,
                    run_dir,
                    item,
                    plan,
                    prompt,
                    1,
                    resume_session="ses-probe-sentinel",
                )
            except BaseException as e:
                exc = e
            finally:
                subprocess.Popen = real_popen  # type: ignore[assignment]

            self.assertNotIsInstance(
                exc,
                FileNotFoundError,
                f"run_opencode raised FileNotFoundError on missing sessions parent: {exc}",
            )
            self.assertTrue(
                (run_dir / "sessions").is_dir(),
                "Expected run_dir/sessions directory to exist after run_opencode",
            )

    def test_agy_run_agy_turn_guarantees_sessions_dir(self) -> None:
        """(e) agy_runipd.run_agy_turn creates sessions/ on a bare run directory and reaches launch."""
        real_popen = subprocess.Popen

        def fake_popen(argv: Any, **kw: Any) -> Any:
            cmd = list(argv) if isinstance(argv, (list, tuple)) else [str(argv)]
            if cmd and cmd[0] in ("git", sys.executable, "bwrap"):
                return real_popen(argv, **kw)
            raise RuntimeError("stop-before-launch")

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            run_dir = root / "run"
            run_dir.mkdir()
            prompt = root / "prompt.md"
            prompt.write_text("probe\n", encoding="utf-8")
            state = {
                "run_id": "run-probe",
                "repo": str(repo),
                "set_sessions": {},
                "session_turn_counts": {},
                "options": {"opencode": "/bin/false", "agy_executable": "/bin/false"},
                "queue": [],
            }
            item = {
                "id6": "probe1",
                "setid": "probe",
                "position": 1,
                "action": "execute",
            }

            subprocess.Popen = fake_popen  # type: ignore[assignment]
            exc: BaseException | None = None
            try:
                _agy.run_agy_turn(
                    state,
                    run_dir,
                    item,
                    prompt,
                    1,
                    session_id="ses-probe-sentinel",
                    use_continue=False,
                )
            except BaseException as e:
                exc = e
            finally:
                subprocess.Popen = real_popen  # type: ignore[assignment]

            self.assertNotIsInstance(
                exc,
                FileNotFoundError,
                f"run_agy_turn raised FileNotFoundError on missing sessions parent: {exc}",
            )
            self.assertTrue(
                (run_dir / "sessions").is_dir(),
                "Expected run_dir/sessions directory to exist after run_agy_turn",
            )


if __name__ == "__main__":
    unittest.main()
