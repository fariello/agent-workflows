"""Tests for `aw commit --scope-reason` escape and begin-receipt persistence.

Pins the commit-gate matrix (accepted, still-refused, partial-exemption, malformed),
the selector recovery across four argument orders, the receipt writer/reader idempotence,
the no-receipt warning behavior, and the end-to-end lifecycle consumption at finalize.
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import (
    check_engine,
    cli,
    ipd_lifecycle as LC,
    work_cmd,
    worktree_lease,
)
from tests import support
from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _completed_plan_text,
    _init_git,
    _write_plan,
)


class CommitFlagRecoveryTests(unittest.TestCase):
    """Unit tests pinning selector recovery in _recover_commit_flags for four argument orders."""

    def test_selector_recovered_when_flag_before_selector(self) -> None:
        """Flag before selector: selector must be recovered, not the flag's value."""
        raw = ["--scope-reason", "a/b.py=why", "abc123", "--", "x.py"]
        selector, saw_no_plan, pre = work_cmd._recover_commit_flags(raw)
        self.assertEqual(selector, "abc123")
        self.assertFalse(saw_no_plan)

    def test_selector_recovered_when_flag_after_selector(self) -> None:
        """Flag after selector: selector must still be recovered correctly."""
        raw = ["abc123", "--scope-reason", "a/b.py=why", "--", "x.py"]
        selector, saw_no_plan, pre = work_cmd._recover_commit_flags(raw)
        self.assertEqual(selector, "abc123")
        self.assertFalse(saw_no_plan)

    def test_selector_recovered_when_equals_form(self) -> None:
        """Single-token --scope-reason=PATH=WHY form must not be treated as selector."""
        raw = ["abc123", "--scope-reason=a/b.py=why", "--", "x.py"]
        selector, saw_no_plan, pre = work_cmd._recover_commit_flags(raw)
        self.assertEqual(selector, "abc123")
        self.assertFalse(saw_no_plan)

    def test_selector_recovered_with_no_flag(self) -> None:
        """Baseline order with no --scope-reason flag."""
        raw = ["abc123", "--", "x.py"]
        selector, saw_no_plan, pre = work_cmd._recover_commit_flags(raw)
        self.assertEqual(selector, "abc123")
        self.assertFalse(saw_no_plan)


