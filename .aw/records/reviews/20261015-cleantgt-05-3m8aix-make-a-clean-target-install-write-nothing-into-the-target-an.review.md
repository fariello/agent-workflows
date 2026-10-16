# Review findings: plan 3m8aix

- Subject-Id: 3m8aix
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `5b1873341`.

- The plan was committed and unchanged, so no snapshot was needed.
- `aw ipd lint --phase author` was clean before the edits.
- No cleantgt child is in `executed/` at this HEAD. The accessors this plan builds on (`fnnwj3` `home_configured_root`, `kfnfji` `project_records_dir`, `4gn1ka` `_system_member_destination`) are therefore verified against their reviewed plans, not against code.

### Evidence verified

- `engine.install_into_repo` step sequence, `use_git = git_available(...)`, `generated_members = {**shim_members, **skill_members}`.
- The five `BACKUPS_DIR` compositions (`allocate_backup_timestamp`, `create_backup_path`, `save_created_files_record`, `prune_old_backups`, `run_rollback`). Every other backup site goes through `create_backup_path`.
- `write_setup_marker` / `remove_setup_marker` / `attention.setup_needed` (in-repo path only), and `doctor.probe_environment` -> `attention.setup_needed`.
- Both `cli._install_one` and `engine.run` call `prompt_and_run_commit`; `print_summary`'s `Git:` line; `render_pre_write_plan`'s adapter lines and the interim `kvwwt0` line.
- The test's `assertIn("tracked by backlog kvwwt0", plan)`.

### Probe

Temp `HOME`/`AW_HOME`, global git identity, `aw install <t> --preset completely-clean-target -y --no-interactive`:

- rc 0, `356 files changed`, `Changes committed: 0af8028`.
- Ignored: `.agent-workflows-installer-backups/`, `.aw/setup-repo-needed.md`, `.aw/system/layout.json`, `.aw/system/layout.schema.json`, `.aw/workflow-artifacts/`.
- Home held `config/` and `state/durable/{history,install.json}`.
- `--dry-run` printed the three target adapter lines and the interim `kvwwt0` line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness / Set coverage | `kfnfji` Deferred: "Installer records scaffolding (`engine._record_scaffold_dirs`, `engine.ensure_plans_readmes`, `engine.ensure_prompts_readmes`, `engine.create_setup_artifacts`, `engine.migrate_local_lanes_to_untracked` ...) Carrier: 3m8aix"; `engine._record_scaffold_dirs` `base = ".aw/records"` | F-01 and the Scope check said children 01/02 remove the records part. `kfnfji` explicitly hands the installer's records scaffolding to THIS plan, and E-03 said only "still scaffolding records under the records-root accessor" without routing anything. So 41 `.aw/records` files would still be written into the target, and nobody in the Set owned them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 (4) routes every records-scaffolding destination through `project_records_dir` via `_records_member_destination` (mirroring `4gn1ka`). F-01, F-07, Scope check and conventions are corrected. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / KISS | `project_context.resolve_project_context` delivery-mode precedence (user `default_delivery_mode`, named profile); `fnnwj3` E-03 `home_configured_root` | E-02's predicate used `resolve_project_context(...).delivery_mode`. That can resolve `clean-delta` from a user-config default with no stored policy, which violates the plan's own "stored policy only" rule. It was also a second mode test, separate from the one children 03/04 use. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 is now a total wrapper over `home_configured_root`; the user-default case is added to the expected outcome and test. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness | `engine.migrate_root_workflow_artifacts(..., use_git=use_git)`, `ensure_plans_readmes`/`ensure_docs_readmes`/`ensure_prompts_readmes`, `check_gitignore`, `print_summary` `Git:` line | E-03's skip list omitted several target-touching steps. `print_summary` would also have claimed "not a git repo" for a git repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now sets `use_git = False` before any step, lists the omitted steps, adds a clean-delta `Git:` line, and verifies `emit_layout_artifacts`/manifest routing from `4gn1ka` in E-01 (5). |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness / rollback | `engine.run_rollback` `target = repo_root / rel` and `git rm --cached`/`git add` | With members at home, the created-files record holds logical names, so rollback would miss them and touch the target index. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 resolves entries through the destination helpers and skips git calls for clean-delta. E-08 `test_case_m` and V-04 prove a rollback with the target left empty. |
| PR-005 | MEDIUM | UNDER-SCOPE | E. Testing | E-05 edits the `engine.run` shell; E-08 tested only `cli` subprocesses | The second shell had no test, and nothing checked a reinstall or the tracked summary parity. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `test_case_m` (reinstall + rollback), `test_case_n` (`engine.run` in-process), tracked parity in `test_case_l`, and the E-01 parity captures. |
| PR-006 | LOW | IN-SCOPE | C. Architecture | `write_setup_marker`, `remove_setup_marker`, `attention.setup_needed` each compose the path | Three separate path compositions could name different files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | One `engine.setup_marker_path` accessor; `aw doctor --json` is added to the V-05 evidence. |
| PR-007 | MEDIUM | UNDER-SCOPE | F. UX / honest docs | `.aw/system/workflows/setup-repo/setup-repo.md` "rm -f .aw/setup-repo-needed.md"; `doctor` `doctor.setup-needed` remediation; `aw --help` has no marker verb | After E-05, `/setup-repo` cannot clear a clean-delta reminder, and the plan only called its `rm` "a no-op". | C:Medium; U:Medium; S:Low; F:Low; Overall:Medium | OPEN | Raised as non-blocking OQ-03 (maintainer, carrier `nwporz`). The fix needs a public verb or a system-bundle prose change outside this plan's Scope-Paths. The failure is fail-safe: the reminder over-reports. |
| PR-008 | LOW | IN-SCOPE | G. Executability | Gate "Execute E-01..E-07 in order"; "Cohesion rationale: not required"; no `- Readiness:` | The gate omitted E-08, had no blocked-accessor rule and no OQ status statement, and gave no cohesion rationale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate and cohesion are updated. |
| PR-009 | LOW | IN-SCOPE | G. Traceability | `aw check all`: `check.ipd-uncarried-obligation` "deferred row 1: carrier or061f resolves to no backlog item or plan" (ERROR, pre-existing) | The user-scope adapter deferral named a spec id as its carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Repointed to source item `kvwwt0` (the spec id and the parked `m15n3k` both fail the rule, measured). The remaining `check.ipd-carrier-ungated` (INFO) for OQ-03 is intended: the question is non-blocking. |

PR-007 is OPEN at MEDIUM, below the `HIGH` gate threshold. It is carried as non-blocking OQ-03 rather than escalated as blocking.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who owns the installer's records scaffolding? | This plan (E-03 (4)) | Leave it to `kfnfji` (which explicitly deferred it here); add a new child | `kfnfji` Deferred row "Installer records scaffolding ... Carrier: 3m8aix" | yes |
| D-2 | Which mode predicate should the installer use? | Wrap `fnnwj3`'s `home_configured_root` | `resolve_project_context(...).delivery_mode` (reads user defaults, not the stored policy) | plan convention "reads the stored policy"; resolver delivery-mode precedence | yes |
| D-3 | Should this plan add a marker-clear verb or edit the `/setup-repo` prose? | No; raise OQ-03 for the maintainer, carried by `nwporz` | Add `aw setup-marker clear` (public CLI surface); edit the shipped workflow prose | Scope-Paths; AGENTS.md "public contracts" are the human's to decide | yes |
