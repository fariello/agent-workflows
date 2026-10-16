# IPD: Restore the deleted benchmark runners and reports tests and prove they guard compute_aggregate_metrics

- Date: 2026-10-16
- Kind: child
- Concern: Rollup backlog `9qvfie` outcome 1 is property `PROP-02` (`agent_workflows/benchmark_metrics.py::compute_aggregate_metrics`, 195 exclusive lines) with final verdict `unprovable`: the survivor probe used the full default selection and "could not produce junit XML", while the control (the deleted `tests/test_benchmark_runners_reports.py` re-added) was killed by 4 tests (findings `hpjj44` `## Mutation results`, row `PROP-02`). The only test that reached it was deleted by commit `19313eed`, so today no surviving test guards the benchmark metrics aggregation.
- Scope: Restore `tests/test_benchmark_runners_reports.py` byte-for-byte from `19313eed^` (it passes unchanged at authoring HEAD: `14 passed in 0.20s`), commit it, then re-run the audit's own instrument `tools/mutation_probe.py` with a NARROWED selection so the `unprovable` verdict is replaced by a measured `guarded` / `unguarded` verdict. No production code changes.
- Scope-Paths: tests/test_benchmark_runners_reports.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 24h56i

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Give `compute_aggregate_metrics` (and the benchmark runner, ablation, threshold and report surface the same file exercises) a surviving behavioral guard again, and settle `PROP-02` with a real mutation verdict instead of `unprovable`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Restore the deleted module

- [ ] E-01 Restore the file with `git show 19313eed^:tests/test_benchmark_runners_reports.py > tests/test_benchmark_runners_reports.py` (no edits). Confirm it reads no production source (`grep -nE 'inspect\.|import ast|getsource' tests/test_benchmark_runners_reports.py` prints nothing) and run it explicitly: `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_benchmark_runners_reports.py`. If any test fails at execution HEAD, classify the failure the way findings `hpjj44` `## Replay failures` does (cite the commit that changed the asserted behavior via `git log -S`/`-G` on the asserted symbol), and update ONLY the assertion that encodes the superseded behavior, never weakening an assertion whose behavior is unchanged.
  - Depends on: none
  - Expected outcome: 14 tests pass (or each failure is classified with a cited commit and minimally updated), and the module carries no source-reading assertion.
  - Execution state: pending

- [ ] E-02 Run the fast suite bare (`python3 -m pytest`) and commit only the restored module: `aw commit <this plan> -- tests/test_benchmark_runners_reports.py`.
  - Depends on: E-01
  - Expected outcome: fast suite green; one path-scoped commit containing only the module.
  - Execution state: pending

### Task group 2: Settle PROP-02 with a measured verdict

- [ ] E-03 With the module committed (the probe mutates COMMITTED HEAD in a disposable worktree, `tools/mutation_probe.py` `probe`), run the selection preflight `python3 -m pytest -o addopts= -q --collect-only tests/test_benchmark_runners_reports.py` (exit 0, 14 collected), then the survivor probe `python3 tools/mutation_probe.py agent_workflows/benchmark_metrics.py::compute_aggregate_metrics --op return-none --format json -- tests/test_benchmark_runners_reports.py`. Write its JSON to `.aw/state/trimcarry-24h56i/prop02.json` (gitignored, `.aw/.gitignore` `/state/`). Map the probe verdict with the `rq3q7v` rule: `killed` -> `guarded`; `survived` -> `unguarded`; `error`/`timeout`/`invalid` -> `unprovable` with the reason. Record the final verdict, the `newly_failing` ids and `wall_s` in this plan's V-03 evidence; Order 06 (`z2xs98`) cites it in the Set reconciliation.
  - Depends on: E-02
  - Expected outcome: probe verdict `killed` (final `guarded`), with `test_metrics_computation_and_proportions`, `test_benchmark_reports_generation_and_formatting`, `test_baseline_comparison_and_regression_triage` and `test_ci_safe_offline_benchmark_runner` among `newly_failing` (these four are the ones the control killed in `hpjj44`), and `checkout_status_changed` empty.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: pasted `-v` runner output listing all 14 tests PASSED (or each failure with its cited commit and the one-line diff of the updated assertion), plus the empty output of the `grep -nE 'inspect\.|import ast|getsource'` check, plus `git diff --no-index <(git show 19313eed^:tests/test_benchmark_runners_reports.py) tests/test_benchmark_runners_reports.py` output (empty when unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted final summary line of bare `python3 -m pytest` (`N passed`, no failures), pasted `aw commit` output, and `git show --stat HEAD` listing only `tests/test_benchmark_runners_reports.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted collect-only summary (`14 tests collected`, exit 0); the pasted probe JSON (produced by `tools/mutation_probe.py` `main`) showing `head` equal to the E-02 commit, `verdict`, `newly_failing`, `checkout_status_changed: []` and `wall_s`; the one-line final verdict mapping; pasted `git status --short` showing no probe artifact is tracked or staged.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Scope fence: `- Scope-Paths:` declares only `tests/test_benchmark_runners_reports.py`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Probe output goes under the gitignored `.aw/state/`; nothing else is written in the tree. When you report tests or probes passed, paste the ACTUAL runner output; never claim success you did not run. Commit only this plan's own changed files through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` through `aw ipd finalize` (under a runner, the runner finalizes).
