#!/usr/bin/env python3
"""finalback (`zzcrlo`, refined by `787hb4`): a refused finalize is reported honestly and handed back.

statusvocab Order 02 (`787hb4`) refines the retryable trigger to per-class arms by answerability:
  - pre-transition gate refusal (incomplete E/V bookkeeping) -> retryable
  - stale begin receipt refusal (digest mismatch or contract reduction) -> retryable
  - scope contract rewrite / fence widening -> NOT retryable (terminal)
  - missing begin receipt -> NOT retryable (terminal)
  - out-of-scope mutation / scope reconciliation refusal -> NOT retryable (terminal)
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as agy_driver
from agent_workflows import ipd_lifecycle
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
REDUCTION_REFUSAL_SINGULAR = (
    "refused: the begin receipt for 787hb4 is STALE: the plan content changed since begin; "
    "re-run `aw ipd begin`.\n"
    "  plan content digest no longer matches the receipt\n"
    "  Scope-Paths entry REMOVED since begin (a contract reduction, never accepted as a widening): "
    "tests/test_rununify_initialize_run_characterization.py"
)
REDUCTION_REFUSAL_PLURAL = (
    "refused: the begin receipt for 787hb4 is STALE: the plan content changed since begin; "
    "re-run `aw ipd begin`.\n"
    "  plan content digest no longer matches the receipt\n"
    "  Scope-Paths entries REMOVED since begin (a contract reduction, never accepted as a widening): "
    "tests/test_1.py, tests/test_2.py"
)
REWRITE_REFUSAL = (
    "refused: the begin receipt for 787hb4 is STALE: the plan content changed since begin; "
    "re-run `aw ipd begin`.\n"
    "  plan content digest no longer matches the receipt\n"
    "  Scope-Paths gained agent_workflows/cli.py but a frozen REQUIREMENT also changed, "
    "so this is a contract rewrite rather than an additive widening"
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

    def test_substantially_complete_was_not_removed_from_the_outcome_tuple(self):
        """Guards the tempting wrong fix, which the plan's fence explicitly forbids."""
        import inspect

        src = inspect.getsource(render_stream.render_run_summary_table)
        self.assertIn(
            '"executed", "reviewed", "approved", "substantially-complete"',
            src,
            "the outcome tuple must still admit `substantially-complete`; the refusal, not the "
            "disposition, is what downgrades the outcome",
        )

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
        """The gate's raw message is multi-line; the diagnostics block renders a reason inline."""
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
    """E-02/F-15: neither the `IPD-S404` code nor the bare nonzero exit may be the trigger."""

    def test_the_measured_pre_transition_refusal_is_retryable(self):
        self.assertTrue(runner_shared.finalize_refusal_is_retryable(MEASURED_REFUSAL))

    def test_a_missing_begin_receipt_is_NOT_retryable(self):
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(MISSING_RECEIPT_REFUSAL)
        )

    def test_a_STALE_begin_receipt_is_retryable(self):
        """Answerable in one bounded turn (statusvocab 02 `787hb4`): re-run `aw ipd begin`."""
        self.assertTrue(
            runner_shared.finalize_refusal_is_retryable(STALE_RECEIPT_REFUSAL)
        )

    def test_a_scope_reduction_refusal_is_retryable(self):
        """Answerable in one bounded turn (statusvocab 02 `787hb4`): justify or revert reduction."""
        self.assertTrue(
            runner_shared.finalize_refusal_is_retryable(REDUCTION_REFUSAL_SINGULAR)
        )
        self.assertTrue(
            runner_shared.finalize_refusal_is_retryable(REDUCTION_REFUSAL_PLURAL)
        )

    def test_a_fence_widening_rewrite_is_NOT_retryable(self):
        """spec 5.5's changed frozen requirements / contract rewrite remains terminal."""
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(REWRITE_REFUSAL))

    def test_a_scope_reconciliation_refusal_is_NOT_retryable(self):
        """spec 5.5's FIRST never-retry entry, out-of-scope mutation."""
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(SCOPE_REFUSAL))

    def test_a_MIXED_message_is_NOT_retryable(self):
        """EVERY finding must be allowlisted, else a never-retry class rides along with a safe one."""
        mixed_pre = (
            MEASURED_REFUSAL
            + "\n  IPD-S404 out-of-scope path needs a --scope-reason: agent_workflows/cli.py"
        )
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(mixed_pre))
        mixed_stale = (
            STALE_RECEIPT_REFUSAL
            + "\n  Scope-Paths gained agent_workflows/cli.py but a frozen REQUIREMENT also changed, "
            "so this is a contract rewrite rather than an additive widening"
        )
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(mixed_stale))

    def test_an_empty_or_summary_only_message_is_NOT_retryable(self):
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(""))
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(
                "refused: pre-transition gate did NOT conform (error); plan left unmoved."
            ),
            "the summary alone does not say WHICH class refused, so it must not be retried",
        )
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(
                "refused: the begin receipt for zzcrlo is STALE: the plan content changed since begin; re-run `aw ipd begin`."
            ),
            "the summary alone does not say WHICH class refused, so it must not be retried",
        )

    def test_the_allowlist_texts_are_the_ones_ipd_lint_ACTUALLY_EMITS(self):
        """THE PIN THAT MATTERS: the trigger is prose, so the prose must be verified, not trusted."""
        with tempfile.TemporaryDirectory() as temp:
            plan = Path(temp) / "plan.ipd.md"
            plan.write_text(
                "# IPD: x\n\n"
                "- Id: xbwq8n\n"
                "- Status: approved\n"
                "- Set: lanetruth\n"
                "- Order: 1\n"
                "- Kind: child\n"
                "- Scope: x\n"
                "- Scope-Paths: x\n"
                "- Item-Dependencies: none\n\n"
                "## Detailed Implementation Checklist (TODO)\n\n"
                "- [ ] E-01 do work\n"
                "  - Execution state: pending\n\n"
                "## Validation and cross-check (verify before reporting done)\n\n"
                "- [ ] V-01 validates E-01\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n",
                encoding="utf-8",
            )
            result = ipd_lint.lint_file(plan, checkpoint="pre-transition")
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

    def test_the_summary_text_is_the_one_finalize_precheck_ACTUALLY_EMITS(self):
        """The other half of the same pin: the summary sentence must still be the gate's."""
        import inspect

        src = inspect.getsource(ipd_lifecycle.finalize_precheck)
        self.assertIn(
            runner_shared.RETRYABLE_FINALIZE_SUMMARY,
            src,
            "the retryable summary must be the literal `finalize_precheck` emits",
        )
        self.assertIn(
            "is STALE: the plan content changed since begin;",
            src,
            "the stale summary must be the literal `finalize_precheck` emits",
        )

    def test_the_reduction_invariant_text_matches_ipd_lifecycle_findings(self):
        """E-01: FINDING_SCOPE_REDUCED_INVARIANT is part of both singular and plural reduction findings."""
        singular = (
            "Scope-Paths entry "
            + f"{ipd_lifecycle.FINDING_SCOPE_REDUCED_INVARIANT}: a.py"
        )
        plural = (
            "Scope-Paths entries "
            + f"{ipd_lifecycle.FINDING_SCOPE_REDUCED_INVARIANT}: a.py, b.py"
        )
        self.assertIn(ipd_lifecycle.FINDING_SCOPE_REDUCED_INVARIANT, singular)
        self.assertIn(ipd_lifecycle.FINDING_SCOPE_REDUCED_INVARIANT, plural)
        self.assertEqual(
            ipd_lifecycle.FINDING_SCOPE_REDUCED,
            ipd_lifecycle.FINDING_SCOPE_REDUCED_INVARIANT,
        )


