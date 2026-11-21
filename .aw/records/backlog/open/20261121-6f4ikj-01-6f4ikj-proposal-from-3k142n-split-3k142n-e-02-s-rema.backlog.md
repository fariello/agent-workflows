- Id: 6f4ikj
- Status: open
- Set: 6f4ikj
- Work-Kind: feature
- Priority: high
- Summary: Proposal from 3k142n: Split 3k142n E-02's rema
- Short-Description: Proposal from 3k142n: Split 3k142n E-02's rema
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from 3k142n: Split 3k142n E-02's rema

## Agent Proposal from 3k142n

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: 3k142n
- Lane-Branch: aw/lane/3k142n
- Blocked-By: 3k142n Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-02 (G4b-3k142n-2) has 29 hand refusals (29 static in 653ndz F-30 [0 in tests/test_dependency_block_reporting.py + 20 in tests/test_executed_transition_gate_e2e.py + 7 in tests/test_executed_transition_gate.py + 2 in tests/test_finalize_refusal_findings.py] plus 0 apply-time not-equivalent).
- Kind: different-approach
- Size: material

### Why
3k142n was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-02 into two <=25-site items exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split 3k142n E-02's remaining 29 hand conversions into two <=25-site items while retaining completed E-01 (ed68bdb3f), E-02 Step-3 proved codemod rewrites (dcc7859a7), completed E-03 (a7d806644), and recorded plan evidence (16031a1b6, ecb42d5ae) already committed on aw/lane/3k142n: (1) E-02a (20 hand): tests/test_executed_transition_gate_e2e.py (20 unsupported-shape refusals across _write_executed_prompt, _flip_status_in_place, _move_into_executed, _commit_plan_already_executed, _edit_already_executed_plan, _substitute_plan_at_executed_path, _flip_status_inside_executed, _write_plan_at, _make_lane, and _hand_edit_no_merge, plus 9 legacy-kept sites and E-09 helper census for _write_plan and _write_plan_at); (2) E-02b (9 hand): tests/test_executed_transition_gate.py (7 remaining unsupported-shape refusals across headingless/preamble/merge/raw-transition tests) and tests/test_finalize_refusal_findings.py (2 unsupported-shape refusals in test_child_finalize_prints_findings_exactly_once), noting tests/test_dependency_block_reporting.py already reached 0 remaining F-01 matches via Step 3.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-187-3k142n-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-6.ipd.md
- tests/test_executed_transition_gate_e2e.py
- tests/test_executed_transition_gate.py
- tests/test_finalize_refusal_findings.py
