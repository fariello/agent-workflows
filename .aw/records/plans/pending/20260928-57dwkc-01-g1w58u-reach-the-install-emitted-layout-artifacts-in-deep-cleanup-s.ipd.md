# IPD: Reach the install-emitted layout artifacts in deep cleanup so no .aw/ directory remains

- Date: 2026-09-28
- Kind: child
- Concern: `aw uninstall --deep` with records REMOVE LEAVES AN `.aw/` DIRECTORY BEHIND, so the documented "no `.aw/` remains" guarantee is false. `engine.install_into_repo` calls `engine.emit_layout_artifacts`, which writes `.aw/system/layout.json` and `.aw/system/layout.schema.json` (spec `kw5y2s` Section 6.1). NEITHER removal layer reaches them: they are NOT in the ownership manifest (measured: `manifest.files` holds 309 entries, 158 under `.aw/system`, and `.aw/system/layout.json` is absent while `.aw/system/VERSION` is present), so `engine.plan_uninstall` never classifies them; and `.aw/system` is absent from `engine._DEEP_CLEANUP_ROOTS`, so `engine.plan_deep_cleanup` never enumerates them. Because two files survive, the step-7 empty-dir prune at the end of `engine.uninstall_repo` and the equivalent prune in `engine.run_deep_cleanup` cannot remove `.aw/system/` or `.aw/`. RE-MEASURED at HEAD `08007c9c`: after `install_into_repo` -> `uninstall_repo(force=True)` -> `plan_deep_cleanup` -> `run_deep_cleanup(remove_records=True)`, enumerating the tree prints exactly `.aw/system DIR`, `.aw/system/layout.json FILE`, `.aw/system/layout.schema.json FILE`, and nothing else. Two tests assert the guarantee and BOTH FAIL at HEAD: `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` (`AssertionError: True is not false : NO .aw/ directory must remain after deep cleanup removing records`) and `tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`. Both are in slow-marked modules, so the bare contract run never shows them (backlog `4vfkl1` records exactly this invisibility). THE BACKLOG ITEM'S SUGGESTED FIX IS UNSAFE AND THIS PLAN REJECTS IT; see OQ-01 and F-4/F-5. Adding the `.aw/system` DIRECTORY to `_DEEP_CLEANUP_ROOTS` was driven at authoring and (a) DESTROYS USER-PRESERVED CONTENT, because base uninstall deliberately PRESERVES a drifted owned workflow file and a subsequent deep cleanup then swept `.aw/system/workflows/advise/advise.md` away even under `--keep-records` (measured: `drifted preserved: True` after base uninstall, then `False` after the cleanup), and (b) REGRESSES the defect plan `baxbdh` just fixed, because both emitted files are gitignored and untracked so `_git_file_state` returns `at_risk` for each, turning `plan.all_recoverable` from `True` to `False` on a fully committed install and re-breaking `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` (measured: `variant=roots all_recoverable=False at_risk=['.aw/system/layout.json', '.aw/system/layout.schema.json']`).
- Scope: IN: (a) `engine.uninstall_repo` removes the two install-emitted layout artifacts by their EXACT named constants (`AW_LAYOUT_JSON_PATH`, `AW_LAYOUT_SCHEMA_PATH`) in its deterministic framework-generated-file step, beside the `.aw/config` / `.aw/state` / `.aw/.gitignore` removals that already exist for exactly this reason, so the EXISTING step-7 `.aw` empty-dir prune can then remove `.aw/system/` and `.aw/`; (b) a default-visible behavioral test file proving the base-uninstall removal, the resulting full `.aw/` removal, and the negative controls that a drifted owned workflow file and a kept records tree both survive; (c) one `CHANGELOG.md` line. OUT: adding `.aw/system` (the directory) to `_DEEP_CLEANUP_ROOTS`, which OQ-01 rejects on measured evidence; any change to `_DEEP_CLEANUP_ROOTS`, `_DEEP_CLEANUP_REGENERABLE`, `plan_deep_cleanup`, `run_deep_cleanup`, or `_git_file_state`; any change to the ownership manifest format or to what `emit_layout_artifacts` writes; changing ANY assertion in `tests/test_installer.py` or `tests/test_cli.py` (both must pass exactly as written); `.aw/system/managed-sections.json` (the manifest itself, already removed last by design, step 6); and `agent_workflows/cli.py`.
- Scope-Paths: agent_workflows/engine.py, tests/test_uninstall_layout_artifacts.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 57dwkc
- Blocks-Release: next
- Set: 57dwkc
- Order: 1
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: g1w58u

