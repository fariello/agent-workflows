# IPD: Route clean-target system and records to AW_HOME and leave zero target delta

- Date: 2026-10-14
- Kind: child
- Concern: `aw install --preset completely-clean-target` and `--preset local-only` (`delivery_mode: clean-delta`, `records_backend: home`) route `config` and `state` to `AW_HOME/projects/<project_id>/` after `p425hv`, but `engine.install_into_repo` still writes and `git add`-stages 356 files into the target repository (`161` under `.aw/system/`, `41` under `.aw/records/`, and `154` host-adapter/setup files) plus unstaged target artifacts while writing zero `system` or `records` files under `AW_HOME`.
- Scope: Add pure `project_system_dir` and `project_records_dir` locators in `agent_workflows/project_context.py`, recognize home-configured clean-target repositories in `is_project_dir`, `find_project_root`, `doctor.probe_environment`, and `cli._collect_repo_status_details`, route `system` and `records` installation/readers to their resolved physical classes in `agent_workflows/engine.py` and `agent_workflows/manifest.py`, skip target-repo-only writes/staging/commits when `delivery_mode == "clean-delta"`, extend `aw uninstall` to clean up home `system` and `--deep` home `records`, restore the zero-target-delta pre-write plan line in `agent_workflows/install_wizard.py`, update `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` and `CHANGELOG.md`, and lock the behavior with subprocess tests in `tests/test_clean_target_config_home.py` and `tests/test_install_consent_truth.py`.
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/engine.py, agent_workflows/manifest.py, agent_workflows/cli.py, agent_workflows/doctor.py, agent_workflows/install_wizard.py, tests/test_clean_target_config_home.py, tests/test_install_consent_truth.py, .aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md, CHANGELOG.md
- Item-Dependencies: executed:p425hv
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleancfg
- Order: 2
- Highest E allocated: 09
- Author: antigravity
- Id: irjoga

## Workflow history
- 2026-10-14 to-review (aw set): ready for review (from backlog kvwwt0)

- 2026-10-14 draft (antigravity): created from backlog item `kvwwt0`.

## Goal

Ensure `aw install` with `--preset completely-clean-target` or `--preset local-only` (`delivery_mode: clean-delta`, `records_backend: home`) writes the `system` bundle (`workflows/`, `VERSION`, `managed-sections.json`, `layout.json`, `layout.schema.json`) and `records` scaffolding under `<aw_home>/projects/<project_id>/system` and `<aw_home>/projects/<project_id>/records` and creates zero files, directories, staged index entries, or commits in the target repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measurement and clean-target system/records locators

- [ ] E-01 Re-measure `engine.install_into_repo` (`agent_workflows/engine.py:7184`), `project_context.project_config_dir` (`agent_workflows/project_context.py:755`), `manifest.resolve_manifest_path` (`agent_workflows/manifest.py:56`), `cli._install_one` (`agent_workflows/cli.py:8023`), `doctor.probe_environment` (`agent_workflows/doctor.py:378`), and `install_wizard.render_pre_write_plan` (`agent_workflows/install_wizard.py:470`) at execution `HEAD`, and run a scratch `aw install <repo> --preset completely-clean-target -y` reproduction before editing to confirm baseline offsets and staged file counts.
  - Depends on: none
  - Expected outcome: Current line offsets, call sites, and the baseline reproduction (`356` staged files in target git and zero `system`/`records` directories in `AW_HOME/projects/<project_id>/`) are verified at execution `HEAD` and recorded in `V-01`.
  - Execution state: pending

- [ ] E-02 Add pure, side-effect-free `project_system_dir(repo_root: str | Path, aw_home: Optional[str | Path] = None) -> Path` and `project_records_dir(repo_root: str | Path, aw_home: Optional[str | Path] = None) -> Path` helpers beside `project_context.project_config_dir` (`agent_workflows/project_context.py:755`), and update `project_context.find_project_root` (`agent_workflows/project_context.py:315`), `project_context.is_project_dir` (`agent_workflows/project_context.py:502`), `doctor.probe_environment` (`agent_workflows/doctor.py:378`), and `cli._collect_repo_status_details` (`agent_workflows/cli.py:9541`) so a clean-target repository whose `project.json` resides at `<aw_home>/projects/<project_id>/config/project.json` is recognized as an `.aw`-configured project root even when `<repo>/.aw/` is absent on disk.
  - Depends on: E-01
  - Expected outcome: `project_system_dir` and `project_records_dir` return in-tree `<repo>/.aw/system` and `<repo>/.aw/records` when present or in `tracked`/`repository` mode, and return `<aw_home>/projects/<project_id>/system` and `<aw_home>/projects/<project_id>/records` (or `<companion>/records`) when configured under `clean-delta` / `home` (or `companion`); `is_project_dir`, `find_project_root`, `aw doctor`, and `aw status` recognize a zero-target-delta clean-target repo without requiring `<repo>/.aw/` to exist.
  - Execution state: pending

