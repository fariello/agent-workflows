#!/usr/bin/env python3
"""Tests for the durable, monotonic stop-request record and the cooperative stop poll.

Set `runstop` Phase 1 (`gq6m2u`), spec `c4gd2h` R7-R9/R11.

Two of these test classes exist because of MEASURED failures, not from reading the code, and they
are the reason the implementation looks more complicated than "write a JSON file":

- `MonotonicityUnderConcurrencyTests` runs MANY racing pairs, because the naive
  atomic-write-only implementation loses the higher level in roughly half of all trials. A
  single-trial test would pass ~50% of the time by luck and prove nothing.
- `SignalHandlerSafetyTests` delivers a REAL signal while the sidecar lock is held, because a
  BLOCKING lock acquire reached from a signal handler deadlocks the process outright. Every test
  here that can hang is bounded by a subprocess timeout so a regression FAILS the suite instead of
  hanging it.

Both concurrency and signal tests are marked `slow` (they spawn subprocesses), so run this file
with `-m ''` or via `make test-all`; the default `addopts` deselects `-m 'not slow'`.

HOW THIS FILE IS TABULATED, AND THE SAFETY RULE THAT CONSTRAINED IT. STOP IS A SAFETY MECHANISM: it
terminates a live, unattended run that may be an hour into an agent turn with uncommitted work in a
worktree. So the merge obeyed one rule above all others: EVERY DISTINCT STOP LEVEL AND EVERY DISTINCT
TRIGGER KEEPS ITS OWN ROW, ASSERTING ITS OWN SPECIFIC OBSERVABLE OUTCOME. No row anywhere in this file
says merely "it stopped". The four levels differ in exactly what in-flight work is allowed to finish,
which is the whole design, so each level's row pins its NAME (printed to the operator), its BUDGET (the
bound that stops a hung turn from making a stop hang forever), its DEADLINE ARITHMETIC, whether it is a
BETWEEN-TURN level, and what the poll reports. A table that collapsed the levels into one "a stop is
recorded" assertion would be worse than the tests it replaced, and is precisely what was avoided.

Three clusters were merged, each because its members differed ONLY in data:
1. THE LEVEL x PROPERTY MATRIX (`StopLevelTests`). `MonotonicityTests.test_escalation_to_four`,
   `BudgetTests`' four fixture tests, `PollTests.test_poll_observes_an_escalation` and
   `RecordRoundTripTests.test_round_trip_preserves_level_and_metadata` were each asserting one or two
   properties of one or two levels, leaving most of the matrix unasserted: level 2 in particular had
   NO name, NO poll, and NO round-trip assertion anywhere, and level 1 had no name assertion. The
   table asserts all six properties for all FOUR levels, so it is strictly more coverage, not less.
2. UNUSABLE CONTROL FILES (`UnusableRecordTests`). Six tests plus a bare `for` loop all wrote one
   broken file and asserted `read_stop_request` returns None. The DAMAGE KIND is the data; the
   assertion was identical. Each row now also asserts `poll_stop` agrees, which only one of the old
   tests checked, and that pairing is the property that matters: the poll is what a running driver
   calls, so a poll that raised where the reader returned None would crash the run.
3. MONOTONIC SEQUENCES (`MonotonicitySequenceTests`). Four tests walked a sequence of requests and
   asserted the final level; they differed only in the sequence. Rows now carry the per-request
   ACCEPTED flags and the expected HISTORY too, which pins that a refused request is a no-op rather
   than an accepted downgrade.

WHAT WAS DELIBERATELY NOT MERGED, with the reason on each surviving test:
* `assertRaises` tests (invalid levels to `request_stop`/`request_stop_nowait`, the torn-write
  injections, the lock-contention timeout). A row asserting a return value cannot assert an exception
  type, and forcing both into one table would mean a column that is meaningless for most rows.
* Anything with a LIVE THREAD, a REAL SIGNAL, or a TIMING bound: the concurrency trials, the signal
  handler probes, the contention timeout. These are the two classes the file header says exist because
  of MEASURED deadlocks and lost updates, and their value is in their trial counts and their hard
  timeouts, neither of which is data in a row.
* The `mock.patch` injections (torn writes, a failing drain, a read-only filesystem), whose setup is
  materially different from every other test here.
* The SOURCE-INSPECTION wiring assertions (`PollWiringTests`, the state-root fence), which read module
  text rather than exercising behavior.
* `VerifierStopAndIsolatedGitStatusTests`, which drives two real drivers through `execute_item` with a
  git repository on disk.

SIBLING FILES OWN THE LEVEL BEHAVIOR, AND THIS FILE DELIBERATELY DOES NOT DUPLICATE THEM. Verified by
reading them: `tests/test_runner_stop_level3.py` owns level 3's SAFE-CHECKPOINT semantics (the
checkpoint predicate, the observer control flow, the stopped disposition record, deadline arithmetic
and budget-BREACH detection, and both drivers' level-3 wiring), and `tests/test_runner_stop_triggers.py`
owns the TRIGGER surfaces (real SIGINT escalation up the 1->3->4 ladder, SIGTERM mapping to level 3,
the `stop` verb and its four level flags, out-of-band stop from a second process, liveness probing, and
budget ESCALATION end to end). THIS file owns only the durable RECORD and the cooperative POLL: writing
a level, reading it back, refusing a downgrade, surviving a torn write, and the deferral slot a signal
handler uses. So the level rows here assert the RECORD's per-level fields, never what a driver DOES at
that level, which is the sibling files' subject.
"""

from __future__ import annotations

import datetime as dt
import errno
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import platform_lock, runner_stop
from tests.support import REPO_ROOT

_CHILD_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
# Every subprocess probe is bounded so a reintroduced deadlock FAILS rather than hangs the suite.
_CHILD_TIMEOUT = 30.0


def _run_child(script: str, *args: str, timeout: float = _CHILD_TIMEOUT):
    """Run a probe script in a child interpreter under a hard timeout."""

    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "probe.py"
        path.write_text(textwrap.dedent(script), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(path), *args],
            capture_output=True,
            text=True,
            env=_CHILD_ENV,
            timeout=timeout,
        )


