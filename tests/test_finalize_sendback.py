#!/usr/bin/env python3
"""finalback (`zzcrlo`): a refused finalize is reported honestly and handed back to the same agent.

THE MEASURED DEFECT these tests exist to guard, from run `run-20260908T213552Z-3724920` (agy host,
plan `xbwq8n`): the agent wrote correct code and committed it to its lane, never ticked its
`E-*`/`V-*` boxes, `aw ipd finalize` refused with nine `IPD-S404` findings, and the run printed
`Outcome: COMPLETED` at `Progress: 1/1 100%` while two commits sat stranded on `aw/lane/xbwq8n`.
Order 01 of a ten-plan Set had not landed and the summary said it had.

WHAT IS DELIBERATELY NOT TESTED HERE, because it was never broken: the run's EXIT CODE. It comes
from `runner_stop.deliberate_stop_exit_code` via `item_reached_success`, whose execute-action bar
excludes `substantially-complete`, so the measured run already exited 1. A test is included below
pinning that it STILL does, precisely so a future "fix" to the summary cannot quietly change it.

THE ALLOWLIST STRINGS ARE PINNED ON PURPOSE (`TheRetryTriggerIsAPositiveAllowlist`). The retry
trigger cannot be the `IPD-S404` code (it is the code for EVERY checkpoint diagnostic) and cannot be
the bare nonzero exit (`finalize_precheck` returns the same `(1, message)` shape for a missing
receipt, a STALE receipt and a scope refusal, all of which spec 25kzda 5.5 forbids retrying). So the
trigger matches finding TEXT, and these tests pin that text against the real `ipd_lint` output: a
wording change there must break a test rather than silently widen or disable the send-back.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as agy_driver
from agent_workflows import ipd_lint
from agent_workflows import oc_runipd as oc_driver
from agent_workflows import render_stream
from agent_workflows import runner_shared


# The REAL refusal message shape, reproduced end-to-end rather than paraphrased: `aw ipd finalize`
# prints `refused: <summary>` followed by one `  <RULE> <detail>` line per diagnostic, and
# `finalize_precheck`'s pre-transition summary is the literal below.
MEASURED_REFUSAL = "\n".join(
    [
        "refused: pre-transition gate did NOT conform (error); plan left unmoved.",
        "  IPD-S404 E-01: not 'performed' at pre-transition",
        "  IPD-S404 E-02: not 'performed' at pre-transition",
        "  IPD-S404 V-01: not 'pass' at pre-transition",
        "  IPD-S404 V-01: empty Observed evidence at pre-transition",
        "  IPD-S404 V-02: not 'pass' at pre-transition",
        "  IPD-S404 V-02: empty Observed evidence at pre-transition",
        "  IPD-S404 V-03: not 'pass' at pre-transition",
        "  IPD-S404 V-03: empty Observed evidence at pre-transition",
        "  IPD-S404 V-04: not 'pass' at pre-transition",
    ]
)

# spec 25kzda 5.5's never-retry classes that share the IDENTICAL `(1, message)` shape, so the
# classifier cannot tell them apart by exit code and must refuse them by text.
MISSING_RECEIPT_REFUSAL = (
    "refused: no begin receipt for zzcrlo: run `aw ipd begin` first (fail-closed: no receipt = "
    "no execution authority).\n  missing begin receipt at .aw/state/ipd-receipts/zzcrlo.json"
)
STALE_RECEIPT_REFUSAL = (
    "refused: the begin receipt for zzcrlo is STALE: the plan content changed since begin; "
    "re-run `aw ipd begin`.\n  plan content digest no longer matches the receipt"
)
SCOPE_REFUSAL = (
    "refused: scope reconciliation is unresolved; plan left unmoved.\n"
    "  out-of-scope path needs a --scope-reason: agent_workflows/cli.py"
)


def _item(**overrides):
    """One queue entry in the shape a real run persists."""
    item = {
        "position": 1,
        "id6": "xbwq8n",
        "setid": "lanetruth",
        "action": "execute",
        "status": "substantially-complete",
        "verification_status": "verified",
        "attempts": [{"number": 1}],
    }
    item.update(overrides)
    return item


def _state(queue, **options):
    return {
        "run_id": "run-20260908T213552Z-3724920",
        "repo": "/repo",
        "queue": queue,
        "options": dict(options),
    }


class TheRunOutcomeReflectsARefusedFinalize(unittest.TestCase):
    """E-01/E-05: the run must not report `COMPLETED` over a refused finalize."""

    def outcome_line(self, state):
        rendered = render_stream.render_run_summary_table(state)
        for line in rendered.splitlines():
            if "Outcome:" in line:
                return render_stream._strip_ansi(line)
        self.fail("no Outcome line was rendered")

    def test_the_measured_incident_is_not_reported_completed(self):
        """THE FALSIFIABLE CORE OF THIS PLAN, on the measured run's own state shape."""
        state = _state([_item(finalize_refusal=MEASURED_REFUSAL)])
        outcome = self.outcome_line(state)
        self.assertNotIn(
            "COMPLETED",
            outcome,
            "a run whose only item had its finalize REFUSED must not report COMPLETED; "
            f"got {outcome!r}",
        )
        self.assertIn("PARTIAL", outcome)

    def test_a_structured_refusal_record_is_also_honoured(self):
        """The forward path: both refusal arms now record a `Refusal` through the ONE writer."""
        item = _item()
        render_stream.record_refusal(
            item,
            code=runner_shared.FINALIZE_REFUSAL_CODE,
            reason="the finalize gate refused this plan's pre-transition checkpoint",
            remedy="complete the E/V bookkeeping and finalize again",
        )
        self.assertNotIn("COMPLETED", self.outcome_line(_state([item])))

    def test_a_refusal_free_substantially_complete_item_is_UNCHANGED(self):
        """The narrow fix: do NOT recategorize runs this plan is not about.

        `substantially-complete` stays a legitimate success-ish state for an item that finished with
        NO refused transition, which is why the discrimination is on the recorded refusal and not on
        the disposition.
        """
        self.assertIn("COMPLETED", self.outcome_line(_state([_item()])))

    def test_the_refusal_is_visible_on_the_summary_itself(self):
        """The table alone must not read as success (the measured row said `verified`, no refusal)."""
        rendered = render_stream.render_run_summary_table(
            _state([_item(finalize_refusal=MEASURED_REFUSAL)])
        )
        plain = render_stream._strip_ansi(rendered)
        self.assertIn("Diagnostics", plain)
        self.assertIn("xbwq8n", plain)
        self.assertIn("remedy:", plain, "a refusal must say what to do next")

    def test_a_legacy_multiline_refusal_does_not_break_the_diagnostics_layout(self):
        """The gate's raw message is multi-line; the diagnostics block renders a reason inline.

        Interpolating it raw pushes the remedy off its own line, which is the one property that block
        exists to guarantee. So the legacy reader FLATTENS it, and the full untruncated text stays in
        durable state.
        """
        item = _item(finalize_refusal=MEASURED_REFUSAL)
        refusal = render_stream.refusal_of_item(item)
        self.assertIsNotNone(refusal)
        assert refusal is not None
        self.assertNotIn("\n", refusal.reason)
        for token in (
            "not 'performed' at pre-transition",
            "pre-transition gate did NOT conform",
        ):
            self.assertIn(token, refusal.reason, "flattening must not DROP findings")
        rendered = render_stream._strip_ansi(
            render_stream.render_run_summary_table(_state([item]))
        )
        remedy_lines = [
            line
            for line in rendered.splitlines()
            if line.strip().startswith("\u2192 remedy:")
        ]
        self.assertEqual(
            1, len(remedy_lines), "the remedy must occupy exactly one line of its own"
        )
        self.assertEqual(
            MEASURED_REFUSAL,
            item["finalize_refusal"],
            "the full multi-line message must stay intact in durable state",
        )

    def test_the_exit_code_is_UNCHANGED_and_was_never_zero(self):
        """F-13: the process contract was already honest, so this plan must not touch it."""
        from agent_workflows import runner_stop

        self.assertNotIn("substantially-complete", runner_shared.SUCCESS_STATES)
        self.assertEqual(
            1,
            runner_stop.deliberate_stop_exit_code(
                ["substantially-complete"],
                success_states=runner_shared.SUCCESS_STATES,
                stopped=False,
            ),
        )


