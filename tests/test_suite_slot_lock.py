"""Tests for test-suite machine-wide slot lock and stall heartbeat (IPD xvm6no E-06).

Cells covered:
(a) two subprocesses calling suite_slot with AW_SUITE_SLOTS=1 serialize (recorded
    enter/exit timestamps prove non-overlap) and waiter prints waiting line naming holder pid;
(b) with 2 slots, two hold concurrently and a third waits;
(c) AW_SUITE_SLOT_TIMEOUT=2 runs anyway, prints warning and reports acquired=False;
(d) nested guard (E-03), both with and without AW_SUITE_SLOT_HELD=1 marker;
(e) heartbeat observer returns False on first poll, True after touch, False again with
    no further touch, and never raises on missing directory;
(f) holder killed with SIGKILL frees its slot for the next waiter despite leftover holder file;
(g) END TO END on each host (oc_runipd and agy_runipd) with a REAL child built by
    support.make_fake_executable driving stall_timeout 1.0, asserting heartbeat child is not
    reaped while control child raises StallTimeout.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    runner_shared,
    stall_progress,
    suite_cache,
)
from tests import support

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _clean_slot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)


_WORKER_SCRIPT = textwrap.dedent("""
    import json
    import os
    import sys
    import time
    from pathlib import Path
    from agent_workflows import suite_cache

    log_file = Path(sys.argv[1])
    worker_id = sys.argv[2]
    hold_duration = float(sys.argv[3])
    started_file = Path(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None
    release_file = Path(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] else None

    with suite_cache.suite_slot() as slot:
        enter_mono = time.monotonic()
        enter_wall = time.time()
        if started_file is not None:
            started_file.write_text(str(os.getpid()), encoding="utf-8")
        if release_file is not None:
            deadline = time.monotonic() + hold_duration
            while not release_file.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
        else:
            time.sleep(hold_duration)
        exit_mono = time.monotonic()
        exit_wall = time.time()
        record = {
            "id": worker_id,
            "pid": os.getpid(),
            "slot_acquired": slot.slot_acquired,
            "waited_seconds": slot.waited_seconds,
            "slot_index": slot.slot_index,
            "enter_mono": enter_mono,
            "exit_mono": exit_mono,
            "enter_wall": enter_wall,
            "exit_wall": exit_wall,
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\\n")
""")

_HEARTBEAT_CHILD_CODE = textwrap.dedent("""
    import os
    import sys
    import time
    from agent_workflows import suite_cache

    run_id = os.environ.get("AW_RUN_ID")
    item_id6 = os.environ.get("AW_ITEM_ID6")
    if not run_id or not item_id6:
        sys.exit(1)

    deadline = time.monotonic() + 1.8
    while time.monotonic() < deadline:
        suite_cache.touch_heartbeat(run_id, item_id6)
        time.sleep(0.15)
    sys.exit(0)
""")

_CONTROL_CHILD_CODE = textwrap.dedent("""
    import sys
    import time
    time.sleep(1.8)
    sys.exit(0)
""")


def _make_fake_agent_repo(root: Path):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=root, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-qm", "init"], cwd=root, check=True
    )

    worktree = root / "worktree"
    worktree.mkdir(parents=True, exist_ok=True)
    run_dir = root / ".aw" / "records" / "runs" / "run-test-e2e"
    (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
    prompt_path = root / "prompt.md"
    prompt_path.write_text("prompt text", encoding="utf-8")
    plan_path = root / "plan.ipd.md"
    plan_path.write_text("plan text", encoding="utf-8")
    return worktree, run_dir, prompt_path, plan_path


def test_two_subprocesses_serialize_and_print_waiting_line(tmp_path: Path):
    """Cell (a): two subprocesses calling suite_slot with AW_SUITE_SLOTS=1 serialize and waiter prints waiting line."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)
    log_file = tmp_path / "log.jsonl"
    started1 = tmp_path / "p1.started"

    env_base = os.environ.copy()
    env_base["AW_SUITE_LOCK_DIR"] = str(lock_dir)
    env_base["AW_SUITE_SLOTS"] = "1"
    env_base["AW_SUITE_SLOT_POLL_INTERVAL"] = "0.05"
    env_base["PYTHONPATH"] = str(_REPO_ROOT)
    env_base.pop("AW_SUITE_SLOT_HELD", None)

    # Subprocess 1: holds slot for 2.0s
    p1 = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _WORKER_SCRIPT,
            str(log_file),
            "w1",
            "2.0",
            str(started1),
        ],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    deadline = time.monotonic() + 5.0
    while not started1.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert started1.exists(), "p1 did not start in time"

    # Subprocess 2: attempts to acquire slot, must wait until p1 releases
    p2 = subprocess.Popen(
        [sys.executable, "-c", _WORKER_SCRIPT, str(log_file), "w2", "0.2"],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    out1, err1 = p1.communicate(timeout=15)
    out2, err2 = p2.communicate(timeout=15)

    assert p1.returncode == 0, f"p1 failed: {err1}"
    assert p2.returncode == 0, f"p2 failed: {err2}"

    p1_pid = int(started1.read_text(encoding="utf-8").strip())
    assert f"pid {p1_pid}" in err2
    assert "waiting for a test-suite slot" in err2

    records = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").strip().splitlines()
    ]
    assert len(records) == 2
    r1 = next(r for r in records if r["id"] == "w1")
    r2 = next(r for r in records if r["id"] == "w2")

    assert r1["slot_acquired"] is True
    assert r2["slot_acquired"] is True
    assert r2["waited_seconds"] > 0
    assert r2["enter_mono"] >= r1["exit_mono"] - 0.05


def test_two_slots_concurrent_and_third_waits(tmp_path: Path):
    """Cell (b): with 2 slots, two hold concurrently and a third waits."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)
    log_file = tmp_path / "log.jsonl"
    started1 = tmp_path / "p1.started"
    started2 = tmp_path / "p2.started"

    env_base = os.environ.copy()
    env_base["AW_SUITE_LOCK_DIR"] = str(lock_dir)
    env_base["AW_SUITE_SLOTS"] = "2"
    env_base["AW_SUITE_SLOT_POLL_INTERVAL"] = "0.05"
    env_base["PYTHONPATH"] = str(_REPO_ROOT)
    env_base.pop("AW_SUITE_SLOT_HELD", None)

    p1 = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _WORKER_SCRIPT,
            str(log_file),
            "w1",
            "2.0",
            str(started1),
        ],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    p2 = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _WORKER_SCRIPT,
            str(log_file),
            "w2",
            "2.0",
            str(started2),
        ],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    deadline = time.monotonic() + 5.0
    while (
        not started1.exists() or not started2.exists()
    ) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert started1.exists() and started2.exists(), "p1 or p2 did not start in time"

    p3 = subprocess.Popen(
        [sys.executable, "-c", _WORKER_SCRIPT, str(log_file), "w3", "0.2"],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    p1.communicate(timeout=15)
    p2.communicate(timeout=15)
    out3, err3 = p3.communicate(timeout=15)

    assert p3.returncode == 0, f"p3 failed: {err3}"
    assert "waiting for a test-suite slot" in err3

    records = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").strip().splitlines()
    ]
    assert len(records) == 3
    r1 = next(r for r in records if r["id"] == "w1")
    r2 = next(r for r in records if r["id"] == "w2")
    r3 = next(r for r in records if r["id"] == "w3")

    # w1 and w2 overlapped:
    assert r1["enter_mono"] < r2["exit_mono"]
    assert r2["enter_mono"] < r1["exit_mono"]

    # w3 waited for one of them:
    earliest_exit = min(r1["exit_mono"], r2["exit_mono"])
    assert r3["enter_mono"] >= earliest_exit - 0.05
    assert r3["waited_seconds"] > 0


def test_slot_timeout_runs_anyway_with_warning(tmp_path: Path):
    """Cell (c): AW_SUITE_SLOT_TIMEOUT=2 runs anyway, prints warning and reports acquired=False."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)
    log_file = tmp_path / "log.jsonl"
    started1 = tmp_path / "p1.started"
    release1 = tmp_path / "p1.release"

    env_base = os.environ.copy()
    env_base["AW_SUITE_LOCK_DIR"] = str(lock_dir)
    env_base["AW_SUITE_SLOTS"] = "1"
    env_base["PYTHONPATH"] = str(_REPO_ROOT)
    env_base.pop("AW_SUITE_SLOT_HELD", None)

    p1 = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _WORKER_SCRIPT,
            str(log_file),
            "w1",
            "15.0",
            str(started1),
            str(release1),
        ],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5.0
    while not started1.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert started1.exists(), "p1 did not start in time"

    env2 = env_base.copy()
    env2["AW_SUITE_SLOT_TIMEOUT"] = "0.6"
    env2["AW_SUITE_SLOT_POLL_INTERVAL"] = "0.03"
    p2 = subprocess.Popen(
        [sys.executable, "-c", _WORKER_SCRIPT, str(log_file), "w2", "0.2"],
        env=env2,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        out2, err2 = p2.communicate(timeout=10)
    finally:
        release1.write_text("release", encoding="utf-8")
        p1.communicate(timeout=10)

    assert p2.returncode == 0, f"p2 failed: {err2}"
    assert "timed out waiting for test-suite slot" in err2
    assert "running anyway without a slot" in err2

    records = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").strip().splitlines()
    ]
    r2 = next(r for r in records if r["id"] == "w2")
    assert r2["slot_acquired"] is False
    assert r2["waited_seconds"] >= 0.55