class TheBudgetIsSpentOncePerRedispatch(unittest.TestCase):
    """E-04 / E-03: one spend per send-back, `0` means none, exhaustion FAILS the item."""

    def test_budget_zero_performs_NO_retry_and_fails_the_item(self):
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
        self.assertEqual(
            0, runner_shared.frozen_retry_budget({"options": {"retry_budget": 0}})
        )
        self.assertEqual(
            7, runner_shared.frozen_retry_budget({"options": {"retry_budget": 7}})
        )

    def test_an_ABSENT_budget_falls_back_to_the_shared_resolver(self):
        self.assertEqual(
            runner_shared.resolve_retry_budget(None),
            runner_shared.frozen_retry_budget({"options": {}}),
        )

    def test_the_guard_is_is_None_shaped_so_a_legal_zero_survives(self):
        self.assertNotEqual(
            runner_shared.frozen_retry_budget({"options": {"retry_budget": 0}}),
            runner_shared.frozen_retry_budget({"options": {}}),
        )

    def test_no_second_budget_knob_was_introduced(self):
        self.assertEqual(
            runner_shared.resolve_retry_budget(None),
            __import__(
                "agent_workflows.run_recovery", fromlist=["x"]
            ).DEFAULT_RETRY_LIMIT,
        )

    def test_a_non_retryable_refusal_is_neither_retried_nor_failed(self):
        item = _item()
        decision = runner_shared.finalize_retry_decision(
            item, _state([item], retry_budget=2), SCOPE_REFUSAL
        )
        self.assertFalse(decision.retry)
        self.assertFalse(decision.exhausted)