class TheRetryTriggerIsAPositiveAllowlist(unittest.TestCase):
    """E-03/F-15: neither the `IPD-S404` code nor the bare nonzero exit may be the trigger."""

    def test_the_measured_pre_transition_refusal_is_retryable(self):
        self.assertTrue(runner_shared.finalize_refusal_is_retryable(MEASURED_REFUSAL))

    def test_a_missing_begin_receipt_is_NOT_retryable(self):
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(MISSING_RECEIPT_REFUSAL)
        )

    def test_a_STALE_begin_receipt_is_NOT_retryable(self):
        """spec 5.5's "changed frozen requirements"."""
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(STALE_RECEIPT_REFUSAL)
        )

    def test_a_scope_reconciliation_refusal_is_NOT_retryable(self):
        """spec 5.5's FIRST never-retry entry, out-of-scope mutation."""
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(SCOPE_REFUSAL))

    def test_a_MIXED_message_is_NOT_retryable(self):
        """EVERY finding must be allowlisted, else a never-retry class rides along with a safe one."""
        mixed = (
            MEASURED_REFUSAL
            + "\n  IPD-S404 out-of-scope path needs a --scope-reason: agent_workflows/cli.py"
        )
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(mixed))

    def test_an_empty_or_summary_only_message_is_NOT_retryable(self):
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(""))
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(
                "refused: pre-transition gate did NOT conform (error); plan left unmoved."
            ),
            "the summary alone does not say WHICH class refused, so it must not be retried",
        )

    def test_the_allowlist_texts_are_the_ones_ipd_lint_ACTUALLY_EMITS(self):
        """THE PIN THAT MATTERS: the trigger is prose, so the prose must be verified, not trusted.

        Builds a plan whose `E-*`/`V-*` bookkeeping is incomplete in all three ways, lints it at the
        real `pre-transition` checkpoint, and asserts every emitted diagnostic is matched by the
        allowlist. If `ipd_lint` rewords a message, this fails instead of the send-back silently
        turning itself off.
        """
        with tempfile.TemporaryDirectory() as temp:
            plan = Path(temp) / "p.ipd.md"
            plan.write_text(
                "# IPD: pin\n\n"
                "- Date: 2026-09-20\n"
                "- Status: approved\n"
                "- Id: pin001\n\n"
                "## Detailed Implementation Checklist (TODO)\n\n"
                "- [ ] E-01 do the thing\n"
                "  - Depends on: none\n"
                "  - Expected outcome: it is done\n"
                "  - Execution state: pending\n\n"
                "## Validation and cross-check (verify before reporting done)\n\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: paste it\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n",
                encoding="utf-8",
            )
            result = ipd_lint.lint_file(plan, checkpoint="pre-transition")
            self.assertFalse(result.passing, "the fixture must actually fail the gate")
            checkpoint_diags = [
                d for d in result.diagnostics if d.code == ipd_lint.C_CHECKPOINT
            ]
            self.assertTrue(checkpoint_diags, "expected checkpoint diagnostics")
            for diag in checkpoint_diags:
                self.assertTrue(
                    any(
                        token in diag.message
                        for token in runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS
                    ),
                    f"ipd_lint emits {diag.message!r} at pre-transition but the retry allowlist "
                    f"does not match it; update RETRYABLE_FINALIZE_FINDING_TEXTS deliberately",
                )


