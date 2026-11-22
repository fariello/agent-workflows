"""Behavioral tests for runner startup latency capture and `aw runs analyze` integration.

Verifies that both `aw agy run` and `aw oc run` record elapsed latency across:
    script start -> first output -> first question -> first start of execution
into `state.json` and `events.jsonl`, and that `aw runs analyze`, `aw runs query`,
the analytics privacy boundary, and the published dashboard surface those metrics honestly.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import (
    agy_runipd,
    cli,
    oc_runipd,
    run_analytics,
    run_analytics_privacy,
    run_analytics_query,
    run_dashboard,
    runner_shared,
)
from tests.record_builder import RecordBuilder


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


def _init_min_git_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "README.md").write_text("# test\n", encoding="utf-8")
    (root / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "add", "README.md", ".gitignore"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root


def _write_approved_plan(repo: Path, id6: str = "st1001") -> Path:
    path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20261120-stset-01-{id6}-sample-plan.ipd.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        str(
            RecordBuilder().plan(
                title="Startup timing test plan",
                when="2026-11-20",
                plan_role="child",
                scope_paths="README.md",
                item_dependencies="none",
                status="approved",
                set="stset",
                order=1,
                highest_e_allocated="01",
                priority="medium",
                work_kind="chore",
                author="test",
                id6=id6,
                approval="2026-11-20, recorded via aw ipd set: status set to approved",
                readiness="go-pending-approval",
                history=[
                    "- 2026-11-20 approved (aw set): status set to approved",
                    "- 2026-11-20 /plan-review (test): APPROVE",
                    "- 2026-11-20 draft (test): created.",
                ],
                raw_fields={
                    "Concern": "startup timing test concern.",
                    "Scope": "demo scope.",
                },
                body=(
                    "## Goal\n\nDemo goal sentence.\n\n"
                    "## Detailed Implementation Checklist (TODO)\n\n"
                    "Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.\n\n"
                    "### Task group 1: demo\n\n"
                    "- [ ] E-01 Update README.md.\n"
                    "  - Depends on: none\n"
                    "  - Expected outcome: README.md updated.\n"
                    "  - Execution state: pending\n\n"
                    "## Project conventions discovered (Step 0)\n\n- demo convention.\n\n"
                    "## Findings\n\ndemo findings.\n\n"
                    "## Proposed changes (ordered, validatable)\n\n1. README.md: update it.\n\n"
                    "## Deferred / out of scope (with reason)\n\nnone.\n\n"
                    "## Scope check\n\n- Over-scope: none.\n- Under-scope: none.\n\n"
                    "## Required tests / validation\n\nManual check that README.md exists.\n\n"
                    "## Spec / documentation sync\n\nN/A: demo only.\n\n"
                    "## Open questions\n\n"
                    "### OQ-01: none?\n\n"
                    "- Blocking: no\n"
                    "- Status: resolved\n"
                    "- Owner: none\n"
                    "- Resolution or deferral rationale: none.\n\n"
                    "## Validation and cross-check (verify before reporting done)\n\n"
                    "Validation-state rule: inspect evidence in a separate pass.\n\n"
                    "- [ ] V-01 validates E-01\n"
                    "  - Required evidence: README.md present.\n"
                    "  - Observed evidence:\n"
                    "  - Result: pending\n\n"
                    "## Approval and execution gate\n\n"
                    "- Size assessment: standard\n"
                    "- Cohesion rationale: not required\n\n"
                    "Execution contract: commit path-scoped; do not push."
                ),
                text_only=True,
            )
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", str(path)], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", f"add plan {id6}"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return path


def _read_events(run_dir: Path) -> list[dict[str, Any]]:
    ev = run_dir / "events.jsonl"
    if not ev.is_file():
        return []
    return [
        json.loads(line)
        for line in ev.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class StartupLatencyTrackerTests(unittest.TestCase):
    def test_stream_proxy_captures_first_non_empty_output_and_unwraps_immediately(
        self,
    ) -> None:
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with (
            mock.patch.object(sys, "stdout", buf_out),
            mock.patch.object(sys, "stderr", buf_err),
        ):
            with runner_shared.track_startup_timings(
                invocation_kind="start", start_mono=100.0, start_wall=1700000000.0
            ) as tracker:
                # Empty write must NOT trigger first_output or unwrap.
                sys.stdout.write("")
                self.assertNotIn("startup_to_first_output_seconds", tracker.snapshot())
                self.assertIsNot(sys.stdout, buf_out)

                # First non-empty write triggers capture AND unwraps both streams immediately.
                sys.stderr.write("starting...\n")
                self.assertIs(sys.stdout, buf_out)
                self.assertIs(sys.stderr, buf_err)

                snap = tracker.snapshot()
                self.assertIn("startup_to_first_output_seconds", snap)
                self.assertIn("first_output_at", snap)
                self.assertGreaterEqual(snap["startup_to_first_output_seconds"], 0.0)

            self.assertIs(sys.stdout, buf_out)
            self.assertIs(sys.stderr, buf_err)
            self.assertIsNone(runner_shared.active_startup_tracker())
        self.assertEqual(buf_err.getvalue(), "starting...\n")

    def test_milestones_deltas_monotonicity_and_post_execution_question_ignored(
        self,
    ) -> None:
        tracker = runner_shared.StartupLatencyTracker(
            invocation_kind="start",
            start_mono=1000.0,
            start_wall=1700000000.0,
        )
        self.assertTrue(
            tracker.mark_first_output(now_mono=1001.25, now_wall=1700000001.25)
        )
        # Second mark_first_output is ignored.
        self.assertFalse(
            tracker.mark_first_output(now_mono=1002.0, now_wall=1700000002.0)
        )
        self.assertTrue(
            tracker.mark_first_question(now_mono=1004.5, now_wall=1700000004.5)
        )
        self.assertTrue(
            tracker.mark_first_execution(now_mono=1012.75, now_wall=1700000012.75)
        )
        snap = tracker.snapshot()
        self.assertEqual(snap["invocation_kind"], "start")
        self.assertAlmostEqual(snap["startup_to_first_output_seconds"], 1.25, places=5)
        self.assertAlmostEqual(snap["startup_to_first_question_seconds"], 4.5, places=5)
        self.assertAlmostEqual(
            snap["startup_to_first_execution_seconds"], 12.75, places=5
        )
        self.assertAlmostEqual(
            snap["first_output_to_first_question_seconds"], 3.25, places=5
        )
        self.assertAlmostEqual(
            snap["first_question_to_first_execution_seconds"], 8.25, places=5
        )
        self.assertAlmostEqual(
            snap["first_output_to_first_execution_seconds"], 11.5, places=5
        )

        # A question asked AFTER execution has started must not retroactively record a startup question.
        tracker2 = runner_shared.StartupLatencyTracker(
            invocation_kind="start",
            start_mono=2000.0,
            start_wall=1700000000.0,
        )
        tracker2.mark_first_output(now_mono=2001.0, now_wall=1700000001.0)
        tracker2.mark_first_execution(now_mono=2005.0, now_wall=1700000005.0)
        self.assertFalse(
            tracker2.mark_first_question(now_mono=2010.0, now_wall=1700000010.0)
        )
        snap2 = tracker2.snapshot()
        self.assertNotIn("startup_to_first_question_seconds", snap2)
        self.assertNotIn("first_output_to_first_question_seconds", snap2)
        self.assertNotIn("first_question_to_first_execution_seconds", snap2)
        self.assertAlmostEqual(
            snap2["first_output_to_first_execution_seconds"], 4.0, places=5
        )

    def test_prompt_functions_record_first_question_only_when_interactive_tty(
        self,
    ) -> None:
        # Non-TTY prompt returns None without marking first_question.
        with runner_shared.track_startup_timings(
            invocation_kind="start", start_mono=time.monotonic(), start_wall=time.time()
        ) as tracker:
            ans = runner_shared.prompt_for_gate_phrase(
                "Proceed? ",
                timeout=0.01,
                stdin=io.StringIO("yes\n"),
                stderr=io.StringIO(),
            )
            self.assertIsNone(ans)
            self.assertNotIn("startup_to_first_question_seconds", tracker.snapshot())

        # TTY prompt marks first_question (and first_output if none preceded it).
        fake_in = _FakeTTY("yes\n")
        fake_err = _FakeTTY()
        with (
            mock.patch("select.select", return_value=([fake_in], [], [])),
            runner_shared.track_startup_timings(
                invocation_kind="start",
                start_mono=time.monotonic(),
                start_wall=time.time(),
            ) as tracker2,
        ):
            ans2 = runner_shared.prompt_for_gate_phrase(
                "Proceed? ",
                timeout=1.0,
                stdin=fake_in,
                stderr=fake_err,
            )
            self.assertEqual(ans2, "yes\n")
            snap = tracker2.snapshot()
            self.assertIn("startup_to_first_output_seconds", snap)
            self.assertIn("startup_to_first_question_seconds", snap)
            self.assertGreaterEqual(
                snap["startup_to_first_question_seconds"],
                snap["startup_to_first_output_seconds"],
            )


class RunnerHostStartupTimingPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = _init_min_git_repo(Path(self._tmp.name) / "repo")
        _write_approved_plan(self.repo, "st1001")

    def test_both_hosts_record_start_question_and_first_execution_in_state_and_events(
        self,
    ) -> None:
        for host_mod, host_name in (
            (agy_runipd, "agy"),
            (oc_runipd, "oc"),
        ):
            with self.subTest(host=host_name):
                run_id = f"run-20261120T120000Z-{host_name}1"

                def _fake_execute_item(
                    run_dir: Path,
                    state: dict[str, Any],
                    item: dict[str, Any],
                    **kwargs: Any,
                ) -> None:
                    # Verify startup_timings is ALREADY persisted when execution starts!
                    on_disk = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    self.assertIn("startup_timings", on_disk)
                    self.assertIn(
                        "startup_to_first_execution_seconds",
                        on_disk["startup_timings"],
                    )
                    item["status"] = "executed"
                    host_mod.save_state(run_dir, state)

                orig_init = host_mod.initialize_run

                def _wait_mono_tick() -> None:
                    t0 = time.monotonic()
                    while time.monotonic() <= t0:
                        time.sleep(0.005)

                def _init_with_question(args: Any) -> Path:
                    print(f"[{host_name}] preparing queue...", file=sys.stderr)
                    _wait_mono_tick()
                    runner_shared.mark_active_startup_first_question()
                    _wait_mono_tick()
                    return orig_init(args)

                out_buf = io.StringIO()
                err_buf = io.StringIO()
                with (
                    mock.patch.object(sys, "stdout", out_buf),
                    mock.patch.object(sys, "stderr", err_buf),
                    mock.patch.object(
                        host_mod, "initialize_run", side_effect=_init_with_question
                    ),
                    mock.patch.object(
                        host_mod, "execute_item", side_effect=_fake_execute_item
                    ),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                ):
                    rc = host_mod.main(
                        [
                            "start",
                            "st1001",
                            "--repo",
                            str(self.repo),
                            "--run-id",
                            run_id,
                            "--unattended",
                        ]
                    )

                self.assertEqual(rc, 0, out_buf.getvalue() + err_buf.getvalue())
                run_dir = self.repo / ".aw" / "records" / "runs" / run_id
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                st = state["startup_timings"]
                self.assertEqual(st["invocation_kind"], "start")
                self.assertIn("script_start_at", st)
                self.assertIn("first_output_at", st)
                self.assertIn("first_question_at", st)
                self.assertIn("first_execution_start_at", st)
                self.assertGreaterEqual(st["startup_to_first_output_seconds"], 0.0)
                self.assertGreater(
                    st["startup_to_first_question_seconds"],
                    st["startup_to_first_output_seconds"],
                )
                self.assertGreater(
                    st["startup_to_first_execution_seconds"],
                    st["startup_to_first_question_seconds"],
                )
                self.assertAlmostEqual(
                    st["first_output_to_first_question_seconds"],
                    st["startup_to_first_question_seconds"]
                    - st["startup_to_first_output_seconds"],
                    places=4,
                )
                self.assertAlmostEqual(
                    st["first_question_to_first_execution_seconds"],
                    st["startup_to_first_execution_seconds"]
                    - st["startup_to_first_question_seconds"],
                    places=4,
                )
                self.assertAlmostEqual(
                    st["first_output_to_first_execution_seconds"],
                    st["startup_to_first_execution_seconds"]
                    - st["startup_to_first_output_seconds"],
                    places=4,
                )

                evts = [
                    e
                    for e in _read_events(run_dir)
                    if e.get("event") == runner_shared.STARTUP_TIMINGS_EVENT
                ]
                self.assertEqual(len(evts), 1)
                self.assertEqual(evts[0]["invocation_kind"], "start")
                self.assertEqual(
                    evts[0]["startup_to_first_execution_seconds"],
                    st["startup_to_first_execution_seconds"],
                )

    def test_prepare_only_records_partial_timings_without_first_execution_and_resume_preserves_start(
        self,
    ) -> None:
        for host_mod, host_name in (
            (agy_runipd, "agy"),
            (oc_runipd, "oc"),
        ):
            with self.subTest(host=host_name):
                run_id = f"run-20261120T120500Z-{host_name}2"
                out_buf = io.StringIO()
                err_buf = io.StringIO()
                with (
                    mock.patch.object(sys, "stdout", out_buf),
                    mock.patch.object(sys, "stderr", err_buf),
                ):
                    rc = host_mod.main(
                        [
                            "start",
                            "st1001",
                            "--repo",
                            str(self.repo),
                            "--run-id",
                            run_id,
                            "--prepare-only",
                            "--unattended",
                        ]
                    )
                self.assertEqual(rc, 0, out_buf.getvalue() + err_buf.getvalue())
                run_dir = self.repo / ".aw" / "records" / "runs" / run_id
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                initial_st = state["startup_timings"]
                self.assertEqual(initial_st["invocation_kind"], "start")
                self.assertIn("startup_to_first_output_seconds", initial_st)
                self.assertNotIn("startup_to_first_question_seconds", initial_st)
                self.assertNotIn("startup_to_first_execution_seconds", initial_st)

                # Now resume the run and execute the item; original startup_timings must stay intact
                # while resume_startup_timings records the resume's own timings.
                def _fake_exec(
                    rd: Path, st_obj: dict[str, Any], item: dict[str, Any], **kw: Any
                ) -> None:
                    item["status"] = "executed"
                    host_mod.save_state(rd, st_obj)

                out_buf2 = io.StringIO()
                err_buf2 = io.StringIO()
                with (
                    mock.patch.object(sys, "stdout", out_buf2),
                    mock.patch.object(sys, "stderr", err_buf2),
                    mock.patch.object(host_mod, "execute_item", side_effect=_fake_exec),
                    mock.patch.object(host_mod, "install_stop_triggers"),
                ):
                    rc2 = host_mod.main(["resume", run_id, "--repo", str(self.repo)])
                self.assertEqual(rc2, 0, out_buf2.getvalue() + err_buf2.getvalue())
                state2 = json.loads(
                    (run_dir / "state.json").read_text(encoding="utf-8")
                )
                self.assertEqual(state2["startup_timings"], initial_st)
                self.assertEqual(len(state2["resume_startup_timings"]), 1)
                res_st = state2["resume_startup_timings"][0]
                self.assertEqual(res_st["invocation_kind"], "resume")
                self.assertIn("startup_to_first_execution_seconds", res_st)

                evts = [
                    e
                    for e in _read_events(run_dir)
                    if e.get("event") == runner_shared.STARTUP_TIMINGS_EVENT
                ]
                self.assertEqual(
                    [e["invocation_kind"] for e in evts], ["start", "resume"]
                )

    def test_cli_main_captures_start_time_before_driver_dispatch(self) -> None:
        observed_delay: list[float] = []

        def _fake_agy_main(argv: list[str] | None = None) -> int:
            start_mono, _ = runner_shared.resolve_invocation_start()
            observed_delay.append(time.monotonic() - start_mono)
            return 0

        orig_dispatch = cli._dispatch

        def _slow_dispatch(argv: Any) -> int:
            t0 = time.monotonic()
            while time.monotonic() - t0 < 0.02:
                time.sleep(0.005)
            return orig_dispatch(argv)

        with (
            mock.patch.object(cli, "_dispatch", side_effect=_slow_dispatch),
            mock.patch.object(agy_runipd, "main", side_effect=_fake_agy_main),
        ):
            rc = cli.main(["agy", "run", "--help"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(observed_delay), 1)
        self.assertGreaterEqual(observed_delay[0], 0.015)
        self.assertIsNone(cli.get_invocation_start())


class StartupTimingsAnalyticsAndAnalyzeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.runs_root = self.repo / ".aw" / "records" / "runs"
        self.runs_root.mkdir(parents=True)
        (self.repo / ".aw" / "config").mkdir(parents=True)

    def _write_run(
        self,
        run_id: str,
        *,
        startup_timings: dict[str, Any] | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> Path:
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state: dict[str, Any] = {
            "schema_version": 1,
            "run_id": run_id,
            "created_at": "2026-11-20T10:00:00+00:00",
            "updated_at": "2026-11-20T10:05:00+00:00",
            "repo": str(self.repo),
            "manifest": str(run_dir / "manifest.json"),
            "manifest_sha256": "a" * 64,
            "runbook": str(run_dir / "runbook.md"),
            "runbook_sha256": "b" * 64,
            "selectors": ["stset"],
            "set_sessions": {},
            "driver": {"id": "agy_runipd", "path": "agent_workflows/agy_runipd.py"},
            "options": {"model": "gemini-4-neon-high"},
            "queue": [
                {
                    "id6": "st1001",
                    "setid": "stset",
                    "action": "execute",
                    "status": "executed",
                    "attempts": [
                        {
                            "number": 1,
                            "started_at": "2026-11-20T10:00:10+00:00",
                            "ended_at": "2026-11-20T10:04:50+00:00",
                            "tokens": {"input": 100, "output": 50, "total": 150},
                            "cost": 0.25,
                        }
                    ],
                }
            ],
        }
        if startup_timings is not None:
            state["startup_timings"] = startup_timings
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        ev_lines = (
            events
            if events is not None
            else [{"at": "2026-11-20T10:00:00+00:00", "event": "run-created"}]
        )
        (run_dir / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in ev_lines) + "\n", encoding="utf-8"
        )
        return run_dir

    def test_privacy_boundary_accepts_numeric_startup_metrics_and_refuses_strings_and_nonfinite(
        self,
    ) -> None:
        good = {
            "run_id": "run-20261120T100000Z-1001",
            "startup_to_first_output_seconds": 1.25,
            "startup_to_first_question_seconds": 3.5,
            "startup_to_first_execution_seconds": 12.0,
            "first_output_to_first_question_seconds": 2.25,
            "first_question_to_first_execution_seconds": 8.5,
            "first_output_to_first_execution_seconds": 10.75,
        }
        projected = run_analytics_privacy.project_metric_facts(good)
        self.assertEqual(projected["startup_to_first_execution_seconds"], 12.0)

        for key in run_analytics.STARTUP_TIMING_METRIC_KEYS:
            with self.subTest(key=key, bad="string"):
                with self.assertRaises(run_analytics_privacy.PrivacyRefusal):
                    run_analytics_privacy.project_metric_facts(
                        {"run_id": "run-20261120T100000Z-1001", key: "/tmp/secret"}
                    )
            with self.subTest(key=key, bad="nan"):
                with self.assertRaises(run_analytics_privacy.PrivacyRefusal):
                    run_analytics_privacy.project_metric_facts(
                        {"run_id": "run-20261120T100000Z-1001", key: float("nan")}
                    )

    def test_legacy_run_omits_startup_keys_and_events_fallback_works(self) -> None:
        legacy = self._write_run("run-20261120T100000Z-9001")
        metric_legacy, _, _, _ = run_analytics.build_cache_facts(legacy)
        for key in run_analytics.STARTUP_TIMING_METRIC_KEYS:
            self.assertNotIn(key, metric_legacy)

        from_events = self._write_run(
            "run-20261120T100100Z-9002",
            startup_timings=None,
            events=[
                {"at": "2026-11-20T10:01:00+00:00", "event": "run-created"},
                {
                    "at": "2026-11-20T10:01:08+00:00",
                    "event": "run-startup-timings",
                    "invocation_kind": "start",
                    "startup_to_first_output_seconds": 1.5,
                    "startup_to_first_question_seconds": 4.0,
                    "startup_to_first_execution_seconds": 8.0,
                },
            ],
        )
        metric_ev, _, _, _ = run_analytics.build_cache_facts(from_events)
        self.assertAlmostEqual(metric_ev["startup_to_first_output_seconds"], 1.5)
        self.assertAlmostEqual(metric_ev["startup_to_first_question_seconds"], 4.0)
        self.assertAlmostEqual(metric_ev["startup_to_first_execution_seconds"], 8.0)
        # Missing stage-to-stage deltas are derived cleanly.
        self.assertAlmostEqual(metric_ev["first_output_to_first_question_seconds"], 2.5)
        self.assertAlmostEqual(
            metric_ev["first_question_to_first_execution_seconds"], 4.0
        )
        self.assertAlmostEqual(
            metric_ev["first_output_to_first_execution_seconds"], 6.5
        )

    def test_runs_analyze_and_runs_query_and_dashboard_surface_startup_timings(
        self,
    ) -> None:
        # 2 instrumented runs (one with question, one without) + 1 legacy run.
        self._write_run(
            "run-20261120T100000Z-1001",
            startup_timings={
                "invocation_kind": "start",
                "script_start_at": "2026-11-20T10:00:00+00:00",
                "first_output_at": "2026-11-20T10:00:02+00:00",
                "startup_to_first_output_seconds": 2.0,
                "first_question_at": "2026-11-20T10:00:05+00:00",
                "startup_to_first_question_seconds": 5.0,
                "first_output_to_first_question_seconds": 3.0,
                "first_execution_start_at": "2026-11-20T10:00:15+00:00",
                "startup_to_first_execution_seconds": 15.0,
                "first_output_to_first_execution_seconds": 13.0,
                "first_question_to_first_execution_seconds": 10.0,
            },
        )
        self._write_run(
            "run-20261120T101000Z-1002",
            startup_timings={
                "invocation_kind": "start",
                "script_start_at": "2026-11-20T10:10:00+00:00",
                "first_output_at": "2026-11-20T10:10:04+00:00",
                "startup_to_first_output_seconds": 4.0,
                "first_execution_start_at": "2026-11-20T10:10:25+00:00",
                "startup_to_first_execution_seconds": 25.0,
                "first_output_to_first_execution_seconds": 21.0,
            },
        )
        self._write_run("run-20261120T102000Z-1003", startup_timings=None)

        out_json = io.StringIO()
        err_json = io.StringIO()
        with (
            contextlib.redirect_stdout(out_json),
            contextlib.redirect_stderr(err_json),
        ):
            rc = cli.main(["runs", "analyze", "--json", "--dir", str(self.repo)])
        self.assertEqual(rc, 0, out_json.getvalue() + err_json.getvalue())
        payload = json.loads(out_json.getvalue())
        st_data = payload["data"]["startup_timings"]
        self.assertEqual(st_data["runs_analyzed"], 3)
        self.assertEqual(st_data["runs_with_startup_timings"], 2)
        self.assertEqual(
            st_data["metrics"]["startup_to_first_output_seconds"]["count"], 2
        )
        self.assertAlmostEqual(
            st_data["metrics"]["startup_to_first_output_seconds"]["median"], 3.0
        )
        self.assertEqual(
            st_data["metrics"]["startup_to_first_question_seconds"]["count"], 1
        )
        self.assertAlmostEqual(
            st_data["metrics"]["startup_to_first_question_seconds"]["median"], 5.0
        )
        self.assertEqual(
            st_data["metrics"]["startup_to_first_execution_seconds"]["count"], 2
        )
        self.assertAlmostEqual(
            st_data["metrics"]["startup_to_first_execution_seconds"]["median"], 20.0
        )

        # Verify analysis.json in the published report bundle carries startup_timings.
        analysis_rel = payload["data"]["report"]["analysis_json"]
        analysis_doc = json.loads(
            (self.repo / analysis_rel).read_text(encoding="utf-8")
        )
        self.assertEqual(analysis_doc["startup_timings"], st_data)

        # Verify human output includes the concise startup_median_s evidence line.
        out_human = io.StringIO()
        err_human = io.StringIO()
        with (
            contextlib.redirect_stdout(out_human),
            contextlib.redirect_stderr(err_human),
        ):
            rc_h = cli.main(["runs", "analyze", "--dir", str(self.repo)])
        self.assertEqual(rc_h, 0, out_human.getvalue() + err_human.getvalue())
        self.assertIn("startup_median_s", out_human.getvalue())
        self.assertIn("out=3.00s", out_human.getvalue())
        self.assertIn("q=5.00s", out_human.getvalue())
        self.assertIn("exec=20.00s", out_human.getvalue())

        # Verify `aw runs query metrics` aggregates startup timings and counts legacy run as missing.
        q_res = run_analytics_query.run_query(
            "metrics",
            metric="startup_to_first_execution_seconds",
            stat="median",
            repo=self.repo,
        )
        self.assertFalse(q_res.refused)
        self.assertAlmostEqual(q_res.payload["value"], 20.0)
        self.assertEqual(q_res.payload["sample_size"], 2)
        self.assertEqual(q_res.payload["missing_count"], 1)

        # Verify dashboard collect_rows includes startup_timings summary in info.
        _rows, info = run_dashboard.collect_rows(
            sorted(self.runs_root.iterdir()), repo=self.repo
        )
        self.assertEqual(info["startup_timings"]["runs_with_startup_timings"], 2)
        self.assertAlmostEqual(
            info["startup_timings"]["metrics"]["startup_to_first_execution_seconds"][
                "median"
            ],
            20.0,
        )


if __name__ == "__main__":
    unittest.main()
