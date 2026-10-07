"""Behavioral tests pinning lifecycle glyph rendering in the run summary table.

IPD qhpov0 / backlog phdpbf / spec uonrjg Section 5 / Section 9.1 / Section 9.4.
"""

from __future__ import annotations

import re
from typing import Any, Set

from agent_workflows import render_stream, term as _T
from agent_workflows.render_stream import Palette, render_run_summary_table

_BOX_START_CHARS = ("╭", "│", "├", "╰", "+", "|")


def _box_drawing_widths(rendered: str) -> Set[int]:
    """Return the set of distinct visible column widths of lines starting with box-drawing chars."""
    widths: Set[int] = set()
    for line in rendered.splitlines():
        if line and line[0] in _BOX_START_CHARS:
            widths.add(_T.visible_width(line))
    return widths


def _extract_body_rows(rendered: str) -> list[list[str]]:
    """Extract table rows as lists of cell contents (stripped of ANSI and outer borders)."""
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


def _make_state(queue: list[Any]) -> dict[str, Any]:
    return {
        "repo": "/repo",
        "run_id": "run-test-lifecycle-glyph",
        "created_at": "2026-10-02T12:00:00Z",
        "updated_at": "2026-10-02T12:05:00Z",
        "queue": queue,
    }


def test_status_cell_carries_section_5_unicode_glyphs() -> None:
    """Status cell carries the Section 5 glyph ahead of the native word for blocked and executed items."""
    queue = [
        {
            "position": 1,
            "id6": "item01",
            "setid": "set1",
            "action": "execute",
            "status": "blocked",
            "verification_status": "-",
            "attempts": [],
        },
        {
            "position": 2,
            "id6": "item02",
            "setid": "set1",
            "action": "execute",
            "status": "executed",
            "verification_status": "pass",
            "attempts": [
                {
                    "started_at": "2026-10-02T12:00:00Z",
                    "ended_at": "2026-10-02T12:01:00Z",
                }
            ],
        },
    ]
    state = _make_state(queue)
    rendered = render_run_summary_table(state, pal=Palette(False), use_unicode=True)

    rows = _extract_body_rows(rendered)
    assert len(rows) == 2
    # Row 1: blocked carries U+26A0 U+FE0E
    assert rows[0][5] == "\u26a0\ufe0e blocked"
    # Row 2: executed carries ✓
    assert rows[1][5] == "✓ executed"


def test_status_cell_ascii_mode_emits_section_5_fallbacks() -> None:
    """In ASCII mode, Status cell emits exact Section 5 ASCII fallbacks and no Unicode graphemes."""
    queue = [
        {
            "position": 1,
            "id6": "item01",
            "setid": "set1",
            "action": "execute",
            "status": "blocked",
            "verification_status": "-",
            "attempts": [],
        },
        {
            "position": 2,
            "id6": "item02",
            "setid": "set1",
            "action": "execute",
            "status": "executed",
            "verification_status": "pass",
            "attempts": [
                {
                    "started_at": "2026-10-02T12:00:00Z",
                    "ended_at": "2026-10-02T12:01:00Z",
                }
            ],
        },
    ]
    state = _make_state(queue)
    rendered = render_run_summary_table(
        state, pal=Palette(False, use_unicode=False), use_unicode=False
    )

    rows = _extract_body_rows(rendered)
    assert len(rows) == 2
    assert rows[0][5] == "! blocked"
    assert rows[1][5] == "+ executed"
    assert "\u26a0" not in rendered
    assert "✓" not in rendered


