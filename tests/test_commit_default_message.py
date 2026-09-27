"""Behavioral tests for aw commit's default commit message derivation (IPD isgno7, backlog qivywd).

Cases:
  (1) no -m, plan with - Id: and an # IPD: <title> H1 -> work(wk0001): <title>
  (2) no -m, plan whose H1 is absent or empty -> work(<id6>): <filename slug> (proves _plan_id6 is used)
  (3) explicit -m "custom subject" -> exactly custom subject
  (4) --no-plan without -m -> exit 2, message names requires -m/--message, HEAD unchanged
  (5) -m "" -> falls through to the derived default (or semantics preserved)
  (6) a title containing backticks, double quotes and $(...) survives VERBATIM in the subject
  (7) unit-level: _default_commit_message on text with no - Id: and a non-clustered filename returns work: <plan_rel> unchanged
"""

from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows.work_cmd import _default_commit_message
from tests import support

_PLAN = """# IPD: Demo work plan

- Date: 2026-08-28
- Kind: child
- Concern: A real concern statement for review.
- Scope: A real scope statement.
- Scope-Paths: src/, tests/
- Item-Dependencies: none
- Status: approved
- Priority: medium
- Work-Kind: chore
- Set: wk
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: wk0001

## Workflow history
- 2026-08-28 approved (aw set): approved

## Goal
A real goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: work
- [ ] E-01 Do a real observable thing.
  - Depends on: none
  - Expected outcome: a real observable result.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: a real falsifiable evidence statement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


class CommitDefaultMessageTest(unittest.TestCase):
    def setUp(self):
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.plan_path = self.plans / "20260828-wk-01-wk0001-demo.ipd.md"
        self.plan_path.write_text(_PLAN, encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "f.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 1
        output = out.getvalue() + err.getvalue()
        return rc, output

    def _last_commit_subject(self) -> str:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()

    def _head(self) -> str:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()

    def test_case_1_no_message_derives_id6_and_title(self):
        """Case (1): no -m, plan with - Id: and an # IPD: <title> H1 -> work(wk0001): <title>."""
        (self.root / "src" / "f.py").write_text("print('change 1')\n", encoding="utf-8")
        rc, out = self._run(
            ["commit", "wk0001", "--dir", str(self.root), "--", "src/f.py"]
        )
        self.assertEqual(rc, 0, f"aw commit failed with output:\n{out}")
        self.assertEqual(self._last_commit_subject(), "work(wk0001): Demo work plan")

    def test_case_2_no_message_title_absent_falls_back_to_slug(self):
        """Case (2): no -m, plan whose H1 is absent -> work(<id6>): <filename slug>.

        Proves that the id6 reader is _plan_id6 and not ipd_lint.parse().meta_fields,
        because ipd_lint.parse() returns empty meta_fields when the H1 header is absent.
        """
        titleless = "\n".join(
            ln for ln in _PLAN.splitlines() if not ln.startswith("# IPD:")
        )
        self.plan_path.write_text(titleless, encoding="utf-8")
        (self.root / "src" / "f.py").write_text("print('change 2')\n", encoding="utf-8")
        rc, out = self._run(
            ["commit", "wk0001", "--dir", str(self.root), "--", "src/f.py"]
        )
        self.assertEqual(rc, 0, f"aw commit failed with output:\n{out}")
        self.assertEqual(self._last_commit_subject(), "work(wk0001): demo")

    def test_case_3_explicit_message_honored(self):
        """Case (3): explicit -m 'custom subject' -> exactly custom subject."""
        (self.root / "src" / "f.py").write_text("print('change 3')\n", encoding="utf-8")
        rc, out = self._run(
            [
                "commit",
                "wk0001",
                "-m",
                "custom subject",
                "--dir",
                str(self.root),
                "--",
                "src/f.py",
            ]
        )
        self.assertEqual(rc, 0, f"aw commit failed with output:\n{out}")
        self.assertEqual(self._last_commit_subject(), "custom subject")

    def test_case_4_no_plan_without_message_refuses(self):
        """Case (4): --no-plan without -m -> exit 2, names requires -m/--message, HEAD unchanged."""
        (self.root / "src" / "f.py").write_text("print('change 4')\n", encoding="utf-8")
        head_before = self._head()
        rc, out = self._run(
            ["commit", "--no-plan", "--dir", str(self.root), "--", "src/f.py"]
        )
        self.assertEqual(rc, 2)
        self.assertIn("requires -m/--message", out)
        self.assertEqual(self._head(), head_before)

    def test_case_5_empty_message_falls_through_to_derived_default(self):
        """Case (5): -m '' -> falls through to the derived default, preserving 'or' semantics."""
        (self.root / "src" / "f.py").write_text("print('change 5')\n", encoding="utf-8")
        rc, out = self._run(
            ["commit", "wk0001", "-m", "", "--dir", str(self.root), "--", "src/f.py"]
        )
        self.assertEqual(rc, 0, f"aw commit failed with output:\n{out}")
        self.assertEqual(self._last_commit_subject(), "work(wk0001): Demo work plan")

    def test_case_6_title_punctuation_preserved_verbatim(self):
        """Case (6): a title containing backticks, double quotes and $(...) survives VERBATIM in subject."""
        custom_title = '`refactor` and $(cmd) "foo"'
        custom_plan = _PLAN.replace("# IPD: Demo work plan", f"# IPD: {custom_title}")
        self.plan_path.write_text(custom_plan, encoding="utf-8")
        (self.root / "src" / "f.py").write_text("print('change 6')\n", encoding="utf-8")
        rc, out = self._run(
            ["commit", "wk0001", "--dir", str(self.root), "--", "src/f.py"]
        )
        self.assertEqual(rc, 0, f"aw commit failed with output:\n{out}")
        expected_subject = f"work(wk0001): {custom_title}"
        self.assertEqual(self._last_commit_subject(), expected_subject)

    def test_case_7_unit_level_no_id6_and_non_clustered_returns_plan_rel(self):
        """Case (7): unit-level _default_commit_message on text with no - Id: and non-clustered filename."""
        text_without_id = "# Just some notes\n\nNo id front matter here.\n"
        result = _default_commit_message(text_without_id, "notes/scratch.txt")
        self.assertEqual(result, "work: notes/scratch.txt")
