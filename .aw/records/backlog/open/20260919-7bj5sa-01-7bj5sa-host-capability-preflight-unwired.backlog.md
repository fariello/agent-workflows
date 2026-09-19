- Id: 7bj5sa
- Status: open
- Set: 7bj5sa
- Priority: medium
- Work-Kind: chore
- Summary: Neither host runner calls host_sandbox_profile.preflight_host_capabilities, so spec 25kzda 5.4/5.7's host_capability_unavailable refusal can never fire

## Workflow history
- 2026-09-19 created (aw backlog): Neither host runner calls host_sandbox_profile.preflight_host_capabilities, so spec 25kzda 5.4/5.7's host_capability_unavailable refusal can never fire

MEASURED 2026-09-19 at HEAD 7562ca6c while executing plan m85gxh: 'preflight_host_capabilities' occurs ZERO times in agent_workflows/oc_runipd.py, agy_runipd.py and runner_shared.py. The function itself is shipped, tested (tests/test_host_capability_extension.py), and correctly per-item (it returns aborts_run=False, cascade_dependents=True, session_started=False with reason_code host_capability_unavailable). Spec 25kzda 5.4 and 5.7 both require an item to be refused before session start when a required host guarantee is unproven, and spec 5.2/2.1 line 171 states it plainly: 'Before any actionable item starts, the engine loads a current capability descriptor for the exact host/version/mode and refuses the item if a required guarantee is unsupported, unverified, degraded below the required assurance, or stale.' So the gate exists and is unreachable, which from the operator's seat is indistinguishable from no gate. This is the same defect class runner_shared.enforce_mixed_type_gate's docstring already records for the mixed-type gate ('a fully tested, importable, completely unreachable gate is indistinguishable from no gate at all'). Plan m85gxh kept host_capability_unavailable in its closed reason vocabulary (it is spec-named and genuinely per-artifact) and recorded in the code that no current run can emit it.
