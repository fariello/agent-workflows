- Id: i2i81x
- Status: graduated
- Graduated-To: revcost
- Set: revsteps
- Priority: high
- Work-Kind: feature
- Summary: aw runs analyze: break review cost down by token type, steps, context, session reuse, tool use, run commit and label, model, and redo counts

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175005Z-1383890: avg8qv
- 2026-10-19 created (aw backlog): aw runs analyze: break review cost down by token type, steps, context, session reuse, tool use, run commit and label, model, and redo counts

Needed to measure the plan-review redesign (spec k3yx72 Section 13) and to make review cost visible. The full request, with the facts measured on 2026-10-17 (1,311 OpenCode review attempts, 16.05B tokens, 98.8 percent cache reads, $10,528), is prompt okj4bg at .aw/records/prompts/pending/20261018-revsteps-02-okj4bg-runs-analyze-review-cost.prompt.md. Done when every question in that prompt's Section 3 is answerable with an aw runs query command, or its missing data is listed.