### Task group 2: Route system and records install/read paths to resolved physical classes

- [ ] E-03 Route `system` bundle writes, manifest lookup/save, layout artifact emission, prune candidate collection, and installed-version reads through `project_context.project_system_dir` across `manifest.resolve_manifest_path` (`agent_workflows/manifest.py:56`) and `engine.write_file` (`agent_workflows/engine.py:2218`), `engine.collect_target_framework_files` (`agent_workflows/engine.py:2538`), `engine.prune_stale` (`agent_workflows/engine.py:2591`), `engine.emit_layout_artifacts` (`agent_workflows/engine.py:6961`), `engine.read_installed_version` (`agent_workflows/engine.py:7136`), and `engine.install_into_repo` (`agent_workflows/engine.py:7184`).
  - Depends on: E-02
  - Expected outcome: When `project_system_dir(repo_root)` resolves outside `repo_root` (`<aw_home>/projects/<project_id>/system`), `.aw/system/workflows/**`, `.aw/system/VERSION`, `.aw/system/managed-sections.json`, `.aw/system/layout.json`, and `.aw/system/layout.schema.json` are written, updated, pruned, and read under `<aw_home>/projects/<project_id>/system/` without calling `git add` or `git rm` in the target repository.
  - Execution state: pending

- [ ] E-04 Route `records` scaffolding writes in `engine.ensure_plans_readmes` (`agent_workflows/engine.py:6483`), `engine.ensure_docs_readmes` (`agent_workflows/engine.py:6557`), `engine.ensure_prompts_readmes` (`agent_workflows/engine.py:6633`), `engine.create_setup_artifacts` (`agent_workflows/engine.py:6700`), and `engine.migrate_local_lanes_to_untracked` (`agent_workflows/engine.py:7098`) through `project_context.project_records_dir(repo_root)`, mapping `.aw/records/...` relative paths onto the resolved `records` root and staging in target Git only when `records_dir == repo_root / ".aw" / "records"` and the `records` git policy is `target-git`.
  - Depends on: E-02
  - Expected outcome: Under `records_backend == "home"` (and `"companion"`), all 41 records README and `.gitkeep` files plus `prompts/untracked` and `comms/untracked/*` directories are materialized under `<aw_home>/projects/<project_id>/records/` (or `<companion>/records/`) and never written or staged in `<target>/.aw/records/`.
  - Execution state: pending

### Task group 3: Suppress clean-delta target writes/staging and extend home uninstall

- [ ] E-05 Suppress target-repository file creation, git staging, and auto-commit when `delivery_mode == "clean-delta"` in `engine.install_into_repo` (`agent_workflows/engine.py:7184`), `engine.save_created_files_record` (`agent_workflows/engine.py:4214`), `engine.prune_old_backups` (`agent_workflows/engine.py:4250`), `engine.run_rollback` (`agent_workflows/engine.py:4350`), `engine.check_gitignore` (`agent_workflows/engine.py:3510`), and `cli._install_one` (`agent_workflows/cli.py:8023`): skip target-repo host adapters (`shim_members`, `skill_members`, `update_agents_pointer`), target `.gitignore` edits (`ensure_backups_gitignored`, `ensure_untracked_gitignore`), target `.aw/.gitignore`, `.aw/workflow-artifacts/README.md`, `.aw/inbox/README.md`, `.gitleaksignore`, `.github/workflows/secret-scan.yml`, target `.aw/setup-repo-needed.md`, and `prompt_and_run_commit`, and route backup/created-files records under `<aw_home>/projects/<project_id>/state/runtime/backups/`.
  - Depends on: E-03, E-04
  - Expected outcome: After `aw install <target> --preset completely-clean-target -y` or `--preset local-only -y`, `git -C <target> status --porcelain --ignored` is completely empty, no `.aw/`, `.agents/`, `.claude/`, `.opencode/`, `.github/`, `.agent-workflows-installer-backups/`, `AGENTS.md`, `.gitignore`, or `.gitleaksignore` is created or modified in `<target>`, and `git -C <target> rev-parse HEAD` is unchanged.
  - Execution state: pending

