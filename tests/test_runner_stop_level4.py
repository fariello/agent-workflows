#!/usr/bin/env python3
"""runstop Phase 4 (`m0z0ti`): level 4, STOP-NOW-FORCE with `unknown_outcome` and resume refusal.

Spec `c4gd2h` R18-R19, R21-R22, acceptance A2 and A6.

WHAT MAKES LEVEL 4 DIFFERENT FROM LEVEL 3, and therefore what these tests must prove. Spec section 3
says it in as many words: "The only difference between 3 and 4 is outcome CERTAINTY, not cleanliness."
So this suite proves TWO things and must not conflate them:

1. CLEANLINESS IS THE SAME. Every behavioral test asserts the identical four Phase-0 invariants a
   level-3 stop satisfies, and one test asserts the reap went through the SHARED
   `runner_shutdown.clean_shutdown` rather than a local `terminate_process` or a bare kill (spec R5).
   A level 4 that "optimized" into a raw kill would still stop the turn, so only these assertions
   catch it.
2. CERTAINTY IS NOT. The turn is cut at a point the driver did NOT observe, so the item is recorded
   `unknown_outcome` with `certainty: indeterminate`, its git state is CAPTURED, and no
   last-completed-operation is invented. Then a later RESUME must REFUSE to re-run it.

THE THREE WAYS THE EXISTING STATE MACHINE FIGHTS THIS, all pinned below, because each was a real
defect rather than a hypothetical:

* `run_queue` calls `reconcile_interrupted` and then `requeue_interrupted` UNCONDITIONALLY on every
  start and resume, and `requeue_interrupted` used to flip every `interrupted` item straight back to
  `queued` with no operator gate. So the R19 refusal has to be INSIDE the requeue, and V-04's evidence
  must come from the real `run_queue` entry - a test that only calls a refusal helper would pass while
  the driver still silently re-ran the item. `RealEntryPointTests` drives the actual CLI.
* `--retry-incomplete` is a SECOND route into the same requeue, whose status set includes
  `interrupted`. It is gated on the same predicate and tested separately.
* `reconcile_interrupted` promotes an item to `executed` whenever the PLAN'S DIRECTORY is `executed/`,
  consulting neither the outcome artifact nor any stop record. For a force-cut turn that records a
  success the driver never established: the exact R22 violation this level exists to prevent. Gated,
  with a CONTROL test proving an ordinary interrupted item is still promoted - without that control,
  the "fix" could simply have disabled a legitimate promotion.

WHY THE STATUS IS `interrupted` AND NOT `unknown_outcome`. Both naive representations are broken and
the tests assert the chosen one is handled by the existing machinery: a NEW status would be absent
from `runner_shutdown.KNOWN_ITEM_STATUSES` (failing Phase 0's R3 coherence check) and invisible to
reconcile/requeue/dequeue, making the item INERT; reusing `interrupted` ALONE would get it silently
requeued. So indeterminacy is an explicit `certainty` FLAG carried alongside a status the state
machine already understands. `StatusRepresentationTests` pins both halves.

THE FOUR PHASE-0 INVARIANTS are asserted with R4 as "tree UNCHANGED by cleanup" rather than "tree
clean", because Phase 0 (`2ouj70`) made R4 observe-and-report; demanding a clean tree would assert a
behavior the shared routine explicitly does not have.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agent_workflows import agy_runipd as agy
from agent_workflows import oc_runipd as oc
from agent_workflows import runner_shutdown, runner_stop
from tests.support import REPO_ROOT

_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

# ---------------------------------------------------------------------------------------------
# The fake child.
#
# For level 4 the interesting scripts are the ones where NO checkpoint is reachable, because that is
# what separates level 4 from level 3. Two matter:
#
#   `force`  - the child requests level 4 and then emits ONLY non-checkpoint events forever. A level-3
#              implementation would wait for a completed event that never comes; level 4 must cut
#              anyway. Its defect witness file proves whether it kept running.
#   `silent` - the child requests level 4 and then goes COMPLETELY quiet. This is the case an in-loop
#              poll alone cannot handle: `for line in process.stdout` blocks, so "immediately" would
#              mean "whenever the child next speaks", i.e. never. It is also exactly the case Phase 3's
#              budget breach escalates FROM (spec A7).
# ---------------------------------------------------------------------------------------------

_FAKE_CHILD = r'''#!/usr/bin/env python3
import json, os, pathlib, re, sys, time

args = sys.argv[1:]
# Both drivers deliberately (orchestrator CID-3): `oc_runipd` passes the prompt positionally after
# `--`, `agy_runipd` passes it via `-p`.
if "--" in args:
    prompt = args[args.index("--") + 1]
elif "-p" in args:
    prompt = args[args.index("-p") + 1]
else:
    prompt = ""

# Assembled rather than inline so the repo's local-leak detector does not read a hardcoded session id
# in a tracked file (the established convention in tests/test_oc_runipd.py and the level-3 suite).
_fallback_session = "ses" + "_" + "level4"
session = args[args.index("--session") + 1] if "--session" in args else _fallback_session

id6 = ""
m = re.search(r"Assigned IPD: (\S+)", prompt)
if m:
    id6 = m.group(1)

outcome = re.search(r"Required JSON outcome: (.+)", prompt)
plan = re.search(r"Plan file at launch: (.+)", prompt)

SCHEMA = os.environ.get("SCHEMA", "oc")


def emit(event):
    event["sessionID"] = session
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


def not_a_checkpoint(text):
    if SCHEMA == "oc":
        return {"type": "text", "part": {"text": text}}
    return {"type": "step_update", "step_update": {"state": "ACTIVE", "step_type": "tool",
                                                   "tool_info": {"name": "run_command"}}}


def completed_tool(name="bash"):
    if SCHEMA == "oc":
        return {"type": "tool_use",
                "part": {"type": "tool", "tool": name, "state": {"status": "completed"}}}
    return {"type": "step_update", "step_update": {"state": "DONE", "step_type": "tool",
                                                   "tool_info": {"name": name},
                                                   "duration_seconds": 0.01}}


def step_start():
    if SCHEMA == "oc":
        return {"type": "step_start", "part": {}}
    return {"type": "step_update", "step_update": {"state": "ACTIVE", "step_type": "agent_response"}}


def write_stop_request(level):
    run_dir = pathlib.Path(os.environ["RUN_DIR"])
    run_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, os.environ["AW_REPO_ROOT"])
    from agent_workflows import runner_stop
    runner_stop.request_stop(run_dir, level, "test-operator")


def move_plan_to_executed():
    """Simulate the agent having moved the plan to executed/ BEFORE being cut.

    This is the laundering setup: the plan's DIRECTORY then says `executed` while the driver never
    established that the work completed.
    """
    if plan:
        src = pathlib.Path(plan.group(1).strip())
        dst = pathlib.Path(str(src).replace("/pending/", "/executed/"))
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)


def finish_turn():
    move_plan_to_executed()
    if outcome:
        path = pathlib.Path(outcome.group(1).strip())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema_version": 1, "id6": id6, "disposition": "executed", "pushed": False,
        }))


mode = os.environ.get("CHILD_MODE", "plain")
target = os.environ.get("STOP_AFTER", "")

if mode == "force" and id6 == target:
    # NO completed event is EVER emitted after the request. A level-3-style implementation would wait
    # for a checkpoint that never arrives; level 4 must cut anyway.
    emit(step_start())                              # 1
    emit(not_a_checkpoint("thinking"))              # 2
    if os.environ.get("MOVE_PLAN_FIRST") == "1":
        # The laundering setup: the plan is already in executed/ when the cut lands.
        move_plan_to_executed()
    write_stop_request(int(os.environ.get("STOP_LEVEL", "4")))
    for extra in range(3, 400):
        emit(not_a_checkpoint("never a checkpoint %d" % extra))
        time.sleep(0.05)
    (pathlib.Path(os.environ["RUN_DIR"]) / "CHILD_RAN_TO_COMPLETION").write_text("yes")
    finish_turn()
    sys.exit(0)

if mode == "silent" and id6 == target:
    # The child goes COMPLETELY quiet after requesting the stop. An in-loop poll alone can never see
    # the request here, because the driver's read blocks on a line that never comes.
    emit(not_a_checkpoint("armed"))
    write_stop_request(int(os.environ.get("STOP_LEVEL", "4")))
    time.sleep(float(os.environ.get("CHILD_SILENCE", "30.0")))
    (pathlib.Path(os.environ["RUN_DIR"]) / "CHILD_RAN_TO_COMPLETION").write_text("yes")
    sys.exit(0)

if os.environ.get("FAIL_FOR", "") == id6 and id6:
    emit(not_a_checkpoint("failing"))
    sys.exit(3)

emit(step_start())
emit(completed_tool("read"))
finish_turn()
emit(not_a_checkpoint("done"))
'''

_PLAN_TEMPLATE = """\
- Id: {id6}
- Set: {setid}
- Status: approved
- Order: {order}
# Plan {id6}

