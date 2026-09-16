- Id: h5a3ba
- Status: open
- Set: dirtygates
- Priority: low
- Work-Kind: followup
- Summary: IPD 9iq461 F-7 mis-diagnoses the earned-paths hazard: the cwd is fine, the COMMIT RANGE is empty

## Workflow history
- 2026-09-16 created (aw backlog): found while executing dirtygates-03 (9iq461)

Recorded so the same wrong diagnosis is not re-derived by a later plan reading 9iq461's findings table.

WHAT F-7 CLAIMS: that collect_earned_paths would fail or return nothing when run with cwd=main, because for an isolated turn both commits live on the LANE BRANCH. It offers two fixes: (a) compute earned_paths from the lane worktree, or (b) resolve the lane commits from main by SHA.

WHAT IS ACTUALLY TRUE, measured in a scratch repo during execution:
  * A linked worktree SHARES the object database and the ref namespace with its parent, so git diff <sha>..<sha> over lane commits resolves IDENTICALLY from either cwd (both printed the same path, rc=0). The cwd was never the problem, and fix (a) is a no-op.
  * THE REAL PROBLEM IS THE RANGE. collect_earned_paths diffs the attempt's starting_head..ending_head, and both of those are git_head(repo), i.e. MAIN's HEAD sampled before and after the turn. For an isolated turn main's HEAD does not move, so the range is X..X, which is EMPTY.

WHY IT MATTERED ANYWAY: F-7's CONCLUSION was right even though its mechanism was wrong. An empty earned set makes the gate refuse every close, silently, because the earned gate can only ever WITHHOLD one. So the hazard was real and 9iq461 fixed it, by naming the range that actually holds the work (the lane's base_commit..branch, via the new runner_shared.collect_lane_earned_paths).

NO CODE ACTION IS REQUIRED: the fix is in and tested (tests/test_runner_backlog_close_in_lane.py::TheEarnedPathsRangeIsTheLaneBranch pins both halves, including that the attempt's own range is empty). This item exists only so the stale finding in the executed plan does not mislead a future reader, and can be closed by anyone who confirms the note is unnecessary.
