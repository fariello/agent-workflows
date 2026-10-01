# IPD: Remand verification evidence refusals and verification failures back to the agent under retry conventions

- Date: 2026-10-01
- Kind: child
- Concern: In execute_item_core, independent verification failures (including verifier-no-test-evidence, unverified or failed verdicts, and missing outcome files) immediately transition to terminal disposition fail-verify, skipping turn retries and stranding lanes without remanding the issue back to the agent under the run's retry budget, which violates spec 25kzda Section 5.5's retryable class for missing or stale validation evidence.
- Scope: Introduce verification retry accounting and a verification retry decision helper in runner_shared.py following the proven finalize_retry_decision pattern; route verification failure sites through handle_verification_refusal so retryable verification refusals are remanded back to the agent in its lane as queued with recovery_next=True until the retry budget is exhausted; ensure recovery prompts surface the verification refusal context; add comprehensive unit and regression tests in tests/test_verification_sendback.py.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, tests/test_verification_sendback.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: kw31r2
- From-Spec: 25kzda
- Blocks-Release: next
- Set: verremand
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: t18l64

## Workflow history

- 2026-10-01 to-review (antigravity): authored plan graduating backlog kw31r2. Every code claim verified against agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, and measured run run-20260930T233959Z-250047.

## Goal

Ensure that verification failures, including missing verification evidence (`verifier-no-test-evidence`), failed verdicts, and unreadable or missing verification outcomes, are remanded back to the executing agent in its lane under the run's configured retry budget (`--retry-budget`), following the established retry and remand conventions rather than terminating immediately as unretryable `fail-verify`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: verification retry decision and accounting

- [ ] E-01 Add verification retry accounting, classification, and decision helpers to `agent_workflows/runner_shared.py`. Define `VERIFICATION_RETRY_COUNT_KEY = "verification_retry_count"`, `VERIFICATION_RETRY_EXHAUSTED_STATUS = "fail-verify"`, and `VERIFICATION_RETRYABLE_REFUSAL_CODES = (VERIFY_REFUSAL_CODE_UNEVIDENCED, "unverified", "verify-failed", VERIFY_ABSENCE_NO_OUTCOME_FILE, VERIFY_ABSENCE_VERDICT_UNREADABLE)`. Implement `verification_retry_attempts(item: Mapping[str, Any]) -> int`, `verification_failure_is_retryable(item: Mapping[str, Any], refusal_code: str, reason: str) -> tuple[bool, str]`, and `verification_retry_decision(item: Mapping[str, Any], state: Mapping[str, Any], refusal_code: str, reason: str, remedy: str) -> VerificationRetryDecision` returning a typed dataclass with `retry: bool`, `exhausted: bool`, `reason: str`, `attempts: int`, `budget: int`, and idempotency `key: str`. Enforce that the decision is bounded by `frozen_retry_budget(state)` and refuses non-retryable classes (operator stops, corrupt ledger).
  - Depends on: none
  - Expected outcome: helper functions in `agent_workflows/runner_shared.py` providing bounded, idempotent verification retry decisions calibrated against `frozen_retry_budget(state)`.
  - Execution state: pending

### Task group 2: verification failure routing and remand mechanism

- [ ] E-02 Implement `handle_verification_refusal` in `agent_workflows/runner_shared.py` and route all non-verified verification branches in `_run_verifier_turn` through it. When `verify_disp != VERIFY_DISP_VERIFIED` or `not v_has_evidence` or outcome file is missing, evaluate `verification_retry_decision`. If `decision.retry`: increment `item[VERIFICATION_RETRY_COUNT_KEY] = decision.attempts + 1`, record `verification_refused` on `attempt` and `item`, record the refusal via `record_refusal`, transition `item["status"] = "queued"`, set `item["recovery_next"] = True`, set `item["requeue_from_status"] = disposition`, emit event `verification-sent-back` to `events.jsonl`, and return `disposition = "queued"`. If `decision.exhausted`: set `item["status"] = VERIFICATION_RETRY_EXHAUSTED_STATUS`, clear `recovery_next`, emit event `verification-retry-exhausted`, and return `disposition = "fail-verify"`. If non-retryable: keep `disposition = "fail-verify"`.
  - Depends on: E-01
  - Expected outcome: verification failure sites in `execute_item_core` remand retryable failures back to the agent as `queued` with `recovery_next = True` while budget remains, rather than immediately terminating the item.
  - Execution state: pending

### Task group 3: recovery prompt context and lane containment

- [ ] E-03 Update `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` and `runner_shared.build_prompt` so the executing agent receives the verification refusal context on the recovery turn. Add `'verification_refused'` to `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` so the prior attempt summary retains it in isolated lane worktrees. In `build_prompt` (when `recovery=True`), if `prior` or `item` carries `verification_refused`, format the refusal code, reason, and remedy into the recovery instructions so the agent knows exactly what verification rejected and what remediation is required.
  - Depends on: E-02
  - Expected outcome: a resumed or re-dispatched worker receives clear, actionable feedback regarding the verification refusal in its recovery prompt without leaking un-scrubbed host paths.
  - Execution state: pending

