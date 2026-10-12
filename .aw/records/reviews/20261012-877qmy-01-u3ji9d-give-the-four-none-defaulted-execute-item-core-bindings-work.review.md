# Review findings: plan u3ji9d

- Subject-Id: u3ji9d
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `28fd3c4bb` in an isolated review lane. The plan was committed and unchanged (`0ffc4e4d9`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was re-run after revisions.

Re-verified:
- F-01 census by a probe over the `getattr(driver_module, ...)` bindings in `execute_item_core`: `None` defaults are exactly `integration_is_earned`, `driver_finalize`, `observe_host_model`, `set_plan_approved`, plus `integrate_review_lane_branch` via `globals().get` of an undefined name. Both hosts define all four targets.
- F-02: `observe_host_model` is called under `if session_id and observe_host_model is not None`; `baseline_extractor` is used under `and callable(baseline_extractor)`.
- F-03: host wrapper bodies of `driver_finalize`, `set_plan_approved` and `integrate_review_lane_branch` in `oc_runipd` and `agy_runipd` match the plan's lambdas exactly. `oc_runipd.integration_is_earned is runner_shared.integration_is_earned` (and agy) is `True`. `OC_HOST_LABELS.command == "aw oc run"`, `AGY_HOST_LABELS.command == "aw agy run"`.
- Shared signatures: `integration_is_earned(*, validate, verify_disp, suite_result)`, `driver_finalize(..., *, labels, env_builder, argv_builder, run_id=None)`, `set_plan_approved(repo, id6, message, *, labels, argv_builder, run_checked)`. `_call_driver_finalize` calls `driver_finalize_fn(repo, plan_path, id6, actor, message, run_id=run_id)`, which the E-03 lambda accepts.
- `run_checked` is a function-local `getattr` binding with a pre-bound lambda default; the E-03/E-04 lambdas close over it late, so ordering is safe.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Evidence / E. Testing | `runner_shared.isolation_for_action` (reads `isolate_<action>`, falls back to `isolate_worktree`); `ipd_lifecycle.EXECUTION_ROLE_ENV = "AW_EXECUTION_ROLE"`; `tests/test_runner_fallback_bindings.py` `_drive_execute_turn_with_driver` `opts.setdefault("isolate_worktrees", False)` | F-08 said the `driver_finalize`, `set_plan_approved` and `integrate_review_lane_branch` call sites are unreachable from the fixture, and E-05/V-03/V-05 accepted an undefined "narrower real call" substitute. The claim came from a misconfigured probe: `isolate_worktrees` is never read, and the real `driver_begin` refused under an inherited `AW_EXECUTION_ROLE` against a non-linting fixture plan. Re-measured at review, all three are reached through full turns (execute `self_finalize=True, isolate_worktree=False` with stub `driver_begin` and passing `SuiteCheckResult` -> `executed ['fin']`; review `full_auto=True` -> `['approve']`, with `isolate_review=True` -> `['irlb', 'approve']`). A weaker substitute would have tested the lambda and not the binding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 rewritten with the measured configurations. E-05 now drives every call site through a full turn with those configurations, uses the real option keys, clears the role env, and fixes the helper's inert key. V-03/V-04/V-05 demand the full-turn evidence. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (evidence feasibility) | V-03 original "`run_checked` is the function-local pre-bound callable" | The function-local binding cannot be identity-compared from outside the function, so this demand was unsatisfiable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now demands `run_checked` is callable and returns the fixture's 40-hex HEAD for `git rev-parse HEAD`, which observes the binding behaviourally. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Regression set | `grep -rln "execute_item_core(" tests/` at `28fd3c4bb` | The targeted set omitted `tests/test_attempt_agy_model_observation.py`, `tests/test_runwire_verifier_authority.py` and `tests/test_receipt_lane_record.py`, which call `execute_item_core`, and `tests/test_runner_shared.py`, which pins `set_plan_approved`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all four; re-derivation at execution HEAD kept. |
| PR-004 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate said "honor Scope-Paths exactly" (a fence, contrary to the declaration rule), and lacked the OQ status, `aw ipd begin`, the staged-set check, the MUST-paste rule, and conditional finalize ownership. It also restated that Readiness is absent, which this review now writes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with every element; the E-01 STOP is kept as the one genuine stop. |
| PR-005 | LOW | IN-SCOPE | Open questions | OQ-01/OQ-02 `- Owner: none` | Resolved questions named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to `plan author` (the author resolved them from evidence). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Must every fallback be proven through a full `execute_item_core` turn? | Yes, using the F-08 configurations measured at review | Allow a "narrower real call" of a hand-built lambda (tests a copy, not the binding) | Review probes `p877d.py` / `p877e.py` reached all three call sites | yes |
| D-2 | May E-05 edit the shared helper's `isolate_worktrees` key? | Yes, to `isolate_worktree` | Leave it inert (misleads every future caller, as it misled F-08) | `runner_shared.isolation_for_action`; the file is already in Scope-Paths | yes |
