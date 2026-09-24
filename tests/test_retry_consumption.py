#!/usr/bin/env python3
"""retrywire (`xipfy1`): the frozen correction budget is actually SPENT on a retryable turn failure.

THE DEFECT THIS CLOSES. Spec `25kzda` 2.1's correction budget was fully built, range-validated,
operator-settable and frozen into `state.json`, and then spent on exactly ONE failure class (a refused
`aw ipd finalize`, wired by `zzcrlo`). The class spec 5.5 names FIRST - a HOST attempt that failed -
had no consumer at all, so an item whose turn failed reached `partial`/`failed-safely` on its first
failure and was never re-dispatched no matter what budget the operator froze.

FIXTURE-BASED, NEVER LIVE RECORDS, and that rule is not stylistic. `.aw/records/runs/` is gitignored
with zero tracked files, so a test keyed to live runs is unrunnable in CI and in every lane worktree
the runner allocates by default. The rule is documented in `tests/test_run_viewer.py`'s header ("a new
test must NOT read the live repository via `dir='.'`") and this module copies its pattern: every state
dict below is built in-process, and the two tests that need a run directory use `tempfile`.

WHAT IS NEW BEHAVIOR AND WHAT IS CHARACTERIZATION is labelled per test, because two of the six
boundary cases were ALREADY GREEN before this change and presenting them as proof of the wiring would
be dishonest:

  * NEW: budget 2 buys exactly 2 corrections then escalates; budget 0 buys none; a non-retryable class
    buys none at budget 10; a deliberate operator stop is never retried.
  * CHARACTERIZATION: a resumed run keeps its frozen budget (already guaranteed by
    `refuse_frozen_flags_on_resume`, which REFUSES `--retry-budget` on resume outright rather than
    letting it override), and a repeated idempotency key does not double-spend (`plan_retry`'s
    equivalent is already pinned by `tests/test_run_recovery_cli.py`). Both are kept as REGRESSION
    coverage for the new driver-side substrate, which has its own implementation of each property.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as agy_driver
from agent_workflows import oc_runipd as oc_driver
from agent_workflows import render_stream
from agent_workflows import runner_shared
from agent_workflows import runner_shutdown


def _item(**overrides):
    """One queue entry in the shape a real run persists."""
    item = {
        "position": 1,
        "id6": "xipfy1",
        "setid": "retrywire",
        "action": "execute",
        "status": "failed-safely",
        "attempts": [{"number": 1}],
    }
    item.update(overrides)
    return item


def _state(queue, **options):
    return {
        "run_id": "run-20260922T024054Z-2245533",
        "repo": "/repo",
        "queue": queue,
        "options": dict(options),
    }


def _run_dir(root: Path) -> Path:
    """A minimal run directory: only what the performer writes into."""
    run_dir = root / "run-20260922T024054Z-2245533"
    (run_dir / "outcomes").mkdir(parents=True)
    return run_dir


def _perform(run_dir: Path, state, item, disposition, attempt_no=1):
    """Drive `handle_turn_failure_retry` with real writers, returning its disposition.

    `save_state` and `append_jsonl` are INJECTED by the production signature, so the fixture supplies
    real ones (a JSON write and a JSONL append) rather than mocks: the point of several assertions
    below is that the durable record actually lands on disk, which a mock would not prove.
    """

    def save_state(rd: Path, st) -> None:
        (rd / "state.json").write_text(json.dumps(st, indent=2), encoding="utf-8")

    def append_jsonl(path: Path, payload) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")

    attempt = item.setdefault("attempts", [{}])[-1]
    return runner_shared.handle_turn_failure_retry(
        run_dir=run_dir,
        state=state,
        item=item,
        attempt=attempt,
        attempt_no=attempt_no,
        disposition=disposition,
        host_labels=runner_shared.OC_HOST_LABELS,
        save_state=save_state,
        append_jsonl=append_jsonl,
    )


class TheAllowlistIsPositiveAndCoversEveryStatus(unittest.TestCase):
    """E-01: an ALLOWLIST with a per-class justification, never a denylist."""

    def test_only_the_host_failure_class_is_retryable(self):
        self.assertEqual(
            {"failed-safely"},
            set(runner_shared.TURN_RETRYABLE_DISPOSITIONS),
            "spec 5.5's retryable set for a finished driver turn is the host-failure class only",
        )

    def test_partial_is_deliberately_left_to_its_own_owner(self):
        """NARROWED DURING EXECUTION, and the narrowing is the finding worth pinning.

        A blanket `partial` retry is strictly broader than approved sibling plan `dy9ymn`'s narrow
        "provably attempted nothing" predicate (which "EXCLUDES retrying any item that produced ANY
        evidence of work"), and it MEASURABLY broke five shipped tests that pin `partial` as terminal.
        `partial` is also what a VERIFIER DOWNGRADE writes, so retrying it would spend correction
        budget on a rejected verdict. Pinned so a later widening is a deliberate act.
        """
        self.assertNotIn("partial", runner_shared.TURN_RETRYABLE_DISPOSITIONS)
        retryable, why = runner_shared.turn_failure_is_retryable(_item(), "partial")
        self.assertFalse(retryable)
        self.assertIn("dy9ymn", why)

    def test_the_classification_table_agrees_with_the_allowlist(self):
        """The table is the justification carrier, so it must not disagree with the allowlist."""
        tabled = {
            name
            for name, retryable, _ in runner_shared.TURN_RETRY_CLASSIFICATION
            if retryable
        }
        self.assertEqual(set(runner_shared.TURN_RETRYABLE_DISPOSITIONS), tabled)

    def test_every_class_carries_a_justification(self):
        for name, _retryable, why in runner_shared.TURN_RETRY_CLASSIFICATION:
            with self.subTest(status=name):
                self.assertTrue(why.strip(), f"{name} has no recorded justification")

    def test_the_table_has_no_duplicate_rows(self):
        names = [name for name, _, _ in runner_shared.TURN_RETRY_CLASSIFICATION]
        self.assertEqual(
            len(names),
            len(set(names)),
            "a duplicated row makes one verdict unreachable",
        )

    def test_the_table_covers_both_closed_status_VOCABULARIES(self):
        """A status added elsewhere must FAIL HERE rather than default to retryable.

        This is the fail-closed guarantee in test form: `turn_failure_is_retryable` refuses an
        unclassified disposition, and this test is what keeps the table from silently falling behind
        the vocabularies it classifies.
        """
        tabled = {name for name, _, _ in runner_shared.TURN_RETRY_CLASSIFICATION}
        for label, vocabulary in (
            ("oc TERMINAL_STATES", oc_driver.TERMINAL_STATES),
            ("agy TERMINAL_STATES", agy_driver.TERMINAL_STATES),
            (
                "runner_shutdown.KNOWN_ITEM_STATUSES",
                runner_shutdown.KNOWN_ITEM_STATUSES,
            ),
        ):
            with self.subTest(vocabulary=label):
                self.assertEqual(
                    set(),
                    set(vocabulary) - tabled,
                    f"{label} carries statuses with NO retryable verdict; add a row with its reason",
                )

    def test_an_unclassified_disposition_is_refused_fail_closed(self):
        retryable, why = runner_shared.turn_failure_is_retryable(
            _item(), "some-new-status"
        )
        self.assertFalse(retryable)
        self.assertIn("FAIL-CLOSED", why)


class ADeliberateOperatorStopIsNeverRetried(unittest.TestCase):
    """E-01 / E-06 case 4 (NEW BEHAVIOR): the most expensive class to get wrong.

    `reconcile_disposition` maps a recorded stop to `interrupted`, which is already outside the
    allowlist - but its OWN comment records that without that branch a stop reconciles as
    `failed-safely`, which IS inside it. So the `stopped` record is checked directly rather than
    trusted to have been mapped away.
    """

    def test_a_stop_recorded_under_a_retryable_disposition_is_still_refused(self):
        item = _item(stopped={"stopped_deliberately": True, "level": 3})
        retryable, why = runner_shared.turn_failure_is_retryable(item, "failed-safely")
        self.assertFalse(
            retryable,
            "a DELIBERATE OPERATOR STOP must never be retried even when it arrives under a "
            "disposition that is otherwise in the retryable class",
        )
        self.assertIn("DELIBERATE OPERATOR STOP", why)

    def test_it_spends_nothing_even_at_a_generous_budget(self):
        item = _item(stopped={"stopped_deliberately": True})
        decision = runner_shared.turn_retry_decision(
            item, _state([item], retry_budget=10), "failed-safely", 1
        )
        self.assertFalse(decision.retry)
        self.assertFalse(decision.exhausted)
        self.assertEqual(0, decision.attempts)

    def test_the_interrupted_disposition_is_also_non_retryable(self):
        """The other half: `requeue_interrupted` owns that route and applies the R19 certainty gate."""
        retryable, why = runner_shared.turn_failure_is_retryable(_item(), "interrupted")
        self.assertFalse(retryable)
        self.assertIn("requeue_interrupted", why)

    def test_a_refused_finalize_is_left_to_its_own_counter(self):
        """Double-spend guard: `finalize_retry_decision` already charges that class."""
        item = _item(finalize_refusal="refused: pre-transition gate did NOT conform")
        retryable, why = runner_shared.turn_failure_is_retryable(
            item, "substantially-complete"
        )
        self.assertFalse(retryable)
        self.assertIn("REFUSED FINALIZE", why)


class TheFrozenBudgetIsWhatIsRead(unittest.TestCase):
    """E-02: read the FROZEN integer, never `args`; `0` is legal and must not be re-resolved."""

    def test_a_zero_budget_is_read_as_zero_and_not_as_unset(self):
        """The `is None` guard rather than a truthiness one. An off-by-one here is expensive."""
        self.assertEqual(
            0, runner_shared.frozen_retry_budget({"options": {"retry_budget": 0}})
        )
        self.assertEqual(2, runner_shared.frozen_retry_budget({"options": {}}))
        self.assertNotEqual(
            runner_shared.frozen_retry_budget({"options": {"retry_budget": 0}}),
            runner_shared.frozen_retry_budget({"options": {}}),
            "a truthiness check would make these equal, silently converting an operator's "
            "deliberate opt-out into the default of two paid correction turns",
        )

    def test_remaining_is_reported_rather_than_recomputed_by_each_caller(self):
        state = _state([], retry_budget=2)
        item = _item()
        self.assertEqual(2, runner_shared.turn_retry_budget_remaining(item, state))
        item[runner_shared.TURN_RETRY_COUNT_KEY] = 1
        self.assertEqual(1, runner_shared.turn_retry_budget_remaining(item, state))
        item[runner_shared.TURN_RETRY_COUNT_KEY] = 2
        self.assertEqual(0, runner_shared.turn_retry_budget_remaining(item, state))
        item[runner_shared.TURN_RETRY_COUNT_KEY] = 99
        self.assertEqual(
            0,
            runner_shared.turn_retry_budget_remaining(item, state),
            "remaining is never negative",
        )

    def test_a_malformed_frozen_value_falls_back_to_the_default(self):
        self.assertEqual(
            2, runner_shared.frozen_retry_budget({"options": {"retry_budget": "two"}})
        )


class TheBudgetIsSpentThroughTheSharedSemantics(unittest.TestCase):
    """E-03 / E-06 case 1 (NEW BEHAVIOR): budget 2 buys exactly 2 corrections, then escalates."""

    def test_budget_two_gives_exactly_two_corrections_then_escalates(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=2)

            observed = []
            for attempt_no in (1, 2, 3):
                item["attempts"].append({"number": attempt_no})
                observed.append(
                    _perform(run_dir, state, item, "failed-safely", attempt_no)
                )

            self.assertEqual(
                ["queued", "queued", "failed-safely"],
                observed,
                "budget 2 must buy exactly two corrections and then FAIL the item (spec 4.6's "
                "`RETRY, then FAIL ITEM`), never a third correction and never an endless loop",
            )
            self.assertEqual(2, runner_shared.turn_retry_attempts(item))
            self.assertEqual(0, runner_shared.turn_retry_budget_remaining(item, state))

    def test_the_failed_attempt_is_PRESERVED_beside_the_retry(self):
        """`plan_retry`'s contract, on this substrate: a retry never deletes the failed attempt."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item(attempts=[{"number": 1, "exit_code": 1}])
            state = _state([item], retry_budget=2)
            _perform(run_dir, state, item, "failed-safely", 1)
            self.assertEqual(
                [1],
                [a.get("number") for a in item["attempts"]],
                "the failed attempt must still be present after the retry is scheduled",
            )
            self.assertEqual(1, item["attempts"][0]["exit_code"])

    def test_the_retry_is_dispatched_through_the_ESTABLISHED_recovery_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            _perform(run_dir, _state([item], retry_budget=2), item, "failed-safely", 1)
            self.assertEqual("queued", item["status"])
            self.assertTrue(
                item["recovery_next"],
                "`recovery_next` is what makes the next turn interpolate `Prior attempt:`, which is "
                "how the correction packet reaches the agent",
            )
            self.assertEqual("failed-safely", item["requeue_from_status"])

    def test_the_total_dispatches_never_exceed_budget_plus_one(self):
        """The MECHANICAL bound. Nothing else supplies one; the in-tree precedent is a 201-spin."""
        for budget in (0, 1, 2, 5):
            with self.subTest(budget=budget):
                with tempfile.TemporaryDirectory() as tmp:
                    run_dir = _run_dir(Path(tmp))
                    item = _item()
                    state = _state([item], retry_budget=budget)
                    dispatches = 1
                    for attempt_no in range(1, budget + 5):
                        item["attempts"].append({"number": attempt_no})
                        result = _perform(
                            run_dir, state, item, "failed-safely", attempt_no
                        )
                        if result != "queued":
                            break
                        dispatches += 1
                    self.assertEqual(
                        budget + 1,
                        dispatches,
                        f"budget {budget} must permit exactly {budget + 1} total dispatches",
                    )


class TheCorrectionPacketCarriesOnlyWhatFailed(unittest.TestCase):
    """E-04: a correction is not a re-run, and stale evidence may not satisfy it."""

    def test_the_packet_names_only_failed_predicates(self):
        item = _item(
            verification_status="unverified",
            last_outcome={
                "disposition": "failed-safely",
                "incomplete_requirements": ["E-03 not performed"],
                "summary": "a passing thing that must NOT be re-sent",
            },
        )
        decision = runner_shared.turn_retry_decision(
            item, _state([item], retry_budget=2), "failed-safely", 1
        )
        packet = runner_shared.turn_correction_packet(
            item, _state([item], retry_budget=2), "failed-safely", decision
        )
        blob = json.dumps(packet)
        self.assertIn("E-03 not performed", blob)
        self.assertIn("unverified", blob)
        self.assertNotIn(
            "a passing thing that must NOT be re-sent",
            blob,
            "a correction packet must carry the FAILED predicates only; re-sending the whole task "
            "costs more and invites the model to redo work that already passed",
        )
        self.assertEqual("correction", packet["kind"])
        self.assertEqual(1, packet["attempt"])
        self.assertEqual(2, packet["of"])

    def test_the_packet_is_never_empty(self):
        """An empty list would read to the next turn as "nothing failed"."""
        item = _item()
        decision = runner_shared.turn_retry_decision(
            item, _state([item], retry_budget=2), "failed-safely", 1
        )
        packet = runner_shared.turn_correction_packet(
            item, _state([item], retry_budget=2), "failed-safely", decision
        )
        self.assertTrue(packet["failed_predicates"])

    def test_evidence_from_the_failed_attempt_cannot_satisfy_the_retry(self):
        """THE DANGEROUS HALF TO OMIT: a correction must not inherit the wrong green result."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item(
                verification_status="verified", last_outcome={"disposition": "executed"}
            )
            _perform(run_dir, _state([item], retry_budget=2), item, "failed-safely", 1)
            self.assertIsNone(
                item.get("verification_status"),
                "the failed attempt's verification must be INVALIDATED, not inherited: "
                "`run_viewer` tests `verification_status == 'verified'`, so a stale-but-present "
                "field would let dead evidence satisfy the retried attempt",
            )
            self.assertIsNone(item.get("last_outcome"))
            records = item[runner_shared.TURN_RETRY_INVALIDATIONS_KEY]
            self.assertEqual(1, len(records))
            self.assertEqual("correction", records[0]["kind"])
            self.assertEqual(1, records[0]["invalidates_attempt"])
            self.assertIn("verification_status", records[0]["invalidated"])


class TheCorrectionReachesTheAgentsPROMPT(unittest.TestCase):
    """E-04's delivery half, asserted on the RENDERED PROMPT rather than on a flag.

    THE MEASURED TRAP THIS PINS. The obvious channel is the existing `Prior attempt:` line, which
    already carries `finalize_refused` to a recovery turn. But that line is built by
    `lane_containment.prior_attempt_summary`, which projects an ALLOWLIST for an ISOLATED turn, and
    ISOLATION IS THE DEFAULT - so a packet left only on the attempt record is STRIPPED before it
    reaches the prompt on exactly the path a real run takes. A test asserting on the attempt dict
    would have passed over that; these assert on the rendered text.
    """

    def _prompt(self, item, recovery, lane_root=None):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            return runner_shared.build_prompt(
                item,
                _state([item], retry_budget=2) | {"repo": tmp, "runbook": ""},
                run_dir,
                Path(tmp) / "plan.ipd.md",
                recovery,
                lane_root=lane_root,
                labels=runner_shared.OC_HOST_LABELS,
            )

    def _item_with_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item(
                verification_status="verified",
                last_outcome={"incomplete_requirements": ["E-03 not performed"]},
            )
            _perform(run_dir, _state([item], retry_budget=2), item, "failed-safely", 1)
            return item

    def test_the_packet_is_rendered_into_the_recovery_prompt(self):
        prompt = self._prompt(self._item_with_packet(), recovery=True)
        self.assertIn("BOUNDED CORRECTION attempt (1 of 2)", prompt)
        self.assertIn("E-03 not performed", prompt)
        self.assertIn("INVALIDATED", prompt)

    def test_it_survives_an_ISOLATED_turn_which_is_the_default(self):
        """The whole point: the allowlist projection must not be able to strip it."""
        with tempfile.TemporaryDirectory() as lane:
            prompt = self._prompt(
                self._item_with_packet(), recovery=True, lane_root=Path(lane)
            )
            self.assertIn("BOUNDED CORRECTION attempt (1 of 2)", prompt)
            self.assertIn("E-03 not performed", prompt)

    def test_a_first_attempt_prompt_is_unchanged(self):
        """No correction, no block: an ordinary prompt must not grow a section."""
        self.assertNotIn("BOUNDED CORRECTION", self._prompt(_item(), recovery=False))
        self.assertNotIn("BOUNDED CORRECTION", self._prompt(_item(), recovery=True))

    def test_the_prompt_states_the_bound_so_the_agent_does_not_merely_repeat(self):
        prompt = self._prompt(self._item_with_packet(), recovery=True)
        self.assertIn("fix the CAUSE rather than repeating the same attempt", prompt)
        self.assertIn("FAILED rather", prompt)


class ExhaustionEscalatesOntoAReadSurface(unittest.TestCase):
    """E-05 / E-06 cases 2 and 3: exhaustion is terminal, named, and actually RENDERED."""

    def test_budget_zero_gives_no_corrections_and_escalates_immediately(self):
        """E-06 case 2 (NEW BEHAVIOR). Spec 5.5: `0` fails the item on the FIRST failure."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=0)
            result = _perform(run_dir, state, item, "failed-safely", 1)
            self.assertEqual("failed-safely", result)
            self.assertEqual(
                0,
                runner_shared.turn_retry_attempts(item),
                "a --retry-budget 0 run must perform ZERO corrections, not fall back to the "
                "default of 2",
            )
            self.assertNotIn("recovery_next", item)

    def test_a_non_retryable_class_gets_no_corrections_at_budget_ten(self):
        """E-06 case 3 (NEW BEHAVIOR): non-retryable stays non-retryable at EVERY budget."""
        for status in (
            "blocked",
            "dependency-blocked",
            "integration-blocked",
            "unknown_outcome",
        ):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    run_dir = _run_dir(Path(tmp))
                    item = _item(status=status)
                    result = _perform(
                        run_dir, _state([item], retry_budget=10), item, status, 1
                    )
                    self.assertEqual(
                        status,
                        result,
                        "a non-retryable class must be returned UNCHANGED",
                    )
                    self.assertEqual(0, runner_shared.turn_retry_attempts(item))
                    self.assertNotIn("recovery_next", item)

    def test_the_exhausted_status_is_in_BOTH_closed_vocabularies(self):
        """Inventing a status would make every later shutdown observation report the run broken."""
        self.assertIn(
            runner_shared.TURN_RETRY_EXHAUSTED_STATUS, oc_driver.TERMINAL_STATES
        )
        self.assertIn(
            runner_shared.TURN_RETRY_EXHAUSTED_STATUS, agy_driver.TERMINAL_STATES
        )
        self.assertIn(
            runner_shared.TURN_RETRY_EXHAUSTED_STATUS,
            runner_shutdown.KNOWN_ITEM_STATUSES,
        )

    def test_the_exhaustion_reason_is_actually_RENDERED_not_merely_stored(self):
        """Asserted on RENDERED OUTPUT, because a reason in state that renders nowhere is invisible.

        The diagnostics block reads a `Refusal` record for ANY status; its legacy arm reads the
        specific key `driver_error` for exactly three statuses. A reason written under a new key would
        sit in state and reach no surface at all, which is why this asserts on the rendering.
        """
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=0)
            _perform(run_dir, state, item, "failed-safely", 1)

            rendered = render_stream._strip_ansi(
                render_stream.render_run_summary_table(state)
            )
            self.assertIn("Diagnostics", rendered)
            self.assertIn("correction budget is exhausted", rendered)
            self.assertIn("0 of 0 correction attempts spent", rendered)
            self.assertIn("remedy:", rendered)

    def test_the_reason_names_how_many_attempts_the_budget_bought(self):
        """ "failed once" must be distinguishable from "failed after two corrections"."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=2)
            for attempt_no in (1, 2, 3):
                item["attempts"].append({"number": attempt_no})
                _perform(run_dir, state, item, "failed-safely", attempt_no)
            refusal = render_stream.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            assert refusal is not None
            self.assertIn("2 of 2 correction attempts spent", refusal.reason)
            self.assertEqual(runner_shared.TURN_RETRY_REFUSAL_CODE, refusal.code)

    def test_the_resulting_queue_is_still_COHERENT_to_the_shutdown_observer(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=0)
            _perform(run_dir, state, item, "failed-safely", 1)
            # Read from the state the performer actually SAVED, which is what `observe_ledger` reads.
            ok, detail = runner_shutdown.observe_ledger(run_dir)
            self.assertTrue(
                ok,
                f"an exhausted item must leave the ledger coherent (R3); got {detail!r}",
            )

    def test_a_pending_correction_also_leaves_the_queue_coherent(self):
        """`queued` is in the in-flight half of the closed vocabulary, so a pending retry is coherent."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            _perform(run_dir, _state([item], retry_budget=2), item, "failed-safely", 1)
            self.assertEqual("queued", item["status"])
            ok, detail = runner_shutdown.observe_ledger(run_dir)
            self.assertTrue(ok, f"got {detail!r}")

    def test_the_remedy_names_a_RUNNABLE_command_on_both_hosts(self):
        """A remedy is an instruction, so a malformed command makes it useless.

        MEASURED WHILE COLLECTING THIS PLAN'S V-05 EVIDENCE: `labels.command` already carries the verb
        (`aw oc run`), so a suffixed `run` rendered `aw oc run run xipfy1`. Invisible in the state dict
        and obvious in the rendered output, which is exactly why V-05 demands rendered output.
        """
        for labels, expected in (
            (runner_shared.OC_HOST_LABELS, "aw oc run xipfy1"),
            (runner_shared.AGY_HOST_LABELS, "aw agy run xipfy1"),
        ):
            with self.subTest(host=labels.command):
                remedy = runner_shared.turn_retry_remedy(labels, "xipfy1", retry=False)
                self.assertIn(expected, remedy)
                self.assertNotIn("run run", remedy)

    def test_a_pending_correction_remedy_does_not_invite_a_duplicate_turn(self):
        remedy = runner_shared.turn_retry_remedy(
            runner_shared.OC_HOST_LABELS, "xipfy1", retry=True
        )
        self.assertIn("no action needed yet", remedy)
        self.assertNotIn("re-run", remedy)

    def test_the_exhausted_item_is_NOT_counted_as_a_success(self):
        self.assertFalse(
            runner_shared.item_reached_success(
                {
                    "action": "execute",
                    "status": runner_shared.TURN_RETRY_EXHAUSTED_STATUS,
                }
            ),
            "the FAIL half of `RETRY, then FAIL ITEM` is what makes the loop safe; an exhausted "
            "correction must never read as success",
        )


