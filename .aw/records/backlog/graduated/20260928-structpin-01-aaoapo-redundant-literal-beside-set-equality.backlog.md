- Id: aaoapo
- Status: graduated
- Graduated-To: structpin
- Set: structpin
- Priority: low
- Work-Kind: chore
- Summary: Two tests pin a redundant literal length beside a correct set-equality assertion, so the literal only goes stale

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 44c42h
- 2026-09-28 created (aw backlog): Two tests pin a redundant literal length beside a correct set-equality assertion, so the literal only goes stale

OBSERVED 2026-09-28 while sweeping the code-structure pins for backlog `5zyuc8` (plan `b02ohu`). Two tests assert a literal COUNT on the line beside an assertion that already pins the same collection by SET EQUALITY, so the literal proves nothing the neighbouring line does not, and its only future is to go stale when the collection legitimately grows.

CASE 1: `tests/test_reaskscore_composed.py::TestSharedConstants::test_terminal_states_three_copies_are_mutually_equal` asserts `len(runner_shared.TERMINAL_STATES) == 24`, commented "23 + `retired`". The real invariants are in the same test and are untouched by this: the mutual equality of the three copies, and the absence of the deferrable pair.

CASE 2: `tests/test_term.py::AuthoredSixteenColorPaletteTests::test_palette_coverage_named_colors_separations_and_collapses` asserts `len(T.STAGE_COLOR_16) == 20` on the line AFTER asserting `set(T.STAGE_COLOR_16) == set(LS.ALL_STAGES)`. The set equality already pins the palette to the stage vocabulary exactly, so the `20` is a derived fact restated as a literal.

WHY THIS IS A CHORE AND NOT A BUG, on the user-perceptible-impact test: neither literal is wrong today and neither costs a user any wait. The cost is the "tax on correct changes" backlog `5zyuc8` describes, paid once, by whoever next adds a terminal status or a stage. That is real but small and invisible to users.

WHY IT WAS NOT FIXED IN `b02ohu`: these are counts over a RUNTIME DATA STRUCTURE, not over code structure obtained by reading source, so they are outside that plan scope (which was the source-read pins A1..A6) and outside the guard in `76ic0k` (which detects production-source reads and deliberately does NOT detect count shapes, because `assertEqual(len(x), 3)` is syntactically indistinguishable from legitimate assertions about collections of outputs). Widening either plan would have been opportunistic scope growth.

SUGGESTED FIX: delete both literals and keep the set-equality assertions. Confirm first that no OTHER assertion in either test depends on the literal, and re-run the two files.
