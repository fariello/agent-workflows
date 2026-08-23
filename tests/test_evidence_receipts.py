"""Tests for Anti-Greenwashing Evidence Receipts and Exit Code Parity.

awcliux Order 03 (`8su0r3`) E-02 / V-02.

Asserts:
1. Receipts NEVER report success (clean/ok/conforms) for skipped, partial, unverified, or cannot-run work.
2. Consistency of outcome, complete, verified, evidence, and exit fields.
3. Embedded `exit` matches the process exit code across the Order 01 0/1/2 classification.
4. Evidence receipts name what was checked rather than raw file contents or sensitive data.
"""

from __future__ import annotations

import io
import json
import unittest

from agent_workflows import agent_schema as schema
from agent_workflows.renderers import AgentRenderer
from agent_workflows.result_types import (
    Change,
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
    OutputContext,
    OutputMode,
)


class AntiGreenwashingInvariantsTests(unittest.TestCase):
    """Assert anti-greenwashing rules: never report ok for incomplete/unverified/cannot-run work."""

    def test_reject_clean_outcome_when_unverified(self):
        # Directly constructed record with verified=False and outcome=clean must fail validation
        rec = {
            "schema": "aw.agent/v1",
            "kind": "result",
            "cmd": "check",
            "outcome": "clean",
            "exit": 0,
            "verified": False,  # Violation!
            "complete": True,
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Greenwash violation" in e for e in errs))
        with self.assertRaises(ValueError):
            schema.assert_valid_agent_record(rec)

    def test_reject_clean_outcome_when_incomplete_non_preview(self):
        # Directly constructed record with complete=False and outcome=clean must fail validation
        rec = {
            "schema": "aw.agent/v1",
            "kind": "result",
            "cmd": "install",
            "outcome": "clean",
            "exit": 0,
            "verified": True,
            "complete": False,  # Violation!
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Greenwash violation" in e for e in errs))
        with self.assertRaises(ValueError):
            schema.assert_valid_agent_record(rec)

    def test_reject_clean_outcome_with_exit_1(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "result",
            "cmd": "check",
            "outcome": "clean",  # Incompatible with exit=1
            "exit": 1,
            "verified": True,
            "complete": True,
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Exit code mismatch" in e for e in errs))

    def test_reject_clean_outcome_with_exit_2(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "result",
            "cmd": "check",
            "outcome": "clean",  # Incompatible with exit=2
            "exit": 2,
            "verified": True,
            "complete": True,
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Exit code mismatch" in e for e in errs))


class ReceiptStatesAndExitParityTests(unittest.TestCase):
    """Assert receipts and exit code parity across all work states (E-02 / V-02)."""

    def _render_and_emit(self, result: CommandResult) -> tuple[int, dict]:
        buf = io.StringIO()
        ctx = OutputContext(mode=OutputMode.AGENT, stdout=buf)
        renderer = AgentRenderer()
        exit_code = renderer.emit(result, ctx)
        output_str = buf.getvalue()
        record = json.loads(output_str.strip())
        return exit_code, record

    def test_clean_state_receipt(self):
        res = CommandResult(
            command="check plans",
            status="clean",
            exit_code=0,
            summary="17 plans checked",
            verified=True,
            complete=True,
            evidence=[Evidence(key="ipd-lint:author", value=True, status="verified")],
            data={"checked": 17},
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 0)
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["outcome"], "clean")
        self.assertTrue(rec["verified"])
        self.assertTrue(rec["complete"])
        self.assertEqual(rec["checked"], 17)
        self.assertEqual(rec["findings"], 0)
        self.assertIn("ipd-lint:author", str(rec["evidence"]))

    def test_findings_state_receipt(self):
        res = CommandResult(
            command="check specs",
            status="findings",
            exit_code=1,
            summary="2 findings",
            verified=True,
            complete=True,
            diagnostics=[
                Diagnostic(
                    location="specs/01.md", rule="spec.draft", detail="missing author"
                ),
                Diagnostic(
                    location="specs/02.md", rule="spec.title", detail="empty title"
                ),
            ],
            evidence=[Evidence(key="spec-lint", value={"errors": 2}, status="fail")],
            next_actions=[NextAction(command="aw check specs --fix")],
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 1)
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["outcome"], "findings")
        self.assertTrue(rec["verified"])
        self.assertTrue(rec["complete"])
        self.assertEqual(rec["findings"], 2)
        self.assertEqual(rec["next"], "aw check specs --fix")

    def test_preview_state_receipt(self):
        res = CommandResult(
            command="rename plans",
            status="preview",
            exit_code=0,
            summary="preview rename",
            target="plans/6psux0",
            applied=False,
            complete=False,
            verified=True,
            changes=[Change(path="plans/old.md", kind="rename", applied=False)],
            next_actions=[
                NextAction(command="aw rename plans 6psux0 --slug new-slug --apply")
            ],
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 0)
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["outcome"], "preview")
        self.assertFalse(rec["applied"])
        self.assertFalse(rec["complete"])
        self.assertTrue(rec["verified"])
        self.assertEqual(rec["target"], "plans/6psux0")
        self.assertEqual(rec["next"], "aw rename plans 6psux0 --slug new-slug --apply")

    def test_skipped_state_receipt(self):
        res = CommandResult(
            command="install",
            status="skipped",
            exit_code=0,
            summary="repo on never-install exclude list",
            complete=False,
            verified=True,
            evidence=[
                Evidence(key="install-exclude-list", value="matched", status="verified")
            ],
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 0)
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["outcome"], "skipped")
        self.assertFalse(rec["complete"])
        self.assertTrue(rec["verified"])

    def test_partial_state_receipt(self):
        res = CommandResult(
            command="install all",
            status="partial",
            exit_code=0,
            summary="3 of 5 repos installed",
            complete=False,
            verified=True,
            data={"installed": 3, "total": 5},
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 0)
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["outcome"], "partial")
        self.assertFalse(rec["complete"])
        self.assertTrue(rec["verified"])

    def test_unverified_state_receipt(self):
        res = CommandResult(
            command="check",
            status="unverified",
            exit_code=1,
            summary="verification probe timeout",
            complete=True,
            verified=False,
            evidence=[Evidence(key="probe-timeout", value=True, status="unverified")],
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 1)
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["outcome"], "unverified")
        self.assertFalse(rec["verified"])

    def test_cannot_run_error_state_receipt(self):
        res = CommandResult(
            command="check invalid_type",
            status="cannot-run",
            exit_code=2,
            summary="unknown artifact type 'invalid_type'",
            complete=False,
            verified=False,
            next_actions=[NextAction(command="aw check --help")],
        )
        proc_exit, rec = self._render_and_emit(res)
        self.assertEqual(proc_exit, 2)
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertFalse(rec["complete"])
        self.assertEqual(rec["next"], "aw check --help")


if __name__ == "__main__":
    unittest.main()
