# IPD: Lock ipd_lint lint_file and check_item_dependencies dependency-rule coverage into the core tier

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `kkzvca` (Set `trimgap`, group 15 of the `wo21z5` `## Filing plan`) carries two production keys of `agent_workflows/ipd_lint.py`, `lint_file` and `check_item_dependencies`, which the `wo21z5` budget probe never measured (verdict `budget-exhausted`, operator `return-none`, control `tests/test_ipd_dependency_check.py`). The remedy is "probe then restore". Probing at authoring HEAD `f367b918a` (F-02, F-03) shows the control file is already restored (executed plan `zhoul7`, commit `5620a5a13`, which is NOT an ancestor of the `wo21z5` baseline `f3afece92`), and its explicit-path run kills both `return-none` mutants. But `zhoul7` marked only ONE test of that file `core` (`EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule`, which calls `check_engine.evaluate_ipd_dependencies` directly and never reaches either key), so under `-m core` the control file lets both mutants SURVIVE (F-03). The routine gate still goes red through `tests/test_ipd_lint.py`, but only by incidental crash or broad corpus fallout (F-04): no core test asserts the dependency-rule BEHAVIOR of the two keys, that is, which severity `check_item_dependencies` assigns at each lint phase and which resolution findings `lint_file` adds at a blocking phase.
- Scope: Add `@pytest.mark.core` to exactly the two `tests/test_ipd_dependency_check.py` tests that assert that behavior and that the explicit-path probe showed kill both mutants: `PhasedLintTests.test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase` and `PhasedLintTests.test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase`. Then re-probe both keys under `-m core` against the control file alone and record `killed`. EXCLUDES any production-code change; EXCLUDES any change to test bodies or tables (the file's docstring states `EvaluatorRuleMatrixTests` is left byte-unchanged deliberately, and the PhasedLint tables are already the behavior oracle); EXCLUDES other `ipd_lint.py` keys and other test files; EXCLUDES `FromSpecSchemaRecognitionTests.test_from_spec_does_not_raise_unknown_field` (it also kills both mutants, but asserts a metadata-recognition property, not dependency-rule behavior, so it adds no coverage of these keys beyond the two PhasedLint tests).
- Scope-Paths: tests/test_ipd_dependency_check.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: kkzvca
- Set: trimgap
- Order: 28
- Highest E allocated: 03
- Author: opencode
- Id: 3wkrng

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `kkzvca`. Ran `tools/mutation_probe.py --op return-none` for both keys at HEAD `f367b918a` under three selections (control file explicit-path; control file `-m core`; `tests/test_ipd_lint.py` `-m core`) and recorded the verdicts (F-02 to F-04). The gap is the core marking, not missing test bodies.
- 2026-10-23 draft (opencode): created.

## Goal

Make the routine core-tier gate assert the dependency-rule behavior of `ipd_lint.check_item_dependencies` (phase-dependent severity) and `ipd_lint.lint_file` (repo-aware resolution findings) directly, so a `return-none` mutation of either key fails a test that names the broken rule rather than only crashing unrelated tests. Done means both keys report `verdict: killed` under `-m core tests/test_ipd_dependency_check.py` alone, and the bare gate stays green inside its 30s budget.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: core-mark the behavior tests

- [ ] E-01 In `tests/test_ipd_dependency_check.py`, add the decorator `@pytest.mark.core` (the file already has `import pytest`, used by "@pytest.mark.core" on `EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule`) directly above `PhasedLintTests.test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase` and above `PhasedLintTests.test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase`. Change nothing else in the file. Commit through `aw commit 3wkrng -- tests/test_ipd_dependency_check.py` before E-02, because `tools/mutation_probe.py` probes a detached worktree at committed `HEAD` and cannot see an uncommitted edit.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -m core --collect-only -q tests/test_ipd_dependency_check.py` lists exactly three tests (the existing `EvaluatorRuleMatrixTests` one plus the two above), and `python3 -m pytest -o addopts="" -v tests/test_ipd_dependency_check.py` passes every test.
  - Execution state: pending

### Task group 2: prove the gap is closed

- [ ] E-02 Run `python3 tools/mutation_probe.py --op return-none agent_workflows/ipd_lint.py::<key> -- -o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py` for `<key>` in `lint_file` and `check_item_dependencies`, and confirm each output's `head:` equals the E-01 commit. Record each `head:`, `selection:`, `verdict:`, `mutant_failing:` and `newly_failing` list in Findings. Each `newly_failing` list must include at least one of the two newly core-marked `PhasedLintTests` tests. If either probe reports `survived`, mark this item `failed`, do not edit test bodies under this plan, and record the output for a follow-up backlog item.
  - Depends on: E-01
  - Expected outcome: two probe outputs, each `verdict: killed`, each `newly_failing` naming a `PhasedLintTests` test.
  - Execution state: pending

- [ ] E-03 Run the routine bare gate `python3 -m pytest` and confirm it passes within the core tier's 30s budget (the conftest budget check reports an overrun as a failure).
  - Depends on: E-02
  - Expected outcome: the bare run's summary line shows `passed` and no `failed`, with no core-budget overrun message.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): the two tests being core-marked call `ipd_lint.check_item_dependencies` on parsed documents and `ipd_lint.lint_file` on fixture repositories and assert on the returned rule codes across every phase. No test reads source.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`) and enforces a 30s wall-time budget (`conftest` "Enforce the wall-time budget on the core tier"). Per-test `@pytest.mark.core` is the established way `zhoul7` E-02 brought this file into the core tier selectively.
