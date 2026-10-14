# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for turn fix-it turns on crash, stall, or spawn failure (IPD ytas91, E-06).

Validates that:
1. Nonzero exit with no outcome and no work reaches a fix-it turn (item executed, turn_retry_attempts == 1).
2. Nonzero exit that left a commit (rung-5 path) reaches a fix-it turn, then succeeds.
3. Stall reaches a fix-it turn, then succeeds.
4. Turn-limit expiry records turn_failure_kind='turn-limit' and reaches a fix-it turn.
5. Missing host binary spends retry budget, then item ends failed-safely, the next queued item runs,
   and run_queue returns normally.
6. Budget 0 yields no fix-it turn (fails immediately).
7. Deliberate stop yields no fix-it turn.
8. Verification refusal is owned by verification send-back and not double-counted here.
9. Session plus lane resume re-enters the failed attempt's lane and resumes session, or falls back.
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared, runner_stop
from agent_workflows.runner_shared import (
    HostSpawnError,
    StallTimeout,
    VERIFICATION_REFUSED_KEY,
    recorded_outcome_path,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _make_test_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    (path / ".gitignore").write_text(".aw/state/\n.aw/worktrees/\n", encoding="utf-8")
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md", ".gitignore"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=path, check=True)
    return path


def _write_plan(
    repo: Path,
    *,
    id6: str = "tst001",
    setid: str = "tstset",
    status: str = "approved",
    order: int = 1,
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261007-{setid}-{order:02d}-{id6}-test-plan.ipd.md"
    content = f"""# IPD: Test Plan {id6}

- Date: 2026-10-07
- Kind: child
- Concern: Test concern.
- Scope: Test scope.
- Scope-Paths: agent_workflows/runner_shared.py
- Status: {status}
- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Priority: medium
- Work-Kind: feature
- Id: {id6}
- Item-Dependencies: none

## Workflow history
- 2026-10-07 {status} (test): created.

## Goal
Test goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
- None.
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_outcome_file(
    run_dir: Path, item: dict[str, Any], *, disposition: str = "executed"
) -> None:
    rec_p = recorded_outcome_path(run_dir, item)
    if rec_p is None:
        rec_p = (
            run_dir / "outcomes" / f"{item.get('position', 1):02d}-{item['id6']}.json"
        )
    rec_p.parent.mkdir(parents=True, exist_ok=True)
    outcome_data = {
        "schema_version": 1,
        "run_id": "test_run",
        "position": item.get("position", 1),
        "id6": item["id6"],
        "setid": item.get("setid", "tstset"),
        "disposition": disposition,
        "summary": "done",
        "starting_head": "0" * 40,
        "ending_head": "0" * 40,
        "commits": [],
        "files_changed": [],
        "tests": [],
        "decision_ids": [],
        "deferred_question_ids": [],
        "incomplete_requirements": [],
        "defect_report": {"state": "none-found", "findings": []},
        "partial_work_location": None,
        "recommended_next_action": "none",
        "pushed": False,
    }
    rec_p.write_text(json.dumps(outcome_data), encoding="utf-8")


def _patch_host_launcher(module: Any, launcher_fn: Any) -> Any:
    if module is oc_runipd:

        def _oc_wrapper(
            state: Any,
            run_dir: Any,
            item: Any,
            plan_path: Any,
            prompt_path: Any,
            attempt_no: Any,
            **kwargs: Any,
        ) -> Any:
            if item.get("id6") == "probe1":
                subprocess.Popen(
                    ["opencode", "--session", kwargs.get("resume_session") or "probe"]
                )
                log_p = Path(run_dir) / "logs" / "probe.log"
                return 0, None, log_p, ["opencode"]
            return launcher_fn(
                state, run_dir, item, plan_path, prompt_path, attempt_no, **kwargs
            )

        return mock.patch.object(oc_runipd, "run_opencode", _oc_wrapper)

    def _agy_wrapper(
        state: Any,
        run_dir: Any,
        item: Any,
        prompt_path: Any,
        attempt_no: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if item.get("id6") == "probe1":
            subprocess.Popen(["agy", "--session", kwargs.get("session_id") or "probe"])
            log_p = Path(run_dir) / "logs" / "probe.log"
            return 0, None, log_p, ["agy"]
        work_dir = kwargs.get("work_dir")
        root = Path(work_dir) if work_dir else Path(state.get("repo", "."))
        plan_path = runner_shared.queue_artifact_path(root, item)
        return launcher_fn(
            state, run_dir, item, plan_path, prompt_path, attempt_no, **kwargs
        )

    return mock.patch.object(agy_runipd, "run_agy_turn", _agy_wrapper)


def _passing_suite_check(
    repo_path: Any, run_id: Any, **kwargs: Any
) -> runner_shared.SuiteCheckResult:
    return runner_shared.SuiteCheckResult(
        passing=True,
        exit_code=0,
        summary="1 passed",
        reason="suite passed",
        cwd=str(repo_path),
        timeout_seconds=60.0,
        elapsed_seconds=0.1,
    )


class TestTurnFixIt(unittest.TestCase):
    """Guards for turn fix-it turns across crash, stall, turn-limit, and spawn failures (E-06)."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.suite_patchers = [
            mock.patch.object(runner_shared, "run_suite_check", _passing_suite_check),
            mock.patch.object(oc_runipd, "run_suite_check", _passing_suite_check),
            mock.patch.object(agy_runipd, "run_suite_check", _passing_suite_check),
        ]
        for p in self.suite_patchers:
            p.start()

    def tearDown(self) -> None:
        for p in reversed(self.suite_patchers):
            p.stop()
        self.temp_dir.cleanup()

    def _setup_run(
        self,
        module: Any,
        *,
        id6: str = "tst001",
        budget: int = 2,
        isolate: bool = False,
    ) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        repo = _make_test_repo(self.root / f"repo_{module.__name__}_{id6}")
        plan_file = _write_plan(repo, id6=id6)
        subprocess.run(["git", "add", ".aw"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "add plan"], cwd=repo, check=True)

        run_dir = self.root / f"run_{module.__name__}_{id6}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(exist_ok=True)
        (run_dir / "prompts").mkdir(exist_ok=True)
        (run_dir / "logs").mkdir(exist_ok=True)

        item = {
            "id6": id6,
            "action": "execute",
            "setid": "tstset",
            "position": 1,
            "status": "queued",
            "attempts": [],
            "configured_file": str(plan_file.relative_to(repo)),
        }
        state = {
            "run_id": f"run_{id6}",
            "repo": str(repo),
            "options": {
                "auto": True,
                "no_audit": True,
                "no_verify": True,
                "retry_budget": budget,
                "isolate_worktree": isolate,
            },
            "queue": [item],
        }
        module.save_state(run_dir, state)
        return run_dir, state, item

    def test_01_nonzero_exit_no_outcome_then_success(self) -> None:
        """Scenario 1: Nonzero exit with no outcome, then success on fix-it turn."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item = self._setup_run(mod, id6=f"nz1{host_label}")
                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("failed attempt 1\n", encoding="utf-8")

                call_count = [0]

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    call_count[0] += 1
                    if call_count[0] == 1:
                        # Attempt 1: crash with nonzero exit and no outcome
                        return 1, "ses-1", log_file, ["cmd"]
                    else:
                        # Attempt 2 (fix-it turn): write valid outcome and succeed
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "ses-1", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                self.assertEqual(rc, 0)
                final_state = mod.load_state(run_dir)
                final_item = final_state["queue"][0]
                self.assertEqual(final_item["status"], "executed")
                self.assertEqual(final_item.get("turn_retry_attempts"), 1)
                self.assertEqual(len(final_item.get("attempts", [])), 2)
                att1 = final_item["attempts"][0]
                self.assertEqual(att1.get("turn_failure_kind"), "no-outcome")
                self.assertEqual(att1.get("exit_code"), 1)
                att2 = final_item["attempts"][1]
                self.assertIsNone(att2.get("turn_failure_kind"))

    def test_02_nonzero_exit_with_commit_rung5_then_success(self) -> None:
        """Scenario 2: Nonzero exit that left a commit (rung-5 path), then success."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item = self._setup_run(mod, id6=f"nz2{host_label}")
                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("failed attempt with commit\n", encoding="utf-8")

                call_count = [0]

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    call_count[0] += 1
                    target_dir = Path(kw.get("work_dir") or st["repo"])
                    if call_count[0] == 1:
                        # Commit something to simulate rung 5
                        (target_dir / "work.txt").write_text(
                            "partial work\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "work.txt"], cwd=target_dir, check=True
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", "partial"],
                            cwd=target_dir,
                            check=True,
                        )
                        # Exit nonzero without outcome
                        return 2, "ses-1", log_file, ["cmd"]
                    else:
                        # Attempt 2: write outcome and succeed
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "ses-1", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                self.assertEqual(rc, 0)
                final_state = mod.load_state(run_dir)
                final_item = final_state["queue"][0]
                self.assertEqual(final_item["status"], "executed")
                self.assertEqual(final_item.get("turn_retry_attempts"), 1)
                att1 = final_item["attempts"][0]
                self.assertEqual(att1.get("turn_failure_kind"), "no-outcome")
                self.assertEqual(att1.get("exit_code"), 2)

    def test_03_stall_then_success(self) -> None:
        """Scenario 3: Stall then success on fix-it turn with session preserved."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item = self._setup_run(mod, id6=f"stl{host_label}")
                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("stall log\n", encoding="utf-8")

                call_count = [0]

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    call_count[0] += 1
                    if call_count[0] == 1:
                        raise StallTimeout(
                            "watchdog stall", session_id="stalled-ses-42"
                        )
                    else:
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "stalled-ses-42", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                self.assertEqual(rc, 0)
                final_state = mod.load_state(run_dir)
                final_item = final_state["queue"][0]
                self.assertEqual(final_item["status"], "executed")
                self.assertEqual(final_item.get("turn_retry_attempts"), 1)
                att1 = final_item["attempts"][0]
                self.assertEqual(att1.get("turn_failure_kind"), "stall")
                self.assertEqual(att1.get("session_id"), "stalled-ses-42")

    def test_04_turn_limit_expiry(self) -> None:
        """Scenario 4: Turn-limit expiry records turn_failure_kind='turn-limit' and retries."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item = self._setup_run(mod, id6=f"tlim{host_label}")
                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("turn limit log\n", encoding="utf-8")

                call_count = [0]

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    call_count[0] += 1
                    if call_count[0] == 1:
                        # Simulate reaper recording turn_bound_expiry during attempt
                        itm["turn_bound_expiry"] = {
                            "bound": "MAX_TURN_TIMEOUT",
                            "timeout_seconds": 30.0,
                        }
                        return 137, "ses-1", log_file, ["cmd"]
                    else:
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "ses-1", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                self.assertEqual(rc, 0)
                final_state = mod.load_state(run_dir)
                final_item = final_state["queue"][0]
                self.assertEqual(final_item["status"], "executed")
                att1 = final_item["attempts"][0]
                self.assertEqual(att1.get("turn_failure_kind"), "turn-limit")
                self.assertEqual(att1.get("bound"), "MAX_TURN_TIMEOUT")
                self.assertEqual(att1.get("timeout_seconds"), 30.0)
                self.assertNotIn("turn_bound_expiry", final_item)

    def test_05_missing_host_binary_exhausts_and_continues_next_item(self) -> None:
        """Scenario 5: Missing host binary exhausts retry budget, sets failed-safely, and next queued item runs."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item1 = self._setup_run(
                    mod, id6=f"spn1{host_label}", budget=1
                )
                repo = Path(state["repo"])
                plan_file2 = _write_plan(repo, id6=f"spn2{host_label}", order=2)
                item2 = {
                    "id6": f"spn2{host_label}",
                    "action": "execute",
                    "setid": "tstset",
                    "position": 2,
                    "status": "queued",
                    "attempts": [],
                    "configured_file": str(plan_file2.relative_to(repo)),
                }
                state["queue"].append(item2)
                mod.save_state(run_dir, state)

                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("ok\n", encoding="utf-8")

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    if itm["id6"].startswith("spn1"):
                        # Host binary not found
                        raise HostSpawnError("Cannot find 'nonexistent-host' on PATH")
                    else:
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "ses-2", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                # Queue ran normally; rc 1 due to failed item, but without crashing
                self.assertEqual(rc, 1)
                final_state = mod.load_state(run_dir)
                f_item1 = final_state["queue"][0]
                f_item2 = final_state["queue"][1]

                self.assertEqual(f_item1["status"], "failed-safely")
                self.assertEqual(
                    len(f_item1["attempts"]), 2
                )  # 1 initial + 1 retry = 2 attempts
                for att in f_item1["attempts"]:
                    self.assertEqual(att.get("turn_failure_kind"), "spawn-failure")
                    self.assertIn("nonexistent-host", att.get("spawn_error", ""))

                self.assertEqual(f_item2["status"], "executed")

    def test_06_budget_0_no_fix_it_turn(self) -> None:
        """Scenario 6: Budget 0 immediately fails item on first error without fix-it turn."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item = self._setup_run(
                    mod, id6=f"bg0{host_label}", budget=0
                )
                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("fail\n", encoding="utf-8")

                call_count = [0]

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    call_count[0] += 1
                    return 1, "ses-1", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                self.assertEqual(rc, 1)
                self.assertEqual(call_count[0], 1)
                final_state = mod.load_state(run_dir)
                final_item = final_state["queue"][0]
                self.assertEqual(final_item["status"], "failed-safely")
                self.assertEqual(len(final_item.get("attempts", [])), 1)

    def test_07_deliberate_stop_no_fix_it_turn(self) -> None:
        """Scenario 7: Deliberate operator stop yields no fix-it turn."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                run_dir, state, item = self._setup_run(
                    mod, id6=f"stp{host_label}", budget=2
                )

                def fake_turn(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    raise runner_stop.StopNowForce(level=4, requester="operator-test")

                with _patch_host_launcher(mod, fake_turn), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    with self.assertRaises(runner_stop.StopNowForce):
                        mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "interrupted")
                # Deliberate stop refusal
                retryable, why = runner_shared.turn_failure_is_retryable(
                    item, "interrupted"
                )
                self.assertFalse(retryable)
                self.assertIn("DELIBERATE OPERATOR STOP", why)

    def test_08_verification_refusal_not_double_counted(self) -> None:
        """Scenario 8: Verification refusal is refused by turn_failure_is_retryable and not double-counted."""
        item = {
            "id6": "ver001",
            "attempts": [
                {
                    "turn_failure_kind": "no-outcome",
                    VERIFICATION_REFUSED_KEY: True,
                }
            ],
        }
        retryable, why = runner_shared.turn_failure_is_retryable(item, "failed-safely")
        self.assertFalse(retryable)
        self.assertIn("REFUSED VERIFICATION", why)

    def test_09_session_and_lane_resume_including_fallback(self) -> None:
        """Scenario 9: Fix-it recovery resumes lane and session, and falls back if lane missing or no session."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                # Part A: Resume case
                run_dir, state, item = self._setup_run(
                    mod, id6=f"res{host_label}", budget=2, isolate=True
                )
                log_file = run_dir / "logs" / "attempt.log"
                log_file.write_text("log\n", encoding="utf-8")

                recorded_work_dirs: list[str | None] = []
                recorded_sessions: list[str | None] = []

                def fake_turn_resume(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    recorded_work_dirs.append(kw.get("work_dir"))
                    recorded_sessions.append(
                        kw.get("session_id") or kw.get("resume_session")
                    )
                    if len(recorded_work_dirs) == 1:
                        # Attempt 1: fail
                        return 1, "session-shared-99", log_file, ["cmd"]
                    else:
                        # Attempt 2: succeed
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "session-shared-99", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn_resume), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc = mod.run_queue(run_dir, retry_incomplete=False)

                self.assertEqual(rc, 0)
                final_state = mod.load_state(run_dir)
                final_item = final_state["queue"][0]
                self.assertEqual(final_item["status"], "executed")
                self.assertEqual(len(final_item["attempts"]), 2)
                att2 = final_item["attempts"][1]
                self.assertEqual(att2.get("fix_it_lane"), "resumed")
                # Both attempts ran in the SAME worktree directory and resumed session
                self.assertEqual(recorded_work_dirs[0], recorded_work_dirs[1])
                self.assertEqual(recorded_sessions[1], "session-shared-99")

                # Part B: Fallback case (missing prior session id)
                run_dir_fb, state_fb, item_fb = self._setup_run(
                    mod, id6=f"fbk{host_label}", budget=2, isolate=True
                )
                call_fb = [0]
                fb_work_dirs: list[str | None] = []

                def fake_turn_fallback(
                    st: Any,
                    rd: Any,
                    itm: Any,
                    plan_p: Any,
                    prompt_p: Any,
                    att_no: Any,
                    **kw: Any,
                ) -> tuple[int, str | None, Path, list[str]]:
                    call_fb[0] += 1
                    fb_work_dirs.append(kw.get("work_dir"))
                    if call_fb[0] == 1:
                        # Attempt 1: fail with NO session id
                        return 1, None, log_file, ["cmd"]
                    else:
                        _write_outcome_file(rd, itm, disposition="executed")
                        return 0, "new-session", log_file, ["cmd"]

                with _patch_host_launcher(mod, fake_turn_fallback), mock.patch.object(
                    mod, "driver_begin", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "driver_finalize", lambda *a, **k: (0, "ok")
                ), mock.patch.object(
                    mod, "assert_child_tool_identity", lambda *a, **k: None
                ), mock.patch("sys.stderr", new_callable=io.StringIO):
                    rc_fb = mod.run_queue(run_dir_fb, retry_incomplete=False)

                self.assertEqual(rc_fb, 0)
                final_state_fb = mod.load_state(run_dir_fb)
                final_item_fb = final_state_fb["queue"][0]
                self.assertEqual(final_item_fb["status"], "executed")
                att2_fb = final_item_fb["attempts"][1]
                self.assertTrue(str(att2_fb.get("fix_it_lane")).startswith("fresh:"))


if __name__ == "__main__":
    unittest.main()