- [ ] E-06 Extend `engine.plan_uninstall` (`agent_workflows/engine.py:5152`), `engine.uninstall_repo` (`agent_workflows/engine.py:5189`), `engine.plan_deep_cleanup` (`agent_workflows/engine.py:5018`), `engine.run_deep_cleanup` (`agent_workflows/engine.py:5058`), and `cli._uninstall_dry_run_report` (`agent_workflows/cli.py:9060`) so `aw uninstall <target>` on a clean-target repository removes `<aw_home>/projects/<project_id>/system/` (including `workflows/`, `VERSION`, `managed-sections.json`, `layout.json`, `layout.schema.json`) and `<aw_home>/projects/<project_id>/state/` + `config/` while preserving `<aw_home>/projects/<project_id>/records/` by default and removing home `records/` when `--deep` (or interactive records removal) is selected.
  - Depends on: E-05
  - Expected outcome: `aw uninstall <target> --yes` removes `<aw_home>/projects/<project_id>/system/`, `config/`, and `state/` while preserving `<aw_home>/projects/<project_id>/records/`, and `aw uninstall <target> --deep --yes` removes `<aw_home>/projects/<project_id>/records/` and prunes the empty `<aw_home>/projects/<project_id>/` directory.
  - Execution state: pending

### Task group 4: Restore honest pre-write consent plan and sync spec/CHANGELOG

- [ ] E-07 Update `install_wizard.render_pre_write_plan` (`agent_workflows/install_wizard.py:461`) so `delivery_mode == DeliveryMode.CLEAN_DELTA.value` renders `"  - None in target repository (clean-delta mode writes no target host adapters)."` under `Host Adapter Exceptions:` and `"  Target Delta:     ZERO AW-owned target files created (clean-target)."` under `Expected Deltas:`, and update `tests/test_install_consent_truth.py` (`test_install_consent_truth.TestInstallConsentTruth`, `tests/test_install_consent_truth.py:21`) to assert both the restored clean-target consent line and that a live `aw install --preset completely-clean-target -y` produces zero target delta (`git status --porcelain --ignored` == `""`).
  - Depends on: E-05
  - Expected outcome: `aw install <target> --preset completely-clean-target --dry-run` prints `Target Delta:     ZERO AW-owned target files created (clean-target).` and does not reference `backlog kvwwt0`, and `tests/test_install_consent_truth.py` verifies that the dry-run claim matches the real install's zero-target-delta outcome.
  - Execution state: pending

- [ ] E-08 Update `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 4 (`"## 4. Physical Placement and Preset Mapping"`, `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md:145`) and append a workflow history note via `aw specs note 20260810-1447-01` recording that `cleancfg` Order 02 (`irjoga`) completes `system` and `records` home routing and zero-target-delta enforcement, and add a `### Fixed` entry under `"## [Unreleased]"` in `CHANGELOG.md` (`CHANGELOG.md:8`) with no em or en dashes.
  - Depends on: E-05, E-06, E-07
  - Expected outcome: Spec `20260810-1447-01` Section 4 and `## Workflow history` reflect the completed clean-target `system`/`records` routing and zero-target-delta enforcement (`aw check specs` exits `0`), and `CHANGELOG.md` documents the fix under `## [Unreleased]` with zero em or en dashes.
  - Execution state: pending

### Task group 5: End-to-end tests and mutation proof

- [ ] E-09 Expand `tests/test_clean_target_config_home.py` (`test_clean_target_config_home.TestCleanTargetConfigHome`, `tests/test_clean_target_config_home.py:29`) with unit and subprocess tests covering `project_system_dir`, `project_records_dir`, `is_project_dir`/`find_project_root` on a zero-delta clean-target repo, `aw install --preset completely-clean-target -y` and `--preset local-only -y` (asserting `git status --porcelain --ignored` is empty, `HEAD` is unchanged, `<aw_home>/projects/<id>/system/VERSION`, `managed-sections.json`, `layout.json`, `workflows/index.md`, and `<aw_home>/projects/<id>/records/plans/README.md` exist), `aw status` and `aw doctor`, and `aw uninstall` (default preserving home `records/` vs `--deep` removing home `records/`), perform a one-line mutation proof, and run `python3 -m pytest`.
  - Depends on: E-06, E-07, E-08
  - Expected outcome: `python3 -m pytest tests/test_clean_target_config_home.py tests/test_install_consent_truth.py` passes, a temporary one-line mutation in `engine.install_into_repo` fails the new clean-target zero-delta test and passes again when restored, and the full suite (`python3 -m pytest`) passes with zero regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Never work or edit directly on `main`; all implementation and test runs take place in an isolated lane worktree and commit through `aw commit <plan> -- <paths>` (see `AGENTS.md` `"USE THE TOOLED COMMIT PATH"`).