def test_nested_guard_with_and_without_marker(tmp_path: Path):
    """Cell (d): nested guard (E-03), both with and without AW_SUITE_SLOT_HELD=1."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)

    env_base = os.environ.copy()
    env_base["AW_SUITE_LOCK_DIR"] = str(lock_dir)
    env_base["AW_SUITE_SLOTS"] = "1"
    env_base["AW_SUITE_SLOT_TIMEOUT"] = "0.4"
    env_base["AW_SUITE_SLOT_POLL_INTERVAL"] = "0.05"
    env_base.pop("AW_SUITE_SLOT_HELD", None)

    with suite_cache.suite_slot(env=env_base) as parent_slot:
        assert parent_slot.slot_acquired is True

        # Nested call WITH marker: acquires immediately without waiting
        nested_env = env_base.copy()
        nested_env["AW_SUITE_SLOT_HELD"] = "1"
        t0 = time.monotonic()
        with suite_cache.suite_slot(env=nested_env) as nested_slot:
            assert nested_slot.slot_acquired is True
            assert nested_slot.waited_seconds == 0.0
        elapsed_nested = time.monotonic() - t0
        assert elapsed_nested < 0.1

        # Nested call WITHOUT marker: attempts to acquire, waits and times out
        unmarked_env = env_base.copy()
        unmarked_env.pop("AW_SUITE_SLOT_HELD", None)
        t0 = time.monotonic()
        with suite_cache.suite_slot(env=unmarked_env) as unmarked_slot:
            assert unmarked_slot.slot_acquired is False
            assert unmarked_slot.waited_seconds >= 0.35
        elapsed_unmarked = time.monotonic() - t0
        assert elapsed_unmarked >= 0.35


def test_heartbeat_observer_lifecycle_and_nonexistent_dir(tmp_path: Path):
    """Cell (e): heartbeat observer returns False on first poll, True after touch, False again, and never raises on missing dir."""
    missing_dir = tmp_path / "nonexistent" / "dir"
    env = os.environ.copy()
    env["AW_SUITE_LOCK_DIR"] = str(missing_dir)

    obs = stall_progress.SuiteHeartbeatObserver("run-test-1", "abc123")
    with mock.patch.dict(os.environ, env):
        assert obs.poll() is False
        assert obs.poll() is False

    valid_dir = tmp_path / "valid_lock"
    valid_dir.mkdir(mode=0o700)
    env["AW_SUITE_LOCK_DIR"] = str(valid_dir)

    with mock.patch.dict(os.environ, env):
        obs2 = stall_progress.SuiteHeartbeatObserver("run-test-2", "def456")
        assert obs2.poll() is False

        suite_cache.touch_heartbeat("run-test-2", "def456", env=env)
        assert obs2.poll() is True
        assert obs2.poll() is False

        time.sleep(0.05)
        suite_cache.touch_heartbeat("run-test-2", "def456", env=env)
        assert obs2.poll() is True

        suite_cache.remove_heartbeat_file("run-test-2", "def456", env=env)
        hb_path = suite_cache.heartbeat_path("run-test-2", "def456", env=env)
        assert hb_path is not None and not hb_path.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX SIGKILL recovery test only")
def test_dead_holder_frees_slot_despite_leftover_file(tmp_path: Path):
    """Cell (f): holder killed with SIGKILL frees its slot for the next waiter despite leftover holder file."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)
    log_file = tmp_path / "log.jsonl"
    started1 = tmp_path / "p1.started"

    env_base = os.environ.copy()
    env_base["AW_SUITE_LOCK_DIR"] = str(lock_dir)
    env_base["AW_SUITE_SLOTS"] = "1"
    env_base["AW_SUITE_SLOT_POLL_INTERVAL"] = "0.05"
    env_base["PYTHONPATH"] = str(_REPO_ROOT)
    env_base.pop("AW_SUITE_SLOT_HELD", None)

    p1 = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _WORKER_SCRIPT,
            str(log_file),
            "w1",
            "60.0",
            str(started1),
        ],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5.0
    while not started1.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert started1.exists(), "p1 did not start in time"

    holder_file = lock_dir / "suite-slot-0.holder.json"
    assert holder_file.exists()
    p1_pid = int(started1.read_text(encoding="utf-8").strip())

    os.kill(p1_pid, signal.SIGKILL)
    p1.wait()

    assert holder_file.exists()

    p2 = subprocess.Popen(
        [sys.executable, "-c", _WORKER_SCRIPT, str(log_file), "w2", "0.2"],
        env=env_base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out2, err2 = p2.communicate(timeout=10)
    assert p2.returncode == 0, f"p2 failed: {err2}"

    records = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").strip().splitlines()
    ]
    r2 = next(r for r in records if r["id"] == "w2")
    assert r2["slot_acquired"] is True


