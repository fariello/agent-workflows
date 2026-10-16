# IPD: Route every system-bundle reader through one system-root accessor

- Date: 2026-10-15
- Kind: child
- Concern: The installed `system` bundle (`workflows/`, `VERSION`, `managed-sections.json`, `layout.json`, `layout.schema.json`) is located by hand-composed `<repo>/.aw/system/...` paths (`engine.AW_SYSTEM_DIR`, `manifest.DEFAULT_MANIFEST_RELPATH`, `engine.AW_LAYOUT_JSON_PATH`) in every reader and writer, although `resolve_project_context` already places `physical_classes["system"]` under `AW_HOME/projects/<project_id>/system` whenever the stored `delivery_mode` is `clean-delta`. So a clean-target install writes and `git add`s the bundle into the target (irjoga F-01 measured 161 staged `.aw/system/` files), and if the bundle lived at home, `read_installed_version`, the manifest lookup, `aw check` and `aw layout` would all report "not installed".
- Scope: Add ONE pure accessor `project_context.project_system_dir(repo_root, aw_home=None) -> Path` (in-tree `<repo>/.aw/system` for an unconfigured or `tracked` project, the resolver's `physical_classes["system"]` when the STORED policy places it elsewhere), and route every TARGET-side system location decision through it: the read side (manifest path, installed version, layout detection, split-brain detection, compat state, emitted-layout load, `aw layout`, `clean_delta.resolve_system_provider`), the install write side (member destination mapping, git staging gate, framework-file collection, prune, layout emission, manifest save) and the upgrade rehearsal probe. Repository-backed and `tracked` installs (including this repository) keep byte-identical behavior. SOURCE-side literals (the package's own bundled `.aw/system` used by `resolve_source_root`, `_compat`, `release_readiness`, `versioning.resolve_version` defaults, `security_hardening`, `host_capability_registry`) are audited and left unchanged with reasons. Out of scope: suppressing host adapters, setup files, backups and the auto-commit (`3m8aix`), uninstall (`xoy5yg`), and project-root recognition with no in-repo `.aw` (`fnnwj3`).
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/manifest.py, agent_workflows/engine.py, agent_workflows/compat_migration.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/clean_delta.py, agent_workflows/upgrade_rehearsal.py, tests/test_system_root_accessor.py, .aw/records/plans/pending/20261015-cleantgt-02-4gn1ka-route-every-system-bundle-reader-through-one-system-root-acc.ipd.md
- Item-Dependencies: executed:kfnfji
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 2
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 4gn1ka
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review: revisions applied (PR-001..PR-006)
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every agent-workflows code path that reads or writes the installed system bundle find it in ONE place, so a clean-delta install puts `workflows/`, `VERSION`, the manifest and the layout documents under `AW_HOME/projects/<project_id>/system/` with nothing staged in the target, while every `tracked` install behaves exactly as today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and the accessor

- [ ] E-01 Re-measure at execution HEAD and capture baselines: re-run the `.aw/system` census (F-01 commands); in a temp repo with temp `HOME`/`AW_HOME` and git identity, run `aw install <t> --preset private-target -y` and save `git -C <t> ls-files --stage`, the sorted `find <t>/.aw/system -type f` list and `managed-sections.json` as the TRACKED baseline; in a second temp repo run `aw install <t2> --preset completely-clean-target -y` and record the count of `.aw/system/` paths in `git -C <t2> ls-files` and the absence of `<AW_HOME>/projects/<id>/system/`. Add the new test file `tests/test_system_root_accessor.py` with subprocess tests that encode this plan's outcomes (V-03, V-04) and observe them FAIL on the unmodified code.
  - Depends on: none
  - Expected outcome: Census, both install baselines and the failing test run are recorded in V-01; the tracked baseline files are kept outside the repo for the E-07 parity diff.
  - Execution state: pending

