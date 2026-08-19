# IPD: releases record class and blocks-release gate

- Date: 2026-08-18
- Kind: orchestrator
- Concern: Spec 20260818-1525-03 (RELEASE BLOCKER, TODO item #35): whether a backlog item / spec / plan BLOCKS THE NEXT RELEASE is captured only in prose today ("RELEASE BLOCKER" paragraphs), with no programmatically parsable single source and no artifact representing "the release" to gate against. This is DISTINCT from an item being blocked-BY something (the existing `Status: blocked` + typed `Gate-Kind`/`Gate-Ref`, attention_contract.py). The maintainer DECIDED (spec Section 3): a NEW dedicated `.aw/records/releases/` record class + tree (files `...*.release.md`), where a release record is a thin ship-gate anchor (front-matter Id / Status{planned,blocked,shipped} / Version-or-`next` / Summary), and items declare they gate a release via a machine-readable `Blocks-Release: <release-id6|next>` field pointing FROM the item TO the release. `next` resolves to the single planned/active release record; an explicit release id6 is also allowed.
- Scope: This Set builds the release-record class and the `Blocks-Release` gate FIELD end to end. IN: (a) the new `.aw/records/releases/` record class - a `_RECORD_CLASS_SUBPATHS` entry (record_producers.py:125), a resolver subpath, an attention class-map (`_RELEASES_MAP` registered in CLASS_MAPS, attention_contract.py:194-275), a check validator, README + installer scaffolding (engine.py DOCS_SUBDIRS/scaffold), plus a release-record creator/validator; (b) the `release` naming-grammar facet added to ARTIFACT_TYPE_FACETS at BOTH grammar sites (plans_refs.py:33, normalize_plan_names.py:113) since files are `*.release.md`; (c) the `Blocks-Release:` item field - parser support in the backlog/specs/plans front-matter parsers plus a setter (`--blocks-release` on `aw backlog set` / `aw specs set`) and dangling-ref validation folded into the check engine (Set awcheck); (d) documenting BLOCKS-RELEASE vs BLOCKED-BY in AGENTS.md. OUT: `aw attention` SURFACING of "what blocks the next/active release" (owned by Set awdoctor, which DEPENDS ON this Set for the gate data); automating the actual release (RELEASING.md Section 9, human-gated); a full roadmap/milestone system (spec Non-goals).
- Status: reviewed
- Set: awrelease
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: rreixg

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): high-level skeleton from spec 20260818-1525-03 (new .aw/records/releases/ class + Blocks-Release gate, RELEASE BLOCKER); children to be fleshed out.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. PR-002 (MEDIUM): completion criteria + V-01 required `aw check` verb output for the dangling-release check, but `aw check` is Set A/awcmdsurf's verb and does not exist when this Set completes; reworded to require the ENGINE function check_blocks_release(repo_root) returning the Drift. GO - PENDING HUMAN APPROVAL.

## Goal

