"""Behavioral tests for the pre-work suite baseline mode gate (IPD 9ec94f).

Pins the behavioral requirements:
(a) attempt_validates over the five option shapes:
    - validate: True -> True
    - validate: False -> False
    - no_verify: True (validate absent) -> False
    - no_audit: True (validate absent) -> False
    - neither present (default) -> True
(b) Validation ON (default): drive execute_item_core via oc_runipd.execute_item,
    asserting no suite-baseline-started event, exactly one suite-baseline-skipped
    event, and no attempt["suite_baseline_started"] key.
(c) Validation OFF (validate: False): drive execute_item_core via oc_runipd.execute_item
    with SUITE_CHECK_ARGV and run_suite_check patched, asserting suite-baseline-started
    then suite-baseline-collected with state: "completed".
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import oc_runipd, runner_shared
from tests import support
from tests.test_oc_runipd import _init_repo_with_conforming_plan


class SuiteBaselineModeGateTests(unittest.TestCase):
    """Behavioral tests for runner suite baseline launch gating."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        return run_dir

    def _oc_state_and_item(
        self, repo: Path, plan: Path, *, isolate: bool = True
    ) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "wir001",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": isolate,
                "no_audit": False,
            },
        }
        return state, item

    def _fake_oc_agent_commits_in_worktree(
        self,
        run_dir: Path,
        active_baselines: list[runner_shared.SuiteBaselineRun] | None = None,
    ):
        def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("fresh_session"):
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]

            target_dir = Path(work_dir) if work_dir else Path(state["repo"])
            (target_dir / "src").mkdir(parents=True, exist_ok=True)
            (target_dir / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=target_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=target_dir,
                check=True,
            )
            # Wait for any started detached baseline to drain before the runner
            # collects it, so collection never races the child under contention.
            for b_run in active_baselines or []:
                b_run._drain.join(timeout=10.0)
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def _read_events(self, run_dir: Path) -> list[dict]:
        events_file = run_dir / "events.jsonl"
        if not events_file.exists():
            return []
        return [
            json.loads(line)
            for line in events_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_attempt_validates_five_shapes(self) -> None:
        """Cell (a): attempt_validates matches the expected booleans across the five option shapes."""
        # 1. validate: True present -> True
        self.assertTrue(runner_shared.attempt_validates({"validate": True}))
        # 2. validate: False present -> False
        self.assertFalse(runner_shared.attempt_validates({"validate": False}))
        # 3. absent with no_verify True -> False
        self.assertFalse(runner_shared.attempt_validates({"no_verify": True}))
        # 4. absent with no_audit True -> False
        self.assertFalse(runner_shared.attempt_validates({"no_audit": True}))
        # 5. absent with neither -> True (default configuration)
        self.assertTrue(runner_shared.attempt_validates({}))

    def test_validation_on_skips_suite_baseline(self) -> None:
        """Cell (b): validation ON emits suite-baseline-skipped and records no started baseline."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan)
            fake_agent = self._fake_oc_agent_commits_in_worktree(run_dir)

            with mock.patch.object(oc_runipd, "run_opencode", fake_agent):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed")
            events = self._read_events(run_dir)
            event_names = [e.get("event") for e in events]

            # Assert no suite-baseline-started event
            self.assertNotIn("suite-baseline-started", event_names)
            # Assert exactly one suite-baseline-skipped event
            self.assertEqual(event_names.count("suite-baseline-skipped"), 1)

            skipped = [e for e in events if e.get("event") == "suite-baseline-skipped"][
                0
            ]
            self.assertEqual(skipped.get("id6"), item["id6"])
            self.assertEqual(skipped.get("attempt"), 1)
            self.assertEqual(
                skipped.get("reason"),
                (
                    "validation is ON; the verifier's verdict is this attempt's "
                    "trust signal and nothing collects a baseline"
                ),
            )

            att = item["attempts"][0]
            # Assert no attempt["suite_baseline_started"] key
            self.assertNotIn("suite_baseline_started", att)

    def test_validation_off_starts_and_collects_suite_baseline(self) -> None:
        """Cell (c): validation OFF (validate: False) starts and collects baseline."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan)
            state["options"]["validate"] = False
            active_baselines: list[runner_shared.SuiteBaselineRun] = []
            original_start = runner_shared.start_suite_baseline

            def tracking_start(*args, **kwargs):
                run, absent = original_start(*args, **kwargs)
                if run is not None:
                    active_baselines.append(run)
                return run, absent

            fake_agent = self._fake_oc_agent_commits_in_worktree(
                run_dir, active_baselines=active_baselines
            )

            fast_argv = (sys.executable, "-c", "print('1 passed')")
            fake_suite_result = runner_shared.SuiteCheckResult(
                passing=True,
                exit_code=0,
                summary="1 passed",
                reason="",
                cwd=str(repo),
                timeout_seconds=600.0,
                elapsed_seconds=0.01,
                failures=(),
            )

            with (
                mock.patch.object(oc_runipd, "run_opencode", fake_agent),
                mock.patch.object(oc_runipd, "SUITE_CHECK_ARGV", fast_argv),
                mock.patch.object(
                    oc_runipd, "run_suite_check", lambda r, rid: fake_suite_result
                ),
                mock.patch.object(
                    runner_shared, "start_suite_baseline", side_effect=tracking_start
                ),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed")
            events = self._read_events(run_dir)
            event_names = [e.get("event") for e in events]

            # Assert suite-baseline-started then suite-baseline-collected with state: "completed"
            self.assertIn("suite-baseline-started", event_names)
            self.assertIn("suite-baseline-collected", event_names)
            self.assertLess(
                event_names.index("suite-baseline-started"),
                event_names.index("suite-baseline-collected"),
            )

            collected = [
                e for e in events if e.get("event") == "suite-baseline-collected"
            ][0]
            self.assertEqual(collected.get("state"), "completed")

            att = item["attempts"][0]
            self.assertIn("suite_baseline_started", att)
            self.assertEqual(att.get("suite_baseline", {}).get("state"), "completed")
