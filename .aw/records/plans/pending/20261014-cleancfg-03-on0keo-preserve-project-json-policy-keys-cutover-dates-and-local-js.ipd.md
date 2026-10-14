# IPD: Preserve project.json policy keys, cutover dates, and local.json settings across aw install

- Date: 2026-10-14
- Kind: child
- Concern: `install_wizard.persist_project_policy` constructs fresh `ProjectPolicySchema` and `LocalBindingSchema` instances from only the wizard's `ProjectPolicy` fields and overwrites `project.json` and `local.json` via `os.replace` without reading existing files on disk, wiping `cutovers` (which `sync_cutovers_on_install` then re-stamps with today's install date over any hand-set or earlier-stamped cutover), `setids`, `unknown_fields` (`run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_interval_commits`, `ci_checkup_workflow`, `ci_checkup_branch`, `ci_red_exempt_sets`, `dependency_schema_cutover`), and `local.json` settings (`run_analytics_sharing`, `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, `companion_dir`), while `resolve_existing_policy`, `resolve_project_context`, and `cli._cmd_install` also drop `enabled_hosts`, `role`, `non_secret_consent`, `companion_dir`, and non-default presets on `aw install -y`.
- Scope: Preserve `cutovers`, `setids`, `unknown_fields`, and `non_secret_consent` when writing `project.json` and preserve `human_slug`, `worktree_path`, `common_dir`, `local_aliases`, `runtime_overrides`, `companion_dir`, and `unknown_fields` (`run_analytics_sharing`, `run_analytics_telemetry`) when writing `local.json` in `install_wizard.persist_project_policy` (`replace_config=False`); preserve empty-dict `cutovers`/`setids` in `ProjectPolicySchema.to_dict`; preserve `enabled_hosts`, `role`, `companion_dir`, `non_secret_consent`, and existing presets across `resolve_project_context`, `resolve_existing_policy`, `resolve_policy_noninteractive`, and `cli._cmd_install`; add `CHANGELOG.md` entry; and add unit + subprocess regression tests in `tests/test_reinstall_preserves_config.py`.
- Scope-Paths: agent_workflows/project_schema.py, agent_workflows/project_context.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, CHANGELOG.md, tests/test_reinstall_preserves_config.py
- Item-Dependencies: executed:p425hv
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: qyevpr
- Blocks-Release: next
- Set: cleancfg
- Order: 3
- Highest E allocated: 08
- Author: antigravity
- Id: on0keo

## Workflow history
- 2026-10-14 to-review (aw set): ready for review (from backlog qyevpr)

- 2026-10-14 draft (antigravity): created from backlog item `qyevpr`.

## Goal

Ensure re-running `aw install` (interactively or noninteractively with `-y`) and calling `install_wizard.persist_project_policy` with `replace_config=False` preserve all existing `.aw/config/project.json` policy sections (`cutovers`, `setids`, `run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_*`, `ci_red_exempt_sets`, `dependency_schema_cutover`, `non_secret_consent`, `enabled_hosts`, `role`, and existing preset) and `.aw/config/local.json` machine-local settings (`run_analytics_sharing`, `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, `companion_dir`) across both in-tree (`.aw/config/`) and home-backed (`AW_HOME/projects/<project_id>/config/`) layouts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measurement and schema round-trip preservation

- [ ] E-01 Re-measure `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:532`), `project_context.resolve_project_context` (`agent_workflows/project_context.py:1383`), `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`), `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`), `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:920`), and `cli._cmd_install` (`agent_workflows/cli.py:8295`) at execution `HEAD`, and run the baseline reproduction probe showing `persist_project_policy` wiping `cutovers.spec_id6`, `run`, `setids`, `release_gate_work_kinds`, `enabled_hosts`, `run_analytics_sharing`, and `runtime_overrides`.
  - Depends on: none
  - Expected outcome: Current line offsets and baseline reproduction output (before/after `project.json` and `local.json` payloads) are verified at execution `HEAD` and recorded in `V-01`.
  - Execution state: pending

