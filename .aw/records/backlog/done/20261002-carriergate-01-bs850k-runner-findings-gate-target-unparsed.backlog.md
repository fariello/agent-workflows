- Id: bs850k
- Status: done
- Blocks-Release: next
- Set: carriergate
- Priority: medium
- Work-Kind: bug
- Summary: Runner review-findings dependency gate never fires: dependency_status_detailed passes a parsed ItemDependency to dependency_target_id6, which re-parses a string and returns None for every edge, so subject_gating_blocks receives the raw token and matches no Subject-Id

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD k81fqx executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-carriergate-01-k81fqx-pass-the-parsed-edge-s-id6-to-the-runner-review-findings-dep.ipd.md); evidence .aw/records/plans/executed/20261012-carriergate-01-k81fqx-pass-the-parsed-edge-s-id6-to-the-runner-review-findings-dep.ipd.md
- 2026-10-02 created (aw backlog): Found while authoring plan rpw4sb from backlog hc6n7r (F-09). Excluded from that plan's scope: different module, and a bug needing a release gate a followup plan must not carry.
