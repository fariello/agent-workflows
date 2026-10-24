# IPD: Restore behavioral test coverage for check_engine review-finding, priority, spec-criteria and plan-disposition keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `lzg859` (Set `trimgap`, group 1 of the `wo21z5` `## Filing plan`) carries 10 `agent_workflows/check_engine.py` keys whose `wo21z5` budget probe never ran (final verdict `budget-exhausted`, "budget exhausted at 11130.81s" / "10845.88s"), so whether the routine suite guards them was unknown. Re-probing all 10 at authoring HEAD `303cd2fd1` against the full routine core selection (`-m core tests/`, F-02) settles it: 5 are now killed (`check_ipd_draft_ready`, `check_review_decision_unescalated`, `check_names`, `check_release_gate_consistency`, `_iter_type_files`) and 5 SURVIVE (`check_plan_priority_required`, `check_spec_criteria_uncovered`, `check_review_finding_unescalated`, `evaluate_review_finding_escalation`, `_plan_disposition`). A survivor means a `return-none` mutation of that function passes every core test, so, for example, `aw check` could silently stop reporting unescalated gating review findings, missing Priority/Work-Kind on approved plans, or uncovered spec criteria, and the merge gate would stay green.
- Scope: (1) Restore `tests/test_review_findings_gate.py` from `19313eed^` (minus its source-reading `SourceInvariantTests` class and its live-corpus test), with `@pytest.mark.core` on `GateOutcomeTests` only, which alone kills both review-finding survivors. (2) Add a core-marked `tests/test_check_engine_restored_behavior.py` with direct behavioral tests for `check_plan_priority_required`, `_plan_disposition`, and (thin-guard reinforcement, F-04) `check_ipd_draft_ready`. (3) Add `@pytest.mark.core` to two existing cheap tests in `tests/test_check_engine_spec_criteria.py` that already kill the `check_spec_criteria_uncovered` survivor but are not in the core tier. EXCLUDES any production-code change; EXCLUDES new tests for the other four keys killed at HEAD (F-02, F-04); EXCLUDES restoring `tests/test_bug_gate_default.py`, `tests/test_prompt_id6_filenames.py`, `tests/test_work_commit.py` and `tests/test_check_engine_receipt_liveness.py` wholesale (F-05).
- Scope-Paths: tests/test_review_findings_gate.py, tests/test_check_engine_restored_behavior.py, tests/test_check_engine_spec_criteria.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lzg859
- Set: trimgap
- Order: 27
- Highest E allocated: 05
- Author: opencode
- Id: p79jts
- Approval: 2026-10-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (hand-edit production spot-checks replaced by mutation_probe after a commit step), PR-002 (V-01 rg would match two surviving string references; E-01 rewords them), PR-003 (scope-fence wording, diff checks) fixed; F-03/F-04 reproduced at 49e83b75a (F-06)

- 2026-10-23 to-review (opencode): authored from backlog `lzg859`. Ran `tools/mutation_probe.py` for all 10 keys against `-m core tests/` at HEAD `303cd2fd1` (F-02), probed candidate control files for each survivor (F-03), and prototyped the E-04 direct tests in a scratch file that failed under each key's `return-none` mutant before being deleted (F-04).
- 2026-10-23 draft (opencode): created.

## Goal

Every one of the 10 `lzg859` keys ends with a recorded probe verdict, and each of the 5 that survives the routine core tier at HEAD is guarded by a core-tier behavioral test. Done means a `return-none` mutation of any of those 5 turns a bare `python3 -m pytest` red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the review-findings gate module