- [ ] E-02 Update `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:532`) to test `if self.cutovers is not None:` and `if self.setids is not None:` rather than truthiness (`if self.cutovers:` / `if self.setids:`) so explicit empty dictionaries (`"cutovers": {}`, `"setids": {}`) round-trip through `parse_portable_policy` and `to_dict()` without being dropped while `None` continues to omit the key.
  - Depends on: E-01
  - Expected outcome: `ProjectPolicySchema.to_dict()` preserves `cutovers={}` and `setids={}` when explicitly present as empty dicts and omits `cutovers`/`setids` when `None`.
  - Execution state: pending

### Task group 2: Merge existing `project.json` and `local.json` in `persist_project_policy`

- [ ] E-03 Update `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:920`) so that when `replace_config` is `False` (the default) and `proj_json` already exists on disk, it reads and parses the existing file via `parse_portable_policy` (with a fallback extracting `cutovers`, `setids`, `non_secret_consent`, and non-forbidden, non-path-leaking top-level keys when a pre-wizard partial `project.json` lacks required wizard fields) and carries existing `cutovers`, `setids`, `unknown_fields`, and merged `non_secret_consent` (`{**existing_consent, **policy.non_secret_consent}`) into the `ProjectPolicySchema` written to `proj_json` before `_config.sync_cutovers_on_install` runs; when `replace_config=True`, write a fresh `ProjectPolicySchema` without merging prior policy keys.
  - Depends on: E-02
  - Expected outcome: Calling `persist_project_policy(repo_path, policy)` on a repository with existing `project.json` preserves `cutovers` (including earlier or hand-set dates such as `cutovers.spec_id6 = "2020-01-01"` so `sync_cutovers_on_install` only fills missing feature keys), `setids`, `unknown_fields` (`run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_*`, `ci_red_exempt_sets`, `dependency_schema_cutover`, and custom keys), and existing `non_secret_consent` entries, while `persist_project_policy(..., replace_config=True)` resets `project.json` to the fresh wizard schema plus newly synced cutovers.
  - Execution state: pending

- [ ] E-04 Update `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:969`) so that when `replace_config` is `False` and `local_json` already exists on disk, it reads and parses the existing file via `parse_local_binding` (with a raw-dict fallback if `project_id` was absent) and carries existing `human_slug`, `worktree_path`, `common_dir`, `local_aliases`, `runtime_overrides`, `unknown_fields` (`run_analytics_sharing`, `run_analytics_telemetry`, and custom local keys), and `companion_dir` (when `policy.records_backend == RecordsBackend.COMPANION.value` and `policy.companion_dir is None`) into the `LocalBindingSchema` written to `local_json`.
  - Depends on: E-03
  - Expected outcome: Calling `persist_project_policy(repo_path, policy)` on a repository with existing `local.json` preserves `run_analytics_sharing` (written by `run_analytics_wizard.write_settings`), `runtime_overrides` (including `runtime_overrides.run_analytics_telemetry`), `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, and `companion_dir`.
  - Execution state: pending

### Task group 3: Preserve existing wizard policy attributes across `resolve_existing_policy`, `resolve_policy_noninteractive`, and `aw install -y`

- [ ] E-05 Update `project_context.resolve_project_context` (`agent_workflows/project_context.py:1383`) so `resolved_hosts` falls back from explicit `enabled_hosts` to `merged_local_binding.get("enabled_hosts")`, then `project_policy_data.get("enabled_hosts")`, then `DEFAULT_ENABLED_HOSTS`; and update `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`) and `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`) so `resolve_existing_policy` reads `role=getattr(ctx, "project_role", ProjectRole.TARGET.value)`, `companion_dir` (from `ctx.companion_repo` or existing `local.json`), `enabled_hosts=list(ctx.enabled_hosts)`, and `non_secret_consent` (from existing `project.json`), and `resolve_policy_noninteractive` preserves `role` and `non_secret_consent` from `existing_policy`, normalizes `explicit_preset` via `normalize_preset`, and refreshes preset defaults (`delivery_mode`, `records_backend`, `durability_state`, `placements`, `git_policies`) when `explicit_preset` changes the preset.
  - Depends on: E-04
  - Expected outcome: `resolve_existing_policy` and `resolve_policy_noninteractive` accurately round-trip `role`, `enabled_hosts`, `companion_dir`, and `non_secret_consent` from existing config files, and passing an explicit `--preset` on reinstall updates `delivery_mode`, `records_backend`, `durability_state`, `placements`, and `git_policies` coherently for the new preset (including short aliases like `clean-target` and `public-private-companion`).
  - Execution state: pending

- [ ] E-06 Update `cli._cmd_install` (`agent_workflows/cli.py:8295`) to resolve `existing_policy = resolve_existing_policy(str(repo_root))` before applying the `-y` fallback to `Preset.PRIVATE_TARGET.value`, so `explicit_preset` defaults to `Preset.PRIVATE_TARGET.value` only on a first install (`existing_policy is None`) when neither `--preset`, `--delivery-mode`, nor `--records-backend` was passed, and pass `existing_policy=existing_policy` into `collect_policy_interactive`.
  - Depends on: E-05
  - Expected outcome: Re-running `aw install <repo> -y --no-interactive` without `--preset` on an already-configured repository preserves its existing preset (`local-only`, `completely-clean-target`, `public-target-private-companion`, or `private-target`) instead of forcing `private-target`, while a first-time `aw install <repo> -y` on an unconfigured repository still defaults to `private-target`.
  - Execution state: pending

### Task group 4: Documentation sync, regression test suite, and mutation proof

- [ ] E-07 Add a `### Fixed` entry under `"## [Unreleased]"` in `CHANGELOG.md` (`CHANGELOG.md:8`) describing the preservation of `.aw/config/project.json` policy sections, cutover dates, existing presets/hosts/roles, and `.aw/config/local.json` machine-local settings across `aw install`, using zero em or en dashes.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: `CHANGELOG.md` documents the fix under `## [Unreleased]` with zero em or en dashes.
  - Execution state: pending

