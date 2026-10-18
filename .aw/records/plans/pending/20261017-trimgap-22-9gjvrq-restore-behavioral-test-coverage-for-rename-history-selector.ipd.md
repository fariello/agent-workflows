# IPD: Restore behavioral test coverage for rename history, selectors, readiness recheck, gate answers and run state

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the remaining small groups: 37 (`record_history.py`, 2 keys), 44 (`run_state.py`, 1), 45 (`cli.py`, 3 keys, verdict `property-unidentifiable`), 46 (`research_cmd.py`, 1), 49 (`runner_shared.py`, 1), 52 (`research_refs.py`, 1), 55 (`selectors.py`, 1), 57 (`artifact_refs.py`, 1), 59 (`plan_readiness.py`, 1) and 60 (`run_engine.py`, 1), 13 keys in all.
- Scope: Restore ten deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, with `core` markers on the cheapest tests reaching each key, and add residual tests for the two keys whose wrong value no restored test detects (`record_history._synthetic_key`, the `True` polarity of `Resolution.is_unique`, F-04). Review added `tests/test_help_token.py` (guards `_rewrite_help_token` against an identity mutation), a second core marker for `RecheckResult.holding`, and removal of the document-text `ContractConsistencyTests` class (F-04, E-01, E-04). The 13 keys: `record_history._synthetic_key`, `read_renames_for`; `run_state.is_legal_edge`; `cli._nv_resolve_types`, `_rewrite_help_token`, `_run_noun_verb`; `research_cmd.plan_set_priority`; `runner_shared.gate_answer_needs_human_remedy`; `research_refs.plan_reference_rewrites`; `selectors.Resolution.is_unique`; `artifact_refs._rp_type_facet`; `plan_readiness.RecheckResult.holding`; `run_engine.RunEngine.run_state`. EXCLUDES any production change; EXCLUDES `tests/test_cli_help_and_errors.py` and `tests/test_selector_resolver_parity.py` (F-05).
- Scope-Paths: tests/test_help_token.py, tests/test_artifact_rename.py, tests/test_artifact_group.py, tests/test_rename_ledger.py, tests/test_research_priority.py, tests/test_reference_matcher_parity.py, tests/test_selector_resolver_matrix.py, tests/test_plan_readiness_recheck.py, tests/test_gate_answer_wiring.py, tests/test_run_state_engine.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 22
- Highest E allocated: 06
- Author: opencode
- Id: 9gjvrq
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach via coverage contexts, per-test durations, and an early-return mutation sweep over the 13 keys (both polarities for boolean keys); scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 13 keys reached by the routine bare core-tier run through restored behavioral tests that rename and regroup artifacts through the CLI, append and read the rename ledger, resolve selectors, plan reference rewrites, recheck plan readiness, render gate-answer remedies, and drive the run state machine, asserting on exit codes, written files and returned records. Done means an early-return mutation of any of the 13 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for E-01..E-05: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. Disposition rule if a kept test fails at execution HEAD: do not mark the item performed until it is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue. Insert `pytestmark = pytest.mark.core` AFTER the last complete top-level import statement (several files end their imports with a parenthesized multi-line `from agent_workflows import (...)`).

### Task group 1: restore the modules

- [x] E-01 Restore `tests/test_artifact_rename.py` and `tests/test_artifact_group.py` unchanged, with `@pytest.mark.core` on exactly `TestArtifactRename.test_rename_comms_is_unsupported` and `TestArtifactRename.test_rename_roadmaps` (they reach `_synthetic_key` and the three `cli.py` noun-verb keys for 0.27 to 0.33s; `tests/test_artifact_group.py` stays wholly in the explicit-path tier as an additional reach of `_nv_resolve_types` and `_run_noun_verb`). Also restore `tests/test_help_token.py` unchanged with `@pytest.mark.core` on exactly `HelpTokenTests.test_pure_rewrite` and `HelpTokenTests.test_option_value_help_preserved` (pure function calls, under 0.01s): the rename tests reach `_rewrite_help_token` but only a `return None` or `return []` mutation fails them, while an identity mutation (`return list(argv)`, "never rewrite `help`") passes the whole nine-file set and is killed only by `test_pure_rewrite` (measured at review).
  - Depends on: none
  - Expected outcome: every restored test in the three files passes and exactly the four named tests are selected by `-m core` (7, 8 and 4 tests at review; the counts are context, not the bar).
  - Execution state: performed

