"""Tests for orchestrator retirement closing backlog item (lr6lnm E-05, E-07)."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest

from agent_workflows import coverage_record, oc_runipd, runner_shared
from tests import support
from tests.test_orchestrator_retirement import (
    _init_git_repo,
    _table,
    _write_conforming_plan,
)


class TestOrchestratorRetireClosesBacklog(unittest.TestCase):
    """Behavioral tests verifying orchestrator retirement closes its backlog item."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        from agent_workflows import ipd_lifecycle as LC

        LC.clear_checkout_control_root_cache()
        self.addCleanup(LC.clear_checkout_control_root_cache)

    def test_orchestrator_retirement_closes_backlog_item(self) -> None:
        """When an orchestrator retires and all carriers are terminal, its backlog item closes done."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git_repo(repo)

            bkl_dir = repo / ".aw" / "records" / "backlog" / "open"
            bkl_dir.mkdir(parents=True, exist_ok=True)
            bkl_file = bkl_dir / "20260906-bkl001-01-bkl001-test-item.backlog.md"
            bkl_file.write_text(
                "- Id: bkl001\n"
                "- Status: open\n"
                "- Summary: test item\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n\n"
                "## Workflow history\n"
                "- 2026-09-06 created (aw backlog): created\n",
                encoding="utf-8",
            )

            # Executed child plan in executed/
            _write_conforming_plan(
                repo,
                "executed",
                plan_id="chi001",
                set_id="seto",
                order=1,
                status="executed",
                kind="child",
            )

            # Orchestrator plan in pending/
            child_table = _table(
                ["Order", "Id", "Child", "Depends on"],
                [["01", "chi001", "child 01", "none"]],
            )
            checklist_rows = [
                "- [ ] E-01 CONFIRM chi001 REACHED executed\n"
                "  - Depends on: none\n"
                "  - Expected outcome: chi001 reached executed\n"
                "  - Execution state: pending"
            ]
            validation_rows = [
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: chi001 reached executed\n"
                "  - Observed evidence:\n"
                "  - Result: pending"
            ]
            orc_file = _write_conforming_plan(
                repo,
                "pending",
                plan_id="orc001",
                set_id="seto",
                order=0,
                status="approved",
                kind="orchestrator",
                child_table=child_table,
                checklist_rows=checklist_rows,
                validation_rows=validation_rows,
            )
            txt = orc_file.read_text("utf-8")
            txt = txt.replace("- Id: orc001", "- Id: orc001\n- From-Backlog: bkl001")
            orc_file.write_text(txt, "utf-8")

            coverage_record.write(
                orc_file, verdict=coverage_record.COVERAGE_PASS, commit=False
            )

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "initial state"], cwd=repo, check=True
            )

            run_dir = repo / "run"
            run_dir.mkdir(parents=True, exist_ok=True)

            item = {
                "id6": "orc001",
                "setid": "seto",
                "action": "orchestrate",
                "status": "queued",
                "from_backlog": "bkl001",
                "configured_file": str(orc_file),
            }
            state = {
                "run_id": "run-test-retire-success",
                "repo": str(repo),
                "queue": [item],
            }

            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                decision = runner_shared.dispatch_orchestrator_item(
                    repo,
                    run_dir,
                    state,
                    item,
                    actor="aw oc run",
                    terminal_states=oc_runipd.TERMINAL_STATES,
                    success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                    host="oc",
                    process_backlog_close=oc_runipd.process_backlog_close,
                )

            self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_RETIRE)
            self.assertEqual(item.get("status"), "executed")
            self.assertIsNotNone(item.get("last_plan_path"))
            self.assertIn("executed", item["last_plan_path"])

            backlog_close = item.get("backlog_close") or {}
            self.assertTrue(backlog_close.get("closed"))
            self.assertEqual(backlog_close.get("item"), "bkl001")

            # Assert backlog item moved to done/
            done_items = list(
                (repo / ".aw" / "records" / "backlog" / "done").glob("*bkl001*")
            )
            open_items = list(
                (repo / ".aw" / "records" / "backlog" / "open").glob("*bkl001*")
            )
            self.assertEqual(len(done_items), 1)
            self.assertEqual(len(open_items), 0)

            # Assert unclosed reports nothing
            unclosed = runner_shared.classify_unclosed(state, run_dir=run_dir)
            self.assertEqual(unclosed, [])

    def test_orchestrator_retirement_with_unexecuted_sibling_stays_waiting(
        self,
    ) -> None:
        """When an orchestrator retires but a sibling carrier is unexecuted, backlog item stays waiting-on-carriers."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git_repo(repo)

            bkl_dir = repo / ".aw" / "records" / "backlog" / "open"
            bkl_dir.mkdir(parents=True, exist_ok=True)
            bkl_file = bkl_dir / "20260906-bkl002-01-bkl002-test-item.backlog.md"
            bkl_file.write_text(
                "- Id: bkl002\n"
                "- Status: open\n"
                "- Summary: test item 2\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n\n"
                "## Workflow history\n"
                "- 2026-09-06 created (aw backlog): created\n",
                encoding="utf-8",
            )

            # Child plan of orchestrator (executed)
            _write_conforming_plan(
                repo,
                "executed",
                plan_id="chi002",
                set_id="seto",
                order=1,
                status="executed",
                kind="child",
            )

            # Sibling carrier in pending/ (unexecuted)
            sib_file = _write_conforming_plan(
                repo,
                "pending",
                plan_id="sib002",
                set_id="sets",
                order=1,
                status="approved",
                kind="child",
            )
            txt_s = sib_file.read_text("utf-8").replace(
                "- Id: sib002", "- Id: sib002\n- From-Backlog: bkl002"
            )
            sib_file.write_text(txt_s, "utf-8")

            # Orchestrator plan in pending/
            child_table = _table(
                ["Order", "Id", "Child", "Depends on"],
                [["01", "chi002", "child 01", "none"]],
            )
            checklist_rows = [
                "- [ ] E-01 CONFIRM chi002 REACHED executed\n"
                "  - Depends on: none\n"
                "  - Expected outcome: chi002 reached executed\n"
                "  - Execution state: pending"
            ]
            validation_rows = [
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: chi002 reached executed\n"
                "  - Observed evidence:\n"
                "  - Result: pending"
            ]
            orc_file = _write_conforming_plan(
                repo,
                "pending",
                plan_id="orc002",
                set_id="seto",
                order=0,
                status="approved",
                kind="orchestrator",
                child_table=child_table,
                checklist_rows=checklist_rows,
                validation_rows=validation_rows,
            )
            txt = orc_file.read_text("utf-8")
            txt = txt.replace("- Id: orc002", "- Id: orc002\n- From-Backlog: bkl002")
            orc_file.write_text(txt, "utf-8")

            coverage_record.write(
                orc_file, verdict=coverage_record.COVERAGE_PASS, commit=False
            )

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "initial state"], cwd=repo, check=True
            )

            run_dir = repo / "run"
            run_dir.mkdir(parents=True, exist_ok=True)

            item = {
                "id6": "orc002",
                "setid": "seto",
                "action": "orchestrate",
                "status": "queued",
                "from_backlog": "bkl002",
                "configured_file": str(orc_file),
            }
            state = {
                "run_id": "run-test-retire-sibling",
                "repo": str(repo),
                "queue": [item],
            }

            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                decision = runner_shared.dispatch_orchestrator_item(
                    repo,
                    run_dir,
                    state,
                    item,
                    actor="aw oc run",
                    terminal_states=oc_runipd.TERMINAL_STATES,
                    success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                    host="oc",
                    process_backlog_close=oc_runipd.process_backlog_close,
                )

            self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_RETIRE)
            self.assertEqual(item.get("status"), "executed")

            backlog_close = item.get("backlog_close") or {}
            self.assertFalse(backlog_close.get("closed"))
            self.assertIn(
                "IPD carrier(s) not executed", backlog_close.get("reason", "")
            )

            # Backlog item remains in open/
            open_items = list(
                (repo / ".aw" / "records" / "backlog" / "open").glob("*bkl002*")
            )
            done_items = list(
                (repo / ".aw" / "records" / "backlog" / "done").glob("*bkl002*")
            )
            self.assertEqual(len(open_items), 1)
            self.assertEqual(len(done_items), 0)

            # Unclosed item has cause waiting-on-carriers and detail sib002
            unclosed = runner_shared.classify_unclosed(state, run_dir=run_dir)
            self.assertEqual(len(unclosed), 1)
            self.assertEqual(unclosed[0].cause, "waiting-on-carriers")
            self.assertEqual(unclosed[0].detail, "sib002")
            self.assertFalse(unclosed[0].needs_action)
