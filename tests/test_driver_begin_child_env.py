"""Behavioral tests for driver_begin child environment pin and baseline overlay.

Restored by backlog o0gy5v / plan lyqn1t (site S-26 in yuhl6o).
Guards the tool-identity pin and baseline overlay handed to the `aw ipd begin` child
process by `runner_shared.driver_begin` across both host drivers (oc_runipd, agy_runipd).
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence
import unittest.mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared


class _LaunchSpy:
    """Stands in for subprocess.run, recording argv, kwargs, and call count."""

    def __init__(self) -> None:
        self.calls = 0
        self.argv: list[str] | None = None
        self.kwargs: dict[str, Any] = {}

    def __call__(
        self, argv: Sequence[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        self.calls += 1
        self.argv = list(argv)
        self.kwargs = kwargs
        return subprocess.CompletedProcess(list(argv), 0, stdout="", stderr="")

    @property
    def env(self) -> dict[str, str]:
        return self.kwargs.get("env") or {}


def _clean_environ() -> dict[str, str]:
    """Return os.environ with pin-inherited keys removed."""
    return {
        k: v
        for k, v in os.environ.items()
        if k not in ("AW_PIN_KEEP_ROOT", "PYTHONPATH", "AW_ISOLATED_BASELINE")
    }


@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("host_module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
def test_driver_begin_child_env_pin(host_module: Any, isolated: bool) -> None:
    """Assert child process receives runner tool-identity pin and DEVNULL stdin."""
    spy = _LaunchSpy()
    prefix = runner_shared.pinned_module_argv([])
    expected_root = runner_shared.runner_package_root()

    with (
        unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
        unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
    ):
        rc, _stderr = host_module.driver_begin(
            Path("/nonexistent"), "aaa111", "actor", isolated=isolated
        )

    assert rc == 0
    assert spy.calls == 1
    assert spy.env["AW_PIN_KEEP_ROOT"] == expected_root
    assert expected_root in spy.env["PYTHONPATH"].split(os.pathsep)
    assert spy.argv is not None
    assert spy.argv[: len(prefix)] == prefix
    assert spy.argv[len(prefix) :] == [
        "ipd",
        "begin",
        "aaa111",
        "--actor",
        "actor",
        "--dir",
        str(Path("/nonexistent")),
    ]
    assert spy.kwargs["stdin"] is subprocess.DEVNULL
    assert spy.kwargs["cwd"] == str(Path("/nonexistent"))


@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("host_module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
def test_driver_begin_baseline_overlay(host_module: Any, isolated: bool) -> None:
    """Assert AW_ISOLATED_BASELINE is overlayed exactly when isolated=True."""
    spy = _LaunchSpy()
    with (
        unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
        unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
    ):
        rc, _stderr = host_module.driver_begin(
            Path("/nonexistent"), "aaa111", "actor", isolated=isolated
        )

    assert rc == 0
    assert spy.calls == 1
    if isolated:
        assert spy.env.get("AW_ISOLATED_BASELINE") == "1"
    else:
        assert "AW_ISOLATED_BASELINE" not in spy.env


@pytest.mark.parametrize("host_module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
def test_driver_begin_run_id_propagation(host_module: Any) -> None:
    """Assert run_id is propagated via --run-id flag on both hosts."""
    spy_with = _LaunchSpy()
    with (
        unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
        unittest.mock.patch.object(runner_shared.subprocess, "run", spy_with),
    ):
        rc, _ = host_module.driver_begin(
            Path("/nonexistent"), "aaa111", "actor", run_id="run-x"
        )
    assert rc == 0
    assert spy_with.calls == 1
    assert spy_with.argv is not None
    assert spy_with.argv[-2:] == ["--run-id", "run-x"]

    spy_without = _LaunchSpy()
    with (
        unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
        unittest.mock.patch.object(runner_shared.subprocess, "run", spy_without),
    ):
        rc, _ = host_module.driver_begin(
            Path("/nonexistent"), "aaa111", "actor", run_id=None
        )
    assert rc == 0
    assert spy_without.calls == 1
    assert spy_without.argv is not None
    assert "--run-id" not in spy_without.argv


def test_unpinned_builder_fails_pin_assertions() -> None:
    """Assert an unpinned builder measurably fails pin assertions through the launcher."""
    spy = _LaunchSpy()
    prefix = runner_shared.pinned_module_argv([])
    expected_root = runner_shared.runner_package_root()

    with (
        unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
        unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
    ):
        runner_shared.driver_begin(
            Path("/nonexistent"),
            "aaa111",
            "actor",
            env_builder=lambda: dict(os.environ),
            argv_builder=lambda args: [sys.executable, "-m", "agent_workflows", *args],
        )

    assert spy.calls == 1
    assert "AW_PIN_KEEP_ROOT" not in spy.env
    assert expected_root not in spy.env.get("PYTHONPATH", "").split(os.pathsep)
    assert spy.argv is not None
    assert spy.argv[: len(prefix)] != prefix
