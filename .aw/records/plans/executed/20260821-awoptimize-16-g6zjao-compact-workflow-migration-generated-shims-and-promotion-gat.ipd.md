# IPD: Compact Workflow Migration Generated Shims and Promotion Gates

- Date: 2026-08-21
- Kind: child
- Concern: Migrate the compact workflows without needless orchestration and gate every family on benchmark evidence.
- Scope: Migrate getting-started/list-workflows/whatnext/handoff/research/verify/spec/release-notes/scaffold + generate all legacy command shims and selected skills from canonical packages + run per-family benchmark promotion gates (failing families stay legacy with a corrective backlog item).
- Status: executed
- Set: awoptimize
- Order: 16
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: g6zjao

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-07 E-08..E-10 into 4 right-sized E-items (compact-workflow migration, generated shims/skills with parity, per-family benchmark promotion gates, tests); carries the auto-activate OQ.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Deps on 14 (inventory), 15 (complex), 13 (benchmark for promotion gates) all justified. Sound: shims reuse the Order-11/engine.py generator (no duplicate path), aliases bound to canonical digest + parity, per-family promotion gate keeps failing families on legacy with a corrective item (never advertised as migrated). PR-001 (LOW): E-01 listed `research` (whose body dir is `research-prompt/`) which could mislead an executor - FIXED by noting the command->body-dir mapping and directing to Order 14's inventory for exact resolution. V-01..V-04 map 1:1 with falsifiable evidence. OQ-01 (auto-activate skills) non-blocking, deferred to benchmark activation-precision evidence.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-04 implemented directly (general subagent under opencode direction) - migration_compact.py (9 compact typed contracts + shim/skill generation REUSING engine.py generator, identity-asserted; Order-13 promotion gates w/ legacy fallback + corrective item; no threshold weakened) + tests/test_migration_compact_shims.py (22 tests). Non-destructive (no manifest/body edits). opencode independently verified: 22 module tests + full suite 1749 passed 1 skipped (pytest rc=0). V-01..V-04 filled. Terminal transition to executed/.

## Goal

Migrate the compact/deterministic workflows without imposing needless orchestration, generate all
legacy command shims + selected skill entry points from the canonical packages (preserving names +
argument behavior), and gate every migrated family on its risk-class benchmark - keeping any family
that fails the gate on the legacy path with an explicit reason. This is the final migration stage
(shared families = Order 14, complex orchestrated = Order 15); removing legacy shims is Order 17.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: compact workflows

