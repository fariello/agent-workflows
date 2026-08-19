"""Tests for awhistory Order 03: idempotent inline->sidecar migration (EXCLUDING plans) + read verb."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import record_history as rh


class MigrateInlineHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.specs = self.root / ".aw" / "records" / "specs"
        self.specs.mkdir(parents=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "executed"
        self.plans.mkdir(parents=True)
        # a spec with 3 inline history records + an id6
        (self.specs / "20260101-1200-01-x.spec.md").write_text(
            "# Spec\n\n- Id: aaa111\n- Status: draft\n\n## Workflow history\n"
            "- 2026-01-01 draft (t): a\n- 2026-01-02 to-review (t): b\n- 2026-01-03 reviewed (t): c\n",
            encoding="utf-8",
        )
        # a plan with an executed history line that MUST be preserved (IPD-S405)
        self.plan = self.plans / "20260101-demo-01-ppp111-x.ipd.md"
        self.plan.write_text(
            "# IPD\n\n- Id: ppp111\n- Status: executed\n\n## Workflow history\n"
            "- 2026-01-01 draft (t): created\n- 2026-01-05 executed (t): done\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_preview_writes_nothing(self) -> None:
        n = rh.migrate_inline_history(self.root, apply=False)
        self.assertEqual(n, 3)  # the 3 spec records
        self.assertEqual(rh.read_all(self.root), [])  # nothing written
        # spec inline history untouched in preview
        self.assertIn(
            "- 2026-01-01 draft",
            (self.specs / "20260101-1200-01-x.spec.md").read_text(),
        )

    def test_apply_folds_and_slims_excluding_plans(self) -> None:
        n = rh.migrate_inline_history(self.root, apply=True)
        self.assertEqual(n, 3)
        recs = rh.read_for(self.root, "aaa111")
        self.assertEqual([r["message"] for r in recs], ["a", "b", "c"])
        # spec inline slimmed to latest-one
        spec_text = (self.specs / "20260101-1200-01-x.spec.md").read_text()
        after = spec_text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        self.assertEqual(inline, ["- 2026-01-03 reviewed (t): c"])
        # PLANS UNTOUCHED: the executed plan keeps its FULL inline history (IPD-S405) and is not in sidecar
        plan_text = self.plan.read_text()
        self.assertIn("- 2026-01-05 executed (t): done", plan_text)
        self.assertIn("- 2026-01-01 draft (t): created", plan_text)
        self.assertEqual(rh.read_for(self.root, "ppp111"), [])

    def test_idempotent(self) -> None:
        rh.migrate_inline_history(self.root, apply=True)
        again = rh.migrate_inline_history(self.root, apply=True)
        self.assertEqual(again, 0)  # nothing new folded on re-run


if __name__ == "__main__":
    unittest.main()
