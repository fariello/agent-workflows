"""What a frozen begin base MEANS once main has moved past it (rcptstale `wmnmei`, backlog `v880xk`).

THE CONDITION THIS FILE IS ABOUT, which neither existing liveness test covers. A plan in `pending/`
whose `base_head` IS an ancestor of HEAD is LIVE by both tests in `_receipt_is_live` while being
arbitrarily far behind: measured 2026-09-22 across six live receipts, 4 to 344 non-merge commits, five
of the six holding a lane worktree that was being actively worked. All 350 findings those receipts
produced named OTHER agents' commits.

AND "STALE" MISNAMES IT, which is why this file tests a TREE and not an AGE. Nothing about those bases
is wrong; each is correctly frozen for an execution still in flight, and it is MAIN that moved. So the
defect is MISATTRIBUTION, and every age-keyed remedy (an expiry, a distance threshold, a skip once the
base is "too old") fires hardest on the healthiest, most active execution, which inverts the intent.

THE ANSWER, per the maintainer's ruling of 2026-09-10 (OQ-01): MEASURE THE ISOLATED LANE WHEN THERE IS
ONE, AND REPORT NOTHING WHEN THERE IS NOT. The advisory's subject is a lane-isolated execution's own
tree. Asked which of five candidate BASELINES to adopt (frozen base as-is, merge-base, the plan's own
commits, an age-gated skip, or commit-cohesion attribution), the maintainer rejected the axis: "I don't
see a way to do this in main if more than one entity (human or agent) is working on main."

THE ACCEPTED COST IS TESTED HERE TOO, deliberately, so nobody later "restores" it as an oversight:
work done by hand directly in a shared main checkout gets NO scope advisory at all
(`test_a_change_in_the_main_checkout_is_not_reported`). That silence is the contract.

NO EXPIRY IS IMPLEMENTED AND NO RECEIPT IS DELETED. The item forbids both, and
`test_the_rule_never_removes_a_receipt` pins the second directly, because a `committed-incomplete`
finalize journal can still need a receipt whose plan is already terminal.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as life
from agent_workflows import worktree_lease as lease

RULE = "check.scope-drift"
PLAN_ID = "aaa111"
PLAN_NAME = f"20260828-t-01-{PLAN_ID}-x.ipd.md"


class _Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n", encoding="utf-8"
        )
        self.pending = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending.mkdir(parents=True)
        (self.root / "src").mkdir()
        self.plan = self.pending / PLAN_NAME
        self.plan.write_text(
            f"# IPD: x\n\n- Id: {PLAN_ID}\n- Kind: child\n- Status: approved\n- Set: t\n"
            "- Order: 1\n- Scope-Paths: src/\n\n## Workflow history\n"
            "- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n",
            encoding="utf-8",
        )
        self.base = self._commit("init")
        self._write_receipt(self.base)

    def _commit(self, msg: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _write_receipt(self, base: str) -> None:
        rp = life.receipt_path_for(self.root, PLAN_ID)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(
            json.dumps(
                {"plan_id": PLAN_ID, "base_head": base, "scope_paths": ["src/"]}
            ),
            encoding="utf-8",
        )

    def _advance_main(self, n: int = 3) -> None:
        """Land `n` foreign commits on main AFTER the base was frozen: other agents' work."""
        for i in range(n):
            (self.root / f"coworker{i}.py").write_text("theirs\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "--", f"coworker{i}.py"], cwd=self.root, check=True
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-q",
                    "-m",
                    f"another agent {i}",
                    "--",
                    f"coworker{i}.py",
                ],
                cwd=self.root,
                check=True,
            )

    def _hits(self):
        return [d for d in ce.check_scope_drift(self.root) if d.rule == RULE]


