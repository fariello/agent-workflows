# IPD: Restore behavioral test coverage for migration_inventory disposition inventory, shared harnesses and plan-review views

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `igefrj` (Set `trimgap`, group 12 of the `b1mx2w` filing plan) records that 25 production keys in `agent_workflows/migration_inventory.py` (189 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests lived in `tests/test_migration_inventory_shared.py` (15 tests), deleted by the suite trim `19313eed`; `hpjj44` `## Derived properties` attributes the exclusive reach of every one of these keys to that file. The only surviving direct test of the module, `test_core_module_coverage.test_migration_inventory_dispositions`, imports `EXECUTION_MODES` and nothing that exercises the shared harnesses, the rollup gate, or the plan-review views. So a mutation that, for example, made `plan_rollup` skip its confirmation gate, made `assert_no_lens_fork` accept a reserved key, or made `detect_view_drift` always return False, would pass the routine suite.
- Scope: Restore ONE behavioral test module at its original path, `tests/test_migration_inventory_shared.py`, mined from `19313eed^:tests/test_migration_inventory_shared.py`, marked `core` so the routine gate reaches it, and extended where the deleted file left a key's return value unasserted or an error branch unexercised (`Disposition.to_dict`, `InventoryResult.to_dict` / `InventoryResult.ok` on a failing result, `LensModule.contribution`, `PersonaModule.contribution`, `HarnessRegistry.catalog_rows` row fields, and the unknown-member branches of `HarnessRegistry.resolve_lens` / `resolve_persona`). It drives all 25 keys named in `b1mx2w`: `_harness_ir`, `HarnessRegistry.catalog_rows`, `plan_rollup`, `build_assess_harness`, `plan_review_parity`, `build_advise_harness`, `Disposition.to_dict`, `_plan_review_views_from_ir`, `PlanReviewViews.view_digest`, `InventoryResult.to_dict`, `LensModule.contribution`, `assert_no_lens_fork`, `PersonaModule.contribution`, `compile_plan_review`, `HarnessRegistry.register_lens`, `HarnessRegistry.register_persona`, `HarnessRegistry.resolve_lens`, `HarnessRegistry.resolve_persona`, `render_agent_report`, `InventoryResult.ok`, `PlanReviewViews.semantic_digest`, `SharedHarness.compiled`, `SharedHarness.semantic_digest`, `detect_view_drift`, `plan_review_views_from_ir`. Private helpers (`_harness_ir`, `_plan_review_views_from_ir`) are driven through their public callers. EXCLUDES any change to `agent_workflows/migration_inventory.py` or any other production file; EXCLUDES the six other `migration_inventory` keys the same deleted file reached (`check_completeness`, `_command_disposition`, `enumerate_subjects`, `Disposition.validate`, `build_inventory`, `_catalog_disposition`), whose `b1mx2w` verdict is `budget-exhausted` (reached at baseline, mutation not completed) rather than `unguarded-unreached` and which are therefore not this item's keys; the restored tests will incidentally execute and assert them anyway. EXCLUDES `workflow_compiler._compile_step_packets`, which `hpjj44` also attributes to this file but which belongs to another module.
- Scope-Paths: tests/test_migration_inventory_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: igefrj
- Set: trimgap
- Order: 12
- Highest E allocated: 05
- Author: opencode
- Id: 94wi2f

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `igefrj`. Recovered the deleted module from `19313eed^`, ran it unchanged against HEAD `ddc7f543b` (15 passed in 0.87s, slowest call 0.02s), and measured every added expected value below by direct call (Findings F-02 to F-05) before writing it.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 25 `unguarded-unreached` `migration_inventory` keys from backlog `igefrj` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its return values and raised errors. Done means a `return-none`, `negate-return` or `raise` mutation (the operators `b1mx2w` assigned these keys) of any of them turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restored behavioral test module

- [ ] E-01 Create `tests/test_migration_inventory_shared.py` from `git show 19313eed^:tests/test_migration_inventory_shared.py`, adding `import pytest` and module-level `pytestmark = pytest.mark.core`, and amending the module docstring to name backlog `igefrj`, findings `b1mx2w`, plan `94wi2f`, and the source `19313eed^`. Keep the stdlib `unittest.TestCase` classes and the table-driven structure as recovered (pytest collects them and applies the module mark). The recovered file contains no `inspect`/`ast`/source-reading or symbol-identity assertions, so nothing is removed. No subprocess, no filesystem writes: every test reads the in-repo `SOURCE_WORKFLOWS` and the existing fixture `tests/fixtures/workflow-src/plan-review`.
  - Depends on: none
  - Expected outcome: the file exists, is collected by a bare `python3 -m pytest` (it carries the `core` marker), and all 15 recovered tests pass.
  - Execution state: pending

- [ ] E-02 Inventory and report tests (`InventoryCompletenessTests`, recovered): the eight-row mutation table over `check_completeness`, the live-inventory shape table, `render_agent_report` parses as JSON with `ok` True and `count` equal to the inventory size, and the alias-distinguishability test. ADD: `build_inventory(SOURCE_WORKFLOWS).dispositions["setup-repo"].to_dict()` equals `{"subject": "setup-repo", "kind": "command", "family": "setup-repo", "canonical_package": "setup-repo", "execution_mode": "guided", "interaction": "interactive", "risk": "medium", "skill_decision": "thin-entry", "orchestration_decision": "orchestrator", "evidence_level": "artifact", "aliases": [], "migration_owner": "order-15", "is_alias": False}`; the report's `dispositions["plan-review-long"]` has `is_alias` True and `canonical_package` `plan-review`, and its top-level key set is exactly `{"count", "dispositions", "findings", "ok"}` with `dispositions` keys sorted; `InventoryResult(dispositions={}, findings=["x"])` has `ok` False and `to_dict()` equal to `{"ok": False, "count": 0, "dispositions": {}, "findings": ["x"]}` (this reaches `InventoryResult.ok` under `negate-return` and `InventoryResult.to_dict` / `Disposition.to_dict` with a falsifiable value).
  - Depends on: E-01
  - Expected outcome: all recovered and added inventory/report tests pass.
  - Execution state: pending

- [ ] E-03 Shared-harness tests (`SharedHarnessTests`, recovered): the two-family resolution table (every lens through `assess`, every persona through `advise`, one digest per family, digests differ across families, catalog rows carry the harness digest, no reserved keys contributed); every `HARNESS_RESERVED_KEYS` key is refused by `assert_no_lens_fork`; a forking `LensModule` subclass is refused by `register_lens`. ADD: `build_assess_harness(...).resolve_lens("no-such-lens")` and `build_advise_harness(...).resolve_persona("no-such-persona")` each raise `InventoryError` naming `unknown lens concern` / `unknown persona`; a forking `PersonaModule` subclass whose `contribution()` adds `evidence` is refused by `register_persona` with `HarnessForkError`; `assess.lenses["security"].contribution()` equals `{"concern": "security", "lens_body": ".aw/system/workflows/assess/lenses/security.md", "rubric_focus": "Assess security posture and propose an IPD.", "lead_personas": []}`; `advise.personas["skeptic"].contribution()` has key set `{"persona", "persona_body", "charter"}` with `persona` `skeptic` and `persona_body` `.aw/system/workflows/advise/personas/skeptic.md`; `assess.catalog_rows()[0]` has `command` `assess-accessibility`, `harness` `assess`, `member` `accessibility`, `kind` `lens`, and `advise.catalog_rows()[0]` has `command` `advise-architect`, `kind` `persona`; `assess.harness.compiled()["manifest"]["id"]` is `assess` and `advise.harness.compiled()["manifest"]["id"]` is `advise` (this reaches `SharedHarness.compiled` and `_harness_ir` with a falsifiable value).
  - Depends on: E-01
  - Expected outcome: all recovered and added shared-harness tests pass.
  - Execution state: pending

- [ ] E-04 Rollup tests (`SharedHarnessTests`, recovered): the three confirmed-rollup rows (first-seen order `("security", "bugs")`, de-duplication with cost 2, `None` meaning every live lens with cost equal to the lens count), an unconfirmed rollup raising `RollupConfirmationError`, and an unknown lens raising `InventoryError`. ADD: `plan_rollup(assess, ["security"], confirmed=True, cost_per_member=3).estimated_cost_units` is 3 (the multiplier branch).
  - Depends on: E-01
  - Expected outcome: all recovered and added rollup tests pass.
  - Execution state: pending

- [ ] E-05 Plan-review view tests (`PlanReviewCollapseTests`, recovered): the three-row drift table (untampered shows no drift in either view; tampering one view drifts only that view), parity of the one package (`plan_review_parity(...).ok`, `aliases_ok`, `PLAN_REVIEW_ALIAS` in aliases, parity digest equals `views.semantic_digest()`, descriptor carries `takes_argument`), byte-identical recompilation, the `plan_review_views_from_ir` seam matching `compile_plan_review` on both view digests, and `view_digest("no-such-view")` raising `InventoryError`. ADD: a `PlanReviewViews` built with `dataclasses.replace(views, aliases=())` yields `plan_review_parity(...).aliases_ok` False, `ok` False, and a `reason` containing `expected canonical 'plan-review' with alias 'plan-review-long'` (the failing branch the recovered file never drives); and `compile_plan_review` on an empty temporary directory (pytest `tmp_path`) raises `InventoryError` naming `plan-review package failed to load`.
  - Depends on: E-01
  - Expected outcome: all recovered and added plan-review tests pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). No `inspect`, `ast`, regex over production source, caller counts, or symbol-identity pins. The recovered file already complies.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`; marker declared in `pyproject.toml` `markers`). A restored module must carry `pytestmark = pytest.mark.core` to be reached by the merge gate. `tests/test_core_module_coverage.py` is the established example (`pytestmark = pytest.mark.core`).
- Sibling plan `syzi9i` (Set `trimgap`, Order 11, backlog `fdyjv6`) is the established shape for this Set's restore plans: restore the deleted module at its original path, core-marked, extend where values were unasserted, no production change, scratch mutation spot-checks reverted before commit.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows `agent_workflows/migration_inventory.py::*`; `b1mx2w` `## Filing plan` row 12; `hpjj44` `## Derived properties` rows for each key | 31 module keys total: 25 `unreached` / `unguarded-unreached` (this item), 6 `budget-exhausted` (excluded). Operators: `return-none` (most), `negate-return` (`InventoryResult.ok`, `detect_view_drift`), `raise` (`assert_no_lens_fork`, `register_lens`, `register_persona`). `hpjj44` attributes each key's exclusive reach to `tests/test_migration_inventory_shared.py` (15 removed funcs). `rg migration_inventory tests/` finds only `test_core_module_coverage.test_migration_inventory_dispositions`. |
| F-02 | `git show 19313eed^:tests/test_migration_inventory_shared.py` copied to a scratch test path and run with `-o addopts=""` at HEAD `ddc7f543b`, then deleted | `15 passed in 0.87s`; slowest call 0.02s. The recovered file needs no API adaptation; its imports (`engine`, `migration_inventory`, `workflow_loader`, `tests.support.SOURCE_WORKFLOWS`) and fixture `tests/fixtures/workflow-src/plan-review` all exist at HEAD, and the path `tests/test_migration_inventory_shared.py` is unoccupied. |
| F-03 | direct calls at HEAD `ddc7f543b` | `build_assess_harness` has 31 lenses; `build_advise_harness` personas are `architect`, `domain-expert`, `naive-user`, `red-teamer`, `skeptic`, `spec-editor`, `staff-engineer`. First catalog rows: `assess-accessibility` (kind `lens`) and `advise-architect` (kind `persona`). Harness compiled manifest ids `assess` / `advise`; semantic digests differ (`5993a0f7...` vs `f7d7e743...`). `security` lens contribution and `skeptic` persona contribution are the values quoted in E-03. |
| F-04 | direct calls | `dispositions["setup-repo"].to_dict()` is the dict quoted in E-02; `plan-review-long` is `is_alias` True targeting `plan-review`; report keys `count`, `dispositions`, `findings`, `ok`, count 65, findings empty; `InventoryResult(dispositions={}, findings=["x"]).to_dict()` is `{"ok": False, "count": 0, "dispositions": {}, "findings": ["x"]}`; `resolve_lens("nope")` raises `unknown lens concern 'nope'`, `resolve_persona("nope")` raises `unknown persona 'nope'`. |
| F-05 | `migration_inventory.plan_review_parity`, `migration_inventory.compile_plan_review` | `plan_review_parity` sets `aliases_ok` only when the manifest id is `plan-review` AND `plan-review-long` is in `views.aliases`; emptying `aliases` drives the failing branch and its `reason` string. `compile_plan_review` raises `InventoryError("plan-review package failed to load: ...")` when `load_package` reports not ok. Fixture compile yields aliases `('plan-review-long',)`. |

