# IPD: Phase 0: threat model, assurance classes, invariant catalog, and observable-evidence definitions

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij section 7.1/8 (Phase 0): before implementing any control you must classify each invariant and define what evidence is observable, or you risk describing local hooks/hashes/files as stronger than they are and building controls with no precise target. There is no catalog today of the toolkit's process invariants, their assurance class, or their observable evidence.
- Scope: Author the Phase-0 foundation as a durable spec/record (under `.aw/records/specs/` or a docs artifact): (1) a threat model (an agent with broad local shell access can use raw tools, edit files, bypass local hooks, fabricate local records; remote acceptance is the authority boundary); (2) three assurance classes - Guidance (cooperative agents follow), Repository-invariant (noncompliant artifacts must fail checks/merge), Authority-invariant (even a locally-privileged agent must not forge/authorize); (3) an invariant catalog enumerating the toolkit's key process rules (path-scoped commits/no `add -A`, no push without authorization, no hand-edited lifecycle status, test evidence bound to the tree, IPD finalize requires validation, backlog release-gate preservation, etc.), each tagged with its assurance class and its observable evidence (what artifact/event proves compliance) or an honest "unverifiable/probabilistic" label. One catalog entry MUST be the authoring-lifecycle invariant "a finished draft IPD is advanced to `to-review`" (assurance class: Guidance; observable evidence: a `draft` plan with no authoring placeholders is deterministically detectable, so it is nudged, not left silently `draft`) - this closes the recurring miss where agents finish drafting but never advance the status, and phase-1 child 02 implements the `check.ipd-draft-ready-to-review` detect-and-nudge rule from it. This child produces NO enforcement code; it is the classification that phases 1-5 target. Deliverable is a reviewed spec/record that the phase-1 policy schema is built from.
- Scope-Paths: .aw/records/specs/, docs/, tests/
- Status: draft
- Set: agentadhere
- Order: 1
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: gfokao

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Produce the Phase-0 classification foundation: a threat model, three assurance classes, and an invariant catalog tagging each process rule with its assurance class and observable evidence, so phases 1-5 have precise, honest targets.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the catalog spec

- [ ] E-01 Author a reviewed spec/record capturing the threat model, the three assurance classes (Guidance / Repository-invariant / Authority-invariant), and an invariant catalog: each toolkit process rule with its assurance class and its observable evidence (or an honest unverifiable/probabilistic label). No enforcement code.
  - Depends on: none
  - Expected outcome: a spec under `.aw/records/specs/` enumerating invariants + classes + evidence, reviewable and citable by phase 1.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Findings bu9yij is the source of truth (sections 7.1 assurance levels, 6 mechanism table, 10 residual risks/non-goals).
- Existing enforced invariants to catalog: path-scoped commits (AGENTS.md), `status_untooled_gate`/`executed_transition_gate` hooks, `aw ipd lint` finalize gates, `aw check` rules, the bklggrad release-gate guard, leak-sanitizer.
- Specs carry a bare-enum `- Status:` and a `## Workflow history`; use `aw specs`/`aw spec` to manage.

## Findings

The catalog is analysis, not code; its value is preventing later phases from overselling local controls. Reliability comes from honest labeling of what is observable vs probabilistic (findings section 10 non-goals).

## Proposed changes (ordered, validatable)

1. New spec/record: threat model + assurance classes + invariant catalog with evidence tags.
2. Cross-reference AGENTS.md invariants into the catalog.

## Deferred / out of scope (with reason)

- Any enforcement (schema, engine, hooks, CI): phases 1-5.

## Scope check

- Over-scope: none (no code).
- Under-scope: none (the classification is the whole deliverable).

## Required tests / validation

- The spec exists, lists each invariant with an assurance class and an observable-evidence entry (or honest unverifiable label), and passes `aw specs check`.
- A reviewer can trace each phase-1 policy rule back to a cataloged invariant.

## Spec / documentation sync

- The catalog IS a spec; link it from AGENTS.md and the agentadhere orchestrator.

## Open questions

### OQ-01: One spec, or a catalog data file the engine can load?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Start with a human-reviewed spec; if phase 1 benefits from a machine-readable catalog, derive a data file from it then. Decide at phase-1 boundary.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
