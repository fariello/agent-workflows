# IPD: Fix companion and AW_HOME core storage context placement switch and git_mv bugs

- Date: 2026-11-24
- Kind: child
- Concern: Core context, storage, and placement-switch modules have 14 verified defects affecting companion repositories (`records_backend == "companion"`) and `~/.aw/` (`AW_HOME` / `records_backend == "home"` / `clean-delta`): split-brain `AW_HOME` resolution between `project_context` and `config`/`project_registry`; stale `.aw/config/local.json:companion_dir` overriding `storage.move_companion`/`detach_companion`/`reattach_companion`; missing security/non-nesting validation on explicit or `local.json` `companion_dir`; companion `.gitignore` omitting `records/runs/`, `records/history.jsonl`, `records/*/untracked/`, and `INDEX.*`; unhashed machine-local path written to `companion_identity.json:git_common_dir_hash`; `placement_switch` rollback deleting pre-existing companion identity/attachment files or tracked `.aw/.gitignore`, staging `repository-untracked` records, checking wrong leftover root on `in-place` attach, dropping custom `project_id`, and dereferencing tracked symlinks; `record_placement.resolve_type_dir` falling back to `.agents/` before checking stored external placement; `artifact_core.git_mv` degrading to unstaged `shutil.move` on home local-git and custom companion repos; `artifact_core._is_verbatim_preserved` missing external research paths; `project_context` cache invalidation and `local-only` preset derivation bugs; `config.plan_cutovers_update` discarding `aw_home`; and `project_layout` dropping `companion_dir` or hardcoding `.aw/system`.
- Scope: Fix all 14 core storage/context/placement bugs in `project_context.py`, `config.py`, `project_registry.py`, `storage.py`, `placement_switch.py`, `record_placement.py`, `artifact_core.py`, and `project_layout.py`, with behavioral tests covering both companion and `~/.aw/` modes. Excludes installer (`7gverp`), `status_set`/finalize (`mmuv3v`), CLI record verbs (`7eivm2`), hooks (`7hfx7r`), and runner lanes (`4vnd36`).
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/config.py, agent_workflows/project_registry.py, agent_workflows/storage.py, agent_workflows/placement_switch.py, agent_workflows/record_placement.py, agent_workflows/artifact_core.py, agent_workflows/project_layout.py, tests/test_companion_containment_and_storage.py, tests/test_home_isolation.py, tests/test_placement_switch_companion_execute.py, .aw/records/plans/pending/20261124-comphome-01-ywl7uc-fix-companion-and-aw-home-core-storage-context-placement-swi.ipd.md
- Item-Dependencies: none
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 1
- Highest E allocated: 6
- Id: ywl7uc
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 01 child IPD for `/assess-bugs` (Set `comphome`).

## Goal

Make `AW_HOME` resolution, companion attachment/move/detach persistence, security containment, placement-switch rollback, external record placement, and `git_mv` reliable and leak-free across both companion and `~/.aw/` modes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Context, `AW_HOME` unification, and cache invalidation

- [ ] E-01 Unify `AW_HOME` resolution across `project_context.py`, `config.py`, and `project_registry.py`: share one canonical resolver with `$VAR` expansion (`os.path.expandvars`) and consistent `XDG_CONFIG_HOME` behavior, and plumb `aw_home` plus primary-checkout fallback into `config.plan_cutovers_update`.
  - Depends on: none
  - Expected outcome: `config.get_aw_home()`, `project_context._resolve_effective_aw_home()`, and `project_registry.find_project()` always resolve the same `AW_HOME` root, and `plan_cutovers_update` honors explicit `aw_home` and linked worktrees.
  - Execution state: pending

