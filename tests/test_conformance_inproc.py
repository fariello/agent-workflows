"""Behavioral tests for run_cli_inproc in tests/conformance_matrix.py (IPD c8bfp9 E-04 / V-04).

Asserts:
1. Parity: equal (returncode, stdout) against run_cli for cheap leaves (--version, layout --agent, usage error).
2. Isolation: restored os.getcwd(), os.environ, and sys.argv after both normal completion and exceptions.
3. NO_COLOR: honored and passed through the pinned environment.
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

from tests.conformance_matrix import (
    ANSI_RE,
    REPO_ROOT,
    run_cli,
    run_cli_inproc,
)


class ConformanceInprocTests(unittest.TestCase):
    """Behavioral tests for the in-process CLI runner helper."""

    def test_parity_version(self) -> None:
        """Assert run_cli_inproc matches run_cli for --version."""
        argv = ["--version"]
        res_sub = run_cli(argv)
        res_inp = run_cli_inproc(argv)
        self.assertEqual(res_inp.returncode, res_sub.returncode)
        self.assertEqual(res_inp.stdout, res_sub.stdout)
        self.assertEqual(res_inp.stderr, res_sub.stderr)

    def test_parity_layout_agent(self) -> None:
        """Assert run_cli_inproc matches run_cli for layout --agent."""
        argv = ["layout", "--agent"]
        res_sub = run_cli(argv)
        res_inp = run_cli_inproc(argv)
        self.assertEqual(res_inp.returncode, res_sub.returncode)
        self.assertEqual(res_inp.stdout, res_sub.stdout)
        self.assertEqual(res_inp.stderr, res_sub.stderr)

    def test_parity_usage_error(self) -> None:
        """Assert run_cli_inproc matches run_cli for usage errors."""
        argv = ["--non-existent-flag-for-testing-c8bfp9"]
        res_sub = run_cli(argv)
        res_inp = run_cli_inproc(argv)
        self.assertEqual(res_inp.returncode, res_sub.returncode)
        self.assertEqual(res_inp.returncode, 2)
        self.assertEqual(res_inp.stderr, res_sub.stderr)

    def test_restore_cwd_and_env_after_raise(self) -> None:
        """Assert os.getcwd(), os.environ, and sys.argv are restored when cli.main raises."""
        orig_cwd = os.getcwd()
        orig_env = dict(os.environ)
        orig_argv = list(sys.argv)
        target_cwd = REPO_ROOT / "tests"

        with mock.patch(
            "agent_workflows.cli.main", side_effect=RuntimeError("simulated crash")
        ):
            with self.assertRaises(RuntimeError):
                run_cli_inproc(
                    ["--version"],
                    cwd=target_cwd,
                    env_overrides={"TEST_INPROC_SENTINEL_RAISE": "active"},
                )

        self.assertEqual(os.getcwd(), orig_cwd)
        self.assertEqual(dict(os.environ), orig_env)
        self.assertEqual(sys.argv, orig_argv)
        self.assertNotIn("TEST_INPROC_SENTINEL_RAISE", os.environ)

    def test_restore_cwd_and_env_normal(self) -> None:
        """Assert os.getcwd(), os.environ, and sys.argv are restored after normal run."""
        orig_cwd = os.getcwd()
        orig_env = dict(os.environ)
        orig_argv = list(sys.argv)
        target_cwd = REPO_ROOT / "tests"

        res = run_cli_inproc(
            ["--version"],
            cwd=target_cwd,
            env_overrides={"TEST_INPROC_SENTINEL_NORMAL": "active"},
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(os.getcwd(), orig_cwd)
        self.assertEqual(dict(os.environ), orig_env)
        self.assertEqual(sys.argv, orig_argv)
        self.assertNotIn("TEST_INPROC_SENTINEL_NORMAL", os.environ)

    def test_no_color_honored(self) -> None:
        """Assert no_color=True sets NO_COLOR=1 in environment and output is ANSI-free."""
        observed_env = {}

        def spy_main(argv):
            observed_env["NO_COLOR"] = os.environ.get("NO_COLOR")
            observed_env["FORCE_COLOR"] = os.environ.get("FORCE_COLOR")
            return 0

        with mock.patch("agent_workflows.cli.main", side_effect=spy_main):
            res = run_cli_inproc(["--version"], no_color=True)
            self.assertEqual(res.returncode, 0)
            self.assertEqual(observed_env.get("NO_COLOR"), "1")
            self.assertIsNone(observed_env.get("FORCE_COLOR"))

        # Real execution with no_color produces no ANSI escape sequences
        res_real = run_cli_inproc(["layout"], no_color=True)
        self.assertEqual(res_real.returncode, 0)
        self.assertIsNone(ANSI_RE.search(res_real.stdout))
        self.assertIsNone(ANSI_RE.search(res_real.stderr))


if __name__ == "__main__":
    unittest.main()