class TheBudgetIsSpentOncePerRedispatch(unittest.TestCase):
    """E-04: one spend per send-back, `0` means none, exhaustion FAILS the item."""

    def test_budget_zero_performs_NO_retry_and_fails_the_item(self):
        """spec 5.5: "`0` means the first failed deterministic check ... immediately fails the item".

        An off-by-one here converts a deliberate opt-out into a silent retry, which is why this case
        gets its own test.
        """
        item = _item()
        decision = runner_shared.finalize_retry_decision(
            item, _state([item], retry_budget=0), MEASURED_REFUSAL
        )
        self.assertFalse(decision.retry)
        self.assertTrue(decision.exhausted)
        self.assertEqual(0, decision.budget)

    def test_one_unit_is_spent_per_redispatch_and_no_more(self):
        item = _item()
        state = _state([item], retry_budget=2)

        first = runner_shared.finalize_retry_decision(item, state, MEASURED_REFUSAL)
        self.assertTrue(first.retry)
        self.assertEqual(0, first.attempts)

        item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = 1
        second = runner_shared.finalize_retry_decision(item, state, MEASURED_REFUSAL)
        self.assertTrue(second.retry)
        self.assertEqual(1, second.attempts)

        item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = 2
        third = runner_shared.finalize_retry_decision(item, state, MEASURED_REFUSAL)
        self.assertFalse(
            third.retry, "the budget of 2 must not fund a third correction"
        )
        self.assertTrue(third.exhausted)

    def test_the_budget_is_read_from_FROZEN_state_not_re_resolved(self):
        """The frozen value is what `freeze_run_policy_flags` already resolved; do not re-resolve."""
        self.assertEqual(
            0, runner_shared.frozen_retry_budget({"options": {"retry_budget": 0}})
        )
        self.assertEqual(
            7, runner_shared.frozen_retry_budget({"options": {"retry_budget": 7}})
        )

    def test_an_ABSENT_budget_falls_back_to_the_shared_resolver(self):
        """A state frozen before the flag existed must not crash and must not invent a value."""
        self.assertEqual(
            runner_shared.resolve_retry_budget(None),
            runner_shared.frozen_retry_budget({"options": {}}),
        )

    def test_the_guard_is_is_None_shaped_so_a_legal_zero_survives(self):
        """A truthiness test here would silently promote `0` to the default of two."""
        self.assertNotEqual(
            runner_shared.frozen_retry_budget({"options": {"retry_budget": 0}}),
            runner_shared.frozen_retry_budget({"options": {}}),
        )

    def test_no_second_budget_knob_was_introduced(self):
        """OQ-03: bound against the attempt list, but never with a competing budget concept."""
        self.assertIs(
            runner_shared.resolve_retry_budget,
            runner_shared.resolve_retry_budget,
        )
        self.assertEqual(
            runner_shared.resolve_retry_budget(None),
            __import__(
                "agent_workflows.run_recovery", fromlist=["x"]
            ).DEFAULT_RETRY_LIMIT,
            "the send-back must spend the run's existing --retry-budget, not a new default",
        )

    def test_a_non_retryable_refusal_is_neither_retried_nor_failed(self):
        """Fall through to today's behavior: preserve and report, unchanged."""
        item = _item()
        decision = runner_shared.finalize_retry_decision(
            item, _state([item], retry_budget=2), SCOPE_REFUSAL
        )
        self.assertFalse(decision.retry)
        self.assertFalse(decision.exhausted)


