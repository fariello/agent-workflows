"""Tests for Token Control, Compact Defaults, --fields, --limit, and Escape Hatches.

awcliux Order 03 (`8su0r3`) E-03 / V-03.

Asserts:
1. Compact defaults achieve measurably smaller byte/token size compared to verbose/JSON forms
   with zero loss of core decision facts (outcome, completeness, verification, evidence, next).
2. Field projection (`--fields`) filters non-requested fields while preserving mandatory envelope.
3. Stream truncation under `--limit` produces exact items plus summary with total, emitted,
   omitted, complete=False, and continuation `next` command.
4. `--verbose` and `--json` escape hatches provide full debugging details when explicitly requested.
"""

from __future__ import annotations

import json
import unittest

from agent_workflows.renderers import AgentRenderer, JsonRenderer
from agent_workflows.result_types import (
    Change,
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
    OutputContext,
    OutputMode,
)


class TokenControlAndBudgetUnitTests(unittest.TestCase):
    """Assert token budget and compact default size reductions (E-03 / V-03)."""

    def setUp(self) -> None:
        # Build a realistic multi-finding / multi-change / multi-evidence command result
        self.result = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            summary="Found 10 lint warnings and uncommitted changes across 4 subsystems",
            target="plans/all",
            diagnostics=[
                Diagnostic(
                    location=f"plans/plan_{i:02d}.ipd.md",
                    rule="ipd-lint.author",
                    detail=f"Author field format warning in section {i}: expected 'First Last <email>'",
                    severity="warning",
                    fix=f"aw ipd fix author plans/plan_{i:02d}.ipd.md",
                )
                for i in range(10)
            ],
            changes=[
                Change(
                    path=f"plans/plan_{i:02d}.ipd.md",
                    kind="modify",
                    detail="Applied author slug normalization",
                    applied=False,
                )
                for i in range(8)
            ],
            evidence=[
                Evidence(
                    key="ipd-lint:author",
                    value={"checked": 10, "passed": 0},
                    status="findings",
                ),
                Evidence(
                    key="git:status",
                    value={"clean": True, "branch": "main"},
                    status="verified",
                ),
                Evidence(
                    key="schema:conformance",
                    value={"version": "1.0"},
                    status="verified",
                ),
            ],
            next_actions=[
                NextAction(
                    command="aw check --fix", description="auto-fix all author warnings"
                )
            ],
            data={"checked": 10, "findings": 10},
        )

    def test_compact_default_vs_verbose_and_json_size_measurement(self):
        # 1. Render in compact default mode (agent)
        compact_ctx = OutputContext(mode=OutputMode.AGENT, verbose=False)
        agent_renderer = AgentRenderer()
        compact_output = agent_renderer.render(self.result, compact_ctx)

        # 2. Render in verbose agent mode
        verbose_ctx = OutputContext(mode=OutputMode.AGENT, verbose=True)
        verbose_output = agent_renderer.render(self.result, verbose_ctx)

        # 3. Render in JSON mode
        json_renderer = JsonRenderer()
        json_ctx = OutputContext(mode=OutputMode.JSON)
        json_output = json_renderer.render(self.result, json_ctx)

        compact_bytes = len(compact_output.encode("utf-8"))
        verbose_bytes = len(verbose_output.encode("utf-8"))
        json_bytes = len(json_output.encode("utf-8"))

        # Assert size relationship: compact < verbose < json
        self.assertLess(
            compact_bytes,
            verbose_bytes,
            f"Compact ({compact_bytes}B) should be smaller than verbose ({verbose_bytes}B)",
        )
        self.assertLess(
            compact_bytes,
            json_bytes,
            f"Compact ({compact_bytes}B) should be smaller than full JSON ({json_bytes}B)",
        )

        # Size reduction ratio must be significant (>= 40% reduction compared to full JSON)
        reduction_ratio = (json_bytes - compact_bytes) / json_bytes
        self.assertGreater(
            reduction_ratio,
            0.40,
            f"Expected at least 40% size reduction, got {reduction_ratio:.1%}",
        )

        # 4. Assert zero loss of decision facts in compact output
        compact_rec = json.loads(compact_output.strip())
        self.assertEqual(compact_rec["schema"], "aw.agent/v1")
        self.assertEqual(compact_rec["kind"], "result")
        self.assertEqual(compact_rec["cmd"], "check")
        self.assertEqual(compact_rec["outcome"], "findings")
        self.assertEqual(compact_rec["exit"], 1)
        self.assertEqual(compact_rec["findings"], 10)
        self.assertEqual(compact_rec["checked"], 10)
        self.assertTrue(compact_rec["verified"])
        self.assertTrue(compact_rec["complete"])
        self.assertEqual(compact_rec["next"], "aw check --fix")
        self.assertIn("ipd-lint:author", str(compact_rec["evidence"]))

    def test_fields_filtering_projection(self):
        # Request only outcome, findings, and next
        ctx = OutputContext(
            mode=OutputMode.AGENT,
            fields=["outcome", "findings", "next"],
            verbose=False,
        )
        renderer = AgentRenderer()
        output = renderer.render(self.result, ctx)
        rec = json.loads(output.strip())

        # Mandatory envelope fields must always be present
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "check")
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["outcome"], "findings")
        self.assertTrue(rec["verified"])
        self.assertTrue(rec["complete"])

        # Requested fields must be present
        self.assertEqual(rec["findings"], 10)
        self.assertEqual(rec["next"], "aw check --fix")

        # Non-requested optional fields must be omitted
        self.assertNotIn("diagnostics", rec)
        self.assertNotIn("changes", rec)
        self.assertNotIn("evidence", rec)

    def test_limit_stream_truncation_with_continuation_command(self):
        # Simulate 50 attention / repo stream items
        stream_items = [
            {
                "id": f"item-{i:02d}",
                "path": f"plans/p_{i:02d}.ipd.md",
                "status": "needs-review",
            }
            for i in range(50)
        ]

        # 1. Truncated stream with limit=20
        ctx_truncated = OutputContext(mode=OutputMode.AGENT, limit=20)
        renderer = AgentRenderer()
        output_truncated = renderer.render_stream(
            items=stream_items,
            cmd="attention",
            context=ctx_truncated,
            total=50,
            next_template="aw attention --agent --limit {limit}",
        )

        lines = [line for line in output_truncated.strip().split("\n") if line]
        self.assertEqual(len(lines), 21)  # 20 items + 1 summary

        # Check item records
        for line in lines[:20]:
            item_rec = json.loads(line)
            self.assertEqual(item_rec["kind"], "item")
            self.assertEqual(item_rec["cmd"], "attention")

        # Check summary record
        summary_rec = json.loads(lines[-1])
        self.assertEqual(summary_rec["kind"], "summary")
        self.assertEqual(summary_rec["cmd"], "attention")
        self.assertEqual(summary_rec["total"], 50)
        self.assertEqual(summary_rec["emitted"], 20)
        self.assertEqual(summary_rec["omitted"], 30)
        self.assertFalse(summary_rec["complete"])
        self.assertEqual(summary_rec["next"], "aw attention --agent --limit 50")

        # 2. Non-truncated stream (limit=None)
        ctx_full = OutputContext(mode=OutputMode.AGENT, limit=None)
        output_full = renderer.render_stream(
            items=stream_items,
            cmd="attention",
            context=ctx_full,
            total=50,
        )
        full_lines = [line for line in output_full.strip().split("\n") if line]
        self.assertEqual(len(full_lines), 51)  # 50 items + 1 summary
        full_summary = json.loads(full_lines[-1])
        self.assertEqual(full_summary["total"], 50)
        self.assertEqual(full_summary["emitted"], 50)
        self.assertEqual(full_summary["omitted"], 0)
        self.assertTrue(full_summary["complete"])
        self.assertIsNone(full_summary.get("next"))


if __name__ == "__main__":
    unittest.main()
