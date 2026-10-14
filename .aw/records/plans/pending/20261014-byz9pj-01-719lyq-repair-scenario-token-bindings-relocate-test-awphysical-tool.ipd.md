# IPD: Repair scenario-token bindings, relocate test_awphysical_tools into tests, and drop collection exemption

- Date: 2026-10-14
- Kind: child
- Concern: `tools/awphysical/test_awphysical_tools.py` sits outside `pyproject.toml` `testpaths = ["tests"]` (and outside `Makefile` `test`/`test-all` and `.github/workflows/tests.yml`), so no standard gate collects it (`tests.test_uncollected_test_modules.EXEMPT` carries a temporary exemption owned by backlog `byz9pj`). Running the module directly reports `1 failed, 30 passed`: `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` fails on the first alphabetical token (`acknowledged-remote`) because commit `19313eed7` removed four test modules (`tests/test_acceptance_matrix.py`, `tests/test_layout_migration.py`, `tests/test_awphysical_migration.py`, `tests/test_awphysical_routing.py`) to which 117 of the 139 tokens in `tools/awphysical/scenario-token-bindings.json` were bound, while the remaining 22 tokens bind by dotted name to `tools.awphysical.test_awphysical_tools.*`.
- Scope: Relocate `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py` (adjusting its `TOOLS_DIR` and fixture path anchors), add focused behavioral test methods in `tests/test_awphysical_tools.py` for the scenario tokens whose behavioral coverage was lost when commit `19313eed7` deleted their host modules, rewrite `tools/awphysical/scenario-token-bindings.json` so all 139 tokens bind to real collected test methods under `tests/`, update `tools/awphysical/README.md`, and remove the `"tools/awphysical/test_awphysical_tools.py"` exemption from `tests/test_uncollected_test_modules.py`.
- Scope-Paths: tools/awphysical/test_awphysical_tools.py, tests/test_awphysical_tools.py, tools/awphysical/scenario-token-bindings.json, tools/awphysical/README.md, tests/test_uncollected_test_modules.py
- Item-Dependencies: none
- Status: to-review
- From-Backlog: byz9pj
- Work-Kind: followup
- Priority: medium
- Set: byz9pj
- Order: 1
- Highest E allocated: 06
- Author: antigravity
- Id: 719lyq

## Workflow history
- 2026-10-14 to-review (aw set): authored review-ready IPD from backlog byz9pj

- 2026-10-14 draft (antigravity): created.

## Goal

Bring the `awphysical` tool and scenario-binding tests under every standard test gate, green, by relocating `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py`, restoring behavioral test coverage for the scenario tokens orphaned by commit `19313eed7` while re-pointing already-covered tokens to live `tests.*` methods in `tools/awphysical/scenario-token-bindings.json`, and removing the `tools/awphysical/test_awphysical_tools.py` exemption from `tests/test_uncollected_test_modules.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Record baseline and relocate the module into tests/

- [ ] E-01 Record the pre-execution baseline at starting HEAD: run `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py`, `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"`, a one-liner counting loadable vs unloadable bindings across all 139 entries in `tools/awphysical/scenario-token-bindings.json`, and a bare `python3 -m pytest` run (recording the summary line, wall time, and any failing test node IDs).
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py` reports `1 failed, 30 passed` failing on `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` (`acknowledged-remote`), collected count for `tests/test_awphysical_tools.py` is `0`, the binding audit reports `22` loadable `tools.awphysical.test_awphysical_tools.*` bindings and `117` unloadable `tests.*` bindings across 39 deleted methods, and the bare-suite baseline is recorded.
  - Execution state: pending

- [ ] E-02 Relocate `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py` via `git mv` and update its internal path and module references for `tests/`: set `TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "awphysical"`, change the seven fixture lookups in `InventoryTests.test_e01` through `InventoryTests.test_e07` from `Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"` to `Path(__file__).resolve().parent / "fixtures"`, update `ScenarioBindingTests.test_bad_binding_is_rejected` to resolve `"tests.test_awphysical_tools.InventoryTests.test_e01"`, and update `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` to collect all broken bindings into a list before asserting `self.assertEqual(problems, [])`.
  - Depends on: E-01
  - Expected outcome: `git status --short -M` shows `R  tools/awphysical/test_awphysical_tools.py -> tests/test_awphysical_tools.py`, all 30 non-`test_every_binding_loads_a_real_test_method_and_names_an_assertion` tests in `tests/test_awphysical_tools.py` pass when run with `python3 -m pytest -o addopts="" -k "not test_every_binding_loads_a_real_test_method_and_names_an_assertion" tests/test_awphysical_tools.py`, and `test_every_binding_loads_a_real_test_method_and_names_an_assertion` reports all unloadable bindings at once rather than stopping at `acknowledged-remote`.
  - Execution state: pending

