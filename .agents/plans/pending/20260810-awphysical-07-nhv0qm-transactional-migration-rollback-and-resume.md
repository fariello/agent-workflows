# IPD: Transactional migration rollback and resume

- Date: 2026-08-10
- Kind: child
- Concern: Execute approved legacy-to-physical-layout migrations without loss, silent exposure, split authority, or irreversible partial state.
- Scope: Migration transaction state machine, immutable input verification, copy/verify/switch/retain phases, writer lock, Git-boundary staging, resume, rollback, retention, cleanup preview, CLI, and focused tests.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 7
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: nhv0qm

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to replace move-first migration with a journaled copy-verify-switch-retain protocol.

## Goal

Consume an approved, unchanged Order 06 migration map and migrate each repository through explicit recoverable phases. Never delete a legacy source during cutover, never allow two authoritative writers, never stage across the wrong Git repository, and never report success until independent comparison prerequisites are complete.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Freeze inputs and transaction state

- [ ] E-01 Implement a versioned migration transaction state machine with unique transaction ID, immutable inventory/map digests, policy digest, source/destination Git identities, phase journal, timestamps, acknowledgements, and last verified checkpoint stored under resolved runtime state.
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

- [ ] E-08 Add fault injection after every journaled operation and tests for stale inputs, concurrent writers, copy failure, verification mismatch, switch failure, process kill, disk/permission loss, cross-Git partial staging, resume, rollback, cleanup refusal, and source-checkout protection.
  - Depends on: E-01
  - Expected outcome: Every injected failure has exact authoritative-root, retained-source, journal, Git-index, exit-code, and recovery assertions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 02, 04, 05, and 06 must be executed and verified.
- Order 06 output is immutable transaction input, not a hint to recompute during apply.
- Migration never commits, pushes, deletes external repos/remotes, or removes legacy content during cutover.
- System source checkout is developer-owned and cannot be treated as an ordinary installed target.

## Findings

- Current migration uses a limited mapping and does not prove every legacy file by frozen hash.
- Per-file compensation alone is insufficient for multiple roots and Git repositories without an authoritative switch protocol.
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
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`

## Spec / documentation sync

- Update transaction, writer exclusion, Git-boundary, resume, rollback, retention, and cleanup sections of the controlling spec.
- Document operator recovery for each terminal/nonterminal transaction phase.
- Do not publish general migration instructions until Order 12 validates the entire flow.

## Open questions

No open questions. Migration copies and verifies before switching, retains legacy sources, and makes cleanup a later separately confirmed operation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: State-machine and stale-input tests prove one active writer, immutable inventory/policy/Git identity, durable checkpoints, and unambiguous recovery for every nonterminal phase.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Changes between inventory and apply stop before copy; lock ownership and stale-lock recovery are explicit and tested across interruption. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Every copied item is hash-verified against the frozen inventory and remains non-authoritative until the whole destination set verifies. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Failure before switch leaves legacy authoritative; failure after switch is detectable and rollbackable; no operation writes to both layouts. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Users can inspect or roll back after cutover; retained candid material does not become newly tracked or copied into the wrong repository. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Cross-repository moves are represented as independent deltas and recovery instructions; a failure in one Git owner cannot be presented as globally committed. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Repeated resume/rollback is safe; cleanup cannot run as part of migration, cannot touch foreign/changed items, and defaults to preview. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-08: Every injected failure has exact authoritative-root, retained-source, journal, Git-index, exit-code, and recovery assertions. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Frozen inputs, writer lock, copy/verify/switch/retain, Git boundaries, and recovery are inseparable parts of one safe migration transaction.

Execution requires verified Orders 02/04/05/06, a GO `/plan-review`, explicit human approval, and disposable fixture rehearsal before any real repository. Scope fence: migration transaction/status/resume/rollback/cleanup-preview logic and focused tests/docs. Never test mutation first on a human repository, never push, never auto-commit, never delete legacy or external content during cutover, and never cross-stage Git owners. Paste actual evidence, path-scope commits, and stop on any hash, identity, authority, privacy, or recovery mismatch. Complete pre-transition lint before moving this plan to `executed/`.
