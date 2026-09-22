- Id: ldy1al
- Status: open
- Blocks-Release: next
- Set: ldy1al
- Priority: medium
- Work-Kind: bug
- Summary: aw commit <plan> is unusable for the rest of an execution once one out-of-scope path is legitimately committed

## Workflow history
- 2026-09-22 created (aw backlog): aw commit <plan> is unusable for the rest of an execution once one out-of-scope path is legitimately committed

FOUND while executing plan i4ak5n (revladder-01).

WHAT IS WRONG. `aw commit <plan>` runs `check.scope-drift`, which compares EVERY path changed since the begin receipt's frozen `base_head` against the plan's declared Scope-Paths. So the moment an execution legitimately touches one out-of-scope path, `aw commit <plan>` refuses for the WHOLE REMAINDER of that execution, including for commits containing only in-scope paths. The out-of-scope path cannot be 'gotten past' by committing it separately either, because the check reads the execution DIFF and not the staged set.

WHY THAT IS A DEFECT AND NOT THE GATE WORKING. The repository DESIGNS FOR this case: `aw ipd finalize --scope-reason PATH=WHY` exists precisely to justify an out-of-scope path per path, and AGENTS.md states the rule as 'an out-of-scope edit must be made only if genuinely required and then JUSTIFIED to aw ipd finalize with a --scope-reason per path'. But the commit gate refuses BEFORE finalize can ever be reached, so the sanctioned route is unreachable from inside the tooled commit path. The agent is pushed onto `aw commit --no-plan`, which SKIPS Scope-Paths enforcement and plan validation for every subsequent commit of that execution - strictly less protection than if the out-of-scope path had never been needed.

MEASURED. Plan i4ak5n declared four paths; E-08 required `agent_workflows/render_stream.py` (the only run-summary renderer, so the requirement was unmeetable from a declared path). After committing that file with `--no-plan`, `aw commit i4ak5n -- <four in-scope paths>` still refused with `check.scope-drift: changed path 'agent_workflows/render_stream.py' is outside the plan's declared Scope-Paths`, with an empty staged set.

POSSIBLE SHAPES (not a decision): let `aw commit` accept the same `--scope-reason PATH=WHY` finalize takes and record it for finalize to consume; or have the gate compare the STAGED set rather than the whole execution diff, leaving the execution-wide reconciliation to finalize where it already lives; or let it read an already-recorded justification. Each needs a decision about where the justification is durably stored.
