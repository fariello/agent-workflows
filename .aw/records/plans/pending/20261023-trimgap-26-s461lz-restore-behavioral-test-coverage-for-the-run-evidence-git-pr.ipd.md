# IPD: Restore behavioral test coverage for the run_evidence git provenance helpers (get_git_head, _porcelain_paths, dirty_within) and record validate_evidence as guarded

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `i2g20d` (Set `trimgap`, group 6 of the `wo21z5` `## Filing plan`) carries four `agent_workflows/run_evidence.py` keys whose `wo21z5` `## Budget probe results` verdict is `budget-exhausted` (never mutation-probed): `validate_evidence` (control `tests/test_benchmark_corpus.py`) and the three git provenance helpers `_porcelain_paths`, `dirty_within` and `get_git_head` (control `tests/test_begin_dirty_gate_scope.py`, deleted by the suite trim `19313eed`). Probing at authoring HEAD `b169e12bb` (F-01 to F-05) shows `validate_evidence` is GUARDED, including under the routine `core` selection, while the three git helpers are guarded ONLY by the non-core (thorough-tier) suite: under a bare `python3 -m pytest` (the core tier and the runner merge gate) a `return-none` mutant of each survives with zero newly failing tests. These helpers feed `aw ipd begin`'s in-scope dirty gate (`ipd_lifecycle._baseline_ambiguity` delegates to `run_evidence.dirty_within`) and the receipt's `base_head` (`ipd_lifecycle.begin` calls `run_evidence.get_git_head`), so a regression that makes begin stop refusing in-scope dirt, or record a wrong base commit, would pass the routine gate today.
- Scope: Restore the deleted `tests/test_begin_dirty_gate_scope.py` from `19313eed^` as a `core`-marked behavioral module, dropping the one test that pins a function signature via `inspect` (forbidden by P16); and add a new `core`-marked module `tests/test_run_evidence_git_provenance.py` with direct behavioral tests of `run_evidence.get_git_head`, `run_evidence._porcelain_paths` and `run_evidence.dirty_within` against throwaway git repositories. Record `validate_evidence` as guarded with re-run probe evidence; no new tests are owed for it. EXCLUDES any change to `agent_workflows/run_evidence.py`, `agent_workflows/ipd_lifecycle.py` or any other production file; EXCLUDES `get_git_dirty_digest` and `get_worktree_path` (measured guarded by `wo21z5` itself, not in this item); EXCLUDES `run_cli._run_evidence` (a different module's key).
- Scope-Paths: tests/test_begin_dirty_gate_scope.py, tests/test_run_evidence_git_provenance.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: i2g20d
- Set: trimgap
- Order: 26
- Highest E allocated: 06
- Author: opencode
- Id: s461lz
- Approval: 2026-10-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (core re-probes need a commit first: new E-06 owns commit, probes and bare gate), PR-002 (unsatisfiable budget and count bars), PR-003 (provenance line vs inspect grep), PR-004 (head/baseline_failing/base evidence), PR-005 (execution contract) fixed; F-04/F-06/F-02 reproduced at baeb8d0cc (F-08)

- 2026-10-23 to-review (opencode): authored from backlog `i2g20d`; probed all four keys at HEAD `b169e12bb` under both the per-file non-slow selection and the routine `-m core` selection, and probed the deleted control file, before writing expected outcomes (F-01..F-06).
- 2026-10-23 draft (opencode): created.

## Goal

Make a mutation that breaks any of the three `run_evidence` git provenance helpers turn a routine (bare, core-tier) test red, by restoring the deleted `aw ipd begin` dirty-gate test module and adding direct tests of the helpers' return contracts, and record with probe evidence that `validate_evidence` is already guarded by the core tier so its gap is closed without new tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the control module

- [x] E-01 Before any edit, record `git rev-parse HEAD` as `<base>`. Restore `tests/test_begin_dirty_gate_scope.py` from `git show 19313eed^:tests/test_begin_dirty_gate_scope.py` (319 lines, 19 tests in classes `IsolatedBaselineGrantsAuthorityTests`, `IsolatedBaselineStillFailsClosedTests`, `NonIsolatedRefusalIsUnchangedTests`, `RefusalMessageIsActionableTests`, `BaseHeadAlwaysComesFromTheMainTreeTests`, `RunnerDeclaresTheExecutionBaselineTests`). Add `import pytest` and `pytestmark = pytest.mark.core` after the imports, and extend the module docstring with one line in the shape `tests/test_attention_stem.py` uses: "Restored under backlog i2g20d, findings wo21z5, from revision 19313eed^." followed by a line naming the one dropped test (E-02), for example "Excluded: test_driver_begin_accepts_the_isolated_declaration (it pinned a function signature; P16)." Do not write the word `inspect` in either line, because V-02 checks the file has no `inspect` reference. Keep every other test body verbatim, including its imports of `_commit_all`, `_init_git`, `_ready_plan_text` and `_write_plan` from `tests.test_ipd_lifecycle_cli`.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, carries the `core` marker, and every verbatim test passes at HEAD (measured at authoring: `19 passed in 1.58s`, F-05; at review the probe baseline over the same file was `baseline_failing: 0`, F-08).
  - Execution state: performed

- [x] E-02 Delete `RunnerDeclaresTheExecutionBaselineTests.test_driver_begin_accepts_the_isolated_declaration` from the restored module. It asserts on `inspect.signature(OC.driver_begin)` (parameter kind and default), which pins code structure rather than behavior and is forbidden by the `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" rule (1) and P16. Keep the other two tests of that class (`test_isolated_turn_sends_the_declaration`, `test_non_isolated_turn_sends_nothing`), which call `OC.begin_baseline_env` and assert its returned mapping. Do not add a replacement: the isolated-declaration behavior is already exercised end to end by `IsolatedBaselineGrantsAuthorityTests`, which calls `LC.begin(..., isolated_baseline=True)`.
  - Depends on: E-01
  - Expected outcome: `test_driver_begin_accepts_the_isolated_declaration` is absent, the module contains no `inspect` reference, and every remaining test passes (18 at authoring; re-derive at execution, the count is not the bar).
  - Execution state: performed

### Task group 2: direct helper tests

- [x] E-03 Create `tests/test_run_evidence_git_provenance.py` (`pytestmark = pytest.mark.core`, stdlib `subprocess` plus pytest `tmp_path`, a local `_git` helper that runs git with `check=True` and sets `user.email`/`user.name` via `git config` in the fixture repo) with a `GetGitHead` group calling `run_evidence.get_git_head` directly. Assert, all measured at authoring (F-06): a non-repo directory returns `"unversioned"`; a freshly `git init`-ed repo with no commit returns `"unversioned"`; after one commit it returns exactly the 40-character SHA that `git rev-parse HEAD` prints for that repo.
  - Depends on: none
  - Expected outcome: the assertions pass at HEAD; the committed-repo assertion fails under a `return None` mutant of `get_git_head` (and the two `"unversioned"` ones fail too, since `None != "unversioned"`). The mutant is proven by E-06.
  - Execution state: performed

- [x] E-04 Add a `PorcelainPaths` group to the same module calling `run_evidence._porcelain_paths` directly. Assert (F-06): a non-repo directory returns `None`; an unborn repo and a clean committed repo each return `[]`; after (a) modifying committed `a.txt`, (b) `git mv b.txt c.txt` and (c) creating untracked `new/sub/x.py` inside a wholly new directory, the result sorted equals `["a.txt", "b.txt", "c.txt", "new/sub/x.py"]` (both rename sides present, the untracked file listed individually rather than as `new/`), and the returned list has no duplicates.
  - Depends on: E-03
  - Expected outcome: the assertions pass at HEAD; the clean-repo `[]` and dirty-list assertions fail under a `return None` mutant (proven by E-06).
  - Execution state: performed

- [x] E-05 Add a `DirtyWithin` group to the same module calling `run_evidence.dirty_within(repo, scope_paths, matcher)` directly with an injected matcher `lambda p, s: p == s or p.startswith(s.rstrip("/") + "/")`. Assert (F-06): a non-repo directory with a non-empty scope returns `"unversioned"`; empty `scope_paths` returns `"clean"` even when the tree is dirty; on the E-04 dirty tree, scope `["a.txt"]` returns `"a.txt"`, scope `["new/", "a.txt", "b.txt"]` returns `"a.txt\nb.txt\nnew/sub/x.py"` (sorted, newline-joined), and the disjoint scope `["zzz.txt"]` returns `"clean"` (the path-overlap rule: out-of-scope dirt is ignored); on a clean committed repo scope `["a.txt"]` returns `"clean"`.
  - Depends on: E-04
  - Expected outcome: all assertions pass at HEAD; every assertion except the empty-scope one fails under a `return None` mutant of `dirty_within`, and the in-scope and clean assertions also fail under a `return None` mutant of `_porcelain_paths` (which `dirty_within` maps to `"unversioned"`). The mutants are proven by E-06.
  - Execution state: performed

### Task group 3: commit and prove at the core tier

- [x] E-06 Commit both test files through `aw commit s461lz -- tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py` (`tools/mutation_probe.py` checks out committed `HEAD` into its own worktree via `git worktree add --detach <dir> HEAD`, so uncommitted tests are invisible to it and every probe would report `survived`; F-08). If the mutating `ruff --fix`/`ruff-format` pre-commit hook rewrites lines, `aw commit` re-stages and retries; record those hunks as hook churn in V-06. Then run, for each key in (`get_git_head`, `_porcelain_paths`, `dirty_within`), `python3 tools/mutation_probe.py agent_workflows/run_evidence.py::<key> --op return-none -- -o addopts= -q -p no:randomly -m core tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py`; re-run the F-02 guarded check `python3 tools/mutation_probe.py agent_workflows/run_evidence.py::validate_evidence --op return-none -- -o addopts= -q -p no:randomly -m core tests/test_benchmark_corpus.py tests/test_run_evidence_completion.py tests/test_host_runner_output_bound.py`; then run the bare routine gate `python3 -m pytest`. A probe with `baseline_failing` above 0 or a `verdict:` other than `killed`/`survived` (for example `error`) is not a result: record it, fix the cause if in scope, and re-run. Never hand-edit `agent_workflows/`.
  - Depends on: E-02, E-05
  - Expected outcome: every probe prints a `head:` at or after the E-06 commit, `baseline_failing: 0` and `verdict: killed`; the `get_git_head`, `_porcelain_paths` and `dirty_within` probes' `newly_failing` lists each name at least one test from `tests/test_run_evidence_git_provenance.py` (re-derive; the count is not the bar); `validate_evidence` stays `killed` (F-02, F-08). The bare gate exits 0 with no `failed` or `error`. A core-tier wall-time overrun is reported verbatim, not a pass/fail bar for this plan, because the bare run already exceeded 30s before this change (F-07: 34.93s); it counts against this plan only if a test from either module is among the printed slowest tests.
  - Execution state: performed

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
| F-08 | review at HEAD `baeb8d0cc`: `tools/mutation_probe.py` (`git worktree add --detach ... HEAD`); control probes `--op return-none --extra-test 19313eed:tests/test_begin_dirty_gate_scope.py -- -o addopts= -q -p no:randomly tests/test_begin_dirty_gate_scope.py`; `validate_evidence` core probe; F-06 direct calls re-run inline | Probe reads committed HEAD only, so the core re-probes must follow a commit (E-06). Control probes all `killed`, `baseline_failing: 0` (so every restored test passes at HEAD): `get_git_head` 6, `_porcelain_paths` 7, `dirty_within` 12. `validate_evidence` core probe: `killed`, `baseline_failing: 0`, 3 newly failing (the three F-02 `AdversarialScoringTests`). F-06 direct-call values reproduce exactly, including the de-duplicated dirty list. `runner_shared.begin_baseline_env` (re-exported by `oc_runipd`) and `oc_runipd.driver_begin` exist. Whole-tier F-03 probes (about 4 to 5 min each) not re-run. |
| F-07 | bare `python3 -m pytest` at HEAD `b169e12bb` | `1675 passed, 11 warnings in 34.93s`, measured while four mutation probes from other lanes were running on the same host; the restored and new modules add roughly 2s. |

## Proposed changes (ordered, validatable)

1. E-01 restores the control module with the `core` marker and provenance docstring.
2. E-02 drops the single signature-pinning test.
3. E-03 adds direct tests of `get_git_head`.
4. E-04 adds direct tests of `_porcelain_paths`.
5. E-05 adds direct tests of `dirty_within`.
6. E-06 commits both modules, then proves every helper mutant killed under `-m core`, re-confirms `validate_evidence` guarded, and runs the bare gate.

## Deferred / out of scope (with reason)

- `validate_evidence` gets no new tests: F-01 and F-02 show its `return-none` mutant is killed by 90 surviving tests, 3 of them in the core tier, so it is guarded at the routine gate. E-06 / V-06 re-run the core probe at execution HEAD to confirm that still holds.
  - Carrier-Declined: no work is owed; the key is measured guarded at the core tier.
- `get_git_dirty_digest` and `get_worktree_path` are not keys of this backlog item: `wo21z5` `## Budget probe results` already records both `killed`/`guarded`.
  - Carrier-Declined: not part of the item and already measured guarded by the findings doc.
- Whether the routine core tier budget (30s) is being exceeded on a loaded host (F-07) is a suite-infrastructure question independent of this plan; this plan adds about 2s and does not change the budget.
  - Carrier-Declined: no reach gap is created by this plan and the backlog item names no work on the budget; it is a separate maintainer decision.

## Scope check

- Over-scope: none. The two declared test files are the only paths changed. No production code changes.
- Under-scope: none. All four keys named by backlog `i2g20d` are probed at both selections (F-01 to F-04); the three unguarded keys get restored and direct coverage, and the guarded key is recorded with evidence.

## Required tests / validation

- `python3 -m pytest tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py -o addopts="" -v -p no:randomly` passes, with the per-test list pasted (the restored tests, 18 at authoring, plus the E-03/E-04/E-05 tests; every test PASSED is the bar, not the count).
- Bare `python3 -m pytest` exits 0 (core tier, including both modules), with the summary line, exit status and any `CORE TIER BUDGET EXCEEDED` block pasted.
- Core-tier mutation re-probes (E-06), after the E-06 commit, for each of `_porcelain_paths`, `dirty_within`, `get_git_head`: full output pasted (`head`, `selection` with `-m core`, `baseline_failing: 0`, `verdict: killed`, `newly_failing` naming a test from the new module).
- Guarded re-check (E-06): the F-02 core probe for `validate_evidence`, full output pasted.
- `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should `validate_evidence` get new tests even though it probes guarded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The remedy "probe then restore" means restore only what the probe shows unguarded (the `rf1xxr` E-02 mapping). F-02 measured the mutant killed by three core-tier tests in the already-restored `tests/test_benchmark_corpus.py`, so it is guarded at the routine gate. E-06 / V-06 re-confirm at execution HEAD.

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

- [x] V-01 validates E-01
  - Required evidence: paste `<base>`; paste `python3 -m pytest -o addopts= --collect-only -q -m core tests/test_begin_dirty_gate_scope.py` output listing the restored tests as selected (proving the `core` marker); and paste `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_begin_dirty_gate_scope.py` with every test PASSED.
  - Observed evidence:
    Base commit: `83840ffeda6b72052cffadc27e56f978cf16d232`
    Collection check:
      ```
tests/test_begin_dirty_gate_scope.py::RunnerDeclaresTheExecutionBaselineTests::test_non_isolated_turn_sends_nothing
tests/test_begin_dirty_gate_scope.py::RunnerDeclaresTheExecutionBaselineTests::test_isolated_turn_sends_the_declaration
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_preserves_the_two_properties_existing_tests_assert
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_does_not_tell_the_operator_to_touch_another_partys_work
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_offers_a_remedy_the_operator_may_actually_apply
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_refusal_text_has_no_em_or_en_dash
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineGrantsAuthorityTests::test_isolated_turn_granted_despite_in_scope_dirt_in_main_tree
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineGrantsAuthorityTests::test_isolated_turn_records_the_committed_base_it_will_be_cut_from
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn
tests/test_begin_dirty_gate_scope.py::BaseHeadAlwaysComesFromTheMainTreeTests::test_base_head_is_this_repos_head_even_when_isolated
tests/test_begin_dirty_gate_scope.py::BaseHeadAlwaysComesFromTheMainTreeTests::test_isolated_and_non_isolated_receipts_bind_the_same_base
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineStillFailsClosedTests::test_isolated_baseline_does_not_exempt_out_of_scope_or_empty_scope
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_default_argument_and_explicit_false_agree
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_default_argument_receipt_is_unchanged_on_a_clean_tree
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_default_argument_preserves_todays_refusal

============================== SLOW TESTS REPORT ===============================
0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
18 tests collected in 1.84s
      ```
    - Execution check:
      ```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/s461lz
configfile: pyproject.toml
plugins: anyio-4.14.1, cov-7.1.0, xdist-3.8.0
collecting ... collected 18 items

tests/test_begin_dirty_gate_scope.py::IsolatedBaselineGrantsAuthorityTests::test_isolated_turn_granted_despite_in_scope_dirt_in_main_tree PASSED [  5%]
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineGrantsAuthorityTests::test_isolated_turn_records_the_committed_base_it_will_be_cut_from PASSED [ 11%]
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn PASSED [ 16%]
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo PASSED [ 22%]
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineStillFailsClosedTests::test_isolated_baseline_does_not_exempt_out_of_scope_or_empty_scope PASSED [ 27%]
tests/test_begin_dirty_gate_scope.py::IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated PASSED [ 33%]
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_default_argument_and_explicit_false_agree PASSED [ 38%]
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_default_argument_preserves_todays_refusal PASSED [ 44%]
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_default_argument_receipt_is_unchanged_on_a_clean_tree PASSED [ 50%]
tests/test_begin_dirty_gate_scope.py::NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline PASSED [ 55%]
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_does_not_tell_the_operator_to_touch_another_partys_work PASSED [ 61%]
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_offers_a_remedy_the_operator_may_actually_apply PASSED [ 66%]
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_preserves_the_two_properties_existing_tests_assert PASSED [ 72%]
tests/test_begin_dirty_gate_scope.py::RefusalMessageIsActionableTests::test_refusal_text_has_no_em_or_en_dash PASSED [ 77%]
tests/test_begin_dirty_gate_scope.py::BaseHeadAlwaysComesFromTheMainTreeTests::test_base_head_is_this_repos_head_even_when_isolated PASSED [ 83%]
tests/test_begin_dirty_gate_scope.py::BaseHeadAlwaysComesFromTheMainTreeTests::test_isolated_and_non_isolated_receipts_bind_the_same_base PASSED [ 88%]
tests/test_begin_dirty_gate_scope.py::RunnerDeclaresTheExecutionBaselineTests::test_isolated_turn_sends_the_declaration PASSED [ 94%]
tests/test_begin_dirty_gate_scope.py::RunnerDeclaresTheExecutionBaselineTests::test_non_isolated_turn_sends_nothing PASSED [100%]
============================== SLOW TESTS REPORT ===============================

0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
============================== 18 passed in 1.67s ==============================
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff --no-index` (or equivalent) between `19313eed^:tests/test_begin_dirty_gate_scope.py` and the restored file showing that the only changes are the `pytest` import, the `pytestmark` line, the docstring provenance lines, and the removal of `test_driver_begin_accepts_the_isolated_declaration`; paste `grep -c "inspect" tests/test_begin_dirty_gate_scope.py` returning `0`; paste the `-v` run showing every test PASSED and `test_driver_begin_accepts_the_isolated_declaration` absent.
  - Observed evidence:
    - Diff against 19313eed^:
      ```diff
diff --git a/tests/test_begin_dirty_gate_scope.py b/tests/test_begin_dirty_gate_scope.py
index 12277dad9..ef22729f2 100644
--- a/tests/test_begin_dirty_gate_scope.py
+++ b/tests/test_begin_dirty_gate_scope.py
@@ -21,6 +21,9 @@ safety property rather than rescoped it. So this module pins, in one place, that

 Fixtures are built here (stdlib unittest, git-backed throwaway repos) rather than pointed at any live
 lane: the live lane set churns hourly, so a test naming one would rot.
+
+Restored under backlog i2g20d, findings wo21z5, from revision 19313eed^.
+Excluded: test_driver_begin_accepts_the_isolated_declaration (it pinned a function signature; P16).
 """

 from __future__ import annotations
@@ -30,6 +33,8 @@ import tempfile
 import unittest
 from pathlib import Path

+import pytest
+
 from agent_workflows import ipd_lifecycle as LC
 from agent_workflows import oc_runipd as OC

@@ -40,6 +45,8 @@ from tests.test_ipd_lifecycle_cli import (
     _write_plan,
 )

+pytestmark = pytest.mark.core
+
 IN_SCOPE = "agent_workflows/demo.py"
 OUT_OF_SCOPE = "unrelated_note.txt"

@@ -304,16 +311,6 @@ class RunnerDeclaresTheExecutionBaselineTests(unittest.TestCase):
         # Sending nothing (rather than "0") keeps the non-isolated path byte-identical to pre-fix.
         self.assertEqual(OC.begin_baseline_env(False), {})

-    def test_driver_begin_accepts_the_isolated_declaration(self) -> None:
-        import inspect
-
-        sig = inspect.signature(OC.driver_begin)
-        self.assertIn("isolated", sig.parameters)
-        param = sig.parameters["isolated"]
-        # Keyword-only with a behavior-preserving default: existing call shapes are unaffected.
-        self.assertEqual(param.kind, inspect.Parameter.KEYWORD_ONLY)
-        self.assertIs(param.default, False)
-

 if __name__ == "__main__":  # pragma: no cover
     unittest.main()
      ```
    - Absence of inspect:
      ```
$ grep -c "inspect" tests/test_begin_dirty_gate_scope.py
0
      ```
    - `-v` run: as shown in V-01, 18 passed with `test_driver_begin_accepts_the_isolated_declaration` absent.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_run_evidence_git_provenance.py` output listing the `get_git_head` direct tests (the three cases: non-repo, unborn, committed SHA) as PASSED.
  - Observed evidence:
    ```
tests/test_run_evidence_git_provenance.py::TestGetGitHead::test_non_repo_returns_unversioned PASSED [  8%]
tests/test_run_evidence_git_provenance.py::TestGetGitHead::test_unborn_repo_returns_unversioned PASSED [ 16%]
tests/test_run_evidence_git_provenance.py::TestGetGitHead::test_committed_repo_returns_head_sha PASSED [ 25%]
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the same `-v` output listing the `_porcelain_paths` direct tests (non-repo `None`; unborn and clean `[]`; the four-path dirty list with no duplicates) as PASSED.
  - Observed evidence:
    ```
tests/test_run_evidence_git_provenance.py::TestPorcelainPaths::test_non_repo_returns_none PASSED [ 33%]
tests/test_run_evidence_git_provenance.py::TestPorcelainPaths::test_unborn_repo_returns_empty_list PASSED [ 41%]
tests/test_run_evidence_git_provenance.py::TestPorcelainPaths::test_clean_committed_repo_returns_empty_list PASSED [ 50%]
tests/test_run_evidence_git_provenance.py::TestPorcelainPaths::test_dirty_tree_returns_sorted_deduped_paths PASSED [ 58%]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the same `-v` output listing the `dirty_within` direct tests (non-repo `"unversioned"`, empty scope `"clean"`, in-scope hits sorted and newline-joined, disjoint scope `"clean"`, clean repo `"clean"`) as PASSED.
  - Observed evidence:
    ```
tests/test_run_evidence_git_provenance.py::TestDirtyWithin::test_non_repo_with_non_empty_scope_returns_unversioned PASSED [ 66%]
tests/test_run_evidence_git_provenance.py::TestDirtyWithin::test_empty_scope_returns_clean_even_when_tree_is_dirty PASSED [ 75%]
tests/test_run_evidence_git_provenance.py::TestDirtyWithin::test_in_scope_dirt_returns_sorted_newline_joined PASSED [ 83%]
tests/test_run_evidence_git_provenance.py::TestDirtyWithin::test_disjoint_scope_returns_clean PASSED [ 91%]
tests/test_run_evidence_git_provenance.py::TestDirtyWithin::test_clean_repo_returns_clean PASSED [100%]
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `aw commit` output naming the E-06 commit; paste the full output of the three helper probes and the `validate_evidence` probe (produced by `tools/mutation_probe.py` itself in E-06), each showing `head:` at or after that commit, a `selection:` containing `-m core`, `baseline_failing: 0` and `verdict: killed`, with each helper probe's `newly_failing` list naming at least one test from `tests/test_run_evidence_git_provenance.py`; paste the bare `python3 -m pytest` summary line showing `passed` with no `failed` or `error`, its exit status, and any `CORE TIER BUDGET EXCEEDED` block verbatim; paste `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/`, both empty, and `git diff --stat <base>..HEAD` naming only the two test files and this plan.
  - Observed evidence:
    - `aw commit` output:
      ```
aw commit: committed 2 path(s): 935af371a32a367201a373817f057a57f75dd38d
      ```
    - Probe `get_git_head`:
      ```
head: 935af371a32a367201a373817f057a57f75dd38d
target: agent_workflows/run_evidence.py::get_git_head
operator: return-none
selection: -o addopts= -q -p no:randomly -m core tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py
verdict: killed
baseline_failing: 0
mutant_failing: 9
newly_failing (9 total):
  tests.test_begin_dirty_gate_scope.BaseHeadAlwaysComesFromTheMainTreeTests::test_base_head_is_this_repos_head_even_when_isolated
  tests.test_begin_dirty_gate_scope.BaseHeadAlwaysComesFromTheMainTreeTests::test_isolated_and_non_isolated_receipts_bind_the_same_base
  tests.test_begin_dirty_gate_scope.IsolatedBaselineGrantsAuthorityTests::test_isolated_turn_granted_despite_in_scope_dirt_in_main_tree
  tests.test_begin_dirty_gate_scope.IsolatedBaselineGrantsAuthorityTests::test_isolated_turn_records_the_committed_base_it_will_be_cut_from
  tests.test_begin_dirty_gate_scope.IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_default_argument_receipt_is_unchanged_on_a_clean_tree
  tests.test_run_evidence_git_provenance.TestGetGitHead::test_committed_repo_returns_head_sha
  tests.test_run_evidence_git_provenance.TestGetGitHead::test_non_repo_returns_unversioned
  tests.test_run_evidence_git_provenance.TestGetGitHead::test_unborn_repo_returns_unversioned
wall_s: 12.87
      ```
    - Probe `_porcelain_paths`:
      ```
head: 935af371a32a367201a373817f057a57f75dd38d
target: agent_workflows/run_evidence.py::_porcelain_paths
operator: return-none
selection: -o addopts= -q -p no:randomly -m core tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py
verdict: killed
baseline_failing: 0
mutant_failing: 13
newly_failing (13 total):
  tests.test_begin_dirty_gate_scope.BaseHeadAlwaysComesFromTheMainTreeTests::test_isolated_and_non_isolated_receipts_bind_the_same_base
  tests.test_begin_dirty_gate_scope.IsolatedBaselineStillFailsClosedTests::test_isolated_baseline_does_not_exempt_out_of_scope_or_empty_scope
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_default_argument_preserves_todays_refusal
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_default_argument_receipt_is_unchanged_on_a_clean_tree
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline
  tests.test_begin_dirty_gate_scope.RefusalMessageIsActionableTests::test_offers_a_remedy_the_operator_may_actually_apply
  tests.test_begin_dirty_gate_scope.RefusalMessageIsActionableTests::test_preserves_the_two_properties_existing_tests_assert
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_clean_repo_returns_clean
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_disjoint_scope_returns_clean
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_in_scope_dirt_returns_sorted_newline_joined
  tests.test_run_evidence_git_provenance.TestPorcelainPaths::test_clean_committed_repo_returns_empty_list
  tests.test_run_evidence_git_provenance.TestPorcelainPaths::test_dirty_tree_returns_sorted_deduped_paths
  tests.test_run_evidence_git_provenance.TestPorcelainPaths::test_unborn_repo_returns_empty_list
wall_s: 13.01
      ```
    - Probe `dirty_within`:
      ```
head: 935af371a32a367201a373817f057a57f75dd38d
target: agent_workflows/run_evidence.py::dirty_within
operator: return-none
selection: -o addopts= -q -p no:randomly -m core tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py
verdict: killed
baseline_failing: 0
mutant_failing: 17
newly_failing (17 total):
  tests.test_begin_dirty_gate_scope.BaseHeadAlwaysComesFromTheMainTreeTests::test_isolated_and_non_isolated_receipts_bind_the_same_base
  tests.test_begin_dirty_gate_scope.IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn
  tests.test_begin_dirty_gate_scope.IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo
  tests.test_begin_dirty_gate_scope.IsolatedBaselineStillFailsClosedTests::test_isolated_baseline_does_not_exempt_out_of_scope_or_empty_scope
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_default_argument_and_explicit_false_agree
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_default_argument_preserves_todays_refusal
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_default_argument_receipt_is_unchanged_on_a_clean_tree
  tests.test_begin_dirty_gate_scope.NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline
  tests.test_begin_dirty_gate_scope.RefusalMessageIsActionableTests::test_does_not_tell_the_operator_to_touch_another_partys_work
  tests.test_begin_dirty_gate_scope.RefusalMessageIsActionableTests::test_offers_a_remedy_the_operator_may_actually_apply
  tests.test_begin_dirty_gate_scope.RefusalMessageIsActionableTests::test_preserves_the_two_properties_existing_tests_assert
  tests.test_begin_dirty_gate_scope.RefusalMessageIsActionableTests::test_refusal_text_has_no_em_or_en_dash
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_clean_repo_returns_clean
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_disjoint_scope_returns_clean
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_empty_scope_returns_clean_even_when_tree_is_dirty
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_in_scope_dirt_returns_sorted_newline_joined
  tests.test_run_evidence_git_provenance.TestDirtyWithin::test_non_repo_with_non_empty_scope_returns_unversioned
wall_s: 13.87
      ```
    - Guarded re-check `validate_evidence`:
      ```
head: 935af371a32a367201a373817f057a57f75dd38d
target: agent_workflows/run_evidence.py::validate_evidence
operator: return-none
selection: -o addopts= -q -p no:randomly -m core tests/test_benchmark_corpus.py tests/test_run_evidence_completion.py tests/test_host_runner_output_bound.py
verdict: killed
baseline_failing: 0
mutant_failing: 3
newly_failing (3 total):
  tests.test_benchmark_corpus.AdversarialScoringTests::test_honest_control_scored_complete
  tests.test_benchmark_corpus.AdversarialScoringTests::test_one_golden_transcript_per_class_scored_as_intended
  tests.test_benchmark_corpus.AdversarialScoringTests::test_zero_critical_seed_missed
wall_s: 7.23
      ```
    - Bare `python3 -m pytest`:
      - Summary line: `1792 passed, 11 warnings in 65.12s (0:01:05)` (0 failed, 0 error)
      - Exit status: 1
      - CORE TIER BUDGET EXCEEDED block:
        ```
================================ CORE TIER BUDGET EXCEEDED ================================
Core tier wall time: 65.12s exceeded budget of 30.00s.
Host 1-minute load average: 11.18 on 12 CPUs
Top 10 slowest core tests:
   1.   8.38s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
   2.   8.19s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
   3.   7.36s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
   4.   5.34s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
   5.   5.17s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
   6.   4.10s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
   7.   4.02s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
   8.   3.89s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
   9.   3.25s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
  10.   2.87s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
===========================================================================================
        ```
    - Diffs:
      - `git diff --stat 83840ffeda6b72052cffadc27e56f978cf16d232..HEAD -- agent_workflows/`: empty
      - `git diff --stat -- agent_workflows/`: empty
      - `git diff --stat 83840ffeda6b72052cffadc27e56f978cf16d232..HEAD`:
        ```
 tests/test_begin_dirty_gate_scope.py      | 316 ++++++++++++++++++++++++++++++
 tests/test_run_evidence_git_provenance.py | 136 +++++++++++++
 2 files changed, 452 insertions(+)
        ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit s461lz -- tests/test_begin_dirty_gate_scope.py tests/test_run_evidence_git_provenance.py` (plus this plan when recording evidence); verify `git diff --cached --name-only`; never `git add -A`; never push. You MUST paste the ACTUAL probe and runner output into each `V-*`; never claim a mutant was killed or a test passed that you did not run. Mutation checks use `tools/mutation_probe.py` only (it mutates a disposable worktree, never the checkout), after the E-06 commit; no production file under `agent_workflows/` may change. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize s461lz` itself.
