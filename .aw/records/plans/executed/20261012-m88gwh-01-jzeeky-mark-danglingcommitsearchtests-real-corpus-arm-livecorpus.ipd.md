# IPD: Mark DanglingCommitSearchTests real-corpus arm livecorpus

- Date: 2026-10-12
- Kind: child
- Concern: `DanglingCommitSearchTests.test_07_real_corpus_arm_conditional` reads THIS repository's live git object store and history (cwd checkout, commit `0abc01d9`, id6 `8u6770`) but carries no `livecorpus` marker, so it runs in the default fast suite and its verdict depends on live repo state rather than on the code under test.
- Scope: add `@pytest.mark.livecorpus` (and the `import pytest` it needs) to that one test method in `tests/test_runner_shared.py`; no production code changes.
- Scope-Paths: tests/test_runner_shared.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: jzeeky verified (set m88gwh, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-verified at HEAD d795acb85: test body and conditions as F1 states, 0abc01d9 present and not an ancestor of main, test passes, tests 01-06 hermetic, no pytest import in the file.

- 2026-10-12 draft (agent): created.
- 2026-10-12 to-review (agent): authored review-ready from backlog m88gwh.

## Goal

Deselect the live-corpus-dependent test `DanglingCommitSearchTests.test_07_real_corpus_arm_conditional` from the default fast suite by marking it `livecorpus`, so a lane's integration gate is not decided by the state of this repository's own git history, while it still runs in `make test-all` and release-review.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Mark the test

- [x] E-01 In `tests/test_runner_shared.py`, add `import pytest` if it is not already imported, as its own third-party group after `from unittest import mock` and before `from agent_workflows import ...` (the grouping `tests/test_verbose_flag_reach.py` uses), and decorate `DanglingCommitSearchTests.test_07_real_corpus_arm_conditional` with `@pytest.mark.livecorpus`, preceded by a short comment stating why (it reads this repository's live git objects and history via `pathlib.Path.cwd()`), mirroring the comment style used beside `@pytest.mark.livecorpus` in `tests/test_verbose_flag_reach.py`. The comment must also name what keeps the fast suite covered (the hermetic tests 01-06 in the same class) and that it still runs in `make test-all`. Do not change the test body, its skip conditions, or any other test.
  - Depends on: none
  - Expected outcome: the test method carries the `livecorpus` marker; no other test or production file changes.
  - Execution state: performed

### Task group 2: Verify selection behavior

- [x] E-02 Run the bare default suite (`python3 -m pytest`) once BEFORE E-01 as a baseline and once after it, and a marker-selected run (`python3 -m pytest -o addopts="" -m livecorpus tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional -rs -v`) and record both outputs.
  - Depends on: E-01
  - Expected outcome: the default run deselects the test and shows the same failing-test set as a bare baseline run taken on the tree as found before E-01 (re-derive it; do not fix, skip, or deselect other parties' failures); the marker-selected run collects exactly that one test, which passes or skips by its own conditional logic.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `pyproject.toml` declares the `livecorpus` marker (text beginning "livecorpus: asserts a property over EVERY artifact in this repository's own .aw/records/ tree") and `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, so a marked test is deselected by default and still runs under `make test-all` (Makefile comment "`-m \"\"` clears the default `not slow and not livecorpus` filter").
- Precedent: `tests/test_verbose_flag_reach.py` applies `@pytest.mark.livecorpus` to a method of a `unittest.TestCase` subclass with an explanatory comment, so pytest markers on TestCase methods are an established pattern here.
- `tests/test_runner_shared.py` currently imports `unittest` but not `pytest` (import block near "from typing import Any").
- AGENTS.md repo-local rule: run the suite bare as `python3 -m pytest`; use `-o addopts=""` for narrowed runs.
- MARKER FIT: the `livecorpus` marker text in `pyproject.toml` describes tests asserting over `.aw/records/`, while test 07 reads the git object store and the `main` ref. Its stated operational reason applies unchanged (a test whose verdict depends on live repository state can red a lane's merge-and-revalidate gate for every concurrent lane), and backlog `m88gwh` prescribes this marker, so it is used as is. The marker text is NOT amended here (that would change a shared contract for one test); `tests/livecorpus_notice.py` only observes `.aw/records/` reads and is unaffected.
- Sibling plan `vzk1iw` (to-review) also declares `tests/test_runner_shared.py` (it adds a test beside `CrossHostReadIdReExportTests`); the sites are disjoint and the runner isolates each item's worktree, so no `- Item-Dependencies:` edge is needed.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | `test_07_real_corpus_arm_conditional` uses `repo_path = pathlib.Path.cwd()` and runs `git cat-file -e 0abc01d9` / `git merge-base --is-ancestor 0abc01d9 main`, then calls `runner_shared.find_dangling_commits_by_subject(repo_path, "8u6770")`. Its outcome depends on the live checkout's object store and `main` tip. | Method body in `DanglingCommitSearchTests` |
| F2 | It carries no marker, so it runs in the default fast suite, i.e. inside every lane's merge-and-revalidate gate, where the live repo can flip it: it SKIPS when `0abc01d9` is absent or reachable from `main`, and FAILS when the object exists, is unreachable from `main`, yet is reachable from some other ref or reflog (so `git fsck --connectivity-only` does not report it dangling). Re-measured at review: object present, not an ancestor of `main`, no ref contains it, test passes in 1.18s. | absence of `pytest.mark` on the method; `addopts` filter; `git merge-base --is-ancestor 0abc01d9 main` -> 1 |
| F3 | The synthetic-repo tests 01-06 in the same class already cover `find_dangling_commits_by_subject` behavior hermetically, so deselecting test 07 by default loses no fast-suite behavioral coverage. | sibling methods using `_make_repo` |

## Proposed changes (ordered, validatable)

1. E-01: add `import pytest` and `@pytest.mark.livecorpus` with an explanatory comment on the one method.
2. E-02: demonstrate default deselection and marker selection.

## Deferred / out of scope (with reason)

- Auditing other tests in the repo for missing `livecorpus` markers: not requested by backlog m88gwh; would broaden scope.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Changing the test's assertions or conditional skip logic: the backlog item asks only for the marker.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

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
- Owner: plan author
- Resolution or deferral rationale: No. Its purpose is to check the real-corpus arm (an actual unreachable commit in this repository), which cannot be made hermetic without becoming a duplicate of tests 01-06; the backlog item prescribes the marker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff -- tests/test_runner_shared.py` showing `import pytest` (if newly added) and `@pytest.mark.livecorpus` directly above `def test_07_real_corpus_arm_conditional`, plus pasted `git diff --name-only` output listing only `tests/test_runner_shared.py`.
  - Observed evidence:
    `git diff -- tests/test_runner_shared.py`:
    ```diff
    diff --git a/tests/test_runner_shared.py b/tests/test_runner_shared.py
    index 73280d7ad..38dd5c694 100644
    --- a/tests/test_runner_shared.py
    +++ b/tests/test_runner_shared.py
    @@ -45,6 +45,8 @@ import unittest
     from typing import Any
     from unittest import mock

    +import pytest
    +
     from agent_workflows import agy_runipd, oc_runipd, runner_shared

     sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    @@ -5912,6 +5914,11 @@ class DanglingCommitSearchTests(unittest.TestCase):
                     subjects,
                 )

    +    # Deselected from the default fast suite via @pytest.mark.livecorpus because it reads
    +    # this repository's live git objects and history via pathlib.Path.cwd().
    +    # Its behavioral contract is covered in the fast suite by the hermetic tests 01-06 in the
    +    # same class. Still run in make test-all.
    +    @pytest.mark.livecorpus
         def test_07_real_corpus_arm_conditional(self):
             """(7) Conditional real-corpus search: if 0abc01d9 resolves and is unreachable, 8u6770 search finds it."""
             import subprocess
    ```
    `git diff --name-only`:
    ```
    tests/test_runner_shared.py
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted summary lines of the bare `python3 -m pytest` baseline (before E-01) and post-edit runs, with the failing-test set identical by name (none expected) and the passed count not lower except by the one deselected test, and pasted output of the `-m livecorpus ... -k test_07_real_corpus_arm_conditional -rs -v` run showing exactly one collected test with PASSED or SKIPPED (with skip reason); plus pasted `python3 -m pytest -o addopts="" -m "not slow and not livecorpus" tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional` output showing 1 deselected and 0 selected (pytest exit code 5, `no tests ran`, is the expected outcome and is pasted).
  - Observed evidence:
    1. Bare baseline run summary (`python3 -m pytest`):
    ```
    NOTE: 291 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    8053 passed, 4 skipped, 18 xfailed, 3 warnings in 747.86s (0:12:27)
    ```
    2. Bare post-edit run summary (`python3 -m pytest`):
    ```
    NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    8052 passed, 4 skipped, 18 xfailed, 3 warnings in 1019.03s (0:16:59)
    ```
    Both runs had 0 failures. The passed count decreased by exactly 1 (8053 -> 8052) and deselected count increased by exactly 1 (291 -> 292).

    3. Marker-selected run (`python3 -m pytest -o addopts="" -m livecorpus tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional -rs -v`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3277860873
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 1 item                                                              collected 136 items / 135 deselected / 1 selected

    tests/test_runner_shared.py::DanglingCommitSearchTests::test_07_real_corpus_arm_conditional PASSED [100%]

    NOTE: 135 tests were deselected by -m/-k and did not run (filtered by marker expression: 'livecorpus', and -k/--deselect also contributed)
    ====================== 1 passed, 135 deselected in 6.17s =======================
    ```
    Exactly one collected test was run and PASSED.

    4. Deselection check (`python3 -m pytest -o addopts="" -m "not slow and not livecorpus" tests/test_runner_shared.py -k test_07_real_corpus_arm_conditional`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3333543047
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 1 item                                                              collected 136 items / 136 deselected / 0 selected

    NOTE: 136 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus', and -k/--deselect also contributed); run everything with: make test-all
    =========================== 136 deselected in 1.05s ============================
    ```
    Exit code 5 (`no tests ran`), 136 deselected, 0 selected.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 is resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Start with `aw ipd begin`. Commit only through `aw commit jzeeky -- tests/test_runner_shared.py` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize`. Never hand-roll the move or `git mv` this plan into `executed/`; it happens only after `aw ipd lint --phase pre-transition` conforms and V-01 and V-02 record concrete pasted evidence with Result: pass. Release gate: this plan carries `- Blocks-Release: next` inherited from backlog `m88gwh`; keep it, and let the item close through the handoff route (this plan executed with `- From-Backlog: m88gwh`), not by hand.