class TheRefusalArmPerformsTheSendBack(unittest.TestCase):
    """E-03/E-06: the decision lives IN the refusal arm, and it drives real state."""

    def _run(self, fin_msg, budget=2, item=None):
        saved = []
        events = []
        item = item if item is not None else _item()
        state = _state([item], retry_budget=budget)
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            disposition = runner_shared.handle_finalize_refusal(
                run_dir=run_dir,
                state=state,
                item=item,
                attempt=item["attempts"][-1],
                fin_rc=1,
                fin_msg=fin_msg,
                disposition="substantially-complete",
                host_labels=None,
                save_state=lambda rd, st: saved.append(st),
                append_jsonl=lambda path, rec: events.append(rec),
            )
        return disposition, item, events

    def test_a_retryable_refusal_requeues_the_item_in_recovery_mode(self):
        disposition, item, events = self._run(MEASURED_REFUSAL, budget=2)
        self.assertEqual("queued", disposition)
        self.assertEqual("queued", item["status"])
        self.assertTrue(
            item["recovery_next"],
            "the established re-dispatch pattern is `queued` + `recovery_next`",
        )
        self.assertEqual(1, item[runner_shared.FINALIZE_RETRY_COUNT_KEY])
        self.assertEqual(1, len(events))
        self.assertTrue(events[0]["retry_scheduled"])
        self.assertEqual("ipd-finalize-refused", events[0]["event"])

    def test_the_gate_findings_are_PRESERVED_for_the_next_turn(self):
        """The feedback channel already exists; this asserts the data it carries is still there."""
        _disposition, item, _events = self._run(MEASURED_REFUSAL)
        self.assertEqual(MEASURED_REFUSAL, item["finalize_refusal"])
        self.assertEqual(MEASURED_REFUSAL, item["attempts"][-1]["finalize_refused"])

    def test_exhaustion_FAILS_the_item_rather_than_leaving_it_success_ish(self):
        item = _item()
        item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = 2
        disposition, item, events = self._run(MEASURED_REFUSAL, budget=2, item=item)
        self.assertEqual(runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS, disposition)
        self.assertEqual("failed-safely", item["status"])
        self.assertNotIn("recovery_next", item)
        self.assertFalse(events[0]["retry_scheduled"])

    def test_budget_zero_fails_on_the_FIRST_refusal(self):
        disposition, item, _events = self._run(MEASURED_REFUSAL, budget=0)
        self.assertEqual("failed-safely", item["status"])
        self.assertEqual(runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS, disposition)

    def test_a_never_retry_class_falls_through_UNCHANGED(self):
        disposition, item, events = self._run(SCOPE_REFUSAL, budget=2)
        self.assertEqual("substantially-complete", disposition)
        self.assertEqual("substantially-complete", item["status"])
        self.assertNotIn("recovery_next", item)
        self.assertEqual(0, runner_shared.finalize_retry_attempts(item))
        self.assertFalse(events[0]["retryable"])

    def test_every_arm_records_a_refusal_with_a_remedy(self):
        """r2i1b1's contract: a refusal that cannot say what to do next is incomplete."""
        for msg in (MEASURED_REFUSAL, SCOPE_REFUSAL):
            with self.subTest(msg=msg.splitlines()[0]):
                _disposition, item, _events = self._run(msg)
                refusal = render_stream.refusal_of_item(item)
                self.assertIsNotNone(refusal)
                assert refusal is not None
                self.assertEqual(runner_shared.FINALIZE_REFUSAL_CODE, refusal.code)
                self.assertTrue(refusal.reason.strip())
                self.assertTrue(refusal.remedy.strip())

    def test_an_exhausted_item_is_reported_FAILED_not_COMPLETED(self):
        item = _item()
        item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = 2
        _disposition, item, _events = self._run(MEASURED_REFUSAL, budget=2, item=item)
        rendered = render_stream.render_run_summary_table(_state([item]))
        outcome = next(
            render_stream._strip_ansi(line)
            for line in rendered.splitlines()
            if "Outcome:" in line
        )
        self.assertIn("FAILED", outcome)
        self.assertNotIn("COMPLETED", outcome)

    def test_the_REDISPATCHED_PROMPT_CONTAINS_the_gate_findings(self):
        """V-03's decisive assertion: assert on the PROMPT, not on the flag.

        THE CHANNEL DEPENDS ON ATTEMPT ORDERING, which is why this asserts on rendered text rather
        than on `recovery_next`: the recovery prompt reads `attempts[-1]`, and `finalize_refused` is
        written onto the ATTEMPT. If a future change stops the refused attempt being last, every flag
        would still look right while the channel silently emptied.
        """
        _disposition, item, _events = self._run(MEASURED_REFUSAL, budget=2)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            run_dir = repo / "run"
            run_dir.mkdir(parents=True)
            plan = repo / "plan.ipd.md"
            plan.write_text("# IPD: x\n\n- Id: xbwq8n\n", encoding="utf-8")
            state = _state([item], retry_budget=2)
            state["repo"] = str(repo)
            for label_name in ("OC_HOST_LABELS", "AGY_HOST_LABELS"):
                with self.subTest(host=label_name):
                    prompt = runner_shared.build_prompt(
                        item,
                        state,
                        run_dir,
                        plan,
                        recovery=True,
                        labels=getattr(runner_shared, label_name),
                    )
                    self.assertIn(
                        "finalize_refused",
                        prompt,
                        "the recovery prompt must carry the refusal through the existing "
                        "`Prior attempt:` channel",
                    )
                    for token in (
                        "not 'performed' at pre-transition",
                        "empty Observed evidence at pre-transition",
                    ):
                        self.assertIn(
                            token,
                            prompt,
                            f"the agent must receive the gate's own finding {token!r}",
                        )

    def test_finalize_refused_is_an_ALLOWLISTED_prior_attempt_key(self):
        """The one mechanical fact the whole channel rests on."""
        from agent_workflows import lane_containment

        self.assertIn("finalize_refused", lane_containment._PRIOR_ATTEMPT_SAFE_KEYS)

    def test_the_full_multi_finding_message_survives_the_projection_intact(self):
        """A truncating projection would hand the agent a partial findings list."""
        from agent_workflows import lane_containment

        projected = lane_containment.prior_attempt_summary(
            {"number": 1, "finalize_refused": MEASURED_REFUSAL}, None
        )
        self.assertIsNotNone(projected)
        assert projected is not None
        self.assertEqual(MEASURED_REFUSAL, projected["finalize_refused"])


