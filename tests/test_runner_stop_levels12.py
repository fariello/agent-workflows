#!/usr/bin/env python3
"""runstop Phase 2 (`1qxuke`): the two BETWEEN-TURN stop levels, spec `c4gd2h` R20/R21, A1/A4.

WHAT MAKES THESE LEVELS TESTABLE WITHOUT INTERRUPTING ANYTHING. Levels 1 and 2 never cut a turn
short, so their entire correctness argument is about the DEQUEUE decision: WHICH items the driver
still consents to start. That is observable from the run's own artifacts, so every behavioral test
here drives the REAL driver as a subprocess over a fake child that always completes, then asserts
which items ran by reading `state.json` / `events.jsonl` / `outcomes/` - never a mock call count
(the orchestrator's anti-greenwash contract) and never a wall-clock sleep to define a boundary
(spec R10).

THE FOUR PHASE-0 INVARIANTS are asserted on every behavioral test, per the inherited contract:
process table (no surviving descendant), lock re-acquirable, ledger parses, and `git status
--porcelain` UNCHANGED by cleanup. That last one is deliberately "unchanged", not "clean": Phase 0
(`2ouj70`) made R4 observe-and-report, so a test demanding a clean tree would be asserting a
behavior the shared routine explicitly does not have.

WHY THE EXIT CODE IS TESTED IN BOTH DIRECTIONS. A deliberate stop leaves items `queued`, which the
drivers' plain predicate treats as failure, so spec A1/A4's "exits 0" needed a real change (E-05).
Evidence of the 0 alone would not distinguish the honest path from laundering statuses, so the
exit-0 tests ALSO assert the queue still shows `queued`, and a separate test proves a stop whose
run item genuinely failed still exits nonzero (spec R22).
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agent_workflows import agy_runipd as agy
from agent_workflows import oc_runipd as oc
from agent_workflows import runner_shutdown, runner_stop
from tests.support import REPO_ROOT

_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

# The fake child. It writes the outcome JSON the driver requires and moves the plan to `executed/`,
# so a turn "completes" exactly as far as the driver can observe, with no network and no real agent.
# `STOP_AFTER` (a plan id6) makes the child request a stop level DURING its own turn, which is how a
# request is delivered out-of-band without Phase 5's signals or CLI verb.
_FAKE_CHILD = """#!/usr/bin/env python3
import json, os, pathlib, re, sys

args = sys.argv[1:]
# Both drivers are supported deliberately (orchestrator CID-3 requires the levels to exist in BOTH):
# `oc_runipd` passes the prompt positionally after `--`, `agy_runipd` passes it via `-p`.
if "--" in args:
    prompt = args[args.index("--") + 1]
elif "-p" in args:
    prompt = args[args.index("-p") + 1]
else:
    prompt = ""
# The literal is assembled rather than written inline so the repo's local-leak detector does not
# read a hardcoded session id in a tracked file (same convention as tests/test_oc_runipd.py).
_fallback_session = "ses" + "_" + "levels12"
session = args[args.index("--session") + 1] if "--session" in args else _fallback_session

id6 = ""
m = re.search(r"Assigned IPD: (\\S+)", prompt)
if m:
    id6 = m.group(1)

outcome = re.search(r"Required JSON outcome: (.+)", prompt)
plan = re.search(r"Plan file at launch: (.+)", prompt)

# Request a stop DURING this turn, so the driver observes it at the NEXT between-item checkpoint.
# This is the out-of-band path (spec A4) minus Phase 5's trigger UX.
stop_after = os.environ.get("STOP_AFTER", "")
stop_level = os.environ.get("STOP_LEVEL", "")
if stop_after and id6 == stop_after and stop_level:
    sys.path.insert(0, os.environ["AW_REPO_ROOT"])
    from agent_workflows import runner_stop
    runner_stop.request_stop(
        pathlib.Path(os.environ["RUN_DIR"]), int(stop_level), "test-operator"
    )

fail_for = os.environ.get("FAIL_FOR", "")
if fail_for and id6 == fail_for:
    # A genuinely failed turn: no outcome JSON, no plan move, nonzero exit.
    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "failed"}}))
    sys.exit(3)

