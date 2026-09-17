- Id: wxf5iq
- Status: open
- Set: wxf5iq
- Priority: low
- Work-Kind: chore
- Summary: IPD lqly9m's OQ-01 says finalize routes through commit_isolated, but 82922f5c moved it to coordinator_worktree; the stale claim should not mislead a later reader

## Workflow history
- 2026-09-17 created (aw backlog): IPD lqly9m's OQ-01 says finalize routes through commit_isolated, but 82922f5c moved it to coordinator_worktree; the stale claim should not mislead a later reader

DISCOVERED while executing IPD `lqly9m`. This is a DOCUMENTATION/PROVENANCE defect in an approved plan's
resolved open question, not a code defect; nothing shipped is wrong because of it.

WHAT THE PLAN SAYS. `lqly9m` OQ-01 (marked `resolved`, non-blocking) states: "Finalize DOES route
through the shared helper: `ipd_lifecycle.py:2740` calls `_clock.commit_isolated(...)`, so it inherits
E-01/E-02/E-09", and its `Project conventions` section repeats "FINALIZE SHARES THIS EXACT CODE PATH".
The plan's F-16 builds on that premise, deriving the absent-path sentinel requirement from finalize
passing `[plan_rel, dest_rel]`.

WHAT IS TRUE AT HEAD `4b68a786`. `ipd_lifecycle` no longer calls `commit_isolated` AT ALL. Commit
`82922f5c` ("mutate and commit a terminal transition in a coordinator worktree, land it with a refusing
fast-forward") moved finalize onto `commit_lock.coordinator_worktree` instead, and the code now carries
an explicit comment explaining WHY NOT `commit_isolated` (its copy direction is shared -> worktree, so a
mutation performed in a different worktree is invisible to it, and it performs the ref advance itself
under a CAS, which must not precede the fast-forward). Verified: the only remaining `commit_isolated`
call site in the package is `git_commit_helper.py:604`.

WHY THIS DID NOT CHANGE THE IMPLEMENTATION. The absent-path sentinel E-01 requires is still CORRECT and
still REACHABLE: `offer_commit` really does pass a path that is gone from disk (a plain deletion is the
common case, verified: `offer_commit` on a deleted file reaches `commit_isolated` with the path absent),
and the retry's re-add had to handle a staged deletion too (a defect found and fixed during execution).
So the sentinel is load-bearing for `offer_commit`'s own callers rather than for finalize, and removing
it would still be wrong.

WHAT THE WORK IS. Nothing urgent. When someone next touches `lqly9m`'s lineage or writes a plan citing
finalize's commit path, correct the claim so a future author does not re-derive a requirement from a
path that no longer exists. Note this is precisely the failure mode `AGENTS.md` warns about (re-locate
by symbol rather than trusting a citation), and the plan itself already had to correct stale citations
twice (F-6, F-22).
