# IPD: Print reclassified refusal reason on unmeasured integration failure instead of raw combined-red

- Date: 2026-10-17
- Kind: child
- Concern: When post-merge revalidation is unmeasured (`measured: False`, e.g. harness fault or suite execution crash), `runner_shared.record_integration_refusal` reclassifies the refusal kind to `merge-unchecked` and writes the reclassified explanation to `item["integration_deferral"]`, but operator-facing refusal reporting (the stderr console line in `execute_item_core` and `land_retired_lane_turn`, the structured refusal reason in `render_record_integration_refusal`, and the prompt in `ask_operator_about_integration` on deferred retry) prints or displays the raw gate `integ_reason` which still reads "integration gate did not pass (integration_failed_combined_red)...", misleading the operator into thinking the code failed revalidation when the gate could not measure.
- Scope: Update `execute_item_core`, `land_retired_lane_turn`, and `reattempt_deferred_integrations` in `agent_workflows/runner_shared.py` to use the reclassified refusal reason (`item.get("integration_deferral") or integ_reason`) for console stderr output, `render_record_integration_refusal` refusal recording, and operator interactive retry questions. Add behavioral tests covering first-attempt execution refusal, retired lane refusal, and deferred re-attempt refusal under unmeasured revalidation failures in `tests/test_unmeasured_refusal_console.py`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_unmeasured_refusal_console.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: geajrj
- Blocks-Release: next
- Set: geajrj
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: h8peam

## Workflow history

- 2026-10-17 draft (antigravity): created.
- 2026-10-17 to-review (antigravity): authored from backlog geajrj with findings, checklist, and validation.

## Goal

Ensure operator-facing console output and refusal metadata consistently report the reclassified refusal reason (`item["integration_deferral"]`) rather than the raw gate reason when an integration is refused due to an unmeasured post-merge revalidation, eliminating spurious "combined-red" messages for harness faults and unmeasured refusals.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Production console and refusal reason updates

- [ ] E-01 In `agent_workflows/runner_shared.py`, update `execute_item_core` and `land_retired_lane_turn` so that when `record_integration_refusal` has evaluated the refusal and recorded `item["integration_deferral"]`, the effective reason used for `render_record_integration_refusal` and the stderr warning line is `item.get("integration_deferral") or integ_reason` (falling back to the raw gate reason only if `integration_deferral` is absent). Specifically:
  1. In `execute_item_core` (lines around 44140-44185), compute `effective_reason = item.get("integration_deferral") or read_integration_cause(recorded_reason)[2]`; pass `reason=effective_reason` to `render_record_integration_refusal(...)`, and print `effective_reason` in the yellow `f"  ! IPD {item['id6']} finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {effective_reason}"` line to stderr.
  2. In `land_retired_lane_turn` (lines around 37420-37430), compute `effective_reason = item.get("integration_deferral") or integ_reason`; print `effective_reason` in the yellow `f"  ! IPD {item['id6']} retired on lane {wt_handle.branch} but NOT integrated to main ({decision.status}): {effective_reason}"` line to stderr.
  - Depends on: none
  - Expected outcome: for an unmeasured revalidation failure, stderr and `item["refusal"]["reason"]` show "integration refused because the post-merge revalidation COULD NOT MEASURE the merge result..." instead of "integration_failed_combined_red ... (per-lane-green + combined-red)".
  - Execution state: pending
- [ ] E-02 In `agent_workflows/runner_shared.py`, update `reattempt_deferred_integrations` (lines around 12340-12360) so that after `decision = record_integration_refusal(...)`, the prompt question passed to `ask_operator_about_integration(str(item.get("id6") or ""), reason, interactive=interactive)` uses `effective_reason = item.get("integration_deferral") or reason` instead of the raw `reason`.
  - Depends on: none
  - Expected outcome: if a deferred re-attempt exhausts its automatic rungs and prompts the operator interactively, the prompt question displays the reclassified reason stating that revalidation could not measure rather than the raw combined-red message.
  - Execution state: pending

### Task group 2: Behavioral test coverage

