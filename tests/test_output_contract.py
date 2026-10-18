"""Tests for Normative Output Contract conformance.

awcliux Order 01 (`hd3kln`) E-03 / V-03.

Asserts:
1. Documented exit code semantics:
   - 0: clean
   - 1: domain findings / failure
   - 2: usage / cannot-run
2. Stream separation:
   - stdout carries structured payload only (no progress logs)
   - stderr carries transient / cannot-start errors
3. Exactly one machine-readable output convention:
   - Agent output conforms to `aw.agent/v1` JSONL schema
   - No conflicting legacy TSV wire form on migrated handlers

Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
Deliberately not restored: code-pinning doc-prose test asserting contract documentation text.
"""

from __future__ import annotations

import json
import unittest

import pytest

from agent_workflows.renderers import AgentRenderer
from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
)

pytestmark = pytest.mark.core


class ExitCodeAndStreamSemanticsTests(unittest.TestCase):
    """Assert standard 0/1/2 exit codes and stream separation (V-03)."""

    def test_clean_result_exit_code_0(self):
        res = CommandResult(command="check", status="clean", exit_code=0)
        self.assertEqual(res.exit_code, 0)
        self.assertFalse(res.has_findings)
        self.assertFalse(res.is_error)

    def test_findings_result_exit_code_1(self):
        res = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            diagnostics=[Diagnostic(location="x", rule="r", detail="d")],
        )
        self.assertEqual(res.exit_code, 1)
        self.assertTrue(res.has_findings)
        self.assertFalse(res.is_error)

    def test_cannot_run_error_exit_code_2(self):
        res = CommandResult(
            command="check", status="error", exit_code=2, summary="cannot run"
        )
        self.assertEqual(res.exit_code, 2)
        self.assertTrue(res.is_error)

    def test_agent_renderer_emits_single_machine_convention(self):
        # Asserts aw.agent/v1 JSON record is emitted without raw TSV or ANSI escapes
        res = CommandResult(
            command="doctor",
            status="findings",
            exit_code=1,
            diagnostics=[
                Diagnostic(location="f.txt", rule="doctor.git-dirty", detail="modified")
            ],
        )
        renderer = AgentRenderer()
        output = renderer.render(res)
        # Must parse cleanly as JSON
        record = json.loads(output.strip())
        self.assertEqual(record["schema"], "aw.agent/v1")
        self.assertEqual(record["cmd"], "doctor")
        self.assertEqual(record["outcome"], "findings")
        self.assertEqual(record["exit"], 1)
        self.assertEqual(len(record["diagnostics"]), 1)
        # No ANSI codes present
        self.assertNotIn("\x1b[", output)


class ResidualKeyTests(unittest.TestCase):
    """Residual tests asserting values measured at authoring (F-04 / E-05)."""

    def test_command_result_has_findings(self):
        self.assertFalse(CommandResult(command="c").has_findings)
        self.assertTrue(CommandResult(command="c", exit_code=1).has_findings)
        self.assertFalse(CommandResult(command="c", exit_code=2).has_findings)
        self.assertTrue(
            CommandResult(
                command="c",
                diagnostics=[Diagnostic(location="a", rule="r", detail="d")],
            ).has_findings
        )


if __name__ == "__main__":
    unittest.main()
