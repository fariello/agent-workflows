- Id: cl8thr
- Status: open
- Set: cl8thr
- Work-Kind: bug
- Priority: high
- Summary: Isolated runner preflight warns and launches even when main has uncommitted tracked changes overlapping queued plan files or their Scope-Paths, causing stale worktrees and predictable fail-merge
- Short-Description: Isolated runner preflight warns and launches even when main has uncommitted tracked changes overlapping queued plan files or their Scope-Paths, causing stale worktrees and predictable fail-merge
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-26 created (aw backlog): Isolated runner preflight warns and launches even when main has uncommitted tracked changes overlapping queued plan files or their Scope-Paths, causing stale worktrees and predictable fail-merge

Observed in pubrun run-20261126T014957Z-3020938: two plans (0cjiv5 and pqcx6o) had uncommitted Status: approved edits in main's working tree ~3.5 minutes before aw agy run doc-audit launched (while HEAD still had Status: reviewed). Because dirtygates (d7qoxv) sets CleanBaseResult.refuses=False for isolated worktrees (runner_shared.py::clean_base_launch_decision returns CLEAN_BASE_WARN), the runner proceeded without stopping or prompting. This caused two defects: (1) queue discovery read Status: approved from the dirty working tree while git worktree branched from HEAD (Status: reviewed), so both lanes executed and finalized without their Approval: field or approved history entry; and (2) all three lanes touching those dirty paths (0cjiv5, pqcx6o, and 77pdvl which added Carrier-Evidence to 0cjiv5) passed execution and verification only to hit fail-merge at integration ('main tree has un-owned dirty paths overlapping the incoming change'), stranding 3 verified lanes and fail-depending orchestrator 86cd17. Fix: in preflight (lane_containment.evaluate_clean_base / runner_shared.py::clean_base_launch_decision and both drivers), compute the intersection between main's dirty tracked paths and the queued items' own plan paths + declared Scope-Paths (and carrier targets where known). Keep CLEAN_BASE_WARN only for truly disjoint dirty paths; when dirty tracked paths overlap queued plans or their Scope-Paths (especially when a queued plan file itself is dirty/uncommitted), fail closed unless the user explicitly accepts the risk (prompt interactively on a TTY to commit/fix first or proceed with risk acknowledged; refuse non-interactively unless an explicit CLI flag such as --allow-dirty-base / --allow-overlapping-dirty-base is passed). Also prevent worktrees from branching from a HEAD whose plan Status disagrees with the working-tree Status that qualified the item for dispatch.
