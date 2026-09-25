- Id: iw3mvh
- Status: done
- Set: iw3mvh
- Priority: low
- Work-Kind: chore
- Summary: decide whether commit_isolated should merge instead of compare-and-swap the branch ref: a raced peer commit today leaves the work committed but NOT landed, though this has never fired in any recorded run

## Workflow history
- 2026-09-25 done (aw set): RETIRED at 8e74dcac (triage): decided keep compare-and-swap: 0 raced refusals in 265 runs; refusal fails closed and retry works; finalize no longer calls commit_isolated
- 2026-09-13 created (aw backlog): decide whether commit_isolated should merge instead of compare-and-swap the branch ref: a raced peer commit today leaves the work committed but NOT landed, though this has never fired in any recorded run

## What CAS means here, stated plainly because the name is jargon

COMPARE-AND-SWAP: "move this pointer from EXACTLY this old value to this new value, and if it is not at
the old value any more, refuse". The concrete call is
`git update-ref <ref> <new> <expected-old>` (`commit_lock.py:270`).

The alternative under discussion is a MERGE, which combines two histories rather than requiring one to be
exactly where you left it.

## How `commit_isolated` works today

Documented at `commit_lock.py:166-179`, and the reason it exists is measured: committing in the SHARED
tree lets `pre-commit` stash the whole working tree, run hooks, then restore the stash OVER whatever is on
disk, DESTROYING any peer write in that window. A writer lock cannot help, because the peer is not
committing, it is merely editing a file.

So the committer stops endangering writers:

1. Snapshot HEAD into a throwaway DETACHED worktree.
2. Copy in ONLY the requested paths (a peer's dirty file is never swept in).
3. Run the real `git commit`, hooks and all, THERE.
4. Advance the branch with a CAS ref update, which fails loudly rather than discarding a peer commit.

## The gap, demonstrated rather than argued

A ref move does not touch working files. Reproduced in a scratch repository 2026-09-13:

```
main working file BEFORE ref move:  v1
CAS ok
main working file AFTER ref move:   v1        <- unchanged
git status in main:                 M  f.txt
```

After the CAS, HEAD held the new content while the shared checkout's file still held the old, and
`git status` reported a MODIFICATION when the truth was that the working copy was merely STALE. Only
`git reset --hard HEAD` cleared it; `git restore --source=HEAD -- <path>` and `git checkout -- <path>` did
NOT.

Today this is harmless because the mutations happen IN MAIN, so the content is already on disk by the time
the ref moves, and the code only drops the stale index entry
(`_git(repo_root, ["reset", "--quiet", "HEAD", "--", *rel])`, `commit_lock.py:284`).

## The actual question

When a peer commit lands between the snapshot and the ref move, the CAS refuses and returns `ISO_RACED`
with the message "another commit landed on `<branch>` while this one was being prepared, so the branch was
NOT moved (the work is preserved as commit `<sha>`; cherry-pick or retry)" (`commit_lock.py:273-280`).

So the work is COMMITTED BUT NOT LANDED. It is safe (nothing is lost, the commit is reachable) but it does
not arrive, and a human or a retry must finish the job.

A MERGE would land it, because in the raced case the two commits touch disjoint paths by construction:
`commit_isolated` mirrors only the requested paths into the private worktree, so it cannot contain the
peer's file at all.

## Why this is LOW priority: it has never happened

Measured 2026-09-13 across every recorded run under `.aw/records/runs/`: `ISO_RACED` appears in ZERO run
event logs. Not rare, not occasional. Zero.

For contrast, the failures that actually cost items in the four runs of 2026-09-13, counted from each run's
`state.json`:

| count | cause |
|---:|---|
| 27 + 23 + 18 = 68 | `blocked`: "refusing to launch an unattended isolated turn" (the pre-launch whole-tree dirty gate) |
| roughly 55 | `dependency-blocked`, cascading behind those refusals |
| 2 | `merge-conflict` (lanes `bzz5e6`, `f6idxs`), each a LOCAL-CHANGES refusal misclassified as terminal |
| 0 | `ISO_RACED` |

So the maintainer's three weeks of frustration with large runs failing early is caused by the pre-launch
gate and by one misclassification, NOT by CAS. Those two are addressed by plans `d7qoxv` (Order 01) and
`metc8b` (Order 02) of Set `dirtygates`, both already revised and conforming.

CHANGING `commit_isolated` WOULD THEREFORE TOUCH THE COMMIT PATH EVERY FINALIZE USES IN ORDER TO FIX A CASE
THAT HAS OCCURRED ZERO TIMES. That is the same trade this item exists to make visible, so nobody
re-litigates it without evidence.

## Blast radius if someone does change it

Two callers, and they handle the outcomes differently, so both must be considered:

- `ipd_lifecycle.py:2752` (the finalize transaction). It EXPLICITLY handles `ISO_RACED` at `:2758-2762`,
  translating it into a nonzero rc plus a detail naming the preserved commit, and notes that "rolling back
  is correct and loses nothing". A merge would remove the case this branch exists for, so the branch and
  its comment would need rewriting rather than deleting.
- `git_commit_helper.py:595` (`offer_commit`, the shared path-scoped commit helper). It does NOT handle
  `ISO_RACED` distinctly: everything that is not `ISO_COMMITTED` or `ISO_NOTHING` collapses into a generic
  `git commit failed: <detail>` error outcome. So a raced commit currently surfaces here as a plain
  failure, which is honest but tells the operator less than the lifecycle path does.

## Where a merge DOES belong, and is already planned

Recorded so this item is not read as "merge is wrong":

- Plan `metc8b` (dirtygates Order 02) stops PREDICTING a lane merge-back with a dirty-overlap heuristic and
  attempts the real `git merge` instead, letting git's own refusal be the answer. That is the maintainer's
  idea, it is measured (`git merge-tree` was shown to report clean where the real merge refused), and it
  addresses the 2 measured `merge-conflict` items directly.
- Plan `u23gbn` (dirtygates Order 04) E-06 must reconcile the shared checkout with the new HEAD after the
  CAS, once the retirement's mutations move into a worktree. A `git merge --ff-only` is the honest
  operation there and is STRICTLY BETTER than the destructive `git reset --hard HEAD` the demonstration
  above needed, because ff-only REFUSES rather than clobbers, which is the property a shared checkout
  wants. If merge machinery is to be added anywhere new, that is the place.

## What would resolve this item

1. Instrument or search for a real `ISO_RACED` occurrence. Until one exists, the honest answer is "leave
   CAS alone".
2. If one occurs, decide between: (a) merge in `commit_isolated` so the raced case lands; (b) keep CAS and
   have the CALLER retry automatically, since the preserved commit is reachable and the retry is safe;
   (c) keep CAS and improve only the reporting in `offer_commit`, which today collapses raced into a
   generic failure.
3. Option (b) deserves first consideration: it needs no change to the commit mechanism at all, and the
   existing message already says "cherry-pick or retry", so the retry is the documented remedy.

## Honest limit of this record

The zero count is over RECORDED runs in this repository only. It says nothing about a busier shared
checkout, more parallel runs, or a CI environment with concurrent writers. The window is narrow (between a
HEAD snapshot and a ref update) but it is real, and a design that fails safe today could still be improved.
This item is LOW priority because nothing has been measured, not because the concern is imaginary.
