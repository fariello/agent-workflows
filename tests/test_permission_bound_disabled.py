"""Behavioral tests for the disabled-by-default PERMISSION_TIMEOUT bound.

Exercising TurnBoundWatch directly without code-structure pins (P16).
Four behaviors:
(a) Default construction does not arm permission timeout.
(b) Armed, it fires and reaps with BOUND_PERMISSION.
(c) Progress disarms a pending permission request.
(d) Without an observation, nothing arms the bound.
"""

from __future__ import annotations

import time
from typing import List, Tuple

from agent_workflows.lane_containment import (
    BOUND_PERMISSION,
    TurnBoundWatch,
)


def test_default_construction_does_not_arm() -> None:
    """Default construction does not arm permission timeout (propagating PERMISSION_TIMEOUT=0.0)."""
    reaps: List[Tuple[str, float]] = []
    # Explicit small check_interval (0.01s) so the background loop ticks quickly.
    # Note: MAX_TURN_TIMEOUT is armed by default, so watch.enabled is True and the thread runs.
    watch = TurnBoundWatch(
        reap=lambda bound, timeout: reaps.append((bound, timeout)),
        check_interval=0.01,
    )
    with watch:
        watch.note_permission_request()
        # Sleep for 0.08s, which is 8 multiples of check_interval (0.01s), allowing multiple poll ticks.
        time.sleep(0.08)

    assert reaps == []
    assert watch.fired is None


def test_armed_it_fires() -> None:
    """When permission_timeout is armed explicitly, an observed ask fires BOUND_PERMISSION."""
    reaps: List[Tuple[str, float]] = []
    permission_timeout = 0.1
    # check_interval=0.01; constructor clamps check_interval to min(0.01, 0.1/4)=0.01.
    watch = TurnBoundWatch(
        reap=lambda bound, timeout: reaps.append((bound, timeout)),
        max_turn_timeout=0.0,
        permission_timeout=permission_timeout,
        check_interval=0.01,
    )
    start_time = time.monotonic()
    with watch:
        watch.note_permission_request()
        deadline = start_time + 2.0  # 2.0s generous ceiling to avoid hangs
        while not reaps and time.monotonic() < deadline:
            time.sleep(0.005)

    elapsed = time.monotonic() - start_time
    assert len(reaps) == 1
    assert reaps[0] == (BOUND_PERMISSION, permission_timeout)
    assert watch.fired == BOUND_PERMISSION
    assert elapsed >= permission_timeout
    assert elapsed < 2.0


def test_progress_disarms_it() -> None:
    """Armed, note_permission_request then note_progress clears the ask and produces zero reaps."""
    reaps: List[Tuple[str, float]] = []
    permission_timeout = 0.1
    watch = TurnBoundWatch(
        reap=lambda bound, timeout: reaps.append((bound, timeout)),
        max_turn_timeout=0.0,
        permission_timeout=permission_timeout,
        check_interval=0.01,
    )
    with watch:
        watch.note_permission_request()
        watch.note_progress()
        # Sleep for 0.15s, past the 0.1s window and 15 multiples of check_interval (0.01s).
        time.sleep(0.15)

    assert reaps == []
    assert watch.fired is None


def test_without_observation_nothing_arms_it() -> None:
    """Armed with permission_timeout, but without note_permission_request, zero reaps occur."""
    reaps: List[Tuple[str, float]] = []
    permission_timeout = 0.1
    watch = TurnBoundWatch(
        reap=lambda bound, timeout: reaps.append((bound, timeout)),
        max_turn_timeout=0.0,
        permission_timeout=permission_timeout,
        check_interval=0.01,
    )
    with watch:
        # note_permission_request() is NEVER called
        # Sleep for 0.15s, past the 0.1s window and 15 multiples of check_interval (0.01s).
        time.sleep(0.15)

    assert reaps == []
    assert watch.fired is None
