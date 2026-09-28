- Id: 7yz545
- Status: open
- Set: runsdash
- Priority: medium
- Work-Kind: feature
- Summary: Record the resolved model id per attempt in run state so run analytics can compare models (about 2/3 of runs record no model today)

## Workflow history
- 2026-09-27 created (aw backlog): Record the resolved model id per attempt in run state so run analytics can compare models (about 2/3 of runs record no model today)

Measured 2026-09-27: only about 100 of 298 run state.json files carry options.model or options.cost_attribution.model, and OpenCode session JSONL carries no model id. The runsdash dashboard (97i0ao) labels those rows (unrecorded). The drivers should persist the model the host actually used on each attempt (OpenCode: from the session's assistant message modelID; Antigravity: from settings), so model comparisons cover the whole corpus going forward.
