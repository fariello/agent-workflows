"""Unit and regression tests for verifier evidence consumption (runverdict-05, bxx9af).

Tests that the runner consumes verifier test evidence, enforces the calibrated evidence predicate
fail-closed, renders evidence in execution-report.md and aw runs, and maintains cross-driver symmetry.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest import TestCase

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows.run_viewer import load_run_summary, render_step_details
from agent_workflows.runner_shared import (
    INTEGRATION_EARNED_BY_SUITE,
    INTEGRATION_EARNED_BY_VERIFIER,
    INTEGRATION_REFUSED_SUITE_FAILED,
    INTEGRATION_REFUSED_VERIFIER_DECLINED,
    SuiteCheckResult,
    VERIFY_DISP_UNVERIFIED,
    VERIFY_DISP_VERIFIED,
    VERIFY_REFUSAL_CODE_UNEVIDENCED,
    entry_has_command_content,
    extract_verifier_corrections,
    extract_verifier_test_commands,
    has_verifier_test_evidence,
    integration_is_earned,
    is_command_like,
    verifier_evidence_refusal_text,
    write_report,
)
from agent_workflows.term import Term


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "verifier_evidence_corpus.json"


class CorpusSurveyTests(TestCase):
    """E-01 / V-01: Survey of candidate predicates against measured verification outcome shapes."""

    def test_item_proposed_predicate_vs_calibrated_predicate_over_corpus_shapes(
        self,
    ) -> None:
        """Demonstrate that the backlog item's proposed bar fails on bare strings and name-keyed dicts,

        while the calibrated predicate passes all 9 genuine shapes and rejects invalid ones.
        """
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        shapes = data["shapes"]
        negative_cases = data["negative_cases"]

        # 1. Backlog item's proposed predicate: requires dict with command AND (exit_code or exit)
        def item_proposed_bar(v_data: dict[str, Any]) -> bool:
            tests_run = v_data.get("tests_run")
            if not isinstance(tests_run, list) or not tests_run:
                return False
            for entry in tests_run:
                if isinstance(entry, dict):
                    has_cmd = "command" in entry or "cmd" in entry
                    has_exit = "exit_code" in entry or "exit" in entry
                    if has_cmd and has_exit:
                        return True
            return False

        item_passed = []
        item_failed = []
        calibrated_passed = []
        calibrated_failed = []

        for shape in shapes:
            name = shape["name"]
            entry = shape["entry"]
            v_dict = {"tests_run": [entry]}
            if item_proposed_bar(v_dict):
                item_passed.append(name)
            else:
                item_failed.append(name)

            if has_verifier_test_evidence(v_dict):
                calibrated_passed.append(name)
            else:
                calibrated_failed.append(name)

        # The item's proposed bar fails on bare strings and the name-keyed dict (F-5 / F-14)
        self.assertIn("bare_string_standard", item_failed)
        self.assertIn("bare_string_658_chars", item_failed)
        self.assertIn("dict_detail_name_result", item_failed)
        self.assertIn("dict_command_result", item_failed)

        # Our calibrated predicate passes ALL genuine shapes (zero false negatives)
        self.assertEqual(len(calibrated_failed), 0)
        self.assertEqual(len(calibrated_passed), len(shapes))

        # And fails all negative / contentless shapes
        for neg in negative_cases:
            self.assertFalse(
                has_verifier_test_evidence(neg["outcome"]),
                f"Negative case {neg['name']} unexpectedly passed",
            )


class EvidencePredicateUnitTests(TestCase):
    """E-02 / V-02: Unit tests for predicate functions, command detection, and extractors."""

    def test_is_command_like(self) -> None:
        # Valid commands
        self.assertTrue(
            is_command_like("python3 -m unittest tests.test_from_backlog -v")
        )
        self.assertTrue(is_command_like("python -m pytest tests/"))
        self.assertTrue(is_command_like("pytest tests/test_run_viewer.py"))
        self.assertTrue(is_command_like("make test"))
        self.assertTrue(is_command_like("git diff --stat"))
        self.assertTrue(is_command_like("aw runs --json"))
        self.assertTrue(is_command_like("./scripts/test.sh"))
        self.assertTrue(is_command_like("bin/run_tests"))
        self.assertTrue(is_command_like("sh -c 'pytest'"))
        self.assertTrue(is_command_like("bash test.sh"))

        # Prose containing command execution patterns
        self.assertTrue(
            is_command_like(
                "python -m unittest tests.test_release_gate_close -v -> Ran 25 tests in 0.102s OK (exit 0): ..."
            )
        )

        # Non-command / whitespace / contentless
        self.assertFalse(is_command_like(""))
        self.assertFalse(is_command_like("   "))
        self.assertFalse(is_command_like("all tests passed"))
        self.assertFalse(is_command_like("looks good"))
        self.assertFalse(is_command_like("verified"))
        self.assertFalse(is_command_like("none"))
        self.assertFalse(is_command_like("N/A"))
        self.assertFalse(is_command_like(None))
        self.assertFalse(is_command_like(123))

    def test_entry_has_command_content_individual_shapes(self) -> None:
        # 1. dict with command and exit_code
        self.assertTrue(
            entry_has_command_content(
                {
                    "command": "python3 -m unittest tests.test_from_backlog",
                    "exit_code": 0,
                }
            )
        )
        # 2. dict with cmd and exit
        self.assertTrue(
            entry_has_command_content({"cmd": "pytest tests/test_verify.py", "exit": 0})
        )
        # 3. dict with command and no exit code
        self.assertTrue(
            entry_has_command_content({"command": "git diff --stat", "result": "clean"})
        )
        # 4. dict carrying command under name with no command key (F-14 shape)
        self.assertTrue(
            entry_has_command_content(
                {
                    "name": "python -m unittest tests.test_from_backlog -v",
                    "result": "pass",
                    "detail": "Ran 6 tests ... OK",
                }
            )
        )
        # 5. dict with detail, name, result but NO command content (must FAIL)
        self.assertFalse(
            entry_has_command_content(
                {"detail": "tests passed", "name": "suite", "result": "pass"}
            )
        )
        # 6. bare string naming a command
        self.assertTrue(
            entry_has_command_content("pytest tests/test_verifier_evidence.py -v")
        )
        # 7. 658-character prose string
        long_str = "python -m unittest tests.test_release_gate_close -v -> " + (
            "x" * 590
        )
        self.assertEqual(len(long_str), 645)
        self.assertTrue(entry_has_command_content(long_str))
        # 8. empty dict
        self.assertFalse(entry_has_command_content({}))
        # 9. empty string
        self.assertFalse(entry_has_command_content("   "))

    def test_has_verifier_test_evidence(self) -> None:
        # Missing tests_run
        self.assertFalse(has_verifier_test_evidence({"verdict": "VERIFIED"}))
        # None tests_run
        self.assertFalse(has_verifier_test_evidence({"tests_run": None}))
        # Empty list
        self.assertFalse(has_verifier_test_evidence({"tests_run": []}))
        # List of whitespace strings
        self.assertFalse(has_verifier_test_evidence({"tests_run": ["", "  ", "\t"]}))
        # Non-dict
        self.assertFalse(has_verifier_test_evidence("invalid"))

        # Valid list
        self.assertTrue(
            has_verifier_test_evidence(
                {
                    "tests_run": [
                        {
                            "command": "python3 -m unittest tests.test_foo",
                            "exit_code": 0,
                        }
                    ]
                }
            )
        )

    def test_extract_verifier_test_commands_and_corrections(self) -> None:
        v_data = {
            "tests_run": [
                {"command": "python3 -m unittest tests.test_one", "exit_code": 0},
                {"name": "pytest tests/test_two.py", "result": "pass"},
                "python3 -m pytest tests/test_three.py -v -> OK",
            ],
            "corrections_made": [
                "Fixed lint error in runner_shared.py",
                "Updated test expectation",
            ],
        }
        cmds = extract_verifier_test_commands(v_data)
        self.assertEqual(
            cmds,
            [
                "python3 -m unittest tests.test_one",
                "pytest tests/test_two.py",
                "python3 -m pytest tests/test_three.py -v -> OK",
            ],
        )
        corrs = extract_verifier_corrections(v_data)
        self.assertEqual(
            corrs,
            [
                "Fixed lint error in runner_shared.py",
                "Updated test expectation",
            ],
        )

    def test_extract_verifier_test_commands_truncation(self) -> None:
        long_cmd = "python3 -m unittest " + ("a" * 200)
        v_data = {"tests_run": [long_cmd]}
        cmds = extract_verifier_test_commands(v_data, max_len=50)
        self.assertEqual(len(cmds[0]), 50)
        self.assertTrue(cmds[0].endswith("..."))

    def test_verifier_evidence_refusal_text(self) -> None:
        code, reason, remedy = verifier_evidence_refusal_text({"tests_run": []})
        self.assertEqual(code, VERIFY_REFUSAL_CODE_UNEVIDENCED)
        self.assertIn("provided no test evidence in 'tests_run'", reason)
        self.assertIn("re-run this item's verification", remedy)


class FixtureCorpusRegressionFenceTests(TestCase):
    """E-03 / V-03: Regression fence asserting all 9 measured dict key-sets plus bare strings pass."""

    def test_fixture_corpus_covers_all_nine_dict_key_sets_and_bare_string(self) -> None:
        self.assertTrue(FIXTURE_PATH.is_file(), f"Fixture file {FIXTURE_PATH} missing")
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        shapes = data["shapes"]

        measured_key_sets = {
            tuple(sorted(["command", "exit_code", "name", "result"])),
            tuple(sorted(["command", "exit_code", "note", "result"])),
            tuple(sorted(["command", "exit_code", "result"])),
            tuple(sorted(["command", "exit", "result"])),
            tuple(sorted(["command", "result"])),
            tuple(sorted(["detail", "name", "result"])),
            tuple(sorted(["command", "detail", "result"])),
            tuple(sorted(["cmd", "exit", "result"])),
            tuple(sorted(["command", "exit_code", "name", "result", "verdict"])),
        }

        fixture_key_sets = set()
        has_bare_string = False

        for shape in shapes:
            entry = shape["entry"]
            # Assert each positive fixture shape passes the predicate
            v_data = {"tests_run": [entry]}
            self.assertTrue(
                has_verifier_test_evidence(v_data),
                f"Shape {shape['name']} failed evidence predicate",
            )
            if isinstance(entry, dict):
                fixture_key_sets.add(tuple(sorted(entry.keys())))
            elif isinstance(entry, str):
                has_bare_string = True

        # Assert all 9 key sets are covered by the fixture
        for ks in measured_key_sets:
            self.assertIn(ks, fixture_key_sets, f"Missing key set {ks} in fixture")
        self.assertTrue(has_bare_string, "Bare string shape missing in fixture")


class RunnerVerificationGateTests(TestCase):
    """E-04 / V-04: Host verification gate behavior for unevidenced and unreadable outcomes."""

    def test_cross_driver_symmetry(self) -> None:
        """Assert both oc_runipd and agy_runipd re-export the identical runner_shared symbols."""
        for sym in (
            "has_verifier_test_evidence",
            "extract_verifier_test_commands",
            "extract_verifier_corrections",
            "verifier_evidence_refusal_text",
            "VERIFY_COMMAND_PREFIXES",
            "VERIFY_REFUSAL_CODE_UNEVIDENCED",
        ):
            oc_obj = getattr(oc_runipd, sym)
            agy_obj = getattr(agy_runipd, sym)
            shared_obj = getattr(runner_shared, sym)
            self.assertIs(
                oc_obj, shared_obj, f"oc_runipd.{sym} is not runner_shared.{sym}"
            )
            self.assertIs(
                agy_obj, shared_obj, f"agy_runipd.{sym} is not runner_shared.{sym}"
            )

    def test_execute_item_core_refuses_verified_verdict_with_empty_tests_run(
        self,
    ) -> None:
        """Simulate outcome parsing in execute_item_core when verdict is VERIFIED but tests_run is empty."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            outcomes_dir = run_dir / "outcomes"
            outcomes_dir.mkdir(parents=True)
            v_file = outcomes_dir / "01-abc123-verification.json"
            v_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id6": "abc123",
                        "verdict": "VERIFIED",
                        "summary": "verified everything",
                        "evidence": ["all good"],
                        "tests_run": [],
                    }
                ),
                encoding="utf-8",
            )

            # Parse as execute_item_core does
            v_data = json.loads(v_file.read_text(encoding="utf-8"))
            v_raw_verdict = v_data.get("verdict", "")
            v_map = runner_shared.map_verdict(v_raw_verdict)
            verify_disp = v_map.verify_disp
            disposition = "executed"

            v_has_evidence = has_verifier_test_evidence(v_data)
            self.assertFalse(v_has_evidence)

            if verify_disp == VERIFY_DISP_VERIFIED and not v_has_evidence:
                verify_disp = VERIFY_DISP_UNVERIFIED
                disposition = "partial"
                v_code, v_reason, v_remedy = verifier_evidence_refusal_text(v_data)

            self.assertEqual(verify_disp, "unverified")
            self.assertEqual(disposition, "partial")
            self.assertEqual(v_code, VERIFY_REFUSAL_CODE_UNEVIDENCED)