def test_table_rectangular_across_render_modes() -> None:
    """Table is rectangular (single distinct visible width) in unstyled, styled, and ASCII-box modes."""
    queue = [
        {
            "position": 1,
            "id6": "item01",
            "setid": "set1",
            "action": "execute",
            "status": "blocked",
            "verification_status": "-",
            "attempts": [],
        },
        {
            "position": 2,
            "id6": "item02",
            "setid": "set1",
            "action": "execute",
            "status": "executed",
            "verification_status": "pass",
            "attempts": [
                {
                    "started_at": "2026-10-02T12:00:00Z",
                    "ended_at": "2026-10-02T12:01:00Z",
                }
            ],
        },
        {
            "position": 3,
            "id6": "item03",
            "setid": "set1",
            "action": "execute",
            "status": "reviewed",
            "verification_status": "-",
            "attempts": [],
        },
    ]
    state = _make_state(queue)

    # 1. Unstyled Unicode
    rendered_unstyled = render_run_summary_table(
        state, pal=Palette(False), use_unicode=True
    )
    widths_unstyled = _box_drawing_widths(rendered_unstyled)
    assert len(widths_unstyled) == 1, f"Expected 1 width, got {widths_unstyled}"

    # 2. Styled Unicode
    rendered_styled = render_run_summary_table(
        state, pal=Palette(True), use_unicode=True
    )
    widths_styled = _box_drawing_widths(rendered_styled)
    assert len(widths_styled) == 1, f"Expected 1 width, got {widths_styled}"

    # 3. ASCII box
    rendered_ascii = render_run_summary_table(
        state, pal=Palette(False, use_unicode=False), use_unicode=False
    )
    widths_ascii = _box_drawing_widths(rendered_ascii)
    assert len(widths_ascii) == 1, f"Expected 1 width, got {widths_ascii}"


def test_palette_disabled_output_has_no_ansi_escapes() -> None:
    """Palette(False) output contains no ANSI escape sequences."""
    queue = [
        {
            "position": 1,
            "id6": "item01",
            "setid": "set1",
            "action": "execute",
            "status": "blocked",
            "verification_status": "-",
            "attempts": [],
        },
        {
            "position": 2,
            "id6": "item02",
            "setid": "set1",
            "action": "execute",
            "status": "executed",
            "verification_status": "pass",
            "attempts": [
                {
                    "started_at": "2026-10-02T12:00:00Z",
                    "ended_at": "2026-10-02T12:01:00Z",
                }
            ],
        },
    ]
    state = _make_state(queue)
    rendered = render_run_summary_table(state, pal=Palette(False), use_unicode=True)
    assert "\x1b" not in rendered


def test_malformed_entry_renders_unknown_glyph() -> None:
    """A malformed queue entry row renders the unknown glyph '?' rather than crashing."""
    queue = ["not-a-mapping"]
    state = _make_state(queue)
    rendered = render_run_summary_table(state, pal=Palette(False), use_unicode=True)

    rows = _extract_body_rows(rendered)
    assert len(rows) == 1
    assert rows[0][5] == "? malformed-entry"


def test_ascii_mode_has_no_non_ascii_codepoints() -> None:
    """In use_unicode=False mode with completed and blocked items, output has NO codepoints above U+007F."""
    queue = [
        {
            "position": 1,
            "id6": "item01",
            "setid": "set1",
            "action": "execute",
            "status": "executed",
            "verification_status": "pass",
            "attempts": [
                {
                    "started_at": "2026-10-02T12:00:00Z",
                    "ended_at": "2026-10-02T12:01:00Z",
                    "tokens": {"total": 120, "input": 80, "output": 40, "cache": 0},
                }
            ],
        },
        {
            "position": 2,
            "id6": "item02",
            "setid": "set1",
            "action": "execute",
            "status": "blocked",
            "verification_status": "-",
            "attempts": [],
        },
    ]
    state = _make_state(queue)
    rendered = render_run_summary_table(
        state, pal=Palette(False, use_unicode=False), use_unicode=False
    )
    non_ascii = sorted({f"U+{ord(c):04X} ({c})" for c in rendered if ord(c) > 127})
    assert not non_ascii, f"Expected no non-ASCII codepoints, got: {non_ascii}"
