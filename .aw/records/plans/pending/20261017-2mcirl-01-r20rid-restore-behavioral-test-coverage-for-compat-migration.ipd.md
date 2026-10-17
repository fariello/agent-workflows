# IPD: Restore behavioral test coverage for compat_migration

- Date: 2026-10-17
- Kind: child
- Concern: `agent_workflows/compat_migration.py` (the compatibility contract, the idempotent previewable migrator, rollback with the data-schema downgrade warning, interrupted-migration recovery, and the opt-in deprecation diagnostics) has 36 production functions that NO surviving routine test reaches (findings `b1mx2w` `## Rollup mutation results`, every `compat_migration.py::` row reads reach class `unreached`, verdict `unguarded-unreached`). Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted `tests/test_compat_migration_rollback.py`, the file that exercised them (findings `hpjj44`, row `tests/test_compat_migration_rollback.py`: `pass-exclusive`, 42 functions with exclusive reach). The only surviving caller is `tests/test_core_module_coverage.py::test_compat_migration_versioning`, which touches `_version_tuple` and `_version_lt` alone. So a regression that, for example, lets a rollback strand newer-schema runtime data, or lets `apply` overwrite a human-owned instruction file, would ship with no test failing.
- Scope: IN: restore `tests/test_compat_migration_rollback.py` from `19313eed^` at its canonical (currently free) path, with three adjustments: its temp-repo fixture uses the repository's hermetic git helpers, the one silent `skipTest` escape becomes a hard failure, and one constant-pinning arm is dropped; add one falsifiable arm for `CompatSurface.validate`'s rejection branches; then prove with the repository's mutation probe that the restored file kills mutants of the named keys. No production code changes. OUT: `tests/test_lifecycle_fixtures.py` (the second file the item names) because it guards `agent_workflows/lifecycle_fixtures.py`, which sibling backlog item `lzn56i` owns (see Deferred).
- Scope-Paths: tests/test_compat_migration_rollback.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 2mcirl
- Set: 2mcirl
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: r20rid
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261017-2mcirl-01-r20rid-restore-behavioral-test-coverage-for-compat-migration.review.md`)
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready plan graduating backlog `2mcirl`. Measured at lane HEAD `d2ec81544`: the deleted file still passes 41 of 41 unmodified, enters all 36 candidate keys, and kills the two mutants probed (F-03, F-04, F-05).
- 2026-10-17 draft (opencode): created.

## Goal

Give `agent_workflows.compat_migration` real behavioral test callers again, so a regression in the compatibility contract check, migration preview/apply, rollback, interrupted recovery, or deprecation gating turns the suite red. Every restored arm drives the module in a temporary git repository and asserts on returned values and on-disk side effects; none reads production source.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the deleted module

- [ ] E-01 Restore `tests/test_compat_migration_rollback.py` from `git show 19313eed^:tests/test_compat_migration_rollback.py`, then make its shared fixture hermetic: add `from tests import support` (the import form `tests/test_migrate_layout_cli.py` uses), in `_RepoFixture.setUp` replace the raw `subprocess.run(["git", "init", ...])` with `support.init_repo(Path(self.target_repo))`, and in BOTH seeding tests of `RollbackTests` (`test_rollback_reverses_records_move_without_record_loss` and `test_recover_interrupted_migration_completes_it`, each running one `git add -A` and one `git commit`, four calls in total) pass `env=support.clean_git_env()` (keep `check=True`), dropping the inline `-c user.email=... -c user.name=...` since `init_repo` sets a local identity. Keep `AW_HOME` pointed at the temp dir and restored in `tearDown`, exactly as the deleted fixture does. Update the module docstring to name this plan (`r20rid`) and backlog `2mcirl` in place of the old Order 17 wording. Do NOT add `pytestmark = pytest.mark.slow` (the restored arms run in about 6 s serially, F-03) and do not add `pytest.mark.core` (OQ-01).
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -q tests/test_compat_migration_rollback.py` reports every collected test passing with 0 failed and 0 errors. The repo-level `tests.git_config_guard` plugin (loaded by the root `conftest.py` `pytest_plugins`) fails any test that alters the checkout's identity keys, so a clean run is the proof that the outer `.git/config` was not touched (`git status` cannot show `.git/config` and is not that proof).
  - Execution state: pending

