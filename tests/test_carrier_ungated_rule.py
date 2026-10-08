"""Outcome tests for check.ipd-carrier-ungated advisory rule.

carriergate Order 01 (`rpw4sb`) E-05.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import artifact_core as ac
from agent_workflows import check_engine as ce
from agent_workflows import cli
from tests import support


class TestCarrierUngatedRule(unittest.TestCase):
    """Pin the check.ipd-carrier-ungated rule behaviorally in both directions."""

    def _make_oq_block(self, questions: list[dict[str, str]]) -> str:
        blocks = ["## Open questions\n"]
        for q in questions:
            loc = q.get("id", "OQ-01")
            blocks.append(f"### {loc}: Question heading\n")
            for k, v in q.items():
                if k != "id":
                    blocks.append(f"- {k}: {v}")
            if "Resolution or deferral rationale" not in q:
                blocks.append("- Resolution or deferral rationale: Not resolved yet.")
            blocks.append("")
        return "\n".join(blocks) + "\n"

    def _build_plan(
        self,
        *,
        plan_id: str = "pl000a",
        when: str = "2026-09-26",
        status: str = "approved",
        deps: str = "none",
        questions: list[dict[str, str]] | None = None,
    ) -> str:
        raw = support.ready_plan_text(plan_id=plan_id, when=when, status=status)
        lines = []
        for line in raw.splitlines():
            if line.startswith("- Item-Dependencies:"):
                lines.append(f"- Item-Dependencies: {deps}")
            else:
                lines.append(line)
        text = "\n".join(lines) + "\n"

        if questions is not None:
            oq_text = self._make_oq_block(questions)
            text = text.replace("## Open questions\n\n#", oq_text)
        return text

    def _setup_repo(
        self,
        td: str,
        *,
        plan_text: str,
        plan_lane: str = "pending",
        carrier_status: str = "open",
        carrier_id: str = "bk0001",
    ) -> tuple[Path, Path]:
        root = Path(td)
        cfg = root / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text(
            json.dumps({"cutovers": {"carrier_obligations": "20260901"}}),
            encoding="utf-8",
        )

        # Create carrier as live backlog item
        bk_dir = root / ".aw" / "records" / "backlog" / carrier_status
        bk_dir.mkdir(parents=True, exist_ok=True)
        bk_text = (
            f"- Id: {carrier_id}\n"
            f"- Status: {carrier_status}\n"
            f"- Set: sample\n"
            f"- Priority: medium\n"
            f"- Work-Kind: chore\n"
            f"- Summary: Carrier item\n\n"
            f"## Workflow history\n"
            f"- 2026-09-26 created (aw backlog): Carrier item\n\n"
            f"Description\n"
        )
        (
            bk_dir / f"20260926-sample-01-{carrier_id}-carrier-item.backlog.md"
        ).write_text(bk_text, encoding="utf-8")

        p_dir = root / ".aw" / "records" / "plans" / plan_lane
        p_dir.mkdir(parents=True, exist_ok=True)
        p_path = p_dir / "20260926-sample-01-pl000a-plan-a.ipd.md"
        p_path.write_text(plan_text, encoding="utf-8")

        return root, p_path

    def _run_check_plans(self, repo: Path) -> tuple[int, dict]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(["check", "plans", "--agent", "--dir", str(repo)])
        output_str = buf.getvalue().strip()
        data = {}
        for line in output_str.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    break
                except Exception:
                    pass
        return code, data

    def test_case_a_reported_open_carried_question_no_edge(self):
        """Case (a): pending plan with open carried question and Item-Dependencies: none is reported."""
        questions = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        plan_text = self._build_plan(deps="none", questions=questions)
        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(td, plan_text=plan_text)
            drifts = ce.evaluate_carrier_ungated(
                repo, plan_path=plan_path, plan_text=plan_text
            )
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            self.assertEqual(d.rule, "check.ipd-carrier-ungated")
            self.assertEqual(d.severity, "info")
            self.assertIn("OQ-01", d.detail)
            self.assertIn("bk0001", d.detail)

    def test_case_b_edged_is_silent_whatever_qualifier(self):
        """Case (b): declaring an edge targeting the carrier is silent under any status qualifier."""
        questions = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        # state:backlog:graduated
        plan_grad = self._build_plan(
            deps="state:backlog:graduated:bk0001", questions=questions
        )
        # state:backlog:done
        plan_done = self._build_plan(
            deps="state:backlog:done:bk0001", questions=questions
        )
        # exists:backlog
        plan_exists = self._build_plan(
            deps="exists:backlog:bk0001", questions=questions
        )

        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(td, plan_text=plan_grad)
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo, plan_path=plan_path, plan_text=plan_grad
                ),
                [],
            )
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo, plan_path=plan_path, plan_text=plan_done
                ),
                [],
            )
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo, plan_path=plan_path, plan_text=plan_exists
                ),
                [],
            )

    def test_case_c_non_subject_rows_are_silent(self):
        """Case (c): resolved, deferred, and Carrier-Declined questions yield nothing."""
        q_resolved = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "resolved",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        q_deferred = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "deferred",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        q_declined = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier-Declined": "No carrier needed for this item.",
            }
        ]

        with tempfile.TemporaryDirectory() as td:
            plan_res = self._build_plan(deps="none", questions=q_resolved)
            plan_def = self._build_plan(deps="none", questions=q_deferred)
            plan_dec = self._build_plan(deps="none", questions=q_declined)
            repo, plan_path = self._setup_repo(td, plan_text=plan_res)
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo, plan_path=plan_path, plan_text=plan_res
                ),
                [],
            )
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo, plan_path=plan_path, plan_text=plan_def
                ),
                [],
            )
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo, plan_path=plan_path, plan_text=plan_dec
                ),
                [],
            )

    def test_case_d_tier_and_exit_code_invariance(self):
        """Case (d): emitted Drift severity is info and drift_exit_code over it returns 0."""
        questions = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        plan_text = self._build_plan(deps="none", questions=questions)
        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(td, plan_text=plan_text)
            drifts = ce.evaluate_carrier_ungated(
                repo, plan_path=plan_path, plan_text=plan_text
            )
            self.assertEqual(len(drifts), 1)
            self.assertEqual(drifts[0].severity, "info")
            self.assertEqual(ac.drift_exit_code(drifts), 0)

    def test_case_e_exit_code_invariance_and_visible_in_cli(self):
        """Case (e): aw check plans exits 0 and prints rule id when only finding is this rule."""
        questions = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        plan_text = self._build_plan(deps="none", questions=questions)
        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(td, plan_text=plan_text)
            code, data = self._run_check_plans(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data.get("outcome"), "conforms")
            diagnostics = data.get("diagnostics", [])
            rules = [d.get("rule") for d in diagnostics]
            self.assertIn("check.ipd-carrier-ungated", rules)
            # Confirm no failing rule is present
            failing_severities = {"error", "warning"}
            for d in diagnostics:
                self.assertNotIn(d.get("severity"), failing_severities)

    def test_case_f_terminal_plans_never_reported(self):
        """Case (f): the same offending plan placed in executed/ yields nothing in the sweep."""
        questions = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "executed",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        plan_text = self._build_plan(
            status="executed", deps="none", questions=questions
        )
        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(
                td, plan_text=plan_text, plan_lane="executed"
            )
            drifts = ce.check_carrier_ungated(repo)
            self.assertEqual(drifts, [])

    def test_case_g_multiple_rows_collapse(self):
        """Case (g): plan with six offending questions yields ONE Drift naming five locators and (and 1 more)."""
        questions = [
            {
                "id": f"OQ-0{i}",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier": f"bk000{i}",
            }
            for i in range(1, 7)
        ]
        plan_text = self._build_plan(deps="none", questions=questions)
        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(td, plan_text=plan_text)
            drifts = ce.evaluate_carrier_ungated(
                repo, plan_path=plan_path, plan_text=plan_text
            )
            self.assertEqual(len(drifts), 1)
            detail = drifts[0].detail
            for i in range(1, 6):
                self.assertIn(f"OQ-0{i}", detail)
            self.assertNotIn("OQ-06", detail)
            self.assertIn(" (and 1 more)", detail)

    def test_cutover_invariance(self):
        """Pre-cutover-dated plan is reported at info identically to post-cutover plan."""
        questions = [
            {
                "id": "OQ-01",
                "Blocking": "no",
                "Status": "open",
                "Owner": "maintainer",
                "Carrier": "bk0001",
            }
        ]
        # Pre-cutover date: 2026-08-15 (cutover is 20260901)
        plan_pre = self._build_plan(when="2026-08-15", deps="none", questions=questions)
        # Post-cutover date: 2026-09-26
        plan_post = self._build_plan(
            when="2026-09-26", deps="none", questions=questions
        )

        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = self._setup_repo(td, plan_text=plan_pre)
            drifts_pre = ce.evaluate_carrier_ungated(
                repo, plan_path=plan_path, plan_text=plan_pre
            )
            drifts_post = ce.evaluate_carrier_ungated(
                repo, plan_path=plan_path, plan_text=plan_post
            )
            self.assertEqual(len(drifts_pre), 1)
            self.assertEqual(len(drifts_post), 1)
            self.assertEqual(drifts_pre[0].severity, "info")
            self.assertEqual(drifts_post[0].severity, "info")

    def test_truncated_plan_never_raises(self):
        """Evaluator returns [] on truncated or invalid plan text rather than raising."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            dummy_path = repo / "dummy.ipd.md"
            self.assertEqual(
                ce.evaluate_carrier_ungated(
                    repo,
                    plan_path=dummy_path,
                    plan_text="truncated content with no headers",
                ),
                [],
            )
            self.assertEqual(
                ce.evaluate_carrier_ungated(repo, plan_path=dummy_path, plan_text=""),
                [],
            )


if __name__ == "__main__":
    unittest.main()
