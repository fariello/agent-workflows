# IPD: Probe then restore core-tier behavioral coverage for runner_shared recovery routing and spec-impact keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `l2zsa9` (Set `trimgap`, group 11 of the `wo21z5` `## Filing plan`) carries three production keys of `agent_workflows/runner_shared.py` that the `wo21z5` budget probe never measured (verdict `budget-exhausted` at 11130.81s, operator `return-none`): `spec_impacts_for_queue`, `expand_selectors` and `route_recovery_turn`. Their control files were deleted by `19313eed` (`tests/test_spec_visibility.py`, `tests/test_runipd_selector_admission.py`, `tests/test_resumedupe.py`). Probing at authoring HEAD `35aa5ec9` under the routine core tier (bare `python3 -m pytest`, the runner merge gate) shows `spec_impacts_for_queue` and `route_recovery_turn` `return-none` mutants SURVIVE (F-01, F-03), while `expand_selectors` is already KILLED by nine existing core tests (F-02). So a regression making the spec-edit announcement collect nothing, or making a recovery turn skip recording its routing decision, would pass the merge gate.
- Scope: Add ONE new core-marked test module, `tests/test_runner_shared_restored_behavior.py`, holding three behavioral tests mined from the `19313eed^` control files: `TestSpecImpactsForQueue::test_impacts_are_collected_across_the_queue_and_bad_items_are_skipped` (from `tests/test_spec_visibility.py`) and `TestDurableRecording::test_the_routing_decision_and_its_inputs_are_recorded` plus `TestDurableRecording::test_a_reexecuted_run_is_distinguishable_from_a_verify_run_in_state_alone` (from `tests/test_resumedupe.py`), which together kill both surviving mutants (F-04). Then re-probe all three keys under the core selection. EXCLUDES any production-code change; EXCLUDES restoring the control files whole; EXCLUDES new tests for `expand_selectors` (already killed in core, F-02); EXCLUDES every control test that reads module source (`module_source`, `TestDriverSymmetry`, `TestBothHostsShareOneDefinition`, `TheTwoHostsShareOnePredicateTests`), which `AGENTS.md` forbids restoring.
- Scope-Paths: tests/test_runner_shared_restored_behavior.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: l2zsa9
- Set: trimgap
- Order: 29
- Highest E allocated: 04
- Author: opencode
- Id: wfm5iv

## Workflow history

- 2026-10-23 reviewed (opencode): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (V-01 grep unsatisfiable on verbatim body), PR-002 (gate lifecycle and honesty contract), PR-003 (E-03/V-03 exit-status bar on an enforcing host), PR-004 (baseline_failing and base sha evidence), PR-005 (ruff import layout) fixed; mined tests re-run 3 passed and expand_selectors re-probed killed at `e15d3e43` (F-07)
- 2026-10-23 to-review (opencode): authored from backlog `l2zsa9`. Probed all three keys at HEAD `35aa5ec9` under `-m core` (`spec_impacts_for_queue` and `route_recovery_turn` `survived`, `expand_selectors` `killed` by 9), and probed three-test subsets of the `19313eed^` control files (both surviving keys `killed`); measured bare core at `1675 passed, 11 warnings in 105.48s`.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of each of the three `l2zsa9` keys turn the routine core tier red. Two keys need a minimal set of restored behavioral tests in a core-marked module; the third is already guarded and only needs its verdict confirmed. Done means all three keys report `verdict: killed` under the full `-m core` selection with the new module committed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the minimal core-tier module

