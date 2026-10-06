- Id: 7yz545
- Status: open
- Graduated-To: attmodel
- Set: runsdash
- Priority: medium
- Work-Kind: feature
- Summary: Record the resolved model id per attempt in run state so run analytics can compare models (about 2/3 of runs record no model today)

## Workflow history
- 2026-10-06 open (aw set): 1u4olp returned to authoring: uncovered obligation: The Set-level obligations are: the three children's test files all present and green; re-run graduation to complete the handoff
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 1u4olp, czut8j, ov2c9n, r5fk4k
- 2026-09-27 created (aw backlog): Record the resolved model id per attempt in run state so run analytics can compare models (about 2/3 of runs record no model today)

Measured 2026-09-27: only about 100 of 298 run state.json files carry options.model or options.cost_attribution.model, and OpenCode session JSONL carries no model id. The runsdash dashboard (97i0ao) labels those rows (unrecorded). The drivers should persist the model the host actually used on each attempt (OpenCode: from the session's assistant message modelID; Antigravity: from settings), so model comparisons cover the whole corpus going forward.
