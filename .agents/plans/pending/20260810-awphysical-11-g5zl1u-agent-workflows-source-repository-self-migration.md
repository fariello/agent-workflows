# IPD: Agent-workflows source repository self-migration

- Date: 2026-08-10
- Kind: child
- Concern: Migrate the framework source repository itself into the physical `.aw/` model without overwriting source or losing its extensive project records and history.
- Scope: Source-repository inventory, source-checkout policy, canonical system relocation, repository records/config/state placement choice, migration execution, reference regeneration, independent audit, rollback rehearsal, and path-scoped commits.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 11
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: g5zl1u

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created as the required dogfood migration after generic machinery is independently verified.

## Goal

Use the same supported wizard, resolver, inventory, migration, routing, adapter, and postcheck surfaces that ordinary projects use to adopt the new hierarchy in agent-workflows. Preserve canonical framework source ownership, every durable artifact, Git history, open concurrent work, and rollback evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Prepare and freeze the source repository

- [ ] E-01 Require all prior implementation Orders 04 through 10 to be terminal, ensure the worktree/index and concurrent branches are coordinated, select and persist the human-approved source-repository preset, and establish a no-writer migration window.
  - Depends on: none
  - Expected outcome: No active agent or workflow writes during inventory/cutover; source-checkout role and config/state/records Git destinations are explicit; unrelated concurrent commits are not absorbed.
  - Execution state: pending

- [ ] E-02 Run the production inventory/plan against all source-repository legacy and partial-layout material, including canonical workflows, Python/package sources, plans, specs, research, prompts, comms, run records, backups, adapters, ignored content, open actions, and externally resolved roots; obtain human approval of every disposition.
  - Depends on: E-01
  - Expected outcome: Expected source-item set equals inventoried set, developer-owned product source is distinguished from project records, and no unknown/collision remains.
  - Execution state: pending

### Task group 2: Rehearse and execute

- [ ] E-03 Clone or copy the repository plus required external roots into a disposable rehearsal environment, execute migration, run comparison/postcheck/fresh-agent review, exercise representative producing workflows, and prove rollback plus resume before touching the real checkout.
  - Depends on: E-01
  - Expected outcome: Rehearsal produces actual green evidence for source protection, record preservation, Git boundaries, routing, adapters, package build, rollback, and resumed completion.
  - Execution state: pending

- [ ] E-04 Execute the approved transaction on the real repository without auto-staging, committing, pushing, or deleting retained legacy data; verify hashes after every phase and stop on any difference from rehearsal inputs or expected Git identities.
  - Depends on: E-01
  - Expected outcome: Canonical workflow source adopts the approved `.aw/system` source-checkout location, project durable material reaches approved roots, and only one writer becomes authoritative.
  - Execution state: pending

### Task group 3: Regenerate, audit, and commit safely

- [ ] E-05 Regenerate owner-managed indexes, adapters, manifests, version/resource references, docs links, test fixtures, and package metadata; update only current references while retaining clearly labeled historical evidence.
  - Depends on: E-01
  - Expected outcome: Source checkout builds/tests from the canonical system source; current docs/tools contain no executable legacy writes; historical citations remain intelligible.
  - Execution state: pending

- [ ] E-06 Run deterministic compare/postcheck and the fresh-agent follow-up over the real migration, inspect target/external Git repositories independently, and resolve every HIGH/MEDIUM finding through owning Orders or new corrective IPDs before completion.
  - Depends on: E-01
  - Expected outcome: Completion is independently evidenced; residual low-risk retained/deprecation items have explicit owner and removal trigger.
  - Execution state: pending

- [ ] E-07 Prepare separate path-scoped commits for source repository and any companion repository, review staged and merge-base deltas, commit only after human confirmation, never push, and retain rollback/legacy material through the defined window.
  - Depends on: E-01
  - Expected outcome: Git history separates source relocation, generated derivatives, project-record movement, and external companion changes as policy requires; no unrelated active-agent work is committed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 04 through 10 must be executed and independently verified.
