# IPD: Phase 0: threat model, assurance classes, invariant catalog, and observable-evidence definitions

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij section 7.1/8 (Phase 0): before implementing any control you must classify each invariant and define what evidence is observable, or you risk describing local hooks/hashes/files as stronger than they are and building controls with no precise target. There is no catalog today of the toolkit's process invariants, their assurance class, or their observable evidence.
- Scope: Author the Phase-0 foundation as a durable spec/record (under `.aw/records/specs/` or a docs artifact): (1) a threat model (an agent with broad local shell access can use raw tools, edit files, bypass local hooks, fabricate local records; remote acceptance is the authority boundary); (2) three assurance classes - Guidance (cooperative agents follow), Repository-invariant (noncompliant artifacts must fail checks/merge), Authority-invariant (even a locally-privileged agent must not forge/authorize); (3) an invariant catalog enumerating the toolkit's key process rules (path-scoped commits/no `add -A`, no push without authorization, no hand-edited lifecycle status, test evidence bound to the tree, IPD finalize requires validation, backlog release-gate preservation, etc.), each tagged with its assurance class and its observable evidence (what artifact/event proves compliance) or an honest "unverifiable/probabilistic" label. One catalog entry MUST be the authoring-lifecycle invariant "a finished draft IPD is advanced to `to-review`" (assurance class: Guidance; observable evidence: a `draft` plan with no authoring placeholders is deterministically detectable, so it is nudged, not left silently `draft`) - this closes the recurring miss where agents finish drafting but never advance the status, and phase-1 child 02 implements the `check.ipd-draft-ready-to-review` detect-and-nudge rule from it. This child produces NO enforcement code; it is the classification that phases 1-5 target. Deliverable is a reviewed spec/record that the phase-1 policy schema is built from.
- Scope-Paths: .aw/records/specs/, docs/, tests/
- Status: approved
- Set: agentadhere
- Order: 1
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: gfokao
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 gate execution contract added, PR-002 V-01 concrete evidence, PR-003 right-sizing assessed (single-spec pass, no split), OQ-01 resolved

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Produce the Phase-0 classification foundation: a threat model, three assurance classes, and an invariant catalog tagging each process rule with its assurance class and observable evidence, so phases 1-5 have precise, honest targets.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the catalog spec

