"""Model-free deterministic tests for bounded retry/correction, resume/cancel/crash recovery, and
the mutating `aw run` subcommands (awoptimize Order 07 `7yqm1v` E-01..E-04).

These tests are falsifiable: they assert DETECTION/REJECTION (raised typed exceptions, distinct
nonzero exit codes, error output) and concrete durable effects on the append-only ledger, never that
an enum equals itself. No live model, no network.

Coverage:
  * E-01 retry path: failed attempts preserved, budget enforced (RetryLimitExceededError), no
    repetition-to-success, evidence invalidated after change, idempotency dedup, escalation.
  * E-02 resume/cancel/crash: pure-ledger reconstruction, unknown_outcome detection + refusal +
    explicit reconciliation, torn-line crash recovery.
  * legal/illegal transitions mapped to run_state.TRANSITION_RULES, human gate, dependency branch,
    lock collision (lease), evidence invalidation.
  * E-03 CLI golden tests for every subcommand + each exit class; NO ANSI in machine output;
    terminal refusal (finalize refuses incomplete/invalid/unauthorized); JSONL index rebuild from
    the ledger.

MOST OF THIS FILE IS TABLE-DRIVEN, in two rounds. An earlier round tabulated the CLI surface (the
seventeen-invocation exit-class table and the wrong-format verdict table); a later one tabulated the
RECOVERY layer beneath it, where the repeated shape was: seed a ledger into one state, issue a call
or two, and read back one of a small fixed set of observables.

EXIT CODES AND JSON KEYS ARE LOAD-BEARING and are therefore asserted EXACTLY, with an exit-code
column in every CLI table. `run_cli.EXIT_*` is a closed set machines branch on (0 ok, 1 incomplete, 2
invalid invocation, 3 blocked, 4 invalid evidence, 5 corrupted ledger, 7 not a ledger), and the JSON
payloads are what an agent keys off. Human prose is pinned ONLY as the one identifying phrase a user
greps for (`Run:`, `incomplete`, `EV-FAILED-EXIT`, `not a run ledger`); whole sentences are not
asserted, because rewording a message is not a regression.

A DOCUMENTED ASYMMETRY IS PINNED HERE, NOT FIXED: `runs show` reports ledger corruption with exit 2
while its siblings use `EXIT_CORRUPTED_LEDGER` (5) for the same condition. That is measured, real,
and deliberately preserved by a row in `TestLedgerResolutionAndWrongFormatVerdict.VERDICTS` whose
comment names the code location. Do not "tidy" it: if it is ever unified, THAT row is the one to
update, and the prose claim beside it is what must not weaken.

WHAT IS DELIBERATELY NOT TABULATED, so the next reader does not redo the analysis. `assertRaises`
tests stay apart, because this module's typed exceptions carry the distinctions that matter - a
caller error (`InvalidRetryBudgetError`) must not be catchable as runtime budget exhaustion
(`RetryLimitExceededError`), and the three transition refusals are three DIFFERENT types because an
operator's fix differs for each; a cell asserting "it raised" would erase exactly that. Also apart:
`test_every_legal_edge_in_table_is_accepted`, which already iterates the product's own
`TRANSITION_RULES` and so extends itself when an edge is added; tests with patched collaborators or a
second thread; and tests whose claim is a durable effect read back through a fresh engine. Each
carries a one-line docstring saying which of these reasons applies.
"""

from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

from agent_workflows import cli, run_engine, run_evidence, run_recovery, run_state
from agent_workflows import run_cli
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store

RUN_ID = "run-abcdef1234"
HEAD = "1" * 40


def _run_record(run_id: str = RUN_ID, head: str = HEAD) -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "run",
        "run_id": run_id,
        "actor": "runtime",
        "workflow_digest": "a" * 64,
        "requirement_digest": "b" * 64,
        "repo": "agent-workflows",
        "head": head,
        "parent": "",
    }


def _requirement_set(reqs: List[str]) -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "requirement_set",
        "run_id": RUN_ID,
        "actor": "runtime",
        "requirement_digest": "b" * 64,
        "requirements": [{"id": r} for r in reqs],
        "scope_fence": {},
        "parent": "",
    }


_WORKFLOW: Dict[str, Any] = {
    "id": "wf",
    "steps": [
        {"id": "S-01", "action": "setup", "depends_on": [], "satisfies": ["R-01"]},
        {
            "id": "S-02",
            "action": "deploy",
            "depends_on": ["S-01"],
            "gates": ["deploy_gate"],
            "satisfies": ["R-02"],
        },
    ],
    "requirements": [{"id": "R-01"}, {"id": "R-02"}],
}


def _new_store(tmp: Path) -> ledger_store.RunLedgerStore:
    return ledger_store.RunLedgerStore(tmp / "run.jsonl")


def _seed_store(tmp: Path, reqs: List[str]) -> ledger_store.RunLedgerStore:
    store = _new_store(tmp)
    store.append(_run_record())
    store.append(_requirement_set(reqs))
    return store


def _engine(store: ledger_store.RunLedgerStore) -> run_engine.RunEngine:
    return run_engine.RunEngine(_WORKFLOW, store, run_id=RUN_ID)


def _plan_retry_accepted_limit(engine: run_engine.RunEngine, value: Any) -> Any:
    """The limit `plan_retry` ACCEPTED for `value`, distinguishing acceptance from rejection.

    `plan_retry` does two things in order: it VALIDATES the limit, then it applies it. Those two
    have different failures and must not be conflated, which is what this helper exists for.
    `InvalidRetryBudgetError` means the value was REJECTED and propagates, so the acceptance table
    reports it. `RetryLimitExceededError` means the value was accepted and then APPLIED - which is
    exactly what a legal `limit=0` must produce, since a zero budget makes the first retry already
    over budget - so the limit it carries is returned as the accepted answer.
    """

    try:
        return run_recovery.plan_retry(engine, "S-01", "transient", limit=value).limit
    except run_recovery.RetryLimitExceededError as exc:
        return exc.limit


# ==================================================================================================
# E-01: bounded retry + correction keyed by failure class
# ==================================================================================================