- The repository may be actively edited by multiple agents; a migration window and exact commit/base coordination are mandatory.
- Executed plans and historical records are immutable evidence; path/citation tooling may relocate them without rewriting bodies.
- Source checkout cannot use ordinary installer ownership for developer-edited canonical system source.

## Findings

- The source repository currently uses `.agents/workflows` as canonical system and `.agents/plans/docs/comms/prompts` as project records.
- It contains many tracked historical artifacts plus ignored/local material and generated adapters.
- Generic implementation tests are insufficient to prove the source repository's real corpus and packaging survive.
- Active concurrent work makes in-place migration without a freeze/rebase check unsafe.

## Proposed changes (ordered, validatable)

1. Freeze a coordinated source-repository policy and writer window.
2. Inventory every source/record/state/adapter item and approve dispositions.
3. Rehearse full migration, postcheck, rollback, and resume on a disposable copy.
4. Execute the unchanged approved transaction on real roots.
5. Regenerate all owner-managed derivatives and current references.
6. Run independent deterministic and fresh-agent audits.
7. Prepare separate reviewed commits and retain rollback material.

## Deferred / out of scope (with reason)

- Pushing, merging to main, tagging, publishing, and release are Order 12 or later explicit human actions.
- Unrelated repository exclusions and CLI-help improvements remain concurrent work.
- Legacy cleanup waits for the retention trigger and a separate explicit cleanup run.

## Scope check

- Over-scope: This Order applies already-implemented generic machinery to agent-workflows; it must not redesign the machinery opportunistically.
- Under-scope: Full corpus, external roots, source role, active work coordination, rehearsal, rollback/resume, real execution, derivatives, packaging, producers, adapters, audits, Git separation, and retention are included.

## Required tests / validation

- Production inventory/map, compare, and postcheck tools against rehearsal and real migration.
- `python3 -m unittest discover -s tests -t .` after final regenerated references.
- Package build and archive inspection from source-checkout mode.
- All plan/spec/research indexes and reference checks.
- Sanitizer, generated-file, entry-point/adapter parity, install/update/uninstall, migration rollback/resume, and clean-target gates.
- Separate source and companion Git status/index/merge-base evidence.
- Fresh-agent follow-up verdict with every finding disposition.
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`

## Spec / documentation sync

- Record the self-migration transaction/evidence in a walkthrough under the new records destination through the router.
- Update source-development paths and regeneration instructions through Order 12 documentation ownership.
- Preserve old-path historical citations or add generated redirects/mapping rather than rewriting executed evidence.

## Open questions

No open questions in this plan. The exact private-target versus companion placement remains a human wizard choice recorded before E-01 execution, not an author assumption.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Signed-off context/policy output, clean writer-lock evidence, explicit concurrent-branch/worktree inventory, and terminal status/evidence for Orders 04 through 10 before any source-repository inventory or mutation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Expected source-item set equals inventoried set, developer-owned product source is distinguished from project records, and no unknown/collision remains. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Rehearsal produces actual green evidence for source protection, record preservation, Git boundaries, routing, adapters, package build, rollback, and resumed completion. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Canonical workflow source adopts the approved `.aw/system` source-checkout location, project durable material reaches approved roots, and only one writer becomes authoritative. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Source checkout builds/tests from the canonical system source; current docs/tools contain no executable legacy writes; historical citations remain intelligible. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Completion is independently evidenced; residual low-risk retained/deprecation items have explicit owner and removal trigger. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Git history separates source relocation, generated derivatives, project-record movement, and external companion changes as policy requires; no unrelated active-agent work is committed. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: This is one dogfood migration transaction with mandatory rehearsal, independent audit, and coordinated Git handoff.

Execution requires terminal verified Orders 04 through 10, a GO `/plan-review`, explicit human approval of the chosen preset and migration map, and a confirmed no-writer window. Scope fence: the approved source-repository migration map and its generated derivatives/evidence only. Never absorb concurrent work, auto-stage, auto-commit, push, release, or delete retained material. Rehearsal must pass first. Paste every actual command result, commit only reviewed path sets, and stop on input/Git/hash drift. Complete evidence and lint before moving this plan to `executed/`.
