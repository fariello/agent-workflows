- Id: rryabb
- Status: open
- Set: rryabb
- Work-Kind: bug
- Priority: medium
- Summary: test_runner_resume_clears_stop: three stale-stop resume tests fail in thorough suite on main
- Short-Description: test_runner_resume_clears_stop: three stale-stop resume tests fail in thorough suite on main
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): test_runner_resume_clears_stop: three stale-stop resume tests fail in thorough suite on main

## Problem

Three tests in `tests/test_runner_resume_clears_stop.py` fail on `main` (`b61073951`) under `aw suite --thorough`:

1. `ResumeReconciliationAndStopLevelsTests::test_reconcile_one_item_does_not_bypass_second_indeterminate_item` (`AssertionError: True is not false` on `stop_path.exists()`).
2. `ResumeReconciliationAndStopLevelsTests::test_resume_clears_stale_stop_for_all_four_levels_and_dispatches`.
3. `ResumeCLIClearsStaleStopTests::test_manual_resume_clears_stale_stop_while_self_restart_preserves` (`AssertionError: 1 is not None` on `seen_levels[-1]`).

## Expected behavior

Investigate why stale stop files are not cleared as asserted in these three tests (or whether runner environment variables leak into the test fixtures) and restore green thorough-suite execution.

## Discovery context

Observed on `main` (`b61073951`) during `aw suite --thorough` in IPD `ffceq0`.
