# IPD: Stop aw uninstall calling the framework's own regenerable workflow-artifacts README unrecoverable

- Date: 2026-09-26
- Kind: child
- Concern: `aw uninstall` WARNS THAT CONTENT IS UNRECOVERABLE WHEN THE USER HAS COMMITTED EVERYTHING. `engine.plan_deep_cleanup` walks `_DEEP_CLEANUP_ROOTS` (which includes `.aw/workflow-artifacts`) and appends every file for which `engine._git_file_state` returns `at_risk`; `_git_file_state` returns `at_risk` for any path that is not git-tracked. The installer's own `ensure_workflow_artifacts_readme` writes `.aw/workflow-artifacts/README.md` and deliberately never stages it (D92: run scratch is never committed), and the framework-owned `.aw/.gitignore` ignores the tree (`/workflow-artifacts/`). So after install + `git add -A` + commit, `plan.at_risk == ['.aw/workflow-artifacts/README.md']` and `plan.all_recoverable is False`. WHICH SURFACES ACTUALLY WARN, corrected at review by driving the real CLI on a committed install (this plan formerly said `--deep`, which is the one invocation that prints NOTHING): (a) `aw uninstall <repo> --dry-run` prints `! 1 of these are NOT recoverable from git (untracked/uncommitted)` under `deeper cleanup (offered separately) WOULD remove:`, with or without `--deep`; (b) the INTERACTIVE `_offer_deep_cleanup` offer (no `--deep`, a TTY) prints `WARNING: 1 of these are NOT recoverable from git (untracked, uncommitted, or ignored). Deleting them is permanent:` followed by `! .aw/workflow-artifacts/README.md`; (c) `aw uninstall --yes --deep` prints NO such line, because it performs the cleanup without the prompt. Re-measured at HEAD `b861bb05`: `git check-ignore -v` -> `.aw/.gitignore:75:/workflow-artifacts/`; `tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` FAILS (`python3 -m pytest -o addopts="" -q tests/test_installer.py` -> `2 failed, 93 passed in 220.87s`, the sibling being `57dwkc`'s). The module is `pytestmark = pytest.mark.slow`, so a bare run never shows it. The file is regenerable: `ensure_workflow_artifacts_readme` re-creates it from `templates/workflow-artifacts-README.md` (falling back to `engine._ARTIFACTS_README_FALLBACK`).
- Scope: IN: (a) a named module constant `engine._DEEP_CLEANUP_REGENERABLE = (f"{ARTIFACTS_DIR}README.md",)` with a comment citing `3ypquf` and D92; (b) `plan_deep_cleanup` skips the at-risk classification for a path in that tuple ONLY WHEN IT IS NOT GIT-TRACKED, while STILL listing it in `plan.files`, `plan.other_files`, and `plan.counts` so `run_deep_cleanup` still removes it; (c) behavioral tests, default-visible for the classification rule and slow-marked for the real-install integration case, with negative controls for a user file in that tree, for the TRACKED-and-dirty README, and for records scratch; (d) a docstring-only correction to the now-passing `tests/test_installer.py` test (its assertions untouched); (e) one CHANGELOG line. OUT: `UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` (backlog `57dwkc`, `.aw/system/layout.json` orphaned by `_DEEP_CLEANUP_ROOTS`); changing `_git_file_state`; changing `_DEEP_CLEANUP_ROOTS`; changing any assertion in `tests/test_installer.py`; exempting any other path.
- Scope-Paths: agent_workflows/engine.py, tests/test_deep_cleanup_regenerable.py, tests/test_installer.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 3ypquf
- Blocks-Release: next
- Set: deepclean
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: baxbdh

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred, none open; 5 decisions D-1..D-5 recorded. Reviewed at HEAD b861bb05. `aw ipd lint --phase author --agent` reported `clean`/`findings: 0` before revision; the lane-input copy was byte-identical to the tracked file (sha256 `d23f13c9`) and the tree was clean, so no pre-review snapshot was taken. THE DEFECT IS REAL AND REPRODUCED EXACTLY: on a committed real install `at_risk == ['.aw/workflow-artifacts/README.md']`, `all_recoverable False`, the README in `plan.files` and `plan.other_files`, `counts['.aw/workflow-artifacts'] == 1`, `git check-ignore -v` -> `.aw/.gitignore:75:/workflow-artifacts/`, and the target's shipped template is tracked and byte-identical to the written README. FIVE SUBSTANTIVE CORRECTIONS. (1) THE BLANKET PATH EXEMPTION SILENCES A REAL WARNING: with the README git-TRACKED (a repo that installed before the ignore rule landed, a state `ensure_workflow_artifacts_readme`'s own comment says persists forever) and carrying UNCOMMITTED user edits, the plan's `rel not in _DEEP_CLEANUP_REGENERABLE` test drops it from `at_risk`, so `aw uninstall` would promise recoverability for content git cannot restore. Driven on a real install: blanket -> `[]` (SILENCED), narrowed -> `['.aw/workflow-artifacts/README.md']` (PRESERVED). E-03 now exempts only when the path is NOT tracked. (2) THE NAMED SURFACE WAS WRONG: the title and Concern said `aw uninstall --deep` warns, but `--yes --deep` prints no recoverability line at all; the warning comes from `--dry-run` and from the interactive offer. Driven and corrected. (3) EVERY TEST WAS SLOW-MARKED, so the bare run this repo's own contract judges a change by could not see the fix, which is precisely the invisibility `4vfkl1` and `xuc9v0` were filed about. The classification rule needs no install (verified on a 5-file fixture in 0.24s versus 2 to 3.4s per install), so E-04 is now default-visible and only E-05's integration case is slow-marked. (4) A NOW-PASSING TEST WOULD KEEP A DOCSTRING DECLARING ITSELF A `PRE-EXISTING FAILURE` and asking for the maintainer call this plan makes; E-06 corrects the prose with its assertions untouched. (5) HEAD `61ef21d8` was two commits stale and the `2 failed in 8.79s` evidence came from a two-node selection; both re-measured over the whole module.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 3ypquf; inherits Blocks-Release next. Authored review-ready; the at-risk classification, the gitignore rule, and the failing slow test were re-measured at HEAD 61ef21d8 on a real install. Backlog 4vfkl1 checked and recorded under Deferred as a duplicate.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw uninstall` report "all recoverable" when the user has committed everything they can commit, by not counting the framework's own never-committed, regenerable run-scratch README as user content at risk, while still removing it, still flagging any real user file in that tree, AND still flagging that same README when it IS git-tracked and carries uncommitted edits (the one state in which git genuinely cannot restore it).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. Run `python3 -m pytest -o addopts="" -q "tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed"` and paste the failure. Then, on a scratch repo built with the test module's own helpers (`tests.test_installer.init_repo`, `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)`, `git add -A`, commit), paste `engine.plan_deep_cleanup(repo).at_risk`, whether `.aw/workflow-artifacts/README.md` is in `plan.files`, and `git check-ignore -v .aw/workflow-artifacts/README.md`. If `at_risk` is already empty, STOP and report that the defect is fixed.
  - Depends on: none
  - Expected outcome: the test fails at `self.assertTrue(plan.all_recoverable, ...)`; `at_risk == ['.aw/workflow-artifacts/README.md']`; the README is in `plan.files`; check-ignore names `.aw/.gitignore` `/workflow-artifacts/`.
  - Execution state: pending