- [ ] E-01 Create `tests/test_runner_shared_restored_behavior.py` with a provenance docstring naming backlog `l2zsa9`, plan `wfm5iv`, source `19313eed^` and the two control files `tests/test_spec_visibility.py` and `tests/test_resumedupe.py`; imports grouped as ruff `I001` expects (`from __future__ import annotations`; stdlib `subprocess`, `tempfile`, `unittest`, `from pathlib import Path`; a separate third-party group `import pytest`; then first-party `from agent_workflows import oc_runipd as OC`, `runner_shared`, `worktree_lease as WL`), importing nothing the module does not use (not `agy_runipd`, `Palette` or `format_spec_impact_announcement`), so the mutating pre-commit `ruff --fix` hook does not rewrite and reject the commit; and module-level `pytestmark = pytest.mark.core` after the last import (the pattern of `tests/test_run_gates_restored_behavior.py`). Copy the fixtures from `19313eed^` unchanged in behavior: from `tests/test_spec_visibility.py` the `PLAN` template and `_plan` helper; from `tests/test_resumedupe.py` the `git`, `out`, `fixture_repo`, `commit_in_lane` helpers, the `ZHR6MC_SUBJECT` constant and the `ResumeRoutingBase` class (`setUp`, `state`, `item_for`, `resumed_shape`), importing `oc_runipd as OC` and `worktree_lease as WL`. Do NOT copy `module_source` (it reads production source). Prefix a copied name only if it collides between the two sources.
  - Depends on: none
  - Expected outcome: the module imports cleanly and defines the fixtures with no test methods yet.
  - Execution state: pending

