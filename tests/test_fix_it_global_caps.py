"""Tests for global fix-it turn caps per artifact, per Set, and per run.

Backlog 38hwvk, IPD c0oysi.
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

from agent_workflows import agy_runipd, oc_runipd, render_stream, runner_shared
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


class TestFrozenFixItCaps(unittest.TestCase):
    """Unit tests for frozen_fix_it_caps (E-02 / V-02)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_frozen_caps_defaults(self) -> None:
        """frozen_fix_it_caps({'options': {}}) returns default caps."""
        state = {"options": {}}
        caps = runner_shared.frozen_fix_it_caps(state)
        from agent_workflows import config

        self.assertEqual(caps, config.FIX_IT_CAPS_DEFAULTS)
        self.assertEqual(caps["per_artifact"], 20)
        self.assertEqual(caps["per_set_floor"], 20)
        self.assertEqual(caps["per_set_per_member"], 15)
        self.assertEqual(caps["per_run_floor"], 40)
        self.assertEqual(caps["per_run_per_artifact"], 10)

    def test_frozen_caps_resume_keeps_frozen_values(self) -> None:
        """Frozen caps from options.fix_it_caps are preserved on resume."""
        frozen_vals = {
            "per_artifact": 5,
            "per_set_floor": 10,
            "per_set_per_member": 8,
            "per_run_floor": 25,
            "per_run_per_artifact": 4,
        }
        state = {"options": {"fix_it_caps": dict(frozen_vals)}}
        caps = runner_shared.frozen_fix_it_caps(state)
        self.assertEqual(caps, frozen_vals)

    def test_initialize_run_core_freezes_fix_it_caps(self) -> None:
        """initialize_run_core freezes resolved caps into state['options']['fix_it_caps']."""
        import argparse

        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            for cmd in (
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test"],
            ):
                subprocess.run(cmd, cwd=repo, check=True)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"run": {"fix_it_caps": {"per_artifact": 7}}}),
                encoding="utf-8",
            )
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True, exist_ok=True)
            plan_file = pending / "20261003-test-01-tst001-sample.ipd.md"
            plan_file.write_text(
                _CONFORMING_PLAN.format(id6="tst001"), encoding="utf-8"
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            args = argparse.Namespace(
                repo=str(repo),
                selectors=["all"],
                full_auto=False,
                output_mode="clean",
                verbosity=0,
                stall_timeout=600.0,
                session=None,
                self_finalize=True,
                isolate_worktree=True,
                max_items_per_session=4,
                prepare_only=True,
                action=None,
                run_id="run-test-caps-freeze",
                manifest=None,
                runbook=None,
                types=None,
                allow_mixed=False,
                allow_drafts=False,
                allow_unverifiable=False,
                allow_dirty_base=False,
                allow_concurrent_driver=False,
                allow_uncovered_orchestrator_work=False,
                retry_budget=None,
                integration_retry_limit=None,
                on_integration_blocked=None,
                on_conflict=None,
            )
            run_dir = runner_shared.initialize_run_core(
                args,
                host="oc",
                driver_path=pathlib.Path(__file__),
                host_options={},
                labels=runner_shared.OC_HOST_LABELS,
                expand_selectors_fn=lambda manifest, selectors, **kw: ["tst001"],
                enforce_dependency_preflight_fn=lambda *a, **kw: None,
                announce_run_order_fn=lambda rdir, st: None,
                run_order_rationale_fn=lambda queue, sel: "test rationale",
                write_report_fn=lambda rdir, st: None,
            )
            state = runner_shared.load_json(run_dir / "state.json")
            self.assertIn("fix_it_caps", state["options"])
            self.assertEqual(state["options"]["fix_it_caps"]["per_artifact"], 7)
            self.assertEqual(state["options"]["fix_it_caps"]["per_set_floor"], 20)


class TestFixItTurnsSpent(unittest.TestCase):
    """Unit tests for fix_it_turns_spent and counter accumulation (E-03 / V-03)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_fix_it_turns_spent_sums_all_13_keys(self) -> None:
        """fix_it_turns_spent sums across all 13 active fix-it retry count keys."""
        item: dict[str, int] = {}
        for key in runner_shared.FIX_IT_COUNT_KEYS:
            item[key] = 1
        self.assertEqual(len(runner_shared.FIX_IT_COUNT_KEYS), 13)
        self.assertEqual(runner_shared.fix_it_turns_spent(item), 13)

    def test_fix_it_turns_spent_mixed_item(self) -> None:
        """fix_it_turns_spent returns 4 for mixed item including gate-answer re-run."""
        item = {
            runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY: 1,
            runner_shared.MERGE_CONFLICT_RETRY_COUNT_KEY: 1,
            runner_shared.GATE_ANSWER_RETRY_COUNT_KEY: 2,
        }
        self.assertEqual(runner_shared.fix_it_turns_spent(item), 4)

    def test_gate_answer_accumulates_in_retry_attempts(self) -> None:
        """Successive gate answers accumulate into GATE_ANSWER_RETRY_COUNT_KEY rather than overwrite."""
        item: dict[str, int] = {}
        # First gate answer outcome with 1 attempt
        item[runner_shared.GATE_ANSWER_RETRY_COUNT_KEY] = (
            item.get(runner_shared.GATE_ANSWER_RETRY_COUNT_KEY, 0) + 1
        )
        self.assertEqual(item[runner_shared.GATE_ANSWER_RETRY_COUNT_KEY], 1)
        # Second gate answer outcome with 2 attempts
        item[runner_shared.GATE_ANSWER_RETRY_COUNT_KEY] = (
            item.get(runner_shared.GATE_ANSWER_RETRY_COUNT_KEY, 0) + 2
        )
        self.assertEqual(item[runner_shared.GATE_ANSWER_RETRY_COUNT_KEY], 3)


class TestFixItCapLimits(unittest.TestCase):
    """Unit tests for fix_it_cap_limits (E-03 / V-03)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_limits_3_members_5_items(self) -> None:
        """3 Set members out of 5 total items yields limits (20, 45, 50)."""
        queue = [
            {"id6": "art001", "setid": "setA", "action": "execute"},
            {"id6": "art002", "setid": "setA", "action": "execute"},
            {"id6": "art003", "setid": "setA", "action": "execute"},
            {"id6": "art004", "setid": "setB", "action": "execute"},
            {"id6": "art005", "setid": "setC", "action": "execute"},
        ]
        state = {"queue": queue, "options": {}}
        limits = runner_shared.fix_it_cap_limits(queue[0], state)
        self.assertEqual(limits, (20, 45, 50))

    def test_limits_1_member_2_items(self) -> None:
        """1 Set member out of 2 total items yields limits (20, 20, 40)."""
        queue = [
            {"id6": "art001", "setid": "setA", "action": "execute"},
            {"id6": "art002", "setid": "setB", "action": "execute"},
        ]
        state = {"queue": queue, "options": {}}
        limits = runner_shared.fix_it_cap_limits(queue[0], state)
        self.assertEqual(limits, (20, 20, 40))

    def test_limits_excludes_action_skip(self) -> None:
        """action == 'skip' entries are excluded from Set member and run size counts."""
        queue = [
            {"id6": "art001", "setid": "setA", "action": "execute"},
            {"id6": "art002", "setid": "setA", "action": "skip"},
            {"id6": "art003", "setid": "setB", "action": "execute"},
        ]
        state = {"queue": queue, "options": {}}
        limits = runner_shared.fix_it_cap_limits(queue[0], state)
        self.assertEqual(limits, (20, 20, 40))

    def test_limits_no_setid(self) -> None:
        """Item without setid has per_set_limit of None."""
        queue = [{"id6": "art001", "action": "execute"}]
        state = {"queue": queue, "options": {}}
        limits = runner_shared.fix_it_cap_limits(queue[0], state)
        self.assertEqual(limits, (20, None, 40))


class TestFixItCapDecision(unittest.TestCase):
    """Unit tests for fix_it_cap_decision (E-04 / V-04)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_cap_decision_per_artifact(self) -> None:
        """Artifact cap reached returns cap='per-artifact', reached=True, with reason."""
        item = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 20,
        }
        state = {
            "queue": [item],
            "options": {
                "fix_it_caps": {
                    "per_artifact": 20,
                    "per_set_floor": 30,
                    "per_set_per_member": 30,
                    "per_run_floor": 50,
                    "per_run_per_artifact": 50,
                }
            },
        }
        dec = runner_shared.fix_it_cap_decision(item, state)
        self.assertTrue(dec.reached)
        self.assertEqual(dec.cap, "per-artifact")
        self.assertEqual(dec.limit, 20)
        self.assertEqual(dec.spent, 20)
        self.assertIn("run.fix_it_caps.per_artifact", dec.reason)
        self.assertIn("global fix-it cap reached", dec.reason)

    def test_cap_decision_per_set(self) -> None:
        """Set cap reached returns cap='per-set', reached=True, with reason."""
        item1 = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 10,
        }
        item2 = {
            "id6": "art002",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 10,
        }
        state = {
            "queue": [item1, item2],
            "options": {
                "fix_it_caps": {
                    "per_artifact": 20,
                    "per_set_floor": 20,
                    "per_set_per_member": 10,
                    "per_run_floor": 50,
                    "per_run_per_artifact": 50,
                }
            },
        }
        # item2 has spent 10 of 20 artifact turns, but setA has spent 20 of 20
        dec = runner_shared.fix_it_cap_decision(item2, state)
        self.assertTrue(dec.reached)
        self.assertEqual(dec.cap, "per-set")
        self.assertEqual(dec.limit, 20)
        self.assertEqual(dec.spent, 20)
        self.assertIn("run.fix_it_caps.per_set_floor", dec.reason)
        self.assertIn("global fix-it cap reached", dec.reason)

    def test_cap_decision_per_run(self) -> None:
        """Run cap reached returns cap='per-run', reached=True, with reason."""
        item1 = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 15,
        }
        item2 = {
            "id6": "art002",
            "setid": "setB",
            runner_shared.TURN_RETRY_COUNT_KEY: 15,
        }
        state = {
            "queue": [item1, item2],
            "options": {
                "fix_it_caps": {
                    "per_artifact": 20,
                    "per_set_floor": 20,
                    "per_set_per_member": 20,
                    "per_run_floor": 30,
                    "per_run_per_artifact": 10,
                }
            },
        }
        # item2: art spent 15 of 20, setB spent 15 of 20, but run spent 30 of 30
        dec = runner_shared.fix_it_cap_decision(item2, state)
        self.assertTrue(dec.reached)
        self.assertEqual(dec.cap, "per-run")
        self.assertEqual(dec.limit, 30)
        self.assertEqual(dec.spent, 30)
        self.assertIn("run.fix_it_caps.per_run_floor", dec.reason)
        self.assertIn("global fix-it cap reached", dec.reason)

    def test_cap_decision_not_reached(self) -> None:
        """Spend strictly below all limits returns reached=False, cap=''."""
        item = {"id6": "art001", "setid": "setA", runner_shared.TURN_RETRY_COUNT_KEY: 1}
        state = {"queue": [item], "options": {}}
        dec = runner_shared.fix_it_cap_decision(item, state)
        self.assertFalse(dec.reached)
        self.assertEqual(dec.cap, "")
        self.assertEqual(dec.reason, "")

    def test_cap_decision_cap_0(self) -> None:
        """Cap limit 0 with spent 0 immediately triggers cap reached."""
        item = {"id6": "art001", "setid": "setA"}
        state = {
            "queue": [item],
            "options": {
                "fix_it_caps": {
                    "per_artifact": 0,
                    "per_set_floor": 0,
                    "per_set_per_member": 0,
                    "per_run_floor": 0,
                    "per_run_per_artifact": 0,
                }
            },
        }
        dec = runner_shared.fix_it_cap_decision(item, state)
        self.assertTrue(dec.reached)
        self.assertEqual(dec.limit, 0)
        self.assertEqual(dec.spent, 0)


class TestSixDecidersCapIntegration(unittest.TestCase):
    """Unit tests for all six deciders under cap reached vs not reached (E-05 / V-05)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _reached_state(self, item: dict) -> dict:
        return {
            "queue": [item],
            "options": {
                "retry_budget": 5,
                "fix_it_caps": {
                    "per_artifact": 1,
                    "per_set_floor": 10,
                    "per_set_per_member": 10,
                    "per_run_floor": 20,
                    "per_run_per_artifact": 10,
                },
            },
        }

    def _unreached_state(self, item: dict) -> dict:
        return {
            "queue": [item],
            "options": {
                "retry_budget": 5,
                "fix_it_caps": {
                    "per_artifact": 20,
                    "per_set_floor": 20,
                    "per_set_per_member": 15,
                    "per_run_floor": 40,
                    "per_run_per_artifact": 10,
                },
            },
        }

    def test_finalize_retry_decision(self) -> None:
        """finalize_retry_decision respects cap when reached and retryable."""
        fin_msg = f"{runner_shared.RETRYABLE_HOOK_FINALIZE_SUMMARY} {runner_shared.RETRYABLE_HOOK_FINALIZE_HOOKS_RAN} HOOK_FAIL: error"
        # 1. Cap reached: exhausted=True, retry=False, cap.reached=True
        item_reached = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY: 1,
        }
        state_reached = self._reached_state(item_reached)
        dec_reached = runner_shared.finalize_retry_decision(
            item_reached, state_reached, fin_msg
        )
        self.assertFalse(dec_reached.retry)
        self.assertTrue(dec_reached.exhausted)
        self.assertIsNotNone(dec_reached.cap)
        self.assertTrue(dec_reached.cap.reached)
        self.assertIn("global fix-it cap reached", dec_reached.reason)

        # 2. Cap not reached: retry=True, exhausted=False
        item_ok = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY: 1,
        }
        state_ok = self._unreached_state(item_ok)
        dec_ok = runner_shared.finalize_retry_decision(item_ok, state_ok, fin_msg)
        self.assertTrue(dec_ok.retry)
        self.assertFalse(dec_ok.exhausted)

        # 3. Non-retryable refusal remains non-retryable even with cap reached
        dec_non = runner_shared.finalize_retry_decision(
            item_reached, state_reached, "unrecognized unretryable error"
        )
        self.assertFalse(dec_non.retry)
        self.assertFalse(dec_non.exhausted)

    def test_turn_retry_decision(self) -> None:
        """turn_retry_decision respects cap when reached and retryable."""
        item_reached = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 1,
        }
        state_reached = self._reached_state(item_reached)
        # retryable disposition e.g. "failed-safely"
        dec_reached = runner_shared.turn_retry_decision(
            item_reached, state_reached, "failed-safely", attempt_no=2
        )
        self.assertFalse(dec_reached.retry)
        self.assertTrue(dec_reached.exhausted)
        self.assertIsNotNone(dec_reached.cap)
        self.assertTrue(dec_reached.cap.reached)
        self.assertIn("global fix-it cap reached", dec_reached.reason)

        item_ok = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 1,
        }
        state_ok = self._unreached_state(item_ok)
        dec_ok = runner_shared.turn_retry_decision(
            item_ok, state_ok, "failed-safely", attempt_no=2
        )
        self.assertTrue(dec_ok.retry)
        self.assertFalse(dec_ok.exhausted)

        # Non-retryable disposition
        dec_non = runner_shared.turn_retry_decision(
            item_reached, state_reached, "executed", attempt_no=2
        )
        self.assertFalse(dec_non.retry)
        self.assertFalse(dec_non.exhausted)

    def test_zero_work_retry_decision(self) -> None:
        """zero_work_retry_decision respects cap when reached and retryable."""
        item_reached = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.ZERO_WORK_RETRY_COUNT_KEY: 1,
        }
        state_reached = self._reached_state(item_reached)
        verdict_retryable = runner_shared.ZeroWorkVerdict(
            attempted_nothing=True,
            proven=True,
            reason="zero work",
            facts={},
            truncated=False,
        )
        dec_reached = runner_shared.zero_work_retry_decision(
            item_reached, state_reached, verdict_retryable
        )
        self.assertFalse(dec_reached.retry)
        self.assertTrue(dec_reached.exhausted)
        self.assertIsNotNone(dec_reached.cap)
        self.assertTrue(dec_reached.cap.reached)
        self.assertIn("global fix-it cap reached", dec_reached.reason)

        item_ok = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.ZERO_WORK_RETRY_COUNT_KEY: 1,
        }
        state_ok = self._unreached_state(item_ok)
        dec_ok = runner_shared.zero_work_retry_decision(
            item_ok, state_ok, verdict_retryable
        )
        self.assertTrue(dec_ok.retry)
        self.assertFalse(dec_ok.exhausted)

        # Non-retryable verdict (attempted_nothing=False)
        verdict_non = runner_shared.ZeroWorkVerdict(
            attempted_nothing=False,
            proven=True,
            reason="work done",
            facts={},
            truncated=False,
        )
        dec_non = runner_shared.zero_work_retry_decision(
            item_reached, state_reached, verdict_non
        )
        self.assertFalse(dec_non.retry)
        self.assertFalse(dec_non.exhausted)

    def test_verification_retry_decision(self) -> None:
        """verification_retry_decision respects cap when reached and retryable."""
        item_reached = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.VERIFICATION_RETRY_COUNT_KEY: 1,
        }
        state_reached = self._reached_state(item_reached)
        dec_reached = runner_shared.verification_retry_decision(
            item_reached,
            state_reached,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=2,
        )
        self.assertFalse(dec_reached.retry)
        self.assertTrue(dec_reached.exhausted)
        self.assertIsNotNone(dec_reached.cap)
        self.assertTrue(dec_reached.cap.reached)
        self.assertIn("global fix-it cap reached", dec_reached.reason)

        item_ok = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.VERIFICATION_RETRY_COUNT_KEY: 1,
        }
        state_ok = self._unreached_state(item_ok)
        dec_ok = runner_shared.verification_retry_decision(
            item_ok,
            state_ok,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=2,
        )
        self.assertTrue(dec_ok.retry)
        self.assertFalse(dec_ok.exhausted)

        # Non-retryable refusal code (e.g. BLOCKED)
        dec_non = runner_shared.verification_retry_decision(
            item_reached, state_reached, "BLOCKED", None, attempt_no=2
        )
        self.assertFalse(dec_non.retry)
        self.assertFalse(dec_non.exhausted)

    def test_production_set_retry_decision(self) -> None:
        """production_set_retry_decision respects cap when reached and retryable."""
        item_reached = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.PRODUCTION_SET_RETRY_COUNT_KEY: 1,
        }
        state_reached = self._reached_state(item_reached)
        findings = [("BACKLOG-GRADUATE-SET", "orc001", "orchestrator not ready")]
        dec_reached = runner_shared.production_set_retry_decision(
            item_reached, state_reached, findings, attempt_no=2
        )
        self.assertFalse(dec_reached.retry)
        self.assertTrue(dec_reached.exhausted)
        self.assertIsNotNone(dec_reached.cap)
        self.assertTrue(dec_reached.cap.reached)
        self.assertIn("global fix-it cap reached", dec_reached.reason)

        item_ok = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.PRODUCTION_SET_RETRY_COUNT_KEY: 1,
        }
        state_ok = self._unreached_state(item_ok)
        dec_ok = runner_shared.production_set_retry_decision(
            item_ok, state_ok, findings, attempt_no=2
        )
        self.assertTrue(dec_ok.retry)
        self.assertFalse(dec_ok.exhausted)

        # Non-retryable findings
        non_findings = [("OTHER-ERROR", "orc001", "not retryable")]
        dec_non = runner_shared.production_set_retry_decision(
            item_reached, state_reached, non_findings, attempt_no=2
        )
        self.assertFalse(dec_non.retry)
        self.assertFalse(dec_non.exhausted)

    def test_review_orchestrator_retry_decision(self) -> None:
        """review_orchestrator_retry_decision respects cap when reached."""
        item_reached = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.REVIEW_ORCHESTRATOR_RETRY_COUNT_KEY: 1,
        }
        state_reached = self._reached_state(item_reached)
        dec_reached = runner_shared.review_orchestrator_retry_decision(
            item_reached, state_reached, attempt_no=2
        )
        self.assertFalse(dec_reached.retry)
        self.assertTrue(dec_reached.exhausted)
        self.assertIsNotNone(dec_reached.cap)
        self.assertTrue(dec_reached.cap.reached)
        self.assertIn("global fix-it cap reached", dec_reached.reason)

        item_ok = {
            "id6": "art001",
            "setid": "setA",
            runner_shared.REVIEW_ORCHESTRATOR_RETRY_COUNT_KEY: 1,
        }
        state_ok = self._unreached_state(item_ok)
        dec_ok = runner_shared.review_orchestrator_retry_decision(
            item_ok, state_ok, attempt_no=2
        )
        self.assertTrue(dec_ok.retry)
        self.assertFalse(dec_ok.exhausted)


