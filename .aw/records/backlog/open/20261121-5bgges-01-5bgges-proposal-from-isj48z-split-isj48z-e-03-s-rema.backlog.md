- Id: 5bgges
- Status: open
- Set: 5bgges
- Work-Kind: feature
- Priority: high
- Summary: Proposal from isj48z: Split isj48z E-03's rema
- Short-Description: Proposal from isj48z: Split isj48z E-03's rema
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Proposal from isj48z: Split isj48z E-03's rema

## Agent Proposal from isj48z

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: isj48z
- Lane-Branch: aw/lane/isj48z
- Blocked-By: isj48z Batch rule step 4 stops hand conversion when an item hand count exceeds 25; E-03 (G1b-isj48z-3) has 38 hand refusals (38 static in 653ndz F-30 plus 0 apply-time not-equivalent, with tests/test_releases_line_writers.py at 28 alone).
- Kind: different-approach
- Size: material

### Why
isj48z was approved on 2026-11-16 before 653ndz executed on 2026-11-21 to measure F-30. Re-splitting E-03 (including a single module at 28 hand refusals) into smaller items or child plans exceeds this turn's authorized execution scope and requires plan-structure approval.

### Proposed Change
Split isj48z E-03's remaining 38 hand conversions while retaining the completed E-01 (bed067fb6), E-02 (5b4f30049), and E-03 Step 3 proved codemod rewrites (428d23787) already committed on aw/lane/isj48z: (1) E-03a (10 hand): tests/test_releases.py (5 hand) and tests/test_releases_sibling_line_writers_bounding.py (5 hand); (2) E-03b: tests/test_releases_line_writers.py (28 hand alone) split into two sequential passes of 14 hand each (TestSetBlocksReleaseLine 14 sites, then TestSetFromBacklogLine 14 sites), or reclassify its 12 expected-string local variables as setter-byte assertion and grant a single-module exception for the remaining 16 direct legacy line-writer inputs.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-177-isj48z-move-backlog-release-gate-and-check-test-data-chunk-3-of-7-o.ipd.md
- tests/test_releases_line_writers.py
- tests/test_releases.py
- tests/test_releases_sibling_line_writers_bounding.py
