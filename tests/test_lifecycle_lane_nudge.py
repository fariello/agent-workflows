"""Behavioral tests for lifecycle lane advisory nudge (lifegate m47znv).

Pins the D1 advisory nudge when begin or finalize runs in the main checkout while an unmerged
lane exists for that plan. Ensures:
- Nudge appears in main when a lane exists.
- Nudge does NOT appear when no lane exists.
- Nudge does NOT appear when caller is inside the lane.
- Nudge appears for both begin and finalize.
- Nudge is suppressed under --agent and --json modes with byte-identical payloads.
- Exit codes remain identical in all arms.
- Ended-run lane still produces the nudge (distinction from liveness predicate).
- Merged lane produces NO nudge (PR-202).
- Attempt-scoped lane produces nudge naming the attempt (PR-202).
- aw set executed delegation nudges in human mode and is suppressed under --agent (PR-201).
- Core begin and finalize functions write nothing to stdout or stderr (PR-201).
- driver_begin diagnostic integrity is preserved on refusal when a lane exists (PR-001).
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import runner_shared as RS
from tests import support


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n.aw/runs/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _ready_plan_text(
    *,
    plan_id: str = "abc123",
    set_name: str = "demo",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    return support.ready_plan_text(
        plan_id=plan_id, set_name=set_name, scope_paths=scope_paths
    )


def _completed_plan_text(
    *,
    plan_id: str = "abc123",
    set_name: str = "demo",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    t = _ready_plan_text(plan_id=plan_id, set_name=set_name, scope_paths=scope_paths)
    t = t.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    t = (
        t.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return t


def _write_plan(root: Path, text: str, name: str) -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


class LifecycleLaneNudgeTests(unittest.TestCase):
    """Behavioral test suite for the lifecycle lane nudge (m47znv)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        self.plan_id = "ndg001"
        self.plan_name = f"20261009-demo-01-{self.plan_id}-test-plan.ipd.md"
        self.plan_path = _write_plan(
            self.root,
            _completed_plan_text(plan_id=self.plan_id, set_name="demo"),
            self.plan_name,
        )
        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)
        (self.root / "agent_workflows" / "demo.py").write_text(
            "# demo\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_demo.py").write_text("# test\n", encoding="utf-8")
        _commit_all(self.root, "initial commit with plan")

        self.actor = "opencode model=test"
        self.scope_acks = [
            "--scope-ack",
            "agent_workflows/demo.py=ok",
            "--scope-ack",
            "tests/test_demo.py=ok",
        ]

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            try:
                rc = cli.main(argv)
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
        return rc, out_buf.getvalue(), err_buf.getvalue()

    def _create_lane(self, plan_id: str, attempt: int = 0) -> Path:
        lane_name = plan_id if attempt == 0 else f"{plan_id}_attempt{attempt}"
        lane_dir = self.root / ".aw" / "worktrees" / lane_name
        lane_dir.parent.mkdir(parents=True, exist_ok=True)
        branch = f"aw/lane/{lane_name}"
        subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(lane_dir), "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        (lane_dir / "work.txt").write_text(
            f"work in lane {lane_name}\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "add", "-A"],
            cwd=lane_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", f"work in lane {lane_name}"],
            cwd=lane_dir,
            check=True,
            capture_output=True,
        )
        return lane_dir

    def test_nudge_appears_in_main_when_lane_exists_begin(self) -> None:
        """Nudge appears on stderr when begin runs in main checkout and a lane exists."""
        self._create_lane(self.plan_id)
        rc, out, err = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc, 0)
        expected = f"aw: a lane for this plan exists ({self.plan_id}); finalizing there keeps main cleaner"
        self.assertIn(expected, err)
        # Nudge appears on stderr, NOT stdout
        self.assertNotIn("aw: a lane for this plan exists", out)
        # Emitted at most once
        self.assertEqual(err.count("aw: a lane for this plan exists"), 1)

    def test_nudge_appears_in_main_when_lane_exists_finalize(self) -> None:
        """Nudge appears on stderr when finalize runs in main checkout and a lane exists."""
        # First begin to create receipt
        rc_b, _, _ = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc_b, 0)
        self._create_lane(self.plan_id)

        rc, out, err = self._run_cli(
            [
                "ipd",
                "finalize",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
                "--message",
                "finished work",
                *self.scope_acks,
            ]
        )
        self.assertEqual(rc, 0)
        expected = f"aw: a lane for this plan exists ({self.plan_id}); finalizing there keeps main cleaner"
        self.assertIn(expected, err)
        self.assertNotIn("aw: a lane for this plan exists", out)
        self.assertEqual(err.count("aw: a lane for this plan exists"), 1)

    def test_nudge_absent_when_no_lane_exists(self) -> None:
        """Nudge does not appear for begin or finalize when no lane exists."""
        rc_b, _out_b, err_b = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc_b, 0)
        self.assertNotIn("aw: a lane for this plan exists", err_b)

        rc_f, _out_f, err_f = self._run_cli(
            [
                "ipd",
                "finalize",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
                "--message",
                "finished work",
                *self.scope_acks,
            ]
        )
        self.assertEqual(rc_f, 0)
        self.assertNotIn("aw: a lane for this plan exists", err_f)

    def test_nudge_absent_when_invoked_in_lane_worktree(self) -> None:
        """Nudge does not appear when the command is invoked with --dir pointing to the lane."""
        lane_dir = self._create_lane(self.plan_id)

        rc_b, _out_b, err_b = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(lane_dir),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc_b, 0)
        self.assertNotIn("aw: a lane for this plan exists", err_b)

        rc_f, _out_f, err_f = self._run_cli(
            [
                "ipd",
                "finalize",
                "--dir",
                str(lane_dir),
                self.plan_id,
                "--actor",
                self.actor,
                "--message",
                "finished work",
                *self.scope_acks,
            ]
        )
        self.assertEqual(rc_f, 0)
        self.assertNotIn("aw: a lane for this plan exists", err_f)

    def test_nudge_suppressed_in_agent_and_json_modes_with_byte_identical_payloads(
        self,
    ) -> None:
        """Under --agent and --json, nudge is suppressed on stderr and stdout is byte-identical."""
        # Control run without lane
        ctrl_rc_b_agent, ctrl_out_b_agent, _ctrl_err_b_agent = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
                "--agent",
            ]
        )
        self.assertEqual(ctrl_rc_b_agent, 0)

        # Reset receipt for fresh begin comparison
        receipt_file = (
            self.root
            / ".aw"
            / "state"
            / "ipd-lifecycle"
            / f"{self.plan_id}.receipt.json"
        )
        if receipt_file.exists():
            receipt_file.unlink()

        # Run with lane
        self._create_lane(self.plan_id)
        lane_rc_b_agent, lane_out_b_agent, lane_err_b_agent = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
                "--agent",
            ]
        )
        self.assertEqual(lane_rc_b_agent, ctrl_rc_b_agent)
        self.assertNotIn("aw: a lane for this plan exists", lane_err_b_agent)
        self.assertEqual(ctrl_out_b_agent, lane_out_b_agent)

        # Test --json mode for finalize
        ctrl_rc_f_json, ctrl_out_f_json, ctrl_err_f_json = self._run_cli(
            [
                "ipd",
                "finalize",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
                "--message",
                "fin",
                *self.scope_acks,
                "--json",
            ]
        )
        self.assertEqual(ctrl_rc_f_json, 0)
        self.assertNotIn("aw: a lane for this plan exists", ctrl_err_f_json)

        # Run with lane
        lane_rc_f_json, lane_out_f_json, lane_err_f_json = self._run_cli(
            [
                "ipd",
                "finalize",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
                "--message",
                "fin",
                *self.scope_acks,
                "--json",
            ]
        )
        self.assertEqual(lane_rc_f_json, 0)
        self.assertNotIn("aw: a lane for this plan exists", lane_err_f_json)
        self.assertEqual(ctrl_out_f_json, lane_out_f_json)

    def test_exit_code_invariance_across_arms(self) -> None:
        """Exit codes remain identical with and without lane, across success and failure."""
        # 1. Failure case: unknown selector
        rc_no_lane, _, _ = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                "nonexistent",
                "--actor",
                self.actor,
            ]
        )
        self._create_lane(self.plan_id)
        rc_with_lane, _, _ = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                "nonexistent",
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc_no_lane, rc_with_lane)

        # 2. Success case
        rc_success, _, _ = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc_success, 0)

    def test_ended_run_with_existing_lane_still_nudges(self) -> None:
        """CENTRAL DESIGN CASE: A lane whose run has ended (not held by live run) still nudges."""
        self._create_lane(self.plan_id)

        # Create a run directory with ended/completed status and NO live lock
        run_id = "run-20261009T020000Z-111222"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "queue": [{"id6": self.plan_id, "status": "completed"}],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        # Prove Order 01's holder predicate reports NOT HELD
        holder_res = RS.plan_holder(self.root, self.plan_id)
        self.assertNotEqual(holder_res.verdict, RS.PLAN_HOLDER_HELD)

        # Prove the nudge still fires!
        rc, _out, err = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("aw: a lane for this plan exists", err)

    def test_merged_lane_does_not_nudge(self) -> None:
        """A lane whose branch is merged into main produces NO nudge (PR-202)."""
        self._create_lane(self.plan_id)

        # Merge lane branch into main
        branch = f"aw/lane/{self.plan_id}"
        subprocess.run(
            ["git", "merge", "--no-ff", branch, "-m", "merged lane"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

        rc, _out, err = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("aw: a lane for this plan exists", err)

    def test_attempt_scoped_lane_nudges(self) -> None:
        """An attempt-scoped lane (e.g. aw/lane/<id6>_attempt2) produces nudge naming it."""
        self._create_lane(self.plan_id, attempt=2)

        rc, _out, err = self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self.assertEqual(rc, 0)
        expected = f"aw: a lane for this plan exists ({self.plan_id}_attempt2); finalizing there keeps main cleaner"
        self.assertIn(expected, err)

    def test_aw_set_executed_delegation_human_and_agent(self) -> None:
        """aw set executed in human mode nudges on stderr; under --agent it does not (PR-201)."""
        # Begin first
        self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                self.plan_id,
                "--actor",
                self.actor,
            ]
        )
        self._create_lane(self.plan_id)

        # Human mode
        rc, _out, err = self._run_cli(
            [
                "set",
                "executed",
                self.plan_id,
                "--dir",
                str(self.root),
                "--actor",
                self.actor,
                "--message",
                "done via set",
                *self.scope_acks,
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("aw: a lane for this plan exists", err)
        self.assertEqual(err.count("aw: a lane for this plan exists"), 1)

        # Plan 2 for agent mode
        p2 = "ndg002"
        _write_plan(
            self.root,
            _completed_plan_text(plan_id=p2, set_name="demo"),
            f"20261009-demo-02-{p2}-test-plan.ipd.md",
        )
        _commit_all(self.root, "commit plan 2")
        self._run_cli(
            [
                "ipd",
                "begin",
                "--dir",
                str(self.root),
                p2,
                "--actor",
                self.actor,
            ]
        )
        self._create_lane(p2)

        # Agent mode
        rc_agent, _out_agent, err_agent = self._run_cli(
            [
                "set",
                "executed",
                p2,
                "--dir",
                str(self.root),
                "--actor",
                self.actor,
                "--message",
                "done via set",
                *self.scope_acks,
                "--agent",
            ]
        )
        self.assertEqual(rc_agent, 0)
        self.assertNotIn("aw: a lane for this plan exists", err_agent)

    def test_core_begin_finalize_functions_write_nothing(self) -> None:
        """In-process calls directly to LC.begin and LC.finalize write nothing to stdout or stderr."""
        self._create_lane(self.plan_id)

        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            res_b = LC.begin(
                self.root,
                self.plan_path,
                self.actor,
                timestamp="2026-10-09T05:00:00Z",
            )
            self.assertEqual(res_b.exit_code, 0)
            res_f = LC.finalize(
                self.root,
                self.plan_path,
                self.actor,
                "msg",
                apply=False,
                scope_acks={
                    "agent_workflows/demo.py": "ok",
                    "tests/test_demo.py": "ok",
                },
            )
            self.assertEqual(res_f.exit_code, 0)

        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_driver_begin_diagnostic_integrity_on_refusal(self) -> None:
        """driver_begin refusal diagnostic strips the advisory and leads with real refusal (PR-001)."""
        self._create_lane(self.plan_id)

        # Unrelated refusal: pass invalid empty actor
        rc, diag = RS.driver_begin(self.root, self.plan_id, "")
        self.assertNotEqual(rc, 0)
        # Must not lead with the nudge
        self.assertFalse(diag.startswith("aw: a lane for this plan exists"))
        # Must not contain the nudge at all (stripped by nested_aw_message)
        self.assertNotIn("aw: a lane for this plan exists", diag)
        # Must contain the real refusal
        self.assertIn("requires a non-empty --actor", diag)

    def test_find_lane_candidate_fixtures(self) -> None:
        """find_lane_candidate_for_plan driven against the required fixtures."""
        # 1. Neither present
        cand1 = LC.find_lane_candidate_for_plan(self.root, "absent1")
        self.assertIsNone(cand1)

        # 2. Lane directory and branch present (unmerged)
        self._create_lane(self.plan_id)
        cand2 = LC.find_lane_candidate_for_plan(self.root, self.plan_id)
        self.assertEqual(cand2, self.plan_id)

        # 3. Lane branch present with NO directory (unmerged)
        p3 = "nbr001"
        subprocess.run(
            ["git", "branch", f"aw/lane/{p3}", "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        # Create a commit on that branch so it's not merged into HEAD
        subprocess.run(
            ["git", "update-ref", f"refs/heads/aw/lane/{p3}", "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        # If the branch has work ahead of HEAD, or is unmerged
        # Let's create an orphaned commit or commit ahead for aw/lane/nbr001
        subprocess.run(
            [
                "git",
                "branch",
                "-f",
                f"aw/lane/{p3}",
                f"refs/heads/aw/lane/{self.plan_id}",
            ],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        cand3 = LC.find_lane_candidate_for_plan(self.root, p3)
        self.assertEqual(cand3, p3)

        # 4. Unreadable/corrupt lane owner file
        owner_file = (
            self.root / ".aw" / "worktrees" / ".owners" / f"{self.plan_id}.json"
        )
        owner_file.parent.mkdir(parents=True, exist_ok=True)
        owner_file.write_text("corrupted json{{{", encoding="utf-8")
        cand4 = LC.find_lane_candidate_for_plan(self.root, self.plan_id)
        # Must not raise and returns candidate
        self.assertEqual(cand4, self.plan_id)

        # 5. Merged lane returns None
        branch = f"aw/lane/{self.plan_id}"
        subprocess.run(
            ["git", "merge", "--no-ff", branch, "-m", "merge lane"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        cand5 = LC.find_lane_candidate_for_plan(self.root, self.plan_id)
        self.assertIsNone(cand5)

        # 6. Distinction case: holder reports NOT HELD, helper reports lane
        p6 = "hld006"
        self._create_lane(p6)
        holder_res = RS.plan_holder(self.root, p6)
        self.assertNotEqual(holder_res.verdict, RS.PLAN_HOLDER_HELD)
        cand6 = LC.find_lane_candidate_for_plan(self.root, p6)
        self.assertEqual(cand6, p6)
