- Id: ccu3k7
- Status: open
- Blocks-Release: next
- Set: ccu3k7
- Priority: high
- Work-Kind: bug
- Summary: Audit the 16 symbols lifted by 70a2059f for silent transcription drift: five defects shipped in execute_item_core's deliberate-stop handlers alone

## Workflow history
- 2026-09-23 created (aw backlog): Audit the 16 symbols lifted by 70a2059f for silent transcription drift: five defects shipped in execute_item_core's deliberate-stop handlers alone

## What

The `execute_item` deduplication commit `70a2059f` transcribed each host driver's working
`execute_item` into `runner_shared.execute_item_core`. That transcription silently introduced FIVE
defects into the three deliberate-stop handlers alone, all found while executing plan `13xo5k`:

1. `attempt["exit_code"] = stop.exit_code` in the level-4 spawn-path handler (`AttributeError`;
   `StopNowForce` has no such attribute).
2. The same line in the level-3 spawn-path handler (`AttributeError`; `StopAtCheckpoint` has only
   `observer`).
3. `_record_checkpoint_stop(...)` called without the required keyword-only `git_status_fn` in the
   level-3 SPAWN-PATH handler (`TypeError`).
4. The same missing argument in the level-3 VERIFY/RECONCILE handler (`TypeError`). This one is
   notable because plan `13xo5k` had asserted, from reading the code, that this handler was correct.
5. Both spawn-path handlers `return`ed where the originals `raise`d, and assigned
   `item["status"]` directly instead of routing it through `reconcile_disposition`. The `return`
   meant each host's `run_queue` never observed the stop and dequeued the NEXT IPD, so an operator's
   stop silently failed to stop the run.

All five are fixed by `13xo5k`. This item is about the REST of the commit.

## Why it is a bug and not a chore

Defect 5 is user-perceptible in the strongest sense: an operator who requested a stop got a run that
kept spending money on the next IPD, with a wrong exit code and a wrong summary line. Defects 1 to 4
crashed the runner where it was supposed to wind down cleanly.

## The transferable cause

None of the five is visible in a line-by-line diff review. Defects 3 and 4 have call text that is
BYTE-IDENTICAL to the pre-dedup original; what changed is which definition the bare name RESOLVES to.
In a host module `_record_checkpoint_stop` resolved to that host's wrapper, which binds its own
`git_status`; in `runner_shared` the same name resolves to the shared definition, whose `git_status_fn`
is keyword-only with no default. A move changed behavior while changing no characters.

## What to do

- Audit the remaining symbols `70a2059f` and the `li44r9` lift moved into `runner_shared`, looking
  specifically for (a) bare names that now resolve to a shared definition with a different signature,
  and (b) control-flow verbs (`return` vs `raise`) that differ from the pre-move original. Diff each
  lifted body against `70a2059f^` rather than reviewing the merge diff.
- `tests/test_hostdedup_identical_lift.py` and `tests/test_rununify_execute_item.py` assert that the
  lift HAPPENED (delegation, no re-fork). Neither asserts that a lifted body still BEHAVES as the
  original did. Consider a guard for that class: it is the gap all five defects fell through.

## Evidence

- `git blame -L` on the handler lines attributes every one to `70a2059f`.
- `git show 70a2059f^:agent_workflows/oc_runipd.py` (lines ~6653-6712 and ~7027-7048) holds the
  correct originals.
- Plan `13xo5k`'s execution report carries the measured tracebacks and the before/after test counts
  (19 previously failing end-to-end stop tests now pass).
