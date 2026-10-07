# Review: Make the execute_item_core driver_module fallbacks either work or fail at bind time

- Subject-Id: vfjw09
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `bc5b6b18e` in the sweep lane. The plan was committed and unchanged against its sealed lane input, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before and after the edits.

Re-measured (an authoring-style AST census in a review probe; not a shipped test):

- 25 `getattr(driver_module, ...)` rebindings. The broken set is still exactly `route_recovery_turn` (save_state), `integrate_lane_branch` (host_label, run_checked, action_kind), `build_lane_outcome` (run_checked), `git_head` and `git_status` (run_checked).
- `acquire_review_sweep_lane` is defined by neither host and needs `save_state`, which its call site passes, so F-04 holds. The `None` defaults are `integration_is_earned`, `driver_finalize`, `set_plan_approved`, `observe_host_model` and `extract_suite_failures`; `integrate_review_lane_branch` is absent from `runner_shared`.
- Driving a turn through the `_drive_execute_turn` shape: with `oc_runipd` it reaches `fail-gate`. With an empty module it raises `TypeError: route_recovery_turn() missing 1 required keyword-only argument: 'save_state'`. With the five fixes granted it raises `TypeError: 'NoneType' object is not callable` at `integration = integration_is_earned(`, and the persisted item is left `status=running`, no disposition, `starting_head` set and `starting_status='?? .aw/'`.
- Both host wrappers' `integrate_lane_branch` signatures are `(repo, handle, id6, validation_runner)`.
- Both `build_lane_outcome` call sites guard on `DriverError`, so F-03 holds.
- `execute_item_core(` calls in `tests/` omitting `driver_module`: two (`test_action_table_runner_parity.py:440`, `test_host_capability_wiring.py:92`), not three. `tests/test_verifier_corroboration.py` is a new caller; `tests/test_hostdedup_third_host.py` makes none.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | Testing (E) / reachability | `agent_workflows/runner_shared.py:35304` `integration = integration_is_earned(`; probe above | E-04 required the descriptor-only turn to "reach a terminal item status". Measured, it cannot: after the five fixes the turn raises at `integration_is_earned` and leaves the item `running`. That is the wall E-05 itself pins, so E-04 and E-05 contradicted each other and E-04 was unsatisfiable. The named harness also hard-codes `driver_module=oc_runipd` in a file outside Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now asserts the observed `starting_head`/`starting_status` inside `pytest.raises(TypeError)`, with no terminal status, and reuses `_setup_test_repo` or a local copy of the harness. E-05 identifies the wall by outcome, not by traceback source text (P16). V-04 and V-05 were updated to match. |
| PR-402 | LOW | IN-SCOPE | Evidence accuracy | AST walk of `tests/` | F-10, F-11 and the validation text said three call sites omit `driver_module`; there are two. | all Low | FIXED | Corrected the counts and made them re-derived. |
| PR-403 | LOW | IN-SCOPE | Regression set | as above | `test_verifier_corroboration.py` (a new caller) was missing, and `test_hostdedup_third_host.py` was wrongly described as an `execute_item_core` caller. | all Low | FIXED | Added the file and corrected the description. |
| PR-404 | MEDIUM | IN-SCOPE | Correctness (A) | `oc_runipd.integrate_lane_branch`/`agy_runipd.integrate_lane_branch` are both 4-positional; `_publish` closure | E-03's outcome said `_publish` should call "with the full keyword set", but both host wrappers reject those keywords, so following it literally breaks integration on BOTH shipped hosts. The premise that the hosts take the second branch was also wrong: both take the first. | C:Low; U:Low; S:Low; F:Med; Overall:Medium | FIXED | E-03 now keeps the 4-positional shape and records the measured first-branch fact for re-confirmation by call. |
| PR-405 | LOW | IN-SCOPE | Executability | the working lambdas use `globals()["..."]` | E-02 gave no shape for the `integrate_lane_branch` default and did not warn that a bare name inside the lambda resolves to the rebound local and recurses. The shim also passes the bare shared `run_checked`, not the pre-bound one. | all Low | FIXED | Spelled out the lambda shape, the `globals()` rule and the `run_checked` difference. V-02 now checks agy as well. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should E-04 assert, given that the turn cannot terminate? | Observed `starting_head`/`starting_status` inside `pytest.raises(TypeError)` | Fix the `None` defaults too so the turn terminates (scope creep that contradicts OQ-01); assert a terminal status (unreachable) | probe above; plan OQ-01 | yes |
| D-2 | Which `_publish` call shape should remain after E-03? | 4-positional | Full keyword set (rejected by both host wrappers) | wrapper signatures measured | yes |