- Write no em or en dashes in user-facing prose (`CHANGELOG.md`, CLI output, wizard text); use plain hyphens, colons, or parentheses (`GEMINI.md` Rule 3).
- Run the test suite via bare `python3 -m pytest` without `-n0`, extra `-q`, or `-p no:randomly` (`GEMINI.md` Rule 5).
- Test observable outcomes and CLI/subprocess behavior, never code structure via `inspect`, `ast`, or regex over source files (`GEMINI.md` Rule 6).
- `project_context.py` must remain pure and side-effect-free (`agent_workflows/project_context.py:6`: `"Invariants: - PURE: ZERO filesystem writes, directory creation, or Git mutation."`).

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `engine.install_into_repo` (`agent_workflows/engine.py:7184`) | Running `aw install <repo> --preset completely-clean-target -y` at `HEAD` (`320d42402`) stages **356** files into `<repo>` (`161` under `.aw/system/`, `41` under `.aw/records/`, `92` under `.agents/skills/`, `28` under `.claude/commands/`, `28` under `.opencode/commands/`, plus `.aw/.gitignore`, `.aw/inbox/README.md`, `.github/workflows/secret-scan.yml`, `.gitignore`, `.gitleaksignore`, and `AGENTS.md`) and writes **6** unstaged/ignored files (`.agent-workflows-installer-backups/<ts>/.created-files.json`, `.aw/setup-repo-needed.md`, `.aw/system/layout.json`, `.aw/system/layout.schema.json`, `.aw/workflow-artifacts/README.md`, and `.gitignore`), and auto-commits all 356 staged files into `<repo>` when git identity is configured. |
| F-02 | High | `project_context.resolve_project_context` (`agent_workflows/project_context.py:1244`) | `resolve_project_context` already resolves `physical_classes["system"]` to `<aw_home>/projects/<project_id>/system` when `delivery_mode != "tracked"` (`clean-delta`) and `physical_classes["records"]` to `<aw_home>/projects/<project_id>/records` when `records_backend == "home"`, and sets `permitted_commit_destinations` to `{"product": None, "records": None}` (`agent_workflows/project_context.py:1396`), but `engine.py` and `manifest.py` ignore those resolved paths and hardcode `plan.repo_root / ...`. |
| F-03 | High | `manifest.resolve_manifest_path` (`agent_workflows/manifest.py:56`) and `engine.read_installed_version` (`agent_workflows/engine.py:7136`) | `manifest.resolve_manifest_path` hardcodes `root / ".aw/system/managed-sections.json"` and `engine.read_installed_version` only probes `repo_root / ".aw/system/VERSION"` (and legacy paths). Once `system` lives under `<aw_home>/projects/<project_id>/system`, both must consult `project_system_dir(repo_root)` so ownership hashes, `aw status`, `aw doctor`, `aw check`, and `emit_layout_artifacts` locate the home-installed `system` tree. |
| F-04 | Medium | `project_context.is_project_dir` (`agent_workflows/project_context.py:502`), `project_context.find_project_root` (`agent_workflows/project_context.py:315`), `doctor.probe_environment` (`agent_workflows/doctor.py:378`), and `cli._collect_repo_status_details` (`agent_workflows/cli.py:9541`) | All four check `(repo / ".aw").is_dir()` (or `_is_project_marker(curr / ".aw")`) to decide whether a directory is an `.aw`-configured project root. Previously, a clean-target install accidentally passed those checks only because `install_into_repo` buggily created `<repo>/.aw/system/` and `<repo>/.aw/records/`. Once `<repo>/.aw/` is no longer created in `<repo>`, all four must also check `(project_config_dir(repo) / "project.json").is_file()` so `aw status`, `aw doctor`, `aw attention`, and `aw ipd board` continue to recognize the clean-target repository. |
| F-05 | Medium | `engine.uninstall_repo` (`agent_workflows/engine.py:5296`) and `cli._uninstall_dry_run_report` (`agent_workflows/cli.py:9080`) | `p425hv` E-09 taught `uninstall_repo` and `_uninstall_dry_run_report` to remove `<aw_home>/projects/<project_id>/config/` and `state/`, but once `system/` and `records/` also live under `<aw_home>/projects/<project_id>/`, normal `aw uninstall` must remove home `system/` (and `state/`/`config/`) while preserving home `records/` by default and removing home `records/` under `aw uninstall --deep`. |
| F-06 | Medium | `install_wizard.render_pre_write_plan` (`agent_workflows/install_wizard.py:470`) and `tests/test_install_consent_truth.py` (`test_install_consent_truth.TestInstallConsentTruth`, `tests/test_install_consent_truth.py:21`) | `p425hv` E-06 replaced the false `"ZERO AW-owned target files created"` line with an interim disclosure citing `backlog kvwwt0`. Once `clean-delta` installs leave zero target delta, `render_pre_write_plan` and `tests/test_install_consent_truth.py` must restore the `"ZERO AW-owned target files created (clean-target)."` promise and verify it against a real `aw install --preset completely-clean-target -y` run. |

## Proposed changes (ordered, validatable)

