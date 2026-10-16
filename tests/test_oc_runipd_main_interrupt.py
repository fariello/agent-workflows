#!/usr/bin/env python3
"""Behavioral tests for oc_runipd.main interrupt exit notices and exit codes.

Re-guards site S-07 (from plan 9rthek) after tests/test_interrupt_menu.py was
deleted in 19313eed. Exercises the real oc_runipd.main KeyboardInterrupt handler
when interrupted (SIGINT), terminated (SIGTERM), or terminated without cleanup.
"""

from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from agent_workflows import oc_runipd


class OcRunipdMainInterruptTests(unittest.TestCase):
    """Test exit codes and stderr notices when oc_runipd.main catches KeyboardInterrupt."""

    def _run_main_with_interrupt(
        self, exc_message: str
    ) -> tuple[int, str, str, mock.MagicMock]:
        """Drive oc_runipd.main to its KeyboardInterrupt handler with given exception message."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nonexistent_run_dir = Path(tmp_dir) / "nonexistent-run"
            mock_emit = mock.MagicMock()
            with (
                mock.patch.object(
                    oc_runipd,
                    "run_queue",
                    side_effect=KeyboardInterrupt(exc_message),
                ),
                mock.patch.object(oc_runipd, "emit_shutdown_report", mock_emit),
                mock.patch.object(
                    oc_runipd, "resolve_run_dir", return_value=nonexistent_run_dir
                ),
                mock.patch.object(
                    oc_runipd, "load_state", return_value={"options": {}}
                ),
                mock.patch.object(oc_runipd, "locked_run", mock.MagicMock()),
                mock.patch.object(oc_runipd, "install_stop_triggers", mock.MagicMock()),
                mock.patch("sys.stderr", new_callable=io.StringIO) as err,
                mock.patch("sys.stdout", new_callable=io.StringIO) as out,
            ):
                code = oc_runipd.main(["resume", "run-fake"])
                stderr_val = err.getvalue()
                stdout_val = out.getvalue()
            return code, stderr_val, stdout_val, mock_emit

    def test_clean_up_and_terminate_notice_and_exit_code(self):
        """Interrupted run with clean-up exits 130 and notices durable state preserved."""
        code, stderr, stdout, mock_emit = self._run_main_with_interrupt(
            "clean-up-and-terminate"
        )
        self.assertEqual(code, 130)
        self.assertIn("Interrupted; durable run state was preserved.", stderr)
        mock_emit.assert_called_once_with(to_stderr=True)

    def test_terminated_by_sigterm_notice_and_exit_code(self):
        """SIGTERM interrupt exits 143 and notices durable state preserved."""
        code, stderr, stdout, mock_emit = self._run_main_with_interrupt(
            "Terminated by SIGTERM"
        )
        self.assertEqual(code, 143)
        self.assertIn("Terminated by SIGTERM; durable run state was preserved.", stderr)
        mock_emit.assert_called_once_with(to_stderr=True)

    def test_just_terminate_no_cleanup_notice_and_exit_code(self):
        """Immediate exit without cleanup exits 130 and notices worktree/lanes left in place."""
        code, stderr, stdout, mock_emit = self._run_main_with_interrupt(
            "just-terminate-no-cleanup"
        )
        self.assertEqual(code, 130)
        self.assertIn(
            "Terminated without clean up; worktree and lanes left in place.",
            stderr,
        )
        self.assertNotIn("durable run state was preserved", stderr)
        mock_emit.assert_called_once_with(to_stderr=True)


if __name__ == "__main__":
    unittest.main()
