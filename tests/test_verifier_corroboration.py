"""Tests for verifier test evidence corroboration.

Validates session log command extraction, tolerant command matching, and three-state
fail-open corroboration verdicts across both OpenCode and Antigravity log formats.
Uses committed fixtures only; does not read live run directories.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

import agent_workflows.verifier_corroboration as vc
from agent_workflows.runner_shared import (
    extract_verifier_test_commands,
    has_verifier_test_evidence,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "verifier_corroboration"


class TestSessionLogExtraction:
    """E-01 & E-02: Host-agnostic log extraction, counts, and hostile input handling."""

    def test_oc_and_agy_equivalent_extractions(self) -> None:
        """Verify equivalent session logs from both hosts produce identical command extractions."""
        oc_path = FIXTURES_DIR / "oc_session_corroborated.jsonl"
        agy_path = FIXTURES_DIR / "agy_session_corroborated.jsonl"

        oc_res = vc.extract_session_commands(oc_path)
        agy_res = vc.extract_session_commands(agy_path)

        assert oc_res.format == "oc"
        assert agy_res.format == "agy"
        assert len(oc_res.commands) == 1
        assert len(agy_res.commands) == 1

        assert oc_res.commands[0].command == "python3 -m pytest tests/"
        assert oc_res.commands[0].tool == "bash"
        assert oc_res.commands[0].host == "oc"
        assert oc_res.commands[0].error is False

        assert agy_res.commands[0].command == "python3 -m pytest tests/"
        assert agy_res.commands[0].tool == "run_command"
        assert agy_res.commands[0].host == "agy"
        assert agy_res.commands[0].error is False

    def test_three_categories_counted_separately_oc(self) -> None:
        """Verify OpenCode log distinguishes observed command, delegation, and missing command text."""
        p = FIXTURES_DIR / "oc_session_three_categories.jsonl"
        res = vc.extract_session_commands(p)

        assert len(res.commands) == 1
        assert res.commands[0].command == "python3 -m pytest tests/"
        assert res.delegation_count == 1
        assert res.missing_command_count == 1
        assert res.reason_code == ""

    def test_three_categories_counted_separately_agy(self) -> None:
        """Verify Antigravity twin distinguishes observed command, delegation, and missing command text."""
        p = FIXTURES_DIR / "agy_session_three_categories.jsonl"
        res = vc.extract_session_commands(p)

        assert len(res.commands) == 1
        assert res.commands[0].command == "python3 -m pytest tests/"
        assert res.delegation_count == 1
        assert res.missing_command_count == 1
        assert res.reason_code == ""

    @pytest.mark.parametrize(
        ("case_name", "writer", "expected_reason"),
        [
            ("nonexistent_path", lambda p: None, vc.INDETERMINATE_LOG_UNREADABLE),
            ("directory", lambda p: p.mkdir(), vc.INDETERMINATE_LOG_UNREADABLE),
            (
                "zero_byte_file",
                lambda p: p.write_bytes(b""),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "binary_file",
                lambda p: p.write_bytes(b"\x00\xff\xfe\x00\x01\x02"),
                vc.INDETERMINATE_LOG_UNREADABLE,
            ),
            (
                "not_json_lines",
                lambda p: p.write_text(
                    "hello not json\nworld not json\n", encoding="utf-8"
                ),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "jsonl_top_level_lists",
                lambda p: p.write_text('[1, 2, 3]\n["a", "b"]\n', encoding="utf-8"),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "jsonl_top_level_scalars",
                lambda p: p.write_text('"string"\n12345\ntrue\n', encoding="utf-8"),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "mid_line_truncation",
                lambda p: p.write_text(
                    '{"type": "tool_use", "part": {"tool": "bash"',
                    encoding="utf-8",
                ),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
        ],
    )
    def test_hostile_inputs_never_raise(
        self,
        case_name: str,
        writer: Any,
        expected_reason: str,
    ) -> None:
        """Verify hostile inputs return empty results with expected reason code and never raise."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / f"hostile_{case_name}.log"
            if writer:
                writer(target)
            res = vc.extract_session_commands(target)
            assert res.commands == []
            assert res.reason_code == expected_reason


