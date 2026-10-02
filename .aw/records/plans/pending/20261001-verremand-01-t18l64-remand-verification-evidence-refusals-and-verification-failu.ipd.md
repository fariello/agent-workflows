# IPD: Remand verification evidence refusals and verification failures back to the agent under retry conventions

- Date: 2026-10-01
- Kind: child
- Concern: In execute_item_core, independent verification failures (including verifier-no-test-evidence, unverified or failed verdicts, and missing outcome files) immediately transition to terminal disposition fail-verify, skipping turn retries and stranding lanes without remanding the issue back to the agent under the run's retry budget, which violates spec 25kzda Section 5.5's retryable class for missing or stale validation evidence.
- Scope: Introduce verification retry accounting and a pure verification retry decision helper in runner_shared.py following the proven finalize_retry_decision / turn_retry_decision pattern; record WHICH verification refusal occurred at each verifier failure site and perform the remand ONCE, after the rescore and before the silent-turn / integration gates, through handle_verification_refusal, so retryable verification refusals are remanded back to the agent in its lane as queued with recovery_next=True until the retry budget is exhausted; render the verification refusal into the recovery prompt through a dedicated notice that survives lane isolation; add outcome tests in tests/test_verification_sendback.py; and amend spec 25kzda Section 5.5's class-to-surface table to name the new classification surface.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, tests/test_verification_sendback.py, tests/test_oc_runipd.py, tests/test_defect_report.py, tests/test_inlane_retirement_lands.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: kw31r2
- From-Spec: 25kzda
- Blocks-Release: next
- Set: verremand
- Order: 1
- Highest E allocated: 06
- Author: antigravity
- Id: t18l64
- Approval: 2026-10-02, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-02 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): /plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 (HIGH), PR-005..PR-008 (MEDIUM), PR-009 (LOW), all FIXED. Findings and five decision rows in .aw/records/reviews/20261001-verremand-01-t18l64-remand-verification-evidence-refusals-and-verification-failu.review.md.

- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH), PR-002 (HIGH), PR-003 (HIGH), PR-004 (HIGH), PR-005 (MEDIUM), PR-006 (MEDIUM), PR-007 (MEDIUM), PR-008 (MEDIUM), PR-009 (LOW), all FIXED. Findings and five decision rows in `.aw/records/reviews/20261001-verremand-01-t18l64-remand-verification-evidence-refusals-and-verification-failu.review.md`. THE PLAN'S PREMISE HOLDS: measured by direct call, `has_verifier_test_evidence` rejects a bare nodeid `tests/test_status_set.py::SetterRefusalRetryCommandTests::test_case_a` and accepts `python3 -m pytest ...`, `turn_failure_is_retryable({}, 'fail-verify')` returns `False`, and spec 25kzda 5.5 lists "missing or stale validation evidence" as retryable. THE MECHANISM DID NOT HOLD AND WAS REWRITTEN. PR-001: E-01's retryable code tuple contained `"unverified"` and `"verify-failed"`, which are NOT refusal codes (the verdict-rejection code is `verifier-declined`, `VERDICT_REFUSAL_CODE_DECLINED`), so the actual CORRECTION_REQUIRED rejection would never have been retried; and it did not separate `BLOCKED` (verifier could not finish, an environment fact) from `CORRECTION_REQUIRED` (fixable work). PR-002: E-02 placed the remand INSIDE `_run_verifier_turn`, but `execute_item_core` overwrites `item["status"] = disposition` straight after that call and `_run_verifier_turn` runs a SECOND time on the rescore path, so the requeue would be erased and could double-spend; the remand is now ONE call sited after the rescore and before the silent-turn gate. PR-003: `fail-verify` is non-retryable in `TURN_RETRY_CLASSIFICATION`, so after the remand `handle_turn_failure_retry` would see `queued` and skip, which is correct, but the plan never named the interaction or the lane-preservation ordering. PR-004: three shipped tests (`tests/test_oc_runipd.py` verifier gate and unreadable-verdict tests, `tests/test_defect_report.py` rescore controls, `tests/test_inlane_retirement_lands.py`) pin `fail-verify` under the DEFAULT budget of 2 and will break; they were undeclared. PR-005: the delivery channel through `_PRIOR_ATTEMPT_SAFE_KEYS` alone repeats the exact shape `build_correction_notice`'s docstring measured inert; a dedicated `build_verification_refusal_notice` is required. PR-006: spec 25kzda 5.5's table names only two classification surfaces; adding a third without amending it leaves the spec contradicting the code. PR-007: the verifier writes to a FIXED path `NN-<id6>-verification.json` that is never cleared, so a remanded retry whose verifier crashes would re-read the stale prior verdict. PR-008: the plan carried two deferral rows with no carrier (flagged `error` by `check.ipd-uncarried-obligation`) and a non-conformant execution contract. PR-009: V-04 demanded host symmetry "tested", which must be shown on both hosts by driving `execute_item` rather than by inspection. Structural preflight `aw ipd lint` conforming at `author` before revision and at `review-finalize` after.
- 2026-10-01 to-review (antigravity): authored plan graduating backlog kw31r2. Every code claim verified against agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, and measured run run-20260930T233959Z-250047.

## Goal

Ensure that verification failures the executing agent can fix, namely missing verification evidence (`verifier-no-test-evidence`), a recognized verifier REJECTION (`CORRECTION_REQUIRED`, refusal code `verifier-declined`), an unreadable verdict (`verifier-verdict-unreadable`), and a verifier that wrote no outcome file (`verification-never-recorded`), are remanded back to the executing agent in its lane under the run's configured retry budget (`--retry-budget`), following the established retry and remand conventions rather than terminating immediately as unretryable `fail-verify`. When the budget is exhausted the item ends `fail-verify` exactly as today, so the terminal vocabulary is unchanged.

Non-goals: retrying a `BLOCKED`/`NOT CONFORMING` verdict (the verifier could not complete, an environment fact repetition cannot fix), changing the interrupted-verifier (`verification-interrupted`) or unresolvable-plan (`verification-not-attempted`) arms, which already write `partial` and are owned elsewhere, and changing `has_verifier_test_evidence`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: verification retry decision and accounting

- [x] E-01 Add the PURE verification retry classification and decision to `agent_workflows/runner_shared.py`, sited beside `turn_retry_decision`. Define `VERIFICATION_RETRY_COUNT_KEY = "verification_retry_attempts"` (a SEPARATE counter, per spec 5.5 "separately for each action", exactly as `FINALIZE_RETRY_COUNT_KEY` and `TURN_RETRY_COUNT_KEY` are separate), `VERIFICATION_RETRY_KEYS_KEY = "verification_retry_keys"`, `VERIFICATION_RETRY_EXHAUSTED_STATUS = "fail-verify"` (REUSED, never a new status, because `runner_shutdown.KNOWN_ITEM_STATUSES` is a closed vocabulary), `VERIFICATION_REFUSED_KEY = "verification_refused"`, and `VERIFICATION_RETRYABLE_REFUSAL_CODES = frozenset({VERIFY_REFUSAL_CODE_UNEVIDENCED, VERDICT_REFUSAL_CODE_UNREADABLE, VERIFY_ABSENCE_NO_OUTCOME_FILE})` PLUS a recognized-rejection arm keyed on the verdict MAPPING, not on the code string: `VERDICT_REFUSAL_CODE_DECLINED` is retryable ONLY when the recorded `verify_disp` is `VERIFY_DISP_UNVERIFIED` (a `CORRECTION_REQUIRED` rejection), and is NOT retryable when it is `VERIFY_DISP_BLOCKED` (`BLOCKED`/`NOT CONFORMING`), because `verdict_refusal_text` returns the same `verifier-declined` code for both and only the disposition distinguishes them. Implement `verification_retry_attempts(item) -> int` (never negative, bool-safe, mirroring `turn_retry_attempts`), `verification_failure_is_retryable(item, refusal_code, verify_disp) -> tuple[bool, str]` (FAIL-CLOSED allowlist; refuses a `stopped` record with `stopped_deliberately`, refuses an item carrying `finalize_refusal`, refuses any code not in the allowlist with a reason naming it), and `verification_retry_decision(item, state, refusal_code, verify_disp, attempt_no) -> VerificationRetryDecision`, a `NamedTuple` (matching `TurnRetryDecision`, not a dataclass) with `retry`, `exhausted`, `reason`, `attempts`, `budget`, `key`. The key is `f"{id6}:verify-attempt-{attempt_no}"` and an already-spent key returns neither retry nor exhausted (idempotency, as `turn_retry_key_already_spent`). Budget is read ONLY through `frozen_retry_budget(state)`; `used >= budget` is exhausted, so budget `0` exhausts on the first refusal.
  - Depends on: none
  - Expected outcome: a pure, side-effect-free decision whose three outcomes (retry, exhausted, neither) are determined by the refusal class, the recorded `verify_disp`, the separate counter, the idempotency key, and the frozen budget, and which classifies `BLOCKED` as not retryable while classifying `CORRECTION_REQUIRED` as retryable.
  - Execution state: performed

