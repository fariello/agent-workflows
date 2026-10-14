# IPD: Classify and remand verifier transport failures under verification_retry_decision

- Date: 2026-10-14
- Kind: child
- Concern: Verifier session spawn errors and nonzero exit crashes in `runner_shared._run_verifier_turn` have no `verifier-transport-error` refusal code or retry classification in `verification_retry_decision`.
- Scope: Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR = "verifier-transport-error"` and `verifier_transport_refusal_text`, include it in `VERIFICATION_RETRYABLE_REFUSAL_CODES`, catch verifier spawn/transport errors and nonzero exit crashes in `_run_verifier_turn`, re-export across both host drivers (`oc_runipd`, `agy_runipd`), add unit and end-to-end tests in `tests/test_verification_sendback.py` and `tests/test_fixfirst_end_to_end.py`, and sync spec `25kzda` Section 5.5.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_verification_sendback.py, tests/test_fixfirst_end_to_end.py, .aw/records/specs/*/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: jodcz3
- Blocks-Release: f33nrj
- Set: jodcz3
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: yd4tqw

## Workflow history

- 2026-10-14 draft (Antigravity): created.
- 2026-10-14 to-review (Antigravity): populated review-ready IPD from backlog item `jodcz3`.

## Goal

Implement end-to-end classification, refusal recording, and fix-first remand for skeptical verifier session transport failures (`verifier-transport-error`) under `runner_shared.verification_retry_decision` across both `aw oc run` and `aw agy run`, closing the gap identified in `iksylm` F-06 and backlog item `jodcz3` against spec `25kzda` Section 5.5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Refusal code, retry classification, and `_run_verifier_turn` capture

- [ ] E-01 Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, `verifier_transport_refusal_text`, cross-driver re-exports, and `verification_retry_decision` classification in `agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py`, and `agent_workflows/agy_runipd.py`.
  - Depends on: none
  - Expected outcome: `agent_workflows/runner_shared.py` defines `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR: str = "verifier-transport-error"` alongside `VERIFY_REFUSAL_CODE_UNEVIDENCED` and `VERIFY_REFUSAL_CODE_SESSION_COLLISION` (leaving the 4-element `VERIFY_ABSENCE_CODES` tuple untouched), defines `verifier_transport_refusal_text(detail: str = "", *, exit_code: int | None = None) -> tuple[str, str, str]` applying `_redact_absolute_paths` to `detail` and returning preserved-lane guidance in `remedy`, and includes `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `VERIFICATION_RETRYABLE_REFUSAL_CODES` so `verification_failure_is_retryable` and `verification_retry_decision` classify `"verifier-transport-error"` as retryable under `VERIFICATION_RETRY_COUNT_KEY` and `frozen_retry_budget(state)`. Both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` re-export `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR as VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text as verifier_transport_refusal_text`.
  - Execution state: pending

- [ ] E-02 Catch verifier spawn exceptions and classify nonzero verifier exits without a readable verdict as `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `runner_shared._run_verifier_turn`.
  - Depends on: E-01
  - Expected outcome: In `runner_shared._run_verifier_turn`, `spawn_verifier(v_prompt_file, current_plan_path, work_dir, tracker, attempt_no)` is guarded against `(FileNotFoundError, PermissionError, OSError, HostSpawnError)`: on exception, `_run_verifier_turn` records `attempt["verify_exit_code"] = None`, `attempt["verify_spawn_error"] = _redact_absolute_paths(str(exc))`, `verify_disp = VERIFY_DISP_UNVERIFIED`, and `disposition = "fail-verify"`, calls `record_refusal(item, code=VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, reason=v_reason, remedy=v_remedy)`, and populates `attempt[VERIFICATION_REFUSED_KEY]` so `handle_verification_refusal` remands or terminates the item cleanly without escaping `execute_item_core`. When `spawn_verifier` returns `(v_rc, v_session, _v_log, _v_argv)`, `_run_verifier_turn` records `attempt["verify_exit_code"] = v_rc`; when `not v_session_collision` and (`v_rc != 0` or `scan_last_host_error(_v_log)` is non-empty) and no readable verdict was produced (`not v_outcome_file.is_file()` or `v_unreadable`), `_run_verifier_turn` records `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` (with `exit_code=v_rc` and any redacted host error) with `verify_disp = VERIFY_DISP_UNVERIFIED` and `disposition = "fail-verify"`, while preserving `VERIFY_ABSENCE_NO_OUTCOME_FILE` (`"verification-never-recorded"`) when `v_rc == 0` and no outcome file exists, and preserving `StallTimeout` (`VERIFY_ABSENCE_TURN_INTERRUPTED`, `disposition = "partial"`) unchanged.
  - Execution state: pending

