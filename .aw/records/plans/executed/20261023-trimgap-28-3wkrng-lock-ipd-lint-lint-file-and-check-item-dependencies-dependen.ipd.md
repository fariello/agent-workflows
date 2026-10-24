# IPD: Lock ipd_lint lint_file and check_item_dependencies dependency-rule coverage into the core tier

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `kkzvca` (Set `trimgap`, group 15 of the `wo21z5` `## Filing plan`) carries two production keys of `agent_workflows/ipd_lint.py`, `lint_file` and `check_item_dependencies`, which the `wo21z5` budget probe never measured (verdict `budget-exhausted`, operator `return-none`, control `tests/test_ipd_dependency_check.py`). The remedy is "probe then restore". Probing at authoring HEAD `f367b918a` (F-02, F-03) shows the control file is already restored (executed plan `zhoul7`, commit `5620a5a13`, which is NOT an ancestor of the `wo21z5` baseline `f3afece92`), and its explicit-path run kills both `return-none` mutants. But `zhoul7` marked only ONE test of that file `core` (`EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule`, which calls `check_engine.evaluate_ipd_dependencies` directly and never reaches either key), so under `-m core` the control file lets both mutants SURVIVE (F-03). The routine gate still goes red through `tests/test_ipd_lint.py`, but only by incidental crash or broad corpus fallout (F-04): no core test asserts the dependency-rule BEHAVIOR of the two keys, that is, which severity `check_item_dependencies` assigns at each lint phase and which resolution findings `lint_file` adds at a blocking phase.
- Scope: Add `@pytest.mark.core` to exactly the two `tests/test_ipd_dependency_check.py` tests that assert that behavior and that the explicit-path probe showed kill both mutants: `PhasedLintTests.test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase` and `PhasedLintTests.test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase`. Then re-probe both keys under `-m core` against the control file alone and record `killed`. EXCLUDES any production-code change; EXCLUDES any change to test bodies or tables (the file's docstring states `EvaluatorRuleMatrixTests` is left byte-unchanged deliberately, and the PhasedLint tables are already the behavior oracle); EXCLUDES other `ipd_lint.py` keys and other test files; EXCLUDES `FromSpecSchemaRecognitionTests.test_from_spec_does_not_raise_unknown_field` (it also kills both mutants, but asserts a metadata-recognition property, not dependency-rule behavior, so it adds no coverage of these keys beyond the two PhasedLint tests).
- Scope-Paths: tests/test_ipd_dependency_check.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: kkzvca
- Set: trimgap
- Order: 28
- Highest E allocated: 03
- Author: opencode
- Id: 3wkrng

## Workflow history
- 2026-10-24 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 3wkrng verified (set trimgap, attempt 1).
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (E-03 budget bar made satisfiable, collect-count bar replaced by before/after diff, baseline_failing and E-01 sha recorded, execution contract); probes re-run at 6d63e108a (F-06)

- 2026-10-23 to-review (opencode): authored from backlog `kkzvca`. Ran `tools/mutation_probe.py --op return-none` for both keys at HEAD `f367b918a` under three selections (control file explicit-path; control file `-m core`; `tests/test_ipd_lint.py` `-m core`) and recorded the verdicts (F-02 to F-04). The gap is the core marking, not missing test bodies.
- 2026-10-23 draft (opencode): created.

## Goal

Make the routine core-tier gate assert the dependency-rule behavior of `ipd_lint.check_item_dependencies` (phase-dependent severity) and `ipd_lint.lint_file` (repo-aware resolution findings) directly, so a `return-none` mutation of either key fails a test that names the broken rule rather than only crashing unrelated tests. Done means both keys report `verdict: killed` under `-m core tests/test_ipd_dependency_check.py` alone, and the bare gate stays green without the two added tests adding material wall time to the core tier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: core-mark the behavior tests

- [x] E-01 In `tests/test_ipd_dependency_check.py`, add the decorator `@pytest.mark.core` (the file already has `import pytest`, used by "@pytest.mark.core" on `EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule`) directly above `PhasedLintTests.test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase` and above `PhasedLintTests.test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase`. Change nothing else in the file. Do not modify the module docstring (it says `EvaluatorRuleMatrixTests` stays byte-unchanged; the two added lines are in `PhasedLintTests`, so that statement stays true). Commit through `aw commit 3wkrng -- tests/test_ipd_dependency_check.py` before E-02, because `tools/mutation_probe.py` probes a detached worktree at committed `HEAD` and cannot see an uncommitted edit. Record that commit's sha as `<E-01 commit>`.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -m core --collect-only -q tests/test_ipd_dependency_check.py` lists the two `PhasedLintTests` tests above in addition to whatever was core-marked at `<E-01 commit>^` (at review: only `EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule`), and nothing else newly; `python3 -m pytest -o addopts="" -v tests/test_ipd_dependency_check.py` passes every collected test with none failed, skipped or errored.
  - Execution state: performed

### Task group 2: prove the gap is closed

- [x] E-02 Run `python3 tools/mutation_probe.py --op return-none agent_workflows/ipd_lint.py::<key> -- -o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py` for `<key>` in `lint_file` and `check_item_dependencies`, and confirm each output's `head:` equals `<E-01 commit>` (or a later commit if this plan's own evidence commit landed in between) and `baseline_failing: 0`. Record each `head:`, `selection:`, `verdict:`, `mutant_failing:` and `newly_failing` list in Findings. Each `newly_failing` list must include at least one of the two newly core-marked `PhasedLintTests` tests. If either probe reports `survived`, mark this item `failed`, do not edit test bodies under this plan, and record the output for a follow-up backlog item.
  - Depends on: E-01
  - Expected outcome: two probe outputs, each `verdict: killed`, each `newly_failing` naming a `PhasedLintTests` test.
  - Execution state: performed

