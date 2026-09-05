- Id: nueip1
- Status: open
- Set: depblock
- Priority: medium
- Work-Kind: bug
- Summary: dependency-blocked is terminal and unsatisfiable-means-end-the-run: an item blocked once is never revisited even after its prerequisite completes

## Workflow history
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