class TestBoundedRetry(unittest.TestCase):
    """What a retry does to the ledger, expressed as a sequence of retry calls and its observables.

    ONE table replaces five tests (`failed_attempt_is_preserved`,
    `retry_records_budget_and_preserves_failure`, `idempotency_key_dedup_no_duplicate`,
    `retry_is_not_repetition_to_success`, `retry_budget_remaining`). Every one of them ran the SAME
    setup (drive S-01 to a failed attempt), issued zero or more `plan_retry` calls, and asserted one
    or two of the same four observables: how many failed attempts survive, how many retries are
    recorded, what the step's reconstructed state is, and how much budget remains. Only the CALL
    SEQUENCE differed.

    Why the table beats the five. The four observables are not independent - they are four readings
    of one append-only ledger - and the realistic failure is a retry append that also does something
    else: deletes the failure it retries, counts a deduplicated call anyway, or flips the step to a
    non-failed state. Five tests each report one reading; the table reports the whole ledger state
    after each sequence, so "the failure was deleted" and "the count is off by one" are visible as
    the same defect or as different ones. It also puts the DEDUP rows immediately beside the
    distinct-key rows, which is the only way to see that a repeated key and a fresh key differ in
    exactly one reading.

    EVERY ROW ASSERTS ALL FOUR OBSERVABLES, not merely the one its predecessor cared about, which is
    strictly more coverage than the five tests had: the old dedup test never checked that the failed
    attempt survived deduplication, and the old budget test never checked the step state.

    THE PRESERVATION CLAIM IS THE LOAD-BEARING ONE and is why `failed_attempts` is a column on every
    row rather than one test: the ledger is APPEND-ONLY, so a retry that deletes the attempt it
    retries destroys the only record that the work was tried and failed. A row reporting 0 preserved
    attempts is that, whatever else it reports.

    The `assertRaises` refusals and the evidence-invalidation test are deliberately NOT rows: an
    exception's TYPE and its ATTRIBUTES are a different kind of claim than a ledger reading, and
    evidence invalidation needs a materially different seed (an evidence envelope appended before
    the failure) plus an assertion over a private sequence helper.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.store = _seed_store(self.tmp, ["R-01"])
        self.engine = _engine(self.store)
        # Drive S-01 to a failed attempt.
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")
        self.engine.record_step_attempt("S-01", state="failed", actor="executor")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    #: (case, the retry calls to issue as (idempotency_key or None) tuples, expected surviving failed
    #: attempts, expected recorded retries, expected `duplicate` flags one per call, expected
    #: remaining budget, why this row exists)
    #:
    #: Budgets are expressed relative to `DEFAULT_RETRY_LIMIT` by the loop, never hard-coded:
    #: aligning the default to the spec's 2 (2026-08-31) must not silently invalidate a row.
    RETRY_SEQUENCES = (
        (
            "no retry at all, immediately after the failure",
            (),
            1,
            0,
            (),
            0,
            "THE BASELINE, and the row that gives every other row its meaning: one failed attempt is "
            "durably present, no retry is recorded, and the FULL budget is available. A retry "
            "implementation that recorded something on read would show up here first",
        ),
        (
            "one retry with NO idempotency key",
            (None,),
            1,
            1,
            (False,),
            1,
            "the ordinary path: the retry is appended, it is NOT a duplicate, and the failed attempt "
            "it retries SURVIVES. A ledger that overwrote the failure would report 0 preserved here "
            "while still counting the retry, which is why both columns are on every row",
        ),
        (
            "the SAME idempotency key twice",
            ("k1", "k1"),
            1,
            1,
            (False, True),
            1,
            "IDEMPOTENCY: a repeated key is reported as `duplicate` AND appends nothing, so a "
            "crash-resumed caller that re-issues its retry does not consume budget twice. The two "
            "flags in sequence are the claim - the FIRST call must not be flagged duplicate, or the "
            "check is matching on something other than the recorded key",
        ),
        (
            "TWO DISTINCT idempotency keys",
            ("k1", "k2"),
            1,
            2,
            (False, False),
            2,
            "the mirror of the row above, and what stops it passing vacuously: an implementation "
            "that flagged EVERY keyed retry as a duplicate would satisfy the dedup row while making "
            "keyed retries useless. Two distinct keys must consume two units of budget",
        ),
    )

    def test_every_retry_sequence_leaves_the_ledger_in_the_right_state(self) -> None:
        limit = run_recovery.DEFAULT_RETRY_LIMIT
        wrong = []
        baseline_broken = 0
        for (
            case,
            keys,
            expect_failed,
            expect_retries,
            expect_dupes,
            budget_consumed,
            why,
        ) in self.RETRY_SEQUENCES:
            with tempfile.TemporaryDirectory() as d:
                store = _seed_store(Path(d), ["R-01"])
                eng = _engine(store)
                eng.release_step("S-01")
                eng.start_step("S-01")
                eng.record_step_attempt("S-01", state="failed", actor="executor")
                dupes = []
                for key in keys:
                    plan = run_recovery.plan_retry(
                        eng, "S-01", "transient", idempotency_key=key
                    )
                    dupes.append(plan.duplicate)
                problems = []
                preserved = run_recovery.failed_attempts(eng, "S-01")
                if len(preserved) != expect_failed:
                    problems.append(
                        f"{len(preserved)} failed attempt(s) survive, expected {expect_failed}. THE "
                        "LEDGER IS APPEND-ONLY: a retry that deletes the attempt it retries "
                        "destroys the only record that the work was tried and failed"
                    )
                elif preserved and preserved[0]["state"] != "failed":
                    problems.append(
                        f"the preserved attempt's state is {preserved[0]['state']!r}, expected "
                        "'failed'; the record survived but its verdict was rewritten"
                    )
                recorded = run_recovery.count_retries(eng, "S-01")
                if recorded != expect_retries:
                    problems.append(
                        f"{recorded} retry/retries recorded, expected {expect_retries}"
                    )
                if tuple(dupes) != expect_dupes:
                    problems.append(
                        f"the `duplicate` flags were {tuple(dupes)!r}, expected {expect_dupes!r}"
                    )
                # A retry NEVER converts a failed step to success by mere repetition.
                state = eng.step_state("S-01")
                if state != "failed":
                    problems.append(
                        f"the step reconstructs as {state!r}, expected 'failed'. A retry is "
                        "PERMISSION to try again, never a claim that the step now succeeded"
                    )
                remaining = run_recovery.retry_budget_remaining(eng, "S-01")
                expected_remaining = max(0, limit - budget_consumed)
                if remaining != expected_remaining:
                    problems.append(
                        f"budget remaining is {remaining}, expected {expected_remaining} "
                        f"(DEFAULT_RETRY_LIMIT is {limit} and this row consumes "
                        f"{budget_consumed})"
                    )
                if problems:
                    if not keys:
                        baseline_broken += 1
                    wrong.append(
                        f"  {case}\n    retry keys issued: {keys!r}\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        extra = ""
        if baseline_broken:
            extra = (
                " THE BASELINE ROW (no retry at all) IS AMONG THE FAILURES, and while it is broken "
                "every other row is uninterpretable: they all measure a DELTA from it, so a wrong "
                "starting state makes each of them wrong for a reason that is not about retries."
            )
        self.assertEqual(
            wrong,
            [],
            f"the retry path left the ledger wrong for {len(wrong)} of "
            f"{len(self.RETRY_SEQUENCES)} call sequences.{extra} All four readings come from ONE "
            "append-only ledger, so read WHICH reading moved: every row reporting too few PRESERVED "
            "attempts means the retry path now deletes what it retries, which is the severe case "
            "and loses history permanently; every row's COUNT being high by the number of calls "
            "means deduplication stopped working, so a crash-resumed caller silently burns its "
            "budget; a wrong STEP STATE means a retry is being read as a success. FIX: the budget "
            "figures are derived from `DEFAULT_RETRY_LIMIT`, so if only the budget column is wrong, "
            f"check whether the DEFAULT moved rather than editing a row.\n"
            + "\n".join(wrong),
        )

    def test_retry_limit_escalates_not_loops(self) -> None:
        """Kept separate: an `assertRaises` whose claim is the exception's ATTRIBUTES, not a reading.

        Once the budget is exhausted, plan_retry escalates with RetryLimitExceededError. Consumes
        exactly `DEFAULT_RETRY_LIMIT` retries and then expects the refusal, DERIVING the count from
        the constant rather than hard-coding it: the previous version issued three fixed retries,
        which silently coupled this test to the value being 3.
        """
        for i in range(run_recovery.DEFAULT_RETRY_LIMIT):
            run_recovery.plan_retry(
                self.engine, "S-01", "transient", idempotency_key=f"k{i + 1}"
            )
        with self.assertRaises(run_recovery.RetryLimitExceededError) as ctx:
            run_recovery.plan_retry(
                self.engine, "S-01", "transient", idempotency_key="k-over-budget"
            )
        self.assertEqual(ctx.exception.limit, run_recovery.DEFAULT_RETRY_LIMIT)
        self.assertGreaterEqual(
            ctx.exception.attempts, run_recovery.DEFAULT_RETRY_LIMIT
        )

    def test_retry_of_non_retryable_state_rejected(self) -> None:
        """Kept separate: an `assertRaises`, and the seed is materially different (a PERFORMED step).

        Every table row seeds a FAILED S-01, which is the only state a retry is legal from. This one
        needs the opposite seed, so folding it in would mean carrying a seed column no other row
        varies.
        """
        tmp2 = Path(tempfile.mkdtemp())
        st = _seed_store(tmp2, ["R-01"])
        eng = _engine(st)
        eng.release_step("S-01")
        eng.start_step("S-01")
        eng.record_step_attempt("S-01", state="performed", actor="executor")
        with self.assertRaises(run_recovery.NoRetryableStateError):
            run_recovery.plan_retry(eng, "S-01", "transient")

    def test_evidence_invalidated_after_change(self) -> None:
        """Kept separate: materially different setup and an assertion over a private seq helper.

        Evidence bound to the retried step is invalidated so a stale green result is not reused. The
        seed must append an evidence envelope BEFORE the failure, and the claim is a set equality
        between the plan's `invalidated_evidence` and the sequence numbers `_step_evidence_seqs`
        reported live beforehand - an object no table row constructs.
        """
        tmp2 = Path(tempfile.mkdtemp())
        st = _seed_store(tmp2, ["R-01"])
        eng = _engine(st)
        eng.release_step("S-01")
        eng.start_step("S-01")
        # capture evidence bound to S-01 BEFORE the failure
        st.append(
            run_evidence.build_evidence_envelope(
                RUN_ID, "command", ["S-01"], HEAD, "/repo"
            )
        )
        eng.record_step_attempt("S-01", state="failed", actor="executor")
        # live evidence exists before retry
        recs_before = st.read_records()
        live_before = run_recovery._step_evidence_seqs(recs_before, "S-01")
        self.assertTrue(live_before)
        plan = run_recovery.plan_retry(eng, "S-01", "transient")
        self.assertEqual(set(plan.invalidated_evidence), set(live_before))
        # after invalidation, no live evidence remains bound to S-01
        recs_after = st.read_records()
        self.assertEqual(run_recovery._step_evidence_seqs(recs_after, "S-01"), ())

    def test_correction_required_appends_blocker(self) -> None:
        """Kept separate: a different VERB over a different record kind, not a retry sequence.

        `correction_required` appends a `correction` record that the completion predicate treats as
        a blocker. No table row calls it, and its observable is a record KIND rather than any of the
        four retry readings.
        """
        run_recovery.correction_required(self.engine, "R-01", "fix the bug")
        recs = self.store.read_records()
        corrections = [r for r in recs if r.get("kind") == "correction"]
        self.assertTrue(
            any(c.get("corrects_requirement") == "R-01" for c in corrections)
        )


# ==================================================================================================
# runcodes Order 3 (`sq61qd`): spec 25kzda 2.1's 0..10 inclusive retry-budget range
# ==================================================================================================


class TestRetryBudgetRangeValidation(unittest.TestCase):
    """The retry budget's legal range is enforced at every entry point that accepts one.

    Falsifiable by construction: these assert the BOUNDARIES (-1, 0, 10, 11), not a middle value,
    because an off-by-one is the only bug this validation can realistically ship and a middle value
    passes against one. They also assert the ERROR TYPE, since a bad `limit` (a caller error) must be
    distinguishable from `RetryLimitExceededError` (a step exhausting its budget at runtime).
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.store = _seed_store(self.tmp, ["R-01"])
        self.engine = _engine(self.store)
        # Drive S-01 to a failed attempt so it is retryable (a non-retryable step would raise
        # NoRetryableStateError first and mask which check actually fired).
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")
        self.engine.record_step_attempt("S-01", state="failed", actor="executor")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ---- what the three entry points ACCEPT, in one table -----------------------------------------

    #: (case, a probe taking the budget value and returning the accepted answer, why this row exists)
    #:
    #: The THREE ENTRY POINTS ARE THE COLUMN, which is the whole point: spec 25kzda 2.1's range must
    #: be enforced by ONE validator that all three route through, so the interesting property is that
    #: the same value gets the same answer everywhere. A per-function test cannot state that, and a
    #: per-function test is exactly how `plan_retry` came to be the only path with a bound.
    #:
    #: `retry_budget_remaining` is probed with a FRESH engine per row (no retries consumed), so its
    #: accepted answer is the budget itself and the three probes are directly comparable.
    ACCEPTANCE_PROBES = (
        (
            "validate_retry_budget, the shared validator called with the VALUE ALONE",
            lambda eng, value: run_recovery.validate_retry_budget(value),
            "the bound lives in ONE validator taking just the value (no engine, no step id), which "
            "is what makes it reachable from the `--retry-budget` flag layer (`uyeko5` E-04) where "
            "an operator value is validated at parse time and no engine or step exists yet",
        ),
        (
            "plan_retry(limit=...), the runtime path",
            _plan_retry_accepted_limit,
            "the path an actual retry takes. It must ROUTE THROUGH the validator rather than carry "
            "its own bound, and the accepted value must reach the returned plan's `limit` unchanged "
            "- a path that clamped instead of accepting would silently run a different budget than "
            "the caller asked for. MEASURED AND CORRECTED: a first draft of this probe called "
            "`plan_retry` directly and reported the LOWER BOUND as refused, because `limit=0` is "
            "VALIDATED fine and then correctly raises `RetryLimitExceededError` on the spot (zero "
            "budget means the first retry is already over budget). That is the product behaving "
            "right, so the probe now distinguishes a BUDGET-EXHAUSTION refusal, which confirms the "
            "limit was accepted and applied, from an `InvalidRetryBudgetError`, which is a rejection",
        ),
        (
            "retry_budget_remaining(limit=...), the read path",
            lambda eng, value: run_recovery.retry_budget_remaining(
                eng, "S-01", limit=value
            ),
            "the third entry point, and the one most likely to be forgotten: it is a READ, so an "
            "unvalidated limit here produces a plausible-looking number rather than an error. With "
            "no retries consumed its answer IS the budget, which is what makes it comparable to the "
            "two rows above",
        ),
    )

    #: (case, the value, the answer every entry point must return for it, why this row exists)
    #:
    #: BOUNDARIES ONLY, plus one interior value and the shipped default. An off-by-one is the only
    #: bug this validation can realistically ship, and a middle value passes against one.
    ACCEPTED_VALUES = (
        (
            "the inclusive LOWER bound",
            run_recovery.MIN_RETRY_LIMIT,
            run_recovery.MIN_RETRY_LIMIT,
            "0 is LEGAL and means zero retries. The boundary that a `> 0` check would wrongly "
            "reject, and the one a falsy-value bug would silently replace with the default (its "
            "BEHAVIOR is asserted separately, because acceptance alone would not catch that)",
        ),
        (
            "the inclusive UPPER bound",
            run_recovery.MAX_RETRY_LIMIT,
            run_recovery.MAX_RETRY_LIMIT,
            "10 is LEGAL: the range is inclusive at BOTH ends, so this is the boundary a `< MAX` "
            "check would wrongly reject. Paired with the `MAX + 1` refusal below it fixes the "
            "boundary exactly",
        ),
        (
            "an arbitrary interior value, deliberately NOT the default",
            5,
            5,
            "chosen so this row says nothing about what the default happens to be. If the interior "
            "failed while both boundaries passed, the validator would be an allowlist of two values "
            "rather than a range",
        ),
        (
            "the SHIPPED DEFAULT",
            run_recovery.DEFAULT_RETRY_LIMIT,
            run_recovery.DEFAULT_RETRY_LIMIT,
            "the default must satisfy the bound it ships beside, or every unqualified call refuses. "
            "Derived from the constant rather than hard-coding 2, so aligning the default cannot "
            "silently invalidate this row",
        ),
    )

    def test_every_entry_point_accepts_every_legal_budget_identically(self) -> None:
        wrong = []
        for case, value, expected, why in self.ACCEPTED_VALUES:
            for probe_case, probe, probe_why in self.ACCEPTANCE_PROBES:
                with tempfile.TemporaryDirectory() as d:
                    store = _seed_store(Path(d), ["R-01"])
                    eng = _engine(store)
                    eng.release_step("S-01")
                    eng.start_step("S-01")
                    eng.record_step_attempt("S-01", state="failed", actor="executor")
                    try:
                        got = probe(eng, value)
                    except Exception as exc:
                        wrong.append(
                            f"  {case} ({value!r}) via {probe_case}\n"
                            f"    - REFUSED a legal budget: {type(exc).__name__}: {exc}\n"
                            f"    this row exists because: {why}\n"
                            f"    this entry point is probed because: {probe_why}"
                        )
                        continue
                    if got != expected:
                        wrong.append(
                            f"  {case} ({value!r}) via {probe_case}\n"
                            f"    - expected {expected!r}, got {got!r}\n"
                            f"    this row exists because: {why}\n"
                            f"    this entry point is probed because: {probe_why}"
                        )
        cells = len(self.ACCEPTED_VALUES) * len(self.ACCEPTANCE_PROBES)
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {cells} (legal budget x entry point) cells answered wrongly. Spec "
            "`25kzda` 2.1's range is enforced by ONE validator all three entry points route "
            "through, so read the grouping: an entire ENTRY POINT column failing means that path "
            "stopped delegating and grew a bound of its own (which is the state this table exists to "
            "prevent - `plan_retry` was once the only path with any bound at all); an entire VALUE "
            "row failing means the range itself moved. FIX: if only the BOUNDARY rows fail, it is an "
            "off-by-one and the range is inclusive at both ends; if only the DEFAULT row fails, the "
            "shipped default has drifted outside the bound it ships beside, which makes every "
            f"unqualified call refuse.\n" + "\n".join(wrong),
        )

    # ---- the refusals, each an assertRaises kept apart ---------------------------------------------

    def test_validator_rejects_below_lower_bound(self) -> None:
        """-1 is refused, and the message names the offending value and the legal range."""
        with self.assertRaises(run_recovery.InvalidRetryBudgetError) as ctx:
            run_recovery.validate_retry_budget(-1)
        msg = str(ctx.exception)
        self.assertIn("-1", msg)
        self.assertIn(
            f"{run_recovery.MIN_RETRY_LIMIT}..{run_recovery.MAX_RETRY_LIMIT}", msg
        )

    def test_validator_rejects_above_upper_bound(self) -> None:
        """11 (one past the inclusive upper bound) is refused: the boundary, not a middle value."""
        with self.assertRaises(run_recovery.InvalidRetryBudgetError) as ctx:
            run_recovery.validate_retry_budget(run_recovery.MAX_RETRY_LIMIT + 1)
        self.assertIn(str(run_recovery.MAX_RETRY_LIMIT + 1), str(ctx.exception))

    def test_validator_rejects_an_effectively_unbounded_budget(self) -> None:
        """A huge budget is refused: an unbounded correction loop is what the bound exists to stop."""
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.validate_retry_budget(10_000)

    def test_validator_rejects_bool_and_non_int(self) -> None:
        """`bool` is a subclass of `int`, so `True` must not silently mean a budget of 1."""
        for bad in (True, False, 2.0, "3", None):
            with self.subTest(bad=bad):
                with self.assertRaises(run_recovery.InvalidRetryBudgetError):
                    run_recovery.validate_retry_budget(bad)

    def test_invalid_budget_error_is_not_a_retry_limit_exceeded_error(self) -> None:
        """A caller error must NOT be catchable as normal budget escalation, and vice versa.

        Asserted rather than assumed: `assertRaises(Exception)` would pass against exactly the
        conflation this distinction forbids.
        """
        self.assertTrue(
            issubclass(run_recovery.InvalidRetryBudgetError, run_recovery.RecoveryError)
        )
        self.assertFalse(
            issubclass(
                run_recovery.InvalidRetryBudgetError,
                run_recovery.RetryLimitExceededError,
            )
        )
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.validate_retry_budget(-1)
        try:
            run_recovery.validate_retry_budget(-1)
        except (
            run_recovery.RetryLimitExceededError
        ) as exc:  # pragma: no cover - must not happen
            self.fail(f"out-of-range budget was caught as budget exhaustion: {exc!r}")
        except run_recovery.InvalidRetryBudgetError:
            pass

    # ---- plan_retry routes through the same validator ---------------------------------------------

    def test_plan_retry_rejects_below_lower_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=-1)

    def test_plan_retry_rejects_above_upper_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(
                self.engine,
                "S-01",
                "transient",
                limit=run_recovery.MAX_RETRY_LIMIT + 1,
            )

    def test_plan_retry_rejects_bool_budget(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=True)

    def test_an_out_of_range_budget_appends_nothing(self) -> None:
        """A refused budget is refused BEFORE any ledger append (fail closed, no side effect)."""
        before = len(self.store.read_records())
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=-1)
        self.assertEqual(len(self.store.read_records()), before)

    # ---- retry_budget_remaining routes through the same validator ---------------------------------

    def test_retry_budget_remaining_rejects_below_lower_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=-1)

    def test_retry_budget_remaining_rejects_above_upper_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.retry_budget_remaining(
                self.engine, "S-01", limit=run_recovery.MAX_RETRY_LIMIT + 1
            )

    def test_retry_budget_remaining_rejects_bool_budget(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=True)

    def test_retry_budget_remaining_clamp_still_never_negative(self) -> None:
        """The independent `max(0, ...)` clamp survives: a consumed budget never reports negative."""
        limit = run_recovery.MIN_RETRY_LIMIT + 1
        run_recovery.plan_retry(
            self.engine, "S-01", "transient", limit=limit, idempotency_key="k1"
        )
        self.assertEqual(
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=limit), 0
        )

    # ---- 0 means NO RETRIES, behaviorally ---------------------------------------------------------

    def test_zero_budget_means_no_retries_not_the_default(self) -> None:
        """Kept separate: an `assertRaises` plus the BEHAVIOR of an accepted value, not acceptance.

        The acceptance table already proves `limit=0` is ACCEPTED at all three entry points. That is
        not enough on its own, and this is the test that says why: an implementation treating the
        falsy 0 as "unset" and swapping in `DEFAULT_RETRY_LIMIT` would be ACCEPTED by every row of
        that table while running two retries where the caller asked for none. So the claim here is
        that zero MEANS zero - the FIRST retry is refused, and nothing is recorded.
        """
        zero = run_recovery.MIN_RETRY_LIMIT
        self.assertEqual(
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=zero), 0
        )
        with self.assertRaises(run_recovery.RetryLimitExceededError) as ctx:
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=zero)
        self.assertEqual(ctx.exception.limit, zero)
        # No retry was recorded: the FIRST retry was refused, not merely a later one.
        self.assertEqual(run_recovery.count_retries(self.engine, "S-01"), 0)


