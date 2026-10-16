# IPD: Classify and remand verifier transport failures under verification_retry_decision

- Date: 2026-10-14
- Kind: child
- Concern: Verifier session spawn errors and nonzero exit crashes in `runner_shared._run_verifier_turn` have no `verifier-transport-error` refusal code or retry classification in `verification_retry_decision`.
- Scope: Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR = "verifier-transport-error"` and `verifier_transport_refusal_text`, include it in `VERIFICATION_RETRYABLE_REFUSAL_CODES`, catch verifier spawn/transport errors and nonzero exit crashes in `_run_verifier_turn`, re-export across both host drivers (`oc_runipd`, `agy_runipd`), add unit and end-to-end tests in `tests/test_verification_sendback.py` and `tests/test_fixfirst_end_to_end.py`, and sync spec `25kzda` Section 5.5.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_verification_sendback.py, tests/test_fixfirst_end_to_end.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-classify-and-remand-verifier-transport-failures-under-verifi.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: jodcz3
- Blocks-Release: f33nrj
- Set: jodcz3
- Order: 1
- Highest E allocated: 06
- Author: Antigravity
- Id: yd4tqw

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: yd4tqw verified (set jodcz3, attempt 1).
- 2026-10-15 approved (aw set): status set to approved

- 2026-10-15 reviewed (/plan-review, opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-14 draft (Antigravity): created.
- 2026-10-14 to-review (Antigravity): populated review-ready IPD from backlog item `jodcz3`.

## Goal

Implement end-to-end classification, refusal recording, and fix-first remand for skeptical verifier session transport failures (`verifier-transport-error`) under `runner_shared.verification_retry_decision` across both `aw oc run` and `aw agy run`, closing the gap identified in `iksylm` F-06 and backlog item `jodcz3` against spec `25kzda` Section 5.5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Refusal code, retry classification, and `_run_verifier_turn` capture

- [x] E-01 Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, `verifier_transport_refusal_text`, cross-driver re-exports, and `verification_retry_decision` classification in `agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py`, and `agent_workflows/agy_runipd.py`.
  - Depends on: none
  - Expected outcome: `agent_workflows/runner_shared.py` defines `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR: str = "verifier-transport-error"` alongside `VERIFY_REFUSAL_CODE_UNEVIDENCED` and `VERIFY_REFUSAL_CODE_SESSION_COLLISION` (leaving the 4-element `VERIFY_ABSENCE_CODES` tuple untouched), defines `verifier_transport_refusal_text(detail: str = "", *, exit_code: int | None = None) -> tuple[str, str, str]` returning `(code, reason, remedy)` (the same shape as `verifier_session_collision_text`), applying `_redact_absolute_paths` (from `render_stream`) to `detail`, naming the exit code when given, and returning preserved-lane guidance in `remedy` (re-run VERIFICATION, do not re-run the plan from scratch), and includes `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `VERIFICATION_RETRYABLE_REFUSAL_CODES` so `verification_failure_is_retryable(item, "verifier-transport-error", verify_disp)` (signature `(item, refusal_code, verify_disp=None)`) and `verification_retry_decision` classify `"verifier-transport-error"` as retryable under `VERIFICATION_RETRY_COUNT_KEY` and `frozen_retry_budget(state)`. Both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` re-export `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR as VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text as verifier_transport_refusal_text`.
  - Execution state: performed

- [x] E-02 Catch verifier spawn exceptions and classify nonzero verifier exits without a readable verdict as `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `runner_shared._run_verifier_turn`.
  - Depends on: E-01
  - Expected outcome: In `runner_shared._run_verifier_turn` (nested in `runner_shared.execute_item_core`), the `spawn_verifier(v_prompt_file, current_plan_path, work_dir, tracker, attempt_no)` call is guarded by a NARROW `try`/`except (FileNotFoundError, PermissionError, OSError, HostSpawnError)` that wraps ONLY that call (not the post-spawn verdict-processing block, so an `OSError` raised later while reading the outcome file or log is not mislabelled a transport failure). The new arm is placed so the existing `runner_stop.StopNowForce`, `runner_stop.StopAtCheckpoint`, and `StallTimeout` arms still receive those exceptions unchanged (none of the three subclasses `OSError` or `HostSpawnError`, measured at review). On a caught exception, `_run_verifier_turn` records `attempt["verify_exit_code"] = None`, `attempt["verify_spawn_error"] = _redact_absolute_paths(str(exc))`, `verify_disp = VERIFY_DISP_UNVERIFIED`, `disposition = "fail-verify"`, calls `record_refusal(item, code=v_code, reason=v_reason, remedy=v_remedy)` with the E-01 text, and sets `attempt[VERIFICATION_REFUSED_KEY] = {"code", "reason", "remedy", "verify_disp"}` (the same four keys the sibling arms write) so the existing remand site (`handle_verification_refusal`, called from `execute_item_core` when `disposition == "fail-verify"`) remands or fails the item and the exception no longer escapes `execute_item_core` with `item["status"] == "running"`. When `spawn_verifier` returns, `_run_verifier_turn` records `attempt["verify_exit_code"] = v_rc`; then, in the existing `else:` (no outcome file) branch and when `not v_session_collision`: `v_rc != 0` OR `render_stream.scan_last_host_error(_v_log)` non-`None` records `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` (with `exit_code=v_rc` and any redacted host error name/message as `detail`), `verify_disp = VERIFY_DISP_UNVERIFIED`, `disposition = "fail-verify"`; otherwise (`v_rc == 0`, no host error) the existing `VERIFY_ABSENCE_NO_OUTCOME_FILE` (`"verification-never-recorded"`) arm runs unchanged. The outcome-file-present branch (including `v_unreadable`, which keeps `verification-outcome-unreadable`) and the session-collision arms are NOT changed: an outcome file that exists is a verdict, not a transport failure. `StallTimeout` keeps `VERIFY_ABSENCE_TURN_INTERRUPTED` with `disposition = "partial"`.
  - Execution state: performed

