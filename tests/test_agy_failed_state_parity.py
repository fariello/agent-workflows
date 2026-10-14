"""Cross-reader parity tests for Antigravity FAILED step state (u3enlv).

Drives the real readers (no mocks):
1. agy_runipd.render_agy_event
2. verifier_corroboration.tool_call_from_event
3. run_dashboard.session_stats

over a literal oracle table of step states (ACTIVE, DONE, ERROR, FAILED, CANCELED)
without deriving expectations from AGY_TERMINAL_STATES or AGY_ERROR_STATES.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agent_workflows.agy_runipd import render_agy_event
from agent_workflows.render_stream import Palette
from agent_workflows.run_dashboard import session_stats
from agent_workflows.verifier_corroboration import tool_call_from_event

PALETTE = Palette(False)

# Literal oracle table: (state, expected_observed, expected_errored)
# Deliberately NOT derived from AGY_TERMINAL_STATES or AGY_ERROR_STATES so a wrong
# constant fails the test instead of redefining the oracle.
STATE_PARITY_TABLE: tuple[tuple[str, bool, bool], ...] = (
    ("ACTIVE", False, False),
    ("DONE", True, False),
    ("ERROR", True, True),
    ("FAILED", True, True),
    ("CANCELED", False, False),
)


@pytest.mark.parametrize(
    "state,expected_observed,expected_errored",
    STATE_PARITY_TABLE,
    ids=[row[0] for row in STATE_PARITY_TABLE],
)
def test_cross_reader_agy_tool_state_parity(
    state: str, expected_observed: bool, expected_errored: bool
) -> None:
    ev = {
        "event": "step_update",
        "step_update": {
            "step_index": 1,
            "state": state,
            "step_type": "tool",
            "tool_name": "run_command",
            "tool_info": {
                "name": "run_command",
                "parameters": {"CommandLine": "python3 -m pytest"},
            },
        },
    }
    raw = json.dumps(ev)

    rendered = render_agy_event(raw, PALETTE, verbosity=1, use_unicode=False)
    tc = tool_call_from_event(ev)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "log.jsonl"
        p.write_text(raw + "\n", encoding="utf-8")
        stats = session_stats(p)

    rendered_observed = rendered is not None
    extractor_observed = tc is not None
    dashboard_observed = stats["tool_calls"] == 1

    assert rendered_observed is expected_observed
    assert extractor_observed is expected_observed
    assert dashboard_observed is expected_observed
    assert rendered_observed == (extractor_observed and dashboard_observed)

    if expected_observed:
        assert tc is not None
        assert tc.error is expected_errored
        assert (stats["tool_errors"] == 1) is expected_errored
        assert tc.error == (stats["tool_errors"] == 1)
    else:
        assert stats["tool_calls"] == 0
        assert stats["tool_errors"] == 0
