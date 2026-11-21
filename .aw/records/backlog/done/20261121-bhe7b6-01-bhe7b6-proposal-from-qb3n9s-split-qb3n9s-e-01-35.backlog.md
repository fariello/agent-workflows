- Id: bhe7b6
- Status: done
- Set: bhe7b6
- Work-Kind: feature
- Priority: high
- Summary: Proposal from qb3n9s: Split qb3n9s E-01 (35 remaining hand) and E-02 (30 remaining
- Short-Description: Proposal from qb3n9s: Split qb3n9s E-01 (35 remaining hand) and E-02 (30 remaining

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 done (aw set): Superseded by maintainer decision raising Batch rule step 4 hand-refusal cap from 25 to 100 on the 12 over-cap metastore chunks and salvaging completed lane commits onto main
- 2026-11-21 created (aw backlog): Proposal from qb3n9s: Split qb3n9s E-01 (35 remaining hand) and E-02 (30 remaining

## Agent Proposal from qb3n9s

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: qb3n9s
- Lane-Branch: aw/lane/qb3n9s
- Blocked-By: qb3n9s Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-01 (G4c-qb3n9s-1) has 35 hand refusals (33 static in 653ndz F-30 plus 2 apply-time not-equivalent in tests/test_gradcover_end_to_end.py) and E-02 (G4c-qb3n9s-2) has 30 hand refusals (28 static in 653ndz F-30 plus 2 apply-time not-equivalent, with tests/test_orchestrator_child_retired.py at 27 alone).
- Size: material

### Why
qb3n9s was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-01 and E-02 into <=25-site items (including splitting single module tests/test_orchestrator_child_retired.py at 27 hand refusals across two passes) exceeds this turn authorized execution scope and requires plan-structure approval.

### Proposed Change
Split qb3n9s E-01 (35 remaining hand) and E-02 (30 remaining hand) into four <=25-site items while retaining Step-3 proved codemod rewrites (aba2f0a4b, 4ab679b5a) and recorded plan evidence (e52fa8f10) already committed on aw/lane/qb3n9s: (1) E-01a (20 hand): tests/test_coverage_not_written.py (20 unsupported-shape in _create_orchestrator_and_child; 1 rewrite already landed); (2) E-01b (15 hand): tests/test_coverage_record.py (1 unsupported-shape indirect setter-byte ordering check at text.find), tests/test_gradcover_end_to_end.py (8 unsupported-shape plus 2 not-equivalent in _orchestrator_template and _child_template, 8 legacy-kept, plus E-09 helper census for _write_backlog_item), and tests/test_implementing_spec_replan.py (4 dynamic-construction in _write_spec and _write_plan, 2 legacy-kept, plus E-09 helper census); (3) E-02a (15 hand): tests/test_orchestrator_child_retired.py pass 1 (_make_orchestrator: 12 unsupported-shape), tests/test_orchestrator_kind_derivation.py (1 not-equivalent in _run_legacy_manifest_queue_build; 2 rewrites already landed), and tests/test_orchestrator_not_approved_reason.py (2 dynamic-construction in _make_repo; 1 rewrite already landed); (4) E-02b (15 hand): tests/test_orchestrator_child_retired.py pass 2 (_make_child: 14 unsupported-shape plus 1 not-equivalent in test_skip_conditions_no_set_dirty_whole_set standalone no-Set plan).

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-190-qb3n9s-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-9.ipd.md
- tests/test_coverage_not_written.py
- tests/test_coverage_record.py
- tests/test_gradcover_end_to_end.py
- tests/test_implementing_spec_replan.py
- tests/test_orchestrator_child_retired.py
- tests/test_orchestrator_kind_derivation.py
- tests/test_orchestrator_not_approved_reason.py