1. **Task group 1 (`E-01`, `E-02`) — Pure `project_system_dir` and `project_records_dir` locators and home-configured root recognition (`agent_workflows/project_context.py`, `agent_workflows/doctor.py`, `agent_workflows/cli.py`)**:
   - In `agent_workflows/project_context.py` beside `project_context.project_config_dir` (`agent_workflows/project_context.py:755`), add:
     - `project_system_dir(repo_root: str | Path, aw_home: Optional[str | Path] = None) -> Path`:
       1. If `<repo>/.aw/system` contains `VERSION`, `managed-sections.json`, or `workflows/`, return `<repo>/.aw/system`.
       2. Else let `cfg_dir = project_config_dir(repo_root, aw_home=aw_home)`. If `(cfg_dir / "project.json").is_file()`, read `delivery_mode` and `preset` from `cfg_dir / "project.json"`; when `cfg_dir != Path(repo_root) / ".aw" / "config"` or `delivery_mode == DeliveryMode.CLEAN_DELTA.value` or `preset in (Preset.COMPLETELY_CLEAN_TARGET.value, Preset.LOCAL_ONLY.value, Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value)`, resolve `<aw_home>/projects/<project_id>/system` via `_resolve_effective_aw_home(aw_home=aw_home)` and `_derive_project_id(_canonical_path(repo_root))` and return that `Path`.
       3. Else return `<repo>/.aw/system`.
     - `project_records_dir(repo_root: str | Path, aw_home: Optional[str | Path] = None) -> Path`:
       1. If `<repo>/.aw/records` is an existing directory, return `<repo>/.aw/records`.
       2. Else if `(project_config_dir(repo_root, aw_home=aw_home) / "project.json").is_file()`, resolve `ctx = resolve_project_context(target_repo=str(repo_root), aw_home=str(aw_home) if aw_home else None)` and return `Path(ctx.physical_classes[RootClass.RECORDS.value])`.
       3. Else return `<repo>/.aw/records`.
   - In `project_context.find_project_root` (`agent_workflows/project_context.py:315`) and `project_context.is_project_dir` (`agent_workflows/project_context.py:502`), also return `True` when `(project_config_dir(curr) / "project.json").is_file()` (which matches only the exact canonical repository root whose derived `project_id` has a `config/project.json` in `AW_HOME`, never arbitrary subdirectories or unrelated parent directories).
   - In `doctor.probe_environment` (`agent_workflows/doctor.py:378`) and `cli._collect_repo_status_details` (`agent_workflows/cli.py:9541`), treat `has_aw` as `(repo / ".aw").is_dir() or (project_config_dir(repo) / "project.json").is_file()` so `aw doctor` and `aw status` report `.aw` layout, `preset`, and `records_backend` on a zero-target-delta clean-target repository.

2. **Task group 2 (`E-03`, `E-04`) — Route `system` and `records` installation and readers to `project_system_dir` and `project_records_dir` (`agent_workflows/manifest.py`, `agent_workflows/engine.py`)**:
   - In `manifest.resolve_manifest_path` (`agent_workflows/manifest.py:56`), if `root / DEFAULT_MANIFEST_RELPATH` exists return it; else if `root / LEGACY_MANIFEST_RELPATH` exists return it; else return `project_system_dir(root) / "managed-sections.json"`.
   - In `agent_workflows/engine.py`, add a helper `_resolve_system_member_path(repo_root: Path, relative_posix: str) -> tuple[Path, bool]` that maps any `.aw/system` or `.aw/system/<subpath>` member onto `sys_dir = project_system_dir(repo_root)` and returns `(dest_path, sys_dir == repo_root / ".aw" / "system")`.
   - Update `engine.write_file` (`agent_workflows/engine.py:2218`), `engine.collect_target_framework_files` (`agent_workflows/engine.py:2538`), `engine.prune_stale` (`agent_workflows/engine.py:2591`), `engine.emit_layout_artifacts` (`agent_workflows/engine.py:6961`), `engine.read_installed_version` (`agent_workflows/engine.py:7136`), and the manifest save block in `engine.install_into_repo` (`agent_workflows/engine.py:7344`) to resolve `.aw/system/...` files via `project_system_dir(repo_root)` and stage in target Git only when `sys_dir == repo_root / ".aw" / "system"`.
   - In `engine.ensure_plans_readmes` (`agent_workflows/engine.py:6483`), `engine.ensure_docs_readmes` (`agent_workflows/engine.py:6557`), `engine.ensure_prompts_readmes` (`agent_workflows/engine.py:6633`), `engine.create_setup_artifacts` (`agent_workflows/engine.py:6700`), and `engine.migrate_local_lanes_to_untracked` (`agent_workflows/engine.py:7098`), map `.aw/records/<subpath>` onto `records_dir = project_records_dir(repo_root)` and pass `use_git = use_git and (records_dir == repo_root / ".aw" / "records") and (git_policy_records == "target-git")`.

