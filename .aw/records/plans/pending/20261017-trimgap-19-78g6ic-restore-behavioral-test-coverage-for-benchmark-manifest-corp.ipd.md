# IPD: Restore behavioral test coverage for benchmark manifest, corpus, protocol and scorer

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the benchmark slice: groups 22 (`benchmark_manifest.py`, 8 keys), 25 (`benchmark_protocol.py`, 7), 27 (`benchmark_corpus.py`, 8) and 47 (`benchmark_scorer.py`, 2), 25 keys in all, every one reached at `19313eed^` only by the deleted `tests/test_benchmark_corpus.py`.
- Scope: Restore `tests/test_benchmark_corpus.py` from `19313eed^` unchanged, marked `core`, and add two residual tests for the two boolean keys whose `False` polarity no restored test asserts (`is_ground_truth_accessible`, `is_critical_class`, F-03). The 25 keys: `benchmark_manifest.manifest_from_dict`, `validate_manifest`, `validate_ceilings_dict`, `declared_factors`, `BenchmarkManifest.result_key`, `BenchmarkManifest.to_json`, `can_pool`, `manifest_from_json`; `benchmark_protocol.assert_frozen`, `freeze_protocol`, `validate_protocol`, `_decision_view`, `changed_decision_fields`, `protocol_digest`, `_canonical_json`; `benchmark_corpus.hash_tree`, `materialize_task`, `is_ground_truth_accessible`, `load_ground_truth`, `reset_task`, `SeededTask.ground_truth_path`, `seed_workspace_hash`, `task_classes_present`; `benchmark_scorer.intended_verdict`, `is_critical_class`. EXCLUDES any production change and any change under `tests/benchmark_fixtures/`.
- Scope-Paths: tests/test_benchmark_corpus.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 19
- Highest E allocated: 02
- Author: opencode
- Id: 78g6ic
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted file at HEAD `f84c3af26`, measured per-key reach and durations, and ran an early-return mutation sweep over all 25 keys (both polarities for boolean keys); scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 25 benchmark keys reached by the routine bare core-tier run through the restored corpus, manifest, protocol and adversarial-scoring tests, which materialize and reset seeded tasks, freeze and compare protocols, and score golden transcripts. Done means an early-return mutation of any of the 25 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

- [x] E-01 Create `tests/test_benchmark_corpus.py` from `git show 19313eed^:tests/test_benchmark_corpus.py` with exactly these edits: add `import pytest` and a module-level `pytestmark = pytest.mark.core` (29 tests, 0.11 to 0.17s summed CPU at authoring); add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w` and revision `19313eed^`. The file reads only `tests/benchmark_fixtures/` data through the module under test, which is behavior, so no test is dropped. Disposition rule if a restored test fails at execution HEAD (none did at authoring or at review, 29 passed): do not mark E-01 performed until that test is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that test's expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: every restored test passes (or is dispositioned per the rule above) and a bare `python3 -m pytest --collect-only -q` selects the file (core tier). The authoring and review count of 29 restored tests is context, not the bar.
  - Execution state: performed

- [x] E-02 Append a `ResidualKeyTests(unittest.TestCase)` class with two tests asserting values measured at authoring: (a) `corpus.is_ground_truth_accessible(<tmp>/"missing")` is False, an empty existing tmpdir is False, and after writing `<tmp>/a/b/<corpus.GROUND_TRUTH_FILENAME>` it is True (the nested `rglob` search); (b) for every class in `benchmark_scorer.ADVERSARIAL_CLASSES`, `is_critical_class(c)` is True exactly when `c != benchmark_scorer.CONTROL_CLASS` (`CONTROL_CLASS` is `honest_complete` at authoring), and `is_critical_class("not-a-class")` is False. Re-measure at execution HEAD first; if a value changed, apply the E-01 disposition rule. All values were re-measured at review (`f2bf7b59a`..`c71943e22`) and matched, and a draft of both tests passed and killed both mutations.
  - Depends on: E-01
  - Expected outcome: both tests pass and kill the scratch mutations named in V-02.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): the restored file asserts only on outputs of the benchmark modules.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): the file is cheap enough to mark whole.
- Sibling precedent: `8bhcd3` and `438gkf` in this Set restore one core-marked module plus residual tests.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` reaching-file column | All 25 keys list `tests/test_benchmark_corpus.py` as their only reaching file. |
| F-02 | `tools/deleted_test_replay.py 19313eed tests/test_benchmark_corpus.py` at HEAD `f84c3af26`; scratch coverage contexts | Replay `pass`, 29 passed in 2.32s; every one of the 25 keys has executed lines. |
| F-03 | Early-return mutation sweep, each reverted | 23 keys killed. `is_ground_truth_accessible` -> `False` survives (the restored tests only assert False on clean workspaces, so a constant False passes); `is_critical_class` -> `False` survives (only the True polarity is asserted). Direct calls at HEAD produced the E-02 values (`GROUND_TRUTH_FILENAME` is `ground_truth.json`; 14 classes, 13 critical). |

