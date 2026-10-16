# IPD: Preserve project.json policy keys, cutover dates, and local.json settings across aw install

- Date: 2026-10-14
- Kind: child
- Concern: `install_wizard.persist_project_policy` constructs fresh `ProjectPolicySchema` and `LocalBindingSchema` instances from only the wizard's `ProjectPolicy` fields and overwrites `project.json` and `local.json` via `os.replace` without reading existing files on disk, wiping `cutovers` (which `sync_cutovers_on_install` then re-stamps with today's install date over any hand-set or earlier-stamped cutover), `setids`, `unknown_fields` (`run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_interval_commits`, `ci_checkup_workflow`, `ci_checkup_branch`, `ci_red_exempt_sets`, `dependency_schema_cutover`), and `local.json` settings (`run_analytics_sharing`, `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, `companion_dir`), while `resolve_existing_policy`, `resolve_project_context`, and `cli._run_install` also drop `enabled_hosts`, `role`, `non_secret_consent`, `companion_dir`, and non-default presets on `aw install -y`.
- Scope: Preserve `cutovers`, `setids`, `unknown_fields`, and `non_secret_consent` when writing `project.json` and preserve `human_slug`, `worktree_path`, `common_dir`, `local_aliases`, `runtime_overrides`, `companion_dir`, and `unknown_fields` (`run_analytics_sharing`, `run_analytics_telemetry`) when writing `local.json` in `install_wizard.persist_project_policy` (`replace_config=False`); preserve empty-dict `cutovers`/`setids` in `ProjectPolicySchema.to_dict`; preserve `enabled_hosts`, `role`, `companion_dir`, `non_secret_consent`, and existing presets across `resolve_project_context`, `resolve_existing_policy`, `resolve_policy_noninteractive`, and `cli._run_install`; refuse a reinstall preset switch that would move config between the target and `AW_HOME` (relocation deferred to backlog `ui1aln`); add `CHANGELOG.md` entry; and add unit + subprocess regression tests in `tests/test_reinstall_preserves_config.py`.
- Scope-Paths: agent_workflows/project_schema.py, agent_workflows/project_context.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, CHANGELOG.md, tests/test_reinstall_preserves_config.py
- Item-Dependencies: executed:p425hv
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: qyevpr
- Blocks-Release: next
- Set: cleancfg
- Order: 3
- Highest E allocated: 09
- Author: antigravity
- Id: on0keo

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: on0keo verified (set cleancfg, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010; new backlog ui1aln carries cross-placement relocation
- 2026-10-14 to-review (aw set): ready for review (from backlog qyevpr)

- 2026-10-14 draft (antigravity): created from backlog item `qyevpr`.

## Goal

Ensure re-running `aw install` (interactively or noninteractively with `-y`) and calling `install_wizard.persist_project_policy` with `replace_config=False` preserve all existing `.aw/config/project.json` policy sections (`cutovers`, `setids`, `run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_*`, `ci_red_exempt_sets`, `dependency_schema_cutover`, `non_secret_consent`, `enabled_hosts`, `role`, and existing preset) and `.aw/config/local.json` machine-local settings (`run_analytics_sharing`, `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, `companion_dir`) across both in-tree (`.aw/config/`) and home-backed (`AW_HOME/projects/<project_id>/config/`) layouts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measurement and schema round-trip preservation

- [x] E-01 Re-measure `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:532`), `project_context.resolve_project_context` (`resolved_hosts = (`, `agent_workflows/project_context.py:1383`), `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`), `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`), `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:920`), and the `-y` preset default inside `cli._run_install` (`explicit_preset = Preset.PRIVATE_TARGET.value`, `agent_workflows/cli.py:8302`) at execution `HEAD`, and run the baseline reproduction probe (scratch repo under a temp dir with `AW_HOME` and `XDG_CONFIG_HOME` pointed inside it) showing `persist_project_policy` wiping `cutovers.spec_id6`, `run`, `setids`, `release_gate_work_kinds`, `enabled_hosts`, `role`, `non_secret_consent`, `run_analytics_sharing`, and `runtime_overrides`, the alias preset `clean-target` being stored un-normalized (F-06), and a `local-only` repository reinstalled with `aw install <repo> -y --no-interactive` coming back as `private-target` (F-05).
  - Depends on: none
  - Expected outcome: Current line offsets and baseline reproduction output (before/after `project.json` and `local.json` payloads) are verified at execution `HEAD` and recorded in `V-01`.
  - Execution state: performed

- [x] E-02 Update `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:532`) to test `if self.cutovers is not None:` and `if self.setids is not None:` rather than truthiness (`if self.cutovers:` / `if self.setids:`) so explicit empty dictionaries (`"cutovers": {}`, `"setids": {}`) round-trip through `parse_portable_policy` and `to_dict()` without being dropped while `None` continues to omit the key.
  - Depends on: E-01
  - Expected outcome: `ProjectPolicySchema.to_dict()` preserves `cutovers={}` and `setids={}` when explicitly present as empty dicts and omits `cutovers`/`setids` when `None`.
  - Execution state: performed

### Task group 2: Merge existing `project.json` and `local.json` in `persist_project_policy`

- [x] E-03 Update `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:920`) so that when `replace_config` is `False` (the default) and `proj_json` already exists on disk, it reads the existing file as JSON and, when it is a `dict`, parses it via `project_schema.parse_portable_policy` and carries the parsed `cutovers`, `setids`, `unknown_fields`, and merged `non_secret_consent` (`{**existing_consent, **policy.non_secret_consent}`) into the `ProjectPolicySchema` written to `proj_json` before `_config.sync_cutovers_on_install` runs. `parse_portable_policy` already accepts a partial pre-wizard document (it defaults missing `preset`/`role`/`placements`, F-07), so no separate partial-document parser is needed. When the existing file is unreadable, not a JSON object, or `parse_portable_policy` raises `ValueError` (unknown `preset` such as a previously stored un-normalized alias, unknown `role`, or `schema_version > 2`), fall back to the raw dict: carry `cutovers` and `setids` only when each is a `dict`, `non_secret_consent` only when a `dict`, and every other top-level key not in the `ProjectPolicySchema` field set as an unknown field, so nothing a human wrote is dropped (spec `20260810-1447-01` Section 7, "unknown fields ... remain preserved"); a file that is not valid JSON at all is left to be overwritten exactly as today (no new failure mode). When `replace_config=True`, write a fresh `ProjectPolicySchema` without merging prior policy keys.
  - Depends on: E-02
  - Expected outcome: Calling `persist_project_policy(repo_path, policy)` on a repository with existing `project.json` preserves `cutovers` (including earlier or hand-set dates such as `cutovers.spec_id6 = "2020-01-01"` so `sync_cutovers_on_install` only fills missing feature keys), `setids`, `unknown_fields` (`run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_*`, `ci_red_exempt_sets`, `dependency_schema_cutover`, and custom keys), and existing `non_secret_consent` entries, while `persist_project_policy(..., replace_config=True)` resets `project.json` to the fresh wizard schema plus newly synced cutovers.
  - Execution state: performed