Make release-blockers first-class and machine-visible before shipping. Introduce a lightweight,
dedicated `.aw/records/releases/` record class (a thin ship-gate anchor with a stable id6 + status)
and a machine-readable `Blocks-Release: <release-id6|next>` field that a backlog item / spec / plan
carries to declare it gates that release - a single source of truth ON THE ITEM, distinct from the
existing blocked-BY typed gate. This replaces prose "RELEASE BLOCKER" paragraphs with a parsable model
that Set awdoctor can then surface in `aw attention` and Set awcheck can validate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..03 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. Sequence: 01 (the `.aw/records/releases/` class + `release` facet + release-record creator/validator) is the foundation the gate targets; 02 (the `Blocks-Release:` item field, its setter, and the dangling-ref validation folded into Set awcheck) DEPENDS ON 01 so a `next`/id6 reference has a real record to resolve against; 03 (AGENTS.md docs) follows once the model exists. On completion advance spec 20260818-1525-03 to implemented (clearing this RELEASE BLOCKER). Note the `aw attention` surfacing of release-blockers is Set awdoctor (which consumes this Set's gate data), not this Set.
  - Depends on: none
  - Expected outcome: Orders 01..03 executed; the `.aw/records/releases/` class exists (taxonomy, resolver, attention class-map, check validator, README + installer scaffolding, `release` grammar facet at both sites) with a release-record creator/validator; the `Blocks-Release:` field parses/round-trips on backlog/specs/plans with a `--blocks-release` setter and dangling-ref validation in the check engine; AGENTS.md documents BLOCKS-RELEASE vs BLOCKED-BY; full suite + all `--check`s green; spec 20260818-1525-03 -> implemented.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by concern: 01 builds the release-record CLASS (the new tree + all the mechanical class-plumbing
+ the `release` grammar facet + a release-record creator/validator); 02 builds the `Blocks-Release`
GATE FIELD on items (parser + setter + dangling-ref validation, folded into Set awcheck); 03 DOCUMENTS
the model (BLOCKS-RELEASE vs BLOCKED-BY) in AGENTS.md and points at Set awdoctor for surfacing. 02
depends on 01 (the field must resolve to a real record class); 03 depends on both.

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | awrelease-record-class (to scaffold) | Create the `.aw/records/releases/` record class: a `_RECORD_CLASS_SUBPATHS` entry (record_producers.py:125) + a resolver subpath; a `_RELEASES_MAP` attention class-map registered in CLASS_MAPS (attention_contract.py:194-275); a `check` validator for the class; README + installer scaffolding (engine.py DOCS_SUBDIRS/scaffold); add the `release` facet to ARTIFACT_TYPE_FACETS at BOTH grammar sites (plans_refs.py:33, normalize_plan_names.py:113) so `*.release.md` files are conformant; and a release-record creator/validator producing the thin ship-gate anchor (front-matter Id / Status{planned,blocked,shipped} / Version-or-`next` / Summary), honoring the shared Drift convention (artifact_core.py:247-266). + tests. | none |
| 02 | awrelease-blocks-gate (to scaffold) | Add the `Blocks-Release: <release-id6\|next>` item field: parser support in the backlog/specs/plans front-matter parsers (backlog.py, specs.py, plans); a setter extending `aw backlog set` / `aw specs set` with `--blocks-release` (set/clear); and validation that a `Blocks-Release` value resolves to an existing release record or the literal `next` (flag dangling), folded into the check engine (Set awcheck). `next` resolves to the single planned/active release record; an explicit id6 is also accepted. + tests. | 01; awcheck (fold dangling-ref validation into the check engine) |
| 03 | awrelease-docs (to scaffold) | Document the model in AGENTS.md: BLOCKS-RELEASE (a property pointing FROM an item TO a release, regardless of the item's own status) vs BLOCKED-BY (the item's own `Status: blocked` + typed gate), so agents capture blockers consistently in ONE place (on the item); note that `aw attention` surfacing of release-blockers is delivered by Set awdoctor (this Set only supplies the gate data). | 01; 02 |

## Completion criteria (the whole Set is done only when)

- Orders 01..03 all executed and moved to `.aw/records/plans/executed/`.
- A `.aw/records/releases/` record class exists and is wired into every place the other classes are:
  taxonomy (`_RECORD_CLASS_SUBPATHS`), resolver subpath, attention class-map (`_RELEASES_MAP` in
  CLASS_MAPS), a `check` validator, README + installer scaffolding; `*.release.md` files are
  name-conformant via the `release` facet at BOTH grammar sites.
- A release record can be created carrying a stable id6 + Status{planned,blocked,shipped} + Version-or-`next`
  + Summary (AC1), via a release-record creator/validator emitting Drift.
- A backlog item / spec / plan can carry `Blocks-Release: <release-id6|next>`; the field parses and
  round-trips through the setter (`aw backlog set --blocks-release` / `aw specs set --blocks-release`,
  AC4); `next` resolves to the single planned/active release record and an explicit id6 also resolves.
- The `check_blocks_release` engine function flags an item whose `Blocks-Release` points at a nonexistent release (AC3), via validation
  folded into the check engine (Set awcheck).
- AGENTS.md documents BLOCKS-RELEASE vs BLOCKED-BY (AC5) and notes `aw attention` surfacing is Set awdoctor.
- Full serial suite green; every `--check` + `sanitize --agent` clean.
- Spec 20260818-1525-03 -> implemented (this RELEASE BLOCKER cleared).

## Cross-IPD validation

- Order 01 (release-record class) MUST precede Order 02 (the `Blocks-Release` field) because the field
  must resolve to a real record class - a `next`/id6 reference is meaningless until the `.aw/records/releases/`
  tree, resolver, and record-creator exist.
- Order 02's dangling-ref validation is FOLDED INTO the check engine owned by Set awcheck: the validator
  must plug into that engine's per-type composition (not a divergent second implementation); coordinate
  with awcheck so the release-ref check emits the shared Drift convention.
- Set awdoctor DEPENDS ON this Set: it CONSUMES the `Blocks-Release` gate data to surface "what blocks
  the next/active release" in `aw attention`. This Set does not build that surfacing; it must land the
  gate + resolution semantics first so awdoctor has real data to read.
- After landing, re-run the full check suite to confirm the `release` facet at both grammar sites agrees
  (a `*.release.md` file is conformant to `aw plan-names`/`normalize_plan_names` and to `plans_refs`).

## Deferred / out of scope (with reason)

- `aw attention` surfacing of release-blockers: owned by Set awdoctor (which depends on this Set);
  referenced, not duplicated here.
- Automating the actual release (tag/publish): RELEASING.md Section 9, human-gated (spec Non-goals).
- A full roadmap/milestone system: out of scope; this is minimally "a release + what gates it" (spec
  Non-goals). The `roadmaps/` tree stays "intent, not commitment"; a release is a distinct committed gate.
- Replacing the blocked-BY typed gate: kept as-is for blocked-BY; this Set adds an orthogonal FROM-item gate.

## Scope check

- Over-scope: none. This Set does not build the attention surfacing (awdoctor) nor the check-verb grammar
  (awcmdsurf); it supplies the gate data and folds its validator into the awcheck engine.
- Under-scope: none - Order 01 covers the full class plumbing + the `release` facet at both sites + the
  release-record creator/validator; Order 02 covers the `Blocks-Release` field parser + setter + dangling
  validation; Order 03 covers the AGENTS.md documentation. Surfacing and release automation are the
  documented sibling/OUT concerns.

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria above; the orchestrator's E-01 verification
re-runs the full serial suite + every `--check` + `sanitize --agent`, and demonstrates the spec's
acceptance criteria: a release record is created with an id6 + status (AC1), an item's `Blocks-Release`
round-trips through the setter and parser (AC4), the `check_blocks_release` engine function flags a dangling release reference (AC3),
and AGENTS.md documents the model (AC5). (AC2 - attention hides a done blocker - is verified in Set
awdoctor, which owns the surfacing.)

## Open questions

### OQ-01: Does the `Blocks-Release` field also live on plan (IPD) front-matter in this Set, or only backlog/specs first?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: The spec (R2/R3) names backlog + specs setters explicitly and says
  the item validators (backlog/specs/plans front-matter parsers) must READ the field. Lean: land parser
  READ support on all three (backlog/specs/plans) but a `--blocks-release` SETTER on backlog + specs first
  (plans set the field via the IPD schema), resolving the exact plan-setter surface at Order 02 authoring.
  Not blocking because parser read-support is uniform and the setter surface is an additive refinement.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all three child Orders 01-03 show `Status: executed` under `.aw/records/plans/executed/`; paste evidence that the `.aw/records/releases/` class is wired everywhere the other classes are (taxonomy entry, resolver subpath, `_RELEASES_MAP` in CLASS_MAPS, check validator, README + installer scaffolding) and that a `*.release.md` file is name-conformant at both grammar sites; paste a created release record (id6 + Status + Version-or-`next` + Summary); paste an item's `Blocks-Release` set/cleared via `aw backlog set --blocks-release` / `aw specs set --blocks-release` and round-tripping through the parser; paste the ENGINE function `check_blocks_release(repo_root)` returning a `check.blocks-release-dangling` Drift for an unresolvable value and NONE when it resolves (AC3) - NOT the `aw check` verb, which belongs to Set A/awcmdsurf and does not exist when this Set completes; show AGENTS.md documents BLOCKS-RELEASE vs BLOCKED-BY (AC5); paste full serial suite result + every `--check` + `sanitize --agent` clean; and show spec 20260818-1525-03 is `implemented`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: three Orders for one coherent objective (make release-blockers first-class), split by concern - 01 builds the release-record CLASS (new tree + mechanical class-plumbing + the `release` grammar facet + a record creator/validator), 02 builds the `Blocks-Release` GATE FIELD on items (parser + setter + dangling validation folded into awcheck), 03 DOCUMENTS the model in AGENTS.md - each independently reviewable/executable and each mapping to distinct spec requirements (R1/R2/R3/R5/R6). The dependency chain is strict (02 needs 01's class to resolve against; 03 documents both), so the split isolates the class-plumbing from the item-field work and keeps the awcheck coupling contained to Order 02.

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The
orchestrator (opencode Opus 4.8, or Gemini via `agy` when delegated) drives each child Order through
its own lifecycle, owns all verification + path-scoped commits (`git commit -m msg -- <path>`, never
`git add -A`/`-a`), and NEVER pushes. Each Order (and finally this orchestrator) moves to `executed/`
only after `aw ipd lint --phase pre-transition` conforms and the V-items are verified with pasted
evidence. On completion the orchestrator advances spec 20260818-1525-03 to implemented, clearing this
RELEASE BLOCKER. The `aw attention` surfacing of release-blockers is delivered by Set awdoctor (which
depends on this Set's gate data), not here. Any version bake / tag / publish is Section 9, human-gated -
not part of this Set.
