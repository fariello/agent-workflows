"""Parity tests between aw check and aw doctor collision populations (collpop t0jyb2).

Asserts that aw check all and aw doctor report the identical set of collision findings
(check.id6-collision, check.id6-identity-slot, check.setid-collision) on a tree at default
and widened scope, that identity findings are never demoted into executed_warnings, and
that setid collisions on retired records are hidden by default and surfaced under widening.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import doctor
from tests.test_check_engine import _plan_text, _tree, _walk_text

COLLISION_RULES = {
    "check.id6-collision",
    "check.id6-identity-slot",
    "check.setid-collision",
}


def _rel(loc: str, root: Path) -> str:
    p = Path(loc)
    if p.is_absolute() and p.is_relative_to(root):
        return str(p.relative_to(root))
    return loc


def _extract_collisions(drifts, root: Path) -> set[tuple[str, str]]:
    return {
        (_rel(d.location, root), d.rule) for d in drifts if d.rule in COLLISION_RULES
    }


class CollisionPopulationParityTests(unittest.TestCase):
    """Pin the collision population parity across aw check and aw doctor."""

    def setUp(self):
        # Fixture tree containing:
        # 1) a live pending plan
        # 2) an executed plan aaa111
        # 3) a walkthrough whose identity slot reuses aaa111 while declaring no - Id:
        # 4) two executed plans that both declare - Id: ccc333
        # 5) two executed plans sharing setid 'other' with different descriptives
        self.files = [
            (
                ".aw/records/plans/pending/20260101-demo-01-live01-live.ipd.md",
                _plan_text("live01", "demo", status="approved"),
            ),
            (
                ".aw/records/plans/executed/20260101-demo-01-aaa111-plan-a.ipd.md",
                _plan_text("aaa111", "demo", status="executed"),
            ),
            (
                ".aw/records/walkthroughs/20260101-aaa111-01-aaa111-walk.walkthrough.md",
                _walk_text(id6=None),
            ),
            (
                ".aw/records/plans/executed/20260101-demo-02-ccc333-plan-c1.ipd.md",
                _plan_text("ccc333", "demo", status="executed"),
            ),
            (
                ".aw/records/plans/executed/20260101-demo-03-ccc333-plan-c2.ipd.md",
                _plan_text("ccc333", "demo", status="executed"),
            ),
            (
                ".aw/records/plans/executed/20260101-other-01-oth001-plan-o1.ipd.md",
                _plan_text("oth001", "other", desc="first", status="executed"),
            ),
            (
                ".aw/records/plans/executed/20260101-other-02-oth002-plan-o2.ipd.md",
                _plan_text("oth002", "other", desc="second", status="executed"),
            ),
        ]
        self.root = _tree(self.files)

    def test_collision_population_parity(self):
        check_default = _extract_collisions(
            ce.check_types(self.root, ["all"]), self.root
        )
        doc_default = _extract_collisions(
            doctor.probe_artifacts(self.root).all_drift, self.root
        )

        # (1) default aw check equals default doctor
        diff_doc_extra = doc_default - check_default
        diff_check_extra = check_default - doc_default
        self.assertEqual(
            check_default,
            doc_default,
            f"Default scope collision divergence: doctor has extra {diff_doc_extra}, check has extra {diff_check_extra}",
        )

        # (2) widened aw check equals widened doctor
        check_widened = _extract_collisions(
            ce.check_types(self.root, ["all"], include_retired=True), self.root
        )
        doc_widened = _extract_collisions(
            doctor.probe_artifacts(self.root, include_executed=True).all_drift,
            self.root,
        )
        diff_doc_w_extra = doc_widened - check_widened
        diff_check_w_extra = check_widened - doc_widened
        self.assertEqual(
            check_widened,
            doc_widened,
            f"Widened scope collision divergence: doctor has extra {diff_doc_w_extra}, check has extra {diff_check_w_extra}",
        )

        # (3) identity findings are present in BOTH default sets; retired setid conflict absent by default and present in widened
        slot_finding = (
            ".aw/records/walkthroughs/20260101-aaa111-01-aaa111-walk.walkthrough.md",
            "check.id6-identity-slot",
        )
        id6_coll_finding = (
            ".aw/records/plans/executed/20260101-demo-03-ccc333-plan-c2.ipd.md",
            "check.id6-collision",
        )
        setid_coll_finding = (
            ".aw/records/plans/executed/20260101-other-01-oth001-plan-o1.ipd.md",
            "check.setid-collision",
        )

        self.assertIn(
            slot_finding,
            check_default,
            f"Slot finding {slot_finding} missing from check_default",
        )
        self.assertIn(
            slot_finding,
            doc_default,
            f"Slot finding {slot_finding} missing from doc_default",
        )
        self.assertIn(
            id6_coll_finding,
            check_default,
            f"id6 collision {id6_coll_finding} missing from check_default",
        )
        self.assertIn(
            id6_coll_finding,
            doc_default,
            f"id6 collision {id6_coll_finding} missing from doc_default",
        )

        self.assertNotIn(
            setid_coll_finding,
            check_default,
            f"Retired setid collision {setid_coll_finding} unexpectedly in check_default",
        )
        self.assertNotIn(
            setid_coll_finding,
            doc_default,
            f"Retired setid collision {setid_coll_finding} unexpectedly in doc_default",
        )

        self.assertIn(
            setid_coll_finding,
            check_widened,
            f"Retired setid collision {setid_coll_finding} missing from check_widened",
        )
        self.assertIn(
            setid_coll_finding,
            doc_widened,
            f"Retired setid collision {setid_coll_finding} missing from doc_widened",
        )

        # (4) no identity finding appears in executed_warnings
        doc_executed_warnings = _extract_collisions(
            doctor.probe_artifacts(self.root).executed_warnings, self.root
        )
        demoted_identity = {
            (p, r)
            for (p, r) in doc_executed_warnings
            if r in ("check.id6-collision", "check.id6-identity-slot")
        }
        self.assertEqual(
            demoted_identity,
            set(),
            f"Identity findings unexpectedly demoted into executed_warnings in doctor: {demoted_identity}",
        )
