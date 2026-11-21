- Id: emvcpn
- Status: open
- Set: emvcpn
- Work-Kind: feature
- Priority: high
- Summary: Proposal from 723ct1: Split 723ct1 E-01's remaining 43 hand conversions into two
- Short-Description: Proposal from 723ct1: Split 723ct1 E-01's remaining 43 hand conversions into two
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from 723ct1: Split 723ct1 E-01's remaining 43 hand conversions into two

## Agent Proposal from 723ct1

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: 723ct1
- Lane-Branch: aw/lane/723ct1
- Blocked-By: 723ct1 Batch rule step 4 and D-3 stop hand conversion when an item hand count exceeds 25; E-01 (G4c-723ct1-1) has 43 hand refusals (42 static in 653ndz F-30 [7 in tests/test_orchestrator_probe_payload.py, 0 in tests/test_orchestrator_probe_quotes.py, 1 in tests/test_orchestrator_probe_scope.py, 34 in tests/test_orchestrator_readiness.py] plus 1 apply-time not-equivalent in tests/test_orchestrator_probe_scope.py).
- Kind: different-approach
- Size: material

### Why
723ct1 was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-01 into <=25-site items (including splitting single module tests/test_orchestrator_readiness.py at 34 hand refusals across two passes) exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split 723ct1 E-01's remaining 43 hand conversions into two <=25-site items while retaining E-01 Step-3 proved codemod rewrites (072f7d7c9), completed E-02 (a05a159db), and recorded plan evidence (d1e4c8424) already committed on aw/lane/723ct1: (1) E-01a (21 hand): tests/test_orchestrator_probe_payload.py (7 unsupported-shape across SYNTHETIC_ORCHESTRATOR, SYNTHETIC_ORCHESTRATOR_RESIDUAL_GAP, doc_wrapped, doc, and 3 Workflow-history regex replacement sites; 4 body prose legacy-kept), tests/test_orchestrator_probe_scope.py (1 unsupported-shape at line 51 + 1 apply-time not-equivalent at line 71 in _make_plan_text where test_case_h passes 7-char id6s orc8agy/chi8agy; plus E-09 helper census for _make_plan_text and write_plan), and tests/test_orchestrator_readiness.py pass 1 (_make_orchestrator: 12 unsupported-shape at lines 61-81), noting tests/test_orchestrator_probe_quotes.py already landed 2 standard rewrites with 0 hand remaining; (2) E-01b (22 hand): tests/test_orchestrator_readiness.py pass 2 (_make_child: 14 unsupported-shape at lines 169-179 + test_condition_2_child_status_terminal: 8 unsupported-shape at lines 301-304).

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-191-723ct1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md
- tests/test_orchestrator_probe_payload.py
- tests/test_orchestrator_probe_quotes.py
- tests/test_orchestrator_probe_scope.py
- tests/test_orchestrator_readiness.py