# ==================================================================================================
# E-02: resume / cancel / crash recovery
# ==================================================================================================


class TestResumeCancelCrash(unittest.TestCase):
    """What `resume` reconstructs from a ledger, and what `cancel` writes into one.

    ONE table replaces two tests (`resume_reconstructs_from_ledger_only`,
    `cancel_records_terminal_transaction`). Both seeded a ledger into one shape and asked whether the
    run reconstructs the way that shape implies; they differed in the shape and in which field they
    happened to check.

    Why the table beats the two. `resume` is PURE LEDGER RECONSTRUCTION - that is the whole design
    claim - so the interesting property is that a run's state is a FUNCTION OF ITS LEDGER and of
    nothing else, which one seed cannot state. The terminal/non-terminal contrast is the load-bearing
    part and it needs both shapes side by side: a `resume` that reported `terminal=False`
    unconditionally would pass the old non-terminal test forever, and the cancelled row is what
    refutes it. Every row also asserts through a FRESH ENGINE over the same file, so no row can pass
    on in-memory state the writer happened to leave behind.

    THE FRESH-ENGINE RE-READ IS NOT DECORATION. The seeds are built by driving an engine, so reading
    back through the SAME object would prove only that the object remembers what it was told. Each
    row therefore constructs a second engine over the same path and asserts the same facts from it,
    which is what makes "reconstructed from the ledger" a tested claim rather than a docstring.

    The `assertRaises` refusals (unknown-outcome detection, both reconciliation rejections) and the
    crash-recovery test are deliberately NOT rows, each with its own note saying why.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    #: (case, a builder driving one seed shape and returning any extra facts, expected terminal flag,
    #: expected reconstructed run_state, why this row exists)
    #:
    #: Each builder receives a fresh engine over a fresh ledger and leaves the run in one shape. The
    #: table then RE-READS every fact through a SECOND engine over the same file.
    RECONSTRUCTIONS = (
        (
            "a seeded run nobody has touched",
            lambda eng: None,
            False,
            "pending",
            "THE FLOOR: a run with a `run` record and a requirement set and nothing else "
            "reconstructs as `pending` and NOT terminal, so an interrupted operator can resume it. "
            "If this reported terminal, every resumable run would look finished",
        ),
        (
            "a run whose root step was PERFORMED",
            lambda eng: (
                eng.release_step("S-01"),
                eng.start_step("S-01"),
                eng.record_step_attempt("S-01", state="performed", actor="executor"),
            ),
            False,
            "running",
            "PROGRESS IS NOT COMPLETION: one performed step moves the run to `running` and it is "
            "still NOT terminal, because S-02 remains. This is the row that would break if `resume` "
            "read progress as doneness, which would strand the rest of the DAG unexecuted",
        ),
        (
            "a run that was CANCELLED",
            lambda eng: run_recovery.cancel(
                eng, reason="operator abort", actor="coordinator"
            ),
            True,
            run_state.STATE_CANCELLED,
            "THE TERMINAL ROW, and what makes the two above non-vacuous: a `resume` hard-coding "
            "`terminal=False` would satisfy both of them and only fail here. It also proves "
            "`cancel`'s effect is DURABLE - the cancellation is read back out of the file by an "
            "engine that never saw the call",
        ),
    )

    def test_every_ledger_shape_reconstructs_the_state_it_implies(self) -> None:
        wrong = []
        terminal_rows_broken = 0
        for case, build, expect_terminal, expect_state, why in self.RECONSTRUCTIONS:
            with tempfile.TemporaryDirectory() as d:
                store = _seed_store(Path(d), ["R-01"])
                build(_engine(store))
                # A SECOND engine over the SAME file: no shared memory with the writer above, so
                # every fact below had to come out of the ledger.
                fresh = _engine(ledger_store.RunLedgerStore(store.path))
                problems = []
                report = run_recovery.resume(fresh)
                if report.run_id != RUN_ID:
                    problems.append(
                        f"reconstructed run_id {report.run_id!r}, expected {RUN_ID!r}"
                    )
                if report.terminal is not expect_terminal:
                    problems.append(
                        f"terminal is {report.terminal!r}, expected {expect_terminal!r}"
                    )
                    if expect_terminal:
                        terminal_rows_broken += 1
                if report.run_state != expect_state:
                    problems.append(
                        f"run_state is {report.run_state!r}, expected {expect_state!r}"
                    )
                # No row seeds an interrupted side effect, so none may report one: a false unknown
                # outcome would refuse a resume the operator is entitled to.
                unknown = run_recovery.detect_unknown_outcomes(fresh)
                if unknown != ():
                    problems.append(
                        f"reports unknown outcomes {unknown!r}, but this shape has no step left "
                        "running; a false positive REFUSES a legitimate resume"
                    )
                if problems:
                    wrong.append(
                        f"  {case}\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        extra = ""
        if terminal_rows_broken:
            extra = (
                " THE TERMINAL (cancelled) ROW IS AMONG THE FAILURES, which matters out of "
                "proportion to its count: the two non-terminal rows are VACUOUS against a `resume` "
                "that reports `terminal=False` unconditionally, and this is the only row that "
                "refutes that."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.RECONSTRUCTIONS)} ledger shapes reconstructed wrongly."
            f"{extra} Every fact here is re-read through a SECOND engine over the same file, so a "
            "failure means the LEDGER does not carry what the run did - not merely that a return "
            "value is off. Read the grouping: all rows reporting the same wrong `run_state` means "
            "the state derivation changed; the TERMINAL flags disagreeing means the "
            "terminal-detection predicate moved, which is the dangerous direction in both senses "
            "(a resumable run that looks finished is abandoned, a finished run that looks resumable "
            "gets restarted). FIX: an unexpected unknown-outcome report means detection now fires on "
            f"a shape with nothing running, which refuses resumes that should succeed.\n"
            + "\n".join(wrong),
        )

    def test_unknown_outcome_detected_and_refused(self) -> None:
        """Kept separate: an `assertRaises` whose claim is WHICH STEP the exception names.

        Every `RECONSTRUCTIONS` row asserts a successful reconstruction and that NO unknown outcome
        is reported. This is the opposite shape - a step left running with no terminal attempt, where
        `resume` must REFUSE - and the assertion is on the raised exception's `step_id`, which no row
        returning a report can express.
        """
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step(
            "S-01"
        )  # running, no terminal attempt -> interrupted side effect
        self.assertEqual(run_recovery.detect_unknown_outcomes(eng), ("S-01",))
        with self.assertRaises(run_recovery.UnknownOutcomeError) as ctx:
            run_recovery.resume(eng)
        self.assertEqual(ctx.exception.step_id, "S-01")

    def test_reconcile_unknown_outcome_requires_explicit_state(self) -> None:
        """Kept separate: an `assertRaises` and a BEFORE/AFTER pair around one mutation.

        Reconciliation requires an explicit terminal outcome; a silent rerun is never done. The
        claim spans a rejection and then a state TRANSITION on the same engine (unknown-outcome
        present, then cleared), which is a sequence rather than a seed shape.
        """
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        # invalid reconciled state rejected
        with self.assertRaises(run_recovery.NoRetryableStateError):
            run_recovery.reconcile_unknown_outcome(eng, "S-01", "running")
        # explicit reconciliation clears the unknown-outcome condition
        run_recovery.reconcile_unknown_outcome(
            eng, "S-01", "performed", actor="coordinator"
        )
        self.assertEqual(run_recovery.detect_unknown_outcomes(eng), ())
        report = run_recovery.resume(eng)
        self.assertEqual(report.run_state, "running")

    def test_reconcile_of_non_unknown_step_rejected(self) -> None:
        """Kept separate: an `assertRaises` over a step with NOTHING recorded against it."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        with self.assertRaises(run_recovery.RecoveryError):
            run_recovery.reconcile_unknown_outcome(eng, "S-01", "performed")

    def test_cancel_reports_the_reason_it_was_given(self) -> None:
        """Kept separate: the RETURNED snapshot's reason text, not the reconstructed run state.

        The table's cancelled row already proves the cancellation is DURABLE (a fresh engine reads
        the run back as terminal-cancelled). What it cannot see is the operator's REASON, which
        `resume`'s report does not carry: it lives on the snapshot `cancel` returns. Asserted here so
        an abort recorded with a reason cannot silently drop it, which would leave a cancelled run
        with no record of why.
        """
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        snap = run_recovery.cancel(eng, reason="operator abort", actor="coordinator")
        self.assertEqual(snap.state, run_state.STATE_CANCELLED)
        self.assertEqual(snap.cancellation_reason, "operator abort")

    def test_crash_recovery_truncates_torn_line_and_flags_unknown(self) -> None:
        """Kept separate: materially different setup (a hand-torn file) and a BEFORE/AFTER claim.

        `recover_crash` truncates a torn trailing line and reconstructs surviving state. The seed is
        a file mutated OUTSIDE the store's own append path - a partial line with no newline, as a
        crash mid-append leaves - and the assertions are about the RECOVERY report (a torn line was
        found, bytes were truncated), which no reconstruction row produces.
        """
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        eng.record_step_attempt("S-01", state="performed", actor="executor")
        # Simulate a crash mid-append: a torn partial trailing line with no newline.
        with open(store.path, "a", encoding="utf-8") as fh:
            fh.write('{"kind":"step_attempt","seq":99,"partial"')
        report = run_recovery.recover_crash(eng)
        self.assertTrue(report.recovered_torn_line)
        self.assertGreater(report.truncated_bytes, 0)
        # After recovery, the surviving ledger is clean and reconstructs S-01 performed.
        self.assertEqual(eng.step_state("S-01"), "performed")


# ==================================================================================================
# Legal/illegal transitions, human gate, dependency branch, lock collision
# ==================================================================================================


