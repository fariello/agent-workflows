- Id: ytz6z4
- Status: done
- Set: ytz6z4
- Priority: high
- Work-Kind: bug
- Summary: Runner post-merge revalidation counts the core-tier wall-time budget overrun (load-dependent) as a red suite with no failing test ids, refusing integration of all-green lanes

## Workflow history
- 2026-10-17 done (aw set): Fixed in 8b798b0b8 (no plan; direct fix): runner-launched suites default AW_CORE_BUDGET_ENFORCE=0 via suite_cache.build_suite_child_env and the run-evidence path; bare pytest still enforces. Regression tests in tests/test_core_tier_selection.py.
- 2026-10-17 same-status (aw backlog): status -> open
- 2026-10-17 created (aw backlog): Runner post-merge revalidation counts the core-tier wall-time budget overrun (load-dependent) as a red suite with no failing test ids, refusing integration of all-green lanes
