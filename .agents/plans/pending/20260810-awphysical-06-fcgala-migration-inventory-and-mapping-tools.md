# IPD: Migration inventory and mapping tools

- Date: 2026-08-10
- Kind: child
- Concern: Inventory every legacy AW-related item and produce a complete, deterministic, non-mutating migration map before any repository is changed.
- Scope: Legacy discovery/classification, content-hash inventory, Git/ignore/symlink metadata, destination mapping, collision and risk analysis, JSON schemas, CLI preview, support-script integration, and focused tests.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 6
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: fcgala

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to make migration planning exhaustive, read-only, and independently comparable.

## Goal

Before moving anything, produce a stable manifest of every legacy system, config, state, record, adapter, backup, and unknown item, including its bytes, metadata, Git status, ignore status, symlink target, owner classification, and proposed destination. Refuse migration when any item is unclassified, ambiguous, unsafe, or colliding.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Discover and classify all legacy material

- [ ] E-01 Define a versioned inventory/migration-map JSON schema and a closed legacy-source catalog covering `.agents/workflows`, `.agents/agent-workflows`, `.agents/plans`, `.agents/prompts`, `.agents/docs`, `.agents/comms`, `workflow-artifacts`, installer backups/manifests, managed blocks, host shims, prior partial `.aw` trees, and externally resolved legacy roots.
  - Depends on: none
  - Expected outcome: Every discovered item receives source root, relative path, kind, ownership, lifecycle class, expected destination class, and disposition; unknowns are blocking, not dropped.
  - Execution state: pending

- [ ] E-02 Implement a read-only inventory engine, using or promoting `tools/awphysical/aw_layout_inventory.py`, that records regular files, directories, symlinks, sizes, modes, timestamps, SHA-256, Git tracked/untracked/ignored/conflict status, containing Git common-dir, and sanitized path identifiers.
  - Depends on: E-01
  - Expected outcome: Repeated inventory on unchanged input is content-stable apart from explicitly isolated run metadata; it never follows unsafe symlinks or reads outside declared roots.
  - Execution state: pending

- [ ] E-03 Add bounded content-aware classification for overlapping legacy categories and human-authored/foreign files, preserving unknown extensions and nested files without assuming filename patterns imply ownership.
  - Depends on: E-01
  - Expected outcome: Managed manifests/hashes take precedence; modified/foreign files are flagged for human mapping; record classes preserve relative identities and lifecycle directories.
  - Execution state: pending

### Task group 2: Map and preflight destinations

- [ ] E-04 Generate an exact source-to-destination map from the confirmed Order 02 policy, including target/companion/home Git boundary, copy method, track/ignore expectation, collision policy, compatibility retention, and rollback source for every item.
  - Depends on: E-01
  - Expected outcome: No destination is derived from hard-coded `.agents` paths; one source item cannot silently overwrite or merge with another; identical-content deduplication is explicit and reversible.
  - Execution state: pending

- [ ] E-05 Detect and report path traversal, symlink escape, destination nesting, case/unicode collision, existing-file conflict, insufficient space, permissions, unsupported file type, Git conflict/dirty index, worktree ambiguity, companion mismatch, inaccessible external root, partial prior migration, and concurrent-writer risk.
  - Depends on: E-01
  - Expected outcome: Blocking risks produce nonzero machine output before mutation; warnings require explicit acknowledgement in the later transaction plan.
  - Execution state: pending

### Task group 3: Expose and verify the plan

- [ ] E-06 Add `aw migrate-layout inventory/plan` human, JSON, and agent surfaces with `--output`, stable IDs, summary counts/bytes by class and Git owner, and no-write proofs; never print candid file contents.
  - Depends on: E-01
  - Expected outcome: A human can review every move and Git consequence; Order 07 can consume the exact saved map without recomputing against changed inputs.
  - Execution state: pending

- [ ] E-07 Add fixtures for clean legacy, modified managed files, unknown files, ignored records, symlinks, worktrees, multiple Git roots, public/companion, partial `.aw`, collisions, permission/space failures, and agent-workflows source checkout; test inventory completeness and determinism.
  - Depends on: E-01
  - Expected outcome: Fixture expected-item set equals inventory-item set and every unsupported/unknown case blocks rather than disappearing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 01 and 02 must be verified first.