- [ ] E-03 Create `tests/test_unmeasured_refusal_console.py` with behavioral tests:
  1. First-attempt execute path: invoke `execute_item_core` (with an unmeasured post-merge revalidation where `revalidation_was_unmeasured(item)` is True), capturing stderr; assert that stderr contains `could not MEASURE`, assert that stderr does NOT contain `integration_failed_combined_red`, and assert that `item["refusal"]["reason"]` contains `could not MEASURE`.
  2. Retired lane path: invoke `land_retired_lane_turn` with an unmeasured post-merge revalidation refusal, capturing stderr; assert that stderr contains `could not MEASURE` and does NOT contain `integration_failed_combined_red`.
  3. Deferred re-attempt path: invoke `reattempt_deferred_integrations` with an unmeasured refusal with `ask=True` and `interactive=True`, capturing the prompt string; assert that the question contains `could not MEASURE` and does NOT contain `integration_failed_combined_red`.
  4. Non-regression control: test that a genuine measured failure (`measured=True`, real suite failure or git conflict) still preserves and prints the genuine failure reason and gate status without regression.
  - Depends on: E-01, E-02
  - Expected outcome: all four test cases pass; no tests assert on internal source code or line counts.
  - Execution state: pending
- [ ] E-04 Run the new test module `tests/test_unmeasured_refusal_console.py`, related existing test modules (`tests/test_runner_shared.py`, `tests/test_forkresid_shared_shells.py`, `tests/test_deferred_reattempt_revalidation.py`), the bare core test suite `python3 -m pytest`, and the leak sanitizer `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all test suites pass with zero failures; leak sanitizer reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Refusal reclassification convention: in `runner_shared.record_integration_refusal`, when `integ_kind == INTEGRATION_REFUSAL_CONFLICT and revalidation_was_unmeasured(item)`, `integ_kind` is reclassified to `INTEGRATION_REFUSAL_UNMEASURED` and `integ_reason` is updated to `"integration refused because the post-merge revalidation COULD NOT MEASURE the merge result (this is NOT a merge conflict and NOT a failing suite): ..."`.
- `record_integration_refusal` writes `item["integration_deferral"] = integ_reason` and `attempt["integration_deferred"] = integ_reason`.
- Operator-facing stderr lines: in `execute_item_core`, the console line prints `f"  ! IPD {item['id6']} finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {integ_reason}"` using the pre-reclassification `integ_reason`.
- Tests must assert observable behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); tests must execute the code and assert on real outputs, exit codes, captured stderr, or recorded dictionary fields, never on source text or AST inspection.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | `record_integration_refusal` reclassifies an unmeasured post-merge revalidation refusal to `merge-unchecked` and writes the explanatory reason to `item["integration_deferral"]` | `agent_workflows/runner_shared.py` `record_integration_refusal` ("RECLASSIFY A REFUSAL THE GATE COULD NOT MEASURE"); `item["integration_deferral"] = integ_reason` |
| F-2 | In `execute_item_core`, the operator console warning on stderr prints `integ_reason` rather than `item.get("integration_deferral")`, printing the raw gate message "integration_failed_combined_red ... (per-lane-green + combined-red)" | `agent_workflows/runner_shared.py` `execute_item_core` "finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {integ_reason}" |
| F-3 | In `execute_item_core`, `render_record_integration_refusal` is passed `read_integration_cause(recorded_reason)[2]`, storing the raw un-reclassified gate message into `item["refusal"]["reason"]` | `agent_workflows/runner_shared.py` `execute_item_core` `render_record_integration_refusal(item, code=fail_status, reason=read_integration_cause(recorded_reason)[2], ...)` |
| F-4 | In `land_retired_lane_turn`, stderr similarly prints `integ_reason` rather than `item.get("integration_deferral")` | `agent_workflows/runner_shared.py` `land_retired_lane_turn` "retired on lane {wt_handle.branch} but NOT integrated to main ({decision.status}): {integ_reason}" |
| F-5 | In `reattempt_deferred_integrations`, when automatic rungs are exhausted and `ask_operator_about_integration` is called, it receives raw `reason` rather than `item.get("integration_deferral")`, formatting the interactive question with the raw combined-red message | `agent_workflows/runner_shared.py` `reattempt_deferred_integrations` `answer = ask_operator_about_integration(str(item.get("id6") or ""), reason, interactive=interactive)` |
| F-6 | Review of plan `xc1xh9` (`.aw/records/reviews/20261017-vtcqpf-01-xc1xh9-prove-end-to-end-that-a-budget-only-post-merge-red-is-never.review.md`, PR-003 / F-7) verified that prototype stderr printed the combined-red line for an item recorded as `merge-unchecked`, and filed backlog `geajrj` | `.aw/records/plans/pending/20261017-vtcqpf-01-xc1xh9-prove-end-to-end-that-a-budget-only-post-merge-red-is-never.ipd.md` F-7; backlog `geajrj` Detail |

## Proposed changes (ordered, validatable)

1. E-01: update `execute_item_core` and `land_retired_lane_turn` to use `item.get("integration_deferral") or integ_reason` for stderr reporting and `render_record_integration_refusal`.
2. E-02: update `reattempt_deferred_integrations` to pass `item.get("integration_deferral") or reason` to `ask_operator_about_integration`.
3. E-03: author behavioral tests in `tests/test_unmeasured_refusal_console.py` verifying all three sites print and record the reclassified reason for unmeasured failures, while preserving genuine failure messages for measured failures.
4. E-04: execute new tests, regression tests, core suite, and leak sanitizer.

## Deferred / out of scope (with reason)

- Classifying a budget-only post-merge red as unmeasured in `SuiteCheckResult`: designed in plan `sa629y`, graduated from duplicate backlog item `o58dro`.
  - Carrier: sa629y
- End-to-end host-level proof of budget-only revalidation deferral and re-attempt: designed in plan `xc1xh9` (graduated from backlog item `vtcqpf`).
  - Carrier: xc1xh9
- Load-aware budget enforcement in bare pytest and send-back wording: designed in plan `44nfmd` (Set `48hjbx`).
  - Carrier: 44nfmd
- Seam regression tests under the default demotion: designed in plan `t54fet` (Set `m8d13e`).
  - Carrier: t54fet

## Scope check

- Over-scope: none; scoped strictly to console stderr reporting and refusal reason propagation across `execute_item_core`, `land_retired_lane_turn`, and `reattempt_deferred_integrations`.
- Under-scope: none; all operator-facing refusal reporting sites on first-attempt and deferred re-attempt paths are addressed, accompanied by behavioral tests and non-regression controls.

## Required tests / validation

- `python3 -m pytest -v tests/test_unmeasured_refusal_console.py` passes (V-03).
- `python3 -m pytest tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py` passes (V-04).
- Bare core suite `python3 -m pytest` passes (V-04).
- Leak sanitizer `aw sanitize --agent` passes with exit code 0 (V-04).

## Spec / documentation sync

N/A: no specification or external documentation pins the exact stderr diagnostic text; this change aligns console output with the existing `l2mzxn` internal state contract (`item["integration_deferral"]`).

## Open questions

### OQ-01: Should `render_record_integration_refusal` also receive the reclassified reason?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. `render_stream.record_integration_refusal` writes `item["refusal"]["reason"]`. Passing the raw pre-reclassification reason would leave `item["refusal"]` claiming a combined-red failure while `item["integration_deferral"]` and stderr report an unmeasured refusal. Using `item.get("integration_deferral") or read_integration_cause(recorded_reason)[2]` keeps all refusal records consistent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` hunks for `execute_item_core` and `land_retired_lane_turn` demonstrating `item.get("integration_deferral") or integ_reason` (and `recorded_reason`) is wired to `render_record_integration_refusal` and the stderr `print` statements.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` hunk for `reattempt_deferred_integrations` demonstrating `item.get("integration_deferral") or reason` is passed to `ask_operator_about_integration`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -v tests/test_unmeasured_refusal_console.py` output showing all 4 behavioral test cases pass with zero failures.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste summary lines from running the related test modules, bare `python3 -m pytest` core suite, and `aw sanitize --agent` showing zero failures and clean exit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit h8peam -- agent_workflows/runner_shared.py tests/test_unmeasured_refusal_console.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
