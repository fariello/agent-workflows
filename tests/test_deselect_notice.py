"""Tests for the tests.deselect_notice pytest plugin."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import runner_shared

_REPO_ROOT = str(Path(__file__).resolve().parent.parent)


class DeselectNoticePluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self._temp_dir.name)
        (self.temp_path / "pytest.ini").write_text(
            "[pytest]\nmarkers = slow\naddopts = -q -m 'not slow'\n",
            encoding="utf-8",
        )
        (self.temp_path / "test_sample.py").write_text(
            "import pytest\n"
            "def test_fast():\n"
            "    pass\n"
            "@pytest.mark.slow\n"
            "def test_heavy():\n"
            "    pass\n",
            encoding="utf-8",
        )
        self.env = dict(os.environ)
        pp = self.env.get("PYTHONPATH", "")
        self.env["PYTHONPATH"] = f"{_REPO_ROOT}{os.pathsep}{pp}".rstrip(os.pathsep)

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def _run_pytest(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.deselect_notice",
            *extra_args,
        ]
        return subprocess.run(
            cmd,
            cwd=self.temp_path,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_deselect_notice_with_xdist_workers(self) -> None:
        result = self._run_pytest("-n", "2")
        self.assertNotIn("INTERNALERROR", result.stdout)
        self.assertNotIn("INTERNALERROR", result.stderr)
        self.assertEqual(
            result.returncode, 0, f"pytest failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertIn("NOTE: 1 tests were deselected", result.stdout)
        summary = runner_shared.parse_suite_summary(result.stdout)
        self.assertTrue(
            summary.startswith("1 passed"), f"unexpected summary: {summary}"
        )

    def test_deselect_notice_with_no_xdist(self) -> None:
        result = self._run_pytest("-p", "no:xdist")
        self.assertNotIn("INTERNALERROR", result.stdout)
        self.assertNotIn("INTERNALERROR", result.stderr)
        self.assertEqual(
            result.returncode, 0, f"pytest failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertIn("NOTE: 1 tests were deselected", result.stdout)
        summary = runner_shared.parse_suite_summary(result.stdout)
        self.assertTrue(
            summary.startswith("1 passed"), f"unexpected summary: {summary}"
        )

    def test_deselect_notice_with_zero_workers(self) -> None:
        result = self._run_pytest("-n", "0")
        self.assertNotIn("INTERNALERROR", result.stdout)
        self.assertNotIn("INTERNALERROR", result.stderr)
        self.assertEqual(
            result.returncode, 0, f"pytest failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertIn("NOTE: 1 tests were deselected", result.stdout)
        summary = runner_shared.parse_suite_summary(result.stdout)
        self.assertTrue(
            summary.startswith("1 passed"), f"unexpected summary: {summary}"
        )

    def test_deselect_notice_absent_when_nothing_deselected(self) -> None:
        result = self._run_pytest("-m", "")
        self.assertNotIn("INTERNALERROR", result.stdout)
        self.assertNotIn("INTERNALERROR", result.stderr)
        self.assertEqual(
            result.returncode, 0, f"pytest failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertNotIn("NOTE: 1 tests were deselected", result.stdout)
        self.assertNotIn("tests were deselected", result.stdout)
        summary = runner_shared.parse_suite_summary(result.stdout)
        self.assertTrue(
            summary.startswith("2 passed"), f"unexpected summary: {summary}"
        )

    def test_three_categories_named_in_notice(self) -> None:
        """Assert notice derives and names all three categories in a three-marker configuration."""
        with tempfile.TemporaryDirectory() as td:
            fixture_path = Path(td)
            (fixture_path / "pytest.ini").write_text(
                "[pytest]\n"
                "markers =\n"
                "    slow\n"
                "    livecorpus\n"
                "    gpu\n"
                "addopts = -q -m 'not slow and not livecorpus and not gpu'\n",
                encoding="utf-8",
            )
            (fixture_path / "test_sample.py").write_text(
                "import pytest\n"
                "def test_normal():\n"
                "    pass\n"
                "@pytest.mark.slow\n"
                "def test_slow():\n"
                "    pass\n"
                "@pytest.mark.livecorpus\n"
                "def test_livecorpus():\n"
                "    pass\n"
                "@pytest.mark.gpu\n"
                "def test_gpu():\n"
                "    pass\n",
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "tests.deselect_notice",
            ]
            result = subprocess.run(
                cmd,
                cwd=fixture_path,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"pytest failed:\n{result.stdout}\n{result.stderr}",
            )
            self.assertIn("NOTE: 3 tests were deselected", result.stdout)
            self.assertIn("'slow'", result.stdout)
            self.assertIn("'livecorpus'", result.stdout)
            self.assertIn("'gpu'", result.stdout)
            self.assertIn("make test-all", result.stdout)

    def test_verbatim_fallback_for_unparsed_marker_expression(self) -> None:
        """Assert expressions the reader declines are printed verbatim in the notice."""
        result = self._run_pytest("-m", "not (slow or livecorpus)")
        self.assertEqual(
            result.returncode,
            0,
            f"pytest failed:\n{result.stdout}\n{result.stderr}",
        )
        self.assertIn("NOTE: 1 tests were deselected", result.stdout)
        self.assertIn("not (slow or livecorpus)", result.stdout)
        self.assertNotIn("make test-all", result.stdout)

    def test_no_marker_filter_with_keyword_deselection(self) -> None:
        """Assert runs with no marker filter attribute deselects to -k and omit make test-all."""
        result = self._run_pytest("-m", "", "-k", "not test_heavy")
        self.assertEqual(
            result.returncode,
            0,
            f"pytest failed:\n{result.stdout}\n{result.stderr}",
        )
        self.assertIn("NOTE: 1 tests were deselected", result.stdout)
        self.assertIn("no marker filter was active", result.stdout)
        self.assertNotIn("marker filter skips", result.stdout)
        self.assertNotIn("make test-all", result.stdout)

    def test_mixed_marker_and_keyword_deselection(self) -> None:
        """Assert mixed -m and -k deselects name marker categories and cite -k contribution."""
        (self.temp_path / "test_extra.py").write_text(
            "def test_extra():\n    pass\n",
            encoding="utf-8",
        )
        result = self._run_pytest("-k", "not test_extra")
        self.assertEqual(
            result.returncode,
            0,
            f"pytest failed:\n{result.stdout}\n{result.stderr}",
        )
        self.assertIn("NOTE: 2 tests were deselected", result.stdout)
        self.assertIn("'slow'", result.stdout)
        self.assertIn("-k/--deselect also contributed", result.stdout)
        self.assertIn("make test-all", result.stdout)

    def test_unconditional_print_regression_under_selected_marker(self) -> None:
        """Regression guard: notice must not claim 'slow' was skipped when -m slow selected it."""
        result = self._run_pytest("-m", "slow")
        self.assertEqual(
            result.returncode,
            0,
            f"pytest failed:\n{result.stdout}\n{result.stderr}",
        )
        self.assertIn("NOTE: 1 tests were deselected", result.stdout)
        self.assertNotIn("skips 'slow'", result.stdout)
        self.assertNotIn("the default run skips 'slow'", result.stdout)
        self.assertIn("filtered by marker expression: 'slow'", result.stdout)


if __name__ == "__main__":
    unittest.main()
