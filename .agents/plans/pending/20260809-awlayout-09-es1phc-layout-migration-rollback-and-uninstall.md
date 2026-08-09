# IPD: Layout migration, rollback, and uninstall

- Date: 2026-08-09
- Kind: child
- Concern: Migrate legacy and policy-changing installations transactionally while preserving user data, Git history, and rollback evidence.
- Scope: `agent_workflows/layout_migration.py`, migration integration in installer and uninstall commands, migration fixtures, and `tests/test_layout_migration.py`.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 9
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: es1phc

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L9-01 (add §15.2 rule-2 PRE-move destination-writability + free-space precondition check as a gating step). L9-02 (add coverage for the guarded deep-removal path - explicit high-warning opt-in, explains recoverability - and that uninstall never deletes a configured external remote, §15.4). L9-03 (assert the §15.3 single-authoritative-writer invariant during the compatibility window: dual-read allowed, dual-write forbidden). Positive: migration is transactional with real rollback + preserve-on-uninstall-by-default tests.

## Goal

Provide a dry-run-first, recoverable transition from legacy installed paths and between record backends. Never overwrite drifted content, lose history, or delete user-controlled config, state, or records during update or uninstall.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Planning and execution

- [ ] E-01 Implement a versioned migration planner that inventories source ownership, classifies managed, unchanged, drifted, and unknown files, maps each item to the new logical root, and emits a complete no-write plan.
  - Depends on: none
  - Expected outcome: users and tests can inspect every create, copy, move, preserve, conflict, and cleanup action before mutation.
  - Execution state: pending
- [ ] E-02 Execute approved migrations transactionally: copy and verify records first, preserve conflicts beside destinations, commit config and state only after verification, switch registry policy last, and retain a rollback journal.
  - Depends on: E-01
  - Expected outcome: interruption at any injected step leaves either the old layout active or a journaled, resumable state with no lost source.
  - Execution state: pending
- [ ] E-03 Support tracked legacy, clean-delta legacy, home, companion, and repository transitions; detect target Git staging, merges, renames, and worktrees from the merge base without resetting or discarding unrelated changes.
  - Depends on: E-02
  - Expected outcome: migration coexists with dirty repositories and explains any user-owned Git follow-up precisely.
  - Execution state: pending

### Task group 2: Recovery and removal

- [ ] E-04 Implement `aw migrate-layout --dry-run`, apply, resume, rollback, and status plus ownership-aware uninstall that removes managed `system` files and adapters but preserves config, state, records, registry associations, and migration journals by default.
  - Depends on: E-03
  - Expected outcome: lifecycle commands are explicit, idempotent, and conservative with user data.
  - Execution state: pending
- [ ] E-05 Add `tests/test_layout_migration.py` for every legacy and backend route, drift, dirty Git, worktrees, symlinks, low-space and interrupted failures, resume, rollback, repeated migration, and uninstall preservation.
  - Depends on: E-04
  - Expected outcome: migration safety is demonstrated under both normal and adversarial conditions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Existing transactions and manifests should be extended rather than bypassed.
- User worktree changes are never cleanup targets.
- Managed-file hashes can identify unchanged payloads; unknown or drifted content requires preservation.
- Destructive cleanup must be the last phase and only target verified managed paths.

## Findings

| Phase | Safety invariant |
|---|---|
| Inventory | no writes |
| Copy | sources remain intact |
| Verify | hashes and expected structure agree |
| Switch | new policy becomes active only after data verification |
| Cleanup | only verified managed duplicates are eligible |

## Proposed changes (ordered, validatable)

1. Build a complete migration plan.
2. Execute copy, verify, switch, and journal transactionally.
3. Handle backend and Git-state combinations.
4. Expose recovery and conservative uninstall commands.
5. Test failures at every phase.

## Deferred / out of scope (with reason)

- Rewriting public Git history to remove previously committed candid records is excluded and requires repository-specific security review.
- Creating or pushing remote repositories is excluded.
- Clean-delta global skill cutover is Order 10.

## Scope check

- Over-scope: no history rewrite, remote provisioning, credential work, or deletion of preserved user data.
- Under-scope: legacy discovery, all backend transitions, drift, transactions, resume, rollback, Git coexistence, and uninstall are covered.

## Required tests / validation

- `python3 -m unittest tests.test_layout_migration -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m agent_workflows migrate-layout --dry-run --json`

## Spec / documentation sync

- Keep the version mapping and preservation rules aligned with the canonical 2026-08-09 layout specification.
- User migration documentation is completed in Order 11 after command behavior is proven.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: fixture plans account for every source item, classify ownership and drift, and perform no filesystem or Git mutation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: injected interruption at each phase proves no source loss, correct active policy, and successful resume or rollback from the journal.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: backend matrix tests preserve unrelated staged, unstaged, untracked, worktree, and merge-base changes without reset or broad staging.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: command tests prove dry run, apply, resume, rollback, repeated invocation, and default preservation on uninstall.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: focused and full suites pass, including failure injection and low-space simulations with byte-for-byte source preservation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: forward migration, recovery, and uninstall require one ownership-aware transaction model.

STOP if Orders 03, 05, 06, or 08 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
