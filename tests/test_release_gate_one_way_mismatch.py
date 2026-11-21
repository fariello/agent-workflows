"""Behavioral tests asserting check_release_gate_consistency is one-way for From-Backlog carriers.

Plan k9niwu (backlog hybluq): restore behavioral coverage that check_release_gate_consistency
reports zero findings for a gated carrier under an ungated item, while still reporting findings
for the forward direction (gated item with ungated or differently-gated carrier).

This property was lost when tests/test_bug_gate_check.py was deleted in 19313eed.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Optional

from agent_workflows import check_engine
from tests import support
from tests.record_builder import RecordBuilder

RULE_MISMATCH = "check.from-backlog-gate-mismatch"


def _release(root: Path) -> Path:
    d = root / ".aw" / "records" / "releases"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "20260901-rel001-01-rel001-v1.release.md"
    p.write_text(
        RecordBuilder().release(
            version="1.0.0",
            id6="rel001",
            status="planned",
            summary="Test release",
            text_only=True,
        ),
        encoding="utf-8",
    )
    return p


def _item(
    root: Path,
    id6: str,
    *,
    status: str = "graduated",
    work_kind: str = "bug",
    gate: Optional[str] = None,
) -> Path:
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-tst-01-{id6}-a-test-item.backlog.md"
    extra: dict[str, str] = {}
    if gate:
        extra["blocks_release"] = gate
    p.write_text(
        RecordBuilder().backlog(
            id6=id6,
            status=status,
            set="tst",
            priority="medium",
            work_kind=work_kind,
            summary="A test item.",
            when="2026-09-18",
            history=["- 2026-09-18 created (test): A test item."],
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
    return p


def _plan(
    root: Path,
    id6: str,
    backlog_id6: str,
    *,
    gate: Optional[str] = None,
    disposition: str = "pending",
    status: str = "to-review",
) -> Path:
    d = root / ".aw" / "records" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-tst-01-{id6}-a-test-plan.ipd.md"
    extra: dict[str, str] = {}
    if gate:
        extra["blocks_release"] = gate
    p.write_text(
        RecordBuilder().plan(
            title="A test plan",
            when="2026-09-18",
            plan_role="child",
            scope_paths="x",
            item_dependencies="none",
            from_backlog=backlog_id6,
            status=status,
            set="tst",
            order=1,
            author="test",
            id6=id6,
            history=["- 2026-09-18 created (test): Testing."],
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
    return p


def _spec(
    root: Path, id6: str, backlog_id6: str, *, gate: Optional[str] = None
) -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-{id6}-01-{id6}-a-test-spec.spec.md"
    extra: dict[str, str] = {}
    if gate:
        extra["blocks_release"] = gate
    p.write_text(
        RecordBuilder().spec(
            title="A test spec",
            when="2026-09-18",
            status="approved",
            id6=id6,
            from_backlog=backlog_id6,
            history=["- 2026-09-18 created (test): Testing."],
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
    return p


class ReleaseGateOneWayMismatchTests(unittest.TestCase):
    def setUp(self):
        support.declare_execution_role(self)

    def test_gated_carrier_under_ungated_item_is_not_a_mismatch(self):
        """Assert zero check.from-backlog-gate-mismatch findings for a live gated plan
        or spec carrier under an ungated backlog item."""
        cases = [
            ("plan", "pending_plan_gated_under_ungated_item"),
            ("spec", "spec_gated_under_ungated_item"),
        ]
        for carrier_type, case_name in cases:
            with self.subTest(carrier_type=carrier_type, case=case_name):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    _release(root)
                    _item(
                        root, "item01", status="graduated", work_kind="bug", gate=None
                    )
                    if carrier_type == "plan":
                        _plan(
                            root,
                            "plan01",
                            "item01",
                            gate="next",
                            disposition="pending",
                            status="to-review",
                        )
                    else:
                        _spec(root, "spec01", "item01", gate="next")

                    drift = check_engine.check_release_gate_consistency(root)
                    rules = [d.rule for d in drift]
                    self.assertNotIn(
                        "check.from-backlog-gate-mismatch",
                        rules,
                        f"Expected zero '{RULE_MISMATCH}' findings for gated {carrier_type} under ungated item, got {rules}",
                    )

    def test_forward_direction_still_fires(self):
        """Anti-vacuity tests asserting the rule still fires for forward-direction mismatches."""
        # (a) gated item (next) with a live pending/ plan carrying NO gate
        with self.subTest(case="a_ungated_plan"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td).resolve()
                _release(root)
                _item(root, "item01", status="graduated", work_kind="bug", gate="next")
                plan_p = _plan(
                    root,
                    "plan01",
                    "item01",
                    gate=None,
                    disposition="pending",
                    status="to-review",
                )
                drift = check_engine.check_release_gate_consistency(root)
                mismatches = [
                    d for d in drift if d.rule == "check.from-backlog-gate-mismatch"
                ]
                self.assertEqual(len(mismatches), 1)
                self.assertEqual(mismatches[0].location, str(plan_p))
                self.assertIn("item01", mismatches[0].detail)

        # (b) gated item (next) with a live plan gated to a DIFFERENT, unresolvable release string
        with self.subTest(case="b_differently_gated_plan"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td).resolve()
                _release(root)
                _item(root, "item02", status="graduated", work_kind="bug", gate="next")
                plan_p = _plan(
                    root,
                    "plan02",
                    "item02",
                    gate="v9z9z9",
                    disposition="pending",
                    status="to-review",
                )
                drift = check_engine.check_release_gate_consistency(root)
                mismatches = [
                    d for d in drift if d.rule == "check.from-backlog-gate-mismatch"
                ]
                self.assertEqual(len(mismatches), 1)
                self.assertEqual(mismatches[0].location, str(plan_p))
                self.assertIn("item02", mismatches[0].detail)

        # (c) gated item with a matching-gated live plan and assert zero findings
        with self.subTest(case="c_matching_plan_zero_findings"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td).resolve()
                _release(root)
                _item(root, "item03", status="graduated", work_kind="bug", gate="next")
                _plan(
                    root,
                    "plan03",
                    "item03",
                    gate="next",
                    disposition="pending",
                    status="to-review",
                )
                drift = check_engine.check_release_gate_consistency(root)
                mismatches = [
                    d for d in drift if d.rule == "check.from-backlog-gate-mismatch"
                ]
                self.assertEqual(len(mismatches), 0)

        # (d) gated item (next) with a SPEC carrier gated to v9z9z9, built with the SAME spec helper E-01(b) uses
        with self.subTest(case="d_differently_gated_spec"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td).resolve()
                _release(root)
                _item(root, "item04", status="graduated", work_kind="bug", gate="next")
                spec_p = _spec(root, "spec04", "item04", gate="v9z9z9")
                drift = check_engine.check_release_gate_consistency(root)
                mismatches = [
                    d for d in drift if d.rule == "check.from-backlog-gate-mismatch"
                ]
                self.assertEqual(len(mismatches), 1)
                self.assertEqual(mismatches[0].location, str(spec_p))
                self.assertIn("item04", mismatches[0].detail)
                self.assertIn("spec", mismatches[0].detail)


if __name__ == "__main__":
    unittest.main()
