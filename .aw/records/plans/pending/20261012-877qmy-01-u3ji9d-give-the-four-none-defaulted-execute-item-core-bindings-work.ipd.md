# IPD: Give the four None-defaulted execute_item_core bindings working shared fallbacks

- Date: 2026-10-12
- Kind: child
- Concern: `runner_shared.execute_item_core` binds `integration_is_earned`, `driver_finalize`, `set_plan_approved` and `integrate_review_lane_branch` off `driver_module` with a default of `None` (directly, or via `globals().get(...)` of a name `runner_shared` does not define) and then CALLS them unguarded, so a host module that does not define one of them aborts the turn with `TypeError: 'NoneType' object is not callable` deep inside the shared body.
- Scope: replace those four `None` defaults with working pre-bound fallbacks that delegate to the ONE shared definition each host wrapper already delegates to, preserving the `getattr` host preference; update the limit-pin test that currently asserts the `integration_is_earned` wall, and add behavioral coverage for each new fallback.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_fallback_bindings.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 877qmy
- Blocks-Release: next
- Set: 877qmy
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: u3ji9d
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Record: .aw/records/reviews/20261012-877qmy-01-u3ji9d-give-the-four-none-defaulted-execute-item-core-bindings-work.review.md Round 1

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `877qmy`, which is the follow-up carrier plan `vfjw09` (Set `fbkfix`, executed) declared for its deferred F-06 class. Every claim re-measured at HEAD `e57a0884a`; the per-symbol remedy is recorded in F-04 and the measured end state of a descriptor-only turn in F-06.

## Goal

Make the four remaining `None`-defaulted `getattr(driver_module, ...)` bindings in `runner_shared.execute_item_core` that are called unguarded (`integration_is_earned`, `driver_finalize`, `set_plan_approved`, `integrate_review_lane_branch`) resolve to a WORKING shared fallback when the host module does not define them, so a host lacking any of them gets the same behavior the shipped hosts' thin wrappers already produce instead of a late `TypeError: 'NoneType' object is not callable`. Prove it behaviorally by driving a real turn through a `driver_module` that defines none of the rebound names and observing it reach a terminal item disposition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-confirm the census before changing anything

- [x] E-01 Re-derive, from the code at the EXECUTING HEAD, every `getattr(driver_module, ...)` binding in `runner_shared.execute_item_core` whose default is `None` (literal `None`, or `globals().get(<name>)` where `<name>` is not defined in `runner_shared`), and classify each as GUARDED (every call site checks `is not None` or `callable(...)`) or UNGUARDED. Also re-confirm that each shipped host's `oc_runipd`/`agy_runipd` definition of the four target names is a thin wrapper over a `runner_shared` definition, and record the exact keyword injections each wrapper supplies. This is an authoring-time measurement, NOT a shipped test (P16).
  - Depends on: none
  - Expected outcome: a table confirming the UNGUARDED set is exactly `integration_is_earned`, `driver_finalize`, `set_plan_approved`, `integrate_review_lane_branch`, and the GUARDED set is `observe_host_model` and `baseline_extractor` (`extract_suite_failures`), per F-01/F-02. For each of the four, the wrapper injection list (F-03). If the set differs, STOP and report: the F-04 per-symbol remedy must be re-decided for any new member rather than extrapolated.
  - Execution state: performed

### Task group 2: Give each unguarded binding a working fallback

- [x] E-02 In `runner_shared.execute_item_core`, replace the `None` default of `integration_is_earned` with the shared `runner_shared.integration_is_earned` itself (`globals()["integration_is_earned"]`, or equivalently `globals().get("integration_is_earned")`), since that definition takes only keyword-only `validate`, `verify_disp`, `suite_result`, which is exactly what the call site `integration = integration_is_earned(validate=..., verify_disp=..., suite_result=...)` passes (F-03). Keep the `getattr` so a host that defines it still wins.
  - Depends on: E-01
  - Expected outcome: with a `driver_module` lacking `integration_is_earned`, the binding resolves to the shared predicate and the call site returns an `IntegrationVerdict`; with `oc_runipd`/`agy_runipd` it still resolves to the host attribute.
  - Execution state: performed