- [ ] E-08 Create `tests/test_reinstall_preserves_config.py` with unit and subprocess `aw install` tests covering `project.json` preservation (`cutovers` with earlier hand-set dates, `run`, `setids` non-empty and empty `{}`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_red_exempt_sets`, `non_secret_consent`, `role`, `enabled_hosts`), `local.json` preservation (`run_analytics_sharing` via `run_analytics_wizard.write_settings`, `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, `companion_dir`), `aw install <repo> -y --no-interactive` without `--preset` on both tracked (`private-target`) and home-backed (`local-only`) repositories, explicit `--preset` switching on reinstall without losing policy keys, and `replace_config=True` reset behavior; perform a one-line mutation proof; and run the full test suite (`python3 -m pytest`) and `aw sanitize --agent`.
  - Depends on: E-06, E-07
  - Expected outcome: `python3 -m pytest tests/test_reinstall_preserves_config.py tests/test_install_consent_truth.py` passes, a temporary one-line mutation in `install_wizard.persist_project_policy` fails the new regression test and passes when restored, `python3 -m pytest` passes across the repository, and `aw sanitize --agent` exits `0`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Never work or edit directly on `main`; all implementation and test runs take place in an isolated lane worktree and commit through `aw commit <plan> -- <paths>` (see `AGENTS.md` `"USE THE TOOLED COMMIT PATH"`).
