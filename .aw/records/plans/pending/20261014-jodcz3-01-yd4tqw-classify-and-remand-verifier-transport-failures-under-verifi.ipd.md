# IPD: Classify and remand verifier transport failures under verification_retry_decision

- Date: 2026-10-14
- Kind: child
- Concern: Verifier session spawn errors and nonzero exit crashes in `runner_shared._run_verifier_turn` have no `verifier-transport-error` refusal code or retry classification in `verification_retry_decision`.
- Scope: Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR = "verifier-transport-error"` and `verifier_transport_refusal_text`, include it in `VERIFICATION_RETRYABLE_REFUSAL_CODES`, catch verifier spawn/transport errors and nonzero exit crashes in `_run_verifier_turn`, re-export across both host drivers (`oc_runipd`, `agy_runipd`), add unit and end-to-end tests in `tests/test_verification_sendback.py` and `tests/test_fixfirst_end_to_end.py`, and sync spec `25kzda` Section 5.5.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_verification_sendback.py, tests/test_fixfirst_end_to_end.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-classify-and-remand-verifier-transport-failures-under-verifi.ipd.md
- Item-Dependencies: none
- Status: approved
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
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved

- 2026-10-15 reviewed (/plan-review, opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-14 draft (Antigravity): created.
- 2026-10-14 to-review (Antigravity): populated review-ready IPD from backlog item `jodcz3`.

## Goal

Implement end-to-end classification, refusal recording, and fix-first remand for skeptical verifier session transport failures (`verifier-transport-error`) under `runner_shared.verification_retry_decision` across both `aw oc run` and `aw agy run`, closing the gap identified in `iksylm` F-06 and backlog item `jodcz3` against spec `25kzda` Section 5.5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Refusal code, retry classification, and `_run_verifier_turn` capture

- [ ] E-01 Define `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, `verifier_transport_refusal_text`, cross-driver re-exports, and `verification_retry_decision` classification in `agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py`, and `agent_workflows/agy_runipd.py`.
  - Depends on: none
  - Expected outcome: `agent_workflows/runner_shared.py` defines `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR: str = "verifier-transport-error"` alongside `VERIFY_REFUSAL_CODE_UNEVIDENCED` and `VERIFY_REFUSAL_CODE_SESSION_COLLISION` (leaving the 4-element `VERIFY_ABSENCE_CODES` tuple untouched), defines `verifier_transport_refusal_text(detail: str = "", *, exit_code: int | None = None) -> tuple[str, str, str]` returning `(code, reason, remedy)` (the same shape as `verifier_session_collision_text`), applying `_redact_absolute_paths` (from `render_stream`) to `detail`, naming the exit code when given, and returning preserved-lane guidance in `remedy` (re-run VERIFICATION, do not re-run the plan from scratch), and includes `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `VERIFICATION_RETRYABLE_REFUSAL_CODES` so `verification_failure_is_retryable(item, "verifier-transport-error", verify_disp)` (signature `(item, refusal_code, verify_disp=None)`) and `verification_retry_decision` classify `"verifier-transport-error"` as retryable under `VERIFICATION_RETRY_COUNT_KEY` and `frozen_retry_budget(state)`. Both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` re-export `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR as VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text as verifier_transport_refusal_text`.
  - Execution state: pending

