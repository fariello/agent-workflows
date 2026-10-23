- Id: jycfw3
- Status: graduated
- Graduated-To: jycfw3
- Set: jycfw3
- Priority: low
- Work-Kind: followup
- Summary: tests/test_suite_cache.py run_full_suite calls (~L325, 377, 544, 552) do not isolate AW_SUITE_LOCK_DIR, so under load they can wait on the machine-wide suite slot past the 240s per-test ceiling; same starvation fixed for test_core_tier_selection.py in 548fa71da (twz0tw)

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T221918Z-2698454: zyy2yg
- 2026-10-23 created (aw backlog): carried from plan f4txy2 deferred row 2