### Task group 2: Behavioral unit tests, end-to-end matrix coverage, and spec sync

- [ ] E-03 Add unit and end-to-end verification-sendback tests for `verifier-transport-error` in `tests/test_verification_sendback.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_verification_sendback.py` tests: (a) `verification_failure_is_retryable(VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, "unverified")` and `verification_retry_decision` retry (`attempts < budget`), exhaustion (`attempts >= budget`), `retry_budget == 0`, and global cap (`fix_it_cap_decision`) behavior; (b) `verifier_transport_refusal_text` path redaction and preserved-lane remedy; (c) cross-driver object identity of `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text` on `oc_runipd`, `agy_runipd`, and `runner_shared`; (d) `build_verification_refusal_notice` and `build_prompt(..., recovery=True)` rendering `verifier-transport-error` with `prompt.count(FIX_IT_RULE_TEXT) == 1`; and (e) `execute_item_core` end-to-end runs covering both a verifier spawn exception (`FileNotFoundError` / `HostSpawnError`) and a nonzero verifier exit (`v_rc != 0` with no outcome file) remanded on attempt 1 to a passing attempt 2 (`status == "executed"`, `verification_retry_attempts == 1`), as well as budget exhaustion stopping at terminal `"fail-verify"` with `item["refusal"]["code"] == "verifier-transport-error"`.
  - Execution state: pending

- [ ] E-04 Add `VERIFICATION_RETRY_COUNT_KEY` and `verifier-transport-error` end-to-end matrix tests across `oc` and `agy` in `tests/test_fixfirst_end_to_end.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_fixfirst_end_to_end.py` includes `runner_shared.VERIFICATION_RETRY_COUNT_KEY` in `ALL_CORRECTION_COUNTERS` and adds `_run_matrix_verifier_transport_error`, `test_matrix_verifier_transport_error_oc`, and `test_matrix_verifier_transport_error_agy` on `TestFixFirstEndToEnd`, driving `mod.run_queue(run_dir, retry_incomplete=False)` with verification enabled (`no_verify=False`, `validate=True`), injecting a verifier transport failure on attempt 1 and a passing verifier (`VERIFIED` with `tests_run` command strings) on attempt 2, and asserting via `_assert_counters_isolated(final_item, runner_shared.VERIFICATION_RETRY_COUNT_KEY)` and `_assert_v02_prompt(..., "verifier-transport-error")` that the item ends `"executed"` with `VERIFICATION_RETRY_COUNT_KEY == 1`, all other counters in `ALL_CORRECTION_COUNTERS` at `0`/`None`, and `prompt.count(FIX_IT_RULE_TEXT) == 1`.
  - Execution state: pending

- [ ] E-05 Sync `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5 (`### 5.5 Retry policy`) and record a workflow history note.
  - Depends on: E-02
  - Expected outcome: In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy`, the `verification_retry_decision` bullet lists `verifier-transport-error` alongside `verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, and `verification-never-recorded`, the `verifier transport failure` table row cites `yd4tqw` (`Implementing: yd4tqw (from backlog jodcz3).`), and `aw specs note 25kzda --message ...` records the sync in `## Workflow history`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shutdown.KNOWN_ITEM_STATUSES` and `runner_shared.TERMINAL_STATES` are closed item-status vocabularies: a failed verification sets the item/attempt disposition to `"fail-verify"` (`VERIFICATION_RETRY_EXHAUSTED_STATUS = "fail-verify"` in `agent_workflows/runner_shared.py`), while the specific verification failure token (`verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, `verification-never-recorded`, and now `verifier-transport-error`) is recorded in `attempt[VERIFICATION_REFUSED_KEY]["code"]` and `item["refusal"]["code"]` via `render_stream.record_refusal` and classified by `runner_shared.verification_failure_is_retryable` / `runner_shared.verification_retry_decision`.
