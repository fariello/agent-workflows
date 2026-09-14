"""Lane RETENTION: a lane is destroyed only when the driver can account for everything in it.

Covers spec `7ckptx` R5.5, R5.6 and R5.6a (criteria A15, A15b) for plan `xdr83v` E-01..E-03.

WHY THESE ASSERTIONS ARE SHAPED THE WAY THEY ARE, since the obvious version of each is the one the
spec calls insufficient:

  * THE IGNORED CASE IS FIRST-CLASS, not a variation on the untracked one. Enumerating only untracked
    content leaves ignored content invisible, and "ignored means disposable" is precisely the reasoning
    that destroyed lane content silently before (spec R5.5, plan F-1). `IgnoredEnumerationTests`
    therefore proves the enumeration SEES ignored files, and does it by REMOVING the ignored half of
    the flags and showing the file stops being reported: a suite that passes for the untracked file
    while silently missing the ignored one is the exact defect the requirement exists to prevent.
  * DISCARDABILITY COMES FROM RECORDS, NOT FROM PATHS. Driver-written content is established from the
    SEALED INPUT MANIFEST (`nna8yz`, R5.1) and a collected submission from the ATTEMPT-KEYED COLLECTION
    RECEIPT (`cqx5v7`, R2.5). `ManifestSourcedClassificationTests` proves the lookup is the manifest by
    changing the MANIFEST and watching the classification follow, which a hardcoded path list could
    not do.
  * R5.6a is proven from the RENDERED SUMMARY, never from the event. A test asserting only that the
    event was written would pass while reproducing the measured failure exactly: run
    `run-20260901T042331Z-118022` preserved TWO lanes and mentioned it ZERO times in the summary a
    human reads.
  * EVERY behavioral test is PARAMETERIZED OVER BOTH DRIVERS (`DRIVERS`) rather than written twice,
    because orchestrator CID-3 makes a rule present in one driver only a DEFECT and two copied test
    functions are how such an omission survives review.
"""

from __future__ import annotations

import ast
import inspect
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from agent_workflows import agy_runipd, lane_containment, oc_runipd

LC = lane_containment

#: The two host drivers the retention rule must be wired into IDENTICALLY (orchestrator CID-3).
DRIVERS = (("oc", oc_runipd), ("agy", agy_runipd))


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return proc.stdout


class _Handle:
    """The minimal `worktree_lease.WorktreeHandle` surface the teardown gate reads."""

    def __init__(self, path: Path, branch: str = "aw/lane/ret001") -> None:
        self.path = path
        self.branch = branch
        self.lane_id = branch.rsplit("/", 1)[-1]
        self.base_commit = "0" * 40
        self.disposition = "created"