- [ ] E-02 Harden companion path security, preset derivation, and cache invalidation in `agent_workflows/project_context.py`: enforce `_check_path_security` and bidirectional `_is_safe_subpath` non-nesting checks on explicit and `local.json` `companion_dir`; use `canon_path.parts` in `record_owner_root`; derive `DeliveryMode.CLEAN_DELTA` for `Preset.LOCAL_ONLY`; resolve linked-worktree gitfiles in `_git_index_stamp` and watch `<system_root>/VERSION`, `<state_root>/actions/open`, active profile, and `<aw_home>/config/registry.json` in `_watched_context_paths`.
  - Depends on: E-01
  - Expected outcome: nested or traversal `companion_dir` raises `PathSecurityError`; relative paths under external `records/` resolve in `record_owner_root`; `local-only` derives `clean-delta`; linked worktree staged policy violations invalidate cache.
  - Execution state: pending

### Task group 2: Companion storage attachment, `.gitignore`, and portable identity

- [ ] E-03 Fix companion storage persistence in `agent_workflows/storage.py`: update `.aw/config/local.json:companion_dir` atomically in `attach_companion`, `move_companion`, and `reattach_companion` and clear it in `detach_companion` (preserving other fields); SHA-256 hash `comp_git_common` before passing `git_common_dir_hash` to `create_companion_identity` so no raw machine-local path is written into `.aw/companion_identity.json`; expand `materialize_companion_storage`'s `.gitignore` to ignore `records/runs/`, `records/history.jsonl`, `records/*/untracked/`, and `records/{plans,research,prompts}/INDEX.{json,md}`.
  - Depends on: E-02
  - Expected outcome: after `move_companion`/`detach_companion`/`reattach_companion`, `resolve_project_context` immediately resolves the new (or detached) target without stale `local.json` override; `companion_identity.json` contains no raw local paths; companion `git status` ignores runtime runs, history sidecar, untracked lanes, and generated indexes.
  - Execution state: pending

### Task group 3: Placement-switch rollback, leftovers, custom `project_id`, and symlinks

- [ ] E-04 Fix `agent_workflows/placement_switch.py` transaction and rollback defects: guard `_perform_rollback` so pre-existing `.aw/companion_identity.json` and `.aw/state/durable/companion_attachment.json` are only unlinked/restored when the transaction actually created or modified them (`attach_started`/`detach_started`); snapshot `prior_aw_gitignore_bytes` before calling `_ensure_aw_gitignore` in `_run_records_transaction` and call `ensure_untracked_records_ignore` (without staging `.aw/records/**`) when switching to `repository-untracked`; include `"in-place"` in the `old_records_root` leftover check during companion attach; persist planned `old_records_root`/`new_records_root` so custom `project_id` works in `execute_records_root_switch`; resolve parent-only (`p.parent.resolve() / p.name`) in `git_owner`, `is_tracked`, and staging/removal so tracked symlinks targeting outside the repo are preserved.
  - Depends on: E-03
  - Expected outcome: detach and records-switch rollbacks never delete pre-existing companion identity, attachment metadata, or tracked `.aw/.gitignore`; `home -> repository-untracked` leaves records ignored and unstaged; custom `project_id` switches pass verification; tracked symlinks migrate intact.
  - Execution state: pending

### Task group 4: Record placement, `artifact_core.git_mv`, verbatim research, and `project_layout`

- [ ] E-05 Fix external-records path and move helpers in `record_placement.py`, `artifact_core.py`, and `project_layout.py`: move the `has_stored_records_placement(repo_root)` check ahead of the `.agents/` fallback in `record_placement.resolve_type_dir`; update `artifact_core.git_mv` to fall back to `resolved_root` when `record_owner_root` is `None`, redirect `actual_git_root` via `record_git_root(resolved_src)` for both `companion` and `home` local-git repos, and raise `MoveOutsideRepositoryError` if `resolved_dst` escapes `actual_git_root`; include `("records", "research")` in `artifact_core._VERBATIM_PRESERVED_SEGMENTS`; pass `companion_dir`/`preset`/`role` in `project_layout.materialize_project_layout` and resolve `project_system_dir` in `uninstall_system_tree`.
  - Depends on: E-02
  - Expected outcome: first-record creation in companion/`~/.aw/` repos never falls back to target `.agents/`; `git_mv` stages renames cleanly in both `home` local-git and custom companion repos while refusing escapes; external research files preserve verbatim formatting; `project_layout` honors custom companion dirs and clean-delta system roots.
  - Execution state: pending

