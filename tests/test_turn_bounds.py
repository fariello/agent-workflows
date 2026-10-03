"""Behavioral turn-bound coverage for spec 7ckptx A10, A10b, A10c, and A10d.

Tests in this file exercise observable outcomes and runtime behaviors: real
subprocess execution, signal termination, timeout arithmetic, launcher arming,
and prompt byte-identity. No assertion in this file reads production source code,
pins docstrings, or inspects ASTs (P16).
"""

from __future__ import annotations

import hashlib
import io
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest import mock


from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared


# --------------------------------------------------------------------------------------------------
# Task group 1: the expiry path, proven by killing real processes (A10)
# --------------------------------------------------------------------------------------------------


def test_real_child_max_turn_bound_kills_process(tmp_path: Path) -> None:
    """E-01: Max-turn bound kills an immortal real child via the default shared reaper.

    The child executes an infinite sleep loop. The TurnBoundWatch is constructed
    with the default reaper (reap=bound_expiry_reaper(proc, tmp_path, item) with
    no inner reap= override), ensuring termination is attributable to
    runner_shutdown.clean_shutdown.

    check_interval: uses the clamped interval (min(1.0, 0.3 / 4.0) = 0.075s).
    """
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time\nwhile True: time.sleep(0.05)"]
    )
    item: dict[str, Any] = {"id6": "f15tne", "position": 1, "setid": "f15tne"}
    reaper = lane_containment.bound_expiry_reaper(proc, tmp_path, item)
    bound_seconds = 0.3
    watch = lane_containment.TurnBoundWatch(
        reap=reaper,
        is_alive=lambda: proc.poll() is None,
        max_turn_timeout=bound_seconds,
        permission_timeout=0.0,
    )

    t0 = time.monotonic()
    with watch:
        try:
            rc = proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            rc = "TIMEOUT(survived)"
    elapsed = time.monotonic() - t0

    assert rc != "TIMEOUT(survived)", (
        f"child survived wait timeout (rc={rc!r} elapsed={elapsed:.3f}s "
        f"fired={watch.fired!r} record={item.get('turn_bound_expiry')})"
    )
    assert (
        isinstance(rc, int) and rc < 0
    ), f"expected negative signal returncode, got {rc}"
    assert (
        elapsed >= bound_seconds
    ), f"elapsed {elapsed:.3f}s must be >= bound {bound_seconds}s"
    assert elapsed < 3.0, f"elapsed {elapsed:.3f}s exceeded wait ceiling"
    assert watch.fired == lane_containment.BOUND_MAX_TURN

    expiry_record = item.get("turn_bound_expiry")
    assert expiry_record is not None
    assert expiry_record["bound"] == lane_containment.BOUND_MAX_TURN
    assert expiry_record["disposition"] == lane_containment.BOUND_EXPIRY_DISPOSITION


def test_real_child_permission_bound_kills_process(tmp_path: Path) -> None:
    """E-01: Permission bound kills an immortal real child after an ask is noted.

    Demonstrably not at the coarse no-progress bound: PERM * 20 <= STALL is
    explicitly asserted in the test body, and observed elapsed is strictly under STALL.
    """
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time\nwhile True: time.sleep(0.05)"]
    )
    item: dict[str, Any] = {"id6": "f15tne", "position": 1, "setid": "f15tne"}
    reaper = lane_containment.bound_expiry_reaper(proc, tmp_path, item)

    perm_seconds = 0.3
    stall_ceiling = 6.0
    assert (
        perm_seconds * 20 <= stall_ceiling
    ), "margin between permission and stall must be >= 20x"

    watch = lane_containment.TurnBoundWatch(
        reap=reaper,
        is_alive=lambda: proc.poll() is None,
        max_turn_timeout=0.0,
        permission_timeout=perm_seconds,
    )

    t0 = time.monotonic()
    with watch:
        watch.note_permission_request()
        try:
            rc = proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            rc = "TIMEOUT(survived)"
    elapsed = time.monotonic() - t0

    assert rc != "TIMEOUT(survived)", (
        f"child survived wait timeout (rc={rc!r} elapsed={elapsed:.3f}s "
        f"fired={watch.fired!r} record={item.get('turn_bound_expiry')})"
    )
    assert (
        isinstance(rc, int) and rc < 0
    ), f"expected negative signal returncode, got {rc}"
    assert (
        elapsed >= perm_seconds
    ), f"elapsed {elapsed:.3f}s must be >= bound {perm_seconds}s"
    assert (
        elapsed < stall_ceiling
    ), f"elapsed {elapsed:.3f}s must be under stall ceiling {stall_ceiling}s"
    assert watch.fired == lane_containment.BOUND_PERMISSION

    expiry_record = item.get("turn_bound_expiry")
    assert expiry_record is not None
    assert expiry_record["bound"] == lane_containment.BOUND_PERMISSION
    assert expiry_record["disposition"] == lane_containment.BOUND_EXPIRY_DISPOSITION


