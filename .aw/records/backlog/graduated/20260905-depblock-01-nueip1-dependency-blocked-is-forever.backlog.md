- Id: nueip1
- Status: graduated
- Set: depblock
- Priority: medium
- Work-Kind: bug
- Summary: dependency-blocked is terminal and unsatisfiable-means-end-the-run: an item blocked once is never revisited even after its prerequisite completes

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan akzy45 (depblock-01), carrying both parts. See the RE-MEASUREMENT section appended. Both confirmed live and every claim held in substance, but EVERY line number had drifted by 1300 to 3400 lines and was re-located by symbol. THE MEASUREMENT IS STRONGER THAN THIS ITEM RECORDED: reading run-20260905T050043Z-639569's state.json shows 5slbpi was blocked on 'executed:6ypimw (target dependency-blocked)', a CASCADE OF A CASCADE where a dependent was killed by a sibling's LABEL rather than by any real unsatisfiability. That is the case no root-cause fix elsewhere prevents, and it is the strongest argument for the split. All three prerequisites now read executed, so all three dependents were killed by a condition that has since cleared. The scope boundary re-verified against the covering plans: 51vw4y E-01 states that keeping integration-deferred OUT of TERMINAL_STATES 'is exactly what stops the cascade from killing dependents', so that plan already DEPENDS on this distinction rather than duplicating it, and this item's instruction not to close it by pointing at 5wdoze/yocdq4 is correct. 7nkcgp's deliberate preservation re-verified, so this is a design change with a stated rationale.
- 2026-09-05 created (aw backlog): dependency-blocked is terminal and unsatisfiable-means-end-the-run: an item blocked once is never revisited even after its prerequisite completes

THE DEFECT, IN TWO PARTS.

PART 1 - BLOCKED IS TERMINAL. `dependency-blocked` is in `TERMINAL_STATES`
(`oc_runipd.py:249`). Once written, the item is not `queued`, so the selection filter
(`oc_runipd.py:5812`) never considers it again. `cascade_dependency_blocked`
(`oc_runipd.py:3661`) only ever moves `queued -> dependency-blocked`, never back.

PART 2 - ALL-OR-NOTHING BREAK. When NO queued item is satisfiable, the loop marks EVERY remaining
queued item `dependency-blocked` and BREAKS out of the run entirely
(`oc_runipd.py:5847-5881`). So a single unsatisfiable node does not park one item; it can END a run
that still holds work. The runner's own comment at `oc_runipd.py:276-278` says exactly this: "when
NO queued item is satisfiable, the selection loop marks EVERY remaining queued item
`dependency-blocked` and BREAKS out of the run. So a findings-block can end a run rather than
merely park one item."

WHAT WORKS TODAY, so it is not mistaken for broken: an item merely SKIPPED by the inner selection
pass (`oc_runipd.py:5829-5833`) writes no status and IS re-examined on the next iteration. Ordering
is handled correctly right up until something is actually LABELLED blocked. The bug is the labelling,
not the scheduling.

RECOVERY IS MANUAL AND NON-OBVIOUS. A bare `resume` does NOT re-queue a dependency-blocked item;
only `resume --retry-incomplete` does (`oc_runipd.py:5745-5758`). The runner states this in
`DEPENDENCY_BLOCK_RECOVERY_HINT` (`oc_runipd.py:279-283`) and surfaces it in the event payload and
report, which is good, but it means an unattended run that hits this stops making progress until a
human intervenes with a specific flag.

MEASURED. Run `run-20260905T050043Z-639569`: `6ypimw`, `wpomxa`, and `5slbpi` all ended
`dependency-blocked` solely because their prerequisites ended `integration-blocked` rather than
`executed`. Those prerequisites' lanes are intact and merge clean today, so all three were blocked
by a transient condition that has since cleared, and none will ever be retried by the runner.

SCOPE BOUNDARY - READ THIS BEFORE STARTING. The integration-deferral ladder and the re-integrate
verb (items `5wdoze` and `yocdq4`) fix the COMMON CAUSE of the blocking seen in that run: if
prerequisites integrate instead of stranding, these dependents become runnable and the cascade never
happens. That is the bulk of the practical harm and it is being addressed elsewhere.

THIS item is the remaining DESIGN defect that survives those fixes: "blocked is forever" and
"unsatisfiable ends the run" are wrong independent of WHY something was blocked. Do not close this
item by pointing at those two.

DESIGN DIRECTION. The core confusion is that ONE status carries two different facts: "not ready
yet" and "can never be ready". Distinguish them. A prerequisite in a NON-TERMINAL state means wait
and re-test; a prerequisite in a non-success TERMINAL state means genuinely dead, and only that case
warrants the terminal label and the cascade. `cascade_dependency_blocked` already reasons in exactly
these terms (`oc_runipd.py:3707-3714` tests `st in TERMINAL_STATES and st not in required`), so
the concept exists; it is the drain-time path at `oc_runipd.py:5847-5881` that flattens the
distinction by labelling everything blocked at once.

