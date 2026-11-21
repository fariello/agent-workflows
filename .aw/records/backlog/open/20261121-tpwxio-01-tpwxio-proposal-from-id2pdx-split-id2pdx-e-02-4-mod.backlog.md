- Id: tpwxio
- Status: open
- Set: tpwxio
- Work-Kind: feature
- Priority: high
- Summary: Proposal from id2pdx: Split id2pdx E-02 (4 mod
- Short-Description: Proposal from id2pdx: Split id2pdx E-02 (4 mod
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from id2pdx: Split id2pdx E-02 (4 mod

## Agent Proposal from id2pdx

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: id2pdx
- Lane-Branch: aw/lane/id2pdx
- Blocked-By: id2pdx Batch rule step 4 and Review Decision D-2 stop hand conversion when an item hand count exceeds 25; E-02 (G1a-id2pdx-2) has 44 hand refusals (42 static in 653ndz F-30 plus 2 apply-time not-equivalent refusals in G1a-id2pdx-2-codemod.json)
- Kind: different-approach
- Size: material

### Why
id2pdx was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-02 into smaller items or a new child plan exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split id2pdx E-02 (4 modules, 44 hand refusals) into two items or child plans of 22 hand refusals each (both within the 25-refusal ceiling): (1) tests/test_backlog_duplicate_guard.py (14 hand) and tests/test_backlog_gate_follows_status.py (8 hand) = 22 hand; (2) tests/test_backlog_handoff_close.py (13 hand, plus helper deletions _write_backlog_item, _write_plan, _write_spec) and tests/test_backlog_history_dedup_parity.py (9 hand) = 22 hand. Retain the completed E-01 work and E-02 Step 3 proved codemod rewrites already committed on branch aw/lane/id2pdx.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-175-id2pdx-move-backlog-release-gate-and-check-test-data-chunk-1-of-7-o.ipd.md
- tests/test_backlog_duplicate_guard.py
- tests/test_backlog_gate_follows_status.py
- tests/test_backlog_handoff_close.py
- tests/test_backlog_history_dedup_parity.py
