"""End-to-end tests proving budget-only post-merge red defers and never sends back on either host.

Plan xc1xh9 (vtcqpf):
- Proves a budget-only post-merge revalidation red defers as unmeasured and is never sent back
  as combined-red to the agent on either host (oc_runipd and agy_runipd).
- Proves deferred integration retry re-measures and integrates without another agent turn.
- Proves an exhausted retry limit produces an honest unmeasured terminal refusal without
  claiming the suite was red.
- Proves a real failing suite with failing test ids still triggers the combined-red send-back loop.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}


def _git(cwd: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestBudgetOnlyCombinedRedE2E(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _passing_suite(self, repo: Path) -> runner_shared.SuiteCheckResult:
        return runner_shared.SuiteCheckResult(
            passing=True,
            reason="suite passed",
            exit_code=0,
            summary="745 passed",
            cwd=str(repo),
            timeout_seconds=60.0,
            elapsed_seconds=0.1,
            failures=(),
            budget_only=False,
        )

    def _setup_driver_fixture(
        self,
        td: str,
        id6: str = "wir001",
        retry_budget: int = 2,
        integration_retry_limit: int = 10,
    ) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
        repo = Path(td) / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        _git(repo, ["init", "-q", "-b", "main"])
        _git(repo, ["config", "user.email", "test@example.invalid"])
        _git(repo, ["config", "user.name", "Test"])
        _git(repo, ["config", "commit.gpgsign", "false"])

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
        _git(repo, ["add", "-A"])
        _git(repo, ["commit", "-qm", "initial"])

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
                "on_integration_blocked": "defer",
                "integration_retry_limit": integration_retry_limit,
            },
            "host_capabilities": {
                "descriptor": {
                    "supports_fresh_verifier_session": True,
                    "supports_session_resume": True,
                }
            },
        }
        return repo, run_dir, state, item

    def test_budget_only_red_defers_and_is_never_sent_back(self) -> None:
        """E-02: Budget-only post-merge red defers as unmeasured, never sent back, integrates on retry."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2, integration_retry_limit=10
                )

                budget_only_reval = runner_shared.SuiteCheckResult(
                    passing=False,
                    exit_code=1,
                    failures=(),
                    summary="745 passed",
                    budget_only=True,
                    reason="core-tier wall-time budget exceeded: 35.2s > 30.0s",
                    cwd=str(repo),
                    timeout_seconds=60.0,
                    elapsed_seconds=35.2,
                )
                current_reval = [budget_only_reval]
                reval_calls: list[Path] = []

                def fake_suite_check(
                    path: Path, run_id: str = ""
                ) -> runner_shared.SuiteCheckResult:
                    reval_dir = run_dir / "revalidation"
                    if str(path).startswith(str(reval_dir)):
                        reval_calls.append(Path(path))
                        return current_reval[0]
                    return self._passing_suite(repo)

                launcher_calls: list[str] = []

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = Path(work_dir) if work_dir else repo
                    log_suffix = kwargs.get("log_suffix", "")
                    launcher_calls.append(log_suffix)

                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    _git(target_dir, ["add", "clash.txt"])
                    _git(target_dir, ["commit", "-qm", "lane commit"])

                    outcome_path = (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    )
                    outcome_path.write_text(
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
                    driver_mod, "run_suite_check", fake_suite_check
                ), mock.patch.object(
                    runner_shared, "start_suite_baseline", return_value=(None, None)
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                # Observable state assertions on deferral
                self.assertEqual(
                    item["status"], runner_shared.INTEGRATION_DEFERRED_STATUS
                )
                self.assertEqual(
                    item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY, 0), 0
                )
                self.assertEqual(len(launcher_calls), 1)
                self.assertNotIn("combined-red", launcher_calls)

                events_path = run_dir / "events.jsonl"
                if events_path.exists():
                    events = [
                        json.loads(line)
                        for line in events_path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                    event_names = [e.get("event") for e in events]
                    self.assertNotIn("combined-red-sent-back", event_names)

                self.assertIs(
                    item[runner_shared.REVALIDATION_CACHE_KEY]["measured"], False
                )
                self.assertEqual(
                    item["integration_ladder"]["kind"],
                    runner_shared.INTEGRATION_REFUSAL_UNMEASURED,
                )
                self.assertIs(item["integration_ladder"]["deferrable"], True)
                self.assertIn("budget", item["integration_deferral"])
                self.assertNotIn("no test ids recorded", item["integration_deferral"])

                # Switch revalidation to passing and retry without clearing the cache
                current_reval[0] = self._passing_suite(repo)

                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod, "run_suite_check", fake_suite_check
                ), mock.patch.object(
                    runner_shared, "start_suite_baseline", return_value=(None, None)
                ):
                    driver_mod.retry_deferred_integrations(run_dir, state)

                # Assertions on successful retry integration
                self.assertGreaterEqual(len(reval_calls), 2)
                self.assertEqual(item["status"], "executed")

                rc, out, _ = _git(repo, ["log", "main", "--name-only"])
                self.assertEqual(rc, 0)
                self.assertIn("clash.txt", out)
                self.assertEqual(len(launcher_calls), 1)

    def test_budget_only_red_exhausted_budget_does_not_claim_a_red_suite(self) -> None:
        """E-03: Budget-only red with retry_limit=0 is terminal, reports unmeasured, does not claim red suite."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2, integration_retry_limit=0
                )

                budget_only_reval = runner_shared.SuiteCheckResult(
                    passing=False,
                    exit_code=1,
                    failures=(),
                    summary="745 passed",
                    budget_only=True,
                    reason="core-tier wall-time budget exceeded: 35.2s > 30.0s",
                    cwd=str(repo),
                    timeout_seconds=60.0,
                    elapsed_seconds=35.2,
                )

                def fake_suite_check(
                    path: Path, run_id: str = ""
                ) -> runner_shared.SuiteCheckResult:
                    reval_dir = run_dir / "revalidation"
                    if str(path).startswith(str(reval_dir)):
                        return budget_only_reval
                    return self._passing_suite(repo)

                launcher_calls: list[str] = []

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = Path(work_dir) if work_dir else repo
                    log_suffix = kwargs.get("log_suffix", "")
                    launcher_calls.append(log_suffix)

                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    _git(target_dir, ["add", "clash.txt"])
                    _git(target_dir, ["commit", "-qm", "lane commit"])

                    outcome_path = (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    )
                    outcome_path.write_text(
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
                    driver_mod, "run_suite_check", fake_suite_check
                ), mock.patch.object(
                    runner_shared, "start_suite_baseline", return_value=(None, None)
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item["status"], runner_shared.INTEGRATION_BLOCKED_STATUS
                )
                self.assertEqual(
                    item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY, 0), 0
                )
                self.assertEqual(len(launcher_calls), 1)

                ladder_verdict = item["integration_ladder"]["verdict"]
                self.assertNotIn("it was RED", ladder_verdict)
                self.assertIn("could not MEASURE", ladder_verdict)

    def test_measured_red_with_failing_id_is_still_sent_back(self) -> None:
        """E-04: Real failing suite with failing test id triggers combined-red sendback and recovers."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2, integration_retry_limit=10
                )

                failing_reval = runner_shared.SuiteCheckResult(
                    passing=False,
                    exit_code=1,
                    failures=("FAILED tests/test_foo.py::test_failing_case - boom",),
                    summary="1 failed, 744 passed",
                    budget_only=False,
                    reason="1 test failed",
                    cwd=str(repo),
                    timeout_seconds=60.0,
                    elapsed_seconds=5.0,
                )
                current_reval = [failing_reval]
                prompts_delivered: list[str] = []
                launcher_calls: list[str] = []

                def fake_suite_check(
                    path: Path, run_id: str = ""
                ) -> runner_shared.SuiteCheckResult:
                    reval_dir = run_dir / "revalidation"
                    if str(path).startswith(str(reval_dir)):
                        return current_reval[0]
                    return self._passing_suite(repo)

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = Path(work_dir) if work_dir else repo
                    log_suffix = kwargs.get("log_suffix", "")
                    launcher_calls.append(log_suffix)

                    if log_suffix == "combined-red":
                        prompt_path = None
                        if runner == "oc_runipd" and len(args) >= 2:
                            prompt_path = args[1]
                        elif runner == "agy_runipd" and len(args) >= 1:
                            prompt_path = args[0]
                        if prompt_path and Path(prompt_path).is_file():
                            prompts_delivered.append(
                                Path(prompt_path).read_text(encoding="utf-8")
                            )

                        (target_dir / "clash.txt").write_text(
                            "lane fixed line\n", encoding="utf-8"
                        )
                        _git(target_dir, ["add", "clash.txt"])
                        _git(target_dir, ["commit", "-qm", "fix combined-red"])

                        current_reval[0] = self._passing_suite(repo)
                        return 0, "ses1", str(rd / "red-log"), [runner]

                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    _git(target_dir, ["add", "clash.txt"])
                    _git(target_dir, ["commit", "-qm", "lane commit"])

                    outcome_path = (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    )
                    outcome_path.write_text(
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
                    driver_mod, "run_suite_check", fake_suite_check
                ), mock.patch.object(
                    runner_shared, "start_suite_baseline", return_value=(None, None)
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY), 1
                )

                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                event_names = [e.get("event") for e in events]
                self.assertIn("combined-red-sent-back", event_names)

                self.assertTrue(len(prompts_delivered) >= 1)
                self.assertIn(
                    "tests/test_foo.py::test_failing_case", prompts_delivered[0]
                )
                self.assertEqual(item["status"], "executed")


if __name__ == "__main__":
    unittest.main()
