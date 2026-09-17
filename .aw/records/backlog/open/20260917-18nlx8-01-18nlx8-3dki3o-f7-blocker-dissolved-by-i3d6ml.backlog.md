- Id: 18nlx8
- Status: open
- Set: 18nlx8
- Priority: medium
- Work-Kind: followup
- Summary: plan 3dki3o's Goal table and F-7 blocker are stale: sibling i3d6ml lifted EmptyStatusSelection into runner_shared, so the closure is 9/2/5/8/3 not 8/2/5/9/3 and the proven exit-0-becomes-exit-2 hazard is structurally gone

## Workflow history
- 2026-09-17 created (aw backlog): plan 3dki3o's Goal table and F-7 blocker are stale: sibling i3d6ml lifted EmptyStatusSelection into runner_shared, so the closure is 9/2/5/8/3 not 8/2/5/9/3 and the proven exit-0-becomes-exit-2 hazard is structurally gone

FOUND BY: rununify Order 11 (`3dki3o`) E-01, re-deriving the closure at execution HEAD as its own
E-item demands ('refuse to proceed to E-04 on a stale list').

THE CHANGE, measured at HEAD 761edad3. `main`'s closure is still 27 module-level names, but ONE has
changed class:

    EmptyStatusSelection:  still-defined-twice  ->  shared-same-object

    class histogram  plan (2026-09-16)   HEAD (2026-09-17)
    shared-same-object            8                   9
    shared-host-wrapper           2                   2
    one-object-agy-imports-oc     5                   5
    still-defined-twice           9                   8
    oc-only                       3                   3

CAUSE: sibling `i3d6ml` (commit `d26c1061`, 'lift the 9 closure-clean shared runner symbols into
runner_shared') moved the class. Both hosts now resolve the SAME object
(`oc.EmptyStatusSelection is agy.EmptyStatusSelection is runner_shared.EmptyStatusSelection`).

WHY IT MATTERS: plan `3dki3o` F-7 is marked BLOCKER and is one of the three findings its blocking
OQ-03 rested on. Its mechanism REQUIRED two distinct sibling classes, neither a subclass of the other,
so that a shared core's `except EmptyStatusSelection` would miss one host and return 2 where spec
`25kzda` 2.4a property 3 requires 0. With one shared class that mechanism cannot fire. The hazard was
reproduced under a deliberate re-fork during execution (0 for the matching class, 2 for the sibling),
confirming both the original finding AND that it is now dissolved.

SO THE SPLIT IS CHEAPER THAN THE APPROVED PLAN SAYS: eight injections rather than nine, and one of
three blocker findings retired. Anyone sequencing the remaining `main` work should re-read the closure
rather than the plan's table.

GUARDED, so this cannot silently regress:
`tests/test_rununify_main.py::TheClosureClassification::test_the_still_double_defined_count_is_stated_not_implied`
fails if the class is re-forked, and
`tests/test_rununify_main_characterization.py::TheEmptySweepExitCodeContract` pins both the behavior
(exit 0) and the structural precondition (one shared class).