- `runner_shared.VERIFY_ABSENCE_CODES` is a closed 4-tuple (`VERIFY_ABSENCE_VERDICT_UNREADABLE`, `VERIFY_ABSENCE_NO_OUTCOME_FILE`, `VERIFY_ABSENCE_TURN_INTERRUPTED`, `VERIFY_ABSENCE_PLAN_UNRESOLVABLE`) pinned by `tests/test_finalize_stale_plan_path.py::FinalizeStalePlanPathTests.test_d_verify_absence_vocabulary_remains_disjoint` (`self.assertEqual(len(runner_shared.VERIFY_ABSENCE_CODES), 4)`) and `tests/test_agy_runipd_cli.py::test_verification_absence_codes_and_reasons`. Refusal codes outside the four absence facts (such as `VERIFY_REFUSAL_CODE_UNEVIDENCED = "verifier-no-test-evidence"` and `VERIFY_REFUSAL_CODE_SESSION_COLLISION = "verifier-session-collision"`) are defined alongside `VERIFY_REFUSAL_CODE_UNEVIDENCED` and listed in `VERIFICATION_RETRYABLE_REFUSAL_CODES`, never appended to `VERIFY_ABSENCE_CODES`.
- Both host drivers (`agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`) re-export shared verifier constants and helpers from `agent_workflows/runner_shared.py` using the explicit `from agent_workflows.runner_shared import X as X` idiom so `ruff --fix` preserves the re-export and cross-driver symmetry tests (`tests/test_verifier_evidence.py::RunnerVerificationGateTests.test_cross_driver_symmetry`) see identical objects on both modules.
- In `runner_shared.build_prompt`, `build_verification_refusal_notice(item, recovery)` calls `build_fix_it_notice(..., include_rule=False)` because `build_prompt` appends `FIX_IT_RULE_TEXT` once to the concatenated `raw_notices` block (`tests/test_fix_it_notice.py::PromptAssemblyTests.test_recovery_prompt_with_verification_refusal_contains_rule_once`).

## Findings

| # | Location / symbol | Finding | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/runner_shared.py` (`VERIFICATION_RETRYABLE_REFUSAL_CODES`, `verification_failure_is_retryable`, `verification_retry_decision`) | Spec `25kzda` Section 5.5 (`### 5.5 Retry policy`) specifies row `\| verifier transport failure \| verifier-transport-error \| verification_retry_decision \| Yes \|`, and the `verification_retry_decision` bullet lists only `verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, and `verification-never-recorded`. `VERIFICATION_RETRYABLE_REFUSAL_CODES` in `runner_shared.py` contains only those four codes, so `"verifier-transport-error"` is neither defined nor classified as retryable. | Any `verifier-transport-error` code passed to `verification_retry_decision` returns `retry=False, exhausted=False` with reason `"unrecognized verification refusal code 'verifier-transport-error'"`. |
| F-02 | `agent_workflows/runner_shared.py` (`_run_verifier_turn`, `spawn_verifier`) | Inside `_run_verifier_turn`, `v_rc, v_session, _v_log, _v_argv = spawn_verifier(...)` only catches `runner_stop.StopNowForce`, `runner_stop.StopAtCheckpoint`, and `StallTimeout`. Unlike `spawn_executor` in `execute_item_core` (which catches `(FileNotFoundError, PermissionError, OSError, HostSpawnError)`), an OS spawn error or `HostSpawnError` from `spawn_verifier` escapes `_run_verifier_turn` and `execute_item_core` before `handle_verification_refusal` can run. | A verifier binary `FileNotFoundError` / `PermissionError` / `OSError` crashes `run_queue` with an unhandled exception leaving `item["status"] == "running"`, and a `HostSpawnError` (a `DriverError` subclass) hits `run_queue`'s outer `except DriverError` handler (`failed-safely`) with zero verification retry attempts. |
| F-03 | `agent_workflows/runner_shared.py` (`_run_verifier_turn`, `VERIFY_ABSENCE_NO_OUTCOME_FILE`) | `_run_verifier_turn` binds `v_rc` from `spawn_verifier(...)` and never inspects or records it (`attempt["verify_exit_code"]` is never written). When the verifier process crashes (`v_rc != 0`) and writes no outcome file, `_run_verifier_turn` falls into the `VERIFY_ABSENCE_NO_OUTCOME_FILE` (`"verification-never-recorded"`) branch whose reason text asserts `"it ran to completion and wrote nothing"`. | Verifier transport crashes with nonzero exit codes are misclassified as `"verification-never-recorded"` instead of `"verifier-transport-error"`, hiding the exit code and any host error in `_v_log`. |
| F-04 | `tests/test_fixfirst_end_to_end.py` (`ALL_CORRECTION_COUNTERS`, `TestFixFirstEndToEnd`) | `ALL_CORRECTION_COUNTERS` in `tests/test_fixfirst_end_to_end.py` lists seven correction counters (`TURN_RETRY_COUNT_KEY`, `HOOK_FINALIZE_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY`, `FINALIZE_RETRY_COUNT_KEY`, `UNTOOLED_STATUS_RETRY_COUNT_KEY`, `HOOK_BYPASS_RETRY_COUNT_KEY`) and omits `VERIFICATION_RETRY_COUNT_KEY`, and `TestFixFirstEndToEnd` has no matrix test for `verifier-transport-error`. | The fix-first end-to-end matrix in `tests/test_fixfirst_end_to_end.py` does not exercise `verification_retry_decision` or `VERIFICATION_RETRY_COUNT_KEY` isolation for `verifier-transport-error`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py` (E-01)**:
   - Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR: str = "verifier-transport-error"` and `verifier_transport_refusal_text(detail: str = "", *, exit_code: int | None = None) -> tuple[str, str, str]` in `agent_workflows/runner_shared.py`.
   - Add `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` to `VERIFICATION_RETRYABLE_REFUSAL_CODES` and update `verification_failure_is_retryable`'s reason text for `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` to cite spec `25kzda` Section 5.5 (`verifier transport failure`).
   - Re-export `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR as VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text as verifier_transport_refusal_text` in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
