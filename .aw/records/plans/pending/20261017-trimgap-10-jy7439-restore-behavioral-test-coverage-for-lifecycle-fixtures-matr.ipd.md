# IPD: Restore behavioral test coverage for lifecycle_fixtures matrix runners, registry and isolation

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `lzn56i` (Set `trimgap`, group 10 of the `b1mx2w` filing plan `z2xs98`) records that 21 production keys in `agent_workflows/lifecycle_fixtures.py` (244 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. `lifecycle_fixtures` is the awoptimize Order 18 (`0zst62`) lifecycle matrix: eleven named fixtures that each build a real legacy starting state in an isolated temp environment and drive it through `compat_migration.CompatMigrator` / `compat_migration.CompatRollback` and `host_capability_registry`, returning a `FixtureOutcome`. Its only behavioral tests lived in `tests/test_lifecycle_fixtures.py`, which the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted outright (`hpjj44` records it as `pass-exclusive`: 17 tests, 44 functions with exclusive reach, 460 exclusive lines). So a mutation that, for example, made `run_unsupported_host` report `passed=True` without refusing, made `run_customized_file` stop checking that the human edit survived `apply`, or made `run_fixture` stop cleaning up its temp tree, would pass the routine suite.
- Scope: Restore `tests/test_lifecycle_fixtures.py` from `19313eed^:tests/test_lifecycle_fixtures.py` as a core-tier behavioral module that drives the 21 keys through `run_fixture`, `run_all_fixtures`, `make_isolated_env`, `seed_legacy_tree` and `IsolatedEnv`, and asserts on returned `FixtureOutcome` fields, environment-variable state and the file system; plus one small added class covering the four behaviors the deleted file never asserted directly (an unknown fixture name is refused, `activate_aw_home` followed by `cleanup` restores a caller's prior `AW_HOME`, `run_fixture` removes the isolated tree it created, and a refuse-before-mutation fixture whose refusal DID write to the repo reports `mutated=True` and fails). The 21 keys: `run_clean_install`, `run_legacy_update`, `run_partial_state`, `run_customized_file`, `run_interrupted_update`, `run_rollback`, `run_downgrade_warning`, `run_no_network`, `run_no_credential`, `run_multi_host_discovery`, `run_unsupported_host`, `run_fixture`, `run_all_fixtures`, `make_isolated_env`, `seed_legacy_tree`, `_migrator`, `_snapshot_tree`, `_sha`, `IsolatedEnv.activate_aw_home`, `IsolatedEnv.restore_aw_home`, `IsolatedEnv.cleanup`. EXCLUDES any change to `agent_workflows/lifecycle_fixtures.py` or any other production file (see F-05 and Deferred for the one latent defect found), and EXCLUDES `tests/test_core_module_coverage.py`, whose existing `test_lifecycle_fixtures` smoke test stays as is.
- Scope-Paths: tests/test_lifecycle_fixtures.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lzn56i
- Set: trimgap
- Order: 10
- Highest E allocated: 05
- Author: opencode
- Id: jy7439
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-17 to-review (opencode): authored from backlog `lzn56i`. Ran the deleted `19313eed^:tests/test_lifecycle_fixtures.py` verbatim against HEAD `5c29f238e` before writing any expected outcome (F-03: 17 passed in 2.32s), probed the added behaviors and the `AW_HOME` handling directly (F-04, F-05), and pre-ran all nine E-04 mutations (F-08), so the expectations below are observed, not inferred.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 21 `unguarded-unreached` lifecycle_fixtures keys from backlog `lzn56i` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its outputs and side effects. Done means a mutation that breaks any fixture's pass/refusal verdict, its `mutated` flag, the registry/runner mapping, or the isolated-environment lifecycle turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the module into the core tier

- [ ] E-01 Restore the file with `git show 19313eed^:tests/test_lifecycle_fixtures.py > tests/test_lifecycle_fixtures.py`, then add `import pytest` and a module-level `pytestmark = pytest.mark.core` (the pattern `tests/test_backlog.py` uses for `unittest.TestCase` classes) so the bare core-tier gate collects it. Extend the module docstring with one paragraph naming backlog `lzn56i`, findings `b1mx2w` and `hpjj44`, and the trim commit `19313eed` it was restored from. Make no other change to the restored content. Disposition rule if a restored test fails at execution HEAD (none did at authoring, F-03, nor at review, F-09): do not mark the item performed until it is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, and bare `python3 -m pytest --collect-only -q` lists it as selected by the core tier with every restored test (17 at authoring and review).
  - Execution state: pending

- [ ] E-02 Append one `unittest.TestCase` class `IsolatedEnvLifecycleTests` with exactly four tests (add `import os` and `from unittest import mock` to the imports). (a) `test_unknown_fixture_name_is_refused`: `lf.run_fixture("no-such-fixture")` raises `ValueError` whose message contains `"clean-install"` (the known-names list `run_fixture` prints). (b) `test_activate_then_cleanup_restores_prior_aw_home`: set `os.environ["AW_HOME"]` to a sentinel string, call `lf.make_isolated_env()`, call `env.activate_aw_home()` and assert `os.environ["AW_HOME"] == str(env.aw_home)`, call `env.cleanup()` and assert `os.environ["AW_HOME"]` equals the sentinel again and `env.base_dir.exists()` is False; restore the original value in a `finally`/`addCleanup`. (c) `test_run_fixture_removes_its_isolated_tree`: wrap `lf.make_isolated_env` with `unittest.mock.patch.object(lf, "make_isolated_env", spy)` where `spy` calls the real function and records the returned env; call `lf.run_fixture("clean-install")` and assert `.passed`; then assert exactly one env was made and its `base_dir.exists()` is False. This is the guard for `run_fixture`'s `finally: env.cleanup()`, which F-08 shows no restored test catches. (d) `test_a_refusal_that_mutated_the_repo_is_reported_as_mutated`: make an env with `lf.make_isolated_env()` (`addCleanup(env.cleanup)`), patch `lf.hcr.render_probe_commands` with a function accepting `**kwargs` that writes `env.target_repo / "stray.txt"` and then raises `ValueError`, call `lf.run_unsupported_host(env)`, and assert `outcome.mutated is True`, `outcome.passed is False` and `outcome.evidence["no_mutation"] is False`. This is the guard for `_snapshot_tree`, the before/after comparison every refuse-before-mutation verdict rests on; F-09 shows that making it return `{}` survives every other test, because the real refusals never write. Do NOT add any test asserting what `cleanup` does to `AW_HOME` when `activate_aw_home` was never called (F-05: that behavior is a latent defect and must not be pinned).
  - Depends on: E-01
  - Expected outcome: all four added tests pass at HEAD (observed in F-04, F-08 and F-09).
  - Execution state: pending

### Task group 2: confirm the keys are guarded

- [ ] E-03 Run the module alone (`python3 -m pytest tests/test_lifecycle_fixtures.py -o addopts="" -v`) and confirm every test (17 restored plus 4 added at review) passes with no skips.
  - Depends on: E-02
  - Expected outcome: every collected test passed, no skips (21 at review; the bar is all-pass, not the count).
  - Execution state: pending

- [ ] E-04 Mutation spot-check, scratch edits to `agent_workflows/lifecycle_fixtures.py` never committed, one at a time, rerunning the module after each and reverting before the next: (a) in `run_unsupported_host`, set `refused = False` in the `except ValueError` branch; (b) in `run_customized_file`, delete the `mig.register_human_file(rel)` call; (c) in `run_downgrade_warning`, set `mutated=True`; (d) in `run_clean_install`, delete the `mig.apply(preview)` call; (e) in `IsolatedEnv.restore_aw_home`, make the body `os.environ.pop("AW_HOME", None)` unconditionally; (f) in `run_fixture`, replace the `finally` body `env.cleanup()` with `pass`; (g) in `_sha`, return `os.urandom(8).hex()`; (h) remove the `FIXTURE_ROLLBACK: run_rollback,` entry from `FIXTURE_RUNNERS`; (i) make `seed_legacy_tree` return before writing anything; (j) make `_snapshot_tree` return `{}` as its first statement. Then confirm `git diff agent_workflows/` is empty.
  - Depends on: E-03
  - Expected outcome (pre-observed at HEAD, F-08): each mutation turns at least one test red: (a) `FailBeforeMutationTests::test_unsupported_host_refused_before_mutation`; (b) `LifecycleFixturePassTests::test_customized_file_passes`; (c) `DowngradeWarningTests::test_downgrade_warns_and_is_refused_without_corruption`; (d) `LifecycleFixturePassTests::test_clean_install_passes` and `NoUnmanagedDriftTests::test_clean_install_rerun_is_no_op`; (e) `IsolatedEnvLifecycleTests::test_activate_then_cleanup_restores_prior_aw_home`; (f) `IsolatedEnvLifecycleTests::test_run_fixture_removes_its_isolated_tree`; (g) `LifecycleFixturePassTests::test_customized_file_passes`; (h) `LifecycleFixtureRegistryTests::test_every_fixture_has_a_runner`; (i) `LifecycleFixturePassTests::test_legacy_update_passes`; (j) `IsolatedEnvLifecycleTests::test_a_refusal_that_mutated_the_repo_is_reported_as_mutated` (F-09). If any mutation survives at execution time, report it in V-04 as a failure rather than marking pass. The production diff is empty afterwards.
  - Execution state: pending

### Task group 3: core-tier fit

- [ ] E-05 Run bare `python3 -m pytest` and confirm it passes with the new module included, recording the wall time against the core-tier budget (30s, enforced by `conftest.pytest_sessionfinish`, IPD `hguae9`). If the budget line fires, rerun once to separate host load from this module's cost (F-06, F-09) and report both runs plus the module's own `--durations=5` slice. A budget overrun attributable to host load or pre-existing tests (backlog `o58dro`) is reported, not fixed here; do not un-mark the module to make the budget.
  - Depends on: E-03
  - Expected outcome: the summary line reports passed; the module's own serial cost stays near the 2.3s observed in F-03.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). The restored file calls the module's functions and asserts on `FixtureOutcome` fields and environment state; it reads no production source. Its registry test compares `set(lf.ALL_FIXTURES)` to the eleven named fixtures, which is a content check of the advertised matrix, not a symbol census.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget, so the restored module must carry `pytestmark = pytest.mark.core`. Module-level `pytestmark` applies to `unittest.TestCase` classes, as `tests/test_backlog.py` already relies on.
- HOME ISOLATION is owned by the root `conftest.py` ("Home isolation: no test may read or write the developer's real AW_HOME or user config"): it sets `AW_HOME`/`XDG_CONFIG_HOME` to a session sandbox before import and an autouse fixture `_restore_home_sandbox` re-applies it after every test. So the F-05 `AW_HOME` removal cannot leak past a single test under pytest, and E-02(b) may set `AW_HOME` freely.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for `agent_workflows/lifecycle_fixtures.py::*`, and its per-module totals row "`agent_workflows/lifecycle_fixtures.py` \| 21 \| 21 \| 0" | Exactly 21 keys carry `unreached` / `unguarded-unreached`: the 21 named in Scope. `FixtureOutcome.to_dict` is not among them. |
| F-02 | `hpjj44` row for `tests/test_lifecycle_fixtures.py` | The deleted file was `pass-exclusive`: 17 tests, sole reacher of 44 functions (460 exclusive lines) across `lifecycle_fixtures`, `compat_migration` and `layout_migration`, including all 21 keys here. Restoring it therefore also restores incidental reach into `CompatMigrator.preview`/`apply` and `MigrationManager.status_migration`, which are other trimgap items' gaps (`2mcirl` and siblings) and are not claimed here. |
| F-03 | `git show 19313eed^:tests/test_lifecycle_fixtures.py` written to a scratch test path and run at HEAD `5c29f238e` with `-o addopts="" --durations=0` | `17 passed in 2.32s`. Slowest calls: `RunAllTests::test_run_all_fixtures_pass` 0.94s, `test_customized_file_passes` 0.18s, the rest at or below 0.15s. Restoration needs no rewrite. |
| F-04 | Direct probe at HEAD: `run_fixture("nope")`; `AW_HOME="/prior"` then `make_isolated_env()`, `activate_aw_home()`, `cleanup()` | `run_fixture` raises `ValueError("unknown lifecycle fixture 'nope'; known: ['clean-install', ...]")`; after activate `AW_HOME == str(env.aw_home)`; after cleanup `AW_HOME == "/prior"` and the base dir is gone. Both E-02 tests are true at HEAD. |
| F-05 | Direct probe at HEAD: `AW_HOME=<x>` then `run_fixture("clean-install")` printed `AW_HOME` as `None`; `run_fixture("partial-state")` left it at `<x>` | LATENT DEFECT, not fixed here. `IsolatedEnv.cleanup` always calls `restore_aw_home`, which pops `AW_HOME` when `_prev_aw_home is None`. That attribute is only set by `activate_aw_home`, so for the nine fixtures that never activate, `cleanup` DELETES a caller's `AW_HOME`. Observed effect so far: none on disk; a probe running `run_all_fixtures()` with a throwaway `HOME`, `XDG_CONFIG_HOME` and `AW_HOME` left both directories empty, and under pytest `_restore_home_sandbox` re-applies the sandbox after every test. The module has no production caller (`grep lifecycle_fixtures` in `agent_workflows/` finds only the module itself). |
| F-06 | Two bare `python3 -m pytest` runs at HEAD `5c29f238e`, before any change | First: `754 passed in 54.68s` with "CORE TIER BUDGET EXCEEDED ... 38.53s exceeded budget of 30.00s" (slowest `test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement` 12.40s). Second: exit 0. The core tier is already at or over budget under host load without this module, a pre-existing condition tracked by backlog `o58dro`. E-05 therefore reports this module's own cost separately. |
| F-08 | Scratch run at HEAD `5c29f238e`: the restored file plus the E-02 class, then each E-04 mutation applied and reverted one at a time | Baseline `19 passed in 2.69s` (17 restored plus the two E-02 (a)/(b) tests). Mutations (a), (b), (c), (d), (e), (g), (h) and (i) each turned the tests listed in E-04 red. Mutation (f) (no `env.cleanup()` in `run_fixture`) left everything at `19 passed`: no restored test observes the temp tree being removed. A candidate E-02(c) test was then added and run: it passed at HEAD and failed under (f) with `AssertionError: True is not false` on `base_dir.exists()`. No production file was left modified (`git status --short` showed only this plan). |
| F-09 | review (2026-10-17, HEAD `3dc559634`): scratch restore plus the E-02 class, scratch mutations of `lifecycle_fixtures.py` reverted (`git diff agent_workflows/` empty) | With E-02 (a)..(c): `20 passed in 2.85s`; bare collect `tests/test_lifecycle_fixtures.py: 20`; `ruff check --select F` clean. All nine E-04 mutations (a)..(i) KILLED as F-08 states, plus two extra mutations: overwriting the human file before `apply` (killed by `test_customized_file_passes`) and `_migrator` pointing at `env.base_dir` (5 failed). SURVIVED: `_snapshot_tree` returning `{}` (`20 passed`), because no real refusal writes, so `before == after` holds trivially. The E-02 (d) test passed at HEAD and failed under that mutation. Bare `python3 -m pytest` with the file: `774 passed in 38.75s` (budget exceeded); without it, at the same HEAD: `753 passed in 34.04s` with `CORE TIER BUDGET EXCEEDED`, so the overrun is pre-existing host load (F-06), and this module adds about 2.8s serial (`RunAllTests::test_run_all_fixtures_pass` 0.97s). Note: `--collect-only -q` prints one line per FILE (`path: N`), so `rg -c` counts files, not tests. |
| F-07 | `git log -S lifecycle_fixtures -- tests/test_core_module_coverage.py` | `87f7eb421` (`hguae9`, after the `86f0d88d` baseline) added `test_core_module_coverage.py::test_lifecycle_fixtures`, a smoke test that calls `make_isolated_env` and `cleanup` and asserts only that the base dir exists. At HEAD those 3 keys (`make_isolated_env`, `IsolatedEnv.cleanup`, `IsolatedEnv.restore_aw_home`) are therefore reached but not guarded on their outcomes; E-02(b) and E-04(e) supply the guard. The other 18 keys remain unreached at HEAD. |

## Proposed changes (ordered, validatable)

1. E-01 restores `tests/test_lifecycle_fixtures.py` with the core marker and a provenance note.
2. E-02 adds four tests: unknown-name refusal, prior-`AW_HOME` restoration, temp-tree cleanup by `run_fixture`, and a mutated refusal reported as mutated.
3. E-03 runs the module in isolation.
4. E-04 proves the keys are guarded by scratch mutations that turn tests red.
5. E-05 confirms core-tier fit.

## Deferred / out of scope (with reason)

- F-05: `IsolatedEnv.cleanup` removes a caller's `AW_HOME` when `activate_aw_home` was never called. Fixing it would change production code, which this restore-only item excludes, and no on-disk effect has been observed (F-05), so by the repository's user-perceptible-impact rule it is not a `bug`. E-02 deliberately does not pin the current behavior, so a later fix will not break these tests.
  - Carrier-Declined: latent, test-helper-only, no observed effect and no production caller. Reviewer decision (2026-10-17, review D-2): no backlog item is filed; the repository's perceptible-impact rule makes this not a `bug`, the root `conftest.py` re-applies the home sandbox after every test, and E-02 deliberately leaves the behavior unpinned so a later fix stays free.
- The incidental reach into `compat_migration` and `layout_migration` (F-02) is not claimed as closing those modules' trimgap items.
  - Carrier-Declined: owned by sibling trimgap backlog items, which carry their own plans.
- Converting the restored `unittest.TestCase` classes to pytest-style functions is out of scope: it would rewrite tests that pass verbatim (F-03) for no behavioral gain.
  - Carrier-Declined: style-only, no defect or gap owed.

## Scope check

- Over-scope: none. One restored test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 21 named keys. `_migrator` is a one-line helper reached by every migrator fixture, so it is guarded through mutations (b), (d) and (i); it gets no dedicated mutation.

## Required tests / validation

- `python3 -m pytest tests/test_lifecycle_fixtures.py -o addopts="" -v` passes, with the per-test list pasted (21 tests at review).
- Bare `python3 -m pytest` passes (core tier, including the restored module), with the summary line and any budget line pasted, per E-05.
- Mutation spot-checks of E-04: paste the failing test id and assertion for each of the 10 scratch mutations, then an empty `git diff agent_workflows/`.
- `aw sanitize --agent` reports no `fail` on `tests/test_lifecycle_fixtures.py`.

## Spec / documentation sync

N/A: this plan restores tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the deleted file verbatim, or write a new module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: restore verbatim under its original name, plus the two-test class of E-02. The backlog item names `test_lifecycle_fixtures.py` at `19313eed^` as the file to mine; it passes unmodified at HEAD (F-03), reaches all 21 keys (F-02), runs in about 2.3s serial, and no current `tests/test_lifecycle_fixtures.py` exists to collide with (`ls tests | grep lifecycle` lists none). This matches sibling plan `dwjfu4`.

### OQ-02: Should this plan fix the F-05 `AW_HOME` removal?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. The backlog item's remedy is "restore behavioral test coverage", every sibling trimgap plan excludes production changes, and F-05 has no observed on-disk effect. It is recorded in Deferred and E-02 avoids pinning it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` showing only `tests/test_lifecycle_fixtures.py` added (besides this plan); paste a diff of `19313eed^:tests/test_lifecycle_fixtures.py` against the new file showing only the `pytest` import, the `pytestmark` line and the provenance paragraph (plus E-02's appended class); paste `python3 -m pytest --collect-only -q | rg test_lifecycle_fixtures` showing the line `tests/test_lifecycle_fixtures.py: <N>` (the bare core tier selects the module), and state that N matches the `-v` count in V-03.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the added `IsolatedEnvLifecycleTests` class source and the `-v` lines for its four tests showing PASSED; confirm by inspection that no test asserts `AW_HOME` state after `cleanup` without a prior `activate_aw_home`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing every collected test as PASSED and the summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste, for each of the 10 scratch mutations (a) through (j), the failing test id and assertion message from the rerun; then paste the empty output of `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare `python3 -m pytest` summary line and wall time, any `CORE TIER BUDGET` line verbatim with the rerun if one fired, and the module's `--durations=5` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01, OQ-02).
- Scope fence: `tests/test_lifecycle_fixtures.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under the E-01 disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch edits to `agent_workflows/lifecycle_fixtures.py` that must be reverted before commit and must be absent from the diff.
- Honesty: you MUST paste the actual runner output for every test and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit jy7439 -- tests/test_lifecycle_fixtures.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize jy7439` instead. Never hand-`git mv` the plan.
