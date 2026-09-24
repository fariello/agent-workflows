- Id: e8i8dz
- Status: open
- Blocks-Release: next
- Set: e8i8dz
- Priority: high
- Work-Kind: bug
- Summary: runner_shared._record_checkpoint_stop and _record_forced_stop were called by execute_item_core without the required git_status_fn, so every deliberate stop on that path raised TypeError and wrote no stop record

## Workflow history
- 2026-09-23 created (aw backlog): Found by hostdedup Order 02 (nmlx47) E-05 while lifting _record_forced_stop; FIXED in that same change (commit 63b71d8b). Filed for the record because the defect was LIVE and its blast radius is larger than the symbol lifted.

MEASURED 2026-09-23 at HEAD 525442c4, before the fix.

WHAT WAS WRONG. `runner_shared.execute_item_core` records a deliberate stop through the module-level `_record_forced_stop` (level 4) and `_record_checkpoint_stop` (level 3), at FOUR call sites: two on the execute turn and two on the verifier turn. `_record_checkpoint_stop` takes a REQUIRED keyword-only `git_status_fn` (added by hostdedup Order 01 `li44r9`, which fixed the same class of defect in that function's body), and NONE of the four call sites passed it. So every one raised

    TypeError: _record_checkpoint_stop() missing 1 required keyword-only argument: 'git_status_fn'

WHY IT MATTERED. Those handlers sit in `except runner_stop.StopNowForce` / `except runner_stop.StopAtCheckpoint` blocks whose job is to WRITE the stop record and then re-raise. A TypeError there means `item[\"stopped\"]` is never written, and `runner_stop.is_indeterminate` - the ONE predicate every level-4 gate branches on - reads exactly that record. So on this code path a level-4 stop produced no certainty marker at all, which is the condition spec c4gd2h R22 exists to prevent: the driver cannot then tell a forced cut from a completed turn.

HOW IT SURVIVED. `execute_item_core` is the UNIFIED execution core both hosts now call, but these four sites resolve the SHARED functions from module globals rather than from `driver_module`, so each host's own correctly-injecting wrapper was bypassed. No test drove a deliberate stop through the shared core, which is why a green suite coexisted with it.

THE FIX (in 63b71d8b). All four sites now pass `git_status_fn=git_status`, where `git_status` is the name `execute_item_core` already binds from `driver_module` for exactly this reason. `_record_forced_stop` gained the same required parameter, so the mistake cannot recur silently, and `tests/test_hostdedup_divergent_unify.py::TheForcedStopRecordsTheOBSERVEDTree` now asserts the signature, that the body calls the injected function and not the module-level one, and that all four call sites pass it.

WHAT IS STILL OPEN, and why this item is filed rather than closed: there is no test that drives a REAL deliberate stop (level 3 and level 4, execute and verifier turn) through `execute_item_core` and asserts the recorded `git_state` is the OBSERVED working tree rather than an `<unobserved: ...>` string. The structural guard added above would catch a regression in the wiring; it would not catch a future handler added without the injection. That behavioral test is the remaining work.