class IntegrationEarnedInteractionTests(TestCase):
    """E-05 / V-05: Interaction with integration_is_earned on validation-on and validation-off paths."""

    def test_validation_on_path_refuses_non_verified_dispositions(self) -> None:
        # validate=True requires verify_disp == "verified"
        res_verified = integration_is_earned(
            validate=True, verify_disp="verified", suite_result=None
        )
        self.assertTrue(res_verified.earned)
        self.assertEqual(res_verified.signal, INTEGRATION_EARNED_BY_VERIFIER)

        res_unverified = integration_is_earned(
            validate=True, verify_disp="unverified", suite_result=None
        )
        self.assertFalse(res_unverified.earned)
        self.assertEqual(res_unverified.signal, INTEGRATION_REFUSED_VERIFIER_DECLINED)

        res_none = integration_is_earned(
            validate=True, verify_disp=None, suite_result=None
        )
        self.assertFalse(res_none.earned)
        self.assertEqual(res_none.signal, INTEGRATION_REFUSED_VERIFIER_DECLINED)

    def test_validation_off_path_ignores_verify_disp_and_reads_suite(self) -> None:
        # validate=False ignores verify_disp entirely and evaluates suite_result
        passing_suite = SuiteCheckResult(
            passing=True,
            exit_code=0,
            summary="200 passed",
            reason="all 200 tests passed",
            cwd=".",
            timeout_seconds=60.0,
            elapsed_seconds=1.5,
        )
        failing_suite = SuiteCheckResult(
            passing=False,
            exit_code=1,
            summary="2 failed, 198 passed",
            reason="2 tests failed",
            cwd=".",
            timeout_seconds=60.0,
            elapsed_seconds=1.5,
        )

        res_pass = integration_is_earned(
            validate=False, verify_disp="unverified", suite_result=passing_suite
        )
        self.assertTrue(res_pass.earned)
        self.assertEqual(res_pass.signal, INTEGRATION_EARNED_BY_SUITE)

        res_fail = integration_is_earned(
            validate=False, verify_disp="unverified", suite_result=failing_suite
        )
        self.assertFalse(res_fail.earned)
        self.assertEqual(res_fail.signal, INTEGRATION_REFUSED_SUITE_FAILED)


