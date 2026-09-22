- Id: 770fkp
- Status: done
- Blocks-Release: next
- Set: 770fkp
- Priority: high
- Work-Kind: bug
- Summary: 31 tests fail inside any runner lane because AW_EXECUTION_ROLE=worker refuses aw ipd begin/finalize

## Workflow history
- 2026-09-22 set (aw backlog): closed by aw oc run: IPD e4lkv5 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260917-lanesuite-01-e4lkv5-make-the-suite-green-inside-a-lane-by-controlling-the-execut.ipd.md); evidence .aw/records/plans/executed/20260917-lanesuite-01-e4lkv5-make-the-suite-green-inside-a-lane-by-controlling-the-execut.ipd.md
- 2026-09-18 graduated (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 graduated (aw set): Graduated into IPD e4lkv5 (lanesuite Order 01); design handed off, code not yet written
- 2026-09-17 created (aw backlog): 31 tests fail inside any runner lane because AW_EXECUTION_ROLE=worker refuses aw ipd begin/finalize

Measured at 4a1bb873 by plan s16omw (rununify Order 10), while taking the pre-change baseline the plan's V-05 requires.

WHAT IS WRONG. A bare `python3 -m pytest` inside a driver-created lane reports 31 failures at a HEAD whose suite is otherwise green:

  $ python3 -m pytest
  31 failed, 7645 passed, 3 skipped, 2 xfailed in 105.51s

  $ env -u AW_EXECUTION_ROLE python3 -m pytest
  7676 passed, 3 skipped, 2 xfailed in 99.32s

CAUSE. `aw oc run` exports AW_EXECUTION_ROLE=worker into each lane. agent_workflows/ipd_lifecycle.py:69 correctly refuses begin/finalize for a worker-role process with AW-LIFECYCLE-ROLE-001. Thirty-one tests across five files (tests/test_ipd_lifecycle_cli.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_backlog_close_in_lane.py) invoke those verbs directly WITHOUT neutralizing the variable, so they inherit the ambient role from the environment rather than controlling it.

WHY IT MATTERS, and why it is worth a high priority despite being a test-isolation defect rather than a product defect. Every plan executed in a lane is required by its own validation contract to run the suite and compare against a baseline. A red baseline invites two bad outcomes: an executor attributes 31 pre-existing failures to their own change and burns a turn chasing them, or an executor learns to wave failures away as environmental and stops noticing a real one. The refusal itself is correct behavior and must not be weakened.

SUGGESTED FIX: the affected tests should control the variable explicitly (monkeypatch/env-clear in setUp, or a fixture that asserts the role it intends), so they test the role they mean rather than the role they inherit. Do NOT relax AW-LIFECYCLE-ROLE-001.
