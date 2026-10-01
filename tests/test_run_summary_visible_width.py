"""Regression tests asserting run summary table is rectangular in visible columns.

Guards against misalignments caused by zero-width Unicode characters (combining marks,
variation selectors, format controls) in table cells or banners.
IPD 4taj2e / backlog 8xcsjr.
"""

from __future__ import annotations

import unittest
from typing import Set

from agent_workflows import render_stream, term as _T

_BOX_START_CHARS = ("╭", "│", "├", "╰", "+", "|")


def _box_drawing_widths(rendered: str) -> Set[int]:
    """Return the set of distinct visible column widths of lines starting with box-drawing chars."""
    widths: Set[int] = set()
    for line in rendered.splitlines():
        if line and line[0] in _BOX_START_CHARS:
            widths.add(_T.visible_width(line))
    return widths


class RunSummaryVisibleWidthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cell_queue_state = {
            "run_id": "run-test-cell",
            "queue": [
                {
                    "position": 1,
                    "id6": "m11111",
                    "setid": "s\u26a0\ufe0e1",
                    "status": "executed",
                    "action": "execute",
                    "verification_status": "pass",
                },
                {
                    "position": 2,
                    "id6": "m22222",
                    "setid": "plain-set",
                    "status": "executed",
                    "action": "execute",
                    "verification_status": "pass",
                },
            ],
        }

        # Banner with an exit_reason long enough to widen the table beyond natural width,
        # containing NFD combining accent 'cafe\u0301' (U+0301 is category Mn).
        self.long_nfd_exit_reason = (
            "FAILED (merge refused: worktree cafe\u0301/path/to/a/very/long/component/"
            "that/widens/the/summary/table/banner/beyond/natural/column/widths/and/exercises/max_banner_w)"
        )
        self.banner_queue_state = {
            "run_id": "run-test-banner",
            "queue": [
                {
                    "position": 1,
                    "id6": "m11111",
                    "setid": "set1",
                    "status": "failed",
                    "action": "execute",
                },
            ],
        }

        self.ascii_queue_state = {
            "run_id": "run-test-ascii",
            "queue": [
                {
                    "position": 1,
                    "id6": "m11111",
                    "setid": "set1",
                    "status": "executed",
                    "action": "execute",
                    "verification_status": "pass",
                },
                {
                    "position": 2,
                    "id6": "m22222",
                    "setid": "set2",
                    "status": "executed",
                    "action": "execute",
                    "verification_status": "pass",
                },
            ],
        }

    def test_cell_variation_selector_is_rectangular_unstyled(self) -> None:
        rendered = render_stream.render_run_summary_table(
            self.cell_queue_state, pal=render_stream.Palette(False)
        )
        widths = _box_drawing_widths(rendered)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )

    def test_cell_variation_selector_is_rectangular_styled(self) -> None:
        rendered = render_stream.render_run_summary_table(
            self.cell_queue_state, pal=render_stream.Palette(True)
        )
        widths = _box_drawing_widths(rendered)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )

    def test_cell_variation_selector_is_rectangular_ascii_box(self) -> None:
        rendered = render_stream.render_run_summary_table(
            self.cell_queue_state, pal=render_stream.Palette(False), use_unicode=False
        )
        widths = _box_drawing_widths(rendered)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )

    def test_banner_zero_width_accent_is_rectangular_unstyled(self) -> None:
        rendered = render_stream.render_run_summary_table(
            self.banner_queue_state,
            pal=render_stream.Palette(False),
            exit_reason=self.long_nfd_exit_reason,
        )
        widths = _box_drawing_widths(rendered)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )

    def test_banner_zero_width_accent_is_rectangular_styled(self) -> None:
        rendered = render_stream.render_run_summary_table(
            self.banner_queue_state,
            pal=render_stream.Palette(True),
            exit_reason=self.long_nfd_exit_reason,
        )
        widths = _box_drawing_widths(rendered)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )

    def test_banner_zero_width_accent_is_rectangular_ascii_box(self) -> None:
        rendered = render_stream.render_run_summary_table(
            self.banner_queue_state,
            pal=render_stream.Palette(False),
            exit_reason=self.long_nfd_exit_reason,
            use_unicode=False,
        )
        widths = _box_drawing_widths(rendered)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )

    def test_all_ascii_table_is_rectangular_and_stable(self) -> None:
        render1 = render_stream.render_run_summary_table(
            self.ascii_queue_state, pal=render_stream.Palette(False)
        )
        render2 = render_stream.render_run_summary_table(
            self.ascii_queue_state, pal=render_stream.Palette(False)
        )
        widths = _box_drawing_widths(render1)
        self.assertEqual(
            len(widths),
            1,
            f"Expected exactly 1 distinct visible width, got {widths}",
        )
        self.assertEqual(
            render1,
            render2,
            "Renders of the same ASCII queue must be byte-identical",
        )


if __name__ == "__main__":
    unittest.main()
