# IPD: Workflow Family Migration

- Date: 2026-08-21
- Kind: child
- Concern: Migrate every workflow catalog entry to the appropriate canonical, deterministic, skill, or orchestrated form without semantic loss.
- Scope: Complete manifest disposition, canonical package migration, generated adapters, workflow-specific tests, and deprecation aliases. No compatibility removal or release.
- Status: reviewed
- Set: awoptimize
- Order: 7
- Highest E allocated: 10
- Author: Codex GPT-5.6 Sol
- Id: 01iuql

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created from the complete 151-file workflow inventory and family analysis.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Broadest-scope child (migrates all 60 manifest rows + 38 lenses + 7 personas) but appropriately staged (shared families -> complex orchestrated -> compact) with per-family benchmark promotion gates and explicit legacy fallback. PR-A size assessment corrected exception->standard (10 leaves/3 groups, neither threshold exceeded); the per-stage independent-review-checkpoint requirement was moved from the cohesion field into the gate prose so it is preserved as an execution rule. E-01 completeness tooling guarantees zero unassigned rows. OQ-01 (which compact workflows auto-activate as skills) is non-blocking, correctly deferred to activation-precision evidence. This Order sequences after Orders 01-06.

## Goal

Apply the new architecture selectively rather than forcing every command into an orchestrator. Complex workflows get deterministic orchestration and isolated verification, shared families keep one harness plus modules, and simple workflows remain compact while gaining typed inputs, outputs, and evidence where appropriate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Inventory and shared families

- [ ] E-01 Produce a machine-validated disposition row for every manifest command, every assess lens, every advise persona, and the non-invokable conformance package; include canonical package, execution mode, interaction, risk, skill decision, orchestration decision, evidence level, aliases, and migration owner.
  - Depends on: none
  - Expected outcome: zero manifest rows or package files are silently omitted and aliases are distinguishable from independent workflows.
  - Execution state: pending
- [ ] E-02 Migrate `assess` plus all assess lenses and `advise` plus all personas as shared canonical harnesses with typed modules, generated catalog rows, explicit scope/cost confirmation for rollups, and de-duplication rules.
  - Depends on: E-01
  - Expected outcome: concern/persona modules cannot fork lifecycle or evidence semantics and every module passes schema and dispatch tests.
  - Execution state: pending
- [ ] E-03 Collapse `plan-review` and `plan-review-long` into one modular canonical package that compiles both bounded step packets and a portable single-file view with semantic-digest parity.
  - Depends on: E-02
  - Expected outcome: the long and single interfaces remain aliases during migration and cannot drift.
  - Execution state: pending

### Complex orchestrated workflows

- [ ] E-04 Migrate `release-review` and `release-review-plan` to a deterministic coordinator with frozen mode, persona/lens audit lanes, issue ledger, Fix Bar predicate, confirmation gates, serialized mutation, independent verification, and release boundary.
  - Depends on: E-03
  - Expected outcome: the 52 KB protocol is delivered just in time, every finding is dispositioned, and planning mode cannot enter mutation or release states.
  - Execution state: pending
- [ ] E-05 Migrate `verify-execution` and `ipd-lifecycle` to the runtime/ledger/verifier architecture, preserving corrective-IPD behavior and making terminal transitions mechanically unreachable to executor contexts.
  - Depends on: E-04
  - Expected outcome: actual diff, raw checks, intent coverage, and lifecycle gates are enforced, not merely requested.
  - Execution state: pending
- [ ] E-06 Migrate `assess-all` to read-only parallel assessment lanes plus one coordinator-owned synthesis, and migrate `setup-repo` to a deterministic interactive state machine with preflight, per-change consent, idempotency, rollback, and noninteractive refusal.
  - Depends on: E-05
  - Expected outcome: parallelism is used only for independent analysis and setup mutations remain serialized and recoverable.
  - Execution state: pending
- [ ] E-07 Migrate `incident`, `migrate`, and `benchmark` as risk-aware orchestrated or hybrid packages with operator-owned external data clearly labeled, staged reversibility, consent gates, and verifiable artifacts.
  - Depends on: E-06
  - Expected outcome: missing production evidence or scheduler authority produces honest limitations instead of implied certification.
  - Execution state: pending

### Compact and deterministic workflows

- [ ] E-08 Migrate `getting-started`, `list-workflows`, `whatnext`, `handoff`, `research`, `verify`, `spec`, `release-notes`, and `scaffold` as compact single-context or deterministic-first packages with typed contracts, explicit write gates, and reusable scripts where fragility warrants.
  - Depends on: E-07
  - Expected outcome: these workflows gain precision without unnecessary subagent or orchestration overhead.
  - Execution state: pending
- [ ] E-09 Generate all legacy command shims and selected skill entry points from canonical packages, preserving names and argument behavior; add per-workflow golden, negative, interaction, evidence, and semantic-parity tests.
  - Depends on: E-08
  - Expected outcome: old invocations work during migration and every adapter resolves to the intended package and digest.
  - Execution state: pending
