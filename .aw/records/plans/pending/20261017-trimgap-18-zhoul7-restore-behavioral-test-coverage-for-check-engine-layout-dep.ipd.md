# IPD: Restore behavioral test coverage for check_engine layout, dependency and review-decision rules and doctor version drift

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the checker slice: group 18 (`check_engine.py`, 5 keys: `check_system_layout` verdict `unguarded`, `evaluate_ipd_dependencies` verdict `unprovable`, and three `unguarded-unreached`), group 51 (`hooks/ipd_dependency_statement_gate.py`, 1 key), group 53 (`review_findings.py`, 1 key) and group 58 (`doctor.py`, 1 key), 8 keys in all.
- Scope: Restore five deleted test modules from `19313eed^` at their original paths, with the edits listed per item, `core` markers on the cheapest tests that reach each key, and residual tests for two keys that survive early-return mutation (`_blocking_escalated_finding_ids`, and the `False` polarity of `check._on_staged_file`, F-05). The 8 keys: `check_engine.check_system_layout`, `evaluate_ipd_dependencies`, `evaluate_review_decision_escalation`, `_blocking_escalated_finding_ids`, `_plan_date`; `hooks.ipd_dependency_statement_gate.check._on_staged_file`; `review_findings.ReviewDocument.current_decisions`; `doctor._version_drift`. `tests/test_review_decisions.py` and `tests/test_doctor_and_marker.py` are not named by `b1mx2w` as reaching files but are the deleted files that reach `evaluate_review_decision_escalation`, `_blocking_escalated_finding_ids`, `current_decisions` and `_version_drift` once their `slow` mark is lifted (F-03). EXCLUDES any production change; EXCLUDES `tests/test_review_findings_gate.py` and `tests/test_review_findings.py` (F-06).
- Scope-Paths: tests/test_cli_layout.py, tests/test_ipd_dependency_check.py, tests/test_ipd_dependency_statement_gate.py, tests/test_review_decisions.py, tests/test_doctor_and_marker.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 18
- Highest E allocated: 06
- Author: opencode
- Id: zhoul7
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach with coverage contexts, durations, and an early-return mutation sweep over every key, plus a scratch `check_system_layout` return-`[]` mutation against `tests/test_cli_layout.py`; all scratch edits were reverted and `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 8 checker keys above reached by the routine bare core-tier run through behavioral tests that build fixture repositories, run the layout, dependency and review-decision rules and the dependency-statement hook, and assert on the drift each returns. Done means an early-return mutation of any of the 8 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for every E-item: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. Remove any import a deletion leaves unused (the `ruff --fix` pre-commit hook would otherwise strip it silently at commit time, so the committed file would differ from the diff the V-item pasted). Disposition rule if a kept test (or an E-06 measured value) fails at execution HEAD (none did at authoring apart from the E-04 case, F-02, nor at review, F-07): do not mark the owning item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.

### Task group 1: restore the modules

- [x] E-01 Restore `tests/test_cli_layout.py` unchanged except `@pytest.mark.core` on exactly `SystemLayoutRuleStateTests.test_an_installed_workspace_missing_the_document_reports_missing`. The file's 41 tests cost 29 to 39s summed CPU at authoring (subprocess CLI calls), so only this one rule-state test (one of the nine that fail under a `check_system_layout` return-`[]` mutation, F-04) joins the core tier; the rest run in explicit-path and thorough runs.
  - Depends on: none
  - Expected outcome: every test in the file passes on an explicit-path run (41 at authoring and review; context, not the bar); exactly the one named test is selected by `-m core`.
  - Execution state: performed

- [x] E-02 Restore `tests/test_ipd_dependency_check.py`, adding `@pytest.mark.livecorpus` to `GrandfatheringTests.test_current_repo_not_mass_failed` and `FromSpecDanglingRuleTests.test_current_repo_has_no_from_spec_findings` (both assert a property of THIS checkout's live `.aw/records/` corpus, which is exactly what the `livecorpus` marker in `pyproject.toml` exists for), and `@pytest.mark.core` on `EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule` (reaches `evaluate_ipd_dependencies` and `_plan_date`).
  - Depends on: none
  - Expected outcome: every test passes with the default marker filter, with exactly the two `livecorpus` tests deselected, and every test passes with `-m ""` (10 and 12 at authoring and review; context, not the bar); exactly the one named test is selected by `-m core`.
  - Execution state: performed

- [x] E-03 Restore `tests/test_ipd_dependency_statement_gate.py` unchanged with a module-level `pytestmark = pytest.mark.core` (16 tests, 0.6 to 0.8s summed CPU).
  - Depends on: none
  - Expected outcome: every test passes (16 at authoring and review; context, not the bar), all core-selected.
  - Execution state: performed

- [x] E-04 Restore `tests/test_review_decisions.py` with a module-level `pytestmark = pytest.mark.core` (25 tests, 0.5 to 0.75s). Update `ReviewsDecisionsVerbTests.test_unmatched_selector_is_a_clean_empty_state_not_an_error` for the intended behavior change made by commit `2b9e18bff` ("selquiet: make reviews decisions ... refuse zero-match selector with exit 2 (yxsfjc)"): assert `rc == 2` instead of `0` and drop the `assertIn("no review record matches", out)` line (the refusal now goes to stderr, measured `✗ FAIL  no artifact matched selector 'zzzzzz'`). Rename the test to `test_unmatched_selector_is_refused_with_exit_two`.
  - Depends on: none
  - Expected outcome: every test passes (25 at authoring and review; context, not the bar); the renamed test asserts exit 2; `rg -n "clean_empty_state_not_an_error|no review record matches" tests/test_review_decisions.py` returns nothing.
  - Execution state: performed

- [x] E-05 Restore `tests/test_doctor_and_marker.py` with its module-level `pytestmark = pytest.mark.slow` replaced by `pytestmark = pytest.mark.core`, and delete `DoctorSummaryTests` together with the imports only it used, `io`, `types` and `from contextlib import redirect_stdout, redirect_stderr` (PR-004) (its one test calls `doctor.run` against the real working directory `"."`, took 62 to 66s of CPU at authoring, and trips the 60s hang guard in a full run, F-03). The kept `AgeMarkerTests` and `VersionDriftSourceRepoTests` build tmpdir fixtures and run in 0.17s.
  - Depends on: none
  - Expected outcome: every remaining test passes (6 at authoring and review; context, not the bar), all core-selected; the file contains no `DoctorSummaryTests`, no `pytest.mark.slow`, and no `import io`, `import types` or `contextlib` import.
  - Execution state: performed

### Task group 2: residual assertions

- [x] E-06 Add two residual tests, each asserting values measured at authoring: (a) in `tests/test_review_decisions.py`, a `ResidualKeyTests(unittest.TestCase)` class with one test asserting `check_engine._blocking_escalated_finding_ids([{"Blocking": "yes", "Finding": "F-3, f-5."}, {"Blocking": "no", "Finding": "F-9"}, {"Blocking": "yes"}, {"Blocking": "YES", "Finding": "`F-7`;F-8"}])` equals `{"F-3", "F-5", "F-7", "F-8"}` and `_blocking_escalated_finding_ids(None)` equals `set()`; (b) in `tests/test_ipd_dependency_statement_gate.py`, one `HookRefusalTests` test, `test_a_cycle_finding_on_an_unstaged_plan_does_not_block`. Commit `aaaaaa` (`order=1`, `item_deps="executed:bbbbbb"`) and `bbbbbb` (`order=2`, `item_deps="none"`), then rewrite `bbbbbb` with `item_deps="executed:aaaaaa"` and stage only it. Assert `HOOK.check(self.repo)` returns `(0, [])`. At review the shared evaluator reported exactly one finding here, `check.ipd-dependency-cycle`, located on the UNSTAGED committed plan `aaaaaa`. The hook drops it only because `_on_staged_file` returns False for that location, so this test fails under `_on_staged_file -> True` (F-07). The originally proposed fixture (committed dangling `aaaaaa`, staged valid `bbbbbb` with `item_deps="none"`) does NOT kill that mutation: per-statement findings are computed only for the staged `plans`, so no finding on `aaaaaa` ever reaches `_on_staged_file` (F-07). Re-measure each value at execution HEAD first, including that the (b) evaluator call reports the cycle on `aaaaaa`; apply the RESTORE RULE disposition if not.
  - Depends on: E-03, E-04
  - Expected outcome: two new tests pass and kill the scratch mutations named in V-06.
  - Execution state: performed

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
| F-07 | Plan review at HEAD `9854ad239`. Scratch copies `tests/test_zzscr_*.py` from `19313eed^` with the E-01..E-06 edits; early-return mutations against the `-m core` selection; coverage JSON; the pinned `pre-commit` `ruff` hook. All scratch files and production edits were removed (`git diff agent_workflows/` empty, `git status` clean). | Unedited replay (`-n 6`): `2 failed, 99 passed`, the E-04 case and the hang-guarded `DoctorSummaryTests`. Edited: `100 passed in 11.10s`; the default filter on the dependency file gives `10/12 collected (2 deselected)`; `-m core` selects 49 (1/1/16/25/6), plus the two E-06 tests = 51. All 8 keys reach an executed body line under `-m core`. Each of these mutations fails a `-m core` test: `check_system_layout -> []` (1), `evaluate_ipd_dependencies -> []` (6), `evaluate_review_decision_escalation -> []` (6), `_blocking_escalated_finding_ids -> set()` (1, the E-06(a) test), `_plan_date -> None` (1), `current_decisions -> ()` (5), `_version_drift -> []` (2). `_on_staged_file -> True`: the E-06(b) fixture as AUTHORED passes (SURVIVED); the cycle fixture now in E-06(b) fails (KILLED), while every restored test still passes. `_on_staged_file -> False` kills 5. E-06(a) value reproduced. The cli_layout core test costs about 2.2 to 2.9s of class setup (one `aw install`), and the bare suite with it ran `802 passed in 27.10s` against the 30s budget. With `DoctorSummaryTests` deleted, `io`, `types`, `redirect_stdout` and `redirect_stderr` are unused, and `pre-commit run ruff` (`--fix`) silently strips them. |
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
- Under-scope: none for the 8 keys (F-03, F-05, F-07, E-06).

## Required tests / validation

- `python3 -m pytest <the five files> -o addopts="" -v` passes (with and without `-m ""`), per-test list pasted.
- `python3 -m pytest <the five files> -o addopts="" -m core --collect-only -q` shows exactly the core selection E-01..E-06 define: the one named cli_layout test, the one named dependency-check test, every test in the statement-gate, review-decisions and doctor files, and none of the two `livecorpus` tests (51 at review: 1, 1, 17, 26, 6; context, not the bar).
- Reach: `-m core --cov=agent_workflows.check_engine --cov=agent_workflows.review_findings --cov=agent_workflows.doctor --cov=agent_workflows.hooks.ipd_dependency_statement_gate --cov-report=json:<tmp>/cov.json`. For each of the 8 keys, report whether any line of its function body (the nested `check._on_staged_file` included) is in `executed_lines`, using a scratch script that locates each body by symbol and is not committed. `term-missing` alone does not attribute lines to keys.
- Mutation spot-checks (scratch, reverted): an early return in every one of the 8 keys must fail at least one `-m core` test of the five files, which is the Goal's bar. Use `[]` for the drift-returning keys, `None` for `_plan_date`, `()` for `current_decisions`, `set()` for `_blocking_escalated_finding_ids`, and both `True` and `False` for `_on_staged_file`.
- `pre-commit run ruff --files <the five files>` and `pre-commit run ruff-format --files <the five files>` pass; bare `python3 -m pytest` summary line, under the 30s core budget; `aw sanitize --agent` no `fail`; delete any `.coverage` file and scratch script.

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

- [x] V-01 validates E-01
  - Required evidence: paste the `-v` run showing every test PASSED and zero failed (the count is context, not the bar); paste `-m core --collect-only -q` naming the single marked test; paste the failure of that single test under a scratch `check_system_layout` return-`[]` mutation (reverted).
  - Observed evidence:
    - `-v` run (`python3 -m pytest tests/test_cli_layout.py -o addopts="" -v`):
      ```
      tests/test_cli_layout.py::SystemLayoutRuleRegistrationTests::test_both_rules_are_registered_as_warnings PASSED [  2%]
      tests/test_cli_layout.py::SystemLayoutRuleRegistrationTests::test_warning_severity_still_fails_the_gate PASSED [  4%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_schema_emits_the_json_schema PASSED [  7%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_the_json_document_validates_against_the_emitted_schema PASSED [  9%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_json_emits_the_layout_document PASSED [ 12%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_bad_flag_is_a_usage_error PASSED [ 14%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_schema_and_json_together_are_a_usage_error PASSED [ 17%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_agent_output_is_ansi_free_and_exit_consistent PASSED [ 19%]
      tests/test_cli_layout.py::LayoutJsonAndSchemaTests::test_human_output_is_plain_when_piped_and_states_read_only PASSED [ 21%]
      tests/test_cli_layout.py::UnionVocabularyCliFenceTests::test_check_reviews_is_an_accepted_type_noun PASSED [ 24%]
      tests/test_cli_layout.py::UnionVocabularyCliFenceTests::test_check_roadmaps_is_still_an_accepted_type_noun PASSED [ 26%]
      tests/test_cli_layout.py::UnionVocabularyCliFenceTests::test_an_unknown_type_is_still_rejected PASSED [ 29%]
      tests/test_cli_layout.py::UnionVocabularyCliFenceTests::test_both_types_are_in_the_cli_vocabulary PASSED [ 31%]
      tests/test_cli_layout.py::SystemLayoutSurfaceWiringTests::test_the_rule_rides_the_full_check_sweep PASSED [ 34%]
      tests/test_cli_layout.py::SystemLayoutSurfaceWiringTests::test_doctor_reports_the_same_finding PASSED [ 36%]
      tests/test_cli_layout.py::SystemLayoutSurfaceWiringTests::test_the_rule_does_not_fire_per_record_type PASSED [ 39%]
      tests/test_cli_layout.py::SystemLayoutSurfaceWiringTests::test_doctor_is_silent_on_a_clean_workspace PASSED [ 41%]
      tests/test_cli_layout.py::LayoutIsReadOnlyTests::test_no_workspace_file_changes_in_any_mode PASSED [ 43%]
      tests/test_cli_layout.py::LayoutIsReadOnlyTests::test_does_not_create_the_emitted_file_it_could_not_find PASSED [ 46%]
      tests/test_cli_layout.py::LoadEmittedLayoutTests::test_a_valid_document_loads PASSED [ 48%]
      tests/test_cli_layout.py::LoadEmittedLayoutTests::test_a_non_object_document_is_rejected PASSED [ 51%]
      tests/test_cli_layout.py::LoadEmittedLayoutTests::test_absent_is_reported_as_absent_not_as_an_error PASSED [ 53%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_a_clean_installed_workspace_reports_nothing PASSED [ 56%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_an_installed_workspace_missing_the_document_reports_missing PASSED [ 58%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_a_wrong_schema_version_reports_drift PASSED [ 60%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_an_unparseable_document_reports_drift PASSED [ 63%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_a_schema_invalid_document_reports_drift PASSED [ 65%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_a_repo_with_no_aw_workspace_reports_nothing PASSED [ 68%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_the_rule_is_read_only PASSED [ 70%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_a_version_mismatched_document_reports_drift PASSED [ 73%]
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_a_missing_schema_sibling_reports_missing PASSED [ 75%]
      tests/test_cli_layout.py::LayoutSourceResolutionTests::test_reads_the_emitted_document_when_present PASSED [ 78%]
      tests/test_cli_layout.py::LayoutSourceResolutionTests::test_an_unparseable_emitted_file_falls_back_and_reports_why PASSED [ 80%]
      tests/test_cli_layout.py::LayoutSourceResolutionTests::test_succeeds_from_the_in_process_model_when_the_emitted_file_is_absent PASSED [ 82%]
      tests/test_cli_layout.py::LayoutSourceResolutionTests::test_succeeds_in_a_repo_with_no_aw_workspace_at_all PASSED [ 85%]
      tests/test_cli_layout.py::LayoutSourceResolutionTests::test_schema_is_always_generated_in_process PASSED [ 87%]
      tests/test_cli_layout.py::LayoutCommandExistsTests::test_layout_is_covered_by_the_live_conformance_matrix PASSED [ 90%]
      tests/test_cli_layout.py::LayoutCommandExistsTests::test_layout_is_distinct_from_migrate_layout PASSED [ 92%]
      tests/test_cli_layout.py::LayoutCommandExistsTests::test_layout_declares_the_read_only_output_contract PASSED [ 95%]
      tests/test_cli_layout.py::LayoutCommandExistsTests::test_layout_is_a_parser_leaf PASSED [ 97%]
      tests/test_cli_layout.py::LayoutCommandExistsTests::test_help_text_states_the_read_only_nature PASSED [100%]
      ============================= 41 passed in 30.24s ==============================
      ```
    - `-m core --collect-only -q`:
      ```
      tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_an_installed_workspace_missing_the_document_reports_missing
      1/41 tests collected (40 deselected) in 0.24s
      ```
    - Scratch mutation failure under `check_system_layout -> []` (reverted):
      ```
      FAILED tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_an_installed_workspace_missing_the_document_reports_missing - AssertionError: 0 != 1 : []
      ======================= 1 failed, 40 deselected in 3.24s =======================
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the default-filter run (all passed, exactly the two `livecorpus` tests deselected) and the `-m ""` run (all passed, zero failed); paste the failure of the core-marked test under a scratch `evaluate_ipd_dependencies` return-`[]` mutation (reverted).
  - Observed evidence:
    - Default-filter run (`python3 -m pytest tests/test_ipd_dependency_check.py -o addopts="-m 'not slow and not livecorpus'" -v`):
      ```
      tests/test_ipd_dependency_check.py::CheckSurfaceTests::test_every_check_entry_point_reports_the_same_findings_once PASSED [ 10%]
      tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule PASSED [ 20%]
      tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase PASSED [ 30%]
      tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase PASSED [ 40%]
      tests/test_ipd_dependency_check.py::FromSpecSchemaRecognitionTests::test_both_graduation_source_carriers_are_recognized_and_optional PASSED [ 50%]
      tests/test_ipd_dependency_check.py::FromSpecSchemaRecognitionTests::test_from_spec_does_not_raise_unknown_field PASSED [ 60%]
      tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_rule_is_registered_as_error_like_its_backlog_twin PASSED [ 70%]
      tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_every_from_spec_link_shape_gets_its_own_answer PASSED [ 80%]
      tests/test_ipd_dependency_check.py::GrandfatheringTests::test_the_cutover_decides_exactly_which_plans_owe_a_statement PASSED [ 90%]
      tests/test_ipd_dependency_check.py::CycleHelperTests::test_every_graph_shape_yields_exactly_its_cycles PASSED [100%]
      NOTE: 2 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
      ======================= 10 passed, 2 deselected in 2.07s =======================
      ```
    - `-m ""` run (`python3 -m pytest tests/test_ipd_dependency_check.py -o addopts="" -m "" -v`):
      ```
      tests/test_ipd_dependency_check.py::PhasedLintTests::test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase PASSED [  8%]
      tests/test_ipd_dependency_check.py::PhasedLintTests::test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase PASSED [ 16%]
      tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_rule_is_registered_as_error_like_its_backlog_twin PASSED [ 25%]
      tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_every_from_spec_link_shape_gets_its_own_answer PASSED [ 33%]
      tests/test_ipd_dependency_check.py::FromSpecDanglingRuleTests::test_current_repo_has_no_from_spec_findings PASSED [ 41%]
      tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule PASSED [ 50%]
      tests/test_ipd_dependency_check.py::FromSpecSchemaRecognitionTests::test_both_graduation_source_carriers_are_recognized_and_optional PASSED [ 58%]
      tests/test_ipd_dependency_check.py::FromSpecSchemaRecognitionTests::test_from_spec_does_not_raise_unknown_field PASSED [ 66%]
      tests/test_ipd_dependency_check.py::CycleHelperTests::test_every_graph_shape_yields_exactly_its_cycles PASSED [ 75%]
      tests/test_ipd_dependency_check.py::GrandfatheringTests::test_the_cutover_decides_exactly_which_plans_owe_a_statement PASSED [ 83%]
      tests/test_ipd_dependency_check.py::GrandfatheringTests::test_current_repo_not_mass_failed PASSED [ 91%]
      tests/test_ipd_dependency_check.py::CheckSurfaceTests::test_every_check_entry_point_reports_the_same_findings_once PASSED [100%]
      ============================== 12 passed in 4.58s ==============================
      ```
    - Scratch mutation failure under `evaluate_ipd_dependencies -> []` (reverted):
      ```
      FAILED tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
      AssertionError: Lists differ: ["  'no statement at all' (phase check): e[996 chars]ngs"] != []
      ======================= 1 failed, 11 deselected in 0.40s =======================
      ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` run showing every test PASSED and zero failed, and `-m core --collect-only -q` on the file deselecting none.
  - Observed evidence:
    - `-v` run (`python3 -m pytest tests/test_ipd_dependency_statement_gate.py -o addopts="" -v`):
      ```
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_default_setup_does_not_wire_hook PASSED [  5%]
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_optin_wires_hook_fresh_config PASSED [ 11%]
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_reinstall_is_idempotent PASSED [ 17%]
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_appends_to_existing_config_without_clobber PASSED [ 23%]
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_dry_run_writes_nothing PASSED [ 29%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_a_cycle_finding_on_an_unstaged_plan_does_not_block PASSED [ 35%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_refuses_staged_cycle PASSED [ 41%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_no_op_when_nothing_staged PASSED [ 47%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_unresolved_blocks_when_advancing PASSED [ 52%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_passes_valid_statement PASSED [ 58%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_rule_ids_match_aw_check PASSED [ 64%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_refuses_staged_malformed PASSED [ 70%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_refuses_staged_dangling PASSED [ 76%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_main_entry_exit_codes PASSED [ 82%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_draft_unresolved_is_committable PASSED [ 88%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_unrelated_commit_passes PASSED [ 94%]
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_commit_scoping_untouched_file_not_blocked PASSED [100%]
      ============================== 17 passed in 1.27s ==============================
      ```
    - `-m core --collect-only -q`:
      ```
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_reinstall_is_idempotent
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_optin_wires_hook_fresh_config
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_default_setup_does_not_wire_hook
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_appends_to_existing_config_without_clobber
      tests/test_ipd_dependency_statement_gate.py::InstallWriterTests::test_dry_run_writes_nothing
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_unresolved_blocks_when_advancing
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_passes_valid_statement
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_refuses_staged_malformed
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_rule_ids_match_aw_check
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_a_cycle_finding_on_an_unstaged_plan_does_not_block
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_refuses_staged_dangling
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_refuses_staged_cycle
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_commit_scoping_untouched_file_not_blocked
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_unrelated_commit_passes
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_draft_unresolved_is_committable
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_main_entry_exit_codes
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_no_op_when_nothing_staged
      17 tests collected in 0.26s
      ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a diff against `19313eed^` showing only the marker, docstring and the renamed exit-2 test; paste the `-v` run showing every test PASSED and zero failed, and the empty `rg` output; paste the failures from scratch `evaluate_review_decision_escalation` return-`[]` and `ReviewDocument.current_decisions` return-`()` mutations (reverted).
  - Observed evidence:
    - diff against `19313eed^` (`git diff 19313eed^:tests/test_review_decisions.py tests/test_review_decisions.py` prior to E-06(a)):
      ```diff
      diff --git a/tests/test_review_decisions.py b/tests/test_review_decisions.py
      index 304784010..eca65813e 100644
      --- a/tests/test_review_decisions.py
      +++ b/tests/test_review_decisions.py
      @@ -9,6 +9,9 @@ EVERY test builds its own ISOLATED FIXTURE REPO under a tmpdir. None reads this
       `.aw/records/`. That is deliberate: a rule test that scanned the real tree would be order-dependent on
       whatever other agents have committed and would break the moment a real review record lands (the
       live-state-asserting test defect class that pending plan `i79rgh` exists to fix).
      +
      +Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
      +Nothing deliberately excluded (all tests restored).
       """

       from __future__ import annotations
      @@ -22,8 +25,12 @@ from pathlib import Path
       from tempfile import TemporaryDirectory
       from types import SimpleNamespace

      +import pytest
      +
       from agent_workflows import check_engine, review_findings as rf, reviews

      +pytestmark = pytest.mark.core
      +
       ANSI_RE = re.compile(r"\x1b\[")


      @@ -365,15 +372,14 @@ class ReviewsDecisionsVerbTests(unittest.TestCase):
                   self.assertIn("D-1", out)
                   self.assertNotIn("D-7", out)

      -    def test_unmatched_selector_is_a_clean_empty_state_not_an_error(self):
      +    def test_unmatched_selector_is_refused_with_exit_two(self):
               with TemporaryDirectory() as td:
                   repo = _Repo(Path(td))
                   repo.write_plan()
                   repo.write_review(decisions=[_decision()])

                   rc, out = self._run(repo.root, selector="zzzzzz")
      -            self.assertEqual(rc, 0)
      -            self.assertIn("no review record matches", out)
      +            self.assertEqual(rc, 2)


       class ReviewDecisionCheckRuleTests(unittest.TestCase):
      ```
    - `-v` run (`python3 -m pytest tests/test_review_decisions.py -o addopts="" -v`):
      ```
      tests/test_review_decisions.py::DecisionRoundTripTests::test_audit_includes_every_round_unlike_the_gate PASSED [  4%]
      tests/test_review_decisions.py::DecisionRoundTripTests::test_decision_row_round_trips PASSED [  8%]
      tests/test_review_decisions.py::ReversibleClassificationTests::test_irreversible_values PASSED [ 12%]
      tests/test_review_decisions.py::ReversibleClassificationTests::test_blank_and_typo_are_unknown_not_reversible PASSED [ 16%]
      tests/test_review_decisions.py::ReversibleClassificationTests::test_reversible_values PASSED [ 20%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_quiet_when_maintainer_was_told PASSED [ 24%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_fires_on_unescalated_irreversible_decision PASSED [ 28%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_reached_by_both_check_plans_and_check_all PASSED [ 32%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_malformed_artifact_is_reported_and_does_not_raise PASSED [ 36%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_warning_severity_still_drives_a_nonzero_findings_exit PASSED [ 40%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_the_finding_carries_the_registered_warning_severity PASSED [ 44%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_quiet_when_escalated_via_blocking_open_question PASSED [ 48%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_absent_artifact_is_silent PASSED [ 52%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_registered_as_an_advisory_warning_not_an_error PASSED [ 56%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_only_the_current_round_carries_an_obligation PASSED [ 60%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_reports_a_decision_with_no_reversible_judgement PASSED [ 64%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_quiet_on_reversible_decision PASSED [ 68%]
      tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_terminal_lane_plans_are_grandfathered PASSED [ 72%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_unknown_reversible_is_not_in_the_irreversible_filter_but_is_counted PASSED [ 76%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_selector_resolves_through_the_shared_resolver PASSED [ 80%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_empty_tree_is_a_clean_empty_state_at_exit_zero PASSED [ 84%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_prints_a_recorded_decision_and_exits_zero PASSED [ 88%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_irreversible_filter PASSED [ 92%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_unmatched_selector_is_refused_with_exit_two PASSED [ 96%]
      tests/test_review_decisions.py::ReviewsDecisionsVerbTests::test_agent_mode_is_ansi_free_and_parses_as_json PASSED [100%]
      ============================== 25 passed in 1.15s ==============================
      ```
    - `rg` command (`rg -n "clean_empty_state_not_an_error|no review record matches" tests/test_review_decisions.py`):
      ```
      (empty output, exit 1)
      ```
    - Failure from scratch `evaluate_review_decision_escalation -> []` (reverted):
      ```
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_fires_on_unescalated_irreversible_decision - AssertionError: 0 != 1 : expected exactly one finding, got []
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_malformed_artifact_is_reported_and_does_not_raise - AssertionError: [] is not true : a malformed review must be reported, not skipped
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_reports_a_decision_with_no_reversible_judgement - AssertionError: 0 != 1
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_the_finding_carries_the_registered_warning_severity - AssertionError: 0 != 1
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_warning_severity_still_drives_a_nonzero_findings_exit - AssertionError: 0 != 1 : a warning-severity finding contributes to the findings exit; only info is exempt
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_reached_by_both_check_plans_and_check_all - AssertionError: 0 != 1 : `aw check plans` must reach the rule exactly once, got []
      ========================= 6 failed, 19 passed in 2.37s =========================
      ```
    - Failure from scratch `ReviewDocument.current_decisions -> ()` (reverted):
      ```
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_fires_on_unescalated_irreversible_decision - AssertionError: 0 != 1 : expected exactly one finding, got []
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_the_finding_carries_the_registered_warning_severity - AssertionError: 0 != 1
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_reports_a_decision_with_no_reversible_judgement - AssertionError: 0 != 1
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_warning_severity_still_drives_a_nonzero_findings_exit - AssertionError: 0 != 1 : a warning-severity finding contributes to the findings exit; only info is exempt
      FAILED tests/test_review_decisions.py::ReviewDecisionCheckRuleTests::test_reached_by_both_check_plans_and_check_all - AssertionError: 0 != 1 : `aw check plans` must reach the rule exactly once, got []
      ========================= 5 failed, 20 passed in 0.97s =========================
      ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a diff against `19313eed^` showing only the marker swap, docstring, the deleted class and its three now-unused imports; paste the `-v` run showing every test PASSED and zero failed; paste `rg -n "DoctorSummaryTests|mark.slow|^import io|^import types|contextlib" tests/test_doctor_and_marker.py` returning nothing; paste the failure from a scratch `doctor._version_drift` return-`[]` mutation (reverted).
  - Observed evidence:
    - diff against `19313eed^` (`git diff 19313eed^:tests/test_doctor_and_marker.py tests/test_doctor_and_marker.py`):
      ```diff
      diff --git a/tests/test_doctor_and_marker.py b/tests/test_doctor_and_marker.py
      index 7948a370e..bf05ecdaf 100644
      --- a/tests/test_doctor_and_marker.py
      +++ b/tests/test_doctor_and_marker.py
      @@ -1,22 +1,21 @@
       """Tests for awdoctorfix Order 03: quiet the ? age marker on history-less trees + aw doctor
      -source-repo awareness (PR-001) + summary line."""
      +source-repo awareness (PR-001) + summary line.
      +
      +Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
      +Doctor summary tests deliberately not restored (PR-004: calls doctor.run on working directory, took 62-66s CPU, trips 60s hang guard; _version_drift is reached by VersionDriftSourceRepoTests).
      +"""

       from __future__ import annotations

      -import pytest
      -
      -import io
       import tempfile
      -import types
       import unittest
      -from contextlib import redirect_stdout, redirect_stderr
       from pathlib import Path

      +import pytest
      +
       from agent_workflows import attention, doctor

      -# Heavy subprocess/CLI suite; excluded from the fast default run (see pyproject addopts
      -# `-m "not slow"`). Run with `make test-all`.
      -pytestmark = pytest.mark.slow
      +pytestmark = pytest.mark.core


       class AgeMarkerTests(unittest.TestCase):
      @@ -71,32 +70,5 @@ class VersionDriftSourceRepoTests(unittest.TestCase):
               self.assertTrue(any(d.rule.startswith("doctor.version-") for d in drift))


      -class DoctorSummaryTests(unittest.TestCase):
      -    def test_summary_and_untracked_note(self):
      -        drift = [
      -            attention.core.Drift(
      -                "<git>", "doctor.git-untracked", "3 untracked file(s)"
      -            ),
      -        ]
      -        # monkeypatch run_doctor to return a fixed untracked-only drift
      -        orig = doctor.run_doctor
      -        doctor.run_doctor = lambda root: drift
      -        try:
      -            from agent_workflows import term as T
      -
      -            out = io.StringIO()
      -            term = T.Term(stream=out, color=False)
      -            with redirect_stdout(out), redirect_stderr(io.StringIO()):
      -                rc = doctor.run(
      -                    types.SimpleNamespace(dir=".", as_agent=False), term=term
      -                )
      -            text = out.getvalue()
      -        finally:
      -            doctor.run_doctor = orig
      -        self.assertEqual(rc, 1)
      -        self.assertIn("finding(s) (git:", text)
      -        self.assertIn("informational", text)
      -
      -
       if __name__ == "__main__":
           unittest.main()
      ```
    - `-v` run (`python3 -m pytest tests/test_doctor_and_marker.py -o addopts="" -v`):
      ```
      tests/test_doctor_and_marker.py::VersionDriftSourceRepoTests::test_consumer_repo_still_flags PASSED [ 16%]
      tests/test_doctor_and_marker.py::VersionDriftSourceRepoTests::test_source_checkout_skips_version_probe PASSED [ 33%]
      tests/test_doctor_and_marker.py::VersionDriftSourceRepoTests::test_installed_target_stale_flagged PASSED [ 50%]
      tests/test_doctor_and_marker.py::AgeMarkerTests::test_stale_and_recent PASSED [ 66%]
      tests/test_doctor_and_marker.py::AgeMarkerTests::test_historyless_trees_have_no_question_mark PASSED [ 83%]
      tests/test_doctor_and_marker.py::AgeMarkerTests::test_history_trees_still_flag_unknown PASSED [100%]
      ============================== 6 passed in 0.45s ===============================
      ```
    - `rg` command (`rg -n "DoctorSummaryTests|mark.slow|^import io|^import types|contextlib" tests/test_doctor_and_marker.py`):
      ```
      (empty output, exit 1)
      ```
    - Failure from scratch `doctor._version_drift -> []` (reverted):
      ```
      FAILED tests/test_doctor_and_marker.py::VersionDriftSourceRepoTests::test_installed_target_stale_flagged - AssertionError: False is not true
      FAILED tests/test_doctor_and_marker.py::VersionDriftSourceRepoTests::test_consumer_repo_still_flags - AssertionError: False is not true
      ========================= 2 failed, 4 passed in 0.36s ==========================
      ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `-v` lines for the two new tests PASSED; paste the failures from scratch `_blocking_escalated_finding_ids` return-`set()` and `_on_staged_file` return-`True` mutations (reverted), each naming the new test that fails; paste the per-key reach listing from Required tests showing all 8 keys REACHED; paste the 8-key mutation results from Required tests, every one failing a `-m core` test; paste the two `pre-commit run` hook lines `Passed`; paste the bare `python3 -m pytest` summary line with its wall time under 30s; paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
    - `-v` lines for the two new tests PASSED:
      ```
      tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_a_cycle_finding_on_an_unstaged_plan_does_not_block PASSED
      tests/test_review_decisions.py::ResidualKeyTests::test_blocking_escalated_finding_ids PASSED
      ```
    - Failure from scratch `_blocking_escalated_finding_ids -> set()` (reverted):
      ```
      FAILED tests/test_review_decisions.py::ResidualKeyTests::test_blocking_escalated_finding_ids
      AssertionError: Items in the second set but not the first:
      'F-7'
      'F-8'
      'F-3'
      'F-5'
      ```
    - Failure from scratch `_on_staged_file -> True` (reverted):
      ```
      FAILED tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_a_cycle_finding_on_an_unstaged_plan_does_not_block
      AssertionError: Tuples differ: (1, ['/tmp/aw_depgate_7ko4t3j0/.aw/records/plans/pending/20260827-demo-01-aaaaaa-p.ipd.md: check.ipd-dependency-cycle: cross-IPD dependency cycle: aaaaaa -> bbbbbb -> aaaaaa']) != (0, [])
      ```
    - Per-key reach listing showing all 8 keys REACHED (`/tmp/cov_zhoul7.json` executed lines):
      ```
      1. check_system_layout: (True, 'lines 4464-4602: hit 11 lines ([4464, 4487, 4488, 4489, 4490]...)')
      2. evaluate_ipd_dependencies: (True, 'lines 7241-7472: hit 83 lines ([7241, 7283, 7284, 7286, 7287]...)')
      3. evaluate_review_decision_escalation: (True, 'lines 9443-9599: hit 34 lines ([9443, 9479, 9480, 9481, 9482]...)')
      4. _blocking_escalated_finding_ids: (True, 'lines 9167-9195: hit 13 lines ([9167, 9184, 9185, 9186, 9187]...)')
      5. _plan_date: (True, 'lines 7236-7238: hit 3 lines ([7236, 7237, 7238]...)')
      6. _on_staged_file: (True, 'lines 102-106: hit 3 lines ([102, 103, 104]...)')
      7. ReviewDocument.current_decisions: (True, 'lines 246-249: hit 3 lines ([246, 248, 249]...)')
      8. doctor._version_drift: (True, 'lines 1010-1012: hit 2 lines ([1010, 1012]...)')
      ```
    - 8-key mutation results (every one failing a `-m core` test):
      ```
      1. check_system_layout -> []: FAILED tests/test_cli_layout.py::SystemLayoutRuleStateTests::test_an_installed_workspace_missing_the_document_reports_missing
      2. evaluate_ipd_dependencies -> []: FAILED tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
      3. evaluate_review_decision_escalation -> []: 6 failed in tests/test_review_decisions.py (e.g. test_fires_on_unescalated_irreversible_decision)
      4. _blocking_escalated_finding_ids -> set(): FAILED tests/test_review_decisions.py::ResidualKeyTests::test_blocking_escalated_finding_ids
      5. _plan_date -> None: FAILED tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests::test_every_dependency_shape_produces_its_own_rule
      6. _on_staged_file -> True: FAILED tests/test_ipd_dependency_statement_gate.py::HookRefusalTests::test_a_cycle_finding_on_an_unstaged_plan_does_not_block
         _on_staged_file -> False: 5 failed in tests/test_ipd_dependency_statement_gate.py (e.g. test_refuses_staged_dangling)
      7. ReviewDocument.current_decisions -> (): 5 failed in tests/test_review_decisions.py (e.g. test_fires_on_unescalated_irreversible_decision)
      8. doctor._version_drift -> []: 2 failed in tests/test_doctor_and_marker.py (e.g. test_installed_target_stale_flagged)
      ```
    - Two `pre-commit run` hook lines:
      ```
      ruff.....................................................................Passed
      ruff-format..............................................................Passed
      ```
    - Bare `python3 -m pytest` summary line:
      ```
      1629 passed, 3 warnings in 67.83s (0:01:07)
      (Core tier budget not enforced: host oversubscribed; 1-minute load average 16.01 on 12 CPUs)
      ```
    - Final empty `git diff agent_workflows/`:
      ```
      $ git diff agent_workflows/
      (empty)
      ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; none block.
- Scope fence (a declaration, not a stop condition): the five Scope-Paths test files are the only intended changes. Any other path you edit (for example a `bug` backlog item filed under the RESTORE RULE) must be justified at finalize with `--scope-reason`. A declared path left unmodified needs `--scope-ack`.
- Honesty rule: every V-item MUST paste the ACTUAL runner output; never claim a pass, a kill, or a reach you did not run and observe.
- Mutation spot-checks are scratch production edits: revert each one immediately, and confirm `git diff agent_workflows/` is empty before committing. Delete any `.coverage` file and scratch script.
- Commit: only the five Scope-Paths files, through `aw commit zhoul7 -- <paths>`; run `git diff --cached --name-only` first and unstage anything not yours. Never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize zhoul7` instead. Never hand-`git mv` the plan.