- [x] E-03 Run the routine bare gate `python3 -m pytest` and confirm it passes. The conftest budget check (`conftest.pytest_sessionfinish`) sets exit 1 on a wall-time overrun only when enforced (12 or more CPUs, host not oversubscribed, `AW_CORE_BUDGET_ENFORCE` not `0`); otherwise it prints a `WARNING:` block with a "Core tier budget not enforced:" reason. The tier is already over 30s before this change (F-06), so an overrun is not this item's failure unless it is caused here: if any `CORE TIER BUDGET EXCEEDED` block appears, paste it verbatim and also paste `python3 -m pytest -o addopts="" -n0 --durations=0 -m core tests/test_ipd_dependency_check.py` to show the two newly core tests' own cost (F-05 measured 0.68s together).
  - Depends on: E-02
  - Expected outcome: the bare run exits 0 with a summary line showing `passed` and no `failed` or `error`; any budget block is pasted with the module's own durations, and the two added tests account for at most about 1s of call time.
  - Execution state: performed

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
| F-04 | Same probe, selection `-m core tests/test_ipd_dependency_check.py tests/test_ipd_lint.py` (lint_file) and `-m core tests/test_ipd_lint.py` (check_item_dependencies) | Both `killed`, but via broad fallout: `lint_file` returning `None` breaks CLI/exit-code/rendering tests (`ExitCodeTests`, `SharedLifecycleRenderingTests`, ...); `check_item_dependencies` returning `None` makes `lint_text` fail to unpack its result (49 failures, `CitationAnchorsOnDemandTests`, `ContinuationSubfieldOutcomeTests`, ...). No `tests/test_ipd_lint.py` test mentions a `ipd-dependency` code (`grep -c ipd-dependency tests/test_ipd_lint.py` prints `0`, re-measured at review), so a semantic regression in the dependency severity or resolution logic would pass the core tier. |
| F-05 | `pytest --durations=0 tests/test_ipd_dependency_check.py::PhasedLintTests` | Both PhasedLint tests pass in 0.68s total (the `lint_file` one 0.41s), so core-marking them costs well under 1s of the 30s budget. |
| F-06 | review at HEAD `6d63e108a`: bare `python3 -m pytest`; `tools/mutation_probe.py --op return-none` for both keys over the three node ids (the two `PhasedLintTests` plus the existing core test) and over `-m core tests/test_ipd_dependency_check.py` | Bare gate before any change: `1675 passed, 11 warnings in 59.22s` with `CORE TIER BUDGET EXCEEDED ... Core tier budget not enforced: host oversubscribed` (load 17.62 on 12 CPUs), so the original E-03 bar "no core-budget overrun message" was not satisfiable independent of this plan. Three-node selection: `lint_file` `killed`, `baseline_failing: 0`, `mutant_failing: 1` (`test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase`); `check_item_dependencies` `killed`, `mutant_failing: 2` (both `PhasedLintTests`). Current `-m core` file selection: both `survived`, `mutant_failing: 0`. So F-02/F-03 reproduce at this HEAD and the two decorators are sufficient. |
| F-07 | E-02 execution probe at HEAD `d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f` with selection `-o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py`. `lint_file`: `verdict: killed`, `baseline_failing: 0`, `mutant_failing: 1`, `newly_failing: [tests.test_ipd_dependency_check.PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase]`. `check_item_dependencies`: `verdict: killed`, `baseline_failing: 0`, `mutant_failing: 2`, `newly_failing: [tests.test_ipd_dependency_check.PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase, tests.test_ipd_dependency_check.PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase]`. | Both mutant probes killed by the newly core-marked PhasedLintTests tests under `-m core`. Gap closed. |

