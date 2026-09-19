- Id: 3dg3dv
- Status: open
- Blocks-Release: next
- Set: 3dg3dv
- Priority: medium
- Work-Kind: bug
- Summary: rununify yrqyxb Scope-Paths omits three test files carrying execute_item source pins

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): rununify yrqyxb Scope-Paths omits three test files carrying execute_item source pins

Plan yrqyxb (rununify 07) declares ten test files in Scope-Paths as the source-inspection pins that read execute_item's body. Measured at HEAD 85c14014 there are 21 such pins across 12 files, and three of those files are absent from the declaration: tests/test_review_lane_isolation.py (1 pin, asserts disposition-before-integration ordering), tests/test_runner_backlog_close_in_lane.py (2 pins, asserts close-in-lane-before-integrate ordering), tests/test_rununify_conflicts.py (1 pin, asserts agy's truthful isolate value at driver_begin). Two of the three carry ORDERING pins over the safety gates plan F-2 calls load-bearing, so the plan also under-counts the ordering pins as six when the real figure is eight. Any future plan that performs the execute_item split must declare all twelve. Evidence: the reproducible scanner committed at .aw/state/lane-submissions/run-20260917T023628Z-4108757/08-yrqyxb/attempt-1/evidence/pin_scan.py and the inventory in E03-pin-inventory.md.
