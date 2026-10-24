# IPD: Restore behavioral coverage for benchmark ablation cell key and metric and gate to_dict payloads

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` (Set `trimgap`, groups 26, 28 and 29 of the `wo21z5` `## Filing plan`, remedy "investigate probe") carries three benchmark keys whose `wo21z5` verdict was `unprovable` ("control survived"): `benchmark_ablations.AblationTrialSpec.cell_key`, `benchmark_metrics.MetricSummary.to_dict` and `benchmark_thresholds.GateEvaluationResult.to_dict`, all with operator `return-none`. Re-measured at authoring HEAD `6c0a6b72a` (F-01, F-02): none of the three is reached by the routine core tier at all, and a `return-none` mutant of each SURVIVES the whole surviving non-core file that reaches it (`tests/test_benchmark_runners_reports.py`). So the probe IS applicable (the operator applies and the mutation changes the returned value, F-03); the gap is that no test anywhere asserts on what these three return.
- Scope: Add ONE new core-marked test module, `tests/test_benchmark_residual_payloads.py`, that calls the three keys through their public objects (`AblationScheduler.generate_schedule` and `AblationTrialSpec`, `compute_aggregate_metrics`, `GateEvaluationResult`) and asserts on the returned tuple and dicts, then probes each key under the core selection. EXCLUDES any production-code change; EXCLUDES the other benchmark keys owned by sibling items (`BenchmarkManifest.to_dict` is guarded by core, F-01 of plan `e6lq6y`; the digest keys are owned by plan `ya0h23`; `TrialResult.to_dict` and `RunnerAdapter.adapter_digest` belong to backlog `l9ssp6`).
- Scope-Paths: tests/test_benchmark_residual_payloads.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 29
- Highest E allocated: 05
- Author: opencode
- Id: 1z19cn

## Workflow history
- 2026-10-24 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 1z19cn verified (set trimgap, attempt 1).
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed (execution contract, E-04 commit/parent recorded, two-architectures-per-cell assertion); F-03/F-04 reproduced at 72da75876

- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm` (groups 26, 28, 29). Measured core reach at HEAD `6c0a6b72a` (all three unreached) and probed all three against their surviving non-core file (all `survived`) before writing expected outcomes.
- 2026-10-23 draft (opencode): created.

## Goal

Answer the item's "investigate probe" question for these three keys with recorded evidence (the probe is applicable; the gap is real), and close the gap so a `return-none` mutation of any of the three turns a routine core-tier test red. Done means all three report `verdict: killed` under a `-m core` selection containing the new module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the new core-tier module

- [x] E-01 Create `tests/test_benchmark_residual_payloads.py` with a provenance docstring naming backlog `nzc6dm`, plan `1z19cn` and findings `wo21z5`, `import pytest`, module-level `pytestmark = pytest.mark.core` (the pattern of `tests/test_engine_restored_behavior.py`), and a `CellKeyTests` class. Build `benchmark_runners.ModelProfile(model_id="m1", reasoning_effort="high", display_name="M", vendor="v")` and `benchmark_ablations.AblationScheduler(task_seeds=["t1"], model_profiles=[mp], hosts=["opencode"], architectures=[ARCH_MONOLITH, ARCH_MODULAR], trial_count=2, timeout_seconds=60.0, random_seed=7)`. Assert: `generate_schedule()` returns 4 specs; the set of their `cell_key` values is exactly `{("t1","m1","high","opencode",1), ("t1","m1","high","opencode",2)}` ; each of those two keys is carried by exactly two specs whose `ablation_config.architecture` values are `{ARCH_MONOLITH, ARCH_MODULAR}` (two architectures share each cell, which is the property the key exists for, and is what the paired-delta grouping relies on); and a single `AblationTrialSpec` built directly with `trial=2` has `cell_key == ("t1","m1","high","opencode",2)`.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_benchmark_residual_payloads.py` shows the `CellKeyTests` tests PASSED (values measured at authoring, F-04).
  - Execution state: performed

- [x] E-02 Add a `MetricSummaryToDictTests` class: `benchmark_metrics.compute_aggregate_metrics([]).to_dict()` returns a dict whose keys are exactly `{"sample_size", "completed_trials", "pending_trials", "metrics", "credits_or_quota_records"}`, with `sample_size == 0`, a `metrics` mapping of 14 entries, and `metrics["task_correctness"] == {"name": "task_correctness", "value": 0.0, "sample_size": 0, "ci_lower": 0.0, "ci_upper": 0.0, "is_available": True, "unit": "ratio"}`. Assert also that the dict round-trips through `json.dumps` (it is the report payload).
  - Depends on: none
  - Expected outcome: the class's tests PASS at HEAD (values measured at authoring, F-04).
  - Execution state: performed

- [x] E-03 Add a `GateEvaluationResultToDictTests` class: `benchmark_thresholds.GateEvaluationResult(passed=False, risk_class="high", findings=("f1", "f2"), checked_thresholds={"a": False}, model_profile_name="m").to_dict()` equals `{"passed": False, "risk_class": "high", "findings": ["f1", "f2"], "checked_thresholds": {"a": False}, "model_profile_name": "m"}` (note `findings` is converted from tuple to list), and the default `model_profile_name` serializes as `None`.
  - Depends on: none
  - Expected outcome: the class's tests PASS at HEAD (value measured at authoring, F-04).
  - Execution state: performed

