"""Tests for driver restart on new code between items (runfresh Order 03, `re15ol`).

Validates spec 25kzda 5.3b points 2 to 5 and 7:
- Pure restart decision logic across all four outcomes (none, unavailable, limit-reached, restart)
- Resume argv construction with frozen display mode propagation
- Lock release before replacement and module-level held lock registry
- Runner queue integration for both oc and agy hosts
- Run summary table reporting restart counts and limit refusals
- Real process replacement via execv in an isolated subprocess
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    loaded_code,
    oc_runipd,
    agy_runipd,
    render_stream,
    runner_shared,
)
from tests.support import REPO_ROOT


class RestartDecisionTests(unittest.TestCase):
    """Behavioral tests for runner_shared.restart_decision pure logic."""

    def test_disabled_via_flag(self) -> None:
        """Disabled returns none even when code changed and restartable."""
        change = loaded_code.CodeChange(
            changed=True,
            old="fp1",
            new="fp2",
            restartable=True,
            changed_files=["agent_workflows/foo.py"],
        )
        dec = runner_shared.restart_decision(change, restart_count=0, disabled=True)
        self.assertEqual(dec, "none")

    def test_pending_stop_level_returns_none(self) -> None:
        """A pending stop level returns none so wind-down handles the stop."""
        change = loaded_code.CodeChange(
            changed=True,
            old="fp1",
            new="fp2",
            restartable=True,
            changed_files=["agent_workflows/foo.py"],
        )
        dec = runner_shared.restart_decision(change, restart_count=0, stop_level=1)
        self.assertEqual(dec, "none")
        dec2 = runner_shared.restart_decision(change, restart_count=0, stop_level=2)
        self.assertEqual(dec2, "none")

    def test_no_work_returns_none(self) -> None:
        """No remaining queued or deferred work returns none."""
        change = loaded_code.CodeChange(
            changed=True,
            old="fp1",
            new="fp2",
            restartable=True,
            changed_files=["agent_workflows/foo.py"],
        )
        dec = runner_shared.restart_decision(change, restart_count=0, has_work=False)
        self.assertEqual(dec, "none")

    def test_code_not_changed_returns_none(self) -> None:
        """Unchanged code returns none."""
        change = loaded_code.CodeChange(
            changed=False,
            old="fp1",
            new="fp1",
            restartable=True,
            changed_files=[],
        )
        dec = runner_shared.restart_decision(change, restart_count=0)
        self.assertEqual(dec, "none")

    def test_changed_but_non_target_returns_unavailable(self) -> None:
        """Code changed in non-target checkout returns unavailable."""
        change = loaded_code.CodeChange(
            changed=True,
            old="fp1",
            new="fp2",
            restartable=False,
            changed_files=["agent_workflows/foo.py"],
        )
        dec = runner_shared.restart_decision(change, restart_count=0)
        self.assertEqual(dec, "unavailable")

    def test_limit_reached_returns_limit_reached(self) -> None:
        """restart_count >= limit returns limit-reached."""
        change = loaded_code.CodeChange(
            changed=True,
            old="fp1",
            new="fp2",
            restartable=True,
            changed_files=["agent_workflows/foo.py"],
        )
        dec = runner_shared.restart_decision(change, restart_count=20, limit=20)
        self.assertEqual(dec, "limit-reached")
        dec2 = runner_shared.restart_decision(change, restart_count=21, limit=20)
        self.assertEqual(dec2, "limit-reached")

    def test_normal_change_returns_restart(self) -> None:
        """Changed, restartable, has work, under limit, no stop returns restart."""
        change = loaded_code.CodeChange(
            changed=True,
            old="fp1",
            new="fp2",
            restartable=True,
            changed_files=["agent_workflows/foo.py"],
        )
        dec = runner_shared.restart_decision(change, restart_count=0, limit=20)
        self.assertEqual(dec, "restart")
        dec_sub = runner_shared.restart_decision(change, restart_count=19, limit=20)
        self.assertEqual(dec_sub, "restart")


class BuildResumeArgvTests(unittest.TestCase):
    """Behavioral tests for building resume argv with frozen options."""

    def test_oc_host_quiet_and_verbose(self) -> None:
        """Frozen quiet and verbosity 2 propagate as --quiet -v -v."""
        state = {
            "run_id": "run-20261006T120000Z-111111",
            "repo": "/tmp/test-repo",
            "options": {
                "output_mode": "quiet",
                "verbosity": 2,
            },
        }
        argv = runner_shared.build_resume_argv(
            state, host_labels=runner_shared.OC_HOST_LABELS
        )
        expected_prefix = [
            sys.executable,
            "-m",
            "agent_workflows",
            "oc",
            "run",
            "resume",
            "run-20261006T120000Z-111111",
            "--repo",
            "/tmp/test-repo",
            "--quiet",
            "-v",
            "-v",
        ]
        self.assertEqual(argv, expected_prefix)
        # Verify oc resume parser accepts it
        parser = oc_runipd.build_parser()
        args = parser.parse_args(argv[5:])
        self.assertEqual(args.command, "resume")
        self.assertEqual(args.run_id, "run-20261006T120000Z-111111")
        self.assertEqual(args.output_mode, "quiet")
        self.assertEqual(args.verbosity, 2)

    def test_agy_host_clean_and_zero_verbosity(self) -> None:
        """Frozen clean output mode and 0 verbosity omit display flags."""
        state = {
            "run_id": "run-20261006T120000Z-222222",
            "repo": "/tmp/test-repo",
            "options": {
                "output_mode": "clean",
                "verbosity": 0,
            },
        }
        argv = runner_shared.build_resume_argv(
            state, host_labels=runner_shared.AGY_HOST_LABELS
        )
        expected_prefix = [
            sys.executable,
            "-m",
            "agent_workflows",
            "agy",
            "run",
            "resume",
            "run-20261006T120000Z-222222",
            "--repo",
            "/tmp/test-repo",
        ]
        self.assertEqual(argv, expected_prefix)
        # Verify agy resume parser accepts it
        parser = agy_runipd.build_parser()
        args = parser.parse_args(argv[5:])
        self.assertEqual(args.command, "resume")
        self.assertEqual(args.run_id, "run-20261006T120000Z-222222")
        self.assertEqual(args.output_mode, "clean")
        self.assertIsNone(args.verbosity)

    def test_raw_output_mode(self) -> None:
        """Frozen raw output mode propagates as --raw."""
        state = {
            "run_id": "run-20261006T120000Z-333333",
            "repo": "/tmp/test-repo",
            "options": {
                "output_mode": "raw",
                "verbosity": 1,
            },
        }
        argv = runner_shared.build_resume_argv(
            state, host_labels=runner_shared.OC_HOST_LABELS
        )
        self.assertIn("--raw", argv)
        self.assertIn("-v", argv)
        parser = oc_runipd.build_parser()
        args = parser.parse_args(argv[5:])
        self.assertEqual(args.output_mode, "raw")
        self.assertEqual(args.verbosity, 1)


class FakeReplacementTests(unittest.TestCase):
    """Behavioral tests for fake-replacement across oc and agy host runners."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / ".git").mkdir(parents=True, exist_ok=True)
        self.pkg_dir = self.root / "agent_workflows"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
        (self.pkg_dir / "mod.py").write_text("x = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp.cleanup()

    def _setup_run(
        self, run_id: str, host_id: str, output_mode: str = "quiet", verbosity: int = 2
    ) -> Path:
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        initial_fp = loaded_code.fingerprint(self.root)
        loaded_code_rec = {
            "package_root": str(self.root),
            "fingerprint": initial_fp,
            "recorded_at": "2026-10-06T12:00:00+00:00",
            "is_target_checkout": True,
        }
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "queue": [
                {
                    "id6": "it0001",
                    "position": 1,
                    "status": "queued",
                    "setid": "testset",
                }
            ],
            "options": {
                "output_mode": output_mode,
                "verbosity": verbosity,
            },
            "driver": {
                "id": host_id,
                "path": None,
                "sha256": None,
                "loaded_code": [loaded_code_rec],
            },
        }
        runner_shared.save_state(run_dir, state)
        # Establish initial process memo
        loaded_code.loaded_code_record(self.root, package_root=self.root)
        return run_dir

    def test_oc_run_queue_fake_replacement(self) -> None:
        """Calling oc_runipd.run_queue over a changed fixture package restarts and releases lock."""
        run_id = "run-20261006T120000Z-ocfake"
        run_dir = self._setup_run(
            run_id, host_id="oc_runipd", output_mode="quiet", verbosity=2
        )
        old_fp = loaded_code.fingerprint(self.root)

        # Modify code under fixture package
        (self.pkg_dir / "mod.py").write_text("x = 42\n", encoding="utf-8")
        new_fp = loaded_code.fingerprint(self.root)
        self.assertNotEqual(old_fp, new_fp)

        replaces: list[tuple[list[str], dict[str, str]]] = []

        def fake_replace(argv: list[str], env: dict[str, str]) -> None:
            replaces.append((argv, env))

        with runner_shared.locked_run(run_dir):
            oc_runipd.run_queue(
                run_dir,
                retry_incomplete=False,
                replace=fake_replace,
                package_root=self.root,
            )

        self.assertEqual(len(replaces), 1)
        argv, env = replaces[0]
        self.assertIn("oc", argv)
        self.assertIn("resume", argv)
        self.assertIn(run_id, argv)
        self.assertIn("--quiet", argv)
        self.assertEqual(argv.count("-v"), 2)
        self.assertEqual(env.get("AW_DRIVER_RESTART"), "1")

        # Check state.json
        state = runner_shared.load_state(run_dir)
        self.assertEqual(state.get("driver_restarts"), 1)
        loaded_entries = state["driver"]["loaded_code"]
        self.assertEqual(len(loaded_entries), 2)
        second_entry = loaded_entries[1]
        self.assertEqual(second_entry["package_root"], str(self.root))
        self.assertEqual(second_entry["fingerprint"], new_fp)
        self.assertTrue(second_entry["is_target_checkout"])
        self.assertEqual(second_entry["restart"], 1)
        self.assertIn("recorded_at", second_entry)

        # Check events.jsonl
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        restarted_events = [e for e in events if e.get("event") == "driver-restarted"]
        self.assertEqual(len(restarted_events), 1)
        rev = restarted_events[0]
        self.assertEqual(rev["old_fingerprint"], old_fp)
        self.assertEqual(rev["new_fingerprint"], new_fp)
        self.assertIn("agent_workflows/mod.py", rev["changed_files"])
        self.assertIsNone(rev["previous_id6"])
        self.assertEqual(rev["restart_count"], 1)

        # Check lock is acquirable by another process
        from agent_workflows import platform_lock

        lock_path = run_dir / "driver.lock"
        acquired = platform_lock.acquire(lock_path)
        acquired.release()

    def test_agy_run_queue_fake_replacement(self) -> None:
        """Calling agy_runipd.run_queue over a changed fixture package restarts and releases lock."""
        run_id = "run-20261006T120000Z-agyfake"
        run_dir = self._setup_run(
            run_id, host_id="agy_runipd", output_mode="clean", verbosity=0
        )
        old_fp = loaded_code.fingerprint(self.root)

        # Modify code under fixture package
        (self.pkg_dir / "mod.py").write_text("x = 99\n", encoding="utf-8")
        new_fp = loaded_code.fingerprint(self.root)
        self.assertNotEqual(old_fp, new_fp)

        replaces: list[tuple[list[str], dict[str, str]]] = []

        def fake_replace(argv: list[str], env: dict[str, str]) -> None:
            replaces.append((argv, env))

        with runner_shared.locked_run(run_dir):
            agy_runipd.run_queue(
                run_dir,
                retry_incomplete=False,
                replace=fake_replace,
                package_root=self.root,
            )

        self.assertEqual(len(replaces), 1)
        argv, env = replaces[0]
        self.assertIn("agy", argv)
        self.assertIn("resume", argv)
        self.assertIn(run_id, argv)
        self.assertNotIn("--quiet", argv)
        self.assertNotIn("-v", argv)
        self.assertEqual(env.get("AW_DRIVER_RESTART"), "1")

        # Check state.json
        state = runner_shared.load_state(run_dir)
        self.assertEqual(state.get("driver_restarts"), 1)
        self.assertEqual(len(state["driver"]["loaded_code"]), 2)

        # Check lock is acquirable
        from agent_workflows import platform_lock

        lock_path = run_dir / "driver.lock"
        acquired = platform_lock.acquire(lock_path)
        acquired.release()