- [x] E-04 Update `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:969`) so that when `replace_config` is `False` and `local_json` already exists on disk, it reads and parses the existing file via `project_schema.parse_local_binding` (which tolerates a missing `project_id`; on `ValueError` for `schema_version > 2` or a non-dict payload, fall back to the raw dict exactly as E-03 does) and carries existing `human_slug`, `worktree_path`, `common_dir`, `local_aliases`, `runtime_overrides`, `unknown_fields` (`run_analytics_sharing`, `run_analytics_telemetry`, and custom local keys), and `companion_dir` (when `policy.records_backend == RecordsBackend.COMPANION.value` and `policy.companion_dir is None`) into the `LocalBindingSchema` written to `local_json`.
  - Depends on: E-03
  - Expected outcome: Calling `persist_project_policy(repo_path, policy)` on a repository with existing `local.json` preserves `run_analytics_sharing` (written by `run_analytics_wizard.write_settings`), `runtime_overrides` (including `runtime_overrides.run_analytics_telemetry`), `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, and `companion_dir`.
  - Execution state: performed

### Task group 3: Preserve existing wizard policy attributes across `resolve_existing_policy`, `resolve_policy_noninteractive`, and `aw install -y`

- [x] E-05 Update `project_context.resolve_project_context` (`resolved_hosts = (`, `agent_workflows/project_context.py:1383`) so `resolved_hosts` falls back from the explicit `enabled_hosts` argument to `merged_local_binding.get("enabled_hosts")`, then `project_policy_data.get("enabled_hosts")` (each used only when it is a `list` of `str`), then `DEFAULT_ENABLED_HOSTS`, with `provenance_map["enabled_hosts"]` naming the level actually used (`MACHINE_LOCAL_BINDING` / `PROJECT_DURABLE_CONFIG` / `BUILTIN_DEFAULTS`), mirroring the existing `resolved_role` precedence chain (`elif project_policy_data.get("role"):`, `agent_workflows/project_context.py:1072`). The resolver stays pure (no writes).
  - Depends on: E-04
  - Expected outcome: `resolve_project_context(target_repo=...)` on a repository whose `project.json` holds `enabled_hosts: ["opencode"]` returns `ctx.enabled_hosts == ["opencode"]` with `PROJECT_DURABLE_CONFIG` provenance, an explicit `enabled_hosts=` argument still wins, and a repository with no stored hosts still resolves `DEFAULT_ENABLED_HOSTS`. The existing `tests/test_project_context.py` suite still passes.
  - Execution state: performed

- [x] E-09 Update `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`) and `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`):
  - `resolve_existing_policy`: read `role=ctx.project_role` (the `ProjectContext` field is `project_role`; `getattr(ctx, "role", ...)` always returns the default, F-04), `enabled_hosts=list(ctx.enabled_hosts)` (now disk-backed via E-05), `companion_dir` from the existing `local.json` `companion_dir` (`ProjectContext` has no companion attribute; there is no `companion_repo` field), and `non_secret_consent=dict(...)` from the existing `project.json` when it is a `dict`. Read both files from `project_config_dir(p_repo)` already computed in the function.
  - `resolve_policy_noninteractive` (existing-policy branch): normalize `explicit_preset` with `normalize_preset` before use (so a stored preset is always canonical, F-06); when the normalized explicit preset differs from `existing_policy.preset`, take `placements`, `git_policies`, `delivery_mode`, `records_backend`, and `durability_state` from `get_preset_defaults(preset)` (each of `delivery`/`backend` still overridden by an explicit flag); otherwise keep the existing values (also overridden by explicit flags); and carry `role=existing_policy.role` and `non_secret_consent=dict(existing_policy.non_secret_consent)` into the returned `ProjectPolicy`.
  - Cross-placement guard (F-08, review decision D-3): when the new preset's `config_project` placement differs from the existing one (a `target-*` placement versus `home-*`, for example `private-target` to `local-only`), raise `InvalidPolicyError` (a `PolicyError`, which `cli._run_install` already reports via `term.status("fail", ...)` and exit `1`) naming both presets and stating that switching config placement is not supported by reinstall yet (backlog `ui1aln`). Without this guard, refreshing defaults would write the new `project.json` under `AW_HOME` while `project_context.project_config_dir` keeps resolving the stale in-tree one (split brain). A switch within the same placement (for example `completely-clean-target` to `local-only`) proceeds.
  - Depends on: E-05
  - Expected outcome: a cross-placement switch raises `InvalidPolicyError` before anything is written; `resolve_existing_policy` round-trips `role` (for example `source-checkout`), `enabled_hosts`, `companion_dir`, and `non_secret_consent` from existing config files, and `resolve_policy_noninteractive(..., explicit_preset="clean-target")` on an existing `local-only` policy (same home placement) returns `preset == "completely-clean-target"` with `delivery_mode == "clean-delta"` and `records_backend == "home"`, while the same call on an existing `private-target` policy raises `InvalidPolicyError` (today it returns `clean-target`/`tracked`/`repository`, an incoherent policy stored with an un-normalized preset that `parse_portable_policy` then rejects).
  - Execution state: performed

- [x] E-06 Update `cli._run_install` (the `-y` preset default `explicit_preset = Preset.PRIVATE_TARGET.value`, `agent_workflows/cli.py:8302`; the plan earlier called this `cli._cmd_install`, which does not exist) to import `resolve_existing_policy` alongside the existing `install_wizard` imports, resolve `existing_policy = resolve_existing_policy(str(repo_root))` before applying the `-y` fallback, so `explicit_preset` defaults to `Preset.PRIVATE_TARGET.value` only on a first install (`existing_policy is None`) when neither `--preset`, `--delivery-mode`, nor `--records-backend` was passed, and pass `existing_policy=existing_policy` into `collect_policy_interactive`. Keep the `state_durable` normalization announcement (`Normalizing state_durable git policy`) and its `existing_proj` read unchanged.
  - Depends on: E-09
  - Expected outcome: Re-running `aw install <repo> -y --no-interactive` without `--preset` on an already-configured repository preserves its existing preset (`local-only`, `completely-clean-target`, `public-target-private-companion`, or `private-target`) instead of forcing `private-target`, while a first-time `aw install <repo> -y` on an unconfigured repository still defaults to `private-target`.
  - Execution state: performed

### Task group 4: Documentation sync, regression test suite, and mutation proof

- [x] E-07 Add one `- Fixed: ...` bullet to the bullet list of the top pending release section `## 2.0.0 (pending) - AW project layout, storage backends, install wizard, and operational state` in `CHANGELOG.md` (the file has no `## [Unreleased]` heading and no `### Fixed` subsections; entries are flat `- Fixed:`/`- Added:`/`- Changed:` bullets, F-09), describing the preservation of `project.json` policy sections, cutover dates, existing presets/hosts/roles, and `local.json` machine-local settings across `aw install`, and that switching to a preset with a different config placement now refuses instead of silently splitting config; zero em or en dashes.
  - Depends on: E-03, E-04, E-05, E-06, E-09
  - Expected outcome: `CHANGELOG.md` gains exactly one `- Fixed:` bullet in the `2.0.0 (pending)` section with zero em or en dashes.
  - Execution state: performed

- [x] E-08 Create `tests/test_reinstall_preserves_config.py` as `unittest.TestCase` classes (the suite also runs under `python3 -m unittest discover`), each test using its own `tempfile.TemporaryDirectory` scratch git repo with `AW_HOME` and `XDG_CONFIG_HOME` pointed inside it (via `patch.dict(os.environ, ...)` for in-process tests and an explicit `env=` for subprocesses), so no test touches the developer's real home. Cover:
  - `project.json` preservation through `persist_project_policy(replace_config=False)`: `cutovers` with an earlier hand-set date (`spec_id6 = "2020-01-01"`) kept while missing `config.KNOWN_FEATURE_CUTOVERS` keys are still filled, `run`, `setids` non-empty and empty `{}`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_red_exempt_sets`, `non_secret_consent`, `role` (`source-checkout`), `enabled_hosts`; a partial pre-wizard `project.json` (`{"cutovers": {...}, "run": {...}}`); and a `project.json` that `parse_portable_policy` rejects (stored `preset: "clean-target"`) still keeping its `run` key.
  - `local.json` preservation: `run_analytics_sharing` written via `run_analytics_wizard.write_settings`, `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, `companion_dir`.
  - `replace_config=True` discarding prior unknown fields and `setids`.
  - `resolve_project_context` hosts precedence (E-05) and `resolve_existing_policy`/`resolve_policy_noninteractive` round-trip, alias normalization, same-placement preset refresh, and the cross-placement `InvalidPolicyError` (E-09).
  - Subprocess `python3 -m agent_workflows install <repo> -y --no-interactive` (with `AW_NO_REEXEC=1` and `PYTHONPATH` set to the repository root in the child env, and `timeout=`) without `--preset` on a `private-target` repository and on a `local-only` repository (config under `<AW_HOME>/projects/<project_id>/config/`), asserting the preset and every customized key survive; a first install with `-y` and no preset still yields `private-target`; and `--preset local-only` on a `private-target` repository exits `1` with nothing changed in `.aw/config/project.json`. Mark the subprocess test class `@pytest.mark.slow` only if it measures above the fast-suite budget (the repository's slow-marker convention, e.g. `tests/test_install_report_truth.py` `pytestmark = pytest.mark.slow`), and record the measured wall time in V-08.
  - Perform two mutation proofs (each restored and confirmed by `git diff` afterwards): (a) drop the existing-`project.json` merge in `persist_project_policy`; (b) drop the existing-`local.json` merge. Then run `python3 -m pytest tests/test_reinstall_preserves_config.py tests/test_install_consent_truth.py tests/test_project_context.py tests/test_records_untracked_backend.py -o addopts=""`, the bare suite `python3 -m pytest`, and `aw sanitize --agent`.
  - Depends on: E-06, E-07
  - Expected outcome: the new module and the adjacent install/context suites pass; mutation (a) fails the `project.json` preservation tests and mutation (b) fails the `local.json` preservation tests, both pass again after restoration; bare `python3 -m pytest` passes; `aw sanitize --agent` exits `0`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Never work or edit directly on `main`; all implementation and test runs take place in an isolated lane worktree and commit through `aw commit <plan> -- <paths>` (see `AGENTS.md` `"USE THE TOOLED COMMIT PATH"`).
- Write no em or en dashes in user-facing prose (`CHANGELOG.md`, CLI output, wizard text); use plain hyphens, colons, or parentheses (`GEMINI.md` Rule 3).
- Run the test suite via bare `python3 -m pytest` without `-n0`, extra `-q`, or `-p no:randomly` (`GEMINI.md` Rule 5).
- Test observable outcomes and CLI/subprocess behavior, never code structure via `inspect`, `ast`, or regex over source files (`GEMINI.md` Rule 6).
- `project_context.py` must remain pure and side-effect-free (`agent_workflows/project_context.py:6`: `"Invariants: - PURE: ZERO filesystem writes, directory creation, or Git mutation."`).
- Preserve existing `state_durable` upgrade normalization in `cli._run_install` (`"Normalizing state_durable git policy from target-git to ignored"`, `agent_workflows/cli.py:8389`, and `test_install_consent_truth.TestInstallConsentTruth.test_upgrade_normalization_announcement_and_no_repeat`, `tests/test_install_consent_truth.py:228`), which relies on `ProjectPolicy.__post_init__` deriving canonical `placements` and `git_policies` from `get_preset_defaults(preset)`.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:952`) | `persist_project_policy` constructs a brand-new `ProjectPolicySchema` with only the 9 wizard fields (`schema_version`, `preset`, `role`, `placements`, `git_policies`, `enabled_hosts`, `non_secret_consent`, `delivery_mode`, `records_backend`) and overwrites `proj_json` via `os.replace`, ignoring `replace_config: bool = False`. Every existing `cutovers` entry, `setids` map, and `unknown_fields` key (`run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_checkup_interval_commits`, `ci_checkup_workflow`, `ci_checkup_branch`, `ci_red_exempt_sets`, `dependency_schema_cutover`) is discarded. Immediately afterward (`install_wizard.persist_project_policy`, `agent_workflows/install_wizard.py:983`), `_config.sync_cutovers_on_install(repo_path, aw_home=policy.aw_home)` sees no `cutovers` map in `project.json` and stamps `now_iso` (or install-history date) over every hand-set or previously stamped cutover date (verified in reproduction probe: `cutovers.spec_id6: "2020-01-01"` was overwritten with `"2026-10-14"`). |
| F-02 | High | `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:969`) | `persist_project_policy` constructs a fresh `LocalBindingSchema(schema_version=2, project_id=ctx.project_id, companion_dir=policy.companion_dir)` and overwrites `local_json` via `os.replace` without reading the existing `local.json`. This wipes `unknown_fields` (specifically `run_analytics_sharing` written by `run_analytics_wizard.write_settings` at `agent_workflows/run_analytics_wizard.py:183` and top-level `run_analytics_telemetry`), `runtime_overrides` (such as `runtime_overrides.run_analytics_telemetry`), `local_aliases`, `human_slug`, `worktree_path`, and `common_dir`. |
| F-03 | Medium | `project_schema.ProjectPolicySchema.to_dict` (`agent_workflows/project_schema.py:546`) | `ProjectPolicySchema.to_dict` checks `if self.cutovers:` and `if self.setids:` using truthiness instead of `is not None`, so an explicit empty dictionary (`"cutovers": {}` or `"setids": {}`) parsed by `parse_portable_policy` is silently dropped on serialization. |
| F-04 | Medium | `project_context.resolve_project_context` (`resolved_hosts = (`, `agent_workflows/project_context.py:1383`), `install_wizard.resolve_existing_policy` (`agent_workflows/install_wizard.py:518`), and `install_wizard.resolve_policy_noninteractive` (`agent_workflows/install_wizard.py:557`) | (1) `resolve_project_context` sets `resolved_hosts = enabled_hosts if enabled_hosts is not None else DEFAULT_ENABLED_HOSTS`, ignoring `project_policy_data.get("enabled_hosts")` and `merged_local_binding.get("enabled_hosts")`, so `resolve_existing_policy` resets `enabled_hosts` to `["opencode", "claude", "antigravity"]` on reinstall. (2) `resolve_existing_policy` reads `getattr(ctx, "role", ...)` and `getattr(ctx, "companion_dir", None)`, but `project_schema.ProjectContext` (`agent_workflows/project_schema.py:792`) defines `project_role` and has no companion field at all, so both always return their defaults; and `resolve_policy_noninteractive` does not forward `role` or `non_secret_consent` from `existing_policy`. Review probe at `461fdf679`: after hand-setting `role`, `enabled_hosts: ["opencode"]` and `non_secret_consent`, `resolve_existing_policy` returned `('private-target', 'target', ['opencode', 'claude', 'antigravity'], {})`. |
| F-05 | Medium | `cli._run_install` (`explicit_preset = Preset.PRIVATE_TARGET.value`, `agent_workflows/cli.py:8302`) | When `aw install <repo> -y` is invoked without `--preset` or `--delivery-mode`, `cli._run_install` unconditionally sets `explicit_preset = Preset.PRIVATE_TARGET.value` before `collect_policy_interactive` resolves `existing_policy`. Review probe at `461fdf679` (subprocess `python3 -m agent_workflows install <repo> -y --no-interactive` on a `local-only` repository with `run` and `cutovers.spec_id6 = "2020-01-01"` hand-set): exit `0`, and the home-backed `project.json` came back `preset: private-target`, `run: None`, `spec_id6: 2026-10-15`. |
| F-06 | Medium | `install_wizard.resolve_policy_noninteractive` (existing-policy branch, `preset = explicit_preset or existing_policy.preset`) | The existing-policy branch neither normalizes an alias preset nor refreshes preset defaults. Review probe: `explicit_preset="clean-target"` on an existing `private-target` policy produced and stored `preset: "clean-target"` with `delivery_mode: tracked`, `records_backend: repository`; `parse_portable_policy` then raises `ValueError: Unknown preset: 'clean-target'` on that file. |
| F-07 | Low | `project_schema.parse_portable_policy` (`agent_workflows/project_schema.py:589`) | The plan assumed a `SchemaValidationError` on a partial `project.json` and a `FORBIDDEN_PORTABLE_KEYS`/`_check_no_path_leaks` filter; none of these symbols exist in `agent_workflows/`. `parse_portable_policy` defaults missing `preset`/`role`/`placements` and raises plain `ValueError` only for an unknown preset or role or `schema_version > 2`. Review probe: `parse_portable_policy({"cutovers": {"spec_id6": "2020-01-01"}, "run": {"retry_budget": 4}})` returns a schema whose `to_dict()` keeps both keys. |
| F-08 | High | `project_context.project_config_dir` (`agent_workflows/project_context.py:755`) vs `install_wizard.persist_project_policy` (`proj_json = Path(ctx.physical_classes["config_project"])`) | `project_config_dir` prefers `<repo>/.aw/config/project.json` whenever it exists, but `persist_project_policy` writes to the NEW preset's `config_project` placement. Review probe: after a `private-target` install, persisting a coherent `local-only` policy wrote `<AW_HOME>/projects/<id>/config/project.json` while the stale in-tree `private-target` file remained and is what every reader resolves. Refreshing preset defaults (needed for F-06) would therefore turn today's incoherent switch into a silent split brain. `private-target` and `public-target-private-companion` place config in the target; `completely-clean-target` and `local-only` place it under `AW_HOME`. |
| F-09 | Low | `CHANGELOG.md` top section `## 2.0.0 (pending) - AW project layout, storage backends, install wizard, and operational state` | There is no `## [Unreleased]` heading and no `### Fixed` subsection; entries are flat `- Fixed:`/`- Added:`/`- Changed:` bullets in the pending release section. |

## Proposed changes (ordered, validatable)

1. **Task group 1 (`E-01`, `E-02`): re-measurement and `ProjectPolicySchema.to_dict` empty-dict preservation (`agent_workflows/project_schema.py`)**: in `project_schema.ProjectPolicySchema.to_dict`, change `if self.cutovers:` to `if self.cutovers is not None:` and `if self.setids:` to `if self.setids is not None:`.
2. **Task group 2 (`E-03`, `E-04`): read-modify-write merge in `install_wizard.persist_project_policy`**: when `not replace_config` and the target file exists, read it, parse with `parse_portable_policy` / `parse_local_binding`, fall back to the raw dict on `ValueError`, and carry `cutovers`, `setids`, `unknown_fields`, merged `non_secret_consent` (project) and `human_slug`, `worktree_path`, `common_dir`, `local_aliases`, `runtime_overrides`, `unknown_fields`, `companion_dir` (`policy.companion_dir if policy.companion_dir is not None else (existing_local.companion_dir if policy.records_backend == RecordsBackend.COMPANION.value else None)`) (local) into the written schemas before `_config.sync_cutovers_on_install` runs.
3. **Task group 3 (`E-05`, `E-09`, `E-06`): round-trip existing policy**: hosts precedence in `resolve_project_context` (E-05); `role`/`enabled_hosts`/`companion_dir`/`non_secret_consent` round-trip, alias normalization, same-placement default refresh, and a cross-placement `InvalidPolicyError` in `install_wizard` (E-09); `existing_policy` resolved before the `-y` preset default in `cli._run_install` (E-06).
4. **Task group 4 (`E-07`, `E-08`): `CHANGELOG.md` bullet and `tests/test_reinstall_preserves_config.py`** with two mutation proofs, adjacent suites, the bare suite, and `aw sanitize --agent`.

## Deferred / out of scope (with reason)

- Relocating config when `aw install --preset` switches between a target-placed preset (`private-target`, `public-target-private-companion`) and a home-placed one (`completely-clean-target`, `local-only`) (F-08). This is a migration that moves or deletes tracked files and must reconcile two config locations; this plan instead refuses the switch with `InvalidPolicyError` (E-09) so the bug fix does not introduce a silent split brain.
  - Carrier: ui1aln

## Scope check

- Over-scope: none. Every E-item directly serves backlog `qyevpr` (stopping `aw install` and `persist_project_policy` from clobbering `.aw/config/project.json` policy sections, cutover dates, and `.aw/config/local.json` machine-local settings across reinstalls).
- Under-scope: none. Both the direct API surface (`persist_project_policy`, `resolve_existing_policy`, `resolve_policy_noninteractive`, `ProjectPolicySchema.to_dict`, `resolve_project_context`) and the CLI entrypoint (`cli._run_install` with `aw install -y`) are covered across both in-tree and `AW_HOME`-backed config placements. Cross-placement relocation is deferred to `ui1aln` and guarded here (E-09).

## Required tests / validation

- Unit tests in `tests/test_reinstall_preserves_config.py` verifying:
  - `ProjectPolicySchema.to_dict()` preserves empty dicts (`cutovers={}`, `setids={}`) and omits `None`.
  - `persist_project_policy` (`replace_config=False`) preserves `cutovers` (including earlier dates like `"2020-01-01"` while still filling any missing `KNOWN_FEATURE_CUTOVERS` keys via `sync_cutovers_on_install`), `run`, `setids`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, `ci_red_exempt_sets`, `dependency_schema_cutover`, and `non_secret_consent` in `project.json`, as well as `run_analytics_sharing` (`run_analytics_wizard.write_settings`), `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, and `companion_dir` in `local.json`.
  - `persist_project_policy` on a pre-wizard partial `project.json` (containing only `{"cutovers": {"spec_id6": "2020-01-01"}, "run": {"retry_budget": 4}}`) preserves both keys when upgrading to the full v2 `ProjectPolicySchema`.
  - `persist_project_policy(..., replace_config=True)` discards prior `unknown_fields` and `setids` when an explicit reset is requested.
- Subprocess CLI integration tests in `tests/test_reinstall_preserves_config.py` running `python3 -m agent_workflows install <repo> -y --no-interactive` (child env: scratch `AW_HOME`/`XDG_CONFIG_HOME`, `AW_NO_REEXEC=1`, `PYTHONPATH=<repo root>`):
  - On a `private-target` repo with customized `.aw/config/project.json` (`cutovers.spec_id6 = "2020-01-01"`, `run = {"retry_budget": 2}`, `setids = {"warn_length": 10}`, `release_gate_work_kinds = ["bug", "security"]`, `enabled_hosts = ["opencode"]`, `role = "source-checkout"` (the only non-default value in `project_schema.PROJECT_ROLES`; `companion` is rejected by `parse_portable_policy`), `non_secret_consent = {"telemetry_prompted": True}`) and customized `.aw/config/local.json` (`run_analytics_sharing`, `runtime_overrides`), asserting every field is identical after reinstall.
  - On a `local-only` repo (config stored under `<aw_home>/projects/<project_id>/config/`) re-running `aw install <repo> -y --no-interactive` without `--preset`, asserting `preset == "local-only"` and all custom `project.json` and `local.json` keys under `AW_HOME` are preserved.
  - On a `private-target` repo re-running `aw install <repo> --preset local-only -y --no-interactive`, asserting exit `1` with an error naming the unsupported config-placement switch and `.aw/config/project.json` byte-identical to before (F-08, deferred to `ui1aln`).
  - On a `local-only` repo re-running with `--preset clean-target`, asserting the stored preset is `completely-clean-target` (normalized) with every custom key and cutover date preserved.
  - On a fresh repo, `aw install <repo> -y --no-interactive` with no preset still yields `private-target`.
- Mutation proofs: separately remove the `project.json` merge and the `local.json` merge in `install_wizard.persist_project_policy`, run `python3 -m pytest -o addopts="" tests/test_reinstall_preserves_config.py` to observe the matching tests fail, restore each, confirm with `git diff`, and re-run.
- Adjacent suites: `python3 -m pytest -o addopts="" tests/test_install_consent_truth.py tests/test_project_context.py tests/test_records_untracked_backend.py tests/test_project_layout.py`.
- Full suite: bare `python3 -m pytest`; `aw sanitize --agent`.

## Spec / documentation sync

- Add one `- Fixed:` bullet to the `## 2.0.0 (pending)` section of `CHANGELOG.md` with zero em or en dashes (E-07). No spec amendment is required: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 7 (`## 7. Configuration and precedence`) already defines `project.json`/`local.json` as versioned JSON whose unknown fields "remain preserved", and `project_schema.parse_portable_policy` / `parse_local_binding` already round-trip `unknown_fields`, `cutovers`, and `setids`; this plan makes the install writer honor that existing contract. The new cross-placement refusal is install-wizard behavior, not a spec-governed contract change, and the relocation design that would need spec text is carried by `ui1aln`.

## Open questions

### OQ-01: Should `persist_project_policy` preserve existing `cutovers`, `setids`, and `unknown_fields` when `project.json` was partially populated before the install wizard first ran (for example by `sync_cutovers_on_install` or manual edits lacking `preset` / `placements`)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. Resolved from repository evidence: `config.sync_cutovers_on_install` (`agent_workflows/config.py:1505`) rewrites whatever dict `project.json` holds, so a pre-wizard file can hold only `cutovers`; and `project_schema.parse_portable_policy` (`agent_workflows/project_schema.py:589`) defaults missing `preset`/`role`/`placements` rather than raising (corrected at review: there is no `SchemaValidationError`, F-07; demonstrated by the review probe recorded in F-07, which round-tripped a `{cutovers, run}` partial document). So the partial case is handled by the normal parse path, and the raw-dict fallback in E-03 covers only the `ValueError` cases (unknown preset or role, `schema_version > 2`). The written `ProjectPolicySchema` is still a complete v2 document because the wizard fields come from `policy`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted command output from the pre-edit re-measurement at execution `HEAD` showing the line offsets of `ProjectPolicySchema.to_dict`, `resolve_project_context`, `resolve_existing_policy`, `resolve_policy_noninteractive`, `persist_project_policy`, and the `-y` preset default in `cli._run_install`, together with the baseline reproduction output (scratch temp repo; no real home touched) demonstrating `project.json` and `local.json` clobbering, the un-normalized `clean-target` preset (F-06), and the `local-only` repository coming back `private-target` after `aw install <repo> -y --no-interactive` (F-05).
  - Observed evidence:
    Pre-edit line offsets at execution HEAD (ffd5e679bf3c8a8f917ba833f9f64f222e0d09f5):
    - `ProjectPolicySchema.to_dict`: agent_workflows/project_schema.py:532
    - `resolve_project_context` (`resolved_hosts = (`): agent_workflows/project_context.py:1632
    - `resolve_existing_policy`: agent_workflows/install_wizard.py:518
    - `resolve_policy_noninteractive`: agent_workflows/install_wizard.py:557
    - `persist_project_policy`: agent_workflows/install_wizard.py:920
    - `cli._run_install` (`explicit_preset = Preset.PRIVATE_TARGET.value`): agent_workflows/cli.py:8388

    Baseline reproduction probe output:
    ```
    Resolved existing policy role: target
    Resolved existing policy enabled_hosts: ['opencode', 'claude', 'antigravity']
    --- After persist_project_policy ---
    project.json cutovers: {'spec_id6': '2026-10-16', 'dependency_schema': '2026-10-16', 'carrier_obligations': '2026-10-16', 'setid_length': '2026-10-16', 'prompt_id6': '2026-10-16', 'walkthrough_id6': '2026-10-16', 'release_gate_at_rest': '2026-10-16', 'graduation_ready': '2026-10-16', 'spec_requirement_ids': '2026-10-16'}
    project.json run: None
    project.json setids: None
    project.json release_gate_work_kinds: None
    project.json non_secret_consent: {}
    project.json role: target
    project.json enabled_hosts: ['opencode', 'claude', 'antigravity']
    local.json run_analytics_sharing: None
    local.json runtime_overrides: {}
    --- F-06 resolve_policy_noninteractive explicit_preset=clean-target ---
    preset: clean-target
    delivery_mode: tracked
    records_backend: home
    --- F-05 First install local-only returncode --- 0
    --- F-05 Reinstall returncode --- 0
    --- F-05 Preset after reinstall --- private-target
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/project_schema.py` and pasted Python one-liner output showing `parse_portable_policy( data ).to_dict()` preserving `"cutovers": {}` and `"setids": {}` when set to empty dicts and omitting them when `None`.
  - Observed evidence:
    `git diff -- agent_workflows/project_schema.py`:
    ```diff
    @@ -543,9 +543,9 @@ def to_dict(self) -> Dict[str, Any]:
                 res["delivery_mode"] = self.delivery_mode
             if self.records_backend:
                 res["records_backend"] = self.records_backend
    -        if self.cutovers:
    +        if self.cutovers is not None:
                 res["cutovers"] = dict(self.cutovers)
    -        if self.setids:
    +        if self.setids is not None:
                 res["setids"] = dict(self.setids)
             if self.unknown_fields:
                 for k, v in self.unknown_fields.items():
    ```
    Python one-liner output:
    ```
    with empty dicts: True {} True {}
    with None: False False
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/install_wizard.py` for `persist_project_policy`'s `project.json` handling and pasted Python probe output showing `persist_project_policy` preserving `cutovers` (including `"spec_id6": "2020-01-01"`), `setids`, `run`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`, and `non_secret_consent` on both a full v2 `project.json` and a partial pre-wizard `project.json`, and resetting them when `replace_config=True`.
  - Observed evidence:
    `git diff -- agent_workflows/install_wizard.py`:
    ```diff
    @@ -952,6 +1012,50 @@ def persist_project_policy(
             local_json.parent.mkdir(parents=True, exist_ok=True)

         # 1. Write portable project policy
    +    existing_cutovers: Optional[Dict[str, str]] = None
    +    existing_setids: Optional[Dict[str, Any]] = None
    +    existing_unknown: Dict[str, Any] = {}
    +    existing_consent: Dict[str, bool] = {}
    +
    +    if not replace_config and proj_json.exists():
    +        try:
    +            with open(proj_json, "r", encoding="utf-8") as f:
    +                raw_proj = json.load(f)
    +            if isinstance(raw_proj, dict):
    +                try:
    +                    parsed_proj = parse_portable_policy(raw_proj)
    +                    existing_cutovers = parsed_proj.cutovers
    +                    existing_setids = parsed_proj.setids
    +                    existing_unknown = dict(parsed_proj.unknown_fields or {})
    +                    existing_consent = dict(parsed_proj.non_secret_consent or {})
    +                except ValueError:
    +                    known_proj_keys = {
    +                        "schema_version", "preset", "role", "placements", "git_policies",
    +                        "enabled_hosts", "non_secret_consent", "delivery_mode",
    +                        "records_backend", "cutovers", "setids",
    +                    }
    +                    if isinstance(raw_proj.get("cutovers"), dict):
    +                        existing_cutovers = dict(raw_proj["cutovers"])
    +                    if isinstance(raw_proj.get("setids"), dict):
    +                        existing_setids = dict(raw_proj["setids"])
    +                    if isinstance(raw_proj.get("non_secret_consent"), dict):
    +                        existing_consent = dict(raw_proj["non_secret_consent"])
    +                    existing_unknown = {
    +                        k: v for k, v in raw_proj.items() if k not in known_proj_keys
    +                    }
    +        except Exception:
    +            pass
    +
    +    merged_consent = {**existing_consent, **(policy.non_secret_consent or {})}
    +
         proj_schema = ProjectPolicySchema(
             schema_version=2,
             preset=policy.preset,
             role=policy.role,
             placements=policy.placements,
             git_policies=policy.git_policies,
             enabled_hosts=policy.enabled_hosts,
    -        non_secret_consent=policy.non_secret_consent,
    +        non_secret_consent=merged_consent,
             delivery_mode=policy.delivery_mode,
             records_backend=policy.records_backend,
    +        cutovers=existing_cutovers,
    +        setids=existing_setids,
    +        unknown_fields=existing_unknown if existing_unknown else None,
         )
    ```
    Python probe output:
    ```
    === Full v2 after persist_project_policy (replace_config=False) ===
    cutovers.spec_id6: 2020-01-01
    setids: {'warn_length': 10}
    run: {'retry_budget': 2}
    release_gate_work_kinds: ['bug', 'security']
    review_findings_gate: {'strict': True}
    run_analytics_telemetry: {'enabled': False}
    non_secret_consent: {'consent_a': True, 'consent_b': True}
    === Partial pre-wizard after persist_project_policy (replace_config=False) ===
    cutovers.spec_id6: 2020-01-01
    run: {'retry_budget': 4}
    === After persist_project_policy (replace_config=True) ===
    cutovers.spec_id6: 2026-10-16
    run: None
    setids: None
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff -- agent_workflows/install_wizard.py` for `persist_project_policy`'s `local.json` handling and pasted Python probe output showing `persist_project_policy` preserving `run_analytics_sharing` (written by `run_analytics_wizard.write_settings`), `runtime_overrides`, `local_aliases`, `human_slug`, `worktree_path`, `common_dir`, and `companion_dir` in `local.json`.
  - Observed evidence:
    `git diff -- agent_workflows/install_wizard.py`:
    ```diff
    @@ -967,11 +1074,79 @@ def persist_project_policy(
         os.replace(tmp_proj, proj_json)

         # 2. Write machine-local binding
    -    local_schema = LocalBindingSchema(
    -        schema_version=2,
    -        project_id=ctx.project_id,
    -        companion_dir=policy.companion_dir,
    -    )
    +    existing_slug = ""
    +    existing_common = None
    +    existing_worktree = None
    +    existing_companion = None
    +    existing_overrides: Dict[str, Any] = {}
    +    existing_aliases: Dict[str, str] = {}
    +    existing_local_unknown: Dict[str, Any] = {}
    +
    +    if not replace_config and local_json.exists():
    +        try:
    +            with open(local_json, "r", encoding="utf-8") as f:
                raw_local = json.load(f)
            if isinstance(raw_local, dict):
                try:
                    parsed_local = parse_local_binding(raw_local)
                    existing_slug = parsed_local.human_slug
                    existing_common = parsed_local.common_dir
                    existing_worktree = parsed_local.worktree_path
                    existing_companion = parsed_local.companion_dir
                    existing_overrides = dict(parsed_local.runtime_overrides or {})
                    existing_aliases = dict(parsed_local.local_aliases or {})
                    existing_local_unknown = dict(parsed_local.unknown_fields or {})
                except ValueError:
                    known_local_keys = {
                        "schema_version", "project_id", "human_slug", "common_dir",
                        "worktree_path", "companion_dir", "runtime_overrides", "local_aliases",
                    }
                    existing_slug = str(raw_local.get("human_slug") or "")
                    existing_common = raw_local.get("common_dir")
                    existing_worktree = raw_local.get("worktree_path")
                    existing_companion = raw_local.get("companion_dir")
                    if isinstance(raw_local.get("runtime_overrides"), dict):
                        existing_overrides = dict(raw_local["runtime_overrides"])
                    if isinstance(raw_local.get("local_aliases"), dict):
                        existing_aliases = dict(raw_local["local_aliases"])
                    existing_local_unknown = {
                        k: v for k, v in raw_local.items() if k not in known_local_keys
                    }
        except Exception:
            pass
    +
    +    companion_dir_to_write = policy.companion_dir
    +    if (
    +        companion_dir_to_write is None
    +        and policy.records_backend == RecordsBackend.COMPANION.value
    +        and existing_companion is not None
    +    ):
    +        companion_dir_to_write = existing_companion
    +
    +    if replace_config or not local_json.exists():
    +        local_schema = LocalBindingSchema(
    +            schema_version=2,
    +            project_id=ctx.project_id,
    +            companion_dir=policy.companion_dir,
    +        )
    +    else:
    +        local_schema = LocalBindingSchema(
    +            schema_version=2,
    +            project_id=ctx.project_id,
    +            human_slug=existing_slug,
    +            common_dir=existing_common,
    +            worktree_path=existing_worktree,
    +            companion_dir=companion_dir_to_write,
    +            runtime_overrides=existing_overrides if existing_overrides else None,
    +            local_aliases=existing_aliases if existing_aliases else None,
    +            unknown_fields=existing_local_unknown if existing_local_unknown else None,
    +        )
    ```
    Python probe output:
    ```
    local human_slug: my-slug
    local common_dir: /common/dir
    local worktree_path: /worktree/path
    local companion_dir: /companion/dir (with RecordsBackend.COMPANION)
    local local_aliases: {'al': 'alias_val'}
    local runtime_overrides: {'ro': 'override_val'}
    local run_analytics_sharing: {'opt_in': True}
    === After persist_project_policy (replace_config=True) ===
    local human_slug:
    local run_analytics_sharing: None
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `git diff -- agent_workflows/project_context.py` and pasted Python probe output showing `resolve_project_context(target_repo=...).enabled_hosts` equal to `["opencode"]` with `PROJECT_DURABLE_CONFIG` provenance when only `project.json` stores it, the explicit `enabled_hosts=` argument winning over it, and `DEFAULT_ENABLED_HOSTS` when nothing is stored; plus pasted passing output of `python3 -m pytest -o addopts="" tests/test_project_context.py`.
  - Observed evidence:
    `git diff -- agent_workflows/project_context.py`:
    ```diff
    @@ -1629,17 +1629,36 @@ def resolve_project_context(
         )

         # 10. Enabled Hosts
    -    resolved_hosts = (
    -        enabled_hosts if enabled_hosts is not None else DEFAULT_ENABLED_HOSTS
    -    )
    -    provenance_map["enabled_hosts"] = Provenance(
    -        source=(
    -            PrecedenceLevel.EXPLICIT_FLAGS.value
    -            if enabled_hosts is not None
    -            else PrecedenceLevel.BUILTIN_DEFAULTS.value
    -        ),
    -        detail=f"enabled third-party hosts ({','.join(resolved_hosts)})",
    -    )
    +    if enabled_hosts is not None:
    +        resolved_hosts = list(enabled_hosts)
    +        provenance_map["enabled_hosts"] = Provenance(
    +            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
    +            detail=f"enabled third-party hosts ({','.join(resolved_hosts)})",
    +        )
    +    elif (
    +        isinstance(merged_local_binding.get("enabled_hosts"), list)
    +        and all(isinstance(x, str) for x in merged_local_binding["enabled_hosts"])
    +    ):
    +        resolved_hosts = list(merged_local_binding["enabled_hosts"])
    +        provenance_map["enabled_hosts"] = Provenance(
    +            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
    +            detail=f"machine-local binding ({','.join(resolved_hosts)})",
    +        )
    +    elif (
    +        isinstance(project_policy_data.get("enabled_hosts"), list)
    +        and all(isinstance(x, str) for x in project_policy_data["enabled_hosts"])
    +    ):
    +        resolved_hosts = list(project_policy_data["enabled_hosts"])
    +        provenance_map["enabled_hosts"] = Provenance(
    +            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
    +            detail=f"portable project policy ({','.join(resolved_hosts)})",
    +        )
    +    else:
    +        resolved_hosts = list(DEFAULT_ENABLED_HOSTS)
    +        provenance_map["enabled_hosts"] = Provenance(
    +            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
    +            detail=f"enabled third-party hosts ({','.join(resolved_hosts)})",
    +        )

         # 11. Permitted Commit Destinations
         product_dest = (
    ```
    Python probe output:
    ```
    Case 1 (empty): True builtin_defaults
    Case 2 (project.json): ['opencode'] True
    Case 3 (explicit arg): ['claude'] True
    ```
    Runner output:
    ```
    python3 -m pytest -o addopts="" tests/test_project_context.py
    ============================== 20 passed in 1.02s ==============================
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: Pasted `git diff -- agent_workflows/install_wizard.py` for `resolve_existing_policy` and `resolve_policy_noninteractive`, and pasted Python probe output showing (1) `resolve_existing_policy` returning `role="source-checkout"`, `enabled_hosts=["opencode"]`, the stored `companion_dir`, and the stored `non_secret_consent`; (2) `resolve_policy_noninteractive(..., explicit_preset="clean-target")` on an existing `local-only` policy returning `preset="completely-clean-target"`, `delivery_mode="clean-delta"`, `records_backend="home"`, with `role` and `non_secret_consent` carried; and (3) the same call on an existing `private-target` policy raising `InvalidPolicyError` whose message names both presets and `ui1aln`.
  - Observed evidence:
    `git diff -- agent_workflows/install_wizard.py`:
    ```diff
    @@ -540,9 +540,32 @@ def resolve_existing_policy(repo_path: str) -> Optional[ProjectPolicy]:
             from agent_workflows.project_context import resolve_project_context

             ctx = resolve_project_context(target_repo=repo_path)
    +
    +        comp_dir = None
    +        if local_json.exists():
    +            try:
    +                with open(local_json, "r", encoding="utf-8") as f:
    +                    ldata = json.load(f)
    +                if isinstance(ldata, dict):
    +                    comp_dir = ldata.get("companion_dir")
    +            except Exception:
    +                pass
    +
    +        consent: Dict[str, bool] = {}
    +        if proj_json.exists():
    +            try:
    +                with open(proj_json, "r", encoding="utf-8") as f:
    +                    pdata = json.load(f)
    +                if isinstance(pdata, dict) and isinstance(
    +                    pdata.get("non_secret_consent"), dict
    +                ):
    +                    consent = dict(pdata["non_secret_consent"])
    +            except Exception:
    +                pass
    +
             return ProjectPolicy(
                 preset=getattr(ctx, "preset", Preset.PRIVATE_TARGET.value),
    -            role=getattr(ctx, "role", ProjectRole.TARGET.value),
    +            role=getattr(ctx, "project_role", ProjectRole.TARGET.value),
                 delivery_mode=ctx.delivery_mode,
                 records_backend=ctx.records_backend,
                 durability_state=ctx.durability_state,
    @@ -549,7 +572,8 @@ def resolve_existing_policy(repo_path: str) -> Optional[ProjectPolicy]:
    -            companion_dir=getattr(ctx, "companion_dir", None),
    -            enabled_hosts=getattr(
    -                ctx, "enabled_hosts", ["opencode", "claude", "antigravity"]
    +            companion_dir=comp_dir,
    +            enabled_hosts=list(
    +                getattr(ctx, "enabled_hosts", ["opencode", "claude", "antigravity"])
                 ),
    +            non_secret_consent=consent,
             )
    @@ -567,9 +591,39 @@ def resolve_policy_noninteractive(
         if existing_policy is not None:
    -        preset = explicit_preset or existing_policy.preset
    -        delivery = explicit_delivery or existing_policy.delivery_mode
    -        backend = explicit_backend or existing_policy.records_backend
    +        normalized_explicit = (
    +            normalize_preset(explicit_preset) if explicit_preset else None
    +        )
    +        preset = normalized_explicit or existing_policy.preset
    +
    +        existing_defaults = get_preset_defaults(existing_policy.preset)
    +        existing_cfg_placement = (
    +            existing_policy.placements.get(RootClass.CONFIG_PROJECT.value)
    +            or existing_defaults[0].get(RootClass.CONFIG_PROJECT.value)
    +        )
    +        new_defaults = get_preset_defaults(preset)
    +        new_cfg_placement = new_defaults[0].get(RootClass.CONFIG_PROJECT.value)
    +
    +        if new_cfg_placement != existing_cfg_placement:
    +            raise InvalidPolicyError(
    +                f"Switching config placement from {existing_policy.preset} ({existing_cfg_placement}) "
    +                f"to {preset} ({new_cfg_placement}) is not supported by reinstall yet (backlog ui1aln)."
    +            )
    +
    +        if normalized_explicit and normalized_explicit != existing_policy.preset:
    +            pls, gps, dm, rb, ds = new_defaults
    +            delivery = explicit_delivery or dm
    +            backend = explicit_backend or rb
    +            durability = ds
    +            placements = pls
    +            git_policies = gps
    +        else:
    +            delivery = explicit_delivery or existing_policy.delivery_mode
    +            backend = explicit_backend or existing_policy.records_backend
    +            durability = existing_policy.durability_state
    +            placements = existing_policy.placements
    +            git_policies = existing_policy.git_policies
    ```
    Python probe output:
    ```
    1. role: source-checkout
    1. enabled_hosts: ['opencode']
    1. companion_dir: /my/companion
    1. non_secret_consent: {'telemetry': True}
    2. preset: completely-clean-target
    2. delivery_mode: clean-delta
    2. records_backend: home
    2. role: source-checkout
    2. non_secret_consent: {'telemetry': True}
    3. Raised InvalidPolicyError: True
    3. Message: Switching config placement from private-target (target-tracked) to completely-clean-target (home-untracked) is not supported by reinstall yet (backlog ui1aln).
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` and pasted subprocess output (reachable via `cli._run_install` -> `collect_policy_interactive` -> `resolve_policy_noninteractive` -> `persist_project_policy`, updated in `E-03`, `E-04`, `E-09`, and `E-06`) from running `python3 -m agent_workflows install <repo> -y --no-interactive` (scratch `AW_HOME`/`XDG_CONFIG_HOME`, `AW_NO_REEXEC=1`) without `--preset` on a `local-only` repository and on a `private-target` repository, confirming the existing preset and all `project.json` / `local.json` policy keys and cutover dates remain intact; plus a first install on a fresh repository with `-y` and no preset yielding `private-target`; plus `--preset local-only` on a `private-target` repository exiting `1` with `.aw/config/project.json` unchanged.
  - Observed evidence:
    `git diff -- agent_workflows/cli.py`:
    ```diff
    @@ -8377,13 +8377,17 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
                     collect_policy_interactive,
                     persist_project_policy,
                     render_pre_write_plan,
    +                resolve_existing_policy,
                 )

    +            existing_policy = resolve_existing_policy(str(repo_root))
                 explicit_preset = getattr(args, "preset", None)
                 if (
                     getattr(args, "yes", False)
    +                and existing_policy is None
                     and not explicit_preset
                     and not getattr(args, "delivery_mode", None)
    +                and not getattr(args, "records_backend", None)
                 ):
                     explicit_preset = Preset.PRIVATE_TARGET.value

    @@ -8390,6 +8394,7 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
                     policy = collect_policy_interactive(
                         term=term,
                         repo_path=str(repo_root),
    +                    existing_policy=existing_policy,
                         assume_yes=getattr(args, "yes", False),
                         explicit_preset=explicit_preset,
                         explicit_delivery=getattr(args, "delivery_mode", None),
    ```
    Subprocess probe output:
    ```
    1. Fresh repo returncode: 0
    1. Fresh repo preset: private-target
    2. Local-only reinstall returncode: 0
    2. Local-only preset after reinstall: local-only
    2. Local-only cutovers.spec_id6: 2020-01-01
    2. Local-only run: {'retry_budget': 5}
    3. Private-target reinstall returncode: 0
    3. Private-target preset after reinstall: private-target
    3. Private-target cutovers.spec_id6: 2020-01-01
    3. Private-target run: {'retry_budget': 7}
    3. Private-target role: source-checkout
    3. Private-target local run_analytics_sharing: {'opt_in': True}
    4. Switch cross-placement returncode: 1
    4. Switch project.json unchanged: True
    4. Switch stderr/stdout mentions ui1aln: True
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Pasted `git diff -- CHANGELOG.md` and pasted output of a Python check confirming zero em or en dashes (`\u2014`, `\u2013`) in the added `CHANGELOG.md` lines.
  - Observed evidence:
    `git diff -- CHANGELOG.md`:
    ```diff
    @@ -24,6 +24,8 @@

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: aw install and install_wizard.persist_project_policy now preserve existing project.json policy sections (cutovers, setids, run, release_gate_work_kinds, review_findings_gate, run_analytics_telemetry, ci_checkup_* keys, non_secret_consent, role, enabled_hosts, and existing presets) and local.json machine-local settings (run_analytics_sharing, runtime_overrides, local_aliases, human_slug, worktree_path, common_dir, and companion_dir) across reinstalls, and switching to a preset with a different config placement refuses with InvalidPolicyError instead of silently splitting configuration.
    +
     - Added: aw oc review and aw agy review now support re-reviewing a plan at reviewed, approved, or auto-approved behind an explicit confirmation (-y/--yes or typed phrase re-review), demoting to to-review at lane dispatch with approval withdrawn, and ending at reviewed awaiting fresh human approval.
    ```
    Python check output:
    ```
    Added lines: 2
    Em/en dashes in added lines: 0
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" tests/test_reinstall_preserves_config.py` failing under mutation (a) (the `project.json` preservation tests fail) and under mutation (b) (the `local.json` preservation tests fail), passing after each restoration, with a pasted `git diff -- agent_workflows/install_wizard.py` after restoration showing only the intended E-03/E-04/E-09 edits; pasted passing output of the adjacent suites (`tests/test_install_consent_truth.py`, `tests/test_project_context.py`, `tests/test_records_untracked_backend.py`, `tests/test_project_layout.py`); the measured wall time of the subprocess test class and whether it was marked `slow`; the pasted summary line of the bare full suite `python3 -m pytest`; and `aw sanitize --agent` output exiting `0`. Test counts are re-derived from the runner output at execution, not fixed here.
  - Observed evidence:
    Mutation proof (a) failure output:
    ```
    FAILED tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation::test_preserves_partial_pre_wizard_project_json
    FAILED tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation::test_preserves_full_v2_policy_keys_on_reinstall
    FAILED tests/test_reinstall_preserves_config.py::TestReinstallPreservesConfigSubprocess::test_subprocess_reinstall_local_only_preserves_all_keys
    FAILED tests/test_reinstall_preserves_config.py::TestReinstallPreservesConfigSubprocess::test_subprocess_reinstall_local_only_to_clean_target_normalizes_and_preserves
    FAILED tests/test_reinstall_preserves_config.py::TestReinstallPreservesConfigSubprocess::test_subprocess_reinstall_private_target_preserves_all_keys
    ======================== 5 failed, 11 passed in 16.15s =========================
    ```
    Mutation proof (b) failure output:
    ```
    FAILED tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation::test_preserves_companion_dir_for_companion_backend
    FAILED tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation::test_preserves_local_json_keys
    FAILED tests/test_reinstall_preserves_config.py::TestReinstallPreservesConfigSubprocess::test_subprocess_reinstall_private_target_preserves_all_keys
    ======================== 3 failed, 13 passed in 17.88s =========================
    ```
    Restoration confirmed clean via `git diff -- agent_workflows/install_wizard.py`.
    Post-restoration suite: `16 passed in 22.33s`.
    Adjacent suites output:
    ```
    python3 -m pytest -o addopts="" tests/test_reinstall_preserves_config.py tests/test_install_consent_truth.py tests/test_project_context.py tests/test_records_untracked_backend.py tests/test_project_layout.py
    ============================= 65 passed in 41.20s ==============================
    ```
    Subprocess test class wall time: measured ~16.5s in standalone module run; marked `@pytest.mark.slow`.
    Bare full suite output:
    ```
    python3 -m pytest
    707 passed in 36.71s
    ```
    aw sanitize --agent output:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5236,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute in dependency order `E-01`, `E-02`, `E-03`, `E-04`, `E-05`, `E-09`, `E-06`, `E-07`, `E-08` inside an isolated worktree; do not execute until `- Status: approved`. Open questions: OQ-01 is resolved; none remain open. Mark an `E-*` item `performed` only after doing it, and a `V-*` item `pass` only with concrete pasted evidence; paste the ACTUAL runner output for every test claim and never claim a pass you did not run. Run the full suite bare as `python3 -m pytest` (never `-n0`, an extra `-q`, or `-p no:randomly`). Every probe and test uses a scratch temp repository with `AW_HOME` and `XDG_CONFIG_HOME` inside it; never install into this repository or touch the real home. Mutation proofs are temporary and MUST NOT be committed.
- **Scope fence** (a declaration, not a stop condition): the declared paths are `- Scope-Paths:`. An edit outside them is permitted only when justified, recorded at finalize with `--scope-reason <path>=<why>` (and `--scope-ack` for a declared path left unmodified).
- **Commit**: commit only the paths you changed, plus this IPD, through `aw commit on0keo -- <paths>`; never `git add -A`, never push.
- **Post-gate lifecycle move**: once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` reports no errors, the plan must reach `.aw/records/plans/executed/`: under `aw oc run` / `aw agy run` the runner owns that transition (a lane agent does not finalize its own plan); when executed by hand outside a runner, the executor runs `aw ipd finalize on0keo`. Never hand-`git mv` the plan.
