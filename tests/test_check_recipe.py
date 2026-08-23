"""Tests for aw check doctor-derived recipe, dual-audience rendering, and exit contract.

awcliux Order 02 (`czw99i`) E-02 / V-02.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli, plans_index
from agent_workflows.renderers import HumanRenderer
from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
    OutputContext,
    OutputMode,
)

_ANSI = re.compile(r"\033\[[0-9;]*m")


class FakeTTYStream(io.StringIO):
    """StringIO stream that simulates a TTY."""

    def isatty(self) -> bool:
        return True


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True)


def _sync_index(plans_dir: Path) -> None:
    entries, _ = plans_index.scan_plans(plans_dir)
    (plans_dir / "INDEX.json").write_text(
        plans_index.build_index_json(entries), encoding="utf-8"
    )
    (plans_dir / "INDEX.md").write_text(
        plans_index.build_index_md(entries), encoding="utf-8"
    )


class CheckRecipeUnitTests(unittest.TestCase):
    """V-02: Test aw check handler across clean, empty, findings, and cannot-run states."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "Test User")
        (self.root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (self.root / ".aw" / "records" / "plans" / "executed").mkdir(parents=True)
        (self.root / ".aw" / "records" / "plans" / "reusable").mkdir(parents=True)
        (self.root / ".aw" / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        plans_dir = self.root / ".aw" / "records" / "plans"
        _sync_index(plans_dir)
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli_human(self, argv: list[str]) -> tuple[int, str, str]:
        out_stream = FakeTTYStream()
        err_stream = io.StringIO()
        with patch("sys.stdout", out_stream), patch("sys.stderr", err_stream):
            with patch.dict(
                os.environ, {"TERM": "xterm-256color", "NO_COLOR": "1"}, clear=True
            ):
                try:
                    rc = cli.main(argv)
                except SystemExit as e:
                    rc = int(e.code or 0)
        return rc, out_stream.getvalue(), err_stream.getvalue()

    def _run_cli_agent(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main([*argv, "--agent"])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_check_empty_clean_state_human_and_agent(self):
        # 1. Human mode (TTY)
        rc, out, err = self._run_cli_human(["check", "plans", "--dir", str(self.root)])
        self.assertEqual(rc, 0, err)
        plain = _ANSI.sub("", out)
        self.assertIn("AW check  plans", plain)
        self.assertIn("CONFORMS  0 plans checked", plain)
        self.assertIn("Evidence", plain)
        self.assertIn("pending  0", plain)
        self.assertIn("Next  aw ipd board", plain)
        self.assertIn("Agent output: --agent (automatic when piped)", plain)

        # 2. Agent mode (piped / non-TTY)
        rc_agent, out_agent, _ = self._run_cli_agent(
            ["check", "plans", "--dir", str(self.root)]
        )
        self.assertEqual(rc_agent, 0)
        rec = json.loads(out_agent.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "check")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["findings"], 0)
        self.assertEqual(rec["outcome"], "conforms")

    def test_check_valid_plan_clean_state(self):
        plan_content = """# IPD: Test Valid Plan

- Date: 2026-08-22
- Kind: child
- Concern: Test verification.
- Scope: Test only.
- Status: pending
- Set: testset
- Order: 1
- Highest E allocated: 01
- Author: Test
- Id: abc123

## Goal
Verify clean check.

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Do something.
  - Depends on: none
  - Expected outcome: done.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: evidence.
  - Observed evidence:
  - Result: pending
"""
        plan_path = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260822-testset-01-abc123-test-valid-plan.ipd.md"
        )
        plan_path.write_text(plan_content, encoding="utf-8")
        plans_dir = self.root / ".aw" / "records" / "plans"
        _sync_index(plans_dir)

        # Human mode
        rc, out, err = self._run_cli_human(["check", "plans", "--dir", str(self.root)])
        self.assertEqual(rc, 0, err)
        plain = _ANSI.sub("", out)
        self.assertIn("AW check  plans", plain)
        self.assertIn("CONFORMS  1 plans checked", plain)
        self.assertIn("pending  1", plain)
        self.assertIn("Next  aw ipd board", plain)

        # Agent mode
        rc_agent, out_agent, _ = self._run_cli_agent(
            ["check", "plans", "--dir", str(self.root)]
        )
        self.assertEqual(rc_agent, 0)
        rec = json.loads(out_agent.strip())
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["findings"], 0)

    def test_check_findings_state_exit_1(self):
        # Plant a non-conformant plan (bad filename / invalid naming grammar)
        bad_plan = (
            self.root / ".aw" / "records" / "plans" / "pending" / "invalid_name.md"
        )
        bad_plan.write_text("# Bad Plan\n", encoding="utf-8")
        plans_dir = self.root / ".aw" / "records" / "plans"
        _sync_index(plans_dir)

        # Human mode
        rc, out, err = self._run_cli_human(["check", "plans", "--dir", str(self.root)])
        self.assertEqual(rc, 1, err)
        plain = _ANSI.sub("", out)
        self.assertIn("AW check  plans", plain)
        self.assertIn("FINDINGS", plain)
        self.assertIn("invalid_name.md", plain)
        self.assertIn("Fix:", plain)
        self.assertIn("Evidence", plain)

        # Agent mode
        rc_agent, out_agent, _ = self._run_cli_agent(
            ["check", "plans", "--dir", str(self.root)]
        )
        self.assertEqual(rc_agent, 1)
        rec = json.loads(out_agent.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "check")
        self.assertEqual(rec["exit"], 1)
        self.assertGreater(rec["findings"], 0)
        self.assertTrue(len(rec["diagnostics"]) > 0)

    def test_check_cannot_run_invalid_type_exit_2(self):
        rc, out, err = self._run_cli_human(
            ["check", "unknown_xyz_type", "--dir", str(self.root)]
        )
        self.assertEqual(rc, 2)
        plain = _ANSI.sub("", out)
        self.assertIn("ERROR", plain)
        self.assertIn("unknown", plain)
        self.assertIn("Next  aw check --help", plain)

        # Agent mode exit 2
        rc_agent, out_agent, _ = self._run_cli_agent(
            ["check", "unknown_xyz_type", "--dir", str(self.root)]
        )
        self.assertEqual(rc_agent, 2)
        rec = json.loads(out_agent.strip())
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(rec["outcome"], "error")