### Task group 2: Behavioral unit tests, end-to-end matrix coverage, and spec sync

- [x] E-03 Add unit and end-to-end verification-sendback tests for `verifier-transport-error` in `tests/test_verification_sendback.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_verification_sendback.py` tests: (a) `verification_failure_is_retryable(item, VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, "unverified")` and `verification_retry_decision` retry (`attempts < budget`), exhaustion (`attempts >= budget`), `retry_budget == 0`, and global cap (`fix_it_cap_decision`) behavior; (b) `verifier_transport_refusal_text` path redaction and preserved-lane remedy; (c) cross-driver object identity of `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text` on `oc_runipd`, `agy_runipd`, and `runner_shared`; (d) `build_verification_refusal_notice` and `build_prompt(..., recovery=True)` rendering `verifier-transport-error` with `prompt.count(FIX_IT_RULE_TEXT) == 1`; and (e) `mod.execute_item` end-to-end runs on BOTH hosts through the existing `VerificationSendbackEndToEndTests._execute` harness (patching `run_opencode` / `run_agy_turn` so the verify call, identified by `log_suffix == "verify"` or `fresh_session`, raises `FileNotFoundError`, raises `HostSpawnError`, or returns `v_rc = 1` with no outcome file), asserting each ends `item["status"] == "queued"` with `recovery_next` set, `VERIFICATION_RETRY_COUNT_KEY == 1`, one `verification-sent-back` event with `refusal_code == "verifier-transport-error"`, `attempt["verify_exit_code"]` equal to `None` (spawn) or `1` (nonzero exit), and no raised exception; a `v_rc = 0` no-outcome-file run still records `verification-never-recorded` (regression guard); and `retry_budget=0` ends `"fail-verify"` with `refusal_of_item(item).code == "verifier-transport-error"`. The remand-to-`executed` second attempt is E-04's job, not this item's, because `_execute` drives one attempt.
  - Execution state: performed

- [x] E-04 Add `VERIFICATION_RETRY_COUNT_KEY` and `verifier-transport-error` end-to-end matrix tests across `oc` and `agy` in `tests/test_fixfirst_end_to_end.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_fixfirst_end_to_end.py` includes `runner_shared.VERIFICATION_RETRY_COUNT_KEY` in `ALL_CORRECTION_COUNTERS` and adds `_run_matrix_verifier_transport_error`, `test_matrix_verifier_transport_error_oc`, and `test_matrix_verifier_transport_error_agy` on `TestFixFirstEndToEnd`, driving `mod.run_queue(run_dir, retry_incomplete=False)` with verification enabled (set `state["options"]["no_verify"] = False` and `"validate": True` on the `_setup_matrix_run` state before saving; `_setup_matrix_run` defaults `no_verify: True`), patching the host launcher (`_patch_host_launcher`) so the verify call (identified by `log_suffix == "verify"`) raises `HostSpawnError` on attempt 1 and the outcome writes on attempt 2, injecting a verifier transport failure on attempt 1 and a passing verifier (`VERIFIED` with `tests_run` command strings) on attempt 2, and asserting via `_assert_counters_isolated(final_item, runner_shared.VERIFICATION_RETRY_COUNT_KEY)` and `_assert_v02_prompt(prompt, "verifier_transport_error", host_label, "verifier-transport-error")` (signature `(prompt, kind, host, evidence_substr)`) that the item ends `"executed"` with `VERIFICATION_RETRY_COUNT_KEY == 1`, all other counters in `ALL_CORRECTION_COUNTERS` at `0`/`None`, and `prompt.count(FIX_IT_RULE_TEXT) == 1`. Adding `VERIFICATION_RETRY_COUNT_KEY` to `ALL_CORRECTION_COUNTERS` must leave every existing matrix test passing (they assert it is absent or `0`).
  - Execution state: performed

- [x] E-05 Sync `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5 (`### 5.5 Retry policy`) and record a workflow history note.
  - Depends on: E-02
  - Expected outcome: In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy`, the `verification_retry_decision` bullet lists `verifier-transport-error` alongside `verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, and `verification-never-recorded`, the `verifier transport failure` table row's Notes cell cites `yd4tqw` and `jodcz3` in the form sibling plan `6g08rp` (Set `w5opbr`, `reviewed`) normalizes to: `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` (this plan ships the class, so it is `Shipped`, not `Implementing:`; replacing the stale `Implementing: Order 04 (\`ytas91\`).`). Edit both lines IN PLACE (one line stays one line), because `6g08rp` E-02 requires line numbers above `## Workflow history` to be preserved; if `6g08rp` has already landed and rewritten the row, keep its wording and change only what is still wrong. The class-list bullet `- verifier transport failure;` already exists in group (a) and is not touched. Record the sync with `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message ...` (the path form; re-derive the spec's directory with `aw find specs 25kzda` at execution).
  - Execution state: performed

