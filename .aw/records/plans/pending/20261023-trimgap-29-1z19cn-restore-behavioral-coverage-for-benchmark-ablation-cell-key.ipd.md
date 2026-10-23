# IPD: Restore behavioral coverage for benchmark ablation cell key and metric and gate to_dict payloads

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` (Set `trimgap`, groups 26, 28 and 29 of the `wo21z5` `## Filing plan`, remedy "investigate probe") carries three benchmark keys whose `wo21z5` verdict was `unprovable` ("control survived"): `benchmark_ablations.AblationTrialSpec.cell_key`, `benchmark_metrics.MetricSummary.to_dict` and `benchmark_thresholds.GateEvaluationResult.to_dict`, all with operator `return-none`. Re-measured at authoring HEAD `6c0a6b72a` (F-01, F-02): none of the three is reached by the routine core tier at all, and a `return-none` mutant of each SURVIVES the whole surviving non-core file that reaches it (`tests/test_benchmark_runners_reports.py`). So the probe IS applicable (the operator applies and the mutation changes the returned value, F-03); the gap is that no test anywhere asserts on what these three return.
- Scope: Add ONE new core-marked test module, `tests/test_benchmark_residual_payloads.py`, that calls the three keys through their public objects (`AblationScheduler.generate_schedule` and `AblationTrialSpec`, `compute_aggregate_metrics`, `GateEvaluationResult`) and asserts on the returned tuple and dicts, then probes each key under the core selection. EXCLUDES any production-code change; EXCLUDES the other benchmark keys owned by sibling items (`BenchmarkManifest.to_dict` is guarded by core, F-01 of plan `e6lq6y`; the digest keys are owned by plan `ya0h23`; `TrialResult.to_dict` and `RunnerAdapter.adapter_digest` belong to backlog `l9ssp6`).
- Scope-Paths: tests/test_benchmark_residual_payloads.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 29
- Highest E allocated: 05
- Author: opencode
- Id: 1z19cn

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm` (groups 26, 28, 29). Measured core reach at HEAD `6c0a6b72a` (all three unreached) and probed all three against their surviving non-core file (all `survived`) before writing expected outcomes.
- 2026-10-23 draft (opencode): created.

## Goal

Answer the item's "investigate probe" question for these three keys with recorded evidence (the probe is applicable; the gap is real), and close the gap so a `return-none` mutation of any of the three turns a routine core-tier test red. Done means all three report `verdict: killed` under a `-m core` selection containing the new module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the new core-tier module

- [ ] E-01 Create `tests/test_benchmark_residual_payloads.py` with a provenance docstring naming backlog `nzc6dm`, plan `1z19cn` and findings `wo21z5`, `import pytest`, module-level `pytestmark = pytest.mark.core` (the pattern of `tests/test_engine_restored_behavior.py`), and a `CellKeyTests` class. Build `benchmark_runners.ModelProfile(model_id="m1", reasoning_effort="high", display_name="M", vendor="v")` and `benchmark_ablations.AblationScheduler(task_seeds=["t1"], model_profiles=[mp], hosts=["opencode"], architectures=[ARCH_MONOLITH, ARCH_MODULAR], trial_count=2, timeout_seconds=60.0, random_seed=7)`. Assert: `generate_schedule()` returns 4 specs; the set of their `cell_key` values is exactly `{("t1","m1","high","opencode",1), ("t1","m1","high","opencode",2)}` (two architectures share each cell, which is the property the key exists for); and a single `AblationTrialSpec` built directly with `trial=2` has `cell_key == ("t1","m1","high","opencode",2)`.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_benchmark_residual_payloads.py` shows the `CellKeyTests` tests PASSED (values measured at authoring, F-04).
  - Execution state: pending

