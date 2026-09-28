- Id: hf76th
- Status: open
- Blocks-Release: next
- Set: hf76th
- Priority: medium
- Work-Kind: bug
- Summary: the transaction discards its lifecycle commit by deleting the coordinator branch on every failure arm, so the released evidence bytes survive only as a dangling object gc will prune and no tooled verb can name it

## Workflow history
- 2026-09-28 created (aw backlog): Filed while authoring cnf7gw's graduation plan; measured, see body.

MEASURED 2026-09-28 at HEAD 6171375d, in a scratch fixture driving a real `ipd_lifecycle.finalize(apply=True)` whose ff-only merge RACED.

WHAT IS WRONG. `commit_lock.coordinator_worktree`'s `finally` unconditionally runs `git worktree remove --force` and `git branch -D <branch>`, and its docstring justifies that as safe 'BECAUSE the caller has already landed (or deliberately abandoned) the commit'. On the FAILURE arms the caller has NOT landed it, so the commit becomes UNREACHABLE: no ref, no reflog entry (the branch's reflog dies with the branch), only a dangling object.

MEASURED after a raced finalize: the journal records `worktree_commit: 607622ef...`; `git cat-file -e` on it succeeds; `git merge-base --is-ancestor <it> HEAD` is NONZERO; `git branch -a` shows `* master` only; `git reflog --all` does not mention it; and `git fsck` reports `dangling commit 607622ef...`. So it is recoverable ONLY by `git fsck` archaeology until gc prunes it, and no `aw` verb names it.

WHY THAT MATTERS RATHER THAN BEING MERELY UNTIDY. `_release_own_plan_edit_before_landing` runs BEFORE the merge and deliberately drops the executing agent's uncommitted evidence edits from the working tree, on the proven premise that the landed commit carries them. When the merge then fails, that premise is true of a commit nobody can reach. Measured: an agent's own uncommitted `V-01` evidence text was absent from the working tree afterwards, present only in the dangling commit and in the journal's `original_bytes`. The journal is the honest recovery route today and it is undocumented as such.

WHAT A FIX MIGHT LOOK LIKE (not decided here): keep the branch on a failure arm under a recoverable name and report it; or write a tag/ref the operator can `git show`; or have the report name `worktree_commit` and the journal path explicitly. Any of those is a design question.

WHERE: `agent_workflows/commit_lock.coordinator_worktree` (the `finally`), consumed by `agent_workflows/ipd_lifecycle._finalize_transaction`.
Evidence: the fsck/ancestor/reflog measurements above.
