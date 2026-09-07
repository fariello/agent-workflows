- Id: yocdq4
- Status: graduated
- Blocks-Release: next
- Set: integdefer
- Priority: high
- Work-Kind: bug
- Summary: no way to re-integrate a verified lane without a full agent re-run, and resume re-dispatches finished work instead of merging it: add aw <host> integrate and call it from resume

## Workflow history
- 2026-09-07 graduated (aw set): Graduated to plan rl67b0 (integpath-04): add aw <host> integrate and make resume merge finished lanes instead of re-dispatching them. NOTE: this item's ordering note said txc9l1 blocks the work; txc9l1 has since executed and its concern is complementary (it acts at dispatch, this acts before dispatch).
- 2026-09-05 created (aw backlog): no way to re-integrate a verified lane without a full agent re-run, and resume re-dispatches finished work instead of merging it: add aw <host> integrate and call it from resume

TWO DEFECTS, ONE FIX.

DEFECT 1 - NO RE-INTEGRATE PATH EXISTS. When a lane finishes, verifies, finalizes, and then fails to
integrate, there is NO verb that retries just the merge. Confirmed 2026-09-05: no `integrate`
subcommand exists in `cli.py` or either runner. The only routes are a full agent re-run (paid,
slow) or a hand merge (outside the tooling, no record). For run
`run-20260905T050043Z-639569` this left four verified lanes stranded that ALL MERGE CLEAN against
main today (verified with `git merge-tree --write-tree main aw/lane/<id6>` for `76gsmv`,
`eyh1fu`, `txc9l1`, `uyeko5`). A 10-second fix required either hours of paid re-execution or
untooled manual git.

DEFECT 2 - RESUME RE-DISPATCHES FINISHED WORK, DESTROYING IT. This is the serious half.

A bare `resume` does nothing with these items: `integration-blocked` is in `TERMINAL_STATES`
(`oc_runipd.py:249`), so they are not `queued` and are never selected.

`resume --retry-incomplete` flips them to `queued` with `recovery_next=True`
(`oc_runipd.py:5745-5758`) and RE-DISPATCHES THEM AS FULL AGENT TURNS. There is no code path
anywhere that says "this lane is already verified, just retry the merge". That re-dispatch is
actively harmful:

  * The lane still exists and holds commits, so `allocate_worktree` classifies it HOLDS-WORK and
    attempt-scopes to `aw/lane/<id6>_attempt2` (`worktree_lease.py:518-524`), ORPHANING the
    finished lane. This is exactly the duplicate-work failure `k1nity` measured (byte-identical
    duplicate commits on 3+ resumed runs; on `ntf6sx`, 4 commits where 2 were expected and an empty
    `git diff`).
  * Worse, the plan file was already moved to `executed/` ON THE LANE but is still `pending/` on
    main, so the fresh turn begins against a plan main believes was never executed.
  * The recovery prompt does warn the agent (`runner_shared.py:493`), but `k1nity`'s measured
    finding is that informing is NECESSARY AND NOT SUFFICIENT.

Concretely: resuming this run with `--retry-incomplete` would spend four more agent turns to
reproduce work a `git merge` completes now.

THE FIX.

PART A - the explicit verb: `aw <host> integrate <id6>` (both hosts). Re-attempt integration for a
named verified lane, no agent turn. Worth having on its own merits: it works when there is no run to
resume, it is the natural recovery for a lane stranded by an OLDER run, and it gives resume one code
path to call rather than its own copy.

PART B - resume calls it, AUTOMATICALLY. On resume, an item in `integration-blocked` or
`merge-conflict` whose lane still exists and is verified must attempt INTEGRATION ONLY - no agent,
no tokens - BEFORE it is ever eligible for re-dispatch. This must NOT be behind a flag: the
alternative default (silent re-dispatch of finished work) is strictly worse. Empirically this alone
would have resolved all four items in the measured run.

Build A first, then have B call it.

MANDATORY CONDITION - RE-VERIFY, DO NOT TRUST. A lane verified against yesterday's main is not
verified against today's. Route every attempt through the existing
`orchestrate_isolation.execute_merge_and_revalidate_gate`, which already encodes "per-lane green
never implies integrated green". Do NOT shortcut to a bare `git merge` because `merge-tree` came
back clean: that proves absence of TEXTUAL conflict only, and says nothing about whether the suite
still passes. The `merge-tree` evidence cited above is offered as proof that the work is RECOVERABLE,
not as proof that it is SAFE to merge unverified.

ORDERING NOTE. `txc9l1` (approved, pending) is the closest existing artifact: it routes a resumed
turn whose lane already holds its work to a verify-and-continue turn instead of a fresh execution.
It is necessary but NOT sufficient for this item, because it operates once a turn is being
dispatched, whereas Part B must run BEFORE dispatch is even considered - the cheapest correct action
is a merge with no turn at all. Note the irony that `txc9l1` is itself one of the four stranded
items, so it cannot land until this is resolved by hand or by Part A.

STATE OF THE FOUR LANES as of 2026-09-05 (all intact, nothing lost): `76gsmv` 2 commits,
`eyh1fu` 2 commits, `txc9l1` 3 commits, `uyeko5` 3 commits; worktrees present under
`.aw/worktrees/<id6>`; each plan is `executed/` on its lane and `pending/` on main.
