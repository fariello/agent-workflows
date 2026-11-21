- Id: op7dwg
- Status: done
- Set: op7dwg
- Work-Kind: feature
- Priority: high
- Summary: Proposal from 872zd9: Split 872zd9 E-01's rema
- Short-Description: Proposal from 872zd9: Split 872zd9 E-01's rema

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 done (aw set): Superseded by maintainer decision raising Batch rule step 4 hand-refusal cap from 25 to 100 on the 12 over-cap metastore chunks and salvaging completed lane commits onto main
- 2026-11-21 created (aw backlog): Proposal from 872zd9: Split 872zd9 E-01's rema

## Agent Proposal from 872zd9

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: 872zd9
- Lane-Branch: aw/lane/872zd9
- Blocked-By: 872zd9 Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-01 (G2a-872zd9-1) has 39 hand refusals (35 static in 653ndz F-30 plus 4 apply-time not-equivalent in tests/test_check_engine.py).
- Size: material

### Why
872zd9 was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-01 into smaller items or child plans exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split 872zd9 E-01's remaining 39 hand conversions while retaining the completed E-02 (27cdc01db) and E-01 Step 3 proved codemod rewrites (ee1c48fc4, including 85/85 rewrites in tests/test_check_engine_release_gate.py) already committed on aw/lane/872zd9: (1) E-01a (14 hand): tests/test_check_engine_metadata_region.py (2 hand), tests/test_check_engine_plan_date_filename.py (12 hand plus deletion of _build_plan), and tests/test_check_engine_release_gate.py (0 hand, Step 3 complete); (2) E-01b (25 hand): tests/test_check_engine.py (21 static plus 4 apply-time not-equivalent = 25 hand, within the 25-site limit).

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-180-872zd9-move-backlog-release-gate-and-check-test-data-chunk-6-of-7-o.ipd.md
- tests/test_check_engine_metadata_region.py
- tests/test_check_engine_plan_date_filename.py
- tests/test_check_engine.py