2. **`agent_workflows/runner_shared.py` (E-02)**:
   - In `_run_verifier_turn`, catch `(FileNotFoundError, PermissionError, OSError, HostSpawnError)` from `spawn_verifier(...)`, recording `attempt["verify_exit_code"] = None`, `attempt["verify_spawn_error"] = _redact_absolute_paths(str(exc))`, `verify_disp = VERIFY_DISP_UNVERIFIED`, `disposition = "fail-verify"`, `record_refusal(item, code=VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, reason=v_reason, remedy=v_remedy)`, and `attempt[VERIFICATION_REFUSED_KEY]`.
   - When `spawn_verifier` returns `(v_rc, v_session, _v_log, _v_argv)`, record `attempt["verify_exit_code"] = v_rc`. When `not v_session_collision` and (`v_rc != 0` or `scan_last_host_error(_v_log)` is non-empty when `not v_outcome_file.is_file()`) and no readable verdict was produced (`not v_outcome_file.is_file()` or `v_unreadable`), classify the failure as `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` with `verify_disp = VERIFY_DISP_UNVERIFIED` and `disposition = "fail-verify"`, preserving `VERIFY_ABSENCE_NO_OUTCOME_FILE` when `v_rc == 0` and no outcome file was written.
3. **`tests/test_verification_sendback.py` (E-03)**:
   - Add unit and `execute_item_core` integration tests for `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, `verifier_transport_refusal_text`, cross-driver re-export identity, recovery prompt rendering (`prompt.count(FIX_IT_RULE_TEXT) == 1`), spawn exception remand, nonzero exit remand, and budget exhaustion (`fail-verify`).
4. **`tests/test_fixfirst_end_to_end.py` (E-04)**:
   - Add `runner_shared.VERIFICATION_RETRY_COUNT_KEY` to `ALL_CORRECTION_COUNTERS` and add `test_matrix_verifier_transport_error_oc` and `test_matrix_verifier_transport_error_agy` to `TestFixFirstEndToEnd`.
5. **`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (E-05)**:
   - Update the `verification_retry_decision` bullet and the `verifier transport failure` row in Section 5.5 (`### 5.5 Retry policy`) and record a workflow history entry via `aw specs note`.

## Deferred / out of scope (with reason)

none

## Scope check

- Over-scope: none.
- Under-scope: none. Every finding (`F-01` through `F-04`) is covered by `E-01` through `E-05` and validated by `V-01` through `V-05`.

## Required tests / validation

- Run targeted unit and end-to-end tests: `python3 -m pytest tests/test_verification_sendback.py tests/test_fixfirst_end_to_end.py tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py tests/test_fix_it_notice.py`
- Run full repository test suite: `python3 -m pytest`
- Run repository checks and leak sanitizer: `aw check all` and `aw sanitize --agent`

## Spec / documentation sync

