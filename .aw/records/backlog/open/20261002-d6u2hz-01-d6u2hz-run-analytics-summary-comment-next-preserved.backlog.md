- Id: d6u2hz
- Status: open
- Set: d6u2hz
- Priority: low
- Work-Kind: chore
- Summary: refresh the run_analytics_cli query-summary comment once a --fields projection preserves next, since its stated reason becomes false

## Workflow history
- 2026-10-02 created (aw backlog): refresh the run_analytics_cli query-summary comment once a --fields projection preserves next, since its stated reason becomes false

FILED BY PLAN `6rcby1` (backlog `kkjrqr`) as the carrier for a comment that plan deliberately leaves alone.

`run_analytics_cli._emit_query_agent` renders its summary WITHOUT a field-projection context, and a 12-line comment above the call explains why. Its load-bearing sentence is:

> The summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`, so projecting this record could drop the paging continuation

Plan `6rcby1` adds `next` to `_PRESERVED_FIELDS`, which makes that CAUSAL CLAIM false: after it lands, projecting the record could no longer drop the continuation, so the stated reason no longer holds.

WHAT DOES NOT CHANGE, and why this is a comment refresh rather than a code change: the no-context call stays CORRECT on the OTHER ground the same comment gives two paragraphs down. A query's summary must report the engine's `total`/`emitted`/`omitted` rather than `render_stream`'s own `--limit` truncation counts, because the latter knows nothing about the row bound the query engine already applied and would report `omitted: 0` for a page that left rows unread. So the call shape is right; only its first justification expires.

WHY `6rcby1` DID NOT JUST FIX IT: `agent_workflows/run_analytics_cli.py` is not in that plan's `- Scope-Paths:`, adding it would put a fifth file in scope for a prose-only edit, and mixing a comment refresh into a contract fix is what its scope check explicitly refuses.

NOTE THE LINEAGE, because this comment has now been invalidated twice by the same mechanism. Plan `gygujf` left it stale and filed `cm80ge`; `cm80ge` was executed as plan `mcdvx0`, which REWROTE the comment into its current form and filed `kkjrqr` for the behavior it described; `6rcby1` now graduates `kkjrqr` and falsifies the sentence `mcdvx0` wrote. The fix here should describe the POST-FIX reality (the call passes no context because the counts must be the engine's, full stop) rather than explaining a workaround, so the comment stops tracking a defect that no longer exists.

DO NOT START THIS UNTIL `6rcby1` IS EXECUTED: until then the existing comment is accurate and editing it would make it wrong.
