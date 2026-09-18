- Id: x7wfyx
- Status: open
- Blocks-Release: next
- Set: x7wfyx
- Priority: medium
- Work-Kind: bug
- Summary: Tell the agent its remaining turn budget, and retry a turn that provably attempted nothing instead of letting one partial block a whole Set

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): Split from q1z9gn: the agent-side prompt fix landed, but the driver still does not tell the agent its remaining budget and still treats a zero-work turn as a terminal partial that blocked three siblings

SPLIT OFF from `q1z9gn`, which is now `done`. That item's agent-side cause is fixed (the shared execute
prompt now tells the agent to run result-bearing commands in the FOREGROUND and never to end a turn
while waiting on one). Its fix sketch had three parts; parts 2 and 3 are DRIVER-side and are recorded
here rather than closed silently, because a prompt instruction is guidance and not a guarantee: the next
agent that ends a turn early for some other reason produces the same cascade.

MEASURED, run `run-20260918T045802Z-2547360`, item `zqs0px` (`nobugship-01`):

    02 zqs0px nobugship execute     partial              36s   <- did no work, wrote no outcome
    03 qmgn12 nobugship orchestrate dependency-blocked    -
    04 di08i9 nobugship execute     dependency-blocked    -
    05 rgaasb nobugship execute     dependency-blocked    -

Run outcome `BLOCKED`, 1 of 5 items executed. The turn used 36s of a 600s stall budget, exited 0, and
the host reported `status: SUCCESS`. No bound fired and none could have: the agent chose to stop.

## What is still missing

**A. THE AGENT IS NOT TOLD HOW MUCH TURN IT HAS LEFT.** The driver knows `stall_timeout` (600s here) and
`MAX_TURN_TIMEOUT`, and the agent knows neither. So an agent cannot decide whether a ~130-second suite
run fits before starting it; it discovers the bound by being killed. Stating the remaining budget in the
prompt is cheap and turns a guess into an arithmetic decision.

**B. A ZERO-WORK TURN IS TERMINAL WHEN IT COULD BE RETRYABLE.** `zqs0px` performed no E-item, wrote no
outcome file, and left a clean tree at the same HEAD it started from (`starting_head` ==
`ending_head` == `7c233993`, `git status` clean, lane holds 0 commits). That is DISTINGUISHABLE from a
turn that genuinely attempted the work and fell short, and `_reset_item_for_retry` already exists. A
`partial` that blocks three siblings should require evidence that something was attempted.

Suggested predicate for "nothing was attempted", all already recorded on the attempt: no outcome file
written, `starting_head == ending_head`, no commits on the lane branch, and a clean worktree. When all
hold, retry the item rather than marking it `partial`, bounded by the existing retry budget so a
deterministically-failing item cannot loop.

## Why the cascade itself is CORRECT and must not be "fixed"

`qmgn12` is an orchestrator requiring all three children `executed`, and `di08i9`/`rgaasb` declare
`executed:` edges. Blocking on an unmet prerequisite is exactly right, and loosening it would dispatch a
dependent against a base lacking the commits it depends on. The defect is the TRIGGER (a turn that did
nothing being treated as a terminal attempt), never the propagation.

## Honest limit on B

A retry costs a full turn's tokens and wall time, and an item that fails identically twice has burned
two. That is why the predicate must be NARROW (provably nothing attempted) rather than "the item did not
reach executed", and why the existing retry budget must bound it. If the budget is already spent, the
current terminal `partial` is the right outcome.
