"""Behavioral tests pinning both suppressors of terminal-plan scope-drift silence (IPD s2e2um, backlog f9nf0e).

CHARTER AND PURPOSE:
Pin both mechanisms that suppress scope-drift advisories on terminal plans:
1. OUTER SUPPRESSOR (E-01): `check_engine._iter_type_files(root, "plans")` excludes plans in
   any of the `plans.TERMINAL` lifecycle directories (`executed`, `superseded`, `not-executed`),
   as well as `<disposition>/YYYYMM/` sharded placements (e.g. `executed/202609`).
   This is the active suppressor in production today, previously unguarded by any test.
2. INNER DEFENSE-IN-DEPTH BRANCH (E-02):
   (a) Direct call to `check_engine._receipt_is_live(root, plan_path, receipt)` returns False
       for all terminal plan dispositions and True for `pending/`.
   (b) Defense-in-depth end-to-end: under a simulated perturbation where the outer filter
       no longer excludes terminal plans (narrowed `_RETIRED_PATH_SEGMENTS`), `check_scope_drift`
       still reports zero drift findings for terminal plans holding out-of-scope lane changes.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine
from agent_workflows import ipd_lifecycle
from agent_workflows import plans
from tests import support


class TestReceiptLivenessSuppressors(unittest.TestCase):
    """Pin the two independent suppressors of terminal-plan scope-drift silence."""

    #: (plan_dir, should_yield, description)
    OUTER_FILTER_CASES = (
        (
            "pending",
            True,
            "positive control (live twin): pending plan IS yielded by _iter_type_files",
        ),
        (
            "executed",
            False,
            "terminal plan under executed/ is excluded by outer retired-path filter",
        ),
        (
            "executed/202609",
            False,
            "terminal plan under executed/YYYYMM/ sharded path is excluded by outer retired-path filter",
        ),
        (
            "superseded",
            False,
            "terminal plan under superseded/ is excluded by outer retired-path filter",
        ),
        (
            "not-executed",
            False,
            "terminal plan under not-executed/ is excluded by outer retired-path filter",
        ),
    )

    #: (plan_dir, expected_live, description)
    DIRECT_VERDICT_CASES = (
        (
            "pending",
            True,
            "positive control: pending plan receipt is live",
        ),
        (
            "executed",
            False,
            "terminal plan under executed/ receipt is not live",
        ),
        (
            "executed/202609",
            False,
            "terminal plan under executed/YYYYMM/ sharded path receipt is not live",
        ),
        (
            "superseded",
            False,
            "terminal plan under superseded/ receipt is not live",
        ),
        (
            "not-executed",
            False,
            "terminal plan under not-executed/ receipt is not live",
        ),
    )

    #: (plan_dir, description)
    DEFENSE_IN_DEPTH_CASES = (
        (
            "executed",
            "terminal plan under executed/ remains silent via inner defense-in-depth",
        ),
        (
            "executed/202609",
            "sharded terminal plan under executed/202609 remains silent via inner defense-in-depth",
        ),
        (
            "superseded",
            "terminal plan under superseded/ remains silent via inner defense-in-depth",
        ),
        (
            "not-executed",
            "terminal plan under not-executed/ remains silent via inner defense-in-depth",
        ),
    )

    def test_outer_retired_path_filter_suppresses_terminal_plans_table(self) -> None:
        """E-01: outer filter excludes all terminal dispositions and yields pending positive control.

        Asserts on the yielded set from `_iter_type_files` rather than inspecting
        `_RETIRED_PATH_SEGMENTS` membership, testing outcome rather than code structure.
        """
        wrong = []
        positive_control_failed = False
        silent_rows_failed = False

        for plan_dir, should_yield, desc in self.OUTER_FILTER_CASES:
            with tempfile.TemporaryDirectory() as td:
                root, _lane = support.scope_drift_repo(
                    Path(td),
                    plan_id="abc123",
                    plan_dir=plan_dir,
                )
                yielded = list(check_engine._iter_type_files(root, "plans"))

                if should_yield:
                    if not yielded:
                        positive_control_failed = True
                        wrong.append(
                            f"  {plan_dir}: expected plan to be yielded, got empty list ([]): {desc}"
                        )
                    elif len(yielded) != 1:
                        wrong.append(
                            f"  {plan_dir}: expected exactly 1 plan yielded, got {len(yielded)}: "
                            f"{[p.name for p in yielded]!r}: {desc}"
                        )
                else:
                    if yielded:
                        silent_rows_failed = True
                        wrong.append(
                            f"  {plan_dir}: expected empty list ([]), but plan was wrongly yielded: "
                            f"{[p.name for p in yielded]!r}: {desc}"
                        )

        if positive_control_failed and not silent_rows_failed:
            self.fail(
                "VACUITY DETECTED: positive control (pending/) was not yielded while "
                "terminal rows appeared silent. The fixture or filter is yielding nothing.\n"
                + "\n".join(wrong)
            )

        self.assertEqual(
            wrong,
            [],
            f"_iter_type_files answered {len(wrong)} of {len(self.OUTER_FILTER_CASES)} fixtures wrongly:\n"
            + "\n".join(wrong),
        )

    def test_inner_receipt_is_live_direct_verdict_table(self) -> None:
        """E-02(a): _receipt_is_live directly returns False for terminal plans and True for pending."""
        wrong = []

        for plan_dir, expected_live, desc in self.DIRECT_VERDICT_CASES:
            with tempfile.TemporaryDirectory() as td:
                root, _lane = support.scope_drift_repo(
                    Path(td),
                    plan_id="abc123",
                    plan_dir=plan_dir,
                )
                plan_files = list(
                    (root / ".aw" / "records" / "plans").rglob("*.ipd.md")
                )
                self.assertEqual(
                    len(plan_files),
                    1,
                    f"Fixture error: expected 1 plan file for {plan_dir}",
                )
                plan_file = plan_files[0]
                receipt = ipd_lifecycle.read_receipt(root, "abc123")
                self.assertIsNotNone(
                    receipt,
                    f"Fixture error: receipt missing for {plan_dir}",
                )

                verdict = check_engine._receipt_is_live(root, plan_file, receipt)
                if verdict != expected_live:
                    wrong.append(
                        f"  {plan_dir}: expected _receipt_is_live={expected_live}, "
                        f"got {verdict}: {desc}"
                    )

        self.assertEqual(
            wrong,
            [],
            f"_receipt_is_live answered {len(wrong)} of {len(self.DIRECT_VERDICT_CASES)} fixtures wrongly:\n"
            + "\n".join(wrong),
        )

    def test_defense_in_depth_under_narrowed_retired_path_filter(self) -> None:
        """E-02(b): check_scope_drift stays silent for terminal plans when outer filter is narrowed.

        Simulates outer filter no longer excluding terminal plans by temporarily narrowing
        `check_engine._RETIRED_PATH_SEGMENTS`. Restores original value in `finally` and
        re-asserts stock behavior to guard against state leakage.
        """
        orig = check_engine._RETIRED_PATH_SEGMENTS
        wrong = []

        try:
            # Narrow outer retired path segments to exclude plans.TERMINAL dispositions
            check_engine._RETIRED_PATH_SEGMENTS = frozenset(
                seg for seg in orig if seg not in plans.TERMINAL
            )

            for plan_dir, desc in self.DEFENSE_IN_DEPTH_CASES:
                with tempfile.TemporaryDirectory() as td:
                    root, lane = support.scope_drift_repo(
                        Path(td),
                        scope_paths="src/",
                        plan_id="abc123",
                        plan_dir=plan_dir,
                    )
                    # Dirty the lane with an out-of-scope modification
                    out_file = lane / "other" / "drift.txt"
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text("drift\n", encoding="utf-8")

                    # Verify prerequisite: outer filter now yields this terminal plan
                    yielded = list(check_engine._iter_type_files(root, "plans"))
                    self.assertEqual(
                        len(yielded),
                        1,
                        f"Perturbation failed: {plan_dir} was not yielded under narrowed filter",
                    )

                    drifts = [
                        d
                        for d in check_engine.check_scope_drift(root)
                        if d.rule == "check.scope-drift"
                    ]
                    if drifts:
                        wrong.append(
                            f"  {plan_dir}: expected 0 findings (inner branch holding), "
                            f"got {len(drifts)}: {[d.detail for d in drifts]!r}: {desc}"
                        )

            self.assertEqual(
                wrong,
                [],
                f"Defense-in-depth failed for {len(wrong)} of {len(self.DEFENSE_IN_DEPTH_CASES)} cases:\n"
                + "\n".join(wrong),
            )
        finally:
            check_engine._RETIRED_PATH_SEGMENTS = orig

        # Post-restore re-assertions
        self.assertEqual(
            check_engine._RETIRED_PATH_SEGMENTS,
            orig,
            "Restore verification failed: _RETIRED_PATH_SEGMENTS not restored to orig",
        )
        # Verify stock behavior restored: outer filter once again suppresses terminal plans
        with tempfile.TemporaryDirectory() as td:
            root, _lane = support.scope_drift_repo(
                Path(td),
                plan_id="abc123",
                plan_dir="executed",
            )
            yielded = list(check_engine._iter_type_files(root, "plans"))
            self.assertEqual(
                yielded,
                [],
                "Stock behavior not restored: executed/ still yielded after restore",
            )
