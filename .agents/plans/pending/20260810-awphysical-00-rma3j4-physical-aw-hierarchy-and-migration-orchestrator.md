# IPD: Physical .aw hierarchy and migration orchestrator

- Date: 2026-08-10
- Kind: orchestrator
- Concern: Replace the partially logical legacy layout with a physically compartmentalized `.aw/` model, complete placement and Git-policy choices, and a loss-resistant migration for agent-workflows and every installed project.
- Scope: Orders 01 through 12 of Set `awphysical`, their shared contract, dependency gates, migration safety, source-repository adoption, independent postcheck, documentation, and release evidence.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 0
- Highest E allocated: 14
- Author: Codex (GPT-5)
- Id: rma3j4

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created after maintainer approval of the refined hierarchy, including durable/runtime state separation and a source-checkout role.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.

## Goal

Deliver one coherent major-version cutover in which canonical AW material is physically separated into `system`, `config`, `state`, and `records`, every durable placement and Git consequence is chosen and previewed, and legacy projects can migrate without losing or silently exposing information. The Set must work both for ordinary target repositories and for the agent-workflows source repository itself.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Freeze the cross-Set contract

- [ ] E-01 Obtain human approval of the amended physical-layout specification and record the exact cross-Set invariants, root vocabulary, preset semantics, compatibility window, and release boundary that every child must implement.
  - Depends on: none
  - Expected outcome: No child begins implementation against an ambiguous logical-only hierarchy; the approved spec explicitly distinguishes portable config from local config and durable state from runtime state.
  - Execution state: pending

### Task group 2: Execute the foundational contract and resolver

- [ ] E-02 Execute Order 01 and independently verify the physical root, ownership, tracking, source-checkout, and Git-boundary contract.
  - Depends on: E-01
  - Expected outcome: One normative mapping governs target, home, companion, clean-target, and source-checkout placements.
  - Execution state: pending

- [ ] E-03 Execute Order 02 and independently verify the versioned policy schema, precedence, provenance, path safety, and pure resolver.
  - Depends on: E-01
  - Expected outcome: `aw context` can explain every resolved path and tracking destination without reading prose or prompting.
  - Execution state: pending

### Task group 3: Execute configuration and installation surfaces

- [ ] E-04 Execute Order 03 and independently verify all wizard presets, custom choices, update review, persistence, accessibility, and noninteractive parity.
  - Depends on: E-01
  - Expected outcome: Users can select all-in-private-target, public-plus-private-companion, clean-target, local-only, or safe custom placement with an exact pre-write preview.
  - Execution state: pending

- [ ] E-05 Execute Order 04 and independently verify canonical `.aw/system/` installation, atomic update, manifest ownership, packaging, and protected source-checkout behavior.
  - Depends on: E-01
  - Expected outcome: Installed system content is isolated from mutable config, state, and records, while the framework source repository remains editable and cannot be overwritten by self-install.
  - Execution state: pending

- [ ] E-06 Execute Order 05 and independently verify companion selection, identity attachment, Git initialization, durability reporting, and privacy-honest remote acknowledgement.
  - Depends on: E-01
  - Expected outcome: A public target can keep candid durable material in an explicitly selected private companion without storing machine paths or private content in the public repository.
  - Execution state: pending

### Task group 4: Execute migration machinery and cutover

- [ ] E-07 Execute Order 06 and independently verify complete legacy inventory, deterministic classification, migration mapping, hash manifests, and collision/preflight reporting.
  - Depends on: E-01
  - Expected outcome: Every legacy file is known before mutation, including tracked, untracked, ignored, symlinked, external, and cross-Git-boundary material.
  - Execution state: pending

- [ ] E-08 Execute Order 07 and independently verify copy-verify-switch-retain migration, resume, rollback, cross-repository commit boundaries, and explicit cleanup.
  - Depends on: E-01
  - Expected outcome: Interruption or failure cannot produce two authoritative writers or a success claim with missing or changed content.
  - Execution state: pending

- [ ] E-09 Execute Order 08 and independently verify every record producer, reader, index, attention source, workflow instruction, and legacy compatibility reader against resolved roots.
  - Depends on: E-01
  - Expected outcome: New writes use exactly one resolved destination and no producing workflow silently recreates a legacy tree.
  - Execution state: pending

