# IPD: Write clean-target project config and install state under AW_HOME where the resolver places them

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `mbx0o4`. A `completely-clean-target` install (`delivery_mode: clean-delta`) writes `.aw/config/project.json` and `.aw/config/local.json` INTO the target, because `install_wizard.persist_project_policy` hard-codes `p_repo / ".aw" / "config"` and `config.sync_cutovers_on_install` hard-codes `root / ".aw" / "config" / "project.json"`, while `project_context.resolve_project_context` resolves `config_project`/`config_local` to `<aw_home>/projects/<project-id>/config/` for every non-`tracked` delivery mode and `install_wizard.render_pre_write_plan` prints those home paths plus "Target Delta: ZERO AW-owned target files created (clean-target)." The same install writes `state/durable/install.json` and `history/installs.jsonl` to `<aw_home>/projects/state/durable/` with NO project-id segment, because the resolver, once a target `local.json` exists, takes `project_id` from it and the wizard wrote `"project_id": ""` (`LocalBindingSchema` default), and `dict.get("project_id", fallback)` returns the empty string rather than the fallback. Because every reader (`resolve_project_context` Levels 2/3, `install_wizard.resolve_existing_policy`, `install_history.record_install_history`, the `config.py` policy readers) looks only at `<target>/.aw/config/`, moving the write alone would make a clean-target repo unconfigured on the next command; readers must find the home copy.
- Scope: IN: (1) one shared locator, `project_context.project_config_dir(repo_root)`, returning `<target>/.aw/config` when that directory holds `project.json` or `local.json` (existing tracked and legacy installs keep working byte-for-byte) and otherwise `<aw_home>/projects/<derived-project-id>/config` when such a home `project.json` exists, else the target path; (2) `persist_project_policy` writes to the resolver's `config_project`/`config_local` paths for the policy being persisted (home for `clean-delta`, target for `tracked`), and writes a non-empty `project_id` into `local.json`; (3) `config.sync_cutovers_on_install` and the `config.py` `project.json` readers, `run_analytics_config.read_project_settings`/`read_local_settings`, `run_analytics_wizard._local_path`, `install_wizard.resolve_existing_policy`, `install_history.record_install_history` and `cli` install's D92 normalization read through the locator; (4) `resolve_project_context` reads Level 2/3 files through the locator and treats an empty `project_id` as absent; (5) `engine.stage_tracked_policy_files` stays a no-op for clean-delta (no target file exists to stage; verified, not changed); (6) the consent plan's "Target Delta" line for clean-delta stops claiming zero target files and names the classes that ARE kept out of the target (config and state), pointing at backlog `kvwwt0` for the rest; (7) spec `20260810-1447-01` Section 4 gets a dated note that clean-delta config/state resolve under `AW_HOME`, and that the full zero-target-write install remains spec `or061f` Phase 3; (8) behavior tests; (9) `project_context.read_project_identity` (backs `aw doctor`/`aw status`) reads through the locator; (10) `aw uninstall` removes the config and state files the install wrote under `AW_HOME/projects/<id>/` (E-09). Both clean-delta presets (`completely-clean-target`, `local-only`) are covered. OUT: `.aw/system/`, `.aw/records/`, `.aw/.gitignore`, `.aw/inbox`, `.aw/workflow-artifacts`, root `.gitignore`/`.gitleaksignore`, `.github/workflows` and host adapters still written into a clean-target target (backlog `kvwwt0`, spec `or061f` Phase 3); reinstall discarding unmodeled `project.json` keys and restamping cutovers (backlog `qyevpr`); a registry entry for the project (`project_registry.register_or_update_project` is not called by install today and is not needed for derivation); migrating an existing clean-target install that already wrote into its target (it keeps working through locator rule 1).
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/install_wizard.py, agent_workflows/config.py, agent_workflows/install_history.py, agent_workflows/run_analytics_config.py, agent_workflows/run_analytics_wizard.py, agent_workflows/cli.py, agent_workflows/engine.py, agent_workflows/doctor.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md, CHANGELOG.md, tests/test_clean_target_config_home.py, tests/test_install_consent_truth.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: mbx0o4
- Blocks-Release: next
- Set: cleancfg
- Order: 1
- Highest E allocated: 09
- Author: opencode/claude-opus-5.5
- Id: p425hv

