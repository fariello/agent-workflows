# IPD: Restore behavioral test coverage for check_engine layout, dependency and review-decision rules and doctor version drift

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the checker slice: group 18 (`check_engine.py`, 5 keys: `check_system_layout` verdict `unguarded`, `evaluate_ipd_dependencies` verdict `unprovable`, and three `unguarded-unreached`), group 51 (`hooks/ipd_dependency_statement_gate.py`, 1 key), group 53 (`review_findings.py`, 1 key) and group 58 (`doctor.py`, 1 key), 8 keys in all.
- Scope: Restore five deleted test modules from `19313eed^` at their original paths, with the edits listed per item, `core` markers on the cheapest tests that reach each key, and residual tests for two keys that survive early-return mutation (`_blocking_escalated_finding_ids`, and the `False` polarity of `check._on_staged_file`, F-05). The 8 keys: `check_engine.check_system_layout`, `evaluate_ipd_dependencies`, `evaluate_review_decision_escalation`, `_blocking_escalated_finding_ids`, `_plan_date`; `hooks.ipd_dependency_statement_gate.check._on_staged_file`; `review_findings.ReviewDocument.current_decisions`; `doctor._version_drift`. `tests/test_review_decisions.py` and `tests/test_doctor_and_marker.py` are not named by `b1mx2w` as reaching files but are the deleted files that reach `evaluate_review_decision_escalation`, `_blocking_escalated_finding_ids`, `current_decisions` and `_version_drift` once their `slow` mark is lifted (F-03). EXCLUDES any production change; EXCLUDES `tests/test_review_findings_gate.py` and `tests/test_review_findings.py` (F-06).
- Scope-Paths: tests/test_cli_layout.py, tests/test_ipd_dependency_check.py, tests/test_ipd_dependency_statement_gate.py, tests/test_review_decisions.py, tests/test_doctor_and_marker.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 18
- Highest E allocated: 06
- Author: opencode
- Id: zhoul7

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach with coverage contexts, durations, and an early-return mutation sweep over every key, plus a scratch `check_system_layout` return-`[]` mutation against `tests/test_cli_layout.py`; all scratch edits were reverted and `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 8 checker keys above reached by the routine bare core-tier run through behavioral tests that build fixture repositories, run the layout, dependency and review-decision rules and the dependency-statement hook, and assert on the drift each returns. Done means an early-return mutation of any of the 8 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for every E-item: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. If a kept test fails at execution HEAD, STOP on it: record it in Findings, and either update only that expectation for an intended change (cite the commit `git log -S` finds) or file a `bug` backlog item with `--blocks-release next` for a regression.

### Task group 1: restore the modules

- [ ] E-01 Restore `tests/test_cli_layout.py` unchanged except `@pytest.mark.core` on exactly `SystemLayoutRuleStateTests.test_an_installed_workspace_missing_the_document_reports_missing`. The file's 41 tests cost 29 to 39s summed CPU at authoring (subprocess CLI calls), so only this one rule-state test (one of the nine that fail under a `check_system_layout` return-`[]` mutation, F-04) joins the core tier; the rest run in explicit-path and thorough runs.
  - Depends on: none
  - Expected outcome: 41 tests pass on an explicit-path run; exactly 1 selected by `-m core`.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_ipd_dependency_check.py`, adding `@pytest.mark.livecorpus` to `GrandfatheringTests.test_current_repo_not_mass_failed` and `FromSpecDanglingRuleTests.test_current_repo_has_no_from_spec_findings` (both assert a property of THIS checkout's live `.aw/records/` corpus, which is exactly what the `livecorpus` marker in `pyproject.toml` exists for), and `@pytest.mark.core` on `EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule` (reaches `evaluate_ipd_dependencies` and `_plan_date`).
  - Depends on: none
  - Expected outcome: 10 tests pass with the default marker filter, 12 with `-m ""`; exactly 1 selected by `-m core`.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_ipd_dependency_statement_gate.py` unchanged with a module-level `pytestmark = pytest.mark.core` (16 tests, 0.6 to 0.8s summed CPU).
  - Depends on: none
  - Expected outcome: 16 tests pass, all core-selected.
  - Execution state: pending

- [ ] E-04 Restore `tests/test_review_decisions.py` with a module-level `pytestmark = pytest.mark.core` (25 tests, 0.5 to 0.75s). Update `ReviewsDecisionsVerbTests.test_unmatched_selector_is_a_clean_empty_state_not_an_error` for the intended behavior change made by commit `2b9e18bff` ("selquiet: make reviews decisions ... refuse zero-match selector with exit 2 (yxsfjc)"): assert `rc == 2` instead of `0` and drop the `assertIn("no review record matches", out)` line (the refusal now goes to stderr, measured `✗ FAIL  no artifact matched selector 'zzzzzz'`). Rename the test to `test_unmatched_selector_is_refused_with_exit_two`.
  - Depends on: none
  - Expected outcome: 25 tests pass; the renamed test asserts exit 2.
  - Execution state: pending

- [ ] E-05 Restore `tests/test_doctor_and_marker.py` with its module-level `pytestmark = pytest.mark.slow` replaced by `pytestmark = pytest.mark.core`, and delete `DoctorSummaryTests` (its one test calls `doctor.run` against the real working directory `"."`, took 62 to 66s of CPU at authoring, and trips the 60s hang guard in a full run, F-03). The kept `AgeMarkerTests` and `VersionDriftSourceRepoTests` build tmpdir fixtures and run in 0.17s.
  - Depends on: none
  - Expected outcome: 6 tests pass, all core-selected; the file contains no `DoctorSummaryTests` and no `pytest.mark.slow`.
  - Execution state: pending

### Task group 2: residual assertions

- [ ] E-06 Add two residual tests, each asserting values measured at authoring: (a) in `tests/test_review_decisions.py`, a `ResidualKeyTests(unittest.TestCase)` class with one test asserting `check_engine._blocking_escalated_finding_ids([{"Blocking": "yes", "Finding": "F-3, f-5."}, {"Blocking": "no", "Finding": "F-9"}, {"Blocking": "yes"}, {"Blocking": "YES", "Finding": "`F-7`;F-8"}])` equals `{"F-3", "F-5", "F-7", "F-8"}` and `_blocking_escalated_finding_ids(None)` equals `set()`; (b) in `tests/test_ipd_dependency_statement_gate.py`, one `HookRefusalTests` test asserting that with `aaaaaa` committed carrying `item_deps="executed:zzzzzz"` and a second valid plan `bbbbbb` (`item_deps="none"`) staged, `HOOK.check(self.repo)` returns `(0, [])` (the committed dangling plan is not a staged file, so `_on_staged_file` must say False for it). Re-measure each value at execution HEAD first.
  - Depends on: E-03, E-04
  - Expected outcome: two new tests pass and kill the scratch mutations named in V-06.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16). None of these five files reads production source; the only edits are tier marking, one obsolete expectation and one real-checkout test.
- `livecorpus` marker (`pyproject.toml` `markers`): a test asserting a property over this repository's own `.aw/records/` tree is deselected from the routine gate because any agent writing a plan can turn it red; E-02 applies it to the two real-checkout tests.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): `tests/test_cli_layout.py` alone would add about 29s of CPU, so it contributes one test.
- Backlog `wxgu55` (done) records that a since-deleted test in `tests/test_review_decisions.py` counted symbol occurrences in `check_engine.py` source; that test is absent from `19313eed^` (it was retired as a pin before the trim, plan `ev7t1w` row S-10), so the restored file carries no source-reading test.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for `check_engine.py`; `hpjj44` `## Derived properties` | `check_system_layout` is `unguarded` (survivor `survived`, control `killed (newly_failing: 11)`), `evaluate_ipd_dependencies` is `unprovable` (survivor `timeout`), the other three are `unguarded-unreached`. Derived reaching files: `tests/test_cli_layout.py`, `tests/test_ipd_dependency_check.py`, `tests/test_ipd_dependency_statement_gate.py`, `tests/test_doctor_and_marker.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26` | `test_cli_layout.py` 41 passed; `test_doctor_and_marker.py` 7 passed (62s, one slow test); `test_ipd_dependency_check.py` 12 passed; `test_ipd_dependency_statement_gate.py` 16 passed. `test_review_decisions.py` (replayed by direct copy) 35 passed with `test_review_findings_gate.py`, 1 failed: `test_unmatched_selector_is_a_clean_empty_state_not_an_error` `AssertionError: 2 != 0`, the intended `2b9e18bff` change. |
| F-03 | Coverage contexts with the default marker filter | Without `test_doctor_and_marker.py` (module-marked `slow`) and `test_review_decisions.py`, `evaluate_review_decision_escalation`, `_blocking_escalated_finding_ids`, `ReviewDocument.current_decisions` and `doctor._version_drift` have zero executed lines. With E-04/E-05 all 8 keys execute. `DoctorSummaryTests.test_summary_and_untracked_note` exceeded the 60s hang guard (`conftest.TestHangTimeout`) in a full `-m ""` run. |
| F-04 | Scratch `return []` at the top of `check_system_layout`, run against `tests/test_cli_layout.py`, reverted | 9 failed, 32 passed, including `test_an_installed_workspace_missing_the_document_reports_missing`, so the survivor verdict in F-01 was a gap of the trimmed suite, closed by restoring this file. |
| F-05 | Early-return mutation sweep over the 8 keys (bool keys both polarities), each reverted | Killed: `check_system_layout`, `evaluate_ipd_dependencies`, `evaluate_review_decision_escalation` (6 failed), `_plan_date`, `current_decisions` (5 failed), `_version_drift` (2 failed). SURVIVED: `_blocking_escalated_finding_ids` -> `set()` (25 passed), and `check._on_staged_file` -> `True` (only the False polarity was killed). Direct calls at HEAD produced the E-06 values. |
| F-06 | Coverage contexts with `test_review_findings_gate.py` added | `test_review_findings_gate.py` (1311 lines) reaches `_blocking_escalated_finding_ids` but, like the restored file, does not assert its parsed set; E-06 asserts it directly, so the large file adds nothing for this item. |

## Proposed changes (ordered, validatable)

1. E-01..E-05 restore the five modules with the listed tier marks and edits.
2. E-06 adds residual assertions for the two surviving keys.

## Deferred / out of scope (with reason)

- `DoctorSummaryTests.test_summary_and_untracked_note` is not restored.
  - Carrier-Declined: no work is owed for this item; it reaches no `q86fxm` key (`_version_drift` is reached by `VersionDriftSourceRepoTests`), it runs `doctor.run` against the real working directory, and it exceeds the 60s hang guard.
- `tests/test_review_findings_gate.py` and `tests/test_review_findings.py` are not restored.
  - Carrier-Declined: no work is owed for this item; F-06 shows they add no `q86fxm` key reach beyond E-04 and E-06.

## Scope check

- Over-scope: none. Five test files; no production code.
- Under-scope: none for the 8 keys (F-03, F-05, E-06).

## Required tests / validation

- `python3 -m pytest <the five files> -o addopts="" -v` passes (with and without `-m ""`), per-test list pasted.
- `python3 -m pytest <the five files> -o addopts="" -m core --collect-only -q` shows 51 core items (cli_layout 1, ipd_dependency_check 1, ipd_dependency_statement_gate 17, review_decisions 26, doctor_and_marker 6).
- Reach: `-m core --cov=agent_workflows.check_engine --cov=agent_workflows.review_findings --cov=agent_workflows.doctor --cov=agent_workflows.hooks.ipd_dependency_statement_gate --cov-report=term-missing`, each of the 8 keys executing.
- Mutation spot-checks (scratch, reverted): `check_system_layout` return `[]` (against the single core-marked cli_layout test), `evaluate_review_decision_escalation` return `[]`, `_version_drift` return `[]`, plus the three in V-06.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is the replay failure of the unmatched-selector test a regression or an intended change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: intended. Commit `2b9e18bff` (backlog `yxsfjc`) made `aw reviews decisions` refuse a zero-match selector with exit 2 on purpose; E-04 updates the expectation and renames the test. The same commit explains the `plan_readiness_recheck` replay failure handled by `9gjvrq`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `-v` run listing 41 PASSED; paste `-m core --collect-only -q` naming the single marked test; paste the failure of that single test under a scratch `check_system_layout` return-`[]` mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the default-filter run (10 passed, 2 deselected) and the `-m ""` run (12 passed); paste the failure of the core-marked test under a scratch `evaluate_ipd_dependencies` return-`[]` mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` run listing 16 PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a diff against `19313eed^` showing only the marker, docstring and the renamed exit-2 test; paste the `-v` run listing 25 PASSED; paste the failures from scratch `evaluate_review_decision_escalation` return-`[]` and `ReviewDocument.current_decisions` return-`()` mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` run listing 6 PASSED; paste `rg -n "DoctorSummaryTests|mark.slow" tests/test_doctor_and_marker.py` returning nothing; paste the failure from a scratch `doctor._version_drift` return-`[]` mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `-v` lines for the two new tests PASSED; paste the failures from scratch `_blocking_escalated_finding_ids` return-`set()` and `_on_staged_file` return-`True` mutations (reverted); paste the reach output from Required tests showing all 8 keys executing, the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the five Scope-Paths files through `aw commit zhoul7 -- <paths>`; never push. Mutation spot-checks are scratch production edits that must be reverted and absent from the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
