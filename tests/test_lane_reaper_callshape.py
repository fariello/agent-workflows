"""Behavioral call-shape guards for bound_expiry_reaper's injected reaper.

Backlog g321ny reported two static type errors, and both shipped before this plan executed:
- Item 2: The `Callable[[Any, Path], Any]` annotation in `agent_workflows/lane_containment.py`
  became the `_ReapCallable` Protocol in plan `2o9osz` at commit `d0d0c9e4` (authored from
  backlog item `jt01do`, now done), and `lane_containment.py` consequently type-checks clean.
- Item 1: The `.strip()`-on-a-tuple defect in `agent_workflows/runner_shared.py` and the
  "behavioral decision" the item reserved were settled by executed plan `87jnym` (E-01
  unpacked the tuple and chose fail-safe on `rc != 0`; E-07 added the moved-HEAD arm). The
  guard is `tests/test_interrupt_reconcile.py::InterruptReconcileNoWorktreeUnitTests::test_no_worktree_committed_work_preserves_work`,
  verified at review by deleting the moved-HEAD arm and observing that test go red.

These tests call `bound_expiry_reaper` with an injected reaper and with its default,
then assert the observed cleanup behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from agent_workflows import lane_containment, runner_shutdown


def test_injected_reaper_invoked_by_keyword(tmp_path: Path) -> None:
    """Pin the injected-reaper calling convention by behavior (E-01).

    The spy accepts (process, *, run_dir) keyword-only, asserting that the product
    call binds run_dir as a keyword argument and invokes the spy exactly once.
    """
    process_sentinel = object()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    item: dict[str, Any] = {"id6": "yifr0h"}

    calls: list[dict[str, Any]] = []

    def keyword_only_spy(process: Any, *, run_dir: Path) -> None:
        calls.append({"process": process, "run_dir": run_dir})

    expire = lane_containment.bound_expiry_reaper(
        process_sentinel,
        run_dir,
        item,
        reap=keyword_only_spy,
    )
    expire("max-turn", 1.0)

    assert len(calls) == 1
    assert calls[0]["process"] is process_sentinel
    assert calls[0]["run_dir"] == run_dir


def test_positional_only_reaper_raises_type_error(tmp_path: Path) -> None:
    """Assert a positional-only reaper raises TypeError on product call (E-01 negative).

    Because `_expire` invokes `reaper(process, run_dir=run_dir)` outside the
    `contextlib.suppress(Exception)` block, a reaper that refuses keyword binding
    for `run_dir` raises TypeError.
    """
    process_sentinel = object()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    item: dict[str, Any] = {"id6": "yifr0h"}

    def pos_only_spy(process: Any, run_dir: Path, /) -> None:
        pass

    expire = lane_containment.bound_expiry_reaper(
        process_sentinel,
        run_dir,
        item,
        reap=pos_only_spy,  # type: ignore[arg-type]
    )
    with pytest.raises(TypeError, match="positional-only"):
        expire("max-turn", 1.0)


def test_omitted_reap_defaults_to_clean_shutdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert an omitted reap defaults to runner_shutdown.clean_shutdown (E-02).

    Spec c4gd2h R5 mandates a single shared cleanup implementation across all levels.
    bound_expiry_reaper imports runner_shutdown inside its body and reads
    runner_shutdown.clean_shutdown at call time, so patching the module attribute
    proves the default reaper reaches clean_shutdown.
    """
    process_sentinel = object()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    item: dict[str, Any] = {"id6": "yifr0h"}

    mock_shutdown = MagicMock()
    monkeypatch.setattr(runner_shutdown, "clean_shutdown", mock_shutdown)

    expire = lane_containment.bound_expiry_reaper(
        process_sentinel,
        run_dir,
        item,
        reap=None,
    )
    expire("max-turn", 1.0)

    mock_shutdown.assert_called_once_with(process_sentinel, run_dir=run_dir)