### Task group 2: Restore behavioral test coverage for orphaned scenario tokens

- [ ] E-03 Add `ScenarioContractBehaviorTests(unittest.TestCase)` in `tests/test_awphysical_tools.py` with nine focused behavioral test methods exercising the real `agent_workflows` APIs for the 68 scenario tokens whose prior test methods in `tests/test_acceptance_matrix.py`, `tests/test_awphysical_migration.py`, and `tests/test_layout_migration.py` were removed in commit `19313eed7` and have no existing counterpart in `tests/`: `test_companion_durability_and_remote_acknowledgement`, `test_setup_marker_lifecycle_and_dismissal`, `test_clean_delta_and_external_record_routing`, `test_conservative_uninstall_preserves_config_state_and_external_records`, `test_migration_planning_dry_run_and_wizard_decline_make_no_mutations`, `test_transactional_move_switches_authority_and_loads_system`, `test_rollback_restores_legacy_and_cleanup_refuses_changed_content`, `test_crash_mid_move_is_resumable`, and `test_fault_injection_before_switch_keeps_legacy_authoritative` (as specified in `## Proposed changes (ordered, validatable)`).
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py -k ScenarioContractBehaviorTests` passes all 9 behavioral tests in under 2 seconds with zero code-pinning.
  - Execution state: pending

### Task group 3: Rewrite scenario-token-bindings.json to resolve all 139 tokens

- [ ] E-04 Rewrite `tools/awphysical/scenario-token-bindings.json` so its `"note"` field cites `tests.test_awphysical_tools.ScenarioBindingTests` and all 139 token bindings resolve to collected test methods under `tests/` while keeping every token's `"assertion"` string unchanged, following the exact mapping table in `## Proposed changes (ordered, validatable)` (22 tokens updated from `tools.awphysical.test_awphysical_tools.*` to `tests.test_awphysical_tools.*`, 49 tokens re-pointed to 15 live test methods across `tests/test_installer.py`, `tests/test_record_producers.py`, `tests/test_project_layout.py`, `tests/test_project_context.py`, `tests/test_project_registry.py`, `tests/test_records_untracked_backend.py`, and `tests/test_cli.py`, and 68 tokens bound to the 9 `tests.test_awphysical_tools.ScenarioContractBehaviorTests.*` methods).
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py` passes all 40 tests (`31` original + `9` in `ScenarioContractBehaviorTests`), including `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`.
  - Execution state: pending

### Task group 4: Update documentation and remove the uncollected-module guard exemption

- [ ] E-05 Update the `test_awphysical_tools.py` bullet in `tools/awphysical/README.md` (`## Files`) to point to `tests/test_awphysical_tools.py`, and remove the `"tools/awphysical/test_awphysical_tools.py"` key from `tests.test_uncollected_test_modules.EXEMPT` in `tests/test_uncollected_test_modules.py`.
  - Depends on: E-04
  - Expected outcome: `git grep -n "tools/awphysical/test_awphysical_tools\|tools\.awphysical\.test_awphysical_tools" -- agent_workflows tests tools` exits `1` with no matches, and `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` passes all collected tests.
  - Execution state: pending

### Task group 5: Verify collection and bare test suite

