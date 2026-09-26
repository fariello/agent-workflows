# IPD: Stop aw uninstall --deep calling the framework's own regenerable workflow-artifacts README unrecoverable

- Date: 2026-09-26
- Kind: child
- Concern: `aw uninstall --deep` WARNS THAT CONTENT IS UNRECOVERABLE WHEN THE USER HAS COMMITTED EVERYTHING. `engine.plan_deep_cleanup` walks `_DEEP_CLEANUP_ROOTS` (which includes `.aw/workflow-artifacts`) and appends every file for which `engine._git_file_state` returns `at_risk`; `_git_file_state` returns `at_risk` for any path that is not git-tracked. The installer's own `ensure_workflow_artifacts_readme` writes `.aw/workflow-artifacts/README.md` and deliberately never stages it (D92: run scratch is never committed), and the framework-owned `.aw/.gitignore` ignores the tree (`/workflow-artifacts/`). So after install + `git add -A` + commit, `plan.at_risk == ['.aw/workflow-artifacts/README.md']` and `plan.all_recoverable is False`, and both `cli` surfaces print the NOT-recoverable warning (the preview's `! N of these are NOT recoverable from git` and `_offer_deep_cleanup`'s `WARNING: ... Deleting them is permanent`). Re-measured at HEAD `61ef21d8`: `git check-ignore -v` -> `.aw/.gitignore:75:/workflow-artifacts/`; `tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` FAILS (`python3 -m pytest -o addopts="" ...` -> `2 failed` together with the sibling below). The module is `pytestmark = pytest.mark.slow`, so a bare run never shows it. The file is regenerable: `ensure_workflow_artifacts_readme` re-creates it from `templates/workflow-artifacts-README.md` (falling back to `engine._ARTIFACTS_README_FALLBACK`), and after install the target's own `.aw/system/workflows/templates/workflow-artifacts-README.md` is tracked and byte-identical to it (measured).
- Scope: IN: (a) a named module constant `engine._DEEP_CLEANUP_REGENERABLE = (f"{ARTIFACTS_DIR}README.md",)` with a comment citing `3ypquf` and D92; (b) `plan_deep_cleanup` skips the at-risk classification for a path in that tuple, while STILL listing it in `plan.files`, `plan.other_files`, and `plan.counts` so `run_deep_cleanup` still removes it; (c) behavioral tests on a real install, including a negative control proving an untracked USER file under `.aw/workflow-artifacts/` is still at-risk, and the previously failing test passing unmodified. OUT: `UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` (backlog `57dwkc`, `.aw/system/layout.json` orphaned by `_DEEP_CLEANUP_ROOTS`); changing `_git_file_state`; changing `_DEEP_CLEANUP_ROOTS`; exempting any other path.
- Scope-Paths: agent_workflows/engine.py, tests/test_deep_cleanup_regenerable.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 3ypquf
- Blocks-Release: next
- Set: deepclean
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: baxbdh

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 3ypquf; inherits Blocks-Release next. Authored review-ready; the at-risk classification, the gitignore rule, and the failing slow test were re-measured at HEAD 61ef21d8 on a real install. Backlog 4vfkl1 checked and recorded under Deferred as a duplicate.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw uninstall --deep` report "all recoverable" when the user has committed everything they can commit, by not counting the framework's own never-committed, regenerable run-scratch README as user content at risk, while still removing it and still flagging any real user file in that tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. Run `python3 -m pytest -o addopts="" -q "tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed"` and paste the failure. Then, on a scratch repo built with the test module's own helpers (`tests.test_installer.init_repo`, `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)`, `git add -A`, commit), paste `engine.plan_deep_cleanup(repo).at_risk`, whether `.aw/workflow-artifacts/README.md` is in `plan.files`, and `git check-ignore -v .aw/workflow-artifacts/README.md`. If `at_risk` is already empty, STOP and report that the defect is fixed.
  - Depends on: none
  - Expected outcome: the test fails at `self.assertTrue(plan.all_recoverable, ...)`; `at_risk == ['.aw/workflow-artifacts/README.md']`; the README is in `plan.files`; check-ignore names `.aw/.gitignore` `/workflow-artifacts/`.
  - Execution state: pending

### Task group 2: exempt the regenerable file

- [ ] E-02 ADD `engine._DEEP_CLEANUP_REGENERABLE: tuple[str, ...] = (f"{ARTIFACTS_DIR}README.md",)` beside `_DEEP_CLEANUP_ROOTS`, with a comment stating the criterion for membership (framework-written, never committed by design, and re-created by `ensure_workflow_artifacts_readme` from the shipped template or `_ARTIFACTS_README_FALLBACK`, so deleting it loses nothing the framework cannot rebuild), citing `3ypquf` and D92, and saying that a path belongs here only if all three hold.
  - Depends on: E-01
  - Expected outcome: `engine._DEEP_CLEANUP_REGENERABLE == (".aw/workflow-artifacts/README.md",)`.
  - Execution state: pending

- [ ] E-03 CHANGE `engine.plan_deep_cleanup` so the at-risk test reads `if rel not in _DEEP_CLEANUP_REGENERABLE and _git_file_state(repo_root, rel) == "at_risk":`. Leave the `plan.files` / `records_files` / `other_files` appends and the `n += 1` count unchanged, so the file is still announced and removed. Update the `DeepCleanupPlan` docstring's `at_risk` sentence to say regenerable framework files are excluded.
  - Depends on: E-02
  - Expected outcome: E-01's scratch probe now shows `at_risk == []`, the README still in `plan.files` and `plan.other_files`, and `plan.counts[".aw/workflow-artifacts"] >= 1`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 ADD `tests/test_deep_cleanup_regenerable.py`, behavioral only (maintainer's 2026-09-26 ruling: no source-text pins), marked `pytestmark = pytest.mark.slow` like `tests/test_installer.py` because it performs a real install. Cases on a committed real install: (1) `plan_deep_cleanup(repo).all_recoverable is True` and `at_risk == []`; (2) the README is still in `plan.files` and in `plan.other_files`; (3) `run_deep_cleanup(repo, plan, use_git=True)` removes `.aw/workflow-artifacts/README.md` from disk; (4) NEGATIVE CONTROL: after writing an untracked `.aw/workflow-artifacts/my-notes.md`, it IS in `plan.at_risk` and `all_recoverable is False`; (5) NEGATIVE CONTROL: an uncommitted `.aw/records/research/scratch.md` is still at-risk (unchanged behavior). Also re-run the previously failing `tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` UNMODIFIED; it must now pass.
  - Depends on: E-03
  - Expected outcome: all pass; cases (1) and the existing installer test FAIL before E-03; cases (2) to (5) pass before and after (controls).
  - Execution state: pending

## Project conventions discovered (Step 0)

- D92 / wfartifacts: `.aw/workflow-artifacts/` is local run scratch, never committed, ignored by the framework-owned `.aw/.gitignore` with `/workflow-artifacts/`; `ensure_workflow_artifacts_readme` is "DELIBERATELY NOT STAGED (wfartifacts Order 01 / gzhd7t, decision D-01)".
- The README has ONE fallback, `engine._ARTIFACTS_README_FALLBACK`, used when the template cannot be read, so the file is always regenerable.
- `_DEEP_CLEANUP_ROOTS` lists `.aw/workflow-artifacts` as non-records "OTHER" scaffolding, removed even under `--keep-records` (its comment). This plan does not change that.
- `_git_file_state` is deliberately loud ("anything uncertain is \"at_risk\""); the exemption is a named, reviewed list in the caller rather than a softening of that function.
- `tests/test_installer.py` is module-marked slow (`pytestmark = pytest.mark.slow`), and `pyproject.toml` `addopts` carries `-m 'not slow'`, so the evidence for this plan must use `-o addopts=""` or `-m slow` in addition to the bare run.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `engine.plan_deep_cleanup` | The framework's own ignored README is classified at-risk on a fully committed install. | probe: `at_risk ['.aw/workflow-artifacts/README.md']`, `README in files True` |
| F-2 | INFO | `.aw/.gitignore` | The file is ignored by design, so `git add -A` can never commit it. | `git check-ignore -v` -> `.aw/.gitignore:75:/workflow-artifacts/	.aw/workflow-artifacts/README.md` |
| F-3 | MEDIUM | tests | The slow test asserting "all committed -> nothing at risk" fails. | `python3 -m pytest -o addopts="" -q <that node> <57dwkc node>` -> `2 failed in 8.79s` |
| F-4 | INFO | regenerability | After install the target carries a tracked template byte-identical to the README. | probe: `target template exists True True`, `tpl tracked True` |
| F-5 | INFO | backlog `4vfkl1` | Names exactly two failing tests: this item's and `57dwkc`'s. | its body lists `UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` and `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures.
2. E-02 adds the named regenerable-path constant.
3. E-03 exempts it from `at_risk` only, keeping it in the removal set.
4. E-04 adds behavioral tests with two negative controls and re-runs the failing installer test unmodified.

