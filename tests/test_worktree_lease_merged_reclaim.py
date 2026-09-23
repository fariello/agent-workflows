#!/usr/bin/env python3
"""A MERGED lane is reclaimable and is reclaimed on interrupt (laneorph Order 01, `65cuw0`).

THE DEFECT, measured 2026-09-17 and re-measured at review. `worktree_lease.inspect_lane` computes
`commits_ahead` as `rev-list --count <the lane's OWN base>..<head>`, so a lane whose work has been
merged into the integration target KEEPS a non-zero count forever, stays `LANE_HOLDS_WORK`, and was
therefore never reclaimable. Six real lanes each reported `HOLDS-WORK` with 4 to 6 commits ahead while
`git merge-base --is-ancestor <branch> main` returned 0 for every one, so the interrupt-path reclaimer
left each of them on disk permanently.

THIS FILE IS DELIBERATELY TWO LAYERS, because review round 2 measured that the READING and the
BEHAVIOR are separable and that only the second is observable:

  * LAYER 1 (`TheReadingTests`) pins `LaneState.merged_into_target` and `LaneState.reclaimable`. It
    would pass while the interrupt path still preserved every merged lane, so it is NOT evidence that
    the defect is fixed.
  * LAYER 2 (`TheInterruptBehaviorTests`) DRIVES the real `reclaim_lanes_on_interrupt` on BOTH hosts.
    This is the layer that catches the INERT fix: the loop tests `if lane["holds_work"]:` and
    `continue`s BEFORE it reads `reclaimable`, and a merged lane is still `holds_work`, so an
    implementation with the reading but not the decision-order change yields `action = "preserved"`
    here while layer 1 is fully green.
  * LAYER 3 (`TheNoDirectForceTeardownTests`) asserts STRUCTURALLY, by AST, that the merged branch
    reaches the shared spec-R5.5 teardown gate and never a direct
    `worktree_lease.teardown_worktree(..., force=True)`.

EVERY BEHAVIORAL TEST IS PARAMETERIZED OVER BOTH DRIVERS rather than written twice: orchestrator CID-3
makes a rule present in one driver only a DEFECT, and two copied test functions are how such an
omission survives review.

WHAT THE IGNORED-FILE CASE ASSERTS, AND WHY IT IS NOT WHAT THE PLAN'S V-03 WORDING SAYS. The plan
(authored 2026-09-17) expects an unaccounted GITIGNORED file to PRESERVE a merged lane with reason code
`unknown-ignored-file`. Spec `7ckptx` R5.5 was AMENDED on 2026-09-18 - by this plan's own declared
dependency `laneign` `5w8g8j` - to make gitignored files DISPOSABLE upon lane destruction, precisely
because the blanket refusal fired on 100 percent of clean runs (any lane that ran the suite holds
`__pycache__`) and stranded 38 worktrees. `LaneInventory.unknown` excludes `unknown_ignored` and
`reason_codes` never emits `RETENTION_UNKNOWN_IGNORED`, and `tests/test_lane_retention.py` pins that.
So the plan's wording is stale, and implementing it would FORK R5.5 (a stricter rule on the interrupt
path than on the success path), which R6.1 forbids. The HAZARD the requirement exists for is covered by
the two conditions amended R5.5 actually names, and both are pinned below: an unaccounted UNTRACKED
file (the `wfamig` hazard class - a merged lane holding the only copy of a real source file) and an
uncollected submission. See decision `08-65cuw0-D3`.
"""

from __future__ import annotations

import ast
import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import agy_runipd as AGY
from agent_workflows import lane_containment as LC
from agent_workflows import oc_runipd as OC
from agent_workflows import runner_shared
from agent_workflows import worktree_lease as WL

#: The two host drivers the reclaim decision must be wired into IDENTICALLY (orchestrator CID-3).
DRIVERS = (("oc", OC), ("agy", AGY))


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return proc.stdout.strip()


def git_rc(repo: Path, *args: str) -> int:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True).returncode