class TestTransitionsAndDependencies(unittest.TestCase):
    """The state machine's edges, its three refusal classes, the DAG gate, and the writer lock.

    DELIBERATELY NOT TABULATED, and the reasoning is recorded so the next agent does not repeat the
    investigation. Nothing here is a cluster of rows differing only in data:

    * `test_every_legal_edge_in_table_is_accepted` is ALREADY the table, and a better one than a
      hand-written row set could be: it iterates `run_state.TRANSITION_RULES` itself, deriving the
      actor and the predicate FROM each rule, so adding an edge to the product extends the coverage
      automatically. Re-expressing those edges as literal rows would freeze a copy that a new edge
      could not fail.
    * The three refusals are `assertRaises` over three DIFFERENT exception types
      (`IllegalTransitionError`, `UnauthorizedActorError`, `PredicateUnsatisfiedError`), which is the
      whole point of them: they are the three reasons a transition can be refused, and an operator's
      fix differs for each. A table cell asserting "it raised" would be satisfied by any of the
      three, so merging them would delete the distinction they exist to make.
    * The dependency-gate and lock-collision tests are structurally different from everything else
      here: one is a BEFORE/AFTER sequence over a mutating engine, the other runs a second THREAD to
      contend for a lease.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.store = _seed_store(self.tmp, ["R-01", "R-02"])
        self.engine = _engine(self.store)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_every_legal_edge_in_table_is_accepted(self) -> None:
        """Already table-driven, and derived from the product's own rule table rather than restated.

        Each rule in TRANSITION_RULES is accepted for an authorized actor with its predicate.
        """
        for rule in run_state.TRANSITION_RULES:
            actor = sorted(rule.authorized_actors)[0]
            accepted = run_state.check_transition(
                rule.source,
                rule.target,
                actor,
                predicate_values={rule.required_predicate: True},
            )
            self.assertEqual(accepted.target, rule.target)

    def test_illegal_edge_rejected(self) -> None:
        """An edge absent from the table is rejected as illegal."""
        with self.assertRaises(run_state.IllegalTransitionError):
            run_state.check_transition("pending", "complete", "coordinator")

    def test_executor_cannot_author_completion(self) -> None:
        """verified -> complete authored by executor is rejected (unauthorized)."""
        with self.assertRaises(run_state.UnauthorizedActorError):
            run_state.check_transition(
                "verified",
                "complete",
                "executor",
                predicate_values={"every_frozen_completion_predicate_true": True},
            )

    def test_missing_predicate_rejected(self) -> None:
        """A legal, authorized edge with an unsatisfied predicate fails closed."""
        with self.assertRaises(run_state.PredicateUnsatisfiedError):
            run_state.check_transition(
                "pending",
                "runnable",
                "runtime",
                predicate_values={"dependencies_and_approvals_satisfied": False},
            )

    def test_dependency_branch_gates_downstream_step(self) -> None:
        """S-02 is not runnable until S-01 is performed (dependency) AND the gate is approved."""
        self.assertEqual(
            [s.step_id for s in self.engine.get_runnable_steps()], ["S-01"]
        )
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")
        self.engine.record_step_attempt("S-01", state="performed", actor="executor")
        # dependency satisfied, but the human gate blocks S-02
        self.assertEqual(self.engine.get_runnable_steps(), [])
        self.engine.record_approval("deploy_gate", approver="lead", actor="human")
        self.assertEqual(
            [s.step_id for s in self.engine.get_runnable_steps()], ["S-02"]
        )

    def test_lock_collision_fails_closed(self) -> None:
        """A second writer contending for the single-writer lock times out (lease serialization)."""
        held = threading.Event()
        release = threading.Event()

        def holder() -> None:
            with self.engine.lease(timeout=5.0):
                held.set()
                release.wait(2.0)

        t = threading.Thread(target=holder)
        t.start()
        self.assertTrue(held.wait(2.0))
        other = run_engine.RunEngine(
            _WORKFLOW,
            ledger_store.RunLedgerStore(self.store.path, lock_timeout=0.2),
            run_id=RUN_ID,
        )
        with self.assertRaises(ledger_store.LedgerLockError):
            with other.lease(timeout=0.2):
                pass
        release.set()
        t.join()


# ==================================================================================================
# E-03: CLI golden tests for every subcommand + each exit class
# ==================================================================================================


#: The check vocabulary shared by the two CLI-surface tables below. A row's expectations are a
#: tuple of these, so one loop can express "exits 4 AND names EV-FAILED-EXIT" and "exits 7 AND the
#: JSON says not_a_ledger AND denies corruption" without either table weakening to a single claim.
#:
#:   ("text-in", needle)         a substring a user or an agent greps for MUST be present
#:   ("text-not-in", needle)     a substring that MUST NOT be present (a wrong VERDICT, e.g. the
#:                               word "corrupt" on a file that is merely the wrong format)
#:   ("itext-in" / "itext-not-in", needle)
#:                               the same two, CASE-INSENSITIVELY, for prose whose capitalization
#:                               is not itself a contract
#:   ("json-eq", key, value)     machine output parses and that key equals that value EXACTLY
#:   ("json-in", key, member)    machine output parses and that key's collection contains it
#:
#: Case folding is deliberately confined to the TEXT modes: JSON keys and values are consumed by
#: machines, so they are always compared exactly.
_CHECK_MODES = (
    "text-in",
    "text-not-in",
    "itext-in",
    "itext-not-in",
    "json-eq",
    "json-in",
)


def _parse_machine(out: str) -> Any:
    """Parse machine output, tolerating both the pretty `--json` block and one-line `--agent`.

    `--agent` emits a single compact line (sometimes preceded by human prose), while `--json`
    pretty-prints a multi-line object, so neither "parse the whole thing" nor "parse the last line"
    works alone.
    """
    text = out.strip()
    try:
        return json.loads(text)
    except ValueError:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise
        return json.loads(lines[-1])


def _stdout_problems(out: str, checks: "tuple[tuple[Any, ...], ...]") -> List[str]:
    """Return one human-readable problem string per failed check (never raises, never short-circuits).

    Accumulating rather than asserting is what lets a row report BOTH a wrong exit code and a wrong
    payload in the same run, which is the difference between "the verdict moved" and "the wording
    moved".
    """
    problems: List[str] = []
    parsed: Any = None
    parse_error: Any = None
    if any(mode.startswith("json") for mode, *_ in checks):
        try:
            parsed = _parse_machine(out)
        except ValueError as exc:
            parse_error = exc
    for check in checks:
        mode = check[0]
        assert mode in _CHECK_MODES, f"unknown check mode {mode!r}"
        if mode in ("text-in", "itext-in"):
            haystack = out.lower() if mode == "itext-in" else out
            if check[1] not in haystack:
                problems.append(f"stdout is missing {check[1]!r}; got {out[:300]!r}")
        elif mode in ("text-not-in", "itext-not-in"):
            haystack = out.lower() if mode == "itext-not-in" else out
            if check[1] in haystack:
                problems.append(
                    f"stdout must NOT contain {check[1]!r} (that is the WRONG VERDICT for this "
                    f"input); got {out[:300]!r}"
                )
        elif parse_error is not None:
            problems.append(
                f"machine output did not parse as JSON ({parse_error}); got {out[:300]!r}"
            )
        elif not isinstance(parsed, dict):
            problems.append(f"machine output is not a JSON object; got {parsed!r}")
        elif check[1] not in parsed:
            problems.append(
                f"machine output has no key {check[1]!r}; keys are {sorted(parsed)}"
            )
        elif mode == "json-eq":
            if parsed[check[1]] != check[2]:
                problems.append(
                    f"machine key {check[1]!r} expected {check[2]!r}, got {parsed[check[1]]!r}"
                )
        elif check[2] not in parsed[check[1]]:
            problems.append(
                f"machine key {check[1]!r} does not contain {check[2]!r}; it is "
                f"{parsed[check[1]]!r}"
            )
    return problems


def _rewrite_is_byte_identical(index_path: Path) -> bool:
    """Re-derive the index at `index_path` and report whether the bytes are unchanged.

    Split out of the projection table so the determinism row stays a one-line probe like its
    neighbors. The ledger path is recovered from the sibling `run.jsonl`, which is how every seed in
    this module lays the two files out.
    """

    before = index_path.read_bytes()
    run_cli.write_index(index_path.parent / "run.jsonl", index_path)
    return index_path.read_bytes() == before


def _complete_run_records() -> List[Dict[str, Any]]:
    """Records for a clean, complete, finalizable run (requirements covered by verifier passes)."""
    return [
        _run_record(),
        _requirement_set(["R-01"]),
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "step_attempt",
            "run_id": RUN_ID,
            "actor": "executor",
            "step": "S-01",
            "state": "performed",
            "attempt": 1,
            "parent": "",
        },
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "verifier_decision",
            "run_id": RUN_ID,
            "actor": "verifier",
            "requirement": "R-01",
            "result": "satisfied",
            "parent": "",
        },
    ]


class TestRunCliSubcommands(unittest.TestCase):
    """Every `aw run`/`aw runs` invocation exits in its own class and says why (E-03).

    ONE table replaces seventeen tests of identical shape: seed a ledger, run one argv, assert the
    exit code and (sometimes) one substring or JSON key. Only the SEED, the ARGV and the EXPECTED
    VERDICT differed.

    Why the table beats the seventeen. THE EXIT CODES ARE A CLOSED SET THAT MACHINES CONSUME
    (`run_cli.EXIT_*`: 0 ok, 1 incomplete, 2 invalid invocation, 3 blocked, 4 invalid evidence, 5
    corrupted ledger, 6 operational, 7 not a ledger), and the realistic failure is not one command
    breaking in isolation but a renumbering, or a shared helper (`_build_engine`, the runnability
    check, the terminal-refusal gate) changing the class it maps a condition onto. Seventeen tests
    report that as seventeen unrelated red lines with no way to see that they all moved the SAME
    direction; the table reports one failure listing every invocation whose class moved, which is
    the shape of the real problem.

    MODES ARE COLUMNS, NOT SEPARATE TABLES. `--json` (pretty multi-line), `--agent` (one compact
    line) and plain human output are all in the `argv` column, and the `checks` column carries a
    check MODE per expectation so a row can make two DIFFERENT KINDS of claim about one invocation
    (exit 4 AND `EV-FAILED-EXIT` present; exit 7 AND `not_a_ledger` true AND the word "corrupt"
    absent) rather than being weakened to whichever single claim fits a uniform table.

    POSITIVE ROWS ARE IN THE SAME TABLE deliberately, and their failure message says so: every
    nonzero row is VACUOUS against a CLI that refuses everything, so `next` exiting 0 with S-01
    runnable, `record performed` exiting 0, `cancel` exiting 0 and `finalize` on a complete run
    exiting 0 are the rows that keep the refusal rows meaningful.

    HUMAN PROSE IS PINNED ONLY AS THE ONE IDENTIFYING PHRASE a user greps for (`Run:`,
    `incomplete`, `EV-FAILED-EXIT`). Whole sentences of error text are NOT asserted: they are not
    load-bearing, and pinning them would make a reworded message a test failure.
    """

    #: (case, seed, argv template, expected exit code, checks, why this row exists)
    #:
    #: `seed` is one of "none" (no ledger file at all), "incomplete", "complete", "root-performed",
    #: "bad-evidence", "corrupt". In the argv template `LEDGER` is replaced by the ledger path and
    #: `WORKFLOW` by the workflow JSON path, so a row stays readable as an invocation.
    INVOCATIONS = (
        # ---- exit 2: invalid invocation. An OPERATOR error, distinct from a run-state refusal. ----
        (
            "status on a ledger path that does not exist",
            "none",
            ("runs", "status", "LEDGER"),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "a missing file is the operator's mistake, so it is exit 2 and NOT exit 5 "
            "(corrupted) or 7 (wrong format): nothing was read, so nothing can be judged",
        ),
        (
            "start with no --step",
            "incomplete",
            ("run", "start", "LEDGER"),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "a required flag is missing, which is an invocation error and must not be reported as "
            "the run being blocked",
        ),
        (
            "record with a --state outside the enum",
            "incomplete",
            ("run", "record", "LEDGER", "--step", "S-01", "--state", "bogus"),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "an unparseable state is rejected at the boundary; accepting it would append a "
            "meaningless attempt to an append-only ledger that can never be deleted",
        ),
        (
            "record naming a step the workflow does not define",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-99",
                "--state",
                "performed",
            ),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "an UNKNOWN step is exit 2 while a known-but-not-runnable step is exit 3 (the row "
            "below). Collapsing the two would hide a typo'd step id as a dependency problem",
        ),
        # ---- exit 1: incomplete. The run was read fine; its predicates are unsatisfied. ----------
        (
            "status on an incomplete run (human output)",
            "incomplete",
            ("runs", "status", "LEDGER"),
            run_cli.EXIT_INCOMPLETE,
            (("text-in", "Run:"),),
            "`Run:` is the ONE identifying phrase a human greps for in the status block; the rest "
            "of the prose is deliberately not pinned",
        ),
        (
            "status --agent on an incomplete run",
            "incomplete",
            ("runs", "status", "LEDGER", "--agent"),
            run_cli.EXIT_INCOMPLETE,
            (("json-eq", "run_id", RUN_ID),),
            "MODE COLUMN: the machine mode must carry the same verdict as the human mode and "
            "surface the run id as a KEY, since an agent keys off the field rather than the prose",
        ),
        (
            "finalize refuses an incomplete run",
            "incomplete",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_INCOMPLETE,
            (("text-in", "incomplete"),),
            "TERMINAL REFUSAL: finalizing is the act that declares a run done, so an unsatisfied "
            "predicate must refuse rather than exit 0, and must NAME incompleteness as the reason",
        ),
        # ---- exit 3: blocked. Legal invocation, correct ledger, the run cannot proceed. ----------
        (
            "next when the only root step is already performed and S-02 is gated",
            "root-performed",
            ("runs", "next", "LEDGER", "--workflow", "WORKFLOW", "--agent"),
            run_cli.EXIT_BLOCKED,
            (("json-eq", "runnable_steps", []),),
            "nothing runnable is BLOCKED (3), not OK (0) with an empty list: an unattended driver "
            "polling `next` must be able to tell 'wait for a human' from 'there is work'",
        ),
        (
            "record a failed outcome",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-01",
                "--state",
                "failed",
            ),
            run_cli.EXIT_BLOCKED,
            (),
            "RECORDING A FAILURE SUCCEEDS AS AN APPEND BUT IS NOT SUCCESS: the command exits 3, so "
            "a script cannot read 'the step failed and I wrote that down' as a green step",
        ),
        (
            "record a step whose dependencies and gate are unmet",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-02",
                "--state",
                "performed",
            ),
            run_cli.EXIT_BLOCKED,
            (),
            "S-02 depends on an unperformed S-01 and needs deploy_gate, so claiming it performed is "
            "refused: the ledger must never record work the DAG says could not have happened",
        ),
        # ---- exit 6: operational. Authorization, not invocation shape and not run state. ---------
        (
            "cancel authored by the executor",
            "incomplete",
            ("run", "cancel", "LEDGER", "--actor", "executor"),
            run_cli.EXIT_OPERATIONAL,
            (),
            "only a coordinator or a human may cancel; an UNAUTHORIZED actor is its own class (6) "
            "so it is not confused with a malformed command (2) or a blocked run (3)",
        ),
        (
            "finalize authored by the executor",
            "complete",
            ("run", "finalize", "LEDGER", "--actor", "executor"),
            run_cli.EXIT_OPERATIONAL,
            (),
            "the executor cannot author its own completion. Note the seed is COMPLETE, so this row "
            "proves authority is checked even when every predicate would otherwise pass",
        ),
        # ---- exit 4 and 5: the two ways captured evidence can refuse a finalize. -----------------
        (
            "finalize with a tool_event that exited nonzero",
            "bad-evidence",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_INVALID_EVIDENCE,
            (("text-in", "EV-FAILED-EXIT"),),
            "a failing command inside a 'complete' run is INVALID EVIDENCE (4), separate from "
            "corruption (5). The finding code is asserted because it is what tells an agent WHICH "
            "evidence rule fired",
        ),
        (
            "finalize on a ledger whose hash chain was broken by hand",
            "corrupt",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_CORRUPTED_LEDGER,
            (),
            "TAMPERING IS ITS OWN CLASS (5): it must never be excused as merely incomplete (1) or "
            "invalid evidence (4), because the file itself can no longer be trusted",
        ),
        # ---- exit 0: the positive rows. Without these every row above is vacuous. ----------------
        (
            "next on a fresh run lists the runnable root step",
            "incomplete",
            ("runs", "next", "LEDGER", "--workflow", "WORKFLOW", "--json"),
            run_cli.EXIT_OK,
            (("json-in", "runnable_steps", "S-01"),),
            "POSITIVE: work available is exit 0 and NAMES the step. A CLI that returned 3 for "
            "everything would satisfy every blocked row above while being useless",
        ),
        (
            "record a performed outcome for a runnable root step",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-01",
                "--state",
                "performed",
            ),
            run_cli.EXIT_OK,
            (),
            "POSITIVE: the legal append succeeds, which is what makes the three refusal rows above "
            "evidence of a check rather than of a broken command. Durability is asserted "
            "separately by `test_a_recorded_attempt_is_durable_in_the_ledger`",
        ),
        (
            "resume a non-terminal run",
            "incomplete",
            ("runs", "resume", "LEDGER", "--json"),
            run_cli.EXIT_OK,
            (("json-eq", "terminal", False),),
            "POSITIVE: a healthy resume exits 0 and reports the run as NOT terminal, so a driver "
            "knows it may continue rather than that the run is over",
        ),
        (
            "cancel with a reason",
            "incomplete",
            ("run", "cancel", "LEDGER", "--reason", "abort", "--json"),
            run_cli.EXIT_OK,
            (
                ("json-eq", "cancelled", True),
                ("json-eq", "run_state", run_state.STATE_CANCELLED),
            ),
            "POSITIVE, and TWO KINDS OF CLAIM about one invocation: the command reports it acted "
            "(`cancelled`) AND that the reconstructed run state is terminal-cancelled, which is "
            "the durable effect rather than the report of it",
        ),
        (
            "finalize a complete run",
            "complete",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_OK,
            (("json-eq", "finalized", True),),
            "POSITIVE, and the most important one here: four rows above assert finalize REFUSES. "
            "Without this row a finalize that refused unconditionally would pass all of them",
        ),
    )

    def test_every_invocation_exits_in_its_class_and_says_why(self) -> None:
        wrong = []
        by_code: Dict[int, int] = {}
        for case, seed, template, expected_rc, checks, why in self.INVOCATIONS:
            with tempfile.TemporaryDirectory() as seed_dir:
                argv = self._materialize(template, Path(seed_dir), seed)
                rc, out = self._cli(*argv)
            problems = []
            if rc != expected_rc:
                by_code[expected_rc] = by_code.get(expected_rc, 0) + 1
                problems.append(
                    f"exit code expected {expected_rc} "
                    f"({self._exit_name(expected_rc)}), got {rc} ({self._exit_name(rc)})"
                )
            problems.extend(_stdout_problems(out, checks))
            if "\x1b" in out:
                problems.append(
                    "ANSI escape leaked into the output of a machine-consumed command"
                )
            if problems:
                printable = " ".join(
                    arg if "/" not in arg else f"<{Path(arg).name}>" for arg in argv
                )
                wrong.append(
                    f"  {case}\n    argv: aw {printable}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        code_summary = ", ".join(
            f"{self._exit_name(code)} ({count} row(s))"
            for code, count in sorted(by_code.items())
        )
        self.assertEqual(
            wrong,
            [],
            f"the run CLI gave the wrong verdict for {len(wrong)} of {len(self.INVOCATIONS)} "
            f"invocations. Wrong exit codes were expected in: {code_summary or 'none'}. THE EXIT "
            "CODES ARE CONSUMED BY MACHINES, so read the grouping before editing a row. Several "
            "rows expecting the SAME code failing together means that code was renumbered or its "
            "meaning moved; several DIFFERENT codes failing on commands that share a helper "
            "(`_build_engine`, the runnability check, the terminal-refusal gate) means the helper "
            "changed which class it maps a condition onto. FIX: if a row expecting EXIT_OK is "
            "failing, fix that FIRST, because every refusal row is vacuous against a CLI that "
            "refuses everything, and a refusal row passing beside a broken positive row proves "
            "nothing. A substring failure alone (right code, missing phrase) is the milder case: "
            "the verdict is intact and only the one identifying phrase a user or an agent greps "
            f"for moved.\n" + "\n".join(wrong),
        )

    @staticmethod
    def _exit_name(code: int) -> str:
        """Name an exit code, so a failure reads `EXIT_BLOCKED` rather than a bare `3`."""
        names = {
            value: name
            for name, value in vars(run_cli).items()
            if name.startswith("EXIT_") and isinstance(value, int)
        }
        return names.get(code, f"UNNAMED({code})")

    def _materialize(
        self, template: "tuple[str, ...]", seed_dir: Path, seed: str
    ) -> "list[str]":
        """Seed a ledger of the requested shape and substitute the LEDGER/WORKFLOW placeholders."""
        self.ledger = seed_dir / "run.jsonl"
        if seed == "incomplete":
            self._seed_incomplete()
        elif seed == "complete":
            self._seed_complete()
        elif seed == "root-performed":
            self._seed_root_performed()
        elif seed == "bad-evidence":
            self._seed_invalid_evidence()
        elif seed == "corrupt":
            self._seed_complete()
            self._corrupt_chain()
        else:
            assert seed == "none", f"unknown seed {seed!r}"
        workflow = str(seed_dir / "wf.json")
        (seed_dir / "wf.json").write_text(json.dumps(_WORKFLOW), encoding="utf-8")
        return [
            str(self.ledger)
            if arg == "LEDGER"
            else (workflow if arg == "WORKFLOW" else arg)
            for arg in template
        ]

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ledger = self.tmp / "run.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _store(self) -> ledger_store.RunLedgerStore:
        return ledger_store.RunLedgerStore(self.ledger)

    def _workflow_file(self) -> str:
        """Write the DAG workflow to a JSON file so DAG-dependent CLI commands know the steps."""
        p = self.tmp / "wf.json"
        p.write_text(json.dumps(_WORKFLOW), encoding="utf-8")
        return str(p)

    def _seed_complete(self) -> None:
        store = self._store()
        for rec in _complete_run_records():
            store.append(rec)

    def _seed_incomplete(self) -> None:
        store = self._store()
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))

    def _seed_root_performed(self) -> None:
        """Seed a run whose only root step is performed, leaving S-02 gated on deploy_gate."""
        self._seed_incomplete()
        self._store().append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "step_attempt",
                "run_id": RUN_ID,
                "actor": "executor",
                "step": "S-01",
                "state": "performed",
                "attempt": 1,
                "parent": "",
            }
        )

    def _seed_invalid_evidence(self) -> None:
        """Seed an otherwise-complete run carrying a tool_event that exited nonzero."""
        self._seed_root_performed()
        store = self._store()
        store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "tool_event",
                "run_id": RUN_ID,
                "actor": "executor",
                "argv": ["pytest"],
                "cwd": "/repo",
                "exit_code": 1,  # failed exit -> EV-FAILED-EXIT
                "stdout_sha256": "e" * 64,
                "parent": "",
            }
        )
        store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "verifier_decision",
                "run_id": RUN_ID,
                "actor": "verifier",
                "requirement": "R-01",
                "result": "satisfied",
                "parent": "",
            }
        )

    def _corrupt_chain(self) -> None:
        """Break the hash chain by hand-appending a line with a wrong prev_hash."""
        with open(self.ledger, "a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "step_attempt",
                        "seq": 99,
                        "run_id": RUN_ID,
                        "actor": "executor",
                        "timestamp": "2026-08-22T10:00:09Z",
                        "parent": "",
                        "prev_hash": "0" * 64,
                        "step": "S-02",
                        "state": "performed",
                        "attempt": 1,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )

    def _cli(self, *argv: str) -> "tuple[int, str]":
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    def test_a_recorded_attempt_is_durable_in_the_ledger(self) -> None:
        """Kept separate: asserts a DURABLE EFFECT read back through a fresh engine, not an exit code.

        The table's `record performed` row proves the command exits 0. This proves the append
        actually happened, by reconstructing the step's state from the ledger with an engine that
        shares no memory with the CLI process. That is a different claim over a different object,
        and a table row cannot make it without carrying an unused engine for every other row.
        """
        self._seed_incomplete()
        rc, _ = self._cli(
            "run",
            "record",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--step",
            "S-01",
            "--state",
            "performed",
        )
        self.assertEqual(rc, run_cli.EXIT_OK)
        eng = run_engine.RunEngine(_WORKFLOW, self._store(), run_id=RUN_ID)
        self.assertEqual(
            eng.step_state("S-01"),
            "performed",
            "the CLI exited 0 but a fresh engine over the same ledger does not see the attempt, so "
            "the append was not durable",
        )

    def test_resume_cli_reports_unknown_outcome_condition(self) -> None:
        """Kept separate: the only CLI test with PATCHED COLLABORATORS, which no table row has.

        The resume CLI surfaces the UNKNOWN_OUTCOME sentinel when a side effect is interrupted. The
        `running` state is EPHEMERAL and not persisted, so no ledger a table row could seed produces
        this condition in a fresh CLI process; reaching the branch at all requires patching
        `detect_unknown_outcomes` and `resume`. Folding that into the invocation table would mean
        every other row carrying patches it must not apply.
        """
        self._seed_incomplete()

        # Force the interrupted-side-effect branch: patch detection + resume to raise as if a step
        # were left running mid-flight (running state is ephemeral and not persisted across procs).
        def _fake_detect(_engine: Any) -> "tuple[str, ...]":
            return ("S-01",)

        def _fake_resume(_engine: Any) -> Any:
            raise run_recovery.UnknownOutcomeError("S-01")

        with (
            patch.object(run_recovery, "detect_unknown_outcomes", _fake_detect),
            patch.object(run_recovery, "resume", _fake_resume),
        ):
            rc, out = self._cli(
                "runs",
                "resume",
                str(self.ledger),
                "--workflow",
                self._workflow_file(),
                "--json",
            )
        self.assertEqual(rc, run_cli.EXIT_BLOCKED)
        data = json.loads(out)
        self.assertEqual(data["condition"], run_recovery.UNKNOWN_OUTCOME)
        self.assertIn("S-01", data["unknown_outcome_steps"])

    def test_resume_refuses_unknown_outcome(self) -> None:
        """Kept separate: an `assertRaises` at the RECOVERY layer, not a CLI invocation at all.

        The comment below records why this cannot be a CLI test: `running` is ephemeral, so the
        condition is only observable in-process. It lives in this class because it is the in-process
        counterpart of the patched CLI test above, and the two together are what show the sentinel is
        real rather than only mocked.
        """
        store = self._store()
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        # persist a running side-effect marker so a fresh CLI process detects it: the ledger has a
        # step_attempt only if recorded; to make it visible we record a running via a torn state is
        # not possible, so we assert the detection at the recovery layer through the in-process ledger
        # by recording NO terminal attempt. The CLI reconstructs S-01 as pending (running is
        # ephemeral), so unknown_outcome is only observable in-process; assert that path directly.
        self.assertEqual(run_recovery.detect_unknown_outcomes(eng), ("S-01",))
        with self.assertRaises(run_recovery.UnknownOutcomeError):
            run_recovery.resume(eng)

    # ---- machine output is ANSI-free, PARSES, and carries its verdict, in both modes ---------------

    #: (read verb, expected exit code on a COMPLETE ledger, why this row exists)
    #:
    #: `status`, `next` and `resume` are READ verbs, so they live under `aw runs` after the
    #: runnamecollapse `0soncw` split (`next`/`resume` only reconstruct state and report). The OUTPUT
    #: MODE is a column supplied by the loop (`--agent` one compact line, `--json` pretty
    #: multi-line), because the whole claim is that BOTH machine modes are consumable and carry the
    #: same verdict; a per-mode test would let one of them rot.
    #:
    #: EXIT CODES ARE ASSERTED, not just ANSI-absence. The three verbs deliberately reach three
    #: DIFFERENT classes on one and the same ledger, which is the property worth pinning: a machine
    #: polling these cannot act on a payload it cannot classify.
    MACHINE_READ_VERBS = (
        (
            "status",
            run_cli.EXIT_INCOMPLETE,
            "reports the run and exits INCOMPLETE (1): every step is not done, and `status` is "
            "honest about that rather than exiting 0 because the read itself succeeded",
        ),
        (
            "next",
            run_cli.EXIT_BLOCKED,
            "the SAME ledger yields BLOCKED (3) here, because S-01 is performed and S-02 is gated "
            "on a human approval, so there is nothing runnable. A driver polling `next` must be able "
            "to tell 'wait for a human' from 'the run is incomplete'",
        ),
        (
            "resume",
            run_cli.EXIT_OK,
            "and the SAME ledger yields OK (0) here, because the run is resumable: nothing is "
            "wrong. Three verbs, three classes, one file - which is what makes the codes meaningful "
            "rather than a synonym for 'the command ran'",
        ),
    )

    def test_both_machine_modes_are_parseable_ansi_free_and_carry_the_verdict(
        self,
    ) -> None:
        self._seed_complete()
        wrong = []
        for verb, expected_rc, why in self.MACHINE_READ_VERBS:
            for mode in ("--agent", "--json"):
                rc, out = self._cli("runs", verb, str(self.ledger), mode)
                problems = []
                if rc != expected_rc:
                    problems.append(
                        f"exit code expected {expected_rc} "
                        f"({TestRunCliSubcommands._exit_name(expected_rc)}), got {rc} "
                        f"({TestRunCliSubcommands._exit_name(rc)})"
                    )
                if "\x1b" in out:
                    problems.append(
                        "an ANSI escape leaked into machine-consumed output, so a consumer parsing "
                        "this gets control characters inside its payload"
                    )
                try:
                    parsed = _parse_machine(out)
                except ValueError as exc:
                    problems.append(
                        f"the payload did not parse as JSON ({exc}); got {out[:200]!r}"
                    )
                else:
                    if not isinstance(parsed, dict):
                        problems.append(
                            f"the payload is not a JSON object; got {parsed!r}"
                        )
                    elif parsed.get("run_id") != RUN_ID:
                        problems.append(
                            f"the payload's `run_id` is {parsed.get('run_id')!r}, expected "
                            f"{RUN_ID!r}; an agent keys off the FIELD, not the prose"
                        )
                if problems:
                    wrong.append(
                        f"  aw runs {verb} {mode}\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        cells = len(self.MACHINE_READ_VERBS) * 2
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {cells} (read verb x machine mode) cells produced unusable machine "
            "output. Read the grouping: one whole MODE column failing means that renderer changed "
            "(most likely a human-prose line being emitted into the machine stream); one whole VERB "
            "row failing means that verb's payload or class moved; every cell leaking ANSI means "
            "color detection stopped honoring the machine modes, which corrupts every consumer at "
            "once. FIX: a wrong EXIT CODE is the load-bearing failure here - the three verbs "
            "deliberately reach three different classes on ONE ledger, so two of them agreeing on "
            "the same code means the classes collapsed and a driver can no longer tell 'wait for a "
            f"human' from 'incomplete'.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# JSONL index rebuildable from the authoritative ledger
# ==================================================================================================


class TestRebuildableIndex(unittest.TestCase):
    """The runtime index is a REBUILDABLE PROJECTION of the ledger (append-only JSONL, no SQLite).

    ONE table replaces two tests. Both projected the same complete ledger and asserted one property
    of the result; they differed in whether the projection was taken IN MEMORY (`rebuild_index`) or
    THROUGH A FILE (`write_index`), and in which property each happened to check.

    Why the table beats the two. "Rebuildable projection" is a conjunction of properties, and the two
    tests split it arbitrarily: the in-memory one checked record kinds and seq contiguity while the
    file one checked line count and byte-stability, so neither checked the other's half and a
    projection that reordered records on the way to disk would have passed both. Every row here
    states ONE property and every property is checked in BOTH forms, which is what makes the file and
    the in-memory answer provably the same object.

    THE LEDGER STAYS AUTHORITATIVE is the claim under all of it: the index may be deleted and rebuilt
    at any time, so it must be a pure function of the ledger. That is why DETERMINISM (writing twice
    produces identical bytes) is a row rather than a footnote - a projection that varied between runs
    would make the index unrebuildable and put it in an operator's diffs on every invocation.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ledger = self.tmp / "run.jsonl"
        store = ledger_store.RunLedgerStore(self.ledger)
        for rec in _complete_run_records():
            store.append(rec)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    #: (case, a probe taking (rows read back from the FILE, rows from `rebuild_index`, the written
    #: path) and returning a problem string or None, why this row exists)
    PROJECTION_PROPERTIES = (
        (
            "the first row is the `run` record",
            lambda disk, mem, path: (
                None
                if mem and mem[0]["kind"] == "run"
                else f"the first projected kind is {(mem[0]['kind'] if mem else None)!r}, expected "
                "'run'"
            ),
            "a run's OPENING record must come first, because every later record is interpreted "
            "relative to it (the run id, the workflow digest, the head commit). A projection that "
            "reordered records would make the index unreadable in sequence",
        ),
        (
            "every record kind in the ledger survives the projection",
            lambda disk, mem, path: (
                None
                if {"run", "requirement_set", "step_attempt", "verifier_decision"}
                <= {r["kind"] for r in mem}
                else "the projection dropped kind(s) "
                f"{sorted({'run', 'requirement_set', 'step_attempt', 'verifier_decision'} - {r['kind'] for r in mem})!r}"
            ),
            "THE PROJECTION MUST LOSE NOTHING. `step_attempt` and `verifier_decision` are the two "
            "kinds that carry what was DONE and what was VERIFIED, so an index that filtered either "
            "would answer questions about a run with evidence silently missing",
        ),
        (
            "sequence numbers are contiguous from 0",
            lambda disk, mem, path: (
                None
                if [r["seq"] for r in mem] == list(range(len(mem)))
                else f"seqs are {[r['seq'] for r in mem]!r}, expected {list(range(len(mem)))!r}"
            ),
            "a GAP would mean a record was skipped and a REPEAT would mean one was counted twice, "
            "and either makes the index disagree with the ledger it projects. Contiguity from 0 is "
            "how a reader knows it has the whole run",
        ),
        (
            "the written file holds exactly one JSON object per projected row",
            lambda disk, mem, path: (
                None
                if len(disk) == len(mem)
                else f"the file has {len(disk)} line(s) but the projection has {len(mem)} row(s)"
            ),
            "JSONL, not a JSON array: the file must be line-addressable so a consumer can stream it "
            "without holding a whole run in memory. This row is also what proves the disk form and "
            "the in-memory form are the SAME projection rather than two similar ones",
        ),
        (
            "the written rows are byte-parseable and carry the same kinds in the same order",
            lambda disk, mem, path: (
                None
                if [r["kind"] for r in disk] == [r["kind"] for r in mem]
                else f"the file's kinds {[r['kind'] for r in disk]!r} differ from the projection's "
                f"{[r['kind'] for r in mem]!r}"
            ),
            "ORDER is part of the contract, not an accident of iteration: the two tests this table "
            "replaced split kinds and line-count between them, so a projection that reordered "
            "records on the way to disk would have passed BOTH of them",
        ),
        (
            "writing twice produces identical bytes",
            lambda disk, mem, path: (
                None
                if _rewrite_is_byte_identical(path)
                else "re-running write_index produced DIFFERENT bytes, so the projection is not "
                "deterministic"
            ),
            "DETERMINISM IS WHAT MAKES THE INDEX DISPOSABLE: it may be deleted and rebuilt at any "
            "time, so a projection that varied between runs would put the index in an operator's "
            "diffs on every invocation and make 'rebuild it' an unsafe instruction",
        ),
    )

    def test_the_index_is_a_faithful_deterministic_projection_of_the_ledger(
        self,
    ) -> None:
        index_path = self.tmp / "index.jsonl"
        written = run_cli.write_index(self.ledger, index_path)
        self.assertTrue(
            written.is_file(),
            f"write_index reported {written!r} but no file exists there, so no row below can be "
            "evaluated",
        )
        mem = run_cli.rebuild_index(self.ledger)
        disk = [
            json.loads(line)
            for line in written.read_text(encoding="utf-8").strip().splitlines()
        ]
        wrong = []
        for case, probe, why in self.PROJECTION_PROPERTIES:
            problem = probe(disk, mem, written)
            if problem:
                wrong.append(
                    f"  {case}\n    - {problem}\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the index projection violates {len(wrong)} of {len(self.PROJECTION_PROPERTIES)} "
            "properties. THE LEDGER IS AUTHORITATIVE and the index is a disposable function of it, "
            "so read the grouping: the ORDER and CONTIGUITY rows failing together means the "
            "projection's iteration changed, and a DROPPED KIND is the severe case because the "
            "index then answers questions about a run with evidence silently missing. FIX: if only "
            "the DETERMINISM row fails, the projection has acquired a timestamp, a set iteration or "
            "some other nondeterminism - the index still reads correctly today but can no longer be "
            f"rebuilt without showing up as a spurious change.\n" + "\n".join(wrong),
        )


