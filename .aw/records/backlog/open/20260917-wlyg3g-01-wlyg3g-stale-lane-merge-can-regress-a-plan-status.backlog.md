- Id: wlyg3g
- Status: open
- Set: wlyg3g
- Priority: medium
- Work-Kind: bug
- Summary: Merging a stale lane can resurrect a plan in pending/ at an earlier status while main holds it terminal, and no gate refuses the lifecycle regression

## Workflow history
- 2026-09-17 created (aw backlog): Merging a stale lane can resurrect a plan in pending/ at an earlier status while main holds it terminal, and no gate refuses the lifecycle regression

## Observed

Found 2026-09-17 while triaging `.aw/worktrees/` (17 worktrees, 1.8G). Lane `aw/lane/d7qoxv` held one
commit, `74b0ef17 chore(plans): set status approved`, whose entire content is a `- Status:` flip on
`.aw/records/plans/pending/20260913-dirtygates-01-d7qoxv-...ipd.md`.

In main that same plan is now:

```
.aw/records/plans/executed/20260913-dirtygates-01-d7qoxv-...ipd.md
- Status: executed
```

The lane's copy still reads `- Status: approved` at the `pending/` path. So merging that lane would ADD
a `pending/` copy at `approved` while the `executed/` copy remains, leaving the same plan in two
lifecycle directories at two different statuses, the older of which claims the work is not done.

`git merge-tree` reports the merge as clean, because the two paths are different files and git has no
concept of a lifecycle. Nothing refuses it.

## Why this is not merely hypothetical

Every lane that ran before its plan finalized holds a `pending/` copy of that plan. Of the 17 worktrees
triaged, `d7qoxv` was the one whose ONLY content was such a flip, but the same shape sits inside any
stale lane whose plan later reached a terminal state by another route. The triage decision "is this lane
safe to merge or should it be deleted" therefore requires reading each lane's plan status against
main's, by hand, per lane. That is exactly the judgement `ut0vzr` (the lane-triage plan) has to make 13
times, and getting it wrong in the merge direction silently un-finalizes a plan.

## What makes it worse

The regression would be recorded as a NORMAL commit by a legitimate verb. There is no fabricated
evidence and no hook violation: someone merges a preserved lane in good faith, believing they are
recovering work, and the lifecycle moves backwards. The plan's own `## Workflow history` would then
carry an `executed` entry ABOVE an `approved` status line, which is the self-contradiction a reader
would eventually trip over rather than a gate catching it.

## Measured today: nothing is currently broken

No plan currently exists in two lifecycle directories:

```
$ for f in .aw/records/plans/*/*.ipd.md; do basename "$f"; done | sort | uniq -d
(empty)
```

So this is LATENT, which is why it is `medium` and not `high`. `d7qoxv`'s worktree was removed rather
than merged (its branch is kept at `74b0ef17`), so the one live instance was resolved by deletion.

## Expected

Merging a lane must not be able to move a plan's lifecycle backwards. At minimum the condition should
be DETECTED and refused rather than committed silently.

## Fix sketch

1. Add an `aw check` rule for the structural symptom: the same plan id6 (or filename stem) present in
   more than one lifecycle directory. That is cheap, deterministic, and catches this however it arises,
   including by hand-merge. Note `aw check` already detects duplicate SET IDS but not duplicate
   ARTIFACT LOCATIONS; measured today, its 3 duplicate findings are all set-id collisions.
2. Add the same test to the driver's integration path, so a lane whose merge would introduce a second
   copy of a plan is refused as `integration-blocked` with the two paths named, rather than merged.
3. Give the lane-triage workflow a mechanical answer instead of a per-lane judgement: for each lane,
   compare the lane's plan status/location against main's and report REGRESSION / SAME / AHEAD. `ut0vzr`
   E-04 currently asks a human to decide this by reading; this would make it a computed verdict.
4. Regression test: a lane holding a `pending/` copy at `approved` for a plan main has in `executed/`
   must be refused, and the `aw check` rule must fail on a tree containing both copies.

## Related

* `ut0vzr` (lane-branch triage, `to-review`): the consumer of this. It must disposition 13 branches and
  this defect is one of the traps its E-04 has to avoid; item 3 above would make its job mechanical.
* `5bmq5f` (open): the BACKLOG analogue, an item duplicated across status directories. Same class of
  defect on a different artifact tree, and the three instances landed today (`yocdq4`, `egqt32`,
  `nuanaw`) show the shape is real and recurring. A fix for either should probably generalize.
* `a58s04`: why these stale lanes accumulate in the first place. Fixing that reduces the exposure here
  without closing it.
