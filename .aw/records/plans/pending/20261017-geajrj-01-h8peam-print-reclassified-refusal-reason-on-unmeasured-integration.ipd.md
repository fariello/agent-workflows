# IPD: Print reclassified refusal reason on unmeasured integration failure instead of raw combined-red

- Date: 2026-10-17
- Kind: child
- Concern: When post-merge revalidation is unmeasured (`measured: False`, e.g. a harness fault, a suite that raised, or a budget-only red), `runner_shared.record_integration_refusal` reclassifies the refusal kind to `merge-unchecked` and writes the reclassified, token-stripped explanation to `item["integration_deferral"]`, but three operator-facing surfaces still carry the raw gate reason ("[aw-integration-cause=gate-combined-red] integration gate did not pass (integration_failed_combined_red) ... (per-lane-green + combined-red)"): the stderr console line in `execute_item_core` and in `integrate_retired_lane`, the structured `item["refusal"]["reason"]` written by `render_record_integration_refusal` in `execute_item_core` (which additionally asserts "measured the merged tree and it was RED"), and the rung-3 prompt in `ask_operator_about_integration` on a deferred re-attempt. Each misleads the operator into thinking the code failed revalidation when the gate could not measure, and the console and prompt surfaces also leak the internal cause token.
- Scope: In `agent_workflows/runner_shared.py`, make `execute_item_core`, `integrate_retired_lane`, and `reattempt_deferred_integrations` read the operator-facing reason from `item["integration_deferral"]` (the value `record_integration_refusal` has just written, already reclassified and token-stripped) for the stderr line, the `render_record_integration_refusal` refusal reason, and the rung-3 operator question. Add behavioral tests covering the first-attempt execute refusal on both hosts, the retired-lane refusal, the deferred re-attempt prompt, and a measured-red non-regression control in `tests/test_unmeasured_refusal_console.py`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_unmeasured_refusal_console.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: geajrj
- Blocks-Release: next
- Set: geajrj
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: h8peam

