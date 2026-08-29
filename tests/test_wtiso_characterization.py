#!/usr/bin/env python3
"""wtiso Phase 0 (`8zgybk` E-03, E-04, E-05): CHARACTERIZATION tests.

A characterization test PINS BEHAVIOR THAT EXISTS, including behavior that is WRONG. Each test
below asserts a defect research x03wgn diagnosed, so that the phase which fixes it must
deliberately come here and INVERT the assertion. That is the safety net: a later phase cannot
"accidentally" half-fix one of these, and it cannot silently regress after fixing it.

Read every assertion below as "this is true today and SHOULD NOT BE". The owning phase is named
in each docstring.

  * E-03 -> `qcqhj7` (Phase 1): the worker prompt names absolute paths OUTSIDE the lane.
  * E-04 -> `58ha43` (Phase 4): the begin receipt is COPIED into the lane, forking authority.
  * E-05 -> `2c122z` (Phase 5): integration validation returns True BEFORE the merged tree exists.

All three run purely in-memory or against plain temp directories. None needs a real git repo, a
real worktree, or a subprocess, which keeps the net fast enough to stay in the default suite.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, ipd_lifecycle, oc_runipd


class WorkerPromptPathCharacterizationTests(unittest.TestCase):
    """E-03. x03wgn Section 8 Phase 1 item 1: "Change generated worker prompts so every named
    worker input/output path is inside the lane." Today they are not."""

    def test_worker_prompt_names_main_run_paths(self):
        """PINNED DEFECT: the prompt directs the worker to ABSOLUTE paths outside its lane.

        `oc_runipd.build_prompt` (agent_workflows/oc_runipd.py:1448) interpolates the driver's
        external run directory, the outcome JSON path, and the report path straight into the
        worker's instructions (the emitted lines are at oc_runipd.py:1469-1472). A worker obeying
        the prompt therefore writes control-plane artifacts into the MAIN checkout, which is the
        root of the qyaime permission-deadlock (the write is outside the lane, so the host asks
        for `external_directory` permission and a headless `--auto` turn waits forever).

        FLIPPED BY: `qcqhj7` (Phase 1). When that phase lands, this test must be inverted to
        assert the prompt names LANE-RELATIVE paths only, and `assertNotIn(str(run_dir), prompt)`.
        """

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # The driver's run dir lives OUTSIDE the lane; that is the whole point of the defect.
            run_dir = root / "main-checkout" / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            plan_path = root / "plan.ipd.md"
            plan_path.write_text("# IPD: fixture\n", encoding="utf-8")

            item = {
                "setid": "wtiso",
                "id6": "8zgybk",
                "position": 1,
                "attempts": [],
            }
            state = {"run_id": "run-test"}

            prompt = oc_runipd.build_prompt(
                item, state, run_dir, plan_path, recovery=False
            )

            # The three current-behavior tokens emitted at oc_runipd.py:1469-1472.
            self.assertIn("External run directory:", prompt)
            self.assertIn("Required JSON outcome:", prompt)
            self.assertIn("Driver report:", prompt)

            # And they carry the ABSOLUTE external paths, not lane-relative ones. This is the
            # assertion Phase 1 must invert.
            self.assertIn(str(run_dir), prompt)
            self.assertIn(
                str(run_dir / "outcomes" / "01-8zgybk.json"),
                prompt,
                "the prompt should name the absolute main-run outcome path today",
            )
            self.assertIn(str(run_dir / "execution-report.md"), prompt)

            # The named paths are outside any lane worktree: nothing in the prompt scopes them
            # under `.aw/worktrees/`.
            self.assertNotIn(".aw/worktrees", str(run_dir))


class ReceiptCopyCharacterizationTests(unittest.TestCase):
    """E-04. x03wgn Section 7 row "Receipt copied into lane": "Two authorities diverge or are
    consumed independently"; the prescribed guard is "One central driver-created receipt bound to
    attempt; delete receipt-copy path.\" """

    def test_receipt_is_copied_into_lane(self):
        """PINNED DEFECT: the begin receipt is duplicated into the lane worktree.

        `oc_runipd.sync_receipt_into_worktree` (agent_workflows/oc_runipd.py:470-484) copies the
        main checkout's receipt to the WORKTREE-RELATIVE path returned by
        `ipd_lifecycle.receipt_path_for` (agent_workflows/ipd_lifecycle.py:249-251). After the
        copy, two files claim to be the execution authority for the same plan and can be consumed
        or invalidated independently.

        FLIPPED BY: `58ha43` (Phase 4), which relocates the canonical receipt out of the repo and
        deletes the copy path. When that lands, this test is deleted or inverted to assert NO
        in-lane receipt exists.
        """

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Two PLAIN directories are enough: the copy is a filesystem operation and never
            # consults git, so no real worktree is required to demonstrate the fork.
            repo = root / "repo"
            worktree = root / "worktree"
            repo.mkdir()
            worktree.mkdir()
            id6 = "8zgybk"

            src = ipd_lifecycle.receipt_path_for(repo, id6)
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(
                '{"plan_id": "8zgybk", "base_head": "deadbeef"}\n', encoding="utf-8"
            )

            oc_runipd.sync_receipt_into_worktree(repo, worktree, id6)

            dst = ipd_lifecycle.receipt_path_for(worktree, id6)
            self.assertTrue(
                dst.is_file(),
                "the receipt should be copied into the lane today (the pinned defect)",
            )
            # The duplicate resolves UNDER the worktree, i.e. it is lane-local, not a single
            # central control-plane location. `relative_to` raises if it is not, so this is the
            # falsifiable form of "not a central root".
            self.assertEqual(
                dst.relative_to(worktree),
                Path(".aw/state/ipd-lifecycle/8zgybk.receipt.json"),
            )
            # Two independent authorities now exist with identical content.
            self.assertTrue(src.is_file())
            self.assertEqual(
                src.read_text(encoding="utf-8"), dst.read_text(encoding="utf-8")
            )
            self.assertNotEqual(src.resolve(), dst.resolve())


class IntegrationValidationCharacterizationTests(unittest.TestCase):
    """E-05. x03wgn Section 7 row "Validation occurs before actual merge": "Passing test does not
    cover merge result"; the prescribed guard is "Merge into candidate first and validate that
    exact tree.\" """

    def test_integration_validation_returns_true_before_merge(self):
        """PINNED DEFECT: the integration validation gate is unconditionally True.

        `agy_runipd.make_integration_validation_runner`
        (agent_workflows/agy_runipd.py:644-655) returns a callable whose body is a bare
        `return True` (agent_workflows/agy_runipd.py:653). It ignores both the combined diff and
        the merged file list, so the gate "passes" for content it never inspected and before the
        merged tree exists at all. An irreversible action (updating the target ref) is authorized
        by a check that cannot fail.

        FLIPPED BY: `2c122z` (Phase 5), which builds a real candidate merge and validates THAT
        exact tree. When it lands, a fabricated non-empty diff must be able to FAIL here.
        """

        runner = agy_runipd.make_integration_validation_runner({}, Path("."), {})

        # A fabricated, obviously-unvalidated diff still passes.
        self.assertTrue(runner("non-empty combined diff", ["changed.py"]))
        # So does the degenerate empty case, confirming the result is independent of the inputs.
        self.assertTrue(runner("", []))


if __name__ == "__main__":
    unittest.main()
