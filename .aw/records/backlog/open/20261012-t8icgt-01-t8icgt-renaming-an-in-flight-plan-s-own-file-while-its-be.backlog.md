- Id: t8icgt
- Status: open
- Blocks-Release: next
- Set: t8icgt
- Priority: low
- Work-Kind: bug
- Summary: renaming an in-flight plan's own file while its begin receipt is live is unguarded

## Workflow history
- 2026-10-12 created (aw backlog): renaming an in-flight plan's own file while its begin receipt is live is unguarded

Raised as F-07 of plan 69pxm5 (Set scoperewrite). Reproduction (review 2026-10-12 at ebe34e463, re-driven 2026-10-12 at 09cf2ec24 by tests/test_rename_receipt_guard.py test_i): with a begin receipt present at .aw/state/ipd-lifecycle/p22222.receipt.json, `aw rename plans p22222 --slug renamed --apply --no-commit` renames the executing plan's own file, rc 0. The receipt keys on the id6 (ipd_lifecycle.receipt_path_for), so finalize still finds the receipt; the open question is whether a runner holding the old plan path strands. This is a source-file move, not a citation rewrite, so 69pxm5's filter_in_flight_plan_edits cannot reach it. Measure whether a lane strands, then decide whether to refuse or report the self-rename of an in-flight plan.
