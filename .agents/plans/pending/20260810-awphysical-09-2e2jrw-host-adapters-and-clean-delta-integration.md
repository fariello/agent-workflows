# IPD: Host adapters and clean-delta integration

- Date: 2026-08-10
- Kind: child
- Concern: Keep canonical AW logic under the resolved system root while satisfying host discovery requirements with thin generated adapters and proving a truly clean target mode.
- Scope: Adapter model/generation, AGENTS/native managed blocks, host-specific shims/skills/commands, dynamic root discovery, clean-target user-scope mechanisms, drift/uninstall, legacy adapter conversion, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 9
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: 2e2jrw

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to reduce `.agents` and other host paths to compatibility adapters rather than canonical storage.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.

## Goal

Generate only the minimum files each enabled host requires, with no independent normative workflow logic or records. In clean-target mode, use only evidence-proven user-scope discovery and demonstrate that install, update, workflow use, and uninstall leave no AW-owned target files or baseline local delta.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Define and generate thin adapters

- [ ] E-01 Define a versioned adapter manifest whose entries name host, required exact path, adapter kind, canonical system command/body identity, generated hash, ownership marker, tracking policy, and uninstall behavior.
  - Depends on: none
  - Expected outcome: Every out-of-`.aw` AW file has a host-evidence justification and manifest owner; adapters contain pointers/invocation metadata only and cannot fork workflow instructions.
  - Execution state: pending

- [ ] E-02 Refactor OpenCode, Claude, Codex/AGENTS, Antigravity/Gemini, Cursor, VS Code, and supported skill/command generators to resolve the Order 04 system provider and Order 02 project context without embedding brittle machine-local absolute paths in tracked files.
  - Depends on: E-01
  - Expected outcome: Tracked adapters use portable target-relative references when system is target-resident; external-system modes use a stable resolver invocation or proven user-scope mechanism.
  - Execution state: pending

- [ ] E-03 Add adapter purity validation that rejects copied workflow bodies, records, mutable state, unowned prose, stale hashes, unsafe commands, or references to legacy canonical roots.
  - Depends on: E-01
  - Expected outcome: Generated adapter set equals manifest set, and every canonical instruction remains single-sourced under system.
  - Execution state: pending

### Task group 2: Prove clean-target behavior

- [ ] E-04 Implement clean-target install/update/use discovery for each enabled host only where user-scope support is proven; otherwise fail with an honest unsupported-host explanation or require an explicit ignored fallback that is no longer called clean-target.
  - Depends on: E-01
  - Expected outcome: No fabricated universal mechanism; support claims cite executable host gates; unavailable integrations do not silently write target adapters.
  - Execution state: pending

- [ ] E-05 Add target baseline snapshots before and after install, update, representative workflow resolution, status, and uninstall, including tracked, untracked, ignored, index, managed-block, and filesystem metadata checks.
  - Depends on: E-01
  - Expected outcome: Clean-target mode proves zero AW-owned target delta; target-resident modes show exactly the adapter/system delta previewed by policy.
  - Execution state: pending

### Task group 3: Convert, detect drift, and uninstall safely

- [ ] E-06 Convert legacy `.agents/workflows`, `.claude`, `.opencode`, AGENTS/CLAUDE/GEMINI managed blocks, and other adapters through manifest-aware replace-not-append logic that preserves foreign files and human text.
  - Depends on: E-01
  - Expected outcome: Migration creates one current adapter per enabled host, preserves sibling/foreign content byte-for-byte, and reports ambiguous or modified owned adapters for review.
  - Execution state: pending

- [ ] E-07 Integrate adapter drift/status/repair/uninstall with source-checkout protection, selected hosts, clean-target policy, and conservative ownership; add cross-platform and inaccessible-external-system tests.
  - Depends on: E-01
  - Expected outcome: Repair touches only verified owned adapters; uninstall removes only manifest-owned content; disabling a host prunes its adapter without touching other host/user files.
  - Execution state: pending

