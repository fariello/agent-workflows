- Id: yxfw4k
- Status: open
- Blocks-Release: next
- Set: reaskscore
- Priority: high
- Work-Kind: bug
- Summary: A defect re-ask that completes the work is never rescored, so a successful turn is recorded partial and cascades dependency-blocked to its whole Set

## Workflow history
- 2026-09-19 created (aw backlog): Measured twice on 2026-09-18 (zqs0px, zz5yxq): the re-ask completed and committed the work, recollect wrote the executed outcome to the path reconcile_disposition reads, and nothing rescored it; both runs went BLOCKED with 3 siblings dependency-blocked each

MEASURED TWICE on 2026-09-18, on the antigravity host only, in two consecutive runs. In both, the
item's work was COMPLETED, COMMITTED, and its outcome file says `executed`, and in both the driver
recorded `partial` and cascaded `dependency-blocked` across the rest of the Set.

    run-20260918T193638Z-2963696   02 zqs0px nobugship execute partial 56s
      03 qmgn12 orchestrate dependency-blocked    04 di08i9 execute dependency-blocked
      05 rgaasb execute dependency-blocked                     -> run outcome BLOCKED, 0 of 4 executed

    run-20260918T190723Z-2697256   02 zz5yxq runnoop  execute partial 39s
      02 7ewc74 orchestrate dependency-blocked    03 m85gxh execute dependency-blocked
      04 bsc457 execute dependency-blocked                     -> run outcome BLOCKED, 0 of 4 executed

The work is NOT lost, which is why this is a scoring defect and not a data-loss defect. Both lanes
hold a real commit (`aw/lane/zqs0px_attempt3` -> `08416ebd`, `aw/lane/zz5yxq` -> `8247a13c`) and both
were preserved with reason "the item finished 'partial' rather than executed". The cost is a wasted
human recovery, a stranded lane, and three blocked siblings per occurrence.

## The defect, precisely

`runner_shared.execute_item_core` scores the turn ONCE, at `runner_shared.py:13107`:

    disposition, outcome = reconcile_disposition(repo, item, run_dir, exit_code, plan_repo=...)

At that moment there is no outcome file (the first turn wrote none), so `reconcile_disposition`
correctly returns its empty-outcome fallback, `("partial" if exit_code == 0 else "failed-safely")`
(`oc_runipd.py:6135`, twin `agy_runipd.py:2988`, shared `runner_shared.py:12397`).

The defect re-ask block then runs at `runner_shared.py:13220`. It resumes the SAME session, the
resumed turn does the whole job, and `perform_defect_reask`'s injected `recollect` RE-COLLECTS the
lane submissions (`runner_shared.py:8943-8947` calling `lane_containment.collect_lane_submissions`),
writing the agent's now-complete outcome to `<run_dir>/outcomes/<NN>-<id6>.json`. That is the EXACT
path `reconcile_disposition` reads, as `lane_containment.py:607` says in as many words: "The outcome
JSON: the submission `reconcile_disposition` actually reads".

NOTHING RESCORES IT. The re-ask block re-reads that file for the defect report ALONE
(`runner_shared.py:8949`, `read_defect_report_outcome`), and mutates only
`attempt["defect_reask_prompt"]`, `attempt["defect_reasked"]`, `attempt["defect_reask_exit_code"]`,
`attempt["defect_report"]` and `item["defect_report"]`. The four carriers that decide the item's fate
keep their pre-re-ask values: the local `disposition`, `attempt["disposition"]`, `item["status"]`, and
`item["last_outcome"]`.

Everything downstream then reads that stale local: `integration_gate_relevant`
(`runner_shared.py:13337`, gated on `disposition in ("executed","substantially-complete")`), so no
verifier turn runs, no suite check runs, `integration_is_earned` is never consulted, the lane is never
integrated, `driver_finalize` is never called, and the item lands `partial`.

Had it been rescored, `reconcile_disposition` would have returned `substantially-complete` (the
deliberate downgrade of an agent's self-claimed `executed`, `oc_runipd.py:6114-6117`), which IS inside
that gate and inside `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:492`), so the siblings would not have
been blocked.