- [ ] E-02 Add the pure accessor `project_context.project_system_dir(repo_root: str | Path, aw_home: Optional[str | Path] = None) -> Path` beside `project_records_dir`, built on the memoized resolution that `kfnfji` E-02 introduced (do not add a second cache or a second resolver call). Note that `kfnfji`'s `_stored_physical_classes` returns `None` whenever the RECORDS placement is not stored, which is the wrong gate for `system`: a stored `{"delivery_mode":"clean-delta","records_backend":"repository"}` is refused by the resolver anyway, but a stored `{"delivery_mode":"clean-delta"}` with a `records_backend` that comes only from built-in defaults would be dropped. So generalize the helper in place to `_stored_physical_classes(repo_root, aw_home=None, *, root_class)` (or return the cached `(ctx-derived physical_classes, provenance)` pair and gate per class), keeping `kfnfji`'s records behavior byte-identical. The `system` placement is STORED when the resolved `delivery_mode` provenance is `project_durable_config` or `machine_local_binding` (an explicit key, or the `completely-clean-target` derivation, which the resolver labels `project_durable_config`), or when `local.json` binds `system_root`. Rule: no config files, or a placement that is not stored (for example `project.json` = `{"role":"target"}`, or a `local-only` preset stored without `delivery_mode`; see F-08), returns `Path(repo_root) / ".aw" / "system"`. Otherwise return `physical_classes[RootClass.SYSTEM.value]`, and when that equals the canonical form of `<repo>/.aw/system` return the caller's spelling `Path(repo_root) / ".aw" / "system"` (byte-identical paths for a symlinked repo root). A `ProjectContextError` (including the clean-delta `PathSecurityError` "system root ... is inside target repository") propagates and is not cached. Add unit tests: unconfigured, `{"role":"target"}` (in-tree), stored `tracked`, stored `clean-delta` in a home config with no in-repo `.aw`, a stored `completely-clean-target` preset with no `delivery_mode` key (home), a `system_root` override in `local.json`, a source-checkout role (this repository's own stored `tracked` policy resolves in-tree), and a re-run of `kfnfji`'s records accessor unit tests unchanged.
  - Depends on: E-01
  - Expected outcome: `project_system_dir` returns `<repo>/.aw/system` for unconfigured, not-stored and `tracked`, `<AW_HOME>/projects/<id>/system` for stored `clean-delta`, and the override path when bound; unit tests pass; `project_context.py` performs zero writes.
  - Execution state: pending

### Task group 2: Read side

- [ ] E-03 Route the READ-side target system lookups through `project_system_dir`: `manifest.resolve_manifest_path` (new path = `project_system_dir(root) / "managed-sections.json"`, legacy `.agents/agent-workflows/managed-sections.json` fallback unchanged), `engine.read_installed_version` (first candidate `project_system_dir(repo_root) / VERSION_FILE`, then `.../workflows/VERSION`, then the legacy `.agents/workflows/VERSION`), `engine.resolve_target_layout` and `engine.detect_split_brain_layout` (system presence = `project_system_dir(repo_root).exists()`), `compat_migration.CompatMigrator.detect_state` (`has_aw_system`), `cli._handle_legacy_migration` (`is_legacy_only`), `check_engine.load_emitted_layout` and `check_engine.check_system_layout` (layout document at `project_system_dir(root) / "layout.json"`, diagnostics still report the logical `.aw/system/layout.json` location), `cli._run_layout` (`source_path`), and `clean_delta.resolve_system_provider` (use the accessor instead of an unconditional resolver call, so it no longer resolves an unconfigured repo through built-in defaults; it and its only caller `clean_delta.resolve_adapter_reference` have NO caller in `agent_workflows/` or `tests/` at review, so cover the change with one direct unit test rather than an end-to-end one).
  - Depends on: E-02
  - Expected outcome: With a bundle placed under `<AW_HOME>/projects/<id>/system/` for a stored `clean-delta` fixture, `engine.read_installed_version` returns the bundle VERSION, `aw doctor --json` run with cwd = the fixture reports it as `installed_version`, `aw list-repos --json` reports it for the fixture once the fixture is registered in the temp user config (`XDG_CONFIG_HOME`, as `aw install` itself does; `aw status --json` reports only config-registered repositories, so an unregistered fixture shows `installed: null` at HEAD for a reason unrelated to this plan), `aw check all` emits no `check.system-layout-missing`, and `aw layout` reports the emitted document as its source; a `tracked` fixture resolves exactly the paths it did before.
  - Execution state: pending

### Task group 3: Install write side

