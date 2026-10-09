"""Behavioral tests for the unified fix-it notice builder, prompt assembly, and rule deduplication (IPD mcbph5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import runner_shared as rs


class FixItNoticeBuilderTests(unittest.TestCase):
    """E-01 / V-01: Unit tests for build_fix_it_notice, bounds, redaction, and recovery contract."""

    KINDS_ORDERS_04_TO_07 = [
        "nonzero exit",
        "stall",
        "spawn failure",
        "hook refusal",
        "red suite",
        "out-of-scope",
        "untooled status change",
        "hook bypass",
    ]

    def test_builder_renders_all_five_parts_for_all_kinds(self) -> None:
        """Parts (1)-(5) are present in order for all Orders 04-07 kinds."""
        for kind in self.KINDS_ORDERS_04_TO_07:
            with self.subTest(kind=kind):
                evidence = f"Verbatim error output for failure kind: {kind}"
                notice = rs.build_fix_it_notice(
                    kind,
                    evidence,
                    attempt=1,
                    budget=3,
                    recovery=True,
                    include_rule=True,
                )

                # Part (1): kind line naming failure kind and "attempt n of N"
                self.assertIn(kind, notice)
                self.assertIn("attempt 1 of 3", notice)
                # Part (2): verbatim evidence
                self.assertIn(evidence, notice)
                # Part (3): fix-the-cause instruction
                self.assertIn(
                    "Fix what caused this. Do not change the gate, check, hook or test that refused to make it pass.",
                    notice,
                )
                # Part (4): maintainer judgement rule and proposal instruction
                self.assertIn(
                    "Changing a gate or an `aw` tool is normally the job of a plan scoped to change it.",
                    notice,
                )
                self.assertIn(
                    "record a `proposal` in your outcome file",
                    notice,
                )
                # Part (5): outcome-file reminder
                self.assertIn(
                    "Record your findings and disposition in your outcome file before exiting.",
                    notice,
                )

                # Parts must appear in order
                idx_part1 = notice.index(kind)
                idx_part2 = notice.index(evidence)
                idx_part3 = notice.index("Fix what caused this.")
                idx_part4 = notice.index("Changing a gate or an `aw` tool")
                idx_part5 = notice.index("Record your findings and disposition")
                self.assertTrue(
                    idx_part1 < idx_part2 < idx_part3 < idx_part4 < idx_part5
                )

    def test_non_recovery_returns_empty_string(self) -> None:
        """When recovery is False, returns empty string (first attempt is byte-identical)."""
        notice = rs.build_fix_it_notice(
            "hook refusal",
            "pre-commit hook refused",
            1,
            2,
            recovery=False,
            include_rule=True,
        )
        self.assertEqual(notice, "")

    def test_include_rule_false_omits_only_parts_3_and_4(self) -> None:
        """When include_rule is False, parts (3) and (4) are omitted while (1), (2), (5) remain."""
        evidence = "Hook failed with exit code 1"
        notice = rs.build_fix_it_notice(
            "hook refusal",
            evidence,
            1,
            2,
            recovery=True,
            include_rule=False,
        )
        self.assertIn("hook refusal", notice)
        self.assertIn("attempt 1 of 2", notice)
        self.assertIn(evidence, notice)
        self.assertIn("Record your findings and disposition", notice)
        self.assertNotIn("Fix what caused this.", notice)
        self.assertNotIn("Changing a gate or an `aw` tool", notice)
        self.assertNotIn(rs.FIX_IT_RULE_TEXT, notice)

    def test_overlong_evidence_is_elided_with_marker_and_pointer(self) -> None:
        """Evidence exceeding FIX_IT_EVIDENCE_BOUND is elided with marker and pointer."""
        long_evidence = "X" * (rs.FIX_IT_EVIDENCE_BOUND + 1500)
        notice = rs.build_fix_it_notice(
            "red suite",
            long_evidence,
            1,
            2,
            recovery=True,
        )
        self.assertIn(rs.FIX_IT_ELISION_MARKER, notice)
        self.assertIn("Prior attempt:", rs.FIX_IT_ELISION_MARKER)
        self.assertIn("outcome file", rs.FIX_IT_ELISION_MARKER)
        # Sliced evidence has bound length
        self.assertIn("X" * rs.FIX_IT_EVIDENCE_BOUND, notice)
        self.assertNotIn("X" * (rs.FIX_IT_EVIDENCE_BOUND + 1), notice)

    def test_absolute_path_in_evidence_is_redacted(self) -> None:
        """Absolute driver-side paths in evidence are redacted."""
        driver_path = "/opt/secret/dir/file.py"
        evidence = f"Error located at {driver_path}: line 123"
        notice = rs.build_fix_it_notice(
            "nonzero exit",
            evidence,
            1,
            2,
            recovery=True,
        )
        self.assertNotIn("/opt/secret", notice)
        self.assertIn("<path>", notice)


class ExistingNoticesRoutingTests(unittest.TestCase):
    """E-02 / V-02: Existing notices route through build_fix_it_notice and preserve distinctive text."""

    def test_stale_receipt_notice_routed(self) -> None:
        item = {
            "attempts": [
                {
                    "attempt": 1,
                    "budget": 2,
                    "finalize_refused": rs.RETRYABLE_STALE_RECEIPT_SUMMARY,
                }
            ]
        }
        notice = rs.build_stale_receipt_notice(item, recovery=True)
        self.assertIn("The plan text changed after `begin`", notice)
        self.assertIn("Change after begin:", notice)
        self.assertIn("Do NOT run `aw ipd begin` or `aw ipd finalize` yourself", notice)
        # Notice itself called with include_rule=False
        self.assertNotIn(rs.FIX_IT_RULE_TEXT, notice)
        # Recovery False returns ""
        self.assertEqual(rs.build_stale_receipt_notice(item, recovery=False), "")

    def test_correction_notice_routed(self) -> None:
        item = {
            "attempts": [
                {
                    "turn_correction": {
                        "attempt": 1,
                        "of": 2,
                        "failed_predicates": ["predicate_foo_passed"],
                    }
                }
            ]
        }
        notice = rs.build_correction_notice(item, recovery=True)
        self.assertIn("Bounded correction", notice)
        self.assertIn("attempt 1 of 2", notice)
        self.assertIn("predicate_foo_passed", notice)
        self.assertIn("Address ONLY the failed predicates", notice)
        self.assertNotIn(rs.FIX_IT_RULE_TEXT, notice)
        self.assertEqual(rs.build_correction_notice(item, recovery=False), "")

    def test_verification_refusal_notice_routed(self) -> None:
        item = {
            rs.VERIFICATION_RETRY_COUNT_KEY: 1,
            "attempts": [
                {
                    rs.VERIFICATION_REFUSED_KEY: {
                        "code": rs.VERIFY_REFUSAL_CODE_UNEVIDENCED,
                        "reason": "tests_run has no command strings",
                        "remedy": "record actual commands run",
                        "verify_disp": "unverified",
                        "attempt": 1,
                        "budget": 2,
                    }
                }
            ],
        }
        notice = rs.build_verification_refusal_notice(item, recovery=True)
        self.assertIn(
            "## Verification failed on the prior attempt (verifier-no-test-evidence)",
            notice,
        )
        self.assertIn("This is verification correction attempt 1 of 2", notice)
        self.assertIn("record actual commands run", notice)
        self.assertIn("must be the COMMAND STRINGS that were run", notice)
        self.assertNotIn(rs.FIX_IT_RULE_TEXT, notice)
        self.assertEqual(rs.build_verification_refusal_notice(item, recovery=False), "")


class PromptAssemblyTests(unittest.TestCase):
    """E-02 / E-03 / V-02 / V-03: Rule deduplication in build_prompt."""

    def _state_and_plan(self, td: str) -> tuple[dict, Path, Path, Path]:
        repo = Path(td)
        lane_root = repo / "lane"
        lane_root.mkdir()
        run_dir = repo / "run"
        run_dir.mkdir()
        plan_path = repo / "plan.ipd.md"
        plan_path.write_text("# IPD: test\n\n- Id: tst123\n", encoding="utf-8")
        state = {
            "run_id": "test-run",
            "repo": str(repo),
            "options": {"retry_budget": 2},
        }
        return state, lane_root, run_dir, plan_path

    def test_first_attempt_contains_rule_exactly_once(self) -> None:
        """First-attempt execute prompt has rule exactly once (in body copy)."""
        with tempfile.TemporaryDirectory() as td:
            state, lane_root, run_dir, plan_path = self._state_and_plan(td)
            item = {
                "id6": "tst123",
                "position": 1,
                "setid": "testset",
                "attempts": [],
            }
            prompt = rs.build_prompt(
                item,
                state,
                run_dir,
                plan_path,
                recovery=False,
                lane_root=lane_root,
                labels=rs.OC_HOST_LABELS,
            )
            self.assertEqual(prompt.count(rs.FIX_IT_RULE_TEXT), 1)
            self.assertIn(
                "Do not weaken checks, fabricate evidence, broaden approved\nscope, bypass lifecycle controls, discard unrelated work, or push.",
                prompt,
            )

    def test_recovery_prompt_with_multiple_notices_contains_rule_exactly_once(
        self,
    ) -> None:
        """Recovery prompt with both correction and stale receipt has rule exactly once."""
        with tempfile.TemporaryDirectory() as td:
            state, lane_root, run_dir, plan_path = self._state_and_plan(td)
            item = {
                "id6": "tst123",
                "position": 1,
                "setid": "testset",
                "attempts": [
                    {
                        "attempt": 1,
                        "turn_correction": {
                            "attempt": 1,
                            "of": 2,
                            "failed_predicates": ["pred_check_ok"],
                        },
                        "finalize_refused": rs.RETRYABLE_STALE_RECEIPT_SUMMARY,
                    }
                ],
            }
            prompt = rs.build_prompt(
                item,
                state,
                run_dir,
                plan_path,
                recovery=True,
                lane_root=lane_root,
                labels=rs.OC_HOST_LABELS,
            )
            # Rule appears exactly once
            self.assertEqual(prompt.count(rs.FIX_IT_RULE_TEXT), 1)
            # Both notice bodies are present
            self.assertIn("The plan text changed after `begin`", prompt)
            self.assertIn("Change after begin:", prompt)
            self.assertIn("Bounded correction", prompt)
            self.assertIn("pred_check_ok", prompt)

    def test_recovery_prompt_with_verification_refusal_contains_rule_once(self) -> None:
        """Recovery prompt with verification refusal has rule exactly once."""
        with tempfile.TemporaryDirectory() as td:
            state, lane_root, run_dir, plan_path = self._state_and_plan(td)
            item = {
                "id6": "tst123",
                "position": 1,
                "setid": "testset",
                rs.VERIFICATION_RETRY_COUNT_KEY: 1,
                "attempts": [
                    {
                        rs.VERIFICATION_REFUSED_KEY: {
                            "code": rs.VERIFY_REFUSAL_CODE_UNEVIDENCED,
                            "reason": "tests_run missing",
                            "remedy": "record actual commands",
                            "verify_disp": "unverified",
                            "attempt": 1,
                            "budget": 2,
                        }
                    }
                ],
            }
            prompt = rs.build_prompt(
                item,
                state,
                run_dir,
                plan_path,
                recovery=True,
                lane_root=lane_root,
                labels=rs.AGY_HOST_LABELS,
            )
            self.assertEqual(prompt.count(rs.FIX_IT_RULE_TEXT), 1)
            self.assertIn(
                "## Verification failed on the prior attempt (verifier-no-test-evidence)",
                prompt,
            )


class E05CorrectionTextsTests(unittest.TestCase):
    """E-05 / V-05: Tests for production, review, and merge-conflict texts."""

    def test_production_set_correction_prompt_contains_rule_once(self) -> None:
        findings = [("CODE1", "orch01", "obligation not covered")]
        decision = rs.ProductionSetRetryDecision(
            retry=True,
            exhausted=False,
            reason="retry",
            attempts=0,
            budget=2,
            key="key1",
        )
        prompt = rs.build_production_set_correction_prompt(
            {"id6": "prod01"},
            findings,
            Path("/tmp"),
            attempt_no=1,
            decision=decision,
        )
        self.assertEqual(prompt.count(rs.FIX_IT_RULE_TEXT), 1)
        self.assertIn("Correction Turn: Production Set Verification", prompt)
        self.assertIn("never delete the checklist", prompt)

    def test_review_orchestrator_correction_prompt_contains_rule_once(self) -> None:
        readiness = type("Readiness", (), {"ready": False, "findings": []})()
        decision = rs.ReviewOrchestratorRetryDecision(
            retry=True,
            exhausted=False,
            reason="retry",
            attempts=0,
            budget=2,
            key="key2",
        )
        prompt = rs.build_review_orchestrator_correction_prompt(
            {"id6": "orch01"},
            readiness,
            "to-review",
            1,
            decision,
        )
        self.assertEqual(prompt.count(rs.FIX_IT_RULE_TEXT), 1)
        self.assertIn("Correction Turn: Orchestrator Review for orch01", prompt)

    def test_merge_conflict_question_contains_rule_once(self) -> None:
        detail = {
            "shape": rs.CONFLICT_SHAPE_ADJACENCY_ONLY,
            "files": [{"path": "file1.py", "shape": rs.CONFLICT_SHAPE_ADJACENCY_ONLY}],
        }
        prompt = rs.merge_conflict_question(detail, main_tip="abcdef123456")
        self.assertEqual(prompt.count(rs.FIX_IT_RULE_TEXT), 1)
        self.assertIn("git commit --no-edit", prompt)
        self.assertNotIn("aw commit", prompt)

    def test_runbook_directive_aligned(self) -> None:
        """Directive 3 in DEFAULT_RUNBOOK_TEXT references the execute prompt rule."""
        self.assertIn(
            "3. Make safe, verifiable forward progress. Do not weaken checks or fabricate evidence (see the gate-and-tool rule in your execute prompt).",
            rs.DEFAULT_RUNBOOK_TEXT,
        )
