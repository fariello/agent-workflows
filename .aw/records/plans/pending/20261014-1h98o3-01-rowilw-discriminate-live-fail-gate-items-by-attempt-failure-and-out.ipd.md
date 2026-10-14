# IPD: Discriminate live fail-gate items by attempt failure and outcome disposition in the run summary outcome-word ladder

- Date: 2026-10-14
- Kind: child
- Concern: Run summary `Outcome:` word classification for live `fail-gate` queue items in `agent_workflows/render_stream.py`.
- Scope: Add item-level `fail-gate` producer discrimination in `agent_workflows/render_stream.py` (`outcome_class_of_item`) so `render_run_summary_table` maps nonzero-exit / crashed `fail-gate` turns to `OUTCOME_CLASS_FAILED` (`FAILED`), executed-claim-not-moved `fail-gate` turns without a gate refusal to `OUTCOME_CLASS_SUCCESS` (`COMPLETED` when work landed or `--no-self-finalize`, `STRANDED` when `work_did_not_land(item)` is true), and gate refusals awaiting a human (plus bare `fail-gate` items) to `OUTCOME_CLASS_BLOCKED` (`BLOCKED`); cover all three producers in `tests/test_outcome_word_ladder.py`.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_outcome_word_ladder.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: 1h98o3
- Set: 1h98o3 (fail-gate outcome-word discrimination)
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: rowilw

## Workflow history

- 2026-10-14 draft (Antigravity): created from backlog item `1h98o3`.
- 2026-10-14 to-review (Antigravity): populated findings, design for `outcome_class_of_item`, and `E-01`..`E-03` / `V-01`..`V-03` pairs.

## Goal

Restore accurate `Outcome:` header words (`FAILED`, `COMPLETED`, `STRANDED`, and `BLOCKED`) in `render_stream.render_run_summary_table` for live `fail-gate` items after `cyamvi` (commit `6b94a4d9d`) unified `reconcile_disposition`'s nonzero-exit fallback and `outcome_precedence_disposition`'s executed-claim-not-moved branch onto the canonical `"fail-gate"` status token. Discriminate the three live `"fail-gate"` producers in `agent_workflows/render_stream.py` using already-recorded item/attempt fields (`attempts[-1]["exit_code"]`, `attempts[-1]["turn_failure_kind"]`, `host_error`, `refusal_of_item(item)`, and `last_outcome["disposition"]`) rather than overloading the status token.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Item-level `fail-gate` outcome-class discriminator in `render_stream.py`