- [ ] E-02 Add a `MetricSummaryToDictTests` class: `benchmark_metrics.compute_aggregate_metrics([]).to_dict()` returns a dict whose keys are exactly `{"sample_size", "completed_trials", "pending_trials", "metrics", "credits_or_quota_records"}`, with `sample_size == 0`, a `metrics` mapping of 14 entries, and `metrics["task_correctness"] == {"name": "task_correctness", "value": 0.0, "sample_size": 0, "ci_lower": 0.0, "ci_upper": 0.0, "is_available": True, "unit": "ratio"}`. Assert also that the dict round-trips through `json.dumps` (it is the report payload).
  - Depends on: none
  - Expected outcome: the class's tests PASS at HEAD (values measured at authoring, F-04).
  - Execution state: pending

- [ ] E-03 Add a `GateEvaluationResultToDictTests` class: `benchmark_thresholds.GateEvaluationResult(passed=False, risk_class="high", findings=("f1", "f2"), checked_thresholds={"a": False}, model_profile_name="m").to_dict()` equals `{"passed": False, "risk_class": "high", "findings": ["f1", "f2"], "checked_thresholds": {"a": False}, "model_profile_name": "m"}` (note `findings` is converted from tuple to list), and the default `model_profile_name` serializes as `None`.
  - Depends on: none
  - Expected outcome: the class's tests PASS at HEAD (value measured at authoring, F-04).
  - Execution state: pending

### Task group 2: commit and prove the mutants die in core

- [ ] E-04 Commit the module with `aw commit 1z19cn -- tests/test_benchmark_residual_payloads.py`, then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_benchmark_residual_payloads.py` for the module's own cost.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: bare run shows no failures and includes the new tests; the module's own call time is well under one second (pure in-memory calls).
  - Execution state: pending

- [ ] E-05 For each key K in (`agent_workflows/benchmark_ablations.py::AblationTrialSpec.cell_key`, `agent_workflows/benchmark_metrics.py::MetricSummary.to_dict`, `agent_workflows/benchmark_thresholds.py::GateEvaluationResult.to_dict`), run `python3 tools/mutation_probe.py --op return-none --format json K -- -o addopts= -q -p no:randomly -n0 -m core tests/test_benchmark_residual_payloads.py`. The tool mutates in its own disposable worktree cut from HEAD, so it must run after E-04's commit. Record each `verdict`, `baseline_failing` and `mutant_failing`. A kill under this core-marked subset is a kill under the full core tier, which is a superset. If any key reports `survived`, add the missing assertion for that key to the module, commit it the same way, and re-probe.
  - Depends on: E-04
  - Expected outcome: three `verdict: killed` results, each with `baseline_failing: 0`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): every test calls the production object and asserts on its returned value; none reads source.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget that `conftest.pytest_sessionfinish` enforces only on 12+ CPUs and an un-oversubscribed host. Module-level `pytestmark = pytest.mark.core` is the established way in (`tests/test_engine_restored_behavior.py`, executed `33f8tn`).
- Probe tool: `tools/mutation_probe.py` (`--op`, `--format json`, `--extra-test COMMIT:PATH`, pytest selection after `--`) is the tool `wo21z5` and siblings `92tzo6`/`2qlg0w` used, so verdicts are comparable.
- Commit only through `aw commit 1z19cn -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/replay_coverage_diff.py baseline --out .aw/state/nzc6dm-auth/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `6c0a6b72a` (`functions: 2892`, `wall_s: 125.48`) | None of `AblationTrialSpec.cell_key`, `MetricSummary.to_dict`, `GateEvaluationResult.to_dict` appears in the core baseline: the routine gate never executes them. |
| F-02 | `python3 tools/mutation_probe.py --op return-none --format json <K> -- -o addopts= -q -p no:randomly -n 6 -m "not slow and not livecorpus" tests/test_benchmark_runners_reports.py` at `6c0a6b72a` | `cell_key`: `survived`, `mutant_failing 0` (5.43s). `MetricSummary.to_dict`: `survived`, 0 (5.03s). `GateEvaluationResult.to_dict`: `survived`, 0 (5.75s). The one surviving file that reaches them never asserts on their result, matching `wo21z5`'s "control survived". |
| F-03 | `tools.mutation_probe.apply_operator(src, qualname, "return-none")` at HEAD | Returns a mutated source for all three keys (operator applicable), and every key returns a non-None value at HEAD (F-04), so a `return-none` mutant is observable to any test that reads the result. The `unprovable` verdict was a coverage gap, not an inapplicable probe. |
| F-04 | direct calls at HEAD `6c0a6b72a` | `AblationScheduler(...).generate_schedule()` (inputs as in E-01) -> 4 specs, cell keys `{('t1','m1','high','opencode',1), ('t1','m1','high','opencode',2)}`. `compute_aggregate_metrics([]).to_dict()` -> keys `completed_trials, credits_or_quota_records, metrics, pending_trials, sample_size`, `sample_size 0`, 14 metrics, `task_correctness` = `{'name': 'task_correctness', 'value': 0.0, 'sample_size': 0, 'ci_lower': 0.0, 'ci_upper': 0.0, 'is_available': True, 'unit': 'ratio'}`. `GateEvaluationResult(passed=False, risk_class='high', findings=('f1','f2'), checked_thresholds={'a': False}, model_profile_name='m').to_dict()` -> `{'passed': False, 'risk_class': 'high', 'findings': ['f1', 'f2'], 'checked_thresholds': {'a': False}, 'model_profile_name': 'm'}`. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module and the `cell_key` tests.
2. E-02 adds the `MetricSummary.to_dict` payload tests.
3. E-03 adds the `GateEvaluationResult.to_dict` payload tests.
4. E-04 commits the module and records the bare core gate and the module's cost.
5. E-05 probes all three keys under the core selection against the committed tree.