### Task group 2: commit and prove the mutants die in core

- [x] E-04 Commit the module with `aw commit 1z19cn -- tests/test_benchmark_residual_payloads.py` and record the resulting commit hash as `<E-04 commit>` (its parent is `<E-04 parent>`, used by V-05), then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_benchmark_residual_payloads.py` for the module's own cost.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: bare run shows no failures and includes the new tests; the module's own call time is well under one second (pure in-memory calls).
  - Execution state: performed

- [x] E-05 For each key K in (`agent_workflows/benchmark_ablations.py::AblationTrialSpec.cell_key`, `agent_workflows/benchmark_metrics.py::MetricSummary.to_dict`, `agent_workflows/benchmark_thresholds.py::GateEvaluationResult.to_dict`), run `python3 tools/mutation_probe.py --op return-none --format json K -- -o addopts= -q -p no:randomly -n0 -m core tests/test_benchmark_residual_payloads.py`. The tool mutates in its own disposable worktree cut from HEAD, so it must run after E-04's commit. Record each `verdict`, `baseline_failing` and `mutant_failing`. A kill under this core-marked subset is a kill under the full core tier, which is a superset. If any key reports `survived`, add the missing assertion for that key to the module, commit it the same way, and re-probe.
  - Depends on: E-04
  - Expected outcome: three `verdict: killed` results, each with `baseline_failing: 0`.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_benchmark_residual_payloads.py` showing the provenance docstring (naming `nzc6dm`, `1z19cn`, `wo21z5`) and `pytestmark = pytest.mark.core`; paste the `-v` lines for every `CellKeyTests` test, each PASSED, and the test body lines asserting the cell-key set, the two-architectures-per-cell property, and the direct `trial=2` key; paste `grep -nE "inspect|getsource|ast\." tests/test_benchmark_residual_payloads.py` returning nothing.
  - Observed evidence:
```python
"""Behavioral tests for benchmark ablation cell key, metric summaries, and gate results.

Restores behavioral coverage for residual benchmark keys recorded in backlog item nzc6dm
(Set trimgap), plan 1z19cn, and research findings wo21z5.
"""

from __future__ import annotations

import json
import unittest

import pytest

from agent_workflows import benchmark_ablations
from agent_workflows import benchmark_metrics
from agent_workflows import benchmark_runners
from agent_workflows import benchmark_thresholds

pytestmark = pytest.mark.core
```
```
tests/test_benchmark_residual_payloads.py::CellKeyTests::test_ablation_trial_spec_cell_key PASSED [100%]
```
```python
        # The set of their cell_key values is exactly {("t1","m1","high","opencode",1), ("t1","m1","high","opencode",2)}
        cell_keys = {s.cell_key for s in specs}
        assert cell_keys == {
            ("t1", "m1", "high", "opencode", 1),
            ("t1", "m1", "high", "opencode", 2),
        }

        # Each of those two keys is carried by exactly two specs whose ablation_config.architecture values are {ARCH_MONOLITH, ARCH_MODULAR}
        for key in cell_keys:
            matching = [s for s in specs if s.cell_key == key]
            assert len(matching) == 2
            assert {s.ablation_config.architecture for s in matching} == {
                benchmark_ablations.ARCH_MONOLITH,
                benchmark_ablations.ARCH_MODULAR,
            }

        # A single AblationTrialSpec built directly with trial=2 has cell_key == ("t1","m1","high","opencode",2)
        ceilings = benchmark_ablations.make_ceilings(
            per_trial_wall_seconds=60.0,
            trial_count=2,
        )
        direct_spec = benchmark_ablations.AblationTrialSpec(
            task_seed="t1",
            model_profile=mp,
            host="opencode",
            ablation_config=benchmark_ablations.STANDARD_ABLATION_CONFIGS[
                benchmark_ablations.ARCH_MONOLITH
            ],
            trial=2,
            timeout_seconds=60.0,
            ceilings=ceilings,
            order_index=0,
        )
        assert direct_spec.cell_key == ("t1", "m1", "high", "opencode", 2)
```
Grep check returning nothing:
```sh
$ grep -nE "inspect|getsource|ast\." tests/test_benchmark_residual_payloads.py
(empty output, exit code 0)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` lines for every `MetricSummaryToDictTests` test, each PASSED.
  - Observed evidence:
```
tests/test_benchmark_residual_payloads.py::MetricSummaryToDictTests::test_metric_summary_to_dict_payload PASSED [ 75%]
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` lines for every `GateEvaluationResultToDictTests` test, each PASSED.
  - Observed evidence:
