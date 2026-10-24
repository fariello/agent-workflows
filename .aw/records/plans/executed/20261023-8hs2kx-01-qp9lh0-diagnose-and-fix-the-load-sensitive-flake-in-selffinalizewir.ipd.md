# IPD: Diagnose and fix the load-sensitive flake in SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success

- Date: 2026-10-23
- Kind: child
- Concern: `tests/test_oc_runipd.py::SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success` failed once (`1 failed, 385 passed in 446.09s`) during a 7-module related-modules run recorded in executed plan `h8peam` V-05, then passed on three reruns (alone, whole file, whole class). Only the `FAILED` node line was preserved, not the assertion or traceback, so the failure mode and cause are unknown. A test that fails intermittently on the merge-gate path erodes trust in the suite and can spuriously refuse a runner integration.
- Scope: Reproduce the failure under load and capture its full traceback; make the test's ordering assertion self-diagnosing so any future failure records WHY `run_opencode` was not reached; fix the root cause if the reproduction identifies one. Edits are confined to `tests/test_oc_runipd.py` unless the reproduction proves a production defect (see Scope check).
- Scope-Paths: tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 8hs2kx
- Set: 8hs2kx
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: qp9lh0

## Workflow history
- 2026-10-24 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: qp9lh0 verified (set 8hs2kx, attempt 1).
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004

- 2026-10-23 draft (opencode): created.
- 2026-10-23 to-review (opencode): authored from backlog 8hs2kx with findings, checklist, and validation.

## Goal

Turn an unexplained one-off failure into either a fixed root cause or, if it cannot be reproduced within a bounded effort, a test whose failure message alone is enough to diagnose the next occurrence. Non-goals: no retry/rerun plugin, no `skip`/`xfail`/quarantine marker, no loosening of the asserted ordering property (begin before run), and no change to sibling tests in `SelfFinalizeWiringTests`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reproduce and make the failure self-diagnosing

- [x] E-01 Attempt a bounded reproduction under load and capture the full failure output. Run the same 7-module set `h8peam` E-05 ran (`tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py`) with the default `addopts` (xdist + pytest-randomly) and `-p randomly --randomly-seed=<n>` for at least 5 distinct seeds, plus at least 50 isolated iterations of the single node in a shell loop while that module set runs concurrently in a second process to supply load. Record every seed and outcome, and for any failure save the complete assertion message, traceback AND pytest's "Captured stderr call" section (`execute_item_core` prints each gate's refusal, for example "begin refused (no execution authority); not launching", to stderr, so that section may name the cause even before E-02 lands); `-o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` keeps the summary line visible. Also record, once per session, the ambient `AW_*` environment (`env | grep '^AW_'`) and `uptime` load average, since F-4 names ambient environment and load as candidate causes. Write the raw logs under `/tmp/opencode/qp9lh0/` (never committed). Bound: stop after the attempts above (5 seeded module-set runs plus 50 loaded single-node iterations) or at the first reproduction, whichever comes first; do not extend the hunt beyond that without recording why.
  - Depends on: none
  - Expected outcome: a table of attempts (seed, command, result) and either the captured traceback of at least one reproduction or an explicit "not reproduced in N attempts" statement.
  - Execution state: performed

- [x] E-02 In `tests/test_oc_runipd.py` `SelfFinalizeWiringTests.test_begin_precedes_run_opencode_on_success`, replace the bare `self.assertEqual(order[:2], ["begin", "run"])` with the same equality assertion carrying a `msg=` that reports the observed `order` list, `item["status"]`, the last attempt's `disposition`, any refusal/gate field present on the item (`begin_refusal`, `clean_base_refusal`, `scope_target_refusal`, `refusal`, `worktree_error`), the last attempt dict's gate keys (`host_capability_unavailable`, `scope_target_refused`, `clean_base_refused`, `begin_refused`), and the last few `event` names from `run_dir / "events.jsonl"` when that file exists (the gates append `ipd-begin-refused` and similar records there). Build the message in a small local helper inside the test so a missing key or file reads as absent rather than raising. A tool-identity mismatch (`runner_shared.assert_child_tool_identity` raising `ToolIdentityError`) propagates out of `driver.execute_item` as an exception with its own traceback, so it needs no message field. The asserted property is unchanged; only the failure message gains the state that explains which gate in `runner_shared.execute_item_core` stopped the turn before `run_opencode`.
  - Depends on: E-01
  - Expected outcome: the test still passes, and a deliberately injected refusal (for example a temporary local patch making the patched `driver_begin` return `(1, "x")`, NOT committed) produces a failure message naming the status and refusal field.
  - Execution state: performed

