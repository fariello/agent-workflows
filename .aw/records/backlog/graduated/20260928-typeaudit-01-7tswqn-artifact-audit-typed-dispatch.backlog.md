- Id: 7tswqn
- Status: graduated
- Graduated-To: typeaudit
- Blocks-Release: next
- Set: typeaudit
- Priority: high
- Work-Kind: bug
- Summary: artifact audit type blindness flags graduated backlog items as regressed

## Workflow history
- 2026-09-28 graduated (aw set): graduated to plan mlhryi
- 2026-09-28 created (aw backlog): artifact audit type blindness flags graduated backlog items as regressed

## Description
When plan `8l8dgb` introduced typed queue entries for runner dispatch (allowing runs to execute `--action plan` over backlog items and `--action review` over specs), `agent_workflows/artifact_audit.py` was not updated to be artifact-type or action aware.

As observed in active run `run-20260928T034313Z-2200079`, 31 successfully planned backlog items residing cleanly in `records/backlog/graduated/` (or `done/`) were reported as `regressed` by `aw runs`, with 19 queued/running/fail-gate steps reported as `unknown`:
- `expected_dir_for_status` maps runner status `executed` to directory `executed/` using plan-only `_TERMINAL_EXPECTED_DIR`.
- `_status_disagrees` demands that declared status match `executed` or `complete`.
- `_classified` treats any non-executed actual directory as `CLASS_REGRESSED`.
- `run_viewer.StepSummary` drops `artifact_type` when parsing queue items from `state.json`.

## Requirements
1. `StepSummary` in `agent_workflows/run_viewer.py` must retain `artifact_type` and pass `artifact_type` and `action` to `audit_step_artifact`.
2. `agent_workflows/artifact_audit.py` must support typed expectation mapping `(artifact_type, action, run_status)` aligning with `agent_workflows/record_placement.py`.
3. Backlog items whose planning succeeded and transitioned to `graduated/` or `done/` must classify cleanly as `CLASS_UNCHANGED` (no location or status mismatch).
4. In-flight queued/running backlog items in `open/` must classify as `CLASS_UNCHANGED` without false location mismatch.
5. Unit tests in `tests/test_artifact_audit.py` and `tests/test_run_viewer.py` must pin typed audit behavior for backlog, spec, and plan steps.