- Write no em or en dashes in user-facing prose (`CHANGELOG.md`, CLI output, wizard text); use plain hyphens, colons, or parentheses (`GEMINI.md` Rule 3).
- Run the test suite via bare `python3 -m pytest` without `-n0`, extra `-q`, or `-p no:randomly` (`GEMINI.md` Rule 5).
- Test observable outcomes and CLI/subprocess behavior, never code structure via `inspect`, `ast`, or regex over source files (`GEMINI.md` Rule 6).
- `project_context.py` must remain pure and side-effect-free (`agent_workflows/project_context.py:6`: `"Invariants: - PURE: ZERO filesystem writes, directory creation, or Git mutation."`).
- Preserve existing `state_durable` upgrade normalization in `cli._cmd_install` (`agent_workflows/cli.py:8376` and `test_install_consent_truth.TestInstallConsentTruth.test_upgrade_normalization_announcement_and_no_repeat`, `tests/test_install_consent_truth.py:228`), which relies on `ProjectPolicy.__post_init__` deriving canonical `placements` and `git_policies` from `get_preset_defaults(preset)`.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:952`) | `persist_project_policy` constructs a brand-new `ProjectPolicySchema` with only the 9 wizard fields (`schema_version`, `preset`, `role`, `placements`, `git_policies`, `enabled_hosts`, `non_secret_consent`, `delivery_mode`, `records_backend`) and overwrites `proj_json` via `os.replace`, ignoring `replace_config: bool = False`. Every existing `cutovers` entry, `setids` map, and `unknown_fields` key (`run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_interval_commits`, `ci_checkup_workflow`, `ci_checkup_branch`, `ci_red_exempt_sets`, `dependency_schema_cutover`) is discarded. Immediately afterward (`install_wizard.persist_project_policy`, `agent_workflows/install_wizard.py:983`), `_config.sync_cutovers_on_install(repo_path, aw_home=policy.aw_home)` sees no `cutovers` map in `project.json` and stamps `now_iso` (or install-history date) over every hand-set or previously stamped cutover date (verified in reproduction probe: `cutovers.spec_id6: "2020-01-01"` was overwritten with `"2026-10-14"`). |
| F-02 | High | `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:969`) | `persist_project_policy` constructs a fresh `LocalBindingSchema(schema_version=2, project_id=ctx.project_id, companion_dir=policy.companion_dir)` and overwrites `local_json` via `os.replace` without reading the existing `local.json`. This wipes `unknown_fields` (specifically `run_analytics_sharing` written by `run_analytics_wizard.write_settings` at `agent_workflows/run_analytics_wizard.py:183` and top-level `run_analytics_telemetry`), `runtime_overrides` (such as `runtime_overrides.run_analytics_telemetry`), `local_aliases`, `human_slug`, `worktree_path`, and `common_dir`. |
| F-03 | Medium | `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:546`) | `ProjectPolicySchema.to_dict` checks `if self.cutovers:` and `if self.setids:` using truthiness instead of `is not None`, so an explicit empty dictionary (`"cutovers": {}` or `"setids": {}`) parsed by `parse_portable_policy` is silently dropped on serialization. |
| F-04 | Medium | `project_context.resolve_project_context` (`agent_workflows/project_context.py:1383`), `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`), and `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`) | (1) `resolve_project_context` sets `resolved_hosts = enabled_hosts if enabled_hosts is not None else DEFAULT_ENABLED_HOSTS`, ignoring `project_policy_data.get("enabled_hosts")` and `merged_local_binding.get("enabled_hosts")`, so `resolve_existing_policy` resets `enabled_hosts` to `["opencode", "claude", "antigravity"]` on reinstall. (2) `resolve_existing_policy` reads `getattr(ctx, "role", ...)` and `getattr(ctx, "companion_dir", None)`, whereas `project_schema.ProjectContext` defines `project_role` and `companion_repo` (`agent_workflows/project_schema.py:810`), and `resolve_policy_noninteractive` fails to forward `role` or `non_secret_consent` from `existing_policy` or normalize/refresh preset defaults when `explicit_preset` is passed on reinstall. |
| F-05 | Medium | `cli._cmd_install` (`agent_workflows/cli.py:8295`) | When `aw install <repo> -y` is invoked without `--preset` or `--delivery-mode`, `cli._cmd_install` unconditionally sets `explicit_preset = Preset.PRIVATE_TARGET.value` before `collect_policy_interactive` resolves `existing_policy`. On a repository already configured with `local-only`, `completely-clean-target`, or `public-target-private-companion`, `aw install <repo> -y` overwrites its preset with `private-target`. |

## Proposed changes (ordered, validatable)

1. **Task group 1 (`E-01`, `E-02`) — Re-measurement and `project_schema.ProjectPolicySchema.to_dict` empty-dict preservation (`agent_workflows/project_schema.py`)**:
   - In `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:546`), change `if self.cutovers:` to `if self.cutovers is not None:` and `if self.setids:` to `if self.setids is not None:`.

2. **Task group 2 (`E-03`, `E-04`) — Read-modify-write merge in `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py`)**:
   - In `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:920`), when `not replace_config` and `proj_json.is_file()`:
     - Read raw JSON from `proj_json`. If it is a `dict`, attempt `existing_proj = parse_portable_policy(raw_proj)`.
     - If `parse_portable_policy` raises `SchemaValidationError` (for example, on a partial `project.json` created before the wizard ran), extract `cutovers` (when `isinstance(raw_proj.get("cutovers"), dict)`), `setids` (when `isinstance(raw_proj.get("setids"), dict)`), `non_secret_consent` (when `isinstance(raw_proj.get("non_secret_consent"), dict)`), and `unknown_fields` (keys in `raw_proj` not in `ProjectPolicySchema` known keys, not in `FORBIDDEN_PORTABLE_KEYS`, and passing `_check_no_path_leaks`).
     - Merge `non_secret_consent = {**(existing_consent or {}), **(policy.non_secret_consent or {})}` and populate `cutovers`, `setids`, and `unknown_fields` on `proj_schema` before writing `proj_json` and calling `_config.sync_cutovers_on_install(repo_path, aw_home=policy.aw_home)`.
   - When `not replace_config` and `local_json.is_file()`:
     - Read raw JSON from `local_json`. If it is a `dict`, parse via `parse_local_binding(raw_local)` (falling back to raw dict extraction if `project_id` was missing).
     - Carry `human_slug`, `worktree_path`, `common_dir`, `local_aliases`, `runtime_overrides`, `unknown_fields`, and `companion_dir` (`policy.companion_dir if policy.companion_dir is not None else (existing_local.companion_dir if policy.records_backend == RecordsBackend.COMPANION.value else None)`) into `local_schema` before writing `local_json`.

3. **Task group 3 (`E-05`, `E-06`) — Round-trip existing policy in `resolve_project_context`, `resolve_existing_policy`, `resolve_policy_noninteractive`, and `cli._cmd_install` (`agent_workflows/project_context.py`, `agent_workflows/install_wizard.py`, `agent_workflows/cli.py`)**:
   - In `project_context.resolve_project_context` (`agent_workflows/project_context.py:1383`), resolve `enabled_hosts` by checking `enabled_hosts` argument first, then `merged_local_binding.get("enabled_hosts")` (if a list of strings), then `project_policy_data.get("enabled_hosts")` (if a list of strings), and finally `DEFAULT_ENABLED_HOSTS`.
   - In `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`), read `role=getattr(ctx, "project_role", ProjectRole.TARGET.value)`, `companion_dir=getattr(ctx, "companion_repo", None) or local_data.get("companion_dir")`, `enabled_hosts=list(getattr(ctx, "enabled_hosts", ["opencode", "claude", "antigravity"]))`, and `non_secret_consent=dict(proj_data.get("non_secret_consent") or {})` (when `proj_json.is_file()`).
   - In `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`), when `existing_policy is not None`:
     - Normalize `explicit_preset` via `normalize_preset(explicit_preset)` when provided.
     - If `explicit_preset` is provided and differs from `existing_policy.preset`, derive `pls, gps, dm, rb, ds = get_preset_defaults(preset)` and use `explicit_delivery or dm`, `explicit_backend or rb`, and `ds`; otherwise keep `existing_policy.delivery_mode`, `existing_policy.records_backend`, and `existing_policy.durability_state` (overridden by `explicit_delivery` / `explicit_backend` when passed).
     - Carry `role=existing_policy.role` and `non_secret_consent=dict(existing_policy.non_secret_consent)` into the returned `ProjectPolicy`.
   - In `cli._cmd_install` (`agent_workflows/cli.py:8295`), import `resolve_existing_policy`, compute `existing_policy = resolve_existing_policy(str(repo_root))`, default `explicit_preset = Preset.PRIVATE_TARGET.value` only when `existing_policy is None and getattr(args, "yes", False) and not explicit_preset and not getattr(args, "delivery_mode", None) and not getattr(args, "records_backend", None)`, and pass `existing_policy=existing_policy` to `collect_policy_interactive`.

4. **Task group 4 (`E-07`, `E-08`) — `CHANGELOG.md` and regression test suite (`CHANGELOG.md`, `tests/test_reinstall_preserves_config.py`)**:
   - Add a `### Fixed` bullet under `"## [Unreleased]"` in `CHANGELOG.md` (`CHANGELOG.md:8`) with zero em or en dashes.
   - Create `tests/test_reinstall_preserves_config.py` testing `ProjectPolicySchema.to_dict`, `persist_project_policy` (`replace_config=False` vs `replace_config=True`), `resolve_existing_policy`, `resolve_policy_noninteractive`, and end-to-end subprocess `aw install` runs across `private-target` and `local-only` presets; perform the one-line mutation proof; and run `python3 -m pytest` and `aw sanitize --agent`.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none. Every E-item directly serves backlog `qyevpr` (stopping `aw install` and `persist_project_policy` from clobbering `.aw/config/project.json` policy sections, cutover dates, and `.aw/config/local.json` machine-local settings across reinstalls).
