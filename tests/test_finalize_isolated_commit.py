"""`aw ipd finalize` must not let ``pre-commit`` clobber a concurrent writer's edit.

WHY THIS FILE EXISTS. `finalize` performed its lifecycle commit in the SHARED working tree. That is
unsafe in a shared checkout: ``pre-commit`` stashes unstaged changes, runs the hooks, then restores
the stash OVER whatever is on disk, so a peer process writing a tracked file during that window loses
the write entirely (measured 2026-09-06; reproduced in `tests/test_isolated_commit.py`).

It was not hypothetical here. Retirement of orchestrator `84j8d7` REFUSED with
``finalize-refused`` / "lifecycle commit did not happen", naming a hook that reported no findings,
while the real cause was another agent's review run editing an unrelated plan file inside that window
(run `run-20260906T222302Z-2985274`). The Set was fully eligible; the transaction rolled back for a
reason that had nothing to do with it.

WHAT MUST STAY TRUE, and is therefore asserted here rather than assumed:

* the peer's in-flight write SURVIVES a finalize,
* the plan still reaches `executed/` with the branch advanced and the `lifecycle(<id>)` marker intact,
  because the transaction classifies itself by OBSERVED repository state and a broken marker would
  silently turn a success into `unknown-outcome`,
* the hooks STILL GATE: a rejecting hook must leave the plan UNMOVED and roll the transaction back.

Real git and real ``pre-commit`` throughout: the defect was a wrong belief about what pre-commit does
to a working tree, so a mock would encode the same wrong belief and pass.

SECOND SUBJECT, added by scopeattr Order 01 (`h9cn0y` E-01): the ISOLATED lane's SCOPE ATTRIBUTION,
pinned as a CHARACTERIZATION test of behavior that is ALREADY CORRECT rather than as a fix. See
:class:`IsolatedFinalizeCommittedHalfIsLaneLocalTests` for why that distinction is the whole point.
Those tests need real git but NOT ``pre-commit``, so they live in their own unskipped class.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC

from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _completed_plan_text,
    _init_git,
    _write_plan,
)

ACTOR = "opencode/test"
SCOPE = "agent_workflows/demo.py, tests/test_demo.py"

SLOW_HOOK = """\
repos:
  - repo: local
    hooks:
      - id: slow
        name: slow hook
        entry: python3 -c "import time; time.sleep(2); print('hook ran')"
        language: system
        pass_filenames: false
        always_run: true
"""

REJECTING_HOOK = """\
repos:
  - repo: local
    hooks:
      - id: reject
        name: always reject
        entry: python3 -c "import sys; print('REJECTED BY HOOK'); sys.exit(1)"
        language: system
        pass_filenames: false
        always_run: true
