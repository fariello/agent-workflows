# IPD: Fix installer clean-delta hijack companion project policy diff and leak allowlist bugs

- Date: 2026-11-24
- Kind: child
- Concern: Six verified installer and configuration bugs break `tracked`+`home`, `public-target-private-companion`, and `clean-delta` (`~/.aw/`) repositories: (1) `engine._clean_delta_home_trees` unconditionally enters partial-uninstall recovery whenever `<AW_HOME>/projects/<pid>/records` exists, hijacking `tracked`+`home` updates into `~/.aw/.../system` and stranding `<repo>/.aw/` on uninstall; (2) `public-target-private-companion` install leaves `.aw/config/project.json` permanently untracked and uncommitted due to a three-way policy mismatch across `install_wizard`, `project_context`, and `engine`; (3) noninteractive `aw install --preset public-target-private-companion --yes` without `--companion-dir` skips companion git init and attachment; (4) `engine.migrate_local_lanes_to_untracked` crashes with `ValueError` on external `records/` trees; (5) `aw install --diff` ignores external `system`/`records` destinations and clean-delta exclusions; and (6) `leak_sanitizer.resolve_allowlist_path` hardcodes `<repo>/.aw/config/local-leaks-allowlist.toml` instead of `project_config_dir`, dirtying `clean-delta` target repos.
- Scope: Fix all six installer, wizard, and leak-allowlist bugs in `engine.py`, `install_wizard.py`, `cli.py`, `project_context.py`, and `leak_sanitizer.py`, with end-to-end behavioral tests across `tracked`+`home`, `public-target-private-companion`, and `clean-delta`.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, agent_workflows/project_context.py, agent_workflows/leak_sanitizer.py, tests/test_home_isolation.py, tests/test_companion_containment_and_storage.py, tests/test_leak_sanitizer.py, .aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md
- Item-Dependencies: executed:ywl7uc
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 2
- Highest E allocated: 5
- Id: 7gverp
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 02 child IPD for `/assess-bugs` (Set `comphome`).

## Goal

Ensure `aw install`, `aw install --diff`, `aw uninstall`, and `aw sanitize --configure` preserve exact target-repo and `~/.aw/` footprints across `tracked`+`home`, `public-target-private-companion`, and `clean-delta` modes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Installer home-tree recovery, local-lane migration, and `--diff`

- [ ] E-01 Fix `engine._clean_delta_home_trees`, `engine.migrate_local_lanes_to_untracked`, and `aw install --diff` (`engine.run`, `engine.show_install_diffs`): skip partial clean-delta recovery in `_clean_delta_home_trees` when an in-tree tracked policy exists in `<repo>/.aw/config/project.json` (and do not treat a `records/`-only home directory as a clean-delta system tree); guard `new.relative_to(repo_root)` with `try/except ValueError` in `migrate_local_lanes_to_untracked`; route destination paths in `run()` and `show_install_diffs()` through `_system_member_destination` and `_records_member_destination` while honoring clean-delta exclusions.
  - Depends on: none
  - Expected outcome: `tracked`+`home` update and uninstall keep `.aw/system/` in the target repo; legacy `prompts/local/` migration succeeds on companion or `home` records; `aw install --diff` on an up-to-date companion, `home`, or `clean-delta` install reports zero spurious new files.
  - Execution state: pending

### Task group 2: Companion preset policy consistency and noninteractive attachment

- [ ] E-02 Reconcile `public-target-private-companion` `config_project` policy across `install_wizard.get_preset_defaults`, `project_context._resolve_project_context_uncached`, and `engine.stage_tracked_policy_files` / `_AW_GITIGNORE_TEMPLATE` so fresh installs leave zero untracked/unignored `.aw/config/project.json` in the target repo.
  - Depends on: E-01
  - Expected outcome: `aw install --preset public-target-private-companion --companion-dir ../repo.aw --yes` completes with a clean target `git status` and consistent `config_project` policy across `install_wizard`, `project_context`, and `.aw/.gitignore`.
  - Execution state: pending

