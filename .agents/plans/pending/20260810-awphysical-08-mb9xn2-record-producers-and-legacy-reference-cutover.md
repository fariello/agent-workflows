# IPD: Record producers and legacy reference cutover

- Date: 2026-08-10
- Kind: child
- Concern: Route every AW record/state producer and consumer through resolved physical roots so no workflow recreates or trusts the legacy hierarchy after migration.
- Scope: Record-class router, producer and reader integrations, plans/specs/research/prompts/comms/runs/actions/history/index/attention surfaces, compatibility readers, forbidden-write guard, generated workflow text, and focused tests.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 8
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: mb9xn2

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to complete the writer cutover and prevent post-migration legacy-tree regeneration.

## Goal

Make the Order 02 context resolver and a single record-class router authoritative for all AW-created records and durable state. Preserve bounded read compatibility during migration, but permit exactly one write destination and fail closed when context or migration authority is invalid.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Complete the routing API

- [ ] E-01 Extend the canonical router with closed record and durable-state classes, safe path construction, lifecycle-aware destinations, permitted Git owner, tracking policy, migration authority, and public-safe logical path rendering.
  - Depends on: none
  - Expected outcome: Producers cannot pass arbitrary relative paths, escape roots, mix records with state, or stage against the wrong repository; unsupported classes fail explicitly.
  - Execution state: pending

- [ ] E-02 Add a centralized write guard that rejects legacy destinations, unresolved/inaccessible roots, active pre-switch migrations, stale context, unsafe symlinks, cross-Git staging, and writes into installed system or runtime from record producers.
  - Depends on: E-01
  - Expected outcome: A literal or indirect legacy write fails before file creation; post-switch compatibility readers cannot become writers.
  - Execution state: pending

### Task group 2: Cut over all producers and consumers

- [ ] E-03 Migrate plans/IPDs, specifications, research, prompts, assessments, incidents, communications, workflow run evidence, and generated indexes to router-owned paths, preserving lifecycle identity, set/index behavior, and record Git destinations.
  - Depends on: E-01
  - Expected outcome: Every producing CLI/workflow returns the actual resolved destination and commits/stages only where policy permits; repository and external backends behave equivalently apart from Git owner.
  - Execution state: pending

- [ ] E-04 Migrate actions, install snapshots/history, routing receipts, migration durable receipts, and other operational writers into `state/durable/`; route locks, transactions, backups, caches, and temporary output into `state/runtime/` with enforced ignore/no-stage rules.
  - Depends on: E-01
  - Expected outcome: Durable state remains inspectable and optionally trackable; runtime data never enters a Git index or records tree.
  - Execution state: pending

- [ ] E-05 Update read-side indexes, `aw attention`, `/whatnext`, workflow discovery, status, history, archive, ref checks, and other consumers to use resolver/router discovery and non-repo-relative logical item paths safely.
  - Depends on: E-01
  - Expected outcome: External records/state work without fake repo-relative paths; D125 remains the one attention projection; failure is explicit and public-safe.
  - Execution state: pending

### Task group 3: Bound compatibility and prove no legacy writes

- [ ] E-06 Implement a read-only compatibility adapter for retained legacy data, enabled only by migration state and time/version bound, with duplicate-authority detection and explicit deprecation output.
  - Depends on: E-01
  - Expected outcome: Old content remains readable during retention, but new writes cannot target it and ambiguous new/old duplicates invalidate the view.
  - Execution state: pending

- [ ] E-07 Update canonical workflow bodies/templates and generated derivatives to request paths through `aw context`/router surfaces instead of hard-coded `.agents` or `workflow-artifacts`; add a semantic producer-write audit rather than an impossible blanket text grep.
  - Depends on: E-01
  - Expected outcome: Legitimate historical/docs references remain allowed, while executable producers and instructions cannot write to forbidden paths.
  - Execution state: pending

- [ ] E-08 Add one end-to-end test per producer/consumer class across repository, home, companion, clean-target, migration-retention, inaccessible-root, wrong-Git, and state/records-confusion cases.
  - Depends on: E-01
  - Expected outcome: The producer/consumer inventory equals the test inventory, and filesystem/Git assertions prove one authoritative destination with no legacy recreation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 02, 06, and 07 must be verified before switching writers.
