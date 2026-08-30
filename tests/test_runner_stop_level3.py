#!/usr/bin/env python3
"""runstop Phase 3 (`foi1b3`): level 3, STOP-NOW at the next OBSERVED safe checkpoint.

Spec `c4gd2h` R10/R11/R18/R21/R22, acceptance A3.

WHAT MAKES LEVEL 3 DIFFERENT FROM LEVELS 1-2, and therefore what these tests must prove. Levels 1
and 2 stop BETWEEN turns, so their correctness is about the dequeue decision. Level 3 stops INSIDE a
turn, so its correctness is about two things instead:

1. WHEN the turn is cut. Spec R10 forbids defining that instant by elapsed time, so it is defined by
   an OBSERVATION of the child's own event stream: after a COMPLETED tool/step event, before the next
   is dispatched. The behavioral tests below script a fake child so that the FIRST completed event
   after the stop request is at a KNOWN index, then assert the driver stopped at exactly that index.
2. WHAT IS RECORDED. A level-3 stop must be recorded stopped/incomplete with KNOWN certainty - never
   `unknown_outcome` (level 4's, spec-owned), never a success (R22), and CRUCIALLY never
   `failed-safely`, which is what the un-intercepted `reconcile_disposition` fallback produces for a
   deliberate stop.

THE THREE OUTPUT MODES ARE NOT DECORATION. `render_event` is called only under
`output_mode == "clean"`, so a checkpoint detector built on it would silently never fire under `raw`
or `quiet` - the feature would depend on an unrelated display flag. Every mode is therefore driven
end-to-end below.

THE SCHEMAS ARE PER-DRIVER. `oc` completion is `tool_use` + `part.state.status == "completed"` (or
`step_finish`); `agy` completion is `step_update` + `state == "DONE"`. The cross-schema tests assert
each detector REJECTS the other driver's completion line, so a single-schema implementation fails
here instead of silently never firing on one driver.

VERIFIED EVENT VOCABULARY, not assumed. Parsing the real session JSONL cited by the spec's OQ-01
resolution (`.aw/records/runs/run-20260829T053827Z-2084502/sessions/01-jolfpj-attempt-1.jsonl`) gives
122 `step_start`, 122 `step_finish`, 135 `tool_use` (every one `part.state.status == "completed"`),
and 85 `text`. The fake children below emit those exact shapes.

WHAT THE STOP MECHANISM ACTUALLY IS, so no test here overstates it. The child is a one-shot
`opencode run` / `agy` subprocess with NO cooperative stop channel, so stopping the turn IS
TERMINATION - at an instant chosen by observation. Levels 3 and 4 share that mechanism and differ
only in WHEN it is issued. "KNOWN" certainty therefore means no PREVIOUSLY OBSERVED operation was cut
mid-flight, NOT that the agent finished tidily.

THE FOUR PHASE-0 INVARIANTS are asserted on the behavioral tests, per the inherited contract, with
R4 asserted as "UNCHANGED by cleanup" rather than "clean": Phase 0 (`2ouj70`) made R4
observe-and-report, so demanding a clean tree would assert a behavior the shared routine explicitly
does not have.
"""

from __future__ import annotations

import fcntl
import inspect
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
# It emits a SCRIPTED event sequence in the real vocabularies, requests a level-3 stop partway
# through, and then keeps emitting. The script is chosen so that the FIRST completed event after the
# request is at a fixed index, which is what lets the tests assert WHERE the driver stopped rather
# than merely that it stopped.
#
# WHY THE STOP INDEX IS DETERMINISTIC AND NOT A RACE. The child writes the stop request BEFORE
# emitting event 3, and the driver can only read event 3 after the child wrote it, so by the time the
# driver processes event 3 the request is durably visible. Events 1-4 are deliberately NON-checkpoints
# (`step_start`, `text`, `text`, a `tool_use` whose status is `running`), so no checkpoint can be
# reached earlier even if the request became visible on event 1. Event 5 is the first COMPLETED event,
# so the stop index is always 5. Events 6+ exist only to prove they are never consumed.
# ---------------------------------------------------------------------------------------------