- [ ] E-08 Add claim-set-equals-evidence-set tests for supported host/mode combinations, plus negative unsupported, stale, copied-logic, foreign-file, malformed-block, clean-target, and source-checkout cases.
  - Depends on: E-01
  - Expected outcome: Every advertised host/mode has an executable proof and no unproven capability appears in help or docs.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 02, 04, 07, and 08 must be verified.
- Host-required exact paths are exceptions, not additional canonical roots.
- Clean-target means no AW-owned tracked, untracked, ignored, or baseline-local target files.
- Existing sectioned managed-block parsing must preserve foreign sibling blocks and user prose.

## Findings

- Current canonical workflow bodies live under `.agents/workflows`, while generated host paths also live outside that tree.
- Some hosts have repository-specific discovery only; clean-target support must not be claimed without a user-scope mechanism.
- Existing adapters and managed blocks require conversion rather than blind deletion/recreation.
- Prior clean-delta code is not integrated into the main installer policy/materializer path.

## Proposed changes (ordered, validatable)

1. Define adapter manifest and purity contract.
2. Generate every host adapter from the resolved canonical system.
3. Reject copied logic and mutable content in adapters.
4. Implement only evidence-proven clean-target integrations.
5. Prove exact target deltas across lifecycle operations.
6. Convert legacy adapters safely.
7. Integrate drift, repair, disable, and uninstall.
8. Match all host claims to executable evidence.

## Deferred / out of scope (with reason)

- Adding unsupported host capabilities without evidence is out of scope.
- Producer routing is Order 08.
- User-facing final documentation is Order 12.
- Remote companion behavior is Order 05.

## Scope check

- Over-scope: Adapter and host discovery behavior only; no workflow logic duplication or unrelated host configuration.
- Under-scope: All supported hosts, exact paths, manifests, portability, external roots, clean-target proof, legacy conversion, foreign preservation, drift, repair, disable, uninstall, source mode, and claims gating are included.

## Required tests / validation

- Existing installer, comms, setup-artifact, host parity, managed-block, uninstall, and clean-delta suites.
- New adapter manifest/purity and claim-evidence equality tests.
- Target baseline before/after snapshots for every supported clean-target host/mode.
- Generated adapter diff proving no canonical workflow body duplication.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`
- Full suite after regenerating owned adapters.

## Spec / documentation sync

- Update host adapter, clean-target, source resolution, conversion, drift, and uninstall sections of the controlling spec.
- Regenerate adapters through owner tools; do not hand-edit generated files.
- Record unsupported combinations honestly for Order 12 documentation.

## Open questions

No open questions. Clean-target support is evidence-gated per host; exact-path adapters remain thin and manifest-owned.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Adapter manifest tests prove every AW-owned exception outside `.aw` has a host requirement, canonical target, generated hash, tracking policy, and uninstall rule, with no unmanifested generated adapter.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Tracked adapters use portable target-relative references when system is target-resident; external-system modes use a stable resolver invocation or proven user-scope mechanism. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Generated adapter set equals manifest set, and every canonical instruction remains single-sourced under system. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: No fabricated universal mechanism; support claims cite executable host gates; unavailable integrations do not silently write target adapters. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Clean-target mode proves zero AW-owned target delta; target-resident modes show exactly the adapter/system delta previewed by policy. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Migration creates one current adapter per enabled host, preserves sibling/foreign content byte-for-byte, and reports ambiguous or modified owned adapters for review. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Repair touches only verified owned adapters; uninstall removes only manifest-owned content; disabling a host prunes its adapter without touching other host/user files. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-08: Every advertised host/mode has an executable proof and no unproven capability appears in help or docs. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Adapter manifest, generation, clean-target discovery, conversion, drift, and uninstall are one host integration boundary.

Execution requires verified Orders 02/04/07/08, a GO `/plan-review`, and human approval. Scope fence: adapter model/generators, host discovery, managed blocks/shims, clean-target integration, drift/uninstall, and focused tests/docs. Do not duplicate workflow logic, alter workflow semantics, claim unsupported hosts, or edit generated adapters by hand. Coordinate shared CLI files with concurrent help work. Paste actual outputs, path-scope commits, never broad-stage, and never push. Complete evidence and lint before moving this plan to `executed/`.
