"""Tests for plans regroup/rename + reference integrity (Set plans-adopter, Order 04).

Stdlib unittest, git-backed throwaway repos (renames use git mv). Verifies set-assign (Set/Order
metadata + optional clustering rename, stable Id), mv, and the reference updater across the three
citation forms (full-name, bare-stem, range) driven by an explicit plan old->new map, INCLUDING the
critical guard that a spec-only bare stem sharing the YYYYMMDD-HHMM-NN grammar is NOT rewritten.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import plans_refs as R


def _init_git(root: Path):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)


def _plan(
    root, disposition, name, *, plan_id, date="20260701", set_id=None, order=None
):
    d = root / ".agents" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    meta = [
        f"- Date: {date}",
        "- Kind: child",
        "- Concern: x.",
        "- Scope: x.",
        "- Status: executed",
        "- Author: t",
        f"- Id: {plan_id}",
    ]
    if set_id:
        meta += [f"- Set: {set_id}", f"- Order: {order}"]
    (d / name).write_text(
        "# IPD: x\n\n" + "\n".join(meta) + "\n\n## Goal\n\nx\n", encoding="utf-8"
    )
    return d / name


class SetAssignTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.pdir = self.root / ".agents" / "plans"
        _plan(self.root, "executed", "20260701-1030-01-alpha.md", plan_id="aaaaaa")
        _plan(
            self.root,
            "executed",
            "20260702-1145-02-beta.md",
            plan_id="bbbbbb",
            date="20260702",
        )

    def test_metadata_only_assign(self):
        plans, err = R.plan_set_assign(
            self.pdir, ["aaaaaa", "bbbbbb"], "grp", start_order=0, rename=False
        )
        self.assertIsNone(err)
        R.apply_renames(self.root, self.pdir, plans, "grp", apply=True)
        t = (self.pdir / "executed" / "20260701-1030-01-alpha.md").read_text()
        self.assertIn("- Set: grp", t)
        self.assertIn("- Order: 0", t)
        self.assertIn("- Id: aaaaaa", t)  # id unchanged

    def test_rename_clusters_and_keeps_id(self):
        plans, err = R.plan_set_assign(
            self.pdir, ["aaaaaa"], "grp", start_order=0, rename=True
        )
        self.assertIsNone(err)
        R.apply_renames(self.root, self.pdir, plans, "grp", apply=True)
        moved = list((self.pdir / "executed").glob("*aaaaaa*.md"))
        self.assertEqual(len(moved), 1)
        self.assertTrue(moved[0].name.startswith("20260701-grp-00-aaaaaa-"))
        self.assertIn("- Id: aaaaaa", moved[0].read_text())

    def test_unknown_id_errors(self):
        plans, err = R.plan_set_assign(self.pdir, ["zzzzzz"], "grp")
        self.assertIsNone(plans)
        self.assertIn("no plan has Id", err)


class ReferenceRewriteTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.pdir = self.root / ".agents" / "plans"
        _plan(self.root, "executed", "20260701-1030-01-alpha.md", plan_id="aaaaaa")
        # A spec sharing the bare-stem grammar (must NOT be rewritten).
        specs = self.root / ".agents" / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "20260701-1030-01-some-spec.spec.md").write_text(
            "spec body\n", encoding="utf-8"
        )
        # DECISIONS cites the plan three ways + cites the spec by bare stem.
        (self.root / "DECISIONS.md").write_text(
            "Full: 20260701-1030-01-alpha.md\n"
            "Bare plan stem: 20260701-1030-01 did the thing.\n"
            "Range: `20260701-1030-00`..`01` covers it.\n"
            "Spec cite (must NOT change): 20260701-1030-01-some-spec.spec.md\n",
            encoding="utf-8",
        )

    def test_three_forms_rewritten_spec_untouched(self):
        # Rename the plan; build the plan-only name map and rewrite citations.
        plans, _ = R.plan_set_assign(
            self.pdir, ["aaaaaa"], "grp", start_order=1, rename=True
        )
        name_map = {
            p.old_path.name: p.new_path.name for p in plans if p.old_path != p.new_path
        }
        edits = R.plan_reference_rewrites(self.root, name_map, self.pdir)
        R.apply_reference_rewrites(edits)
        text = (self.root / "DECISIONS.md").read_text()
        new_name = plans[0].new_path.name
        new_stem = new_name[:-3]
        # (a) full filename rewritten
        self.assertIn(new_name, text)
        self.assertNotIn("20260701-1030-01-alpha.md", text)
        # (b) bare plan stem rewritten to the new stem
        self.assertIn(new_stem, text)
        # (d) the SPEC full filename is UNCHANGED (its bare stem was shared, but the plan map only
        # rewrites the plan; the spec's full name is a different string and stays).
        self.assertIn("20260701-1030-01-some-spec.spec.md", text)

    def test_bare_stem_not_rewritten_when_not_a_plan(self):
        # A name_map that does NOT include a given stem must leave that stem alone.
        edits = R.plan_reference_rewrites(self.root, {}, self.pdir)
        self.assertEqual(edits, [])


if __name__ == "__main__":
    unittest.main()