- [ ] E-02 Add the three test methods with bodies copied verbatim from `19313eed^`: `spec_impacts_for_queue` = `TestSpecImpactsForQueue::test_impacts_are_collected_across_the_queue_and_bad_items_are_skipped` (pytest class with its `QUEUES` table and `tmp_path` fixture); `route_recovery_turn` = `TestDurableRecording::test_the_routing_decision_and_its_inputs_are_recorded` and `TestDurableRecording::test_a_reexecuted_run_is_distinguishable_from_a_verify_run_in_state_alone` (subclass of `ResumeRoutingBase`). Each test calls `runner_shared.spec_impacts_for_queue` or `oc_runipd.route_recovery_turn` and asserts on returned impact lists, the durable `recovery_routing` record and `events.jsonl`; none reads source.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_runner_shared_restored_behavior.py` reports 3 PASSED.
  - Execution state: pending

### Task group 2: commit and prove the mutants die in the core tier

- [ ] E-03 Record `git rev-parse HEAD` as `<base>`, then commit `tests/test_runner_shared_restored_behavior.py` with `aw commit wfm5iv -- tests/test_runner_shared_restored_behavior.py`, then run the routine bare gate `python3 -m pytest` and record the summary line and any `CORE TIER BUDGET EXCEEDED` block, plus the module's own durations from `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_runner_shared_restored_behavior.py`.
  - Depends on: E-02
  - Expected outcome: the bare run's summary shows `passed` with no `failed` or `error`, and its collected count includes the 3 new tests. It either exits 0 or exits 1 solely because of an enforced `CORE TIER BUDGET EXCEEDED` block (no `Core tier budget not enforced` line) whose listed slowest tests include none of the 3 new tests: the core tier already overruns its 30s budget before this plan (F-05; sibling `bli2ba` review measured 34.61s, exit 1, 1675 passed on a 12-CPU host), and `conftest.pytest_sessionfinish` sets exit 1 whenever the overrun is enforced. Any other non-zero exit is a failure. The module's summed call time stays under about 1s (F-05 measured 0.29s and 0.24s for the two git-backed tests).
  - Execution state: pending

- [ ] E-04 For each key K in (`spec_impacts_for_queue`, `expand_selectors`, `route_recovery_turn`), run `python3 tools/mutation_probe.py --op return-none agent_workflows/runner_shared.py::K -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` against the tree committed in E-03 (`tools/mutation_probe.py` mutates in an isolated worktree cut from HEAD, so the module must already be committed). Record each `head:`, `verdict:`, `baseline_failing:` and `mutant_failing:` line in Findings. A probe with `baseline_failing` above 0 or a `verdict:` other than `killed`/`survived` (for example `error` or `invalid`) is not a result: record it, fix the cause if it is in scope, and re-run. If a key reports `survived`, add the next killing test for that key from its control file (for `route_recovery_turn`: `TestFreshExecutionCases::test_d_an_unreadable_lane_is_undetermined_and_dispatched_as_fresh_execution` or `TestDurableRecording::test_a_first_attempt_records_no_routing`; for `expand_selectors`: `EverySelectorFormIsFilteredTests::test_naming_the_set_drops_the_retired_members_silently` from `tests/test_runipd_selector_admission.py`), commit it, and re-probe.
  - Depends on: E-03
  - Expected outcome: three `verdict: killed` lines, each with `baseline_failing: 0`, under the full core selection.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): every restored test calls runner functions on real temp dirs or throwaway git repos and asserts on results. The source-reading control tests are excluded.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget enforced by `conftest.pytest_sessionfinish`. Module-level `pytestmark = pytest.mark.core` applies to both pytest-style and `unittest.TestCase` classes (`tests/test_run_gates_restored_behavior.py`, `tests/test_engine_restored_behavior.py`).
- `oc_runipd.route_recovery_turn` is a one-line wrapper that calls `runner_shared.route_recovery_turn(..., save_state=save_state)`, so driving the OC wrapper exercises the shared key; `spec_impacts_for_queue` is re-exported from `runner_shared` into both drivers.
- Probe tool: `tools/mutation_probe.py` (`--op`, `--extra-test COMMIT:PATH`, selection after `--`) is the tool `wo21z5` and sibling plan `2qlg0w` used, so verdicts are comparable.
- Commit only through `aw commit wfm5iv -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `tools/mutation_probe.py --op return-none agent_workflows/runner_shared.py::spec_impacts_for_queue -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `35aa5ec9` | `verdict: survived`, `baseline_failing: 0`, `mutant_failing: 0`, `wall_s: 369.27`. The merge gate does not guard the pre-run spec-edit announcement collector. |
| F-02 | same probe for `expand_selectors` | `verdict: killed`, `mutant_failing: 9` (`wall_s: 378.01`), killed by `tests.test_run_selection_policy` (4 parametrized cases) and `tests.test_runner_shared` (`PathSelectorKindTests::test_path_selector_kind` and four `Verification*` tests). Already guarded by core; no restore owed. |
| F-03 | same probe for `route_recovery_turn` | `verdict: survived`, `mutant_failing: 0`, `wall_s: 422.08`. The merge gate does not guard recovery routing's durable record. |
| F-04 | same probe tool with `--extra-test 19313eed:<control>` and `-n0` over the E-02 node ids | `route_recovery_turn` with the two `TestDurableRecording` tests: `verdict: killed`, `mutant_failing: 2` (21.87s). `spec_impacts_for_queue` with `TestSpecImpactsForQueue`: `verdict: killed`, `mutant_failing: 1` (18.07s). |
| F-05 | `-n0 --durations=0` over the three E-02 tests copied from `19313eed^`; bare `python3 -m pytest` at HEAD `35aa5ec9` | The three tests: `3 passed in 1.20s`, calls 0.29s and 0.24s for the git-backed pair, under 0.005s for the table test. Bare core: `1675 passed, 11 warnings in 105.48s (0:01:45)`, already over the 30s budget before any change (host load and pre-existing tests; not caused here). The restore adds well under 1s CPU. |
| F-07 | `/plan-review` at lane HEAD `e15d3e43`: the three E-02 test bodies run verbatim from `19313eed^` copies with `-o addopts= -q -p no:randomly -n0 --durations=0`; `expand_selectors` re-probe under `-m core tests/test_run_selection_policy.py tests/test_runner_shared.py`; substring grep of the copied fixture-plus-test text | `3 passed in 1.01s` (calls 0.27s and 0.17s), so the mined bodies still match HEAD behavior. `expand_selectors`: `killed`, `baseline_failing: 0`, `mutant_failing: 9` (80.99s), F-02 reproduces. The old V-01 pattern `inspect` matched lines 100-101 of the copied text (`record["inspected_lane_id"]`, `record["inspected_branch"]`), so V-01 as written was unsatisfiable. |
| F-06 | `git show 19313eed^:tests/test_resumedupe.py`, `tests/test_spec_visibility.py`, `tests/test_runipd_selector_admission.py` | `module_source` and the driver-symmetry classes in all three files assert object identity or read module text; excluded as code-structure pins. The chosen tests call code and assert outcomes. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module with fixtures mined from `19313eed^`.
2. E-02 adds the three behavioral tests.
3. E-03 commits the module and checks the bare core gate and the module's cost.
4. E-04 re-probes all three keys under the full core selection against the committed tree.

## Deferred / out of scope (with reason)

- Restoring the three control files whole.
  - Carrier-Declined: no work is owed; the item's remedy is behavioral coverage of three keys, which three tests plus existing core tests deliver (F-02, F-04), and the core tier is already over budget (F-05).
- New tests for `expand_selectors`.
  - Carrier-Declined: no work is owed; nine existing core tests already kill its `return-none` mutant (F-02). E-04 re-confirms the verdict and carries a fallback if it regresses.
- The source-reading driver-symmetry tests.
  - Carrier-Declined: no work is owed; they pin code structure, which `AGENTS.md` forbids restoring (F-06).

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. Both surviving keys get killing tests (E-02); all three keys get a core-selection probe (E-04).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_runner_shared_restored_behavior.py`: 3 PASSED, per-test list pasted (E-02).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-03).
- Three `tools/mutation_probe.py` runs under `-m "core and not slow and not livecorpus" tests/`, full `head`/`target`/`operator`/`selection`/`verdict`/`mutant_failing` output pasted, each `killed` (E-04).
- `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty, `<base>` recorded in E-03 (no production change committed or left in the tree).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore tests for `expand_selectors` even though core already kills it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. F-02 shows nine existing core tests already kill the `return-none` mutant, so the item's gap does not exist for that key; adding tests would be redundant core-tier cost (sibling `92tzo6` and `2qlg0w` applied the same no-redundant-tests reasoning). E-04 still probes it, so the verdict is re-measured on the executed tree.

### OQ-02: Should E-04 probe the full core selection or only the new file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the full core selection, because the item's gap is "the routine gate does not kill the mutant" (F-01, F-03), and only a probe over that exact selection proves it closed. It costs about 6 to 7 minutes per key (F-01..F-03 wall times).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_runner_shared_restored_behavior.py` showing the provenance docstring (naming `l2zsa9`, `wfm5iv`, `19313eed^`) and `pytestmark = pytest.mark.core`; paste `grep -nwE "inspect|getsource|module_source|__file__" tests/test_runner_shared_restored_behavior.py` and `grep -nE "\bast\.|import ast" tests/test_runner_shared_restored_behavior.py`, both returning nothing (whole-word match: the verbatim `TestDurableRecording` body asserts on the record keys `inspected_lane_id` and `inspected_branch`, which a substring `inspect` pattern would falsely match, F-07).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_runner_shared_restored_behavior.py` listing the three named tests, each PASSED, and the `3 passed` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) showing only `tests/test_runner_shared_restored_behavior.py`; paste the bare `python3 -m pytest` summary line showing `passed` and no `failed` or `error`, its exit status, any `CORE TIER BUDGET EXCEEDED` block verbatim (an exit 1 passes only per E-03's expected outcome; state that check), and the `--durations=0` output for the new module.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full output of the three `tools/mutation_probe.py` runs (produced by the tool itself in E-04), each with `selection:` containing `-m core and not slow and not livecorpus tests/`, a `head:` equal to the E-03 commit or later, `baseline_failing: 0` and `verdict: killed`; paste `<base>` (recorded in E-03), `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/`, both showing no change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`); every open question is resolved. Commit only `tests/test_runner_shared_restored_behavior.py` and this plan through `aw commit wfm5iv -- <paths>`; never `git add -A`, never push. You MUST paste the ACTUAL runner and probe output into each `V-*`; never claim a test passed or a mutant was killed that you did not run. No production file under `agent_workflows/` may change. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize wfm5iv` itself.
