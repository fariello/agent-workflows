# IPD: Private companion attachment and durability

- Date: 2026-08-10
- Kind: child
- Concern: Make a separately access-controlled companion repository a first-class home for portable/private config, durable state, and records without overstating privacy or durability.
- Scope: Companion selection/identity, storage bundle layout, Git initialization and inspection, remote acknowledgement, registry bindings, commit boundaries, detach/reattach/move behavior, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 5
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: 1e9ggw

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created for the public-project plus private-companion use case and other external durable bundles.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.

## Goal

Allow a user to choose an existing companion directory/repository or initialize a local one, attach it to exactly one project identity, and store selected durable root classes there. AW must report observable Git and backup facts, require explicit remote/privacy acknowledgement, and never create, select, push, or delete a remote without authorization.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Define and validate companion identity

- [ ] E-01 Implement a portable companion identity document and, without duplicating Order 02 path ownership, a machine-local attachment record binding project ID, target identity hints, schema version, selected root classes, and companion Git common-dir without exposing machine-local paths in tracked content.
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

- [ ] E-05 Add dry-run-first attach, detach, move, reattach, and `aw storage status`/preflight warning flows with exact target/companion deltas, confirmation boundaries, recovery notes, and safeguards against deleting companion content or remotes.
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
- For target and companion separately, record `git status --short`, `git ls-files`, `git diff --cached --name-only`, and merge-base deltas; plant a candid record and absolute-path canary and require both absent from public target evidence.
- Sanitizer check over generated identity, policy, state, and output fixtures.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e01` | `tests/fixtures/awphysical/order05/e01-*` | A companion can move and reattach safely, cannot silently attach to a different project, and does not trust origin URL alone as identity. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e02` | `tests/fixtures/awphysical/order05/e02-*` | Unsafe or ambiguous attachment stops before writes and reports recovery choices without modifying either repository. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e03` | `tests/fixtures/awphysical/order05/e03-*` | The public-plus-private-companion preset has one private durable Git boundary and no candid target records; exact permitted commit destinations are available to producers and migration. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e04` | `tests/fixtures/awphysical/order05/e04-*` | Durability states distinguish unversioned, local Git, observed remote without acknowledgement, acknowledged durable arrangement, unreachable/unknown, and repository-managed cases honestly. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e05` | `tests/fixtures/awphysical/order05/e05-*` | Path changes update local bindings atomically; identity remains stable; detach preserves durable content; uninstall never deletes an external Git repository. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e06` | `tests/fixtures/awphysical/order05/e06-*` | AW identifies each Git owner, stages only within that owner when authorized, never commits or pushes across boundaries, and reports both worktrees independently. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e07` | `tests/fixtures/awphysical/order05/e07-*` | Every attachment and durability state has exact filesystem, identity, Git, output, and no-side-effect assertions. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Verify implementation against the controlling specification's companion bundle, identity, durability, privacy, Git-boundary, detach/reattach, and uninstall requirements. Stop and return the specification to review on conflict.
- Document only observable privacy/durability claims and explicit user responsibilities.
- End-user migration instructions remain Order 12.

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


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Companion identity, durable bundle materialization, Git observation, attachment lifecycle, and commit boundaries are one external-storage trust boundary.

Execution requires verified Orders 01/02 and the Order 03 handoff, a GO `/plan-review`, and human approval. Scope fence: companion identity/registry/storage/Git status and their CLI surfaces/tests/docs only. Never create or modify a remote, authenticate, commit, push, delete companion content, or migrate legacy data in this Order. Paste actual outputs, path-scope commits, never broad-stage, and never push. Stop on identity, privacy, durability, or Git-boundary uncertainty. Complete evidence and lint before moving the plan to `executed/`.
