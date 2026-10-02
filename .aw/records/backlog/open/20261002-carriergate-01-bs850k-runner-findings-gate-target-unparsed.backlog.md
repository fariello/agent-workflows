- Id: bs850k
- Status: open
- Blocks-Release: next
- Set: carriergate
- Priority: medium
- Work-Kind: bug
- Summary: Runner review-findings dependency gate never fires: dependency_status_detailed passes a parsed ItemDependency to dependency_target_id6, which re-parses a string and returns None for every edge, so subject_gating_blocks receives the raw token and matches no Subject-Id

## Workflow history
- 2026-10-02 created (aw backlog): Found while authoring plan rpw4sb from backlog hc6n7r (F-09). Excluded from that plan's scope: different module, and a bug needing a release gate a followup plan must not carry.