class TheRefusalArmPerformsTheSendBack(unittest.TestCase):
    """E-02/E-03: the decision lives IN the refusal arm, and it drives real state."""

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

    def test_a_retryable_pretransition_refusal_requeues_the_item_in_recovery_mode(self):
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

    def test_a_stale_receipt_refusal_requeues_the_item_in_recovery_mode(self):
        disposition, item, events = self._run(STALE_RECEIPT_REFUSAL, budget=2)
        self.assertEqual("queued", disposition)
        self.assertEqual("queued", item["status"])
        self.assertTrue(item["recovery_next"])
        self.assertEqual(1, item[runner_shared.FINALIZE_RETRY_COUNT_KEY])
        self.assertTrue(events[0]["retry_scheduled"])

    def test_a_scope_reduction_refusal_requeues_the_item_in_recovery_mode(self):
        disposition, item, events = self._run(REDUCTION_REFUSAL_SINGULAR, budget=2)
        self.assertEqual("queued", disposition)
        self.assertEqual("queued", item["status"])
        self.assertTrue(item["recovery_next"])
        self.assertEqual(1, item[runner_shared.FINALIZE_RETRY_COUNT_KEY])
        self.assertTrue(events[0]["retry_scheduled"])

    def test_the_gate_findings_are_PRESERVED_for_the_next_turn(self):
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

    def test_exhaustion_on_stale_receipt_ends_terminal_with_findings_preserved(self):
        """E-03: exhaustion on stale receipt ends terminal and preserves gate findings."""
        item = _item()
        item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = 2
        disposition, item, events = self._run(
            STALE_RECEIPT_REFUSAL, budget=2, item=item
        )
        self.assertEqual(runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS, disposition)
        self.assertEqual("failed-safely", item["status"])
        self.assertIn("failed-safely", runner_shared.TERMINAL_STATES)
        self.assertNotIn("failed-safely", runner_shared.SUCCESS_STATES)
        self.assertEqual(STALE_RECEIPT_REFUSAL, item["finalize_refusal"])
        self.assertNotIn("recovery_next", item)
        self.assertFalse(events[0]["retry_scheduled"])

    def test_second_identical_refusal_does_not_reset_counter(self):
        """E-03: a second refusal increments rather than resets the retry count."""
        item = _item()
        _disp1, item1, _ev1 = self._run(STALE_RECEIPT_REFUSAL, budget=2, item=item)
        self.assertEqual(1, item1[runner_shared.FINALIZE_RETRY_COUNT_KEY])
        _disp2, item2, _ev2 = self._run(STALE_RECEIPT_REFUSAL, budget=2, item=item1)
        self.assertEqual(2, item2[runner_shared.FINALIZE_RETRY_COUNT_KEY])

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
        for msg in (MEASURED_REFUSAL, SCOPE_REFUSAL, STALE_RECEIPT_REFUSAL):
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
        """Assert on the PROMPT, not on the flag."""
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

    def test_the_REDISPATCHED_PROMPT_CONTAINS_stale_receipt_findings(self):
        """V-02: rendered recovery prompt carries the stale receipt findings."""
        _disposition, item, _events = self._run(REDUCTION_REFUSAL_SINGULAR, budget=2)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            run_dir = repo / "run"
            run_dir.mkdir(parents=True)
            plan = repo / "plan.ipd.md"
            plan.write_text("# IPD: x\n\n- Id: xbwq8n\n", encoding="utf-8")
            state = _state([item], retry_budget=2)
            state["repo"] = str(repo)
            prompt = runner_shared.build_prompt(
                item,
                state,
                run_dir,
                plan,
                recovery=True,
                labels=runner_shared.AGY_HOST_LABELS,
            )
            self.assertIn("finalize_refused", prompt)
            self.assertIn("plan content digest no longer matches the receipt", prompt)
            self.assertIn("Scope-Paths entry REMOVED since begin", prompt)

    def test_finalize_refused_is_an_ALLOWLISTED_prior_attempt_key(self):
        from agent_workflows import lane_containment

        self.assertIn("finalize_refused", lane_containment._PRIOR_ATTEMPT_SAFE_KEYS)

    def test_the_full_multi_finding_message_survives_the_projection_intact(self):
        from agent_workflows import lane_containment

        projected = lane_containment.prior_attempt_summary(
            {"number": 1, "finalize_refused": MEASURED_REFUSAL}, None
        )
        self.assertIsNotNone(projected)
        assert projected is not None
        self.assertEqual(MEASURED_REFUSAL, projected["finalize_refused"])

    def test_the_decision_lives_in_the_refusal_arm_and_not_a_later_sweep(self):
        import inspect

        src = inspect.getsource(runner_shared.execute_item_core)
        self.assertEqual(
            2,
            src.count("handle_finalize_refusal("),
            "BOTH refusal arms (lane and no-lane) must delegate to the one shared performer",
        )