- Update `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5 (`### 5.5 Retry policy`) so the `verification_retry_decision` bullet lists `verifier-transport-error` and the `verifier transport failure` table row cites `yd4tqw`, and record the note via `aw specs note 25kzda` (E-05 / V-05).

## Open questions

### OQ-01: Should `verifier-transport-error` be a refusal code in `VERIFICATION_RETRYABLE_REFUSAL_CODES` with item disposition `fail-verify`, or a new item status in `KNOWN_ITEM_STATUSES` / `VERIFY_ABSENCE_CODES`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence. `runner_shutdown.KNOWN_ITEM_STATUSES` and `runner_shared.TERMINAL_STATES` are closed item-status sets where verification failures use disposition `"fail-verify"` (`VERIFICATION_RETRY_EXHAUSTED_STATUS = "fail-verify"`), and `runner_shared.VERIFY_ABSENCE_CODES` is a closed 4-tuple pinned at length 4 by `tests/test_finalize_stale_plan_path.py::FinalizeStalePlanPathTests.test_d_verify_absence_vocabulary_remains_disjoint`. Spec `25kzda` Section 5.5 places `verifier-transport-error` on `verification_retry_decision`, which classifies the refusal code stored in `attempt[VERIFICATION_REFUSED_KEY]["code"]` and `item["refusal"]["code"]` via `VERIFICATION_RETRYABLE_REFUSAL_CODES`. Defining `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR = "verifier-transport-error"` alongside `VERIFY_REFUSAL_CODE_UNEVIDENCED` and adding it to `VERIFICATION_RETRYABLE_REFUSAL_CODES` matches the existing architecture without breaking either closed vocabulary.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR == "verifier-transport-error"` is in `runner_shared.VERIFICATION_RETRYABLE_REFUSAL_CODES` and NOT in `runner_shared.VERIFY_ABSENCE_CODES` (`len(runner_shared.VERIFY_ABSENCE_CODES) == 4`), `runner_shared.verification_failure_is_retryable("verifier-transport-error", "unverified")[0]` is `True`, and `oc_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR is runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `agy_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR is runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` (verified via `python3 -m pytest tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Inspection of `runner_shared._run_verifier_turn` and test execution via `E-03` confirming that: (1) `(FileNotFoundError, PermissionError, OSError, HostSpawnError)` raised by `spawn_verifier` is caught inside `_run_verifier_turn`, sets `attempt["verify_exit_code"] = None`, `verify_disp = "unverified"`, `disposition = "fail-verify"`, and records `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `item["refusal"]` and `attempt[VERIFICATION_REFUSED_KEY]`; (2) `v_rc != 0` without a readable outcome file records `attempt["verify_exit_code"] = v_rc` and `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` instead of `VERIFY_ABSENCE_NO_OUTCOME_FILE`; and (3) `v_rc == 0` with no outcome file still records `VERIFY_ABSENCE_NO_OUTCOME_FILE` (`"verification-never-recorded"`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted runner output from `python3 -m pytest tests/test_verification_sendback.py tests/test_fix_it_notice.py` showing all new unit and `execute_item_core` tests for `verifier-transport-error` (predicate classification, path redaction, cross-driver identity, recovery prompt rule count `== 1`, spawn exception remand to `"executed"`, nonzero exit remand to `"executed"`, and budget exhaustion stopping at `"fail-verify"`) passing with 0 failures.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted runner output from `python3 -m pytest tests/test_fixfirst_end_to_end.py` showing `test_matrix_verifier_transport_error_oc` and `test_matrix_verifier_transport_error_agy` (and all existing matrix tests with `VERIFICATION_RETRY_COUNT_KEY` in `ALL_CORRECTION_COUNTERS`) passing with 0 failures.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Diff or inspection of `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5 showing `verifier-transport-error` in the `verification_retry_decision` bullet, `yd4tqw` in the `verifier transport failure` table row, a `## Workflow history` note recorded by `aw specs note`, and `aw check all` + `aw sanitize --agent` + full `python3 -m pytest` passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute before `- Status:` is `approved` (or `auto-approved`). During execution, commit only scoped files via `aw commit yd4tqw -- <paths>`, paste actual test runner output into `Observed evidence:` for `V-01` through `V-05`, and let the runner or `aw ipd finalize` transition the plan to `.aw/records/plans/executed/` once all `E-*` items are `performed` and all `V-*` items are `pass`.
