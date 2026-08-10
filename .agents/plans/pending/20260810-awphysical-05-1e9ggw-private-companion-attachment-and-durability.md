# IPD: Private companion attachment and durability

- Date: 2026-08-10
- Kind: child
- Concern: Make a separately access-controlled companion repository a first-class home for portable/private config, durable state, and records without overstating privacy or durability.
- Scope: Companion selection/identity, storage bundle layout, Git initialization and inspection, remote acknowledgement, registry bindings, commit boundaries, detach/reattach/move behavior, and focused tests.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 5
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: 1e9ggw

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created for the public-project plus private-companion use case and other external durable bundles.

## Goal

Allow a user to choose an existing companion directory/repository or initialize a local one, attach it to exactly one project identity, and store selected durable root classes there. AW must report observable Git and backup facts, require explicit remote/privacy acknowledgement, and never create, select, push, or delete a remote without authorization.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Define and validate companion identity

- [ ] E-01 Implement a portable companion identity document and machine-local attachment record binding project ID, target identity hints, schema version, selected root classes, and companion Git common-dir without exposing machine-local paths in tracked content.
  - Depends on: none
  - Expected outcome: A companion can move and reattach safely, cannot silently attach to a different project, and does not trust origin URL alone as identity.
  - Execution state: pending

- [ ] E-02 Add preflight validation for existing/non-existing directories, nested/overlapping Git repositories, symlinks, worktrees, case aliases, conflicting identities, dirty state, inaccessible paths, and public-target leakage.
  - Depends on: E-01
  - Expected outcome: Unsafe or ambiguous attachment stops before writes and reports recovery choices without modifying either repository.
  - Execution state: pending

### Task group 2: Materialize and report durable storage

- [ ] E-03 Materialize the selected companion `.aw/config`, `.aw/state/durable`, and `.aw/records` classes plus managed ignore rules for local config and runtime data; keep runtime outside tracked companion history unless custom policy explicitly chooses an untracked companion path.
  - Depends on: E-01
  - Expected outcome: The public-plus-private-companion preset has one private durable Git boundary and no candid target records; exact permitted commit destinations are available to producers and migration.
  - Execution state: pending

- [ ] E-04 Implement explicit local Git initialization, existing Git inspection, remote enumeration, reachability/status reporting, and acknowledgement/revocation without inferring remote privacy, creating remotes, authenticating, fetching, committing, or pushing automatically.
  - Depends on: E-01
  - Expected outcome: Durability states distinguish unversioned, local Git, observed remote without acknowledgement, acknowledged durable arrangement, unreachable/unknown, and repository-managed cases honestly.
  - Execution state: pending

### Task group 3: Operate the attachment safely

- [ ] E-05 Add dry-run-first attach, detach, move, reattach, status, and doctor flows with exact target/companion deltas, confirmation boundaries, recovery notes, and safeguards against deleting companion content or remotes.
  - Depends on: E-01
  - Expected outcome: Path changes update local bindings atomically; identity remains stable; detach preserves durable content; uninstall never deletes an external Git repository.
  - Execution state: pending

- [ ] E-06 Enforce repository-specific staging and commit instructions so target and companion changes are never combined, and expose clean machine output for migration and postcheck.
  - Depends on: E-01
  - Expected outcome: AW identifies each Git owner, stages only within that owner when authorized, never commits or pushes across boundaries, and reports both worktrees independently.
  - Execution state: pending

- [ ] E-07 Add existing-private-repo, new-local-repo, no-Git, multiple-remotes, unacknowledged remote, acknowledged remote, move/reattach, worktree, nested-repo, identity conflict, public leak, dirty state, and uninstall tests.
  - Depends on: E-01
  - Expected outcome: Every attachment and durability state has exact filesystem, identity, Git, output, and no-side-effect assertions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 01, 02, and the relevant Order 03 wizard handoff must be verified.
- Privacy is never inferred from a remote URL or provider name.
- Credentials and secrets must never be stored in AW policy, identity, state, history, or test fixtures.
- External repositories are never deleted by uninstall or cleanup.

## Findings

- Current `companion` defaults to `<repo>.aw/records` and routes only records.
- The wizard does not collect a companion path or existing private repository.
- Storage initialization can run `git init`, but remote acknowledgement is separate and not integrated into the install decision.
- Config and durable state cannot currently be selected into the same companion bundle through the wizard.

## Proposed changes (ordered, validatable)

1. Define companion identity and local attachment records.
2. Validate paths, Git topology, identity, and target leakage.
3. Materialize selected durable classes and ignore runtime/local data.
4. Implement honest Git/durability inspection and explicit acknowledgement.
5. Add safe attachment lifecycle operations.
6. Enforce independent Git commit destinations.
7. Test every topology and failure boundary.

## Deferred / out of scope (with reason)

- Remote creation, access-control administration, credential handling, commit, push, or deletion are out of scope.
- Bulk legacy migration is Order 07.
- General cloud backup integrations require separate decisions.

## Scope check

- Over-scope: Companion identity/storage/Git observation only; no provider API, remote mutation, push, or record-content interpretation.
- Under-scope: Existing/new companion, selected durable classes, runtime exclusion, identity conflicts, moves, worktrees, remotes, acknowledgements, staging boundaries, uninstall, public leakage, and machine output are included.

## Required tests / validation

- `python3 -m unittest tests.test_storage tests.test_project_registry tests.test_project_context tests.test_acceptance_matrix`
- New companion topology and identity fixtures with real local Git repositories and synthetic remote URLs.
- Target and companion `git status --short` plus index assertions after every mutating fixture.
- Sanitizer check over generated identity, policy, state, and output fixtures.
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`

## Spec / documentation sync

- Update companion bundle, identity, durability, privacy, Git boundary, detach/reattach, and uninstall sections of the controlling spec.
- Document only observable privacy/durability claims and explicit user responsibilities.
- End-user migration instructions remain Order 12.

## Open questions

No open questions. The companion may hold selected durable classes; runtime/local material remains untracked; remote changes require separate explicit user action.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Move/reattach and conflict tests prove stable identity without tracked machine paths, reject a mismatched project and origin-spoofing case, and preserve both repositories byte-for-byte on failed attachment.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Unsafe or ambiguous attachment stops before writes and reports recovery choices without modifying either repository. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: The public-plus-private-companion preset has one private durable Git boundary and no candid target records; exact permitted commit destinations are available to producers and migration. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Durability states distinguish unversioned, local Git, observed remote without acknowledgement, acknowledged durable arrangement, unreachable/unknown, and repository-managed cases honestly. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Path changes update local bindings atomically; identity remains stable; detach preserves durable content; uninstall never deletes an external Git repository. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: AW identifies each Git owner, stages only within that owner when authorized, never commits or pushes across boundaries, and reports both worktrees independently. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Every attachment and durability state has exact filesystem, identity, Git, output, and no-side-effect assertions. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Companion identity, durable bundle materialization, Git observation, attachment lifecycle, and commit boundaries are one external-storage trust boundary.

Execution requires verified Orders 01/02 and the Order 03 handoff, a GO `/plan-review`, and human approval. Scope fence: companion identity/registry/storage/Git status and their CLI surfaces/tests/docs only. Never create or modify a remote, authenticate, commit, push, delete companion content, or migrate legacy data in this Order. Paste actual outputs, path-scope commits, never broad-stage, and never push. Stop on identity, privacy, durability, or Git-boundary uncertainty. Complete evidence and lint before moving the plan to `executed/`.
