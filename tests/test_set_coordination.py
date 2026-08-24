"""Tests for the Set-coordination layer (execset Order 02, `3m4e54`).

V-01: ledger-schema extension (versioning + 9 new kinds pos/neg + investigator role) AND the
      separate `set_`-prefixed Set state machine (transition table, no-collision, completion refusal,
      illegal actors/edges, derivation).
V-02: the exact four-clause no-stop classifier truth table + STOP-and-report containment +
      unknown-outcome reconciliation routing.
V-03: local projections, tracked walkthrough, attention-valid blocked backlog promotion with a
      D<number> Gate-Ref (resume NOT in Gate-Ref), close-on-answer, and recovery promotion.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import run_ledger_schema as S
from agent_workflows import set_state as SS
from agent_workflows import set_stop_policy as P
from agent_workflows import set_records as R
from agent_workflows import run_state as RS
from agent_workflows import verify_roles as VR
from agent_workflows import backlog as B


def _env(kind, actor="runtime", ver=2, seq=0):
    return {
        "schema_version": ver,
        "kind": kind,
        "seq": seq,
        "run_id": "run-deadbeef",
        "actor": actor,
        "timestamp": "2026-08-24T00:00:00Z",
        "parent": "",
    }


# ==================================================================================================
# V-01 (a): ledger schema
# ==================================================================================================


class LedgerVersioningV01(unittest.TestCase):
    def test_v1_ledger_still_validates(self):
        rec = _env("run", ver=1)
        rec.update(
            {
                "workflow_digest": "a" * 64,
                "requirement_digest": "b" * 64,
                "repo": "r",
                "head": "h",
            }
        )
        self.assertTrue(S.validate_record(rec).ok)

    def test_supported_versions(self):
        self.assertEqual(S.SUPPORTED_SCHEMA_VERSIONS, frozenset((1, 2)))
        self.assertEqual(S.LEDGER_SCHEMA_VERSION, 2)

    def test_v2_only_kind_rejected_at_v1(self):
        rec = _env("autonomous_decision", actor="coordinator", ver=1)
        rec.update(
            {
                "decision_id": "D1",
                "selected_option": "x",
                "confidence": "high",
                "consultation_preferred": False,
                "reversible": True,
                "prev": "",
            }
        )
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        self.assertIn("RL-E018", {f.code for f in res.findings})

    def test_unsupported_version_rejected(self):
        rec = _env("run", ver=999)
        rec.update(
            {
                "workflow_digest": "a",
                "requirement_digest": "b",
                "repo": "r",
                "head": "h",
            }
        )
        res = S.validate_record(rec)
        self.assertIn("RL-E012", {f.code for f in res.findings})

    def test_investigator_role_accepted_and_reconciled(self):
        self.assertIn("investigator", S.ROLES)
        self.assertEqual(VR.ROLE_INVESTIGATOR, "investigator")
        self.assertIn(VR.ROLE_INVESTIGATOR, S.ROLES)
        rec = _env("tool_event", actor="investigator")
        rec.update(
            {"argv": ["ls"], "cwd": ".", "exit_code": 0, "stdout_sha256": "a" * 64}
        )
        self.assertTrue(S.validate_record(rec).ok)


class NewKindsPosNegV01(unittest.TestCase):
    """Each of the nine new kinds gets a positive AND a negative schema test."""

    def _base(self, kind, actor):
        return _env(kind, actor=actor)

    def test_question_raised(self):
        ok = self._base("question_raised", "coordinator")
        ok.update({"question_id": "Q1", "context": "c", "affected_nodes": ["a:E-01"]})
        self.assertTrue(S.validate_record(ok).ok)
        bad = dict(ok)
        del bad["context"]
        self.assertFalse(S.validate_record(bad).ok)

    def test_question_disposition(self):
        ok = self._base("question_disposition", "coordinator")
        ok.update(
            {"question_id": "Q1", "disposition": "decided_autonomously", "prev": ""}
        )
        self.assertTrue(S.validate_record(ok).ok)
        bad = dict(ok, disposition="nonsense")
        res = S.validate_record(bad)
        self.assertFalse(res.ok)
        self.assertIn("RL-E050", {f.code for f in res.findings})

    def test_human_answer_authority(self):
        ok = self._base("human_answer", "human")
        ok.update({"question_id": "Q1", "answer": "yes"})
        self.assertTrue(S.validate_record(ok).ok)
        bad = self._base("human_answer", "coordinator")
        bad.update({"question_id": "Q1", "answer": "yes"})
        res = S.validate_record(bad)
        self.assertFalse(res.ok)
        self.assertIn("RL-E051", {f.code for f in res.findings})

    def test_autonomous_decision(self):
        ok = self._base("autonomous_decision", "coordinator")
        ok.update(
            {
                "decision_id": "D1",
                "selected_option": "x",
                "confidence": "high",
                "consultation_preferred": True,
                "reversible": True,
                "prev": "",
            }
        )
        self.assertTrue(S.validate_record(ok).ok)
        bad = self._base("autonomous_decision", "verifier")  # wrong authority
        bad.update(
            {
                "decision_id": "D1",
                "selected_option": "x",
                "confidence": "high",
                "consultation_preferred": True,
                "reversible": True,
                "prev": "",
            }
        )
        res = S.validate_record(bad)
        self.assertFalse(res.ok)
        self.assertIn("RL-E057", {f.code for f in res.findings})

    def test_scope_deferred(self):
        ok = self._base("scope_deferred", "coordinator")
        ok.update({"scope": "a:E-03", "reason": "no default", "blocks": ["a:E-03"]})
        self.assertTrue(S.validate_record(ok).ok)
        bad = dict(ok)
        del bad["blocks"]
        self.assertFalse(S.validate_record(bad).ok)

    def test_work_claim(self):
        ok = self._base("work_claim", "coordinator")
        ok.update({"lane_id": "a:E-01", "node": "a:E-01"})
        self.assertTrue(S.validate_record(ok).ok)
        bad = dict(ok)
        del bad["node"]
        self.assertFalse(S.validate_record(bad).ok)

    def test_lane_outcome(self):
        ok = self._base("lane_outcome", "coordinator")
        ok.update({"lane_id": "a:E-01", "outcome": "performed"})
        self.assertTrue(S.validate_record(ok).ok)
        bad = dict(ok, outcome="exploded")
        res = S.validate_record(bad)
        self.assertFalse(res.ok)
        self.assertIn("RL-E052", {f.code for f in res.findings})

    def test_integration_result(self):
        ok = self._base("integration_result", "coordinator")
        ok.update({"lane_id": "a:E-01", "result": "integrated"})
        self.assertTrue(S.validate_record(ok).ok)
        bad = self._base("integration_result", "executor")  # wrong authority
        bad.update({"lane_id": "a:E-01", "result": "integrated"})
        res = S.validate_record(bad)
        self.assertFalse(res.ok)
        self.assertIn("RL-E054", {f.code for f in res.findings})

    def test_set_checkpoint(self):
        ok = self._base("set_checkpoint", "coordinator")
        ok.update({"set_id": "execset", "set_state": "set_running"})
        self.assertTrue(S.validate_record(ok).ok)
        bad = dict(ok, set_state="running")  # a run_state token, not a set_ token
        res = S.validate_record(bad)
        self.assertFalse(res.ok)
        self.assertIn("RL-E055", {f.code for f in res.findings})


# ==================================================================================================
# V-01 (b): Set state machine
# ==================================================================================================


class SetStateMachineV01(unittest.TestCase):
    def test_no_collision_with_run_state(self):
        self.assertTrue(SS.ALL_SET_STATES.isdisjoint(RS.ALL_STATES))
        for s in SS.ALL_SET_STATES:
            self.assertTrue(s.startswith("set_"))

    def test_legal_edges(self):
        for src, tgt in [
            (SS.SET_PLANNED, SS.SET_RUNNING),
            (SS.SET_RUNNING, SS.SET_WAITING_INPUT),
            (SS.SET_WAITING_INPUT, SS.SET_RUNNING),
            (SS.SET_RUNNING, SS.SET_PARTIAL),
            (SS.SET_PARTIAL, SS.SET_RUNNING),
            (SS.SET_RUNNING, SS.SET_FAILED),
            (SS.SET_RUNNING, SS.SET_CANCELLED),
        ]:
            res = SS.validate_set_transition(src, tgt, "coordinator")
            self.assertTrue(
                res.ok,
                msg="{0}->{1} should be legal: {2}".format(src, tgt, res.findings),
            )

    def test_illegal_edge_rejected(self):
        res = SS.validate_set_transition(SS.SET_PLANNED, SS.SET_COMPLETE, "coordinator")
        self.assertFalse(res.ok)
        self.assertIn("SS-ILLEGAL-TRANSITION", {f.code for f in res.findings})

    def test_illegal_actor_rejected(self):
        res = SS.validate_set_transition(SS.SET_RUNNING, SS.SET_COMPLETE, "executor")
        self.assertFalse(res.ok)
        self.assertIn("SS-UNAUTHORIZED-ACTOR", {f.code for f in res.findings})

    def test_completion_refused_without_all_verified(self):
        res = SS.validate_set_transition(
            SS.SET_RUNNING,
            SS.SET_COMPLETE,
            "coordinator",
            predicate_values={"all_required_children_verified_terminal": False},
        )
        self.assertFalse(res.ok)
        self.assertIn("SS-COMPLETION-REFUSED", {f.code for f in res.findings})
        with self.assertRaises(SS.SetCompletionRefusedError):
            SS.check_set_transition(
                SS.SET_RUNNING,
                SS.SET_COMPLETE,
                "coordinator",
                predicate_values={"all_required_children_verified_terminal": False},
            )

    def test_completion_allowed_when_all_verified(self):
        res = SS.validate_set_transition(
            SS.SET_RUNNING,
            SS.SET_COMPLETE,
            "coordinator",
            predicate_values={"all_required_children_verified_terminal": True},
        )
        self.assertTrue(res.ok)

    def test_terminal_state_immutable(self):
        res = SS.validate_set_transition(SS.SET_COMPLETE, SS.SET_RUNNING, "coordinator")
        self.assertFalse(res.ok)
        self.assertIn("SS-TERMINAL-STATE", {f.code for f in res.findings})

    def test_human_can_cancel_coordinator_authority_default(self):
        # human authorized for cancellation
        self.assertTrue(
            SS.validate_set_transition(SS.SET_RUNNING, SS.SET_CANCELLED, "human").ok
        )
        # human NOT authorized to drive planned->running (coordinator-only authority)
        self.assertFalse(
            SS.validate_set_transition(SS.SET_PLANNED, SS.SET_RUNNING, "human").ok
        )

    def test_derivation(self):
        self.assertEqual(
            SS.derive_set_state(
                started=True,
                any_required_deferred=False,
                all_required_verified_terminal=True,
                waiting_on_human=False,
                unrecoverable=False,
            ),
            SS.SET_COMPLETE,
        )
        self.assertEqual(
            SS.derive_set_state(
                started=True,
                any_required_deferred=True,
                all_required_verified_terminal=False,
                waiting_on_human=False,
                unrecoverable=False,
            ),
            SS.SET_PARTIAL,
        )
        # complete requires no deferral even if all-verified flag is set
        self.assertEqual(
            SS.derive_set_state(
                started=True,
                any_required_deferred=True,
                all_required_verified_terminal=True,
                waiting_on_human=False,
                unrecoverable=False,
            ),
            SS.SET_PARTIAL,
        )


# ==================================================================================================
# V-02: no-stop classifier truth table
# ==================================================================================================


class ClassifierV02(unittest.TestCase):
    def _q(self, **kw):
        base = dict(
            needs_human=True,
            has_robust_decision=False,
            can_defer_subgraph=False,
            can_defer_ipd=False,
        )
        base.update(kw)
        return P.QuestionSituation(**base)

    def test_predicate_only_all_four(self):
        # Exhaustive 4-bit truth table: hard_stop true iff all four clauses true.
        for nh in (False, True):
            for nr in (False, True):
                for cs in (False, True):
                    for ci in (False, True):
                        expected = nh and nr and cs and ci
                        got = P.hard_stop_predicate(
                            needs_human=nh,
                            no_robust_decision=nr,
                            cannot_defer_subgraph=cs,
                            cannot_defer_ipd=ci,
                        )
                        self.assertEqual(got, expected)

    def test_robust_decision_never_stops(self):
        r = P.classify(self._q(has_robust_decision=True))
        self.assertEqual(r.action, P.ACTION_DECIDE)
        self.assertFalse(r.hard_stop)

    def test_trivial_question_no_human_proceeds(self):
        r = P.classify(self._q(needs_human=False))
        self.assertEqual(r.action, P.ACTION_DECIDE)
        self.assertFalse(r.hard_stop)

    def test_defer_subgraph_beats_stop(self):
        r = P.classify(self._q(can_defer_subgraph=True))
        self.assertEqual(r.action, P.ACTION_DEFER_SUBGRAPH)
        self.assertFalse(r.hard_stop)

    def test_defer_ipd_beats_stop(self):
        r = P.classify(self._q(can_defer_ipd=True))
        self.assertEqual(r.action, P.ACTION_DEFER_IPD)
        self.assertFalse(r.hard_stop)

    def test_drain_then_stop(self):
        r = P.classify(self._q(independent_frontier=("a:E-01", "b:E-02")))
        self.assertEqual(r.action, P.ACTION_DRAIN_THEN_STOP)
        self.assertTrue(r.hard_stop)
        self.assertEqual(r.drain_first, ("a:E-01", "b:E-02"))

    def test_hard_stop_only_when_all_four_and_no_frontier(self):
        r = P.classify(self._q())
        self.assertEqual(r.action, P.ACTION_HARD_STOP)
        self.assertTrue(r.hard_stop)

    def test_release_approval_cannot_be_synthesized(self):
        # A release-approval question (needs_human, no robust default, cannot defer) MUST stop, never
        # auto-decide.
        r = P.classify(self._q())
        self.assertTrue(r.hard_stop)
        self.assertNotEqual(r.action, P.ACTION_DECIDE)

    def test_unknown_outcome_routes_to_reconcile(self):
        r = P.classify(self._q(is_unknown_outcome=True))
        self.assertEqual(r.action, P.ACTION_RECONCILE_UNKNOWN)
        self.assertFalse(r.hard_stop)

    def test_stop_containment_child_scope(self):
        c = P.contain_child_stop("If X is absent, STOP and report to the user.")
        self.assertTrue(c.is_stop_instruction)
        self.assertEqual(c.scope, "child")
        self.assertFalse(P.contain_child_stop("carry on").is_stop_instruction)

    def test_frontier_after_drain(self):
        self.assertEqual(P.frontier_after_drain(("a", "b", "c"), ("b",)), ("a", "c"))


# ==================================================================================================
# V-03: durable + inspectable records
# ==================================================================================================


class RecordsV03(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / ".aw" / "records" / "walkthroughs").mkdir(parents=True)
        (self.root / ".aw" / "records" / "backlog").mkdir(parents=True)
        self.records = [
            {
                "kind": "autonomous_decision",
                "decision_id": "D1",
                "selected_option": "reuse X",
                "confidence": "high",
                "consultation_preferred": True,
                "reversible": True,
                "prev": "",
                "timestamp": "2026-08-24T00:00:00Z",
                "actor": "coordinator",
            },
            {
                "kind": "question_raised",
                "question_id": "Q1",
                "context": "ambiguous target repo",
                "affected_nodes": ["a:E-02"],
                "timestamp": "2026-08-24T00:00:00Z",
                "actor": "coordinator",
            },
            {
                "kind": "scope_deferred",
                "scope": "a:E-03",
                "reason": "no robust default",
                "blocks": ["a:E-03"],
                "timestamp": "2026-08-24T00:00:00Z",
                "actor": "coordinator",
            },
        ]

    def test_local_projections_written(self):
        proj = R.write_local_projections(
            self.root, "exec-set", "run-abcdef01", self.records
        )
        self.assertTrue(proj.decisions_path.exists())
        self.assertTrue(proj.open_questions_path.exists())
        self.assertTrue(proj.deferred_work_path.exists())
        dtext = proj.decisions_path.read_text()
        self.assertIn("D1", dtext)
        self.assertIn("consultation_preferred", dtext)
        self.assertIn("Q1", proj.open_questions_path.read_text())
        self.assertIn("a:E-03", proj.deferred_work_path.read_text())

    def test_superseded_decision_marked(self):
        recs = list(self.records) + [
            {
                "kind": "autonomous_decision",
                "decision_id": "D2",
                "selected_option": "reverse D1",
                "confidence": "high",
                "consultation_preferred": False,
                "reversible": True,
                "prev": "D1",
                "timestamp": "2026-08-24T01:00:00Z",
                "actor": "coordinator",
            }
        ]
        text = R.render_decisions(recs)
        self.assertIn("## D1 (SUPERSEDED)", text)

    def test_answered_question_not_open(self):
        recs = list(self.records) + [
            {
                "kind": "human_answer",
                "question_id": "Q1",
                "answer": "repo X",
                "timestamp": "2026-08-24T01:00:00Z",
                "actor": "human",
            }
        ]
        self.assertIn("No unresolved questions", R.render_open_questions(recs))

    def test_walkthrough_conformant(self):
        from agent_workflows import artifact_naming as N

        body = R.render_walkthrough(
            set_id="execset",
            run_id="run-abcdef01",
            checkpoint="partial",
            records=self.records,
        )
        wp = R.write_walkthrough(
            self.root,
            set_id="execset",
            order=2,
            id6="3m4e54",
            slug="partial",
            body=body,
        )
        self.assertTrue(wp.exists())
        self.assertTrue(N.is_clustered_conformant(wp.name, expected_type="walkthrough"))

    def test_backlog_promotion_valid_and_resume_not_in_gate_ref(self):
        pr = R.promote_question_to_backlog(
            self.root,
            decision_number=1,
            summary="Resolve ambiguous target repo",
            resume_command="aw ipd execute-set execset --resume",
            context="which repo?",
            set_id="execset",
        )
        text = pr.path.read_text()
        item = B.parse_item(text)
        self.assertEqual(item.status, "blocked")
        self.assertEqual(item.gate_kind, "decision")
        self.assertEqual(item.gate_ref, "D1")
        # resume command is in the BODY, not the Gate-Ref.
        self.assertNotIn("execute-set execset --resume", item.gate_ref or "")
        self.assertIn("aw ipd execute-set execset --resume", text)
        # passes backlog validation.
        self.assertEqual(B.validate_item(pr.path, text), [])

    def test_close_on_answer_transitions_blocked_to_done(self):
        pr = R.promote_question_to_backlog(
            self.root,
            decision_number=2,
            summary="Answered question",
            resume_command="aw ipd execute-set execset --resume",
            set_id="execset",
        )
        newp = R.close_on_answer(self.root, pr.path)
        self.assertEqual(newp.parent.name, "done")
        item = B.parse_item(newp.read_text())
        self.assertEqual(item.status, "done")
        self.assertIsNone(item.gate_kind)
        self.assertEqual(B.validate_item(newp, newp.read_text()), [])
        # original blocked file removed.
        self.assertFalse(pr.path.exists())

    def test_recovery_promotes_checkpoint(self):
        rp = R.promote_local_checkpoints(
            self.root,
            workflow="exec-set",
            run_id="run-abcdef01",
            set_id="execset",
            order=2,
            id6="3m4e54",
            records=self.records,
        )
        self.assertTrue(rp.promoted)
        self.assertIsNotNone(rp.walkthrough_path)
        self.assertTrue(rp.walkthrough_path.exists())

    def test_recovery_noop_when_nothing_to_promote(self):
        rp = R.promote_local_checkpoints(
            self.root,
            workflow="exec-set",
            run_id="run-empty0001",
            set_id="execset",
            order=2,
            id6="3m4e54",
            records=[],
        )
        self.assertFalse(rp.promoted)


if __name__ == "__main__":
    unittest.main()
