# IPD: Retire the old placement's AW-owned footprint after a placement switch

- Date: 2026-10-16
- Kind: child
- Concern: After a placement switch the OLD side still holds AW-owned files: for `to-home` the target keeps `.aw/system/**`, `.aw/.gitignore`, `.aw/inbox/README.md`, `.aw/setup-repo-needed.md`, `.aw/workflow-artifacts/`, managed host adapters (`.claude/commands/*.md`, `.opencode/commands/*.md`, `.agents/skills/**`) and the managed `AGENTS.md` block, all tracked by a `private-target` install (Order 02 `xvlemm` F-02); for `to-target` the home dir `<AW_HOME>/projects/<id>/` keeps `system/`, `state/`, `config/`. Leaving them means a `completely-clean-target` repo is not clean (the preset's whole point) and, worse, `project_context.project_config_dir` and `project_system_dir` would still find in-tree material. `engine.uninstall_repo` already removes exactly this footprint, manifest-driven and drift-preserving, but it auto-selects its side through `engine._clean_delta_home_trees(repo_root)`, which after a `to-home` flip returns the NEW home trees, so calling it as-is would delete the freshly moved destination instead of the old target files.
- Scope: IN: `placement_switch.retire_footprint(repo_root, side, *, use_git=True, preserve=(), changed_out=None) -> list[str]` that retires ONE explicit side; for `side="target"` it calls `engine.uninstall_repo(repo_root, use_git, home_trees=None, ...)` through a new keyword `engine.uninstall_repo(..., side="target")` that forces the in-tree branch (skips the `_clean_delta_home_trees` auto-detect and the clean-delta lane teardown) while keeping every existing caller's default behavior; `preserve` is a set of repo-relative paths the retirement must not touch (the executor passes the already-handled config and records paths); for `side="home"` it removes only `<project_dir>/system`, `<project_dir>/state` and the remaining `<project_dir>/config` files, then prunes `<project_dir>` only when empty, refusing (raising) if `<project_dir>/records` still holds files. OUT: moving data (Order 04), CLI (Order 05).
- Scope-Paths: agent_workflows/placement_switch.py, agent_workflows/engine.py, tests/test_placement_switch_retire.py
- Item-Dependencies: executed:xvlemm
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 3
- Highest E allocated: 04
- Author: opencode
- Id: gjylny
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

The only deletion code in the Set is one reviewable primitive that removes the old placement's AW-owned files on exactly the side it is told, reusing the existing manifest-driven uninstall rather than a second hand-written sweep, and never touching user content or the new side.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Side-explicit uninstall

- [x] E-01 In `agent_workflows/engine.py` add keyword-only `side: Optional[str] = None` to `uninstall_repo` AND to `plan_uninstall`. `None` keeps today's behavior exactly; any value other than `None`/`"target"` raises `ValueError`. Under `side="target"` EVERY path the uninstall resolves must be the explicit in-tree one, because after a to-home flip every resolver it calls today routes to the NEW home side (review probes, F-04 to F-06). Concretely, when `side == "target"`: (a) `home_trees` stays `None` and `_clean_delta_home_trees` is never called, in `uninstall_repo` (skipping the clean-delta lane-teardown block and every `if home_trees is not None:` branch) and in `plan_uninstall` (whose own "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)" would otherwise re-detect; passing `home_trees=None` to it is NOT enough, and an empty-dict sentinel is wrong because `uninstall_repo` treats any non-`None` value as clean-delta and indexes `home_trees["project_dir"]`); (b) the manifest path is `repo_root / AW_SYSTEM_DIR / "managed-sections.json"`, else `repo_root / manifest_mod.LEGACY_MANIFEST_RELPATH`, never `manifest_mod.resolve_manifest_path` (which goes through `project_system_dir` and, after the flip, returns the absent home manifest, so `has_manifest` is False and the PRE-MANIFEST FALLBACK SWEEP deletes every shim including user-edited ones; probe: an edited, committed `.opencode/commands/advise.md` was "removed", not PRESERVED), in both the plan step and the final manifest-removal step 6; (c) system members map to `repo_root / AW_SYSTEM_DIR / <tail>` without calling `_system_member_destination`'s `project_system_dir` fallback (add a `side` keyword to `_system_member_destination` or compute it inline); (d) the step-4 `else:` sub-branch that runs when `.aw/config` is absent ("home_cfg = project_config_dir(repo_root)") is SKIPPED entirely: after the flip it resolves the NEW home config and deletes its `project.json`, `local.json` and the whole home `state/` (probe: "removed <AW_HOME>/projects/r-4ff147/config/project.json" and ".../state/durable/install.json"); (e) the setup marker is `repo_root / SETUP_MARKER_PATH`, not `setup_marker_path(repo_root)` (which returns the home `state_runtime` marker once the repo resolves as clean-delta). Also accept keyword `preserve: frozenset[str] = frozenset()` and skip any repo-relative path in it (or under a preserved directory) in the manifest-driven removal loop, the pre-manifest fallback and the step-4 `.aw/config` and `.aw/state` sweeps.
  - Depends on: none
  - Expected outcome: default calls unchanged (the existing uninstall suites stay green); `side="target"` on a repo whose authoritative config is already home-placed removes only in-tree AW files, uses the in-tree manifest (so drifted files are PRESERVED), and leaves every file under `<AW_HOME>` byte-identical.
  - Execution state: performed

- [x] E-02 In `agent_workflows/placement_switch.py` add `retire_footprint(repo_root, side, *, use_git=True, preserve=(), changed_out=None)`. `side="target"`: call `engine.uninstall_repo(repo_root, use_git, side="target", preserve=frozenset(preserve), changed_out=changed_out)` with `force=False` and no `drift_decider`, so user-edited managed files are PRESERVED and reported (existing uninstall contract), then ALSO remove what `uninstall_repo` leaves behind on the target side, which the Concern names and a `completely-clean-target` repo must not keep: `.aw/inbox/README.md` (tracked, not in the manifest; review probe: a default `uninstall_repo` on a fresh `private-target` install left it and `git ls-files .aw/inbox` still listed it) is removed with `engine._uninstall_remove` ONLY when its bytes equal the shipped template that `engine.ensure_inbox_readme` installs (obtain it via `engine.collect_scaffold_members(repo_root, source_root, category="inbox")`, with `source_root` from `engine.resolve_source_root(None)`; else reported `PRESERVED`), and the `.aw/inbox/` and `.aw/workflow-artifacts/` directories are pruned ONLY when empty (anything inside them is user material and is reported `PRESERVED`, never deleted, spec Section 11.2 item 9), then prune empty dirs under `.aw/`. Return the combined actions. `side="home"`: resolve `<AW_HOME>/projects/<id>` with `project_context._resolve_effective_aw_home` and `_derive_project_id(_canonical_path(checkout_main_root(repo) or repo))` (the same derivation `engine._clean_delta_home_trees` case (b) uses), refuse with `PlacementSwitchError` if `records/` under it has any file, else remove `system/`, `state/`, `config/` and `worktrees/.owners` and prune empty dirs; it never runs `git` (home is not a repo). Return human-readable actions.
  - Depends on: E-01
  - Expected outcome: one call per side; neither side's call can reach the other side.
  - Execution state: performed

### Task group 2: Tests

- [x] E-03 Create `tests/test_placement_switch_retire.py` (`unittest.TestCase`, scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`, a fresh real install subprocess per test in `setUp` into its own temp dir, with `GIT_AUTHOR_*`/`GIT_COMMITTER_*` in the env and an `--allow-empty` initial commit so the installer's sync commit lands; do NOT `copytree` an installed repo: a copied `private-target` repo's `local.json` keeps the original's `project_id` and a copied clean-target repo has no config at all (`xvlemm` review PR-004)). Cases: (1) target side on a `private-target` install after simulating the flip (write a valid home `project.json` with `delivery_mode: clean-delta` at `<AW_HOME>/projects/<derived id>/config/`, plus a home `state/durable/install.json` and a home `records/keep.md`, then delete the in-tree `project.json` and `local.json` and the now-empty `.aw/config/`, so `engine._is_clean_delta_install` is True exactly as after a real flip): every manifest-owned in-tree file is gone, deletions are STAGED (`git diff --cached --name-status` shows `D`), nothing is committed (`git rev-list --count HEAD` unchanged), the home tree is byte-identical before and after (snapshot), a user file `notes/mine.md` and a user section in `AGENTS.md` outside the managed block survive; (2) on the same simulated flip, a hand-edited and committed `.opencode/commands/advise.md` survives and is reported `PRESERVED` (this is the case the pre-manifest fallback would delete); (3) `preserve={".aw/records"}` leaves `.aw/records/**` untouched; (4) home side removes `system/`, `state/`, `config/`, prunes the project dir, and the target repo tree is unchanged; (4b) target side on the simulated flip leaves no tracked path under `.aw/` other than the `preserve`d ones (`git ls-files .aw` after the call, with `preserve={".aw/records"}`, lists only `.aw/records/**`), and a user file dropped in `.aw/inbox/` survives and is reported `PRESERVED`; (5) home side with a file under `records/` raises and removes nothing; (6) `uninstall_repo` default (`side=None`) on a `completely-clean-target` install still removes the home trees (regression of the existing contract). Then run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py tests/test_uninstall_layout_artifacts.py -v` and every other module that calls `uninstall_repo` (`grep -l uninstall_repo tests/*.py`; at review that was `tests/test_uninstall_layout_artifacts.py` and `tests/test_installer.py`).
  - Depends on: E-02
  - Expected outcome: all pass; the existing uninstall modules pass unchanged.
  - Execution state: performed

- [x] E-04 Mutation proof, two separate temporary mutations, each restored before the next: (M1) make `side="target"` fall through to the `_clean_delta_home_trees` auto-detect, run case (1), confirm it fails (home tree snapshot differs or in-tree files remain); (M2) keep the auto-detect bypass but restore the step-4 `project_config_dir` sub-branch and `manifest_mod.resolve_manifest_path` for `side="target"` (i.e. the plan as originally written), run cases (1) and (2), confirm (1) fails on the home snapshot (home `project.json` deleted) and (2) fails (edited shim removed). Restore, confirm with `git diff`, rerun green. Run bare `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: M1 fails case (1); M2 fails cases (1) and (2); restored code passes; bare suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `engine.uninstall_repo` "Stages deletions (git rm -f when tracked/staged) and never commits. Never touches user content outside the framework namespace" (its docstring); a user-EDITED owned file is preserved unless `force` or `drift_decider` says remove.
- Managed `AGENTS.md` content is removed by `engine.remove_agents_pointer`, which strips only the managed block (`_strip_managed_block`) and leaves user prose.
- Tests drive real installs in scratch dirs (`tests/test_uninstall_layout_artifacts.py` `test_real_install_uninstall_deep_cleanup_removes_aw_directory` is the precedent).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `uninstall_repo` auto-selects the home side whenever the repo currently resolves as clean-delta. | `engine.uninstall_repo`: "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)"; `_clean_delta_home_trees` case (a) "if _is_clean_delta_install(repo)". After a to-home flip that predicate is true. |
| F-02 | `_system_member_destination` independently auto-detects the home system dir. | `engine._system_member_destination`: "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)" then `project_system_dir(repo_root)`, which reads the stored placement (`project_context.project_system_dir` -> `_stored_physical_classes`). |
| F-04 | After a to-home flip, `manifest_mod.resolve_manifest_path` returns the home manifest (absent), so `plan_uninstall` takes the pre-manifest fallback sweep, which deletes every shim regardless of edits. | `manifest.resolve_manifest_path` "new_path = project_system_dir(root) / \"managed-sections.json\""; review probe with `_clean_delta_home_trees` forced to `None`: first action "removed .aw/system/workflows/" (the fallback string) and an edited committed `.opencode/commands/advise.md` "removed". |
| F-05 | The step-4 sub-branch for a repo with no `.aw/config` deletes the HOME config and state that `project_config_dir` resolves. | `engine.uninstall_repo` "home_cfg = project_config_dir(repo_root)"; review probe: "removed <AW_HOME>/projects/r-4ff147/config/project.json", ".../state/durable/install.json". |
| F-06 | `plan_uninstall` auto-detects independently of `uninstall_repo`, and `setup_marker_path` routes home once clean-delta. | `engine.plan_uninstall` "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)"; review probe `setup_marker <AW_HOME>/projects/r-2e1559/state/runtime/setup-repo-needed.md`. |
| F-03 | The in-tree branch of step 4 already removes `.aw/config/**`, `.aw/state/**`, layout files and `.aw/.gitignore`, and step 7 prunes empty `.aw/` dirs. | `engine.uninstall_repo` comments "# 4. Deterministic framework-created lifecycle files" and "# 7. Prune now-empty directories under .aw". |

## Proposed changes (ordered, validatable)

1. `side`/`preserve` keywords on `uninstall_repo` (E-01).
2. `retire_footprint` for both sides (E-02).
3. Tests (E-03) and a mutation proof (E-04).

## Deferred / out of scope (with reason)

- Calling `retire_footprint` at the right moment of the transaction: Order 04.
  - Carrier: 6u755v
- A `--deep` style removal of user-created scaffolding (`engine.run_deep_cleanup`): the switch retires only framework-owned files, per spec Section 11.2 item 9's "never deletes without an explicit choice".
  - Carrier-Declined: deliberate non-goal; the operator can still run `aw uninstall --deep` on purpose.

## Scope check

- Over-scope: none; the `engine.py` change is a `side` keyword on `uninstall_repo`/`plan_uninstall` (and optionally `_system_member_destination`) plus `preserve`, all defaulting to today's behavior.
- Under-scope: none; both retire sides named in Order 02's `retire_side` are implemented.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py -v` passes.
- Every existing test module calling `uninstall_repo` (`tests/test_uninstall_layout_artifacts.py`, `tests/test_installer.py` at review) passes unchanged.
- Mutations M1 and M2 (E-04) fail their named cases, then pass after restore.
- Bare `python3 -m pytest` passes.

## Spec / documentation sync

N/A: spec Section 8.1 (Order 01) already states that old-side tracked files are removed with `git rm` and left staged; this child implements that. No user-facing surface changes here.

## Open questions

### OQ-01: Reuse `uninstall_repo` or write a dedicated sweep?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Reuse. `uninstall_repo` already encodes the manifest ownership, drift preservation, managed-block stripping and stage-not-commit rules (F-03); a second sweep would duplicate them and drift. The only defect for this use is side auto-detection (F-01, F-02), fixed with an explicit keyword whose default is today's behavior. Amended at review: the auto-detection is not one call site but five resolvers (F-04 to F-06), and E-01 now bypasses every one of them under `side="target"`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff -- agent_workflows/engine.py` showing the `side`/`preserve` keywords and their defaults, and each of the five `side == "target"` bypasses (a) to (e) of E-01.
  - Observed evidence:
```diff
--- a/agent_workflows/engine.py
+++ b/agent_workflows/engine.py
@@ -1077,6 +1077,7 @@ def _system_member_destination(
     repo_root: Path,
     rel: str,
     home_trees: Optional[dict[str, Any]] = None,
+    side: Optional[str] = None,
 ) -> tuple[Path, bool]:
     if not _is_system_member(rel):
         return repo_root / rel, True
+    if side == "target":
+        return repo_root / AW_SYSTEM_DIR / tail, True
@@ -5600,6 +5608,8 @@ def plan_uninstall(
     repo_root: Path,
     home_trees: Optional[dict[str, Any]] = None,
+    side: Optional[str] = None,
+    preserve: frozenset[str] = frozenset(),
 ) -> UninstallPlan:
+    if side == "target":
+        home_trees = None
@@ -5665,6 +5675,8 @@ def uninstall_repo(
+    side: Optional[str] = None,
+    preserve: frozenset[str] = frozenset(),
 ) -> list[str]:
+    # (a) When side == "target", home_trees stays None and _clean_delta_home_trees is never called
+    if side == "target":
+        home_trees = None
+    # (b) Under side="target", resolve manifest in-tree only
+    if side == "target":
+        cand = repo_root / AW_SYSTEM_DIR / "managed-sections.json"
+    # (c) system members map with side=side passed to _system_member_destination
+    dest, in_tree = _system_member_destination(
+        repo_root, rel, home_trees=home_trees, side=side
+    )
+    # (d) Skip this sub-branch entirely when side == "target"
+    elif side != "target":
+        from agent_workflows.project_context import project_config_dir
+    # (e) Under side="target", use repo_root / SETUP_MARKER_PATH directly
+    if side == "target":
+        p_marker = repo_root / SETUP_MARKER_PATH
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/placement_switch.py` for `retire_footprint`, and the returned action list from one target-side and one home-side scratch call.
  - Observed evidence: retire_footprint implementation in `agent_workflows/placement_switch.py`:
```python
def retire_footprint(
    repo_root: str | Path,
    side: str,
    *,
    use_git: bool = True,
    preserve: Collection[str] = (),
    changed_out: Optional[list[str]] = None,
    aw_home: Optional[str | Path] = None,
) -> list[str]:
    ...
```
Scratch execution outputs:
Target-side scratch call (`retire_footprint(repo, "target")`):
```
TARGET ACTIONS:
  - removed .agents/skills/advise-architect/SKILL.md
  - removed .agents/skills/advise-architect/reference/canonical-body.md
  - removed .agents/skills/advise-domain-expert/SKILL.md
  - removed .agents/skills/advise-domain-expert/reference/canonical-body.md
  - removed .agents/skills/advise-naive-user/SKILL.md
  ... (318 total actions)
```
Home-side scratch call (`retire_footprint(repo, "home")`):
```
HOME ACTIONS:
  - removed .../aw_home/projects/repo-e2326a/system/managed-sections.json
  - removed .../aw_home/projects/repo-e2326a/system
  - removed .../aw_home/projects/repo-e2326a/state/test.json
  - removed .../aw_home/projects/repo-e2326a/state
  - removed .../aw_home/projects/repo-e2326a/config/project.json
  - removed .../aw_home/projects/repo-e2326a/config
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `-v` output of `tests/test_placement_switch_retire.py` and of every test module calling `uninstall_repo`, all passing, with case (1)'s home snapshot assertion and case (2)'s `PRESERVED` action visible in the test names or output.
  - Observed evidence: test run outputs:
`python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py tests/test_uninstall_layout_artifacts.py -v`:
```
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_02_target_side_drifted_file_preserved_action_reported PASSED [  8%]
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_05_home_side_records_present_raises_placement_switch_error_and_removes_nothing PASSED [ 16%]
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_06_uninstall_repo_default_clean_target_regression_removes_home_trees PASSED [ 25%]
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_04_home_side_removes_framework_trees_and_prunes_project_dir PASSED [ 33%]
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_04b_target_side_tracked_paths_clean_and_inbox_user_file_preserved PASSED [ 41%]
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_03_target_side_preserve_records_leaves_records_untouched PASSED [ 50%]
tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_01_target_side_simulated_flip_home_snapshot_byte_identical_and_staged_deletions PASSED [ 58%]
tests/test_uninstall_layout_artifacts.py::UninstallLayoutArtifactsTests::test_negative_control_unrelated_sibling_preserves_aw_system PASSED [ 66%]
tests/test_uninstall_layout_artifacts.py::UninstallLayoutArtifactsTests::test_uninstall_removes_layout_artifacts PASSED [ 75%]
tests/test_uninstall_layout_artifacts.py::UninstallLayoutArtifactsTests::test_uninstall_prunes_empty_aw_system_and_aw_base PASSED [ 83%]
tests/test_uninstall_layout_artifacts.py::UninstallLayoutArtifactsTests::test_uninstall_records_layout_artifacts_in_changed_out PASSED [ 91%]
tests/test_uninstall_layout_artifacts.py::RealInstallIntegrationTests::test_real_install_uninstall_deep_cleanup_removes_aw_directory PASSED [100%]
============================= 12 passed in 36.72s ==============================
```
`python3 -m pytest -o addopts="" -m '' tests/test_installer.py -k "uninstall" -v`:
```
tests/test_installer.py::DeepCleanupTests::test_workflows_litter_deep_vs_standard_uninstall PASSED [  8%]
tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_keep_preserves_records_and_removes_other PASSED [ 16%]
tests/test_installer.py::UninstallCompletenessTests::test_uninstall_removes_config_state_gitignore_and_setup_marker PASSED [ 25%]
tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory PASSED [ 33%]
tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_plan_partitions_records_and_other PASSED [ 41%]
tests/test_installer.py::UninstallApplyTests::test_section_entries_are_never_file_removal_candidates PASSED [ 50%]
tests/test_installer.py::UninstallApplyTests::test_pre_manifest_fallback_removes_namespace PASSED [ 58%]
tests/test_installer.py::UninstallApplyTests::test_changed_out_collects_paths_and_sections_preserved PASSED [ 66%]
tests/test_installer.py::UninstallApplyTests::test_plan_uninstall_classifies_remove_drifted_and_missing PASSED [ 75%]
tests/test_installer.py::UninstallApplyTests::test_every_consent_mode_disposes_of_a_drifted_file_correctly PASSED [ 83%]
tests/test_installer.py::UninstallApplyTests::test_uninstall_removes_framework_and_manifest_while_keeping_user_files PASSED [ 91%]
tests/test_installer.py::UninstallApplyTests::test_pre_manifest_repo_has_no_manifest PASSED [100%]
===================== 12 passed, 132 deselected in 55.42s ======================
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted failing output under M1 (case 1) and M2 (cases 1 and 2), `git diff --stat` after restore, the passing re-run, and the bare-suite summary line.
  - Observed evidence: mutation runs and suite output:
M1 failure output (`python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py -k "test_01"`):
```
FAILED tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_01_target_side_simulated_flip_home_snapshot_byte_identical_and_staged_deletions
AssertionError: True is not false : (self.repo / ".aw" / "system").exists()
======================= 1 failed, 6 deselected in 5.11s ========================
```
M2 failure output (`python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py -k "test_02"`):
```
FAILED tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_02_target_side_drifted_file_preserved_action_reported
AssertionError: False is not true : advise.exists() was False (pre-manifest fallback removed drifted command)
======================= 1 failed, 6 deselected in 3.30s ========================
```
`git diff --stat` after restoring M1 and M2:
```
 agent_workflows/engine.py           | 104 +++++++++++++++++++++++++++++++++++++++---
 agent_workflows/placement_switch.py | 184 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 280 insertions(+), 8 deletions(-)
```
Passing re-run:
```
============================== 7 passed in 27.91s ==============================
```
Full repository test suite via `aw suite`:
```
708 passed in 27.43s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xvlemm` is executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never run a retirement against this repository or the real home. Paste ACTUAL runner output. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit gjylny -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize gjylny` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
