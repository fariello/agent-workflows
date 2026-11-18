- Id: 2a24ky
- Status: open
- Set: revsweep
- Work-Kind: bug
- Priority: high
- Summary: aw agy/oc run --action review with a Set selector refuses the whole run when the Set's orchestrator is already reviewed
- Short-Description: aw agy/oc run --action review with a Set selector refuses the whole run when the Set's orchestrator is already reviewed
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-18 created (aw backlog): aw agy/oc run --action review with a Set selector refuses the whole run when the Set's orchestrator is already reviewed

Observed 2026-11-17 in uni-ai-survey (agent-workflows 1.3.0rc2.dev12486+ge20b00a78): 'aw agy run --action review --model gemini-4-hydrogen-high findcore repolayout' refused: '--action review is illegal for 2 selected item(s): 5n6jm1 (status reviewed -> action orchestrate), ngnohz (status reviewed -> action orchestrate)'. No run started. The refusal is in runner_shared (the --action legality check near line 36145, which states 'An orchestrate item satisfies --action review NEVER'). Refusing to put a non-review turn into a review run is correct. The defect is that a SET selector implicitly pulls in the Order-0 orchestrator, so whenever an earlier sweep already reviewed the parent while children still await review (the normal state after a partial review sweep), a Set-level --action review is impossible; the operator must enumerate every child id6 by hand. Expected: for an IMPLICIT member of a Set selector, exclude an orchestrator whose next legal action is not review, report it as skipped with the reason, and review the rest; keep the hard refusal only when the operator named that orchestrator explicitly (id6 or path). Workarounds today: list the child id6s, or 'aw agy review' (sweeps only items awaiting review, across all Sets).

Additional context. The refusal came AFTER an interactive confirmation: the run first printed 'Re-review requested for 5 plan(s): ixowuu, i0yy2s, glwrr8, ixxin4, 31p43b (status reviewed) ... Type re-review to confirm', the operator typed 're-review', and only then did the legality check refuse the whole selection. The legality check should run before any confirmation prompt, so the operator is not asked to confirm a run that is already certain to be refused.