## Workflow history
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Record: .aw/records/reviews/20261012-cleancfg-01-p425hv-write-clean-target-project-config-and-install-state-under-aw.review.md Round 1

- 2026-10-12 draft (opencode/claude-opus-5.5): created.
- 2026-10-12 to-review (opencode/claude-opus-5.5): authored from backlog `mbx0o4` after reproducing F-01..F-06 in scratch targets at HEAD `ffce69f34`; filed out-of-scope findings as backlog `kvwwt0` and `qyevpr`.

## Goal

A clean-target install keeps its project policy, machine binding and install history out of the target repository, at exactly the `AW_HOME` paths the consent plan shows, and every later `aw` command still finds that policy; the consent plan stops promising a zero target delta that the installer does not deliver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD with `AW_NO_REEXEC=1` and `HOME`, `XDG_CONFIG_HOME` and `AW_HOME` pointed into a temp dir: in a fresh temp git repo run `aw install . --preset completely-clean-target -y --no-interactive --dry-run` (record the `config_project`, `config_local`, `state_durable` lines and the "Target Delta" line), then the same without `--dry-run`, then `ls -a .aw .aw/config`, and repeat the dry-run and install for `--preset local-only` in a second temp repo (also `delivery_mode: clean-delta`, F-09), `git status --short --ignored -- .aw/config .aw/state`, `find "$AW_HOME" -type f`, `cat .aw/config/local.json`, and `python3 -c` printing `resolve_project_context(target_repo='.').project_id` and `.physical_classes`. Record the HEAD sha. If target `.aw/config/` is absent and the home paths match the dry-run, record that and stop.
  - Depends on: none
  - Expected outcome: F-01..F-04 reproduce: target holds `.aw/config/project.json` (`?? .aw/config/`) and `local.json` (ignored) with `"project_id": ""`; `AW_HOME` holds only `projects/state/durable/install.json` and `projects/state/durable/history/installs.jsonl`; the resolver prints `project_id ''` and paths under `<aw_home>/projects/` with no id segment.
  - Execution state: pending

### Task group 2: one locator

- [ ] E-02 In `agent_workflows/project_context.py` add `project_config_dir(repo_root, aw_home=None) -> Path` and make `resolve_project_context` use it. Rules, in order: (1) if `<repo>/.aw/config/project.json` or `<repo>/.aw/config/local.json` (or legacy `config.json`/`policy.json`) exists, return `<repo>/.aw/config`; (2) else compute `aw_home` exactly as `resolve_project_context` does (explicit, `AW_HOME`, user config `aw_home`, `get_default_aw_home()`; factor that block into a private helper both call) and, if `<aw_home>/projects/<_derive_project_id(repo_abs)>/config/project.json` exists, return that directory; (3) else return `<repo>/.aw/config`. Pure and side-effect free (spec 20260810-1447-01 Section 7). In `resolve_project_context`, read `local_binding_file`, `project_policy_file`, `legacy_config_file` and `legacy_policy_file` from `project_config_dir(...)`, and resolve `project_id` so that an empty or non-string value at either level is treated as absent (falls through to `_derive_project_id(repo_abs)`). Rule 1 before rule 2 is what makes existing tracked installs and already-polluted clean-target installs resolve exactly as today.
  - Depends on: E-01
  - Expected outcome: with a target `local.json` carrying `"project_id": ""` the resolver returns the derived `<slug>-<hash6>` id and per-project home paths; with no target config and a home `project.json` it reads that file (preset/delivery mode come from it, `is_configured` is True); with neither it behaves as today.
  - Execution state: pending

### Task group 3: write where the resolver says

- [ ] E-03 Change `install_wizard.persist_project_policy` to call `resolve_project_context(target_repo=repo_path, aw_home=policy.aw_home, delivery_mode=policy.delivery_mode, records_backend=policy.records_backend, preset=policy.preset, role=policy.role, companion_dir=policy.companion_dir)` and write `project.json` and `local.json` to `physical_classes["config_project"]` and `["config_local"]` (parent `mkdir`, same tmp-then-`os.replace` pattern, tmp file in the destination directory). Write `LocalBindingSchema.project_id = ctx.project_id` (never empty). Return `written_paths` as the actual written paths, repo-relative when under the target and absolute otherwise, and keep `WIZARD_WRITTEN_PATHS` as the target-relative constants `engine.stage_tracked_policy_files` iterates. Then call `config.sync_cutovers_on_install(repo_path, aw_home=policy.aw_home)` (E-04 signature). Under `dry_run` behavior is unchanged.
  - Depends on: E-02
  - Expected outcome: a clean-target install creates no `<target>/.aw/config/`; `project.json` and `local.json` exist under `<aw_home>/projects/<id>/config/`; a private-target install writes the target paths byte-identically to today (same keys, same order).
  - Execution state: pending