class LaneFixture:
    """A real git lane with a real ignore rule, a real manifest, and a real collection receipt.

    A REAL REPOSITORY RATHER THAN A FAKE PORCELAIN STRING, deliberately. The property under test is
    that the ENUMERATION sees ignored files, and a hand-written porcelain fixture would assert only
    that the parser handles a `!!` line the test itself wrote - it could not catch the flag being
    wrong, which is the actual hazard.
    """

    def __init__(self, root: Path) -> None:
        self.repo = root / "repo"
        self.lane = root / "lane"
        self.run_dir = root / "run"
        for path in (self.repo, self.lane, self.run_dir):
            path.mkdir(parents=True, exist_ok=True)
        _git(self.lane, "init", "-q", ".")
        _git(self.lane, "config", "user.email", "driver@example.invalid")
        _git(self.lane, "config", "user.name", "driver")
        # `.aw/state/` is ignored in the real repository, and the lane is a worktree of the same
        # commit, so the ignore rule applies inside the lane too. Reproduced here for the same reason.
        (self.lane / ".gitignore").write_text(".aw/state/\n*.log\n", encoding="utf-8")
        (self.lane / "tracked.txt").write_text("original\n", encoding="utf-8")
        _git(self.lane, "add", ".gitignore", "tracked.txt")
        _git(self.lane, "commit", "-qm", "base")
        self.item: dict[str, Any] = {
            "position": 3,
            "id6": "ret001",
            "setid": "lanectn",
            "status": "executed",
            "attempts": [{"number": 1}],
        }
        self.handle = _Handle(self.lane)

    # -- lane content ---------------------------------------------------------------------------
    def add_untracked(self, rel: str = "work/note.txt") -> Path:
        target = self.lane / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("unexplained\n", encoding="utf-8")
        return target

    def add_ignored(self, rel: str = "build/output.log") -> Path:
        target = self.lane / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ignored but real\n", encoding="utf-8")
        return target

    def dirty_tracked(self) -> Path:
        target = self.lane / "tracked.txt"
        target.write_text("edited by the worker\n", encoding="utf-8")
        return target

    # -- driver records -------------------------------------------------------------------------
    def materialize_inputs(self) -> LC.LaneInputManifest:
        """Write a driver input the SEALED MANIFEST accounts for (R5.1)."""
        plan = self.repo / "plan.ipd.md"
        plan.write_text("# plan\n", encoding="utf-8")
        return LC.materialize_lane_inputs(
            lane_root=self.lane, plan_path=plan, repo=self.repo
        )

    def submit(self) -> Path:
        """Write the worker's outcome submission inside the lane (the R2 shape)."""
        paths = LC.project_worker_paths(
            item=self.item,
            run_id="run-test",
            run_dir=self.run_dir,
            plan_path=self.repo / "plan.ipd.md",
            lane_root=self.lane,
        )
        assert paths.lane_outcome is not None
        paths.lane_outcome.parent.mkdir(parents=True, exist_ok=True)
        paths.lane_outcome.write_text(
            json.dumps({"disposition": "executed"}), encoding="utf-8"
        )
        return paths.lane_outcome

    def collect(self) -> dict[str, Any] | None:
        """Run the REAL collection so the receipt is the real artifact, not a fabricated one."""
        return LC.collect_lane_submissions(
            run_dir=self.run_dir,
            item=self.item,
            run_id="run-test",
            lane_root=self.lane,
            plan_path=self.repo / "plan.ipd.md",
        )

    def inventory(self, **kwargs: Any) -> LC.LaneInventory:
        return LC.inventory_lane(
            lane_root=self.lane, run_dir=self.run_dir, item=self.item, **kwargs
        )


class _FixtureCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = LaneFixture(Path(self._tmp.name))


class ClassificationTests(_FixtureCase):
    """R5.5 classification (criterion A15): what the inventory reports, per category."""

    def test_a_fully_accounted_lane_is_classified(self):
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        inv = self.fx.inventory()

        self.assertTrue(inv.readable, inv.failure)
        self.assertTrue(inv.classified, inv.reason)
        self.assertEqual(inv.unknown, ())
        self.assertEqual(inv.reason_codes, ())
        self.assertFalse(inv.uncollected_submission, inv.submission_detail)
        # The driver's own content was SEEN and classified discardable, not merely absent from the
        # unknown lists: an enumeration that missed it entirely would also produce an empty unknown set.
        self.assertTrue(inv.discardable, inv.as_dict())

    def test_an_unknown_untracked_file_is_reported_unknown(self):
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        self.fx.add_untracked()
        inv = self.fx.inventory()

        self.assertIn("work/note.txt", inv.unknown_untracked)
        self.assertFalse(inv.classified)
        self.assertIn(LC.RETENTION_UNKNOWN_UNTRACKED, inv.reason_codes)

    def test_an_unknown_IGNORED_file_is_reported_unknown(self):
        # THE CASE THIS REQUIREMENT EXISTS FOR (spec R5.5, plan F-1). Ignored content was previously
        # invisible to the enumeration and therefore destroyed silently.
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        self.fx.add_ignored()
        inv = self.fx.inventory()

        self.assertIn("build/output.log", inv.unknown_ignored)
        self.assertFalse(inv.classified)
        self.assertIn(LC.RETENTION_UNKNOWN_IGNORED, inv.reason_codes)

    def test_a_dirty_tracked_file_is_reported_unknown(self):
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        self.fx.dirty_tracked()
        inv = self.fx.inventory()

        self.assertIn("tracked.txt", inv.dirty_tracked)
        self.assertFalse(inv.classified)
        self.assertIn(LC.RETENTION_DIRTY_TRACKED, inv.reason_codes)

    def test_an_uncollected_submission_blocks_classification(self):
        # A submission written but NEVER collected: the lane holds the only copy.
        self.fx.materialize_inputs()
        self.fx.submit()
        inv = self.fx.inventory()

        self.assertTrue(inv.uncollected_submission)
        self.assertFalse(inv.classified)
        self.assertIn(LC.RETENTION_UNCOLLECTED_SUBMISSION, inv.reason_codes)
        assert inv.submission_detail is not None
        self.assertIn("receipt", inv.submission_detail)

    def test_the_reason_names_each_condition_that_held(self):
        # R5.6 forbids a generic message: the reason must name WHICH condition held.
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.add_untracked()
        self.fx.add_ignored()
        self.fx.dirty_tracked()
        inv = self.fx.inventory()

        self.assertEqual(
            set(inv.reason_codes),
            {
                LC.RETENTION_DIRTY_TRACKED,
                LC.RETENTION_UNKNOWN_UNTRACKED,
                LC.RETENTION_UNKNOWN_IGNORED,
                LC.RETENTION_UNCOLLECTED_SUBMISSION,
            },
        )
        for fragment in ("tracked.txt", "work/note.txt", "build/output.log"):
            self.assertIn(fragment, inv.reason)

    def test_the_reason_caps_the_named_paths_but_never_the_recorded_evidence(self):
        # The SENTENCE is truncated past the limit; the RECORD keeps every path. Truncating the
        # recorded evidence instead would be the dishonest choice.
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        count = LC.RETENTION_REASON_PATH_LIMIT + 5
        for index in range(count):
            self.fx.add_untracked(f"work/many/{index:03d}.txt")
        inv = self.fx.inventory()

        self.assertEqual(len(inv.unknown_untracked), count)
        self.assertEqual(len(inv.as_dict()["unknown_untracked"]), count)
        self.assertIn("and 5 more", inv.reason)
        self.assertIn(str(count), inv.reason)


