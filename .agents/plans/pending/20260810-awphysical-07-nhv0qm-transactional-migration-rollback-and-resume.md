# IPD: Transactional migration rollback and resume

- Date: 2026-08-10
- Kind: child
- Concern: Execute approved legacy-to-physical-layout migrations without loss, silent exposure, split authority, or irreversible partial state.
- Scope: Migration transaction state machine, immutable input verification, copy/verify/switch/retain phases, writer lock, Git-boundary staging, resume, rollback, retention, cleanup preview, CLI, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 7
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: nhv0qm

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to replace move-first migration with a journaled copy-verify-switch-retain protocol.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.

## Goal

Consume an approved, unchanged Order 06 migration map and migrate each repository through explicit recoverable phases. Never delete a legacy source during cutover, never allow two authoritative writers, never stage across the wrong Git repository, and never report success until independent comparison prerequisites are complete.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Freeze inputs and transaction state

- [ ] E-01 Replace the current non-copying `execute_migration` path with a versioned migration transaction state machine with unique transaction ID, immutable inventory/map digests, policy digest, source/destination Git identities, phase journal, timestamps, acknowledgements, and last verified checkpoint stored under resolved runtime state.
  - Depends on: none
  - Expected outcome: Apply refuses stale or edited inventory, map, policy, roots, or Git identity; only one transaction/writer can be active; every phase is resumable or rollbackable.
  - Execution state: pending

- [ ] E-02 Add a repository/project writer lock and pre-apply revalidation of source hashes, destinations, disk space, permissions, dirty/conflicted Git state, companion identity, backups, and external-root accessibility.
  - Depends on: E-01
  - Expected outcome: Changes between inventory and apply stop before copy; lock ownership and stale-lock recovery are explicit and tested across interruption.
  - Execution state: pending

### Task group 2: Copy, verify, and switch once

- [ ] E-03 Implement phase-scoped copy into transaction-specific staging destinations, preserving bytes, modes, safe symlinks, relative identities, and record lifecycle; never overwrite collisions or follow links outside approved roots.
  - Depends on: E-01
  - Expected outcome: Every copied item is hash-verified against the frozen inventory and remains non-authoritative until the whole destination set verifies.
  - Execution state: pending

- [ ] E-04 Implement destination verification and one authoritative policy/registry switch written last, with durable switch receipt and compatibility-reader activation; block all legacy writers before and after switch.
  - Depends on: E-01
  - Expected outcome: Failure before switch leaves legacy authoritative; failure after switch is detectable and rollbackable; no operation writes to both layouts.
  - Execution state: pending

- [ ] E-05 Preserve legacy sources in a read-only retained state with exact old-to-new mapping, hashes, rollback instructions, retention trigger, and no automatic deletion; move transient backups/journals to runtime state.
  - Depends on: E-01
  - Expected outcome: Users can inspect or roll back after cutover; retained candid material does not become newly tracked or copied into the wrong repository.
  - Execution state: pending

### Task group 3: Git boundaries, recovery, and cleanup

- [ ] E-06 Generate separate target, companion, and source-repository staging/commit plans; stage only with explicit confirmation, never commit or push automatically, and verify each index contains only intended paths.
  - Depends on: E-01
  - Expected outcome: Cross-repository moves are represented as independent deltas and recovery instructions; a failure in one Git owner cannot be presented as globally committed.
  - Execution state: pending

- [ ] E-07 Implement idempotent status, resume, and rollback commands for every failure point, plus a separate post-retention cleanup preview/apply command requiring fresh inventory, independent postcheck success, and explicit high-warning confirmation.
  - Depends on: E-01
  - Expected outcome: Repeated resume/rollback is safe; cleanup cannot run as part of migration, cannot touch foreign/changed items, and defaults to preview.
  - Execution state: pending

- [ ] E-08 Add journal read/resume/rollback plus fault injection after every journaled operation and tests for stale inputs, concurrent writers, copy failure, verification mismatch, switch failure, process kill, disk/permission loss, cross-Git partial staging, resume, rollback, cleanup refusal, and source-checkout protection.
  - Depends on: E-01
  - Expected outcome: Every injected failure has exact authoritative-root, retained-source, journal, Git-index, exit-code, and recovery assertions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 02, 04, 05, and 06 must be executed and verified.
- Order 06 output is immutable transaction input, not a hint to recompute during apply.
- Migration never commits, pushes, deletes external repos/remotes, or removes legacy content during cutover.
- System source checkout is developer-owned and cannot be treated as an ordinary installed target.
- Spec traceability: E-01/E-02 implement Sections 7 and 11.2; E-03 through E-06 implement Section 11.2; E-07/E-08 implement Sections 11.2, 11.3, and 13.

## Findings

- Current migration uses a limited mapping and does not prove every legacy file by frozen hash.
- Reuse and extend `project_layout.TransactionJournal.compensate` and `engine.run_rollback`; per-file compensation alone is insufficient for multiple roots and Git repositories without an authoritative switch protocol.
- Changing policy before records verify can strand writers; deleting legacy sources early can lose candid untracked/ignored material.
- Cross-Git migration requires distinct staging and commit transactions even when one AW command coordinates them.

