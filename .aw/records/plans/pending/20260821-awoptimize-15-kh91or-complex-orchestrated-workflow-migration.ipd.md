# IPD: Complex Orchestrated Workflow Migration

- Date: 2026-08-21
- Kind: child
- Concern: Migrate the complex, stateful workflows onto the runtime/ledger/verifier architecture without semantic loss.
- Scope: Migrate release-review(+plan), verify-execution, ipd-lifecycle, assess-all, setup-repo, and incident/migrate/benchmark to deterministic orchestration with frozen modes, serialized mutation, and independent verification.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 15
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: kh91or

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-07 E-04..E-07 into 5 right-sized E-items (release-review, verify-execution+ipd-lifecycle, assess-all+setup-repo, incident/migrate/benchmark, tests).
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. Deps on the runtime/ledger/verifier layers (05-09) + 01-04 are all justified (each migrated complex workflow genuinely consumes packets/ledger/verifier/isolation). Verified every named workflow exists under .aw/system/workflows/. Sound: 52KB release-review protocol delivered just-in-time, terminal transitions executor-unreachable, planning/release boundary holds, incident/migrate/benchmark keep honest operator-data limits, clean boundary vs Order 14 (shared families) and Order 16 (compact). V-01..V-05 map 1:1 with falsifiable evidence. No findings. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

## Goal

Migrate the complex, stateful workflows onto the runtime/ledger/verifier architecture (Orders 02-09)
without semantic loss: release-review, verify-execution, ipd-lifecycle, assess-all, setup-repo, and
the risk-aware incident/migrate/benchmark family. Each keeps its judgment prose but moves sequencing,
gates, and terminal authority into deterministic code. Shared families are Order 14; compact
workflows + shims + promotion gates are Order 16.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: review and lifecycle

- [ ] E-01 Migrate `release-review` and `release-review-plan` to a deterministic coordinator with a frozen mode, persona/lens audit lanes, an issue ledger, a Fix Bar predicate, confirmation gates, serialized mutation, independent verification, and an explicit release boundary.
  - Depends on: none
  - Expected outcome: release fixtures cover both modes; every persona finding is dispositioned; planning mode cannot enter mutation or release states; the Fix Bar is computed; integration is serial; a release needs explicit authority.
  - Execution state: pending
- [ ] E-02 Migrate `verify-execution` and `ipd-lifecycle` to the runtime/ledger/verifier architecture, preserving corrective-IPD behavior and making terminal transitions mechanically unreachable to executor contexts.
  - Depends on: E-01
  - Expected outcome: verification/lifecycle fixtures inspect the actual diff + raw checks, emit corrective artifacts for gaps, and prove an executor context cannot perform a terminal move.
  - Execution state: pending

### Task group 2: aggregate, setup, and risk-aware

- [ ] E-03 Migrate `assess-all` to read-only parallel assessment lanes plus one coordinator-owned synthesis, and `setup-repo` to a deterministic interactive state machine with preflight, per-change consent, idempotency, rollback, and non-interactive refusal.
  - Depends on: E-02
  - Expected outcome: assess-all lanes are read-only and synthesis is single-writer; setup fixtures prove preflight, per-change consent, idempotency, rollback, and headless refusal before any mutation.
  - Execution state: pending