class IgnoredEnumerationTests(_FixtureCase):
    """R5.5: prove the ENUMERATION sees ignored files, not merely that the parser can."""

    def test_the_status_args_carry_all_three_flags(self):
        self.assertIn("--porcelain", LC.LANE_INVENTORY_STATUS_ARGS)
        # `all` so a file nested in an untracked directory is reported individually.
        self.assertIn("--untracked-files=all", LC.LANE_INVENTORY_STATUS_ARGS)
        # `traditional` rather than `matching`: `matching` reports the ignored DIRECTORY, which is too
        # coarse to compare against a manifest entry inside that directory.
        self.assertIn("--ignored=traditional", LC.LANE_INVENTORY_STATUS_ARGS)

    def test_dropping_the_ignored_flag_makes_the_ignored_file_vanish(self):
        """SABOTAGE, targeted at the ignored half specifically (plan V-01).

        An enumeration that passes for untracked files while silently missing ignored ones is the exact
        defect this requirement exists to prevent, so the proof is that REMOVING the ignored flag
        changes the answer. Done by injecting a runner that strips the flag, which sabotages the
        BEHAVIOR without editing the product.
        """
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        self.fx.add_ignored()
        self.fx.add_untracked()

        from agent_workflows import runner_shared

        def runner_without_ignored(repo: Path, args: list[str]):
            stripped = [a for a in args if not a.startswith("--ignored")]
            return runner_shared._run_git(repo, stripped)

        crippled = self.fx.inventory(git_runner=runner_without_ignored)
        # The untracked file is STILL reported, which is why a suite checking only that case would
        # have passed while ignored content was being destroyed.
        self.assertIn("work/note.txt", crippled.unknown_untracked)
        self.assertEqual(
            crippled.unknown_ignored,
            (),
            "with the ignored flag stripped the ignored file is invisible; this is the sabotage",
        )

        restored = self.fx.inventory()
        self.assertIn("build/output.log", restored.unknown_ignored)

    def test_a_nested_ignored_file_is_reported_per_file_not_per_directory(self):
        # `--ignored=matching` would report `.aw/state/` and hide what is inside it, which would make
        # a manifest comparison impossible for anything under an ignored directory.
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        nested = self.fx.lane / ".aw/state/unexplained/deep.txt"
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.write_text("under an ignored prefix\n", encoding="utf-8")

        inv = self.fx.inventory()
        self.assertIn(".aw/state/unexplained/deep.txt", inv.unknown_ignored)