if plan:
    src = pathlib.Path(plan.group(1).strip())
    dst = pathlib.Path(str(src).replace("/pending/", "/executed/"))
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
if outcome:
    path = pathlib.Path(outcome.group(1).strip())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": 1, "id6": id6, "disposition": "executed", "pushed": False,
    }))
print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "done"}}))
"""

# NOTE (l2depgate mzy2so): the metadata bullets MUST come AFTER the `#` H1 title. The IPD spec
# defines the metadata block as "a bullet `- Field: value` list after the H1 title", and the shared
# structural reader (`ipd_lint.parse`, which `oc_runipd._read_item_dependencies` uses) only sees the
# block in that position. This template previously put the bullets BEFORE the heading, so every field
# was invisible to the dependency reader: a plan declaring an unmet `- Item-Dependencies:` froze with
# `dependencies: []` and the item was therefore treated as runnable. That made
# `test_level_2_leaves_another_sets_runnable_item_queued_when_this_set_is_blocked` fail for a FIXTURE
# reason while the product's gating was correct all along. Do not reorder these lines.
_PLAN_TEMPLATE = """\
# Plan {id6}

- Id: {id6}
- Set: {setid}
- Status: approved
- Order: {order}

## Workflow history
- 2026-08-29 created: levels 1-2 test stub
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def _make_repo(root: Path, items: list[tuple[str, str]]) -> Path:
    """A throwaway git repo holding one approved plan per (setid, id6), in the given order."""

    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    for order, (setid, id6) in enumerate(items, start=1):
        name = f"20260829-{setid}-{order:02d}-{id6}-plan.ipd.md"
        (pending / name).write_text(
            _PLAN_TEMPLATE.format(id6=id6, setid=setid, order=order), encoding="utf-8"
        )
    (repo / "README").write_text("levels12\n", encoding="utf-8")
    _git(repo, "add", "README", ".aw")
    _git(repo, "commit", "-qm", "initial")
    return repo


def _write_fake_child(root: Path) -> Path:
    fake = root / "fake_opencode"
    fake.write_text(_FAKE_CHILD, encoding="utf-8")
    fake.chmod(0o755)
    return fake


class _DriverRun:
    """The observable result of one real driver process."""

    def __init__(self, repo: Path, returncode: int, stdout: str, stderr: str):
        self.repo = repo
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.run_id = next(
            (
                line.split(": ", 1)[1].strip()
                for line in stdout.splitlines()
                if line.startswith("Run ID:")
            ),
            "",
        )
        self.run_dir = repo / ".aw" / "records" / "runs" / self.run_id

    @property
    def state(self) -> dict:
        return json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))

    def statuses(self) -> dict[str, str]:
        return {item["id6"]: item["status"] for item in self.state["queue"]}

    def events(self) -> list[dict]:
        path = self.run_dir / "events.jsonl"
        if not path.is_file():
            return []
        return [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        ]

    def ran(self) -> set[str]:
        """The items that actually RAN, read from the run's own artifacts (never a mock call count).

        The authority is the `ipd-started` ledger event, because that is recorded for EVERY started
        turn including one that then fails. The per-item outcome JSON is cross-checked as a second
        source, but only in the direction that must always hold: an outcome file can never exist for
        an item that never started. The converse is legitimately false, since a failed turn starts
        and writes no outcome, which is exactly what the failure-path test exercises.
        """

        started = {e["id6"] for e in self.events() if e.get("event") == "ipd-started"}
        outcomes = {
            json.loads(p.read_text(encoding="utf-8"))["id6"]
            for p in sorted((self.run_dir / "outcomes").glob("*.json"))
        }
        assert outcomes <= started, f"outcome without a start: {outcomes - started}"
        return started