- [ ] E-04 Route the remaining hard-coded readers and writers of `.aw/config/project.json` / `local.json` through `project_context.project_config_dir`: `project_context.read_project_identity` (its canonical and legacy `.aw/config/` candidates; it backs `aw doctor`, `aw status` and `artifact_core._is_repository_untracked_backend`, F-10), `config.resolve_cutover_date`, `config.sync_cutovers_on_install` (accept optional `aw_home`), `config.read_dependency_schema_cutover`, `config.read_review_findings_gate`, `config.release_gate_work_kinds`, `config.read_run_policy`, `config.policy_retry_budget`, `config.policy_on_conflict`, `config.policy_isolation`, `config.read_setid_policy_object`; `run_analytics_config.read_project_settings` and `read_local_settings`; `run_analytics_wizard._local_path`; `install_wizard.resolve_existing_policy` (existence probe and context); `install_history.record_install_history` (`project_file`); and the D92 normalization probe in `cli`'s install loop ("Check for state_durable policy upgrade normalization"). Import `project_context` lazily inside `config.py` functions (it already imports `config` lazily in `_is_repos_schema_mapping`). Re-grep `".aw" / "config"`, `".aw", "config"` and `PROJECT_POLICY_REL`/`LOCAL_BINDING_REL` across `agent_workflows/` at execution and route any new reader added since; leave `engine.stage_tracked_policy_files` target-relative (it stages target files only, and a clean-delta install has none) and `doctor`'s legacy-path map untouched.
  - Depends on: E-03
  - Expected outcome: in a clean-target target with config only under `AW_HOME`, `aw install` a second time sees an existing policy (no first-install behavior), cutovers stamped at the first install are read by `resolve_cutover_date`, and a `run` key set in the home `project.json` is read by `read_run_policy`; `aw doctor` and `aw status` report the stored preset (not `None`); for a tracked target every function returns what it returns today.
  - Execution state: pending

- [ ] E-05 Install history lands under the project. Confirm, by re-running E-01, that after E-02/E-03 `install_history.record_install_history` resolves `state_durable` to `<aw_home>/projects/<id>/state/durable/` (no code change expected beyond E-04's `project_file`); if it still writes `<aw_home>/projects/state/`, fix the resolver path, not the writer. `config._find_install_history_cutover` keeps reading target paths first and additionally reads the resolved `state_durable` history when the target has none.
  - Depends on: E-04
  - Expected outcome: `find "$AW_HOME" -type f` lists `projects/<slug>-<hash6>/config/project.json`, `.../config/local.json`, `.../state/durable/install.json`, `.../state/durable/history/installs.jsonl` and nothing at `projects/state/`; `install.json` carries the non-empty `project_id`.
  - Execution state: pending

- [ ] E-09 Keep uninstall at parity. Today `engine.uninstall_repo` removes every file under `<target>/.aw/config` and `<target>/.aw/state` ("Deterministic framework-created lifecycle files (config, state, .aw/.gitignore)"). After E-03 a clean-delta install's config and state live under `AW_HOME`, so without this item an uninstall would leave them behind and locator rule 2 would make the NEXT install of the same path silently adopt the stale policy (F-11). In `engine.uninstall_repo`, when the target has no `.aw/config` and `project_context.project_config_dir(repo_root)` resolves to a home directory, remove exactly the files this plan writes there: `project.json`, `local.json` under that config dir, and every file under the sibling `state/` of `<aw_home>/projects/<id>/`. Never remove anything outside `<aw_home>/projects/<id>/`, never the `projects/` or `AW_HOME` directories themselves, and report each removed path in the returned actions (absolute paths). Under `--dry-run` (`cli`'s uninstall preview) list them without removing anything. Include the home config dir in `cli._run_uninstall`'s `has_footprint` probe so a target whose only AW footprint is home config is not reported as not installed.
  - Depends on: E-05
  - Expected outcome: after a clean-target install then `aw uninstall . -y`, nothing remains under `AW_HOME/projects/<id>/config` or `AW_HOME/projects/<id>/state`, the actions list names those paths, and a following clean-target install behaves as a first install; a tracked target's uninstall is unchanged.
  - Execution state: pending