- [ ] E-10 Run the benchmark promotion gates per risk class and keep any failing workflow on the legacy path with an explicit reason and corrective backlog item.
  - Depends on: E-09
  - Expected outcome: migration is evidence-gated and partial rollout is honest, reversible, and observable.
  - Execution state: pending

## Initial disposition by family

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

## Project conventions discovered (Step 0)

- The manifest contains aliases plus large assess and advise families sharing bodies.
- `release-review` is already modular but its run protocol is very large.
- `plan-review` and `plan-review-long` deliberately duplicate semantics for A/B use.
- Simple discovery and routing commands do not justify multi-agent overhead.

## Findings

| Finding | Consequence |
|---|---|
| Treating every manifest row as a separate skill would duplicate shared behavior. | Generate entries from shared harness/module composition. |
| Treating every workflow as multi-agent adds cost and merge risk. | Orchestrate only when independent work, isolation, or deterministic gates justify it. |
| Compatibility aliases can mask drift. | Bind aliases to canonical digest and test argument parity. |
| Migrating all workflows at once creates an unreviewable cutover. | Stage by family and retain per-workflow promotion gates. |

## Proposed changes (ordered, validatable)

1. Freeze the complete disposition ledger.
2. Migrate shared assess and advise families.
3. Collapse plan-review variants to one source.
4. Migrate complex stateful workflows.
5. Migrate compact and deterministic workflows without excess orchestration.
6. Generate compatibility adapters and per-family tests.
7. Promote only families that pass risk-class benchmarks.

## Deferred / out of scope (with reason)

- Removal of legacy adapters belongs to Order 08.
- New assess lenses, advise personas, or product workflows are separate scope.
- Live host/model combinations that fail Order 06 remain on legacy or manual fallback.
- Publishing a release is not authorized.

## Scope check

- Over-scope: no new workflow capabilities, release, push, or compatibility deletion.
- Under-scope: complete disposition and every existing workflow family are explicitly owned.

## Required tests / validation

- Manifest-to-disposition completeness with zero unassigned rows/files.
- Per-family schema, compilation, semantic-digest, command argument, and interaction tests.
- Release plan-only mutation refusal and release-boundary tests.
- Verifier isolation and terminal-authority tests.
- Shared harness/lens/persona no-drift tests.
- Full suite, leak scan, generated drift, IPD lint, and risk-class benchmark gates.

## Spec / documentation sync

- Update the manifest, catalog descriptions, invocation examples, skill inventory, orchestration diagrams, and deprecation notes from canonical data.
- Retain a per-command old-to-new behavior matrix and explicit fallback instructions.

## Open questions

### OQ-01: Which compact workflows should auto-activate as skills?

- Blocking: no
- Status: open
- Owner: maintainer and benchmark owner
- Resolution or deferral rationale: default to explicit invocation for costly or mutating tasks; use activation precision/recall evidence before enabling automatic activation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a completeness tool proves every manifest row, lens, persona, and conformance file has exactly one reviewed disposition and valid canonical target.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: all assess lenses and advise personas resolve through one harness each, schema/parity tests reject local lifecycle forks, and rollup confirmation/de-duplication fixtures pass.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: both legacy command names compile from one package, share semantic digest and arguments, and mutation of either generated view is detected as drift.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: release fixtures cover both modes, all persona findings are dispositioned, planning mode cannot mutate, Fix Bar is computed, integration is serial, and release needs explicit authority.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: verification/lifecycle fixtures inspect actual diff and raw checks, emit corrective artifacts for gaps, and prove executor contexts cannot perform terminal moves.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: assess-all parallel lanes are read-only and synthesis is single-writer; setup fixtures prove preflight, per-change consent, idempotency, rollback, and headless refusal before mutation.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: incident/migrate/benchmark fixtures label unavailable operator data, preserve rollback/consent boundaries, emit conformant artifacts, and refuse unsupported certification or submission claims.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: each compact workflow passes typed input/output, read/write boundary, interaction, deterministic script, and negative tests without unnecessary subagent invocation.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: every compatibility command and selected skill resolves correct package/digest, argument golden tests pass, and hand-edited generated outputs fail drift checks.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: per-family benchmark reports meet approved risk thresholds or record legacy fallback plus corrective backlog; no failing family is advertised as migrated.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 01 through 06 and approved per-family rollout order. Execute the family stages in the listed order (shared families, then complex orchestrated, then compact/deterministic) with an independent review checkpoint after each stage rather than migrating all families in one pass. Stop a family migration if benchmark gates fail; do not weaken thresholds or silently fall back.

Execution contract: path-scoped commits per family, no push or broad staging, raw parity and benchmark evidence retained. The coordinator alone advances family stage and terminal status.