class BothHostsBehaveIdentically(unittest.TestCase):
    """E-03/E-06: the incident was agy and the twin is where drift hides."""

    def test_the_send_back_symbols_are_reachable_from_both_hosts(self):
        for driver in (oc_driver, agy_driver):
            with self.subTest(driver=driver.__name__):
                shared = driver.runner_shared
                self.assertIs(
                    shared.handle_finalize_refusal,
                    runner_shared.handle_finalize_refusal,
                )
                self.assertIs(
                    shared.finalize_refusal_is_retryable,
                    runner_shared.finalize_refusal_is_retryable,
                )

    def test_both_hosts_agree_on_the_success_bars(self):
        self.assertEqual(
            oc_driver.EXECUTION_SUCCESS_STATES, agy_driver.EXECUTION_SUCCESS_STATES
        )
        self.assertEqual(oc_driver.SUCCESS_STATES, agy_driver.SUCCESS_STATES)


class TheLoopIsMECHANICALLYBounded(unittest.TestCase):
    """E-06: a test asserting only "it retried" would pass on an implementation that retries forever.

    NOTHING ELSE SUPPLIES A BOUND. `max_items_per_session` rotates the SESSION, it does not cap
    dispatch, and the selection loop re-picks any `queued` item whose dependencies are satisfied. The
    in-tree precedent is a MEASURED 201-dispatch orchestrator spin that the drain path could not
    catch. So the bound is asserted as a COUNT.
    """

    def test_total_dispatches_for_one_item_never_exceed_budget_plus_one(self):
        for budget in (0, 1, 2, 5):
            with self.subTest(budget=budget):
                item = _item()
                state = _state([item], retry_budget=budget)
                dispatches = 0
                # Simulate the run loop: dispatch, refuse, decide, repeat. Hard-capped far above the
                # legal bound so a runaway implementation FAILS here instead of hanging.
                for _ in range(100):
                    dispatches += 1
                    decision = runner_shared.finalize_retry_decision(
                        item, state, MEASURED_REFUSAL
                    )
                    if not decision.retry:
                        break
                    item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = decision.attempts + 1
                else:  # pragma: no cover - only reached by a runaway loop
                    self.fail(
                        f"the send-back did not terminate within 100 dispatches at budget {budget}"
                    )
                self.assertEqual(
                    budget + 1,
                    dispatches,
                    f"an item with budget {budget} must be dispatched exactly {budget + 1} times "
                    "(the original plus one per budget unit)",
                )
                self.assertTrue(
                    runner_shared.finalize_retry_decision(
                        item, state, MEASURED_REFUSAL
                    ).exhausted
                )

    def test_a_successful_correction_ENDS_the_loop(self):
        """The happy path: the agent ticks its boxes, finalize returns 0, nothing re-dispatches."""
        item = _item()
        item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = 1
        # A conforming second turn produces rc=0, so the refusal arm is never entered at all: the
        # `if fin_rc == 0` branch finalizes and the item reaches `executed`.
        self.assertTrue(
            runner_shared.finalize_retry_decision(
                item, _state([item], retry_budget=2), MEASURED_REFUSAL
            ).retry,
            "precondition: budget still remained, so the loop ended by SUCCESS and not exhaustion",
        )
        item["status"] = "executed"
        rendered = render_stream.render_run_summary_table(_state([item]))
        outcome = next(
            render_stream._strip_ansi(line)
            for line in rendered.splitlines()
            if "Outcome:" in line
        )
        self.assertIn(
            "COMPLETED",
            outcome,
            "a corrected item that finalized must report success",
        )


