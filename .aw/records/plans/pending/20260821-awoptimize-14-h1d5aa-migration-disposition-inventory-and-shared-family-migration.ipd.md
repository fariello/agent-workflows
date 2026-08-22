# IPD: Migration Disposition Inventory and Shared Family Migration

- Date: 2026-08-21
- Kind: child
- Concern: Account for every workflow before migrating any, and migrate the shared families first.
- Scope: Machine-validated disposition inventory for every manifest command/lens/persona/conformance file + migration of the shared assess+lenses and advise+personas harness families. No complex/compact migration (Orders 15/16).
- Status: draft
- Set: awoptimize
- Order: 14
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: h1d5aa

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

## Goal

Account for EVERY workflow catalog entry before migrating any, then migrate the SHARED families
(assess+lenses, advise+personas) and collapse the plan-review A/B pair onto one canonical source.
This is the first migration stage; it must leave zero manifest rows unaccounted for and must not fork
lifecycle/evidence semantics. Complex orchestrated workflows are Order 15; compact workflows + shims +
promotion gates are Order 16.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: complete disposition inventory

- [ ] E-01 Produce a machine-validated disposition row for EVERY manifest command, every assess lens, every advise persona, and the non-invokable conformance package: canonical package, execution mode, interaction, risk, skill decision, orchestration decision, evidence level, aliases, and migration owner.
  - Depends on: none
  - Expected outcome: a completeness tool proves every manifest row, lens, persona, and conformance file has exactly ONE reviewed disposition and a valid canonical target; zero rows/files silently omitted; aliases are distinguishable from independent workflows.
  - Execution state: pending

### Task group 2: shared families

- [ ] E-02 Migrate `assess` + all assess lenses and `advise` + all personas as shared canonical harnesses with typed modules, generated catalog rows, explicit scope/cost confirmation for rollups, and de-duplication rules.
  - Depends on: E-01
  - Expected outcome: every lens/persona resolves through ONE harness each; schema/parity tests reject a local lifecycle/evidence fork; rollup confirmation + de-duplication fixtures pass.
  - Execution state: pending
- [ ] E-03 Collapse `plan-review` and `plan-review-long` into ONE modular canonical package that compiles both bounded step packets and a portable single-file view with semantic-digest parity, keeping both command names as aliases during migration.
  - Depends on: E-02
  - Expected outcome: both legacy command names compile from one package, share the semantic digest + arguments, and mutation of either generated view is detected as drift; the long and single interfaces cannot diverge.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_migration_inventory_shared.py` (stdlib unittest): the completeness tool (every row/lens/persona/conformance file dispositioned exactly once); shared-harness resolution + no-lifecycle-fork parity; plan-review one-source + alias parity + drift detection. Then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: completeness + shared-family + plan-review-collapse tests pass; the full serial suite is green (pasted).
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: pasted completeness-tool output proving every manifest row, lens, persona, and conformance file has exactly one reviewed disposition + valid canonical target, with zero omissions and aliases distinguished.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted test output showing all assess lenses + advise personas resolve through one harness each, schema/parity tests reject a local lifecycle fork, and rollup confirmation/de-duplication fixtures pass.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted test output showing both `plan-review` and `plan-review-long` compile from one package, share semantic digest + arguments, and a mutation of either generated view is detected as drift.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_migration_inventory_shared.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 05 (runtime) and Order 11 (skills/adapters generation), plus Orders 01-10 upstream. Scope fence: touch only the disposition-inventory tool, the shared assess/advise harness migration + the plan-review canonical package, their generated catalog rows/fixtures, and `tests/test_migration_inventory_shared.py`; do NOT migrate complex orchestrated workflows (Order 15), compact workflows/shims/promotion gates (Order 16), or delete legacy shims (Order 17) - if it seems to need more, STOP and report. Zero manifest rows may be silently omitted; no migrated family may fork lifecycle/evidence semantics. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