def test_stall_watchdog_heartbeat_e2e_oc(tmp_path: Path):
    """Cell (g) OpenCode: child touching heartbeat is not reaped; control child is reaped with StallTimeout."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)

    worktree, run_dir, prompt_path, plan_path = _make_fake_agent_repo(tmp_path)
    (tmp_path / "bin").mkdir(parents=True, exist_ok=True)
    hb_child = support.make_fake_executable(
        tmp_path / "bin" / "hb_child", _HEARTBEAT_CHILD_CODE
    )
    ctl_child = support.make_fake_executable(
        tmp_path / "bin" / "ctl_child", _CONTROL_CHILD_CODE
    )

    item = {"position": 1, "id6": "abc123", "setid": "demo"}

    env_patch = {
        "AW_SUITE_LOCK_DIR": str(lock_dir),
        "PYTHONPATH": str(_REPO_ROOT),
    }

    with mock.patch.dict(os.environ, env_patch):
        os.environ.pop("AW_SUITE_SLOT_HELD", None)

        # 1. Heartbeat child: silent on stdout for 1.8s, touches heartbeat every 0.15s -> NOT reaped
        state_hb = {
            "run_id": "run-test-e2e",
            "options": {
                "opencode": str(hb_child),
                "stall_timeout": 1.0,
                "timeout": 10.0,
            },
            "repo": str(tmp_path),
            "queue": [],
        }
        with (
            mock.patch(
                "agent_workflows.oc_runipd.observe_opencode_policy",
                return_value="observed",
            ),
            mock.patch("agent_workflows.lane_containment.record_host_posture"),
        ):
            rc, session_id, log_path, argv = oc_runipd.run_opencode(
                state=state_hb,
                run_dir=run_dir,
                item=item,
                plan_path=plan_path,
                prompt_path=prompt_path,
                attempt_no=1,
                work_dir=str(worktree),
            )
            assert rc == 0
            hb_file = suite_cache.heartbeat_path("run-test-e2e", "abc123")
            assert hb_file is not None and not hb_file.exists()

        # 2. Control child: silent for 1.8s, touches nothing -> StallTimeout raised after ~1s
        state_ctl = {
            "run_id": "run-test-e2e",
            "options": {
                "opencode": str(ctl_child),
                "stall_timeout": 1.0,
                "timeout": 10.0,
            },
            "repo": str(tmp_path),
            "queue": [],
        }
        with (
            mock.patch(
                "agent_workflows.oc_runipd.observe_opencode_policy",
                return_value="observed",
            ),
            mock.patch("agent_workflows.lane_containment.record_host_posture"),
        ):
            with pytest.raises(runner_shared.StallTimeout):
                oc_runipd.run_opencode(
                    state=state_ctl,
                    run_dir=run_dir,
                    item=item,
                    plan_path=plan_path,
                    prompt_path=prompt_path,
                    attempt_no=2,
                    work_dir=str(worktree),
                )


def test_stall_watchdog_heartbeat_e2e_agy(tmp_path: Path):
    """Cell (g) Agy: child touching heartbeat is not reaped; control child is reaped with StallTimeout."""
    lock_dir = tmp_path / "lock"
    lock_dir.mkdir(mode=0o700)

    worktree, run_dir, prompt_path, _ = _make_fake_agent_repo(tmp_path)
    (tmp_path / "bin").mkdir(parents=True, exist_ok=True)
    hb_child = support.make_fake_executable(
        tmp_path / "bin" / "hb_agy_child", _HEARTBEAT_CHILD_CODE
    )
    ctl_child = support.make_fake_executable(
        tmp_path / "bin" / "ctl_agy_child", _CONTROL_CHILD_CODE
    )

    item = {"position": 1, "id6": "xyz789", "setid": "demo"}

    env_patch = {
        "AW_SUITE_LOCK_DIR": str(lock_dir),
        "PYTHONPATH": str(_REPO_ROOT),
    }

    with mock.patch.dict(os.environ, env_patch):
        os.environ.pop("AW_SUITE_SLOT_HELD", None)

        # 1. Heartbeat child: silent on stdout for 1.8s, touches heartbeat every 0.15s -> NOT reaped
        state_hb = {
            "run_id": "run-test-e2e-agy",
            "options": {
                "agy_executable": str(hb_child),
                "stall_timeout": 1.0,
                "timeout": 10.0,
            },
            "repo": str(tmp_path),
            "queue": [],
        }
        with mock.patch("agent_workflows.lane_containment.record_host_posture"):
            rc, session_id, log_path, argv = agy_runipd.run_agy_turn(
                state=state_hb,
                run_dir=run_dir,
                item=item,
                prompt_path=prompt_path,
                attempt_no=1,
                session_id=None,
                use_continue=False,
                work_dir=str(worktree),
            )
            assert rc == 0
            hb_file = suite_cache.heartbeat_path("run-test-e2e-agy", "xyz789")
            assert hb_file is not None and not hb_file.exists()

        # 2. Control child: silent for 1.8s, touches nothing -> StallTimeout raised after ~1s
        state_ctl = {
            "run_id": "run-test-e2e-agy",
            "options": {
                "agy_executable": str(ctl_child),
                "stall_timeout": 1.0,
                "timeout": 10.0,
            },
            "repo": str(tmp_path),
            "queue": [],
        }
        with mock.patch("agent_workflows.lane_containment.record_host_posture"):
            with pytest.raises(runner_shared.StallTimeout):
                agy_runipd.run_agy_turn(
                    state=state_ctl,
                    run_dir=run_dir,
                    item=item,
                    prompt_path=prompt_path,
                    attempt_no=2,
                    session_id=None,
                    use_continue=False,
                    work_dir=str(worktree),
                )
