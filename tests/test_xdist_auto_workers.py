"""Behavioral outcome tests for pytest-xdist auto worker count bounding in conftest.

Tests observable behavior and outcomes: verifies that the pytest_xdist_auto_num_workers
hook caps -n auto at half of available CPUs (minimum 1) and honors explicit environment
overrides.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import conftest


def test_auto_num_workers_defaults_to_half_cpus() -> None:
    """When -n auto is used, worker count is bounded to half of available CPUs."""
    config = MagicMock()
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("PYTEST_XDIST_AUTO_NUM_WORKERS", None)
        with patch.object(conftest, "_available_cpus", return_value=12):
            assert conftest.pytest_xdist_auto_num_workers(config) == 6


def test_auto_num_workers_scaling_and_floors() -> None:
    """Verify worker counts across various CPU counts, ensuring floor of 1."""
    config = MagicMock()
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("PYTEST_XDIST_AUTO_NUM_WORKERS", None)
        cases = [
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 2),
            (8, 4),
            (12, 6),
            (16, 8),
            (32, 16),
            (64, 32),
        ]
        for cpus, expected_workers in cases:
            with patch.object(conftest, "_available_cpus", return_value=cpus):
                actual = conftest.pytest_xdist_auto_num_workers(config)
                assert (
                    actual == expected_workers
                ), f"For {cpus} CPUs, expected {expected_workers} workers, got {actual}"


def test_auto_num_workers_honors_env_override() -> None:
    """PYTEST_XDIST_AUTO_NUM_WORKERS explicitly overrides the auto calculation."""
    config = MagicMock()
    with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "3"}):
        with patch.object(conftest, "_available_cpus", return_value=12):
            assert conftest.pytest_xdist_auto_num_workers(config) == 3


def test_auto_num_workers_env_override_floors_at_one() -> None:
    """PYTEST_XDIST_AUTO_NUM_WORKERS <= 0 is floored at 1."""
    config = MagicMock()
    with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "0"}):
        with patch.object(conftest, "_available_cpus", return_value=12):
            assert conftest.pytest_xdist_auto_num_workers(config) == 1


def test_auto_num_workers_invalid_env_falls_back_to_half_cpus() -> None:
    """Invalid non-integer in PYTEST_XDIST_AUTO_NUM_WORKERS falls back gracefully."""
    config = MagicMock()
    with patch.dict(os.environ, {"PYTEST_XDIST_AUTO_NUM_WORKERS": "not-a-number"}):
        with patch.object(conftest, "_available_cpus", return_value=12):
            assert conftest.pytest_xdist_auto_num_workers(config) == 6


def test_available_cpus_returns_positive_integer() -> None:
    """_available_cpus returns a sensible positive CPU count on the running system."""
    cpus = conftest._available_cpus()
    assert isinstance(cpus, int)
    assert cpus >= 1
