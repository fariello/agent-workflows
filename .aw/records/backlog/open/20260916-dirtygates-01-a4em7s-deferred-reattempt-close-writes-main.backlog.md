- Id: a4em7s
- Status: open
- Blocks-Release: next
- Set: dirtygates
- Priority: medium
- Work-Kind: bug
- Summary: A deferred integration re-attempt still closes its backlog item in the shared checkout

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): found while executing dirtygates-03 (9iq461)

dirtygates-03 moved the backlog close INTO the lane for the first-attempt success path, so a successful item no longer writes to the shared checkout mid-run. ONE PATH REMAINS, and it is recorded here rather than hidden in a comment.

WHERE: retry_deferred_integrations._finish in BOTH agent_workflows/oc_runipd.py and agent_workflows/agy_runipd.py. When an item was NOT eligible to close during its original turn (for example a sibling carrier had not executed yet) but IS eligible after a later deferred re-attempt merges, the close still runs against main. By that point the lane has been torn down by the same function, so there is no lane left to write in.

WHY IT WAS NOT FIXED IN 9iq461: with the lane gone, the only correct fix is a coordinator-owned throwaway worktree, which is exactly the mechanism dirtygates Order 04 (u23gbn) introduces for orchestrator retirement. Reusing it here belongs with that work, not in a plan scoped to the worker-side close.

HOW OFTEN: only for an item whose eligibility CHANGED between its own turn and a later re-attempt. The common case already skips this call (guarded on the close record), so an eligible item closed in its lane is untouched.

SUGGESTED FIX: once u23gbn has landed its coordinator worktree helper, perform this close inside one, so the write lands via a ref update like every other path.
