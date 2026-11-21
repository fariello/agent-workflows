- Id: ptkizn
- Status: open
- Set: ptkizn
- Work-Kind: feature
- Priority: high
- Summary: Proposal from 2fn0vd: Split 2fn0vd's remaining
- Short-Description: Proposal from 2fn0vd: Split 2fn0vd's remaining
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from 2fn0vd: Split 2fn0vd's remaining

## Agent Proposal from 2fn0vd

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: 2fn0vd
- Lane-Branch: aw/lane/2fn0vd
- Blocked-By: 2fn0vd Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-01 (G1a-2fn0vd-1) has 42 hand refusals (40 static in 653ndz F-30 plus 2 apply-time not-equivalent, with test_backlog_metadata_duplicate_and_gate_summary.py at 28 alone) and E-02 (G1a-2fn0vd-2) has 44 hand refusals (42 static in 653ndz F-30 plus 2 apply-time not-equivalent).
- Kind: different-approach
- Size: material

### Why
2fn0vd was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting both items (including a single module at 28 hand refusals) into smaller items or child plans exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split 2fn0vd's remaining hand conversions while retaining the 33 proved Step 3 codemod rewrites already committed on aw/lane/2fn0vd (a6416ac0c, f28438d9a): (1) E-01a (14 hand): tests/test_backlog_history_empty_rule.py (7), tests/test_backlog_new_gate_vocabulary.py (0), tests/test_backlog_positional_close_gate.py (7); (2) E-01b: tests/test_backlog_metadata_duplicate_and_gate_summary.py (28 hand alone) split into two sequential passes (16 sites for _make_item and test_gate_summary_rules, then 12 sites for duplicate-bullet/sub-bullet syntax tests and _make_item deletion) or granted a single-module exception; (3) E-02a (20 hand): tests/test_backlog_production.py (10, plus _write_backlog_item and _write_plan_content deletion), tests/test_backlog_set_adapter.py (2), tests/test_backlog_transition_authority.py (8); (4) E-02b (24 hand): tests/test_backlog.py alone.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-176-2fn0vd-move-backlog-release-gate-and-check-test-data-chunk-2-of-7-o.ipd.md
- tests/test_backlog_history_empty_rule.py
- tests/test_backlog_metadata_duplicate_and_gate_summary.py
- tests/test_backlog_new_gate_vocabulary.py
- tests/test_backlog_positional_close_gate.py
- tests/test_backlog_production.py
- tests/test_backlog.py
- tests/test_backlog_set_adapter.py
- tests/test_backlog_transition_authority.py