### Task group 4: tell the truth in the consent plan

- [ ] E-06 In `install_wizard.render_pre_write_plan`, replace the clean-delta "Target Delta" text with a line that does not claim zero target files: state that project config, local config and install state are written only under the AW_HOME paths listed above, and that workflow files, records scaffolding and host adapters are still written into the target (tracked by backlog `kvwwt0`). No em or en dashes (user-facing). Update `tests/test_install_consent_truth.py` only where it asserts the old wording, by asserting the new behavior (the printed config/state paths equal the paths the install then writes).
  - Depends on: E-09
  - Expected outcome: the dry-run for `completely-clean-target` and for `local-only` no longer prints "ZERO AW-owned target files"; every path it prints for `config_project`, `config_local` and `state_durable` exists after the real install, and no `<target>/.aw/config` or `<target>/.aw/state` exists.
  - Execution state: pending

### Task group 5: spec, changelog, tests

- [ ] E-07 Amend implemented spec `20260810-1447-01`: add a dated `AMENDED 2026-10-12 (cleancfg p425hv)` paragraph after the Section 4 container paragraph ("`<container>` may be the target repository, ...") stating that for `clean-delta` the installer writes `config/project.json`, `config/local.json` and `state/durable/` under `AW_HOME/projects/<project-id>/`, that readers locate config target-first then home (the `project_config_dir` rule), that an empty `project_id` is treated as absent, and that the remaining target writes are the open `or061f` Phase 3 work (backlog `kvwwt0`). Record it with `aw specs note <spec> --message "..."` citing this plan and backlog `mbx0o4`. Add a CHANGELOG entry under the pending 2.0.0 section (user-facing, no em or en dashes).
  - Depends on: E-06
  - Expected outcome: the spec text matches shipped behavior; its workflow history carries the note; `aw specs check` reports no new finding.
  - Execution state: pending

- [ ] E-08 Add `tests/test_clean_target_config_home.py`, driving the real CLI by subprocess (pattern of `tests/test_install_state_records.py` `setUp`: temp git repo, `HOME`, `XDG_CONFIG_HOME` and `AW_HOME` in the temp dir, `AW_NO_REEXEC=1`, `PYTHONPATH` at the checkout) and asserting on files, contents, exit codes and `git status`: (a) clean-target install leaves no `<target>/.aw/config` and no `<target>/.aw/state`, and `git status --porcelain --ignored -- .aw/config .aw/state` is empty; (b) `project.json`, `local.json`, `install.json`, `history/installs.jsonl` exist under `AW_HOME/projects/<id>/` where `<id>` equals `resolve_project_context(...).project_id`, is non-empty, and equals the id in the dry-run's printed paths; nothing exists at `AW_HOME/projects/state`; (c) a second clean-target install exits 0, keeps the stored preset, and appends a second history line in the same home file; (d) `config.resolve_cutover_date(repo, "spec_id6")` returns the date stamped in the home `project.json`; (e) a private-target install still writes `<target>/.aw/config/project.json` (staged) and `local.json` (ignored) and nothing under `AW_HOME/projects/*/config`; (f) a target pre-seeded with the OLD polluted layout (target `local.json` with `"project_id": ""` and a target `project.json`) resolves a non-empty project id and keeps reading the target config; (g) cases (a) and (b) repeated for `--preset local-only`; (h) after a clean-target install, `aw doctor` reports the stored preset; (i) after a clean-target install, `aw uninstall . -y` removes the home config and state files and a following install exits 0 as a first install (E-09); (j) a public-target-private-companion install is unchanged (its `config_project` stays under the target, its `delivery_mode` is `tracked`). Prove (a) can fail by reverting E-03's destination to the target path and pasting the failure, then restore.
  - Depends on: E-07
  - Expected outcome: all ten cases pass; the mutation fails case (a); existing install, consent, state-record, project-context and config tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `project_context.resolve_project_context` is the single resolver of physical class paths and must stay pure (spec `20260810-1447-01` Section 7: "The resolver MUST be pure and side-effect free"); the new locator lives beside it and is equally pure.
