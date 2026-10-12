# IPD: Remove dead verdict pre-seeds and prove the verdict comes from the verifier turn in agy and stale-plan-path tests

- Date: 2026-10-12
- Kind: child
- Concern: Backlog 6r7zmw asks that verifier mocks in the agy runner tests and the stale-plan-path finalize tests write the verification outcome DURING the verifier turn. Commit 91d973f58 ("test: reconcile verifier mocks in agy and stale plan path tests (fixes 6r7zmw)", AW-Item t18l64) added in-turn writes, so the tests pass, but it left the old pre-seeded `NN-<id6>-verification.json` writes in place (before `execute_item` in `tests/test_agy_runipd_cli.py`, and inside the EXECUTOR mock in `tests/test_finalize_stale_plan_path.py`). `runner_shared.execute_item_core._run_verifier_turn` unlinks that file before spawning the verifier, so the pre-seeds are dead and obscure what each test proves. The agy fakes also branch on `k.get("fresh_session")`, a kwarg `agy_runipd._spawn_verifier` never passes (it passes `log_suffix="verify"`), so half of that condition is dead too. The backlog item was never closed because no plan carried it.
- Scope: Test-only. In `tests/test_agy_runipd_cli.py` (`AgySelfFinalizeTests.test_finalize_fires_on_verified_and_marks_executed`, `AgySelfFinalizeTests.test_finalize_refusal_leaves_not_executed_and_not_forced`) remove the pre-seeded verification write and the dead `fresh_session` branch, so the verdict exists only because the verifier-turn fake wrote it. In `tests/test_finalize_stale_plan_path.py` (`test_a1_lane_arm_refuses_when_finalize_re_resolution_fails`, `test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails`) remove the verification write from the executor mock and keep it only in `mock_verifier`. Add one negative control in `tests/test_agy_runipd_cli.py` showing that a verdict written only BEFORE the run (with a verifier fake that writes nothing) does not let the item reach `executed`, which proves the in-turn write is load-bearing on the agy host. No production code changes.
- Scope-Paths: tests/test_agy_runipd_cli.py, tests/test_finalize_stale_plan_path.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 6r7zmw
- Blocks-Release: next
- Set: 6r7zmw
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: dlggmo
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed; review record .aw/records/reviews/20261012-6r7zmw-01-dlggmo-remove-dead-verdict-pre-seeds-and-prove-the-verdict-comes-fr.review.md

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored the plan graduating backlog 6r7zmw. Repository evidence: commit 91d973f58 already adds in-turn verifier writes; `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_finalize_stale_plan_path.py` reports `67 passed`; the remaining work is removing the dead pre-seeds and adding a negative control.

## Goal

Make the agy and stale-plan-path verifier mocks write the verification outcome only during the verifier turn, matching the runner's real contract (`_run_verifier_turn` unlinks `NN-<id6>-verification.json` before it spawns the verifier). Then show that the in-turn write is what makes the tests pass, so a future regression that stops clearing the stale verdict, or a mock that quietly falls back to a pre-seed, is caught.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: agy runner tests

- [ ] E-01 In `tests/test_agy_runipd_cli.py`, in `AgySelfFinalizeTests.test_finalize_fires_on_verified_and_marks_executed` and `AgySelfFinalizeTests.test_finalize_refusal_leaves_not_executed_and_not_forced`, delete the `(run_dir / "outcomes" / "01-agy001-verification.json").write_text(...)` pre-seed that runs before `execute_item`. Then reduce each `fake_agy` condition from `k.get("fresh_session") or k.get("log_suffix") == "verify"` to `k.get("log_suffix") == "verify"`.
  - Depends on: none
  - Expected outcome: the only write of `01-agy001-verification.json` in each test is inside the verifier branch of `fake_agy`; both tests still pass with their existing assertions (`executed`, and `fail-gate` respectively).
  - Execution state: pending

