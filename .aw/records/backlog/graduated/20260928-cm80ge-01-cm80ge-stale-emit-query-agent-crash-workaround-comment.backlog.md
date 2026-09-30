- Id: cm80ge
- Status: graduated
- Graduated-To: cm80ge
- Set: cm80ge
- Priority: low
- Work-Kind: chore
- Summary: run_analytics_cli._emit_query_agent's crash-workaround comment goes stale once the --fields projection defect is fixed

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: mcdvx0
- 2026-09-28 created (aw backlog): Filed while authoring plan gygujf (from backlog 3f4ayi): that plan removes the crash this comment describes as unfixed, but deliberately leaves run_analytics_cli.py out of scope.

MEASURED 2026-09-28 at HEAD `71aee0d3` while authoring plan `gygujf` from backlog item `3f4ayi`.

`run_analytics_cli._emit_query_agent` carries a 12-line comment block above its `render_summary` call that explains, correctly and in detail, why it renders its summary WITHOUT the output context: doing so with `ctx.fields` set raises `ValueError: Invalid aw.agent/v1 record: Summary record missing required field 'total' ...`. That comment is the reason backlog item `3f4ayi` exists at all, and it is the best in-tree description of the defect.

ONCE `3f4ayi` IS FIXED, PART OF THAT COMMENT BECOMES FALSE. It states the bug "lives in `renderers.py` / `agent_schema.py`, neither of which is in this plan's Scope-Paths", that it "was previously unreachable because no production caller passed `fields` to `render_summary`", and that it "is REPORTED (see the execution report) and NOT fixed here". After plan `gygujf` lands, `filter_record_fields` preserves the per-kind required fields and the crash is gone, so a future reader of that comment is told a live defect exists when it does not, and may re-file it or work around it again.

WHAT MUST NOT CHANGE, and this is why the fix is a comment edit and not a code edit. The no-context call is SEMANTICALLY CORRECT on its own terms, independent of the crash: a query's summary must report the QUERY ENGINE's `total`/`emitted`/`omitted` rather than the stream renderer's, and projecting those counts away would destroy the `emitted + omitted == total` invariant that lets a caller tell a bounded answer from a complete one. The comment says this too, in its last paragraph, and that paragraph stays true. So the call site keeps its current behavior; only the stale crash narrative is rewritten.

SUGGESTED FIX: replace the crash-workaround paragraphs with a short statement of the surviving reason (the summary reports engine counts, not stream counts, so it deliberately takes no field projection), and cite `3f4ayi`/`gygujf` as the record of the defect that used to also force this shape. Keep the invariant paragraph. Do not change the call.

WHY IT IS A CHORE AND NOT A BUG: nothing a user runs behaves differently, and no output changes. The cost is a future maintainer reading a confident, detailed, wrong claim about the state of the code, which is real but not user-perceptible, so it does not gate a release.

NOT FIXED IN `gygujf`: `agent_workflows/run_analytics_cli.py` is deliberately absent from that plan's Scope-Paths. Adding it would put a fifth file in scope for a prose-only change and mix a comment refresh into a contract fix. Filed so the staleness has a carrier rather than living in that plan's prose. This item becomes actionable only once `gygujf` is executed.
