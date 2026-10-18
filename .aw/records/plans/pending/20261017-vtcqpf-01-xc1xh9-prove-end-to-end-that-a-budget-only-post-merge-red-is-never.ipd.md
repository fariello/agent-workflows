# IPD: Prove end to end that a budget-only post-merge red is never reported as combined-red on either host

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `vtcqpf` reports that when the core-tier wall-time budget in the root `conftest.py` is overrun under host load, the post-merge revalidation refuses an all-green merged tree as combined-red and names no failing test, so a verified lane is sent back to its agent for a fix turn with nothing to fix and then refused terminally. The production fix is already split across authored carriers (`44nfmd` names a budget-only red in suite reports; `sa629y` records a budget-only post-merge red as unmeasured so it defers), but no carrier proves the OPERATOR-VISIBLE outcome the backlog item describes on either host: that a budget-only red driven through a host's `execute_item` never fires the combined-red send-back, ends `merge-retry` with a reason naming the budget, and integrates on the deferred re-attempt once the suite is green.
- Scope: One new behavioral test module that drives `oc_runipd.execute_item` and `agy_runipd.execute_item` end to end (real `runner_shared.make_integration_validation_runner`, real merge materialization, real `record_integration_refusal`, real combined-red send-back loop) with only the suite checker and the agent launcher stubbed, plus the deferred re-attempt through each host's `retry_deferred_integrations`, and a measured-red control proving the send-back path still fires for a real failing test. It does NOT edit production code, the 30s budget, the conftest guard, the suite reason text, the send-back wording, or the CHANGELOG (all carried by `44nfmd` and `sa629y`).
- Scope-Paths: tests/test_budget_only_combined_red_e2e.py
- Item-Dependencies: executed:44nfmd, executed:sa629y
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: vtcqpf
- Blocks-Release: next
- Set: vtcqpf
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xc1xh9
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261017-vtcqpf-01-xc1xh9-prove-end-to-end-that-a-budget-only-post-merge-red-is-never.review.md`)
- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog vtcqpf with Step 0 evidence; review-ready.

## Goal

Prove, at the layer the operator actually sees, that the `vtcqpf` symptom cannot recur on either host: a merged tree whose only failure is the core-tier wall-time budget is never refused as combined-red, never costs a fix turn whose prompt says "no test ids recorded", is deferred with a reason that names the budget, and integrates on the next re-attempt once the suite is green, while a genuinely failing merged tree still gets the combined-red send-back.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: fixture and prerequisite check

- [x] E-01 Confirm the prerequisites landed (read-only, no file written). Confirm that plan `sa629y` (backlog `o58dro`) is in `.aw/records/plans/executed/`, that `runner_shared.SuiteCheckResult` carries its budget-only fact (expected name `budget_only`, per `sa629y` E-01), and that `make_integration_validation_runner` does not store a budget-only measurement in the per-run tree cache (`sa629y` E-02, review finding PR-001 of that plan). If the executed design used a different field name or carrier, use THAT and record the name in V-01. If no budget-only fact reaches `SuiteCheckResult` at all, set this item and every later item `blocked` and report that the prerequisite did not ship as designed (do not add one here: production code is outside `- Scope-Paths:`).
  - Depends on: none
  - Expected outcome: the field name to use is recorded, or the plan is blocked with the reason.
  - Execution state: performed

- [x] E-06 Create `tests/test_budget_only_combined_red_e2e.py` (NOT `core`-marked: it drives `execute_item` on git fixtures for two hosts and belongs in the explicit-path and thorough tiers). Add a fixture helper with the shape of `tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests._setup_driver_fixture` (git repo on `main` with `commit.gpgsign false`, `.gitignore` for `.aw/state/`, `.aw/worktrees/`, `.aw/records/runs/`, the plan from `tests.test_oc_runipd._CONFORMING_PLAN` with `Scope-Paths: clash.txt`, a run dir with `outcomes/`, `prompts/`, `sessions/`, options `self_finalize`, `isolate_worktree`, `no_audit`, `no_verify`, `retry_budget: 2`, `on_integration_blocked: "defer"`, and `integration_retry_limit` passed per test), calling `support.declare_execution_role` in `setUp`. Add a fake launcher in the shape of that file's `fake_launcher(state_arg, rd, itm, *args, **kwargs)` that commits `clash.txt` in `kwargs["work_dir"]`, writes the executed outcome JSON, records every call's `kwargs.get("log_suffix")`, and returns session `"ses1"`; patch it on `run_opencode` for `oc_runipd` and on `run_agy_turn` for `agy_runipd`. Add a path-discriminating `run_suite_check` stub patched on the host module, as `tests/test_deferred_reattempt_revalidation.py` discriminates: a call whose path is the primary repo returns a passing `SuiteCheckResult`; a call whose path is under `<run_dir>/revalidation/` returns whatever the test configured through a mutable holder, so a test can switch it between turns. Patch `runner_shared.start_suite_baseline` to return `(None, None)` so no real `aw suite` subprocess launches. Review prototyped exactly this fixture (reusing `DriverHookAndSuiteFixItTests._setup_driver_fixture`) on both hosts (F-5): the real gate, ladder, send-back loop and `retry_deferred_integrations` are all reached.
  - Depends on: E-01
  - Expected outcome: a fixture that runs the REAL `make_integration_validation_runner`, merge materialization, `record_integration_refusal` and combined-red send-back loop, with only the suite verdict and the agent turn scripted.
  - Execution state: performed

### Task group 2: the budget-only outcome on both hosts

- [x] E-02 Add `test_budget_only_red_defers_and_is_never_sent_back` over `oc_runipd` and `agy_runipd` (`subTest` per host). Configure the revalidation result as the budget-only shape: `passing=False`, `exit_code=1`, `failures=()`, `summary="745 passed"`, the budget-only fact True (E-01's field), and a `reason` naming the core-tier wall-time budget. Call `driver_mod.execute_item(run_dir, state, item, recovery=False)` with `integration_retry_limit: 10`. Assert, on observable state only: `item["status"] == runner_shared.INTEGRATION_DEFERRED_STATUS`; `item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY, 0) == 0`; the launcher ran exactly once and never with `log_suffix == "combined-red"`; no `combined-red-sent-back` event in `run_dir / "events.jsonl"`; `item[runner_shared.REVALIDATION_CACHE_KEY]["measured"] is False`; `item["integration_ladder"]["kind"] == runner_shared.INTEGRATION_REFUSAL_UNMEASURED` and `item["integration_ladder"]["deferrable"] is True`; `"budget"` appears in `item["integration_deferral"]` and `"no test ids recorded"` does not. Then switch the revalidation result to passing, call `driver_mod.retry_deferred_integrations(run_dir, state)` WITHOUT touching `state[runner_shared.REVALIDATION_CACHE_KEY]`, and assert that the revalidation stub was called again on the retry (count its calls under `<run_dir>/revalidation/`: at least 2 in total), `item["status"] == "executed"`, that `git log main --name-only` in the fixture repo lists `clash.txt`, and that the launcher call count is still 1 (the verified lane integrated without another agent turn). The re-measure assertion is load-bearing: the per-run revalidation cache is keyed on the merged tree, an unchanged main rebuilds the same tree, and review measured (F-6) that a cached unmeasured reading is served on the retry so the item stays `merge-retry`; only `sa629y`'s cache exclusion lets the retry integrate. Do NOT clear the cache in the test to make it pass, and do NOT assert on stderr text: the execute-path console line still prints the gate's raw combined-red reason for an unmeasured refusal (F-7, filed as backlog `geajrj`).
  - Depends on: E-06
  - Expected outcome: both host variants pass; the vtcqpf symptom (combined-red, empty ids, fix turn) is absent and the work integrates on re-attempt.
  - Execution state: performed

- [x] E-03 Add `test_budget_only_red_exhausted_budget_does_not_claim_a_red_suite` over both hosts: the same budget-only revalidation result with `integration_retry_limit: 0`, so the first refusal is terminal. Assert `item["status"] == runner_shared.INTEGRATION_BLOCKED_STATUS`, `item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY, 0) == 0`, the launcher ran once, and `item["integration_ladder"]["verdict"]` does not contain `"it was RED"` (the combined-red sentence of `runner_shared.terminal_refusal_verdict`, "the post-merge revalidation MEASURED the merged tree and it was RED") while it does contain `"could not MEASURE"` (the unmeasured wording of `runner_shared.decide_integration_deferral`), so even the terminal report does not assert a failing suite that never failed.
  - Depends on: E-06
  - Expected outcome: both host variants pass; an exhausted budget-only refusal is terminal but honestly worded.
  - Execution state: performed

### Task group 3: control and run

- [x] E-04 Add the control `test_measured_red_with_failing_id_is_still_sent_back` over both hosts, proving the fixture really reaches the send-back loop so E-02's absence-of-send-back assertion is not vacuous: the first revalidation result is a real red (`passing=False`, `exit_code=1`, `failures=("FAILED tests/test_foo.py::test_failing_case - boom",)`, budget-only fact False); the launcher's `combined-red` call commits a fix and switches the revalidation result to passing for the next measurement. Assert `item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY) == 1`, a `combined-red-sent-back` event exists, the prompt file delivered on the combined-red call contains `tests/test_foo.py::test_failing_case`, and `item["status"] == "executed"`. Read the prompt path the way `tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests.test_v03_e03_combined_red_sendback_and_warning_on_out_of_scope` does (`args[1]` for `oc_runipd`, `args[0]` for `agy_runipd`).
  - Depends on: E-06
  - Expected outcome: both host variants pass, so the module demonstrably distinguishes a budget-only red from a measured red.
  - Execution state: performed

- [x] E-05 Run the new module explicitly (`python3 -m pytest -o addopts="" -v tests/test_budget_only_combined_red_e2e.py`), the neighbouring contracts unchanged (`python3 -m pytest tests/test_hook_and_suite_fix_it.py tests/test_deferred_reattempt_revalidation.py`), the bare core tier `python3 -m pytest`, and `aw sanitize --agent`. If an E-02 or E-03 assertion fails because the runner really does send back or mislabel a budget-only red, do NOT weaken the test and do NOT edit production code under this plan: set the failing item `blocked`, paste the failing output, and report it as a live regression of `o58dro`/`vtcqpf` needing a corrective plan.
  - Depends on: E-02, E-03, E-04, E-06
  - Expected outcome: every test in the new module passes for both hosts; existing modules pass unchanged; core tier green; sanitizer pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The budget guard is the root `conftest.pytest_sessionfinish` (docstring "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)"): on overrun with `cpu_count >= 12` and `AW_CORE_BUDGET_ENFORCE != "0"` it writes `CORE TIER BUDGET EXCEEDED` to stderr and sets `session.exitstatus = 1`, printing no `FAILED` line, so the run reads "N passed" and exits 1.
- `suite_cache.build_suite_child_env` carries the `ytz6z4` demotion (`base.setdefault(AW_CORE_BUDGET_ENFORCE_ENV, "0")`, commit `8b798b0b8`), so a default runner-launched suite does not enforce the budget; an explicit `AW_CORE_BUDGET_ENFORCE=1` still enforces (`tests/test_core_tier_selection.py::test_gate_suite_honors_explicit_enforce`).
- Today a budget-only red reaching `runner_shared.make_integration_validation_runner` is recorded `measured=True` with empty `failures`; `runner_shared.new_failures_since_baseline` then answers `REVALIDATION_UNKNOWN` ("the merged suite did NOT pass yet reported NO failing ids"), the gate `orchestrate_isolation.execute_merge_and_revalidate_gate` refuses with `integration_failed_combined_red`, and the send-back loop beside the `combined-red-sent-back` event builds `fail_lines = ... else "no test ids recorded"`.
- That send-back loop is guarded by `and not revalidation_was_unmeasured(item)`, and `runner_shared.record_integration_refusal` reclassifies a `fail-merge` refusal whose record is unmeasured to `INTEGRATION_REFUSAL_UNMEASURED` (`merge-unchecked`), embedding the record's `reason` in `item["integration_deferral"]`; `decide_integration_deferral` defers it while `integration_retry_limit` lasts and, once exhausted, says "the gate still could not MEASURE the merge result".
- Both hosts reach this through `runner_shared.execute_item_core`, which resolves `make_integration_validation_runner` and `run_suite_check` off the host module (`getattr(driver_module, "run_suite_check", run_suite_check)`), so patching the host module's `run_suite_check` reaches both the primary-checkout suite check and the revalidation call; the deferred re-attempt is `<host>.retry_deferred_integrations`, which delegates to `runner_shared.retry_deferred_integrations` and rebuilds the validation runner on the live item.
- Existing tests to copy shapes from: `tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests` (fixture, launcher patch targets; its `test_v03_e03_unmeasured_revalidation_negative_not_sent_back` stubs the whole runner factory and so does NOT exercise the real classification) and `tests/test_deferred_reattempt_revalidation.py` (path-discriminating suite stub, `retry_deferred_integrations`).
- Tests must assert observable behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); this module calls `execute_item` and `retry_deferred_integrations` and asserts on item state, events, prompts and git history, never on source text.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | `vtcqpf` is one of five filings of the same defect, filed during run item `tgfxin` before the runner-side demotion landed | commit `7cfc74e80` (file `vtcqpf`, 2026-10-16 20:45) precedes `8b798b0b8` (ytz6z4 demotion, 21:20); siblings `ytz6z4` (done), `48hjbx` (graduated to `44nfmd`), `m8d13e` (graduated to `t54fet`), `o58dro` (graduated to `sa629y` on its lane) |
| F-2 | The production fixes are already designed and must not be written a third time | `44nfmd` (budget-only `reason` in `suite_cache.run_full_suite`, send-back wording, load-aware guard); `sa629y` (`SuiteCheckResult.budget_only`, budget-only red recorded `measured=False` so it routes to `merge-unchecked`); both edit `agent_workflows/runner_shared.py` |
| F-3 | No carrier proves the operator-visible outcome `vtcqpf` describes on the host entry points: `sa629y` tests the factory and `record_integration_refusal` in isolation, `t54fet` tests the seams under the DEFAULT demotion (where no budget-only red arises), and the existing unmeasured send-back test stubs the whole validation-runner factory | `sa629y` E-04/E-05; `t54fet` E-02..E-04; `tests/test_hook_and_suite_fix_it.py::test_v03_e03_unmeasured_revalidation_negative_not_sent_back` patches `make_integration_validation_runner` |
| F-4 | (SUPERSEDED at review) At authoring, `sa629y` existed only on a lane branch, so `executed:sa629y` linted as dangling. It is now on `main` (integrated by `4af5e66b1`, `- Status: reviewed`), and `aw ipd lint --phase review-finalize` with `- Item-Dependencies: executed:44nfmd, executed:sa629y` is `clean` with no dependency finding; `aw check all` raises none for this plan either | review run at HEAD `4af5e66b1` |
| F-5 | (review) A prototype of E-06's fixture on both hosts (`_setup_driver_fixture`, path-discriminating `run_suite_check`, `start_suite_baseline` patched, launcher on `run_opencode`/`run_agy_turn`) with an UNMEASURED stand-in revalidation (the suite stub raised, since `budget_only` does not exist yet): `limit 10` -> `merge-retry`, ladder `merge-unchecked`, `deferrable True`, `measured False`, combined-red count 0, launcher called once with no `combined-red` suffix; `limit 0` -> `fail-merge`, verdict contains `could not MEASURE` and not `it was RED`; measured red with a failing id -> combined-red count 1, launcher suffixes `['', 'combined-red']`, `executed`, `clash.txt` on main. So E-02 to E-04 are reachable and their assertions hold for the unmeasured path today. | scratch pytest module under gitignored `tmp/`, `7 passed`; removed after |
| F-6 | (review) In that prototype the deferred re-attempt did NOT integrate: after switching the stub to green, `retry_deferred_integrations` left the item `merge-retry` and `clash.txt` absent from main on both hosts, because the cached unmeasured reading for the unchanged merged tree was served; clearing `state["post_merge_revalidation"]` before the retry made both hosts integrate (`executed`, landed). `sa629y` (reviewed) now excludes a budget-only measurement from that cache, which is what makes E-02's re-attempt half pass. | same prototype, `CLEAR=0` vs `CLEAR=1` |
| F-7 | (review) The operator's stderr line on the first attempt reads `NOT integrated to main (merge-retry): ... integration gate did not pass (integration_failed_combined_red) ... (per-lane-green + combined-red)` even though the recorded ladder is `merge-unchecked`, because `runner_shared.execute_item_core` prints the raw gate `integ_reason` rather than the reclassified one. Out of this plan's test-only scope; filed as backlog `geajrj` (bug, `Blocks-Release: next`). | prototype stderr; `execute_item_core` "finalized on lane {lane_branch} but NOT " print |

## Proposed changes (ordered, validatable)

1. E-01: confirm the prerequisite fact and cache exclusion exist. E-06: build the host-level fixture with only the suite verdict and agent turn scripted.
2. E-02 and E-03: the budget-only outcome on both hosts, deferral plus re-attempt, and an honest terminal verdict on an exhausted budget.
3. E-04: measured-red control proving the send-back path is reachable in the fixture.
4. E-05: run the module, neighbours, core tier, and sanitizer.

## Deferred / out of scope (with reason)

- Classifying a budget-only post-merge red as unmeasured, and excluding it from the revalidation cache so a re-attempt re-measures (the production fix of this defect): designed in `sa629y`, graduated from the duplicate backlog item `o58dro`.
  - Carrier: sa629y
  - Carrier-Evidence: .aw/records/plans/executed/20261017-o58dro-01-sa629y-budget-only-post-merge-red-defers-as-unmeasured.ipd.md
- The execute-path console line printing the raw combined-red gate reason for a refusal recorded as `merge-unchecked` (F-7): a production change outside this test-only plan.
  - Carrier: geajrj
- Naming a budget-only red in the suite `reason`, replacing "no test ids recorded" in the send-back text, and the load-aware conftest guard: designed in `44nfmd`.
  - Carrier: 44nfmd
  - Carrier-Evidence: .aw/records/plans/executed/20261017-48hjbx-01-44nfmd-make-the-core-tier-wall-time-budget-load-aware-and-name-a-bu.ipd.md
- Seam regression tests under the default demotion: designed in `t54fet`.
  - Carrier: t54fet
  - Carrier-Evidence: .aw/records/plans/executed/20261017-m8d13e-01-t54fet-prove-every-runner-revalidation-seam-reports-an-all-green-ov.ipd.md

## Scope check

- Over-scope: none; one new test module, no production edit.
- Under-scope: none; both hosts, deferral, re-attempt (with a real re-measure), exhausted-budget wording, and a non-vacuity control are covered, and every production surface is carried by `sa629y`, `44nfmd` or `geajrj`.

## Required tests / validation

- New `tests/test_budget_only_combined_red_e2e.py` (E-02 to E-04, each over both hosts); unchanged `tests/test_hook_and_suite_fix_it.py` and `tests/test_deferred_reattempt_revalidation.py`; the bare core tier `python3 -m pytest`; `aw sanitize --agent`. Actual runner output must be pasted in each `V-*`.

## Spec / documentation sync

- N/A: this plan adds tests only and changes no behavior a spec or user document describes; the CHANGELOG lines for the behavior change belong to `44nfmd` and `sa629y`. No spec file is touched, so none is listed in Scope-Paths.

## Open questions

### OQ-01: Gate on `state:backlog:done:o58dro` or on `executed:sa629y`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `executed:sa629y`. The authoring-time reason for the backlog proxy (the edge linted as dangling) no longer holds: `sa629y` is on `main` and the edge lints clean (F-4). The direct edge is also more precise: `o58dro` reaching `done` is a separate human or runner act after `sa629y` executes (a graduated item does not auto-close), so the proxy could hold this plan back after its real prerequisite shipped, or depend on an unrelated close. E-01 still re-checks that `sa629y` shipped the field and the cache exclusion before any test is written.

### OQ-02: Should this graduation write the fix itself instead of tests?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The fix is already designed in `sa629y` and `44nfmd`, both in `agent_workflows/runner_shared.py` (F-2); a third production change would collide with them and duplicate their detector. What no carrier covers is proof of the user-visible outcome at the host entry points (F-3), so that is this plan's whole scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `ls .aw/records/plans/executed/ | grep sa629y` output and `rg -n "budget_only" agent_workflows/runner_shared.py` output showing the field on `SuiteCheckResult` and the cache guard in `make_integration_validation_runner` (or the substitute name recorded).
  - Observed evidence:
    `ls .aw/records/plans/executed/ | grep sa629y`:
    ```
    20261017-o58dro-01-sa629y-budget-only-post-merge-red-defers-as-unmeasured.ipd.md
    ```
    `rg -n "budget_only" agent_workflows/runner_shared.py`:
    ```
    30416:        budget_only_red = False
    30453:                and bool(getattr(result, "budget_only", False))
    30460:                budget_only_red = True
    30494:        if isinstance(cache, dict) and tree_id and not budget_only_red:
    47144:    budget_only: bool = False
    47232:    budget_only = False
    47234:        budget_only = bool(
    47235:            suite_cache.is_budget_only_failure(
    47252:        budget_only=budget_only,
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_budget_only_combined_red_e2e.py -k budget_only_red_defers` showing PASSED (both host subtests), and the test body's re-measure assertion on the revalidation stub's call count (code paths: `<host>.execute_item` -> `runner_shared.execute_item_core` -> `make_integration_validation_runner` -> `record_integration_refusal`; then `<host>.retry_deferred_integrations`).
  - Observed evidence:
    ```
    tests/test_budget_only_combined_red_e2e.py::TestBudgetOnlyCombinedRedE2E::test_budget_only_red_defers_and_is_never_sent_back PASSED [100%]

    NOTE: 2 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 1 passed, 2 deselected in 6.93s ========================
    ```
    Re-measure assertion on the revalidation stub's call count from test body:
    ```python
    self.assertGreaterEqual(len(reval_calls), 2)
    self.assertEqual(item["status"], "executed")
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted output of the same command with `-k exhausted_budget` showing PASSED for both hosts (code path: `runner_shared.decide_integration_deferral` exhausted branch via `record_integration_refusal`).
  - Observed evidence:
    ```
    tests/test_budget_only_combined_red_e2e.py::TestBudgetOnlyCombinedRedE2E::test_budget_only_red_exhausted_budget_does_not_claim_a_red_suite PASSED [100%]

    NOTE: 2 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 1 passed, 2 deselected in 6.11s ========================
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted output of the same command with `-k measured_red` showing PASSED for both hosts (code path: the combined-red send-back loop in `runner_shared.execute_item_core` that emits `combined-red-sent-back`).
  - Observed evidence:
    ```
    tests/test_budget_only_combined_red_e2e.py::TestBudgetOnlyCombinedRedE2E::test_measured_red_with_failing_id_is_still_sent_back PASSED [100%]

    NOTE: 2 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 1 passed, 2 deselected in 24.82s =======================
    ```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted tail of the full new-module run with its `passed` line and zero failed; pasted tail of `python3 -m pytest tests/test_hook_and_suite_fix_it.py tests/test_deferred_reattempt_revalidation.py` (N passed, zero failed); pasted tail of bare `python3 -m pytest` (N passed, zero failed); the `aw sanitize --agent` result record with status pass.
  - Observed evidence:
    Pasted tail of `python3 -m pytest -o addopts="" -v tests/test_budget_only_combined_red_e2e.py`:
    ```
    tests/test_budget_only_combined_red_e2e.py::TestBudgetOnlyCombinedRedE2E::test_budget_only_red_exhausted_budget_does_not_claim_a_red_suite PASSED [ 33%]
    tests/test_budget_only_combined_red_e2e.py::TestBudgetOnlyCombinedRedE2E::test_measured_red_with_failing_id_is_still_sent_back PASSED [ 66%]
    tests/test_budget_only_combined_red_e2e.py::TestBudgetOnlyCombinedRedE2E::test_budget_only_red_defers_and_is_never_sent_back PASSED [100%]
    ============================== 3 passed in 12.63s ==============================
    ```
    Pasted tail of `python3 -m pytest tests/test_hook_and_suite_fix_it.py tests/test_deferred_reattempt_revalidation.py`:
    ```
    ............                                                             [100%]
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    12 passed in 14.89s
    ```
    Pasted tail of bare `python3 -m pytest`:
    ```
    ............................................................             [100%]
    NOTE: 8349 tests were deselected by core filter/-m/-k and did not run (default bare run selects 'core' and marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    1213 passed in 31.33s
    ```
    Pasted `aw sanitize --agent`:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5907,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: pasted `git diff --stat` showing `tests/test_budget_only_combined_red_e2e.py` as the only changed path, and pasted `grep -n "start_suite_baseline\|run_opencode\|run_agy_turn\|revalidation" tests/test_budget_only_combined_red_e2e.py` showing the baseline patch, both launcher patch targets and the path-discriminating stub; `grep -c "pytest.mark.core"` on the module returning 0.
  - Observed evidence:
    `git diff --stat`:
    ```
     tests/test_budget_only_combined_red_e2e.py | 467 +++++++++++++++++++++++++++++
     1 file changed, 467 insertions(+)
    ```
    `grep -n "start_suite_baseline\|run_opencode\|run_agy_turn\|revalidation" tests/test_budget_only_combined_red_e2e.py`:
    ```
    4:- Proves a budget-only post-merge revalidation red defers as unmeasured and is never sent back
    154:                    reval_dir = run_dir / "revalidation"
    194:                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
    202:                    runner_shared, "start_suite_baseline", return_value=(None, None)
    237:                # Switch revalidation to passing and retry without clearing the cache
    245:                    runner_shared, "start_suite_baseline", return_value=(None, None)
    281:                    reval_dir = run_dir / "revalidation"
    320:                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
    328:                    runner_shared, "start_suite_baseline", return_value=(None, None)
    370:                    reval_dir = run_dir / "revalidation"
    427:                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
    435:                    runner_shared, "start_suite_baseline", return_value=(None, None)
    ```
    `grep -c "pytest.mark.core" tests/test_budget_only_combined_red_e2e.py`:
    ```
    0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`) and after `44nfmd` and `sa629y` are executed (`- Item-Dependencies: executed:44nfmd, executed:sa629y`). Execution contract:

- Open questions: OQ-01 and OQ-02 are resolved; nothing blocks execution.
- Scope fence: `- Scope-Paths:` declares the one file this plan edits. An edit outside it is made and then justified with `--scope-reason` at finalize; but a failing E-02/E-03 outcome assertion is a live regression to report (E-05), never a reason to edit production code here.
- Honesty: paste ACTUAL runner output in each `V-*`; never claim a pass you did not run.
- Commits: path-scoped via `aw commit xc1xh9 -- tests/test_budget_only_combined_red_e2e.py`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. Executed by hand (`aw work begin xc1xh9`), finish with `aw ipd finalize xc1xh9 --actor <agent/model> --message <summary> --apply` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan to `executed/`.
