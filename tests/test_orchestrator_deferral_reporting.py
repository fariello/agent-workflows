"""runghostid Order 01 (`zyw4n3`): a DEFERRED orchestrator must SAY SO, with a remedy.

WHAT THIS PINS, and why the defect needed pinning at all rather than being obvious.

The runner already computed a precise, typed reason for every orchestrator refusal
(`runner_shared.ORCH_REASON_*`, seven values) and then DISCARDED it on the path that matters. The
RECONSIDER (deferral) branch of `dispatch_orchestrator_item` appended its reason to `events.jsonl`
and wrote NO item field, and no read surface consumes `events.jsonl`; the TERMINATE branch wrote
`orchestrator_refusal_reason`/`orchestrator_refusal_detail`, which no RENDER surface reads. So the
summary for a run that did nothing carried a table row with an empty `Verify` column and not one word
saying the orchestrator was deferred, why, or what to do. Backlog `i2fjf8` is an operator hitting
exactly that.

The fix is delivery, not diagnosis: both branches now record `orchprobe` `r2i1b1`'s `Refusal`
(code/reason/remedy), which the summary's diagnostics block and `aw runs` already render for ANY
status. Hence the four subjects below.

  1. `DeferralRecordTests` - the RECONSIDER branch records the refusal AND still writes no status, so
     the item stays `queued` and a later iteration re-selects it. That invariant is the reason the
     three-way dispatch exists (`pgq326`): a terminal write here excluded an orchestrator whose
     children finished LATER IN THE SAME RUN.
  2. `TerminateRecordTests` - the TERMINATE branch records the SAME record, and the fields that
     already existed are untouched, because a live test and both hosts' `## Dependency blocks (why)`
     report section read them.
  3. `ReasonMappingTests` - every one of the seven reasons yields a SPECIFIC reason and a remedy that
     names an action; an unknown code is handled deliberately; and the two overlapping reason
     vocabularies cannot be confused for one another.
  4. `StaleDeferralRecordTests` - the record is CLEARED when the same item is re-dispatched, which is
     the hazard the deferral's transience creates and the one this module would be negligent to omit:
     a deferral that later RETIREs would otherwise leave a refusal on an `executed` item, and
     MEASURED on the real surfaces that renders a finished Set as `Outcome: PARTIAL` with a stale
     remedy telling the operator to run children that already ran.

FIXTURE-DRIVEN, NEVER AGAINST `.aw/records/runs/`. That tree is gitignored with zero tracked files and
`tests/test_run_viewer.py` records that it "is gitignored and absent in every fresh checkout", so a
test keyed to a live run would be unrunnable in CI and in every lane worktree the runner allocates.
Each case builds a temp repo and drives the REAL `dispatch_orchestrator_item`, following
`tests/test_orchestrator_retirement.py`'s `DispatchRunCase` recipe.
"""

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import render_stream as rstream
from agent_workflows import runner_shared as rs

PLAN = (
    "# IPD: synthetic {kind}\n\n"
    "- Date: 2026-09-08\n"
    "- Kind: {kind}\n"
    "- Id: {id6}\n"
    "- Set: {setid}\n"
    "- Order: {order}\n"
    "- Status: {status}\n\n"
    "## Child IPDs, sequence, and dependencies\n\n"
    "| Order | Id | Child | Depends on |\n"
    "|---|---|---|---|\n"
    "{rows}"
)

#: The two sets the dispatch is driven with, matching what both hosts pass.
TERMINAL = {"failed-safely", "dependency-blocked", "executed", "merge-refused"}
SUCCESS = {"executed"}


