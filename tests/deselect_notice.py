"""Pytest plugin to report count of deselected tests in the terminal summary."""

from __future__ import annotations

from typing import Any

_deselected_count = 0
_worker_counts: list[int] = []


def pytest_configure(config: Any) -> None:
    global _deselected_count, _worker_counts
    _deselected_count = 0
    _worker_counts = []

    if config.pluginmanager.hasplugin("xdist"):

        class _XdistNoticeHooks:
            def pytest_testnodedown(self, node: Any, error: Any) -> None:
                worker_output = getattr(node, "workeroutput", {})
                if worker_output and "deselected_count" in worker_output:
                    _worker_counts.append(worker_output["deselected_count"])

        config.pluginmanager.register(
            _XdistNoticeHooks(), name="tests_deselect_notice_xdist"
        )


def pytest_deselected(items: Any) -> None:
    global _deselected_count
    _deselected_count += len(items)


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    config = getattr(session, "config", None)
    if config and hasattr(config, "workeroutput"):
        config.workeroutput["deselected_count"] = _deselected_count


def pytest_terminal_summary(
    terminalreporter: Any, exitstatus: Any, config: Any
) -> None:
    worker_max = max(_worker_counts) if _worker_counts else 0
    total_deselected = max(worker_max, _deselected_count)
    if total_deselected > 0:
        terminalreporter.write_line(
            f"NOTE: {total_deselected} tests were deselected by -m/-k and did not "
            "run (the default run skips 'slow' and 'livecorpus'); run everything with: "
            "make test-all"
        )