class ExecutionReportRenderingTests(TestCase):
    """E-06 / V-06: Surface evidence in execution-report.md."""

    def test_write_report_renders_verification_evidence_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            outcomes_dir = run_dir / "outcomes"
            outcomes_dir.mkdir(parents=True)
            v_file = outcomes_dir / "01-abc123-verification.json"
            v_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id6": "abc123",
                        "verdict": "VERIFIED",
                        "tests_run": [
                            "python3 -m pytest tests/test_verifier_evidence.py -v"
                        ],
                        "corrections_made": ["Cleaned up whitespace in test"],
                    }
                ),
                encoding="utf-8",
            )

            state = {
                "run_id": "run-20260924T000000Z-123456",
                "repo": "agent-workflows",
                "queue": [
                    {
                        "position": 1,
                        "id6": "abc123",
                        "setid": "testset",
                        "status": "executed",
                        "verification_status": "verified",
                    }
                ],
            }

            write_report(run_dir, state, labels=runner_shared.OC_HOST_LABELS)
            report_text = (run_dir / "execution-report.md").read_text(encoding="utf-8")

            self.assertIn("## Verification evidence", report_text)
            self.assertIn("- `abc123` (position 1):", report_text)
            self.assertIn(
                "python3 -m pytest tests/test_verifier_evidence.py -v", report_text
            )
            self.assertIn("Cleaned up whitespace in test", report_text)

    def test_write_report_omits_section_when_no_verification_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            state = {
                "run_id": "run-20260924T000000Z-123456",
                "repo": "agent-workflows",
                "queue": [
                    {
                        "position": 1,
                        "id6": "abc123",
                        "setid": "testset",
                        "status": "executed",
                        "verification_status": "",
                    }
                ],
            }

            write_report(run_dir, state, labels=runner_shared.OC_HOST_LABELS)
            report_text = (run_dir / "execution-report.md").read_text(encoding="utf-8")
            self.assertNotIn("## Verification evidence", report_text)