- [ ] E-10 Execute Order 09 and independently verify thin host adapters, root pointers, generated shims, source ownership, clean-target discovery, uninstall, and zero-target-delta proof.
  - Depends on: E-01
  - Expected outcome: Host-required exceptions contain no canonical logic or records, and clean-target mode leaves no AW-owned target files.
  - Execution state: pending

### Task group 5: Audit, dogfood, and release

- [ ] E-11 Execute Order 10 and independently verify the deterministic postcheck plus fresh-agent follow-up review against successful, partial, interrupted, and deceptive fixtures.
  - Depends on: E-01
  - Expected outcome: Migration completion depends on independently reproduced evidence, not the migrator's own summary.
  - Execution state: pending

- [ ] E-12 Execute Order 11 and independently migrate the agent-workflows repository, verifying source-checkout protection and preservation of its existing plans, specifications, research, prompts, communications, and history.
  - Depends on: E-01
  - Expected outcome: The source repository dogfoods the same policy and migration machinery without duplicating or overwriting canonical framework source.
  - Execution state: pending

- [ ] E-13 Execute Order 12 and independently verify documentation, compatibility messaging, upgrade/release behavior, and the complete acceptance scenario matrix.
  - Depends on: E-01
  - Expected outcome: User guidance, CLI help, schemas, examples, generated material, tests, and release metadata describe one behavior and every named scenario has executable evidence.
  - Execution state: pending

- [ ] E-14 Perform the whole-Set closeout from a clean checkout, compare the implementation and evidence sets, run the complete regression and package gates, and record any intentionally retained legacy material plus its removal trigger.
  - Depends on: E-01
  - Expected outcome: Claim set equals evidence set; all children are terminal and conforming; no legacy writer remains; rollback and retention evidence exist; no release, tag, push, or cleanup occurs without its separate human gate.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Set dependencies |
|---:|---|---|---|
| 01 | `cwjnj0` | Physical hierarchy, ownership, tracking, and normative policy matrix | approved spec |
| 02 | `sywony` | Versioned policy schema and deterministic context resolver | 01 |
| 03 | `x2dfen` | Interactive presets, advanced placement, persistence, update checkpoint | 01, 02 |
| 04 | `ru5pmd` | Canonical system installation, packaging, atomic updates, source-checkout role | 01, 02 |
| 05 | `1e9ggw` | Companion identity, Git/durability handling, private-storage safeguards | 01, 02, 03 |
| 06 | `fcgala` | Read-only legacy inventory, classification, hash manifest, migration map | 01, 02 |
| 07 | `nhv0qm` | Transactional migration, resume, rollback, retention, cleanup planning | 02, 04, 05, 06 |
| 08 | `mb9xn2` | Producer/reader routing, legacy compatibility, indexes and attention | 02, 06, 07 |
| 09 | `2e2jrw` | Thin host adapters, clean-target integration, uninstall | 02, 04, 07, 08 |
| 10 | `n3fz8b` | Independent deterministic postcheck and skeptical agent follow-up | 06, 07, 08, 09 |
| 11 | `g5zl1u` | agent-workflows source-repository self-migration | 04 through 10 |
| 12 | `pszk6x` | Documentation, compatibility, release, acceptance matrix | 03 through 11 |

Orders may be implemented in parallel only when all listed dependencies are terminal and independently verified. Order 07 is the first mutation-capable migration order; Orders 01 through 06 must not migrate a live repository.

## Completion criteria (the whole Set is done only when)

- The canonical target hierarchy is physically `.aw/system`, `.aw/config`, `.aw/state`, and `.aw/records` wherever those roots are target-resident.
- `config/project.json` and `state/durable/` are separately trackable; `config/local.json` and `state/runtime/` are never tracked.
- All durable material in the private-target preset is tracked except explicitly prohibited local/runtime data.
- Public-plus-private-companion and clean-target presets are end-to-end proven with separate Git repositories.
- The source-checkout role protects canonical agent-workflows source and uses the same resolver contract.
- Pre-migration inventory and post-migration comparison account for every source item by hash and disposition.
- Migration is resumable, rollback-capable, cross-Git aware, and never deletes legacy material during the cutover transaction.
- Every producer writes only through the resolver, every compatibility reader is bounded, and forbidden legacy writes are covered by executable tests.
- The independent postcheck and fresh-agent review both pass after the migrator reports success.
- Full tests, packaging, sanitizer, generated-file, index, parity, install/uninstall, migration, and clean-delta gates pass from a clean checkout.

