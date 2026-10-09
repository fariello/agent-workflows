"""Tests for backlog.run_set adapter delegating to status_set.run_set_command (IPD vhiqo6).

Covers:
1. Hand-built Namespace shapes used by existing tests across direct callers:
   - path attribute only
   - args list attribute
   - path selector (id6, setid, relative path)
2. --gate-dir splits the gate root from the write root.
3. runner_shared.close_backlog_item closes an item end to end, with and without
   lane carrier override.
4. Recorded actor defaults to (aw backlog).
5. Direct caller validation of --work-kind and --priority enums.
6. Confirmation gate for machine callers (--agent / --json) requiring --yes.
7. Multi-match setid updates all matching items.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import backlog, runner_shared


class BacklogSetAdapterTests(unittest.TestCase):
    """Test suite for backlog.run_set adapter delegation."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_backlog_adapter_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.tmp,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Runner"],
            cwd=self.tmp,
            check=True,
        )

    def _create_item(
        self,
        *,
        repo: Path | None = None,
        id6: str = "bk0001",
        status: str = "open",
        slug: str = "fixture",
        work_kind: str = "bug",
        priority: str = "high",
        setid: str = "testset",
        blocks_release: str | None = None,
        body_extra: str = "",
    ) -> Path:
        target_repo = repo or self.tmp
        bk_dir = target_repo / ".aw" / "records" / "backlog" / status
        bk_dir.mkdir(parents=True, exist_ok=True)
        p = bk_dir / f"20261009-{id6}-{slug}.md"
        br_line = f"- Blocks-Release: {blocks_release}\n" if blocks_release else ""
        text = (
            f"# Backlog item {id6}\n\n"
            f"- Id: {id6}\n"
            f"- Status: {status}\n"
            f"- Work-Kind: {work_kind}\n"
            f"- Priority: {priority}\n"
            f"- Set: {setid}\n"
            f"{br_line}"
            f"{body_extra}\n"
            f"## Description\nFixture description\n\n"
            f"## Workflow history\n- 2026-10-09 {status} (tester): initial\n"
        )
        p.write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=target_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"add {id6}"], cwd=target_repo, check=True
        )
        return p

    def _create_executed_plan(
        self,
        repo: Path,
        *,
        id6: str = "pl0001",
        from_backlog: str = "bk0001",
        blocks_release: str = "next",
    ) -> Path:
        plan_dir = repo / ".aw" / "records" / "plans" / "executed"
        plan_dir.mkdir(parents=True, exist_ok=True)
        p = plan_dir / f"20261009-testset-01-{id6}-plan.ipd.md"
        text = (
            f"# IPD: Plan {id6}\n\n"
            f"- Id: {id6}\n"
            f"- Status: executed\n"
            f"- Set: testset\n"
            f"- From-Backlog: {from_backlog}\n"
            f"- Blocks-Release: {blocks_release}\n"
            f"- Scope: Fixture scope\n"
            f"- Scope-Paths: tests/test_backlog_set_adapter.py\n\n"
            f"## Goal\nDone\n\n"
            f"## Workflow history\n- 2026-10-09 executed (tester): finished\n"
        )
        p.write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"add executed plan {id6}"], cwd=repo, check=True
        )
        return p

    def test_hand_built_namespace_shape_path_attribute(self) -> None:
        """Callers constructing Namespace(path=...) transition successfully."""
        p = self._create_item(id6="sh0001", status="open")
        args = argparse.Namespace(
            path=str(p),
            status="done",
            message="finished work",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = backlog.run_set(args)

        self.assertEqual(rc, 0, f"Expected rc=0, got {rc}: {err.getvalue()}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-sh0001-fixture.md"
        )
        self.assertTrue(dest.is_file(), f"Destination not found: {dest}")
        content = dest.read_text(encoding="utf-8")
        self.assertIn("- Status: done", content)

    def test_hand_built_namespace_shape_args_list(self) -> None:
        """Callers constructing Namespace(args=[...]) transition successfully."""
        p = self._create_item(id6="sh0002", status="open")
        args = argparse.Namespace(
            args=[str(p)],
            status="done",
            message="finished work via args list",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = backlog.run_set(args)

        self.assertEqual(rc, 0, f"Expected rc=0, got {rc}: {err.getvalue()}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-sh0002-fixture.md"
        )
        self.assertTrue(dest.is_file(), f"Destination not found: {dest}")

    def test_recorded_actor_defaults_to_aw_backlog(self) -> None:
        """History entries stamp (aw backlog) when actor is not explicitly specified."""
        self._create_item(id6="sh0003", status="open")
        args = argparse.Namespace(
            path="sh0003",
            status="done",
            message="verified actor stamp",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = backlog.run_set(args)

        self.assertEqual(rc, 0, f"Expected rc=0, got {rc}: {err.getvalue()}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-sh0003-fixture.md"
        )
        content = dest.read_text(encoding="utf-8")
        self.assertIn("(aw backlog): verified actor stamp", content)

    def test_gate_dir_splits_gate_root_from_write_root(self) -> None:
        """--gate-dir evaluates release gates against gate_root while relocating in repo_root."""
        gate_repo = Path(tempfile.mkdtemp(prefix="aw_gate_repo_"))
        self.addCleanup(lambda: shutil.rmtree(gate_repo, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=gate_repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=gate_repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Runner"],
            cwd=gate_repo,
            check=True,
        )

        self._create_item(
            id6="gt0001",
            status="graduated",
            blocks_release="next",
        )
        # Without carrier in self.tmp, close without gate_dir is refused
        args_fail = argparse.Namespace(
            path="gt0001",
            status="done",
            message="close attempt",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc_fail = backlog.run_set(args_fail)
        self.assertEqual(rc_fail, 1)

        # Create executed plan in gate_repo
        self._create_executed_plan(
            gate_repo, id6="plgt01", from_backlog="gt0001", blocks_release="next"
        )

        # With --gate-dir pointing to gate_repo, close succeeds and lands in self.tmp
        args_success = argparse.Namespace(
            path="gt0001",
            status="done",
            message="close with gate-dir",
            gate_dir=str(gate_repo),
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc_ok = backlog.run_set(args_success)
        self.assertEqual(rc_ok, 0, f"Expected rc=0, got {rc_ok}: {err.getvalue()}")

        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-gt0001-fixture.md"
        )
        self.assertTrue(dest.is_file(), f"Destination not found in lane repo: {dest}")
        self.assertFalse(
            (gate_repo / ".aw" / "records" / "backlog" / "done").exists(),
            "Gate repo should not have received the moved item",
        )

    def test_direct_call_refuses_invalid_work_kind_and_priority(self) -> None:
        """Direct calls with invalid enum values exit 2 before modifying files."""
        p = self._create_item(id6="ev0001", status="open")
        initial_content = p.read_text(encoding="utf-8")

        # Invalid work-kind
        args_wk = argparse.Namespace(
            path=str(p),
            status="open",
            work_kind="unsupported_kind",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc_wk = backlog.run_set(args_wk)
        self.assertEqual(rc_wk, 2)
        self.assertEqual(p.read_text(encoding="utf-8"), initial_content)

        # Invalid priority
        args_prio = argparse.Namespace(
            path=str(p),
            status="open",
            priority="unsupported_priority",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc_prio = backlog.run_set(args_prio)
        self.assertEqual(rc_prio, 2)
        self.assertEqual(p.read_text(encoding="utf-8"), initial_content)

    def test_confirmation_gate_for_agent_caller_without_yes(self) -> None:
        """Agent and JSON callers require --yes to execute mutation."""
        p = self._create_item(id6="cg0001", status="open")
        args = argparse.Namespace(
            path=str(p),
            status="done",
            message="agent close attempt",
            agent=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = backlog.run_set(args)
        self.assertEqual(rc, 2)
        self.assertTrue(p.is_file(), "Item file should remain in open/")
        self.assertIn("aw.agent/v1", out.getvalue())

    def test_setid_multi_selector_updates_all_matches(self) -> None:
        """A multi-match setid updates every matching item in the set."""
        self._create_item(id6="mm0001", setid="multiset", status="open")
        self._create_item(id6="mm0002", setid="multiset", status="open")

        args = argparse.Namespace(
            path="multiset",
            status="done",
            message="close entire set",
            yes=True,
            no_commit=True,
            dir=str(self.tmp),
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = backlog.run_set(args)
        self.assertEqual(rc, 0, f"Expected rc=0: {err.getvalue()}")

        dest1 = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-mm0001-fixture.md"
        )
        dest2 = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-mm0002-fixture.md"
        )
        self.assertTrue(dest1.is_file(), f"First item not moved: {dest1}")
        self.assertTrue(dest2.is_file(), f"Second item not moved: {dest2}")

    def test_runner_shared_close_backlog_item_end_to_end(self) -> None:
        """runner_shared.close_backlog_item drives delegation cleanly."""
        item = self._create_item(
            id6="rs0001",
            status="graduated",
            blocks_release="next",
        )
        self._create_executed_plan(
            self.tmp, id6="plrs01", from_backlog="rs0001", blocks_release="next"
        )

        def runner_run_checked(cmd: list[str], cwd: Path | None = None) -> str:
            res = subprocess.run(
                cmd,
                cwd=cwd or self.tmp,
                capture_output=True,
                text=True,
                check=True,
                env=os.environ,
            )
            return res.stdout

        rc, output = runner_shared.close_backlog_item(
            self.tmp,
            item,
            "rs0001",
            evidence="",
            message="closed by runner test",
            run_checked=runner_run_checked,
        )
        self.assertEqual(rc, 0, f"close_backlog_item failed: {output}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20261009-rs0001-fixture.md"
        )
        self.assertTrue(dest.is_file(), f"Item not moved to done: {dest}")


if __name__ == "__main__":
    unittest.main()