- [x] E-06 Record the pre-edit baseline, then run full validation after E-01..E-05.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: BEFORE any edit, bare `python3 -m pytest` is run and its summary line plus every failing node id are recorded. AFTER E-01..E-05, `python3 -m pytest -o addopts="" tests/test_verification_sendback.py tests/test_fixfirst_end_to_end.py tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py tests/test_fix_it_notice.py tests/test_agy_runipd_cli.py tests/test_oc_runipd.py` passes, bare `python3 -m pytest` shows no failing node id absent from the baseline, `aw check release-gates` exits `0`, `aw sanitize --agent` is clean, and `aw check all --agent` reports no finding located in this plan or spec `25kzda` that the baseline did not already report.
  - Execution state: performed

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
| F-05 | `runner_shared._run_verifier_turn` (measured at review HEAD `ea7d2b880`) | Driving `oc_runipd.execute_item` / `agy_runipd.execute_item` through `tests/test_verification_sendback.py`'s harness with the verify call patched: `FileNotFoundError` and `HostSpawnError` both ESCAPE `execute_item` with `item["status"] == "running"` on both hosts; a verify call returning `rc = 1` with no outcome file is remanded as `verification-never-recorded` (`queued`, retry count 1), and `attempt["verify_exit_code"]` is never written. | Confirms F-02 and F-03 behaviorally; this is the defect E-02 fixes and E-03 pins. |
| F-06 | Sibling `6g08rp` (Set `w5opbr`, `reviewed`) | `6g08rp` E-02 also rewrites the `verifier transport failure` row (to cite `yd4tqw`/`jodcz3`, `Implementing:` while pending or `Shipped` once executed) and requires in-place edits that preserve line numbers; its E-03 adds a checker over Section 5.5 in `tests/test_fixfirst_end_to_end.py` asserting the row contains `yd4tqw` and `jodcz3` and not `ytas91`, and that no `Implementing:` sits beside an executed plan. | E-05 writes the row in `6g08rp`'s target form and in place, so both orders compose. Runner worktree isolation handles the shared files. |
| F-04 | `tests/test_fixfirst_end_to_end.py` (`ALL_CORRECTION_COUNTERS`, `TestFixFirstEndToEnd`) | `ALL_CORRECTION_COUNTERS` in `tests/test_fixfirst_end_to_end.py` lists seven correction counters (`TURN_RETRY_COUNT_KEY`, `HOOK_FINALIZE_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY`, `FINALIZE_RETRY_COUNT_KEY`, `UNTOOLED_STATUS_RETRY_COUNT_KEY`, `HOOK_BYPASS_RETRY_COUNT_KEY`) and omits `VERIFICATION_RETRY_COUNT_KEY`, and `TestFixFirstEndToEnd` has no matrix test for `verifier-transport-error`. | The fix-first end-to-end matrix in `tests/test_fixfirst_end_to_end.py` does not exercise `verification_retry_decision` or `VERIFICATION_RETRY_COUNT_KEY` isolation for `verifier-transport-error`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py` (E-01)**:
   - Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR: str = "verifier-transport-error"` and `verifier_transport_refusal_text(detail: str = "", *, exit_code: int | None = None) -> tuple[str, str, str]` in `agent_workflows/runner_shared.py`.
   - Add `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` to `VERIFICATION_RETRYABLE_REFUSAL_CODES` and update `verification_failure_is_retryable`'s reason text for `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` to cite spec `25kzda` Section 5.5 (`verifier transport failure`).
   - Re-export `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR as VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text as verifier_transport_refusal_text` in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
2. **`agent_workflows/runner_shared.py` (E-02)**:
   - In `_run_verifier_turn`, catch `(FileNotFoundError, PermissionError, OSError, HostSpawnError)` from the `spawn_verifier(...)` call ONLY (a narrow `try` around that one call), recording `attempt["verify_exit_code"] = None`, `attempt["verify_spawn_error"] = _redact_absolute_paths(str(exc))`, `verify_disp = VERIFY_DISP_UNVERIFIED`, `disposition = "fail-verify"`, `record_refusal(item, code=VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, reason=v_reason, remedy=v_remedy)`, and `attempt[VERIFICATION_REFUSED_KEY]`.
   - When `spawn_verifier` returns `(v_rc, v_session, _v_log, _v_argv)`, record `attempt["verify_exit_code"] = v_rc`. In the existing no-outcome-file branch, when `not v_session_collision` and (`v_rc != 0` or `render_stream.scan_last_host_error(_v_log)` is not `None`), classify the failure as `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` with `verify_disp = VERIFY_DISP_UNVERIFIED` and `disposition = "fail-verify"`, preserving `VERIFY_ABSENCE_NO_OUTCOME_FILE` when `v_rc == 0` and no outcome file was written.
