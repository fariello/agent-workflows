"""Behavioral tests for the plan-scoped live-holder lifecycle gate (lifegate e25iy9).

Replaces the deleted location-guess and per-run driver token gate from executed plan u27oh3.
Pins the positive live-holder check inside begin, finalize, and orchestrator retirement,
covering D4's entry point matrix, the two regression cases (feat-partition human worktrees
and dead-runner lane recovery), the E-05 environment fence, UNDETERMINABLE verdicts,
and the deliberate --take-over override.
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli, ipd_lifecycle as LC, oc_runipd, runner_shared as RS
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


class LifecycleHolderGateMatrixTests(unittest.TestCase):
    """Tests the D4 entry-point matrix against a plan held by a live run."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        self.plan_id = "hld001"
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

        self.holder_run_id = "run-20261009T010000Z-999001"
        self.run_dir = self.root / ".aw" / "runs" / self.holder_run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": self.holder_run_id,
            "queue": [{"id6": self.plan_id, "status": "running"}],
        }
        (self.run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        self.parser = cli._build_parser()
        self.actor = "opencode model=test"

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

    def test_entry_01_aw_ipd_begin_cli(self) -> None:
        """Entry 1: aw ipd begin refuses when held; proceeds with --run-id."""
        with RS.run_lock(self.run_dir):
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
            combined = out + err
            self.assertNotEqual(rc, 0)
            self.assertIn(self.holder_run_id, combined)
            self.assertIn("is held by live run", combined)
            self.assertIn("--take-over", combined)

            # Proceeds when caller declares matching --run-id
            rc_ok, out_ok, err_ok = self._run_cli(
                [
                    "ipd",
                    "begin",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(
                rc_ok,
                0,
                f"Expected 0 with matching run-id. Output:\n{out_ok}\n{err_ok}",
            )

    def test_entry_02_aw_ipd_finalize_cli(self) -> None:
        """Entry 2: aw ipd finalize refuses when held; proceeds with --run-id."""
        with RS.run_lock(self.run_dir):
            # Create receipt first with holder run id so finalize can evaluate receipt
            rc_b, _, _ = self._run_cli(
                [
                    "ipd",
                    "begin",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(rc_b, 0)

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
                    "done",
                ]
            )
            combined = out + err
            self.assertNotEqual(rc, 0)
            self.assertIn(self.holder_run_id, combined)
            self.assertIn("is held by live run", combined)
            self.assertIn("--take-over", combined)

            # Commit changes to declared paths so finalize scope reconciliation succeeds
            (self.root / "agent_workflows" / "demo.py").write_text(
                "# demo modified\n", encoding="utf-8"
            )
            (self.root / "tests" / "test_demo.py").write_text(
                "# test modified\n", encoding="utf-8"
            )
            _commit_all(self.root, "commit work")

            # Proceeds when caller passes matching --run-id
            rc_ok, out_ok, err_ok = self._run_cli(
                [
                    "ipd",
                    "finalize",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--message",
                    "done",
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(
                rc_ok,
                0,
                f"Expected 0 with matching run-id. Output:\n{out_ok}\n{err_ok}",
            )

    def test_entry_03_aw_set_executed_cli(self) -> None:
        """Entry 3: aw set executed refuses when held; proceeds with --run-id."""
        with RS.run_lock(self.run_dir):
            rc_b, _, _ = self._run_cli(
                [
                    "ipd",
                    "begin",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(rc_b, 0)

            rc, out, err = self._run_cli(
                [
                    "set",
                    "executed",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--by-human",
                    "--message",
                    "human completed work",
                ]
            )
            combined = out + err
            self.assertNotEqual(rc, 0)
            self.assertIn(self.holder_run_id, combined)
            self.assertIn("is held by live run", combined)

            (self.root / "agent_workflows" / "demo.py").write_text(
                "# demo modified\n", encoding="utf-8"
            )
            (self.root / "tests" / "test_demo.py").write_text(
                "# test modified\n", encoding="utf-8"
            )
            _commit_all(self.root, "commit work")

            rc_ok, out_ok, err_ok = self._run_cli(
                [
                    "set",
                    "executed",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--by-human",
                    "--message",
                    "human completed work",
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(
                rc_ok,
                0,
                f"Expected 0 with matching run-id. Output:\n{out_ok}\n{err_ok}",
            )

    def test_entry_04_aw_ipd_set_executed_cli(self) -> None:
        """Entry 4: aw ipd set executed refuses when held; proceeds with --run-id."""
        with RS.run_lock(self.run_dir):
            rc_b, _, _ = self._run_cli(
                [
                    "ipd",
                    "begin",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(rc_b, 0)

            rc, out, err = self._run_cli(
                [
                    "ipd",
                    "set",
                    "executed",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--by-human",
                    "--message",
                    "human completed work",
                ]
            )
            combined = out + err
            self.assertNotEqual(rc, 0)
            self.assertIn(self.holder_run_id, combined)
            self.assertIn("is held by live run", combined)

            (self.root / "agent_workflows" / "demo.py").write_text(
                "# demo modified\n", encoding="utf-8"
            )
            (self.root / "tests" / "test_demo.py").write_text(
                "# test modified\n", encoding="utf-8"
            )
            _commit_all(self.root, "commit work")

            rc_ok, out_ok, err_ok = self._run_cli(
                [
                    "ipd",
                    "set",
                    "executed",
                    "--dir",
                    str(self.root),
                    self.plan_id,
                    "--actor",
                    self.actor,
                    "--by-human",
                    "--message",
                    "human completed work",
                    "--run-id",
                    self.holder_run_id,
                ]
            )
            self.assertEqual(
                rc_ok,
                0,
                f"Expected 0 with matching run-id. Output:\n{out_ok}\n{err_ok}",
            )

    def test_entry_05_retire_orchestrator_in_process(self) -> None:
        """Entry 5: retire_orchestrator refuses when held; proceeds with matching run_id."""
        orch_id = "orch01"
        orch_name = f"20261009-demo-00-{orch_id}-orchestrator.ipd.md"
        orch_text = f"""# IPD: Demo Orchestrator
- Id: {orch_id}
- Set: demo
- Order: 0
- Kind: orchestrator
- Status: approved
- Author: human
- Date: 2026-10-09
- Readiness: go
- Work-Kind: feature
- Priority: medium

## Child IPDs, sequence, and dependencies
| Order | Id | Depends on | Status | Description |
|---|---|---|---|---|
| 01 | {self.plan_id} | none | executed | child work |

## Detailed Implementation Checklist (TODO)
- [ ] E-01 CONFIRM {self.plan_id} REACHED executed
  - Depends on: none
"""
        executed_dir = self.root / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)
        child_text = _completed_plan_text(
            plan_id=self.plan_id, set_name="demo"
        ).replace("Status: approved", "Status: executed")
        (executed_dir / self.plan_name).write_text(child_text, encoding="utf-8")
        if self.plan_path.exists():
            self.plan_path.unlink()

        orch_path = _write_plan(self.root, orch_text, orch_name)
        _commit_all(self.root, "add orchestrator and mark child executed")

        state = {
            "schema_version": 1,
            "run_id": self.holder_run_id,
            "queue": [
                {"id6": self.plan_id, "status": "running"},
                {"id6": orch_id, "status": "running"},
            ],
        }
        (self.run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        with RS.run_lock(self.run_dir):
            # 1. Foreign caller without run_id
            res_refused = LC.retire_orchestrator(
                self.root,
                orch_path,
                orch_id,
                setid="demo",
                run_id="run-different-111",
                apply=False,
                env={},
            )
            self.assertEqual(res_refused.exit_code, LC.EXIT_CANNOT_RUN)
            self.assertIn(LC.ROLLUP_REFUSED_PLAN_HELD, res_refused.findings)
            self.assertIn(self.holder_run_id, res_refused.message)

            # 2. Matching run_id passes gate
            res_ok = LC.retire_orchestrator(
                self.root,
                orch_path,
                orch_id,
                setid="demo",
                run_id=self.holder_run_id,
                apply=False,
                env={},
            )
            self.assertEqual(res_ok.exit_code, LC.EXIT_OK)

    def test_entry_06_runner_driver_begin(self) -> None:
        """Entry 6: runner_shared.driver_begin refuses when held; proceeds with run_id."""
        with RS.run_lock(self.run_dir):
            rc, msg = RS.driver_begin(self.root, self.plan_id, self.actor)
            self.assertNotEqual(rc, 0)
            self.assertIn(self.holder_run_id, msg)
            self.assertIn("is held by live run", msg)

            rc_ok, msg_ok = RS.driver_begin(
                self.root, self.plan_id, self.actor, run_id=self.holder_run_id
            )
            self.assertEqual(rc_ok, 0, f"driver_begin failed with run_id: {msg_ok}")

    def test_entry_07_runner_driver_finalize(self) -> None:
        """Entry 7: oc_runipd.driver_finalize refuses when held; proceeds with run_id."""
        with RS.run_lock(self.run_dir):
            rc_b, _ = RS.driver_begin(
                self.root, self.plan_id, self.actor, run_id=self.holder_run_id
            )
            self.assertEqual(rc_b, 0)

            rc, msg = oc_runipd.driver_finalize(
                self.root, self.plan_path, self.plan_id, self.actor, "finished"
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(self.holder_run_id, msg)
            self.assertIn("is held by live run", msg)

            (self.root / "agent_workflows" / "demo.py").write_text(
                "# demo modified\n", encoding="utf-8"
            )
            (self.root / "tests" / "test_demo.py").write_text(
                "# test modified\n", encoding="utf-8"
            )
            _commit_all(self.root, "commit work")

            rc_ok, msg_ok = oc_runipd.driver_finalize(
                self.root,
                self.plan_path,
                self.plan_id,
                self.actor,
                "finished",
                run_id=self.holder_run_id,
            )
            self.assertEqual(rc_ok, 0, f"driver_finalize failed with run_id: {msg_ok}")


class RegressionAndFenceTests(unittest.TestCase):
    """Tests the two regression cases, E-05 environment fence, UNDETERMINABLE, and --take-over."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        self.plan_id = "reg001"
        self.plan_name = f"20261009-demo-01-{self.plan_id}-regression-test.ipd.md"
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

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_regression_human_worktree_under_dot_aw_worktrees_succeeds(self) -> None:
        """Regression 1: A human worktree under .aw/worktrees/feat-partition with no live run succeeds."""
        wt_dir = self.root / ".aw" / "worktrees" / "feat-partition"
        wt_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", "-b", "feat-partition", str(wt_dir)],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        wt_plan = wt_dir / ".aw" / "records" / "plans" / "pending" / self.plan_name

        # begin succeeds in human worktree
        res_b = LC.begin(
            wt_dir,
            wt_plan,
            actor=self.actor,
            timestamp="2026-10-09T01:00:00Z",
            env={},
        )
        self.assertEqual(res_b.exit_code, LC.EXIT_OK, res_b.message)

        # Commit work in worktree so finalize scope reconciliation succeeds
        (wt_dir / "agent_workflows" / "demo.py").write_text(
            "# demo wt\n", encoding="utf-8"
        )
        (wt_dir / "tests" / "test_demo.py").write_text("# test wt\n", encoding="utf-8")
        _commit_all(wt_dir, "work in wt")

        # finalize succeeds in human worktree
        res_f = LC.finalize(
            wt_dir,
            wt_plan,
            actor=self.actor,
            message="human work completed in worktree",
            apply=False,
            env={},
        )
        self.assertEqual(res_f.exit_code, LC.EXIT_OK, res_f.message)

    def test_regression_dead_runner_lane_succeeds(self) -> None:
        """Regression 2: A lane whose runner died (dead PID / released lock) succeeds."""
        lane_dir = self.root / ".aw" / "worktrees" / "abc123lane"
        lane_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", "-b", "aw/lane/abc123lane", str(lane_dir)],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        lane_plan = lane_dir / ".aw" / "records" / "plans" / "pending" / self.plan_name

        # Create run dir with dead runner (no lock held)
        dead_run_id = "run-20261009T000000Z-000001"
        run_dir = self.root / ".aw" / "runs" / dead_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": dead_run_id,
            "queue": [{"id6": self.plan_id, "status": "running"}],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        # No driver.lock exists or lock PID is dead.
        res_b = LC.begin(
            lane_dir,
            lane_plan,
            actor=self.actor,
            timestamp="2026-10-09T01:00:00Z",
            env={},
        )
        self.assertEqual(res_b.exit_code, LC.EXIT_OK, res_b.message)

    def test_e05_fence_worker_role_with_aw_run_id_refused(self) -> None:
        """Fence (E-05): A worker-labelled caller with AW_RUN_ID set is STILL refused with AW-LIFECYCLE-ROLE-001."""
        worker_env = {
            LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER,
            "AW_RUN_ID": "run-20261009T010000Z-999001",
        }
        res_b = LC.begin(
            self.root,
            self.plan_path,
            actor=self.actor,
            timestamp="2026-10-09T01:00:00Z",
            env=worker_env,
        )
        self.assertEqual(res_b.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("AW-LIFECYCLE-ROLE-001", res_b.message)
        self.assertIn(LC.ROLLUP_REFUSED_WORKER_ROLE, res_b.findings)

        res_f = LC.finalize(
            self.root,
            self.plan_path,
            actor=self.actor,
            message="attempt by worker",
            apply=False,
            env=worker_env,
        )
        self.assertEqual(res_f.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("AW-LIFECYCLE-ROLE-001", res_f.message)
        self.assertIn(LC.ROLLUP_REFUSED_WORKER_ROLE, res_f.findings)

    def test_undeterminable_foreign_machine_refuses_naming_machine(self) -> None:
        """UNDETERMINABLE verdict (foreign machine) refuses and names machine in diagnostic."""
        run_id = "run-20261009T010000Z-999002"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "queue": [{"id6": self.plan_id, "status": "running"}],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        foreign_host = "remote-node-77"
        (run_dir / "driver.lock").write_text(
            f"pid=999 host={foreign_host} started=2026-10-09T01:00:00Z\n",
            encoding="utf-8",
        )

        res_b = LC.begin(
            self.root,
            self.plan_path,
            actor=self.actor,
            timestamp="2026-10-09T01:00:00Z",
            env={},
        )
        self.assertEqual(res_b.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn(LC.ROLLUP_REFUSED_PLAN_HELD, res_b.findings)
        self.assertIn(foreign_host, res_b.message)
        self.assertIn("--take-over", res_b.message)

        # Finalize also refuses
        res_f = LC.finalize(
            self.root,
            self.plan_path,
            actor=self.actor,
            message="finishing",
            apply=False,
            env={},
        )
        self.assertEqual(res_f.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn(LC.ROLLUP_REFUSED_PLAN_HELD, res_f.findings)
        self.assertIn(foreign_host, res_f.message)

    def test_take_over_override_proceeds_and_records_history(self) -> None:
        """--take-over with non-empty reason overrides live holder and records reason in workflow history."""
        run_id = "run-20261009T010000Z-999003"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "queue": [{"id6": self.plan_id, "status": "running"}],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        with RS.run_lock(run_dir):
            # 1. Empty reason is refused
            res_empty_b = LC.begin(
                self.root,
                self.plan_path,
                actor=self.actor,
                timestamp="2026-10-09T01:00:00Z",
                take_over="   ",
                env={},
            )
            self.assertEqual(res_empty_b.exit_code, LC.EXIT_CANNOT_RUN)
            self.assertIn("non-empty reason", res_empty_b.message)

            res_empty_f = LC.finalize(
                self.root,
                self.plan_path,
                actor=self.actor,
                message="done",
                take_over="",
                apply=False,
                env={},
            )
            self.assertEqual(res_empty_f.exit_code, LC.EXIT_CANNOT_RUN)
            self.assertIn("non-empty reason", res_empty_f.message)

            # 2. Valid reason proceeds at begin and records in receipt
            reason_text = "recovering abandoned work after node reboot"
            res_b = LC.begin(
                self.root,
                self.plan_path,
                actor=self.actor,
                timestamp="2026-10-09T01:00:00Z",
                take_over=reason_text,
                env={},
            )
            self.assertEqual(res_b.exit_code, LC.EXIT_OK, res_b.message)
            self.assertIsNotNone(res_b.receipt)
            assert res_b.receipt is not None
            self.assertIn("take_over", res_b.receipt)
            self.assertEqual(res_b.receipt["take_over"]["reason"], reason_text)
            self.assertEqual(res_b.receipt["take_over"]["overridden_run_id"], run_id)

            # Commit work so finalize scope reconciliation succeeds
            (self.root / "agent_workflows" / "demo.py").write_text(
                "# demo override\n", encoding="utf-8"
            )
            (self.root / "tests" / "test_demo.py").write_text(
                "# test override\n", encoding="utf-8"
            )
            _commit_all(self.root, "work committed")

            # 3. Valid reason proceeds at finalize apply=True and writes history
            res_f = LC.finalize(
                self.root,
                self.plan_path,
                actor=self.actor,
                message="completing overridden plan",
                take_over=reason_text,
                apply=True,
                env={},
            )
            self.assertEqual(res_f.exit_code, LC.EXIT_OK, res_f.message)

            # Verify moved plan has history line
            executed_p = (
                self.root / ".aw" / "records" / "plans" / "executed" / self.plan_name
            )
            self.assertTrue(executed_p.is_file())
            content = executed_p.read_text(encoding="utf-8")
            self.assertIn(
                f"live holder run '{run_id}' overridden: {reason_text}", content
            )

    def test_absent_runs_directory_is_not_held(self) -> None:
        """PR-103: A repository with NO .aw/records/runs or .aw/runs tree succeeds without refusal."""
        with tempfile.TemporaryDirectory() as fresh_repo_dir:
            repo_root = Path(fresh_repo_dir)
            _init_git(repo_root)
            p_text = _completed_plan_text(plan_id="fresh1", set_name="demo")
            plan_file = _write_plan(
                repo_root, p_text, "20261009-demo-01-fresh1-fresh.ipd.md"
            )
            (repo_root / "agent_workflows").mkdir(parents=True, exist_ok=True)
            (repo_root / "tests").mkdir(parents=True, exist_ok=True)
            (repo_root / "agent_workflows" / "demo.py").write_text(
                "# d\n", encoding="utf-8"
            )
            (repo_root / "tests" / "test_demo.py").write_text("# t\n", encoding="utf-8")
            _commit_all(repo_root, "initial commit")

            # Assert .aw/runs does not exist
            self.assertFalse((repo_root / ".aw" / "runs").exists())
            self.assertFalse((repo_root / ".aw" / "records" / "runs").exists())

            # begin and finalize succeed
            b_res = LC.begin(
                repo_root,
                plan_file,
                actor=self.actor,
                timestamp="2026-10-09T01:00:00Z",
                env={},
            )
            self.assertEqual(b_res.exit_code, LC.EXIT_OK, b_res.message)

            (repo_root / "agent_workflows" / "demo.py").write_text(
                "# d2\n", encoding="utf-8"
            )
            (repo_root / "tests" / "test_demo.py").write_text(
                "# t2\n", encoding="utf-8"
            )
            _commit_all(repo_root, "work")

            f_res = LC.finalize(
                repo_root,
                plan_file,
                actor=self.actor,
                message="finalized in fresh repo",
                apply=False,
                env={},
            )
            self.assertEqual(f_res.exit_code, LC.EXIT_OK, f_res.message)

    def test_no_self_finalize_delegated_agent_turn_succeeds(self) -> None:
        """PR-104 / E-10: Under --no-self-finalize, agent is not labelled worker, gets run_id, and succeeds."""
        run_id = "run-20261009T010000Z-999005"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "queue": [{"id6": self.plan_id, "status": "running"}],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        # 1. Notice renders instructions with explicit --run-id
        notice_delegated = LC.runner_owns_lifecycle_notice(False, run_id=run_id)
        self.assertIn(f"--run-id {run_id}", notice_delegated)
        self.assertIn(
            "This run delegates the lifecycle transition to you", notice_delegated
        )

        # 2. Delegated agent (no worker label) passing matching run_id succeeds past live holder
        with RS.run_lock(run_dir):
            res_b = LC.begin(
                self.root,
                self.plan_path,
                actor=self.actor,
                timestamp="2026-10-09T01:00:00Z",
                run_id=run_id,
                env={},  # No worker label
            )
            self.assertEqual(res_b.exit_code, LC.EXIT_OK, res_b.message)

            (self.root / "agent_workflows" / "demo.py").write_text(
                "# demo delegated\n", encoding="utf-8"
            )
            (self.root / "tests" / "test_demo.py").write_text(
                "# test delegated\n", encoding="utf-8"
            )
            _commit_all(self.root, "delegated work")

            res_f = LC.finalize(
                self.root,
                self.plan_path,
                actor=self.actor,
                message="agent self-finalized",
                run_id=run_id,
                apply=False,
                env={},
            )
            self.assertEqual(res_f.exit_code, LC.EXIT_OK, res_f.message)

        # 3. Control: default self_finalize=True sets worker label, which refuses
        notice_default = LC.runner_owns_lifecycle_notice(True, run_id=run_id)
        self.assertIn("The runner performs `aw ipd begin`", notice_default)
        worker_env = {LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER}
        res_ctrl_b = LC.begin(
            self.root,
            self.plan_path,
            actor=self.actor,
            timestamp="2026-10-09T01:00:00Z",
            run_id=run_id,
            env=worker_env,
        )
        self.assertEqual(res_ctrl_b.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("AW-LIFECYCLE-ROLE-001", res_ctrl_b.message)