### Task group 4: test coverage and regression fence

- [ ] E-04 Author comprehensive unit and regression tests in `tests/test_verification_sendback.py`. Test that: (1) `verification_retry_decision` returns `retry=True` when attempts < frozen retry budget; (2) `verification_retry_decision` returns `exhausted=True` when attempts >= frozen retry budget or budget is 0; (3) `handle_verification_refusal` mutates state to `status = "queued"`, sets `recovery_next = True`, increments `verification_retry_count`, and emits `verification-sent-back`; (4) `verifier-no-test-evidence` is classified as retryable under Spec 25kzda Section 5.5; (5) `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` includes `verification_refused`; (6) the recovery prompt interpolates the verification refusal notice.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a focused test suite in `tests/test_verification_sendback.py` exercising all verification retry and sendback code paths, passing cleanly.
  - Execution state: pending

### Task group 5: suite validation and conformance

- [ ] E-05 Execute the owning test modules, run leak sanitization, and verify pre-transition IPD lint conformance. Run `python3 -m pytest tests/test_verification_sendback.py tests/test_verifier_evidence.py tests/test_finalize_sendback.py`, run `aw sanitize --agent` over the repository tree, and verify `aw ipd lint` reports conforming across author and review-finalize phases.
  - Depends on: E-04
  - Expected outcome: all tests pass, leak check reports 0 findings, and lint reports conforming.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Finalize sendback precedent: `runner_shared.handle_finalize_refusal` and `runner_shared.finalize_retry_decision` establish the exact pattern for bounding retries against `frozen_retry_budget(state)`, incrementing a dedicated count key (`FINALIZE_RETRY_COUNT_KEY`), and re-queueing with `item["status"] = "queued"` and `item["recovery_next"] = True`.
- Isolated worktree containment: `lane_containment.prior_attempt_summary` filters prior attempt keys through `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` to avoid leaking absolute driver-side paths into worker prompts. Adding `verification_refused` to this tuple is mandatory for isolated lanes to receive the refusal context.
- Retry budget precedence: Spec `25kzda` Section 5.5 is the normative home for the 0..10 bound and three-tier precedence (`--retry-budget` > `run.retry_budget` > default 2). The budget is frozen at run initialization and accessed via `runner_shared.frozen_retry_budget(state)`.
- Verification failure classification: in `runner_shared.TURN_RETRY_CLASSIFICATION`, `fail-verify` is currently hardcoded as `retryable=False`. Siting the retry decision inside the verifier handling block (matching `handle_finalize_refusal`) allows verification failures to be remanded back to the agent before a terminal disposition is recorded.

## Findings

