"""Tests for the plans scan + find + drift check (Set plans-adopter, Order 03).

Stdlib unittest, throwaway dirs. Verifies scan completeness, the recursive scan (sharded plans
visible), find filters, and check_drift across the three drift classes (missing/invalid Id,
name-vs-metadata mismatch on a clustered name, dangling plan citation), with no false positive on
an un-migrated timestamp-stem name, and no finding for a stale or missing INDEX file (plan w819as).
No INDEX file is written or read: the SQLite metadata cache replaced them (spec 4sd62s 4.5).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import plans_index as I
from tests.record_builder import RecordBuilder

import pytest

pytestmark = pytest.mark.core


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
    when = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) == 8 else date
    raw_fields: dict[str, str | None] = {"Date": date}
    if plan_id is None:
        raw_fields["Id"] = None
    if set_id is None:
        raw_fields["Set"] = None
        raw_fields["Order"] = None
    elif order is None:
        raw_fields["Order"] = None
    text = RecordBuilder().plan(
        id6=plan_id or "tmp001",
        title="x",
        when=when,
        plan_role="child",
        set=set_id or "demo",
        order=order if order is not None else 1,
        status=status,
        author="t",
        body="## Goal\n\nx",
        raw_fields=raw_fields,
        text_only=True,
    )
    (d / name).write_text(text, encoding="utf-8")
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

    def test_missing_id_flagged(self):
        _plan(
            self.root,
            "pending",
            "20260702-set-a-01-nope-y.md",
            plan_id=None,
            set_id="set-a",
            order=1,
        )
        drift = I.check_drift(self.root, self.pdir)
        self.assertTrue(any(d.rule == "id-missing" for d in drift))

    def test_missing_id_in_terminal_plan_not_flagged(self):
        _plan(
            self.root,
            "executed",
            "20260702-set-a-01-nope-y.md",
            plan_id=None,
            set_id="set-a",
            order=1,
        )
        drift = I.check_drift(self.root, self.pdir)
        self.assertFalse(any(d.rule == "id-missing" for d in drift))

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
        drift = I.check_drift(self.root, self.pdir)
        self.assertFalse(any(d.rule == "name-metadata-mismatch" for d in drift))

    def test_stale_index_file_is_not_drift(self):
        # Plan w819as (spec 4sd62s 4.5): the INDEX-file drift rules are deleted with the INDEX files.
        # A leftover manifest with arbitrary bytes is no longer a finding at all.
        (self.pdir / "INDEX.json").write_text("[]\n", encoding="utf-8")
        (self.pdir / "INDEX.md").write_text("stale", encoding="utf-8")
        drift = I.check_drift(self.root, self.pdir)
        self.assertEqual(drift, [])
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_missing_index_file_is_not_drift(self):
        """A never-generated manifest is the normal state of a fresh clone or worktree.

        Plan w819as (spec 4sd62s 4.5): the SQLite metadata cache replaced the INDEX files, so an
        absent manifest produces no finding and does not fail the gate.
        """
        for name in ("INDEX.json", "INDEX.md"):
            self.assertFalse((self.pdir / name).exists(), f"fixture sanity: {name}")
        drift = I.check_drift(self.root, self.pdir)
        self.assertEqual(drift, [])
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_dangling_plan_citation_flagged(self):
        (self.root / "DECISIONS.md").write_text(
            "see PLAN-zqzqzq for that\n", encoding="utf-8"
        )
        drift = I.check_drift(self.root, self.pdir)
        self.assertTrue(any(d.rule == "dangling-citation" for d in drift))


if __name__ == "__main__":
    unittest.main()
