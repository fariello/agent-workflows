"""Behavioral tests for the core tier selection mechanism and budget guard (E-05).

Asserts that:
- A bare pytest run selects only core-marked tests.
- An explicit path invocation runs all non-slow tests (including non-core).
- AW_TEST_TIER=thorough runs all tests even on bare pytest.
- Over-budget with enforce exits nonzero and prints the slowest list.
- Over-budget with AW_CORE_BUDGET_ENFORCE=0 prints a warning and exits 0.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import pytest

pytestmark = pytest.mark.core

CONFTEST_HOOKS = """
import os
import sys
import time
import pytest

@pytest.hookimpl
def pytest_collection_modifyitems(config, items):
    args_source = getattr(config, "args_source", None)
    testpaths_source = getattr(getattr(pytest, "Config", None), "ArgsSource", None) and getattr(pytest.Config.ArgsSource, "TESTPATHS", None)
    if testpaths_source is not None and args_source == testpaths_source and os.environ.get("AW_TEST_TIER") != "thorough":
        config._core_filter_applied = True
        core_items = []
        deselected_items = []
        for item in items:
            if item.get_closest_marker("core") is not None:
                core_items.append(item)
            else:
                deselected_items.append(item)
        if deselected_items:
            config.hook.pytest_deselected(items=deselected_items)
            items[:] = core_items

_CORE_TEST_DURATIONS = []

@pytest.hookimpl
def pytest_sessionstart(session):
    session.config._core_session_start_time = time.perf_counter()
    _CORE_TEST_DURATIONS.clear()

@pytest.hookimpl
def pytest_runtest_logreport(report):
    if report.when == "call" and hasattr(report, "duration") and hasattr(report, "nodeid"):
        _CORE_TEST_DURATIONS.append((report.duration, report.nodeid))

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if "PYTEST_XDIST_WORKER" in os.environ:
        return
    if not getattr(session.config, "_core_filter_applied", False):
        return
    start_time = getattr(session.config, "_core_session_start_time", None)
    if start_time is None:
        return
    elapsed = time.perf_counter() - start_time
    budget_env = os.environ.get("AW_CORE_BUDGET_SECONDS")
    budget = float(budget_env) if budget_env else 30.0
    if elapsed > budget:
        durations = list(_CORE_TEST_DURATIONS)
        durations.sort(key=lambda x: x[0], reverse=True)
        slowest = durations[:10]
        slowest_lines = "\\n".join(f"  {idx + 1:2d}. {dur:6.2f}s  {nodeid}" for idx, (dur, nodeid) in enumerate(slowest))
        msg = (
            f"\\n================================ CORE TIER BUDGET EXCEEDED ================================\\n"
            f"Core tier wall time: {elapsed:.2f}s exceeded budget of {budget:.2f}s.\\n"
            f"Top 10 slowest core tests:\\n{slowest_lines}\\n"
            f"===========================================================================================\\n"
        )
        cpu_count = int(os.environ.get("AW_TEST_CPU_COUNT", str(os.cpu_count() or 1)))
        enforce = os.environ.get("AW_CORE_BUDGET_ENFORCE") != "0"
        if cpu_count >= 12 and enforce:
            sys.stderr.write(msg)
            session.exitstatus = 1
        else:
            sys.stderr.write(f"\\nWARNING: {msg}")
"""


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
        'markers = ["core: core tests"]\n',
        encoding="utf-8",
    )
    conftest = tmp_path / "conftest.py"
    conftest.write_text(CONFTEST_HOOKS, encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_demo = tests_dir / "test_demo.py"
    test_demo.write_text(
        "import pytest\n"
        "import time\n"
        "@pytest.mark.core\n"
        "def test_core_one():\n"
        "    time.sleep(0.05)\n"
        "def test_non_core_one():\n"
        "    pass\n",
        encoding="utf-8",
    )
    return tmp_path


def _clean_env(**overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTEST_XDIST_WORKER", None)
    env.pop("AW_TEST_TIER", None)
    env.update(overrides)
    return env


def test_bare_run_selects_core_only(temp_project: Path) -> None:
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-o", "addopts="],
        cwd=temp_project,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )
    assert res.returncode == 0
    assert "1 passed" in res.stdout
    assert "1 deselected" in res.stdout


def test_explicit_path_runs_non_core(temp_project: Path) -> None:
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_demo.py", "-q", "-o", "addopts="],
        cwd=temp_project,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )
    assert res.returncode == 0
    assert "2 passed" in res.stdout
    assert "deselected" not in res.stdout


def test_thorough_env_runs_all(temp_project: Path) -> None:
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-o", "addopts="],
        cwd=temp_project,
        capture_output=True,
        text=True,
        env=_clean_env(AW_TEST_TIER="thorough"),
    )
    assert res.returncode == 0
    assert "2 passed" in res.stdout
    assert "deselected" not in res.stdout


def test_budget_exceeded_enforced_fails(temp_project: Path) -> None:
    env = _clean_env(
        AW_CORE_BUDGET_SECONDS="0.01",
        AW_CORE_BUDGET_ENFORCE="1",
        AW_TEST_CPU_COUNT="12",
    )
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-o", "addopts="],
        cwd=temp_project,
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode != 0
    combined = res.stdout + res.stderr
    assert "CORE TIER BUDGET EXCEEDED" in combined
    assert "test_core_one" in combined


def test_budget_exceeded_enforce_zero_warns(temp_project: Path) -> None:
    env = _clean_env(
        AW_CORE_BUDGET_SECONDS="0.01",
        AW_CORE_BUDGET_ENFORCE="0",
        AW_TEST_CPU_COUNT="12",
    )
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-o", "addopts="],
        cwd=temp_project,
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0
    combined = res.stdout + res.stderr
    assert "CORE TIER BUDGET EXCEEDED" in combined
    assert "WARNING:" in combined
    assert "test_core_one" in combined