## Workflow history

- 2026-09-28 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 57dwkc; inherits Blocks-Release next. Authored review-ready. Every claim re-measured at HEAD 08007c9c on real installs: the two failing tests reproduced, the three surviving paths enumerated, the manifest checked for ownership, and BOTH candidate fixes driven. The backlog item's suggested fix (adding `.aw/system` to `_DEEP_CLEANUP_ROOTS`) was REJECTED on measured evidence that it deletes user-preserved drifted files and regresses plan baxbdh; OQ-01 records the rejection and the chosen alternative. The chosen fix was PROVEN by a temporary probe in `engine.uninstall_repo`: the 14 tests of `UninstallCompletenessTests`, `DeepCleanupTests`, and `InstallAtomicWizardTests` went from 2 failing to `14 passed in 35.91s`, and the probe was then fully reverted (`git diff agent_workflows/engine.py` empty).
- 2026-09-28 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw uninstall` leave no `.aw/` directory behind when the user removes records, by having the base uninstall remove the two layout files the installer itself generated, so the empty-directory prune that already exists can finish the job. Do it without touching the deep-cleanup removal roots, so a user's preserved records and preserved hand-edited workflow files remain as safe as they are today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce at the executing HEAD

- [ ] E-01 RE-MEASURE the defect before changing anything. Run `python3 -m pytest -o addopts="" -q "tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory" "tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw"` and paste both failures. Then, on a scratch repo built with the test module's own helpers (`tests.test_installer.init_repo`, then `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)`, `engine.write_setup_marker(repo)`), run the full sequence `uninstall_repo(repo, use_git=True, force=True)` -> `plan_deep_cleanup(repo)` -> `run_deep_cleanup(repo, plan, use_git=True, remove_records=True)` and paste an ENUMERATION of everything remaining under `.aw/` (path plus DIR or FILE). Also paste `git check-ignore -v .aw/system/layout.json` and whether `.aw/system/layout.json` is in `manifest.files` (via `agent_workflows.manifest.load(resolve_manifest_path(repo))`). If nothing remains under `.aw/`, STOP and report the defect already fixed.
  - Depends on: none
  - Expected outcome: both nodes fail; the enumeration prints exactly `.aw/system`, `.aw/system/layout.json`, `.aw/system/layout.schema.json` and nothing else; check-ignore names `.aw/.gitignore` and the `system/layout.json` pattern; the path is ABSENT from `manifest.files` while `.aw/system/VERSION` is present.
  - Execution state: pending

### Task group 2: remove the emitted artifacts in the base uninstall

- [ ] E-02 CHANGE `engine.uninstall_repo` so the deterministic framework-created-file step (the one whose existing comment reads "Deterministic framework-created lifecycle files (config, state, .aw/.gitignore) not in the manifest (E-01)", which already removes `.aw/config`, `.aw/state`, and `.aw/.gitignore`) ALSO removes the two install-emitted layout artifacts. Iterate the NAMED CONSTANTS `AW_LAYOUT_JSON_PATH` and `AW_LAYOUT_SCHEMA_PATH` (never string literals, so the removal cannot drift from `emit_layout_artifacts`, which writes those same two constants), and for each: skip when the file is absent, otherwise call the existing `_uninstall_remove(repo_root, rel, use_git)`, call `_record_changed(rel)`, and append a `f"removed {rel}"` action, exactly matching the shape of the neighboring removals. Place it BEFORE the step-7 `.aw` empty-dir prune so that prune can then remove `.aw/system/` and `.aw/`; do NOT add a second prune, because step 7 already walks `.aw` deepest-first. Extend that step's comment to name the layout artifacts and to state WHY they belong to this layer rather than to deep cleanup: they are FRAMEWORK-GENERATED output (`emit_layout_artifacts`, spec `kw5y2s` Section 6.1), they are absent from the ownership manifest so `plan_uninstall` cannot classify them, and they hold no user content, which is the identical rationale the config/state/`.gitignore` removals beside them already carry. Also record that deep cleanup deliberately does NOT own them (see OQ-01: a `.aw/system` root there would sweep away drifted owned workflow files the base uninstall intentionally preserved).
  - Depends on: E-01
  - Expected outcome: after `install_into_repo` then `uninstall_repo(force=True)` on a repo with no records planted, `.aw/system/layout.json` and `.aw/system/layout.schema.json` are both gone, the returned actions contain `removed .aw/system/layout.json` and `removed .aw/system/layout.schema.json`, and a `changed_out` list passed in contains both paths. `engine._DEEP_CLEANUP_ROOTS` and `engine._DEEP_CLEANUP_REGENERABLE` are BYTE-IDENTICAL to HEAD (`git diff` shows no change to either tuple).
  - Execution state: pending

### Task group 3: prove it, including what must NOT change

- [ ] E-03 ADD `tests/test_uninstall_layout_artifacts.py`, DEFAULT-VISIBLE for the cases that need no install and slow-marked (a CLASS-scoped `pytestmark = pytest.mark.slow`, the shape plan `baxbdh` established and verified) ONLY for the real-install cases. Behavioral only, per GUIDING_PRINCIPLES P16: assert on files on disk, returned actions, and `changed_out`, and NEVER on the source text of `engine.py`, a caller count, or the membership of a tuple by reading code. DEFAULT-VISIBLE case, on a hand-built fixture repo (`git init`, write the two layout files plus a `.aw/records/README.md`, no install): `uninstall_repo(repo, use_git=True, force=True)` removes both layout files and, with no records kept, leaves no `.aw/` directory. SLOW real-install cases, each from `install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)`: (1) after `uninstall_repo(force=True)` both emitted paths are gone and both appear in the returned actions and in `changed_out`; (2) THE HEADLINE GUARANTEE, the full sequence with `write_setup_marker` and a planted untracked record then `run_deep_cleanup(remove_records=True)` leaves `(repo / ".aw").exists()` FALSE; (3) NEGATIVE CONTROL for the rejected fix, a repo where an owned workflow file (`.aw/system/workflows/advise/advise.md`) has been EDITED so `plan_uninstall` reports it drifted, then `uninstall_repo(force=False)` (the preserving default) followed by `run_deep_cleanup(remove_records=False)`: the drifted file MUST still exist afterwards, and so must a planted user record and `.aw/records/`. This case is what pins the OQ-01 decision as a TEST rather than as prose; measured at authoring, the backlog item's suggested `.aw/system` root fails it. (4) NEGATIVE CONTROL for `baxbdh`: on a fully committed install, `plan_deep_cleanup(repo).all_recoverable` is True and `at_risk` is empty, so this plan has not reintroduced the at-risk misclassification.
  - Depends on: E-02
  - Expected outcome: all cases pass after E-02. Before E-02, the default-visible case and slow cases (1) and (2) FAIL; cases (3) and (4) PASS both before and after, which is what makes them controls. The default-visible case appears in a BARE `python3 -m pytest` run.
  - Execution state: pending

- [ ] E-04 RUN the two previously failing tests UNMODIFIED and paste them passing: `python3 -m pytest -o addopts="" -q "tests/test_installer.py::UninstallCompletenessTests" "tests/test_installer.py::DeepCleanupTests" "tests/test_cli.py::InstallAtomicWizardTests"`. Do NOT edit any assertion, body line, or docstring in either module: the whole point is that they pass as written, and both are OUT of `- Scope-Paths:` so any edit is an out-of-scope change the finalize gate must refuse. If `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` passes, its docstring (which calls itself a `PRE-EXISTING FAILURE` and says the fix "is a product change this test-only change must not make") becomes stale prose; REPORT that for a follow-up rather than editing it here, exactly as `baxbdh` handled its own sibling docstring under a dedicated E-item with the file in scope.
  - Depends on: E-03
  - Expected outcome: every node in those three classes passes, `14 passed` or more, with zero failures; `git diff --stat` shows NO change to `tests/test_installer.py` or `tests/test_cli.py`.
  - Execution state: pending

- [ ] E-05 ADD one `- Fixed:` line to the `## 2.0.0 (pending)` section of `CHANGELOG.md`, in USER-FACING prose with NO em or en dashes (`CONTRIBUTING.md` Authoring conventions): uninstalling with the deeper cleanup and choosing to remove records now leaves no `.aw` directory behind. Two generated files that record the workspace layout, which the installer writes and can always write again, used to be left behind and kept the folder alive. Removing records still removes everything; keeping records still keeps them, and a workflow file you have edited yourself is still preserved.
  - Depends on: E-02
  - Expected outcome: exactly one added line under the `## 2.0.0 (pending)` heading, and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` prints nothing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `engine.uninstall_repo` is layered by OWNERSHIP, and the layer this plan extends already exists for precisely this class of file. Its step-4 comment reads "Deterministic framework-created lifecycle files (config, state, .aw/.gitignore) not in the manifest (E-01)", and plan `ejhzgk` (awuninstallfix Order 01) created it after finding that `.aw/config`, `.aw/state`, and `.aw/.gitignore` "are removed by neither uninstall layer, so `.aw/` can never be fully removed after install" (its finding UN-001). The layout artifacts are the same shape of defect, arriving later by a different feature.
- `emit_layout_artifacts` is called from `install_into_repo` itself, deliberately, because that is "the SHARED CHOKEPOINT every install path reaches". Its docstring also records the two files are "GENERATED and GITIGNORED", and that committing generated output "is exactly the git drift install-time emission exists to avoid".
- The two emitted paths have NAMED CONSTANTS, `AW_LAYOUT_JSON_PATH` and `AW_LAYOUT_SCHEMA_PATH`, both derived from `AW_SYSTEM_DIR`. The writer uses them, so the remover must too.
- The framework-owned `.aw/.gitignore` carries `system/layout.json` and `system/layout.schema.json`, and `_ensure_aw_gitignore` BACK-FILLS both patterns on a repo installed before emission existed. So the files are untracked by construction, which is why `_git_file_state` calls them `at_risk` and why routing them through deep cleanup regresses `baxbdh`.
- `_DEEP_CLEANUP_ROOTS` holds records roots plus a small non-records set, and its own comment says those "hold user content, so removal is opt-in, warned, and git-state-classified". Generated output with no user content does not match that description, which is the design reason the fix belongs in the base layer.
- `engine.uninstall_repo` PRESERVES a drifted owned file by default (`plan_uninstall` classifies it `drifted`, and only `--force` or an interactive "remove" decision deletes it). `run_deep_cleanup` has no such notion, so any path reachable from a deep-cleanup root is removed unconditionally. That asymmetry is what makes a `.aw/system` root unsafe.
- Both `uninstall_repo` (step 7) and `run_deep_cleanup` already prune empty directories under `.aw` deepest-first, so removing the last two files is sufficient to remove `.aw/system/` and `.aw/`. No new prune is needed.
- `tests/test_installer.py` and `tests/test_cli.py` are module-marked `pytestmark = pytest.mark.slow`, and `pyproject.toml` `addopts` carries `-m 'not slow'`, so evidence for this plan needs `-o addopts=""` in addition to the bare run. Backlog `4vfkl1` exists because that subset can hide regressions; `baxbdh` set the precedent that a NEW test file defaults to VISIBLE and pays the slow mark only where an install is genuinely required.
- A `pytest.mark.slow` applied as a CLASS attribute deselects that class alone and leaves sibling classes in the same file default-visible (verified by `baxbdh`).
- A plan that changes user-visible behavior adds one `- Fixed:` line to `CHANGELOG.md` `## 2.0.0 (pending)`; `CONTRIBUTING.md` forbids em and en dashes there.
- Tests must assert observable behavior, never code structure: no `inspect`, `ast`, regex, or substring search over production source, and no symbol censuses (AGENTS.md execution contract; GUIDING_PRINCIPLES P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All findings measured at HEAD `08007c9c` on real installs built with the test module's own helpers. F-4 and F-5 were produced by DRIVING the backlog item's suggested fix, which is why this plan does not implement it.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `engine.uninstall_repo` + `engine.plan_deep_cleanup` | The "no `.aw/` remains" guarantee is false: after install, base uninstall, and a records-removing deep cleanup, exactly three paths survive, all of them generated layout output. | enumeration after the full sequence: `.aw DIR`, `.aw/system DIR`, `.aw/system/layout.json FILE`, `.aw/system/layout.schema.json FILE`, nothing else |
| F-2 | HIGH | tests | Both tests asserting the guarantee fail. | `test_deep_cleanup_records_remove_leaves_no_aw_directory` -> `AssertionError: True is not false : NO .aw/ directory must remain after deep cleanup removing records`; `test_interactive_deep_cleanup_records_remove_fully_cleans_aw` -> `1 failed` |
| F-3 | INFO | the ownership manifest | The emitted files are NOT manifest-owned, so `plan_uninstall` structurally cannot reach them; the sibling `VERSION` in the same directory IS owned. This is why the gap is a MISSING REMOVAL rather than a misclassification. | `manifest.files` 309 entries, 158 under `.aw/system`; `owned? .aw/system/VERSION True`; `owned? .aw/system/layout.json False`; `owned? .aw/system/layout.schema.json False`; `owned? .aw/system/managed-sections.json False` |
| F-4 | HIGH | the BACKLOG ITEM'S SUGGESTED FIX | Adding the `.aw/system` DIRECTORY to `_DEEP_CLEANUP_ROOTS` DESTROYS USER-PRESERVED CONTENT. A hand-edited owned workflow file is preserved by base uninstall by design, then swept away by the deep cleanup even under `--keep-records`, because `run_deep_cleanup` has no drift concept. | with the root added: `drifted count: 1`, `after base uninstall, drifted file preserved: True`, `drifted workflow in deep plan: True`, then `>>> after keep-records deep cleanup, drifted file still there: False` |
| F-5 | HIGH | the BACKLOG ITEM'S SUGGESTED FIX | The same change REGRESSES the defect plan `baxbdh` just fixed. Both emitted files are gitignored and untracked, so `_git_file_state` returns `at_risk`, flipping `all_recoverable` to False on a fully committed install and re-breaking `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed`. | `variant=baseline all_recoverable=True at_risk=[]`; `variant=roots all_recoverable=False at_risk=['.aw/system/layout.json', '.aw/system/layout.schema.json']`; `git check-ignore -v` -> `.aw/.gitignore:33:system/layout.json` and `:34:system/layout.schema.json` |
| F-6 | INFO | the CHOSEN fix | Removing the two files in the base uninstall passes every scenario, including both controls, WITHOUT touching any deep-cleanup tuple. | probe: `A: .aw exists after: False`; `B: all_recoverable on installed repo: True at_risk: []`; `C: drifted STILL preserved: True, user record preserved: True, .aw/records remains: True` |
| F-7 | INFO | the CHOSEN fix, end to end | A temporary probe implementing E-02 turned the two failures green with no other node regressing, then was fully reverted. | `python3 -m pytest -o addopts="" -q` over `UninstallCompletenessTests`, `DeepCleanupTests`, `InstallAtomicWizardTests` -> `14 passed in 35.91s`; after revert `git diff --stat agent_workflows/engine.py` empty |
| F-8 | LOW | `resolve_target_layout` | While the orphans remain, a fully uninstalled repo still answers `aw` for its target layout even with `.aw/system/VERSION` gone, because the resolver keys on `.aw/system` EXISTING. The fix removes that stale signal as a side effect; no separate change is needed. | after full deep cleanup at HEAD: `resolve_target_layout -> aw`, `read_installed_version -> None`, `.aw/system/VERSION exists: False`, `leftover .aw/system exists: True` |
| F-9 | LOW | `tests/test_installer.py` docstring | The failing test's docstring documents the cause correctly and explicitly defers the fix ("This is a real completeness gap in `agent_workflows/`, whose fix is a product change this test-only change must not make"). It becomes stale once this plan lands, but the file is OUT of scope, so E-04 reports it instead of editing it. | the quoted docstring sentence, plus its naming of `.aw/system/layout.json` and `layout.schema.json` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the defect and confirms the two emitted files are unowned and gitignored.
2. E-02 removes them in `uninstall_repo`'s deterministic framework-generated-file step via the named constants, letting the existing prune remove `.aw/system/` and `.aw/` (F-1, F-3, F-6).
3. E-03 adds a new test file: default-visible for the no-install case, slow-marked for the real-install cases, with the two negative controls that pin the rejected alternative (F-4) and the `baxbdh` non-regression (F-5).
4. E-04 proves the two previously failing tests pass UNMODIFIED and reports the now-stale docstring instead of editing it (F-2, F-9).
5. E-05 adds the CHANGELOG line.

## Deferred / out of scope (with reason)

- Adding `.aw/system` to `_DEEP_CLEANUP_ROOTS`, the fix the backlog item suggests as LIKELY.
  - Carrier-Declined: REJECTED ON MEASURED EVIDENCE, not deferred. It deletes user-preserved drifted workflow files (F-4) and regresses `baxbdh` (F-5). OQ-01 records the full reasoning and the alternative chosen instead.
- Moving `.aw/system/VERSION` or any other `.aw/system` member into this removal, which the backlog item asks to have "confirmed".
  - Carrier-Declined: CONFIRMED UNNECESSARY at authoring, so there is nothing to carry. `VERSION` IS manifest-owned and is already removed by `plan_uninstall`/`uninstall_repo` (F-3); `managed-sections.json` is the manifest itself, removed LAST by design in step 6 so a mid-uninstall failure leaves the ownership record intact for a retry; `.aw/system/workflows/**` is manifest-owned per-file, with drift PRESERVED on purpose. Only the two emitted layout files fall through, which is exactly the enumerated residue in F-1.
- Correcting the now-stale docstring of `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` (F-9).
  - Carrier-Declined: a DOCSTRING-ONLY prose correction, which is not a defect and carries no behavioral obligation: the test PASSES after E-02 and every assertion in it is already proven by V-04. The file is deliberately OUT of `- Scope-Paths:` so the finalize gate refuses any edit to a module whose unmodified assertions are this plan's primary evidence, and E-04 requires the staleness be REPORTED so a human can file it if they want the prose tidied. Filing a backlog item to rewrite one accurate-but-dated comment would cost more attention than the comment does.
- Closing backlog `4vfkl1` ("Two slow-marked test_installer deep-cleanup tests fail at HEAD").
  - Carrier: 4vfkl1
  - Carrier-Declined: not an uncarried obligation: the item IS its own carrier, it is `open` with `- Blocks-Release: next`, and it names exactly two failing tests, `3ypquf`'s (landed via `baxbdh`) and THIS item's. Executing this plan makes it closable, but a plan must not set another item's status, and its workflow-history note assigns the `tests.yml` `continue-on-error` removal to whichever of `57dwkc`, `3ypquf`, `4vfkl1`, `g0bdgg` closes last, which is an act for that item.
- Making the slow subset visible in the bare run, so a regression in it cannot hide.
  - Carrier: xuc9v0
  - Carrier-Declined: already owned elsewhere and needs no new carrier: backlog `xuc9v0` holds the CI-policy question and plan `4petcj` (approved) is implementing it. What this plan owes is not ADDING to the problem, which E-03 discharges by making its no-install case default-visible.

## Scope check

- Over-scope: none. No deep-cleanup tuple or function is touched, the ownership manifest is untouched, `emit_layout_artifacts` is untouched, and `agent_workflows/cli.py` is untouched. `tests/test_installer.py` and `tests/test_cli.py` are deliberately EXCLUDED from `- Scope-Paths:` so the gate refuses any edit to the tests that must pass as written.
- Under-scope: `agent_workflows/cli.py` needs no change, because every uninstall surface calls `engine.uninstall_repo` and reads `plan_deep_cleanup`; the interactive wizard path is covered end to end by the `tests/test_cli.py` node E-04 re-runs. The empty-directory prune needs no change, because step 7 of `uninstall_repo` already walks `.aw` deepest-first and only lacked the two files being gone (F-6 case A).
- Scope-Paths justification: `engine.py` holds the removal step (E-02); the new test file holds E-03; `CHANGELOG.md` holds E-05. E-01 and E-04 are measurement only and write no file.

## Required tests / validation

- `tests/test_uninstall_layout_artifacts.py` (new): one default-visible no-install case, plus a slow-marked class holding the real-install removal, the full `.aw/`-removal guarantee, and the two negative controls (drift preservation under keep-records, and `all_recoverable` on a committed install).
- `python3 -m pytest -o addopts="" -q "tests/test_installer.py::UninstallCompletenessTests" "tests/test_installer.py::DeepCleanupTests" "tests/test_cli.py::InstallAtomicWizardTests"` before and after: the two failures become passes with nothing else regressing. Measured on the authoring probe as `14 passed in 35.91s`.
- `python3 -m pytest -o addopts="" -q tests/test_installer.py tests/test_cli.py`: the whole slow modules, to catch any node the narrower selection misses.
- Bare `python3 -m pytest` before and after; compare failing node id sets. The new default-visible case MUST appear in this run.
- `aw sanitize --agent` and `aw check` clean before finalizing.

## Spec / documentation sync

- No `.spec.md` is in `- Scope-Paths:` and none is amended. Spec `kw5y2s` (`unified-workspace-hierarchy-spec-and-install-time-layout-emi`, approved) Section 6.1 specifies only the INSTALL-time emission of the two files, its four steps covering the model build, both writes, and the `.aw/.gitignore` patterns; grepping that file for `uninstall`, `remove`, and `cleanup` returns nothing, so it states no removal contract this plan could contradict. Spec `physical-aw-hierarchy-placement-and-migration` (implemented) mentions uninstall but not the layout artifacts or the deep-cleanup roots.
- The user-facing text this plan owes is E-05's `CHANGELOG.md` line, because the observable end state of `aw uninstall --deep` changes. The `aw uninstall --deep` help text needs no edit: it describes what `--deep` additionally removes (records scaffolding and legacy litter) and makes no claim about the layout artifacts, which the BASE uninstall now removes.

## Open questions

### OQ-01: Should the fix add `.aw/system` to `_DEEP_CLEANUP_ROOTS`, as the backlog item suggests, or remove the two emitted files in the base uninstall?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE BY DRIVING BOTH CANDIDATES; the backlog item's suggestion is REJECTED. It proposes adding `.aw/system` to `_DEEP_CLEANUP_ROOTS` classified as OTHER, by analogy with `.aw/workflow-artifacts`. The analogy does not hold, because `.aw/workflow-artifacts` is a tree of PURELY generated local scratch, whereas `.aw/system` also holds 158 manifest-owned files including every workflow body a user may have hand-edited. Two measured consequences follow. FIRST, IT DESTROYS PRESERVED USER CONTENT (F-4): `uninstall_repo` classifies an edited owned file as `drifted` and PRESERVES it unless forced, but `run_deep_cleanup` has no drift concept and removes every file under a root even with `--keep-records`, so a directory root makes the deep cleanup delete exactly what the base uninstall just promised to keep. Driven end to end: the edited `advise.md` survives base uninstall and is then gone. SECOND, IT REGRESSES `baxbdh` (F-5): both emitted files are gitignored, so `_git_file_state` returns `at_risk`, `all_recoverable` flips to False on a fully committed install, and `DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed` breaks again. A narrower variant adding the two exact FILE paths as roots plus matching `_DEEP_CLEANUP_REGENERABLE` entries WAS also driven and does work (`variant=both all_recoverable=True at_risk=[]`), but it is strictly worse than the chosen fix: it costs two tuple edits instead of one, it leaves the files present between a base uninstall and a cleanup that may never be offered (`--yes` without `--deep` skips it by design), and it classifies framework-generated output as opt-in "scaffolding that holds user content", which is what `_DEEP_CLEANUP_ROOTS`'s own comment says that tuple is for. THE CHOSEN FIX instead extends the step of `uninstall_repo` that ALREADY removes framework-generated, non-manifest files (`.aw/config`, `.aw/state`, `.aw/.gitignore`), created by plan `ejhzgk` for this identical defect shape: unowned framework files that no layer removed, so `.aw/` could never be fully removed. It touches no deep-cleanup tuple, so drift preservation and the at-risk classification are unchanged by construction, and it makes the base uninstall self-consistent, since a repo whose framework is gone no longer carries a layout document describing an installation that no longer exists (F-8). E-03 case (3) pins the rejection as an executable control rather than as prose.

### OQ-02: Should `.aw/system/VERSION` or any other `.aw/system` member be removed alongside the two layout files, which the backlog item asks to have confirmed?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO; confirmed by enumerating the directory and querying the manifest on a real install (F-3). `.aw/system` after install holds `VERSION`, `layout.json`, `layout.schema.json`, `managed-sections.json`, and `workflows/`. `VERSION` and all 158 files under `workflows/` ARE manifest-owned, so `plan_uninstall` already classifies them and `uninstall_repo` already removes them (with drift preserved on purpose). `managed-sections.json` is the ownership manifest itself, removed LAST in step 6 with the recorded reason that a mid-uninstall failure must leave the ownership record intact for a retry; pulling it earlier would break that recovery property. That leaves exactly `layout.json` and `layout.schema.json` unowned and unreachable, which is precisely the residue measured in F-1, so the fix needs no broader reach. The empirical check is that after E-02 the enumeration in E-01 returns nothing at all.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the two pytest failures verbatim (node ids plus the `AssertionError` line), the full enumeration of what remains under `.aw/` after the four-step sequence, the `git check-ignore -v` output for `.aw/system/layout.json`, and the manifest membership booleans for `.aw/system/VERSION`, `layout.json`, and `layout.schema.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/engine.py` showing ONLY the added removal loop and the extended comment, and showing NO change to `_DEEP_CLEANUP_ROOTS` or `_DEEP_CLEANUP_REGENERABLE`. Then paste a driven probe on a real install: the returned actions containing both `removed .aw/system/layout.*` lines, the `changed_out` list containing both paths, and `(repo / ".aw/system/layout.json").exists()` False for both. Confirm in writing that the added code references `AW_LAYOUT_JSON_PATH` and `AW_LAYOUT_SCHEMA_PATH` rather than string literals, and that no second empty-dir prune was added.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_uninstall_layout_artifacts.py` passing with its count, AND the same file run with the E-02 change reverted (for example via `git stash push agent_workflows/engine.py`) showing the default-visible case and slow cases (1) and (2) FAILING while controls (3) and (4) PASS. Paste a bare `python3 -m pytest tests/test_uninstall_layout_artifacts.py` proving the default-visible case is selected and the slow class deselected. State explicitly that no test in the file reads production source text, uses `inspect`/`ast`/regex over `engine.py`, or asserts tuple membership by reading code.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q "tests/test_installer.py::UninstallCompletenessTests" "tests/test_installer.py::DeepCleanupTests" "tests/test_cli.py::InstallAtomicWizardTests"` with its `N passed` summary and zero failures, plus `python3 -m pytest -o addopts="" -q tests/test_installer.py tests/test_cli.py` for the whole modules. Paste `git diff --stat` proving `tests/test_installer.py` and `tests/test_cli.py` are UNCHANGED. Paste the bare `python3 -m pytest` summary line before and after, and name any failing-node-id difference (an empty delta plus the new default-visible case is the expected result). Report the stale docstring as a follow-up without editing it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly one added `- Fixed:` line under `## 2.0.0 (pending)`, and paste the em/en-dash grep returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is authored `to-review` and carries no `- Readiness:` field, which is an output of `/plan-review` and must not be hand-written.

Execution contract: commit only the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Do not edit `tests/test_installer.py` or `tests/test_cli.py`: they are excluded from scope precisely so their assertions prove the fix as written. Paste ACTUAL runner output for every validation item; do not claim a test run that did not happen. After every `E-*` is performed and every `V-*` is verified with pasted evidence, run `aw ipd lint --phase pre-transition` and require conforming, then move this plan to `.aw/records/plans/executed/` with the tooled lifecycle transition (`aw ipd set executed`), never by hand. Backlog `57dwkc` is set `graduated` by the runner on verification; do not set it `done` from this plan. The `- Blocks-Release: next` gate is inherited from that item and must travel with this plan.
