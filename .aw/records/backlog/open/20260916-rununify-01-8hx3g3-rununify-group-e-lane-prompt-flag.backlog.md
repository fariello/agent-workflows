- Id: 8hx3g3
- Status: open
- Set: rununify
- Priority: medium
- Work-Kind: followup
- Summary: Group E of the rununify lift is blocked on a DESIGN act, not a constant move: _lane_reclaim_prompt reads the same _LANE_PROMPT_DISABLED global that the permanently-unmovable disable_lane_prompt writes

## Workflow history
- 2026-09-16 created (aw backlog): Filed by rununify 03 (i3d6ml) execution 2026-09-17 as a defect-report finding.

MEASURED AT i3d6ml's EXECUTION HEAD e93ba3de by the closure method that plan's E-01 prescribes.

WHAT THE PLAN SAID. Plan i3d6ml classified 6 symbols as group E, 'blocked on a module CONSTANT (directly or transitively)', and its OQ-03 resolution ruled group E IN SCOPE for the lift on the premise that the fix is mechanical: 'perform the precursor move and then the lift, in the same pass'. The named precursors were the byte-identical constants LANE_PROMPT_TIMEOUT, _SIGINT_GRACE_SECONDS, _SIGTERM_GRACE_SECONDS and TERMINAL_STATES.

WHY THAT PREMISE IS WRONG FOR ONE OF THE SIX. `_lane_reclaim_prompt` closes over THREE module-level names, not one: LANE_PROMPT_TIMEOUT (a constant, movable), `select` (an import, trivial), and _LANE_PROMPT_DISABLED. The third is not a constant. It is the MUTABLE module-level flag that `disable_lane_prompt` writes through `global`, and `disable_lane_prompt` is group D: PERMANENTLY excluded from the lift, pinned by tests/test_runner_shared.py::UnmovableSymbolTests, for exactly this reason.

SO THE COUPLING IS A DEADLOCK, and it is the group-D hazard in the mirror. runner_shared's own docstring states the group-D direction: lifting the WRITER would make it write the shared module's flag while each host's reader kept reading its own. Lifting the READER instead produces the same silent failure from the other side: the shared reader would consult runner_shared._LANE_PROMPT_DISABLED, which no host's `disable_lane_prompt` ever sets, so prompt suppression on a repeated interrupt stops working. Neither direction has a test that names the cause, and the symptom is the one runner_shared documents: an unattended run pausing for a question nobody is there to answer.

WHAT THE ACTUAL WORK IS. Making these two symbols share requires the FLAG to stop being module-level mutable state: pass suppression as a parameter, carry it on a run-scoped object, or make the pair a small class. Any of those is a DESIGN decision about a live interrupt path, not the mechanical 'move a constant, then lift' the plan's OQ-03 authorized. Three tests exercise the behavior today and constrain the choice: UnmovableSymbolTests (tests/test_runner_shared.py), tests/test_lane_allocation_idempotent.py (the prompt-suppression behavior in both hosts), and the disable_lane_prompt call sites in each runner's interrupt teardown.

NOTE ALSO that runner_shared's 'NO module-level mutable state' prohibition (its docstring) independently forbids the naive fix of moving the flag, and records that a registration seam was already considered and DECLINED by the maintainer because process-global state makes behavior depend on import order.

SCOPE OF THIS ITEM. Just this pair plus `reclaim_lanes_on_interrupt`, which calls the prompt and is therefore transitively blocked on the same decision. It does NOT cover the other three group-E symbols (terminate_process, reconcile_disposition, locked_run), whose blockers really are a constant or an import.
