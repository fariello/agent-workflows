# IPD: Eliminate hardcoded file count in test_case_l and verify derived assertions

- Date: 2026-10-17
- Kind: child
- Concern: In `tests/test_clean_target_config_home.py`, method `test_case_l_tracked_install_still_writes_target` previously asserted a literal file count (`358 files changed`) on the commit created by `aw install . --preset private-target -y`. Because this hardcoded number equals the exact count of shipped payload files, any expansion or change to the workflow system bundle (such as adding workflow documentation or assets) caused the test to break even though installer behavior was completely correct.
- Scope: In `tests/test_clean_target_config_home.py`, eliminate the hardcoded file count check from `test_case_l_tracked_install_still_writes_target` and ensure it uses a resilient, derived assertion verifying that the install commit captures exactly the set of installed and tracked files (with required anchors `AGENTS.md` and `.aw/.gitignore` present and a clean git working tree). Validate that the test passes and remains sensitive to omitted files or stray untracked files via negative/mutation verification.
- Scope-Paths: tests/test_clean_target_config_home.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 96lj37
- Blocks-Release: next
- Set: 96lj37
- Order: 1
- Highest E allocated: 02
- Author: Antigravity
- Id: rg7rnx

## Workflow history

- 2026-10-17 draft (Antigravity): created.
- 2026-10-17 to-review (Antigravity): authored review-ready from backlog 96lj37.

## Goal

Ensure `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target` asserts observable behavioral outcomes (the commit captures all tracked installed files, contains required anchor files, and leaves a clean git working tree) rather than a brittle hardcoded file count, preventing spurious test failures when system bundle assets change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Verify test_case_l eliminates the hardcoded file count and uses derived path-set assertions

- [ ] E-01 In `tests/test_clean_target_config_home.py`, confirm that `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target` contains no hardcoded file count literal (such as "358 files changed") and asserts derived git properties: (a) `commit_paths` from `git show --name-only --format= HEAD`, (b) `tracked_paths` from `git ls-files` minus `README.md`, (c) `self.assertEqual(commit_paths, tracked_paths)`, (d) `commit_paths` is non-empty and contains `AGENTS.md` and `.aw/.gitignore`, and (e) `git status --porcelain` is empty. If the file diverges or still contains a hardcoded count, edit the test to remove the literal and apply the derived assertions.
  - Depends on: none
  - Expected outcome: `tests/test_clean_target_config_home.py` contains no hardcoded "files changed" count, and case (l) asserts that all installed tracked paths match the install commit with a clean working tree.
  - Execution state: pending

### Task group 2: Validate behavioral pass and sensitivity proof

- [ ] E-02 Run `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l` and the entire module `tests/test_clean_target_config_home.py`. Demonstrate sensitivity of the derived assertions by verifying that temporary mutations produce expected failures: (1) dropping a committed path (e.g., cached removal of `AGENTS.md`) fails `assertEqual(commit_paths, tracked_paths)`, and (2) introducing an untracked file (e.g., writing `stray.txt`) fails the clean status assertion `assertEqual(status, "")`. Verify all temporary edits are reverted and run the test suite.
  - Depends on: E-01
  - Expected outcome: `test_case_l` passes; both temporary mutations fail with their respective assertion errors; the test file is clean after reverting mutations; test suite passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests must assert on real outputs, exit codes, and side effects. The replacement assertions read the target repo's git state produced by actually running `aw install`, which satisfies this; a literal payload size is an implementation detail of the shipped asset set, not an outcome of the behavior under test.