- [ ] E-06 Verify that `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"` reports `40`, run every external test module targeted by `tools/awphysical/scenario-token-bindings.json` (`python3 -m pytest -o addopts="" -q tests/test_awphysical_tools.py tests/test_uncollected_test_modules.py tests/test_project_layout.py tests/test_project_context.py tests/test_project_registry.py tests/test_record_producers.py tests/test_records_untracked_backend.py`), and run the bare test suite `python3 -m pytest`, comparing the result and any failing test node IDs against the `E-01` baseline.
  - Depends on: E-05
  - Expected outcome: collect-only count for `tests/test_awphysical_tools.py` is `40`, all targeted modules pass with `0 failed`, and the bare `python3 -m pytest` run completes with no new failing test node IDs relative to the `E-01` baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite execution contract (`AGENTS.md` repo-local section): run the full suite bare as `python3 -m pytest`, where `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Narrowed verification runs that need `-v` or `--collect-only` clear `addopts` explicitly via `-o addopts=""`.
- Collection gates (`pyproject.toml` `testpaths = ["tests"]`, `Makefile` `test`/`test-all`, `.github/workflows/tests.yml`, and `tests/test_uncollected_test_modules.py` added by executed plan `5s31xp`): placing `test_awphysical_tools.py` directly under `tests/` causes every standard gate to collect it with no gate-configuration edit, and `tests/test_uncollected_test_modules.py` fails closed if a stale exemption remains in `EXEMPT` after the file moves.
- Test outcomes, not code structure (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES` P16): tests must exercise real functions, CLI commands, or subprocesses and assert on observable outputs, return values, exceptions, and filesystem/git side effects; never inspect production source text for string anchors.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at starting HEAD `9bd7f2b3c` in this lane.

| # | Finding | Evidence |
|---|---|---|
| F-01 | Sibling plan `5s31xp` (backlog `n8adhb`) and sibling plan `g0u7f9` (backlog `gte0pd`) have already executed on `main` (`9bd7f2b3c` and `b417e9c2d`). `tests/test_uncollected_test_modules.py` is live and its `EXEMPT` dict holds only three entries: `tools/awphysical/test_awphysical_tools.py` (owned by `byz9pj`), `tools/aw_upgrade_test.py`, and `tests/test_lift_drift_scan.py`. | `tests.test_uncollected_test_modules.EXEMPT`; `git log -n 5 --oneline`. `- Item-Dependencies:` is therefore `none`. |
| F-02 | `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` failed on `acknowledged-remote` only because it asserts inside a `for token, b in sorted(bindings.items()):` loop and aborts on the first alphabetical token. Auditing all 139 tokens in `tools/awphysical/scenario-token-bindings.json` shows 22 tokens bound to 10 methods in `tools.awphysical.test_awphysical_tools.*` (all loadable) and 117 tokens bound to 39 methods across 4 modules removed by commit `19313eed7`: `tests.test_acceptance_matrix` (24 methods, 68 tokens), `tests.test_layout_migration` (8 methods, 30 tokens), `tests.test_awphysical_migration` (6 methods, 15 tokens), and `tests.test_awphysical_routing` (1 method, 4 tokens). | `tools/awphysical/scenario-token-bindings.json` and `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` in `tools/awphysical/test_awphysical_tools.py`; `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`. |
| F-03 | Why the 117 broken bindings went undetected during commit `19313eed7`: two tests originally enforced `tools/awphysical/scenario-token-bindings.json` — `tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e06` (deleted in `19313eed7`) and `tools.awphysical.test_awphysical_tools.ScenarioBindingTests` (uncollected because `tools/awphysical/` is outside `testpaths = ["tests"]`). | Module docstring of `19313eed7^:tests/test_acceptance_matrix.py` ("checked by `PhysicalLayoutAcceptanceTests.test_e06` below and again by `tools.awphysical.test_awphysical_tools.ScenarioBindingTests`"). |
| F-04 | Of the 117 unloadable token bindings (39 deleted methods), 49 tokens (across 16 deleted methods) assert behaviors that are ALREADY exercised and asserted by 15 live test methods in `tests/` (`tests.test_installer`, `tests.test_record_producers`, `tests.test_project_layout`, `tests.test_project_context`, `tests.test_project_registry`, `tests.test_records_untracked_backend`, `tests.test_cli`). In particular, `tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e03` inspected source files for string anchors (a code-pinning pattern retired by `GUIDING_PRINCIPLES` P16), while its non-pinning routing/inventory properties live in `tests.test_record_producers.{ProducerInventoryTests,RoutingResolutionTests}`. | Verified by resolving and inspecting all 15 live test methods in `tests/` against each token's `"assertion"` string in `tools/awphysical/scenario-token-bindings.json`. |
| F-05 | The remaining 68 tokens (across 23 deleted methods) assert behavioral contracts of `MigrationManager` (dry-run planning, transactional move-verify-switch, git staging plan separation, pre-switch fault injection safety, mid-move crash resume, rollback, cleanup refusal, conservative `uninstall_layout`), `CleanDeltaManager.install_clean_delta` (zero target writes), `storage` (`get_storage_status`, `init_records_storage`, `acknowledge_remote_durability` on `companion`), `engine.write_setup_marker`/`remove_setup_marker` + `attention.setup_needed` dismissal, and `resolve_record_routing` on `home` backend that lost their direct tests in commit `19313eed7`. | Confirmed via `git grep` across `tests/` (`resume_migration`, `status_migration`, `cleanup_migration`, `plan_migration`, `uninstall_layout`, `CleanDeltaManager`, `remove_setup_marker`, `acknowledge_remote_durability` have zero live calls in `tests/`) and `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`. Consolidating them into 9 behavioral test methods in `ScenarioContractBehaviorTests` inside `tests/test_awphysical_tools.py` restores real behavioral coverage for all 68 tokens in ~0.9s total runtime. |
| F-06 | Relocating `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py` requires three internal path/FQN adjustments in the moved file: (1) `TOOLS_DIR = Path(__file__).resolve().parent` must become `Path(__file__).resolve().parent.parent / "tools" / "awphysical"`; (2) the seven `fx = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / ...` expressions in `InventoryTests.test_e01`..`test_e07` must become `Path(__file__).resolve().parent / "fixtures" / ...` (because at depth 2 under `tests/`, `.parent.parent.parent` climbs above the repo root); and (3) the positive control in `ScenarioBindingTests.test_bad_binding_is_rejected` must resolve `"tests.test_awphysical_tools.InventoryTests.test_e01"`. | Direct inspection of `TOOLS_DIR`, `InventoryTests.test_e01`..`test_e07`, and `ScenarioBindingTests.test_bad_binding_is_rejected` in `tools/awphysical/test_awphysical_tools.py`. |
| F-07 | Outside `.aw/records/`, the only other reference to `test_awphysical_tools` is the file-list bullet in `tools/awphysical/README.md` (`- \`test_awphysical_tools.py\`: isolated tests for the three Python tools.`). | `git grep -n "test_awphysical_tools" -- ':!.aw/records'`. |

