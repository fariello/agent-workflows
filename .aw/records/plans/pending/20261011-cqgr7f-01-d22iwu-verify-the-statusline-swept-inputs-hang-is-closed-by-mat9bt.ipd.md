# IPD: Verify the statusline swept-inputs hang is closed by mat9bt and 6ye76g and record cqgr7f as its duplicate

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `cqgr7f` reports `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` exceeding the 90s per-test hang guard under `-n auto` xdist CPU contention. Two executed plans (`mat9bt`, `6ye76g`) already addressed this exact nodeid via sibling backlog items `8sr0or` and `mu4k1g`, and both explicitly declined to close `cqgr7f` as a duplicate, leaving a live release-gating bug record with no remaining defect behind it.
- Scope: Verification-only. Re-measure the named test in isolation and in the full default suite, confirm the two existing fixes are present and behaving, and record the evidence in this plan so `cqgr7f` can be closed as satisfied by this plan's execution. No production or test code change.
- Scope-Paths: .aw/records/plans/**
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: cqgr7f
- Blocks-Release: next
- Set: cqgr7f
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: d22iwu
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004 (all fixed; E-01..E-04 re-measured at review: pairwise + slow markers present, hang guard `9 passed`, isolated call `0.04s`, full suite `39 failed, 7180 passed` with the named nodeid absent from FAILED and the slowest-50; F-04 cause corrected).
- 2026-10-12 draft (opencode): created.
- 2026-10-11 to-review (opencode): authored from backlog cqgr7f as a verification-only plan; root cause already fixed by executed plans mat9bt and 6ye76g.

## Goal

Prove, with pasted runner output, that the swept-inputs statusline test no longer approaches any hang budget under the default parallel suite, so the duplicate release-blocking record `cqgr7f` can close against concrete evidence instead of lingering as a phantom `Blocks-Release: next` blocker.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the fixes are present

- [x] E-01 Confirm the `mat9bt` pairwise fix is present: in `tests/test_statusline_behavior.py`, `TestStatuslineBoxInvariants.test_box_renderer_invariants_across_swept_inputs` iterates `generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)` rows, and the 7,776-row cartesian sweep lives only in `test_box_renderer_invariants_exhaustive_sweep` marked `@pytest.mark.slow`.
  - Depends on: none
  - Expected outcome: Both facts confirmed by `grep -n "generate_pairwise_covering_array\|pytest.mark.slow\|def test_box_renderer" tests/test_statusline_behavior.py` output.
  - Execution state: performed

- [x] E-02 Confirm the `6ye76g` CPU-time hang guard is present in root `conftest.py` (`_DEFAULT_TEST_CPU_TIMEOUT`, `_DEFAULT_TEST_WALL_TIMEOUT = 240.0`, `ITIMER_PROF`) and that its behavioral tests pass: `python3 -m pytest tests/test_hang_guard_budget.py`.
  - Depends on: none
  - Expected outcome: grep shows the constants; the pytest run reports all tests passed.
  - Execution state: performed

### Task group 2: Re-measure the named test

- [x] E-03 Run the named test in isolation with durations: `python3 -m pytest -o addopts="" -q --durations=5 tests/test_statusline_behavior.py -k swept_inputs`.
  - Depends on: E-01
  - Expected outcome: 1 passed; call duration well under 1s (authoring measurement: 0.03s).
  - Execution state: performed

- [x] E-04 Run the full default suite BARE with durations (`python3 -m pytest --durations=50`), the configuration the backlog item reported failing under, and record whether the named nodeid appears in any failure or in the slowest-50 list.
  - Depends on: E-03
  - Expected outcome: The named nodeid is absent from the FAILED list and from the slowest-50 list (or present with a duration far below the CPU and wall budgets). Unrelated failures, if any, are recorded by file name and count and not acted on here. The FAILED set's size is a live artifact (38 at authoring, 39 at review), so it is NOT a bar: re-derive it at execution, and the only bar is the named nodeid's absence plus its duration.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite command is bare `python3 -m pytest`; `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` (AGENTS.md repo-local development contract). Narrowed runs clear defaults with `-o addopts=""`.
- Duplicate backlog records are closed by a maintainer-sanctioned act, not silently by an unrelated plan: both `mat9bt` ("Carrier-Declined ... RECOMMENDED ACTION FOR THE REVIEWER: once this plan executes, close `cqgr7f` ... as duplicates") and `6ye76g` ("close `cqgr7f` as a duplicate of `mu4k1g` with this plan as the evidence") deferred the closure. This plan is the explicit carrier for that closure, graduating `cqgr7f` itself.
- Tests must assert outcomes, not code structure (GUIDING_PRINCIPLES P16). This plan adds no test; the greps in E-01/E-02 are executor evidence-gathering, not test assertions.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The swept-inputs test no longer runs the 7,776-combination cartesian product in the default suite; it iterates a pairwise covering array, and the exhaustive sweep is `@pytest.mark.slow` with `@pytest.mark.timeout(300)`. | `.aw/records/plans/executed/20261002-8sr0or-01-mat9bt-cut-the-statusline-swept-input-sweep-to-a-pairwise-covering.ipd.md` (`- Status: executed`); `tests/test_statusline_behavior.py` `TestStatuslineBoxInvariants.test_box_renderer_invariants_exhaustive_sweep` carries both markers. |
| F-02 | The per-test hang guard now charges CPU time (`ITIMER_PROF`) with a retained 240s wall ceiling, so xdist contention no longer bills a correct test for waiting on CPU. | `.aw/records/plans/executed/20261002-hangcpu-01-6ye76g-make-the-per-test-hang-guard-measure-cpu-time-so-machine-loa.ipd.md` (`- Status: executed`); `conftest.py` "_DEFAULT_TEST_WALL_TIMEOUT = 240.0". |
| F-03 | Authoring-time measurement: isolated run `1 passed ... in 0.98s`, call `0.03s`; full default suite `38 failed, 7181 passed, 2 skipped ... in 201.72s`, with the named nodeid NOT among the failures, and `0.06s` when run alongside `tests/test_hang_guard_budget.py` (`55 passed in 7.92s`). | Runner output captured in this lane on 2026-10-11. |
| F-04 | The full-suite failures are unrelated to the statusline and the hang guard. CORRECTED AT REVIEW (2026-10-12): the cause is not the nested lane worktree. A re-run in the review lane reported `39 failed, 7180 passed, 2 skipped, 3 warnings in 203.09s`. Most of the failures (`tests/test_no_project_exit_is_cannot_run.py`, `tests/test_explicit_dir_non_project.py`, `tests/test_validator_nonsurveyable_dir.py`, `tests/test_nonsurveyable_root_refusal.py`, `tests/test_read_class_callers_refuse.py`, ...) are no-project tests whose `tmp_path` fixtures (`/tmp/pytest-of-<user>/...`) climb via `project_context.find_project_root` to a stray host directory `/tmp/.aw/records`, which makes `/tmp` look like an AW project (e.g. `Human surface for ('att',) expected exit 2, got 0`). `tests/test_commit_run_trailers_env.py` fails because the lane exports `AW_RUN_ID`/`AW_ITEM_ID6`/`AW_EXECUTION_ROLE`. Both are host or lane environment, not product defects that this plan carries. | Review-lane FAILED list; `ls -d /tmp/.aw/records`; failure text quoted. None touch `render_stream` or `conftest.py` hang-guard behavior. |
| F-05 | `cqgr7f` is the last open record of three describing one defect (`8sr0or` -> `mat9bt`, `mu4k1g` -> `6ye76g`), and it carries `Work-Kind: bug` + `Blocks-Release: next`, so it falsely gates the next release. | `.aw/records/backlog/graduated/20261001-cqgr7f-01-cqgr7f-statusline-swept-inputs-test-exceeds-90s-hang-time.backlog.md` (moved from `open/` when this plan graduated it; `8sr0or` and `mu4k1g` are `done`); F-11 of `mat9bt`, F-10 of `6ye76g`. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: confirm both fixes exist and the hang-guard tests pass.
2. E-03, E-04: re-measure the named test isolated and under the full parallel suite; paste output.
3. On execution, this plan becomes the `From-Backlog` same-gate carrier for `cqgr7f`; once `executed`, the HANDOFF close path (`aw backlog set done cqgr7f`) is satisfied without further code change.

## Deferred / out of scope (with reason)

- The 38 unrelated full-suite failures (F-04): not this item's defect; if they reproduce on the main checkout they deserve their own backlog item, filed by whoever confirms them there.
  - Carrier-Declined: Not carried because they were observed only inside a nested lane worktree and are not yet confirmed on the main checkout; filing an unconfirmed environment artifact as a bug would add a phantom release blocker, the very defect this plan removes.
- Any change to `conftest.py` budgets or to `tests/test_statusline_behavior.py`: the defect is already fixed (F-01, F-02); changing either would broaden scope with no failing evidence.
  - Carrier-Declined: Nothing to carry: there is no remaining defect to fix (F-01, F-02, F-03).
- Setting `cqgr7f` to `done` as an E-item: the runner (`runner_shared.evaluate_backlog_close`) or a human/agent via `aw backlog set done cqgr7f` closes it after this plan executes (see the gate); this plan supplies the executed carrier. `cqgr7f` is already `graduated` (to `d22iwu`), not `open`.
  - Carrier-Declined: This plan itself is the From-Backlog carrier for `cqgr7f`; no further record is needed.

## Scope check

- Over-scope: none. No code is modified; only this plan file records evidence.
- Under-scope: none. If E-03 or E-04 shows the named test failing or near a budget, the executor marks the item `failed` with the output and the plan does not finalize, which correctly keeps `cqgr7f` live.

## Required tests / validation

- `python3 -m pytest tests/test_hang_guard_budget.py` passes (E-02, V-02).
- `python3 -m pytest -o addopts="" -q --durations=5 tests/test_statusline_behavior.py -k swept_inputs` passes with sub-second call time (E-03, V-03).
- Bare `python3 -m pytest --durations=50` shows the named nodeid neither failed nor near a budget (E-04, V-04).

## Spec / documentation sync

N/A: no behavior changes; no spec describes this test's runtime.

## Open questions

### OQ-01: Should cqgr7f be fixed with new code or closed as a duplicate?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Closed as a duplicate via this verification plan. Repository evidence (F-01, F-02, F-03) shows the defect is fixed and the test runs in 0.03s; both prior plans explicitly recommended closing `cqgr7f` against their execution. New code would have no failing case to target.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted grep output from `tests/test_statusline_behavior.py` showing `generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)` used in `test_box_renderer_invariants_across_swept_inputs` and `@pytest.mark.slow` on `test_box_renderer_invariants_exhaustive_sweep`.
  - Observed evidence:
    ```
    $ grep -n "generate_pairwise_covering_array\|pytest.mark.slow\|def test_box_renderer" tests/test_statusline_behavior.py
    21:def generate_pairwise_covering_array(domains: list[list[Any]]) -> list[list[Any]]:
    318:        rows1 = generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)
    319:        rows2 = generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)
    345:    def test_box_renderer_invariants_across_swept_inputs(self) -> None:
    360:        rows = generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)
    377:    @pytest.mark.slow
    379:    def test_box_renderer_invariants_exhaustive_sweep(self) -> None:
    ```
    Line 360 confirms `rows = generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)` inside `test_box_renderer_invariants_across_swept_inputs`, and line 377 confirms `@pytest.mark.slow` decorating `test_box_renderer_invariants_exhaustive_sweep`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted grep of `conftest.py` showing `ITIMER_PROF` and `_DEFAULT_TEST_WALL_TIMEOUT`, plus the pasted `N passed` summary line of `python3 -m pytest tests/test_hang_guard_budget.py` with zero failures.
  - Observed evidence:
    1. Grep of `conftest.py`:
    ```
    $ grep -n "_DEFAULT_TEST_CPU_TIMEOUT\|_DEFAULT_TEST_WALL_TIMEOUT\|ITIMER_PROF" conftest.py
    214:# 1. CPU BUDGET (ITIMER_PROF, counting user + sys CPU): measures actual work done by the test.
    215:#    ITIMER_PROF is used rather than ITIMER_VIRTUAL because ITIMER_VIRTUAL measures only user time
    218:#    (29.16s re-measured at execution head). _DEFAULT_TEST_CPU_TIMEOUT = 60.0s provides >2x headroom
    222:#    _DEFAULT_TEST_WALL_TIMEOUT = 240.0s is well above worst unmarked in-suite wall time (66.53s
    251:_DEFAULT_TEST_CPU_TIMEOUT = 60.0
    252:_DEFAULT_TEST_WALL_TIMEOUT = 240.0
    253:_DEFAULT_TEST_TIMEOUT = _DEFAULT_TEST_CPU_TIMEOUT  # backward-compatibility alias
    275:            default_cpu = _DEFAULT_TEST_CPU_TIMEOUT
    277:        default_cpu = _DEFAULT_TEST_CPU_TIMEOUT
    284:            default_wall = _DEFAULT_TEST_WALL_TIMEOUT
    286:        default_wall = _DEFAULT_TEST_WALL_TIMEOUT
    419:        # Arm CPU budget on ITIMER_PROF / SIGPROF (user + sys CPU)
    423:            and hasattr(_signal, "ITIMER_PROF")
    426:            _signal.setitimer(_signal.ITIMER_PROF, cpu_budget, 1.0)
    433:                _signal.setitimer(_signal.ITIMER_PROF, 0)
    ```
    2. Runner output for `python3 -m pytest tests/test_hang_guard_budget.py`:
    ```
    bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
    .........                                                                [100%]
    9 passed in 15.60s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing `1 passed` and the `--durations` line for the named nodeid with a call time under 1s.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -q --durations=5 tests/test_statusline_behavior.py -k swept_inputs
    .                                                                        [100%]
    NOTE: 46 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ============================= slowest 5 durations ==============================
    0.24s call     tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs

    (2 durations < 0.005s hidden.  Use -vv to show these durations.)
    1 passed, 46 deselected in 2.46s
    ```
    Call duration is 0.24s, well below the 1s ceiling and well under the hang guard budget.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted final summary line of the bare full-suite run, plus pasted output of `grep -n "swept_inputs"` over the saved full output (FAILED lines AND the slowest-50 block), showing it absent from FAILED and either absent from the slowest-50 or listed at a duration below 10s. Also paste the per-file count of the FAILED list (`grep "^FAILED" | cut -d: -f1 | sort | uniq -c`) so a reader can see that no failing file is `tests/test_statusline_behavior.py`, `tests/test_hang_guard_budget.py` or `conftest.py`-level.
  - Observed evidence:
    1. Bare full-suite summary line:
    ```
    7705 passed, 4 skipped, 3 warnings in 714.29s (0:11:54)
    ```

    2. Grep for `swept_inputs` in the full suite output (FAILED and slowest-50):
    ```
    $ grep -n "swept_inputs" .aw/state/lane-submissions/run-20261013T014119Z-1382357/08-d22iwu/attempt-1/pytest_full.log
    (exit code 1; absent from both FAILED and slowest-50)
    ```
    The test passed cleanly and was absent from the slowest-50 durations list (the 50th slowest duration was 9.30s; `swept_inputs` finished well under 9.30s).

    3. Per-file count of FAILED lines:
    ```
    $ grep "^FAILED" .aw/state/lane-submissions/run-20261013T014119Z-1382357/08-d22iwu/attempt-1/pytest_full.log | cut -d: -f1 | sort | uniq -c
    (empty; 0 failures across the entire suite)
    ```
    Zero failures across all test files.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval. The executor modifies no code and records observed evidence in this plan only. It commits through `aw commit d22iwu -- <plan path>` (never `git add -A`, `-a` or `--no-verify`), verifies the staged set with `git diff --cached --name-only` first, and never pushes, tags or releases. Paste the ACTUAL runner output for every test claim; never claim a pass you did not run. `- Scope-Paths:` is a declaration: if an out-of-scope edit proves necessary, make it and justify it with `--scope-reason`. If any V-item fails (the named test fails or approaches a budget), the plan must NOT reach `executed`; record the failure and leave `cqgr7f` live. On success, `aw ipd lint --phase pre-transition` must conform before the terminal transition. In a runner lane the runner owns finalize; outside one, the executor runs `aw ipd finalize d22iwu` (never a hand `git mv`). Afterwards `cqgr7f` closes via the HANDOFF path (this plan carries the same `- From-Backlog: cqgr7f` and `- Blocks-Release: next`, checked by `check_engine.evaluate_blocking_close`); in a runner lane that close is the runner's (`runner_shared.evaluate_backlog_close`), otherwise run `aw backlog set done cqgr7f`.
