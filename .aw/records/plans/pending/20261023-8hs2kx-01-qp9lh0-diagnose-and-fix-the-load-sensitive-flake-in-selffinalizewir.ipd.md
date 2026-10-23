# IPD: Diagnose and fix the load-sensitive flake in SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success

- Date: 2026-10-23
- Kind: child
- Concern: `tests/test_oc_runipd.py::SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success` failed once (`1 failed, 385 passed in 446.09s`) during a 7-module related-modules run recorded in executed plan `h8peam` V-05, then passed on three reruns (alone, whole file, whole class). Only the `FAILED` node line was preserved, not the assertion or traceback, so the failure mode and cause are unknown. A test that fails intermittently on the merge-gate path erodes trust in the suite and can spuriously refuse a runner integration.
- Scope: Reproduce the failure under load and capture its full traceback; make the test's ordering assertion self-diagnosing so any future failure records WHY `run_opencode` was not reached; fix the root cause if the reproduction identifies one. Edits are confined to `tests/test_oc_runipd.py` unless the reproduction proves a production defect (see Scope check).
- Scope-Paths: tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 8hs2kx
- Set: 8hs2kx
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: qp9lh0

## Workflow history

- 2026-10-23 draft (opencode): created.
- 2026-10-23 to-review (opencode): authored from backlog 8hs2kx with findings, checklist, and validation.

## Goal

Turn an unexplained one-off failure into either a fixed root cause or, if it cannot be reproduced within a bounded effort, a test whose failure message alone is enough to diagnose the next occurrence. Non-goals: no retry/rerun plugin, no `skip`/`xfail`/quarantine marker, no loosening of the asserted ordering property (begin before run), and no change to sibling tests in `SelfFinalizeWiringTests`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reproduce and make the failure self-diagnosing

- [ ] E-01 Attempt a bounded reproduction under load and capture the full failure output. Run the same 7-module set `h8peam` E-05 ran (`tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py`) with the default `addopts` (xdist + pytest-randomly) and `-p randomly --randomly-seed=<n>` for at least 5 distinct seeds, plus at least 50 isolated iterations of the single node in a shell loop while that module set runs concurrently in a second process to supply load. Record every seed and outcome, and for any failure save the complete assertion message and traceback (`-o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` keeps the summary line visible).
  - Depends on: none
  - Expected outcome: a table of attempts (seed, command, result) and either the captured traceback of at least one reproduction or an explicit "not reproduced in N attempts" statement.
  - Execution state: pending

- [ ] E-02 In `tests/test_oc_runipd.py` `SelfFinalizeWiringTests.test_begin_precedes_run_opencode_on_success`, replace the bare `self.assertEqual(order[:2], ["begin", "run"])` with the same equality assertion carrying a `msg=` that reports the observed `order` list, `item["status"]`, the last attempt's `disposition`, and any refusal/gate field present on the item (`begin_refusal`, `clean_base_refusal`, `scope_target_refusal`, `refusal`, `worktree_error`). The asserted property is unchanged; only the failure message gains the state that explains which gate in `runner_shared.execute_item_core` stopped the turn before `run_opencode`.
  - Depends on: E-01
  - Expected outcome: the test still passes, and a deliberately injected refusal (for example a temporary local patch making the patched `driver_begin` return `(1, "x")`, NOT committed) produces a failure message naming the status and refusal field.
  - Execution state: pending

- [ ] E-03 Resolve the root cause. If E-01 reproduced the failure, fix the cause it identifies with the smallest change that preserves the test's behavioral assertion (for a test-side cause, in `tests/test_oc_runipd.py`, for example an unpatched gate or shared module state leaking between tests; for a production cause, in the module the traceback names, recorded as an out-of-scope path with its reason per the Scope check). If E-01 did not reproduce, record in Findings that the cause remains unknown, that E-02 is the shipped mitigation, and do not invent a mechanism.
  - Depends on: E-01, E-02
  - Expected outcome: either a diff fixing the identified cause with a written cause statement, or a written "cause unknown, not reproduced in N attempts" finding.
  - Execution state: pending

### Task group 2: Validation runs

- [ ] E-04 Run the validation set: the `SelfFinalizeWiringTests` class; `tests/test_oc_runipd.py` under 3 fixed seeds; the 7-module set from E-01 three times; the bare core suite `python3 -m pytest`; and `aw sanitize --agent`.
  - Depends on: E-03
  - Expected outcome: every run reports zero failures and zero errors; sanitizer exit 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Test suite contract (AGENTS.md, repo-local "Repository development contract"): bare `python3 -m pytest` runs the core tier; `addopts` is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; do not add `-q` (hides the summary line) or `-p no:randomly`; clear defaults with `-o addopts=""` for per-test counts. `pyproject.toml` declares pytest-randomly and says to reproduce an order with `-p randomly --randomly-seed=<n>` rather than hide it with `-p no:randomly`.