## Proposed changes (ordered, validatable)

1. E-01 restores the core-marked module.
2. E-02 covers the inventory, `Disposition.to_dict`, `InventoryResult.ok`/`to_dict` and the agent report.
3. E-03 covers the two shared harnesses, registration-time fork refusal, member resolution and catalog rows.
4. E-04 covers the rollup confirmation gate, de-duplication and cost.
5. E-05 covers plan-review compilation, parity, view digests and drift.

## Deferred / out of scope (with reason)

- The six `budget-exhausted` `migration_inventory` keys (`check_completeness`, `_command_disposition`, `enumerate_subjects`, `Disposition.validate`, `build_inventory`, `_catalog_disposition`) are not this item's keys; the restored E-02 table asserts them anyway.
  - Carrier-Declined: no work is owed by this plan; `b1mx2w` records those keys as reached at baseline, not filed under `igefrj`.
- `workflow_compiler._compile_step_packets` (attributed to the same deleted file by `hpjj44`) belongs to another module.
  - Carrier-Declined: not a `migration_inventory` key; the restored E-05 tests incidentally execute it.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All 25 keys from F-01 are driven by E-02 to E-05, private helpers through their public callers.

## Required tests / validation

- `python3 -m pytest tests/test_migration_inventory_shared.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes with the new module included, with the summary line pasted.
- Reach: `python3 -m pytest tests/test_migration_inventory_shared.py -o addopts="" --cov=agent_workflows.migration_inventory --cov-report=term-missing` shows the bodies of all 25 keys executed; paste the output.
- Mutation spot-check: scratch, uncommitted edits to `agent_workflows/migration_inventory.py`, one per V-item as listed there, each run against the new module with the failure pasted, then reverted with `git diff agent_workflows/` shown empty.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore at the original path, or under a new name?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: original path. The file is restored verbatim plus additions (F-02), so its original name keeps `git log --follow` and the `hpjj44` / `b1mx2w` citations pointing at a real file; this matches sibling `syzi9i`. The path is unoccupied at HEAD.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` showing only `tests/test_migration_inventory_shared.py` added; paste `python3 -m pytest --collect-only -q | rg -c test_migration_inventory_shared` showing a nonzero count under the bare (core) selection; paste the bare `python3 -m pytest` summary line showing it passed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every `InventoryCompletenessTests` test as PASSED, including the added `to_dict` and failing-result tests; paste the failure produced by scratch-mutating `InventoryResult.ok` to `return bool(self.findings)` and the failure produced by scratch-mutating `Disposition.to_dict` to `return None` (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing every `SharedHarnessTests` harness test as PASSED, including the added unknown-member, persona-fork, contribution and catalog-row tests; paste the failures produced by scratch-mutating `assert_no_lens_fork` to `return None` as its first statement, `HarnessRegistry.register_persona` to skip its `assert_no_lens_fork` call, and `HarnessRegistry.catalog_rows` to `return None` (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing every rollup test as PASSED; paste the failure produced by scratch-mutating `plan_rollup` to remove its `if not confirmed: raise ...` gate (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` output listing every `PlanReviewCollapseTests` test as PASSED, including the added parity-failure and load-failure tests; paste the failures produced by scratch-mutating `detect_view_drift` to negate its return and `plan_review_parity` to set `aliases_ok = True` unconditionally (each reverted afterwards); paste the coverage `term-missing` output for `agent_workflows/migration_inventory.py` showing all 25 keys' bodies executed; paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_migration_inventory_shared.py` through `aw commit <plan> -- tests/test_migration_inventory_shared.py`; never push. Mutation spot-checks are scratch edits to `agent_workflows/migration_inventory.py` that must be reverted before commit and must not appear in the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