class TestLedgerResolutionAndWrongFormatVerdict(unittest.TestCase):
    """`e6b9kt`: the ledger must not claim `events.jsonl`, and wrong-format is not corruption.

    Before this fix, `aw run show <any-real-run-id>` resolved to the driver's own `events.jsonl` and
    printed `ledger corruption detected` with eight RL-E010 findings about a perfectly healthy file.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.run_id = RUN_ID
        self.run_dir = self.tmp / ".aw" / "records" / "runs" / self.run_id
        self.run_dir.mkdir(parents=True)
        # The RUNNER's own event log: healthy, and NOT a ledger.
        (self.run_dir / "events.jsonl").write_text(
            json.dumps({"at": "2026-08-24T14:01:12Z", "event": "run_start", "queue": 3})
            + "\n",
            encoding="utf-8",
        )
        # THE `state.json` IS REQUIRED FOR THIS TO BE A DRIVER RUN AT ALL (`d91i3e` E-06), and this
        # fixture went without one until the driver-run signpost was added. The reason is not
        # cosmetic: `run_viewer.repair_run` refuses a directory that has no `state.json` with
        # `not a run directory` at exit 2, so the refusal's detector deliberately declines to suggest
        # `aw runs repair` for one. Written against the events-only shape, the driver-run rows below
        # would have demanded a suggestion the detector must NOT make, and the only ways to make them
        # pass would have been to weaken the detector into suggesting a command that then fails.
        # The events-only directory is kept as its own row instead (see `ABSENT_LEDGER_TARGETS`).
        #
        # The root is `.aw/records/runs/`, which BOTH resolvers search, so this fixture does not sit
        # on the divergence axis between them. Do NOT "simplify" it to `.aw/state/runs/`: the ledger
        # reader searches there and `discover_run_dirs` does not, so `repair` could not see it.
        (self.run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": self.run_id,
                    "selectors": ["demo"],
                    "queue": [{"position": 1, "id6": "item01", "status": "executed"}],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        # A driver run the VIEWER'S resolver cannot see: the ledger reader searches
        # `.aw/state/runs/` but `discover_run_dirs` does not, so `aw runs repair` answers
        # `no run matched target` here. Seeded once so the "declines to suggest" row can use it.
        self.invisible_run_id = "run-20260824T140112Z-999999"
        self.invisible_dir = self.tmp / ".aw" / "state" / "runs" / self.invisible_run_id
        self.invisible_dir.mkdir(parents=True)
        (self.invisible_dir / "state.json").write_text(
            json.dumps({"run_id": self.invisible_run_id}) + "\n", encoding="utf-8"
        )
        (self.invisible_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
        # A directory holding ONLY an event log: resolvable by NAME, but refused by `repair_run`.
        self.stateless_run_id = "run-20260824T140112Z-888888"
        self.stateless_dir = (
            self.tmp / ".aw" / "records" / "runs" / self.stateless_run_id
        )
        self.stateless_dir.mkdir(parents=True)
        (self.stateless_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cli(self, *argv: str) -> "tuple[int, str]":
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    # ---- resolution ---------------------------------------------------------------------------

    #: (case, the target to resolve, what to seed first, expected resolution, why this row exists)
    #:
    #: `expect` is a CHECK-MODE column rather than one value, because the three old tests made
    #: DIFFERENT KINDS of claim about the resolver: one that it returns NOTHING, two that it returns
    #: a SPECIFIC path. Collapsing those into one comparison would have meant weakening the
    #: must-not-resolve row to something like "not the event log", which a resolver returning any
    #: other wrong path would satisfy.
    #:   ("none",)             resolution must be None
    #:   ("path", attribute)   resolution must equal that seeded path, RESOLVED
    RESOLUTIONS = (
        (
            "a bare run id when the directory holds only the driver's event log",
            "run-id",
            "nothing",
            ("none",),
            "e6b9kt, THE ORIGINAL BUG: a bare run id resolved to `events.jsonl`, a file the ledger "
            "does not own, and the caller then reported eight findings of corruption about a "
            "perfectly healthy log. Resolving to NOTHING is the correct answer, because there is "
            "no ledger here",
        ),
        (
            "a bare run id when a real ledger exists beside the event log",
            "run-id",
            "ledger",
            ("path", "ledger"),
            "POSITIVE, and what keeps the row above honest: a resolver that returned None "
            "unconditionally would satisfy it while making `aw runs show <id>` useless. The event "
            "log is STILL PRESENT in this row, so the resolver must pick the ledger over it rather "
            "than merely finding the only file in the directory",
        ),
        (
            "an explicit path to a file that is not a ledger at all",
            "explicit",
            "odd-file",
            ("path", "odd"),
            "an operator naming a file VERBATIM keeps working; the resolver's job is to find a "
            "path, not to judge it. The shape check downstream is what returns the wrong-format "
            "verdict, which is why this row expects the odd file back rather than None",
        ),
    )

    def test_every_target_resolves_to_the_path_it_should(self) -> None:
        """One table over ledger-path resolution, replacing three tests.

        Each of the three seeded a run directory, called `resolve_ledger_path` once, and asserted
        one thing about the result. The table beats the three because resolution is ONE lookup with
        a precedence order (an explicit path wins; otherwise a run id finds `ledger.jsonl` and
        nothing else), and the bug it exists to prevent (e6b9kt) was that order picking up a file it
        does not own. Seeing all three answers together is what shows whether the precedence moved
        or a single case broke.
        """
        wrong = []
        for case, target_kind, seed, expect, why in self.RESOLUTIONS:
            paths = {}
            if seed == "ledger":
                ledger = self.run_dir / ledger_store.LEDGER_FILENAME
                ledger_store.RunLedgerStore(ledger).append(_run_record())
                paths["ledger"] = ledger
            elif seed == "odd-file":
                odd = self.tmp / "somewhere-else.jsonl"
                odd.write_text("{}\n", encoding="utf-8")
                paths["odd"] = odd
            target = (
                self.run_id
                if target_kind == "run-id"
                else str(paths[next(iter(paths))])
            )
            resolved = run_cli.resolve_ledger_path(target, self.tmp)
            if expect[0] == "none":
                if resolved is not None:
                    wrong.append(
                        f"  {case}: expected NO resolution, got {str(resolved)!r}\n"
                        f"    this row exists because: {why}"
                    )
            else:
                expected = paths[expect[1]].resolve()
                if resolved != expected:
                    wrong.append(
                        f"  {case}:\n    expected {str(expected)!r}\n"
                        f"    got      {str(resolved)!r}\n"
                        f"    this row exists because: {why}"
                    )
            # Each row gets a clean directory so a seeded ledger cannot leak into the next row.
            for made in paths.values():
                made.unlink()
        self.assertEqual(
            wrong,
            [],
            f"run_cli.resolve_ledger_path resolved {len(wrong)} of {len(self.RESOLUTIONS)} targets "
            "wrongly. One lookup with one precedence order produces all three answers, so several "
            "rows failing together means that order changed rather than three independent bugs. "
            "FIX: if the FIRST row now resolves to something, check WHAT it resolved to. Resolving "
            "to `events.jsonl` is e6b9kt returning, and the caller will then report a healthy "
            "driver log as a corrupted ledger, which is the exact user-visible symptom this whole "
            "class was written for. If the POSITIVE row is the one failing, `aw runs show <run-id>` "
            f"can no longer find a real ledger at all.\n" + "\n".join(wrong),
        )

    # ---- the verdict --------------------------------------------------------------------------

    #: (case, target, extra argv, expected exit code, checks, why this row exists)
    #:
    #: `target` is the ledger argument: "event-log" (a healthy driver log), "run-id" (a bare id
    #: resolving to nothing), "tampered" (a real ledger with a broken hash chain) or "healthy" (a
    #: real, complete ledger). The SUBCOMMAND and the OUTPUT MODE are columns of `verb`/`extra`, not
    #: reasons for separate tables: the whole claim is that one shape check produces one verdict
    #: everywhere, so rows must sit side by side to express it.
    VERDICTS = (
        # ---- the wrong-format verdict, across the four verbs that read a ledger ----------------
        (
            "show on the driver's event log",
            "show",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (
                ("itext-in", "not a run ledger"),
                ("itext-not-in", "corrupt"),
            ),
            "e6b9kt: a healthy `events.jsonl` is the WRONG FORMAT (7), not corruption (5). It must "
            "say `not a run ledger` and must NOT use the word corrupt at all, because telling a "
            "user their log is corrupted sends them hunting for tampering that never happened",
        ),
        (
            "verify-ledger on the driver's event log",
            "verify-ledger",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (("itext-not-in", "corrupt"),),
            "the verb whose ENTIRE JOB is judging integrity is the one most likely to call a "
            "wrong-format file corrupt, so it needs its own row",
        ),
        (
            "evidence on the driver's event log",
            "evidence",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (("itext-not-in", "corrupt"),),
            "the evidence reader shares the shape check rather than carrying its own copy",
        ),
        (
            "status on the driver's event log",
            "status",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (("itext-not-in", "corrupt"),),
            "the MUTATING family reaches the same verdict through `_build_engine`, which is a "
            "different code path from the read verbs above; without this row the check could be "
            "installed on only half the CLI",
        ),
        (
            "show --agent on the driver's event log",
            "show",
            "event-log",
            ("--agent",),
            run_cli.EXIT_NOT_A_LEDGER,
            (
                ("json-eq", "not_a_ledger", True),
                ("json-eq", "corrupted", False),
                ("json-eq", "exit_code", run_cli.EXIT_NOT_A_LEDGER),
            ),
            "MODE COLUMN, and the load-bearing half: an agent reads the KEYS, so the payload must "
            "both assert the wrong format AND explicitly DENY corruption. `corrupted: false` is a "
            "positive claim, not an omission, so a consumer cannot default it to true",
        ),
        (
            "show on a bare run id with no ledger anywhere",
            "show",
            "run-id",
            (),
            run_cli.EXIT_INVALID_INVOCATION,
            (("itext-not-in", "corruption"),),
            "A THIRD DISTINCT VERDICT: nothing was found, so this is an invocation error (2), not "
            "wrong-format (7) and not corruption (5). Reporting corruption for a file that was "
            "never even opened is the original e6b9kt symptom",
        ),
        # ---- ADVERSARIAL: real corruption must still be reported as corruption -----------------
        (
            "show on a ledger whose hash chain was tampered with",
            "show",
            "tampered",
            (),
            run_cli.EXIT_INVALID_INVOCATION,
            (("itext-in", "corruption"),),
            "THE ADVERSARIAL ROW: the wrong-format path must not become a blanket excuse. A "
            "tampered ledger must still be NAMED as corruption, or the fix for a cosmetic "
            "misdiagnosis would have silenced the one verdict that matters. MEASURED, NOT ASSUMED: "
            "`runs show` reports corruption with exit 2 (`run_cli.py:295-308` hard-codes it) while "
            "`run finalize` uses EXIT_CORRUPTED_LEDGER (5) for the same condition. That asymmetry "
            "is pinned here rather than wished away; if it is ever unified, THIS row is the one to "
            "update, and the prose claim below it is what must not weaken",
        ),
        (
            "show --agent on a tampered ledger",
            "show",
            "tampered",
            ("--agent",),
            run_cli.EXIT_INVALID_INVOCATION,
            (
                ("json-eq", "corrupted", True),
                ("json-eq", "ok", False),
            ),
            "THE MACHINE HALF OF THE ADVERSARIAL ROW, and the load-bearing one given the exit-code "
            "asymmetry noted above: whatever the code, the payload must say `corrupted: true`. This "
            "is the exact mirror of the event-log row's `corrupted: false`, so the two rows "
            "together prove the flag is a real signal rather than a constant in either direction",
        ),
        # ---- POSITIVE: a real, healthy ledger must pass all the same verbs ----------------------
        (
            "show on a real, complete ledger",
            "show",
            "healthy",
            (),
            run_cli.EXIT_OK,
            (("text-in", "Run:"),),
            "POSITIVE: every row above is vacuous against a CLI that refuses every file. This is "
            "the row that proves the shape check ACCEPTS a genuine ledger rather than rejecting "
            "everything and coincidentally satisfying the negative rows",
        ),
        (
            "verify-ledger --agent on a real, healthy ledger",
            "verify-ledger",
            "healthy",
            ("--agent",),
            run_cli.EXIT_OK,
            (
                ("json-eq", "chain_clean", True),
                ("json-eq", "ok", True),
            ),
            "POSITIVE in the machine mode: a clean chain is reported as clean. Paired with the "
            "tampered row, this is what makes `chain_clean` a real signal rather than a constant",
        ),
    )

    def test_every_verb_reaches_the_same_verdict_for_each_file_shape(self) -> None:
        """One table over the wrong-format verdict, replacing six tests and folding in two positives.

        Each of the six ran one subcommand against `events.jsonl` and asserted an exit code plus the
        absence of the word "corrupt". The SUBCOMMAND and the OUTPUT MODE were the only differences,
        so they are columns here.

        Why the table beats the six. The claim is not about any one verb: it is that ONE shape check
        produces ONE verdict across every verb that reads a ledger, including the mutating family
        that reaches it by a different path (`_build_engine`). Six tests can only assert that
        separately; the table asserts it as the pattern it is, and a failure that hits every verb at
        once reads as "the check moved" rather than as six coincidences.

        THREE DISTINCT VERDICTS ARE IN THE SAME TABLE ON PURPOSE (wrong format 7; a target that
        resolves to no file 2; real corruption, which `show` also reports as 2 but with
        `corrupted: true` and the word corruption in its prose) because the bug being guarded is
        precisely a CONFLATION of them. Asserting them apart is what lets the fix for the cosmetic
        misdiagnosis be checked against the adversarial rows that must keep firing.

        THE POSITIVE ROWS ARE NOT DECORATION: a shape check that rejected every file would satisfy
        all six original tests. Their failure message says so.
        """
        wrong = []
        for case, verb, target, extra, expected_rc, checks, why in self.VERDICTS:
            argv = ["runs", verb, *self._target_argv(target), *extra]
            rc, out = self._cli(*argv)
            problems = []
            if rc != expected_rc:
                problems.append(
                    f"exit code expected {expected_rc} "
                    f"({TestRunCliSubcommands._exit_name(expected_rc)}), got {rc} "
                    f"({TestRunCliSubcommands._exit_name(rc)})"
                )
            problems.extend(_stdout_problems(out, checks))
            if "\x1b[" in out:
                problems.append("ANSI escape leaked into machine-consumed output")
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the ledger-shape verdict is wrong for {len(wrong)} of {len(self.VERDICTS)} "
            "invocations. One shape check serves every verb here, so read the grouping. EVERY "
            "event-log row failing together means the check itself changed; ONE verb failing while "
            "its siblings pass means that verb stopped routing through the shared check (most "
            "likely `status`, which reaches it through `_build_engine` rather than directly). FIX: "
            "if the TAMPERED row is failing, stop and fix that first, whatever else is red: the "
            "wrong-format path has become a blanket excuse and real tamper evidence is now being "
            "swallowed at the CLI boundary, which is strictly worse than the cosmetic misdiagnosis "
            "this class was written to fix. If a POSITIVE row is failing, the check now rejects "
            "genuine ledgers and every negative row above is passing vacuously. A row that has the "
            "right exit code but leaks the word `corrupt` is the mild case: the machine verdict is "
            f"correct and only the human prose is misleading.\n" + "\n".join(wrong),
        )

    def _target_argv(self, target: str) -> "list[str]":
        """Build the ledger argument (and `--dir` where needed) for one `VERDICTS` target."""
        if target == "event-log":
            return [str(self.run_dir / "events.jsonl")]
        if target == "run-id":
            return [self.run_id, "--dir", str(self.tmp)]
        ledger = self.run_dir / f"{target}-ledger.jsonl"
        store = ledger_store.RunLedgerStore(ledger)
        if target == "tampered":
            store.append(_run_record())
            store.append(_requirement_set(["R-01"]))
            lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
            tampered = json.loads(lines[1])
            tampered["prev_hash"] = "f" * 64
            lines[1] = json.dumps(tampered, sort_keys=True) + "\n"
            ledger.write_text("".join(lines), encoding="utf-8")
        else:
            assert target == "healthy", f"unknown target {target!r}"
            for rec in _complete_run_records():
                store.append(rec)
        return [str(ledger)]

    # ---- the SIGNPOST on the not-found refusal (`d91i3e`) --------------------------------------
    #
    # These extend the class rather than starting a module because they assert about the SAME
    # refusal, on the SAME fixture, as the rows above: the not-found verdict (exit 2) that the
    # `e6b9kt` rows already distinguish from the wrong-format verdict (exit 7). Keeping them here is
    # what makes that fence visible, since the new text must NOT leak into the exit-7 class.

    #: Every leaf that emits the absent-ledger refusal, with the NOUN it lives under and whether it
    #: WRITES. Ten of them: three build the refusal at their own call site and seven reach it through
    #: `_resolve_or_error`. The direction column is not decoration: four of the ten MUTATE a ledger,
    #: so a message calling its own caller a reader would be false exactly there, which is the claim
    #: `test_the_signpost_wording_is_true_of_a_writer_too` pins.
    REFUSAL_LEAVES: "tuple[tuple[str, str, bool], ...]" = (
        ("runs", "show", False),
        ("runs", "status", False),
        ("runs", "verify-ledger", False),
        ("runs", "evidence", False),
        ("runs", "next", False),
        ("runs", "resume", False),
        ("run", "start", True),
        ("run", "record", True),
        ("run", "cancel", True),
        ("run", "finalize", True),
    )

    #: (case, the target attribute or literal, expect a repair suggestion, why this row exists)
    #:
    #: The whole claim is that the signpost appears EXACTLY when `aw runs repair <target>` would
    #: actually work, so each row's `expect_suggestion` is really a prediction about `repair`, and
    #: `test_the_signpost_agrees_with_what_repair_actually_does` checks it against `repair` itself
    #: rather than against this table's opinion.
    ABSENT_LEDGER_TARGETS: "tuple[tuple[str, str, bool, str], ...]" = (
        (
            "a driver run the viewer's resolver can see, holding state.json and events.jsonl",
            "run_id",
            True,
            "THE CASE THE WORK EXISTS FOR (backlog `sv8z1e`): an operator whose driver run crashed "
            "reaches for `aw runs resume <id>`, whose own --help promises exactly that situation, "
            "and was told only that a file was absent while the run sat plainly on disk. This row "
            "is what proves the dead end became a signpost",
        ),
        (
            "a target that resolves to nothing at all",
            "totalgibberish",
            False,
            "THE FAIL-CLOSED ROW: inventing a `repair` suggestion for a target that resolves to "
            "nothing would send the operator to a command that then answers `no run matched "
            "target`, which is worse than saying nothing, because it burns their trust in every "
            "other suggestion this surface makes. Today's honest message is CORRECT here",
        ),
        (
            "a driver run under .aw/state/runs/, where the viewer's resolver cannot see it",
            "invisible_run_id",
            False,
            "RESOLVER-DIVERGENCE AXIS (a): the ledger reader searches `.aw/state/runs/` and "
            "`discover_run_dirs` does not. A detector that probed the READER's own roots would "
            "suggest `repair` here and `repair` would then refuse, which is the precise trap this "
            "row exists to keep shut",
        ),
        (
            "a run directory holding events.jsonl but no state.json",
            "stateless_run_id",
            False,
            "RESOLVER-DIVERGENCE AXIS (b), and the reason resolving the target is not a sufficient "
            "test: the viewer's resolver DOES match this directory (by name), but `repair_run` "
            "refuses it with `not a run directory`. Only the extra state.json condition keeps the "
            "suggestion honest, so this row is what fails if that condition is dropped",
        ),
    )

    def _absent_target(self, spec: str) -> str:
        """Resolve one `ABSENT_LEDGER_TARGETS` spec to the literal CLI argument."""
        return getattr(self, spec, spec)

    def test_the_signpost_appears_exactly_when_repair_would_work(self) -> None:
        """One table: the driver-run signpost is offered for precisely the targets `repair` can act on.

        Accumulates rather than asserting per row because the realistic failure is directional and
        only legible across rows: a detector that is too EAGER fails the three negative rows
        together (it is suggesting a command that will refuse), while one that is too STRICT fails
        the single positive row alone (the dead end is back). Four independent red lines would not
        show which of those happened.
        """
        wrong = []
        for case, spec, expect_suggestion, why in self.ABSENT_LEDGER_TARGETS:
            target = self._absent_target(spec)
            rc, out = self._cli("runs", "resume", target, "--dir", str(self.tmp))
            problems = []
            if rc != run_cli.EXIT_INVALID_INVOCATION:
                problems.append(
                    f"exit {rc}, expected {run_cli.EXIT_INVALID_INVOCATION}; this plan changes "
                    "GUIDANCE, never the invocation contract"
                )
            suggested = "aw runs repair" in out
            if suggested != expect_suggestion:
                problems.append(
                    f"repair suggestion {'offered' if suggested else 'absent'}, expected "
                    f"{'offered' if expect_suggestion else 'absent'}"
                )
            # The three honest clauses survive in EVERY row: the signpost is an addition, and a
            # rewrite that dropped them would re-open `i1hlgx`.
            for needle in ("ledger.jsonl", "no driver run writes one", "events.jsonl"):
                if needle not in out:
                    problems.append(
                        f"lost the {needle!r} clause from the `i1hlgx` wording"
                    )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the driver-run signpost is wrong for {len(wrong)} of "
            f"{len(self.ABSENT_LEDGER_TARGETS)} targets. READ THE GROUPING: if every NEGATIVE row "
            "failed together the detector became too eager and is now naming `aw runs repair` for "
            "targets repair itself refuses, which is the fail-open direction and the worse one. If "
            "only the POSITIVE row failed, the signpost is gone and an operator pointing a ledger "
            "reader at a crashed driver run is back to a message that names no action at all, which "
            "is the defect backlog `sv8z1e` was filed for.\n" + "\n".join(wrong),
        )

    def test_the_signpost_agrees_with_what_repair_actually_does(self) -> None:
        """The prediction above is checked against `aw runs repair` itself, not against our opinion.

        Kept apart from the table because its claim is a CROSS-COMMAND agreement rather than a
        per-target expectation, and because it is the only thing standing between this work and its
        central risk: a suggestion that does not work. The two commands resolve targets through
        DIFFERENT code (the readers' `resolve_ledger_path` versus the viewer's `discover_run_dirs`),
        so agreement has to be measured. `repair` answering exit 0 means it acted or had nothing to
        do, which is a fine place to send an operator; any nonzero answer is a refusal, and a
        refusal is what we must never have suggested.
        """
        disagreements = []
        for case, spec, expect_suggestion, _why in self.ABSENT_LEDGER_TARGETS:
            target = self._absent_target(spec)
            _rc, refusal = self._cli("runs", "resume", target, "--dir", str(self.tmp))
            suggested = "aw runs repair" in refusal
            repair_rc, repair_out = self._cli(
                "runs", "repair", target, "--dir", str(self.tmp)
            )
            if suggested and repair_rc != 0:
                disagreements.append(
                    f"  {case}: we suggested `aw runs repair` but it exited {repair_rc}: "
                    f"{repair_out.strip()[:200]!r}"
                )
            if not suggested and repair_rc == 0:
                disagreements.append(
                    f"  {case}: `aw runs repair` WORKS here (exit 0) but we did not offer it: "
                    f"{repair_out.strip()[:200]!r}"
                )
            if suggested != expect_suggestion:
                disagreements.append(
                    f"  {case}: table predicts suggestion={expect_suggestion}, got {suggested}"
                )
        self.assertEqual(
            disagreements,
            [],
            "the refusal's suggestion and `aw runs repair`'s real behaviour disagree. A suggestion "
            "that REFUSES is the failure this whole change exists to avoid: the operator followed "
            "our advice and got a second dead end. FIX: make the detector ask the viewer's own "
            "resolver (`resolve_target_runs_detailed`) and additionally require the `state.json` "
            "that `repair_run` requires; do NOT re-derive repair's resolution rules, which is what "
            "produces exactly this divergence.\n" + "\n".join(disagreements),
        )

    def test_every_one_of_the_ten_leaves_carries_the_signpost(self) -> None:
        """All ten leaves that refuse, in both nouns, name the action; nine cannot be left behind.

        Apart from the target table because the axis is the LEAF rather than the target: the refusal
        was emitted from four call sites and a per-leaf fix would have left copies of the dead end
        behind. This is the row-per-leaf proof that the consolidation reached all of them.
        """
        problems = []
        for noun, leaf, _writes in self.REFUSAL_LEAVES:
            rc, out = self._cli(noun, leaf, self.run_id, "--dir", str(self.tmp))
            if rc != run_cli.EXIT_INVALID_INVOCATION:
                problems.append(
                    f"aw {noun} {leaf}: exit {rc}, expected "
                    f"{run_cli.EXIT_INVALID_INVOCATION} (returned value, no pipeline)"
                )
            if "aw runs repair" not in out:
                problems.append(
                    f"aw {noun} {leaf}: no repair suggestion in {out[:200]!r}"
                )
            if "aw runs " + self.run_id not in out:
                problems.append(
                    f"aw {noun} {leaf}: no READ suggestion; an operator who was just refused "
                    "usually wants to SEE the run, and `repair` mutates"
                )
        self.assertEqual(
            [],
            problems,
            "a leaf that refuses without naming the action is the dead end this change removes. "
            "All ten route through one emitter, so ONE leaf failing alone means it stopped using "
            "it.\n" + "\n".join(problems),
        )

    def test_the_signpost_wording_is_true_of_a_writer_too(self) -> None:
        """The shared sentence must not call its caller a reader: four of the ten leaves WRITE.

        Apart from the ten-leaf table because the claim is about TRUTHFULNESS rather than presence.
        The obvious phrasing for this refusal ("these readers serve a different run model") is false
        exactly where it is printed by `aw run start|record|cancel|finalize`, and a refusal an
        operator catches in a lie is worse than the vague one it replaced. The fix is to name the RUN
        MODEL rather than the leaf's direction, so this asserts the prohibition directly.
        """
        for noun, leaf, writes in self.REFUSAL_LEAVES:
            if not writes:
                continue
            with self.subTest(leaf=f"aw {noun} {leaf}"):
                _rc, out = self._cli(noun, leaf, self.run_id, "--dir", str(self.tmp))
                lowered = out.lower()
                for forbidden in ("these readers", "this reader", "read-only command"):
                    self.assertNotIn(
                        forbidden,
                        lowered,
                        f"aw {noun} {leaf} WRITES a ledger, so calling itself {forbidden!r} is "
                        "false about the very leaf that printed it",
                    )
                self.assertIn(
                    "ledger run model",
                    lowered,
                    "the sentence must name the RUN MODEL, which is true in both directions, "
                    "rather than the leaf's direction, which is not",
                )

    def test_no_renderer_leaks_an_absolute_path_into_the_suggestion(self) -> None:
        """The most-copied output on this surface must not carry a home directory (D92).

        Apart from everything else because it is a LEAK check, not a behaviour check. The detector
        legitimately knows an absolute run directory (it had to find one to classify the target),
        and printing it is the obvious way to make the suggestion unambiguous - which is exactly the
        trap, since this refusal is what an operator pastes into an issue. `agent_schema` looks for
        precisely a `/home/` segment, so that is what is asserted.
        """
        for extra in ((), ("--agent",), ("--json",)):
            with self.subTest(renderer=extra or ("human",)):
                _rc, out = self._cli(
                    "runs", "resume", self.run_id, "--dir", str(self.tmp), *extra
                )
                self.assertIn("aw runs repair", out, "precondition: signpost present")
                self.assertNotIn(
                    str(self.tmp),
                    out,
                    "the resolved run directory must never be printed; suggest the target as the "
                    "operator spelled it",
                )
                self.assertNotIn(
                    "/home/",
                    out,
                    "a home-directory segment in the most-pasted output on this surface is the "
                    "leak `aw sanitize` exists to catch",
                )

    def test_both_machine_renderers_carry_the_suggestion_as_data(self) -> None:
        """An agent consumer reads a FIELD, never an English sentence, and the keys EXTEND the shape.

        Apart from the human assertions because the contract is structural. A human-only signpost
        leaves the gap exactly where it does most damage: an automated consumer cannot parse prose at
        all, so it would still see only a bare failure. The `exit_code` is checked against the
        RETURNED code so the payload cannot claim one thing while the process does another.

        DELIBERATELY NOT an `aw.agent/v1` conformance check: these payloads are bare dicts and are
        not records of that schema, which is a real gap on a different contract and not this one. So
        this asserts the EXISTING keys survive and the new ones are additions.
        """
        for extra in ("--agent", "--json"):
            with self.subTest(renderer=extra):
                rc, out = self._cli(
                    "runs", "resume", self.run_id, "--dir", str(self.tmp), extra
                )
                payload = json.loads(
                    out.strip().splitlines()[-1] if extra == "--agent" else out
                )
                self.assertEqual(run_cli.EXIT_INVALID_INVOCATION, rc)
                self.assertEqual(
                    rc,
                    payload["exit_code"],
                    "the payload's exit_code must equal the code the process actually returned",
                )
                self.assertIs(False, payload["ok"])
                self.assertEqual("driver-run", payload["target_kind"])
                self.assertEqual(
                    [
                        f"aw runs {self.run_id}",
                        f"aw runs repair {self.run_id}",
                    ],
                    payload["suggested_commands"],
                    "the READ comes first: an operator who was just refused usually wants to SEE "
                    "the run, and `repair` mutates",
                )
                self.assertLessEqual(
                    {"ok", "error", "exit_code"},
                    set(payload),
                    "the pre-existing payload shape is EXTENDED, never replaced: consumers key off "
                    "these three today",
                )
                self.assertNotIn(
                    "\x1b[", out, "machine streams are documented ANSI-free"
                )

    def test_an_unknown_target_keeps_the_bare_machine_shape(self) -> None:
        """The negative half of the payload claim: no suggestion means no suggestion KEYS either.

        Separate because it is what keeps the new fields from becoming unconditional noise. A
        consumer testing `if "suggested_commands" in payload` must be able to trust the absence, so
        the keys appear only when there is genuinely something to suggest.
        """
        rc, out = self._cli(
            "runs", "resume", "totalgibberish", "--dir", str(self.tmp), "--agent"
        )
        payload = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(run_cli.EXIT_INVALID_INVOCATION, rc)
        self.assertEqual(
            {"ok", "error", "exit_code"},
            set(payload),
            "an unresolvable target's payload must stay exactly as it was: adding empty suggestion "
            "keys would make their presence meaningless as a signal",
        )
        self.assertNotIn("aw runs repair", payload["error"])

    def test_the_three_way_classification_names_all_three_answers(self) -> None:
        """The detector returns one of three answers, not a bool, and a ledger run is one of them.

        Apart from the CLI tables because it addresses the helper directly: a two-valued answer
        would have to push the UNKNOWN case into one of the other arms, and the arm it would land in
        (driver run) is the one that emits a command. That is how a boolean turns into a suggestion
        for a target that does not exist.
        """
        self.assertEqual(
            run_cli.TARGET_DRIVER_RUN,
            run_cli._classify_absent_target(self.run_id, str(self.tmp)),
        )
        self.assertEqual(
            run_cli.TARGET_UNKNOWN,
            run_cli._classify_absent_target("totalgibberish", str(self.tmp)),
        )
        # A LEDGER run is the caller's OWN answer: `resolve_ledger_path` returning a path IS that
        # verdict, so the third value exists as a named constant the message builder branches on
        # rather than as a case this detector is ever asked.
        ledger = self.run_dir / ledger_store.LEDGER_FILENAME
        ledger_store.RunLedgerStore(ledger).append(_run_record())
        self.assertIsNotNone(run_cli.resolve_ledger_path(self.run_id, self.tmp))
        self.assertEqual(
            3,
            len(
                {
                    run_cli.TARGET_LEDGER_RUN,
                    run_cli.TARGET_DRIVER_RUN,
                    run_cli.TARGET_UNKNOWN,
                }
            ),
            "three distinct answers, so no case has to be folded into another",
        )

    def test_classifying_a_target_never_hands_the_event_log_to_a_ledger_parser(
        self,
    ) -> None:
        """The `e6b9kt` guarantee survives the detector: it may CLASSIFY, never parse (`d91i3e` E-05).

        Apart from the resolution table because the claim is about what the NEW code may not do. The
        detector reads a driver run directory on purpose, which is one short step from handing its
        `events.jsonl` to the ledger reader and resurrecting the bug that reported a healthy driver
        log as corrupt. So this pins both halves: the resolver still refuses the event log for a
        bare id, and the refusal that follows still never says corrupt.
        """
        self.assertIsNone(
            run_cli.resolve_ledger_path(self.run_id, self.tmp),
            "a bare run id must STILL resolve to no ledger even though a driver run is there; "
            "resolving to `events.jsonl` is e6b9kt returning",
        )
        rc, out = self._cli("runs", "show", self.run_id, "--dir", str(self.tmp))
        self.assertEqual(run_cli.EXIT_INVALID_INVOCATION, rc)
        self.assertNotIn("corrupt", out.lower())


if __name__ == "__main__":
    unittest.main()
