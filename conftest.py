"""Root pytest conftest: guarantee the suite ALWAYS runs in parallel (-n auto), and
run the suite in the COORDINATOR role so a runner-launched turn measures the same
tree a human does (backlog `1uq1cu`).

The release suite is large and IO/subprocess bound; running it serially costs multiples of
the wall time, so `-n auto` (pytest-xdist, capped at half of available CPUs up to six workers,
minimum 1) is the default in
`[tool.pytest.ini_options] addopts` in pyproject.toml. That default hard-requires the
xdist plugin: without it, pytest aborts with `unrecognized arguments: -n` before any
test runs.

This guard makes that default self-healing: if `xdist` is not importable when pytest
starts, install `pytest-xdist` into the current interpreter and re-exec pytest so the
`-n auto` in addopts always has its plugin. The net effect is that EVERY pytest
invocation - `pytest`, `python -m pytest`, `make test`, or an agent shelling out raw -
runs in parallel, with no serial fallback and no manual `pip install '.[test]'` step.

This runs at conftest import time, which pytest performs during startup, before it
parses the ini `addopts` (so the `-n` option is registered by the time argument
parsing happens). It is a no-op on the common path where xdist is already installed.
"""

from __future__ import annotations

import atexit as _atexit
import faulthandler as _faulthandler
import importlib.util
import os
from pathlib import Path
import shutil as _shutil
import signal as _signal
import subprocess
import sys
import tempfile as _tempfile
import threading as _threading
import time

import pytest

# --------------------------------------------------------------------------------------
# Git config identity guard: prevent tests from leaking identity keys into .git/config
# (IPD `lp1zkb`, backlog `8o7gco`).
# --------------------------------------------------------------------------------------
#
# WHAT WENT WRONG. Between 2026-10-08 01:31:49 and 2026-10-09 09:06:05, 322 runner and
# agent commits carried `Test <test@example.com>` because a test wrote identity keys into
# the repository's shared `.git/config` (the common dir every worktree reads).
#
# WHY IDENTITY KEYS ONLY. Worktrees share the common dir config, and concurrent agents or
# runners legitimately mutate other keys (worktrees, branch tracking, remotes) during a
# run. Guarding only identity-bearing keys (`user.*`, `author.*`, `committer.*`) prevents
# false failures while strictly containing provenance corruption (decision D-1).
pytest_plugins = [
    "tests.deselect_notice",
    "tests.livecorpus_notice",
    "tests.git_config_guard",
]
os.environ.setdefault("AW_IN_TEST_SESSION", "1")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# --------------------------------------------------------------------------------------
# Pytest traceback formatting guard: prevent worker crash when tb_lineno is None.
# --------------------------------------------------------------------------------------
try:
    import _pytest._code.code as _pytest_code

    _orig_tb_entry_lineno_fget = _pytest_code.TracebackEntry.lineno.fget

    def _safe_tb_entry_lineno(self: object) -> int:
        tb_lineno = getattr(getattr(self, "_rawentry", None), "tb_lineno", None)
        if tb_lineno is None:
            return 0
        return _orig_tb_entry_lineno_fget(self)

    _pytest_code.TracebackEntry.lineno = property(_safe_tb_entry_lineno)
except Exception:
    pass


def _available_cpus() -> int:
    """Return available CPU count, respecting sched_getaffinity if available."""
    if hasattr(os, "sched_getaffinity"):
        try:
            return len(os.sched_getaffinity(0))
        except Exception:
            pass
    return os.cpu_count() or 2


