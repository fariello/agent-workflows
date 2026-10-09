"""Tests for Scope-Exceeded metadata insertion, out-of-scope send-back, and recording-only commit.

Covers IPD psgyzw (Set fixfirst, Order 06) requirements:
(a) finalize inserting `- Scope-Exceeded: <path> (<reason>); ...` into moved plan metadata when out-of-scope paths are reconciled;
(b) finalize leaving plan metadata untouched when changes were fully in-scope;
(c) multiple out-of-scope paths formatted deterministically (sorted by path, newlines sanitized);
(d) runner retry loop when finalize refuses with scope-reconciliation: prompt receives out-of-scope notice with recovery turn instructions;
(e) `aw commit <id6> --scope-reason <path>=<why>` without paths records into the begin receipt without creating a git commit, and `aw commit --help` documents it;
(f) `aw commit <id6> --scope-reason` rejects paths that are NOT out-of-scope for the plan;
(g) recorded scope justifications survive recovery re-begin.
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
    cli,
    ipd_lifecycle as LC,
    ipd_lint,
    runner_shared,
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


class TestScopeExceededMetadataAndSendBack(unittest.TestCase):
    """Behavioral tests covering Scope-Exceeded lifecycle, send-back notice, and commit handling."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        self.parser = cli._build_parser()

        run_id = "run-test-20261009"
        run_dir = self.root / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _setup_lane_and_plan(
        self, plan_id: str, scope_paths: str = "src/demo.py"
    ) -> tuple[Path, Path, str]:
        """Create a conforming plan and an isolated lane worktree."""
        plan_name = f"20260824-demo-01-{plan_id}-demo.ipd.md"
        plan_text = _completed_plan_text(
            plan_id=plan_id,
            scope_paths=scope_paths,
        )
        _write_plan(self.root, plan_text, plan_name)
        (self.root / "src").mkdir(parents=True, exist_ok=True)
        (self.root / "src" / "demo.py").write_text("print('demo')\n", encoding="utf-8")
        _commit_all(self.root, "initial commit")

        lane = worktree_lease.allocate_worktree(self.root, plan_id).path
        lane_plan = lane / ".aw" / "records" / "plans" / "pending" / plan_name
        return lane, lane_plan, plan_name

    def test_case_a_finalize_inserts_scope_exceeded_metadata(self) -> None:
        """(a) finalize inserts `- Scope-Exceeded: <path> (<reason>); ...` when out-of-scope paths are reconciled."""
        plan_id = "scxa01"
        lane, lane_plan, plan_name = self._setup_lane_and_plan(plan_id, "src/demo.py")
        actor = "test-actor"

        begin_res = LC.begin(lane, lane_plan, actor, timestamp="2026-10-09T00:00:00Z")
        self.assertEqual(begin_res.exit_code, LC.EXIT_OK, begin_res.message)

        # In-scope change
        (lane / "src" / "demo.py").write_text("print('in scope')\n", encoding="utf-8")
        # Out-of-scope change
        (lane / "extra.py").write_text("print('out of scope')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/demo.py", "extra.py"], cwd=lane, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "feat: in and out of scope edits"],
            cwd=lane,
            check=True,
        )

        fin_res = LC.finalize(
            lane,
            lane_plan,
            actor,
            "finalize case a",
            apply=True,
            scope_reasons={"extra.py": "needed for feature extension"},
        )
        self.assertEqual(fin_res.exit_code, LC.EXIT_OK, fin_res.message)

        executed_plan = lane / ".aw" / "records" / "plans" / "executed" / plan_name
        self.assertTrue(
            executed_plan.is_file(), f"Plan must be moved to {executed_plan}"
        )
        content = executed_plan.read_text(encoding="utf-8")
        self.assertIn(
            "- Scope-Exceeded: extra.py (needed for feature extension)\n",
            content,
            "Executed plan must carry Scope-Exceeded metadata bullet",
        )

        # Must conform to linting (no unknown-field IPD-M103)
        lint_res = ipd_lint.lint_file(executed_plan)
        self.assertEqual(lint_res.disposition, "legacy/not evaluated")

    def test_case_b_finalize_leaves_metadata_untouched_when_fully_in_scope(
        self,
    ) -> None:
        """(b) finalize leaves plan metadata untouched when changes were fully in-scope."""
        plan_id = "scxb01"
        lane, lane_plan, plan_name = self._setup_lane_and_plan(plan_id, "src/demo.py")
        actor = "test-actor"

        begin_res = LC.begin(lane, lane_plan, actor, timestamp="2026-10-09T00:00:00Z")
        self.assertEqual(begin_res.exit_code, LC.EXIT_OK, begin_res.message)

        (lane / "src" / "demo.py").write_text("print('updated')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/demo.py"], cwd=lane, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "feat: in scope only"], cwd=lane, check=True
        )

        fin_res = LC.finalize(
            lane,
            lane_plan,
            actor,
            "finalize case b",
            apply=True,
        )
        self.assertEqual(fin_res.exit_code, LC.EXIT_OK, fin_res.message)

        executed_plan = lane / ".aw" / "records" / "plans" / "executed" / plan_name
        self.assertTrue(executed_plan.is_file())
        content = executed_plan.read_text(encoding="utf-8")
        self.assertNotIn("- Scope-Exceeded:", content)

        lint_res = ipd_lint.lint_file(executed_plan)
        self.assertEqual(lint_res.disposition, "legacy/not evaluated")

    def test_case_c_multiple_out_of_scope_paths_sorted_and_sanitized(self) -> None:
        """(c) multiple out-of-scope paths formatted deterministically (sorted, sanitized newlines)."""
        plan_id = "scxc01"
        lane, lane_plan, plan_name = self._setup_lane_and_plan(plan_id, "src/demo.py")
        actor = "test-actor"

        begin_res = LC.begin(lane, lane_plan, actor, timestamp="2026-10-09T00:00:00Z")
        self.assertEqual(begin_res.exit_code, LC.EXIT_OK, begin_res.message)

        (lane / "src" / "demo.py").write_text("# demo updated\n", encoding="utf-8")
        (lane / "z_file.py").write_text("# z\n", encoding="utf-8")
        (lane / "a_file.py").write_text("# a\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "src/demo.py", "z_file.py", "a_file.py"],
            cwd=lane,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-qm", "feat: multiple out of scope"],
            cwd=lane,
            check=True,
        )

        reasons = {
            "z_file.py": "reason for z\nwith newline that must be sanitized",
            "a_file.py": "reason for a",
        }
        fin_res = LC.finalize(
            lane,
            lane_plan,
            actor,
            "finalize case c",
            apply=True,
            scope_reasons=reasons,
        )
        self.assertEqual(fin_res.exit_code, LC.EXIT_OK, fin_res.message)

        executed_plan = lane / ".aw" / "records" / "plans" / "executed" / plan_name
        content = executed_plan.read_text(encoding="utf-8")
        expected_meta = (
            "- Scope-Exceeded: a_file.py (reason for a); "
            "z_file.py (reason for z with newline that must be sanitized)\n"
        )
        self.assertIn(expected_meta, content)

    def test_case_d_runner_retry_loop_out_of_scope_notice(self) -> None:
        """(d) runner retry loop receives out-of-scope notice with recovery turn instructions."""
        refusal_msg = (
            "refused: finalize needs scope reconciliation answers (plan left unmoved).\n"
            "  out-of-scope path needs a --scope-reason: extra_one.py\n"
            "  out-of-scope path needs a --scope-reason: extra_two.py"
        )

        # 1. Verification of retryable classification
        self.assertTrue(runner_shared.finalize_refusal_is_retryable(refusal_msg))

        item = {
            "id6": "scxd01",
            "setid": "demo",
            "position": 1,
            "action": "execute",
            "attempts": [{"finalize_refused": refusal_msg}],
        }
        state = {"retry_budget": 2, "run_id": "run-test-20261009"}
        decision = runner_shared.finalize_retry_decision(item, state, refusal_msg)
        self.assertTrue(decision.retry)
        self.assertIn("out-of-scope paths need reconciliation reasons", decision.reason)

        # 2. build_out_of_scope_notice creates detailed action options
        notice = runner_shared.build_out_of_scope_notice(item, recovery=True)
        self.assertIn("Out-of-scope modification", notice)
        self.assertIn("REVERT the change", notice)
        self.assertIn("JUSTIFY it", notice)
        self.assertIn("aw commit scxd01 --scope-reason", notice)

        # 3. Notice is injected into recovery prompt
        lane, lane_plan, _ = self._setup_lane_and_plan("scxd01")
        run_dir = self.root / ".aw" / "records" / "runs" / "run-test-20261009"
        prompt = runner_shared.build_prompt(
            item,
            state,
            run_dir,
            lane_plan,
            recovery=True,
            labels=runner_shared.OC_HOST_LABELS,
        )
        self.assertIn("Out-of-scope modification", prompt)
        self.assertIn("aw commit scxd01 --scope-reason", prompt)

    def test_case_e_commit_scope_reason_recording_only_without_paths(self) -> None:
        """(e) `aw commit <id6> --scope-reason <path>=<why>` without paths records without git commit."""
        plan_id = "scxe01"
        lane, lane_plan, _ = self._setup_lane_and_plan(plan_id, "src/demo.py")
        actor = "test-actor"

        begin_res = LC.begin(lane, lane_plan, actor, timestamp="2026-10-09T00:00:00Z")
        self.assertEqual(begin_res.exit_code, LC.EXIT_OK, begin_res.message)

        # Create and commit an out-of-scope file with raw git commit
        (lane / "unscoped.py").write_text("print('unscoped')\n", encoding="utf-8")
        subprocess.run(["git", "add", "unscoped.py"], cwd=lane, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "feat: unscoped commit"], cwd=lane, check=True
        )

        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=lane, text=True
        ).strip()

        # Run aw commit <id6> --scope-reason unscoped.py=<why> without paths
        args = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(lane),
                "--scope-reason",
                "unscoped.py=needed for unscoped utility",
                plan_id,
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = work_cmd.run_commit(args)
        out = buf.getvalue()
        self.assertEqual(rc, 0, f"Expected rc 0, got {rc}. Output:\n{out}")
        self.assertIn("recorded 1 scope justification(s)", out.lower())

        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=lane, text=True
        ).strip()
        self.assertEqual(
            head_before, head_after, "No git commit should have been created"
        )

        # Verify receipt has the recorded scope reason
        receipt_reasons = LC.read_scope_reasons(lane, plan_id)
        self.assertEqual(
            receipt_reasons,
            {"unscoped.py": "needed for unscoped utility"},
        )

        # Verify CLI help documents recording-only mode
        help_buf = io.StringIO()
        with redirect_stdout(help_buf):
            try:
                self.parser.parse_args(["commit", "--help"])
            except SystemExit:
                pass
        help_out = help_buf.getvalue()
        self.assertIn("--scope-reason", help_out)
        self.assertIn("without committing", help_out)
        self.assertIn("already-committed paths", help_out)

    def test_case_f_commit_scope_reason_rejects_paths_not_out_of_scope(self) -> None:
        """(f) `aw commit <id6> --scope-reason` rejects paths that are NOT out-of-scope for the plan."""
        plan_id = "scxf01"
        lane, lane_plan, _ = self._setup_lane_and_plan(plan_id, "src/demo.py")
        actor = "test-actor"

        begin_res = LC.begin(lane, lane_plan, actor, timestamp="2026-10-09T00:00:00Z")
        self.assertEqual(begin_res.exit_code, LC.EXIT_OK, begin_res.message)

        # 1. Reject an in-scope path
        args_in_scope = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(lane),
                "--scope-reason",
                "src/demo.py=already in scope",
                plan_id,
            ]
        )
        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            rc1 = work_cmd.run_commit(args_in_scope)
        out1 = buf1.getvalue()
        self.assertEqual(rc1, 2)
        self.assertIn("is not an out-of-scope changed path", out1)

        # 2. Reject an untouched / non-existent path
        args_untouched = self.parser.parse_args(
            [
                "commit",
                "--dir",
                str(lane),
                "--scope-reason",
                "nonexistent.py=not even touched",
                plan_id,
            ]
        )
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = work_cmd.run_commit(args_untouched)
        out2 = buf2.getvalue()
        self.assertEqual(rc2, 2)
        self.assertIn("is not an out-of-scope changed path", out2)

    def test_case_g_recorded_scope_justifications_survive_recovery_rebegin(
        self,
    ) -> None:
        """(g) recorded scope justifications survive recovery re-begin."""
        plan_id = "scxg01"
        lane, lane_plan, _ = self._setup_lane_and_plan(plan_id, "src/demo.py")
        actor1 = "test-actor-1"
        actor2 = "test-actor-2"

        # Begin turn 1
        res1 = LC.begin(lane, lane_plan, actor1, timestamp="2026-10-09T00:00:00Z")
        self.assertEqual(res1.exit_code, LC.EXIT_OK, res1.message)

        # Record justification in turn 1
        LC.record_scope_reasons(
            lane, plan_id, {"extra.py": "justification from attempt 1"}
        )
        self.assertEqual(
            LC.read_scope_reasons(lane, plan_id),
            {"extra.py": "justification from attempt 1"},
        )

        # Recovery re-begin in turn 2
        res2 = LC.begin(lane, lane_plan, actor2, timestamp="2026-10-09T01:00:00Z")
        self.assertEqual(res2.exit_code, LC.EXIT_OK, res2.message)

        # Verify justification survived re-begin
        reasons_after = LC.read_scope_reasons(lane, plan_id)
        self.assertEqual(
            reasons_after,
            {"extra.py": "justification from attempt 1"},
            "Recorded scope reasons must survive recovery re-begin",
        )

        # Verify audit history in receipt JSON
        receipt_path = LC.receipt_path_for(lane, plan_id)
        receipt_data = json.loads(receipt_path.read_text(encoding="utf-8"))
        audit = receipt_data.get("scope_justifications_audit", [])
        self.assertTrue(len(audit) >= 1)
        self.assertEqual(audit[0]["path"], "extra.py")
        self.assertEqual(audit[0]["reason"], "justification from attempt 1")
