# IPD: Restore behavioral test coverage for migration_compact contracts, projections, shim resolution and promotion gates

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `fdyjv6` (Set `trimgap`, group 11 of the `b1mx2w` filing plan) records that all 24 production keys in `agent_workflows/migration_compact.py` (210 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests lived in `tests/test_migration_compact_shims.py` (22 tests), deleted by the suite trim `19313eed`; `hpjj44` `## Derived properties` attributes the exclusive reach of every one of these keys to that file. The only surviving test touching the module, `test_core_module_coverage.test_migration_compact_families`, calls `advertised_families(())` on an empty tuple, which cannot distinguish a passing family from a failing one. So a mutation that, for example, made `evaluate_promotion_gate` advertise a failing family as migrated, made `TypedContract.validate` accept `needs_subagent=True`, or made `detect_shim_drift` miss a hand-edit, would pass the routine suite.
- Scope: Restore ONE behavioral test module at its original path, `tests/test_migration_compact_shims.py`, mined from `19313eed^:tests/test_migration_compact_shims.py`, marked `core` so the routine gate reaches it, and extended where the deleted file left a key's return value unasserted (the three `to_dict` methods and the fail-closed error branches). It drives all 24 keys named in `b1mx2w`: `evaluate_promotion_gate`, `build_metric_summary`, `_mv` (via `build_metric_summary`), `TypedContract.validate`, `TypedContract.to_dict`, `build_compact_package`, `build_all_compact_packages`, `generate_compact_projection`, `resolve_shim`, `check_compact_completeness`, `old_invocation_still_works`, `resolve_body_dir`, `_workflow_by_command` (via `resolve_body_dir` and `build_compact_package`), `argument_parity`, `render_agent_report`, `CompactPackage.to_dict`, `skill_resolves_package`, `advertised_families`, `legacy_fallback_families`, `CompactProjection.to_dict`, `CompactProjection.shim_for`, `assert_no_needless_subagent`, `_shim_view_digest` (via `detect_shim_drift`), `detect_shim_drift`. EXCLUDES any change to `agent_workflows/migration_compact.py` or any other production file; EXCLUDES the non-`migration_compact` keys that the same deleted file also reached (`benchmark_thresholds.evaluate_release_gate`, `host_adapters.SkillPackage.to_dict`, `engine.validate_shim_grammar`), which other `trimgap` items own; EXCLUDES the deleted `tests/test_exec_set_workflow.py`, whose only `migration_compact` use is one `detect_shim_drift(content, content)` call already covered here and whose remaining reach (`set_records`, `ipd_set_plan`) is not this item's module; and EXCLUDES the deleted `test_generator_is_reused_not_forked` `assertIs` symbol-identity assertions, which pin code structure (re-export identity) rather than behavior and so are forbidden by the AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" rule. Its behavioral half (projection shims equal the engine generator's output) IS restored.
- Scope-Paths: tests/test_migration_compact_shims.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: fdyjv6
- Set: trimgap
- Order: 11
- Highest E allocated: 05
- Author: opencode
- Id: syzi9i

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `fdyjv6`. Recovered the deleted module from `19313eed^`, ran it unchanged against HEAD `823b8e00e` (22 passed in 1.65s, slowest call 0.04s), and measured every expected value below by direct call (Findings F-02 to F-05) before writing it.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 24 `unguarded-unreached` `migration_compact` keys from backlog `fdyjv6` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its return values and raised errors. Done means a `return-none`, `negate-return` or `raise` mutation (the operators `b1mx2w` assigned these keys) of any of them turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restored behavioral test module

- [ ] E-01 Create `tests/test_migration_compact_shims.py` from `git show 19313eed^:tests/test_migration_compact_shims.py`, adding `import pytest` and module-level `pytestmark = pytest.mark.core`, and amending the module docstring to name backlog `fdyjv6`, findings `b1mx2w`, plan `syzi9i`, and the source `19313eed^`. Keep the stdlib `unittest.TestCase` classes as recovered (pytest collects them and applies the module mark). Remove from `test_generator_is_reused_not_forked` the two `assertIs(MCC.<symbol>, ENGINE.<symbol>)` lines (symbol-identity, structure-pinning), keeping its `assertEqual(projection.shims, direct)` behavioral assertion. No subprocess, no filesystem writes: every test reads the in-repo `SOURCE_WORKFLOWS`.
  - Depends on: none
  - Expected outcome: the file exists, is collected by a bare `python3 -m pytest` (it carries the `core` marker), and all recovered tests pass.
  - Execution state: pending

- [ ] E-02 Contract tests (`CompactContractTests`, recovered): completeness is clean for the nine `COMPACT_COMMANDS`; `resolve_body_dir("research", ...)` is `research-prompt`; every package from `build_all_compact_packages` has an empty `contract.validate()`; deterministic-first packages name a script; `assert_no_needless_subagent` accepts every real package and raises `CompactMigrationError` for a `needs_subagent=True` contract whose `validate()` reports `needless orchestration`; `build_compact_package("release-review", ...)` raises; out-of-vocabulary mode, boundary and interaction are each flagged. ADD: `resolve_body_dir("not-a-command", ...)` raises `CompactMigrationError` naming `not a live manifest row`; a deterministic-first `TypedContract` with `script=None` reports `names no reusable script`; `build_compact_package("verify", ...).to_dict()` equals a dict whose `command` is `verify`, `canonical_package` is `verify`, `body` equals the package `body`, `semantic_digest` equals the package digest, and `contract` equals `{"command": "verify", "mode": "deterministic-first", "input_kind": "arguments", "output_kind": "evidence", "write_boundary": "consented-write", "interaction": "optional", "needs_subagent": False, "script": "run_checks"}` (this reaches `CompactPackage.to_dict` and `TypedContract.to_dict` with a falsifiable value).
  - Depends on: E-01
  - Expected outcome: all recovered and added contract tests pass.
  - Execution state: pending

- [ ] E-03 Shim and skill tests (`ShimAndSkillTests`, recovered): `generate_compact_projection(...).shim_for(cmd)` returns at least 2 shims for every compact command; `resolve_shim` returns the right `command`, a `body_target` containing the command (or `research-prompt`), and a `semantic_digest` equal to the package's; `argument_parity` is True for every compact command; `detect_shim_drift` is False for an identical regeneration and True for an appended hand-edit; every selected skill `skill_resolves_package` its package, and a package with a `"0" * 64` digest does not; `old_invocation_still_works` is True for every compact command; projection shims equal `engine.generate_shim_members` output. ADD: `old_invocation_still_works("not-a-command", ...)` is False (the no-match branch); `generate_compact_projection(SOURCE_WORKFLOWS, skill_commands=["not-a-command"])` raises `CompactMigrationError`; `generate_compact_projection(SOURCE_WORKFLOWS, skill_commands=["spec"]).skill_packages` has exactly the key `spec` (the override branch); and the default projection's `skill_packages` key set is non-empty and a subset of `COMPACT_COMMANDS`.
  - Depends on: E-01
  - Expected outcome: all recovered and added shim/skill tests pass.
  - Execution state: pending

- [ ] E-04 Promotion-gate tests (`PromotionGateTests`, recovered): a passing summary at risk `low` yields `passed`, `PATH_MIGRATED`, `advertised`, no corrective item, and appears in `advertised_families`; a failing summary at risk `high` yields `PATH_LEGACY_FALLBACK`, not advertised, an `open` corrective item with non-empty findings, absent from `advertised_families` and present in `legacy_fallback_families`; a mixed pair partitions into `("f-pass",)` and `["f-fail"]`; a `RiskThresholds` with `max_critical_escapes=5` makes `ThresholdPolicy` raise `ThresholdError`; one critical escape fails a perfect-quality `low` gate. ADD: `build_metric_summary(requirement_recall=0.9, task_correctness=0.8, evidence_validity=0.7, critical_escapes=2, scope_violations=3, sample_size=4)` returns a `MetricSummary` whose `sample_size` is 4, `requirement_recall.value` 0.9, `task_correctness.value` 0.8, `evidence_validity.value` 0.7, `defect_escape.value` 0.5, `scope_violations.value` 3, and `requirement_recall.sample_size` 4 (this reaches `_mv` with a falsifiable value); and the failing decision's `to_dict()["corrective_item"]["family"]` equals the family name.
  - Depends on: E-01
  - Expected outcome: all recovered and added promotion-gate tests pass.
  - Execution state: pending

- [ ] E-05 Report tests (`ReportTests`, recovered): `render_agent_report` is identical across two calls, parses as JSON with empty `compact_completeness_findings` and `packages` keyed by exactly `COMPACT_COMMANDS`. ADD: `data["projection"]["shim_paths"]` is sorted, non-empty, and equals `sorted(generate_compact_projection(SOURCE_WORKFLOWS).shims)`; `data["projection"]["skill_packages"]` has the same key set as the default projection's `skill_packages` (this reaches `CompactProjection.to_dict` with a falsifiable value); and `data["packages"]["research"]["body"]` ends with `research-prompt/research-prompt.md`.
  - Depends on: E-01
  - Expected outcome: all recovered and added report tests pass.
  - Execution state: pending

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
| F-06 | `19313eed^:tests/test_exec_set_workflow.py` | Imports `migration_compact as MC` for one call, `MC.detect_shim_drift(content, content)`; nothing else from this module. Its other exclusive reach (`set_records.*`, `ipd_set_plan.*`) is outside this item. |

## Proposed changes (ordered, validatable)

1. E-01 restores the core-marked module and removes the structure-pinning lines.
2. E-02 covers typed contracts, body-dir resolution, package building and the no-needless-subagent guard.
3. E-03 covers projection, shim resolution, drift, argument parity, skill resolution and old invocations.
4. E-04 covers the metric-summary seam and the promotion gate partition.
5. E-05 covers the agent report and `CompactProjection.to_dict`.

## Deferred / out of scope (with reason)

- Non-`migration_compact` keys reached by the same deleted file (`benchmark_thresholds.evaluate_release_gate`, `host_adapters.SkillPackage.to_dict`, `engine.validate_shim_grammar`) are not this item's keys; the restored tests will incidentally execute them, but asserting their contracts belongs to the `trimgap` items filed for those modules.
  - Carrier-Declined: no work is owed by this plan; `b1mx2w` `## Filed items` routes those modules to their own backlog items.
- `tests/test_exec_set_workflow.py` is not restored: its single `migration_compact` call is duplicated by E-03's drift test (F-06).
  - Carrier-Declined: no `migration_compact` reach is lost; its remaining reach is outside this item's module.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All 24 keys from F-01 are driven by E-02 to E-05, private helpers through their public callers.

## Required tests / validation

- `python3 -m pytest tests/test_migration_compact_shims.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes with the new module included, with the summary line pasted.
- Reach: `python3 -m pytest tests/test_migration_compact_shims.py -o addopts="" --cov=agent_workflows.migration_compact --cov-report=term-missing` shows the bodies of all 24 keys executed; paste the output.
- Mutation spot-check: scratch, uncommitted edits to `agent_workflows/migration_compact.py`, one per V-item as listed there, each run against the new module with the failure pasted, then reverted with `git diff agent_workflows/` shown empty.

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

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat HEAD` (or `git status --short`) showing only `tests/test_migration_compact_shims.py` added; paste `python3 -m pytest --collect-only -q | rg -c test_migration_compact_shims` showing a nonzero count under the bare (core) selection; paste the bare `python3 -m pytest` summary line showing it passed; paste `rg -n "assertIs\(" tests/test_migration_compact_shims.py` returning no match.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every `CompactContractTests` test as PASSED, including the added error-branch, missing-script and `to_dict` tests; paste the failure produced by scratch-mutating `TypedContract.validate` to `return []` and the failure produced by scratch-mutating `assert_no_needless_subagent` to `return None` before its `if` (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing every `ShimAndSkillTests` test as PASSED; paste the failures produced by scratch-mutating `detect_shim_drift` to negate its return and `old_invocation_still_works` to negate its final `return True` (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing every `PromotionGateTests` test as PASSED; paste the failure produced by scratch-mutating `evaluate_promotion_gate` so its failing branch sets `advertised=True` and `migration_path=PATH_MIGRATED`, and the failure produced by scratch-mutating `_mv` to pass `sample_size=1` (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` output listing every `ReportTests` test as PASSED; paste the coverage `term-missing` output for `agent_workflows/migration_compact.py` showing all 24 keys' bodies executed; paste the failure produced by scratch-mutating `CompactProjection.to_dict` to return `{}`; paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_migration_compact_shims.py` through `aw commit <plan> -- tests/test_migration_compact_shims.py`; never push. Mutation spot-checks are scratch edits to `agent_workflows/migration_compact.py` that must be reverted before commit and must not appear in the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
