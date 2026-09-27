"""Tests for the tests.deselect_notice pytest plugin."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
