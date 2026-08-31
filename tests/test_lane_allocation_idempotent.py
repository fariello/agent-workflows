"""Lane allocation is idempotent, and an interrupt preserves work instead of leaking or destroying it.

laneorphan-01 (`zwnjp3`) E-07 / V-07. Every case runs on a THROWAWAY git repo built here; none of
them touch this repository's real `.aw/worktrees/`, which may hold live lanes owned by other running
drivers.

The ten cases, each named for the hazard it pins:

  (a) the exact reported failure: a second allocation for the same lane id no longer raises
      `a branch named 'aw/lane/<id>' already exists`.
  (b) a BRANCH-ONLY leftover (worktree removed, branch surviving) also allocates. This wedges
      allocation identically and is the likelier residue, and a directory-existence check misses it.
  (c) an EMPTY same-base lane is ADOPTED and no second worktree appears.
  (d) a lane holding commits is NOT adopted, gets an attempt-scoped lane, and is byte-identical
      afterward (asserted on the tip sha and `git status --porcelain`, not on a claim).
  (e) THE DESTRUCTIVE-CASE GUARD: after an interrupt, a work-holding lane's tip is reachable BY
      REFERENCE, not merely present as an object. This is the assertion that catches the measured
      defect where teardown deleted the lane branch, leaving the commits unreferenced with an empty
      reflog. An object-existence assertion would PASS against that behavior and prove nothing.
  (f) a subsequent run of the same Set allocates successfully after an interrupt (the end-to-end
      property the backlog item actually asks for).
  (g) BOTH drivers, via a symmetry assertion that fails if only one was changed.
  (h) THE STALE GUARD: a clean leftover lane whose base is an ANCESTOR of, not equal to, the
      requested base is attempt-scoped and NOT adopted, asserted on the classification AND on the
      resulting lane name, so a regression to a four-state classifier fails here.
  (i) THE NON-DESTRUCTIVE FAILURE-PATH GUARD: a failed `git worktree add` where a work-holding
      branch of that name already exists leaves that branch present, its tip unchanged and still
      reachable by reference. This fails against a name-based `branch -D` cleanup.
  (j) THE LIVE-OWNER GUARD: a lane whose owner process is ALIVE is not adopted (two REAL processes,
      since a same-process simulation cannot show that a live owner is detected), with the
      complement that a lane whose owner is GONE ***is*** adopted, so the guard cannot be satisfied
      by disabling adoption outright.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import pytest

from agent_workflows import agy_runipd as AGY
from agent_workflows import oc_runipd as OC
from agent_workflows import worktree_lease as WL


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )


def out(root: Path, *args: str) -> str:
    return git(root, *args).stdout.strip()


def fixture_repo(tmp: Path, name: str = "repo") -> Path:
    root = tmp / name
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Fixture")
    (root / "README.md").write_text("seed\n")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "seed")
    return root


def commit_in_lane(path: Path, filename: str, body: str = "work\n") -> str:
    (path / filename).write_text(body)
    git(path, "add", filename)
    git(path, "commit", "-q", "-m", f"lane work {filename}")
    return out(path, "rev-parse", "HEAD")


def refs_pointing_at(root: Path, sha: str) -> str:
    return out(root, "for-each-ref", "--points-at", sha, "--format=%(refname)")


class TestAllocationIsIdempotent(unittest.TestCase):
    """(a), (b), (c), (d), (h): allocation tolerates its own debris and destroys nothing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    # (a) the exact reported failure
    def test_a_second_allocation_for_same_lane_id_does_not_raise(self):
        repo = fixture_repo(self.tmp)
        first = WL.allocate_worktree(repo, "abc123")
        # PRE-FIX this raised WorktreeError("... fatal: a branch named 'aw/lane/abc123' already
        # exists"), which is the reported incident verbatim. The second allocation comes BEFORE any
        # assertion on the new fields, so against pre-fix code this test fails on the real BEHAVIOR
        # rather than on a missing attribute.
        second = WL.allocate_worktree(repo, "abc123")
        self.assertEqual(first.disposition, WL.DISPOSITION_CREATED)
        self.assertTrue(second.path.is_dir())
        self.assertIn(
            second.disposition,
            (WL.DISPOSITION_ADOPTED, WL.DISPOSITION_ATTEMPT_SCOPED),
        )

    # (b) a branch-only leftover wedges allocation identically, and refs must be consulted
    def test_b_branch_only_leftover_also_allocates(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "lonely")
        git(repo, "worktree", "remove", "--force", str(handle.path))
        self.assertFalse(handle.path.exists(), "worktree directory is gone")
        self.assertIn("aw/lane/lonely", out(repo, "branch", "--list", "aw/lane/lonely"))
        # PRE-FIX this raised the IDENTICAL `already exists` error as case (a): a surviving branch
        # wedges allocation just as hard as a full lane, and it is the likelier residue.
        again = WL.allocate_worktree(repo, "lonely")
        self.assertTrue(again.path.is_dir())
        # The classifier must SEE the leftover despite the missing directory (refs, not the
        # filesystem): a directory-existence check would have missed this case entirely.
        state = WL.inspect_lane(repo, "lonely")
        self.assertTrue(state.branch_exists)
        self.assertFalse(state.worktree_registered)
        self.assertNotEqual(state.state, WL.LANE_ABSENT)

    # (c) an EMPTY same-base lane is ADOPTED, with no second worktree
    def test_c_empty_same_base_lane_is_adopted(self):
        repo = fixture_repo(self.tmp)
        first = WL.allocate_worktree(repo, "empty1")
        before = out(repo, "worktree", "list")
        second = WL.allocate_worktree(repo, "empty1")
        after = out(repo, "worktree", "list")
        self.assertEqual(second.disposition, WL.DISPOSITION_ADOPTED)
        self.assertEqual(second.branch, first.branch)
        self.assertEqual(second.path, first.path)
        self.assertEqual(before, after, "adoption must not create a second worktree")
        self.assertEqual(
            len(out(repo, "branch", "--list", "aw/lane/*").splitlines()),
            1,
            "adoption must not create a second branch",
        )

    # (d) a lane holding commits is NOT adopted and is byte-identical afterward
    def test_d_work_holding_lane_is_attempt_scoped_and_untouched(self):
        repo = fixture_repo(self.tmp)
        held = WL.allocate_worktree(repo, "worky")
        tip_before = commit_in_lane(held.path, "unmerged.py", "real unmerged work\n")
        porcelain_before = out(held.path, "status", "--porcelain")
        self.assertEqual(WL.inspect_lane(repo, "worky").state, WL.LANE_HOLDS_WORK)

        scoped = WL.allocate_worktree(repo, "worky")
        self.assertEqual(scoped.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)
        self.assertNotEqual(scoped.branch, held.branch)
        self.assertEqual(scoped.displaced_from, held.branch)
        # Byte-identical: proven by sha comparison, not by assertion.
        self.assertEqual(out(repo, "rev-parse", held.branch), tip_before)
        self.assertEqual(out(held.path, "status", "--porcelain"), porcelain_before)
        self.assertIn("refs/heads/" + held.branch, refs_pointing_at(repo, tip_before))

    # (h) THE STALE GUARD: a clean lane at an OLDER base must NOT be adopted
    def test_h_stale_base_lane_is_attempt_scoped_not_adopted(self):
        repo = fixture_repo(self.tmp)
        stale = WL.allocate_worktree(repo, "stale1")
        lane_base = stale.base_commit
        (repo / "mainfile.py").write_text("main advanced after the lane was cut\n")
        git(repo, "add", "mainfile.py")
        git(repo, "commit", "-q", "-m", "main advances")
        requested = out(repo, "rev-parse", "HEAD")
        self.assertNotEqual(lane_base, requested)

        # Assert the CLASSIFICATION, so a regression to a four-state scheme (which would call this
        # EMPTY) fails right here rather than passing silently.
        state = WL.inspect_lane(repo, "stale1")
        self.assertEqual(state.state, WL.LANE_STALE)
        self.assertEqual(state.commits_ahead, 0)
        self.assertFalse(state.dirty)
        self.assertEqual(state.base_sha, lane_base)
        self.assertEqual(state.requested_base, requested)

        scoped = WL.allocate_worktree(repo, "stale1")
        # And assert the resulting NAME, so "it proceeded" is not mistaken for "it was scoped".
        self.assertEqual(scoped.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)
        self.assertNotEqual(scoped.branch, stale.branch)
        # WHY it matters: `aw ipd begin` freezes base_head and finalize computes this execution's
        # changed set as base_head..HEAD, so committing on a lane cut from an OLDER base attributes
        # main's own intervening commits to this execution.
        would_have_been = out(
            repo, "diff", "--name-only", f"{requested}..{stale.branch}"
        )
        self.assertIn(
            "mainfile.py",
            would_have_been,
            "adopting a stale-base lane would mis-attribute main's own file to this execution",
        )