class RunViewerSurfacingTests(TestCase):
    """E-07 / V-07: Surface evidence in aw runs human view, --json, and --agent."""

    def test_step_summary_and_json_payload_carry_tests_run_and_corrections(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run-20260924T000000Z-123456"
            outcomes_dir = run_dir / "outcomes"
            outcomes_dir.mkdir(parents=True)
            v_file = outcomes_dir / "01-abc123-verification.json"
            v_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id6": "abc123",
                        "verdict": "VERIFIED",
                        "tests_run": ["pytest tests/test_verifier_evidence.py -v"],
                        "corrections_made": ["Fixed docstring typo"],
                    }
                ),
                encoding="utf-8",
            )
            state_file = run_dir / "state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "run_id": "run-20260924T000000Z-123456",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "abc123",
                                "setid": "testset",
                                "status": "executed",
                                "verification_status": "verified",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = load_run_summary(run_dir)
            self.assertIsNotNone(summary)
            self.assertEqual(len(summary.steps), 1)
            step = summary.steps[0]
            self.assertEqual(
                step.tests_run, ["pytest tests/test_verifier_evidence.py -v"]
            )
            self.assertEqual(step.corrections_made, ["Fixed docstring typo"])

            # Test JSON serialization via asdict
            payload = asdict(step)
            self.assertIn("tests_run", payload)
            self.assertIn("corrections_made", payload)
            self.assertEqual(
                payload["tests_run"], ["pytest tests/test_verifier_evidence.py -v"]
            )

            # Test human details rendering
            term = Term(color=False)
            details = render_step_details([step], term)
            details_str = "\n".join(details)
            self.assertIn("pytest tests/test_verifier_evidence.py -v", details_str)
            self.assertIn("Fixed docstring typo", details_str)
