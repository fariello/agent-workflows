"""Outcome tests for verification evidence refusals and remand (IPD t18l64).

Validates E-01 through E-05:
1. Pure verification retry classification and decision (allowlist, BLOCKED excluded, budget bounds, idempotency).
2. End-to-end verification sendback on both oc and agy hosts: item requeued, events appended, finalize not called.
3. Zero-budget behavior: item ends fail-verify with verifier refusal recorded.
4. CORRECTION_REQUIRED vs BLOCKED: CORRECTION_REQUIRED remands, BLOCKED fails terminal.
5. Stale-verdict clearing: pre-existing VERIFIED outcome file unlinked before spawn, preventing stale pass.
6. Recovery prompt delivery: prompt contains refusal code, remedy, attempt bound, command-string guidance, no leak.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared
from agent_workflows.render_stream import refusal_of_item
from tests import support
from tests.test_oc_runipd import _init_repo_with_conforming_plan

_HOSTS = (("oc", oc_runipd, "run_opencode"), ("agy", agy_runipd, "run_agy_turn"))


def _state_and_item(repo: Path, plan: Path, retry_budget: int = 2) -> tuple[dict, dict]:
    item = {
        "position": 1,
        "id6": "vrs001",
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
            "no_audit": False,
            "retry_budget": retry_budget,
        },
    }
    return state, item


def _fake_run_with_change_and_verifier(
    run_dir: Path,
    v_outcome: dict | None = None,
    *,
    write_nothing: bool = False,
    verifier_action: Any = None,
):
    """Worker turn commits a change in the lane; verifier turn writes v_outcome unless write_nothing."""

    def fake_run(state, rd, item, *_args, **kwargs):
        if kwargs.get("fresh_session") or kwargs.get("log_suffix") == "verify":
            if verifier_action is not None:
                if isinstance(verifier_action, type) and issubclass(
                    verifier_action, BaseException
                ):
                    raise verifier_action("verifier exception")
                if isinstance(verifier_action, BaseException):
                    raise verifier_action
                if isinstance(verifier_action, int):
                    return verifier_action, "vses", str(run_dir / "vlog"), ["x"]
                if callable(verifier_action):
                    return verifier_action(state, rd, item, *_args, **kwargs)
            if not write_nothing and v_outcome is not None:
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(json.dumps(v_outcome), encoding="utf-8")
            return 0, "vses", str(run_dir / "vlog"), ["x"]
        wt = Path(kwargs["work_dir"]) if kwargs.get("work_dir") else Path(state["repo"])
        (wt / "change.txt").write_text("change\n", encoding="utf-8")
        subprocess.run(["git", "add", "change.txt"], cwd=wt, check=True)
        subprocess.run(["git", "commit", "-qm", "commit change"], cwd=wt, check=True)
        (
            run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
        ).write_text(
            json.dumps(
                {
                    "disposition": "executed",
                    "pushed": False,
                    "defect_report": {"state": "none-found", "findings": []},
                    "incomplete_requirements": [],
                }
            ),
            encoding="utf-8",
        )
        return 0, "ses1", str(run_dir / "log"), ["x"]

    return fake_run


class VerificationRetryDecisionUnitTests(unittest.TestCase):
    """V-01: Unit tests for pure verification retry decision and accounting."""

    def test_decision_cases(self) -> None:
        state = {"options": {"retry_budget": 2}}
        item: dict = {"id6": "abc123"}

        # 1. Below budget -> retry=True
        dec = runner_shared.verification_retry_decision(
            item,
            state,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=1,
        )
        self.assertTrue(dec.retry)
        self.assertFalse(dec.exhausted)
        self.assertEqual(dec.attempts, 0)
        self.assertEqual(dec.budget, 2)
        self.assertEqual(dec.key, "abc123:verify-attempt-1")

        # 2. At budget -> exhausted=True
        item_at_budget = {
            "id6": "abc123",
            runner_shared.VERIFICATION_RETRY_COUNT_KEY: 2,
        }
        dec_ex = runner_shared.verification_retry_decision(
            item_at_budget,
            state,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=3,
        )
        self.assertFalse(dec_ex.retry)
        self.assertTrue(dec_ex.exhausted)
        self.assertEqual(dec_ex.attempts, 2)

        # 3. Budget 0 -> exhausted=True on first refusal
        state_0 = {"options": {"retry_budget": 0}}
        dec_0 = runner_shared.verification_retry_decision(
            item,
            state_0,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=1,
        )
        self.assertFalse(dec_0.retry)
        self.assertTrue(dec_0.exhausted)
        self.assertEqual(dec_0.attempts, 0)
        self.assertEqual(dec_0.budget, 0)

        # 4. verifier-declined with verify_disp="blocked" -> neither retry nor exhausted
        dec_blocked = runner_shared.verification_retry_decision(
            item,
            state,
            runner_shared.VERDICT_REFUSAL_CODE_DECLINED,
            runner_shared.VERIFY_DISP_BLOCKED,
            attempt_no=1,
        )
        self.assertFalse(dec_blocked.retry)
        self.assertFalse(dec_blocked.exhausted)
        self.assertIn("not retryable", dec_blocked.reason)

        # 5. verifier-declined with verify_disp="unverified" (CORRECTION_REQUIRED) -> retry=True
        dec_corr = runner_shared.verification_retry_decision(
            item,
            state,
            runner_shared.VERDICT_REFUSAL_CODE_DECLINED,
            runner_shared.VERIFY_DISP_UNVERIFIED,
            attempt_no=1,
        )
        self.assertTrue(dec_corr.retry)
        self.assertFalse(dec_corr.exhausted)

        # 6. Already spent key -> neither retry nor exhausted
        item_spent = {
            "id6": "abc123",
            runner_shared.VERIFICATION_RETRY_KEYS_KEY: ["abc123:verify-attempt-1"],
        }
        dec_spent = runner_shared.verification_retry_decision(
            item_spent,
            state,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=1,
        )
        self.assertFalse(dec_spent.retry)
        self.assertFalse(dec_spent.exhausted)
        self.assertIn("ALREADY recorded", dec_spent.reason)

        # 7. Deliberately stopped -> neither retry nor exhausted
        item_stopped = {"id6": "abc123", "stopped": {"stopped_deliberately": True}}
        dec_stop = runner_shared.verification_retry_decision(
            item_stopped,
            state,
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
            None,
            attempt_no=1,
        )
        self.assertFalse(dec_stop.retry)
        self.assertFalse(dec_stop.exhausted)
        self.assertIn("DELIBERATE OPERATOR STOP", dec_stop.reason)

    def test_verifier_transport_error_retry_decision_cases(self) -> None:
        state = {"options": {"retry_budget": 2}}
        item: dict = {"id6": "vte001"}

        # Predicate check
        retryable, why = runner_shared.verification_failure_is_retryable(
            item, runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, "unverified"
        )
        self.assertTrue(retryable)
        self.assertIn("verifier transport failure", why)

        # 1. Below budget -> retry=True
        dec = runner_shared.verification_retry_decision(
            item,
            state,
            runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
            "unverified",
            attempt_no=1,
        )
        self.assertTrue(dec.retry)
        self.assertFalse(dec.exhausted)
        self.assertEqual(dec.attempts, 0)
        self.assertEqual(dec.budget, 2)
        self.assertEqual(dec.key, "vte001:verify-attempt-1")

        # 2. At budget -> exhausted=True
        item_at_budget = {
            "id6": "vte001",
            runner_shared.VERIFICATION_RETRY_COUNT_KEY: 2,
        }
        dec_ex = runner_shared.verification_retry_decision(
            item_at_budget,
            state,
            runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
            "unverified",
            attempt_no=3,
        )
        self.assertFalse(dec_ex.retry)
        self.assertTrue(dec_ex.exhausted)
        self.assertEqual(dec_ex.attempts, 2)

        # 3. Budget 0 -> exhausted=True on first attempt
        state_0 = {"options": {"retry_budget": 0}}
        dec_0 = runner_shared.verification_retry_decision(
            item,
            state_0,
            runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
            "unverified",
            attempt_no=1,
        )
        self.assertFalse(dec_0.retry)
        self.assertTrue(dec_0.exhausted)
        self.assertEqual(dec_0.attempts, 0)
        self.assertEqual(dec_0.budget, 0)

        # 4. Global fix-it cap reached -> exhausted=True with cap attached
        item_capped = {
            "id6": "vte001",
            "setid": "setA",
            runner_shared.TURN_RETRY_COUNT_KEY: 20,
        }
        state_capped = {
            "queue": [item_capped],
            "options": {
                "retry_budget": 2,
                "fix_it_caps": {
                    "per_artifact": 20,
                    "per_set_floor": 30,
                    "per_set_per_member": 30,
                    "per_run_floor": 50,
                    "per_run_per_artifact": 50,
                },
            },
        }
        dec_cap = runner_shared.verification_retry_decision(
            item_capped,
            state_capped,
            runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
            "unverified",
            attempt_no=1,
        )
        self.assertFalse(dec_cap.retry)
        self.assertTrue(dec_cap.exhausted)
        self.assertIsNotNone(dec_cap.cap)
        self.assertTrue(dec_cap.cap.reached)
        self.assertIn("global fix-it cap reached", dec_cap.reason)

    def test_verifier_transport_refusal_text(self) -> None:
        code, reason, remedy = runner_shared.verifier_transport_refusal_text(
            "/opt/tools/bin/agy missing", exit_code=1
        )
        self.assertEqual(code, runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR)
        self.assertNotIn("/opt/tools/bin/agy", reason)
        self.assertIn("<path> missing", reason)
        self.assertIn("exit code 1", reason)
        self.assertIn("PRESERVED", remedy)
        self.assertIn("re-run", remedy)
        self.assertIn("do NOT re-run the plan from scratch", remedy)

    def test_cross_driver_object_identity(self) -> None:
        self.assertIs(
            oc_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
            runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
        )
        self.assertIs(
            agy_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
            runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR,
        )
        self.assertIs(
            oc_runipd.verifier_transport_refusal_text,
            runner_shared.verifier_transport_refusal_text,
        )
        self.assertIs(
            agy_runipd.verifier_transport_refusal_text,
            runner_shared.verifier_transport_refusal_text,
        )


class VerificationSendbackEndToEndTests(unittest.TestCase):
    """V-02..V-05: End-to-end drive of execute_item on both oc and agy hosts."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _execute(
        self,
        mod,
        spawn_name: str,
        v_outcome: dict | None,
        *,
        retry_budget: int = 2,
        write_nothing: bool = False,
        pre_write_file: dict | None = None,
        verifier_action: Any = None,
    ):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo = Path(temp.name) / "repo"
        plan = _init_repo_with_conforming_plan(repo, "vrs001")
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        state, item = _state_and_item(repo, plan, retry_budget=retry_budget)

        if pre_write_file is not None:
            (
                run_dir
                / "outcomes"
                / f"{item['position']:02d}-{item['id6']}-verification.json"
            ).write_text(json.dumps(pre_write_file), encoding="utf-8")

        finalize_calls: list = []
        real_finalize = mod.driver_finalize

        def spy_finalize(*a, **k):
            finalize_calls.append(a)
            return real_finalize(*a, **k)

        fake_run = _fake_run_with_change_and_verifier(
            run_dir,
            v_outcome,
            write_nothing=write_nothing,
            verifier_action=verifier_action,
        )

        with (
            mock.patch.object(mod, spawn_name, fake_run),
            mock.patch.object(mod, "driver_finalize", spy_finalize),
        ):
            mod.execute_item(run_dir, state, item, recovery=False)

        events_file = run_dir / "events.jsonl"
        events = []
        if events_file.is_file():
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        return repo, plan, item, finalize_calls, events

    def test_unevidenced_verification_remands_end_to_end_on_both_hosts(self) -> None:
        """E-05 (2): verifier-no-test-evidence with retry_budget 2 remands to queued on both hosts."""
        bad_evidence_outcome = {
            "verdict": "VERIFIED",
            "tests_run": [
                "tests/test_status_set.py::SetterRefusalRetryCommandTests::test_case_a"
            ],
        }
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls, events = self._execute(
                    mod, spawn, bad_evidence_outcome, retry_budget=2
                )
                self.assertEqual(item["status"], "queued")
                self.assertTrue(item.get("recovery_next"))
                self.assertEqual(
                    item.get(runner_shared.VERIFICATION_RETRY_COUNT_KEY), 1
                )
                self.assertEqual(
                    finalize_calls, [], "finalize must not be called when remanded"
                )

                sent_back_events = [
                    e for e in events if e.get("event") == "verification-sent-back"
                ]
                self.assertEqual(len(sent_back_events), 1)
                self.assertEqual(
                    sent_back_events[0]["refusal_code"], "verifier-no-test-evidence"
                )
                self.assertEqual(sent_back_events[0]["retry_attempts_used"], 1)
                self.assertEqual(sent_back_events[0]["retry_budget"], 2)

                # V-03 requirement: check turn_retry_skipped
                attempts = item.get("attempts") or []
                self.assertTrue(len(attempts) >= 1)
                self.assertIn("turn_retry_skipped", attempts[-1])

    def test_unevidenced_verification_exhausts_at_budget_zero(self) -> None:
        """E-05 (3): retry_budget 0 ends fail-verify with verifier-no-test-evidence refusal recorded."""
        bad_evidence_outcome = {
            "verdict": "VERIFIED",
            "tests_run": [
                "tests/test_status_set.py::SetterRefusalRetryCommandTests::test_case_a"
            ],
        }
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls, events = self._execute(
                    mod, spawn, bad_evidence_outcome, retry_budget=0
                )
                self.assertEqual(item["status"], "fail-verify")
                self.assertFalse(item.get("recovery_next", False))
                refusal = refusal_of_item(item)
                self.assertIsNotNone(refusal)
                self.assertEqual(refusal.code, "verifier-no-test-evidence")
                self.assertEqual(finalize_calls, [])
                sent_back_events = [
                    e for e in events if e.get("event") == "verification-sent-back"
                ]
                self.assertEqual(sent_back_events, [])

    def test_correction_required_remands_and_blocked_fails(self) -> None:
        """E-05 (4): CORRECTION_REQUIRED remands; BLOCKED ends fail-verify without send-back event."""
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label, verdict="CORRECTION_REQUIRED"):
                _, _, item_corr, fin_corr, events_corr = self._execute(
                    mod, spawn, {"verdict": "CORRECTION_REQUIRED"}, retry_budget=2
                )
                self.assertEqual(item_corr["status"], "queued")
                self.assertTrue(item_corr.get("recovery_next"))
                self.assertEqual(fin_corr, [])
                self.assertTrue(
                    any(e.get("event") == "verification-sent-back" for e in events_corr)
                )

            with self.subTest(host=label, verdict="BLOCKED"):
                _, _, item_blk, fin_blk, events_blk = self._execute(
                    mod, spawn, {"verdict": "BLOCKED"}, retry_budget=2
                )
                self.assertEqual(item_blk["status"], "fail-verify")
                self.assertFalse(item_blk.get("recovery_next", False))
                self.assertEqual(fin_blk, [])
                self.assertFalse(
                    any(e.get("event") == "verification-sent-back" for e in events_blk)
                )

    def test_stale_verdict_clearing(self) -> None:
        """E-05 (5): Pre-existing VERIFIED outcome file + verifier writing nothing yields verification-never-recorded."""
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                pre_write = {"verdict": "VERIFIED", "tests_run": ["python3 -m pytest"]}
                _, _, item, _, _ = self._execute(
                    mod,
                    spawn,
                    None,
                    retry_budget=0,
                    write_nothing=True,
                    pre_write_file=pre_write,
                )
                self.assertEqual(item["status"], "fail-verify")
                refusal = refusal_of_item(item)
                self.assertIsNotNone(refusal)
                self.assertEqual(
                    refusal.code, runner_shared.VERIFY_ABSENCE_NO_OUTCOME_FILE
                )
                self.assertNotEqual(item.get("verification_status"), "verified")

    def test_verifier_transport_error_spawn_exception_remands_on_both_hosts(
        self,
    ) -> None:
        """E-03 (e): spawn exceptions (FileNotFoundError, HostSpawnError) remand to queued on both hosts."""
        exceptions_to_test = [
            ("file_not_found", FileNotFoundError("/opt/tools/bin/missing_binary")),
            (
                "host_spawn_error",
                runner_shared.HostSpawnError(
                    "cannot spawn host binary: /usr/bin/missing"
                ),
            ),
        ]
        for exc_label, exc in exceptions_to_test:
            for label, mod, spawn in _HOSTS:
                with self.subTest(host=label, exc=exc_label):
                    repo, plan, item, finalize_calls, events = self._execute(
                        mod, spawn, None, retry_budget=2, verifier_action=exc
                    )
                    self.assertEqual(item["status"], "queued")
                    self.assertTrue(item.get("recovery_next"))
                    self.assertEqual(
                        item.get(runner_shared.VERIFICATION_RETRY_COUNT_KEY), 1
                    )
                    self.assertEqual(
                        finalize_calls, [], "finalize must not be called when remanded"
                    )

                    sent_back_events = [
                        e for e in events if e.get("event") == "verification-sent-back"
                    ]
                    self.assertEqual(len(sent_back_events), 1)
                    self.assertEqual(
                        sent_back_events[0]["refusal_code"], "verifier-transport-error"
                    )
                    self.assertEqual(sent_back_events[0]["retry_attempts_used"], 1)
                    self.assertEqual(sent_back_events[0]["retry_budget"], 2)

                    attempts = item.get("attempts") or []
                    self.assertTrue(len(attempts) >= 1)
                    last_att = attempts[-1]
                    self.assertIsNone(last_att.get("verify_exit_code"))
                    self.assertIsNotNone(last_att.get("verify_spawn_error"))
                    self.assertNotIn(
                        "/opt/tools/bin", str(last_att.get("verify_spawn_error"))
                    )
                    self.assertNotIn(
                        "/usr/bin", str(last_att.get("verify_spawn_error"))
                    )
                    refused = last_att.get(runner_shared.VERIFICATION_REFUSED_KEY)
                    self.assertIsNotNone(refused)
                    self.assertEqual(refused.get("code"), "verifier-transport-error")

    def test_verifier_transport_error_nonzero_exit_remands_on_both_hosts(self) -> None:
        """E-03 (e): nonzero exit without outcome file remands to queued on both hosts."""
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls, events = self._execute(
                    mod, spawn, None, retry_budget=2, verifier_action=1
                )
                self.assertEqual(item["status"], "queued")
                self.assertTrue(item.get("recovery_next"))
                self.assertEqual(
                    item.get(runner_shared.VERIFICATION_RETRY_COUNT_KEY), 1
                )
                self.assertEqual(
                    finalize_calls, [], "finalize must not be called when remanded"
                )

                sent_back_events = [
                    e for e in events if e.get("event") == "verification-sent-back"
                ]
                self.assertEqual(len(sent_back_events), 1)
                self.assertEqual(
                    sent_back_events[0]["refusal_code"], "verifier-transport-error"
                )
                self.assertEqual(sent_back_events[0]["retry_attempts_used"], 1)
                self.assertEqual(sent_back_events[0]["retry_budget"], 2)

                attempts = item.get("attempts") or []
                self.assertTrue(len(attempts) >= 1)
                last_att = attempts[-1]
                self.assertEqual(last_att.get("verify_exit_code"), 1)
                refused = last_att.get(runner_shared.VERIFICATION_REFUSED_KEY)
                self.assertIsNotNone(refused)
                self.assertEqual(refused.get("code"), "verifier-transport-error")

    def test_verifier_transport_error_exhausts_at_budget_zero(self) -> None:
        """E-03 (e): retry_budget 0 ends fail-verify with verifier-transport-error refusal recorded."""
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls, events = self._execute(
                    mod, spawn, None, retry_budget=0, verifier_action=1
                )
                self.assertEqual(item["status"], "fail-verify")
                self.assertFalse(item.get("recovery_next", False))
                refusal = refusal_of_item(item)
                self.assertIsNotNone(refusal)
                self.assertEqual(refusal.code, "verifier-transport-error")
                self.assertEqual(finalize_calls, [])
                sent_back_events = [
                    e for e in events if e.get("event") == "verification-sent-back"
                ]
                self.assertEqual(sent_back_events, [])

    def test_zero_exit_no_outcome_regression_guard(self) -> None:
        """E-03 (e): v_rc == 0 with no outcome file still records verification-never-recorded."""
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls, events = self._execute(
                    mod, spawn, None, retry_budget=2, verifier_action=0
                )
                self.assertEqual(item["status"], "queued")
                sent_back_events = [
                    e for e in events if e.get("event") == "verification-sent-back"
                ]
                self.assertEqual(len(sent_back_events), 1)
                self.assertEqual(
                    sent_back_events[0]["refusal_code"],
                    runner_shared.VERIFY_ABSENCE_NO_OUTCOME_FILE,
                )
                attempts = item.get("attempts") or []
                self.assertTrue(len(attempts) >= 1)
                last_att = attempts[-1]
                self.assertEqual(last_att.get("verify_exit_code"), 0)
                self.assertEqual(
                    last_att.get("verify_absence"),
                    runner_shared.VERIFY_ABSENCE_NO_OUTCOME_FILE,
                )


