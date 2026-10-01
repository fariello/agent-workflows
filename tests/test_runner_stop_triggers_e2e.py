#!/usr/bin/env python3
"""End-to-end stop trigger behaviors: real SIGTERM and terminal-rung SIGINTs.

Spec `c4gd2h` R13/A3 and terminal-rung interrupt contracts, restored as signal-driven
behavioral tests against a real spawned driver.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


from agent_workflows import oc_runipd as oc
from agent_workflows import runner_shutdown, runner_stop
from tests.support import REPO_ROOT
from tests.test_oc_runipd import _CONFORMING_PLAN

_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

# ---------------------------------------------------------------------------------------------
# The fake child.
#
# For the TRIGGER tests the interesting child is one that runs LONG ENOUGH to be signalled and that
# ANNOUNCES when it is ready, so a test never has to sleep-and-hope before delivering a signal (the
# orchestrator's anti-greenwash contract forbids a wall-clock sleep defining a boundary).
#
#   `ready`       - emits a non-checkpoint event, drops a READY marker file, then emits COMPLETED
#                   events slowly forever.
#   `checkpoints` - like `ready` but every event is a completed checkpoint, so a level-3 request
#                   lands at the very next line.
#   `silent`      - emits a non-checkpoint event, drops READY, then goes COMPLETELY quiet.
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
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    for order, (setid, id6) in enumerate(items, start=1):
        name = f"20260830-{setid}-{order:02d}-{id6}-plan.ipd.md"
        plan_text = _CONFORMING_PLAN.format(id6=id6)
        plan_text = re.sub(
            r"^- Set:\s*.*$", f"- Set: {setid}", plan_text, flags=re.MULTILINE
        )
        plan_text = re.sub(
            r"^- Order:\s*.*$", f"- Order: {order}", plan_text, flags=re.MULTILINE
        )
        (pending / name).write_text(plan_text, encoding="utf-8")
    (repo / "README").write_text("triggers\n", encoding="utf-8")
    _git(repo, "add", "-A")
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
        signals are not queued, so back-to-back deliveries COALESCE into one handler invocation.
        Tests that merely need the run to END must therefore escalate deliberately rather than assume
        a burst walked the ladder.
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


class _InvariantAssertions(unittest.TestCase):
    """The four Phase-0 clean-shutdown invariants, OBSERVED rather than asserted from code.

    Identical in shape to the level-3/level-4 suites deliberately: spec R1-R4 hold at EVERY level, so
    a new TRIGGER must not be allowed to reach a level in a way that skips them. R4 is asserted as
    "the dirty set never SHRANK" because Phase 0's recorded semantics are observe-and-report; demanding
    a clean tree would assert a behavior the shared routine explicitly does not have.
    """

    def assert_phase0_invariants(self, run: _SignalledRun, tree_before: str) -> None:
        # R1: no descendant of the driver survives, observed in the real process table.
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
                except BlockingIOError:
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


class PreExistingInterruptContractTests(_InvariantAssertions):
    """The pre-existing `KeyboardInterrupt` behaviors a SIGINT handler SUPPRESSES.

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
