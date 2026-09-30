"""Unit tests for segment-aware Scope-Paths matching and fence callers (IPD mxja4g)."""

from __future__ import annotations

import argparse
import io
import subprocess
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_workflows import ipd_lifecycle
from agent_workflows import work_cmd


class ScopeMatchUnitTests(unittest.TestCase):
    """Table-driven unit tests for ipd_lifecycle._scope_match."""

    def test_scope_match_table(self) -> None:
        # Table entries: (path, pattern, expected, reason)
        cases = [
            # --- MUST-REFUSE: Suffix after '**' must not be dropped ---
            (
                ".aw/records/backlog/open/anything.backlog.md",
                ".aw/records/**/index.md",
                False,
                "Backlog file must not match records index.md pattern via dropped suffix",
            ),
            (
                ".aw/records/specs/x.spec.md",
                ".aw/records/**/index.md",
                False,
                "Spec file must not match records index.md pattern via dropped suffix",
            ),
            (
                ".aw/records/research/20260901-topic.md",
                ".aw/records/**/index.md",
                False,
                "Research file must not match records index.md pattern via dropped suffix",
            ),
            (
                ".aw/records/comms/shared/inbox/msg.md",
                ".aw/records/**/index.md",
                False,
                "Comms inbox file must not match records index.md pattern via dropped suffix",
            ),
            (
                "tests/anything.txt",
                "tests/**/*.py",
                False,
                "Non-python file must not match tests/**/*.py via dropped suffix",
            ),
            (
                "agent_workflows/README.md",
                "agent_workflows/**/*.py",
                False,
                "Markdown file must not match agent_workflows/**/*.py via dropped suffix",
            ),
            # --- MUST-REFUSE: Out-of-prefix path ---
            (
                ".aw/records/specs/x.spec.md",
                ".aw/records/plans/**",
                False,
                "Spec path outside plans directory must not match plans pattern",
            ),
            # --- MUST-REFUSE: Single '*' must not cross '/' ---
            (
                "tests/sub/a.py",
                "tests/*.py",
                False,
                "Single '*' wildcard must not cross directory separator",
            ),
            # --- MUST-ACCEPT: Trailing /** directory-bounded ---
            (
                "a",
                "a/**",
                True,
                "Base directory exact match against dir/** pattern",
            ),
            (
                "a/b/c",
                "a/**",
                True,
                "Nested path match against dir/** pattern",
            ),
            # --- MUST-ACCEPT: Zero-segment '**' ---
            (
                "tests/a.py",
                "tests/**/*.py",
                True,
                "Zero-segment match for '**' in tests/**/*.py",
            ),
            (
                ".aw/records/index.md",
                ".aw/records/**/index.md",
                True,
                "Zero-segment match for '**' in .aw/records/**/index.md",
            ),
            # --- MUST-ACCEPT: One or more segments '**' ---
            (
                ".aw/records/plans/index.md",
                ".aw/records/**/index.md",
                True,
                "One-segment match for '**' in .aw/records/**/index.md",
            ),
            (
                "tests/x/y/a.py",
                "tests/**/*.py",
                True,
                "Multi-segment match for '**' in tests/**/*.py",
            ),
            # --- MUST-ACCEPT: Trailing slash and bare directory literal ---
            (
                "tests/test_a.py",
                "tests/",
                True,
                "Trailing slash directory pattern matches file underneath",
            ),
            (
                "agent_workflows/x.py",
                "agent_workflows",
                True,
                "Bare directory literal matches file underneath",
            ),
            # --- MUST-ACCEPT: Multiple '**' segments ---
            (
                "a/b/c/d/e",
                "a/**/c/**/e",
                True,
                "Multiple '**' segments correctly match intermediate segments",
            ),
        ]

        for path, pattern, expected, reason in cases:
            with self.subTest(path=path, pattern=pattern, reason=reason):
                actual = ipd_lifecycle._scope_match(path, pattern)
                self.assertEqual(
                    actual,
                    expected,
                    f"Failed for {path!r} vs {pattern!r}: expected {expected}, got {actual}. Reason: {reason}",
                )

    def test_pathological_glob_avoids_exponential_time(self) -> None:
        """Assert multiple '**' segments do not exhibit exponential backtracking."""
        path = "a/" + "/".join(["x"] * 30) + "/z"
        pattern = "a/**/**/**/**/**/**/z_nonmatching"
        start = time.perf_counter()
        result = ipd_lifecycle._scope_match(path, pattern)
        duration = time.perf_counter() - start
        self.assertFalse(result)
        self.assertLess(
            duration,
            0.1,
            f"Pathological pattern took {duration:.4f}s; expected < 0.1s",
        )


