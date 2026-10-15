# IPD: Make a clean-target install write nothing into the target and state that truthfully

- Date: 2026-10-15
- Kind: child
- Concern: After children 01..04 route records, system, project recognition, run state and worktrees through stored-policy accessors, `engine.install_into_repo` and `cli._install_one` still unconditionally write host adapters, `AGENTS.md`, root `.gitignore`, `.aw/.gitignore`, `.gitleaksignore`, `.github/workflows/secret-scan.yml`, `.aw/inbox/README.md`, `.aw/workflow-artifacts/README.md`, the `.aw/setup-repo-needed.md` marker and `.agent-workflows-installer-backups/` into the target, stage them, and auto-commit them; measured at HEAD `57d5e8184` a `completely-clean-target` install advances target HEAD by a 356-file commit and leaves 5 ignored target paths. The consent plan (`install_wizard.render_pre_write_plan`) still prints the interim `tracked by backlog kvwwt0` disclosure.
- Scope: In `agent_workflows/engine.py`, add one stored-policy predicate (`engine._is_clean_delta_install`) and, when it is true, skip every target-only write, stage and commit in `engine.install_into_repo` (host adapters, AGENTS pointer, root and `.aw/` gitignores, inbox and workflow-artifacts READMEs, gitleaks/secret-scan setup artifacts, tracked-policy staging) and route the backup directory and created-files record under `<AW_HOME>/projects/<project_id>/state/runtime/backups/` (`engine.allocate_backup_timestamp`, `engine.create_backup_path`, `engine.save_created_files_record`, `engine.prune_old_backups`, `engine.run_rollback`); in `agent_workflows/cli.py` make `cli._install_one` skip `engine.prompt_and_run_commit` and write the setup marker under home runtime state, and teach `attention.setup_needed` to read it there; in `agent_workflows/install_wizard.py` restore the honest ZERO-target-delta line and the no-host-adapter line for clean-delta; lock the behavior with subprocess tests in `tests/test_install_consent_truth.py` and `tests/test_clean_target_config_home.py`.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/install_wizard.py, agent_workflows/attention.py, tests/test_install_consent_truth.py, tests/test_clean_target_config_home.py
- Item-Dependencies: executed:qk0ew6
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 5
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3m8aix

