"""dirtygates-03 (`9iq461`): a successful item's backlog close happens IN THE LANE, not in main.

THE DEFECT THIS PINS, and it is measured rather than reasoned. `process_backlog_close` used to run
AFTER `integrate_lane_branch` and AFTER the lane teardown, operating on MAIN. So a successful item's
own bookkeeping WROTE INTO THE SHARED CHECKOUT while the run was still going, and when that write
landed only half the move, the shared tree was left dirty and a whole-tree gate then refused every
remaining item. Across three consecutive runs on 2026-09-13 that cost 27 of 42, 23 of 41 and 18 of 43
queue items, every refusal naming ONE uncommitted backlog markdown file
(`run-20260913T031350Z-1732436`, `run-20260913T031148Z-1722898`, `run-20260913T031521Z-1774617`).

THE HARM IS CROSS-ITEM, WHICH IS WHY THE CENTRAL ASSERTION HERE IS ABOUT MAIN'S CLEANLINESS AFTER
ITEM 1 AND ABOUT ITEMS 2 AND 3 STILL RUNNING. A per-item test cannot see this class of defect: item 1
itself succeeded in every one of those runs.

WHAT IS ASSERTED HERE:
  * the WRITE happens in the lane and rides the merge: main's `git status --porcelain` is EMPTY across
    a closing item, the item's move appears in the merge's `--name-status`, and NO separate close
    commit exists on main (V-01, V-02);
  * a FAILED integration leaves the item unclosed and still `graduated`, which is the property the
    maintainer asked for explicitly ("the move lands if and only if the merge lands");
  * the ELIGIBILITY DECISION is still taken against MAIN (OQ-01), proved on a fixture where the two
    views DIFFER, including the RELEASE-GATE case F-10 identified as the real hazard: an item carrying
    `Blocks-Release` whose only candidate carrier is this plan's own file must reach the same verdict
    it would reach against main, because the lane view is the PERMISSIVE one;
  * a MULTI-CARRIER item with an unexecuted sibling is not closed, built from a THREE-carrier shape
    because F-12 measured the real tail at 9/6/5/4/4/4 rather than pairs;
  * the MANDATORY POSITIVE CASE (F-7): an eligible item actually REACHING `done` through the merge,
    with a non-empty earned set, because every negative assertion above is equally satisfied by a
    close path that refuses unconditionally;
  * the NON-ISOLATED path unchanged: its close still moves AND still commits via
    `commit_backlog_close`;
  * both hosts, by object identity plus a call-site assertion.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


def _effective_execute_item_source(mod) -> str:
    src = inspect.getsource(mod.execute_item)
    if "execute_item_core" in src:
        return inspect.getsource(runner_shared.execute_item_core)
    return src


_PLAN = """\
# IPD: Demo {id6}

- Date: 2026-09-13
- Kind: child
- Concern: demo concern.
- Scope: demo scope.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
- Set: demo
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
{from_backlog}
## Workflow history

- 2026-09-13 approved (aw set): status set to approved
- 2026-09-13 draft (test): created.

## Goal

Demo goal sentence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: demo

- [x] E-01 Create the demo file.
  - Depends on: none
  - Expected outcome: the demo file exists.
  - Execution state: performed

## Project conventions discovered (Step 0)

- demo convention.

## Findings

demo findings.

## Proposed changes (ordered, validatable)

1. src/demo.txt: create it.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Manual check that the demo file exists.

## Spec / documentation sync

N/A: demo only.

## Open questions

### OQ-01: none?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass.

- [x] V-01 validates E-01
  - Required evidence: the demo file present.
  - Observed evidence: the demo file present.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit path-scoped; do not push.