- This Order is strictly read-only with respect to target, companion, AW_HOME, Git index, and policy.
- Content hashes and metadata support migration evidence but are not a substitute for backups.
- Path output must use sanitized logical labels in public-safe mode; raw machine paths belong only in explicitly local evidence files.

## Findings

- Current migration planning lists a small fixed set of directories and does not inventory every file by content hash and Git disposition.
- Existing legacy artifacts span tracked, untracked, ignored, root-level, host-specific, external, and backup locations.
- The agent-workflows repository mixes canonical workflows and its own project records within `.agents`, making ownership classification essential.
- A migration cannot honestly claim completeness without an explicit source-item set and disposition for every member.

## Proposed changes (ordered, validatable)

1. Freeze versioned inventory and migration-map schemas.
2. Implement exhaustive read-only filesystem/Git inventory.
3. Classify ownership using manifests plus conservative fallbacks.
4. Map every item through confirmed policy and Git boundaries.
5. Detect all blocking collisions and environmental risks.
6. Expose stable preview outputs and saveable evidence.
7. Test completeness against adversarial fixtures and source checkout.

## Deferred / out of scope (with reason)

- Copying, switching, rollback, resume, cleanup, staging, and commit are Order 07.
- Producer cutover is Order 08.
- Post-migration comparison is Order 10, though it consumes this schema.

## Scope check

- Over-scope: Inventory and planning only; absolutely no writes to project roots, Git indexes, policy, or registry.
- Under-scope: All known legacy homes, unknown items, hashes, metadata, Git/ignore, symlinks, worktrees, external roots, classification, exact mapping, collision/risk analysis, stable output, and source-checkout fixtures are included.

## Required tests / validation

- Unit tests for inventory/map schemas, hashing, Git classification, ignore handling, symlink safety, collision detection, and stable serialization.
- Fixture assertion: expected source item IDs equal actual inventory item IDs for every scenario.
- Before/after filesystem metadata and `git status` snapshots proving inventory/plan commands make no changes.
- `python3 tools/awphysical/aw_layout_inventory.py --help` and fixture runs for the supplied reference tool.
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`

## Spec / documentation sync

- Update migration inventory, preflight, classification, evidence, and no-write preview sections of the controlling spec.
- Document the JSON schema and sanitization boundary for downstream Orders.
- Keep support scripts under `tools/awphysical/` until promoted or replaced; record their disposition explicitly.

## Open questions

No open questions. Unknown, ambiguous, unsafe, or unaccounted items block migration and require an explicit human disposition.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Schema fixtures and catalog tests prove every named legacy home and prior partial-layout form has a closed classification path, while a planted unknown item appears as blocking and remains present in the saved manifest.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Repeated inventory on unchanged input is content-stable apart from explicitly isolated run metadata; it never follows unsafe symlinks or reads outside declared roots. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Managed manifests/hashes take precedence; modified/foreign files are flagged for human mapping; record classes preserve relative identities and lifecycle directories. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: No destination is derived from hard-coded `.agents` paths; one source item cannot silently overwrite or merge with another; identical-content deduplication is explicit and reversible. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Blocking risks produce nonzero machine output before mutation; warnings require explicit acknowledgement in the later transaction plan. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: A human can review every move and Git consequence; Order 07 can consume the exact saved map without recomputing against changed inputs. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Fixture expected-item set equals inventory-item set and every unsupported/unknown case blocks rather than disappearing. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Inventory, classification, destination mapping, collision analysis, and preview output form one immutable input contract for transactional migration.

Execution requires verified Orders 01/02, a GO `/plan-review`, and human approval. Scope fence: read-only inventory/map schemas, discovery/classification/preflight, preview CLI, support-tool promotion, and focused tests/docs. Do not copy, move, delete, stage, commit, switch policy, or write into target/companion/AW_HOME. Paste actual outputs, path-scope commits, never broad-stage, and never push. Stop if completeness cannot be proven. Complete evidence and lint before moving this plan to `executed/`.