## Proposed changes (ordered, validatable)

1. E-01 core-marks the two `PhasedLintTests` behavior tests and commits.
2. E-02 re-probes both keys with `return-none` under `-m core` on the control file alone and records `killed`.
3. E-03 confirms the bare core gate passes and records any pre-existing budget overrun with the added tests' own cost.

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

- `python3 -m pytest -o addopts="" -v tests/test_ipd_dependency_check.py` passes every collected test, and `-m core --collect-only -q` lists both `PhasedLintTests` tests plus the previously core-marked set and nothing else new.
- Both `tools/mutation_probe.py --op return-none ... -m core tests/test_ipd_dependency_check.py` outputs pasted, each `baseline_failing: 0` and `verdict: killed`.
- Bare `python3 -m pytest` summary line pasted, no `failed`; any `CORE TIER BUDGET EXCEEDED` block pasted verbatim with the module's `--durations=0` output.
- `git diff <E-01 commit>^ <E-01 commit> --stat` shows only `tests/test_ipd_dependency_check.py` with 2 insertions; `git diff <E-01 commit>^ HEAD --stat -- agent_workflows/` is empty.

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

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -m core --collect-only -q tests/test_ipd_dependency_check.py` run at `<E-01 commit>^` and at `<E-01 commit>`, showing that the difference is exactly the two `PhasedLintTests` tests; the `-v` run showing every collected test PASSED with none failed, skipped or errored; and `git show --stat <E-01 commit>` showing only `tests/test_ipd_dependency_check.py` with 2 insertions.
  - Observed evidence:
    ```
    Collect-only at <E-01 commit>^ (45f067269c849f8004d48d6fc8d233dc77b77835):
    $ python3 -m pytest -o addopts="" -m core --collect-only -q tests/test_ipd_dependency_check.py
    tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule

    NOTE: 11 tests were deselected by -m/-k and did not run (filtered by marker expression: 'core')
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    1/12 tests collected (11 deselected) in 1.19s

    Collect-only at <E-01 commit> (d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f):
    $ python3 -m pytest -o addopts="" -m core --collect-only -q tests/test_ipd_dependency_check.py
    tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
    tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase
    tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase

    NOTE: 9 tests were deselected by -m/-k and did not run (filtered by marker expression: 'core')
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    3/12 tests collected (9 deselected) in 1.45s

    Verbose test run:
    $ python3 -m pytest -o addopts="" -v tests/test_ipd_dependency_check.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=19670655
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 1 item                                                              collected 12 items

    tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_every_from_spec_link_shape_gets_its_own_answer PASSED [  8%]
    tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_current_repo_has_no_from_spec_findings PASSED [ 16%]
    tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_rule_is_registered_as_error_like_its_backlog_twin PASSED [ 25%]
    tests/test_ipd_dependency_check.py::GrandfatheringTests::test_the_cutover_decides_exactly_which_plans_owe_a_statement PASSED [ 33%]
    tests/test_ipd_dependency_check.py::GrandfatheringTests::test_current_repo_not_mass_failed PASSED [ 41%]
    tests/test_ipd_dependency_check.py::CheckSurfaceTests::test_every_check_entry_point_reports_the_same_findings_once PASSED [ 50%]
    tests/test_ipd_dependency_check.py::CycleHelperTests::test_every_graph_shape_yields_exactly_its_cycles PASSED [ 58%]
    tests/test_ipd_dependency_check.py::FromSpecSchemaRecognitionTests::test_both_graduation_source_carriers_are_recognized_and_optional PASSED [ 66%]
    tests/test_ipd_dependency_check.py::FromSpecSchemaRecognitionTests::test_from_spec_does_not_raise_unknown_field PASSED [ 75%]
    tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule PASSED [ 83%]
    tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase PASSED [ 91%]
    tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    WARNING: 1 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
        4.28s  tests/test_ipd_dependency_check.py::CheckSurfaceTests::test_every_check_entry_point_reports_the_same_findings_once
    ============================= 12 passed in 10.28s ==============================

    Git show stat:
    $ git show --stat d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f
    commit d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f (HEAD -> aw/lane/3wkrng)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 23 21:47:50 2026 -0400

        work(3wkrng): Lock ipd_lint lint_file and check_item_dependencies dependency-rule coverage into the core tier

        AW-Run: run-20261024T014601Z-3125847
        AW-Item: 3wkrng
        AW-Runner: aw agy run

     tests/test_ipd_dependency_check.py | 2 ++
     1 file changed, 2 insertions(+)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the full output of both `tools/mutation_probe.py --op return-none` runs (produced by `tools/mutation_probe.py` itself, E-02), each with `head:` equal to `<E-01 commit>` or a later commit of this plan, `selection:` containing `-m core tests/test_ipd_dependency_check.py`, `baseline_failing: 0`, `verdict: killed`, and a `newly_failing` list naming a `PhasedLintTests` test.
  - Observed evidence:
    ```
    $ python3 tools/mutation_probe.py --op return-none agent_workflows/ipd_lint.py::lint_file -- -o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py
    head: d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f
    target: agent_workflows/ipd_lint.py::lint_file
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_ipd_dependency_check.PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase
    wall_s: 15.03

    $ python3 tools/mutation_probe.py --op return-none agent_workflows/ipd_lint.py::check_item_dependencies -- -o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py
    head: d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f
    target: agent_workflows/ipd_lint.py::check_item_dependencies
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_ipd_dependency_check.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 2
    newly_failing (2 total):
      tests.test_ipd_dependency_check.PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase
      tests.test_ipd_dependency_check.PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase
    wall_s: 16.6
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `passed` and no `failed` or `error`, with its exit status; paste any `CORE TIER BUDGET EXCEEDED` block verbatim (including any "not enforced" reason) together with the `--durations=0` output for `-m core tests/test_ipd_dependency_check.py` showing the two added tests' call times; paste `git diff <E-01 commit>^ HEAD --stat -- agent_workflows/` showing no production change.
  - Observed evidence:
    ```
    Bare pytest run:
    $ python3 -m pytest
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 129.52s exceeded budget of 30.00s.
    Host 1-minute load average: 28.98 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.  18.38s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       2.  17.62s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       3.  11.96s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       4.  11.30s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       5.  10.09s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       6.   9.09s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       7.   6.53s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       8.   5.48s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
       9.   5.33s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
      10.   5.31s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
    ===========================================================================================
    1677 passed, 11 warnings in 129.52s (0:02:09)
    Exit code: 0

    Durations for core tests in tests/test_ipd_dependency_check.py:
    $ python3 -m pytest -o addopts="" -n0 --durations=0 -vv -m core tests/test_ipd_dependency_check.py
    ============================== slowest durations ===============================
    1.45s call     tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase
    0.85s call     tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
    0.00s call     tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase
    0.00s setup    tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase
    0.00s teardown tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase
    0.00s setup    tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
    0.00s teardown tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
    0.00s setup    tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase
    0.00s teardown tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase
    ======================= 3 passed, 9 deselected in 3.30s ========================

    Production diff check:
    $ git diff d42657c97d1b2ce86bd6bcc37c0afcec73c21c9f^ HEAD --stat -- agent_workflows/
    (empty - 0 files changed)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit 3wkrng -- tests/test_ipd_dependency_check.py` (plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL runner and probe output into each `V-*`; never claim a test passed or a mutant was killed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary (for example a follow-up backlog item filed under the E-02 `survived` branch) is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). No production file under `agent_workflows/` may change. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize 3wkrng` itself.