class MisattributionTests(_Fixture):
    """The measured defect: a live, correctly frozen base reported as this plan's drift."""

    def test_intervening_foreign_commits_are_no_longer_reported_as_this_plans_drift(
        self,
    ):
        """THE HEADLINE CASE. The plan is live, its base is an ancestor, main moved, the lane is CLEAN.

        Pre-fix this reported one finding per foreign file. The plan drifted nowhere, so the correct
        answer is silence, and the evidence for it is the lane rather than an age heuristic.
        """
        lane = lease.allocate_worktree(self.root, PLAN_ID).path
        self._advance_main(3)

        # The premise: the receipt is LIVE by both existing tests, so nothing here is spent authority.
        receipt = life.read_receipt(self.root, PLAN_ID)
        assert receipt is not None
        self.assertTrue(
            ce._receipt_is_live(self.root, self.plan, receipt),
            "premise: this receipt must be LIVE, or the test is measuring liveness instead",
        )
        self.assertTrue(lane.is_dir())

        self.assertEqual(
            [d.detail for d in self._hits()],
            [],
            "other agents' intervening commits must not be reported as this plan's scope drift",
        )

    def test_the_plans_own_lane_work_IS_still_reported(self):
        """The mirror, so the fix is a NARROWING and not a disabling: the same tree, the same moved
        main, but the offending path is in the plan's OWN lane. It must be flagged."""
        lane = lease.allocate_worktree(self.root, PLAN_ID).path
        self._advance_main(3)
        (lane / "other").mkdir(parents=True, exist_ok=True)
        (lane / "other" / "mine.py").write_text("mine\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "other/mine.py"], cwd=lane, check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-q",
                "-m",
                "my out-of-scope work",
                "--",
                "other/mine.py",
            ],
            cwd=lane,
            check=True,
        )

        hits = self._hits()
        self.assertEqual(len(hits), 1, [d.detail for d in hits])
        self.assertIn("other/mine.py", hits[0].detail)
        self.assertNotIn(
            "coworker0.py",
            hits[0].detail,
            "the foreign commits must not be swept into the plan's own finding",
        )

    def test_age_alone_changes_nothing_which_is_the_point(self):
        """DISTANCE IS NOT STALENESS. 30 intervening commits with a clean lane is still silence.

        This pins the ruling against a future age-keyed 'improvement': if someone reintroduces an
        expiry or a distance threshold, the honest execution below is the first thing it breaks.
        """
        lease.allocate_worktree(self.root, PLAN_ID)
        self._advance_main(30)

        receipt = life.read_receipt(self.root, PLAN_ID)
        assert receipt is not None
        self.assertTrue(ce._receipt_is_live(self.root, self.plan, receipt))
        self.assertEqual([d.detail for d in self._hits()], [])