class ScopeCallerFenceTests(unittest.TestCase):
    """Tests pinning the two key caller fences: work_cmd._in_scope and ipd_lifecycle._is_implicitly_allowed."""

    def test_in_scope_refuses_backlog_under_pending_scope(self) -> None:
        """cfab6d incident regression test: work_cmd._in_scope must refuse backlog item."""
        backlog_path = ".aw/records/backlog/open/20260924-cfab6d-incident.backlog.md"
        declared_scope = [".aw/records/plans/pending"]
        plan_rel = ".aw/records/plans/pending/20260924-scopeglob-01-8u6770-test.ipd.md"

        self.assertFalse(
            work_cmd._in_scope(backlog_path, declared_scope, plan_rel),
            "work_cmd._in_scope must not admit backlog files under pending plans scope",
        )

    def test_is_implicitly_allowed(self) -> None:
        """Implicit allowances must admit plan lifecycle artifacts and refuse non-lifecycle records."""
        plan_rel = ".aw/records/plans/pending/20260924-scopeglob-01-mxja4g-test.ipd.md"

        # MUST-ALLOW:
        self.assertTrue(
            ipd_lifecycle._is_implicitly_allowed(plan_rel, plan_rel),
            "Plan file itself must be implicitly allowed",
        )
        self.assertTrue(
            ipd_lifecycle._is_implicitly_allowed(
                ".aw/records/plans/INDEX.md", plan_rel
            ),
            "Plans INDEX.md must be implicitly allowed",
        )
        self.assertTrue(
            ipd_lifecycle._is_implicitly_allowed(
                ".aw/records/plans/executed/20260924-scopeglob-01-mxja4g-test.ipd.md",
                plan_rel,
            ),
            "Plan destination under executed/ must be implicitly allowed",
        )

        # MUST-REFUSE:
        self.assertFalse(
            ipd_lifecycle._is_implicitly_allowed(
                ".aw/records/backlog/open/item.backlog.md", plan_rel
            ),
            "Backlog files must not be implicitly allowed",
        )
        self.assertFalse(
            ipd_lifecycle._is_implicitly_allowed(
                ".aw/records/specs/implemented/spec.spec.md", plan_rel
            ),
            "Spec files must not be implicitly allowed",
        )
        self.assertFalse(
            ipd_lifecycle._is_implicitly_allowed(
                ".aw/records/research/20260901-report.md", plan_rel
            ),
            "Research files must not be implicitly allowed",
        )


