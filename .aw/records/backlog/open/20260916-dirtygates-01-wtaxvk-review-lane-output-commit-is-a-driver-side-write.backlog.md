- Id: wtaxvk
- Status: open
- Set: dirtygates
- Priority: medium
- Work-Kind: followup
- Summary: A review that leaves its output uncommitted needs the driver to commit it, and that step is invisible in the plan record

## Workflow history
- 2026-09-16 created (aw backlog): A review that leaves its output uncommitted needs the driver to commit it, and that step is invisible in the plan record

Found while executing plan ajxr5d (dirtygates Order 05).

WHAT WAS ADDED AND WHY IT HAD TO BE: runner_shared.commit_review_lane_output. integrate_lane_branch merges the BRANCH (git diff base..branch), so UNCOMMITTED files in a lane are invisible to it, and the lane is torn down afterwards. Before isolation, a review that edited the plan but did not commit left those files in MAIN's working tree, where the operator saw them and could commit them. Isolating a review WITHOUT this step would therefore have SILENTLY DESTROYED the output of any review that did not commit for itself, which is strictly worse than the dirty tree the plan set out to remove.

WHY THIS IS WORTH A DURABLE CARRIER RATHER THAN JUST A COMMENT: the plan ajxr5d never mentions this step, so it is a genuinely new driver-side WRITE that no reviewed design authorized. It is conservative (path-scoped to exactly what git status reports inside the lane, never add -A; hooks run normally with no --no-verify; a hook rejection is treated as 'nothing committed' so the work stays in the lane and the integration is a reported no-op). But it means the DRIVER now authors a commit whose content it did not produce, attributed with subject 'review(<host>): record the review of <id6>'.

THE CONCERN TO ADJUDICATE: whether the driver should commit an agent's uncommitted work at all, or whether a review turn should instead be REQUIRED to commit for itself and a non-committing review reported as a failed turn. The second is arguably more honest (the agent's work is the agent's to attest) at the cost of losing work that today survives. This deserves a maintainer decision rather than a default chosen inside an execution turn.

CONCRETE POINTER: agent_workflows/runner_shared.py, commit_review_lane_output, and its two call sites at the head of each host's 'if is_review and wt_handle is not None:' branch.