3. **Task group 3 (`E-05`, `E-06`) — Zero target delta under `clean-delta` and home-aware `aw uninstall` (`agent_workflows/engine.py`, `agent_workflows/cli.py`)**:
   - In `engine.install_into_repo` (`agent_workflows/engine.py:7184`), check whether the resolved policy for `repo_root` has `delivery_mode == DeliveryMode.CLEAN_DELTA.value` (via `project_context.resolve_project_context(target_repo=str(repo_root))` when `(project_config_dir(repo_root) / "project.json").is_file()`). When `is_clean_delta` is `True`:
     - Pass `generated_members = {}` to `install_all` and `prune_stale` so no target host adapters (`.agents/skills/**`, `.claude/commands/**`, `.opencode/commands/**`) are written into `repo_root`.
     - Skip `update_agents_pointer`, `ensure_backups_gitignored`, `ensure_untracked_gitignore`, `ensure_workflow_artifacts_readme`, `ensure_inbox_readme`, and `_ensure_aw_gitignore` in `repo_root`, and in `create_setup_artifacts` skip target-only files (`AW_GITIGNORE_PATH`, `GITLEAKSIGNORE_FILE`, `SECRET_SCAN_CI`) while still scaffolding `records` under `project_records_dir(repo_root)`.
     - Route backup storage (`create_backup_path`, `allocate_backup_timestamp`, `save_created_files_record`, `prune_old_backups`, `run_rollback`) to `<aw_home>/projects/<project_id>/state/runtime/backups` when `is_clean_delta` is `True`.
     - In `cli._install_one` (`agent_workflows/cli.py:8129`), skip `engine.write_setup_marker(repo_root)` and `engine.prompt_and_run_commit(...)` when `is_clean_delta` is `True` (or make `write_setup_marker` write under `<aw_home>/projects/<project_id>/state/runtime/setup-repo-needed.md` and `prompt_and_run_commit` return immediately when `delivery_mode == "clean-delta"`).
   - In `engine.plan_uninstall` (`agent_workflows/engine.py:5152`), `engine.uninstall_repo` (`agent_workflows/engine.py:5189`), `engine.plan_deep_cleanup` (`agent_workflows/engine.py:5018`), `engine.run_deep_cleanup` (`agent_workflows/engine.py:5058`), and `cli._uninstall_dry_run_report` (`agent_workflows/cli.py:9060`), resolve `.aw/system/...` manifest entries against `project_system_dir(repo_root)`, remove `<aw_home>/projects/<project_id>/system/` (including `layout.json`, `layout.schema.json`, `managed-sections.json`, and empty directories) during normal `aw uninstall`, preserve `<aw_home>/projects/<project_id>/records/` on normal uninstall, and include `<aw_home>/projects/<project_id>/records/` in `plan_deep_cleanup` / `run_deep_cleanup` so `aw uninstall --deep` removes home `records/` and prunes `<aw_home>/projects/<project_id>/` when empty.

4. **Task group 4 (`E-07`, `E-08`) — Pre-write consent truth, spec note, and CHANGELOG (`agent_workflows/install_wizard.py`, `tests/test_install_consent_truth.py`, `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`, `CHANGELOG.md`)**:
   - Update `install_wizard.render_pre_write_plan` (`agent_workflows/install_wizard.py:461`) so `clean-delta` policies display `"  - None in target repository (clean-delta mode writes no target host adapters)."` under `Host Adapter Exceptions:` and `"  Target Delta:     ZERO AW-owned target files created (clean-target)."` under `Expected Deltas:`.
   - Update `tests/test_install_consent_truth.py` (`test_install_consent_truth.TestInstallConsentTruth`, `tests/test_install_consent_truth.py:21`) to assert the restored zero-target-delta consent line and assert via a live `aw install --preset completely-clean-target -y` subprocess that `git -C <target> status --porcelain --ignored` is empty.
   - Amend `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 4 (`"## 4. Physical Placement and Preset Mapping"`, `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md:145`), append a workflow history note via `aw specs note 20260810-1447-01`, and add a `### Fixed` bullet under `"## [Unreleased]"` in `CHANGELOG.md` (`CHANGELOG.md:8`).

5. **Task group 5 (`E-09`) — End-to-end tests and mutation proof (`tests/test_clean_target_config_home.py`)**:
   - Expand `tests/test_clean_target_config_home.py` (`test_clean_target_config_home.TestCleanTargetConfigHome`, `tests/test_clean_target_config_home.py:29`) with unit and subprocess tests for `project_system_dir`, `project_records_dir`, `is_project_dir`, `find_project_root`, `aw install --preset completely-clean-target -y`, `aw install --preset local-only -y`, `aw status`, `aw doctor`, `aw uninstall`, and `aw uninstall --deep`, perform the one-line mutation proof, and run `python3 -m pytest`.

