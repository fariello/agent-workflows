# IPD: complete uninstall - remove orphaned config/state/.gitignore/setup-marker so .aw/ can be fully removed; fix file-vs-dir cleanup label

- Date: 2026-08-20
- Kind: child
- Concern: uninstall completeness + honesty. On a fresh install then `aw uninstall .` (+ deep cleanup), several AW-owned file classes survive because they are removed by NEITHER the manifest-driven base uninstall NOR the deep cleanup: `.aw/config/{project,local}.json`, `.aw/state/**` (`install.json`, `durable/install.json`, `durable/history/installs.jsonl`, `history/installs.jsonl`), `.aw/.gitignore`, `.aw/setup-repo-needed.md`. So `.aw/` can never be fully removed. Separately, the deep-cleanup announcement mislabels FILE roots as directories.
- Scope: `agent_workflows/engine.py` (`uninstall_repo` to also remove the deterministic framework lifecycle files config+state+.gitignore + call `remove_setup_marker`; keep `_DEEP_CLEANUP_ROOTS` owning records/; partition the deep-cleanup plan into a records class vs non-records scaffolding) + `agent_workflows/cli.py` (a DEDICATED records keep/remove prompt distinct from the non-records scaffolding prompt; deep-cleanup announcement label: file vs directory) + regression tests. Does NOT change the manifest format or the drift-preservation behavior. Sibling to awinstallfix-01 (install side); this is the uninstall side.
- Status: executed
- Set: awuninstallfix
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ejhzgk

## Workflow history

- 2026-08-20 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-20 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; anchors verified (UN-001..UN-004 confirmed); PR-001 (records-keep data-safety: run_deep_cleanup must not receive records files when kept), PR-002 (setup marker handled once) fixed in place; OQ-01 resolved. review-finalize lint conforming.
- 2026-08-20 approved (maintainer, human): cleared for execution.
- 2026-08-20 executed (agy gemini exec + opencode independent validation): E-01..E-06 implemented in commits 7a93ff2 + 53e2751; V-01..V-06 independently verified (base uninstall removes config/state/.gitignore + remove_setup_marker; dedicated records keep/remove prompt; run_deep_cleanup(remove_records=False) preserves records - data-safety; empty-.aw prune; file-vs-dir label; spec 15.4 synced). Full serial suite 1260 passed, 1 skipped; sanitize clean; attention valid.

## Goal

Make `aw uninstall` actually able to fully remove the framework: the base uninstall removes the deterministic, framework-created lifecycle files (`.aw/config/*`, `.aw/state/**`, `.aw/.gitignore`, and the `.aw/setup-repo-needed.md` marker) in addition to the manifest-owned files; the deep cleanup asks a DEDICATED question about keeping the user's authored records under `.aw/records/` (plans/specs/walkthroughs/etc.) separate from the throwaway non-records scaffolding, so a user can keep their work while everything else goes; and it fixes the announcement so file roots are not mislabeled as directories. Keeping records leaves `.aw/records/` + `.aw/`; removing records (with config/state/.gitignore/marker already gone) prunes `.aw/` to nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: base uninstall removes the orphaned framework lifecycle files