## Cross-IPD validation

- Maintain one machine-readable root/policy vocabulary imported by resolver, wizard, installer, migration, adapters, storage, and tests.
- Maintain one explicit scenario-to-test map; no child may claim a scenario already covered without naming the executable test.
- Compare source claims, documentation claims, and observed paths for every preset.
- Run migration fixtures through inventory, execution, comparison, postcheck, rollback, resume, and cleanup-preview surfaces.
- Verify target and companion Git indexes independently and prove no command stages or commits across the wrong boundary.
- Verify all support scripts with stdlib `unittest` fixtures and deterministic JSON output.
- Use the fresh-agent follow-up instruction only after deterministic postcheck output exists; the agent must consume evidence rather than reconstruct it from summaries.

## Deferred / out of scope (with reason)

- Secret storage is out of scope. AW policy files must not become a credential vault.
- Automatic remote creation, remote privacy inference, push, tag, release, or destructive cleanup is out of scope without separate explicit human authorization.
- General project task tracking remains outside AW actions and records.
- Repository exclusion-list behavior and CLI help ordering/detail are owned by concurrent work and must not be modified by this Set unless a merge conflict requires coordination.

## Scope check

- Over-scope: The Set changes AW layout, placement policy, migration, routing, adapters, self-adoption, and documentation only; it does not redesign unrelated workflow semantics.
- Under-scope: Physical naming, root internals, Git policy, presets, custom placement, persistence, source checkout, companion durability, inventory, collision handling, rollback/resume, compatibility, all producers/readers, adapters, self-migration, independent audit, documentation, and release evidence are included.

## Required tests / validation

- Each child must run `python3 -m agent_workflows ipd lint --phase pre-transition --agent <child>` before transition.
- The orchestrator must run `python3 -m agent_workflows ipd lint --phase pre-transition --agent <orchestrator>` after every child evidence update.
- The final executor must run the exact focused commands named by each child, then `python3 -m unittest discover -s tests -t .` after the final code change.
- Run `python3 -m agent_workflows plans index --check --agent`, all generated-file and entry-point parity checks, package build/inspection, and `python3 -m agent_workflows check-local-leaks . --agent`.
- Exercise every row in `tools/awphysical/migration-scenarios.json`; fail if the scenario set and evidence set differ.
- Run `tools/awphysical/aw_layout_inventory.py`, `aw_layout_compare.py`, and `aw_layout_postcheck.py` against fixtures and the agent-workflows self-migration; preserve their actual JSON and exit statuses.
- Prove `git status --short`, `git diff --cached --name-only`, and merge-base deltas separately for target, companion, and source repositories.

## Open questions

### OQ-01: The controlling physical-layout spec does not yet exist (BLOCKS the whole Set)

- Blocking: yes
- Status: open
- Owner: GPT-5.6 High (author) + human maintainer (approval)
- Resolution or deferral rationale: /plan-review (2026-08-10, Opus 4.8) confirmed E-01/V-01 require an approved physical-layout spec that does not exist; the only layout spec (20260809-2211-01) is `implemented` and declares the tree LOGICAL. Maintainer decision: author a NEW dated spec that SUPERSEDES 20260809-2211-01 (record supersession + DECISIONS entry); it must be human-approved before any child executes. Handoff prompt: `.agents/prompts/pending/20260810-1417-01-awphysical-superseding-spec-and-set-reconciliation.md`.

### OQ-02: `tools/awphysical/` tracking + clean-checkout reconciliation