- For any non-`tracked` delivery mode the resolver places `system`, `config` and `state` under `os.path.join(aw_home_abs, "projects", project_id)`; `_derive_project_id` is deterministic (`<slug>-<sha256(repo_abs)[:6]>`), so a home config can be located from the repo path alone with no registry.
- `install_history.record_install_history` already writes wherever the resolver puts `state_durable` (it is why install history landed in `AW_HOME` at all); only the empty `project_id` mis-routes it.
- `engine.stage_tracked_policy_files` iterates `WIZARD_WRITTEN_PATHS` (target-relative) and stages only `target-git` classes; for clean-delta every class is `untracked`, so it stages nothing either way.
- `config.py` functions already import sibling modules lazily (`from agent_workflows import config as _config` in `install_wizard`; `_is_repos_schema_mapping` imports `config` from `project_context`), so a lazy `project_context` import in `config.py` avoids a cycle.
- Subprocess tests isolate `HOME`/`XDG_CONFIG_HOME` and set `AW_NO_REEXEC=1` (`tests/test_install_state_records.py` `setUp`); tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `ffce69f34` with `AW_NO_REEXEC=1`, `HOME` and `AW_HOME` in `/tmp`.

| # | Finding | Evidence |
|---|---|---|
| F-01 | Clean-target install writes config into the target. | `aw install <repo> --preset completely-clean-target -y --no-interactive`: `ls .aw/config` -> `local.json project.json`; `git status --short --ignored -- .aw/config .aw/state` -> `?? .aw/config/`, `!! .aw/config/local.json`; `project.json` carries `"delivery_mode": "clean-delta"`, all placements `home-untracked` |
| F-02 | The dry-run consent plan promises the home paths and zero target files. | `--dry-run` prints `config_project : <aw_home>/projects/r2-cc30f4/config/project.json [home] (untracked)` and `Target Delta:     ZERO AW-owned target files created (clean-target).` |
| F-03 | Install state lands at `AW_HOME/projects/state/` with no project segment. | `find $AW_HOME` -> `projects/state/durable/install.json`, `projects/state/durable/history/installs.jsonl`; `install.json` has `"project_id": ""` |
| F-04 | The empty id comes from the wizard's `local.json`. | target `local.json`: `"project_id": ""` (`LocalBindingSchema` default `project_id: str = ""`); `resolve_project_context` uses `merged_local_binding.get("project_id", ...)`, which returns `""`; after install `resolve_project_context(target_repo=repo).project_id` -> `''` and `physical_classes['config_project']` -> `<aw_home>/projects/config/project.json` |
| F-05 | Every reader looks only in the target. | `resolve_project_context`: `local_binding_file = os.path.join(repo_abs, ".aw", "config", "local.json")`, `project_policy_file = os.path.join(repo_abs, ".aw", "config", "project.json")`; `install_wizard.resolve_existing_policy`: `proj_json = p_repo / ".aw" / "config" / "project.json"`; ten `project_file = Path(repo_root) / ".aw" / "config" / "project.json"` sites in `config.py`; `run_analytics_config.read_project_settings`: `Path(repo_root).joinpath(".aw", *PROJECT_POLICY_REL)` |
| F-06 | The writers are hard-coded. | `install_wizard.persist_project_policy`: `config_dir = p_repo / ".aw" / "config"`; `config.sync_cutovers_on_install`: `project_file = root / ".aw" / "config" / "project.json"` |
| F-07 | The rest of the clean-target target delta is far larger than config. | same install stages 161 `.aw/system` paths, 41 `.aw/records` paths, `.aw/.gitignore`, host adapters; filed as backlog `kvwwt0` (out of scope) |
| F-09 | `local-only` has the same defect. | scratch target at HEAD `660882253`, `--preset local-only`: dry-run prints `config_project : ~/awh/projects/r-fd67e6/config/project.json [home] (untracked)` and "ZERO AW-owned target files created (clean-target)."; after install `ls .aw/config` -> `local.json project.json`, `delivery_mode` `clean-delta`, `find $AW_HOME` -> `projects/state/durable/install.json` |
| F-10 | `read_project_identity` is a further target-only reader. | `project_context.read_project_identity` candidates `root / ".aw" / "config" / "project.json"` and `root / ".aw" / "config" / "config.json"`; callers `doctor` ("identity = project_context.read_project_identity(repo_root)"), `cli` status, `artifact_core._is_repository_untracked_backend` |
| F-11 | Uninstall removes only target config and state. | `engine.uninstall_repo`: `cfg_dir = repo_root / ".aw" / "config"` and `state_dir = repo_root / ".aw" / "state"`, nothing under `AW_HOME`; `cli._run_uninstall` `has_footprint` probes only target dirs |
| F-08 | Reinstall drops unmodeled `project.json` keys and restamps cutovers. | private-target target: set `cutovers.spec_id6` to `2020-01-01` and add `run`, reinstall -> `2026-10-12 None`; filed as backlog `qyevpr` (out of scope) |

