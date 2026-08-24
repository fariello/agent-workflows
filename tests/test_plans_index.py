"""Tests for the plans manifest + browse-by-Set + --check (Set plans-adopter, Order 03).

Stdlib unittest, throwaway dirs. Verifies JSON completeness, the recursive scan (sharded plans
visible), the browse-by-Set view (grouping + Order + bound + singleton band), find filters,
determinism, and --check across the four drift classes (missing/invalid Id, name-vs-metadata
mismatch on a clustered name, stale view, dangling plan citation), with no false positive on an
un-migrated timestamp-stem name.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import plans_index as I


def _plan(
    root,
    disposition,
    name,
    *,
    plan_id,
    set_id=None,
    order=None,
    status="executed",
    date="20260701",
):
    d = root / ".agents" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    meta = [
        f"- Date: {date}",
        "- Kind: child",
        "- Concern: x.",
        "- Scope: x.",
        f"- Status: {status}",
        "- Author: t",
    ]
    if plan_id:
        meta.append(f"- Id: {plan_id}")
    if set_id:
        meta.append(f"- Set: {set_id}")
        meta.append(f"- Order: {order}")
    (d / name).write_text(
        "# IPD: x\n\n" + "\n".join(meta) + "\n\n## Goal\n\nx\n", encoding="utf-8"
    )
    return d / name


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.pdir = self.root / ".agents" / "plans"
        _plan(
            self.root,
            "executed",
            "20260701-set-a-00-aaaaaa-x.md",
            plan_id="aaaaaa",
            set_id="set-a",
            order=0,
        )
        _plan(
            self.root,
            "executed",
            "20260702-set-a-01-bbbbbb-y.md",
            plan_id="bbbbbb",
            set_id="set-a",
            order=1,
            date="20260702",
        )
        _plan(
            self.root,
            "pending",
            "20260703-set-b-00-cccccc-z.md",
            plan_id="cccccc",
            set_id="set-b",
            order=0,
            status="approved",
            date="20260703",
        )

    def test_json_has_every_plan(self):
        entries, drift = I.scan_plans(self.pdir)
        self.assertEqual(drift, [])
        self.assertEqual({e.plan_id for e in entries}, {"aaaaaa", "bbbbbb", "cccccc"})

    def test_recursive_scan_sees_sharded_plan(self):
        # A plan inside executed/YYYYMM/ keeps its top-level disposition and is included.
        _plan(
            self.root,
            "executed/202606",
            "20260601-set-a-02-dddddd-old.md",
            plan_id="dddddd",
            set_id="set-a",
            order=2,
            date="20260601",
        )
        entries, _ = I.scan_plans(self.pdir)
        sharded = [e for e in entries if e.plan_id == "dddddd"]
        self.assertEqual(len(sharded), 1)
        self.assertEqual(sharded[0].disposition, "executed")

    def test_index_md_groups_by_set_with_order(self):
        entries, _ = I.scan_plans(self.pdir)
        md = I.build_index_md(entries)
        self.assertIn("## set-a", md)
        self.assertIn("## set-b", md)
        # set-a members listed with their order tokens.
        self.assertIn("aaaaaa", md)
        self.assertIn("bbbbbb", md)

    def test_index_md_bound_and_singleton_band(self):
        _plan(
            self.root,
            "executed",
            "20260705-solo-plan-00-eeeeee-s.md",
            plan_id="eeeeee",
            date="20260705",
        )
        entries, _ = I.scan_plans(self.pdir)
        md = I.build_index_md(entries, limit=1)
        # Only 1 Set section shown; the rest is in JSON.
        self.assertEqual(md.count("\n## set-"), 1)

    def test_determinism(self):
        entries, _ = I.scan_plans(self.pdir)
        a = I.build_index_json(entries) + I.build_index_md(entries)
        entries2, _ = I.scan_plans(self.pdir)
        b = I.build_index_json(entries2) + I.build_index_md(entries2)
        self.assertEqual(a, b)


class FindTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.pdir = self.root / ".agents" / "plans"
        _plan(
            self.root,
            "executed",
            "20260701-set-a-00-aaaaaa-x.md",
            plan_id="aaaaaa",
            set_id="set-a",
            order=0,
        )
        _plan(
            self.root,
            "pending",
            "20260703-set-b-00-cccccc-z.md",
            plan_id="cccccc",
            set_id="set-b",
            order=0,
            status="approved",
            date="20260703",
        )

    def test_find_by_set(self):
        entries, _ = I.scan_plans(self.pdir)
        self.assertEqual(
            [e.plan_id for e in I.query(entries, set_id="set-a")], ["aaaaaa"]
        )

    def test_find_by_disposition(self):
        entries, _ = I.scan_plans(self.pdir)
        self.assertEqual(
            [e.plan_id for e in I.query(entries, disposition="pending")], ["cccccc"]
        )


class CheckDriftTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.pdir = self.root / ".agents" / "plans"
        _plan(
            self.root,
            "executed",
            "20260701-set-a-00-aaaaaa-x.md",
            plan_id="aaaaaa",
            set_id="set-a",
            order=0,
        )

    def _regen(self):
        entries, _ = I.scan_plans(self.pdir)
        (self.pdir / I.INDEX_JSON).write_text(
            I.build_index_json(entries), encoding="utf-8"
        )
        (self.pdir / I.INDEX_MD).write_text(I.build_index_md(entries), encoding="utf-8")

    def test_clean_after_regen(self):
        self._regen()
        self.assertEqual(I.check_drift(self.root, self.pdir), [])

    def test_missing_id_flagged(self):
        _plan(
            self.root,
            "executed",
            "20260702-set-a-01-nope-y.md",
            plan_id=None,
            set_id="set-a",
            order=1,
        )
        drift = I.check_drift(self.root, self.pdir)
        self.assertTrue(any(d.rule == "id-missing" for d in drift))

    def test_name_metadata_mismatch_on_clustered_name(self):
        # A clustered name whose id6 disagrees with metadata Id.
        _plan(
            self.root,
            "executed",
            "20260702-set-a-01-zzzzzz-y.md",
            plan_id="bbbbbb",
            set_id="set-a",
            order=1,
        )
        drift = I.check_drift(self.root, self.pdir)
        self.assertTrue(any(d.rule == "name-metadata-mismatch" for d in drift))

    def test_unmigrated_timestamp_name_not_flagged(self):
        # Old-style YYYYMMDD-HHMM-NN-slug.md is NOT a clustered name -> no name mismatch.
        _plan(
            self.root,
            "executed",
            "20260702-1030-01-old-style.md",
            plan_id="bbbbbb",
            set_id="set-a",
            order=1,
        )
        self._regen()
        drift = I.check_drift(self.root, self.pdir)
        self.assertFalse(any(d.rule == "name-metadata-mismatch" for d in drift))

    def test_stale_index_flagged(self):
        self._regen()
        (self.pdir / I.INDEX_MD).write_text("stale", encoding="utf-8")
        drift = I.check_drift(self.root, self.pdir)
        self.assertTrue(any(d.rule == "stale-index" for d in drift))

    def test_dangling_plan_citation_flagged(self):
        self._regen()
        (self.root / "DECISIONS.md").write_text(
            "see PLAN-zqzqzq for that\n", encoding="utf-8"
        )
        drift = I.check_drift(self.root, self.pdir)
        self.assertTrue(any(d.rule == "dangling-citation" for d in drift))


class RunIndexOutputTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.pdir = self.root / ".agents" / "plans"
        _plan(
            self.root,
            "executed",
            "20260701-set-a-00-aaaaaa-x.md",
            plan_id="aaaaaa",
            set_id="set-a",
            order=0,
        )

    def test_run_index_change_detection_and_output(self):
        import argparse
        import io
        from contextlib import redirect_stdout

        args = argparse.Namespace(
            dir=str(self.root), limit=None, check=False, quiet=False, no_color=True
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = I.run_index(args)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("wrote", out)
        self.assertIn(".agents/plans/INDEX.json, INDEX.md", out)
        self.assertIn("(1 plans)", out)

        # Second run: up to date
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = I.run_index(args)
        self.assertEqual(rc2, 0)
        out2 = buf2.getvalue()
        self.assertIn("up to date", out2)
        self.assertIn(".agents/plans/INDEX.json, INDEX.md", out2)


class DefaultLimitTests(unittest.TestCase):
    def test_default(self):
        self.assertEqual(I.DEFAULT_INDEX_LIMIT, 40)


if __name__ == "__main__":
    unittest.main()
