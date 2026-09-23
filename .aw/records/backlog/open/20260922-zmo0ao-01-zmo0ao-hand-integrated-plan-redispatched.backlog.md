- Id: zmo0ao
- Status: open
- Blocks-Release: next
- Set: zmo0ao
- Priority: high
- Work-Kind: bug
- Summary: a hand-integrated lane leaves its plan approved in pending/, so the runner re-dispatches an already-merged plan and spends an agent turn on an empty diff

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing li44r9: its lift, backlog and evidence commits plus the integrate commit are all ancestors of HEAD, yet the plan sat approved in pending/ and was queued at position 02, costing a turn that produced no code. Distinct from lb5dzj, which covers the already-executed status rather than a stale approved one.

## The defect

A plan whose lane is integrated BY HAND keeps `- Status: approved` and stays in
`.aw/records/plans/pending/`, because the `aw ipd finalize` transition is part of the RUNNER's publish
path and not part of a human `git merge`. The runner then maps `approved` -> `execute` and re-dispatches
the plan as work, so a full agent turn is spent discovering the deliverable is already on `main`.

MEASURED 2026-09-23 on `li44r9` (hostdedup Order 01). All four of its commits are ancestors of HEAD,
confirmed with `git merge-base --is-ancestor`:

    12a5c05b  lift(li44r9): give 16 byte-identical runner symbols one definition each
    266c0cf3  chore(backlog): file four findings from executing li44r9
    e2e8757d  docs(li44r9): record E-01..E-08 performed and V-01..V-08 verified with pasted evidence
    d5d5c8eb  integrate: merge verified lane li44r9 to main

`d5d5c8eb` is a hand integration (its message records resolving four conflicts, including a near-miss
that would have reverted `finidem ld8lb3`). The plan carries every `E-*` as `performed`, every `V-*` as
`pass` with pasted evidence, and `aw ipd lint --phase pre-transition` exits 0. Nothing about it is
incomplete except the transition. It was nonetheless queued at position 02 of
`run-20260923T023317Z-3622118` and consumed an agent turn that produced no code.

## Why this is not already covered

Backlog `lb5dzj` covers the ADJACENT case: `aw oc run <id6>` naming a plan whose status is already
`executed`, where `runner_shared.determine_action` maps `executed` -> `execute` with no admission gate.
That is a different input. Here the status is legitimately `approved`, so `determine_action` is
CORRECT to map it to `execute`; the defect is that the plan's status no longer describes the tree,
and nothing reconciles the two before an agent turn is spent.

## Cost, which is what makes this a bug rather than a chore

An operator waits on a whole agent turn (minutes, plus model spend) for an empty diff. The turn is
also not harmless: an executor that trusts the queue rather than re-deriving state could plausibly
re-apply a lift onto a tree that has since absorbed a conflicting fix, which is exactly the revert the
hand integration caught by hand. The user-perceptible impact is a wasted run slot in an unattended
queue, where slots are the scarce resource.

## A second-order consequence, observed

Stale status propagates into other records. Backlog `e59lhn` (now `done`) reasons about lane
supersession and states that `li44r9`'s plan is "still in pending/, so [its] work genuinely has not
landed". That was true when written and is false at HEAD. Any predicate keyed on a plan's directory
inherits the same staleness.

## Candidate fixes, not equivalent

1. AN ADMISSION CHECK AT DISPATCH: before spending a turn on an `approved` plan, ask whether its
   deliverable is already on the current branch (its lane branch merged, or its recorded execution
   commits ancestors of HEAD). Report it as already-landed and offer retirement instead of execution.
   Cheap, and it fails in the safe direction (a false negative just runs the plan).
2. MAKE HAND INTEGRATION CARRY THE TRANSITION: document and tool the publish path so a human merge of
   a lane runs the same finalize the runner would, e.g. an `aw integrate` verb. Fixes the cause rather
   than the symptom, but only binds humans who use it.
3. AN `aw check` RULE for a plan in `pending/` whose execution commits are ancestors of HEAD, so the
   drift is visible on the attention surface even when no run is queued.

RECOMMENDATION: (1) plus (3). (1) stops the turn being spent, (3) surfaces the backlog of plans already
in this state. (2) is worth doing but cannot be relied on alone, since it is a protocol and not an
enforcement boundary.

## Where

`runner_shared.determine_action` and the queue-build/dispatch path in `agent_workflows/oc_runipd.py`
and `agent_workflows/agy_runipd.py`; the plan lifecycle in `agent_workflows/engine.py`. Instance:
`.aw/records/plans/pending/20260917-hostdedup-01-li44r9-lift-the-seventeen-byte-identical-runner-symbols-into-runner.ipd.md`.

Found while executing li44r9 in run `run-20260923T023317Z-3622118`.