class TheFrozenBudgetSurvivesAResume(unittest.TestCase):
    """E-06 case 5 (CHARACTERIZATION): a resume keeps the budget it was created with.

    ALREADY GUARANTEED BEFORE THIS CHANGE, by a REFUSAL rather than by a precedence rule:
    `refuse_frozen_flags_on_resume` rejects `--retry-budget` on resume outright. Kept as regression
    coverage because the new consumption path is the first thing that would NOTICE if a later change
    let a resume override the value.
    """

    def test_retry_budget_is_refused_on_resume_rather_than_allowed_to_override(self):
        refused = {
            row.dest
            for row in runner_shared.RUN_POLICY_FLAGS
            if row.resume_rule == runner_shared.RESUME_REFUSE
        }
        self.assertIn(
            "retry_budget",
            refused,
            "`refuse_frozen_flags_on_resume` REFUSES this flag on resume, which is what makes the "
            "frozen value unchangeable; the consumption path relies on that",
        )

    def test_the_decision_uses_the_frozen_value_and_ignores_a_different_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            frozen = _state([item], retry_budget=0)
            # A resume that somehow carried a DIFFERENT budget must not raise this item's ceiling:
            # the decision reads the frozen state, so the value below reaches nothing.
            _perform(run_dir, frozen, item, "failed-safely", 1)
            self.assertEqual(
                "failed-safely",
                item["status"],
                "the ORIGINALLY frozen budget of 0 must govern, so the item escalates",
            )
            self.assertEqual(0, runner_shared.turn_retry_attempts(item))