### Task group 5: Behavioral verification

- [ ] E-06 Add behavioral tests covering all fixes in `tests/test_companion_containment_and_storage.py`, `tests/test_home_isolation.py`, and `tests/test_placement_switch_companion_execute.py`, then run `python3 -m pytest` on those suites plus `mypy` on all 8 modified modules and `aw sanitize`.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: all new and existing behavioral tests pass, `mypy` reports zero errors on modified modules, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Never write code-pinning source inspection tests (`inspect`, `ast`, regex over production source).
- Run pytest bare (`python3 -m pytest <targets>` without `-n0`, `-q`, or `-p no:randomly`).
- Commit via `aw commit ywl7uc -- <paths>` inside an isolated worktree.

## Findings

All 14 bugs traced from `/assess-bugs` run `20261124-213000`:
- `BUG-01` (`storage.py`): `move_companion`/`detach_companion`/`attach_companion`/`reattach_companion` leave stale `local.json:companion_dir`.
- `BUG-02` (`project_context.py`, `config.py`, `project_registry.py`): split-brain `AW_HOME` under `XDG_CONFIG_HOME` and `$VAR`.
- `BUG-03` (`placement_switch.py`): `_perform_rollback` deletes pre-existing `companion_identity.json` / `companion_attachment.json`.
- `BUG-04` (`placement_switch.py`): `_run_records_transaction` deletes tracked `.aw/.gitignore` on rollback and stages `repository-untracked` records.
- `BUG-05` (`record_placement.py`): `resolve_type_dir` falls back to `<target>/.agents/` before `has_stored_records_placement`.
- `BUG-06` (`artifact_core.py`): `git_mv` degrades to unstaged `shutil.move` on home local-git and custom `--dir` companions and bypasses escape guard.
- `BUG-07` (`project_context.py`): explicit/`local.json` `companion_dir` skips `_check_path_security` and non-nesting check.
- `BUG-08` (`storage.py`): companion `.gitignore` omits `records/runs/`, `records/history.jsonl`, `records/*/untracked/`, `INDEX.*`.
- `BUG-09` (`project_context.py`): `record_owner_root` checks raw `Path(path).parts` instead of `canon_path.parts`.
- `BUG-10` (`placement_switch.py`): `in-place` companion attach checks wrong `old_records_root`; `execute_records_root_switch` ignores custom `project_id`; symlink dereference in `git_owner`/`is_tracked`.
- `BUG-11` (`artifact_core.py`): `_is_verbatim_preserved` misses external `records/research`.
- `BUG-12` (`project_context.py`): `_git_index_stamp` misses linked worktree gitfiles and `_watched_context_paths` misses `~/.aw/` files.
- `BUG-13` (`project_context.py`): `local-only` preset misses `DeliveryMode.CLEAN_DELTA`.
- `BUG-14` (`project_layout.py`, `config.py`): `materialize_project_layout` drops `companion_dir`, `uninstall_system_tree` hardcodes `.aw/system`, `plan_cutovers_update` drops `aw_home`.

## Proposed changes (ordered, validatable)

1. Unify `AW_HOME` resolution and `config.plan_cutovers_update` (`E-01`).
2. Harden `project_context.py` companion security, `record_owner_root`, preset derivation, and cache invalidation (`E-02`).
3. Fix `storage.py` `local.json` sync, SHA-256 identity hash, and companion `.gitignore` (`E-03`).
4. Fix `placement_switch.py` rollbacks, `repository-untracked`, `in-place` leftovers, custom `project_id`, and symlinks (`E-04`).
5. Fix `record_placement.py`, `artifact_core.py`, and `project_layout.py` (`E-05`).
6. Add behavioral tests and validate (`E-06`).