- Probe tool: `tools/mutation_probe.py` is the tool `wo21z5` used, so E-02 is directly comparable to the original (unmeasured) queue row. It mutates a detached worktree at committed `HEAD` only.
- Sibling precedent: pending `92tzo6` (Order 24) handled the same situation (control file restored after the `wo21z5` baseline) with a verification-first plan; pending `ya0h23` (Order 25) shows the probe-commit-then-probe ordering used in E-01/E-02.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Budget probe results` rows for `ipd_lint.py::lint_file` and `ipd_lint.py::check_item_dependencies`: operator `return-none`, verdict `budget-exhausted`, reason "budget exhausted at 10845.88s"; `wo21z5` baseline `head: f3afece925f5`. `hpjj44` `## Derived properties`: `tests/test_ipd_dependency_check.py` is `pass-exclusive`, carrying 3 exclusive lines of `lint_file` and 2 of `check_item_dependencies`. | The keys were never probed; the original verdict says nothing about coverage. The deleted control file is the only file with exclusive reach into the dependency branches of both keys. |
| F-02 | `git log -- tests/test_ipd_dependency_check.py` shows `5620a5a13` "work(zhoul7): Restore behavioral test coverage for check_engine layout, dependency and review-decision rules" (2026-10-17 23:59); `git merge-base --is-ancestor 5620a5a13 f3afece925` prints not-ancestor. `tools/mutation_probe.py --op return-none` at HEAD `f367b918a`, selection `-o addopts= -q -p no:randomly tests/test_ipd_dependency_check.py` | Control file restored after the probe baseline. Explicit-path: `lint_file` `verdict: killed`, `mutant_failing: 2` (`FromSpecSchemaRecognitionTests::test_from_spec_does_not_raise_unknown_field`, `PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase`); `check_item_dependencies` `verdict: killed`, `mutant_failing: 3` (those two plus `PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase`). Restoring test bodies is therefore not needed. |
| F-03 | Same probe, selection `-o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py`; `zhoul7` E-02 core-marks only `EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule` | Both keys `verdict: survived`, `mutant_failing: 0`. The single core test calls `check_engine.evaluate_ipd_dependencies` directly and reaches neither key. This is the gap. |
| F-04 | Same probe, selection `-m core tests/test_ipd_dependency_check.py tests/test_ipd_lint.py` (lint_file) and `-m core tests/test_ipd_lint.py` (check_item_dependencies) | Both `killed`, but via broad fallout: `lint_file` returning `None` breaks CLI/exit-code/rendering tests (`ExitCodeTests`, `SharedLifecycleRenderingTests`, ...); `check_item_dependencies` returning `None` makes `lint_text` fail to unpack its result (49 failures, `CitationAnchorsOnDemandTests`, `ContinuationSubfieldOutcomeTests`, ...). No `tests/test_ipd_lint.py` test asserts a `check.ipd-dependency-*` code (grep finds none), so a semantic regression in the dependency severity or resolution logic would pass the core tier. |
| F-05 | `pytest --durations=0 tests/test_ipd_dependency_check.py::PhasedLintTests` | Both PhasedLint tests pass in 0.68s total (the `lint_file` one 0.41s), so core-marking them costs well under 1s of the 30s budget. |

## Proposed changes (ordered, validatable)

1. E-01 core-marks the two `PhasedLintTests` behavior tests and commits.
2. E-02 re-probes both keys with `return-none` under `-m core` on the control file alone and records `killed`.
3. E-03 confirms the bare core gate passes inside budget.

## Deferred / out of scope (with reason)

- Adding a `tests/test_ipd_lint.py` test that asserts `check.ipd-dependency-*` codes.
  - Carrier-Declined: redundant; the two `PhasedLintTests` tables already assert every dependency code at every phase (F-02), and core-marking them closes F-04's semantic gap without duplicating the oracle.
- Core-marking `FromSpecSchemaRecognitionTests.test_from_spec_does_not_raise_unknown_field`.
  - Carrier-Declined: it asserts From-Spec metadata recognition, not dependency-rule behavior; it kills the mutants only because a `None` result has no diagnostics (F-02).
- Other `ipd_lint.py` keys.
  - Carrier-Declined: not carried by `kkzvca`.

## Scope check

- Over-scope: none. One test file, two decorator lines; no production change.
- Under-scope: none. Both carried keys are probed (E-02) and the "restore" half of the remedy is satisfied by F-02 (bodies already restored by `zhoul7`) plus E-01 (core reach).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_ipd_dependency_check.py` passes, and `-m core --collect-only -q` lists exactly the three core tests.
- Both `tools/mutation_probe.py --op return-none ... -m core tests/test_ipd_dependency_check.py` outputs pasted, each `verdict: killed`.
- Bare `python3 -m pytest` summary line pasted, no `failed`, no budget overrun.
- `git diff <E-01 commit>^ <E-01 commit> --stat` shows only `tests/test_ipd_dependency_check.py` with 2 insertions.

## Spec / documentation sync

N/A: this plan changes test markers only and no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore deleted test bodies, or only core-mark the restored ones?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: only core-mark. `zhoul7` already restored the file from `19313eed^` (F-02) and its explicit-path run kills both mutants; the remaining gap is that the killing tests are outside the core tier (F-03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -m core --collect-only -q tests/test_ipd_dependency_check.py` listing exactly the three core tests, the `-v` run showing every test PASSED, and `git show --stat` of the E-01 commit showing only `tests/test_ipd_dependency_check.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the full output of both `tools/mutation_probe.py --op return-none` runs (produced by `tools/mutation_probe.py` itself, E-02), each with `head:` equal to the E-01 commit, `selection:` containing `-m core tests/test_ipd_dependency_check.py`, `verdict: killed`, and a `newly_failing` list naming a `PhasedLintTests` test.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `passed`, no `failed`, and no core-budget overrun.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_ipd_dependency_check.py` and this plan through `aw commit 3wkrng -- <paths>`; never push. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
