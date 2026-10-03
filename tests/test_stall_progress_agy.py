#!/usr/bin/env python3
"""Tests for AgyTranscriptProgressObserver and stall watchdog progress checks."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


from agent_workflows import agy_runipd, oc_runipd, runner_shared, stall_progress


def test_agy_observer_background_task_activation(tmp_path: Path) -> None:
    """Observer remains inactive until background task activity is observed."""
    app_data = tmp_path / "app_data"
    cid = "test-conv-001"
    observer = stall_progress.AgyTranscriptProgressObserver(
        conversation_id=cid,
        app_data_dir=app_data,
        start_at_end=True,
    )
    assert not observer.background_tasks_active

    # An ordinary stdout line does not activate background tasks
    observer.note_stdout_line('{"event":"step_update","step_update":{"step_index":1}}')
    assert not observer.background_tasks_active

    # Host waiting line activates background tasks
    host_wait_line = "root agent idle; waiting up to 4h0m0s for 2 background task(s)"
    observer.note_stdout_line(host_wait_line)
    assert observer.background_tasks_active
    assert observer.task_count == 2


def test_agy_observer_tool_announcement_activation(tmp_path: Path) -> None:
    """Tool invocations like schedule activate background tasks."""
    app_data = tmp_path / "app_data"
    cid = "test-conv-002"
    observer = stall_progress.AgyTranscriptProgressObserver(
        conversation_id=cid,
        app_data_dir=app_data,
        start_at_end=True,
    )
    assert not observer.background_tasks_active

    # Schedule tool call line
    schedule_line = json.dumps(
        {
            "event": "step_update",
            "step_update": {
                "step_index": 5,
                "tool_name": "schedule",
                "tool_info": {
                    "name": "schedule",
                    "parameters": {"DurationSeconds": 60},
                },
            },
        }
    )
    observer.note_stdout_line(schedule_line)
    assert observer.background_tasks_active


def test_agy_observer_learns_conversation_id(tmp_path: Path) -> None:
    """Observer extracts conversation_id from stream lines if not provided upfront."""
    app_data = tmp_path / "app_data"
    observer = stall_progress.AgyTranscriptProgressObserver(
        conversation_id=None,
        app_data_dir=app_data,
        start_at_end=True,
    )
    assert observer.conversation_id is None

    # Init event announces conversation_id
    init_line = json.dumps(
        {
            "event": "init",
            "conversation_id": "conv-learned-123",
            "init": {"tools": []},
        }
    )
    observer.note_stdout_line(init_line)
    assert observer.conversation_id == "conv-learned-123"


def test_agy_observer_polls_transcript_and_task_logs(tmp_path: Path) -> None:
    """Observer detects updates to transcript.jsonl and task log files when active."""
    app_data = tmp_path / "app_data"
    cid = "conv-progress-test"
    brain_dir = app_data / "brain" / cid
    logs_dir = brain_dir / ".system_generated" / "logs"
    tasks_dir = brain_dir / ".system_generated" / "tasks"
    logs_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)

    transcript = logs_dir / "transcript.jsonl"
    transcript.write_text(json.dumps({"step_index": 0}) + "\n", encoding="utf-8")

    observer = stall_progress.AgyTranscriptProgressObserver(
        conversation_id=cid,
        app_data_dir=app_data,
        start_at_end=True,
    )

    # Inactive observer yields False
    assert not observer.poll()

    # Now activate background tasks
    observer.background_tasks_active = True

    # No new data yet, so poll yields False
    assert not observer.poll()

    # Append new step to transcript
    with transcript.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"step_index": 1}) + "\n")

    assert observer.poll()
    assert observer.last_progress_source == "transcript"
    assert observer.progress_count == 1

    # Second poll with no new data returns False
    assert not observer.poll()

    # Background task writes output
    task_log = tasks_dir / "task-1.log"
    task_log.write_text("running pytest...\n", encoding="utf-8")

    assert observer.poll()
    assert observer.last_progress_source == "task"
    assert observer.progress_count == 2

    # Appending more data to existing task log
    with task_log.open("a", encoding="utf-8") as f:
        f.write("test_something passed\n")

    assert observer.poll()
    assert observer.last_progress_source == "task"
    assert observer.progress_count == 3


def test_agy_observer_session_log_update(tmp_path: Path) -> None:
    """Observer detects updates to optional session_log_path."""
    app_data = tmp_path / "app_data"
    session_log = tmp_path / "sessions" / "01-test.jsonl"
    session_log.parent.mkdir(parents=True, exist_ok=True)
    session_log.write_text('{"event":"init"}\n', encoding="utf-8")

    observer = stall_progress.AgyTranscriptProgressObserver(
        conversation_id="conv-session-log",
        app_data_dir=app_data,
        session_log_path=session_log,
        start_at_end=True,
    )
    observer.background_tasks_active = True
    assert not observer.poll()

    with session_log.open("a", encoding="utf-8") as f:
        f.write('{"event":"step_update"}\n')

    assert observer.poll()
    assert observer.last_progress_source == "session"


def test_stall_watchdog_pre_reap_progress_check() -> None:
    """StallWatchdog checks progress_checker before reaping."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
    try:
        checked = []

        def checker() -> bool:
            checked.append(True)
            return (
                len(checked) == 1
            )  # First check returns True (spares reap), second False

        reaped = []
        watchdog = runner_shared.StallWatchdog(
            proc,
            timeout=0.2,
            check_interval=0.05,
            reaper=lambda p: reaped.append(p),
            progress_checker=checker,
        )

        with watchdog:
            # Sleep long enough for watchdog to hit timeout once and check
            time.sleep(0.3)
            # progress_checker returned True, so watchdog touched and did not reap
            assert not watchdog.stalled
            assert len(reaped) == 0
            assert len(checked) >= 1

            # Next timeout window: checker returns False, watchdog reaps
            time.sleep(0.3)
            assert watchdog.stalled
            assert len(reaped) == 1
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_progress_poller_with_agy_observer(tmp_path: Path) -> None:
    """ProgressPoller drives AgyTranscriptProgressObserver on background thread."""
    app_data = tmp_path / "app_data"
    cid = "conv-poller-test"
    brain_dir = app_data / "brain" / cid
    logs_dir = brain_dir / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    transcript = logs_dir / "transcript.jsonl"
    transcript.write_text("", encoding="utf-8")

    observer = stall_progress.AgyTranscriptProgressObserver(
        conversation_id=cid,
        app_data_dir=app_data,
        start_at_end=True,
    )
    observer.background_tasks_active = True

    touches = []
    poller = stall_progress.ProgressPoller(
        observer,
        touch_callbacks=(lambda: touches.append("touch"),),
        interval=0.05,
    )

    with poller:
        time.sleep(0.05)
        assert len(touches) == 0

        # Append new step
        with transcript.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"step_index": 1}) + "\n")

        # Wait for poller tick
        for _ in range(20):
            if touches:
                break
            time.sleep(0.05)

        assert len(touches) > 0


def test_runner_subclass_signatures() -> None:
    """Both host runner subclasses accept progress_checker parameter."""
    dummy_proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1)"])
    try:
        w_agy = agy_runipd.StallWatchdog(
            dummy_proc, timeout=10.0, progress_checker=lambda: True
        )
        assert w_agy.progress_checker is not None
        assert w_agy.progress_checker() is True

        w_oc = oc_runipd.StallWatchdog(
            dummy_proc, timeout=10.0, progress_checker=lambda: False
        )
        assert w_oc.progress_checker is not None
        assert w_oc.progress_checker() is False
    finally:
        dummy_proc.kill()
        dummy_proc.wait()
