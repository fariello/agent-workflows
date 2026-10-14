"""Behavioral tests for aw.agent/v1 findings_by_severity breakdown (IPD wizzis)."""

from __future__ import annotations

import json
import unittest

from agent_workflows import agent_schema
from agent_workflows.renderers import AgentRenderer
from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
    OutputContext,
    OutputMode,
)


class AgentFindingsSeverityTests(unittest.TestCase):
    """Behavioral tests verifying the additive findings_by_severity breakdown."""

    def test_case_a_single_warning_diagnostic_clean_exit_zero(self) -> None:
        """(a) backlog measured case: clean exit 0 with warning diagnostic."""
        result = CommandResult(
            command="doctor",
            status="clean",
            exit_code=0,
            summary="advisory warning",
            diagnostics=[
                Diagnostic(
                    location="doc.md",
                    rule="doc.advisory",
                    detail="note",
                    severity="warning",
                ),
            ],
        )
        rec = result.to_agent_record()
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["findings"], 1)
        self.assertEqual(
            rec["findings_by_severity"],
            {"error": 0, "warning": 1, "info": 0},
        )
        rendered_rec = json.loads(AgentRenderer().render(result))
        self.assertEqual(rendered_rec["outcome"], "clean")
        self.assertEqual(rendered_rec["exit"], 0)
        self.assertEqual(rendered_rec["findings"], 1)
        self.assertEqual(
            rendered_rec["findings_by_severity"],
            {"error": 0, "warning": 1, "info": 0},
        )
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        self.assertEqual(agent_schema.validate_agent_record(rendered_rec), [])

    def test_case_b_mixed_severity_diagnostics_sum_to_findings(self) -> None:
        """(b) mixed set: two error, one warning, one info sum to findings == 4."""
        result = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            summary="mixed findings",
            diagnostics=[
                Diagnostic(location="f1.md", rule="r1", detail="d1", severity="error"),
                Diagnostic(location="f2.md", rule="r2", detail="d2", severity="error"),
                Diagnostic(
                    location="f3.md", rule="r3", detail="d3", severity="warning"
                ),
                Diagnostic(location="f4.md", rule="r4", detail="d4", severity="info"),
            ],
        )
        rec = result.to_agent_record()
        self.assertEqual(rec["findings"], 4)
        expected_breakdown = {"error": 2, "warning": 1, "info": 1}
        self.assertEqual(rec["findings_by_severity"], expected_breakdown)
        self.assertEqual(
            sum(rec["findings_by_severity"].values()),
            rec["findings"],
        )
        rendered_rec = json.loads(AgentRenderer().render(result))
        self.assertEqual(rendered_rec["findings"], 4)
        self.assertEqual(rendered_rec["findings_by_severity"], expected_breakdown)
        self.assertEqual(
            sum(rendered_rec["findings_by_severity"].values()),
            rendered_rec["findings"],
        )

    def test_case_c_unrecognized_severity_counted_under_error(self) -> None:
        """(c) unrecognized severity string counted under error (fail closed)."""
        result = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            summary="unrecognized severities",
            diagnostics=[
                Diagnostic(
                    location="f1.md", rule="r1", detail="d1", severity="unknown_custom"
                ),
                Diagnostic(location="f2.md", rule="r2", detail="d2", severity=""),
                Diagnostic(
                    location="f3.md", rule="r3", detail="d3", severity="WARNING"
                ),
            ],
        )
        rec = result.to_agent_record()
        self.assertEqual(rec["findings"], 3)
        self.assertEqual(
            rec["findings_by_severity"],
            {"error": 3, "warning": 0, "info": 0},
        )
        rendered_rec = json.loads(AgentRenderer().render(result))
        self.assertEqual(
            rendered_rec["findings_by_severity"],
            {"error": 3, "warning": 0, "info": 0},
        )

    def test_case_d_data_findings_fallback_omits_severity_breakdown(self) -> None:
        """(d) result with no diagnostics and data={"findings": 3} yields findings == 3 and no findings_by_severity key."""
        result = CommandResult(
            command="status",
            status="clean",
            exit_code=0,
            summary="data findings",
            data={"findings": 3},
        )
        rec = result.to_agent_record()
        self.assertEqual(rec["findings"], 3)
        self.assertNotIn("findings_by_severity", rec)
        rendered_rec = json.loads(AgentRenderer().render(result))
        self.assertEqual(rendered_rec["findings"], 3)
        self.assertNotIn("findings_by_severity", rendered_rec)

    def test_case_e_clean_result_no_diagnostics_omits_severity_breakdown(self) -> None:
        """(e) clean result with no diagnostics yields findings == 0 and no findings_by_severity key."""
        result = CommandResult(
            command="status",
            status="clean",
            exit_code=0,
            summary="clean",
        )
        rec = result.to_agent_record()
        self.assertEqual(rec["findings"], 0)
        self.assertNotIn("findings_by_severity", rec)
        rendered_rec = json.loads(AgentRenderer().render(result))
        self.assertEqual(rendered_rec["findings"], 0)
        self.assertNotIn("findings_by_severity", rendered_rec)

    def test_case_f_fields_projection_retains_severity_and_envelope(self) -> None:
        """(f) OutputContext with fields=["findings_by_severity"] retains key and mandatory envelope."""
        result = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            summary="findings",
            diagnostics=[
                Diagnostic(location="f.md", rule="r", detail="d", severity="warning"),
            ],
        )
        ctx = OutputContext(mode=OutputMode.AGENT, fields=["findings_by_severity"])
        rec = result.to_agent_record(ctx)
        self.assertIn("findings_by_severity", rec)
        self.assertEqual(
            rec["findings_by_severity"],
            {"error": 0, "warning": 1, "info": 0},
        )
        mandatory = {"schema", "kind", "cmd", "exit", "outcome", "verified", "complete"}
        for field in mandatory:
            self.assertIn(field, rec)
        self.assertNotIn("diagnostics", rec)
        self.assertNotIn("findings", rec)

        rendered_rec = json.loads(AgentRenderer().render(result, ctx))
        self.assertIn("findings_by_severity", rendered_rec)
        for field in mandatory:
            self.assertIn(field, rendered_rec)
        self.assertNotIn("diagnostics", rendered_rec)
        self.assertNotIn("findings", rendered_rec)

    def test_case_g_all_produced_records_pass_schema_validation(self) -> None:
        """(g) every produced record passes agent_schema.validate_agent_record with an empty error list."""
        cases = [
            CommandResult(
                command="c1",
                status="clean",
                exit_code=0,
                diagnostics=[
                    Diagnostic(location="a", rule="r", detail="d", severity="warning")
                ],
            ),
            CommandResult(
                command="c2",
                status="findings",
                exit_code=1,
                diagnostics=[
                    Diagnostic(location="a", rule="r1", detail="d1", severity="error"),
                    Diagnostic(location="b", rule="r2", detail="d2", severity="info"),
                ],
            ),
            CommandResult(
                command="c3",
                status="clean",
                exit_code=0,
                data={"findings": 3},
            ),
            CommandResult(
                command="c4",
                status="clean",
                exit_code=0,
            ),
            CommandResult(
                command="c5",
                status="findings",
                exit_code=1,
                diagnostics=[
                    Diagnostic(
                        location="x", rule="rx", detail="dx", severity="advisory"
                    )
                ],
            ),
        ]
        for idx, res in enumerate(cases):
            with self.subTest(case_idx=idx):
                rec = res.to_agent_record()
                errors = agent_schema.validate_agent_record(rec)
                self.assertEqual(
                    errors, [], f"Case {idx} failed schema validation: {errors}"
                )
                rendered = json.loads(AgentRenderer().render(res))
                rendered_errors = agent_schema.validate_agent_record(rendered)
                self.assertEqual(
                    rendered_errors,
                    [],
                    f"Case {idx} rendered failed validation: {rendered_errors}",
                )


if __name__ == "__main__":
    unittest.main()