## Deferred / out of scope (with reason)

- Core-marking `tests/test_benchmark_runners_reports.py` instead of writing a new module.
  - Carrier-Declined: no work is owed; F-02 shows that file does not kill any of the three mutants, so marking it core would add time without closing the gap.
- `benchmark_manifest.BenchmarkManifest.to_dict`, the other benchmark key in `nzc6dm` (group 27).
  - Carrier: e6lq6y

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. All three keys get direct assertions (E-01 to E-03) and a core-selection probe (E-05).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_benchmark_residual_payloads.py`: every test PASSED, list pasted (E-01 to E-03).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-04).
- Three `tools/mutation_probe.py` JSON results pasted, each `verdict: killed`, `baseline_failing: 0` (E-05).
- `git diff --stat <E-04 parent>..HEAD -- agent_workflows/` empty (no production change).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is the probe applicable to these "unprovable" keys?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. F-03 shows `return-none` applies to all three and each key returns a non-None value, so a test that reads the result sees the mutation. `wo21z5` marked them `unprovable` only because the control test also survived (F-02 reproduces that), which means no test asserted on the result, not that the probe cannot work. The remedy is therefore a direct assertion, which E-05 proves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_benchmark_residual_payloads.py` showing the provenance docstring (naming `nzc6dm`, `1z19cn`, `wo21z5`) and `pytestmark = pytest.mark.core`; paste the `-v` lines for every `CellKeyTests` test, each PASSED; paste `grep -nE "inspect|getsource|ast\." tests/test_benchmark_residual_payloads.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` lines for every `MetricSummaryToDictTests` test, each PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` lines for every `GateEvaluationResultToDictTests` test, each PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only `tests/test_benchmark_residual_payloads.py`; paste the bare `python3 -m pytest` summary line showing `passed` and no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim, and the module's `--durations=0` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the three JSON outputs produced by `tools/mutation_probe.py` (E-05), each with `head` equal to the E-04 commit or later, a selection containing `-m core tests/test_benchmark_residual_payloads.py`, `verdict: killed` and `baseline_failing: 0`; paste `git diff --stat <E-04 parent>..HEAD -- agent_workflows/` showing no change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract: all open questions are resolved. SCOPE FENCE: `tests/test_benchmark_residual_payloads.py` only; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Commit through `aw commit 1z19cn -- tests/test_benchmark_residual_payloads.py`, never push, never `git add -A`, and paste actual runner output for every `V-*`. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
