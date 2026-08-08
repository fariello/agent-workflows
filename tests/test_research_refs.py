"""Tests for research regroup/rename + reference integrity (Set research-org, Order 04).

Stdlib unittest, throwaway dirs. Verifies set-assign (shared date, ordered NN, stable id6), mv
(re-slug keeps id6), the reference updater (full-old-name only, bare-id6 untouched, outside-scan-root
untouched), the dangling-cite detector (stale full path flagged, stable bare id6 not falsely
flagged), and the single pinned scan-root constant.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import research_contract as R
from agent_workflows import research_refs as RF


def _mk_research(root: Path, name: str, body: str = "content") -> Path:
    rroot = root / R.RESEARCH_ROOT
    rroot.mkdir(parents=True, exist_ok=True)
    p = rroot / name
    p.write_text(body, encoding="utf-8")
    return p


class SetAssignTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _mk_research(self.root, "20260701-alpha-00-aaaaaa-first.notes.md")
        _mk_research(self.root, "20260705-beta-00-bbbbbb-second.notes.md")

    def test_shared_date_ordered_nn_stable_id(self):
        plans, err = RF.plan_set_assign(
            self.rroot, ["aaaaaa", "bbbbbb"], "grouped", "20260710", start_order=0
        )
        self.assertIsNone(err)
        self.assertEqual(len(plans), 2)
        p0, _ = R.parse_name(plans[0].new_path.name)
        p1, _ = R.parse_name(plans[1].new_path.name)
        # Shared date + set.
        self.assertEqual(p0.date, "20260710")
        self.assertEqual(p1.date, "20260710")
        self.assertEqual(p0.set_id, "grouped")
        self.assertEqual(p1.set_id, "grouped")
        # Ordered NN.
        self.assertEqual(p0.order, "00")
        self.assertEqual(p1.order, "01")
        # Stable ids.
        self.assertEqual(p0.id6, "aaaaaa")
        self.assertEqual(p1.id6, "bbbbbb")

    def test_unknown_id_errors(self):
        plans, err = RF.plan_set_assign(self.rroot, ["zzzzzz"], "g", "20260710")
        self.assertIsNone(plans)
        self.assertIn("no research file", err)


class MvTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _mk_research(self.root, "20260701-alpha-00-aaaaaa-old-slug.notes.md")

    def test_reslug_keeps_id(self):
        plan, err = RF.plan_mv(self.rroot, "aaaaaa", slug="New Slug")
        self.assertIsNone(err)
        parsed, _ = R.parse_name(plan.new_path.name)
        self.assertEqual(parsed.id6, "aaaaaa")
        self.assertEqual(parsed.slug, "new-slug")

    def test_change_kind_validated(self):
        plan, err = RF.plan_mv(self.rroot, "aaaaaa", kind="not-a-kind")
        self.assertIsNone(plan)
        self.assertIn("unknown kind", err)


class ReferenceRewriteTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        self.rroot.mkdir(parents=True)
        # A citing file inside the scan root.
        (self.root / "DECISIONS.md").write_text(
            "See 20260701-alpha-00-aaaaaa-old.notes.md and bare id aaaaaa.\n",
            encoding="utf-8",
        )
        # A file OUTSIDE the scan root.
        outside = self.root / "somewhere-else"
        outside.mkdir()
        (outside / "note.md").write_text(
            "cite 20260701-alpha-00-aaaaaa-old.notes.md\n", encoding="utf-8"
        )
        self.outside_file = outside / "note.md"

    def test_full_name_rewritten_bare_id_untouched(self):
        renames = {
            "20260701-alpha-00-aaaaaa-old.notes.md": "20260710-grp-00-aaaaaa-old.notes.md"
        }
        edits = RF.plan_reference_rewrites(self.root, renames)
        self.assertTrue(any(e.file.name == "DECISIONS.md" for e in edits))
        RF.apply_reference_rewrites(edits)
        text = (self.root / "DECISIONS.md").read_text(encoding="utf-8")
        # Full old name replaced.
        self.assertIn("20260710-grp-00-aaaaaa-old.notes.md", text)
        self.assertNotIn("20260701-alpha-00-aaaaaa-old.notes.md", text)
        # Bare id6 still present and untouched.
        self.assertIn("bare id aaaaaa", text)

    def test_outside_scan_root_untouched(self):
        renames = {
            "20260701-alpha-00-aaaaaa-old.notes.md": "20260710-grp-00-aaaaaa-old.notes.md"
        }
        edits = RF.plan_reference_rewrites(self.root, renames)
        # No edit targets the outside file.
        self.assertFalse(any(e.file == self.outside_file for e in edits))
        self.assertIn(
            "20260701-alpha-00-aaaaaa-old.notes.md",
            self.outside_file.read_text(encoding="utf-8"),
        )


class DanglingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        # A present research file with id6 "aaaaaa".
        _mk_research(self.root, "20260701-alpha-00-aaaaaa-present.notes.md")

    def test_stale_id_flagged(self):
        (self.root / "DECISIONS.md").write_text(
            "cite to a gone doc zqzqzq here\n", encoding="utf-8"
        )
        danglers = RF.find_dangling_citations(self.root)
        self.assertTrue(any(d.id6 == "zqzqzq" for d in danglers))

    def test_stable_bare_id_not_flagged(self):
        (self.root / "DECISIONS.md").write_text(
            "cite the present doc aaaaaa here\n", encoding="utf-8"
        )
        danglers = RF.find_dangling_citations(self.root)
        self.assertFalse(any(d.id6 == "aaaaaa" for d in danglers))


class ScanRootTests(unittest.TestCase):
    def test_single_pinned_constant(self):
        self.assertIn("DECISIONS.md", RF.SCAN_ROOTS)
        self.assertIn(".agents/plans", RF.SCAN_ROOTS)
        self.assertIn(".agents/docs", RF.SCAN_ROOTS)

    def test_iter_scan_files_bounded_to_roots(self):
        root = Path(tempfile.mkdtemp())
        (root / "DECISIONS.md").write_text("x", encoding="utf-8")
        (root / ".agents" / "docs").mkdir(parents=True)
        (root / ".agents" / "docs" / "a.md").write_text("x", encoding="utf-8")
        stray = root / "stray"
        stray.mkdir()
        (stray / "b.md").write_text("x", encoding="utf-8")
        files = RF.iter_scan_files(root)
        names = {f.name for f in files}
        self.assertIn("DECISIONS.md", names)
        self.assertIn("a.md", names)
        self.assertNotIn("b.md", names)


if __name__ == "__main__":
    unittest.main()
