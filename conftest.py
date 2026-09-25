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
import importlib.util
import os
import shutil as _shutil
import subprocess
import sys
import tempfile as _tempfile

import pytest

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
# `0 failed, 7993 passed` without it (re-measured at IPD `8i0xa7`: 42 tests in protected files
# fail under the re-assert probe, because role declaration was incomplete; see backlog `owi0no`).
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
# WHY NOT RELAX THE GUARD TEST. `tests/test_worker_role_refusal.py` asserts that the
# driver's own process is not worker-marked and is CORRECT as written; backlog `1uq1cu`
# names relaxing it as the wrong fix. This scrub is what makes that assertion true again
# inside a runner turn, rather than weakening it.
#
# HONEST LIMITS, both deliberate. (1) A test that needs the marking must set it ITSELF, on
# an explicit env dict passed to the code under test (or declare its role with
# `support.declare_execution_role`). Note that `test_driver_own_process_is_not_worker_role`
# is the one exception whose subject IS the ambient environment: because of this scrub,
# that test cannot fail via ordinary shell export, but it remains falsifiable via a
# `pytest_configure` re-assert plugin (see `tests/test_role_declaration_guard.py`).
# Note also that compliance across the suite is incomplete (e.g. 42 tests in
# `tests/test_ipd_lifecycle_cli.py` still inherit the ambient role, tracked in backlog
# `owi0no`). (2) This scrubs the CURRENT process only; a subprocess a test spawns
# inherits this already-cleaned environment, which is the intended propagation.
#
# CROSS-REFERENCE: `tests/test_role_declaration_guard.py` asserts behavioral outcome
# invariance under both roles across protected files by injecting a `pytest_configure`
# plugin that re-asserts the marking after this scrub and before test collection.
#
# Done at import time, before any test module is collected, so no test can observe the
# marked value. `pop` is unconditional and side-effect-free when the variable is absent,
# which is the common case for a human-typed run.
os.environ.pop("AW_EXECUTION_ROLE", None)

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