- `aw attention` remains the only cross-tree attention projection and stays read-only.
- Plans/research/spec indexes are owner-generated and must be regenerated through their commands.
- Literal legacy-path references in historical evidence are not defects; executable write surfaces are the guarded set.

## Findings

- Existing workflow bodies and tools contain many `.agents/...` and `workflow-artifacts/...` paths.
- A literal zero-match grep cannot distinguish legitimate history/read compatibility from active producers.
- Current records routing exists but legacy producers and state writers are not comprehensively integrated.
- External action and attention paths already require special non-repo-relative handling that must generalize safely.

## Proposed changes (ordered, validatable)

1. Complete closed router classes and safe path construction.
2. Enforce one write authority and Git owner.
3. Cut over every record producer.
4. Separate durable and runtime state writers.
5. Cut over all readers/indexes/attention consumers.
6. Add bounded read-only legacy compatibility.
7. Regenerate workflow instructions and add semantic forbidden-write audit.
8. Prove every producer/consumer across all placements.

## Deferred / out of scope (with reason)

- Host adapter path generation is Order 09.
- Migration copy/switch mechanics are Order 07.
- Final legacy cleanup is separately gated after Order 10.
- General workflow behavior unrelated to path/routing is out of scope.

## Scope check

- Over-scope: Path resolution, writing, reading, indexing, and instructions only; no unrelated workflow redesign.
- Under-scope: All record classes, durable/runtime state, every producer/consumer, Git owners, attention, compatibility, generated text, forbidden writes, external roots, and failure states are included.

## Required tests / validation

- Existing plans, specs, research, attention, actions, comms, archive, record-routing, and workflow-contract suites.
- New producer/consumer manifest assertion: declared source set equals exercised test set.
- End-to-end filesystem and separate Git-index assertions for every placement preset.
- Semantic forbidden-write audit with planted indirect/literal legacy writers and allowed historical references.
- `python3 -m agent_workflows plans index --check --agent` and corresponding specs/research checks.
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`

## Spec / documentation sync

- Update producing-workflow, state-class, attention, compatibility, and path-rendering sections of the controlling spec.
- Regenerate all owner-managed workflow indexes and host-source templates touched by source path changes.
- Do not hand-edit generated shims; Order 09 owns their final regeneration.

## Open questions

No open questions. Compatibility is read-only and bounded; all new writes use one router-selected authority.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Router unit tests enumerate every closed record/state class, exact root and Git owner for every preset, traversal/symlink failures, and rejection of state-record-system-runtime class confusion.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: A literal or indirect legacy write fails before file creation; post-switch compatibility readers cannot become writers. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Every producing CLI/workflow returns the actual resolved destination and commits/stages only where policy permits; repository and external backends behave equivalently apart from Git owner. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Durable state remains inspectable and optionally trackable; runtime data never enters a Git index or records tree. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: External records/state work without fake repo-relative paths; D125 remains the one attention projection; failure is explicit and public-safe. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Old content remains readable during retention, but new writes cannot target it and ambiguous new/old duplicates invalidate the view. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Legitimate historical/docs references remain allowed, while executable producers and instructions cannot write to forbidden paths. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-08: The producer/consumer inventory equals the test inventory, and filesystem/Git assertions prove one authoritative destination with no legacy recreation. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Router, writers, readers, compatibility, generated instructions, and exhaustive producer tests must cut over together to prevent split authority.

Execution requires verified Orders 02/06/07, a GO `/plan-review`, and human approval. Scope fence: router, listed producers/readers/indexes/attention/state writers, canonical workflow path instructions, semantic audit, and focused tests/docs. Do not change unrelated workflow semantics, host adapters, migration copy engine, exclusion policy, or CLI help outside owned commands. Paste actual outputs, path-scope commits, never broad-stage, never push, and stop if any producer lacks an authoritative class or Git owner. Complete evidence and lint before moving this plan to `executed/`.