- [ ] E-04 Route the INSTALL write side through one helper `engine._system_member_destination(repo_root: Path, relative_posix: str) -> tuple[Path, bool]` that maps a member beginning `.aw/system/` onto `project_system_dir(repo_root) / <tail>` and returns whether the destination is inside `repo_root` (every other member maps to `repo_root / relative_posix`, in tree). Use it in `engine.write_file` (destination, and call `_stage_installed_file` only when in tree), `engine.collect_target_framework_files` (enumerate the resolved workflows dir and VERSION, reporting LOGICAL `.aw/system/...` member names so manifest keys are unchanged), `engine.prune_stale` (destination, and `git rm` only when in tree and tracked), `engine.emit_layout_artifacts` (target path), and `engine.install_into_repo` (manifest load/save path via E-03's `resolve_manifest_path`, and `_layout_pre_existing` sampled at the resolved paths). Manifest keys and `installed`/`skipped` report strings stay LOGICAL (`.aw/system/...`), so `managed-sections.json` is portable and identical in shape for both placements.
  - Depends on: E-03
  - Expected outcome: After `aw install <t> --preset completely-clean-target -y`, `<AW_HOME>/projects/<id>/system/` holds `VERSION`, `managed-sections.json`, `layout.json`, `layout.schema.json` and `workflows/index.md`; `git -C <t> ls-files` and `git -C <t> status --porcelain --ignored` contain NO `.aw/system` path; a second install reports the bundle current (no rewrite); a stale member injected under the home bundle is pruned. Other target writes (host adapters, records scaffolding, setup files) still occur; they are `3m8aix`'s.
  - Execution state: pending

- [ ] E-05 Route the upgrade rehearsal probe: `upgrade_rehearsal.installed_version`, `upgrade_rehearsal.detect_layout` and `upgrade_rehearsal.manifest_summary` resolve the system dir through `project_system_dir(repo, aw_home=<sandbox>/.aw-upgrade-test/aw-home)` (the same AW_HOME `upgrade_rehearsal.sandbox_env` gives the sandboxed `aw` subprocesses), keeping `VERSION_LOCATIONS` as the in-tree fallback order, so `aw upgrade-test` reports a clean-delta sandbox's installed version and manifest instead of "none". FEASIBILITY (F-09): `upgrade_rehearsal.sandbox_env` puts AW_HOME at `<sandbox>/.aw-upgrade-test/aw-home`, INSIDE the sandbox repo, and the resolver refuses that for clean-delta (measured at review: `PathSecurityError: Clean-delta security violation: system root (<sandbox>/.aw-upgrade-test/aw-home/projects/<id>/system) is inside target repository`). So the probe MUST catch `ProjectContextError` from the accessor, fall back to the in-tree `VERSION_LOCATIONS`, and record `system_root_error: <message>` in the probe output instead of crashing the rehearsal. Moving the sandbox AW_HOME outside the sandbox (which would make the clean-delta probe work) changes the rehearsal's containment invariant (invariant 3) and is deferred.
  - Depends on: E-04
  - Expected outcome: A rehearsal probe of a clean-delta sandbox whose policy and bundle live under an AW_HOME OUTSIDE the sandbox (passed explicitly to the probe in a unit test) reports `installed_version` from the home bundle and a non-empty manifest summary; a probe of a clean-delta sandbox using the default in-sandbox AW_HOME completes, reports the in-tree fallback, and carries `system_root_error`; a tracked sandbox probe is unchanged.
  - Execution state: pending

### Task group 4: Residual audit and validation

- [ ] E-06 Re-run the census and classify EVERY remaining `.aw/system` occurrence in `agent_workflows/` into exactly one of: (a) routed through `project_system_dir`; (b) LOGICAL member name or classifier on repo-relative strings (`engine.AW_SYSTEM_DIR`/`AW_SYSTEM_WORKFLOWS_DIR`/`AW_LAYOUT_JSON_PATH` as manifest keys, `engine.in_framework_namespace`, `engine.collect_source_members`, `engine.resolve_workflows_dir`, `migration_compact.resolve_body_dir`, `host_adapters.disabled_skill_still_invocable`, `doctor._map_aw_to_legacy`, `clean_delta` adapter `canonical_system_identity` strings, `layout.LOGICAL_ROOTS`); (c) SOURCE side, i.e. the toolkit's own packaged or checked-out bundle and never a target (`engine.resolve_source_root`, `engine.is_source_checkout`, `_compat.SYSTEM_DATA_RELATIVE`, `release_readiness` gates rooted at `release_readiness._repo_root`, `versioning.resolve_version`, `security_hardening._load_scan_secrets`, `host_capability_registry.DEFAULT_MATRIX_PATH`); (d) docstring, comment or message; (e) DEFERRED with a carrier (`engine.plan_uninstall`, `engine.uninstall_repo`, `project_layout.uninstall_system_tree`, `cli._offer_deep_cleanup` to `xoy5yg`; `install_wizard.render_pre_write_plan` text to `3m8aix`; `layout_inventory`/`layout_migration` migration inventory, declined in Deferred). Write the table into V-06.
  - Depends on: E-05
  - Expected outcome: A complete table where class (a) target-side constructions remain only inside `project_system_dir` and `_system_member_destination`, and each class (e) row names its carrier.
  - Execution state: pending

- [ ] E-07 Prove `tracked` parity and the fix: repeat the E-01 `private-target` install with the changed code and diff `git ls-files --stage`, the `.aw/system` file list and `managed-sections.json` against the baseline (must be empty diffs); in THIS repository diff `aw doctor --json` and `aw check all --json` before and after (`check all` rejects `--format` with exit 2), after NORMALIZING (drop `data.elapsed_ms` and other timing keys, sort `diagnostics` and `next_actions` as `json.dumps(..., sort_keys=True)` strings), plus `aw status --json` with `data...git.ahead`/`behind` dropped (it changes as commits land); first run each normalized command twice at the BASE commit to prove the control diff is empty (measured at review: two `aw status --json` runs differed only in `git.ahead`; two `check all --json` runs differed in `elapsed_ms` and `next_actions` order); run `python3 -m pytest -o addopts="" tests/test_system_root_accessor.py tests/test_clean_target_config_home.py tests/test_installer.py -q`; mutation proof (make `project_system_dir` always return `<repo>/.aw/system`; the clean-delta tests must fail; restore); then the bare suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: Empty parity diffs; narrowed tests pass; mutation red then green; bare suite shows no failure that does not also fail on the base commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context.py` is PURE ("PURE: ZERO filesystem writes, directory creation, or Git mutation."). Both accessors share `kfnfji`'s single memoized resolution (`_stored_physical_classes`, generalized here to gate per root class); this child depends on `executed:kfnfji` so the two never edit `project_context.py` concurrently (brief, Set layout).
- Routing reads the STORED policy and `physical_classes`; never preset names (irjoga PR-003/PR-004). `resolve_project_context` puts `system` in tree exactly when the resolved `delivery_mode` is `tracked` (`system_root` branch: `elif resolved_delivery_mode == DeliveryMode.TRACKED.value`), unless `local.json` binds `system_root`. A clean-delta resolution raises `PathSecurityError` if any root lies inside the target ("Clean-delta security violation"), so the accessor cannot return an in-target path for clean-delta.
- Manifest keys are repo-relative logical member names (`manifest.DEFAULT_MANIFEST_RELPATH`, `engine.collect_source_members` emits `.aw/system/...`); keeping them logical is what lets one manifest shape serve both placements.
- Suite: bare `python3 -m pytest`; narrowed runs with `-o addopts=""`; outcome tests only (P16). Install fixtures: temp `HOME`/`AW_HOME`, unset `XDG_CONFIG_HOME`/`AW_CONFIG_DIR`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*` set (the irjoga Step 0 fixture recipe, as in `tests/test_clean_target_config_home.py`).
- Commit through `aw commit 4gn1ka -- <paths>`; never `git add -A`; never push.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `agent_workflows/` census | At HEAD `57d5e8184`: `rg -o '\.aw/system\|"\.aw" / "system"\|"\.aw", "system"' agent_workflows --glob '*.py' \| wc -l` = 122 occurrences across 26 files (largest `engine.py` 36 lines, `layout_inventory.py` 5, `clean_delta.py` 8, `cli.py` 8, `release_readiness.py` 6, `check_engine.py` 6). An AST classification of string constants gives 39 code literals, 29 docstrings, 27 comments and 54 `"system"` segments (24 of those in `layout_inventory.py`'s migration tables). Most are logical names or source side; the target-side location deciders are the ones listed in E-03/E-04/E-05. |
| F-02 | High | `engine.write_file`, `engine._stage_installed_file`, `engine.prune_stale` | `destination = plan.repo_root / relative_posix` and staging `git add -- <relative_posix>` unconditionally. Routing the destination outside the repo without gating staging would make `git add` fail on a missing pathspec and abort the install, so destination mapping and the staging gate must change together (E-04). |
| F-03 | High | `manifest.resolve_manifest_path`, `engine.read_installed_version`, `check_engine.check_system_layout` | All three probe only `<repo>/.aw/system/...` (and legacy). `check_system_layout` is gated on `read_installed_version`, `aw status` (`cli._run_list`, `cli._repos_for_report`) and `aw doctor` (`doctor.probe_environment`) report it, so a home bundle would read as "not installed" everywhere until E-03. `doctor.py` needs no edit: it consumes `read_installed_version`. |
| F-04 | Medium | `engine.resolve_target_layout`, `engine.detect_split_brain_layout`, `compat_migration.CompatMigrator.detect_state`, `cli._handle_legacy_migration` | Layout classification tests `(repo_root / AW_SYSTEM_DIR).exists()`. With an external bundle and a legacy `.agents/workflows` tree in the target, these would misclassify the repo as legacy-only and offer a migration. |
| F-05 | Medium | `upgrade_rehearsal.installed_version`, `detect_layout`, `manifest_summary` | The probe runs IN PROCESS while `upgrade_rehearsal.sandbox_env` redirects `AW_HOME` only for the sandboxed subprocesses, so the probe must pass the sandbox AW_HOME explicitly or it would consult the operator's real home. |
| F-06 | Low | `release_readiness`, `_compat`, `versioning.resolve_version`, `security_hardening._load_scan_secrets`, `host_capability_registry.DEFAULT_MATRIX_PATH` | These root at the toolkit's own package or checkout (`release_readiness._repo_root` is `Path(__file__).resolve().parent.parent`; `_compat.SYSTEM_DATA_RELATIVE = ("_data", ".aw", "system")`), never at a target, so they are correct as is (class c in E-06). |
| F-08 | High | `resolve_project_context` delivery-mode provenance | Plan-review measurement with temp `HOME`/`AW_HOME`: `{"role":"target"}` -> `tracked` from `builtin_defaults` (system in tree); stored `{"preset":"completely-clean-target"}` -> `clean-delta` labelled `project_durable_config` (home system); stored `{"preset":"local-only"}` with no `delivery_mode` -> `tracked` from `builtin_defaults` (system in tree, because only the clean-target preset derives clean-delta in the resolver; the installer always writes `delivery_mode`, so real installs are unaffected); stored `{"delivery_mode":"tracked","records_backend":"home"}` -> system in tree. The `system` gate must therefore key on the delivery-mode provenance and not on `kfnfji`'s records-backend provenance. |
| F-09 | Medium | `upgrade_rehearsal.sandbox_env` | AW_HOME = `<sandbox>/.aw-upgrade-test/aw-home` is inside the sandbox repo; with a stored clean-delta policy the resolver raises `PathSecurityError` ("system root ... is inside target repository"), measured at review. |
| F-10 | Low | real install at review | `aw install <t> --preset completely-clean-target -y --no-interactive` (temp HOME/AW_HOME, HEAD `23863c32a`): exit 0, `Changes committed: a1bfc04`, `git ls-files \| grep -c '^.aw/system/'` = 161, `<AW_HOME>/projects/<id>/` holds only `config` and `state`, the resolver gives `system` = `<AW_HOME>/projects/<id>/system`; `cli._run_install` calls `install_wizard.persist_project_policy` BEFORE `cli._install_one`, so the stored policy is visible to the accessor at write time. |
| F-07 | Low | shipped surface | `git show v1.3.0-rc.1:agent_workflows/project_schema.py` fails ("exists on disk, but not in 'v1.3.0-rc.1'"): the clean-target presets have never shipped in a tagged release, so no released install has an in-tree bundle under a stored `clean-delta` policy that would need migrating (OQ-01). |

## Proposed changes (ordered, validatable)

1. E-01: census, tracked and clean-target install baselines, failing tests.
2. E-02: `project_system_dir` on `kfnfji`'s memoized resolution, generalized to gate per root class (system keyed on delivery-mode provenance or a `system_root` binding, F-08); caller-spelling preservation for in-tree results; resolver errors propagate uncached.
3. E-03: read side (manifest, version, layout and split-brain detection, compat state, emitted layout, `aw layout`, system provider).
4. E-04: write side through `_system_member_destination` with the in-tree-only staging gate; logical manifest keys.
5. E-05: rehearsal probe with the sandbox AW_HOME, degrading honestly on the in-sandbox clean-delta `PathSecurityError` (F-09).
6. E-06: residual classification table.
7. E-07: tracked parity diffs, normalized in-repo diffs with a control run, mutation proof, bare suite.

## Deferred / out of scope (with reason)

- Suppressing target host adapters, `AGENTS.md`, `.gitignore`, `.aw/.gitignore`, `.gitleaksignore`, secret-scan CI, setup marker, installer backups and the auto-commit for clean-delta, and the consent text in `install_wizard.render_pre_write_plan`:
  - Carrier: 3m8aix
- Uninstall of a home bundle (`engine.plan_uninstall`, `engine.uninstall_repo`, `project_layout.uninstall_system_tree`, `cli._offer_deep_cleanup`):
  - Carrier: xoy5yg
- Recognizing a project whose only `.aw` is at home (`project_context.find_project_root`, `is_project_dir`, `doctor.probe_environment` `has_aw`, `cli._collect_repo_status_details`):
  - Carrier: fnnwj3
- Records routing (`project_records_dir` and its readers):
  - Carrier: kfnfji
- Layout migration and inventory (`layout_inventory`, `layout_migration`): they move an existing in-tree legacy layout by design.
  - Carrier-Declined: a clean-target project has no in-tree layout to migrate; changing what migration moves is a separate design decision outside backlog kvwwt0.
- `aw upgrade-test` with a clean-delta sandbox under its DEFAULT in-sandbox AW_HOME (F-09): making that rehearsal exercise the home bundle requires moving the sandbox AW_HOME outside the sandbox directory, which changes `upgrade_rehearsal`'s containment invariant (everything inside the sandbox) and its cleanup.
  - Carrier-Declined: the clean-target presets have never shipped (F-07), so no user rehearses an upgrade of one; E-05 makes the probe degrade honestly (`system_root_error`) instead of crashing; changing the containment invariant is a separate design decision outside backlog kvwwt0.
- How a host agent discovers an external bundle with no in-repo pointer (user-scope adapters): spec `or061f` (deferred) owns global host delivery.
  - Carrier-Declined: user-scope host adapter delivery is a separate feature specified in deferred spec or061f; this child only makes the toolkit's own readers find the bundle.

## Scope check

- Over-scope: none. Each scoped module holds a target-side system location decision (F-02..F-05); the test file and this plan record the evidence.
- Under-scope: the census is re-derived at E-06; any further target-side decider found there is converted here and justified at finalize with `--scope-reason`, unless it belongs to a carrier above.

## Required tests / validation

- `tests/test_system_root_accessor.py` (new): accessor unit tests (E-02); subprocess `aw install --preset completely-clean-target -y` asserting the home bundle files exist, no `.aw/system` path in `git ls-files` or `git status --porcelain --ignored`, `aw doctor --json` (cwd = target) and `aw list-repos --json` (target registered in the temp user config) report the installed version, `aw check all` has no `check.system-layout-missing`, a second install is a no-op for the bundle, and an injected stale home member is pruned; subprocess `aw install --preset private-target -y` asserting the in-tree bundle and staging are unchanged.
- Tracked parity diffs (E-07) and normalized in-repo `aw status --json`/`aw doctor --json`/`aw check all --json` diffs with a base-commit control run.
- Mutation proof on `project_system_dir`; bare `python3 -m pytest`.

## Spec / documentation sync

- N/A in this child: spec 20260810-1447-01 Section 4.1 already says `system/` is "Tracked only when policy says `target-tracked` or role is `source-checkout`; otherwise external and untracked from target"; this plan makes the code obey it. The Section 4/5 amendment and the CHANGELOG `- Fixed:` bullet for the Set are owned by `nwporz`.

## Open questions

### OQ-01: Should the accessor prefer an existing in-tree `.aw/system` over the stored clean-delta placement (irjoga's proposed step 1)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The maintainer rule is to read the STORED policy and `physical_classes`, never to re-derive (brief; irjoga PR-003/PR-004). An in-tree bundle under a stored clean-delta policy exists only from the pre-fix buggy install, and F-07 shows the presets never shipped in a tagged release, so no released install needs that fallback. Preferring an in-tree bundle would also keep the target delta alive forever on such a repo. A re-install after this plan writes the home bundle; removing a stale in-tree one is uninstall territory (`xoy5yg`).

### OQ-02: Should manifest keys become paths relative to the system root instead of logical `.aw/system/...` member names?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `engine.collect_source_members`, `engine.in_framework_namespace` and the uninstall sweep all key on `.aw/system/...` member names; keeping them logical leaves `managed-sections.json` byte-identical for tracked installs (E-07 parity) and makes the destination a pure function of `_system_member_destination`. Re-keying would be a manifest schema change with migration cost and no user benefit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted census output, pasted tracked-baseline capture commands with file counts, pasted clean-target baseline showing the count of `.aw/system/` paths in `git ls-files` and the missing home `system/`, and pasted `python3 -m pytest -o addopts="" tests/test_system_root_accessor.py -q` output with the expected failures.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/project_context.py` showing only `project_system_dir` and the per-class gate generalization of `_stored_physical_classes` (no write calls, no second cache), the pasted `kfnfji` records-accessor unit tests still passing, and pasted narrowed pytest output of the accessor unit tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output (reachable via `cli._run_list` -> `engine.read_installed_version` for `aw list-repos --json` on the registered fixture, `doctor.probe_environment` -> `engine.read_installed_version` for `aw doctor --json` with cwd = the fixture, and `check_engine.check_system_layout` for `aw check all --dir <fixture>`) on a stored clean-delta fixture whose bundle lives ONLY under the home system dir (the in-tree `.aw/system` removed), showing the installed version and no `check.system-layout-missing`, plus the same commands on the unmodified code showing "not installed"/null.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted subprocess output (reachable via `cli._run_install` -> `cli._install_one` -> `engine.install_into_repo` -> `engine.write_file`) of `aw install <t> --preset completely-clean-target -y`, then pasted `find <AW_HOME>/projects/<id>/system -maxdepth 1`, `git -C <t> ls-files | grep -c '^.aw/system/'` (0), a second install's output showing the bundle current, and the stale-member prune.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted rehearsal probe output (reachable via `upgrade_rehearsal.probe` -> `installed_version`/`manifest_summary`) for a clean-delta sandbox with an external AW_HOME showing the home bundle version and manifest row count, for a clean-delta sandbox with the default in-sandbox AW_HOME showing completion plus `system_root_error`, and for a tracked sandbox showing values identical to the pre-change run.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: The pasted re-run census and the complete classification table (classes a to e, carrier id6 for every class e row), plus, if the residual exceeded the RIGHT-SIZING threshold, the pasted `aw backlog new ... --apply` output naming the follow-on id6.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: The pasted normalization script, pasted empty base-commit control diffs, pasted empty parity diffs (tracked install and normalized in-repo commands), pasted narrowed pytest output, pasted mutation-red and restore-green output, and the pasted summary line of the bare `python3 -m pytest` (any failure shown to fail identically on the base commit).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

RIGHT-SIZING NOTE. Eight production modules, but the edit set is small and concentrated: about a dozen target-side deciders, most in `engine.py`. E-03 (read side) and E-04 (write side) must land in that order so that every intermediate commit leaves a tracked install working. If E-06 finds more than about 10 additional target-side deciders, do not widen this pass: commit the completed groups, file the remainder as ONE release-gated follow-on backlog item (`aw backlog new --work-kind bug ... --apply`, then `aw backlog set <id6> --blocks-release next`), record it as class (e) rows in V-06 naming that id6, and continue to E-07.

Execute only after `kfnfji` is executed (Item-Dependencies) and after human approval (`aw ipd set approved 4gn1ka --by-human`). Execute in an isolated worktree via `aw work begin 4gn1ka` (or under `aw oc run`), then `aw ipd begin 4gn1ka`, and perform E-01..E-07 in order. Commit per task group through `aw commit 4gn1ka -- <paths>`, verifying `git diff --cached --name-only` first; never `git add -A`, never push, never tag. HONESTY: every `V-*` pastes ACTUAL output. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is justified at finalize with `--scope-reason`. Post-gate: `aw ipd lint --phase pre-transition` must conform; under a runner the runner finalizes, by hand run `aw ipd finalize 4gn1ka`. Inherits `- Blocks-Release: next` from `kvwwt0`.