- [x] E-03 Resolve the root cause. If E-01 reproduced the failure, fix the cause it identifies with the smallest change that preserves the test's behavioral assertion (for a test-side cause, in `tests/test_oc_runipd.py`, for example an unpatched gate or shared module state leaking between tests; for a production cause, in the module the traceback names, recorded as an out-of-scope path with its reason per the Scope check). If the reproduction shows several sibling tests in `SelfFinalizeWiringTests` share the cause, apply the same fix to them here. If E-01 did not reproduce, record in Findings that the cause remains unknown, that E-02 is the shipped mitigation, and do not invent a mechanism.
  - Depends on: E-01, E-02
  - Expected outcome: either a diff fixing the identified cause with a written cause statement, or a written "cause unknown, not reproduced in N attempts" finding.
  - Execution state: performed

### Task group 2: Validation runs

- [x] E-04 Run the validation set: the `SelfFinalizeWiringTests` class; `tests/test_oc_runipd.py` under seeds 1, 2 and 3 (`-p randomly --randomly-seed=<n>`), plus any seed that reproduced the failure in E-01; the 7-module set from E-01 three times; the bare core suite `python3 -m pytest`; and `aw sanitize --agent`.
  - Depends on: E-03
  - Expected outcome: every run reports zero failures and zero errors; sanitizer exit 0.
  - Execution state: performed

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
| F-5 | Cause unknown, not reproduced in 55 attempts (5 seeded 7-module runs with seeds 101-105 plus 50 isolated iterations under concurrent test load). E-02 provides self-diagnosing message for any future failure. | E-01 / V-01 reproduction attempts |

## Proposed changes (ordered, validatable)

1. E-01: bounded load reproduction with captured traceback.
2. E-02: self-diagnosing failure message on the existing assertion (behavior unchanged).
3. E-03: root-cause fix if reproduced; otherwise a recorded "cause unknown" finding.
4. E-04: validation runs.

## Deferred / out of scope (with reason)

None outstanding. Rejected options, recorded as decisions rather than deferred work: a rerun/flaky plugin or an `xfail`/`skip` marker (it hides the defect, per the pyproject pytest-randomly note); installing `pytest-repeat` (a shell loop suffices and adds no dependency). The five sibling tests in `SelfFinalizeWiringTests` are untouched unless E-01 shows they share the identified cause, in which case E-03 extends the same fix to them in this plan, so nothing is left for a later carrier.

## Scope check

- Over-scope: none.
- Under-scope: if E-01 shows a production defect (for example a gate in `runner_shared.execute_item_core` that is genuinely load-sensitive), the fix lives outside `- Scope-Paths:`. `- Scope-Paths:` is a declaration, not a stop condition: make the fix and justify the path with `--scope-reason` at finalize. If that fix would change behavior a spec describes, do not make it in this plan (it declares no spec edit): ship E-02, record the cause and the proposed fix as a `proposal` in the outcome file (or a backlog item filed with `aw backlog new` when executing by hand), mark E-03 `blocked` with that reason, and finish the remaining independent work.

## Required tests / validation

- `python3 -m pytest -o addopts="" "tests/test_oc_runipd.py::SelfFinalizeWiringTests"` passes.
- `python3 -m pytest tests/test_oc_runipd.py -p randomly --randomly-seed=<n>` for seeds 1, 2, 3 (and any reproducing seed from E-01) passes.
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