## Proposed changes (ordered, validatable)

1. Freeze transaction inputs and single-writer journal.
2. Revalidate environment before writes.
3. Copy into staged destinations and hash-verify every item.
4. Switch authoritative policy exactly once and last.
5. Retain legacy sources and rollback evidence.
6. Separate all Git-owner deltas.
7. Implement resume, rollback, and separately gated cleanup.
8. Fault-inject every phase.

## Deferred / out of scope (with reason)

- Remote commits/pushes and access-control changes are out of scope.
- Producer implementation is Order 08; this Order only blocks legacy writes through the switch contract.
- Independent completion certification is Order 10.
- Final source-repository execution is Order 11.

## Scope check

- Over-scope: Transactional migration/recovery only; no workflow feature redesign or remote mutation.
- Under-scope: Frozen inputs, locks, staging, hashes, switch, retention, Git boundaries, resume, rollback, cleanup, interruptions, source mode, and every phase failure are included.

## Required tests / validation

- Unit/state-machine tests for every valid/invalid phase transition and journal version.
- Fault-injection integration tests after every write/pivot/stage operation.
- Hash comparison with Order 06 inventory before and after copy.
- Separate `git status --short` and `git diff --cached --name-only` assertions for every Git owner.
- `python3 -m unittest tests.test_layout_migration tests.test_acceptance_matrix` plus new migration transaction suites.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e01` | `tests/fixtures/awphysical/order07/e01-*` | Apply refuses stale or edited inventory, map, policy, roots, or Git identity; only one transaction/writer can be active; every phase is resumable or rollbackable. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e02` | `tests/fixtures/awphysical/order07/e02-*` | Changes between inventory and apply stop before copy; lock ownership and stale-lock recovery are explicit and tested across interruption. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e03` | `tests/fixtures/awphysical/order07/e03-*` | Every copied item is hash-verified against the frozen inventory and remains non-authoritative until the whole destination set verifies. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e04` | `tests/fixtures/awphysical/order07/e04-*` | Failure before switch leaves legacy authoritative; failure after switch is detectable and rollbackable; no operation writes to both layouts. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e05` | `tests/fixtures/awphysical/order07/e05-*` | Users can inspect or roll back after cutover; retained candid material does not become newly tracked or copied into the wrong repository. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e06` | `tests/fixtures/awphysical/order07/e06-*` | Cross-repository moves are represented as independent deltas and recovery instructions; a failure in one Git owner cannot be presented as globally committed. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e07` | `tests/fixtures/awphysical/order07/e07-*` | Repeated resume/rollback is safe; cleanup cannot run as part of migration, cannot touch foreign/changed items, and defaults to preview. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-08 | `python3 -m unittest tests.test_layout_migration.TransactionalMigrationTests.test_e08` | named injections: `stale-input`, `concurrent-writer`, `copy-failure`, `verify-mismatch`, `switch-failure`, `kill-after-switch-before-receipt`, `disk-loss`, `permission-loss`, `cross-git-partial-stage`, `resume`, `rollback`, `cleanup-refusal`, `source-protection` | Every injection asserts exact exit and journal phase. In `kill-after-switch-before-receipt`, exactly one physical backend is authoritative, legacy writers are disabled, every retained-source hash equals the frozen inventory, target and companion indexes are clean, and resume or rollback is explicitly available. | any injection is absent, authority is zero/dual, a retained hash/index differs, exit is wrong, or recovery is unavailable |

## Spec / documentation sync

- Verify implementation against the controlling specification's transaction, writer-exclusion, Git-boundary, resume, rollback, retention, and cleanup requirements. Stop and return the specification to review on conflict.
- Document operator recovery for each terminal/nonterminal transaction phase.
- Do not publish general migration instructions until Order 12 validates the entire flow.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: yes
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` is `to-review`. This plan MUST NOT execute until that spec is independently reviewed and human-approved; approval is a design gate, not an executor inference.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Run Evidence matrix row E-01 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Run Evidence matrix row E-02 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Run Evidence matrix row E-03 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Run Evidence matrix row E-04 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Run Evidence matrix row E-05 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Run Evidence matrix row E-06 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Run Evidence matrix row E-07 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: Run Evidence matrix row E-08 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Frozen inputs, writer lock, copy/verify/switch/retain, Git boundaries, and recovery are inseparable parts of one safe migration transaction.

Execution requires verified Orders 02/04/05/06, a GO `/plan-review`, explicit human approval, and disposable fixture rehearsal before any real repository. Scope fence: migration transaction/status/resume/rollback/cleanup-preview logic and focused tests/docs. Never test mutation first on a human repository, never push, never auto-commit, never delete legacy or external content during cutover, and never cross-stage Git owners. Paste actual evidence, path-scope commits, and stop on any hash, identity, authority, privacy, or recovery mismatch. Complete pre-transition lint before moving this plan to `executed/`.