## Proposed changes (ordered, validatable)

1. **Relocate and update path anchors in `tests/test_awphysical_tools.py` (`E-02`)**:
   - `git mv tools/awphysical/test_awphysical_tools.py tests/test_awphysical_tools.py`.
   - Update `TOOLS_DIR` to `Path(__file__).resolve().parent.parent / "tools" / "awphysical"`.
   - Update the seven fixture path expressions in `InventoryTests.test_e01` through `InventoryTests.test_e07` to `Path(__file__).resolve().parent / "fixtures" / "awphysical" / "order06" / ...`.
   - Update `ScenarioBindingTests.test_bad_binding_is_rejected` positive control to `self._resolve("tests.test_awphysical_tools.InventoryTests.test_e01")`.
   - Update `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` to collect all failing tokens (`bad_fqn`, `unloadable`, `missing_assertion`) across `sorted(bindings.items())` and assert `self.assertEqual(problems, [])`.

2. **Add `ScenarioContractBehaviorTests` in `tests/test_awphysical_tools.py` (`E-03`)**:
   - `test_companion_durability_and_remote_acknowledgement`: configures `records_backend="companion"`, verifies `get_storage_status` reports `DurabilityState.UNVERSIONED.value` before git init, calls `init_records_storage` and verifies `DurabilityState.LOCAL_GIT.value` (not `acknowledged-durable`), attaches a local bare remote with an initial pushed commit to verify `DurabilityState.UNACKNOWLEDGED_REMOTE.value`, and calls `acknowledge_remote_durability(..., acknowledge=True)` to verify `remote_acknowledged is True` and `DurabilityState.ACKNOWLEDGED_DURABLE.value`.
   - `test_setup_marker_lifecycle_and_dismissal`: verifies `attention.setup_needed` is `False` on a fresh repo, `True` after `engine.write_setup_marker`, `False` after `engine.remove_setup_marker`, `False` (and marker not recreated on read) after unlinking `.aw/setup-repo-needed.md`, and `True` again when `engine.write_setup_marker` re-creates the marker.
   - `test_clean_delta_and_external_record_routing`: verifies `CleanDeltaManager.install_clean_delta("opencode", "1.0.0", user_skills_dir=...)` reports `target_writes == 0`, and that `resolve_record_routing` with `records_backend="home"` places `records_root` outside `target_repo` with `allow_git_stage is False`.
   - `test_conservative_uninstall_preserves_config_state_and_external_records`: populates `.aw/system`, `.aw/config/policy.json`, `.aw/state`, `.aw/records/sample.md`, and an external record under `aw_home`, runs `MigrationManager.uninstall_layout(preserve_records=True, deep_remove_records=False)`, and verifies `.aw/system` is removed while `.aw/config`, `.aw/state`, `.aw/records/sample.md`, and the external record are preserved.
   - `test_migration_planning_dry_run_and_wizard_decline_make_no_mutations`: seeds a legacy `.agents/` repo, verifies `MigrationManager.plan_migration(target_backend="repository")` returns a valid plan with `available_bytes > 0` without creating `.aw/`, and verifies `cli.main(["migrate-layout"])` with declined confirmation (`"1\n1\nn\n"`) returns `1` without creating `.aw/` or mutating `.agents/`.
   - `test_transactional_move_switches_authority_and_loads_system`: runs `MigrationManager.execute_migration(target_backend="repository", dry_run=False)` on a seeded `.agents/` repo and verifies legacy sources are moved (not copied) into `.aw/system/workflows/` and `.aw/records/plans/`, `.aw/system/VERSION` is placed as a system-root sibling, `engine.parse_manifest` loads `.aw/system/workflows`, `migration_transaction.json` has `schema_version == 1`, non-empty `transaction_id`, and `git_staging_plans` keys `{"target", "companion", "source"}`, `switch_receipt.json` records `authority == "switched"`, and `git status --short` shows staged renames (`->`).
   - `test_rollback_restores_legacy_and_cleanup_refuses_changed_content`: after `execute_migration`, verifies `cleanup_migration(confirm=False)` returns `status == "preview"` with `would_remove == []` and `cleanup_migration(fault_injection="cleanup-refusal")` raises `CleanupError`; then runs `rollback_migration()` and verifies `status == "rolled_back"`, `authority == "legacy"`, legacy `.agents/` files restored, `.aw/system` and `.aw/records` removed, and `git status --short` free of `->` renames.
   - `test_crash_mid_move_is_resumable`: rewinds the last entry of `move_journal` after `execute_migration` back to its `.agents/` source with transaction `status = "locked"` and `switch_receipt.json` unlinked, calls `MigrationManager.resume_migration()`, and verifies `status == "completed"` with the remaining move completed on disk.
   - `test_fault_injection_before_switch_keeps_legacy_authoritative`: exercises `execute_migration(target_backend="repository", fault_injection=...)` across `stale-input` (`StaleInputError`), `concurrent-writer` (`TransactionLockError`), `disk-loss` (`PreflightGateError`), `permission-loss` (`PreflightGateError`), `copy-failure` (`MigrationError`), `verify-mismatch` (`VerificationError`), `switch-failure` (`SwitchError`), `kill-after-switch-before-receipt` (`MigrationError`), and `cross-git-partial-stage` (`MigrationError`), verifying each raises its expected exception and that none of the seven pre-switch injections writes `switch_receipt.json`.