def test_reset_asymmetry_permission_disarmed_by_progress() -> None:
    """E-02(a) part 1: Progress disarms the permission bound (resettable)."""
    reap_calls: list[str] = []
    watch = lane_containment.TurnBoundWatch(
        reap=lambda bound, timeout: reap_calls.append(bound),
        is_alive=lambda: True,
        max_turn_timeout=0.0,
        permission_timeout=0.05,
    )
    with watch:
        watch.note_permission_request()
        watch.note_progress()
        time.sleep(0.15)

    assert (
        reap_calls == []
    ), f"reaper must not be called after note_progress: {reap_calls}"
    assert watch.fired is None


def test_reset_asymmetry_max_turn_survives_progress() -> None:
    """E-02(a) part 2: Max-turn bound is unresettable; tight progress loop does not disarm it."""
    reap_calls: list[str] = []
    watch = lane_containment.TurnBoundWatch(
        reap=lambda bound, timeout: reap_calls.append(bound),
        is_alive=lambda: True,
        max_turn_timeout=0.05,
        permission_timeout=0.0,
    )
    with watch:
        t0 = time.monotonic()
        while time.monotonic() - t0 < 0.2 and not reap_calls:
            watch.note_progress()
            time.sleep(0.01)

    assert reap_calls == [lane_containment.BOUND_MAX_TURN]
    assert watch.fired == lane_containment.BOUND_MAX_TURN


def test_dead_child_not_reaped_twice() -> None:
    """E-02(b): Dead child is not reaped; watch thread exits when is_alive() is False."""
    reap_calls: list[str] = []
    watch = lane_containment.TurnBoundWatch(
        reap=lambda bound, timeout: reap_calls.append(bound),
        is_alive=lambda: False,
        max_turn_timeout=0.05,
        permission_timeout=0.0,
    )
    with watch:
        time.sleep(0.2)

    assert reap_calls == []
    assert watch.fired is None


def test_bookkeeping_failure_does_not_block_reap(tmp_path: Path) -> None:
    """E-02(c): Bookkeeping failure (unwritable run dir) must not block the reap.

    This test is the single place in this suite where an injected reaper double
    is permitted, because observing that the reap survives an event logging
    failure requires a spy. The injected callable preserves the keyword shape
    (process, *, run_dir) required by _ReapCallable.
    """
    double_calls: list[str] = []

    def spy_reaper(process: Any, /, *, run_dir: Path) -> Any:
        double_calls.append("r")

    bad_run_dir = tmp_path / "bad\x00path"
    item: dict[str, Any] = {"id6": "t001"}
    reaper = lane_containment.bound_expiry_reaper(
        "fake_proc", bad_run_dir, item, reap=spy_reaper
    )
    reaper(lane_containment.BOUND_MAX_TURN, 0.05)

    assert double_calls == ["r"]


# --------------------------------------------------------------------------------------------------
# Task group 2: the bounds are named, defaulted and uniformly armed (A10b)
# --------------------------------------------------------------------------------------------------


