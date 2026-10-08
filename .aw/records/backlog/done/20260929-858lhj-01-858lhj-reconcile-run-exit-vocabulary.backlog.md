- Id: 858lhj
- Status: done
- Graduated-To: runexitvocab
- Set: 858lhj
- Priority: low
- Work-Kind: chore
- Summary: Reconcile the run-execution exit vocabulary with the CLI three-state exit classification

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD u28vqb executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-runexitvocab-01-u28vqb-scope-the-published-three-state-exit-claim-to-the-surface-it.ipd.md); evidence .aw/records/plans/executed/20260930-runexitvocab-01-u28vqb-scope-the-published-three-state-exit-claim-to-the-surface-it.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: u28vqb
- 2026-09-29 created (aw backlog): Reconcile the run-execution exit vocabulary with the CLI three-state exit classification

The CLI publishes a UNIFORM THREE-STATE exit classification (0 clean / 1 findings / 2 cannot-run) in docs/cli-output-contract.md Section 3, docs/cli-human-guide.md and README.md, and agent_schema.validate_agent_record enforces it for aw.agent/v1. EIGHT command_surface declarations legitimately contradict it, measured 2026-09-29: ipd execute-set (0,1,2,3), run start (0,2,3,5,6), runs next (0,3), run record (0,2,3,5,6), runs resume (0,3), run cancel (0,5,6), runs status (0,1,3,5), run finalize (0,1,4,6). These belong to the run-execution vocabulary where 3 means 'human input or explicit acknowledgement is required' (run_cli.EXIT_BLOCKED, run_evidence.AGGREGATE_NEEDS_INPUT, spec 25kzda's six-row table). run_evidence itself carries a comment recording that the two tables disagree at 3 and 4. SO THE WORD 'uniform' IS FALSE as published, and a consumer reading either document cannot tell which table governs a given verb. THE FIX IS A CONTRACT DECISION, NOT A TWEAK: either amend approved spec 25kzda's exit table, or renumber shipped aw runs codes that consumers read, or scope the three-state claim explicitly to the non-run surface. Each needs a survey of who reads these codes. RAISED BY plan rwvzqm (OQ-02), which fixed the one condition where the tables do not conflict (no-project on a read verb) and amended Section 3 to acknowledge the divergence rather than conceal it. That acknowledgement is a stopgap; this item is the real reconciliation.
