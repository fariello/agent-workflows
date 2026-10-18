- Id: twz0tw
- Status: open
- Set: twz0tw
- Priority: low
- Work-Kind: followup
- Summary: tests/test_core_tier_selection.py gate_suite tests (over_budget_tree[run-evidence|subprocess], honors_explicit_enforce) failed once in the bare routine gate under heavy host load and passed in isolation and on rerun; cause unknown, possibly timing-sensitive

## Workflow history
- 2026-10-18 created (aw backlog): tests/test_core_tier_selection.py gate_suite tests (over_budget_tree[run-evidence|subprocess], honors_explicit_enforce) failed once in the bare routine gate under heavy host load and passed in isolation and on rerun; cause unknown, possibly timing-sensitive
- 2026-10-18 note (ej30u4 attempt 2): recurred, same 3 tests, `3 failed, 1662 passed` in 358.02s under host load (normal ~40s); the 3 then passed in isolation (`3 passed, 8 deselected in 240.87s`) and the bare gate rerun reported `1665 passed, 11 warnings in 36.27s`. Two occurrences in one day, both only under load.
