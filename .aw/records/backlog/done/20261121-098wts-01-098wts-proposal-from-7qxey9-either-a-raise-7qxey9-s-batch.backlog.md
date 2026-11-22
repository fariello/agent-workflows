- Id: 098wts
- Status: done
- Set: 098wts
- Work-Kind: feature
- Priority: high
- Summary: Proposal from 7qxey9: Either (a) raise 7qxey9's Batch rule step 4 hand-refusal cap
- Short-Description: Proposal from 7qxey9: Either (a) raise 7qxey9's Batch rule step 4 hand-refusal cap

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 done (aw set): Superseded by maintainer decision raising Batch rule step 4 hand-refusal cap from 25 to 150 (and late-module cap from 8 to 20) on 8 remaining metastore plans and salvaging 7qxey9/nbfg7w lane commits onto main
- 2026-11-22 created (aw backlog): Proposal from 7qxey9: Either (a) raise 7qxey9's Batch rule step 4 hand-refusal cap

## Agent Proposal from 7qxey9

- Run-Id: run-20261122T004102Z-1599448
- Proposing-Item: 7qxey9
- Lane-Branch: aw/lane/7qxey9
- Blocked-By: 7qxey9 Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-04 (G4c-7qxey9-04) has 43 hand refusals (42 static in 653ndz F-30 [0 in tests/test_orchestrator_shape_composed.py + 12 in tests/test_orchestrator_shape_gate.py + 21 in tests/test_orchestrator_status_gate.py + 9 in tests/test_partition.py] plus 1 apply-time not-equivalent at tests/test_orchestrator_shape_gate.py L70-153).
- Size: material

### Why
7qxey9 was approved on 2026-11-16 before 653ndz measured F-30 and was not included in commit 6edbb2c83's 12-chunk cap update (25 -> 100); overriding the 25 stop gate or re-splitting E-04 exceeds this turn's authorized execution scope and requires plan-level approval.

### Proposed Change
Either (a) raise 7qxey9's Batch rule step 4 hand-refusal cap from 25 to 100 matching maintainer decision commit 6edbb2c83 (raw site count over-counts list elements in _make_orchestrator and .replace() pairs in _make_child/test_prepare_only_succeeds_on_conforming_queue) and salvage completed E-07 (3527c71fc) and E-04 Step-3 rewrites (9c1337935) onto main so the remaining 43 E-04 hand conversions and E-06 finish in one turn, or (b) split E-04's remaining 43 hand refusals into two <=25-site items (E-04a: tests/test_orchestrator_shape_gate.py [13] + tests/test_partition.py [9] = 22 hand, noting tests/test_orchestrator_shape_composed.py is already at 0 F-01 matches from Step 3; E-04b: tests/test_orchestrator_status_gate.py = 21 hand) while retaining committed work on aw/lane/7qxey9.

### Affected Paths
- .aw/records/plans/pending/20261107-metastore-39-7qxey9-move-spec-plan-lifecycle-orchestration-and-runner-test-data.ipd.md
- tests/test_orchestrator_shape_composed.py
- tests/test_orchestrator_shape_gate.py
- tests/test_orchestrator_status_gate.py
- tests/test_partition.py
