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
import tempfile
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
        cpu_count = int(os.environ.get("AW_TEST_CPU_COUNT", str(os.cpu_count() or 1)))
        enforce = os.environ.get("AW_CORE_BUDGET_ENFORCE") != "0"
        load_avg = None
        env_load = os.environ.get("AW_TEST_LOADAVG")
        if env_load is not None:
            try:
                load_avg = float(env_load)
            except ValueError:
                load_avg = None
        else:
            try:
                load_avg = os.getloadavg()[0]
            except (OSError, AttributeError):
                load_avg = None
        if load_avg is not None:
            load_line = f"Host 1-minute load average: {load_avg:.2f} on {cpu_count} CPUs"
        else:
            load_line = f"Host 1-minute load average: unknown on {cpu_count} CPUs"
        not_enforced_reason = None
        if not enforce:
            not_enforced_reason = "AW_CORE_BUDGET_ENFORCE=0"
        elif cpu_count < 12:
            not_enforced_reason = "fewer than 12 CPUs"
        elif load_avg is not None and load_avg > cpu_count:
            not_enforced_reason = "host oversubscribed (1-minute load average above the CPU count)"
        not_enforced_line = (
            f"Core tier budget not enforced: {not_enforced_reason}\\n"
            if not_enforced_reason
            else ""
        )
        msg = (
            f"\\n================================ CORE TIER BUDGET EXCEEDED ================================\\n"
            f"Core tier wall time: {elapsed:.2f}s exceeded budget of {budget:.2f}s.\\n"
            f"{load_line}\\n"
            f"{not_enforced_line}"
            f"Top 10 slowest core tests:\\n{slowest_lines}\\n"
            f"===========================================================================================\\n"
        )
        if not_enforced_reason is None:
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
    env["AW_TEST_LOADAVG"] = "0"
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


