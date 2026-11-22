- Id: t90xwx
- Status: open
- Set: t90xwx
- Work-Kind: followup
- Priority: medium
- Summary: Convert inline legacy backlog fixture in tests/test_partition_set_cohesion.py (commit 284f9b6f9) onto RecordBuilder
- Short-Description: Convert inline legacy backlog fixture in tests/test_partition_set_cohesion.py (commit 284f9b6f9) onto RecordBuilder

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Convert inline legacy backlog fixture in tests/test_partition_set_cohesion.py (commit 284f9b6f9) onto RecordBuilder

## Context

Commit `284f9b6f9` (`feat(partition): add --split-sets flag and suggest it when Set cohesion collapses shards`) landed after `7qxey9` E-07 was salvaged and added an inline hand-built legacy backlog fixture loop in `tests/test_partition_set_cohesion.py` (`test_split_sets_backlog_items`, lines 1588-1595) that writes `- Id:`, `- Set:`, `- Status:`, and `- Priority:` bullets directly instead of calling `tests.record_builder.RecordBuilder().backlog(...)`.

## Acceptance

Replace the inline backlog fixture literal in `tests/test_partition_set_cohesion.py` with `RecordBuilder().backlog(..., text_only=True)` and verify identical per-test outcomes on `tests/test_partition_set_cohesion.py` and zero remaining `F-01` matches in that test.