class DispatchFixture(unittest.TestCase):
    """A temp repo, a synthetic Set on disk, and a run directory. No live run state is read."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.run_dir = self.root / "run-deferral"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def write_plan(
        self, *, bucket, id6, order, status, kind, setid="zset", declared=()
    ):
        d = self.root / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        rows = "".join(f"| {tok} | x | x | x |\n" for tok in declared)
        path = d / f"20260908-{setid}-{order:02d}-{id6}-synthetic.ipd.md"
        path.write_text(
            PLAN.format(
                kind=kind, id6=id6, setid=setid, order=order, status=status, rows=rows
            ),
            encoding="utf-8",
        )
        return path

    def item(self, id6, action, status, *, position=1, setid="zset"):
        return {
            "position": position,
            "id6": id6,
            "setid": setid,
            "action": action,
            "kind": "orchestrator" if action == "orchestrate" else "child",
            "status": status,
            "dependencies": [],
            "attempts": [],
        }

    def dispatch(self, item, queue, *, terminal_status="dependency-blocked"):
        state = {
            "repo": str(self.root),
            "run_id": "run-deferral",
            "queue": queue,
        }
        decision = rs.dispatch_orchestrator_item(
            self.root,
            self.run_dir,
            state,
            item,
            actor="aw oc run model=test",
            terminal_states=TERMINAL,
            success_states=SUCCESS,
            terminal_status=terminal_status,
        )
        return decision, state

    def events(self):
        path = self.run_dir / "events.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def deferred_set(self):
        """A Set whose one child is queued-but-unfinished: the RECONSIDER case."""
        self.write_plan(
            bucket="pending",
            id6="orc001",
            order=0,
            status="approved",
            kind="orchestrator",
            declared=("01",),
        )
        self.write_plan(
            bucket="pending", id6="chi001", order=1, status="approved", kind="child"
        )
        orch = self.item("orc001", "orchestrate", "queued", position=1)
        child = self.item("chi001", "execute", "queued", position=2)
        return orch, [orch, child]


class DeferralRecordTests(DispatchFixture):
    """The RECONSIDER branch: record the refusal, and STILL write no status."""

    def test_a_deferred_orchestrator_carries_a_refusal_record(self):
        orch, queue = self.deferred_set()
        decision, _state = self.dispatch(orch, queue)

        self.assertEqual(decision.outcome, rs.ORCH_DISPATCH_RECONSIDER)
        self.assertEqual(decision.reason, rs.ORCH_REASON_UNFINISHED_CHILDREN)

        refusal = rstream.refusal_of_item(orch)
        self.assertIsNotNone(
            refusal,
            "a DEFERRED orchestrator must carry a refusal record; without it the reason reaches "
            "only events.jsonl, which no read surface consumes (this is the defect)",
        )
        self.assertEqual(refusal.code, rs.ORCH_REASON_UNFINISHED_CHILDREN)
        self.assertTrue(refusal.reason.strip())
        self.assertTrue(refusal.remedy.strip())

    def test_the_record_names_the_blocking_children_from_the_dispatch_detail(self):
        """The RUN-SPECIFIC half: a generic reason cannot name which child is blocking."""
        orch, queue = self.deferred_set()
        decision, _state = self.dispatch(orch, queue)
        refusal = rstream.refusal_of_item(orch)
        self.assertIn("chi001", refusal.reason)
        self.assertIn(decision.detail, refusal.reason)

    def test_the_deferral_still_writes_no_status_so_it_is_re_selected(self):
        """THE INVARIANT THIS PATH GUARDS. A terminal write here is `pgq326`'s measured defect."""
        orch, queue = self.deferred_set()
        self.dispatch(orch, queue)
        self.assertEqual(
            orch["status"],
            "queued",
            "the deferred item must stay `queued` so a later iteration re-tests it once its "
            "children finish; a terminal status excluded such an orchestrator forever",
        )
        for key in ("unsatisfied_dependencies", "unsatisfied_dependency_reasons"):
            self.assertNotIn(
                key,
                orch,
                "the RECONSIDER path must not write the TERMINATE path's dependency fields",
            )

    def test_the_orchestrator_deferred_event_keeps_its_existing_shape(self):
        """Additive: the record is written BESIDE the event, which 28+ on disk already use."""
        orch, queue = self.deferred_set()
        self.dispatch(orch, queue)
        deferred = [
            e for e in self.events() if e.get("event") == "orchestrator-deferred"
        ]
        self.assertEqual(len(deferred), 1)
        event = deferred[0]
        self.assertEqual(event["reason"], rs.ORCH_REASON_UNFINISHED_CHILDREN)
        self.assertIs(event["terminated"], False)
        self.assertEqual(event["unfinished_children"], [["chi001", "queued"]])
        # The RECONSIDER event deliberately carries NO `status`/`unauthored_rows` (the TERMINATE one
        # does), so the two events stay distinguishable.
        self.assertNotIn("status", event)
        self.assertNotIn("unauthored_rows", event)

    def test_the_record_type_is_the_one_imported_from_render_stream(self):
        """No look-alike defined locally.

        `r2i1b1` E-01 sites `Refusal` in `render_stream` because `runner_shared` imports that module
        at module level while it imports no first-party module at all, so the reverse edge would be
        circular. A second record shape in `runner_shared` is the exact divergence that plan exists to
        prevent, and every other assertion here would still pass with one.
        """
        orch, queue = self.deferred_set()
        self.dispatch(orch, queue)
        refusal = rstream.refusal_of_item(orch)
        self.assertIs(type(refusal), rstream.Refusal)
        self.assertIs(rs.REFUSAL_KEY, rstream.REFUSAL_KEY)
        self.assertNotIn(
            "Refusal",
            vars(rs),
            "`runner_shared` must neither define nor re-export `Refusal`: that would create the "
            "circular import `r2i1b1` sited the type in `render_stream` to avoid",
        )