### Task group 2: exempt the regenerable file

- [ ] E-02 ADD `engine._DEEP_CLEANUP_REGENERABLE: tuple[str, ...] = (f"{ARTIFACTS_DIR}README.md",)` beside `_DEEP_CLEANUP_ROOTS`, with a comment stating the THREE-PART criterion for membership (framework-written, never committed by design, and re-created by `ensure_workflow_artifacts_readme` from the shipped template or `_ARTIFACTS_README_FALLBACK`, so deleting it loses nothing the framework cannot rebuild), citing `3ypquf` and D92, and saying that a path belongs here only if all three hold. The comment MUST also state the TRACKED CAVEAT E-03 implements and why: membership makes a path exempt only while it is UNTRACKED, because `ensure_workflow_artifacts_readme`'s own comment records that a repo which installed before the ignore rule landed "would keep the file tracked forever", and a tracked file carrying uncommitted edits holds content git cannot restore.
  - Depends on: E-01
  - Expected outcome: `engine._DEEP_CLEANUP_REGENERABLE == (".aw/workflow-artifacts/README.md",)`.
  - Execution state: pending

- [ ] E-03 CHANGE `engine.plan_deep_cleanup` so a path in `_DEEP_CLEANUP_REGENERABLE` is exempted from the at-risk classification ONLY WHEN IT IS NOT GIT-TRACKED, e.g. `if not (rel in _DEEP_CLEANUP_REGENERABLE and not git_is_tracked(repo_root, rel)) and _git_file_state(repo_root, rel) == "at_risk":` (any equivalent spelling is fine; the REQUIRED property is the four-state truth table in the expected outcome). DO NOT exempt by path alone: measured at review on a real install, a force-added README carrying uncommitted edits is dropped from `at_risk` by the path-only test, so `aw uninstall` would promise recoverability for content git cannot restore. Leave the `plan.files` / `records_files` / `other_files` appends and the `n += 1` count unchanged, so the file is still announced and removed. Update the `DeepCleanupPlan` docstring's `at_risk` sentence to say an UNTRACKED regenerable framework file is excluded.
  - Depends on: E-02
  - Expected outcome: all four states correct on a real install: untracked README -> NOT in `at_risk`; tracked + clean -> not in `at_risk` (already true, `_git_file_state` returns `recoverable`); tracked + uncommitted edits -> IS in `at_risk`; a sibling untracked user file in the same tree -> IS in `at_risk`. Plus the README still in `plan.files` and `plan.other_files`, and `plan.counts[".aw/workflow-artifacts"] >= 1`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 ADD `tests/test_deep_cleanup_regenerable.py` with the CLASSIFICATION-RULE cases, DEFAULT-VISIBLE (NO module-level `pytest.mark.slow`), behavioral only (maintainer's 2026-09-26 ruling: no source-text pins). These must NOT perform an install: build a minimal fixture repo by hand (`git init`, a `.aw/.gitignore` containing `/workflow-artifacts/`, the README, one `.aw/records/README.md`, commit) so the fix is visible to the BARE `python3 -m pytest` the execution contract judges a change by. Measured at review: such a fixture costs about 0.24s for five scenarios against 2 to 3.4s for one real install. Four cases, each asserting on `plan_deep_cleanup(repo).at_risk` and `all_recoverable`: (1) untracked ignored README -> `at_risk == []` and `all_recoverable is True`; (2) NEGATIVE CONTROL, a sibling untracked `.aw/workflow-artifacts/my-notes.md` -> IS in `at_risk` and the README is still absent from it; (3) NEGATIVE CONTROL, README `git add -f`'d and committed then edited -> IS in `at_risk` (this is the case a path-only exemption silences); (4) NEGATIVE CONTROL, an uncommitted `.aw/records/README.md` edit -> still at-risk.
  - Depends on: E-03
  - Expected outcome: 4 cases pass after E-03; case (1) FAILS before it; cases (2) to (4) pass before and after (controls). They appear in a BARE `python3 -m pytest` run.
  - Execution state: pending

- [ ] E-05 ADD to the same file a SEPARATE class carrying a class-scoped `pytestmark = pytest.mark.slow` (verified at review to deselect per class under `-m 'not slow'` while leaving sibling classes default-visible) holding the REAL-INSTALL integration case, because only a real install proves the shipped installer plus the shipped `.aw/.gitignore` produce the exempt state. On a committed real install (`tests.test_installer.init_repo`, `engine.install_into_repo(..., yes=True, no_color=True)`, `git add -A`, commit): (a) `all_recoverable is True` and `at_risk == []`; (b) the README is in `plan.files` and in `plan.other_files`, and `counts[".aw/workflow-artifacts"] >= 1`; (c) `run_deep_cleanup(repo, plan, use_git=True)` removes `.aw/workflow-artifacts/README.md` from disk.
  - Depends on: E-03
  - Expected outcome: passes under `-o addopts=""` and is DESELECTED by the bare run; (a) fails before E-03.
  - Execution state: pending

- [ ] E-06 CORRECT the docstring of `tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed`, whose prose declares itself a `PRE-EXISTING FAILURE`, says the expectation may need to change, and asks for "a maintainer call about `agent_workflows/`" that this plan makes. Replace that paragraph with one sentence recording that the product answered it (`_DEEP_CLEANUP_REGENERABLE` in `engine.plan_deep_cleanup`, plan `baxbdh`, backlog `3ypquf`). DO NOT touch a single assertion, the test body, or any other test in the module: the whole point is that it passes AS WRITTEN. Re-run the node UNMODIFIED first and paste it passing before editing the prose.
  - Depends on: E-03
  - Expected outcome: `git diff tests/test_installer.py` shows docstring lines only (no `assert`, no `self.assert*`, no body line), and the node passes both before and after the docstring edit.
  - Execution state: pending

- [ ] E-07 ADD one `- Fixed:` line to the `## 2.0.0 (pending)` section of `CHANGELOG.md`, in USER-FACING prose with no em or en dashes: `aw uninstall` previously warned that deleting the leftover scaffolding was permanent and unrecoverable even when the user had committed everything they could commit, because it counted its own run-scratch README (a file it writes, never commits, and can always write again) as content at risk. That file no longer counts. It is still listed and still removed, any other file you put in that folder is still flagged, and the README itself is still flagged in the one case where git cannot bring it back.
  - Depends on: E-03
  - Expected outcome: exactly one added line under the 2.0.0 heading; `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` prints nothing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- D92 / wfartifacts: `.aw/workflow-artifacts/` is local run scratch, never committed, ignored by the framework-owned `.aw/.gitignore` with `/workflow-artifacts/`; `ensure_workflow_artifacts_readme` is "DELIBERATELY NOT STAGED (wfartifacts Order 01 / gzhd7t, decision D-01)".
- The README has ONE fallback, `engine._ARTIFACTS_README_FALLBACK`, used when the template cannot be read, so the file is always regenerable.
- `_DEEP_CLEANUP_ROOTS` lists `.aw/workflow-artifacts` as non-records "OTHER" scaffolding, removed even under `--keep-records` (its comment). This plan does not change that.
- `_git_file_state` is deliberately loud ("anything uncertain is \"at_risk\""); the exemption is a named, reviewed list in the caller rather than a softening of that function.
- `tests/test_installer.py` is module-marked slow (`pytestmark = pytest.mark.slow`), and `pyproject.toml` `addopts` carries `-m 'not slow'`, so the evidence for this plan must use `-o addopts=""` or `-m slow` in addition to the bare run. THAT IS A COST, NOT A MODEL TO COPY: backlog `4vfkl1` and `xuc9v0` both exist because the slow subset can accumulate real regressions invisibly, and plan `4petcj` (approved) is making the slow set visible in CI. So a NEW test file defaults to visible and pays the slow mark only for the part that genuinely needs an install (E-04 versus E-05).
- `pytest.mark.slow` applied as a CLASS attribute (`pytestmark` inside a `unittest.TestCase`) deselects that class alone and leaves sibling classes in the same file default-visible. Verified at review on a fixture: default `2 passed`, `-m 'not slow'` `1 passed, 1 deselected`, `-m slow` `1 passed, 1 deselected`.
- `ensure_workflow_artifacts_readme` is NO-CLOBBER: an existing README is skipped `[already current]`, so a user's own edits to that file survive every re-install (verified at review on a real install). This is why the exemption must be conditioned on git state rather than granted by path alone.
- A plan that changes user-visible behavior adds one `- Fixed:` line to `CHANGELOG.md` `## 2.0.0 (pending)`; `CONTRIBUTING.md` Authoring conventions forbids em and en dashes in that file.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 to F-5 were measured at authoring HEAD `61ef21d8` and RE-MEASURED at review HEAD `b861bb05`; F-6 to F-9 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `engine.plan_deep_cleanup` | The framework's own ignored README is classified at-risk on a fully committed install. | probe: `at_risk ['.aw/workflow-artifacts/README.md']`, `all_recoverable False`, `README in files True`, `README in other_files True`, `counts['.aw/workflow-artifacts'] 1` |
| F-2 | INFO | `.aw/.gitignore` | The file is ignored by design, so `git add -A` can never commit it. | `git check-ignore -v` -> `.aw/.gitignore:75:/workflow-artifacts/	.aw/workflow-artifacts/README.md` |
| F-3 | MEDIUM | tests | The slow test asserting "all committed -> nothing at risk" fails. | `python3 -m pytest -o addopts="" -q tests/test_installer.py` -> `2 failed, 93 passed in 220.87s`, the sibling being `57dwkc`'s node |
| F-4 | INFO | regenerability | After install the target carries a TRACKED template byte-identical to the written README, and `_ARTIFACTS_README_FALLBACK` covers the case where it cannot be read. | probe: `tpl exists True`, `tpl identical to README True`, `tpl tracked True` |
| F-5 | INFO | backlog `4vfkl1` | Names exactly two failing tests: this item's and `57dwkc`'s. | its body lists `UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` and `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` |
| F-6 | HIGH | the authored fix | A PATH-ONLY exemption silences a warning that is CORRECT: with the README git-tracked (the pre-ignore-rule install shape `ensure_workflow_artifacts_readme`'s comment says persists forever) and holding uncommitted edits, `aw uninstall` would call unrecoverable content recoverable. | driven on a real install with the README `git add -f`'d, committed, then edited: `_git_file_state` -> `at_risk`; path-only rule -> `[]`; tracked-aware rule -> `['.aw/workflow-artifacts/README.md']` |
| F-7 | MEDIUM | the plan's own title and Concern | `aw uninstall --yes --deep` prints NO recoverability line; the warning comes from `--dry-run` (`! 1 of these are NOT recoverable from git (untracked/uncommitted)`) and from the interactive offer (`WARNING: ... Deleting them is permanent:`). | the three invocations driven against the real CLI on a committed install; `--yes --deep` -> `lines mentioning recoverable/permanent: (NONE)`, README removed |
| F-8 | MEDIUM | E-04 as authored | Marking every new test slow hides the fix from the bare run this repo's contract judges a change by, the exact invisibility `4vfkl1` and `xuc9v0` were filed about; and the classification rule needs no install to test. | a 5-scenario hand-built fixture reproduces all four states in 0.24s; one real install costs 1.83s to 3.38s (three runs) |
| F-9 | LOW | `tests/test_installer.py` docstring | The now-passing test would keep prose calling itself a `PRE-EXISTING FAILURE` and asking for the maintainer call this plan makes. | its docstring: "Either the product should exclude its own gitignored run-scratch README from the at-risk set, or this expectation should change; that is a maintainer call about `agent_workflows/`" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures.
2. E-02 adds the named regenerable-path constant with its three-part criterion and the tracked caveat.
3. E-03 exempts it from `at_risk` ONLY while untracked, keeping it in the removal set (F-6).
4. E-04 adds default-visible classification tests with three negative controls (F-8).
5. E-05 adds the slow-marked real-install integration case in a separate class.
6. E-06 corrects the stale docstring of the now-passing installer test, assertions untouched (F-9).
7. E-07 adds the CHANGELOG line.

## Deferred / out of scope (with reason)

- The sibling failure `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` (`.aw/system/layout.json` and `layout.schema.json` orphaned because `_DEEP_CLEANUP_ROOTS` does not list `.aw/system`).
  - Carrier: 57dwkc
  - Rationale: a different defect with its own backlog item (also `Blocks-Release: next`); fixing it here would widen a one-line classification change into a removal-root change.
- Backlog `4vfkl1` ("Two slow-marked test_installer deep-cleanup tests fail at HEAD"), which is NOT a separate defect: its two failing tests are this item's test and `57dwkc`'s test.
  - Carrier-Declined: duplicate of 3ypquf, to be closed with it; because its second failing test is `57dwkc`'s defect, it can only be closed `done` once `57dwkc` has also landed (or be retired as a duplicate of the pair). Its secondary point, that the slow subset is invisible to the bare run, is a CI-policy question owned by `xuc9v0` and by plan `4petcj` (approved), not by this plan; what this plan DOES owe it is not adding to the problem, which E-04 discharges by making the new classification tests default-visible.
- Retro-fitting `tests/test_installer.py`'s remaining install-heavy cases to a lighter fixture, or splitting its module-level slow mark.
  - Carrier-Declined: out of scope for a one-line classification fix, and the file's own `DeepCleanupTests` docstring records a deliberate reason for its shape ("these are the most destructive operations in the codebase"). E-04 sets the lighter precedent for new tests without rewriting the existing module.

## Scope check

- Over-scope: none. `tests/test_installer.py` is in scope for a DOCSTRING correction only (E-06); no assertion in it is touched, and its failing test must pass exactly as written.
- Under-scope: `agent_workflows/cli.py` is deliberately NOT changed: all three surfaces read `plan.at_risk` (`_uninstall_dry_run_report` via `deep.at_risk`, and `_offer_deep_cleanup`'s two `[f for f in plan.at_risk if f in ...]` filters), so they become correct automatically. No `cli` test is added, because the plan asserts on the classifier the surfaces read rather than re-asserting rendered strings.
- Scope-Paths justification: `engine.py` holds the classifier and the constant (E-02, E-03); the new test file holds E-04 and E-05; `tests/test_installer.py` holds E-06's docstring; `CHANGELOG.md` holds E-07.

## Required tests / validation

- `tests/test_deep_cleanup_regenerable.py` (new): four DEFAULT-VISIBLE classification cases (three of them negative controls) plus one slow-marked real-install integration class.
- `python3 -m pytest -o addopts="" -q tests/test_installer.py` before and after: the `DeepCleanupTests` failure is gone and the only remaining failure is `57dwkc`'s node.
- Bare `python3 -m pytest` before and after; compare failing node IDs. The new default-visible cases MUST appear in this run.

## Spec / documentation sync

- N/A for specs: the physical-layout spec (`physical-aw-hierarchy-placement-and-migration` Section 5, which names `.aw/workflow-artifacts/` as per-machine control state covered by the framework-owned `.aw/.gitignore`) and the wfartifacts contracts say the tree is never committed; none specifies deep-cleanup's at-risk classification (grep of `.aw/records/specs/` for `plan_deep_cleanup`, `at_risk`, and `uninstall --deep` finds nothing). No `.spec.md` is in `- Scope-Paths:`.
- No user-facing doc describes the at-risk count: `README.md` and `docs/` contain no occurrence of `uninstall --deep` or of "recoverable" in this sense (grepped at review). The only user-facing text this plan owes is E-07's `CHANGELOG.md` line, because the warning a user sees changes.

## Open questions

### OQ-01: Should the exemption apply even when a user has edited the README (the installer's no-clobber rule preserves such edits)?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: SUPERSEDED AT REVIEW, and the answer is now split by GIT STATE rather than by content. The original resolution ("yes, exempt by path") rested on correct premises (D92 makes the tree local-only scratch, `_DEEP_CLEANUP_ROOTS` already removes it even under `--keep-records`, and only the exact README path is exempt) but overlooked one state in which the warning is CORRECT: a README that is git-TRACKED and carries uncommitted edits. That state is not hypothetical, because `ensure_workflow_artifacts_readme`'s own comment records that a repo which installed before the ignore rule landed "would keep the file tracked forever", and git's ignore rules do not untrack an already-tracked path. Driven at review on a real install: the path-only test drops that file from `at_risk`, so the tool would promise recoverability for content git cannot restore. E-03 therefore exempts the path only while it is UNTRACKED. On the UNTRACKED-and-user-edited case the original answer stands and is deliberate: the file is exempt even if the user typed into it, because git holds nothing either way, an ignored path can never be committed, and the alternative (content-equality against the shipped template) would still be wrong in the tracked case while adding a template read and a byte comparison to a classifier. A user's own notes in that tree remain protected, because only the exact README path is ever exempt and E-04 case (2) pins that a sibling untracked user file stays at-risk.

### OQ-02: Is backlog `4vfkl1` the same defect as `3ypquf`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Partly, from repository evidence: `4vfkl1` names two failing tests, one of which is exactly `3ypquf`'s and the other `57dwkc`'s, and it names no third cause. It is therefore a duplicate umbrella of the two, recorded under Deferred; no work is owed to it beyond those two items.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the failing test output, the scratch probe (`at_risk`, README-in-files, check-ignore), and the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the constant's diff with its comment and `python3 -c "from agent_workflows import engine; print(engine._DEEP_CLEANUP_REGENERABLE)"`. The pasted comment must visibly state all three membership criteria AND the tracked caveat.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `plan_deep_cleanup` diff and a FOUR-ROW truth table driven on a real install, each row showing the actual `at_risk` list: untracked README (absent), tracked + clean (absent), tracked + uncommitted edit (PRESENT), sibling untracked user file (PRESENT). Also paste the README still in `files` and `other_files` and a non-zero `.aw/workflow-artifacts` count. A pasted table missing the tracked-and-dirty row does not satisfy this item, because that row is the entire content of F-6.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -q tests/test_deep_cleanup_regenerable.py` (BARE, no `-o addopts=""`) showing the four classification cases SELECTED and passing, proving they are default-visible; then the same file with E-03 temporarily reverted, showing case (1) FAILING and cases (2) to (4) passing; and the wall-clock line from each run.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_deep_cleanup_regenerable.py` with its total count, and a bare `python3 -m pytest -q tests/test_deep_cleanup_regenerable.py` whose `deselected` count shows the install class was deselected. Paste the E-03-reverted run showing case (a) FAILING.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff tests/test_installer.py` in full (it must contain no changed line matching `self.assert` or `assert `), and `python3 -m pytest -o addopts="" -q tests/test_installer.py` before and after, showing `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` moving from FAILED to passed and `57dwkc`'s node as the only remaining failure.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly one added `- Fixed:` line under `## 2.0.0 (pending)`, and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing. Also paste the bare `python3 -m pytest` summary line before and after the whole change, with the after-minus-before failing node-ID set (must be empty), and `aw sanitize --agent` exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw uninstall` stops counting `.aw/workflow-artifacts/README.md`, a file the framework writes, never commits, and can always regenerate, as unrecoverable user content. Three things are preserved deliberately: the file is still listed and still removed; any other untracked file in that tree is still flagged; and that same README is still flagged in the one state where git genuinely cannot restore it (tracked, with uncommitted edits, which is the shape of a repo that installed before the ignore rule landed). The user-visible change is recorded in `CHANGELOG.md`. This graduates backlog `3ypquf` (a `bug`) and inherits its `- Blocks-Release: next`. The sibling `.aw/system/layout.json` defect stays with `57dwkc`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/engine.py` (`_DEEP_CLEANUP_REGENERABLE`, `plan_deep_cleanup`, the `DeepCleanupPlan` docstring), the new `tests/test_deep_cleanup_regenerable.py`, a DOCSTRING-ONLY edit to `tests/test_installer.py`, and one line in `CHANGELOG.md`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show the new classification cases in a BARE run (that is what proves they are default-visible), and V-05/V-06 must ALSO paste `-o addopts=""` runs, because the installer test and E-05's class are slow-marked and a bare run alone cannot show them.

GENUINE STOP CONDITIONS. (1) If E-01 finds `at_risk` already empty on a committed install, retire this plan instead of executing it. (2) Do NOT satisfy any validation item by weakening a test: specifically, do not delete or relax E-04 case (3) (tracked + dirty stays at-risk), and do not change any assertion in `tests/test_installer.py`. Either would make this plan pass while re-introducing the defect it exists to avoid.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `3ypquf` `done` with `--evidence` citing the executed plan; its release gate is preserved by this plan's `From-Backlog` + `Blocks-Release` handoff.