- [ ] E-01 In `agent_workflows/render_stream.py`, define a pure helper `outcome_class_of_item(item: Mapping[str, Any]) -> str` next to `RUN_OUTCOME_CLASS_BY_STATUS` that returns `RUN_OUTCOME_CLASS_BY_STATUS.get(item.get("status"), OUTCOME_CLASS_NONE)` for any status other than `"fail-gate"`, and for `"fail-gate"` discriminates the three live producers from recorded item/attempt fields: (1) returns `OUTCOME_CLASS_FAILED` when the last mapping entry in `item.get("attempts")` has a non-empty `turn_failure_kind`, a non-boolean integer `exit_code != 0`, or a truthy `host_error`, or when `item.get("host_error")` is truthy, or when `refusal_of_item(item)` has `code` in `("SPEC-PRODUCTION-FAILED", "BACKLOG-PRODUCTION-FAILED")`; (2) otherwise returns `OUTCOME_CLASS_SUCCESS` when `refusal_of_item(item) is None`, `not item.get("proposal_record")`, `not item.get("needs_input")`, and `item.get("last_outcome")` is a `Mapping` with `disposition` in `("executed", "completed", "substantially-complete")`; (3) otherwise returns `OUTCOME_CLASS_BLOCKED`.
  - Depends on: none
  - Expected outcome: `render_stream.outcome_class_of_item` is importable and classifies `"fail-gate"` items into `OUTCOME_CLASS_FAILED`, `OUTCOME_CLASS_SUCCESS`, or `OUTCOME_CLASS_BLOCKED` according to recorded attempt/outcome/refusal fields while preserving `RUN_OUTCOME_CLASS_BY_STATUS["fail-gate"] == OUTCOME_CLASS_BLOCKED` as the token-level default.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/render_stream.py`, update the outcome-word ladder in `render_run_summary_table` to call `outcome_class_of_item(it)` in place of `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` across the `all_failed` (`FAILED`), `BLOCKED`, and `COMPLETED` / `PARTIAL` arms so that a nonzero-exit `fail-gate` item renders `FAILED`, an executed-claim-not-moved `fail-gate` item without a gate refusal renders `COMPLETED` (or reaches the `STRANDED` arm when `work_did_not_land(it)` is true), and a gate-refusal or bare `fail-gate` item continues to render `BLOCKED`.
  - Depends on: E-01
  - Expected outcome: `render_run_summary_table` derives each item's outcome class through `outcome_class_of_item(it)` in all ladder arms without breaking existing `RUN_OUTCOME_CLASS_BY_STATUS` invariants.
  - Execution state: pending

### Task group 2: Unit and regression tests in `tests/test_outcome_word_ladder.py`

- [ ] E-03 In `tests/test_outcome_word_ladder.py`, add tests exercising `outcome_class_of_item` and `render_run_summary_table` across all three live `"fail-gate"` producer shapes: (a) nonzero-exit / crashed turns (`exit_code != 0`, `turn_failure_kind` set, `host_error` set, and `SPEC-PRODUCTION-FAILED` / `BACKLOG-PRODUCTION-FAILED` refusal codes) rendering `Outcome: FAILED` (and `PARTIAL` when mixed with an `executed` item); (b) executed-claim-not-moved turns (`exit_code == 0`, no refusal, `last_outcome={"disposition": "executed"}` or `"substantially-complete"`) rendering `Outcome: COMPLETED` when `work_did_not_land` is false and `Outcome: STRANDED` when `integration_signal` is a non-landing signal (`"suite-failed"`); and (c) gate refusals awaiting a human (`awaiting-human-decision`, `finalize-refused`, `clean-base-refused`, `SPEC-PLAN-LINT`, and bare `fail-gate` items) continuing to render `Outcome: BLOCKED`.
  - Depends on: E-01, E-02
  - Expected outcome: `python3 -m pytest tests/test_outcome_word_ladder.py tests/test_zero_dispatch_outcome.py tests/test_review_failure_reason.py` and the full pytest suite pass with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `RUN_OUTCOME_CLASS_BY_STATUS` in `agent_workflows/render_stream.py` (defined around `OUTCOME_CLASS_BLOCKED = "blocked"`) is the single source of truth mapping item status tokens to token-level outcome classes (`OUTCOME_CLASS_FAILED`, `OUTCOME_CLASS_BLOCKED`, `OUTCOME_CLASS_SKIPPED`, `OUTCOME_CLASS_SUCCESS`, `OUTCOME_CLASS_NONE`), and `tests/test_outcome_word_ladder.py` (`test_run_outcome_class_table_covers_every_declared_status_token`, `test_canonical_aliases_share_outcome_class_unless_declared`) pins that every declared status token has an entry in `RUN_OUTCOME_CLASS_BY_STATUS` and that `"fail-gate"` is listed in `DECLARED_OUTCOME_ALIAS_DIVERGENCES` alongside `"failed-safely"`, `"blocked"`, and `"substantially-complete"`.
- Plan `064awu` (`.aw/records/plans/executed/20261012-3l0dmi-01-064awu-declare-one-outcome-word-arm-per-status-token-so-canonical-f.ipd.md`) resolved the two-arm `"fail-gate"` collision in `render_run_summary_table` by assigning `"fail-gate": OUTCOME_CLASS_BLOCKED` in `RUN_OUTCOME_CLASS_BY_STATUS` and filing backlog item `1h98o3` to discriminate the live `"fail-gate"` producers using recorded item/attempt fields.
- Tests must exercise observable behavior (`outcome_class_of_item` and `render_run_summary_table` outputs) and never inspect source code via `inspect`, `ast`, or regex.

## Findings

| # | Producer of `item["status"] = "fail-gate"` in `agent_workflows/runner_shared.py` | Pre-`6b94a4d9d` status token & `Outcome:` word | Recorded fields on `item` and `item["attempts"][-1]` | Desired `outcome_class_of_item(item)` & `Outcome:` word |
|---|---|---|---|---|
| 1 | Nonzero-exit / crashed turn in `reconcile_disposition` (Rung 2 review `exit_code != 0`, Rung 2b spec production `exit_code != 0`, Rung 5 fallback `exit_code != 0`) and `execute_item_core` post-turn recording | `"failed-safely"` -> `OUTCOME_CLASS_FAILED` -> `FAILED` | `attempts[-1]["exit_code"]` is a non-zero `int`, `attempts[-1]["turn_failure_kind"]` is `"nonzero-exit"` / `"no-outcome"` / `"turn-limit"` / `"spawn-failure"` / `"stall"`, `host_error` is set on `attempt` or `item`, or `refusal_of_item(item)["code"]` is `"SPEC-PRODUCTION-FAILED"` / `"BACKLOG-PRODUCTION-FAILED"` | `OUTCOME_CLASS_FAILED` -> `FAILED` (single/all failed) or `PARTIAL` (when paired with a landed item) |
| 2 | Executed-claim-not-moved / `substantially-complete` turn in `outcome_precedence_disposition` (Rung 2 `bucket != "executed"` with `outcome["disposition"] in ("executed", "completed")`, or Rung 3 `canonical_terminal_status("substantially-complete")`) when `exit_code == 0` and no gate refusal was recorded | `"substantially-complete"` -> `OUTCOME_CLASS_SUCCESS` -> `COMPLETED` (when `not work_did_not_land(item)`, e.g. `--no-self-finalize`) or `STRANDED` (when `work_did_not_land(item)` is true, e.g. `integration_signal == "suite-failed"`) | `attempts[-1]["exit_code"] == 0` (or absent), no `turn_failure_kind`, `refusal_of_item(item) is None`, `not item.get("proposal_record")`, `not item.get("needs_input")`, and `item["last_outcome"]["disposition"] in ("executed", "completed", "substantially-complete")` | `OUTCOME_CLASS_SUCCESS` -> `COMPLETED` when `not work_did_not_land(item)`, or falls through to `STRANDED` (`STRANDED_OUTCOME`) when `work_did_not_land(item)` is true |
| 3 | Pre-dispatch or post-turn gate refusal awaiting a human (`clean_base_refused`, `scope_target_refused`, `host_capability_unavailable`, `proposal_record` / `awaiting-human-decision`, `finalize-refused`, `finalize-plan-unresolvable`, `spec-review-not-reviewed`, `review-zero-output`, `IPD-REVIEW-ORCHESTRATOR-READY`, `SPEC-PLAN-*`, `BACKLOG-GRADUATE-*`, agent-recorded `disposition in ("blocked", "fail-gate")`, or bare `fail-gate` fixtures) | `"blocked"` / `"fail-gate"` -> `OUTCOME_CLASS_BLOCKED` -> `BLOCKED` | No nonzero `exit_code`, no `turn_failure_kind`, and either `refusal_of_item(item)` is a gate refusal, `proposal_record` / `needs_input` is set, `last_outcome` is absent or has a non-success disposition, or `attempts` is empty/minimal | `OUTCOME_CLASS_BLOCKED` -> `BLOCKED` |

## Proposed changes (ordered, validatable)

1. **Add `outcome_class_of_item(item: Mapping[str, Any]) -> str` in `agent_workflows/render_stream.py` (`E-01`)**:
   - Keep `RUN_OUTCOME_CLASS_BY_STATUS` and `DECLARED_OUTCOME_ALIAS_DIVERGENCES` intact so `"fail-gate": OUTCOME_CLASS_BLOCKED` remains the token-level default.
   - Define `outcome_class_of_item(item: Mapping[str, Any]) -> str` right after `DECLARED_OUTCOME_ALIAS_DIVERGENCES`:
     - If `not isinstance(item, Mapping)`, return `OUTCOME_CLASS_NONE`.
     - Look up `status = item.get("status")` and `base = RUN_OUTCOME_CLASS_BY_STATUS.get(status, OUTCOME_CLASS_NONE)`.
     - If `status != "fail-gate"`, return `base`.
     - Inspect the last mapping entry in `item.get("attempts")` (when `isinstance(attempts, list)`):
       - If `isinstance(last_attempt.get("turn_failure_kind"), str)` and `last_attempt["turn_failure_kind"].strip()`, return `OUTCOME_CLASS_FAILED`.
       - If `exit_code = last_attempt.get("exit_code")` satisfies `isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code != 0`, return `OUTCOME_CLASS_FAILED`.
       - If `last_attempt.get("host_error")` is truthy, return `OUTCOME_CLASS_FAILED`.
     - If `item.get("host_error")` is truthy, return `OUTCOME_CLASS_FAILED`.
     - Check `refusal = refusal_of_item(item)`:
       - If `refusal is not None` and `refusal.get("code") in ("SPEC-PRODUCTION-FAILED", "BACKLOG-PRODUCTION-FAILED")`, return `OUTCOME_CLASS_FAILED` (covering spec/backlog production where a correction turn exited nonzero while the initial attempt recorded `exit_code == 0`).
       - If `refusal is not None`, return `OUTCOME_CLASS_BLOCKED` (a deterministic gate refusal such as `finalize-refused`, `awaiting-human-decision`, `SPEC-PLAN-LINT`, `BACKLOG-GRADUATE-LINT`, or `review-zero-output` was recorded).
     - If `not item.get("proposal_record")` and `not item.get("needs_input")`:
       - Check `last_outcome = item.get("last_outcome")`: if `isinstance(last_outcome, Mapping)` and `last_outcome.get("disposition") in ("executed", "completed", "substantially-complete")`, return `OUTCOME_CLASS_SUCCESS`.
     - Return `OUTCOME_CLASS_BLOCKED`.

2. **Wire `outcome_class_of_item(it)` into `render_run_summary_table`'s outcome-word ladder in `agent_workflows/render_stream.py` (`E-02`)**:
   - In `render_run_summary_table` (around `all_failed = bool(queue) and all(...)`), replace each `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` call in the outcome-word ladder with `outcome_class_of_item(it)`:
     - `all_failed`: `all(outcome_class_of_item(it) == OUTCOME_CLASS_FAILED for it in queue)`
     - `BLOCKED` arm: `elif any(outcome_class_of_item(it) == OUTCOME_CLASS_BLOCKED for it in queue):`
     - `COMPLETED` (all-success) arm: `elif all(outcome_class_of_item(it) == OUTCOME_CLASS_SUCCESS for it in queue) and not any(work_did_not_land(it) for it in queue):`
     - `COMPLETED` / `PARTIAL` (success + skipped) arm: `elif any(outcome_class_of_item(it) == OUTCOME_CLASS_SUCCESS and not work_did_not_land(it) for it in queue) and all(outcome_class_of_item(it) in (OUTCOME_CLASS_SUCCESS, OUTCOME_CLASS_SKIPPED) for it in queue) and not any(work_did_not_land(it) for it in queue):`

3. **Add unit and regression tests in `tests/test_outcome_word_ladder.py` (`E-03`)**:
   - Test `outcome_class_of_item` and `render_run_summary_table` for:
     - `fail-gate` with `attempts=[{"number": 1, "exit_code": 1, "turn_failure_kind": "no-outcome"}]` -> `OUTCOME_CLASS_FAILED` and `Outcome: FAILED`.
     - `fail-gate` with `attempts=[{"number": 1, "exit_code": 137}]` -> `OUTCOME_CLASS_FAILED` and `Outcome: FAILED`.
     - `fail-gate` with `attempts=[{"number": 1, "exit_code": 0, "turn_failure_kind": "turn-limit"}]` -> `OUTCOME_CLASS_FAILED` and `Outcome: FAILED`.
     - `fail-gate` with `host_error={"type": "ProviderError", "message": "boom"}` -> `OUTCOME_CLASS_FAILED` and `Outcome: FAILED`.
     - `fail-gate` with `refusal={"code": "SPEC-PRODUCTION-FAILED", "reason": "correction turn exited 1"}` and `attempts=[{"number": 1, "exit_code": 0}]` -> `OUTCOME_CLASS_FAILED` and `Outcome: FAILED`.
     - Mixed queue `[executed_item, crashed_fail_gate_item]` -> `Outcome: PARTIAL` (instead of `Outcome: BLOCKED`).
     - `fail-gate` with `attempts=[{"number": 1, "exit_code": 0}]` and `last_outcome={"disposition": "executed"}` (or `"substantially-complete"`), no refusal, and no non-landing `integration_signal` (e.g. `--no-self-finalize`) -> `OUTCOME_CLASS_SUCCESS` and `Outcome: COMPLETED`.
     - `fail-gate` with `attempts=[{"number": 1, "exit_code": 0}]`, `last_outcome={"disposition": "executed"}`, no refusal, and `integration_signal="suite-failed"` -> `OUTCOME_CLASS_SUCCESS`, `work_did_not_land` is true, and `render_run_summary_table` renders `Outcome: STRANDED`.
     - `fail-gate` with `attempts=[{"number": 1, "exit_code": 0}]`, `last_outcome={"disposition": "executed"}`, and `finalize_refusal={"code": "finalize-refused", "reason": "unchecked E-01"}` -> `OUTCOME_CLASS_BLOCKED` and `Outcome: BLOCKED`.
     - `fail-gate` with `proposal_record` / `awaiting-human-decision`, `SPEC-PLAN-LINT`, `clean-base-refused`, or bare `attempts=[]` -> `OUTCOME_CLASS_BLOCKED` and `Outcome: BLOCKED`.

## Deferred / out of scope (with reason)

- Changing `runner_shared.reconcile_disposition` or `runner_shared.outcome_precedence_disposition` status tokens: out of scope because backlog item `1h98o3` and spec `77tr3o` intentionally keep `"fail-gate"` as the single canonical status token and require discriminating producers in `render_stream.py` from recorded item/attempt fields rather than minting or reverting status tokens.

## Scope check

- Over-scope: none.
- Under-scope: none — all three live `"fail-gate"` producer families in `runner_shared.py` (`exit_code != 0` / turn-failure / production-crash, executed-claim-not-moved `last_outcome`, and human-gated refusals) and their interactions with `work_did_not_land` and `refusal_of_item` in `render_run_summary_table` are covered.

## Required tests / validation

- Focused test run: `python3 -m pytest tests/test_outcome_word_ladder.py tests/test_zero_dispatch_outcome.py tests/test_review_failure_reason.py`
- Full repository test suite: `python3 -m pytest`

## Spec / documentation sync

- N/A with reason: spec `77tr3o` defines `"fail-gate"` as the canonical status token for gate refusals and non-zero/unmoved reconciliation, while the run summary `Outcome:` header word is an internal rendering concern in `agent_workflows/render_stream.py` tracked by backlog item `1h98o3`.

## Open questions

### OQ-01: How should an executed-claim-not-moved `fail-gate` item be classified when `self_finalize` subsequently records a finalize gate refusal (`finalize-refused`) versus when integration fails (`integration_signal="suite-failed"`)?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in `agent_workflows/runner_shared.py` (`execute_item_core`, `handle_finalize_refusal`) and `agent_workflows/render_stream.py` (`refusal_of_item`, `work_did_not_land`). When `self_finalize` refuses, `handle_finalize_refusal` records `item["finalize_refusal"]` (surfaced by `refusal_of_item(item)` with `code="finalize-refused"`), which is a genuine gate refusal awaiting human/agent remediation and therefore stays `OUTCOME_CLASS_BLOCKED` (`BLOCKED`). When `self_finalize` is skipped because the integration gate did not earn (`integration_signal="suite-failed"` or `"verifier-declined"`), no gate refusal is recorded (`refusal_of_item(item) is None`) and `work_did_not_land(item)` is true; classifying the item as `OUTCOME_CLASS_SUCCESS` (matching pre-`6b94a4d9d` `"substantially-complete"`) allows the ladder to bypass `BLOCKED` and reach the `STRANDED` arm (`elif any(work_did_not_land(it) for it in queue): outcome_str = STRANDED_OUTCOME`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/render_stream.py` showing `outcome_class_of_item(item)` defined next to `RUN_OUTCOME_CLASS_BY_STATUS` and handling all three `"fail-gate"` producer cases (attempt failure / nonzero exit / host error / production-crash refusal code -> `OUTCOME_CLASS_FAILED`; refusal-free executed/completed/substantially-complete `last_outcome` -> `OUTCOME_CLASS_SUCCESS`; gate refusals and bare `fail-gate` -> `OUTCOME_CLASS_BLOCKED`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/render_stream.py` showing `render_run_summary_table`'s outcome-word ladder calling `outcome_class_of_item(it)` in the `all_failed`, `BLOCKED`, and `COMPLETED` / `PARTIAL` arms.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of `python3 -m pytest tests/test_outcome_word_ladder.py tests/test_zero_dispatch_outcome.py tests/test_review_failure_reason.py` and `python3 -m pytest` showing all new and existing tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is at `- Status: to-review`. Once reviewed and approved, execute `E-01`..`E-03`, validate `V-01`..`V-03` with pasted command output, commit only the scoped paths via `aw commit rowilw -- agent_workflows/render_stream.py tests/test_outcome_word_ladder.py`, and finalize through the runner or `aw ipd set executed rowilw`.
