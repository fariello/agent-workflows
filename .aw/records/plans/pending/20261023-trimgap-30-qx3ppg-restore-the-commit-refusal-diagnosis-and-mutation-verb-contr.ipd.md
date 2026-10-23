# IPD: Restore the commit-refusal diagnosis and mutation-verb control modules into the core tier

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` carries three keys whose deleted control modules restore cleanly: `ipd_lifecycle.classify_commit_refusal` (group 37, remedy "restore behavioral coverage", `wo21z5` verdict `unguarded`) and `plans_refs.apply_renames` / `plans_refs._dirs` (group 17, "probe then restore", `budget-exhausted`). Measured at authoring HEAD `6c0a6b72a` (F-01 to F-03): `classify_commit_refusal` is not reached by the core tier and its `return-none` mutant SURVIVES every surviving file that reaches it; `apply_renames` and `_dirs` are not reached by the core tier, and are killed only by non-core files (thorough tier). The deleted control files `tests/test_commit_refusal_diagnosis.py` and `tests/test_awcmdsurf_mutation_verbs.py` (removed by `19313eed`) pass at HEAD unchanged and kill all three mutants (F-04, F-05). So today a regression that silenced the concurrent-writer diagnosis, or that broke the `aw rename plans` / `aw group plans` CLI path, would pass the routine merge gate.
- Scope: Restore the two control files from `19313eed^` at their original paths, verbatim except for a provenance docstring line and a module-level `pytestmark = pytest.mark.core`, then probe the three keys under the core selection. EXCLUDES any production-code change and any change to other test files.
- Scope-Paths: tests/test_commit_refusal_diagnosis.py, tests/test_awcmdsurf_mutation_verbs.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 30
- Highest E allocated: 04
- Author: opencode
- Id: qx3ppg

## Workflow history
- 2026-10-23 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (existing docstring, import placement verified with pinned ruff), PR-002 (core membership proved with -m core; explicit-path collect-only bypasses the core filter), PR-003 (pre-existing budget overrun not a failure), PR-004 (execution contract), PR-005 (counts re-derived from the 19313eed^ blobs) fixed. Kills reproduced at 3969bf382 (F-07); review record .aw/records/reviews/20261023-trimgap-30-qx3ppg-restore-the-commit-refusal-diagnosis-and-mutation-verb-contr.review.md

- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm` (groups 17, 37). Measured core reach at HEAD `6c0a6b72a`, probed the three keys against surviving files, and ran and probed both deleted control files from `19313eed^` before writing expected outcomes.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of `classify_commit_refusal`, `apply_renames` or `_dirs` turn the routine core tier red by restoring the two deleted behavioral modules that already kill them. Done means all three keys report `verdict: killed` under a `-m core` selection containing the restored files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the control modules

- [ ] E-01 Restore `tests/test_commit_refusal_diagnosis.py` with `git show 19313eed^:tests/test_commit_refusal_diagnosis.py > tests/test_commit_refusal_diagnosis.py` (151 lines, 9 module-level pytest tests with a `repo` fixture over a throwaway git repo). Append to the module docstring one line "Restored under backlog nzc6dm, plan qx3ppg, findings wo21z5, from revision 19313eed^." and add `pytestmark = pytest.mark.core` after the imports (`pytest` is already imported). Keep every test body verbatim.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_commit_refusal_diagnosis.py` passes every test the module defines, and that number equals the count of `def test_` functions in `git show 19313eed^:tests/test_commit_refusal_diagnosis.py`, re-derived at execution (9 at authoring and at review, F-04).
  - Execution state: pending

- [ ] E-02 Restore `tests/test_awcmdsurf_mutation_verbs.py` with `git show 19313eed^:tests/test_awcmdsurf_mutation_verbs.py > tests/test_awcmdsurf_mutation_verbs.py` (97 lines, 7 tests in `MutationVerbsTests` that drive `cli.main` for `rename plans`, `group plans` and `archive` over a throwaway git repo). It already has a one-line module docstring (`"""Tests for awcmdsurf Order 03: the noun-verb MUTATION verbs (rename/group/archive) + --no-refs."""`) and does not import `pytest`: append the provenance line "Restored under backlog nzc6dm, plan qx3ppg, findings wo21z5, from revision 19313eed^." to that docstring (making it multi-line), add `import pytest` as a third-party import between the stdlib block and `from agent_workflows import cli`, and add `pytestmark = pytest.mark.core` after the imports. Verified at review: with that placement the pinned pre-commit `ruff` (v0.4.4) reports `All checks passed!`. Keep every test body verbatim.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_awcmdsurf_mutation_verbs.py` passes every test the module defines, and that number equals the count of `def test_` methods in `git show 19313eed^:tests/test_awcmdsurf_mutation_verbs.py`, re-derived at execution (7 at authoring and at review, F-05).
  - Execution state: pending

### Task group 2: commit and prove the mutants die in core

