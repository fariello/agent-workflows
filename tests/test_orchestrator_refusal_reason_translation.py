"""Behavioral tests for RETIRE_REFUSED to ORCH_REASON translation and unrecognized-reason fallback.

Guards two properties of the orchestrator refusal path (yuhl6o S-10, S-11):
(a) runner_shared.decide_orchestrator_dispatch translates every RETIRE_REFUSED_* value produced
    by evaluate_set_retirement into an ORCH_REASON_* value that orchestrator_refusal_text maps,
    including the near-miss pair 'unfinished-children' versus 'children-unfinished'; and
(b) orchestrator_refusal_text reports an unrecognized or empty/None code verbatim with a
    non-empty, renderable reason and remedy instead of raising.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import oc_runipd, render_stream, runner_shared


class TestOrchestratorRefusalReasonTranslation(unittest.TestCase):
    """Test retirement-refusal reason translation and unrecognized-reason reporting fallback."""

    def _make_repo(
        self,
        temp: str,
        *,
        setid: str,
        include_orchestrator: bool = True,
        orchestrator_id: str = "par001",
        orchestrator_status: str = "queued",
        table_orders: list[tuple[str, str, str]] | None = None,
        children: list[tuple[str, int, str]] | None = None,
    ) -> Path:
        """Create a minimal repo holding an orchestrator and child plans."""
        repo = Path(temp)
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        if include_orchestrator:
            orch_content = (
                f"# IPD: orch\n\n"
                f"- Id: {orchestrator_id}\n"
                f"- Set: {setid}\n"
                f"- Order: 0\n"
                f"- Kind: orchestrator\n"
                f"- Status: {orchestrator_status}\n"
            )
            if table_orders is not None:
                orch_content += (
                    f"\n## {runner_shared._CHILD_IPDS_HEADING}\n\n"
                    f"| Order | Id | Child |\n"
                    f"|---|---|---|\n"
                )
                for order_tok, cid, desc in table_orders:
                    orch_content += f"| {order_tok} | {cid} | {desc} |\n"
            (pending / f"20261014-{setid}-00-{orchestrator_id}-orch.ipd.md").write_text(
                orch_content, encoding="utf-8"
            )
        if children:
            for cid, order_num, st in children:
                child_content = (
                    f"# IPD: child\n\n"
                    f"- Id: {cid}\n"
                    f"- Set: {setid}\n"
                    f"- Order: {order_num}\n"
                    f"- Kind: child\n"
                    f"- Status: {st}\n"
                )
                (
                    pending / f"20261014-{setid}-{order_num:02d}-{cid}-child.ipd.md"
                ).write_text(child_content, encoding="utf-8")
        return repo

    def test_case_01_translation_at_dispatch_decision(self):
        """E-01: Table-driven test verifying retirement-refusal translation and eligible control."""
        cases = [
            (
                "no-orchestrator",
                "noorch",
                False,
                None,
                [("kid001", 1, "approved")],
                runner_shared.RETIRE_REFUSED_NO_ORCHESTRATOR,
                runner_shared.ORCH_REASON_NO_ORCHESTRATOR,
                runner_shared.ORCH_DISPATCH_TERMINATE,
                [],
            ),
            (
                "no-children",
                "nokids",
                True,
                None,
                [],
                runner_shared.RETIRE_REFUSED_NO_CHILDREN,
                runner_shared.ORCH_REASON_NO_CHILDREN,
                runner_shared.ORCH_DISPATCH_TERMINATE,
                [
                    {
                        "id6": "par001",
                        "setid": "nokids",
                        "status": "queued",
                        "action": "orchestrate",
                    }
                ],
            ),
            (
                "unauthored-child-rows",
                "unauth",
                True,
                [("01", "kid001", "first child"), ("02", "kid002", "second child")],
                [("kid001", 1, "executed")],
                runner_shared.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
                runner_shared.ORCH_REASON_UNAUTHORED_CHILD_ROWS,
                runner_shared.ORCH_DISPATCH_TERMINATE,
                [
                    {
                        "id6": "par001",
                        "setid": "unauth",
                        "status": "queued",
                        "action": "orchestrate",
                    },
                    {
                        "id6": "kid001",
                        "setid": "unauth",
                        "status": "executed",
                        "action": "execute",
                    },
                ],
            ),
            (
                "unfinished-children",
                "unfin",
                True,
                [("01", "kid001", "first child")],
                [("kid001", 1, "approved")],
                runner_shared.RETIRE_REFUSED_UNFINISHED_CHILDREN,
                runner_shared.ORCH_REASON_UNFINISHED_CHILDREN,
                runner_shared.ORCH_DISPATCH_RECONSIDER,
                [
                    {
                        "id6": "par001",
                        "setid": "unfin",
                        "status": "queued",
                        "action": "orchestrate",
                    },
                    {
                        "id6": "kid001",
                        "setid": "unfin",
                        "status": "queued",
                        "action": "execute",
                    },
                ],
            ),
        ]

        for (
            branch,
            setid,
            include_orch,
            table_orders,
            children,
            expected_retire_refused,
            expected_orch_reason,
            expected_outcome,
            queue,
        ) in cases:
            with self.subTest(branch=branch):
                with tempfile.TemporaryDirectory() as temp:
                    repo = self._make_repo(
                        temp,
                        setid=setid,
                        include_orchestrator=include_orch,
                        table_orders=table_orders,
                        children=children,
                    )
                    retire_decision = runner_shared.evaluate_set_retirement(repo, setid)
                    self.assertFalse(retire_decision.eligible)
                    self.assertEqual(retire_decision.reason, expected_retire_refused)

                    dispatch_decision = runner_shared.decide_orchestrator_dispatch(
                        repo,
                        setid,
                        "par001",
                        queue,
                        terminal_states=runner_shared.TERMINAL_STATES,
                        success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                    )
                    self.assertEqual(dispatch_decision.outcome, expected_outcome)
                    self.assertEqual(dispatch_decision.reason, expected_orch_reason)

                    reason_text, _ = runner_shared.orchestrator_refusal_text(
                        dispatch_decision.reason
                    )
                    self.assertNotIn(
                        "THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE",
                        reason_text,
                    )

        with self.subTest(branch="control-eligible"):
            with tempfile.TemporaryDirectory() as temp:
                repo = self._make_repo(
                    temp,
                    setid="ctrlok",
                    include_orchestrator=True,
                    table_orders=[("01", "kid001", "first child")],
                    children=[("kid001", 1, "executed")],
                )
                control_decision = runner_shared.evaluate_set_retirement(repo, "ctrlok")
                self.assertTrue(control_decision.eligible)
                self.assertEqual(control_decision.reason, runner_shared.RETIRE_ELIGIBLE)

    def test_case_02_read_surface_via_dispatch_orchestrator_item(self):
        """E-02: End-to-end translation through dispatch_orchestrator_item and refusal_of_item."""
        with tempfile.TemporaryDirectory() as temp:
            setid = "unfin"
            repo = self._make_repo(
                temp,
                setid=setid,
                include_orchestrator=True,
                table_orders=[("01", "kid001", "first child")],
                children=[("kid001", 1, "approved")],
            )
            run_dir = repo / "run-case"
            run_dir.mkdir(parents=True, exist_ok=True)
            orch_item = {
                "position": 1,
                "id6": "par001",
                "setid": setid,
                "action": "orchestrate",
                "kind": "orchestrator",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            }
            child_item = {
                "position": 2,
                "id6": "kid001",
                "setid": setid,
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            }
            state = {
                "repo": str(repo),
                "run_id": "run-case",
                "queue": [orch_item, child_item],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
            decision = runner_shared.dispatch_orchestrator_item(
                repo,
                run_dir,
                state,
                orch_item,
                actor="aw oc run model=test",
                terminal_states=runner_shared.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
            )
            self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_RECONSIDER)
            self.assertEqual(orch_item["status"], "queued")
            refusal = render_stream.refusal_of_item(orch_item)
            self.assertIsNotNone(refusal)
            self.assertEqual(
                refusal.code, runner_shared.ORCH_REASON_UNFINISHED_CHILDREN
            )
            self.assertNotEqual(
                refusal.code, runner_shared.RETIRE_REFUSED_UNFINISHED_CHILDREN
            )
            self.assertNotIn("NOT RECOGNIZE", refusal.reason)
            untranslated_reason, _ = runner_shared.orchestrator_refusal_text(
                runner_shared.RETIRE_REFUSED_UNFINISHED_CHILDREN
            )
            self.assertIn("NOT RECOGNIZE", untranslated_reason)

    def test_case_03_unknown_code_fallback(self):
        """E-03: Unknown-code fallback reports verbatim, non-empty, and constructs Refusal."""
        reason, remedy = runner_shared.orchestrator_refusal_text("some-future-reason")
        self.assertTrue(bool(reason and reason.strip()))
        self.assertTrue(bool(remedy and remedy.strip()))
        self.assertIn("THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE", reason)
        self.assertIn("some-future-reason", reason)
        self.assertIn("some-future-reason", remedy)
        self.assertIn("events.jsonl", remedy)
        ref = render_stream.Refusal(
            code="some-future-reason", reason=reason, remedy=remedy
        )
        self.assertEqual(ref.code, "some-future-reason")
        self.assertEqual(ref.reason, reason)
        self.assertEqual(ref.remedy, remedy)

    def test_case_04_empty_and_none_fallback(self):
        """E-04: Empty or None reason produces (no reason recorded) fallback and constructs Refusal."""
        for input_val in ("", None):
            with self.subTest(input_val=input_val):
                reason, remedy = runner_shared.orchestrator_refusal_text(input_val)
                self.assertTrue(bool(reason and reason.strip()))
                self.assertTrue(bool(remedy and remedy.strip()))
                self.assertIn("(no reason recorded)", reason)
                self.assertIn("NOT RECOGNIZE", reason)
                ref = render_stream.Refusal(
                    code="(no reason recorded)", reason=reason, remedy=remedy
                )
                self.assertEqual(ref.code, "(no reason recorded)")
                self.assertEqual(ref.reason, reason)
                self.assertEqual(ref.remedy, remedy)


if __name__ == "__main__":
    unittest.main()
