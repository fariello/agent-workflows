- Id: 0ndipg
- Status: done
- Graduated-To: isoraced
- Blocks-Release: next
- Set: 0ndipg
- Priority: low
- Work-Kind: bug
- Summary: commit_isolated leaves its commit dangling when the compare-and-swap loses the race, recoverable only by git fsck until gc prunes it

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD a1ygjp executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-isoraced-01-a1ygjp-stop-the-isolated-commit-s-compare-and-swap-exhaustion-from.ipd.md); evidence .aw/records/plans/executed/20260930-isoraced-01-a1ygjp-stop-the-isolated-commit-s-compare-and-swap-exhaustion-from.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: a1ygjp
- 2026-09-29 created (aw backlog): commit_isolated leaves its commit dangling when the compare-and-swap loses the race, recoverable only by git fsck until gc prunes it

MEASURED 2026-09-29 at HEAD `74b9c5c2`, by inducing the compare-and-swap race against the real
`commit_lock.commit_isolated` in a scratch git fixture (patching `commit_lock._git` to land a peer
commit immediately before the `update-ref`).

WHAT IS WRONG. `commit_isolated` commits inside a throwaway DETACHED worktree and then advances the
branch with a compare-and-swap `git update-ref <ref> <new> <expected-old>`. When the CAS fails
(`ISO_RACED`), the `finally` removes the worktree and the commit is left reachable from NOTHING:
measured `git fsck` -> `dangling commit 4e2ed93ac895...`, `git merge-base --is-ancestor <sha> HEAD`
rc 1, and `git reflog --all` does not mention it. `git gc --prune=now` then collects it.

WHY THIS IS NARROWER THAN ITS SIBLING `hf76th`, and the difference is what makes it its own item
rather than part of that plan. TWO mitigations exist here that do not exist for
`coordinator_worktree`. FIRST, the sha is RETURNED to the caller in `IsolatedCommitResult.commit`,
so a caller can always name it to an operator, whereas `coordinator_worktree` yields nothing and
its caller learns the sha only from the journal. SECOND, `git_commit_helper` RETRIES the CAS up to
`ISO_RACED_MAX_ATTEMPTS = 5` times, so the ordinary outcome is that the work lands rather than
being stranded. So the exposure is the retry-exhausted case, not every race.

WHAT IS NOT MEASURED AND MUST BE BEFORE FIXING: whether retry exhaustion actually happens in
practice, and whether the bytes it would strand are irreplaceable (as they provably are in
`hf76th`'s case, where `_release_own_plan_edit_before_landing` has already dropped the agent's
evidence from the working tree) or merely re-committable (the caller's own paths are still on disk
in the shared tree, since `commit_isolated` COPIES them in rather than moving them, which suggests
re-running simply works). If they are re-committable, the honest resolution may be to close this as
not-a-defect rather than to retain a ref. DO NOT assume the `hf76th` remedy transfers.

WHERE: `agent_workflows/commit_lock.commit_isolated` (the CAS arm and the `finally`), with the
retry at `agent_workflows/git_commit_helper.py` (`ISO_RACED_MAX_ATTEMPTS`).

FILED FROM: plan `c8ioct`'s `## Deferred / out of scope`, which excluded it deliberately because
`commit_isolated` backs `git_commit_helper.offer_commit`, the shared self-commit path behind every
`aw` verb, and folding it in would widen that plan's blast radius for a defect with different
mechanics.