class MergedLaneFixture:
    """A REAL repository with REAL lane worktrees, cut from an OLDER base so a merge is meaningful.

    A REAL REPOSITORY RATHER THAN A FAKE `LaneState`, deliberately and for the same reason
    `tests/test_lane_retention.py` gives: the property under test is what GIT reports about a merged
    branch, and a hand-built namedtuple would assert only that the test's own fixture agrees with
    itself. It could not catch `commits_ahead` being computed against the wrong base, which IS the
    defect.
    """

    def __init__(self, root: Path, name: str = "repo") -> None:
        self.repo = root / name
        self.repo.mkdir(parents=True)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        # A REAL ignore rule, so the gitignored case is genuinely ignored rather than reported `??`.
        (self.repo / ".gitignore").write_text("build/\n", encoding="utf-8")
        (self.repo / "README.md").write_text("seed\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore", "README.md")
        git(self.repo, "commit", "-q", "-m", "seed")
        #: The OLDER base every lane is cut from. Without this, a lane cut from HEAD would be an
        #: ancestor of the target trivially and the merge under test would be a no-op.
        self.older = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "moved-on.md").write_text("main moved on\n", encoding="utf-8")
        git(self.repo, "add", "moved-on.md")
        git(self.repo, "commit", "-q", "-m", "main advances past the lane base")
        self.run_dir = self.repo / ".aw" / "records" / "runs" / "run-fixture"
        (self.run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        self._position = 0

    # -- lane shapes -------------------------------------------------------------------------------
    def lane_with_commit(self, lane_id: str, *, from_older: bool = True) -> Any:
        handle = WL.allocate_worktree(
            self.repo, lane_id, base_commit=self.older if from_older else "HEAD"
        )
        (handle.path / f"{lane_id}.py").write_text(
            "real work that must not be lost\n", encoding="utf-8"
        )
        git(handle.path, "add", f"{lane_id}.py")
        git(handle.path, "commit", "-q", "-m", f"lane work {lane_id}")
        return handle

    def merge_into_target(self, handle: Any) -> None:
        """Land the lane the way the drivers do: a controlled `--no-ff` merge in the main checkout."""
        git(
            self.repo, "merge", "--no-ff", "-m", f"merge {handle.branch}", handle.branch
        )

    def merged_lane(self, lane_id: str) -> Any:
        handle = self.lane_with_commit(lane_id)
        self.merge_into_target(handle)
        return handle

    def empty_lane(self, lane_id: str) -> Any:
        """A lane reclaimable TODAY: clean, no commits, at the CURRENT base."""
        return WL.allocate_worktree(self.repo, lane_id, base_commit="HEAD")

    def add_untracked(self, handle: Any, rel: str = "unexplained.py") -> Path:
        target = handle.path / rel
        target.write_text("the only copy of something\n", encoding="utf-8")
        return target

    def add_gitignored(self, handle: Any, rel: str = "build/residue.txt") -> Path:
        """A gitignored residue, ASSERTED to be ignored by git.

        THE ASSERTION IS THE POINT, copied from `tests/test_lane_retention.py`'s reasoning: a path git
        does NOT actually ignore is reported `??` and lands in `unknown_untracked`, so a test using it
        would prove the UNTRACKED rule while claiming to prove the ignored one.
        """
        target = handle.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("regenerable residue\n", encoding="utf-8")
        assert (
            git_rc(handle.path, "check-ignore", "-q", rel) == 0
        ), f"fixture error: git does not ignore {rel!r}"
        return target

    # -- driver records ----------------------------------------------------------------------------
    def item_for(self, handle: Any) -> dict[str, Any]:
        self._position += 1
        return {
            "position": self._position,
            "id6": handle.lane_id,
            "setid": "laneorph",
            "status": "interrupted",
            "attempts": [
                {
                    "number": 1,
                    "worktree": str(handle.path),
                    "worktree_branch": handle.branch,
                    "worktree_lane_id": handle.lane_id,
                    "worktree_base": handle.base_commit,
                    "worktree_disposition": handle.disposition,
                }
            ],
        }

    def write_collection_receipt(self, item: dict[str, Any], handle: Any) -> Path:
        """A COMPLETE receipt, i.e. the driver provably holds this lane's submissions (spec R2.5).

        WITHOUT ONE THE GATE REFUSES, which is itself pinned below: `submission_retention` answers
        `uncollected=True` when no attempt-keyed receipt exists, because absence means NOT collected.
        """
        path = LC.collection_receipt_path(self.run_dir, item, 1)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": "run-fixture",
                    "position": item["position"],
                    "id6": item["id6"],
                    "attempt": 1,
                    "lane_root": str(handle.path),
                    "status": LC.RECEIPT_COMPLETE,
                    "submissions": [{"name": "outcome", "result": "absent"}],
                }
            ),
            encoding="utf-8",
        )
        return path

    def state_for(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {"run_id": "run-fixture", "repo": str(self.repo), "queue": list(items)}

    def inspect(self, lane_id: str) -> WL.LaneState:
        return WL.inspect_lane(self.repo, lane_id, base_commit="HEAD")

    def worktrees(self) -> str:
        return git(self.repo, "worktree", "list")


class _FixtureCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)


