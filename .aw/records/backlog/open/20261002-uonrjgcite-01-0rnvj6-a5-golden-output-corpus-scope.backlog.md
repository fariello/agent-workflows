- Id: 0rnvj6
- Status: open
- Set: uonrjgcite
- Priority: low
- Work-Kind: followup
- Summary: Decide whether uonrjg criterion A5 should extend to a committed lifecycle golden-output corpus

## Workflow history
- 2026-10-02 created (aw backlog): Decide whether uonrjg criterion A5 should extend to a committed lifecycle golden-output corpus

RAISED BY plan xtensb (backlog nzqj6m) as its OQ-01, while sweeping spec uonrjg's criteria for stale citations and uncovered surfaces.

THE QUESTION. Criterion A5 of spec uonrjg reads: '⚠️ and ↩️ do not occur in lifecycle constants or golden output'. Plan xtensb closes the 'lifecycle constants' half exhaustively (every stage in lifecycle_style.STAGE_ORDER, both the Unicode glyph and the ASCII fallback, plus the text-selector check on lifecycle_style.MULTI_CODEPOINT_GLYPHS), and covers the 'golden output' half by RENDERING at all three color depths and both Unicode modes through format_lifecycle_marker and style_lifecycle_text. That is the strongest assertion available today.

WHY IT IS STILL OPEN. No committed lifecycle golden-file corpus exists to scan, so 'golden output' currently has no second referent beyond the rendered-output assertion. If a snapshot corpus is later added for lifecycle rows, A5 would want extending to it, otherwise an emoji-presentation glyph could enter a committed snapshot with nothing failing.

NOT BLOCKING, and nothing is unasserted today as a result. The decision is only reachable once such a corpus exists; until then there is no surface to assert against.

WHAT WOULD CLOSE IT: either a ruling that the rendered-output assertion is the whole of A5's 'golden output' obligation (in which case amend A5 to say so plainly, so a later reader does not re-raise this), or the addition of a lifecycle snapshot corpus together with an A5 assertion over it.