## Proposed changes (ordered, validatable)

1. Shared, pure config locator and empty-id fix in the resolver (E-02).
2. Policy writer targets the resolved class paths (E-03).
3. Every config reader goes through the locator (E-04); install history follows (E-05); uninstall removes what the install wrote under `AW_HOME` (E-09).
4. Consent plan wording made true (E-06).
5. Spec note and CHANGELOG (E-07); behavior tests with mutation proof (E-08).

## Deferred / out of scope (with reason)

- The remaining clean-target target writes (`.aw/system/`, `.aw/records/`, `.aw/.gitignore`, `.aw/inbox`, `.aw/workflow-artifacts`, root ignore files, `.github/workflows`, host adapters).
  - Carrier: kvwwt0
- Reinstall discarding unmodeled `project.json` keys and restamping every cutover to today.
  - Carrier: qyevpr
- Registering clean-target projects in `AW_HOME/registry.json`.
  - Carrier-Declined: not needed for this fix; `_derive_project_id` is deterministic from the repo path, and install does not register any preset today. A moved repo derives a new id; `aw project attach` already exists for that case.
- Clean-delta config in a git worktree of the same repository (a runner lane) derives a different `project_id` from its own path, so it does not find the main checkout's home config.
  - Carrier-Declined: parity with today, not a regression: today the clean-target config is untracked in the target (`?? .aw/config/`, F-01), so a worktree does not see it either. Sharing one home config across worktrees needs a project id keyed on the git common dir, a resolver change outside `mbx0o4`.
- Migrating an existing clean-target install whose config already sits in its target.
  - Carrier-Declined: locator rule 1 keeps such a repo working unchanged; moving its files is a placement migration (spec Section 11), not a writer fix, and no such install exists in this repository.

## Scope check

- Over-scope: none. The reader rerouting (E-04) is required: without it the first command after a fixed clean-target install would treat the repo as unconfigured, a worse regression than the bug.
- Under-scope: none known after review (review added `local-only` coverage F-09, the `read_project_identity` reader F-10, and uninstall parity F-11/E-09) for `mbx0o4`. The backlog item names the config writer and the missing project-id segment; both are covered (E-03, E-02/E-05), and the consent line it quotes is made true (E-06).

## Required tests / validation

- `tests/test_clean_target_config_home.py` (E-08) cases (a) to (j), narrowed run `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py`, with the mutation proof.
- `python3 -m pytest -o addopts="" tests/test_install_consent_truth.py tests/test_install_state_records.py tests/test_project_context.py tests/test_config.py tests/test_project_registry.py tests/test_records_untracked_backend.py tests/test_run_analytics.py tests/test_run_analytics_cli.py` passes.
- Bare `python3 -m pytest` summary line pasted before and after.
- The E-01 scratch probe re-run after E-05 and E-06 shows the fixed layout.

## Spec / documentation sync

- Spec `20260810-1447-01` Section 4 gains a dated amendment (E-07). WHY a plan edits an implemented spec: Section 4 states that a clean-target policy "can therefore leave no target `.aw/`" and Section 5 that a policy must not "claim clean-target while creating any AW-owned target baseline delta"; this plan changes where clean-delta config and state are written and how readers find them, and says plainly which target writes remain, so the spec does not silently overstate what ships.
- CHANGELOG entry under 2.0.0 (pending) (E-07).

## Open questions

