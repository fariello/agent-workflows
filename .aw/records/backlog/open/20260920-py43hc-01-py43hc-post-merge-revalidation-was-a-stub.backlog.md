- Id: py43hc
- Status: open
- Blocks-Release: next
- Set: py43hc
- Priority: high
- Work-Kind: bug
- Summary: The integration gate's post-merge revalidation never ran a suite: full_validation_runner was a constant return True on both hosts, so 'per-lane green never implies integrated green' was asserted and never enforced

## Workflow history
- 2026-09-20 created (aw backlog): Found and FIXED while executing daexj1 (E-03). Recorded for the record because the gate shipped inert for its whole life: execute_merge_and_revalidate_gate calls full_validation_runner at orchestrate_isolation.py:1160, and make_integration_validation_runner's entire body was 'return True', so a single-lane gate passed unconditionally. Combined with the pre-merge suite running in the PRIMARY checkout while isolate_worktree defaults TRUE, no suite ever measured a tree containing the lane's commits. Fixed by building the merge result with git merge-tree --write-tree and running the bare suite in it; proven on a per-lane-green/combined-red fixture. This item can be closed as done citing daexj1.
