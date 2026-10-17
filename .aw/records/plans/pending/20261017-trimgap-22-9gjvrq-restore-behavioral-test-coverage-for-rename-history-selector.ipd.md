# IPD: Restore behavioral test coverage for rename history, selectors, readiness recheck, gate answers and run state

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the remaining small groups: 37 (`record_history.py`, 2 keys), 44 (`run_state.py`, 1), 45 (`cli.py`, 3 keys, verdict `property-unidentifiable`), 46 (`research_cmd.py`, 1), 49 (`runner_shared.py`, 1), 52 (`research_refs.py`, 1), 55 (`selectors.py`, 1), 57 (`artifact_refs.py`, 1), 59 (`plan_readiness.py`, 1) and 60 (`run_engine.py`, 1), 13 keys in all.
- Scope: Restore ten deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, with `core` markers on the cheapest tests reaching each key, and add residual tests for the two keys whose wrong value no restored test detects (`record_history._synthetic_key`, the `True` polarity of `Resolution.is_unique`, F-04). Review added `tests/test_help_token.py` (guards `_rewrite_help_token` against an identity mutation), a second core marker for `RecheckResult.holding`, and removal of the document-text `ContractConsistencyTests` class (F-04, E-01, E-04). The 13 keys: `record_history._synthetic_key`, `read_renames_for`; `run_state.is_legal_edge`; `cli._nv_resolve_types`, `_rewrite_help_token`, `_run_noun_verb`; `research_cmd.plan_set_priority`; `runner_shared.gate_answer_needs_human_remedy`; `research_refs.plan_reference_rewrites`; `selectors.Resolution.is_unique`; `artifact_refs._rp_type_facet`; `plan_readiness.RecheckResult.holding`; `run_engine.RunEngine.run_state`. EXCLUDES any production change; EXCLUDES `tests/test_cli_help_and_errors.py` and `tests/test_selector_resolver_parity.py` (F-05).
- Scope-Paths: tests/test_help_token.py, tests/test_artifact_rename.py, tests/test_artifact_group.py, tests/test_rename_ledger.py, tests/test_research_priority.py, tests/test_reference_matcher_parity.py, tests/test_selector_resolver_matrix.py, tests/test_plan_readiness_recheck.py, tests/test_gate_answer_wiring.py, tests/test_run_state_engine.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 22
- Highest E allocated: 06
- Author: opencode
- Id: 9gjvrq

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach via coverage contexts, per-test durations, and an early-return mutation sweep over the 13 keys (both polarities for boolean keys); scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 13 keys reached by the routine bare core-tier run through restored behavioral tests that rename and regroup artifacts through the CLI, append and read the rename ledger, resolve selectors, plan reference rewrites, recheck plan readiness, render gate-answer remedies, and drive the run state machine, asserting on exit codes, written files and returned records. Done means an early-return mutation of any of the 13 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for E-01..E-05: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. Disposition rule if a kept test fails at execution HEAD: do not mark the item performed until it is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue. Insert `pytestmark = pytest.mark.core` AFTER the last complete top-level import statement (several files end their imports with a parenthesized multi-line `from agent_workflows import (...)`).

### Task group 1: restore the modules

- [ ] E-01 Restore `tests/test_artifact_rename.py` and `tests/test_artifact_group.py` unchanged, with `@pytest.mark.core` on exactly `TestArtifactRename.test_rename_comms_is_unsupported` and `TestArtifactRename.test_rename_roadmaps` (they reach `_synthetic_key` and the three `cli.py` noun-verb keys for 0.27 to 0.33s; `tests/test_artifact_group.py` stays wholly in the explicit-path tier as an additional reach of `_nv_resolve_types` and `_run_noun_verb`). Also restore `tests/test_help_token.py` unchanged with `@pytest.mark.core` on exactly `HelpTokenTests.test_pure_rewrite` and `HelpTokenTests.test_option_value_help_preserved` (pure function calls, under 0.01s): the rename tests reach `_rewrite_help_token` but only a `return None` or `return []` mutation fails them, while an identity mutation (`return list(argv)`, "never rewrite `help`") passes the whole nine-file set and is killed only by `test_pure_rewrite` (measured at review).
  - Depends on: none
  - Expected outcome: every restored test in the three files passes and exactly the four named tests are selected by `-m core` (7, 8 and 4 tests at review; the counts are context, not the bar).
  - Execution state: pending

