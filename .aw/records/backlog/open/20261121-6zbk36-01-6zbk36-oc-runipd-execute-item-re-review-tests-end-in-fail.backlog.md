- Id: 6zbk36
- Status: open
- Set: 6zbk36
- Work-Kind: bug
- Priority: medium
- Summary: oc_runipd.execute_item re-review tests end in fail-gate instead of reviewed
- Short-Description: oc_runipd.execute_item re-review tests end in fail-gate instead of reviewed
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): oc_runipd.execute_item re-review tests end in fail-gate instead of reviewed

Observed during aw suite --thorough (epsj2v validation): tests/test_rereview_reviewed_plan.py::TestRereviewExecutionTurn::test_execute_item_core_full_auto_skips_auto_approve and test_execute_item_core_rereview_demotes_and_turn_sees_to_review fail with AssertionError: 'fail-gate' != 'reviewed'.
