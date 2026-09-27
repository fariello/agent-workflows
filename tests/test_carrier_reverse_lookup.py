"""Tests for carrier reverse lookup and finished carrier verification findings.

carrierwarn Order 01 (`cnzrxb`) E-05.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import cli
from tests import support


class CarrierReverseLookupTests(unittest.TestCase):
    """Four outcome tests for carrier reverse lookup and aw check plans behavior (E-05)."""

    def _setup_repo(
        self,
        td: str,
        *,
        b_status: str = "executed",
        a_obligation_field: str = "- Carrier: pl000b",
    ) -> tuple[Path, Path, Path]:
        root = Path(td)
        cfg = root / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text(
            json.dumps({"cutovers": {"carrier_obligations": "20260901"}}),
            encoding="utf-8",
        )

        # Plan B in executed or superseded
        b_dir = (
            root
            / ".aw"
            / "records"
            / "plans"
            / ("executed" if b_status == "executed" else "superseded")
        )
        b_dir.mkdir(parents=True, exist_ok=True)
        b_text = (
            f"# IPD: Plan B\n\n"
            f"- Date: 2026-09-26\n"
            f"- Id: pl000b\n"
            f"- Status: {b_status}\n"
        )
        b_path = b_dir / "20260926-sample-01-pl000b-plan-b.ipd.md"
        b_path.write_text(b_text, encoding="utf-8")

        # Plan A in pending
        a_dir = root / ".aw" / "records" / "plans" / "pending"
        a_dir.mkdir(parents=True, exist_ok=True)
        raw_a = support.ready_plan_text(
            plan_id="pl000a", when="2026-09-26", status="approved"
        )
        lines = raw_a.splitlines()
        idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("## Deferred"):
                idx = i
                break
        if idx >= 0:
            lines.insert(idx + 1, f"  {a_obligation_field}")
            lines.insert(idx + 1, "- Row 1 deferred")
            a_text = "\n".join(lines) + "\n"
        else:
            a_text = (
                raw_a
                + "\n## Deferred / out of scope (with reason)\n- Row 1 deferred\n"
                + f"  {a_obligation_field}\n"
            )
        a_path = a_dir / "20260926-sample-01-pl000a-plan-a.ipd.md"
        a_path.write_text(a_text, encoding="utf-8")

        return root, a_path, b_path

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

    def test_case_a_finished_carrier_exits_0_with_unverified_finding(self):
        """Case (a): plan A defers to executed plan B -> aw check plans exit 0 with
        a check.ipd-carrier-finished-unverified finding naming A's row."""
        with tempfile.TemporaryDirectory() as td:
            repo, a_path, b_path = self._setup_repo(
                td, b_status="executed", a_obligation_field="- Carrier: pl000b"
            )
            code, data = self._run_check_plans(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data.get("outcome"), "conforms")
            diagnostics = data.get("diagnostics", [])
            rules = [d.get("rule") for d in diagnostics]
            self.assertIn("check.ipd-carrier-finished-unverified", rules)
            self.assertNotIn("check.ipd-uncarried-obligation", rules)

            # Finding names A's row
            finished_diags = [
                d
                for d in diagnostics
                if d.get("rule") == "check.ipd-carrier-finished-unverified"
            ]
            self.assertEqual(len(finished_diags), 1)
            self.assertIn(
                "20260926-sample-01-pl000a-plan-a.ipd.md",
                finished_diags[0].get("location", ""),
            )

    def test_case_b_abandoned_carrier_exits_1_with_uncarried_finding(self):
        """Case (b): plan A defers to superseded plan B -> aw check plans exit 1 with
        check.ipd-uncarried-obligation."""
        with tempfile.TemporaryDirectory() as td:
            repo, a_path, b_path = self._setup_repo(
                td, b_status="superseded", a_obligation_field="- Carrier: pl000b"
            )
            code, data = self._run_check_plans(repo)
            self.assertEqual(code, 1)
            self.assertEqual(data.get("outcome"), "findings")
            diagnostics = data.get("diagnostics", [])
            rules = [d.get("rule") for d in diagnostics]
            self.assertIn("check.ipd-uncarried-obligation", rules)
            self.assertNotIn("check.ipd-carrier-finished-unverified", rules)

    def test_case_c_carrier_evidence_produces_no_finding(self):
        """Case (c): the same row with - Carrier-Evidence: -> no carrier finding and exit 0."""
        with tempfile.TemporaryDirectory() as td:
            repo, a_path, b_path = self._setup_repo(
                td,
                b_status="executed",
                a_obligation_field="- Carrier-Evidence: .aw/records/plans/executed/20260926-sample-01-pl000b-plan-b.ipd.md",
            )
            code, data = self._run_check_plans(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data.get("outcome"), "conforms")
            diagnostics = data.get("diagnostics", [])
            rules = [d.get("rule") for d in diagnostics]
            self.assertNotIn("check.ipd-carrier-finished-unverified", rules)
            self.assertNotIn("check.ipd-uncarried-obligation", rules)

    def test_case_d_find_obligations_carried_by(self):
        """Case (d): find_obligations_carried_by(repo, B) returns A's row, and [] for an id6 nobody names."""
        with tempfile.TemporaryDirectory() as td:
            repo, a_path, b_path = self._setup_repo(
                td, b_status="executed", a_obligation_field="- Carrier: pl000b"
            )
            carried = ce.find_obligations_carried_by(repo, "pl000b")
            self.assertEqual(len(carried), 1)
            self.assertEqual(carried[0].plan_id6, "pl000a")
            self.assertEqual(carried[0].locator, "deferred row 1")
            self.assertEqual(carried[0].row_text, "- Row 1 deferred")
            self.assertEqual(carried[0].plan_path, a_path)

            nobody = ce.find_obligations_carried_by(repo, "zzzzzz")
            self.assertEqual(nobody, [])


if __name__ == "__main__":
    unittest.main()
