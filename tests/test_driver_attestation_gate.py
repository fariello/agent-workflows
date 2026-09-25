"""Tests for the positive driver attestation requirement on the terminal finalize/retire.

IPD roleattest-01 (`u27oh3`). Inside a lane worktree, `ipd_lifecycle.finalize` and
`ipd_lifecycle.retire_orchestrator` refuse unless a per-run driver attestation is presented
and verifies. Outside a lane (main checkout), human workflows are unaffected.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import oc_runipd
from agent_workflows import runner_shared as _rs
from tests import support


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


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


class LaneWorktreeActiveTests(unittest.TestCase):
    """Unit tests for `ipd_lifecycle.lane_worktree_active` (E-01/V-01)."""

    def setUp(self) -> None:
        LC.clear_checkout_control_root_cache()
        self.addCleanup(LC.clear_checkout_control_root_cache)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        _commit_all(self.root, "initial commit")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_main_checkout_returns_false(self) -> None:
        self.assertFalse(LC.lane_worktree_active(self.root))

    def test_lane_worktree_in_dot_aw_worktrees_returns_true(self) -> None:
        lane_dir = self.root / ".aw" / "worktrees" / "abc123"
        lane_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", "-b", "aw/lane/abc123", str(lane_dir)],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        self.assertTrue(LC.lane_worktree_active(lane_dir))

    def test_offtree_lane_branch_returns_true(self) -> None:
        offtree_dir = self.root.parent / f"{self.root.name}-offtree-lane"
        subprocess.run(
            ["git", "worktree", "add", "-b", "aw/lane/xyz789", str(offtree_dir)],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        try:
            self.assertTrue(LC.lane_worktree_active(offtree_dir))
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(offtree_dir)],
                cwd=self.root,
                check=False,
                capture_output=True,
            )

    def test_non_git_dir_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as non_git:
            self.assertFalse(LC.lane_worktree_active(Path(non_git)))


class DriverAttestationPrimitivesTests(unittest.TestCase):
    """Unit tests for minting and verifying driver attestations (E-02/V-02)."""

    def setUp(self) -> None:
        LC.clear_checkout_control_root_cache()
        self.addCleanup(LC.clear_checkout_control_root_cache)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        _commit_all(self.root, "initial commit")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_mint_and_verify_happy_path(self) -> None:
        run_id = "run-20260925T120000Z-123456"
        run_dir = self.root / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        attestation = LC.mint_driver_attestation(run_dir)
        self.assertTrue(attestation.startswith(f"{run_id}:"))
        token = attestation.split(":", 1)[1]
        self.assertEqual(len(token), 64)

        token_file = run_dir / LC.DRIVER_ATTEST_FILENAME
        self.assertTrue(token_file.is_file())
        file_mode = stat.S_IMODE(token_file.stat().st_mode)
        self.assertEqual(
            file_mode, 0o600, f"Expected 0600 permissions, got {oct(file_mode)}"
        )

        ok, msg = LC.verify_driver_attestation(self.root, attestation)
        self.assertTrue(ok, f"Verification failed: {msg}")

    def test_verify_wrong_token_refused(self) -> None:
        run_id = "run-test-wrong-token"
        run_dir = self.root / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        LC.mint_driver_attestation(run_dir)

        bad_attestation = (
            f"{run_id}:0000000000000000000000000000000000000000000000000000000000000000"
        )
        ok, msg = LC.verify_driver_attestation(self.root, bad_attestation)
        self.assertFalse(ok)
        self.assertIn("mismatch", msg.lower())

    def test_verify_unknown_run_id_refused(self) -> None:
        ok, msg = LC.verify_driver_attestation(self.root, "run-unknown-xyz:token123")
        self.assertFalse(ok)
        self.assertIn("not found", msg.lower())

    def test_verify_traversal_run_id_refused(self) -> None:
        ok, msg = LC.verify_driver_attestation(self.root, "../dummy:token123")
        self.assertFalse(ok)
        self.assertIn("invalid", msg.lower())

    def test_verify_malformed_value_refused(self) -> None:
        for malformed in [None, "", "notoken", ":tokenonly", "runidonly:"]:
            ok, msg = LC.verify_driver_attestation(self.root, malformed)
            self.assertFalse(ok)
            self.assertIn("malformed", msg.lower())

    def test_lane_and_main_resolve_same_runs_dir(self) -> None:
        lane_dir = self.root / ".aw" / "worktrees" / "abc123"
        lane_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", "-b", "aw/lane/abc123", str(lane_dir)],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

        main_runs_dir = _rs.state_root(self.root).resolve()
        lane_control_parent = LC.checkout_control_root(lane_dir).parent
        lane_derived_runs_dir = _rs.state_root(lane_control_parent).resolve()

        print(f"Main checkout runs dir: {main_runs_dir}")
        print(f"Lane derived runs dir:  {lane_derived_runs_dir}")
        self.assertEqual(main_runs_dir, lane_derived_runs_dir)


class IncidentShapeAndGateRefusalTests(unittest.TestCase):
    """End-to-end regression tests for the terminal finalize gate in lane worktrees (E-03/E-07)."""

    def setUp(self) -> None:
        LC.clear_checkout_control_root_cache()
        self.addCleanup(LC.clear_checkout_control_root_cache)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)
        (self.root / "agent_workflows" / "demo.py").write_text(
            "# demo\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_demo.py").write_text("# test\n", encoding="utf-8")

        self.plan_id = "u27tst"
        self.plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=self.plan_id, set_name="roleattest"),
            f"20260925-roleattest-01-{self.plan_id}-test.ipd.md",
        )
        _commit_all(self.root, "initial plan and code")

        # Begin receipt created by coordinator
        begin_res = LC.begin(
            self.root, self.plan, "agent/test", timestamp=_rs.utc_now()
        )
        self.assertEqual(begin_res.exit_code, LC.EXIT_OK, begin_res.message)

        # Create the lane worktree
        self.lane_dir = self.root / ".aw" / "worktrees" / self.plan_id
        self.lane_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "-b",
                f"aw/lane/{self.plan_id}",
                str(self.lane_dir),
            ],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(support.REPO_ROOT)
        env.pop(LC.EXECUTION_ROLE_ENV, None)
        env.pop(LC.DRIVER_ATTEST_ENV, None)
        if extra:
            env.update(extra)
        return env

    def test_incident_shape_stripping_execution_role_is_refused(self) -> None:
        """Case 1: env -u AW_EXECUTION_ROLE finalize from lane is refused without driver token."""
        main_head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        lane_head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane_dir, text=True
        ).strip()

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "ipd",
                "finalize",
                self.plan_id,
                "--actor",
                "agent/lane",
                "--message",
                "lane turn done",
                "--apply",
            ],
            cwd=self.lane_dir,
            env=self._env(),
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.returncode, LC.EXIT_CANNOT_RUN)
        combined_output = proc.stdout + proc.stderr
        self.assertTrue(
            "no-driver-attestation" in combined_output
            or "Unsetting AW_EXECUTION_ROLE does NOT grant driver authority"
            in combined_output
        )

        # Plan still in pending/
        self.assertTrue(
            (
                self.root / ".aw" / "records" / "plans" / "pending" / self.plan.name
            ).is_file()
        )
        self.assertFalse(
            (
                self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
            ).is_file()
        )

        # Main and lane HEADs unchanged
        main_head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        lane_head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.lane_dir, text=True
        ).strip()
        self.assertEqual(main_head_before, main_head_after)
        self.assertEqual(lane_head_before, lane_head_after)

        # Receipt still present
        receipt = LC.read_receipt(self.root, self.plan_id)
        self.assertIsNotNone(receipt)

    def test_aw_set_executed_from_lane_is_refused(self) -> None:
        """Case 2: aw set executed <id6> route from lane is refused without driver token."""
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "set",
                "executed",
                self.plan_id,
                "--actor",
                "agent/lane",
                "--message",
                "set executed attempt",
                "--scope-ack",
                "agent_workflows/demo.py",
                "--scope-ack",
                "tests/test_demo.py",
            ],
            cwd=self.lane_dir,
            env=self._env(),
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(proc.returncode, 0)
        combined_output = proc.stdout + proc.stderr
        self.assertTrue(
            "no-driver-attestation" in combined_output
            or "Unsetting AW_EXECUTION_ROLE does NOT grant driver authority"
            in combined_output
        )
        self.assertTrue(
            (
                self.root / ".aw" / "records" / "plans" / "pending" / self.plan.name
            ).is_file()
        )

    def test_retire_orchestrator_from_lane_is_refused(self) -> None:
        """Case 6: retire_orchestrator from lane root refuses with ROLLUP_REFUSED_NO_DRIVER_ATTESTATION."""
        res = LC.retire_orchestrator(
            self.lane_dir,
            self.plan,
            "agent/test",
            setid="roleattest",
            env={},
        )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertEqual(res.findings, (LC.ROLLUP_REFUSED_NO_DRIVER_ATTESTATION,))
        self.assertIn(
            "Unsetting AW_EXECUTION_ROLE does NOT grant driver authority", res.message
        )

    def test_driver_with_token_succeeds_from_lane(self) -> None:
        """Case 4: Finalize from lane with valid AW_DRIVER_ATTEST succeeds."""
        run_id = "run-20260925T120000Z-999999"
        run_dir = self.root / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        attestation = LC.mint_driver_attestation(run_dir)

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "ipd",
                "finalize",
                self.plan_id,
                "--actor",
                "runner/driver",
                "--message",
                "driver turn finalized",
                "--scope-ack",
                "agent_workflows/demo.py",
                "--scope-ack",
                "tests/test_demo.py",
                "--apply",
            ],
            cwd=self.lane_dir,
            env=self._env({LC.DRIVER_ATTEST_ENV: attestation}),
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        self.assertFalse(
            (
                self.lane_dir / ".aw" / "records" / "plans" / "pending" / self.plan.name
            ).is_file()
        )
        self.assertTrue(
            (
                self.lane_dir
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / self.plan.name
            ).is_file()
        )

    def test_main_checkout_human_succeeds_without_token(self) -> None:
        """Case 5: Finalize from main checkout with neither variable set succeeds."""
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "ipd",
                "finalize",
                self.plan_id,
                "--actor",
                "human/maintainer",
                "--message",
                "human finalize from main checkout",
                "--scope-ack",
                "agent_workflows/demo.py",
                "--scope-ack",
                "tests/test_demo.py",
                "--apply",
            ],
            cwd=self.root,
            env=self._env(),
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        self.assertFalse(
            (
                self.root / ".aw" / "records" / "plans" / "pending" / self.plan.name
            ).is_file()
        )
        self.assertTrue(
            (
                self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
            ).is_file()
        )


class ChildEnvAndDriverFinalizeTests(unittest.TestCase):
    """Tests for child env scrubbing and subprocess carriage (E-05/E-06)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_child_env_scrubs_driver_attest_for_both_hosts(self) -> None:
        """Case 7: Child env built by run_opencode / run_agy_turn omits AW_DRIVER_ATTEST."""
        run_dir = self.root / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        prompt_path = self.root / "prompt.md"
        prompt_path.write_text("do something", encoding="utf-8")
        plan_path = self.root / "plan.ipd.md"
        plan_path.write_text("plan", encoding="utf-8")
        state = {
            "run_id": "run-test",
            "options": {
                "opencode": "opencode",
                "agy_executable": "agy",
                "stall_timeout": 10.0,
                "timeout": 10.0,
            },
            "repo": str(self.root),
            "queue": [],
        }
        item = {"position": 1, "id6": "abc123", "setid": "demo"}

        with mock.patch.dict(os.environ, {LC.DRIVER_ATTEST_ENV: "run-test:mocktoken"}):
            # Test oc_runipd child env construction
            with mock.patch(
                "agent_workflows.oc_runipd.pinned_child_env",
                return_value={
                    LC.DRIVER_ATTEST_ENV: "run-test:mocktoken",
                    "PATH": "/bin",
                },
            ):
                with mock.patch(
                    "agent_workflows.oc_runipd.observe_opencode_policy",
                    return_value="observed",
                ):
                    with mock.patch(
                        "agent_workflows.lane_containment.record_host_posture"
                    ):
                        with mock.patch("subprocess.Popen") as mock_popen:
                            mock_popen.return_value.poll.return_value = 0
                            mock_popen.return_value.returncode = 0
                            mock_popen.return_value.stdout = io_empty = mock.MagicMock()
                            mock_popen.return_value.stderr = mock.MagicMock()
                            io_empty.readline.return_value = ""

                            oc_runipd.run_opencode(
                                state=state,
                                run_dir=run_dir,
                                item=item,
                                plan_path=plan_path,
                                prompt_path=prompt_path,
                                attempt_no=1,
                                work_dir=str(self.root / "worktree"),
                            )

                            self.assertTrue(mock_popen.called)
                            call_kwargs = mock_popen.call_args[1]
                            child_env = call_kwargs.get("env", {})
                            self.assertNotIn(LC.DRIVER_ATTEST_ENV, child_env)

            # Test agy_runipd child env construction
            with mock.patch(
                "agent_workflows.agy_runipd.pinned_child_env",
                return_value={
                    LC.DRIVER_ATTEST_ENV: "run-test:mocktoken",
                    "PATH": "/bin",
                },
            ):
                with mock.patch("agent_workflows.lane_containment.record_host_posture"):
                    with mock.patch("subprocess.Popen") as mock_popen_agy:
                        mock_popen_agy.return_value.poll.return_value = 0
                        mock_popen_agy.return_value.returncode = 0
                        mock_popen_agy.return_value.stdout = mock.MagicMock()
                        mock_popen_agy.return_value.stderr = mock.MagicMock()

                        agy_runipd.run_agy_turn(
                            state=state,
                            run_dir=run_dir,
                            item=item,
                            prompt_path=prompt_path,
                            attempt_no=1,
                            session_id=None,
                            use_continue=False,
                            work_dir=str(self.root / "worktree"),
                        )

                        self.assertTrue(mock_popen_agy.called)
                        call_kwargs_agy = mock_popen_agy.call_args[1]
                        child_env_agy = call_kwargs_agy.get("env", {})
                        self.assertNotIn(LC.DRIVER_ATTEST_ENV, child_env_agy)

    def test_driver_finalize_places_attestation_in_subprocess_env_not_argv(
        self,
    ) -> None:
        """Case 8: driver_finalize passes attestation via subprocess env and not argv."""
        captured_proc: list[dict] = []

        def fake_run(
            cmd, cwd=None, env=None, text=True, stdin=None, stdout=None, stderr=None
        ):
            captured_proc.append({"cmd": cmd, "cwd": cwd, "env": env})
            m = mock.MagicMock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m

        with mock.patch(
            "agent_workflows.runner_shared.subprocess.run", side_effect=fake_run
        ):
            with mock.patch(
                "agent_workflows.runner_shared.compute_scope_reconciliation",
                return_value=({}, {}),
            ):
                _rs.driver_finalize(
                    Path("/tmp/fake-lane"),
                    Path("/tmp/fake-lane/plan.md"),
                    "abc123",
                    "actor/driver",
                    "finalize msg",
                    labels=_rs.OC_HOST_LABELS,
                    env_builder=lambda: {"BASE_VAR": "1"},
                    argv_builder=lambda args: ["aw", *args],
                    attestation="run-1234:mocktoken123",
                )

        self.assertEqual(len(captured_proc), 1)
        call_info = captured_proc[0]
        cmd = call_info["cmd"]
        env = call_info["env"]

        # Token NOT in argv
        self.assertNotIn("run-1234:mocktoken123", " ".join(cmd))
        self.assertNotIn("--driver-token", " ".join(cmd))
        self.assertNotIn("--driver-attest", " ".join(cmd))

        # Token present in subprocess env
        self.assertEqual(env.get(LC.DRIVER_ATTEST_ENV), "run-1234:mocktoken123")


class CliNoTokenFlagTests(unittest.TestCase):
    """Unit test confirming no driver token flag is exposed in the finalize CLI (E-04/V-04)."""

    def test_finalize_help_has_no_token_flag(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "ipd", "finalize", "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn("--driver-token", proc.stdout)
        self.assertNotIn("--driver-attest", proc.stdout)
        self.assertNotIn("--attestation", proc.stdout)