class _RunDirCase(unittest.TestCase):
    """A fresh tmp run dir per test, with the process-local deferral slot reset around it."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)


class StopLevelTests(unittest.TestCase):
    """EVERY LEVEL GETS ITS OWN ROW, asserting the SPECIFIC observable outcome of THAT level.

    ONE table replaces the level-specific halves of seven tests spread over four classes
    (`RecordRoundTripTests.test_round_trip_preserves_level_and_metadata`,
    `MonotonicityTests.test_escalation_to_four`, `BudgetTests`' `test_every_level_has_a_budget`,
    `test_level_four_has_a_zero_budget` and `test_deadline_is_requested_at_plus_the_levels_budget`,
    and `PollTests.test_poll_observes_an_escalation`). Every one wrote a stop request and asserted one
    or two fields of the resulting record.

    THIS TABLE IS STRICTLY MORE COVERAGE THAN WHAT IT REPLACES, WHICH IS WHY IT EXISTS. The old tests
    sampled the level x property matrix unevenly: only level 3 got a round trip, only level 3's name
    was ever asserted (`"now"`), level 4's budget was asserted alone, and LEVEL 2 HAD NO NAME
    ASSERTION, NO POLL ASSERTION AND NO ROUND TRIP ANYWHERE IN THE FILE. Six properties x four levels
    is a matrix, and a safety mechanism's levels are exactly the thing that must not be sampled.

    WHY EACH LEVEL NEEDS ITS OWN ROW RATHER THAN A SHARED "A STOP IS RECORDED" ASSERTION. The four
    levels differ ONLY in how much in-flight work is permitted to COMPLETE before shutdown begins, so
    the level IS the behavior. A table that asserted only that some stop was recorded would be
    satisfied by an implementation that wrote level 4 for every request, which would kill a run
    mid-turn when the operator asked for a graceful after-call stop, losing an hour of agent work. So
    every row pins:
      * the LEVEL NAME, which is printed to the operator and recorded in the disposition, so a
        mis-mapped name misreports what actually happened to a run;
      * the BUDGET, the bound that keeps a hung turn from making a stop hang forever;
      * the DEADLINE ARITHMETIC (`requested_at + budget`), because the budget is only meaningful if
        the deadline is actually derived from it;
      * what `poll_stop` REPORTS, since the poll is the only thing a running driver consults;
      * whether the level is a BETWEEN-TURN level, which decides at WHICH checkpoint the driver may
        act on it at all.

    WHAT THIS TABLE DELIBERATELY DOES NOT ASSERT: what a driver DOES at each level. Level 3's
    safe-checkpoint semantics are owned by `tests/test_runner_stop_level3.py` and the trigger surfaces
    by `tests/test_runner_stop_triggers.py`; this file owns the durable RECORD, so the rows assert the
    record's per-level fields and stop there.
    """

    #: (the level, the constant that must equal it, its exact `level_name`, its budget in seconds, is
    #: it a BETWEEN-TURN level, why this row exists)
    #:
    #: THE NAMES AND BUDGETS ARE LITERALS, NOT reads of `LEVEL_NAMES` / `budget_for_level`. Deriving
    #: them from the module would make this table agree with any value the module happened to hold,
    #: which is the one thing it must not do: the names are printed to an operator deciding whether a
    #: run stopped the way they asked, and the budgets are the safety bounds.
    LEVELS = (
        (
            1,
            "LEVEL_AFTER_CALL",
            "after-call",
            7200.0,
            True,
            "THE GENTLEST LEVEL: the in-flight IPD's agent turn FINISHES and the next item is simply "
            "not dequeued. Its budget is 7200s (2h), sized from one observed ~70-minute agent turn "
            "with headroom, and that number is the whole point of the level: shrink it and a normal "
            "turn breaches its deadline and gets escalated, which converts the operator's graceful "
            "request into a forced kill",
        ),
        (
            2,
            "LEVEL_AFTER_SET",
            "after-set",
            28800.0,
            True,
            "THE REST OF THIS SET finishes; the run stops before any NEXT set. Its 28800s (8h) budget "
            "is sized for the unattended overnight posture these drivers are actually run in. THIS "
            "LEVEL HAD NO NAME, NO POLL AND NO ROUND-TRIP ASSERTION ANYWHERE BEFORE THIS TABLE, which "
            "is the clearest single argument for tabulating the matrix: the level reachable only "
            "out-of-band was also the level nothing checked",
        ),
        (
            3,
            "LEVEL_NOW",
            "now",
            600.0,
            False,
            "THE CURRENT TURN STOPS AT ITS NEXT SAFE CHECKPOINT, so it is NOT a between-turn level: it "
            "acts inside a turn. Its 600s budget is deliberately EQUAL to the drivers' "
            "DEFAULT_STALL_TIMEOUT, because a checkpoint is observed from the child's event stream and "
            "the stall watchdog already declares the turn dead after that window; a checkpoint must "
            "occur inside it or the turn is already a stall case. What a driver DOES at this level is "
            "`test_runner_stop_level3.py`'s subject, not this file's",
        ),
        (
            4,
            "LEVEL_NOW_FORCE",
            "now-force",
            0.0,
            False,
            "INTERRUPT IMMEDIATELY, outcome INDETERMINATE. Its budget is 0.0 BY DEFINITION - there is "
            "no wind-down phase to bound - and a nonzero value here would mean the most urgent level "
            "waits, which is the exact opposite of what an operator asking for it wants. It is the "
            "terminal rung: nothing escalates past it",
        ),
    )

    def test_every_level_records_its_own_name_budget_deadline_and_poll(self):
        wrong = []
        for level, constant, name, budget, between_turn, why in self.LEVELS:
            problems = []
            if getattr(runner_stop, constant, None) != level:
                problems.append(
                    f"runner_stop.{constant} is {getattr(runner_stop, constant, None)!r}, not {level}"
                )
            if level not in runner_stop.LEVELS:
                problems.append(
                    f"level {level} is not in runner_stop.LEVELS ({runner_stop.LEVELS!r}), so it "
                    "cannot be requested at all"
                )
            with tempfile.TemporaryDirectory() as temp:
                run_dir = Path(temp)
                runner_stop.reset_deferred_request()
                try:
                    result = runner_stop.request_stop(run_dir, level, "tester")
                    if not result.accepted:
                        problems.append(
                            "the FIRST request at this level was not accepted, so this level cannot "
                            "be requested on a clean run at all"
                        )
                    loaded = runner_stop.read_stop_request(run_dir)
                    if loaded is None:
                        problems.append(
                            "the record did not read back at all, so a stop at this level is not "
                            "DURABLE and an out-of-band requester's instruction is simply lost"
                        )
                    else:
                        if loaded.level != level:
                            problems.append(
                                f"the record reads back level {loaded.level}, not {level}; a level "
                                "that changes on the round trip means the run is stopped more or "
                                "less abruptly than the operator asked"
                            )
                        if loaded.level_name != name:
                            problems.append(
                                f"level_name is {loaded.level_name!r}, expected {name!r}; this string "
                                "is printed to the operator and recorded in the disposition, so a "
                                "wrong one misreports what happened to the run"
                            )
                        if loaded.requester != "tester":
                            problems.append(
                                f"requester is {loaded.requester!r}, not 'tester'; the record must "
                                "attribute the request"
                            )
                        if loaded.requested_at != result.request.requested_at:
                            problems.append(
                                "the persisted requested_at differs from the one the writer returned"
                            )
                        if loaded.first_requested_at != result.request.requested_at:
                            problems.append(
                                "on a FIRST request, first_requested_at must equal requested_at"
                            )
                        if len(loaded.history) != 1:
                            problems.append(
                                f"a first request must leave exactly ONE history entry, got "
                                f"{len(loaded.history)}: {loaded.history!r}"
                            )
                        if loaded.budget_seconds != budget:
                            problems.append(
                                f"budget_seconds is {loaded.budget_seconds!r}, expected {budget!r}; "
                                "this is the bound that stops a hung turn from making the stop hang "
                                "forever"
                            )
                        expected_deadline = dt.datetime.fromisoformat(
                            loaded.requested_at
                        ) + dt.timedelta(seconds=budget)
                        actual_deadline = dt.datetime.fromisoformat(loaded.deadline)
                        if actual_deadline != expected_deadline:
                            problems.append(
                                f"deadline is {loaded.deadline!r}; requested_at + {budget}s is "
                                f"{expected_deadline.isoformat()!r}. The budget is meaningless unless "
                                "the deadline is actually derived from it"
                            )
                    reported = runner_stop.poll_stop(run_dir)
                    if reported != level:
                        problems.append(
                            f"poll_stop reports {reported!r}, not {level}; the poll is the ONLY thing "
                            "a running driver consults, so a level it cannot see is a level that "
                            "never takes effect"
                        )
                    declared_budget = runner_stop.budget_for_level(level)
                    if declared_budget != budget:
                        problems.append(
                            f"budget_for_level({level}) is {declared_budget!r}, expected {budget!r}"
                        )
                    if not isinstance(declared_budget, float):
                        problems.append(
                            f"budget_for_level({level}) returned {type(declared_budget).__name__}, "
                            "not float; the deadline arithmetic adds it to a timedelta"
                        )
                finally:
                    runner_stop.reset_deferred_request()
            is_between = level in runner_stop.BETWEEN_TURN_LEVELS
            if is_between != between_turn:
                problems.append(
                    f"BETWEEN_TURN_LEVELS membership is {is_between}, expected {between_turn}; this "
                    "decides at WHICH checkpoint a driver may act on the level, so a level in the "
                    "wrong set acts at the wrong moment (or never)"
                )
            if problems:
                wrong.append(
                    f"  level {level} ({name}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.LEVELS)} stop levels are wrong. EVERY LEVEL IS ITS OWN ROW "
            "because the levels differ ONLY in how much in-flight work may finish, so read the rows "
            "individually and do NOT treat this as one failure: a level whose NAME moved misreports a "
            "stop to the operator, a level whose BUDGET moved changes when a graceful request gets "
            "escalated into a forced kill, and a level the POLL cannot see never takes effect at all. "
            "If ALL FOUR rows failed on the same property, one shared table changed "
            "(`LEVEL_NAMES`, `WIND_DOWN_BUDGET_SECONDS`, or the deadline computation) rather than four "
            "levels each breaking. FIX: the names and budgets in this table are LITERALS on purpose; "
            "reading them from `LEVEL_NAMES`/`budget_for_level` would make the table agree with "
            "whatever the module holds, which is precisely what it must not do. Changing a budget is a "
            f"safety change, so change the literal here deliberately and say why.\n"
            + "\n".join(wrong),
        )

    def test_the_table_covers_every_level_the_module_offers(self):
        """Two-sided guard: a FIFTH level with no row must FAIL rather than ship unasserted.

        Kept separate because it is a claim about the table's coverage of a closed set, not about any
        level. A new stop level is a new safety behavior, and the one thing worse than a wrong level is
        a level whose name, budget and poll answer nothing checks.
        """
        tabulated = tuple(level for level, _c, _n, _b, _bt, _w in self.LEVELS)
        self.assertEqual(
            tabulated,
            runner_stop.LEVELS,
            "the LEVELS table and runner_stop.LEVELS have diverged. Levels with no row: "
            f"{sorted(set(runner_stop.LEVELS) - set(tabulated))!r}. FIX: add a row stating the new "
            "level's name, budget, between-turn membership, and WHAT IT LETS FINISH, because that last "
            "part is the only thing that distinguishes one stop level from another.",
        )

    def test_level_names_cover_exactly_the_levels(self):
        """Kept separate: a claim about the NAME MAP's key set, which no per-level row can state.

        Each row asserts its own name maps correctly; this asserts the map has no EXTRA entries, so a
        stale name for a removed level cannot linger and be printed for an out-of-range value.
        """
        self.assertEqual(
            sorted(runner_stop.LEVEL_NAMES),
            sorted(runner_stop.LEVELS),
            "LEVEL_NAMES must have exactly one entry per level: an extra key is a name that can "
            "never be printed, and a missing one makes `level_name` report 'unknown' for a real level.",
        )


class UnusableRecordTests(_RunDirCase):
    """An unusable control file is NO STOP REQUESTED, never a guess and never a crash.

    ONE table replaces six tests plus an inline `for` loop (`RecordRoundTripTests`'
    `test_absent_file_reads_as_none`, `test_truncated_file_reads_as_none`,
    `test_garbage_file_reads_as_none`, `test_valid_json_with_unusable_level_reads_as_none`,
    `test_directory_in_place_of_record_reads_as_none`,
    `test_poll_on_malformed_file_returns_none_and_does_not_raise`). All wrote one broken file and
    asserted the reader returns None; the DAMAGE KIND was the only thing that differed, and the
    bogus-level cases were already a loop with its reasons compressed into one comment.

    EVERY ROW ASSERTS BOTH THE READER AND THE POLL, which is stronger than what it replaces: only one
    of the old tests exercised `poll_stop` at all, and on only one damage kind. The pairing is the
    property that matters operationally, because THE POLL IS WHAT A RUNNING DRIVER CALLS, on every
    stream line and at every dequeue. A reader that returns None while the poll raises is not a
    half-fix; it is a crash in the middle of a live agent turn, triggered by a corrupt file the
    operator cannot see.

    WHY FAILING CLOSED IS THE RIGHT DIRECTION HERE, AND WHY THAT IS NOT OBVIOUS. For most safety
    mechanisms the safe default is to ACT. Here it is the reverse: an unreadable control file must mean
    NO STOP, because guessing a level would terminate a healthy unattended run on the strength of a
    corrupt byte. The record is written atomically and is monotonic, so the only honest reading of
    damage is `I cannot tell what was asked`, and the operator's remedy (re-issue the stop) is cheap
    while a spurious level 4 costs an hour of agent work.

    A VALID RECORD IS IN THIS TABLE for the usual reason: a reader that returned None for EVERYTHING
    would satisfy every damaged row on its own, and that failure mode is invisible to this table
    without the positive row. It also means the table states the whole predicate rather than half.
    """

    #: (case, a callable writing the control file's state given (run_dir, path), the expected
    #: `read_stop_request` level or None, the expected `poll_stop` result, why this row exists)
    DAMAGE = (
        (
            "no file at all",
            lambda run_dir, path: None,
            None,
            None,
            "THE BASELINE: a run with no stop requested. This is the state of every healthy run, so a "
            "reader that invented a level here would stop every run in the fleet",
        ),
        (
            "a TRUNCATED record (the first half of a real one)",
            lambda run_dir, path: path.write_text(
                path.read_text(encoding="utf-8")[
                    : len(path.read_text(encoding="utf-8")) // 2
                ],
                encoding="utf-8",
            ),
            None,
            None,
            "THE REALISTIC CORRUPTION, and the one the atomic write exists to prevent: a half-written "
            "file from a crash mid-write. It must read as ABSENT rather than as whatever level the "
            "surviving prefix happens to parse to, because a truncated escalation could otherwise be "
            "read as the LOWER level it was replacing",
        ),
        (
            "binary garbage",
            lambda run_dir, path: path.write_text(
                "\x00\x01 not json at all", encoding="utf-8"
            ),
            None,
            None,
            "not JSON at all: the reader must not raise on a decode error. Garbage in this path is "
            "usually a filesystem or editor accident, and a traceback out of the poll would take down "
            "the run it was asked about",
        ),
        (
            "a bare opening brace",
            lambda run_dir, path: path.write_text("{", encoding="utf-8"),
            None,
            None,
            "the MINIMAL JSON syntax error. Kept beside the binary row because it exercises the JSON "
            "parser's error path rather than the decoder's, and the two are separate exception types "
            "that an over-narrow `except` could miss one of",
        ),
        (
            "an empty file",
            lambda run_dir, path: path.write_text("", encoding="utf-8"),
            None,
            None,
            "zero bytes, which is what an interrupted create leaves behind. It is neither valid JSON "
            "nor a decode error, so it is a third distinct parse path",
        ),
        (
            "a JSON LIST where an object belongs",
            lambda run_dir, path: path.write_text("[1,2,3]", encoding="utf-8"),
            None,
            None,
            "STRUCTURALLY VALID JSON of the WRONG TYPE. This is the row that catches a parser which "
            "checks `json.loads` succeeded and then subscripts the result: `payload['level']` on a "
            "list raises TypeError, which is a different failure from a parse error and needs its own "
            "row",
        ),
        (
            "a DIRECTORY in place of the record",
            lambda run_dir, path: path.mkdir(),
            None,
            None,
            "an IsADirectoryError on open, which is an OSError rather than a parse failure. Unlikely "
            "but not impossible (a mis-aimed mkdir, a bad restore), and the point is that the reader's "
            "error handling covers I/O errors and not only malformed content",
        ),
        (
            "valid JSON with level 0",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": 0, "requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "BELOW the range. A structurally perfect file whose level is unusable must not be honored: "
            "there is no such thing as a level-0 stop, and treating it as falsy-so-no-stop by accident "
            "would be the right answer for the wrong reason",
        ),
        (
            "valid JSON with level 5",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": 5, "requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "ABOVE the range, and the DANGEROUS direction: if an out-of-range level were honored by "
            "comparison rather than by membership, a 5 would outrank level 4 and force the most abrupt "
            "shutdown available on the strength of a corrupt digit",
        ),
        (
            "valid JSON with level -1",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": -1, "requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "a NEGATIVE level, which a range check written as `level <= 4` would accept. Membership in "
            "the closed set is the only correct test",
        ),
        (
            "valid JSON with the level as a STRING",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": "3", "requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "`'3'` IS NOT 3, and this is the likeliest real defect in the list: a hand-edited control "
            "file or a JSON writer that stringified. It must be REFUSED rather than coerced, because "
            "coercion here would mean the reader accepts inputs the writer can never produce and the "
            "two halves of the contract stop matching",
        ),
        (
            "valid JSON with a null level",
            lambda run_dir, path: path.write_text(
                json.dumps(
                    {"level": None, "requested_at": "2026-08-30T00:00:00+00:00"}
                ),
                encoding="utf-8",
            ),
            None,
            None,
            "an explicit null, distinct from the key being absent. A reader using `.get('level')` sees "
            "the same None for both, which is fine only because both answers are the same; the row "
            "records that equivalence deliberately",
        ),
        (
            "valid JSON with the level as `true`",
            lambda run_dir, path: path.write_text(
                json.dumps(
                    {"level": True, "requested_at": "2026-08-30T00:00:00+00:00"}
                ),
                encoding="utf-8",
            ),
            None,
            None,
            "THE PYTHON TRAP: `True == 1` and `True in (1, 2, 3, 4)` are BOTH True, so a membership "
            "test alone accepts this and the file reads as a LEVEL 1 STOP. Refusing it requires an "
            "explicit bool check, which is exactly what `_validate_level` does, and this row is the "
            "only thing that keeps that check from looking redundant and being deleted",
        ),
        (
            "valid JSON with the level as a float",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": 3.0, "requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "`3.0 == 3` in Python, so a float ALSO passes a naive membership test, the same trap as "
            "`True` by a different route. The type must be int exactly",
        ),
        (
            "valid JSON with the level as a LIST",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": [3], "requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "an UNHASHABLE value, which raises TypeError inside a `in` test against a set (though not "
            "against a tuple). It is here so the validation path is proven not to depend on which "
            "container the level set happens to be",
        ),
        (
            "valid JSON with NO level key",
            lambda run_dir, path: path.write_text(
                json.dumps({"requested_at": "2026-08-30T00:00:00+00:00"}),
                encoding="utf-8",
            ),
            None,
            None,
            "the level MISSING entirely, which is a partial write of a plausible shape. A record with "
            "no level asks for nothing, so it must be silent rather than defaulting to any level",
        ),
        (
            "a valid level with NO requested_at",
            lambda run_dir, path: path.write_text(
                json.dumps({"level": 3}), encoding="utf-8"
            ),
            None,
            None,
            "the TIMESTAMP missing, and this row is the reason the whole record is validated rather "
            "than only the level: without `requested_at` there is no deadline arithmetic and no "
            "history, so honoring the level would create a stop with an unbounded wind-down - exactly "
            "the hang the budget exists to prevent",
        ),
        (
            "A VALID, COMPLETE RECORD",
            lambda run_dir, path: runner_stop.request_stop(run_dir, 3, "tester"),
            3,
            3,
            "THE POSITIVE ROW: a real request written by the real writer must be READ and POLLED "
            "normally. Every damaged row above is VACUOUS while this one is broken, because a reader "
            "that returned None for everything would satisfy all of them - and that failure would be "
            "silent, because its observable effect is that stops simply stop working",
        ),
    )

    def test_every_unusable_record_reads_as_absent_on_both_surfaces(self):
        wrong = []
        valid_row_broken = False
        for case, prepare, want_read, want_poll, why in self.DAMAGE:
            with tempfile.TemporaryDirectory() as temp:
                run_dir = Path(temp)
                path = runner_stop.stop_request_path(run_dir)
                if case.startswith("a TRUNCATED"):
                    # The truncation needs a real record to cut in half first.
                    runner_stop.request_stop(run_dir, 3, "tester")
                prepare(run_dir, path)
                problems = []
                try:
                    record = runner_stop.read_stop_request(run_dir)
                except Exception as exc:  # noqa: BLE001 - the point is that nothing escapes
                    problems.append(
                        f"read_stop_request RAISED {exc!r}; an unusable control file must read as "
                        "absent, never raise"
                    )
                    record = "RAISED"
                else:
                    got_read = None if record is None else record.level
                    if got_read != want_read:
                        if want_read is not None:
                            valid_row_broken = True
                        problems.append(
                            f"read_stop_request returned level {got_read!r}, expected {want_read!r}"
                        )
                try:
                    polled = runner_stop.poll_stop(run_dir)
                except Exception as exc:  # noqa: BLE001
                    problems.append(
                        f"poll_stop RAISED {exc!r}. THE POLL IS CALLED ON EVERY STREAM LINE AND AT "
                        "EVERY DEQUEUE, so this is a crash in the middle of a live agent turn caused "
                        "by a file the operator cannot see"
                    )
                else:
                    if polled != want_poll:
                        if want_poll is not None:
                            valid_row_broken = True
                        problems.append(
                            f"poll_stop returned {polled!r}, expected {want_poll!r}"
                        )
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        vacuity = ""
        if valid_row_broken:
            vacuity = (
                " THE VALID RECORD row is among the failures, and while it is broken every damaged row "
                "here is VACUOUS: a reader that returns None for everything satisfies all of them, and "
                "its only symptom is that stop requests silently stop working."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DAMAGE)} control-file states were handled wrongly.{vacuity} "
            "Read WHICH SURFACE failed: a mismatch on `read_stop_request` is a logic error, while a "
            "RAISE out of `poll_stop` is an outage, because the poll runs on every stream line of a "
            "live run. THE ROWS TO CHECK FIRST IF SEVERAL MOVED are the type-confusion ones (`True`, "
            "`3.0`, `'3'`): `True == 1` and `3.0 == 3` in Python, so a membership test ALONE accepts "
            "both and a corrupt file reads as a real stop level; refusing them needs the explicit "
            "`isinstance` and bool checks in `_validate_level`, which look redundant and are not. FIX: "
            "the correct direction here is FAIL CLOSED AS NO STOP, which is the opposite of most safety "
            "defaults: guessing a level would terminate a healthy unattended run over a corrupt byte, "
            "and re-issuing a stop is cheap while a spurious level 4 costs an hour of agent work.\n"
            + "\n".join(wrong),
        )


class MonotonicitySequenceTests(_RunDirCase):
    """A request may only RAISE the level (spec R9): whole SEQUENCES, with per-request verdicts.

    ONE table replaces four tests (`MonotonicityTests`'
    `test_one_then_three_then_one_stays_three_with_two_entry_history`,
    `test_no_sequence_can_lower_the_level`, `test_equal_level_is_a_no_op_leaving_the_file_untouched`,
    and `test_escalation_to_four`'s sequence half). Each walked a sequence of requests and asserted the
    final level, differing only in the sequence, so the sequence is the data.

    EACH ROW PINS MORE THAN THE FINAL LEVEL, and that is where the strength is. A row carries the
    per-request ACCEPTED flags and the expected HISTORY, which together state the property the final
    level alone cannot: that a refused request is a NO-OP rather than an accepted downgrade. The two are
    indistinguishable by final level (a downgrade followed by a re-escalation ends at the same place),
    and they are completely different safety outcomes, because a momentary downgrade is a window in
    which a driver polls the LOWER level and lets work proceed that the operator asked to stop.

    THE POLL IS CHECKED AFTER EVERY REQUEST IN THE SEQUENCE, not only at the end, which is the claim
    absorbed from `PollTests.test_poll_observes_an_escalation` and generalized: the level in force must
    be the RUNNING MAXIMUM at each step. Walking the sequence through the surface a driver actually
    consults is what catches a downgrade AT THE STEP it happens; a final-state assertion cannot, because
    a later re-escalation restores the right answer after the damage is done.

    WHY MONOTONICITY IS A SAFETY PROPERTY AND NOT A TIDINESS ONE. Escalation is how an operator whose
    graceful stop is taking too long gets a firmer one, and the drivers themselves escalate on a budget
    breach. If a later, lower request could win, then a level-1 request arriving after a level-4 one
    would RESUME a run that was being force-stopped. That is the silent downgrade R9 forbids, and it is
    why every row here includes at least one request that must be REFUSED.

    THE BYTES-UNTOUCHED CLAIM is a separate column on the equal-level row rather than its own test: an
    equal request must not even rewrite the file, because a rewrite would move `requested_at` and
    thereby EXTEND the wind-down deadline, quietly granting a hung turn more time every time anyone
    re-issued the same stop.
    """

    #: (case, the sequence of levels requested in order, the expected `accepted` flag per request, the
    #: expected final level, the expected history levels, why this row exists)
    SEQUENCES = (
        (
            "1 then 3 then 1",
            (1, 3, 1),
            (True, True, False),
            3,
            [1, 3],
            "THE CANONICAL CASE: an escalation followed by a lower request. The third request must be "
            "REFUSED and must leave NO history entry, so the history reads as the two decisions that "
            "actually took effect. A downgrade here would drop the run back to 'finish the turn' after "
            "the operator had already asked it to stop at the next checkpoint",
        ),
        (
            "3 then 4",
            (3, 4),
            (True, True),
            4,
            [3, 4],
            "PLAIN ESCALATION to the terminal rung, which must be ACCEPTED: this is the path an "
            "operator takes when a level-3 stop is not happening fast enough, and it is also what the "
            "budget-breach watch does automatically. If escalation were refused, a hung turn could "
            "never be forced down",
        ),
        (
            "1 then 2 then 3 then 4: the whole ladder",
            (1, 2, 3, 4),
            (True, True, True, True),
            4,
            [1, 2, 3, 4],
            "EVERY RUNG ACCEPTED IN ORDER, and the history records all four. This is the row that "
            "proves escalation is not special-cased to one jump: the ladder is walked one rung at a "
            "time by the trigger surfaces (a third SIGINT reaches level 4 through it), so each step "
            "must be individually accepted",
        ),
        (
            "4 then every level again",
            (4, 1, 2, 3, 4),
            (True, False, False, False, False),
            4,
            [4],
            "ONCE AT THE TERMINAL RUNG, NOTHING IS ACCEPTED - not a lower level, and not an equal one. "
            "Four separate refusals in one row, which is what makes this the strongest statement of R9: "
            "there is no sequence of later requests that can lower or re-log a level-4 stop, so a "
            "force-stop in progress cannot be resumed or restarted by anyone",
        ),
        (
            "3 then 3",
            (3, 3),
            (True, False),
            3,
            [3],
            "AN EQUAL REQUEST IS A NO-OP, not a re-record. It leaves no second history entry AND (see "
            "the bytes column below) does not rewrite the file at all, because a rewrite would move "
            "`requested_at` and EXTEND the deadline - quietly granting a hung turn more wind-down time "
            "every time the same stop was re-issued",
        ),
        (
            "2 then 1",
            (2, 1),
            (True, False),
            2,
            [2],
            "A DOWNGRADE BETWEEN THE TWO BETWEEN-TURN LEVELS specifically. Levels 1 and 2 are both "
            "acted on at the same dequeue checkpoint, so the difference between them is only WHICH "
            "queue boundary ends the run; this row proves monotonicity holds even where the two levels "
            "share a checkpoint and the distinction is easiest to lose",
        ),
    )

    def test_no_sequence_of_requests_can_lower_the_level(self):
        wrong = []
        for (
            case,
            levels,
            want_accepted,
            want_final,
            want_history,
            why,
        ) in self.SEQUENCES:
            with tempfile.TemporaryDirectory() as temp:
                run_dir = Path(temp)
                runner_stop.reset_deferred_request()
                path = runner_stop.stop_request_path(run_dir)
                problems = []
                got_accepted = []
                bytes_before_last = None
                in_force = None
                for index, level in enumerate(levels):
                    if index == len(levels) - 1 and path.exists():
                        bytes_before_last = path.read_bytes()
                    got_accepted.append(
                        runner_stop.request_stop(run_dir, level, f"r{index}").accepted
                    )
                    # AFTER EVERY REQUEST the poll must report the level actually IN FORCE, which is
                    # the running maximum. This walks the sequence through the only surface a driver
                    # consults, so a momentary downgrade is caught AT THE STEP it happens rather than
                    # being hidden by a later re-escalation restoring the final level.
                    in_force = level if in_force is None else max(in_force, level)
                    polled = runner_stop.poll_stop(run_dir)
                    if polled != in_force:
                        problems.append(
                            f"after request #{index + 1} (level {level}), poll_stop reported "
                            f"{polled!r} but the level in force is {in_force}. The poll is the only "
                            "surface a running driver consults, so a wrong answer HERE means the "
                            "driver acts on the wrong level at that moment even if the final record "
                            "is right"
                        )
                if tuple(got_accepted) != want_accepted:
                    refusals_expected = [
                        levels[i] for i, flag in enumerate(want_accepted) if not flag
                    ]
                    problems.append(
                        f"per-request accepted flags were {tuple(got_accepted)!r}, expected "
                        f"{want_accepted!r}. The requests that MUST be refused are at levels "
                        f"{refusals_expected!r}; an accepted one there is a SILENT DOWNGRADE, which is "
                        "a window in which a driver polls the lower level and lets work proceed that "
                        "the operator asked to stop"
                    )
                record = runner_stop.read_stop_request(run_dir)
                if record is None:
                    problems.append("no record at all after the sequence")
                else:
                    if record.level != want_final:
                        problems.append(
                            f"final level is {record.level}, expected {want_final}"
                        )
                    history = [entry["level"] for entry in record.history]
                    if history != want_history:
                        problems.append(
                            f"history is {history!r}, expected {want_history!r}; a refused request "
                            "must leave NO entry, so the history is the list of decisions that "
                            "actually took effect"
                        )
                # An unaccepted FINAL request must not have rewritten the file at all.
                if (
                    bytes_before_last is not None
                    and not want_accepted[-1]
                    and path.read_bytes() != bytes_before_last
                ):
                    problems.append(
                        "the refused final request REWROTE the record. Even an identical rewrite moves "
                        "`requested_at` and therefore EXTENDS the wind-down deadline, so re-issuing "
                        "the same stop would keep granting a hung turn more time"
                    )
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
                runner_stop.reset_deferred_request()
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SEQUENCES)} request sequences violated monotonicity (spec R9). "
            "Read the ACCEPTED FLAGS before the final level: those two failures look the same at the "
            "end of a sequence and are completely different outcomes, because a momentary downgrade "
            "followed by a re-escalation ends at the right level having briefly told the driver to keep "
            "working. If the `4 then every level again` row failed, a force-stop in progress can now be "
            "lowered or restarted, which is the worst case in this file. If only the `3 then 3` row "
            "failed on its BYTES, an equal request began rewriting the record, which extends the "
            "wind-down deadline every time the same stop is re-issued. FIX: escalation is how an "
            "operator (and the budget-breach watch) firms up a stop that is not happening fast enough, "
            f"so the accept direction must stay open while the lower direction stays closed.\n"
            + "\n".join(wrong),
        )

    def test_first_requested_at_is_preserved_across_escalation(self):
        """Kept separate: asserts a field is UNCHANGED while another CHANGES, across one escalation.

        A sequence row pins the final level and the history; this pins that `first_requested_at` keeps
        the ORIGINAL moment while `requested_at` moves to the escalation's. Both halves matter and
        neither is a level: the first is when the operator first asked (the audit answer), the second is
        what the current deadline is computed from.
        """
        first = runner_stop.request_stop(self.run_dir, 1, "a").request
        runner_stop.request_stop(self.run_dir, 4, "b")
        record = runner_stop.read_stop_request(self.run_dir)
        self.assertEqual(
            record.first_requested_at,
            first.requested_at,
            "first_requested_at must keep the moment the operator FIRST asked; it is the audit answer "
            "to 'how long did this stop take'.",
        )
        self.assertNotEqual(
            record.requested_at,
            first.requested_at,
            "requested_at must move to the escalation, because the new level's deadline is computed "
            "from it; leaving it behind would compute the new budget from an old start.",
        )

    def test_escalation_rebases_the_budget_on_the_new_level(self):
        """Kept separate: asserts the DEADLINE ARITHMETIC is recomputed, not a level or a verdict.

        `StopLevelTests` pins each level's budget and deadline on a FIRST request; this pins that an
        escalation re-derives both from the NEW level rather than keeping the old level's budget. It is
        the one place the budget and the monotonicity rules interact, and getting it wrong would give a
        level-3 stop level 1's two-hour wind-down.
        """
        runner_stop.request_stop(self.run_dir, 1, "a")
        record = runner_stop.request_stop(self.run_dir, 3, "b").request
        self.assertEqual(
            record.budget_seconds,
            runner_stop.budget_for_level(3),
            "an escalation must adopt the NEW level's budget, not keep the old one.",
        )
        expected = dt.datetime.fromisoformat(record.requested_at) + dt.timedelta(
            seconds=runner_stop.budget_for_level(3)
        )
        self.assertEqual(
            dt.datetime.fromisoformat(record.deadline),
            expected,
            "the escalated deadline must be the NEW requested_at plus the NEW budget.",
        )

    def test_invalid_level_is_rejected_loudly(self):
        """Kept separate: an `assertRaises` test. The WRITER must refuse what the reader ignores.

        This is the writer-side mirror of `UnusableRecordTests`, and the asymmetry is the point: a
        malformed file on DISK reads as 'no stop' (silent, because guessing would kill a healthy run),
        while a malformed level handed to the API RAISES (loud, because the caller is present and can be
        told). A row cannot carry both a return value and an exception type without a column that is
        meaningless for most rows.

        `True` and `3.0` are included because `True == 1` and `3.0 == 3` in Python, so a membership test
        alone accepts both; only an explicit type check refuses them.
        """
        for bogus in (0, 5, -1, "3", None, True, 3.0):
            with self.subTest(level=bogus), self.assertRaises(ValueError):
                runner_stop.request_stop(self.run_dir, bogus, "x")

    def test_serialization_uses_a_sidecar_lock_not_the_record_file(self):
        """Kept separate: a claim about WHICH FILE is locked, not about any request's outcome.

        The lock MUST be a separate file: the record is swapped by `os.replace`, so a lock held on the
        replaced inode would protect nothing and the concurrency the sidecar exists for would be lost
        while every sequential test still passed.
        """
        runner_stop.request_stop(self.run_dir, 1, "a")
        record = runner_stop.stop_request_path(self.run_dir)
        lock = runner_stop.stop_request_lock_path(self.run_dir)
        self.assertNotEqual(record, lock)
        self.assertTrue(lock.is_file(), "sidecar lock file should exist after a write")
        self.assertEqual(lock.name, "stop-request.lock")

    def test_record_survives_os_replace_swapping_the_inode(self):
        """Kept separate: asserts an INODE CHANGE, which is a property of the write mechanism.

        Proves the escalation went through an atomic replace rather than an in-place rewrite, which is
        what makes a torn read impossible. No level or verdict is involved, so it is not a row.
        """
        runner_stop.request_stop(self.run_dir, 1, "a")
        path = runner_stop.stop_request_path(self.run_dir)
        first_inode = path.stat().st_ino
        runner_stop.request_stop(self.run_dir, 4, "b")
        self.assertNotEqual(
            path.stat().st_ino, first_inode, "escalation should replace the record file"
        )
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)


@pytest.mark.slow
class MonotonicityUnderConcurrencyTests(unittest.TestCase):
    """E-02, the half that actually matters: monotonicity under REAL concurrent writers.

    NOT MERGED INTO ANY TABLE, and this is the clearest case in the file. The value of these two tests
    is their TRIAL COUNT against real racing processes, not their data: a row asserting one outcome of
    one race would pass about half the time against the broken implementation and prove nothing.

    MEASURED (re-verified independently while executing this plan, 200 trials each):
      - atomic write only, read-modify-write UNSERIALIZED: the higher level was LOST in 87/200
        trials (~44%).
      - read-compare-write serialized under the sidecar lock: LOST in 0/200.
    """

    TRIALS = 120  # >= 100 required by V-02; each trial is two racing processes

    def test_racing_writers_never_lose_the_higher_level(self):
        script = """
        import json, sys, os
        from pathlib import Path
        from agent_workflows import runner_stop

        run_dir = Path(sys.argv[1])
        level = int(sys.argv[2])
        gate = Path(sys.argv[3])
        # Spin on a file gate so both children reach the write as simultaneously as possible.
        # This is a RACE PROBE (widening a window), not a checkpoint definition: no test here
        # uses a sleep to decide when something is safe.
        while not gate.exists():
            pass
        runner_stop.request_stop(run_dir, level, f"racer-{level}", timeout=30.0)
        """
        lost = 0
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            probe = root / "probe.py"
            probe.write_text(textwrap.dedent(script), encoding="utf-8")
            for trial in range(self.TRIALS):
                run_dir = root / f"trial-{trial}"
                run_dir.mkdir()
                gate = run_dir / "gate"
                procs = [
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(probe),
                            str(run_dir),
                            str(level),
                            str(gate),
                        ],
                        env=_CHILD_ENV,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    # High level FIRST, low level second: the ordering that loses the update.
                    for level in (4, 1)
                ]
                gate.touch()
                for proc in procs:
                    _out, err = proc.communicate(timeout=_CHILD_TIMEOUT)
                    self.assertEqual(proc.returncode, 0, f"racer failed: {err}")
                record = runner_stop.read_stop_request(run_dir)
                self.assertIsNotNone(record, f"trial {trial} left no record")
                if record.level != 4:
                    lost += 1
        self.assertEqual(
            lost,
            0,
            f"the higher level was lost in {lost}/{self.TRIALS} trials (a lost update is "
            "exactly the silent downgrade spec R9 forbids)",
        )

    def test_many_concurrent_escalators_converge_on_the_maximum(self):
        script = """
        import sys
        from pathlib import Path
        from agent_workflows import runner_stop

        run_dir = Path(sys.argv[1])
        level = int(sys.argv[2])
        gate = Path(sys.argv[3])
        while not gate.exists():
            pass
        runner_stop.request_stop(run_dir, level, f"racer-{level}", timeout=30.0)
        """
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            probe = root / "probe.py"
            probe.write_text(textwrap.dedent(script), encoding="utf-8")
            run_dir = root / "run"
            run_dir.mkdir()
            gate = run_dir / "gate"
            procs = [
                subprocess.Popen(
                    [sys.executable, str(probe), str(run_dir), str(level), str(gate)],
                    env=_CHILD_ENV,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for level in (1, 2, 3, 4, 3, 2, 1, 2)
            ]
            gate.touch()
            for proc in procs:
                _out, err = proc.communicate(timeout=_CHILD_TIMEOUT)
                self.assertEqual(proc.returncode, 0, f"racer failed: {err}")
            self.assertEqual(runner_stop.read_stop_request(run_dir).level, 4)


class TornWriteTests(_RunDirCase):
    """E-02: an interrupted write must never be readable as a valid LOWER level.

    NOT MERGED: all three are `assertRaises` tests wrapped in a `mock.patch` that makes `os.replace`
    fail, and each asserts a DIFFERENT KIND of aftermath (the previous record intact, no temp file
    leaked, no readable request at all). Those are three structurally different claims about the
    filesystem after an injected failure, not three data points.
    """

    def test_failure_mid_write_leaves_the_previous_valid_record(self):
        runner_stop.request_stop(self.run_dir, 3, "first")
        before = runner_stop.stop_request_path(self.run_dir).read_bytes()

        boom = OSError("injected failure between write and rename")
        with mock.patch.object(runner_stop.os, "replace", side_effect=boom):
            with self.assertRaises(OSError):
                runner_stop.request_stop(self.run_dir, 4, "interrupted")

        self.assertEqual(
            runner_stop.stop_request_path(self.run_dir).read_bytes(), before
        )
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 3)

    def test_failed_write_leaves_no_temp_file_behind(self):
        runner_stop.request_stop(self.run_dir, 1, "first")
        with mock.patch.object(runner_stop.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                runner_stop.request_stop(self.run_dir, 4, "interrupted")
        leftovers = [
            p.name
            for p in self.run_dir.iterdir()
            if p.name.startswith(".") and p.name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [], f"temp files leaked: {leftovers}")

    def test_first_write_failing_leaves_no_readable_request(self):
        with mock.patch.object(runner_stop.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                runner_stop.request_stop(self.run_dir, 4, "interrupted")
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))


class PathResolutionTests(unittest.TestCase):
    """E-03: the flag rides the driver's OWN run-dir accessor, with no second root.

    ONE table replaces two tests (`test_path_is_stop_request_json_inside_the_run_dir` and
    `test_both_drivers_state_root_accessors_compose`), which resolved a path through one accessor each
    and compared it to an expectation. The ACCESSOR is the data, so it is the row.

    The monkeypatched-root test and the source fence stay separate, each with a docstring saying why.

    Why the table is worth it: `resolve_stop_request_path` must compose with any accessor and must add
    exactly `<run_id>/stop-request.json`, and the two drivers' accessors must agree. Asserting the
    filename LITERALLY on every row is the load-bearing part, because it is the name an operator looks
    for and the name an out-of-band `stop` from another process writes; the two sides must agree on it
    or an out-of-band stop writes a file the run never reads.
    """

    #: (case, a state-root accessor or None to use `stop_request_path` directly, the repo, the run id,
    #: the expected path or a callable computing it, why this row exists)
    RESOLUTIONS = (
        (
            "the direct run-dir form",
            None,
            None,
            None,
            Path("/x/runs/run-1/stop-request.json"),
            "THE FILENAME IS PINNED LITERALLY: `stop-request.json` directly inside the run dir. This "
            "name is what an operator greps for and what an out-of-band `stop` in ANOTHER PROCESS "
            "writes, so the two sides must agree on it exactly or a stop is recorded where the run "
            "never looks",
        ),
        (
            "composed with the oc driver's state root",
            "oc",
            Path("/repo"),
            "run-7",
            None,
            "the OC driver's accessor must compose: `<state_root>/<run_id>/stop-request.json`. "
            "Asserted against the driver's OWN accessor rather than a hardcoded path, because the root "
            "moved out of the repo once already (`wtiso` Phase 4) and the flag must move with it",
        ),
        (
            "composed with the agy driver's state root",
            "agy",
            Path("/repo"),
            "run-7",
            None,
            "the AGY driver's accessor, which must give the SAME shape. Both drivers need a row "
            "because a stop is often issued for a run started by the other driver, and a divergence "
            "here means one driver's stop lands somewhere the other never polls",
        ),
    )

    def test_each_accessor_resolves_to_the_same_stop_request_filename(self):
        from agent_workflows import agy_runipd, oc_runipd

        accessors = {"oc": oc_runipd.state_root, "agy": agy_runipd.state_root}
        wrong = []
        for case, which, repo, run_id, expected, why in self.RESOLUTIONS:
            if which is None:
                resolved = runner_stop.stop_request_path(Path("/x/runs/run-1"))
                want = expected
            else:
                accessor = accessors[which]
                resolved = runner_stop.resolve_stop_request_path(
                    repo, run_id, state_root=accessor
                )
                want = accessor(repo) / run_id / "stop-request.json"
            if resolved != want:
                wrong.append(
                    f"  {case}:\n"
                    f"    - resolved to {str(resolved)!r}, expected {str(want)!r}\n"
                    f"    this row exists because: {why}"
                )
            elif resolved.name != "stop-request.json":
                wrong.append(
                    f"  {case}:\n"
                    f"    - the filename is {resolved.name!r}, not 'stop-request.json'\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.RESOLUTIONS)} path resolutions are wrong. All three must end "
            "in the SAME literal filename `stop-request.json`: a run polls that name and an "
            "out-of-band `stop` from another process writes it, so a divergence means a recorded stop "
            "is never observed. If BOTH driver rows failed while the direct row passed, "
            "`resolve_stop_request_path`'s composition changed rather than either accessor; if only "
            "ONE driver row failed, the two drivers' roots have forked and a stop issued for a run "
            f"started by the other driver lands where nothing reads it.\n"
            + "\n".join(wrong),
        )

    def test_resolution_follows_a_monkeypatched_state_root(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP - a synthetic accessor and a NEGATIVE assertion.

        Proves there is no hardcoded root by supplying an accessor pointing somewhere arbitrary and then
        asserting the result is NOT under the repo. The table's rows compose with REAL accessors and
        compare positively; this row's value is precisely that its root is unrelated to any real one, and
        its second claim is an absence, which no positive path comparison expresses.
        """
        with tempfile.TemporaryDirectory() as temp:
            relocated = Path(temp) / "elsewhere" / "runs"

            def fake_state_root(_repo: Path) -> Path:
                return relocated

            resolved = runner_stop.resolve_stop_request_path(
                Path("/some/repo"), "run-42", state_root=fake_state_root
            )
            self.assertEqual(resolved, relocated / "run-42" / "stop-request.json")
            self.assertFalse(
                str(resolved).startswith("/some/repo"),
                "the flag must not be pinned under the repo",
            )

    def test_module_constructs_no_state_root_of_its_own(self):
        """Kept separate: SOURCE INSPECTION of the module's own text, not a resolved path.

        Orchestrator CID-2 / `wtiso` Phase 3 guard. The subject is the module source, so it shares no
        input with any resolution row: the table proves the accessor is FOLLOWED, this proves no second
        root is CONSTRUCTED, and a module could do both.
        """
        source = (REPO_ROOT / "agent_workflows" / "runner_stop.py").read_text(
            encoding="utf-8"
        )
        code_lines = [
            line for line in source.splitlines() if not line.strip().startswith("#")
        ]
        for needle in ('".aw"', "'.aw'", '".aw/state"', "'.aw/state'"):
            self.assertNotIn(
                needle,
                "\n".join(code_lines),
                f"runner_stop must not construct a state root itself (found {needle})",
            )


class PollTests(_RunDirCase):
    """E-04: the poll REPORTS the level and never consumes the request (spec R8).

    `StopLevelTests` asserts what the poll reports for EACH level; these two assert properties of
    POLLING ITSELF that no per-level row can state, and they stay separate for that reason.
    """

    def test_poll_is_none_when_no_request_exists(self):
        """Kept separate: the absent case is the baseline of every healthy run, asserted in
        `UnusableRecordTests` as data and here as the poll's own contract on a clean run dir."""
        self.assertIsNone(runner_stop.poll_stop(self.run_dir))

    def test_repeated_polls_are_idempotent_and_leave_the_record_unchanged(self):
        """Kept separate: asserts 25 REPEATED calls change nothing, which is a claim about repetition.

        The poll runs on every stream line of a live run, so a poll that CONSUMED the request would
        make the stop take effect once and then vanish, and a poll that rewrote the record would move
        `requested_at` and extend the wind-down deadline on every line of output. Both are properties
        of calling it many times, which a single-call row cannot express.
        """
        runner_stop.request_stop(self.run_dir, 3, "tester")
        path = runner_stop.stop_request_path(self.run_dir)
        before_bytes = path.read_bytes()
        before_stat = path.stat()
        levels = [runner_stop.poll_stop(self.run_dir) for _ in range(25)]
        self.assertEqual(levels, [3] * 25, "the poll must not consume the request")
        self.assertEqual(path.read_bytes(), before_bytes)
        self.assertEqual(path.stat().st_mtime_ns, before_stat.st_mtime_ns)

    def test_a_long_past_deadline_still_reads_back_normally(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP - a hand-written record with a past deadline.

        R11 is ACCOUNTED here and ENFORCED by the phases owning each level, so this module must not
        start second-guessing an expired record. If the poll suppressed a breached request, a stop whose
        wind-down ran long would silently STOP BEING A STOP, which is the opposite of the escalation the
        budget exists to trigger.
        """
        past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat()
        runner_stop.stop_request_path(self.run_dir).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "level": 3,
                    "requested_at": past,
                    "requester": "old",
                    "first_requested_at": past,
                    "budget_seconds": 1.0,
                    "deadline": past,
                    "history": [],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 3)

    def test_reading_the_deadline_twice_is_stable(self):
        """Kept separate: asserts two reads AGREE, which is a claim about reading, not about a level.

        A deadline recomputed at READ time rather than stored at WRITE time would drift on every poll,
        so the run would never reach it and the budget would never bound anything. The claim is the
        equality of two reads, which needs two calls.
        """
        runner_stop.request_stop(self.run_dir, 3, "tester")
        first = runner_stop.read_stop_request(self.run_dir)
        second = runner_stop.read_stop_request(self.run_dir)
        self.assertEqual(first.deadline, second.deadline)
        self.assertEqual(first.budget_seconds, second.budget_seconds)


@pytest.mark.slow
class CrossProcessPollTests(unittest.TestCase):
    """E-04: the poll must see a level written by ANOTHER PROCESS (the out-of-band `stop` case).

    NOT MERGED: both tests spawn real child interpreters under hard timeouts, and the second one runs a
    50-iteration polling loop with a nested process writing mid-loop. The value is the REAL process
    boundary (this process never holds the object that was written), which is setup, not data.
    """

    def test_poll_observes_a_level_written_by_a_separate_process(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self.assertIsNone(runner_stop.poll_stop(run_dir))
            result = _run_child(
                """
                import sys
                from pathlib import Path
                from agent_workflows import runner_stop
                runner_stop.request_stop(Path(sys.argv[1]), 3, "other-process")
                """,
                str(run_dir),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # A genuinely separate process wrote it; this process never held the object.
            self.assertEqual(runner_stop.poll_stop(run_dir), 3)
            record = runner_stop.read_stop_request(run_dir)
            self.assertEqual(record.requester, "other-process")

    def test_driver_loop_observes_a_mid_run_request(self):
        """The realistic shape: a loop polling per line picks up an out-of-band request."""

        result = _run_child(
            """
            import subprocess, sys
            from pathlib import Path
            from agent_workflows import runner_stop

            run_dir = Path(sys.argv[1])
            seen = []
            for i in range(50):
                if i == 10:
                    subprocess.run(
                        [sys.executable, "-c",
                         "import sys;from pathlib import Path;"
                         "from agent_workflows import runner_stop;"
                         "runner_stop.request_stop(Path(sys.argv[1]), 4, 'oob')",
                         str(run_dir)],
                        check=True,
                    )
                seen.append(runner_stop.poll_stop(run_dir))
            print("before:", seen[0], "after:", seen[-1])
            assert seen[0] is None, seen[:3]
            assert seen[-1] == 4, seen[-3:]
            """,
            str(Path(tempfile.mkdtemp())),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("before: None after: 4", result.stdout)


class PollWiringTests(unittest.TestCase):
    """E-04: the poll is wired at BOTH checkpoints in BOTH drivers (four sites).

    NOT MERGED: every test here reads DRIVER SOURCE TEXT and asserts a structural fact about it (a
    call count, the ORDER of two statements, a window between two anchors). They share no fixture, no
    run dir and no level with anything else in this file, and their assertions are positional rather
    than value comparisons.
    """

    def _source(self, module_name: str) -> str:
        return (REPO_ROOT / "agent_workflows" / module_name).read_text(encoding="utf-8")

    def test_each_driver_polls_at_exactly_two_sites(self):
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            count = source.count("runner_stop.poll_stop(run_dir)")
            self.assertEqual(
                count, 2, f"{module_name} should poll at 2 checkpoints, found {count}"
            )

    def test_in_turn_poll_sits_with_the_watchdog_touch(self):
        # The per-line in-turn checkpoint: beside the existing watchdog heartbeat, which is the
        # established precedent that the driver may act on stream observation alone.
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            # Anchor on the LAST watchdog.touch(), not the first. stallfp (kaga7s) added an
            # EARLIER touch site (the `_subagent_progress` callback, oc_runipd only) after this
            # test was written, so `.index()` began measuring from a site that is not the
            # per-line stream checkpoint at all. `.rindex()` finds the in-turn touch in both
            # drivers regardless of how many earlier callback sites exist.
            idx = source.rindex("watchdog.touch()")
            # 1200, not 700: the window must survive COMMENT growth between the touch and the
            # poll. After merging lanetruth-01 (af7i6p, the parent-session-id learning block) and
            # this plan's own explanatory comment, the gap in oc_runipd is 825 chars of which
            # almost all is comment; the two statements are still only a few lines apart. The
            # window exists to prove the poll sits at the per-line stream checkpoint, not to
            # police comment length.
            window = source[idx : idx + 1200]
            self.assertIn(
                "runner_stop.poll_stop(run_dir)",
                window,
                f"{module_name}: in-turn poll should follow watchdog.touch()",
            )

    def test_between_item_poll_is_in_the_dequeue_loop(self):
        # The between-item checkpoint: inside run_queue's dequeue loop, BEFORE the next item is
        # selected, which is where levels 1-2 will branch.
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            body = source[source.index("def run_queue(") :]
            loop = body.index("while True:")
            select = body.index('item["status"] == "queued"')
            poll = body.index("runner_stop.poll_stop(run_dir)")
            self.assertLess(loop, poll, f"{module_name}: poll must be inside the loop")
            self.assertLess(
                poll, select, f"{module_name}: poll must precede item selection"
            )

    def test_both_drivers_share_the_one_stop_mechanism(self):
        from agent_workflows import agy_runipd, oc_runipd

        self.assertIs(oc_runipd.runner_stop, runner_stop)
        self.assertIs(agy_runipd.runner_stop, runner_stop)

    def test_the_handler_safe_writer_is_the_only_writer_a_signal_handler_uses(self):
        # Scope fence, NARROWED TWICE now, each time by the phase it was reserving room for.
        #
        # Phase 1 (`gq6m2u`) authored it as "no level behavior exists yet", forbidding both any
        # consumption of the poll's return value and any signal handler. Phase 2 (`1qxuke`) removed the
        # first half, because levels 1-2 must consume that return value at the between-item checkpoint.
        # Phase 5 (`71vjbn`) now removes the second half, because the trigger UX is precisely the
        # SIGINT/SIGTERM registration this line was holding open.
        #
        # It is NOT simply deleted, and equally NOT left as written: Phase 5 registers from the SHARED
        # `runner_stop` module, so `assertNotIn("signal.signal(", driver_source)` would now pass
        # VACUOUSLY - green while asserting nothing. The invariant that was always the real point is
        # kept and asserted directly on the installer: a handler may only use the handler-SAFE writer
        # (`request_stop_nowait`), because Phase 1 MEASURED that a blocking sidecar-lock acquire reached
        # from a handler hangs the process outright (entered, hung, killed at a 10s timeout, exit 124).
        import inspect

        installer = inspect.getsource(runner_stop.install_stop_signal_handlers)
        self.assertIn("request_stop_nowait(", installer)
        self.assertNotIn(
            "request_stop(",
            installer.replace("request_stop_nowait(", ""),
            "a signal handler must never take the blocking-retry writer (measured deadlock)",
        )
        # The drivers must go through that installer rather than registering handlers of their own,
        # which is how two phases' handlers would silently race for the same signal.
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            self.assertIn(
                "runner_stop.install_stop_signal_handlers(", source, module_name
            )
            self.assertNotIn("signal.signal(", source, module_name)


@pytest.mark.slow
class SignalHandlerSafetyTests(unittest.TestCase):
    """E-06: the writer a signal handler calls must never block, and must never lose the request.

    NOT MERGED, and this is the other clearest case: these probes deliver a REAL SIGNAL to a real child
    process while the sidecar lock is held on its main thread, bounded by a hard subprocess timeout. The
    deadlock they forbid is a HANG, so the test's mechanism (a timeout) IS the assertion, and a table
    row cannot carry one.

    MEASURED (re-verified while executing this plan): a BLOCKING `flock` reached from a SIGINT
    handler while the main thread holds the sidecar lock hangs the process outright (the handler
    printed "handler entered" and never returned; killed at a 10s timeout, exit 124). The
    non-blocking + defer-to-poll path exits 0 with the level preserved.
    """

    _HANDLER_PROBE = """
        import fcntl, os, signal, sys
        from pathlib import Path
        from agent_workflows import runner_stop

        run_dir = Path(sys.argv[1])
        mode = sys.argv[2]

        def blocking_request(level):
            # The naive implementation this test exists to forbid: a BLOCKING acquire.
            lock_path = runner_stop.stop_request_lock_path(run_dir)
            with lock_path.open("a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        def handler(signum, frame):
            print("handler entered", flush=True)
            if mode == "blocking":
                blocking_request(4)
            else:
                result = runner_stop.request_stop_nowait(run_dir, 4, "sighandler")
                print("deferred=%s" % result.deferred, flush=True)
            print("handler exited", flush=True)

        signal.signal(signal.SIGINT, handler)

        lock_path = runner_stop.stop_request_lock_path(run_dir)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as held:
            # Hold the sidecar lock on the MAIN thread, then deliver a REAL signal to ourselves,
            # which is precisely the re-entrancy the deadlock needs.
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            print("main holds lock", flush=True)
            os.kill(os.getpid(), signal.SIGINT)
            print("main resumed", flush=True)
            fcntl.flock(held.fileno(), fcntl.LOCK_UN)

        print("poll=%s" % runner_stop.poll_stop(run_dir), flush=True)
        """

    def test_real_signal_while_lock_held_neither_hangs_nor_loses_the_request(self):
        run_dir = Path(tempfile.mkdtemp())
        try:
            result = _run_child(
                self._HANDLER_PROBE, str(run_dir), "nowait", timeout=15.0
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "request_stop_nowait DEADLOCKED in a signal handler: it must make a "
                "non-blocking attempt and defer to the poll"
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handler entered", result.stdout)
        self.assertIn("handler exited", result.stdout)
        self.assertIn("deferred=True", result.stdout)
        self.assertIn("main resumed", result.stdout)
        # The level was NOT lost: the polling loop wrote it durably at the next checkpoint.
        self.assertIn("poll=4", result.stdout)

    def test_the_blocking_variant_really_does_hang(self):
        # Characterization: proves this test class exercises a REAL hazard rather than a
        # hypothetical one. If this ever stops timing out, the platform's lock semantics changed
        # and the reasoning behind request_stop_nowait must be re-examined.
        run_dir = Path(tempfile.mkdtemp())
        with self.assertRaises(subprocess.TimeoutExpired):
            _run_child(self._HANDLER_PROBE, str(run_dir), "blocking", timeout=8.0)

    # The two tests below assert the SAME property they always did (no acquisition on either writer
    # path may WAIT), observed at a new seam. IPD `y6mfgo` moved the primitive out of `runner_stop`
    # into `platform_lock`, so `runner_stop.fcntl` no longer exists to patch; the acquisition
    # parameters are now recorded on `platform_lock.acquire` itself, which is strictly more direct
    # evidence than the raw `flock` operation flags were, because it observes the CONTRACT the caller
    # requests rather than one backend's bit flags.

    def _recording_acquire(self, calls):
        real_acquire = platform_lock.acquire

        def recording_acquire(path, *, blocking=False, timeout=None):
            calls.append({"blocking": blocking, "timeout": timeout})
            return real_acquire(path, blocking=blocking, timeout=timeout)

        return recording_acquire

    def _assert_never_waits(self, calls):
        self.assertTrue(calls, "expected an exclusive acquire attempt")
        for call in calls:
            self.assertFalse(
                call["blocking"],
                f"a stop writer must never take a blocking acquire; it deadlocks a signal "
                f"handler (recorded {call})",
            )
            # A non-zero timeout would WAIT inside the primitive, which is the same hazard by
            # another name. Waiting is done by the module's own bounded RETRY loop, above the lock.
            self.assertIn(
                call["timeout"],
                (None, 0, 0.0),
                f"a stop writer must not wait inside the lock (recorded {call})",
            )

    def test_handler_path_takes_no_blocking_acquire(self):
        calls = []
        run_dir = Path(tempfile.mkdtemp())
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)
        with mock.patch.object(
            runner_stop.platform_lock, "acquire", self._recording_acquire(calls)
        ):
            runner_stop.request_stop_nowait(run_dir, 3, "handler")
        self._assert_never_waits(calls)
        print(f"handler-path acquisitions (all non-blocking): {calls}")

    def test_request_stop_also_never_issues_a_blocking_acquire(self):
        # Even the non-handler writer must not block indefinitely: it retries the non-blocking
        # acquire under a bounded deadline and fails loudly.
        calls = []
        run_dir = Path(tempfile.mkdtemp())
        with mock.patch.object(
            runner_stop.platform_lock, "acquire", self._recording_acquire(calls)
        ):
            runner_stop.request_stop(run_dir, 3, "main")
        self._assert_never_waits(calls)
        print(f"request_stop acquisitions (all non-blocking): {calls}")


class DeferredRequestTests(_RunDirCase):
    """E-06: the process-local deferral slot, and the poll draining it DURABLY.

    ONE table replaces the level-varying half of three tests
    (`test_nowait_writes_durably_when_the_lock_is_free`,
    `test_nowait_defers_when_contended_and_the_poll_drains_it`,
    `test_deferred_slot_keeps_the_highest_level`). Each wrote through the handler-safe writer under one
    lock condition and asserted one outcome; the CONTENTION STATE and the LEVEL are the data, so they
    are the columns.

    EVERY LEVEL KEEPS ITS OWN ROW IN BOTH CONTENTION STATES, which is the safety rule this file is
    written to. The deferral slot is the ONLY path by which a signal-triggered stop becomes durable, so
    a level that survives contention while another silently does not would mean an operator's Ctrl-C
    was recorded at some levels and lost at others - and lost SILENTLY, because the handler cannot
    report anything. So each row asserts the level SPECIFICALLY: which level lands in the slot, which
    level the drain writes, and which level reads back from disk afterwards.

    THE FULL ROUND TRIP IS ASSERTED ON EVERY ROW, never a weakened half. A deferred request is only
    worth anything if it eventually reaches DISK, so a contended row walks the whole path: the writer
    DEFERS rather than blocking (the measured deadlock), nothing is durable yet, the poll returns None
    WHILE THE LOCK IS STILL HELD (it cannot write either, and must not claim to have), the slot still
    holds the request after that failed attempt, and then after the lock is released the next poll
    makes it durable, clears the slot, and the record on disk carries that exact level.

    WHY THE SLOT MUST KEEP THE HIGHEST LEVEL rather than the latest: an operator pressing Ctrl-C
    repeatedly walks UP the ladder, and each press may land in the slot before any poll drains it. If
    the slot kept the last write, a stray lower request would erase a level-4 escalation that the
    operator had already asked for, which is the same silent downgrade R9 forbids, moved into memory.
    """

    def _hold_lock(self):
        """Hold the sidecar lock so the next nowait attempt is forced to defer."""

        lock_path = runner_stop.stop_request_lock_path(self.run_dir)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.addCleanup(handle.close)
        return handle

    #: (case, is the sidecar lock HELD when the handler writes?, the level(s) the handler requests in
    #: order, the level the slot must hold while contended (or None when it wrote through), the level
    #: the record must carry once the path completes, why this row exists)
    DEFERRALS = (
        (
            "level 1, lock FREE",
            False,
            (1,),
            None,
            1,
            "UNCONTENDED: the handler-safe writer writes level 1 THROUGH to disk immediately and "
            "defers nothing. This is the common case, and it must not route through the slot at all, "
            "because a request sitting in memory is lost if the process dies before the next poll",
        ),
        (
            "level 4, lock FREE",
            False,
            (4,),
            None,
            4,
            "the same uncontended path at the TERMINAL level, which is the one an operator's third "
            "Ctrl-C produces and the one whose loss would matter most. Both ends of the ladder are "
            "rows so a write-through that worked only for lower levels could not hide",
        ),
        (
            "level 1, lock HELD",
            True,
            (1,),
            1,
            1,
            "CONTENDED at the gentlest level: the handler must DEFER rather than block (the measured "
            "deadlock), and the next poll after the lock frees must make level 1 durable. A graceful "
            "stop requested during a contended moment must not be silently downgraded to no stop at all",
        ),
        (
            "level 3, lock HELD",
            True,
            (3,),
            3,
            3,
            "CONTENDED at the SIGTERM level, which is the level a real signal actually maps to, so this "
            "is the most operationally likely contended row in the table",
        ),
        (
            "level 4, lock HELD",
            True,
            (4,),
            4,
            4,
            "CONTENDED at the terminal level. THE MEASURED DEADLOCK CASE: a blocking acquire reached "
            "from a signal handler hangs the process outright, so this is exactly the path "
            "`request_stop_nowait` exists for, and the level that must survive it is the one the "
            "operator resorts to when nothing else worked",
        ),
        (
            "levels 1 then 4 then 2, lock HELD",
            True,
            (1, 4, 2),
            4,
            4,
            "THE SLOT KEEPS THE HIGHEST, NOT THE LATEST. An operator pressing Ctrl-C repeatedly walks "
            "UP the ladder and each press may land before any poll drains it; if the slot kept the last "
            "write, the trailing 2 would ERASE the level-4 escalation already asked for. That is the "
            "silent downgrade R9 forbids, moved from the file into memory",
        ),
    )

    def test_every_level_survives_the_deferral_slot_and_reaches_disk(self):
        wrong = []
        for case, held, levels, want_slot, want_final, why in self.DEFERRALS:
            with tempfile.TemporaryDirectory() as temp:
                run_dir = Path(temp)
                runner_stop.reset_deferred_request()
                problems = []
                handle = None
                try:
                    if held:
                        lock_path = runner_stop.stop_request_lock_path(run_dir)
                        lock_path.parent.mkdir(parents=True, exist_ok=True)
                        handle = lock_path.open("a+")
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                    results = [
                        runner_stop.request_stop_nowait(run_dir, level, "handler")
                        for level in levels
                    ]
                    last = results[-1]

                    if held:
                        if not last.deferred:
                            problems.append(
                                "the handler-safe writer did NOT defer while the lock was held. It "
                                "must never block: a blocking acquire reached from a signal handler "
                                "was MEASURED to hang the process outright"
                            )
                        if last.accepted:
                            problems.append(
                                "a deferred request must not report `accepted`; nothing is durable yet"
                            )
                        slot = runner_stop.pending_deferred_request()
                        if slot is None or slot[0] != want_slot:
                            problems.append(
                                f"the deferral slot holds {slot!r}, expected level {want_slot}. The "
                                "slot is the ONLY path by which a signal-triggered stop becomes "
                                "durable, so a level lost here is lost SILENTLY - a handler cannot "
                                "report anything"
                            )
                        if runner_stop.read_stop_request(run_dir) is not None:
                            problems.append(
                                "something became durable while the lock was held, which means the "
                                "write bypassed the lock that serializes monotonicity"
                            )
                        if runner_stop.poll_stop(run_dir) is not None:
                            problems.append(
                                "the poll reported a level while the lock was STILL HELD. It cannot "
                                "have written anything, so reporting a level claims a durability it "
                                "does not have"
                            )
                        if runner_stop.pending_deferred_request() is None:
                            problems.append(
                                "the failed drain CLEARED the slot, so the operator's request is now "
                                "lost entirely: it is neither on disk nor pending"
                            )
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                    else:
                        if last.deferred:
                            problems.append(
                                "the writer deferred even though the lock was FREE; a request left in "
                                "memory is lost if the process dies before the next poll"
                            )
                        if not last.accepted:
                            problems.append(
                                "an uncontended handler write must be `accepted` and durable at once"
                            )
                        if runner_stop.pending_deferred_request() is not None:
                            problems.append(
                                f"the slot is non-empty ({runner_stop.pending_deferred_request()!r}) "
                                "after an uncontended write that should have gone straight to disk"
                            )

                    drained = runner_stop.poll_stop(run_dir)
                    if drained != want_final:
                        problems.append(
                            f"the poll reports {drained!r} after the path completes, expected "
                            f"{want_final}"
                        )
                    if runner_stop.pending_deferred_request() is not None:
                        problems.append(
                            f"the slot still holds {runner_stop.pending_deferred_request()!r} after a "
                            "successful drain, so the same request would be re-applied on every "
                            "subsequent poll"
                        )
                    record = runner_stop.read_stop_request(run_dir)
                    if record is None:
                        problems.append(
                            "NOTHING REACHED DISK. A deferred request is worth nothing until it is "
                            "durable: the run could end without the stop ever being recorded"
                        )
                    elif record.level != want_final:
                        problems.append(
                            f"the durable record carries level {record.level}, expected {want_final}"
                        )
                finally:
                    if handle is not None:
                        handle.close()
                    runner_stop.reset_deferred_request()
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DEFERRALS)} deferral paths failed. EVERY LEVEL HAS ITS OWN ROW "
            "IN BOTH CONTENTION STATES because the slot is the ONLY route by which a signal-triggered "
            "stop becomes durable, and a level lost here is lost SILENTLY: a signal handler cannot "
            "report anything to the operator. Read WHICH STAGE failed, since the path has four: the "
            "writer must DEFER rather than block (a blocking acquire from a handler was MEASURED to "
            "hang the process), nothing may be durable while the lock is held, a poll that cannot "
            "write must report None AND keep the slot, and the first poll after the lock frees must "
            "make it durable and clear the slot. If the CONTENDED rows failed while the FREE rows "
            "passed, the fallback path broke and a stop requested at a busy moment is dropped; if the "
            "`levels 1 then 4 then 2` row failed, the slot now keeps the LATEST rather than the "
            "HIGHEST, so a stray low request erases an escalation the operator already asked for.\n"
            + "\n".join(wrong),
        )

    def test_drained_request_still_respects_monotonicity(self):
        """Kept separate: the DURABLE record and the SLOT disagree, and the durable one must win.

        Every table row starts from an empty record, so none of them can state this: a LOWER level
        sitting in the slot must not downgrade a HIGHER level already on disk. It is the intersection of
        the deferral path with R9, and the failure it guards is the worst shape in this file - a
        force-stop in progress being lowered by a stale in-memory request.
        """
        runner_stop.request_stop(self.run_dir, 4, "already-hard")
        handle = self._hold_lock()
        runner_stop.request_stop_nowait(self.run_dir, 1, "handler")
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        # Draining a LOWER deferred level must not downgrade the durable record.
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 4)
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)

    def test_a_failing_drain_leaves_the_request_pending(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP - `request_stop` is patched to RAISE.

        The table's contended rows cover a drain that cannot yet acquire the lock; this covers a drain
        that FAILS outright, which needs an injected exception. The claim is identical in spirit and
        opposite in mechanism: a failed drain must never drop the operator's request.
        """
        self._hold_lock()
        runner_stop.request_stop_nowait(self.run_dir, 3, "handler")
        with mock.patch.object(
            runner_stop,
            "request_stop",
            side_effect=runner_stop.StopRequestError("busy"),
        ):
            self.assertIsNone(runner_stop.poll_stop(self.run_dir))
        self.assertEqual(
            runner_stop.pending_deferred_request(),
            (3, "handler"),
            "a failed drain must never drop the operator's request",
        )

    def test_nowait_defers_rather_than_raising_on_a_filesystem_failure(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP - `Path.mkdir` is patched to a read-only error.

        A handler must never propagate an exception, even if the control dir is unusable, because an
        exception raised inside a signal handler surfaces at an arbitrary point in the main thread. The
        setup is an injected OSError, which no table row has.
        """
        with mock.patch.object(
            runner_stop.Path, "mkdir", side_effect=OSError(errno.EROFS, "read-only")
        ):
            result = runner_stop.request_stop_nowait(self.run_dir, 4, "handler")
        self.assertTrue(result.deferred)
        self.assertEqual(runner_stop.pending_deferred_request(), (4, "handler"))

    def test_nowait_rejects_an_invalid_level(self):
        """Kept separate: an `assertRaises` test, and the handler-safe writer's half of the writer
        contract asserted for `request_stop` above. Validation happens BEFORE any deferral, so a bogus
        level cannot be parked in the slot and drained later."""
        with self.assertRaises(ValueError):
            runner_stop.request_stop_nowait(self.run_dir, 9, "handler")


class LockContentionTests(unittest.TestCase):
    """`request_stop` fails LOUDLY on a stuck lock rather than hanging forever.

    NOT MERGED: the first test is an `assertRaises` with a TIMING bound (it measures elapsed time to
    prove the failure was fast rather than a hang), and the other two assert which LOCK FILES exist or
    are held, using a real driver lock. None of the three is a data point about a stop level.
    """

    def test_request_stop_raises_when_the_lock_stays_contended(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            lock_path = runner_stop.stop_request_lock_path(run_dir)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                started = time.monotonic()
                with self.assertRaises(runner_stop.StopRequestError):
                    runner_stop.request_stop(run_dir, 3, "blocked", timeout=0.2)
                elapsed = time.monotonic() - started
            self.assertLess(elapsed, 10.0, "must fail fast, not hang")

    def test_the_run_lock_is_not_reused_for_stop_requests(self):
        # Scope fence: `driver.lock` is a DIFFERENT lock with a run-long lifetime. Reusing it
        # would make an out-of-band `stop` impossible while a run holds it.
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            runner_stop.request_stop(run_dir, 3, "tester")
            self.assertFalse((run_dir / "driver.lock").exists())
            self.assertTrue((run_dir / "stop-request.lock").exists())

    def test_a_held_driver_lock_does_not_prevent_a_stop_request(self):
        # The out-of-band `stop` case: a live run holds driver.lock; a stop must still be
        # recordable from another process.
        from agent_workflows import oc_runipd

        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            with oc_runipd.run_lock(run_dir):
                result = runner_stop.request_stop(run_dir, 4, "second-terminal")
            self.assertTrue(result.accepted)
            self.assertEqual(runner_stop.read_stop_request(run_dir).level, 4)


class VerifierStopAndIsolatedGitStatusTests(unittest.TestCase):
    """Regression tests for stop handling during verification and isolated git status (hp9rot E-06, E-07).

    NOT MERGED: both tests build a REAL GIT REPOSITORY on disk, patch a driver's turn function, and
    drive `execute_item` through two different drivers. The setup is materially different from
    everything else in this file (which touches only a stop-request record), and each already
    sub-tests both drivers.
    """

    def test_verifier_stop(self):
        """E-06: Level 3/4 stop during verification turn records stop metadata, does not leave item in running status."""
        from agent_workflows import agy_runipd, oc_runipd

        for name, mod in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as temp:
                repo = Path(temp) / "repo"
                repo.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "config", "user.email", "test@example.invalid"],
                    cwd=repo,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test"], cwd=repo, check=True
                )
                plan_dir = repo / ".aw/records/plans/pending"
                plan_dir.mkdir(parents=True, exist_ok=True)
                plan = plan_dir / "20260908-demo-01-stp001-demo.ipd.md"
                plan.write_text(
                    "# IPD: stp001\n\n- Date: 2026-09-08\n- Kind: child\n- Status: approved\n- Set: demo\n- Order: 1\n- Id: stp001\n\n## Goal\nDemo.\n",
                    encoding="utf-8",
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=repo, check=True
                )

                run_dir = repo / ".aw/records/runs/run-test"
                (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
                (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

                item = {
                    "position": 1,
                    "id6": "stp001",
                    "setid": "demo",
                    "status": "queued",
                    "configured_file": str(plan.relative_to(repo)),
                    "action": "execute",
                }
                state = {
                    "run_id": "run-test",
                    "created_at": "2026-09-08T00:00:00+00:00",
                    "updated_at": "2026-09-08T00:00:00+00:00",
                    "selectors": ["demo"],
                    "repo": str(repo),
                    "queue": [item],
                    "set_sessions": {},
                    "session_id": None,
                    "options": {
                        "model": "opus",
                        "self_finalize": True,
                        "isolate_worktree": True,
                        "no_audit": False,
                    },
                }

                (run_dir / "outcomes" / "01-stp001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )

                def fake_turn(st, rd, it, *a, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    if (
                        kwargs.get("fresh_session")
                        or kwargs.get("log_suffix") == "verify"
                    ):
                        raise runner_stop.StopNowForce(requester="test")
                    wt = Path(work_dir) if work_dir else repo
                    (wt / "src").mkdir(parents=True, exist_ok=True)
                    (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
                    subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
                    subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
                    return 0, "ses1", str(run_dir / "log"), ["driver"]

                turn_fn = "run_opencode" if name == "oc_runipd" else "run_agy_turn"
                with (
                    mock.patch.object(mod, "driver_begin", lambda *a, **k: (0, "ok")),
                    mock.patch.object(mod, turn_fn, fake_turn),
                ):
                    with self.assertRaises(runner_stop.StopNowForce):
                        mod.execute_item(run_dir, state, item, recovery=False)

                self.assertIsNotNone(
                    item.get("stopped"), "stopped metadata must be recorded on item"
                )
                self.assertNotEqual(
                    item["status"], "running", "item must not be left in running status"
                )

    def test_stop_isolated_git_status(self):
        """E-07: Stop with dirty work in isolated worktree records git state listing modified files."""
        from agent_workflows import agy_runipd, oc_runipd

        for name, mod in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as temp:
                repo = Path(temp) / "repo"
                repo.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "config", "user.email", "test@example.invalid"],
                    cwd=repo,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test"], cwd=repo, check=True
                )
                (repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
                subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=repo, check=True
                )

                work_dir = Path(temp) / "isolated_lane"
                work_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "init", "-q"], cwd=work_dir, check=True)
                subprocess.run(
                    ["git", "config", "user.email", "test@example.invalid"],
                    cwd=work_dir,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test"], cwd=work_dir, check=True
                )
                (work_dir / "tracked.txt").write_text("initial\n", encoding="utf-8")
                subprocess.run(["git", "add", "tracked.txt"], cwd=work_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=work_dir, check=True
                )
                # Make isolated worktree dirty
                (work_dir / "dirty_file.txt").write_text(
                    "uncommitted dirt\n", encoding="utf-8"
                )

                run_dir = repo / ".aw/records/runs/run-test"
                run_dir.mkdir(parents=True, exist_ok=True)

                item = {"id6": "stp001", "position": 1}
                state = {"repo": str(repo), "run_id": "run-test"}

                # Check _record_forced_stop
                stop = runner_stop.StopNowForce(requester="test")
                record = mod._record_forced_stop(
                    run_dir, state, item, stop, work_dir=work_dir
                )
                self.assertIn("dirty_file.txt", record["git_state"])
                self.assertNotIn(
                    record["git_state"],
                    ("", "clean"),
                    "git_state must reflect dirty isolated worktree",
                )

                # Check _record_checkpoint_stop
                obs = runner_stop.CheckpointObserver(run_dir)
                rec2 = mod._record_checkpoint_stop(
                    run_dir, state, item, obs, work_dir=work_dir
                )
                self.assertIn("dirty_file.txt", rec2["git_state"])


if __name__ == "__main__":
    unittest.main()