# ======================================================================================================
# LAYER 1: the READING (E-01, E-02). Necessary, and NOT sufficient - see this module's docstring.
# ======================================================================================================


class TheReadingTests(_FixtureCase):
    """`LaneState.merged_into_target` and the widened `reclaimable`."""

    def test_a_merged_lane_reports_merged_while_KEEPING_its_real_commits_ahead(self):
        """E-01's central claim: a field was ADDED, not substituted.

        `commits_ahead` MUST still be non-zero for a merged lane. It is the input to the lane-REUSE
        question (`LANE_EMPTY`/`LANE_STALE`/`LANE_FOREIGN` decide whether a lane may be ADOPTED for a
        fresh execution), so silently redefining it would change which lanes get reused.
        """
        fx = MergedLaneFixture(self.tmp)
        handle = fx.lane_with_commit("mrgd01")
        before = fx.inspect("mrgd01")
        self.assertFalse(
            before.merged_into_target, "an unmerged lane must not report merged"
        )
        self.assertEqual(before.state, WL.LANE_HOLDS_WORK)
        self.assertGreater(before.commits_ahead, 0)

        fx.merge_into_target(handle)
        after = fx.inspect("mrgd01")

        self.assertTrue(after.merged_into_target, "a merged lane must report merged")
        # The defect's signature, still present and still correct: merging does NOT reset this figure.
        self.assertEqual(
            after.commits_ahead,
            before.commits_ahead,
            "`commits_ahead` must keep its meaning; it is the lane-REUSE input",
        )
        self.assertEqual(after.state, WL.LANE_HOLDS_WORK)
        self.assertTrue(after.holds_work)
        # And git agrees, independently of our reading.
        self.assertEqual(
            git_rc(fx.repo, "merge-base", "--is-ancestor", handle.branch, "main"), 0
        )

    def test_an_unanswerable_landing_question_is_NOT_merged(self):
        """`lane_work_has_landed` is three-valued; `None` must collapse to False, never True.

        A `NamedTuple` boolean cannot express "unanswerable", and collapsing it to True would authorize
        reclaiming a lane whose recovery was never proven.
        """
        fx = MergedLaneFixture(self.tmp)
        handle = fx.lane_with_commit("gone01")
        fx.merge_into_target(handle)
        git(fx.repo, "worktree", "remove", "--force", str(handle.path))
        git(fx.repo, "branch", "-D", handle.branch)

        state = fx.inspect("gone01")
        self.assertFalse(state.branch_exists)
        self.assertFalse(
            state.merged_into_target,
            "an unanswerable landing question must never read as merged",
        )
        self.assertFalse(state.reclaimable)

    def test_a_merged_CLEAN_lane_is_reclaimable(self):
        fx = MergedLaneFixture(self.tmp)
        fx.merged_lane("mrgd02")
        state = fx.inspect("mrgd02")
        self.assertTrue(state.merged_into_target)
        self.assertFalse(state.dirty)
        self.assertTrue(
            state.reclaimable,
            "PRE-FIX this was False forever, which is the whole defect",
        )

    def test_a_merged_DIRTY_lane_is_NOT_reclaimable(self):
        """The dirty half of the safety rule must not be weakened by the merged case."""
        fx = MergedLaneFixture(self.tmp)
        handle = fx.merged_lane("mrgd03")
        (handle.path / "mrgd03.py").write_text(
            "edited after the merge\n", encoding="utf-8"
        )
        state = fx.inspect("mrgd03")
        self.assertTrue(state.merged_into_target)
        self.assertTrue(state.dirty)
        self.assertFalse(state.reclaimable)

    def test_an_UNMERGED_lane_is_unaffected(self):
        fx = MergedLaneFixture(self.tmp)
        fx.lane_with_commit("unmrg1")
        state = fx.inspect("unmrg1")
        self.assertFalse(state.merged_into_target)
        self.assertFalse(state.reclaimable)
        self.assertTrue(state.holds_work)

    def test_a_lane_reclaimable_TODAY_still_is(self):
        """REGRESSION GUARD on the pre-existing `LANE_EMPTY`/`LANE_STALE` path."""
        fx = MergedLaneFixture(self.tmp)
        fx.empty_lane("empty1")
        state = fx.inspect("empty1")
        self.assertEqual(state.state, WL.LANE_EMPTY)
        self.assertEqual(state.commits_ahead, 0)
        self.assertFalse(state.dirty)
        self.assertTrue(state.reclaimable)

    def test_the_landing_question_has_exactly_ONE_definition(self):
        """E-01 requires DELEGATION, not a second `merge-base --is-ancestor` call (spec R6.1).

        Asserted by AST over the whole package rather than by reading the diff: the count is what makes
        "we did not fork the predicate" falsifiable.
        """
        package = Path(str(WL.__file__)).parent
        callers: list[str] = []
        for path in sorted(package.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                for arg in node.args:
                    if not isinstance(arg, ast.List):
                        continue
                    literals = [
                        el.value
                        for el in arg.elts
                        if isinstance(el, ast.Constant) and isinstance(el.value, str)
                    ]
                    if "merge-base" in literals and "--is-ancestor" in literals:
                        callers.append(f"{path.name}:{node.lineno}")
        # `worktree_lease` has ONE (`base_sha` vs `requested_base`, the STALE/FOREIGN question, which is
        # a different question against different refs) and `runner_shared` has ONE (the landing
        # predicate). The landing question itself must exist exactly once.
        self.assertIn("runner_shared.py", " ".join(callers), callers)
        landing = [c for c in callers if c.startswith("runner_shared.py")]
        self.assertEqual(
            len(landing),
            1,
            f"the landing predicate must exist exactly ONCE; found {landing}",
        )
        # And the lease module reaches it by DELEGATION rather than issuing its own. Asserted over the
        # CODE, not the source text: the docstring legitimately QUOTES the git command it delegates to,
        # so a text search would be satisfied by prose and would also fail for the honest docstring.
        body = ast.parse(inspect.getsource(WL.lane_merged_into_target)).body[0]
        assert isinstance(body, ast.FunctionDef)
        called = {
            node.func.attr
            for node in ast.walk(body)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertIn("lane_work_has_landed", called)
        string_args = [
            el.value
            for node in ast.walk(body)
            if isinstance(node, ast.Call)
            for arg in node.args
            if isinstance(arg, ast.List)
            for el in arg.elts
            if isinstance(el, ast.Constant) and isinstance(el.value, str)
        ]
        self.assertNotIn(
            "--is-ancestor",
            string_args,
            "the lease module must DELEGATE the landing question, not issue its own git call",
        )

    def test_the_reclaimable_docstring_states_it_is_NOT_an_authorization(self):
        """E-02: the old "safe to tear down" sentence became false once merged lanes qualified.

        A stale authorization claim in the codebase is how a future caller reaches
        `teardown_worktree(force=True)` believing the reading cleared it.
        """
        doc = WL.LaneState.reclaimable.__doc__ or ""
        self.assertIn("NECESSARY BUT NOT SUFFICIENT", doc)
        self.assertIn("teardown_lane_if_classified", doc)
        # The SUMMARY LINE is what a reader and an IDE tooltip see, so the withdrawn claim must not be
        # there. The body may (and does) explain that the old wording was withdrawn and why, which is
        # more useful than deleting the history of the correction.
        self.assertNotIn("safe to tear down", doc.splitlines()[0])
        self.assertIn("withdrawn", doc)


# ======================================================================================================
# LAYER 2: the BEHAVIOR (E-03). THIS is the layer that proves the fix is not inert.
# ======================================================================================================


class TheInterruptBehaviorTests(_FixtureCase):
    """Drive the real `reclaim_lanes_on_interrupt` on BOTH hosts."""

    def test_a_merged_accounted_lane_is_RECLAIMED_not_preserved(self):
        """THE ITEM THAT WOULD HAVE CAUGHT AN INERT FIX.

        An implementation carrying E-01 and E-02 but NOT E-03's decision-order change yields
        `action = "preserved"` here while every layer-1 assertion above is green, because the loop bails
        out on `holds_work` before it ever reads `reclaimable`.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("mrgacc")
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)
                state = fx.state_for([item])

                self.assertIn(str(handle.path), fx.worktrees())
                lanes = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, state, interactive=False
                )

                lane = lanes[0]
                self.assertEqual(
                    lane["action"],
                    "reclaimed",
                    f"{host}: a merged, accounted lane must be reclaimed; got {lane!r}",
                )
                self.assertTrue(lane["merged_into_target"])
                self.assertTrue(
                    lane["holds_work"],
                    "the merged lane is STILL holds_work; that is why the ORDER matters",
                )
                self.assertFalse(handle.path.exists())
                self.assertNotIn(str(handle.path), fx.worktrees())

    def test_the_reclaim_is_recorded_as_an_event(self):
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("mrgevt")
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)
                driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                )
                events = [
                    json.loads(line)
                    for line in (fx.run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                reclaimed = [
                    e for e in events if e["event"] == "lane-reclaimed-on-interrupt"
                ]
                self.assertEqual(len(reclaimed), 1, events)
                self.assertEqual(reclaimed[0]["branch"], handle.branch)
                self.assertTrue(reclaimed[0]["merged_into_target"])

    def test_a_merged_lane_with_an_unaccounted_UNTRACKED_file_is_PRESERVED(self):
        """THE `wfamig` HAZARD CLASS: a merged lane holding the ONLY copy of a real source file.

        Measured in the 2026-09-17 sweep: lane `wfamig` was fully merged and held an untracked 89-line
        plan that existed NOWHERE in `main`. A merged-ness-only teardown would have deleted the only
        copy. This is the case amended spec R5.5 still refuses on, and it is the reason merged-ness
        alone must never authorize destruction.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("mrgunt")
                precious = fx.add_untracked(handle)
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)

                lanes = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                )

                lane = lanes[0]
                self.assertEqual(lane["action"], "preserved", lane)
                self.assertTrue(handle.path.is_dir(), f"{host}: the lane must survive")
                self.assertTrue(
                    precious.exists(), f"{host}: the only copy must still be on disk"
                )
                self.assertEqual(
                    git_rc(fx.repo, "rev-parse", "--verify", handle.branch), 0
                )

    def test_a_merged_lane_with_NO_collection_receipt_is_PRESERVED_with_its_reason(
        self,
    ):
        """The gate's other refusal condition under amended R5.5, plus the R5.6 reason record.

        `submission_retention` answers `uncollected=True` when no attempt-keyed receipt exists, because
        absence means NOT collected: a driver that crashed before collecting leaves exactly this state
        and the lane holds the only copy of its submission.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("norcpt")
                item = fx.item_for(handle)
                # DELIBERATELY no receipt.

                lanes = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                )

                lane = lanes[0]
                self.assertEqual(lane["action"], "preserved", lane)
                self.assertIn(
                    LC.RETENTION_UNCOLLECTED_SUBMISSION,
                    lane["retention_reason_codes"],
                    f"{host}: the refusal must name WHICH condition held (spec R5.6)",
                )
                self.assertIn("uncollected submission", lane["retention_reason"])
                self.assertTrue(handle.path.is_dir())
                # R5.6a: the preservation is in DURABLE STATE too, so the run summary can name it.
                self.assertEqual(item["preserved_branch"], handle.branch)
                self.assertIn(
                    LC.RETENTION_UNCOLLECTED_SUBMISSION,
                    item["preserved_retention_reasons"],
                )

    def test_a_merged_lane_holding_ONLY_gitignored_residue_IS_reclaimed(self):
        """AMENDED R5.5 (2026-09-18, `laneign` `5w8g8j`): gitignored content is DISPOSABLE.

        THIS ASSERTION IS THE OPPOSITE OF THIS PLAN'S V-03 WORDING, and that is deliberate: the plan
        was authored 2026-09-17, the day before the amendment, so its wording predates the rule it is
        told to comply with. Implementing the plan's letter would FORK R5.5 (a stricter rule on the
        interrupt path than on the success path), which R6.1 forbids, and would red
        `tests/test_lane_retention.py::test_a_lane_holding_ONLY_gitignored_files_IS_torn_down`.

        The protection that matters is untouched and is pinned by the two tests above: uncommitted work
        is UNTRACKED or DIRTY, never gitignored. See decision `08-65cuw0-D3`. If the maintainer restores
        the pre-amendment rule, THIS is the assertion to flip.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("mrgign")
                fx.add_gitignored(handle)
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)

                # The inventory SEES it (the enumeration passes `--ignored=traditional`) and
                # deliberately does not refuse on it.
                inv = LC.inventory_lane(
                    lane_root=handle.path, run_dir=fx.run_dir, item=item
                )
                self.assertTrue(
                    inv.unknown_ignored, "the ignored file must be ENUMERATED"
                )
                self.assertTrue(inv.classified, inv.reason)
                self.assertEqual(inv.reason_codes, ())

                lanes = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                )
                self.assertEqual(lanes[0]["action"], "reclaimed", lanes[0])
                self.assertFalse(handle.path.exists())

    def test_an_UNMERGED_lane_still_takes_the_snapshot_and_preserve_path(self):
        """E-03 reorders a shared control path, and the `holds_work` branch is where snapshotting lives.

        THE LIKELIEST ACCIDENTAL CASUALTY of the reorder, which is why it is asserted explicitly.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.lane_with_commit("unmrgd")
                tip = git(handle.path, "rev-parse", "HEAD")
                (handle.path / "loose.py").write_text("uncommitted\n", encoding="utf-8")
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)

                lanes = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                )

                lane = lanes[0]
                self.assertEqual(lane["action"], "preserved", lane)
                self.assertFalse(lane["merged_into_target"])
                snapshot = lane.get("snapshot_commit")
                self.assertTrue(
                    snapshot,
                    f"{host}: dirty lane work must be SNAPSHOTTED, not left loose",
                )
                self.assertIn(
                    "INTERRUPTED SNAPSHOT",
                    git(fx.repo, "log", "-1", "--format=%B", handle.branch),
                )
                self.assertNotEqual(snapshot, tip)
                self.assertTrue(handle.path.is_dir())
                self.assertEqual(
                    git_rc(fx.repo, "rev-parse", "--verify", handle.branch), 0
                )
                # Nothing was stashed, reset, or moved.
                self.assertEqual(git(fx.repo, "stash", "list"), "")

    def test_a_provably_EMPTY_lane_is_still_reclaimed(self):
        """REGRESSION CHECK ON TODAY'S RECLAIM, pinned on BOTH hosts.

        An empty lane cut from HEAD is TRIVIALLY an ancestor of the target, so `merged_into_target` is
        True for it. Without the `holds_work` clause in `lane_is_recovered_and_reclaimable` it would be
        diverted into the R5.5 gate, refused for an uncollected submission (an interrupted lane has no
        completed receipt), and PRESERVED - turning the leak fix into a leak. Measured while building
        this; that is why the clause exists and why this assertion is here.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.empty_lane("empty2")
                item = fx.item_for(handle)

                lanes = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                )

                self.assertEqual(lanes[0]["action"], "reclaimed", lanes[0])
                self.assertFalse(handle.path.exists())
                self.assertEqual(git(fx.repo, "branch", "--list", handle.branch), "")

    def test_reclamation_of_a_merged_lane_is_IDEMPOTENT(self):
        """`reclaim_lanes_on_interrupt`'s documented contract: safe to call twice."""
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("idemp1")
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)
                state = fx.state_for([item])

                first = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, state, interactive=False
                )
                second = driver.reclaim_lanes_on_interrupt(
                    fx.repo, fx.run_dir, state, interactive=False
                )
                self.assertEqual(first[0]["action"], "reclaimed")
                # The second pass sees an ABSENT lane and does nothing at all.
                self.assertEqual(second[0]["state"], WL.LANE_ABSENT)
                self.assertIsNone(second[0].get("action"))

    def test_the_merged_decision_is_the_SHARED_predicate_on_both_hosts(self):
        """Spec R6.1 / CID-3: one predicate, reached identically, not two agreeing copies.

        DRIVEN, NOT GREPPED. A source search would be satisfied by the comment that names the symbol;
        the spy proves a REAL reclaim actually consults it, and the identity check proves neither host
        holds its own copy.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                self.assertIs(
                    driver.runner_shared.lane_is_recovered_and_reclaimable,
                    runner_shared.lane_is_recovered_and_reclaimable,
                    f"{host} must reach the SHARED predicate",
                )
                self.assertIs(
                    driver.runner_shared.reclaim_lane_through_gate,
                    runner_shared.reclaim_lane_through_gate,
                    f"{host} must reach the SHARED teardown call",
                )

                fx = MergedLaneFixture(self.tmp, name=f"repo-{host}")
                handle = fx.merged_lane("shared1")
                item = fx.item_for(handle)
                fx.write_collection_receipt(item, handle)

                seen: list[dict[str, Any]] = []
                real = runner_shared.lane_is_recovered_and_reclaimable

                def spy(lane, _seen=seen, _real=real):
                    _seen.append(lane)
                    return _real(lane)

                original = runner_shared.lane_is_recovered_and_reclaimable
                runner_shared.lane_is_recovered_and_reclaimable = spy
                try:
                    lanes = driver.reclaim_lanes_on_interrupt(
                        fx.repo, fx.run_dir, fx.state_for([item]), interactive=False
                    )
                finally:
                    runner_shared.lane_is_recovered_and_reclaimable = original

                self.assertEqual(
                    len(seen), 1, f"{host} never consulted the shared predicate"
                )
                self.assertEqual(lanes[0]["action"], "reclaimed")


# ======================================================================================================
# LAYER 3: the STRUCTURAL invariant (E-05).
# ======================================================================================================


def _find_merged_branch(node: ast.FunctionDef) -> ast.If | None:
    """The `lane_is_recovered_and_reclaimable(lane)` branch of a reclaimer body, or None.

    MATCHES BOTH CALL FORMS, which became necessary when `gqo6if` E-03 gave the two hosts one shared
    implementation: in a host body the call was `runner_shared.lane_is_recovered_and_reclaimable(...)`
    (an `ast.Attribute`), while inside `runner_shared` itself the same call is the bare
    `lane_is_recovered_and_reclaimable(...)` (an `ast.Name`). An attribute-only matcher would report the
    branch as MISSING from the very module that now contains it.
    """
    for child in ast.walk(node):
        if not isinstance(child, ast.If):
            continue
        test = child.test
        if not isinstance(test, ast.Call):
            continue
        func = test.func
        name = (
            func.attr
            if isinstance(func, ast.Attribute)
            else (func.id if isinstance(func, ast.Name) else "")
        )
        if name == "lane_is_recovered_and_reclaimable":
            return child
    return None


def _has_merged_branch(node: ast.FunctionDef) -> bool:
    return _find_merged_branch(node) is not None


class TheNoDirectForceTeardownTests(unittest.TestCase):
    """The merged branch reaches the shared gate, never a direct force teardown.

    SCOPED HONESTLY, because the repository holds FOUR direct force-teardown callers and a repo-wide
    count would be wrong in both directions:

      * `oc_runipd` / `agy_runipd`: the operator-`discard` branch and the pre-existing provably-EMPTY
        branch. BOTH PREDATE THIS PLAN and are deliberately unchanged (see decision `08-65cuw0-D1`:
        routing the empty branch through the gate would refuse every interrupted lane, since none has a
        completed collection receipt, and would red two existing test files).
      * `runner_shared.teardown_isolation_worktree`: the shared GATE'S OWN remover. It must keep working,
        so an assertion forbidding it would forbid the gate its own mechanism.
      * `runner_shared`'s no-files-changed cleanup: untouched by this plan.

    So what is asserted is the property that is both TRUE and load-bearing: the MERGED branch calls the
    shared gate and contains no direct `teardown_worktree`, on both hosts.
    """

    @staticmethod
    def _reclaimer_ast(driver: Any) -> ast.FunctionDef:
        """The reclaimer's DECISION LOGIC, wherever it now lives.

        RE-BASED BY runresidue 01 (`gqo6if`) E-03, which gave the two hosts ONE implementation in
        `runner_shared` and left a one-line wrapper on each. Reading `driver.reclaim_lanes_on_interrupt`
        after that lift returns the WRAPPER, which contains no decision at all, so every structural
        assertion below would look for a merged-lane branch in a body that has none and fail with
        "no merged-lane branch found" - a RED that would mean the opposite of what it says, since the
        decision order it guards was never touched.
        RESOLVED BY FOLLOWING THE LOGIC RATHER THAN BY WEAKENING THE ASSERTION: the wrapper is
        unwrapped to the shared implementation, so the decision-order property is still asserted, now at
        the single place it is implemented. Each host's own binding is separately proven to reach that
        implementation by the delegation test in `tests/test_rununify_run_queue.py`, and the BEHAVIORAL
        layer in this same file still drives each host end to end, which is what makes unwrapping safe:
        structure is checked once because there IS one body, while behavior is still checked twice.
        """
        source = inspect.getsource(driver.reclaim_lanes_on_interrupt)
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)
        if not _has_merged_branch(node):
            shared = ast.parse(
                inspect.getsource(runner_shared.reclaim_lanes_on_interrupt)
            ).body[0]
            assert isinstance(shared, ast.FunctionDef)
            # The wrapper must REALLY delegate to the body being read, or unwrapping would silently
            # assert a property of code this host does not run.
            assert "reclaim_lanes_on_interrupt" in TheNoDirectForceTeardownTests._calls(
                node
            ), (
                f"{driver.__name__}.reclaim_lanes_on_interrupt has no merged-lane branch AND does "
                "not delegate, so its decision logic cannot be located"
            )
            return shared
        return node

    @staticmethod
    def _merged_branch(node: ast.FunctionDef) -> ast.If:
        """The `lane_is_recovered_and_reclaimable(lane)` branch, found by AST."""
        branch = _find_merged_branch(node)
        if branch is None:
            raise AssertionError(
                "no merged-lane branch found; the fix is INERT without the decision-order change"
            )
        return branch

    @staticmethod
    def _calls(node: ast.AST) -> list[str]:
        names: list[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute):
                    names.append(func.attr)
                elif isinstance(func, ast.Name):
                    names.append(func.id)
        return names

    def test_the_merged_branch_reaches_the_shared_gate_and_no_direct_force_teardown(
        self,
    ):
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                branch = self._merged_branch(self._reclaimer_ast(driver))
                calls = self._calls(branch)
                self.assertIn(
                    "reclaim_lane_through_gate",
                    calls,
                    f"{host}: the merged reclaim must go through the shared R5.5 gate",
                )
                self.assertNotIn(
                    "teardown_worktree",
                    calls,
                    f"{host}: the merged reclaim must NOT force-delete directly",
                )
                self.assertNotIn("teardown_isolation_worktree", calls, host)

    def test_the_merged_decision_PRECEDES_the_holds_work_bail_out(self):
        """THE DECISION ORDER, asserted structurally rather than trusted.

        Measured at review: the loop tests `if lane["holds_work"]:` and `continue`s BEFORE it reads
        `reclaimable`, and a merged lane is still `holds_work`, so a reading-only fix changes nothing
        observable. A future edit that moves the merged check back below the bail-out reintroduces
        exactly that inert state, and this is what catches it.
        """
        for host, driver in DRIVERS:
            with self.subTest(host=host):
                node = self._reclaimer_ast(driver)
                merged_line = self._merged_branch(node).lineno
                holds_work_lines = [
                    child.lineno
                    for child in ast.walk(node)
                    if isinstance(child, ast.If)
                    and isinstance(child.test, ast.Subscript)
                    and isinstance(child.test.slice, ast.Constant)
                    and child.test.slice.value == "holds_work"
                ]
                self.assertTrue(holds_work_lines, f"{host}: no holds_work guard found")
                self.assertLess(
                    merged_line,
                    min(holds_work_lines),
                    f"{host}: the merged check MUST precede the holds_work bail-out or the fix is inert",
                )

    def test_the_gate_helper_calls_the_ONE_shared_teardown_gate(self):
        """`reclaim_lane_through_gate` must delegate, not reimplement (spec R6.1)."""
        node = ast.parse(
            inspect.getsource(runner_shared.reclaim_lane_through_gate)
        ).body[0]
        assert isinstance(node, ast.FunctionDef)
        # OVER THE CODE, not the source text: the docstring legitimately NAMES the dangerous call it
        # replaces, and explaining that is exactly what makes the function's contract readable.
        calls = self._calls(node)
        self.assertIn("teardown_lane_if_classified", calls)
        self.assertNotIn("teardown_worktree", calls)
        # And it forwards BOTH run-context fields the inventory needs; without either, the gate refuses
        # every lane (measured).
        forwarded = {
            kw.arg
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            for kw in child.keywords
        }
        self.assertIn("run_dir", forwarded)
        self.assertIn("item", forwarded)

    def test_the_three_legitimate_force_teardown_callers_are_NOT_flagged(self):
        """An over-broad assertion that reds on untouched code gets reverted by the next executor.

        These callers are enumerated so a reader can see the assertion above is narrow ON PURPOSE.
        """
        package = Path(str(WL.__file__)).parent
        flagged: list[str] = []
        for path in sorted(package.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else (func.id if isinstance(func, ast.Name) else "")
                )
                if name != "teardown_worktree":
                    continue
                if any(
                    kw.arg == "force"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                    for kw in node.keywords
                ):
                    flagged.append(f"{path.name}:{node.lineno}")
        # The GATE's own remover must be among them and must keep working.
        self.assertTrue(
            any(c.startswith("runner_shared.py") for c in flagged),
            f"the gate's own remover must still call it; found {flagged}",
        )
        # And the assertion under test does not look at these at all: it is scoped to the merged branch.
        for host, driver in DRIVERS:
            branch = TheNoDirectForceTeardownTests._merged_branch(
                TheNoDirectForceTeardownTests._reclaimer_ast(driver)
            )
            self.assertNotIn("teardown_worktree", self._calls(branch), host)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