- [ ] E-02 Catch verifier spawn exceptions and classify nonzero verifier exits without a readable verdict as `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` in `runner_shared._run_verifier_turn`.
  - Depends on: E-01
  - Expected outcome: In `runner_shared._run_verifier_turn` (nested in `runner_shared.execute_item_core`), the `spawn_verifier(v_prompt_file, current_plan_path, work_dir, tracker, attempt_no)` call is guarded by a NARROW `try`/`except (FileNotFoundError, PermissionError, OSError, HostSpawnError)` that wraps ONLY that call (not the post-spawn verdict-processing block, so an `OSError` raised later while reading the outcome file or log is not mislabelled a transport failure). The new arm is placed so the existing `runner_stop.StopNowForce`, `runner_stop.StopAtCheckpoint`, and `StallTimeout` arms still receive those exceptions unchanged (none of the three subclasses `OSError` or `HostSpawnError`, measured at review). On a caught exception, `_run_verifier_turn` records `attempt["verify_exit_code"] = None`, `attempt["verify_spawn_error"] = _redact_absolute_paths(str(exc))`, `verify_disp = VERIFY_DISP_UNVERIFIED`, `disposition = "fail-verify"`, calls `record_refusal(item, code=v_code, reason=v_reason, remedy=v_remedy)` with the E-01 text, and sets `attempt[VERIFICATION_REFUSED_KEY] = {"code", "reason", "remedy", "verify_disp"}` (the same four keys the sibling arms write) so the existing remand site (`handle_verification_refusal`, called from `execute_item_core` when `disposition == "fail-verify"`) remands or fails the item and the exception no longer escapes `execute_item_core` with `item["status"] == "running"`. When `spawn_verifier` returns, `_run_verifier_turn` records `attempt["verify_exit_code"] = v_rc`; then, in the existing `else:` (no outcome file) branch and when `not v_session_collision`: `v_rc != 0` OR `render_stream.scan_last_host_error(_v_log)` non-`None` records `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` (with `exit_code=v_rc` and any redacted host error name/message as `detail`), `verify_disp = VERIFY_DISP_UNVERIFIED`, `disposition = "fail-verify"`; otherwise (`v_rc == 0`, no host error) the existing `VERIFY_ABSENCE_NO_OUTCOME_FILE` (`"verification-never-recorded"`) arm runs unchanged. The outcome-file-present branch (including `v_unreadable`, which keeps `verification-outcome-unreadable`) and the session-collision arms are NOT changed: an outcome file that exists is a verdict, not a transport failure. `StallTimeout` keeps `VERIFY_ABSENCE_TURN_INTERRUPTED` with `disposition = "partial"`.
  - Execution state: pending

### Task group 2: Behavioral unit tests, end-to-end matrix coverage, and spec sync

- [ ] E-03 Add unit and end-to-end verification-sendback tests for `verifier-transport-error` in `tests/test_verification_sendback.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_verification_sendback.py` tests: (a) `verification_failure_is_retryable(item, VERIFY_REFUSAL_CODE_TRANSPORT_ERROR, "unverified")` and `verification_retry_decision` retry (`attempts < budget`), exhaustion (`attempts >= budget`), `retry_budget == 0`, and global cap (`fix_it_cap_decision`) behavior; (b) `verifier_transport_refusal_text` path redaction and preserved-lane remedy; (c) cross-driver object identity of `VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` and `verifier_transport_refusal_text` on `oc_runipd`, `agy_runipd`, and `runner_shared`; (d) `build_verification_refusal_notice` and `build_prompt(..., recovery=True)` rendering `verifier-transport-error` with `prompt.count(FIX_IT_RULE_TEXT) == 1`; and (e) `mod.execute_item` end-to-end runs on BOTH hosts through the existing `VerificationSendbackEndToEndTests._execute` harness (patching `run_opencode` / `run_agy_turn` so the verify call, identified by `log_suffix == "verify"` or `fresh_session`, raises `FileNotFoundError`, raises `HostSpawnError`, or returns `v_rc = 1` with no outcome file), asserting each ends `item["status"] == "queued"` with `recovery_next` set, `VERIFICATION_RETRY_COUNT_KEY == 1`, one `verification-sent-back` event with `refusal_code == "verifier-transport-error"`, `attempt["verify_exit_code"]` equal to `None` (spawn) or `1` (nonzero exit), and no raised exception; a `v_rc = 0` no-outcome-file run still records `verification-never-recorded` (regression guard); and `retry_budget=0` ends `"fail-verify"` with `refusal_of_item(item).code == "verifier-transport-error"`. The remand-to-`executed` second attempt is E-04's job, not this item's, because `_execute` drives one attempt.
  - Execution state: pending

