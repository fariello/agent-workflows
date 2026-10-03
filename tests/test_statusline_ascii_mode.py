"""Regression guard asserting ASCII-mode purity, visible width parity, and boundary preservation.

Spec uonrjg Section 9.4 contract: guaranteed single-byte alignment in ASCII mode.
Validates IPD mzrr7x (E-01 through E-05).
"""

from __future__ import annotations

import io
import time
import pytest

from agent_workflows import term as _T
from agent_workflows.render_stream import (
    Palette,
    Statusline,
    format_progress_bar,
    format_statusline_lines,
)


class TestStatuslineAsciiModePurity:
    """Assert ASCII-mode purity, width parity, and boundary properties across renderer and class."""

    @pytest.mark.parametrize("enabled", [False, True], ids=["plain", "styled"])
    @pytest.mark.parametrize(
        ("cur", "tot"),
        [
            (0, 0),  # degenerate zero total
            (0, 10),  # un-started run (0/N)
            (1, 10),  # started run
            (3, 10),  # fractional eighth state
            (5, 10),  # mid state
            (10, 10),  # completed run (N/N)
            (3, 80),  # fractional eighths on wider total
            (79, 80),  # 99% boundary
        ],
    )
    def test_format_statusline_lines_ascii_purity_swept_states(
        self, enabled: bool, cur: int, tot: int
    ) -> None:
        """Level 1 (renderer): format_statusline_lines under use_unicode=False emits only ASCII."""
        pal = Palette(enabled, use_unicode=False)
        lines = format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1700000000.0,
            item_start_ts=1700000000.0,
            last_act_ts=1700000000.0,
            current_idx=cur,
            total_items=tot,
            setid="statuscov",
            id6="mzrr7x",
            pal=pal,
            use_unicode=False,
        )
        assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"
        for i, line in enumerate(lines):
            non_ascii = [c for c in line if ord(c) >= 128]
            assert not non_ascii, f"Line {i} for cur={cur}, tot={tot}, enabled={enabled} contains non-ASCII: {non_ascii}"
        # All 4 lines must share the exact same visible terminal width
        widths = {_T.visible_width(line) for line in lines}
        assert (
            len(widths) == 1
        ), f"Expected uniform visible width across 4 lines, got {widths}"

    @pytest.mark.parametrize("enabled", [False, True], ids=["plain", "styled"])
    @pytest.mark.parametrize(
        ("cur", "tot"),
        [
            (0, 0),
            (0, 10),
            (1, 10),
            (3, 10),
            (5, 10),
            (10, 10),
            (3, 80),
            (79, 80),
        ],
    )
    def test_statusline_class_ascii_purity_swept_states(
        self, enabled: bool, cur: int, tot: int
    ) -> None:
        """Level 2 (class): Statusline with a use_unicode=False palette forwards ASCII mode."""
        pal = Palette(enabled, use_unicode=False)
        sl = Statusline(
            pal=pal,
            stream=io.StringIO(),
            current_idx=cur,
            total_items=tot,
            setid="statuscov",
            id6="mzrr7x",
            run_start_mono=time.monotonic(),
        )
        box = sl.render_line()
        lines = box.splitlines()
        assert (
            len(lines) == 4
        ), f"Expected 4 lines in rendered statusline, got {len(lines)}"
        for i, line in enumerate(lines):
            non_ascii = [c for c in line if ord(c) >= 128]
            assert not non_ascii, f"Statusline line {i} for cur={cur}, tot={tot}, enabled={enabled} contains non-ASCII: {non_ascii}"
        widths = {_T.visible_width(line) for line in lines}
        assert (
            len(widths) == 1
        ), f"Expected uniform visible width across 4 statusline lines, got {widths}"

    def test_statusline_explicit_use_unicode_override(self) -> None:
        """Statusline constructor honors explicit use_unicode parameter override."""
        pal = Palette(True, use_unicode=True)
        sl = Statusline(
            pal=pal,
            stream=io.StringIO(),
            current_idx=3,
            total_items=10,
            setid="statuscov",
            id6="mzrr7x",
            use_unicode=False,
        )
        box = sl.render_line()
        non_ascii = [c for c in box if ord(c) >= 128]
        assert (
            not non_ascii
        ), f"Expected pure ASCII with use_unicode=False override, got: {non_ascii}"

    @pytest.mark.parametrize(
        ("cur", "tot"),
        [
            (0, 0),
            (0, 10),
            (1, 10),
            (3, 10),
            (5, 10),
            (10, 10),
            (3, 80),
            (79, 80),
            (80, 80),
        ],
    )
    def test_progress_bar_visible_width_parity_and_ascii_purity(
        self, cur: int, tot: int
    ) -> None:
        """ASCII progress bar matches Unicode progress bar visible width at all swept states."""
        u_bar = format_progress_bar(cur, tot, width=10, use_unicode=True)
        a_bar = format_progress_bar(cur, tot, width=10, use_unicode=False)
        # ASCII purity
        non_ascii = [c for c in a_bar if ord(c) >= 128]
        assert (
            not non_ascii
        ), f"ASCII bar for cur={cur}, tot={tot} contains non-ASCII: {non_ascii}"
        # Width parity
        u_width = _T.visible_width(u_bar)
        a_width = _T.visible_width(a_bar)
        assert (
            a_width == u_width
        ), f"Width mismatch for ({cur}/{tot}): ascii width {a_width} != unicode width {u_width}"

    def test_progress_bar_boundary_distinguishability(self) -> None:
        """Boundary preservation (F-12): started != unstarted (1/80 != 0/80) and incomplete != complete (79/80 != 80/80)."""
        b0 = format_progress_bar(0, 80, width=10, use_unicode=False)
        b1 = format_progress_bar(1, 80, width=10, use_unicode=False)
        b79 = format_progress_bar(79, 80, width=10, use_unicode=False)
        b80 = format_progress_bar(80, 80, width=10, use_unicode=False)

        assert (
            b1 != b0
        ), f"Boundary collision: started run (1/80: '{b1}') must differ from unstarted (0/80: '{b0}')"
        assert (
            b79 != b80
        ), f"Boundary collision: incomplete run (79/80: '{b79}') must differ from complete (80/80: '{b80}')"