class CommitScopeReasonGateTests(unittest.TestCase):
    """Tests covering the commit-gate matrix using real git repos and real lane worktrees."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        self.plan_id = "abc123"
        self.plan_name = f"20260824-demo-01-{self.plan_id}-demo.ipd.md"
        self.plan_text = _completed_plan_text(
            plan_id=self.plan_id,
            scope_paths="agent_workflows/demo.py",
        )
        self.plan_path = _write_plan(self.root, self.plan_text, self.plan_name)

        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "agent_workflows" / "demo.py").write_text(
            "print('demo')\n", encoding="utf-8"
        )
        (self.root / "agent_workflows" / "render.py").write_text(
            "print('render')\n", encoding="utf-8"
        )
        (self.root / "agent_workflows" / "extra.py").write_text(
            "print('extra')\n", encoding="utf-8"
        )
        _commit_all(self.root, "init")

        # F-18: allocate lane named specifically for plan_id
        self.lane = worktree_lease.allocate_worktree(self.root, self.plan_id).path
        self.lane_plan = (
            self.lane / ".aw" / "records" / "plans" / "pending" / self.plan_name
        )
        self.actor = "opencode/test"
        res = LC.begin(
            self.lane, self.lane_plan, self.actor, timestamp="2026-08-24T00:00:00Z"
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        # Assert the lane RESOLVES in check_engine (F-18 guard against false green)
        base_head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()
        resolved = check_engine._plan_execution_tree(self.lane, self.plan_id, base_head)
        self.assertIsNotNone(
            resolved,
            f"Lane '{self.lane}' for plan '{self.plan_id}' must resolve in check_engine._plan_execution_tree",
        )
        self.parser = cli._build_parser()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_out_of_scope_accepted_with_scope_reason(self) -> None:
        """Case (a): an out-of-scope path named with a matching --scope-reason commits (exit 0)."""
        (self.lane / "agent_workflows" / "render.py").write_text(
            "print('render edited')\n", encoding="utf-8"
        )

        args = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(self.lane),
                "--scope-reason",
                "agent_workflows/render.py=needed for render functionality",
                self.plan_id,
                "--",
                "agent_workflows/render.py",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()
        self.assertEqual(rc, 0, f"Expected rc 0, got {rc}. Output:\n{out}")
        self.assertIn("committed 1 path(s)", out)

        show_out = subprocess.check_output(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.lane,
            text=True,
        )
        self.assertIn("agent_workflows/render.py", show_out.strip())

    def test_out_of_scope_still_refused_without_scope_reason(self) -> None:
        """Case (b): same out-of-scope path with NO flag exits 1 with out-of-scope change(s) present and HEAD unchanged."""
        (self.lane / "agent_workflows" / "render.py").write_text(
            "print('render unapproved')\n", encoding="utf-8"
        )
        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()

        args = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(self.lane),
                self.plan_id,
                "--",
                "agent_workflows/render.py",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()
        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()

        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("aw commit: refusing - out-of-scope change(s) present:", out)
        self.assertIn("agent_workflows/render.py", out)
        self.assertEqual(
            head_before, head_after, "HEAD must remain unchanged after refusal"
        )

    def test_scope_reason_not_a_blanket_key(self) -> None:
        """Case (c): --scope-reason for path A does NOT exempt an unjustified out-of-scope path B."""
        (self.lane / "agent_workflows" / "render.py").write_text(
            "print('render change')\n", encoding="utf-8"
        )
        (self.lane / "agent_workflows" / "extra.py").write_text(
            "print('extra change')\n", encoding="utf-8"
        )
        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()

        args = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(self.lane),
                "--scope-reason",
                "agent_workflows/render.py=needed for render functionality",
                self.plan_id,
                "--",
                "agent_workflows/render.py",
                "agent_workflows/extra.py",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()
        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()

        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("aw commit: refusing - out-of-scope change(s) present:", out)
        self.assertIn("agent_workflows/extra.py", out)
        self.assertEqual(
            head_before,
            head_after,
            "HEAD must remain unchanged when an unjustified path is present",
        )

    def test_malformed_scope_reason_refused_exit_2(self) -> None:
        """Case (d): a malformed --scope-reason token (no =) exits 2 and names the malformation."""
        (self.lane / "agent_workflows" / "render.py").write_text(
            "print('render change')\n", encoding="utf-8"
        )
        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()

        args = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(self.lane),
                "--scope-reason",
                "noequals",
                self.plan_id,
                "--",
                "agent_workflows/render.py",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()
        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane, text=True
        ).strip()

        self.assertEqual(rc, 2, f"Expected rc 2, got {rc}. Output:\n{out}")
        self.assertIn("malformed --scope-reason", out)
        self.assertIn("noequals", out)
        self.assertEqual(
            head_before, head_after, "HEAD must remain unchanged on malformed input"
        )


class ReceiptScopeReasonTests(unittest.TestCase):
    """Tests for record_scope_reasons and read_scope_reasons idempotence and warning behavior."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        self.plan_id = "abc123"
        self.plan_name = f"20260824-demo-01-{self.plan_id}-demo.ipd.md"
        self.plan_text = _completed_plan_text(
            plan_id=self.plan_id,
            scope_paths="agent_workflows/demo.py",
        )
        self.plan_path = _write_plan(self.root, self.plan_text, self.plan_name)
        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "agent_workflows" / "demo.py").write_text(
            "print('demo')\n", encoding="utf-8"
        )
        (self.root / "agent_workflows" / "render.py").write_text(
            "print('render')\n", encoding="utf-8"
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_record_scope_reasons_idempotent_and_audited(self) -> None:
        """Writing a reason for the same path twice leaves the newer reason effective and both in the audit list."""
        actor = "opencode/test"
        res = LC.begin(
            self.root, self.plan_path, actor, timestamp="2026-08-24T00:00:00Z"
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK)

        # 1. First write
        ok1, msg1 = LC.record_scope_reasons(
            self.root,
            self.plan_id,
            {"agent_workflows/render.py": "initial reason"},
            timestamp="2026-08-24T01:00:00Z",
        )
        self.assertTrue(ok1, msg1)
        reasons1 = LC.read_scope_reasons(self.root, self.plan_id)
        self.assertEqual(reasons1, {"agent_workflows/render.py": "initial reason"})

        # 2. Second write for same path with updated reason
        ok2, msg2 = LC.record_scope_reasons(
            self.root,
            self.plan_id,
            {"agent_workflows/render.py": "updated reason"},
            timestamp="2026-08-24T02:00:00Z",
        )
        self.assertTrue(ok2, msg2)
        reasons2 = LC.read_scope_reasons(self.root, self.plan_id)
        self.assertEqual(reasons2, {"agent_workflows/render.py": "updated reason"})

        # 3. Verify audit history in receipt JSON
        rcpt_path = LC.receipt_path_for(self.root, self.plan_id)
        receipt = json.loads(rcpt_path.read_text(encoding="utf-8"))
        audit = receipt.get("scope_justifications_audit", [])
        self.assertEqual(len(audit), 2)
        self.assertEqual(audit[0]["reason"], "initial reason")
        self.assertIsNone(audit[0]["previous_reason"])
        self.assertEqual(audit[1]["reason"], "updated reason")
        self.assertEqual(audit[1]["previous_reason"], "initial reason")

        # 4. Invariant: base_head is untouched and receipt remains current
        self.assertTrue(LC.receipt_is_current(receipt, self.plan_text))
        pre_exit, pre_msg, _, _ = LC.finalize_precheck(self.root, self.plan_path)
        self.assertEqual(pre_exit, LC.EXIT_OK, pre_msg)

    def test_commit_with_no_receipt_succeeds_and_warns(self) -> None:
        """aw commit <plan> --scope-reason on a plan with no begin receipt exits 0, commits, and warns."""
        # No LC.begin was run, so no begin receipt exists
        rcpt_path = LC.receipt_path_for(self.root, self.plan_id)
        self.assertFalse(rcpt_path.exists())

        (self.root / "agent_workflows" / "render.py").write_text(
            "print('render without receipt')\n", encoding="utf-8"
        )
        parser = cli._build_parser()
        args = parser.parse_args(
            [
                "commit",
                "--dir",
                str(self.root),
                "--scope-reason",
                "agent_workflows/render.py=needed without begin",
                self.plan_id,
                "--",
                "agent_workflows/render.py",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()

        self.assertEqual(rc, 0, f"Expected rc 0, got {rc}. Output:\n{out}")
        self.assertIn("could not persist scope reason(s) to begin receipt", out)
        self.assertIn("supplied again at finalize", out)
        self.assertIn("committed 1 path(s)", out)
        # Invariant: no receipt file was minted
        self.assertFalse(
            rcpt_path.exists(), "Must never mint a receipt during aw commit"
        )


class LifecycleEndToEndTests(unittest.TestCase):
    """End-to-end tests proving commit-time reasons survive and are consumed by finalize."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        self.plan_id = "abc123"
        self.plan_name = f"20260824-demo-01-{self.plan_id}-demo.ipd.md"
        self.plan_text = _completed_plan_text(
            plan_id=self.plan_id,
            scope_paths="agent_workflows/demo.py",
        )
        self.plan_path = _write_plan(self.root, self.plan_text, self.plan_name)
        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "agent_workflows" / "demo.py").write_text(
            "print('demo')\n", encoding="utf-8"
        )
        (self.root / "agent_workflows" / "render.py").write_text(
            "print('render')\n", encoding="utf-8"
        )
        _commit_all(self.root, "init")

        self.lane = worktree_lease.allocate_worktree(self.root, self.plan_id).path
        self.lane_plan = (
            self.lane / ".aw" / "records" / "plans" / "pending" / self.plan_name
        )
        self.actor = "opencode/test"
        res = LC.begin(
            self.lane, self.lane_plan, self.actor, timestamp="2026-08-24T00:00:00Z"
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        run_id = "run-20260824T000000Z-123456"
        run_dir = self.root / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        self.parser = cli._build_parser()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_end_to_end_reason_survives_commit_and_satisfies_finalize(self) -> None:
        """An out-of-scope path justified once at commit time finalizes without re-supplying the reason."""
        (self.lane / "agent_workflows" / "demo.py").write_text(
            "print('demo edited')\n", encoding="utf-8"
        )
        (self.lane / "agent_workflows" / "render.py").write_text(
            "print('render justified')\n", encoding="utf-8"
        )

        # 1. Commit out-of-scope path with --scope-reason (alongside declared in-scope path)
        reason_text = "needed for specialized rendering output"
        args = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(self.lane),
                "--scope-reason",
                f"agent_workflows/render.py={reason_text}",
                self.plan_id,
                "--",
                "agent_workflows/demo.py",
                "agent_workflows/render.py",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()
        self.assertEqual(rc, 0, f"Expected rc 0, got {rc}. Output:\n{out}")

        # 2. Check receipt store has the reason
        stored = LC.read_scope_reasons(self.lane, self.plan_id)
        self.assertEqual(stored.get("agent_workflows/render.py"), reason_text)

        # 3. Finalize precheck/reconciliation with NO scope_reasons re-supplied passes (exit 0)
        res_preview = LC.finalize(
            self.lane,
            self.lane_plan,
            actor=self.actor,
            message="complete execution",
            apply=False,
            env={},
        )
        self.assertEqual(
            res_preview.exit_code,
            LC.EXIT_OK,
            f"Preview finalize should pass exit 0; got {res_preview.exit_code}: {res_preview.message}. Findings: {res_preview.findings}",
        )

        # 4. Finalize with apply=True passes and records reason in ## Workflow history
        res_apply = LC.finalize(
            self.lane,
            self.lane_plan,
            actor=self.actor,
            message="complete execution",
            apply=True,
            env={},
        )
        self.assertEqual(
            res_apply.exit_code,
            LC.EXIT_OK,
            f"Apply finalize should pass exit 0; got {res_apply.exit_code}: {res_apply.message}. Findings: {res_apply.findings}",
        )

        # Check moved plan in executed/ has the reason text verbatim in history
        executed_plan = (
            self.lane / ".aw" / "records" / "plans" / "executed" / self.plan_name
        )
        self.assertTrue(
            executed_plan.is_file(), f"Plan must be moved to executed: {executed_plan}"
        )
        content = executed_plan.read_text(encoding="utf-8")
        self.assertIn("out-of-scope agent_workflows/render.py: " + reason_text, content)

    def test_end_to_end_unjustified_path_refuses_at_finalize(self) -> None:
        """Contrast: when no reason is supplied, finalize refuses with exit 1 demanding it."""
        (self.lane / "agent_workflows" / "demo.py").write_text(
            "print('demo edited')\n", encoding="utf-8"
        )
        (self.lane / "agent_workflows" / "render.py").write_text(
            "print('render unjustified')\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py", "agent_workflows/render.py"],
            cwd=self.lane,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "unjustified change"],
            cwd=self.lane,
            check=True,
        )

        res_preview = LC.finalize(
            self.lane,
            self.lane_plan,
            actor=self.actor,
            message="complete execution",
            apply=False,
            env={},
        )
        self.assertEqual(res_preview.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any(
                "out-of-scope path needs a --scope-reason: agent_workflows/render.py"
                in f
                for f in res_preview.findings
            ),
            f"Expected out-of-scope path finding in {res_preview.findings}",
        )