- [ ] E-02 Restore `tests/test_rename_ledger.py` with `@pytest.mark.core` on exactly `AppendRenameUnitTests.test_synthetic_key_only_via_case3_path` (reaches `read_renames_for`; the file's `CliEmissionTests` cost 2.4s), and `tests/test_run_state_engine.py` with `@pytest.mark.core` on exactly `TestRunStateMachineTransitionTable.test_exhaustive_state_actor_matrix` and `TestRunEngineConcurrencyAndIntegrity.test_cancellation_from_multiple_states` (reach `is_legal_edge` and `RunEngine.run_state`).
  - Depends on: none
  - Expected outcome: every restored test passes and exactly the three named tests are selected by `-m core` (12 and 19 tests at review).
  - Execution state: pending

- [ ] E-03 Restore `tests/test_research_priority.py`, `tests/test_reference_matcher_parity.py` and `tests/test_selector_resolver_matrix.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each (11, 5 and 20 tests; under 0.3s summed).
  - Depends on: none
  - Expected outcome: every restored test passes and all are core-selected (11, 5 and 20 at review).
  - Execution state: pending

- [ ] E-04 Restore `tests/test_plan_readiness_recheck.py`, deleting the whole `AntiForkTests` class (its own docstring says it is "Asserted against the module SOURCE rather than by behavior": `test_the_recheck_calls_all_three_shipped_predicates` and `test_the_recheck_does_not_reimplement_the_open_question_parser` slice `plan_readiness.py` and `review_findings.py` source) and `WriteTargetIsPinnedTests.test_go_is_UNREACHABLE_because_the_target_is_not_a_parameter` (asserts on `inspect.signature`), and the whole `ContractConsistencyTests` class (its `setUp` reads `.aw/system/workflows/plan-review/plan-review.md` and its four tests assert that specific wording remains in that document, which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" item (3) forbids; sibling `8bhcd3` drops docstring-text tests on the same ground). Update `CliVerbTests.test_an_unresolved_selector_exits_1` for the intended change made by commit `2b9e18bff` ("selquiet: make reviews decisions, record-history, graduation and ipd recheck-readiness refuse zero-match selector with exit 2 (yxsfjc)"): assert exit 2 and rename it `test_an_unresolved_selector_exits_2`. Mark `@pytest.mark.core` on exactly `ConditionsAreReportedIndividuallyTests.test_a_NON_blocking_open_question_does_not_hold_the_condition` and `ConditionsAreReportedIndividuallyTests.test_a_blocking_question_holds_only_the_question_condition` (both reach `RecheckResult.holding`; the file's subprocess `CliVerbTests` cost 4.8s). The second is required: the first asserts `holding() == ()`, so a `holding` return-`()` mutation passes it and passed the whole core selection at review; the second asserts a non-empty held set and fails under that mutation (0.08s).
  - Depends on: none
  - Expected outcome: every kept test passes (40 at review); exactly the two named tests are selected by `-m core`; `rg -n "AntiForkTests|ContractConsistencyTests|import inspect|inspect\.signature|agent_workflows\" / \"|plan-review\.md" tests/test_plan_readiness_recheck.py` returns nothing (the file's other `read_text` calls read plans written into its own temporary repos and are behavior, so `read_text` is not a usable marker).
  - Execution state: pending

- [ ] E-05 Restore `tests/test_gate_answer_wiring.py`, deleting `test_the_refusal_code_has_ONE_definition_shared_by_writer_and_renderer` (its only assertion is `assertIs` between two modules' constants, structure not behavior). Mark `@pytest.mark.core` on exactly `NeedsHumanIsSurfacedAsADecisionRequest.test_it_is_DISTINCT_from_an_ordinary_refusal_line` (reaches `gate_answer_needs_human_remedy`; the file's `TheFailingTestNamesAreCaptured` runs a real pytest subprocess for 2.6s).
  - Depends on: none
  - Expected outcome: every kept test passes (50 at review); exactly the named test is selected by `-m core`.
  - Execution state: pending

### Task group 2: residual assertions

- [ ] E-06 Add residual tests asserting values measured at authoring (F-04), each re-measured at execution HEAD first: in `tests/test_rename_ledger.py`, a core-marked `SyntheticKeyTests(unittest.TestCase)` test asserting `record_history._synthetic_key("20260101-foo.bar.md") == "synthetic:foo"`, `_synthetic_key("abc.md") == "synthetic:abc"`, `_synthetic_key("20260101-1200-01-My Plan!.ipd.md") == "synthetic:my-plan"` and `_synthetic_key("20260101-.md") == "synthetic:unknown"`; in `tests/test_selector_resolver_matrix.py`, a test asserting `Resolution(paths=[Path("a")], kind=None, rejected_kind=None, selector="x").is_unique` is True while the same with `paths=[]` and with `paths=[Path("a"), Path("b")]` is False (`is_unique` is a property).
  - Depends on: E-02, E-03
  - Expected outcome: the new tests pass and kill the scratch mutations named in V-06.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: paste the `-v` runs listing every restored test in the three files PASSED, `-m core --collect-only -q` listing exactly the 4 marked tests, and the core-tier failures under scratch `cli._run_noun_verb` return-`-1` and `cli._rewrite_help_token` return-`list(argv)` mutations (each reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` runs listing every restored test PASSED, `-m core --collect-only -q` listing the 3 marked tests, and the failures of those tests under scratch `read_renames_for` return-`[]` and `is_legal_edge` return-True mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` runs listing every restored test PASSED and the failures from scratch `plan_set_priority` return-`()` and `plan_reference_rewrites` return-`[]` mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a diff against `19313eed^` showing only the two removed classes and one removed test, the exit-2 rename, the two markers and the docstring; paste the `-v` run listing every kept test PASSED, `-m core --collect-only -q` naming the two marked tests, the empty `rg` output, and the `-m core` failure of `test_a_blocking_question_holds_only_the_question_condition` under a scratch `RecheckResult.holding` return-`()` mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` run listing every kept test PASSED, `-m core --collect-only -q` naming the one marked test, and its failure under a scratch `gate_answer_needs_human_remedy` return-`""` mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `-v` lines for the two residual tests PASSED; paste the failures from scratch `_synthetic_key` return-`""` and `Resolution.is_unique` return-True mutations (reverted); paste the per-key reach listing from Required tests (13 keys, each nonzero), the bare `python3 -m pytest` summary line (within the 30s core budget; 796 passed in 28.41s at review with this plan's core tests present), `aw sanitize --agent` with no `fail`, a final empty `git diff agent_workflows/`, and `git status --short` showing no `.coverage` or other scratch file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Scope fence: the ten Scope-Paths test files are the only declared paths. An out-of-scope edit (for example a gated `bug` backlog item filed under the disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch production edits that must be reverted and must be absent from the diff; scratch coverage files live under the gitignored `.aw/state/` and are deleted.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit 9gjvrq -- <the ten Scope-Paths files>` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize 9gjvrq` instead. Never hand-`git mv` the plan.