### OQ-01: How does a reader find a home-placed config when nothing in the target points at it?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: derive it. `project_context._derive_project_id` is deterministic from the canonical repo path and is exactly what the resolver already uses to build the home paths the consent plan prints (F-02), so the reader can compute `<aw_home>/projects/<id>/config/` with no pointer file (a pointer in the target would itself be an AW-owned target file, defeating the fix) and no registry (install registers nothing today). Target-first ordering (locator rule 1) preserves every existing tracked and legacy install. Reversible: one function.

### OQ-02: Should the consent plan keep promising a zero target delta for clean-target?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: no. F-07 shows the installer still writes hundreds of target paths for this preset; after this plan the config and state classes are true to the promise but the rest is not, and AGENTS.md's consent rule requires the prompt to carry what the human needs to decide. The line is reworded to say what is kept out and what is still written (E-06); restoring the stronger promise is the job of backlog `kvwwt0`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the HEAD sha and the actual output of every E-01 probe (dry-run lines, `ls -a .aw .aw/config`, `git status --short --ignored -- .aw/config .aw/state`, `find "$AW_HOME" -type f`, target `local.json`, resolver `project_id` and `physical_classes`). Produced by the E-01 scratch install (`cli` install path).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: PASTE `git diff agent_workflows/project_context.py` and a `python3 -c` session showing `project_config_dir` and `resolve_project_context(...).project_id` for three temp repos: target `local.json` with `"project_id": ""` (derived non-empty id), home-only `project.json` (home dir returned, `is_configured` True, preset read from it), and neither (target dir returned).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: PASTE `git diff agent_workflows/install_wizard.py` for `persist_project_policy`, then after a real clean-target scratch install `ls -a <target>/.aw` (no `config`), `find "$AW_HOME" -path '*config*' -type f`, and the home `local.json` showing a non-empty `project_id`; and after a private-target scratch install `cat .aw/config/project.json` compared with the pre-change output from E-01's private run (`diff` empty apart from cutover dates).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: PASTE the grep at execution showing no remaining hard-coded `.aw/config/project.json` or `local.json` reader in `agent_workflows/` other than the ones the plan leaves target-relative (with the reason per line), and, in a clean-target scratch target, a second `aw install` output (no first-install behavior), `aw doctor` output showing the stored preset, plus `python3 -c` output of `config.resolve_cutover_date(repo, "spec_id6")` and `config.read_run_policy(repo)` after adding `run` to the home `project.json`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: PASTE `find "$AW_HOME" -type f` after two clean-target installs (four files under `projects/<id>/`, none under `projects/state/`), `wc -l` of the home `installs.jsonl` (2), and `install.json`'s `project_id` line.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: PASTE `git diff` of `engine.uninstall_repo` and `cli._run_uninstall`; in a clean-target scratch target, `find "$AW_HOME" -type f` before and after `aw uninstall . -y`, the uninstall output naming the removed home paths, the `--dry-run` uninstall output listing them without removing, and the following install's output showing first-install behavior.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: PASTE the new clean-target dry-run "Expected Deltas" block, and a shell check that every `config_project`, `config_local` and `state_durable` path the dry-run printed exists after the real install while `<target>/.aw/config` and `<target>/.aw/state` do not; plus the `tests/test_install_consent_truth.py` diff if any.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: PASTE the spec diff, the `aw specs note` output, `aw specs check` output for the spec, and the CHANGELOG diff.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: PASTE the narrowed run of `tests/test_clean_target_config_home.py` (cases (a) to (j) passing), the mutation failure output for case (a), the listed regression files passing, and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one defect, where clean-delta config lives; the writer move (E-03) and the reader rerouting (E-04) must ship together or a fixed install reads as unconfigured, so they are not split across plans.

EXECUTION CONTRACT. Execute only after explicit human approval. OQ-01 and OQ-02 are resolved from repository evidence; no question is open. Execute E-items in dependency order (E-09 after E-05, before E-06). Commit only files changed for this plan through `aw commit p425hv -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME`, `XDG_CONFIG_HOME` and `AW_HOME` pointed at a temp dir, never the operator's real `AW_HOME`. SPEC EDIT: this plan amends implemented spec `20260810-1447-01` (declared in `- Scope-Paths:`, reason in the spec-sync section). SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example a further test pinning the old target-only read, or a reader E-04's re-grep finds in another module) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. Do NOT fix backlog `kvwwt0` or `qyevpr` here. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize p425hv`, never by a hand `git mv`.
