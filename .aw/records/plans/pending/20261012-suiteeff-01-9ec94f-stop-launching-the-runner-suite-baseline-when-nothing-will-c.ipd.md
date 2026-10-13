# IPD: Stop launching the runner suite baseline when nothing will collect it

- Date: 2026-10-12
- Kind: child
- Concern: `runner_shared.execute_item_core` starts a full-suite pre-work baseline (`start_suite_baseline`, condition: not review, not production, self-finalize, extractor and `SUITE_CHECK_ARGV` present) BEFORE the turn, but collects it only inside `if integration_gate_relevant and not validate:` after the turn, and then abandons it in the turn's `finally`. `validate` is computed after the turn (`validate = opts.get("validate", False)`, defaulting to `not (no_verify or no_audit)` when the key is absent), and is True in the default configuration. Measured over October: 322 `suite-baseline-started`, 0 `suite-baseline-collected`; of 320 baseline-bearing attempts, 318 had validation ON. Each was a full 12-worker suite thrown away.
- Scope: IN: compute the attempt's `validate` value once, BEFORE the baseline start, from the same expression, and start the baseline only when `not validate` (the only mode that collects it); a test proving both directions; one CHANGELOG line. OUT: changing what `validate` means or its default; the baseline's consumers (`revalidation_baseline_for`, `suite_baseline_context`), which only read a collected baseline; caching (Order 02).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_suite_baseline_mode_gate.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
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
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (record `.aw/records/reviews/20261012-suiteeff-01-9ec94f-stop-launching-the-runner-suite-baseline-when-nothing-will-c.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 01 of Set `suiteeff` from backlog `58x9mw`.

## Goal

A suite baseline is launched only when the attempt will read it, removing about one full suite per default-mode execute turn.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the gate

- [x] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` before the first edit; record its summary line and failing node ids.
  - Depends on: none
  - Expected outcome: a recorded summary line and failing-node-id list.
  - Execution state: performed

- [x] E-02 In `runner_shared.py`, add a pure helper `attempt_validates(options: Mapping) -> bool` returning exactly today's expression (`options["validate"]` when the key is present, else `not (options.get("no_verify") or options.get("no_audit"))`), use it at the existing post-turn assignment in `execute_item_core` (so behavior there is unchanged), and add `and not attempt_validates(state.get("options", {}))` to the condition that calls `start_suite_baseline`. Comment WHY with the measured 322/0 count, and name the reason nothing else needs the baseline in ON mode: the only other reader of the pre-turn `suite_baseline` value is the `gate_answer_is_warranted` follow-up, which asks only on the suite-failure signal, and that signal cannot arise when `run_suite_check` did not run. When skipped BECAUSE OF VALIDATION ONLY (every other existing condition held: not review, not production, self-finalize, extractor and `SUITE_CHECK_ARGV` present), append one `suite-baseline-skipped` event; a review or production turn emits nothing new. The event carries `id6`, `attempt` and `reason: "validation is ON; the verifier's verdict is this attempt's trust signal and nothing collects a baseline"`, so the absence is explained, not silent.
  - Depends on: E-01
  - Expected outcome: a validation-ON attempt emits `suite-baseline-skipped`, emits no `suite-baseline-started`, and records no `attempt["suite_baseline_started"]`; a validation-OFF attempt starts and later collects the baseline exactly as today.
  - Execution state: performed

### Task group 2: tests and changelog

- [x] E-03 Add `tests/test_suite_baseline_mode_gate.py` (behavioral, P16): (a) `attempt_validates` over the five option shapes (`validate` True present; `validate` False present; absent with `no_verify` True; absent with `no_audit` True; absent with neither) matches the expected booleans; (b) drive `execute_item_core` through `oc_runipd.execute_item` with validation ON (options as `tests/test_attempt_lane_facts.py`'s `_oc_state_and_item` builds them: `no_audit: False`, `validate` absent): assert no `suite-baseline-started` event, exactly one `suite-baseline-skipped` event, and no `attempt["suite_baseline_started"]` key; (c) the same with `validate: False`: assert `suite-baseline-started` then `suite-baseline-collected` with `state: "completed"`. HARNESS (the `tests/test_suite_baseline.py` this item originally named was deleted by `19313eed7`): reuse `tests.test_oc_runipd._init_repo_with_conforming_plan` and `tests.test_attempt_lane_facts.AttemptLaneFactsTests`' state builder and fake agent (`mock.patch.object(oc_runipd, "run_opencode", ...)`), and for cell (c) ALSO patch `oc_runipd.SUITE_CHECK_ARGV` to a fast command that prints a summary line (for example `(sys.executable, "-c", "print('1 passed')")`) and `oc_runipd.run_suite_check` to return a passing `runner_shared.SuiteCheckResult`, so the cell never runs a real pytest inside the fixture. Do NOT assert on the baseline checkout directory as the distinguishing signal: the existing `finally` removes it in both modes, so its absence cannot fail with E-02 reverted.
  - Depends on: E-02
  - Expected outcome: the file passes; cell (b) fails with E-02's condition reverted. (Measured at review with this harness on the unchanged code: default options produce `['suite-baseline-started']` and no collection; `validate: False` with the two patches produces `suite-baseline-started` then `suite-baseline-collected` state `completed`.)
  - Execution state: performed

- [x] E-04 Add one `- Fixed:` bullet as the first `- Fixed:`/`- Changed:` bullet under `CHANGELOG.md`'s `## 2.0.0 (pending)` heading (the heading carries a trailing title; match on its prefix): runs with verification on no longer start a background test-suite baseline they never read. No em or en dashes.
  - Depends on: E-02
  - Expected outcome: one new CHANGELOG line.
  - Execution state: performed

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
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

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

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-change `python3 -m pytest` summary line and failing node ids.
  - Observed evidence:
    ```
    8237 passed, 4 skipped, 18 xfailed, 3 warnings in 1341.36s (0:22:21)
    Failing node ids: none
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the `git diff` of `execute_item_core`'s baseline condition and `attempt_validates`, plus the pasted events.jsonl lines from E-03 cells (b) and (c) (code path: `execute_item_core` -> `attempt_validates` -> `start_suite_baseline` or `suite-baseline-skipped`).
  - Observed evidence:
    `git diff` of `execute_item_core`'s baseline condition and `attempt_validates`:
    ```diff
    @@ -26457,6 +26457,19 @@ class SuiteBaselineRun:
                 self.process.kill()


    +def attempt_validates(options: Mapping) -> bool:
    +    """Return whether an attempt runs independent verification.
    +
    +    When the "validate" key is present, its value controls; otherwise, verification
    +    is enabled unless "no_verify" or "no_audit" is requested.
    +    """
    +    if not isinstance(options, Mapping):
    +        return False
    +    if "validate" in options:
    +        return bool(options["validate"])
    +    return not (options.get("no_verify") or options.get("no_audit"))
    +
    +
     def start_suite_baseline(
         repo: Path,
         *,
    @@ -36981,13 +36994,22 @@ def execute_item_core(
         suite_baseline_run: SuiteBaselineRun | None = None
         suite_baseline: SuiteBaseline | None = None
         baseline_extractor = getattr(driver_module, "extract_suite_failures", None)
    -    if (
    +    baseline_eligible = (
             not is_review
             and not is_production
             and self_finalize
             and callable(baseline_extractor)
             and getattr(driver_module, "SUITE_CHECK_ARGV", None)
    -    ):
    +    )
    +    if baseline_eligible and not attempt_validates(state.get("options", {})):
             suite_baseline_run, suite_baseline = start_suite_baseline(
                 repo,
                 id6=item["id6"],
    @@ -37026,6 +37048,20 @@ def execute_item_core(
                         ),
                     },
                 )
    +    elif baseline_eligible:
    +        append_jsonl(
    +            run_dir / "events.jsonl",
    +            {
    +                "at": utc_now(),
    +                "event": "suite-baseline-skipped",
    +                "id6": item["id6"],
    +                "attempt": attempt_no,
    +                "reason": (
    +                    "validation is ON; the verifier's verdict is this attempt's "
    +                    "trust signal and nothing collects a baseline"
    +                ),
    +            },
    +        )
    ```
    Pasted `events.jsonl` lines from cell (b) and cell (c):
    Cell (b):
    ```json
    {"at": "2026-10-13T21:23:55+00:00", "attempt": 1, "event": "suite-baseline-skipped", "id6": "wir001", "reason": "validation is ON; the verifier's verdict is this attempt's trust signal and nothing collects a baseline"}
    ```
    Cell (c):
    ```json
    {"at": "2026-10-13T21:23:57+00:00", "attempt": 1, "base_commit": "68564aff93efd26a110a7c1ecb1c435c1c773570", "checkout": "/tmp/tmp7pgz8uxu/repo/.aw/state/suite-baselines/wir001-attempt1", "event": "suite-baseline-started", "id6": "wir001"}
    {"at": "2026-10-13T21:23:58+00:00", "attempt": 1, "base_commit": "68564aff93efd26a110a7c1ecb1c435c1c773570", "event": "suite-baseline-collected", "failing_count": 0, "id6": "wir001", "reason": "", "state": "completed"}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted passing run of `python3 -m pytest tests/test_suite_baseline_mode_gate.py tests/test_suite_baseline_direction.py tests/test_attempt_lane_facts.py`; pasted failing cell (b) with E-02's condition reverted (then restored); pasted post-change bare suite summary with no new failing node id versus V-01.
  - Observed evidence:
    Passing run:
    ```
    $ python3 -m pytest tests/test_suite_baseline_mode_gate.py tests/test_suite_baseline_direction.py tests/test_attempt_lane_facts.py
    ............                                                             [100%]
    12 passed in 5.03s
    ```
    Failing cell (b) with E-02's condition reverted:
    ```
    $ python3 -m pytest tests/test_suite_baseline_mode_gate.py
    .F.                                                                      [100%]
    =================================== FAILURES ===================================
    ______ SuiteBaselineModeGateTests.test_validation_on_skips_suite_baseline ______
    >           self.assertNotIn("suite-baseline-started", event_names)
    E           AssertionError: 'suite-baseline-started' unexpectedly found in ['ipd-started', 'tool-identity-verified', 'worktree-allocated', 'receipt-lane-recorded', 'lane-inputs-materialized', 'suite-baseline-started', 'lane-submissions-collected', 'defect-report-recorded', 'ipd-finalized', 'ipd-finished']
    1 failed, 2 passed in 4.60s
    ```
    Post-change bare suite summary:
    ```
    8240 passed, 4 skipped, 18 xfailed, 3 warnings in 460.79s (0:07:40)
    Failing node ids: none
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` pasted, one added line, no em/en dash.
  - Observed evidence:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index d4e3c6032..94e7967f0 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: runs with verification on no longer start a background test-suite baseline they never read.
     - Fixed: a mismatch between the runner's own agent_workflows package and the one a nested aw call would load now fails only the affected item (with a tool-identity-mismatch refusal) instead of stopping the whole aw oc run or aw agy run; other independent items keep running.
     - Fixed: aw runs and aw run human output now masks tokens (such as ghp_ tokens and Bearer credentials) the same way --agent and --json already did.
     - Fixed: closing a release-blocking backlog item with --evidence now refuses a cited plan that has not been executed, on both setter spellings.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open question (OQ-01) is resolved. Run `aw ipd begin 9ec94f` before the first edit. Scope fence: `- Scope-Paths:` declares every path this plan expects to change; an out-of-scope edit is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every `V-*` MUST carry the ACTUAL pasted runner output; never claim a pass that was not run. Commit only Scope-Paths via `aw commit 9ec94f -- <paths>`; never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns the terminal transition and the executor does NOT run `aw ipd finalize`; run by hand, finish with `aw ipd finalize 9ec94f` once `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status: executed` and never `git mv` the file.