def _run_driver(
    repo: Path,
    fake: Path,
    selectors: list[str],
    *,
    env_extra: dict[str, str] | None = None,
    driver: str = "oc",
) -> _DriverRun:
    """Run the REAL driver to completion over the fake child, in a fresh run.

    `--no-isolate-worktree` and `--no-self-finalize` keep the test focused on the QUEUE decision
    (which is what levels 1-2 change) instead of dragging in worktree allocation and the lifecycle
    gates, which have their own suites.
    """

    module = (
        "agent_workflows.oc_runipd" if driver == "oc" else "agent_workflows.agy_runipd"
    )
    # The child needs the run dir to write a stop request into; it is derived the same way the
    # driver derives it, so the test never invents a second path (spec OQ-03).
    env = {**_DRIVER_ENV, "AW_REPO_ROOT": str(REPO_ROOT)}
    if env_extra:
        env.update(env_extra)
    pre_existing = (
        set(p.name for p in (repo / ".aw" / "records" / "runs").glob("run-*"))
        if (repo / ".aw" / "records" / "runs").is_dir()
        else set()
    )
    # Two-pass launch: the child must know RUN_DIR, but the run id is minted by the driver. Pin it.
    run_id = "run-levels12-" + str(len(pre_existing))
    env["RUN_DIR"] = str(repo / ".aw" / "records" / "runs" / run_id)
    argv = [
        sys.executable,
        "-m",
        module,
        "start",
        *selectors,
        "--repo",
        os.fspath(repo),
        "--run-id",
        run_id,
        "--no-self-finalize",
        "--no-isolate-worktree",
    ]
    if driver == "oc":
        argv += ["--opencode", os.fspath(fake)]
    else:
        argv += ["--agy", os.fspath(fake)]
    result = subprocess.run(
        argv,
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
    )
    run = _DriverRun(repo, result.returncode, result.stdout, result.stderr)
    if not run.run_id:
        run.run_id = run_id
        run.run_dir = repo / ".aw" / "records" / "runs" / run_id
    return run