- [x] E-02 Restore `tests/test_rename_ledger.py` with `@pytest.mark.core` on exactly `AppendRenameUnitTests.test_synthetic_key_only_via_case3_path` (reaches `read_renames_for`; the file's `CliEmissionTests` cost 2.4s), and `tests/test_run_state_engine.py` with `@pytest.mark.core` on exactly `TestRunStateMachineTransitionTable.test_exhaustive_state_actor_matrix` and `TestRunEngineConcurrencyAndIntegrity.test_cancellation_from_multiple_states` (reach `is_legal_edge` and `RunEngine.run_state`).
  - Depends on: none
  - Expected outcome: every restored test passes and exactly the three named tests are selected by `-m core` (12 and 19 tests at review).
  - Execution state: performed

- [x] E-03 Restore `tests/test_research_priority.py`, `tests/test_reference_matcher_parity.py` and `tests/test_selector_resolver_matrix.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each (11, 5 and 20 tests; under 0.3s summed).
  - Depends on: none
  - Expected outcome: every restored test passes and all are core-selected (11, 5 and 20 at review).
  - Execution state: performed

- [x] E-04 Restore `tests/test_plan_readiness_recheck.py`, deleting the whole `AntiForkTests` class (its own docstring says it is "Asserted against the module SOURCE rather than by behavior": `test_the_recheck_calls_all_three_shipped_predicates` and `test_the_recheck_does_not_reimplement_the_open_question_parser` slice `plan_readiness.py` and `review_findings.py` source) and `WriteTargetIsPinnedTests.test_go_is_UNREACHABLE_because_the_target_is_not_a_parameter` (asserts on `inspect.signature`), and the whole `ContractConsistencyTests` class (its `setUp` reads `.aw/system/workflows/plan-review/plan-review.md` and its four tests assert that specific wording remains in that document, which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" item (3) forbids; sibling `8bhcd3` drops docstring-text tests on the same ground). Update `CliVerbTests.test_an_unresolved_selector_exits_1` for the intended change made by commit `2b9e18bff` ("selquiet: make reviews decisions, record-history, graduation and ipd recheck-readiness refuse zero-match selector with exit 2 (yxsfjc)"): assert exit 2 and rename it `test_an_unresolved_selector_exits_2`. Mark `@pytest.mark.core` on exactly `ConditionsAreReportedIndividuallyTests.test_a_NON_blocking_open_question_does_not_hold_the_condition` and `ConditionsAreReportedIndividuallyTests.test_a_blocking_question_holds_only_the_question_condition` (both reach `RecheckResult.holding`; the file's subprocess `CliVerbTests` cost 4.8s). The second is required: the first asserts `holding() == ()`, so a `holding` return-`()` mutation passes it and passed the whole core selection at review; the second asserts a non-empty held set and fails under that mutation (0.08s).
  - Depends on: none
  - Expected outcome: every kept test passes (40 at review); exactly the two named tests are selected by `-m core`; `rg -n "AntiForkTests|ContractConsistencyTests|import inspect|inspect\.signature|agent_workflows\" / \"|plan-review\.md" tests/test_plan_readiness_recheck.py` returns nothing (the file's other `read_text` calls read plans written into its own temporary repos and are behavior, so `read_text` is not a usable marker).
  - Execution state: performed

- [x] E-05 Restore `tests/test_gate_answer_wiring.py`, deleting `test_the_refusal_code_has_ONE_definition_shared_by_writer_and_renderer` (its only assertion is `assertIs` between two modules' constants, structure not behavior). Mark `@pytest.mark.core` on exactly `NeedsHumanIsSurfacedAsADecisionRequest.test_it_is_DISTINCT_from_an_ordinary_refusal_line` (reaches `gate_answer_needs_human_remedy`; the file's `TheFailingTestNamesAreCaptured` runs a real pytest subprocess for 2.6s).
  - Depends on: none
  - Expected outcome: every kept test passes (50 at review); exactly the named test is selected by `-m core`.
  - Execution state: performed

### Task group 2: residual assertions

- [x] E-06 Add residual tests asserting values measured at authoring (F-04), each re-measured at execution HEAD first: in `tests/test_rename_ledger.py`, a core-marked `SyntheticKeyTests(unittest.TestCase)` test asserting `record_history._synthetic_key("20260101-foo.bar.md") == "synthetic:foo"`, `_synthetic_key("abc.md") == "synthetic:abc"`, `_synthetic_key("20260101-1200-01-My Plan!.ipd.md") == "synthetic:my-plan"` and `_synthetic_key("20260101-.md") == "synthetic:unknown"`; in `tests/test_selector_resolver_matrix.py`, a test asserting `Resolution(paths=[Path("a")], kind=None, rejected_kind=None, selector="x").is_unique` is True while the same with `paths=[]` and with `paths=[Path("a"), Path("b")]` is False (`is_unique` is a property).
  - Depends on: E-02, E-03
  - Expected outcome: the new tests pass and kill the scratch mutations named in V-06.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): source slicing, `inspect.signature` and cross-module `assertIs` checks are dropped (E-04, E-05).
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): several of these files spawn the CLI or pytest in subprocesses, so they contribute only the cheapest key-reaching tests.
- `cli.py` group 45 carries verdict `property-unidentifiable` (`hpjj44`): no single derived property could be named, so the restored CLI-driving rename tests are the reach, and the early-return sweep (F-04) confirms all three keys are guarded by them.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` | Reaching files per key: `_synthetic_key` -> `test_artifact_rename.py`, `test_rename_ledger.py`; `read_renames_for` -> `test_rename_ledger.py`; `is_legal_edge` -> `test_migration_complex.py`, `test_run_state_engine.py`; `cli.py` keys -> `test_artifact_group.py`, `test_artifact_rename.py`, `test_cli_help_and_errors.py`, `test_help_token.py`; `plan_set_priority` -> `test_research_priority.py`; `gate_answer_needs_human_remedy` -> `test_gate_answer_wiring.py`; `plan_reference_rewrites`, `_rp_type_facet` -> `test_reference_matcher_parity.py`; `is_unique` -> `test_selector_resolver_matrix.py`, `test_selector_resolver_parity.py`; `holding` -> `test_plan_readiness_recheck.py`; `run_state` -> `test_run_state_engine.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26` | All `pass` except `test_plan_readiness_recheck.py`: 46 passed, 1 failed, `test_an_unresolved_selector_exits_1` `AssertionError: 2 != 1`, the intended `2b9e18bff` change. `test_gate_answer_wiring.py` 51 passed. |
| F-03 | Scratch restore with E-01..E-05, coverage contexts | All 13 keys execute, and each is reached by a core-marked test; this child's core items cost about 0.6 to 0.9s summed CPU. |
| F-04 | Early-return mutation sweep, bool keys both polarities, each reverted | 11 keys killed (explicit-path run of all nine files). Review re-ran the sweep restricted to `-m core`, which is what the goal is defined on: `RecheckResult.holding` -> `()` and `cli._rewrite_help_token` -> `list(argv)` (identity) ALSO survived, fixed by the extra E-04 marker and the E-01 `test_help_token.py` restore. SURVIVED: `_synthetic_key` -> `""` (no test asserts the returned key string), and `Resolution.is_unique` -> True (only the False direction is asserted). Direct calls at HEAD produced the E-06 values. |
| F-05 | Coverage contexts | `test_cli_help_and_errors.py` and `test_selector_resolver_parity.py` add reach only to keys the E-01..E-03 files already reach (`test_help_token.py` also adds only reach, but is the only file that guards `_rewrite_help_token`'s rewrite against an identity mutation, so E-01 restores it); `test_migration_complex.py` is owned by plan `pdemar`. |

## Proposed changes (ordered, validatable)

1. E-01..E-05 restore ten modules with the listed edits and markers.
2. E-06 adds residual assertions for the two surviving keys.

## Deferred / out of scope (with reason)

- `tests/test_cli_help_and_errors.py` and `tests/test_selector_resolver_parity.py` are not restored.
  - Carrier-Declined: no work is owed for this item; F-05 shows every `q86fxm` key they reach is reached by a restored file here.

## Scope check

- Over-scope: none. Test files only; no production code.
- Under-scope: none for the 13 keys (F-03, F-04, E-06).

## Required tests / validation

- `python3 -m pytest <the ten Scope-Paths files> -o addopts="" -v` passes, per-test list pasted.
- Reach: `-m core --cov=agent_workflows.record_history --cov=agent_workflows.run_state --cov=agent_workflows.cli --cov=agent_workflows.research_cmd --cov=agent_workflows.runner_shared --cov=agent_workflows.research_refs --cov=agent_workflows.selectors --cov=agent_workflows.artifact_refs --cov=agent_workflows.plan_readiness --cov=agent_workflows.run_engine --cov-report=json:<scratch>/cov.json` with `COVERAGE_FILE=<scratch>/cov` and `<scratch>` under the gitignored `.aw/state/`; print each of the 13 keys' `files[<module>]["functions"][<key>]["executed_lines"]` count from the JSON (coverage 7.x), every count nonzero (`term-missing` reports lines, not functions). Measured at review: all 13 nonzero under `-m core`. Delete the scratch directory afterwards.
- Mutation spot-checks (scratch, reverted), each run with `-m core` over the ten files: `is_legal_edge` return True, `gate_answer_needs_human_remedy` return `""`, `plan_set_priority` return `()`, `RecheckResult.holding` return `()`, `_rewrite_help_token` return `list(argv)`, plus the two in V-06. Method: insert `return <value>` as the first body statement after the docstring. At review (core only), every key was killed except the four this plan now covers (`_synthetic_key`, `is_unique` True, `holding`, `_rewrite_help_token` identity), and each of those four was shown killed by its added test or marker.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is the readiness-recheck replay failure a regression?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. Commit `2b9e18bff` (backlog `yxsfjc`) deliberately made `aw ipd recheck-readiness` refuse a zero-match selector with exit 2; E-04 updates the expectation. `zhoul7` applies the same correction to `aw reviews decisions`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `-v` runs listing every restored test in the three files PASSED, `-m core --collect-only -q` listing exactly the 4 marked tests, and the core-tier failures under scratch `cli._run_noun_verb` return-`-1` and `cli._rewrite_help_token` return-`list(argv)` mutations (each reverted).
  - Observed evidence:
    All 19 tests in `tests/test_artifact_rename.py`, `tests/test_artifact_group.py`, and `tests/test_help_token.py` passed:
    ```
    tests/test_help_token.py::HelpTokenTests::test_option_value_help_preserved PASSED [  5%]
    tests/test_help_token.py::HelpTokenTests::test_aw_ipd_help_shows_ipd_usage PASSED [ 10%]
    tests/test_help_token.py::HelpTokenTests::test_aw_help_shows_usage PASSED [ 15%]
    tests/test_help_token.py::HelpTokenTests::test_pure_rewrite PASSED       [ 21%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_roadmaps PASSED [ 26%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_specs_legacy_timestamp PASSED [ 31%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_releases PASSED [ 36%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_comms_is_unsupported PASSED [ 42%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_walkthroughs PASSED [ 47%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_backlog_preview_and_apply PASSED [ 52%]
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_prompts PASSED [ 57%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_backlog_preview_and_apply PASSED [ 63%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_roadmaps_injects_set PASSED [ 68%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_releases PASSED [ 73%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_comms_is_unsupported PASSED [ 78%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_walkthroughs_injects_set PASSED [ 84%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_prompts_with_order PASSED [ 89%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_specs_injects_set PASSED [ 94%]
    tests/test_artifact_group.py::TestArtifactGroup::test_group_backlog_metadata_only PASSED [100%]
    ============================== 19 passed in 7.33s ==============================
    ```
    Core collection collected exactly the 4 marked tests:
    ```
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_roadmaps
    tests/test_artifact_rename.py::TestArtifactRename::test_rename_comms_is_unsupported
    tests/test_help_token.py::HelpTokenTests::test_option_value_help_preserved
    tests/test_help_token.py::HelpTokenTests::test_pure_rewrite
    4/19 tests collected (15 deselected) in 1.39s
    ```
    Mutation 1: `cli._run_noun_verb` return `-1` (reverted) killed both core rename tests:
    ```
    FAILED tests/test_artifact_rename.py::TestArtifactRename::test_rename_comms_is_unsupported
    FAILED tests/test_artifact_rename.py::TestArtifactRename::test_rename_roadmaps
    ================== 2 failed, 2 passed, 15 deselected in 5.42s ==================
    ```
    Mutation 2: `cli._rewrite_help_token` return `list(argv)` (reverted) killed `test_pure_rewrite`:
    ```
    FAILED tests/test_help_token.py::HelpTokenTests::test_pure_rewrite - AssertionError: Lists differ: ['help'] != ['--help']
    ================== 1 failed, 3 passed, 15 deselected in 2.33s ==================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` runs listing every restored test PASSED, `-m core --collect-only -q` listing the 3 marked tests, and the failures of those tests under scratch `read_renames_for` return-`[]` and `is_legal_edge` return-True mutations (reverted).
  - Observed evidence:
    All 31 restored tests passed:
    ```
    tests/test_rename_ledger.py::AppendRenameUnitTests::test_malformed_id6_raises PASSED [  3%]
    tests/test_rename_ledger.py::AppendRenameUnitTests::test_write_and_read_back PASSED [  6%]
    tests/test_rename_ledger.py::AppendRenameUnitTests::test_synthetic_key_only_via_case3_path PASSED [  9%]
    tests/test_rename_ledger.py::AppendRenameUnitTests::test_status_reader_and_migration_ignore_rename_keys PASSED [ 12%]
    tests/test_rename_ledger.py::CliEmissionTests::test_applied_plan_rename_appends_one_record PASSED [ 16%]
    tests/test_rename_ledger.py::CliEmissionTests::test_dry_run_appends_nothing PASSED [ 19%]
    tests/test_rename_ledger.py::RecordRenameCaseTests::test_noop_records_nothing PASSED [ 22%]
    tests/test_rename_ledger.py::RecordRenameCaseTests::test_case1_id6_to_id6 PASSED [ 25%]
    tests/test_rename_ledger.py::RecordRenameCaseTests::test_case3_both_id6less_synthetic_key PASSED [ 29%]
    tests/test_rename_ledger.py::RecordRenameCaseTests::test_additivity_unwritable_ledger_does_not_raise PASSED [ 32%]
    tests/test_rename_ledger.py::RecordRenameCaseTests::test_case2_id6less_to_id6_keys_on_new_id6 PASSED [ 35%]
    tests/test_rename_ledger.py::RecordRenameCaseTests::test_multi_rename_history_accumulates PASSED [ 38%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_executor_cannot_author_verifier_transitions PASSED [ 41%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_exhaustive_state_actor_matrix PASSED [ 45%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_missing_predicate_fails_closed PASSED [ 48%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_executor_cannot_author_terminal_completion PASSED [ 51%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_all_states_and_roles_defined PASSED [ 54%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_legal_transitions_with_authorized_actors PASSED [ 58%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_executor_cannot_cancel_run PASSED [ 61%]
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_unlisted_and_backward_transitions_rejected PASSED [ 64%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_concurrent_coordinators_cannot_both_act_simultaneously PASSED [ 67%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_cancellation_from_multiple_states PASSED [ 70%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_full_lifecycle_and_completion_enforcement PASSED [ 74%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_torn_or_corrupt_ledger_fails_closed PASSED [ 77%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_incomplete_predicates_reject_completion PASSED [ 80%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_lock_loss_fails_closed PASSED [ 83%]
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_broken_hash_chain_fails_closed PASSED [ 87%]
    tests/test_run_state_engine.py::TestRunEngineDAGScheduling::test_gate_approval_blocks_step_until_approved PASSED [ 90%]
    tests/test_run_state_engine.py::TestRunEngineDAGScheduling::test_failed_or_blocked_step_stops_downstream_dag PASSED [ 93%]
    tests/test_run_state_engine.py::TestRunEngineDAGScheduling::test_dag_progression_releases_dependent_steps PASSED [ 96%]
    tests/test_run_state_engine.py::TestRunEngineDAGScheduling::test_initial_state_only_root_step_runnable PASSED [100%]
    ============================== 31 passed in 3.84s ==============================
    ```
    Core collection listed exactly the 3 marked tests:
    ```
    tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_exhaustive_state_actor_matrix
    tests/test_run_state_engine.py::TestRunEngineConcurrencyAndIntegrity::test_cancellation_from_multiple_states
    tests/test_rename_ledger.py::AppendRenameUnitTests::test_synthetic_key_only_via_case3_path
    3/31 tests collected (28 deselected) in 3.38s
    ```
    Mutation 1: `record_history.read_renames_for` return `[]` (reverted) killed `test_synthetic_key_only_via_case3_path`:
    ```
    FAILED tests/test_rename_ledger.py::AppendRenameUnitTests::test_synthetic_key_only_via_case3_path
    AssertionError: 0 != 1
    ================== 1 failed, 2 passed, 28 deselected in 0.41s ==================
    ```
    Mutation 2: `run_state.is_legal_edge` return `True` (reverted) killed `test_exhaustive_state_actor_matrix`:
    ```
    FAILED tests/test_run_state_engine.py::TestRunStateMachineTransitionTable::test_exhaustive_state_actor_matrix
    AssertionError: unexpectedly None
    ================== 1 failed, 2 passed, 28 deselected in 0.41s ==================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` runs listing every restored test PASSED and the failures from scratch `plan_set_priority` return-`()` and `plan_reference_rewrites` return-`[]` mutations (reverted).
  - Observed evidence:
    All 36 restored tests in the three files passed:
    ```
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_match_selector_status_now_supported PASSED [  2%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_find_target_record_no_match PASSED [  5%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_find_target_record_all_unique_kinds PASSED [  8%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_resolve_one_exact_kinds PASSED [ 11%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_match_selector_path_id_set_substring PASSED [ 13%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_find_target_record_returns_single_for_multi PASSED [ 16%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_match_selector_stem_via_substring PASSED [ 19%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_resolve_one_path_kind_no_match PASSED [ 22%]
    tests/test_selector_resolver_matrix.py::ResolverMatrixTests::test_resolve_one_stem_and_substring PASSED [ 25%]
    tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests::test_review_record_is_still_resolvable_as_its_own_type PASSED [ 27%]
    tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests::test_bare_id6_is_unambiguous_across_types PASSED [ 30%]
    tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests::test_reviews_is_not_swept_into_other PASSED [ 33%]
    tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests::test_reviews_has_no_status_lifecycle PASSED [ 36%]
    tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests::test_other_still_owns_a_genuinely_unowned_tree PASSED [ 38%]
    tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests::test_the_three_dir_sets_are_disjoint PASSED [ 41%]
    tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_result_shape_unique_and_ambiguous PASSED [ 44%]
    tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_denied_kind_is_clear_rejection_not_silent PASSED [ 47%]
    tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_exact_kinds_are_exact_not_substring PASSED [ 50%]
    tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_no_match_is_empty_not_rejection PASSED [ 52%]
    tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_precedence_and_kinds PASSED [ 55%]
    tests/test_reference_matcher_parity.py::DanglingConsistencyTests::test_id6_handles_recognized_uniformly PASSED [ 58%]
    tests/test_reference_matcher_parity.py::ResearchFixAndStabilityTests::test_id6_handle_and_setid_never_rewritten PASSED [ 61%]
    tests/test_reference_matcher_parity.py::ResearchFixAndStabilityTests::test_research_rename_rewrites_full_and_bare_stem PASSED [ 63%]
    tests/test_reference_matcher_parity.py::DeadFilenamePrimitiveTests::test_cross_type_research_name_not_flagged_for_plans PASSED [ 66%]
    tests/test_reference_matcher_parity.py::DeadFilenamePrimitiveTests::test_flags_only_the_truly_dead_type_appropriate_name PASSED [ 69%]
    tests/test_research_priority.py::ResearchPriorityIndexTests::test_index_priority_empty_when_absent PASSED [ 72%]
    tests/test_research_priority.py::ResearchPriorityIndexTests::test_index_carries_priority PASSED [ 75%]
    tests/test_research_priority.py::ResearchPriorityContractTests::test_priority_not_in_required_fields PASSED [ 77%]
    tests/test_research_priority.py::ResearchPriorityContractTests::test_valid_priority_conforms PASSED [ 80%]
    tests/test_research_priority.py::ResearchPriorityContractTests::test_absent_priority_conforms PASSED [ 83%]
    tests/test_research_priority.py::ResearchPriorityContractTests::test_out_of_vocab_priority_flagged PASSED [ 86%]
    tests/test_research_priority.py::ResearchPriorityNewAndSetTests::test_plan_set_priority_rejects_out_of_vocab PASSED [ 88%]
    tests/test_research_priority.py::ResearchPriorityNewAndSetTests::test_new_emits_priority_line_only_when_given PASSED [ 91%]
    tests/test_research_priority.py::ResearchPriorityNewAndSetTests::test_new_rejects_out_of_vocab_priority PASSED [ 94%]
    tests/test_research_priority.py::ResearchPriorityNewAndSetTests::test_set_priority_writes_inserts_and_clears PASSED [ 97%]
    tests/test_research_priority.py::ResearchPriorityAttentionTests::test_research_record_populates_priority PASSED [100%]
    ============================== 36 passed in 0.85s ==============================
    ```
    Mutation 1: `research_cmd.plan_set_priority` return `()` (reverted) killed `test_plan_set_priority_rejects_out_of_vocab`:
    ```
    FAILED tests/test_research_priority.py::ResearchPriorityNewAndSetTests::test_plan_set_priority_rejects_out_of_vocab
    ValueError: not enough values to unpack (expected 3, got 0)
    ========================= 1 failed, 35 passed in 1.72s =========================
    ```
    Mutation 2: `research_refs.plan_reference_rewrites` return `[]` (reverted) killed `test_research_rename_rewrites_full_and_bare_stem`:
    ```
    FAILED tests/test_reference_matcher_parity.py::ResearchFixAndStabilityTests::test_research_rename_rewrites_full_and_bare_stem
    AssertionError: '20260101-demo-02-abc123-topic.gpt56.findings.md' not found
    ========================= 1 failed, 35 passed in 1.20s =========================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a diff against `19313eed^` showing only the two removed classes and one removed test, the exit-2 rename, the two markers and the docstring; paste the `-v` run listing every kept test PASSED, `-m core --collect-only -q` naming the two marked tests, the empty `rg` output, and the `-m core` failure of `test_a_blocking_question_holds_only_the_question_condition` under a scratch `RecheckResult.holding` return-`()` mutation (reverted).
  - Observed evidence:
    Diff against `19313eed^:tests/test_plan_readiness_recheck.py`:
    ```diff
    --- a/tests/test_plan_readiness_recheck.py
    +++ b/tests/test_plan_readiness_recheck.py
    @@ -1,4 +1,8 @@
    -"""Tests for rdyrecheck Order 01 (plan `qhy3i3`): the readiness RE-CHECK and the escalation return path.
    +"""
    +Restored for backlog q86fxm (findings b1mx2w) from 19313eed^.
    +Source-slicing anti-fork tests, workflow markdown contract consistency tests, and
    +the parameter signature pin were deliberately not restored as code-pinning / structure-only tests.
    +Tests for rdyrecheck Order 01 (plan `qhy3i3`): the readiness RE-CHECK and the escalation return path.
    @@ -35,6 +39,7 @@
     import tempfile
     import unittest
    +import pytest
     from pathlib import Path
    @@ -190,6 +195,7 @@

    +    @pytest.mark.core
         def test_a_blocking_question_holds_only_the_question_condition(self) -> None:
    @@ -227,6 +233,7 @@

    +    @pytest.mark.core
         def test_a_NON_blocking_open_question_does_not_hold_the_condition(self) -> None:
    @@ -246,36 +253,6 @@
    -class AntiForkTests(unittest.TestCase):
    -...
    @@ -309,24 +286,6 @@
    -    def test_go_is_UNREACHABLE_because_the_target_is_not_a_parameter(self) -> None:
    -...
    @@ -755,7 +714,7 @@
    -    def test_an_unresolved_selector_exits_1(self) -> None:
    +    def test_an_unresolved_selector_exits_2(self) -> None:
             r = _aw(
                 "ipd",
                 "recheck-readiness",
                 "zzzzzz",
                 "--dir",
                 str(self.repo),
                 cwd=self.repo,
             )
    -        self.assertEqual(r.returncode, 1, r.stdout)
    +        self.assertEqual(r.returncode, 2, r.stdout)
    @@ -875,43 +834,5 @@
    -class ContractConsistencyTests(unittest.TestCase):
    -...
    ```
    All 40 kept tests passed:
    ```
    tests/test_plan_readiness_recheck.py::WiringTests::test_the_verb_is_in_the_ipd_parser PASSED [  2%]
    tests/test_plan_readiness_recheck.py::WiringTests::test_the_verb_is_DECLARED_in_the_command_inventory PASSED [  5%]
    tests/test_plan_readiness_recheck.py::WiringTests::test_the_verb_appears_in_generated_completion_for_every_shell PASSED [  7%]
    tests/test_plan_readiness_recheck.py::WiringTests::test_the_verbs_flags_appear_in_completion PASSED [ 10%]
    tests/test_plan_readiness_recheck.py::WriteTargetIsPinnedTests::test_the_only_permitted_write_is_no_go_to_go_pending_approval PASSED [ 12%]
    tests/test_plan_readiness_recheck.py::WriteTargetIsPinnedTests::test_the_internal_assertion_itself_refuses_a_widened_target PASSED [ 15%]
    tests/test_plan_readiness_recheck.py::WriteTargetIsPinnedTests::test_the_pin_FAILS_against_a_deliberately_widened_writer PASSED [ 17%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_apply_writes_exactly_the_readiness_line_and_one_history_record PASSED [ 20%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_agent_mode_emits_a_parsable_record PASSED [ 22%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_stale_findings_dry_run_writes_nothing PASSED [ 25%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_an_unresolved_selector_exits_2 PASSED [ 27%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_stale_findings_apply_appends_the_round_and_then_clears PASSED [ 30%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_the_sweep_default_covers_pending_and_reusable_only PASSED [ 32%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_a_refusal_exits_0_and_names_the_cause PASSED [ 35%]
    tests/test_plan_readiness_recheck.py::CliVerbTests::test_dry_run_is_the_DEFAULT_and_writes_nothing PASSED [ 37%]
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_blocking_question_holds_only_the_question_condition PASSED [ 40%]
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_an_unidentifiable_plan_fails_CLOSED_on_the_finding_condition PASSED [ 42%]
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_clean_plan_holds_nothing_and_may_write PASSED [ 45%]
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_NON_blocking_open_question_does_not_hold_the_condition PASSED [ 47%]
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_gating_finding_holds_only_the_finding_condition PASSED [ 50%]
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_negative_prose_verdict_holds_only_the_verdict_condition PASSED [ 52%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_a_question_naming_a_DIFFERENT_finding_does_not_clear_this_one PASSED [ 55%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_the_appended_round_marks_it_fixed_and_CITES_the_question PASSED [ 57%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_a_MALFORMED_review_record_is_never_amended PASSED [ 60%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_the_finding_BLOCKS_before_and_is_EMPTY_after PASSED [ 62%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_the_NEGATIVE_case_an_OPEN_question_leaves_its_finding_blocking PASSED [ 65%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_a_still_unresolved_SIBLING_finding_is_CARRIED_FORWARD PASSED [ 67%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_a_question_with_NO_finding_reference_clears_nothing PASSED [ 70%]
    tests/test_plan_readiness_recheck.py::StaleEscalationTests::test_the_recheck_CLEARS_once_the_stale_finding_is_closed PASSED [ 72%]
    tests/test_plan_readiness_recheck.py::RefusalTests::test_an_OUT_OF_VOCAB_readiness_field_is_refused PASSED [ 75%]
    tests/test_plan_readiness_recheck.py::RefusalTests::test_a_held_condition_refuses_and_NAMES_the_surviving_cause PASSED [ 77%]
    tests/test_plan_readiness_recheck.py::RefusalTests::test_an_ALREADY_APPROVABLE_readiness_is_refused PASSED [ 80%]
    tests/test_plan_readiness_recheck.py::RefusalTests::test_an_unreadable_plan_refuses_instead_of_raising PASSED [ 82%]
    tests/test_plan_readiness_recheck.py::RefusalTests::test_an_ABSENT_readiness_field_is_refused_rather_than_MINTED PASSED [ 85%]
    tests/test_plan_readiness_recheck.py::HistoryEntryIsNotAVerdictTests::test_the_entry_is_PREPENDED_so_it_is_the_newest PASSED [ 87%]
    tests/test_plan_readiness_recheck.py::HistoryEntryIsNotAVerdictTests::test_the_entry_states_NO_review_verdict_token PASSED [ 90%]
    tests/test_plan_readiness_recheck.py::HistoryEntryIsNotAVerdictTests::test_newest_verdict_still_resolves_to_the_REVIEW_after_the_recheck PASSED [ 92%]
    tests/test_plan_readiness_recheck.py::HistoryEntryIsNotAVerdictTests::test_the_entry_names_the_three_conditions_and_cites_the_review PASSED [ 95%]
    tests/test_plan_readiness_recheck.py::HistoryEntryIsNotAVerdictTests::test_the_entry_is_not_classified_as_a_review_record PASSED [ 97%]
    tests/test_plan_readiness_recheck.py::HistoryEntryIsNotAVerdictTests::test_the_review_CITATION_carries_no_verdict_token PASSED [100%]
    ============================== 40 passed in 5.11s ==============================
    ```
    Core collection listed exactly the 2 marked tests:
    ```
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_NON_blocking_open_question_does_not_hold_the_condition
    tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_blocking_question_holds_only_the_question_condition
    2/40 tests collected (38 deselected) in 0.22s
    ```
    The `rg` check returned nothing (exit 1):
    ```sh
    rg -n "AntiForkTests|ContractConsistencyTests|import inspect|inspect\.signature|agent_workflows\" / \"|plan-review\.md" tests/test_plan_readiness_recheck.py
    # (empty, exit 1)
    ```
    Mutation: `RecheckResult.holding` return `()` (reverted) killed `test_a_blocking_question_holds_only_the_question_condition`:
    ```
    FAILED tests/test_plan_readiness_recheck.py::ConditionsAreReportedIndividuallyTests::test_a_blocking_question_holds_only_the_question_condition
    AssertionError: Items in the second set but not the first:
    'unresolved-blocking-question' : ('an unresolved BLOCKING open question remains (OQ-01: does the escalated finding still stop execution?); `has_unresolved_blocking_question` -> True',)
    ================== 1 failed, 1 passed, 38 deselected in 0.31s ==================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `-v` run listing every kept test PASSED, `-m core --collect-only -q` naming the one marked test, and its failure under a scratch `gate_answer_needs_human_remedy` return-`""` mutation (reverted).
  - Observed evidence:
    All 50 kept tests in `tests/test_gate_answer_wiring.py` passed:
    ```
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_needs_human_REFUSES_and_is_marked_as_awaiting_a_DECISION PASSED [  2%]
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_SILENCE_refuses PASSED [  4%]
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_a_REASONLESS_not_mine_refuses PASSED [  6%]
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_a_release_is_recorded_as_integrating_and_a_refusal_is_not PASSED [  8%]
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_mine_REFUSES_and_there_is_no_override PASSED [ 10%]
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_an_UNKNOWN_TOKEN_refuses_and_is_refused_BY_NAME PASSED [ 12%]
    tests/test_gate_answer_wiring.py::OnlyNotMineReleases::test_not_mine_with_a_reason_RELEASES PASSED [ 14%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_a_PASSING_rerun_is_what_releases_and_not_the_claim PASSED [ 16%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_a_fixed_claim_that_fails_then_succeeds_on_a_FURTHER_attempt_integrates PASSED [ 18%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_a_fixed_claim_whose_RERUN_PASSES_integrates PASSED [ 20%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_a_fixed_claim_that_NEVER_passes_refuses_with_the_lane_preserved PASSED [ 22%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_a_budget_of_ZERO_never_verifies_and_therefore_refuses PASSED [ 24%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_the_rerun_count_NEVER_exceeds_the_resolved_retry_budget PASSED [ 26%]
    tests/test_gate_answer_wiring.py::AFixedClaimIsVerifiedByTheSuite::test_the_budget_comes_from_the_runs_FROZEN_value PASSED [ 28%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_a_review_turn_is_never_asked PASSED [ 30%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_no_trust_signal_at_all_is_not_asked_about PASSED [ 32%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_a_verifier_DECLINE_is_never_answerable_away_by_the_agent_it_judged PASSED [ 34%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_it_is_bounded_at_exactly_one_ask_per_attempt PASSED [ 36%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_a_turn_with_no_resumable_session_is_not_asked PASSED [ 38%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_an_EARNED_integration_is_not_asked_about PASSED [ 40%]
    tests/test_gate_answer_wiring.py::OnlyTheSuiteRefusalIsAskable::test_a_suite_failure_refusal_IS_asked_about PASSED [ 42%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_the_question_does_not_ACCUSE PASSED [ 44%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_the_question_states_the_CONSEQUENCE_of_each_answer PASSED [ 46%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_the_turn_is_CHARGED_to_the_session_exactly_once PASSED [ 48%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_the_rendered_question_shows_the_failing_tests_and_the_changed_files PASSED [ 50%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_a_MISSING_outcome_file_is_an_observation_and_not_a_crash PASSED [ 52%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_an_isolated_lane_RECOLLECTS_before_re_reading_the_outcome PASSED [ 54%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_the_follow_up_is_ONE_turn_per_answer_and_never_loops PASSED [ 56%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_BOTH_hosts_resume_their_OWN_session_flag PASSED [ 58%]
    tests/test_gate_answer_wiring.py::TheQuestionCarriesTheEvidenceItNeeds::test_a_FAILING_recollect_does_not_kill_the_turn PASSED [ 60%]
    tests/test_gate_answer_wiring.py::NeedsHumanIsSurfacedAsADecisionRequest::test_the_remedy_says_DECIDE_rather_than_RERUN PASSED [ 62%]
    tests/test_gate_answer_wiring.py::NeedsHumanIsSurfacedAsADecisionRequest::test_the_item_and_the_requested_decision_appear_in_the_operator_output PASSED [ 64%]
    tests/test_gate_answer_wiring.py::NeedsHumanIsSurfacedAsADecisionRequest::test_it_is_DISTINCT_from_an_ordinary_refusal_line PASSED [ 66%]
    tests/test_gate_answer_wiring.py::NeedsHumanIsSurfacedAsADecisionRequest::test_a_run_with_NO_such_answer_gains_no_spurious_line PASSED [ 68%]
    tests/test_gate_answer_wiring.py::TheGateItselfStaysHard::test_integration_is_earned_still_refuses_a_failing_suite PASSED [ 70%]
    tests/test_gate_answer_wiring.py::TheGateItselfStaysHard::test_integration_is_earned_still_refuses_a_declined_verifier PASSED [ 72%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_the_new_field_carries_the_actual_node_ids PASSED [ 74%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_duplicate_lines_are_collapsed PASSED [ 76%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_the_field_is_DEFAULTED_so_existing_construction_sites_are_unchanged PASSED [ 78%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_a_real_run_populates_the_field_and_the_summary_stays_a_count PASSED [ 80%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_failing_text_never_renders_an_empty_section_into_the_prompt PASSED [ 82%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_the_OLD_behavior_yields_only_a_count_line PASSED [ 84%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_the_line_count_is_capped_so_one_bad_suite_cannot_crowd_out_the_question PASSED [ 86%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_a_count_only_field_would_FAIL_this_item PASSED [ 88%]
    tests/test_gate_answer_wiring.py::TheFailingTestNamesAreCaptured::test_a_COLLECTION_ERROR_is_captured_too PASSED [ 90%]
    tests/test_gate_answer_wiring.py::TheAnswerIsDurableAndAttributable::test_the_failing_tests_the_answer_was_given_ABOUT_are_recorded PASSED [ 92%]
    tests/test_gate_answer_wiring.py::TheAnswerIsDurableAndAttributable::test_ASKED_AND_SILENT_is_distinguishable_from_NEVER_ASKED PASSED [ 94%]
    tests/test_gate_answer_wiring.py::TheAnswerIsDurableAndAttributable::test_the_rerun_outcome_is_recorded_beside_the_claim PASSED [ 96%]
    tests/test_gate_answer_wiring.py::TheAnswerIsDurableAndAttributable::test_the_record_is_json_serializable PASSED [ 98%]
    tests/test_gate_answer_wiring.py::TheAnswerIsDurableAndAttributable::test_a_reader_can_identify_WHO_claimed_not_mine_and_WHY PASSED [100%]
    ============================== 50 passed in 2.77s ==============================
    ```
    Core collection listed exactly the 1 marked test:
    ```
    tests/test_gate_answer_wiring.py::NeedsHumanIsSurfacedAsADecisionRequest::test_it_is_DISTINCT_from_an_ordinary_refusal_line
    1/50 tests collected (49 deselected) in 0.47s
    ```
    Mutation: `runner_shared.gate_answer_needs_human_remedy` return `""` (reverted) killed the core test:
    ```
    FAILED tests/test_gate_answer_wiring.py::NeedsHumanIsSurfacedAsADecisionRequest::test_it_is_DISTINCT_from_an_ordinary_refusal_line
    ValueError: Refusal.remedy must be a non-empty string (got ''); a refusal that cannot say what happened or what to do next is incomplete by construction
    ======================= 1 failed, 49 deselected in 1.38s =======================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `-v` lines for the two residual tests PASSED; paste the failures from scratch `_synthetic_key` return-`""` and `Resolution.is_unique` return-True mutations (reverted); paste the per-key reach listing from Required tests (13 keys, each nonzero), the bare `python3 -m pytest` summary line (within the 30s core budget; 796 passed in 28.41s at review with this plan's core tests present), `aw sanitize --agent` with no `fail`, a final empty `git diff agent_workflows/`, and `git status --short` showing no `.coverage` or other scratch file.
  - Observed evidence:
    The two residual tests passed:
    ```
    tests/test_rename_ledger.py::SyntheticKeyTests::test_synthetic_key_deterministic_derivation PASSED [ 50%]
    tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_resolution_is_unique_property PASSED [100%]
    ============================== 2 passed in 0.25s ===============================
    ```
    Mutation 1: `record_history._synthetic_key` return `""` (reverted) killed `test_synthetic_key_deterministic_derivation`:
    ```
    FAILED tests/test_rename_ledger.py::SyntheticKeyTests::test_synthetic_key_deterministic_derivation
    AssertionError: '' != 'synthetic:foo'
    + synthetic:foo
    ================== 1 failed, 1 passed, 11 deselected in 0.25s ==================
    ```
    Mutation 2: `selectors.Resolution.is_unique` return `True` (reverted) killed `test_resolution_is_unique_property`:
    ```
    FAILED tests/test_selector_resolver_matrix.py::UnifiedResolveTests::test_resolution_is_unique_property
    AssertionError: True is not false
    ========================= 1 failed, 20 passed in 0.48s =========================
    ```
    Per-key reach listing (all 13 keys, each nonzero):
    ```
    === 13 KEYS REACH CHECK ===
    agent_workflows/record_history.py :: _synthetic_key -> executed_lines count: 5 (nonzero=True)
    agent_workflows/record_history.py :: read_renames_for -> executed_lines count: 1 (nonzero=True)
    agent_workflows/run_state.py :: is_legal_edge -> executed_lines count: 4 (nonzero=True)
    agent_workflows/cli.py :: _nv_resolve_types -> executed_lines count: 10 (nonzero=True)
    agent_workflows/cli.py :: _rewrite_help_token -> executed_lines count: 9 (nonzero=True)
    agent_workflows/cli.py :: _run_noun_verb -> executed_lines count: 38 (nonzero=True)
    agent_workflows/research_cmd.py :: plan_set_priority -> executed_lines count: 5 (nonzero=True)
    agent_workflows/runner_shared.py :: gate_answer_needs_human_remedy -> executed_lines count: 2 (nonzero=True)
    agent_workflows/research_refs.py :: plan_reference_rewrites -> executed_lines count: 2 (nonzero=True)
    agent_workflows/selectors.py :: Resolution.is_unique -> executed_lines count: 1 (nonzero=True)
    agent_workflows/artifact_refs.py :: _rp_type_facet -> executed_lines count: 1 (nonzero=True)
    agent_workflows/plan_readiness.py :: RecheckResult.holding -> executed_lines count: 1 (nonzero=True)
    agent_workflows/run_engine.py :: RunEngine.run_state -> executed_lines count: 1 (nonzero=True)
    ```
    Suite run (`aw suite`):
    ```
    1041 passed in 35.09s
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ```
    `aw sanitize --agent` result:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5882,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    Final git diff on `agent_workflows/` is empty:
    ```sh
    git diff agent_workflows/
    # (empty)
    ```
    Final `git status --short` has no scratch files:
    ```
    ?? tests/test_artifact_group.py
    ?? tests/test_artifact_rename.py
    ?? tests/test_gate_answer_wiring.py
    ?? tests/test_help_token.py
    ?? tests/test_plan_readiness_recheck.py
    ?? tests/test_reference_matcher_parity.py
    ?? tests/test_rename_ledger.py
    ?? tests/test_research_priority.py
    ?? tests/test_run_state_engine.py
    ?? tests/test_selector_resolver_matrix.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Scope fence: the ten Scope-Paths test files are the only declared paths. An out-of-scope edit (for example a gated `bug` backlog item filed under the disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch production edits that must be reverted and must be absent from the diff; scratch coverage files live under the gitignored `.aw/state/` and are deleted.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit 9gjvrq -- <the ten Scope-Paths files>` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize 9gjvrq` instead. Never hand-`git mv` the plan.
