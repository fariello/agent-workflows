#!/usr/bin/env python3
"""Tests for hook refusals and combined-red suite fix-it turns (IPD w9nvq4).

Validates E-01 through E-06 and V-01 through V-06:
- E-01 / V-01: Hook refusal at finalize retryable, prompt with hook output, negative with DIAGNOSIS:.
- E-02 / V-02: Tag hook refusals at integrate_lane_branch (cause hook-refused, main without MERGE_HEAD, path redacted).
- E-03 / V-03: Combined red post-merge suite sent back with failing test IDs, warning on undeclared paths.
- E-04 / V-04: Per-kind counters, exhaustion reasons naming kinds, budget 0, counter isolation.
- E-05 / V-05: Both hosts (oc_runipd and agy_runipd) driven end-to-end with scripted hooks and runners.
- E-06 / V-06: Integration hook refusal sent back, prompt with hook output, successful retry and git log.
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "runner_shared": runner_shared,
}


def _make_script(path: pathlib.Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


class UnitHookAndSuiteFixItTests(unittest.TestCase):
    """Unit tests for classification, extraction, prompt building, and tagging."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_v01_finalize_refusal_is_retryable_positive_and_diagnosis_negative(
        self,
    ) -> None:
        """V-01: finalize_refusal_is_retryable admits hook refusals, but refuses DIAGNOSIS:."""
        hook_msg = (
            "error: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected "
            "in the coordinator worktree (hooks ran): HOOK_ERROR: trailing whitespace in plan.ipd.md); "
            "rolled back to pre-finalize state."
        )
        self.assertTrue(
            runner_shared.finalize_refusal_is_retryable(hook_msg),
            "Hook refusal must be recognized as retryable",
        )
        self.assertTrue(
            runner_shared.finalize_refusal_is_hook_refusal(hook_msg),
            "finalize_refusal_is_hook_refusal must be True",
        )

        # DIAGNOSIS: concurrent-writer signature must refuse retry
        diag_msg = (
            "error: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected "
            "in the coordinator worktree (hooks ran): git commit failed);\n"
            "DIAGNOSIS: concurrent writer detected in stash window"
        )
        self.assertFalse(
            runner_shared.finalize_refusal_is_retryable(diag_msg),
            "Refusal with DIAGNOSIS: must NOT be retryable",
        )
        self.assertFalse(
            runner_shared.finalize_refusal_is_hook_refusal(diag_msg),
            "finalize_refusal_is_hook_refusal must be False when DIAGNOSIS: present",
        )

    def test_v01_extract_hook_finalize_output_and_notice(self) -> None:
        """V-01: extract_hook_finalize_output extracts clean hook text; build_hook_finalize_notice formats notice."""
        hook_msg = (
            "error: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected "
            "in the coordinator worktree (hooks ran): HOOK_ERROR: trailing whitespace in plan.ipd.md); "
            "rolled back to pre-finalize state."
        )
        extracted = runner_shared.extract_hook_finalize_output(hook_msg)
        self.assertEqual(extracted, "HOOK_ERROR: trailing whitespace in plan.ipd.md")

        item = {
            "attempts": [
                {
                    "attempt": 1,
                    "finalize_refused": hook_msg,
                }
            ]
        }
        notice = runner_shared.build_hook_finalize_notice(item, recovery=True)
        self.assertIn("hook-refusal-finalize", notice)
        self.assertIn("HOOK_ERROR: trailing whitespace in plan.ipd.md", notice)
        self.assertIn("the hook ran on your plan file and the lifecycle commit", notice)
        self.assertIn(
            "apply the same fix to your lane and commit it with `aw commit`", notice
        )

        # recovery=False yields empty notice
        self.assertEqual(
            "", runner_shared.build_hook_finalize_notice(item, recovery=False)
        )

    def test_v02_tag_integration_hook_refusals_unit(self) -> None:
        """V-02: pre-merge-commit refusal tagged hook-refused, MERGE_HEAD cleared, path redacted; conflict tagged git-merge-conflict."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            repo = root / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
            )

            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "base.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            # Create lane branch
            base_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            branch = "aw/lane/tst001"
            subprocess.run(["git", "branch", branch], cwd=repo, check=True)
            wt = root / "wt-tst001"
            subprocess.run(
                ["git", "worktree", "add", "-q", str(wt), branch], cwd=repo, check=True
            )
            (wt / "file.txt").write_text("lane\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=wt, check=True)
            subprocess.run(["git", "commit", "-qm", "lane commit"], cwd=wt, check=True)

            from agent_workflows import worktree_lease

            handle = worktree_lease.WorktreeHandle(
                lane_id="tst001", path=wt, branch=branch, base_commit=base_head
            )

            # Advance main so that fast-forward is not possible and --no-ff runs
            (repo / "main_advance.txt").write_text("advance\n", encoding="utf-8")
            subprocess.run(["git", "add", "main_advance.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "main advance"], cwd=repo, check=True
            )

            # Install pre-merge-commit hook that rejects with an absolute machine path
            hooks_dir = repo / ".git" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            hook_file = hooks_dir / "pre-merge-commit"
            _make_script(
                hook_file,
                f"#!/usr/bin/env bash\n"
                f"echo 'HOOK_REFUSAL: rejecting merge from {td}/secret/path/tool.sh' >&2\n"
                f"exit 1\n",
            )

            ok, reason, kind = runner_shared.integrate_lane_branch(
                repo,
                handle,
                "tst001",
                lambda _d, _f: True,
                host_label="oc",
                run_checked=oc_runipd.run_checked,
                action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
            )
            self.assertFalse(ok)
            self.assertEqual(kind, runner_shared.INTEGRATION_REFUSAL_CONFLICT)

            cause, _, op_reason = runner_shared.read_integration_cause(reason)
            self.assertEqual(cause, runner_shared.INTEGRATION_CAUSE_HOOK_REFUSED)
            self.assertFalse(
                (repo / ".git" / "MERGE_HEAD").exists(),
                "MERGE_HEAD must not remain on main",
            )
            self.assertNotIn(str(td), reason, "Absolute path must be redacted")
            self.assertIn("HOOK_REFUSAL: rejecting merge", reason)

            # Remove hook and test genuine content conflict
            hook_file.unlink()
            (repo / "file.txt").write_text("main conflict\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "main writes conflicting file"],
                cwd=repo,
                check=True,
            )

            ok2, reason2, kind2 = runner_shared.integrate_lane_branch(
                repo,
                handle,
                "tst001",
                lambda _d, _f: True,
                host_label="oc",
                run_checked=oc_runipd.run_checked,
                action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
            )
            self.assertFalse(ok2)
            cause2, _, _ = runner_shared.read_integration_cause(reason2)
            self.assertEqual(cause2, runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT)

            # Check terminal_refusal_verdict for hook-refused
            verdict = runner_shared.terminal_refusal_verdict(kind, cause)
            self.assertIn("a git hook refused the integration commit", verdict)
            self.assertIn("THIS IS NOT A CONTENT CONFLICT between branches", verdict)

    def test_v04_per_kind_counters_and_exhaustion_unit(self) -> None:
        """V-04: finalize_retry_decision uses HOOK_FINALIZE_RETRY_COUNT_KEY, leaves FINALIZE_RETRY_COUNT_KEY unchanged."""
        hook_msg = (
            "error: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected "
            "in the coordinator worktree (hooks ran): HOOK_ERROR: fail); rolled back to pre-finalize state."
        )
        item: dict[str, Any] = {"id6": "wir001"}
        state = {"options": {"retry_budget": 1}}

        # First attempt (count 0 < 1)
        dec1 = runner_shared.finalize_retry_decision(item, state, hook_msg)
        self.assertTrue(dec1.retry)
        self.assertFalse(dec1.exhausted)
        self.assertEqual(item.get(runner_shared.FINALIZE_RETRY_COUNT_KEY, 0), 0)

        # Simulate one turn spent
        item[runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY] = 1
        dec2 = runner_shared.finalize_retry_decision(item, state, hook_msg)
        self.assertFalse(dec2.retry)
        self.assertTrue(dec2.exhausted)
        self.assertIn("a git hook refused the finalize commit", dec2.reason)
        # Verify pre-transition counter is completely untouched
        self.assertEqual(item.get(runner_shared.FINALIZE_RETRY_COUNT_KEY, 0), 0)

        # Check combined red verdict sentence update
        red_verdict = runner_shared.terminal_refusal_verdict(
            runner_shared.INTEGRATION_REFUSAL_CONFLICT,
            runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
        )
        self.assertIn("the run's fix-it budget was spent", red_verdict)
        self.assertNotIn("terminal on its first attempt", red_verdict)


class DriverHookAndSuiteFixItTests(unittest.TestCase):
    """End-to-end tests driving execute_item across BOTH hosts (oc_runipd and agy_runipd)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_driver_fixture(
        self, td: str, id6: str = "wir001", retry_budget: int = 2
    ) -> tuple[pathlib.Path, pathlib.Path, dict, dict]:
        repo = pathlib.Path(td) / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
        )
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")

        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        plan_text = _CONFORMING_PLAN.format(id6=id6)
        plan_text = plan_text.replace("Scope-Paths: src/", "Scope-Paths: clash.txt")
        plan = pending / f"20260828-demo-01-{id6}-demo.ipd.md"
        plan.write_text(plan_text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)

        item = {
            "position": 1,
            "id6": id6,
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
                "agy": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_audit": True,
                "no_verify": True,
                "retry_budget": retry_budget,
            },
        }
        return repo, run_dir, state, item

    def _passing_suite(self, repo: pathlib.Path) -> runner_shared.SuiteCheckResult:
        return runner_shared.SuiteCheckResult(
            passing=True,
            reason="ok",
            exit_code=0,
            summary="ok",
            cwd=str(repo),
            timeout_seconds=60.0,
            elapsed_seconds=0.1,
        )

    def test_v01_e01_hook_refusal_finalize_sendback_and_recovery(self) -> None:
        """V-01 / E-01: Hook refusal at finalize triggers fix-it turn with hook output in prompt, recovery integrates."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2
                )
                hooks_dir = repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)

                counter_file = pathlib.Path(td) / "hook_count.txt"
                counter_file.write_text("0", encoding="utf-8")

                # Install pre-commit hook that rejects only in coordinator worktree on attempt 1
                hook_script = (
                    "#!/usr/bin/env bash\n"
                    "branch=$(git branch --show-current 2>/dev/null || echo '')\n"
                    'if [[ "$branch" == aw/coordinator/* ]]; then\n'
                    f'    cnt=$(cat "{counter_file}" 2>/dev/null || echo 0)\n'
                    '    if [ "$cnt" -lt 1 ]; then\n'
                    f'        echo $((cnt + 1)) > "{counter_file}"\n'
                    '        echo "HOOK_FAIL: trailing whitespace in plan.ipd.md" >&2\n'
                    "        exit 1\n"
                    "    fi\n"
                    "fi\n"
                    "exit 0\n"
                )
                _make_script(hooks_dir / "pre-commit", hook_script)

                turn_count = 0
                prompts_delivered: list[str] = []

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal turn_count
                    turn_count += 1
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)

                    # Inspect the prompt passed to the turn
                    prompt_path = None
                    if runner == "oc_runipd" and len(args) >= 2:
                        prompt_path = args[1]
                    elif runner == "agy_runipd" and len(args) >= 1:
                        prompt_path = args[0]
                    if prompt_path and pathlib.Path(prompt_path).is_file():
                        prompts_delivered.append(
                            pathlib.Path(prompt_path).read_text(encoding="utf-8")
                        )

                    # Lane makes its commit
                    (target_dir / "clash.txt").write_text(
                        f"turn {turn_count}\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", f"turn {turn_count}"],
                        cwd=target_dir,
                        check=True,
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    # Turn 1: finalize is refused, item is marked queued for recovery
                    driver_mod.execute_item(run_dir, state, item, recovery=False)
                    self.assertEqual(item["status"], "queued")
                    self.assertEqual(
                        item.get(runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY), 1
                    )
                    self.assertEqual(
                        item.get(runner_shared.FINALIZE_RETRY_COUNT_KEY, 0), 0
                    )

                    # Turn 2: redispatch in recovery mode, prompt has hook output, finalize succeeds
                    driver_mod.execute_item(run_dir, state, item, recovery=True)

                self.assertEqual(
                    item["status"], "executed", "Item must execute cleanly on recovery"
                )
                self.assertEqual(
                    len(item["attempts"]),
                    2,
                    "Expected attempt 1 and recovery attempt 2",
                )
                self.assertGreaterEqual(turn_count, 2)

                # Delivered prompt on turn 2 must contain hook output and instruction
                self.assertTrue(len(prompts_delivered) >= 2)
                recovery_prompt = prompts_delivered[-1]
                self.assertIn(
                    "HOOK_FAIL: trailing whitespace in plan.ipd.md", recovery_prompt
                )
                self.assertIn(
                    "the hook ran on your plan file and the lifecycle commit",
                    recovery_prompt,
                )

    def test_v06_e06_integration_hook_refusal_sendback(self) -> None:
        """V-06 / E-06: Pre-merge-commit refusal sends back to agent, emits event, and integrates on retry."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2
                )
                hooks_dir = repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)

                counter_file = pathlib.Path(td) / "merge_hook_count.txt"
                counter_file.write_text("0", encoding="utf-8")

                # Install pre-merge-commit hook that rejects on attempt 1 with an absolute machine path
                hook_script = (
                    "#!/usr/bin/env bash\n"
                    f'cnt=$(cat "{counter_file}" 2>/dev/null || echo 0)\n'
                    'if [ "$cnt" -lt 1 ]; then\n'
                    f'    echo $((cnt + 1)) > "{counter_file}"\n'
                    f'    echo "HOOK_MERGE_FAIL: check failed on {td}/opt/verifier.sh" >&2\n'
                    "    exit 1\n"
                    "fi\n"
                    "exit 0\n"
                )
                _make_script(hooks_dir / "pre-merge-commit", hook_script)

                ask_count = 0
                prompts_delivered: list[str] = []

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    log_suffix = kwargs.get("log_suffix", "")

                    if log_suffix == "hook-refusal":
                        ask_count += 1
                        # Inspect the hook-refusal prompt
                        prompt_path = None
                        if runner == "oc_runipd" and len(args) >= 2:
                            prompt_path = args[1]
                        elif runner == "agy_runipd" and len(args) >= 1:
                            prompt_path = args[0]
                        if prompt_path and pathlib.Path(prompt_path).is_file():
                            prompts_delivered.append(
                                pathlib.Path(prompt_path).read_text(encoding="utf-8")
                            )

                        # Agent fixes the issue on the fix-it turn
                        (target_dir / "clash.txt").write_text(
                            "lane line fixed\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "clash.txt"], cwd=target_dir, check=True
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", "lane fix"],
                            cwd=target_dir,
                            check=True,
                        )
                        return 0, "ses1", str(rd / "hook-log"), [runner]

                    # Initial execution turn
                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    # Advance main non-conflictingly so fast-forward is not possible and --no-ff runs
                    (repo / "main_advance.txt").write_text(
                        "advance\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "main_advance.txt"], cwd=repo, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "main advance"], cwd=repo, check=True
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item["status"],
                    "executed",
                    "Item must execute after hook-refusal sendback",
                )
                self.assertEqual(
                    ask_count, 1, "Expected exactly 1 hook-refusal sendback"
                )
                self.assertEqual(
                    item.get(runner_shared.HOOK_INTEGRATION_RETRY_COUNT_KEY), 1
                )

                # Check events.jsonl for integration-hook-refusal-sent-back
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                event_names = [e.get("event") for e in events]
                self.assertIn("integration-hook-refusal-sent-back", event_names)

                # Check prompt contents: contains hook output and redacted path
                self.assertTrue(len(prompts_delivered) >= 1)
                self.assertIn("HOOK_MERGE_FAIL: check failed on", prompts_delivered[0])
                self.assertNotIn(
                    str(td), prompts_delivered[0], "Absolute path must be redacted"
                )

                # Check git log on main after retry
                log_res = subprocess.run(
                    ["git", "log", "--oneline", "-3"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertIn("lane fix", log_res.stdout)

    def test_v06_e06_integration_hook_refusal_negative_no_session(self) -> None:
        """V-06 / E-06 negative: With no session_id, hook refusal does not send back, falls through to fail-merge."""
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, item = self._setup_driver_fixture(td, retry_budget=2)
            hooks_dir = repo / ".git" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            _make_script(
                hooks_dir / "pre-merge-commit",
                "#!/usr/bin/env bash\necho 'HOOK_MERGE_FAIL: refused' >&2\nexit 1\n",
            )

            def fake_launcher_no_session(state_arg, rd, itm, *args, **kwargs):
                work_dir = kwargs.get("work_dir")
                target_dir = pathlib.Path(work_dir)
                (target_dir / "clash.txt").write_text("lane line\n", encoding="utf-8")
                subprocess.run(["git", "add", "clash.txt"], cwd=target_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "lane commit"], cwd=target_dir, check=True
                )

                (repo / "main_advance.txt").write_text("advance\n", encoding="utf-8")
                subprocess.run(["git", "add", "main_advance.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "main advance"], cwd=repo, check=True
                )

                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                # session_id is None
                return 0, None, str(rd / "log"), ["oc_runipd"]

            driver_mod = oc_runipd
            with mock.patch.object(
                driver_mod, "run_opencode", fake_launcher_no_session
            ), mock.patch.object(
                driver_mod, "run_suite_check", lambda *a, **k: self._passing_suite(repo)
            ), mock.patch.object(
                driver_mod,
                "make_integration_validation_runner",
                lambda *a, **k: (lambda _d, _f: True),
            ):
                driver_mod.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-merge")
            self.assertEqual(
                item.get(runner_shared.HOOK_INTEGRATION_RETRY_COUNT_KEY, 0), 0
            )

    def test_v03_e03_combined_red_sendback_and_warning_on_out_of_scope(self) -> None:
        """V-03 / E-03: Combined red triggers sendback listing failing tests, warning on undeclared paths, green re-run."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2
                )
                reval_calls = 0

                def reval_runner_factory(*a, **k):
                    def runner_fn(diff, files):
                        nonlocal reval_calls
                        reval_calls += 1
                        if reval_calls == 1:
                            runner_shared._record_revalidation(
                                item,
                                tree_id="tree_red",
                                passed=False,
                                reason="1 new failure",
                                failures=["tests/test_foo.py::test_failing_case"],
                                merged_files=["clash.txt"],
                                measured=True,
                                comparison=runner_shared.RevalidationComparison(
                                    judgement="regressed",
                                    new_ids=("tests/test_foo.py::test_failing_case",),
                                    reason="1 new failure",
                                    baseline_ids=(),
                                    merged_ids=(
                                        "tests/test_foo.py::test_failing_case",
                                    ),
                                ),
                            )
                            return False
                        runner_shared._record_revalidation(
                            item,
                            tree_id="tree_green",
                            passed=True,
                            reason="green",
                            failures=[],
                            merged_files=["clash.txt"],
                            measured=True,
                        )
                        return True

                    return runner_fn

                ask_count = 0
                prompts_delivered: list[str] = []

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    log_suffix = kwargs.get("log_suffix", "")

                    if log_suffix == "combined-red":
                        ask_count += 1
                        prompt_path = None
                        if runner == "oc_runipd" and len(args) >= 2:
                            prompt_path = args[1]
                        elif runner == "agy_runipd" and len(args) >= 1:
                            prompt_path = args[0]
                        if prompt_path and pathlib.Path(prompt_path).is_file():
                            prompts_delivered.append(
                                pathlib.Path(prompt_path).read_text(encoding="utf-8")
                            )

                        # Fix commit touches clash.txt AND an undeclared path extra.txt
                        (target_dir / "clash.txt").write_text(
                            "lane fixed line\n", encoding="utf-8"
                        )
                        (target_dir / "extra.txt").write_text(
                            "extra out-of-scope\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "clash.txt", "extra.txt"],
                            cwd=target_dir,
                            check=True,
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", "fix with undeclared path"],
                            cwd=target_dir,
                            check=True,
                        )
                        return 0, "ses1", str(rd / "red-log"), [runner]

                    # Initial execution turn
                    (target_dir / "clash.txt").write_text(
                        "lane initial line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "initial lane commit"],
                        cwd=target_dir,
                        check=True,
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    reval_runner_factory,
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item["status"],
                    "executed",
                    "Item must execute cleanly on green re-run",
                )
                self.assertEqual(ask_count, 1)
                self.assertEqual(
                    item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY), 1
                )

                # Check prompt contents: contains failing test ID
                self.assertTrue(len(prompts_delivered) >= 1)
                self.assertIn(
                    "tests/test_foo.py::test_failing_case", prompts_delivered[0]
                )

                # Check send-back record on attempt: warning about extra.txt outside Scope-Paths
                att = item["attempts"][0]
                sendback = att.get("combined_red_sendback")
                self.assertTrue(sendback)
                warning = sendback[0].get("warning", "")
                self.assertIn("extra.txt", warning)
                self.assertIn("outside declared Scope-Paths", warning)

                # Check event emitted
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                event_names = [e.get("event") for e in events]
                self.assertIn("combined-red-sent-back", event_names)

    def test_v03_e03_unmeasured_revalidation_negative_not_sent_back(self) -> None:
        """V-03 / E-03 negative: Unmeasured revalidation (harness fault) is terminal, not sent back."""
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, item = self._setup_driver_fixture(td, retry_budget=2)

            def unmeasured_runner_factory(*a, **k):
                def runner_fn(diff, files):
                    runner_shared._record_revalidation(
                        item,
                        tree_id="tree_unmeasured",
                        passed=False,
                        reason="harness fault",
                        failures=["harness fault"],
                        merged_files=["clash.txt"],
                        measured=False,
                    )
                    return False

                return runner_fn

            def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                work_dir = kwargs.get("work_dir")
                target_dir = pathlib.Path(work_dir)
                (target_dir / "clash.txt").write_text(
                    "lane initial\n", encoding="utf-8"
                )
                subprocess.run(["git", "add", "clash.txt"], cwd=target_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=target_dir, check=True
                )
                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                return 0, "ses1", str(rd / "log"), ["oc_runipd"]

            driver_mod = oc_runipd
            with mock.patch.object(
                driver_mod, "run_opencode", fake_launcher
            ), mock.patch.object(
                driver_mod, "run_suite_check", lambda *a, **k: self._passing_suite(repo)
            ), mock.patch.object(
                driver_mod,
                "make_integration_validation_runner",
                unmeasured_runner_factory,
            ):
                driver_mod.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "merge-retry")
            self.assertEqual(item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY, 0), 0)

    def test_v04_e04_budget_zero_and_exhaustion_with_kind_naming(self) -> None:
        """V-04 / E-04: Budget 0 gives 0 turns; budget 1 gives 1 turn, exhaustion reason names the kind."""
        # 1. Budget 0 with hook refusal
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, item = self._setup_driver_fixture(td, retry_budget=0)
            hooks_dir = repo / ".git" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            _make_script(
                hooks_dir / "pre-merge-commit",
                "#!/usr/bin/env bash\necho 'HOOK_MERGE_FAIL: permanent refusal' >&2\nexit 1\n",
            )

            ask_count = 0

            def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                nonlocal ask_count
                if kwargs.get("log_suffix") == "hook-refusal":
                    ask_count += 1
                work_dir = kwargs.get("work_dir")
                target_dir = pathlib.Path(work_dir)
                (target_dir / "clash.txt").write_text(
                    "lane initial\n", encoding="utf-8"
                )
                subprocess.run(["git", "add", "clash.txt"], cwd=target_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=target_dir, check=True
                )

                (repo / "main_advance.txt").write_text("advance\n", encoding="utf-8")
                subprocess.run(["git", "add", "main_advance.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "main advance"], cwd=repo, check=True
                )

                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                return 0, "ses1", str(rd / "log"), ["oc_runipd"]

            with mock.patch.object(
                oc_runipd, "run_opencode", fake_launcher
            ), mock.patch.object(
                oc_runipd, "run_suite_check", lambda *a, **k: self._passing_suite(repo)
            ), mock.patch.object(
                oc_runipd,
                "make_integration_validation_runner",
                lambda *a, **k: (lambda _d, _f: True),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-merge")
            self.assertEqual(ask_count, 0, "Budget 0 must yield 0 send-back turns")

        # 2. Budget 1 with continuous hook refusal -> 1 send-back turn, then exhaustion naming kind
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, item = self._setup_driver_fixture(td, retry_budget=1)
            hooks_dir = repo / ".git" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            _make_script(
                hooks_dir / "pre-merge-commit",
                "#!/usr/bin/env bash\necho 'HOOK_MERGE_FAIL: permanent refusal' >&2\nexit 1\n",
            )

            ask_count = 0

            def fake_launcher_b1(state_arg, rd, itm, *args, **kwargs):
                nonlocal ask_count
                if kwargs.get("log_suffix") == "hook-refusal":
                    ask_count += 1
                work_dir = kwargs.get("work_dir")
                target_dir = pathlib.Path(work_dir)
                (target_dir / "clash.txt").write_text(
                    f"lane initial {ask_count}\n", encoding="utf-8"
                )
                subprocess.run(["git", "add", "clash.txt"], cwd=target_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", f"initial {ask_count}"],
                    cwd=target_dir,
                    check=True,
                )

                (repo / "main_advance.txt").write_text(
                    f"advance {ask_count}\n", encoding="utf-8"
                )
                subprocess.run(["git", "add", "main_advance.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", f"main advance {ask_count}"],
                    cwd=repo,
                    check=True,
                )

                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                return 0, "ses1", str(rd / "log"), ["oc_runipd"]

            with mock.patch.object(
                oc_runipd, "run_opencode", fake_launcher_b1
            ), mock.patch.object(
                oc_runipd, "run_suite_check", lambda *a, **k: self._passing_suite(repo)
            ), mock.patch.object(
                oc_runipd,
                "make_integration_validation_runner",
                lambda *a, **k: (lambda _d, _f: True),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-merge")
            self.assertEqual(
                ask_count, 1, "Budget 1 must yield exactly 1 send-back turn"
            )
            self.assertEqual(
                item.get(runner_shared.HOOK_INTEGRATION_RETRY_COUNT_KEY), 1
            )

            # Refusal reason on item must name kind and exhausted budget
            deferral_reason = item.get("integration_deferral", "")
            self.assertIn(
                "a git hook refused the integration commit and the run's correction budget is exhausted",
                deferral_reason,
            )


if __name__ == "__main__":
    unittest.main()