# --------------------------------------------------------------------------------------
# xdist auto-num-workers hook: cap -n auto worker count and stay optional under -p no:xdist
# (backlog `6ljil4`).
#
# WHY optionalhook=True IS LOAD-BEARING. `pytest_xdist_auto_num_workers` is an
# `xdist.newhooks` hookspec registered only when `xdist.plugin` loads. When pytest is
# invoked with `-p no:xdist` (such as in `tools/replay_coverage_diff.py` serial runs or
# `python3 -m pytest -o addopts="" -p no:xdist`), pluggy's `PytestPluginManager.check_pending()`
# fails with `pluggy.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'`
# unless this hook implementation is declared with `optionalhook=True`.
# --------------------------------------------------------------------------------------
@pytest.hookimpl(optionalhook=True)
def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    """Resolve -n auto worker count.

    Use at most half the available CPUs and never more than six workers (minimum 1).
    An explicit PYTEST_XDIST_AUTO_NUM_WORKERS can lower the count, but cannot
    exceed the same limit.

    Declared with optionalhook=True because pytest_xdist_auto_num_workers is an
    xdist.newhooks hookspec loaded only when xdist.plugin is active; without
    optionalhook=True, running pytest under -p no:xdist raises PluginValidationError
    during PytestPluginManager.check_pending() (backlog `6ljil4`).
    """
    cpus = _available_cpus()
    limit = min(6, max(1, cpus // 2))
    env_var = os.environ.get("PYTEST_XDIST_AUTO_NUM_WORKERS")
    if env_var:
        try:
            return min(limit, max(1, int(env_var)))
        except ValueError:
            pass
    return limit


# --------------------------------------------------------------------------------------
# Core test tier selection: run only core-marked tests on bare pytest invocation (IPD hguae9).
# --------------------------------------------------------------------------------------
@pytest.hookimpl
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Select the core test tier on a bare pytest invocation.

    Only applies when pytest fell back to testpaths (config.args_source == ArgsSource.TESTPATHS)
    and AW_TEST_TIER is not 'thorough'. Explicit path or nodeid runs (make test-all, pytest tests/,
    pytest tests/test_foo.py) retain all non-slow tests they name.
    """
    args_source = getattr(config, "args_source", None)
    testpaths_source = getattr(
        getattr(pytest, "Config", None), "ArgsSource", None
    ) and getattr(pytest.Config.ArgsSource, "TESTPATHS", None)

    if (
        testpaths_source is not None
        and args_source == testpaths_source
        and os.environ.get("AW_TEST_TIER") != "thorough"
    ):
        config._core_filter_applied = True  # type: ignore[attr-defined]
        core_items: list[pytest.Item] = []
        deselected_items: list[pytest.Item] = []
        for item in items:
            if item.get_closest_marker("core") is not None:
                core_items.append(item)
            else:
                deselected_items.append(item)
        if deselected_items:
            config.hook.pytest_deselected(items=deselected_items)
            items[:] = core_items


_CORE_TEST_DURATIONS: list[tuple[float, str]] = []


@pytest.hookimpl
def pytest_sessionstart(session: pytest.Session) -> None:
    session.config._core_session_start_time = time.perf_counter()  # type: ignore[attr-defined]
    _CORE_TEST_DURATIONS.clear()


@pytest.hookimpl
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if (
        report.when == "call"
        and hasattr(report, "duration")
        and hasattr(report, "nodeid")
    ):
        _CORE_TEST_DURATIONS.append((report.duration, report.nodeid))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Enforce the wall-time budget on the core tier (IPD hguae9 E-05)."""
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
        slowest_lines = "\n".join(
            f"  {idx + 1:2d}. {dur:6.2f}s  {nodeid}"
            for idx, (dur, nodeid) in enumerate(slowest)
        )
        msg = (
            f"\n================================ CORE TIER BUDGET EXCEEDED ================================\n"
            f"Core tier wall time: {elapsed:.2f}s exceeded budget of {budget:.2f}s.\n"
            f"Top 10 slowest core tests:\n{slowest_lines}\n"
            f"===========================================================================================\n"
        )
        cpu_count = int(os.environ.get("AW_TEST_CPU_COUNT", str(os.cpu_count() or 1)))
        enforce = os.environ.get("AW_CORE_BUDGET_ENFORCE") != "0"
        if cpu_count >= 12 and enforce:
            sys.stderr.write(msg)
            session.exitstatus = 1
        else:
            sys.stderr.write(f"\nWARNING: {msg}")


def _load_slow_allowlist(rootpath: Path) -> dict[str, str]:
    allowlist_path = rootpath / "tests" / "slow_allowlist.txt"
    if not allowlist_path.exists():
        return {}
    allowed: dict[str, str] = {}
    for line in allowlist_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 1)
        node_id = parts[0].strip()
        reason = parts[1].strip() if len(parts) > 1 else ""
        allowed[node_id] = reason
    return allowed


@pytest.hookimpl
def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    """Report tests whose call duration exceeded threshold and are not in slow_allowlist.txt (IPD c8bfp9 E-09)."""
    if "PYTEST_XDIST_WORKER" in os.environ:
        return

    threshold_env = os.environ.get("AW_SLOW_REPORT_SECONDS")
    try:
        threshold = float(threshold_env) if threshold_env else 2.0
    except ValueError:
        threshold = 2.0

    rootpath = getattr(config, "rootpath", Path(config.rootdir))
    allowlist = _load_slow_allowlist(rootpath)

    unlisted: list[tuple[float, str]] = []
    for dur, nodeid in _CORE_TEST_DURATIONS:
        if dur > threshold and nodeid not in allowlist:
            unlisted.append((dur, nodeid))

    unlisted.sort(key=lambda x: x[0], reverse=True)

    terminalreporter.section("SLOW TESTS REPORT", yellow=True)
    if unlisted:
        terminalreporter.write_line(
            f"WARNING: {len(unlisted)} test(s) exceeded {threshold:g}s and are not listed in tests/slow_allowlist.txt:"
        )
        for dur, nodeid in unlisted:
            terminalreporter.write_line(f"  {dur:6.2f}s  {nodeid}")
    else:
        terminalreporter.write_line(
            f"0 unlisted slow tests (all tests > {threshold:g}s are documented in tests/slow_allowlist.txt)."
        )


# --------------------------------------------------------------------------------------
# The test session is a COORDINATOR, never a managed worker lane (backlog `1uq1cu`).
# --------------------------------------------------------------------------------------
#
# WHAT WENT WRONG, measured 2026-09-18 at HEAD `6ff7a7ba`. Both runners export
# `AW_EXECUTION_ROLE=worker` into an isolated execute turn's environment
# (`oc_runipd.py:5876`, `agy_runipd.py:2779`), which is correct: it marks the AGENT as a
# managed worker so `aw ipd begin`/`finalize` refuse there, because lifecycle authority
# belongs to the driver. But every plan's validation section then tells that same agent to
# run the repository suite, and the suite INHERITS the marking. `ipd_lifecycle.run_begin`
# and `run_finalize` read the ambient process environment directly
# (`worker_role_active(os.environ)`, ipd_lifecycle.py:4105 and :4285), so every in-process
# test that drives those CLI wrappers gets the worker refusal instead of the behavior it
# asserts. Measured suite-wide: `31 failed, 8080 passed` with the marking present versus
# `0 failed, 7993 passed` without it (the gap where tests inherited the ambient role was
# closed by plan yx9xsa).
#
# WHY IT MATTERS EVEN THOUGH IT CANNOT SHIP A BUG. The driver's own merge gate
# (`oc_runipd.run_suite_check`) runs in the PRIMARY checkout inheriting the DRIVER's
# unmarked environment, so integration was never at risk. The damage is to EVIDENCE: an
# agent measuring its own baseline and post-change counts sees the same 31 phantom
# failures in both, so the delta cancels and the check usually passes by luck. An agent
# that measures its baseline differently, or reads the 32 as real, either excuses a
# genuine regression or reports one that does not exist, and then pastes that number into
# a `V-*` `Observed evidence` block as fact.
#
# WHY HERE AND NOT IN THE RUNNERS. The marking on the agent is DELIBERATE and load-bearing
# (it is what makes `AW-LIFECYCLE-ROLE-001` fire on a lane agent that tries to finalize its
# own plan, incident `i452hf`), so removing it there would restore a real defect to fix a
# reporting one. The suite, by contrast, is never a managed worker: it is a test session
# that CONSTRUCTS worker environments explicitly as fixtures. Scrubbing at the session
# boundary fixes every affected test family at once (begin/finalize, worktree isolation,
# fail-closed integration, backlog-close-in-lane) without touching the guard or any
# individual fixture, and it makes a bare `python3 -m pytest` mean the same thing whether a
# human or a runner turn typed it.
#
# NO SHIPPED GUARD TEST. The scrub's invariance is not asserted by any shipped test today
# (the guard file that did so was deleted), which is why a one-off re-assert probe is the
# check.
#
# HONEST LIMITS, both deliberate. (1) Tests that drive lifecycle wrappers declare their
# role with `support.declare_execution_role`, and a test that needs the worker marking sets
# it on an explicit env dict passed to the code under test; re-asserting the marker with a
# throwaway `pytest_runtest_setup` plugin is how to check a file (as plan yx9xsa did). The scrub
# is pytest-only; `make test-serial` (`python3 -m unittest`) loads this file only through an
# explicit import, and `tests/test_xdist_auto_workers.py` restores `os.environ` around that
# import; serial unittest suites are otherwise protected only by the per-class declarations.
# (2) This scrubs the CURRENT process only; a subprocess a test spawns inherits this
# already-cleaned environment, which is the intended propagation.
#
# Done at import time, before any test module is collected, so no test can observe the
# marked value. `pop` is unconditional and side-effect-free when the variable is absent,
# which is the common case for a human-typed run.
os.environ.pop("AW_EXECUTION_ROLE", None)

# trailread (a6xbso) E-06: an agent turn now exports AW_RUN_ID and AW_ITEM_ID6, every
# plan tells that agent to run the suite, and without this scrub a test reaching
# work_cmd._trailers_from_args would read the outer run's ids and fail only inside a
# runner turn.
os.environ.pop("AW_RUN_ID", None)
os.environ.pop("AW_ITEM_ID6", None)
os.environ.pop("AW_RUNNER", None)
os.environ.pop("AW_AGENT_MODEL", None)
os.environ.pop("GIT_COMMITTER_NAME", None)
os.environ.pop("GIT_COMMITTER_EMAIL", None)

# userconfig (9y27t2) E-06: an agent turn now exports AW_CONFIG_DIR and every plan tells
# that agent to run the suite, so without this scrub the suite's own XDG_CONFIG_HOME
# sandbox would be bypassed by the outer turn's value.
os.environ.pop("AW_CONFIG_DIR", None)

# Scrub CI / AW_NONINTERACTIVE at the session boundary so tests that exercise interactive
# prompt machinery (e.g. `--interactive`, completion installation offers, confirmation prompts)
# are not forced into unattended non-interactive mode by the ambient CI runner environment.
# Tests asserting CI/non-interactive behavior set or mock these explicitly.
os.environ.pop("CI", None)
os.environ.pop("AW_NONINTERACTIVE", None)

# --------------------------------------------------------------------------------------
# Tree-relative import root: guarantee the test session and its subprocesses measure THIS
# repository tree, not an editable install pin to another checkout (IPD `lhjsu0`).
# --------------------------------------------------------------------------------------
_REPO_ROOT = str(os.path.dirname(os.path.abspath(__file__)))
if sys.path and sys.path[0] != _REPO_ROOT:
    if _REPO_ROOT in sys.path:
        sys.path.remove(_REPO_ROOT)
    sys.path.insert(0, _REPO_ROOT)

_current_pp = os.environ.get("PYTHONPATH", "")
if _REPO_ROOT not in _current_pp.split(os.pathsep):
    os.environ["PYTHONPATH"] = f"{_REPO_ROOT}{os.pathsep}{_current_pp}".rstrip(
        os.pathsep
    )


# --------------------------------------------------------------------------------------
# Home isolation: no test may read or write the developer's real AW_HOME or user config.
# --------------------------------------------------------------------------------------
#
# WHAT WENT WRONG, measured 2026-09-24. `tests/__init__.py` pointed AW_HOME and
# XDG_CONFIG_HOME at a throwaway directory, but (1) only when the caller had NOT already
# exported them, so a shell with XDG_CONFIG_HOME set got no sandbox at all; and (2) about
# twenty tests clean up with `os.environ.pop(...)` instead of restoring the previous value,
# which DELETES the sandbox for every later test in the same xdist worker. Test order is
# randomized, so any unisolated test scheduled after one of those pops wrote to the real
# home. Caught with an audit hook on a bare `python3 -m pytest`:
# `DeclarativeAllowedValuesTests` rewrote `~/.config/agent-workflows/config.json`, leaving
# `"aw_home": "~/allowed"`, and the run-analytics tests left hundreds of cache directories
# under `~/.aw/projects/` and `~/allowed/projects/`.
#
# THE FIX HAS TWO PARTS. The sandbox is established here UNCONDITIONALLY, before any test
# module is imported, so an exported value cannot opt a run out of it. Then an autouse
# fixture restores both variables after EVERY test, so a test that pops or rewrites them
# damages only itself. A test that wants a different home still sets one for its own
# duration, exactly as before.
_HOME_KEYS = ("AW_HOME", "XDG_CONFIG_HOME")
_AW_TEST_SANDBOX = _tempfile.mkdtemp(prefix="aw-test-home-")
_atexit.register(_shutil.rmtree, _AW_TEST_SANDBOX, True)
_SANDBOX_ENV = {
    "AW_HOME": _AW_TEST_SANDBOX,
    "XDG_CONFIG_HOME": os.path.join(_AW_TEST_SANDBOX, "xdg-config"),
    "AW_PROJECT_CEILING": _tempfile.gettempdir(),
}
os.environ.update(_SANDBOX_ENV)


@pytest.fixture(autouse=True)
def _restore_home_sandbox():
    """Re-point AW_HOME/XDG_CONFIG_HOME at the session sandbox around every test."""
    os.environ.update(_SANDBOX_ENV)
    os.environ.pop("AW_CONFIG_DIR", None)
    yield
    os.environ.update(_SANDBOX_ENV)
    os.environ.pop("AW_CONFIG_DIR", None)
    _xdg_dir = _SANDBOX_ENV["XDG_CONFIG_HOME"]
    if os.path.exists(_xdg_dir):
        _shutil.rmtree(_xdg_dir, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def _register_basetemp_project_ceiling(tmp_path_factory: pytest.TempPathFactory):
    """Register pytest's resolved basetemp as an AW project climb ceiling."""
    basetemp = str(tmp_path_factory.getbasetemp().resolve())
    current = _SANDBOX_ENV.get("AW_PROJECT_CEILING", "")
    updated = f"{current}{os.pathsep}{basetemp}" if current else basetemp
    _SANDBOX_ENV["AW_PROJECT_CEILING"] = updated
    os.environ["AW_PROJECT_CEILING"] = updated


# --------------------------------------------------------------------------------------
# Per-test hang guard: dual CPU budget + wall ceiling (IPD 6ye76g).
# --------------------------------------------------------------------------------------
#
# WHY, measured 2026-09-27 (run `run-20260927T174631Z-291785`, plan `8l8dgb`). A test's
# fake `execute_item` updated status only in memory while `run_queue` reloaded from disk,
# re-dispatching the same item forever. Without a guard, pytest sat silent until the runner's
# 600s stall timeout killed the whole 48-minute turn and its dependency chain.
#
# WHY DUAL BUDGET (CPU + WALL CEILING).
# The original guard measured wall clock alone (ITIMER_REAL). Under the suite's -n auto
# parallelism, machine load inflated wall durations of CPU-heavy tests (e.g. statusline
# sweep measured 29.53s isolated vs 66.53s in-suite at review, and 128.46s isolated vs 100.53s
# in-suite under lane contention) while consuming the same ~28-29s of CPU time (28.61s review,
# 29.16s measured at execution head). The guard failed correct tests because the machine was busy.
#
# To eliminate load-dependent false failures, the guard uses a DUAL budget:
# 1. CPU BUDGET (ITIMER_PROF, counting user + sys CPU): measures actual work done by the test.
#    ITIMER_PROF is used rather than ITIMER_VIRTUAL because ITIMER_VIRTUAL measures only user time
#    and is blind to syscall-bound loops (F-07: a syscall loop splits cost between user and sys).
#    Sized from the whole-suite CPU census: worst observed self-CPU in the fast suite was 28.61s
#    (29.16s re-measured at execution head). _DEFAULT_TEST_CPU_TIMEOUT = 60.0s provides >2x headroom
#    (60.0 / 28.61 = 2.10x, 60.0 / 29.16 = 2.05x).
#
# 2. WALL CEILING (ITIMER_REAL, wall clock): retained as a liveness ceiling, NOT a cost control.
#    _DEFAULT_TEST_WALL_TIMEOUT = 240.0s is well above worst unmarked in-suite wall time (66.53s
#    in F-02, 93.60s in heavy contention: 240.0 / 66.53 = 3.61x, 240.0 / 93.60 = 2.56x headroom)
#    while remaining far below the runner's 900s stall budget (oc_runipd.DEFAULT_STALL_TIMEOUT = 900.0s),
#    leaving an 11-minute (660s) safety margin so a runaway costs minutes rather than the turn.
#
# ACCEPTED BLIND SPOTS AND WHY THE WALL CEILING MUST STAY (F-05, F-13, F-15).
# Anyone tempted to delete the wall arm as redundant must review these empirical findings:
# - A CPU budget cannot see a test blocked on I/O, a lock, or a child process (deadlock):
#   F-05 tested threading.Event().wait(45) under a CPU-only guard; it consumed 0.00s CPU and
#   ran to completion untouched because a CPU timer never expires on zero-CPU waits.
# - A CPU budget cannot see a runaway LOOP whose iterations mostly wait on child processes:
#   F-13 measured parent CPU for subprocess loops (`subprocess.run([sys.executable, "-c", "pass"])`,
#   the exact shape of the founding 8l8dgb hang) at only ~1% of wall time (0.04s CPU for 3.02s wall).
#   A CPU-only timer would allow an 8l8dgb runaway loop to burn the entire runner stall timeout.
# - Signal delivery to main thread (F-15): Python delivers signal handlers in the main thread only
#   when it runs bytecode. If a background thread burns CPU while the main thread blocks in a C wait
#   like thread.join(), the SIGPROF handler is deferred until the wait ends (measured: handler ran
#   at 6.0s for a 6s spin while ITIMER_REAL ran at 1.01s). The wall arm bounds the wait.
#
# OVERRIDES AND SEMANTICS:
# - Default CPU: AW_TEST_TIMEOUT=<seconds> (default 60s). AW_TEST_TIMEOUT=0 disables BOTH arms.
# - Default Wall: AW_TEST_WALL_TIMEOUT=<seconds> (default 240s). AW_TEST_WALL_TIMEOUT=0 disables wall arm only.
# - Per-test marker: @pytest.mark.timeout(seconds, wall=None). Sets CPU budget to `seconds` AND
#   floors the wall ceiling at max(ceiling, seconds). Flooring ensures existing subprocess-heavy
#   tests with markers (e.g. timeout(500) where serial wall is 185s+ but CPU is ~0) do not trip the
#   wall ceiling (F-14). Keyword `wall=<seconds>` sets the wall ceiling explicitly.
#   A marker value of 0 (@pytest.mark.timeout(0)) disables BOTH arms.
# - Stand-down: If a test has installed its own handler for EITHER SIGALRM or SIGPROF, the guard
#   stands down completely so tests exercising alarm signals are never clobbered.
_DEFAULT_TEST_CPU_TIMEOUT = 60.0
_DEFAULT_TEST_WALL_TIMEOUT = 240.0
_DEFAULT_TEST_TIMEOUT = _DEFAULT_TEST_CPU_TIMEOUT  # backward-compatibility alias


class TestHangTimeout(BaseException):
    """Raised inside a test that exceeded its hang-guard budget.

    A `BaseException`, NOT an `Exception`, and that is the fix for a measured miss: the `8l8dgb`
    hang looped through `except Exception:` handlers that swallowed an `Exception`-based timeout
    for ~20s. Deriving from `BaseException` (as `KeyboardInterrupt` and `SystemExit` do) walks
    straight past every `except Exception`, while pytest still records it as this test's failure.
    """

    __test__ = False  # not a test class, despite the name


def _test_timeout_budgets(item) -> tuple[float, float]:
    """Return (cpu_budget, wall_budget) for the given test item."""
    raw_cpu = os.environ.get("AW_TEST_TIMEOUT", "").strip()
    if raw_cpu:
        try:
            default_cpu = float(raw_cpu)
        except ValueError:
            default_cpu = _DEFAULT_TEST_CPU_TIMEOUT
    else:
        default_cpu = _DEFAULT_TEST_CPU_TIMEOUT

    raw_wall = os.environ.get("AW_TEST_WALL_TIMEOUT", "").strip()
    if raw_wall:
        try:
            default_wall = float(raw_wall)
        except ValueError:
            default_wall = _DEFAULT_TEST_WALL_TIMEOUT
    else:
        default_wall = _DEFAULT_TEST_WALL_TIMEOUT

    # AW_TEST_TIMEOUT=0 disables both arms
    if default_cpu <= 0:
        return 0.0, 0.0

    marker = item.get_closest_marker("timeout")
    if marker is not None:
        cpu_val = None
        wall_val = None

        if marker.args:
            try:
                cpu_val = float(marker.args[0])
            except (ValueError, TypeError):
                pass
        elif "cpu" in marker.kwargs:
            try:
                cpu_val = float(marker.kwargs["cpu"])
            except (ValueError, TypeError):
                pass

        if "wall" in marker.kwargs:
            try:
                wall_val = float(marker.kwargs["wall"])
            except (ValueError, TypeError):
                pass

        # Marker value of 0 disables both arms
        if cpu_val is not None and cpu_val <= 0:
            return 0.0, 0.0

        if cpu_val is not None:
            eff_cpu = cpu_val
            eff_wall = max(default_wall, cpu_val) if wall_val is None else wall_val
        else:
            eff_cpu = default_cpu
            eff_wall = default_wall if wall_val is None else wall_val

        return eff_cpu, max(0.0, eff_wall)

    return default_cpu, max(0.0, default_wall)


def _test_timeout_seconds(item) -> float:
    """Return effective CPU timeout seconds (backward-compatibility helper)."""
    return _test_timeout_budgets(item)[0]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "timeout(seconds, wall=None): per-test hang-guard budget: sets CPU budget and floors wall ceiling at max(ceiling, seconds); wall= sets wall ceiling explicitly (0 disables).",
    )


_WIN_ACTIVE_TEST: dict[str, object] | None = None
_WIN_WATCHDOG_STARTED = False


def _ensure_win_watchdog() -> None:
    global _WIN_WATCHDOG_STARTED
    if _WIN_WATCHDOG_STARTED:
        return
    _WIN_WATCHDOG_STARTED = True

    import ctypes
    import time

    def _watchdog_loop() -> None:
        while True:
            time.sleep(0.5)
            active = _WIN_ACTIVE_TEST
            if active is None:
                continue
            deadline = float(active["deadline"])  # type: ignore[arg-type]
            if time.monotonic() < deadline:
                continue
            nodeid = str(active["nodeid"])
            wall_b = float(active["wall_budget"])  # type: ignore[arg-type]
            tid = int(active["tid"])  # type: ignore[arg-type]
            if not active.get("dumped"):
                active["dumped"] = True
                msg = (
                    f"\n[conftest] TEST HANG GUARD: {nodeid} exceeded {wall_b:g}s wall ceiling; "
                    "stacks of every thread at expiry follow.\n"
                )
                for stream in (sys.stderr, getattr(sys, "__stderr__", None)):
                    if stream is not None:
                        try:
                            stream.write(msg)
                            _faulthandler.dump_traceback(file=stream, all_threads=True)
                            stream.flush()
                        except Exception:
                            pass
            try:
                from agent_workflows import runner_shutdown

                for child in runner_shutdown.live_children():
                    runner_shutdown.signal_process(child, _signal.SIGTERM)
            except Exception:
                pass
            try:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulong(tid), ctypes.py_object(TestHangTimeout)
                )
            except Exception:
                pass

    _threading.Thread(
        target=_watchdog_loop, name="conftest-win-hang-guard", daemon=True
    ).start()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    cpu_budget, wall_budget = _test_timeout_budgets(item)
    if cpu_budget <= 0 and wall_budget <= 0:
        yield
        return

    # Guard runs on POSIX main thread via SIGALRM/ITIMER_REAL, with a watchdog thread fallback on Windows
    if not (
        hasattr(_signal, "SIGALRM")
        and hasattr(_signal, "ITIMER_REAL")
        and _threading.current_thread() is _threading.main_thread()
    ):
        if _threading.current_thread() is _threading.main_thread() and wall_budget > 0:
            import time

            _ensure_win_watchdog()
            global _WIN_ACTIVE_TEST
            tid = _threading.get_ident()
            state: dict[str, object] = {
                "nodeid": item.nodeid,
                "wall_budget": wall_budget,
                "deadline": time.monotonic() + wall_budget,
                "tid": tid,
                "dumped": False,
            }
            _WIN_ACTIVE_TEST = state
            try:
                yield
            finally:
                _WIN_ACTIVE_TEST = None
                if state.get("dumped"):
                    try:
                        import ctypes

                        ctypes.pythonapi.PyThreadState_SetAsyncExc(
                            ctypes.c_ulong(tid), None
                        )
                    except Exception:
                        pass
            return
        yield
        return

    # Stand down if test installed its own handler for EITHER SIGALRM or SIGPROF
    alrm_custom = _signal.getsignal(_signal.SIGALRM) not in (
        _signal.SIG_DFL,
        _signal.SIG_IGN,
        None,
    )
    prof_custom = hasattr(_signal, "SIGPROF") and _signal.getsignal(
        _signal.SIGPROF
    ) not in (
        _signal.SIG_DFL,
        _signal.SIG_IGN,
        None,
    )
    if alrm_custom or prof_custom:
        yield
        return

    fired = {"n": 0}

    def _on_cpu_alarm(_signum, _frame):
        fired["n"] += 1
        if fired["n"] == 1:
            sys.stderr.write(
                f"\n[conftest] TEST HANG GUARD: {item.nodeid} exceeded {cpu_budget:g}s CPU budget; "
                "stacks of every thread at expiry follow.\n"
            )
            _faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
            sys.stderr.flush()
        raise TestHangTimeout(
            f"TEST HANG GUARD: {item.nodeid} exceeded its {cpu_budget:g}s CPU budget. The frame "
            "that did not return is in the stack dump in captured stderr. Raise the budget for a "
            "legitimately slow test with @pytest.mark.timeout(<seconds>)."
        )

    def _on_wall_alarm(_signum, _frame):
        fired["n"] += 1
        if fired["n"] == 1:
            sys.stderr.write(
                f"\n[conftest] TEST HANG GUARD: {item.nodeid} exceeded {wall_budget:g}s wall ceiling; "
                "stacks of every thread at expiry follow.\n"
            )
            _faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
            sys.stderr.flush()
        raise TestHangTimeout(
            f"TEST HANG GUARD: {item.nodeid} exceeded its {wall_budget:g}s wall ceiling. The frame "
            "that did not return is in the stack dump in captured stderr. Raise the budget for a "
            "legitimately slow test with @pytest.mark.timeout(<seconds>) or @pytest.mark.timeout(wall=<seconds>)."
        )

    prev_prof = None
    prev_alrm = None
    armed_prof = False
    armed_real = False
    try:
        # Arm wall ceiling on ITIMER_REAL / SIGALRM
        if wall_budget > 0:
            prev_alrm = _signal.signal(_signal.SIGALRM, _on_wall_alarm)
            # REPEATING at 1.0s interval: guarantees re-raising lands outside any broad except Exception
            _signal.setitimer(_signal.ITIMER_REAL, wall_budget, 1.0)
            armed_real = True

        # Arm CPU budget on ITIMER_PROF / SIGPROF (user + sys CPU)
        if (
            cpu_budget > 0
            and hasattr(_signal, "SIGPROF")
            and hasattr(_signal, "ITIMER_PROF")
        ):
            prev_prof = _signal.signal(_signal.SIGPROF, _on_cpu_alarm)
            _signal.setitimer(_signal.ITIMER_PROF, cpu_budget, 1.0)
            armed_prof = True

        yield
    finally:
        if armed_prof:
            try:
                _signal.setitimer(_signal.ITIMER_PROF, 0)
            finally:
                _signal.signal(_signal.SIGPROF, prev_prof)
        if armed_real:
            try:
                _signal.setitimer(_signal.ITIMER_REAL, 0)
            finally:
                _signal.signal(_signal.SIGALRM, prev_alrm)


