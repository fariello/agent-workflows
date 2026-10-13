"""Cross-reader parity tests for Antigravity tool-name precedence (n8we3u).

Ensures all five in-tree readers:
1. agy_runipd.render_agy_event
2. agy_view.format_record
3. runner_stop.event_label
4. agy_run._progress_messages
5. verifier_corroboration.tool_call_from_event

agree on the tool name resolved by verifier_corroboration.agy_tool_name
across all canonical and edge-case step_update shapes.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from agent_workflows.agy_run import _progress_messages
from agent_workflows.agy_runipd import render_agy_event
from agent_workflows.agy_view import format_record
from agent_workflows.render_stream import Palette
from agent_workflows.runner_stop import event_label
from agent_workflows.verifier_corroboration import (
    agy_tool_name,
    tool_call_from_event,
)

PALETTE = Palette(False)

PARITY_CASES = [
    (
        "conflict",
        {"tool_name": "cmd_tool", "tool_info": {"name": "sub_tool"}},
        "sub_tool",
    ),
    (
        "reverse_conflict",
        {"tool_name": "sub_tool", "tool_info": {"name": "cmd_tool"}},
        "cmd_tool",
    ),
    (
        "name_only",
        {"tool_name": "cmd_tool"},
        "cmd_tool",
    ),
    (
        "info_only",
        {"tool_info": {"name": "sub_tool"}},
        "sub_tool",
    ),
    (
        "padded",
        {"tool_info": {"name": "  padded_tool  "}},
        "padded_tool",
    ),
    (
        "non_string_name",
        {"tool_name": "fallback_tool", "tool_info": {"name": 42}},
        "fallback_tool",
    ),
    (
        "non_mapping_info",
        {"tool_name": "fallback_tool", "tool_info": "junk"},
        "fallback_tool",
    ),
    (
        "neither",
        {},
        "",
    ),
]


@pytest.mark.parametrize("shape_name,update_fields,expected_name", PARITY_CASES)
def test_cross_reader_tool_name_parity(
    shape_name: str, update_fields: dict[str, Any], expected_name: str
) -> None:
    step = {
        "step_index": 1,
        "step_type": "tool",
        "state": "DONE",
        **update_fields,
    }
    evt = {"event": "step_update", "step_update": step}
    raw = json.dumps(evt)

    # 0. Canonical resolver
    resolved = agy_tool_name(step)
    assert resolved == expected_name

    # 1. agy_runipd.render_agy_event (at verbosity=1)
    # Default when empty is "tool"
    exp_render_name = expected_name if expected_name else "tool"
    rendered = render_agy_event(raw, PALETTE, verbosity=1)
    assert rendered is not None
    assert exp_render_name in rendered

    # 2. agy_view.format_record
    # Default when empty is "tool"
    exp_view_name = expected_name if expected_name else "tool"
    formatted = format_record(1, evt)
    assert f"DONE   {exp_view_name}" in formatted

    # 3. runner_stop.event_label
    # Default when empty is step_type ("tool")
    exp_stop_suffix = expected_name if expected_name else "tool"
    label = event_label(raw)
    assert label == f"unknown:{exp_stop_suffix}"

    # 4. agy_run._progress_messages
    # Message emitted only when tool_info is a Mapping; default name when empty is "tool"
    progress = _progress_messages(evt, "phase")
    if isinstance(step.get("tool_info"), dict):
        exp_prog_name = expected_name if expected_name else "tool"
        assert len(progress) == 1
        assert progress[0][0] == f"step:1:DONE:tool:{exp_prog_name}"
        assert progress[0][1] == f"[phase] tool finished: {exp_prog_name}"
    else:
        assert len(progress) == 0

    # 5. verifier_corroboration.tool_call_from_event
    # Default when empty is ""
    tc = tool_call_from_event(evt)
    assert tc is not None
    assert tc.tool == expected_name


def test_non_mapping_tool_info_does_not_raise() -> None:
    """Ensure non-mapping tool_info does not raise across all readers (F-08)."""
    step = {
        "step_index": 1,
        "step_type": "tool",
        "state": "DONE",
        "tool_name": "safe_tool",
        "tool_info": "junk",
    }
    evt = {"event": "step_update", "step_update": step}
    raw = json.dumps(evt)

    # None of these should raise
    assert agy_tool_name(step) == "safe_tool"
    assert "safe_tool" in (render_agy_event(raw, PALETTE, verbosity=1) or "")
    assert "safe_tool" in format_record(1, evt)
    assert event_label(raw) == "unknown:safe_tool"
    assert _progress_messages(evt, "phase") == []
    tc = tool_call_from_event(evt)
    assert tc is not None and tc.tool == "safe_tool"
