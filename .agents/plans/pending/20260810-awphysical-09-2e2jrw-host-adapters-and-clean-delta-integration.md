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
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): final cursory re-review after GPT-5.6 1544-01 closeout (0f6f238) - all 13 conforming at review-finalize, residuals closed (Order 01/02/05/06 canary fixtures, Order 04 path-equality-only, Order 07 test-module + per-fault, Order 09 clean_delta planted-write, Order 12 token->test binding), full suite 825 OK. Controlling spec 20260810-1447-01 advanced to reviewed. Set remains NO-GO pending HUMAN approval of the spec (the sole remaining gate); Status unchanged (reviewed).

## Goal

Generate only the minimum files each enabled host requires, with no independent normative workflow logic or records. In clean-target mode, use only evidence-proven user-scope discovery and demonstrate that install, update, workflow use, and uninstall leave no AW-owned target files or baseline local delta.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Define and generate thin adapters

- [ ] E-01 Replace dead hard-coded-zero evidence in `agent_workflows/clean_delta.py`, then define a versioned adapter manifest whose entries name host, required exact path, adapter kind, canonical system command/body identity, generated hash, ownership marker, tracking policy, and uninstall behavior.
  - Depends on: none
  - Expected outcome: Every out-of-`.aw` AW file has a host-evidence justification and manifest owner; adapters contain pointers/invocation metadata only and cannot fork workflow instructions.
  - Execution state: pending

- [ ] E-02 Refactor OpenCode, Claude, Codex/AGENTS, Antigravity/Gemini, Cursor, VS Code, and supported skill/command generators to resolve the Order 04 system provider and Order 02 project context without embedding brittle machine-local absolute paths in tracked files.
  - Depends on: E-01
  - Expected outcome: Tracked adapters use portable target-relative references when system is target-resident; external-system modes use a stable resolver invocation or proven user-scope mechanism.
  - Execution state: pending

- [ ] E-03 Define adapter purity against the actual generator boundary in `engine.py`, including embedded assess/advise prose, then reject copied workflow bodies, records, mutable state, unowned prose, stale hashes, unsafe commands, or references to legacy canonical roots.
  - Depends on: E-01
  - Expected outcome: Generated adapter set equals manifest set, and every canonical instruction remains single-sourced under system.
  - Execution state: pending

### Task group 2: Prove clean-target behavior

- [ ] E-04 Implement clean-target install/update/use discovery for each enabled host only where user-scope support is proven; otherwise fail with an honest unsupported-host explanation or require an explicit ignored fallback that is no longer called clean-target.
  - Depends on: E-01
  - Expected outcome: No fabricated universal mechanism; support claims cite executable host gates; unavailable integrations do not silently write target adapters.
  - Execution state: pending

- [ ] E-05 Define zero delta from the target merge-base tree and Git index, not a momentary `git status`, then add target baseline snapshots before and after install, update, representative workflow resolution, status, and uninstall, including tracked, untracked, ignored, index, managed-block, and filesystem metadata checks.
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
- Spec traceability: E-01 through E-04 implement Sections 4.1, 5, and 7; E-05/E-06 implement Sections 9 and 11.3; E-07 implements Section 13.

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

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e01` | `tests/fixtures/awphysical/order09/e01-*`, including `planted-aw-owned-target-write` | Every out-of-`.aw` AW file has a host-evidence justification and manifest owner; adapters contain pointers/invocation metadata only and cannot fork workflow instructions; `install_clean_delta` derives its write count from observed before/after evidence and rejects the planted target write. | the planted write is reported as `target_writes: 0`, the install reports success despite that write, evidence remains a hard-coded literal, or a manifest ownership assertion fails |
| E-02 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e02` | `tests/fixtures/awphysical/order09/e02-*` | Tracked adapters use portable target-relative references when system is target-resident; external-system modes use a stable resolver invocation or proven user-scope mechanism. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e03` | `tests/fixtures/awphysical/order09/e03-*` | Generated adapter set equals manifest set, and every canonical instruction remains single-sourced under system. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e04` | `tests/fixtures/awphysical/order09/e04-*` | No fabricated universal mechanism; support claims cite executable host gates; unavailable integrations do not silently write target adapters. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e05` | `tests/fixtures/awphysical/order09/e05-*`, including tracked, untracked, ignored, staged, and `planted-aw-owned-target-write` canaries | Clean-target mode proves zero AW-owned target delta from merge-base, index, and filesystem evidence; target-resident modes show exactly the adapter/system delta previewed by policy. | any planted target write or index delta is missed, a nonzero observed delta is reported as zero, or target-resident output differs from the previewed policy delta |
| E-06 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e06` | `tests/fixtures/awphysical/order09/e06-*` | Migration creates one current adapter per enabled host, preserves sibling/foreign content byte-for-byte, and reports ambiguous or modified owned adapters for review. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e07` | `tests/fixtures/awphysical/order09/e07-*` | Repair touches only verified owned adapters; uninstall removes only manifest-owned content; disabling a host prunes its adapter without touching other host/user files. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-08 | `python3 -m unittest tests.test_clean_delta.PhysicalAdapterAndDeltaTests.test_e08` | `tests/fixtures/awphysical/order09/e08-*` | Every advertised host/mode has an executable proof and no unproven capability appears in help or docs. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Verify implementation against the controlling specification's host-adapter, clean-target, source-resolution, conversion, drift, and uninstall requirements. Stop and return the specification to review on conflict.
- Regenerate adapters through owner tools; do not hand-edit generated files.
- Record unsupported combinations honestly for Order 12 documentation.

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
- [ ] V-08 validates E-08
  - Required evidence: Run Evidence matrix row E-08 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Adapter manifest, generation, clean-target discovery, conversion, drift, and uninstall are one host integration boundary.

Execution requires verified Orders 02/04/07/08, a GO `/plan-review`, and human approval. Scope fence: adapter model/generators, host discovery, managed blocks/shims, clean-target integration, drift/uninstall, and focused tests/docs. Do not duplicate workflow logic, alter workflow semantics, claim unsupported hosts, or edit generated adapters by hand. Coordinate shared CLI files with concurrent help work. Paste actual outputs, path-scope commits, never broad-stage, and never push. Complete evidence and lint before moving this plan to `executed/`.