## Deferred / out of scope (with reason)

- Global user-scope host adapter and skill delivery (`~/.config/opencode/`, `~/.claude/`, `~/.gemini/antigravity/skills/`) for `clean-delta` installs: this plan stops `aw install` from writing or staging host adapters (`AGENTS.md`, `.agents/skills/`, `.claude/commands/`, `.opencode/commands/`) into the target repository when `delivery_mode == "clean-delta"`, while delivering user-scoped host skills into global host directories remains a separate feature specified in deferred spec `or061f` (`.aw/records/specs/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md`).
  - Carrier-Declined: Global user-scope host skill installation is already specified in deferred spec `or061f` (gated on `m15n3k`) and is an independent feature from fixing `aw install` to honor the `clean-delta` zero-target-delta invariant required by `kvwwt0`.

## Scope check

- Over-scope: none. Every E-item directly serves backlog `kvwwt0` (routing `system` and `records` to `AW_HOME` under `clean-delta` / `home`, eliminating target-repo writes and git staging on clean-target installs, extending `aw uninstall` to the home `system`/`records` trees, and restoring the honest pre-write consent text).
- Under-scope: none. Every write site reached by `aw install <repo> --preset completely-clean-target` and `--preset local-only` (`engine.install_into_repo`, `manifest.resolve_manifest_path`, `cli._install_one`, `engine.uninstall_repo`, `install_wizard.render_pre_write_plan`) and the readers that inspect the resulting install (`read_installed_version`, `is_project_dir`, `find_project_root`, `doctor.probe_environment`, `cli._collect_repo_status_details`) are covered.

## Required tests / validation

- Subprocess integration test in `tests/test_clean_target_config_home.py`: run `aw install <target> --preset completely-clean-target -y` and `--preset local-only -y` with an isolated `AW_HOME` and configured git user identity; assert exit `0`, `git -C <target> status --porcelain --ignored` == `""`, `git -C <target> rev-parse HEAD` unchanged from before install, `<target>/.aw` does not exist, `<aw_home>/projects/<id>/system/VERSION`, `<aw_home>/projects/<id>/system/managed-sections.json`, `<aw_home>/projects/<id>/system/layout.json`, `<aw_home>/projects/<id>/system/workflows/index.md`, and `<aw_home>/projects/<id>/records/plans/README.md` exist.
- Subprocess verification of `aw status --json`, `aw doctor <target> --json`, and `is_project_dir` / `find_project_root` on the clean-target repository confirming `preset == "completely-clean-target"`, `records_backend == "home"`, and `version_status == "current"` even with no `<target>/.aw/` directory on disk.
- Subprocess verification of `aw uninstall <target> --dry-run`, `aw uninstall <target> --yes` (removes home `system/`, `config/`, `state/` while preserving home `records/`), and `aw uninstall <target> --deep --yes` (removes home `records/` and prunes `<aw_home>/projects/<id>/`).
- Subprocess and unit verification in `tests/test_install_consent_truth.py` that `render_pre_write_plan` for `clean-delta` prints `Target Delta:     ZERO AW-owned target files created (clean-target).` and matches the real install's zero target delta.
- Mutation proof: temporarily revert the `is_clean_delta` guard or `project_system_dir` routing in `agent_workflows/engine.py`, run `python3 -m pytest tests/test_clean_target_config_home.py` to observe failure, restore the fix, and re-run `python3 -m pytest`.

## Spec / documentation sync

- Amend `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 4 (`"## 4. Physical Placement and Preset Mapping"`, `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md:145`) to record that `cleancfg` Order 02 (`irjoga`) completes `system` and `records` home routing and zero-target-delta enforcement for `completely-clean-target` and `local-only`, and append a history entry via `aw specs note 20260810-1447-01`.
- Add a `### Fixed` entry under `"## [Unreleased]"` in `CHANGELOG.md` (`CHANGELOG.md:8`) describing the fix with zero em or en dashes.

## Open questions

### OQ-01: How should host adapters (`AGENTS.md`, `.agents/skills/`, `.claude/commands/`, `.opencode/commands/`) and target setup files (`.gitignore`, `.aw/.gitignore`, `.gitleaksignore`, `.github/workflows/secret-scan.yml`) be handled when `delivery_mode == "clean-delta"`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence in `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 4/5 (`"A clean-target policy can therefore leave no target .aw/ while still using the canonical physical shape outside the target"`, `"A custom policy MUST NOT ... claim clean-target while creating any AW-owned target baseline delta"`), `project_context.resolve_project_context` (`agent_workflows/project_context.py:1396`, `product_dest = repo_abs if resolved_delivery_mode == DeliveryMode.TRACKED.value else None`), and `kvwwt0`'s requirement (`"Expected: the target working tree and index are untouched (`git status --short` empty)"`). Under `delivery_mode == "clean-delta"`, `engine.install_into_repo` must not write or stage host adapters or target setup files into the target repository, leaving the target working tree, index, and `HEAD` completely untouched (`E-05`, `E-07`).