- [ ] E-02 Remove the two places where the restored module swallows a migration-engine exception. (a) In `RollbackTests.test_rollback_reverses_records_move_without_record_loss`, remove the `try: mgr.execute_migration(...) except Exception as exc: self.skipTest(...)` wrapper (and its `# pragma: no cover` comment) so an exception from `MigrationManager.execute_migration` fails the test. A skip there turns a broken migration engine into a green run, which is the exact silent-loss mode this restoration exists to close; F-03 measured that the call succeeds at HEAD, so no skip is needed. (b) In `RollbackTests.test_recover_interrupted_migration_completes_it`, replace the `try: mgr.execute_migration(..., fault_injection="kill-after-switch-before-receipt") except Exception: pass` with `with self.assertRaises(MigrationError):` around the same call (import `MigrationError` from `agent_workflows.layout_migration`). The bare `except Exception: pass` accepts any failure, including a crash before the switch write, as an "interruption"; asserting the injected `MigrationError` proves the fault fired where intended (F-09 demonstrates it raises `MigrationError`).
  - Depends on: E-01
  - Expected outcome: The narrowed run reports `test_rollback_reverses_records_move_without_record_loss` PASSED (not SKIPPED), `-rs` output lists no skipped test in the module, and `test_recover_interrupted_migration_completes_it` still passes with the `assertRaises(MigrationError)` in place.
  - Execution state: pending

- [ ] E-03 Drop `MigrationPreviewTests.test_all_install_states_are_reachable_names`. It calls no code and asserts only that the constant `cm.INSTALL_STATES` equals a hand-written set of five other constants, which pins a declaration rather than behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Four of the five states are already asserted behaviorally by `detect_state` arms in `MigrationPreviewTests` (`STATE_LEGACY` in `test_legacy_state_detected`, `STATE_CURRENT` in `test_current_state_after_apply_and_idempotent_rerun`, `STATE_DRIFTED` in `test_drift_detected_backed_up_and_regenerated`, `STATE_CUSTOMIZED` in `test_human_owned_file_is_preserved_never_overwritten`). `STATE_PARTIAL` is NOT: the dropped arm is the only place the restored file names it, and `CompatMigrator.detect_state`'s `return STATE_PARTIAL` branch is among the lines F-03's coverage run left unexecuted. So, in the same edit, add to `RollbackTests.test_recover_interrupted_migration_completes_it`: immediately after the interrupted `execute_migration`, `self.assertEqual(cm.CompatMigrator(self.target_repo).detect_state(), cm.STATE_PARTIAL)`, and after `recover_interrupted()`, `self.assertNotEqual(cm.CompatMigrator(self.target_repo).detect_state(), cm.STATE_PARTIAL)` (F-09 demonstrates `partial` then `current`). Keep `test_surface_exit_codes_preserved`: it is the golden test the contract row `exit-codes` names by string (`compat_migration._CONTRACT_ROWS`), so removing it would make `test_every_row_names_a_golden_test_that_exists` fail.
  - Depends on: E-02
  - Expected outcome: `test_all_install_states_are_reachable_names` is absent from the module, every collected test passes (40 at authoring: 41 restored minus this one; context, not the bar), and the recover arm asserts the `partial` state before recovery and a non-`partial` state after.
  - Execution state: pending

### Task group 2: close the one uncovered falsifiable branch