3. **Rewrite `tools/awphysical/scenario-token-bindings.json` (`E-04`)**:
   - Update `"note"` to cite `tests.test_awphysical_tools.ScenarioBindingTests`.
   - Rewrite the 22 `tools.awphysical.test_awphysical_tools.<Class>.<method>` bindings to `tests.test_awphysical_tools.<Class>.<method>`.
   - Re-bind the 49 tokens covered by existing live `tests.*` methods:
     - `no-source-trust`, `origin-not-identity`, `source-not-overwritten`, `source-specific-diagnostic` -> `tests.test_installer.PhysicalSystemInstallTests.test_physical_source_packaging_and_spoof_protection`
     - `legacy-writer-disabled` -> `tests.test_record_producers.WriteGuardTests.test_a_legacy_agents_write_is_still_rejected`
     - `no-legacy-fallback-write` -> `tests.test_record_producers.ProducerInventoryTests.test_no_known_writer_module_reintroduced_a_legacy_write_sink`
     - `no-development-records`, `owned-system-adapters-only` -> `tests.test_record_producers.ProducerInventoryTests.test_the_legacy_allowlist_still_holds_only_non_writers`
     - `explicit-fallback-not-called-clean` -> `tests.test_record_producers.RoutingResolutionTests.test_legacy_read_paths_resolve_for_a_doc_family_class`
     - `no-stage-attempt` -> `tests.test_record_producers.RoutingResolutionTests.test_git_owner_is_unchanged_for_records_and_runtime`
     - `no-repository-records` -> `tests.test_project_layout.TestProjectLayoutAndOwnership.test_materialize_tracked_home_backend_omits_target_records_dir`
     - `portable-local-separation`, `ordinary-target-role`, `tracked-paths-portable` -> `tests.test_project_context.PhysicalContextResolutionTests.test_e01`
     - `local-config-ignored`, `runtime-ignored` -> `tests.test_project_layout.PhysicalPolicyMatrixTests.test_e01`
     - `durable-material-target-tracked`, `explicit-durability-choice`, `target-tracked-durable` -> `tests.test_project_layout.PhysicalPolicyMatrixTests.test_e03`
     - `actionable-incomplete-policy-diagnostic`, `fail-before-write`, `first-install-eof-fails-closed`, `no-write-before-complete-choice`, `safe-install-or-refusal` -> `tests.test_records_untracked_backend.TestRecordsUntrackedBackend.test_e05_missing_field_hint_and_cli_help`
     - `no-migration-required`, `no-policy-switch`, `no-writes`, `same-version-noop-checkpoint` -> `tests.test_cli.InstallDiagnosticsTests.test_no_change_reinstall_says_already_current`
     - `no-policy-overwrite`, `update-keeps-policy` -> `tests.test_project_layout.TestProjectLayoutAndOwnership.test_config_merge_preserves_unknown_human_keys`
     - `correct-worktree-path`, `local-binding-updated`, `no-reattach-without-explicit-recovery`, `stable-identity`, `stable-project-identity` -> `tests.test_project_registry.TestProjectRegistry.test_cli_project_attach_and_move`
     - `attachment-rejected`, `authority-invalid`, `identity-conflict` -> `tests.test_project_registry.TestProjectRegistry.test_negative_two_projects_shared_origin_no_auto_attach`
     - `external-local-roots` -> `tests.test_project_context.TestProjectContextResolver.test_path_traversal_refusal`
     - `color-auto-always-never`, `no-color-and-term-dumb`, `meaning-never-color-only`, `screen-reader-text-without-color` -> `tests.test_cli.AccessibilityTests.test_no_color_output_has_no_ansi_and_keeps_status_words`
     - `privacy-status-observable-only` -> `tests.test_records_untracked_backend.TestRecordsUntrackedBackend.test_e03_materialize_and_boundaries`
     - `honest-unsupported-result`, `optional-link-absent-or-broken-safe` -> `tests.test_project_context.TestProjectContextResolver.test_section_9_coverage_guard`
     - `fail-closed`, `human-disposition-required`, `human-owned-review` -> `tests.test_cli.Order16MigrateLayoutCliTests.test_migrate_layout_noninteractive_requires_confirmation`
   - Bind the 68 remaining tokens to `tests.test_awphysical_tools.ScenarioContractBehaviorTests.*`:
     - `acknowledged-remote`, `companion-durable`, `private-destination`, `private-durable-bundle`, `durability-action-open`, `durability-action-or-acknowledgement`, `explicit-git-init`, `honest-unversioned-status`, `local-git-not-durable-private`, `unversioned-honest-status` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_companion_durability_and_remote_acknowledgement`
     - `applicable-actions-only`, `setup-action-visible-on-status-surfaces`, `setup-completion-closes-action`, `dismissal-history-no-resurrection`, `action-generations-supersede` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_setup_marker_lifecycle_and_dismissal`
     - `no-candid-public-delta`, `public-system-only`, `host-support-evidence`, `no-target-write`, `zero-target-delta` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_clean_delta_and_external_record_routing`
     - `external-bytes-untouched`, `external-config-state-records`, `external-repo-never-deleted`, `external-runtime`, `external-system`, `config-state-records-preserved` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_conservative_uninstall_preserves_config_state_and_external_records`
     - `all-paths-previewed`, `filesystem-aware-preflight`, `preview-only-default` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_migration_planning_dry_run_and_wizard_decline_make_no_mutations`
     - `bytes-preserved`, `content-not-lost`, `copy-verify-switch-retain`, `explicit-untrack-plan`, `history-preserved`, `no-duplicate-copy`, `no-overwrite`, `all-records-preserved`, `complete-packaged-system`, `correct-version-manifest`, `one-canonical-system-source`, `package-green`, `single-current-schema`, `stable-transaction-id`, `new-authority-explicit`, `never-push`, `separate-git-evidence`, `valid-git-destinations` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_transactional_move_switches_authority_and_loads_system`
     - `byte-identical-rollback`, `git-index-restored`, `journal-retained`, `legacy-preserved`, `policy-restored`, `rollback-ready`, `rollback-safe`, `source-retained`, `changed-content-not-deleted`, `cleanup-blocked`, `cleanup-refused` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_rollback_restores_legacy_and_cleanup_refuses_changed_content`
     - `idempotent-resume`, `recoverable-staging`, `recovery-guidance`, `resume-safe` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_crash_mid_move_is_resumable`
     - `fail-before-switch`, `legacy-authoritative`, `no-switch`, `one-authority`, `safe-fallback-transaction`, `writer-lock-or-hash-drift-stop` -> `tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_fault_injection_before_switch_keeps_legacy_authoritative`

