# IPD: Stop launching the runner suite baseline when nothing will collect it

- Date: 2026-10-12
- Kind: child
- Concern: `runner_shared.execute_item_core` starts a full-suite pre-work baseline (`start_suite_baseline`, condition: not review, not production, self-finalize, extractor and `SUITE_CHECK_ARGV` present) BEFORE the turn, but collects it only inside `if integration_gate_relevant and not validate:` after the turn, and then abandons it in the turn's `finally`. `validate` is computed after the turn (`validate = opts.get("validate", False)`, defaulting to `not (no_verify or no_audit)` when the key is absent), and is True in the default configuration. Measured over October: 322 `suite-baseline-started`, 0 `suite-baseline-collected`; of 320 baseline-bearing attempts, 318 had validation ON. Each was a full 12-worker suite thrown away.
- Scope: IN: compute the attempt's `validate` value once, BEFORE the baseline start, from the same expression, and start the baseline only when `not validate` (the only mode that collects it); a test proving both directions; one CHANGELOG line. OUT: changing what `validate` means or its default; the baseline's consumers (`revalidation_baseline_for`, `suite_baseline_context`), which only read a collected baseline; caching (Order 02).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_suite_baseline_mode_gate.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9ec94f

## Workflow history

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (record `.aw/records/reviews/20261012-suiteeff-01-9ec94f-stop-launching-the-runner-suite-baseline-when-nothing-will-c.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 01 of Set `suiteeff` from backlog `58x9mw`.

## Goal

A suite baseline is launched only when the attempt will read it, removing about one full suite per default-mode execute turn.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the gate

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` before the first edit; record its summary line and failing node ids.
  - Depends on: none
  - Expected outcome: a recorded summary line and failing-node-id list.
  - Execution state: pending

- [ ] E-02 In `runner_shared.py`, add a pure helper `attempt_validates(options: Mapping) -> bool` returning exactly today's expression (`options["validate"]` when the key is present, else `not (options.get("no_verify") or options.get("no_audit"))`), use it at the existing post-turn assignment in `execute_item_core` (so behavior there is unchanged), and add `and not attempt_validates(state.get("options", {}))` to the condition that calls `start_suite_baseline`. Comment WHY with the measured 322/0 count, and name the reason nothing else needs the baseline in ON mode: the only other reader of the pre-turn `suite_baseline` value is the `gate_answer_is_warranted` follow-up, which asks only on the suite-failure signal, and that signal cannot arise when `run_suite_check` did not run. When skipped BECAUSE OF VALIDATION ONLY (every other existing condition held: not review, not production, self-finalize, extractor and `SUITE_CHECK_ARGV` present), append one `suite-baseline-skipped` event; a review or production turn emits nothing new. The event carries `id6`, `attempt` and `reason: "validation is ON; the verifier's verdict is this attempt's trust signal and nothing collects a baseline"`, so the absence is explained, not silent.
  - Depends on: E-01
  - Expected outcome: a validation-ON attempt emits `suite-baseline-skipped`, emits no `suite-baseline-started`, and records no `attempt["suite_baseline_started"]`; a validation-OFF attempt starts and later collects the baseline exactly as today.
  - Execution state: pending

### Task group 2: tests and changelog

- [ ] E-03 Add `tests/test_suite_baseline_mode_gate.py` (behavioral, P16): (a) `attempt_validates` over the five option shapes (`validate` True present; `validate` False present; absent with `no_verify` True; absent with `no_audit` True; absent with neither) matches the expected booleans; (b) drive `execute_item_core` through `oc_runipd.execute_item` with validation ON (options as `tests/test_attempt_lane_facts.py`'s `_oc_state_and_item` builds them: `no_audit: False`, `validate` absent): assert no `suite-baseline-started` event, exactly one `suite-baseline-skipped` event, and no `attempt["suite_baseline_started"]` key; (c) the same with `validate: False`: assert `suite-baseline-started` then `suite-baseline-collected` with `state: "completed"`. HARNESS (the `tests/test_suite_baseline.py` this item originally named was deleted by `19313eed7`): reuse `tests.test_oc_runipd._init_repo_with_conforming_plan` and `tests.test_attempt_lane_facts.AttemptLaneFactsTests`' state builder and fake agent (`mock.patch.object(oc_runipd, "run_opencode", ...)`), and for cell (c) ALSO patch `oc_runipd.SUITE_CHECK_ARGV` to a fast command that prints a summary line (for example `(sys.executable, "-c", "print('1 passed')")`) and `oc_runipd.run_suite_check` to return a passing `runner_shared.SuiteCheckResult`, so the cell never runs a real pytest inside the fixture. Do NOT assert on the baseline checkout directory as the distinguishing signal: the existing `finally` removes it in both modes, so its absence cannot fail with E-02 reverted.
  - Depends on: E-02
  - Expected outcome: the file passes; cell (b) fails with E-02's condition reverted. (Measured at review with this harness on the unchanged code: default options produce `['suite-baseline-started']` and no collection; `validate: False` with the two patches produces `suite-baseline-started` then `suite-baseline-collected` state `completed`.)
  - Execution state: pending

- [ ] E-04 Add one `- Fixed:` bullet as the first `- Fixed:`/`- Changed:` bullet under `CHANGELOG.md`'s `## 2.0.0 (pending)` heading (the heading carries a trailing title; match on its prefix): runs with verification on no longer start a background test-suite baseline they never read. No em or en dashes.
  - Depends on: E-02
  - Expected outcome: one new CHANGELOG line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The baseline machinery is advisory by contract and must never fail an item (`start_suite_baseline` docstring: "This function NEVER raises").
- `integration_is_earned`'s two modes are alternatives: validation ON trusts the verifier, OFF trusts the driver-run suite; post-merge revalidation records `skipped: true` with that reason in ON mode (269 of 269 October items).
- Behavioral tests only (GUIDING_PRINCIPLES P16); run the suite bare.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | Baselines are started and never collected. | 322 `suite-baseline-started` vs 0 `suite-baseline-collected` in `.aw/records/runs/run-202610*/events.jsonl`; 0 of 318 attempts carry `attempt["suite_baseline"]`. |
| F-02 | The collector is gated on validation OFF. | `execute_item_core`: "if integration_gate_relevant and not validate:" wraps `run_suite_check` and `suite_baseline_run.collect`. |
| F-03 | Validation is ON by default. | 318 of 320 baseline-bearing attempts had `validate` absent and `no_verify` False, so `validate = not (no_verify or no_audit)` is True. |

## Proposed changes (ordered, validatable)

1. Hoist the validate computation into `attempt_validates` and gate the baseline start on it (E-02).
2. Tests (E-03), CHANGELOG (E-04).

## Deferred / out of scope (with reason)

- Whether validation-ON mode should ALSO run the driver suite: a policy question about `integration_is_earned`, not waste removal.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

New test file (E-03); the existing baseline-adjacent tests `tests/test_suite_baseline_direction.py` and `tests/test_attempt_lane_facts.py` must still pass; bare suite against E-01. Invariants: (I1) validation ON starts no baseline (E-03 b); (I2) validation OFF still starts AND collects it, so `revalidation_baseline_for` keeps its input (E-03 c); (I3) `validate`'s computed value after the turn is unchanged, since `attempt_validates` returns today's expression (E-03 a over all five shapes).

## Spec / documentation sync

N/A: no spec states that a baseline is started in validation-ON mode; spec `25kzda`'s integration modes are unchanged.

## Open questions

### OQ-01: Remove the baseline entirely instead?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED (by the plan author) to keep it for validation-OFF mode: there it feeds the relative post-merge verdict (`revalidation_baseline_for`), which measurably unblocked stranded lanes (`tgyfs2`, run `run-20260922T024054Z-2245533`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change `python3 -m pytest` summary line and failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `git diff` of `execute_item_core`'s baseline condition and `attempt_validates`, plus the pasted events.jsonl lines from E-03 cells (b) and (c) (code path: `execute_item_core` -> `attempt_validates` -> `start_suite_baseline` or `suite-baseline-skipped`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted passing run of `python3 -m pytest tests/test_suite_baseline_mode_gate.py tests/test_suite_baseline_direction.py tests/test_attempt_lane_facts.py`; pasted failing cell (b) with E-02's condition reverted (then restored); pasted post-change bare suite summary with no new failing node id versus V-01.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` pasted, one added line, no em/en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open question (OQ-01) is resolved. Run `aw ipd begin 9ec94f` before the first edit. Scope fence: `- Scope-Paths:` declares every path this plan expects to change; an out-of-scope edit is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every `V-*` MUST carry the ACTUAL pasted runner output; never claim a pass that was not run. Commit only Scope-Paths via `aw commit 9ec94f -- <paths>`; never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns the terminal transition and the executor does NOT run `aw ipd finalize`; run by hand, finish with `aw ipd finalize 9ec94f` once `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status: executed` and never `git mv` the file.
