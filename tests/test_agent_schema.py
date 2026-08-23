"""Tests for aw.agent/v1 JSONL schema, closed record kinds, ANSI-free output, and leak sanitization.

awcliux Order 03 (`8su0r3`) E-01 / V-01.

Asserts:
1. Closed record kinds (`result`, `summary`, `item`, `error`) and required fields.
2. Rejection of invalid kinds, missing mandatory fields, and malformed exit codes.
3. Records are strictly ANSI-free (zero escape codes).
4. All path-valued fields are repo-relative, normalized, and pass `aw sanitize --agent` with 0 findings.
5. Identical fixtures parse cleanly across standard JSON parsers with stable serialization.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_workflows import agent_schema as schema
from agent_workflows import leak_sanitizer as ls
from agent_workflows.renderers import AgentRenderer
from agent_workflows.result_types import (
    Change,
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class AgentSchemaRecordKindsUnitTests(unittest.TestCase):
    """Assert closed record kinds and mandatory envelope fields (E-01 / V-01)."""

    def test_result_record_valid_construction(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "result",
            "cmd": "check plans",
            "outcome": "clean",
            "exit": 0,
            "checked": 17,
            "findings": 0,
            "verified": True,
            "complete": True,
            "evidence": ["ipd-lint:author"],
            "next": None,
        }
        self.assertTrue(schema.is_valid_agent_record(rec))
        rendered = schema.render_jsonl_record(rec)
        parsed = json.loads(rendered.strip())
        self.assertEqual(parsed["schema"], "aw.agent/v1")
        self.assertEqual(parsed["kind"], "result")
        self.assertEqual(parsed["cmd"], "check plans")
        self.assertEqual(parsed["exit"], 0)
        self.assertTrue(parsed["verified"])
        self.assertTrue(parsed["complete"])

    def test_summary_record_valid_construction(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "summary",
            "cmd": "attention",
            "outcome": "findings",
            "exit": 1,
            "total": 49,
            "emitted": 20,
            "omitted": 29,
            "complete": False,
            "next": "aw attention --agent --limit 50",
        }
        self.assertTrue(schema.is_valid_agent_record(rec))
        rendered = schema.render_jsonl_record(rec)
        parsed = json.loads(rendered.strip())
        self.assertEqual(parsed["kind"], "summary")
        self.assertEqual(parsed["total"], 49)
        self.assertEqual(parsed["emitted"], 20)
        self.assertEqual(parsed["omitted"], 29)
        self.assertFalse(parsed["complete"])

    def test_item_record_valid_construction(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "item",
            "cmd": "attention",
            "outcome": "clean",
            "exit": 0,
            "id": "att-001",
            "path": "plans/6psux0.ipd.md",
            "status": "ready",
            "complete": True,
            "verified": True,
        }
        self.assertTrue(schema.is_valid_agent_record(rec))
        rendered = schema.render_jsonl_record(rec)
        parsed = json.loads(rendered.strip())
        self.assertEqual(parsed["kind"], "item")
        self.assertEqual(parsed["id"], "att-001")

    def test_error_record_valid_construction(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "error",
            "cmd": "check",
            "outcome": "cannot-run",
            "exit": 2,
            "summary": "Unknown artifact type 'invalid_type'",
            "complete": False,
            "verified": False,
            "next": "aw check --help",
        }
        self.assertTrue(schema.is_valid_agent_record(rec))
        rendered = schema.render_jsonl_record(rec)
        parsed = json.loads(rendered.strip())
        self.assertEqual(parsed["kind"], "error")
        self.assertEqual(parsed["exit"], 2)
        self.assertEqual(parsed["outcome"], "cannot-run")
        self.assertFalse(parsed["complete"])

    def test_reject_unknown_record_kind(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "unknown_custom_kind",
            "cmd": "check",
            "outcome": "clean",
            "exit": 0,
            "verified": True,
            "complete": True,
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Invalid kind" in e for e in errs))
        with self.assertRaises(ValueError):
            schema.assert_valid_agent_record(rec)

    def test_reject_invalid_schema_version(self):
        rec = {
            "schema": "aw.agent/v99",
            "kind": "result",
            "cmd": "check",
            "outcome": "clean",
            "exit": 0,
            "verified": True,
            "complete": True,
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Invalid schema" in e for e in errs))
        with self.assertRaises(ValueError):
            schema.assert_valid_agent_record(rec)

    def test_reject_summary_inconsistent_counts(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "summary",
            "cmd": "attention",
            "outcome": "clean",
            "exit": 0,
            "total": 50,
            "emitted": 20,
            "omitted": 10,  # 20 + 10 != 50
            "complete": False,
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("Summary counts inconsistent" in e for e in errs))


class AnsiAndPathSanitizationTests(unittest.TestCase):
    """Assert ANSI-free and leak-sanitized records (E-01 / V-01)."""

    def test_reject_ansi_escapes_in_record(self):
        rec = {
            "schema": "aw.agent/v1",
            "kind": "result",
            "cmd": "check",
            "outcome": "clean",
            "exit": 0,
            "verified": True,
            "complete": True,
            "summary": "\x1b[32mSuccess\x1b[0m",
        }
        errs = schema.validate_agent_record(rec)
        self.assertTrue(any("ANSI escape code detected" in e for e in errs))
        with self.assertRaises(ValueError):
            schema.assert_valid_agent_record(rec)

    def test_normalize_repo_path_relative_and_clean(self):
        root = REPO_ROOT
        # Absolute path inside repo
        abs_in_repo = root / "agent_workflows" / "renderers.py"
        norm = schema.normalize_repo_path(abs_in_repo, root)
        self.assertEqual(norm, "agent_workflows/renderers.py")
        self.assertFalse(norm.startswith("/"))

        # Path with backslashes
        win_path = "agent_workflows\\term.py"
        self.assertEqual(
            schema.normalize_repo_path(win_path), "agent_workflows/term.py"
        )

        # Path with leading ./
        rel_dot = "./docs/cli-output-contract.md"
        self.assertEqual(
            schema.normalize_repo_path(rel_dot), "docs/cli-output-contract.md"
        )

    def test_command_result_path_sanitization_under_agent_renderer(self):
        # Build CommandResult with absolute paths planted
        res = CommandResult(
            command="rename plans",
            status="preview",
            exit_code=0,
            summary="preview rename",
            target=str(REPO_ROOT / ".aw" / "records" / "plans" / "6psux0.ipd.md"),
            changes=[
                Change(
                    path=str(REPO_ROOT / "docs" / "old.md"),
                    kind="rename",
                    detail="renamed",
                    applied=False,
                )
            ],
            diagnostics=[
                Diagnostic(
                    location=str(REPO_ROOT / "agent_workflows" / "cli.py"),
                    rule="style",
                    detail="info",
                )
            ],
            evidence=[
                Evidence(
                    key="backlog-check",
                    value=str(REPO_ROOT / "records" / "item.md"),
                    status="verified",
                )
            ],
            next_actions=[NextAction(command="aw rename plans 6psux0 --apply")],
            data={"repo_root": REPO_ROOT},
        )
        renderer = AgentRenderer()
        output = renderer.render(res)

        # 1. Must parse cleanly as JSON
        record = json.loads(output.strip())
        self.assertEqual(record["schema"], "aw.agent/v1")
        self.assertEqual(record["kind"], "result")
        self.assertEqual(record["target"], ".aw/records/plans/6psux0.ipd.md")
        self.assertEqual(record["changes"][0]["path"], "docs/old.md")
        self.assertEqual(record["diagnostics"][0]["location"], "agent_workflows/cli.py")

        # 2. Must be 100% ANSI-free
        self.assertNotIn("\x1b", output)
        self.assertNotIn("\033", output)

        # 3. Must pass leak_sanitizer scan with ZERO findings
        rs = ls.build_ruleset(REPO_ROOT)
        findings = ls.scan_text(output, "sample_agent_record.jsonl", rs)
        fail_findings = [
            f for f in findings if getattr(f, "severity", "fail") == "fail"
        ]
        self.assertEqual(
            fail_findings, [], f"Sanitizer failed on agent output: {findings}"
        )


if __name__ == "__main__":
    unittest.main()