class DriverRestartBoundaryTests(unittest.TestCase):
    """Behavioral tests for limit, unavailable, no-lock, and pending stop cases."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / ".git").mkdir(parents=True, exist_ok=True)
        self.pkg_dir = self.root / "agent_workflows"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
        (self.pkg_dir / "mod.py").write_text("x = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp.cleanup()

    def test_limit_reached_records_refusal_and_breaks_loop(self) -> None:
        """When restart count reaches limit, refusal is stored, event appended, and loop exits 1."""
        run_id = "run-20261006T120000Z-limit"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        initial_fp = loaded_code.fingerprint(self.root)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "driver_restarts": 20,
            "queue": [
                {
                    "id6": "it0001",
                    "position": 1,
                    "status": "queued",
                    "setid": "testset",
                }
            ],
            "options": {"output_mode": "clean", "verbosity": 0},
            "driver": {
                "id": "oc_runipd",
                "loaded_code": [
                    {
                        "package_root": str(self.root),
                        "fingerprint": initial_fp,
                        "recorded_at": "2026-10-06T12:00:00+00:00",
                        "is_target_checkout": True,
                    }
                ],
            },
        }
        runner_shared.save_state(run_dir, state)
        loaded_code.loaded_code_record(self.root, package_root=self.root)

        # Modify code
        (self.pkg_dir / "mod.py").write_text("x = 999\n", encoding="utf-8")

        replaces = []

        def fake_replace(argv: list[str], env: dict[str, str]) -> None:
            replaces.append((argv, env))

        with runner_shared.locked_run(run_dir):
            exit_code = oc_runipd.run_queue(
                run_dir,
                retry_incomplete=False,
                replace=fake_replace,
                package_root=self.root,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(len(replaces), 0)

        # Verify state has refusal and remainder queued
        updated_state = runner_shared.load_state(run_dir)
        self.assertIn("driver_restart_refusal", updated_state)
        refusal = updated_state["driver_restart_refusal"]
        self.assertEqual(refusal["code"], "driver-restart-limit")
        self.assertIn("20", refusal["reason"])
        self.assertIn("Resume", refusal["remedy"])
        self.assertEqual(updated_state["queue"][0]["status"], "queued")

        # Verify event
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        limit_events = [e for e in events if e.get("event") == "driver-restart-limit"]
        self.assertEqual(len(limit_events), 1)

        # Verify render_run_summary_table output
        summary = render_stream.render_run_summary_table(updated_state, run_dir=run_dir)
        self.assertIn("Restarts: 20", summary)
        self.assertIn("driver-restart-limit:", summary)
        self.assertIn("remedy:", summary)

    def test_no_lock_registered_records_unavailable(self) -> None:
        """Calling restart when not inside locked_run appends no-run-lock event and does not restart."""
        run_id = "run-20261006T120000Z-nolock"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        initial_fp = loaded_code.fingerprint(self.root)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "queue": [
                {
                    "id6": "it0001",
                    "position": 1,
                    "status": "queued",
                    "setid": "testset",
                }
            ],
            "options": {"output_mode": "clean", "verbosity": 0},
            "driver": {
                "id": "oc_runipd",
                "loaded_code": [
                    {
                        "package_root": str(self.root),
                        "fingerprint": initial_fp,
                        "recorded_at": "2026-10-06T12:00:00+00:00",
                        "is_target_checkout": True,
                    }
                ],
            },
        }
        runner_shared.save_state(run_dir, state)
        loaded_code.loaded_code_record(self.root, package_root=self.root)
        (self.pkg_dir / "mod.py").write_text("x = 55\n", encoding="utf-8")

        replaces = []

        def fake_replace(argv: list[str], env: dict[str, str]) -> None:
            replaces.append((argv, env))

        # Do NOT enter locked_run(run_dir)
        decision = runner_shared.restart_on_new_code_if_needed(
            run_dir,
            state,
            host_labels=runner_shared.OC_HOST_LABELS,
            previous_id6=None,
            stop_level=None,
            replace=fake_replace,
            package_root=self.root,
        )
        self.assertEqual(decision, "unavailable")
        self.assertEqual(len(replaces), 0)

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        unavail_events = [
            e for e in events if e.get("event") == "driver-restart-unavailable"
        ]
        self.assertEqual(len(unavail_events), 1)
        self.assertEqual(unavail_events[0]["reason"], "no-run-lock")

    def test_pending_stop_skips_restart(self) -> None:
        """When stop is pending, restart is skipped and existing stop path handles wind-down."""
        run_id = "run-20261006T120000Z-stop"
        run_dir = self.root / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        initial_fp = loaded_code.fingerprint(self.root)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "queue": [
                {
                    "id6": "it0001",
                    "position": 1,
                    "status": "queued",
                    "setid": "testset",
                }
            ],
            "options": {"output_mode": "clean", "verbosity": 0},
            "driver": {
                "id": "oc_runipd",
                "loaded_code": [
                    {
                        "package_root": str(self.root),
                        "fingerprint": initial_fp,
                        "recorded_at": "2026-10-06T12:00:00+00:00",
                        "is_target_checkout": True,
                    }
                ],
            },
        }
        runner_shared.save_state(run_dir, state)
        loaded_code.loaded_code_record(self.root, package_root=self.root)
        (self.pkg_dir / "mod.py").write_text("x = 77\n", encoding="utf-8")

        replaces = []

        def fake_replace(argv: list[str], env: dict[str, str]) -> None:
            replaces.append((argv, env))

        with runner_shared.locked_run(run_dir):
            decision = runner_shared.restart_on_new_code_if_needed(
                run_dir,
                state,
                host_labels=runner_shared.OC_HOST_LABELS,
                previous_id6=None,
                stop_level=1,  # Stop level 1 is pending
                replace=fake_replace,
                package_root=self.root,
            )
            self.assertEqual(decision, "none")
            self.assertEqual(len(replaces), 0)


class RealSubprocessExecTests(unittest.TestCase):
    """Behavioral test for real process replacement via default replace on an all-terminal run."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / ".git").mkdir(parents=True, exist_ok=True)
        self.pkg_dir = self.root / "agent_workflows"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
        (self.pkg_dir / "x.py").write_text("val = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp.cleanup()

    def test_real_subprocess_exec_restarts_and_resumes(self) -> None:
        """A subprocess holding locked_run calls restart_on_new_code_if_needed and replaces process cleanly."""
        (self.root / ".aw" / "records").mkdir(parents=True, exist_ok=True)
        run_id = "run-20261006T120000Z-realexec"
        run_dir = runner_shared.state_root(self.root) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        initial_fp = loaded_code.fingerprint(self.root)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "queue": [
                {
                    "id6": "it0001",
                    "position": 1,
                    "status": "executed",
                    "setid": "testset",
                }
            ],
            "options": {
                "output_mode": "clean",
                "verbosity": 0,
            },
            "driver": {
                "id": "oc_runipd",
                "path": None,
                "sha256": None,
                "loaded_code": [
                    {
                        "package_root": str(self.root),
                        "fingerprint": initial_fp,
                        "recorded_at": "2026-10-06T12:00:00+00:00",
                        "is_target_checkout": True,
                    }
                ],
            },
        }
        runner_shared.save_state(run_dir, state)

        # Write runner script to drive the restart in a real subprocess
        script_path = self.root / "drive_restart.py"
        script_code = f"""
import sys
from pathlib import Path
from agent_workflows import loaded_code, runner_shared

root = Path({str(self.root)!r})
run_dir = Path({str(run_dir)!r})

# Initialize baseline memo
loaded_code.loaded_code_record(root, package_root=root)

state = runner_shared.load_state(run_dir)

with runner_shared.locked_run(run_dir):
    # Edit code to change fingerprint
    (root / "agent_workflows" / "x.py").write_text("val = 2\\n", encoding="utf-8")
    runner_shared.restart_on_new_code_if_needed(
        run_dir,
        state,
        host_labels=runner_shared.OC_HOST_LABELS,
        previous_id6=None,
        stop_level=None,
        package_root=root,
        has_work=True,
    )
"""
        script_path.write_text(script_code, encoding="utf-8")

        env = dict(os.environ)
        env["AW_NO_REEXEC"] = "1"
        env["PYTHONPATH"] = str(REPO_ROOT)

        proc = subprocess.run(
            [sys.executable, "-c", script_code],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            proc.returncode,
            0,
            f"Subprocess failed:\nstdout: {proc.stdout}\nstderr: {proc.stderr}",
        )
        self.assertNotIn("already controlled by another process", proc.stderr)

        # Verify driver-restarted event was recorded
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        restarted = [e for e in events if e.get("event") == "driver-restarted"]
        self.assertEqual(len(restarted), 1)
        rev = restarted[0]
        self.assertEqual(rev["old_fingerprint"], initial_fp)
        self.assertNotEqual(rev["new_fingerprint"], initial_fp)
        self.assertIn("agent_workflows/x.py", rev["changed_files"])
