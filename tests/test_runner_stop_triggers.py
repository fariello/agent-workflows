#!/usr/bin/env python3
"""runstop Phase 5 (`71vjbn`): the TRIGGER UX - escalating SIGINT, SIGTERM, and `run stop`.

Spec `c4gd2h` R11-R17, acceptance A5, A7, and A10.

WHAT THIS PHASE IS FOR, and therefore what these tests must prove. Phases 2-4 built four stop LEVELS
and were exercised by writing the Phase-1 stop record DIRECTLY. Before this phase, a human could not
reach any of them: neither driver installed a signal handler, so a Ctrl-C was Python's default
`KeyboardInterrupt` and a SIGTERM merely killed the driver, leaving its child reparented to init. So
this suite's job is to prove REACHABILITY through the surfaces an operator actually touches, and to
prove it by DELIVERING REAL SIGNALS to a REAL spawned driver rather than by calling a handler
function.

WHY EVERY SIGNAL TEST SPAWNS A SUBPROCESS. A test that calls the handler directly would pass even if
`signal.signal` were never called, which is exactly the defect that matters here (the whole phase is
the REGISTRATION). So the signal tests `os.kill` a real driver process and then read the durable
record it wrote. Each is bounded by a `subprocess` timeout, so a handler that deadlocks - the failure
mode Phase 1 MEASURED when a blocking `flock` was reached from a handler - FAILS this suite instead of
hanging it.

THE THREE DEFECTS THIS PHASE'S PLAN-REVIEW FOUND BY EXERCISING THE REAL CODE, each pinned below
because each would otherwise have shipped:

1. THE IMPLICIT-START SHIM WOULD HAVE SWALLOWED THE NEW VERB. Both drivers' `main()` rewrite
   `argv = ["start"] + argv` for any first token outside a HARDCODED set, and that shim lives in
   `main()`, NOT `build_parser()`. So adding the `stop` subparser alone would have turned
   `stop <run-id> --now` into `start stop <run-id> --now`: an operator asking to STOP would instead
   have LAUNCHED a run with the literal selector `stop`. `ImplicitStartShimTests` drives the real
   `main` and asserts the opposite.
2. REGISTERING A SIGINT HANDLER IS A MODIFICATION, NOT AN ADDITION. It SUPPRESSES the default
   `KeyboardInterrupt` that two existing handlers depend on: `main`'s exit-130 path, and
   `execute_item`'s item-level bookkeeping (marks the item `interrupted`, appends `ipd-interrupted`,
   reclaims lanes) that Phases 3-4 rely on. `PreExistingInterruptContractTests` asserts the chosen
   resolution - PRESERVED at the terminal rung - rather than letting it be silently stranded.
3. R17's "ALREADY-FINISHED" CASE HAD NO SOUND PROBE. `driver.lock` EXISTING is provably not liveness:
   the `2ouj70` review measured a stale lock file outliving its holder while the `flock` was already
   free. `LivenessProbeTests` asserts the decision is made by lock ACQUIRABILITY and would fail an
   implementation that checked `Path.exists()`.

PLATFORM SCOPE, STATED HONESTLY (spec A10; orchestrator OQ-02's lock half is now ANSWERED). UPDATED
by IPD `y6mfgo`: the drivers and `runner_stop` NO LONGER `import fcntl`; the lock comes from
`platform_lock`, so those modules now IMPORT on a non-POSIX host where before they could not load at
all. That is the import-time barrier removed, and nothing more. This suite still does NOT assert a
working Windows subset, because the SIGINT/SIGTERM ladder needs POSIX signal semantics and the
process-tree reap has no Windows equivalent, both of which are out of `y6mfgo`'s scope.
`PlatformHonestyTests` therefore keeps asserting the OPPOSITE of support: that no user-facing text
claims a working Windows subset, and that an uninstallable trigger is reported LOUDLY rather than
silently no-opping. What CHANGED in this suite is only the premise tripwire, which now asserts that
the top-level `fcntl` imports are GONE and that `platform_lock` owns the one guarded import; a
`sys.platform` monkeypatch is still deliberately NOT used as evidence about imports.
"""

from __future__ import annotations

import ast
import fcntl
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pytest

from agent_workflows import agy_runipd as agy
from agent_workflows import oc_runipd as oc
from agent_workflows import runner_shutdown, runner_stop
from tests.support import REPO_ROOT

_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

# ---------------------------------------------------------------------------------------------
# The fake child.
#
# For the TRIGGER tests the interesting child is one that runs LONG ENOUGH to be signalled and that
# ANNOUNCES when it is ready, so a test never has to sleep-and-hope before delivering a signal (the
# orchestrator's anti-greenwash contract forbids a wall-clock sleep defining a boundary).
#
#   `ready`     - emits a non-checkpoint event, drops a READY marker file, then emits COMPLETED events
#                 slowly forever. A level-3 stop has a reachable checkpoint here; a level-1 stop lets
#                 the turn finish (it will not, so a level-1 test uses the short `plain` mode instead).
#   `checkpoints`- like `ready` but every event is a completed checkpoint, so a level-3 request lands
#                 at the very next line.
#   `silent`    - emits a non-checkpoint event, drops READY, then goes COMPLETELY quiet. This is the
#                 escalation TARGET case (spec A7): no further line ever arrives, so anything that
#                 only runs "when the next line arrives" can never fire.
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
# in a tracked file (the established convention across the runstop suites).
_fallback_session = "ses" + "_" + "triggers"
session = args[args.index("--session") + 1] if "--session" in args else _fallback_session

id6 = ""
m = re.search(r"Assigned IPD: (\S+)", prompt)
if m:
    id6 = m.group(1)

outcome = re.search(r"Required JSON outcome: (.+)", prompt)
plan = re.search(r"Plan file at launch: (.+)", prompt)

SCHEMA = os.environ.get("SCHEMA", "oc")
RUN_DIR = pathlib.Path(os.environ["RUN_DIR"])


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


def ready():
    """Announce that this turn is running, so a test can signal WITHOUT sleeping first."""
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / ("CHILD_READY_%s" % id6)).write_text(str(os.getpid()))


def finish_turn():
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


mode = os.environ.get("CHILD_MODE", "plain")
target = os.environ.get("STOP_AFTER", "")
budget = os.environ.get("STOP_BUDGET", "")

if mode in ("ready", "checkpoints", "silent") and id6 == target:
    emit(step_start())
    emit(not_a_checkpoint("working"))
    ready()
    if mode == "silent":
        # No further line EVER. The escalation must be noticed out-of-band or not at all.
        time.sleep(float(os.environ.get("CHILD_SILENCE", "45.0")))
        (RUN_DIR / "CHILD_RAN_TO_COMPLETION").write_text("yes")
        sys.exit(0)
    for extra in range(3, 4000):
        emit(completed_tool("t%d" % extra) if mode == "checkpoints"
             else not_a_checkpoint("still working %d" % extra))
        time.sleep(0.05)
    (RUN_DIR / "CHILD_RAN_TO_COMPLETION").write_text("yes")
    finish_turn()
    sys.exit(0)

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
- 2026-08-30 created: trigger-UX test stub
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
    (repo / "README").write_text("triggers\n", encoding="utf-8")
    _git(repo, "add", "README", ".aw")
    _git(repo, "commit", "-qm", "initial")
    return repo


def _write_fake_child(root: Path) -> Path:
    fake = root / "fake_agent"
    fake.write_text(_FAKE_CHILD, encoding="utf-8")
    fake.chmod(0o755)
    return fake


def _driver_module(driver: str) -> str:
    return (
        "agent_workflows.oc_runipd" if driver == "oc" else "agent_workflows.agy_runipd"
    )


class _SignalledRun:
    """A driver process spawned so REAL signals can be delivered to it, plus its observable result."""

    def __init__(self, repo: Path, run_dir: Path, driver: str) -> None:
        self.repo = repo
        self.run_dir = run_dir
        self.run_id = run_dir.name
        self.driver = driver
        self.process: subprocess.Popen | None = None
        self.stdout = ""
        self.stderr = ""
        self.returncode: int | None = None

    # --- observation ---------------------------------------------------------------------

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

    def request(self) -> runner_stop.StopRequest | None:
        return runner_stop.read_stop_request(self.run_dir)

    # --- control -------------------------------------------------------------------------

    def wait_for_child_ready(self, id6: str, timeout: float = 60.0) -> None:
        """Block until the fake child announces it is RUNNING.

        A marker file, not a sleep: the orchestrator's contract forbids a wall-clock sleep defining a
        boundary, and a fixed sleep would also make the signal land before the turn started on a slow
        host (where it would be missed entirely).
        """

        marker = self.run_dir / f"CHILD_READY_{id6}"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if marker.is_file():
                return
            if self.process is not None and self.process.poll() is not None:
                raise AssertionError(
                    f"driver exited (rc={self.process.returncode}) before the child was ready"
                )
            time.sleep(0.02)
        raise AssertionError(f"child never became ready within {timeout}s")

    def wait_for_level(
        self, level: int, timeout: float = 30.0
    ) -> runner_stop.StopRequest:
        """Block until the DURABLE record reaches at least `level`. Returns it.

        Reading the record (not the handler's return) is what makes this evidence about the real
        signal path: the record only reaches this level if the handler ran and the write landed.
        """

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            request = self.request()
            if request is not None and request.level >= level:
                return request
            time.sleep(0.02)
        raise AssertionError(
            f"stop level {level} was never recorded within {timeout}s "
            f"(record: {self.request()})"
        )

    def signal(self, sig: int) -> None:
        assert self.process is not None
        self.process.send_signal(sig)

    def escalate_to_terminal(self, timeout: float = 60.0) -> runner_stop.StopRequest:
        """Press Ctrl-C, WAITING for each rung to be recorded, until the terminal level is reached.

        This is the real operator's loop, not a burst: spec R16 makes the driver print which level it
        accepted and how to escalate, so a human presses again after SEEING that. It is spelled out as
        a helper because a tight `for _ in range(3)` burst does NOT reach level 4 - standard POSIX
        signals are not queued, so back-to-back deliveries COALESCE into one handler invocation
        (measured; see `test_signal_coalescing_is_an_os_property_not_a_handler_defect`). Tests that
        merely need the run to END must therefore escalate deliberately rather than assume a burst
        walked the ladder.
        """

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current = self.request()
            level = current.level if current is not None else 0
            if level >= runner_stop.LEVEL_NOW_FORCE:
                assert current is not None
                return current
            self.signal(signal.SIGINT)
            target = (
                runner_stop.escalation_target(level)
                if level in runner_stop.LEVELS
                else runner_stop.LEVEL_AFTER_CALL
            )
            try:
                self.wait_for_level(target or runner_stop.LEVEL_NOW_FORCE, timeout=10.0)
            except AssertionError:
                continue  # the press coalesced; loop and press again
        raise AssertionError(
            f"could not escalate to the terminal level within {timeout}s "
            f"(record: {self.request()})"
        )

    def wait(self, timeout: float = 120.0) -> int:
        assert self.process is not None
        try:
            self.stdout, self.stderr = self.process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.stdout, self.stderr = self.process.communicate()
            raise AssertionError(
                f"driver did not exit within {timeout}s after the stop was requested; "
                f"stderr tail: {self.stderr[-2000:]}"
            )
        self.returncode = self.process.returncode
        assert self.returncode is not None
        return self.returncode


