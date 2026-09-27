"""Behavioral tests for runner peer dependency waiting (e54nz9).

Validates:
(a) predicate: live peer with id6 running -> held; peer process exited -> not held;
    peer entry executed/fail-verify -> not held; target in own queue -> not held;
    exists:/state:/spec edge -> not held.
(b) wait released: background thread moves prerequisite into executed/ -> released=True.
(c) peer-gone: holder process exits mid-wait -> released=False, outcome "peer-gone".
(d) timeout: injected clock -> outcome "timeout".
(e) stop: stop request -> stopped=True, outcome "stopped".
(f) no-peer drain arm: with no live peer, external-edge item ends fail-depend (regression pin).
(g) BOTH hosts: oc_runipd and agy_runipd run_queue dispatch the item when prerequisite lands.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import init_repo

_HOLDER_CODE = """
import sys
from pathlib import Path
from agent_workflows import platform_lock

held = platform_lock.acquire(Path(sys.argv[1]))
sys.stdout.write("locked\\n")
sys.stdout.flush()
sys.stdin.read()
held.release()
"""


class _HolderProcess:
    """Live subprocess holding driver.lock via platform_lock."""

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = lock_path
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _HOLDER_CODE, str(self.lock_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline().strip()
        assert line == "locked", f"Holder failed to acquire lock: {line!r}"

    def stop(self) -> None:
        if self.proc is not None:
            if self.proc.poll() is None:
                if self.proc.stdin is not None:
                    try:
                        self.proc.stdin.close()
                    except OSError:
                        pass
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=5)
            self.proc = None

    def __enter__(self) -> _HolderProcess:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()


@contextlib.contextmanager
def _held_observed():
    """Yield an Event set the first time the waiter SEES a prerequisite held by a live peer.

    The release tests used to move the plan after a fixed `time.sleep(0.15)`, racing a wall-clock
    timer against the waiter's own setup (driver-lock probe, peer discovery, state read). On a slow
    runner (measured on the Windows CI runner, and reproduced by delaying the first probe 400 ms) the
    plan moved BEFORE the first check, the waiter correctly found nothing to wait for, and the test
    failed. Gating the move on this event guarantees the order the tests assert: held, then released.
    """
    seen = threading.Event()
    real = runner_shared.peer_held_prerequisites

    def observing(*args: object, **kwargs: object):
        held = real(*args, **kwargs)
        if held:
            seen.set()
        return held

    with mock.patch.object(runner_shared, "peer_held_prerequisites", observing):
        yield seen


def _setup_repo_and_runs(
    tmp: Path,
    repo_name: str = "repo",
    run_name: str = "run-current",
    peer_name: str = "run-peer",
) -> tuple[Path, Path, Path]:
    repo = init_repo(tmp / repo_name)
    runs_dir = repo / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)

    current_run_dir = runs_dir / run_name
    current_run_dir.mkdir(parents=True, exist_ok=True)

    peer_run_dir = runs_dir / peer_name
    peer_run_dir.mkdir(parents=True, exist_ok=True)

    return repo, current_run_dir, peer_run_dir


class RunnerPeerDependencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_a_predicate_subcases(self) -> None:
        repo, current_run_dir, peer_run_dir = _setup_repo_and_runs(self.tmp)

        # Write peer state.json with prereq running
        (peer_run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-peer",
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )

        current_state = {
            "run_id": "run-current",
            "repo": str(repo),
            "queue": [
                {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": ["executed:prereq"],
                },
            ],
        }
        item = current_state["queue"][0]

        # 1. Live peer with id6 running -> held
        with _HolderProcess(peer_run_dir / "driver.lock"):
            held = runner_shared.peer_held_prerequisites(
                repo, item, current_state, exclude_run_dir=current_run_dir
            )
            self.assertIn("prereq", held)
            self.assertEqual(held["prereq"].run_id, "run-peer")
            self.assertEqual(held["prereq"].peer_state, runner_shared.PEER_LIVE)
            self.assertEqual(held["prereq"].item_status, "running")

        # 2. Peer process exited (lock released) -> not held
        held = runner_shared.peer_held_prerequisites(
            repo, item, current_state, exclude_run_dir=current_run_dir
        )
        self.assertEqual(held, {})

        # 3. Peer entry executed / fail-verify -> not held
        with _HolderProcess(peer_run_dir / "driver.lock"):
            for terminal_status in ("executed", "fail-verify"):
                (peer_run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "run_id": "run-peer",
                            "repo": str(repo),
                            "queue": [{"id6": "prereq", "status": terminal_status}],
                        }
                    ),
                    encoding="utf-8",
                )
                held = runner_shared.peer_held_prerequisites(
                    repo, item, current_state, exclude_run_dir=current_run_dir
                )
                self.assertEqual(
                    held, {}, f"Expected not held for status {terminal_status}"
                )

        # 4. Target in own queue -> not held
        (peer_run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-peer",
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )
        state_with_target = {
            "run_id": "run-current",
            "repo": str(repo),
            "queue": [
                {"id6": "prereq", "status": "queued"},
                {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": ["executed:prereq"],
                },
            ],
        }
        with _HolderProcess(peer_run_dir / "driver.lock"):
            held = runner_shared.peer_held_prerequisites(
                repo, item, state_with_target, exclude_run_dir=current_run_dir
            )
            self.assertEqual(held, {})

        # 5. Non-executed:ipd edges -> not held
        with _HolderProcess(peer_run_dir / "driver.lock"):
            for dep_token in (
                "exists:prereq",
                "state:approved:prereq",
                "executed:spec:prereq",
            ):
                test_item = {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": [dep_token],
                }
                held = runner_shared.peer_held_prerequisites(
                    repo, test_item, current_state, exclude_run_dir=current_run_dir
                )
                self.assertEqual(held, {}, f"Expected not held for {dep_token}")

    def test_b_wait_released(self) -> None:
        repo, current_run_dir, peer_run_dir = _setup_repo_and_runs(self.tmp)
        (peer_run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-peer",
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )
        current_state = {
            "run_id": "run-current",
            "repo": str(repo),
            "queue": [
                {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": ["executed:prereq"],
                },
            ],
        }
        item = current_state["queue"][0]
        (current_run_dir / "state.json").write_text(
            json.dumps(current_state), encoding="utf-8"
        )

        plan_pending = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260101-s-01-prereq-plan.ipd.md"
        )
        plan_pending.write_text(
            "# Plan prereq\n- Id: prereq\n- Status: approved\n", encoding="utf-8"
        )

        with _HolderProcess(peer_run_dir / "driver.lock"):

            def _move_prereq() -> None:
                assert held_seen.wait(timeout=10), "the waiter never saw the peer hold"
                plan_executed = (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "executed"
                    / "20260101-s-01-prereq-plan.ipd.md"
                )
                plan_pending.rename(plan_executed)

            with _held_observed() as held_seen:
                t = threading.Thread(target=_move_prereq)
                t.start()
                try:
                    res = runner_shared.wait_for_peer_prerequisites(
                        current_run_dir,
                        current_state,
                        [item],
                        poll=0.05,
                        timeout=5.0,
                    )
                finally:
                    t.join()

            self.assertTrue(res.waited)
            self.assertTrue(res.released)
            self.assertFalse(res.stopped)
            self.assertEqual(res.outcome, "released")

            events = [
                json.loads(line)
                for line in (current_run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line
            ]
            started = [
                e for e in events if e.get("event") == "peer-dependency-wait-started"
            ]
            ended = [
                e for e in events if e.get("event") == "peer-dependency-wait-ended"
            ]
            self.assertEqual(len(started), 1)
            self.assertEqual(len(ended), 1)
            self.assertEqual(ended[0]["outcome"], "released")
            self.assertIn("elapsed_s", ended[0])
            self.assertEqual(item["status"], "queued")  # writes no item status

    def test_c_peer_gone(self) -> None:
        repo, current_run_dir, peer_run_dir = _setup_repo_and_runs(self.tmp)
        (peer_run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-peer",
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )
        current_state = {
            "run_id": "run-current",
            "repo": str(repo),
            "queue": [
                {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": ["executed:prereq"],
                },
            ],
        }
        item = current_state["queue"][0]
        (current_run_dir / "state.json").write_text(
            json.dumps(current_state), encoding="utf-8"
        )

        holder = _HolderProcess(peer_run_dir / "driver.lock")
        holder.start()

        with _held_observed() as held_seen:

            def _stop_holder() -> None:
                assert held_seen.wait(timeout=10), "the waiter never saw the peer hold"
                holder.stop()

            t = threading.Thread(target=_stop_holder)
            t.start()
            try:
                res = runner_shared.wait_for_peer_prerequisites(
                    current_run_dir,
                    current_state,
                    [item],
                    poll=0.05,
                    timeout=10.0,
                )
            finally:
                t.join()
                holder.stop()

        self.assertTrue(res.waited)
        self.assertFalse(res.released)
        self.assertFalse(res.stopped)
        self.assertEqual(res.outcome, "peer-gone")
        self.assertLess(res.elapsed_s, 5.0)

        events = [
            json.loads(line)
            for line in (current_run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        ]
        ended = [e for e in events if e.get("event") == "peer-dependency-wait-ended"]
        self.assertEqual(len(ended), 1)
        self.assertEqual(ended[0]["outcome"], "peer-gone")

    def test_d_timeout(self) -> None:
        repo, current_run_dir, peer_run_dir = _setup_repo_and_runs(self.tmp)
        (peer_run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-peer",
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )
        current_state = {
            "run_id": "run-current",
            "repo": str(repo),
            "queue": [
                {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": ["executed:prereq"],
                },
            ],
        }
        item = current_state["queue"][0]

        current_mono = 1000.0

        def fake_now() -> float:
            return current_mono

        def fake_sleep(_secs: float) -> None:
            nonlocal current_mono
            current_mono += 100.0

        with _HolderProcess(peer_run_dir / "driver.lock"):
            res = runner_shared.wait_for_peer_prerequisites(
                current_run_dir,
                current_state,
                [item],
                timeout=50.0,
                poll=5.0,
                now=fake_now,
                sleep=fake_sleep,
            )

        self.assertTrue(res.waited)
        self.assertFalse(res.released)
        self.assertFalse(res.stopped)
        self.assertEqual(res.outcome, "timeout")
        self.assertGreaterEqual(res.elapsed_s, 50.0)

    def test_e_stop(self) -> None:
        repo, current_run_dir, peer_run_dir = _setup_repo_and_runs(self.tmp)
        (peer_run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-peer",
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )
        current_state = {
            "run_id": "run-current",
            "repo": str(repo),
            "queue": [
                {
                    "id6": "dep001",
                    "status": "queued",
                    "dependencies": ["executed:prereq"],
                },
            ],
        }
        item = current_state["queue"][0]

        polls = 0

        def fake_poll_stop(_rd: Path) -> int | None:
            nonlocal polls
            polls += 1
            if polls >= 2:
                return 1
            return None

        with _HolderProcess(peer_run_dir / "driver.lock"):
            res = runner_shared.wait_for_peer_prerequisites(
                current_run_dir,
                current_state,
                [item],
                poll=0.01,
                timeout=10.0,
                poll_stop=fake_poll_stop,
            )

        self.assertTrue(res.waited)
        self.assertFalse(res.released)
        self.assertTrue(res.stopped)
        self.assertEqual(res.outcome, "stopped")

    def test_f_no_peer_drain_arm(self) -> None:
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                repo, current_run_dir, _ = _setup_repo_and_runs(
                    self.tmp,
                    repo_name=f"repo-f-{module.__name__}",
                    run_name=f"run-{module.__name__}",
                )
                dep_plan = (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20260101-s-01-dep001-plan.ipd.md"
                )
                dep_plan.write_text(
                    "# Plan dep001\n- Id: dep001\n- Status: approved\n- Item-Dependencies: executed:prereq\n",
                    encoding="utf-8",
                )

                state = {
                    "schema_version": 1,
                    "run_id": f"run-{module.__name__}",
                    "repo": str(repo),
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "selectors": ["s"],
                    "options": {},
                    "queue": [
                        {
                            "position": 1,
                            "id6": "dep001",
                            "setid": "s",
                            "action": "execute",
                            "kind": "child",
                            "status": "queued",
                            "path": str(dep_plan.relative_to(repo)),
                            "dependencies": ["executed:prereq"],
                            "attempts": [],
                            "order": 1,
                        }
                    ],
                }
                (current_run_dir / "state.json").write_text(
                    json.dumps(state), encoding="utf-8"
                )

                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    module.run_queue(current_run_dir, retry_incomplete=False)

                reloaded = json.loads(
                    (current_run_dir / "state.json").read_text(encoding="utf-8")
                )
                item = reloaded["queue"][0]
                self.assertEqual(item["status"], "fail-depend")

                events = [
                    json.loads(line)
                    for line in (current_run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line
                ]
                self.assertFalse(
                    any(
                        e.get("event") == "peer-dependency-wait-started" for e in events
                    )
                )
                dep_blocked = [
                    e for e in events if e.get("event") == "dependency-blocked"
                ]
                self.assertEqual(len(dep_blocked), 1)
                self.assertEqual(dep_blocked[0]["id6"], "dep001")

    def test_g_both_hosts_dispatch_after_peer_release(self) -> None:
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                repo, current_run_dir, peer_run_dir = _setup_repo_and_runs(
                    self.tmp,
                    repo_name=f"repo-g-{module.__name__}",
                    run_name=f"run-{module.__name__}",
                    peer_name=f"run-peer-{module.__name__}",
                )

                (peer_run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "run_id": f"run-peer-{module.__name__}",
                            "repo": str(repo),
                            "queue": [{"id6": "prereq", "status": "running"}],
                        }
                    ),
                    encoding="utf-8",
                )

                prereq_plan = (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20260101-s-01-prereq-plan.ipd.md"
                )
                prereq_plan.write_text(
                    "# Plan prereq\n- Id: prereq\n- Status: approved\n",
                    encoding="utf-8",
                )

                dep_plan = (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20260101-s-02-dep001-plan.ipd.md"
                )
                dep_plan.write_text(
                    "# Plan dep001\n- Id: dep001\n- Status: approved\n- Item-Dependencies: executed:prereq\n",
                    encoding="utf-8",
                )

                state = {
                    "schema_version": 1,
                    "run_id": f"run-{module.__name__}",
                    "repo": str(repo),
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "selectors": ["s"],
                    "options": {},
                    "queue": [
                        {
                            "position": 1,
                            "id6": "dep001",
                            "setid": "s",
                            "action": "execute",
                            "kind": "child",
                            "status": "queued",
                            "path": str(dep_plan.relative_to(repo)),
                            "dependencies": ["executed:prereq"],
                            "attempts": [],
                            "order": 2,
                        }
                    ],
                }
                (current_run_dir / "state.json").write_text(
                    json.dumps(state), encoding="utf-8"
                )

                dispatched: list[str] = []

                def _fake_execute(
                    rd: Path, st: dict, it: dict, *args: object, **kwargs: object
                ) -> None:
                    dispatched.append(it["id6"])
                    it["status"] = "executed"
                    module.save_state(rd, st)

                with _HolderProcess(
                    peer_run_dir / "driver.lock"
                ), _held_observed() as held_seen:

                    def _release_prereq() -> None:
                        assert held_seen.wait(
                            timeout=10
                        ), "the waiter never saw the peer hold"
                        prereq_exec = (
                            repo
                            / ".aw"
                            / "records"
                            / "plans"
                            / "executed"
                            / "20260101-s-01-prereq-plan.ipd.md"
                        )
                        prereq_plan.rename(prereq_exec)

                    t = threading.Thread(target=_release_prereq)
                    t.start()
                    try:
                        orig_wait = runner_shared.wait_for_peer_prerequisites

                        def fast_wait(
                            *wargs: object, **wkwargs: object
                        ) -> runner_shared.PeerWaitOutcome:
                            wkwargs["poll"] = 0.05
                            return orig_wait(*wargs, **wkwargs)

                        with (
                            mock.patch.object(module, "execute_item", _fake_execute),
                            mock.patch.object(
                                runner_shared, "wait_for_peer_prerequisites", fast_wait
                            ),
                            contextlib.redirect_stdout(io.StringIO()),
                            contextlib.redirect_stderr(io.StringIO()),
                        ):
                            module.run_queue(current_run_dir, retry_incomplete=False)
                    finally:
                        t.join()

                self.assertEqual(
                    dispatched, ["dep001"], f"{module.__name__} did not dispatch dep001"
                )
                reloaded = json.loads(
                    (current_run_dir / "state.json").read_text(encoding="utf-8")
                )
                self.assertEqual(reloaded["queue"][0]["status"], "executed")

    def _drain_fixture(self, name: str) -> tuple[Path, Path, Path]:
        """A run whose only item waits on `prereq`, which a live peer holds `running`."""
        repo, rd, peer = _setup_repo_and_runs(
            self.tmp,
            repo_name=f"repo-{name}",
            run_name=f"run-{name}",
            peer_name=f"run-peer-{name}",
        )
        (peer / "state.json").write_text(
            json.dumps(
                {
                    "run_id": peer.name,
                    "repo": str(repo),
                    "queue": [{"id6": "prereq", "status": "running"}],
                }
            ),
            encoding="utf-8",
        )
        pending = repo / ".aw" / "records" / "plans" / "pending"
        (pending / "20260101-s-01-prereq-plan.ipd.md").write_text(
            "# Plan prereq\n- Id: prereq\n- Status: approved\n", encoding="utf-8"
        )
        dep = pending / "20260101-s-02-dep001-plan.ipd.md"
        dep.write_text(
            "# Plan dep001\n- Id: dep001\n- Status: approved\n- Item-Dependencies: executed:prereq\n",
            encoding="utf-8",
        )
        state = {
            "schema_version": 1,
            "run_id": rd.name,
            "repo": str(repo),
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "selectors": ["s"],
            "options": {},
            "queue": [
                {
                    "position": 1,
                    "id6": "dep001",
                    "setid": "s",
                    "action": "execute",
                    "kind": "child",
                    "status": "queued",
                    "path": str(dep.relative_to(repo)),
                    "dependencies": ["executed:prereq"],
                    "attempts": [],
                    "order": 2,
                }
            ],
        }
        (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return repo, rd, peer

    def test_h_level3_stop_during_wait_ends_the_run_on_both_hosts(self) -> None:
        """A level-3 stop mid-wait must END the run, not re-enter the drain arm forever.

        Regression for the verify-execution finding: `_observe_between_turn_stop` makes no wind-down
        for level 3, so a bare `continue` after a stopped wait re-waited indefinitely.
        """
        from agent_workflows import runner_stop

        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                _repo, rd, peer = self._drain_fixture(f"h-{module.__name__}")
                orig = runner_shared.wait_for_peer_prerequisites
                calls = [0]

                def bounded(*a: object, **k: object) -> runner_shared.PeerWaitOutcome:
                    calls[0] += 1
                    if calls[0] > 5:
                        raise AssertionError(
                            "drain arm re-entered the wait after a stop (spin)"
                        )
                    k["poll"] = 0.02
                    k["timeout"] = 5.0
                    return orig(*a, **k)

                def stopper() -> None:
                    # Stop only once the wait is genuinely in progress (see `_held_observed`).
                    assert held_seen.wait(
                        timeout=10
                    ), "the waiter never saw the peer hold"
                    runner_stop.request_stop(rd, runner_stop.LEVEL_NOW, "test")

                with _HolderProcess(
                    peer / "driver.lock"
                ), _held_observed() as held_seen:
                    th = threading.Thread(target=stopper)
                    th.start()
                    try:
                        with (
                            mock.patch.object(
                                runner_shared, "wait_for_peer_prerequisites", bounded
                            ),
                            contextlib.redirect_stdout(io.StringIO()),
                            contextlib.redirect_stderr(io.StringIO()),
                        ):
                            module.run_queue(rd, retry_incomplete=False)
                    finally:
                        th.join()
                reloaded = json.loads((rd / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(calls[0], 1)
                self.assertEqual(reloaded["queue"][0]["status"], "queued")

    def test_i_wait_is_visible_by_default(self) -> None:
        """With no `say=` (as the hosts call it) the wait must announce itself on stderr."""
        _repo, rd, peer = self._drain_fixture("i")
        state = json.loads((rd / "state.json").read_text(encoding="utf-8"))
        err = io.StringIO()
        with _HolderProcess(peer / "driver.lock"), contextlib.redirect_stderr(err):
            res = runner_shared.wait_for_peer_prerequisites(
                rd, state, [state["queue"][0]], poll=0.01, timeout=0.05
            )
        self.assertTrue(res.waited)
        self.assertIn("[peer-dependency]", err.getvalue())
        self.assertIn("prereq", err.getvalue())
        # The limit renders as an HH:MM:SS clock, not raw float seconds.
        self.assertIn("waiting up to 00:00:00", err.getvalue())
        self.assertNotIn("0.05s", err.getvalue())


class FormatClockTests(unittest.TestCase):
    def test_format_clock(self) -> None:
        self.assertEqual(runner_shared.format_clock(1022.6), "00:17:02")
        self.assertEqual(runner_shared.format_clock(1800.0), "00:30:00")
        self.assertEqual(runner_shared.format_clock(18000), "05:00:00")
        self.assertEqual(runner_shared.format_clock(0), "00:00:00")
        self.assertEqual(runner_shared.format_clock(None), "00:00:00")
        self.assertEqual(runner_shared.format_clock(-5), "00:00:00")
        self.assertEqual(runner_shared.format_clock(360000), "100:00:00")


if __name__ == "__main__":
    unittest.main()