- Under-scope: none. Both the direct API surface (`persist_project_policy`, `resolve_existing_policy`, `resolve_policy_noninteractive`, `ProjectPolicySchema.to_dict`, `resolve_project_context`) and the CLI entrypoint (`cli._cmd_install` with `aw install -y`) are covered across both in-tree and `AW_HOME`-backed config placements.

## Required tests / validation

- Unit tests in `tests/test_reinstall_preserves_config.py` verifying:
  - `ProjectPolicySchema.to_dict()` preserves empty dicts (`cutovers={}`, `setids={}`) and omits `None`.
  - `persist_project_policy` (`replace_config=False`) preserves `cutovers` (including earlier dates like `"2020-01-01"` while still filling any missing `KNOWN_FEATURE_CUTOVERS` keys via `sync_cutovers_on_install`), `run`, `setids`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_red_exempt_sets`, `dependency_schema_cutover`, and `non_secret_consent` in `project.json`, as well as `run_analytics_sharing` (`run_analytics_wizard.write_settings`), `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, and `companion_dir` in `local.json`.
  - `persist_project_policy` on a pre-wizard partial `project.json` (containing only `{"cutovers": {"spec_id6": "2020-01-01"}, "run": {"retry_budget": 4}}`) preserves both keys when upgrading to the full v2 `ProjectPolicySchema`.
  - `persist_project_policy(..., replace_config=True)` discards prior `unknown_fields` and `setids` when an explicit reset is requested.
