- Id: hf5cc4
- Status: done
- Blocks-Release: next
- Graduated-To: setrefuse
- Set: setrefuse
- Priority: medium
- Work-Kind: bug
- Summary: Clarify and style status refusal messages and orchestrator readiness gates

## Workflow history
- 2026-10-09 done (aw backlog): closed by aw agy run: IPD juu1rj executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261007-setrefuse-01-juu1rj-clarify-and-style-status-refusal-messages-and-orchestrator-r.ipd.md); evidence .aw/records/plans/executed/20261007-setrefuse-01-juu1rj-clarify-and-style-status-refusal-messages-and-orchestrator-r.ipd.md
- 2026-10-07 graduated (aw set): status set to graduated
- 2026-10-07 created (aw backlog): Clarify and style status refusal messages and orchestrator readiness gates

## Context

When running status transitions such as `aw set approved` on an orchestrator whose child fails readiness or lint, the setter outputs:
```text
Orchestrator itamry is not ready for review:
  - [child-lint-failing] 62pkkg: child 62pkkg fails author lint: IPD-Q501 OQ-06: BLOCKING question is still 'open'. Ask the human and record the answer (run `/askme`, then set 'Status: resolved' with a rationale). If it does not actually block, set 'Blocking: no'.
    Remedy: fix the child's named lint finding
```

This error output has several significant usability and ergonomic defects:
1. **Incorrect lifecycle action**: It declares "Orchestrator <id6> is not ready for review" even when the command was `aw set approved` or `aw set reviewed`. The orchestrator was already reviewed; it is not ready for approval.
2. **Missing causal parent-child narrative**: It fails to explain the hierarchical constraint: the parent is an orchestrator, its child has readiness 'no-go' or unready lint, and therefore the parent cannot transition to the target status.
3. **No visual hierarchy or styling**: There is no ANSI bold or color highlighting for id6s, setids, or status words across any error surface in `status_set.py` or `orchestrator_readiness.py`. Everything runs together into un-skimmable monochrome text.
4. **Dumping raw linter diagnostic codes**: For `child-lint-failing`, it dumps the internal diagnostic token (`IPD-Q501 OQ-06: ...`) rather than extracting and presenting the title or text of the blocking open question.
5. **Dense run-on paragraphs in other refusal surfaces**: Single-plan approval gate refusals, backward moves without `--message`, terminal reopenings, and priority backstops in `status_set.py` and `plan_readiness.py` are formatted as dense, unindented paragraphs that bury key information.

## Goal

1. Make `orchestrator_readiness.render_human()` status-aware by accepting the target status, rendering appropriate headers (e.g. "Refusing to set approved for orchestrator <id6> (set <setid>):"), and explaining the parent-child constraint clearly.
2. Extract and format the question text or summary for blocking open questions on child plans.
3. Add ANSI color and bold styling for id6s, setids, and lifecycle statuses across `orchestrator_readiness.py` and `status_set.py`.
4. Polish and bulletize refusal messages for single-plan approval gates, backward moves without `--message`, terminal reopenings, and priority backstops.
