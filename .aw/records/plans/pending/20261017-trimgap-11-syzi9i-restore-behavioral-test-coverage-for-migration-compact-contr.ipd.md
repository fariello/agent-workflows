# IPD: Restore behavioral test coverage for migration_compact contracts, projections, shim resolution and promotion gates

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `fdyjv6` (Set `trimgap`, group 11 of the `b1mx2w` filing plan) records that all 24 production keys in `agent_workflows/migration_compact.py` (210 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests lived in `tests/test_migration_compact_shims.py` (22 tests), deleted by the suite trim `19313eed`; `hpjj44` `## Derived properties` attributes the exclusive reach of every one of these keys to that file. The only surviving test touching the module, `test_core_module_coverage.test_migration_compact_families`, calls `advertised_families(())` on an empty tuple, which cannot distinguish a passing family from a failing one. So a mutation that, for example, made `evaluate_promotion_gate` advertise a failing family as migrated, made `TypedContract.validate` accept `needs_subagent=True`, or made `detect_shim_drift` miss a hand-edit, would pass the routine suite.
- Scope: Restore ONE behavioral test module at its original path, `tests/test_migration_compact_shims.py`, mined from `19313eed^:tests/test_migration_compact_shims.py`, marked `core` so the routine gate reaches it, and extended where the deleted file left a key's return value unasserted (the three `to_dict` methods and the fail-closed error branches). It drives all 24 keys named in `b1mx2w`: `evaluate_promotion_gate`, `build_metric_summary`, `_mv` (via `build_metric_summary`), `TypedContract.validate`, `TypedContract.to_dict`, `build_compact_package`, `build_all_compact_packages`, `generate_compact_projection`, `resolve_shim`, `check_compact_completeness`, `old_invocation_still_works`, `resolve_body_dir`, `_workflow_by_command` (via `resolve_body_dir` and `build_compact_package`), `argument_parity`, `render_agent_report`, `CompactPackage.to_dict`, `skill_resolves_package`, `advertised_families`, `legacy_fallback_families`, `CompactProjection.to_dict`, `CompactProjection.shim_for`, `assert_no_needless_subagent`, `_shim_view_digest` (via `detect_shim_drift`), `detect_shim_drift`. EXCLUDES any change to `agent_workflows/migration_compact.py` or any other production file; EXCLUDES the non-`migration_compact` keys that the same deleted file also reached (`benchmark_thresholds.evaluate_release_gate`, `host_adapters.SkillPackage.to_dict`, `engine.validate_shim_grammar`), which other `trimgap` items own; EXCLUDES the deleted `tests/test_exec_set_workflow.py`, whose only `migration_compact` use is one `detect_shim_drift(content, content)` call already covered here and whose remaining reach (`set_records`, `ipd_set_plan`) is not this item's module; and EXCLUDES the deleted `test_generator_is_reused_not_forked` `assertIs` symbol-identity assertions, which pin code structure (re-export identity) rather than behavior and so are forbidden by the AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" rule. Its behavioral half (projection shims equal the engine generator's output) IS restored.
- Scope-Paths: tests/test_migration_compact_shims.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: fdyjv6
- Set: trimgap
- Order: 11
- Highest E allocated: 06
- Author: opencode
- Id: syzi9i
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-17 to-review (opencode): authored from backlog `fdyjv6`. Recovered the deleted module from `19313eed^`, ran it unchanged against HEAD `823b8e00e` (22 passed in 1.65s, slowest call 0.04s), and measured every expected value below by direct call (Findings F-02 to F-05) before writing it.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 24 `unguarded-unreached` `migration_compact` keys from backlog `fdyjv6` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its return values and raised errors. Done means a `return-none`, `negate-return` or `raise` mutation (the operators `b1mx2w` assigned these keys) of any of them turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restored behavioral test module

- [x] E-01 Create `tests/test_migration_compact_shims.py` from `git show 19313eed^:tests/test_migration_compact_shims.py`, adding `import pytest` and module-level `pytestmark = pytest.mark.core`, and amending the module docstring to name backlog `fdyjv6`, findings `b1mx2w`, plan `syzi9i`, and the source `19313eed^`. Keep the stdlib `unittest.TestCase` classes as recovered (pytest collects them and applies the module mark). Remove from `test_generator_is_reused_not_forked` the two `assertIs(MCC.<symbol>, ENGINE.<symbol>)` lines (symbol-identity, structure-pinning), keeping its `assertEqual(projection.shims, direct)` behavioral assertion. No subprocess, no filesystem writes: every test reads the in-repo `SOURCE_WORKFLOWS`. Disposition rule if a recovered test fails at execution HEAD (none did at authoring, F-02, nor at review, F-07): do not mark this item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, is selected by a bare `python3 -m pytest` (it carries the `core` marker), and all recovered tests pass.
  - Execution state: performed

- [x] E-02 Contract tests (`CompactContractTests`, recovered): completeness is clean for the nine `COMPACT_COMMANDS`; `resolve_body_dir("research", ...)` is `research-prompt`; every package from `build_all_compact_packages` has an empty `contract.validate()`; deterministic-first packages name a script; `assert_no_needless_subagent` accepts every real package and raises `CompactMigrationError` for a `needs_subagent=True` contract whose `validate()` reports `needless orchestration`; `build_compact_package("release-review", ...)` raises; out-of-vocabulary mode, boundary and interaction are each flagged. ADD: `resolve_body_dir("not-a-command", ...)` raises `CompactMigrationError` naming `not a live manifest row`; a deterministic-first `TypedContract` with `script=None` reports `names no reusable script`; `build_compact_package("verify", ...).to_dict()` equals a dict whose `command` is `verify`, `canonical_package` is `verify`, `body` equals the package `body`, `semantic_digest` equals the package digest, and `contract` equals `{"command": "verify", "mode": "deterministic-first", "input_kind": "arguments", "output_kind": "evidence", "write_boundary": "consented-write", "interaction": "optional", "needs_subagent": False, "script": "run_checks"}` (this reaches `CompactPackage.to_dict` and `TypedContract.to_dict` with a falsifiable value).
  - Depends on: E-01
  - Expected outcome: all recovered and added contract tests pass.
  - Execution state: performed

- [x] E-03 Shim and skill tests (`ShimAndSkillTests`, recovered): `generate_compact_projection(...).shim_for(cmd)` returns at least 2 shims for every compact command; `resolve_shim` returns the right `command`, a `body_target` containing the command (or `research-prompt`), and a `semantic_digest` equal to the package's; `argument_parity` is True for every compact command; `detect_shim_drift` is False for an identical regeneration and True for an appended hand-edit; every selected skill `skill_resolves_package` its package, and a package with a `"0" * 64` digest does not; `old_invocation_still_works` is True for every compact command; projection shims equal `engine.generate_shim_members` output. ADD: `old_invocation_still_works("not-a-command", ...)` is False (the no-match branch); `generate_compact_projection(SOURCE_WORKFLOWS, skill_commands=["not-a-command"])` raises `CompactMigrationError`; `generate_compact_projection(SOURCE_WORKFLOWS, skill_commands=["spec"]).skill_packages` has exactly the key `spec` (the override branch); and the default projection's `skill_packages` key set is non-empty and a subset of `COMPACT_COMMANDS`.
  - Depends on: E-01
  - Expected outcome: all recovered and added shim/skill tests pass.
  - Execution state: performed

- [x] E-04 Promotion-gate tests (`PromotionGateTests`, recovered): a passing summary at risk `low` yields `passed`, `PATH_MIGRATED`, `advertised`, no corrective item, and appears in `advertised_families`; a failing summary at risk `high` yields `PATH_LEGACY_FALLBACK`, not advertised, an `open` corrective item with non-empty findings, absent from `advertised_families` and present in `legacy_fallback_families`; a mixed pair partitions into `("f-pass",)` and `["f-fail"]`; a `RiskThresholds` with `max_critical_escapes=5` makes `ThresholdPolicy` raise `ThresholdError`; one critical escape fails a perfect-quality `low` gate. ADD: `build_metric_summary(requirement_recall=0.9, task_correctness=0.8, evidence_validity=0.7, critical_escapes=2, scope_violations=3, sample_size=4)` returns a `MetricSummary` whose `sample_size` is 4, `requirement_recall.value` 0.9, `task_correctness.value` 0.8, `evidence_validity.value` 0.7, `defect_escape.value` 0.5, `scope_violations.value` 3, and `requirement_recall.sample_size` 4 (this reaches `_mv` with a falsifiable value); and the failing decision's `to_dict()["corrective_item"]["family"]` equals the family name.
  - Depends on: E-01
  - Expected outcome: all recovered and added promotion-gate tests pass.
  - Execution state: performed

- [x] E-05 Report tests (`ReportTests`, recovered): `render_agent_report` is identical across two calls, parses as JSON with empty `compact_completeness_findings` and `packages` keyed by exactly `COMPACT_COMMANDS`. ADD: `data["projection"]["shim_paths"]` is sorted, non-empty, and equals `sorted(generate_compact_projection(SOURCE_WORKFLOWS).shims)`; `data["projection"]["skill_packages"]` has the same key set as the default projection's `skill_packages` (this reaches `CompactProjection.to_dict` with a falsifiable value); and `data["packages"]["research"]["body"]` ends with `research-prompt/research-prompt.md`.
  - Depends on: E-01
  - Expected outcome: all recovered and added report tests pass.
  - Execution state: performed

### Task group 2: proof that every key is guarded

- [x] E-06 Run the full 24-key mutation sweep against the finished module: for each key in `b1mx2w` `## Rollup mutation results` rows `agent_workflows/migration_compact.py::*`, apply that row's assigned operator (`return-none`, `negate-return`, `raise`) as a scratch edit to `agent_workflows/migration_compact.py` at the top of the key's body (for `negate-return`, wrap the function so it returns `not` its original result), run `python3 -m pytest tests/test_migration_compact_shims.py -o addopts="" -q -p no:randomly`, record KILLED (nonzero exit) or SURVIVED with the summary line, and restore the file before the next key. Keep any sweep driver script in a gitignored scratch location (for example `.aw/state/`) and never commit it. Then run the reach command in Required tests. A survivor is a defect in this plan's deliverable: add the missing assertion to `tests/test_migration_compact_shims.py` and re-sweep that key; do not mark this item performed with a survivor outstanding.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: every one of the 24 keys is KILLED by its assigned operator (at review the recovered file alone left `TypedContract.to_dict`, `CompactPackage.to_dict` and `CompactProjection.to_dict` surviving, and the E-02/E-05 `to_dict` additions killed all three, F-07); `git diff agent_workflows/` is empty afterwards.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). No `inspect`, `ast`, regex over production source, caller counts, or symbol-identity pins. This is why E-01 drops the recovered `assertIs` re-export lines.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`; marker declared in `pyproject.toml` `markers`). A restored module must carry `pytestmark = pytest.mark.core` to be reached by the merge gate. `tests/test_core_module_coverage.py` is the established example (`pytestmark = pytest.mark.core`).
- Sibling plan `33f8tn` (Set `trimgap`, Order 9, backlog `7df9md`) is the established shape for this Set's restore plans: one new core-marked behavioral test file, no production change, scratch mutation spot-checks reverted before commit.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows `agent_workflows/migration_compact.py::*`; `b1mx2w` `## Filing plan` row 11; `hpjj44` `## Derived properties` rows for each key | Exactly 24 keys, all `unreached` / `unguarded-unreached`, operators `return-none` (most), `negate-return` (`argument_parity`, `detect_shim_drift`, `old_invocation_still_works`) and `raise` (`assert_no_needless_subagent`). `hpjj44` attributes each key's exclusive reach to `tests/test_migration_compact_shims.py` (22 removed funcs). `rg migration_compact tests/` finds only `test_core_module_coverage.test_migration_compact_families`, which asserts `advertised_families(()) == ()`. |
| F-02 | `git show 19313eed^:tests/test_migration_compact_shims.py` copied to a scratch test path and run with `-o addopts=""` at HEAD `823b8e00e`, then deleted | `22 passed in 1.65s`; slowest call 0.04s (`test_report_is_deterministic_json_and_clean`). The recovered file needs no API adaptation and fits the core budget. |
| F-03 | direct calls at HEAD `823b8e00e` | Default projection: 56 shims, 2 per compact command, `skill_packages` keys `handoff`, `list-workflows`, `research`, `whatnext`. `resolve_body_dir("research")` is `research-prompt`; `resolve_shim("research").body_target` is `.aw/system/workflows/research-prompt/research-prompt.md`. |
| F-04 | direct calls | `resolve_body_dir("nope")` and `generate_compact_projection(skill_commands=["nope"])` each raise `CompactMigrationError` with `not a live manifest row`; `old_invocation_still_works("nope")` is False; `build_compact_package("verify").to_dict()["contract"]` is the dict quoted in E-02. |
| F-05 | direct calls | Failing gate (`recall 0.5`, `correctness 0.4`, risk `high`) findings begin `RECALL GATE FAILURE` and `CORRECTNESS GATE FAILURE`; report JSON top-level keys `compact_completeness_findings`, `packages`, `projection`, and `projection` keys `shim_paths`, `skill_packages`. |
| F-07 | plan review, HEAD `711302a31`: recovered file as a scratch test, then a scratch sweep applying each `b1mx2w` row's assigned operator to `agent_workflows/migration_compact.py` (restored after each key; `git diff agent_workflows/` empty afterwards); then the E-02 `verify` `to_dict` test and the E-05 projection assertions appended and the three survivors re-swept; plus direct calls | Recovered file: `22 passed in 0.48s`. Sweep: 21 of 24 KILLED; `SURVIVED` for `TypedContract.to_dict@return-none`, `CompactPackage.to_dict@return-none` and `CompactProjection.to_dict@return-none` (each `22 passed`), so coverage shows these bodies executed while nothing asserts their output. With the additions: all three `KILLED` (`1 failed, 23 passed`). Every ADD expected value in E-02 to E-05 reproduced by direct call (`resolve_body_dir` / `skill_commands` refusals name `not a live manifest row`; `old_invocation_still_works("not-a-command")` False; missing-script message; `verify` `to_dict` dict; `skill_commands=["spec"]` keys `['spec']`; metric values `4 0.9 0.8 0.7 0.5 3 4`; report `shim_paths == sorted(shims)` (56); research body `.aw/system/workflows/research-prompt/research-prompt.md`). |
| F-06 | `19313eed^:tests/test_exec_set_workflow.py` | Imports `migration_compact as MC` for one call, `MC.detect_shim_drift(content, content)`; nothing else from this module. Its other exclusive reach (`set_records.*`, `ipd_set_plan.*`) is outside this item. |

## Proposed changes (ordered, validatable)

1. E-01 restores the core-marked module and removes the structure-pinning lines.
2. E-02 covers typed contracts, body-dir resolution, package building and the no-needless-subagent guard.
3. E-03 covers projection, shim resolution, drift, argument parity, skill resolution and old invocations.
4. E-04 covers the metric-summary seam and the promotion gate partition.
5. E-05 covers the agent report and `CompactProjection.to_dict`.
6. E-06 proves the Goal by sweeping every key with its assigned mutation operator.

## Deferred / out of scope (with reason)

- Non-`migration_compact` keys reached by the same deleted file (`benchmark_thresholds.evaluate_release_gate`, `host_adapters.SkillPackage.to_dict`, `engine.validate_shim_grammar`) are not this item's keys; the restored tests will incidentally execute them, but asserting their contracts belongs to the `trimgap` items filed for those modules.
  - Carrier-Declined: no work is owed by this plan; `b1mx2w` `## Filed items` routes those modules to their own backlog items.
- `tests/test_exec_set_workflow.py` is not restored: its single `migration_compact` call is duplicated by E-03's drift test (F-06).
  - Carrier-Declined: no `migration_compact` reach is lost; its remaining reach is outside this item's module.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All 24 keys from F-01 are driven by E-02 to E-05, private helpers through their public callers, and E-06 demonstrates each is guarded (F-07).

## Required tests / validation

- `python3 -m pytest tests/test_migration_compact_shims.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes with the new module included, with the summary line pasted.
- Reach: `python3 -m pytest tests/test_migration_compact_shims.py -o addopts="" --cov=agent_workflows.migration_compact --cov-report=term-missing` shows the bodies of all 24 keys executed; paste the output.
- Mutation spot-checks: scratch, uncommitted edits to `agent_workflows/migration_compact.py`, one per V-item as listed there, each run against the new module with the failure pasted, then reverted with `git diff agent_workflows/` shown empty.
- Mutation sweep (E-06): all 24 keys with their `b1mx2w` assigned operators, one KILLED/SURVIVED line per key pasted.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore at the original path, or a new `*_restored_behavior.py` name like `33f8tn`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: original path. The file is restored nearly verbatim (F-02), so its original name keeps `git log --follow` and the `hpjj44` / `b1mx2w` citations pointing at a real file; `33f8tn` used a new name because it mines two different deleted files into a new module, which is not the case here. The path is unoccupied at HEAD.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff --stat HEAD` (or `git status --short`) showing only `tests/test_migration_compact_shims.py` added; paste the `tests/test_migration_compact_shims.py: N` line from bare `python3 -m pytest --collect-only -q` (the core selection prints one `path: N` line per file, so `rg -c` would print 1, not N), with N matching the per-test list of the Required tests `-v` run; paste the bare `python3 -m pytest` summary line showing it passed (if it prints `CORE TIER BUDGET EXCEEDED`, paste that too with the same run's line without the module, and report it rather than un-marking tests; a pre-existing overrun is tracked separately, backlog `o58dro`); paste `rg -n "assertIs\(" tests/test_migration_compact_shims.py` returning no match.
  - Observed evidence:
    `git status --short`:
    ```
    ?? tests/test_migration_compact_shims.py
    ```

    `python3 -m pytest --collect-only -q | grep tests/test_migration_compact_shims.py`:
    ```
    tests/test_migration_compact_shims.py: 29
    ```

    Bare `python3 -m pytest` summary line (core tier wall time 32.30s, pre-existing budget overrun tracked in `o58dro`):
    ```
    1276 passed in 32.30s
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 32.30s exceeded budget of 30.00s.
    ```
    Same bare run without the module (`python3 -m pytest --ignore=tests/test_migration_compact_shims.py`):
    ```
    1247 passed in 44.70s
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 44.70s exceeded budget of 30.00s.
    ```

    `rg -n "assertIs\(" tests/test_migration_compact_shims.py` (exit code 1, no matches):
    ```
    (no match, exit code 1)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every `CompactContractTests` test as PASSED, including the added error-branch, missing-script and `to_dict` tests; paste the failures produced by scratch-mutating `TypedContract.to_dict` and `CompactPackage.to_dict` each to `return None` (survivors of the recovered file alone, F-07), with the added `verify` `to_dict` test among the failures; paste the failure produced by scratch-mutating `TypedContract.validate` to `return []` and the failure produced by scratch-mutating `assert_no_needless_subagent` to `return None` before its `if` (each reverted afterwards).
  - Observed evidence:
    `CompactContractTests` `-v` run:
    ```
    tests/test_migration_compact_shims.py::CompactContractTests::test_no_compact_package_needs_a_subagent PASSED [  9%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_all_nine_compact_commands_are_live_manifest_rows PASSED [ 18%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_negative_needless_subagent_is_rejected PASSED [ 27%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_negative_non_compact_command_is_refused PASSED [ 36%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_every_compact_package_has_valid_typed_contract PASSED [ 45%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_research_body_dir_is_research_prompt_not_command_name PASSED [ 54%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_negative_bad_vocabulary_is_flagged PASSED [ 63%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_resolve_body_dir_nonexistent_command_raises PASSED [ 72%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_build_compact_package_to_dict_matches_expected_structure PASSED [ 81%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_deterministic_first_contract_missing_script_is_flagged PASSED [ 90%]
    tests/test_migration_compact_shims.py::CompactContractTests::test_deterministic_first_packages_name_a_reusable_script PASSED [100%]
    11 passed in 0.35s
    ```

    Failure when mutating `TypedContract.to_dict` to `return None`:
    ```
    FAILED tests/test_migration_compact_shims.py::CompactContractTests::test_build_compact_package_to_dict_matches_expected_structure - AssertionError: {'com[104 chars]ct': None, 'semantic_digest': '56e25ded7e99772[46 chars]f62'} != {'com[104 chars]ct': {'command': 'verify', 'mode': 'determinis[261 chars]f62'}
    1 failed, 28 passed in 0.43s
    ```

    Failure when mutating `CompactPackage.to_dict` to `return None`:
    ```
    FAILED tests/test_migration_compact_shims.py::ReportTests::test_report_is_deterministic_json_and_clean - TypeError: 'NoneType' object is not subscriptable
    FAILED tests/test_migration_compact_shims.py::CompactContractTests::test_build_compact_package_to_dict_matches_expected_structure - AssertionError: None != {'command': 'verify', 'canonical_package'[375 chars]f62'}
    2 failed, 27 passed in 0.48s
    ```

    Failure when mutating `TypedContract.validate` to `return []`:
    ```
    FAILED tests/test_migration_compact_shims.py::CompactContractTests::test_negative_bad_vocabulary_is_flagged - AssertionError: False is not true
    FAILED tests/test_migration_compact_shims.py::CompactContractTests::test_deterministic_first_contract_missing_script_is_flagged - AssertionError: False is not true : expected 'names no reusable script' in problems: []
    FAILED tests/test_migration_compact_shims.py::CompactContractTests::test_negative_needless_subagent_is_rejected - AssertionError: False is not true : a needs_subagent contract must be flagged: []
    3 failed, 26 passed in 0.45s
    ```

    Failure when mutating `assert_no_needless_subagent` to `return None` before its `if`:
    ```
    FAILED tests/test_migration_compact_shims.py::CompactContractTests::test_negative_needless_subagent_is_rejected - AssertionError: CompactMigrationError not raised
    1 failed, 28 passed in 0.42s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` output listing every `ShimAndSkillTests` test as PASSED; paste the failures produced by scratch-mutating `detect_shim_drift` to negate its return and `old_invocation_still_works` to negate its final `return True` (each reverted afterwards).
  - Observed evidence:
    `ShimAndSkillTests` `-v` run:
    ```
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_old_invocation_still_works_nonexistent_command_is_false PASSED [  9%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_generate_compact_projection_skill_commands_override_and_default PASSED [ 18%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_argument_golden_parity_holds_for_every_compact_command PASSED [ 27%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_hand_edited_shim_fails_drift_check PASSED [ 36%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_every_compact_command_generates_a_shim PASSED [ 45%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_shim_resolves_correct_package_and_digest PASSED [ 54%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_negative_skill_bound_to_wrong_digest_is_detected PASSED [ 63%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_generate_compact_projection_unknown_skill_command_raises PASSED [ 72%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_selected_skill_resolves_correct_package_and_digest PASSED [ 81%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_old_invocations_still_work PASSED [ 90%]
    tests/test_migration_compact_shims.py::ShimAndSkillTests::test_generator_is_reused_not_forked PASSED [100%]
    11 passed in 0.38s
    ```

    Failure when scratch-mutating `detect_shim_drift` to negate its return:
    ```
    FAILED tests/test_migration_compact_shims.py::ShimAndSkillTests::test_hand_edited_shim_fails_drift_check - AssertionError: True is not false
    1 failed, 28 passed in 0.53s
    ```

    Failure when scratch-mutating `old_invocation_still_works` to negate its final `return True`:
    ```
    FAILED tests/test_migration_compact_shims.py::ShimAndSkillTests::test_old_invocations_still_work - AssertionError: False is not true : old invocation broke for 'getting-started'
    1 failed, 28 passed in 0.87s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `-v` output listing every `PromotionGateTests` test as PASSED; paste the failure produced by scratch-mutating `evaluate_promotion_gate` so its failing branch sets `advertised=True` and `migration_path=PATH_MIGRATED`, and the failure produced by scratch-mutating `_mv` to pass `sample_size=1` (each reverted afterwards).
  - Observed evidence:
    `PromotionGateTests` `-v` run:
    ```
    tests/test_migration_compact_shims.py::PromotionGateTests::test_critical_escape_fails_gate_even_with_perfect_quality PASSED [ 16%]
    tests/test_migration_compact_shims.py::PromotionGateTests::test_build_metric_summary_reaches_metric_value PASSED [ 33%]
    tests/test_migration_compact_shims.py::PromotionGateTests::test_gate_reuses_order13_and_cannot_be_weakened PASSED [ 50%]
    tests/test_migration_compact_shims.py::PromotionGateTests::test_failing_family_falls_back_to_legacy_with_corrective_item PASSED [ 66%]
    tests/test_migration_compact_shims.py::PromotionGateTests::test_passing_family_is_advertised_as_migrated PASSED [ 83%]
    tests/test_migration_compact_shims.py::PromotionGateTests::test_mixed_families_partition_correctly PASSED [100%]
    6 passed in 1.06s
    ```

    Failure when scratch-mutating `evaluate_promotion_gate` so failing branch sets `advertised=True` and `migration_path=PATH_MIGRATED`:
    ```
    FAILED tests/test_migration_compact_shims.py::PromotionGateTests::test_failing_family_falls_back_to_legacy_with_corrective_item - AssertionError: 'migrated' != 'legacy-fallback'
    FAILED tests/test_migration_compact_shims.py::PromotionGateTests::test_mixed_families_partition_correctly - AssertionError: Tuples differ: ('f-fail', 'f-pass') != ('f-pass',)
    FAILED tests/test_migration_compact_shims.py::PromotionGateTests::test_critical_escape_fails_gate_even_with_perfect_quality - AssertionError: True is not false
    3 failed, 26 passed in 3.17s
    ```

    Failure when scratch-mutating `_mv` to pass `sample_size=1`:
    ```
    FAILED tests/test_migration_compact_shims.py::PromotionGateTests::test_build_metric_summary_reaches_metric_value - AssertionError: 1 != 4
    FAILED tests/test_migration_compact_shims.py::PromotionGateTests::test_critical_escape_fails_gate_even_with_perfect_quality - AssertionError: True is not false
    2 failed, 27 passed in 0.46s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `-v` output listing every `ReportTests` test as PASSED; paste the failures produced by scratch-mutating `CompactProjection.to_dict` to return `{}` and to `return None` (its `b1mx2w` operator, which the recovered file alone does not kill, F-07), each reverted afterwards, with an added E-05 assertion among the failures.
  - Observed evidence:
    `ReportTests` `-v` run:
    ```
    tests/test_migration_compact_shims.py::ReportTests::test_report_is_deterministic_json_and_clean PASSED [100%]
    1 passed in 0.51s
    ```

    Failure when scratch-mutating `CompactProjection.to_dict` to return `{}`:
    ```
    FAILED tests/test_migration_compact_shims.py::ReportTests::test_report_is_deterministic_json_and_clean - KeyError: 'shim_paths'
    1 failed, 28 passed in 0.51s
    ```

    Failure when scratch-mutating `CompactProjection.to_dict` to return `None`:
    ```
    FAILED tests/test_migration_compact_shims.py::ReportTests::test_report_is_deterministic_json_and_clean - TypeError: 'NoneType' object is not subscriptable
    1 failed, 28 passed in 0.43s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the sweep output, one line per key naming the key, its operator, KILLED or SURVIVED, and the pytest summary line, covering all 24 `b1mx2w` keys with zero SURVIVED; paste the coverage `term-missing` output for `agent_workflows/migration_compact.py` from the Required tests reach command, with every listed miss outside the 24 key bodies; paste a final empty `git diff agent_workflows/` and `git status --short` showing no sweep script staged or tracked.
  - Observed evidence:
    Sweep output for all 24 keys (0 SURVIVED):
    ```
    evaluate_promotion_gate (return-none): KILLED (4 failed, 25 passed in 0.44s)
    build_metric_summary (return-none): KILLED (5 failed, 24 passed in 1.27s)
    TypedContract.validate (return-none): KILLED (6 failed, 23 passed in 0.43s)
    build_compact_package (return-none): KILLED (10 failed, 19 passed in 0.40s)
    generate_compact_projection (return-none): KILLED (9 failed, 20 passed in 0.56s)
    resolve_shim (return-none): KILLED (1 failed, 28 passed in 0.46s)
    check_compact_completeness (return-none): KILLED (2 failed, 27 passed in 0.42s)
    old_invocation_still_works (negate-return): KILLED (2 failed, 27 passed in 0.43s)
    TypedContract.to_dict (return-none): KILLED (1 failed, 28 passed in 0.56s)
    resolve_body_dir (return-none): KILLED (4 failed, 25 passed in 0.37s)
    argument_parity (negate-return): KILLED (1 failed, 28 passed in 0.76s)
    render_agent_report (return-none): KILLED (1 failed, 28 passed in 0.54s)
    CompactPackage.to_dict (return-none): KILLED (2 failed, 27 passed in 0.68s)
    skill_resolves_package (return-none): KILLED (1 failed, 28 passed in 0.86s)
    advertised_families (return-none): KILLED (3 failed, 26 passed in 0.75s)
    legacy_fallback_families (return-none): KILLED (2 failed, 27 passed in 0.82s)
    CompactProjection.to_dict (return-none): KILLED (1 failed, 28 passed in 0.60s)
    assert_no_needless_subagent (raise): KILLED (2 failed, 27 passed in 0.62s)
    CompactProjection.shim_for (return-none): KILLED (2 failed, 27 passed in 0.53s)
    _shim_view_digest (return-none): KILLED (1 failed, 28 passed in 1.35s)
    detect_shim_drift (negate-return): KILLED (1 failed, 28 passed in 0.60s)
    _mv (return-none): KILLED (5 failed, 24 passed in 2.67s)
    _workflow_by_command (return-none): KILLED (12 failed, 17 passed in 0.86s)
    build_all_compact_packages (return-none): KILLED (5 failed, 24 passed in 0.55s)
    Final outcome: ALL KILLED
    ```

    `python3 -m pytest tests/test_migration_compact_shims.py -o addopts="" --cov=agent_workflows.migration_compact --cov-report=term-missing`:
    ```
    Name                                   Stmts   Miss  Cover   Missing
    --------------------------------------------------------------------
    agent_workflows/migration_compact.py     238     20    92%   135, 323, 340, 345, 350, 402-407, 410, 417-419, 421, 426, 532, 562, 568, 606, 629, 658, 662
    --------------------------------------------------------------------
    TOTAL                                    238     20    92%
    ```

    Final `git diff agent_workflows/` is empty.
    Final `git status --short`:
    ```
    ?? tests/test_migration_compact_shims.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01).
- Scope fence: `tests/test_migration_compact_shims.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under the E-01 disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks and the E-06 sweep are scratch edits to `agent_workflows/migration_compact.py` that must be reverted before commit and must be absent from the diff; any sweep script lives in a gitignored scratch location and is never committed.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit syzi9i -- tests/test_migration_compact_shims.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize syzi9i` instead. Never hand-`git mv` the plan.