- Blocking: yes
- Status: open
- Owner: GPT-5.6 High
- Resolution or deferral rationale: the migration/audit tools + `migration-scenarios.json` the Set depends on are untracked, breaking the clean-checkout replay gate (E-14). GPT-5.6 to decide whether they are committed as tracked prototypes or authored/promoted during a named Order, and encode it (running `aw sanitize` first if committed).

## Plan-review outcome (2026-08-10 /plan-review-long, Opus 4.8 opencode)

Verdict: REVIEWED - OPEN QUESTIONS. Readiness: NO-GO (blocked on the superseding physical-layout spec being authored and human-approved; see OQ-01). All 13 plans lint `conforming` at `--phase author`; the migration design, privacy posture, and independent-postcheck approach are sound. The 13-lane parallel audit found: (BLOCKER) no approved physical spec (every child gates on E-01); (Set-wide, FIXED in review) `aw ipd lint --phase executor` was invalid across all 13 + orchestrator and was corrected to `--phase pre-transition`; (Set-wide, OPEN) `tools/awphysical/` untracked; and numerous per-plan findings (boilerplate V-evidence needing concrete falsifiable per-item evidence, "no open questions" while the spec is unwritten, orchestrator E-item dependencies flattened to E-01 vs the true child DAG, stale/nonexistent test-module and corrective-plan references, phantom producer inventory anchors in Order 08, a fabricated `clean_delta.py` proof in Order 09, `execute_migration` never copying bytes in Order 07, rehearsal-vs-real-repo baseline gap in Order 11, CHANGELOG describing the logical layout in Order 12). The full per-plan findings and required corrections were handed to GPT-5.6 High (the Set's author) in the prompt cited in OQ-01 for resolution alongside the new spec. Maintainer confirmed Order 11 (self-migrate this repo) stays IN scope but hard-gated (dogfood the physical layout; require a real before/after hash+history baseline of the actual repo, not just the rehearsal copy).

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The controlling spec is approved by the human maintainer and contains the complete physical tree, placement/preset matrix, Git-policy invariants, source-checkout exception, migration retention rule, and compatibility/release boundary cited by every child.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: One normative mapping governs target, home, companion, clean-target, and source-checkout placements. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: `aw context` can explain every resolved path and tracking destination without reading prose or prompting. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Users can select all-in-private-target, public-plus-private-companion, clean-target, local-only, or safe custom placement with an exact pre-write preview. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Installed system content is isolated from mutable config, state, and records, while the framework source repository remains editable and cannot be overwritten by self-install. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: A public target can keep candid durable material in an explicitly selected private companion without storing machine paths or private content in the public repository. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Every legacy file is known before mutation, including tracked, untracked, ignored, symlinked, external, and cross-Git-boundary material. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-08: Interruption or failure cannot produce two authoritative writers or a success claim with missing or changed content. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-09: New writes use exactly one resolved destination and no producing workflow silently recreates a legacy tree. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-10: Host-required exceptions contain no canonical logic or records, and clean-target mode leaves no AW-owned target files. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-11: Migration completion depends on independently reproduced evidence, not the migrator's own summary. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-12: The source repository dogfoods the same policy and migration machinery without duplicating or overwriting canonical framework source. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-13: User guidance, CLI help, schemas, examples, generated material, tests, and release metadata describe one behavior and every named scenario has executable evidence. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-14: Claim set equals evidence set; all children are terminal and conforming; no legacy writer remains; rollback and retention evidence exist; no release, tag, push, or cleanup occurs without its separate human gate. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The Set is one major-version cutover, but its independently verifiable contracts, resolver, wizard, installer, companion, migration, routing, adapters, audit, dogfood, and release surfaces are separated into short child IPDs.

Execution is blocked until `/plan-review` gives the orchestrator and every child a GO verdict and the human maintainer approves the controlling spec and Set. Each executor must obey its child scope fence, coordinate overlapping files with concurrent work, paste actual runner output for every claimed pass, commit only its explicitly scoped paths with path-scoped Git commands, never use broad staging, and never push. Any discovered data-loss, privacy, Git-boundary, source-overwrite, or rollback ambiguity is a hard stop. After all children pass independently, update this orchestrator's E/V evidence, run the whole-Set gates, and move it to `executed/`; do not release or delete retained legacy material without the separate gates in Order 12.