class TerminateRecordTests(DispatchFixture):
    """The TERMINATE branch: the SAME record, and nothing existing disturbed."""

    def no_children_set(self):
        self.write_plan(
            bucket="pending",
            id6="orc406",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="noname",
            declared=("01",),
        )
        orch = self.item("orc406", "orchestrate", "queued", setid="noname")
        return orch, [orch]

    def test_a_terminated_orchestrator_carries_the_same_record(self):
        orch, queue = self.no_children_set()
        decision, _state = self.dispatch(orch, queue)
        self.assertEqual(decision.outcome, rs.ORCH_DISPATCH_TERMINATE)
        self.assertEqual(decision.reason, rs.ORCH_REASON_NO_CHILDREN)

        refusal = rstream.refusal_of_item(orch)
        self.assertIsNotNone(refusal)
        self.assertIs(type(refusal), rstream.Refusal)
        self.assertEqual(refusal.code, rs.ORCH_REASON_NO_CHILDREN)
        self.assertTrue(refusal.remedy.strip())
        self.assertEqual(orch["status"], "dependency-blocked")

    def test_the_bespoke_fields_a_live_test_reads_are_unchanged(self):
        """`tests/test_orchestrator_retirement.py` asserts both, so they cannot be dropped."""
        orch, queue = self.no_children_set()
        self.dispatch(orch, queue)
        self.assertEqual(
            orch["orchestrator_refusal_reason"], rs.ORCH_REASON_NO_CHILDREN
        )
        self.assertIn("noname", orch["orchestrator_refusal_detail"])

    def test_the_dependency_fields_the_report_section_reads_are_unchanged(self):
        """Both hosts' `## Dependency blocks (why)` section reads these two keys."""
        self.write_plan(
            bucket="pending",
            id6="orc002",
            order=0,
            status="approved",
            kind="orchestrator",
            declared=("01",),
        )
        self.write_plan(
            bucket="pending", id6="chi002", order=1, status="approved", kind="child"
        )
        orch = self.item("orc002", "orchestrate", "queued", position=1)
        # The child is unfinished on disk and ABSENT from the queue: nothing this run does can finish
        # it, so the dispatch terminates and NAMES the dependency.
        decision, _state = self.dispatch(orch, [orch])
        self.assertEqual(decision.reason, rs.ORCH_REASON_CHILDREN_NOT_IN_RUN)
        self.assertEqual(orch["unsatisfied_dependencies"], ["executed:chi002"])
        self.assertEqual(
            orch["unsatisfied_dependency_reasons"],
            # The reason names the child's PLAN STATUS, not its directory: retirement keys on the
            # `- Status:` field (measured; a file moved to `executed/` whose front matter still reads
            # `approved` is still unfinished).
            {"executed:chi002": "child chi002 is approved"},
        )
        self.assertIsNotNone(rstream.refusal_of_item(orch))

    def test_both_outcomes_use_one_record_shape(self):
        """The two halves of one function must not report differently, which was the defect."""
        deferred_orch, deferred_queue = self.deferred_set()
        self.dispatch(deferred_orch, deferred_queue)
        terminated_orch, terminated_queue = self.no_children_set()
        self.dispatch(terminated_orch, terminated_queue)

        a = rstream.refusal_of_item(deferred_orch)
        b = rstream.refusal_of_item(terminated_orch)
        self.assertEqual(type(a), type(b))
        self.assertEqual(
            sorted(a.to_dict().keys()),
            sorted(b.to_dict().keys()),
            "one record shape across both dispatch outcomes",
        )


