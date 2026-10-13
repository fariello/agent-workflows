"""Unit tests for the outcome-word ladder status classification (plan 064awu).

Validates:
(a) WORD TABLE: every token in runner_shared.TERMINAL_STATES renders the exact
    outcome word declared in Findings F-02 across zero and one attempt, with and
    without a recorded refusal.
(b) TOTALITY: runner_shared.TERMINAL_STATES is a subset of
    render_stream.RUN_OUTCOME_CLASS_BY_STATUS, preventing fallthrough to PARTIAL.
(c) ALIAS AGREEMENT: every alias in runner_shared.TERMINAL_STATUS_ALIASES agrees
    with its canonical token unless listed in render_stream.DECLARED_OUTCOME_ALIAS_DIVERGENCES,
    and every declared divergence actually differs.
(d) CANONICAL FAIL-GATE: fail-gate renders BLOCKED across all combinations,
    beside failed-safely rendering FAILED, enforcing OQ-01 directly.
"""

from __future__ import annotations

import re
import unittest
from typing import Any

from agent_workflows import render_stream, runner_shared


def _item(**overrides: Any) -> dict[str, Any]:
    """Build one queue entry in the shape persisted by runner state."""
    item: dict[str, Any] = {
        "position": 1,
        "id6": "test01",
        "setid": "3l0dmi",
        "action": "execute",
        "status": "reviewed",
        "verification_status": "verified",
        "attempts": [],
    }
    item.update(overrides)
    return item


def _state(queue: list[dict[str, Any]], **options: Any) -> dict[str, Any]:
    """Build minimal state dictionary for render_run_summary_table."""
    return {
        "run_id": "run-test-064awu",
        "repo": "/repo",
        "queue": queue,
        "options": dict(options),
    }


def _render_outcome_word(
    status: str,
    attempts: list[dict[str, Any]],
    with_refusal: bool = False,
) -> str:
    """Render a single-item queue and extract the outcome word."""
    it = _item(status=status, attempts=attempts)
    if with_refusal:
        render_stream.record_refusal(
            it,
            code="test-refusal",
            reason="test reason",
            remedy="test remedy",
        )
    rendered = render_stream.render_run_summary_table(
        _state([it]),
        pal=render_stream.Palette(False),
    )
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Outcome:" in line:
            match = re.search(r"Outcome:\s+([A-Z ]+?)\s+Duration:", line)
            if match:
                return match.group(1).strip()
    raise AssertionError(
        f"Could not parse outcome word from rendered table:\n{rendered}"
    )


# Expected words from Findings F-02:
# (att=0/noref, att=0/ref, att=1/noref, att=1/ref)
EXPECTED_WORDS: dict[str, tuple[str, str, str, str]] = {
    "already-landed": ("PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"),
    "approved": ("COMPLETED", "PARTIAL", "COMPLETED", "PARTIAL"),
    "blocked": ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
    "dependency-blocked": ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
    "executed": ("COMPLETED", "PARTIAL", "COMPLETED", "PARTIAL"),
    "fail-begin": ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
    "fail-depend": ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
    "fail-gate": ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
    "fail-lane": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "fail-merge": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "fail-verify": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "failed": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "failed-safely": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "integration-blocked": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "interrupted": ("INTERRUPTED", "INTERRUPTED", "INTERRUPTED", "INTERRUPTED"),
    "merge-conflict": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "merge-needs-human": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "merge-refused": ("FAILED", "FAILED", "FAILED", "FAILED"),
    "not-attempted": ("QUEUED", "QUEUED", "QUEUED", "QUEUED"),
    "not-run": ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
    "partial": ("PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"),
    "retired": ("PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"),
    "reviewed": ("NO WORK PERFORMED", "QUEUED", "COMPLETED", "PARTIAL"),
    "substantially-complete": ("COMPLETED", "PARTIAL", "COMPLETED", "PARTIAL"),
}


