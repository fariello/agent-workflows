- Id: 2zknl8
- Status: done
- Graduated-To: ztvubn
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Clearing Blocks-Release with dash writes literal dash instead of unsetting field in status_set._render_gate_fields
- Short-Description: Clearing Blocks-Release with dash writes literal dash instead of unsetting field in status_set._render_gate_fields
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 done (aw backlog): closed by aw agy run: IPD ztvubn executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261127-metastore-323-ztvubn-fix-post-cutover-status-set-selectors-and-runner-commit-log.ipd.md); evidence .aw/records/plans/executed/20261127-metastore-323-ztvubn-fix-post-cutover-status-set-selectors-and-runner-commit-log.ipd.md
- 2026-11-27 graduated (aw set): Graduated to Order 323 child plan ztvubn in Set metastore.
- 2026-11-27 created (aw backlog): Clearing Blocks-Release with dash writes literal dash instead of unsetting field in status_set._render_gate_fields

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), agent_workflows/status_set.py::_render_gate_fields (around lines 3662-3693) merges fields={'blocks_release': '-'} as a literal string '-' instead of removing the blocks_release field when a user runs 'aw backlog set <id6> --status done --blocks-release -'. check_engine.evaluate_blocking_close then observes blocks_release='-' and refuses to close the de-gated backlog item. Discovered during IPD psm9ac (batch B test conversion); blocks 3 tests in tests/test_backlog_handoff_close.py (test_case_6d, test_case_7_degated_allowed, test_kntbbc_case_6_degated_executed_same_gate_superseded_ungated_plan_allowed).
