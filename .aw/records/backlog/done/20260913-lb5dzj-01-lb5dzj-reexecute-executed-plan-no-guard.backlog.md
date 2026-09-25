- Id: lb5dzj
- Status: done
- Set: lb5dzj
- Priority: high
- Work-Kind: bug
- Summary: aw oc run will re-execute an already-executed plan named by id6: determine_action maps executed to execute and no gate refuses it, so an agent turn is spent before finalize rejects the backwards transition

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: obsolete: initial_queue_status/TERMINAL_QUEUE_STATUSES (ee99c41d) keep executed plans out of dispatch
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.

## The defect

`aw oc run <id6>` naming a plan whose status is already `executed` dispatches it as WORK. There is no
admission gate for the already-executed case, and no flag is required to opt into a re-run.

The mapping is unconditional (`runner_shared.determine_action`, `:3066-3071`):

```python
def determine_action(status: str) -> str:
    """Return 'review' for to-review/draft plans; 'execute' for approved/ready plans."""
    norm = (status or "").lower().strip()
    if norm in ("to-review", "draft"):
        return "review"
    return "execute"
```

`executed` is neither `to-review` nor `draft`, so it falls through to `execute`.

## Verified, not inferred

Measured in this repository 2026-09-13:

```
discovered plans: 638
with status executed: 475

id6=oc4cph status=executed kind=child
action_for -> execute
```

So all 475 already-executed plans are discoverable by the runner AND resolve to the `execute` action.
`action_for` (`runner_shared.py:3074-3092`) only diverts an ORCHESTRATOR away from `determine_action`, and
only to `orchestrate`; a `child` plan gets `execute` regardless of being finished.

## Why no existing gate catches it

Three gates were checked and none applies:

1. `enforce_draft_admission_gate` (`oc_runipd.py:2801`) gates DRAFTS only, and only for status sweeps. An
   explicit id6 is deliberately admitted without gating (spec 2.5a bullet 2: "a draft named EXPLICITLY by
   path or id6 is admitted without gating; the operator named it, asking is noise"). That rule is
   reasonable for a draft and is the wrong rule for a finished plan.
2. `enforce_requested_action` (`oc_runipd.py:2428`) validates `--action <a>` against each item's derived
   action. It has no notion of "already executed", and it only fires when `--action` is passed at all.
3. The `plan_bucket(path) == "executed"` check at `oc_runipd.py:7016` is NOT a dispatch gate. It is the
   `runstop m0z0ti` fabricated-success gate for an item whose turn was FORCE-CUT after the agent already
   moved the plan, and it is documented as "deliberately narrow". It never runs on a fresh dispatch.

## What the operator gets

Expected sequence, traced through the code rather than executed end to end (see the honesty note below):
the item is queued with `action=execute`, an agent turn is spawned and paid for, and the run then reaches
`aw ipd finalize`, which refuses because `executed -> executed` is a backwards transition
(`ipd_lifecycle.py:717-722`, "missing predecessor: backwards transition"). `_TERMINAL_STATUSES` is
`frozenset(("executed",))` (`:620`) and `to_rank < from_rank` is the refusal condition.

So the failure is LOUD at the end but the COST IS ALREADY SUNK. On the measured runs of 2026-09-13 an
execute turn cost between $8.26 and $30.72, so an accidental id6 typo naming a finished plan can spend
that before failing.

Worse than the money: the agent turn RUNS. It is handed a plan whose work already exists, in a lane cut
from a HEAD that already contains that work, and asked to execute it. What it does in that situation is
undefined. It may no-op, it may duplicate, it may "fix" what it sees as missing.

## Expected behavior

Refuse an already-executed plan at admission, BEFORE any turn is spawned, naming the plan and its status,
and require an explicit flag to force a re-run. The refusal should occur at the same fail-closed point as
the dependency preflight, so a refused run leaves no host session, no run directory, and no durable state
to reconcile (that ordering is already described at `oc_runipd.py:2446-2449`).

## Suggested shape

1. Add an admission gate for terminal statuses, alongside the draft gate, refusing before the queue is
   frozen. Include `executed` and any other status in `_TERMINAL_STATUSES`.
2. Require an explicit opt-in to override (for example `--allow-executed` or `--force-rerun`), so a re-run
   is possible but never accidental. Follow the draft gate's precedent: the flag admits, it does not
   silently change behavior.
3. Apply it to BOTH hosts. `determine_action` and `action_for` are shared (`runner_shared`), so the gate
   belongs at the shared admission layer rather than in one driver.
4. Regression tests: (a) `aw oc run <executed-id6>` refuses with a message naming the plan and its status,
   and spawns NO agent turn; (b) with the override flag it proceeds; (c) a status sweep never selects an
   executed plan in the first place; (d) an orchestrator that is `executed` is unaffected by the gate,
   since `action_for` already routes it to `orchestrate`.

## Honesty note on what was and was not tested

VERIFIED BY DIRECT MEASUREMENT: discovery includes 475 executed plans; `action_for` returns `execute` for
an executed child plan; the three candidate gates do not cover this case; `executed -> executed` is a
backwards transition the transition checker refuses.

NOT TESTED END TO END: a full `aw oc run <executed-id6>` invocation was NOT performed, because doing so
would spawn a paid agent turn, which is the very cost this item is about. The sequence after dispatch is
therefore traced from the code, not observed. Anyone fixing this should confirm the observed behavior
first; it is possible `aw ipd begin` refuses earlier than finalize, which would make the failure cheap
rather than costly, and that would change the severity but not the defect.

## Related

- Backlog `cjefq5`: the runner also mishandles an already-executed plan as a DEPENDENCY, recording
  `file: null` and a guessed status for an executed Set child, which blocked every dependent and cost a
  whole run at queue build. Same underlying gap (already-executed plans are not modelled coherently), a
  different symptom, and worth fixing together.
