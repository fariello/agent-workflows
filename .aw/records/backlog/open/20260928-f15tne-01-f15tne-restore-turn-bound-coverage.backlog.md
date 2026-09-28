- Id: f15tne
- Status: open
- Set: f15tne
- Priority: medium
- Work-Kind: followup
- Summary: The bound-expiry and turn-bound surface has zero test coverage: spec 7ckptx A10's permission-deadline demonstration was lost when 19313eed deleted tests/test_turn_bounds.py

## Workflow history
- 2026-09-28 created (aw backlog): Filed while authoring plan 2o9osz (from backlog jt01do), which needed a carrier for coverage it deliberately did not restore. MEASURED at HEAD 40c6dcc3: searching tests/ and tools/ for bound_expiry_reaper, bound_expiry_record, driver_bound_for_host, BOUND_MAX_TURN, BOUND_PERMISSION, MAX_TURN_TIMEOUT and TurnBoundWatch returns ZERO hits in either tree. Plan lhmrhx delivered spec 7ckptx criterion A10 (an unanswered permission request terminates within the deadline, the disposition is the safe-failure value, the reason names which bound fired, and no second reaper is introduced, checked structurally rather than by text grep) into tests/test_turn_bounds.py; commit 19313eed ('test: trim test suite from 9,136 to under 2,000 tests') deleted that file, and tests/test_lane_permission_posture.py with it. Plan 2o9osz adds only a CONTRACT guard (tests/test_reap_contract.py, that the reap annotation matches the call), which is deliberately not behavioral coverage. Restoring A10 means re-deriving a spec-acceptance demonstration with real subprocesses. Note spec 7ckptx is approved and its A10 is currently undemonstrated.

Scope: restore behavioral coverage for agent_workflows/lane_containment.py's TurnBoundWatch, bound_expiry_reaper, bound_expiry_record and driver_bound_for_host, sufficient to demonstrate spec 7ckptx criteria A10, A10b, A10c and A10d.

Do NOT simply resurrect the deleted file wholesale: commit 19313eed's sibling 80db6750 deleted 366 tests that 'pinned code structure instead of behaviour' (reading source with ast, __file__, or substring search), so any restored test must exercise the code. Note A10 itself requires the no-second-reaper check be done structurally rather than by text grep, which is the one sanctioned exception and should be written as an import-graph or AST check with that reason stated.