- [ ] E-02 Add a test in `AgySelfFinalizeTests` (for example `test_preseeded_verdict_without_verifier_write_is_not_executed`) that writes a VERIFIED `01-agy001-verification.json` before the run (with the same `tests_run` evidence the positive tests use, `python3 -m unittest tests.test_from_backlog -v`, so the pre-seed would be ACCEPTED if it survived), uses a `run_agy_turn` fake whose verifier branch (`log_suffix == "verify"`) writes nothing, drives `agy_runipd.execute_item`, and asserts that `item["status"] == "fail-verify"`, that the item's refusal code (`render_stream.refusal_of_item(item).code`, or `item["refusal"]["code"]`) is `verification-never-recorded`, that `driver_finalize` was never called, and that the plan file is still at its pending path. Mirror the setup of `test_finalize_fires_on_verified_and_marks_executed`, including `state["options"]["no_verify"] = False` and the conforming executor outcome, and pin `state["options"]["retry_budget"] = 0` (REQUIRED, not conditional: measured at review, the default budget leaves the item `queued` with refusal `verification-sent-back`). The fake's verifier branch MUST return a session id DIFFERENT from the executor's (for example `"s_verify"` versus `"s"`, as the positive tests do): measured at review, returning the same `"s"` for both turns makes the item fail `verifier-session-collision`, so the test would pass for a reason unrelated to the stale verdict.
  - Depends on: E-01
  - Expected outcome: the new test passes with `fail-verify` / `verification-never-recorded`, and it FAILS (the item reaches `executed` and `driver_finalize` is called once) when the verdict unlink in `_run_verifier_turn` is disabled. Run that mutation probe as an in-process monkeypatch (wrap `pathlib.Path.unlink` so it is a no-op for names ending `-verification.json`) or a temporary edit reverted before commit; never commit it. Both outcomes were reproduced at review with a scratch driver of this exact setup.
  - Execution state: pending

### Task group 2: stale plan path finalize tests

- [ ] E-03 In `tests/test_finalize_stale_plan_path.py`, in `test_a1_lane_arm_refuses_when_finalize_re_resolution_fails` and `test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails`, delete the verification write (`outcomes/01-1fz001-verification.json` and `outcomes/01-1fz002-verification.json` respectively) from the EXECUTOR mock, and keep the write in `mock_verifier`.
  - Depends on: none
  - Expected outcome: each test writes its verification outcome only from `mock_verifier`, and both still pass with their existing refusal assertions unchanged.
  - Execution state: pending

### Task group 3: regression

