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

    def test_clears_deferred_request_on_manual_resume(self) -> None:
        runner_stop.request_stop(
            self.run_dir, runner_stop.LEVEL_AFTER_CALL, "signal pid=444"
        )
        # Hold the sidecar lock so request_stop_nowait records into _DEFERRED_REQUEST.
        with runner_stop._sidecar_lock(self.run_dir, timeout=1.0):
            runner_stop.request_stop_nowait(
                self.run_dir, runner_stop.LEVEL_NOW_FORCE, "signal pid=444"
            )
        self.assertIsNotNone(runner_stop.pending_deferred_request())

        env = {k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"}
        with mock.patch.dict(os.environ, env, clear=True):
            cleared = runner_stop.clear_stop_request_on_manual_resume(
                self.run_dir, invocation_started_at=time.time() + 1.0
            )
        self.assertIsNotNone(cleared)
        self.assertIsNone(runner_stop.pending_deferred_request())


class ResumeReconciliationAndStopLevelsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / ".git").mkdir(parents=True, exist_ok=True)
        runner_stop.reset_deferred_request()

    def tearDown(self) -> None:
        runner_stop.reset_deferred_request()
        self._tmp.cleanup()

    def _backdate_stop_file(self, run_dir: Path) -> Path:
        stop_path = runner_stop.stop_request_path(run_dir)
        payload = json.loads(stop_path.read_text(encoding="utf-8"))
        payload["requested_at"] = "2026-11-18T13:42:47+00:00"
        stop_path.write_text(json.dumps(payload), encoding="utf-8")
        past = time.time() - 60.0
        os.utime(stop_path, (past, past))
        return stop_path

    def test_resume_clears_stale_stop_for_all_four_levels_and_dispatches(self) -> None:
        """Stopping at levels 1-4 leaves stop-request.json; resuming clears it and dispatches."""
        for host_mod, driver_id in (
            (agy_runipd, "agy_runipd"),
            (oc_runipd, "oc_runipd"),
        ):
            for level in (
                runner_stop.LEVEL_AFTER_CALL,
                runner_stop.LEVEL_AFTER_SET,
                runner_stop.LEVEL_NOW,
                runner_stop.LEVEL_NOW_FORCE,
            ):
                with self.subTest(host=driver_id, level=level):
                    run_id = f"run-20261119T13000{level}Z-{driver_id}"
                    run_dir = self.root / ".aw" / "runs" / run_id
                    if level == runner_stop.LEVEL_NOW_FORCE:
                        item = {
                            "id6": "lv4001",
                            "position": 1,
                            "status": "interrupted",
                            "setid": "testset",
                            "stopped": runner_stop.forced_disposition(
                                requester="signal pid=force"
                            ),
                        }
                        extra_args = ["--reconcile", "lv4001"]
                    elif level == runner_stop.LEVEL_NOW:
                        item = {
                            "id6": "lv3001",
                            "position": 1,
                            "status": "interrupted",
                            "setid": "testset",
                            "stopped": runner_stop.stopped_disposition(
                                level=runner_stop.LEVEL_NOW,
                                requester="signal pid=now",
                                last_completed_index=1,
                                last_completed_label="tool_use",
                                git_state="",
                                events_seen=2,
                                at="2026-11-18T13:42:47+00:00",
                            ),
                        }
                        extra_args = []
                    else:
                        item = {
                            "id6": f"lv{level}001",
                            "position": 1,
                            "status": "queued",
                            "setid": "testset",
                        }
                        extra_args = []

                    _write_run_state(
                        run_dir,
                        run_id=run_id,
                        repo=self.root,
                        driver_id=driver_id,
                        queue=[item],
                    )
                    runner_stop.request_stop(run_dir, level, f"signal level={level}")
                    stop_path = self._backdate_stop_file(run_dir)
                    self.assertTrue(stop_path.is_file())

                    dispatched: list[tuple[str, int | None, bool]] = []

                    def _fake_execute_item(
                        rd: Path, st: dict, q_item: dict, *a: object, **kw: object
                    ) -> None:
                        dispatched.append(
                            (
                                q_item["id6"],
                                runner_stop.poll_stop(rd),
                                "stopped" in q_item,
                            )
                        )
                        q_item["status"] = "executed"
                        runner_shared.save_state(rd, st)

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
                        mock.patch.object(host_mod, "git_status", return_value=""),
                        mock.patch.object(
                            host_mod, "execute_item", side_effect=_fake_execute_item
                        ),
                        mock.patch.object(host_mod, "write_report"),
                        mock.patch.object(
                            runner_shared,
                            "restart_on_new_code_if_needed",
                            return_value="none",
                        ),
                        redirect_stderr(stderr_buf),
                    ):
                        rc = host_mod.main(
                            ["resume", run_id, "--repo", str(self.root), *extra_args]
                        )

                    self.assertEqual(rc, 0, stderr_buf.getvalue())
                    self.assertFalse(stop_path.exists())
                    self.assertEqual(len(dispatched), 1)
                    id6_ran, seen_stop, had_stale_stopped = dispatched[0]
                    self.assertEqual(id6_ran, item["id6"])
                    self.assertIsNone(seen_stop)
                    self.assertFalse(
                        had_stale_stopped,
                        "prior stopped record must be cleared/archived before re-dispatch",
                    )

    def test_indeterminate_refusal_prints_once_and_names_exact_reconcile_command(
        self,
    ) -> None:
        """Default resume refuses R19 indeterminate item, prints message once, and gives exact command."""
        for host_mod, driver_id, host_cmd in (
            (agy_runipd, "agy_runipd", "aw agy run"),
            (oc_runipd, "oc_runipd", "aw oc run"),
        ):
            with self.subTest(host=driver_id):
                run_id = f"run-20261119T140000Z-{driver_id}"
                run_dir = self.root / ".aw" / "runs" / run_id
                _write_run_state(
                    run_dir,
                    run_id=run_id,
                    repo=self.root,
                    driver_id=driver_id,
                    queue=[
                        {
                            "id6": "ind101",
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
                stop_path = self._backdate_stop_file(run_dir)

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
                stderr_text = stderr_buf.getvalue()
                # Printed exactly ONCE (not duplicated between requeue_interrupted and run_queue).
                self.assertEqual(stderr_text.count("refusing to resume ind101"), 1)
                expected_cmd = f"{host_cmd} resume {run_id} --reconcile ind101"
                self.assertIn(expected_cmd, stderr_text)
                self.assertIn("resume refused: 1 item(s)", stderr_text)
                self.assertTrue(stop_path.is_file())
                events = _read_events(run_dir)
                refusals = [
                    e
                    for e in events
                    if e.get("event") == "resume-refused-unknown-outcome"
                ]
                self.assertEqual(len(refusals), 1)
                self.assertIn(expected_cmd, refusals[0]["reason"])

    def test_reconcile_one_item_does_not_bypass_second_indeterminate_item(
        self,
    ) -> None:
        """--reconcile <id6> clears only that item, audits it, and keeps other indeterminate items blocked."""
        for host_mod, driver_id, host_cmd in (
            (agy_runipd, "agy_runipd", "aw agy run"),
            (oc_runipd, "oc_runipd", "aw oc run"),
        ):
            with self.subTest(host=driver_id):
                run_id = f"run-20261119T150000Z-{driver_id}"
                run_dir = self.root / ".aw" / "runs" / run_id
                _write_run_state(
                    run_dir,
                    run_id=run_id,
                    repo=self.root,
                    driver_id=driver_id,
                    queue=[
                        {
                            "id6": "ind201",
                            "position": 1,
                            "status": "interrupted",
                            "setid": "testset",
                            "preserved_branch": "aw/lane/ind201",
                            "stopped": runner_stop.forced_disposition(
                                requester="signal pid=force"
                            ),
                        },
                        {
                            "id6": "ind202",
                            "position": 2,
                            "status": "interrupted",
                            "setid": "testset",
                            "preserved_branch": "aw/lane/ind202",
                            "stopped": runner_stop.forced_disposition(
                                requester="signal pid=force"
                            ),
                        },
                    ],
                )
                runner_stop.request_stop(
                    run_dir, runner_stop.LEVEL_NOW_FORCE, "signal pid=force"
                )
                stop_path = self._backdate_stop_file(run_dir)

                dispatched: list[str] = []

                def _fake_execute_item(
                    rd: Path, st: dict, q_item: dict, *a: object, **kw: object
                ) -> None:
                    dispatched.append(q_item["id6"])
                    q_item["status"] = "executed"
                    runner_shared.save_state(rd, st)

                env_manual = {
                    k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"
                }

                # Pass 1: reconcile ONLY ind201 -> ind202 MUST still refuse, nothing dispatched, stop file kept.
                stderr_1 = io.StringIO()
                with (
                    mock.patch.dict(os.environ, env_manual, clear=True),
                    mock.patch.object(
                        host_mod, "resolve_run_dir", return_value=run_dir
                    ),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                    mock.patch.object(
                        host_mod, "git_status", return_value=" M file_a.py"
                    ),
                    mock.patch.object(
                        host_mod, "execute_item", side_effect=_fake_execute_item
                    ),
                    mock.patch.object(host_mod, "write_report"),
                    redirect_stderr(stderr_1),
                ):
                    rc_1 = host_mod.main(
                        [
                            "resume",
                            run_id,
                            "--repo",
                            str(self.root),
                            "--reconcile",
                            "ind201",
                        ]
                    )

                self.assertEqual(rc_1, 1)
                self.assertEqual(dispatched, [])
                self.assertTrue(stop_path.is_file())
                err1 = stderr_1.getvalue()
                self.assertIn("reconciled indeterminate item ind201", err1)
                self.assertEqual(err1.count("refusing to resume ind201"), 0)
                self.assertEqual(err1.count("refusing to resume ind202"), 1)
                self.assertIn(f"{host_cmd} resume {run_id} --reconcile ind202", err1)

                # Verify ind201 preserved its prior stopped record in reconciliations & events.jsonl.
                st_after_1 = runner_shared.load_state(run_dir)
                item1, item2 = st_after_1["queue"]
                self.assertFalse(runner_stop.is_indeterminate(item1))
                self.assertEqual(len(item1.get("reconciliations", [])), 1)
                self.assertEqual(
                    item1["reconciliations"][0]["prior_stopped"]["disposition"],
                    runner_stop.FORCED_DISPOSITION,
                )
                self.assertEqual(
                    item1["reconciliations"][0]["git_state"], " M file_a.py"
                )
                self.assertEqual(
                    item1["reconciliations"][0]["branch"], "aw/lane/ind201"
                )
                self.assertTrue(runner_stop.is_indeterminate(item2))

                rec_events = [
                    e
                    for e in _read_events(run_dir)
                    if e.get("event") == runner_stop.RECONCILED_ITEM_EVENT
                ]
                self.assertEqual(len(rec_events), 1)
                self.assertEqual(rec_events[0]["id6"], "ind201")
                self.assertEqual(rec_events[0]["git_state"], " M file_a.py")

                # Pass 2: re-run with both --reconcile ind201 (idempotent) and --reconcile ind202.
                stderr_2 = io.StringIO()
                with (
                    mock.patch.dict(os.environ, env_manual, clear=True),
                    mock.patch.object(
                        host_mod, "resolve_run_dir", return_value=run_dir
                    ),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                    mock.patch.object(host_mod, "git_status", return_value=""),
                    mock.patch.object(
                        host_mod, "execute_item", side_effect=_fake_execute_item
                    ),
                    mock.patch.object(host_mod, "write_report"),
                    mock.patch.object(
                        runner_shared,
                        "restart_on_new_code_if_needed",
                        return_value="none",
                    ),
                    redirect_stderr(stderr_2),
                ):
                    rc_2 = host_mod.main(
                        [
                            "resume",
                            run_id,
                            "--repo",
                            str(self.root),
                            "--reconcile",
                            "ind201",
                            "--reconcile",
                            "ind202",
                        ]
                    )

                self.assertEqual(rc_2, 0, stderr_2.getvalue())
                self.assertFalse(stop_path.exists())
                self.assertEqual(dispatched, ["ind201", "ind202"])
                rec_events_2 = [
                    e
                    for e in _read_events(run_dir)
                    if e.get("event") == runner_stop.RECONCILED_ITEM_EVENT
                ]
                self.assertEqual([e["id6"] for e in rec_events_2], ["ind201", "ind202"])

    def test_reconcile_rejects_unknown_or_non_indeterminate_id_without_mutation(
        self,
    ) -> None:
        for host_mod, driver_id in (
            (agy_runipd, "agy_runipd"),
            (oc_runipd, "oc_runipd"),
        ):
            with self.subTest(host=driver_id):
                run_id = f"run-20261119T160000Z-{driver_id}"
                run_dir = self.root / ".aw" / "runs" / run_id
                _write_run_state(
                    run_dir,
                    run_id=run_id,
                    repo=self.root,
                    driver_id=driver_id,
                    queue=[
                        {
                            "id6": "ind301",
                            "position": 1,
                            "status": "interrupted",
                            "setid": "testset",
                            "stopped": runner_stop.forced_disposition(
                                requester="signal pid=force"
                            ),
                        },
                        {
                            "id6": "ord302",
                            "position": 2,
                            "status": "queued",
                            "setid": "testset",
                        },
                    ],
                )
                runner_stop.request_stop(
                    run_dir, runner_stop.LEVEL_NOW_FORCE, "signal pid=force"
                )
                stop_path = self._backdate_stop_file(run_dir)

                env_manual = {
                    k: v for k, v in os.environ.items() if k != "AW_DRIVER_RESTART"
                }
                for bad_args, expected_err in (
                    (
                        ["--reconcile", "ind301", "--reconcile", "no_such"],
                        "does not match",
                    ),
                    (
                        ["--reconcile", "ind301", "--reconcile", "ord302"],
                        "is not indeterminate",
                    ),
                ):
                    stderr_buf = io.StringIO()
                    with (
                        mock.patch.dict(os.environ, env_manual, clear=True),
                        mock.patch.object(
                            host_mod, "resolve_run_dir", return_value=run_dir
                        ),
                        mock.patch.object(host_mod, "install_stop_triggers"),
                        redirect_stderr(stderr_buf),
                    ):
                        rc = host_mod.main(
                            ["resume", run_id, "--repo", str(self.root), *bad_args]
                        )
                    self.assertEqual(rc, 2)
                    self.assertIn(expected_err, stderr_buf.getvalue())
                    # All-or-nothing: ind301 must still be indeterminate and stop file intact.
                    st = runner_shared.load_state(run_dir)
                    self.assertTrue(runner_stop.is_indeterminate(st["queue"][0]))
                    self.assertTrue(stop_path.is_file())


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
