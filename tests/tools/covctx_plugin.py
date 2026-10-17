"""Pytest plugin for per-test dynamic coverage context propagation.

Switches coverage context to item.nodeid and updates COVERAGE_PROCESS_CONFIG
so child subprocesses inherit the test node id as their static context.
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(
    item: pytest.Item, nextitem: pytest.Item | None
) -> Generator[None, None, None]:
    """Switch coverage context to item.nodeid during test execution."""
    cov = None
    try:
        import coverage

        cov = coverage.Coverage.current()
    except Exception:
        pass

    if cov is not None:
        try:
            cov.switch_context(item.nodeid)
        except Exception:
            pass

    orig_process_config = os.environ.get("COVERAGE_PROCESS_CONFIG")
    if orig_process_config is not None:
        try:
            from coverage.config import CoverageConfig

            cfg = CoverageConfig.deserialize(orig_process_config)
            cfg.context = item.nodeid
            os.environ["COVERAGE_PROCESS_CONFIG"] = cfg.serialize()
        except Exception:
            pass

    try:
        yield
    finally:
        if orig_process_config is not None:
            os.environ["COVERAGE_PROCESS_CONFIG"] = orig_process_config
        else:
            os.environ.pop("COVERAGE_PROCESS_CONFIG", None)

        if cov is not None:
            try:
                cov.switch_context("")
            except Exception:
                pass
