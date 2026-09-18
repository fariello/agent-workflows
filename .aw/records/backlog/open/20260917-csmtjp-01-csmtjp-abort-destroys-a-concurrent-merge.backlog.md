- Id: csmtjp
- Status: open
- Set: csmtjp
- Priority: high
- Work-Kind: bug
- Summary: A driver's merge-conflict path runs git merge --abort on the shared checkout, which destroys an unrelated in-progress merge it did not start

## Workflow history
- 2026-09-17 created (aw backlog): A driver's merge-conflict path runs git merge --abort on the shared checkout, which destroys an unrelated in-progress merge it did not start

## Observed

2026-09-18T02:01:48Z, run `run-20260917T231229Z-2701568`, review item `i4ak5n`. A human-driven
`git merge --no-ff --no-commit aw/lane/upgtest` was staged in the main checkout (14 files, zero
conflicts) and awaiting validation before commit. The concurrently running review sweep attempted its
own merge-back, which git refused:

```
review-lane-not-integrated  i4ak5n  merge-back conflict; fatal: You have not concluded your merge
(MERGE_HEAD exists). Please, commit your changes before you merge.
```

The driver then classified that refusal as a content conflict and aborted, and the reflog records the
consequence:

```
36129255 HEAD@{2026-09-17 22:01:48 -0400}: reset: moving to HEAD
```

The 14 staged files were gone. Nothing was corrupted and no commit was lost, but the merge had to be
redone; it was noticed only because the staged count went from 14 to 0.

## CORRECTION 2026-09-17: the trigger described above is HUMAN-ONLY, and the summary overstated it

Asked "what merge needs to be staged?", I checked, and the honest answer narrows this item sharply.

THE DRIVER NEVER STAGES A MERGE. `integrate_lane_branch` runs `git merge --ff-only` then
`git merge --no-ff --no-edit -m ...` (`runner_shared.py:2270-2284`). Both AUTO-COMMIT. `--no-commit`
appears nowhere in any merge in the package (the only two hits, `agy_runipd.py:948` and `:976`, are
`aw set ... --no-commit`, unrelated to merging). So a driver cannot leave a `MERGE_HEAD` lying around
between calls the way I did: its merge either completes or is aborted within one call.

WHAT THAT MEANS FOR THIS ITEM. The measured incident required a HUMAN (me) running
`git merge --no-commit` by hand in the shared checkout and leaving it staged across a long validation
run. That is a self-inflicted condition and the cheapest fix is "do not do that", which is already the
honest-limit note at the bottom.

WHAT SURVIVES, and why the item is still worth keeping open:

* THE ASSUMPTION IN THE CODE IS STILL WRONG. `merge_in_progress` is used as "did MY merge start" when it
  actually answers "is ANY merge in progress". That is a latent correctness bug regardless of who
  creates the foreign state.
* TWO DRIVERS ARE NOT SERIALIZED AGAINST EACH OTHER. `run_lock` takes `run_dir / "driver.lock"`
  (`oc_runipd.py:2679`), i.e. a PER-RUN lock, not a per-repository one. Measured tonight: four
  concurrent `opencode run` processes on this one checkout. Two drivers can therefore both reach
  `integrate_lane_branch` on the same tree. Their merges auto-commit, so the window is much narrower
  than a human's staged merge, but a conflicted merge from driver A leaves `MERGE_HEAD` set for the
  duration of A's own abort, and driver B entering that window would abort A's merge instead of its
  own.
* THE HUMAN CASE WILL RECUR. The repository's own contract tells agents to expect concurrent humans and
  agents in one checkout; a tool that responds to a foreign merge by destroying it is the wrong default
  whoever created it.

SO THE PRIORITY IS ARGUABLY MEDIUM, NOT HIGH, and the summary should say "can destroy" rather than
implying a routine driver-vs-driver collision. Left at high pending a maintainer read, because the
destructive-action-on-unowned-state property is what makes it unpleasant rather than the frequency. The
verification below stands as measured; only the FREQUENCY claim was wrong.

## Root cause