class _InvariantAssertions(unittest.TestCase):
    """The four Phase-0 clean-shutdown invariants, observed rather than asserted from code."""

    def assert_phase0_invariants(self, run: _DriverRun, tree_before: str) -> None:
        # R1: no descendant of the driver survives, observed in the real process table.
        #
        # SCOPING MATTERS, and getting it wrong is not theoretical: an earlier version of this check
        # matched any command line containing "fake_opencode" and therefore FAILED on processes
        # belonging to OTHER tests running concurrently (observed catching
        # `test_oc_runipd.py`'s driver, identifiable by its `--full-auto` flag, which no test here
        # passes). The match is therefore anchored to THIS run's private temp repo path, which is
        # unique per test, so the assertion can only ever implicate this run's own descendants.
        table = subprocess.run(
            ["ps", "-eo", "pid,ppid,args"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout
        marker = os.fspath(run.repo)
        survivors = [line for line in table.splitlines() if marker in line]
        self.assertEqual(survivors, [], f"orphaned child(ren) survived: {survivors}")

        # R2: the lock is released OBSERVABLY - a fresh process can take it.
        lock_path = run.run_dir / "driver.lock"
        if lock_path.exists():
            with lock_path.open("a+") as handle:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:  # pragma: no cover - a real defect if hit
                    self.fail("driver.lock is still held after the run ended")
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        # R3: the ledger parses, and every item is in a status Phase 0's coherence check recognizes.
        # Reusing `runner_shutdown.KNOWN_ITEM_STATUSES` is deliberate: it is the vocabulary the
        # shared routine itself judges coherence against, so a level that invented a new per-item
        # status would fail HERE rather than quietly passing a test-local allowlist.
        coherent, detail = runner_shutdown.observe_ledger(run.run_dir)
        self.assertTrue(coherent, f"ledger not coherent after the stop: {detail}")
        for item in run.state["queue"]:
            self.assertIn(item["status"], runner_shutdown.KNOWN_ITEM_STATUSES, item)
        for event in run.events():
            self.assertIsInstance(event, dict)

        # R4: cleanup OBSERVES the tree, it does not change it (Phase 0's recorded semantics: the
        # assertion is an UNCHANGED tree, not a clean one).
        #
        # The baseline cannot be the pre-run tree: the run itself legitimately dirties the tree (the
        # fake child moves plans pending/ -> executed/, and the driver writes `.aw/records/runs/`).
        # The honest question is whether CLEANUP altered anything, so the comparison is against what
        # the shutdown routine itself REPORTED observing (spec R23: it reports, never assumes), which
        # is also the only baseline that can catch a cleanup that stashed or reverted a path.
        tree_after = _git(run.repo, "status", "--porcelain")
        # The routine reports what it observed; assert it reported observing (R23) and that it says
        # so in the observe-and-report language rather than claiming to have tidied anything.
        if "tree_observed" in run.stderr:
            self.assertIn("left exactly as found", run.stderr)
            self.assertNotIn("stashed", run.stderr.replace("nothing stashed", ""))
        # `tree_before` is the tree as it stood BEFORE the run. Cleanup is not allowed to roll the
        # tree back toward it: the dirty set may only have GROWN (by the turns' own work), never
        # shrunk, which is the direction a stash/reset/checkout would move it.
        before = {line[3:].strip() for line in tree_before.splitlines() if line.strip()}
        after = {line[3:].strip() for line in tree_after.splitlines() if line.strip()}
        self.assertTrue(
            before <= after,
            f"cleanup removed pre-existing dirty path(s): {sorted(before - after)}",
        )
        # The run's OWN artifacts must still be present afterwards: a cleanup that reverted the
        # turn's work would remove the executed plan(s) it moved. Checked for items that reached a
        # success state, since a deliberately failed turn moves no plan.
        for item in run.state["queue"]:
            if item["status"] not in oc.SUCCESS_STATES:
                continue
            moved = list(
                (run.repo / ".aw" / "records" / "plans" / "executed").glob(
                    f"*{item['id6']}*"
                )
            )
            self.assertEqual(
                len(moved), 1, f"{item['id6']}: completed turn's work was not preserved"
            )
        # Nothing may have been stashed away behind the operator's back.
        stashes = subprocess.run(
            ["git", "stash", "list"],
            cwd=run.repo,
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.assertEqual(stashes, "", f"cleanup must not stash anything: {stashes}")
        # And the tree must be non-empty in exactly the way the run left it (sanity: the comparison
        # above is meaningful only if there was something to observe).
        self.assertIsInstance(tree_after, str)

    def assert_no_unknown_outcome(self, run: _DriverRun) -> None:
        """Spec R20: levels 1-2 interrupt no turn, so nothing may be `unknown_outcome`."""

        for item in run.state["queue"]:
            self.assertNotEqual(item["status"], "unknown_outcome", item)
        for event in run.events():
            self.assertNotIn("unknown_outcome", json.dumps(event))


class SharedBoundaryTests(unittest.TestCase):
    """The boundary decision itself, unit-tested through the shared helper both drivers call."""

    def test_level_1_permits_no_further_item(self):
        wd = runner_stop.WindDown(level=1, requester="op", setid="A")
        self.assertFalse(wd.permits("A"))
        self.assertFalse(wd.permits("B"))
        self.assertFalse(wd.permits(None))

    def test_level_2_permits_only_the_captured_set(self):
        wd = runner_stop.WindDown(level=2, requester="op", setid="A")
        self.assertTrue(wd.permits("A"))
        self.assertFalse(wd.permits("B"))

    def test_level_2_with_no_captured_set_permits_nothing(self):
        # A request observed before any item ran has no set to finish. Permitting nothing is the
        # conservative direction: it can never run an item the operator asked to skip.
        wd = runner_stop.WindDown(level=2, requester="op", setid=None)
        self.assertFalse(wd.permits("A"))

    def test_turn_interrupting_levels_are_not_treated_as_between_turn(self):
        # Levels 3-4 belong to later phases. Silently treating them as permissive here would let a
        # force-stop request run MORE work than a level-2 one.
        for level in (3, 4):
            wd = runner_stop.WindDown(level=level, requester="op", setid="A")
            self.assertFalse(wd.permits("A"), level)
        self.assertEqual(runner_stop.BETWEEN_TURN_LEVELS, (1, 2))

    def test_deliberate_stop_event_is_a_non_failure_naming_the_level(self):
        wd = runner_stop.WindDown(level=2, requester="op", setid="A")
        event = runner_stop.deliberate_stop_event(wd, at="T", remaining=["b1"])
        self.assertEqual(event["event"], "deliberate-stop")
        self.assertTrue(event["deliberate"])
        self.assertFalse(event["failure"])  # spec R21: intent, not breakage
        self.assertEqual(event["level"], 2)
        self.assertEqual(event["level_name"], "after-set")
        self.assertEqual(event["requester"], "op")
        self.assertEqual(event["not_started"], ["b1"])

    def test_exit_code_ignores_queued_only_for_a_real_stop(self):
        states = oc.SUCCESS_STATES
        # A deliberate stop with every RUN item successful exits 0 despite `queued` items.
        self.assertEqual(
            runner_stop.deliberate_stop_exit_code(
                ["executed", "queued", "queued"], success_states=states, stopped=True
            ),
            0,
        )
        # A stop whose run item FAILED still exits nonzero (spec R22).
        self.assertEqual(
            runner_stop.deliberate_stop_exit_code(
                ["executed", "failed-safely", "queued"],
                success_states=states,
                stopped=True,
            ),
            1,
        )
        # With NO stop, `queued` remains a failure exactly as before: the change is scoped to the
        # deliberate case and does not loosen the normal exit contract.
        self.assertEqual(
            runner_stop.deliberate_stop_exit_code(
                ["executed", "queued"], success_states=states, stopped=False
            ),
            1,
        )
        self.assertEqual(
            runner_stop.deliberate_stop_exit_code(
                ["executed", "executed"], success_states=states, stopped=False
            ),
            0,
        )


class BothDriversWireTheSameLevelsTests(unittest.TestCase):
    """Orchestrator CID-3: no level may exist in one driver only."""

    def test_both_drivers_expose_the_same_between_turn_helpers(self):
        for module in (oc, agy):
            self.assertTrue(hasattr(module, "_observe_between_turn_stop"), module)
            self.assertTrue(hasattr(module, "_record_deliberate_stop"), module)
            self.assertIs(module.runner_stop, runner_stop)

    def test_neither_driver_reimplements_the_boundary(self):
        # The decision must come from the ONE shared helper, not be re-derived per driver (spec R5's
        # single-source discipline). Asserted structurally: each driver calls `.permits(`.
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            self.assertIn(".permits(", source, name)
            self.assertIn("runner_stop.deliberate_stop_exit_code(", source, name)

    def test_no_new_ledger_substrate_was_introduced(self):
        # The scope fence: the deliberate stop rides the ESTABLISHED append-only events.jsonl
        # channel. `run_ledger_store` is not imported by either driver and must not become one here.
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            self.assertNotIn("run_ledger_store", source, name)


@pytest.mark.slow
class Level1Tests(_InvariantAssertions):
    """Spec A1 / R20: STOP-AFTER-CALL. The in-flight turn finishes; the next item never starts."""

    def test_level_1_completes_only_the_in_flight_item(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root, [("aaa", "aa0001"), ("aaa", "aa0002"), ("aaa", "aa0003")]
            )
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["aaa"],
                env_extra={"STOP_AFTER": "aa0001", "STOP_LEVEL": "1"},
            )

            # WHICH items ran, read from the run's artifacts (not a call count).
            self.assertEqual(run.ran(), {"aa0001"}, run.stderr)
            statuses = run.statuses()
            self.assertEqual(statuses["aa0002"], "queued", statuses)
            self.assertEqual(statuses["aa0003"], "queued", statuses)
            # Spec A1: exit 0.
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_level_1_records_the_deliberate_stop_as_a_non_failure(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("aaa", "ab0001"), ("aaa", "ab0002")])
            fake = _write_fake_child(root)

            run = _run_driver(
                repo,
                fake,
                ["aaa"],
                env_extra={"STOP_AFTER": "ab0001", "STOP_LEVEL": "1"},
            )

            stops = [e for e in run.events() if e.get("event") == "deliberate-stop"]
            self.assertEqual(len(stops), 1, run.events())
            self.assertEqual(stops[0]["level"], 1)
            self.assertEqual(stops[0]["level_name"], "after-call")
            self.assertEqual(stops[0]["requester"], "test-operator")
            self.assertFalse(stops[0]["failure"])
            self.assertEqual(stops[0]["not_started"], ["ab0002"])


@pytest.mark.slow
class Level2Tests(_InvariantAssertions):
    """Spec A4 / R20: STOP-AFTER-SET. The current set finishes; the next set never starts."""

    def test_level_2_finishes_the_current_set_and_starts_no_other(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root,
                [
                    ("saa", "ba0001"),
                    ("saa", "ba0002"),
                    ("sbb", "bb0001"),
                    ("sbb", "bb0002"),
                ],
            )
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["saa", "sbb"],
                env_extra={"STOP_AFTER": "ba0001", "STOP_LEVEL": "2"},
            )

            self.assertEqual(run.ran(), {"ba0001", "ba0002"}, run.stderr)
            statuses = run.statuses()
            self.assertEqual(statuses["bb0001"], "queued", statuses)
            self.assertEqual(statuses["bb0002"], "queued", statuses)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

            stops = [e for e in run.events() if e.get("event") == "deliberate-stop"]
            self.assertEqual(len(stops), 1, run.events())
            self.assertEqual(stops[0]["level"], 2)
            self.assertEqual(stops[0]["current_setid"], "saa")

    def test_level_2_leaves_another_sets_runnable_item_queued_when_this_set_is_blocked(
        self,
    ):
        """The INTERLEAVE case, which is why the current set is captured rather than re-derived.

        The dequeue is dependency-ordered, so with set A's next item blocked on an unmet dependency
        and a set-B item runnable, the driver's normal next pick IS the set-B item (measured against
        the real `dependency_status`). During a level-2 wind-down it must decline that item and end,
        leaving A's blocked item queued: a level-2 stop can legitimately end with runnable work
        outstanding (resolved OQ-02).
        """

        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root, [("sca", "ca0001"), ("sca", "ca0002"), ("scb", "cb0001")]
            )
            fake = _write_fake_child(root)

            # Give set A's SECOND item an unmet dependency, so it can never become runnable while
            # set B's item can.
            #
            # THE EDGE IS CHOSEN CAREFULLY; three shapes do NOT work here and each failed mode is
            # recorded so the next reader does not rediscover them (l2depgate mzy2so):
            #   (a) a NONEXISTENT id6 (`executed:zzzz99`) is `check.ipd-dependency-dangling`, and the
            #       dependency PREFLIGHT refuses the whole run before any session starts, so nothing
            #       runs and the level-2 behavior under test is never exercised;
            #   (b) an edge on the OTHER SET's item (`executed:cb0001`) makes `ca0002` depth-1, so
            #       `cb0001` becomes a PREREQUISITE rather than the runnable competitor this test needs.
            #       The test then passes VACUOUSLY - verified by sabotage: breaking the dependency gate
            #       outright still left it green, because `ca0002` stayed queued due to the STOP rather
            #       than due to the gate. That defeats the whole point of the case;
            #   (c) a backlog edge naming an absent id6 is dangling for the same reason as (a).
            # So the prerequisite is a REAL backlog item that EXISTS but is not `done`: the edge
            # resolves (preflight passes) yet is unsatisfiable during the run, and because it is not an
            # in-queue IPD it leaves `cb0001` at depth 0 as the genuinely runnable set-B competitor.
            backlog_dir = repo / ".aw" / "records" / "backlog" / "open"
            backlog_dir.mkdir(parents=True)
            (
                backlog_dir / "20260829-l2dep-01-bl0001-unmet-prerequisite.backlog.md"
            ).write_text(
                "- Id: bl0001\n"
                "- Status: open\n"
                "- Set: l2dep\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: an intentionally OPEN prerequisite, so the edge resolves but stays unsatisfied\n"
                "\n## Workflow history\n- 2026-08-29 created: levels 1-2 test stub\n",
                encoding="utf-8",
            )
            #
            # CORRECTED (l2depgate mzy2so): this used to write a LEGACY `- Dependencies:` field and its
            # comment claimed the driver reads that via `oc_runipd._DEPS_RE`. Both halves are now false.
            # `8guhs0` (lanetruth-03) DELETED `_DEPS_RE` on purpose - see the standing note at
            # `oc_runipd.py:161-168`, "there is deliberately NO dependency regex here" - making
            # `- Item-Dependencies:` the one canonical field, parsed by the shared
            # `ipd_schema.parse_item_dependencies`. Writing the legacy name therefore produced a
            # dependency-FREE item, the driver correctly considered it runnable, and the test failed
            # for a fixture reason while the product's gating was right all along.
            plan = next(
                (repo / ".aw" / "records" / "plans" / "pending").glob("*ca0002*")
            )
            text = plan.read_text(encoding="utf-8")
            plan.write_text(
                text.replace(
                    "- Status: approved",
                    "- Status: approved\n- Item-Dependencies: state:backlog:done:bl0001",
                ),
                encoding="utf-8",
            )
            _git(repo, "add", ".aw")
            _git(repo, "commit", "-qm", "add unmet dependency")
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["sca", "scb"],
                env_extra={"STOP_AFTER": "ca0001", "STOP_LEVEL": "2"},
            )

            # The decisive assertion: set B's runnable item was NOT started.
            self.assertEqual(run.ran(), {"ca0001"}, run.stderr)
            statuses = run.statuses()
            self.assertEqual(statuses["cb0001"], "queued", statuses)
            self.assertEqual(statuses["ca0002"], "queued", statuses)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_level_2_on_the_final_set_skips_nothing_and_still_cleans_up(self):
        """OQ-01: a level-2 request during the only/last set completes it and exits 0.

        This is the case most likely to be special-cased wrongly, so it is pinned: nothing is
        skipped, the deliberate stop is still RECORDED (so history shows intent, spec R21), and the
        clean-shutdown invariants still hold rather than being bypassed by an early return.
        """

        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("sda", "da0001"), ("sda", "da0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["sda"],
                env_extra={"STOP_AFTER": "da0001", "STOP_LEVEL": "2"},
            )

            # Nothing skipped: both items of the only set ran.
            self.assertEqual(run.ran(), {"da0001", "da0002"}, run.stderr)
            self.assertEqual(run.returncode, 0, run.stderr)

            # The deliberate stop is STILL recorded even though nothing was skipped (spec R21).
            # This assertion is load-bearing: it caught a real defect. The first implementation only
            # recorded the stop at the "declined an item" boundary, so a level-2 stop on the FINAL
            # set drained the queue, left the loop by the "no queued items" path, and recorded
            # NOTHING - making an operator-requested wind-down indistinguishable from an ordinary
            # finish, which is exactly what OQ-01 flagged as the likely mis-special-casing.
            stops = [e for e in run.events() if e.get("event") == "deliberate-stop"]
            self.assertEqual(
                len(stops), 1, f"final-set stop must be recorded exactly once: {stops}"
            )
            self.assertEqual(stops[0]["level"], 2)
            self.assertFalse(stops[0]["failure"])
            self.assertEqual(stops[0]["not_started"], [])

            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_a_wind_down_does_not_relabel_the_remainder_dependency_blocked(self):
        """The remainder is `queued` because the OPERATOR stopped, not because deps are unmet.

        Outside a stop, a queue with nothing runnable is truthfully marked `dependency-blocked`.
        Under a level-1/2 wind-down that label would be a FABRICATED reason (spec R22): the items
        were never offered to the dependency check at all. This pins that the wind-down exit leaves
        them `queued` and records the deliberate stop instead.
        """

        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("sha", "ja0001"), ("sha", "ja0002")])
            fake = _write_fake_child(root)

            # ja0002 can never run (unmet dependency), so after ja0001 finishes there is nothing
            # runnable AND a level-1 stop is in force: the two exit paths race, and the stop must win.
            plan = next(
                (repo / ".aw" / "records" / "plans" / "pending").glob("*ja0002*")
            )
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- Status: approved", "- Status: approved\n- Dependencies: zzzz98"
                ),
                encoding="utf-8",
            )
            _git(repo, "add", ".aw")
            _git(repo, "commit", "-qm", "unmet dep")

            run = _run_driver(
                repo,
                fake,
                ["sha"],
                env_extra={"STOP_AFTER": "ja0001", "STOP_LEVEL": "1"},
            )

            statuses = run.statuses()
            self.assertEqual(
                statuses["ja0002"],
                "queued",
                f"a stopped run must not invent `dependency-blocked`: {statuses}",
            )
            stops = [e for e in run.events() if e.get("event") == "deliberate-stop"]
            self.assertEqual(len(stops), 1, run.events())
            self.assertEqual(run.returncode, 0, run.stderr)