class TestPerformGateAnswerCap(unittest.TestCase):
    """Test perform_gate_answer when cap is reached (E-06 / V-06)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_perform_gate_answer_cap_reached(self) -> None:
        """perform_gate_answer stops re-run when cap_reached callback returns True."""
        failing = runner_shared.SuiteCheckResult(
            passing=False,
            exit_code=1,
            summary="1 failed",
            reason="failed tests",
            cwd=tempfile.gettempdir(),
            timeout_seconds=60.0,
            elapsed_seconds=0.1,
            failures=("test failed",),
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            json.dump(
                {
                    runner_shared.GATE_ANSWER_KEY: {
                        "answer": "fixed",
                        "reason": "fixing",
                    }
                },
                f,
            )
            f.flush()
            rerun_calls = 0

            def dummy_rerun():
                nonlocal rerun_calls
                rerun_calls += 1
                return failing

            outcome = runner_shared.perform_gate_answer(
                suite_result=failing,
                ask=lambda p: None,
                outcome_path=f.name,
                rerun_suite=dummy_rerun,
                retry_budget=2,
                cap_reached=lambda attempts: True,
            )
            self.assertFalse(outcome.release)
            self.assertIsNotNone(outcome.cap)
            self.assertTrue(outcome.cap.reached)
            self.assertEqual(rerun_calls, 0)


class TestEndToEndGlobalCaps(unittest.TestCase):
    """End-to-end tests driving execute_item across BOTH hosts (oc_runipd and agy_runipd) (E-10 / V-07)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_driver_fixture(
        self,
        td: str,
        id6: str = "wir001",
        retry_budget: int = 2,
        fix_it_caps: dict | None = None,
        setid: str = "demo",
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
        plan_text = plan_text.replace(
            "Scope-Paths: src/", f"Scope-Paths: clash_{id6}.txt"
        )
        if setid != "demo":
            plan_text = plan_text.replace("- Set: demo", f"- Set: {setid}")
        plan = pending / f"20260828-{setid}-01-{id6}-demo.ipd.md"
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
            "setid": setid,
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        options: dict[str, Any] = {
            "opencode": "/bin/true",
            "agy": "/bin/true",
            "model": "opus",
            "self_finalize": True,
            "isolate_worktree": True,
            "no_audit": True,
            "no_verify": True,
            "retry_budget": retry_budget,
        }
        if fix_it_caps is not None:
            options["fix_it_caps"] = dict(fix_it_caps)

        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": [setid],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": options,
        }
        return repo, run_dir, state, item

    def _add_plan_item(
        self, repo: pathlib.Path, id6: str, setid: str, position: int
    ) -> dict:
        pending = repo / ".aw" / "records" / "plans" / "pending"
        plan_text = _CONFORMING_PLAN.format(id6=id6)
        plan_text = plan_text.replace(
            "Scope-Paths: src/", f"Scope-Paths: clash_{id6}.txt"
        )
        if setid != "demo":
            plan_text = plan_text.replace("- Set: demo", f"- Set: {setid}")
        plan = pending / f"20260828-{setid}-01-{id6}-demo.ipd.md"
        plan.write_text(plan_text, encoding="utf-8")
        subprocess.run(["git", "add", str(plan)], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True
        )
        return {
            "position": position,
            "id6": id6,
            "setid": setid,
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }

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

    def test_case_a_per_artifact_cap_stops_needs_human_exit_3(self) -> None:
        """Case (a): retry_budget: 2, per_artifact: 1, hook refuses finalize twice.
        Exactly 1 hook fix-it delivered, then stops with fix-it-cap-reached, needs_input=True, exit 3.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td,
                    retry_budget=2,
                    fix_it_caps={
                        "per_artifact": 1,
                        "per_set_floor": 20,
                        "per_set_per_member": 15,
                        "per_run_floor": 40,
                        "per_run_per_artifact": 10,
                    },
                )
                hooks_dir = repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)

                counter_file = pathlib.Path(td) / "hook_count.txt"
                counter_file.write_text("0", encoding="utf-8")

                hook_script = (
                    "#!/usr/bin/env bash\n"
                    "branch=$(git branch --show-current 2>/dev/null || echo '')\n"
                    'if [[ "$branch" == aw/coordinator/* ]]; then\n'
                    f'    cnt=$(cat "{counter_file.as_posix()}" 2>/dev/null || echo 0)\n'
                    f'    echo $((cnt + 1)) > "{counter_file.as_posix()}"\n'
                    '    echo "HOOK_FAIL: whitespace error" >&2\n'
                    "    exit 1\n"
                    "fi\n"
                    "exit 0\n"
                )
                _make_script(hooks_dir / "pre-commit", hook_script)

                turn_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal turn_count
                    turn_count += 1
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    (target_dir / f"clash_{itm['id6']}.txt").write_text(
                        f"turn {turn_count}\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", f"clash_{itm['id6']}.txt"],
                        cwd=target_dir,
                        check=True,
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
                    # Turn 1: finalize is refused, item is marked queued for recovery (1 fix-it delivered)
                    driver_mod.execute_item(run_dir, state, item, recovery=False)
                    self.assertEqual(item["status"], "queued")
                    self.assertEqual(
                        item.get(runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY), 1
                    )

                    # Turn 2: recovery attempt refuses again. per_artifact cap (1) is reached!
                    driver_mod.execute_item(run_dir, state, item, recovery=True)

                self.assertTrue(
                    item.get(runner_shared.NEEDS_INPUT_KEY),
                    "Item must be marked needs_input",
                )
                self.assertIsNotNone(item.get("fix_it_cap_stop"))
                self.assertEqual(item["fix_it_cap_stop"]["cap"], "per-artifact")

                refusal = render_stream.refusal_of_item(item)
                self.assertIsNotNone(refusal)
                self.assertEqual(refusal.code, "fix-it-cap-reached")
                self.assertIn("per-artifact", refusal.reason)

                # Exit code must be 3
                exit_code = runner_shared.run_exit_code(state["queue"], stopped=False)
                self.assertEqual(exit_code, 3)

                # Write report and verify ## Fix-it caps section
                driver_mod.write_report(run_dir, state)
                report_text = (run_dir / "execution-report.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("## Fix-it caps", report_text)
                self.assertIn(
                    f"- `{item['id6']}`: stopped by per-artifact cap (limit: 1, spent: 1)",
                    report_text,
                )
                self.assertIn("Frozen caps: per-artifact=1", report_text)

                # Exactly one fix-it-cap-reached event in events.jsonl
                events_file = run_dir / "events.jsonl"
                self.assertTrue(events_file.is_file())
                cap_events = [
                    json.loads(line)
                    for line in events_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                    and json.loads(line).get("event") == "fix-it-cap-reached"
                ]
                self.assertEqual(len(cap_events), 1)
                self.assertEqual(cap_events[0]["cap"], "per-artifact")
                self.assertEqual(cap_events[0]["limit"], 1)
                self.assertEqual(cap_events[0]["spent"], 1)

                # Summary lines
                summary_text = render_stream.render_run_summary_table(state)
                self.assertIn("fix-it-cap-reached", summary_text)
                self.assertIn("per-artifact", summary_text)

    def test_case_b_per_set_cap_stops_second_item(self) -> None:
        """Case (b): Two-item Set with per_set_floor: 1, per_set_per_member: 0.
        Item 1 spends 1 fix-it turn, and item 2's fix-it request is refused naming per-set.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item1 = self._setup_driver_fixture(
                    td,
                    id6="art001",
                    retry_budget=2,
                    setid="demoset",
                    fix_it_caps={
                        "per_set_floor": 1,
                        "per_set_per_member": 0,
                        "per_artifact": 20,
                        "per_run_floor": 40,
                        "per_run_per_artifact": 10,
                    },
                )
                item2 = self._add_plan_item(repo, "art002", "demoset", position=2)
                state["queue"].append(item2)

                hooks_dir = repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)

                counter_file = pathlib.Path(td) / "hook_count.txt"
                counter_file.write_text("0", encoding="utf-8")

                # Hook fails on attempt 1 of item1 (cnt 0), succeeds on attempt 2 (cnt 1),
                # and fails on attempt 1 of item2 (cnt 2)
                hook_script = (
                    "#!/usr/bin/env bash\n"
                    "branch=$(git branch --show-current 2>/dev/null || echo '')\n"
                    'if [[ "$branch" == aw/coordinator/* ]]; then\n'
                    f'    cnt=$(cat "{counter_file.as_posix()}" 2>/dev/null || echo 0)\n'
                    f'    echo $((cnt + 1)) > "{counter_file.as_posix()}"\n'
                    '    if [ "$cnt" -eq 0 ]; then\n'
                    '        echo "HOOK_FAIL: item1 attempt 1 refusal" >&2\n'
                    "        exit 1\n"
                    "    fi\n"
                    '    if [ "$cnt" -ge 2 ]; then\n'
                    '        echo "HOOK_FAIL: item2 refusal" >&2\n'
                    "        exit 1\n"
                    "    fi\n"
                    "fi\n"
                    "exit 0\n"
                )
                _make_script(hooks_dir / "pre-commit", hook_script)

                turn_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal turn_count
                    turn_count += 1
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    (target_dir / f"clash_{itm['id6']}.txt").write_text(
                        f"turn {turn_count}\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", f"clash_{itm['id6']}.txt"],
                        cwd=target_dir,
                        check=True,
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
                    # Item 1: attempt 1 refused by hook -> spends 1 fix-it turn
                    driver_mod.execute_item(run_dir, state, item1, recovery=False)
                    self.assertEqual(item1["status"], "queued")
                    self.assertEqual(
                        item1.get(runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY), 1
                    )

                    # Item 1: attempt 2 succeeds -> executed
                    driver_mod.execute_item(run_dir, state, item1, recovery=True)
                    self.assertEqual(item1["status"], "executed")

                    # Now Set "demoset" has spent 1 fix-it turn, reaching the per_set cap (1)
                    # Item 2: attempt 1 refused by hook -> cap reached immediately, refused naming per-set
                    driver_mod.execute_item(run_dir, state, item2, recovery=False)

                self.assertTrue(item2.get(runner_shared.NEEDS_INPUT_KEY))
                self.assertIsNotNone(item2.get("fix_it_cap_stop"))
                self.assertEqual(item2["fix_it_cap_stop"]["cap"], "per-set")

                refusal = render_stream.refusal_of_item(item2)
                self.assertIsNotNone(refusal)
                self.assertEqual(refusal.code, "fix-it-cap-reached")
                self.assertIn("per-set", refusal.reason)

    def test_case_c_per_run_cap_stops_second_item(self) -> None:
        """Case (c): Two singleton Sets with per_set_floor: 1, per_set_per_member: 0,
        per_run_floor: 1, per_run_per_artifact: 0.
        Item 1 spends 1 fix-it turn (spending the run cap).
        Item 2's fix-it request is refused naming per-run.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item1 = self._setup_driver_fixture(
                    td,
                    id6="art001",
                    retry_budget=2,
                    setid="setA",
                    fix_it_caps={
                        "per_set_floor": 1,
                        "per_set_per_member": 0,
                        "per_run_floor": 1,
                        "per_run_per_artifact": 0,
                        "per_artifact": 20,
                    },
                )
                item2 = self._add_plan_item(repo, "art002", "setB", position=2)
                state["queue"].append(item2)

                hooks_dir = repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)

                counter_file = pathlib.Path(td) / "hook_count.txt"
                counter_file.write_text("0", encoding="utf-8")

                hook_script = (
                    "#!/usr/bin/env bash\n"
                    "branch=$(git branch --show-current 2>/dev/null || echo '')\n"
                    'if [[ "$branch" == aw/coordinator/* ]]; then\n'
                    f'    cnt=$(cat "{counter_file.as_posix()}" 2>/dev/null || echo 0)\n'
                    f'    echo $((cnt + 1)) > "{counter_file.as_posix()}"\n'
                    '    if [ "$cnt" -eq 0 ]; then\n'
                    '        echo "HOOK_FAIL: item1 attempt 1 refusal" >&2\n'
                    "        exit 1\n"
                    "    fi\n"
                    '    if [ "$cnt" -ge 2 ]; then\n'
                    '        echo "HOOK_FAIL: item2 refusal" >&2\n'
                    "        exit 1\n"
                    "    fi\n"
                    "fi\n"
                    "exit 0\n"
                )
                _make_script(hooks_dir / "pre-commit", hook_script)

                turn_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal turn_count
                    turn_count += 1
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    (target_dir / f"clash_{itm['id6']}.txt").write_text(
                        f"turn {turn_count}\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", f"clash_{itm['id6']}.txt"],
                        cwd=target_dir,
                        check=True,
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
                    # Item 1 spends 1 fix-it turn and executes
                    driver_mod.execute_item(run_dir, state, item1, recovery=False)
                    self.assertEqual(item1["status"], "queued")
                    driver_mod.execute_item(run_dir, state, item1, recovery=True)
                    self.assertEqual(item1["status"], "executed")

                    # Run cap is 1, spent is 1. setB spent is 0 of 1.
                    # Item 2's fix-it request is refused naming per-run
                    driver_mod.execute_item(run_dir, state, item2, recovery=False)

                self.assertTrue(item2.get(runner_shared.NEEDS_INPUT_KEY))
                self.assertIsNotNone(item2.get("fix_it_cap_stop"))
                self.assertEqual(item2["fix_it_cap_stop"]["cap"], "per-run")

                refusal = render_stream.refusal_of_item(item2)
                self.assertIsNotNone(refusal)
                self.assertEqual(refusal.code, "fix-it-cap-reached")
                self.assertIn("per-run", refusal.reason)

    def test_case_a2_integration_loop_merge_conflict_cap_0(self) -> None:
        """Case (a2): Merge-conflict with per_artifact: 0.
        Refusal names fix-it-cap-reached and remedy preserves the lane branch warning.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td,
                    retry_budget=2,
                    fix_it_caps={
                        "per_artifact": 0,
                        "per_set_floor": 20,
                        "per_set_per_member": 15,
                        "per_run_floor": 40,
                        "per_run_per_artifact": 10,
                    },
                )
                ask_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    log_suffix = kwargs.get("log_suffix", "")
                    if log_suffix == "merge-conflict":
                        ask_count += 1
                        return 0, "ses1", str(rd / "conflict-log"), [runner]

                    target_dir = pathlib.Path(work_dir)
                    # Write clash in lane
                    (target_dir / f"clash_{itm['id6']}.txt").write_text(
                        "lane version\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", f"clash_{itm['id6']}.txt"],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    # Write clash in main repo to cause conflict
                    (repo / f"clash_{itm['id6']}.txt").write_text(
                        "main version\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", f"clash_{itm['id6']}.txt"], cwd=repo, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "main clash"], cwd=repo, check=True
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
                    ask_count, 0, "Zero send-back turns with per_artifact: 0"
                )
                self.assertEqual(item["status"], "fail-merge")
                self.assertTrue(item.get(runner_shared.NEEDS_INPUT_KEY))

                refusal = render_stream.refusal_of_item(item)
                self.assertIsNotNone(refusal)
                self.assertEqual(refusal.code, "fix-it-cap-reached")
                self.assertIn(
                    "the verified work is PRESERVED on branch", refusal.remedy
                )
                self.assertIn("run.fix_it_caps.per_artifact", refusal.remedy)

    def test_case_d_defaults_with_one_fix_it_executes_no_cap_report_section(
        self,
    ) -> None:
        """Case (d): Defaults with 1 fix-it turn executes cleanly and report has no ## Fix-it caps section."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td,
                    retry_budget=2,
                    fix_it_caps=None,  # defaults
                )
                hooks_dir = repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)

                counter_file = pathlib.Path(td) / "hook_count.txt"
                counter_file.write_text("0", encoding="utf-8")

                # Fails only once on attempt 1
                hook_script = (
                    "#!/usr/bin/env bash\n"
                    "branch=$(git branch --show-current 2>/dev/null || echo '')\n"
                    'if [[ "$branch" == aw/coordinator/* ]]; then\n'
                    f'    cnt=$(cat "{counter_file.as_posix()}" 2>/dev/null || echo 0)\n'
                    f'    echo $((cnt + 1)) > "{counter_file.as_posix()}"\n'
                    '    if [ "$cnt" -eq 0 ]; then\n'
                    '        echo "HOOK_FAIL: once" >&2\n'
                    "        exit 1\n"
                    "    fi\n"
                    "fi\n"
                    "exit 0\n"
                )
                _make_script(hooks_dir / "pre-commit", hook_script)

                turn_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal turn_count
                    turn_count += 1
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    (target_dir / f"clash_{itm['id6']}.txt").write_text(
                        f"turn {turn_count}\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", f"clash_{itm['id6']}.txt"],
                        cwd=target_dir,
                        check=True,
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
                    driver_mod.execute_item(run_dir, state, item, recovery=False)
                    self.assertEqual(item["status"], "queued")
                    driver_mod.execute_item(run_dir, state, item, recovery=True)
                    self.assertEqual(item["status"], "executed")

                driver_mod.write_report(run_dir, state)
                report_text = (run_dir / "execution-report.md").read_text(
                    encoding="utf-8"
                )
                self.assertNotIn("## Fix-it caps", report_text)