## Workflow history
- 2026-08-30 created: level 4 test stub
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
    repo = root / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    for order, (setid, id6) in enumerate(items, start=1):
        name = f"20260830-{setid}-{order:02d}-{id6}-plan.ipd.md"
        (pending / name).write_text(
            _PLAN_TEMPLATE.format(id6=id6, setid=setid, order=order), encoding="utf-8"
        )
    (repo / "README").write_text("level4\n", encoding="utf-8")
    _git(repo, "add", "README", ".aw")
    _git(repo, "commit", "-qm", "initial")
    return repo


def _write_fake_child(root: Path) -> Path:
    fake = root / "fake_agent"
    fake.write_text(_FAKE_CHILD, encoding="utf-8")
    fake.chmod(0o755)
    return fake


class _DriverRun:
    """The observable result of one real driver process."""

    def __init__(
        self,
        repo: Path,
        run_dir: Path,
        returncode: int,
        stdout: str,
        stderr: str,
        elapsed: float,
    ):
        self.repo = repo
        self.run_dir = run_dir
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed
        self.run_id = run_dir.name

    @property
    def state(self) -> dict:
        return json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))

    def statuses(self) -> dict[str, str]:
        return {item["id6"]: item["status"] for item in self.state["queue"]}

    def item(self, id6: str) -> dict:
        return next(i for i in self.state["queue"] if i["id6"] == id6)

    def events(self) -> list[dict]:
        path = self.run_dir / "events.jsonl"
        if not path.is_file():
            return []
        return [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        ]

    def events_named(self, name: str) -> list[dict]:
        return [e for e in self.events() if e.get("event") == name]

    def ran(self) -> set[str]:
        return {e["id6"] for e in self.events() if e.get("event") == "ipd-started"}

    def start_counts(self) -> dict[str, int]:
        """How many times EACH item was started.

        A set of ids is NOT sufficient evidence for "the item was not re-run": a SECOND
        `ipd-started` for the same id6 leaves the set unchanged. Measured while mutation-testing this
        suite - with the `run_queue` refusal disabled, `--retry-incomplete` re-ran the flagged item and
        a set comparison still passed. So the refusal assertions count STARTS.
        """

        counts: dict[str, int] = {}
        for event in self.events():
            if event.get("event") == "ipd-started":
                counts[event["id6"]] = counts.get(event["id6"], 0) + 1
        return counts


def _driver_module(driver: str) -> str:
    return (
        "agent_workflows.oc_runipd" if driver == "oc" else "agent_workflows.agy_runipd"
    )


