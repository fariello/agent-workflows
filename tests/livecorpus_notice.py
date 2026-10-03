"""Pytest plugin that records live-corpus reads and reports on test failure.

SCOPE AND PURPOSE:
When a test has ALREADY FAILED, this plugin appends a section ("LIVE-CORPUS NOTE")
to the test report naming the live .aw/records/ paths it read during its call phase.
This makes live corpus traps self-explaining to agents and developers without adding
routine noise to clean runs.

THE DETECTOR'S FOUR BOUNDS:
- BOUND NOT-A-GATE: It fails nothing and deselects nothing. A corpus trap still
  reds the suite exactly as it does today; the only claim is that the red now
  NAMES its cause. Anyone reading this as a protection against the 2026-09-19
  incident recurring has misread it: the incident would recur, with a better
  error message.
- BOUND SUBPROCESS-BLIND: An in-process audit hook cannot observe a read performed
  by a spawned `python3 -m agent_workflows`, and this suite spawns the CLI often
  through `tests/support.run_cli`. A corpus trap reached only that way therefore
  gets no note at all.
- BOUND READING-IS-NOT-A-DEFECT: This is why the note is worded as information and
  never as an accusation. Many tests touch the corpus incidentally (an `aw status`
  smoke test asserting only its output envelope) or read ONE named artifact
  (`tests/test_runner_shared.py`'s check on spec `25kzda`). Neither shape can be
  reddened by a third party's new artifact. The shape that CAN is the subset
  asserting over a SET enumerated at runtime, and separating those two mechanically
  would mean judging the assertion rather than the read, which is precisely what
  no detector here attempts.
- BOUND NO-CAUSATION: A test may read the corpus and fail for a wholly unrelated
  reason. The note reports that a live read happened during a failing test; the
  reader still judges whether it mattered.

EMPIRICAL POPULATION MEASUREMENTS (measured 2026-10-01):
- AST population: A tight AST sweep over `tests/test_*.py` for calls to
  glob/rglob/iterdir referencing .aw/records without a livecorpus marker (requiring
  a repo-root anchor or literal base and excluding tempdir hints) found 4 unmarked
  functions (authoring measured 4, review measured 19 tight / 31 loose). Looser
  sweeps matching any records reference find up to 47 functions. The AST count is
  a property of the sweep heuristic rather than of the tree.
- Runtime population: A single-process probe running `pytest -o addopts="-q -m 'not slow and not livecorpus'"`
  (forced single-process because worker counts do not cross the xdist boundary to the
  coordinator) identified 52 distinct tests reading live .aw/records/ paths during their
  call phase (authoring measured 38, review measured 42). Over `-m ''`, 57 tests read
  live records, of which 5 carry `@pytest.mark.livecorpus`. The runtime population
  strictly exceeds the syntactic AST sweep under all criteria.
- Cost of always-on: Run-to-run suite execution variance (measured between 114.71s
  and 120.62s on this machine, a spread of 5.91s) exceeds any observable instrumented
  overhead. The cost of the in-process audit hook with fast-path prefix checking is
  below the measurement noise floor.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARDED_ROOT = str(os.path.realpath(REPO_ROOT / ".aw" / "records"))

# Python audit hooks (sys.addaudithook) cannot be removed once registered.
# The hook is therefore flag-gated via _ARMED[0] so it is active only while a test
# executes its call phase, and inert at all other times.
_ARMED: list[bool] = [False]
RECORDED_PATHS: set[str] = set()


def _hook(event: str, args: tuple[Any, ...]) -> None:
    if not _ARMED[0]:
        return
    if event not in ("open", "os.scandir", "os.listdir"):
        return
    try:
        raw = os.fsdecode(args[0])
    except Exception:
        # e.g. open(fd, ...) passes an int, which causes os.fsdecode to raise
        return

    guarded = str(GUARDED_ROOT)
    guarded_prefix = guarded if guarded.endswith(os.sep) else guarded + os.sep

    # Fast-path prefix check for absolute paths matching guarded root
    if raw == guarded or raw.startswith(guarded_prefix):
        RECORDED_PATHS.add(raw)
        return

    # Fallback to realpath for relative paths (e.g. CWD-relative glob or open)
    try:
        real = os.path.realpath(raw)
    except Exception:
        return

    if real == guarded or real.startswith(guarded_prefix):
        RECORDED_PATHS.add(real)


sys.addaudithook(_hook)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: Any) -> Any:
    RECORDED_PATHS.clear()
    _ARMED[0] = True
    try:
        yield
    finally:
        _ARMED[0] = False
        item._livecorpus_paths = set(RECORDED_PATHS)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any) -> Any:
    outcome = yield
    report = outcome.get_result()
    # Report on failure only, via report.sections, and say nothing on a pass.
    if report.when == "call" and not report.passed:
        paths = getattr(item, "_livecorpus_paths", None)
        if paths:
            count = len(paths)
            examples = sorted(paths)[:3]
            example_lines = "\n".join(f"  - {p}" for p in examples)
            more_msg = f"\n  ... ({count - 3} more paths)" if count > 3 else ""
            text = (
                f"This test read {count} distinct live-corpus path(s) under .aw/records/ "
                f"during its call phase:\n{example_lines}{more_msg}\n\n"
                "Note: .aw/records/ is a LIVE tree that any agent or concurrent run "
                "may write to. A failure here may be caused by another party's artifact "
                "rather than by this lane's change. If this test genuinely asserts a "
                "whole-corpus property across all artifacts in .aw/records/, mark it with "
                "@pytest.mark.livecorpus (defined in pyproject.toml's pytest.ini_options) "
                "so it does not block default lanes or CI."
            )
            report.sections.append(("LIVE-CORPUS NOTE", text))
