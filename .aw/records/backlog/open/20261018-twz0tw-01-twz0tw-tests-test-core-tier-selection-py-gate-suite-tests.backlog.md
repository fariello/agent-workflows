- Id: twz0tw
- Status: open
- Set: twz0tw
- Priority: low
- Work-Kind: followup
- Summary: tests/test_core_tier_selection.py gate_suite tests (over_budget_tree[run-evidence|subprocess], honors_explicit_enforce) failed once in the bare routine gate under heavy host load and passed in isolation and on rerun; cause unknown, possibly timing-sensitive

## Workflow history
- 2026-10-18 created (aw backlog): tests/test_core_tier_selection.py gate_suite tests (over_budget_tree[run-evidence|subprocess], honors_explicit_enforce) failed once in the bare routine gate under heavy host load and passed in isolation and on rerun; cause unknown, possibly timing-sensitive
- 2026-10-18 note (ej30u4 attempt 2): recurred, same 3 tests, `3 failed, 1662 passed` in 358.02s under host load (normal ~40s); the 3 then passed in isolation (`3 passed, 8 deselected in 240.87s`) and the bare gate rerun reported `1665 passed, 11 warnings in 36.27s`. Two occurrences in one day, both only under load.
- 2026-10-18 note (ej30u4 attempt 2, combined-red fix): cause found. `suite_cache.run_full_suite` takes a machine-wide test-suite slot (`suite_slot`, lock dir `$XDG_RUNTIME_DIR/agent-workflows`, 2 slots on 12 CPUs). When the enclosing suite run or peer drivers hold every slot, the three gate_suite tests wait for one and hit the 240s per-test wall hang guard (reproduced: both slots held -> `TestHangTimeout ... exceeded its 240s wall ceiling`, log shows `waiting for a test-suite slot (2 of 2 held)`). Fixed in tests by pointing `AW_SUITE_LOCK_DIR` at a per-test private dir; with both real slots held the 3 tests now pass in 2.80s. Candidate to close as done.
