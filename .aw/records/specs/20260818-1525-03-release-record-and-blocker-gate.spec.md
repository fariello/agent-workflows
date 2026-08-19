# Spec: release record + `Blocks-Release` gate (make release-blockers first-class)

- Date: 2026-08-18
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Today, whether a backlog item / spec / plan BLOCKS THE NEXT RELEASE is captured only in prose (e.g. a spec paragraph "RELEASE BLOCKER"). There is no programmatically parsable, single-source way to (a) mark that an item gates a release, and (b) surface "what blocks the next release" in `aw attention`. This is DISTINCT from an item being blocked-BY something (the existing `blocked` status + typed gate). Item #35 asks for a consistent, machine-readable release-blocker model, and notes there is currently no artifact representing "the release" to block against. The maintainer chose: introduce a lightweight RELEASE record that items target via a gate field.
- Relation to prior work: BUILDS ON the typed-gate model (`Gate-Kind`/`Gate-Ref`, attention_contract.py) and the attention view (attention.py). Consumes the roadmaps record tree (a natural home for a release record) or a new record class. Feeds Set F (attention must surface release-blockers).
- Design spec; all decisions now RESOLVED (Sections 3, 6). **RELEASE BLOCKER (maintainer-confirmed 2026-08-18):** so this release's blockers are machine-visible before shipping. Implementation IPDs authored after the release-critical UX Sets (A-F).

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8): authored from TODO item #35; the maintainer explicitly asked to discuss/decide and chose the release-record model (a release artifact that items target via a Blocks-Release field).
- 2026-08-18 note (aw specs): spec-editor pass (opencode Opus 4.8): added Users/scenarios + Constraints/dependencies sections, tagged requirements MUST/SHOULD; fixed stale/verb-coupled items (02 R2/AC1 latest-one + plans/IPD-S405 exclusion; 03 R5/AC3 -> check_blocks_release engine function not the aw check verb).

## 0. Concepts (kept distinct)

- BLOCKED-BY (exists today): an item cannot proceed because something else must happen first. Modeled by `Status: blocked` + a typed `Gate-Kind`/`Gate-Ref` on the item.
- BLOCKS-RELEASE (this spec): an item, regardless of its own status, is a gate on shipping the NEXT (or a specific) release. This is a property pointing FROM the item TO a release, not the item's own blocked state.

These must not be conflated: a `ready`/`open` item can still be a release blocker (it must be DONE before release), and a `blocked` item may or may not gate the release.

## 0.1 Users / actors and scenarios

- **Maintainer / release driver (human):** asks "what still blocks the release?" and wants a single, machine-computed answer instead of grepping prose. Scenario: creates a `2.0.0` release record; as items are marked `Blocks-Release: next`, `aw attention` shows exactly the outstanding gates; when the last one is done, the release-blocker view is empty -> ready for the human-gated Section 9.
- **Coding agent:** when it identifies a must-fix-before-release item, it records that ON the item (`aw backlog set <id> --blocks-release next`) rather than editing a prose paragraph, so the fact is parsable and lives in one place.
- **Reviewer:** validates that no item points at a nonexistent release (a dangling gate), via the check engine.
Key distinction the model enforces: BLOCKS-RELEASE (this item gates shipping) is orthogonal to BLOCKED-BY (this item is itself stuck) - a `ready` item can still block the release.

## 0.2 Constraints and dependencies

- BUILDS ON the typed-gate model (`Gate-Kind`/`Gate-Ref`) and the attention view; a NEW record class means the standard integration points (RecordClass enum + `_RECORD_CLASS_SUBPATHS`, the `release` naming facet in BOTH grammar sites, an attention `_RELEASES_MAP`, a `check` validator, README + installer scaffolding incl. the DUPLICATED `DOCS_SUBDIRS`) - all mechanical, following existing class patterns.
- The dangling-reference VALIDATION is delivered as an engine FUNCTION (`check_blocks_release` returning Drift), folded into the Set D (awcheck) engine seam; the user-facing `aw check` VERB that surfaces it belongs to Set A (awcmdsurf) and is NOT a prerequisite for this spec's mechanism.
- The attention SURFACING of the release-blocker set (G3) is implemented in Set F (awdoctor), which consumes the `Blocks-Release` field this spec defines.
- No network; a release record is a local `.aw/records/releases/*.release.md` file.

## 1. Goals