class TreeSelectionTests(_Fixture):
    """`_plan_execution_tree`: which tree the advisory may speak about, and when it must stay silent."""

    def test_a_change_in_the_main_checkout_is_not_reported(self):
        """THE ACCEPTED COST, asserted so it cannot be called an oversight later.

        Hand work directly in a shared main checkout gets NO advisory, because no honest attribution
        exists there when several parties share one tree. The maintainer accepted this explicitly and
        declined the variant that printed a "scope not checked" line, in favor of plain silence.
        """
        lease.allocate_worktree(self.root, PLAN_ID)
        (self.root / "other").mkdir(parents=True, exist_ok=True)
        (self.root / "other" / "by-hand.py").write_text("x\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "--", "other/by-hand.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "by hand in main", "--", "other/by-hand.py"],
            cwd=self.root,
            check=True,
        )

        self.assertEqual([d.detail for d in self._hits()], [])

    def test_a_plan_with_no_lane_is_silent(self):
        """No lane means no subject the advisory may speak about, so it reports nothing at all."""
        state = lease.inspect_lane(self.root, PLAN_ID)
        self.assertEqual(state.state, lease.LANE_ABSENT, "premise: no lane exists")
        self.assertIsNone(ce._plan_execution_tree(self.root, PLAN_ID, self.base))
        self._advance_main(3)
        self.assertEqual([d.detail for d in self._hits()], [])

    def test_a_lane_cut_from_a_different_base_is_silent(self):
        """A lane whose HEAD does not descend from the FROZEN base cannot be diffed against it.

        Real and measured, not hypothetical: `allocate_worktree` attempt-scopes a STALE or HOLDS-WORK
        lane rather than adopting it, so lane and receipt legitimately disagree, and one of six live
        contributors on 2026-09-22 (`lc4unl`) was exactly this shape. Diffing across that fork would
        attribute main's own commits to the plan, which is the defect the tree selection removes.
        """
        lane = lease.allocate_worktree(self.root, PLAN_ID).path
        # Re-freeze the receipt at a LATER main commit the lane does not contain.
        self._advance_main(2)
        later = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self._write_receipt(later)
        (lane / "other").mkdir(parents=True, exist_ok=True)
        (lane / "other" / "x.py").write_text("y\n", encoding="utf-8")

        self.assertIsNone(ce._plan_execution_tree(self.root, PLAN_ID, later))
        self.assertEqual([d.detail for d in self._hits()], [])

    def test_the_resolved_tree_is_the_lane_the_production_allocator_created(self):
        """The helper resolves the SAME path `worktree_lease` allocated, not a reconstructed one."""
        handle = lease.allocate_worktree(self.root, PLAN_ID)
        resolved = ce._plan_execution_tree(self.root, PLAN_ID, self.base)
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.resolve(), handle.path.resolve())

    def test_tree_resolution_fails_SILENT_when_git_cannot_answer(self):
        """FAIL SAFE, matching `_receipt_is_live`: an undeterminable subject yields no finding.

        A rule that cannot establish which tree it is speaking about must not invent one. Driven by
        inducing the error rather than asserting on source text.
        """
        lane = lease.allocate_worktree(self.root, PLAN_ID).path
        (lane / "other").mkdir(parents=True, exist_ok=True)
        (lane / "other" / "x.py").write_text("y\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "other/x.py"], cwd=lane, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "w", "--", "other/x.py"], cwd=lane, check=True
        )
        self.assertTrue(self._hits(), "sanity: this arrangement flags when healthy")

        real = ce._git_capture
        calls = []

        def boom(repo_root, args):
            if args[:1] == ["merge-base"] and Path(repo_root) == lane:
                calls.append(args)
                raise OSError("git unavailable")
            return real(repo_root, args)

        ce._git_capture = boom
        try:
            hits = self._hits()  # must not raise
        finally:
            ce._git_capture = real
        self.assertTrue(calls, "the induced error path must actually be exercised")
        self.assertEqual([d.detail for d in hits], [])


class NoExpiryTests(_Fixture):
    """E-04: the REJECTED framing stays rejected. No expiry, and no receipt is ever removed."""

    def test_the_rule_never_removes_a_receipt(self):
        """Ignoring a receipt is licensed; deleting one is not, even for a very distant base.

        A `committed-incomplete` finalize journal re-runs finalize against a plan already in
        `executed/`, so the receipt can still be required execution authority.
        """
        lease.allocate_worktree(self.root, PLAN_ID)
        self._advance_main(30)
        rp = life.receipt_path_for(self.root, PLAN_ID)
        self.assertTrue(rp.exists())

        ce.check_scope_drift(self.root)

        self.assertTrue(
            rp.exists(), "the rule is read-only; it must not consume a receipt"
        )
        self.assertEqual(json.loads(rp.read_text())["base_head"], self.base)

    def test_no_distance_or_age_field_gates_the_advisory(self):
        """The rule's inputs carry no age or distance term, so no 'too far' threshold can be read
        into it. Asserted behaviorally: identical trees, wildly different distances, same verdict."""
        lane = lease.allocate_worktree(self.root, PLAN_ID).path
        (lane / "other").mkdir(parents=True, exist_ok=True)
        (lane / "other" / "x.py").write_text("y\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "other/x.py"], cwd=lane, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "w", "--", "other/x.py"], cwd=lane, check=True
        )

        near = [d.detail for d in self._hits()]
        self._advance_main(40)
        far = [d.detail for d in self._hits()]
        self.assertEqual(
            near,
            far,
            "the verdict changed with DISTANCE alone, so an age term has entered the rule",
        )
        self.assertTrue(near)


if __name__ == "__main__":
    unittest.main()
