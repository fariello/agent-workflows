"""Narrow regression tests for the executed-transition pre-commit gate (IPD kecxnb).

NOTE: This is a NEW narrow regression test file and NOT the restored 1267-line test suite
that commit `19313eed` deleted. That deleted suite covered merge-aware evidence paths, both
git stages, and pre-commit registration, and is tracked for separate restoration under
backlog item ove09p (F-5).

This file covers the specific defect where `_has_executed_status` matched quoted or body
status lines (such as a fenced `- Status: executed`), falsely triggering refusal of commits
that add such quotes to non-executed plans.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.hooks import executed_transition_gate as GATE


class ExecutedStatusUnitTests(unittest.TestCase):
    """Unit tests for `_has_executed_status` bounded to the metadata region."""

    def test_case_a_approved_with_fenced_executed_returns_false(self):
        """Case (a): metadata approved plus a fenced `- Status: executed` returns False."""
        text = (
            "# IPD: Example Plan\n\n"
            "- Id: kecxnb\n"
            "- Status: approved\n"
            "- Author: test\n\n"
            "## Goal\n\n"
            "```text\n"
            "- Status: executed\n"
            "```\n"
        )
        self.assertFalse(GATE._has_executed_status(text))

    def test_case_b_metadata_executed_returns_true(self):
        """Case (b): metadata executed returns True."""
        text = (
            "# IPD: Example Plan\n\n"
            "- Id: kecxnb\n"
            "- Status: executed\n"
            "- Author: test\n\n"
            "## Goal\n\n"
            "Some content.\n"
        )
        self.assertTrue(GATE._has_executed_status(text))

    def test_case_c_metadata_done_returns_true(self):
        """Case (c): metadata done alias returns True."""
        text = (
            "# IPD: Example Plan\n\n"
            "- Id: kecxnb\n"
            "- Status: done\n"
            "- Author: test\n\n"
            "## Goal\n\n"
            "Some content.\n"
        )
        self.assertTrue(GATE._has_executed_status(text))

    def test_case_d_metadata_executed_with_oq_open_below_returns_true(self):
        """Case (d): metadata executed with an OQ block's own `- Status: open` below returns True."""
        text = (
            "# IPD: Example Plan\n\n"
            "- Id: kecxnb\n"
            "- Status: executed\n"
            "- Author: test\n\n"
            "## Open questions\n\n"
            "### OQ-01: Some question\n"
            "- Status: open\n"
        )
        self.assertTrue(GATE._has_executed_status(text))

    def test_case_e_headingless_approved_with_fenced_executed_returns_false(self):
        """Case (e): headingless record (no `##` heading) with metadata approved and fenced quote returns False."""
        text = (
            "# IPD: Example Plan\n\n"
            "- Id: kecxnb\n"
            "- Status: approved\n"
            "- Author: test\n\n"
            "```text\n"
            "- Status: executed\n"
            "```\n"
        )
        self.assertFalse(GATE._has_executed_status(text))


class ExecutedGateEndToEndTests(unittest.TestCase):
    """End-to-end regression tests verifying that staging a commit adding a fenced quote is accepted."""

    def test_commit_adding_fenced_executed_to_approved_plan_passes_gate(self):
        """Staging a commit that adds a fenced `- Status: executed` quote to an approved plan returns (0, [])."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=root, check=True
            )

            plan_dir = root / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True)
            plan_file = plan_dir / "20260925-fencegate-01-kecxnb-sample.ipd.md"

            # 1. Base commit: plan with Status: approved at HEAD
            initial_content = (
                "# IPD: Sample Plan\n\n"
                "- Id: kecxnb\n"
                "- Status: approved\n"
                "- Author: test\n\n"
                "## Goal\n\n"
                "Initial goal.\n"
            )
            plan_file.write_text(initial_content, encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "Initial plan commit"],
                cwd=root,
                check=True,
            )

            # 2. Stage a commit that adds a fenced `- Status: executed` quote
            modified_content = (
                "# IPD: Sample Plan\n\n"
                "- Id: kecxnb\n"
                "- Status: approved\n"
                "- Author: test\n\n"
                "## Goal\n\n"
                "Initial goal.\n\n"
                "```text\n"
                "- Status: executed\n"
                "```\n"
            )
            plan_file.write_text(modified_content, encoding="utf-8")
            subprocess.run(["git", "add", str(plan_file)], cwd=root, check=True)

            # 3. GATE.check should accept this commit: return (0, [])
            exit_code, refusals = GATE.check(root)
            self.assertEqual(
                exit_code,
                0,
                f"Expected exit_code 0, got {exit_code} with refusals: {refusals}",
            )
            self.assertEqual(refusals, [])
