- Id: 7l1ggb
- Status: open
- Set: 7l1ggb
- Priority: low
- Work-Kind: bug
- Summary: test_rununify_run_queue.py's closure census never classified _integrate_stranded_lanes, a real double-defined fork in both runners

## Workflow history
- 2026-09-18 open (aw set): Not a release gate: the instance was repaired in zz5yxq's commit (the fork is now classified), and the residual work is a test-harness hardening (add the missing-direction assertion), not a shipping defect.
- 2026-09-18 created (aw backlog): test_rununify_run_queue.py's closure census never classified _integrate_stranded_lanes, a real double-defined fork in both runners

Found while executing plan `zz5yxq` (runnoop Order 01) and REPAIRED there; filed so the class of gap is recorded rather than only the instance.

THE DEFECT. `tests/test_rununify_run_queue.py` classifies every module-level name `run_queue` closes over into six classes, and its census asserts the six partition 41 names exactly. `_integrate_stranded_lanes` was reached by `run_queue` on BOTH hosts and appeared in NO class. Measured at the pre-change baseline: `missing: []  unclassified: ['_integrate_stranded_lanes']`. It is a REAL fork (`oc._integrate_stranded_lanes is agy._integrate_stranded_lanes` -> False; `__module__` `agent_workflows.oc_runipd` vs `agent_workflows.agy_runipd`), so it belonged in `STILL_DOUBLE_DEFINED` all along, and the split analysis that table feeds was understating the remaining work by one fork.

WHY IT WENT UNSEEN, which is the reusable lesson: `test_run_queue_still_closes_over_every_pinned_symbol` only fails in ONE direction (a LISTED name that stopped being reached). Nothing failed for a REACHED name that was never listed, so the table could silently omit a fork indefinitely.

FIXED IN PASSING by `zz5yxq`: the name was added to `STILL_DOUBLE_DEFINED` (8 -> 9) with the measurement recorded in a comment.

THE RESIDUAL WORK, and why it is worth an item. Add the MISSING-DIRECTION assertion (every REACHED name must be classified), so the next unclassified symbol fails a test instead of waiting for an unrelated plan to trip over it. `free_module_level_names` already computes what is needed; the assertion is `reached - classified == set()`. Note its docstring deliberately accepts a simpler scanner on the grounds that assertions run in the membership direction only, so adding the reverse direction may require tightening the scanner first, or allowlisting names it over-reports.
