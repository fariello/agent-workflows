"""Behavioral tests for the worker lane missing-input token contract (IPD 38pxaz).

Pins the behavioral agreement across the emitted report token, the token form published in
the worker prompt, and the coordinator parser following the re-homing of AW_MISSING_INPUT.
This test asserts strictly on returned values and rendered text; it does not read module
source and makes no assertion about which module holds the constant.
"""

from pathlib import Path
from agent_workflows.lane_containment import (
    format_missing_input_token,
    isolation_notice,
    parse_missing_input_token,
)


def test_token_round_trip_parse_and_format():
    """Verify that format_missing_input_token and parse_missing_input_token round trip cleanly."""
    path = "path/to/required_input.txt"
    why = "needed for compilation check"
    rendered = format_missing_input_token(path, why)
    parsed = parse_missing_input_token(rendered)
    assert parsed == (path, why)


def test_token_round_trip_with_colons_in_reason():
    """Verify that reasons containing colons parse correctly without splitting the reason."""
    path = "config/settings.json"
    why = "note: needed because key:value is missing in file:line"
    rendered = format_missing_input_token(path, why)
    parsed = parse_missing_input_token(rendered)
    assert parsed == (path, why)


def test_prompt_published_form_agrees_with_emitter_prefix():
    """Verify that the worker prompt notice publishes the identical token prefix the emitter produces."""
    prompt = isolation_notice(Path("/test/lane"))
    emitted = format_missing_input_token("dummy/path", "dummy reason")
    emitted_prefix = emitted.split(":", 1)[0]
    expected_line = f"    {emitted_prefix}:<repo-relative-path>:<why it is required>"
    assert expected_line in prompt


def test_parser_rejects_unrelated_or_mismatched_lines():
    """Verify that parse_missing_input_token returns None for unrelated output or mismatched prefixes."""
    assert parse_missing_input_token("regular stdout line from worker") is None
    assert parse_missing_input_token("DIFFERENT_TOKEN:foo:bar") is None
    assert parse_missing_input_token("") is None
