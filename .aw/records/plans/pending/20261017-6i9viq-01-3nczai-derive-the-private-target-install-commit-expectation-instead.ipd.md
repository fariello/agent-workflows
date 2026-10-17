# IPD: Derive the private-target install commit expectation instead of hard-coding a file count

- Date: 2026-10-17
- Kind: child
- Concern: `tests/test_clean_target_config_home.py` method `test_case_l_tracked_install_still_writes_target` asserts a literal file count (`self.assertIn("358 files changed", tail)`) on the commit a `private-target -y` install makes. The count is the size of the shipped payload, so every added or removed workflow asset breaks the test with no behavior change. It has already been bumped once (commit a75488af5 changed "357" to "358"), backlog `6i9viq` and the duplicate backlog `ioegmo` were both filed for the same breakage, and it will recur on the next payload change.
- Scope: IN: replace the literal count assertion in `test_case_l_tracked_install_still_writes_target` with assertions derived from the install's own observable result (the commit contains exactly the files the install left tracked in the target, the worktree is clean afterwards, and the commit is non-empty). OUT: any change to the installer, the payload, or other test cases; closing backlog `ioegmo` (a separate item; noted for the reviewer below).
- Scope-Paths: tests/test_clean_target_config_home.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 6i9viq
- Blocks-Release: next
- Set: 6i9viq
- Order: 1
- Highest E allocated: 02
- Author: opencode
- Id: 3nczai

## Workflow history

- 2026-10-17 draft (opencode): created.
- 2026-10-17 to-review (opencode): authored review-ready from backlog 6i9viq.

## Goal

Make test case (l) verify what actually matters about a tracked `private-target -y` install (it commits everything it wrote, and nothing is left uncommitted) without pinning the payload size, so the test stops failing every time a workflow file is added or removed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Replace the pinned count with derived assertions

- [ ] E-01 In `test_case_l_tracked_install_still_writes_target`, remove the `git show --stat` tail parse and the literal `"358 files changed"` assertion. Replace them with: (a) `git show --name-only --format= HEAD` gives the set of paths the install commit touched; (b) `git ls-files` in the target, minus the pre-existing `README.md`, gives the set of tracked installed paths; assert (a) equals (b); (c) assert that set is non-empty and contains `AGENTS.md` and `.aw/.gitignore`; (d) assert `git status --porcelain` in the target is empty, so the install left nothing staged or untracked outside the commit. Keep every other existing assertion in the method unchanged.
  - Depends on: none
  - Expected outcome: the method contains no hard-coded file count, and its assertions are all computed from the target repository's git state after the install.
  - Execution state: pending

### Task group 2: Prove the test still detects a broken commit

- [ ] E-02 Run the modified test and the full module, then demonstrate the new assertions are not vacuous: temporarily (uncommitted, reverted before commit) make the test see a partial commit, for example by running `git rm --cached -q AGENTS.md && git commit -qm drop` in the target before the assertions, confirm the test fails on the set-equality or clean-status assertion, then revert the temporary edit.
  - Depends on: E-01
  - Expected outcome: the real test passes; the deliberately broken variant fails with an assertion error naming the mismatch; the temporary edit is absent from the final diff.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests must assert on real outputs, exit codes, and side effects. The replacement assertions read the target repo's git state produced by actually running `aw install`, which satisfies this; a literal payload size is an implementation detail of the shipped asset set, not an outcome of the behavior under test.
- The routine gate is bare `python3 -m pytest`; narrowed per-test runs use `python3 -m pytest -o addopts="" <path> -k <name>` (AGENTS.md, repository development contract).
- Commits go through `aw commit <plan> -- <paths>`; never push.
- The test drives the CLI through the class helper `self._run_aw(...)` and git through `subprocess.run(..., cwd=str(target))`; the new assertions follow the same pattern.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The assertion pins the payload size. | `test_case_l_tracked_install_still_writes_target` ends with `self.assertIn("358 files changed", tail)` where `tail` is the last line of `git show --stat --format= HEAD`. |
| F2 | The count has already drifted once. | `git log -L` on that line: introduced as "357" in 9ca816dba (3m8aix), changed to "358" in a75488af5 (ki6t17). |
| F3 | The backlog item's stated failure is already masked at the current tip, but the defect (a pinned count) remains. | In this worktree `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l` reports `1 passed`, because a75488af5 bumped the literal. Any further payload change re-breaks it. |
| F4 | A duplicate backlog item exists for the same breakage. | `.aw/records/backlog/open/20261016-ioegmo-01-ioegmo-test-clean-target-config-home-pins-stale-357-files.backlog.md` ("pins stale 357 files changed count broken by askme rationale.md"). |
| F5 | The intent of the count was "the install commit captures the installed tree", which can be checked directly. | The method's docstring: "tracked private-target install still writes target, commits under -y, and matches baseline". |

## Proposed changes (ordered, validatable)

1. E-01: rewrite the tail of `test_case_l_tracked_install_still_writes_target` to compare the install commit's path set with the tracked installed path set and assert a clean worktree. Validated by V-01.
2. E-02: run the test and module, and prove a broken commit is caught. Validated by V-02.

## Deferred / out of scope (with reason)

- Backlog `ioegmo` describes the same defect. Closing or de-duplicating it is a backlog decision for the maintainer and is outside this plan's scope fence; this plan's fix would satisfy it, which a reviewer may cite as evidence when closing it.
- No installer or payload change: the installer behavior is correct; only the test is wrong.

## Scope check

- Over-scope: none.
- Under-scope: none. The only failing surface named by the backlog item is the single literal in this one method; no other test in `tests/` asserts a "files changed" count (`grep -rn "files changed" tests/` finds only this line and an unrelated comment in `tests/test_status_set.py`).

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l` passes (V-01).
- `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py` passes (V-02).
- A deliberately partial commit makes the test fail (V-02).
- The routine gate `python3 -m pytest` passes (V-02).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes the install commit's file count.

## Open questions

None. The remedy follows from AGENTS.md's outcome-testing rule and the test's own docstring; no decision needs the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- tests/test_clean_target_config_home.py` showing the literal `"358 files changed"` removed and the path-set and clean-status assertions added; paste `grep -n "files changed" tests/test_clean_target_config_home.py` returning no match; paste the actual output of `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l` showing `1 passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual failing output (the assertion error line) of the temporarily broken variant created in E-02; paste the actual output of `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py` with the `N passed` summary and zero failures after reverting; paste the `N passed` summary line of a bare `python3 -m pytest`; paste `git diff --cached --name-only` at commit time listing only `tests/test_clean_target_config_home.py` (plus this plan file).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- After every V-item reads `pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` through the tooled lifecycle.