class RecoveryPromptNoticeTests(unittest.TestCase):
    """V-04: Test build_verification_refusal_notice, prompt formatting and lane containment."""

    def test_recovery_prompt_delivery(self) -> None:
        lane_dir = Path("/tmp/lane_root")
        run_dir = Path("/tmp/run_dir")
        plan_path = Path("plan.ipd.md")
        item = {
            "id6": "abc123",
            "position": 1,
            "setid": "demo",
            runner_shared.VERIFICATION_RETRY_COUNT_KEY: 1,
            "attempts": [
                {
                    "attempt_number": 1,
                    runner_shared.VERIFICATION_REFUSED_KEY: {
                        "code": runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
                        "reason": "tests_run has no command strings",
                        "remedy": "record actual commands run",
                        "verify_disp": "unverified",
                        "attempt": 1,
                        "budget": 2,
                    },
                }
            ],
        }
        state = {
            "run_id": "run-test",
            "options": {"retry_budget": 2},
        }

        # First attempt prompt has none of the refusal notice text
        first_prompt = runner_shared.build_prompt(
            item,
            state,
            run_dir,
            plan_path,
            recovery=False,
            lane_root=lane_dir,
            labels=runner_shared.OC_HOST_LABELS,
        )
        self.assertNotIn("Verification failed on the prior attempt", first_prompt)

        # Recovery prompt contains the refusal notice for both host label sets
        for labels in (runner_shared.OC_HOST_LABELS, runner_shared.AGY_HOST_LABELS):
            with self.subTest(host=labels.command):
                rec_prompt = runner_shared.build_prompt(
                    item,
                    state,
                    run_dir,
                    plan_path,
                    recovery=True,
                    lane_root=lane_dir,
                    labels=labels,
                )
                self.assertIn(
                    "## Verification failed on the prior attempt (verifier-no-test-evidence)",
                    rec_prompt,
                )
                self.assertIn(
                    "This is verification correction attempt 1 of 2", rec_prompt
                )
                self.assertIn("record actual commands run", rec_prompt)
                self.assertIn("must be the COMMAND STRINGS that were run", rec_prompt)
                self.assertEqual(
                    lane_containment.absolute_paths_outside_lane(rec_prompt, lane_dir),
                    [],
                )

        # lane_containment.prior_attempt_summary retains verification_refused
        attempt = item["attempts"][0]
        summary = lane_containment.prior_attempt_summary(attempt, lane_dir)
        self.assertIn("verification_refused", summary)
        self.assertEqual(
            summary["verification_refused"]["code"],
            runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED,
        )

    def test_recovery_prompt_delivery_verifier_transport_error(self) -> None:
        """E-03 (d): build_verification_refusal_notice and build_prompt render verifier-transport-error with rule count == 1."""
        lane_dir = Path("/tmp/lane_root")
        run_dir = Path("/tmp/run_dir")
        plan_path = Path("plan.ipd.md")
        code, reason, remedy = runner_shared.verifier_transport_refusal_text(
            "cannot spawn binary: /opt/tools/missing", exit_code=1
        )
        item = {
            "id6": "vte123",
            "position": 1,
            "setid": "demo",
            runner_shared.VERIFICATION_RETRY_COUNT_KEY: 1,
            "attempts": [
                {
                    "attempt_number": 1,
                    runner_shared.VERIFICATION_REFUSED_KEY: {
                        "code": code,
                        "reason": reason,
                        "remedy": remedy,
                        "verify_disp": "unverified",
                        "attempt": 1,
                        "budget": 2,
                    },
                }
            ],
        }
        state = {
            "run_id": "run-test",
            "options": {"retry_budget": 2},
        }

        notice = runner_shared.build_verification_refusal_notice(item, recovery=True)
        self.assertIn("verifier-transport-error", notice)
        self.assertIn("attempt 1 of 2", notice)
        self.assertNotIn("/opt/tools/missing", notice)

        for labels in (runner_shared.OC_HOST_LABELS, runner_shared.AGY_HOST_LABELS):
            with self.subTest(host=labels.command):
                rec_prompt = runner_shared.build_prompt(
                    item,
                    state,
                    run_dir,
                    plan_path,
                    recovery=True,
                    lane_root=lane_dir,
                    labels=labels,
                )
                self.assertIn(
                    "## Verification failed on the prior attempt (verifier-transport-error)",
                    rec_prompt,
                )
                self.assertIn(
                    "This is verification correction attempt 1 of 2", rec_prompt
                )
                self.assertEqual(
                    rec_prompt.count(runner_shared.FIX_IT_RULE_TEXT),
                    1,
                    "FIX_IT_RULE_TEXT must appear exactly once",
                )
                self.assertEqual(
                    lane_containment.absolute_paths_outside_lane(rec_prompt, lane_dir),
                    [],
                )