- The routine gate is bare `python3 -m pytest`; narrowed per-test runs use `python3 -m pytest -o addopts="" <path> -k <name>` (AGENTS.md, repository development contract).
- Commits go through `aw commit <plan> -- <paths>`; never push.
- The test drives the CLI through the class helper `self._run_aw(...)` and git through `subprocess.run(..., cwd=str(target))`; the derived assertions follow the same pattern.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The assertion previously pinned payload size literally. | Before commit `84cba788cd58ece72756a63042700308ffeab6e5`, `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target` ended with `self.assertIn("358 files changed", tail)`. |
| F2 | The count drifted multiple times as files were added. | Introduced as "357" in commit `9ca816dba5c8e51e32e22b2faef9d37c702a68cf` (plan `3m8aix`), bumped to "358" in commit `a75488af518290645266f8d6792be348e263bf2d` (plan `ki6t17`). Backlog items `6i9viq`, `ioegmo`, and `96lj37` were filed when bundle changes broke the count. |
| F3 | Derived path-set assertions replace the fragile literal count. | Commit `84cba788cd58ece72756a63042700308ffeab6e5` implemented path set comparison between `git show --name-only --format= HEAD` and `git ls-files` (excluding `README.md`), plus verifying non-empty anchor files (`AGENTS.md`, `.aw/.gitignore`) and empty porcelain status. |
| F4 | The test was temporarily quarantined with xfail in lane vgus66, then reactivated in plan 3nczai. | Commit `24e4c39cc` added `@pytest.mark.xfail(strict=False, reason="bug: 96lj37 - hardcodes file count")` which was removed during execution of plan `3nczai` so the test actively executes and validates. |
| F5 | The only "files changed" literal in the test tree was in this method. | Running `grep -rn "files changed" tests/` finds no numeric count assertions in the test suite. |

## Proposed changes (ordered, validatable)

1. E-01: Confirm `tests/test_clean_target_config_home.py` contains no hardcoded count and verifies derived git path sets and clean porcelain status (editing only on divergence). Validated by V-01.
2. E-02: Run `test_case_l` and the full test module, and verify mutation sensitivity against partial commit and stray file. Validated by V-02.

## Deferred / out of scope (with reason)

- Other test cases in `tests/test_clean_target_config_home.py` or other test files: only `test_case_l_tracked_install_still_writes_target` asserted a hardcoded file count; other test cases test independent clean-target and configuration behaviors and do not assert on installed bundle file counts.
  - Carrier-Declined: single-site test defect in test_case_l; other test cases do not pin payload file counts
- Installer runtime or system bundle payload changes: the installer and workflow system bundle operate as intended; this defect is purely a brittle test assertion.
  - Carrier-Declined: installer and workflow bundle behaviors are correct; test-only scope
- Closing duplicate backlog item `ioegmo` or its plan `im4afa`: `ioegmo` is a separate backlog item graduated to plan `im4afa`; closing or retiring duplicate items is a maintainer decision outside this plan's scope fence.
  - Carrier-Declined: duplicate backlog item ioegmo is tracked separately and graduated to plan im4afa

## Scope check

- Over-scope: none. Changes and verification are strictly confined to `tests/test_clean_target_config_home.py`.
- Under-scope: none. The only failing surface named in backlog `96lj37` is the hardcoded file count in `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l` passes (V-01).
- `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py` passes (V-02).
- Deliberate partial commit mutation fails set equality assertion (V-02).
- Deliberate stray untracked file mutation fails clean porcelain status assertion (V-02).
- Routine gate `python3 -m pytest` passes (V-02).

## Spec / documentation sync

N/A: test-only change; no user-facing documentation or specification defines the exact count of files written by private-target installs.

## Open questions

None. The remedy follows the project's behavioral outcome-testing convention in AGENTS.md; no open decisions require maintainer input.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- tests/test_clean_target_config_home.py` (empty unless E-01 found divergence, in which case paste corrective diff and rationale); paste `git show 84cba788c -- tests/test_clean_target_config_home.py` showing landed derived assertions; paste `grep -n "files changed" tests/test_clean_target_config_home.py` returning no match; paste actual output of `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l` showing `1 passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for EACH of the two mutation variants in E-02, paste the actual `AssertionError` lines showing which assertion failed (set equality for partial commit; empty porcelain status for stray file); paste `git status --short tests/test_clean_target_config_home.py` showing clean working tree after reverting mutations; paste output of `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py` with passing summary; paste passing summary line of bare `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; modifications are strictly confined to `tests/test_clean_target_config_home.py`.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit rg7rnx -- <this plan> [tests/test_clean_target_config_home.py only if E-01 edited it]`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Post-gate lifecycle: after every V-item reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan moves to `executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize rg7rnx`, passing `--scope-ack tests/test_clean_target_config_home.py` when E-01 needed no edit. Never `git mv` the plan by hand. This plan carries `- Blocks-Release: next` inherited from backlog `96lj37`.
