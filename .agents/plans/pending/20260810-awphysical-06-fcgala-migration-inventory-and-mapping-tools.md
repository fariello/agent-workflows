# IPD: Migration inventory and mapping tools

- Date: 2026-08-10
- Kind: child
- Concern: Inventory every legacy AW-related item and produce a complete, deterministic, non-mutating migration map before any repository is changed.
- Scope: Legacy discovery/classification, content-hash inventory, Git/ignore/symlink metadata, destination mapping, collision and risk analysis, JSON schemas, CLI preview, support-script integration, and focused tests.
- Status: approved
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 6
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: fcgala
- Approval: 2026-08-10 human maintainer (chat, after approving the controlling spec 20260810-1447-01) - approved to execute the awphysical Set; recorded by opencode Opus 4.8.

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to make migration planning exhaustive, read-only, and independently comparable.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): final cursory re-review after GPT-5.6 1544-01 closeout (0f6f238) - all 13 conforming at review-finalize, residuals closed (Order 01/02/05/06 canary fixtures, Order 04 path-equality-only, Order 07 test-module + per-fault, Order 09 clean_delta planted-write, Order 12 token->test binding), full suite 825 OK. Controlling spec 20260810-1447-01 advanced to reviewed. Set remains NO-GO pending HUMAN approval of the spec (the sole remaining gate); Status unchanged (reviewed).
- 2026-08-10 approved (human maintainer via chat, recorded by opencode Opus 4.8): controlling spec 20260810-1447-01 human-approved; Set cleared to execute. Status reviewed -> approved; OQ-01 resolved. Not yet executed.

## Goal

Before moving anything, produce a stable manifest of every legacy system, config, state, record, adapter, backup, and unknown item, including its bytes, metadata, Git status, ignore status, symlink target, owner classification, and proposed destination. Refuse migration when any item is unclassified, ambiguous, unsafe, or colliding.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Discover and classify all legacy material

- [ ] E-01 Define a versioned inventory/migration-map JSON schema and a closed legacy-source catalog covering `.agents/workflows`, `.agents/agent-workflows`, `.agents/plans`, `.agents/prompts`, `.agents/docs`, `.agents/comms`, `workflow-artifacts`, installer backups/manifests, managed blocks, host shims, prior partial `.aw` trees, and external legacy roots supplied explicitly with repeatable operator `--root` declarations.
  - Depends on: none
  - Expected outcome: Every discovered item receives source root, relative path, kind, ownership, lifecycle class, expected destination class, and disposition; unknowns are blocking, not dropped.
  - Execution state: pending

- [ ] E-02 Implement a read-only inventory engine, using or promoting `tools/awphysical/aw_layout_inventory.py`, that records regular files, directories, symlinks, sizes, modes, SHA-256, containing Git common-dir, and sanitized path identifiers. Isolate capture timestamps as run metadata, and use the closed Git classification `tracked`, `untracked`, `ignored`, `not-listed`, `unmerged`, `external`, or `mixed:<sorted-members>`.
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
- Spec traceability: E-01 through E-03 implement Section 11.1; E-04/E-05 implement Sections 7 and 11.1; E-06/E-07 implement Sections 11.1 and 13.

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
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e01` | `tests/fixtures/awphysical/order06/e01-*` | Every discovered item, including every repeatable `--root` external tree, receives source root, relative path, kind, ownership, lifecycle class, expected destination class, and disposition; unknowns are blocking, not dropped. | omitting a declared external-root canary or adding an unknown item does not produce a nonzero result |
| E-02 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e02` | `tests/fixtures/awphysical/order06/e02-*` | Repeated inventory is stable after excluding normalized run timestamp metadata; symlink escapes are not followed; `tracked`, `untracked`, `ignored`, `not-listed`, `unmerged`, and deterministic `mixed:<sorted-members>` fixtures receive exact classifications. | any classification is absent/wrong, ordering changes bytes, a symlink escape is read, or command is nonzero on the clean fixture |
| E-03 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e03` | `tests/fixtures/awphysical/order06/e03-*` | Managed manifests/hashes take precedence; modified/foreign files are flagged for human mapping; record classes preserve relative identities and lifecycle directories. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e04` | `tests/fixtures/awphysical/order06/e04-*` | No destination is derived from hard-coded `.agents` paths; one source item cannot silently overwrite or merge with another; identical-content deduplication is explicit and reversible. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e05` | one fixture per blocking rule: unknown owner, inaccessible root, destination collision, unsafe symlink, unmerged Git state, missing disposition, and stale policy digest | Each planted risk produces nonzero machine output naming its exact rule and item ID before any filesystem or Git mutation; warning-only fixtures remain distinct and require a recorded acknowledgement. | any planted blocker returns zero, reports only a generic failure, mutates a source/destination/index, or a warning is accepted without recorded acknowledgement |
| E-06 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e06` | `tests/fixtures/awphysical/order06/e06-*` | A human can review every move and Git consequence; Order 07 can consume the exact saved map without recomputing against changed inputs. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e07` | closed expected-item manifests plus planted missing, extra, duplicate-disposition, unknown, ignored, untracked, empty-directory, and external-root canaries | Expected item IDs equal actual inventory IDs; every ID has exactly one disposition; each unsupported/unknown or set mismatch blocks and names the differing IDs without mutation. | any canary disappears, an extra/missing/duplicate item is accepted, output omits the set difference, or inventory/plan changes filesystem or Git state |

## Spec / documentation sync

- Verify implementation against the controlling specification's migration inventory, preflight, classification, evidence, and no-write preview requirements. Stop and return the specification to review on conflict.
- Document the JSON schema and sanitization boundary for downstream Orders.
- Treat tracked `tools/awphysical/` files from commit `767d98c` as review prototypes. This Order owns inventory/map promotion; Order 10 owns compare/postcheck promotion. Preserve prototypes until parity tests prove replacement.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-10 - the controlling spec `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` was human-approved (Status: approved). The Set is cleared to execute via ipd-lifecycle in dependency order.

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
- Cohesion rationale: Inventory, classification, destination mapping, collision analysis, and preview output form one immutable input contract for transactional migration.

Execution requires verified Orders 01/02, a GO `/plan-review`, and human approval. Scope fence: read-only inventory/map schemas, discovery/classification/preflight, preview CLI, support-tool promotion, and focused tests/docs. Do not copy, move, delete, stage, commit, switch policy, or write into target/companion/AW_HOME. Paste actual outputs, path-scope commits, never broad-stage, and never push. Stop if completeness cannot be proven. Complete evidence and lint before moving this plan to `executed/`.
