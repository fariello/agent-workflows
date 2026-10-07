"""Tests for the static typecheck gate configuration and F-06 defect fix.

Plan m7fllj E-04 / E-05.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

import pytest

from agent_workflows.runner_shared import (
    RecoveryDisposition,
    build_verify_and_continue_notice,
)


class VerifyAndContinueNoticeTests(unittest.TestCase):
    """Behavioral coverage for build_verify_and_continue_notice (E-04)."""

    def test_verify_and_continue_notice_behavior(self) -> None:
        """When verify_and_continue is true, returns non-empty notice string."""
        branch = "aw/lane/test-notice"
        sha = "abc1234"
        subject = "Fix regression defect"
        decision = RecoveryDisposition(
            disposition="verify-and-continue",
            reason="prior attempt committed work",
            inspected_lane_id="lane-1",
            inspected_branch=branch,
            inspected_worktree=Path("/tmp"),
            lane_state="valid",
            commits_ahead=1,
            dirty=False,
            snapshot_only=False,
            real_commits=[(sha, subject)],
        )
        rendered = build_verify_and_continue_notice(Path("."), decision)
        self.assertIsInstance(rendered, str)
        self.assertGreater(len(rendered), 0)
        self.assertIn(branch, rendered)
        self.assertIn(sha, rendered)
        self.assertIn(subject, rendered)
        # Verify prompt interpolation does not produce "Mode: recoveryNone"
        prompt_snippet = f"Mode: recovery{rendered}"
        self.assertNotIn("Mode: recoveryNone", prompt_snippet)
        self.assertIn("Mode: recovery\n\n## A PRIOR ATTEMPT", prompt_snippet)

    def test_verify_and_continue_notice_false_case(self) -> None:
        """When verify_and_continue is false, returns exactly empty string."""
        decision = RecoveryDisposition(
            disposition="rerun-fresh",
            reason="abandoned",
            inspected_lane_id="lane-1",
            inspected_branch="aw/lane/test-notice",
            inspected_worktree=Path("/tmp"),
            lane_state="valid",
            commits_ahead=0,
            dirty=False,
            snapshot_only=False,
            real_commits=[],
        )
        rendered = build_verify_and_continue_notice(Path("."), decision)
        self.assertEqual(rendered, "")


@pytest.mark.slow
class TypecheckGateTests(unittest.TestCase):
    """Pin the configured static type gate exit status (E-05)."""

    @pytest.mark.timeout(300)
    def test_typecheck_gate_clean_exit(self) -> None:
        """The configured narrowed mypy gate exits 0 over agent_workflows/."""
        repo_root = Path(__file__).resolve().parent.parent
        res = subprocess.run(
            [sys.executable, "-m", "mypy", "agent_workflows"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"Type gate failed with exit code {res.returncode}:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("Success: no issues found", res.stdout)


if __name__ == "__main__":
    unittest.main()