- [ ] E-04 Add `VERIFICATION_RETRY_COUNT_KEY` and `verifier-transport-error` end-to-end matrix tests across `oc` and `agy` in `tests/test_fixfirst_end_to_end.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_fixfirst_end_to_end.py` includes `runner_shared.VERIFICATION_RETRY_COUNT_KEY` in `ALL_CORRECTION_COUNTERS` and adds `_run_matrix_verifier_transport_error`, `test_matrix_verifier_transport_error_oc`, and `test_matrix_verifier_transport_error_agy` on `TestFixFirstEndToEnd`, driving `mod.run_queue(run_dir, retry_incomplete=False)` with verification enabled (set `state["options"]["no_verify"] = False` and `"validate": True` on the `_setup_matrix_run` state before saving; `_setup_matrix_run` defaults `no_verify: True`), patching the host launcher (`_patch_host_launcher`) so the verify call (identified by `log_suffix == "verify"`) raises `HostSpawnError` on attempt 1 and the outcome writes on attempt 2, injecting a verifier transport failure on attempt 1 and a passing verifier (`VERIFIED` with `tests_run` command strings) on attempt 2, and asserting via `_assert_counters_isolated(final_item, runner_shared.VERIFICATION_RETRY_COUNT_KEY)` and `_assert_v02_prompt(prompt, "verifier_transport_error", host_label, "verifier-transport-error")` (signature `(prompt, kind, host, evidence_substr)`) that the item ends `"executed"` with `VERIFICATION_RETRY_COUNT_KEY == 1`, all other counters in `ALL_CORRECTION_COUNTERS` at `0`/`None`, and `prompt.count(FIX_IT_RULE_TEXT) == 1`. Adding `VERIFICATION_RETRY_COUNT_KEY` to `ALL_CORRECTION_COUNTERS` must leave every existing matrix test passing (they assert it is absent or `0`).
  - Execution state: pending

- [ ] E-05 Sync `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5 (`### 5.5 Retry policy`) and record a workflow history note.
  - Depends on: E-02
  - Expected outcome: In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy`, the `verification_retry_decision` bullet lists `verifier-transport-error` alongside `verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, and `verification-never-recorded`, the `verifier transport failure` table row's Notes cell cites `yd4tqw` and `jodcz3` in the form sibling plan `6g08rp` (Set `w5opbr`, `reviewed`) normalizes to: `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` (this plan ships the class, so it is `Shipped`, not `Implementing:`; replacing the stale `Implementing: Order 04 (\`ytas91\`).`). Edit both lines IN PLACE (one line stays one line), because `6g08rp` E-02 requires line numbers above `## Workflow history` to be preserved; if `6g08rp` has already landed and rewritten the row, keep its wording and change only what is still wrong. The class-list bullet `- verifier transport failure;` already exists in group (a) and is not touched. Record the sync with `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message ...` (the path form; re-derive the spec's directory with `aw find specs 25kzda` at execution).
  - Execution state: pending