- [x] V-01 validates E-01
  - Required evidence: paste the attempt table (seed, exact command, pytest summary line for each run, loop iteration count and pass/fail tally), the recorded `AW_*` environment and load average, and, if any run failed, the complete pasted assertion message, traceback and "Captured stderr call" section; otherwise the literal statement "not reproduced in N attempts" with N.
  - Observed evidence:
    Attempt table:
    | Seed / Run | Exact Command | Result Summary Line |
    |---|---|---|
    | Seed 101 | `python3 -m pytest tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -p randomly --randomly-seed=101 -o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` | `============================= 386 passed in 33.28s =============================` |
    | Seed 102 | `python3 -m pytest tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -p randomly --randomly-seed=102 -o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` | `============================= 386 passed in 29.19s =============================` |
    | Seed 103 | `python3 -m pytest tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -p randomly --randomly-seed=103 -o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` | `============================= 386 passed in 31.83s =============================` |
    | Seed 104 | `python3 -m pytest tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -p randomly --randomly-seed=104 -o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` | `============================= 386 passed in 32.58s =============================` |
    | Seed 105 | `python3 -m pytest tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -p randomly --randomly-seed=105 -o addopts="-n auto --dist=worksteal -m 'not slow and not livecorpus'" -rA --tb=long` | `============================= 386 passed in 35.67s =============================` |
    | Single-node 50-iteration loop under load | `for i in $(seq 1 50); do python3 -m pytest -o addopts="" -rA --tb=long "tests/test_oc_runipd.py::SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success"; done` (with concurrent background 7-module test execution) | 50 iterations: 50 passed, 0 failed |

    Ambient `AW_*` environment:
    ```
    AW_RUN_ID=run-20261024T014611Z-3126016
    AW_DRIVER_RESTART=3
    AW_HOME=/mnt/md1/VC/agent-workflows/.aw/records/runs/run-20261024T014611Z-3126016/agent-aw-home/06-qp9lh0-attempt-1
    AW_CONFIG_DIR=/mnt/md1/VC/agent-workflows/.aw/records/runs/run-20261024T014611Z-3126016/agent-user-config/06-qp9lh0-attempt-1
    AW_PIN_KEEP_ROOT=/mnt/md1/VC/agent-workflows
    AW_EXECUTION_ROLE=worker
    AW_ITEM_ID6=qp9lh0
    AW_RUNNER=aw agy run
    AW_AGENT_MODEL=Gemini 3.8 Flash High
    ```
    Load average: `1.41, 0.66, 0.55` before run; `15.63, 9.74, 4.57` during/after concurrent load.

    Statement: not reproduced in 55 attempts.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff tests/test_oc_runipd.py` hunk showing the assertion still compares `order[:2]` to `["begin", "run"]` and now carries a `msg=` with order, status, disposition and refusal fields; paste the failure output from the temporary injected-refusal run (produced by E-02's uncommitted local patch) showing the message names `fail-begin`, `begin_refusal` and the `ipd-begin-refused` event; paste `git diff --stat` after reverting that patch showing only the intended hunk remains.
  - Observed evidence:
    `git diff tests/test_oc_runipd.py` hunk:
    ```diff
    diff --git a/tests/test_oc_runipd.py b/tests/test_oc_runipd.py
    index 4ae5b7c20..a5e6a1817 100644
    --- a/tests/test_oc_runipd.py
    +++ b/tests/test_oc_runipd.py
    @@ -3153,7 +3153,53 @@ class SelfFinalizeWiringTests(unittest.TestCase):
                     )
                     driver.execute_item(run_dir, state, item, recovery=False)

    -            self.assertEqual(order[:2], ["begin", "run"])
    +            def _diagnostic_msg() -> str:
    +                attempts = item.get("attempts") or []
    +                last_attempt = (
    +                    attempts[-1] if (attempts and isinstance(attempts[-1], dict)) else {}
    +                )
    +                item_refusals = {
    +                    k: item[k]
    +                    for k in (
    +                        "begin_refusal",
    +                        "clean_base_refusal",
    +                        "scope_target_refusal",
    +                        "refusal",
    +                        "worktree_error",
    +                    )
    +                    if k in item
    +                }
    +                attempt_gates = {
    +                    k: last_attempt[k]
    +                    for k in (
    +                        "host_capability_unavailable",
    +                        "scope_target_refused",
    +                        "clean_base_refused",
    +                        "begin_refused",
    +                    )
    +                    if k in last_attempt
    +                }
    +                events: list[str] = []
    +                events_path = run_dir / "events.jsonl"
    +                if events_path.is_file():
    +                    try:
    +                        for line in events_path.read_text(encoding="utf-8").splitlines():
    +                            line = line.strip()
    +                            if line:
    +                                ev = json.loads(line)
    +                                if isinstance(ev, dict) and "event" in ev:
    +                                    events.append(str(ev["event"]))
    +                    except Exception:
    +                        pass
    +                return (
    +                    f"order={order!r}, status={item.get('status')!r}, "
    +                    f"disposition={last_attempt.get('disposition')!r}, "
    +                    f"item_refusals={item_refusals!r}, "
    +                    f"attempt_gate_keys={attempt_gates!r}, "
    +                    f"events={events[-5:]!r}"
    +                )
    +
    +            self.assertEqual(order[:2], ["begin", "run"], msg=_diagnostic_msg())
    ```
    Failure output from temporary injected refusal (`lambda r, i, a: order.append("begin") or (1, "x")`):
    ```
    =================================== FAILURES ===================================
    _____ SelfFinalizeWiringTests.test_begin_precedes_run_opencode_on_success ______

    self = <tests.test_oc_runipd.SelfFinalizeWiringTests testMethod=test_begin_precedes_run_opencode_on_success>
    ...
    >           self.assertEqual(order[:2], ["begin", "run"], msg=_diagnostic_msg())
    E           AssertionError: Lists differ: ['begin'] != ['begin', 'run']
    E
    E           Second list contains 1 additional elements.
    E           First extra element 1:
    E           'run'
    E
    E           - ['begin']
    E           + ['begin', 'run'] : order=['begin'], status='fail-begin', disposition='fail-begin', item_refusals={'begin_refusal': 'x'}, attempt_gate_keys={'begin_refused': 'x'}, events=['ipd-started', 'tool-identity-verified', 'ipd-begin-refused']
    ...
    ----------------------------- Captured stderr call -----------------------------
    ✗ IPD 01/1 wir001 begin refused (no execution authority); not launching. x
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd.py::SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success
    ============================== 1 failed in 0.97s ===============================
    ```
    `git diff --stat` after reverting patch:
    ```
     tests/test_oc_runipd.py | 48 +++++++++++++++++++++++++++++++++++++++++++++++-
     1 file changed, 47 insertions(+), 1 deletion(-)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: either (a) the fix diff plus a one-paragraph cause statement tied to the E-01 traceback, and a re-run of the E-01 reproduction command that previously failed now passing (pasted summary line); or (b) the Findings row recording "cause unknown, not reproduced in N attempts" with the N from V-01.
  - Observed evidence:
    Findings row F-5 recorded:
    ```markdown
    | F-5 | Cause unknown, not reproduced in 55 attempts (5 seeded 7-module runs with seeds 101-105 plus 50 isolated iterations under concurrent test load). E-02 provides self-diagnosing message for any future failure. | E-01 / V-01 reproduction attempts |
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the summary line of each run: the class run, the 3 seeded whole-file runs, the 3 seven-module runs, bare `python3 -m pytest`, and the `aw sanitize --agent` result record with exit code; each shows zero failures/errors and exit 0.
  - Observed evidence: All validation runs passed with zero failures/errors and exit 0.
    Class run: `============================== 6 passed in 5.51s ===============================`
    Whole-file seed 1: `177 passed in 19.93s`
    Whole-file seed 2: `177 passed in 21.99s`
    Whole-file seed 3: `177 passed in 20.88s`
    7-module run 1 (seed 201): `386 passed in 30.90s`
    7-module run 2 (seed 202): `386 passed in 29.64s`
    7-module run 3 (seed 203): `386 passed in 30.41s`
    Bare core suite: `1810 passed, 11 warnings in 73.63s (0:01:13)`
    Sanitizer: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6071,"findings":0,"evidence":["leak-scan"],"next":null}` (exit 0)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit qp9lh0 -- tests/test_oc_runipd.py` (plus any justified out-of-scope path per the Scope check); never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