class ManifestSourcedClassificationTests(_FixtureCase):
    """R5.5/R6.1: driver-written content comes from the MANIFEST, never a hardcoded path list."""

    def test_the_manifest_entries_are_what_make_content_discardable(self):
        manifest = self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        entry = manifest.entries[0]

        accounted = LC.driver_written_lane_paths(self.fx.lane)
        self.assertIn(entry.path, accounted)
        inv = self.fx.inventory()
        self.assertIn(entry.path, inv.discardable)
        self.assertNotIn(entry.path, inv.unknown)

    def test_a_manifest_that_stops_listing_a_file_makes_it_unknown(self):
        """The lookup follows the MANIFEST: change the record, the classification changes.

        A hardcoded path list would keep classifying the file as driver-written after the manifest
        stopped claiming it, which is the drift spec R6.1 and plan F-4 forbid.
        """
        manifest = self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()
        entry = manifest.entries[0]
        self.assertIn(entry.path, self.fx.inventory().discardable)

        document = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        document["inputs"] = []
        manifest.manifest_path.chmod(
            0o644
        )  # the seal is an accident guard, not immutability
        manifest.manifest_path.write_text(json.dumps(document), encoding="utf-8")

        inv = self.fx.inventory()
        self.assertIn(
            entry.path,
            inv.unknown_ignored,
            "with the manifest no longer listing it, the file must be UNKNOWN",
        )

    def test_an_absent_manifest_accounts_for_nothing(self):
        # Fail-closed: with no record of what the driver wrote, nothing is discardable.
        self.assertEqual(LC.driver_written_lane_paths(self.fx.lane), set())

    def test_the_prefix_match_is_segment_aware(self):
        # `.aw/state/lane-inputs-scratch/x` must NOT be absorbed by the prefix `.aw/state/lane-inputs`.
        self.assertTrue(LC._is_within("a/b/c.txt", ["a/b"]))
        self.assertTrue(LC._is_within("a/b", ["a/b"]))
        self.assertFalse(LC._is_within("a/bc/d.txt", ["a/b"]))
        self.assertFalse(LC._is_within("a/b.txt", []))


class SubmissionRetentionTests(_FixtureCase):
    """R2.5 consumed by R5.5: the RECEIPT answers "was it collected?", never path presence."""

    def test_no_receipt_means_uncollected(self):
        self.fx.submit()
        result = LC.submission_retention(
            run_dir=self.fx.run_dir, item=self.fx.item, lane_root=self.fx.lane
        )
        self.assertTrue(result.uncollected)
        self.assertEqual(result.collected_paths, ())

    def test_a_complete_receipt_accounts_for_the_collected_sources(self):
        self.fx.submit()
        self.fx.collect()
        result = LC.submission_retention(
            run_dir=self.fx.run_dir, item=self.fx.item, lane_root=self.fx.lane
        )
        self.assertFalse(result.uncollected, result.detail)
        self.assertTrue(result.collected_paths)

    def test_an_in_progress_receipt_means_uncollected(self):
        self.fx.submit()
        self.fx.collect()
        path = LC.collection_receipt_path(self.fx.run_dir, self.fx.item, 1)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["status"] = LC.RECEIPT_IN_PROGRESS
        path.write_text(json.dumps(document), encoding="utf-8")

        result = LC.submission_retention(
            run_dir=self.fx.run_dir, item=self.fx.item, lane_root=self.fx.lane
        )
        self.assertTrue(result.uncollected)
        assert result.detail is not None
        self.assertIn(LC.RECEIPT_IN_PROGRESS, result.detail)

    def test_a_FAILED_collection_means_uncollected(self):
        # R2.5 requires a failure be recorded as failed rather than omitted, precisely so this case is
        # distinguishable from a lane that wrote nothing. Deleting output whose collection FAILED is
        # the failure mode inferring from path presence would produce.
        self.fx.submit()
        self.fx.collect()
        path = LC.collection_receipt_path(self.fx.run_dir, self.fx.item, 1)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["submissions"][0]["result"] = "failed"
        document["submissions"][0]["reason"] = "OSError: disk full"
        path.write_text(json.dumps(document), encoding="utf-8")

        result = LC.submission_retention(
            run_dir=self.fx.run_dir, item=self.fx.item, lane_root=self.fx.lane
        )
        self.assertTrue(result.uncollected)
        assert result.detail is not None
        self.assertIn("FAILED", result.detail)

    def test_a_receipt_is_attempt_keyed(self):
        # A retry must not read the previous attempt's outcome as its own.
        self.fx.submit()
        self.fx.collect()
        second = LC.submission_retention(
            run_dir=self.fx.run_dir,
            item=self.fx.item,
            lane_root=self.fx.lane,
            attempt=2,
        )
        self.assertTrue(second.uncollected)


