- Id: l76ir6
- Status: open
- Blocks-Release: next
- Set: l76ir6
- Priority: medium
- Work-Kind: bug
- Summary: Statusline pads box columns with len() rather than visible_width, so any Ambiguous-width or VS-bearing glyph misaligns the box

## Workflow history
- 2026-09-20 created (aw backlog): Found executing plan qdd5jq (lifeglyph 07).

FOUND WHILE EXECUTING plan `qdd5jq` (Set `lifeglyph`, spec `uonrjg`).

WHAT IS WRONG. `render_stream.format_statusline_lines` computes every column width and every pad with bare `len()` (the `col2_w`/`col3_w`/`col5_w`..`col10_w` computations and their `f"{...:>{w}s}"` pads). Spec `uonrjg` Section 9.4 bullet 4 forbids exactly this ("no use of `len(styled_text)` to compute a visible column"), because `len()` counts a zero-width variation selector as a column and counts ANSI bytes as columns.

WHY IT DID NOT BITE FOR THE CELL I OWNED. Plan `qdd5jq` E-03 added the ACTIVITY cell to this box and routes that ONE cell through `term.visible_width` via `format_activity_cell`, so the `recovering` glyph `↩︎` (U+21A9 U+FE0E, two code points and one column) aligns correctly. Measured: the four box lines report visible widths (130, 130, 130, 130) with that activity, while raw `len()` of the cell is 13 against a visible 12. The REST of the box is still measured with `len()`.

WHY IT IS STILL A LIVE DEFECT. Any other cell that ever carries a VS-bearing or East-Asian-Ambiguous grapheme will misalign, and the failure is silent. The `setid`/`id6` cell is the realistic exposure: those are free-form identifiers interpolated straight into a `len()`-measured column.

SCOPE NOTE. This is deliberately NOT fixed in `qdd5jq`: that plan's scope fence covers the lifecycle rows and its own activity cell, and converting the whole box is a wider change to a layout pinned byte-for-byte by `tests/test_render_stream.py::test_format_statusline_user_example_box_layout`.

WHERE. `agent_workflows/render_stream.py`, `format_statusline_lines` (the `col*_w` width computations and their pads).
