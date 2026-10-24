"""Behavioral outcome tests for pytest-xdist auto worker count bounding in conftest.

Tests observable behavior and outcomes: verifies that the pytest_xdist_auto_num_workers
hook caps -n auto at half of available CPUs (minimum 1, maximum 6), honors explicit environment
overrides, and stays optional under -p no:xdist (backlog 6ljil4).
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import types
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.core

conftest: Any = None


def _load_conftest() -> types.ModuleType:
    """Load or retrieve the root conftest module with contained environment side effects."""
    if "conftest" in sys.modules:
        return sys.modules["conftest"]
    if importlib.util.find_spec("xdist") is None:
        raise unittest.SkipTest(
            "xdist is not installed; skipping conftest-dependent tests under unittest"
        )
    env_snapshot = dict(os.environ)
    try:
        import conftest as _conftest

        return _conftest
    finally:
        os.environ.clear()
        os.environ.update(env_snapshot)


class XdistAutoWorkersTests(unittest.TestCase):
    conftest: types.ModuleType | None = None

    @classmethod
    def setUpClass(cls) -> None:
        global conftest
        conftest = _load_conftest()
        cls.conftest = conftest

    def _run_pytest_without_xdist(self) -> subprocess.CompletedProcess[str]:
        """Run pytest with -p no:xdist while scrubbing ambient pytest env vars."""
        env = dict(os.environ)
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-o",
            "addopts=",
            "-p",
            "no:xdist",
            "tests/test_xdist_auto_workers.py",
            "-k",
            "test_available_cpus_returns_positive_integer",
        ]
        repo_root = os.path.dirname(os.path.abspath(conftest.__file__))
        return subprocess.run(
            cmd,
            env=env,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

    def test_auto_num_workers_defaults_to_half_cpus(self) -> None:
        """On 12 available CPUs, the default uses six workers."""
        config = MagicMock()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PYTEST_XDIST_AUTO_NUM_WORKERS", None)
            os.environ.pop("GITHUB_ACTIONS", None)
            os.environ.pop("CI", None)
            with patch.object(conftest, "_available_cpus", return_value=12):
                self.assertEqual(conftest.pytest_xdist_auto_num_workers(config), 6)

    def test_auto_num_workers_scaling_and_floors(self) -> None:
        """Verify worker counts: cpus if <= 4, otherwise max(4, cpus // 2)."""
        config = MagicMock()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PYTEST_XDIST_AUTO_NUM_WORKERS", None)
            os.environ.pop("GITHUB_ACTIONS", None)
            os.environ.pop("CI", None)
            cases = [
                (1, 1),
                (2, 2),
                (3, 3),
                (4, 4),
                (5, 4),
                (6, 4),
                (8, 4),
                (10, 5),
                (12, 6),
                (16, 8),
                (32, 16),
                (64, 32),
            ]
            for cpus, expected_workers in cases:
                with patch.object(conftest, "_available_cpus", return_value=cpus):
                    actual = conftest.pytest_xdist_auto_num_workers(config)
                    self.assertEqual(
                        actual,
                        expected_workers,
                        f"For {cpus} CPUs, expected {expected_workers} workers, got {actual}",
                    )

    def test_auto_num_workers_ci_mode(self) -> None:
        """CI uses the same policy: cpus if <= 4, otherwise max(4, cpus // 2)."""
        config = MagicMock()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PYTEST_XDIST_AUTO_NUM_WORKERS", None)
            cases = [
                (1, 1),
                (2, 2),
                (3, 3),
                (4, 4),
                (6, 4),
                (8, 4),
                (12, 6),
                (16, 8),
            ]
            for cpus, expected_workers in cases:
                with patch.object(conftest, "_available_cpus", return_value=cpus):
                    actual = conftest.pytest_xdist_auto_num_workers(config)
                    self.assertEqual(
                        actual,
                        expected_workers,
                        f"For {cpus} CPUs in CI, expected {expected_workers} workers, got {actual}",
                    )

    def test_auto_num_workers_honors_env_override(self) -> None:
        """PYTEST_XDIST_AUTO_NUM_WORKERS explicitly overrides the auto calculation."""
        config = MagicMock()
        with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "3"}):
            with patch.object(conftest, "_available_cpus", return_value=12):
                self.assertEqual(conftest.pytest_xdist_auto_num_workers(config), 3)

    def test_auto_num_workers_env_override_unbounded(self) -> None:
        """PYTEST_XDIST_AUTO_NUM_WORKERS explicitly overrides auto calculation above cpu count."""
        config = MagicMock()
        with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "12"}):
            with patch.object(conftest, "_available_cpus", return_value=4):
                self.assertEqual(conftest.pytest_xdist_auto_num_workers(config), 12)

    def test_auto_num_workers_env_override_floors_at_one(self) -> None:
        """PYTEST_XDIST_AUTO_NUM_WORKERS <= 0 is floored at 1."""
        config = MagicMock()
        with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "0"}):
            with patch.object(conftest, "_available_cpus", return_value=12):
                self.assertEqual(conftest.pytest_xdist_auto_num_workers(config), 1)

    def test_auto_num_workers_invalid_env_falls_back_to_local_policy(self) -> None:
        """Invalid non-integer in PYTEST_XDIST_AUTO_NUM_WORKERS falls back gracefully."""
        config = MagicMock()
        with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "not-a-number"}):
            os.environ.pop("GITHUB_ACTIONS", None)
            os.environ.pop("CI", None)
            with patch.object(conftest, "_available_cpus", return_value=12):
                self.assertEqual(conftest.pytest_xdist_auto_num_workers(config), 6)

    def test_available_cpus_returns_positive_integer(self) -> None:
        """_available_cpus returns a sensible positive CPU count on the running system."""
        cpus = conftest._available_cpus()
        self.assertIsInstance(cpus, int)
        self.assertGreaterEqual(cpus, 1)

    def test_pytest_runs_without_xdist_plugin(self) -> None:
        """When xdist is disabled (-p no:xdist), pytest runs without PluginValidationError."""
        res = self._run_pytest_without_xdist()
        self.assertEqual(
            res.returncode,
            0,
            f"pytest failed with output:\n{res.stdout}\n{res.stderr}",
        )
        self.assertNotIn("PluginValidationError", res.stderr)

    def test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags(
        self,
    ) -> None:
        """Ambient PYTEST_ADDOPTS with xdist flags does not leak into scrubbed subprocess."""
        with patch.dict(os.environ, {"PYTEST_ADDOPTS": "-n 2 --dist=worksteal"}):
            res = self._run_pytest_without_xdist()
        self.assertEqual(
            res.returncode,
            0,
            f"pytest failed with output:\n{res.stdout}\n{res.stderr}",
        )
        self.assertNotIn("PluginValidationError", res.stderr)
        self.assertNotIn("unrecognized arguments", res.stderr)
        self.assertNotIn("unrecognized arguments", res.stdout)

    def test_conftest_registers_on_pluginmanager_without_xdist_hookspecs(
        self,
    ) -> None:
        """In-process test that conftest registers and validates without xdist hookspecs."""
        pm = pytest.PytestPluginManager()
        self.assertFalse(pm.hasplugin("xdist"))
        pm.register(conftest)
        pm.check_pending()