class TestAllocationFailurePathIsNonDestructive(unittest.TestCase):
    """(i): the fail-closed path must clean up only a branch IT created."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_failed_add_with_no_prior_branch_leaves_no_stray_branch(self):
        repo = fixture_repo(self.tmp)
        # Occupy the target directory so `git worktree add` genuinely fails.
        blocked = repo / WL.WORKTREES_SUBDIR / "failme"
        blocked.mkdir(parents=True)
        (blocked / "in_the_way.txt").write_text("occupied\n")
        with self.assertRaises(WL.WorktreeError):
            WL.allocate_worktree(repo, "failme")
        # A failed add still CREATES the branch, so the failure path must remove the one it made.
        self.assertEqual(out(repo, "branch", "--list", "aw/lane/*"), "")

    def test_i_failed_add_never_deletes_a_pre_existing_work_holding_branch(self):
        repo = fixture_repo(self.tmp)
        precious = WL.allocate_worktree(repo, "precious")
        tip = commit_in_lane(
            precious.path, "unmerged.py", "work that must not be lost\n"
        )
        git(repo, "worktree", "remove", "--force", str(precious.path))
        # Force the ADD ITSELF to fail on the attempt-scoped path this allocation will pick.
        blocked = repo / WL.WORKTREES_SUBDIR / "precious_attempt2"
        blocked.mkdir(parents=True)
        (blocked / "in_the_way.txt").write_text("occupied\n")
        with self.assertRaises(WL.WorktreeError):
            WL.allocate_worktree(repo, "precious")
        # PRE-FIX, allocation failed on the `already exists` error BEFORE ever reaching an add, so no
        # cleanup ran; the hazard this pins is the obvious FIX for that, a name-based `branch -D`.
        # A NAME-BASED `branch -D` on the failure path would have deleted this branch, after which
        # no ref pointed at the work and its reflog was empty. Same reference-not-object standard
        # as case (e).
        self.assertEqual(
            out(repo, "branch", "--list", "aw/lane/precious"), "aw/lane/precious"
        )
        self.assertEqual(out(repo, "rev-parse", "aw/lane/precious"), tip)
        self.assertIn("refs/heads/aw/lane/precious", refs_pointing_at(repo, tip))


class TestLaneClassifier(unittest.TestCase):
    """E-01/V-01: all FIVE states, including the one a four-state scheme silently mishandles."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_five_states_are_each_reachable_and_distinct(self):
        repo = fixture_repo(self.tmp)
        self.assertEqual(WL.inspect_lane(repo, "l1").state, WL.LANE_ABSENT)
        WL.allocate_worktree(repo, "l1")
        self.assertEqual(WL.inspect_lane(repo, "l1").state, WL.LANE_EMPTY)

        (repo / "mainfile.py").write_text("advanced\n")
        git(repo, "add", "mainfile.py")
        git(repo, "commit", "-q", "-m", "main advances")
        self.assertEqual(
            WL.inspect_lane(repo, "l1").state,
            WL.LANE_STALE,
            "the SAME untouched lane must become STALE once main advances, not stay EMPTY",
        )

        committed = WL.allocate_worktree(repo, "l2")
        commit_in_lane(committed.path, "w.py")
        self.assertEqual(WL.inspect_lane(repo, "l2").state, WL.LANE_HOLDS_WORK)

        dirty = WL.allocate_worktree(repo, "l3")
        (dirty.path / "loose.py").write_text("uncommitted\n")
        dirty_state = WL.inspect_lane(repo, "l3")
        self.assertEqual(dirty_state.state, WL.LANE_HOLDS_WORK)
        self.assertEqual(
            dirty_state.commits_ahead, 0, "dirty ALONE must count as holding work"
        )
        self.assertTrue(dirty_state.dirty)

        # FOREIGN: a lane cut from an unrelated root.
        git(repo, "checkout", "-q", "--orphan", "unrelated")
        git(repo, "rm", "-q", "-rf", ".")
        (repo / "other.txt").write_text("unrelated history\n")
        git(repo, "add", "other.txt")
        git(repo, "commit", "-q", "-m", "unrelated root")
        unrelated = out(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-q", "main")
        git(
            repo,
            "worktree",
            "add",
            "-q",
            "-b",
            "aw/lane/l4",
            str(repo / WL.WORKTREES_SUBDIR / "l4"),
            unrelated,
        )
        self.assertEqual(WL.inspect_lane(repo, "l4").state, WL.LANE_FOREIGN)

    def test_classifier_reports_the_base_sha_not_merely_a_boolean(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "based")
        state = WL.inspect_lane(repo, "based")
        self.assertEqual(state.base_sha, handle.base_commit)
        self.assertEqual(state.requested_base, handle.base_commit)

    def test_classifier_never_mutates_the_repository(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "readonly")
        tip = commit_in_lane(handle.path, "w.py")
        branches = out(repo, "branch", "--list", "aw/lane/*")
        worktrees = out(repo, "worktree", "list")
        for _ in range(3):
            WL.inspect_lane(repo, "readonly")
        self.assertEqual(out(repo, "branch", "--list", "aw/lane/*"), branches)
        self.assertEqual(out(repo, "worktree", "list"), worktrees)
        self.assertEqual(out(repo, "rev-parse", handle.branch), tip)


class TestDispositionIsReportedWithoutCouplingTheModule(unittest.TestCase):
    """E-03/V-03: the caller can tell adoption from creation, and the module stays stdlib-only."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_all_three_dispositions_are_observable(self):
        repo = fixture_repo(self.tmp)
        created = WL.allocate_worktree(repo, "d1")
        self.assertEqual(created.disposition, WL.DISPOSITION_CREATED)
        adopted = WL.allocate_worktree(repo, "d1")
        self.assertEqual(adopted.disposition, WL.DISPOSITION_ADOPTED)
        commit_in_lane(adopted.path, "w.py")
        scoped = WL.allocate_worktree(repo, "d1")
        self.assertEqual(scoped.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)
        self.assertEqual(scoped.displaced_from, created.branch)

    def test_worktree_lease_stays_stdlib_only(self):
        # Plan `2c122z` E-06 DEPENDS on this: it reuses allocate_worktree for disposable candidate
        # worktrees, so a ledger/run-context import here would couple a low-level primitive to run
        # state and would misrecord candidates as lanes.
        source = Path(WL.__file__).read_text(encoding="utf-8")
        imports = [
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]
        self.assertTrue(imports)
        for line in imports:
            self.assertNotIn("agent_workflows", line, f"non-stdlib import: {line}")
        self.assertNotIn("append_jsonl(", source, "no ledger call in the primitive")
        self.assertNotIn("run_dir", source, "no run context in the primitive")


class TestDriverSymmetry(unittest.TestCase):
    """(g): a one-driver fix would leave `aw agy run` wedgeable by the reported failure."""

    def test_g_both_drivers_expose_the_same_lane_reclamation_surface(self):
        for name in (
            "reclaim_lanes_on_interrupt",
            "describe_lane",
            "format_lane_report",
            "print_lane_interrupt_report",
            "build_recovery_lane_notice",
        ):
            self.assertTrue(
                callable(getattr(OC, name, None)), f"oc_runipd is missing {name}"
            )
            self.assertTrue(
                callable(getattr(AGY, name, None)), f"agy_runipd is missing {name}"
            )

    def test_g_both_drivers_record_lane_identity_at_allocation(self):
        for module in (OC, AGY):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertIn('attempt["worktree_lane_id"]', source, module.__name__)
            self.assertIn('attempt["worktree_base"]', source, module.__name__)
            self.assertIn('attempt["worktree_disposition"]', source, module.__name__)
            self.assertIn('item["preserved_lane_id"]', source, module.__name__)

    def test_g_both_drivers_reclaim_on_the_existing_interrupt_path(self):
        for module in (OC, AGY):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertIn("except KeyboardInterrupt:", source, module.__name__)
            self.assertIn("reclaim_lanes_on_interrupt(", source, module.__name__)

    def test_lane_reclamation_survives_the_runstop_signal_handlers(self):
        # CONSCIOUSLY UPDATED by `runstop` Phase 5 (`71vjbn`), not deleted.
        #
        # This test was authored as "neither driver registers a signal handler", because Phase 5 OWNED
        # that registration and whichever plan registered last would silently win. Phase 5 has now
        # landed it, so the reservation has been redeemed rather than violated.
        #
        # It is not simply removed, because this plan's real stake is different and still live: lane
        # reclamation hangs off the drivers' `except KeyboardInterrupt` path, and installing a SIGINT
        # handler SUPPRESSES the default `KeyboardInterrupt` that path depends on. Phase 5's recorded
        # decision is to PRESERVE it - the terminal rung of the ladder re-raises `KeyboardInterrupt`,
        # so lane reclamation still runs on a third Ctrl-C exactly as it did on the first one before.
        # That is what is asserted here now.
        for module in (OC, AGY):
            source = Path(module.__file__).read_text(encoding="utf-8")
            # Registration goes through the shared installer, so no two plans can race for the signal.
            self.assertIn(
                "runner_stop.install_stop_signal_handlers(", source, module.__name__
            )
            self.assertNotIn("signal.signal(", source, module.__name__)
            # And the path this plan owns is still reachable: something must still RAISE
            # `KeyboardInterrupt` for `reclaim_lanes_on_interrupt` to be invoked at all.
            self.assertIn("raise KeyboardInterrupt(", source, module.__name__)
            self.assertIn("reclaim_lanes_on_interrupt(", source, module.__name__)


class TestReclamationPreservesWorkAndReclaimsOnlyEmpty(unittest.TestCase):
    """(e), (f) and E-05/E-09: the destructive-case guard and the end-to-end property."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        return run_dir

    def _state_for(
        self, repo: Path, lanes: list[tuple[str, WL.WorktreeHandle]]
    ) -> dict:
        return {
            "run_id": "run-fixture",
            "repo": str(repo),
            "queue": [
                {
                    "id6": id6,
                    "setid": "fixture",
                    "position": i + 1,
                    "status": "interrupted",
                    "attempts": [
                        {
                            "worktree": str(handle.path),
                            "worktree_branch": handle.branch,
                            "worktree_lane_id": handle.lane_id,
                            "worktree_base": handle.base_commit,
                            "worktree_disposition": handle.disposition,
                        }
                    ],
                }
                for i, (id6, handle) in enumerate(lanes)
            ],
        }

    # (e) THE DESTRUCTIVE-CASE GUARD
    def test_e_interrupt_leaves_work_holding_lane_reachable_by_reference(self):
        for module in (OC, AGY):
            with self.subTest(driver=module.__name__):
                repo = fixture_repo(self.tmp, f"e_{module.__name__}")
                empty = WL.allocate_worktree(repo, "aaaaaa")
                held = WL.allocate_worktree(repo, "bbbbbb")
                tip = commit_in_lane(
                    held.path, "unmerged.py", "1180 lines of real work\n"
                )
                porcelain_before = out(held.path, "status", "--porcelain")
                run_dir = self._run_dir(repo)
                state = self._state_for(repo, [("aaaaaa", empty), ("bbbbbb", held)])

                lanes = module.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                # The work-holding lane is byte-identical AND its tip is reachable BY REFERENCE.
                # Object existence is NOT enough: a blanket force teardown deletes the branch and
                # leaves the commit as an unreferenced, garbage-collectable object with an empty
                # reflog, which an object-existence assertion would happily accept.
                self.assertEqual(out(repo, "rev-parse", held.branch), tip)
                self.assertIn(
                    "refs/heads/" + held.branch,
                    refs_pointing_at(repo, tip),
                    "the work-holding lane's tip MUST still be reachable by a ref",
                )
                self.assertEqual(
                    out(held.path, "status", "--porcelain"), porcelain_before
                )
                self.assertTrue(
                    held.path.is_dir(), "a work-holding lane is never removed"
                )

                # The provably-empty lane is gone, so the next run is not wedged.
                self.assertFalse(empty.path.exists())
                self.assertEqual(out(repo, "branch", "--list", empty.branch), "")

                by_branch = {lane["branch"]: lane for lane in lanes}
                self.assertEqual(by_branch[held.branch]["action"], "preserved")
                self.assertEqual(by_branch[empty.branch]["action"], "reclaimed")

                # Nothing was stashed, reset, or moved.
                self.assertEqual(out(repo, "stash", "list"), "")

    def test_reclamation_is_idempotent(self):
        repo = fixture_repo(self.tmp)
        empty = WL.allocate_worktree(repo, "aaaaaa")
        held = WL.allocate_worktree(repo, "bbbbbb")
        tip = commit_in_lane(held.path, "w.py")
        run_dir = self._run_dir(repo)
        state = self._state_for(repo, [("aaaaaa", empty), ("bbbbbb", held)])

        first = OC.reclaim_lanes_on_interrupt(repo, run_dir, state, interactive=False)
        second = OC.reclaim_lanes_on_interrupt(repo, run_dir, state, interactive=False)
        self.assertEqual(out(repo, "rev-parse", held.branch), tip)
        self.assertTrue(held.path.is_dir())
        self.assertEqual(
            {lane["branch"] for lane in first if lane.get("action") == "preserved"},
            {lane["branch"] for lane in second if lane.get("action") == "preserved"},
        )

    # E-09: uncommitted lane work is snapshotted, not left loose and not destroyed
    def test_dirty_lane_work_is_snapshotted_on_its_own_branch(self):
        repo = fixture_repo(self.tmp)
        dirty = WL.allocate_worktree(repo, "dddddd")
        (dirty.path / "loose.py").write_text("uncommitted work that matters\n")
        main_porcelain_before = out(repo, "status", "--porcelain")
        main_head_before = out(repo, "rev-parse", "HEAD")
        run_dir = self._run_dir(repo)
        state = self._state_for(repo, [("dddddd", dirty)])

        lanes = OC.reclaim_lanes_on_interrupt(repo, run_dir, state, interactive=False)

        snapshot = lanes[0].get("snapshot_commit")
        self.assertTrue(snapshot, "dirty lane work must be committed, not left loose")
        self.assertIn("refs/heads/" + dirty.branch, refs_pointing_at(repo, snapshot))
        message = out(repo, "log", "-1", "--format=%B", dirty.branch)
        self.assertIn("INTERRUPTED SNAPSHOT", message)
        self.assertIn("NOT validated or reviewed work", message)
        self.assertIn(
            "loose.py", out(repo, "show", "--name-only", "--format=", dirty.branch)
        )
        self.assertTrue(dirty.path.is_dir(), "the lane still exists after a snapshot")
        # MAIN is untouched.
        self.assertEqual(out(repo, "status", "--porcelain"), main_porcelain_before)
        self.assertEqual(out(repo, "rev-parse", "HEAD"), main_head_before)

    def test_clean_lane_gets_no_snapshot_commit(self):
        repo = fixture_repo(self.tmp)
        clean = WL.allocate_worktree(repo, "cccccc")
        tip = commit_in_lane(clean.path, "w.py")
        run_dir = self._run_dir(repo)
        state = self._state_for(repo, [("cccccc", clean)])
        lanes = OC.reclaim_lanes_on_interrupt(repo, run_dir, state, interactive=False)
        self.assertIsNone(lanes[0].get("snapshot_commit"))
        self.assertEqual(out(repo, "rev-parse", clean.branch), tip)

    def test_a_live_owners_lane_is_never_torn_down(self):
        repo = fixture_repo(self.tmp)
        # Written by THIS process, so the owner record names a live pid that is not us... make it a
        # different live pid: pid 1 always exists and is never this test.
        live = WL.allocate_worktree(repo, "eeeeee")
        owner_file = repo / WL.OWNERS_SUBDIR / "eeeeee.json"
        record = json.loads(owner_file.read_text())
        record["pid"] = 1
        record.pop("start_token", None)
        owner_file.write_text(json.dumps(record))
        run_dir = self._run_dir(repo)
        state = self._state_for(repo, [("eeeeee", live)])
        OC.reclaim_lanes_on_interrupt(repo, run_dir, state, interactive=False)
        self.assertTrue(live.path.is_dir(), "a live owner's lane must be left alone")
        self.assertIn(live.branch, out(repo, "branch", "--list", live.branch))

    # (f) the end-to-end property the backlog item asks for
    def test_f_next_run_of_the_same_set_allocates_after_an_interrupt(self):
        repo = fixture_repo(self.tmp)
        run_dir = self._run_dir(repo)
        # Run 1 allocates two lanes; one does real work, one stays empty; then it is interrupted.
        empty = WL.allocate_worktree(repo, "aaaaaa")
        held = WL.allocate_worktree(repo, "bbbbbb")
        held_tip = commit_in_lane(held.path, "unmerged.py")
        state = self._state_for(repo, [("aaaaaa", empty), ("bbbbbb", held)])
        OC.reclaim_lanes_on_interrupt(repo, run_dir, state, interactive=False)

        # Run 2, the SAME Set: both allocations must succeed. PRE-FIX the `bbbbbb` allocation died
        # with `fatal: a branch named 'aw/lane/bbbbbb' already exists` and stayed wedged.
        again_a = WL.allocate_worktree(repo, "aaaaaa")
        again_b = WL.allocate_worktree(repo, "bbbbbb")
        self.assertTrue(again_a.path.is_dir())
        self.assertTrue(again_b.path.is_dir())
        self.assertEqual(again_a.disposition, WL.DISPOSITION_CREATED)
        self.assertEqual(again_b.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)
        # And run 1's real work is still there, untouched.
        self.assertEqual(out(repo, "rev-parse", held.branch), held_tip)
        self.assertIn("refs/heads/" + held.branch, refs_pointing_at(repo, held_tip))


class TestInterruptReportIsActionable(unittest.TestCase):
    """E-06/V-06: the operator can tell an empty lane from a work-holding one without running git."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_report_distinguishes_empty_from_work_holding(self):
        repo = fixture_repo(self.tmp)
        empty = WL.allocate_worktree(repo, "aaaaaa")
        held = WL.allocate_worktree(repo, "bbbbbb")
        commit_in_lane(held.path, "unmerged.py")
        described = [
            OC.describe_lane(
                repo,
                {
                    "id6": "aaaaaa",
                    "lane_id": empty.lane_id,
                    "base_commit": empty.base_commit,
                    "worktree": str(empty.path),
                },
            ),
            OC.describe_lane(
                repo,
                {
                    "id6": "bbbbbb",
                    "lane_id": held.lane_id,
                    "base_commit": held.base_commit,
                    "worktree": str(held.path),
                },
            ),
        ]
        text = OC.format_lane_report(described)
        self.assertIn("HOLDS WORK", text)
        self.assertIn("1 commit(s) beyond base", text)
        self.assertIn(held.branch, text)
        self.assertIn(str(held.path), text)
        self.assertIn("nothing to recover", text)
        # User-facing text: no em or en dashes (execution contract).
        self.assertNotIn("\u2014", text)
        self.assertNotIn("\u2013", text)

    def test_report_facts_come_from_the_classifier(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "ffffff")
        (handle.path / "loose.py").write_text("dirty\n")
        described = OC.describe_lane(
            repo,
            {
                "id6": "ffffff",
                "lane_id": handle.lane_id,
                "base_commit": handle.base_commit,
                "worktree": str(handle.path),
            },
        )
        classified = WL.inspect_lane(
            repo, handle.lane_id, base_commit=handle.base_commit
        )
        self.assertEqual(described["state"], classified.state)
        self.assertEqual(described["dirty"], classified.dirty)
        self.assertEqual(described["commits_ahead"], classified.commits_ahead)
        self.assertEqual(described["holds_work"], classified.holds_work)

    def test_no_new_cli_verb_or_flag_was_added(self):
        # `aw doctor --lanes` and `aw recover <run-id>` are owned by plan `2c122z`.
        cli = Path(Path(OC.__file__).parent / "cli.py").read_text(encoding="utf-8")
        self.assertNotIn("--lanes", cli)
        self.assertNotIn('"recover"', cli)


class TestRecoveryPromptNamesTheLane(unittest.TestCase):
    """E-11/V-11: a resumed turn is TOLD it is resuming, reusing the existing recovery branch."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _item(self, repo: Path, handle: WL.WorktreeHandle) -> dict:
        return {
            "id6": "bbbbbb",
            "setid": "fixture",
            "position": 1,
            "status": "queued",
            "preserved_worktree": str(handle.path),
            "preserved_branch": handle.branch,
            "preserved_lane_id": handle.lane_id,
            "preserved_base": handle.base_commit,
            "attempts": [{"attempt": 1, "worktree_branch": handle.branch}],
        }

    def test_recovery_prompt_states_the_interrupt_and_names_the_lane(self):
        for module in (OC, AGY):
            with self.subTest(driver=module.__name__):
                repo = fixture_repo(self.tmp, f"p_{module.__name__}")
                handle = WL.allocate_worktree(repo, "bbbbbb")
                commit_in_lane(handle.path, "unmerged.py")
                state = {"run_id": "run-fixture", "repo": str(repo)}
                item = self._item(repo, handle)
                run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
                (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
                plan = repo / "plan.ipd.md"
                plan.write_text("# plan\n")

                recovered = module.build_prompt(item, state, run_dir, plan, True)
                self.assertIn("Mode: RECOVERY/CONTINUATION", recovered)
                self.assertIn("continuing an INTERRUPTED attempt", recovered)
                self.assertIn(handle.branch, recovered)
                self.assertIn(str(handle.path), recovered)
                self.assertIn("HOLDS 1 commit(s) beyond its base", recovered)
                self.assertIn("Establish the CURRENT state yourself", recovered)

                normal = module.build_prompt(item, state, run_dir, plan, False)
                self.assertIn("Mode: NORMAL EXECUTION", normal)
                self.assertNotIn("continuing an INTERRUPTED attempt", normal)
                self.assertNotIn(handle.branch, normal)

    def test_no_acknowledgement_gate_or_refusal_path_was_added(self):
        for module in (OC, AGY):
            source = Path(module.__file__).read_text(encoding="utf-8")
            notice = source[source.index("def build_recovery_lane_notice(") :]
            notice = notice[: notice.index("\ndef build_prompt(")]
            # Strip the docstring, which legitimately explains that NO acknowledgement gate exists.
            body = notice.split('"""', 2)[-1]
            for banned in ("input(", "acknowledgement required", "refuse"):
                self.assertNotIn(banned, body, module.__name__)

    def test_snapshot_is_described_as_a_snapshot(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "bbbbbb")
        (handle.path / "loose.py").write_text("dirty\n")
        state = {"run_id": "run-fixture", "repo": str(repo)}
        notice = OC.build_recovery_lane_notice(self._item(repo, handle), state, True)
        self.assertIn("uncommitted changes", notice)
        self.assertIn("INTERRUPTED SNAPSHOT", notice)


class TestOptionalPromptNeverBlocksAnUnattendedRun(unittest.TestCase):
    """E-10/V-10: with no TTY there is no prompt and no wait, ever."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_no_tty_means_no_prompt(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "aaaaaa")
        lane = OC.describe_lane(
            repo,
            {
                "id6": "aaaaaa",
                "lane_id": handle.lane_id,
                "base_commit": handle.base_commit,
                "worktree": str(handle.path),
            },
        )
        # pytest replaces stdin with a non-tty object, so this is the real unattended shape.
        self.assertIsNone(OC._lane_reclaim_prompt(lane, "discard"))
        self.assertIsNone(AGY._lane_reclaim_prompt(lane, "discard"))

    def test_repeated_interrupt_bypasses_the_prompt(self):
        repo = fixture_repo(self.tmp)
        handle = WL.allocate_worktree(repo, "aaaaaa")
        lane = OC.describe_lane(
            repo,
            {
                "id6": "aaaaaa",
                "lane_id": handle.lane_id,
                "base_commit": handle.base_commit,
                "worktree": str(handle.path),
            },
        )
        for module in (OC, AGY):
            with self.subTest(driver=module.__name__):
                saved = module._LANE_PROMPT_DISABLED
                try:
                    module.disable_lane_prompt()
                    self.assertTrue(module._LANE_PROMPT_DISABLED)
                    # Even with a fake TTY the prompt must be skipped once disabled.
                    self.assertIsNone(module._lane_reclaim_prompt(lane, "discard"))
                finally:
                    module._LANE_PROMPT_DISABLED = saved

    def test_second_interrupt_still_preserves_and_reports(self):
        # A repeated interrupt must skip the PROMPT, never the PRESERVATION.
        for module in (OC, AGY):
            source = Path(module.__file__).read_text(encoding="utf-8")
            handler = source[
                source.index(
                    "        except KeyboardInterrupt:\n            # laneorphan"
                ) :
            ]
            handler = handler[: handler.index("            raise")]
            self.assertIn("disable_lane_prompt()", handler, module.__name__)
            self.assertIn("interactive=False", handler, module.__name__)
            self.assertIn("repeated-interrupt", handler, module.__name__)

    def test_prompt_has_a_bounded_wait(self):
        for module in (OC, AGY):
            self.assertIsInstance(module.LANE_PROMPT_TIMEOUT, float)
            self.assertLessEqual(
                module.LANE_PROMPT_TIMEOUT,
                60.0,
                "an unattended run must never block long on shutdown",
            )
            source = Path(module.__file__).read_text(encoding="utf-8")
            prompt = source[source.index("def _lane_reclaim_prompt(") :]
            prompt = prompt[: prompt.index("\ndef ")]
            self.assertIn("select.select", prompt, "the wait must be bounded")
            self.assertIn("isatty", prompt, "a prompt requires a real terminal")


@pytest.mark.slow
class TestLiveOwnerGuardWithTwoRealProcesses(unittest.TestCase):
    """(j)/V-08: only two real processes can show that a LIVE owner is detected."""

    ALLOC_AND_WAIT = textwrap.dedent(
        """
        import json, os, sys
        from pathlib import Path
        from agent_workflows import worktree_lease as WL
        handle = WL.allocate_worktree(Path(sys.argv[1]), sys.argv[2])
        print(json.dumps({"pid": os.getpid(), "branch": handle.branch,
                          "path": str(handle.path), "disposition": handle.disposition}),
              flush=True)
        sys.stdin.readline()
        """
    )
    ALLOC_ONCE = textwrap.dedent(
        """
        import json, sys
        from pathlib import Path
        from agent_workflows import worktree_lease as WL
        handle = WL.allocate_worktree(Path(sys.argv[1]), sys.argv[2])
        print(json.dumps({"branch": handle.branch, "path": str(handle.path),
                          "disposition": handle.disposition,
                          "displaced_from": handle.displaced_from}))
        """
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.alloc_wait = self.tmp / "alloc_and_wait.py"
        self.alloc_wait.write_text(self.ALLOC_AND_WAIT)
        self.alloc_once = self.tmp / "alloc_once.py"
        self.alloc_once.write_text(self.ALLOC_ONCE)
        self.env = dict(os.environ)
        repo_root = str(Path(WL.__file__).resolve().parents[1])
        self.env["PYTHONPATH"] = (
            repo_root + os.pathsep + self.env.get("PYTHONPATH", "")
        ).rstrip(os.pathsep)

    def test_j_live_owner_not_adopted_and_dead_owner_is(self):
        repo = fixture_repo(self.tmp)
        owner = subprocess.Popen(
            [sys.executable, str(self.alloc_wait), str(repo), "X"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=self.env,
        )
        self.addCleanup(owner.kill)
        a_facts = json.loads(owner.stdout.readline())
        self.assertIsNone(owner.poll(), "process A must still be alive")
        a_tip_before = out(Path(a_facts["path"]), "rev-parse", "HEAD")
        a_porcelain_before = out(Path(a_facts["path"]), "status", "--porcelain")

        second = subprocess.run(
            [sys.executable, str(self.alloc_once), str(repo), "X"],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        b_facts = json.loads(second.stdout)

        # A LIVE owner's worktree must never be handed to a second driver.
        self.assertEqual(b_facts["disposition"], WL.DISPOSITION_ATTEMPT_SCOPED)
        self.assertNotEqual(b_facts["branch"], a_facts["branch"])
        self.assertNotEqual(b_facts["path"], a_facts["path"])
        self.assertEqual(out(Path(a_facts["path"]), "rev-parse", "HEAD"), a_tip_before)
        self.assertEqual(
            out(Path(a_facts["path"]), "status", "--porcelain"), a_porcelain_before
        )
        porcelain = out(repo, "worktree", "list", "--porcelain")
        self.assertIn(a_facts["path"], porcelain)
        self.assertIn(b_facts["path"], porcelain)
        # The liveness signal is durable and readable from a FRESH process.
        record = WL.read_lane_owner(repo, "X")
        self.assertEqual(record["pid"], a_facts["pid"])

        # THE COMPLEMENT, which proves adoption was not simply disabled: with the owner GONE, the
        # same lane IS adopted and no second worktree appears.
        owner.stdin.write("\n")
        owner.stdin.flush()
        owner.wait(timeout=30)
        self.assertIsNotNone(
            WL.read_lane_owner(repo, "X"), "record survives process exit"
        )
        before = out(repo, "worktree", "list")
        third = subprocess.run(
            [sys.executable, str(self.alloc_once), str(repo), "X"],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(third.returncode, 0, third.stderr)
        c_facts = json.loads(third.stdout)
        self.assertEqual(c_facts["disposition"], WL.DISPOSITION_ADOPTED)
        self.assertEqual(c_facts["branch"], a_facts["branch"])
        self.assertEqual(out(repo, "worktree", "list"), before)

    def test_j_ambiguous_owner_record_falls_through_to_attempt_scoping(self):
        repo = fixture_repo(self.tmp)
        WL.allocate_worktree(repo, "Y")
        owner_file = repo / WL.OWNERS_SUBDIR / "Y.json"
        record = json.loads(owner_file.read_text())
        record["host"] = "some-other-machine.invalid"
        owner_file.write_text(json.dumps(record))
        safe, reason = WL.lane_is_safe_to_adopt(repo, "Y")
        self.assertFalse(safe, reason)
        scoped = WL.allocate_worktree(repo, "Y")
        self.assertEqual(scoped.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)

    def test_j_unreadable_owner_record_fails_safe(self):
        repo = fixture_repo(self.tmp)
        WL.allocate_worktree(repo, "Z")
        (repo / WL.OWNERS_SUBDIR / "Z.json").write_text("{ not json")
        safe, reason = WL.lane_is_safe_to_adopt(repo, "Z")
        self.assertFalse(safe, reason)
        scoped = WL.allocate_worktree(repo, "Z")
        self.assertEqual(scoped.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)


if __name__ == "__main__":
    unittest.main()