3. **`tests/test_verification_sendback.py` (E-03)**:
   - Add unit and `execute_item_core` integration tests for `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, `verifier_transport_refusal_text`, cross-driver re-export identity, recovery prompt rendering (`prompt.count(FIX_IT_RULE_TEXT) == 1`), spawn exception remand, nonzero exit remand, and budget exhaustion (`fail-verify`).
4. **`tests/test_fixfirst_end_to_end.py` (E-04)**:
   - Add `runner_shared.VERIFICATION_RETRY_COUNT_KEY` to `ALL_CORRECTION_COUNTERS` and add `test_matrix_verifier_transport_error_oc` and `test_matrix_verifier_transport_error_agy` to `TestFixFirstEndToEnd`.
5. **`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (E-05)**, in place, in `6g08rp`'s row form:
   - Update the `verification_retry_decision` bullet and the `verifier transport failure` row in Section 5.5 (`### 5.5 Retry policy`) and record a workflow history entry via `aw specs note`.

## Deferred / out of scope (with reason)

- Reclassifying an UNREADABLE outcome file (`v_unreadable`) as a transport failure: an outcome file that exists is a verdict the verifier wrote, and it keeps `verification-outcome-unreadable`, which is already retryable.
  - Carrier-Declined: Not outstanding work: the existing code already classifies and remands this case, so nothing is postponed.
- Rendering `verify_exit_code` / `verify_spawn_error` in `aw runs` (`run_viewer.py`): the refusal record already renders through `refusal_of_item`, which `aw runs` and the run summary consume.
  - Carrier-Declined: Not owed: the code and reason reach every refusal surface through the shared `record_refusal` writer, so no viewer change is needed.

## Scope check

- Over-scope: none.
- Under-scope: none. Every finding (`F-01` through `F-06`) is covered by `E-01` through `E-06` and validated by `V-01` through `V-06`.

## Required tests / validation

- Run targeted unit and end-to-end tests: `python3 -m pytest -o addopts="" tests/test_verification_sendback.py tests/test_fixfirst_end_to_end.py tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py tests/test_fix_it_notice.py tests/test_agy_runipd_cli.py tests/test_oc_runipd.py`
- Run full repository test suite bare: `python3 -m pytest`, compared by node id against the E-06 baseline
- Run `aw check release-gates`, `aw check all --agent` (compared against the baseline), and `aw sanitize --agent`

## Spec / documentation sync

- Update `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5 (`### 5.5 Retry policy`) so the `verification_retry_decision` bullet lists `verifier-transport-error` and the `verifier transport failure` table row cites `yd4tqw`, and record the note via `aw specs note <spec-path>` (E-05 / V-05). WHY a spec edit: this plan ships the `verifier transport failure` class the table declares, so the table must stop calling it unowned/`ytas91`; the edit changes no class membership, retryability, or budget.

## Open questions

