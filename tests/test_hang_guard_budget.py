"""Behavioral outcome tests for the dual-budget per-test hang guard (IPD 6ye76g).

Tests observable behavior and outcomes (P16): drives the hang guard through real
pytest subprocesses and asserts on exit codes and stdout/stderr output. Never reads
or inspects conftest.py as text, AST, or source.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _run_pytest_subprocess(
    test_body: str,
    *,
    tmp_path: Path,
    extra_args: tuple[str, ...] = (),
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute pytest against a scratch test file in tmp_path with conftest loaded."""
    test_file = tmp_path / "test_case.py"
    test_file.write_text(test_body, encoding="utf-8")
    env = os.environ.copy()
    repo_root = str(Path(__file__).resolve().parent.parent)
    current_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{current_pp}".rstrip(os.pathsep)
    if env_overrides:
        env.update(env_overrides)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-p",
        "conftest",
        "-q",
        *extra_args,
        str(test_file),
    ]
    return subprocess.run(
        cmd,
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )


def test_cpu_runaway_caught_and_named(tmp_path: Path) -> None:
    """A CPU-burning spin is caught and specifically named as a CPU budget overrun."""
    code = """
def test_spin():
    while True:
        pass
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "0.5", "AW_TEST_WALL_TIMEOUT": "15"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0
    assert "TEST HANG GUARD" in combined
    assert "CPU budget" in combined
    assert "TestHangTimeout" in combined


def test_syscall_bound_spin_caught_by_cpu_arm(tmp_path: Path) -> None:
    """A syscall-heavy loop is caught by ITIMER_PROF counting system CPU."""
    code = """
import os
def test_syscall_spin():
    fd = os.open("/dev/zero", os.O_RDONLY)
    try:
        while True:
            os.read(fd, 1024 * 1024)
    finally:
        os.close(fd)
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "0.5", "AW_TEST_WALL_TIMEOUT": "15"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0
    assert "TEST HANG GUARD" in combined
    assert "CPU budget" in combined


def test_sleep_past_cpu_budget_inside_wall_ceiling_passes(tmp_path: Path) -> None:
    """A sleeping test that exceeds the CPU budget but stays under the wall ceiling passes."""
    code = """
import time
def test_sleep():
    time.sleep(1.2)
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "0.5", "AW_TEST_WALL_TIMEOUT": "15"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode == 0, f"Expected 0, got {res.returncode}:\n{combined}"
    assert "1 passed" in combined
    assert "TEST HANG GUARD" not in combined


def test_zero_cpu_deadlock_caught_by_wall_ceiling(tmp_path: Path) -> None:
    """A zero-CPU deadlock is caught and named as a wall ceiling overrun."""
    code = """
import threading
def test_deadlock():
    threading.Event().wait(10.0)
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "15", "AW_TEST_WALL_TIMEOUT": "1"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0
    assert "TEST HANG GUARD" in combined
    assert "wall ceiling" in combined


def test_subprocess_bound_runaway_loop_caught_by_wall_ceiling(tmp_path: Path) -> None:
    """A subprocess-bound loop (8l8dgb shape) with minimal parent CPU is caught by the wall ceiling."""
    code = """
import subprocess, sys
def test_subproc_loop():
    while True:
        subprocess.run([sys.executable, "-c", "pass"])
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "15", "AW_TEST_WALL_TIMEOUT": "2"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0
    assert "TEST HANG GUARD" in combined
    assert "wall ceiling" in combined


def test_timeout_zero_disables_both_arms(tmp_path: Path) -> None:
    """AW_TEST_TIMEOUT=0 disables both arms of the guard."""
    code = """
import time
def test_disabled_guard():
    time.sleep(1.5)
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "0", "AW_TEST_WALL_TIMEOUT": "1"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode == 0, f"Expected 0, got {res.returncode}:\n{combined}"
    assert "1 passed" in combined
    assert "TEST HANG GUARD" not in combined


def test_marker_lowers_cpu_budget(tmp_path: Path) -> None:
    """A per-test marker @pytest.mark.timeout lowers the CPU budget."""
    code = """
import pytest
@pytest.mark.timeout(0.5)
def test_marked_spin():
    while True:
        pass
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_TIMEOUT": "60", "AW_TEST_WALL_TIMEOUT": "15"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0
    assert "TEST HANG GUARD" in combined
    assert "CPU budget" in combined


def test_marker_above_wall_ceiling_floors_and_raises_wall_allowance(
    tmp_path: Path,
) -> None:
    """A marker with a value above the ambient wall ceiling raises that test's wall allowance."""
    code = """
import pytest, time
@pytest.mark.timeout(3)
def test_sleep_with_marker_floor():
    time.sleep(1.5)
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        env_overrides={"AW_TEST_WALL_TIMEOUT": "1"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode == 0, f"Expected 0, got {res.returncode}:\n{combined}"
    assert "1 passed" in combined
    assert "TEST HANG GUARD" not in combined


def test_guard_under_xdist_workers(tmp_path: Path) -> None:
    """The guard functions identically inside pytest-xdist worker processes (-n 2)."""
    code = """
def test_xdist_spin():
    while True:
        pass
"""
    res = _run_pytest_subprocess(
        code,
        tmp_path=tmp_path,
        extra_args=("-n", "2"),
        env_overrides={"AW_TEST_TIMEOUT": "0.5", "AW_TEST_WALL_TIMEOUT": "15"},
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0
    assert "TEST HANG GUARD" in combined
    assert "CPU budget" in combined
