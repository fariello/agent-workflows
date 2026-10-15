"""Behavioral tests for pwatch signal exits and handler restoration (IPD ww744p).

Pins:
1. SIGTERM returns exit code 143 (precedent: render_stream and oc_runipd).
2. SIGINT returns exit code 0 (clean interrupt).
3. Previous signal handlers are preserved and restored on return from in-process invocations.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import pytest

from agent_workflows import pwatch

pytestmark = pytest.mark.skipif(
    sys.platform != "linux",
    reason="pwatch requires Linux /proc to read processes",
)


def test_subprocess_sigterm_exit_143() -> None:
    p = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "pwatch",
            "-m",
            "python",
            "--interval",
            "0.3",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        assert p.stdout is not None
        first_line = p.stdout.readline()
        assert first_line, "Expected at least one header line before signaling"
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=10)
        assert p.returncode == 143
    finally:
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            p.wait(timeout=5)


def test_subprocess_sigint_exit_0() -> None:
    p = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "pwatch",
            "-m",
            "python",
            "--interval",
            "0.3",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        assert p.stdout is not None
        first_line = p.stdout.readline()
        assert first_line, "Expected at least one header line before signaling"
        os.killpg(p.pid, signal.SIGINT)
        p.wait(timeout=10)
        assert p.returncode == 0
    finally:
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            p.wait(timeout=5)


def test_inprocess_handler_restoration_after_clean_exit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def sentinel_int(_signum: int, _frame: object) -> None:
        pass

    def sentinel_term(_signum: int, _frame: object) -> None:
        pass

    old_int = signal.signal(signal.SIGINT, sentinel_int)
    old_term = signal.signal(signal.SIGTERM, sentinel_term)
    try:
        rc = pwatch.main(["-m", "python", "--once", "--no-color"])
        assert rc == 0
        assert signal.getsignal(signal.SIGINT) is sentinel_int
        assert signal.getsignal(signal.SIGTERM) is sentinel_term
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)


def test_inprocess_handler_restoration_after_sigterm(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def sentinel_int(_signum: int, _frame: object) -> None:
        pass

    def sentinel_term(_signum: int, _frame: object) -> None:
        pass

    old_int = signal.signal(signal.SIGINT, sentinel_int)
    old_term = signal.signal(signal.SIGTERM, sentinel_term)

    call_count = 0

    def bounded_sleep(_interval: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise AssertionError(
                "pwatch loop iterated more than once without exiting on SIGTERM"
            )
        os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(pwatch.time, "sleep", bounded_sleep)
    try:
        rc = pwatch.main(["-m", "python", "--no-color"])
        assert rc == 143
        assert call_count == 1
        assert signal.getsignal(signal.SIGINT) is sentinel_int
        assert signal.getsignal(signal.SIGTERM) is sentinel_term
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
