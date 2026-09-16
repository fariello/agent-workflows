- Id: cnf7gw
- Status: open
- Set: cnf7gw
- Priority: high
- Work-Kind: bug
- Summary: finalize's ff-only reconciliation refuses when a PEER holds an uncommitted edit to the plan being finalized, and the refusal is correct but has no tooled remedy

## Workflow history
- 2026-09-16 created (aw backlog): finalize's ff-only reconciliation refuses when a PEER holds an uncommitted edit to the plan being finalized, and the refusal is correct but has no tooled remedy

FOUND while executing plan u23gbn (dirtygates Order 04), which relocated the terminal transition's mutations into a coordinator-owned worktree and lands the commit with `git merge --ff-only`.

WHAT IS WRONG. That merge REFUSES (rc=1, "Your local changes to the following files would be overwritten by merge") when the shared checkout holds an uncommitted change to the plan file being moved. The refusal is CORRECT: it is protecting a co-worker's bytes, and u23gbn deliberately reports it rather than forcing it. But the operator is left with no TOOLED way forward. The message says "Land or set that edit aside and re-run", and the house rules correctly forbid an agent from committing or stashing another party's work, so an agent that hits this can only stop and escalate.

WHY IT IS NARROWER THAN IT SOUNDS, stated so nobody over-prioritizes it. u23gbn's own transaction releases the ONE case that is provably lossless (its own mirrored bytes, verified to be carried by the landed commit), which is the common case: an executing agent's uncommitted evidence edits to its own plan. The remaining case is a genuine THIRD PARTY editing the same plan file concurrently, which `_assert_rollup_touched_only_owned_paths` already refuses up front on the rollup path, so what is left is a race.

WHAT A FIX MIGHT LOOK LIKE (not decided here): a tooled verb that reports the objecting path plus the exact operation a human should run, or a retry that waits for the tree to settle, or landing the transition on a branch the operator merges themselves. Any of those is a design question, not a mechanical fix.

WHERE: `agent_workflows/ipd_lifecycle.land_worktree_commit` (the RECONCILED_REFUSED arm) and `_release_own_plan_edit_before_landing`.
Evidence: the contended-arm measurement in the u23gbn execution transcript, and `tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_refuses_and_the_peers_bytes_survive`.
