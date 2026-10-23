# IPD: Restore behavioral test coverage for the run_evidence git provenance helpers (get_git_head, _porcelain_paths, dirty_within) and record validate_evidence as guarded

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `i2g20d` (Set `trimgap`, group 6 of the `wo21z5` `## Filing plan`) carries four `agent_workflows/run_evidence.py` keys whose `wo21z5` `## Budget probe results` verdict is `budget-exhausted` (never mutation-probed): `validate_evidence` (control `tests/test_benchmark_corpus.py`) and the three git provenance helpers `_porcelain_paths`, `dirty_within` and `get_git_head` (control `tests/test_begin_dirty_gate_scope.py`, deleted by the suite trim `19313eed`). Probing at authoring HEAD `b169e12bb` (F-01 to F-05) shows `validate_evidence` is GUARDED, including under the routine `core` selection, while the three git helpers are guarded ONLY by the non-core (thorough-tier) suite: under a bare `python3 -m pytest` (the core tier and the runner merge gate) a `return-none` mutant of each survives with zero newly failing tests. These helpers feed `aw ipd begin`'s in-scope dirty gate (`ipd_lifecycle._baseline_ambiguity` delegates to `run_evidence.dirty_within`) and the receipt's `base_head` (`ipd_lifecycle.begin` calls `run_evidence.get_git_head`), so a regression that makes begin stop refusing in-scope dirt, or record a wrong base commit, would pass the routine gate today.
- Scope: Restore the deleted `tests/test_begin_dirty_gate_scope.py` from `19313eed^` as a `core`-marked behavioral module, dropping the one test that pins a function signature via `inspect` (forbidden by P16); and add a new `core`-marked module `tests/test_run_evidence_git_provenance.py` with direct behavioral tests of `run_evidence.get_git_head`, `run_evidence._porcelain_paths` and `run_evidence.dirty_within` against throwaway git repositories. Record `validate_evidence` as guarded with re-run probe evidence; no new tests are owed for it. EXCLUDES any change to `agent_workflows/run_evidence.py`, `agent_workflows/ipd_lifecycle.py` or any other production file; EXCLUDES `get_git_dirty_digest` and `get_worktree_path` (measured guarded by `wo21z5` itself, not in this item); EXCLUDES `run_cli._run_evidence` (a different module's key).
- Scope-Paths: tests/test_begin_dirty_gate_scope.py, tests/test_run_evidence_git_provenance.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: i2g20d
- Set: trimgap
- Order: 26
- Highest E allocated: 05
- Author: opencode
- Id: s461lz

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `i2g20d`; probed all four keys at HEAD `b169e12bb` under both the per-file non-slow selection and the routine `-m core` selection, and probed the deleted control file, before writing expected outcomes (F-01..F-06).
- 2026-10-23 draft (opencode): created.

## Goal

Make a mutation that breaks any of the three `run_evidence` git provenance helpers turn a routine (bare, core-tier) test red, by restoring the deleted `aw ipd begin` dirty-gate test module and adding direct tests of the helpers' return contracts, and record with probe evidence that `validate_evidence` is already guarded by the core tier so its gap is closed without new tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the control module

- [ ] E-01 Restore `tests/test_begin_dirty_gate_scope.py` from `git show 19313eed^:tests/test_begin_dirty_gate_scope.py` (319 lines, 19 tests in classes `IsolatedBaselineGrantsAuthorityTests`, `IsolatedBaselineStillFailsClosedTests`, `NonIsolatedRefusalIsUnchangedTests`, `RefusalMessageIsActionableTests`, `BaseHeadAlwaysComesFromTheMainTreeTests`, `RunnerDeclaresTheExecutionBaselineTests`). Add `import pytest` and `pytestmark = pytest.mark.core` after the imports, and extend the module docstring with one line in the shape `tests/test_attention_stem.py` uses: "Restored under backlog i2g20d, findings wo21z5, from revision 19313eed^." followed by a line naming the one dropped test (E-02). Keep every other test body verbatim, including its imports of `_commit_all`, `_init_git`, `_ready_plan_text` and `_write_plan` from `tests.test_ipd_lifecycle_cli`.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, carries the `core` marker, and all 19 verbatim tests pass at HEAD (measured at authoring: `19 passed in 1.58s`, F-05).
  - Execution state: pending

- [ ] E-02 Delete `RunnerDeclaresTheExecutionBaselineTests.test_driver_begin_accepts_the_isolated_declaration` from the restored module. It asserts on `inspect.signature(OC.driver_begin)` (parameter kind and default), which pins code structure rather than behavior and is forbidden by the `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" rule (1) and P16. Keep the other two tests of that class (`test_isolated_turn_sends_the_declaration`, `test_non_isolated_turn_sends_nothing`), which call `OC.begin_baseline_env` and assert its returned mapping. Do not add a replacement: the isolated-declaration behavior is already exercised end to end by `IsolatedBaselineGrantsAuthorityTests`, which calls `LC.begin(..., isolated_baseline=True)`.
  - Depends on: E-01
  - Expected outcome: the module carries 18 tests, contains no `import inspect` and no `inspect.` reference, and all 18 pass.
  - Execution state: pending

### Task group 2: direct helper tests

- [ ] E-03 Create `tests/test_run_evidence_git_provenance.py` (`pytestmark = pytest.mark.core`, stdlib `subprocess` plus pytest `tmp_path`, a local `_git` helper that runs git with `check=True` and sets `user.email`/`user.name` via `git config` in the fixture repo) with a `GetGitHead` group calling `run_evidence.get_git_head` directly. Assert, all measured at authoring (F-06): a non-repo directory returns `"unversioned"`; a freshly `git init`-ed repo with no commit returns `"unversioned"`; after one commit it returns exactly the 40-character SHA that `git rev-parse HEAD` prints for that repo.
  - Depends on: none
  - Expected outcome: three assertions pass at HEAD; the committed-repo assertion fails under a `return None` mutant of `get_git_head` (and the two `"unversioned"` ones fail too, since `None != "unversioned"`).
  - Execution state: pending

- [ ] E-04 Add a `PorcelainPaths` group to the same module calling `run_evidence._porcelain_paths` directly. Assert (F-06): a non-repo directory returns `None`; an unborn repo and a clean committed repo each return `[]`; after (a) modifying committed `a.txt`, (b) `git mv b.txt c.txt` and (c) creating untracked `new/sub/x.py` inside a wholly new directory, the result sorted equals `["a.txt", "b.txt", "c.txt", "new/sub/x.py"]` (both rename sides present, the untracked file listed individually rather than as `new/`), and the returned list has no duplicates.
  - Depends on: E-03
  - Expected outcome: the assertions pass at HEAD; the clean-repo `[]` and dirty-list assertions fail under a `return None` mutant.
  - Execution state: pending

- [ ] E-05 Add a `DirtyWithin` group to the same module calling `run_evidence.dirty_within(repo, scope_paths, matcher)` directly with an injected matcher `lambda p, s: p == s or p.startswith(s.rstrip("/") + "/")`. Assert (F-06): a non-repo directory with a non-empty scope returns `"unversioned"`; empty `scope_paths` returns `"clean"` even when the tree is dirty; on the E-04 dirty tree, scope `["a.txt"]` returns `"a.txt"`, scope `["new/", "a.txt", "b.txt"]` returns `"a.txt\nb.txt\nnew/sub/x.py"` (sorted, newline-joined), and the disjoint scope `["zzz.txt"]` returns `"clean"` (the path-overlap rule: out-of-scope dirt is ignored); on a clean committed repo scope `["a.txt"]` returns `"clean"`.
  - Depends on: E-04
  - Expected outcome: all assertions pass at HEAD; every assertion except the empty-scope one fails under a `return None` mutant of `dirty_within`, and the in-scope and clean assertions also fail under a `return None` mutant of `_porcelain_paths` (which `dirty_within` maps to `"unversioned"`).
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). Every retained or new assertion calls `LC.begin`, `LC._baseline_ambiguity`, `LC.receipt_path_for`, `OC.begin_baseline_env` or a `run_evidence` helper and checks the returned value, exit code, receipt file or refusal text. E-02 removes the one restored test that inspects a signature instead.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s wall budget (`conftest` "AW_CORE_BUDGET_SECONDS", default `30.0`). A test reached only by the thorough tier does not guard the merge gate, which is exactly the gap F-03 measures. Both modules therefore carry `pytestmark = pytest.mark.core`. The restored module ran 19 tests in 1.58s at authoring (F-05).
- Restoration precedent in this Set: `tests/test_attention_stem.py` (restored under backlog `q86fxm`) and pending plan `a5drqh` restore a deleted module with `pytestmark = pytest.mark.core` and a provenance docstring line; E-01 follows that shape.
- Mutation probing: `tools/mutation_probe.py <path.py>::<qualname> --op <op> --format json [--extra-test COMMIT:PATH] -- <pytest args>` mutates committed HEAD in a disposable worktree; `--extra-test 19313eed:<path>` reads `19313eed^:<path>`. Verdict mapping is the `rf1xxr` E-02 rule as used in `a5drqh`: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`. This plan applies it to the CORE selection, since that is the gate a regression must trip.
- `run_evidence.dirty_within` takes the Scope-Paths matcher by injection ("``matcher`` is injected (rather than reimplementing the Scope-Paths grammar here)"), so the direct tests supply a simple prefix matcher and assert the helper's own contract (sorted, de-duplicated, newline-joined hits; `"clean"`; `"unversioned"`), not the Scope-Paths grammar.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/mutation_probe.py agent_workflows/run_evidence.py::validate_evidence --op return-none --format json -- -m "not slow and not livecorpus" tests/test_capture_command_stream_bounds.py tests/test_host_runner_output_bound.py tests/test_run_evidence_completion.py tests/test_run_recovery_cli.py tests/test_run_viewer.py tests/test_runs_subdir_root.py tests/test_benchmark_corpus.py` at HEAD `b169e12bb` | `verdict: killed`, `baseline_failing: 0`, `newly_failing_total: 90`, `wall_s: 138.93`. The `wo21z5` control `tests/test_benchmark_corpus.py` is no longer deleted: it was restored by commit `03241d58a` ("work(78g6ic): Restore behavioral test coverage for benchmark manifest, corpus, protocol and scorer"). |
| F-02 | same probe with `-m core tests/test_benchmark_corpus.py tests/test_run_evidence_completion.py tests/test_host_runner_output_bound.py` | `verdict: killed`, `newly_failing_total: 3` (`test_benchmark_corpus.AdversarialScoringTests::test_honest_control_scored_complete`, `::test_one_golden_transcript_per_class_scored_as_intended`, `::test_zero_critical_seed_missed`), `wall_s: 7.63`. Mapped verdict: `guarded` under the routine gate. |
| F-03 | survivor probes of `_porcelain_paths`, `dirty_within`, `get_git_head` with the `wo21z5` reaching files under `-m "not slow and not livecorpus"` | All `killed`: `_porcelain_paths` 102 newly failing (`wall_s: 267.39`), `dirty_within` 107 (`wall_s: 338.17`), `get_git_head` 8 on a 4-file subset (`wall_s: 107.64`). But NONE of the 13 reaching files is `core`-marked (`--collect-only -m core` over them: "no tests collected (215 deselected)"). Re-probing each with `-m core -n 4 tests/` (the whole core tier): `_porcelain_paths` `survived` 0 newly failing (`wall_s: 288.63`), `dirty_within` `survived` 0 (`wall_s: 261.14`), `get_git_head` `survived` 0 (`wall_s: 217.19`), each `baseline_failing: 0`. The routine gate does not detect any of the three mutants. |
| F-04 | control probes `--extra-test 19313eed:tests/test_begin_dirty_gate_scope.py -- -o addopts="" -p no:randomly tests/test_begin_dirty_gate_scope.py` | All `killed`, `baseline_failing: 0`, `extra_tests_overwrote: []`: `_porcelain_paths` 7 newly failing (for example `NonIsolatedRefusalIsUnchangedTests::test_default_argument_preserves_todays_refusal`), `dirty_within` 12 (for example `IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn`), `get_git_head` 6 (for example `BaseHeadAlwaysComesFromTheMainTreeTests::test_base_head_is_this_repos_head_even_when_isolated`). Mapped verdict for all three: `unguarded` at the core tier, with the deleted control file as the remedy source. |
| F-05 | the control file copied into `tests/` as a scratch file and run with `python3 -m pytest -o addopts="" -q -p no:randomly`, then removed | `19 passed in 1.58s`; no adaptation is needed for HEAD. One test, `test_driver_begin_accepts_the_isolated_declaration`, asserts only on `inspect.signature(OC.driver_begin)`. No file under the current `tests/` defines any of the module's class names (`grep` for `class IsolatedBaselineGrantsAuthorityTests`/`RunnerDeclaresTheExecutionBaselineTests` returns nothing). |
| F-06 | direct calls at HEAD `b169e12bb` in a throwaway repo | `get_git_head`: non-repo `'unversioned'`; unborn repo `'unversioned'`; committed repo equals `git rev-parse HEAD` (40 chars). `_porcelain_paths`: non-repo `None`; unborn `[]`; clean `[]`; after modify `a.txt`, `git mv b.txt c.txt`, untracked `new/sub/x.py`: `['a.txt', 'b.txt', 'c.txt', 'new/sub/x.py']`. `dirty_within` (prefix matcher): non-repo `'unversioned'`; clean `'clean'`; `['a.txt']` -> `'a.txt'`; `['new/','a.txt','b.txt']` -> `'a.txt\nb.txt\nnew/sub/x.py'`; `['zzz.txt']` -> `'clean'`; `[]` -> `'clean'`. |
| F-07 | bare `python3 -m pytest` at HEAD `b169e12bb` | `1675 passed, 11 warnings in 34.93s`, measured while four mutation probes from other lanes were running on the same host; the restored and new modules add roughly 2s. |

## Proposed changes (ordered, validatable)

1. E-01 restores the control module with the `core` marker and provenance docstring.
2. E-02 drops the single signature-pinning test.
3. E-03 adds direct tests of `get_git_head`.
4. E-04 adds direct tests of `_porcelain_paths`.
5. E-05 adds direct tests of `dirty_within`.

## Deferred / out of scope (with reason)

- `validate_evidence` gets no new tests: F-01 and F-02 show its `return-none` mutant is killed by 90 surviving tests, 3 of them in the core tier, so it is guarded at the routine gate. V-05 re-runs the core probe at execution HEAD to confirm that still holds.
  - Carrier-Declined: no work is owed; the key is measured guarded at the core tier.
- `get_git_dirty_digest` and `get_worktree_path` are not keys of this backlog item: `wo21z5` `## Budget probe results` already records both `killed`/`guarded`.
  - Carrier-Declined: not part of the item and already measured guarded by the findings doc.
- Whether the routine core tier budget (30s) is being exceeded on a loaded host (F-07) is a suite-infrastructure question independent of this plan; this plan adds about 2s and does not change the budget.
  - Carrier-Declined: no reach gap is created by this plan and the backlog item names no work on the budget; it is a separate maintainer decision.

## Scope check

- Over-scope: none. The two declared test files are the only paths changed. No production code changes.
- Under-scope: none. All four keys named by backlog `i2g20d` are probed at both selections (F-01 to F-04); the three unguarded keys get restored and direct coverage, and the guarded key is recorded with evidence.

## Required tests / validation

- `python3 -m pytest tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py -o addopts="" -v -p no:randomly` passes, with the per-test list pasted (18 restored tests plus the E-03/E-04/E-05 tests).
- Bare `python3 -m pytest` passes (core tier, including both modules), with the summary line pasted.
- Core-tier mutation re-probe: `python3 tools/mutation_probe.py agent_workflows/run_evidence.py::<key> --op return-none --format json -- -m core tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py` for each of `_porcelain_paths`, `dirty_within`, `get_git_head`. The probe mutates committed HEAD, so it runs after the E-01..E-05 commit (or with `--extra-test` pointing at it); paste each JSON's `verdict` (must be `killed`) and `newly_failing_total` (must be nonzero).
- Guarded re-check: re-run the F-02 core probe for `validate_evidence` at execution HEAD and paste `verdict` and `newly_failing_total`.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should `validate_evidence` get new tests even though it probes guarded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The remedy "probe then restore" means restore only what the probe shows unguarded (the `rf1xxr` E-02 mapping). F-02 measured the mutant killed by three core-tier tests in the already-restored `tests/test_benchmark_corpus.py`, so it is guarded at the routine gate. V-05 re-confirms at execution HEAD.

### OQ-02: Does "guarded" mean killed by the thorough suite, or by the core tier?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The core tier. The `AGENTS.md` repository development contract states "The core tier is the runner merge gate", and a bare `python3 -m pytest` is what every executor runs. F-03 shows the three git helpers are killed only by non-core modules, so a regression would merge through the runner unseen; that is the coverage gap the backlog item exists to close. Recording them as guarded on the strength of thorough-tier kills would leave the gap open.

### OQ-03: Restore `test_driver_begin_accepts_the_isolated_declaration` or drop it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Drop it (E-02). Its only assertions are on `inspect.signature(OC.driver_begin)`, which `AGENTS.md` rule (1) "NEVER write or restore tests that read production source code using `inspect`" forbids outright. The behavior it was a proxy for (the isolated declaration changing begin's outcome) is asserted directly by `IsolatedBaselineGrantsAuthorityTests` through `LC.begin(..., isolated_baseline=True)`.

### OQ-04: Put the direct helper tests in the restored module or a new one?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A new module, `tests/test_run_evidence_git_provenance.py`. The restored module's subject is `aw ipd begin`'s baseline gate (its docstring and fixtures build an approved plan); the helpers are `run_evidence` primitives with their own return contract and need no plan fixture. Keeping them separate keeps the restored file verbatim except for E-01/E-02, which V-02 verifies by diff.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` showing only `tests/test_begin_dirty_gate_scope.py` and `tests/test_run_evidence_git_provenance.py` added; paste `python3 -m pytest --collect-only -q -m core tests/test_begin_dirty_gate_scope.py` output showing a nonzero collected count (proving the `core` marker); and paste the bare `python3 -m pytest` summary line showing the run passed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --no-index` (or equivalent) between `19313eed^:tests/test_begin_dirty_gate_scope.py` and the restored file showing that the only changes are the `pytest` import, the `pytestmark` line, the docstring provenance lines, and the removal of `test_driver_begin_accepts_the_isolated_declaration`; paste `grep -c "inspect" tests/test_begin_dirty_gate_scope.py` returning `0`; paste the `-v` run showing `18 passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing the `get_git_head` direct tests as PASSED, and paste the `tools/mutation_probe.py agent_workflows/run_evidence.py::get_git_head --op return-none --format json -- -m core tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py` JSON fields `verdict` (`killed`), `newly_failing_total` (nonzero) and the newly failing names, which must include an E-03 test.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing the `_porcelain_paths` direct tests as PASSED, and paste the same core probe for `_porcelain_paths` showing `verdict: killed`, a nonzero `newly_failing_total`, and newly failing names that include an E-04 test.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` output listing the `dirty_within` direct tests as PASSED; paste the same core probe for `dirty_within` showing `verdict: killed`, a nonzero `newly_failing_total`, and newly failing names that include an E-05 test; and paste, from re-running the F-02 core probe for `validate_evidence` at execution HEAD, its `verdict` (`killed`) and `newly_failing_total` (nonzero). Finish with an empty `git diff agent_workflows/` showing no production change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). The executor follows the agent execution contract in `AGENTS.md`: change only `tests/test_begin_dirty_gate_scope.py` and `tests/test_run_evidence_git_provenance.py`, commit through `aw commit s461lz -- tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py`, never push, run mutation probes only through `tools/mutation_probe.py` (which mutates a disposable worktree, never the checkout), and paste actual runner output for every `V-*`. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
