"""Behavioral tests for check_engine.check_scope_drift (IPD qqg41f, backlog caf5ed).

CHARTER AND PURPOSE:
Restores provable behavioral test coverage for `check_engine.check_scope_drift` following
the deletion of the four historical test files in commit 19313eed. Prior to this module,
the rule had zero behavioral test coverage (inserting an unconditional early return left
the entire bare suite green at 3387 passed).

SENSITIVITY AND VALIDATION MUTATIONS (proven in E-05 and E-07):
This module is proven sensitive against three distinct defect models:
1. Early return (`return drift`): breaks row (a) and the pending twin.
2. Wrong-tree redirection (`exec_tree = Path(repo_root)`): breaks row (a) and the wrong-tree row.
3. Historical union defect (changed paths = union of lane and main changed set): breaks ONLY
   the wrong-tree row, proving the wrong-tree row is uniquely capable of discriminating the
   actual historical regression.

EXPLICIT BOUND OF THIS MODULE:
This module covers the drift advisory's own OBSERVABLE decisions:
- Which tree is measured (isolated lane worktree vs main checkout)
- One-finding-per-plan collapse (multi-offender grouping in a single finding detail)
- In-scope silence (changes inside declared Scope-Paths are clean)
- Grandfathered sentinel carve-out (empty frozen allowlist is advisory-satisfied)
- No-receipt silence (absence of execution authority produces no drift)
- Terminal plan silence (retired plans produce no drift)
- Unreachable frozen base silence (non-ancestor base in main produces no drift)

BOUND RESTRICTION: This module deliberately does NOT restore the receipt-liveness
(`_receipt_is_live` unit suite), event-derived transition-validity, or finalize-ownership
attribution surfaces that died in the same commit; those belong to the general trim audit
backlog xvp5vx.

TERMINAL ROW ATTRIBUTION NOTE (E-04, F-09):
The terminal rows in this module assert the rule's observable black-box contract
('a terminal plan gets no drift advisory'). In production, the measured suppressor
is `_iter_type_files`' retired-path filter (`is_retired` returning True for `executed`),
which excludes the plan before `_receipt_is_live` is ever reached. These rows do NOT
claim to exercise `_receipt_is_live`'s terminal rejection branch (tracked in backlog f9nf0e).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine
from agent_workflows import ipd_lifecycle
from tests import support


class TestCheckScopeDrift(unittest.TestCase):
    """Behavioral coverage for check_engine.check_scope_drift."""

    RULE = "check.scope-drift"

    #: (case description, declared Scope-Paths, tuple of paths dirtied in lane,
    #:  write_receipt flag, expected needles in detail or None for silent, why this row exists)
    CORE_FIXTURES = (
        (
            "out-of-scope change in lane FIRES (three paths collapsed)",
            "src/",
            ("other/a.txt", "other/b.txt", "other/c.txt"),
            True,
            ("other/a.txt", "other/b.txt", "other/c.txt"),
            "THE RULE'S ONE POSITIVE CASE in the core table: three out-of-scope paths "
            "collapse into exactly one Drift finding whose detail names all three paths. "
            "Anti-vacuity control for rows (b) through (d).",
        ),
        (
            "in-scope change in lane is SILENT",
            "src/",
            ("src/demo.py",),
            True,
            None,
            "THE RULE'S PURPOSE: changes within declared Scope-Paths must not trigger a drift advisory.",
        ),
        (
            "grandfathered Scope-Paths sentinel is SILENT",
            "grandfathered",
            ("other/a.txt",),
            True,
            None,
            "DOCUMENTED CARVE-OUT: grandfathered sentinel yields empty allowlist, "
            "treated as advisory-satisfied.",
        ),
        (
            "no begin receipt is SILENT (lane still allocated)",
            "src/",
            ("other/a.txt",),
            False,
            None,
            "NO LIVE EXECUTION: no receipt means no execution authority to reconcile. "
            "Lane is still allocated so silence is attributable to missing receipt alone.",
        ),
    )

    def test_core_contract_table(self):
        """Core contract table restoring the 4-row contract from deleted test_event_derived_lifecycle.

        Row (a) arranges THREE out-of-scope paths and asserts both len(drift) == 1 and that all
        three paths appear in the finding's detail (pinning one-finding-per-plan collapse).
        Row (a) is the anti-vacuity control for the three silent rows (b), (c), and (d).
        Row (d) still allocates its lane worktree so its silence is attributable to the missing receipt.
        """
        wrong = []
        firing_failed = False
        silent_failed = False
        for (
            case,
            scope,
            dirty_paths,
            receipt,
            expected_needles,
            why,
        ) in self.CORE_FIXTURES:
            with tempfile.TemporaryDirectory() as td:
                root, lane = support.scope_drift_repo(
                    Path(td),
                    scope_paths=scope,
                    write_receipt=receipt,
                )
                self.assertTrue(lane.is_dir(), f"Lane must be allocated for {case}")

                for rel_path in dirty_paths:
                    target = lane / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("drift\n", encoding="utf-8")

                hits = [
                    d
                    for d in check_engine.check_scope_drift(root)
                    if d.rule == self.RULE
                ]
                problems = []
                if expected_needles is None:
                    if hits:
                        silent_failed = True
                        problems.append(
                            f"expected SILENT, got {[d.detail for d in hits]!r}"
                        )
                else:
                    if not hits:
                        firing_failed = True
                        problems.append(
                            "expected finding, got nothing (rule was silent)"
                        )
                    elif len(hits) != 1:
                        problems.append(
                            f"expected 1 collapsed finding, got {len(hits)}: {[d.detail for d in hits]!r}"
                        )
                    for needle in expected_needles:
                        if not any(needle in d.detail for d in hits):
                            problems.append(
                                f"detail missing needle {needle!r}: {[d.detail for d in hits]!r}"
                            )
                if problems:
                    wrong.append(
                        f"  {case} (scope={scope!r}, receipt={receipt}, dirty={dirty_paths!r}):\n"
                        + "\n".join(f"    - {p}" for p in problems)
                        + f"\n    Why this row exists: {why}"
                    )

        if firing_failed and not silent_failed:
            self.fail(
                "SYSTEMATIC VACUITY DETECTED: Row (a) (firing control) failed to report drift, "
                "while all three silent rows passed. The rule has stopped reporting entirely "
                "and the silent rows are vacuous.\n" + "\n".join(wrong)
            )

        self.assertEqual(
            wrong,
            [],
            f"`check_scope_drift` answered {len(wrong)} of {len(self.CORE_FIXTURES)} fixtures wrongly:\n"
            + "\n".join(wrong),
        )

    def test_liveness_pending_twin_fires(self):
        """Liveness row (a): pending twin that FIRES.

        Identical in every respect to the terminal rows (b) and (c) except the plan's directory
        is 'pending'. Proves that this arrangement fires when the plan is not terminal.
        """
        with tempfile.TemporaryDirectory() as td:
            root, lane = support.scope_drift_repo(
                Path(td),
                scope_paths="src/",
                plan_dir="pending",
            )
            out_file = lane / "other" / "f.txt"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text("drift\n", encoding="utf-8")

            drifts = [
                d for d in check_engine.check_scope_drift(root) if d.rule == self.RULE
            ]
            self.assertEqual(len(drifts), 1)
            self.assertIn("other/f.txt", drifts[0].detail)

    def test_liveness_terminal_plan_silent(self):
        """Liveness row (b): plan under .aw/records/plans/executed/ is SILENT.

        Observable contract: a terminal plan gets no drift advisory.
        ATTRIBUTION NOTE (E-04, F-09): The measured suppressor in production is
        `_iter_type_files`' retired-path filter (`is_retired` returning True for
        the 'executed' path segment), which skips the plan before `_receipt_is_live`
        is ever called. This row asserts the observable contract and does NOT claim
        to exercise `_receipt_is_live`.
        """
        with tempfile.TemporaryDirectory() as td:
            root, lane = support.scope_drift_repo(
                Path(td),
                scope_paths="src/",
                plan_dir="executed",
            )
            out_file = lane / "other" / "f.txt"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text("drift\n", encoding="utf-8")

            drifts = [
                d for d in check_engine.check_scope_drift(root) if d.rule == self.RULE
            ]
            self.assertEqual(drifts, [])

    def test_liveness_sharded_terminal_plan_silent(self):
        """Liveness row (c): plan under executed/YYYYMM/ sharded path is SILENT.

        Observable contract: an archived/sharded terminal plan gets no drift advisory.
        ATTRIBUTION NOTE (E-04, F-09): Like row (b), the measured suppressor is
        `_iter_type_files`' retired-path filter, not `_receipt_is_live`.
        """
        with tempfile.TemporaryDirectory() as td:
            root, lane = support.scope_drift_repo(
                Path(td),
                scope_paths="src/",
                plan_dir="executed/202609",
            )
            out_file = lane / "other" / "f.txt"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text("drift\n", encoding="utf-8")

            drifts = [
                d for d in check_engine.check_scope_drift(root) if d.rule == self.RULE
            ]
            self.assertEqual(drifts, [])

    def test_liveness_unreachable_base_silent_via_lane_only_commit(self):
        """Liveness row (d): receipt frozen at an unreachable commit is SILENT.

        Constructed via a LANE-ONLY COMMIT: committing on the lane after allocation
        creates a commit reachable from the lane's HEAD but unreachable from main's HEAD.
        Freezing the receipt's base_head at that lane-only commit makes `_receipt_is_live`
        return False while `_plan_execution_tree` still resolves the lane. This isolates
        `_receipt_is_live` as the single suppressor (one-variable design, avoiding
        over-determined orphan-commit arrangements; see F-10).
        """
        with tempfile.TemporaryDirectory() as td:
            root, lane = support.scope_drift_repo(
                Path(td),
                scope_paths="src/",
                plan_id="abc123",
                plan_dir="pending",
            )
            # Create a lane-only commit
            lane_file = lane / "lane_commit.txt"
            lane_file.write_text("lane only\n", encoding="utf-8")
            support.git(lane, "add", "lane_commit.txt")
            support.git(lane, "commit", "-m", "commit on lane only", "-q")
            lane_head = support.git(lane, "rev-parse", "HEAD").stdout.strip()

            # Freeze receipt at that lane commit
            rcpt_path = ipd_lifecycle.receipt_path_for(root, "abc123")
            rcpt_data = {"base_head": lane_head, "plan_id": "abc123"}
            rcpt_path.write_text(json.dumps(rcpt_data), encoding="utf-8")

            # Out-of-scope change in lane
            out_file = lane / "other" / "f.txt"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text("drift\n", encoding="utf-8")

            # Probe liveness and execution tree resolution (single suppressor proof)
            plan_file = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260901-demo-01-abc123-demo.ipd.md"
            )
            self.assertFalse(check_engine._receipt_is_live(root, plan_file, rcpt_data))
            resolved_lane = check_engine._plan_execution_tree(root, "abc123", lane_head)
            self.assertIsNotNone(resolved_lane)
            self.assertEqual(resolved_lane.resolve(), lane.resolve())

            drifts = [
                d for d in check_engine.check_scope_drift(root) if d.rule == self.RULE
            ]
            self.assertEqual(drifts, [])

    def test_wrong_tree_main_dirty_lane_clean_silent(self):
        """Wrong-tree row: MAIN dirty out of scope, LANE clean, asserted SILENT.

        COVERS THE RULE'S HEADLINE CLAIM (WHICH TREE IS MEASURED):
        `check_scope_drift`'s docstring records that the rule once diffed the frozen
        base against whichever tree the command ran in, producing 350 findings across
        six plans of which 350 of 350 were other agents' COMMITTED history, while the
        lane-measured answer for the same six was 9/5/1/0 with two plans having no
        usable lane. This row asserts that the fix holds: out-of-scope modifications
        made in the main repository checkout while the plan's lane is clean do NOT
        produce a drift advisory against the plan.

        ACCEPTED COST NOTE (maintainer ruling 2026-09-10, wmnmei / v880xk):
        The silence asserted here IS the deliberate design choice that hand work
        performed in a shared main checkout gets no advisory at all, because no
        honest attribution exists when multiple entities share one tree. This test
        pins that ruling as observable behavior, not as an oversight.
        """
        with tempfile.TemporaryDirectory() as td:
            root, lane = support.scope_drift_repo(
                Path(td),
                scope_paths="src/",
                plan_dir="pending",
            )
            # Write out-of-scope change in MAIN CHECKOUT, leaving LANE clean
            main_out_file = root / "other" / "main_unrelated.txt"
            main_out_file.parent.mkdir(parents=True, exist_ok=True)
            main_out_file.write_text("modified on main\n", encoding="utf-8")

            drifts = [
                d for d in check_engine.check_scope_drift(root) if d.rule == self.RULE
            ]
            self.assertEqual(
                drifts,
                [],
                "check_scope_drift must measure the isolated lane, not the main tree: "
                "changes in main checkout must not be attributed to the plan.",
            )


if __name__ == "__main__":
    unittest.main()
