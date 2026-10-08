"""Tests for the guarded aw.agent/v1 record serializer and AgentRenderer degradation.

IPD wqiofa / Set un6ppd (Order 01).
Pins the guarded serializer seam in agent_schema, strict-mode controls under pytest,
the no-leak property across all F-05 violation classes, byte-identity on valid records,
AgentRenderer degradation behavior, and the honesty bounds on hand-built CLI crash sites.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock

from agent_workflows.agent_schema import (
    LAST_RESORT_ERROR_DIAGNOSTIC,
    SCHEMA_VERSION,
    _ANSI_ESCAPE_RE,
    _HOME_PATH_RE,
    is_valid_agent_record,
    render_guarded_jsonl_record,
    render_jsonl_record,
    validate_agent_record,
)
from agent_workflows.renderers import AgentRenderer
from agent_workflows.result_types import (
    CommandResult,
    OutputContext,
    OutputMode,
)


# F-05 violation classes fixture builder
_TEST_HOME = "/home/" + "testuser"


def make_f05_violation_records() -> Dict[str, Dict[str, Any]]:
    """Build one invalid raw agent record per F-05 violation class plus Unknown outcome."""
    return {
        "class_1_out_of_range_exit": {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "clean",
            "exit": 7,
            "verified": True,
            "complete": True,
        },
        "class_2_home_path_in_next": {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "clean",
            "exit": 0,
            "verified": True,
            "complete": True,
            "next": f"aw install {_TEST_HOME}/proj",
        },
        "class_3_home_path_in_evidence": {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "clean",
            "exit": 0,
            "verified": True,
            "complete": True,
            "evidence": [{"key": "path", "value": f"{_TEST_HOME}/secret"}],
        },
        "class_4_home_path_in_diagnostics": {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "findings",
            "exit": 1,
            "verified": True,
            "complete": True,
            "diagnostics": [
                {
                    "location": "test.py",
                    "rule": "check.rule",
                    "fix": f"{_TEST_HOME}/fix.sh",
                }
            ],
        },
        "class_5_ansi_in_diagnostics": {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "findings",
            "exit": 1,
            "verified": True,
            "complete": True,
            "diagnostics": [{"location": "test.py", "rule": "\x1b[31mbad-rule\x1b[0m"}],
        },
        "class_6_unknown_outcome": {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "nonsense_outcome",
            "exit": 0,
            "verified": True,
            "complete": True,
        },
    }


class AgentRecordGuardTests(unittest.TestCase):
    """Pin the guarded serializer seam and degrade behavior."""

    def test_guarded_serializer_substitutes_on_invalid_records(self) -> None:
        """Invalid records degrade to a valid kind=error record with exit=2 in guarded mode."""
        classes = make_f05_violation_records()
        for class_name, raw_rec in classes.items():
            with self.subTest(class_name=class_name):
                line = render_guarded_jsonl_record(raw_rec, strict=False)
                parsed = json.loads(line)
                self.assertEqual(parsed.get("schema"), SCHEMA_VERSION)
                self.assertEqual(parsed.get("kind"), "error")
                self.assertEqual(parsed.get("outcome"), "error")
                self.assertEqual(parsed.get("exit"), 2)
                self.assertFalse(parsed.get("verified"))
                self.assertFalse(parsed.get("complete"))
                self.assertEqual(validate_agent_record(parsed), [])

    def test_no_leak_property(self) -> None:
        """The substitute record's serialized line never leaks home paths, ANSI escapes, or offending values."""
        classes = make_f05_violation_records()
        offending_literals = {
            "class_1_out_of_range_exit": "7",
            "class_2_home_path_in_next": f"{_TEST_HOME}/proj",
            "class_3_home_path_in_evidence": f"{_TEST_HOME}/secret",
            "class_4_home_path_in_diagnostics": f"{_TEST_HOME}/fix.sh",
            "class_5_ansi_in_diagnostics": "\x1b[31m",
            "class_6_unknown_outcome": "nonsense_outcome",
        }
        for class_name, raw_rec in classes.items():
            with self.subTest(class_name=class_name):
                line = render_guarded_jsonl_record(raw_rec, strict=False)
                self.assertIsNone(
                    _HOME_PATH_RE.search(line),
                    f"Home path leaked in {class_name}: {line}",
                )
                self.assertIsNone(
                    _ANSI_ESCAPE_RE.search(line),
                    f"ANSI escape leaked in {class_name}: {line}",
                )
                literal = offending_literals[class_name]
                self.assertNotIn(
                    literal,
                    line,
                    f"Literal offending value {literal!r} leaked in {class_name}: {line}",
                )

    def test_strict_mode_controls(self) -> None:
        """Strict mode re-raises original ValueError with unredacted message."""
        raw_rec = {
            "schema": SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test",
            "outcome": "clean",
            "exit": 7,
            "verified": True,
            "complete": True,
        }
        # Explicit strict=True re-raises original unredacted ValueError
        with self.assertRaises(ValueError) as ctx:
            render_guarded_jsonl_record(raw_rec, strict=True)
        self.assertIn("'7'", str(ctx.exception))

        # Default under pytest (PYTEST_CURRENT_TEST set) raises
        with mock.patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_fn"}):
            with self.assertRaises(ValueError):
                render_guarded_jsonl_record(raw_rec)

        # Default outside pytest (production) returns substitute
        with mock.patch.dict(os.environ, {}, clear=True):
            line = render_guarded_jsonl_record(raw_rec)
            parsed = json.loads(line)
            self.assertEqual(parsed.get("kind"), "error")
            self.assertEqual(parsed.get("exit"), 2)

    def test_byte_identity_on_valid_records(self) -> None:
        """For all valid records across diverse combinations, guarded serializer output is byte-identical."""
        valid_records: List[Dict[str, Any]] = [
            {
                "schema": SCHEMA_VERSION,
                "kind": "result",
                "cmd": "check",
                "outcome": "clean",
                "exit": 0,
                "verified": True,
                "complete": True,
                "findings": 0,
                "next": None,
            },
            {
                "schema": SCHEMA_VERSION,
                "kind": "result",
                "cmd": "doctor",
                "outcome": "findings",
                "exit": 1,
                "verified": True,
                "complete": True,
                "findings": 2,
                "diagnostics": [{"location": "foo.py", "rule": "r1"}],
                "next": "aw fix",
            },
            {
                "schema": SCHEMA_VERSION,
                "kind": "result",
                "cmd": "rename",
                "outcome": "preview",
                "exit": 0,
                "verified": True,
                "complete": False,
                "applied": False,
                "changes": [{"kind": "modify", "path": "file.txt"}],
                "next": "aw rename --apply",
            },
            {
                "schema": SCHEMA_VERSION,
                "kind": "summary",
                "cmd": "find",
                "outcome": "clean",
                "exit": 0,
                "total": 10,
                "emitted": 4,
                "omitted": 6,
                "complete": False,
                "next": "aw find --limit 10",
            },
            {
                "schema": SCHEMA_VERSION,
                "kind": "error",
                "cmd": "project",
                "outcome": "cannot-run",
                "exit": 2,
                "verified": False,
                "complete": False,
                "next": "aw project init",
            },
        ]
        for rec in valid_records:
            strict_out = render_jsonl_record(rec)
            guarded_out = render_guarded_jsonl_record(rec, strict=False)
            self.assertEqual(strict_out, guarded_out)

    def test_floor_record_fallback_conformance(self) -> None:
        """Floor record constant is provably conforming and validates clean."""
        floor_rec = {
            "schema": SCHEMA_VERSION,
            "kind": "error",
            "cmd": "aw",
            "exit": 2,
            "outcome": "error",
            "verified": False,
            "complete": False,
            "error": LAST_RESORT_ERROR_DIAGNOSTIC,
            "next": None,
        }
        self.assertEqual(validate_agent_record(floor_rec), [])
        self.assertTrue(is_valid_agent_record(floor_rec))

    def test_agent_renderer_emit_guarded_production(self) -> None:
        """In production (non-pytest) mode, AgentRenderer.emit writes a conforming record."""
        result = CommandResult(command="test", exit_code=7)
        renderer = AgentRenderer()
        buf = io.StringIO()
        ctx = OutputContext(mode=OutputMode.AGENT, stdout=buf)

        with mock.patch.dict(os.environ, {}, clear=True):
            rc = renderer.emit(result, ctx)
            self.assertEqual(rc, 7)
            output = buf.getvalue()
            self.assertTrue(len(output) > 0)
            parsed = json.loads(output)
            self.assertEqual(parsed.get("kind"), "error")
            self.assertEqual(parsed.get("outcome"), "error")
            self.assertEqual(parsed.get("exit"), 2)
            self.assertEqual(validate_agent_record(parsed), [])