### OQ-02: How should repo-scoped verbs and status/doctor probes recognize a clean-target repository once `<target>/.aw/` is no longer created on disk?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence in `project_context.project_config_dir` (`agent_workflows/project_context.py:755`), `project_context.is_project_dir` (`agent_workflows/project_context.py:502`), `project_context.find_project_root` (`agent_workflows/project_context.py:315`), `doctor.probe_environment` (`agent_workflows/doctor.py:378`), and `cli._collect_repo_status_details` (`agent_workflows/cli.py:9541`). Because `project_config_dir(p)` derives `project_id` from `_canonical_path(p)` and checks `<aw_home>/projects/<project_id>/config/project.json`, checking `(project_config_dir(p) / "project.json").is_file()` is `True` if and only if `p` is the exact canonical repository root configured under `AW_HOME`. Adding this check to `is_project_dir`, `find_project_root`, `doctor.probe_environment`, and `cli._collect_repo_status_details` preserves project-root discovery and `aw status` / `aw doctor` reporting without creating any file in `<target>` (`E-02`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted command output from the pre-edit re-measurement at execution `HEAD` showing the line offsets of `engine.install_into_repo`, `project_context.project_config_dir`, `manifest.resolve_manifest_path`, `cli._install_one`, `doctor.probe_environment`, and `install_wizard.render_pre_write_plan` and the baseline `git status --short` staged count on a scratch `completely-clean-target` install.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/project_context.py agent_workflows/doctor.py agent_workflows/cli.py` and pasted Python one-liner output demonstrating `project_system_dir`, `project_records_dir`, `is_project_dir`, and `find_project_root` for both a tracked repository and a home-configured clean-target repository with no `<repo>/.aw/` directory.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/manifest.py agent_workflows/engine.py` and pasted output from a probe showing `manifest.resolve_manifest_path(repo)`, `engine.emit_layout_artifacts(repo)`, and `engine.read_installed_version(repo)` resolving under `<aw_home>/projects/<project_id>/system/` when `delivery_mode == "clean-delta"`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff -- agent_workflows/engine.py` for the records scaffolding ensurers (`ensure_plans_readmes`, `ensure_docs_readmes`, `ensure_prompts_readmes`, `create_setup_artifacts`, `migrate_local_lanes_to_untracked`) and pasted probe output confirming all 41 records README and `.gitkeep` files plus `untracked` lanes are created under `<aw_home>/projects/<project_id>/records/` and absent from `<target>/.aw/records/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted subprocess output (reachable via `cli._run_install` -> `cli._install_one` -> `engine.install_into_repo` updated in `E-03`..`E-05`) from running `aw install <target> --preset completely-clean-target -y` and `aw install <target2> --preset local-only -y` showing exit `0`, empty `git -C <target> status --porcelain --ignored`, unchanged `git -C <target> rev-parse HEAD`, and populated `<aw_home>/projects/<project_id>/system/` and `records/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted subprocess output (reachable via `cli._run_uninstall` -> `engine.uninstall_repo` / `engine.run_deep_cleanup` updated in `E-06`) from running `aw uninstall <target> --dry-run`, `aw uninstall <target> --yes` (showing `<aw_home>/projects/<id>/system/`, `config/`, and `state/` removed while `records/` is preserved), and `aw uninstall <target> --deep --yes` (showing `records/` and `<aw_home>/projects/<id>/` removed).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted `git diff -- agent_workflows/install_wizard.py tests/test_install_consent_truth.py` and pasted output of `python3 -m pytest tests/test_install_consent_truth.py` showing all tests passing and `Target Delta:     ZERO AW-owned target files created (clean-target).` verified against a real install.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Pasted `git diff -- .aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md CHANGELOG.md`, pasted output of `AW_NO_REEXEC=1 python3 -m agent_workflows.cli check specs`, and pasted output of a check confirming zero em or en dashes in the new `CHANGELOG.md` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: Pasted output of `python3 -m pytest tests/test_clean_target_config_home.py` failing under the one-line mutation and passing after restoration, followed by pasted output of the full test suite (`python3 -m pytest`) and `AW_NO_REEXEC=1 python3 -m agent_workflows.cli sanitize --agent` exiting `0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ready for review (`- Status: to-review`). Do not execute until `- Status: approved`. Upon execution completion and verification of `V-01`..`V-09`, finalize the plan via `aw ipd finalize irjoga` and commit all modified paths through `aw commit irjoga -- <paths>`.