EVIDENCE the recollection really happened and really carried the right answer, from
`run-20260918T193638Z-2963696`:

  * `collections/02-zqs0px-attempt-1.json`: `"collection_runs": 2`, `"status": "complete"`,
    `"collected": ["outcome","report","decisions"]`, `"failed": []`;
  * `outcomes/02-zqs0px.json`: `"disposition": "executed"`, 4 files changed, commit `08416ebd`;
  * `state.json` queue entry: `"status": "partial"`, `"verification_status": null`,
    `"last_outcome": null`.

`last_outcome: null` beside a fully collected outcome file is the defect in one line.

## Why it is invisible on the opencode host

It is NOT an agy-only bug; it is an agy-only TRIGGER. The bug needs a first turn that writes no
outcome but whose re-ask then completes the work. On oc the first turn completes, so the re-ask (when
it fires at all) is report-only and rescoring it would change nothing. Any future oc turn that ends
without an outcome and is rescued by its re-ask hits the identical code path.

## Why the agy trigger is the host's doing, not the agent's

Worth recording because the obvious reading (and `q1z9gn`'s premise) is that the agent chose to
background its suite, and the logs say otherwise. The agent issued a plain FOREGROUND command:

    step 6: run_command {"CommandLine":"python3 -m pytest"}

with no background flag available or used. The HOST converted it into `task-6` and then ended the turn
under the agent:

    root agent idle; waiting up to 5s for 2 background task(s)
    terminating 2 background task(s) on exit
    {"event":"result","status":"SUCCESS","duration_seconds":47.46,"num_turns":1}

So the FOREGROUND instruction added by `q1z9gn` was ALREADY IN THIS PROMPT and was obeyed; it cannot
fix this, because the agent is not the one backgrounding the command. Measured across the captured agy
sessions, the host emits two different lines for the same situation: 3 sessions say `waiting for N
background task(s) (bounded by --print-timeout)` and WAIT, while 8 say `waiting up to 5s` and CUT. The
5s variant is what truncates these turns. No driver bound fired and none could have: `--print-timeout`
was `240m`, the driver bound was 14100s, the stall budget was 600s, and the turn lasted 47s with
`exit_code 0` and no `turn_bound_expiry`, no `interrupt_reason`, no `turn-bound-expired` event.

## Two independent fixes, both needed

**A. RESCORE AFTER THE RE-ASK (this item's core).** After a re-ask whose `recollect` succeeded,
recompute the disposition from the re-collected outcome before `integration_gate_relevant` is
computed. `reconcile_disposition` is a PURE function (no writes in any of the three copies), and the
body already calls it twice on the stop paths (`runner_shared.py:13194`, `:13206`), so a second call
is an established shape rather than a novelty. Three caveats an implementer must handle: it reads
`item["status"]`, which the body already overwrote, so the `integration-deferred` passthrough must not
be corrupted; the original executor `exit_code` must be passed, never the re-ask's; and a rescore must
only ever be able to IMPROVE the disposition, so a re-ask cannot downgrade a turn that already
succeeded.

**B. DO NOT PRESENT A HOST-TRUNCATED TURN AS A CLEAN EXIT.** The driver sees the host's own
`waiting up to 5s` / `terminating N background task(s) on exit` lines on the stream it already reads
line by line (`agy_runipd.py:2762-2769`), and currently ignores them, accepting `exit_code 0` as a
normal completion. A turn whose own host says it killed the work should be recorded as truncated, not
clean, so it is retryable rather than terminal.

## Relationship to the existing items

`q1z9gn` (done) fixed the agent-side half on the belief the agent chose to background; that belief is
now measurably wrong for these two runs, and its own fix sketch item 3 (treat a zero-work turn as
retryable) is still open as `x7wfyx`. This item is NOT a duplicate of `x7wfyx`: that one is about
RETRYING a turn that did nothing, while this one is about a turn that DID EVERYTHING and was scored as
though it had not. They compose: fixing only `x7wfyx` would retry a turn whose work was already
complete and committed.
