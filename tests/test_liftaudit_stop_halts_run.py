from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    runner_shared,
    runner_shutdown,
    runner_stop,
)
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN


def _init_clean_repo(repo: Path) -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


def _init_repo_with_two_plans(
    repo: Path, id1: str = "qa0001", id2: str = "qa0002"
) -> tuple[Path, Path]:
    _init_clean_repo(repo)
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan1 = plans_dir / f"20260828-demo-01-{id1}-plan1.ipd.md"
    plan2 = plans_dir / f"20260828-demo-02-{id2}-plan2.ipd.md"
    plan1.write_text(_CONFORMING_PLAN.format(id6=id1), encoding="utf-8")
    plan2.write_text(_CONFORMING_PLAN.format(id6=id2), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)
    return plan1, plan2


class LiftauditStopHaltsRunTests(unittest.TestCase):
    """Behavioral tests verifying deliberate stops halt run_queue across hosts and levels."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_run(
        self, tmp_path: Path, id1: str = "qa0001", id2: str = "qa0002"
    ) -> tuple[Path, Path]:
        repo = tmp_path / "repo"
        plan1, plan2 = _init_repo_with_two_plans(repo, id1=id1, id2=id2)
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "events.jsonl").touch()

        item1 = {
            "position": 1,
            "id6": id1,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan1.relative_to(repo)),
            "action": "execute",
        }
        item2 = {
            "position": 2,
            "id6": id2,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan2.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item1, item2],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "self_finalize": False,
                "no_audit": True,
                "isolate_worktree": False,
            },
        }
        (run_dir / "state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
        return repo, run_dir

    def _run_stop_test(
        self, host: str, stop_level: int, stop_exc: BaseException
    ) -> None:
        driver_module = oc_runipd if host == "oc" else agy_runipd
        launcher_name = "run_opencode" if host == "oc" else "run_agy_turn"

        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            repo, run_dir = self._setup_run(tmp)

            dispatched_ids: list[str] = []

            def fake_launcher(*args, **kwargs):
                state_file = run_dir / "state.json"
                if state_file.is_file():
                    st = json.loads(state_file.read_text(encoding="utf-8"))
                    for it in st.get("queue", []):
                        if it.get("status") == "running":
                            dispatched_ids.append(it["id6"])
                            break
                raise stop_exc

            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            with (
                mock.patch.object(
                    driver_module, "driver_begin", return_value=(0, "ok")
                ),
                mock.patch.object(driver_module, launcher_name, fake_launcher),
                mock.patch("sys.stdout", stdout_buf),
                mock.patch("sys.stderr", stderr_buf),
            ):
                rc = driver_module.run_queue(run_dir, retry_incomplete=False)

            captured_output = stdout_buf.getvalue() + stderr_buf.getvalue()
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            queue = saved_state["queue"]

            # (a) Launcher was called for the FIRST id6 only
            self.assertEqual(
                dispatched_ids,
                ["qa0001"],
                "Launcher must be called for the first item only (no dispatch leak)",
            )

            # (b) Second item's persisted status is still queued
            self.assertEqual(
                queue[1]["status"],
                "queued",
                "Second item must remain queued",
            )

            # (c) First item's persisted status is interrupted and stopped record has expected certainty
            self.assertEqual(
                queue[0]["status"],
                "interrupted",
                "First item status must be interrupted",
            )
            expected_certainty = (
                runner_stop.CERTAINTY_KNOWN
                if stop_level == 3
                else runner_stop.CERTAINTY_INDETERMINATE
            )
            self.assertEqual(
                queue[0].get("stopped", {}).get("certainty"),
                expected_certainty,
                f"Stop record must have certainty {expected_certainty}",
            )

            # (d) observe_ledger returns coherent (True)
            coherent, ledger_msg = runner_shutdown.observe_ledger(run_dir)
            self.assertTrue(
                coherent,
                f"Ledger must be coherent under spec R3, got: {ledger_msg}",
            )

            # (e) Captured output contains STOPPED proving run reported deliberate stop
            self.assertIn(
                "STOPPED",
                captured_output,
                "Run output must contain 'STOPPED' reporting deliberate stop",
            )

            # (f) Exit code matches deliberate_stop_exit_code calculation
            expected_rc = runner_stop.deliberate_stop_exit_code(
                runner_shared.exit_code_statuses(queue),
                success_states={runner_shared.EXIT_SUCCESS_TOKEN},
                stopped=True,
            )
            self.assertEqual(rc, expected_rc)

    def test_oc_run_queue_stop_at_checkpoint_level3(self):
        stop_exc = runner_stop.StopAtCheckpoint(
            runner_stop.CheckpointObserver(
                detector=lambda line: True,
                requested_level=3,
                stop_at_checkpoint=True,
            )
        )
        self._run_stop_test("oc", 3, stop_exc)

    def test_oc_run_queue_stop_now_force_level4(self):
        stop_exc = runner_stop.StopNowForce(level=4, events_seen=2)
        self._run_stop_test("oc", 4, stop_exc)

    def test_agy_run_queue_stop_at_checkpoint_level3(self):
        stop_exc = runner_stop.StopAtCheckpoint(
            runner_stop.CheckpointObserver(
                detector=lambda line: True,
                requested_level=3,
                stop_at_checkpoint=True,
            )
        )
        self._run_stop_test("agy", 3, stop_exc)

    def test_agy_run_queue_stop_now_force_level4(self):
        stop_exc = runner_stop.StopNowForce(level=4, events_seen=2)
        self._run_stop_test("agy", 4, stop_exc)

    def test_record_forced_stop_injected_git_status(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "events.jsonl").touch()
            state = {"repo": temp}
            item = {"id6": "qa0001"}
            stop = runner_stop.StopNowForce(level=4, events_seen=1)
            rec = runner_shared._record_forced_stop(
                run_dir,
                state,
                item,
                stop,
                git_status_fn=lambda repo: "M file.txt",
            )
            self.assertEqual(rec["git_state"], "M file.txt")
            self.assertEqual(item["stopped"]["git_state"], "M file.txt")

    def test_record_forced_stop_omitted_git_status_fn_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            state = {"repo": temp}
            item = {"id6": "qa0001"}
            stop = runner_stop.StopNowForce(level=4, events_seen=1)
            with self.assertRaises(TypeError):
                runner_shared._record_forced_stop(run_dir, state, item, stop)  # type: ignore[call-arg]

    def test_record_checkpoint_stop_dirty_isolated_worktree(self):
        for mod, driver_name in (
            (oc_runipd, "oc_runipd"),
            (agy_runipd, "agy_runipd"),
        ):
            with self.subTest(driver=driver_name):
                with tempfile.TemporaryDirectory() as temp:
                    tmp = Path(temp)
                    main_repo = _init_clean_repo(tmp / "main")
                    lane_repo = _init_clean_repo(tmp / "lane")
                    (lane_repo / "dirty_file.txt").write_text(
                        "lane dirty\n", encoding="utf-8"
                    )
                    run_dir = main_repo / ".aw" / "records" / "runs" / "run-test"
                    run_dir.mkdir(parents=True, exist_ok=True)
                    events_file = run_dir / "events.jsonl"
                    events_file.touch()

                    state = {"repo": str(main_repo)}
                    item = {"id6": "qa0001"}
                    obs = runner_stop.CheckpointObserver(
                        detector=lambda line: True,
                        requested_level=3,
                    )
                    rec = mod._record_checkpoint_stop(
                        run_dir, state, item, obs, work_dir=lane_repo
                    )
                    self.assertIn("dirty_file.txt", rec["git_state"])
                    self.assertFalse(rec["git_state"].startswith("<unobserved"))
                    self.assertEqual(item["stopped"]["git_state"], rec["git_state"])
                    self.assertTrue(item["stopped"]["stopped_deliberately"])
                    self.assertEqual(item["stopped"]["level"], 3)

                    events_lines = [
                        json.loads(line)
                        for line in events_file.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                    self.assertEqual(len(events_lines), 1)
                    self.assertEqual(events_lines[0].get("id6"), "qa0001")

    def test_record_checkpoint_stop_worktree_resolution_precedence(self):
        for mod, driver_name in (
            (oc_runipd, "oc_runipd"),
            (agy_runipd, "agy_runipd"),
        ):
            with tempfile.TemporaryDirectory() as temp:
                tmp = Path(temp)
                main_repo = _init_clean_repo(tmp / "main")
                lane_repo = _init_clean_repo(tmp / "lane")
                (main_repo / "main_dirty.txt").write_text(
                    "main dirty\n", encoding="utf-8"
                )
                (lane_repo / "dirty_file.txt").write_text(
                    "lane dirty\n", encoding="utf-8"
                )
                run_dir = main_repo / ".aw" / "records" / "runs" / "run-test"
                run_dir.mkdir(parents=True, exist_ok=True)
                events_file = run_dir / "events.jsonl"
                events_file.touch()

                state = {"repo": str(main_repo)}
                obs = runner_stop.CheckpointObserver(
                    detector=lambda line: True,
                    requested_level=3,
                )

                cases = [
                    (
                        "item_worktree",
                        {"id6": "qa0001", "worktree": str(lane_repo)},
                        None,
                        "dirty_file.txt",
                        "main_dirty.txt",
                    ),
                    (
                        "attempts_worktree",
                        {
                            "id6": "qa0001",
                            "attempts": [{"worktree": str(lane_repo)}],
                        },
                        None,
                        "dirty_file.txt",
                        "main_dirty.txt",
                    ),
                    (
                        "work_dir_precedence",
                        {"id6": "qa0001", "worktree": str(main_repo)},
                        lane_repo,
                        "dirty_file.txt",
                        "main_dirty.txt",
                    ),
                    (
                        "fallback_repo",
                        {"id6": "qa0001"},
                        None,
                        "main_dirty.txt",
                        "dirty_file.txt",
                    ),
                ]

                for (
                    case_name,
                    item_dict,
                    work_dir,
                    expected_dirty,
                    forbidden_dirty,
                ) in cases:
                    with self.subTest(driver=driver_name, case=case_name):
                        item = dict(item_dict)
                        rec = mod._record_checkpoint_stop(
                            run_dir, state, item, obs, work_dir=work_dir
                        )
                        self.assertIn(expected_dirty, rec["git_state"])
                        self.assertNotIn(forbidden_dirty, rec["git_state"])
                        self.assertFalse(rec["git_state"].startswith("<unobserved"))

    def test_record_checkpoint_stop_injected_git_status(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "events.jsonl").touch()
            lane_path = Path(temp) / "my_lane"
            lane_path.mkdir()
            state = {"repo": temp}
            item = {"id6": "qa0001"}
            obs = runner_stop.CheckpointObserver(
                detector=lambda line: True,
                requested_level=3,
            )
            rec = runner_shared._record_checkpoint_stop(
                run_dir,
                state,
                item,
                obs,
                work_dir=lane_path,
                git_status_fn=lambda repo: f"?? {repo.name}-dirty",
            )
            expected = f"?? {lane_path.name}-dirty"
            self.assertEqual(rec["git_state"], expected)
            self.assertEqual(item["stopped"]["git_state"], expected)

    def test_record_checkpoint_stop_raising_git_status_fn_yields_unobserved(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "events.jsonl").touch()
            state = {"repo": temp}
            item = {"id6": "qa0001"}
            obs = runner_stop.CheckpointObserver(
                detector=lambda line: True,
                requested_level=3,
            )

            def bad_status_fn(repo: Path) -> str:
                raise RuntimeError("git execution failed")

            rec = runner_shared._record_checkpoint_stop(
                run_dir,
                state,
                item,
                obs,
                git_status_fn=bad_status_fn,
            )
            self.assertTrue(rec["git_state"].startswith("<unobserved:"))
            self.assertIn("git execution failed", rec["git_state"])
            self.assertEqual(item["stopped"]["git_state"], rec["git_state"])

    def test_record_checkpoint_stop_omitted_git_status_fn_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            state = {"repo": temp}
            item = {"id6": "qa0001"}
            obs = runner_stop.CheckpointObserver(
                detector=lambda line: True,
                requested_level=3,
            )
            with self.assertRaises(TypeError):
                runner_shared._record_checkpoint_stop(
                    run_dir,
                    state,
                    item,
                    obs,  # type: ignore[call-arg]
                )


if __name__ == "__main__":
    unittest.main()