class ReasonMappingTests(unittest.TestCase):
    """Every typed reason maps to a SPECIFIC human reason and an ACTIONABLE remedy."""

    #: The seven values `decide_orchestrator_dispatch` can put on a refusal.
    ALL_REASONS = (
        rs.ORCH_REASON_UNFINISHED_CHILDREN,
        rs.ORCH_REASON_DEAD_CHILDREN,
        rs.ORCH_REASON_CHILDREN_NOT_IN_RUN,
        rs.ORCH_REASON_NO_CHILDREN,
        rs.ORCH_REASON_UNAUTHORED_CHILD_ROWS,
        rs.ORCH_REASON_FINALIZE_REFUSED,
        rs.ORCH_REASON_NO_ORCHESTRATOR,
    )

    def test_every_reason_is_mapped_and_distinct(self):
        self.assertEqual(len(set(self.ALL_REASONS)), 7)
        seen_reasons, seen_remedies = set(), set()
        for code in self.ALL_REASONS:
            reason, remedy = rs.orchestrator_refusal_text(code)
            self.assertTrue(reason.strip(), code)
            self.assertTrue(remedy.strip(), code)
            self.assertNotIn(
                "NOT RECOGNIZE",
                reason,
                f"{code} fell through to the unknown-code fallback, which is the generic string "
                "this mapping exists to avoid",
            )
            seen_reasons.add(reason)
            seen_remedies.add(remedy)
        self.assertEqual(len(seen_reasons), 7, "no two reasons may share prose")
        self.assertEqual(len(seen_remedies), 7, "no two remedies may share prose")

    def test_every_remedy_names_a_concrete_action(self):
        """The remedy is the half the backlog item actually asked for."""
        verbs = (
            "approve",
            "author",
            "run",
            "read",
            "check",
            "let",
            "resolve",
            "name",
            "add",
        )
        for code in self.ALL_REASONS:
            _reason, remedy = rs.orchestrator_refusal_text(code)
            self.assertTrue(
                any(v in remedy.lower() for v in verbs),
                f"{code}'s remedy names no action: {remedy!r}",
            )

    def test_no_remedy_suggests_full_auto(self):
        """OQ-01, resolved: NEVER offer an approval bypass inside a refusal message.

        `--full-auto` clears a `reviewed` plan to `auto-approved`, so naming it as the remedy for
        "children are not approved" offers to bypass the approval gate at the exact moment an operator
        is frustrated that nothing ran. A remedy must name the CONSTRUCTIVE action, never a shortcut
        past the thing that refused.
        """
        for code in self.ALL_REASONS:
            reason, remedy = rs.orchestrator_refusal_text(code)
            self.assertNotIn("--full-auto", remedy, code)
            self.assertNotIn("--full-auto", reason, code)

    def test_no_remedy_names_a_host_command(self):
        """The dispatch is shared and has no `HostLabels`, so a host command here would be a guess.

        `probe_refusal_remedy` takes the host as an argument precisely because its caller has one;
        this function's callers do not, and its docstring records that a remedy naming the WRONG host
        "is a defect even though the identity check passes".
        """
        for code in self.ALL_REASONS:
            _reason, remedy = rs.orchestrator_refusal_text(code)
            self.assertNotIn("aw oc run", remedy, code)
            self.assertNotIn("aw agy run", remedy, code)

    def test_no_remedy_tells_the_reader_to_delete_the_thing_that_refused(self):
        """`m7gvuz` E-06's discipline: a prohibition-only message gets complied with by DELETION."""
        unauthored = rs.orchestrator_refusal_text(rs.ORCH_REASON_UNAUTHORED_CHILD_ROWS)[
            1
        ]
        self.assertIn("author the missing child", unauthored.lower())
        dead = rs.orchestrator_refusal_text(rs.ORCH_REASON_DEAD_CHILDREN)[1]
        self.assertIn("do not remove the child's row", dead.lower())

    def test_the_dead_children_remedy_covers_the_awaiting_approval_case(self):
        """The reason NAME is narrower than the condition, and the remedy must match the condition.

        `children-terminally-failed` reads like a crash, but `reviewed` is in `TERMINAL_STATES` and is
        the status that actually arrives here: MEASURED end to end on the backlog item's own scenario
        (an approved orchestrator over a `reviewed` child), the dispatch produced exactly this code.
        So the dominant case is a child AWAITING APPROVAL, and a remedy saying only "fix what failed"
        would send an operator hunting a failure that does not exist.
        """
        reason, remedy = rs.orchestrator_refusal_text(rs.ORCH_REASON_DEAD_CHILDREN)
        self.assertIn("not approved", reason.lower())
        self.assertIn("reviewed", remedy)
        self.assertIn("aw ipd set approved", remedy)
        self.assertIn(
            "outcome record", remedy, "the genuine-failure case is still covered"
        )

    def test_an_unknown_code_is_reported_verbatim_and_never_empty(self):
        """Decided and recorded: report, do not raise. A raise here would be RUN-FATAL."""
        reason, remedy = rs.orchestrator_refusal_text("some-future-reason")
        self.assertIn("some-future-reason", reason)
        self.assertIn("some-future-reason", remedy)
        self.assertIn("NOT RECOGNIZE", reason)
        self.assertTrue(remedy.strip())
        # Constructible, so an unknown code still produces a renderable record rather than raising
        # inside a host's run loop.
        rec = rstream.Refusal(code="some-future-reason", reason=reason, remedy=remedy)
        self.assertEqual(rec.code, "some-future-reason")

    def test_an_empty_reason_is_still_handled(self):
        reason, remedy = rs.orchestrator_refusal_text("")
        self.assertTrue(reason.strip())
        self.assertTrue(remedy.strip())

    def test_the_mapping_is_keyed_on_ORCH_REASON_and_the_other_vocabulary_is_translated(
        self,
    ):
        """TWO overlapping vocabularies exist, and one pair differs only in WORD ORDER.

        `RETIRE_REFUSED_*` is what `evaluate_set_retirement` produces; `ORCH_REASON_*` is what
        `decide_orchestrator_dispatch` writes. They share three values verbatim and carry the
        near-miss pair `unfinished-children` versus `children-unfinished`, which is exactly the shape
        that makes a dict-keyed mapping silently miss. Assert the translation rather than assuming it:
        if a future branch forwards an untranslated value, this fails instead of the mapping quietly
        degrading to its unknown-code fallback.
        """
        retire = {
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            rs.RETIRE_REFUSED_NO_CHILDREN,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            rs.RETIRE_REFUSED_NO_ORCHESTRATOR,
        }
        orch = set(self.ALL_REASONS)
        self.assertEqual(
            retire & orch,
            {"no-children", "no-orchestrator", "unauthored-child-rows"},
            "the three shared values",
        )
        # THE NEAR MISS, asserted explicitly so a future rename cannot quietly align them.
        self.assertEqual(rs.RETIRE_REFUSED_UNFINISHED_CHILDREN, "unfinished-children")
        self.assertEqual(rs.ORCH_REASON_UNFINISHED_CHILDREN, "children-unfinished")
        self.assertNotEqual(
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN, rs.ORCH_REASON_UNFINISHED_CHILDREN
        )
        # The one value that is NOT shared must therefore be unmapped, which is what proves the
        # mapping is keyed on `ORCH_REASON_*` and not on the union of both vocabularies.
        unshared_reason, _ = rs.orchestrator_refusal_text(
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN
        )
        self.assertIn("NOT RECOGNIZE", unshared_reason)

    def test_the_translation_is_asserted_on_the_real_decider(self):
        """Every `RETIRE_REFUSED_*` branch in `decide_orchestrator_dispatch` is translated."""
        import inspect

        src = inspect.getsource(rs.decide_orchestrator_dispatch)
        # Each comparison against a RETIRE_REFUSED_* constant must return an ORCH_REASON_* value.
        for name in (
            "RETIRE_REFUSED_NO_CHILDREN",
            "RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS",
            "RETIRE_REFUSED_NO_ORCHESTRATOR",
        ):
            self.assertIn(name, src)
        self.assertNotIn(
            "reason=RETIRE_REFUSED",
            src.replace(" ", ""),
            "a branch forwarding an untranslated RETIRE_REFUSED_* value as the dispatch reason "
            "would reach the reason mapping under the wrong vocabulary",
        )


