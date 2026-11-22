"""Tests for orchestrator retirement closing backlog item (lr6lnm E-05, E-07)."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import re
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
from tests.record_builder import RecordBuilder


def _orchestrator_with_backlog(
    repo: Path,
    *,
    plan_id: str,
    set_id: str,
    from_backlog: str,
    child_table: str,
    checklist_rows: list[str],
    validation_rows: list[str],
) -> Path:
    text = str(
        RecordBuilder().plan(
            plan_role="orchestrator",
            title="synthetic orchestrator",
            author="tester",
            when="2026-09-06",
            set=set_id,
            order=0,
            id6=plan_id,
            status="approved",
            scope_paths="grandfathered",
            item_dependencies="none",
            priority="medium",
            work_kind="chore",
            approval="2026-09-06, human: approved",
            readiness="go-pending-approval",
            from_backlog=from_backlog,
            text_only=True,
        )
    )
    text = text.replace(
        "## Child IPDs, sequence, and dependencies\n\n"
        "| Order | Id | File | What it does | Depends on |\n"
        "|---|---|---|---|---|\n"
        "| 01 | `c0ch01` | TODO child plan filename | TODO what it does. | none |\n",
        child_table + "\n",
    )
    exec_body = "\n\n".join(checklist_rows)
    text = re.sub(
        r"### Task group 1: TODO\n\n- \[ \] E-01 CONFIRM c0ch01 REACHED executed.*?(?=\n\n##|\Z)",
        f"### Task group 1: Child confirmation\n\n{exec_body}\n",
        text,
        flags=re.DOTALL,
    )
    valid_body = "\n\n".join(validation_rows)
    text = re.sub(
        r"- \[ \] V-01 validates E-01.*?(?=\n\n##|\Z)",
        f"{valid_body}\n",
        text,
        flags=re.DOTALL,
    )
    d = repo / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"20260906-{set_id}-00-{plan_id}-synthetic.ipd.md"
    path.write_text(text, encoding="utf-8")
    return path


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
                RecordBuilder().backlog(
                    id6="bkl001",
                    status="open",
                    summary="test item",
                    priority="medium",
                    work_kind="bug",
                    history=["- 2026-09-06 created (aw backlog): created"],
                    text_only=True,
                ),
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
            orc_file = _orchestrator_with_backlog(
                repo,
                plan_id="orc001",
                set_id="seto",
                from_backlog="bkl001",
                child_table=child_table,
                checklist_rows=checklist_rows,
                validation_rows=validation_rows,
            )

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
                RecordBuilder().backlog(
                    id6="bkl002",
                    status="open",
                    summary="test item 2",
                    priority="medium",
                    work_kind="bug",
                    history=["- 2026-09-06 created (aw backlog): created"],
                    text_only=True,
                ),
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
            RecordBuilder(repo).plan(
                plan_role="child",
                title="synthetic child",
                author="tester",
                when="2026-09-06",
                set="sets",
                order=1,
                id6="sib002",
                status="approved",
                scope_paths="grandfathered",
                item_dependencies="none",
                priority="medium",
                work_kind="chore",
                approval="2026-09-06, human: approved",
                readiness="go-pending-approval",
                from_backlog="bkl002",
                disposition="pending",
                slug="synthetic",
            )

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
            orc_file = _orchestrator_with_backlog(
                repo,
                plan_id="orc002",
                set_id="seto",
                from_backlog="bkl002",
                child_table=child_table,
                checklist_rows=checklist_rows,
                validation_rows=validation_rows,
            )

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