### Task group 2: verification failure routing and remand mechanism

- [x] E-02 Make every NON-retry-performing verifier failure arm inside `_run_verifier_turn` RECORD which refusal occurred, without changing its disposition: at the no-evidence arm (`verify_disp == VERIFY_DISP_VERIFIED and not v_has_evidence`), the non-verified verdict arm (`verify_disp != VERIFY_DISP_VERIFIED`, both the recognized and the unreadable sub-case), and the no-outcome-file arm, write `attempt[VERIFICATION_REFUSED_KEY] = {"code": v_code, "reason": v_reason, "remedy": v_remedy, "verify_disp": verify_disp}` beside the existing `record_refusal` call. These arms keep setting `disposition = "fail-verify"` exactly as today. Leave the `StallTimeout` arm and the `DriverError` plan-unresolvable arm untouched (they write `partial` and are non-goals). Then, BEFORE the verifier is spawned (immediately after `v_outcome_file` is computed and before `spawn_verifier` is called), delete a pre-existing outcome file with `v_outcome_file.unlink(missing_ok=True)` so a re-verification cannot re-read the PREVIOUS attempt's verdict when the new verifier writes nothing (the verifier writes to a fixed `NN-<id6>-verification.json` that nothing else clears).
  - Depends on: E-01
  - Expected outcome: every retryable verification failure leaves a structured `verification_refused` record on the CURRENT attempt naming its code, reason, remedy and `verify_disp`; no disposition changes inside `_run_verifier_turn`; and a re-run verifier that writes nothing is classified `verification-never-recorded` rather than inheriting a stale verdict.
  - Execution state: performed

- [x] E-03 Implement `handle_verification_refusal(*, run_dir, state, item, attempt, attempt_no, disposition, host_labels, save_state, append_jsonl) -> str` in `agent_workflows/runner_shared.py`, mirroring `handle_turn_failure_retry`, and call it EXACTLY ONCE in `execute_item_core`: AFTER the reaskscore rescore block (so it sees the FINAL `_run_verifier_turn` result even when the verifier ran twice) and BEFORE the `turn_attempted_nothing` silent-turn block and the `integration_gate_relevant` computation, guarded by `not is_review and not is_production and disposition == "fail-verify" and attempt.get(VERIFICATION_REFUSED_KEY)`. Its returned disposition must be assigned to the local `disposition` AND to `attempt["disposition"]` and `item["status"]`, so the later unconditional `item["status"] = disposition` cannot erase it. Behavior: on `decision.retry`, increment `item[VERIFICATION_RETRY_COUNT_KEY] = decision.attempts + 1`, append the key to `item[VERIFICATION_RETRY_KEYS_KEY]`, call `invalidate_turn_evidence(item, attempt_no, decision.reason)` (spec 5.5: "invalidates stale evidence from earlier attempts"), set `item["status"] = "queued"`, `item["recovery_next"] = True`, `item["requeue_from_status"] = "fail-verify"`, record a `Refusal` through `record_refusal` with code `verification-sent-back` and a remedy saying no action is needed yet, `save_state`, append event `verification-sent-back` carrying `id6`, `refusal_code`, `retry_attempts_used`, `retry_budget`, `idempotency_key`, and return `"queued"`. On `decision.exhausted`, keep `item["status"] = "fail-verify"`, pop `recovery_next`, record a `Refusal` with code `verification-retry-exhausted` whose remedy names `aw runs show <run-id>` and the preserved lane, append event `verification-retry-exhausted`, and return `"fail-verify"`. On neither, record `attempt["verification_retry_skipped"] = decision.reason` and return `disposition` UNCHANGED (the existing `Refusal` from the verifier arm stays). The remanded `queued` item then flows through the existing gates as follows, which the executor must confirm rather than re-derive: `turn_attempted_nothing` is not entered for `queued`; `integration_gate_relevant` is False because `queued` is not in its disposition tuple; the lane-preservation block runs because `item["status"] != "executed"`, so the lane is recorded preserved and the recovery turn's `route_recovery_turn` / `build_verify_and_continue_notice` points the agent at it; and `handle_turn_failure_retry` sees `queued`, classifies it not retryable, and returns it unchanged, so no double spend.
  - Depends on: E-01, E-02
  - Expected outcome: a retryable verification refusal with budget remaining leaves the item `queued` with `recovery_next = True` after `execute_item_core` returns, on both hosts; an exhausted or non-retryable refusal leaves it `fail-verify` with today's `Refusal`; the counter never exceeds the frozen budget, and a verifier run twice in one attempt (rescore path) spends at most one unit.
  - Execution state: performed

### Task group 3: recovery prompt context and lane containment

- [x] E-04 Deliver the verification refusal to the recovery turn through a DEDICATED notice, `build_verification_refusal_notice(item, recovery) -> str` in `agent_workflows/runner_shared.py`, concatenated into `build_prompt`'s `correction_notice` beside `build_correction_notice` and `build_stale_receipt_notice`. It returns `""` unless `recovery` is True AND the LAST attempt carries a `verification_refused` mapping, so every first-attempt prompt and every other recovery prompt is byte-identical to before. The block states: the verifier refusal code, the reason and the remedy (each passed through `render_stream._redact_absolute_paths` or the equivalent redaction `record_refusal` applies, so no absolute host path reaches the worker); that this is correction attempt N of M; that the lane already holds the prior work, so the agent must FIX the cause rather than re-implement; and, for `verifier-no-test-evidence`, that `tests_run` entries must be the COMMAND STRINGS that were run (for example `python3 -m pytest tests/test_x.py`), not test nodeids. Additionally add `"verification_refused"` to `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` with a one-line comment that it carries only code/reason/remedy/verify_disp text already redacted by `record_refusal`'s rule, so the `Prior attempt:` JSON also carries it in isolated lanes.
  - Depends on: E-02
  - Expected outcome: a recovery prompt rendered for an isolated lane (`lane_root` set) after a verification remand contains the refusal code, reason, remedy and the attempt bound, and contains no absolute path outside the lane; first-attempt prompts are unchanged.
  - Execution state: performed

### Task group 4: test coverage, spec sync, and regression fence