- [ ] E-03 Fix noninteractive companion initialization in `install_wizard.resolve_policy_noninteractive` and `cli._run_install`: when `--preset public-target-private-companion` (or `records_backend="companion"`) is passed without `--companion-dir`, default `companion_dir` to `<anchor>.aw` (matching `project_context`'s sibling convention) so companion `git init`, `storage.attach_companion`, `.aw/companion_identity.json`, and companion `.gitignore` always run.
  - Depends on: E-02
  - Expected outcome: `aw install --preset public-target-private-companion --yes` (without `--companion-dir`) initializes and attaches `<repo>.aw` as a versioned companion repository.
  - Execution state: pending

### Task group 3: Leak allowlist path under `clean-delta` / `~/.aw/`

- [ ] E-04 Route `leak_sanitizer.resolve_allowlist_path` and `write_repo_allowlist` through `project_context.project_config_dir(repo_root) / "local-leaks-allowlist.toml"` (preserving `.agents/local-leaks-allowlist.toml` legacy fallback).
  - Depends on: none
  - Expected outcome: `aw sanitize --configure` writes to `<AW_HOME>/projects/<pid>/config/local-leaks-allowlist.toml` in `clean-delta` mode with zero target-repo dirtiness, and `aw sanitize` reads allowlists stored there.
  - Execution state: pending

### Task group 4: Behavioral verification

- [ ] E-05 Add behavioral tests for all six fixes across `tests/test_home_isolation.py`, `tests/test_companion_containment_and_storage.py`, and `tests/test_leak_sanitizer.py`, then run pytest, `mypy`, and `aw sanitize`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: all targeted pytest suites pass, `mypy` is clean on modified files, and `aw sanitize` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run bare `python3 -m pytest <targets>` (no `-n0`, `-q`, or `-p no:randomly`); write observable behavioral tests only.
- Commit path-scoped via `aw commit 7gverp -- <paths>` in an isolated worktree.

## Findings

Six verified bugs from `/assess-bugs` run `20261124-213000`:
- Blocker: `engine._clean_delta_home_trees` hijacks `tracked`+`home` installs and uninstalls.
- High: `public-target-private-companion` install leaves `.aw/config/project.json` untracked/unignored/uncommitted.
- Medium: `engine.migrate_local_lanes_to_untracked` crashes with `ValueError` on external records.
- Medium: noninteractive `--preset public-target-private-companion --yes` without `--companion-dir` skips companion init/attachment.
- Medium: `aw install --diff` ignores external `system`/`records` roots and clean-delta exclusions.
- Medium: `leak_sanitizer.resolve_allowlist_path` ignores `project_config_dir` and dirties `clean-delta` target repos.

## Proposed changes (ordered, validatable)

1. Guard `_clean_delta_home_trees`, fix `migrate_local_lanes_to_untracked`, and align `aw install --diff` (`E-01`).
2. Align `public-target-private-companion` `config_project` policy (`E-02`) and default sibling `companion_dir` in noninteractive installs (`E-03`).
3. Route `leak_sanitizer.resolve_allowlist_path` through `project_config_dir` (`E-04`).
4. Add behavioral tests and run pytest, mypy, and sanitize (`E-05`).

## Deferred / out of scope (with reason)

- Companion `.gitignore` expansion is owned by Order 01 (`ywl7uc`).
  - Carrier: ywl7uc

## Scope check

- Over-scope: none.
- Under-scope: none; all installer and allowlist bugs from `/assess-bugs` are covered.

## Required tests / validation

- `python3 -m pytest tests/test_home_isolation.py tests/test_companion_containment_and_storage.py tests/test_leak_sanitizer.py`
- `python3 -m mypy agent_workflows/engine.py agent_workflows/install_wizard.py agent_workflows/cli.py agent_workflows/project_context.py agent_workflows/leak_sanitizer.py`
- `aw sanitize`

## Spec / documentation sync

Update `public-target-private-companion` policy documentation if `config_project` tracking policy changes in `E-02`.

## Open questions

### OQ-01: `config_project` policy for `public-target-private-companion`

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Confirm during `/plan-review` whether `.aw/config/project.json` in `public-target-private-companion` should be `target-git` (staged/committed on install) or ignored/stored in the companion repo.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste pytest output proving `tracked`+`home` update/uninstall keeps `.aw/system/` in repo, `migrate_local_lanes_to_untracked` succeeds on external records, and `aw install --diff` reports no spurious changes on an up-to-date companion/clean-delta install.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste pytest output proving a fresh `public-target-private-companion` install leaves target `git status --porcelain` clean regarding `.aw/config/project.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste pytest output proving `aw install --preset public-target-private-companion --yes` (omitting `--companion-dir`) creates `<repo>.aw/.git`, `.aw/companion_identity.json`, and attachment metadata.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_leak_sanitizer.py` output proving `aw sanitize --configure` writes to `<AW_HOME>/projects/<pid>/config/local-leaks-allowlist.toml` without creating `.aw/` in a `clean-delta` target repo.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste full pytest summary for `test_home_isolation.py`, `test_companion_containment_and_storage.py`, and `test_leak_sanitizer.py`, `mypy` zero-error output on `engine.py`, `install_wizard.py`, `cli.py`, `project_context.py`, and `leak_sanitizer.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after human approval (`Status: approved`) and after `executed:ywl7uc`. Commit only path-scoped files via `aw commit 7gverp -- <paths>`; never push.