class StaleDeferralRecordTests(DispatchFixture):
    """A deferral is TRANSIENT, so its record must not survive the item's next dispatch.

    THE HAZARD, MEASURED rather than reasoned. `render_run_summary_table`'s `COMPLETED` branch
    contains `not any(refusal_of_item(it) ...)` and `run_selection_policy.derive_item_disposition`
    gives a recorded refusal ABSOLUTE precedence, so a refusal left over from a deferral on an item
    that later reached `executed` renders a finished Set as `Outcome: PARTIAL` and prints a stale
    remedy telling the operator to run children that already ran. A false alarm on a green run is
    worse than the silence the record exists to remove.
    """

    def finish_the_child(self, child):
        """Make the child EXECUTED as a later iteration of the same run would see it.

        BOTH the plan's `- Status:` AND its directory, because retirement keys on the STATUS FIELD:
        measured, moving the file to `executed/` while its front matter still reads `approved` leaves
        `evaluate_set_retirement` refusing with `unfinished-children` and "chi001 (approved)". A
        fixture that moved the file only would therefore never reach the RETIRE branch this class is
        about, and would have looked like a product defect.
        """
        pending = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260908-zset-01-chi001-synthetic.ipd.md"
        )
        executed_dir = self.root / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)
        text = pending.read_text(encoding="utf-8").replace(
            "- Status: approved", "- Status: executed"
        )
        (executed_dir / pending.name).write_text(text, encoding="utf-8")
        pending.unlink()
        child["status"] = "executed"

    def retire(self, orch, queue):
        """Dispatch with the RETIREMENT TRANSITION stubbed to succeed.

        The transition itself commits in a throwaway git worktree, which is `orchretire` 02's subject
        and not this plan's; `tests/test_orchestrator_retirement.py` stubs it for the same reason. What
        matters here is the branch the dispatch TAKES and what it leaves on the item.
        """
        from unittest.mock import patch

        from agent_workflows import ipd_lifecycle as LC

        class _Ok:
            exit_code = 0
            message = "retired"

        with patch.object(LC, "retire_orchestrator", return_value=_Ok()):
            return self.dispatch(orch, queue)

    def test_a_deferral_that_later_retires_leaves_no_refusal_behind(self):
        orch, queue = self.deferred_set()
        child = queue[1]

        self.dispatch(orch, queue)
        self.assertIsNotNone(
            rstream.refusal_of_item(orch), "the deferral records a refusal"
        )

        self.finish_the_child(child)
        decision, _state = self.retire(orch, queue)
        self.assertEqual(
            decision.outcome,
            rs.ORCH_DISPATCH_RETIRE,
            "with its child executed the orchestrator is now eligible to retire",
        )
        self.assertEqual(orch["status"], "executed")
        self.assertIsNone(
            rstream.refusal_of_item(orch),
            "a refusal from the earlier DEFERRAL must not survive onto an item this run went on to "
            "retire; it would render a finished Set as PARTIAL with a stale remedy",
        )

    def test_the_summary_reports_a_completed_set_as_completed(self):
        """The end-to-end consequence, on the real renderer."""
        orch, queue = self.deferred_set()
        child = queue[1]
        _decision, state = self.dispatch(orch, queue)

        self.finish_the_child(child)
        child["attempts"] = [{"n": 1}]
        self.retire(orch, queue)

        table = rstream.render_run_summary_table(
            state, pal=rstream.Palette(False), use_unicode=False
        )
        outcome = [ln for ln in table.splitlines() if "Outcome:" in ln][0]
        self.assertIn(
            "COMPLETED",
            outcome,
            "a Set whose orchestrator retired and whose child executed is COMPLETED; a stale "
            f"deferral record renders it PARTIAL instead. Got: {outcome.strip()!r}",
        )
        self.assertNotIn("Diagnostics", table)

    def test_a_re_dispatch_replaces_rather_than_accumulates(self):
        """The record always describes the CURRENT disposition, never a previous one."""
        orch, queue = self.deferred_set()
        self.dispatch(orch, queue)
        first = rstream.refusal_of_item(orch)
        self.assertEqual(first.code, rs.ORCH_REASON_UNFINISHED_CHILDREN)

        # The child dies: the same item now terminates for a DIFFERENT reason.
        queue[1]["status"] = "failed-safely"
        decision, _state = self.dispatch(orch, queue)
        self.assertEqual(decision.reason, rs.ORCH_REASON_DEAD_CHILDREN)
        second = rstream.refusal_of_item(orch)
        self.assertEqual(second.code, rs.ORCH_REASON_DEAD_CHILDREN)
        self.assertNotIn(
            first.reason,
            second.reason,
            "the stale deferral prose must not be carried into the new refusal",
        )


