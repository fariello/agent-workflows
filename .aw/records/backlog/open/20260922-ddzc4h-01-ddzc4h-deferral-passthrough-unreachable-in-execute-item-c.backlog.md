- Id: ddzc4h
- Status: open
- Set: ddzc4h
- Priority: low
- Work-Kind: chore
- Summary: E-03's premise is false in a live turn: item status is 'running' at the first score, so a deferral can never be the pre-rescore disposition

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing skn8uk. reconcile_disposition's deferral passthrough reads item['status'] == INTEGRATION_DEFERRED_STATUS, but execute_item_core sets item['status'] = 'running' at dispatch, so the passthrough cannot fire on a live turn's first score and merge-retry can never be the 'before' value at the post-re-ask rescore point. The rescore's refusal to replace a deferral is therefore defence in depth rather than a live path (kept deliberately, and pinned by a scripted-reconcile test). Worth deciding whether the passthrough has ANY reachable caller in execute_item_core, or whether the deferral is only ever set downstream by record_integration_refusal, in which case the passthrough's comment overstates its role.