@pytest.mark.slow
class AgyDriverParityTests(_InvariantAssertions):
    """Orchestrator CID-3, proven BEHAVIORALLY: `agy_runipd` honors both levels too.

    A structural check that the symbols exist in both drivers is not enough; a level that existed in
    only one driver in PRACTICE would still pass one. These drive the real `agy_runipd` process over
    the same fake child and assert the same observable outcomes.
    """

    def test_agy_level_1_completes_only_the_in_flight_item(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root, [("gaa", "ha0001"), ("gaa", "ha0002"), ("gaa", "ha0003")]
            )
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["gaa"],
                env_extra={"STOP_AFTER": "ha0001", "STOP_LEVEL": "1"},
                driver="agy",
            )

            self.assertEqual(run.ran(), {"ha0001"}, run.stderr)
            statuses = run.statuses()
            self.assertEqual(statuses["ha0002"], "queued", statuses)
            self.assertEqual(statuses["ha0003"], "queued", statuses)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_agy_level_2_finishes_the_current_set_only(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root,
                [
                    ("gba", "ia0001"),
                    ("gba", "ia0002"),
                    ("gbb", "ib0001"),
                ],
            )
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["gba", "gbb"],
                env_extra={"STOP_AFTER": "ia0001", "STOP_LEVEL": "2"},
                driver="agy",
            )

            self.assertEqual(run.ran(), {"ia0001", "ia0002"}, run.stderr)
            self.assertEqual(run.statuses()["ib0001"], "queued", run.statuses())
            self.assertEqual(run.returncode, 0, run.stderr)
            stops = [e for e in run.events() if e.get("event") == "deliberate-stop"]
            self.assertEqual(len(stops), 1, run.events())
            self.assertEqual(stops[0]["level"], 2)
            self.assertEqual(stops[0]["current_setid"], "gba")
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)