## Workflow history
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw install <target> --preset completely-clean-target -y` and `--preset local-only -y` leave the target with `git status --porcelain --ignored` empty and HEAD unchanged, with every artifact the install produces (system, records, config, state, backups, the created-files record and the setup marker) under `<AW_HOME>/projects/<project_id>/`, and make the pre-write consent plan say exactly that. This is the install half of the maintainer's 2026-10-15 clean-delta goal: nothing from agent-workflows visible in a public target checkout.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and the one clean-delta predicate

- [ ] E-01 Re-measure at execution HEAD the symbols this plan edits (`engine.install_into_repo`, `cli._install_one`, `install_wizard.render_pre_write_plan`, `engine.allocate_backup_timestamp`, `engine.create_backup_path`, `engine.save_created_files_record`, `engine.prune_old_backups`, `engine.run_rollback`, `engine.write_setup_marker`, `engine.prompt_and_run_commit`, `attention.setup_needed`) and the accessors children 01..04 delivered (the records-root and system-root accessors in `agent_workflows/project_context.py`, and the home state/worktrees routing), then reproduce the baseline: in a temp git repo with temp `HOME`/`AW_HOME` and a git identity, run `aw install <t> --preset completely-clean-target -y --no-interactive` and record the target HEAD delta and `git status --porcelain --ignored`.
  - Depends on: none
  - Expected outcome: Symbol locations and accessor names recorded in V-01; baseline shows the residual target writes this plan removes (at authoring HEAD `57d5e8184`: HEAD advanced by one 356-file commit, ignored `.agent-workflows-installer-backups/`, `.aw/setup-repo-needed.md`, `.aw/system/layout.json`, `.aw/system/layout.schema.json`, `.aw/workflow-artifacts/`; after children 01..04 the system/records counts are expected to be gone and only target-only adapter/setup writes remain).
  - Execution state: pending

- [ ] E-02 Add `engine._is_clean_delta_install(repo_root: Path) -> bool` that reads the STORED policy only: true iff `project_context.project_config_dir(repo_root) / "project.json"` is a file and `project_context.resolve_project_context(target_repo=str(repo_root)).delivery_mode == DeliveryMode.CLEAN_DELTA.value`. It never re-derives from a preset name (irjoga PR-003/PR-004) and writes nothing. `cli._run_install` calls `install_wizard.persist_project_policy` before `cli._install_one`, so the stored policy exists when `install_into_repo` runs.
  - Depends on: E-01
  - Expected outcome: The predicate returns True after a `completely-clean-target` or `local-only` policy is persisted, False for `private-target`, `public-target-private-companion`, a repo with no stored config, and a repo whose stored policy is tracked.
  - Execution state: pending

### Task group 2: Suppress every target write, stage and commit under clean-delta

- [ ] E-03 In `engine.install_into_repo`, when `_is_clean_delta_install(repo_root)` is true: pass an empty generated-members map (no `shim_members`, no `_build_skill_members` output) to `install_all` and `prune_stale`; skip `update_agents_pointer`, `ensure_backups_gitignored`, `ensure_untracked_gitignore`, `ensure_workflow_artifacts_readme`, `ensure_inbox_readme`, `_ensure_aw_gitignore`, `stage_tracked_policy_files` and `warn_tracking_and_scan`; make `create_setup_artifacts` skip the target-only entries (`AW_GITIGNORE_PATH`, `GITLEAKSIGNORE_FILE`, `SECRET_SCAN_CI`) while still scaffolding records under the records-root accessor; force `use_git` False for every staging call (`_stage_installed_file`, `git_add_optional`) so the target index is never touched; and return status strings that say the step was skipped for clean-delta (consumed by `print_summary`).
  - Depends on: E-02
  - Expected outcome: No call inside `install_into_repo` writes or stages a path under `repo_root` for a clean-delta policy; the returned `use_git` is False so `print_summary` prints the filesystem-only line rather than "changes staged; commit offered below".
  - Execution state: pending

- [ ] E-04 Route installer backups and the `--undo` created-files record under home runtime state for clean-delta: add `engine._backups_root(repo_root) -> Path` returning `Path(resolve_project_context(target_repo=str(repo_root)).physical_classes["state_runtime"]) / "backups"` when `_is_clean_delta_install(repo_root)` and `repo_root / BACKUPS_DIR` otherwise, and use it in `allocate_backup_timestamp`, `create_backup_path`, `save_created_files_record`, `prune_old_backups` and `run_rollback` instead of `repo_root / BACKUPS_DIR`. Created-files entries stay repo-or-home relative exactly as today (no path format change).
  - Depends on: E-02
  - Expected outcome: After a clean-delta install `<AW_HOME>/projects/<id>/state/runtime/backups/<ts>/.created-files.json` exists and `<target>/.agent-workflows-installer-backups/` does not; a tracked install still writes `<target>/.agent-workflows-installer-backups/`.
  - Execution state: pending

- [ ] E-05 In `cli._install_one`, when `engine._is_clean_delta_install(repo_root)` is true skip `engine.prompt_and_run_commit` entirely (print one `ok` status line saying nothing was staged or committed in the target) and write the setup marker under home runtime state instead of `<target>/.aw/setup-repo-needed.md`: give `engine.write_setup_marker` a clean-delta branch writing `<state_runtime>/setup-repo-needed.md` without calling `_ensure_aw_gitignore`, give `engine.remove_setup_marker` the matching branch, and make `attention.setup_needed` check that home path when the in-repo marker is absent. Apply the same `prompt_and_run_commit` skip in the `engine.run` presentation shell, which calls `install_into_repo` then `prompt_and_run_commit` independently.
  - Depends on: E-03
  - Expected outcome: A clean-delta install leaves target HEAD unchanged even with a configured git identity and `-y`; `aw attention` on that target still reports setup pending, read from `<AW_HOME>/projects/<id>/state/runtime/setup-repo-needed.md`.
  - Execution state: pending

### Task group 3: Truthful consent text and tests

- [ ] E-06 Update `install_wizard.render_pre_write_plan` so that when `policy.delivery_mode == DeliveryMode.CLEAN_DELTA.value` the `Host Adapter Exceptions:` block prints `  - None in target repository (clean-delta writes no target host adapters).` instead of the three target adapter lines, and `Expected Deltas:` prints `  Target Delta:     ZERO AW-owned target files created (clean-target).` replacing the interim line ending `(tracked by backlog kvwwt0).`; non-clean-delta output is byte-identical.
  - Depends on: E-05
  - Expected outcome: `aw install <t> --preset completely-clean-target --dry-run` prints the ZERO line and no target adapter path; `aw install <t> --preset private-target --dry-run` prints the same lines as before.
  - Execution state: pending

- [ ] E-07 Rewrite `TestInstallConsentTruth.test_clean_target_consent_paths_and_delta` in `tests/test_install_consent_truth.py` to assert, for both clean presets, the restored ZERO line and the no-adapter line in `render_pre_write_plan` output, then run a real subprocess `install --preset completely-clean-target -y` with a git identity and assert `git status --porcelain --ignored` is `""` and HEAD is unchanged (P16: outcomes only, no source-text assertions).
  - Depends on: E-06
  - Expected outcome: The consent claim and the real install outcome are checked against each other in one test, which fails if either drifts.
  - Execution state: pending

- [ ] E-08 Add to `tests/test_clean_target_config_home.py`: `test_case_k_clean_target_install_zero_target_delta` (both presets by subprocess: empty porcelain-ignored output, unchanged HEAD, no `<target>/.aw`, `AGENTS.md`, `.agents`, `.claude`, `.opencode`, `.github`, `.gitignore`, `.gitleaksignore`; present `<AW_HOME>/projects/<id>/state/runtime/backups/*/.created-files.json` and `setup-repo-needed.md`), `test_case_l_tracked_install_still_writes_target` (private-target still writes `AGENTS.md`, `.aw/.gitignore`, target backups), and a unit test for `engine._is_clean_delta_install`; then perform the mutation proof and the bare suite run.
  - Depends on: E-03, E-04, E-05, E-07
  - Expected outcome: Narrowed run passes; with `_is_clean_delta_install` forced to `False` the zero-delta tests fail and pass again after restore; bare `python3 -m pytest` shows no failure that does not also fail on the base commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context.py` is PURE (module docstring: "PURE: ZERO filesystem writes, directory creation, or Git mutation."); this plan adds no writer there. The predicate and backup root live in `engine.py`.
- Every routing decision reads the stored policy (`project_config_dir(repo)/project.json`) and `resolve_project_context(...).physical_classes`; never the preset name (irjoga PR-003: an unstored `local-only` resolves `delivery_mode == "tracked"`).
- `engine.install_into_repo` is the single shared install core (its docstring "This is the single shared source of the install STEPS (D83)"); `cli._install_one` is the one per-repo shell that adds summary, marker and commit offer; `engine.run` has its own presentation shell that also calls `prompt_and_run_commit`. Both shells must honor the skip.
- `aw install --undo` is not a CLI flag on `aw install` (`aw install --help` lists none); `engine.run_rollback` is reached through the engine `run()` `args.undo` path (`install-workflows.py`), so backups routing is tested through `engine.run_rollback` directly.
- Subprocess install tests are not marked `slow` today in either test file (grep for `pytestmark` returns nothing), so they run in the default bare suite. Fixtures set `HOME`/`AW_HOME` to temp dirs, unset `XDG_CONFIG_HOME`/`AW_CONFIG_DIR`, and pass a git identity so the auto-commit path is exercised.
- Suite: bare `python3 -m pytest`; narrowed verbose runs use `python3 -m pytest -o addopts="" <files>` (AGENTS.md repository development contract).
- No em or en dashes in user-facing strings (CLI and wizard output).

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `engine.install_into_repo` | Measured at HEAD `57d5e8184` (temp repo, temp AW_HOME, git identity, `--preset completely-clean-target -y`): rc 0, target HEAD advanced by one commit of 356 files (161 `.aw/system`, 94 `.agents/skills`, 41 `.aw/records`, 27 `.opencode/commands`, 27 `.claude/commands`, plus `.aw/.gitignore`, `.aw/inbox/README.md`, `.github/workflows/secret-scan.yml`, `.gitignore`, `.gitleaksignore`, `AGENTS.md`), and `git status --porcelain --ignored` lists `.agent-workflows-installer-backups/`, `.aw/setup-repo-needed.md`, `.aw/system/layout.json`, `.aw/system/layout.schema.json`, `.aw/workflow-artifacts/`. Home held only `config/` and `state/`. Children 01/02 remove the system/records part; the rest is this plan. |
| F-02 | High | `engine.install_into_repo` steps `update_agents_pointer`, `ensure_backups_gitignored`, `ensure_untracked_gitignore`, `ensure_workflow_artifacts_readme`, `ensure_inbox_readme`, `_ensure_aw_gitignore`, `create_setup_artifacts`, `stage_tracked_policy_files` | Each runs unconditionally with `use_git = git_available(plan.repo_root)`; none consults `delivery_mode`. `generated_members = {**shim_members, **skill_members}` is always passed to `install_all`. |
| F-03 | High | `cli._install_one` and `engine.run` | Both call `engine.prompt_and_run_commit`, which returns early only on `not use_git or plan.dry_run`; under `-y` it commits. `cli._install_one` also calls `engine.write_setup_marker`, which writes `.aw/setup-repo-needed.md` and calls `_ensure_aw_gitignore`. |
| F-04 | Medium | `engine.allocate_backup_timestamp`, `engine.create_backup_path`, `engine.save_created_files_record`, `engine.prune_old_backups`, `engine.run_rollback` | All five compose `repo_root / BACKUPS_DIR` (`BACKUPS_DIR = ".agent-workflows-installer-backups"`); `grep BACKUPS_DIR` finds no other composition site in `agent_workflows/`. |
| F-05 | Medium | `attention.setup_needed` | Reads only `(Path(repo_root) / ".aw" / "setup-repo-needed.md").is_file()`; moving the marker without teaching this reader would silently drop "setup pending" for clean-delta. |
| F-06 | Medium | `install_wizard.render_pre_write_plan` and `tests/test_install_consent_truth.py` `TestInstallConsentTruth.test_clean_target_consent_paths_and_delta` | The function prints three target adapter paths for every policy and, for clean-delta, the interim line "...host adapters are still written into the target (tracked by backlog kvwwt0)."; the test asserts `assertNotIn("ZERO AW-owned target files", plan)` and `assertIn("tracked by backlog kvwwt0", plan)`, so it must be inverted in the same change. |

## Proposed changes (ordered, validatable)

1. E-01: baseline re-measure and reproduction (no code change).
2. E-02: `engine._is_clean_delta_install(repo_root)`, stored-policy only.
3. E-03: guard each target-only step in `engine.install_into_repo` with the predicate; empty generated members; force `use_git=False` for staging; clean-delta skip status strings.
4. E-04: `engine._backups_root(repo_root)` adopted by the five backup functions.
5. E-05: `cli._install_one` and `engine.run` skip `prompt_and_run_commit` under clean-delta; `write_setup_marker`/`remove_setup_marker`/`attention.setup_needed` home branch.
6. E-06: `render_pre_write_plan` clean-delta lines.
7. E-07: consent-truth test rewrite.
8. E-08: zero-delta and regression tests, mutation proof, bare suite.

## Deferred / out of scope (with reason)

- Delivering host adapters and skills to user-scope host directories (`~/.config/opencode/`, `~/.claude/`) for clean-delta, so an agent in the target can discover the workflows without in-repo shims. This plan stops writing them into the target; user-scope delivery is a separate feature already specified in deferred spec `or061f`.
  - Carrier: or061f
- Uninstall of the home trees this install creates (backups, marker, system, records, worktrees). Owned by the next Set child.
  - Carrier: xoy5yg
- Spec `20260810-1447-01` amendment, CHANGELOG line, and the end-to-end ordinary-use zero-delta proof. Owned by the final Set child so the contract is amended once, after the behavior exists.
  - Carrier: nwporz

## Scope check

- Over-scope: none. Each item removes one class of target write, or makes the consent text and tests match the new behavior.
- Under-scope: none known. Every target write observed in the F-01 baseline is either removed here (adapters, AGENTS.md, gitignores, gitleaks, secret-scan, inbox README, workflow-artifacts README, marker, backups, commit) or by children 01/02 (system, records, layout artifacts). E-01 re-runs the baseline after 01..04 so any residual path is caught before editing; a residual path found there is in scope here.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_install_consent_truth.py tests/test_clean_target_config_home.py -v` passes, including the new cases.
- Subprocess proof, both presets: `git -C <t> status --porcelain --ignored` prints nothing and `git -C <t> rev-parse HEAD` equals the pre-install value.
- Regression: `private-target` install still writes target `AGENTS.md`, `.aw/.gitignore` and `.agent-workflows-installer-backups/`.
- Mutation proof: make `_is_clean_delta_install` return `False`, observe the zero-delta tests fail, restore, observe pass.
- Bare `python3 -m pytest` summary line pasted.

## Spec / documentation sync

N/A in this plan: spec `20260810-1447-01` Section 4/5 amendment, `aw specs note`, and the CHANGELOG `- Fixed:` line are owned by Set child `nwporz` (Order 07), which amends the contract once after install, uninstall and ordinary use are all zero-delta. No spec file is edited here, so none is in `- Scope-Paths:`.

## Open questions

### OQ-01: Where should the setup-repo-needed marker live for clean-delta, given the target may hold nothing?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Under `<state_runtime>/setup-repo-needed.md` (home runtime state), read by `attention.setup_needed`. Evidence: the marker is per-machine and gitignored by design (`engine.write_setup_marker` docstring, and `doctor` remediation text "it clears the .aw/setup-repo-needed.md reminder"), `state_runtime` is the untracked per-machine class in every preset (spec 20260810-1447-01 Section 5: "`config_local` and `state_runtime` MUST be untracked in every preset"), and the maintainer decision of 2026-10-15 puts all clean-delta per-machine state under `AW_HOME/projects/<project_id>/state/`. The `/setup-repo` workflow text that says `rm -f .aw/setup-repo-needed.md` is a no-op for clean-delta; `aw attention` stays correct because it reads the home path.

### OQ-02: Should a clean-delta install still auto-commit anything anywhere?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `resolve_project_context` sets `permitted_commit_destinations` to `None` for product when `delivery_mode != tracked` (irjoga F-02), and the acceptance bar is HEAD unchanged. Home trees are not a git repository in these presets, so there is nothing to commit; `prompt_and_run_commit` is skipped outright.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `grep -n` output locating each symbol listed in E-01 at execution HEAD, the names of the accessors children 01..04 added, and the pasted baseline reproduction output (`git rev-parse HEAD` before/after, `git show --stat --format= HEAD | tail -1`, `git status --porcelain --ignored`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff` hunk adding `engine._is_clean_delta_install` and pasted output of the new predicate unit test run (`python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k is_clean_delta -v`) showing True for both clean presets and False for private-target, companion, and unconfigured repos.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/engine.py` for `install_into_repo`, plus pasted subprocess output (path: `cli._run_install` -> `cli._install_one` -> `engine.install_into_repo`) of a clean-target install showing `git status --porcelain --ignored` empty and no `AGENTS.md`, `.agents/`, `.claude/`, `.opencode/`, `.github/`, `.gitignore`, `.gitleaksignore`, `.aw/` in the target (`ls -A <t>` pasted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `ls` of `<AW_HOME>/projects/<id>/state/runtime/backups/*/` showing `.created-files.json`, pasted absence check of `<t>/.agent-workflows-installer-backups`, and pasted output of a test calling `engine.run_rollback(<t>, True)` on a clean-delta install returning 0 using the home backups.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted subprocess output of a clean-target install with a configured git identity and `-y` showing the "nothing staged or committed" status line, `git rev-parse HEAD` unchanged before/after, the home marker path existing, and `aw attention` (path: `attention.setup_needed`) reporting setup pending on that target.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `aw install <t> --preset completely-clean-target --dry-run` output showing `Target Delta:     ZERO AW-owned target files created (clean-target).` and `None in target repository`, and pasted `--preset private-target --dry-run` output showing the unchanged adapter lines.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted `git diff -- tests/test_install_consent_truth.py` and pasted `python3 -m pytest -o addopts="" tests/test_install_consent_truth.py -v` output showing `test_clean_target_consent_paths_and_delta` PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Pasted narrowed run `python3 -m pytest -o addopts="" tests/test_install_consent_truth.py tests/test_clean_target_config_home.py -v` summary; pasted failing output under the mutation (`_is_clean_delta_install` forced False) and passing output after restore; pasted bare `python3 -m pytest` summary line, with any failure shown to fail identically on the base commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Do not execute until `- Status: approved` and `qk0ew6` is executed (Item-Dependencies). Execute in an isolated worktree via `aw work begin 3m8aix` (or under `aw oc run`, which isolates by default). Execute E-01..E-07 in order. Mark an `E-*` performed only after doing it and a `V-*` pass only with concrete pasted evidence; paste the ACTUAL runner output and never claim a pass you did not run. Every install probe and test uses a temp git repo with temp `HOME`/`AW_HOME`; never install into this repository or the real home. The mutation proof is temporary and MUST NOT be committed. Commit only the paths you changed plus this IPD through `aw commit 3m8aix -- <paths>`; never `git add -A`, never push, never `--no-verify`.

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize 3m8aix`. Never `git mv` the plan by hand. This plan inherits `- Blocks-Release: next` from `kvwwt0`.