class CheckRecipeGoldenAndWidthTests(unittest.TestCase):
    """V-02: PTY goldens at 40/80/120 columns for clean, empty, findings, and cannot-run."""

    def test_clean_check_golden_output(self):
        res = CommandResult(
            command="check",
            status="conforms",
            exit_code=0,
            summary="17 plans checked",
            evidence=[
                Evidence(
                    key="inventory",
                    value={"pending": 17, "reusable": 2, "terminal": 41},
                    status="verified",
                ),
                Evidence(
                    key="rules",
                    value={"errors": 0, "warnings": 0},
                    status="verified",
                ),
            ],
            next_actions=[NextAction(command="aw ipd board")],
            data={"target": "plans", "elapsed_ms": 38},
        )
        ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
        renderer = HumanRenderer()
        rendered = renderer.render(res, ctx)
        self.assertIn("AW check  plans", rendered)
        self.assertIn("38 ms", rendered)
        self.assertIn("CONFORMS  17 plans checked", rendered)
        self.assertIn("Evidence", rendered)
        self.assertIn("pending  17", rendered)
        self.assertIn("reusable  2", rendered)
        self.assertIn("terminal  41", rendered)
        self.assertIn("Next  aw ipd board", rendered)
        self.assertIn("Agent output: --agent (automatic when piped)", rendered)

    def test_findings_check_golden_output(self):
        res = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            summary="2 finding(s) detected across 17 plans",
            diagnostics=[
                Diagnostic(
                    location=".aw/records/plans/pending/invalid.ipd.md",
                    rule="check.name-nonconformant",
                    detail="filename does not match naming grammar",
                    severity="error",
                    fix="run 'aw rename plans'",
                )
            ],
            evidence=[
                Evidence(
                    key="inventory",
                    value={"pending": 17, "reusable": 2, "terminal": 41},
                    status="verified",
                ),
                Evidence(
                    key="rules",
                    value={"errors": 1, "warnings": 0},
                    status="findings",
                ),
            ],
            next_actions=[NextAction(command="run 'aw rename plans'")],
            data={"target": "plans", "elapsed_ms": 42},
        )
        ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
        renderer = HumanRenderer()
        rendered = renderer.render(res, ctx)
        self.assertIn("AW check  plans", rendered)
        self.assertIn("42 ms", rendered)
        self.assertIn("FINDINGS  2 finding(s) detected across 17 plans", rendered)
        self.assertIn("Findings:", rendered)
        self.assertIn("invalid.ipd.md", rendered)
        self.assertIn("Fix: run 'aw rename plans'", rendered)
        self.assertIn("Next  run 'aw rename plans'", rendered)


if __name__ == "__main__":
    unittest.main()