def test_budget_exceeded_high_load_warns_and_demotes(temp_project: Path) -> None:
    env = _clean_env(
        AW_CORE_BUDGET_SECONDS="0.01",
        AW_CORE_BUDGET_ENFORCE="1",
        AW_TEST_CPU_COUNT="12",
        AW_TEST_LOADAVG="30",
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
    assert "WARNING:" in combined
    assert "CORE TIER BUDGET EXCEEDED" in combined
    assert "load average: 30.00" in combined
    assert "Core tier budget not enforced:" in combined


def test_budget_exceeded_low_load_fails(temp_project: Path) -> None:
    env = _clean_env(
        AW_CORE_BUDGET_SECONDS="0.01",
        AW_CORE_BUDGET_ENFORCE="1",
        AW_TEST_CPU_COUNT="12",
        AW_TEST_LOADAVG="2",
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
    assert "load average: 2.00" in combined
    assert "Core tier budget not enforced:" not in combined


def test_budget_exceeded_unparseable_load_fails(temp_project: Path) -> None:
    env = _clean_env(
        AW_CORE_BUDGET_SECONDS="0.01",
        AW_CORE_BUDGET_ENFORCE="1",
        AW_TEST_CPU_COUNT="12",
        AW_TEST_LOADAVG="not-a-number",
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
    assert "load average: unknown" in combined
    assert "Core tier budget not enforced:" not in combined


def _gate_env(lock_dir: Path | None = None, **overrides: str) -> dict[str, str]:
    # `run_full_suite` acquires a machine-wide test-suite slot. Point it at a private lock
    # directory so these tests never wait on slots held by the enclosing suite or peer drivers
    # (backlog twz0tw: with every real slot busy the wait outlived the 240s hang guard).
    if lock_dir is None:
        lock_dir = Path(tempfile.mkdtemp(prefix="aw-gate-suite-locks-"))
    env = _clean_env(
        AW_CORE_BUDGET_SECONDS="0.01",
        AW_TEST_CPU_COUNT="12",
        AW_SUITE_LOCK_DIR=str(lock_dir),
    )
    env.pop("AW_CORE_BUDGET_ENFORCE", None)
    env.pop("AW_SUITE_SLOT_HELD", None)
    env.update(overrides)
    return env


@pytest.mark.parametrize(
    "via_run_id", [False, True], ids=["subprocess", "run-evidence"]
)
def test_gate_suite_passes_an_all_green_over_budget_tree(
    temp_project: Path, via_run_id: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """backlog ytz6z4: the runner's gate suite must not turn a load-dependent wall-time overrun into red.

    Both launch paths of `run_full_suite` are driven (the plain subprocess path and the run-evidence
    capture path a runner uses), against a project whose only test passes but blows the core budget.
    The toy project runs with `-n 0`: its minimal conftest has no xdist relay of the core-filter flag
    (the real `tests/deselect_notice.py` has one), so under workers its budget hook would never fire.
    """
    from agent_workflows import suite_cache

    for k, v in _gate_env(temp_project / ".suite-locks").items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("AW_CORE_BUDGET_ENFORCE", raising=False)
    monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)
    run_id = None
    if via_run_id:
        run_id = "run-20261017T000000Z-1"
        monkeypatch.chdir(temp_project)
    res = suite_cache.run_full_suite(
        temp_project,
        argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"],
        use_cache=False,
        run_id=run_id,
    )
    assert res.passed, res.reason
    assert res.exit_code == 0
    assert "AW_CORE_BUDGET_ENFORCE" not in os.environ


def test_gate_suite_honors_explicit_enforce(
    temp_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An operator who explicitly sets AW_CORE_BUDGET_ENFORCE=1 still gets enforcement at the gate."""
    from agent_workflows import suite_cache

    res = suite_cache.run_full_suite(
        temp_project,
        argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"],
        use_cache=False,
        env=_gate_env(temp_project / ".suite-locks", AW_CORE_BUDGET_ENFORCE="1"),
    )
    assert not res.passed
    assert res.exit_code == 1


@pytest.mark.parametrize("launch_shape", ["subprocess", "run-evidence", "explicit-env"])
def test_gate_suite_ignores_saturated_ambient_slots(
    temp_project: Path,
    tmp_path: Path,
    launch_shape: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gate_suite tests must isolate their slot directory from ambient slot contention."""
    from agent_workflows import platform_lock, suite_cache

    ambient = tmp_path / "ambient-locks"
    ambient.mkdir(parents=True, exist_ok=True)
    os.chmod(ambient, 0o700)

    monkeypatch.setenv("AW_SUITE_LOCK_DIR", str(ambient))
    monkeypatch.setenv("AW_SUITE_SLOTS", "1")
    monkeypatch.setenv("AW_SUITE_SLOT_TIMEOUT", "5")
    monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)

    handle = platform_lock.acquire(ambient / "suite-slot-0.lock", blocking=False)
    try:
        if launch_shape == "subprocess":
            for k, v in _gate_env(temp_project / ".suite-locks").items():
                monkeypatch.setenv(k, v)
            monkeypatch.delenv("AW_CORE_BUDGET_ENFORCE", raising=False)
            monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)
            res = suite_cache.run_full_suite(
                temp_project,
                argv=[
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-o",
                    "addopts=",
                    "-n",
                    "0",
                ],
                use_cache=False,
            )
        elif launch_shape == "run-evidence":
            for k, v in _gate_env(temp_project / ".suite-locks").items():
                monkeypatch.setenv(k, v)
            monkeypatch.delenv("AW_CORE_BUDGET_ENFORCE", raising=False)
            monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)
            monkeypatch.chdir(temp_project)
            res = suite_cache.run_full_suite(
                temp_project,
                argv=[
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-o",
                    "addopts=",
                    "-n",
                    "0",
                ],
                use_cache=False,
                run_id="run-20261017T000000Z-1",
            )
        elif launch_shape == "explicit-env":
            res = suite_cache.run_full_suite(
                temp_project,
                argv=[
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-o",
                    "addopts=",
                    "-n",
                    "0",
                ],
                use_cache=False,
                env=_gate_env(
                    temp_project / ".suite-locks", AW_CORE_BUDGET_ENFORCE="0"
                ),
            )
        else:
            raise AssertionError(f"Unknown launch shape {launch_shape}")

        assert res.passed
        assert res.exit_code == 0
        assert res.slot["slot_acquired"] is True
        assert res.slot["waited_seconds"] < 2.0
    finally:
        handle.release()
