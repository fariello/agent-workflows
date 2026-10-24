"""Behavioral tests for runner_shared recovery routing and spec-impact keys.

Restores test coverage for unguarded runner_shared keys recorded in backlog item l2zsa9
and plan wfm5iv (spec_impacts_for_queue and route_recovery_turn), whose behavioral tests
were deleted at 19313eed^ (specifically from tests/test_spec_visibility.py and
tests/test_resumedupe.py).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import oc_runipd as OC
from agent_workflows import runner_shared
from agent_workflows import worktree_lease as WL

pytestmark = pytest.mark.core

PLAN = """\
# IPD: demo

- Date: 2026-09-07
- Kind: child
- Scope-Paths: {scope}
- Status: approved
- Set: demo
- Order: 1
- Id: {id6}
"""


def _plan(root: Path, id6: str, scope: str) -> Path:
    p = root / f"20260907-demo-01-{id6}-demo.ipd.md"
    p.write_text(PLAN.format(scope=scope, id6=id6), encoding="utf-8")
    return p


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


def commit_in_lane(path: Path, filename: str, subject: str, body: str = "") -> str:
    (path / filename).write_text("work\n")
    git(path, "add", filename)
    args = ["commit", "-q", "-m", subject]
    if body:
        args.extend(["-m", body])
    git(path, *args)
    return out(path, "rev-parse", "HEAD")


# The subject of the real `zhr6mc` duplicate pair, used verbatim so the fixture is recognizably the
# measured shape rather than a generic one.
ZHR6MC_SUBJECT = (
    "feat(runner): close a backlog item when the run executes its last carrier"
)


class ResumeRoutingBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def state(self, repo: Path) -> dict:
        return {"repo": str(repo), "run_id": "run-fixture", "queue": []}

    def item_for(self, lane_handle, **extra) -> dict:
        """A durable item record shaped exactly as the drivers write one at allocation."""
        item = {
            "id6": "zhr6mc",
            "position": 1,
            "setid": "resumedupe",
            "status": "running",
            "attempts": [
                {
                    "number": 1,
                    "worktree_lane_id": lane_handle.lane_id,
                    "worktree_base": lane_handle.base_commit,
                    "worktree_branch": lane_handle.branch,
                    "worktree": str(lane_handle.path),
                }
            ],
        }
        item.update(extra)
        return item

    def resumed_shape(self, repo: Path, lane_id: str = "zhr6mc"):
        """THE REAL SHAPE, built with the REAL allocator rather than a hand-made state dict.

        Returns (prior_handle, current_handle, item). The second `allocate_worktree` is what makes
        this the genuine resume shape: allocation NEVER reuses a lane holding work, so the resumed
        turn gets a fresh attempt-scoped lane at zero commits while the work stays on the displaced
        one. A hand-built dict would assume that away and the inertness guard would prove nothing.
        """
        prior = WL.allocate_worktree(repo, lane_id)
        commit_in_lane(prior.path, "carrier.py", ZHR6MC_SUBJECT)
        commit_in_lane(prior.path, "test_carrier.py", "test: cover the carrier close")
        item = self.item_for(prior)
        current = WL.allocate_worktree(repo, lane_id)
        return prior, current, item


class TestSpecImpactsForQueue:
    """Collecting declared spec edits across a queue of plan files on disk.

    ONE table replaces four tests. Each built a queue of item dicts, called `spec_impacts_for_queue`,
    and asserted the impact list; they differed in the QUEUE SHAPE (how many items, how each item's
    path was spelled, whether the file existed, whether a path was present at all), which is a
    column.

    Why the table beats the four: this stage adds exactly two behaviors on top of the extractor
    (resolve a repo-relative path, and skip an item that cannot be read) and must otherwise pass the
    extractor's answer through untouched. Both skip rows are ADVISORY-SURFACE guarantees - a run must
    never fail to start because an announcement could not be built - so they belong beside the
    collecting rows that show the surface still works when nothing is wrong. Read together they say
    the stage is fail-soft rather than silent.

    THE MIXED-QUEUE ROW IS THE IMPORTANT ONE: an item declaring only code must be ABSENT from the
    output rather than present with an empty `specs` list, because the formatter counts plans from
    this list and an empty entry would announce a plan that changes no spec.
    """

    #: (case, the queue as a list of `(id6, how to spell the path, scope value or None to write no
    #: file)` tuples, the EXACT expected impact list built with `{id6, setid, specs}`, why this row
    #: exists)
    QUEUES = (
        (
            "two queued plans, only one of which touches a spec",
            (
                ("bbb111", "absolute", "x/one.spec.md, agent_workflows/cli.py"),
                ("bbb222", "absolute", "agent_workflows/only_code.py"),
            ),
            [{"id6": "bbb111", "setid": "demo", "specs": ["x/one.spec.md"]}],
            (
                "THE CANONICAL CASE and the row that pins the output SHAPE: the code-only plan must be "
                "ABSENT from the list, not present with an empty `specs`. The formatter counts plans from "
                "this list, so an empty entry would announce that a plan changes a spec when it does not"
            ),
        ),
        (
            "a queue item whose path is repo-RELATIVE",
            (("ccc111", "relative", "x/one.spec.md"),),
            [{"id6": "ccc111", "setid": "demo", "specs": ["x/one.spec.md"]}],
            (
                "QUEUE ITEMS ARRIVE WITH EITHER SPELLING depending on how the queue was built, and a "
                "relative path must be resolved against the repo root rather than the process cwd. "
                "Unresolved, it would read as unreadable and be silently SKIPPED by the row below, so "
                "this row is what stops the fail-soft behavior from swallowing a real spec edit"
            ),
        ),
        (
            "a queue item naming a plan file that does not exist",
            (("ddd111", "missing", None),),
            [],
            (
                "FAIL-SOFT BY DESIGN: this is an advisory surface, so an unreadable plan is skipped and "
                "the run still starts. Refusing to begin a run because an announcement could not be built "
                "would be a worse failure than a missing line of output"
            ),
        ),
        (
            "a queue item with no path key at all",
            (("eee111", "nokey", None),),
            [],
            (
                "the other malformed-item shape, from a queue entry built before its path was known. It "
                "must be skipped by the same route rather than raising a KeyError inside pre-run output"
            ),
        ),
    )

    def test_impacts_are_collected_across_the_queue_and_bad_items_are_skipped(
        self, tmp_path: Path
    ) -> None:
        wrong = []
        collecting_rows_broken = 0
        for case, items, expected, why in self.QUEUES:
            queue = []
            for id6, spelling, scope in items:
                if scope is not None:
                    written = _plan(tmp_path, id6, scope)
                if spelling == "absolute":
                    entry = {"id6": id6, "setid": "demo", "path": str(written)}
                elif spelling == "relative":
                    entry = {"id6": id6, "setid": "demo", "path": written.name}
                elif spelling == "missing":
                    entry = {
                        "id6": id6,
                        "setid": "demo",
                        "path": "does/not/exist.ipd.md",
                    }
                else:
                    entry = {"id6": id6, "setid": "demo"}
                queue.append(entry)
            got = runner_shared.spec_impacts_for_queue(tmp_path, queue)
            if got != expected:
                if expected:
                    collecting_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - queue: {queue!r}\n"
                    f"    - expected {expected!r}\n"
                    f"    - got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        extra = ""
        if collecting_rows_broken:
            extra = (
                f" {collecting_rows_broken} COLLECTING row(s) are among the failures, and while any "
                "of those is broken the two SKIP rows here are vacuous: a function returning an empty "
                "list for every queue satisfies both of them while announcing nothing, ever."
            )
        assert not wrong, (
            f"`spec_impacts_for_queue` mishandled {len(wrong)} of {len(self.QUEUES)} queue "
            f"shapes.{extra} This stage adds exactly two behaviors over the extractor (resolve a "
            "repo-relative path; skip an unreadable item), so read the grouping: the relative-path "
            "row failing alone means resolution now happens against the process cwd, which makes real "
            "plans read as unreadable and be SILENTLY SKIPPED by the fail-soft path; a skip row "
            "failing means a malformed queue entry can now stop a run from starting, which is a worse "
            "failure than a missing line of output. FIX: an item declaring no spec must be ABSENT "
            "from this list rather than present with an empty `specs`, because the formatter counts "
            "plans from it.\n" + "\n".join(wrong)
        )


class TestDurableRecording(ResumeRoutingBase):
    """E-05: the decision and its inputs are readable after the fact, from state alone."""

    def test_the_routing_decision_and_its_inputs_are_recorded(self):
        repo = fixture_repo(self.tmp)
        prior, _current, item = self.resumed_shape(repo)
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}

        OC.route_recovery_turn(run_dir, state, item, True)
        record = item["recovery_routing"]
        self.assertEqual(record["disposition"], OC.DISPOSITION_VERIFY_AND_CONTINUE)
        self.assertEqual(record["dispatched_as"], OC.DISPOSITION_VERIFY_AND_CONTINUE)
        # The INSPECTED LANE ID is the field that tells a reader which lane decided it.
        self.assertEqual(record["inspected_lane_id"], prior.lane_id)
        self.assertEqual(record["inspected_branch"], prior.branch)
        self.assertEqual(record["commits_ahead"], 2)
        self.assertFalse(record["snapshot_only"])
        self.assertEqual(len(record["real_commits"]), 2)
        self.assertTrue(record["reason"])

        events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("recovery-routed", events)
        self.assertIn(prior.lane_id, events)

    def test_a_reexecuted_run_is_distinguishable_from_a_verify_run_in_state_alone(self):
        repo = fixture_repo(self.tmp)
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

        _prior, _current, verify_item = self.resumed_shape(repo)
        empty = WL.allocate_worktree(repo, "otheritem")
        fresh_item = self.item_for(empty)
        fresh_item["id6"] = "otherid"
        state = {
            "repo": str(repo),
            "run_id": "run-fixture",
            "queue": [verify_item, fresh_item],
        }

        OC.route_recovery_turn(run_dir, state, verify_item, True)
        OC.route_recovery_turn(run_dir, state, fresh_item, True)
        self.assertEqual(
            verify_item["recovery_routing"]["dispatched_as"],
            OC.DISPOSITION_VERIFY_AND_CONTINUE,
        )
        self.assertEqual(
            fresh_item["recovery_routing"]["dispatched_as"],
            OC.DISPOSITION_FRESH_EXECUTION,
        )
