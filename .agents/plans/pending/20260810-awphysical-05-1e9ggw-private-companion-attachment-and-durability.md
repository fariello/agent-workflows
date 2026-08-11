# IPD: Private companion attachment and durability

- Date: 2026-08-10
- Kind: child
- Concern: Make a separately access-controlled companion repository a first-class home for portable/private config, durable state, and records without overstating privacy or durability.
- Scope: Companion selection/identity, storage bundle layout, Git initialization and inspection, remote acknowledgement, registry bindings, commit boundaries, detach/reattach/move behavior, and focused tests.
- Status: executed
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
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): final cursory re-review after GPT-5.6 1544-01 closeout (0f6f238) - all 13 conforming at review-finalize, residuals closed (Order 01/02/05/06 canary fixtures, Order 04 path-equality-only, Order 07 test-module + per-fault, Order 09 clean_delta planted-write, Order 12 token->test binding), full suite 825 OK. Controlling spec 20260810-1447-01 advanced to reviewed. Set remains NO-GO pending HUMAN approval of the spec (the sole remaining gate); Status unchanged (reviewed).
- 2026-08-10 approved (human maintainer via chat, recorded by opencode Opus 4.8): controlling spec 20260810-1447-01 human-approved; Set cleared to execute. Status reviewed -> approved; OQ-01 resolved. Not yet executed.
- 2026-08-11 executed (Antigravity CLI): implemented companion identity, preflight validation, storage materialization, durability classification, attachment lifecycle, commit boundaries, and falsifiable tests (Order 05). Execute commit 249796a (storage.py +452, cli.py +243, test_storage.py +358, 7 order05 fixtures). Wrapper reported ERROR: timeout waiting for response; work + plan bookkeeping completed and committed.
- 2026-08-11 orchestrator verification + fix + terminal transition (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): Independent full-suite verification of the execute commit was RED on ONE test: tests.test_cli.SubcommandDescriptionTests.test_every_subparser_has_fuller_description failed because the 4 new storage subcommands (detach, move, reattach, preflight) were added without entries in the central _DESCRIPTIONS map, violating the clianx-01 E-06 contract (every subparser needs a description strictly longer than its help). The companion/durability logic itself was correct. Orchestrator fix-forward: added the 4 _DESCRIPTIONS entries (commit 6dffe13, cli.py only). Independent re-verification: full suite Ran 851 OK (skipped=2) exit 0 (baseline 844 + 7 Order-05 E-tests). Read the Order-05 tests: test_e04 walks the durability state machine UNVERSIONED -> LOCAL_GIT -> UNACKNOWLEDGED_REMOTE -> ACKNOWLEDGED_DURABLE (only after explicit ack + reachable) and asserts revocation downgrades back and clears the ack (truthful durability, no false-durable claims); test_e05 asserts detach preserves companion content (companion_deleted False); test_e06 asserts separate target/companion git owners. Mutation-probe: forcing remote_acknowledged=True unconditionally in get_storage_status makes test_e04 fail RED; restored -> GREEN. Pre-transition ipd lint conforming. Status approved -> executed; Approval line removed; moved pending/ -> executed/.


## Goal

Allow a user to choose an existing companion directory/repository or initialize a local one, attach it to exactly one project identity, and store selected durable root classes there. AW must report observable Git and backup facts, require explicit remote/privacy acknowledgement, and never create, select, push, or delete a remote without authorization.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Define and validate companion identity

- [x] E-01 Implement a portable companion identity document and, without duplicating Order 02 path ownership, a machine-local attachment record binding project ID, target identity hints, schema version, selected root classes, and companion Git common-dir without exposing machine-local paths in tracked content.
  - Depends on: none
  - Expected outcome: A companion can move and reattach safely, cannot silently attach to a different project, and does not trust origin URL alone as identity.
  - Execution state: performed

- [x] E-02 Add preflight validation for existing/non-existing directories, nested/overlapping Git repositories, symlinks, worktrees, case aliases, conflicting identities, dirty state, inaccessible paths, and public-target leakage.
  - Depends on: E-01
  - Expected outcome: Unsafe or ambiguous attachment stops before writes and reports recovery choices without modifying either repository.
  - Execution state: performed

### Task group 2: Materialize and report durable storage

- [x] E-03 Materialize the selected companion `.aw/config`, `.aw/state/durable`, and `.aw/records` classes plus managed ignore rules for local config and runtime data; keep runtime outside tracked companion history unless custom policy explicitly chooses an untracked companion path.
  - Depends on: E-01
  - Expected outcome: The public-plus-private-companion preset has one private durable Git boundary and no candid target records; exact permitted commit destinations are available to producers and migration.
  - Execution state: performed

- [x] E-04 Consume Order 02's Section 10 durability enum and legacy alias, then implement explicit local Git initialization, existing Git inspection, remote enumeration, reachability/status reporting, and acknowledgement/revocation without inferring remote privacy, creating remotes, authenticating, fetching, committing, or pushing automatically.
  - Depends on: E-01
  - Expected outcome: Durability states distinguish unversioned, local Git, observed remote without acknowledgement, acknowledged durable arrangement, unreachable/unknown, and repository-managed cases honestly.
  - Execution state: performed

### Task group 3: Operate the attachment safely

- [x] E-05 Add dry-run-first attach, detach, move, reattach, and `aw storage status`/preflight warning flows with exact target/companion deltas, confirmation boundaries, recovery notes, and safeguards against deleting companion content or remotes.
  - Depends on: E-01
  - Expected outcome: Path changes update local bindings atomically; identity remains stable; detach preserves durable content; uninstall never deletes an external Git repository.
  - Execution state: performed