- [x] E-05 Author outcome tests in `tests/test_verification_sendback.py` and reconcile the shipped tests that pin the old behavior. New tests, each driving real functions and asserting returned values or resulting state: (1) `verification_retry_decision` returns `retry=True` below budget, `exhausted=True` at budget, `exhausted=True` on the first refusal when budget is `0`, neither for a `verifier-declined` refusal with `verify_disp="blocked"`, `retry=True` for `verifier-declined` with `verify_disp="unverified"`, neither for an already-spent key, and neither when the item carries a deliberate `stopped` record; (2) END-TO-END on BOTH hosts (`oc_runipd` with `run_opencode`, `agy_runipd` with `run_agy_turn`, following the `_HOSTS` pattern in `tests/test_inlane_retirement_lands.py`), driving `execute_item` with a committed lane change and a verification outcome of `{"verdict": "VERIFIED", "tests_run": ["tests/test_status_set.py::SetterRefusalRetryCommandTests::test_case_a"]}` under `retry_budget` 2: the item ends `queued` with `recovery_next` True, `verification_retry_attempts == 1`, `events.jsonl` contains one `verification-sent-back` event, and `driver_finalize` was not called; (3) the same drive under `retry_budget` 0 ends `fail-verify` with the `verifier-no-test-evidence` refusal recorded; (4) the same drive with `CORRECTION_REQUIRED` remands, and with `BLOCKED` ends `fail-verify` with no `verification-sent-back` event; (5) a stale-verdict case: a pre-existing `VERIFIED` verification outcome file plus a verifier that writes nothing yields `verification-never-recorded`, not `verified`; (6) a rendered recovery prompt (`build_prompt(..., recovery=True, lane_root=<lane>)`) for both host label sets contains the refusal code, the remedy and the command-string guidance, and `lane_containment.prior_attempt_summary(attempt, lane_root)` retains `verification_refused`. Reconcile: in `tests/test_oc_runipd.py` (`test_verifier_gate`, `test_an_unreadable_verdict_file_fails_closed_end_to_end`), `tests/test_defect_report.py` (the rescore controls asserting `fail-verify`), and `tests/test_inlane_retirement_lands.py` (`test_unverified_retirement_does_not_land`), pin `"retry_budget": 0` in the test state's `options` where the test's subject is the terminal refusal (so it keeps asserting today's terminal behavior), and do NOT weaken any finalize-not-called or not-landed assertion. Re-derive at execution which of these tests actually break rather than trusting this list; a test that does not break needs no edit and its path is `--scope-ack`ed.
  - Depends on: E-03, E-04
  - Expected outcome: a new test module whose cases fail if the remand, the BLOCKED exclusion, the zero budget, the stale-file clearing, or the prompt delivery is removed; and the reconciled shipped tests still assert the terminal refusal under an explicit zero budget.
  - Execution state: performed

- [x] E-06 Amend spec 25kzda Section 5.5 and run the validation. In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.5: add a third bullet to "The runner provides two distinct classification surfaces" (renaming it "three") for `verification_retry_decision`, which classifies a refused independent verification by its refusal code and recorded verdict disposition; and change the `missing or stale validation evidence` table row so its Classification Surface names both `finalize_retry_decision` (at finalize) and `verification_retry_decision` (at verification, disposition `fail-verify`), with a note that a `BLOCKED` verdict is not retried. Do NOT change the normative bound sentence (`must be an integer from 0 through 10 inclusive`), which `tests/test_retry_budget_citation.py` anchors. Then run `python3 -m pytest tests/test_verification_sendback.py tests/test_verifier_evidence.py tests/test_finalize_sendback.py tests/test_retry_class_mapping.py tests/test_retry_budget_citation.py tests/test_oc_runipd.py tests/test_defect_report.py tests/test_inlane_retirement_lands.py`, then the BARE suite `python3 -m pytest`, then `aw sanitize --agent`, then `aw ipd lint --phase pre-transition --agent <this plan>`.
  - Depends on: E-05
  - Expected outcome: spec 5.5 names the new classification surface and still contains the anchored bound sentence exactly once; every named module and the bare suite pass; the sanitizer exits 0; and pre-transition lint conforms.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Finalize and turn sendback precedent: `runner_shared.handle_finalize_refusal` / `finalize_retry_decision` and `runner_shared.handle_turn_failure_retry` / `turn_retry_decision` establish the pattern: a PURE `NamedTuple` decision, a separate per-item counter key, an idempotency key, `frozen_retry_budget(state)`, re-queueing with `item["status"] = "queued"` and `item["recovery_next"] = True`, a `Refusal` via `record_refusal`, and a named event.
- The performer must RETURN the disposition and be sited where the run learns of the failure but BEFORE any later unconditional overwrite: `execute_item_core` writes `item["status"] = disposition` right after `_run_verifier_turn` and again right before the auto-approve block, which is exactly why `handle_turn_failure_retry`'s comment requires its return value to be assigned rather than relying on the status it writes.
- `_run_verifier_turn` can run TWICE per attempt: once for the first score and once on the reaskscore rescore path (`disposition, verify_disp = _run_verifier_turn(disposition)` inside the `rescore_is_an_improvement` branch). A remand inside it would therefore be evaluated twice and overwritten once.
- Isolated worktree containment: `lane_containment.prior_attempt_summary` filters prior attempt keys through `_PRIOR_ATTEMPT_SAFE_KEYS`. `build_correction_notice`'s docstring records that a packet carried ONLY by `Prior attempt:` was MEASURED inert on the default isolated path; a dedicated notice rendered by `build_prompt` is the shipped remedy.
- Retry budget precedence: Spec `25kzda` Section 5.5 is the normative home for the 0..10 bound and three-tier precedence. The budget is frozen at run initialization and read via `runner_shared.frozen_retry_budget(state)`; `0` is legal and means fail on the first refusal.
- Verification refusal vocabulary (measured by direct call): `VERIFY_REFUSAL_CODE_UNEVIDENCED == "verifier-no-test-evidence"`, `VERDICT_REFUSAL_CODE_DECLINED == "verifier-declined"` (returned for BOTH `CORRECTION_REQUIRED` and `BLOCKED`), `VERDICT_REFUSAL_CODE_UNREADABLE == VERIFY_ABSENCE_VERDICT_UNREADABLE == "verifier-verdict-unreadable"`, `VERIFY_ABSENCE_NO_OUTCOME_FILE == "verification-never-recorded"`. `map_verdict("BLOCKED").verify_disp == "blocked"`, `map_verdict("CORRECTION_REQUIRED").verify_disp == "unverified"`. `"unverified"` and `"verify-failed"` are `verify_disp` / render tokens, NOT refusal codes.
- `fail-verify` is a member of `TERMINAL_STATES` and `KNOWN_ITEM_STATUSES`; `queued` is in `KNOWN_ITEM_STATUSES` and not terminal, so a remanded item is reconsidered by orchestrator dispatch rather than declaring its Set dead.

## Findings

| Finding | Summary | Citation / Measurement |
| :--- | :--- | :--- |
| F-01 | **VERIFICATION FAILURES ARE CURRENTLY ABANDONED WITHOUT RETRY:** When verification fails (`verifier-no-test-evidence`, a non-`verified` verdict, or no outcome file), `_run_verifier_turn` sets `disposition = "fail-verify"`, and `handle_turn_failure_retry` then records `turn_retry_skipped` because `TURN_RETRY_CLASSIFICATION` marks `fail-verify` non-retryable (measured: `turn_failure_is_retryable({}, 'fail-verify')` returns `(False, "disposition 'fail-verify' is not retryable: ...")`). The item ends terminal and its lane is preserved but never re-dispatched. | `runner_shared.execute_item_core` (`_run_verifier_turn`), `runner_shared.TURN_RETRY_CLASSIFICATION` row `"fail-verify"`, `runner_shared.handle_turn_failure_retry` |
| F-02 | **SPEC 25kzda SECTION 5.5 PERMITS RETRYING VALIDATION EVIDENCE FAILURES:** "The engine may spend budget only on failures classified as retryable: ... missing or stale validation evidence; ...". Its class-to-surface table currently routes that class ONLY through `finalize_retry_decision`, so the verification surface is unimplemented AND unnamed in the spec. Section 4.2's `RUN-FRESH-VERIFIER` row also prescribes `RETRY, then FAIL ITEM` for a missing verification, and the `VERIFY_ABSENCE_NO_OUTCOME_FILE` comment states "The spec's RETRY half is NOT implemented here". | Spec `25kzda` Section 5.5 bullet "missing or stale validation evidence" and its table row; Section 4.2 `RUN-FRESH-VERIFIER`; comment above `runner_shared.VERIFY_ABSENCE_NO_OUTCOME_FILE` |
| F-03 | **LANE CONTAINMENT DROPS REFUSAL CONTEXT IN ISOLATED WORKTREES UNLESS DELIVERED SEPARATELY:** `prior_attempt_summary` projects `_PRIOR_ATTEMPT_SAFE_KEYS` for an isolated turn; verification refusal data is absent. `build_correction_notice`'s docstring records that relying on `Prior attempt:` alone was measured INERT on the default path, so a dedicated notice is required, with the allowlist entry as a secondary carrier. | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`, `lane_containment.prior_attempt_summary`, `runner_shared.build_correction_notice` docstring |
| F-04 | **RE-QUEUE PATTERN IS ALREADY SHARED AND PROVEN:** `item["status"] = "queued"`, `item["recovery_next"] = True`, `item["requeue_from_status"] = disposition` is consumed by both hosts' `run_queue` (`recovery = bool(runnable.pop("recovery_next", False))` in `oc_runipd.py` and `agy_runipd.py`). | `runner_shared.handle_finalize_refusal`, `runner_shared.handle_turn_failure_retry`, `oc_runipd.run_queue`, `agy_runipd.run_queue` |
| F-05 | **MEASURED STRANDING IN PRODUCTION:** In run `run-20260930T233959Z-250047`, item `5poaqh` (Set `pftva5`) passed its tests and lint, but the verifier wrote test nodeids instead of commands in `tests_run`, so the runner refused it with `verifier-no-test-evidence` and stranded the lane. The run directory is gitignored (`.aw/.gitignore` `records/runs/`) and not present in this worktree, so the claim rests on backlog `kw31r2`'s record; the MECHANISM is re-measured here: `has_verifier_test_evidence({"tests_run": ["tests/test_status_set.py::SetterRefusalRetryCommandTests::test_case_a"]})` is `False` and `has_verifier_test_evidence({"tests_run": ["python3 -m pytest tests/test_status_set.py"]})` is `True`. | backlog `kw31r2`; `runner_shared.has_verifier_test_evidence`, `runner_shared.is_command_like` |
| F-06 | **ADDED AT REVIEW (PR-001). THE REJECTION CODE IS `verifier-declined`, NOT `unverified`, AND IT IS SHARED BY TWO DIFFERENT FACTS.** `verdict_refusal_text` returns `VERDICT_REFUSAL_CODE_DECLINED` for BOTH a recognized `CORRECTION_REQUIRED` (`verify_disp="unverified"`, fixable work) and a `BLOCKED`/`NOT CONFORMING` verdict (`verify_disp="blocked"`, the verifier could not complete). Only the recorded `verify_disp` distinguishes them, so classification must key on it. | `runner_shared.verdict_refusal_text`, `runner_shared._VERDICT_TABLE`, `runner_shared.VERDICT_REFUSAL_CODE_DECLINED` |
| F-07 | **ADDED AT REVIEW (PR-002). THE REMAND CANNOT LIVE INSIDE `_run_verifier_turn`.** Directly after the first call, `execute_item_core` writes `item["status"] = disposition` from the local, and on the rescore path it calls `_run_verifier_turn` a second time and writes the result again. A requeue written inside the helper would be overwritten unless its disposition is returned, and would be evaluated twice per attempt. | `runner_shared.execute_item_core`: `disposition, verify_disp = _run_verifier_turn(disposition)` followed by `item["status"] = disposition`; the second `_run_verifier_turn(disposition)` call in the `rescore_is_an_improvement` branch |
| F-08 | **ADDED AT REVIEW (PR-007). THE VERIFICATION OUTCOME PATH IS FIXED AND NEVER CLEARED.** Both `build_verifier_prompt` and `_run_verifier_turn` use `outcomes/NN-<id6>-verification.json` with no attempt number, and no code unlinks it. A remanded retry whose verifier writes nothing would therefore read the PREVIOUS attempt's verdict; with a stale `VERIFIED` plus valid evidence, that would integrate an unverified correction. | `runner_shared.build_verifier_prompt` (`verify_outcome`), `runner_shared._run_verifier_turn` (`v_outcome_file`); no `unlink` of either in `runner_shared.py` |
| F-09 | **ADDED AT REVIEW (PR-004). SHIPPED TESTS PIN TODAY'S TERMINAL BEHAVIOR UNDER THE DEFAULT BUDGET.** `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_verifier_gate` and `test_an_unreadable_verdict_file_fails_closed_end_to_end` assert `item["status"] == "fail-verify"` with no `retry_budget` in options (so `frozen_retry_budget` resolves to 2); `tests/test_defect_report.py` rescore controls and `tests/test_inlane_retirement_lands.py::test_unverified_retirement_does_not_land` assert the terminal outcome on similar fixtures. These are candidate breakages to re-derive at execution. | named tests; `frozen_retry_budget({})` returns `2` |

## Proposed changes (ordered, validatable)

1. E-01: pure classification and decision (`verification_failure_is_retryable`, `verification_retry_decision`, `VerificationRetryDecision`) with a separate counter and idempotency key, BLOCKED excluded.
2. E-02: record `verification_refused` on the attempt at each retryable verifier arm without changing disposition; clear the stale verification outcome file before spawning the verifier.
3. E-03: `handle_verification_refusal`, called once after the rescore and before the silent-turn and integration gates, returning the disposition the caller assigns.
4. E-04: `build_verification_refusal_notice` rendered by `build_prompt`; `verification_refused` added to `_PRIOR_ATTEMPT_SAFE_KEYS`.
5. E-05: new outcome tests on both hosts; reconcile shipped tests by pinning `retry_budget: 0` where the terminal refusal is the subject.
6. E-06: amend spec 25kzda 5.5's classification-surface list and table row; run named modules, bare suite, sanitizer, pre-transition lint.

## Deferred / out of scope (with reason)

- In-session verifier re-prompting: re-prompting the verifier agent within the same session for a malformed `tests_run` is deferred. Remanding to the executing agent in its lane follows the backlog item's instruction, works in both isolated and non-isolated modes, and addresses code/test failures as well as evidence gaps.
  - Carrier-Declined: no work is owed. This is a design choice recorded for the reviewer; the remand delivered here covers the measured case, and no defect remains that an item would describe.
- Altering the `has_verifier_test_evidence` predicate: its command-like content requirement (plan `bxx9af`) remains untouched; the measured defect is the missing remand, not the predicate.
  - Carrier-Declined: no work is owed. The predicate is correct as shipped; the agent is told in E-04's notice how to satisfy it.
- Retrying a `BLOCKED`/`NOT CONFORMING` verdict, a killed verifier turn (`verification-interrupted`) or an unresolvable plan path (`verification-not-attempted`): the first is an environment fact repetition cannot fix, and the other two already write `partial` and are owned by the zero-work / interrupt recovery routes.
  - Carrier-Declined: no work is owed. Each class has an existing owner or is deliberately non-retryable per spec 5.5's construction.

## Scope check

- Over-scope: none. Changes are confined to runner verification retry accounting, the verifier refusal recording, one performer call site, one prompt notice, one allowlist entry, tests, and the spec 5.5 surface table.
- Under-scope: none after review. Both OpenCode and Antigravity runners inherit the behavior via the shared `execute_item_core`, and E-05 drives both. The three shipped test paths and the spec path are declared because PR-004 and PR-006 measured that they must change; a declared path that does not change at execution is `--scope-ack`ed at finalize.

## Required tests / validation

- Named modules: `python3 -m pytest tests/test_verification_sendback.py tests/test_verifier_evidence.py tests/test_finalize_sendback.py tests/test_retry_class_mapping.py tests/test_retry_budget_citation.py tests/test_oc_runipd.py tests/test_defect_report.py tests/test_inlane_retirement_lands.py`.
- Bare suite: `python3 -m pytest` (no added flags). The collected count is a live population; compare against a baseline the executor measures before E-01, not against any number in this plan.
- Behaviors pinned (each by an outcome assertion, not by source inspection): retry below budget; exhaust at budget and at budget 0; BLOCKED not retried; CORRECTION_REQUIRED retried; idempotent key; deliberate stop refused; end-to-end remand on both hosts with `driver_finalize` not called; stale verification file not re-read; recovery prompt carries code, remedy and command-string guidance with no out-of-lane path.
- Leak check: `aw sanitize --agent` exits 0.
- Lint conformance: `aw ipd lint --phase pre-transition --agent` conforming.

## Spec / documentation sync

Spec `25kzda` Section 5.5 already lists `missing or stale validation evidence` as retryable, so the BEHAVIOR is conformance, not a new policy. But Section 5.5 also declares the runner's classification surfaces ("two distinct classification surfaces") and a class-to-surface table whose `missing or stale validation evidence` row names only `finalize_retry_decision`. Adding `verification_retry_decision` without amending that text would leave the approved spec asserting a surface list the code contradicts, so E-06 amends it in the same change. WHY: the spec is the contract other plans are reviewed against, and a reviewer reading 5.5 must be able to find the third surface. The amendment is additive (a third bullet and a widened table cell plus a BLOCKED note); the normative bound sentence anchored by `tests/test_retry_budget_citation.py` is not touched. The spec path is listed in `Scope-Paths` so both runners announce the declared spec edit. No user-facing documentation changes.

## Open questions

### OQ-01: Should verification retry budget share `--retry-budget` or introduce a separate knob?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY CONVENTIONS AND SPEC 25kzda 5.5: Share `--retry-budget`. The maintainer ruled against a second retry knob ("share it, add no second knob", 2026-09-20, recorded in executed plan `ounhsn`'s Step 0 conventions), and Spec 25kzda 5.5 designates `--retry-budget` as the single normative budget, counted "separately for each action", which is why E-01 uses a SEPARATE counter key over the SHARED budget.

### OQ-02: Should `verification_refused` replace or complement `finalize_refused` in recovery notices?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: Complement. An item can hit a verification refusal on attempt 1 and a finalize refusal on attempt 2, or vice versa; they are distinct lifecycle stages. Each notice reads only the LAST attempt's own key, so at most the refusal that actually ended the prior attempt is rendered. Re-owned at review from `antigravity` to `plan author` because no maintainer answer is recorded; the reviewer's concurrence is decision row D-5 in the review record.

### OQ-03: Should a `BLOCKED` verifier verdict be remanded to the executing agent?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM REPOSITORY EVIDENCE: No. `verdict_refusal_text` describes `BLOCKED` as "it could not complete the verification" with remedy "resolve that obstacle, then re-run this item", an environment or tooling fact rather than fixable work, and spec 5.5 permits spend "only on failures classified as retryable", a positive allowlist. `CORRECTION_REQUIRED` is the verifier's explicit statement that the work needs correcting, which is exactly what a remand serves. Demonstrated by direct call: `map_verdict("BLOCKED").verify_disp == "blocked"` and `map_verdict("CORRECTION_REQUIRED").verify_disp == "unverified"`, so the two are distinguishable by the recorded value E-02 stores. Reversible: a later plan can widen the allowlist by one entry. Recorded as decision D-1.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff adding `VerificationRetryDecision`, `verification_retry_attempts`, `verification_failure_is_retryable`, `verification_retry_decision` and the constants. Paste test output from `tests/test_verification_sendback.py` for the decision cases: retry below budget, exhausted at budget, exhausted on first refusal at budget 0, BLOCKED (`verify_disp="blocked"`) neither retried nor exhausted, CORRECTION_REQUIRED (`verify_disp="unverified"`) retried, already-spent key neither, deliberate stop refused. Paste a direct-call transcript showing `verification_retry_decision` returns each of the three outcome shapes for a concrete item and state.
  - Observed evidence: Added VerificationRetryDecision, helpers, constants to runner_shared.py; test_decision_cases passed; direct call transcript verified.
    Added constants and helper functions to `agent_workflows/runner_shared.py`:
    ```diff
    +#: Separate counter key for verification retry attempts.
    +VERIFICATION_RETRY_COUNT_KEY: str = "verification_retry_attempts"
    +
    +#: Idempotency keys spent for verification retries.
    +VERIFICATION_RETRY_KEYS_KEY: str = "verification_retry_keys"
    +
    +#: Terminal status reached when verification retry budget is exhausted.
    +VERIFICATION_RETRY_EXHAUSTED_STATUS: str = "fail-verify"
    +
    +#: Attempt-level key recording the structured verification refusal.
    +VERIFICATION_REFUSED_KEY: str = "verification_refused"
    +
    +#: Refusal code recorded on verification sendback.
    +VERIFICATION_RETRY_REFUSAL_CODE: str = "verification-sent-back"
    +
    +#: Refusal code recorded when verification retry budget is exhausted.
    +VERIFICATION_RETRY_EXHAUSTED_CODE: str = "verification-retry-exhausted"
    +
    +#: Retryable verification refusal codes.
    +VERIFICATION_RETRYABLE_REFUSAL_CODES: frozenset[str] = frozenset(
    +    {
    +        VERIFY_REFUSAL_CODE_UNEVIDENCED,
    +        VERDICT_REFUSAL_CODE_UNREADABLE,
    +        VERIFY_ABSENCE_NO_OUTCOME_FILE,
    +    }
    +)
    +
    +
    +def verification_retry_attempts(item: Mapping[str, Any]) -> int:
    +    """How many VERIFICATION corrections this item has already consumed. Never negative."""
    +    raw = item.get(VERIFICATION_RETRY_COUNT_KEY)
    +    if isinstance(raw, bool) or not isinstance(raw, int):
    +        return 0
    +    return max(0, raw)
    +
    +
    +def verification_retry_idempotency_key(
    +    item: Mapping[str, Any], attempt_no: int
    +) -> str:
    +    """The key identifying ONE verification correction, so a repeated decision cannot double-spend."""
    +    return f"{item.get('id6') or '?'}:verify-attempt-{int(attempt_no)}"
    +
    +
    +def verification_retry_key_already_spent(item: Mapping[str, Any], key: str) -> bool:
    +    """Has this exact verification correction already been recorded?"""
    +    recorded = item.get(VERIFICATION_RETRY_KEYS_KEY)
    +    return isinstance(recorded, list) and key in recorded
    +
    +
    +def verification_failure_is_retryable(
    +    item: Mapping[str, Any], refusal_code: str, verify_disp: str | None = None
    +) -> tuple[bool, str]:
    +    """Is this verification refusal in the retryable class? Returns (retryable, why)."""
    +    stopped = item.get("stopped")
    +    if isinstance(stopped, Mapping) and stopped.get("stopped_deliberately"):
    +        return (
    +            False,
    +            "the turn ended in a DELIBERATE OPERATOR STOP, which is an intent and not a failure; "
    +            "retrying it would spend paid model turns fighting the operator",
    +        )
    +    if item.get("finalize_refusal"):
    +        return (
    +            False,
    +            "the turn's failure is a REFUSED FINALIZE, which the finalize send-back already "
    +            "classifies and already spends correction budget on (see `finalize_retry_decision`)",
    +        )
    +    code = (refusal_code or "").strip()
    +    disp = (verify_disp or "").strip() if verify_disp else None
    +    if code in VERIFICATION_RETRYABLE_REFUSAL_CODES:
    +        return (
    +            True,
    +            f"verification refusal code {code!r} is in spec 5.5's retryable validation-evidence class",
    +        )
    +    if code == VERDICT_REFUSAL_CODE_DECLINED:
    +        if disp == VERIFY_DISP_UNVERIFIED:
    +            return (
    +                True,
    +                f"verification refusal code {code!r} with verify_disp {disp!r} (CORRECTION_REQUIRED) "
    +                "is in spec 5.5's retryable validation-evidence class",
    +            )
    +        if disp == VERIFY_DISP_BLOCKED:
    +            return (
    +                False,
    +                f"verification refusal code {code!r} with verify_disp {disp!r} (BLOCKED/NOT CONFORMING) "
    +                "is not retryable: the verifier could not complete (environment/tooling obstacle)",
    +            )
    +        return (
    +            False,
    +            f"verification refusal code {code!r} with verify_disp {disp!r} is not retryable",
    +        )
    +    return (
    +        False,
    +        f"verification refusal code {code!r} is not in the retryable allowlist",
    +    )
    +
    +
    +class VerificationRetryDecision(NamedTuple):
    +    """What to do about ONE failed verification. DECIDES ONLY: no state write, no print, no dispatch."""
    +
    +    retry: bool
    +    exhausted: bool
    +    reason: str
    +    attempts: int
    +    budget: int
    +    key: str
    +
    +
    +def verification_retry_decision(
    +    item: Mapping[str, Any],
    +    state: Mapping[str, Any],
    +    refusal_code: str,
    +    verify_disp: str | None,
    +    attempt_no: int,
    +) -> VerificationRetryDecision:
    +    """Decide RETRY / FAIL-ITEM / LEAVE-ALONE for one failed verification."""
    +    used = verification_retry_attempts(item)
    +    budget = frozen_retry_budget(state)
    +    key = verification_retry_idempotency_key(item, attempt_no)
    +    retryable, why = verification_failure_is_retryable(item, refusal_code, verify_disp)
    +    if not retryable:
    +        return VerificationRetryDecision(
    +            retry=False,
    +            exhausted=False,
    +            reason=why,
    +            attempts=used,
    +            budget=budget,
    +            key=key,
    +        )
    +    if verification_retry_key_already_spent(item, key):
    +        return VerificationRetryDecision(
    +            retry=False,
    +            exhausted=False,
    +            reason=(
    +                f"verification correction {key} was ALREADY recorded for this item, so this decision spends "
    +                f"nothing (idempotency, as `plan_retry` guarantees for a repeated key)"
    +            ),
    +            attempts=used,
    +            budget=budget,
    +            key=key,
    +        )
    +    if used >= budget:
    +        return VerificationRetryDecision(
    +            retry=False,
    +            exhausted=True,
    +            reason=(
    +                f"verification failed ({refusal_code}) in a retryable class and the run's correction "
    +                f"budget is exhausted ({used} of {budget} correction attempt"
    +                f"{'' if budget == 1 else 's'} spent), so the item is FAILED rather than re-dispatched"
    +            ),
    +            attempts=used,
    +            budget=budget,
    +            key=key,
    +        )
    +    return VerificationRetryDecision(
    +        retry=True,
    +        exhausted=False,
    +        reason=(
    +            f"verification failed ({refusal_code}) in a retryable class, so the item is being handed back "
    +            f"for a bounded correction turn; correction attempt {used + 1} of {budget}"
    +        ),
    +        attempts=used,
    +        budget=budget,
    +        key=key,
    +    )
    ```
    Output from `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py -k test_decision_cases`:
    ```
    tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_decision_cases PASSED [100%]
    ======================= 1 passed, 5 deselected in 0.45s ========================
    ```
    Direct-call transcript demonstrating the three outcome shapes:
    ```
    >>> from agent_workflows import runner_shared
    >>> # 1. retry below budget:
    >>> item1 = {'id6': 'abc123', 'verification_retry_attempts': 0}
    >>> state = {'options': {'retry_budget': 2}}
    >>> d1 = runner_shared.verification_retry_decision(item1, state, runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED, None, attempt_no=1)
    >>> print('Case 1 (retry):', d1)
    Case 1 (retry): VerificationRetryDecision(retry=True, exhausted=False, reason='verification failed (verifier-no-test-evidence) in a retryable class, so the item is being handed back for a bounded correction turn; correction attempt 1 of 2', attempts=0, budget=2, key='abc123:verify-attempt-1')
    >>> # 2. exhausted at budget:
    >>> item2 = {'id6': 'abc123', 'verification_retry_attempts': 2}
    >>> d2 = runner_shared.verification_retry_decision(item2, state, runner_shared.VERIFY_REFUSAL_CODE_UNEVIDENCED, None, attempt_no=3)
    >>> print('Case 2 (exhausted):', d2)
    Case 2 (exhausted): VerificationRetryDecision(retry=False, exhausted=True, reason="verification failed (verifier-no-test-evidence) in a retryable class and the run's correction budget is exhausted (2 of 2 correction attempts spent), so the item is FAILED rather than re-dispatched", attempts=2, budget=2, key='abc123:verify-attempt-3')
    >>> # 3. neither (blocked / non-retryable):
    >>> item3 = {'id6': 'abc123', 'verification_retry_attempts': 0}
    >>> d3 = runner_shared.verification_retry_decision(item3, state, runner_shared.VERDICT_REFUSAL_CODE_DECLINED, runner_shared.VERIFY_DISP_BLOCKED, attempt_no=1)
    >>> print('Case 3 (neither):', d3)
    Case 3 (neither): VerificationRetryDecision(retry=False, exhausted=False, reason="verification refusal code 'verifier-declined' with verify_disp 'blocked' (BLOCKED/NOT CONFORMING) is not retryable: the verifier could not complete (environment/tooling obstacle)", attempts=0, budget=2, key='abc123:verify-attempt-1')
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of the three `_run_verifier_turn` arms showing `attempt["verification_refused"]` written beside the existing `record_refusal` and `disposition = "fail-verify"` unchanged, and the `unlink(missing_ok=True)` placed before `spawn_verifier`. Paste test output for the stale-verdict case: a pre-existing `VERIFIED` verification file plus a verifier that writes nothing yields refusal code `verification-never-recorded` and `verification_status` not `verified`.
  - Observed evidence: Added verification_refused to 3 arms, unlink before spawn; test_stale_verdict_clearing passed (1 passed).
    Diff in `agent_workflows/runner_shared.py`:
    ```diff
    @@ -32947,6 +33276,12 @@ def execute_item_core(
                             ),
                             flush=True,
                         )
    +                    v_outcome_file = (
    +                        run_dir
    +                        / "outcomes"
    +                        / f"{item['position']:02d}-{item['id6']}-verification.json"
    +                    )
    +                    v_outcome_file.unlink(missing_ok=True)
                         try:
                             v_rc, _v_session, _v_log, _v_argv = spawn_verifier(
                                 v_prompt_file,
    @@ -33102,6 +33432,12 @@ def execute_item_core(
                                     record_refusal(
                                         item, code=v_code, reason=v_reason, remedy=v_remedy
                                     )
    +                                attempt[VERIFICATION_REFUSED_KEY] = {
    +                                    "code": v_code,
    +                                    "reason": v_reason,
    +                                    "remedy": v_remedy,
    +                                    "verify_disp": verify_disp,
    +                                }
                                     print(
                                         pal(f"  ! IPD {item['id6']} {v_reason}", "yellow"),
                                         file=sys.stderr,
    @@ -33122,6 +33458,12 @@ def execute_item_core(
                                     record_refusal(
                                         item, code=v_code, reason=v_reason, remedy=v_remedy
                                     )
    +                                attempt[VERIFICATION_REFUSED_KEY] = {
    +                                    "code": v_code,
    +                                    "reason": v_reason,
    +                                    "remedy": v_remedy,
    +                                    "verify_disp": verify_disp,
    +                                }
                                     print(
                                         pal(f"  ! IPD {item['id6']} {v_reason}", "yellow"),
                                         file=sys.stderr,
    @@ -33169,16 +33511,23 @@ def execute_item_core(
                                 v_reason, v_remedy = verify_absence_text(
                                     VERIFY_ABSENCE_NO_OUTCOME_FILE
                                 )
    +                            v_code = VERIFY_ABSENCE_NO_OUTCOME_FILE
                                 record_refusal(
                                     item,
    -                                code=VERIFY_ABSENCE_NO_OUTCOME_FILE,
    +                                code=v_code,
                                     reason=v_reason,
                                     remedy=v_remedy,
                                 )
    -                            attempt["verify_absence"] = VERIFY_ABSENCE_NO_OUTCOME_FILE
    -                            item["verify_absence"] = VERIFY_ABSENCE_NO_OUTCOME_FILE
    +                            attempt["verify_absence"] = v_code
    +                            item["verify_absence"] = v_code
                                 verify_disp = VERIFY_DISP_UNVERIFIED
                                 disposition = "fail-verify"
    +                            attempt[VERIFICATION_REFUSED_KEY] = {
    +                                "code": v_code,
    +                                "reason": v_reason,
    +                                "remedy": v_remedy,
    +                                "verify_disp": verify_disp,
    +                            }
    ```
    Output from `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py -k test_stale_verdict_clearing`:
    ```
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_stale_verdict_clearing PASSED [100%]
    ======================= 1 passed, 5 deselected in 2.59s ========================
    ```
    Pre-existing `VERIFIED` outcome file is unlinked before `spawn_verifier`; when verifier writes nothing, refusal code is `verification-never-recorded` and `item["verification_status"]` is not `verified`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the source of `handle_verification_refusal` and the single call site in `execute_item_core`, showing it sits after the rescore block and before `turn_attempted_nothing`, and that its return is assigned to `disposition`, `attempt["disposition"]` and `item["status"]`. Paste end-to-end test output for BOTH hosts showing, for a `verifier-no-test-evidence` drive at `retry_budget` 2: final `item["status"] == "queued"`, `item["recovery_next"] is True`, `item["verification_retry_attempts"] == 1`, exactly one `verification-sent-back` event in `events.jsonl`, and `driver_finalize` not called; and at `retry_budget` 0: final status `fail-verify`. Paste the item's `attempts[-1]["turn_retry_skipped"]` showing `handle_turn_failure_retry` saw `queued` and did not spend the turn counter.
  - Observed evidence: handle_verification_refusal placed after rescore before turn_attempted_nothing; test_unevidenced_verification passed on both hosts (2 passed); turn_retry_skipped verified.
    Source of `handle_verification_refusal`:
    ```python
    def handle_verification_refusal(
        *,
        run_dir: Path,
        state: MutableMapping[str, Any],
        item: dict[str, Any],
        attempt: MutableMapping[str, Any],
        attempt_no: int,
        disposition: str,
        host_labels: "HostLabels | None",
        save_state: Callable[[Path, Any], Any],
        append_jsonl: Callable[..., Any],
    ) -> str:
        """PERFORM the outcome of one refused verification. Returns the item's disposition."""
        refused_data = attempt.get(VERIFICATION_REFUSED_KEY) or {}
        refusal_code = str(refused_data.get("code") or "")
        verify_disp = refused_data.get("verify_disp")

        decision = verification_retry_decision(
            item, state, refusal_code, verify_disp, attempt_no
        )
        if not (decision.retry or decision.exhausted):
            attempt["verification_retry_skipped"] = decision.reason
            return disposition

        pal = Palette(should_color(sys.stdout))
        command = getattr(host_labels, "command", None) or "aw oc run"
        if decision.retry:
            item[VERIFICATION_RETRY_COUNT_KEY] = decision.attempts + 1
            item.setdefault(VERIFICATION_RETRY_KEYS_KEY, []).append(decision.key)
            attempt[VERIFICATION_REFUSED_KEY]["attempt"] = decision.attempts + 1
            attempt[VERIFICATION_REFUSED_KEY]["budget"] = decision.budget
            invalidate_turn_evidence(item, attempt_no, decision.reason)
            item["status"] = "queued"
            item["recovery_next"] = True
            item["requeue_from_status"] = "fail-verify"
            record_refusal(
                item,
                code=VERIFICATION_RETRY_REFUSAL_CODE,
                reason=decision.reason,
                remedy=(
                    "no action needed yet: the run is handing this item back for a bounded correction turn "
                    "in this same run to address verification issues. Its work is preserved on its lane and "
                    "nothing was forced"
                ),
            )
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "verification-sent-back",
                    "id6": item["id6"],
                    "refusal_code": refusal_code,
                    "retry_attempts_used": decision.attempts + 1,
                    "retry_budget": decision.budget,
                    "idempotency_key": decision.key,
                },
            )
            print(
                pal(
                    f"  -> IPD {item['id6']} verification failed ({refusal_code}); handing it back for a bounded "
                    f"correction (attempt {decision.attempts + 1} of {decision.budget})",
                    "cyan",
                ),
                file=sys.stderr,
            )
            return "queued"
        else:
            item["status"] = "fail-verify"
            record_refusal(
                item,
                code=VERIFICATION_RETRY_EXHAUSTED_CODE,
                reason=decision.reason,
                remedy=(
                    f"read the failed attempts before re-running: verification correction budget was spent "
                    f"without success ({decision.attempts} of {decision.budget} attempts spent). "
                    f"Inspect them with `aw runs show <run-id>`, correct the plan or tests, then "
                    f"re-run with `{command} {item['id6']}` (or `{command} resume <run-id> --retry-incomplete`). "
                    f"Do NOT discard the lane: the partial work is preserved there"
                ),
            )
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "verification-retry-exhausted",
                    "id6": item["id6"],
                    "refusal_code": refusal_code,
                    "retry_attempts_used": decision.attempts,
                    "retry_budget": decision.budget,
                    "idempotency_key": decision.key,
                },
            )
            print(
                pal(
                    f"  ! IPD {item['id6']} verification FAILED: correction budget exhausted "
                    f"({decision.attempts} of {decision.budget} spent); the plan did NOT land",
                    "red",
                ),
                file=sys.stderr,
            )
            return "fail-verify"
    ```
    Single call site in `execute_item_core`:
    ```python
            # verremand (t18l64) E-03: Remand retryable verification failures back to the agent in its lane
            # under the frozen retry budget, called ONCE after the rescore and before silent-turn / integration gates.
            if (
                not is_review
                and not is_production
                and disposition == "fail-verify"
                and attempt.get(VERIFICATION_REFUSED_KEY)
            ):
                disposition = handle_verification_refusal(
                    run_dir=run_dir,
                    state=state,
                    item=item,
                    attempt=attempt,
                    attempt_no=attempt_no,
                    disposition=disposition,
                    host_labels=host_labels,
                    save_state=save_state,
                    append_jsonl=append_jsonl,
                )
                attempt["disposition"] = disposition
                item["status"] = disposition

            # r0iob3 E-02: consult turn_attempted_nothing on the completion path.
            # Option (b): reuse existing non-retryable disposition "fail-gate" at the shared in-core seam.
            outcome_written, lane = read_zero_work_evidence(repo, run_dir, item, attempt)
    ```
    Output from `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py -k test_unevidenced_verification`:
    ```
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_unevidenced_verification_remands_end_to_end_on_both_hosts PASSED [ 50%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_unevidenced_verification_exhausts_at_budget_zero PASSED [100%]
    ======================= 2 passed, 4 deselected in 5.43s ========================
    ```
    On both `oc` and `agy` hosts:
    - At `retry_budget` 2: `item["status"] == "queued"`, `item["recovery_next"] is True`, `item["verification_retry_attempts"] == 1`, exactly 1 `verification-sent-back` event in `events.jsonl`, `finalize_calls == []`.
    - At `retry_budget` 0: `item["status"] == "fail-verify"`, 0 `verification-sent-back` events.
    - `attempt["turn_retry_skipped"]`: "the item was REQUEUED for another attempt in this run, so turn failure retry spends nothing on this attempt".
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the source of `build_verification_refusal_notice`, its concatenation in `build_prompt`, and the modified `_PRIOR_ATTEMPT_SAFE_KEYS`. Paste test output showing a recovery prompt rendered with `lane_root` set, for both `OC_HOST_LABELS` and `AGY_HOST_LABELS`, contains the refusal code, the remedy, the attempt bound and the command-string guidance, and that `lane_containment.absolute_paths_outside_lane(prompt, lane_root)` returns `[]` for it (the shipped R1.1 property helper); and that a first-attempt prompt contains none of the notice text.
  - Observed evidence: build_verification_refusal_notice added and concatenated into prompt; safe key added; test_recovery_prompt_delivery passed (1 passed).
    Source of `build_verification_refusal_notice` in `agent_workflows/runner_shared.py`:
    ```python
    def build_verification_refusal_notice(item: Mapping[str, Any], recovery: bool) -> str:
        """Render the pending verification refusal notice into the recovery prompt, or "" when none."""
        if not recovery:
            return ""
        attempts = [a for a in (item.get("attempts") or []) if isinstance(a, Mapping)]
        if not attempts:
            return ""
        refused = attempts[-1].get(VERIFICATION_REFUSED_KEY)
        if not isinstance(refused, Mapping):
            return ""
        from agent_workflows.render_stream import _redact_absolute_paths

        v_code = _redact_absolute_paths(str(refused.get("code") or ""))
        v_reason = _redact_absolute_paths(str(refused.get("reason") or ""))
        v_remedy = _redact_absolute_paths(str(refused.get("remedy") or ""))
        att_num = refused.get("attempt") or (verification_retry_attempts(item) + 1)
        budget = refused.get("budget") or 2

        lines = [
            "",
            "",
            f"## Verification failed on the prior attempt ({v_code})",
            "",
            f"This is verification correction attempt {att_num} of {budget}.",
            "The previous attempt passed turn execution but independent verification was refused:",
            "",
            f"  - Refusal code: {v_code}",
            f"  - Reason: {v_reason}",
            f"  - Remedy: {v_remedy}",
            "",
            "The lane already holds your prior work, so you must FIX the cause rather than re-implementing "
            "from scratch.",
        ]
        if v_code == VERIFY_REFUSAL_CODE_UNEVIDENCED:
            lines.extend(
                [
                    "",
                    "IMPORTANT: `tests_run` entries in the outcome file must be the COMMAND STRINGS that were run "
                    "(for example `python3 -m pytest tests/test_x.py`), not test nodeids or module paths.",
                ]
            )
        return "\n".join(lines)
    ```
    Concatenation in `build_prompt`:
    ```python
        correction_notice = (
            build_correction_notice(item, recovery)
            + build_stale_receipt_notice(item, recovery)
            + build_verification_refusal_notice(item, recovery)
        )
    ```
    Allowlist addition in `agent_workflows/lane_containment.py`:
    ```diff
     _PRIOR_ATTEMPT_SAFE_KEYS = (
         "integration_detail",
         "finalize_refused",
         "begin_refused",
    +    # verification_refused carries only code/reason/remedy/verify_disp text already redacted by record_refusal's rule.
    +    "verification_refused",
         "cost",
         "tokens",
    ```
    Output from `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py -k test_recovery_prompt_delivery`:
    ```
    tests/test_verification_sendback.py::RecoveryPromptNoticeTests::test_recovery_prompt_delivery PASSED [100%]
    ======================= 1 passed, 5 deselected in 0.46s ========================
    ```
    Tested:
    - First-attempt prompt has no refusal notice text.
    - Recovery prompt for both `OC_HOST_LABELS` and `AGY_HOST_LABELS` contains refusal code (`verifier-no-test-evidence`), remedy (`record actual commands run`), attempt bound (`attempt 1 of 2`), and command-string guidance (`must be the COMMAND STRINGS that were run`).
    - `lane_containment.absolute_paths_outside_lane(rec_prompt, lane_dir)` returned `[]`.
    - `lane_containment.prior_attempt_summary` retains `verification_refused`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the actual output of `python3 -m pytest tests/test_verification_sendback.py` showing all tests passing, including the end-to-end cases run for BOTH the `oc` and `agy` hosts. For each shipped test edited in `tests/test_oc_runipd.py`, `tests/test_defect_report.py` and `tests/test_inlane_retirement_lands.py`, paste its diff showing the only change is the explicit `retry_budget: 0` (no assertion weakened) and its passing output; for each declared test path NOT edited, state that it did not break and paste its passing output.
  - Observed evidence: test_verification_sendback.py passed (6 passed); test_oc_runipd.py passed (182 passed); test_defect_report.py and test_inlane_retirement_lands.py unedited and passed (32 passed).
    Output from `python3 -m pytest -o addopts="" -v tests/test_verification_sendback.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2262665681
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 6 items

    tests/test_verification_sendback.py::RecoveryPromptNoticeTests::test_recovery_prompt_delivery PASSED [ 16%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_unevidenced_verification_exhausts_at_budget_zero PASSED [ 33%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_correction_required_remands_and_blocked_fails PASSED [ 50%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_stale_verdict_clearing PASSED [ 66%]
    tests/test_verification_sendback.py::VerificationSendbackEndToEndTests::test_unevidenced_verification_remands_end_to_end_on_both_hosts PASSED [ 83%]
    tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_decision_cases PASSED [100%]

    ============================== 6 passed in 10.37s ==============================
    ```
    Diff for shipped tests edited in `tests/test_oc_runipd.py`:
    ```diff
    @@ -6853,6 +6880,7 @@ class VerifierGateAndRunnerBugTests(unittest.TestCase):
                         "self_finalize": True,
                         "isolate_worktree": True,
                         "no_audit": False,
    +                    "retry_budget": 0,
                     },
                 }

    @@ -6950,6 +6981,7 @@ class VerifierGateAndRunnerBugTests(unittest.TestCase):
                         "self_finalize": True,
                         "isolate_worktree": True,
                         "no_audit": False,
    +                    "retry_budget": 0,
                     },
                 }
    ```
    Output from `python3 -m pytest -o addopts="" tests/test_oc_runipd.py`:
    182 passed in 58.74s.
    Declared test paths `tests/test_defect_report.py` and `tests/test_inlane_retirement_lands.py` did not break and were not edited; passing output:
    ```
    tests/test_inlane_retirement_lands.py .........                          [ 28%]
    tests/test_defect_report.py .......................                      [100%]

    ============================= 32 passed in 21.92s ==============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the spec 25kzda Section 5.5 diff showing the third classification surface and the widened `missing or stale validation evidence` row, and paste `tests/test_retry_budget_citation.py` passing. Paste the actual output of the named-module command and of the bare `python3 -m pytest` with its `N passed` summary line, compared against the executor's own pre-E-01 baseline. Paste `aw sanitize --agent` output with exit 0. Paste `aw ipd lint --phase pre-transition --agent` output showing conforming.
  - Observed evidence: Spec 25kzda Section 5.5 amended and test_retry_budget_citation.py passed (1 passed); named modules passed (299 passed); bare suite passed (4630 passed, 0 regressions); sanitize passed clean.
    Diff of spec 25kzda Section 5.5:
    ```diff
    @@ -1338,9 +1338,10 @@ It must never retry these classes regardless of budget:

    -The runner provides two distinct classification surfaces that key on different evidence by design:
    +The runner provides three distinct classification surfaces that key on different evidence by design:
     - `turn_failure_is_retryable`: classifies a finished turn by its runner disposition.
     - `finalize_retry_decision`: classifies a refused finalize by the gate's findings carried across the subprocess boundary. It keys primarily on shipped lint finding codes (`finalize_refusal_is_retryable`, `retryable_finalize_finding_codes`), retaining a prose fallback for findings without a lint code and for answerable checkpoint messages excluded from the code set.
    +- `verification_retry_decision`: classifies a refused or unevidenced verification outcome before integration. It remands the lane to the executing agent under the shared `--retry-budget` with a separate action counter when verification evidence is missing (`verifier-no-test-evidence`), the verdict requires correction (`verifier-declined`), or the outcome file was unreadable/unrecorded (`verification-outcome-unreadable`, `verification-never-recorded`); environment obstacles (`BLOCKED`) are not retryable.

     The normative mapping between the retry classes above and the runner's disposition vocabulary is declared in the following table:

    @@ -1349,7 +1350,7 @@ The normative mapping between the retry classes above and the runner's dispositi
     | host spawn failure | `failed-safely` | `turn_failure_is_retryable` | Yes | Host failed to spawn or crashed under driver supervision. Guarded against deliberate operator stop. Canonical token `failed` has no live producer and is classified non-retryable in code. |
     | host nonzero exit that did not create an ambiguous side effect | `failed-safely` | `turn_failure_is_retryable` | Yes | Nonzero exit cleanly captured and contained in lane worktree. |
     | missing expected artifact or failed deterministic check for which a bounded correction is safe | None (turn); findings (finalize) | `finalize_retry_decision` | Yes (at finalize) | Handled at finalize gate by finding codes; no distinct retryable turn disposition. |
    -| missing or stale validation evidence | None (turn); findings (finalize) | `finalize_retry_decision` | Yes (at finalize) | Handled at finalize gate (`IPD-S401`, `IPD-S402`, `IPD-S403`); turn disposition `substantially-complete` is not retryable at turn level to avoid double-spend. |
    +| missing or stale validation evidence | None (turn); findings (finalize); refusal (verification) | `finalize_retry_decision`, `verification_retry_decision` | Yes (at finalize and verification) | Handled at finalize gate (`IPD-S401`, `IPD-S402`, `IPD-S403`) and verification gate (`verifier-no-test-evidence`, `verifier-declined`, `verification-outcome-unreadable`, `verification-never-recorded`; `BLOCKED` is not retried); turn disposition `substantially-complete` is not retryable at turn level to avoid double-spend. |
    ```
    Output from `python3 -m pytest -o addopts="" tests/test_retry_budget_citation.py`:
    ```
    tests/test_retry_budget_citation.py .                                    [100%]
    ============================== 1 passed in 0.22s ===============================
    ```
    Named-module test command:
    `python3 -m pytest -o addopts="" tests/test_verification_sendback.py tests/test_verifier_evidence.py tests/test_finalize_sendback.py tests/test_retry_class_mapping.py tests/test_retry_budget_citation.py tests/test_oc_runipd.py tests/test_defect_report.py tests/test_inlane_retirement_lands.py`
    Output:
    `======================= 299 passed in 110.29s (0:01:50) ========================`

    Bare suite command `python3 -m pytest`:
    Pre-E-01 baseline on main: 4621 passed, 3 failed, 2 skipped, 3 warnings in 238.12s.
    Post-implementation run: 4630 passed, 3 failed, 2 skipped, 3 warnings in 252.60s.
    The 3 failures are identical to the baseline failures on main (`test_selector_type_containment.py::test_must_not_refuse_matrix`, `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`). Net +9 passing tests, 0 regressions.

    Leak check:
    `aw sanitize --agent`
    Output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    Exited 0 (clean).

    Pre-transition lint check:
    `aw ipd lint --phase pre-transition --agent .aw/records/plans/pending/20261001-verremand-01-t18l64-remand-verification-evidence-refusals-and-verification-failu.ipd.md`
    Conforming with 0 findings.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required.

This plan must not be executed until a human sets it `approved`. All open questions are resolved; none blocks execution.

EXECUTION CONTRACT. Commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, `git add .` or `-a`, never `--no-verify`, never push. Paste the ACTUAL runner output for every test claim; do not claim a pass that was not run. Run the suite BARE as `python3 -m pytest`. If an edit outside `Scope-Paths` proves necessary, make it and JUSTIFY it at finalize with `--scope-reason`; a declared path left unmodified is `--scope-ack`ed. Stop and report only for a genuinely unsafe condition: a concurrent edit to `runner_shared.py` that cannot be safely combined, or a cited symbol (`handle_turn_failure_retry`, `_run_verifier_turn`, `rescore_is_an_improvement`, `frozen_retry_budget`, `verdict_refusal_text`) absent at the executing HEAD.

LIFECYCLE TRANSITION. After every `E-*` is performed and every `V-*` carries pasted, non-empty observed evidence, `aw ipd lint --phase pre-transition` must conform. When this plan is executed by `aw oc run` / `aw agy run`, the RUNNER owns the terminal transition (`aw ipd finalize`) and the executor must NOT run it; when executed by hand outside a runner, finalize through `aw ipd finalize` so the plan moves to `.aw/records/plans/executed/` with a scope-reconciled commit. Never hand-`git mv` the plan.

BACKLOG HANDOFF. This plan carries `- From-Backlog: kw31r2` and inherits its `- Blocks-Release: next`; the item is already `graduated` and may close once this plan is `executed`.