class InventoryFailureTests(_FixtureCase):
    """R5.5: an inventory that CANNOT RUN must refuse, not proceed."""

    def test_a_failing_git_yields_an_unreadable_inventory(self):
        def broken(repo: Path, args: list[str]):
            return 128, "", "fatal: not a git repository"

        inv = self.fx.inventory(git_runner=broken)
        self.assertFalse(inv.readable)
        self.assertFalse(inv.classified)
        self.assertIn(LC.RETENTION_INVENTORY_FAILED, inv.reason_codes)
        self.assertIn("not a git repository", inv.reason)

    def test_a_raising_git_yields_an_unreadable_inventory(self):
        def exploding(repo: Path, args: list[str]):
            raise OSError("no such executable: git")

        inv = self.fx.inventory(git_runner=exploding)
        self.assertFalse(inv.readable)
        self.assertFalse(inv.classified)
        self.assertIn("no such executable", inv.reason)

    def test_unreadable_is_not_the_same_as_empty(self):
        # The specific confusion to prevent: an unreadable inventory has no unknown paths, so a check
        # written as "no unknowns -> tear down" would DESTROY the lane it knows nothing about.
        inv = self.fx.inventory(git_runner=lambda repo, args: (1, "", "boom"))
        self.assertEqual(inv.unknown, ())
        self.assertFalse(inv.classified)


class TeardownGateTests(_FixtureCase):
    """R5.5 refusal (criterion A15): only a fully classified lane may be torn down."""

    def _decide(self, **kwargs: Any) -> LC.LaneTeardownDecision:
        calls: list[tuple[Path, Any]] = []

        def fake_teardown(repo: Path, handle: Any) -> None:
            calls.append((repo, handle))
            # The real teardown force-removes the worktree AND deletes the branch; emulate the
            # destructive half so "the lane still exists" is a real observation.
            import shutil

            shutil.rmtree(handle.path)

        decision = LC.teardown_lane_if_classified(
            repo=self.fx.repo,
            handle=self.fx.handle,
            run_dir=self.fx.run_dir,
            item=self.fx.item,
            teardown=fake_teardown,
            **kwargs,
        )
        self._teardown_calls = calls
        return decision

    def test_a_fully_classified_clean_lane_IS_torn_down(self):
        # Proves the gate is not simply refusing always, which is what would make every other
        # assertion in this class vacuous.
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()

        decision = self._decide()
        self.assertTrue(decision.torn_down, decision.reason)
        self.assertEqual(len(self._teardown_calls), 1)
        self.assertFalse(self.fx.lane.exists())

    def test_each_unknown_condition_leaves_the_lane_on_disk(self):
        # The condition-maker is named rather than BOUND, because `setUp` below replaces `self.fx` and a
        # bound method captured here would add its content to the PREVIOUS lane - which is exactly how
        # this test first passed against a lane that no longer existed.
        cases = {
            LC.RETENTION_UNKNOWN_UNTRACKED: "add_untracked",
            LC.RETENTION_UNKNOWN_IGNORED: "add_ignored",
            LC.RETENTION_DIRTY_TRACKED: "dirty_tracked",
        }
        for code, maker in cases.items():
            with self.subTest(condition=code):
                self.setUp()  # a fresh lane per condition
                self.fx.materialize_inputs()
                self.fx.submit()
                self.fx.collect()
                getattr(self.fx, maker)()

                decision = self._decide()
                self.assertFalse(decision.torn_down)
                self.assertTrue(decision.preserved)
                self.assertEqual(self._teardown_calls, [])
                self.assertTrue(
                    self.fx.lane.is_dir(), "the lane directory MUST still exist"
                )
                self.assertIn(code, decision.reason_codes)

    def test_an_uncollected_submission_leaves_the_lane_on_disk(self):
        self.fx.materialize_inputs()
        self.fx.submit()  # written but never collected

        decision = self._decide()
        self.assertFalse(decision.torn_down)
        self.assertEqual(self._teardown_calls, [])
        self.assertTrue(self.fx.lane.is_dir())
        self.assertIn(LC.RETENTION_UNCOLLECTED_SUBMISSION, decision.reason_codes)

    def test_an_inventory_failure_preserves_rather_than_proceeds(self):
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()

        decision = self._decide(git_runner=lambda repo, args: (128, "", "fatal: boom"))
        self.assertFalse(decision.torn_down)
        self.assertEqual(self._teardown_calls, [])
        self.assertTrue(self.fx.lane.is_dir())
        self.assertIn(LC.RETENTION_INVENTORY_FAILED, decision.reason_codes)

    def test_a_teardown_that_was_authorized_but_FAILED_counts_as_preserved(self):
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.collect()

        def failing(repo: Path, handle: Any) -> None:
            raise RuntimeError("git worktree remove refused")

        decision = LC.teardown_lane_if_classified(
            repo=self.fx.repo,
            handle=self.fx.handle,
            run_dir=self.fx.run_dir,
            item=self.fx.item,
            teardown=failing,
        )
        self.assertFalse(decision.torn_down)
        self.assertTrue(decision.preserved)
        assert decision.error is not None
        self.assertIn("git worktree remove refused", decision.reason)
        self.assertTrue(self.fx.lane.is_dir())

    def test_an_unconditional_pass_classification_destroys_the_lane(self):
        """SABOTAGE of the central refusal (plan V-02), by breaking the PRODUCT behavior.

        Patches `inventory_lane` so it always reports a fully classified lane - the unconditional-pass
        version this plan exists to prevent - and shows the SAME gate call then DESTROYS a lane holding
        unexplained work. That is what proves the refusal assertions above pass because the refusal
        works, not for an unrelated reason.
        """
        from unittest import mock

        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.add_untracked()  # unexplained content: the real gate MUST refuse

        real = self._decide()
        self.assertFalse(real.torn_down, real.reason)
        self.assertTrue(self.fx.lane.is_dir())

        always_clean = LC.LaneInventory(lane_root=str(self.fx.lane), readable=True)
        self.assertTrue(always_clean.classified)  # the sabotaged verdict
        with mock.patch.object(LC, "inventory_lane", return_value=always_clean):
            sabotaged = self._decide()
        self.assertTrue(
            sabotaged.torn_down,
            "with classification forced to pass, the gate tears down a lane holding unexplained "
            "work; that is the behavior the real inventory refuses",
        )
        self.assertFalse(self.fx.lane.exists())