`runner_shared.integrate_lane_branch` discriminates the two ways a merge can fail by testing for
`MERGE_HEAD` (`merge_in_progress`, `runner_shared.py:497`), then:

```python
if merge_in_progress(repo):
    conflicted = conflicted_paths(repo)
    _run_git(repo, ["merge", "--abort"])
    return (False, ..., "merge-conflict")
```

The structural test is CORRECT for the case it was designed for and its docstring documents the
measurement behind it (a content conflict leaves `MERGE_HEAD`; a local-changes refusal does not). The
defect is an unstated assumption: that any `MERGE_HEAD` present belongs to the merge THIS CALL just
attempted. Here git refused to start the driver's merge precisely BECAUSE a foreign `MERGE_HEAD`
already existed, so the predicate read someone else's merge state and the abort discarded someone
else's work.

Note the irony: the refusal text git emitted ("You have not concluded your merge") is explicit that
the pre-existing merge is a THIRD PARTY's, and the code reaches for the structural test specifically to
avoid parsing git's localizable English, so the one signal that would have disambiguated was
deliberately not read.

## Why high

1. It is a DESTRUCTIVE action on state the caller does not own, which the repository's own contract
   forbids agents from doing by hand ("never revert, stage, commit, discard, or clean up another
   party's work"). The runner should hold itself to the rule it imposes.
2. It is silent. `--abort` succeeds, the item is recorded `merge-conflict` with a plausible reason, and
   nothing anywhere says "I discarded an unrelated merge".
3. It is reachable by concurrent use of the checkout, which this repository actively encourages.
   Measured: four `opencode run` processes plus a human were live when it fired. SEE THE CORRECTION
   ABOVE for how narrow the driver-vs-driver window actually is: drivers auto-commit their merges, so
   the realistic trigger is a human's staged merge, and the driver-vs-driver case needs driver B to
   enter the window while driver A is between a conflicted merge and its own abort.

## Expected

A driver must not abort a merge it did not start. When `MERGE_HEAD` exists BEFORE the driver's own
merge attempt, the correct outcome is `integration-blocked` (leave everything alone, preserve the lane,
report that the checkout is mid-merge and by whom if determinable), not `merge-conflict` plus an abort.

## Fix sketch

1. Capture `merge_in_progress(repo)` BEFORE attempting the merge. If it is already true, refuse
   immediately as `integration-blocked` and do NOT attempt a merge or an abort; the checkout is busy.
2. Only abort when the pre-attempt check was False and the post-attempt check is True, i.e. when the
   merge this call started is the one in progress. That single ordering change closes the hole.
3. Keep the existing structural discriminator otherwise; it is right and its docstring's measurements
   still hold. This is a NARROWING, not a replacement.
4. Report the refusal distinctly enough that an operator can tell "the tree was already mid-merge" from
   "my lane conflicts with main". They need opposite responses.
5. Regression test: with a foreign `MERGE_HEAD` staged in a scratch repo, assert
   `integrate_lane_branch` returns `integration-blocked`, performs NO abort, and leaves the staged
   index byte-identical. Assert the genuine-conflict case still aborts exactly as today.
6. Check the agy host for the same shape: both hosts call the shared function, so one fix should cover
   both, but `agy_runipd.py:4231` emits the same event name and should be confirmed.

## Related, and how this differs

* `h1ksy6` (graduated): the pre-merge dirty check scopes to the lane's changed files, so a non-ff merge
  touching OTHER paths misreports. Adjacent, and both concern misclassifying an integration refusal,
  but that item is about which PATHS are examined; this one is about aborting a merge the driver does
  not own. Neither fix implies the other.
* `rnl3b7`: the executed-transition pre-commit gate has no merge-aware path. Same theme (tooling that
  does not expect a merge in progress), different surface.
* The `a58s04` lane-reclaim defect is unrelated; this one destroys index state rather than leaking disk.

## Honest limit

A human staging a merge in a checkout that live drivers are using is asking for interference, and the
cheapest mitigation is not to do that. This item is filed anyway because the runner's response to
finding a foreign merge should be to refuse, not to destroy, and because the same abort will fire on
one DRIVER's merge state as readily as on a human's once two drivers overlap.