4. **Update `tools/awphysical/README.md` and `tests/test_uncollected_test_modules.py` (`E-05`)**:
   - Update `tools/awphysical/README.md` bullet under `## Files` to reference `tests/test_awphysical_tools.py`.
   - Remove `"tools/awphysical/test_awphysical_tools.py"` from `tests.test_uncollected_test_modules.EXEMPT`.

## Deferred / out of scope (with reason)

- Full deleted-test audit and mutation-proving across all 208 uncited files removed in commit `19313eed7` (including the non-bound methods of `tests/test_layout_migration.py`, `tests/test_awphysical_migration.py`, `tests/test_awphysical_routing.py`, and `tests/test_acceptance_matrix.py`): tracked separately by Set `uncitedaudit` (orchestrator `k93w2g`, pending follow-up `xmr5qj`, backlog `e486tz`).
  - Carrier: k93w2g
- Remaining two exemptions in `tests.test_uncollected_test_modules.EXEMPT` (`tools/aw_upgrade_test.py` and `tests/test_lift_drift_scan.py`): intentional non-unit harnesses (a standalone upgrade harness and a `-m livecorpus` corpus scan), documented in executed plan `5s31xp` and outside `byz9pj`'s scope.
  - Carrier-Declined: intentional non-pytest-default harnesses documented when `EXEMPT` was created in plan `5s31xp`, not defects.

