# Spec: release record + `Blocks-Release` gate (make release-blockers first-class)

- Date: 2026-08-18
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Today, whether a backlog item / spec / plan BLOCKS THE NEXT RELEASE is captured only in prose (e.g. a spec paragraph "RELEASE BLOCKER"). There is no programmatically parsable, single-source way to (a) mark that an item gates a release, and (b) surface "what blocks the next release" in `aw attention`. This is DISTINCT from an item being blocked-BY something (the existing `blocked` status + typed gate). Item #35 asks for a consistent, machine-readable release-blocker model, and notes there is currently no artifact representing "the release" to block against. The maintainer chose: introduce a lightweight RELEASE record that items target via a gate field.
- Relation to prior work: BUILDS ON the typed-gate model (`Gate-Kind`/`Gate-Ref`, attention_contract.py) and the attention view (attention.py). Consumes the roadmaps record tree (a natural home for a release record) or a new record class. Feeds Set F (attention must surface release-blockers).
- Design spec for maintainer approval. Likely a release blocker itself only in the sense that the maintainer wants blockers visible before shipping; the MECHANISM can ship in the UX batch.

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8): authored from TODO item #35; the maintainer explicitly asked to discuss/decide and chose the release-record model (a release artifact that items target via a Blocks-Release field).

## 0. Concepts (kept distinct)

- BLOCKED-BY (exists today): an item cannot proceed because something else must happen first. Modeled by `Status: blocked` + a typed `Gate-Kind`/`Gate-Ref` on the item.
- BLOCKS-RELEASE (this spec): an item, regardless of its own status, is a gate on shipping the NEXT (or a specific) release. This is a property pointing FROM the item TO a release, not the item's own blocked state.

These must not be conflated: a `ready`/`open` item can still be a release blocker (it must be DONE before release), and a `blocked` item may or may not gate the release.

## 1. Goals

- G1. A first-class, lightweight RELEASE record (an artifact with a stable id6) representing a planned release, e.g. under `.aw/records/roadmaps/` or a new `releases` class. It carries the release's target version (or "next"), a summary, and a status (planned/blocked/shipped).
- G2. A machine-readable `Blocks-Release: <release-id6|next>` field that a backlog item / spec / plan may carry to declare it gates that release. Single source of truth ON THE ITEM (not duplicated on the release).
- G3. `aw attention` surfaces, in a dedicated section or column, every item whose `Blocks-Release` targets the next/active release and is not yet done - i.e. "what blocks the release" (feeds Set F item #35/#36).
- G4. A verb to set/clear the field (e.g. `aw backlog set <id> --blocks-release next`) and to view the release's blocker set (e.g. `aw find all --blocks-release next` or a release read verb).
- G5. Validation: `Blocks-Release` must resolve to an existing release record (or the literal `next`); a check flags a dangling release reference.

## 2. Non-goals

- Automating the actual release (that is RELEASING.md Section 9, human-gated).
- Replacing the typed blocked-by gate (that stays for blocked-BY).
- A full roadmap/milestone system; this is minimally "a release + what gates it".

## 3. Design options (for maintainer decision at review)

- OPTION A - reuse the roadmaps tree: a release IS a roadmap record with `Kind: release`. Minimal new surface; roadmaps already exist as a record class. Recommendation.
- OPTION B - new `releases` record class + tree (`.aw/records/releases/`): cleaner separation, more new surface (taxonomy, resolver, attention mapping, validators).

Recommendation: OPTION A (a roadmap record of kind release) to minimize new surface, unless the maintainer wants a dedicated tree.

## 4. Requirements (once the option is chosen)

- R1. Define the release record shape (front-matter: `Id`, `Status` in {planned, blocked, shipped}, `Version` or `next`, `Summary`) + where it lives.
- R2. Define the `Blocks-Release:` item field grammar (value = a release id6 or the literal `next`), parsed by the item validators (backlog/specs/plans front-matter parsers).
- R3. A setter: extend `aw backlog set` / `aw specs set` (and the plan metadata) to set/clear `--blocks-release`.
- R4. `aw attention` computes and displays the release-blocker set for the next/active release (items with `Blocks-Release` targeting it that are not done). See Set F.
- R5. Validation (`aw check`): a `Blocks-Release` value must resolve to an existing release record or `next`; flag dangling. Fold into the Set D check engine.
- R6. Document the concept (BLOCKS-RELEASE vs BLOCKED-BY) in AGENTS.md so agents capture blockers consistently and in ONE place (on the item).

## 5. Testable acceptance criteria

- AC1. A release record can be created and carries a stable id6 + status.
- AC2. An item with `Blocks-Release: next` is surfaced by `aw attention` in the release-blocker view and disappears from it when the item reaches done.
- AC3. `aw check` flags an item whose `Blocks-Release` points at a nonexistent release.
- AC4. The setter sets/clears the field and it round-trips through the parser.
- AC5. AGENTS.md documents the model; the existing prose "RELEASE BLOCKER" specs can be re-expressed via the field.

## 6. Open questions

### OQ-1: roadmap-record (A) vs dedicated releases class (B)?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: determines the whole surface. Recommendation A (roadmap kind=release).

### OQ-2: value grammar - allow only `next`, or also a specific release id6 from day one?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Recommendation: support BOTH `next` (the singleton active release) and an explicit release id6, so multiple planned releases can each gate. `next` resolves to the single release record whose status is planned/active.

### OQ-3: is the mechanism itself a release blocker for THIS release?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Recommendation: the mechanism ships in the UX batch (so this release's blockers become visible), but it need not gate the release on itself. Maintainer to confirm.
