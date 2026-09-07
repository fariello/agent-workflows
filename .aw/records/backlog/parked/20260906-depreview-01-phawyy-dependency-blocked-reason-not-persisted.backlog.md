- Id: phawyy
- Status: parked
- Set: depreview
- Priority: high
- Work-Kind: bug
- Summary: a dependency-blocked item records no reason in run state or events, so the cause survives only in the terminal that happened to be watching

## Workflow history
- 2026-09-07 parked (aw set): RETRACTED: the premise is false. Measured at HEAD 670bf38c: both blocked paths already persist the reason (unsatisfied_dependency_reasons, dependency_block_recovery) and both emit events carrying reasons plus recovery; verified present on both runs this item was filed from. My original probe checked a hardcoded list of wrong key names and I read its silence as absence. What remains true is far narrower and not release-blocking: aw runs does not SURFACE the persisted reason in rendered output. Re-scope to the viewer or close.
- 2026-09-06 created (aw backlog): a dependency-blocked item records no reason in run state or events, so the cause survives only in the terminal that happened to be watching

/tmp/opencode/dep2.md

---

## RETRACTED 2026-09-07: THE PREMISE IS FALSE

This item asserts that a `dependency-blocked` item "records no reason in run state or events".
MEASURED at HEAD `670bf38c` while attempting to graduate it: THAT IS WRONG. Both blocked paths
already persist the reason in full, and the events file carries it too.

THE DRAIN PATH (`oc_runipd.py:7076-7096`) writes FOUR keys onto the item, not one:

    item["unsatisfied_dependencies"]        = missing
    item["unsatisfied_dependency_reasons"]  = why      # the per-dependency reason MAP
    item["dependency_block_recovery"]       = DEPENDENCY_BLOCK_RECOVERY_HINT

and emits an event carrying `dependencies`, `reasons` AND `recovery`. The comment there records
that `unsatisfied_dependency_reasons` was added deliberately as "an ADDITIVE companion key" by
revgate Order 03 (`7nkcgp`) E-04, precisely so the reasons live alongside the flat list.

THE CASCADE PATH (`:4166-4180`) likewise sets `unsatisfied_dependencies` and emits an event with
`dependencies` plus a `reason`.

VERIFIED ON BOTH RUNS THIS ITEM WAS FILED FROM. `run-20260907T025241Z-199431` and
`run-20260907T030340Z-200856` each hold, on the blocked queue entry:

    unsatisfied_dependency_reasons = {'executed:tm2cz8': "executed:tm2cz8: external target tm2cz8
      is in 'pending', needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so
      it cannot become satisfied here)"}
    dependency_block_recovery = "resolve the named cause, then re-queue with `aw oc runipd resume
      --repo <repo> --retry-incomplete <run-id>`; a bare `resume` does NOT re-queue a
      dependency-blocked item"

and the events file carries the same `reasons` map plus `recovery`.

WHY I FILED IT ANYWAY, recorded because the error is instructive rather than embarrassing. My probe
printed a HARDCODED list of candidate keys (`unsatisfied`, `dependency_reasons`, `item_dependencies`,
`reason`) and none of those is the real key name (`unsatisfied_dependency_reasons`). I read the
probe's silence as absence rather than checking what keys the record actually had. The lesson is the
one this repository already records for exit codes measured through a pipe: an absence reported by a
tool I wrote myself is evidence about my tool, not about the system.

WHAT REMAINS TRUE, and is much narrower: `aw runs <id>` does not SURFACE the persisted reason in its
rendered output, so an operator sees that an item was dependency-blocked without seeing why unless
they read `state.json` directly. That is a display gap, not a persistence gap, and it is not worth a
release-blocking item. Anyone picking this up should re-scope it to the viewer, or close it.

NOT GRADUATED. The sibling item `yf9fj9` (the real gate bug this one claimed to have hidden) IS
graduated, to plan `03ie04`; that bug was diagnosable from the terminal message alone, which is
itself evidence this item's premise was wrong.