## Deferred / out of scope (with reason)

- The sibling failure `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` (`.aw/system/layout.json` and `layout.schema.json` orphaned because `_DEEP_CLEANUP_ROOTS` does not list `.aw/system`).
  - Carrier: 57dwkc
  - Rationale: a different defect with its own backlog item (also `Blocks-Release: next`); fixing it here would widen a one-line classification change into a removal-root change.
- Backlog `4vfkl1` ("Two slow-marked test_installer deep-cleanup tests fail at HEAD"), which is NOT a separate defect: its two failing tests are this item's test and `57dwkc`'s test.
  - Carrier-Declined: duplicate of 3ypquf, to be closed with it; because its second failing test is `57dwkc`'s defect, it can only be closed `done` once `57dwkc` has also landed (or be retired as a duplicate of the pair). Its secondary point, that the slow subset is invisible to the bare run, is a CI-policy question outside this plan.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/cli.py` is deliberately NOT changed: both warning surfaces read `plan.at_risk`, so they become correct automatically. `tests/test_installer.py` is NOT modified; its failing test must pass as written.
- Scope-Paths justification: `engine.py` holds the classifier and the constant; the new test file holds E-04.

## Required tests / validation

- `tests/test_deep_cleanup_regenerable.py` (new, slow-marked): five behavioral cases with two negative controls.
- `python3 -m pytest -o addopts="" -q tests/test_installer.py` before and after: the `DeepCleanupTests` failure is gone and the only remaining failure is `57dwkc`'s node.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: the physical-layout and wfartifacts contracts say the tree is never committed; none specifies deep-cleanup's at-risk classification (grep of `.aw/records/specs/` for `plan_deep_cleanup` / `at_risk` finds nothing). No `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs describe the at-risk count.

## Open questions

### OQ-01: Should the exemption apply even when a user has edited the README (the installer's no-clobber rule preserves such edits)?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Yes, exempt by path, per the graduation brief's specified fix and repository evidence: the file lives in a tree that D92 defines as local-only scratch that is never committed, its README is documentation of that tree rather than user content, and `_DEEP_CLEANUP_ROOTS` already removes the whole tree even under `--keep-records`. A user who writes their own notes in that tree is still protected, because only the exact README path is exempt and E-04 case (4) pins that an untracked user file there stays at-risk. A reviewer who wants content-equality gating instead can request it; it would change E-03 only.

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
  - Required evidence: paste the constant's diff with its comment and `python3 -c "from agent_workflows import engine; print(engine._DEEP_CLEANUP_REGENERABLE)"`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `plan_deep_cleanup` diff and the re-run probe showing `at_risk == []` with the README still in `files` and `other_files` and a non-zero `.aw/workflow-artifacts` count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_deep_cleanup_regenerable.py` passing with its count; the same with E-03 temporarily reverted showing case (1) FAILING and cases (2) to (5) passing; `python3 -m pytest -o addopts="" -q tests/test_installer.py` before and after, showing `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` moving from FAILED to passed and `57dwkc`'s node as the only remaining failure; and the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw uninstall --deep` stops counting `.aw/workflow-artifacts/README.md`, a file the framework writes, never commits, and can always regenerate, as unrecoverable user content. The file is still listed and still removed, and any other untracked file in that tree is still flagged. This graduates backlog `3ypquf` (a `bug`) and inherits its `- Blocks-Release: next`. The sibling `.aw/system/layout.json` defect stays with `57dwkc`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/engine.py` (`_DEEP_CLEANUP_REGENERABLE`, `plan_deep_cleanup`, the `DeepCleanupPlan` docstring) and the new `tests/test_deep_cleanup_regenerable.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. Because the relevant tests are slow-marked, V-04 must ALSO paste the `-o addopts=""` runs; a bare run alone cannot show this fix.

GENUINE STOP CONDITION: if E-01 finds `at_risk` already empty on a committed install, retire this plan instead of executing it.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `3ypquf` `done` with `--evidence` citing the executed plan; its release gate is preserved by this plan's `From-Backlog` + `Blocks-Release` handoff.
