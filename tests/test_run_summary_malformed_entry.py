"""Tests pinning that render_run_summary_table tolerates malformed queue entries.

Pins:
  (1) render_run_summary_table returns rather than raising on a non-mapping queue entry;
  (2) The returned table contains exactly one body row per queue entry including the malformed one;
  (3) The malformed row's Status cell carries the malformed-entry status token;
  (4) The malformed row's ID6 cell carries the explicit unreadable marker;
  (5) The malformed entry appears in the Progress line's status census;
  (6) The outcome word is NOT COMPLETED when all other entries are successes;
  (7) The contract holds both with and without state["run_order"] present;
  (8) Mixed queues render all rows with distinct markers and statuses.
"""

from __future__ import annotations

import re
from typing import Any


from agent_workflows import render_stream
from agent_workflows.render_stream import (
    Palette,
    render_run_summary_table,
)

MALFORMED_ENTRY_TOKEN = "malformed-entry"
UNREADABLE_MARKER = "(unreadable)"


def _make_state(
    queue: list[Any],
    *,
    run_order: dict[str, Any] | None = None,
    run_id: str = "run-20260930T000000Z-123456",
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "repo": "/repo",
        "run_id": run_id,
        "created_at": "2026-09-30T00:00:00Z",
        "updated_at": "2026-09-30T00:05:00Z",
        "selectors": ["sel1"],
        "set_sessions": {},
        "queue": queue,
    }
    if run_order is not None:
        state["run_order"] = run_order
    return state


def _extract_progress_line(rendered: str) -> str:
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Progress:" in line:
            return line.strip()
    raise AssertionError(f"No Progress line found in rendered output:\n{rendered}")


def _extract_outcome_line(rendered: str) -> str:
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Outcome:" in line:
            return line.strip()
    raise AssertionError(f"No Outcome line found in rendered output:\n{rendered}")


def _extract_outcome_word(rendered: str) -> str:
    line = _extract_outcome_line(rendered)
    match = re.search(r"Outcome:\s+([A-Z ]+?)\s+Duration:", line)
    if not match:
        raise AssertionError(f"Could not parse outcome word from line: {line!r}")
    return match.group(1).strip()


def _extract_body_rows(rendered: str) -> list[list[str]]:
    plain = render_stream._strip_ansi(rendered)
    rows: list[list[str]] = []
    in_table = False
    for line in plain.splitlines():
        line = line.strip()
        if not line or not (line.startswith("│") or line.startswith("|")):
            continue
        parts = [p.strip() for p in re.split(r"[│|]", line)]
        if len(parts) >= 2 and parts[0] == "" and parts[-1] == "":
            parts = parts[1:-1]
        if not parts:
            continue
        if parts[0] == "Run" and "Pos" in parts and "ID6" in parts:
            in_table = True
            continue
        if in_table:
            if parts[0].startswith("Total ("):
                break
            if re.match(r"^\d+$", parts[0]):
                rows.append(parts)
    return rows


def test_malformed_entry_without_run_order() -> None:
    """A non-mapping queue entry without run_order renders an honest row and status census."""
    queue = ["not-a-mapping"]
    state = _make_state(queue, run_order=None)

    rendered = render_run_summary_table(state, pal=Palette(False))

    rows = _extract_body_rows(rendered)
    assert len(rows) == len(queue)
    row = rows[0]
    # Row layout: [Run, Pos, ID6, Set, Action, Status, Verify, Duration, Spend, Tok tot, Tok in, Tok out, Tok cache]
    assert row[0] == "01"
    assert row[1] == UNREADABLE_MARKER
    assert row[2] == UNREADABLE_MARKER
    assert row[3] == UNREADABLE_MARKER
    assert row[4] == UNREADABLE_MARKER
    assert row[5] == MALFORMED_ENTRY_TOKEN
    assert row[6] == "-"

    progress_line = _extract_progress_line(rendered)
    assert f"1 {MALFORMED_ENTRY_TOKEN}" in progress_line

    outcome_word = _extract_outcome_word(rendered)
    assert outcome_word != "COMPLETED"


def test_malformed_entry_with_run_order() -> None:
    """A non-mapping queue entry with run_order present renders rather than crashing early in sort."""
    queue = ["not-a-mapping"]
    state = _make_state(queue, run_order={"executed": ["item01"]})

    rendered = render_run_summary_table(state, pal=Palette(False))

    rows = _extract_body_rows(rendered)
    assert len(rows) == len(queue)
    row = rows[0]
    assert row[0] == "01"
    assert row[1] == UNREADABLE_MARKER
    assert row[2] == UNREADABLE_MARKER
    assert row[3] == UNREADABLE_MARKER
    assert row[4] == UNREADABLE_MARKER
    assert row[5] == MALFORMED_ENTRY_TOKEN
    assert row[6] == "-"

    progress_line = _extract_progress_line(rendered)
    assert f"1 {MALFORMED_ENTRY_TOKEN}" in progress_line

    outcome_word = _extract_outcome_word(rendered)
    assert outcome_word != "COMPLETED"


def test_mixed_queue_with_success_item_never_claims_completed() -> None:
    """A mixed queue of malformed and executed items never claims COMPLETED and renders all rows."""
    well_formed_item = {
        "position": 2,
        "id6": "abc123",
        "setid": "set1",
        "action": "execute",
        "status": "executed",
        "verification_status": "pass",
        "attempts": [
            {"started_at": "2026-09-30T00:01:00Z", "ended_at": "2026-09-30T00:02:00Z"}
        ],
    }
    queue = ["not-a-mapping", well_formed_item]
    state = _make_state(queue, run_order={"executed": ["abc123"]})

    rendered = render_run_summary_table(state, pal=Palette(False))

    rows = _extract_body_rows(rendered)
    assert len(rows) == len(queue)

    # Malformed row
    malformed_rows = [r for r in rows if r[5] == MALFORMED_ENTRY_TOKEN]
    assert len(malformed_rows) == 1
    m_row = malformed_rows[0]
    assert m_row[1] == UNREADABLE_MARKER
    assert m_row[2] == UNREADABLE_MARKER

    # Well-formed row
    wf_rows = [r for r in rows if r[2] == "abc123"]
    assert len(wf_rows) == 1
    w_row = wf_rows[0]
    assert w_row[5] == "executed"
    assert w_row[6] == "pass"

    progress_line = _extract_progress_line(rendered)
    assert f"1 {MALFORMED_ENTRY_TOKEN}" in progress_line
    assert "1 executed" in progress_line

    outcome_word = _extract_outcome_word(rendered)
    assert outcome_word != "COMPLETED"


def test_mixed_queue_without_run_order() -> None:
    """A mixed queue without run_order renders both entries honestly."""
    well_formed_item = {
        "position": 2,
        "id6": "def456",
        "setid": "set2",
        "action": "execute",
        "status": "reviewed",
        "verification_status": "-",
        "attempts": [],
    }
    queue = ["not-a-mapping", well_formed_item]
    state = _make_state(queue, run_order=None)

    rendered = render_run_summary_table(state, pal=Palette(False))

    rows = _extract_body_rows(rendered)
    assert len(rows) == len(queue)
    assert any(
        r[5] == MALFORMED_ENTRY_TOKEN and r[2] == UNREADABLE_MARKER for r in rows
    )
    assert any(r[5] == "reviewed" and r[2] == "def456" for r in rows)

    outcome_word = _extract_outcome_word(rendered)
    assert outcome_word != "COMPLETED"
