"""Subprocess equivalence and rewritten-suite tests for ``tools/fixture_codemod.py`` (IPD ``j2xjtt`` E-09).

Moved out of ``tests/test_fixture_codemod.py`` per E-09's 10-second serial wall-time
bound because combined execution of cases (a)-(c), (e)-(f), (g), and (h) under
``-n 0`` exceeded 10 s (measured 10.68 s).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from tests import support
from tests.test_fixture_codemod import _run_codemod, _stage_fixture_in_temp_repo

pytestmark = pytest.mark.slow


class FixtureCodemodEquivalenceTests(unittest.TestCase):
    """E-09: cases (g) not-equivalent isolation and (h) rewritten module tests pass."""

    def test_case_g_not_equivalent_site_is_isolated_and_reverted_while_others_stay(
        self,
    ) -> None:
        """Case (g): bisection reverts the not-equivalent site and keeps other rewrites."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td), "not_equivalent.py.txt", "test_not_equivalent_fixture.py"
            )
            rel_target = target.relative_to(repo).as_posix()

            proc, report = _run_codemod(repo, "--apply", "--format", "json", rel_target)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")
            self.assertIsNotNone(report)
            assert report is not None
            self.assertEqual(report["totals"]["sites"], 3)
            self.assertEqual(report["totals"]["rewrites"], 2)
            self.assertEqual(report["totals"]["refusals"], 1)
            self.assertEqual(report["totals"]["by_reason"]["not-equivalent"], 1)
            self.assertEqual(report["totals"]["by_disposition"]["hand"], 1)
            self.assertEqual(report["totals"]["by_disposition"]["legacy-kept"], 0)

            mod = report["modules"][0]
            self.assertTrue(mod["changed"])
            self.assertTrue(mod["proof"]["equivalent"])
            self.assertIsNotNone(mod["proof"]["before_hash"])
            self.assertEqual(mod["proof"]["before_hash"], mod["proof"]["after_hash"])
            self.assertGreaterEqual(mod["proof"]["pytest_runs"], 3)

            actions = [
                (s["action"], s["reason"], s["record_type"]) for s in mod["sites"]
            ]
            self.assertEqual(
                actions,
                [
                    ("rewrite", None, "ipd"),
                    ("refuse", "not-equivalent", "spec"),
                    ("rewrite", None, "release"),
                ],
            )
            self.assertEqual(mod["sites"][1]["disposition"], "hand")

            rewritten = target.read_text(encoding="utf-8")
            self.assertIn("from tests.record_builder import RecordBuilder\n", rewritten)
            self.assertIn("RecordBuilder().plan(", rewritten)
            self.assertIn("RecordBuilder().release(", rewritten)
            self.assertIn('"# Spec: Layout Sensitive\\n"', rewritten)
            self.assertIn('"- Id: sp7002\\n"', rewritten)
            self.assertIn('"- Status: draft\\n"', rewritten)
            self.assertNotIn("RecordBuilder().spec(", rewritten)

    def test_case_h_rewritten_fixture_module_tests_pass(self) -> None:
        """Case (h): the rewritten fixture module's own pytest suite passes."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td),
                "rewritten_module_passes.py.txt",
                "test_rewritten_passes_fixture.py",
            )
            rel_target = target.relative_to(repo).as_posix()

            proc, report = _run_codemod(repo, "--apply", "--format", "json", rel_target)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")
            assert report is not None
            self.assertEqual(report["totals"]["sites"], 3)
            self.assertEqual(report["totals"]["rewrites"], 3)
            self.assertEqual(report["totals"]["standard_rewrites"], 2)
            self.assertEqual(report["totals"]["invalid_input_rewrites"], 1)
            self.assertEqual(report["totals"]["refusals"], 0)
            self.assertTrue(report["modules"][0]["changed"])
            self.assertTrue(report["modules"][0]["proof"]["equivalent"])

            rewritten = target.read_text(encoding="utf-8")
            self.assertIn("RecordBuilder().plan(", rewritten)
            self.assertIn("RecordBuilder().spec(", rewritten)
            self.assertIn("raw_fields={'Status': 'EXECUTED'}", rewritten)

            pytest_proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-o",
                    "addopts=",
                    "-m",
                    "",
                    "-p",
                    "no:randomly",
                    "-n",
                    "0",
                    "-v",
                    str(target.resolve()),
                ],
                cwd=str(support.REPO_ROOT),
                env=support.pinned_env(),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                check=False,
            )
            self.assertEqual(
                pytest_proc.returncode,
                0,
                f"stdout:\n{pytest_proc.stdout}\nstderr:\n{pytest_proc.stderr}",
            )
            self.assertIn("test_rewritten_plain_plan PASSED", pytest_proc.stdout)
            self.assertIn("test_rewritten_fstring_spec PASSED", pytest_proc.stdout)
            self.assertIn(
                "test_rewritten_invalid_input_spec PASSED", pytest_proc.stdout
            )
            self.assertIn("3 passed", pytest_proc.stdout)


if __name__ == "__main__":
    unittest.main()