- G1. A first-class, lightweight RELEASE record (an artifact with a stable id6) representing a planned release, under a NEW `.aw/records/releases/` tree (Section 3). It carries the release's target version (or "next"), a summary, and a status (planned/blocked/shipped).
- G2. A machine-readable `Blocks-Release: <release-id6|next>` field that a backlog item / spec / plan may carry to declare it gates that release. Single source of truth ON THE ITEM (not duplicated on the release).
- G3. `aw attention` surfaces, in a dedicated section or column, every item whose `Blocks-Release` targets the next/active release and is not yet done - i.e. "what blocks the release" (feeds Set F item #35/#36).
- G4. A verb to set/clear the field (e.g. `aw backlog set <id> --blocks-release next`) and to view the release's blocker set (e.g. `aw find all --blocks-release next` or a release read verb).
- G5. Validation: `Blocks-Release` must resolve to an existing release record (or the literal `next`); a check flags a dangling release reference.

## 2. Non-goals

- Automating the actual release (that is RELEASING.md Section 9, human-gated).
- Replacing the typed blocked-by gate (that stays for blocked-BY).
- A full roadmap/milestone system; this is minimally "a release + what gates it".

## 3. Release record home (DECIDED, maintainer 2026-08-18)

- **A NEW dedicated record class + tree: `.aw/records/releases/`**, files named `...*.release.md` per the uniform grammar.
- Rationale (discovery + adherence, maintainer's priority): `roadmaps/` is explicitly "intent and possibilities, NOT a commitment to execute" (its README) - the OPPOSITE of a committed ship gate, so a release does not belong there semantically. A human or agent asking "what's needed for the release?" pattern-matches on `releases/` far more readily than on `roadmaps/`; a named tree lets `aw attention`/`aw check`/AGENTS.md hook it as a first-class concept (much harder if a release is a buried `Kind:` variant of a possibilities tree). Distinct concepts (committed release gate vs maybe-later roadmap) deserve distinct homes, mirroring the `prompts/` vs `prompt-library/` split.
- Cost accepted: a new record class means a `_RECORD_CLASS_SUBPATHS` entry, a resolver subpath, an attention class-map, a `check` validator, README + installer scaffolding - all mechanical, all following existing patterns for the other classes.

## 4. Requirements

(MUST = required; SHOULD = strongly preferred.)

- R1 (MUST). Define the release record shape (front-matter: `Id`, `Status` in {planned, blocked, shipped}, `Version` or `next`, `Summary`) + its home `.aw/records/releases/`, wired at all standard class integration points.
- R2 (MUST). Define the `Blocks-Release:` item field grammar (value = a release id6 or the literal `next`), parsed by the item validators (backlog/specs front-matter parsers; a plan-side setter is a deferred follow-up per the awrelease-02 note).
- R3 (MUST). A setter: extend `aw backlog set` / `aw specs set` to set/clear `--blocks-release`.
- R4 (SHOULD, delivered by Set F). `aw attention` computes and displays the release-blocker set for the next/active release (items with `Blocks-Release` targeting it that are not done). Implemented in Set F (awdoctor), which consumes this field.
- R5 (MUST). Validation delivered as the engine FUNCTION `check_blocks_release(repo_root) -> List[Drift]` (folded into the Set D check engine seam): a `Blocks-Release` value MUST resolve to an existing release record or `next` (exactly one planned release), else emit `check.blocks-release-dangling`. The user-facing `aw check` verb that renders it is Set A's, not a prerequisite here.
- R6 (MUST). Document the concept (BLOCKS-RELEASE vs BLOCKED-BY) in AGENTS.md so agents capture blockers consistently and in ONE place (on the item).

## 5. Testable acceptance criteria

- AC1. A release record can be created and carries a stable id6 + status.
- AC2. An item with `Blocks-Release: next` is surfaced by `aw attention` in the release-blocker view and disappears from it when the item reaches done.
- AC3. The `check_blocks_release` engine function flags an item whose `Blocks-Release` points at a nonexistent release (and passes when it resolves). (The `aw check` verb that surfaces this is verified in Set A, not here.)
- AC4. The setter sets/clears the field and it round-trips through the parser.
- AC5. AGENTS.md documents the model; the existing prose "RELEASE BLOCKER" specs can be re-expressed via the field.

## 6. Open questions

### OQ-1: roadmap-record vs dedicated releases class? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: NEW dedicated `.aw/records/releases/` tree (Section 3), chosen for discovery + adherence over reusing roadmaps.

### OQ-2: value grammar - `next` only, or also a specific release id6?

- Blocking: no
- Status: resolved
- Owner: opencode (recommendation adopted)
- Resolution or deferral rationale: support BOTH `next` (resolves to the single planned/active release record) and an explicit release id6, so multiple planned releases can each gate.

### OQ-3: is the mechanism a release blocker for THIS release? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: YES - the maintainer designated this a RELEASE BLOCKER (so this release's blockers are machine-visible before shipping). Implementation IPDs are authored after the release-critical UX Sets (A-F).
