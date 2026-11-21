- Id: dxz25q
- Status: open
- Set: dxz25q
- Work-Kind: feature
- Priority: high
- Summary: Proposal from 2zo3g5: Split 2zo3g5 E-03's rema
- Short-Description: Proposal from 2zo3g5: Split 2zo3g5 E-03's rema
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from 2zo3g5: Split 2zo3g5 E-03's rema

## Agent Proposal from 2zo3g5

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: 2zo3g5
- Lane-Branch: aw/lane/2zo3g5
- Blocked-By: 2zo3g5 Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-03 (G4a-2zo3g5-3) has 88 hand refusals (87 static in 653ndz F-30 [23 in tests/test_ipd_lifecycle_cli.py + 64 in tests/test_ipd_lint.py] plus 1 apply-time not-equivalent at tests/test_ipd_lint.py line 55 _conforming_child).
- Kind: different-approach
- Size: material

### Why
2zo3g5 was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-03 (including splitting single module tests/test_ipd_lint.py at 65 hand refusals across three <=25-site passes) exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split 2zo3g5 E-03's remaining 88 hand conversions while retaining completed E-01 (0215934c0), completed E-02 (da70e0a1f), and E-03 Step-3 proved codemod rewrites (15c765380) already committed on aw/lane/2zo3g5: (1) E-03a (23 hand): tests/test_ipd_lifecycle_cli.py (23 hand sites, including helper census for _write_plan/_ready_plan_text/_completed_plan_text); (2) E-03b (23 hand): tests/test_ipd_lint.py pass 1 (_conforming_child [1 not-equivalent], _executed_child [4], StructuralRuleTests [4], ReadinessAttestationTests [5], ReadinessRequiredTests [6], CheckpointPhaseTests [3]); (3) E-03c (19 hand): tests/test_ipd_lint.py pass 2 (PostTransitionExecutedHistoryTests [3], DispositionTests [2], DensityAdvisoryLintTests [2], CitationAnchorAdvisoryTests [2], _with_scope_paths [2], _approved [5], ParenthesizedActorParsesInTheAttributionRegex [3]); (4) E-03d (23 hand): tests/test_ipd_lint.py pass 3 (SetidLengthLintTests [6], TerminalPathStatusLintTests [9], CitationAnchorsOnDemandTests [6], DateMetadataLintTests [2]).

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-184-2zo3g5-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-3.ipd.md
- tests/test_ipd_lifecycle_cli.py
- tests/test_ipd_lint.py