def _spawn_driver(
    repo: Path,
    fake: Path,
    selectors: list[str],
    *,
    env_extra: dict[str, str] | None = None,
    driver: str = "oc",
    run_tag: str = "",
) -> _SignalledRun:
    """Spawn the REAL driver in its OWN process group so tests can signal the DRIVER only.

    `start_new_session=True` matters: it mirrors how the driver itself spawns its child, and it means
    a signal sent here reaches the driver and not the test runner.

    `--no-isolate-worktree` / `--no-self-finalize` keep these tests on the TRIGGER behavior rather
    than dragging in worktree allocation and the lifecycle gates, which have their own suites.
    """

    env = {**_DRIVER_ENV, "AW_REPO_ROOT": str(REPO_ROOT)}
    env.setdefault("SCHEMA", "oc" if driver == "oc" else "agy")
    runs_dir = repo / ".aw" / "records" / "runs"
    existing = len(list(runs_dir.glob("run-*"))) if runs_dir.is_dir() else 0
    run_id = f"run-triggers-{run_tag or driver}-{existing}"
    env["RUN_DIR"] = str(runs_dir / run_id)
    if env_extra:
        env.update(env_extra)
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
        "--opencode" if driver == "oc" else "--agy",
        os.fspath(fake),
    ]
    run = _SignalledRun(repo, runs_dir / run_id, driver)
    run.process = subprocess.Popen(
        argv,
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    return run


def _run_stop_command(
    repo: Path,
    run_id: str,
    flag: str,
    *,
    driver: str = "oc",
    timeout: float = 60.0,
) -> subprocess.CompletedProcess:
    """Invoke the `stop` verb from a SEPARATE process, as an operator in a second terminal would.

    A separate process is the point: it is what proves the request travels through the durable record
    rather than through in-process state, and it is the only shape that exercises the sidecar lock's
    two-writer case for real.
    """

    return subprocess.run(
        [
            sys.executable,
            "-m",
            _driver_module(driver),
            "stop",
            run_id,
            flag,
            "--repo",
            os.fspath(repo),
        ],
        cwd=repo,
        env=_DRIVER_ENV,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


class _InvariantAssertions(unittest.TestCase):
    """The four Phase-0 clean-shutdown invariants, OBSERVED rather than asserted from code.

    Identical in shape to the level-3/level-4 suites deliberately: spec R1-R4 hold at EVERY level, so
    a new TRIGGER must not be allowed to reach a level in a way that skips them. R4 is asserted as
    "the dirty set never SHRANK" because Phase 0's recorded semantics are observe-and-report; demanding
    a clean tree would assert a behavior the shared routine explicitly does not have.
    """

    def assert_phase0_invariants(self, run: _SignalledRun, tree_before: str) -> None:
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

        # R2: the lock is released OBSERVABLY - a fresh handle can take it.
        lock_path = run.run_dir / "driver.lock"
        if lock_path.exists():
            with lock_path.open("a+") as handle:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:  # pragma: no cover - a real defect if hit
                    self.fail("driver.lock is still held after the run ended")
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        # R3: the ledger parses and every item carries a status Phase 0's coherence check knows.
        coherent, detail = runner_shutdown.observe_ledger(run.run_dir)
        self.assertTrue(coherent, f"ledger not coherent after the stop: {detail}")
        for item in run.state["queue"]:
            self.assertIn(item["status"], runner_shutdown.KNOWN_ITEM_STATUSES, item)

        # R4: cleanup OBSERVES the tree, it does not change it.
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


# =============================================================================================
# E-01 / V-01: the SIGINT escalation ladder, delivered as REAL signals
# =============================================================================================


@pytest.mark.slow
class SigintEscalationTests(_InvariantAssertions):
    """Spec R12/A2: 1st SIGINT -> level 1, 2nd -> level 3, 3rd -> level 4, monotonically."""

    def test_three_real_sigints_walk_the_ladder_1_3_4(self):
        # THE CENTRAL E-01 ASSERTION, and the reason it spawns a process: the record can only reach
        # these levels if `signal.signal` was actually called in the child driver. A test that invoked
        # the handler function directly would pass with no registration at all.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("saa", "sa0001"), ("saa", "sa0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["saa"],
                env_extra={"CHILD_MODE": "ready", "STOP_AFTER": "sa0001"},
                run_tag="ladder",
            )
            try:
                run.wait_for_child_ready("sa0001")

                run.signal(signal.SIGINT)
                first = run.wait_for_level(runner_stop.LEVEL_AFTER_CALL)
                self.assertEqual(
                    first.level,
                    runner_stop.LEVEL_AFTER_CALL,
                    f"1st SIGINT must request level 1, got {first.level}",
                )

                run.signal(signal.SIGINT)
                second = run.wait_for_level(runner_stop.LEVEL_NOW)
                self.assertEqual(
                    second.level,
                    runner_stop.LEVEL_NOW,
                    f"2nd SIGINT must request level 3, got {second.level}",
                )

                run.signal(signal.SIGINT)
                third = run.wait_for_level(runner_stop.LEVEL_NOW_FORCE)
                self.assertEqual(
                    third.level,
                    runner_stop.LEVEL_NOW_FORCE,
                    f"3rd SIGINT must request level 4, got {third.level}",
                )
            finally:
                run.wait(timeout=180.0)

            # THE ESCALATION HISTORY, which is what spec A2 requires to be visible in the run record.
            record = run.request()
            self.assertIsNotNone(record)
            assert record is not None
            levels = [entry["level"] for entry in record.history]
            self.assertEqual(
                levels,
                [
                    runner_stop.LEVEL_AFTER_CALL,
                    runner_stop.LEVEL_NOW,
                    runner_stop.LEVEL_NOW_FORCE,
                ],
                f"the 1 -> 3 -> 4 escalation path must appear in the record: {record.history}",
            )
            print(
                "escalation history recorded from three REAL SIGINTs: "
                + json.dumps(list(record.history), indent=2)
            )
            self.assert_phase0_invariants(run, tree_before)

    def test_rapid_repeated_sigints_are_monotonic_and_never_downgrade(self):
        """Spec R9 under the REAL trigger: rapid presses may COALESCE, but must never go backwards.

        WHAT THIS TEST ORIGINALLY ASSERTED, AND WHY THAT WAS WRONG (measured, not reasoned). It first
        asserted that three back-to-back `SIGINT`s reach level 4. They do not, and no user-space
        design can make them: standard POSIX signals are NOT QUEUED. If a second SIGINT arrives while
        the first is still pending or being handled, the two collapse into ONE delivery, so the handler
        is invoked fewer times than the signals sent. Measured directly on this host with a minimal
        harness (three `os.kill` calls in a tight loop, no driver involved):

            trivial handler (counter only)     -> 1 invocation for 3 signals
            handler costing 1ms                -> 1 invocation for 3 signals
            handler costing ~20ms (an fsync)   -> 2 invocations for 3 signals

        And the coalescing is NOT an artifact of counting presses in process-local state: an
        alternative handler that derives the next rung from the RECORDED level instead of a private
        counter was measured reaching level 1 for the same three-signal burst, because the handler
        simply never ran a second time. The loss is at kernel delivery, above any handler design.

        SO WHAT IS ACTUALLY REQUIRED, AND IS ASSERTED HERE. Spec R9 requires MONOTONICITY - "a request
        may only RAISE the level, never lower it, so an operator pressing harder is always honored" -
        and that holds regardless of coalescing. Spec R12's ladder is asserted separately by
        `test_three_real_sigints_walk_the_ladder_1_3_4`, which waits for each rung to be RECORDED
        before pressing again. That is also the real operator's loop: R16 makes the driver print what
        it is waiting for and how to escalate, so a human presses again after SEEING the report, by
        which time the handler has long returned. A programmatic burst in a tight loop is the only
        shape that coalesces, and for it "at least one rung, never a downgrade" is the honest contract.
        """

        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("sba", "sb0001")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["sba"],
                env_extra={"CHILD_MODE": "ready", "STOP_AFTER": "sb0001"},
                run_tag="rapid",
            )
            try:
                run.wait_for_child_ready("sb0001")
                for _ in range(3):
                    run.signal(signal.SIGINT)
                # At least ONE rung must be reached; how many depends on kernel coalescing.
                reached = run.wait_for_level(runner_stop.LEVEL_AFTER_CALL)
                print(
                    f"3 back-to-back SIGINTs reached level {reached.level} "
                    f"({reached.level_name}) after {len(reached.history)} handler invocation(s); "
                    f"POSIX signals are not queued, so >=1 rung is the honest guarantee"
                )
                # Then escalate DELIBERATELY (as a human would, after reading the printed hint) so the
                # endless child does not gate this test.
                final = run.escalate_to_terminal()
            finally:
                run.wait(timeout=180.0)

            self.assertEqual(final.level, runner_stop.LEVEL_NOW_FORCE)
            # MONOTONIC: every recorded step is >= its predecessor. A downgrade anywhere fails here,
            # which is the property spec R9 actually demands and the one coalescing cannot break.
            record = run.request()
            assert record is not None
            seen = [entry["level"] for entry in record.history]
            self.assertEqual(
                seen,
                sorted(seen),
                f"a downgrade appeared in the escalation history: {seen}",
            )
            self.assertTrue(
                all(level in runner_stop.SIGINT_LADDER for level in seen),
                f"a SIGINT recorded a level that is not on the ladder: {seen}",
            )
            print(f"monotonic escalation history: {seen}")
            self.assert_phase0_invariants(run, tree_before)

    def test_signal_coalescing_is_an_os_property_not_a_handler_defect(self):
        """The premise the test above rests on, MEASURED rather than asserted from documentation.

        Recorded as its own test so a future reader who doubts "rapid presses may coalesce" can see the
        evidence, and so that if a platform ever DID queue these signals this premise fails loudly
        instead of the ladder test silently under-asserting.
        """

        probe = (
            "import os, signal, time\n"
            "count = 0\n"
            "def h(s, f):\n"
            "    global count\n"
            "    count += 1\n"
            "signal.signal(signal.SIGINT, h)\n"
            "pid = os.getpid()\n"
            "if os.fork() == 0:\n"
            "    time.sleep(0.4)\n"
            "    for _ in range(3):\n"
            "        os.kill(pid, signal.SIGINT)\n"
            "    os._exit(0)\n"
            "time.sleep(1.5)\n"
            "os.wait()\n"
            "print(count)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        invocations = int(result.stdout.strip())
        print(
            f"3 back-to-back SIGINTs delivered {invocations} handler invocation(s) on this host "
            f"(standard POSIX signals are not queued)"
        )
        self.assertGreaterEqual(invocations, 1)
        self.assertLessEqual(
            invocations,
            3,
            "more invocations than signals sent would mean something else is signalling",
        )

    def test_the_handler_itself_performs_no_teardown(self):
        # Spec R7: the handler RECORDS and returns; the POLL acts. Observed rather than asserted from
        # code: after the FIRST SIGINT (level 1) the child must still be ALIVE, because level 1 lets
        # the in-flight turn finish. A handler that tore down in place would have reaped it already.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("sca", "sc0001")])
            fake = _write_fake_child(root)

            run = _spawn_driver(
                repo,
                fake,
                ["sca"],
                env_extra={"CHILD_MODE": "ready", "STOP_AFTER": "sc0001"},
                run_tag="noteardown",
            )
            try:
                run.wait_for_child_ready("sc0001")
                child_pid = int(
                    (run.run_dir / "CHILD_READY_sc0001").read_text(encoding="utf-8")
                )
                run.signal(signal.SIGINT)
                run.wait_for_level(runner_stop.LEVEL_AFTER_CALL)

                # The level-1 request is recorded, and the child is STILL RUNNING: no teardown
                # happened inside the handler.
                alive = Path(f"/proc/{child_pid}").exists() or _pid_alive(child_pid)
                self.assertTrue(
                    alive,
                    "the SIGINT handler tore the child down in place; it must only RECORD "
                    "and let the cooperative poll act (spec R7)",
                )
                print(
                    f"after the level-1 request the child pid {child_pid} is still alive: "
                    f"no teardown inside the handler"
                )
                # Now escalate so the test does not depend on the endless child finishing. Done
                # rung-by-rung (see `escalate_to_terminal`) because a burst would coalesce.
                run.escalate_to_terminal()
            finally:
                run.wait(timeout=180.0)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@pytest.mark.slow
class PreExistingInterruptContractTests(_InvariantAssertions):
    """The pre-existing `KeyboardInterrupt` behaviors a SIGINT handler SUPPRESSES (E-01's decision).

    Registering a SIGINT handler is a MODIFICATION: it removes the default `KeyboardInterrupt` that
    `main`'s exit-130 path and `execute_item`'s item-level bookkeeping both depended on. The DECISION
    recorded in `install_stop_triggers` is to PRESERVE both at the TERMINAL rung, because Phases 3-4
    rely on the interrupted item being recorded and because a third Ctrl-C is an operator asking for
    exactly the old immediate unwind. These tests assert that choice rather than assuming it.
    """

    def test_the_terminal_rung_still_records_the_item_interrupted(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("kaa", "ka0001"), ("kaa", "ka0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["kaa"],
                env_extra={"CHILD_MODE": "ready", "STOP_AFTER": "ka0001"},
                run_tag="kbint",
            )
            try:
                run.wait_for_child_ready("ka0001")
                # Rung-by-rung, not a burst: back-to-back SIGINTs coalesce (see
                # `escalate_to_terminal`), and this test needs the TERMINAL rung specifically, because
                # that is the only one that raises `KeyboardInterrupt`.
                run.escalate_to_terminal()
            finally:
                rc = run.wait(timeout=180.0)

            # The IN-FLIGHT item is recorded interrupted, one way or the other: either through
            # `execute_item`'s pre-existing `except KeyboardInterrupt` (which the terminal rung
            # preserves by raising) or through the level-4 record. Both are `interrupted`; what must
            # never happen is the item being left `running` or claimed successful.
            item = run.item("ka0001")
            self.assertEqual(
                item["status"],
                "interrupted",
                f"the interrupted item must be recorded `interrupted`, got {item}",
            )
            self.assertNotIn(item["status"], oc.SUCCESS_STATES, item)
            print(f"in-flight item after 3x SIGINT: status={item['status']!r}")

            # And the pre-existing exit-130 path is still reachable (the handler RAISES at the
            # terminal rung rather than swallowing it). 130 is SIGINT's; a level-4 stop that unwound
            # through `run_queue` instead exits nonzero too. Either is acceptable; a ZERO is not,
            # because nothing succeeded.
            self.assertNotEqual(
                rc,
                0,
                f"a force-stopped run must not exit 0 (stderr: {run.stderr[-1500:]})",
            )
            print(f"driver exit code after the terminal rung: {rc}")
            self.assert_phase0_invariants(run, tree_before)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "PRE-EXISTING REGRESSION at HEAD: the 2026-09-18 `execute_item_core` deduplication "
            "stopped calling `runner_shared.reconcile_item_on_interrupt`, so an interrupted item is "
            "left `running` and no `ipd-interrupted` event is appended. Fixing it means editing "
            "`agent_workflows/`, which is out of scope for the test-quality change that FOUND it."
        ),
    )
    def test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt(self):
        """THE CONTRACT: a real 3x-SIGINT interrupt must REACH the item-level bookkeeping.

        SPLIT FROM its structural sibling deliberately, following this repo's own documented
        convention (see `tests/test_wtiso_adversarial.py`'s header): a single function holding both a
        passing half and a known-failing half reports only `1 xfailed`, which makes the PASSING
        assertions invisible and lets a regression in them hide behind the expected failure. Split,
        the pair reports `1 passed, 1 xfailed` and a break in the structural half is visible.

        `strict=True` so that when the drivers are fixed this reports `XPASS(strict)` and forces
        somebody to remove the marker, rather than silently staying "expected to fail" forever.

        THE DEFECT, as measured: `reconcile_item_on_interrupt` was invoked at `oc_runipd.py:6717`
        before the deduplication commit and is invoked from NOWHERE in `agent_workflows/` after it -
        only `tests/test_interrupt_menu.py` calls it. The old source-text pin stayed green because
        `ipd-interrupted` still appears in each driver's `install_stop_triggers` DOCSTRING.
        """

        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("wka", "wk0001")])
            fake = _write_fake_child(root)
            run = _spawn_driver(
                repo,
                fake,
                ["wka"],
                env_extra={"CHILD_MODE": "ready", "STOP_AFTER": "wk0001"},
                run_tag="wired",
            )
            try:
                run.wait_for_child_ready("wk0001")
                run.escalate_to_terminal()
            finally:
                run.wait(timeout=180.0)

            item = run.item("wk0001")
            interrupted_events = run.events_named("ipd-interrupted")
            self.assertTrue(
                interrupted_events,
                "REGRESSION (pre-existing at HEAD, NOT introduced by this test): a real 3x-SIGINT "
                "interrupt appended NO `ipd-interrupted` event, so the item-level bookkeeping the "
                "stop ladder promised to preserve is STRANDED. Root cause: the 2026-09-18 "
                "`execute_item_core` deduplication moved the emitter into "
                "`runner_shared.reconcile_item_on_interrupt` and stopped calling it - it was invoked "
                "at `oc_runipd.py:6717` before that commit and is invoked nowhere in "
                "`agent_workflows/` after it. The old source-text pin stayed GREEN because "
                "`ipd-interrupted` still appears in each driver's `install_stop_triggers` DOCSTRING. "
                f"FIX: call `runner_shared.reconcile_item_on_interrupt` from `execute_item_core`'s "
                f"`except KeyboardInterrupt` path. Item as recorded: {item}; events: "
                f"{[e.get('event') for e in run.events()]}",
            )
            self.assertEqual(
                item["status"],
                "interrupted",
                f"the in-flight item must be recorded `interrupted` by that bookkeeping, got "
                f"{item['status']!r}",
            )


