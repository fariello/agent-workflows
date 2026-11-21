- Id: vrvlj5
- Status: open
- Set: vrvlj5
- Work-Kind: feature
- Priority: high
- Summary: Proposal from qqaqw8: Split qqaqw8 E-02's rema
- Short-Description: Proposal from qqaqw8: Split qqaqw8 E-02's rema
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from qqaqw8: Split qqaqw8 E-02's rema

## Agent Proposal from qqaqw8

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: qqaqw8
- Lane-Branch: aw/lane/qqaqw8
- Blocked-By: qqaqw8 Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-02 (G4a-qqaqw8-2) has 34 hand refusals (34 static in 653ndz F-30 [16 in tests/test_plan_priority_required.py + 12 in tests/test_plan_readiness_recheck.py + 6 in tests/test_plans_archive.py] plus 0 apply-time not-equivalent).
- Kind: different-approach
- Size: material

### Why
qqaqw8 was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-02 into two <=25-site items exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split qqaqw8 E-02's remaining 34 hand conversions into two <=25-site items while retaining completed E-01 (ea5df43e1), E-02 Step-3 proved codemod rewrite (f23ee6357), and recorded E-01/V-01 evidence (12104000a) already committed on aw/lane/qqaqw8: (1) E-02a (16 hand): tests/test_plan_priority_required.py (16 hand refusals across _build_test_plan and scaffold/setter line-index checks, plus helper census for _build_test_plan and ApprovalBackstopTests._plan); (2) E-02b (18 hand): tests/test_plan_readiness_recheck.py (12 hand refusals across _oq, _plan, and test_the_pin_FAILS_against_a_deliberately_widened_writer) and tests/test_plans_archive.py (6 hand refusals in _plan), plus helper census for _plan, _oq, and _review_history.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-185-qqaqw8-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-4.ipd.md
- tests/test_plan_priority_required.py
- tests/test_plan_readiness_recheck.py
- tests/test_plans_archive.py
