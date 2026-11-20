"""Behavioral tests: manual `resume` clears stale stop-request.json while preserving live stops."""

from __future__ import annotations

import io
import json
import os
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared, runner_stop


def _write_run_state(
    run_dir: Path,
    *,
    run_id: str,
    repo: Path,
    driver_id: str,
    queue: list[dict] | None = None,
) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "repo": str(repo),
        "queue": queue
        if queue is not None
        else [
            {
                "id6": "it0001",
                "position": 1,
                "status": "queued",
                "setid": "testset",
            }
        ],
        "options": {"output_mode": "clean", "verbosity": 0},
        "driver": {"id": driver_id, "loaded_code": []},
    }
    runner_shared.save_state(run_dir, state)
    return state


def _read_events(run_dir: Path) -> list[dict]:
    path = run_dir / "events.jsonl"
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class ClearStopRequestHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._tmp.name) / "run-test"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clears_stop_request_older_than_invocation_start(self) -> None:
        runner_stop.request_stop(
            self.run_dir, runner_stop.LEVEL_AFTER_CALL, "signal pid=123"
        )
        self.assertTrue(runner_stop.stop_request_path(self.run_dir).is_file())

        # Ensure invocation_started_at is strictly after the stop request was created.
        started_at = time.time() + 1.0
        env = {k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"}
        with mock.patch.dict(os.environ, env, clear=True):
            cleared = runner_stop.clear_stop_request_on_manual_resume(
                self.run_dir, invocation_started_at=started_at
            )

        self.assertIsNotNone(cleared)
        assert cleared is not None
        self.assertEqual(cleared.level, runner_stop.LEVEL_AFTER_CALL)
        self.assertEqual(cleared.requester, "signal pid=123")
        self.assertFalse(runner_stop.stop_request_path(self.run_dir).exists())
        self.assertIsNone(runner_stop.poll_stop(self.run_dir))

    def test_preserves_stop_request_during_driver_self_restart(self) -> None:
        runner_stop.request_stop(
            self.run_dir, runner_stop.LEVEL_AFTER_CALL, "signal pid=123"
        )
        started_at = time.time() + 10.0

        with mock.patch.dict(os.environ, {"AW_DRIVER_RESTART": "1"}):
            cleared = runner_stop.clear_stop_request_on_manual_resume(
                self.run_dir, invocation_started_at=started_at
            )

        self.assertIsNone(cleared)
        self.assertTrue(runner_stop.stop_request_path(self.run_dir).is_file())
        self.assertEqual(
            runner_stop.poll_stop(self.run_dir), runner_stop.LEVEL_AFTER_CALL
        )

    def test_preserves_stop_request_created_after_invocation_start(self) -> None:
        started_at = time.time() - 5.0
        runner_stop.request_stop(self.run_dir, runner_stop.LEVEL_NOW, "stop-command")

        env = {k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"}
        with mock.patch.dict(os.environ, env, clear=True):
            cleared = runner_stop.clear_stop_request_on_manual_resume(
                self.run_dir, invocation_started_at=started_at
            )

        self.assertIsNone(cleared)
        self.assertTrue(runner_stop.stop_request_path(self.run_dir).is_file())
        self.assertEqual(runner_stop.poll_stop(self.run_dir), runner_stop.LEVEL_NOW)

    def test_preserves_stop_request_whose_mtime_is_newer_than_invocation_start(
        self,
    ) -> None:
        runner_stop.request_stop(self.run_dir, runner_stop.LEVEL_AFTER_SET, "signal")
        path = runner_stop.stop_request_path(self.run_dir)
        started_at = time.time() + 1.0
        # Simulate the file being updated after invocation_started_at even if requested_at was older.
        future = started_at + 10.0
        os.utime(path, (future, future))

        env = {k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"}
        with mock.patch.dict(os.environ, env, clear=True):
            cleared = runner_stop.clear_stop_request_on_manual_resume(
                self.run_dir, invocation_started_at=started_at
            )

        self.assertIsNone(cleared)
        self.assertTrue(path.is_file())

    def test_absent_stop_request_creates_no_sidecar_lock(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"}
        with mock.patch.dict(os.environ, env, clear=True):
            cleared = runner_stop.clear_stop_request_on_manual_resume(
                self.run_dir, invocation_started_at=time.time() + 1.0
            )

        self.assertIsNone(cleared)
        self.assertFalse(runner_stop.stop_request_lock_path(self.run_dir).exists())


class ResumeCLIClearsStaleStopTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / ".git").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_manual_resume_clears_stale_stop_while_self_restart_preserves(self) -> None:
        for host_mod, driver_id in (
            (agy_runipd, "agy_runipd"),
            (oc_runipd, "oc_runipd"),
        ):
            with self.subTest(host=driver_id):
                run_id = f"run-20261119T120000Z-{driver_id}"
                run_dir = self.root / ".aw" / "runs" / run_id
                _write_run_state(
                    run_dir, run_id=run_id, repo=self.root, driver_id=driver_id
                )
                runner_stop.request_stop(
                    run_dir, runner_stop.LEVEL_AFTER_CALL, "signal pid=999"
                )
                # Backdate stop file mtime and requested_at slightly so it strictly predates main().
                stop_path = runner_stop.stop_request_path(run_dir)
                payload = json.loads(stop_path.read_text(encoding="utf-8"))
                payload["requested_at"] = "2026-11-18T13:42:47+00:00"
                stop_path.write_text(json.dumps(payload), encoding="utf-8")
                past = time.time() - 60.0
                os.utime(stop_path, (past, past))

                seen_levels: list[int | None] = []

                def _fake_run_queue(rd: Path, **kwargs: object) -> int:
                    seen_levels.append(runner_stop.poll_stop(rd))
                    return 0

                # 1. Self-restart (AW_DRIVER_RESTART set) must preserve stop-request.json.
                with (
                    mock.patch.dict(os.environ, {"AW_DRIVER_RESTART": "1"}),
                    mock.patch.object(
                        host_mod, "resolve_run_dir", return_value=run_dir
                    ),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                    mock.patch.object(
                        host_mod, "run_queue", side_effect=_fake_run_queue
                    ),
                ):
                    rc_self = host_mod.main(
                        ["resume", run_id, "--repo", str(self.root)]
                    )
                self.assertEqual(rc_self, 0)
                self.assertEqual(seen_levels[-1], runner_stop.LEVEL_AFTER_CALL)
                self.assertTrue(stop_path.is_file())
                self.assertEqual(_read_events(run_dir), [])

                # 2. Manual resume (no AW_DRIVER_RESTART) clears stale stop-request.json,
                #    prints notice, records ledger event, and lets run_queue see no stop.
                env_manual = {
                    k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"
                }
                stderr_buf = io.StringIO()
                with (
                    mock.patch.dict(os.environ, env_manual, clear=True),
                    mock.patch.object(
                        host_mod, "resolve_run_dir", return_value=run_dir
                    ),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                    mock.patch.object(
                        host_mod, "run_queue", side_effect=_fake_run_queue
                    ),
                    redirect_stderr(stderr_buf),
                ):
                    rc_manual = host_mod.main(
                        ["resume", run_id, "--repo", str(self.root)]
                    )
                self.assertEqual(rc_manual, 0)
                self.assertIsNone(seen_levels[-1])
                self.assertFalse(stop_path.exists())
                self.assertIn(
                    "cleared prior stop request: level 1 (after-call)",
                    stderr_buf.getvalue(),
                )
                events = _read_events(run_dir)
                self.assertEqual(len(events), 1)
                self.assertEqual(
                    events[0]["event"], runner_stop.STOP_REQUEST_CLEARED_EVENT
                )
                self.assertEqual(events[0]["prior_level"], runner_stop.LEVEL_AFTER_CALL)
                self.assertEqual(events[0]["prior_requester"], "signal pid=999")

    def test_duplicate_resume_blocked_by_run_lock_never_clears_live_stop_request(
        self,
    ) -> None:
        for host_mod, driver_id in (
            (agy_runipd, "agy_runipd"),
            (oc_runipd, "oc_runipd"),
        ):
            with self.subTest(host=driver_id):
                run_id = f"run-20261119T120001Z-{driver_id}"
                run_dir = self.root / ".aw" / "runs" / run_id
                _write_run_state(
                    run_dir, run_id=run_id, repo=self.root, driver_id=driver_id
                )
                runner_stop.request_stop(
                    run_dir, runner_stop.LEVEL_AFTER_CALL, "signal pid=live"
                )
                stop_path = runner_stop.stop_request_path(run_dir)
                past = time.time() - 60.0
                os.utime(stop_path, (past, past))

                env_manual = {
                    k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"
                }
                # Hold the run lock to simulate an active live driver.
                with runner_shared.run_lock(run_dir):
                    stderr_buf = io.StringIO()
                    with (
                        mock.patch.dict(os.environ, env_manual, clear=True),
                        mock.patch.object(
                            host_mod, "resolve_run_dir", return_value=run_dir
                        ),
                        mock.patch.object(host_mod, "install_stop_triggers"),
                        redirect_stderr(stderr_buf),
                    ):
                        rc = host_mod.main(["resume", run_id, "--repo", str(self.root)])
                self.assertNotEqual(rc, 0)
                self.assertTrue(stop_path.is_file())
                self.assertEqual(
                    runner_stop.poll_stop(run_dir), runner_stop.LEVEL_AFTER_CALL
                )

    def test_resume_with_indeterminate_item_refuses_and_keeps_stop_request(
        self,
    ) -> None:
        for host_mod, driver_id in (
            (agy_runipd, "agy_runipd"),
            (oc_runipd, "oc_runipd"),
        ):
            with self.subTest(host=driver_id):
                run_id = f"run-20261119T120002Z-{driver_id}"
                run_dir = self.root / ".aw" / "runs" / run_id
                _write_run_state(
                    run_dir,
                    run_id=run_id,
                    repo=self.root,
                    driver_id=driver_id,
                    queue=[
                        {
                            "id6": "ind001",
                            "position": 1,
                            "status": "interrupted",
                            "setid": "testset",
                            "stopped": runner_stop.forced_disposition(
                                requester="signal pid=force"
                            ),
                        }
                    ],
                )
                runner_stop.request_stop(
                    run_dir, runner_stop.LEVEL_NOW_FORCE, "signal pid=force"
                )
                stop_path = runner_stop.stop_request_path(run_dir)
                past = time.time() - 60.0
                os.utime(stop_path, (past, past))

                env_manual = {
                    k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"
                }
                stderr_buf = io.StringIO()
                with (
                    mock.patch.dict(os.environ, env_manual, clear=True),
                    mock.patch.object(
                        host_mod, "resolve_run_dir", return_value=run_dir
                    ),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                    redirect_stderr(stderr_buf),
                ):
                    rc = host_mod.main(["resume", run_id, "--repo", str(self.root)])

                self.assertEqual(rc, 1)
                self.assertIn("resume refused", stderr_buf.getvalue())
                self.assertTrue(stop_path.is_file())
                self.assertEqual(
                    runner_stop.poll_stop(run_dir), runner_stop.LEVEL_NOW_FORCE
                )


if __name__ == "__main__":
    unittest.main()
