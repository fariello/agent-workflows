"""Tests for backlog-close host label parameterization across runner hosts.

Validates that runner_shared.process_backlog_close requires host_label (no default)
and that each host runner (oc_runipd, agy_runipd) binds its own HostLabels.command,
stopping agy runs from falsely attributing backlog closes to aw oc run.
"""

from __future__ import annotations

import contextlib
import inspect
import io
from pathlib import Path
from typing import Any
from unittest import mock


from agent_workflows import agy_runipd, oc_runipd, runner_shared


def _setup_backlog_and_plan_fixture(
    root: Path,
    *,
    backlog_id6: str = "tst001",
    plan_id6: str = "pln999",
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Build a minimal repository structure with an open backlog item and executed carrier.

    Returns (run_dir, state, item) ready for process_backlog_close.
    """
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    backlog_dir = repo / ".aw" / "records" / "backlog" / "open"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    item_file = backlog_dir / f"20260929-test-01-{backlog_id6}-item.backlog.md"
    item_file.write_text(
        f"- Id: {backlog_id6}\n- Status: open\n- Set: test\n- Summary: Test\n",
        encoding="utf-8",
    )

    plans_dir = repo / ".aw" / "records" / "plans" / "executed"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plans_dir / f"20260929-test-01-{plan_id6}-plan.ipd.md"
    plan_file.write_text(
        f"- Id: {plan_id6}\n- From-Backlog: {backlog_id6}\n- Status: executed\n",
        encoding="utf-8",
    )

    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Note: item["last_plan_path"] must be absolute to satisfy collect_earned_paths (PR-001/F-12),
    # and item must be placed in state["queue"] so run_earned_paths discovers it.
    item = {
        "id6": plan_id6,
        "from_backlog": backlog_id6,
        "last_plan_path": str(plan_file.resolve()),
    }
    state = {
        "repo": repo,
        "run_id": "run-test-001",
        "queue": [item],
    }
    return run_dir, state, item


def test_shared_process_backlog_close_host_label_has_no_default() -> None:
    """The shared function host_label parameter must be KEYWORD_ONLY with NO DEFAULT."""
    sig = inspect.signature(runner_shared.process_backlog_close)
    assert (
        "host_label" in sig.parameters
    ), "host_label parameter must exist in runner_shared.process_backlog_close"
    param = sig.parameters["host_label"]
    assert (
        param.kind == inspect.Parameter.KEYWORD_ONLY
    ), f"host_label parameter kind must be KEYWORD_ONLY, got {param.kind}"
    assert (
        param.default is inspect.Parameter.empty
    ), f"host_label parameter must have NO DEFAULT, got {param.default!r}"


def test_oc_host_binds_oc_label_and_preserves_message_format(tmp_path: Path) -> None:
    """The oc_runipd runner passes 'aw oc run' and preserves the canonical close message format."""
    run_dir, state, item = _setup_backlog_and_plan_fixture(tmp_path)

    close_messages: list[str] = []
    commit_messages: list[str] = []

    def fake_close(
        repo: Path, item_path: Path, item_id6: str, evidence: str, message: str
    ) -> tuple[int, str]:
        close_messages.append(message)
        return (0, "ok")

    def fake_commit(repo: Path, item_id6: str, message: str, **kwargs: Any) -> str:
        commit_messages.append(message)
        return "mock-commit-sha-oc"

    with mock.patch.object(
        oc_runipd, "close_backlog_item", fake_close
    ), mock.patch.object(
        oc_runipd, "commit_backlog_close", fake_commit
    ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        oc_runipd.process_backlog_close(run_dir, state, item)

    # PR-001 / F-12: The earned-gate guard must pass.
    assert (
        item.get("backlog_close", {}).get("closed") is True
    ), f"Close was not earned or failed: {item.get('backlog_close')}"
    assert len(close_messages) == 1
    assert len(commit_messages) == 1
    assert close_messages[0] == commit_messages[0]

    msg = close_messages[0]
    assert msg.startswith(
        "closed by aw oc run:"
    ), f"Expected msg to start with 'closed by aw oc run:', got: {msg}"
    assert "IPD pln999 executed" in msg
    # Verify remainder format: ({verdict.reason}); evidence {verdict.evidence}
    reason = item["backlog_close"]["reason"]
    evidence = item["backlog_close"]["evidence"]
    expected_msg = (
        f"closed by aw oc run: IPD pln999 executed ({reason}); evidence {evidence}"
    )
    assert (
        msg == expected_msg
    ), f"OC message format drifted: {msg!r} != {expected_msg!r}"


def test_agy_host_binds_agy_label(tmp_path: Path) -> None:
    """The agy_runipd runner passes 'aw agy run' into process_backlog_close."""
    run_dir, state, item = _setup_backlog_and_plan_fixture(tmp_path)

    close_messages: list[str] = []
    commit_messages: list[str] = []

    def fake_close(
        repo: Path, item_path: Path, item_id6: str, evidence: str, message: str
    ) -> tuple[int, str]:
        close_messages.append(message)
        return (0, "ok")

    def fake_commit(repo: Path, item_id6: str, message: str, **kwargs: Any) -> str:
        commit_messages.append(message)
        return "mock-commit-sha-agy"

    with mock.patch.object(
        agy_runipd, "close_backlog_item", fake_close
    ), mock.patch.object(
        agy_runipd, "commit_backlog_close", fake_commit
    ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        agy_runipd.process_backlog_close(run_dir, state, item)

    # PR-001 / F-12: The earned-gate guard must pass.
    assert (
        item.get("backlog_close", {}).get("closed") is True
    ), f"Close was not earned or failed: {item.get('backlog_close')}"
    assert len(close_messages) == 1
    assert len(commit_messages) == 1
    assert close_messages[0] == commit_messages[0]

    msg = close_messages[0]
    assert msg.startswith(
        "closed by aw agy run:"
    ), f"Expected msg to start with 'closed by aw agy run:', got: {msg}"
    assert "IPD pln999 executed" in msg


def test_host_messages_differ_between_oc_and_agy(tmp_path: Path) -> None:
    """Messages built by oc and agy runs differ in their host label."""
    run_dir_oc, state_oc, item_oc = _setup_backlog_and_plan_fixture(tmp_path / "oc")
    run_dir_agy, state_agy, item_agy = _setup_backlog_and_plan_fixture(tmp_path / "agy")

    oc_msgs: list[str] = []
    agy_msgs: list[str] = []

    def fake_close_oc(
        repo: Path, item_path: Path, item_id6: str, evidence: str, message: str
    ) -> tuple[int, str]:
        oc_msgs.append(message)
        return (0, "ok")

    def fake_close_agy(
        repo: Path, item_path: Path, item_id6: str, evidence: str, message: str
    ) -> tuple[int, str]:
        agy_msgs.append(message)
        return (0, "ok")

    def fake_commit(repo: Path, item_id6: str, message: str, **kwargs: Any) -> str:
        return "mock-sha"

    with mock.patch.object(
        oc_runipd, "close_backlog_item", fake_close_oc
    ), mock.patch.object(
        oc_runipd, "commit_backlog_close", fake_commit
    ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        oc_runipd.process_backlog_close(run_dir_oc, state_oc, item_oc)

    with mock.patch.object(
        agy_runipd, "close_backlog_item", fake_close_agy
    ), mock.patch.object(
        agy_runipd, "commit_backlog_close", fake_commit
    ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        agy_runipd.process_backlog_close(run_dir_agy, state_agy, item_agy)

    assert item_oc.get("backlog_close", {}).get("closed") is True
    assert item_agy.get("backlog_close", {}).get("closed") is True

    assert oc_msgs[0].startswith("closed by aw oc run:")
    assert agy_msgs[0].startswith("closed by aw agy run:")
    assert oc_msgs[0] != agy_msgs[0]