| Finding | Summary | Citation / Measurement |
| :--- | :--- | :--- |
| F-01 | **VERIFICATION FAILURES ARE CURRENTLY ABANDONED WITHOUT RETRY:** When verification fails (e.g. `verifier-no-test-evidence`, `verify_disp != VERIFIED`), `execute_item_core` immediately sets `disposition = "fail-verify"`, skips turn retry because `TURN_RETRY_CLASSIFICATION` marks `fail-verify` non-retryable, and moves on to the next item, stranding the lane. | `runner_shared.execute_item_core` (`_run_verifier_turn`), `runner_shared.TURN_RETRY_CLASSIFICATION` |
| F-02 | **SPEC 25kzda SECTION 5.5 EXPLICITLY PERMITS RETRYING VALIDATION EVIDENCE FAILURES:** Spec 25kzda Section 5.5 states: "The engine may spend budget only on failures classified as retryable: ... missing or stale validation evidence; ...". The current implementation fails closed without spending remaining retry budget. | Spec `25kzda` Section 5.5 bullet "missing or stale validation evidence" |
| F-03 | **LANE CONTAINMENT DROPS REFUSAL CONTEXT IN ISOLATED WORKTREES UNLESS ALLOWLISTED:** `lane_containment.prior_attempt_summary` uses `_PRIOR_ATTEMPT_SAFE_KEYS` to filter prior attempts. While `finalize_refused` and `begin_refused` are allowlisted, verification refusal data is absent and would be stripped on recovery turns. | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` |
| F-04 | **RE-QUEUE PATTERN IS ALREADY SHARED AND PROVEN:** Setting `item["status"] = "queued"`, `item["recovery_next"] = True`, and `item["requeue_from_status"] = disposition` is the standard pattern consumed by both `oc_runipd.py` and `agy_runipd.py` in `run_queue`. | `runner_shared.handle_finalize_refusal`, `runner_shared.requeue_interrupted` |
| F-05 | **MEASURED STRANDING IN PRODUCTION:** In run `run-20260930T233959Z-250047`, item `5poaqh` (Set `pftva5`) passed all 90 tests and lint, but because the verifier wrote test nodeids instead of command prefixes in `tests_run`, the runner rejected it with `verifier-no-test-evidence` and stranded the lane instead of remanding the issue to the agent. | `run-20260930T233959Z-250047` outcome `08-5poaqh-verification.json`, `events.jsonl` |

## Proposed changes (ordered, validatable)

1. In `agent_workflows/runner_shared.py`:
   - Define constants: `VERIFICATION_RETRY_COUNT_KEY = "verification_retry_count"`, `VERIFICATION_RETRY_EXHAUSTED_STATUS = "fail-verify"`.
   - Implement `VerificationRetryDecision` dataclass and helper functions: `verification_retry_attempts`, `verification_failure_is_retryable`, and `verification_retry_decision`.
   - Implement `handle_verification_refusal(...)` mirroring `handle_finalize_refusal(...)`.
   - In `_run_verifier_turn`, replace the inline hardcoded `fail-verify` terminal assignments with calls to `handle_verification_refusal`.
2. In `agent_workflows/lane_containment.py`:
   - Add `'verification_refused'` to `_PRIOR_ATTEMPT_SAFE_KEYS`.
3. In `agent_workflows/runner_shared.py`:
   - Update `build_prompt` to format `verification_refused` into the recovery instructions when present on `prior` or `item`.
4. In `tests/test_verification_sendback.py`:
   - Add comprehensive unit and regression tests for `verification_retry_decision`, `handle_verification_refusal`, prompt formatting, and event emission.

## Deferred / out of scope (with reason)

- In-session verifier re-prompting: re-prompting the verifier agent within the same turn session for minor JSON syntax/field issues is deferred. Remanding back to the executing agent in the lane follows the user instruction, works across both isolated and non-isolated modes, and allows addressing actual code/test failures as well as evidence gaps.
- Altering the `has_verifier_test_evidence` predicate: the predicate's command-like content requirement (from plan `bxx9af`) remains untouched.

## Scope check

- Over-scope: none. Changes are strictly confined to runner retry accounting, verifier refusal handling, recovery prompt context, and tests.
- Under-scope: none. Both OpenCode and Antigravity runners inherit this functionality via `execute_item_core` in `runner_shared.py`.

## Required tests / validation

- Bare pytest run over owning tests: `python3 -m pytest tests/test_verification_sendback.py tests/test_verifier_evidence.py tests/test_finalize_sendback.py`.
- Unit tests covering retry decision with positive budget, exhausted budget, and zero budget.
- Regression test demonstrating that an item hitting `verifier-no-test-evidence` is re-queued with `recovery_next = True` when budget remains.
- Leak check: `aw sanitize --agent` reporting clean exit code 0.
- Lint conformance: `aw ipd lint` reporting conforming across author and review-finalize checkpoints.

## Spec / documentation sync

Spec `25kzda` Section 5.5 already specifies `missing or stale validation evidence` as a retryable failure class. This plan brings the implementation into full conformance with that clause of Spec `25kzda`. No spec amendment is required.

## Open questions

### OQ-01: Should verification retry budget share `--retry-budget` or introduce a separate knob?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY CONVENTIONS AND SPEC 25kzda 5.5: Share `--retry-budget`. The maintainer has repeatedly ruled against introducing second retry knobs (see plan `4gx141` and `ounhsn`), and Spec 25kzda 5.5 designates `--retry-budget` as the single normative budget for all automatic correction attempts after the initial execution attempt.

### OQ-02: Should `verification_refused` replace or complement `finalize_refused` in recovery notices?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: RESOLVED: Complement. An item can hit a verification refusal on attempt 1, fix it, hit a finalize refusal on attempt 2, or vice versa. Both refusal types represent distinct lifecycle stages. The recovery prompt inspects both keys independently and displays whichever failure occurred on the prior attempt.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the source of `VerificationRetryDecision`, `verification_retry_attempts`, `verification_failure_is_retryable`, and `verification_retry_decision` from `agent_workflows/runner_shared.py`. Paste unit test output showing that attempts are accurately counted, non-retryable codes are refused, and decisions correctly distinguish `retry=True` from `exhausted=True` against `frozen_retry_budget`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the source of `handle_verification_refusal` from `agent_workflows/runner_shared.py` and the call sites in `_run_verifier_turn`. Paste unit test output showing that when verification fails with `verifier-no-test-evidence`, the item status is set to `queued`, `recovery_next` is set to `True`, `verification_retry_count` is incremented, and the `verification-sent-back` event is emitted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the modified `_PRIOR_ATTEMPT_SAFE_KEYS` tuple from `agent_workflows/lane_containment.py` and the recovery prompt formatting in `runner_shared.build_prompt`. Paste test output showing that a recovery prompt rendered in an isolated lane worktree contains the verification refusal reason and remedy without leaking outer repository paths.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the test execution output of `python3 -m pytest tests/test_verification_sendback.py` showing all tests passing. Confirm that both OpenCode and Antigravity host paths are tested for symmetry.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the execution output of `python3 -m pytest tests/test_verification_sendback.py tests/test_verifier_evidence.py tests/test_finalize_sendback.py`. Paste `aw sanitize --agent` clean output (exit 0). Paste `aw ipd lint` output showing conforming status.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required.
- Execution contract: Once approved, the executing agent must implement E-01 through E-05, paste all required evidence into V-01 through V-05, and finalize the plan via `aw ipd finalize` using the tooled commit path (`aw commit`).