- [x] E-01 In `engine.uninstall_repo` (engine.py:3769), after the manifest-driven removals, ALSO remove the deterministic framework-created lifecycle files that are not in the manifest: `.aw/config/project.json`, `.aw/config/local.json`, `.aw/state/` (recursively: `install.json`, `durable/`, `history/`), and `.aw/.gitignore`. Use the existing `_uninstall_remove(repo_root, rel, use_git)` (git rm when tracked, unlink otherwise) so tracked ones (project.json, .gitignore) are staged for removal and local/ignored ones (local.json, state/**) are unlinked. Record each in `changed_out` and append a human action line. Guard each with an existence check (skip silently if absent). Do NOT remove `.aw/records/` here (that is the opt-in deep cleanup - it may hold user content).
  - Depends on: none
  - Expected outcome: after `aw uninstall`, `.aw/config/`, `.aw/state/`, and `.aw/.gitignore` are gone; only `.aw/records/` (+ any user content) may remain for the deep-cleanup offer.
  - Execution state: performed

- [x] E-02 In `engine.uninstall_repo`, call `remove_setup_marker(repo_root)` (engine.py:4621; idempotent, returns True when it removed the file) as part of the uninstall so `.aw/setup-repo-needed.md` never survives an uninstall (defect C: otherwise a later state read believes setup is still pending on an uninstalled repo). Record it in `changed_out`/actions when the marker existed. The marker is handled ONCE here (via `remove_setup_marker`); do not also enumerate it in the E-01 config/state sweep, to avoid double-handling.
  - Depends on: none
  - Expected outcome: `.aw/setup-repo-needed.md` is absent after uninstall.
  - Execution state: performed

### Task group 2: dedicated records keep/remove prompt + empty-.aw prune + label bug

- [x] E-03 Partition the deep cleanup into a RECORDS class and a NON-RECORDS scaffolding class, and ask about them SEPARATELY (maintainer request: "deep clean should ask about keeping records"). In `engine.plan_deep_cleanup`/`DeepCleanupPlan` (engine.py:3616-3661), tag each root/file as `records` (the `.aw/records/*` and legacy `.agents/*` record roots) vs `other` (`.gitleaksignore`, `.github/workflows/secret-scan.yml`), exposing the split (e.g. `records_files`/`other_files` or a per-file kind) without changing the existing `files`/`counts`/`at_risk` contract. In the CLI deep-cleanup handler (cli.py:2520-2583), replace the single "Remove this scaffolding too?" prompt with: first handle/announce the non-records scaffolding as today, then a DEDICATED prompt for records, e.g. "Keep your authored records under .aw/records/ (plans, specs, walkthroughs, etc.)? [Y/n]" - Yes leaves ALL of `.aw/records/` in place, No removes it. Keep the `--deep` (remove everything) and non-interactive/`--yes`/`--force` semantics (do NOT silently delete records; default keep). CRITICAL data-safety contract: `run_deep_cleanup` currently deletes EVERY path in `plan.files`, so keeping records MUST be enforced by NOT giving those files to it - either pass a filtered plan whose `files` excludes the records class, or add an explicit `remove_records: bool` / class-selector parameter that `run_deep_cleanup` honors. The executor MUST verify (test) that a kept-records run leaves every `.aw/records/*` file untouched; a naive "pass the full plan" that deletes records is a REGRESSION and unacceptable.
  - Depends on: none
  - Expected outcome: the user is asked specifically whether to keep `.aw/records/`; choosing keep preserves all records while other scaffolding is removed; choosing remove deletes records too.
  - Execution state: performed

- [x] E-04 Ensure the emptied `.aw/` tree is pruned according to the records choice. After the base-uninstall removals (E-01/E-02) plus the deep-cleanup outcome (E-03), prune empty dirs deepest-first (only-if-empty `rmdir`, never `rm -rf`, never prune a dir holding non-AW content), reusing the prune approach in `run_deep_cleanup` (engine.py:3682-3700) and extending the base uninstall to prune the `.aw/config`/`.aw/state` dirs it emptied. If the user KEEPS records, `.aw/records/` and the `.aw/` parent remain (the ONLY reason `.aw/` survives is the user's explicit keep). If the user REMOVES records, `.aw/` prunes to nothing.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: keep-records -> `.aw/records/` + `.aw/` remain, nothing else; remove-records -> no `.aw/` at all.
  - Execution state: performed

- [x] E-05 Fix the file-vs-directory label in the deep-cleanup announcement (defect B). In `cli.py` (the announcement at cli.py:2529 `print(f"  - {n} file(s) under {root}/")` and the dry-run variant at cli.py:2506), the hardcoded trailing `/` mislabels FILE roots (`.gitleaksignore`, `.github/workflows/secret-scan.yml`) as directories. Render a directory root as `<root>/` but a file root as just `<root>` (detect via `(repo_root / root).is_dir()` or by tracking the root kind in the plan), and phrase file roots naturally (e.g. `- .gitleaksignore (1 file)` vs `- .aw/records/plans/ (11 files)`). Also make `file(s)` agree in number where trivial.
  - Depends on: none
  - Expected outcome: the deep-cleanup list shows file roots without a spurious trailing slash and with sensible wording; directory roots keep the trailing slash.
  - Execution state: performed

### Task group 3: tests

- [x] E-06 Add regression tests in `tests/test_installer.py` / `tests/test_cli.py`: (a) install into a temp repo, then `uninstall` (force, non-interactive) and assert `.aw/config/`, `.aw/state/`, `.aw/.gitignore`, and `.aw/setup-repo-needed.md` are ALL gone; (b) install -> uninstall -> deep cleanup with records REMOVE -> assert NO `.aw/` directory remains at all (fully clean); (c) install -> uninstall -> deep cleanup with records KEEP -> assert `.aw/records/` (user content) is preserved AND config/state/marker/.gitignore are gone AND the non-records scaffolding (`.gitleaksignore`) is removed; (d) the records keep/remove prompt is asked SEPARATELY from the non-records scaffolding (assert the dedicated records question text appears); (e) the deep-cleanup announcement for a FILE root (`.gitleaksignore`) does not contain the mislabeled `.gitleaksignore/`. Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04,E-05
  - Expected outcome: all new tests pass; full serial suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Base `uninstall_repo` (engine.py:3769) is MANIFEST-DRIVEN: it removes only files recorded in `.aw/system/managed-sections.json` (+ managed blocks/shims), preserving drifted user-edited owned files. Runtime-generated files (`.aw/config/*`, `.aw/state/**`, `.aw/.gitignore`, setup marker) are NOT in the manifest, so the base pass never touches them.
- `_DEEP_CLEANUP_ROOTS` (engine.py:3589-3612) lists `.aw/records/*` + `.gitleaksignore` + `.github/workflows/secret-scan.yml` ONLY - not config/state/.gitignore/marker. So those fall through BOTH layers.
- Verified natures (in this source repo, a proxy for an installed repo): `.aw/config/project.json` + `.aw/.gitignore` are TRACKED framework artifacts; `.aw/config/local.json`, `.aw/state/**`, `.aw/setup-repo-needed.md` are untracked+gitignored local runtime state. `_uninstall_remove` handles both (git rm vs unlink).
- `remove_setup_marker(repo_root)` (engine.py:4621) already exists and returns True when it removed the marker; `write_setup_marker` (engine.py:4610) creates it at install. `SETUP_MARKER_PATH = ".aw/setup-repo-needed.md"` (engine.py:3957).
- `run_deep_cleanup` (engine.py:3664) already prunes emptied dirs deepest-first with only-if-empty `rmdir` and never `rm -rf` a host dir - reuse that prune pattern for the base-uninstall dirs.
- Deep-cleanup announcement: cli.py:2529 (live) + cli.py:2506 (dry-run) hardcode a trailing `/` on every root; `_DEEP_CLEANUP_ROOTS` mixes dir roots and FILE roots (`.gitleaksignore`, `secret-scan.yml`).
- Design decision (maintainer): base uninstall removes config+state+.gitignore+marker (deterministic framework files; local ones carry no user content, tracked ones are git-restorable); records/ stays behind the opt-in deep cleanup (may hold user-authored work).

## Findings

| ID | Severity | Evidence | Finding |
|----|----------|----------|---------|
| UN-001 | HIGH | engine.py:3769 (manifest-only) + `_DEEP_CLEANUP_ROOTS` engine.py:3589 (no config/state) | `.aw/config/*`, `.aw/state/**`, `.aw/.gitignore` are removed by neither uninstall layer, so `.aw/` can never be fully removed after install. |
| UN-002 | MEDIUM | engine.py:3769 (no remove_setup_marker call); marker survives in the reporter's `find .aw/` | `.aw/setup-repo-needed.md` survives uninstall, so setup-pending state persists on an uninstalled repo. |
| UN-003 | MEDIUM | cli.py:2556-2577 single "Remove this scaffolding too?" prompt bundling records with throwaway scaffolding | The deep cleanup does not ask separately about the user's authored records; a user cannot keep `.aw/records/` (plans/specs/walkthroughs) while removing the rest - it is one all-or-nothing prompt. |
| UN-004 | LOW | cli.py:2506/2529 `f"...under {root}/"` | Deep-cleanup announcement mislabels FILE roots (`.gitleaksignore`, `secret-scan.yml`) as directories with a spurious trailing slash. |

## Proposed changes (ordered, validatable)

1. Base uninstall removes config+state+.gitignore (E-01).
2. Base uninstall clears the setup marker via remove_setup_marker (E-02).
3. Dedicated records keep/remove prompt, separate from non-records scaffolding (E-03).
4. Prune emptied `.aw/` dirs per the records choice (E-04).
5. Fix file-vs-dir label in the deep-cleanup announcement (E-05).
6. Regression tests incl. records-keep vs records-remove + empty-.aw guarantee (E-06).

## Deferred / out of scope (with reason)

- Per-records-subtree prompts (asking separately for plans vs specs vs walkthroughs): out of scope - maintainer chose ONE records/ keep-or-remove question; a finer split can be a follow-on if wanted.
- The manifest format / drift-preservation behavior: unchanged.
- Install-side defects (mid-interview writes, ctrl-c, companion validation): owned by the sibling IPD awinstallfix-01, not here.
- Removing a user's own non-AW files that happen to live under `.aw/` if they put them there: never - prune only when empty.

## Scope check

- Over-scope: none - each E maps to a confirmed uninstall-completeness defect.
- Under-scope: none - covers config/state/.gitignore, the marker, the empty-dir prune, the label, and tests.

## Required tests / validation

`tests/test_installer.py`/`tests/test_cli.py`: (a) uninstall removes `.aw/config/`, `.aw/state/`, `.aw/.gitignore`, setup marker; (b) uninstall + deep cleanup with records REMOVE leaves NO `.aw/`; (c) uninstall + deep cleanup with records KEEP preserves `.aw/records/` but removes config/state/marker/.gitignore AND the non-records scaffolding; (d) records keep/remove is a SEPARATE prompt from the non-records scaffolding; (e) file-root announcement has no spurious trailing slash. Full serial suite (`python3 -m pytest -p no:xdist`) green.

## Spec / documentation sync

The uninstall/rollback behavior is covered by spec `20260809-2211-01` (L40 "safe migration, rollback, uninstall"); if the spec enumerates what uninstall removes, add config/state/.gitignore/marker to that enumeration. Otherwise N/A (behavior conforms to the "safe uninstall" clause). Confirm during execution and update if the spec is specific.

## Open questions

### OQ-01: Should the tracked framework files (project.json, .gitignore) be removed by base uninstall, or reserved for deep cleanup since they are git-tracked?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Maintainer decided base uninstall removes them: they are framework-owned (not user-authored), and `_uninstall_remove` uses `git rm` so the removal is staged and fully restorable via `git checkout` if the user changes their mind (same safety the deep-cleanup message already advertises). Records/ (possible user content) stays behind the opt-in deep cleanup.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a test installs then uninstalls (force) and asserts `.aw/config/project.json`, `.aw/config/local.json`, `.aw/state/install.json`, `.aw/state/durable/`, and `.aw/.gitignore` are all absent afterward; `uninstall_repo` records them in the changed list (git rm for tracked, unlink for ignored).
  - Observed evidence: `UninstallCompletenessTests.test_uninstall_removes_config_state_gitignore_and_setup_marker` asserts `.aw/config/project.json`, `.aw/config/local.json`, `.aw/config/`, `.aw/state/install.json`, `.aw/state/`, and `.aw/.gitignore` are absent post-uninstall and tracked files are present in `changed` (`.aw/config/project.json`, `.aw/.gitignore`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: after uninstall, `.aw/setup-repo-needed.md` does not exist; `remove_setup_marker` is invoked from the uninstall path (test asserts marker gone after install-then-uninstall).
  - Observed evidence: `UninstallCompletenessTests.test_uninstall_removes_config_state_gitignore_and_setup_marker` asserts `.aw/setup-repo-needed.md` is absent and recorded in `changed`; `remove_setup_marker` is called in `engine.uninstall_repo`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the deep cleanup asks a DEDICATED records question (assert the "Keep your authored records under .aw/records/" prompt text appears, distinct from the non-records scaffolding prompt); answering keep leaves EVERY `.aw/records/*` file untouched (test asserts the files still exist and were not passed to removal), answering remove deletes them; `run_deep_cleanup` removes the non-records scaffolding independent of the records choice. `DeepCleanupPlan` exposes the records/non-records split and `run_deep_cleanup` honors the selector (never deletes records when kept).
  - Observed evidence: `UninstallCompletenessTests.test_deep_cleanup_plan_partitions_records_and_other` validates `records_files` vs `other_files` partition and `filtered()` method; `test_deep_cleanup_records_keep_preserves_records_and_removes_other` verifies `run_deep_cleanup(remove_records=False)` leaves records untouched while removing non-records scaffolding; `InstallAtomicWizardTests.test_interactive_deep_cleanup_separate_records_prompt_keep_records` asserts distinct "Remove this scaffolding too?" and "Keep your authored records under .aw/records/ (plans, specs, walkthroughs, etc.)?" prompts in CLI.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: install -> uninstall -> deep cleanup records REMOVE leaves NO `.aw/` directory (assert `not (repo/'.aw').exists()`); install -> uninstall -> deep cleanup records KEEP leaves `.aw/records/` present but `.aw/config`/`.aw/state`/`.aw/.gitignore`/marker gone and non-records scaffolding removed.
  - Observed evidence: `UninstallCompletenessTests.test_deep_cleanup_records_remove_leaves_no_aw_directory` and `test_interactive_deep_cleanup_records_remove_fully_cleans_aw` assert `not (repo / ".aw").exists()`; `test_deep_cleanup_records_keep_preserves_records_and_removes_other` asserts `.aw/records/` and `.aw/` remain while `.aw/config`, `.aw/state`, `.aw/.gitignore`, setup marker, and `.gitleaksignore` are removed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the deep-cleanup announcement text for the `.gitleaksignore` file root contains no `.gitleaksignore/` (no spurious trailing slash); a directory root like `.aw/records/plans/` still shows the trailing slash. Asserted by capturing the announcement output in a test.
  - Observed evidence: `InstallAtomicWizardTests.test_deep_cleanup_announcement_file_vs_dir_label` asserts dry-run output contains `.gitleaksignore (1 file)` without `.gitleaksignore/` and contains `.aw/records/plans/`; `test_interactive_deep_cleanup_separate_records_prompt_keep_records` also asserts `.gitleaksignore (1 file)`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_installer.py tests/test_cli.py -p no:xdist -q` green for the new cases (records keep + records remove + separate-prompt + label); FULL serial suite `python3 -m pytest -p no:xdist` tail pasted, green.
  - Observed evidence: INDEPENDENT opencode verification: the exact V-mapped tests exist in `tests/test_installer.py` (`test_uninstall_removes_config_state_gitignore_and_setup_marker`, `test_deep_cleanup_records_remove_leaves_no_aw_directory`, `test_deep_cleanup_records_keep_preserves_records_and_removes_other`, `test_deep_cleanup_plan_partitions_records_and_other`) and pass; the keep-records test asserts a planted user plan SURVIVES + `.aw/records/`+`.aw/` remain while config/state/.gitignore/marker/.gitleaksignore are removed (the PR-001 data-safety invariant). Code re-verified: `run_deep_cleanup(remove_records=False)` excludes `records_files` (engine.py:3713) and skips pruning records dirs (3725); `_format_cleanup_root` (cli.py:2553) renders file roots without a trailing slash. INDEPENDENT FULL serial suite: `python3 -m pytest -p no:xdist` => `1260 passed, 1 skipped in 263.41s (0:04:23)`; `aw sanitize --agent` rc=0; `aw attention --check` valid. All V-01..V-06 re-verified against actual repo state (agy finished cleanly this run; work in commits 7a93ff2 + 53e2751).
  - Result: pass

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 6 E-items exceed the soft cap of 5, but they are one cohesive fix for one goal (a `aw uninstall` that can fully and honestly remove the framework while letting the user keep their authored records) across one tight code area (engine `uninstall_repo`/`plan_deep_cleanup`/`run_deep_cleanup` + the cli deep-cleanup handler). E-01/E-02 (remove orphaned config/state/marker) and E-04 (prune) are mechanically interdependent; E-03 (records prompt) determines what E-04 prunes; E-05 (label) is a one-line honesty fix in the same announcement; E-06 bundles the tests that prove the whole (keep vs remove, empty-.aw, separate prompt, label). Splitting would create artificial seams and duplicate the install/uninstall test surface. Cohesion outweighs the count.

This plan MUST be human-approved (Status: approved) before execution; it is not auto-run. Execution contract: commit only files changed by the plan, path-scoped, never push; run the full serial suite and paste the ACTUAL runner output as V evidence; base uninstall removes config/state/.gitignore/marker but records/ is removed ONLY when the user answers the dedicated records prompt (or --deep); never `rm -rf` a host dir (prune only-if-empty); reuse `_uninstall_remove`/`remove_setup_marker`/the deep-cleanup prune pattern rather than reinventing; on completion lint --phase pre-transition while approved, then flip to executed + executed history line + remove the Approval line + git mv to executed/ + post-transition lint. Do not mark executed until every V item is verified with concrete evidence.