"""


def _item_text(id6: str, *, status: str = "graduated", blocks_release: str = "") -> str:
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        "- Set: demo",
        "- Priority: medium",
        "- Kind: feature",
        "- Summary: a demo item",
    ]
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += ["", "## Workflow history", f"- 2026-09-13 {status} (test): created.", ""]
    return "\n".join(lines)


def _git(repo: Path, *args: str, check: bool = True) -> str:
    res = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if check and res.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {res.stderr}")
    return res.stdout


class _Fixture:
    """A git repo holding N approved plans, each linked to a backlog item, plus the ignore set a
    production install carries (run state, worktrees and receipts are gitignored)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "test@example.invalid")
        _git(root, "config", "user.name", "Test")
        # Match a production install's ignore set. `.aw/records/history.jsonl` and the regenerated
        # `INDEX.*` files matter here specifically: the shared setter appends to the history sidecar,
        # and if it is TRACKED the lane teardown gate correctly refuses (an unknown untracked file), so
        # an unignored fixture would measure the fixture rather than the code under test.
        (root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n"
            ".aw/records/history.jsonl\n.aw/records/plans/INDEX.json\n"
            ".aw/records/plans/INDEX.md\n",
            encoding="utf-8",
        )
        for rel in (
            ".aw/records/plans/pending",
            ".aw/records/plans/executed",
            ".aw/records/backlog/graduated",
            ".aw/records/backlog/done",
            ".aw/records/specs",
        ):
            (root / rel).mkdir(parents=True, exist_ok=True)
        # `git` will not track an empty directory, and the close's own porcelain scan needs the
        # backlog root to EXIST, so seed a keep file in each.
        for rel in (".aw/records/plans/executed", ".aw/records/backlog/done"):
            (root / rel / ".gitkeep").write_text("", encoding="utf-8")

    def add_plan(
        self, id6: str, *, order: int = 1, from_backlog: str | None = None
    ) -> Path:
        path = (
            self.root
            / ".aw/records/plans/pending"
            / f"20260913-demo-{order:02d}-{id6}-demo.ipd.md"
        )
        fb = f"- From-Backlog: {from_backlog}\n" if from_backlog else ""
        path.write_text(
            _PLAN.format(id6=id6, order=order, from_backlog=fb), encoding="utf-8"
        )
        return path

    def add_item(self, id6: str, **kw) -> Path:
        status = kw.get("status", "graduated")
        path = (
            self.root
            / ".aw/records/backlog"
            / status
            / f"20260913-demo-01-{id6}-demo-item.backlog.md"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_item_text(id6, **kw), encoding="utf-8")
        return path

    def commit(self, message: str = "fixture") -> None:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", message)

    def item_status(self, id6: str) -> str | None:
        for status in ("open", "graduated", "blocked", "parked", "done"):
            d = self.root / ".aw/records/backlog" / status
            if d.is_dir():
                for f in d.glob("*.md"):
                    if f"-{id6}-" in f.name:
                        return status
        return None

    def main_porcelain(self) -> str:
        return _git(self.root, "status", "--porcelain", "-uall").strip()


def _state(repo: Path, items: list[dict], *, isolate: bool = True) -> dict:
    return {
        "run_id": "run-test",
        "created_at": "2026-09-13T00:00:00+00:00",
        "updated_at": "2026-09-13T00:00:00+00:00",
        "selectors": ["demo"],
        "repo": str(repo),
        "queue": items,
        "set_sessions": {},
        "session_id": None,
        "options": {
            "opencode": "/bin/true",
            "model": "opus",
            "self_finalize": True,
            "isolate_worktree": isolate,
            # `no_audit: False` exercises the verify -> finalize -> integrate path, exactly as
            # `tests/test_oc_runipd.py::WorktreeIsolationTests` does. With validation OFF the shared
            # `integration_is_earned` predicate requires a DRIVER-RUN SUITE result instead, which this
            # fixture does not produce, so every item would stop at `substantially-complete` and the
            # finalize branch under test would never run.
            "no_audit": False,
        },
    }


def _queue_item(repo: Path, plan: Path, id6: str, position: int, backlog: str) -> dict:
    return {
        "position": position,
        "id6": id6,
        "setid": "demo",
        "status": "queued",
        "configured_file": str(plan.relative_to(repo)),
        "action": "execute",
        "from_backlog": backlog,
    }


def _mk_run_dir(repo: Path) -> Path:
    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    return run_dir


def _fake_agent(run_dir: Path, *, observe: dict | None = None):
    """A `run_opencode` stand-in that commits one in-scope file INSIDE the lane and reports executed.

    Optionally records MAIN's porcelain as observed DURING the turn, which is the window the original
    defect polluted.
    """

    def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
        work_dir = kwargs.get("work_dir")
        if kwargs.get("fresh_session"):
            # The VERIFIER turn: record a CONFORMING verdict, which is what makes
            # `integration_is_earned` return earned with validation ON.
            (
                run_dir
                / "outcomes"
                / f"{item['position']:02d}-{item['id6']}-verification.json"
            ).write_text(
                json.dumps(
                    {
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m unittest tests.test_from_backlog -v"],
                    }
                ),
                encoding="utf-8",
            )
            return 0, "vses", str(run_dir / "vlog"), ["oc"]
        tree = Path(work_dir) if work_dir else Path(state["repo"])
        (tree / "src").mkdir(parents=True, exist_ok=True)
        (tree / "src" / f"{item['id6']}.txt").write_text("demo\n", encoding="utf-8")
        _git(tree, "add", f"src/{item['id6']}.txt")
        _git(tree, "commit", "-qm", f"demo({item['id6']}): create the file")
        if observe is not None:
            observe.setdefault("during", {})[item["id6"]] = _git(
                Path(state["repo"]), "status", "--porcelain", "-uall"
            ).strip()
        (
            run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
        ).write_text(
            json.dumps(
                {
                    "disposition": "executed",
                    "pushed": False,
                    "defect_report": {"state": "none-found", "findings": []},
                }
            ),
            encoding="utf-8",
        )
        return 0, "ses1", str(run_dir / "log"), ["oc"]

    return fake_run


