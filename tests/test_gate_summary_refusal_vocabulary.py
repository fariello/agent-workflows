"""Behavioral tests for the gate-summary refusal vocabulary on validate_gate_flags.

Verifies that attention_contract.validate_gate_flags uses the shared Section 8.8
refusal vocabulary for --gate-summary, matching refuse_unsafe_descriptive.
Governed by IPD vql6j0 (backlog 303k5n).
"""

import pytest

from agent_workflows.attention_contract import (
    refuse_unsafe_descriptive,
    validate_gate_flags,
)

VERB = "aw set"
GATE_KIND = "date"
GATE_REF = "2026-10-02"


@pytest.mark.parametrize(
    "newline_value",
    [
        "a\nb",
        "bad\ngate summary",
        "line1\nline2\nline3",
        "carriage\rreturn",
    ],
)
def test_validate_gate_flags_refuses_embedded_newlines(newline_value: str) -> None:
    expected = f"{VERB}: --gate-summary must not contain embedded newlines"
    actual = validate_gate_flags(VERB, GATE_KIND, GATE_REF, newline_value)
    assert actual == expected
    assert actual == refuse_unsafe_descriptive(VERB, "--gate-summary", newline_value)


@pytest.mark.parametrize(
    "ctrl_value",
    [
        "a\x07b",
        "null\x00byte",
        "escape\x1bchar",
    ],
)
def test_validate_gate_flags_refuses_control_characters(ctrl_value: str) -> None:
    expected = f"{VERB}: --gate-summary must not contain control characters"
    actual = validate_gate_flags(VERB, GATE_KIND, GATE_REF, ctrl_value)
    assert actual == expected
    assert actual == refuse_unsafe_descriptive(VERB, "--gate-summary", ctrl_value)


def test_validate_gate_flags_refuses_overlength_301() -> None:
    value_301 = "x" * 301
    expected = (
        f"{VERB}: --gate-summary exceeds maximum length of 300 characters (301 > 300)"
    )
    actual = validate_gate_flags(VERB, GATE_KIND, GATE_REF, value_301)
    assert actual == expected
    assert actual == refuse_unsafe_descriptive(VERB, "--gate-summary", value_301)


def test_validate_gate_flags_refuses_overlength_400() -> None:
    value_400 = "y" * 400
    expected = (
        f"{VERB}: --gate-summary exceeds maximum length of 300 characters (400 > 300)"
    )
    actual = validate_gate_flags(VERB, GATE_KIND, GATE_REF, value_400)
    assert actual == expected
    assert actual == refuse_unsafe_descriptive(VERB, "--gate-summary", value_400)


def test_validate_gate_flags_accepts_exactly_300_chars() -> None:
    value_300 = "z" * 300
    assert validate_gate_flags(VERB, GATE_KIND, GATE_REF, value_300) is None
    assert refuse_unsafe_descriptive(VERB, "--gate-summary", value_300) is None


@pytest.mark.parametrize(
    "safe_value",
    [
        "ok",
        "plain gate summary",
        "A standard descriptive note about external gate GH#123",
        "123-abc_xyz",
    ],
)
def test_validate_gate_flags_accepts_plain_values(safe_value: str) -> None:
    assert validate_gate_flags(VERB, GATE_KIND, GATE_REF, safe_value) is None
    assert refuse_unsafe_descriptive(VERB, "--gate-summary", safe_value) is None


def test_validate_gate_flags_accepts_none_summary() -> None:
    assert validate_gate_flags(VERB, GATE_KIND, GATE_REF, None) is None
    assert refuse_unsafe_descriptive(VERB, "--gate-summary", None) is None


def test_validate_gate_flags_preserves_custom_verb_prefix() -> None:
    custom_verb = "aw specs set"
    actual = validate_gate_flags(custom_verb, GATE_KIND, GATE_REF, "bad\nsummary")
    expected = f"{custom_verb}: --gate-summary must not contain embedded newlines"
    assert actual == expected
    assert actual == refuse_unsafe_descriptive(
        custom_verb, "--gate-summary", "bad\nsummary"
    )