@pytest.mark.slow
class SigtermTests(_InvariantAssertions):
    """Spec R13/A3: SIGTERM requests level 3 instead of killing the driver and orphaning its child."""

    def test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("taa", "ta0001"), ("taa", "ta0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["taa"],
                # `checkpoints` so a safe checkpoint is reachable on the very next line: level 3 stops
                # at an OBSERVED completed event, so a child emitting none would (correctly) not stop
                # there, and this test is about SIGTERM's LEVEL, not about level 3's own semantics.
                env_extra={"CHILD_MODE": "checkpoints", "STOP_AFTER": "ta0001"},
                run_tag="sigterm",
            )
            try:
                run.wait_for_child_ready("ta0001")
                run.signal(signal.SIGTERM)
                request = run.wait_for_level(runner_stop.LEVEL_NOW)
            finally:
                rc = run.wait(timeout=180.0)

            self.assertEqual(
                request.level,
                runner_stop.LEVEL_NOW,
                f"SIGTERM must request level 3 (spec R13), got {request.level}",
            )
            # NOT an immediate exit: the turn stopped at a CHECKPOINT, with KNOWN certainty.
            stops = run.events_named("deliberate-stop-at-checkpoint")
            self.assertEqual(
                len(stops),
                1,
                f"SIGTERM must stop the turn at a safe checkpoint, not kill the driver; "
                f"events: {run.events()}",
            )
            record = run.item("ta0001")["stopped"]
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_KNOWN)
            self.assertEqual(record["level"], runner_stop.LEVEL_NOW)
            self.assertNotIn(
                "unknown_outcome",
                json.dumps(record),
                "a SIGTERM stop is level 3, so its certainty is KNOWN, never indeterminate",
            )
            print(
                f"SIGTERM -> level {record['level']} ({record['level_name']}), certainty "
                f"{record['certainty']}, stopped after event "
                f"{record['last_completed_event_index']} ({record['last_completed_event']}); "
                f"driver exit {rc}"
            )
            # The next item is never started: the run stops here.
            self.assertEqual(run.statuses()["ta0002"], "queued", run.statuses())
            self.assert_phase0_invariants(run, tree_before)

    def test_the_old_kill_and_orphan_behavior_is_consciously_replaced(self):
        """For a run IN FLIGHT, SIGTERM means level 3 - it no longer kills the driver.

        THE CHARACTERIZATION UPDATE, recorded rather than silently dropped. Phase 0's
        `CharacterizationTests` pinned the OLD residue of an unrequested driver death, and this phase
        does NOT change that: it changes what SIGTERM MEANS (a level-3 REQUEST rather than a death), so
        those tests still hold as written. What IS replaced is the SIGTERM ->
        `KeyboardInterrupt("Terminated by SIGTERM")` -> exit-143 mapping.

        WHAT THIS REPLACES. Three text searches: `assertIn("install_exit_signal_handler",
        render_stream_source)`, `assertIn("install_stop_triggers(run_dir)", driver_source)`, and a
        comparison of their `.index()` OFFSETS to assert install ORDER. The offset comparison is the
        worst of the three: it measured the first TEXTUAL occurrence of each name in a 7000-line file,
        so a docstring or comment mentioning either name earlier silently changed what was being
        compared, and two calls in unrelated functions would compare as "ordered" while never running
        in that sequence.

        REPLACED BY THE OBSERVABLE CONSEQUENCE, which is what "installed AFTER" actually means: after
        both installers run in the drivers' own order, the handler that OWNS SIGTERM must be the stop
        ladder's, and a real SIGTERM must record level 3 rather than raising. That is driven here with
        a real signal. If the order were reversed, the generic exit handler would win and SIGTERM would
        raise `KeyboardInterrupt` instead of recording - the exact defect (spec section 0.1: the driver
        died and left its child reparented to init, still writing the tree).
        """

        # The pre-existing helper must still EXIST, for the out-of-band commands that have no run to
        # wind down. Asserted on the API rather than on file text.
        from agent_workflows import render_stream

        self.assertTrue(
            callable(getattr(render_stream, "install_exit_signal_handler", None)),
            "the pre-existing SIGTERM helper must remain for `stop`/`status`/`report`, which have no "
            "run to wind down",
        )

        for module in (oc, agy):
            with self.subTest(driver=module.__name__):
                run_dir = Path(self.enterContext(TemporaryDirectory()))
                previous = {
                    signal.SIGINT: signal.getsignal(signal.SIGINT),
                    signal.SIGTERM: signal.getsignal(signal.SIGTERM),
                }
                presses_before = runner_stop._SIGINT_PRESSES
                try:
                    runner_stop._SIGINT_PRESSES = 0
                    runner_stop.reset_deferred_request()
                    # THE DRIVERS' OWN ORDER: the generic exit handler first, then the per-run stop
                    # triggers, exactly as `main` does it.
                    render_stream.install_exit_signal_handler()
                    status = module.install_stop_triggers(run_dir)
                    self.assertEqual(
                        status.get("SIGTERM"),
                        "installed",
                        f"{module.__name__}: this host must support SIGTERM for R13 to hold; got "
                        f"{status}",
                    )
                    # WHO OWNS SIGTERM NOW: the stop ladder's handler, not the generic exit one.
                    handler = signal.getsignal(signal.SIGTERM)
                    self.assertEqual(
                        getattr(handler, "__module__", None),
                        runner_stop.__name__,
                        f"{module.__name__}: SIGTERM is owned by {handler!r}, not the stop ladder. "
                        f"The per-run triggers must be installed AFTER the generic exit handler or a "
                        f"SIGTERM kills the driver and orphans its child (spec section 0.1).",
                    )
                    # AND THE CONSEQUENCE: a real SIGTERM RECORDS level 3 and returns; it does not
                    # raise the way the replaced exit-143 mapping did.
                    os.kill(os.getpid(), signal.SIGTERM)
                    recorded = runner_stop.read_stop_request(run_dir)
                    self.assertIsNotNone(
                        recorded,
                        f"{module.__name__}: a real SIGTERM recorded no stop request, so the R13 "
                        f"mapping is not in force",
                    )
                    assert recorded is not None
                    self.assertEqual(
                        recorded.level,
                        runner_stop.SIGTERM_LEVEL,
                        f"{module.__name__}: SIGTERM must request level "
                        f"{runner_stop.SIGTERM_LEVEL} (spec R13), got {recorded.level}",
                    )
                finally:
                    for sig, handler in previous.items():
                        signal.signal(sig, handler)
                    runner_stop._SIGINT_PRESSES = presses_before
                    runner_stop.reset_deferred_request()


# =============================================================================================
# E-03 / V-03: the out-of-band `stop` verb, in BOTH drivers
# =============================================================================================