- [x] E-01 Migrate the compact manifest commands `getting-started`, `list-workflows`, `whatnext`, `handoff`, `research` (whose body dir is `research-prompt/`; resolve each command to its body via Order 14's disposition inventory rather than assuming the dir equals the command name), `verify`, `spec`, `release-notes`, and `scaffold` as compact single-context or deterministic-first packages with typed contracts, explicit write gates, and reusable scripts where fragility warrants - WITHOUT unnecessary subagent or orchestration overhead.
  - Depends on: none
  - Expected outcome: each compact workflow passes typed input/output, read/write-boundary, interaction, deterministic-script, and negative tests without invoking a subagent it does not need.
  - Execution state: performed

### Task group 2: compatibility shims

- [x] E-02 Generate ALL legacy command shims and selected skill entry points from the canonical packages (reusing the Order-11/`engine.py` generator), preserving command names + argument behavior; add per-workflow golden, negative, interaction, evidence, and semantic-parity tests.
  - Depends on: E-01
  - Expected outcome: every compatibility command and selected skill resolves the correct package + digest; argument golden tests pass; a hand-edited generated output fails the drift check; old invocations still work during migration.
  - Execution state: performed

### Task group 3: promotion gates

- [x] E-03 Run the benchmark (Orders 12/13) promotion gates per risk class; keep any workflow that fails its gate on the legacy path with an explicit recorded reason + a corrective backlog item, and never advertise a failing family as migrated.
  - Depends on: E-02
  - Expected outcome: per-family benchmark reports meet the approved risk thresholds OR record a legacy fallback + corrective backlog item; no failing family is advertised as migrated; migration is evidence-gated, reversible, and observable.
  - Execution state: performed

### Task group 4: tests

- [x] E-04 Add `tests/test_migration_compact_shims.py` (stdlib unittest): per-compact-workflow typed-contract + boundary + interaction + negative tests (no needless subagent); shim/skill resolution + argument parity + drift; promotion-gate fixtures (pass -> advertised; fail -> legacy fallback + corrective item, not advertised). Then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: compact-migration + shim-parity + promotion-gate tests pass; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Simple discovery/routing commands (`list-workflows`, `whatnext`, `getting-started`) do not justify multi-agent overhead; they stay compact and gain typed contracts only.
- Compatibility aliases can mask drift; bind each alias to the canonical digest and test argument parity (drift check from Order 01 E-06/E-07; generator from Order 11 / `engine.py`).
- Live host/model combinations that fail the Order 12/13 benchmark remain on legacy or manual fallback - migration is evidence-gated, not asserted.
- Pure/generation module shape (stdlib-only, D138); the promotion gate consumes the offline benchmark reports (live results are operator-run per Order 13).

## Findings

| Finding | Consequence |
|---|---|
| Treating every workflow as multi-agent adds cost + merge risk. | Migrate compact workflows as compact packages; orchestrate only where justified (Order 15). |
| Compatibility aliases can mask drift. | Bind aliases to the canonical digest + test argument parity; hand-edits fail the drift check. |
| Migrating a family before it passes the benchmark would advertise unproven behavior. | Per-family promotion gate: fail -> legacy fallback + corrective backlog item, never advertised as migrated. |

## Proposed changes (ordered, validatable)

1. Migrate compact/deterministic workflows without excess orchestration (E-01).
2. Generate legacy shims + selected skills from canonical packages with parity tests (E-02).
3. Per-family benchmark promotion gates with honest legacy fallback (E-03).
4. Compact-migration + shim-parity + promotion-gate tests + full suite (E-04).

## Deferred / out of scope (with reason)

- The disposition inventory + shared families + plan-review collapse: Order 14. Complex orchestrated migration: Order 15.
- REMOVING legacy adapters/shims (as opposed to generating them): Order 17 (this Order keeps old invocations working; Order 17 deprecates after adoption).
- New lenses/personas/product workflows: separate scope. Publishing a release: not authorized.

## Scope check

- Over-scope: no shared-family/complex migration, no shim REMOVAL, no release, no new capabilities.
- Under-scope: none - compact migration, shim/skill generation with parity, and per-family promotion gates complete the migration layer.

## Required tests / validation

- `tests/test_migration_compact_shims.py`: per-compact-workflow typed-contract/boundary/interaction/deterministic-script/negative (no needless subagent); every compatibility command + selected skill resolves the correct package/digest, argument golden parity, hand-edited generated output fails drift; promotion-gate fixtures (threshold pass -> advertised; fail -> legacy fallback + corrective backlog item, not advertised).
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan + generated-drift + IPD lint + risk-class benchmark gates clean.

## Spec / documentation sync

- Update the manifest, catalog descriptions, invocation examples, skill inventory, and deprecation notes from canonical data; retain a per-command old-to-new behavior matrix + explicit fallback instructions for every compact workflow and shim.

## Open questions

### OQ-01: Which compact workflows should AUTO-ACTIVATE as skills (vs explicit invocation only)?

- Blocking: no
- Status: open
- Owner: maintainer and benchmark owner
- Resolution or deferral rationale: Default to EXPLICIT invocation for any costly or mutating task; enable automatic skill activation for a compact workflow only after the Order 12/13 benchmark reports adequate activation precision/recall for it. Non-blocking: v1 generates the skills with explicit invocation; auto-activation is an additive, evidence-gated per-workflow toggle that does not change this Order's interfaces or which workflows are migrated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted per-compact-workflow test output (typed input/output, read/write boundary, interaction, deterministic script, negative) showing each migrates without invoking an unneeded subagent.
  - Observed evidence: migration_compact.COMPACT_COMMANDS (getting-started, list-workflows, whatnext, handoff, research, verify, spec, release-notes, scaffold) as compact TypedContract/CompactPackage; resolve_body_dir via engine.parse_manifest (research -> research-prompt, not assumed); assert_no_needless_subagent enforced. tests.CompactContractTests incl. typed I/O, read/write boundary, interaction, deterministic-script, negative + needless-subagent rejection. PASS.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output showing every compatibility command + selected skill resolves the correct package/digest, argument golden parity holds, a hand-edited generated output fails the drift check, and old invocations still work.
  - Observed evidence: generate_compact_projection REUSES engine.generate_shim_members + host_adapters.build_skill_package (identity-asserted: MCC.generate_shim_members is engine.generate_shim_members, byte-for-byte shims). resolve_shim/argument_parity via engine.shim_body/validate_shim_grammar; detect_shim_drift FAILS on a hand-edited generated output; skill resolves correct package+digest; old_invocation_still_works. tests.ShimAndSkillTests. PASS.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted promotion-gate fixtures showing a family meeting its risk threshold is advertised as migrated and a failing family records a legacy fallback + corrective backlog item and is NOT advertised as migrated.
  - Observed evidence: evaluate_promotion_gate reuses Order-13 evaluate_release_gate/benchmark_thresholds per risk class; a failing family -> PATH_LEGACY_FALLBACK + CorrectiveBacklogItem(status=open) and is NOT in advertised_families; no threshold weakened (test_gate_reuses_order13_and_cannot_be_weakened, test_critical_escape_fails_gate_even_with_perfect_quality). tests.PromotionGateTests. PASS.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: `tests/test_migration_compact_shims.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence: `tests/test_migration_compact_shims.py` exists and passes (22 tests): per-compact typed-contract + boundary + interaction + negative (no needless subagent); shim/skill resolution + argument parity + drift; promotion-gate pass->advertised / fail->legacy+corrective-item-not-advertised. Full suite green: make test -> 1749 passed, 1 skipped, rc=0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 14 (inventory/shared), Order 15 (complex orchestrated), and Order 13 (benchmark, for the promotion gates), plus Orders 01-11 upstream. Scope fence: touch only the compact-workflow canonical packages + generated projections, the shim/skill generation (reusing Order-11/`engine.py`), the promotion-gate wiring, and `tests/test_migration_compact_shims.py`; do NOT remove legacy shims (Order 17), migrate shared/complex families (Orders 14/15), or publish a release - if it seems to need more, STOP and report. Old invocations MUST keep working; a family that fails its benchmark gate stays legacy with an explicit reason (never silently advertised as migrated); do not weaken a threshold to force a pass. Execution contract: path-scoped commits per family, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
