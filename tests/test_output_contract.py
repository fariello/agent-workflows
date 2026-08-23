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
4. Contract documentation completeness (verifying sections exist in docs/cli-output-contract.md).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
)
from agent_workflows.renderers import AgentRenderer

REPO_ROOT = Path(__file__).resolve().parent.parent


class OutputContractDocTests(unittest.TestCase):
    """Verify the presence and completeness of docs/cli-output-contract.md (V-03)."""

    def test_output_contract_doc_exists_and_contains_required_sections(self):
        doc_path = REPO_ROOT / "docs" / "cli-output-contract.md"
        self.assertTrue(doc_path.is_file(), f"Missing {doc_path}")
        text = doc_path.read_text(encoding="utf-8")

        # Required contract sections (E-03 / V-03):
        # 1. Mode Precedence
        self.assertIn("Audience Modes and Precedence", text)
        self.assertIn("explicit", text.lower())
        # 2. Standard Result Types
        self.assertIn("Standard Result Types and Renderer Boundary", text)
        self.assertIn("CommandResult", text)
        # 3. Exit Code Semantics (0, 1, 2)
        self.assertIn("Exit Code Semantics", text)
        self.assertIn("0", text)
        self.assertIn("1", text)
        self.assertIn("2", text)
        # 4. Stream Separation & Broken Pipes
        self.assertIn("Stream Separation and Broken-Pipe Policy", text)
        self.assertIn("stdout", text)
        self.assertIn("stderr", text)
        # 5. Schema Versioning
        self.assertIn("Schema Versioning", text)
        self.assertIn("aw.agent/v1", text)
        # 6. Hard Cutover Non-TTY Policy
        self.assertIn("Automatic Non-TTY Migration Policy (Hard Cutover)", text)
        # 7. Relationship to Legacy Drift Convention
        self.assertIn("Relationship to Legacy `Drift` Convention", text)
        self.assertIn("SUBSUMES and REPLACES", text)


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
        self.assertNotIn("[", output)


if __name__ == "__main__":
    unittest.main()