def _run_driver(
    repo: Path,
    fake: Path,
    selectors: list[str],
    *,
    env_extra: dict[str, str] | None = None,
    driver: str = "oc",
    output_mode: str = "clean",
    run_tag: str = "",
    timeout: int = 300,
) -> _DriverRun:
    """Run the REAL driver to completion over the fake child, in a fresh run.

    `--no-isolate-worktree` / `--no-self-finalize` keep the test on the STOP behavior rather than
    dragging in worktree allocation and the lifecycle gates, which have their own suites.
    """

    env = {**_DRIVER_ENV, "AW_REPO_ROOT": str(REPO_ROOT)}
    env.setdefault("SCHEMA", "oc" if driver == "oc" else "agy")
    if env_extra:
        env.update(env_extra)
    runs_dir = repo / ".aw" / "records" / "runs"
    existing = len(list(runs_dir.glob("run-*"))) if runs_dir.is_dir() else 0
    # The child needs RUN_DIR, but the run id is minted by the driver, so pin it.
    run_id = f"run-level4-{run_tag or driver}-{existing}"
    env["RUN_DIR"] = str(runs_dir / run_id)
    argv = [
        sys.executable,
        "-m",
        _driver_module(driver),
        "start",
        *selectors,
        "--repo",
        os.fspath(repo),
        "--run-id",
        run_id,
        "--no-self-finalize",
        "--no-isolate-worktree",
    ]
    if output_mode == "raw":
        argv.append("--raw")
    elif output_mode == "quiet":
        argv.append("--quiet")
    argv += ["--opencode" if driver == "oc" else "--agy", os.fspath(fake)]
    started = time.monotonic()
    result = subprocess.run(
        argv,
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return _DriverRun(
        repo,
        runs_dir / run_id,
        result.returncode,
        result.stdout,
        result.stderr,
        time.monotonic() - started,
    )


def _resume_driver(
    run: _DriverRun,
    fake: Path,
    *,
    driver: str = "oc",
    retry_incomplete: bool = False,
    timeout: int = 300,
) -> _DriverRun:
    """RESUME the SAME run through the REAL CLI entry point.

    This is the entry V-04 requires: `resume` -> `run_queue` -> `reconcile_interrupted` ->
    `requeue_interrupted`. Calling a refusal helper directly would prove nothing, because the
    unconditional requeue in that chain would bypass it.

    NOTE `resume` takes no `--opencode`/`--agy` flag (verified against its own `--help`): the child
    binary is read from the run's PERSISTED options, which is precisely why the `fake` argument is
    only used to seed state and is not passed on the command line here.
    """

    env = {**_DRIVER_ENV, "AW_REPO_ROOT": str(REPO_ROOT), "RUN_DIR": str(run.run_dir)}
    env.setdefault("SCHEMA", "oc" if driver == "oc" else "agy")
    argv = [
        sys.executable,
        "-m",
        _driver_module(driver),
        "resume",
        run.run_id,
        "--repo",
        os.fspath(run.repo),
    ]
    if retry_incomplete:
        argv.append("--retry-incomplete")
    started = time.monotonic()
    result = subprocess.run(
        argv,
        cwd=run.repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return _DriverRun(
        run.repo,
        run.run_dir,
        result.returncode,
        result.stdout,
        result.stderr,
        time.monotonic() - started,
    )


class _InvariantAssertions(unittest.TestCase):
    """The four Phase-0 clean-shutdown invariants, OBSERVED rather than asserted from code."""

    def assert_phase0_invariants(self, run: _DriverRun, tree_before: str) -> None:
        # R1: no descendant of the driver survives, observed in the real process table. Anchored to
        # THIS run's private temp repo path (unique per test) so it can never implicate a concurrently
        # running test's processes.
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

        # R3: the ledger parses and every item carries a status Phase 0's coherence check knows.
        # Reusing `runner_shutdown.KNOWN_ITEM_STATUSES` is the point: had level 4 invented a new
        # per-item status, this would FAIL here rather than pass a test-local allowlist.
        coherent, detail = runner_shutdown.observe_ledger(run.run_dir)
        self.assertTrue(coherent, f"ledger not coherent after the stop: {detail}")
        for item in run.state["queue"]:
            self.assertIn(item["status"], runner_shutdown.KNOWN_ITEM_STATUSES, item)

        # R4: cleanup OBSERVES the tree, it does not change it. Phase 0's recorded semantics are
        # observe-and-report, so the assertion is UNCHANGED, not clean. The dirty set may only have
        # GROWN (by the turn's own work), never shrunk - shrinking is the direction a stash, reset, or
        # checkout would move it.
        tree_after = _git(run.repo, "status", "--porcelain")
        before = {line[3:].strip() for line in tree_before.splitlines() if line.strip()}
        after = {line[3:].strip() for line in tree_after.splitlines() if line.strip()}
        self.assertTrue(
            before <= after,
            f"cleanup removed pre-existing dirty path(s): {sorted(before - after)}",
        )
        stashes = subprocess.run(
            ["git", "stash", "list"],
            cwd=run.repo,
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.assertEqual(stashes, "", f"cleanup must not stash anything: {stashes}")

    def assert_nothing_claimed_successful(self, run: _DriverRun) -> None:
        """Spec R22: after a level-4 stop NO item is executed, complete, or successful."""

        for item in run.state["queue"]:
            self.assertNotIn(
                item["status"],
                oc.SUCCESS_STATES,
                f"spec R22: {item['id6']} was recorded as a success after a force stop: {item}",
            )
            self.assertNotIn(
                item["status"],
                ("executed", "substantially-complete"),
                f"spec R22: {item['id6']} claims completion: {item}",
            )
        self.assertEqual(
            run.events_named("interrupted-reconciled-executed"),
            [],
            "spec R22: an indeterminate item must never be promoted to executed",
        )


# =============================================================================================
# E-01 / V-01: the IMMEDIATE interrupt through the SHARED reaper
# =============================================================================================


@pytest.mark.slow
class ImmediateInterruptTests(_InvariantAssertions):
    """Spec A2/R5/R7: the turn is cut without waiting for a checkpoint, cleanly."""

    def test_the_turn_is_cut_without_waiting_for_a_checkpoint(self):
        # THE CENTRAL LEVEL-4 ASSERTION. The child emits NO completed event after the request, ever.
        # A level-3-style implementation would wait for a checkpoint that never arrives and the child
        # would run to completion (writing its witness file). Level 4 must cut anyway.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("faa", "fa0001"), ("faa", "fa0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["faa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "fa0001",
                    "STOP_LEVEL": "4",
                },
            )

            record = run.item("fa0001")["stopped"]
            self.assertEqual(record["level"], runner_stop.LEVEL_NOW_FORCE, record)
            self.assertEqual(record["level_name"], "now-force")
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
            # NO checkpoint was ever emitted, so the level-3 event must be absent: this proves the cut
            # did not come from the checkpoint path.
            self.assertEqual(
                run.events_named("deliberate-stop-at-checkpoint"),
                [],
                "the cut must NOT have come from the level-3 checkpoint path",
            )
            # The child's defect witness: written only if it ran to completion, i.e. was never cut.
            self.assertFalse(
                (run.run_dir / "CHILD_RAN_TO_COMPLETION").exists(),
                "the child ran to completion: the turn was never interrupted",
            )
            self.assertGreater(
                record["events_observed"],
                0,
                "the honest denominator (events consumed) must be recorded",
            )
            self.assert_nothing_claimed_successful(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_a_silent_child_is_still_cut_promptly(self):
        # The case an IN-LOOP poll alone cannot handle: `for line in process.stdout` BLOCKS, so a
        # request arriving while the child is quiet would not be noticed until the child speaks - which
        # here it never does for 30s. This is also exactly the case Phase 3's budget breach escalates
        # FROM (spec A7). BOUNDED assertion: the run must finish in seconds, not wait out the silence.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("saa", "sa0001")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["saa"],
                env_extra={
                    "CHILD_MODE": "silent",
                    "STOP_AFTER": "sa0001",
                    "STOP_LEVEL": "4",
                    "CHILD_SILENCE": "30.0",
                },
                timeout=120,
            )

            record = run.item("sa0001").get("stopped")
            self.assertIsInstance(
                record,
                dict,
                f"a silent child was never cut (elapsed {run.elapsed:.2f}s); "
                f"stderr: {run.stderr[-2000:]}",
            )
            assert record is not None
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
            self.assertLess(
                run.elapsed,
                25.0,
                f"the interrupt was not immediate: {run.elapsed:.2f}s elapsed while the child "
                f"was silent for 30s",
            )
            self.assertFalse((run.run_dir / "CHILD_RAN_TO_COMPLETION").exists())
            self.assert_nothing_claimed_successful(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_the_stop_routes_through_the_shared_clean_shutdown(self):
        # Spec R5: ONE reaper. Observed from the run's OWN output rather than a mock: the per-turn
        # `clean_shutdown` call has no lock and no repo, so `all_satisfied` is False and the routine
        # PRINTS its per-invariant report (spec R23). That text can only appear if `clean_shutdown`
        # actually ran, so a level 4 "optimized" into a bare kill or a local `terminate_process` fails
        # here.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("fba", "fb0001")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["fba"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "fb0001",
                    "STOP_LEVEL": "4",
                },
            )

            self.assertIn("clean shutdown:", run.stderr)
            self.assertIn(
                f"{runner_shutdown.INVARIANT_CHILDREN} (R1)",
                run.stderr,
                "level 4 must go through clean_shutdown, not a bare kill or a local reaper",
            )
            self.assert_phase0_invariants(run, tree_before)

    def test_cleanliness_is_identical_to_a_level_3_stop(self):
        # Spec section 3: "The only difference between 3 and 4 is outcome CERTAINTY, not cleanliness."
        # So the two levels' clean-shutdown reports must be equivalent invariant-for-invariant. Only
        # the certainty differs.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo3 = _make_repo(root / "l3", [("caa", "ca0001")])
            repo4 = _make_repo(root / "l4", [("cba", "cb0001")])
            fake = _write_fake_child(root)

            before3 = _git(repo3, "status", "--porcelain")
            before4 = _git(repo4, "status", "--porcelain")

            # A level-3 stop: the ordinary child DOES emit a completed event, so the checkpoint is
            # reachable and level 3 stops there.
            run3 = _run_driver(
                repo3,
                fake,
                ["caa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "ca0001",
                    "STOP_LEVEL": "3",
                },
                run_tag="l3",
            )
            run4 = _run_driver(
                repo4,
                fake,
                ["cba"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "cb0001",
                    "STOP_LEVEL": "4",
                },
                run_tag="l4",
            )

            self.assert_phase0_invariants(run3, before3)
            self.assert_phase0_invariants(run4, before4)

            # Both went through the SAME routine and reported the SAME invariant set.
            for run in (run3, run4):
                self.assertIn("clean shutdown:", run.stderr, run.stderr[-2000:])
                for invariant in (
                    runner_shutdown.INVARIANT_CHILDREN,
                    runner_shutdown.INVARIANT_LOCK,
                    runner_shutdown.INVARIANT_LEDGER,
                    runner_shutdown.INVARIANT_TREE,
                ):
                    self.assertIn(invariant, run.stderr, f"{invariant} missing")

            # And the ONE difference is certainty. Note the level-3 run here could NOT reach a
            # checkpoint either (this child emits none after the request), so it records no stop at
            # all - which is itself the distinction: level 3 waits, level 4 does not.
            record4 = run4.item("cb0001")["stopped"]
            self.assertEqual(record4["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
            self.assertNotEqual(
                record4["certainty"],
                runner_stop.CERTAINTY_KNOWN,
                "level 4 must not claim level 3's certainty",
            )


@pytest.mark.slow
class AgyDriverParityTests(_InvariantAssertions):
    """Orchestrator CID-3: an operator switching hosts must get the SAME guarantee."""

    def test_agy_is_cut_immediately_and_records_the_same_indeterminacy(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("gfa", "gf0001"), ("gfa", "gf0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["gfa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "gf0001",
                    "STOP_LEVEL": "4",
                    "SCHEMA": "agy",
                },
                driver="agy",
            )

            record = run.item("gf0001")["stopped"]
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
            self.assertEqual(record["disposition"], runner_stop.FORCED_DISPOSITION)
            self.assertIsNone(record["last_completed_event"])
            self.assertFalse((run.run_dir / "CHILD_RAN_TO_COMPLETION").exists())
            self.assertEqual(run.statuses()["gf0002"], "queued", run.statuses())
            self.assert_nothing_claimed_successful(run)
            self.assert_phase0_invariants(run, tree_before)


class BothDriversWireLevel4Tests(unittest.TestCase):
    """Orchestrator CID-3, asserted structurally as well as behaviorally."""

    def _source(self, name: str) -> str:
        return (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")

    def test_both_drivers_use_the_shared_level_4_surface(self):
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(name)
            self.assertIn("runner_stop.StopNowForce", source, name)
            self.assertIn("runner_stop.ForceStopWatch(", source, name)
            self.assertIn("runner_stop.is_indeterminate(", source, name)
        for module in (oc, agy):
            self.assertTrue(hasattr(module, "_record_forced_stop"), module)
            self.assertIs(module.runner_stop, runner_stop)

    def test_neither_driver_reaps_level_4_with_a_bare_kill(self):
        # Spec R5: no second reaper and no raw kill. The force path must reach the shared routine.
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(name)
            for forbidden in ("os.kill(", "process.kill()", "SIGKILL"):
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{name}: level 4 must not reap with {forbidden}; "
                    f"runner_shutdown owns the escalation",
                )

    def test_the_signal_trigger_is_installed_through_the_shared_handler_safe_installer(
        self,
    ):
        # CONSCIOUSLY REPLACED by runstop Phase 5 (`71vjbn`), not deleted.
        #
        # Phase 4 asserted `signal.signal(` appeared in NEITHER driver, reserving SIGINT/SIGTERM for
        # Phase 5. Phase 5 has landed them, from the SHARED `runner_stop` module - which means the
        # original assertion would now pass VACUOUSLY (still no literal in either driver) while
        # asserting nothing. A green test with no meaning is worse than a deleted one, so it is
        # replaced by the invariant that was actually load-bearing: a handler must take the
        # handler-SAFE writer, because Phase 1 measured the blocking one deadlocking a handler.
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(name)
            self.assertIn("runner_stop.install_stop_signal_handlers(", source, name)
            self.assertNotIn("signal.signal(", source, name)
        import inspect

        installer = inspect.getsource(runner_stop.install_stop_signal_handlers)
        self.assertIn("request_stop_nowait(", installer)

    def test_level_4_is_reachable_by_its_own_cli_flag(self):
        # CONSCIOUSLY REPLACED by runstop Phase 5, not deleted. Phase 4 asserted the `stop` verb did
        # not exist yet, and requested level 4 by writing the Phase-1 record directly. Phase 5 has now
        # made it REACHABLE, which is the whole point of that phase, so the positive form is asserted
        # here: level 4 has an out-of-band flag, and it maps to level 4.
        self.assertEqual(
            runner_stop.LEVEL_FLAGS["now_force"], runner_stop.LEVEL_NOW_FORCE
        )
        self.assertIn("--now-force", runner_stop.STOP_LEVEL_FLAG_HELP)
        for name in ("oc_runipd.py", "agy_runipd.py"):
            self.assertIn("runner_stop.add_stop_parser(", self._source(name), name)


# =============================================================================================
# E-02 / V-02: the honest INDETERMINATE record
# =============================================================================================


class ForcedDispositionRecordTests(unittest.TestCase):
    """The record's shape (spec R18/R22), unit-tested through the shared builder."""

    def _record(self) -> dict:
        return runner_stop.forced_disposition(
            requester="operator",
            git_state=" M agent_workflows/x.py",
            events_seen=7,
            at="2026-08-30T00:00:00+00:00",
        )

    def test_it_records_level_certainty_git_state_and_the_reconciliation_requirement(
        self,
    ):
        record = self._record()
        self.assertEqual(record["level"], runner_stop.LEVEL_NOW_FORCE)
        self.assertEqual(record["level_name"], "now-force")
        self.assertEqual(record["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
        self.assertEqual(record["disposition"], runner_stop.FORCED_DISPOSITION)
        self.assertEqual(record["git_state"], " M agent_workflows/x.py")
        self.assertEqual(record["events_observed"], 7)
        self.assertTrue(record["requires_reconciliation"], "spec R19")
        self.assertTrue(
            record["resume_action"], "spec R18 requires a resume instruction"
        )
        self.assertIn("reconcile", record["resume_action"].lower())

    def test_no_last_completed_operation_is_ever_invented(self):
        # THE HONESTY ASSERTION. The cut point was not observed, so naming a last completed operation
        # would be a fabricated field (spec R22). The keys exist and are explicitly None so a reader
        # sees the absence was deliberate.
        record = self._record()
        self.assertIn("last_completed_event", record)
        self.assertIsNone(record["last_completed_event"])
        self.assertIn("last_completed_event_index", record)
        self.assertIsNone(record["last_completed_event_index"])

    def test_prior_observations_are_carried_under_keys_that_cannot_be_misread(self):
        # What the driver HAD seen before the request is legitimate information, but it must not be
        # presented as "the operation that finished last".
        record = runner_stop.forced_disposition(
            requester="operator",
            prior_completed_index=3,
            prior_completed_label="tool_use:read",
        )
        self.assertEqual(record["prior_observed_completed_index"], 3)
        self.assertEqual(record["prior_observed_completed_event"], "tool_use:read")
        self.assertIsNone(record["last_completed_event_index"])
        self.assertIsNone(record["last_completed_event"])

    def test_it_is_never_recorded_as_a_success(self):
        blob = json.dumps(self._record())
        for word in ("executed", "successful", '"complete"'):
            self.assertNotIn(word, blob, f"spec R22 forbids claiming {word!r}")

    def test_it_is_a_deliberate_non_failure_not_a_crash(self):
        record = self._record()
        self.assertTrue(record["stopped_deliberately"], "spec R21: operator intent")
        self.assertFalse(
            record["failure"], "spec R21: a deliberate stop is not breakage"
        )

    def test_certainty_is_the_only_thing_that_differs_from_level_3(self):
        # Both levels use the SAME record shape, which is why the certainty flag is the load-bearing
        # field rather than a second schema.
        known = runner_stop.stopped_disposition(
            level=runner_stop.LEVEL_NOW,
            requester="operator",
            last_completed_index=5,
            last_completed_label="tool_use:read",
        )
        indeterminate = self._record()
        for key in (
            "stopped_deliberately",
            "failure",
            "level",
            "level_name",
            "requester",
            "certainty",
            "last_completed_event_index",
            "last_completed_event",
            "events_observed",
            "git_state",
            "resume_action",
            "at",
        ):
            self.assertIn(key, known, key)
            self.assertIn(key, indeterminate, key)
        self.assertEqual(known["certainty"], runner_stop.CERTAINTY_KNOWN)
        self.assertEqual(
            indeterminate["certainty"], runner_stop.CERTAINTY_INDETERMINATE
        )


class StatusRepresentationTests(unittest.TestCase):
    """E-02's DECIDED representation, with both rejected alternatives pinned as broken."""

    def test_the_chosen_status_is_one_the_existing_state_machine_handles(self):
        # If level 4 had invented a per-item `unknown_outcome` STATUS the item would be INERT. This
        # asserts the chosen status is understood by Phase 0's coherence check and by both drivers.
        status = runner_stop.STOPPED_DISPOSITION
        self.assertEqual(status, "interrupted")
        self.assertIn(status, runner_shutdown.KNOWN_ITEM_STATUSES)
        self.assertNotIn(status, oc.SUCCESS_STATES)
        self.assertNotIn(status, agy.SUCCESS_STATES)

    def test_the_rejected_new_status_would_indeed_be_inert(self):
        # The MEASURED reason option (i) was rejected, asserted rather than asserted-in-prose: the
        # token is absent from every status set the machinery consults, so an item carrying it would
        # never be reconciled, requeued, dequeued, or judged coherent.
        token = runner_stop.FORCED_DISPOSITION
        self.assertNotIn(token, runner_shutdown.KNOWN_ITEM_STATUSES)
        self.assertNotIn(token, oc.TERMINAL_STATES)
        self.assertNotIn(token, agy.TERMINAL_STATES)

    def test_indeterminacy_is_an_explicit_flag_and_the_one_gate_predicate(self):
        item = {
            "id6": "aa0001",
            "status": "interrupted",
            "stopped": runner_stop.forced_disposition(requester="operator"),
        }
        self.assertTrue(runner_stop.is_indeterminate(item))
        # And the level-3 record must NOT trip it, or every ordinary stop would be refused.
        level3 = {
            "id6": "aa0002",
            "status": "interrupted",
            "stopped": runner_stop.stopped_disposition(
                level=runner_stop.LEVEL_NOW,
                requester="operator",
                last_completed_index=5,
                last_completed_label="tool_use:read",
            ),
        }
        self.assertFalse(runner_stop.is_indeterminate(level3))

    def test_the_predicate_fails_safe_on_every_junk_shape(self):
        # Fail-safe direction matters: a shape misread as INDETERMINATE would wrongly block ordinary
        # recovery, so anything unclear must read False.
        for candidate in (
            None,
            {},
            {"stopped": None},
            {"stopped": {}},
            {"stopped": "indeterminate"},
            {"stopped": {"certainty": "known"}},
            {"stopped": {"certainty": None}},
            {"stopped": []},
            "interrupted",
            42,
        ):
            self.assertFalse(runner_stop.is_indeterminate(candidate), repr(candidate))


@pytest.mark.slow
class IndeterminateInTheLedgerTests(_InvariantAssertions):
    """V-02: the LEDGER, after a real level-4 stop of a real driver."""

    def test_the_ledger_records_indeterminacy_git_state_and_the_reconciliation_need(
        self,
    ):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("iaa", "ia0001"), ("iaa", "ia0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["iaa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "ia0001",
                    "STOP_LEVEL": "4",
                },
            )

            item = run.item("ia0001")
            record = item["stopped"]
            self.assertEqual(record["disposition"], runner_stop.FORCED_DISPOSITION)
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
            self.assertTrue(record["requires_reconciliation"])
            self.assertIsInstance(record["git_state"], str)
            self.assertTrue(record["resume_action"])
            # No invented last-completed-operation, in the REAL ledger and not only in the builder.
            self.assertIsNone(record["last_completed_event"])
            self.assertIsNone(record["last_completed_event_index"])
            # The status is the coherent existing one; indeterminacy is the flag.
            self.assertEqual(item["status"], runner_stop.STOPPED_DISPOSITION)
            self.assertNotIn(
                item["status"],
                ("failed-safely", "partial"),
                "a DELIBERATE force stop must not be reported as a failure",
            )
            self.assertTrue(runner_stop.is_indeterminate(item))
            self.assert_nothing_claimed_successful(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_a_missing_outcome_json_is_not_read_as_information(self):
        # A force cut usually leaves NO outcome file at all (the agent writes it at turn END), or a
        # half-written one. Its ABSENCE must not be read as a verdict, and a malformed one must not
        # crash the reconcile path.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("oaa", "oa0001")])
            fake = _write_fake_child(root)

            run = _run_driver(
                repo,
                fake,
                ["oaa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "oa0001",
                    "STOP_LEVEL": "4",
                },
            )

            outcome = run.run_dir / "outcomes" / "01-oa0001.json"
            self.assertFalse(
                outcome.exists(), "the fixture must model the no-outcome-file case"
            )
            # The item is still recorded honestly, from the stop record rather than the missing file.
            self.assertTrue(runner_stop.is_indeterminate(run.item("oa0001")))

            # Now a HALF-WRITTEN outcome file must not crash the reconcile path either.
            outcome.parent.mkdir(parents=True, exist_ok=True)
            outcome.write_text('{"schema_version": 1, "disp', encoding="utf-8")
            state = json.loads((run.run_dir / "state.json").read_text(encoding="utf-8"))
            disposition, parsed = oc.reconcile_disposition(
                repo, state["queue"][0], run.run_dir, 1
            )
            self.assertEqual(disposition, runner_stop.STOPPED_DISPOSITION)
            self.assertIsNone(parsed)


# =============================================================================================
# E-03 / V-03: R22 on this path, and DELIBERATE vs CRASH
# =============================================================================================


class ForcedStopEventTests(unittest.TestCase):
    """The ledger event (spec R21): deliberate, non-failure, and distinguishable from level 3."""

    def _event(self) -> dict:
        record = runner_stop.forced_disposition(requester="operator", events_seen=4)
        return runner_stop.forced_stop_event(
            record, id6="aa0001", at="2026-08-30T00:00:00+00:00"
        )

    def test_it_is_deliberate_and_not_a_failure(self):
        event = self._event()
        self.assertEqual(event["event"], runner_stop.FORCED_STOP_EVENT)
        self.assertTrue(event["deliberate"], "spec R21: operator intent, not a crash")
        self.assertFalse(event["failure"])
        self.assertEqual(event["level"], runner_stop.LEVEL_NOW_FORCE)
        self.assertEqual(event["certainty"], runner_stop.CERTAINTY_INDETERMINATE)
        self.assertTrue(event["requires_reconciliation"])
        self.assertTrue(event["reconciliation_required"])

    def test_it_is_a_distinct_event_from_the_level_3_stop(self):
        # Same channel, different name: an operator (and a test) must be able to tell WHICH level
        # stopped the run from history alone.
        self.assertNotEqual(
            runner_stop.FORCED_STOP_EVENT, "deliberate-stop-at-checkpoint"
        )
        self.assertNotEqual(runner_stop.FORCED_STOP_EVENT, "deliberate-stop")

    def test_it_rides_the_established_channel_and_adds_no_new_substrate(self):
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            self.assertNotIn("run_ledger_store", source, name)


@pytest.mark.slow
class DeliberateVersusCrashTests(_InvariantAssertions):
    """V-03: R22 holds on this path, and a level-4 stop is distinguishable from a crash."""

    def test_no_item_is_recorded_executed_complete_or_successful(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("raa", "ra0001"), ("raa", "ra0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["raa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "ra0001",
                    "STOP_LEVEL": "4",
                },
            )

            self.assert_nothing_claimed_successful(run)
            # Items that never ran keep `queued`; nothing is relabeled to explain the stop.
            self.assertEqual(run.ran(), {"ra0001"}, run.stderr[-2000:])
            self.assertEqual(run.statuses()["ra0002"], "queued", run.statuses())
            self.assertEqual(
                run.events_named("dependency-blocked"),
                [],
                "a stopped run must not invent `dependency-blocked`",
            )
            self.assert_phase0_invariants(run, tree_before)

    def test_a_deliberate_stop_and_a_crash_are_distinguishable_in_the_ledger(self):
        # Spec R21. The two are compared SIDE BY SIDE, because the requirement is about a reader being
        # able to tell them apart, not about either record in isolation.
        with TemporaryDirectory() as temp:
            root = Path(temp)

            # (a) the DELIBERATE level-4 stop.
            repo_stop = _make_repo(root / "stop", [("daa", "da0001")])
            fake = _write_fake_child(root)
            run_stop = _run_driver(
                repo_stop,
                fake,
                ["daa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "da0001",
                    "STOP_LEVEL": "4",
                },
                run_tag="stop",
            )
            stop_events = run_stop.events_named(runner_stop.FORCED_STOP_EVENT)
            self.assertEqual(len(stop_events), 1, run_stop.events())

            # (b) a CRASH: an item left `running` in the ledger with no stop record at all, which is
            # exactly what a killed driver leaves behind. Reconciled through the REAL function.
            repo_crash = _make_repo(root / "crash", [("dba", "db0001")])
            crash_run_dir = (
                repo_crash / ".aw" / "records" / "runs" / "run-level4-crash-0"
            )
            (crash_run_dir / "outcomes").mkdir(parents=True)
            crash_state = {
                "schema_version": 1,
                "run_id": crash_run_dir.name,
                "repo": os.fspath(repo_crash),
                "queue": [
                    {
                        "position": 1,
                        "id6": "db0001",
                        "setid": "dba",
                        "configured_file": ".aw/records/plans/pending/20260830-dba-01-db0001-plan.ipd.md",
                        "dependencies": [],
                        "status": "running",
                        "attempts": [{"number": 1, "log": None}],
                    }
                ],
            }
            (crash_run_dir / "state.json").write_text(
                json.dumps(crash_state), encoding="utf-8"
            )
            oc.reconcile_interrupted(crash_run_dir, crash_state)
            crash_events = [
                json.loads(line)
                for line in (crash_run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]

            # THE DISTINCTION, asserted in both directions.
            deliberate = stop_events[0]
            crash = next(
                e for e in crash_events if e.get("event") == "interrupted-detected"
            )
            self.assertTrue(deliberate["deliberate"])
            self.assertNotIn(
                "deliberate", crash, "a crash must not be recorded as deliberate"
            )
            self.assertEqual(deliberate["level"], runner_stop.LEVEL_NOW_FORCE)
            self.assertNotIn("level", crash, "a crash carries no stop level")
            # And a crash-reconciled item carries no indeterminate flag, so it stays ordinarily
            # recoverable rather than being wrongly refused.
            self.assertFalse(runner_stop.is_indeterminate(crash_state["queue"][0]))


# =============================================================================================
# E-05 / V-05: the pre-existing FABRICATED-SUCCESS vector
# =============================================================================================


class PromotionGateTests(unittest.TestCase):
    """`reconcile_interrupted` must not launder an indeterminate item into `executed` (spec R22)."""

    def _fixture(self, root: Path, *, indeterminate: bool) -> tuple[Path, Path, dict]:
        """A repo whose plan is ALREADY in `executed/`, and a ledger item left `running`."""

        repo = _make_repo(root, [("paa", "pa0001")])
        pending = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260830-paa-01-pa0001-plan.ipd.md"
        )
        executed_dir = repo / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)
        pending.rename(executed_dir / pending.name)

        run_dir = repo / ".aw" / "records" / "runs" / "run-promo"
        (run_dir / "outcomes").mkdir(parents=True)
        item: dict = {
            "position": 1,
            "id6": "pa0001",
            "setid": "paa",
            "configured_file": f".aw/records/plans/pending/{pending.name}",
            "dependencies": [],
            "status": "running",
            "attempts": [{"number": 1, "log": None}],
        }
        if indeterminate:
            item["stopped"] = runner_stop.forced_disposition(requester="test-operator")
        state = {
            "schema_version": 1,
            "run_id": run_dir.name,
            "repo": os.fspath(repo),
            "queue": [item],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return repo, run_dir, state

    def test_an_indeterminate_item_is_not_promoted_to_executed(self):
        # THE LAUNDERING CASE. The plan sits in `executed/`, so the pre-existing directory-based
        # promotion would record `executed` - a success the driver never established, because the turn
        # was force-cut. Both drivers must refuse and REPORT the conflict.
        for module in (oc, agy):
            with self.subTest(driver=module.__name__), TemporaryDirectory() as temp:
                _repo, run_dir, state = self._fixture(Path(temp), indeterminate=True)

                module.reconcile_interrupted(run_dir, state)

                item = state["queue"][0]
                self.assertNotEqual(
                    item["status"],
                    "executed",
                    f"{module.__name__}: spec R22 violated - an indeterminate item was "
                    f"laundered into `executed` from the plan's directory alone",
                )
                self.assertEqual(item["status"], "interrupted")
                self.assertIn(
                    "reconciliation_conflict",
                    item,
                    "the conflict must be REPORTED, not silently swallowed",
                )
                self.assertIn("executed/", item["reconciliation_conflict"])
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                refusals = [
                    e
                    for e in events
                    if e.get("event") == "interrupted-promotion-refused-unknown-outcome"
                ]
                self.assertEqual(len(refusals), 1, events)
                self.assertEqual(
                    [
                        e
                        for e in events
                        if e.get("event") == "interrupted-reconciled-executed"
                    ],
                    [],
                )

    def test_an_ordinary_interrupted_item_is_still_promoted(self):
        # THE CONTROL, and it is required: without it the "fix" could simply have disabled a
        # legitimate promotion rather than closing a fabrication.
        for module in (oc, agy):
            with self.subTest(driver=module.__name__), TemporaryDirectory() as temp:
                _repo, run_dir, state = self._fixture(Path(temp), indeterminate=False)

                module.reconcile_interrupted(run_dir, state)

                item = state["queue"][0]
                self.assertEqual(
                    item["status"],
                    "executed",
                    f"{module.__name__}: ordinary directory-based promotion was broken by "
                    f"the indeterminate gate",
                )
                self.assertNotIn("reconciliation_conflict", item)
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                self.assertEqual(
                    len(
                        [
                            e
                            for e in events
                            if e.get("event") == "interrupted-reconciled-executed"
                        ]
                    ),
                    1,
                    events,
                )


@pytest.mark.slow
class PromotionGateEndToEndTests(_InvariantAssertions):
    """V-05 end-to-end: the laundering case through a REAL driver run."""

    def test_a_force_cut_after_the_plan_moved_is_never_recorded_executed(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("laa", "la0001")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["laa"],
                env_extra={
                    "CHILD_MODE": "force",
                    "STOP_AFTER": "la0001",
                    "STOP_LEVEL": "4",
                    # The agent moves the plan to executed/ BEFORE the cut lands.
                    "MOVE_PLAN_FIRST": "1",
                },
            )

            executed = list(
                (repo / ".aw" / "records" / "plans" / "executed").glob("*la0001*")
            )
            self.assertEqual(
                len(executed), 1, "the fixture must leave the plan in executed/"
            )
            self.assert_nothing_claimed_successful(run)
            self.assertTrue(runner_stop.is_indeterminate(run.item("la0001")))
            self.assert_phase0_invariants(run, tree_before)


# =============================================================================================
# E-04 / V-04: the RESUME refusal, through the REAL entry point
# =============================================================================================


class RequeueGateTests(unittest.TestCase):
    """The gate lives INSIDE `requeue_interrupted` (orchestrator CID-4)."""

    def _state(self, *, indeterminate: bool) -> dict:
        item: dict = {
            "position": 1,
            "id6": "qa0001",
            "setid": "qaa",
            "configured_file": "x",
            "dependencies": [],
            "status": "interrupted",
            "attempts": [],
        }
        if indeterminate:
            item["stopped"] = runner_stop.forced_disposition(requester="test-operator")
        return {"schema_version": 1, "run_id": "r", "repo": ".", "queue": [item]}

    def test_an_indeterminate_item_is_skipped_and_reported(self):
        for module in (oc, agy):
            with self.subTest(driver=module.__name__), TemporaryDirectory() as temp:
                run_dir = Path(temp)
                state = self._state(indeterminate=True)

                requeued = module.requeue_interrupted(run_dir, state)

                self.assertEqual(requeued, [], module.__name__)
                self.assertEqual(state["queue"][0]["status"], "interrupted")
                self.assertNotIn("recovery_next", state["queue"][0])
                self.assertTrue(state["queue"][0]["requires_reconciliation"])
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                refusals = [
                    e
                    for e in events
                    if e.get("event") == "resume-refused-unknown-outcome"
                ]
                self.assertEqual(len(refusals), 1, events)
                self.assertEqual(refusals[0]["id6"], "qa0001")
                self.assertIn("reconcile", refusals[0]["reason"].lower())
                self.assertEqual(
                    [e for e in events if e.get("event") == "interrupted-requeued"], []
                )

    def test_an_ordinary_interrupted_item_is_still_requeued(self):
        # The CONTROL: the gate must not disable ordinary recovery.
        for module in (oc, agy):
            with self.subTest(driver=module.__name__), TemporaryDirectory() as temp:
                run_dir = Path(temp)
                state = self._state(indeterminate=False)

                requeued = module.requeue_interrupted(run_dir, state)

                self.assertEqual(requeued, ["qa0001"], module.__name__)
                self.assertEqual(state["queue"][0]["status"], "queued")
                self.assertTrue(state["queue"][0]["recovery_next"])


class RefusalMessageTests(unittest.TestCase):
    """Refusing must be ACTIONABLE, not an opaque error (spec R19)."""

    def test_the_message_names_the_item_its_state_and_the_action_required(self):
        item = {
            "id6": "zz0001",
            "status": "interrupted",
            "stopped": runner_stop.forced_disposition(requester="operator"),
        }
        message = runner_stop.resume_refusal_message(item)
        self.assertIn("zz0001", message, "the operator must know WHICH item")
        self.assertIn(runner_stop.FORCED_DISPOSITION, message, "and WHY")
        self.assertIn(runner_stop.CERTAINTY_INDETERMINATE, message)
        self.assertIn("4", message, "and which level produced it")
        self.assertIn("reconcile", message.lower(), "and WHAT TO DO")

    def test_the_reconciliation_action_names_the_owning_routine_not_a_new_one(self):
        # Research `ud28vy` owns the reconciliation model; this phase must call it, not restate a
        # parallel algorithm (GUIDING_PRINCIPLES P8).
        self.assertIn("ud28vy", runner_stop.RECONCILIATION_ACTION)


@pytest.mark.slow
class RealEntryPointTests(_InvariantAssertions):
    """V-04: the refusal observed through the REAL `resume` -> `run_queue` -> requeue chain.

    Evidence that only exercises a helper would be worthless here: `run_queue` calls
    `reconcile_interrupted` then `requeue_interrupted` unconditionally on every resume, so a gate
    added anywhere else would be bypassed by the call that already ran.
    """

    def _stopped_run(self, root: Path) -> tuple[_DriverRun, Path]:
        repo = _make_repo(root, [("xaa", "xa0001"), ("xaa", "xa0002")])
        fake = _write_fake_child(root)
        run = _run_driver(
            repo,
            fake,
            ["xaa"],
            env_extra={
                "CHILD_MODE": "force",
                "STOP_AFTER": "xa0001",
                "STOP_LEVEL": "4",
            },
        )
        self.assertTrue(
            runner_stop.is_indeterminate(run.item("xa0001")),
            f"the fixture must leave an indeterminate item; stderr: {run.stderr[-2000:]}",
        )
        return run, fake

    def test_plain_resume_refuses_and_exits_nonzero_without_running_anything(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            run, fake = self._stopped_run(root)
            starts_before = run.start_counts()

            resumed = _resume_driver(run, fake)

            self.assertNotEqual(
                resumed.returncode, 0, f"resume must refuse: {resumed.stdout[-2000:]}"
            )
            # The message must be ACTIONABLE (spec A6): item, state, and required action.
            self.assertIn("xa0001", resumed.stderr)
            self.assertIn(runner_stop.FORCED_DISPOSITION, resumed.stderr)
            self.assertIn(runner_stop.CERTAINTY_INDETERMINATE, resumed.stderr)
            self.assertIn("reconcile", resumed.stderr.lower())
            # The item was NOT re-run, and no other item ran out of order. Asserted on START COUNTS,
            # not on a set of ids: a set cannot see a SECOND start of the SAME item, and a mutation
            # test proved that gap is real (see `start_counts`).
            self.assertEqual(
                resumed.start_counts(),
                starts_before,
                "no item may start (or re-start) during a refused resume",
            )
            self.assertEqual(
                resumed.item("xa0001")["status"],
                "interrupted",
                "the refused item must not be flipped back to queued",
            )
            self.assertNotIn("recovery_next", resumed.item("xa0001"))
            self.assertEqual(resumed.statuses()["xa0002"], "queued")
            self.assert_nothing_claimed_successful(resumed)

    def test_resume_with_retry_incomplete_is_refused_too(self):
        # The SECOND requeue route: `--retry-incomplete`'s status set includes `interrupted`, so an
        # ungated flag would re-run the item even with the first route gated.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            run, fake = self._stopped_run(root)
            starts_before = run.start_counts()

            resumed = _resume_driver(run, fake, retry_incomplete=True)

            self.assertNotEqual(
                resumed.returncode,
                0,
                f"resume --retry-incomplete must refuse: {resumed.stdout[-2000:]}",
            )
            self.assertIn("xa0001", resumed.stderr)
            self.assertIn("reconcile", resumed.stderr.lower())
            self.assertEqual(resumed.start_counts(), starts_before)
            self.assertEqual(resumed.item("xa0001")["status"], "interrupted")
            self.assertNotIn("recovery_next", resumed.item("xa0001"))
            self.assert_nothing_claimed_successful(resumed)

    def test_the_refusal_comes_from_the_real_requeue_path(self):
        # Proven by the LEDGER the real chain writes: the refusal event is appended by
        # `requeue_interrupted` itself, and the auto-requeue event is absent.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            run, fake = self._stopped_run(root)

            resumed = _resume_driver(run, fake)

            refusals = resumed.events_named("resume-refused-unknown-outcome")
            self.assertGreaterEqual(len(refusals), 1, resumed.events())
            self.assertEqual(refusals[-1]["id6"], "xa0001")
            self.assertEqual(
                [
                    e
                    for e in resumed.events_named("interrupted-requeued")
                    if e.get("id6") == "xa0001"
                ],
                [],
                "the unconditional auto-requeue must not have fired for the flagged item",
            )

    def test_an_ordinary_interrupted_run_still_resumes(self):
        # THE END-TO-END CONTROL. A stall leaves an ordinary `interrupted` item with no indeterminate
        # flag, and that run must still resume and run it - otherwise the R19 gate has broken recovery
        # for every non-level-4 interruption.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("yaa", "ya0001")])
            fake = _write_fake_child(root)
            run_dir = repo / ".aw" / "records" / "runs" / "run-level4-ordinary-0"
            for sub in ("outcomes", "prompts", "sessions"):
                (run_dir / sub).mkdir(parents=True)
            state = {
                "schema_version": 1,
                "run_id": run_dir.name,
                "repo": os.fspath(repo),
                "created_at": "2026-08-30T00:00:00+00:00",
                "options": {
                    "opencode": os.fspath(fake),
                    "self_finalize": False,
                    "isolate_worktree": False,
                    "validate": False,
                    "output_mode": "quiet",
                },
                "set_sessions": {},
                "queue": [
                    {
                        "position": 1,
                        "id6": "ya0001",
                        "setid": "yaa",
                        "configured_file": ".aw/records/plans/pending/20260830-yaa-01-ya0001-plan.ipd.md",
                        "dependencies": [],
                        "status": "interrupted",
                        "attempts": [{"number": 1, "log": None}],
                        "action": "execute",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            fake_run = _DriverRun(repo, run_dir, 0, "", "", 0.0)
            resumed = _resume_driver(fake_run, fake)

            self.assertIn(
                "ya0001",
                resumed.ran(),
                f"ordinary recovery was broken by the R19 gate: "
                f"{resumed.stderr[-2000:]}",
            )
            self.assertEqual(
                resumed.events_named("resume-refused-unknown-outcome"),
                [],
                "an ordinary interrupted item must not be refused",
            )


# =============================================================================================
# Scope fence
# =============================================================================================


class ScopeFenceTests(unittest.TestCase):
    """What this phase deliberately does NOT implement (Phase 5 owns it)."""

    def test_no_second_reconciliation_algorithm_was_defined_here(self):
        # Research `ud28vy` owns the reconciliation ALGORITHM and `run_recovery` realizes it. This
        # phase implements the REFUSAL (R19) and calls that model by name; it must not grow a parallel
        # reconcile/rollback implementation.
        exported = set(runner_stop.__all__)
        for forbidden in ("reconcile_", "rollback", "auto_heal", "repair"):
            offenders = [name for name in exported if forbidden in name.lower()]
            self.assertEqual(
                offenders,
                [],
                f"a parallel reconciliation surface was added: {offenders}",
            )

    def test_the_escalation_action_is_still_phase_5s(self):
        # Spec A7 places ENFORCING escalation (a Phase-3 budget breach becoming a level-4 stop) in
        # Phase 5. This phase provides the level-4 BEHAVIOR that escalation targets.
        request = runner_stop.request_stop
        self.assertTrue(callable(request))
        event = runner_stop.budget_breach_event(
            runner_stop.StopRequest(
                level=3,
                requested_at="2026-08-30T00:00:00+00:00",
                requester="operator",
                first_requested_at="2026-08-30T00:00:00+00:00",
                budget_seconds=600.0,
                deadline="2026-08-30T00:10:00+00:00",
            ),
            at="2026-08-30T00:00:00+00:00",
        )
        self.assertTrue(event["escalation_required"])
        self.assertFalse(
            event["escalation_performed"],
            "spec A7: this Set does not perform the escalation until Phase 5",
        )

    def test_no_automatic_reconciliation_happens_in_the_stop_path(self):
        # OQ-01 (this plan) resolved to RECORD and defer: reconciliation inside the stop path would run
        # while the tree is least trustworthy. So the stop path must not auto-heal.
        import inspect

        source = inspect.getsource(runner_stop.forced_disposition)
        for forbidden in ("git checkout", "git reset", "git stash", "restore"):
            self.assertNotIn(forbidden, source, forbidden)

    def test_unknown_outcome_is_not_introduced_as_a_new_item_status(self):
        # The scope fence the plan states explicitly: do NOT add `unknown_outcome` to TERMINAL_STATES.
        for module in (oc, agy):
            self.assertNotIn(runner_stop.FORCED_DISPOSITION, module.TERMINAL_STATES)
        self.assertNotIn(
            runner_stop.FORCED_DISPOSITION, runner_shutdown.KNOWN_ITEM_STATUSES
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