- [x] E-06 Enforce repository-specific staging and commit instructions so target and companion changes are never combined, and expose clean machine output for migration and postcheck.
  - Depends on: E-01
  - Expected outcome: AW identifies each Git owner, stages only within that owner when authorized, never commits or pushes across boundaries, and reports both worktrees independently.
  - Execution state: performed

- [x] E-07 Add existing-private-repo, new-local-repo, no-Git, multiple-remotes, unacknowledged remote, acknowledged remote, move/reattach, worktree, nested-repo, identity conflict, public leak, dirty state, and uninstall tests.
  - Depends on: E-01
  - Expected outcome: Every attachment and durability state has exact filesystem, identity, Git, output, and no-side-effect assertions.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Set dependencies: Orders 01, 02, and the relevant Order 03 wizard handoff must be verified.
- Privacy is never inferred from a remote URL or provider name.
- Credentials and secrets must never be stored in AW policy, identity, state, history, or test fixtures.
- External repositories are never deleted by uninstall or cleanup.
- Spec traceability: E-01/E-02 implement Section 10 identity; E-03/E-04 implement Sections 5.2 and 10; E-05 through E-07 implement Sections 10 and 13. Coordinate the shared durability schema with Order 02 before either Order commits.

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
| E-01 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e01` | `tests/fixtures/awphysical/order05/e01-*`, including same-origin/wrong-project, moved-path/same-common-dir, and copied-identity canaries | A companion moves and reattaches only when stable project identity and Git common-dir evidence agree; origin URL alone and copied identity material never establish identity. | either spoof attaches, moved-path/same-common-dir cannot reattach, a conflicting project ID is overwritten, or either repository changes on refusal |
| E-02 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e02` | `tests/fixtures/awphysical/order05/e02-*` | Unsafe or ambiguous attachment stops before writes and reports recovery choices without modifying either repository. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e03` | `tests/fixtures/awphysical/order05/e03-*`, including candid-record, absolute-path, staged-target, and wrong-owner canaries | The public-plus-private-companion preset has one private durable Git boundary; exact producer and migration destinations are available; target worktree, index, and public-safe output contain none of the planted private canaries. | any canary reaches the target worktree/index/output, a producer selects the wrong Git owner, or private and target commit instructions are combined |
| E-04 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e04` | one named fixture for each current durability state plus `remote-added-unacknowledged`, `acknowledgement-revoked`, `acknowledged-unreachable`, and `probe-inconclusive` | Each fixture yields exactly its expected state: unversioned, local Git, unacknowledged remote, acknowledged durable, repository-managed, unreachable, or unknown; revoking acknowledgement immediately downgrades the state and persisted evidence. | any state fixture aliases another, a remote alone becomes acknowledged durable, revoke leaves durable status/evidence behind, unreachable becomes durable, or inconclusive inspection claims privacy/durability |
| E-05 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e05` | `tests/fixtures/awphysical/order05/e05-*` | Path changes update local bindings atomically; identity remains stable; detach preserves durable content; uninstall never deletes an external Git repository. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e06` | `tests/fixtures/awphysical/order05/e06-*` | AW identifies each Git owner, stages only within that owner when authorized, never commits or pushes across boundaries, and reports both worktrees independently. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e07` | closed matrix of every attachment and durability state plus one planted identity, leak, or downgrade violation per state transition | Every matrix row asserts exact filesystem, identity, Git owner/index, machine output, durability transition, and no-side-effect result; each planted violation is rejected by the rule it targets. | a matrix row or planted violation is absent, a negative fixture passes, the wrong rule fires, a delta differs, or a transition retains stale durability evidence |

## Spec / documentation sync

- Verify implementation against the controlling specification's companion bundle, identity, durability, privacy, Git-boundary, detach/reattach, and uninstall requirements. Stop and return the specification to review on conflict.
- Document only observable privacy/durability claims and explicit user responsibilities.
- End-user migration instructions remain Order 12.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-10 - the controlling spec `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` was human-approved (Status: approved). The Set is cleared to execute via ipd-lifecycle in dependency order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Run Evidence matrix row E-01 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e01` -> Ran 1 test in 0.034s OK.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Run Evidence matrix row E-02 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e02` -> Ran 1 test in 0.032s OK.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Run Evidence matrix row E-03 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e03` -> Ran 1 test in 0.029s OK.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Run Evidence matrix row E-04 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e04` -> Ran 1 test in 0.219s OK.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Run Evidence matrix row E-05 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e05` -> Ran 1 test in 0.072s OK.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: Run Evidence matrix row E-06 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e06` -> Ran 1 test in 0.047s OK.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: Run Evidence matrix row E-07 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_storage.CompanionAttachmentTests.test_e07` -> Ran 1 test in 0.133s OK.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Companion identity, durable bundle materialization, Git observation, attachment lifecycle, and commit boundaries are one external-storage trust boundary.

Execution requires verified Orders 01/02 and the Order 03 handoff, a GO `/plan-review`, and human approval. Scope fence: companion identity/registry/storage/Git status and their CLI surfaces/tests/docs only. Never create or modify a remote, authenticate, commit, push, delete companion content, or migrate legacy data in this Order. Paste actual outputs, path-scope commits, never broad-stage, and never push. Stop on identity, privacy, durability, or Git-boundary uncertainty. Complete evidence and lint before moving the plan to `executed/`.