class RenderedSurfaceTests(DispatchFixture):
    """The deferral reason and remedy actually REACH the read surfaces (the item's complaint)."""

    def test_the_summary_diagnostics_block_shows_the_reason_and_the_remedy(self):
        orch, queue = self.deferred_set()
        _decision, state = self.dispatch(orch, queue)
        table = rstream.render_run_summary_table(
            state, pal=rstream.Palette(False), use_unicode=False
        )
        self.assertIn("Diagnostics", table)
        self.assertIn("DEFERRED", table)
        self.assertIn("remedy:", table)
        self.assertIn("chi001", table)

    def test_a_deferral_is_not_reported_as_a_failure(self):
        """A deferral is an explained NO-OP, not a red run."""
        orch, queue = self.deferred_set()
        _decision, state = self.dispatch(orch, queue)
        table = rstream.render_run_summary_table(
            state, pal=rstream.Palette(False), use_unicode=False
        )
        outcome = [ln for ln in table.splitlines() if "Outcome:" in ln][0]
        self.assertNotIn("FAILED", outcome)
        self.assertNotIn("STRANDED", outcome)
        self.assertEqual(orch["status"], "queued")

    def test_the_end_of_run_disposition_summary_sources_the_remedy(self):
        """`run_selection_policy` reads the record through `r2i1b1`'s ONE reader."""
        from agent_workflows.run_selection_policy import (
            derive_item_disposition,
            render_disposition_summary,
        )

        orch, queue = self.deferred_set()
        self.dispatch(orch, queue)
        decided = derive_item_disposition(orch, rstream.refusal_of_item)
        self.assertEqual(decided.code, rs.ORCH_REASON_UNFINISHED_CHILDREN)
        self.assertTrue(decided.remedy)
        lines = "\n".join(
            render_disposition_summary(queue, refusal_reader=rstream.refusal_of_item)
        )
        self.assertIn(rs.ORCH_REASON_UNFINISHED_CHILDREN, lines)
        self.assertIn("remedy:", lines)

    def test_aw_runs_counts_a_deferred_orchestrator_as_an_issue(self):
        """`r2i1b1` E-04 routed the ONE `Issue` predicate through the refusal record.

        Driven through the REAL predicate on a CLEAN audit (no artifact discrepancy at all), so the
        only thing that can make it report an issue is the refusal this plan writes. That is the
        assertion that proves the record reaches `aw runs` and its `--json`/`--agent` payloads, which
        all five call sites now share.
        """
        from agent_workflows import artifact_audit
        from agent_workflows import run_viewer

        orch, queue = self.deferred_set()
        self.dispatch(orch, queue)

        clean_audit = artifact_audit.ArtifactAudit(
            id6="orc001", stem="20260908-zset-00-orc001-synthetic", run_status="queued"
        )
        step = run_viewer.StepSummary(
            position=1,
            id6="orc001",
            setid="zset",
            action="orchestrate",
            status="queued",
            configured_file="",
            stem="20260908-zset-00-orc001-synthetic",
            refusal=orch.get(rs.REFUSAL_KEY),
        )
        self.assertFalse(
            run_viewer.step_has_issue(clean_audit, None),
            "control: with no refusal in hand the same clean audit is NOT an issue, so the "
            "assertion below is attributable to the refusal alone",
        )
        self.assertTrue(
            run_viewer.step_has_issue(clean_audit, step),
            "a refused item must read as an issue in `aw runs`, including its machine surfaces",
        )
        reasons = run_viewer.step_issue_reasons(clean_audit, step)
        self.assertTrue(any(r.startswith("refused:") for r in reasons), reasons)
        self.assertIn("chi001", " ".join(reasons))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