- Tests assert observable outcomes, never source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). E-02 keeps the assertion on observed call order and adds observed item state to the message.
- `pytest-repeat` is NOT installed in this environment (`ModuleNotFoundError: No module named 'pytest_repeat'`, measured 2026-10-23), so E-01 repeats with a shell loop rather than `--count`.
- The conftest hang guard (`conftest.pytest_runtest_call`, `_DEFAULT_TEST_CPU_TIMEOUT = 60.0`, `_DEFAULT_TEST_WALL_TIMEOUT = 240.0`) raises `TestHangTimeout` on a budget overrun; a guard trip would appear as that exception in the E-01 traceback, which distinguishes it from an assertion failure.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The only recorded failure is in executed plan `h8peam` V-05: `FAILED tests/test_oc_runipd.py::SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success` / `1 failed, 385 passed in 446.09s (0:07:26)`; reruns passed (`1 passed in 3.81s`, `177 passed in 40.55s`, `6 passed in 10.72s`). No assertion text or traceback was kept, so the failure mode is unknown. | `.aw/records/plans/executed/20261017-geajrj-01-h8peam-print-reclassified-refusal-reason-on-unmeasured-integration.ipd.md` V-05 |
| F-2 | Not reproduced at authoring: single node `1 passed in 4.97s`; whole file under `--randomly-seed` 1, 2, 3: `177 passed in 32.38s`, `177 passed in 29.52s`, `177 passed in 30.66s`; class with `AW_EXECUTION_ROLE=worker`: `6 passed in 7.50s`. | measured 2026-10-23 in this lane |
| F-3 | The test asserts only `order[:2] == ["begin", "run"]`. A failure therefore means `run_opencode` was not reached (or `driver_begin` was not called first); the assertion message would show only the list, not WHY. In `runner_shared.execute_item_core`, several gates can return before the spawn: the stale Scope-Paths check (`scope_target_refused`), the host-capability preflight (`preflight_host_capabilities`), the clean-base check (`evaluate_clean_base_for_launch` / `clean_base_launch_decision`), `assert_child_tool_identity` (which runs a subprocess probe once per process, cached in `_TOOL_IDENTITY_VERIFIED`), and the begin refusal. Which, if any, fired is unknown. | `agent_workflows/runner_shared.py` `execute_item_core`, `assert_child_tool_identity`; test body |
| F-4 | Several gates in that path read process-wide or environment state (`_TOOL_IDENTITY_VERIFIED`, ambient `AW_*` environment such as `AW_EXECUTION_ROLE`, git status of the temp repo). Under xdist with randomized order, a sibling test mutating such state is one plausible class of cause; load-dependent timing is another. Neither is established. | `tests/test_tool_identity_item_failure.py` clears and restores `runner_shared._TOOL_IDENTITY_VERIFIED`; `SelfFinalizeHelperTests.setUp` calls `support.declare_execution_role` while `SelfFinalizeWiringTests` does not |

## Proposed changes (ordered, validatable)

1. E-01: bounded load reproduction with captured traceback.
2. E-02: self-diagnosing failure message on the existing assertion (behavior unchanged).
3. E-03: root-cause fix if reproduced; otherwise a recorded "cause unknown" finding.
4. E-04: validation runs.

## Deferred / out of scope (with reason)

None outstanding. Rejected options, recorded as decisions rather than deferred work: a rerun/flaky plugin or an `xfail`/`skip` marker (it hides the defect, per the pyproject pytest-randomly note); installing `pytest-repeat` (a shell loop suffices and adds no dependency). The five sibling tests in `SelfFinalizeWiringTests` are untouched unless E-01 shows they share the identified cause, in which case E-03 extends the same fix to them in this plan, so nothing is left for a later carrier.

## Scope check

- Over-scope: none.
- Under-scope: if E-01 shows a production defect (for example a gate in `runner_shared.execute_item_core` that is genuinely load-sensitive), the fix lives outside `- Scope-Paths:`. `- Scope-Paths:` is a declaration, not a stop condition: make the fix and justify the path with `--scope-reason` at finalize. If that fix changes behavior a spec describes, stop and file a corrective plan instead, because this plan declares no spec edit.

## Required tests / validation

- `python3 -m pytest -o addopts="" "tests/test_oc_runipd.py::SelfFinalizeWiringTests"` passes.
- `python3 -m pytest tests/test_oc_runipd.py -p randomly --randomly-seed=<n>` for 3 seeds passes.
- The 7-module set from E-01 passes three consecutive times.
- Bare `python3 -m pytest` passes.
- `aw sanitize --agent` exits 0.

## Spec / documentation sync

N/A: the change is test-only (or, per Scope check, a production fix that changes no spec-described behavior); no spec or user-facing doc describes this test.

## Open questions

### OQ-01: Should the flake be quarantined if it cannot be reproduced?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `pyproject.toml` states test-order effects are a property of the project and must be reproduced, not hidden; the repository has no quarantine mechanism. If E-01 does not reproduce, E-02's diagnostic message is the deliverable, and the next occurrence will carry its cause.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the attempt table (seed, exact command, pytest summary line for each run, loop iteration count and pass/fail tally) and, if any run failed, the complete pasted assertion message and traceback; otherwise the literal statement "not reproduced in N attempts" with N.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff tests/test_oc_runipd.py` hunk showing the assertion still compares `order[:2]` to `["begin", "run"]` and now carries a `msg=` with order, status, disposition and refusal fields; paste the failure output from the temporary injected-refusal run (produced by E-02's uncommitted local patch) showing the message names `fail-begin` and `begin_refusal`; paste `git diff --stat` after reverting that patch showing only the intended hunk remains.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: either (a) the fix diff plus a one-paragraph cause statement tied to the E-01 traceback, and a re-run of the E-01 reproduction command that previously failed now passing (pasted summary line); or (b) the Findings row recording "cause unknown, not reproduced in N attempts" with the N from V-01.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the summary line of each run: the class run, the 3 seeded whole-file runs, the 3 seven-module runs, bare `python3 -m pytest`, and the `aw sanitize --agent` result record with exit code; each shows zero failures/errors and exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit qp9lh0 -- tests/test_oc_runipd.py` (plus any justified out-of-scope path per the Scope check); never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
