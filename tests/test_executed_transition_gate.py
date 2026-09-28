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

    def test_case_f_vnzm27_pinned_shape_fenced_grep_transcript_returns_false(self):
        """Pin of vnzm27's already-fixed reported shape: metadata approved plus a fenced grep transcript
        containing multiple '- Status: executed' lines returns False (this is a PIN, not a fix;
        already fixed by kecxnb)."""
        text = (
            "# IPD: Example Plan\n\n"
            "- Id: 3v7wo6\n"
            "- Status: approved\n"
            "- Author: test\n\n"
            "## Validation\n\n"
            "```text\n"
            "- Status: executed\n"
            "- Status: executed\n"
            "- Status: executed\n"
            "- Status: executed\n"
            "```\n"
        )
        self.assertFalse(GATE._has_executed_status(text))

    def test_plan_id_of_headingless_record_with_fenced_id_above_metadata(self):
        """Headingless record (no '##' heading) with fenced '- Id: bbbbbb' above metadata '- Id: 3v7wo6'
        must read '3v7wo6' (separates correct first-bullet/fence-skipping from region-only)."""
        text = (
            "# IPD: Headingless Plan\n\n"
            "```text\n"
            "- Id: bbbbbb\n"
            "```\n\n"
            "- Id: 3v7wo6\n"
            "- Status: approved\n"
        )
        self.assertEqual(GATE._plan_id_of(text), "3v7wo6")

    def test_plan_id_of_preamble_versus_body_fenced_quote(self):
        """Assert _plan_id_of returns '3v7wo6' for both a record whose fenced '- Id: bbbbbb' sits in the
        preamble (above the metadata bullets, inside metadata_region ending at '##') and one whose fence
        sits after the first '##' heading (outside metadata_region). A region-only reader passes the
        second and fails the first, which is why fence-skipping is required and not merely belt-and-braces."""
        preamble_text = (
            "# IPD: Preamble Quote Plan\n\n"
            "Preamble quote:\n"
            "```text\n"
            "- Id: bbbbbb\n"
            "```\n\n"
            "- Id: 3v7wo6\n"
            "- Status: approved\n\n"
            "## Goal\n\n"
            "Goal text.\n"
        )
        body_text = (
            "# IPD: Body Quote Plan\n\n"
            "- Id: 3v7wo6\n"
            "- Status: approved\n\n"
            "## Goal\n\n"
            "Body quote:\n"
            "```text\n"
            "- Id: bbbbbb\n"
            "```\n"
        )
        self.assertEqual(GATE._plan_id_of(preamble_text), "3v7wo6")
        self.assertEqual(GATE._plan_id_of(body_text), "3v7wo6")


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

    def test_false_accept_during_merge_with_preamble_fenced_id_is_refused(self):
        """(a) False accept regression: a plan staged into executed/ whose metadata is 3v7wo6 but
        whose preamble fences '- Id: bbbbbb', merged with an incoming branch carrying only
        lifecycle(bbbbbb): finalize, must be REFUSED (exit 1) naming 3v7wo6 and not accepted (0, [])."""
        from agent_workflows import artifact_core

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
            (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
            (root / "init.txt").write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)

            # Create side branch with finalize commit for bbbbbb
            subprocess.run(
                ["git", "checkout", "-q", "-b", "side"], cwd=root, check=True
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-q",
                    "--allow-empty",
                    "-m",
                    artifact_core.finalize_commit_subject("bbbbbb"),
                ],
                cwd=root,
                check=True,
            )

            # Return to main branch and diverge
            subprocess.run(["git", "checkout", "-q", "-"], cwd=root, check=True)
            (root / "diverge.txt").write_text("diverge\n", encoding="utf-8")
            subprocess.run(["git", "add", "diverge.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "diverge"], cwd=root, check=True
            )

            # Begin merge without committing
            subprocess.run(
                ["git", "merge", "--no-ff", "--no-commit", "side"], cwd=root, check=True
            )

            # Stage plan into executed/ whose preamble fences - Id: bbbbbb and whose metadata is 3v7wo6
            plan_dir = root / ".aw" / "records" / "plans" / "executed"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_file = plan_dir / "20260928-test-01-3v7wo6-sample.ipd.md"
            plan_content = (
                "# IPD: Sample Plan\n\n"
                "Preamble quote:\n"
                "```text\n"
                "- Id: bbbbbb\n"
                "```\n\n"
                "- Id: 3v7wo6\n"
                "- Status: executed\n"
                "- Author: test\n\n"
                "## Goal\n\n"
                "Initial goal.\n"
            )
            plan_file.write_text(plan_content, encoding="utf-8")
            subprocess.run(["git", "add", str(plan_file)], cwd=root, check=True)

            exit_code, refusals = GATE.check(root)
            self.assertEqual(
                exit_code,
                1,
                f"Expected exit_code 1 (refusal), got {exit_code} with refusals: {refusals}",
            )
            joined = " ".join(refusals)
            self.assertIn("3v7wo6", joined)
            self.assertNotIn("bbbbbb", joined)

    def test_misattribution_refusal_with_preamble_fenced_id_names_real_id(self):
        """(b) Misattribution regression: a plan staged into executed/ with no merge whose preamble
        fences '- Id: bbbbbb' and whose metadata is 3v7wo6 must refuse naming 3v7wo6 and NOT bbbbbb."""
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
            (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
            (root / "init.txt").write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)

            plan_dir = root / ".aw" / "records" / "plans" / "executed"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_file = plan_dir / "20260928-test-01-3v7wo6-sample.ipd.md"
            plan_content = (
                "# IPD: Sample Plan\n\n"
                "Preamble quote:\n"
                "```text\n"
                "- Id: bbbbbb\n"
                "```\n\n"
                "- Id: 3v7wo6\n"
                "- Status: executed\n"
                "- Author: test\n\n"
                "## Goal\n\n"
                "Initial goal.\n"
            )
            plan_file.write_text(plan_content, encoding="utf-8")
            subprocess.run(["git", "add", str(plan_file)], cwd=root, check=True)

            exit_code, refusals = GATE.check(root)
            self.assertEqual(
                exit_code,
                1,
                f"Expected exit_code 1, got {exit_code} with refusals: {refusals}",
            )
            joined = " ".join(refusals)
            self.assertIn("3v7wo6", joined)
            self.assertNotIn("bbbbbb", joined)

    def test_genuine_raw_transition_into_executed_is_still_refused(self):
        """(d) The gate still refuses a genuine raw transition: a plan with clean metadata - Id: 3v7wo6
        hand-moved into executed/ with no journal and no merge is refused (exit 1), naming 3v7wo6."""
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
            (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")

            # Base commit: plan in pending
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            plan_name = "20260928-test-01-3v7wo6-sample.ipd.md"
            plan_pending = pending_dir / plan_name
            plan_pending.write_text(
                "# IPD: Sample Plan\n\n"
                "- Id: 3v7wo6\n"
                "- Status: approved\n"
                "- Author: test\n\n"
                "## Goal\n\n"
                "Initial goal.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "add plan"], cwd=root, check=True
            )

            # Move to executed with status flip
            exec_dir = root / ".aw" / "records" / "plans" / "executed"
            exec_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "mv", str(plan_pending), str(exec_dir / plan_name)],
                cwd=root,
                check=True,
            )
            exec_plan = exec_dir / plan_name
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "- Status: approved", "- Status: executed"
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", str(exec_plan)], cwd=root, check=True)

            exit_code, refusals = GATE.check(root)
            self.assertEqual(exit_code, 1)
            self.assertEqual(len(refusals), 1)
            self.assertIn("3v7wo6", refusals[0])
            self.assertIn("raw plan->executed transition", refusals[0])
            self.assertNotIn("no readable", refusals[0])