- [ ] E-04 Before the first edit, RE-DERIVE the baseline with a bare `python3 -m pytest` and record its summary line and FAILED node ids (F5's `39 failed` is authoring-time context, not the bar: it was measured with explicit flags in another state of the tree). After E-01..E-03, run the two touched modules, then the bare full suite, and compare the failing node ids against that re-derived baseline.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: both touched modules pass in full, and the full suite reports no failure outside the pre-existing baseline set.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests assert outcomes (dispositions, whether finalize was called, plan file location) by driving `agy_runipd.execute_item` / `runner_shared.execute_item_core`, never by reading source (AGENTS.md, NO CODE-PINNING TESTS).
- The verifier spawn is identified on agy by `log_suffix="verify"` in `agy_runipd._spawn_verifier` (quoted: `log_suffix="verify",` with `telemetry_phase=runner_shared.TELEMETRY_PHASE_VALIDATE`).
- `runner_shared.execute_item_core._run_verifier_turn` clears the fixed verdict path before spawn (quoted: `v_outcome_file.unlink(missing_ok=True)`), introduced by t18l64 (PR-007 of its review).
- The cross-host stale-verdict case is already covered by `tests/test_verification_sendback.py` `test_stale_verdict_clearing` (asserts `verification-never-recorded` with `retry_budget=0`). E-02 is the agy-runner-module counterpart at the `AgySelfFinalizeTests` level and duplicates no assertion of that test's refusal code.
- Run the suite bare: `python3 -m pytest` (AGENTS.md repo-local development contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The backlog item's core fix already landed. | Commit 91d973f58 adds in-turn verifier writes to both test modules; `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_finalize_stale_plan_path.py` gives `67 passed in 12.43s`. |
| F2 | Pre-seeded verdict writes remain and are dead. | `tests/test_agy_runipd_cli.py` writes `01-agy001-verification.json` before `execute_item` in both `AgySelfFinalizeTests` finalize tests; `tests/test_finalize_stale_plan_path.py` writes it inside the executor mock. `_run_verifier_turn` unlinks the file before spawn. |
| F3 | `fresh_session` is never passed to `run_agy_turn` by the verifier spawn. | `agy_runipd._spawn_verifier` passes `session_id=None, use_continue=False, log_suffix="verify"`; no `fresh_session` kwarg. |
| F4 | The backlog item stayed `open` because no plan carried `From-Backlog: 6r7zmw`. | The t18l64 history auto-reconciles the backlog file as out of scope; no plan under `.aw/records/plans/` names 6r7zmw as `From-Backlog`. |
| F6 | E-02's negative control, measured at review with a scratch driver of the planned setup. | Pre-seeded VERIFIED verdict, verifier fake writes nothing: default budget -> `queued`, refusal `verification-sent-back`; `retry_budget: 0` -> `fail-verify`, `verification-never-recorded`, finalize not called. Same with the `-verification.json` unlink disabled -> `executed`, finalize called once. Verifier returning the executor's session id `"s"` -> `fail-verify`, `verifier-session-collision` (wrong reason). A pre-seed with `tests_run: ["x"]` under the disabled unlink -> `verifier-no-test-evidence`, so the pre-seed needs the positive tests' real `tests_run` value for the mutation probe to flip to `executed`. |
| F5 | Pre-change full-suite baseline: `39 failed, 7180 passed, 2 skipped`. All 39 failures are in modules unrelated to this plan (non-project / explicit-dir refusal surfaces, `test_commit_run_trailers_env.py`, one `test_finalize_sendback.py` e2e case), and neither touched module is among them. | `python3 -m pytest -o addopts="" -q -m "not slow and not livecorpus" -n auto tests/` run in this lane on 2026-10-12. |

## Proposed changes (ordered, validatable)

1. E-01: strip the pre-seed and dead branch from the two agy finalize tests.
2. E-02: add the agy negative control proving the in-turn write is load-bearing.
3. E-03: strip the executor-mock verdict write from the two stale-plan-path tests.
4. E-04: regression run against a baseline re-derived at execution start.

## Deferred / out of scope (with reason)

- The 39 pre-existing full-suite failures (F5) are unrelated to verifier mocks and belong to other work; this plan only proves it adds none.
- Other test modules that write `*-verification.json` (for example `tests/test_oc_runipd.py`, `tests/test_defect_report.py`) are not named by backlog 6r7zmw, which is scoped to "agy and stale plan path tests"; auditing them would broaden scope.

## Scope check

- Over-scope: none; two test modules, no production code.
- Under-scope: none; the backlog summary names exactly the agy tests and the stale-plan-path tests, and both are covered (E-01/E-02 and E-03).

## Required tests / validation

- `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_finalize_stale_plan_path.py` passes in full, including the new E-02 test.
- One temporary mutation probe: removing `v_outcome_file.unlink(missing_ok=True)` makes the E-02 test fail; revert it and confirm with `git diff -- agent_workflows/` that nothing is left.
- Bare `python3 -m pytest` shows no failure outside the baseline re-derived at execution start (E-04).

## Spec / documentation sync

N/A: test-only change. The runner contract the tests now mirror (clear the verdict, then spawn the verifier) is already specified by t18l64 and spec 25kzda 5.5. No spec text changes.

## Open questions

### OQ-01: Is any further work needed beyond commit 91d973f58?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes, a small amount. 91d973f58 made the tests pass but left dead pre-seeds (F2, F3) and no in-module proof that the in-turn write matters. Removing the pre-seeds and adding a negative control closes the item honestly; resolved from repository evidence (F1 to F3).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- tests/test_agy_runipd_cli.py` showing the two pre-seed writes and the `fresh_session` conditions removed, plus `grep -n "verification.json\|fresh_session" tests/test_agy_runipd_cli.py` output showing no `01-agy001-verification.json` write outside a `log_suffix == "verify"` branch in `AgySelfFinalizeTests`; paste the actual pytest output for the two named tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual pytest output showing the new test passing, and the test's assertions on `fail-verify`, the `verification-never-recorded` refusal code, zero `driver_finalize` calls and the unmoved plan; then paste the pytest output showing it FAILING (the assertion message must show the item reached `executed` or finalize was called, NOT a collision or setup error) with the verdict unlink in `runner_shared.execute_item_core._run_verifier_turn` (the code path producing the observation) disabled, and `git diff --stat -- agent_workflows/` showing empty after the revert.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- tests/test_finalize_stale_plan_path.py` showing the executor-mock verification writes removed and the `mock_verifier` writes retained, and the actual pytest output for `test_a1_lane_arm_refuses_when_finalize_re_resolution_fails` and `test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the actual runner summary line for `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_finalize_stale_plan_path.py` (0 failed) and for the bare `python3 -m pytest`, with the list of FAILED node ids shown to be a subset of the baseline re-derived at the start of execution (paste both lists).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Resolved questions: OQ-01 is resolved; nothing awaits the maintainer.
- Scope declaration (not a stop directive): `- Scope-Paths:` lists the two test modules. If another edit proves necessary, make it and justify it at finalize with `--scope-reason <path>=<why>`; acknowledge a declared but unmodified path with `--scope-ack`. No production file may be changed; the E-02 mutation probe is never committed.
- Honesty: paste the ACTUAL runner output into every `V-*`; never record a pass you did not observe.
- Commits: `aw commit dlggmo -- tests/test_agy_runipd_cli.py tests/test_finalize_stale_plan_path.py`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` as an isolated worker, do not run `aw ipd begin`/`finalize` in the lane; the driver finalizes. By hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize dlggmo`; never `git mv` the plan by hand.
- Release gate: inherits `- Blocks-Release: next` from backlog `6r7zmw`, which closes through the handoff once this plan is executed.