- [ ] E-04 Add `ContractGoldenTests.test_validate_rejects_bad_vocabulary`: build one `cm.CompatSurface` with `surface=""`, `owner="not-an-owner"`, `status="not-a-status"`, and empty `version_boundary`, `migration` and `test`; assert `row.validate()` returns six problems that respectively contain `empty surface`, `bad owner 'not-an-owner'`, `bad status 'not-a-status'`, `empty version_boundary`, `empty migration` and `empty test`; then assert `cm.check_contract({**cm.build_contract(), "exit-codes": <a valid exit-codes row with owner="not-an-owner">})` is not `ok` and has a finding containing `surface 'exit-codes': bad owner`. Build the second row with `dataclasses.replace(cm.build_contract()["exit-codes"], owner="not-an-owner")` (`CompatSurface` is a `@dataclass(frozen=True)`, so `replace` is the supported way to derive a variant). These six branches are the rejection path F-03 measured as unexecuted by the restored file; without this arm a mutant making `validate` always return `[]` survives the whole module (F-10: 0 failures). Other lines F-03 left unexecuted (for example `build_contract`'s duplicate-row raise) are defensive and stay out of scope. Because `tools/mutation_probe.py` has no "return empty list" operator, demonstrate this arm's falsifiability for that mutant with a throwaway script under the gitignored scratch dir (never under `tests/`) that loads the module and runs it with `unittest.mock.patch.object(cm.CompatSurface, "validate", lambda self: [])`, the same method F-10 used.
  - Depends on: E-03
  - Expected outcome: The new test passes and every collected test in the module passes (41 at authoring; context, not the bar). Under the `validate -> []` patch the scratch run reports `test_validate_rejects_bad_vocabulary` failing (at least 1 failure), where F-10 measured 0 without it.
  - Execution state: pending

### Task group 3: prove reach and kill, then commit

- [ ] E-05 Measure reach. Pick `<scratch>`, a directory under the gitignored `tmp/` (the root `.coverage` file is NOT gitignored, so keep the data file in scratch). Run `COVERAGE_FILE=<scratch>/.coverage python3 -m coverage run --include='agent_workflows/compat_migration.py' -m pytest -o addopts="" -q -p no:cacheprovider tests/test_compat_migration_rollback.py`, then `COVERAGE_FILE=<scratch>/.coverage python3 -m coverage json -o <scratch>/cov.json`. Extract the 36 keys with `grep -o 'compat_migration.py::[A-Za-z0-9_.]*' .aw/records/research/20261016-trimcarry-01-b1mx2w-rollup-reach.findings.md | sort -u` (the character class must include digits, or `_sha256_bytes`/`_sha256_path` truncate to `_sha` and the count reads 35). With a throwaway script in `<scratch>` (never committed, never under `tests/`), look each qualname up in `cov.json`'s `files["agent_workflows/compat_migration.py"]["functions"]` map (coverage 7.x keys functions by qualname, e.g. `CompatSurface.validate`) and report any key missing from the map or with empty `executed_lines`. Delete `<scratch>` afterwards. The script is a measurement aid over coverage data, not a test.
  - Depends on: E-04
  - Expected outcome: The script prints `36 keys; missing: []; unentered: []`, and `coverage report` shows statement coverage for `compat_migration.py` at or above the 89 percent measured at authoring (F-03).
  - Execution state: pending

- [ ] E-06 Commit only the new module: `aw commit r20rid -- tests/test_compat_migration_rollback.py`. Verify first with `git diff --cached --name-only` that nothing else is staged. Never `git add -A`, never commit the scratch files from E-05, never push.
  - Depends on: E-05
  - Expected outcome: One commit whose `git show --stat HEAD` lists exactly `tests/test_compat_migration_rollback.py`.
  - Execution state: pending

- [ ] E-07 Prove the restored file kills mutants of the named keys with the repository's worktree-isolated probe, which mutates committed HEAD in a disposable worktree and so needs E-06's commit. Run each of these, with `--format json`, selecting only the restored file (`-- tests/test_compat_migration_rollback.py`): `--op return-none agent_workflows/compat_migration.py::CompatRollback.scan_future_data`; `--op raise agent_workflows/compat_migration.py::CompatMigrator.register_human_file`; `--op return-none agent_workflows/compat_migration.py::check_contract`; `--op return-none agent_workflows/compat_migration.py::DeprecationDiagnostics.request_alias_removal`; and `--op return-none agent_workflows/compat_migration.py::CompatSurface.validate` selecting ONLY the new arm (`-- tests/test_compat_migration_rollback.py::ContractGoldenTests::test_validate_rejects_bad_vocabulary`), because over the whole file a `None` return is already killed by the pre-existing contract arms (F-10: 9 failures without E-04), so a whole-file selection would not show the new arm doing anything. Then run the full suite: bare `python3 -m pytest` (the core-tier merge gate) and `python3 -m pytest tests/test_compat_migration_rollback.py` with default `addopts` (proving the module is not deselected by the `slow`/`livecorpus` filter, so CI's `python -m pytest tests/ -n auto -rfEs` step runs it).
  - Depends on: E-06
  - Expected outcome: Every probe reports `verdict: killed`, `baseline_failing: 0`, and `checkout_status_changed: []`. Bare `python3 -m pytest` reports no failures; the default-addopts run of the module reports all its tests passed with none deselected.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests assert outcomes, never code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES.md` P16). The restored arms call `CompatMigrator`, `CompatRollback`, `DeprecationDiagnostics` and the contract functions and assert on returned values and files; none reads `compat_migration.py` source. `ContractGoldenTests.test_every_row_names_a_golden_test_that_exists` uses `hasattr` on the TEST class to check that each contract row's `test` string names a real golden test; that checks production data against the test suite, not production source structure, and is kept.
- Temp git repositories in tests use `tests.support.init_repo` and `tests.support.clean_git_env` so a run inside a hook or lane cannot touch the outer repository's git state; the root `conftest.py` loads `tests.git_config_guard` (IPD `lp1zkb`, backlog `8o7gco`) because a test once leaked identity keys into the shared `.git/config`. Precedent: executed plan `1ue3kr` (`tests/test_migrate_layout_cli.py`).
- The bare suite (`python3 -m pytest`) runs only `core`-marked tests (root `conftest.py`, `pyproject.toml` marker `core: fast behavioral regression test run by a bare pytest; author-assigned`); CI's `Run self-tests (parallel)` step in `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs`, which collects every module not marked `slow`/`livecorpus`. So an unmarked restored module is load-bearing in CI and in `make test-all`.
- `tools/mutation_probe.py` (`run_probe`, "Execute a worktree-isolated mutation probe against committed HEAD") is the measurement tool the `b1mx2w` audit used; it mutates in a disposable worktree outside the checkout and reports `checkout_status_changed`.
- Commits go through `aw commit <plan> -- <paths>`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The 36 candidate keys are exactly the `compat_migration.py::` rows of `b1mx2w`'s `## Rollup mutation results`, all `unreached` / `unguarded-unreached` at that audit's baseline. | `grep 'compat_migration.py::' .aw/records/research/20261016-trimcarry-01-b1mx2w-rollup-reach.findings.md` yields 36 distinct keys, from `CompatRollback.scan_future_data` to `CompatMigrator.detect_state`; the totals row reads `agent_workflows/compat_migration.py \| 36 \| 36 \| 0`. |
| F-02 | `tests/test_compat_migration_rollback.py` does not exist at HEAD and nothing else in `tests/` imports `compat_migration` except `tests/test_core_module_coverage.py::test_compat_migration_versioning` (only `_version_tuple`, `_version_lt`). | `ls tests/test_compat_migration_rollback.py` -> no such file; `grep -rln compat_migration tests` -> `tests/test_core_module_coverage.py` only. |
| F-03 | The deleted file, copied unmodified into a gitignored scratch dir, PASSES at lane HEAD `d2ec81544`: `41 passed in 6.21s` (0 skipped), slowest arm 1.44 s. Under `coverage` it enters all 36 keys (`36 keys; unentered: []`) at 89 percent statement coverage of `compat_migration.py`; among the missed lines are `CompatSurface.validate`'s six rejection branches (motivating E-04). | `python3 -m pytest tmp/probe2mcirl/test_cmr_probe.py -o addopts="" -q` -> `41 passed`; `coverage report -m` -> `agent_workflows/compat_migration.py 390 44 89%`, missing includes `151, 153, 155, 157, 159, 161`. Scratch removed after measurement. |
| F-04 | `tools/mutation_probe.py --op return-none ...::CompatRollback.scan_future_data --extra-test 19313eed:tests/test_compat_migration_rollback.py` -> `verdict killed`, `baseline_failing 0`, `mutant_failing 2`, `checkout_status_changed []` (39.1 s). | JSON output at HEAD `d2ec81544aa42a5e95a97b7f6133d6bf457b1bc4`. |
| F-05 | `tools/mutation_probe.py --op raise ...::CompatMigrator.register_human_file` with the same extra test -> `verdict killed`, `mutant_failing 1`, `checkout_status_changed []` (51.0 s). | JSON output, same HEAD. |
| F-06 | The deleted fixture uses raw `git init` and `git -c user.email=t@t -c user.name=t commit` without the repository's clean-env helper, one arm wraps `execute_migration` in `except Exception: self.skipTest(...)`, and the interrupted-recovery arm wraps the fault-injected call in `except Exception: pass`. All are corrected (E-01, E-02) rather than restored verbatim. | `git show 19313eed^:tests/test_compat_migration_rollback.py`, `_RepoFixture.setUp`, `RollbackTests.test_rollback_reverses_records_move_without_record_loss` and `RollbackTests.test_recover_interrupted_migration_completes_it`. |
| F-07 | The second named file, `tests/test_lifecycle_fixtures.py` (136 lines), tests `agent_workflows/lifecycle_fixtures.py` via `lf.run_fixture`; its compat_migration reach is incidental (through `lifecycle_fixtures._migrator`). Sibling open backlog item `lzn56i` ("Restore behavioral test coverage for lifecycle_fixtures") names that same deleted file for its 21 keys. | `git show 19313eed^:tests/test_lifecycle_fixtures.py` (`from agent_workflows import lifecycle_fixtures as lf`); `.aw/records/backlog/open/20261016-trimgap-01-lzn56i-restore-behavioral-test-coverage-for-lifecycle-fix.backlog.md`. |
| F-08 | Baseline bare suite at lane HEAD: `748 passed in 98.63s`, 9047 deselected by the core filter. | `python3 -m pytest` output tail. |
| F-09 | (review, HEAD `e34dd644b`) Driving the interrupted path with the hermetic helpers: `support.init_repo` + `support.git(..., env=support.clean_git_env())` seed both return 0; `execute_migration(..., fault_injection="kill-after-switch-before-receipt")` raises `MigrationError`; `CompatMigrator(repo).detect_state()` then returns `partial`; `CompatRollback.recover_interrupted()["status"]` is `recovered` and `detect_state()` afterwards returns `current`. So E-01's helpers, E-02(b)'s `assertRaises(MigrationError)` and E-03's `STATE_PARTIAL` assertions are all satisfiable. | Scratch script under gitignored `tmp/`, output `0 0` / `injected: MigrationError` / `detect_state: partial` / `recover: recovered after: current`; removed after. |
| F-10 | (review) Running the unmodified deleted module with `CompatSurface.validate` patched: `lambda self: []` -> `failures+errors = 0` (survives); `lambda self: None` -> `failures+errors = 9` (killed by existing contract arms). Also re-measured F-03: `41 passed in 1.67s`, `36 keys; missing: []; unentered: []`, `TOTAL 390 44 89%`, `CompatSurface.validate` 8/14 statements. | `unittest.mock.patch.object` scratch run under `tmp/`; removed after. |

## Proposed changes (ordered, validatable)

1. Restore `tests/test_compat_migration_rollback.py` with a hermetic fixture (E-01).
2. Turn the silent skip and the swallowed interruption into hard assertions (E-02); drop the constant-pinning arm and assert the `partial` state behaviorally instead (E-03).
3. Add the `CompatSurface.validate` rejection arm (E-04).
4. Measure reach (E-05), commit (E-06), prove mutant kills and run the suite (E-07).

## Deferred / out of scope (with reason)

- Restoring `tests/test_lifecycle_fixtures.py`: it guards `lifecycle_fixtures.py`, whose coverage is the subject of a separate open item; restoring it here would duplicate that item's work and collide on its path (F-07). The 36 compat keys are fully reached without it (F-03).
  - Carrier: lzn56i
- Marking the module `pytest.mark.core` (adding it to the bare merge gate): changes the core tier's composition and its 30 s budget, an author/maintainer call recorded in OQ-01; the module is still run by CI's `tests/` step and `make test-all`.
  - Carrier-Declined: deliberate non-goal; the precedent restoration `1ue3kr` made the same choice, and nothing outlives this plan to carry.

## Scope check

- Over-scope: none. One new test file; no production change.
- Under-scope: none for the 36 keys; E-05 proves every key is entered and E-07 proves representative mutants (data scan, human-file registration, contract check, alias-removal refusal, row validation) are killed.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q -rs tests/test_compat_migration_rollback.py`: every collected test passed, 0 failed, 0 skipped (E-01 to E-04; 41 at authoring, context only).
- `validate -> []` patched scratch run: the new arm fails (E-04).
- Coverage reach script: `36 keys; missing: []; unentered: []` (E-05).
- Five mutation probes: each `killed` with `baseline_failing: 0` and `checkout_status_changed: []` (E-07).
- Bare `python3 -m pytest` with no failures, and the default-addopts module run showing it is not deselected (E-07).
- Paste actual runner output in every `V-*`; use the executor's own baseline, not F-08's number.

## Spec / documentation sync

N/A: test-only change; no spec or user-facing document describes this test file and no behavior changes.

## Open questions

### OQ-01: Should the restored module join the core (bare-run) tier?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The `core` marker is author-assigned against a 30 s wall budget (`pyproject.toml` marker text; CONTRIBUTING "runs the core test tier (budgeted under 30s wall time on 6 workers)"), and the precedent restoration `1ue3kr` left its module unmarked. The module stays unmarked and non-`slow`, so CI's `pytest tests/` step and `make test-all` run it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted narrowed run output for `tests/test_compat_migration_rollback.py` showing all tests passed, plus the pasted `_RepoFixture.setUp` lines showing `support.init_repo(...)`, a pasted `grep -n "clean_git_env\|user.email\|\"init\"" tests/test_compat_migration_rollback.py` showing all four seed `git` calls (two in each seeding test) carrying `env=support.clean_git_env()` and no `user.email=` / raw `git init` remaining, and a pasted `grep -c "pytest.mark" tests/test_compat_migration_rollback.py` returning 0.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `-v -rs` narrowed run showing `test_rollback_reverses_records_move_without_record_loss PASSED` and `test_recover_interrupted_migration_completes_it PASSED` and no `SKIPPED` line; a pasted `grep -n "skipTest\|except Exception" tests/test_compat_migration_rollback.py` returning nothing; and the pasted `with self.assertRaises(MigrationError):` block of the recover arm.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `grep -n "test_all_install_states_are_reachable_names\|STATE_PARTIAL" tests/test_compat_migration_rollback.py` showing no hit for the dropped arm and the two `STATE_PARTIAL` assertions in `test_recover_interrupted_migration_completes_it`, plus the pasted narrowed run (re-derived at execution) with 0 failed. The collected count is context, not the bar.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `-v` output line `test_validate_rejects_bad_vocabulary PASSED` and the module summary line with 0 failed (count re-derived at execution); the pasted test body showing the six problem-substring assertions and the `check_contract` finding assertion; and the pasted output of the scratch `validate -> []` patched run showing the new arm failing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted script output `36 keys; missing: []; unentered: []` and the pasted `coverage report` line for `agent_workflows/compat_migration.py` at 89 percent or higher, plus `git status --short` showing no `.coverage` (root or elsewhere) and no scratch file outside the gitignored `tmp/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `git show --stat HEAD` listing exactly `tests/test_compat_migration_rollback.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: The five pasted probe JSON results (at least `target`, `operator`, `verdict`, `baseline_failing`, `mutant_failing`, `checkout_status_changed`), each `killed` with `baseline_failing: 0` and an empty `checkout_status_changed`, the `CompatSurface.validate` probe's `selection` showing only the `test_validate_rejects_bad_vocabulary` node; the pasted summary line of bare `python3 -m pytest` with no failures; and the pasted summary of `python3 -m pytest tests/test_compat_migration_rollback.py` (default addopts) showing every collected test passed and no `deselected` count.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; nothing blocks execution.
- Scope fence: `- Scope-Paths:` declares the one file this plan edits. No production code changes; scratch measurement files live under the gitignored `tmp/` and are never committed.
- Honesty: paste ACTUAL runner output in each `V-*`; never claim a pass you did not run.
- Commits: path-scoped via `aw commit r20rid -- tests/test_compat_migration_rollback.py`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. Executed by hand (`aw work begin r20rid`), finish with `aw ipd finalize r20rid --actor <agent/model> --message <summary> --apply` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan to `executed/`.
