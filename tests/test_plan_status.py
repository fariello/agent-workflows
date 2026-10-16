"""Behavioral tests and live-corpus drift guard for plan status readiness (D52).

Guarantees that plan files carry a recognized readiness status agreeing with their
lifecycle directory, and that status_drift detects missing, unrecognized, or mismatched statuses.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import plans as plans_mod
from tests import support


def status_drift(plans_dir: Path) -> tuple[int, list[str], list[str]]:
    """Iterate disposition directories under plans_dir and report status drift.

    Scans disposition directories recursively (rglob), skips missing directories and
    any file named README.md, reads status with plans_mod.read_status(path), and returns:
    (examined, unrecognized, mismatched)
    - examined: count of plan files read.
    - unrecognized: '<rel>: Status=<value>' for files with None or LEGACY_GROUP status.
    - mismatched: '<rel>: dir=<sub_dir> Status=<value>' for other files in a DIR_TERMINAL
      directory whose status differs from the mapped terminal value.
    """
    examined = 0
    unrecognized: list[str] = []
    mismatched: list[str] = []

    for sub in plans_mod.DISPOSITION_DIRS:
        sub_dir = plans_dir / sub
        if not sub_dir.is_dir():
            continue
        for f in sorted(sub_dir.rglob("*.md")):
            if f.name == "README.md":
                continue
            examined += 1
            rel = f.relative_to(plans_dir).as_posix()
            status = plans_mod.read_status(f)
            if status is None or status == plans_mod.LEGACY_GROUP:
                unrecognized.append(f"{rel}: Status={status}")
            elif (
                sub in plans_mod.DIR_TERMINAL and status != plans_mod.DIR_TERMINAL[sub]
            ):
                mismatched.append(f"{rel}: dir={sub} Status={status}")

    return examined, unrecognized, mismatched


class TestSyntheticPlanStatus(unittest.TestCase):
    """Synthetic-tree tests for status_drift detection behavior."""

    def setUp(self) -> None:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.plans_dir = Path(td.name)

    def _write_plan(self, rel_path: str, status: str | None = None) -> Path:
        p = self.plans_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        if status is not None:
            content = f"# Plan\n\n- Status: {status}\n\n## Content\n"
        else:
            content = "# Plan\n\n## Content without status\n"
        p.write_text(content, encoding="utf-8")
        return p

    def test_clean_tree(self) -> None:
        # pending/ with draft, to-review, approved, auto-approved
        self._write_plan("pending/p1.ipd.md", "draft")
        self._write_plan("pending/p2.ipd.md", "to-review")
        self._write_plan("pending/p3.ipd.md", "approved")
        self._write_plan("pending/p4.ipd.md", "auto-approved")
        # executed/ with executed and legacy DONE
        self._write_plan("executed/p5.ipd.md", "executed")
        self._write_plan("executed/p6.ipd.md", "DONE")
        # superseded/ with superseded
        self._write_plan("superseded/p7.ipd.md", "superseded")
        # not-executed/ with not-executed
        self._write_plan("not-executed/p8.ipd.md", "not-executed")
        # reusable/ with reusable
        self._write_plan("reusable/p9.ipd.md", "reusable")
        # README.md with no status
        self._write_plan("pending/README.md", None)

        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 9)
        self.assertEqual(unrecognized, [])
        self.assertEqual(mismatched, [])

    def test_unrecognized_token(self) -> None:
        # A pending/ file with - Status: aproved appears in unrecognized
        self._write_plan("pending/p_typo.ipd.md", "aproved")
        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 1)
        self.assertTrue(
            any("pending/p_typo.ipd.md" in item for item in unrecognized),
            f"Expected pending/p_typo.ipd.md in unrecognized: {unrecognized}",
        )
        self.assertEqual(mismatched, [])

    def test_missing_status(self) -> None:
        # A pending/ file with no status line appears in unrecognized
        self._write_plan("pending/p_nostatus.ipd.md", None)
        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 1)
        self.assertTrue(
            any("pending/p_nostatus.ipd.md" in item for item in unrecognized),
            f"Expected pending/p_nostatus.ipd.md in unrecognized: {unrecognized}",
        )
        self.assertEqual(mismatched, [])

    def test_terminal_mismatch(self) -> None:
        # An executed/ file with - Status: approved appears in mismatched and not in unrecognized
        self._write_plan("executed/p_bad_terminal.ipd.md", "approved")
        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 1)
        self.assertEqual(unrecognized, [])
        self.assertTrue(
            any("executed/p_bad_terminal.ipd.md" in item for item in mismatched),
            f"Expected executed/p_bad_terminal.ipd.md in mismatched: {mismatched}",
        )

    def test_pending_not_mismatched(self) -> None:
        # A pending/ file with - Status: approved is not reported as mismatched
        self._write_plan("pending/p_ok.ipd.md", "approved")
        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 1)
        self.assertEqual(unrecognized, [])
        self.assertEqual(mismatched, [])

    def test_sharded_terminal_mismatch(self) -> None:
        # A sharded file executed/202609/<name>.ipd.md with - Status: approved appears in mismatched
        self._write_plan("executed/202609/sharded_plan.ipd.md", "approved")
        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 1)
        self.assertEqual(unrecognized, [])
        self.assertTrue(
            any("executed/202609/sharded_plan.ipd.md" in item for item in mismatched),
            f"Expected executed/202609/sharded_plan.ipd.md in mismatched: {mismatched}",
        )

    def test_examined_count_excludes_readme(self) -> None:
        # examined equals the number of non-README files written
        self._write_plan("pending/p1.ipd.md", "approved")
        self._write_plan("executed/p2.ipd.md", "executed")
        self._write_plan("pending/README.md", None)
        self._write_plan("executed/README.md", None)
        examined, unrecognized, mismatched = status_drift(self.plans_dir)
        self.assertEqual(examined, 2)
        self.assertEqual(unrecognized, [])
        self.assertEqual(mismatched, [])

    def test_auto_approved_normalization(self) -> None:
        self.assertEqual(plans_mod.normalize_status("auto-approved"), "auto-approved")
        self.assertEqual(plans_mod.normalize_status("AUTO-APPROVED"), "auto-approved")


class PlanStatusDriftGuard(unittest.TestCase):
    """Live-corpus drift guards asserting on repository plan status."""

    @pytest.mark.livecorpus
    def test_every_repository_plan_has_a_recognized_status(self) -> None:
        self.assertTrue(
            support.SOURCE_PLANS.is_dir(),
            f"SOURCE_PLANS is not a directory: {support.SOURCE_PLANS}",
        )
        examined, unrecognized, _ = status_drift(support.SOURCE_PLANS)
        self.assertGreater(
            examined, 0, "no plan files examined in repository plans tree"
        )
        self.assertEqual(
            unrecognized,
            [],
            f"plans with unrecognized Status: {unrecognized}",
        )

    @pytest.mark.livecorpus
    def test_repository_terminal_plan_status_matches_directory(self) -> None:
        self.assertTrue(
            support.SOURCE_PLANS.is_dir(),
            f"SOURCE_PLANS is not a directory: {support.SOURCE_PLANS}",
        )
        examined, _, mismatched = status_drift(support.SOURCE_PLANS)
        self.assertGreater(
            examined, 0, "no plan files examined in repository plans tree"
        )
        self.assertEqual(
            mismatched,
            [],
            f"terminal status/dir mismatches: {mismatched}",
        )


if __name__ == "__main__":
    unittest.main()