## Workflow history
- 2026-10-18 reviewed (plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007

- 2026-10-17 draft (antigravity): created.
- 2026-10-17 to-review (antigravity): authored from backlog geajrj with findings, checklist, and validation.

## Goal

Ensure operator-facing console output, the structured refusal record, and the rung-3 operator question consistently report the reclassified refusal reason (`item["integration_deferral"]`) rather than the raw gate reason when an integration is refused due to an unmeasured post-merge revalidation, eliminating spurious "combined-red" messages (and the leaked `[aw-integration-cause=...]` token) for harness faults and unmeasured refusals.

Non-goals: no change to the refusal KIND, status, ladder verdict, deferral budget, events, or `item["integration_deferral"]` itself (all already correct, F-1); no change to the review-integration report (`format_review_integration_refusal_report`), which never runs the revalidation gate and so cannot be unmeasured (F-8); no change to `reintegrate_lane` (the out-of-band `integrate` verb), which does not call `record_integration_refusal` (F-8).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Production console and refusal reason updates

- [ ] E-01 In `agent_workflows/runner_shared.py` `execute_item_core`, in the execute arm's refusal block that calls `decision = record_integration_refusal(... integ_reason=recorded_reason ...)` (near the `print` of "finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {integ_reason}"), compute ONE operator-facing reason immediately after that call and use it at both downstream sites:
  1. `operator_reason = item.get("integration_deferral") or read_integration_cause(recorded_reason)[2]`. `record_integration_refusal` always writes `item["integration_deferral"]` (already reclassified for an unmeasured refusal and already token-stripped), so the fallback is defence in depth only; it MUST strip the cause token, so do NOT fall back to bare `integ_reason`.
  2. Pass `reason=operator_reason` to `render_record_integration_refusal(...)` (replacing `read_integration_cause(recorded_reason)[2]`). For a measured refusal this is byte-identical to today, because `integration_deferral` IS `read_integration_cause(recorded_reason)[2]`.
  3. Print `operator_reason` in place of `{integ_reason}` in the yellow "finalized on lane ... but NOT integrated to main ({fail_status}): ..." stderr line. For a measured refusal this intentionally changes the line from the raw tagged gate reason to the recorded reason (token stripped, budget-exhausted prefix where one applies), which is the same text the refusal record and the run summary already show (OQ-02).
  - Depends on: none
  - Expected outcome: for an unmeasured refusal on the execute path, the stderr line and `item["refusal"]["reason"]` both begin "integration refused because the post-merge revalidation COULD NOT MEASURE the merge result" and neither contains `integration_failed_combined_red`, `it was RED`, or `[aw-integration-cause=`; for a measured refusal `item["refusal"]["reason"]` is unchanged.
  - Execution state: pending
- [ ] E-02 In `agent_workflows/runner_shared.py` `integrate_retired_lane` (the shared function behind the retired-lane landing; there is no `land_retired_lane_turn`), after `decision = record_integration_refusal(... integ_reason=integ_reason ...)`, print `item.get("integration_deferral") or read_integration_cause(integ_reason)[2]` in place of `{integ_reason}` in the yellow "retired on lane {wt_handle.branch} but NOT integrated to main ({decision.status}): ..." stderr line.
  - Depends on: none
  - Expected outcome: for an unmeasured refusal on the retired-lane path, the stderr line carries the reclassified "COULD NOT MEASURE" reason and contains neither `integration_failed_combined_red` nor `[aw-integration-cause=`.
  - Execution state: pending
- [ ] E-03 In `agent_workflows/runner_shared.py` `reattempt_deferred_integrations`, in the rung-3 branch (`if not decision.deferred and ask and interactive:`), pass `item.get("integration_deferral") or read_integration_cause(reason)[2]` as the reason argument of `ask_operator_about_integration(str(item.get("id6") or ""), ..., interactive=interactive)` instead of the raw `reason`. Do NOT rebind `reason` itself: it is reassigned by the operator-approved retry just below and feeds `do_finish`.
  - Depends on: none
  - Expected outcome: when a deferred re-attempt of an unmeasured refusal exhausts its budget and prompts interactively, the question reads "lane <id6> cannot integrate: integration refused because the post-merge revalidation COULD NOT MEASURE ..." and contains neither `integration_failed_combined_red` nor `[aw-integration-cause=`.
  - Execution state: pending

### Task group 2: Behavioral test coverage

- [ ] E-04 Create `tests/test_unmeasured_refusal_console.py` with behavioral tests that drive real code and assert on captured stderr, recorded item fields, and the captured prompt string (never on source text). Match the reclassified wording CASE-SENSITIVELY on `COULD NOT MEASURE` (the prefix `record_integration_refusal` writes); do NOT use lowercase `could not MEASURE` as the discriminator, because the deferral verdict line `-> {decision.reason}` (from `decide_integration_deferral`) already prints that phrase on today's code, so such an assertion passes before the fix (F-9). Assert the absence of `integration_failed_combined_red` and `[aw-integration-cause=` on the SPECIFIC "NOT integrated to main" line, not merely on the whole stderr. Fixtures (all demonstrated at review, D-3):
  1. First-attempt execute path, BOTH hosts: reuse `tests.test_budget_only_combined_red_e2e.TestBudgetOnlyCombinedRedE2E._setup_driver_fixture` (or an equivalent local fixture) and drive `oc_runipd.execute_item` / `agy_runipd.execute_item` (each delegates to `runner_shared.execute_item_core`) with `run_suite_check` patched to return a `budget_only=True` `SuiteCheckResult` for revalidation paths, `start_suite_baseline` patched to `(None, None)`, the host launcher (`run_opencode` / `run_agy_turn`) patched to commit a lane change and write an `executed` outcome, the coordinator execution role declared via `tests.support.declare_execution_role(self)`, and stderr captured with `contextlib.redirect_stderr`. Assert `item["integration_ladder"]["kind"] == runner_shared.INTEGRATION_REFUSAL_UNMEASURED`, the "NOT integrated to main" stderr line contains `COULD NOT MEASURE` and neither forbidden string, and `item["refusal"]["reason"]` contains `COULD NOT MEASURE` and neither `integration_failed_combined_red` nor `it was RED`.
  2. Retired-lane path: call `runner_shared.integrate_retired_lane` directly with a `git init` repo, an `integrate_lane_branch` stub that writes `item[runner_shared.REVALIDATION_CACHE_KEY] = {"passed": False, "measured": False, "reason": ...}` and returns `(False, <tagged combined-red gate reason built with runner_shared.tag_integration_cause>, runner_shared.INTEGRATION_REFUSAL_CONFLICT)`, a handle object with a `branch` attribute, and no-op `save_state`/`append_jsonl`. Assert the returned disposition is `runner_shared.INTEGRATION_DEFERRED_STATUS` and the "retired on lane ... NOT integrated to main" stderr line contains `COULD NOT MEASURE` and neither forbidden string.
  3. Deferred re-attempt path: call `runner_shared.reattempt_deferred_integrations` with one item in `runner_shared.INTEGRATION_DEFERRED_STATUS` carrying `integration_attempts: 1`, `options.integration_retry_limit: 0` (so the refusal is terminal and rung 3 is reached), an `integrate` stub like fixture 2, `ask=True`, `interactive=True`, and `runner_shared.prompt_for_gate_phrase` patched to capture the question and return `None`. Assert exactly one question was captured, it contains `COULD NOT MEASURE`, and it contains neither forbidden string.
  4. Non-regression control (measured red): fixture 1 on one host with a measured failing `SuiteCheckResult` (`budget_only=False`, a non-empty `failures` tuple) and `retry_budget=0` so no send-back turn is spent. Assert `item["integration_ladder"]["kind"]` is NOT `INTEGRATION_REFUSAL_UNMEASURED`, `item["refusal"]["reason"]` still contains `integration_failed_combined_red` (the genuine gate status is preserved), the stderr line contains `integration_failed_combined_red` and does NOT contain `COULD NOT MEASURE` or `[aw-integration-cause=`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: every case above passes after E-01 to E-03, and cases 1 to 3 FAIL when run against the pre-change `runner_shared.py` (the executor demonstrates this, see V-04); no test inspects source code, counts callers, or pins line numbers.
  - Execution state: pending
- [ ] E-05 Run the new test module, the related existing modules `tests/test_budget_only_combined_red_e2e.py`, `tests/test_runner_shared.py`, `tests/test_forkresid_shared_shells.py`, `tests/test_deferred_reattempt_revalidation.py`, `tests/test_oc_runipd.py`, and `tests/test_agy_runipd_cli.py`, then the bare core suite `python3 -m pytest`, then the leak sanitizer `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: every run reports zero failures and zero errors; the sanitizer exits 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Refusal reclassification convention: in `runner_shared.record_integration_refusal`, when `integ_kind == INTEGRATION_REFUSAL_CONFLICT and revalidation_was_unmeasured(item)`, `integ_kind` is reclassified to `INTEGRATION_REFUSAL_UNMEASURED` and `integ_reason` is updated to `"integration refused because the post-merge revalidation COULD NOT MEASURE the merge result (this is NOT a merge conflict and NOT a failing suite): ..."`.
- `record_integration_refusal` writes `item["integration_deferral"] = integ_reason` and `attempt["integration_deferred"] = integ_reason`.
- Operator-facing stderr lines: in `execute_item_core`, the console line prints `f"  ! IPD {item['id6']} finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {integ_reason}"` using the pre-reclassification `integ_reason`; `integrate_retired_lane` prints the same shape with "retired on lane".
- Cause-token channel: refusal reasons carry an `[aw-integration-cause=...]` prefix written by `runner_shared.tag_integration_cause` and stripped by `runner_shared.read_integration_cause`, whose docstring says "THE TOKENS ARE STRIPPED, so nothing an operator reads carries one". Any fallback this plan writes must go through `read_integration_cause`.
- Tests must assert observable behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); tests must execute the code and assert on real outputs, exit codes, captured stderr, or recorded dictionary fields, never on source text or AST inspection.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | `record_integration_refusal` reclassifies an unmeasured post-merge revalidation refusal to `merge-unchecked` and writes the explanatory reason to `item["integration_deferral"]` | `agent_workflows/runner_shared.py` `record_integration_refusal` ("RECLASSIFY A REFUSAL THE GATE COULD NOT MEASURE"); `item["integration_deferral"] = integ_reason` |
| F-2 | In `execute_item_core`, the operator console warning on stderr prints `integ_reason` rather than `item.get("integration_deferral")`, printing the raw gate message WITH its cause token. Measured at review (HEAD `08fa69666`, both hosts, budget-only red): `  ! IPD wir001 finalized on lane aw/lane/wir001 but NOT integrated to main (merge-retry): [aw-integration-cause=gate-combined-red] integration gate did not pass (integration_failed_combined_red): full_revalidation_check[integration]: Full test suite / revalidation failed after merging isolated lanes (per-lane-green + combined-red).` while the ladder kind was `merge-unchecked` | `agent_workflows/runner_shared.py` `execute_item_core` "finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {integ_reason}" |
| F-3 | In `execute_item_core`, `render_record_integration_refusal` is passed `read_integration_cause(recorded_reason)[2]`, the PRE-reclassification reason. Worse than a raw gate message: because the cause token is `gate-combined-red`, `recorded_reason` was first rewritten to the budget-exhausted wording, so the measured `item["refusal"]["reason"]` read `the post-merge revalidation measured the merged tree and it was RED and the run's correction budget is exhausted (0 of 2 retries spent): integration gate did not pass (integration_failed_combined_red): ...` for an item the ladder recorded as unmeasured and deferred | `agent_workflows/runner_shared.py` `execute_item_core` `elif cause == INTEGRATION_CAUSE_GATE_COMBINED_RED:` ... "measured the merged tree and it was RED"; `render_record_integration_refusal(item, code=fail_status, reason=read_integration_cause(recorded_reason)[2], ...)` |
| F-4 | In `integrate_retired_lane`, stderr similarly prints raw `integ_reason`. Measured at review: `  ! IPD ret001 retired on lane aw/lane/ret001 but NOT integrated to main (merge-retry): [aw-integration-cause=gate-combined-red] integration gate did not pass (integration_failed_combined_red): ...` with ladder kind `merge-unchecked` | `agent_workflows/runner_shared.py` `integrate_retired_lane`; "retired on lane {wt_handle.branch} but NOT integrated to main ({decision.status}): {integ_reason}" |
| F-5 | In `reattempt_deferred_integrations`, when automatic rungs are exhausted and `ask_operator_about_integration` is called, it receives raw `reason`. Measured at review: the captured question was `  ? lane abc123 cannot integrate: [aw-integration-cause=gate-combined-red] integration gate did not pass (integration_failed_combined_red): ...` | `agent_workflows/runner_shared.py` `reattempt_deferred_integrations` `answer = ask_operator_about_integration(str(item.get("id6") or ""), reason, interactive=interactive)`; `ask_operator_about_integration` "cannot integrate: {reason}" |
| F-8 | The other refusal-reporting sites need no change: the review-integration path (`format_review_integration_refusal_report`, called from `execute_item_core` with `review_reason`) uses `integrate_review_lane_branch`, which runs no revalidation gate and so never yields an unmeasured refusal; `reintegrate_lane` (the `integrate` verb) never calls `record_integration_refusal` and reports its own suite reason | `agent_workflows/runner_shared.py` `format_review_integration_refusal_report`; `reintegrate_lane`; `integrate_lane_branch` `action_kind` "SELECTS WHETHER STEP 1's REVALIDATION GATE RUNS" |
| F-9 | Today's stderr for an unmeasured refusal ALREADY contains lowercase "could not MEASURE", on the cyan deferral-verdict line `-> integration DEFERRED (attempt 1 of 11): the post-merge revalidation could not MEASURE the merge result ...`, so a whole-stderr `assertIn("could not MEASURE", stderr)` passes before the fix. The reclassified reason itself uses uppercase "COULD NOT MEASURE" | measured at review (both hosts); `agent_workflows/runner_shared.py` `decide_integration_deferral` "could not MEASURE the merge result"; `record_integration_refusal` "COULD NOT MEASURE the merge" |
| F-6 | Review of plan `xc1xh9` (`.aw/records/reviews/20261017-vtcqpf-01-xc1xh9-prove-end-to-end-that-a-budget-only-post-merge-red-is-never.review.md`, PR-003 / F-7) verified that prototype stderr printed the combined-red line for an item recorded as `merge-unchecked`, and filed backlog `geajrj` | `.aw/records/plans/pending/20261017-vtcqpf-01-xc1xh9-prove-end-to-end-that-a-budget-only-post-merge-red-is-never.ipd.md` F-7; backlog `geajrj` Detail |

## Proposed changes (ordered, validatable)

1. E-01: `execute_item_core` uses `item.get("integration_deferral") or read_integration_cause(recorded_reason)[2]` for both the stderr line and `render_record_integration_refusal`.
2. E-02: `integrate_retired_lane` uses `item.get("integration_deferral") or read_integration_cause(integ_reason)[2]` for its stderr line.
3. E-03: `reattempt_deferred_integrations` passes `item.get("integration_deferral") or read_integration_cause(reason)[2]` to `ask_operator_about_integration`.
4. E-04: author behavioral tests in `tests/test_unmeasured_refusal_console.py` covering all three sites (execute on both hosts) plus a measured-red control.
5. E-05: run the new tests, the related regression modules, the core suite, and the leak sanitizer.

## Deferred / out of scope (with reason)

- Classifying a budget-only post-merge red as unmeasured in `SuiteCheckResult`: designed in plan `sa629y`, graduated from duplicate backlog item `o58dro`.
  - Carrier: sa629y
  - Carrier-Evidence: .aw/records/plans/executed/20261017-o58dro-01-sa629y-budget-only-post-merge-red-defers-as-unmeasured.ipd.md
- End-to-end host-level proof of budget-only revalidation deferral and re-attempt: designed in plan `xc1xh9` (graduated from backlog item `vtcqpf`).
  - Carrier: xc1xh9
  - Carrier-Evidence: .aw/records/plans/executed/20261017-vtcqpf-01-xc1xh9-prove-end-to-end-that-a-budget-only-post-merge-red-is-never.ipd.md
- Load-aware budget enforcement in bare pytest and send-back wording: designed in plan `44nfmd` (Set `48hjbx`).
  - Carrier: 44nfmd
  - Carrier-Evidence: .aw/records/plans/executed/20261017-48hjbx-01-44nfmd-make-the-core-tier-wall-time-budget-load-aware-and-name-a-bu.ipd.md
- Seam regression tests under the default demotion: designed in plan `t54fet` (Set `m8d13e`).
  - Carrier: t54fet
  - Carrier-Evidence: .aw/records/plans/executed/20261017-m8d13e-01-t54fet-prove-every-runner-revalidation-seam-reports-an-all-green-ov.ipd.md

## Scope check

- Over-scope: none; scoped strictly to the operator-facing reason at the three sites in `execute_item_core`, `integrate_retired_lane`, and `reattempt_deferred_integrations`.
- Under-scope: none; every site that calls `record_integration_refusal` on an execute-gated integration and then reports a reason to an operator is covered (F-8 records why the review path and `reintegrate_lane` are not), with behavioral tests and a measured-red control.

Invariants and the test that pins each:
- I-1 An unmeasured refusal is never reported to an operator as combined-red: E-04 cases 1 to 3.
- I-2 No operator-facing line carries an `[aw-integration-cause=...]` token (`read_integration_cause` docstring): E-04 cases 1 to 4.
- I-3 A measured red still reports the genuine gate status: E-04 case 4.
- I-4 Refusal kind, status, ladder verdict and deferral budget are unchanged: E-05 existing modules (`tests/test_budget_only_combined_red_e2e.py`, `tests/test_runner_shared.py`).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_unmeasured_refusal_console.py` passes, and cases 1 to 3 fail against the pre-change `runner_shared.py` (V-04).
- `python3 -m pytest tests/test_unmeasured_refusal_console.py tests/test_budget_only_combined_red_e2e.py tests/test_runner_shared.py tests/test_forkresid_shared_shells.py tests/test_deferred_reattempt_revalidation.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` passes (V-05).
- Bare core suite `python3 -m pytest` passes (V-05).
- Leak sanitizer `aw sanitize --agent` passes with exit code 0 (V-05).

## Spec / documentation sync

N/A: verified at review that no spec, doc, or test pins the stderr "NOT integrated to main" text or the "cannot integrate:" prompt text (searched `.aw/records/specs/`, `docs/`, and `tests/`; the only test hits are docstrings/comments in `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`). This change aligns console output with the existing `l2mzxn` internal state contract (`item["integration_deferral"]`) and the `read_integration_cause` no-token-to-operators contract; it changes no behavior a spec describes, so no spec is amended and none is listed in `- Scope-Paths:`.

## Open questions

### OQ-01: Should `render_record_integration_refusal` also receive the reclassified reason?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. `render_stream.record_integration_refusal` writes `item["refusal"]["reason"]`. Passing the pre-reclassification reason leaves `item["refusal"]` claiming "measured the merged tree and it was RED" (measured at review, F-3) while `item["integration_deferral"]` reports an unmeasured refusal. Using `item.get("integration_deferral") or read_integration_cause(recorded_reason)[2]` keeps all refusal records consistent, and for a measured refusal is byte-identical to today because `record_integration_refusal` sets `integration_deferral` to exactly `read_integration_cause(recorded_reason)[2]` (`agent_workflows/runner_shared.py` `record_integration_refusal`: `cause, shape, integ_reason = read_integration_cause(integ_reason)` then `item["integration_deferral"] = integ_reason`).

### OQ-02: Should the stderr line for a MEASURED refusal also switch to the recorded reason?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode)
- Resolution or deferral rationale: Yes. Today the measured-path stderr line prints the raw tagged `integ_reason`, leaking `[aw-integration-cause=gate-combined-red]` (measured at review), which `read_integration_cause` says must never reach an operator. Reading `integration_deferral` for every refusal is one rule instead of a measured/unmeasured branch, and it prints the same text the refusal record and run summary already show. The genuine `integration_failed_combined_red` status is still present in the measured text, which E-04 case 4 pins. Recorded as review decision D-2.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` hunk for `execute_item_core` showing one reason computed from `item.get("integration_deferral") or read_integration_cause(recorded_reason)[2]` after `record_integration_refusal`, passed as `reason=` to `render_record_integration_refusal`, and printed in the "finalized on lane ... NOT integrated to main" line.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` hunk for `integrate_retired_lane` showing the "retired on lane ... NOT integrated to main" line printing `item.get("integration_deferral") or read_integration_cause(integ_reason)[2]`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` hunk for `reattempt_deferred_integrations` showing `ask_operator_about_integration` receiving `item.get("integration_deferral") or read_integration_cause(reason)[2]` and `reason` itself not rebound.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_unmeasured_refusal_console.py` output showing every case named in E-04 (execute on both hosts, retired lane, deferred re-attempt prompt, measured control) passing with zero failures; AND paste the output of the same command run with ONLY `agent_workflows/runner_shared.py` reverted to the pre-change version (e.g. `git stash push -- agent_workflows/runner_shared.py`, run, `git stash pop`), showing the unmeasured cases FAILING on the missing `COULD NOT MEASURE` or the present forbidden string, so the tests demonstrably detect the bug.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the summary line of the related-modules pytest run named in E-05, the summary line of bare `python3 -m pytest`, and the `aw sanitize --agent` result record with its exit code, each showing zero failures/errors and exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit h8peam -- agent_workflows/runner_shared.py tests/test_unmeasured_refusal_console.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