# ======================================================================================
# E-01 / E-02 / V-01 / V-02: the write happens in the lane and rides the merge
# ======================================================================================


class TheCloseHappensInTheLane(unittest.TestCase):
    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_main_stays_clean_and_the_move_rides_the_merge(self):
        """V-01/V-02: main's porcelain EMPTY across the item, the move INSIDE the merge, and NO
        separate close commit on main."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            before_head = _git(fx.root, "rev-parse", "HEAD").strip()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])
            observe: dict = {}

            with mock.patch.object(
                oc_runipd, "run_opencode", _fake_agent(run_dir, observe=observe)
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed", item)
            record = item.get("backlog_close") or {}
            self.assertTrue(record.get("closed"), record)
            # THE WRITE WAS IN THE LANE.
            self.assertEqual(record.get("wrote_in"), "lane", record)
            self.assertIsNotNone(
                record.get("commit"),
                "the lane-side move must be COMMITTED, else it is not in the merge and the lane "
                "cannot be torn down",
            )
            # MAIN WAS CLEAN DURING the turn and is clean AFTER it.
            self.assertEqual(observe["during"]["aaaaaa"], "")
            self.assertEqual(
                fx.main_porcelain(),
                "",
                "MAIN must be clean after an item that closed a backlog item",
            )
            # The item really moved.
            self.assertEqual(fx.item_status("bbbbbb"), "done")
            # THE MOVE IS IN THE MERGED RANGE, and its rename is visible.
            name_status = _git(fx.root, "diff", "--name-status", f"{before_head}..HEAD")
            self.assertIn("bbbbbb", name_status, name_status)
            self.assertIn(".aw/records/backlog/done/", name_status, name_status)
            # V-02: NO SEPARATE CLOSE COMMIT WAS MADE *ON MAIN*. The distinction is exact and is the
            # whole point of E-02: the close commit DOES reach main (it must, or the move would not be
            # in the merge), but it arrives as a LANE commit carried by the merge rather than as a
            # commit the driver created in the shared checkout. So the test is not "no such commit
            # exists" -- it is that the commit is REACHABLE FROM THE LANE BRANCH's range, i.e. it was
            # authored in the lane.
            close_commits = [
                line
                for line in _git(
                    fx.root, "log", "--format=%H %s", f"{before_head}..HEAD"
                ).splitlines()
                if "closed by aw oc run" in line
            ]
            self.assertEqual(
                len(close_commits),
                1,
                f"exactly one close commit must have arrived via the merge; saw {close_commits}",
            )
            close_sha = close_commits[0].split()[0]
            # Its PARENT chain starts from the lane's base, proving it was committed on the lane
            # branch (had the driver committed it in main after the merge, it would be main's tip and
            # its parent would be the merge result rather than the finalize commit).
            parent_subject = _git(
                fx.root, "log", "--format=%s", "-n", "1", f"{close_sha}^"
            ).strip()
            self.assertIn(
                "finalize",
                parent_subject,
                f"the close must sit directly on the lane's finalize commit, proving it was "
                f"authored in the lane; its parent was {parent_subject!r}",
            )

    def test_a_failed_integration_leaves_the_item_unclosed_and_graduated(self):
        """The maintainer's explicit property: the move lands IF AND ONLY IF the merge lands."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])

            with (
                mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)),
                mock.patch.object(
                    oc_runipd,
                    "integrate_lane_branch",
                    lambda *a, **k: (
                        False,
                        "induced integration failure",
                        "merge-refused",
                    ),
                ),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertNotEqual(item["status"], "executed", item)
            # MAIN never saw the close: the item is still graduated THERE, and main is clean.
            self.assertEqual(
                fx.item_status("bbbbbb"),
                "graduated",
                "a failed merge must leave the item unclosed in main",
            )
            self.assertEqual(fx.main_porcelain(), "")
            # The lane is PRESERVED, so nothing was lost; the close is on its branch, unmerged.
            self.assertTrue(
                item.get("preserved_branch"),
                "the verified lane must be preserved for a later attempt",
            )


# ======================================================================================
# E-03 / V-03: the DECISION is still main's, proved where the two views DIFFER
# ======================================================================================


