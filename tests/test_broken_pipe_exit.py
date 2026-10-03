"""Regression tests for clean exit on closed stdout pipe (E-01, V-01).

Drives real CLI subprocesses through a pipe whose read end is closed before launch,
verifying that commands exit cleanly within the three-state exit vocabulary {0, 1, 2}
without dumping a BrokenPipeError or a Python traceback on stderr.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest

import pytest

pytestmark = pytest.mark.slow


def _run_with_closed_stdout(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Launch a CLI subprocess with stdout connected to a pre-closed pipe."""
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "agent_workflows", *args],
            stdout=write_fd,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        os.close(write_fd)

    _, stderr = proc.communicate(timeout=180)
    return subprocess.CompletedProcess(
        args=[sys.executable, "-m", "agent_workflows", *args],
        returncode=proc.returncode,
        stdout="",
        stderr=stderr,
    )


class TestBrokenPipeExit(unittest.TestCase):
    """Behavioral tests asserting clean exit when stdout pipe is closed early."""

    def _assert_clean_pipe_exit(
        self,
        proc: subprocess.CompletedProcess[str],
        *,
        expected_exit: int | tuple[int, ...] = (0, 1, 2),
    ) -> None:
        expected = (expected_exit,) if isinstance(expected_exit, int) else expected_exit
        self.assertIn(
            proc.returncode,
            expected,
            f"Process exited with {proc.returncode}, expected one of {expected}. Stderr:\n{proc.stderr}",
        )
        self.assertNotIn(
            proc.returncode,
            (120, 141),
            f"Process exited with forbidden pipe/signal exit code {proc.returncode}. Stderr:\n{proc.stderr}",
        )
        self.assertNotIn(
            "BrokenPipeError",
            proc.stderr,
            f"stderr must not contain 'BrokenPipeError':\n{proc.stderr}",
        )
        self.assertNotIn(
            "Traceback",
            proc.stderr,
            f"stderr must not contain 'Traceback':\n{proc.stderr}",
        )

    def test_find_plans_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["find", "plans"])
        self._assert_clean_pipe_exit(proc)

    def test_find_plans_paths_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["find", "plans", "--paths"])
        self._assert_clean_pipe_exit(proc)

    def test_find_plans_agent_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["find", "plans", "--agent"])
        self._assert_clean_pipe_exit(proc)

    def test_find_plans_json_control_closed_pipe(self) -> None:
        # Control surface: BaseRenderer.emit already catches BrokenPipeError, so this passes at base.
        proc = _run_with_closed_stdout(["find", "plans", "--json"])
        self._assert_clean_pipe_exit(proc, expected_exit=0)

    def test_doctor_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["doctor"])
        self._assert_clean_pipe_exit(proc)

    def test_search_plans_paths_shutdown_flush_closed_pipe(self) -> None:
        # Surface that completes write loop before pipe closes, failing ONLY during interpreter shutdown flush (F-05).
        proc = _run_with_closed_stdout(["search", "plans", "Scope-Paths", "--paths"])
        self._assert_clean_pipe_exit(proc)

    def test_attention_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["attention"])
        self._assert_clean_pipe_exit(proc)

    def test_ipd_board_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["ipd", "board"])
        self._assert_clean_pipe_exit(proc)

    def test_find_all_closed_pipe(self) -> None:
        proc = _run_with_closed_stdout(["find", "all"])
        self._assert_clean_pipe_exit(proc)

    def test_help_argparse_systemexit_closed_pipe(self) -> None:
        # argparse raises SystemExit on --help, bypassing normal dispatch return (F-11).
        proc = _run_with_closed_stdout(["--help"])
        self._assert_clean_pipe_exit(proc, expected_exit=0)


if __name__ == "__main__":
    unittest.main()