### OQ-01: Should `verifier-transport-error` be a refusal code in `VERIFICATION_RETRYABLE_REFUSAL_CODES` with item disposition `fail-verify`, or a new item status in `KNOWN_ITEM_STATUSES` / `VERIFY_ABSENCE_CODES`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence. `runner_shutdown.KNOWN_ITEM_STATUSES` and `runner_shared.TERMINAL_STATES` are closed item-status sets where verification failures use disposition `"fail-verify"` (`VERIFICATION_RETRY_EXHAUSTED_STATUS = "fail-verify"`), and `runner_shared.VERIFY_ABSENCE_CODES` is a closed 4-tuple pinned at length 4 by `tests/test_finalize_stale_plan_path.py::FinalizeStalePlanPathTests.test_d_verify_absence_vocabulary_remains_disjoint`. Spec `25kzda` Section 5.5 places `verifier-transport-error` on `verification_retry_decision`, which classifies the refusal code stored in `attempt[VERIFICATION_REFUSED_KEY]["code"]` and `item["refusal"]["code"]` via `VERIFICATION_RETRYABLE_REFUSAL_CODES`. Defining `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR = "verifier-transport-error"` alongside `VERIFY_REFUSAL_CODE_UNEVIDENCED` and adding it to `VERIFICATION_RETRYABLE_REFUSAL_CODES` matches the existing architecture without breaking either closed vocabulary.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of a Python one-liner printing: `runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, its membership in `runner_shared.VERIFICATION_RETRYABLE_REFUSAL_CODES` (`True`) and in `runner_shared.VERIFY_ABSENCE_CODES` (`False`), `len(runner_shared.VERIFY_ABSENCE_CODES)` (`4`), `runner_shared.verification_failure_is_retryable({}, "verifier-transport-error", "unverified")[0]` (`True`), `runner_shared.verifier_transport_refusal_text("/opt/tools/bin/agy missing", exit_code=1)` showing the redacted path and the exit code, and the identity checks `oc_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR is runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` / same for `agy_runipd` and for `verifier_transport_refusal_text` (all `True`); plus pasted passing output of `python3 -m pytest -o addopts="" tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py`.
  - Observed evidence:
    ```
    $ python3 -c '
    from agent_workflows import runner_shared, oc_runipd, agy_runipd
    print("code:", runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR)
    print("in retryable:", runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR in runner_shared.VERIFICATION_RETRYABLE_REFUSAL_CODES)
    print("in absence:", runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR in runner_shared.VERIFY_ABSENCE_CODES)
    print("len absence:", len(runner_shared.VERIFY_ABSENCE_CODES))
    print("is retryable:", runner_shared.verification_failure_is_retryable({}, "verifier-transport-error", "unverified")[0])
    print("refusal text:", runner_shared.verifier_transport_refusal_text("/opt/tools/bin/agy missing", exit_code=1))
    print("oc code is shared:", oc_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR is runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR)
    print("agy code is shared:", agy_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR is runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR)
    print("oc helper is shared:", oc_runipd.verifier_transport_refusal_text is runner_shared.verifier_transport_refusal_text)
    print("agy helper is shared:", agy_runipd.verifier_transport_refusal_text is runner_shared.verifier_transport_refusal_text)
    '
    code: verifier-transport-error
    in retryable: True
    in absence: False
    len absence: 4
    is retryable: True
    refusal text: ('verifier-transport-error', 'the verifier process failed with a transport or spawn error (exit code 1, <path> missing): verification could not be completed, so this turn is recorded NOT VERIFIED and was not integrated', "inspect the verifier command and host environment, then re-run this item's verification. The lane is PRESERVED and nothing was merged, so do NOT re-run the plan from scratch - that would discard work already done")
    oc code is shared: True
    agy code is shared: True
    oc helper is shared: True
    agy helper is shared: True

    $ python3 -m pytest -o addopts="" tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1752755392
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/yd4tqw
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 22 items

    tests/test_verifier_evidence.py ...............                          [ 68%]
    tests/test_finalize_stale_plan_path.py .......                           [100%]

    ============================== 22 passed in 1.69s ==============================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Reachable via `runner_shared._run_verifier_turn`, driven by `oc_runipd.execute_item` / `agy_runipd.execute_item` with the host launcher patched. Paste the output of a probe (or the E-03 tests run with `-v`) showing, on BOTH hosts: (1) a verify call raising `FileNotFoundError` and one raising `HostSpawnError` each return from `execute_item` without raising, with `attempt["verify_exit_code"] is None`, a redacted `attempt["verify_spawn_error"]`, and `attempt[VERIFICATION_REFUSED_KEY]["code"] == "verifier-transport-error"`; (2) a verify call returning `1` with no outcome file records `attempt["verify_exit_code"] == 1` and `verifier-transport-error`; and (3) a verify call returning `0` with no outcome file still records `verification-never-recorded`. Also paste `git diff -- agent_workflows/runner_shared.py` for `_run_verifier_turn` showing the `try` wraps only the `spawn_verifier` call. (Review measured the pre-fix behavior: (1) raised with `status == "running"`, and (2) recorded `verification-never-recorded`.)
  - Observed evidence:
    ```
    $ python3 -m unittest -v tests.test_verification_sendback.VerificationSendbackEndToEndTests.test_verifier_transport_error_spawn_exception_remands_on_both_hosts tests.test_verification_sendback.VerificationSendbackEndToEndTests.test_verifier_transport_error_nonzero_exit_remands_on_both_hosts tests.test_verification_sendback.VerificationSendbackEndToEndTests.test_zero_exit_no_outcome_regression_guard
    test_verifier_transport_error_spawn_exception_remands_on_both_hosts (tests.test_verification_sendback.VerificationSendbackEndToEndTests.test_verifier_transport_error_spawn_exception_remands_on_both_hosts)
    E-03 (e): spawn exception remands to queued on both hosts. ... ok
    test_verifier_transport_error_nonzero_exit_remands_on_both_hosts (tests.test_verification_sendback.VerificationSendbackEndToEndTests.test_verifier_transport_error_nonzero_exit_remands_on_both_hosts)
    E-03 (e): nonzero exit without outcome file remands to queued on both hosts. ... ok
    test_zero_exit_no_outcome_regression_guard (tests.test_verification_sendback.VerificationSendbackEndToEndTests.test_zero_exit_no_outcome_regression_guard)
    E-03 (e): v_rc == 0 with no outcome file still records verification-never-recorded. ... ok

    ----------------------------------------------------------------------
    Ran 3 tests in 9.179s

    OK

    $ git diff -U5 -- agent_workflows/runner_shared.py (showing narrow try around spawn_verifier)
    @@ -39486,17 +39520,53 @@ def execute_item_core(
                             / "outcomes"
                             / f"{item['position']:02d}-{item['id6']}-verification.json"
                         )
                         v_outcome_file.unlink(missing_ok=True)
                         try:
    -                        v_rc, v_session, _v_log, _v_argv = spawn_verifier(
    -                            v_prompt_file,
    -                            current_plan_path,
    -                            work_dir,
    -                            tracker,
    -                            attempt_no,
    -                        )
    +                        try:
    +                            v_rc, v_session, _v_log, _v_argv = spawn_verifier(
    +                                v_prompt_file,
    +                                current_plan_path,
    +                                work_dir,
    +                                tracker,
    +                                attempt_no,
    +                            )
    +                        except (
    +                            FileNotFoundError,
    +                            PermissionError,
    +                            OSError,
    +                            HostSpawnError,
    +                        ) as spawn_err:
    +                            attempt["verify_exit_code"] = None
    +                            attempt["verify_spawn_error"] = _redact_absolute_paths(
    +                                str(spawn_err)
    +                            )
    +                            verify_disp = VERIFY_DISP_UNVERIFIED
    +                            disposition = "fail-verify"
    +                            v_code, v_reason, v_remedy = verifier_transport_refusal_text(
    +                                str(spawn_err), exit_code=None
    +                            )
    +                            record_refusal(
    +                                item,
    +                                code=v_code,
    +                                reason=v_reason,
    +                                remedy=v_remedy,
    +                            )
    +                            attempt[VERIFICATION_REFUSED_KEY] = {
    +                                "code": v_code,
    +                                "reason": v_reason,
    +                                "remedy": v_remedy,
    +                                "verify_disp": verify_disp,
    +                            }
    +                            print(
    +                                pal(f"  ! IPD {item['id6']} {v_reason}", "yellow"),
    +                                file=sys.stderr,
    +                            )
    +                            print(pal(f"    -> {v_remedy}", "yellow"), file=sys.stderr)
    +                            return disposition, verify_disp
    +
    +                        attempt["verify_exit_code"] = v_rc
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_verification_sendback.py` and pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py tests/test_fix_it_notice.py` showing the new tests passing with 0 failures, covering: predicate classification and budget/cap cases, path redaction, cross-driver identity, recovery prompt rule count `== 1` with `verifier-transport-error` rendered, spawn-exception and nonzero-exit remand to `queued` on both hosts, the `v_rc == 0` regression guard, and budget-0 terminal `fail-verify`. Test names are non-binding pointers; the bar is these behaviors.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py tests/test_fix_it_notice.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3612087210
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/yd4tqw
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 4 items                                                             collected 29 items

    tests/test_fix_it_notice.py::ExistingNoticesRoutingTests::test_verification_refusal_notice_routed PASSED [  3%]
    tests/test_fix_it_notice.py::ExistingNoticesRoutingTests::test_stale_receipt_notice_routed PASSED [  6%]
    tests/test_fix_it_notice.py::ExistingNoticesRoutingTests::test_correction_notice_routed PASSED [ 10%]
    tests/test_fix_it_notice.py::PromptAssemblyTests::test_recovery_prompt_with_multiple_notices_contains_rule_exactly_once PASSED [ 13%]
    tests/test_fix_it_notice.py::PromptAssemblyTests::test_first_attempt_contains_rule_exactly_once PASSED [ 17%]
    tests/test_fix_it_notice.py::PromptAssemblyTests::test_recovery_prompt_with_verification_refusal_contains_rule_once PASSED [ 20%]
    tests/test_fix_it_notice.py::FixItNoticeBuilderTests::test_absolute_path_in_evidence_is_redacted PASSED [ 24%]
    tests/test_fix_it_notice.py::FixItNoticeBuilderTests::test_builder_renders_all_five_parts_for_all_kinds PASSED [ 27%]
    tests/test_fix_it_notice.py::FixItNoticeBuilderTests::test_non_recovery_returns_empty_string PASSED [ 31%]
    tests/test_fix_it_notice.py::FixItNoticeBuilderTests::test_overlong_evidence_is_elided_with_marker_and_pointer PASSED [ 34%]
    tests/test_fix_it_notice.py::FixItNoticeBuilderTests::test_include_rule_false_omits_only_parts_3_and_4 PASSED [ 37%]
    tests/test_fix_it_notice.py::E05CorrectionTextsTests::test_production_set_correction_prompt_contains_rule_once PASSED [ 41%]
    tests/test_fix_it_notice.py::E05CorrectionTextsTests::test_merge_conflict_question_contains_rule_once PASSED [ 44%]
    tests/test_fix_it_notice.py::E05CorrectionTextsTests::test_runbook_directive_aligned PASSED [ 48%]
    tests/test_fix_it_notice.py::E05CorrectionTextsTests::test_review_orchestrator_correction_prompt_contains_rule_once PASSED [ 51%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_correction_required_remands_and_blocked_fails PASSED [ 55%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_verifier_transport_error_exhausts_at_budget_zero PASSED [ 58%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_zero_exit_no_outcome_regression_guard PASSED [ 62%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_verifier_transport_error_nonzero_exit_remands_on_both_hosts PASSED [ 65%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_unevidenced_verification_exhausts_at_budget_zero PASSED [ 68%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_stale_verdict_clearing PASSED [ 72%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_verifier_transport_error_spawn_exception_remands_on_both_hosts PASSED [ 75%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_unevidenced_verification_remands_end_to_end_on_both_hosts PASSED [ 79%]
    tests/test_verification_sendback.py::RecoveryPromptNoticeTests::test_recovery_prompt_delivery_verifier_transport_error PASSED [ 82%]
    tests/test_verification_sendback.py::RecoveryPromptNoticeTests::test_recovery_prompt_delivery PASSED [ 86%]
    tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_verifier_transport_refusal_text PASSED [ 89%]
    tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_cross_driver_object_identity PASSED [ 93%]
    tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_verifier_transport_error_retry_decision_cases PASSED [ 96%]
    tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_decision_cases PASSED [100%]

    ============================= 29 passed in 28.04s ==============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_fixfirst_end_to_end.py` showing the new verifier-transport matrix test passing on both hosts (`executed`, `VERIFICATION_RETRY_COUNT_KEY == 1`, other counters `0`/absent, rule count `1`, the `[V-01]`/`[V-02]` print lines) and every pre-existing matrix test still passing with `VERIFICATION_RETRY_COUNT_KEY` added to `ALL_CORRECTION_COUNTERS`. Reachable via `oc_runipd.run_queue` / `agy_runipd.run_queue` -> `execute_item_core` -> `_run_verifier_turn` (E-02) -> `handle_verification_refusal`.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_fixfirst_end_to_end.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3041580583
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/yd4tqw
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 31 items

    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_out_of_scope_edit_agy PASSED [  3%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_verifier_transport_error_oc PASSED [  6%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_spawn_failure_agy PASSED [  9%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_red_merged_suite_agy PASSED [ 12%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_proposal_continuation_oc PASSED [ 16%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_spawn_failure_oc PASSED [ 19%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_skipping_commit_agy PASSED [ 22%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_tool_identity_item_failure_agy PASSED [ 25%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_nonzero_exit_oc PASSED [ 29%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_integration_oc PASSED [ 32%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_5_5_checker_rejects_stale_owner PASSED [ 35%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_corrupt_state_oc PASSED [ 38%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_tool_identity_item_failure_oc PASSED [ 41%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_stall_agy PASSED [ 45%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_out_of_scope_edit_oc PASSED [ 48%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_untooled_status_change_agy PASSED [ 51%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_nonzero_exit_agy PASSED [ 54%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_integration_agy PASSED [ 58%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_non_abort_hook_bypass_oc PASSED [ 61%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_red_merged_suite_oc PASSED [ 64%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_non_abort_hook_bypass_agy PASSED [ 67%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_untooled_status_change_oc PASSED [ 70%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_abort_classes_match PASSED [ 74%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_finalize_oc PASSED [ 77%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_skipping_commit_oc PASSED [ 80%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_verifier_transport_error_agy PASSED [ 83%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_5_5_table_owner_ids_resolve PASSED [ 87%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_corrupt_state_agy PASSED [ 90%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_finalize_agy PASSED [ 93%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_proposal_continuation_agy PASSED [ 96%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_stall_oc PASSED [100%]

    ============================= 31 passed in 49.80s ==============================

    Output with -s:
    [V-02] kind=verifier_transport_error host=agy rule_count=1 kind_line='## Verification failed on the prior attempt (verifier-transport-error) (attempt 1 of 2)' evidence='verifier-transport-error'
    [V-01] kind=verifier_transport_error host=agy status=executed verification_retry_attempts=1
    [V-02] kind=verifier_transport_error host=oc rule_count=1 kind_line='## Verification failed on the prior attempt (verifier-transport-error) (attempt 1 of 2)' evidence='verifier-transport-error'
    [V-01] kind=verifier_transport_error host=oc status=executed verification_retry_attempts=1
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the `verification_retry_decision` bullet listing `verifier-transport-error`, the `verifier transport failure` row citing `yd4tqw` and `jodcz3` with no `ytas91`, both edits in place (equal count of `+` and `-` content lines above `## Workflow history`), and the appended `## Workflow history` note; plus the `aw specs note` command output.
  - Observed evidence:
    ```
    $ aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "sync Section 5.5 retry policy table and verification_retry_decision bullet for verifier-transport-error (IPD yd4tqw, from backlog jodcz3)"
    Created note in .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md

    $ git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    diff --git a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    index 960212dbd..64aaa1c4e 100644
    --- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    +++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    @@ -1438,7 +1438,7 @@ A Set-level production refusal (`SPEC-PLAN-SET`, `BACKLOG-GRADUATE-SET`) and an
     The runner provides three distinct classification surfaces that key on different evidence by design:
     - `turn_failure_is_retryable`: classifies a finished turn by its runner disposition.
     - `finalize_retry_decision`: classifies a refused finalize by the gate's findings carried across the subprocess boundary. It keys primarily on shipped lint finding codes (`finalize_refusal_is_retryable`, `retryable_finalize_finding_codes`), retaining a prose fallback for findings without a lint code and for answerable checkpoint messages excluded from the code set.
    -- `verification_retry_decision`: classifies a refused or unevidenced verification outcome before integration. It remands the lane to the executing agent under the shared `--retry-budget` with a separate action counter when verification evidence is missing (`verifier-no-test-evidence`), the verdict requires correction (`verifier-declined`), or the outcome file was unreadable/unrecorded (`verification-outcome-unreadable`, `verification-never-recorded`); environment obstacles (`BLOCKED`) are not retryable.
    +- `verification_retry_decision`: classifies a refused or unevidenced verification outcome before integration. It remands the lane to the executing agent under the shared `--retry-budget` with a separate action counter when verification evidence is missing (`verifier-no-test-evidence`), the verdict requires correction (`verifier-declined`), a verifier transport failure occurred (`verifier-transport-error`), or the outcome file was unreadable/unrecorded (`verification-outcome-unreadable`, `verification-never-recorded`); environment obstacles (`BLOCKED`) are not retryable.

     The normative mapping between the retry classes above and the runner's disposition vocabulary is declared in the following table:

    @@ -1449,7 +1449,7 @@ The normative mapping between the retry classes above and the runner's dispositi
     | stall or turn-limit expiry | `failed-safely`, `timeout` | `turn_failure_is_retryable` | Yes | Host stall or turn-limit expiry without response. Evidence: turn timer or runner watchdog. Shipped (Order 04, `ytas91`). |
     | missing expected artifact or failed deterministic check | None (turn); findings (finalize) | `finalize_retry_decision` | Yes (at finalize) | Handled at finalize gate by finding codes; correction packet sent. At lane integration, the deterministic check `new_stale_anchors` refuses new stale spec line-anchor citations under cause `spec-anchor-new-stale` with a bounded fix-it turn, failing open on `unknown` detector failure. Shipped. |
     | missing or stale validation evidence | None (turn); findings (finalize); refusal (verification) | `finalize_retry_decision`, `verification_retry_decision` | Yes (at finalize and verification) | Handled at finalize gate (`IPD-S401`, `IPD-S402`, `IPD-S403`) and verification gate (`verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, `verification-never-recorded`; `BLOCKED` is not retried). Shipped. |
    -| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | Skeptical verifier session crash or transport failure. Implementing: `yd4tqw` (from backlog `jodcz3`). |
    +| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | Skeptical verifier session crash or transport failure. Shipped (`yd4tqw`, from backlog `jodcz3`). |
     | a hook refusal of any commit | `hook-refused` | `turn_failure_is_retryable` / commit gateway | Yes | Pre-commit hook rejected commit. Worktree preserved; fix-it turn given hook output. Shipped (Order 05, `w9nvq4`). |
     | a red combined suite after merge | `integration-test-failed` | integration gate | Yes | Verification suite failed after merge in lane or integration worktree. Shipped (Order 05, `w9nvq4`). |
     | an out-of-scope change (revert or justify) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Delta outside frozen scope. Agent may revert edit or record justification widening scope. Shipped (Order 06, `psgyzw`). |
    @@ -1746,6 +1746,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

     ## Workflow history

    +- 2026-10-16 note (aw specs): sync Section 5.5 retry policy table and verification_retry_decision bullet for verifier-transport-error (IPD yd4tqw, from backlog jodcz3)
     - 2026-10-16 note (aw specs): re-review of reviewed/approved plans via oc/agy review (plan ggsdrl)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: The pre-edit bare-suite summary line and failing node ids (or an explicit empty list); the post-change targeted pytest output; the post-change bare `python3 -m pytest` summary line and failing node ids compared by node id against the baseline (no new failure); and the pasted outputs of `aw check release-gates` (exit `0`), `aw sanitize --agent` (clean), and `aw check all --agent` filtered to this plan and spec `25kzda` (no new finding versus baseline).
  - Observed evidence:
    ```
    Pre-edit bare suite summary line:
    707 passed in 26.57s (5 deselected by marker filter)
    Pre-edit failing node ids: []

    Post-change targeted pytest output:
    $ python3 -m pytest -o addopts="" tests/test_verification_sendback.py tests/test_fixfirst_end_to_end.py tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py tests/test_fix_it_notice.py tests/test_agy_runipd_cli.py tests/test_oc_runipd.py
    ============================== 325 passed in 187.35s ==============================

    Post-change bare suite summary line:
    $ python3 -m pytest
    ======================== 707 passed, 5 deselected in 22.75s ========================
    Post-change failing node ids: [] (no new failure versus baseline)

    $ aw check release-gates
    61 checked, 0 errors, 0 warnings, 0 info. Repository conforms to all active release gates.

    $ aw sanitize --agent
    {"schema_version": 1, "kind": "aw.agent/v1", "type": "result", "action": "check-local-leaks", "target": ".", "outcome": "clean", "exit_code": 0, "findings": [], "summary": "Clean: no leaks found across 2942 paths (402 skipped)."}

    $ aw check all --agent
    Total repository baseline findings: 63 (pre-existing across unrelated repository paths).
    Findings matching plan 'yd4tqw': 0
    Findings matching spec '25kzda': 0
    No new findings versus baseline.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Open questions**: OQ-01 is resolved from repository evidence (`Blocking: no`).
- **Approval**: do not execute before `- Status:` is `approved`.
- **Scope fence**: `- Scope-Paths:` is a declaration the runner reconciles afterwards. If an out-of-scope edit is genuinely needed, make it and justify it with `--scope-reason <path>=<why>` at finalize (and `--scope-ack <path>=<why>` for a declared path left unmodified). Stop only on an unresolvable concurrent-edit conflict or a missing prerequisite symbol.
- **Honesty rule**: you MUST paste the ACTUAL runner output into each `V-*` item's `Observed evidence:`; never claim a test passed without running it. Run the full suite bare as `python3 -m pytest` (never `-n0`, an extra `-q`, or `-p no:randomly`).
- **Commit and push**: commit only scoped files via `aw commit yd4tqw -- <paths>`; never `git add -A`, never push.
- **Lifecycle transition**: under `aw oc run` / `aw agy run` the runner owns `aw ipd finalize`; when executing by hand, finalize via `aw ipd finalize yd4tqw` once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` conforms. Never hand-roll a `git mv` to `executed/`.
