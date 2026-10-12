# IPD: Mark DanglingCommitSearchTests real-corpus arm livecorpus

- Date: 2026-10-12
- Kind: child
- Concern: `DanglingCommitSearchTests.test_07_real_corpus_arm_conditional` reads THIS repository's live git object store and history (cwd checkout, commit `0abc01d9`, id6 `8u6770`) but carries no `livecorpus` marker, so it runs in the default fast suite and its verdict depends on live repo state rather than on the code under test.
- Scope: add `@pytest.mark.livecorpus` (and the `import pytest` it needs) to that one test method in `tests/test_runner_shared.py`; no production code changes.
- Scope-Paths: tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: m88gwh
- Blocks-Release: next
- Set: m88gwh
- Order: 1
- Highest E allocated: 02
- Author: agent
- Id: jzeeky

## Workflow history

- 2026-10-12 draft (agent): created.
- 2026-10-12 to-review (agent): authored review-ready from backlog m88gwh.

## Goal

Deselect the live-corpus-dependent test `DanglingCommitSearchTests.test_07_real_corpus_arm_conditional` from the default fast suite by marking it `livecorpus`, so a lane's integration gate is not decided by the state of this repository's own git history, while it still runs in `make test-all` and release-review.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Mark the test

- [ ] E-01 In `tests/test_runner_shared.py`, add `import pytest` to the stdlib/third-party import block (beside `import unittest`) if it is not already imported, and decorate `DanglingCommitSearchTests.test_07_real_corpus_arm_conditional` with `@pytest.mark.livecorpus`, preceded by a short comment stating why (it reads this repository's live git objects and history via `pathlib.Path.cwd()`), mirroring the comment style used beside `@pytest.mark.livecorpus` in `tests/test_verbose_flag_reach.py`.
  - Depends on: none
  - Expected outcome: the test method carries the `livecorpus` marker; no other test or production file changes.
  - Execution state: pending

### Task group 2: Verify selection behavior

- [ ] E-02 Run the bare default suite (`python3 -m pytest`) and a marker-selected run (`python3 -m pytest -o addopts="" -m livecorpus tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional -rs -v`) and record both outputs.
  - Depends on: E-01
  - Expected outcome: the default run deselects the test and is otherwise green; the marker-selected run collects exactly that one test, which passes or skips by its own conditional logic.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `pyproject.toml` declares the `livecorpus` marker (text beginning "livecorpus: asserts a property over EVERY artifact in this repository's own .aw/records/ tree") and `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, so a marked test is deselected by default and still runs under `make test-all` (Makefile comment "`-m \"\"` clears the default `not slow and not livecorpus` filter").
- Precedent: `tests/test_verbose_flag_reach.py` applies `@pytest.mark.livecorpus` to a method of a `unittest.TestCase` subclass with an explanatory comment, so pytest markers on TestCase methods are an established pattern here.
- `tests/test_runner_shared.py` currently imports `unittest` but not `pytest` (import block near "from typing import Any").
- AGENTS.md repo-local rule: run the suite bare as `python3 -m pytest`; use `-o addopts=""` for narrowed runs.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | `test_07_real_corpus_arm_conditional` uses `repo_path = pathlib.Path.cwd()` and runs `git cat-file -e 0abc01d9` / `git merge-base --is-ancestor 0abc01d9 main`, then calls `runner_shared.find_dangling_commits_by_subject(repo_path, "8u6770")`. Its outcome depends on the live checkout's object store and `main` tip. | Method body in `DanglingCommitSearchTests` |
| F2 | It carries no marker, so it runs in the default fast suite, i.e. inside every lane's merge-and-revalidate gate, where the live repo (a worktree on a lane branch, with a `main` that other lanes advance) can flip it. | absence of `pytest.mark` on the method; `addopts` filter |
| F3 | The synthetic-repo tests 01-06 in the same class already cover `find_dangling_commits_by_subject` behavior hermetically, so deselecting test 07 by default loses no fast-suite behavioral coverage. | sibling methods using `_make_repo` |

## Proposed changes (ordered, validatable)

1. E-01: add `import pytest` and `@pytest.mark.livecorpus` with an explanatory comment on the one method.
2. E-02: demonstrate default deselection and marker selection.

## Deferred / out of scope (with reason)

- Auditing other tests in the repo for missing `livecorpus` markers: not requested by backlog m88gwh; would broaden scope.
- Changing the test's assertions or conditional skip logic: the backlog item asks only for the marker.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog item names one test and one missing marker, both covered by E-01, with E-02 proving the selection effect.

## Required tests / validation

- Default bare suite `python3 -m pytest` passes and does not run the test (V-02).
- `python3 -m pytest -o addopts="" -m livecorpus tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional -rs -v` collects exactly 1 test and reports it PASSED or SKIPPED (V-02).
- Diff limited to `tests/test_runner_shared.py` (V-01).

## Spec / documentation sync

N/A: no spec or user-facing doc describes this individual test's marker; the `livecorpus` marker contract in `pyproject.toml` is unchanged.

## Open questions

### OQ-01: Should test 07 instead be rewritten to be hermetic?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Its purpose is to check the real-corpus arm (an actual unreachable commit in this repository), which cannot be made hermetic without becoming a duplicate of tests 01-06; the backlog item prescribes the marker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- tests/test_runner_shared.py` showing `import pytest` (if newly added) and `@pytest.mark.livecorpus` directly above `def test_07_real_corpus_arm_conditional`, plus pasted `git diff --name-only` output listing only `tests/test_runner_shared.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted tail of the bare `python3 -m pytest` run showing the `N passed` summary with no failures, and pasted output of the `-m livecorpus ... -k test_07_real_corpus_arm_conditional -rs -v` run showing exactly one collected test with PASSED or SKIPPED (with skip reason); plus pasted `python3 -m pytest -o addopts="" -m "not slow and not livecorpus" tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional` output showing 1 deselected and 0 selected.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Commit through `aw commit jzeeky -- tests/test_runner_shared.py`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and V-01 and V-02 record concrete pasted evidence with Result: pass.
