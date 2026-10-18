# IPD: Eliminate hardcoded file count in test_case_l and verify derived assertions

- Date: 2026-10-17
- Kind: child
- Concern: In `tests/test_clean_target_config_home.py`, method `test_case_l_tracked_install_still_writes_target` previously asserted a literal file count (`358 files changed`) on the commit created by `aw install . --preset private-target -y`. Because this hardcoded number equals the exact count of shipped payload files, any expansion or change to the workflow system bundle (such as adding workflow documentation or assets) caused the test to break even though installer behavior was completely correct.
- Scope: In `tests/test_clean_target_config_home.py`, eliminate the hardcoded file count check from `test_case_l_tracked_install_still_writes_target` and ensure it uses a resilient, derived assertion verifying that the install commit captures exactly the set of installed and tracked files (with required anchors `AGENTS.md` and `.aw/.gitignore` present and a clean git working tree). Validate that the test passes and remains sensitive to omitted files or stray untracked files via negative/mutation verification.
- Scope-Paths: tests/test_clean_target_config_home.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
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

- 2026-10-18 reviewed (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-17 draft (Antigravity): created.
- 2026-10-17 to-review (Antigravity): authored review-ready from backlog 96lj37.

## Goal

Ensure `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target` asserts observable behavioral outcomes (the commit captures all tracked installed files, contains required anchor files, and leaves a clean git working tree) rather than a brittle hardcoded file count, preventing spurious test failures when system bundle assets change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Verify test_case_l eliminates the hardcoded file count and uses derived path-set assertions

- [ ] E-01 In `tests/test_clean_target_config_home.py`, confirm that `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target` contains no hardcoded file count literal (such as "358 files changed"), carries no `@pytest.mark.xfail` quarantine, and asserts derived git properties: (a) `commit_paths` from `git show --name-only --format= HEAD`, (b) `tracked_paths` from `git ls-files` minus `README.md`, (c) `self.assertEqual(commit_paths, tracked_paths)`, (d) `commit_paths` is non-empty and contains `AGENTS.md` and `.aw/.gitignore`, and (e) `git status --porcelain` is empty; and that every earlier assertion of the method (`returncode == 0`, HEAD moved, `AGENTS.md`/`.aw/.gitignore`/backups exist, the `Git: changes staged; commit offered below` line) is still present. At review (HEAD `a84e38df4`) all of this already holds: the literal was removed by commit `84cba788c` and the xfail by `baf8f38c0` (plan `3nczai`, executed). If the method at execution time diverges, edit it to match and say so in V-01; otherwise make no edit to the test file.
  - Depends on: none
  - Expected outcome: `tests/test_clean_target_config_home.py` contains no hardcoded "files changed" count, and case (l) asserts that all installed tracked paths match the install commit with a clean working tree.
  - Execution state: pending

### Task group 2: Validate behavioral pass and sensitivity proof

- [ ] E-02 Run `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l` and the entire module `python3 -m pytest -o addopts="" -n 6 tests/test_clean_target_config_home.py`. Then demonstrate the derived assertions are not vacuous with two temporary, uncommitted edits to the method, each inserted immediately after the `self.assertIn("Git: changes staged; commit offered below", res.stdout)` line, run with the `-k test_case_l` command, and reverted with `git checkout -- tests/test_clean_target_config_home.py` before the next: (1) a partial commit, `subprocess.run(["git", "rm", "--cached", "-q", "AGENTS.md"], cwd=str(target), check=True)` followed by `subprocess.run(["git", "commit", "-qm", "drop"], cwd=str(target), check=True)`, which must fail `self.assertEqual(commit_paths, tracked_paths)`; (2) a stray file, `(target / "stray.txt").write_text("x", encoding="utf-8")`, which leaves the commit and tracked sets equal and must fail ONLY `self.assertEqual(status, "")`. Finally run the bare routine gate `python3 -m pytest`.
  - Depends on: E-01
  - Expected outcome: `test_case_l` and every other test in the module pass; variant (1) fails with an `AssertionError` from the set-equality assertion and variant (2) from the clean-status assertion; `git status --short tests/test_clean_target_config_home.py` is empty afterwards; the routine gate reports no failures.
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
| F4 | The test was temporarily quarantined with xfail, then reactivated by plan 3nczai. | Commit `e376b85ae` ("chore(testprune): ... quarantine pre-existing bugs denczr and 96lj37"; integrated to main by merge `24e4c39cc`, lane `vgus66`) added `@pytest.mark.xfail(strict=False, reason="bug: 96lj37 - hardcodes file count")`; commit `baf8f38c0` (`work(3nczai)`) removed it and the then-unused `import pytest`. |
| F5 | No other test pins the private-target payload size. | `grep -rn "files changed" tests/` at review finds one other numeric literal, `assert "20 files changed" in commit_stat` in `tests/test_question_drain.py`; that count is the number of artifacts the test itself creates, a fixture-controlled outcome, not the shipped bundle size, so it is out of this plan's scope. |
| F6 | This plan duplicates already-executed work. | Plan `3nczai` (Set `6i9viq`, `.aw/records/plans/executed/`, `- Status: executed`) performed the identical verify-and-mutation-probe E-01/E-02 on the same method and recorded both mutation failures in its V-02. The method is unchanged since `baf8f38c0`. Executing this plan re-confirms that state and, as `96lj37`'s `From-Backlog` carrier with the same `Blocks-Release: next`, lets `96lj37` close through the HANDOFF route. |

## Proposed changes (ordered, validatable)

1. E-01: Confirm `tests/test_clean_target_config_home.py` contains no hardcoded count and verifies derived git path sets and clean porcelain status (editing only on divergence). Validated by V-01.
2. E-02: Run `test_case_l` and the full test module, and verify mutation sensitivity against partial commit and stray file. Validated by V-02.

## Deferred / out of scope (with reason)

- Other test cases in `tests/test_clean_target_config_home.py` or other test files: only `test_case_l_tracked_install_still_writes_target` asserted a hardcoded file count; other test cases test independent clean-target and configuration behaviors and do not assert on installed bundle file counts.
  - Carrier-Declined: single-site test defect in test_case_l; other test cases do not pin payload file counts
- Installer runtime or system bundle payload changes: the installer and workflow system bundle operate as intended; this defect is purely a brittle test assertion.
  - Carrier-Declined: installer and workflow bundle behaviors are correct; test-only scope
- Retiring this plan as superseded by `3nczai` instead of executing it (then closing `96lj37` with `aw backlog set done 96lj37 --evidence <executed 3nczai plan path>`): a lifecycle act outside a review, recorded as review decision D-1; execution is the self-contained path.
  - Carrier-Declined: executing this plan is itself the carrier that closes 96lj37's gate
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
  - Required evidence: paste `git diff -- tests/test_clean_target_config_home.py` (empty unless E-01 found divergence, in which case paste corrective diff and rationale); paste the current text of `test_case_l_tracked_install_still_writes_target` from the `commit_paths = set(` line through `self.assertEqual(status, "")` showing assertions (a)-(e); paste `grep -n "files changed\|xfail" tests/test_clean_target_config_home.py` returning no match; paste actual output of `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l -v` showing `test_case_l_tracked_install_still_writes_target PASSED` (not `XPASS`/`XFAIL`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for EACH of the two mutation variants in E-02, paste the actual `AssertionError` lines showing which assertion failed (set equality for partial commit; empty porcelain status for stray file); paste `git status --short tests/test_clean_target_config_home.py` showing clean working tree after reverting mutations; paste the summary line of `python3 -m pytest -o addopts="" -n 6 tests/test_clean_target_config_home.py` showing zero failures; paste the summary line of bare `python3 -m pytest` showing zero failures; paste `git diff --cached --name-only` at commit time listing only this plan's paths.
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
