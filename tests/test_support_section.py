"""Tests for bounded section extractor helpers in tests/support.py (IPD 78rxzc)."""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import backlog as B
from agent_workflows import plans as plans_mod
from tests import support


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


class SectionExtractorTests(unittest.TestCase):
    """Prove section extractor happy paths and required refusals."""

    def test_section_bound_error_is_assertion_error_subclass(self):
        """(g) SectionBoundError is an AssertionError subclass."""
        self.assertTrue(issubclass(support.SectionBoundError, AssertionError))

    def test_bounded_section_extraction(self):
        """(a) Bounded section returns exact text; include_end extends through marker."""
        text = (
            "# Document\n\n"
            "## Section 1\n"
            "content 1\n\n"
            "## Section 2\n"
            "content 2\n"
        )
        sec = support.section(text, "## Section 1", "## Section 2")
        self.assertEqual(sec, "## Section 1\ncontent 1\n\n")

        sec_inc = support.section(
            text, "## Section 1", "## Section 2", include_end=True
        )
        self.assertEqual(sec_inc, "## Section 1\ncontent 1\n\n## Section 2")

    def test_end_marker_search_starts_after_start_marker(self):
        """Start marker containing end marker does not match itself."""
        text = "## Workflow history\n" "- 2026-09-30 created: an item\n\n" "## Next\n"
        # start marker "## Workflow history" contains end marker "## "
        sec = support.section(text, "## Workflow history", "## ")
        self.assertNotEqual(sec, "")
        self.assertEqual(sec, "## Workflow history\n- 2026-09-30 created: an item\n\n")

    def test_absent_start_marker_raises(self):
        """(b) Absent start marker raises SectionBoundError naming the marker."""
        text = "## Other section\ncontent\n"
        with self.assertRaises(support.SectionBoundError) as cm:
            support.section(text, "## Missing", "## Other")
        msg = str(cm.exception)
        self.assertIn("## Missing", msg)
        self.assertIn("start marker", msg)

    def test_absent_end_marker_raises_and_points_to_final_section(self):
        """(c) Absent end marker raises SectionBoundError naming marker and final_section."""
        text = "## Start\nsome content to eof\n"
        with self.assertRaises(support.SectionBoundError) as cm:
            support.section(text, "## Start", "## Missing End")
        msg = str(cm.exception)
        self.assertIn("## Missing End", msg)
        self.assertIn("unknown", msg.lower())
        self.assertIn("final_section", msg)

    def test_anchored_skips_body_prose_and_anchored_false_matches_prose(self):
        """(d) Line anchoring skips body-prose mentions; anchored=False finds them."""
        text = (
            "# Heading\n\n"
            "Discussing ## Workflow history in body prose here.\n\n"
            "## Workflow history\n\n"
            "- 2026-09-30: real entry\n\n"
            "## Next section\n"
        )
        # Default anchored=True skips prose and starts at real heading
        sec_anchored = support.section(text, "## Workflow history", "## Next section")
        self.assertTrue(
            sec_anchored.startswith("## Workflow history\n\n- 2026-09-30: real entry")
        )

        # anchored=False matches the prose mention
        sec_unanchored = support.section(
            text, "## Workflow history", "## Next section", anchored=False
        )
        self.assertTrue(
            sec_unanchored.startswith("## Workflow history in body prose here.")
        )

    def test_marker_only_in_prose_refuses_anchored_and_points_to_anchored_false(self):
        """F-09: Marker present only in prose raises on start with hint for anchored=False."""
        text = (
            "# Readme\n\n"
            "This document only quotes ## Workflow history in a sentence.\n"
        )
        with self.assertRaises(support.SectionBoundError) as cm:
            support.section(text, "## Workflow history", "## Next")
        msg = str(cm.exception)
        self.assertIn("## Workflow history", msg)
        self.assertIn("anchored=False", msg)

        # anchored=False succeeds in finding the start
        text_with_end = text + "\n## Next\n"
        sec = support.section(
            text_with_end, "## Workflow history", "## Next", anchored=False
        )
        self.assertEqual(sec, "## Workflow history in a sentence.\n\n")

    def test_final_section_terminal_success_and_refusal(self):
        """(e) final_section returns tail when terminal and refuses when followed by next_marker."""
        text_terminal = "## Header\nintro\n\n## Sets\n- set 1\n- set 2\n"
        tail = support.final_section(text_terminal, "## Sets", next_marker="## ")
        self.assertEqual(tail, "## Sets\n- set 1\n- set 2\n")

        text_non_terminal = text_terminal + "\n## Recently touched\n- x\n"
        with self.assertRaises(support.SectionBoundError) as cm:
            support.final_section(text_non_terminal, "## Sets", next_marker="## ")
        msg = str(cm.exception)
        self.assertIn("## Sets", msg)
        self.assertIn("## ", msg)
        self.assertIn("offset", msg)

    def test_final_section_against_real_plans_render_status_index(self):
        """V-03: final_section on real plans.render_status_index output and appended refusal."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Create minimal fixture with plans declaring a Set
            plans = root / ".agents" / "plans"
            pending = plans / "pending"
            pending.mkdir(parents=True, exist_ok=True)
            (pending / "20260101-0000-01-a.md").write_text(
                "# IPD: a\n\n- Status: approved\n- Set: myset\n- Order: 2\n\n## Goal\n\nx\n",
                encoding="utf-8",
            )
            (pending / "20260101-0001-01-b.md").write_text(
                "# IPD: b\n\n- Status: approved\n- Set: myset\n- Order: 1\n\n## Goal\n\nx\n",
                encoding="utf-8",
            )
            out = plans_mod.render_status_index(root, plans_mod.scan(root))
            self.assertIn("## Sets", out)

            # final_section extracts the terminal Sets section
            tail = support.final_section(out, "## Sets", next_marker="## ")
            self.assertTrue(tail.startswith("## Sets"))
            self.assertIn("myset", tail)

            # Appending a new heading causes final_section to refuse
            appended = out + "\n## Recently touched\n\n- x\n"
            with self.assertRaises(support.SectionBoundError) as cm:
                support.final_section(appended, "## Sets", next_marker="## ")
            msg = str(cm.exception)
            self.assertIn("offset", msg)
            self.assertIn("## Sets", msg)

            # Contrast: unbounded slice absorbs the new section and grows
            unbounded_orig = out[
                out.index("## Sets") :
            ]  # aw-unbounded-ok: control test proving raw slice absorbs appended section
            unbounded_appended = appended[
                appended.index("## Sets") :
            ]  # aw-unbounded-ok: control test proving raw slice absorbs appended section
            self.assertGreater(len(unbounded_appended), len(unbounded_orig))

    def test_section_lines_agreement_and_refusal(self):
        """(f) section_lines agrees with section().splitlines() and inherits refusals."""
        text = (
            "## Workflow history\n"
            "- 2026-09-30 line 1\n"
            "- 2026-09-30 line 2\n"
            "## Next\n"
        )
        lines = support.section_lines(text, "## Workflow history", "## Next")
        expected = support.section(text, "## Workflow history", "## Next").splitlines()
        self.assertEqual(lines, expected)
        self.assertEqual(
            lines, ["## Workflow history", "- 2026-09-30 line 1", "- 2026-09-30 line 2"]
        )

        # Refusal inheritance
        with self.assertRaises(support.SectionBoundError):
            support.section_lines(text, "## Workflow history", "## Missing End")

    def test_backlog_writer_driven_reproduction(self):
        """Load-bearing 1pgrii reproduction driven through real backlog writers (2 vs 4)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            support.init_repo(repo)
            (repo / ".agents" / "backlog" / "open").mkdir(parents=True)
            (repo / ".agents" / "backlog" / "done").mkdir(parents=True)

            body_text = "## Suggested work\n\n- bound the guard\n- add a control test\n"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc_new = B.run_new(
                    _args(
                        dir=str(repo),
                        summary="an item",
                        set="s",
                        priority="medium",
                        kind="bug",
                        slug="x",
                        body=body_text,
                        apply=True,
                    )
                )
            self.assertEqual(rc_new, 0)

            f = next((repo / ".agents" / "backlog" / "open").glob("*.md"))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc_set = B.run_set(
                    _args(
                        dir=str(repo),
                        path=str(f),
                        status="done",
                        gate_kind=None,
                        gate_ref=None,
                        message="finished",
                        apply=True,
                    )
                )
            self.assertEqual(rc_set, 0)

            moved = repo / ".agents" / "backlog" / "done" / f.name
            text = moved.read_text(encoding="utf-8")

            # The buggy unbounded slice reads across sections to EOF
            after = text.split(
                "## Workflow history", 1
            )[
                1
            ]  # aw-unbounded-ok: control test proving raw split absorbs appended section
            unbounded = [ln for ln in after.split("\n") if ln.startswith("- ")]
            self.assertEqual(len(unbounded), 4)

            # The bounded section extractor bounds at the next heading
            bounded_sec = support.section(text, "## Workflow history", "## ")
            bounded_bullets = [
                ln for ln in bounded_sec.splitlines() if ln.startswith("- ")
            ]
            self.assertEqual(len(bounded_bullets), 2)
            self.assertIn("finished", bounded_bullets[0])
            self.assertIn("created", bounded_bullets[1])


if __name__ == "__main__":
    unittest.main()
