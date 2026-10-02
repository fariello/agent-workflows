- Id: 4uw9gy
- Status: graduated
- Graduated-To: limitreach
- Blocks-Release: next
- Set: limitreach
- Priority: medium
- Work-Kind: bug
- Summary: aw check, aw index and aw search accept --limit under --agent and ignore it, so three further documented token-control surfaces are inert

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: 2zvxhx
- 2026-10-01 created (aw backlog): aw check, aw index and aw search accept --limit under --agent and ignore it, so three further documented token-control surfaces are inert

MEASURED 2026-10-01 at HEAD 74b301435 while authoring plan okiso1 from backlog item wdazvp.

wdazvp records --limit being inert on 'aw find --agent'. The defect is WIDER than that one verb, and the breadth was measured while resolving it rather than assumed.

A PARSER WALK RETURNS 250 LEAVES, OF WHICH NINE DECLARE --limit: aw check, aw find, aw group, aw index, aw rename, aw research index, aw runs analyze, aw runs query, aw search. Only ONE consumer of the resolved value exists anywhere in the package: renderers.AgentRenderer.render_stream reads ctx.limit, and before plan okiso1 it had ZERO production callers. run_analytics_cli.emit_query_agent_stream honors the bound by computing it itself in run_analytics_query (MAX_ROW_LIMIT, _parse_limit) rather than through ctx.limit.

MEASURED PER VERB, with and without the flag:

    aw search plans <pattern> --agent --limit 2  -> 1 line, identical to the run without --limit
    aw check plans --agent --limit 1             -> 1 record, same key set as without
    aw index plans --agent --limit 1             -> same single TSV line as without

So three further --agent surfaces accept a documented flag and discard it. docs/cli-output-contract.md Section 6 lists --limit as one of three token-control escape hatches with no stated restriction, and docs/cli-agent-protocol.md omits it entirely (that undercount is item 9qya0k).

NOTE WHAT --limit DOES MEAN ON TWO OF THE NINE, so a fixer does not 'unify' something that is already correct: on 'aw index' it is a HOT-WINDOW SIZE for INDEX.md (plans_index.DEFAULT_INDEX_LIMIT), a genuinely different meaning that is honored in the human path, and on 'aw research index' likewise. Those two are not the same defect as check and search, and conflating them would break a working feature.

WHY IT IS A BUG: a documented flag that silently does nothing is the same user-perceptible defect wdazvp was classified a bug for, on three more commands. An agent passing --limit to bound a check sweep receives the whole thing and cannot tell the flag was dropped. Per AGENTS.md a live bug gates the next release, hence Blocks-Release: next.

THE FIX NEEDS A PER-VERB DESIGN DECISION AND THAT IS WHY IT IS FILED RATHER THAN FOLDED INTO okiso1. 'aw find' has an obvious stream shape (one item per matched artifact), which is what okiso1 builds. 'aw check' and 'aw index' emit a SINGLE result record whose payload is a diagnostics array, so there is no settled answer to what an item would be: one finding, or one checked artifact? Bounding the diagnostics array inside a result record is a different mechanism from an item stream and would need the summary counts to live somewhere a result record has no field for. 'aw search' is closer to find (its payload is a hit list) but its row is 'path:line' rather than an artifact, so its item shape is its own question. Candidate directions: (a) give each a real item stream with the per-verb item shape decided explicitly; (b) refuse --limit at exit 2 on the verbs where it has no meaning, so it never silently lies; (c) bound the in-record payload and report the counts in the result record, which needs a schema decision. Related: wdazvp, plan okiso1, 9qya0k (the protocol doc undercount), kkjrqr (a projection dropping a summary's next).