- Subprocess CLI integration tests in `tests/test_reinstall_preserves_config.py` running `python3 -m agent_workflows.cli install <repo> -y --no-interactive`:
  - On a `private-target` repo with customized `.aw/config/project.json` (`cutovers.spec_id6 = "2020-01-01"`, `run = {"retry_budget": 2}`, `setids = {"warn_length": 10}`, `release_gate_work_kinds = ["bug", "security"]`, `enabled_hosts = ["opencode"]`, `role = "companion"`, `non_secret_consent = {"telemetry_prompted": True}`) and customized `.aw/config/local.json` (`run_analytics_sharing`, `runtime_overrides`), asserting every field is identical after reinstall.
  - On a `local-only` repo (config stored under `<aw_home>/projects/<project_id>/config/`) re-running `aw install <repo> -y --no-interactive` without `--preset`, asserting `preset == "local-only"` and all custom `project.json` and `local.json` keys under `AW_HOME` are preserved.
  - On a `private-target` repo re-running `aw install <repo> --preset local-only -y --no-interactive`, asserting the preset updates to `local-only` while preserving custom policy keys and cutover dates.
- Mutation proof: temporarily comment out the existing-config merge in `install_wizard.persist_project_policy`, run `python3 -m pytest tests/test_reinstall_preserves_config.py` to observe test failure, restore the code, and re-run `python3 -m pytest`.

## Spec / documentation sync

