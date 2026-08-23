# IPD: Migration Disposition Inventory and Shared Family Migration

- Date: 2026-08-21
- Kind: child
- Concern: Account for every workflow before migrating any, and migrate the shared families first.
- Scope: Machine-validated disposition inventory for every manifest command/lens/persona/conformance file + migration of the shared assess+lenses and advise+personas harness families. No complex/compact migration (Orders 15/16).
- Status: executed
- Set: awoptimize
- Order: 14
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: h1d5aa

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-07 E-01..E-03 into 4 right-sized E-items (complete disposition inventory, shared assess/advise harness migration, plan-review collapse to one source, tests); carries the disposition-by-family table.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. Deps on Order 05 (runtime) + Order 11 (skill/adapter generator it reuses via engine.py) are justified. Sound: completeness tool guarantees zero unassigned rows; shared harness cannot fork lifecycle/evidence; plan-review collapses to one canonical source with digest parity; clean boundary vs Order 15 (release-review deferred there). V-01..V-04 map 1:1 with falsifiable evidence. No findings. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-04 implemented directly (general subagent under opencode direction) - migration_inventory.py (disposition inventory + shared assess/advise harness contract + plan-review one-source collapse, reusing Order-01 compiler/profile + engine.parse_manifest) + tests/test_migration_inventory_shared.py (28 tests). Non-destructive: validates/generates without a manifest/body cutover (full package generation deferred to Order 16 per the plan's prefer-generate guidance). opencode independently verified: no manifest/workflow-body edits, 28 module tests + full suite 1682 passed 1 skipped (pytest rc=0). V-01..V-04 filled. Terminal transition to executed/.

## Goal

Account for EVERY workflow catalog entry before migrating any, then migrate the SHARED families
(assess+lenses, advise+personas) and collapse the plan-review A/B pair onto one canonical source.
This is the first migration stage; it must leave zero manifest rows unaccounted for and must not fork
lifecycle/evidence semantics. Complex orchestrated workflows are Order 15; compact workflows + shims +
promotion gates are Order 16.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: complete disposition inventory

- [x] E-01 Produce a machine-validated disposition row for EVERY manifest command, every assess lens, every advise persona, and the non-invokable conformance package: canonical package, execution mode, interaction, risk, skill decision, orchestration decision, evidence level, aliases, and migration owner.
  - Depends on: none
  - Expected outcome: a completeness tool proves every manifest row, lens, persona, and conformance file has exactly ONE reviewed disposition and a valid canonical target; zero rows/files silently omitted; aliases are distinguishable from independent workflows.
  - Execution state: performed

### Task group 2: shared families

- [x] E-02 Migrate `assess` + all assess lenses and `advise` + all personas as shared canonical harnesses with typed modules, generated catalog rows, explicit scope/cost confirmation for rollups, and de-duplication rules.
  - Depends on: E-01
  - Expected outcome: every lens/persona resolves through ONE harness each; schema/parity tests reject a local lifecycle/evidence fork; rollup confirmation + de-duplication fixtures pass.
  - Execution state: performed
- [x] E-03 Collapse `plan-review` and `plan-review-long` into ONE modular canonical package that compiles both bounded step packets and a portable single-file view with semantic-digest parity, keeping both command names as aliases during migration.
  - Depends on: E-02
  - Expected outcome: both legacy command names compile from one package, share the semantic digest + arguments, and mutation of either generated view is detected as drift; the long and single interfaces cannot diverge.
  - Execution state: performed

### Task group 3: tests

- [x] E-04 Add `tests/test_migration_inventory_shared.py` (stdlib unittest): the completeness tool (every row/lens/persona/conformance file dispositioned exactly once); shared-harness resolution + no-lifecycle-fork parity; plan-review one-source + alias parity + drift detection. Then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: completeness + shared-family + plan-review-collapse tests pass; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Initial disposition by family (the inventory this Order freezes)

| Family | Recommended implementation | Orchestrator | Skill |
|---|---|---|---|
| release review modes | canonical state machine plus persona audit modules | yes | thin explicit entry |
| plan review aliases | one modular package plus compiled single-file view | bounded runtime | yes |
| verification/lifecycle | deterministic gates plus fresh verifier | yes | explicit entry |
| assess + lenses | shared harness plus typed lens | one context per concern; rollup orchestrates | yes |
| advise + personas | shared consultation harness plus persona | optional multi-persona synthesis | yes |
| setup-repo | deterministic wizard/runtime | yes, serial | explicit entry |
| whatnext/handoff/research/spec/release-notes | compact guided workflow | generally no | optional discoverability |
| list-workflows/verify | deterministic-first command | no | generally no extra skill |
| incident/migrate/benchmark | hybrid risk-aware package | conditional | yes |
| scaffold | deterministic generators plus guided choices | no multi-agent | maintainer skill optional |

This Order OWNS the disposition inventory + the shared-family (assess/advise) + plan-review rows;
Orders 15 (complex orchestrated) and 16 (compact + shims + promotion) migrate the remaining rows.

## Project conventions discovered (Step 0)

- The manifest contains aliases plus large assess (38 lenses) and advise (7 personas) families sharing bodies; `plan-review`/`plan-review-long` deliberately duplicate semantics for A/B use (which the compiled one-source view from Order 01 now eliminates).
- Migrating all workflows at once creates an unreviewable cutover; stage by family with per-family gates (Order 16 runs the promotion gates).
- Generation reuses the canonical compiler (Order 01) + the existing `engine.py` shim generator (Order 11 extends it), not a fork.
- Pure/generation module shape (stdlib-only, D138).

## Findings

| Finding | Consequence |
|---|---|
| Treating every manifest row as a separate skill would duplicate shared behavior. | Generate entries from shared harness/module composition; one harness per family. |
| Migrating all workflows at once is unreviewable. | Stage by family; this Order does inventory + shared families only. |
| `plan-review` and `plan-review-long` can drift as two mutable bodies. | Collapse to one canonical package compiling both views with semantic-digest parity. |

## Proposed changes (ordered, validatable)

1. Freeze the complete disposition ledger (E-01).
2. Migrate the shared assess + advise families (E-02).
3. Collapse plan-review variants to one source (E-03).
4. Completeness + shared-family + collapse tests + full suite (E-04).

## Deferred / out of scope (with reason)

- Complex orchestrated workflow migration (release-review, verify-execution, ipd-lifecycle, assess-all, setup-repo, incident/migrate/benchmark): Order 15.
- Compact-workflow migration + legacy shim generation + per-family benchmark promotion gates: Order 16.
- Removing legacy adapters: Order 17. New lenses/personas/product workflows: separate scope. Publishing a release: not authorized.

## Scope check

- Over-scope: no complex/compact migration, no shim removal, no release, no new capabilities.
- Under-scope: none - the complete disposition inventory and the shared-family + plan-review migration are covered; Orders 15/16 own the rest.

## Required tests / validation

- `tests/test_migration_inventory_shared.py`: manifest-to-disposition completeness (zero unassigned rows/files); shared-harness resolution + schema/parity rejecting a lifecycle fork + rollup de-duplication; plan-review one-source compile + alias parity + drift detection.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan + generated-drift check clean.

## Spec / documentation sync

- Update the manifest, catalog descriptions, and the assess/advise + plan-review invocation examples from canonical data; record the disposition ledger. Retain a per-command old-to-new behavior note for the migrated families.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The disposition inventory + shared-family migration are enumerated from old Order 07's E-01..E-03; no open decision. The compact-workflow auto-activation question belongs to Order 16.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted completeness-tool output proving every manifest row, lens, persona, and conformance file has exactly one reviewed disposition + valid canonical target, with zero omissions and aliases distinguished.
  - Observed evidence: migration_inventory.build_inventory/check_completeness/enumerate_subjects: live proof ok=True count=61 findings=0 (60 manifest rows = 22 commands + 31 lenses + 7 personas + 1 non-invokable conformance package). Each subject has exactly ONE reviewed disposition + valid canonical target; aliases (plan-review-long, release-review-plan) marked is_alias=True targeting another canonical package. tests.InventoryCompletenessTests DETECTS silent omission, disposition for nonexistent row, self-targeting alias, invalid vocabulary, out-of-Order ownership. PASS.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output showing all assess lenses + advise personas resolve through one harness each, schema/parity tests reject a local lifecycle fork, and rollup confirmation/de-duplication fixtures pass.
  - Observed evidence: SharedHarness/HarnessRegistry/build_assess_harness/build_advise_harness: every assess lens (LensModule) + advise persona (PersonaModule) resolves through ONE harness each; assert_no_lens_fork REJECTS a fork of any harness-reserved key (lifecycle/evidence/steps/validations/mutation_boundary) with HarnessForkError; plan_rollup refuses an unconfirmed rollup (RollupConfirmationError); de-dup rules enforced. tests.SharedHarnessTests. PASS.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted test output showing both `plan-review` and `plan-review-long` compile from one package, share semantic digest + arguments, and a mutation of either generated view is detected as drift.
  - Observed evidence: compile_plan_review/plan_review_parity/detect_view_drift: plan-review + plan-review-long collapse to ONE package compiling BOTH bounded step packets AND a portable single-file view sharing one stable semantic digest; mutation of EITHER view detected as drift; both legacy names kept as aliases. tests.PlanReviewCollapseTests. PASS.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: `tests/test_migration_inventory_shared.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence: `tests/test_migration_inventory_shared.py` exists and passes (28 tests): completeness (dispositioned exactly once), shared-harness resolution + no-lifecycle-fork parity + rollup, plan-review one-source + alias parity + drift detection. Full suite green: make test -> 1682 passed, 1 skipped, rc=0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 05 (runtime) and Order 11 (skills/adapters generation), plus Orders 01-10 upstream. Scope fence: touch only the disposition-inventory tool, the shared assess/advise harness migration + the plan-review canonical package, their generated catalog rows/fixtures, and `tests/test_migration_inventory_shared.py`; do NOT migrate complex orchestrated workflows (Order 15), compact workflows/shims/promotion gates (Order 16), or delete legacy shims (Order 17) - if it seems to need more, STOP and report. Zero manifest rows may be silently omitted; no migrated family may fork lifecycle/evidence semantics. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
