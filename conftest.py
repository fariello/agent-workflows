"""Root pytest conftest: guarantee the suite ALWAYS runs in parallel (-n auto), and
run the suite in the COORDINATOR role so a runner-launched turn measures the same
tree a human does (backlog `1uq1cu`).

The suite is large and IO/subprocess bound; running it serially costs multiples of
the wall time, so `-n auto` (pytest-xdist, one worker per CPU) is the default in
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
import shutil as _shutil
import signal as _signal
import subprocess
import sys
import tempfile as _tempfile
import threading as _threading

import pytest

pytest_plugins = ["tests.deselect_notice"]

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
# is pytest-only, so `make test-serial` (`python3 -m unittest`) never loads this file and is
# protected only by the per-class declarations. (2) This scrubs the CURRENT process only;
# a subprocess a test spawns inherits this already-cleaned environment, which is the
# intended propagation.
#
# Done at import time, before any test module is collected, so no test can observe the
# marked value. `pop` is unconditional and side-effect-free when the variable is absent,
# which is the common case for a human-typed run.
os.environ.pop("AW_EXECUTION_ROLE", None)

# trailread (a6xbso) E-06: an agent turn now exports AW_RUN_ID and AW_ITEM_ID6, every
# plan tells that agent to run the suite, and without this scrub a test reaching
# work_cmd._trailers_from_args would read the outer run's ids and fail only inside a
# runner turn (the same evidence-corruption class documented above). Specifically,
# tests/test_git_commit_helper.py::test_aw_commit_threads_trailers_and_lifecycle_delegates
# asserts work_cmd._trailers_from_args(argparse.Namespace()) == [], which fails if
# outer run trailers leak in. Tests that need the vars set them explicitly.
os.environ.pop("AW_RUN_ID", None)
os.environ.pop("AW_ITEM_ID6", None)

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
}
os.environ.update(_SANDBOX_ENV)


@pytest.fixture(autouse=True)
def _restore_home_sandbox():
    """Re-point AW_HOME/XDG_CONFIG_HOME at the session sandbox around every test."""
    os.environ.update(_SANDBOX_ENV)
    yield
    os.environ.update(_SANDBOX_ENV)


# --------------------------------------------------------------------------------------
# Per-test hang guard: a test that never returns FAILS with a stack dump instead of hanging.
# --------------------------------------------------------------------------------------
#
# WHY, measured 2026-09-27 (run `run-20260927T174631Z-291785`, plan `8l8dgb`). A new test's
# fake `execute_item` updated an item's status only in memory; `run_queue` reloads state from
# disk each iteration, so it re-dispatched the same item forever. Nothing bounded the test, so
# the executing agent's `pytest` call sat silent until the runner's 600s stall timeout killed the
# whole turn (48 minutes of a four-link dependency chain, which then took the other three links
# down with it). A hung test must cost seconds and name itself, not the turn.
#
# HOW. Stdlib only, deliberately, so this adds no dependency and cannot fall over the way a
# missing plugin does. On POSIX a `SIGALRM` timer (`signal.setitimer`) fires in the MAIN thread,
# first dumps every thread's stack (`faulthandler`, so the hang site is IN the failure output),
# then raises `TestHangTimeout` inside the running test, which pytest records as that test's
# ordinary failure and moves on. A `KeyboardInterrupt` is deliberately NOT used: pytest treats it
# as a request to abort the whole session. Where `SIGALRM` does not exist (Windows) the guard is a
# no-op rather than a flaky thread-based imitation. The default is set from the measured duration
# spread: the slowest fast-suite test is ~13s and the slowest `slow`-marked test ~29s, so 90s is
# ~3x headroom and still ~7x below the runner's 600s stall budget. Override per run with
# `AW_TEST_TIMEOUT=<seconds>` (`0` disables), or per test with `@pytest.mark.timeout(<seconds>)`.
# The guard also stands down when a test has already installed its own SIGALRM handler, so it
# never clobbers a test that is exercising alarms itself.
_DEFAULT_TEST_TIMEOUT = 90.0


class TestHangTimeout(BaseException):
    """Raised inside a test that exceeded its hang-guard budget.

    A `BaseException`, NOT an `Exception`, and that is the fix for a measured miss: the `8l8dgb`
    hang looped through `except Exception:` handlers that swallowed an `Exception`-based timeout
    for ~20s. Deriving from `BaseException` (as `KeyboardInterrupt` and `SystemExit` do) walks
    straight past every `except Exception`, while pytest still records it as this test's failure.
    """

    __test__ = False  # not a test class, despite the name


def _test_timeout_seconds(item) -> float:
    marker = item.get_closest_marker("timeout")
    if marker is not None and marker.args:
        return float(marker.args[0])
    raw = os.environ.get("AW_TEST_TIMEOUT", "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return _DEFAULT_TEST_TIMEOUT


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "timeout(seconds): per-test hang-guard budget (default 90s; 0 disables).",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    budget = _test_timeout_seconds(item)
    usable = (
        budget > 0
        and hasattr(_signal, "SIGALRM")
        and _threading.current_thread() is _threading.main_thread()
        and _signal.getsignal(_signal.SIGALRM)
        in (_signal.SIG_DFL, _signal.SIG_IGN, None)
    )
    if not usable:
        yield
        return

    fired = {"n": 0}

    def _on_alarm(_signum, _frame):
        fired["n"] += 1
        if fired["n"] == 1:
            sys.stderr.write(
                f"\n[conftest] TEST HANG GUARD: {item.nodeid} exceeded {budget:g}s; "
                "stacks of every thread at expiry follow.\n"
            )
            _faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
            sys.stderr.flush()
        raise TestHangTimeout(
            f"TEST HANG GUARD: {item.nodeid} exceeded its {budget:g}s per-test budget. The frame "
            "that did not return is in the stack dump in captured stderr. Raise the budget for a "
            "legitimately slow test with @pytest.mark.timeout(<seconds>)."
        )

    previous = _signal.signal(_signal.SIGALRM, _on_alarm)
    # REPEATING, not one-shot, and that is measured rather than cautious: in the very hang this
    # guard exists for (`8l8dgb`), the first raise landed inside `subprocess.run` beneath an
    # `except Exception: return []` in `runner_shared.already_landed_lanes`, which swallowed it and
    # let `run_queue` keep looping. A one-shot alarm therefore did NOT stop the test. Re-raising
    # every second after expiry guarantees one lands outside any broad handler.
    _signal.setitimer(_signal.ITIMER_REAL, budget, 1.0)
    try:
        yield
    finally:
        _signal.setitimer(_signal.ITIMER_REAL, 0)
        _signal.signal(_signal.SIGALRM, previous)


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


_ensure_xdist_then_reexec()