Note the interaction with `5wdoze`: once `integration-deferred` exists as a NON-TERMINAL status,
this distinction becomes load-bearing rather than theoretical, because a dependent of a deferred item
must wait rather than die.

RELATED. `7nkcgp` (executed) is the authoritative record of this behavior: its review corrected a
false draft claim and established the re-queue semantics with citations, then explicitly PRESERVED
the behavior ("Confirm the runner's re-queue default was NOT changed"). So this is documented and
deliberate as of that plan, and changing it is a real decision rather than a bug fix nobody
considered. `mzy2so` (done) is the adjacent ordering defect where a level-2 wind-down breaks BEFORE
the marking block, closed as a fixture bug with no product change. Sibling: the deferred-orchestrator
dead end, filed separately.

## RE-MEASUREMENT, 2026-09-08 at HEAD a2e0438a during graduation

BOTH PARTS CONFIRMED LIVE and the SUBSTANCE of every claim held, but EVERY LINE NUMBER HAD DRIFTED, most
by 1300 to 3400 lines. Re-located by symbol:

    TERMINAL_STATES                cited :249        actual :308-326
    cascade_dependency_blocked     cited :3661       actual :4177
    drain-time labelling branch    cited :5847-5881  actual :7123-7157
    DEPENDENCY_BLOCK_RECOVERY_HINT cited :279-283    actual :337-340
    re-queue branch                cited :5745-5758  actual :7012
    the runner's own comment       cited :276-278    re-verified in substance

Confirmed: `'dependency-blocked' in TERMINAL_STATES` -> True; the drain arm still marks EVERY remaining
queued item and BREAKS; re-queue still happens only under `if retry_incomplete:`.

THE MEASURED INCIDENT IS STRONGER THAN THIS ITEM RECORDED, found by reading that run's `state.json`
rather than its summary. Run `run-20260905T050043Z-639569`:

    6ypimw | dependency-blocked | ['executed:76gsmv (target integration-blocked)']
    wpomxa | dependency-blocked | ['executed:eyh1fu (target integration-blocked)']
    5slbpi | dependency-blocked | ['executed:6ypimw (target dependency-blocked)']

THE THIRD ONE IS A CASCADE OF A CASCADE: `5slbpi` was killed because its prerequisite had itself been
LABELLED, not because anything about `5slbpi` was unsatisfiable. That is the most persuasive evidence
for this item, and it is the case NO root-cause fix elsewhere prevents: any future terminal label
propagates identically. All three prerequisites (`76gsmv`, `eyh1fu`, `6ypimw`) now read `executed`, so
all three dependents were killed by a condition that has since cleared and none will be retried.

THE SCOPE BOUNDARY IN THIS ITEM IS CORRECT AND WAS RE-VERIFIED against the covering plans rather than
accepted: pending plan `51vw4y` (from `5wdoze`, to-review) adds the non-terminal `integration-deferred`,
and its E-01 states that keeping it OUT of `TERMINAL_STATES` "is therefore exactly what stops the
cascade from killing dependents", naming `cascade_dependency_blocked` as the site. So that plan already
DEPENDS on the distinction this item describes being honored, which makes this item's design defect a
precondition for that plan's soundness rather than a duplicate of it. This item's instruction "Do not
close this item by pointing at those two" is therefore correct, and the graduated plan does not
re-implement `integration-deferred`.

`7nkcgp`'s PRESERVATION RE-VERIFIED: its review record corrected a false draft claim that recovery was
free on resume, established the re-queue semantics with citations, and then explicitly instructed "Do
NOT change the re-queue default in this plan". So this is a deliberate design change needing a stated
rationale, exactly as this item says, and the graduated plan fences the default out.

ONE HAZARD RECORDED FOR THE EXECUTOR: the orchestrator dispatch path's comment records that "just leave
it queued" fixes only ONE of two failure modes and that leaving a STRUCTURAL refusal reconsiderable
"would retry a structural refusal every iteration and SPIN". So the re-test mechanism must be bounded
or strictly transient-only; the graduated plan's E-03 and its mutation-check cover that.

GRADUATED to plan `akzy45` (depblock-01), carrying both parts plus the cascade-of-a-cascade case. Its
OQ-01 defers whether the transient case needs its own OPERATOR-VISIBLE status (as opposed to different
internal handling), because `cascade_dependency_blocked`'s docstring records that it deliberately
declined to add `dependency-not-met` since "inventing a parallel state would split the run records
already on disk", and because `51vw4y` is concurrently adding a non-terminal status. If that half is
deferred to a follow-on, this item should be set `graduated` rather than `done`.