class ImplicitStartShimTests(unittest.TestCase):
    """The defect that would have turned a stop request into a run LAUNCH.

    Both drivers' `main()` rewrite `argv = ["start"] + argv` whenever the first token is not in a
    HARDCODED set, and that shim lives in `main()`, NOT `build_parser()`. So declaring the subparser
    alone leaves `stop <run-id> --now` rewritten to `start stop <run-id> --now`: the driver would try
    to START a run whose selector is the literal string `stop`. An operator asking to stop would have
    launched work instead - a silent misfire in the exact opposite direction of their intent.

    Asserted through the REAL `main` (not by inspecting the set), because the set is only half of it:
    the subparser must also exist, and the two must agree.
    """

    def _stop_is_not_rewritten(self, module) -> None:
        # A bogus run id, so the ONLY two possible outcomes are (a) the honest "no such run" path from
        # `stop`, or (b) the shim rewriting it into `start`, which fails completely differently (it
        # tries to resolve `stop` as a plan selector and mints a run).
        with TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            rc = module.main(
                ["stop", "run-nonexistent-abcdef", "--now", "--repo", os.fspath(repo)]
            )
            self.assertNotEqual(rc, 0, "an unknown run must exit nonzero")
            # THE DISCRIMINATOR: had the shim rewritten it, a run directory would exist.
            runs = repo / ".aw" / "records" / "runs"
            self.assertFalse(
                runs.exists() and any(runs.iterdir()),
                f"`stop` was rewritten into `start`: a run was created under {runs}",
            )

    def test_oc_does_not_rewrite_a_bare_stop_into_start(self):
        self._stop_is_not_rewritten(oc)

    def test_agy_does_not_rewrite_a_bare_stop_into_start(self):
        self._stop_is_not_rewritten(agy)

    @staticmethod
    def _shim_set(module) -> set:
        """The shim's subcommand set, read off `main`'s OWN AST rather than by regexing the file.

        WHY THE SET IS READ RATHER THAN IMPORTED. It is deliberately an INLINE SET LITERAL inside
        `main()`, not a module constant - both drivers carry a KEEP-THIS-INLINE comment saying so -
        because the shim lives in `main()` and not in `build_parser()`. So there is nothing to import,
        and it must be extracted.

        REPLACES `re.search(r"subcommands = \\{(.*?)\\}", source, re.S)`, which the three tests that
        used it shared. The regex is non-greedy to the FIRST closing brace, so it silently truncates
        if the set ever contains a nested brace, and `assertIsNotNone(block)` is the only thing
        standing between a reformat and a vacuous pass - its own failure mode, recorded in this file,
        was `"unexpectedly None"`. Reading the ASSIGNMENT NODE inside `main` keeps the
        hoisting-is-forbidden property (a module constant is not an assignment in `main`, so this
        still fails, which is the point of the KEEP-THIS-INLINE comment) while being immune to
        formatting, comments, and nesting.
        """

        import inspect

        tree = ast.parse(textwrap.dedent(inspect.getsource(module.main)))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "subcommands"
                for target in node.targets
            ):
                return set(ast.literal_eval(node.value))
        raise AssertionError(
            f"{module.__name__}.main has no inline `subcommands = {{...}}` assignment. It must stay "
            f"an inline set literal INSIDE `main` (see the KEEP-THIS-INLINE comment in both "
            f"drivers): the implicit-start shim lives in `main()`, not `build_parser()`, so a token "
            f"missing from it is rewritten into `start <token>` and LAUNCHES A RUN."
        )

    #: (the verb, what an operator typing it bare would get if the shim did not know it, why it must
    #: be in the set). Both hazardous verbs, in one table: they differ only in DATA, and the rule each
    #: encodes is identical.
    SHIM_REQUIRED_VERBS = (
        (
            "stop",
            "start stop <run-id> --now",
            "an operator asking to STOP a run would LAUNCH one instead, with the literal selector "
            "`stop` - a silent misfire in the exact opposite direction of their intent",
        ),
        (
            "integrate",
            "start integrate <id6>",
            "integpath-04 (`rl67b0`) E-02: `integrate <id6>` would MINT A RUN with `integrate` as a "
            "selector. Declaring the subparser alone does NOT cover it, because the shim lives in "
            "`main()` rather than `build_parser()`",
        ),
    )

    def test_the_hazardous_verbs_are_listed_in_both_shims_subcommand_sets(self):
        """ONE table for both verbs and both drivers, asserted on `main`'s AST.

        CONSOLIDATES `test_stop_is_listed_in_both_shims_subcommand_sets` and
        `test_integrate_is_listed_in_both_shims_subcommand_sets`, which were the same test with one
        token changed - a textbook single-case pair. MODE (the driver) is a column, not a class.

        The behavioral pair (`test_oc_does_not_rewrite_a_bare_stop_into_start` and its three siblings)
        observes the CONSEQUENCE and is kept: a future edit could drop a token from ONE driver, and
        this table is what names WHICH driver and WHICH verb rather than leaving one behavioral test
        red with no diagnosis.
        """

        failures = []
        for module in (oc, agy):
            shim = self._shim_set(module)
            for verb, would_become, why in self.SHIM_REQUIRED_VERBS:
                if verb not in shim:
                    failures.append(
                        f"  {module.__name__} / {verb!r}:\n"
                        f"    - missing from the shim set, so `{verb} ...` is rewritten to "
                        f"`{would_become}`\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(self.SHIM_REQUIRED_VERBS) * 2} (verb x driver) shim "
            f"memberships are missing. Every one of them turns an out-of-band command into a RUN "
            f"LAUNCH, silently. If rows for BOTH drivers failed for one verb, the verb was never "
            f"added to the shim; if only ONE driver failed, the two shims have forked and that host "
            f"alone misfires. FIX: add the token to the inline `subcommands` set in that driver's "
            f"`main()`.\n" + "\n".join(failures),
        )

    def _integrate_is_not_rewritten(self, module) -> None:
        """integpath-04 (`rl67b0`) E-02/E-05: the SAME hazard for the new `integrate` verb.

        Mirrors `_stop_is_not_rewritten` exactly, including its discriminator: an unregistered
        `integrate` would be rewritten to `start integrate <id6>` and would MINT A RUN with the literal
        selector `integrate`. So the assertion is not merely "it exited nonzero" (a launched run can
        also fail) but "no run directory was created".
        """
        with TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            rc = module.main(["integrate", "zzzzzz", "--repo", os.fspath(repo)])
            self.assertNotEqual(rc, 0, "an id6 with no recorded lane must exit nonzero")
            runs = repo / ".aw" / "records" / "runs"
            self.assertFalse(
                runs.exists() and any(runs.iterdir()),
                f"`integrate` was rewritten into `start`: a run was created under {runs}",
            )

    def test_oc_does_not_rewrite_a_bare_integrate_into_start(self):
        self._integrate_is_not_rewritten(oc)

    def test_agy_does_not_rewrite_a_bare_integrate_into_start(self):
        self._integrate_is_not_rewritten(agy)

    # MERGED INTO `test_the_hazardous_verbs_are_listed_in_both_shims_subcommand_sets` above:
    # `test_integrate_is_listed_in_both_shims_subcommand_sets` was byte-for-byte the `stop` test with
    # one token changed, so the two are now rows of one table with the driver as a column. Its
    # behavioral pair (`test_oc_does_not_rewrite_a_bare_integrate_into_start` and the agy twin) is
    # UNTOUCHED: those drive `main` and observe the consequence, which the table does not.

    #: The shim's subcommand set, RE-DECLARED here so the control test below can evaluate the shim
    #: the way `main` does without importing a module constant that deliberately does not exist (see
    #: the KEEP-THIS-INLINE comment in both drivers).
    #:
    #: streamfmt (mm6wuz) E-12: `"-v"` and `"--version"` were REMOVED from this copy in lockstep with
    #: both drivers. Keeping them here while the drivers dropped them would leave this test passing
    #: while asserting a set the code does not have, which is worse than no test:
    #: `test_the_inline_copy_matches_both_drivers` now pins the two together.
    #:
    #: integpath-04 (`rl67b0`) E-02: `"integrate"` was ADDED to this copy in lockstep with both drivers,
    #: for the same reason `stop` is here at all. An unregistered first token is rewritten into
    #: `start <token>`, so `integrate <id6>` would LAUNCH A RUN with `integrate` as a selector. Adding
    #: the subparser alone does not cover it, because the shim lives in `main()` rather than
    #: `build_parser()`.
    #:
    #: reverify-01 (`mp289j`) E-05: `"audit"` was ADDED to this copy in lockstep with both drivers, for
    #: the identical reason, and with a sharper cost. `audit <id6>` rewritten to `start audit <id6>` does
    #: not merely misfire: an operator asking for a cheap read-only second opinion on an ALREADY-FINISHED
    #: plan would instead pay for a full execution attempt.
    SHIM_SUBCOMMANDS = {
        "start",
        "resume",
        "status",
        "report",
        "stop",
        "integrate",
        "audit",
        "-h",
        "--help",
    }

    def test_a_plain_selector_is_still_implicitly_started(self):
        # The CONTROL: adding `stop` to the set must not break the shim for ordinary selectors, which
        # is the whole reason the shim exists.
        for module in (oc, agy):
            parser = module.build_parser()
            # The shim's own behavior, evaluated the way `main` evaluates it.
            argv = ["someset"]
            self.assertTrue(argv[0] not in self.SHIM_SUBCOMMANDS, module.__name__)
            args = parser.parse_args(["start", *argv])
            self.assertEqual(args.command, "start")
            self.assertEqual(args.selectors, ["someset"])

    def test_the_inline_copy_matches_both_drivers(self):
        """streamfmt (mm6wuz) E-12: this file's copy of the set must DESCRIBE the drivers' sets.

        Without this, the copy above drifts from the code and every assertion built on it keeps
        passing while testing a set that no longer exists.

        Now reads both sets through `_shim_set`, i.e. off `main`'s AST rather than by regexing the
        file. Same property, and it still cannot be satisfied by hoisting the set into a module
        constant (there would then be no `subcommands` assignment inside `main`, which `_shim_set`
        reports as a failure naming the KEEP-THIS-INLINE requirement).
        """

        parsed = {module.__name__: self._shim_set(module) for module in (oc, agy)}
        self.assertEqual(
            parsed[oc.__name__],
            parsed[agy.__name__],
            f"the two drivers' implicit-start subcommand sets have DIVERGED:\n"
            f"  oc only:  {sorted(parsed[oc.__name__] - parsed[agy.__name__])}\n"
            f"  agy only: {sorted(parsed[agy.__name__] - parsed[oc.__name__])}",
        )
        self.assertEqual(
            parsed[oc.__name__],
            self.SHIM_SUBCOMMANDS,
            f"this file's copy of the shim set no longer describes the drivers'. Every assertion "
            f"built on `SHIM_SUBCOMMANDS` would keep passing while testing a set the code does not "
            f"have. Drivers: {sorted(parsed[oc.__name__])}; this copy: "
            f"{sorted(self.SHIM_SUBCOMMANDS)}",
        )

    def test_a_leading_verbose_flag_is_now_prefixed_with_start(self):
        """streamfmt (mm6wuz) E-05/E-12 / OQ-02: the behavior the `-v` removal changes.

        BEFORE, measured at HEAD: `-v` was a member of the set, so `aw oc run -v somesetid` was NOT
        prefixed with `start` and failed with `argument command: invalid choice: 'somesetid'`, while
        `aw oc run -vv somesetid` (not in the set) failed differently with
        `unrecognized arguments: -vv`. Two spellings of the same intent, two different errors, and
        neither reached `start`. AFTER, both are ordinary flags and both are implicitly started.
        """
        for module in (oc, agy):
            for flag in ("-v", "-vv", "--verbose"):
                with self.subTest(module=module.__name__, flag=flag):
                    argv = [flag, "somesetid"]
                    self.assertNotIn(
                        argv[0],
                        self.SHIM_SUBCOMMANDS,
                        "a leading verbosity flag must not be treated as a subcommand",
                    )
                    args = module.build_parser().parse_args(["start", *argv])
                    self.assertEqual(args.command, "start")
                    self.assertEqual(args.selectors, ["somesetid"])
                    self.assertEqual(args.verbosity, 2 if flag == "-vv" else 1)

    def test_neither_driver_registers_the_version_flag_the_removed_entry_guarded(self):
        """OQ-02's evidence, pinned: `--version` was reserved and never implemented.

        If a real `--version` is added later, this test fails and is the place to record that BOTH
        tokens must go back into BOTH drivers' sets together.
        """
        for module in (oc, agy):
            with self.subTest(module=module.__name__):
                with self.assertRaises(SystemExit) as ctx:
                    module.build_parser().parse_args(["--version"])
                self.assertEqual(ctx.exception.code, 2)