- Add a `### Fixed` entry under `"## [Unreleased]"` in `CHANGELOG.md` (`CHANGELOG.md:8`) with zero em or en dashes. No spec amendment is required because `.aw/records/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 9.1 and `project_schema.parse_portable_policy` / `parse_local_binding` already specify forward-compatible `unknown_fields`, `cutovers`, and `setids` preservation.

## Open questions

### OQ-01: Should `persist_project_policy` preserve existing `cutovers`, `setids`, and `unknown_fields` when `project.json` was partially populated before the install wizard first ran (for example by `sync_cutovers_on_install` or manual edits lacking `preset` / `placements`)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence in `config.sync_cutovers_on_install` (`agent_workflows/config.py:1518`), which writes `{"cutovers": ...}` directly to `project.json` even if wizard fields are absent, and `project_schema.parse_portable_policy` (`agent_workflows/project_schema.py:555`), which raises `SchemaValidationError` if `preset` or `placements` is missing. Falling back to extracting `cutovers`, `setids`, `non_secret_consent`, and non-forbidden, non-path-leaking unknown keys from the raw dict when `parse_portable_policy` raises `SchemaValidationError` ensures pre-existing cutovers and policy keys are never lost while the newly written `ProjectPolicySchema` is still a complete, valid v2 document (`E-03`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted command output from the pre-edit re-measurement at execution `HEAD` showing the line offsets of `ProjectPolicySchema.to_dict`, `resolve_project_context`, `resolve_existing_policy`, `resolve_policy_noninteractive`, `persist_project_policy`, and `cli._cmd_install` together with the baseline reproduction output demonstrating `project.json` and `local.json` clobbering.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/project_schema.py` and pasted Python one-liner output showing `parse_portable_policy( data ).to_dict()` preserving `"cutovers": {}` and `"setids": {}` when set to empty dicts and omitting them when `None`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/install_wizard.py` for `persist_project_policy`'s `project.json` handling and pasted Python probe output showing `persist_project_policy` preserving `cutovers` (including `"spec_id6": "2020-01-01"`), `setids`, `run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, and `non_secret_consent` on both a full v2 `project.json` and a partial pre-wizard `project.json`, and resetting them when `replace_config=True`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff -- agent_workflows/install_wizard.py` for `persist_project_policy`'s `local.json` handling and pasted Python probe output showing `persist_project_policy` preserving `run_analytics_sharing` (written by `run_analytics_wizard.write_settings`), `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, and `companion_dir` in `local.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff -- agent_workflows/project_context.py agent_workflows/install_wizard.py` and pasted Python probe output showing `resolve_existing_policy` and `resolve_policy_noninteractive` preserving `enabled_hosts=["opencode"]`, `role="companion"`, `companion_dir`, and `non_secret_consent` from disk, and normalizing/updating preset defaults when `explicit_preset="clean-target"` or `explicit_preset="local-only"` is passed on reinstall.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` and pasted subprocess output (reachable via `cli._cmd_install` -> `collect_policy_interactive` -> `resolve_policy_noninteractive` -> `persist_project_policy` updated in `E-03`..`E-06`) from running `python3 -m agent_workflows.cli install <repo> -y --no-interactive` without `--preset` on a `local-only` repository and on a `private-target` repository, confirming the existing preset and all `project.json` / `local.json` policy keys and cutover dates remain intact.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted `git diff -- CHANGELOG.md` and pasted output of a Python check confirming zero em or en dashes (`\u2014`, `\u2013`) in the added `CHANGELOG.md` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Pasted output of `python3 -m pytest tests/test_reinstall_preserves_config.py` failing under the temporary one-line mutation in `install_wizard.persist_project_policy` and passing after restoration, followed by pasted output of the full test suite (`python3 -m pytest`) and `AW_NO_REEXEC=1 python3 -m agent_workflows.cli sanitize --agent` exiting `0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ready for review (`- Status: to-review`). Do not execute until `- Status: approved`. Upon execution completion and verification of `V-01`..`V-08`, finalize the plan via `aw ipd finalize on0keo` and commit all modified paths through `aw commit on0keo -- <paths>`.