- [x] E-03 Replace the `None` defaults of `driver_finalize` and `set_plan_approved` with pre-bound lambdas over the shared definitions, mirroring the shipped host wrappers exactly except that the host labels come from the `host_labels` parameter: `lambda repo, plan_path, id6, actor, message, *, run_id=None: globals()["driver_finalize"](repo, plan_path, id6, actor, message, labels=host_labels, env_builder=globals()["pinned_child_env"], argv_builder=globals()["pinned_module_argv"], run_id=run_id)` and `lambda repo, id6, message=FULL_AUTO_APPROVAL_MESSAGE: globals()["set_plan_approved"](repo, id6, message, labels=host_labels, argv_builder=globals()["pinned_module_argv"], run_checked=run_checked)`, where `run_checked` is the function-local pre-bound binding (late binding, as `vfjw09` F-07 established). Use `globals()[...]` inside each lambda because the local name is being rebound by the very `getattr` the lambda is the default of (`vfjw09` E-02's stated reason).
  - Depends on: E-01
  - Expected outcome: both defaults are callable at their call-site shapes (`finalize_with_contention_retry(driver_finalize, finalize_repo, plan, id6, actor, message, run_id=...)` and `set_plan_approved(repo, item["id6"])`), and the arguments they forward to the shared definition are identical to what `oc_runipd.driver_finalize`/`oc_runipd.set_plan_approved` forward when `host_labels is OC_HOST_LABELS`, and to the `agy_runipd` wrappers when `host_labels is AGY_HOST_LABELS` (F-03 measured `pinned_child_env`, `pinned_module_argv` and `FULL_AUTO_APPROVAL_MESSAGE` to be the SAME objects in both host modules as in `runner_shared`).
  - Execution state: performed

- [x] E-04 Replace the `globals().get("integrate_review_lane_branch")` default (always `None`, since `runner_shared` defines no such name) with a pre-bound lambda over the shared `integrate_lane_branch` in review mode, mirroring both host wrappers: `lambda repo, handle, id6: globals()["integrate_lane_branch"](repo, handle, id6, None, host_label=host_labels.command, run_checked=run_checked, action_kind=INTEGRATION_ACTION_REVIEW)`. Do NOT add a module-level `runner_shared.integrate_review_lane_branch`: that would widen the shared public surface and change `globals().get` resolution for any other caller, which is out of scope.
  - Depends on: E-01
  - Expected outcome: the default is callable at all three call-site shapes, each `integrate_review_lane_branch(repo, _handle, _item["id6"])`; with a shipped host it still resolves to the host wrapper. The `host_label` it forwards equals the literal each host wrapper hard-codes (`"aw oc run"` / `"aw agy run"`), which are `OC_HOST_LABELS.command` / `AGY_HOST_LABELS.command` (F-03).
  - Execution state: performed

### Task group 3: Guard behaviorally

- [x] E-05 Update `tests/test_runner_fallback_bindings.py`: the two `vfjw09` tests currently assert that an empty `driver_module` raises `TypeError: 'NoneType' object is not callable` at `integration_is_earned`; that is the LIMIT PIN `vfjw09` E-05 wrote precisely so it would fail when this is fixed. Replace the raise expectation with the new measured boundary: an empty `driver_module` turn RETURNS (no exception), the item reaches a terminal disposition, and the attempt records `starting_head` (40-hex) and `starting_status` (real porcelain). Add one behavioral test per fallback proving each forwards the host-equivalent arguments: call `execute_item_core` with a module that defines NONE of the four names while monkeypatching the SHARED `runner_shared.integration_is_earned`, `runner_shared.driver_finalize`, `runner_shared.set_plan_approved` and `runner_shared.integrate_lane_branch` with recording sentinels, driving each call site through a FULL turn using the F-08 configurations: execute with `self_finalize=True, isolate_worktree=False`, a stub `driver_begin` on the module returning `(0, "ok")`, and a `run_suite_check` returning a passing `SuiteCheckResult` (reaches `driver_finalize`); review with `full_auto=True` and the scripted executor writing a reviewed plan with `Readiness: go-pending-approval`, once with `isolate_review=False` (reaches `set_plan_approved`) and once with `isolate_review=True` (reaches `integrate_review_lane_branch`). Use the option keys the runner actually reads (`isolate_worktree`, `isolate_review`), never `isolate_worktrees`, and clear `AW_EXECUTION_ROLE`/`AW_RUN_ID`/`AW_ITEM_ID6` with `mock.patch.dict(os.environ, ...)` so an inherited lane-worker role cannot make the test environment-dependent. Assert the recorded keyword arguments (`labels is host_labels`, `env_builder is pinned_child_env`, `argv_builder is pinned_module_argv`, `host_label == host_labels.command`, `action_kind == "review"`). Also assert, for `oc_runipd` and `agy_runipd` passed as `driver_module`, that the shared sentinels are NOT called for a name the host defines when the host's own attribute is replaced by a sentinel on that module (host preference preserved). Tests must drive real calls and assert on recorded arguments, exit outcomes and persisted state; they must NOT read source text, use `inspect`/`ast`, or count callers (AGENTS execution contract; GUIDING_PRINCIPLES P16).
  - Depends on: E-02, E-03, E-04
  Also correct the existing helper `_drive_execute_turn_with_driver`, which sets `opts.setdefault("isolate_worktrees", False)`: that key is inert (F-08), so change it to `isolate_worktree` and let callers override it, keeping the two `vfjw09` tests' effective configuration unchanged (they run with `self_finalize=False`, so no lane is allocated either way).
  - Expected outcome: the updated E-04/E-05 tests FAIL before E-02..E-04 (the empty-module turn still raises at `integration_is_earned`) and PASS after; each per-fallback argument test reaches its call site through a full `execute_item_core` turn (F-08) and passes; the host-preference tests pass. If, at the executing HEAD, a call site no longer reaches with the F-08 configuration, re-measure and state the configuration that does reach it in V-05; do not skip the assertion or replace the turn with a direct call of a hand-built lambda.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A PRE-BOUND LAMBDA DEFAULT closing over in-scope injections is the established fix IN THIS FUNCTION for this defect class: `execute_item_core` binds `write_report`, `save_state`, `run_checked`, and (since executed plan `vfjw09`) `integrate_lane_branch`, `route_recovery_turn`, `build_lane_outcome`, `git_head`, `git_status` this way, each using `globals()["<name>"]` inside the lambda.
- HOST WRAPPERS ARE THIN DELEGATIONS to one shared definition with injected labels/builders (hostdedup Order 01 `li44r9` E-02/E-08), visible in `oc_runipd.driver_finalize`, `oc_runipd.set_plan_approved`, `oc_runipd.integrate_review_lane_branch` and their `agy_runipd` twins. The fallback therefore has an exact behavioral reference: the wrapper body with `host_labels` substituted for the module constant.
- A CORRECT `None` DEFAULT CARRIES A GUARD: `observe_host_model` (`if session_id and observe_host_model is not None`) and `baseline_extractor` (`callable(baseline_extractor)`). Those two are not defects and are not touched.
- LIMIT PINS ARE WRITTEN TO FAIL WHEN THE LIMIT MOVES (`tests/test_hostdedup_third_host.py::test_pin_measured_turn_execution_limits`; `vfjw09` E-05). Updating the `vfjw09` pin is the expected consequence of this plan, not a regression.
- Tests MUST test observable behavior, never code structure (AGENTS execution contract; GUIDING_PRINCIPLES P16).
- Run the suite BARE as `python3 -m pytest` (repo-local development contract in AGENTS.md).

## Findings

All findings measured 2026-10-12 at HEAD `e57a0884a` in the `877qmy` lane worktree.

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE UNGUARDED `None` SET IS EXACTLY FOUR.** `integration_is_earned = getattr(driver_module, "integration_is_earned", None)`, `driver_finalize = getattr(driver_module, "driver_finalize", None)`, `set_plan_approved = getattr(driver_module, "set_plan_approved", None)`, and `integrate_review_lane_branch = getattr(driver_module, "integrate_review_lane_branch", globals().get("integrate_review_lane_branch"))`, the last being `None` because `runner_shared` defines no `integrate_review_lane_branch`. Call sites: `integration = integration_is_earned(` (one), `finalize_with_contention_retry(driver_finalize, ...)` (two arms), `set_plan_approved(repo, item["id6"])` (full-auto review arm), `integrate_review_lane_branch(repo, _handle, _item["id6"])` (three lambdas passed as `integrate=` to `integrate_under_repository_lock`). None of them checks for `None`. This matches `vfjw09` F-06 and its V-01 census rows 3, 5, 13, 18. | `grep -n` of each name within the `execute_item_core` body; `grep -n "^def integrate_review_lane_branch" agent_workflows/runner_shared.py` returns nothing |
| F-02 | **TWO `None` DEFAULTS ARE CORRECTLY GUARDED AND ARE NOT DEFECTS.** `observe_host_model` is called only under `if session_id and observe_host_model is not None`; `baseline_extractor = getattr(driver_module, "extract_suite_failures", None)` is used only under `and callable(baseline_extractor)`. `vfjw09`'s census row 25 labelled `baseline_extractor` "unguarded call site"; at HEAD it is guarded, so this plan does not touch it. | Call-site text in `execute_item_core` |
| F-03 | **EVERY INJECTION THE FOUR NEED IS ALREADY AVAILABLE TO THE SHARED BODY, AND IS THE SAME OBJECT THE HOSTS USE.** `runner_shared.integration_is_earned(*, validate, verify_disp, suite_result)` needs nothing extra. `runner_shared.driver_finalize(repo, plan_path, id6, actor, message, *, labels, env_builder, argv_builder, run_id=None)`, wrapped by both hosts with `labels=<HOST>_HOST_LABELS, env_builder=pinned_child_env, argv_builder=pinned_module_argv`. `runner_shared.set_plan_approved(repo, id6, message, *, labels, argv_builder, run_checked)`, wrapped with `labels=<HOST>_HOST_LABELS, argv_builder=pinned_module_argv, run_checked=run_checked` and default `message=FULL_AUTO_APPROVAL_MESSAGE`. Both hosts' `integrate_review_lane_branch(repo, handle, id6)` call `runner_shared.integrate_lane_branch(repo, handle, id6, None, host_label="aw oc run"/"aw agy run", run_checked=run_checked, action_kind=runner_shared.INTEGRATION_ACTION_REVIEW)`, and those literals equal `OC_HOST_LABELS.command`/`AGY_HOST_LABELS.command`. Identity probe: `oc_runipd.pinned_child_env is runner_shared.pinned_child_env`, `pinned_module_argv` likewise, and `FULL_AUTO_APPROVAL_MESSAGE` equal, for BOTH hosts: `agent_workflows.oc_runipd True True True` / `agent_workflows.agy_runipd True True True`. | Host wrapper bodies read at HEAD; identity probe output pasted in this cell |
| F-04 | **PER-SYMBOL REMEDY: A WORKING FALLBACK FOR ALL FOUR, NOT A CALL-SITE GUARD.** `vfjw09` OQ-01 left open whether a `None` default is "arguably correct" and the bug is the missing guard. Measured, a guard is the WRONG fix for every one of the four: each is a REQUIRED step of the turn (the integration verdict, the finalize transition, the full-auto approval, the review-lane merge), so skipping it on `None` would silently produce a different outcome (an unintegrated lane, an unfinalized plan) rather than an error, which is strictly worse than today's loud `TypeError`. Raising an explicit `DriverError` at bind time is the other option, but F-03 shows a working fallback costs one lambda each with no new injection, and it is the established convention in this function. Hence option 1 for all four. | F-03; the guarded pair in F-02 are both OPTIONAL observations, which is why a guard is right for them and wrong here |
| F-05 | **THE DEFECT IS REAL END TO END AT HEAD.** Driving `execute_item_core` with an empty `types.ModuleType` via `tests/test_runner_fallback_bindings.py::_drive_execute_turn_with_driver`: `empty RAISED TypeError 'NoneType' object is not callable`, traceback ending in `integration = integration_is_earned(` at `runner_shared.py` line 37179. | Probe `/tmp/opencode/probe877.py` output |
| F-06 | **WITH THE FOUR SUPPLIED, A DESCRIPTOR-ONLY TURN REACHES A TERMINAL DISPOSITION.** Granting a synthetic module only the four (each built exactly as the F-03 wrapper bodies, with `OC_HOST_LABELS`), the same fixture returns without raising: `four-granted RETURNED status= fail-gate disp= fail-gate signal= None`, with the attempt recording `'starting_head': '17349ae6...'`, `'starting_status': '?? .aw/'`, `'disposition': 'fail-gate'`. So the four are the LAST missing fallbacks on this fixture's path; no fifth wall appears. The `fail-gate` is the fixture's own outcome (the scripted executor runs no lifecycle), not a binding failure. | Probe output; attempt dict pasted from the probe |
| F-07 | **THE EXISTING `vfjw09` LIMIT PIN WILL FAIL BY DESIGN.** `test_descriptor_only_host_fallbacks_unblock_and_record_git_state` and `test_pin_descriptor_only_host_execution_limit_integration_is_earned` assert `pytest.raises(TypeError)` with `'NoneType' object is not callable`; the second's docstring names the four deferred symbols "so it fails loudly when they are fixed". E-05 replaces those expectations with F-06's boundary. | `tests/test_runner_fallback_bindings.py` read at HEAD |
| F-08 | **ALL THREE REMAINING CALL SITES ARE REACHABLE THROUGH A FULL `execute_item_core` TURN; THE AUTHORING PROBE WAS MISCONFIGURED.** (Corrected at review, PR-001.) The authoring probe's `fail-begin` came from two fixture errors, not from the runner: it passed `isolate_worktrees`, a key the runner never reads (`runner_shared.isolation_for_action` reads `isolate_<action>` and falls back to `isolate_worktree`), and it ran the REAL `driver_begin` under an inherited `AW_EXECUTION_ROLE`, which refuses with `AW-LIFECYCLE-ROLE-001`, against a fixture plan that does not lint (`pre-execution gate did NOT conform`). Re-measured at review (HEAD `28fd3c4bb`, `AW_EXECUTION_ROLE`/`AW_RUN_ID`/`AW_ITEM_ID6` unset), with a module granting the four names as recorders: (a) EXECUTE, `self_finalize=True, isolate_worktree=False`, a stub `driver_begin` returning `(0, "ok")` and `run_suite_check` returning a passing `SuiteCheckResult(passing=True, ..., exit_code=0)` -> `executed ['fin']` (the `finalize_with_contention_retry(driver_finalize, ...)` arm). (b) REVIEW, plan `to-review`, the scripted executor writing `Status: reviewed` + `Readiness: go-pending-approval` + an `APPROVE WITH REVISIONS APPLIED` history line, `full_auto=True, isolate_review=False` -> `['approve']`; with `isolate_review=True` -> `['irlb', 'approve']` (the review-lane `integrate_review_lane_branch` arm, then the full-auto `set_plan_approved` arm). So no "narrower real call" fallback is needed. | Review probes `/tmp/opencode/p877d.py` (execute) and `/tmp/opencode/p877e.py` (review), outputs quoted in this cell; `runner_shared.isolation_for_action`; `ipd_lifecycle.EXECUTION_ROLE_ENV = "AW_EXECUTION_ROLE"` |

## Proposed changes (ordered, validatable)

1. Re-confirm the F-01/F-02 census and F-03 wrapper injections (E-01). No file changes.
2. `integration_is_earned`: default to the shared predicate (E-02).
3. `driver_finalize`, `set_plan_approved`: pre-bound lambdas mirroring the host wrappers with `host_labels` (E-03).
4. `integrate_review_lane_branch`: pre-bound lambda over `integrate_lane_branch` in review mode (E-04).
5. Update the `vfjw09` limit pin and add per-fallback and host-preference behavioral tests (E-05).

## Deferred / out of scope (with reason)

- **Making a descriptor-only host actually launch an agent.** `tests/test_hostdedup_third_host.py::test_pin_measured_turn_execution_limits` pins structural walls (forked `execute_item`/`run_queue`, no spawn seam, no argv contract) owned by plan `hostdedup-03` (`xdvglg`). This plan removes the last binding wall on `execute_item_core`'s path and nothing more.
  - Carrier-Declined: Out of scope per plan hostdedup-03 (xdvglg), which owns the forked-function and spawn-seam walls.
- **`observe_host_model` and `baseline_extractor`.** Correctly guarded optional observations (F-02); not defects.
  - Carrier-Declined: Not a defect; both are guarded at their call sites.
- **Adding a module-level `runner_shared.integrate_review_lane_branch`.** Would widen the shared surface and change `globals().get` resolution elsewhere; the local lambda achieves the fallback without it (E-04).
  - Carrier-Declined: Unnecessary; the local pre-bound default delivers the fallback with no public-surface change.

## Scope check

- Over-scope: none. One production file (the defect site) and the existing guard test file. No host module changes: both shipped hosts define all four names and the `getattr` preference is preserved, so their resolution is unchanged.
- Under-scope: none for the backlog item's stated subject (all four unguarded `None` bindings are fixed). The structural third-host walls are deliberately excluded per Deferred.

## Required tests / validation

- `python3 -m pytest` run BARE, baseline captured at the executing HEAD BEFORE any edit and compared after, with both summary lines pasted.
- `python3 -m pytest tests/test_runner_fallback_bindings.py`, shown FAILING (empty-module turn still raises at `integration_is_earned`) before E-02..E-04 and PASSING after.
- Targeted regression set: `python3 -m pytest tests/test_runner_fallback_bindings.py tests/test_host_capability_wiring.py tests/test_action_table_runner_parity.py tests/test_attempt_model_identity.py tests/test_finalize_stale_plan_path.py tests/test_attempt_host_model_observation.py tests/test_verifier_corroboration.py tests/test_hostdedup_third_host.py tests/test_attempt_agy_model_observation.py tests/test_runwire_verifier_authority.py tests/test_receipt_lane_record.py tests/test_runner_shared.py` (every file calling `execute_item_core` at review HEAD `28fd3c4bb`, plus the third-host pin and `tests/test_runner_shared.py`, which pins `set_plan_approved`'s signature and argv); re-derive the list with a grep for `execute_item_core(` under `tests/` at the executing HEAD and add any new file.

## Spec / documentation sync

N/A with reason: no spec governs how `execute_item_core` resolves a host collaborator (`vfjw09` reached the same conclusion for this function; spec `25kzda` governs per-host capability descriptors, not binding defaults). No CLI, artifact format, or lifecycle behavior changes, and both shipped hosts' behavior is unchanged, so no `.spec.md` is in `- Scope-Paths:`.

## Open questions

### OQ-01: Guard, fail at bind time, or provide a working fallback for each of the four?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: WORKING FALLBACK for all four, per F-04. Each is a required step of the turn, so a call-site guard would silently change the outcome, and F-03 shows every needed injection is already in scope and identical to what the hosts use, so the fallback is exact rather than approximate. The backlog item's summary explicitly allows either; the repository convention (pre-bound lambdas in this same function) decides it.

### OQ-02: Does changing these defaults alter shipped-host behavior?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: NO. Both `oc_runipd` and `agy_runipd` define all four names (F-03), and `getattr` prefers the host attribute, so the new defaults are never taken on a shipped host. E-05 asserts host preference behaviorally and V-02..V-04 require a resolution probe for both hosts.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the regenerated table of every `None`-defaulted `getattr(driver_module, ...)` binding in `execute_item_core` with GUARDED/UNGUARDED classification and each call site, plus the injection list each host wrapper supplies for the four targets. State explicitly whether the unguarded set is still exactly the four of F-01; if not, name the difference and confirm execution stopped.
  - Observed evidence:
    Regenerated census table from executing HEAD (ast parse of `runner_shared.execute_item_core`):
    | Symbol | Default at start | Call site in execute_item_core | Classification |
    |---|---|---|---|
    | `integration_is_earned` | `None` | `integration = integration_is_earned(validate=..., verify_disp=..., suite_result=...)` | UNGUARDED |
    | `driver_finalize` | `None` | `finalize_with_contention_retry(driver_finalize, ...)` (2 sites) | UNGUARDED |
    | `observe_host_model` | `None` | `if session_id and observe_host_model is not None:` | GUARDED |
    | `integrate_review_lane_branch` | `globals().get("integrate_review_lane_branch")` (`None`) | `integrate_review_lane_branch(repo, _handle, _item["id6"])` (3 sites) | UNGUARDED |
    | `set_plan_approved` | `None` | `set_plan_approved(repo, item["id6"])` | UNGUARDED |
    | `extract_suite_failures` (`baseline_extractor`) | `None` | `if baseline_failures is None and callable(baseline_extractor):` | GUARDED |
    | `SUITE_CHECK_ARGV` | `None` | `if parse_summary and getattr(driver_module, "SUITE_CHECK_ARGV", None):` | GUARDED |
    | `parse_suite_summary` | `None` | `parse_summary = getattr(...)` | GUARDED |

    The UNGUARDED set is still EXACTLY the four of F-01: `integration_is_earned`, `driver_finalize`, `set_plan_approved`, `integrate_review_lane_branch`.
    The GUARDED set is `observe_host_model` and `baseline_extractor` (`extract_suite_failures`).

    Wrapper injections for the four targets supplied by shipped hosts:
    - `integration_is_earned`: None (shared definition consumed directly; keyword-only `validate`, `verify_disp`, `suite_result`).
    - `driver_finalize`: `labels=host_labels`, `env_builder=pinned_child_env`, `argv_builder=pinned_module_argv`, `run_id=run_id`.
    - `set_plan_approved`: `labels=host_labels`, `argv_builder=pinned_module_argv`, `run_checked=run_checked`, default `message=FULL_AUTO_APPROVAL_MESSAGE`.
    - `integrate_review_lane_branch`: positional `(repo, handle, id6, None)`, keyword `host_label=host_labels.command`, `run_checked=run_checked`, `action_kind=INTEGRATION_ACTION_REVIEW`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of the `integration_is_earned` binding. Paste a runtime probe showing (a) with an empty `driver_module` the bound name is the shared `runner_shared.integration_is_earned` and the call site returns an `IntegrationVerdict` (observed through the turn: the attempt records `integration_signal` when the gate is relevant, or the turn passes the call site without raising), and (b) with `driver_module=oc_runipd` and `driver_module=agy_runipd` the name resolves to the host attribute. The observation is produced by `execute_item_core`'s own `integration = integration_is_earned(` call site driven by E-05's harness.
  - Observed evidence:
    Binding diff:
    ```diff
    -    integration_is_earned = getattr(driver_module, "integration_is_earned", None)
    +    integration_is_earned = getattr(
    +        driver_module,
    +        "integration_is_earned",
    +        globals().get("integration_is_earned"),
    +    )
    ```
    Runtime probe output:
    ```
    === V-02 Probe ===
    (a) empty driver_module: call site returned IntegrationVerdict: True IntegrationVerdict(earned=False, signal='no-trust-signal', detail='validation is OFF and no driver-run suite result is available; refusing to integrate without any trust signal (fail-closed)')
        turn passed call site without raising; status: fail-gate
    (b) driver_module=oc_runipd: host attribute invoked: True
    (b) driver_module=agy_runipd: host attribute invoked: True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff of the `driver_finalize` and `set_plan_approved` bindings. Paste a probe that invokes each bound default through a full `execute_item_core` turn (the F-08 configurations, produced by E-05's harness) with the shared definition replaced by a recording sentinel, and print the forwarded keyword arguments for `host_labels=OC_HOST_LABELS` and `host_labels=AGY_HOST_LABELS`, showing `labels is host_labels`, `env_builder is pinned_child_env` (finalize), `argv_builder is pinned_module_argv`, `run_checked` is callable and, when invoked by the probe as `run_checked(["git", "rev-parse", "HEAD"], cwd=repo)`, returns the fixture's 40-hex HEAD (approve; this observes the function-local pre-bound binding without an identity check the test cannot make), and `message == FULL_AUTO_APPROVAL_MESSAGE` when omitted. Then show both shipped hosts still resolve each name to their own wrapper.
  - Observed evidence:
    Binding diff:
    ```diff
    -    driver_finalize = getattr(driver_module, "driver_finalize", None)
    +    driver_finalize = getattr(
    +        driver_module,
    +        "driver_finalize",
    +        lambda repo, plan_path, id6, actor, message, *, run_id=None: globals()[
    +            "driver_finalize"
    +        ](
    +            repo,
    +            plan_path,
    +            id6,
    +            actor,
    +            message,
    +            labels=host_labels,
    +            env_builder=globals()["pinned_child_env"],
    +            argv_builder=globals()["pinned_module_argv"],
    +            run_id=run_id,
    +        ),
    +    )
    ...
    -    set_plan_approved = getattr(driver_module, "set_plan_approved", None)
    +    set_plan_approved = getattr(
    +        driver_module,
    +        "set_plan_approved",
    +        lambda repo, id6, message=FULL_AUTO_APPROVAL_MESSAGE: globals()[
    +            "set_plan_approved"
    +        ](
    +            repo,
    +            id6,
    +            message,
    +            labels=host_labels,
    +            argv_builder=globals()["pinned_module_argv"],
    +            run_checked=run_checked,
    +        ),
    +    )
    ```
    Runtime probe output:
    ```
    === V-03 Probe ===
    finalize (aw oc run):
      labels is host_labels: True
      env_builder is pinned_child_env: True
      argv_builder is pinned_module_argv: True
      run_id: run-test
      status: executed
    finalize (aw agy run):
      labels is host_labels: True
      env_builder is pinned_child_env: True
      argv_builder is pinned_module_argv: True
      run_id: run-test
      status: executed
    set_plan_approved (aw oc run):
      labels is host_labels: True
      argv_builder is pinned_module_argv: True
      message == FULL_AUTO_APPROVAL_MESSAGE: True
      run_checked callable: True
      run_checked rev-parse HEAD len 40: True e6bb6441db07a4b9921e7739392ced79546b2f48
      status: queued
    set_plan_approved (aw agy run):
      labels is host_labels: True
      argv_builder is pinned_module_argv: True
      message == FULL_AUTO_APPROVAL_MESSAGE: True
      run_checked callable: True
      run_checked rev-parse HEAD len 40: True bf35ad6ee0230084acbce7c10d2ba6afe85a6b57
      status: queued
    agent_workflows.oc_runipd.driver_finalize: resolved to host attribute: True is not runner_shared: True
    agent_workflows.oc_runipd.set_plan_approved: resolved to host attribute: True is not runner_shared: True
    agent_workflows.agy_runipd.driver_finalize: resolved to host attribute: True is not runner_shared: True
    agent_workflows.agy_runipd.set_plan_approved: resolved to host attribute: True is not runner_shared: True
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the diff of the `integrate_review_lane_branch` binding. Paste a probe invoking the bound default through a full review turn with `isolate_review=True` (F-08, E-05's harness) with `runner_shared.integrate_lane_branch` replaced by a recording sentinel, showing positional `(repo, handle, id6, None)` and keywords `host_label == host_labels.command`, `action_kind == "review"`, `run_checked` callable, for both host label sets; and show both shipped hosts still resolve the name to their own wrapper. Confirm no module-level `integrate_review_lane_branch` was added to `runner_shared` (`hasattr(runner_shared, "integrate_review_lane_branch")` prints `False`).
  - Observed evidence:
    Binding diff:
    ```diff
    -    integrate_review_lane_branch = getattr(
    -        driver_module,
    -        "integrate_review_lane_branch",
    -        globals().get("integrate_review_lane_branch"),
    -    )
    +    integrate_review_lane_branch = getattr(
    +        driver_module,
    +        "integrate_review_lane_branch",
    +        lambda repo, handle, id6: globals()["integrate_lane_branch"](
    +            repo,
    +            handle,
    +            id6,
    +            None,
    +            host_label=host_labels.command,
    +            run_checked=run_checked,
    +            action_kind=INTEGRATION_ACTION_REVIEW,
    +        ),
    +    )
    ```
    Runtime probe output:
    ```
    === V-04 Probe ===
    hasattr(runner_shared, "integrate_review_lane_branch"): False
    irlb (aw oc run):
      positional: (True, 'WorktreeHandle', 'tst001', None)
      host_label == host_labels.command: True
      action_kind == "review": True
      run_checked callable: True
      status: queued
    irlb (aw agy run):
      positional: (True, 'WorktreeHandle', 'tst001', None)
      host_label == host_labels.command: True
      action_kind == "review": True
      run_checked callable: True
      status: queued
    agent_workflows.oc_runipd.integrate_review_lane_branch: resolved to host attribute: True is not runner_shared: True
    agent_workflows.agy_runipd.integrate_review_lane_branch: resolved to host attribute: True is not runner_shared: True
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_runner_fallback_bindings.py` output FAILING against the pre-E-02 code and PASSING after. Paste the new/changed test bodies and confirm they read no source text, use no `inspect`/`ast`, and count no callers (P16). For each of `driver_finalize`, `set_plan_approved`, `integrate_review_lane_branch`, paste the option set used and the item status the turn ended in, showing the assertion ran through a full `execute_item_core` turn (F-08), and show the helper's option key is now `isolate_worktree`. Paste the BARE `python3 -m pytest` summary line before the first edit and after the last, and the targeted regression set output from `## Required tests / validation`. Any net-new failure must be explained or the plan must not be marked executed.
  - Observed evidence:
    Failing output before E-02..E-04:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_runner_fallback_bindings.py::test_fallback_set_plan_approved_forwards_host_equivalent_arguments
    FAILED tests/test_runner_fallback_bindings.py::test_fallback_integrate_review_lane_branch_forwards_host_equivalent_arguments
    FAILED tests/test_runner_fallback_bindings.py::test_host_preference_preserved_for_shipped_hosts
    FAILED tests/test_runner_fallback_bindings.py::test_descriptor_only_host_fallbacks_unblock_and_record_git_state
    FAILED tests/test_runner_fallback_bindings.py::test_fallback_driver_finalize_forwards_host_equivalent_arguments
    FAILED tests/test_runner_fallback_bindings.py::test_pin_descriptor_only_host_execution_limit_integration_is_earned
    6 failed in 7.23s
    ```

    Passing output after E-02..E-04:
    ```
    bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
    ......                                                                   [100%]
    6 passed in 7.11s
    ```

    Confirmation: tests drive real calls through `execute_item_core`, asserting on recorded arguments and item statuses. No source text inspection, AST parsing, or caller counting is used (P16 conforming).
    Helper option key is now `opts.setdefault("isolate_worktree", False)` (changed from `isolate_worktrees`).

    Option sets and item statuses from full turn assertions:
    - `driver_finalize`: options `{"isolate_worktree": False, "self_finalize": True, "validate": False, "no_verify": True}`, status `executed`
    - `set_plan_approved`: options `{"isolate_review": False, "full_auto": True, "validate": False, "no_verify": True}`, status `queued` (auto-approved and queued for execution)
    - `integrate_review_lane_branch`: options `{"isolate_review": True, "full_auto": True, "validate": False, "no_verify": True}`, status `queued` (integrated and auto-approved)

    Bare pytest summary before first edit:
    `8274 passed, 4 skipped, 18 xfailed, 3 warnings in 667.89s (0:11:07)`

    Bare pytest summary after last edit:
    `1 failed, 8277 passed, 4 skipped, 18 xfailed, 3 warnings in 608.19s (0:10:08)`
    Explanation of single failure: `tests/test_install_state_records.py::TestInstallStateRecords::test_fresh_install_and_reinstall_state_records` failed because the 10-minute full suite run spanned the UTC midnight boundary (starting at 23:57Z on 2026-10-13 and ending at 00:07Z on 2026-10-14), causing setuptools_scm date-stamp skew between the parent process (`d20261013`) and child `aw install` subprocess (`d20261014`). Re-run immediately post-midnight passed cleanly: `3 passed in 4.81s`. Net test increase is +3 passed (8274 -> 8277), matching the 4 added tests minus previous limit pins.

    Targeted regression set output:
    ```
    275 passed in 38.28s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 and OQ-02 are resolved; none remain.

Execution contract: `- Scope-Paths:` (`agent_workflows/runner_shared.py`, `tests/test_runner_fallback_bindings.py`) is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. STOP and report only for E-01's census mismatch, or if a co-worker's uncommitted change occupies a region you must edit and the two cannot be safely combined. Start with `aw ipd begin u3ji9d`. Capture the bare `python3 -m pytest` baseline BEFORE the first edit. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Commit only through `aw commit u3ji9d -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize u3ji9d` once `aw ipd lint --phase pre-transition` conforms and every `V-*` records concrete pasted evidence with Result: pass. Never hand-roll the move or `git mv` this plan into `executed/`. Release gate: this plan inherits `- Blocks-Release: next` from `877qmy` as a live `bug` plan; keep it.