"""


def _git_out(root: Path, args: list) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()


@unittest.skipIf(shutil.which("pre-commit") is None, "pre-commit is required")
class FinalizeIsolatedCommitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        # A file a PEER owns: tracked, and about to be edited mid-finalize.
        (self.root / "peer.txt").write_text("peer v1\n", encoding="utf-8")
        _commit_all(self.root, "add peer file")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _branch(self) -> str:
        """The fixture's branch name, read rather than assumed.

        `_init_git` does not pass `-b`, so the name follows the machine's `init.defaultBranch`
        (observed `master` here, `main` elsewhere). Hardcoding either makes this file pass or fail on
        git configuration rather than on the code under test, which is precisely the defect
        `test_run_viewer.py` documents.
        """
        return _git_out(self.root, ["symbolic-ref", "--short", "HEAD"])

    def _install_hook(self, config: str) -> None:
        """Install a hook config AFTER committing it, with the commit itself unhooked.

        `--no-verify` here is about the FIXTURE, not the code under test: a deliberately rejecting
        hook would otherwise block the setup commits that create the plan, so the test could never
        reach the finalize it exists to exercise. Every commit made by `finalize` is fully hooked.
        """
        (self.root / ".pre-commit-config.yaml").write_text(config, encoding="utf-8")
        subprocess.run(
            ["git", "add", "--", ".pre-commit-config.yaml"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--no-verify", "-q", "-m", "add hook config"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["pre-commit", "install"],
            cwd=str(self.root),
            capture_output=True,
            check=False,
        )

    def _ready_plan(self, plan_id: str = "abc123") -> Path:
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=plan_id, scope_paths=SCOPE),
            f"20260830-demo-01-{plan_id}-demo.ipd.md",
        )
        _commit_all(self.root, f"add plan {plan_id}")
        res = LC.begin(self.root, plan, ACTOR, timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        # The plan's own declared work, committed path-scoped as the contract requires.
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "tests/test_demo.py").write_text("mine\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "--", "agent_workflows/demo.py", "tests/test_demo.py"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--no-verify", "-m", "demo: in-scope work"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        return plan

    def test_a_peer_write_during_finalize_survives(self) -> None:
        """THE REGRESSION TEST. A peer edit inside the hook window must not be reverted."""
        self._install_hook(SLOW_HOOK)
        plan = self._ready_plan()
        (self.root / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

        out: dict = {}

        def run_finalize() -> None:
            out["res"] = LC.finalize(
                self.root, plan, ACTOR, "finalize under a slow hook", apply=True
            )

        t = threading.Thread(target=run_finalize)
        t.start()
        time.sleep(1.0)  # inside pre-commit's stash window
        (self.root / "peer.txt").write_text(
            "peer v3 WRITTEN DURING WINDOW\n", encoding="utf-8"
        )
        t.join(timeout=180)
        self.assertFalse(t.is_alive(), "finalize hung")

        res = out["res"]
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        self.assertEqual(
            (self.root / "peer.txt").read_text(encoding="utf-8"),
            "peer v3 WRITTEN DURING WINDOW\n",
            "the peer's in-flight write was destroyed by pre-commit's stash/restore",
        )

    def test_finalize_still_completes_with_the_marker_intact(self) -> None:
        """The transaction classifies by OBSERVED state, so the marker commit must really land."""
        self._install_hook(SLOW_HOOK)
        plan = self._ready_plan(plan_id="def456")
        branch = self._branch()
        before = _git_out(self.root, ["rev-parse", "HEAD"])

        res = LC.finalize(self.root, plan, ACTOR, "finalize normally", apply=True)

        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        after = _git_out(self.root, ["rev-parse", "HEAD"])
        self.assertNotEqual(after, before, "the branch did not advance")
        subject = _git_out(self.root, ["log", "-1", "--format=%s"])
        self.assertTrue(
            subject.startswith("lifecycle(def456)"),
            f"lifecycle marker missing from the tip subject: {subject!r}",
        )
        # Still on the branch (the isolated worktree commits detached; the ref move must not leak that).
        self.assertEqual(
            _git_out(self.root, ["symbolic-ref", "--short", "HEAD"]), branch
        )
        # And the plan is where a successful finalize must leave it.
        self.assertTrue(
            any((self.root / ".aw/records/plans/executed").glob("*def456*")),
            "plan did not reach executed/",
        )

    def test_the_peers_file_is_not_swept_into_the_lifecycle_commit(self) -> None:
        self._install_hook(SLOW_HOOK)
        plan = self._ready_plan(plan_id="ghi789")
        (self.root / "peer.txt").write_text("peer dirty\n", encoding="utf-8")

        res = LC.finalize(self.root, plan, ACTOR, "finalize", apply=True)

        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        stat = _git_out(self.root, ["show", "--stat", "--format=", "HEAD"])
        self.assertNotIn("peer.txt", stat, "a peer's dirty file entered our commit")
        # The peer's edit is still uncommitted and intact.
        self.assertEqual(
            (self.root / "peer.txt").read_text(encoding="utf-8"), "peer dirty\n"
        )

    def test_a_rejecting_hook_still_blocks_and_rolls_back(self) -> None:
        """Isolation must not become `--no-verify`: the gate must still refuse and roll back."""
        # Build the plan FIRST, then arm the rejecting hook, so the hook gates only the finalize's own
        # lifecycle commit and not the fixture's setup commits.
        plan = self._ready_plan(plan_id="jkl012")
        self._install_hook(REJECTING_HOOK)
        before = _git_out(self.root, ["rev-parse", "HEAD"])

        res = LC.finalize(self.root, plan, ACTOR, "should be refused", apply=True)

        self.assertNotEqual(
            res.exit_code, LC.EXIT_OK, "a rejecting hook did not refuse"
        )
        self.assertEqual(
            _git_out(self.root, ["rev-parse", "HEAD"]),
            before,
            "the branch advanced despite a rejecting hook",
        )
        # Rolled back: the plan is NOT in executed/ and remains readable where it was.
        self.assertFalse(
            any((self.root / ".aw/records/plans/executed").glob("*jkl012*")),
            "plan moved to executed/ despite a refused commit",
        )
        self.assertTrue(plan.exists(), "rollback did not restore the plan in place")


class IsolatedFinalizeCommittedHalfIsLaneLocalTests(unittest.TestCase):
    """scopeattr Order 01 (`h9cn0y` E-01): the ISOLATED case ALREADY attributes correctly.

    THIS IS A CHARACTERIZATION TEST, NOT A FIX, and the distinction is load-bearing. `h9cn0y` was
    AUTHORED believing finalize misattributes in a lane because it "diffs against the begin
    receipt's base_head", and proposed teaching finalize to diff against the lane BRANCH instead.
    Review (F-12) re-measured and found the premise false, so that work was retired and replaced by
    this test. The reason the lane is already right is structural, not incidental:

    * ``_repo_root`` deliberately resolves to the WORKTREE, not the main checkout
      (`ipd_lifecycle.py:424-438`: "for a managed lane that is CORRECT"), and
    * the runner hands an isolated turn ``finalize_repo = Path(work_dir)``
      (`oc_runipd.py:6500`),

    so ``git diff <base>..HEAD`` for an in-lane finalize already RUNS INSIDE THE LANE and therefore
    cannot see a foreign commit made on main at all. MEASURED on the real incident: that diff
    returned ELEVEN paths inside `aw/lane/mm6wuz_attempt3` and FORTY-SEVEN in the main checkout.

    So the real exposure `h9cn0y` fixes is the IN-PLACE / HAND-FINALIZE case, where foreign commits
    genuinely sit in the range the finalize computes. That case is covered in
    ``tests/test_finalize_scope_ownership.py``; this class exists so the E-02 change cannot regress
    the lane, and so a future reader does not re-derive the retired diagnosis and "fix" a path that
    was never broken.

    WHAT MUST NOT APPEAR AS A RESULT OF THIS TEST: a lane-branch diff in finalize (unsafe after
    integration, because ``teardown_worktree`` DELETES the lane branch, `worktree_lease.py`), or any
    ``isolated_baseline`` consumption in finalize (it is a ``begin``-only parameter, is not persisted
    in the receipt, and never reaches finalize).

    No ``pre-commit`` needed here, unlike the class above: these assertions are about which paths the
    scope audit COLLECTS, so they must run everywhere.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        _commit_all(self.root, "init tree")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _plan(self, plan_id: str = "lan001") -> Path:
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=plan_id, scope_paths=SCOPE),
            f"20260830-demo-01-{plan_id}-demo.ipd.md",
        )
        _commit_all(self.root, f"add plan {plan_id}")
        return plan

    def test_isolated_committed_half_contains_only_the_lanes_own_commits(self) -> None:
        """The property that ALREADY HOLDS: a lane's committed half is lane-local.

        Built to the incident's real shape: the lane commits its own declared work while MAIN
        receives unrelated commits from other actors in the same window. The lane's audit must see
        only its own, and must therefore demand NO reason for main's commits.
        """
        plan = self._plan()
        lane = self.root.parent / (self.root.name + "-lane-e01")
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "aw/lane/lan001", str(lane), "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        try:
            lane_plan = lane / plan.relative_to(self.root)
            res = LC.begin(lane, lane_plan, ACTOR, timestamp="t")
            self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
            receipt = LC.read_receipt(lane, "lan001")
            assert receipt is not None
            base = str(receipt["base_head"])

            # The lane does its own declared work, path-scoped as the contract requires.
            (lane / "agent_workflows").mkdir(exist_ok=True)
            (lane / "tests").mkdir(exist_ok=True)
            (lane / "agent_workflows/demo.py").write_text("lane\n", encoding="utf-8")
            (lane / "tests/test_demo.py").write_text("lane\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "--", "agent_workflows/demo.py", "tests/test_demo.py"],
                cwd=lane,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "lane in-scope work"],
                cwd=lane,
                check=True,
                capture_output=True,
            )

            # MEANWHILE other actors COMMIT (not merely dirty) unrelated files on MAIN.
            for name in ("agent_workflows/other_one.py", "tests/test_other_two.py"):
                (self.root / name).write_text("another actor\n", encoding="utf-8")
                subprocess.run(
                    ["git", "add", "--", name],
                    cwd=self.root,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-q", "-m", f"another actor: {name}"],
                    cwd=self.root,
                    check=True,
                    capture_output=True,
                )

            lane_sources = LC._changed_path_sources(lane, base)
            main_sources = LC._changed_path_sources(self.root, base)

            # THE PROPERTY: the lane's committed half is exactly its own two declared files.
            self.assertEqual(
                sorted(lane_sources.committed),
                ["agent_workflows/demo.py", "tests/test_demo.py"],
                "an isolated finalize's committed half must be LANE-LOCAL",
            )
            for foreign in ("agent_workflows/other_one.py", "tests/test_other_two.py"):
                self.assertNotIn(foreign, lane_sources.committed)
                # THE CONTRAST that makes the property meaningful: the SAME diff in the MAIN
                # checkout DOES contain the foreign commits. This is the measured 11-vs-47 shape.
                self.assertIn(foreign, main_sources.committed)
            # The two halves are DISJOINT, which is the sharpest available statement of the
            # contrast: each tree sees only the commits made in it. (Deliberately not a
            # count comparison: main and the lane happen to hold two paths each here, so a
            # `>` assertion would encode the fixture's arithmetic rather than the property.)
            self.assertEqual(
                set(lane_sources.committed) & set(main_sources.committed),
                set(),
                "lane-local and main-local committed halves must not overlap",
            )

            # And the audit consequently demands nothing: no reason, and nothing to disregard.
            code, msg, evidence, _f = LC.finalize_precheck(lane, lane_plan)
            self.assertEqual(code, LC.EXIT_OK, msg)
            audit = evidence["scope_audit"]
            self.assertEqual(audit["out_of_scope_paths"], [])
            self.assertEqual(audit["disregarded_unowned_paths"], [])
            self.assertTrue(audit["in_scope"])
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(lane)],
                cwd=self.root,
                check=False,
            )

    def test_finalize_consumes_no_isolated_baseline_and_no_lane_branch_diff(
        self,
    ) -> None:
        """The NEGATIVE half of E-01, asserted in code rather than left to review.

        ``isolated_baseline`` must stay a ``begin``-only concept and the receipt must not grow a
        field for it, because F-12 shows finalize needs no such discriminator. Reading the source is
        the honest way to pin "a mechanism was NOT introduced"; a behavioral test cannot show the
        absence of a code path.
        """
        import inspect

        for fn in (LC.finalize_precheck, LC.finalize):
            src = inspect.getsource(fn)
            self.assertNotIn(
                "isolated_baseline",
                src,
                f"{fn.__name__} must not consume isolated_baseline (F-12)",
            )
            self.assertNotIn(
                "aw/lane/",
                src,
                f"{fn.__name__} must not diff against a lane branch (F-15: it is deleted at teardown)",
            )

        # The receipt schema is unchanged: no isolated_baseline persisted for finalize to read.
        plan = self._plan(plan_id="lan002")
        res = LC.begin(self.root, plan, ACTOR, timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        receipt = LC.read_receipt(self.root, "lan002")
        assert receipt is not None
        self.assertNotIn("isolated_baseline", receipt)
        self.assertIn("base_head", receipt)


if __name__ == "__main__":
    unittest.main()
