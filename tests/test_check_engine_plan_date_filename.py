"""Tests for plan filename date vs body - Date: metadata check (wyk11f).

Covers:
1. Defect row: filename date disagrees with body Date -> flags check.plan-date-filename-mismatch.
2. Agreeing control: filename date agrees with body Date -> no finding.
3. Set-canonical row: multi-member Set with differing leading dates, each internally consistent -> no finding.
4. No-date row: missing or placeholder Date (<YYYY-MM-DD>) -> skipped / no finding.
5. Retired-reach row: disagreeing plan in executed/ -> found with include_retired=True, absent without it.
6. Entry-point row: check_content(root, "plans", include_untracked=True) surfaces the finding.
7. Non-vacuity control: out-of-vocab Work-Kind in same fixture is reported by check_plan_work_kind.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine as ce


def _check_date_mismatch(
    repo_root: Path,
    include_untracked: bool = False,
    include_retired: bool = False,
) -> list[_core.Drift]:
    fn = getattr(ce, "check_plan_date_filename_mismatch", None)
    if fn is None:
        return []
    return fn(
        repo_root,
        include_untracked=include_untracked,
        include_retired=include_retired,
    )


def _build_plan(
    *,
    id6: str = "aaa111",
    date: str | None = "2026-10-01",
    status: str = "pending",
    work_kind: str = "feature",
    priority: str = "low",
    setid: str = "probeset",
    order: int = 1,
) -> str:
    lines = [
        f"# IPD: Probe {id6}",
        "",
    ]
    if date is not None:
        lines.append(f"- Date: {date}")
    lines.extend(
        [
            "- Kind: child",
            "- Concern: Probe concern.",
            "- Scope: Probe scope.",
            "- Scope-Paths: agent_workflows/check_engine.py",
            "- Item-Dependencies: none",
            f"- Status: {status}",
            f"- Work-Kind: {work_kind}",
            f"- Priority: {priority}",
            f"- Set: {setid}",
            f"- Order: {order}",
            "- Highest E allocated: 01",
            "- Author: test-author",
            f"- Id: {id6}",
            "",
            "## Workflow history",
            f"- 2026-10-01 {status} (test-author): created.",
            "",
            "## Goal",
            "Probe goal.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "- [ ] E-01 Probe item.",
            "  - Depends on: none",
            "  - Expected outcome: done",
            "  - Execution state: pending",
            "",
            "## Project conventions discovered (Step 0)",
            "- Convention.",
            "",
            "## Findings",
            "| Id | Finding | Evidence |",
            "|---|---|---|",
            "| F-01 | Finding. | Evidence. |",
            "",
            "## Proposed changes (ordered, validatable)",
            "1. Probe change.",
            "",
            "## Deferred / out of scope (with reason)",
            "- None.",
            "",
            "## Scope check",
            "- Over-scope: none.",
            "",
            "## Required tests / validation",
            "- Probe test.",
            "",
            "## Spec / documentation sync",
            "None.",
            "",
            "## Open questions",
            "### OQ-01: None.",
            "- Blocking: no",
            "- Status: resolved",
            "- Owner: author",
            "- Resolution or deferral rationale: done.",
            "",
            "## Validation and cross-check (verify before reporting done)",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: done",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "- Size assessment: standard",
            "- Cohesion rationale: not required",
        ]
    )
    return "\n".join(lines) + "\n"


class CheckEnginePlanDateFilenameTests(unittest.TestCase):
    """Behavioral tests for check.plan-date-filename-mismatch."""

    def test_defect_row_filename_date_mismatch_reported(self) -> None:
        """(1) DEFECT ROW: A plan named 20260101-... whose body reads 2026-10-01 yields the finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            defect_path = pending / "20260101-probeset-01-aaa111-probe.ipd.md"
            defect_path.write_text(
                _build_plan(id6="aaa111", date="2026-10-01"), encoding="utf-8"
            )

            drifts = _check_date_mismatch(root, include_untracked=True)
            mismatch_drifts = [
                d
                for d in drifts
                if d.rule == "check.plan-date-filename-mismatch"
                and d.location == str(defect_path)
            ]
            self.assertEqual(
                len(mismatch_drifts),
                1,
                f"Expected check.plan-date-filename-mismatch for {defect_path}, got: {drifts}",
            )

    def test_agreeing_control_no_finding(self) -> None:
        """(2) AGREEING CONTROL: A plan named 20261001-... with body 2026-10-01 yields NO finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan_path = pending / "20261001-probeset-01-aaa111-probe.ipd.md"
            plan_path.write_text(
                _build_plan(id6="aaa111", date="2026-10-01"), encoding="utf-8"
            )

            drifts = _check_date_mismatch(root, include_untracked=True)
            mismatch_drifts = [
                d for d in drifts if d.rule == "check.plan-date-filename-mismatch"
            ]
            self.assertEqual(
                mismatch_drifts,
                [],
                f"Expected no check.plan-date-filename-mismatch, got: {mismatch_drifts}",
            )

    def test_set_canonical_row_differing_dates_within_set_no_finding(
        self,
    ) -> None:
        """(3) SET-CANONICAL ROW: Two plans in one Set with different leading dates, each self-consistent, yield NO finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan1 = pending / "20260712-probeset-01-aaa111-probe1.ipd.md"
            plan1.write_text(
                _build_plan(
                    id6="aaa111",
                    date="2026-07-12",
                    setid="probeset",
                    order=1,
                ),
                encoding="utf-8",
            )
            plan2 = pending / "20260915-probeset-02-bbb222-probe2.ipd.md"
            plan2.write_text(
                _build_plan(
                    id6="bbb222",
                    date="2026-09-15",
                    setid="probeset",
                    order=2,
                ),
                encoding="utf-8",
            )

            drifts = _check_date_mismatch(root, include_untracked=True)
            mismatch_drifts = [
                d for d in drifts if d.rule == "check.plan-date-filename-mismatch"
            ]
            self.assertEqual(
                mismatch_drifts,
                [],
                f"Expected no check.plan-date-filename-mismatch for self-consistent multi-date set, got: {mismatch_drifts}",
            )

    def test_no_date_row_missing_or_placeholder_date_skipped(self) -> None:
        """(4) NO-DATE ROW: Clustered plans with no Date or placeholder Date yield NO finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan_no_date = pending / "20261001-probeset-01-aaa111-nodate.ipd.md"
            plan_no_date.write_text(
                _build_plan(id6="aaa111", date=None), encoding="utf-8"
            )
            plan_placeholder = (
                pending / "20261001-probeset-02-bbb222-placeholder.ipd.md"
            )
            plan_placeholder.write_text(
                _build_plan(id6="bbb222", date="<YYYY-MM-DD>"),
                encoding="utf-8",
            )

            drifts = _check_date_mismatch(root, include_untracked=True)
            mismatch_drifts = [
                d for d in drifts if d.rule == "check.plan-date-filename-mismatch"
            ]
            self.assertEqual(
                mismatch_drifts,
                [],
                f"Expected no check.plan-date-filename-mismatch for missing/placeholder dates, got: {mismatch_drifts}",
            )

    def test_retired_reach_executed_plan_only_found_with_include_retired(
        self,
    ) -> None:
        """(5) RETIRED-REACH ROW: Disagreeing plan in executed/ yields finding with include_retired=True and none without."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executed = root / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            plan_executed = executed / "20260101-probeset-01-aaa111-probe.ipd.md"
            plan_executed.write_text(
                _build_plan(id6="aaa111", date="2026-10-01", status="executed"),
                encoding="utf-8",
            )

            # Default walk without include_retired: must yield no finding
            drifts_default = _check_date_mismatch(
                root, include_untracked=True, include_retired=False
            )
            mismatch_default = [
                d
                for d in drifts_default
                if d.rule == "check.plan-date-filename-mismatch"
            ]
            self.assertEqual(
                mismatch_default,
                [],
                f"Expected no finding without include_retired=True, got: {mismatch_default}",
            )

            # Retired walk with include_retired=True: must yield finding
            drifts_retired = _check_date_mismatch(
                root, include_untracked=True, include_retired=True
            )
            mismatch_retired = [
                d
                for d in drifts_retired
                if d.rule == "check.plan-date-filename-mismatch"
                and d.location == str(plan_executed)
            ]
            self.assertEqual(
                len(mismatch_retired),
                1,
                f"Expected check.plan-date-filename-mismatch with include_retired=True for {plan_executed}, got: {drifts_retired}",
            )

    def test_entry_point_check_content_surfaces_date_mismatch(self) -> None:
        """(6) ENTRY-POINT ROW: check_content(root, 'plans', include_untracked=True) surfaces the finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            defect_path = pending / "20260101-probeset-01-aaa111-probe.ipd.md"
            defect_path.write_text(
                _build_plan(id6="aaa111", date="2026-10-01"), encoding="utf-8"
            )

            drifts = ce.check_content(root, "plans", include_untracked=True)
            mismatch_drifts = [
                d
                for d in drifts
                if d.rule == "check.plan-date-filename-mismatch"
                and d.location == str(defect_path)
            ]
            self.assertEqual(
                len(mismatch_drifts),
                1,
                f"Expected check_content to return check.plan-date-filename-mismatch for {defect_path}, got: {drifts}",
            )

    def test_non_vacuity_control_work_kind_invalid_reported(self) -> None:
        """(7) NON-VACUITY CONTROL: An out-of-vocab Work-Kind is reported by check_plan_work_kind over the same fixture."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan_path = pending / "20260101-probeset-01-aaa111-probe.ipd.md"
            plan_path.write_text(
                _build_plan(id6="aaa111", date="2026-10-01", work_kind="bogus"),
                encoding="utf-8",
            )

            drifts = ce.check_plan_work_kind(root, include_untracked=True)
            work_kind_drifts = [
                d
                for d in drifts
                if d.rule == "check.work-kind-invalid" and d.location == str(plan_path)
            ]
            self.assertEqual(
                len(work_kind_drifts),
                1,
                f"Expected check.work-kind-invalid for {plan_path}, got: {drifts}",
            )


if __name__ == "__main__":
    unittest.main()