_FAKE_CHILD = r'''#!/usr/bin/env python3
import json, os, pathlib, re, sys, tempfile, time

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
# in a tracked file (same convention as tests/test_oc_runipd.py and test_runner_stop_levels12.py).
_fallback_session = "ses" + "_" + "level3"
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
    # `text` in the oc vocabulary; for agy an ACTIVE `step_update`, which is explicitly NOT a
    # completion (only DONE is).
    if SCHEMA == "oc":
        return {"type": "text", "part": {"text": text}}
    return {"type": "step_update", "step_update": {"state": "ACTIVE", "step_type": "tool",
                                                   "tool_info": {"name": "run_command"}}}


def running_tool():
    # A tool event that is NOT completed. Stopping here would cut a live operation, so the driver
    # must not treat it as a checkpoint.
    if SCHEMA == "oc":
        return {"type": "tool_use",
                "part": {"type": "tool", "tool": "bash", "state": {"status": "running"}}}
    return {"type": "step_update", "step_update": {"state": "ACTIVE", "step_type": "tool",
                                                   "tool_info": {"name": "bash"}}}


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


def write_stop_request(level, budget_seconds=None):
    """Record a stop request; optionally with a SHORT INJECTED budget/deadline.

    A short budget is written directly (same record shape `runner_stop._parse` reads) so the
    bounded-wait test cannot pass merely by waiting out the real multi-minute level-3 budget.
    """
    run_dir = pathlib.Path(os.environ["RUN_DIR"])
    run_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, os.environ["AW_REPO_ROOT"])
    from agent_workflows import runner_stop
    if budget_seconds is None:
        runner_stop.request_stop(run_dir, level, "test-operator")
        return
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    record = {
        "schema_version": 1,
        "level": level,
        "level_name": runner_stop.LEVEL_NAMES[level],
        "requested_at": now.isoformat(),
        "requester": "test-operator",
        "first_requested_at": now.isoformat(),
        "budget_seconds": float(budget_seconds),
        "deadline": (now + dt.timedelta(seconds=float(budget_seconds))).isoformat(),
        "history": [{"level": level, "at": now.isoformat(), "requester": "test-operator"}],
    }
    path = runner_stop.stop_request_path(run_dir)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, str(path))


def finish_turn():
    """Complete the turn as far as the driver can observe: move the plan, write the outcome JSON."""
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

if mode == "checkpoint" and id6 == target:
    # Events 1-4 are NON-checkpoints; event 5 is the first COMPLETED one, so the driver must stop
    # exactly there. Events 6+ must never be consumed.
    emit(step_start())                        # 1
    emit(not_a_checkpoint("thinking"))        # 2
    write_stop_request(int(os.environ.get("STOP_LEVEL", "3")))
    emit(not_a_checkpoint("still thinking"))  # 3
    emit(running_tool())                      # 4
    emit(completed_tool("read"))              # 5  <- the safe checkpoint
    # If the driver honored the stop it is already gone. Anything below is a defect witness.
    for extra in range(6, 12):
        emit(completed_tool("never-%d" % extra))
        time.sleep(0.05)
    (pathlib.Path(os.environ["RUN_DIR"]) / "CHILD_RAN_PAST_CHECKPOINT").write_text("yes")
    finish_turn()
    sys.exit(0)

if mode == "silent" and id6 == target:
    # The BOUNDED-WAIT case (spec R11): a level-3 stop with a SHORT injected deadline, then NO further
    # completed event and NO further output at all. A breach detector that only ran when the next line
    # arrived would never fire here, because no next line is ever sent.
    write_stop_request(3, budget_seconds=float(os.environ.get("STOP_BUDGET", "0.25")))
    emit(not_a_checkpoint("armed"))
    emit(not_a_checkpoint("going quiet"))
    time.sleep(float(os.environ.get("CHILD_SILENCE", "4.0")))
    sys.exit(0)

if os.environ.get("FAIL_FOR", "") == id6 and id6:
    # A genuinely failed turn: no outcome JSON, no plan move, nonzero exit. This is the CONTROL for
    # the disposition branch - it must still reconcile to `failed-safely`.
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
- 2026-08-30 created: level 3 test stub
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
    repo.mkdir()
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
    (repo / "README").write_text("level3\n", encoding="utf-8")
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
        self, repo: Path, returncode: int, stdout: str, stderr: str, elapsed: float
    ):
        self.repo = repo
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed
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
        started = {e["id6"] for e in self.events() if e.get("event") == "ipd-started"}
        return started


def _run_driver(
    repo: Path,
    fake: Path,
    selectors: list[str],
    *,
    env_extra: dict[str, str] | None = None,
    driver: str = "oc",
    output_mode: str = "clean",
    run_tag: str = "",
) -> _DriverRun:
    """Run the REAL driver to completion over the fake child, in a fresh run.

    `--no-isolate-worktree` / `--no-self-finalize` keep the test on the STOP behavior rather than
    dragging in worktree allocation and the lifecycle gates, which have their own suites.
    """

    module = (
        "agent_workflows.oc_runipd" if driver == "oc" else "agent_workflows.agy_runipd"
    )
    env = {**_DRIVER_ENV, "AW_REPO_ROOT": str(REPO_ROOT)}
    env.setdefault("SCHEMA", "oc" if driver == "oc" else "agy")
    if env_extra:
        env.update(env_extra)
    runs_dir = repo / ".aw" / "records" / "runs"
    existing = len([p for p in runs_dir.glob("run-*")]) if runs_dir.is_dir() else 0
    # The child needs RUN_DIR, but the run id is minted by the driver, so pin it.
    run_id = f"run-level3-{run_tag or driver}-{existing}"
    env["RUN_DIR"] = str(runs_dir / run_id)
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
    if output_mode == "raw":
        argv.append("--raw")
    elif output_mode == "quiet":
        argv.append("--quiet")
    if driver == "oc":
        argv += ["--opencode", os.fspath(fake)]
    else:
        argv += ["--agy", os.fspath(fake)]
    started = time.monotonic()
    result = subprocess.run(
        argv,
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
    )
    elapsed = time.monotonic() - started
    run = _DriverRun(repo, result.returncode, result.stdout, result.stderr, elapsed)
    if not run.run_id:
        run.run_id = run_id
        run.run_dir = runs_dir / run_id
    return run


class _InvariantAssertions(unittest.TestCase):
    """The four Phase-0 clean-shutdown invariants, OBSERVED rather than asserted from code."""

    def assert_phase0_invariants(self, run: _DriverRun, tree_before: str) -> None:
        # R1: no descendant of the driver survives, observed in the real process table. The match is
        # anchored to THIS run's private temp repo path (unique per test) so the assertion can never
        # implicate a concurrently running test's processes.
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
        # Reusing `runner_shutdown.KNOWN_ITEM_STATUSES` is deliberate: a level that invented a new
        # per-item status fails HERE instead of passing a test-local allowlist.
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

    def assert_no_unknown_outcome(self, run: _DriverRun) -> None:
        """Spec R18/R22: level 3's certainty is KNOWN, so `unknown_outcome` must not appear."""

        for item in run.state["queue"]:
            self.assertNotEqual(item["status"], "unknown_outcome", item)
        blob = json.dumps(run.state) + json.dumps(run.events())
        self.assertNotIn("unknown_outcome", blob)


# =============================================================================================
# E-01 / V-01: the observable safe checkpoint
# =============================================================================================


class SafeCheckpointDefinitionTests(unittest.TestCase):
    """The checkpoint predicate itself: what IS and IS NOT a safe checkpoint (spec R10)."""

    def test_oc_completed_tool_event_is_a_checkpoint(self):
        line = json.dumps(
            {
                "type": "tool_use",
                "part": {
                    "type": "tool",
                    "tool": "bash",
                    "state": {"status": "completed"},
                },
            }
        )
        self.assertTrue(runner_stop.is_oc_safe_checkpoint(line))

    def test_oc_step_finish_is_a_checkpoint(self):
        # `step_finish` is the cleaner completion signal than `step_start`, and the real session file
        # carries 122 of each, so both exist and only the FINISH one may count.
        self.assertTrue(
            runner_stop.is_oc_safe_checkpoint(
                json.dumps({"type": "step_finish", "part": {}})
            )
        )
        self.assertFalse(
            runner_stop.is_oc_safe_checkpoint(
                json.dumps({"type": "step_start", "part": {}})
            )
        )

    def test_a_non_completed_status_is_not_a_checkpoint(self):
        # Stopping on a live operation would cut it mid-flight, which is precisely what the
        # "completed" observation exists to prevent.
        for status in ("running", "pending", "error", "", None):
            line = json.dumps(
                {
                    "type": "tool_use",
                    "part": {
                        "type": "tool",
                        "tool": "bash",
                        "state": {"status": status},
                    },
                }
            )
            self.assertFalse(
                runner_stop.is_oc_safe_checkpoint(line), f"status={status!r}"
            )

    def test_a_malformed_or_missing_state_is_not_a_checkpoint(self):
        for payload in (
            {"type": "tool_use"},
            {"type": "tool_use", "part": {}},
            {"type": "tool_use", "part": {"state": "completed"}},
            {"type": "tool_use", "part": "completed"},
        ):
            self.assertFalse(
                runner_stop.is_oc_safe_checkpoint(json.dumps(payload)), payload
            )

    def test_a_partial_or_interleaved_line_is_not_a_checkpoint(self):
        # A truncated line must read as "not a checkpoint", never default to safe.
        partials = [
            '{"type": "tool_use", "part": {"state": {"sta',
            '{"type": "tool_use"',
            "",
            "   ",
            "not json at all",
            # An interleaved fragment: the tail of one record glued to the head of another.
            '"completed"}}}{"type": "step_finish"',
        ]
        for line in partials:
            self.assertFalse(runner_stop.is_oc_safe_checkpoint(line), repr(line))
            self.assertFalse(runner_stop.is_agy_safe_checkpoint(line), repr(line))

    def test_non_object_json_is_not_a_checkpoint(self):
        for line in ("[1, 2, 3]", '"completed"', "42", "null"):
            self.assertFalse(runner_stop.is_oc_safe_checkpoint(line), line)
            self.assertFalse(runner_stop.is_agy_safe_checkpoint(line), line)

    def test_agy_uses_its_own_schema_step_update_done(self):
        done = json.dumps(
            {
                "type": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_info": {"name": "run_command"},
                },
            }
        )
        self.assertTrue(runner_stop.is_agy_safe_checkpoint(done))
        for state in ("ACTIVE", "ERROR", "FAILED", ""):
            line = json.dumps({"type": "step_update", "step_update": {"state": state}})
            self.assertFalse(runner_stop.is_agy_safe_checkpoint(line), state)

    def test_the_two_schemas_do_not_cross_contaminate(self):
        # The failure this forbids is silent: one shared field read would make the level appear to
        # work on one driver and never fire on the other.
        oc_completed = json.dumps(
            {"type": "tool_use", "part": {"state": {"status": "completed"}}}
        )
        agy_completed = json.dumps(
            {"type": "step_update", "step_update": {"state": "DONE"}}
        )
        self.assertTrue(runner_stop.is_oc_safe_checkpoint(oc_completed))
        self.assertFalse(runner_stop.is_agy_safe_checkpoint(oc_completed))
        self.assertTrue(runner_stop.is_agy_safe_checkpoint(agy_completed))
        self.assertFalse(runner_stop.is_oc_safe_checkpoint(agy_completed))

    def test_the_checkpoint_condition_is_not_defined_by_elapsed_time(self):
        # Spec R10 forbids a time-based CHECKPOINT definition. Asserted on the actual source of the
        # predicates and of the observer's decision method, so a later "simplification" into a
        # timeout fails here.
        for func in (
            runner_stop.is_oc_safe_checkpoint,
            runner_stop.is_agy_safe_checkpoint,
            runner_stop.CheckpointObserver.observe,
        ):
            source = inspect.getsource(func)
            for forbidden in ("time.", "sleep", "monotonic", "deadline", "budget"):
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{func.__qualname__} must not define the checkpoint by time",
                )

    def test_the_detector_matches_the_real_session_vocabulary(self):
        # Guard against drift from the vocabulary the spec's OQ-01 resolution was verified against.
        self.assertEqual(runner_stop.OC_TOOL_EVENT_TYPE, "tool_use")
        self.assertEqual(runner_stop.OC_COMPLETED_STATUS, "completed")
        self.assertEqual(runner_stop.OC_STEP_COMPLETE_TYPE, "step_finish")
        self.assertEqual(runner_stop.AGY_STEP_EVENT_TYPE, "step_update")
        self.assertEqual(runner_stop.AGY_COMPLETED_STATE, "DONE")


class CheckpointObserverTests(unittest.TestCase):
    """The observer's control flow: stop at the FIRST completed event AFTER the request."""

    def _oc(self) -> runner_stop.CheckpointObserver:
        return runner_stop.CheckpointObserver(
            detector=runner_stop.is_oc_safe_checkpoint
        )

    def test_no_stop_without_a_request_however_many_checkpoints_pass(self):
        obs = self._oc()
        for _ in range(5):
            self.assertFalse(
                obs.observe(json.dumps({"type": "step_finish", "part": {}}))
            )
        self.assertFalse(obs.stop_at_checkpoint)
        self.assertEqual(obs.last_checkpoint_index, 5)

    def test_stops_at_the_first_completed_event_after_the_request(self):
        obs = self._oc()
        script = [
            json.dumps({"type": "step_start", "part": {}}),  # 1 not a checkpoint
            json.dumps({"type": "text", "part": {"text": "x"}}),  # 2 not a checkpoint
            json.dumps({"type": "text", "part": {"text": "y"}}),  # 3 not a checkpoint
            json.dumps(
                {
                    "type": "tool_use",
                    "part": {"tool": "bash", "state": {"status": "running"}},
                }
            ),  # 4 not a checkpoint
            json.dumps(
                {
                    "type": "tool_use",
                    "part": {"tool": "read", "state": {"status": "completed"}},
                }
            ),  # 5 THE checkpoint
            json.dumps({"type": "step_finish", "part": {}}),  # 6 must never be consumed
        ]
        obs.request(runner_stop.LEVEL_NOW, "operator")
        stopped_at = None
        for index, line in enumerate(script, start=1):
            if obs.observe(line):
                stopped_at = index
                break
        self.assertEqual(
            stopped_at, 5, "must stop at the first COMPLETED event, not before/after"
        )
        self.assertEqual(obs.last_checkpoint_index, 5)
        self.assertEqual(obs.last_checkpoint_label, "tool_use:read")
        self.assertEqual(obs.events_seen, 5, "event 6 must never have been consumed")

    def test_the_recorded_position_is_the_completed_events_own(self):
        # Not the position of a line that merely arrived after the request.
        obs = self._oc()
        obs.observe(
            json.dumps({"type": "step_finish", "part": {}})
        )  # 1: checkpoint, no request
        obs.request(3, "op")
        self.assertEqual(obs.last_checkpoint_index, 1)
        self.assertTrue(obs.observe(json.dumps({"type": "step_finish", "part": {}})))
        self.assertEqual(obs.last_checkpoint_index, 2)

    def test_the_request_is_monotonic(self):
        obs = self._oc()
        obs.request(4, "hard")
        obs.request(3, "soft")
        self.assertEqual(obs.requested_level, 4, "a request must never be lowered")

    def test_agy_observer_is_driven_by_step_update_done(self):
        obs = runner_stop.CheckpointObserver(
            detector=runner_stop.is_agy_safe_checkpoint
        )
        obs.request(3, "op")
        # An oc-shaped completion must NOT satisfy the agy observer.
        self.assertFalse(
            obs.observe(
                json.dumps(
                    {"type": "tool_use", "part": {"state": {"status": "completed"}}}
                )
            )
        )
        self.assertTrue(
            obs.observe(
                json.dumps(
                    {
                        "type": "step_update",
                        "step_update": {
                            "state": "DONE",
                            "tool_info": {"name": "run_command"},
                        },
                    }
                )
            )
        )
        self.assertEqual(obs.last_checkpoint_label, "step_update:run_command")


class BothDriversWireLevel3Tests(unittest.TestCase):
    """Orchestrator CID-3: level 3 may not exist in one driver only."""

    def _source(self, name: str) -> str:
        return (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")

    def test_both_drivers_use_the_shared_observer_and_their_own_detector(self):
        oc_src = self._source("oc_runipd.py")
        agy_src = self._source("agy_runipd.py")
        for source in (oc_src, agy_src):
            self.assertIn("runner_stop.CheckpointObserver(", source)
            self.assertIn("runner_stop.StopAtCheckpoint", source)
        self.assertIn("runner_stop.is_oc_safe_checkpoint", oc_src)
        self.assertIn("runner_stop.is_agy_safe_checkpoint", agy_src)
        for module in (oc, agy):
            self.assertTrue(hasattr(module, "_record_checkpoint_stop"), module)
            self.assertTrue(hasattr(module, "_budget_breach_recorder"), module)
            self.assertIs(module.runner_stop, runner_stop)

    def test_checkpoint_detection_is_not_routed_through_the_clean_only_renderer(self):
        # The defect this forbids: `render_event` is called ONLY in the `clean` output branch, so a
        # checkpoint built on it would silently never fire under `raw`/`quiet`. Asserted structurally
        # here and BEHAVIORALLY in `AllOutputModesTests`.
        oc_src = self._source("oc_runipd.py")
        observe_line = next(
            line for line in oc_src.splitlines() if "observer.observe(" in line
        )
        self.assertNotIn("render_event", observe_line)
        # The observe call must precede the output-mode branch in the loop.
        observe_at = oc_src.index("if observer.observe(line)")
        render_at = oc_src.index("rendered = render_event(line, pal, tracker=tracker)")
        self.assertLess(
            observe_at,
            render_at,
            "the checkpoint parse must run before (and independently of) the clean-mode render",
        )

    def test_no_signal_handler_is_registered_yet(self):
        # Phase 5 (`71vjbn`) owns the trigger UX; a handler here would bypass the monotonic writer's
        # handler-safe entry point and reintroduce the measured deadlock.
        for name in ("oc_runipd.py", "agy_runipd.py"):
            self.assertNotIn("signal.signal(", self._source(name))

    def test_no_new_ledger_substrate_was_introduced(self):
        for name in ("oc_runipd.py", "agy_runipd.py"):
            self.assertNotIn("run_ledger_store", self._source(name))


# =============================================================================================
# E-02 / V-02: the turn stops at the checkpoint, via the shared clean shutdown
# =============================================================================================


@pytest.mark.slow
class StopAtCheckpointTests(_InvariantAssertions):
    """Spec A3: the turn stops at a safe checkpoint and the Phase-0 invariants hold."""

    def test_the_turn_stops_after_the_completed_event_never_mid_event(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("laa", "la0001"), ("laa", "la0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["laa"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "la0001",
                    "STOP_LEVEL": "3",
                },
            )

            record = run.item("la0001")["stopped"]
            # The stop index is the scripted checkpoint: event 5, the FIRST completed event after the
            # request. Events 1-4 are non-checkpoints, so an "any line after the request" or a
            # "status-blind" implementation would report 3 or 4 here.
            self.assertEqual(
                record["last_completed_event_index"],
                5,
                f"stopped at the wrong event: {record}",
            )
            self.assertEqual(record["last_completed_event"], "tool_use:read")
            self.assertEqual(record["events_observed"], 5)
            self.assertEqual(record["level"], 3)
            self.assertEqual(record["level_name"], "now")
            self.assertEqual(record["requester"], "test-operator")
            # The child's own defect witness: it writes this file only if it kept running past the
            # checkpoint, which means the driver did not stop the turn.
            self.assertFalse(
                (run.run_dir / "CHILD_RAN_PAST_CHECKPOINT").exists(),
                "the child ran past the checkpoint: the turn was not stopped",
            )
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_the_stop_routes_through_the_shared_clean_shutdown(self):
        # Spec R5: one reaper. Observed from the run's OWN output rather than a mock: the per-turn
        # `clean_shutdown` call has no lock and no repo, so `all_satisfied` is False and the routine
        # PRINTS its per-invariant report (spec R23). That report text can only appear if
        # `clean_shutdown` actually ran.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("lba", "lb0001")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["lba"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "lb0001",
                    "STOP_LEVEL": "3",
                },
            )

            self.assertIn("clean shutdown:", run.stderr)
            self.assertIn(
                f"{runner_shutdown.INVARIANT_CHILDREN} (R1)",
                run.stderr,
                "the level-3 stop must go through clean_shutdown, not a local terminate_process",
            )
            self.assert_phase0_invariants(run, tree_before)

    def test_the_stop_is_recorded_as_a_deliberate_non_failure_event(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("lca", "lc0001"), ("lca", "lc0002")])
            fake = _write_fake_child(root)

            run = _run_driver(
                repo,
                fake,
                ["lca"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "lc0001",
                    "STOP_LEVEL": "3",
                },
            )

            stops = run.events_named("deliberate-stop-at-checkpoint")
            self.assertEqual(len(stops), 1, run.events())
            self.assertTrue(stops[0]["deliberate"])
            self.assertFalse(stops[0]["failure"], "spec R21: intent, not breakage")
            self.assertEqual(stops[0]["level"], 3)
            self.assertEqual(stops[0]["certainty"], runner_stop.CERTAINTY_KNOWN)
            self.assertEqual(stops[0]["last_completed_event_index"], 5)

    def test_the_run_stops_and_leaves_later_items_queued(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(
                root, [("lda", "ld0001"), ("lda", "ld0002"), ("lda", "ld0003")]
            )
            fake = _write_fake_child(root)

            run = _run_driver(
                repo,
                fake,
                ["lda"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "ld0001",
                    "STOP_LEVEL": "3",
                },
            )

            self.assertEqual(run.ran(), {"ld0001"}, run.stderr)
            statuses = run.statuses()
            # Spec R22: items that never ran keep `queued`; nothing is relabeled to explain the stop.
            self.assertEqual(statuses["ld0002"], "queued", statuses)
            self.assertEqual(statuses["ld0003"], "queued", statuses)
            self.assertEqual(
                [e for e in run.events_named("dependency-blocked")],
                [],
                "a stopped run must not invent `dependency-blocked`",
            )


@pytest.mark.slow
class AllOutputModesTests(_InvariantAssertions):
    """The feature must not depend on an unrelated DISPLAY flag.

    `render_event` runs only under `output_mode == "clean"`, so a `render_event`-based checkpoint
    would pass a clean-mode test and silently never fire under `raw` or `quiet`. All three modes are
    therefore driven end-to-end and asserted to stop at the SAME scripted event.
    """

    # Explicit, valid 6-character ids per mode. Derived ids are a trap here: `"lm" + "raw"` is only
    # five characters, which is not a valid id6, so the selector matched nothing and the test failed
    # for a fixture reason rather than a behavioral one.
    _MODE_IDS = {
        "clean": ("lmc", "lmc001"),
        "raw": ("lmr", "lmr001"),
        "quiet": ("lmq", "lmq001"),
    }

    def _stop_index_for_mode(self, mode: str) -> int:
        setid, id6 = self._MODE_IDS[mode]
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [(setid, id6)])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                [setid],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": id6,
                    "STOP_LEVEL": "3",
                },
                output_mode=mode,
                run_tag=mode,
            )

            record = run.item(id6).get("stopped")
            self.assertIsInstance(
                record,
                dict,
                f"output_mode={mode}: no stop was recorded, so the checkpoint never fired "
                f"in this mode (stderr: {run.stderr[-2000:]})",
            )
            self.assertFalse(
                (run.run_dir / "CHILD_RAN_PAST_CHECKPOINT").exists(),
                f"output_mode={mode}: the child ran past the checkpoint",
            )
            self.assert_phase0_invariants(run, tree_before)
            assert record is not None
            return record["last_completed_event_index"]

    def test_checkpoint_fires_in_clean_mode(self):
        self.assertEqual(self._stop_index_for_mode("clean"), 5)

    def test_checkpoint_fires_in_raw_mode(self):
        self.assertEqual(self._stop_index_for_mode("raw"), 5)

    def test_checkpoint_fires_in_quiet_mode(self):
        self.assertEqual(self._stop_index_for_mode("quiet"), 5)


@pytest.mark.slow
class AgyDriverParityTests(_InvariantAssertions):
    """Orchestrator CID-3, proven BEHAVIORALLY on the OTHER driver and its OTHER schema."""

    def test_agy_stops_at_its_own_step_update_done_checkpoint(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("gla", "ga0001"), ("gla", "ga0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["gla"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "ga0001",
                    "STOP_LEVEL": "3",
                    "SCHEMA": "agy",
                },
                driver="agy",
            )

            record = run.item("ga0001")["stopped"]
            self.assertEqual(
                record["last_completed_event_index"], 5, f"agy stop record: {record}"
            )
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_KNOWN)
            self.assertEqual(record["last_completed_event"], "step_update:read")
            self.assertFalse((run.run_dir / "CHILD_RAN_PAST_CHECKPOINT").exists())
            self.assertEqual(run.statuses()["ga0002"], "queued", run.statuses())
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)


# =============================================================================================
# E-03 / V-03: the KNOWN disposition
# =============================================================================================


class StoppedDispositionRecordTests(unittest.TestCase):
    """The record's shape (spec R18/R22), unit-tested through the shared builder."""

    def _record(self) -> dict:
        return runner_stop.stopped_disposition(
            level=3,
            requester="operator",
            last_completed_index=5,
            last_completed_label="tool_use:read",
            git_state=" M agent_workflows/x.py",
            events_seen=5,
            at="2026-08-30T00:00:00+00:00",
        )

    def test_it_records_level_certainty_position_git_state_and_resume_action(self):
        record = self._record()
        self.assertEqual(record["level"], 3)
        self.assertEqual(record["level_name"], "now")
        self.assertEqual(record["certainty"], runner_stop.CERTAINTY_KNOWN)
        self.assertEqual(record["last_completed_event_index"], 5)
        self.assertEqual(record["last_completed_event"], "tool_use:read")
        self.assertEqual(record["git_state"], " M agent_workflows/x.py")
        self.assertTrue(
            record["resume_action"], "spec R18 requires a resume instruction"
        )
        self.assertTrue(record["stopped_deliberately"])
        self.assertFalse(
            record["failure"], "spec R21: a deliberate stop is not a failure"
        )

    def test_it_is_never_unknown_outcome_and_never_a_success(self):
        blob = json.dumps(self._record())
        self.assertNotIn(
            "unknown_outcome", blob, "that certainty is level 4's, not level 3's"
        )
        for word in ("executed", 'complete"', "success"):
            self.assertNotIn(word, blob, f"spec R22 forbids claiming {word!r}")

    def test_the_stopped_status_is_an_already_known_coherent_status(self):
        # Inventing a new status would break Phase 0's ledger-coherence check (spec R3) and the
        # existing recovery requeue at once.
        self.assertIn(
            runner_stop.STOPPED_DISPOSITION, runner_shutdown.KNOWN_ITEM_STATUSES
        )
        self.assertNotIn(runner_stop.STOPPED_DISPOSITION, oc.SUCCESS_STATES)
        self.assertNotIn(runner_stop.STOPPED_DISPOSITION, agy.SUCCESS_STATES)

    def test_reconcile_disposition_intercepts_the_deliberate_stop_in_both_drivers(self):
        # The bug this pins: with no outcome file, the plan still in pending/, and a nonzero exit, the
        # un-intercepted fallback returns `failed-safely` for a DELIBERATE stop.
        item = {
            "action": "execute",
            "id6": "zz0001",
            "position": 1,
            "configured_file": ".aw/records/plans/pending/nonexistent.ipd.md",
            "stopped": {"stopped_deliberately": True, "level": 3},
        }
        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            (run_dir / "outcomes").mkdir(parents=True)
            for module in (oc, agy):
                disposition, outcome = module.reconcile_disposition(
                    Path(temp), dict(item), run_dir, 1
                )
                self.assertEqual(
                    disposition,
                    runner_stop.STOPPED_DISPOSITION,
                    f"{module.__name__}: a deliberate stop must not reconcile to {disposition!r}",
                )
                self.assertNotIn(disposition, ("failed-safely", "partial"))
                self.assertIsNone(outcome)

    def test_a_genuine_failure_still_reconciles_to_failed_safely(self):
        # The CONTROL: the new branch is keyed on the `stopped` record, not on the exit code, so it
        # cannot swallow real failures.
        item = {
            "action": "execute",
            "id6": "zz0002",
            "position": 1,
            "configured_file": ".aw/records/plans/pending/nonexistent.ipd.md",
        }
        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            (run_dir / "outcomes").mkdir(parents=True)
            for module in (oc, agy):
                disposition, _ = module.reconcile_disposition(
                    Path(temp), dict(item), run_dir, 3
                )
                self.assertEqual(
                    disposition, "failed-safely", f"{module.__name__}: {disposition}"
                )

    def test_an_empty_or_falsy_stopped_record_does_not_trigger_the_branch(self):
        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            (run_dir / "outcomes").mkdir(parents=True)
            for stopped in (None, {}, {"stopped_deliberately": False}, "yes", 1):
                item = {
                    "action": "execute",
                    "id6": "zz0003",
                    "position": 1,
                    "configured_file": ".aw/records/plans/pending/nonexistent.ipd.md",
                    "stopped": stopped,
                }
                disposition, _ = oc.reconcile_disposition(Path(temp), item, run_dir, 3)
                self.assertEqual(disposition, "failed-safely", repr(stopped))


@pytest.mark.slow
class KnownDispositionInTheLedgerTests(_InvariantAssertions):
    """V-03: the LEDGER, after a real level-3 stop of a real driver."""

    def test_the_interrupted_item_is_known_and_not_failed_safely(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("kaa", "ka0001"), ("kaa", "ka0002")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["kaa"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "ka0001",
                    "STOP_LEVEL": "3",
                },
            )

            statuses = run.statuses()
            # THE CENTRAL ASSERTION. `failed-safely` / `partial` is exactly what the un-intercepted
            # `reconcile_disposition` fallback produces for a deliberate stop, so either value here
            # means the interception is missing.
            self.assertNotIn(
                statuses["ka0001"],
                ("failed-safely", "partial"),
                f"a DELIBERATE stop was recorded as a failure/partial: {statuses}",
            )
            self.assertEqual(
                statuses["ka0001"], runner_stop.STOPPED_DISPOSITION, statuses
            )
            self.assertNotIn(statuses["ka0001"], oc.SUCCESS_STATES)

            record = run.item("ka0001")["stopped"]
            self.assertEqual(record["certainty"], runner_stop.CERTAINTY_KNOWN)
            self.assertEqual(record["last_completed_event_index"], 5)
            self.assertEqual(record["last_completed_event"], "tool_use:read")
            self.assertTrue(record["resume_action"])
            self.assertIsInstance(record["git_state"], str)

            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_a_genuinely_failed_turn_with_no_stop_still_reports_failed_safely(self):
        # The end-to-end CONTROL: the deliberate-stop branch must not mask real breakage.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("kba", "kb0001")])
            fake = _write_fake_child(root)

            run = _run_driver(repo, fake, ["kba"], env_extra={"FAIL_FOR": "kb0001"})

            statuses = run.statuses()
            self.assertEqual(statuses["kb0001"], "failed-safely", statuses)
            self.assertNotIn("stopped", run.item("kb0001"))
            self.assertEqual(run.events_named("deliberate-stop-at-checkpoint"), [])
            self.assertNotEqual(
                run.returncode, 0, "a real failure must still exit nonzero"
            )


# =============================================================================================
# E-04 / V-04: the bounded wait
# =============================================================================================


class DeadlineArithmeticTests(unittest.TestCase):
    """The GIVE-UP bound (spec R11), which is NOT a checkpoint definition (spec R10)."""

    def _request(self, run_dir: Path, level: int = 3) -> runner_stop.StopRequest:
        result = runner_stop.request_stop(run_dir, level, "operator")
        assert result.request is not None
        return result.request

    def test_remaining_time_tracks_the_records_own_deadline(self):
        with TemporaryDirectory() as temp:
            request = self._request(Path(temp))
            remaining = runner_stop.deadline_seconds_remaining(request)
            # The level-3 budget is the ONE authoritative value from Phase 1; not re-derived here.
            self.assertGreater(remaining, 0.0)
            self.assertLessEqual(
                remaining, runner_stop.budget_for_level(runner_stop.LEVEL_NOW) + 1.0
            )

    def test_an_unparseable_deadline_reads_as_already_breached(self):
        # Failing toward "bounded" can never hang; failing toward "infinite" could.
        broken = runner_stop.StopRequest(
            level=3,
            requested_at="2026-08-30T00:00:00+00:00",
            requester="operator",
            first_requested_at="2026-08-30T00:00:00+00:00",
            budget_seconds=600.0,
            deadline="not-a-timestamp",
        )
        self.assertLessEqual(runner_stop.deadline_seconds_remaining(broken), 0.0)

    def test_the_breach_event_requires_escalation_but_records_none_performed(self):
        with TemporaryDirectory() as temp:
            request = self._request(Path(temp))
            event = runner_stop.budget_breach_event(
                request, at="2026-08-30T00:00:00+00:00", id6="aa0001"
            )
            self.assertEqual(event["event"], runner_stop.BUDGET_BREACH_EVENT)
            self.assertTrue(event["escalation_required"], "Phase 5 acts on this signal")
            self.assertEqual(event["escalation_to_level"], runner_stop.LEVEL_NOW_FORCE)
            self.assertFalse(
                event["escalation_performed"],
                "spec A7 places the escalation ACTION in Phase 5; claiming it here would be false",
            )
            self.assertFalse(event["failure"])

    def test_the_breach_watch_is_bounded_and_fires_without_any_further_input(self):
        fired: list[float] = []
        started = time.monotonic()
        watch = runner_stop.BudgetBreachWatch(
            deadline_monotonic=started + 0.2,
            on_breach=lambda: fired.append(time.monotonic() - started),
        )
        with watch:
            # Nothing is fed to it at all: the deadline must be noticed out-of-band.
            time.sleep(1.0)
        self.assertTrue(watch.breached, "the watch never noticed its deadline")
        self.assertEqual(len(fired), 1, "the breach must be recorded exactly once")
        self.assertLess(fired[0], 1.0, f"breach recorded far too late: {fired[0]}s")

    def test_the_breach_watch_stops_quietly_when_the_child_exits_first(self):
        watch = runner_stop.BudgetBreachWatch(
            deadline_monotonic=time.monotonic() + 0.2,
            on_breach=lambda: self.fail("must not fire once the child is gone"),
            is_alive=lambda: False,
        )
        with watch:
            time.sleep(0.5)
        self.assertFalse(watch.breached)


@pytest.mark.slow
class BudgetBreachDetectionTests(_InvariantAssertions):
    """V-04: a level-3 request with NO reachable checkpoint is bounded, not a hang."""

    def test_a_silent_child_yields_a_recorded_breach_within_a_bounded_time(self):
        # The deadline is SUB-SECOND and INJECTED (the child writes the record with a short budget),
        # so this cannot pass by waiting out the real 600s level-3 budget. The child then emits NOTHING
        # at all, so a detector that only ran when the next line arrived could never fire: the blocking
        # `for line in process.stdout` would still be waiting.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("baa", "ba0001")])
            fake = _write_fake_child(root)
            tree_before = _git(repo, "status", "--porcelain")

            run = _run_driver(
                repo,
                fake,
                ["baa"],
                env_extra={
                    "CHILD_MODE": "silent",
                    "STOP_AFTER": "ba0001",
                    "STOP_BUDGET": "0.25",
                    "CHILD_SILENCE": "4.0",
                },
            )

            breaches = run.events_named(runner_stop.BUDGET_BREACH_EVENT)
            self.assertEqual(
                len(breaches),
                1,
                f"no bounded-wait breach was recorded (elapsed {run.elapsed:.2f}s); "
                f"events: {run.events()}",
            )
            breach = breaches[0]
            self.assertEqual(breach["level"], 3)
            self.assertEqual(breach["budget_seconds"], 0.25)
            self.assertTrue(breach["escalation_required"])
            self.assertFalse(
                breach["escalation_performed"],
                "this phase DETECTS the breach; Phase 5 performs the escalation (spec A7)",
            )
            self.assertEqual(breach["escalation_to_level"], runner_stop.LEVEL_NOW_FORCE)
            # BOUNDED: the injected deadline is 0.25s and the child is silent for 4s, so the whole run
            # must finish in seconds, not in the 600s a real level-3 budget would allow.
            self.assertLess(
                run.elapsed,
                60.0,
                f"the driver did not bound its wait: {run.elapsed:.2f}s elapsed",
            )
            # No ESCALATION ACTION was taken here: the durable request is still level 3.
            request = runner_stop.read_stop_request(run.run_dir)
            self.assertIsNotNone(request)
            assert request is not None
            self.assertEqual(
                request.level,
                3,
                "this phase must not raise the level; Phase 5 owns escalation",
            )
            # And no checkpoint was ever reached, so nothing may claim a checkpoint stop.
            self.assertEqual(run.events_named("deliberate-stop-at-checkpoint"), [])
            self.assert_no_unknown_outcome(run)
            self.assert_phase0_invariants(run, tree_before)

    def test_no_breach_is_recorded_when_a_checkpoint_is_reached_in_time(self):
        # The negative control: the breach path must not fire on the normal level-3 stop.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _make_repo(root, [("bba", "bb0001")])
            fake = _write_fake_child(root)

            run = _run_driver(
                repo,
                fake,
                ["bba"],
                env_extra={
                    "CHILD_MODE": "checkpoint",
                    "STOP_AFTER": "bb0001",
                    "STOP_LEVEL": "3",
                },
            )

            self.assertEqual(
                run.events_named(runner_stop.BUDGET_BREACH_EVENT),
                [],
                "a checkpoint was reached, so no budget breach may be claimed",
            )
            self.assertEqual(len(run.events_named("deliberate-stop-at-checkpoint")), 1)


# =============================================================================================
# Scope fence
# =============================================================================================


class ScopeFenceTests(unittest.TestCase):
    """What this phase deliberately does NOT implement (Phases 4 and 5 own it)."""

    def test_level_3_does_not_claim_level_4s_certainty(self):
        # CONSCIOUSLY NARROWED by runstop Phase 4 (`m0z0ti`), not deleted (orchestrator CID-4).
        #
        # As written for Phase 3 this asserted that `runner_stop.py` contained NO `"unknown_outcome"`
        # literal at all, which was the right fence WHILE Phase 4 was unwritten: it stopped Phase 3
        # from inventing level 4's vocabulary early. Phase 4 has now landed level 4 in this same
        # shared module (`FORCED_DISPOSITION = "unknown_outcome"`,
        # `CERTAINTY_INDETERMINATE`), so a whole-file absence check would now fail for the very
        # reason it existed: the term arrived, from its OWNER.
        #
        # The still-live invariant is the one that actually protects level 3: level 3's own record and
        # constants must keep KNOWN certainty and must never claim the indeterminate one. That is what
        # is asserted now, on the API rather than on file text, so it cannot rot into a text check
        # again.
        self.assertEqual(runner_stop.CERTAINTY_KNOWN, "known")
        self.assertNotEqual(
            runner_stop.CERTAINTY_KNOWN, runner_stop.CERTAINTY_INDETERMINATE
        )
        record = runner_stop.stopped_disposition(
            level=runner_stop.LEVEL_NOW,
            requester="operator",
            last_completed_index=5,
            last_completed_label="tool_use:read",
        )
        self.assertEqual(record["certainty"], runner_stop.CERTAINTY_KNOWN)
        self.assertNotIn("unknown_outcome", json.dumps(record))
        # And level 3's status must not have been quietly swapped for a level-4 concept.
        self.assertEqual(runner_stop.STOPPED_DISPOSITION, "interrupted")

    def test_no_cli_verb_was_added(self):
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            self.assertNotIn('add_parser("stop"', source)

    def test_no_agent_prompt_or_handshake_change(self):
        # Spec OQ-01's resolution explicitly rejected agent cooperation: the checkpoint is observed
        # from the stream the driver already reads.
        #
        # Asserted on the module's PUBLIC SURFACE, not by grepping the source text: the docstrings
        # deliberately DISCUSS the rejected handshake so a later reader does not reintroduce it, and a
        # text grep would therefore fail on the very comment that prevents the defect.
        exported = set(runner_stop.__all__)
        for forbidden in (
            "handshake",
            "negotiate",
            "capability",
            "ask_agent",
            "request_wind_down_from_agent",
        ):
            offenders = [name for name in exported if forbidden in name.lower()]
            self.assertEqual(
                offenders, [], f"agent-cooperation surface added: {offenders}"
            )
        # The checkpoint predicates must take a STREAM LINE and nothing else: no process, no stdin, no
        # agent channel. A cooperative implementation could not have this signature.
        for func in (
            runner_stop.is_oc_safe_checkpoint,
            runner_stop.is_agy_safe_checkpoint,
        ):
            params = list(inspect.signature(func).parameters)
            self.assertEqual(params, ["line"], f"{func.__name__}{params}")

    def test_the_drivers_send_the_child_nothing(self):
        # The honest mechanism check: the child is a one-shot subprocess with NO stop channel, so the
        # drivers must never try to WRITE to it. `stdin` is never wired for writing and no
        # `process.stdin.write` / `communicate(` appears in either driver.
        for name in ("oc_runipd.py", "agy_runipd.py"):
            source = (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")
            self.assertNotIn("process.stdin.write", source, name)
            self.assertNotIn("process.communicate(", source, name)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