class BothHostsBehaveIdentically(unittest.TestCase):
    """E-03/E-06: the incident was agy and the twin is where drift hides."""

    def test_both_hosts_execute_through_the_SAME_refusal_arm(self):
        import inspect

        for driver in (oc_driver, agy_driver):
            with self.subTest(driver=driver.__name__):
                src = inspect.getsource(driver)
                self.assertIn(
                    "runner_shared.execute_item_core(",
                    src,
                    f"{driver.__name__} must execute items through the shared core",
                )
                self.assertNotIn(
                    'attempt["finalize_refused"] = fin_msg',
                    src,
                    f"{driver.__name__} must not carry its own refusal arm",
                )

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
    """E-06 / E-03: dispatches are strictly bounded by budget + 1."""

    def test_total_dispatches_for_one_item_never_exceed_budget_plus_one(self):
        for budget in (0, 1, 2, 5):
            with self.subTest(budget=budget):
                item = _item()
                state = _state([item], retry_budget=budget)
                dispatches = 0
                while True:
                    dispatches += 1
                    dec = runner_shared.finalize_retry_decision(
                        item, state, MEASURED_REFUSAL
                    )
                    if not dec.retry:
                        break
                    item[runner_shared.FINALIZE_RETRY_COUNT_KEY] = dec.attempts + 1
                self.assertEqual(budget + 1, dispatches)


class TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains(unittest.TestCase):
    """E-02's DECIDED treatment of the orchestrator injection sites."""

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
        with tempfile.TemporaryDirectory() as temp:
            repo = self._repo_with_unfinished_child(temp)
            decision = self._decide(runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS, repo)
            self.assertEqual(runner_shared.ORCH_DISPATCH_TERMINATE, decision.outcome)
            self.assertEqual(runner_shared.ORCH_REASON_DEAD_CHILDREN, decision.reason)

    def test_the_exhausted_status_is_terminal_and_not_a_success(self):
        status = runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS
        self.assertIn(status, runner_shared.TERMINAL_STATES)
        self.assertNotIn(status, oc_driver.EXECUTION_SUCCESS_STATES)
        self.assertNotIn(status, runner_shared.SUCCESS_STATES)

    def test_a_retrying_child_is_not_terminal_which_is_what_makes_it_actionable(self):
        self.assertNotIn("queued", runner_shared.TERMINAL_STATES)

    def test_the_exhausted_status_keeps_the_manual_recovery_route(self):
        import inspect

        src = inspect.getsource(oc_driver.run_queue)
        self.assertIn(
            f'"{runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS}"',
            src,
            "the exhausted status must remain in --retry-incomplete's set",
        )


class ARefusedItemDoesNotSatisfyADependentEdge(unittest.TestCase):
    """A refused finalize does not satisfy a dependent edge."""

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

    def test_the_in_run_status_shortcut_is_STILL_GONE(self):
        import inspect

        src = inspect.getsource(oc_driver.edge_satisfied)
        executed_branch = src.split('if edge.kind == "executed":', 1)[1]
        executed_branch = executed_branch.split(
            "from agent_workflows import ipd_schema", 1
        )[0]
        self.assertNotIn(
            "by_id",
            executed_branch,
            "the `executed:` edge must stay disk-authoritative (maintainer ruling 2026-09-19); "
            "re-reading in-run status would re-admit `substantially-complete`",
        )

    def test_the_cascade_and_edge_gate_remain_ONE_shared_object_per_host(self):
        self.assertIs(oc_driver.edge_satisfied, agy_driver.edge_satisfied)
        self.assertIs(
            oc_driver.cascade_dependency_blocked, agy_driver.cascade_dependency_blocked
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
