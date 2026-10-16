# IPD: Repair scenario-token bindings, relocate test_awphysical_tools into tests, and drop collection exemption

- Date: 2026-10-14
- Kind: child
- Concern: `tools/awphysical/test_awphysical_tools.py` sits outside `pyproject.toml` `testpaths = ["tests"]` (and outside `Makefile` `test`/`test-all` and `.github/workflows/tests.yml`), so no standard gate collects it (`tests.test_uncollected_test_modules.EXEMPT` carries a temporary exemption owned by backlog `byz9pj`). Running the module directly reports `1 failed, 30 passed`: `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` fails on the first alphabetical token (`acknowledged-remote`) because commit `19313eed7` removed four test modules (`tests/test_acceptance_matrix.py`, `tests/test_layout_migration.py`, `tests/test_awphysical_migration.py`, `tests/test_awphysical_routing.py`) to which 117 of the 139 tokens in `tools/awphysical/scenario-token-bindings.json` were bound, while the remaining 22 tokens bind by dotted name to `tools.awphysical.test_awphysical_tools.*`.
- Scope: Relocate `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py` (adjusting its `TOOLS_DIR` and fixture path anchors), add focused behavioral test methods in `tests/test_awphysical_tools.py` for the scenario tokens whose behavioral coverage was lost when commit `19313eed7` deleted their host modules, rewrite `tools/awphysical/scenario-token-bindings.json` so all 139 tokens bind to real collected test methods under `tests/`, update `tools/awphysical/README.md`, and remove the `"tools/awphysical/test_awphysical_tools.py"` exemption from `tests/test_uncollected_test_modules.py`.
- Scope-Paths: tools/awphysical/test_awphysical_tools.py, tests/test_awphysical_tools.py, tools/awphysical/scenario-token-bindings.json, tools/awphysical/README.md, tests/test_uncollected_test_modules.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Backlog: byz9pj
- Work-Kind: followup
- Priority: medium
- Set: byz9pj
- Order: 1
- Highest E allocated: 06
- Author: antigravity
- Id: 719lyq

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 719lyq verified (set byz9pj, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed (review record 20261014-byz9pj-01-719lyq)
- 2026-10-14 to-review (aw set): authored review-ready IPD from backlog byz9pj

- 2026-10-14 draft (antigravity): created.

## Goal

Bring the `awphysical` tool and scenario-binding tests under every standard test gate, green, by relocating `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py`, restoring behavioral test coverage for the scenario tokens orphaned by commit `19313eed7` while re-pointing already-covered tokens to live `tests.*` methods in `tools/awphysical/scenario-token-bindings.json`, and removing the `tools/awphysical/test_awphysical_tools.py` exemption from `tests/test_uncollected_test_modules.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Record baseline and relocate the module into tests/

- [x] E-01 Record the pre-execution baseline at starting HEAD: run `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py`, `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"`, a binding audit (a short `python3 -` script that loads `tools/awphysical/scenario-token-bindings.json` and resolves each `"test"` value with `importlib.import_module` + `getattr` exactly as `ScenarioBindingTests._resolve` does, printing loadable/unloadable totals and the per-module tally), and a bare `python3 -m pytest` run (recording the summary line, wall time, and any failing test node IDs).
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py` reports `1 failed, 30 passed` failing on `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` (`acknowledged-remote`), collected count for `tests/test_awphysical_tools.py` is `0`, the binding audit reports `22` loadable `tools.awphysical.test_awphysical_tools.*` bindings and `117` unloadable `tests.*` bindings across 39 deleted methods, and the bare-suite baseline is recorded. These counts are the authoring-time measurement and are re-derived, not assumed.
  - Execution state: performed

- [x] E-02 Relocate `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py` via `git mv` and update its internal path and module references for `tests/`: set `TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "awphysical"`, change the seven fixture lookups in `InventoryTests.test_e01` through `InventoryTests.test_e07` from `Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"` to `Path(__file__).resolve().parent / "fixtures"`, update `ScenarioBindingTests.test_bad_binding_is_rejected` to resolve `"tests.test_awphysical_tools.InventoryTests.test_e01"`, and update `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` to collect all broken bindings into a list before asserting `self.assertEqual(problems, [])`.
  - Depends on: E-01
  - Expected outcome: `git status --short -M` shows `R  tools/awphysical/test_awphysical_tools.py -> tests/test_awphysical_tools.py`; every test in `tests/test_awphysical_tools.py` other than `test_every_binding_loads_a_real_test_method_and_names_an_assertion` passes under `python3 -m pytest -o addopts="" -k "not test_every_binding_loads_a_real_test_method_and_names_an_assertion" tests/test_awphysical_tools.py` with `0 failed` (the passing count, 30 at authoring, is recorded as context and is not the bar); and `test_every_binding_loads_a_real_test_method_and_names_an_assertion` still FAILS at this point, its message listing every unloadable binding at once rather than stopping at `acknowledged-remote`.
  - Execution state: performed

### Task group 2: Restore behavioral test coverage for orphaned scenario tokens

- [x] E-03 Add `ScenarioContractBehaviorTests(unittest.TestCase)` in `tests/test_awphysical_tools.py` with nine focused behavioral test methods exercising the real `agent_workflows` APIs for the 70 scenario tokens whose prior test methods in `tests/test_acceptance_matrix.py`, `tests/test_awphysical_migration.py`, `tests/test_layout_migration.py`, and `tests/test_awphysical_routing.py` were removed in commit `19313eed7` and have no live counterpart in `tests/` that asserts the token's named condition: `test_companion_durability_and_remote_acknowledgement`, `test_setup_marker_lifecycle_and_dismissal`, `test_clean_delta_and_external_record_routing`, `test_conservative_uninstall_preserves_config_state_and_external_records`, `test_migration_planning_dry_run_and_wizard_decline_make_no_mutations`, `test_transactional_move_switches_authority_and_loads_system`, `test_rollback_restores_legacy_and_cleanup_refuses_changed_content`, `test_crash_mid_move_is_resumable`, and `test_fault_injection_before_switch_keeps_legacy_authoritative` (each exactly as specified in `## Proposed changes (ordered, validatable)` item 2, including its shared fixture and isolation guardrails).
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py -k ScenarioContractBehaviorTests` reports every `ScenarioContractBehaviorTests` method `PASSED` with `0 failed`; no method reads production source text (behavioral assertions on return values, exceptions, files, and `git status` only). The wall time is recorded as context (about 1s measured by probe at review) and is not a bar.
  - Execution state: performed

### Task group 3: Rewrite scenario-token-bindings.json to resolve all 139 tokens

- [x] E-04 Rewrite `tools/awphysical/scenario-token-bindings.json` so its `"note"` field cites `tests.test_awphysical_tools.ScenarioBindingTests` and all 139 token bindings resolve to collected test methods under `tests/` while keeping every token's `"assertion"` string unchanged, following the exact mapping table in `## Proposed changes (ordered, validatable)` item 3 (22 tokens updated from `tools.awphysical.test_awphysical_tools.*` to `tests.test_awphysical_tools.*`, 47 tokens re-pointed to 22 live test methods across `tests/test_installer.py`, `tests/test_record_producers.py`, `tests/test_project_layout.py`, `tests/test_project_context.py`, `tests/test_project_registry.py`, `tests/test_records_untracked_backend.py`, `tests/test_cli.py`, `tests/test_term.py`, and `tests/test_packaging.py`, and 70 tokens bound to the 9 `tests.test_awphysical_tools.ScenarioContractBehaviorTests.*` methods).
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py` reports every test `PASSED` with `0 failed`, including `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`, `test_every_expected_token_is_bound`, and `test_legacy_crosswalk_assertion_tokens_are_bound`; and a re-derived audit over the rewritten JSON reports 139 bindings, 0 unloadable, 0 bound to a `tools.*` module, and the per-target token tally matching item 3 (the 139 is the manifest's token set, a stable authored fact).
  - Execution state: performed

### Task group 4: Update documentation and remove the uncollected-module guard exemption

- [x] E-05 Update the `test_awphysical_tools.py` bullet in `tools/awphysical/README.md` (`## Files`) to point to `tests/test_awphysical_tools.py`, and remove the `"tools/awphysical/test_awphysical_tools.py"` key from `tests.test_uncollected_test_modules.EXEMPT` in `tests/test_uncollected_test_modules.py`.
  - Depends on: E-04
  - Expected outcome: `git grep -n "tools/awphysical/test_awphysical_tools\|tools\.awphysical\.test_awphysical_tools" -- agent_workflows tests tools` exits `1` with no matches, and `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` passes all collected tests.
  - Execution state: performed

### Task group 5: Verify collection and bare test suite

- [x] E-06 Verify that the default collection (`python3 -m pytest --collect-only -q -o addopts=""`) now includes `tests/test_awphysical_tools.py`, with every `ScenarioContractBehaviorTests` and `ScenarioBindingTests` method present (count recorded as context; it is not the bar), derive the pytest node id of every binding target from the rewritten `tools/awphysical/scenario-token-bindings.json` (`tests.a.B.c` becomes `tests/a.py::B::c`, de-duplicated) and run exactly those node ids with `python3 -m pytest -q -m "not livecorpus" <node ids>` (the `-m` override is required so the slow-marked targets in `tests/test_cli.py` and `tests/test_installer.py` run too; those modules carry `pytestmark = pytest.mark.slow`, so the default gate deselects them and only `make test-all` or the advisory CI slow step would run them), then run `python3 -m pytest -q tests/test_awphysical_tools.py tests/test_uncollected_test_modules.py`, and run the bare test suite `python3 -m pytest`, comparing the result and any failing test node IDs against the `E-01` baseline.
  - Depends on: E-05
  - Expected outcome: `tests/test_awphysical_tools.py` appears in default collection; every derived node id is collected (zero `not found` errors) and passes with `0 failed`; the run lists which bound node ids are slow-marked (11 tokens across the `tests/test_cli.py` and `tests/test_installer.py` targets at review), so the slow-only coverage is visible rather than hidden; the two targeted modules pass with `0 failed`, and the bare `python3 -m pytest` run completes with no new failing test node IDs relative to the `E-01` baseline.
  - Execution state: performed

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
| F-04 | Of the 117 unloadable token bindings (39 deleted methods), 47 tokens assert behaviors that are ALREADY exercised and asserted by 22 live test methods in `tests/` (`tests.test_installer`, `tests.test_record_producers`, `tests.test_project_layout`, `tests.test_project_context`, `tests.test_project_registry`, `tests.test_records_untracked_backend`, `tests.test_cli`, `tests.test_term`, `tests.test_packaging`). As authored this row claimed 49 tokens on 15 methods; plan-review PR-002 found five of those targets did not assert the named condition and re-pointed them (see Proposed changes item 3). In particular, `tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e03` inspected source files for string anchors (a code-pinning pattern retired by `GUIDING_PRINCIPLES` P16), while its non-pinning routing/inventory properties live in `tests.test_record_producers.{ProducerInventoryTests,RoutingResolutionTests}`. | Verified by resolving and inspecting every live target method in `tests/` against each token's `"assertion"` string in `tools/awphysical/scenario-token-bindings.json`. |
| F-05 | The remaining 70 tokens assert behavioral contracts of `MigrationManager` (dry-run planning, transactional move-verify-switch, git staging plan separation, pre-switch fault injection safety, mid-move crash resume, rollback, cleanup refusal, conservative `uninstall_layout`), `CleanDeltaManager.install_clean_delta` (zero target writes), `storage` (`get_storage_status`, `init_records_storage`, `acknowledge_remote_durability` on `companion`), `engine.write_setup_marker`/`remove_setup_marker` + `attention.setup_needed` dismissal, and `resolve_record_routing` on `home` backend that lost their direct tests in commit `19313eed7`. | Confirmed via `git grep` across `tests/` (`resume_migration`, `status_migration`, `cleanup_migration`, `plan_migration`, `uninstall_layout`, `CleanDeltaManager`, `remove_setup_marker`, `acknowledge_remote_durability` have zero live calls in `tests/`) and `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`. Consolidating them into 9 behavioral test methods in `ScenarioContractBehaviorTests` inside `tests/test_awphysical_tools.py` restores real behavioral coverage for all 70 tokens; a review probe of the same API sequences ran in about 1s. |
| F-06 | Relocating `tools/awphysical/test_awphysical_tools.py` to `tests/test_awphysical_tools.py` requires three internal path/FQN adjustments in the moved file: (1) `TOOLS_DIR = Path(__file__).resolve().parent` must become `Path(__file__).resolve().parent.parent / "tools" / "awphysical"`; (2) the seven `fx = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / ...` expressions in `InventoryTests.test_e01`..`test_e07` must become `Path(__file__).resolve().parent / "fixtures" / ...` (because at depth 2 under `tests/`, `.parent.parent.parent` climbs above the repo root); and (3) the positive control in `ScenarioBindingTests.test_bad_binding_is_rejected` must resolve `"tests.test_awphysical_tools.InventoryTests.test_e01"`. | Direct inspection of `TOOLS_DIR`, `InventoryTests.test_e01`..`test_e07`, and `ScenarioBindingTests.test_bad_binding_is_rejected` in `tools/awphysical/test_awphysical_tools.py`. |
| F-08 | (plan-review) Two live target modules carry `pytestmark = pytest.mark.slow`: `tests/test_cli.py` and `tests/test_installer.py`. The default `addopts` `-m 'not slow and not livecorpus'` deselects them, and CI runs `-m slow` only as an advisory `continue-on-error` step, so a token bound there is loadable (and passes `ScenarioBindingTests`) yet is not exercised by the blocking gate. After review re-pointing, 11 tokens remain on slow targets (`no-source-trust`, `origin-not-identity`, `source-not-overwritten`, `source-specific-diagnostic`, `no-writes`, `no-migration-required`, `no-policy-switch`, `same-version-noop-checkpoint`, `fail-closed`, `human-disposition-required`, `human-owned-review`). This is the same exposure those tests already have and is recorded, not fixed, here. | `tests/test_cli.py` and `tests/test_installer.py` (`pytestmark = pytest.mark.slow`); `pyproject.toml` `addopts`; `.github/workflows/tests.yml` step "Run slow-marked tests (ADVISORY ...)". |
| F-07 | Outside `.aw/records/`, the only other reference to `test_awphysical_tools` is the file-list bullet in `tools/awphysical/README.md` (`- \`test_awphysical_tools.py\`: isolated tests for the three Python tools.`). | `git grep -n "test_awphysical_tools" -- ':!.aw/records'`. |

## Proposed changes (ordered, validatable)

1. **Relocate and update path anchors in `tests/test_awphysical_tools.py` (`E-02`)**:
   - `git mv tools/awphysical/test_awphysical_tools.py tests/test_awphysical_tools.py`.
   - Update `TOOLS_DIR` to `Path(__file__).resolve().parent.parent / "tools" / "awphysical"`.
   - Update the seven fixture path expressions in `InventoryTests.test_e01` through `InventoryTests.test_e07` to `Path(__file__).resolve().parent / "fixtures" / "awphysical" / "order06" / ...`.
   - Update `ScenarioBindingTests.test_bad_binding_is_rejected` positive control to `self._resolve("tests.test_awphysical_tools.InventoryTests.test_e01")`.
   - Update `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` to collect all failing tokens (`bad_fqn`, `unloadable`, `missing_assertion`) across `sorted(bindings.items())` and assert `self.assertEqual(problems, [])`.

2. **Add `ScenarioContractBehaviorTests` in `tests/test_awphysical_tools.py` (`E-03`)**:
   - Shared fixture and isolation guardrails (apply to every method): each method builds its own `tempfile.TemporaryDirectory()` holding a fresh `git init` repo (with repo-local `user.email`, `user.name`, `commit.gpgsign=false`) and a private `aw_home` directory; save and restore `os.environ["AW_HOME"]` in `setUp`/`tearDown` exactly as `tests/__init__.py`'s sandbox expects (never `pop` it unconditionally), and restore the working directory after any `os.chdir`. Pass `aw_home=` explicitly to every `MigrationManager`, `CleanDeltaManager`, `storage.*`, and `resolve_record_routing` call. The legacy seed used by the migration methods is `.agents/workflows/index.md` (a resolver-valid manifest: a `# Workflows` heading plus a table between `<!-- WORKFLOWS-MANIFEST:BEGIN -->` and `<!-- WORKFLOWS-MANIFEST:END -->`), `.agents/workflows/VERSION`, and `.agents/plans/pending/p.md`, committed as `seed`. A bare `# w` index is NOT sufficient for `engine.parse_manifest` (probe at review: `index.md is missing the manifest markers`).
   - `test_companion_durability_and_remote_acknowledgement`: writes `.aw/config/config.json` `{"delivery_mode": "tracked", "records_backend": "companion"}`; verifies `get_storage_status` reports `DurabilityState.UNVERSIONED.value` before init; calls `init_records_storage` and verifies `DurabilityState.LOCAL_GIT.value` (asserting it is NOT `ACKNOWLEDGED_DURABLE`); adds a local bare repository as `origin` of the records repo, commits one file and pushes it, then verifies `DurabilityState.UNACKNOWLEDGED_REMOTE.value` with `remote_acknowledged is False` (the remote is not inferred durable); and calls `acknowledge_remote_durability(..., acknowledge=True)` to verify `remote_acknowledged is True` and `DurabilityState.ACKNOWLEDGED_DURABLE.value`. Probe at review reproduced this exact four-state sequence.
   - `test_setup_marker_lifecycle_and_dismissal`: verifies `attention.setup_needed` is `False` on a fresh repo, `True` after `engine.write_setup_marker`, `False` after `engine.remove_setup_marker`; writes the marker again, unlinks `.aw/setup-repo-needed.md` by hand (user dismissal) and verifies `setup_needed` is `False` and that calling `setup_needed` did not recreate the file; then verifies a second `engine.write_setup_marker` makes it `True` again (a new generation supersedes the dismissed one).
   - `test_clean_delta_and_external_record_routing`: verifies `CleanDeltaManager.install_clean_delta("opencode", "1.0.0", user_skills_dir=<tmp>/skills)` reports `target_writes == 0` and writes `SKILL.md` under the user-scope skills dir only; verifies an unsupported host (`install_clean_delta("no-such-host", "0", ...)`) raises `clean_delta.UnsupportedHostError` and creates no skills dir (host support evidence gates the write); and, with `records_backend="home"` in `.aw/config/config.json`, verifies `resolve_record_routing` places `records_root` outside `target_repo` with `allow_git_stage is False` and `commit_destination is None`.
   - `test_conservative_uninstall_preserves_config_state_and_external_records`: populates `.aw/system/manifest.json`, `.aw/config/policy.json`, `.aw/state/`, `.aw/records/sample.md`, and an external records file plus external runtime file under `aw_home`, snapshots the external files' sha256, runs `MigrationManager.uninstall_layout(preserve_records=True, deep_remove_records=False)`, and verifies `status == "uninstalled"`, `.aw/system` is removed, `.aw/config`, `.aw/state`, and `.aw/records/sample.md` are preserved, and every external file under `aw_home` still exists with an unchanged sha256.
   - `test_migration_planning_dry_run_and_wizard_decline_make_no_mutations`: on the seeded repo, verifies `MigrationManager.plan_migration(target_backend="repository")` returns `is_valid` with `available_bytes > 0` and creates no `.aw/`; verifies `execute_migration(target_backend="repository", dry_run=True)` likewise creates no `.aw/`; then, with the cwd set to the repo and `sys.stdin` patched to a `StringIO` subclass whose `isatty()` returns `True` carrying `"1\n1\nn\n"` (stdout captured), verifies `cli.main(["migrate-layout"])` returns `1`, prints the plan preview (`Total Items to Move`), creates no `.aw/`, and leaves every `.agents/` seed file byte-identical. The TTY stub is REQUIRED: with a plain `StringIO` the command takes the non-interactive refusal path instead of the wizard (both return `1`, so only the preview text distinguishes them; probe at review).
   - `test_transactional_move_switches_authority_and_loads_system`: runs `execute_migration(target_backend="repository", dry_run=False)` on the seeded repo (which has a local bare `origin` configured) and verifies: each legacy seed file is gone from `.agents/` and present exactly once under `.aw/system/workflows/` or `.aw/records/plans/pending/` with a sha256 equal to the pre-migration source; `.aw/system/VERSION` exists and `.aw/system/workflows/VERSION` does not; `engine.parse_manifest(.aw/system/workflows)` returns without raising; `migration_transaction.json` has `status == "completed"`, `schema_version == 1`, a non-empty `transaction_id`, every `move_journal` entry `action == "move"`, and `git_staging_plans` keys equal to `{"target", "companion", "source"}`; `switch_receipt.json` has `authority == "switched"` and the same `transaction_id`; `.aw/config/config.json` has `records_backend == "repository"`; `git status --short` contains `R  .agents/workflows/index.md -> .aw/system/workflows/index.md`; and `git ls-remote origin` is empty (no push).
   - `test_rollback_restores_legacy_and_cleanup_refuses_changed_content`: after `execute_migration`, verifies `cleanup_migration(confirm=False)` returns `status == "preview"` with `would_remove == []`; re-creates one retention-manifest `mappings` source path with DIFFERENT bytes and verifies `cleanup_migration(confirm=True)` raises `CleanupError` and leaves that file's content intact (genuine changed-content refusal, probe at review), then removes that file; verifies `cleanup_migration(fault_injection="cleanup-refusal")` raises `CleanupError`; then runs `rollback_migration()` and verifies `status == "rolled_back"`, `authority == "legacy"`, every `.agents/` seed file restored byte-identical to its pre-migration sha256, `.aw/config/config.json` `records_backend == "legacy"`, `.aw/system` and `.aw/records` removed, and `git status --short` free of `->` renames.
   - `test_crash_mid_move_is_resumable`: after `execute_migration`, moves the LAST `move_journal` entry's destination back to its source on disk, drops that entry from `move_journal` (and the last `copied_records` entry), sets transaction `status` and `last_verified_checkpoint` to `"locked"`, unlinks `switch_receipt.json`, and verifies `status_migration()["authority"] == "legacy"`; then calls `MigrationManager(...).resume_migration()` and verifies `status == "completed"`, the source is gone, the destination is present, and the transaction file reads `status == "completed"`. Both the journal trim and the on-disk rewind are required: rewinding the status alone does not simulate a mid-move crash.
   - `test_fault_injection_before_switch_keeps_legacy_authoritative`: uses a fresh seeded repo per injection (a `subTest` per case) and calls `execute_migration(target_backend="repository", fault_injection=...)` for `stale-input` (`StaleInputError`), `concurrent-writer` (`TransactionLockError`), `disk-loss` (`PreflightGateError`), `permission-loss` (`PreflightGateError`), `copy-failure` (`MigrationError`), `verify-mismatch` (`VerificationError`), and `switch-failure` (`SwitchError`), asserting each raises its exception (`assertRaises` with the specific subclass), writes no `switch_receipt.json`, leaves `.aw/config/config.json` absent or without a `records_backend` of `repository`, and leaves `status_migration()["authority"] == "legacy"`; and for the two post-switch injections `kill-after-switch-before-receipt` and `cross-git-partial-stage` (`MigrationError`) asserts the receipt IS present and `status_migration()["authority"] == "switched"` (exactly one authority, detectable after a post-switch crash). Probe at review confirmed this 7/2 split.

3. **Rewrite `tools/awphysical/scenario-token-bindings.json` (`E-04`)**:
   - Keep `"schema_version": 1` and every token's `"assertion"` string; change only `"test"` values and the `"note"`.
   - Update `"note"` to cite `tests.test_awphysical_tools.ScenarioBindingTests`.
   - Rewrite the 22 `tools.awphysical.test_awphysical_tools.<Class>.<method>` bindings to `tests.test_awphysical_tools.<Class>.<method>` (same class and method).
   - Re-bind the 47 tokens whose named condition is asserted by an existing live `tests.*` method (each target was resolved and its assertions read at review):
     - `no-source-trust`, `origin-not-identity`, `source-not-overwritten`, `source-specific-diagnostic` -> `tests.test_installer.PhysicalSystemInstallTests.test_physical_source_packaging_and_spoof_protection`
     - `legacy-writer-disabled` -> `tests.test_record_producers.WriteGuardTests.test_a_legacy_agents_write_is_still_rejected`
     - `no-legacy-fallback-write` -> `tests.test_record_producers.ProducerInventoryTests.test_no_known_writer_module_reintroduced_a_legacy_write_sink`
     - `owned-system-adapters-only` -> `tests.test_record_producers.ProducerInventoryTests.test_the_legacy_allowlist_still_holds_only_non_writers`
     - `no-development-records` -> `tests.test_packaging.PackagingTests.test_wheel_ship_vs_dev_boundary` (asserts no `.aw/records/`, `.aw/state/`, `.agents/plans/` content leaks into the shipped wheel)
     - `no-stage-attempt` -> `tests.test_record_producers.RoutingResolutionTests.test_git_owner_is_unchanged_for_records_and_runtime`
     - `no-repository-records` -> `tests.test_project_layout.TestProjectLayoutAndOwnership.test_materialize_tracked_home_backend_omits_target_records_dir`
     - `portable-local-separation`, `ordinary-target-role`, `tracked-paths-portable` -> `tests.test_project_context.PhysicalContextResolutionTests.test_e01`
     - `local-config-ignored`, `runtime-ignored` -> `tests.test_project_layout.PhysicalPolicyMatrixTests.test_e01`
     - `durable-material-target-tracked`, `explicit-durability-choice`, `target-tracked-durable` -> `tests.test_project_layout.PhysicalPolicyMatrixTests.test_e03`
     - `actionable-incomplete-policy-diagnostic`, `fail-before-write`, `first-install-eof-fails-closed`, `no-write-before-complete-choice`, `safe-install-or-refusal` -> `tests.test_records_untracked_backend.TestRecordsUntrackedBackend.test_e05_missing_field_hint_and_cli_help`
     - `no-migration-required`, `no-policy-switch`, `same-version-noop-checkpoint` -> `tests.test_cli.InstallDiagnosticsTests.test_no_change_reinstall_says_already_current`
     - `no-writes` -> `tests.test_installer.ResolvedVersionStampTests.test_a_second_install_is_idempotent`
     - `no-policy-overwrite`, `update-keeps-policy` -> `tests.test_project_layout.TestProjectLayoutAndOwnership.test_config_merge_preserves_unknown_human_keys`
     - `correct-worktree-path`, `local-binding-updated`, `no-reattach-without-explicit-recovery`, `stable-identity`, `stable-project-identity` -> `tests.test_project_registry.TestProjectRegistry.test_cli_project_attach_and_move`
     - `attachment-rejected`, `authority-invalid`, `identity-conflict` -> `tests.test_project_registry.TestProjectRegistry.test_negative_two_projects_shared_origin_no_auto_attach`
     - `external-local-roots` -> `tests.test_project_context.TestProjectContextResolver.test_path_traversal_refusal`
     - `color-auto-always-never`, `no-color-and-term-dumb` -> `tests.test_term.ShouldColorGridTests.test_should_color_grid_expectations`
     - `meaning-never-color-only`, `screen-reader-text-without-color` -> `tests.test_term.EveryTierKeepsTheInvariantTests.test_invariant_glyph_and_word_preserved_across_tiers` (at every color tier the status word and glyph survive `strip_ansi`, and at `DEPTH_NONE` the line carries no ANSI)
     - `privacy-status-observable-only` -> `tests.test_records_untracked_backend.TestRecordsUntrackedBackend.test_e03_materialize_and_boundaries`
     - `fail-closed`, `human-disposition-required`, `human-owned-review` -> `tests.test_cli.Order16MigrateLayoutCliTests.test_migrate_layout_noninteractive_requires_confirmation`
     - `optional-link-absent-or-broken-safe` -> `tests.test_project_context.TestProjectContextResolver.test_section_9_coverage_guard` (resolves the context with no optional link present and succeeds, which is all deleted `test_19_25_broken_nav_link_resolver_still_works` asserted)
   - Bind the 70 remaining tokens to `tests.test_awphysical_tools.ScenarioContractBehaviorTests.*`:
     - `acknowledged-remote`, `companion-durable`, `private-destination`, `private-durable-bundle`, `durability-action-open`, `durability-action-or-acknowledgement`, `explicit-git-init`, `honest-unversioned-status`, `local-git-not-durable-private`, `unversioned-honest-status` -> `...test_companion_durability_and_remote_acknowledgement`
     - `applicable-actions-only`, `setup-action-visible-on-status-surfaces`, `setup-completion-closes-action`, `dismissal-history-no-resurrection`, `action-generations-supersede` -> `...test_setup_marker_lifecycle_and_dismissal`
     - `no-candid-public-delta`, `public-system-only`, `host-support-evidence`, `no-target-write`, `zero-target-delta`, `explicit-fallback-not-called-clean`, `honest-unsupported-result` -> `...test_clean_delta_and_external_record_routing`
     - `external-bytes-untouched`, `external-config-state-records`, `external-repo-never-deleted`, `external-runtime`, `external-system`, `config-state-records-preserved` -> `...test_conservative_uninstall_preserves_config_state_and_external_records`
     - `all-paths-previewed`, `filesystem-aware-preflight`, `preview-only-default` -> `...test_migration_planning_dry_run_and_wizard_decline_make_no_mutations`
     - `bytes-preserved`, `content-not-lost`, `copy-verify-switch-retain`, `explicit-untrack-plan`, `history-preserved`, `no-duplicate-copy`, `no-overwrite`, `all-records-preserved`, `complete-packaged-system`, `correct-version-manifest`, `one-canonical-system-source`, `package-green`, `single-current-schema`, `stable-transaction-id`, `new-authority-explicit`, `never-push`, `separate-git-evidence`, `valid-git-destinations` -> `...test_transactional_move_switches_authority_and_loads_system`
     - `byte-identical-rollback`, `git-index-restored`, `journal-retained`, `legacy-preserved`, `policy-restored`, `rollback-ready`, `rollback-safe`, `source-retained`, `changed-content-not-deleted`, `cleanup-blocked`, `cleanup-refused` -> `...test_rollback_restores_legacy_and_cleanup_refuses_changed_content`
     - `idempotent-resume`, `recoverable-staging`, `recovery-guidance`, `resume-safe` -> `...test_crash_mid_move_is_resumable`
     - `fail-before-switch`, `legacy-authoritative`, `no-switch`, `one-authority`, `safe-fallback-transaction`, `writer-lock-or-hash-drift-stop` -> `...test_fault_injection_before_switch_keeps_legacy_authoritative`
     - (`...` abbreviates `tests.test_awphysical_tools.ScenarioContractBehaviorTests.`; write the full dotted name in the JSON.)
   - Tally to re-derive at E-04: 22 + 47 + 70 = 139. Nine tokens differ from the authored mapping (plan-review PR-002) because review found the authored live target did not assert the named condition: `explicit-fallback-not-called-clean` (authored target `RoutingResolutionTests.test_legacy_read_paths_resolve_for_a_doc_family_class` asserts the legacy reader IS consulted when a retention manifest exists, the opposite condition; its scenario row in `tools/awphysical/migration-scenarios.json` pairs it with `honest-unsupported-result` and `no-target-write`, so it moves to the clean-delta method); `honest-unsupported-result` (authored target `test_section_9_coverage_guard` only checks `ProjectContext` field presence; moves to the clean-delta unsupported-host refusal); `no-development-records` (authored target `test_the_legacy_allowlist_still_holds_only_non_writers` asserts only that the allowlist is non-empty and excludes one module; `PackagingTests.test_wheel_ship_vs_dev_boundary` asserts no records/state content ships); `color-auto-always-never` and `no-color-and-term-dumb` (authored target `AccessibilityTests.test_no_color_output_has_no_ansi_and_keeps_status_words` sets only `NO_COLOR`; `ShouldColorGridTests.test_should_color_grid_expectations` drives the full `NO_COLOR` x `FORCE_COLOR` x `TERM` grid including `TERM=dumb`). `meaning-never-color-only` and `screen-reader-text-without-color` also move to a fast `tests/test_term.py` method, because `tests/test_cli.py` carries `pytestmark = pytest.mark.slow` and so does not run in the blocking default gate. Eleven tokens still bind to methods in the slow-marked `tests/test_cli.py` and `tests/test_installer.py` (see the slow-target note in E-06). `no-writes` moves to `ResolvedVersionStampTests.test_a_second_install_is_idempotent` (asserts a re-install rewrites no `VERSION`), because `test_no_change_reinstall_says_already_current` asserts only output text; and `no-policy-switch` stays on that no-op reinstall test rather than the config-merge test.

4. **Update `tools/awphysical/README.md` and `tests/test_uncollected_test_modules.py` (`E-05`)**:
   - Update `tools/awphysical/README.md` bullet under `## Files` to reference `tests/test_awphysical_tools.py`.
   - Remove `"tools/awphysical/test_awphysical_tools.py"` from `tests.test_uncollected_test_modules.EXEMPT`.

## Deferred / out of scope (with reason)

- Full deleted-test audit and mutation-proving across all 208 uncited files removed in commit `19313eed7` (including the non-bound methods of `tests/test_layout_migration.py`, `tests/test_awphysical_migration.py`, `tests/test_awphysical_routing.py`, and `tests/test_acceptance_matrix.py`): tracked separately by Set `uncitedaudit` (orchestrator `k93w2g`, pending follow-up `xmr5qj`, backlog `e486tz`).
  - Carrier: k93w2g
  - Carrier-Evidence: .aw/records/plans/executed/20261011-uncitedaudit-00-k93w2g-audit-and-mutation-prove-behavioral-coverage-across-the-unci.ipd.md
- Remaining two exemptions in `tests.test_uncollected_test_modules.EXEMPT` (`tools/aw_upgrade_test.py` and `tests/test_lift_drift_scan.py`): intentional non-unit harnesses (a standalone upgrade harness and a `-m livecorpus` corpus scan), documented in executed plan `5s31xp` and outside `byz9pj`'s scope.
  - Carrier-Declined: intentional non-pytest-default harnesses documented when `EXEMPT` was created in plan `5s31xp`, not defects.
- Moving the 11 slow-target tokens (F-08) onto fast-gate tests: those tests are slow-marked because they drive full installs; duplicating them fast is a coverage-policy change for the slow suite, outside `byz9pj`'s binding-repair scope. E-06 makes the slow-only set visible in evidence.
  - Carrier-Declined: the bound tests exist, pass, and run under `make test-all` and the CI slow step; the residual is the pre-existing slow-gate posture, not a defect this plan introduces.

## Scope check

- Over-scope: none. Every file in `Scope-Paths` is required either to relocate `test_awphysical_tools.py`, repair its scenario-token bindings, update its README reference, or drop its exemption from `tests/test_uncollected_test_modules.py`.
- Under-scope: none. Addressing only `acknowledged-remote` would leave 116 other unloadable bindings in `tools/awphysical/scenario-token-bindings.json` failing `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`; this plan resolves all 139 bindings and removes the collection guard exemption.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py`: every test passes with `0 failed` (`V-03`, `V-04`, `V-06`).
- `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py`: all collected tests pass (`V-05`, `V-06`).
- `python3 -m pytest --collect-only -q -o addopts=""`: includes `tests/test_awphysical_tools.py`; `python3 -m pytest -q -m "not livecorpus" <every bound node id derived from the JSON>`: `0 failed`, no `not found` (`V-06`).
- Bare `python3 -m pytest`: summary line pasted and compared against the `E-01` baseline with zero new failing test node IDs (`V-06`).

## Spec / documentation sync

`tools/awphysical/README.md` (`## Files`) lists `test_awphysical_tools.py` as a local file in `tools/awphysical/` and is updated in `E-05` to reference `tests/test_awphysical_tools.py`. Implemented spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` names only the three production tools (`aw_layout_inventory.py`, `aw_layout_compare.py`, `aw_layout_postcheck.py`) and `migration-scenarios.json`, not `test_awphysical_tools.py` (`git grep -n "test_awphysical_tools" .aw/records/specs/` returns zero matches), so no spec amendment is needed.

## Open questions

### OQ-01: How should the 117 token bindings whose target test modules were removed by commit `19313eed7` be resolved?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Re-bind the 47 tokens whose behavioral assertions are already exercised by live tests in `tests/` directly to those 22 live test methods (item 3), and add 9 focused behavioral test methods in `ScenarioContractBehaviorTests` inside `tests/test_awphysical_tools.py` for the 70 tokens whose underlying `MigrationManager`, `CleanDeltaManager`, companion `storage`, `setup-repo-needed.md` lifecycle, and external `home` routing behaviors have no live test in `tests/` (F-04, F-05). This keeps the suite lean (+9 fast behavioral tests; about 1s by review probe), honors `GUIDING_PRINCIPLES` P16 (behavioral outcomes only, not restoring the retired source-anchor pin in `PhysicalProducerRoutingTests.test_e03`), and ensures every one of the 139 bindings in `tools/awphysical/scenario-token-bindings.json` loads a collected test method that genuinely asserts the named condition.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste (1) the starting HEAD short SHA; (2) the output of `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py` showing exactly one failure, on `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` (30 passed at authoring); (3) the output of `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"` (`0`); (4) the output of the pre-edit binding audit (22 loadable and 117 unloadable at authoring; paste the re-derived numbers); and (5) the bare `python3 -m pytest` baseline summary line, wall time, and any failing test node IDs.
  - Observed evidence:
    1. Starting HEAD short SHA: `bfb051148` (`bfb05114811fc85c464563a5f2583d9876f5e0b9`).
    2. Output of `python3 -m pytest -o addopts="" -q tools/awphysical/test_awphysical_tools.py`:
       ```
       F..............................                                          [100%]
       =================================== FAILURES ===================================
       _ ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion _

       self = <tools.awphysical.test_awphysical_tools.ScenarioBindingTests testMethod=test_every_binding_loads_a_real_test_method_and_names_an_assertion>

           def test_every_binding_loads_a_real_test_method_and_names_an_assertion(self):
               bindings = self._bindings()
               self.assertGreater(len(bindings), 0)
               for token, b in sorted(bindings.items()):
                   ...
       >           self.assertIsNotNone(
                       fn,
                       f"scenario token {token!r} references missing test {test_path!r}",
                   )
       E           AssertionError: unexpectedly None : scenario token 'acknowledged-remote' references missing test 'tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e06'

       tools/awphysical/test_awphysical_tools.py:917: AssertionError
       =========================== short test summary info ============================
       FAILED tools/awphysical/test_awphysical_tools.py::ScenarioBindingTests::test_every_binding_loads_a_real_test_method_and_names_an_assertion
       1 failed, 30 passed in 0.79s
       ```
    3. Collected count in `tests/test_awphysical_tools.py`:
       `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_awphysical_tools.py::"` returned `0`.
    4. Pre-edit binding audit over `tools/awphysical/scenario-token-bindings.json`:
       ```
       Total bindings: 139
       Loadable: 22
       Unloadable: 117
       Unloadable bindings breakdown:
         tests.test_acceptance_matrix: 68
         tests.test_layout_migration: 30
         tests.test_awphysical_migration: 15
         tests.test_awphysical_routing: 4
       Loadable bindings (tools.awphysical.test_awphysical_tools): 22
       ```
    5. Baseline bare `python3 -m pytest` run:
       ```
       695 passed in 21.72s
       ```
       (5 deselected by marker filter `-m 'not slow and not livecorpus'`; 0 failing test node IDs).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git status --short -M` showing `R  tools/awphysical/test_awphysical_tools.py -> tests/test_awphysical_tools.py`, the diff hunks in `tests/test_awphysical_tools.py` for `TOOLS_DIR`, `InventoryTests.test_e01`..`test_e07`, `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`, and `ScenarioBindingTests.test_bad_binding_is_rejected`, and the output of `python3 -m pytest -o addopts="" -q -k "not test_every_binding_loads_a_real_test_method_and_names_an_assertion" tests/test_awphysical_tools.py` showing `0 failed` with its passed count, plus the FAILING output of `python3 -m pytest -o addopts="" -q tests/test_awphysical_tools.py -k test_every_binding_loads_a_real_test_method_and_names_an_assertion` whose assertion message lists more than one unloadable token (proving the collect-all rewrite).
  - Observed evidence:
    1. `git status --short -M`:
       ```
       RM tools/awphysical/test_awphysical_tools.py -> tests/test_awphysical_tools.py
       ```
    2. Diff hunks in `tests/test_awphysical_tools.py`:
       ```diff
       -TOOLS_DIR = Path(__file__).resolve().parent
       +TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "awphysical"
       ```
       And for `InventoryTests.test_e01` through `test_e07`:
       ```diff
       -            Path(__file__).resolve().parent.parent.parent
       -            / "tests"
       +            Path(__file__).resolve().parent
                    / "fixtures"
                    / "awphysical"
                    / "order06"
       ```
       And for `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion` and `test_bad_binding_is_rejected`:
       ```diff
            def test_every_binding_loads_a_real_test_method_and_names_an_assertion(self):
                bindings = self._load_bindings()
       +        problems = []
                for token, b in sorted(bindings.items()):
                    fqn = b.get("test", "")
       -            self.assertTrue(
       -                fqn.count(".") >= 2 and fqn.rsplit(".", 1)[-1].startswith("test"),
       -                f"{token}: binding test is not a module.Class.test_method fqn: {fqn!r}",
       -            )
       -            self.assertIsNotNone(
       -                self._resolve(fqn),
       -                f"{token}: binding names a test method that does not load: {fqn}",
       -            )
       -            self.assertTrue(
       -                b.get("assertion", "").strip(),
       -                f"{token}: binding has no named assertion condition",
       -            )
       +            if not (fqn.count(".") >= 2 and fqn.rsplit(".", 1)[-1].startswith("test")):
       +                problems.append(f"{token}: bad_fqn {fqn!r}")
       +                continue
       +            if self._resolve(fqn) is None:
       +                problems.append(f"{token}: unloadable {fqn}")
       +                continue
       +            if not b.get("assertion", "").strip():
       +                problems.append(f"{token}: missing_assertion")
       +        self.assertEqual(problems, [])

                # And a real binding DOES load (positive control).
                self.assertIsNotNone(
                    self._resolve(
       -                "tools.awphysical.test_awphysical_tools.InventoryTests.test_e01"
       +                "tests.test_awphysical_tools.InventoryTests.test_e01"
                    )
                )
       ```
    3. Output of `python3 -m pytest -o addopts="" -q -k "not test_every_binding_loads_a_real_test_method_and_names_an_assertion" tests/test_awphysical_tools.py`:
       ```
       ..............................                                           [100%]
       30 passed, 1 deselected in 2.16s
       ```
    4. Failing output of `python3 -m pytest -o addopts="" -q tests/test_awphysical_tools.py -k test_every_binding_loads_a_real_test_method_and_names_an_assertion`:
       ```
       F                                                                        [100%]
       =================================== FAILURES ===================================
       _ ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion _
       tests/test_awphysical_tools.py:1591: in test_every_binding_loads_a_real_test_method_and_names_an_assertion
           self.assertEqual(problems, [])
       E   AssertionError: Lists differ: ["acknowledged-remote: unloadable tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e06", ...] != []
       E   First list contains 117 additional elements.
       =========================== short test summary info ============================
       FAILED tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_binding_loads_a_real_test_method_and_names_an_assertion
       1 failed, 30 deselected in 2.08s
       ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py -k ScenarioContractBehaviorTests` showing each of the nine `ScenarioContractBehaviorTests` methods `PASSED`; plus two pasted falsification runs from a throwaway `python3 -` driver (never committed) that applies `unittest.mock.patch` to the name AS THE TEST MODULE REFERENCES IT and runs one test via `unittest`: (a) `MigrationManager.rollback_migration` patched to return `{"status": "rolled_back", "authority": "legacy"}` without restoring anything makes `test_rollback_restores_legacy_and_cleanup_refuses_changed_content` FAIL; (b) `acknowledge_remote_durability` patched to return `get_storage_status(...)` without writing the acknowledgement makes `test_companion_durability_and_remote_acknowledgement` FAIL. This shows the new tests detect the regressions their tokens name rather than passing vacuously.
  - Observed evidence:
    1. Output of `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py -k ScenarioContractBehaviorTests`:
       ```
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_crash_mid_move_is_resumable PASSED [ 11%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_setup_marker_lifecycle_and_dismissal PASSED [ 22%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_rollback_restores_legacy_and_cleanup_refuses_changed_content PASSED [ 33%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_companion_durability_and_remote_acknowledgement PASSED [ 44%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_clean_delta_and_external_record_routing PASSED [ 55%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_transactional_move_switches_authority_and_loads_system PASSED [ 66%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_conservative_uninstall_preserves_config_state_and_external_records PASSED [ 77%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_fault_injection_before_switch_keeps_legacy_authoritative PASSED [ 88%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_migration_planning_dry_run_and_wizard_decline_make_no_mutations PASSED [100%]
       ======================= 9 passed, 31 deselected in 1.58s =======================
       ```
    2. Falsification run (a) (`MigrationManager.rollback_migration` patched to return dummy dict without restoring):
       ```
       --- FALSIFICATION (a): rollback_migration returns dummy dict without restoring ---
       Failures/Errors: 1
       Traceback (most recent call last):
         File ".../tests/test_awphysical_tools.py", line 1421, in test_rollback_restores_legacy_and_cleanup_refuses_changed_content
           rel: hashlib.sha256((repo / rel).read_bytes()).hexdigest()
                               ~~~~~~~~~~~~~~~~~~~~~~~^^
       FileNotFoundError: [Errno 2] No such file or directory: '.../repo/.agents/workflows/index.md'
       ```
    3. Falsification run (b) (`storage.acknowledge_remote_durability` patched to return status without writing acknowledgement):
       ```
       --- FALSIFICATION (b): acknowledge_remote_durability returns status without acknowledging ---
       Failures/Errors: 1
       Traceback (most recent call last):
         File ".../tests/test_awphysical_tools.py", line 1164, in test_companion_durability_and_remote_acknowledgement
           self.assertTrue(st4.remote_acknowledged)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
       AssertionError: False is not true
       ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py` showing every test `PASSED` with `0 failed` (including `ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion`); the re-derived binding audit output (139 total, 0 unloadable, 0 `tools.*` targets, per-target tally equal to item 3); `git diff --stat -- tools/awphysical/scenario-token-bindings.json` plus a `python3 -` check that every token's `"assertion"` string equals its value at `HEAD` (only `"test"` and `"note"` changed); and a falsification check demonstrating that temporarily corrupting one binding in memory is rejected by `ScenarioBindingTests._resolve`.
  - Observed evidence:
    1. Output of `python3 -m pytest -o addopts="" -v tests/test_awphysical_tools.py`:
       ```
       tests/test_awphysical_tools.py::ScenarioCatalogTests::test_legacy_crosswalk_assertions_bind_to_scenarios PASSED [  2%]
       tests/test_awphysical_tools.py::ScenarioCatalogTests::test_scenario_ids_are_unique_and_complete PASSED [  5%]
       tests/test_awphysical_tools.py::CompareTests::test_complete_copy_map_passes PASSED [  7%]
       tests/test_awphysical_tools.py::CompareTests::test_missing_and_unapproved_items_fail PASSED [ 10%]
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_legacy_crosswalk_assertion_tokens_are_bound PASSED [ 12%]
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_bad_binding_is_rejected PASSED [ 15%]
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_binding_loads_a_real_test_method_and_names_an_assertion PASSED [ 17%]
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_expected_token_is_bound PASSED [ 20%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_transactional_move_switches_authority_and_loads_system PASSED [ 22%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_crash_mid_move_is_resumable PASSED [ 25%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_rollback_restores_legacy_and_cleanup_refuses_changed_content PASSED [ 27%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_fault_injection_before_switch_keeps_legacy_authoritative PASSED [ 30%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_conservative_uninstall_preserves_config_state_and_external_records PASSED [ 32%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_setup_marker_lifecycle_and_dismissal PASSED [ 35%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_clean_delta_and_external_record_routing PASSED [ 37%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_companion_durability_and_remote_acknowledgement PASSED [ 40%]
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_migration_planning_dry_run_and_wizard_decline_make_no_mutations PASSED [ 42%]
       tests/test_awphysical_tools.py::InventoryTests::test_e03 PASSED          [ 45%]
       tests/test_awphysical_tools.py::InventoryTests::test_e07 PASSED          [ 47%]
       tests/test_awphysical_tools.py::InventoryTests::test_git_classification_is_closed_and_deterministic PASSED [ 50%]
       tests/test_awphysical_tools.py::InventoryTests::test_backlog_tree_classifies_as_records PASSED [ 52%]
       tests/test_awphysical_tools.py::InventoryTests::test_partial_aw_system_classifies_as_system PASSED [ 55%]
       tests/test_awphysical_tools.py::InventoryTests::test_workflows_migrate_under_system_workflows PASSED [ 57%]
       tests/test_awphysical_tools.py::InventoryTests::test_e06 PASSED          [ 60%]
       tests/test_awphysical_tools.py::InventoryTests::test_e02 PASSED          [ 62%]
       tests/test_awphysical_tools.py::InventoryTests::test_inventory_does_not_follow_symlink PASSED [ 65%]
       tests/test_awphysical_tools.py::InventoryTests::test_host_adapters_preserved_in_place_not_relocated PASSED [ 67%]
       tests/test_awphysical_tools.py::InventoryTests::test_e04 PASSED          [ 70%]
       tests/test_awphysical_tools.py::InventoryTests::test_e05 PASSED          [ 72%]
       tests/test_awphysical_tools.py::InventoryTests::test_e01 PASSED          [ 75%]
       tests/test_awphysical_tools.py::InventoryTests::test_e03_infrastructure_files_get_explicit_dispositions PASSED [ 77%]
       tests/test_awphysical_tools.py::InventoryTests::test_existing_aw_state_is_skipped_not_migrated PASSED [ 80%]
       tests/test_awphysical_tools.py::InventoryTests::test_inventory_classifies_tracked_untracked_and_ignored PASSED [ 82%]
       tests/test_awphysical_tools.py::InventoryTests::test_e02_inventory_prunes_gitignored_dependency_subtree PASSED [ 85%]
       tests/test_awphysical_tools.py::PostcheckTests::test_fabricated_clean_context_fails_without_external_evidence PASSED [ 87%]
       tests/test_awphysical_tools.py::PostcheckTests::test_copied_adapter_logic_and_wrong_git_owner_fail PASSED [ 90%]
       tests/test_awphysical_tools.py::PostcheckTests::test_e07 PASSED          [ 92%]
       tests/test_awphysical_tools.py::PostcheckTests::test_e03 PASSED          [ 95%]
       tests/test_awphysical_tools.py::PostcheckTests::test_clean_context_passes PASSED [ 97%]
       tests/test_awphysical_tools.py::PostcheckTests::test_tracked_runtime_and_legacy_route_fail PASSED [100%]
       ============================== 40 passed in 2.58s ==============================
       ```
    2. Re-derived binding audit over `tools/awphysical/scenario-token-bindings.json`:
       ```
       Total bindings: 139
       Loadable: 139, Unloadable: 0
       Tools targets: 0
       Unique target test methods: 41
       Per-target tally:
         tests.test_awphysical_tools.CompareTests.test_missing_and_unapproved_items_fail: 2
         tests.test_awphysical_tools.InventoryTests.test_e01: 6
         tests.test_awphysical_tools.InventoryTests.test_e03: 2
         tests.test_awphysical_tools.InventoryTests.test_e03_infrastructure_files_get_explicit_dispositions: 1
         tests.test_awphysical_tools.InventoryTests.test_inventory_does_not_follow_symlink: 2
         tests.test_awphysical_tools.InventoryTests.test_partial_aw_system_classifies_as_system: 1
         tests.test_awphysical_tools.PostcheckTests.test_clean_context_passes: 1
         tests.test_awphysical_tools.PostcheckTests.test_copied_adapter_logic_and_wrong_git_owner_fail: 1
         tests.test_awphysical_tools.PostcheckTests.test_fabricated_clean_context_fails_without_external_evidence: 4
         tests.test_awphysical_tools.PostcheckTests.test_tracked_runtime_and_legacy_route_fail: 2
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_clean_delta_and_external_record_routing: 7
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_companion_durability_and_remote_acknowledgement: 10
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_conservative_uninstall_preserves_config_state_and_external_records: 6
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_crash_mid_move_is_resumable: 4
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_fault_injection_before_switch_keeps_legacy_authoritative: 6
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_migration_planning_dry_run_and_wizard_decline_make_no_mutations: 3
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_rollback_restores_legacy_and_cleanup_refuses_changed_content: 11
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_setup_marker_lifecycle_and_dismissal: 5
         tests.test_awphysical_tools.ScenarioContractBehaviorTests.test_transactional_move_switches_authority_and_loads_system: 18
         tests.test_cli.InstallDiagnosticsTests.test_no_change_reinstall_says_already_current: 3
         tests.test_cli.Order16MigrateLayoutCliTests.test_migrate_layout_noninteractive_requires_confirmation: 3
         tests.test_installer.PhysicalSystemInstallTests.test_physical_source_packaging_and_spoof_protection: 4
         tests.test_installer.ResolvedVersionStampTests.test_a_second_install_is_idempotent: 1
         tests.test_packaging.PackagingTests.test_wheel_ship_vs_dev_boundary: 1
         tests.test_project_context.PhysicalContextResolutionTests.test_e01: 3
         tests.test_project_context.TestProjectContextResolver.test_path_traversal_refusal: 1
         tests.test_project_context.TestProjectContextResolver.test_section_9_coverage_guard: 1
         tests.test_project_layout.PhysicalPolicyMatrixTests.test_e01: 2
         tests.test_project_layout.PhysicalPolicyMatrixTests.test_e03: 3
         tests.test_project_layout.TestProjectLayoutAndOwnership.test_config_merge_preserves_unknown_human_keys: 2
         tests.test_project_layout.TestProjectLayoutAndOwnership.test_materialize_tracked_home_backend_omits_target_records_dir: 1
         tests.test_project_registry.TestProjectRegistry.test_cli_project_attach_and_move: 5
         tests.test_project_registry.TestProjectRegistry.test_negative_two_projects_shared_origin_no_auto_attach: 3
         tests.test_record_producers.ProducerInventoryTests.test_no_known_writer_module_reintroduced_a_legacy_write_sink: 1
         tests.test_record_producers.ProducerInventoryTests.test_the_legacy_allowlist_still_holds_only_non_writers: 1
         tests.test_record_producers.RoutingResolutionTests.test_git_owner_is_unchanged_for_records_and_runtime: 1
         tests.test_record_producers.WriteGuardTests.test_a_legacy_agents_write_is_still_rejected: 1
         tests.test_records_untracked_backend.TestRecordsUntrackedBackend.test_e03_materialize_and_boundaries: 1
         tests.test_records_untracked_backend.TestRecordsUntrackedBackend.test_e05_missing_field_hint_and_cli_help: 5
         tests.test_term.EveryTierKeepsTheInvariantTests.test_invariant_glyph_and_word_preserved_across_tiers: 2
         tests.test_term.ShouldColorGridTests.test_should_color_grid_expectations: 2
       ```
    3. `git diff --stat -- tools/awphysical/scenario-token-bindings.json`:
       ```
        tools/awphysical/scenario-token-bindings.json | 280 +++++++++++++-------------
        1 file changed, 140 insertions(+), 140 deletions(-)
       ```
       Assertion check comparison against HEAD: `0 mismatches` (all 139 `"assertion"` strings identical to HEAD).
    4. In-memory corrupted resolve check:
       `ScenarioBindingTests._resolve("tests.test_awphysical_tools.NonExistentClass.bad_method") is None`: `True`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff -- tools/awphysical/README.md tests/test_uncollected_test_modules.py`, the output and exit code (`1`, zero matches) of `git grep -n "tools/awphysical/test_awphysical_tools\|tools\.awphysical\.test_awphysical_tools" -- agent_workflows tests tools`, and the per-test `-v` output of `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` showing all tests `PASSED`.
  - Observed evidence:
    1. `git diff -- tools/awphysical/README.md tests/test_uncollected_test_modules.py`:
       ```diff
       diff --git a/tests/test_uncollected_test_modules.py b/tests/test_uncollected_test_modules.py
       index 009fa725d..622325fbf 100644
       --- a/tests/test_uncollected_test_modules.py
       +++ b/tests/test_uncollected_test_modules.py
       @@ -19,9 +19,6 @@ from typing import Container, Iterable, Mapping, Sequence
        # Explicit, reasoned, self-pruning exemption list.
        # Every entry must name an owning backlog item or plan and a justification.
        EXEMPT: dict[str, str] = {
       -    "tools/awphysical/test_awphysical_tools.py": (
       -        "owned by backlog byz9pj: 1 failing binding test; requires updating scenario token bindings"
       -    ),
            "tools/aw_upgrade_test.py": (
                "not a test module: compat shim for `aw upgrade-test` matching *_test.py pattern with 0 tests"
            ),
       diff --git a/tools/awphysical/README.md b/tools/awphysical/README.md
       index 0a1aabf41..920a16ba6 100644
       --- a/tools/awphysical/README.md
       +++ b/tools/awphysical/README.md
       @@ -18,7 +18,7 @@ move or delete files.
          deterministic migration evidence and identify remaining work.
        - `migration-scenarios.json`: the closed initial scenario catalog that Order 12 must bind to
          executable tests and documentation.
       -- `test_awphysical_tools.py`: isolated tests for the three Python tools.
       +- `tests/test_awphysical_tools.py`: isolated tests for the three Python tools.

        ## Safety boundary
       ```
    2. `git grep -n "tools/awphysical/test_awphysical_tools\|tools\.awphysical\.test_awphysical_tools" -- agent_workflows tests tools` exited 1 with zero matches.
    3. Output of `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py`:
       ```
       tests/test_uncollected_test_modules.py::UncollectedTestModulesGuardTests::test_evaluate_test_module_collection_synthetic_inputs PASSED [ 50%]
       tests/test_uncollected_test_modules.py::UncollectedTestModulesGuardTests::test_no_uncollected_test_modules PASSED [100%]
       ============================== 2 passed in 7.17s ===============================
       ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste (1) the `tests/test_awphysical_tools.py::` lines of `python3 -m pytest --collect-only -q -o addopts=""`; (2) the derived node-id list, the summary line of `python3 -m pytest -q -m "not livecorpus" <node ids>` showing `0 failed` with no `not found`, the list of bound node ids that are slow-marked, and the summary line of `python3 -m pytest -q tests/test_awphysical_tools.py tests/test_uncollected_test_modules.py`; and (3) the bare `python3 -m pytest` summary line and wall time compared against the `V-01` baseline with zero new failing test node IDs.
  - Observed evidence:
    1. `tests/test_awphysical_tools.py::` collection via `python3 -m pytest --collect-only -q -o addopts="" tests/test_awphysical_tools.py`:
       ```
       tests/test_awphysical_tools.py::ScenarioCatalogTests::test_legacy_crosswalk_assertions_bind_to_scenarios
       tests/test_awphysical_tools.py::ScenarioCatalogTests::test_scenario_ids_are_unique_and_complete
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_crash_mid_move_is_resumable
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_migration_planning_dry_run_and_wizard_decline_make_no_mutations
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_rollback_restores_legacy_and_cleanup_refuses_changed_content
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_setup_marker_lifecycle_and_dismissal
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_companion_durability_and_remote_acknowledgement
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_clean_delta_and_external_record_routing
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_conservative_uninstall_preserves_config_state_and_external_records
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_transactional_move_switches_authority_and_loads_system
       tests/test_awphysical_tools.py::ScenarioContractBehaviorTests::test_fault_injection_before_switch_keeps_legacy_authoritative
       tests/test_awphysical_tools.py::CompareTests::test_missing_and_unapproved_items_fail
       tests/test_awphysical_tools.py::CompareTests::test_complete_copy_map_passes
       tests/test_awphysical_tools.py::PostcheckTests::test_e07
       tests/test_awphysical_tools.py::PostcheckTests::test_e03
       tests/test_awphysical_tools.py::PostcheckTests::test_fabricated_clean_context_fails_without_external_evidence
       tests/test_awphysical_tools.py::PostcheckTests::test_copied_adapter_logic_and_wrong_git_owner_fail
       tests/test_awphysical_tools.py::PostcheckTests::test_clean_context_passes
       tests/test_awphysical_tools.py::PostcheckTests::test_tracked_runtime_and_legacy_route_fail
       tests/test_awphysical_tools.py::InventoryTests::test_inventory_does_not_follow_symlink
       tests/test_awphysical_tools.py::InventoryTests::test_e04
       tests/test_awphysical_tools.py::InventoryTests::test_inventory_classifies_tracked_untracked_and_ignored
       tests/test_awphysical_tools.py::InventoryTests::test_e02_inventory_prunes_gitignored_dependency_subtree
       tests/test_awphysical_tools.py::InventoryTests::test_e03_infrastructure_files_get_explicit_dispositions
       tests/test_awphysical_tools.py::InventoryTests::test_backlog_tree_classifies_as_records
       tests/test_awphysical_tools.py::InventoryTests::test_e05
       tests/test_awphysical_tools.py::InventoryTests::test_e01
       tests/test_awphysical_tools.py::InventoryTests::test_workflows_migrate_under_system_workflows
       tests/test_awphysical_tools.py::InventoryTests::test_e03
       tests/test_awphysical_tools.py::InventoryTests::test_e07
       tests/test_awphysical_tools.py::InventoryTests::test_host_adapters_preserved_in_place_not_relocated
       tests/test_awphysical_tools.py::InventoryTests::test_partial_aw_system_classifies_as_system
       tests/test_awphysical_tools.py::InventoryTests::test_existing_aw_state_is_skipped_not_migrated
       tests/test_awphysical_tools.py::InventoryTests::test_git_classification_is_closed_and_deterministic
       tests/test_awphysical_tools.py::InventoryTests::test_e06
       tests/test_awphysical_tools.py::InventoryTests::test_e02
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_legacy_crosswalk_assertion_tokens_are_bound
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_bad_binding_is_rejected
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_expected_token_is_bound
       tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_binding_loads_a_real_test_method_and_names_an_assertion
       (40 tests collected in 0.47s)
       ```
    2. Derived node IDs and runs:
       - 41 unique test node IDs derived from bindings.
       - Slow-marked bound test node IDs (11 tokens across 4 methods):
         `tests/test_cli.py::InstallDiagnosticsTests::test_no_change_reinstall_says_already_current`
         `tests/test_cli.py::Order16MigrateLayoutCliTests::test_migrate_layout_noninteractive_requires_confirmation`
         `tests/test_installer.py::PhysicalSystemInstallTests::test_physical_source_packaging_and_spoof_protection`
         `tests/test_installer.py::ResolvedVersionStampTests::test_a_second_install_is_idempotent`
       - Pytest on all 41 derived node IDs (`python3 -m pytest -m "not livecorpus" <node ids>`):
         ```
         .........................................                                [100%]
         41 passed in 6.99s
         ```
         (0 failed, zero `not found` errors).
       - Targeted modules run (`python3 -m pytest tests/test_awphysical_tools.py tests/test_uncollected_test_modules.py`):
         ```
         ..........................................                               [100%]
         42 passed in 8.55s
         ```
    3. Bare `python3 -m pytest` full suite run:
       ```
       695 passed in 32.83s
       ```
       (5 deselected by default marker filter, 0 failed; identical 695 pass count to V-01 baseline, zero new failing test node IDs).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved 719lyq --by-human`). Open questions: OQ-01 is resolved; none remain. Start execution with `aw ipd begin 719lyq`.

Scope fence: `- Scope-Paths:` is a DECLARATION reconciled at finalize. If an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>`; if a declared path requires no edit, acknowledge it with `--scope-ack`.

Honesty rule: every `V-*` item MUST paste the ACTUAL runner output; never claim a result you did not run.

Commits: the `git mv` relocation (`tools/awphysical/test_awphysical_tools.py` -> `tests/test_awphysical_tools.py`), the `ScenarioContractBehaviorTests` additions, the `tools/awphysical/scenario-token-bindings.json` and `tools/awphysical/README.md` updates, and the `tests/test_uncollected_test_modules.py` exemption removal MUST land together so no intermediate commit leaves a red collected test or a stale exemption in `EXEMPT`. Commit only the modified paths in `Scope-Paths` through `aw commit 719lyq -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify `git diff --cached --name-only` before committing, and never push.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize 719lyq` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-06` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Once this plan is `executed`, backlog `byz9pj` closes `done` via the runner's `process_backlog_close` (or `aw backlog set done byz9pj` when executed by hand).
