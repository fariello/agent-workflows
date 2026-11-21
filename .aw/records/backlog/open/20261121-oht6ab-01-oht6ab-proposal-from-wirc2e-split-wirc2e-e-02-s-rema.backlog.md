- Id: oht6ab
- Status: open
- Set: oht6ab
- Work-Kind: feature
- Priority: high
- Summary: Proposal from wirc2e: Split wirc2e E-02's rema
- Short-Description: Proposal from wirc2e: Split wirc2e E-02's rema
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from wirc2e: Split wirc2e E-02's rema

## Agent Proposal from wirc2e

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: wirc2e
- Lane-Branch: aw/lane/wirc2e
- Blocked-By: wirc2e Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-02 (G1b-wirc2e-2) has 44 hand refusals (44 static in 653ndz F-30 plus 0 apply-time not-equivalent, with tests/test_handoff_ready_gate.py at 26 alone).
- Kind: different-approach
- Size: material

### Why
wirc2e was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-02 (including a single module at 26 hand refusals) into smaller items or child plans exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split wirc2e E-02's remaining 44 hand conversions while retaining the completed E-01 (ee49a5d94), E-03 (0bb6fce3d), and E-02 Step 3 proved codemod rewrites (5736d8c0b) already committed on aw/lane/wirc2e: (1) E-02a (18 hand): tests/test_orchestrator_retire_closes_backlog.py (6 hand) and tests/test_runner_backlog_close_behavior.py (12 hand); (2) E-02b (26 hand): tests/test_handoff_ready_gate.py split into two sequential passes (Pass 1 converts _make_conforming_child [3 sites] and _make_conforming_orchestrator [14 sites] = 17 hand sites; Pass 2 converts and deletes _make_backlog_item [7 sites] and _make_spec [2 sites] = 9 hand sites), or grant a single-module exception at 26 sites since all 26 sit inside four helper functions.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-179-wirc2e-move-backlog-release-gate-and-check-test-data-chunk-5-of-7-o.ipd.md
- tests/test_handoff_ready_gate.py
- tests/test_orchestrator_retire_closes_backlog.py
- tests/test_runner_backlog_close_behavior.py