class TestTolerantCommandMatcher:
    """E-03: Tolerant matching across exact, truncation, prose, chaining, and indirection."""

    def test_exact_match(self) -> None:
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(
            command="python3 -m pytest tests/", tool="bash", host="oc"
        )
        assert vc.match_single_claim(claim, obs) is True

    def test_real_truncation_with_ellipsis(self) -> None:
        """Verify real >120 character truncation from extract_verifier_test_commands matches."""
        full_command = (
            "python3 -m pytest tests/test_verifier_corroboration.py "
            "-k test_a_very_long_test_name_exceeding_one_hundred_and_twenty_characters_long_for_real_truncation "
            "--verbose"
        )
        assert len(full_command) > 120
        claims = extract_verifier_test_commands({"tests_run": [full_command]})
        assert len(claims) == 1
        truncated_claim = claims[0]
        assert truncated_claim.endswith("...")

        obs = vc.ObservedCommand(command=full_command, tool="bash", host="oc")
        assert vc.match_single_claim(truncated_claim, obs) is True

    def test_prose_wrapped_command(self) -> None:
        claim = (
            "python -m unittest tests.test_release_gate_close -v -> "
            "Ran 25 tests in 0.102s OK (exit 0): all checks passed"
        )
        obs = vc.ObservedCommand(
            command="python -m unittest tests.test_release_gate_close -v",
            tool="bash",
            host="oc",
        )
        assert vc.match_single_claim(claim, obs) is True

    def test_chained_command_segment(self) -> None:
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(
            command="cd repo && python3 -m pytest tests/ ; echo done",
            tool="bash",
            host="oc",
        )
        assert vc.match_single_claim(claim, obs) is True

    def test_indirected_command_make_test(self) -> None:
        """Verify make test in KNOWN_TEST_INDIRECTIONS matches a pytest claim."""
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(command="make test", tool="bash", host="oc")
        assert vc.match_single_claim(claim, obs) is True

    def test_unrelated_command_does_not_match(self) -> None:
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(command="git status", tool="bash", host="oc")
        assert vc.match_single_claim(claim, obs) is False

    def test_delegated_turn_has_no_match(self) -> None:
        claims = ["python3 -m pytest tests/"]
        res = vc.match_claims_to_observed(claims, [])
        assert res.matched_claims == []
        assert res.unmatched_claims == claims


class TestTurnLevelVerdicts:
    """E-04: Closed set of three states with six distinct indeterminate reason codes."""

    def test_corroborated_turn(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_corroborated.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.CORROBORATED
        assert v.reason_code == vc.CORROBORATED
        assert v.matched_count == 1

    def test_uncorroborated_turn(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_uncorroborated.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.UNCORROBORATED
        assert v.reason_code == vc.UNCORROBORATED
        assert v.matched_count == 0
        assert v.observed_count == 1

    def test_indeterminate_log_unreadable(self) -> None:
        claims = ["python3 -m pytest tests/"]
        v = vc.corroborate_verifier_turn("nonexistent_session.jsonl", claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_LOG_UNREADABLE

    def test_indeterminate_log_empty(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "session_empty.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_LOG_EMPTY

    def test_indeterminate_claims_empty(self) -> None:
        p = FIXTURES_DIR / "oc_session_corroborated.jsonl"
        v = vc.corroborate_verifier_turn(p, [])
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_CLAIMS_EMPTY

    def test_indeterminate_delegation_present(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_delegated.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_DELEGATION

    def test_indeterminate_missing_command_text(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_missing_command_text.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_MISSING_COMMAND_TEXT

    def test_indeterminate_unresolved_indirection(self) -> None:
        """Verify make check fails open to indeterminate with indirection-unresolved."""
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_indirection_unresolved.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_INDIRECTION_UNRESOLVED

    def test_falsifiability_uncorroborated_to_indeterminate_on_unreadable_log(
        self,
    ) -> None:
        """Verify mutating an uncorroborated log to unreadable resolves to indeterminate."""
        claims = ["python3 -m pytest tests/"]
        src = FIXTURES_DIR / "oc_session_uncorroborated.jsonl"

        with tempfile.TemporaryDirectory() as td:
            mutated_file = Path(td) / "mutated_session.jsonl"
            mutated_file.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

            # Prior to mutation: uncorroborated
            v_before = vc.corroborate_verifier_turn(mutated_file, claims)
            assert v_before.verdict == vc.UNCORROBORATED

            # Mutate to binary unreadable content
            mutated_file.write_bytes(b"\x00\xff\xfe\x00binary_corrupt")
            v_after = vc.corroborate_verifier_turn(mutated_file, claims)
            assert v_after.verdict == vc.INDETERMINATE
            assert v_after.reason_code == vc.INDETERMINATE_LOG_UNREADABLE


class TestHonestyPinAndFabricationGap:
    """E-05 (F-2): Durable pin for the fabrication gap."""

    def test_plausible_unrun_command_accepted_by_gate_reported_uncorroborated(
        self,
    ) -> None:
        """Pin the residual weakness: a plausible-but-unrun command passes has_verifier_test_evidence

        but is reported uncorroborated when the session log contains only unmatching tool calls.
        """
        # A plausible command claim that has never been run
        claimed_command = "python3 -m pytest tests/test_release_gate.py"
        verifier_data = {
            "verdict": "VERIFIED",
            "tests_run": [claimed_command],
        }

        # 1. Shipped evidence predicate accepts it (proves activity, not non-fabrication)
        assert has_verifier_test_evidence(verifier_data) is True

        # 2. Session log shows only git status was executed
        log_path = FIXTURES_DIR / "oc_session_uncorroborated.jsonl"
        extracted = vc.extract_session_commands(log_path)
        assert len(extracted.commands) == 1
        assert extracted.commands[0].command == "git status"

        # 3. Corroboration module reports uncorroborated
        verdict = vc.corroborate_verifier_turn(log_path, verifier_data["tests_run"])
        assert verdict.verdict == vc.UNCORROBORATED
        assert verdict.reason_code == vc.UNCORROBORATED
        assert verdict.matched_count == 0
        assert verdict.observed_count == 1