- [ ] E-06 Record the pre-edit baseline, then run full validation after E-01..E-05.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: BEFORE any edit, bare `python3 -m pytest` is run and its summary line plus every failing node id are recorded. AFTER E-01..E-05, `python3 -m pytest -o addopts="" tests/test_verification_sendback.py tests/test_fixfirst_end_to_end.py tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py tests/test_fix_it_notice.py tests/test_agy_runipd_cli.py tests/test_oc_runipd.py` passes, bare `python3 -m pytest` shows no failing node id absent from the baseline, `aw check release-gates` exits `0`, `aw sanitize --agent` is clean, and `aw check all --agent` reports no finding located in this plan or spec `25kzda` that the baseline did not already report.
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

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of a Python one-liner printing: `runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR`, its membership in `runner_shared.VERIFICATION_RETRYABLE_REFUSAL_CODES` (`True`) and in `runner_shared.VERIFY_ABSENCE_CODES` (`False`), `len(runner_shared.VERIFY_ABSENCE_CODES)` (`4`), `runner_shared.verification_failure_is_retryable({}, "verifier-transport-error", "unverified")[0]` (`True`), `runner_shared.verifier_transport_refusal_text("/opt/tools/bin/agy missing", exit_code=1)` showing the redacted path and the exit code, and the identity checks `oc_runipd.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR is runner_shared.VERIFY_REFUSAL_CODE_TRANSPORT_ERROR` / same for `agy_runipd` and for `verifier_transport_refusal_text` (all `True`); plus pasted passing output of `python3 -m pytest -o addopts="" tests/test_finalize_stale_plan_path.py tests/test_verifier_evidence.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Reachable via `runner_shared._run_verifier_turn`, driven by `oc_runipd.execute_item` / `agy_runipd.execute_item` with the host launcher patched. Paste the output of a probe (or the E-03 tests run with `-v`) showing, on BOTH hosts: (1) a verify call raising `FileNotFoundError` and one raising `HostSpawnError` each return from `execute_item` without raising, with `attempt["verify_exit_code"] is None`, a redacted `attempt["verify_spawn_error"]`, and `attempt[VERIFICATION_REFUSED_KEY]["code"] == "verifier-transport-error"`; (2) a verify call returning `1` with no outcome file records `attempt["verify_exit_code"] == 1` and `verifier-transport-error`; and (3) a verify call returning `0` with no outcome file still records `verification-never-recorded`. Also paste `git diff -- agent_workflows/runner_shared.py` for `_run_verifier_turn` showing the `try` wraps only the `spawn_verifier` call. (Review measured the pre-fix behavior: (1) raised with `status == "running"`, and (2) recorded `verification-never-recorded`.)
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_verification_sendback.py` and pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py tests/test_fix_it_notice.py` showing the new tests passing with 0 failures, covering: predicate classification and budget/cap cases, path redaction, cross-driver identity, recovery prompt rule count `== 1` with `verifier-transport-error` rendered, spawn-exception and nonzero-exit remand to `queued` on both hosts, the `v_rc == 0` regression guard, and budget-0 terminal `fail-verify`. Test names are non-binding pointers; the bar is these behaviors.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_fixfirst_end_to_end.py` showing the new verifier-transport matrix test passing on both hosts (`executed`, `VERIFICATION_RETRY_COUNT_KEY == 1`, other counters `0`/absent, rule count `1`, the `[V-01]`/`[V-02]` print lines) and every pre-existing matrix test still passing with `VERIFICATION_RETRY_COUNT_KEY` added to `ALL_CORRECTION_COUNTERS`. Reachable via `oc_runipd.run_queue` / `agy_runipd.run_queue` -> `execute_item_core` -> `_run_verifier_turn` (E-02) -> `handle_verification_refusal`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the `verification_retry_decision` bullet listing `verifier-transport-error`, the `verifier transport failure` row citing `yd4tqw` and `jodcz3` with no `ytas91`, both edits in place (equal count of `+` and `-` content lines above `## Workflow history`), and the appended `## Workflow history` note; plus the `aw specs note` command output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: The pre-edit bare-suite summary line and failing node ids (or an explicit empty list); the post-change targeted pytest output; the post-change bare `python3 -m pytest` summary line and failing node ids compared by node id against the baseline (no new failure); and the pasted outputs of `aw check release-gates` (exit `0`), `aw sanitize --agent` (clean), and `aw check all --agent` filtered to this plan and spec `25kzda` (no new finding versus baseline).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Open questions**: OQ-01 is resolved from repository evidence (`Blocking: no`).
- **Approval**: do not execute before `- Status:` is `approved`.
- **Scope fence**: `- Scope-Paths:` is a declaration the runner reconciles afterwards. If an out-of-scope edit is genuinely needed, make it and justify it with `--scope-reason <path>=<why>` at finalize (and `--scope-ack <path>=<why>` for a declared path left unmodified). Stop only on an unresolvable concurrent-edit conflict or a missing prerequisite symbol.
- **Honesty rule**: you MUST paste the ACTUAL runner output into each `V-*` item's `Observed evidence:`; never claim a test passed without running it. Run the full suite bare as `python3 -m pytest` (never `-n0`, an extra `-q`, or `-p no:randomly`).
- **Commit and push**: commit only scoped files via `aw commit yd4tqw -- <paths>`; never `git add -A`, never push.
- **Lifecycle transition**: under `aw oc run` / `aw agy run` the runner owns `aw ipd finalize`; when executing by hand, finalize via `aw ipd finalize yd4tqw` once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` conforms. Never hand-roll a `git mv` to `executed/`.