## Proposed changes (ordered, validatable)

1. E-01 restores the module unchanged except marker and docstring.
2. E-02 adds residual tests for the two under-asserted boolean keys.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none. One test file; no production code.
- Under-scope: none for the 25 keys (F-02, F-03, E-02).

## Required tests / validation

- `python3 -m pytest tests/test_benchmark_corpus.py -o addopts="" -v` passes, per-test list pasted.
- Reach: same run with `COVERAGE_FILE` pointing under the gitignored `.aw/state/` (so no `.coverage` lands in the worktree root) and `--cov=agent_workflows.benchmark_manifest --cov=agent_workflows.benchmark_protocol --cov=agent_workflows.benchmark_corpus --cov=agent_workflows.benchmark_scorer --cov-report=json:<that dir>/cov.json`. Per-key reach is then read from the JSON report's per-function `files[<module>]["functions"][<key>]["executed_lines"]` (coverage 7.x), printing each of the 25 keys with its executed-line count; every count must be nonzero. `term-missing` alone reports lines, not functions, and cannot show per-key reach. Measured at review with the restored file alone: all 25 nonzero (`BenchmarkManifest.result_key`, `can_pool`, `protocol_digest` and others at 1). Delete the scratch coverage files afterwards.
- Mutation spot-checks (scratch, reverted): `can_pool` return True, `freeze_protocol` return None, `reset_task` return None, `intended_verdict` return None, plus the two in V-02. Method: insert `return <value>` as the first body line of the named function, run `python3 -m pytest tests/test_benchmark_corpus.py -o addopts="" -q`, and restore the file from a copy (or `git checkout -- <file>`). At review, all six were killed (failures: `can_pool` 2, `freeze_protocol` 9, `reset_task` 2, `intended_verdict` 1, and 1 each for the two residual mutations), and the two residual mutations survived with `-k 'not ResidualKeyTests'`, confirming F-03.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Does the restored file read production source anywhere?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. Its only file reads are `tests/benchmark_fixtures/` JSON through `load_corpus`/`load_ground_truth` and its own fixture constant `FIXTURES`, which is input data, not production code.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste a diff against `19313eed^` showing only the `pytest` import, `pytestmark` and docstring lines (plus E-02's class); paste the `-v` run listing every restored test PASSED (or each failure with its E-01 disposition), plus the bare `python3 -m pytest --collect-only -q` lines showing the file is core-selected; paste the failures from scratch `can_pool` return-True, `freeze_protocol` return-None, `reset_task` return-None and `intended_verdict` return-None mutations, each reverted.
  - Observed evidence:
    - Diff against `19313eed^`:
      ```diff
      $ git diff 19313eed^:tests/test_benchmark_corpus.py tests/test_benchmark_corpus.py
      diff --git a/tests/test_benchmark_corpus.py b/tests/test_benchmark_corpus.py
      index fae6b7c95..16ff2d0cb 100644
      --- a/tests/test_benchmark_corpus.py
      +++ b/tests/test_benchmark_corpus.py
      @@ -11,6 +11,8 @@ Falsifiable, stdlib `unittest` only. Each test asserts DETECTION or REJECTION:
                        intended, with ZERO critical seed missed by the reference scorer.
         * E-04 / V-04: the protocol digest is frozen; a post-result change to any metric/threshold/retry/
                        exclusion/ground-truth is REJECTED without a new protocol version.
      +
      +Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^.
       """

       from __future__ import annotations
      @@ -21,11 +23,15 @@ import tempfile
       import unittest
       from pathlib import Path

      +import pytest
      +
       from agent_workflows import benchmark_corpus as corpus
       from agent_workflows import benchmark_manifest as mani
       from agent_workflows import benchmark_protocol as protocol
       from agent_workflows import benchmark_scorer as scorer

      +pytestmark = pytest.mark.core
      +
       FIXTURES = Path(__file__).resolve().parent / "benchmark_fixtures"
       CORPUS_ROOT = FIXTURES / "corpus"
       ADVERSARIAL_ROOT = FIXTURES / "adversarial"
      @@ -400,5 +406,29 @@ class ProtocolFreezeTests(unittest.TestCase):
               )


      +# ============================================================================================
      +# Residual key tests (E-02 / V-02)
      +# ============================================================================================
      +
      +
      +class ResidualKeyTests(unittest.TestCase):
      +    def test_is_ground_truth_accessible_both_polarities(self):
      +        with tempfile.TemporaryDirectory() as td:
      +            p = Path(td)
      +            self.assertFalse(corpus.is_ground_truth_accessible(p / "missing"))
      +            self.assertFalse(corpus.is_ground_truth_accessible(p))
      +            nested = p / "a" / "b"
      +            nested.mkdir(parents=True)
      +            (nested / corpus.GROUND_TRUTH_FILENAME).write_text("{}", encoding="utf-8")
      +            self.assertTrue(corpus.is_ground_truth_accessible(p))
      +
      +    def test_is_critical_class_both_polarities(self):
      +        for c in scorer.ADVERSARIAL_CLASSES:
      +            if c == scorer.CONTROL_CLASS:
      +                self.assertFalse(scorer.is_critical_class(c))
      +            else:
      +                self.assertTrue(scorer.is_critical_class(c))
      +        self.assertFalse(scorer.is_critical_class("not-a-class"))
      +
       if __name__ == "__main__":
           unittest.main()
      ```
    - `-v` run listing every restored test PASSED:
      ```
      tests/test_benchmark_corpus.py::AdversarialScoringTests::test_honest_control_scored_complete PASSED [  3%]
      tests/test_benchmark_corpus.py::AdversarialScoringTests::test_zero_critical_seed_missed PASSED [  6%]
      tests/test_benchmark_corpus.py::AdversarialScoringTests::test_false_complete_requires_a_completion_claim PASSED [  9%]
      tests/test_benchmark_corpus.py::AdversarialScoringTests::test_one_golden_transcript_per_class_scored_as_intended PASSED [ 12%]
      tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_every_class_has_deterministic_reset_identical_hashes PASSED [ 16%]
      tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_ground_truth_is_plain_reviewable_json PASSED [ 19%]
      tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_hidden_truth_never_materialized_into_workspace PASSED [ 22%]
      tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_ground_truth_loadable_only_via_scorer_path PASSED [ 25%]
      tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_all_seven_task_classes_present PASSED [ 29%]
      tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_reset_restores_after_executor_mutation PASSED [ 32%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_differing_factor_forbids_pooling PASSED [ 35%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_token_ceiling_only_where_host_reports_tokens PASSED [ 38%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_result_key_covers_every_factor PASSED [ 41%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_usage_fields_present_or_unavailable_never_zero_filled PASSED [ 45%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_dollar_cost_rejected_in_usage PASSED [ 48%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_dollar_or_credit_ceiling_rejected PASSED [ 51%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_every_identity_factor_is_required PASSED [ 54%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_round_trip_preserves_identity_and_digest PASSED [ 58%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_trial_is_part_of_identity PASSED [ 61%]
      tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_wall_time_is_always_captured PASSED [ 64%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_cosmetic_change_is_digest_noop PASSED [ 67%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_ground_truth_change_rejected PASSED [ 70%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_incomplete_protocol_cannot_be_frozen PASSED [ 74%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_metric_change_rejected PASSED [ 77%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_exclusion_change_rejected PASSED [ 80%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_freeze_computes_stable_digest PASSED [ 83%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_retry_change_rejected PASSED [ 87%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_declared_new_version_is_allowed PASSED [ 90%]
      tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_threshold_change_rejected_without_version_bump PASSED [ 93%]
      ```
    - Bare `python3 -m pytest --collect-only -q`:
      ```
      $ python3 -m pytest --collect-only -q | grep test_benchmark_corpus
      tests/test_benchmark_corpus.py: 31
      ```
    - Scratch mutation spot-checks (reverted):
      `can_pool` return-True:
      ```
      FAILED tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_trial_is_part_of_identity
      FAILED tests/test_benchmark_corpus.py::ManifestResultIdentityTests::test_differing_factor_forbids_pooling
      2 failed, 29 passed in 0.87s
      ```
      `freeze_protocol` return-None:
      ```
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_metric_change_rejected
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_retry_change_rejected
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_cosmetic_change_is_digest_noop
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_exclusion_change_rejected
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_incomplete_protocol_cannot_be_frozen
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_ground_truth_change_rejected
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_declared_new_version_is_allowed
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_post_result_threshold_change_rejected_without_version_bump
      FAILED tests/test_benchmark_corpus.py::ProtocolFreezeTests::test_freeze_computes_stable_digest
      9 failed, 22 passed in 1.67s
      ```
      `reset_task` return-None:
      ```
      FAILED tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_every_class_has_deterministic_reset_identical_hashes
      FAILED tests/test_benchmark_corpus.py::CorpusDeterminismTests::test_reset_restores_after_executor_mutation
      2 failed, 29 passed in 0.38s
      ```
      `intended_verdict` return-None:
      ```
      FAILED tests/test_benchmark_corpus.py::AdversarialScoringTests::test_one_golden_transcript_per_class_scored_as_intended
      1 failed, 30 passed in 0.47s
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` lines for the two residual tests PASSED (the class name `ResidualKeyTests` is a pointer, not the bar: the bar is that both polarities of both keys are asserted); paste the failures from scratch `is_ground_truth_accessible` return-False and `is_critical_class` return-False mutations (reverted); paste the per-key reach listing from Required tests (25 keys, each with a nonzero executed-line count); paste the bare `python3 -m pytest` summary line, `aw sanitize --agent` with no `fail`, a final empty `git diff agent_workflows/`, and `git status --short` showing no `.coverage` or other scratch file.
  - Observed evidence:
    - `-v` lines for the two residual tests PASSED:
      ```
      tests/test_benchmark_corpus.py::ResidualKeyTests::test_is_ground_truth_accessible_both_polarities PASSED [ 96%]
      tests/test_benchmark_corpus.py::ResidualKeyTests::test_is_critical_class_both_polarities PASSED [100%]
      ```
    - Scratch `is_ground_truth_accessible` return-False mutation (reverted):
      ```
      FAILED tests/test_benchmark_corpus.py::ResidualKeyTests::test_is_ground_truth_accessible_both_polarities
      1 failed, 30 passed in 0.49s
      (confirmed F-03: without ResidualKeyTests, 29 passed, 2 deselected in 1.68s)
      ```
    - Scratch `is_critical_class` return-False mutation (reverted):
      ```
      FAILED tests/test_benchmark_corpus.py::ResidualKeyTests::test_is_critical_class_both_polarities
      1 failed, 30 passed in 0.42s
      (confirmed F-03: without ResidualKeyTests, 29 passed, 2 deselected in 0.45s)
      ```
    - Per-key reach listing (all 25 keys nonzero executed lines):
      ```
      Total keys checked: 25
        benchmark_manifest.manifest_from_dict: 16 executed lines
        benchmark_manifest.validate_manifest: 16 executed lines
        benchmark_manifest.validate_ceilings_dict: 8 executed lines
        benchmark_manifest.declared_factors: 5 executed lines
        benchmark_manifest.BenchmarkManifest.result_key: 1 executed lines
        benchmark_manifest.BenchmarkManifest.to_json: 1 executed lines
        benchmark_manifest.can_pool: 1 executed lines
        benchmark_manifest.manifest_from_json: 1 executed lines
        benchmark_protocol.assert_frozen: 10 executed lines
        benchmark_protocol.freeze_protocol: 4 executed lines
        benchmark_protocol.validate_protocol: 8 executed lines
        benchmark_protocol._decision_view: 4 executed lines
        benchmark_protocol.changed_decision_fields: 6 executed lines
        benchmark_protocol.protocol_digest: 1 executed lines
        benchmark_protocol._canonical_json: 1 executed lines
        benchmark_corpus.hash_tree: 13 executed lines
        benchmark_corpus.materialize_task: 8 executed lines
        benchmark_corpus.is_ground_truth_accessible: 7 executed lines
        benchmark_corpus.load_ground_truth: 3 executed lines
        benchmark_corpus.reset_task: 2 executed lines
        benchmark_corpus.SeededTask.ground_truth_path: 1 executed lines
        benchmark_corpus.seed_workspace_hash: 1 executed lines
        benchmark_corpus.task_classes_present: 1 executed lines
        benchmark_scorer.intended_verdict: 4 executed lines
        benchmark_scorer.is_critical_class: 1 executed lines
      All 25 keys nonzero: True
      ```
    - Suite summary line:
      ```
      886 passed in 39.75s (via aw suite)
      ```
    - `aw sanitize --agent`:
      ```
      {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5864,"findings":0,"evidence":["leak-scan"],"next":null}
      ```
    - Final empty `git diff agent_workflows/`:
      ```
      $ git diff agent_workflows/
      (empty)
      ```
    - `git status --short`:
      ```
      $ git status --short
      ?? tests/test_benchmark_corpus.py
      ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Scope fence: `tests/test_benchmark_corpus.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under E-01's disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch production edits that must be reverted and must be absent from the diff; scratch coverage files live under the gitignored `.aw/state/` and are deleted.
- Honesty: you MUST paste the actual runner output for every test and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit 78g6ic -- tests/test_benchmark_corpus.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize 78g6ic` instead. Never hand-`git mv` the plan.
