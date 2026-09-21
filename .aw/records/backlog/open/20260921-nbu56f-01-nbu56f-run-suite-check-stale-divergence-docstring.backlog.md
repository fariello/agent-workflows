- Id: nbu56f
- Status: open
- Set: nbu56f
- Priority: low
- Work-Kind: chore
- Summary: run_suite_check's docstring still cites a stale 36-vs-15-failed worktree divergence measurement whose cause (dh0uno) is fixed and whose acceptance claim was retracted

## Workflow history
- 2026-09-21 created (aw backlog): run_suite_check's docstring still cites a stale 36-vs-15-failed worktree divergence measurement whose cause (dh0uno) is fixed and whose acceptance claim was retracted

MEASURED 2026-09-21 in lane 9lyg5h (integearn-05 E-01). `oc_runipd.run_suite_check`'s docstring justifies its PRIMARY-CHECKOUT insistence with: "MEASURED: tests/test_run_viewer.py gives `36 passed` in the primary checkout and `15 failed, 20 passed` in a lane", attributed to `.aw/state` resolving relative to cwd (backlog `dh0uno`).

THAT MEASUREMENT IS HISTORICAL. Re-measured in a real linked worktree (`git worktree add --detach`) of a fresh clone holding zero run directories, which is exactly the condition the cited defect describes:

    primary  tests/test_run_viewer.py -> 91 passed
    lane     tests/test_run_viewer.py -> 91 passed
    primary  bare suite -> 1 failed, 7830 passed, 3 skipped, 2 xfailed in 118.47s
    lane     bare suite -> 1 failed, 7830 passed, 3 skipped, 2 xfailed in 107.20s

Identical, including the single environmental failure (backlog `wx72g3`). Backlog `dh0uno` is `- Status: done` and its OWN history retracts the claim ("NOTE the old acceptance claim that ~15 test_run_viewer failures ARE this bug was false").

WHY THIS IS A CHORE AND NOT A BUG, stated so the classification can be disputed on its reasoning: no behavior is wrong. `run_suite_check` still runs in the primary checkout, which remains the right contract for an independent reason (a green PRIMARY tree is what integration endangers). Only the stated REASON is out of date, so nothing a user does produces a wrong or slow answer.

WHY IT IS STILL WORTH FILING: the number is actively misleading to the next implementer. Plan `9lyg5h` was largely DESIGNED around neutralizing that divergence and review had to re-measure it to discover it was gone, and the plan records that building a subtraction layer from those fifteen stale ids would have MASKED fifteen real failures rather than removed fifteen phantom ones. A docstring that invites that mistake costs a review round trip each time.

FIX SHAPE: replace the stale counts with the current measurement, keep the primary-checkout contract and re-justify it on the grounds that actually still hold. Deliberately NOT done in `9lyg5h`, whose 'Deferred / out of scope' section names correcting this docstring as 'a one-line courtesy at most, not a task here'.