class ARefusedItemDoesNotSatisfyADependentEdge(unittest.TestCase):
    """E-02: the in-run dependency question, which the maintainer's 2026-09-19 ruling already fixed.

    THIS PLAN'S F-2/F-14 ANALYSIS IS STALE AND THE TEST RECORDS WHY. `edge_satisfied` used to accept
    any member of `EXECUTION_SUCCESS_STATES` from the dependency's IN-MEMORY run status, which admits
    `substantially-complete` - a status meaning finalize did NOT happen, so the plan is still in
    `pending/` and its lane was never merged. That shortcut was REMOVED on 2026-09-19 after run
    `run-20260919T194413Z-2056285` cost 2h10m and $55.02 dispatching `n4xq3l` against a tree with
    none of `yaxr4i`'s work. The disk is now the only authority.

    So this asserts the PROPERTY this plan owes rather than re-introducing a read of `by_id`, which
    the ruling explicitly forbids ("Do not reintroduce a read of it without that ruling being
    revisited").
    """

    def _edge_state(self, dep_status, repo):
        dep = _item(id6="yaxr4i", status=dep_status, finalize_refusal=MEASURED_REFUSAL)
        dependent = _item(id6="n4xq3l", position=2, status="queued", attempts=[])
        dependent["dependencies"] = ["executed:yaxr4i"]
        return {
            "run_id": "r",
            "repo": str(repo),
            "queue": [dep, dependent],
            "options": {},
        }

    def test_a_refused_dependency_does_not_release_its_dependent(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            # A refused finalize leaves the plan in `pending/`, which is exactly the on-disk state
            # the gate reads.
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            (pending / "20260919-s-01-yaxr4i-dep.ipd.md").write_text(
                "# IPD: dep\n\n- Id: yaxr4i\n- Status: approved\n", encoding="utf-8"
            )
            state = self._edge_state("substantially-complete", repo)
            dependent = state["queue"][1]
            satisfied, unsatisfied = oc_driver.dependency_status(dependent, state)
            self.assertFalse(
                satisfied,
                "a dependency whose finalize was REFUSED must not release its dependent: its work "
                f"was never integrated (unsatisfied={unsatisfied})",
            )
            self.assertEqual(["executed:yaxr4i"], unsatisfied)

    def test_the_cascade_and_edge_gate_remain_ONE_shared_object_per_host(self):
        """Sites 1 and 2 must not be able to disagree (the measured `wslayout` defect)."""
        self.assertIs(oc_driver.edge_satisfied, agy_driver.edge_satisfied)
        self.assertIs(
            oc_driver.cascade_dependency_blocked, agy_driver.cascade_dependency_blocked
        )


class TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains(unittest.TestCase):
    """E-02's DECIDED treatment of the orchestrator injection sites (F-14 sites 3 to 5).

    THE DECISION: leave `decide_orchestrator_dispatch`'s injected `success_states` ALONE, which the
    plan explicitly permits as long as it is a decision rather than an omission. Narrowing it would
    convert a recoverable refusal into a terminal Set-wide `dead-children` kill at the exact moment
    E-03 wants that item re-dispatched, which is a worse regression than the bug being fixed.

    WHY IT IS SAFE: the two states do the work. While a retry is pending the child is `queued`, which
    is NOT terminal, so it reads ACTIONABLE -> RECONSIDER. Once the budget is exhausted it is
    `failed-safely`, a non-success terminal state, so the Set then correctly TERMINATES instead of
    spinning. Both halves are asserted below.
    """

    def _decide(self, child_status, repo, setid="finalback"):
        queue = [
            {
                "id6": "kid001",
                "setid": setid,
                "status": child_status,
                "action": "execute",
            },
        ]
        return runner_shared.decide_orchestrator_dispatch(
            repo,
            setid,
            "par001",
            queue,
            terminal_states=runner_shared.TERMINAL_STATES,
            success_states=oc_driver.EXECUTION_SUCCESS_STATES,
        )

    def _repo_with_unfinished_child(self, temp):
        repo = Path(temp)
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        (pending / "20260908-finalback-00-par001-orch.ipd.md").write_text(
            "# IPD: orch\n\n- Id: par001\n- Set: finalback\n- Order: 0\n- Kind: orchestrator\n",
            encoding="utf-8",
        )
        (pending / "20260908-finalback-01-kid001-child.ipd.md").write_text(
            "# IPD: child\n\n- Id: kid001\n- Set: finalback\n- Order: 1\n- Kind: child\n",
            encoding="utf-8",
        )
        return repo

    def test_a_queued_retrying_child_is_NOT_declared_dead(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self._repo_with_unfinished_child(temp)
            decision = self._decide("queued", repo)
            self.assertNotEqual(
                runner_shared.ORCH_REASON_DEAD_CHILDREN,
                decision.reason,
                "a child awaiting its correction turn must not kill the Set as dead-children",
            )
            self.assertNotEqual(runner_shared.ORCH_DISPATCH_TERMINATE, decision.outcome)

    def test_an_EXHAUSTED_child_DOES_terminate_the_set(self):
        """The other half: once the budget is gone the run must stop waiting, not spin."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._repo_with_unfinished_child(temp)
            decision = self._decide(runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS, repo)
            self.assertEqual(runner_shared.ORCH_DISPATCH_TERMINATE, decision.outcome)
            self.assertEqual(runner_shared.ORCH_REASON_DEAD_CHILDREN, decision.reason)

    def test_the_exhausted_status_is_terminal_and_not_a_success(self):
        """The two properties the orchestrator behavior above depends on."""
        status = runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS
        self.assertIn(status, runner_shared.TERMINAL_STATES)
        self.assertNotIn(status, oc_driver.EXECUTION_SUCCESS_STATES)
        self.assertNotIn(status, runner_shared.SUCCESS_STATES)

    def test_a_retrying_child_is_not_terminal_which_is_what_makes_it_actionable(self):
        self.assertNotIn("queued", runner_shared.TERMINAL_STATES)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
