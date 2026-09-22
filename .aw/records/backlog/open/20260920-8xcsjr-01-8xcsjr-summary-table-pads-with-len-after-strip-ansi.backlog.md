- Id: 8xcsjr
- Status: open
- Blocks-Release: next
- Set: 8xcsjr
- Priority: medium
- Work-Kind: bug
- Summary: render_run_summary_table pads table cells with len(_strip_ansi(...)), which counts a variation selector as a column

## Workflow history
- 2026-09-20 created (aw backlog): Found executing plan qdd5jq (lifeglyph 07).

FOUND WHILE EXECUTING plan `qdd5jq` (Set `lifeglyph`, spec `uonrjg`).

WHAT IS WRONG. `render_stream.render_run_summary_table` measures every column with `len(_strip_ansi(str(cell)))`. Stripping ANSI is HALF the fix and the half that was already right; the remaining half is that `len()` still counts a ZERO-WIDTH code point as a column. `term.visible_width` is the shared primitive that does both (it is built on `strip_ansi` and skips `Mn`/`Me`/`Cf` categories).

WHY IT MATTERS NOW, WHERE IT DID NOT BEFORE. Plan `qdd5jq` E-02/E-03 converted this table's Status column to the shared lifecycle resolver, so its cells can now legitimately contain spec Section 5 glyphs, TWO of which carry U+FE0E: `⚠︎` (`blocked`) and `↩︎` (`recovering`). A `recovering` row (status `ran`, `interrupted`, `partial`, `substantially-complete` or `correction_required`) therefore pads one column short. Before the conversion this table's status cells were plain ASCII words, so the latent defect was unreachable.

CURRENT BLAST RADIUS IS SMALL, stated so the priority is honest: the Status column currently renders the WORD (styled) rather than the glyph, so the VS characters reach the cell only via the glyph-bearing paths. The measurement is wrong regardless, and the next change that puts a marker in a cell makes it visible.

FIX. Replace `len(_strip_ansi(x))` with `term.visible_width(x)` throughout this function, and its manual `" " * pad` arithmetic accordingly. `render_stream` may now import `term` (plan `qdd5jq` re-pointed that guard to an allowlist of proven leaf modules), so no new import barrier stands in the way.

WHERE. `agent_workflows/render_stream.py`, `render_run_summary_table` (the `col_widths` loop, the banner pads, the header/row/totals cell pads).
