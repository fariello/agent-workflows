"""Behavioral tests for the children-not-approved orchestrator refusal reason (ntto7n / swk6r8).

Distinguishes an orchestrator whose children merely await human approval (never dispatched)
from one whose children ran and failed.
"""

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import oc_runipd, render_stream, runner_shared


class TestOrchestratorNotApprovedReason(unittest.TestCase):
    """Test the children-not-approved orchestrator refusal reason and dispatch behavior."""

    def _make_repo(
        self,
        temp: str,
        *,
        child_specs: list[tuple[str, str | None]],
    ) -> Path:
        """Create a minimal repo holding an orchestrator and child plans."""
        repo = Path(temp)
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        (pending / "20260908-finalback-00-par001-orch.ipd.md").write_text(
            "# IPD: orch\n\n- Id: par001\n- Set: finalback\n- Order: 0\n- Kind: orchestrator\n",
            encoding="utf-8",
        )
        for idx, (cid, st) in enumerate(child_specs, start=1):
            status_line = f"- Status: {st}\n" if st is not None else ""
            (pending / f"20260908-finalback-{idx:02d}-{cid}-child.ipd.md").write_text(
                f"# IPD: child\n\n- Id: {cid}\n- Set: finalback\n- Order: {idx}\n- Kind: child\n{status_line}",
                encoding="utf-8",
            )
        return repo

    def _decide(self, repo: Path, queue: list[dict]):
        return runner_shared.decide_orchestrator_dispatch(
            repo,
            "finalback",
            "par001",
            queue,
            terminal_states=runner_shared.TERMINAL_STATES,
            success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
        )

    def test_case_01_single_child_reviewed(self):
        """Case 1: single child reviewed -> TERMINATE + children-not-approved, detail names kid001."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "reviewed")])
            queue = [
                {
                    "id6": "kid001",
                    "setid": "finalback",
                    "status": "reviewed",
                    "action": "execute",
                }
            ]
            dec = self._decide(repo, queue)
            self.assertEqual(dec.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
            self.assertEqual(
                dec.reason, runner_shared.ORCH_REASON_CHILDREN_NOT_APPROVED
            )
            self.assertIn("kid001", dec.detail)

    def test_case_02_single_child_approved(self):
        """Case 2: single child approved -> TERMINATE + children-not-approved, detail names kid001."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "approved")])
            queue = [
                {
                    "id6": "kid001",
                    "setid": "finalback",
                    "status": "approved",
                    "action": "execute",
                }
            ]
            dec = self._decide(repo, queue)
            self.assertEqual(dec.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
            self.assertEqual(
                dec.reason, runner_shared.ORCH_REASON_CHILDREN_NOT_APPROVED
            )
            self.assertIn("kid001", dec.detail)

    def test_case_03_single_child_failed_safely(self):
        """Case 3: single child failed-safely -> TERMINATE + children-terminally-failed."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "failed-safely")])
            queue = [
                {
                    "id6": "kid001",
                    "setid": "finalback",
                    "status": "failed-safely",
                    "action": "execute",
                }
            ]
            dec = self._decide(repo, queue)
            self.assertEqual(dec.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
            self.assertEqual(dec.reason, runner_shared.ORCH_REASON_DEAD_CHILDREN)

            # Also check runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS explicitly
            queue2 = [
                {
                    "id6": "kid001",
                    "setid": "finalback",
                    "status": runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS,
                    "action": "execute",
                }
            ]
            dec2 = self._decide(repo, queue2)
            self.assertEqual(dec2.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
            self.assertEqual(dec2.reason, runner_shared.ORCH_REASON_DEAD_CHILDREN)

    def test_case_04_mixed_children_unapproved_and_failed(self):
        """Case 4: MIXED: two children, reviewed and failed-safely -> children-terminally-failed, unfinished names both."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(
                temp, child_specs=[("kid001", "reviewed"), ("kid002", "failed-safely")]
            )
            queue = [
                {
                    "id6": "kid001",
                    "setid": "finalback",
                    "status": "reviewed",
                    "action": "execute",
                },
                {
                    "id6": "kid002",
                    "setid": "finalback",
                    "status": "failed-safely",
                    "action": "execute",
                },
            ]
            dec = self._decide(repo, queue)
            self.assertEqual(dec.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
            self.assertEqual(dec.reason, runner_shared.ORCH_REASON_DEAD_CHILDREN)
            unfinished_ids = {cid for cid, _status in dec.unfinished}
            self.assertEqual(unfinished_ids, {"kid001", "kid002"})

    def test_case_05_queued_child_unchanged(self):
        """Case 5: queued -> RECONSIDER + children-unfinished (unchanged)."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "queued")])
            queue = [
                {
                    "id6": "kid001",
                    "setid": "finalback",
                    "status": "queued",
                    "action": "execute",
                }
            ]
            dec = self._decide(repo, queue)
            self.assertEqual(dec.outcome, runner_shared.ORCH_DISPATCH_RECONSIDER)
            self.assertEqual(dec.reason, runner_shared.ORCH_REASON_UNFINISHED_CHILDREN)

    def test_case_06_orchestrator_refusal_text_new_code(self):
        """Case 6: orchestrator_refusal_text for new code is mapped, non-empty, contains aw ipd set approved, no --full-auto."""
        reason, remedy = runner_shared.orchestrator_refusal_text(
            runner_shared.ORCH_REASON_CHILDREN_NOT_APPROVED
        )
        self.assertTrue(bool(reason and reason.strip()))
        self.assertTrue(bool(remedy and remedy.strip()))
        self.assertNotIn("THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE", reason)
        self.assertIn("aw ipd set approved", remedy)
        self.assertNotIn("--full-auto", reason)
        self.assertNotIn("--full-auto", remedy)

    def test_case_07_orchestrator_refusal_text_old_code_still_mapped(self):
        """Case 7: orchestrator_refusal_text('children-terminally-failed') is still mapped (no DOES NOT RECOGNIZE)."""
        reason, remedy = runner_shared.orchestrator_refusal_text(
            runner_shared.ORCH_REASON_DEAD_CHILDREN
        )
        self.assertTrue(bool(reason and reason.strip()))
        self.assertTrue(bool(remedy and remedy.strip()))
        self.assertNotIn("DOES NOT RECOGNIZE", reason)

    def test_case_08_read_surface_via_dispatch_orchestrator_item(self):
        """Case 8: through dispatch_orchestrator_item, reviewed child leaves refusal code equal to children-not-approved."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "reviewed")])
            run_dir = repo / "run-case8"
            run_dir.mkdir(parents=True, exist_ok=True)
            orch_item = {
                "position": 1,
                "id6": "par001",
                "setid": "finalback",
                "action": "orchestrate",
                "kind": "orchestrator",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            }
            child_item = {
                "position": 2,
                "id6": "kid001",
                "setid": "finalback",
                "action": "execute",
                "kind": "child",
                "status": "reviewed",
                "dependencies": [],
                "attempts": [],
            }
            state = {
                "repo": str(repo),
                "run_id": "run-case8",
                "queue": [orch_item, child_item],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
            runner_shared.dispatch_orchestrator_item(
                repo,
                run_dir,
                state,
                orch_item,
                actor="aw oc run model=test",
                terminal_states=runner_shared.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
            )
            refusal = render_stream.refusal_of_item(orch_item)
            self.assertIsNotNone(refusal)
            self.assertEqual(
                refusal.code, runner_shared.ORCH_REASON_CHILDREN_NOT_APPROVED
            )

    def test_case_09_outcome_is_unchanged_for_new_code(self):
        """Case 9: outcome is unchanged for the new code, asserting ORCH_DISPATCH_TERMINATE for reviewed and approved."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "reviewed")])
            dec_reviewed = self._decide(
                repo,
                [
                    {
                        "id6": "kid001",
                        "setid": "finalback",
                        "status": "reviewed",
                        "action": "execute",
                    }
                ],
            )
            self.assertEqual(
                dec_reviewed.outcome, runner_shared.ORCH_DISPATCH_TERMINATE
            )

        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", "approved")])
            dec_approved = self._decide(
                repo,
                [
                    {
                        "id6": "kid001",
                        "setid": "finalback",
                        "status": "approved",
                        "action": "execute",
                    }
                ],
            )
            self.assertEqual(
                dec_approved.outcome, runner_shared.ORCH_DISPATCH_TERMINATE
            )

    def test_case_10_child_with_no_status_line(self):
        """Case 10: a child with NO - Status: line (queue status reviewed via initial_queue_status(None)) -> children-not-approved."""
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(temp, child_specs=[("kid001", None)])
            q_status = runner_shared.initial_queue_status(None)
            self.assertEqual(q_status, "reviewed")
            dec = self._decide(
                repo,
                [
                    {
                        "id6": "kid001",
                        "setid": "finalback",
                        "status": q_status,
                        "action": "execute",
                    }
                ],
            )
            self.assertEqual(dec.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
            self.assertEqual(
                dec.reason, runner_shared.ORCH_REASON_CHILDREN_NOT_APPROVED
            )


if __name__ == "__main__":
    unittest.main()