class EligibilityIsDecidedInMain(unittest.TestCase):
    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_a_multi_carrier_item_with_an_unexecuted_sibling_is_not_closed(self):
        """OQ-01's whole point, on a THREE-carrier shape (F-12 measured the tail at 9/6/5/4/4/4, so a
        pair is the easiest case rather than a representative one)."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", order=1, from_backlog="bbbbbb")
            # Two SIBLING carriers, both still pending. Neither is this run's item.
            fx.add_plan("cccccc", order=2, from_backlog="bbbbbb")
            fx.add_plan("dddddd", order=3, from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])

            with mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed", item)
            record = item.get("backlog_close") or {}
            self.assertFalse(
                record.get("closed"),
                "an item whose SIBLING carriers have not executed must NOT close",
            )
            self.assertIn("not executed", record.get("reason", ""))
            # Both siblings must be NAMED in the reason, so the operator can act on it (E-04).
            self.assertIn("cccccc", record.get("reason", ""))
            self.assertIn("dddddd", record.get("reason", ""))
            self.assertEqual(fx.item_status("bbbbbb"), "graduated")

    def test_the_eligible_single_carrier_item_DOES_close_through_the_merge(self):
        """THE MANDATORY POSITIVE CASE (F-7). Every negative assertion in this file is equally
        satisfied by a close path that refuses UNCONDITIONALLY, so without this the change is
        indistinguishable from a silently disabled one."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            before_head = _git(fx.root, "rev-parse", "HEAD").strip()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])

            with mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            record = item.get("backlog_close") or {}
            self.assertTrue(record.get("closed"), record)
            self.assertEqual(fx.item_status("bbbbbb"), "done")
            # THE EARNED SET HAD REAL INPUT. An empty earned set also produces refusals, so the
            # non-emptiness is the discriminator between "correct" and "gate starved of input".
            earned = item.get("earned_paths") or []
            self.assertTrue(earned, "the earned set must be NON-EMPTY for a real close")
            self.assertTrue(
                any("executed/" in p for p in earned),
                f"the earned set must contain the finalized plan path; saw {earned}",
            )
            # And the item's new path is inside the merged range.
            name_status = _git(fx.root, "diff", "--name-status", f"{before_head}..HEAD")
            self.assertIn(".aw/records/backlog/done/", name_status, name_status)

    def test_the_earned_gate_still_refuses_a_close_this_run_did_not_earn(self):
        """E-03: the `earned_paths` gate must survive the move. An already-executed carrier that this
        run did not touch is the case it exists for."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            # A carrier that was ALREADY executed before this run, and no earned paths at all.
            executed = fx.root / ".aw/records/plans/executed" / plan.name
            plan.rename(executed)
            fx.commit("pre-executed carrier")
            verdict = oc_runipd.evaluate_backlog_close(fx.root, "bbbbbb", [])
            self.assertFalse(verdict.close)
            self.assertIn("not earned", verdict.reason)

    def test_the_verdict_is_main_s_view_not_the_lane_s_permissive_one(self):
        """The DISCRIMINATING fixture (F-10): in the lane THIS plan sits in `executed/` while in main
        it is still in `pending/`, and a SIBLING carrier is unexecuted in both. A lane-side evaluation
        would see one executed carrier and could close; main's view must refuse."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", order=1, from_backlog="bbbbbb")
            sibling = fx.add_plan("cccccc", order=2, from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()

            # Build the two views by hand so the assertion is about the PREDICATE, not the runner.
            lane_rel = f".aw/records/plans/executed/{plan.name}"
            main_rel = str(plan.relative_to(fx.root))
            # MAIN's view, with the lane's one fact supplied: still refuses, because the SIBLING is
            # unexecuted in main and no override is granted for it.
            verdict = oc_runipd.evaluate_backlog_close(
                fx.root,
                "bbbbbb",
                [lane_rel],
                executed_overrides={main_rel: lane_rel},
            )
            self.assertFalse(
                verdict.close,
                "main's view must refuse while a sibling carrier is unexecuted, even though the "
                "lane shows THIS plan executed",
            )
            self.assertIn(str(sibling.relative_to(fx.root)), verdict.reason)


# ======================================================================================
# The RELEASE GATE, which is the hazard F-10 named and nothing else covers
# ======================================================================================


class TheReleaseGateIsNotWidened(unittest.TestCase):
    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_a_release_gated_item_reaches_main_s_verdict_not_the_lane_s(self):
        """F-10: `--dir` also re-points `check_engine.evaluate_blocking_close`'s carrier scan.

        THE FIXTURE IS THE DISCRIMINATING ONE. The item carries `Blocks-Release: next` and its ONLY
        candidate carrier is this plan's own file. In the LANE that file is in `executed/` and carries
        `From-Backlog`, so a lane-side HANDOFF scan finds a satisfying carrier; main's view of the same
        item is what decides legitimacy. The setter is gated either way (that is what `--status done`
        buys), and the close is SATISFIED by an evidence citation that must RESOLVE in the tree the
        gate evaluates (F-11), so this test asserts the VERDICT and the citation, not merely that the
        run finished.
        """
        from agent_workflows import check_engine

        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            item_path = fx.add_item("bbbbbb", blocks_release="next")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])

            captured: dict = {}
            real_close = oc_runipd.close_backlog_item

            def spy_close(repo, ip, id6, evidence, message):
                captured["dir"] = str(repo)
                captured["evidence"] = evidence
                # F-11: the citation must RESOLVE in the tree the gate will evaluate against, which is
                # the same `--dir` the setter receives.
                captured["resolves_in_dir"] = check_engine.resolve_evidence_artifact(
                    Path(repo), evidence
                )
                captured["resolves_in_main"] = check_engine.resolve_evidence_artifact(
                    fx.root, evidence
                )
                return real_close(repo, ip, id6, evidence, message)

            with (
                mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)),
                mock.patch.object(oc_runipd, "close_backlog_item", spy_close),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            record = item.get("backlog_close") or {}
            self.assertTrue(record.get("closed"), record)
            # The gate ran against the LANE (one `--dir` cannot be split), so the citation MUST resolve
            # there; that is the F-11 obligation, and it is what keeps the SATISFIED route honest.
            self.assertTrue(
                captured["resolves_in_dir"],
                f"the evidence {captured['evidence']!r} must resolve in the tree the gate "
                f"evaluates ({captured['dir']})",
            )
            self.assertIn(
                "executed/",
                captured["evidence"],
                "the citation must name the carrier's REAL location, not main's stale pending path",
            )
            # THE GATE FIELD SURVIVES the close: dropping it would silently un-block a release.
            done = next((fx.root / ".aw/records/backlog/done").glob("*bbbbbb*.md"))
            self.assertIn(
                "- Blocks-Release: next",
                done.read_text(encoding="utf-8"),
                "the release gate field must be preserved, never silently dropped",
            )
            self.assertFalse(item_path.exists(), "the item must have MOVED")
            # And main is still clean, which is the point of the whole plan.
            self.assertEqual(fx.main_porcelain(), "")

    def test_a_release_gated_item_with_NO_carrier_link_is_still_refused(self):
        """The gate's fail-closed arm must remain reachable: an item carrying `Blocks-Release` whose
        carrier does NOT inherit the gate and with no resolvable evidence must be REFUSED, in either
        tree. This is the assertion that would fail if the redirect had widened the gate."""
        from agent_workflows import check_engine

        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            fx.add_item("bbbbbb", blocks_release="next")
            fx.commit()
            item_path = next(
                (fx.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
            )
            verdict = check_engine.evaluate_blocking_close(
                fx.root, item_path, "done", evidence=None
            )
            self.assertFalse(verdict.legitimate)
            self.assertEqual(verdict.severity, "error")
            # An unresolvable citation must not rescue it either.
            verdict = check_engine.evaluate_blocking_close(
                fx.root, item_path, "done", evidence="src/not-a-record.txt"
            )
            self.assertFalse(verdict.legitimate)


# ======================================================================================
# E-05: the cross-item regression this Set exists for, plus the non-isolated path
# ======================================================================================


class ThreeItemsAndMainStaysClean(unittest.TestCase):
    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_item_one_closing_a_backlog_item_does_not_block_items_two_and_three(self):
        """THE REGRESSION FOR THE MEASURED OUTAGE. Item 1 closes a backlog item; items 2 and 3 must
        still run, and MAIN must be clean after item 1.

        HONEST NOTE ON WHAT THIS ALONE PROVES, measured at execution by reverting the fix in place and
        re-running: the cross-item assertions below PASS EVEN PRE-FIX. That is not a weak test, it is
        an accurate one -- the ROOT CAUSE of the dirty tree was the un-paired move, and it was already
        fixed separately by commit `c53849e5` (the setter relocates with `git mv`), so a post-merge
        close now commits both halves and leaves main clean too. What this Set removes is the remaining
        mid-run WRITE to the shared checkout, which is a different (and still real) property: it is
        what makes the outage impossible rather than merely unlikely, and it is what the `wrote_in`
        assertion below pins. The three findings this file's other tests DO fail on pre-fix are
        recorded in the run's report.
        """
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            p1 = fx.add_plan("aaaaaa", order=1, from_backlog="bbbbbb")
            p2 = fx.add_plan("cccccc", order=2)
            p3 = fx.add_plan("dddddd", order=3)
            fx.add_item("bbbbbb")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            i1 = _queue_item(fx.root, p1, "aaaaaa", 1, "bbbbbb")
            i2 = _queue_item(fx.root, p2, "cccccc", 2, "")
            i3 = _queue_item(fx.root, p3, "dddddd", 3, "")
            i2.pop("from_backlog")
            i3.pop("from_backlog")
            state = _state(fx.root, [i1, i2, i3])
            porcelain_after: dict[str, str] = {}

            with mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)):
                for it in (i1, i2, i3):
                    oc_runipd.execute_item(run_dir, state, it, recovery=False)
                    porcelain_after[it["id6"]] = fx.main_porcelain()

            # THE CROSS-ITEM ASSERTION: main clean after the closing item, which is the state the
            # three measured runs did not reach.
            self.assertEqual(
                porcelain_after["aaaaaa"],
                "",
                "MAIN must be clean after the item that closed a backlog item",
            )
            # AND THE DISCRIMINATING ONE: the close must have been performed IN THE LANE, so main was
            # never written to at all. This is what fails pre-fix, and it is the property that makes
            # the cleanliness above structural rather than incidental.
            self.assertEqual(
                (i1.get("backlog_close") or {}).get("wrote_in"),
                "lane",
                "the close must be performed in the lane, so the shared checkout is never written "
                "to mid-run",
            )
            for it in (i1, i2, i3):
                self.assertEqual(
                    it["status"],
                    "executed",
                    f"item {it['id6']} must have executed; state was {it}",
                )
            self.assertEqual(fx.item_status("bbbbbb"), "done")
            for id6 in ("cccccc", "dddddd"):
                self.assertEqual(porcelain_after[id6], "")

    def test_the_non_isolated_path_still_moves_AND_still_commits(self):
        """E-02's other half, ASSERTED rather than assumed: with `--no-isolate-worktree` the close
        writes into the shared tree (there is no lane) and must still commit via
        `commit_backlog_close`, else it hands the next turn a dirty tree."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item], isolate=False)

            with mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            record = item.get("backlog_close") or {}
            self.assertTrue(record.get("closed"), record)
            self.assertEqual(
                record.get("wrote_in"),
                "main",
                "a non-isolated turn writes in main, by definition",
            )
            self.assertIsNotNone(
                record.get("commit"),
                "the non-isolated close must still COMMIT the move it made in the shared tree",
            )
            self.assertEqual(fx.item_status("bbbbbb"), "done")
            self.assertEqual(
                fx.main_porcelain(),
                "",
                "the non-isolated path must leave the tree clean, as it did before",
            )


# ======================================================================================
# Host parity and anti-divergence
# ======================================================================================


class TheClosingLaneIsStillTornDown(unittest.TestCase):
    """A consequence of moving the close into the lane, MEASURED at execution and fixed here.

    `aw backlog set` appends one record to the global history sidecar
    (`.aw/records/history.jsonl`), so a lane that closes a backlog item now holds that file. The lane
    teardown gate REFUSES while a lane holds an unaccounted untracked or ignored file -- correctly, by
    design -- so before this was handled, EVERY closing lane was preserved with
    "1 unknown IGNORED file(s): .aw/records/history.jsonl". That is the same "refuses always" failure
    the generated-INDEX clause beside it exists to prevent, and it had never been reachable before
    because PLANS are deliberately excluded from the sidecar, so a finalize-only lane never wrote it.

    The lane being preserved is not cosmetic: a preserved lane keeps a worktree and branch alive, and
    accumulating one per closing item is how a run fills its worktree directory.
    """

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_the_sidecar_predicate_is_exact(self):
        from agent_workflows import lane_containment, record_history

        self.assertTrue(
            lane_containment._is_driver_written_history_sidecar(
                record_history.SIDECAR_RELPATH
            )
        )
        self.assertTrue(
            lane_containment._is_driver_written_history_sidecar(
                f"./{record_history.SIDECAR_RELPATH}"
            )
        )
        self.assertTrue(
            lane_containment._is_driver_written_history_sidecar(
                f'"{record_history.SIDECAR_RELPATH}"'
            )
        )
        # NOTHING ELSE. Widening discardability is the dangerous direction, so a neighbouring
        # `.jsonl`, a real record, and a same-named file elsewhere must all stay UNKNOWN.
        for other in (
            ".aw/records/other.jsonl",
            ".aw/records/backlog/done/20260913-demo-01-bbbbbb-demo-item.backlog.md",
            "history.jsonl",
            ".aw/state/history.jsonl",
            ".aw/records/history.jsonl.bak",
        ):
            with self.subTest(path=other):
                self.assertFalse(
                    lane_containment._is_driver_written_history_sidecar(other),
                    f"{other} must NOT be treated as the driver-written sidecar",
                )

    def test_a_lane_that_closed_a_backlog_item_is_torn_down(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])

            with mock.patch.object(oc_runipd, "run_opencode", _fake_agent(run_dir)):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertTrue((item.get("backlog_close") or {}).get("closed"), item)
            self.assertIsNone(
                item.get("preserved_branch"),
                "a successful closing lane must be TORN DOWN, not preserved; the history "
                "sidecar the setter writes must be classified as driver-written",
            )
            self.assertFalse(
                (fx.root / ".aw" / "worktrees" / "aaaaaa").exists(),
                "the lane worktree must be removed",
            )
            branches = _git(fx.root, "branch", "--list", "aw/lane/aaaaaa").strip()
            self.assertEqual(branches, "", "the lane branch must be removed")

    def test_the_inventory_classifies_the_sidecar_as_discardable(self):
        """The unit-level statement of the same rule, so a refactor of the loop cannot lose it."""
        from agent_workflows import lane_containment, record_history

        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            _git(lane, "init", "-q")
            _git(lane, "config", "user.email", "t@t")
            _git(lane, "config", "user.name", "t")
            (lane / ".gitignore").write_text(
                f"{record_history.SIDECAR_RELPATH}\n", encoding="utf-8"
            )
            _git(lane, "add", "-A")
            _git(lane, "commit", "-qm", "base")
            sidecar = lane / record_history.SIDECAR_RELPATH
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_text('{"id6":"bbbbbb"}\n', encoding="utf-8")

            inv = lane_containment.inventory_lane(lane_root=lane)
            self.assertTrue(inv.readable, inv.failure)
            # THE ASSERTION IS ABOUT THIS ONE FILE'S CLASSIFICATION, deliberately, and NOT about
            # `inv.classified`: with no `run_dir`/`item` supplied there is no collection receipt to
            # read, so the inventory ALSO reports an uncollected submission and refuses for that
            # separate and correct reason. Asserting the aggregate here would be asserting the
            # fixture's incompleteness rather than the rule under test; the aggregate is covered
            # end to end by `test_a_lane_that_closed_a_backlog_item_is_torn_down` above.
            self.assertIn(record_history.SIDECAR_RELPATH, inv.discardable)
            self.assertEqual(inv.unknown_ignored, ())
            self.assertEqual(inv.unknown_untracked, ())


class AgyHostClosesInTheLaneToo(unittest.TestCase):
    """E-05, BEHAVIORALLY and not only by source inspection.

    Spec `7ckptx` R4 treats a host-only guard as a divergence, and `z2isfg` already left agy behind
    once on a neighbouring gate, so the agy path is exercised end to end rather than asserted about.
    The agy driver's turn signature differs (`run_agy_turn(state, rd, item, prompt_path, attempt_no,
    **kwargs)`, and its verifier turn is keyed on `log_suffix == "verify"` rather than
    `fresh_session`), which is precisely why a shared fake would not have caught a divergence here.
    """

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def _fake_turn(self, run_dir: Path):
        def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("log_suffix") == "verify":
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            tree = Path(work_dir) if work_dir else Path(state["repo"])
            (tree / "src").mkdir(parents=True, exist_ok=True)
            (tree / "src" / f"{item['id6']}.txt").write_text("demo\n", encoding="utf-8")
            _git(tree, "add", f"src/{item['id6']}.txt")
            _git(tree, "commit", "-qm", f"demo({item['id6']}): create the file")
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

    def test_agy_closes_in_the_lane_and_leaves_main_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            plan = fx.add_plan("aaaaaa", from_backlog="bbbbbb")
            fx.add_item("bbbbbb")
            fx.commit()
            before_head = _git(fx.root, "rev-parse", "HEAD").strip()
            run_dir = _mk_run_dir(fx.root)
            item = _queue_item(fx.root, plan, "aaaaaa", 1, "bbbbbb")
            state = _state(fx.root, [item])
            state["options"]["no_verify"] = False
            state["options"].pop("opencode", None)

            with mock.patch.object(
                agy_runipd, "run_agy_turn", self._fake_turn(run_dir)
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed", item)
            record = item.get("backlog_close") or {}
            self.assertTrue(record.get("closed"), record)
            self.assertEqual(record.get("wrote_in"), "lane", record)
            self.assertEqual(
                fx.main_porcelain(),
                "",
                "MAIN must be clean after an agy item that closed a backlog item",
            )
            self.assertEqual(fx.item_status("bbbbbb"), "done")
            name_status = _git(fx.root, "diff", "--name-status", f"{before_head}..HEAD")
            self.assertIn(".aw/records/backlog/done/", name_status, name_status)

    def test_agy_three_items_and_main_stays_clean(self):
        """The agy half of the cross-item regression: item 1 closes, items 2 and 3 still run."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            p1 = fx.add_plan("aaaaaa", order=1, from_backlog="bbbbbb")
            p2 = fx.add_plan("cccccc", order=2)
            p3 = fx.add_plan("dddddd", order=3)
            fx.add_item("bbbbbb")
            fx.commit()
            run_dir = _mk_run_dir(fx.root)
            i1 = _queue_item(fx.root, p1, "aaaaaa", 1, "bbbbbb")
            i2 = _queue_item(fx.root, p2, "cccccc", 2, "")
            i3 = _queue_item(fx.root, p3, "dddddd", 3, "")
            i2.pop("from_backlog")
            i3.pop("from_backlog")
            state = _state(fx.root, [i1, i2, i3])
            state["options"]["no_verify"] = False
            state["options"].pop("opencode", None)
            porcelain_after: dict[str, str] = {}

            with mock.patch.object(
                agy_runipd, "run_agy_turn", self._fake_turn(run_dir)
            ):
                for it in (i1, i2, i3):
                    agy_runipd.execute_item(run_dir, state, it, recovery=False)
                    porcelain_after[it["id6"]] = fx.main_porcelain()

            self.assertEqual(porcelain_after["aaaaaa"], "")
            self.assertEqual((i1.get("backlog_close") or {}).get("wrote_in"), "lane")
            for it in (i1, i2, i3):
                self.assertEqual(it["status"], "executed", f"{it['id6']}: {it}")
            self.assertEqual(fx.item_status("bbbbbb"), "done")


class BothHostsBehaveIdentically(unittest.TestCase):
    def test_both_drivers_close_in_the_lane_before_integrating(self):
        """The ORDERING is the behavior: the lane-side close must appear BEFORE the integration call
        in each host's finalize-success branch, else it is not riding the merge."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = _effective_execute_item_source(mod)
                self.assertIn(
                    "lane_handle=wt_handle",
                    src,
                    f"{name} must pass the lane handle to the close",
                )
                close_at = src.index("lane_repo=Path(work_dir)")
                integrate_at = src.index("integrated, integ_reason, integ_kind =")
                self.assertLess(
                    close_at,
                    integrate_at,
                    f"{name} must close IN THE LANE before integrating, else the move cannot "
                    f"ride the merge",
                )

    def test_the_post_merge_close_is_guarded_against_overwriting_a_success(self):
        """A second evaluation of an already-closed item answers `already done` (close=False) and
        would overwrite the success record with a refusal, reporting a correct close as 'left open'."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = _effective_execute_item_source(mod)
                self.assertIn(
                    'if not (item.get("backlog_close") or {}).get("closed"):',
                    src,
                    f"{name}'s post-merge close must be guarded",
                )


class TheEarnedPathsRangeIsTheLaneBranch(unittest.TestCase):
    def test_the_lane_range_is_read_from_the_branch_not_from_mains_head(self):
        """F-7, corrected. The attempt records MAIN's HEAD before and after, and for an isolated turn
        main's HEAD does not move, so that range is empty. The lane BRANCH's range is where the work
        is, and it resolves from main because a linked worktree shares the object database."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            fx.add_plan("aaaaaa")
            fx.commit()
            base = _git(fx.root, "rev-parse", "HEAD").strip()
            handle = oc_runipd.allocate_isolation_worktree(fx.root, "aaaaaa")
            lane = Path(handle.path)
            _git(lane, "config", "user.email", "test@example.invalid")
            _git(lane, "config", "user.name", "Test")
            (lane / "src").mkdir(parents=True, exist_ok=True)
            (lane / "src" / "demo.txt").write_text("x\n", encoding="utf-8")
            _git(lane, "add", "src/demo.txt")
            _git(lane, "commit", "-qm", "lane work")

            # The ATTEMPT's own range is empty (main's HEAD never moved) -- the trap.
            self.assertEqual(
                oc_runipd.collect_earned_paths(
                    fx.root,
                    {"attempts": [{"starting_head": base, "ending_head": base}]},
                ),
                [],
                "main's HEAD..HEAD range is empty, which is exactly why the lane range is needed",
            )
            # The LANE BRANCH's range holds the work, read with cwd=main.
            earned = oc_runipd.collect_lane_earned_paths(fx.root, handle)
            self.assertIn("src/demo.txt", earned, earned)

    def test_a_missing_handle_yields_nothing_rather_than_raising(self):
        """Best-effort, exactly like `collect_earned_paths`: fewer earned paths can only WITHHOLD a
        close, so failing quietly is the safe direction, but it must never raise."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo")
            fx.commit()

            class _Bad:
                base_commit = ""
                branch = ""

            self.assertEqual(oc_runipd.collect_lane_earned_paths(fx.root, _Bad()), [])

            class _Nonexistent:
                base_commit = "deadbeef"
                branch = "no/such/branch"

            self.assertEqual(
                oc_runipd.collect_lane_earned_paths(fx.root, _Nonexistent()), []
            )


if __name__ == "__main__":
    unittest.main()