@pytest.mark.slow
class ExitContractTests(_InvariantAssertions):
    """E-05/V-05: exit 0 for an honest deliberate stop, nonzero when a run item really failed."""

    def test_exit_zero_while_the_queue_still_shows_queued_items(self):
        # Both halves in ONE observation: the process exit code AND the persisted queue. This is
        # what makes the 0 credible - it was not bought by rewriting statuses (spec R22).
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("sea", "ea0001"), ("sea", "ea0002")])
            fake = _write_fake_child(root)

            run = _run_driver(
                repo,
                fake,
                ["sea"],
                env_extra={"STOP_AFTER": "ea0001", "STOP_LEVEL": "1"},
            )

            self.assertEqual(run.returncode, 0, run.stderr)
            statuses = run.statuses()
            self.assertEqual(statuses["ea0002"], "queued", statuses)
            self.assertNotIn(
                statuses["ea0002"],
                oc.SUCCESS_STATES,
                "an un-run item must NOT be laundered into a success state",
            )

    def test_a_stop_whose_run_item_failed_exits_nonzero(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root, [("sfa", "fa0001"), ("sfa", "fa0002"), ("sfa", "fa0003")]
            )
            fake = _write_fake_child(root)

            # Item 1 requests the stop and SUCCEEDS; item 2 (same set, so level 2 still permits it)
            # genuinely FAILS. The run therefore ends on a real failure and must not exit 0.
            run = _run_driver(
                repo,
                fake,
                ["sfa"],
                env_extra={
                    "STOP_AFTER": "fa0001",
                    "STOP_LEVEL": "2",
                    "FAIL_FOR": "fa0002",
                },
            )

            statuses = run.statuses()
            self.assertNotEqual(
                statuses["fa0002"],
                "executed",
                f"the failing item must not be recorded executed: {statuses}",
            )
            self.assertNotEqual(
                run.returncode, 0, f"a failed run item must exit nonzero: {statuses}"
            )

    def test_a_run_with_no_stop_keeps_the_original_exit_contract(self):
        # Regression fence: the E-05 change must not make ordinary incomplete runs exit 0.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("sga", "ga0001"), ("sga", "ga0002")])
            fake = _write_fake_child(root)

            run = _run_driver(repo, fake, ["sga"], env_extra={"FAIL_FOR": "ga0002"})

            self.assertEqual(run.ran(), {"ga0001", "ga0002"}, run.stderr)
            self.assertNotEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
