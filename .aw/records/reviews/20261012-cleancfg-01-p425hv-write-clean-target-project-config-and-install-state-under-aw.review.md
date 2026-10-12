# Review findings: plan p425hv

- Subject-Id: p425hv
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `660882253` in an isolated review lane. The plan was committed and unchanged (lane input sha256 `c68e3806...` matches the tracked file), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions. `check_engine.evaluate_durable_carrier` returns `[]` after revisions.

Re-verified in scratch targets (`AW_NO_REEXEC=1`, `HOME`/`XDG_CONFIG_HOME`/`AW_HOME` in `/tmp/opencode`, worktree package on `PYTHONPATH`):
- F-01..F-04 reproduce for `completely-clean-target`: dry-run `config_project : ~/awh/projects/r2-beaf85/config/project.json [home] (untracked)` and "Target Delta:     ZERO AW-owned target files created (clean-target)."; after the install `ls .aw/config` -> `local.json project.json`, `?? .aw/config/`, `!! .aw/config/local.json`, `"project_id": ""`; `find $AW_HOME` -> `projects/state/durable/install.json`, `projects/state/durable/history/installs.jsonl`; resolver `project_id ''`, `config_project` `<aw_home>/projects/config/project.json`.
- `local-only` behaves the same (dry-run home paths and ZERO line, then target `.aw/config`, `delivery_mode` `clean-delta`, `projects/state/durable/install.json`).
- `public-target-private-companion` resolves `delivery_mode` `tracked` with target `config_project`, so E-03's resolver call leaves it unchanged. `private-target` dry-run prints target paths.
- Anchors resolve: `install_wizard.persist_project_policy` (`config_dir = p_repo / ".aw" / "config"`), `install_wizard.resolve_existing_policy` (`proj_json = p_repo / ".aw" / "config" / "project.json"`), `project_context.resolve_project_context` (`merged_local_binding.get("project_id", ...)`, `project_aw_dir = os.path.join(aw_home_abs, "projects", project_id)`), `project_context._derive_project_id`, the ten `config.py` sites, `install_history.record_install_history` (`project_file`), `cli` D92 probe, `engine.stage_tracked_policy_files` (`proj_json_path`). All the regression test files listed in the plan exist.
- Readers missing from E-04: `project_context.read_project_identity` (callers `doctor`, `cli` status, `artifact_core._is_repository_untracked_backend`). Writers/removers missing: `engine.uninstall_repo` (`cfg_dir = repo_root / ".aw" / "config"`, `state_dir = repo_root / ".aw" / "state"`), `cli._run_uninstall` `has_footprint`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `engine.uninstall_repo` "Deterministic framework-created lifecycle files (config, state, .aw/.gitignore)"; `cli._run_uninstall` `has_footprint` | Today uninstall removes target `.aw/config` and `.aw/state`. After E-03 a clean-delta install's config and state live under `AW_HOME`, so uninstall would leave them behind. Locator rule 2 would then make a reinstall at the same path silently adopt the stale policy, so the uninstall-then-fresh-install path regresses. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-09/V-09: remove exactly the written home files, confined to `<aw_home>/projects/<id>/`, report them, preview them under `--dry-run`, and extend `has_footprint`. Added F-11 and test (i). Added `engine.py` to Scope-Paths. |
| PR-002 | HIGH | UNDER-SCOPE | D. Anti-regression | `project_context.read_project_identity` candidates `root / ".aw" / "config" / "project.json"`; callers `doctor`, `cli` status, `artifact_core._is_repository_untracked_backend` | E-04's reader census omitted the shared identity reader. After the move, `aw doctor`/`aw status` would report preset `None` for a clean-target repo, and the untracked-backend probe would misread it. This is the exact "reads as unconfigured" regression the plan's cohesion rationale warns about. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added it to E-04, with an `aw doctor` expectation, V-04 evidence and test (h). Added F-10 and `doctor.py` to Scope-Paths. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing | scratch `--preset local-only`: same ZERO line, target `.aw/config`, `projects/state/` | `local-only` is also `clean-delta` and has the identical defect, but the plan exercised only `completely-clean-target`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 probes it, E-06 covers its dry-run, and test (g) repeats (a)/(b) for it. Added F-09. Test (j) pins public-target-private-companion as unchanged. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness (honest limit) | `project_context._find_git_root` (walks up to the nearest `.git`); `_derive_project_id` hashes `repo_abs` | A derived project id is per worktree path, so a runner lane of a clean-delta repo does not find the main checkout's home config. This is unstated. It is parity with today, since the target config is untracked there too. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded under Deferred with `Carrier-Declined` and the reason. |
| PR-005 | LOW | IN-SCOPE | Step 3 decision recording / G. gate | OQ-01/OQ-02 `- Owner: none`; gate "Execute E-items in order" | The resolved questions had no owner. The gate lacked an explicit human-approval line, and its ordering became ambiguous once E-09 was added. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owners set to `plan author`. The gate now requires approval and states the dependency order. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How is home config found with no target pointer? | Derive `<aw_home>/projects/<_derive_project_id(repo)>/config` (the plan author's choice, kept). | A target pointer file (itself a target write); a registry entry (install registers nothing). | `project_context._derive_project_id`; F-02 dry-run paths | yes |
| D-2 | Should uninstall remove home files, given the risk of deleting outside the target? | Yes, only the files this plan writes, confined to `<aw_home>/projects/<id>/`, and listed. | Leave them (stale policy silently adopted on reinstall); remove the whole `projects/<id>/` tree (could delete a future class this plan does not own). | `engine.uninstall_repo` removes the target equivalents today | yes |
| D-3 | Should worktrees share one home config? | No, recorded as a declined limit. | Key the project id on the git common dir (a resolver identity change outside `mbx0o4`). | parity with the F-01 untracked target config | yes |