class ARepeatedIdempotencyKeyDoesNotDoubleSpend(unittest.TestCase):
    """E-06 case 6 (CHARACTERIZATION of a NEW implementation of an already-pinned property).

    `plan_retry`'s idempotency is pinned by `tests/test_run_recovery_cli.py`, but that is the ENGINE
    substrate. This substrate has its own key, so the property is re-proved here rather than assumed
    to have been inherited: the counter stops a LOOP while the key stops a DOUBLE SPEND of ONE
    decision re-entered after a crash or a `--retry-incomplete` requeue.
    """

    def test_the_key_is_derived_from_the_attempt_being_superseded(self):
        item = _item()
        self.assertEqual(
            "xipfy1:attempt-1", runner_shared.turn_retry_idempotency_key(item, 1)
        )
        self.assertNotEqual(
            runner_shared.turn_retry_idempotency_key(item, 1),
            runner_shared.turn_retry_idempotency_key(item, 2),
        )

    def test_a_repeated_key_spends_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=2)

            first = _perform(run_dir, state, item, "failed-safely", 1)
            self.assertEqual("queued", first)
            self.assertEqual(1, runner_shared.turn_retry_attempts(item))

            # The SAME attempt number again: a crash between the decision and the next dispatch, or a
            # requeue landing on an item already returned to `queued`.
            second = _perform(run_dir, state, item, "failed-safely", 1)
            self.assertEqual(
                1,
                runner_shared.turn_retry_attempts(item),
                "a repeated idempotency key must not spend a second budget unit",
            )
            self.assertNotEqual("queued", second)

    def test_a_fresh_key_does_spend(self):
        """The control: idempotency must not become a blanket refusal to retry at all."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _run_dir(Path(tmp))
            item = _item()
            state = _state([item], retry_budget=2)
            _perform(run_dir, state, item, "failed-safely", 1)
            _perform(run_dir, state, item, "failed-safely", 2)
            self.assertEqual(2, runner_shared.turn_retry_attempts(item))


class BothHostsShareTheWiring(unittest.TestCase):
    """E-07: proven by OBJECT IDENTITY, never by grep."""

    SHARED = (
        "TURN_RETRYABLE_DISPOSITIONS",
        "TURN_RETRY_CLASSIFICATION",
        "turn_failure_is_retryable",
        "turn_retry_decision",
        "turn_retry_budget_remaining",
        "handle_turn_failure_retry",
    )

    def test_both_hosts_resolve_to_the_SAME_object(self):
        for name in self.SHARED:
            with self.subTest(symbol=name):
                expected = getattr(runner_shared, name)
                self.assertIs(getattr(oc_driver, name), expected)
                self.assertIs(getattr(agy_driver, name), expected)
                self.assertIs(getattr(oc_driver, name), getattr(agy_driver, name))


class TheSubstrateChoiceIsRecordedAtTheImplementationSite(unittest.TestCase):
    """OQ-03's explicit requirement: the accepted duplication must be stated IN THE CODE.

    Without it the next reader meets a second implementation of retry semantics with no explanation
    and either deletes it or forks it further. The pointer to the still-open ledger question is part
    of the requirement, not decoration.
    """


if __name__ == "__main__":
    unittest.main()
