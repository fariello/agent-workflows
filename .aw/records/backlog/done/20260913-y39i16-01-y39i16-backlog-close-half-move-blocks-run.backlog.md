- Id: y39i16
- Status: done
- Set: y39i16
- Priority: high
- Work-Kind: bug
- Summary: a runner backlog close committed half the move: the done/ addition landed but the graduated/ deletion was left uncommitted, and the resulting dirty tracked path refused every remaining item in the run

## Workflow history
- 2026-09-13 done (aw set): Filed retroactively at the maintainer's direction: the defect was diagnosed and FIXED before this record existed. Fix shipped as c53849e5 (relocate with git mv; stop passing an already-renamed source to git add; split the two path sets in finalize). Verified end-to-end on the failing scenario, both halves of the move now in one commit and the tree left clean; suite 5997 passed bare with a FAILED-set diff identical to baseline. Cost before the fix: 68 items refused across three runs plus roughly 55 cascaded dependency-blocked.
- 2026-09-13 created (aw backlog): a runner backlog close committed half the move: the done/ addition landed but the graduated/ deletion was left uncommitted, and the resulting dirty tracked path refused every remaining item in the run

## Filed retroactively, and why that is stated up front

THIS ITEM IS A RECORD OF A DEFECT THAT WAS ALREADY FIXED BEFORE THE ITEM EXISTED. It is filed after the
fact at the maintainer's direction, so the backlog tree carries the diagnosis and its link to the four
runs it cost, rather than that reasoning living only in a commit message.

The sequence was: the defect was diagnosed during a live debugging session, a backlog item was drafted,
the maintainer directed that a fix was wanted rather than more paperwork, the draft was discarded, the code
was fixed and landed, and the record was then noticed to be missing. Nothing about the fix is in doubt;
only the written record was absent.

## Observed harm

Four consecutive IPD batch runs on 2026-09-13 failed, three of them to this cause:

| run | items refused | of |
|---|---:|---:|
| `run-20260913T031350Z-1732436` | 27 | 42 |
| `run-20260913T031148Z-1722898` | 23 | 41 |
| `run-20260913T031521Z-1774617` | 18 | 43 |

Every refusal carried the identical message, naming a single uncommitted backlog markdown file:

```
refusing to launch an unattended isolated turn: the target checkout has 1 dirty TRACKED path(s),
which a lane created from HEAD would silently omit: .aw/records/backlog/graduated/<item>.backlog.md
```

Roughly 55 further items then went `dependency-blocked` behind those refusals. Two of the runs spent
$51.00 and $55.09 respectively to complete two plans and one plan.

## The defect

`aw backlog set done` MOVES the item file from `graduated/` to `done/`. A move is two facts to git: a
deletion and an addition. The runner's close then had to find BOTH in `git status` and commit them
together, and when that pairing failed it committed only the addition.

Two real commits prove it, each holding the addition alone with no matching deletion:

```
$ git show --name-status --format="" 52837644
A       .aw/records/backlog/done/20260907-actmodel-01-0k74my-per-action-model-selection.backlog.md

$ git show --name-status --format="" 187f5c69
A       .aw/records/backlog/done/20260905-awinbox-01-lsztiu-aw-adopt-inbox-to-typed-tree.backlog.md
```

The unstaged deletion left behind then tripped the spec-`7ckptx` R5.4 clean-base guard, which correctly
refuses an unattended isolated turn against a dirty tree. So one item's own bookkeeping disabled the rest
of its run, and the guard was working as specified.

## Root cause, which was NOT where it first appeared to be

`commit_backlog_close` (`oc_runipd.py:1340-1422`) already anticipated a partial view and fails closed on
one (`if len(paths) < 2: return None`). That guard was not the problem, and neither was the porcelain
parsing: both were verified correct against a fixture reproducing the exact state.

The actual causes were two, and the second is the one that did the damage:

1. `status_set.apply_status_change` relocated by `atomic_write(dest)` then `unlink(src)`. Git sees two
   unrelated facts, which is why any caller had to pair them at all. `artifact_core.git_mv` already
   existed and six other modules already used it; the status setter was the lone exception, which is why
   the bug class reached only here.
2. `git_commit_helper.offer_commit` passed the already-renamed SOURCE path to `git add`, which fails with
   "pathspec did not match any files". GIT ADD STAGES NOTHING AT ALL WHEN IT FAILS, so the deletion never
   entered the index while the addition, staged in the same doomed invocation, still reached the commit by
   a different path. That is precisely how an addition-only commit arises.

## The fix that shipped

Commit `c53849e5`, "fix: relocate an artifact with git mv so a status change cannot half-commit", three
parts:

1. `status_set.apply_status_change` relocates with `_core.git_mv`, so the move is ONE staged rename with no
   halves to lose. Order matters and is commented: move first, then write the updated content at the
   destination.
2. `git_commit_helper.offer_commit` no longer passes an already-renamed source to `git add`. A new
   `_in_index` helper distinguishes "deleted but still in the index" (git add stages the deletion, keep the
   path) from "already renamed away" (drop it). NOTE FOR ANYONE REVISITING: do NOT use `_staged_paths` for
   this test. For a staged rename git reports only the DESTINATION there, so the source looks absent and a
   membership test wrongly keeps it, reproducing the bug with extra steps. That was measured while writing
   the fix.
3. `ipd_lifecycle` finalize splits the two path sets: `git add` receives only paths that still exist, while
   `commit_isolated` still receives the old location so it propagates the deletion into the commit.

## Evidence the fix works

End-to-end on the exact failing scenario, before and after:

```
before: offer_commit -> error; commit holds 'A done/...' alone; tree left dirty
after:  offer_commit -> committed; commit holds BOTH
          A .aw/records/backlog/done/a-0k74my.backlog.md
          D .aw/records/backlog/graduated/a-0k74my.backlog.md
        tree CLEAN, so no following item is refused
```

Suite at the fix commit: `5997 passed, 3 skipped, 2 xfailed` bare. Serial run `6 failed, 6461 passed`,
identical to main's baseline at the same commit (`comm` diff of the two FAILED sets was EMPTY), so no new
failure was introduced. An earlier attempt broke 53 tests by dropping the old path outright; the suite
caught it and the two-path-set split above is the correction.

## Honest limits of the fix

- It removes the CAUSE of the dirty path. It does NOT change the fact that one dirty tracked path still
  refuses every remaining item in a run. That amplification is a separate design defect, addressed by plan
  `d7qoxv` (Set `dirtygates`, Order 01), which turns the pre-launch refusal into a report.
- The runner still writes to the shared checkout mid-run for a successful item's backlog close. Plan
  `9iq461` (Order 03) moves that write into the lane so it rides the merge.
- The two commits above were repaired by hand (`959c98fc` and `acde2496` committed the straggling
  deletions). Those manual repairs are the thing the fix exists to make unnecessary.

## Related

- Fix commit `c53849e5`; manual repairs `959c98fc`, `acde2496`.
- Backlog `cjefq5`: a different whole-run blocker from the same session (an already-executed Set child
  queued with `file: null`, blocking its dependents).
- Set `dirtygates` (orchestrator `8lfoum`), which removes the guards that amplified this defect into an
  outage and the remaining mid-run writes to the shared checkout.
