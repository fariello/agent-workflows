- Id: q1z9gn
- Status: done
- Set: q1z9gn
- Priority: high
- Work-Kind: bug
- Summary: An execute turn backgrounded the validation suite and was killed still waiting, so it did no work, reported SUCCESS to the host, and blocked three siblings

## Workflow history
- 2026-09-18 done (aw set): Fixed the agent-side cause in the SHARED execute prompt (runner_shared.build_prompt, one definition for both hosts): the agent is now told to run any command it needs the result of in the FOREGROUND, that its turn's processes are terminated when the turn ends, and never to end a turn while waiting on a command it started. Regression-tested in tests/test_turn_bounds.py: removing the instruction fails 3 tests, restoring it passes. Suite 8114 passed, 3 skipped, 2 xfailed. Fix sketch items 2 and 3 (state the remaining turn budget; treat a zero-work turn as retryable) are NOT done and are left for a separate decision, recorded below
- 2026-09-18 created (aw backlog): zqs0px ran python3 -m pytest as a background task and polled it with schedule; the turn ended at 36s, the task was terminated, no outcome was written, and the partial blocked qmgn12/di08i9/rgaasb

MEASURED 2026-09-18 in run `run-20260918T045802Z-2547360` (antigravity host), item `02/5 zqs0px`
(`nobugship-01`). The item finished `partial` after **36 seconds** having performed NO work, and took
three siblings down with it:

    02 zqs0px nobugship execute     partial              36s
    03 qmgn12 nobugship orchestrate dependency-blocked    -
    04 di08i9 nobugship execute     dependency-blocked    -
    05 rgaasb nobugship execute     dependency-blocked    -

Run outcome: `BLOCKED`. One of five items executed. No work was lost (lane `aw/lane/zqs0px` holds 0
commits and its worktree is clean), so the cost is the wasted turn plus three blocked siblings, not
lost code.

## What the agent actually did

From `sessions/03-zqs0px-attempt-1-defect-reask.jsonl`, the agent launched the repository suite as a
BACKGROUND task and then waited for it:

    step 44: run_command  {"CommandLine":"python3 -m pytest"}          <- becomes task-44, RUNNING
    step 46: manage_task  {"Action":"status","TaskId":".../task-44"}   <- "Status: RUNNING ... [ 32%]"
    step 49: agent_response  "Waiting for test suite baseline run to finish."
    step 50: schedule    {"DurationSeconds":30,"Prompt":"Check if pytest baseline completed"}
    step 51: agent_response  "Waiting for test suite run to complete."
    terminating 2 background task(s) on exit
    {"event":"result","status":"SUCCESS","response":"Waiting for test suite baseline run to finish...",
     "duration_seconds":74.85,"num_turns":2}

So the turn ENDED while its own suite was still at 32%, the host terminated the background task, and
the agent's final response was literally "waiting". The suite needs ~122s here; the agent had ~75s of
turn and spent it idling on a `schedule` call.

The host reported `status: SUCCESS` for a turn that produced nothing. The driver correctly did not
believe it: no outcome file was written
(`outcomes/` holds only `01-hp9rot.json`), the defect report came back
`{"state":"absent","verdict":"absent-or-ambiguous"}`, and the item was recorded `partial`. The
driver's handling is RIGHT; the waste is upstream of it.

## Two distinct problems, both worth fixing

**A. The agent blocked its own turn on a background task it could not outlive.** Running the suite in
the background and then polling with `schedule` is a losing pattern under a turn bound: the turn dies,
the task is killed, and the work is lost. A foreground `run_command` would have either completed or
produced a real timeout to report. This is agent-side behavior, which is why it needs a PROMPT or
runbook fix and not only a code fix.

**B. One `partial` sibling silently converted a 4-plan Set into 1 executed + 3 blocked.** That
cascade is correct per the dependency rules (`qmgn12` needs all three children `executed`), but the
TRIGGER was a turn that did no work at all. A turn that performs zero E-items and writes no outcome is
distinguishable from a turn that genuinely tried and fell short, and it is a strong candidate for a
retry rather than a terminal `partial` that blocks a whole Set.

## Fix sketch

1. TELL THE AGENT NOT TO BACKGROUND THE SUITE. The execution prompt should state that the validation
   suite must be run in the FOREGROUND, and that a background task will be killed when the turn ends.
   Cheapest, highest-value half.
2. STATE THE REMAINING TURN BUDGET IN THE PROMPT, so an agent can decide whether a ~2-minute suite run
   fits before starting it, instead of discovering the bound by being killed.
3. CONSIDER TREATING A ZERO-WORK TURN AS RETRYABLE. `zqs0px` wrote no outcome, performed no E-item and
   left a clean tree; `_reset_item_for_retry` already exists and the run had budget. A `partial` that
   blocks three siblings should require evidence that something was actually attempted.
4. Regression test: a turn whose only action is starting a background command and waiting must be
   recorded in a way that does not present as `SUCCESS` from the host, and (if 3 is adopted) must be
   retried rather than blocking its Set.

## Not a duplicate of

`1uq1cu` (the worker-role env breaking the agent's suite counts) is about the CONTENT of the suite
result; this is about the turn ending before any result exists. Independent, and both were observed in
the same night's runs.