- [ ] E-03 Commit both files with `aw commit qx3ppg -- tests/test_commit_refusal_diagnosis.py tests/test_awcmdsurf_mutation_verbs.py`, then prove both modules are IN the core selection with `python3 -m pytest --collect-only -q -m core tests/test_commit_refusal_diagnosis.py tests/test_awcmdsurf_mutation_verbs.py` (an explicit-path `--collect-only` WITHOUT `-m core` lists an unmarked file too, so it proves nothing; verified at review: the unmarked control file collected 9 under the explicit path and was deselected under `-m core`), then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_commit_refusal_diagnosis.py tests/test_awcmdsurf_mutation_verbs.py` for the restored modules' own cost.
  - Depends on: E-01, E-02
  - Expected outcome: the `-m core` collection lists both files with every test from E-01 and E-02; the bare run shows no failures; the two modules together cost about 1.3s serial (F-04, F-05: 0.30s and 1.00s). A `CORE TIER BUDGET EXCEEDED` block is recorded verbatim and is NOT a failure of this plan: at review HEAD `3969bf382`, BEFORE any restore, the bare gate already read `Core tier wall time: 63.97s exceeded budget of 30.00s` with `Core tier budget not enforced: host oversubscribed`, so the bar is "no failures", not "under budget" (same rule as siblings `f6el0l`, `btubm6`).
  - Execution state: pending

- [ ] E-04 Run `python3 tools/mutation_probe.py --op return-none --format json K -- -o addopts= -q -p no:randomly -n0 -m core T` for (K, T) = (`agent_workflows/ipd_lifecycle.py::classify_commit_refusal`, `tests/test_commit_refusal_diagnosis.py`), (`agent_workflows/plans_refs.py::apply_renames`, `tests/test_awcmdsurf_mutation_verbs.py`), (`agent_workflows/plans_refs.py::_dirs`, `tests/test_awcmdsurf_mutation_verbs.py`). The tool mutates a disposable worktree cut from HEAD, so it must run after E-03's commit. A kill under this core-marked subset is a kill under the full core tier, which is a superset. Record each `verdict`, `baseline_failing` and `mutant_failing`.
  - Depends on: E-03
  - Expected outcome: three `verdict: killed`, `baseline_failing: 0`, `mutant_failing` 3, 3 and 4 (F-04, F-05).
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): both restored modules call production code (`classify_commit_refusal` on a real git repo; `cli.main` on a real git repo) and assert on returned reasons, exit codes and moved files. Neither imports `inspect` or `ast` or reads production source (F-06).
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget. Module-level `pytestmark = pytest.mark.core` is the established way in, and restoring a deleted module at its original path with that marker is the Set's precedent (executed `y4bt1c`, `pdemar`).
- Probe tool: `tools/mutation_probe.py` (`--op`, `--format json`, `--extra-test COMMIT:PATH`, selection after `--`), as used by `wo21z5` and siblings.
- Commit only through `aw commit qx3ppg -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/replay_coverage_diff.py baseline --out .aw/state/nzc6dm-auth/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `6c0a6b72a` | None of `classify_commit_refusal`, `apply_renames`, `_dirs` is in the core baseline (2892 functions reached): the routine gate never runs them. |
| F-02 | `tools/mutation_probe.py --op return-none --format json agent_workflows/ipd_lifecycle.py::classify_commit_refusal -- -o addopts= -q -p no:randomly -n 6 -m "not slow and not livecorpus" tests/test_ipd_lifecycle_cli.py tests/test_orchestrator_retirement.py` | `verdict: survived`, `mutant_failing: 0` (56.9s). No surviving test anywhere asserts the diagnosis. |
| F-03 | same tool, non-core selection over the nine surviving files `wo21z5` lists for `plans_refs` (`tests/test_artifact_refs_rewrite.py` ... `tests/test_selector_type_containment.py`) | `apply_renames`: `killed`, 49 (98.13s). `_dirs`: `killed`, 88 (122.78s). Both are guarded by the thorough tier only; the gap is core reach. |
| F-04 | `git show 19313eed^:tests/test_commit_refusal_diagnosis.py` run from gitignored scratch with `-o addopts= -q -p no:randomly -n0`; and `tools/mutation_probe.py --op return-none --extra-test 19313eed:tests/test_commit_refusal_diagnosis.py agent_workflows/ipd_lifecycle.py::classify_commit_refusal -- ... tests/test_commit_refusal_diagnosis.py` | `9 passed in 0.30s`. Probe: `killed`, `baseline_failing 0`, `mutant_failing 3` (`test_counts_and_truncates_many_foreign_paths`, `test_names_a_concurrent_writer_when_a_foreign_path_is_dirty`, `test_says_nothing_was_committed_so_the_state_is_safe`), 3.76s. |
| F-05 | same for `tests/test_awcmdsurf_mutation_verbs.py` with targets `plans_refs.apply_renames` and `plans_refs._dirs` | `7 passed in 1.00s`. `apply_renames`: `killed`, `baseline_failing 0`, `mutant_failing 3` (9.6s). `_dirs`: `killed`, 0, 4 (13.12s). |
| F-06 | `grep -nE "inspect|getsource|ast\." ` over both restored files | No hits; `read_text` appears only on files the test itself wrote in its temp repo (asserting moved content and rewritten citations), which is an output, not production source. |
| F-07 | Re-verified at review HEAD `3969bf382`: both `19313eed^` blobs run from a gitignored scratch dir (`16 passed in 1.25s`); the three `--extra-test` probes over the control files reproduce `killed` 0/3, 0/3, 0/4; the core-marked copies pass under `-m core` (9 and 7) while the unmarked copies are fully deselected; the pinned pre-commit `ruff` v0.4.4 accepts both marked copies. A probe of the not-yet-restored path with `-m core` (no file at HEAD, so the extra-test blob is unmarked) reads `survived`, 0/0, which is why E-04 must run after E-03's commit of the MARKED file. | review lane |