class HonestyBoundSubprocessTests(unittest.TestCase):
    """Assert previously disclosed honesty bounds (hand-built crash sites in attention and runs) now emit valid exit 2 refusals (resolved by enygec/z7ci8k)."""

    def test_attention_agent_with_home_path_refuses(self) -> None:
        env = {**os.environ, "AW_NO_REEXEC": "1"}
        target = str(Path.home() / "nonexistent")
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "attention", target, "--agent"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertNotIn("ValueError", proc.stderr)
        parsed = json.loads(proc.stdout)
        self.assertEqual(parsed.get("exit"), 2)
        self.assertEqual(parsed.get("outcome"), "cannot-run")
        self.assertEqual(validate_agent_record(parsed), [])

    def test_attention_json_with_home_path_refuses(self) -> None:
        env = {**os.environ, "AW_NO_REEXEC": "1"}
        target = str(Path.home() / "nonexistent")
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "attention", target, "--json"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertNotIn("ValueError", proc.stderr)
        parsed = json.loads(proc.stdout)
        self.assertEqual(parsed.get("exit"), 2)
        self.assertEqual(parsed.get("outcome"), "cannot-run")

    def test_runs_agent_with_home_path_refuses(self) -> None:
        env = {**os.environ, "AW_NO_REEXEC": "1"}
        target = str(Path.home() / "nonexistent")
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", target, "--agent"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertNotIn("ValueError", proc.stderr)
        parsed = json.loads(proc.stdout)
        self.assertEqual(parsed.get("exit"), 2)
        self.assertEqual(parsed.get("outcome"), "cannot-run")
        self.assertEqual(validate_agent_record(parsed), [])
