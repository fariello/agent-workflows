# IPD: Restore the deleted benchmark runners and reports tests and prove they guard compute_aggregate_metrics

- Date: 2026-10-16
- Kind: child
- Concern: Rollup backlog `9qvfie` outcome 1 is property `PROP-02` (`agent_workflows/benchmark_metrics.py::compute_aggregate_metrics`, 195 exclusive lines) with final verdict `unprovable`: the survivor probe used the full default selection and "could not produce junit XML", while the control (the deleted `tests/test_benchmark_runners_reports.py` re-added) was killed by 4 tests (findings `hpjj44` `## Mutation results`, row `PROP-02`). The only test that reached it was deleted by commit `19313eed`, so today no surviving test guards the benchmark metrics aggregation.
- Scope: Restore `tests/test_benchmark_runners_reports.py` byte-for-byte from `19313eed^` (it passes unchanged at authoring HEAD: `14 passed in 0.20s`), commit it, then re-run the audit's own instrument `tools/mutation_probe.py` with a NARROWED selection so the `unprovable` verdict is replaced by a measured `guarded` / `unguarded` verdict. No production code changes.
- Scope-Paths: tests/test_benchmark_runners_reports.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 24h56i

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 24h56i verified (set trimcarry, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Give `compute_aggregate_metrics` (and the benchmark runner, ablation, threshold and report surface the same file exercises) a surviving behavioral guard again, and settle `PROP-02` with a real mutation verdict instead of `unprovable`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Restore the deleted module

- [x] E-01 Restore the file with `git show 19313eed^:tests/test_benchmark_runners_reports.py > tests/test_benchmark_runners_reports.py` (no edits). Confirm `tests/test_benchmark_runners_reports.py` did not already exist (`git ls-files tests/test_benchmark_runners_reports.py` prints nothing before the restore); if it does, STOP and report, since another change recreated it. Confirm it reads no production source (`grep -nE 'inspect\.|import ast|getsource' tests/test_benchmark_runners_reports.py` prints nothing) and run it explicitly: `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_benchmark_runners_reports.py`. If any test fails at execution HEAD, classify the failure the way findings `hpjj44` `## Replay failures` does (cite the commit that changed the asserted behavior via `git log -S`/`-G` on the asserted symbol), and update ONLY the assertion that encodes the superseded behavior, never weakening an assertion whose behavior is unchanged.
  - Depends on: none
  - Expected outcome: every collected test passes with zero failures and zero errors (14 at authoring and at review; the count is context, not the bar), or each failure is classified with a cited commit and minimally updated; the module carries no source-reading assertion.
  - Execution state: performed

- [x] E-02 Run the fast suite bare (`python3 -m pytest`) and commit only the restored module: `aw commit <this plan> -- tests/test_benchmark_runners_reports.py`.
  - Depends on: E-01
  - Expected outcome: fast suite green; one path-scoped commit containing only the module.
  - Execution state: performed

### Task group 2: Settle PROP-02 with a measured verdict

- [x] E-03 With the module committed (the probe mutates COMMITTED HEAD in a disposable worktree, `tools/mutation_probe.py` `probe`), run the selection preflight `python3 -m pytest -o addopts= -q --collect-only tests/test_benchmark_runners_reports.py` (exit 0, 14 collected), then the survivor probe (NO `--extra-test`: the selection must be the committed module) `mkdir -p .aw/state/trimcarry-24h56i && python3 tools/mutation_probe.py agent_workflows/benchmark_metrics.py::compute_aggregate_metrics --op return-none --format json -- tests/test_benchmark_runners_reports.py > .aw/state/trimcarry-24h56i/prop02.json` (gitignored, `.aw/.gitignore` `/state/`). Map the probe verdict with the `rq3q7v` rule: `killed` -> `guarded`; `survived` (after the passing preflight) -> `unguarded`; `killed-by-import` -> rerun once with `--op raise`, mapping that rerun's verdict the same way, else `unprovable`; `error`/`timeout`/`invalid` -> `unprovable` with the reason. Record the final verdict, the `newly_failing` ids and `wall_s` in this plan's V-03 evidence; Order 06 (`z2xs98`) cites it in the Set reconciliation.
  - Depends on: E-02
  - Expected outcome: a MEASURED final verdict (`guarded` or `unguarded`) faithfully recorded, `guarded` expected: probe verdict `killed` with a non-empty `newly_failing` drawn from the restored module (review demonstration F5 named `test_metrics_computation_and_proportions`, `test_benchmark_reports_generation_and_formatting`, `test_baseline_comparison_and_regression_triage`, `test_ci_safe_offline_benchmark_runner`; these names are non-binding pointers), and `checkout_status_changed` empty. A final `unprovable` does not meet the goal: record it with the reason and leave V-03 `failed`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior, not code structure (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES.md` P16). The restored module calls `compute_aggregate_metrics`, `RunnerDouble.run_trial`, `compare_with_baseline`, `generate_benchmark_report` and `run_ci_offline_benchmark` and asserts on their return values.
- The routine gate is bare `python3 -m pytest`; `pyproject.toml` `testpaths` is a fixed core list (since `ad9213cc6`, 2026-10-15), so a module outside it must be run explicitly and still runs in `make test-all` (`python3 -m pytest tests/ -m ''`).
- Restoring a deleted module at its ORIGINAL path is the precedent of executed plan `dmxc5h` (`tests/test_lane_input_manifest.py`).
- `tools/mutation_probe.py` operates on committed HEAD inside a disposable worktree and reports `checkout_status_changed`; a narrowed selection must pass a collect-only preflight first because a missing nodeid runs nothing yet yields a valid empty junit file (`rq3q7v` F-03).
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | `PROP-02` is `unprovable` only because the SURVIVOR run (full default selection, 8437 tests) produced no junit XML; the control was killed by 4 tests. | `hpjj44` `## Mutation results` row `PROP-02`: survivor `error` "mutant run could not produce junit XML", control `killed` (mutant_failing 4). |
| F2 | The deleted module passes unchanged at authoring HEAD `24988557b`. | Authoring run: `git show 19313eed^:tests/test_benchmark_runners_reports.py` copied to an untracked scratch path under `.aw/state/` and run with `python3 -m pytest -o addopts="" -q -p no:randomly <copy>` -> `14 passed in 0.20s`. |
| F3 | No surviving test imports `compute_aggregate_metrics`; the only surviving importer of `benchmark_metrics` is `tests/test_run_analytics_statistics.py`, which uses `wilson_score_interval`, `MetricValue` and `_FORBIDDEN_COST_KEYS`. | `grep -rn 'compute_aggregate_metrics\|benchmark_metrics' tests/*.py` at authoring HEAD. |
| F4 | `agent_workflows/benchmark_reports.py` imports `compute_aggregate_metrics` by name and calls it from `generate_benchmark_report` ("metrics = compute_aggregate_metrics(run_record.trials, ground_truths=ground_truths)"), so the report tests also reach the mutated function. | `agent_workflows/benchmark_reports.py`, `generate_benchmark_report`. |
| F5 | Review demonstration at HEAD `a178320e9`: the control form of E-03's probe, `python3 tools/mutation_probe.py agent_workflows/benchmark_metrics.py::compute_aggregate_metrics --op return-none --extra-test 19313eed:tests/test_benchmark_runners_reports.py --format json -- tests/test_benchmark_runners_reports.py`, returned `"verdict": "killed"`, `mutant_failing: 4`, `newly_failing_total: 4` (the four tests named in E-03), `checkout_status_changed: []`, `wall_s: 5.66`, with `git status --porcelain` empty before and after. The `hpjj44` control row lists only three of its four kills by name; this run names the fourth (`test_metrics_computation_and_proportions`). | `tools/mutation_probe.py` `probe` (verdict at the `confirmed` branch); review lane output. |

## Proposed changes (ordered, validatable)

1. Restore the module unchanged and run it (E-01).
2. Fast suite and path-scoped commit (E-02).
3. Narrowed survivor probe replacing `unprovable` with a measured verdict (E-03).

## Deferred / out of scope (with reason)

- Adding the module to `pyproject.toml` `testpaths`: changes the routine-gate composition, a maintainer decision outside backlog `9qvfie`.
  - Carrier-Declined: deliberate non-goal; the module still runs in `make test-all` and release-review.
- The other 37 benchmark keys in the rollup's triaged list (for example `agent_workflows/benchmark_reports.py::compare_with_baseline`, `PROP-29`): they are re-measured by Order 03 (`8dyt88`) at a HEAD that already contains this module, so any this restoration now reaches is classified there.
  - Carrier: 8dyt88

## Scope check

- Over-scope: none.
- Under-scope: none; outcome 1 of `9qvfie` is exactly `PROP-02`, and E-03 replaces its verdict with a measurement.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_benchmark_runners_reports.py` passes (E-01).
- Bare `python3 -m pytest` shows no failures (E-02).
- The narrowed `tools/mutation_probe.py` survivor run returns `killed` (E-03).

## Spec / documentation sync

N/A: test-only restoration; no spec or user-facing document describes this test module, and no behavior changes.

## Open questions

### OQ-01: Restore at the original path or as a new narrowly named module?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Original path. The whole file passes unchanged (F2) and every test in it is behavioral, so nothing is being cherry-picked; restoring at the original path matches executed plan `dmxc5h` and lets `tools/lost_guard_census.py` see the file as recreated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git ls-files` pre-check output (empty); pasted `-v` runner output in which every collected test is PASSED and the summary shows no failures or errors (or each failure with its cited commit and the one-line diff of the updated assertion), plus the empty output of the `grep -nE 'inspect\.|import ast|getsource'` check, plus `git diff --no-index <(git show 19313eed^:tests/test_benchmark_runners_reports.py) tests/test_benchmark_runners_reports.py` output (empty when unchanged).
  - Observed evidence:
    `git ls-files tests/test_benchmark_runners_reports.py`:
    (empty)
    `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_benchmark_runners_reports.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, cov-7.1.0, xdist-3.8.0
    collecting ... collected 14 items

    tests/test_benchmark_runners_reports.py::test_live_runner_adapters_four_target_models PASSED [  7%]
    tests/test_benchmark_runners_reports.py::test_runner_adapter_unknown_host_rejected PASSED [ 14%]
    tests/test_benchmark_runners_reports.py::test_runner_doubles_all_eight_outcomes PASSED [ 21%]
    tests/test_benchmark_runners_reports.py::test_live_execution_gate_blocks_executor_agent PASSED [ 28%]
    tests/test_benchmark_runners_reports.py::test_ablation_scheduler_matrix_and_randomization PASSED [ 35%]
    tests/test_benchmark_runners_reports.py::test_paired_comparison_computes_deltas_and_rejects_incompatible PASSED [ 42%]
    tests/test_benchmark_runners_reports.py::test_metrics_computation_and_proportions PASSED [ 50%]
    tests/test_benchmark_runners_reports.py::test_dollar_cost_is_strictly_rejected PASSED [ 57%]
    tests/test_benchmark_runners_reports.py::test_wilson_score_uncertainty PASSED [ 64%]
    tests/test_benchmark_runners_reports.py::test_release_thresholds_truth_table PASSED [ 71%]
    tests/test_benchmark_runners_reports.py::test_signed_human_revision_policy_enforcement PASSED [ 78%]
    tests/test_benchmark_runners_reports.py::test_benchmark_reports_generation_and_formatting PASSED [ 85%]
    tests/test_benchmark_runners_reports.py::test_baseline_comparison_and_regression_triage PASSED [ 92%]
    tests/test_benchmark_runners_reports.py::test_ci_safe_offline_benchmark_runner PASSED [100%]

    ============================== 14 passed in 0.27s ==============================
    ```
    `grep -nE 'inspect\.|import ast|getsource' tests/test_benchmark_runners_reports.py`:
    (empty, exit 1)
    `git diff --no-index <(git show 19313eed^:tests/test_benchmark_runners_reports.py) tests/test_benchmark_runners_reports.py`:
    (empty, exit 0)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted final summary line of bare `python3 -m pytest` (`N passed`, no failures), pasted `aw commit` output, and `git show --stat HEAD` listing only `tests/test_benchmark_runners_reports.py`.
  - Observed evidence:
    Final summary line of bare `python3 -m pytest`:
    `707 passed in 25.05s`
    `aw commit 24h56i -- tests/test_benchmark_runners_reports.py`:
    ```
    aw commit: committed 1 path(s): ae7781d3f55e6ed9fd2319eaeb4788d0338259e5
    ```
    `git show --stat HEAD`:
    ```
    commit ae7781d3f55e6ed9fd2319eaeb4788d0338259e5 (HEAD -> aw/lane/24h56i)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 16 18:18:09 2026 -0400

        work(24h56i): Restore the deleted benchmark runners and reports tests and prove they guard compute_aggregate_metrics

        AW-Run: run-20261016T221501Z-3469718
        AW-Item: 24h56i
        AW-Runner: aw agy run

     tests/test_benchmark_runners_reports.py | 680 ++++++++++++++++++++++++++++++++
     1 file changed, 680 insertions(+)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted collect-only summary (exit 0, collected count greater than zero and equal to the number of tests the V-01 `-v` run PASSED, which rules out the `rq3q7v` F-03 empty-selection false `survived`); the pasted probe JSON (produced by `tools/mutation_probe.py` `main`) showing `head` equal to the E-02 commit, `selection` equal to `["tests/test_benchmark_runners_reports.py"]`, `extra_tests_overwrote: []`, `verdict`, `newly_failing`, `checkout_status_changed: []` and `wall_s` (plus the `--op raise` rerun JSON if the first verdict was `killed-by-import`); the one-line final verdict mapping, which must be `guarded` or `unguarded` for `pass`; pasted `git status --short` showing no probe artifact is tracked or staged.
  - Observed evidence:
    Preflight collect-only summary:
    `14 tests collected in 0.17s`
    Probe JSON (.aw/state/trimcarry-24h56i/prop02.json):
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "ae7781d3f55e6ed9fd2319eaeb4788d0338259e5", "mutant_failing": 4, "newly_failing": ["tests.test_benchmark_runners_reports::test_baseline_comparison_and_regression_triage", "tests.test_benchmark_runners_reports::test_benchmark_reports_generation_and_formatting", "tests.test_benchmark_runners_reports::test_ci_safe_offline_benchmark_runner", "tests.test_benchmark_runners_reports::test_metrics_computation_and_proportions"], "newly_failing_total": 4, "operator": "return-none", "reason": null, "selection": ["tests/test_benchmark_runners_reports.py"], "target": "agent_workflows/benchmark_metrics.py::compute_aggregate_metrics", "verdict": "killed", "wall_s": 4.6}
    ```
    Final verdict mapping:
    Final verdict: `guarded` (probe verdict `killed`, 4 newly failing tests in restored module, wall_s: 4.6s)
    `git status --short`:
    (empty)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Scope fence: `- Scope-Paths:` declares only `tests/test_benchmark_runners_reports.py`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Probe output goes under the gitignored `.aw/state/`; nothing else is written in the tree. When you report tests or probes passed, paste the ACTUAL runner output; never claim success you did not run. Commit only this plan's own changed files through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` through `aw ipd finalize` (under a runner, the runner finalizes).
