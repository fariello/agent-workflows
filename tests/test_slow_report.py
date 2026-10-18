"""Behavioral tests for the slow test report hook in conftest.py (IPD c8bfp9 E-09).

Asserts:
- An unlisted slow test exceeding the threshold is reported in the terminal summary warning and the run exits 0.
- A slow test listed in tests/slow_allowlist.txt is omitted from the warning and the run exits 0.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

import pytest

pytestmark = pytest.mark.core


_HOOK_CONFTEST = textwrap.dedent("""
    import os
    from pathlib import Path
    import pytest

    _CORE_TEST_DURATIONS = []

    @pytest.hookimpl
    def pytest_sessionstart(session):
        _CORE_TEST_DURATIONS.clear()

    @pytest.hookimpl
    def pytest_runtest_logreport(report):
        if report.when == "call" and hasattr(report, "duration") and hasattr(report, "nodeid"):
            _CORE_TEST_DURATIONS.append((report.duration, report.nodeid))

    def _load_slow_allowlist(rootpath: Path) -> dict[str, str]:
        allowlist_path = rootpath / "tests" / "slow_allowlist.txt"
        if not allowlist_path.exists():
            return {}
        allowed = {}
        for line in allowlist_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 1)
            node_id = parts[0].strip()
            reason = parts[1].strip() if len(parts) > 1 else ""
            allowed[node_id] = reason
        return allowed

    @pytest.hookimpl
    def pytest_terminal_summary(terminalreporter, exitstatus, config):
        if "PYTEST_XDIST_WORKER" in os.environ:
            return

        threshold_env = os.environ.get("AW_SLOW_REPORT_SECONDS")
        try:
            threshold = float(threshold_env) if threshold_env else 2.0
        except ValueError:
            threshold = 2.0

        rootpath = getattr(config, "rootpath", Path(config.rootdir))
        allowlist = _load_slow_allowlist(rootpath)

        unlisted = []
        for dur, nodeid in _CORE_TEST_DURATIONS:
            if dur > threshold and nodeid not in allowlist:
                unlisted.append((dur, nodeid))

        unlisted.sort(key=lambda x: x[0], reverse=True)

        terminalreporter.section("SLOW TESTS REPORT", yellow=True)
        if unlisted:
            terminalreporter.write_line(
                f"WARNING: {len(unlisted)} test(s) exceeded {threshold:g}s and are not listed in tests/slow_allowlist.txt:"
            )
            for dur, nodeid in unlisted:
                terminalreporter.write_line(f"  {dur:6.2f}s  {nodeid}")
        else:
            terminalreporter.write_line(
                f"0 unlisted slow tests (all tests > {threshold:g}s are documented in tests/slow_allowlist.txt)."
            )
""")


_SLOW_TEST_CODE = textwrap.dedent("""
    import time

    def test_slow_sample():
        time.sleep(0.3)
        assert True

    def test_fast_sample():
        assert True
""")


class SlowReportBehaviorTests(unittest.TestCase):
    """Behavioral tests for the slow test terminal summary hook."""

    def test_unlisted_slow_test_is_named_in_warning_and_exits_zero(self) -> None:
        """A test exceeding the threshold without an allowlist entry is named in the warning."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "conftest.py").write_text(_HOOK_CONFTEST, encoding="utf-8")
            tests_dir = root / "tests"
            tests_dir.mkdir(parents=True)
            (tests_dir / "test_sample.py").write_text(_SLOW_TEST_CODE, encoding="utf-8")
            (tests_dir / "slow_allowlist.txt").write_text(
                "# Header comment\\n", encoding="utf-8"
            )

            env = dict(os.environ)
            env.pop("PYTEST_XDIST_WORKER", None)
            env["AW_SLOW_REPORT_SECONDS"] = "0.2"
            env.pop("PYTEST_ADDOPTS", None)

            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--rootdir",
                    str(root),
                    "-o",
                    "addopts=",
                    "tests/test_sample.py",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                res.returncode,
                0,
                f"pytest failed with rc={res.returncode}:\\n{res.stdout}\\n{res.stderr}",
            )
            combined = res.stdout + res.stderr
            self.assertIn("SLOW TESTS REPORT", combined)
            self.assertIn(
                "WARNING: 1 test(s) exceeded 0.2s and are not listed in tests/slow_allowlist.txt:",
                combined,
            )
            self.assertIn("tests/test_sample.py::test_slow_sample", combined)
            self.assertNotIn("tests/test_sample.py::test_fast_sample", combined)

    def test_listed_slow_test_is_omitted_from_warning_and_exits_zero(self) -> None:
        """A test exceeding the threshold that is listed in slow_allowlist.txt is omitted."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "conftest.py").write_text(_HOOK_CONFTEST, encoding="utf-8")
            tests_dir = root / "tests"
            tests_dir.mkdir(parents=True)
            (tests_dir / "test_sample.py").write_text(_SLOW_TEST_CODE, encoding="utf-8")
            slow_nodeid = "tests/test_sample.py::test_slow_sample"
            (tests_dir / "slow_allowlist.txt").write_text(
                f"# Header comment\n{slow_nodeid}\tPermitted slow test for testing\n",
                encoding="utf-8",
            )

            env = dict(os.environ)
            env.pop("PYTEST_XDIST_WORKER", None)
            env["AW_SLOW_REPORT_SECONDS"] = "0.2"
            env.pop("PYTEST_ADDOPTS", None)

            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--rootdir",
                    str(root),
                    "-o",
                    "addopts=",
                    "tests/test_sample.py",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                res.returncode,
                0,
                f"pytest failed with rc={res.returncode}:\\n{res.stdout}\\n{res.stderr}",
            )
            combined = res.stdout + res.stderr
            self.assertIn("SLOW TESTS REPORT", combined)
            self.assertIn("0 unlisted slow tests", combined)
            self.assertNotIn("WARNING: 1 test(s) exceeded", combined)
            self.assertNotIn(f"  {slow_nodeid}", combined)


if __name__ == "__main__":
    unittest.main()