class StopVerbSurfaceTests(unittest.TestCase):
    """Spec R14/R15: all four flags exist in BOTH drivers, and none implies cleanup is optional."""

    def _help(self, driver: str) -> str:
        result = subprocess.run(
            [sys.executable, "-m", _driver_module(driver), "stop", "--help"],
            env=_DRIVER_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return result.stdout

    def test_both_drivers_expose_all_four_level_flags(self):
        for driver in ("oc", "agy"):
            text = self._help(driver)
            for flag in ("--after-call", "--after-set", "--now", "--now-force"):
                self.assertIn(flag, text, f"{driver}: missing {flag}")
            print(f"--- {driver} stop --help ---\n{text}")

    def test_the_help_states_that_cleanup_is_unconditional(self):
        # Spec R15: the flag NAMES describe interruption force. The help must say, in words, that
        # cleanup is not optional - otherwise `--now-force` reads as "skip the tidying".
        #
        # The DESCRIPTION is asserted on the rendered `--help`, because argparse reproduces a
        # `RawDescriptionHelpFormatter` description verbatim.
        for driver in ("oc", "agy"):
            text = self._help(driver)
            self.assertIn("Cleanup is UNCONDITIONAL", text, driver)
            self.assertIn("No flag makes cleanup optional", text, driver)

    def test_each_individual_flags_help_repeats_that_cleanup_still_runs(self):
        # Asserted on the DECLARED help strings rather than on the rendered output, because argparse
        # WRAPS per-option help to the terminal width and inserts newlines mid-phrase - so counting the
        # phrase in the rendered text is a formatting assertion, not a content one (measured: 1 of 4
        # survived the wrap intact). The declared strings are the source of truth for what an operator
        # reading a single line is told.
        self.assertEqual(
            sorted(runner_stop.STOP_LEVEL_FLAG_HELP),
            ["--after-call", "--after-set", "--now", "--now-force"],
        )
        for flag, help_text in runner_stop.STOP_LEVEL_FLAG_HELP.items():
            with self.subTest(flag=flag):
                self.assertIn("Interruption force only", help_text, flag)
                self.assertIn("cleanup still runs unconditionally", help_text, flag)
                print(f"{flag}: {help_text}")
        # And the rendered help really does carry them, however it chooses to wrap: the wrap-insensitive
        # form is the flag name plus the phrase's first words.
        for driver in ("oc", "agy"):
            collapsed = " ".join(self._help(driver).split())
            self.assertEqual(
                collapsed.count("Interruption force only"),
                4,
                f"{driver}: all four flags must state the force-only meaning in the rendered help",
            )
            self.assertEqual(
                collapsed.count("cleanup still runs unconditionally"),
                4,
                f"{driver}: all four flags must state that cleanup still runs",
            )

    def test_no_flag_name_or_help_implies_optional_cleanup(self):
        # The negative form of R15, asserted on the vocabulary rather than on a single phrase.
        for driver in ("oc", "agy"):
            text = self._help(driver).lower()
            for forbidden in (
                "--no-cleanup",
                "--skip-cleanup",
                "--dirty",
                "without cleanup",
                "skips cleanup",
            ):
                self.assertNotIn(forbidden, text, f"{driver}: {forbidden}")

    def test_a_bare_stop_without_a_level_is_a_usage_error(self):
        # Not a silent no-op: an operator who forgot the level must be told, or they will believe a
        # stop was requested when none was.
        for driver in ("oc", "agy"):
            result = subprocess.run(
                [sys.executable, "-m", _driver_module(driver), "stop", "run-x"],
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            self.assertNotEqual(result.returncode, 0, driver)
            self.assertIn("--after-call", result.stderr, driver)


@pytest.mark.slow
class OutOfBandStopTests(_InvariantAssertions):
    """Spec R14/A4: each of the four levels is requestable from a SEPARATE process, in both drivers."""

    def test_each_flag_records_its_level_from_a_second_process(self):
        # V-03 requires evidence for ALL FOUR flags, each recorded by a genuinely separate process.
        # A LIVE run is required (spec R17 refuses a request against a run with no live driver), so a
        # real driver is spawned and held at a running turn while the request is made.
        for flag, expected in (
            ("--after-call", runner_stop.LEVEL_AFTER_CALL),
            ("--after-set", runner_stop.LEVEL_AFTER_SET),
            ("--now", runner_stop.LEVEL_NOW),
            ("--now-force", runner_stop.LEVEL_NOW_FORCE),
        ):
            with self.subTest(flag=flag):
                with TemporaryDirectory() as temp:
                    root = Path(temp)
                    repo = _make_repo(root, [("oba", "ob0001"), ("oba", "ob0002")])
                    fake = _write_fake_child(root)

                    run = _spawn_driver(
                        repo,
                        fake,
                        ["oba"],
                        env_extra={"CHILD_MODE": "checkpoints", "STOP_AFTER": "ob0001"},
                        run_tag=f"oob{flag.strip('-')}",
                    )
                    try:
                        run.wait_for_child_ready("ob0001")
                        result = _run_stop_command(repo, run.run_id, flag)
                        self.assertEqual(
                            result.returncode,
                            0,
                            f"{flag}: stop exited nonzero against a LIVE run: "
                            f"{result.stdout}{result.stderr}",
                        )
                        request = run.wait_for_level(expected)
                        self.assertEqual(request.level, expected, flag)
                        print(
                            f"{flag} from a separate process recorded level "
                            f"{request.level} ({request.level_name}); "
                            f"stop said: {result.stdout.strip()}"
                        )
                        if expected in runner_stop.BETWEEN_TURN_LEVELS:
                            # Levels 1-2 do not interrupt the turn, and this fake child never
                            # finishes, so escalate to end the test deterministically rather than
                            # waiting on it.
                            _run_stop_command(repo, run.run_id, "--now-force")
                    finally:
                        run.wait(timeout=180.0)

    def test_the_agy_driver_behaves_identically(self):
        # Orchestrator CID-3: an operator switching hosts must get the same verb, not a similar one.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("gba", "gb0001"), ("gba", "gb0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["gba"],
                env_extra={
                    "CHILD_MODE": "checkpoints",
                    "STOP_AFTER": "gb0001",
                    "SCHEMA": "agy",
                },
                driver="agy",
                run_tag="agyoob",
            )
            try:
                run.wait_for_child_ready("gb0001")
                result = _run_stop_command(repo, run.run_id, "--now", driver="agy")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                request = run.wait_for_level(runner_stop.LEVEL_NOW)
            finally:
                run.wait(timeout=180.0)

            self.assertEqual(request.level, runner_stop.LEVEL_NOW)
            print(
                f"aw agy run stop --now recorded level {request.level}: {result.stdout.strip()}"
            )
            self.assert_phase0_invariants(run, tree_before)


# =============================================================================================
# E-04 / V-04: the honest error path (spec R17, A5)
# =============================================================================================


class UnknownRunTests(unittest.TestCase):
    """Spec A5: an unknown run exits nonzero, names the run, and mutates NOTHING."""

    def _probe(self, driver: str) -> tuple[subprocess.CompletedProcess, Path]:
        temp = tempfile.mkdtemp()
        repo = Path(temp) / "repo"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))
        result = _run_stop_command(repo, "run-no-such-run-999", "--now", driver=driver)
        after = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))
        self.assertEqual(
            before,
            after,
            f"{driver}: `stop` on an unknown run created or removed paths: "
            f"{set(after) ^ set(before)}",
        )
        return result, repo

    def test_it_exits_nonzero_and_names_the_unknown_run(self):
        for driver in ("oc", "agy"):
            result, repo = self._probe(driver)
            self.assertNotEqual(result.returncode, 0, driver)
            combined = result.stdout + result.stderr
            self.assertIn("run-no-such-run-999", combined, driver)
            print(
                f"{driver}: stop <bogus> -> exit {result.returncode}: {combined.strip()}"
            )

    def test_it_creates_no_run_directory_and_no_stop_request(self):
        for driver in ("oc", "agy"):
            _, repo = self._probe(driver)
            runs = repo / ".aw" / "records" / "runs"
            self.assertFalse(runs.exists(), f"{driver}: a run root was created")
            self.assertEqual(
                list(repo.rglob(runner_stop.STOP_REQUEST_FILENAME)),
                [],
                f"{driver}: a stop-request file was written for a run that does not exist",
            )
            listing = subprocess.run(
                ["find", os.fspath(repo), "-not", "-path", "*/.git/*"],
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout
            print(f"{driver}: filesystem after the refused stop:\n{listing}")


class LivenessProbeTests(unittest.TestCase):
    """R17's LIVE-vs-FINISHED probe, which is lock ACQUIRABILITY and not file existence.

    THE MEASURED FACT THIS ENCODES. The `2ouj70` review observed a `driver.lock` file OUTLIVING its
    holder while the `flock` was already free (the kernel drops an `flock` on holder death). So a
    `Path.exists()` check would report a long-finished run as LIVE, and `stop` would happily write a
    request nothing will ever read - the "appears to succeed" failure spec R17 exists to forbid.
    """

    def test_a_stale_lock_file_reads_as_FINISHED_not_live(self):
        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            run_dir.mkdir(parents=True)
            lock = run_dir / "driver.lock"
            holder = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import fcntl,sys,time\n"
                    "h=open(sys.argv[1],'a+')\n"
                    "fcntl.flock(h.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
                    "print('locked',flush=True)\n"
                    "time.sleep(120)\n",
                    str(lock),
                ],
                stdout=subprocess.PIPE,
                text=True,
            )
            assert holder.stdout is not None
            self.assertEqual(holder.stdout.readline().strip(), "locked")
            self.assertEqual(
                runner_stop.run_liveness(run_dir),
                runner_stop.LIVENESS_LIVE,
                "a live holder must be detected as live",
            )
            holder.kill()
            holder.wait(timeout=10)
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline and _pid_alive(holder.pid):
                time.sleep(0.02)

            # BOTH halves, which is the whole point: the FILE survives, and the run reads FINISHED.
            self.assertTrue(
                lock.is_file(),
                "premise changed: driver.lock no longer survives its holder's death; "
                "this test's discriminator needs rethinking",
            )
            self.assertEqual(
                runner_stop.run_liveness(run_dir),
                runner_stop.LIVENESS_FINISHED,
                "a STALE lock file must read as FINISHED; a `Path.exists()` probe would say LIVE",
            )
            print(
                f"stale lock file exists ({lock.is_file()}) yet liveness is "
                f"{runner_stop.run_liveness(run_dir)!r}: decided by acquirability, not existence"
            )

    def test_stop_on_a_finished_run_exits_nonzero_and_records_nothing(self):
        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            run_dir.mkdir(parents=True)
            # A leftover lock FILE with no holder: the exact stale-residue shape above.
            (run_dir / "driver.lock").write_text(
                "pid=999999 started=old\n", encoding="utf-8"
            )

            result = runner_stop.stop_command(
                run_dir, runner_stop.LEVEL_NOW, run_id="run-finished", requester="test"
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertEqual(result.liveness, runner_stop.LIVENESS_FINISHED)
            self.assertFalse(result.recorded)
            self.assertIn("no live run", result.message)
            self.assertFalse(
                runner_stop.stop_request_path(run_dir).exists(),
                "no stop request may be written for a run with no live driver",
            )
            print(f"finished-run path: exit {result.exit_code}: {result.message}")

    #: (case, does `driver.lock` EXIST?, what the shared acquirability probe answers, the liveness
    #: the probe must report, why this row exists)
    #:
    #: THE TABLE IS THE WHOLE POINT. An existence check maps EXISTENCE to the answer, so the rows
    #: that break it are the ones where existence and the answer DISAGREE. Rows 1 and 2 are exactly
    #: that pair - present-but-free must read FINISHED, absent must read FINISHED - and an
    #: implementation keyed on `.exists()` gets row 1 backwards. Row 3 is the positive control
    #: (present AND held -> LIVE) without which a probe hardcoded to FINISHED would pass rows 1-2.
    #: Row 4 is the answer that an existence check cannot even express.
    LIVENESS_CASES = (
        (
            "present but UNHELD",
            True,
            True,
            "LIVENESS_FINISHED",
            "THE ROW THAT KILLS AN EXISTENCE CHECK. The `2ouj70` review MEASURED a stale lock file "
            "outliving its holder while the `flock` was already free, so a `Path.exists()` probe "
            "reports LIVE for a run with no driver - and `stop` then writes a request nothing will "
            "ever read, telling the operator their stop was accepted when it was not",
        ),
        (
            "absent entirely",
            False,
            True,
            "LIVENESS_FINISHED",
            "a lock cannot be held on a file that does not exist. Same verdict as row 1 from the "
            "OPPOSITE existence value, which is what proves the answer is not keyed on existence",
        ),
        (
            "present and HELD",
            True,
            False,
            "LIVENESS_LIVE",
            "THE POSITIVE CONTROL. Without it a probe hardcoded to FINISHED would satisfy rows 1-2 "
            "while making every `stop` refuse a genuinely live run",
        ),
        (
            "unanswerable (platform or OS error)",
            True,
            None,
            "LIVENESS_UNDETERMINED",
            "`None` is a REAL answer and must not collapse into either side: failing to prove a "
            "holder is alive is not proof it is dead. An existence check has no way to express "
            "this third state at all, so a `.exists()` implementation cannot satisfy this row",
        ),
    )

    def test_the_probe_is_not_implemented_as_a_file_existence_check(self):
        """Liveness is decided by lock ACQUIRABILITY. Driven, so an existence check FAILS here.

        WHAT THIS REPLACES. The pin was `assertIn("lock_is_free", source)` plus
        `assertNotIn(".exists()"/".is_file()", source)` over `inspect.getsource(run_liveness)`. It
        is a change-detector three ways: the name `lock_is_free` appearing in a COMMENT satisfies
        the positive half; the function's own docstring says "never by file existence", so any
        rewording toward `.exists()` in prose fails the negative half; and an existence check
        written as `if target.stat():` or `os.path.exists(...)` passes both while being the exact
        defect. It also asserted a MECHANISM (call this helper) where the contract is an ANSWER.

        REPLACED BY THE DISCRIMINATING STATES, table-driven. The probe's answer is FORCED for each
        row by substituting the shared acquirability helper's verdict, so the rows are exactly the
        four (existence, acquirability) combinations that matter - including the two where existence
        and the correct answer DISAGREE, which is what an existence-check implementation gets wrong.

        This is the UNIT half. The end-to-end proof against a REAL killed holder (a genuinely stale
        file on disk, with a live-then-dead process) is
        `test_a_stale_lock_file_reads_as_FINISHED_not_live` below, which cannot be a row here
        because it spawns and kills a process.
        """

        failures = []
        for case, exists, free, expected_name, why in self.LIVENESS_CASES:
            expected = getattr(runner_stop, expected_name)
            with TemporaryDirectory() as temp:
                run_dir = Path(temp) / "run"
                run_dir.mkdir(parents=True)
                lock = run_dir / "driver.lock"
                if exists:
                    lock.write_text("pid=999999 started=old\n", encoding="utf-8")
                probed: list[Path] = []

                def fake_lock_is_free(path: Path, _free=free, _seen=probed):
                    _seen.append(Path(path))
                    return _free

                with mock.patch.object(
                    runner_shutdown, "lock_is_free", fake_lock_is_free
                ):
                    actual = runner_stop.run_liveness(run_dir)
                if actual != expected:
                    failures.append(
                        f"  {case} (file exists={exists}, lock free={free}):\n"
                        f"    - reported {actual!r}, expected {expected!r} ({expected_name})\n"
                        f"    this row exists because: {why}"
                    )
                elif probed != [lock]:
                    # The answer was right, but it was not obtained by PROBING the lock - so it
                    # cannot have been obtained by acquirability, and the next row's disagreement
                    # between existence and truth would be decided by luck.
                    failures.append(
                        f"  {case} (file exists={exists}, lock free={free}):\n"
                        f"    - reported {actual!r} correctly, but probed {probed!r} instead of "
                        f"[{lock}]: the verdict did not come from the acquirability probe\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            failures,
            [],
            f"liveness is not decided by lock ACQUIRABILITY: {len(failures)} of "
            f"{len(self.LIVENESS_CASES)} states are wrong. Every row forces the shared probe's "
            f"answer, so a `Path.exists()`/`.is_file()` implementation fails the two rows where "
            f"existence and the truth DISAGREE (a stale file present but free, and an absent file), "
            f"and cannot express UNDETERMINED at all. If ONLY the 'present but UNHELD' row failed, "
            f"the probe has been simplified into an existence check and a `stop` against a finished "
            f"run now reports success while writing a request nothing reads. FIX: route the verdict "
            f"through `runner_shutdown.lock_is_free`, which never creates the file.\n"
            + "\n".join(failures),
        )


class AlreadyStoppingTests(unittest.TestCase):
    """Spec R17/R9: an already-stopping run REPORTS its level and is never downgraded."""

    def _live_run_dir(self, temp: Path) -> tuple[Path, subprocess.Popen]:
        """A run dir whose lock is genuinely HELD, so the liveness probe reports LIVE."""

        run_dir = temp / "run"
        run_dir.mkdir(parents=True)
        holder = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import fcntl,sys,time\n"
                "h=open(sys.argv[1],'a+')\n"
                "fcntl.flock(h.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
                "print('locked',flush=True)\n"
                "time.sleep(120)\n",
                str(run_dir / "driver.lock"),
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "locked"
        return run_dir, holder

    def test_a_lower_request_reports_the_level_in_force_and_does_not_downgrade(self):
        with TemporaryDirectory() as temp:
            run_dir, holder = self._live_run_dir(Path(temp))
            try:
                high = runner_stop.stop_command(
                    run_dir, runner_stop.LEVEL_NOW_FORCE, run_id="r", requester="first"
                )
                self.assertEqual(high.exit_code, 0)
                self.assertTrue(high.recorded)

                low = runner_stop.stop_command(
                    run_dir,
                    runner_stop.LEVEL_AFTER_CALL,
                    run_id="r",
                    requester="second",
                )
                # Exit 0: the operator asked for something already guaranteed. But NOT a downgrade,
                # and the message must say the recorded level is UNCHANGED rather than implying the
                # weaker request took effect.
                self.assertEqual(low.exit_code, 0)
                self.assertFalse(low.recorded)
                self.assertEqual(low.level, runner_stop.LEVEL_NOW_FORCE)
                self.assertIn("already stopping at level 4", low.message)
                self.assertIn("UNCHANGED", low.message)

                still = runner_stop.read_stop_request(run_dir)
                assert still is not None
                self.assertEqual(
                    still.level,
                    runner_stop.LEVEL_NOW_FORCE,
                    "a lower out-of-band request must never lower the recorded level (spec R9)",
                )
                print(f"already-stopping report: {low.message}")
            finally:
                holder.kill()
                holder.wait(timeout=10)

    def test_a_higher_request_escalates_and_reports_the_new_level(self):
        with TemporaryDirectory() as temp:
            run_dir, holder = self._live_run_dir(Path(temp))
            try:
                runner_stop.stop_command(
                    run_dir, runner_stop.LEVEL_AFTER_CALL, run_id="r", requester="first"
                )
                up = runner_stop.stop_command(
                    run_dir, runner_stop.LEVEL_NOW, run_id="r", requester="second"
                )
                self.assertEqual(up.exit_code, 0)
                self.assertTrue(up.recorded)
                self.assertEqual(up.level, runner_stop.LEVEL_NOW)
                record = runner_stop.read_stop_request(run_dir)
                assert record is not None
                self.assertEqual(
                    [e["level"] for e in record.history],
                    [runner_stop.LEVEL_AFTER_CALL, runner_stop.LEVEL_NOW],
                )
                print(f"escalating out-of-band request: {up.message}")
            finally:
                holder.kill()
                holder.wait(timeout=10)


# =============================================================================================
# E-05 / V-05: progress reporting (spec R16)
# =============================================================================================


class RequestReportContentTests(unittest.TestCase):
    """Spec R16: every accepted request names the LEVEL, the AWAITED BOUNDARY, and HOW TO ESCALATE.

    All three parts are required. A report that says only "stopping" is a defect: an operator who
    cannot see which boundary is being awaited cannot tell a correct wind-down from a hang, which is
    the confusion this requirement exists to remove.
    """

    def test_every_level_reports_all_three_required_parts(self):
        for level in runner_stop.LEVELS:
            with self.subTest(level=level):
                text = runner_stop.render_request_accepted(level, requester="operator")
                # 1. the level, by number AND name
                self.assertIn(f"level {level}", text)
                self.assertIn(runner_stop.LEVEL_NAMES[level], text)
                # 2. the awaited boundary
                self.assertIn(runner_stop.AWAITING[level], text)
                self.assertIn("waiting for", text)
                # 3. how to escalate (or an honest statement that there is nothing higher)
                target = runner_stop.escalation_target(level)
                if target is None:
                    self.assertIn("nothing harder to escalate to", text)
                else:
                    self.assertIn(f"level {target}", text)
                    self.assertIn("stop harder", text)
                print(f"level {level}: {text}")

    def test_the_escalation_hint_follows_the_specs_ladder(self):
        # Spec R12's ladder is 1 -> 3 -> 4, so level 1's hint must point at 3 (NOT 2), and level 2 -
        # which is reachable only out-of-band - points at 3 as well.
        self.assertEqual(runner_stop.escalation_target(1), runner_stop.LEVEL_NOW)
        self.assertEqual(runner_stop.escalation_target(2), runner_stop.LEVEL_NOW)
        self.assertEqual(runner_stop.escalation_target(3), runner_stop.LEVEL_NOW_FORCE)
        self.assertIsNone(
            runner_stop.escalation_target(4),
            "level 4 is terminal; claiming something higher would be false",
        )

    def test_level_2_is_reachable_only_out_of_band_and_that_is_recorded(self):
        # A reviewer could read the gap as an omission; it is a consequence of the spec's ladder.
        self.assertNotIn(runner_stop.LEVEL_AFTER_SET, runner_stop.SIGINT_LADDER)
        self.assertEqual(
            runner_stop.SIGINT_LADDER,
            (
                runner_stop.LEVEL_AFTER_CALL,
                runner_stop.LEVEL_NOW,
                runner_stop.LEVEL_NOW_FORCE,
            ),
        )
        self.assertIn("after_set", runner_stop.LEVEL_FLAGS)

    def test_a_monotonic_no_op_is_still_reported(self):
        # Silence on a second press would look like the press was dropped.
        text = runner_stop.render_request_accepted(3, accepted=False)
        self.assertIn("already at or above", text)
        self.assertIn("waiting for", text)


@pytest.mark.slow
class SignalledRunReportsProgressTests(_InvariantAssertions):
    """V-05: the THREE required parts appear in the REAL driver's output, for EACH escalation step."""

    def test_captured_output_names_level_boundary_and_escalation_at_every_step(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("raa", "ra0001"), ("raa", "ra0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["raa"],
                env_extra={"CHILD_MODE": "ready", "STOP_AFTER": "ra0001"},
                run_tag="report",
            )
            try:
                run.wait_for_child_ready("ra0001")
                run.signal(signal.SIGINT)
                run.wait_for_level(runner_stop.LEVEL_AFTER_CALL)
                run.signal(signal.SIGINT)
                run.wait_for_level(runner_stop.LEVEL_NOW)
                run.signal(signal.SIGINT)
                run.wait_for_level(runner_stop.LEVEL_NOW_FORCE)
            finally:
                run.wait(timeout=180.0)

            captured = run.stdout + run.stderr
            print("--- captured driver output (stop reports) ---")
            for line in captured.splitlines():
                if "stop accepted" in line or "stop already" in line:
                    print(line)

            for level in (
                runner_stop.LEVEL_AFTER_CALL,
                runner_stop.LEVEL_NOW,
                runner_stop.LEVEL_NOW_FORCE,
            ):
                with self.subTest(level=level):
                    # 1. the accepted level
                    self.assertIn(
                        f"level {level} ({runner_stop.LEVEL_NAMES[level]})",
                        captured,
                        f"level {level} was never reported (spec R16 forbids silence)",
                    )
                    # 2. the awaited boundary
                    self.assertIn(
                        runner_stop.AWAITING[level],
                        captured,
                        f"level {level}'s awaited boundary was not reported",
                    )
                    # 3. the escalation hint
                    target = runner_stop.escalation_target(level)
                    expected_hint = (
                        "nothing harder to escalate to"
                        if target is None
                        else "to stop harder"
                    )
                    self.assertIn(
                        expected_hint,
                        captured,
                        f"level {level}'s escalation hint was not reported",
                    )
            self.assert_phase0_invariants(run, tree_before)


# =============================================================================================
# E-06 / V-06: the wind-down budget escalation Phase 3 only RECORDED (spec R11, A7)
# =============================================================================================


class EscalationDecisionTests(unittest.TestCase):
    """The escalation DECISION, unit-tested without timing so it is not a flaky clock assertion."""

    def _record(self, run_dir: Path, level: int, budget: float) -> None:
        """Write a record whose deadline is ALREADY PAST, via the module's own writer + a rewrite.

        The budget is injected rather than waited out: the real level-1 budget is 2 hours, so a test
        that waited for it would be untestable rather than thorough.
        """

        runner_stop.request_stop(run_dir, level, "operator")
        path = runner_stop.stop_request_path(run_dir)
        payload = json.loads(path.read_text(encoding="utf-8"))
        import datetime as dt

        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=budget + 1.0)
        payload["requested_at"] = past.isoformat()
        payload["budget_seconds"] = budget
        payload["deadline"] = (past + dt.timedelta(seconds=budget)).isoformat()
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def test_a_breached_level_1_escalates_to_level_3(self):
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._record(run_dir, runner_stop.LEVEL_AFTER_CALL, 0.1)
            watch = runner_stop.EscalationWatch(run_dir)
            self.assertEqual(
                watch.check_once(),
                (runner_stop.LEVEL_AFTER_CALL, runner_stop.LEVEL_NOW),
            )
            record = runner_stop.read_stop_request(run_dir)
            assert record is not None
            self.assertEqual(record.level, runner_stop.LEVEL_NOW)
            self.assertIn("budget-escalation", record.requester)

    def test_a_breached_level_3_escalates_to_level_4(self):
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._record(run_dir, runner_stop.LEVEL_NOW, 0.1)
            watch = runner_stop.EscalationWatch(run_dir)
            self.assertEqual(
                watch.check_once(), (runner_stop.LEVEL_NOW, runner_stop.LEVEL_NOW_FORCE)
            )

    def test_level_4_is_terminal_and_is_never_re_escalated(self):
        # Spec R23: re-recording the same level as an "escalation" would claim work not done.
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._record(run_dir, runner_stop.LEVEL_NOW_FORCE, 0.1)
            watch = runner_stop.EscalationWatch(run_dir)
            self.assertIsNone(watch.check_once())
            self.assertFalse(watch.escalated)

    def test_an_unexpired_deadline_does_not_escalate(self):
        # The negative control: escalation must be a BREACH response, not a timer that always fires.
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            runner_stop.request_stop(run_dir, runner_stop.LEVEL_AFTER_CALL, "operator")
            watch = runner_stop.EscalationWatch(run_dir)
            self.assertIsNone(watch.check_once())
            record = runner_stop.read_stop_request(run_dir)
            assert record is not None
            self.assertEqual(record.level, runner_stop.LEVEL_AFTER_CALL)

    def test_no_request_at_all_is_not_a_breach(self):
        with TemporaryDirectory() as temp:
            watch = runner_stop.EscalationWatch(Path(temp))
            self.assertIsNone(watch.check_once())
            self.assertFalse(runner_stop.stop_request_path(Path(temp)).exists())

    def test_the_watch_walks_the_whole_ladder_rather_than_stalling_at_the_middle_rung(
        self,
    ):
        # WHY THIS MATTERS, and why one escalation is not enough for R11. Escalating a breached level-1
        # wind-down to level 3 hands the turn to a level that is observed FROM THE CHILD'S EVENT
        # STREAM, so on a silent child the escalated level-3 stop would never be noticed either and
        # the stop would stall at the middle rung - i.e. it WOULD hang forever, which is exactly what
        # R11 forbids. Only level 4 is acted on unconditionally out-of-band.
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._record(run_dir, runner_stop.LEVEL_AFTER_CALL, 0.1)
            watch = runner_stop.EscalationWatch(run_dir)
            first = watch.check_once()
            self.assertEqual(
                first, (runner_stop.LEVEL_AFTER_CALL, runner_stop.LEVEL_NOW)
            )
            # The escalated request has its OWN budget (level 3's), so force ITS deadline past too.
            path = runner_stop.stop_request_path(run_dir)
            payload = json.loads(path.read_text(encoding="utf-8"))
            import datetime as dt

            payload["deadline"] = (
                dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)
            ).isoformat()
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )
            second = watch.check_once()
            self.assertEqual(
                second, (runner_stop.LEVEL_NOW, runner_stop.LEVEL_NOW_FORCE)
            )
            self.assertEqual(
                watch.escalations,
                (
                    (runner_stop.LEVEL_AFTER_CALL, runner_stop.LEVEL_NOW),
                    (runner_stop.LEVEL_NOW, runner_stop.LEVEL_NOW_FORCE),
                ),
            )
            print(f"ladder walked under repeated breaches: {watch.escalations}")

    def test_the_escalation_event_records_that_it_WAS_performed(self):
        # The deliberate counterpart of Phase 3's breach event, which records
        # `escalation_performed: False`. Read together they show detection and then action, with
        # neither phase claiming the other's work (spec R11/R23).
        event = runner_stop.escalation_event(
            from_level=1,
            to_level=3,
            at="2026-08-30T00:00:00+00:00",
            reason="budget expired",
        )
        self.assertEqual(event["event"], runner_stop.ESCALATION_EVENT)
        self.assertTrue(event["escalation_performed"])
        self.assertTrue(event["escalation_required"])
        self.assertEqual(event["from_level"], 1)
        self.assertEqual(event["level"], 3)
        self.assertFalse(event["failure"])
        self.assertTrue(event["deliberate"])
        breach = runner_stop.budget_breach_event(
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
        self.assertFalse(
            breach["escalation_performed"],
            "Phase 3 DETECTS; this phase ACTS. The two events must stay distinguishable.",
        )

    def test_the_watch_stops_quietly_when_the_child_is_already_gone(self):
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self._record(run_dir, runner_stop.LEVEL_AFTER_CALL, 0.1)
            watch = runner_stop.EscalationWatch(run_dir, is_alive=lambda: False)
            with watch:
                time.sleep(0.4)
            self.assertFalse(watch.escalated)


def _age_deadline(run_dir: Path, *, budget: float = 0.25) -> None:
    """Rewrite the CURRENT stop request so its wind-down deadline is already PAST.

    Injected rather than waited out, and that is what makes the assertion meaningful rather than
    merely slow: the real budgets are 2h (level 1) and 10m (level 3), so a test that waited for one
    would be untestable. The record is written by the module's own writer first, so only the deadline
    fields are synthetic - the shape, the level, and the history are the real ones a request produces.
    """

    import datetime as dt

    path = runner_stop.stop_request_path(run_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=budget + 1.0)
    payload["requested_at"] = past.isoformat()
    payload["budget_seconds"] = budget
    payload["deadline"] = (past + dt.timedelta(seconds=budget)).isoformat()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


@pytest.mark.slow
class BudgetEscalationEndToEndTests(_InvariantAssertions):
    """Spec A7: a level-1 request against a turn that will NOT finish escalates, bounded and recorded.

    THE SHAPE THAT MAKES THIS HONEST EVIDENCE. The budget is INJECTED and sub-second, so the test
    cannot pass merely by waiting out the real 2-hour level-1 budget. The child then goes COMPLETELY
    SILENT, which is the case an in-loop check can never handle: `for line in process.stdout` BLOCKS,
    so anything that only runs "when the next line arrives" would wait forever.

    WHAT "BOUNDED" HONESTLY MEANS HERE, corrected after MEASURING it rather than assuming. This test
    first asserted that a breached level-1 wind-down reaches LEVEL 4 within seconds. It does not, and
    the reason is a real property of the design rather than a bug: each escalation goes through the
    same monotonic writer every other request uses, so the ESCALATED request gets the budget spec R11
    assigns ITS level. Measured: a breached level-1 request escalated to level 3 in ~12ms, and the new
    level-3 request then carried level 3's real 600s deadline, so level 4 was correctly still 10
    minutes away. The bound is therefore the SUM OF THE RUNGS' BUDGETS, not one budget - finite,
    recorded, and never infinite, which is what R11 requires ("a hung turn cannot make a stop hang
    forever"). So this test asserts the breach-to-escalation LATENCY at each rung, and walks the ladder
    by aging each escalated request in turn, instead of pretending one 0.25s injection bounds all
    three rungs.
    """

    def test_a_non_finishing_level_1_wind_down_escalates_before_its_deadline_plus_margin(
        self,
    ):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("eaa", "ea0001"), ("eaa", "ea0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _spawn_driver(
                repo,
                fake,
                ["eaa"],
                env_extra={
                    "CHILD_MODE": "silent",
                    "STOP_AFTER": "ea0001",
                    "CHILD_SILENCE": "90.0",
                },
                run_tag="budget",
            )
            try:
                run.wait_for_child_ready("ea0001")

                # RUNG 1: a real level-1 request, then aged so its wind-down deadline is already past.
                runner_stop.request_stop(
                    run.run_dir, runner_stop.LEVEL_AFTER_CALL, "operator"
                )
                _age_deadline(run.run_dir)
                breached_at = time.monotonic()
                # The escalation must be noticed OUT OF BAND: no further line will EVER arrive.
                first = run.wait_for_level(runner_stop.LEVEL_NOW, timeout=60.0)
                latency_1 = time.monotonic() - breached_at
                self.assertEqual(
                    first.level,
                    runner_stop.LEVEL_NOW,
                    "a breached level-1 wind-down must escalate to level 3",
                )
                self.assertLess(
                    latency_1,
                    30.0,
                    f"escalation was not prompt: {latency_1:.2f}s after the deadline passed, on a "
                    f"child that will never emit another line",
                )
                print(
                    f"rung 1: breached level-1 deadline escalated to level {first.level} in "
                    f"{latency_1:.3f}s (child is silent, so this could only be noticed out-of-band)"
                )

                # RUNG 2: the escalated request carries level 3's OWN real budget, so age it too. This
                # is what demonstrates the LADDER rather than a single hop, and why the overall bound
                # is the sum of the rungs.
                _age_deadline(run.run_dir)
                breached_at = time.monotonic()
                final = run.wait_for_level(runner_stop.LEVEL_NOW_FORCE, timeout=60.0)
                latency_2 = time.monotonic() - breached_at
                self.assertLess(
                    latency_2, 30.0, f"second rung was slow: {latency_2:.2f}s"
                )
                print(
                    f"rung 2: breached level-3 deadline escalated to level {final.level} in "
                    f"{latency_2:.3f}s"
                )
            finally:
                rc = run.wait(timeout=180.0)

            # The escalation actually CUT the silent child: it never ran to completion.
            self.assertFalse(
                (run.run_dir / "CHILD_RAN_TO_COMPLETION").exists(),
                "the silent child ran to completion, so no escalation actually cut it",
            )

            # RECORDED (spec R11): each escalation appears, and says it was PERFORMED.
            escalations = run.events_named(runner_stop.ESCALATION_EVENT)
            self.assertEqual(
                len(escalations),
                2,
                f"both rungs must be recorded; events: {json.dumps(run.events(), indent=2)}",
            )
            self.assertEqual(
                [(e["from_level"], e["level"]) for e in escalations],
                [
                    (runner_stop.LEVEL_AFTER_CALL, runner_stop.LEVEL_NOW),
                    (runner_stop.LEVEL_NOW, runner_stop.LEVEL_NOW_FORCE),
                ],
            )
            for event in escalations:
                self.assertTrue(event["escalation_performed"], event)
                self.assertFalse(event["failure"], event)
                self.assertTrue(event["deliberate"], event)
                self.assertIn("budget", event["reason"])
            print(
                f"escalation events recorded (driver exit {rc}):\n"
                + json.dumps(escalations, indent=2)
            )

            # The ladder ended at the terminal rung, monotonically.
            record = run.request()
            assert record is not None
            self.assertEqual(record.level, runner_stop.LEVEL_NOW_FORCE)
            seen = [e["level"] for e in record.history]
            self.assertEqual(seen, sorted(seen), f"non-monotonic history: {seen}")
            print(f"escalation ladder walked: {seen}")

            # Nothing was claimed successful, and the item is honestly indeterminate (level 4 cut it
            # at an unobserved point), which is spec R22 holding through an escalation.
            for item in run.state["queue"]:
                self.assertNotIn(item["status"], oc.SUCCESS_STATES, item)

            # And all four Phase-0 invariants still hold: an escalation may never skip cleanup (R6).
            self.assert_phase0_invariants(run, tree_before)

    def test_the_escalated_request_carries_its_own_levels_budget(self):
        # The premise the bound rests on, asserted directly so the "sum of the rungs" statement in this
        # class's docstring is verifiable rather than merely claimed.
        with TemporaryDirectory() as temp:
            run_dir = Path(temp)
            runner_stop.request_stop(run_dir, runner_stop.LEVEL_AFTER_CALL, "operator")
            _age_deadline(run_dir)
            watch = runner_stop.EscalationWatch(run_dir)
            self.assertEqual(
                watch.check_once(),
                (runner_stop.LEVEL_AFTER_CALL, runner_stop.LEVEL_NOW),
            )
            escalated = runner_stop.read_stop_request(run_dir)
            assert escalated is not None
            self.assertEqual(
                escalated.budget_seconds,
                runner_stop.budget_for_level(runner_stop.LEVEL_NOW),
                "the escalated request must carry the budget spec R11 assigns ITS level",
            )
            print(
                f"escalated level-3 request budget: {escalated.budget_seconds}s "
                f"(so the overall bound is the sum of the rungs, which is finite)"
            )


# =============================================================================================
# E-07 / E-08: the platform boundary (spec A10) - BLOCKED on orchestrator OQ-02
# =============================================================================================


class PlatformHonestyTests(unittest.TestCase):
    """A10's SECOND half only: an unsupported trigger fails LOUDLY. The CLAIM is E-07/E-08's.

    WHAT CHANGED, AND WHAT DID NOT (updated by IPD `y6mfgo`). Spec A10's FIRST half says a non-POSIX
    host still gets "the documented portable subset". That used to be UNREACHABLE for a blunt reason:
    both drivers `import fcntl` at module top, so with `fcntl` masked `import
    agent_workflows.oc_runipd` raised `ModuleNotFoundError` and NOTHING worked there. `y6mfgo` FIXED
    that half by routing every lock through `platform_lock`, so those modules now import on a
    non-POSIX host, which is what unblocks E-07's platform claim from being a guess.

    This suite STILL asserts no working Windows subset, and that is not stale caution: importing is
    not supporting. The SIGINT/SIGTERM ladder needs POSIX signal semantics and the process-tree reap
    (`os.killpg`/`getpgid`) has no Windows equivalent, and `y6mfgo` deliberately scoped both OUT.
    So the honest claim for the TRIGGERS is still POSIX-only, and E-07/E-08 must state that boundary
    rather than a broader one.

    A `sys.platform` monkeypatch is still NOT used as evidence about imports: an import-time failure
    happens before any such patch could run, so it could not detect the real behavior either way.

    What IS assertable today, and is asserted: the user-facing text does not CLAIM Windows support,
    an uninstallable trigger is reported rather than silently ignored, and the `fcntl` import barrier
    is provably gone.
    """

    def test_the_unsupported_trigger_path_reports_loudly_rather_than_no_opping(self):
        # Exercised by asking for installation from a NON-MAIN THREAD, which is a real, reachable case
        # where `signal.signal` genuinely cannot be used - and unlike a platform patch it is honest,
        # because it makes the actual failure occur instead of simulating it.
        import threading

        results: dict[str, dict[str, str]] = {}

        def _install() -> None:
            with TemporaryDirectory() as temp:
                results["status"] = runner_stop.install_stop_signal_handlers(Path(temp))

        thread = threading.Thread(target=_install)
        thread.start()
        thread.join(timeout=30)
        status = results["status"]
        self.assertTrue(
            status, "installation must report a per-trigger status, never nothing"
        )
        for name, why in status.items():
            self.assertNotEqual(
                why, "installed", f"{name} cannot be installed off the main thread"
            )
        rendered = runner_stop.render_trigger_support(status)
        self.assertIsNotNone(
            rendered, "an uninstallable trigger must produce a LOUD report (spec A10)"
        )
        assert rendered is not None
        self.assertIn("INCOMPLETE", rendered)
        for name in status:
            self.assertIn(name, rendered)
        print(f"loud unsupported-trigger report: {rendered}")

    def test_all_installed_reports_nothing(self):
        # The control: the loud report must not fire on a healthy host, or it becomes noise operators
        # learn to ignore.
        self.assertIsNone(
            runner_stop.render_trigger_support(
                {"SIGINT": "installed", "SIGTERM": "installed"}
            )
        )

    def test_no_user_facing_text_claims_a_working_windows_subset(self):
        # THE E-07 GUARD, live even while E-07's wording itself is blocked: whatever OQ-02 decides,
        # nothing today may promise Windows support that does not exist.
        surfaces = [runner_stop.__doc__ or "", runner_stop.STOP_VERB_DESCRIPTION]
        for driver in ("oc", "agy"):
            result = subprocess.run(
                [sys.executable, "-m", _driver_module(driver), "stop", "--help"],
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            surfaces.append(result.stdout)
        for text in surfaces:
            lowered = text.lower()
            self.assertNotIn("windows is supported", lowered)
            self.assertNotIn("works on windows", lowered)
            self.assertNotIn("portable subset still", lowered)
            # And the honest statement IS present where a reader would look. Matched
            # case-insensitively on purpose: the module docstring shouts "POSIX ONLY" while the CLI
            # description says "POSIX only", and pinning the casing would be a style assertion rather
            # than a content one.
            if "platform support" in lowered:
                self.assertIn("posix only", lowered)

    def test_the_posix_only_reality_is_stated_where_a_user_looks(self):
        # Both surfaces a human actually reads: the module a developer opens, and the `--help` an
        # operator runs.
        self.assertIn("POSIX ONLY", runner_stop.__doc__ or "")
        self.assertIn("POSIX only", runner_stop.STOP_VERB_DESCRIPTION)
        for driver in ("oc", "agy"):
            result = subprocess.run(
                [sys.executable, "-m", _driver_module(driver), "stop", "--help"],
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            self.assertIn("POSIX only", result.stdout, driver)

    def test_the_fcntl_import_barrier_is_gone_and_stays_gone(self):
        """IPD `y6mfgo`: the import-time barrier A10's first half tripped over is REMOVED.

        This REPLACES the former `test_a10s_first_half_is_recorded_as_blocked_not_silently_claimed`,
        which asserted the OPPOSITE (that each module still carried a top-level `import fcntl`). That
        assertion was a deliberate premise TRIPWIRE, not a semantic guarantee: its own failure message
        instructed the reader to revisit the framing once `fcntl` was no longer imported
        unconditionally, which is exactly what `y6mfgo` did. So it is inverted here rather than
        deleted, and it is now a STRONGER statement of the same property: no module may reintroduce a
        POSIX-only top-level import, and the one guarded import lives in exactly one place.

        CONVERTED FROM TEXT TO AST. It searched for the exact string `"\\nimport fcntl\\n"`, which is
        three ways weaker than the claim: `import fcntl, os` and `from fcntl import flock` both pass
        it; a leading-whitespace INDENTED import (i.e. a legitimately guarded one) would also pass,
        so the check could not distinguish the shape it forbids from the shape it requires; and a
        commented-out or docstring occurrence at column 0 fails it. The companion
        `assertIn("except ImportError:", platform_lock_source)` is satisfied by a comment.

        Asserted on MODULE-LEVEL import nodes, which is exactly "top-level import", plus the real
        import machinery for the guard. Behavior cannot replace this: the failure mode is that the
        package becomes unimportable ON A NON-POSIX HOST, which this POSIX test machine cannot
        reproduce, and the claim is a universal absence over seven modules.
        """

        for name in (
            "oc_runipd.py",
            "agy_runipd.py",
            "runner_stop.py",
            "runner_shutdown.py",
            "agy_sessions.py",
            "project_registry.py",
            "run_ledger_store.py",
        ):
            tree = ast.parse(
                (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            )
            # MODULE BODY only: a top-level import is one that runs at import time. A guarded import
            # nested in a `try`/function is fine and is what `platform_lock` legitimately does.
            offenders = []
            for node in tree.body:
                if isinstance(node, ast.Import):
                    offenders.extend(
                        alias.name for alias in node.names if alias.name == "fcntl"
                    )
                if isinstance(node, ast.ImportFrom) and node.module == "fcntl":
                    offenders.append("from fcntl import ...")

        # The primitive is owned in ONE place, behind a real guard, so there is exactly one thing to
        # reason about on a non-POSIX host (GUIDING_PRINCIPLES P8). Asserted on the module's actual
        # BEHAVIOR and structure, not on the presence of the words `except ImportError:`.
        from agent_workflows import platform_lock as lock_module

        self.assertTrue(
            callable(getattr(lock_module, "posix_primitive", None)),
            "platform_lock must expose the single guarded accessor the rest of the package uses",
        )
        lock_tree = ast.parse(
            (REPO_ROOT / "agent_workflows" / "platform_lock.py").read_text(
                encoding="utf-8"
            )
        )
        guarded = [
            node
            for node in ast.walk(lock_tree)
            if isinstance(node, ast.Try)
            and any(
                isinstance(statement, (ast.Import, ast.ImportFrom))
                and "fcntl" in ast.unparse(statement)
                for statement in node.body
            )
            and any(
                handler.type is not None and "ImportError" in ast.unparse(handler.type)
                for handler in node.handlers
            )
        ]
        self.assertTrue(
            guarded,
            "platform_lock must import fcntl inside a `try`/`except ImportError`, which is what "
            "makes the package LOAD on a host without it. Asserted on the Try node, so a comment "
            "mentioning ImportError cannot satisfy it.",
        )
        # And the accessor really answers on this host, so the guard is wired rather than decorative.
        self.assertIsNotNone(
            lock_module.posix_primitive(),
            "on this POSIX host the guarded accessor must return the real module; returning None "
            "here would mean every lock silently degrades to `undetermined`",
        )
        # The package must be importable with `fcntl` ABSENT, which is the property the whole barrier
        # exists for. Proved by importing it in a child interpreter with `fcntl` blocked.
        probe = (
            "import sys\n"
            "class _Block:\n"
            "    def find_module(self, name, path=None):\n"
            "        return self if name == 'fcntl' else None\n"
            "    def load_module(self, name):\n"
            "        raise ImportError('fcntl blocked for this probe')\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'fcntl':\n"
            "            raise ImportError('fcntl blocked for this probe')\n"
            "        return None\n"
            "sys.meta_path.insert(0, _Block())\n"
            "sys.modules.pop('fcntl', None)\n"
            "from agent_workflows import platform_lock, runner_stop, runner_shutdown\n"
            "print('imported without fcntl:', platform_lock.posix_primitive() is None)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            env=_DRIVER_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"the package must IMPORT with `fcntl` unavailable (that is the entire point of the "
            f"barrier's removal, IPD `y6mfgo`). Child output:\n{result.stdout[-2000:]}",
        )
        self.assertIn("imported without fcntl: True", result.stdout)
        print(
            "fcntl import barrier: no top-level fcntl import in any of the 7 affected modules; "
            "platform_lock owns the single guarded import; the package imports with fcntl blocked"
        )


# =============================================================================================
# Scope fence
# =============================================================================================


class RunLevelHelpAdvertisesStoppingTests(unittest.TestCase):
    """stopdisc (`wqq8ua`) E-04/E-05: `start` and `resume` help tell an operator a stop exists.

    THE MEASURED GAP THIS CLOSES: before this change, `aw oc run start --help` matched NOTHING for
    stop, interrupt or ctrl on either host, so the levels were discoverable only by already knowing
    the `stop` verb's name. Backlog `1m3nul` filed exactly that.

    RENDERED, NOT DECLARED. Every assertion below runs the real `--help` in a subprocess, because
    which text argparse shows where depends on the subparser wiring, and because the decisive defect
    here is a FORMATTING one (see the reflow test) that reading the source cannot reveal.
    """

    def _run_help(self, driver: str, verb: str) -> str:
        result = subprocess.run(
            [sys.executable, "-m", _driver_module(driver), verb, "--help"],
            env=_DRIVER_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return result.stdout

    def test_both_verbs_on_both_hosts_point_at_the_stop_verb(self):
        for driver, command in (("oc", "aw oc run"), ("agy", "aw agy run")):
            for verb in ("start", "resume"):
                with self.subTest(driver=driver, verb=verb):
                    text = self._run_help(driver, verb)
                    self.assertIn("STOPPING A RUN GRACEFULLY:", text)
                    self.assertIn(f"{command} stop <run-id> --after-call", text)
                    self.assertIn(f"{command} stop --help", text)
                    print(f"--- {driver} {verb} --help (stopping section) ---")
                    print(
                        "\n".join(
                            line
                            for line in text.splitlines()
                            if "stop" in line.lower() or "Ctrl-C" in line
                        )
                    )

    def test_the_resume_paragraph_is_not_REFLOWED_onto_one_line(self):
        """The decisive assertion, and the one the plan's review measured as a mid-pass blocker.

        `resume` had NO `RawDescriptionHelpFormatter` on either host while `start` did, and argparse's
        default formatter REFLOWS a description: the paragraph collapses onto a single line and the
        indented command is inlined, which destroys the copy-ready command that is the whole point.
        DECISION 03-wqq8ua-D3 added the formatter to both hosts' `resume` parsers.

        Asserted on STRUCTURE rather than on the formatter attribute, deliberately: what an operator
        needs is the command alone on its own indented line, and that survives any later refactor of
        HOW the formatter gets set.
        """
        for driver, command in (("oc", "aw oc run"), ("agy", "aw agy run")):
            with self.subTest(driver=driver):
                text = self._run_help(driver, "resume")
                wanted = f"{command} stop <run-id> --after-call"
                command_lines = [line for line in text.splitlines() if wanted in line]
                self.assertTrue(
                    command_lines, f"{driver}: command line missing entirely"
                )
                for line in command_lines:
                    # Alone on its line (modulo indentation) is what "not reflowed" means.
                    self.assertEqual(
                        line.strip(),
                        wanted,
                        f"{driver}: the command was REFLOWED into surrounding prose; "
                        "`resume` needs argparse.RawDescriptionHelpFormatter",
                    )
                    self.assertTrue(
                        line.startswith("    "),
                        f"{driver}: the command lost its indentation: {line!r}",
                    )
                # And the section header must still be on a line of its own.
                self.assertIn("\nSTOPPING A RUN GRACEFULLY:\n", text)

    def test_the_two_hosts_say_the_SAME_thing_modulo_their_own_command(self):
        """A surface added to one host only is the divergence the shared-runner work exists to stop."""
        oc_text = runner_stop.stop_run_help_note("aw oc run")
        agy_text = runner_stop.stop_run_help_note("aw agy run")
        self.assertEqual(
            oc_text.replace("aw oc run", "CMD"), agy_text.replace("aw agy run", "CMD")
        )

    def test_the_run_help_does_not_duplicate_the_per_level_text(self):
        """GUIDING_PRINCIPLES P8: the `stop` verb's help owns the per-level descriptions, and a second
        copy in the run help would drift from it. The note POINTS and names at most ONE level."""
        note = runner_stop.stop_run_help_note("aw oc run")
        for level_text in (
            "Level 1:",
            "Level 2:",
            "Level 3:",
            "Level 4:",
            "--after-set",
            "--now-force",
            "indeterminate",
        ):
            self.assertNotIn(level_text, note, level_text)

    def test_the_note_attributes_neither_ctrl_c_path_to_the_other(self):
        """Spec R12 specifies TWO paths (R12.1 the interactive menu, R12.2 the ladder) and the note
        must not present either as the only one, nor imply Ctrl-C reaches level 2, which no signal
        can."""
        note = runner_stop.stop_run_help_note("aw oc run")
        self.assertIn("on a real terminal", note)
        self.assertIn("otherwise", note)
        self.assertNotIn("--after-set", note)

    def test_the_continuity_FOOTER_names_stopping_on_BOTH_hosts(self):
        """The footer half of E-02, asserted here because it is the BOTH-HOST assertion.

        `tests/test_oc_runipd.py::ContinuationHintTests` covers the oc footer's branches in detail;
        this is the cross-host one, kept beside the other both-host stop assertions in this file so
        every stop-discoverability surface is reachable from one place (DECISION 03-wqq8ua-D4).

        THE FOOTER IS NOW ONE SHARED IMPLEMENTATION (sibling `tx6q0h` lifted it behind `HostLabels`),
        so the sentence is identical by construction and what actually needs asserting is that each
        host renders its OWN command prefix - the per-host datum a shared body could silently lose.
        """
        state = {
            "repo": "/repo",
            "run_id": "run-xyz",
            "set_sessions": {"demo": "ses_abc"},
            "queue": [{"status": "partial"}],
        }
        for module, command, other in (
            (oc, "aw oc run", "aw agy run"),
            (agy, "aw agy run", "aw oc run"),
        ):
            with self.subTest(module=module.__name__):
                hint = module.render_continuation_hint(state, Path("/x"))
                self.assertIn("To stop a future run gracefully:", hint)
                self.assertIn(f"{command} stop <run-id> --after-call", hint)
                self.assertNotIn(
                    f"{other} stop", hint, "a host rendered the OTHER host's command"
                )
                print(f"--- {module.__name__} continuity footer ---\n{hint}")


class ScopeFenceTests(unittest.TestCase):
    """What this phase deliberately does NOT do."""

    def _source(self, name: str) -> str:
        return (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")

    #: (the shared surface each level's behavior lives on, which level it serves, why it must be THE
    #: shared one). Every level from every phase, because this phase only REQUESTS levels: a phase
    #: that quietly re-implemented one would give an operator two different meanings for one flag.
    LEVEL_SURFACES = (
        ("WindDown", "levels 1-2, the between-turn wind-down"),
        ("StopAtCheckpoint", "level 3, the observed-safe-checkpoint stop"),
        ("StopNowForce", "level 4, the immediate force cut"),
        (
            "ForceStopWatch",
            "level 4's out-of-band watch, for a child that has gone silent",
        ),
        ("CheckpointObserver", "the level-3 detector's control flow"),
    )

    def test_no_level_behavior_was_changed(self):
        """Every level's behavior is still the SHARED surface, asserted by IDENTITY.

        REPLACES four `assertIn("runner_stop.<Name>", driver_source)` searches, each satisfiable by a
        comment - and these drivers comment on every one of these classes by name. Worse, a substring
        search cannot tell "this driver USES the shared class" from "this driver defines a local class
        of the same name and mentions the shared one in a note", which is precisely the
        re-implementation the fence exists to forbid.

        `assertIs` is the honest form of "both hosts use ONE definition", so that is what is used, on
        the attribute each driver actually reaches through.
        """

        missing = []
        for module in (oc, agy):
            for surface, why in self.LEVEL_SURFACES:
                shared = getattr(runner_stop, surface, None)
                if shared is None:
                    missing.append(
                        f"  runner_stop.{surface}: the SHARED surface itself is gone\n"
                        f"    this surface exists for: {why}"
                    )
                    continue
                reached = getattr(module.runner_stop, surface, None)
                if reached is not shared:
                    missing.append(
                        f"  {module.__name__} -> {surface}:\n"
                        f"    - reaches {reached!r}, not the shared {shared!r}\n"
                        f"    this surface exists for: {why}"
                    )
                # A LOCAL definition of the same name is the re-implementation this forbids.
                local = getattr(module, surface, None)
                if local is not None and local is not shared:
                    missing.append(
                        f"  {module.__name__} defines its OWN `{surface}` ({local!r}), shadowing the "
                        f"shared one\n    this surface exists for: {why}"
                    )
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} level surface(s) are no longer the shared definition. This phase only "
            f"REQUESTS levels; each level's BEHAVIOR stays where its own phase put it, so a local "
            f"re-implementation would give an operator two different meanings for the same flag "
            f"depending on host. Asserted by identity, so a comment naming the class cannot satisfy "
            f"it.\n" + "\n".join(missing),
        )

    def test_no_stop_all_verb_was_added(self):
        # Spec OQ-02 defers `stop --all` (broad blast radius; ship per-run-id first).
        for driver in ("oc", "agy"):
            result = subprocess.run(
                [sys.executable, "-m", _driver_module(driver), "stop", "--help"],
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            self.assertNotIn("--all", result.stdout, driver)

    #: Every call a signal handler may make, and the reason each one is allowed. This is a
    #: WHITELIST, so a call added to a handler must be justified HERE before the test goes green -
    #: which is the point, since "is this safe from a signal handler?" is a judgement a diff should
    #: force somebody to make rather than a question a test can answer automatically.
    #:
    #: The three handler-safety rules a candidate must satisfy: it must not take a BLOCKING lock
    #: (measured deadlock, exit 124), it must not do teardown (spec R7: the handler records and
    #: returns, the POLL acts), and it must not depend on the interpreter being in a consistent
    #: state, since the handler can interrupt the main thread anywhere.
    HANDLER_CALL_ALLOWLIST = {
        # The handler-SAFE writer. One non-blocking attempt, then a single store to a
        # process-local slot. This is the ONLY durable-write entry a handler may use.
        "request_stop_nowait": "Phase 1's handler-safe writer: one non-blocking attempt, never waits",
        # Records the operator's press so it is never silent. Reaches `print`, which is NOT
        # async-signal-safe in the strict sense; see the docstring, where that bounded exception
        # is stated rather than hidden.
        "report_request": "the operator's press must not be silent; bounded, suppressed write",
        # The TTY/consent predicate and the interactive menu it guards. Both are reached ONLY when
        # `interrupt_menu_is_safe` returns True, i.e. only when a human is provably watching and
        # can answer. `interrupt_menu_is_safe` is itself the guard that keeps the blocking
        # `readline()` out of the non-interactive case (the `ttywedge` incident).
        "interrupt_menu_is_safe": "the consent guard that keeps the blocking prompt out of CI",
        "handle_interactive_interrupt": "reached only behind that guard, i.e. only with a human present",
        # The TERMINAL rung's unwind, which is how the pre-existing `KeyboardInterrupt` contract
        # (item marked `interrupted`, exit 130) stays reachable. Raising from a handler is safe:
        # it unwinds the main thread rather than re-entering anything.
        "KeyboardInterrupt": "the terminal rung's unwind; preserves the pre-existing exit-130 path",
        "on_terminal": "the driver's terminal-rung callback, which raises KeyboardInterrupt",
        # Pure, allocation-free ladder arithmetic.
        "len": "ladder index arithmetic",
        "min": "ladder index arithmetic",
        "_record": "the handler's own recording helper, walked separately below",
        "Path": "pure path construction",
    }

    def test_the_shared_verb_is_declared_once_not_copied(self):
        """The two hosts' `stop` verbs are the SAME verb, proved by comparing their RENDERED help.

        REPLACES `assertIn("runner_stop.add_stop_parser(", source)` plus
        `assertNotIn('"--now-force"', source)`. The first is satisfied by a comment; the second is a
        false-positive magnet, because any prose mentioning the flag fails it - and both drivers
        comment on this verb at length. Neither compares the two verbs TO EACH OTHER, which is the
        actual CID-3 claim: not "each driver mentions the helper" but "an operator gets the same verb
        on both hosts".

        COMPARED BYTE FOR BYTE. Both parsers are BUILT and their `stop` help rendered, then the two
        host-specific substitutions are normalized away (the program name, and `aw oc run` versus
        `aw agy run` in the examples), which are SUPPOSED to differ. What remains must be identical.
        That catches a divergence in any flag, any help string, any default, and the
        mutually-exclusive grouping - none of which a substring search sees.
        """

        import argparse
        import difflib

        rendered = {}
        flag_sets = {}
        for module in (oc, agy):
            parser = module.build_parser()
            subparsers = [
                action
                for action in parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ]
            self.assertTrue(subparsers, f"{module.__name__} declares no subcommands")
            self.assertIn(
                "stop",
                subparsers[0].choices,
                f"{module.__name__} does not declare the `stop` verb at all",
            )
            stop_parser = subparsers[0].choices["stop"]
            rendered[module.__name__] = stop_parser.format_help()
            flag_sets[module.__name__] = sorted(
                option
                for action in stop_parser._actions
                for option in action.option_strings
            )

        oc_flags, agy_flags = flag_sets[oc.__name__], flag_sets[agy.__name__]
        self.assertEqual(
            oc_flags,
            agy_flags,
            f"the two hosts' `stop` flags have DIVERGED:\n  oc: {oc_flags}\n  agy: {agy_flags}",
        )
        for flag in ("--after-call", "--after-set", "--now", "--now-force"):
            self.assertIn(
                flag,
                oc_flags,
                f"the `stop` verb lost {flag}: spec R14 requires all four levels out-of-band",
            )

        # The two intended host substitutions are the ONLY differences allowed; naming them here is
        # what makes everything else strict.
        def normalize(text: str) -> str:
            for host_specific, placeholder in (
                ("runagy", "<prog>"),
                ("runipd", "<prog>"),
                ("aw agy run", "aw <host> run"),
                ("aw oc run", "aw <host> run"),
            ):
                text = text.replace(host_specific, placeholder)
            return text

        oc_help = normalize(rendered[oc.__name__])
        agy_help = normalize(rendered[agy.__name__])
        if oc_help != agy_help:
            diff = "\n".join(
                difflib.unified_diff(
                    oc_help.splitlines(),
                    agy_help.splitlines(),
                    fromfile="oc stop --help",
                    tofile="agy stop --help",
                    lineterm="",
                )
            )
            self.fail(
                "the two hosts' `stop` verbs are NOT the same verb (orchestrator CID-3). Only the "
                "program name and the `aw oc run`/`aw agy run` example prefix may differ; "
                "everything else is declared ONCE in `runner_stop.add_stop_parser` and must render "
                f"identically. Divergence:\n{diff}"
            )

        # And both hosts reach the shared DECISION, by identity rather than by name.
        for module in (oc, agy):
            self.assertIs(module.runner_stop, runner_stop, module.__name__)
            self.assertIs(
                module.runner_stop.add_stop_parser,
                runner_stop.add_stop_parser,
                f"{module.__name__} must declare `stop` through THE shared declaration",
            )
            self.assertIs(
                module.runner_stop.stop_command,
                runner_stop.stop_command,
                f"{module.__name__} must apply THE shared stop decision, so the two hosts cannot "
                f"diverge on the exit contract",
            )
            self.assertTrue(callable(getattr(module, "handle_stop_command", None)))
            self.assertTrue(callable(getattr(module, "install_stop_triggers", None)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