def test_constants_names_defaults_and_zero_disable() -> None:
    """E-03: Names, defaults, zero-disables read from live module attributes."""
    assert lane_containment.PERMISSION_TIMEOUT == 0.0
    assert lane_containment.MAX_TURN_TIMEOUT == 14400.0
    assert lane_containment.MAX_TURN_TIMEOUT == 4 * 60 * 60.0
    assert lane_containment.HOST_CEILING_OFFSET_SECONDS == 300.0
    assert lane_containment.BOUND_PERMISSION == "permission-timeout"
    assert lane_containment.BOUND_MAX_TURN == "max-turn-timeout"
    assert lane_containment.BOUND_EXPIRY_DISPOSITION == "failed-safely"

    # Contract verification: names are ..._TIMEOUT, not ..._DEADLINE
    assert not hasattr(lane_containment, "PERMISSION_DEADLINE")
    assert not hasattr(lane_containment, "MAX_TURN_DEADLINE")

    # Zero-disable behavior: enabled is False and no thread fires
    zero_calls: list[str] = []
    watch_zero = lane_containment.TurnBoundWatch(
        reap=lambda bound, timeout: zero_calls.append(bound),
        max_turn_timeout=0,
        permission_timeout=0,
    )
    assert watch_zero.enabled is False
    with watch_zero:
        time.sleep(0.05)
    assert zero_calls == []

    # Disposition vocabulary check against shipped terminal states in runner_shared
    assert lane_containment.BOUND_EXPIRY_DISPOSITION in runner_shared.TERMINAL_STATES


