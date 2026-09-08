- Id: onasuh
- Status: graduated
- Set: onasuh
- Priority: medium
- Work-Kind: feature
- Summary: Surface artifact and status discrepancies in aw doctor via shared audit engine

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan 6ltz1y (auditshare-01). Premise verified rather than trusted: find_artifact_file (run_viewer.py:439) and audit_step_artifact (:465) are still defined in run_viewer.py, consumed ONLY there (:489, :1463, :2554, :2558) and in its tests, and doctor.py/check_engine.py/cli.py reference NEITHER, so aw doctor cannot see artifact drift. TWO THINGS THE ITEM DID NOT SAY, both shaping the plan. FIRST, a straight lift-and-shift would propagate two measured defects: find_artifact_file hardcodes NINE directories including a nonexistent plans/archive and two legacy .agents/ paths against a live tree with FIVE plans subdirs and a weekly-SHARDED archive it cannot track, and it matches 'id6 in p.name' returning the FIRST hit with no collision policy, while selectors.resolve treats an id6 multi-match as a data bug not overridable by --force. So the extraction must consume selectors rather than carry the private walk into a second consumer. SECOND, the item's 'accounting for active/live runner states' clause is the reason doctor cannot just call this today: the predicate maps status onto an expected directory and a RUNNING step legitimately sits in pending/, so a liveness-blind consumer would flag every in-flight run; run_viewer's tests already cover a live case at tests/test_run_viewer.py:1285. The item's 'evaluate aw check' half is evaluated and deferred with a stated reason (the audit consumes gitignored run records absent from a clone and a lane, so a fail-closed CI gate would answer differently in CI than locally). No Blocks-Release on the item, so none inherited.
- 2026-08-29 created (aw backlog): Surface artifact and status discrepancies in aw doctor via shared audit engine

Surface artifact location and status discrepancies in `aw doctor` (and evaluate `aw check`) by extracting the audit logic in `run_viewer.py` (`audit_step_artifact` / `find_artifact_file`) into a shared reusable module. This ensures `aw runs`, `aw doctor`, and other diagnosis tooling share a single source of truth for artifact location/status drift, preventing inter-tool discrepancy divergence, while also accounting for active/live runner states.