## Proposed changes (ordered, validatable)

1. E-01 restores `tests/test_commit_refusal_diagnosis.py` with the core marker.
2. E-02 restores `tests/test_awcmdsurf_mutation_verbs.py` with the core marker.
3. E-03 commits both and records the bare core gate and their cost.
4. E-04 probes the three keys under the core selection.

## Deferred / out of scope (with reason)

- Core-marking the nine existing `plans_refs` files instead.
  - Carrier-Declined: no work is owed; those files take about 100s under the probe (F-03), far above the 1s the restored control file costs, and the control file alone kills both keys.

## Scope check

- Over-scope: none. Only the two restored test files are declared; no production file or existing test changes.
- Under-scope: none. All three keys get a killing core-tier module (E-01, E-02) and a core-selection probe (E-04).

## Required tests / validation

- Both restored modules pass with `-o addopts="" -v -p no:randomly`, per-test lists pasted (E-01, E-02).
- `--collect-only -q -m core` over both files listing every restored test (E-03).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the modules' `--durations=0` output (E-03).
- Three `tools/mutation_probe.py` JSON results pasted, each `verdict: killed`, `baseline_failing: 0` (E-04).
- `git diff --stat <E-03 parent>..HEAD -- agent_workflows/` and `git status --short -- agent_workflows/` both empty (no production change, committed or uncommitted).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: `apply_renames` and `_dirs` are already killed by the thorough tier; is restoring them into core owed?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, for the same reason sibling `2qlg0w` restored core coverage for keys killed only by non-core files: the gap the Set closes is "the routine merge gate does not kill the mutant" (F-01), and the item's remedy for group 17 is "probe then restore". The probe shows the routine gate does not reach them, and the control file is cheap (1.00s, F-05), so restoring it closes the gap at small cost.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --no-index <(git show 19313eed^:tests/test_commit_refusal_diagnosis.py) tests/test_commit_refusal_diagnosis.py` (or an equivalent diff) showing only the docstring line and the `pytestmark` line added; paste the `-v` run with every test PASSED, and the `grep -c '^def test_'` count of the `19313eed^` blob equal to the number passed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the equivalent diff against `19313eed^:tests/test_awcmdsurf_mutation_verbs.py` showing only the appended docstring line (with the closing quotes moved), `import pytest` and `pytestmark` lines added; paste the `-v` run with every test PASSED, and the `grep -c '    def test_'` count of the `19313eed^` blob equal to the number passed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only the two restored files; paste `python3 -m pytest --collect-only -q -m core tests/test_commit_refusal_diagnosis.py tests/test_awcmdsurf_mutation_verbs.py` listing both files with the per-file counts equal to V-01's and V-02's; paste the bare `python3 -m pytest` summary line with no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim, and the `--durations=0` output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the three JSON outputs produced by `tools/mutation_probe.py` (E-04), each with `head` equal to the E-03 commit or later, a selection containing `-m core`, `verdict: killed` and `baseline_failing: 0`; paste `git diff --stat <E-03 parent>..HEAD -- agent_workflows/` and `git status --short -- agent_workflows/`, both empty.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved` or a runner's `auto-approved`).

Execution contract:
- Open questions: OQ-01 is resolved; nothing blocks execution.
- Scope fence: `- Scope-Paths:` declares `tests/test_commit_refusal_diagnosis.py` and `tests/test_awcmdsurf_mutation_verbs.py`. It is a declaration the finalize gate reconciles, not a stop rule: a needed out-of-scope edit is made and then justified with `--scope-reason <path>=<why>`, and a declared path left unmodified gets `--scope-ack`. No production file changes.
- Commit: through `aw commit qx3ppg -- tests/test_commit_refusal_diagnosis.py tests/test_awcmdsurf_mutation_verbs.py` only; check `git diff --cached --name-only` holds only those paths; never `git add -A`/bare/`-a`; never push. The `ruff --fix` hook may rewrite a file; `aw commit` re-stages and retries once.
- Honesty: paste the ACTUAL runner and probe output for every `V-*`; never mark a `V-*` from memory or from the matching `E-*` checkmark.
- Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`. In a managed runner lane the runner performs that finalize; an executor working by hand outside a runner runs it. Never a hand-rolled `git mv`.
