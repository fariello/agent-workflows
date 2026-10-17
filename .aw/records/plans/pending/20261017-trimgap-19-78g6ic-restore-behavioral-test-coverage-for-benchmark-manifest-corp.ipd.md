# IPD: Restore behavioral test coverage for benchmark manifest, corpus, protocol and scorer

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the benchmark slice: groups 22 (`benchmark_manifest.py`, 8 keys), 25 (`benchmark_protocol.py`, 7), 27 (`benchmark_corpus.py`, 8) and 47 (`benchmark_scorer.py`, 2), 25 keys in all, every one reached at `19313eed^` only by the deleted `tests/test_benchmark_corpus.py`.
- Scope: Restore `tests/test_benchmark_corpus.py` from `19313eed^` unchanged, marked `core`, and add two residual tests for the two boolean keys whose `False` polarity no restored test asserts (`is_ground_truth_accessible`, `is_critical_class`, F-03). The 25 keys: `benchmark_manifest.manifest_from_dict`, `validate_manifest`, `validate_ceilings_dict`, `declared_factors`, `BenchmarkManifest.result_key`, `BenchmarkManifest.to_json`, `can_pool`, `manifest_from_json`; `benchmark_protocol.assert_frozen`, `freeze_protocol`, `validate_protocol`, `_decision_view`, `changed_decision_fields`, `protocol_digest`, `_canonical_json`; `benchmark_corpus.hash_tree`, `materialize_task`, `is_ground_truth_accessible`, `load_ground_truth`, `reset_task`, `SeededTask.ground_truth_path`, `seed_workspace_hash`, `task_classes_present`; `benchmark_scorer.intended_verdict`, `is_critical_class`. EXCLUDES any production change and any change under `tests/benchmark_fixtures/`.
- Scope-Paths: tests/test_benchmark_corpus.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 19
- Highest E allocated: 02
- Author: opencode
- Id: 78g6ic

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted file at HEAD `f84c3af26`, measured per-key reach and durations, and ran an early-return mutation sweep over all 25 keys (both polarities for boolean keys); scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 25 benchmark keys reached by the routine bare core-tier run through the restored corpus, manifest, protocol and adversarial-scoring tests, which materialize and reset seeded tasks, freeze and compare protocols, and score golden transcripts. Done means an early-return mutation of any of the 25 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

- [ ] E-01 Create `tests/test_benchmark_corpus.py` from `git show 19313eed^:tests/test_benchmark_corpus.py` with exactly these edits: add `import pytest` and a module-level `pytestmark = pytest.mark.core` (29 tests, 0.11 to 0.17s summed CPU at authoring); add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w` and revision `19313eed^`. The file reads only `tests/benchmark_fixtures/` data through the module under test, which is behavior, so no test is dropped. If a test fails at execution HEAD, STOP on it: record it in Findings and either update only that expectation for an intended change (cite the commit `git log -S` finds) or file a `bug` backlog item with `--blocks-release next` for a regression.
  - Depends on: none
  - Expected outcome: 29 tests pass, all core-selected.
  - Execution state: pending

- [ ] E-02 Append a `ResidualKeyTests(unittest.TestCase)` class with two tests asserting values measured at authoring: (a) `corpus.is_ground_truth_accessible(<tmp>/"missing")` is False, an empty existing tmpdir is False, and after writing `<tmp>/a/b/<corpus.GROUND_TRUTH_FILENAME>` it is True (the nested `rglob` search); (b) for every class in `benchmark_scorer.ADVERSARIAL_CLASSES`, `is_critical_class(c)` is True exactly when `c != benchmark_scorer.CONTROL_CLASS` (`CONTROL_CLASS` is `honest_complete` at authoring), and `is_critical_class("not-a-class")` is False. Re-measure at execution HEAD first; apply the E-01 stop rule if a value changed.
  - Depends on: E-01
  - Expected outcome: both tests pass and kill the scratch mutations named in V-02.
  - Execution state: pending

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
- Reach: same run with `--cov=agent_workflows.benchmark_manifest --cov=agent_workflows.benchmark_protocol --cov=agent_workflows.benchmark_corpus --cov=agent_workflows.benchmark_scorer --cov-report=term-missing`, each of the 25 keys executing.
- Mutation spot-checks (scratch, reverted): `can_pool` return True, `freeze_protocol` return None, `reset_task` return None, `intended_verdict` return None, plus the two in V-02.
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

- [ ] V-01 validates E-01
  - Required evidence: paste a diff against `19313eed^` showing only the `pytest` import, `pytestmark` and docstring lines (plus E-02's class); paste the `-v` run listing 29 restored tests PASSED; paste the failures from scratch `can_pool` return-True and `freeze_protocol` return-None mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` lines for both `ResidualKeyTests` tests PASSED; paste the failures from scratch `is_ground_truth_accessible` return-False and `is_critical_class` return-False mutations (reverted); paste the reach output from Required tests with all 25 keys executing; paste the bare `python3 -m pytest` summary line and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_benchmark_corpus.py` through `aw commit 78g6ic -- tests/test_benchmark_corpus.py`; never push. Mutation spot-checks are scratch production edits that must be reverted and absent from the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