- [x] E-01 Author a reviewed spec/record capturing the threat model, the three assurance classes (Guidance / Repository-invariant / Authority-invariant), and an invariant catalog: each toolkit process rule with its assurance class and its observable evidence (or an honest unverifiable/probabilistic label). No enforcement code.
  - Depends on: none
  - Expected outcome: a spec under `.aw/records/specs/` enumerating invariants + classes + evidence, reviewable and citable by phase 1.
  - Execution note: authored `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` (id6 pqsx96) via the new `aw specs new` producer (dogfooding ha55fi: today is 2026-08-28, the id6 cutover, so the spec is id6-clustered by construction). It has: Section 1 threat model (actor, capabilities that defeat local controls, the remote authority boundary), Section 2 the three assurance classes + observable-evidence definition, Section 3 a 15-row invariant catalog (I-01..I-15) each tagged with class + observable evidence (or honest unverifiable/forgeable-locally label), Section 4 traceability, Section 5 non-goals. No enforcement code. Doc-sync scope decision recorded as DECISION 13-gfokao-D1 (AGENTS.md/orchestrator are out of Scope-Paths/another plan, so linkage is via `- From-Plan:` + prose, not an out-of-scope edit).
  - Execution state: performed

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
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - deliver the Phase-0 catalog as ONE human-reviewed spec under `.aw/records/specs/` (the reviewable, citable source of truth phase 1 is built from). Do NOT author a machine-readable data file in this child; if phase 1 (child 02's versioned policy schema) benefits from a derived data file, it derives one FROM this spec at that boundary. Keeping the authored artifact a single spec avoids a premature parallel source of truth. Not a blocker; recorded in the gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) a spec file exists under `.aw/records/specs/` (paste its path) containing the threat model, the three assurance-class definitions (Guidance / Repository-invariant / Authority-invariant), and the invariant catalog; (b) EVERY catalog entry carries an assurance class AND an observable-evidence entry OR an explicit "unverifiable/probabilistic" label - none left blank (paste the catalog table); (c) the catalog INCLUDES the mandated authoring-lifecycle entry "a finished draft IPD is advanced to `to-review`" (class Guidance; evidence: placeholder-free `draft` is deterministically detectable) that phase-1 child 02's `check.ipd-draft-ready-to-review` rule is built from; (d) the catalog enumerates the invariants named in Scope (path-scoped commits/no `add -A`, no push without authorization, no hand-edited lifecycle status, tree-bound test evidence, IPD finalize requires validation, backlog release-gate preservation) - confirm each appears; (e) `aw specs check <path>` passes (paste the actual command output); (f) traceability: pick one phase-1 policy rule and show it traces back to a named cataloged invariant.
  - Observed evidence: |
    (a) `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` exists;
    it has Section 1 (threat model: actor, bypass capabilities, remote authority boundary), Section 2
    (the three assurance classes Guidance / Repository invariant / Authority invariant + observable-evidence
    definition), and Section 3 (the invariant catalog).
    (b) Programmatic check over the 15 catalog rows: "catalog rows: 15" and "rows with blank class/evidence: 0"
    (each row's #, invariant, class, and evidence cell is non-empty; residual-risk rows I-13/I-14/I-15 carry
    explicit "unverifiable / probabilistic / locally-forgeable" labels).
    (c) I-12 is present: "| I-12 | A finished draft IPD is advanced to `to-review` ... | Guidance | A `draft`
    plan that contains NO authoring placeholders ... deterministically detectable ... NUDGED | Phase-1 child
    02 implements `check.ipd-draft-ready-to-review` ... built FROM this catalog entry | ...".
    (d) All Scope-named invariants appear: path-scoped commits/no add -A = I-01; no push without
    authorization = I-02; no hand-edited lifecycle status = I-03 (+ terminal case I-04); tree-bound test
    evidence = I-06; IPD finalize requires validation = I-05; backlog release-gate preservation = I-07
    (grep of I-0[1-7] and I-1[0-9] confirms I-01..I-07, I-10..I-15 present).
    (e) `aw specs check .aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`
    -> "aw specs check: all specs conform." (exit 0). `aw check all --agent` total findings = 68 == HEAD
    baseline (0 new; 0 on the new spec; an interim `- Set: agentadhere` line was removed to avoid a
    cross-type `check.setid-collision`, see DECISION 13-gfokao-D1). `aw sanitize --agent` clean.
    Full suite `python -m pytest tests/ -p no:randomly` -> "2453 passed, 1 skipped in 21.04s".
    (f) Traceability (Section 4): phase-1 rule `check.ipd-draft-ready-to-review` traces to catalog
    invariant I-12 (Guidance; placeholder-free draft deterministically detectable), inheriting I-12's
    Guidance/nudge class; additional traces map `check.status-untooled`->I-03,
    `check.blocking-item-closed-without-gate`->I-07, `check.name-nonconformant`->I-09,
    `executed_transition_gate`->I-04, `evaluate_ipd_dependencies`->I-08.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: E-01 names three parts (threat model, three assurance classes, invariant catalog), but they are ONE cohesive analytical artifact - a single spec document - authored in one focused pass, with a single verification surface (`aw specs check` + one traceability trace) and no independent code test-surfaces. Splitting one spec across child IPDs would fragment a single coherent analysis and add lifecycle overhead with no independent-verification gain, so this stays a single right-sized E-item. The executor MUST treat it as one authoring pass and MUST NOT expand it into enforcement code (that is phases 1-5).

### Open questions resolved

- OQ-01 (one spec vs a machine-readable catalog data file): RESOLVED - deliver ONE human-reviewed spec under `.aw/records/specs/`; a derived machine-readable data file, if ever needed, is phase-1 child 02's to derive FROM this spec. No blocker.

### Execution contract

- Scope fence: touch ONLY `.aw/records/specs/` (the new catalog spec), `docs/` (optional cross-links), and this plan's own lifecycle artifact; optionally add a `tests/` traceability check if one is warranted. Author NO enforcement code (no schema, engine, hooks, or CI - those are phases 1-5). If the work seems to require code or to edit another child, STOP and report; do not expand scope.
- Honesty rule (hard MUST): when V-01 reports `aw specs check` passed or any check passed, paste the ACTUAL command output; never claim a pass you did not run.
- Commit rule: commit ONLY this child's own changed files, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push. Manage the new spec's status/history with `aw spec set`/`aw specs note` (do NOT hand-edit spec status).
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
