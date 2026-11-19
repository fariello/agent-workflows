- Id: 34o2zs
- Status: open
- Blocks-Release: next
- Set: 34o2zs
- Priority: medium
- Work-Kind: bug
- Summary: Fix test_e2e_producer_blocks_release_duplicate mock after artifact_meta migration

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-19 same-status (aw set): Gate next release for live bug
- 2026-11-17 created (aw backlog): Fix test_e2e_producer_blocks_release_duplicate mock after artifact_meta migration

Pre-existing non-core test failure observed on unmodified HEAD in tests/test_backlog_metadata_duplicate_and_gate_summary.py::BacklogMetadataDuplicateAndGateSummaryTests::test_e2e_producer_blocks_release_duplicate. The test patches releases._BLOCKS_RELEASE_LINE_RE to simulate a producer that leaves a duplicate - Blocks-Release: bullet, which was bypassed by 2xwb9b (moving status_set onto artifact_meta) and removed by 3466h8 (moving releases onto artifact_meta.set_legacy_bullet_line). Update the test to exercise duplicate bullet detection through a valid producer simulation or fixture without relying on the retired private regex.