class WorkCmdRefusalRemedyTests(unittest.TestCase):
    """Tests that work_cmd out-of-scope refusal provides the required remedy hint."""

    def test_out_of_scope_refusal_contains_remedy_hint(self) -> None:
        """The refusal message must name --no-plan and Scope-Paths as remedies."""
        plan_content = (
            "# IPD: Test\n"
            "- Scope-Paths: agent_workflows/ipd_lifecycle.py\n"
            "- Status: approved\n"
        )
        fake_plan_path = Path("/dummy/repo/.aw/records/plans/pending/test.ipd.md")
        with patch.object(Path, "read_text", return_value=plan_content), patch.object(
            work_cmd, "_resolve_repo_root", return_value=Path("/dummy/repo")
        ), patch.object(
            work_cmd, "_resolve_plan", return_value=(fake_plan_path, None)
        ), patch.object(work_cmd, "_staged_paths", return_value=[]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                ns = argparse.Namespace(
                    path_argv=[
                        "test",
                        "--",
                        ".aw/records/backlog/open/out_of_scope.backlog.md",
                    ],
                    trailers=[],
                )
                rc = work_cmd.run_commit(ns)
            output = buf.getvalue()

            self.assertEqual(rc, 1)
            self.assertIn(
                "aw commit: refusing - out-of-scope change(s) present:", output
            )
            self.assertIn("--no-plan", output)
            self.assertIn("Scope-Paths", output)

    def test_surviving_refusal_named_and_staged_arms(self) -> None:
        """IPD ygb3nk E-04: out-of-scope refusal survives for both named and staged paths.

        Reaches the real engine (check_type is NOT mocked). Asserts both arms:
          (a) out-of-scope path NAMED after `--` is refused with exit 1 and HEAD unchanged.
          (b) out-of-scope path merely STAGED, with only in-scope paths named, is refused
              with exit 1 and HEAD unchanged.
        """
        plan_text = (
            "# IPD: Demo work plan\n\n"
            "- Date: 2026-08-28\n"
            "- Kind: child\n"
            "- Concern: A real concern statement for review.\n"
            "- Scope: A real scope statement.\n"
            "- Scope-Paths: src/in_scope.py\n"
            "- Item-Dependencies: none\n"
            "- Status: approved\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Set: demo\n"
            "- Order: 1\n"
            "- Highest E allocated: 01\n"
            "- Author: tester\n"
            "- Id: dem001\n\n"
            "## Workflow history\n"
            "- 2026-08-28 approved (aw set): approved\n\n"
            "## Goal\n"
            "A real goal statement.\n\n"
            "## Detailed Implementation Checklist (TODO)\n\n"
            "### Task group 1: work\n"
            "- [ ] E-01 Do a real observable thing.\n"
            "  - Depends on: none\n"
            "  - Expected outcome: a real observable result.\n"
            "  - Execution state: pending\n\n"
            "## Validation and cross-check (verify before reporting done)\n"
            "- [ ] V-01 validates E-01\n"
            "  - Required evidence: a real falsifiable evidence statement.\n"
            "  - Observed evidence:\n"
            "  - Result: pending\n\n"
            "## Approval and execution gate\n"
            "- Size assessment: standard\n"
            "- Cohesion rationale: not required\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@e.com"], cwd=root, check=True
            )
            subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
            plans = root / ".aw" / "records" / "plans" / "pending"
            plans.mkdir(parents=True)
            plan_path = plans / "20260828-demo-01-dem001-test.ipd.md"
            plan_path.write_text(plan_text, encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "in_scope.py").write_text(
                "print('hello')\n", encoding="utf-8"
            )
            (root / "src" / "out_of_scope.py").write_text(
                "print('outside')\n", encoding="utf-8"
            )
            (root / ".gitignore").write_text(
                ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
            head_initial = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            # (a) Arm 1: out-of-scope path NAMED after `--` is refused
            (root / "src" / "out_of_scope.py").write_text(
                "print('modified outside')\n", encoding="utf-8"
            )
            buf_a = io.StringIO()
            with redirect_stdout(buf_a):
                ns_a = argparse.Namespace(
                    path_argv=[
                        "dem001",
                        "--dir",
                        str(root),
                        "-m",
                        "commit named out-of-scope",
                        "--",
                        "src/out_of_scope.py",
                    ],
                    trailers=[],
                )
                rc_a = work_cmd.run_commit(ns_a)
            out_a = buf_a.getvalue()
            head_a = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.assertEqual(rc_a, 1, f"Expected rc 1, got {rc_a}. Output:\n{out_a}")
            self.assertIn(
                "aw commit: refusing - out-of-scope change(s) present:", out_a
            )
            self.assertEqual(
                head_initial,
                head_a,
                "HEAD must be unchanged after named out-of-scope refusal",
            )

            # (b) Arm 2: out-of-scope path merely STAGED, with only in-scope paths named, is refused
            subprocess.run(["git", "add", "src/out_of_scope.py"], cwd=root, check=True)
            (root / "src" / "in_scope.py").write_text(
                "print('modified inside')\n", encoding="utf-8"
            )
            buf_b = io.StringIO()
            with redirect_stdout(buf_b):
                ns_b = argparse.Namespace(
                    path_argv=[
                        "dem001",
                        "--dir",
                        str(root),
                        "-m",
                        "commit in-scope while out-of-scope staged",
                        "--",
                        "src/in_scope.py",
                    ],
                    trailers=[],
                )
                rc_b = work_cmd.run_commit(ns_b)
            out_b = buf_b.getvalue()
            head_b = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.assertEqual(rc_b, 1, f"Expected rc 1, got {rc_b}. Output:\n{out_b}")
            self.assertIn(
                "aw commit: refusing - out-of-scope change(s) present:", out_b
            )
            self.assertEqual(
                head_initial,
                head_b,
                "HEAD must be unchanged after staged out-of-scope refusal",
            )