def _setup_launcher_run_dir(
    tmp_path: Path,
) -> tuple[dict[str, Any], Path, dict[str, Any], Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")
    prompt_path = run_dir / "prompt.md"
    prompt_path.write_text("prompt content", encoding="utf-8")
    state = {"run_id": "run-test", "repo": str(repo), "options": {}}
    item = {"id6": "wir001", "position": 1, "setid": "testset", "action": "execute"}
    return state, run_dir, item, plan_path, prompt_path


def test_launcher_uniform_arming_opencode(tmp_path: Path) -> None:
    """E-04: oc launcher arms TurnBoundWatch uniformly for isolated and non-isolated turns.

    Per OQ-01 and backlog cfgj8s, policy contrast is omitted to maintain hermeticity
    across ambient execution environments, asserting solely the uniform bound arming
    demanded by A10b.
    """
    state, run_dir, item, plan_path, prompt_path = _setup_launcher_run_dir(tmp_path)
    lane_dir = tmp_path / "lane"
    lane_dir.mkdir(parents=True, exist_ok=True)

    class FakeProc:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.pid = 12345
            self.stdout = io.StringIO("")
            self.returncode = 0

        def poll(self) -> int:
            return 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

    spy_calls: list[dict[str, Any]] = []
    real_watch = lane_containment.TurnBoundWatch

    def spy_watch(*args: Any, **kwargs: Any) -> lane_containment.TurnBoundWatch:
        spy_calls.append(kwargs)
        return real_watch(*args, **kwargs)

    with (
        mock.patch.object(lane_containment, "TurnBoundWatch", side_effect=spy_watch),
        mock.patch("subprocess.Popen", side_effect=FakeProc),
        mock.patch.object(oc_runipd, "observe_opencode_policy", return_value=None),
    ):
        # Non-isolated turn
        spy_calls.clear()
        oc_runipd.run_opencode(
            state, run_dir, item, plan_path, prompt_path, 1, work_dir=None
        )
        assert len(spy_calls) == 1
        non_iso_timeout = spy_calls[0].get("max_turn_timeout")
        assert non_iso_timeout == 14400.0

        # Isolated turn
        spy_calls.clear()
        oc_runipd.run_opencode(
            state, run_dir, item, plan_path, prompt_path, 1, work_dir=str(lane_dir)
        )
        assert len(spy_calls) == 1
        iso_timeout = spy_calls[0].get("max_turn_timeout")
        assert iso_timeout == 14400.0

        assert non_iso_timeout == iso_timeout


def test_launcher_uniform_arming_antigravity(tmp_path: Path) -> None:
    """E-04: agy launcher arms TurnBoundWatch uniformly for isolated and non-isolated turns."""
    state, run_dir, item, _, prompt_path = _setup_launcher_run_dir(tmp_path)
    lane_dir = tmp_path / "lane"
    lane_dir.mkdir(parents=True, exist_ok=True)

    class FakeProc:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.pid = 12345
            self.stdout = io.StringIO("")
            self.returncode = 0

        def poll(self) -> int:
            return 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

    spy_calls: list[dict[str, Any]] = []
    real_watch = lane_containment.TurnBoundWatch

    def spy_watch(*args: Any, **kwargs: Any) -> lane_containment.TurnBoundWatch:
        spy_calls.append(kwargs)
        return real_watch(*args, **kwargs)

    with (
        mock.patch.object(lane_containment, "TurnBoundWatch", side_effect=spy_watch),
        mock.patch("subprocess.Popen", side_effect=FakeProc),
    ):
        # Non-isolated turn
        spy_calls.clear()
        agy_runipd.run_agy_turn(
            state,
            run_dir,
            item,
            prompt_path,
            1,
            session_id=None,
            use_continue=False,
            work_dir=None,
        )
        assert len(spy_calls) == 1
        non_iso_timeout = spy_calls[0].get("max_turn_timeout")
        assert non_iso_timeout == 14100.0

        # Isolated turn
        spy_calls.clear()
        agy_runipd.run_agy_turn(
            state,
            run_dir,
            item,
            prompt_path,
            1,
            session_id=None,
            use_continue=False,
            work_dir=str(lane_dir),
        )
        assert len(spy_calls) == 1
        iso_timeout = spy_calls[0].get("max_turn_timeout")
        assert iso_timeout == 14100.0

        assert non_iso_timeout == iso_timeout


def test_non_isolated_prompt_byte_identical_and_names_neither_bound(
    tmp_path: Path,
) -> None:
    """E-05: Non-isolated prompt is byte-identical and names neither bound constant.

    Note that byte-identity is between two builds at the same bound value (omitted vs
    explicit lane_root=None). Changing MAX_TURN_TIMEOUT does affect the prompt text
    because runner_shared.build_turn_budget_notice renders the numeric ceiling.
    """
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    plan = repo / "plan.ipd.md"
    plan.write_text("# Sample Plan\n", encoding="utf-8")
    item = {
        "id6": "aaaaaa",
        "setid": "testset",
        "position": 1,
        "configured_file": "plan.ipd.md",
        "attempts": [],
        "action": "execute",
    }
    state = {"run_id": "run-test", "repo": str(repo), "options": {}}

    # OpenCode prompt
    oc_prompt_1 = oc_runipd.build_prompt(item, state, run_dir, plan, False)
    oc_prompt_2 = oc_runipd.build_prompt(
        item, state, run_dir, plan, False, lane_root=None
    )
    oc_sha_1 = hashlib.sha256(oc_prompt_1.encode("utf-8")).hexdigest()
    oc_sha_2 = hashlib.sha256(oc_prompt_2.encode("utf-8")).hexdigest()
    assert oc_sha_1 == oc_sha_2
    for forbidden in ("MAX_TURN_TIMEOUT", "PERMISSION_TIMEOUT", "lane-submissions"):
        assert forbidden not in oc_prompt_1

    # Antigravity prompt
    agy_prompt_1 = agy_runipd.build_prompt(item, state, run_dir, plan, False)
    agy_prompt_2 = agy_runipd.build_prompt(
        item, state, run_dir, plan, False, lane_root=None
    )
    agy_sha_1 = hashlib.sha256(agy_prompt_1.encode("utf-8")).hexdigest()
    agy_sha_2 = hashlib.sha256(agy_prompt_2.encode("utf-8")).hexdigest()
    assert agy_sha_1 == agy_sha_2
    for forbidden in ("MAX_TURN_TIMEOUT", "PERMISSION_TIMEOUT", "lane-submissions"):
        assert forbidden not in agy_prompt_1

    # Value sensitivity demonstration: ceiling number is rendered into budget notice
    notice = runner_shared.build_turn_budget_notice(
        {"options": {"turn_ceiling": 14100.0}}
    )
    assert "14100 seconds (about 3.9 hours)" in notice


# --------------------------------------------------------------------------------------------------
# Task group 3: the unproven detector and the host overlap (A10c, A10d)
# --------------------------------------------------------------------------------------------------


def test_antigravity_overlap_and_attribution(tmp_path: Path) -> None:
    """E-06: Antigravity overlap arithmetic and behavioral attribution (A10d).

    Per F6, the documentation prose is human-verified in the artifact rather than
    asserted via code-pinning text checks (P16). The behavior it describes is tested here.
    """
    host_timeout_str = agy_runipd.DEFAULT_TIMEOUT
    parsed_host_ceiling = lane_containment.parse_host_ceiling_seconds(host_timeout_str)
    assert parsed_host_ceiling == 14400.0
    assert (
        parsed_host_ceiling != 240.0
    ), "parse must interpret 240m as minutes, not bare seconds"

    driver_bound = lane_containment.driver_bound_for_host(parsed_host_ceiling)
    assert (
        driver_bound < parsed_host_ceiling
    ), "driver bound must fire strictly before host ceiling"
    gap = parsed_host_ceiling - driver_bound
    assert gap == lane_containment.HOST_CEILING_OFFSET_SECONDS == 300.0
    assert driver_bound == 14100.0

    # OpenCode has no host ceiling (None) -> unreduced default
    assert lane_containment.driver_bound_for_host(None) == 14400.0

    # Unparseable ceiling falls back to None and preserves default
    parsed_junk = lane_containment.parse_host_ceiling_seconds("banana")
    assert parsed_junk is None
    assert lane_containment.driver_bound_for_host(parsed_junk) == 14400.0

    # Behavioral attribution: post-mortem record explicitly names max-turn-timeout
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time\nwhile True: time.sleep(0.05)"]
    )
    item: dict[str, Any] = {"id6": "f15tne", "position": 1, "setid": "f15tne"}
    reaper = lane_containment.bound_expiry_reaper(proc, tmp_path, item)
    watch = lane_containment.TurnBoundWatch(
        reap=reaper,
        is_alive=lambda: proc.poll() is None,
        max_turn_timeout=0.3,
        permission_timeout=0.0,
    )
    with watch:
        try:
            rc = proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            rc = "TIMEOUT(survived)"

    assert rc != "TIMEOUT(survived)"
    assert item["turn_bound_expiry"]["bound"] == lane_containment.BOUND_MAX_TURN