class PreservationRecordTests(_FixtureCase):
    """R5.6: the refusal is recorded on the EXISTING preservation event, naming the condition."""

    def _preserve(self) -> dict[str, Any]:
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.add_ignored()
        inventory = self.fx.inventory()
        return LC.record_lane_preserved(
            run_dir=self.fx.run_dir,
            item=self.fx.item,
            handle=self.fx.handle,
            reason=inventory.reason,
            reason_codes=inventory.reason_codes,
            detail=inventory.as_dict(),
        )

    def _events(self) -> list[dict[str, Any]]:
        path = self.fx.run_dir / "events.jsonl"
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_the_event_names_which_condition_held(self):
        self._preserve()
        events = self._events()
        self.assertEqual(len(events), 1, events)
        event = events[0]
        self.assertEqual(event["event"], LC.LANE_PRESERVED_EVENT)
        self.assertIn(LC.RETENTION_UNKNOWN_IGNORED, event["retention_reasons"])
        self.assertIn(LC.RETENTION_UNCOLLECTED_SUBMISSION, event["retention_reasons"])
        # And it carries the EVIDENCE, not merely a code: the paths behind the verdict.
        self.assertIn("build/output.log", event["unknown_ignored"])

    def test_the_event_is_not_generic(self):
        # ASSERT THE PROPERTY, NOT THE WORDING: the reason must name a specific condition, so a
        # reworded generic message ("lane preserved") still fails.
        self._preserve()
        reason = self._events()[0]["reason"]
        self.assertIn("IGNORED", reason)
        self.assertIn("build/output.log", reason)

    def test_it_EXTENDS_the_existing_event_rather_than_adding_a_second(self):
        """CID-2: one preservation event, one emitter.

        Structural, not a grep: assert (a) the event NAME has exactly one definition in the package,
        (b) neither driver constructs a `worktree-preserved` event inline any more, and (c) the
        preservation event literal appears in NO product module other than the shared home.
        """
        pkg = Path(inspect.getfile(LC)).parent
        literal = "worktree-preserved"
        self.assertEqual(LC.LANE_PRESERVED_EVENT, literal)

        holders: list[str] = []
        for path in sorted(pkg.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and node.value == literal:
                    holders.append(path.name)
                    break
        self.assertEqual(
            sorted(set(holders)),
            ["lane_containment.py"],
            "the preservation event literal must live ONLY in the shared home; a driver holding it "
            "means a second emission path exists (CID-2)",
        )

    def test_the_state_write_and_the_event_agree(self):
        event = self._preserve()
        self.assertEqual(self.fx.item["preserved_branch"], event["branch"])
        self.assertEqual(self.fx.item["preserved_reason"], event["reason"])
        self.assertEqual(
            self.fx.item["preserved_retention_reasons"], event["retention_reasons"]
        )

    def test_the_missing_input_path_records_state_WITHOUT_a_second_event(self):
        # The R3.2 preservation has its own dedicated event, so it records only durable state here;
        # emitting the shared event too would be the fork CID-2 forbids, while recording nothing would
        # leave the summary silent about a preserved lane (R5.6a).
        LC.record_preserved_lane_state(
            item=self.fx.item,
            handle=self.fx.handle,
            reason="a missing-input report was refused",
            reason_codes=("missing-input-refused",),
        )
        self.assertFalse((self.fx.run_dir / "events.jsonl").exists())
        self.assertEqual(
            self.fx.item["preserved_retention_reasons"], ["missing-input-refused"]
        )


class SummaryVisibilityTests(_FixtureCase):
    """R5.6a (criterion A15b): the preservation is visible WITHOUT reading the event log."""

    def _state(self) -> dict[str, Any]:
        self.fx.materialize_inputs()
        self.fx.submit()
        self.fx.add_ignored()
        inventory = self.fx.inventory()
        LC.record_lane_preserved(
            run_dir=self.fx.run_dir,
            item=self.fx.item,
            handle=self.fx.handle,
            reason=inventory.reason,
            reason_codes=inventory.reason_codes,
            detail=inventory.as_dict(),
        )
        return {
            "run_id": "run-test",
            "repo": str(self.fx.repo),
            "selectors": ["ret001"],
            "queue": [self.fx.item],
        }

    def test_each_driver_summary_names_the_lane_and_the_reason(self):
        state = self._state()
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                run_dir = self.fx.run_dir / label
                (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
                module.write_report(run_dir, state)
                report = (run_dir / "execution-report.md").read_text(encoding="utf-8")

                self.assertIn("Preserved lanes", report)
                self.assertIn(self.fx.handle.branch, report)
                self.assertIn("build/output.log", report)
                self.assertIn(LC.RETENTION_UNKNOWN_IGNORED, report)

    def test_a_run_with_no_preserved_lane_renders_nothing_extra(self):
        # So an unaffected run's report is unchanged: the section is emitted only when it has content.
        self.assertEqual(LC.format_preserved_lanes({"queue": [{"id6": "x"}]}), [])
        self.assertEqual(LC.format_preserved_lanes({}), [])

    def test_an_event_only_record_would_NOT_satisfy_this(self):
        """The measured failure, asserted as a property (plan V-03, spec A15b).

        Run `run-20260901T042331Z-118022` preserved TWO lanes and mentioned it ZERO times in the
        summary. Reproduce that shape - an event written, no durable state - and show the summary is
        silent, which is why an event-only assertion would pass while the defect persisted.
        """
        state = self._state()
        for item in state["queue"]:
            item.pop("preserved_worktree")
        run_dir = self.fx.run_dir / "eventonly"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        oc_runipd.write_report(run_dir, state)
        report = (run_dir / "execution-report.md").read_text(encoding="utf-8")

        self.assertTrue((self.fx.run_dir / "events.jsonl").is_file())
        self.assertNotIn("Preserved lanes", report)

    def test_a_renderer_that_returns_nothing_makes_every_driver_report_silent(self):
        """SABOTAGE of the R5.6a half (plan V-03), by breaking the PRODUCT behavior.

        Patches the shared renderer to contribute nothing - the state before this plan - and shows BOTH
        drivers' reports fall silent about a preserved lane. So the passing assertions above depend on
        the renderer actually being called by each driver, not on the section text existing somewhere.
        """
        from unittest import mock

        state = self._state()
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                run_dir = self.fx.run_dir / f"sabotage-{label}"
                (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
                with mock.patch.object(LC, "format_preserved_lanes", return_value=[]):
                    module.write_report(run_dir, state)
                silent = (run_dir / "execution-report.md").read_text(encoding="utf-8")
                self.assertNotIn("Preserved lanes", silent)
                self.assertNotIn("build/output.log", silent)

                module.write_report(run_dir, state)  # restored
                restored = (run_dir / "execution-report.md").read_text(encoding="utf-8")
                self.assertIn("Preserved lanes", restored)
                self.assertIn("build/output.log", restored)


class TwinParityTests(unittest.TestCase):
    """CID-2/CID-3: ONE definition of the retention rule, wired into BOTH drivers."""

    #: Every symbol this plan introduced, by the name that IS its single definition.
    OWNED = (
        "LaneInventory",
        "LaneTeardownDecision",
        "SubmissionRetention",
        "inventory_lane",
        "teardown_lane_if_classified",
        "submission_retention",
        "driver_written_lane_paths",
        "record_lane_preserved",
        "record_preserved_lane_state",
        "format_preserved_lanes",
        "parse_porcelain_entries",
        "LANE_INVENTORY_STATUS_ARGS",
        "LANE_PRESERVED_EVENT",
    )

    def _definition_sites(self, name: str) -> list[str]:
        pkg = Path(inspect.getfile(LC)).parent
        sites: list[str] = []
        for path in sorted(pkg.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                found = False
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    found = node.name == name
                elif isinstance(node, ast.Assign):
                    found = any(
                        isinstance(t, ast.Name) and t.id == name for t in node.targets
                    )
                elif isinstance(node, ast.AnnAssign):
                    found = isinstance(node.target, ast.Name) and node.target.id == name
                if found:
                    sites.append(f"{path.name}:{node.lineno}")
        return sites

    def test_each_retention_symbol_has_exactly_one_definition_in_the_shared_home(self):
        for name in self.OWNED:
            with self.subTest(symbol=name):
                sites = self._definition_sites(name)
                self.assertEqual(
                    len(sites), 1, f"{name} is defined at {sites}, not once"
                )
                self.assertTrue(
                    sites[0].startswith("lane_containment.py:"),
                    f"{name} must live in the ONE host-neutral home, not {sites[0]} (spec R2.6)",
                )

    def test_neither_driver_defines_a_private_copy(self):
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                tree = ast.parse(
                    Path(inspect.getfile(module)).read_text(encoding="utf-8")
                )
                defined = {
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                }
                self.assertEqual(defined & set(self.OWNED), set())

    def test_both_drivers_route_teardown_through_the_shared_gate(self):
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                source = inspect.getsource(module)
                self.assertIn(
                    "lane_containment.teardown_lane_if_classified(",
                    source,
                    f"{label} must consult the retention gate before destroying a lane",
                )
                self.assertIn(
                    "lane_containment.record_lane_preserved(",
                    source,
                    f"{label} must record a refusal through the one shared emitter",
                )
                self.assertIn(
                    "lane_containment.format_preserved_lanes(",
                    source,
                    f"{label} must name preserved lanes in the summary (R5.6a)",
                )

    def test_no_driver_calls_the_destructive_teardown_directly(self):
        """STRUCTURE, NOT GREP: a direct call would bypass the inventory entirely.

        Walks each driver's AST for a call to `teardown_isolation_worktree`, which force-removes the
        worktree and deletes the branch. After this plan the only route to it is the shared gate.
        """
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                tree = ast.parse(
                    Path(inspect.getfile(module)).read_text(encoding="utf-8")
                )
                direct = [
                    node.lineno
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and (
                        getattr(node.func, "id", None) == "teardown_isolation_worktree"
                        or getattr(node.func, "attr", None)
                        == "teardown_isolation_worktree"
                    )
                ]
                self.assertEqual(
                    direct,
                    [],
                    f"{label} calls the destructive teardown directly at lines {direct}; it must go "
                    "through `teardown_lane_if_classified` so the inventory runs first",
                )

    def test_the_porcelain_format_has_one_decoder(self):
        """`parse_porcelain_paths` is a PROJECTION, so the format is decoded in exactly one place.

        STRUCTURE, NOT GREP, and specifically not a substring search over the whole source: a docstring
        legitimately mentions the format it delegates, and pinning on that made this test fail for the
        prose rather than for a second parser. So walk the function BODY's AST: the projection must
        contain exactly one call, to `parse_porcelain_entries`, and no line-splitting or slicing of its
        own.
        """
        tree = ast.parse(inspect.getsource(LC.parse_porcelain_paths).lstrip())
        function = tree.body[0]
        assert isinstance(function, ast.FunctionDef)
        # The BODY only: a `set[str]` return annotation is itself a Subscript, so walking the whole
        # definition would flag the signature and say nothing about the format.
        body_nodes = [n for stmt in function.body for n in ast.walk(stmt)]
        called = {
            (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else getattr(node.func, "id", "")
            )
            for node in body_nodes
            if isinstance(node, ast.Call)
        }
        self.assertEqual(called, {"parse_porcelain_entries"})
        self.assertEqual(
            [n for n in body_nodes if isinstance(n, ast.Subscript)],
            [],
            "the projection must not slice a porcelain line; that is the decoder's job",
        )
        # And the decoder itself is the one that does hold the format.
        decoder = inspect.getsource(LC.parse_porcelain_entries)
        for token in ("splitlines", " -> "):
            self.assertIn(token, decoder)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