## Scope check

- Over-scope: none. Every file in `Scope-Paths` is required either to relocate `test_awphysical_tools.py`, repair its scenario-token bindings, update its README reference, or drop its exemption from `tests/test_uncollected_test_modules.py`.
- Under-scope: none. Addressing only `acknowledged-remote` would leave 116 other unloadable bindings in `tools/awphysical/scenario-token-bindings.json` failing `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`; this plan resolves all 139 bindings and removes the collection guard exemption.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py`: all 40 tests pass (`V-03`, `V-04`, `V-06`).
- `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py`: all collected tests pass (`V-05`, `V-06`).
- `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"`: returns `40` (`V-06`).
- Bare `python3 -m pytest`: summary line pasted and compared against the `E-01` baseline with zero new failing test node IDs (`V-06`).

## Spec / documentation sync

`tools/awphysical/README.md` (`## Files`) lists `test_awphysical_tools.py` as a local file in `tools/awphysical/` and is updated in `E-05` to reference `tests/test_awphysical_tools.py`. Implemented spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` names only the three production tools (`aw_layout_inventory.py`, `aw_layout_compare.py`, `aw_layout_postcheck.py`) and `migration-scenarios.json`, not `test_awphysical_tools.py` (`git grep -n "test_awphysical_tools" .aw/records/specs/` returns zero matches), so no spec amendment is needed.

## Open questions

### OQ-01: How should the 117 token bindings whose target test modules were removed by commit `19313eed7` be resolved?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Re-bind the 49 tokens whose behavioral assertions are already exercised by live tests in `tests/` (`tests.test_installer`, `tests.test_record_producers`, `tests.test_project_layout`, `tests.test_project_context`, `tests.test_project_registry`, `tests.test_records_untracked_backend`, `tests.test_cli`) directly to those 15 live test methods, and add 9 focused behavioral test methods in `ScenarioContractBehaviorTests` inside `tests/test_awphysical_tools.py` for the 68 tokens whose underlying `MigrationManager`, `CleanDeltaManager`, companion `storage`, `setup-repo-needed.md` lifecycle, and external `home` routing behaviors have no live test in `tests/` (F-04, F-05). This keeps the suite lean (+9 fast behavioral tests running in ~0.9s total), honors `GUIDING_PRINCIPLES` P16 (behavioral outcomes only, not restoring the retired source-anchor pin in `PhysicalProducerRoutingTests.test_e03`), and ensures every one of the 139 bindings in `tools/awphysical/scenario-token-bindings.json` loads a collected test method that genuinely asserts the named condition.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste (1) the starting HEAD short SHA; (2) the output of `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py` showing `1 failed, 30 passed` on `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`; (3) the output of `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"` (`0`); (4) the output of the pre-edit binding audit count (`22` loadable, `117` unloadable); and (5) the bare `python3 -m pytest` baseline summary line, wall time, and any failing test node IDs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git status --short -M` showing `R  tools/awphysical/test_awphysical_tools.py -> tests/test_awphysical_tools.py`, the diff hunks in `tests/test_awphysical_tools.py` for `TOOLS_DIR`, `InventoryTests.test_e01`..`test_e07`, `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`, and `ScenarioBindingTests.test_bad_binding_is_rejected`, and the output of `python3 -m pytest -o addopts="" -q -k "not test_every_binding_loads_a_real_test_method_and_names_an_assertion" tests/test_awphysical_tools.py` showing `30 passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py -k ScenarioContractBehaviorTests` showing all 9 methods in `ScenarioContractBehaviorTests` `PASSED`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py` showing all 40 tests `PASSED` (including `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`), plus a falsification check demonstrating that temporarily corrupting one binding in memory is rejected by `ScenarioBindingTests._resolve`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff -- tools/awphysical/README.md tests/test_uncollected_test_modules.py`, the output and exit code (`1`, zero matches) of `git grep -n "tools/awphysical/test_awphysical_tools\|tools\.awphysical\.test_awphysical_tools" -- agent_workflows tests tools`, and the per-test `-v` output of `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` showing all tests `PASSED`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste (1) the output of `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"` showing `40`; (2) the summary line of `python3 -m pytest -o addopts="" -q tests/test_awphysical_tools.py tests/test_uncollected_test_modules.py tests/test_project_layout.py tests/test_project_context.py tests/test_project_registry.py tests/test_record_producers.py tests/test_records_untracked_backend.py` showing `0 failed`; and (3) the bare `python3 -m pytest` summary line and wall time compared against the `V-01` baseline with zero new failing test node IDs.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved 719lyq --by-human`). Open questions: OQ-01 is resolved; none remain. Start execution with `aw ipd begin 719lyq`.

Scope fence: `- Scope-Paths:` is a DECLARATION reconciled at finalize. If an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>`; if a declared path requires no edit, acknowledge it with `--scope-ack`.

Honesty rule: every `V-*` item MUST paste the ACTUAL runner output; never claim a result you did not run.

Commits: the `git mv` relocation (`tools/awphysical/test_awphysical_tools.py` -> `tests/test_awphysical_tools.py`), the `ScenarioContractBehaviorTests` additions, the `tools/awphysical/scenario-token-bindings.json` and `tools/awphysical/README.md` updates, and the `tests/test_uncollected_test_modules.py` exemption removal MUST land together so no intermediate commit leaves a red collected test or a stale exemption in `EXEMPT`. Commit only the modified paths in `Scope-Paths` through `aw commit 719lyq -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify `git diff --cached --name-only` before committing, and never push.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize 719lyq` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-06` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Once this plan is `executed`, backlog `byz9pj` closes `done` via the runner's `process_backlog_close` (or `aw backlog set done byz9pj` when executed by hand).