def test_permission_bound_disabled_by_default_and_unproven_detector(
    tmp_path: Path,
) -> None:
    """E-07: Permission bound disabled by default; max-turn bound is sole cover (A10c option ii).

    RECORDED FINDING (2026-09-30, HEAD e9d397a4): The permission detector is unproven
    and note_permission_request has ZERO production call sites in agent_workflows/ or
    tools/. Both drivers call note_progress() on every stdout line, but neither arms
    the permission bound. Thus PERMISSION_TIMEOUT ships at 0.0 (disabled) and MAX_TURN_TIMEOUT
    is currently the only bound covering a permission deadlock. Tracked by carrier 4xtpvg.

    Behavioral test:
    (a) Default remains disabled: PERMISSION_TIMEOUT == 0.0 and default watch never fires
        even with an ask noted.
    (b) Off by default is not unimplemented: armed watch differs from default.
    (c) Real wedged child without permission observation is terminated by MAX_TURN_TIMEOUT alone.
        Note: note_permission_request is NEVER called in this test.
    """
    assert lane_containment.PERMISSION_TIMEOUT == 0.0

    # (a) Default construction does not fire on permission request
    reap_calls: list[str] = []
    watch_default = lane_containment.TurnBoundWatch(
        reap=lambda bound, timeout: reap_calls.append(bound),
        is_alive=lambda: True,
        max_turn_timeout=0.0,
    )
    assert watch_default.permission_timeout == 0.0
    assert not watch_default.enabled
    with watch_default:
        watch_default.note_permission_request()
        time.sleep(0.05)
    assert reap_calls == []

    # (b) Armed construction is enabled
    watch_armed = lane_containment.TurnBoundWatch(
        reap=lambda bound, timeout: reap_calls.append(bound),
        is_alive=lambda: True,
        max_turn_timeout=0.0,
        permission_timeout=0.05,
    )
    assert watch_armed.permission_timeout == 0.05
    assert watch_armed.enabled is True

    # (c) Max-turn alone terminates real wedged child with zero permission observations
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time\nwhile True: time.sleep(0.05)"]
    )
    item: dict[str, Any] = {"id6": "f15tne", "position": 1, "setid": "f15tne"}
    reaper = lane_containment.bound_expiry_reaper(proc, tmp_path, item)
    watch_max_only = lane_containment.TurnBoundWatch(
        reap=reaper,
        is_alive=lambda: proc.poll() is None,
        max_turn_timeout=0.3,
        permission_timeout=0.0,
    )
    with watch_max_only:
        # Deliberately do NOT call note_permission_request()
        try:
            rc = proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            rc = "TIMEOUT(survived)"

    assert rc != "TIMEOUT(survived)"
    assert item["turn_bound_expiry"]["bound"] == lane_containment.BOUND_MAX_TURN