## Deferred / out of scope (with reason)

- Installer policy alignment and clean-delta hijack live in Order 02 (`7gverp`).
  - Carrier: 7gverp
- Metadata commit locking and finalize live in Order 03 (`mmuv3v`).
  - Carrier: mmuv3v

## Scope check

- Over-scope: none; strictly limited to core storage/context/placement modules and their tests.
- Under-scope: none; covers every core storage/context/placement finding from `/assess-bugs`.

## Required tests / validation

- `python3 -m pytest tests/test_companion_containment_and_storage.py tests/test_home_isolation.py tests/test_placement_switch_companion_execute.py tests/test_placement_switch_companion_plan.py`
- `python3 -m mypy agent_workflows/project_context.py agent_workflows/config.py agent_workflows/project_registry.py agent_workflows/storage.py agent_workflows/placement_switch.py agent_workflows/record_placement.py agent_workflows/artifact_core.py agent_workflows/project_layout.py`
- `aw sanitize`

## Spec / documentation sync

N/A: enforces existing documented placement, containment, and `AW_HOME` invariants.

## Open questions

### OQ-01: Default `AW_HOME` when `XDG_CONFIG_HOME` is set

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Confirm during `/plan-review` whether to standardize on `~/.aw` (with legacy XDG detection fallback) or honor `XDG_CONFIG_HOME` consistently across `project_context`, `config`, and `project_registry`. RESOLVED 2026-11-24 by the user via /askme: Always default AW_HOME to ~/.aw, ignoring XDG_CONFIG_HOME (detect and warn if legacy project data already exists under $XDG_CONFIG_HOME/agent-workflows). No reason was given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest tests/test_home_isolation.py` proving `config.get_aw_home`, `project_context._resolve_effective_aw_home`, and `project_registry.find_project` agree under `XDG_CONFIG_HOME` and `$VAR`, and `config.plan_cutovers_update` honors explicit `aw_home` and linked worktrees.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_companion_containment_and_storage.py tests/test_home_isolation.py` proving `PathSecurityError` on nested/traversal `companion_dir`, relative-path `record_owner_root`, `Preset.LOCAL_ONLY` clean-delta derivation, and linked-worktree `_git_index_stamp`/`_watched_context_paths` cache invalidation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_companion_containment_and_storage.py` proving `move_companion`/`detach_companion`/`reattach_companion` update `local.json`, `create_companion_identity` writes hashed `git_common_dir_hash` with no raw path, and `materialize_companion_storage` ignores `records/runs/`, `records/history.jsonl`, `records/*/untracked/`, and `INDEX.*`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_placement_switch_companion_execute.py` proving `_perform_rollback` preserves `companion_identity.json`, `companion_attachment.json`, and tracked `.aw/.gitignore`, `home -> repository-untracked` stays unstaged, `in-place` leftover check and custom `project_id` pass, and tracked symlinks migrate intact.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest` output proving `record_placement.resolve_type_dir` skips `.agents/` when external placement is stored, `artifact_core.git_mv` stages moves in home local-git and custom companion repos while raising `MoveOutsideRepositoryError` on escape, external `records/research` stays verbatim, and `project_layout` honors custom companion/clean-delta roots.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste full pytest summary for `test_companion_containment_and_storage.py`, `test_home_isolation.py`, and `test_placement_switch_companion_execute.py`, `mypy` zero-error output on `project_context.py`, `config.py`, `project_registry.py`, `storage.py`, `placement_switch.py`, `record_placement.py`, `artifact_core.py`, and `project_layout.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: These eight core context/storage/placement modules form the single foundational storage layer (`AW_HOME`, `resolve_project_context`, `storage`, `placement_switch`, `record_placement`, `artifact_core.git_mv`, `project_layout`) that Orders 02-06 depend on; landing them in one Order-01 child guarantees a consistent foundation for all parallel downstream plans.

Execute after human approval (`Status: approved`). Commit only path-scoped files via `aw commit ywl7uc -- <paths>`; never push.