- [ ] E-04 Migrate `incident`, `migrate`, and `benchmark` as risk-aware orchestrated or hybrid packages with operator-owned external data clearly labeled, staged reversibility, consent gates, and verifiable artifacts.
  - Depends on: E-03
  - Expected outcome: fixtures label unavailable operator data, preserve rollback/consent boundaries, emit conformant artifacts, and refuse an unsupported certification/submission claim (honest limitations, not implied certification).
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_migration_complex.py` (stdlib unittest): the release two-mode + Fix Bar + planning-cannot-mutate + serial-integration fixtures; verification/lifecycle actual-diff + corrective + no-executor-terminal fixtures; assess-all read-only-lanes + single-writer-synthesis and setup preflight/consent/idempotency/rollback/headless fixtures; incident/migrate/benchmark operator-data + honest-limitation fixtures. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: all complex-workflow migration fixtures pass; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `release-review` is already modular but its run protocol is very large (~52 KB); it must be delivered just-in-time, not loaded whole.
- `verify-execution` and `ipd-lifecycle` are the repo's existing verification/transition workflows; migration must PRESERVE their corrective-IPD behavior and fail-closed gates, now enforced by the Order-02/03/04 ledger + the Order-05 runtime rather than prose.
- `assess-all` is a read-only-parallel + coordinator-synthesis pattern (D84-style); `setup-repo` is an ask-before-each-change mutating wizard that must stay serial + recoverable.
- `incident`/`migrate`/`benchmark` depend on operator-held data (monitoring, schedulers, live models) the repo cannot fabricate; honesty about that boundary is mandatory.
- Generation reuses the canonical compiler (Order 01) + runtime (Orders 05-07) + verifier (Orders 08-09); no forked orchestration.

## Findings

| Finding | Consequence |
|---|---|
| `release-review`'s 52 KB protocol degrades attention if loaded whole. | Deliver just-in-time via bounded packets (Order 06); the coordinator sequences deterministically. |
| Terminal transitions could otherwise be reachable from an executor context. | Migration makes terminal moves mechanically executor-unreachable (runtime + verifier own them). |
| Planning mode could slip into mutation/release. | A frozen mode + explicit release boundary; planning mode cannot enter mutation states. |
| incident/migrate/benchmark could imply certification the repo cannot back. | Label operator-owned data + refuse unsupported certification/submission claims. |

## Proposed changes (ordered, validatable)

1. Migrate release-review(+plan) to a deterministic coordinator with a release boundary (E-01).
2. Migrate verify-execution + ipd-lifecycle to runtime/ledger/verifier, executor-unreachable terminal (E-02).
3. Migrate assess-all (read-only lanes + single-writer synthesis) and setup-repo (recoverable wizard) (E-03).
4. Migrate incident/migrate/benchmark as risk-aware packages with honest operator-data limits (E-04).
5. Complex-workflow migration fixtures + full suite (E-05).

## Deferred / out of scope (with reason)

- The disposition inventory + shared assess/advise families + plan-review collapse: Order 14.
- Compact/deterministic workflow migration + legacy shim generation + per-family benchmark promotion gates: Order 16.
- Removing legacy adapters: Order 17. Publishing a release: not authorized (release-review migration preserves the boundary; it does not ship).

## Scope check

- Over-scope: no shared-family migration, no compact migration, no shim removal, no release, no new capabilities.
- Under-scope: none - the complex orchestrated workflows (review, lifecycle, aggregate, setup, risk-aware) are all owned here; Orders 14/16 own the rest.

## Required tests / validation

- `tests/test_migration_complex.py`: release two-mode + all-findings-dispositioned + planning-cannot-mutate + Fix Bar + serial integration + explicit release authority; verify-execution/ipd-lifecycle actual-diff + raw-checks + corrective artifacts + executor-cannot-terminal; assess-all read-only lanes + single-writer synthesis; setup-repo preflight/consent/idempotency/rollback/headless-refusal; incident/migrate/benchmark operator-data labels + honest-limitation refusals.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan + generated-drift + IPD lint clean.

## Spec / documentation sync

- Update the migrated workflows' catalog descriptions, invocation examples, and orchestration notes from canonical data; retain a per-command old-to-new behavior matrix + explicit fallback for each migrated complex workflow.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The complex-workflow migration targets + gates are enumerated from old Order 07's E-04..E-07; no open decision. Per-family promotion gating (whether a migrated family is advertised) is Order 16's benchmark step.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted release fixtures covering both modes, all persona findings dispositioned, planning mode unable to mutate, the Fix Bar computed, serial integration, and a release requiring explicit authority.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted verify-execution/ipd-lifecycle fixtures inspecting the actual diff + raw checks, emitting corrective artifacts for gaps, and proving an executor context cannot perform a terminal move.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted assess-all fixtures (read-only lanes, single-writer synthesis) and setup-repo fixtures (preflight, per-change consent, idempotency, rollback, headless refusal before mutation).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted incident/migrate/benchmark fixtures labeling unavailable operator data, preserving rollback/consent boundaries, emitting conformant artifacts, and refusing an unsupported certification/submission claim.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_migration_complex.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 14 (inventory + shared families) and the runtime/verifier layers (Orders 05-09), plus Orders 01-04. Scope fence: touch only the canonical packages + generated projections for release-review(+plan), verify-execution, ipd-lifecycle, assess-all, setup-repo, incident, migrate, benchmark, and `tests/test_migration_complex.py`; do NOT migrate compact workflows/shims/promotion gates (Order 16), remove legacy shims (Order 17), or publish a release - if it seems to need more, STOP and report. Preserve each migrated workflow's semantics (no behavior loss); terminal transitions stay executor-unreachable; planning/release boundaries hold. Execution contract: path-scoped commits per workflow family, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