- [x] E-01 Create `tests/test_review_findings_gate.py` from `git show 19313eed^:tests/test_review_findings_gate.py`. Remove the whole `SourceInvariantTests` class (it slices production source text and asserts substrings, which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" forbids) and `SubjectFieldIndexTests.test_no_review_record_in_the_tree_carries_the_retired_field` (it reads this repository's live `.aw/records/reviews/` rather than a fixture, so it depends on live state). Remove any import left unused by those deletions. Two surviving strings name the removed live-corpus test as the guard that keeps the retired-field row hypothetical (the `_Case` "a review artifact carrying the RETIRED subject field" rationale, and the `SubjectFieldIndexTests` failure message "keep `test_no_review_record_in_the_tree_carries_the_retired_field` green"); reword each to say that corpus-level guard was not restored (plan `p79jts`, live-state read) instead of pointing at a test that no longer exists. Add a module docstring line naming backlog `lzg859`, findings `wo21z5`, plan `p79jts` and source `19313eed^`. Do NOT add a module-level `pytestmark`; the file stays in the thorough tier except as E-02 marks. Disposition rule if a recovered test fails at execution HEAD: record it in Findings, and if `git log -S` shows an intended behavior change adjust only that expectation and cite the commit; if it is a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it.
  - Depends on: none
  - Expected outcome: the module exists and every remaining test passes under `-o addopts=""` (11 recovered tests passed at authoring before the two removals, F-03).
  - Execution state: performed

- [x] E-02 Decorate the `GateOutcomeTests` class in `tests/test_review_findings_gate.py` with `@pytest.mark.core` (adding `import pytest`). Its single table test calls `check_engine.check_review_finding_unescalated` on isolated `tempfile` repos and asserts per row whether `check.review-finding-unescalated` fires, which path it names, and the `detail`/`required`/`recovery` substrings. It was one of the newly failing tests under BOTH the `check_review_finding_unescalated` and the `evaluate_review_finding_escalation` `return-none` mutants (F-03) and ran in 0.31s.
  - Depends on: E-01
  - Expected outcome: `GateOutcomeTests` is collected by a bare `python3 -m pytest`; the other classes are not.
  - Execution state: performed

### Task group 2: direct behavioral tests for the remaining survivors

- [x] E-03 Create `tests/test_check_engine_restored_behavior.py` with `pytestmark = pytest.mark.core`, a module docstring naming backlog `lzg859`, findings `wo21z5` and plan `p79jts`, and `from tests.test_plan_priority_required import _build_test_plan` as the plan-fixture builder (the existing helper `check_plan_priority_required`'s own unit tests use). Add `test_check_plan_priority_required_reports_only_approved_plans_missing_fields`: in a `tempfile.TemporaryDirectory()` repo with `.aw/records/plans/pending/` and `executed/`, write four pending plans built by `_build_test_plan`: `tst001` `status="approved"` with no Priority/Work-Kind; `tst002` `approved`, `priority="high"`, `work_kind="chore"`; `tst003` `to-review` with neither field; `tst004` `approved` with both set to `grandfathered`. Assert `[(Path(d.location).name, d.rule, d.recovery) for d in ce.check_plan_priority_required(repo)]` equals exactly `[("20260924-testset-01-tst001-a.ipd.md", "check.ipd-priority-required", "aw ipd set tst001 --priority <low|medium|high>"), ("20260924-testset-01-tst001-a.ipd.md", "check.ipd-work-kind-required", "aw ipd set tst001 --work-kind <bug|feature|chore|security|followup>")]` (measured by direct call, F-04).
  - Depends on: none
  - Expected outcome: the module exists, is core-marked, and the test passes.
  - Execution state: performed

- [x] E-04 In `tests/test_check_engine_restored_behavior.py` add two more tests. (a) `test_plan_disposition_is_the_first_component_under_the_plans_dir`: for each `(rel, expected)` in `("executed/x.ipd.md", "executed")`, `("executed/202608/x.ipd.md", "executed")`, `("superseded/202601/x.ipd.md", "superseded")`, `("not-executed/202608/x.ipd.md", "not-executed")`, `("pending/202608/x.ipd.md", "pending")`, `("z.ipd.md", None)` (a file directly in the plans dir has no disposition), write the file under `<tmp>/.aw/records/plans/<rel>` and assert `ce._plan_disposition(repo, path) == expected`; also assert a file under `<tmp>/not-a-plan-dir/` yields `None`. This mirrors the deleted `test_check_engine_receipt_liveness.test_f_disposition_is_the_first_path_component` and `test_e_missing_plan_location_is_not_live` without their git-subprocess setup. (b) `test_check_ipd_draft_ready_nudges_only_a_finished_pending_draft`: pending `tst001` `draft` with `priority="low"`, `work_kind="chore"`; pending `tst002` `draft` with both `unresolved` (a scaffold placeholder remains); pending `tst003` `to-review`; and `tst004` `draft` placed under `executed/`. Assert `[(Path(d.location).name, d.rule, d.recovery) for d in ce.check_ipd_draft_ready(repo)]` equals exactly `[("20260924-testset-01-tst001-a.ipd.md", "check.ipd-draft-ready-to-review", "aw ipd set to-review tst001")]` (F-04).
  - Depends on: E-03
  - Expected outcome: both tests pass.
  - Execution state: performed

### Task group 3: put the existing spec-criteria guard in the core tier

- [x] E-05 In `tests/test_check_engine_spec_criteria.py`, add `import pytest` and decorate exactly two methods of `CheckEngineSpecCriteriaTests` with `@pytest.mark.core`: `test_clean_fixture_yields_zero_findings_and_exit_code_zero` and `test_positive_control_fires_when_criterion_missing`. Both call `check_engine.check_spec_criteria_uncovered` on a `TemporaryDirectory` fixture with no subprocess, and both were among the 10 newly failing tests under its `return-none` mutant (F-03). Change nothing else in the file. Then, with E-01 through E-05 done, commit the three files through `aw commit p79jts -- tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py` (the Required-tests mutation probes read committed HEAD and cannot see uncommitted tests). If the mutating `ruff --fix`/`ruff-format` pre-commit hook rewrites lines, `aw commit` re-stages and retries; record any hook churn in V-05 rather than editing it by hand.
  - Depends on: E-02, E-04
  - Expected outcome: those two tests are collected by a bare `python3 -m pytest`; the rest of the file is not; the whole file still passes; one commit holds exactly the three Scope-Paths.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block; `GUIDING_PRINCIPLES` P16). That is why E-01 drops `SourceInvariantTests`, which reads `check_engine`/`ipd_lint` source and asserts substrings.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`), under a 30s budget. So a test that kills a mutant but is unmarked does not guard the merge gate, which is exactly the `check_spec_criteria_uncovered` situation (F-03). Mark only the cheapest killing tests core.
- Sibling precedent: `zhoul7` (`trimgap` Order 18) restored deleted modules at original paths with `core` markers on only the cheapest key-reaching tests; `btubm6`/`5jevb2` add one `*_restored_behavior.py` core module per backlog item. No production edits.
- `tools/mutation_probe.py` mutates inside its own disposable worktree at HEAD, so it only sees COMMITTED tests (or `--extra-test COMMIT:PATH` blobs). Mutation checks therefore run AFTER the test commit, through the probe, and never as hand edits of `agent_workflows/` (sibling precedent `a5drqh`, `di5puw`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Budget probe results` rows `agent_workflows/check_engine.py::*`; `## Filing plan` rank 1; `## Filed items` row `lzg859` | All 10 keys: verdict `budget-exhausted`, no survivor/control run recorded. Operator `return-none` for 9, `raise` for `_iter_type_files`. Control files named by the backlog item: `test_doctor_and_marker.py` (restored by `zhoul7` commit `5620a5a13`, after the `wo21z5` baseline `f3afece92`, and covering none of these keys), and `test_bug_gate_default.py`, `test_check_engine_receipt_liveness.py`, `test_prompt_id6_filenames.py`, `test_work_commit.py` (all absent at HEAD). |
| F-02 | `python3 tools/mutation_probe.py --op <op> agent_workflows/check_engine.py::<key> -- -o addopts= -q -p no:randomly -m core -n 4 tests/` at HEAD `303cd2fd1` (first key with `-n 6 -x`) | KILLED: `check_ipd_draft_ready` (2 failing: `test_check_engine.CollisionTests`, `EntryPointTests`), `check_review_decision_unescalated` (13, `test_review_decisions.ReviewDecisionCheckRuleTests` restored by `zhoul7`), `check_names` (25), `check_release_gate_consistency` (1: `test_core_module_coverage::test_hooks_backlog_blocking_close_gate`), `_iter_type_files` `raise` (53). SURVIVED (`mutant_failing: 0`): `check_plan_priority_required` (587s), `check_spec_criteria_uncovered` (581s), `check_review_finding_unescalated` (395s), `evaluate_review_finding_escalation` (445s), `_plan_disposition` (414s). Raw outputs were under the gitignored `.aw/state/lzgprobe/`. |
| F-03 | the same probe tool with a single-file selection (`--extra-test 19313eed:<path>` for deleted files) | `check_review_finding_unescalated` killed by restored `test_review_findings_gate.py` (5 failing, incl. `GateOutcomeTests::test_the_gate_fires_exactly_when_it_should`); `evaluate_review_finding_escalation` killed (6 failing, incl. the same `GateOutcomeTests` test); `check_spec_criteria_uncovered` killed by the EXISTING but unmarked `tests/test_check_engine_spec_criteria.py` (10 failing, incl. `test_clean_fixture_yields_zero_findings_and_exit_code_zero` and `test_positive_control_fires_when_criterion_missing`); `_plan_disposition` killed by restored `test_check_engine_receipt_liveness.py` only via `test_f_disposition_is_the_first_path_component` (1 failing); `check_plan_priority_required` SURVIVED `tests/test_plan_priority_required.py` (0), restored `test_work_commit.py` (0) and restored `test_ipd_priority.py` (`verdict: survived`): no existing or deleted file asserts its output. The deleted `test_review_findings_gate.py` ran `11 passed in 2.41s` at HEAD; `GateOutcomeTests` 0.31s. |
| F-04 | direct calls, and a scratch prototype of E-03/E-04 run with each key monkeypatched to `lambda *a, **k: None` (scratch deleted) | `check_plan_priority_required` returns exactly the two `tst001` drifts quoted in E-03; `_plan_disposition` returns the values quoted in E-04(a); `check_ipd_draft_ready` returns only the `tst001` drift quoted in E-04(b). Prototype: `3 passed in 0.26s`; under each mutant `1 failed, 2 passed`. `check_ipd_draft_ready` is guarded at HEAD only incidentally (two aggregate tests in `test_check_engine.py`), so E-04(b) is cheap direct reinforcement. |
| F-05 | `git show 19313eed^:tests/<f>.py` run with `-o addopts=""` | `test_bug_gate_default.py` 20 passed, `test_prompt_id6_filenames.py` 19 passed, `test_work_commit.py` 14 passed, `test_check_engine_receipt_liveness.py` 17 passed (git subprocess setup). Their keys (`check_release_gate_consistency`, `check_names`) are already killed at HEAD (F-02), `test_work_commit.py` does not kill `check_plan_priority_required` (F-03), and `_plan_disposition`'s one killing test is reproduced without git in E-04(a). Restoring them adds no guard for an `lzg859` key. |
| F-06 | review at HEAD `49e83b75a`: `git show 19313eed^:tests/test_review_findings_gate.py` run from `/tmp` with `-o addopts=""`; `tools/mutation_probe.py --op return-none --extra-test 19313eed:tests/test_review_findings_gate.py agent_workflows/check_engine.py::<K> -- ... tests/test_review_findings_gate.py::GateOutcomeTests`; direct calls of the E-03/E-04 fixtures; a scratch two-class module | Deleted module: `11 passed in 1.71s`. Both review-finding keys: `verdict: killed`, `baseline_failing: 0`, newly failing `GateOutcomeTests::test_the_gate_fires_exactly_when_it_should` (F-03 reproduces). E-03 and E-04 expected lists reproduce exactly. A class-level `@pytest.mark.core` on a `unittest.TestCase` collects only that class under `-m core`. The two strings naming `test_no_review_record_in_the_tree_carries_the_retired_field` would make the original V-01 `rg` exit 0 after the test's removal. The bare core tier already measured `1675 passed, 11 warnings in 34.68s` at `16d8abbb8`. |

## Proposed changes (ordered, validatable)

1. E-01, E-02 restore the review-findings gate module and put its outcome table in the core tier (guards `check_review_finding_unescalated`, `evaluate_review_finding_escalation`).
2. E-03, E-04 add a core module with direct tests for `check_plan_priority_required`, `_plan_disposition`, `check_ipd_draft_ready`.
3. E-05 marks two existing spec-criteria tests core (guards `check_spec_criteria_uncovered`).

## Deferred / out of scope (with reason)

- New tests for `check_review_decision_unescalated`, `check_names`, `check_release_gate_consistency`, `_iter_type_files`: already killed by the core tier at HEAD (F-02).
  - Carrier-Declined: no work is owed; the probe verdict `killed` is the item's answer for these keys.
- Wholesale restore of `test_bug_gate_default.py`, `test_prompt_id6_filenames.py`, `test_work_commit.py`, `test_check_engine_receipt_liveness.py`: they guard no surviving `lzg859` key (F-05).
  - Carrier-Declined: no work is owed for this item.
- `SourceInvariantTests` and the live-corpus test of `test_review_findings_gate.py`: forbidden code-structure pinning and live-state reads respectively (E-01).
  - Carrier-Declined: deliberately not restored, by repository policy.

## Scope check

- Over-scope: none. Three test paths, no production code.
- Under-scope: none. All 5 survivors are covered (E-02: 2 keys, E-03: 1, E-04(a): 1, E-05: 1); the 5 killed keys carry recorded verdicts (F-02).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py` passes, per-test list pasted.
- Bare `python3 -m pytest` passes with the new core items included, summary line pasted; `python3 -m pytest --collect-only -q` shows the new core items. A pre-existing core-tier wall-time overrun on a loaded host is reported, not a pass/fail bar; the bar is that the newly core items add under 1s combined (paste `--durations` for them).
- Mutation spot-checks, AFTER committing the three test files through `aw commit p79jts -- <paths>`: for each key K in `check_review_finding_unescalated`, `evaluate_review_finding_escalation`, `check_plan_priority_required`, `_plan_disposition`, `check_spec_criteria_uncovered`, `check_ipd_draft_ready`, run `python3 tools/mutation_probe.py --op return-none agent_workflows/check_engine.py::K -- -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py` and paste its full output. Each must show `head:` at or after the test commit, `baseline_failing: 0`, `verdict: killed`, and a `newly_failing` entry from the test the plan assigns to K (E-02 for the two review-finding keys, E-03, E-04(a), E-05, E-04(b) respectively). The probe mutates its own disposable worktree; never hand-edit `agent_workflows/`. Finally `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` are both empty, where `<base>` is HEAD before execution.

## Spec / documentation sync

N/A: this plan adds and marks tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the five deleted control files named by the backlog item, or only what guards a surviving key?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: only what guards a survivor. The item's remedy is "probe then restore"; the probe (F-02) shows 5 keys already guarded, and F-03/F-05 show which tests actually kill each survivor. Restoring files that guard nothing new would grow the suite without closing a gap, and `check_plan_priority_required` is killed by no existing or deleted file, so it needs a new test regardless. This narrows the work without changing the item's requirements.

### OQ-02: Mark the restored review-findings module core wholesale?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no, only `GateOutcomeTests`. It alone kills both review-finding mutants (F-03) in 0.31s; the rest (about 2s, including a 0.82s reach test) stays in the thorough tier, matching `zhoul7`'s "core markers on the cheapest tests that reach each key" under the 30s core budget.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_findings_gate.py` with every test PASSED; paste `rg -n "class SourceInvariantTests|def test_no_review_record_in_the_tree_carries_the_retired_field|test_no_review_record_in_the_tree|inspect\.|getsource" tests/test_review_findings_gate.py` returning no match (exit 1; E-01 rewords the two string references to the removed test, F-06).
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_review_findings_gate.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <python>
    cachedir: .pytest_cache
    Using --randomly-seed=2557055660
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/p79jts
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_review_findings_gate.py::FindingSubfieldStructureTests::test_convention_is_declared_in_the_schema PASSED [ 10%]
    tests/test_review_findings_gate.py::FindingSubfieldStructureTests::test_the_finding_subfield_parses_and_adds_no_diagnostic PASSED [ 20%]
    tests/test_review_findings_gate.py::GrandfatheringTests::test_many_plans_with_no_reviews_produce_no_findings PASSED [ 30%]
    tests/test_review_findings_gate.py::EndToEndReuseChainTests::test_escalation_is_then_caught_by_the_preexisting_pre_execution_gate PASSED [ 40%]
    tests/test_review_findings_gate.py::EndToEndReuseChainTests::test_the_loop_is_closable_by_resolving_the_question PASSED [ 50%]
    tests/test_review_findings_gate.py::RuleRegistrationTests::test_rule_id_resolves_to_a_registered_rulespec PASSED [ 60%]
    tests/test_review_findings_gate.py::GateOutcomeTests::test_the_gate_fires_exactly_when_it_should PASSED [ 70%]
    tests/test_review_findings_gate.py::LintCheckpointTests::test_the_rule_gates_exactly_two_phases_on_the_file_route PASSED [ 80%]
    tests/test_review_findings_gate.py::SubjectFieldIndexTests::test_the_index_and_the_gate_agree_on_the_subject_spelling PASSED [ 90%]
    tests/test_review_findings_gate.py::GateReachTests::test_every_entry_point_reaches_the_rule_and_counts_it_once PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 10 passed in 3.06s ==============================

    $ rg -n "class SourceInvariantTests|def test_no_review_record_in_the_tree_carries_the_retired_field|test_no_review_record_in_the_tree|inspect\.|getsource" tests/test_review_findings_gate.py
    (no match, exit 1)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest --collect-only -q | rg test_review_findings_gate` showing only `GateOutcomeTests` items; paste the full `tools/mutation_probe.py` output for `check_review_finding_unescalated` and `evaluate_review_finding_escalation` (Required tests), each `verdict: killed` with `newly_failing` naming `GateOutcomeTests`.
  - Observed evidence:
    ```
    $ python3 -m pytest --collect-only | rg test_review_findings_gate
    tests/test_review_findings_gate.py::GateOutcomeTests::test_the_gate_fires_exactly_when_it_should

    $ python3 -m pytest --collect-only -q | rg test_review_findings_gate
    tests/test_review_findings_gate.py: 1
    ```
    Probe `check_review_finding_unescalated`:
    ```
    head: ec70d5f522621b05248750f87d21226be5558979
    target: agent_workflows/check_engine.py::check_review_finding_unescalated
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_review_findings_gate.GateOutcomeTests::test_the_gate_fires_exactly_when_it_should
    wall_s: 7.98
    ```
    Probe `evaluate_review_finding_escalation`:
    ```
    head: ec70d5f522621b05248750f87d21226be5558979
    target: agent_workflows/check_engine.py::evaluate_review_finding_escalation
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_review_findings_gate.GateOutcomeTests::test_the_gate_fires_exactly_when_it_should
    wall_s: 8.67
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_check_engine_restored_behavior.py` with the priority test PASSED; paste `python3 -m pytest --collect-only -q | rg -c test_check_engine_restored_behavior` (nonzero); paste the full `tools/mutation_probe.py` output for `check_plan_priority_required` (Required tests), `verdict: killed` with `newly_failing` naming the E-03 test.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_check_engine_restored_behavior.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <python>
    cachedir: .pytest_cache
    Using --randomly-seed=1318480527
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/p79jts
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_check_engine_restored_behavior.py::test_plan_disposition_is_the_first_component_under_the_plans_dir PASSED [ 33%]
    tests/test_check_engine_restored_behavior.py::test_check_ipd_draft_ready_nudges_only_a_finished_pending_draft PASSED [ 66%]
    tests/test_check_engine_restored_behavior.py::test_check_plan_priority_required_reports_only_approved_plans_missing_fields PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 3 passed in 0.41s ===============================

    $ python3 -m pytest --collect-only -q | rg -c test_check_engine_restored_behavior
    1
    ```
    Probe `check_plan_priority_required`:
    ```
    head: ec70d5f522621b05248750f87d21226be5558979
    target: agent_workflows/check_engine.py::check_plan_priority_required
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_check_engine_restored_behavior::test_check_plan_priority_required_reports_only_approved_plans_missing_fields
    wall_s: 8.82
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `-v` lines showing both E-04 tests PASSED; paste the full `tools/mutation_probe.py` output for `_plan_disposition` and `check_ipd_draft_ready` (Required tests), each `verdict: killed` with `newly_failing` naming the matching E-04 test.
  - Observed evidence:
    ```
    tests/test_check_engine_restored_behavior.py::test_plan_disposition_is_the_first_component_under_the_plans_dir PASSED [ 33%]
    tests/test_check_engine_restored_behavior.py::test_check_ipd_draft_ready_nudges_only_a_finished_pending_draft PASSED [ 66%]
    ```
    Probe `_plan_disposition`:
    ```
    head: ec70d5f522621b05248750f87d21226be5558979
    target: agent_workflows/check_engine.py::_plan_disposition
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_check_engine_restored_behavior::test_plan_disposition_is_the_first_component_under_the_plans_dir
    wall_s: 7.98
    ```
    Probe `check_ipd_draft_ready`:
    ```
    head: ec70d5f522621b05248750f87d21226be5558979
    target: agent_workflows/check_engine.py::check_ipd_draft_ready
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_check_engine_restored_behavior::test_check_ipd_draft_ready_nudges_only_a_finished_pending_draft
    wall_s: 7.29
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest --collect-only -q | rg test_check_engine_spec_criteria` showing exactly the two marked tests; paste `python3 -m pytest -o addopts="" -q tests/test_check_engine_spec_criteria.py` all passing; paste the full `tools/mutation_probe.py` output for `check_spec_criteria_uncovered` (Required tests), `verdict: killed` with `newly_failing` naming at least one of the two E-05 tests; paste the bare `python3 -m pytest` summary line and `--durations` for the newly core items; paste `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/`, both empty, and `git diff --stat <base>..HEAD` listing only the three Scope-Paths (plus this plan).
  - Observed evidence:
    ```
    $ python3 -m pytest --collect-only | rg test_check_engine_spec_criteria
    tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests::test_clean_fixture_yields_zero_findings_and_exit_code_zero
    tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests::test_positive_control_fires_when_criterion_missing

    $ python3 -m pytest --collect-only -q | rg test_check_engine_spec_criteria
    tests/test_check_engine_spec_criteria.py: 2

    $ python3 -m pytest -o addopts="" -q tests/test_check_engine_spec_criteria.py
    ...............                                                          [100%]
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    15 passed in 1.27s
    ```
    Probe `check_spec_criteria_uncovered`:
    ```
    head: ec70d5f522621b05248750f87d21226be5558979
    target: agent_workflows/check_engine.py::check_spec_criteria_uncovered
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 2
    newly_failing (2 total):
      tests.test_check_engine_spec_criteria.CheckEngineSpecCriteriaTests::test_clean_fixture_yields_zero_findings_and_exit_code_zero
      tests.test_check_engine_spec_criteria.CheckEngineSpecCriteriaTests::test_positive_control_fires_when_criterion_missing
    wall_s: 6.52
    ```
    Bare test suite summary:
    ```
    1746 passed, 11 warnings in 49.19s
    ```
    Durations for newly core items:
    ```
    $ python3 -m pytest -o addopts="" -m core --durations=0 tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py
    ============================== slowest durations ===============================
    0.42s call     tests/test_review_findings_gate.py::GateOutcomeTests::test_the_gate_fires_exactly_when_it_should
    0.03s call     tests/test_check_engine_restored_behavior.py::test_plan_disposition_is_the_first_component_under_the_plans_dir
    0.01s call     tests/test_check_engine_restored_behavior.py::test_check_plan_priority_required_reports_only_approved_plans_missing_fields
    0.01s call     tests/test_check_engine_restored_behavior.py::test_check_ipd_draft_ready_nudges_only_a_finished_pending_draft
    0.01s call     tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests::test_clean_fixture_yields_zero_findings_and_exit_code_zero
    0.01s call     tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests::test_positive_control_fires_when_criterion_missing
    ======================= 6 passed, 22 deselected in 1.23s =======================
    ```
    Diff checks (<base> = d9896125a4693123b3c3a34df9ea3274bebaf552):
    ```
    $ git diff --stat d9896125a4693123b3c3a34df9ea3274bebaf552..HEAD -- agent_workflows/
    (empty)

    $ git diff --stat -- agent_workflows/
    (empty)

    $ git diff --stat d9896125a4693123b3c3a34df9ea3274bebaf552..HEAD
     tests/test_check_engine_restored_behavior.py |  143 +++
     tests/test_check_engine_spec_criteria.py     |    4 +
     tests/test_review_findings_gate.py           | 1227 ++++++++++++++++++++++++++
     3 files changed, 1374 insertions(+)
    ```
    Hook churn: none observed during `aw commit`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01, OQ-02).
- Scope fence: `- Scope-Paths:` is a declaration, not a stop condition. An out-of-scope edit that proves necessary (for example a gated `bug` backlog item under E-01's disposition rule) is made and then justified at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).
- You MUST paste the ACTUAL command, runner, and probe output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (return values, drift fields), never source text or structure.
- Mutation spot-checks run through `tools/mutation_probe.py` after the test commit; never hand-edit `agent_workflows/`. Confirm with empty `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/`.
- Commit only through `aw commit p79jts -- tests/test_review_findings_gate.py tests/test_check_engine_restored_behavior.py tests/test_check_engine_spec_criteria.py`, verify `git diff --cached --name-only`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; by hand, run `aw ipd lint --phase pre-transition` to conforming with every V-item at `Result: pass`, then `aw ipd finalize p79jts`. Never `git mv` the plan by hand.