class OutcomeWordLadderBehavioralFenceTests(unittest.TestCase):
    """Behavioral guard asserting ladder classifications, totality, and alias agreement."""

    def test_case_a_word_table(self) -> None:
        """(a) WORD TABLE: every token renders the exact expected word across attempts and refusals."""
        shapes: list[tuple[list[dict[str, Any]], bool, int]] = [
            ([], False, 0),
            ([], True, 1),
            ([{"number": 1}], False, 2),
            ([{"number": 1}], True, 3),
        ]
        for token in sorted(runner_shared.TERMINAL_STATES):
            self.assertIn(
                token, EXPECTED_WORDS, f"Missing expected words for token {token}"
            )
            expected_tuple = EXPECTED_WORDS[token]
            for attempts, with_refusal, idx in shapes:
                actual = _render_outcome_word(
                    token, attempts, with_refusal=with_refusal
                )
                expected = expected_tuple[idx]
                self.assertEqual(
                    actual,
                    expected,
                    f"Token {token} at att={len(attempts)} ref={with_refusal} rendered {actual!r}, expected {expected!r}",
                )

    def test_case_b_totality(self) -> None:
        """(b) TOTALITY: every token in TERMINAL_STATES is declared in RUN_OUTCOME_CLASS_BY_STATUS."""
        missing = set(runner_shared.TERMINAL_STATES) - set(
            render_stream.RUN_OUTCOME_CLASS_BY_STATUS
        )
        self.assertEqual(
            missing,
            set(),
            f"Tokens in runner_shared.TERMINAL_STATES missing from RUN_OUTCOME_CLASS_BY_STATUS: {sorted(missing)}",
        )

    def test_case_c_alias_agreement(self) -> None:
        """(c) ALIAS AGREEMENT: aliases agree with canonical tokens unless declared in divergences."""
        shapes: list[tuple[list[dict[str, Any]], bool]] = [
            ([], False),
            ([], True),
            ([{"number": 1}], False),
            ([{"number": 1}], True),
        ]

        # 1. Every alias in TERMINAL_STATUS_ALIASES agrees with canonical unless declared
        for legacy, canonical in sorted(runner_shared.TERMINAL_STATUS_ALIASES.items()):
            if legacy in render_stream.DECLARED_OUTCOME_ALIAS_DIVERGENCES:
                # Must differ in at least one shape
                words_differ = any(
                    _render_outcome_word(legacy, att, ref)
                    != _render_outcome_word(canonical, att, ref)
                    for att, ref in shapes
                )
                self.assertTrue(
                    words_differ,
                    f"Alias {legacy!r} declared divergent from {canonical!r} but renders identically across all shapes",
                )
            else:
                for att, ref in shapes:
                    legacy_word = _render_outcome_word(legacy, att, ref)
                    canonical_word = _render_outcome_word(canonical, att, ref)
                    self.assertEqual(
                        legacy_word,
                        canonical_word,
                        f"Undeclared alias divergence: {legacy!r} ({legacy_word}) != {canonical!r} ({canonical_word}) at att={len(att)} ref={ref}",
                    )

        # 2. Every declared divergence is a real alias whose word differs from canonical
        for div_alias in sorted(
            render_stream.DECLARED_OUTCOME_ALIAS_DIVERGENCES.keys()
        ):
            self.assertIn(
                div_alias,
                runner_shared.TERMINAL_STATUS_ALIASES,
                f"Declared divergence {div_alias!r} is not in runner_shared.TERMINAL_STATUS_ALIASES",
            )
            canonical = runner_shared.TERMINAL_STATUS_ALIASES[div_alias]
            words_differ = any(
                _render_outcome_word(div_alias, att, ref)
                != _render_outcome_word(canonical, att, ref)
                for att, ref in shapes
            )
            self.assertTrue(
                words_differ,
                f"Divergence entry {div_alias!r} is stale: words agree with canonical {canonical!r} across all shapes",
            )

    def test_case_d_canonical_fail_gate(self) -> None:
        """(d) CANONICAL FAIL-GATE: fail-gate renders BLOCKED across all combinations; failed-safely renders FAILED."""
        shapes: list[tuple[list[dict[str, Any]], bool]] = [
            ([], False),
            ([], True),
            ([{"number": 1}], False),
            ([{"number": 1}], True),
        ]
        for attempts, with_refusal in shapes:
            fail_gate_word = _render_outcome_word(
                "fail-gate", attempts, with_refusal=with_refusal
            )
            self.assertEqual(
                fail_gate_word,
                "BLOCKED",
                f"fail-gate must render BLOCKED at att={len(attempts)} ref={with_refusal}, got {fail_gate_word!r}",
            )
            failed_safely_word = _render_outcome_word(
                "failed-safely", attempts, with_refusal=with_refusal
            )
            self.assertEqual(
                failed_safely_word,
                "FAILED",
                f"failed-safely must render FAILED at att={len(attempts)} ref={with_refusal}, got {failed_safely_word!r}",
            )