```
tests/test_benchmark_residual_payloads.py::GateEvaluationResultToDictTests::test_gate_evaluation_result_to_dict_payload PASSED [ 25%]
tests/test_benchmark_residual_payloads.py::GateEvaluationResultToDictTests::test_gate_evaluation_result_to_dict_default_model_profile_name PASSED [ 50%]
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only `tests/test_benchmark_residual_payloads.py`; paste the bare `python3 -m pytest` summary line showing `passed` and no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim, and the module's `--durations=0` output.
  - Observed evidence:
    `aw commit` output:
    ```
    aw commit: committed 1 path(s): 2f9c2879978f351db91842d38f2bfbec2eef28f8
    ```
    `git show --stat 2f9c2879978f351db91842d38f2bfbec2eef28f8`:
    ```
    commit 2f9c2879978f351db91842d38f2bfbec2eef28f8 (HEAD -> aw/lane/1z19cn_attempt2)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 23 21:50:27 2026 -0400

        work(1z19cn): Restore behavioral coverage for benchmark ablation cell key and metric and gate to_dict payloads

        AW-Run: run-20261024T014611Z-3126016
        AW-Item: 1z19cn
        AW-Runner: aw agy run

     tests/test_benchmark_residual_payloads.py | 136 ++++++++++++++++++++++++++++++
     1 file changed, 136 insertions(+)
    ```
    Bare `python3 -m pytest` summary:
    ```
    1679 passed, 11 warnings in 148.94s (0:02:28)
    ```
    `CORE TIER BUDGET EXCEEDED` block verbatim:
    ```
    WARNING:
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 148.95s exceeded budget of 30.00s.
    Host 1-minute load average: 30.92 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.  18.16s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       2.  18.11s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       3.  13.55s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       4.  12.16s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       5.  10.99s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       6.  10.14s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       7.   7.37s  tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested
       8.   6.83s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
       9.   6.81s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
      10.   6.58s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
    ===========================================================================================
    ```
    Module `--durations=0` output (`python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_benchmark_residual_payloads.py`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=4015278194
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/1z19cn_attempt2
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_benchmark_residual_payloads.py ....                           [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== slowest durations ===============================
    0.01s setup    tests/test_benchmark_residual_payloads.py::GateEvaluationResultToDictTests::test_gate_evaluation_result_to_dict_payload

    (11 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 4 passed in 0.83s ===============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the recorded `<E-04 commit>` and `<E-04 parent>` hashes; paste the three JSON outputs produced by `tools/mutation_probe.py` (E-05), each with `head` equal to the E-04 commit or later, a selection containing `-m core tests/test_benchmark_residual_payloads.py`, `verdict: killed` and `baseline_failing: 0`; paste `git diff --stat <E-04 parent>..HEAD -- agent_workflows/` showing no change.
  - Observed evidence:
    `<E-04 commit>`: `2f9c2879978f351db91842d38f2bfbec2eef28f8`
    `<E-04 parent>`: `45f067269c849f8004d48d6fc8d233dc77b77835`

    Probe JSON outputs:
    `agent_workflows/benchmark_ablations.py::AblationTrialSpec.cell_key`:
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "2f9c2879978f351db91842d38f2bfbec2eef28f8", "mutant_failing": 1, "newly_failing": ["tests.test_benchmark_residual_payloads.CellKeyTests::test_ablation_trial_spec_cell_key"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_benchmark_residual_payloads.py"], "target": "agent_workflows/benchmark_ablations.py::AblationTrialSpec.cell_key", "verdict": "killed", "wall_s": 9.16}
    ```

    `agent_workflows/benchmark_metrics.py::MetricSummary.to_dict`:
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "2f9c2879978f351db91842d38f2bfbec2eef28f8", "mutant_failing": 1, "newly_failing": ["tests.test_benchmark_residual_payloads.MetricSummaryToDictTests::test_metric_summary_to_dict_payload"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_benchmark_residual_payloads.py"], "target": "agent_workflows/benchmark_metrics.py::MetricSummary.to_dict", "verdict": "killed", "wall_s": 9.73}
    ```

    `agent_workflows/benchmark_thresholds.py::GateEvaluationResult.to_dict`:
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "2f9c2879978f351db91842d38f2bfbec2eef28f8", "mutant_failing": 2, "newly_failing": ["tests.test_benchmark_residual_payloads.GateEvaluationResultToDictTests::test_gate_evaluation_result_to_dict_default_model_profile_name", "tests.test_benchmark_residual_payloads.GateEvaluationResultToDictTests::test_gate_evaluation_result_to_dict_payload"], "newly_failing_total": 2, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_benchmark_residual_payloads.py"], "target": "agent_workflows/benchmark_thresholds.py::GateEvaluationResult.to_dict", "verdict": "killed", "wall_s": 10.67}
    ```

    `git diff --stat 45f067269c849f8004d48d6fc8d233dc77b77835..HEAD -- agent_workflows/` is empty (0 files changed).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Scope fence: `- Scope-Paths:` (`tests/test_benchmark_residual_payloads.py`) is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and then justified (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path). No production file under `agent_workflows/` may change. Commit only files you changed, through `aw commit 1z19cn -- tests/test_benchmark_residual_payloads.py` (plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL runner and probe output into each `V-*`; never claim a test passed or a mutant was killed that you did not run. Lifecycle: after every `V-*` reads `Result: pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize 1z19cn` itself.