def _ensure_xdist_then_reexec() -> None:
    # Already available: nothing to do (the overwhelmingly common path).
    if importlib.util.find_spec("xdist") is not None:
        return

    # Guard against an infinite re-exec loop if the install silently "succeeds" but
    # the plugin still is not importable (e.g. a broken environment).
    if os.environ.get("AW_XDIST_BOOTSTRAP") == "1":
        return
    os.environ["AW_XDIST_BOOTSTRAP"] = "1"

    sys.stderr.write(
        "conftest: pytest-xdist not found; installing it so the suite runs with -n auto...\n"
    )
    sys.stderr.flush()
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest-xdist>=3"],
            check=True,
        )
    except Exception as exc:  # pragma: no cover - environment-dependent
        sys.stderr.write(
            "conftest: could not auto-install pytest-xdist "
            f"({exc}); run `pip install pytest-xdist` (or `pip install '.[test]'`).\n"
        )
        sys.stderr.flush()
        return

    if importlib.util.find_spec("xdist") is None:  # pragma: no cover
        sys.stderr.write(
            "conftest: pytest-xdist still not importable after install; aborting re-exec.\n"
        )
        sys.stderr.flush()
        return

    # Re-exec the exact same pytest command now that the plugin is present, so the
    # `-n auto` in addopts is honored on this very run.
    os.execv(sys.executable, [sys.executable, "-m", "pytest", *sys.argv[1:]])


@pytest.fixture
def template_repo(tmp_path: Path) -> Path:
    """Provide a fresh copy of the process-cached git repository template (IPD 83nnyn E-09)."""
    from tests.repo_template import copy_template_repo

    return copy_template_repo(tmp_path / "repo")


_ensure_xdist_then_reexec()
