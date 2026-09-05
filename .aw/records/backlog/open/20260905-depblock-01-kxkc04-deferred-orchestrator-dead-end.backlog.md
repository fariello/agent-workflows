- Id: kxkc04
- Status: open
- Set: depblock
- Priority: high
- Work-Kind: bug
- Summary: an orchestrator deferred early can never finalize later in the same run: the deferral path writes a terminal status instead of leaving it queued

## Workflow history
- 2026-09-05 created (aw backlog): an orchestrator deferred early can never finalize later in the same run: the deferral path writes a terminal status instead of leaving it queued

THE DEFECT. The orchestrator dispatch path (`oc_runipd.py:5886-5924`) tests whether every child of
the Set reached `executed`. When they have not, it writes:

    runnable["status"] = "dependency-blocked"     # oc_runipd.py:5908

and then `continue`s. The run correctly keeps going - but the orchestrator is now
`dependency-blocked`, which is in `TERMINAL_STATES` (`oc_runipd.py:249`), so it is no longer
`queued` and the selection filter (`oc_runipd.py:5812`) excludes it FOREVER.

Consequence: its children can all reach `executed` later in the very same run, and the orchestrator
will still never be finalized. The event is even named `orchestrator-deferred`
(`oc_runipd.py:5914`) - a deferral is by definition something you come back to, and nothing ever
does.

WHY IT USUALLY HIDES. `dependency_depth` (`oc_runipd.py:3250`) treats every non-orchestrator
member of the Set as a prerequisite (`oc_runipd.py:3270-3279`), and depth is the FIRST key in
`queue_sort_key` (`oc_runipd.py:3285`). So an orchestrator normally sorts AFTER its children and is
not reached until they are done. The bug only bites when the orchestrator is dispatched while
children are still outstanding - which is exactly what happens when a child is slow, or blocked, or
when the children are not in this run's queue at all.

MEASURED. Run `run-20260905T050043Z-639569`: `5e4sb6` (Set `rununify`, an Order-0 orchestrator)
was deferred at 05:00:44, ONE SECOND into a 7h40m run, and stayed `dependency-blocked` for the
entire run. Three other orchestrators in that run (`rh5tt6`, `3m0urk`, `h0zljh`) ended `queued`,
i.e. never reached, so the incident shows the failure and the normal case side by side.

THE FIX. Do not write a terminal status for a condition that may clear. Leave the orchestrator
`queued` and let the next loop iteration re-test it - which is precisely what the loop already does
for items merely SKIPPED by the inner selection pass (`oc_runipd.py:5829-5833`), where no status is
written and the item is naturally reconsidered. The orchestrator path should behave the same way.

Reserve a terminal status for the genuinely dead case: a child that reached a non-success TERMINAL
state can never become `executed`, so THAT orchestrator really is finished and should say so. The
distinction "not ready yet" versus "can never be ready" is the same one item `nueip1` covers for
ordinary items; this is its orchestrator-specific half. Fix them together if convenient, but neither
subsumes the other: `nueip1` is about the drain-time mass-labelling path, this is about a single
write on the orchestrate branch.

GUARD AGAINST A NEW HANG. Leaving it `queued` must not let the loop spin forever re-testing an
orchestrator whose children will never finish. The drain-time path
(`oc_runipd.py:5847`, when `runnable is None`) already terminates a run whose remaining items are
unsatisfiable, so an orchestrator left queued with dead children will be labelled there. Verify that
explicitly rather than assuming it, and make sure the reported reason names the actual unfinished or
dead children.

SECOND, SEPARABLE DEFECT ON THIS PATH - "no children in queue" is reported as "unmet
dependencies" naming none. `_set_children_all_executed` (`oc_runipd.py:717-736`) returns
`(saw_child and not unfinished), unfinished`, so when the Set has NO children in this run's queue it
returns `(False, [])` under the documented "No children in-queue means nothing to gate on; treat as
not-all-done (safe)" branch. That produced `5e4sb6`'s event with `unfinished_children: []` and a
run summary reading "dependency-blocked (unmet dependencies)" while naming no dependency at all.

The safe default is CORRECT and must not change. The MESSAGE is the defect: distinguish "children
exist and are unfinished: <ids>" from "no children of Set <setid> are in this run's queue", and say
which. Note that for the second case waiting genuinely cannot help, so it IS legitimately terminal -
it should simply say so accurately instead of implying a dependency it cannot name.

Filed as one item because both defects live on the same ~40-line branch and a fix touching one should
correct the other. `5e4sb6`'s own children (`2r306y`, `818uru`) are already `executed` on main,
so that orchestrator is finalizable by hand today, independent of this fix.
