# IPD: research scaffold, directives, and prior-decision updates (Set `research-org`, Order 7)

- Date: 2026-07-30
- Concern: wire the convention into the framework: installer scaffold (dir shape + generated READMEs), the thin always-loaded AGENTS.md pointer (F6 token economy), the P5 revision (cite-by-id replaces never-move-research), a DECISIONS pointer entry, and a TODO future-work note naming `plans/executed/` as the next adopter.
- Scope: scaffold + directives + prior-decision edits, consuming Orders 01/03/05. No new tool behavior. Requires Orders 01, 03, 05 executed; if their symbols/paths are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 7
- Quarantine: old-shape draft; superseded by the ipd-structure convention, to be re-authored to the E-*/V-* shape
- Quarantine owner: maintainer (IPD-system-first sequencing decision, 2026-08-03)
- Quarantine follow-up: re-author the research-org Set to the new schema after the ipd-structure Set lands
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the framework wiring + the recorded unwinding of the prior non-canon decisions.

- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's IPD-system-first sequencing decision defers this old-shape research-org plan; quarantined under spec Section 13.3 (metadata trio added) pending re-authoring to the new E-*/V-* shape after the ipd-structure Set. Not conforming, not an error; an informational disposition.

## Goal

Make the convention ship and be discoverable at near-zero permanent token cost, and record the decisions it revises. Scaffold the research dir shape + generated READMEs via the installer; add ONE thin AGENTS.md pointer line to the `aw research`/`aw archive` verbs (detail lives in `--help` + the dir README, F6); revise GUIDING_PRINCIPLES P5's research carve-out to cite-by-id + tool-maintained references; add a DECISIONS pointer entry to the spec; add a TODO future-work note (plans/executed/ next). Spec Sections 4.11, 7, 8.

## Detailed Implementation Checklist (TODO)

- [ ] **Precheck**: Orders 01, 03, 05 executed; `research/` dir shape + INDEX + states exist, else STOP.
- [ ] **Task 1: installer scaffold** - `research/` dir shape (hot root + `reference/`, `archive/`) + generated no-clobber READMEs describing the convention (point to the spec); wire into the install flow like the other `.agents/docs` READMEs.
- [ ] **Task 2: thin AGENTS.md pointer (F6)** - ONE line in `agents_pointer_prose` pointing at the `aw research`/`aw archive` verbs ("do not hand-name or hand-maintain the index"); regenerate AGENTS.md to an empty diff; AGENT-PLANS sibling untouched.
- [ ] **Task 3: revise P5** - edit `GUIDING_PRINCIPLES.md` research carve-out: research is cited by `<id6>` via the manifest and is freely movable; the tool maintains references. Supersede the never-move-research text.
- [ ] **Task 4: DECISIONS pointer entry** (pin number at execution) referencing the spec; note it revises the timestamp-grouping theory, P5, and the founding free-form-research stance (spec Section 8).
- [ ] **Task 5: TODO future-work note** naming `plans/executed/` (the ~85/mo, 179-file pain) as the highest-value next adopter of the convention.
- [ ] **Tests** for the scaffold (dirs + no-clobber READMEs created; dry-run; idempotent) in the existing scaffold test harness; run + full suite and PASTE output.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- Scaffold precedent: `ensure_docs_readmes`/`create_setup_artifacts` in `engine.py` write no-clobber dir READMEs and mkdir buckets; extend for the research dir shape.
- The always-loaded block is `agents_pointer_prose()` (engine.py), regenerated into AGENTS.md via the sectioned path; a refresh MUST be an empty diff and must not disturb the `AGENT-PLANS` sibling.
- P5 lives in `GUIDING_PRINCIPLES.md` (section 5, "Externalize state"); its research carve-out is the boundary bullet this Set revises.
- DECISIONS entries are short pointers to specs (e.g. D112 points at ipd-spec); keep the depth in the spec, not inline.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C7-1 | HIGH | Low | weak-agent (F6/G1) | discovery | The tools help only if agents know to use them; must be discoverable at near-zero always-loaded token cost. | spec 4.11 |
| C7-2 | MEDIUM | Low | integrity | consistency | P5 currently says "never move research"; the Set moves research, so P5 must be revised or it contradicts the convention. | spec 8, GUIDING_PRINCIPLES P5 |
| C7-3 | MEDIUM | Low | provenance | record | The revised prior decisions must be recorded (not silently contradicted). | spec 8 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 7 | Installer scaffold: research dir shape + generated no-clobber READMEs; wire into install. | `agent_workflows/engine.py`, README templates | Low | scaffold test: dirs + READMEs created, no-clobber, dry-run, idempotent |
| 2 | 4.11 | Thin AGENTS.md pointer to the verbs; regenerate to empty diff; AGENT-PLANS untouched. | `agent_workflows/engine.py`, `AGENTS.md` | Low | `aw install .` yields empty AGENTS.md diff except the one pointer line; AGENT-PLANS byte-identical |
| 3 | 8 | Revise P5 research carve-out (cite-by-id + movable + tool-maintained refs). | `GUIDING_PRINCIPLES.md` | Low | P5 no longer says never-move-research; describes cite-by-id |
| 4 | 8 | DECISIONS pointer entry (pin number). | `DECISIONS.md` | Low | entry present, points to the spec, lists the three revised decisions |
| 5 | 7 | TODO future-work note: plans/executed/ next adopter. | `TODO.md` | Low | note present with the measured rationale |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Implementing the convention for plans/prompts/comms | scope | Future adopters; research-first by design. | The TODO note; a later Set |
| The "do not hand-edit inside aw:block" AGENTS.md directive | scope | Separate existing TODO; this only adds the research pointer line. | Its own IPD |

## Scope check

- Over-scope: none - scaffold + one pointer line + P5/DECISIONS/TODO edits.
- Under-scope: MUST make the convention scaffolded, discoverable (thin pointer), and record the P5/decisions revision so nothing contradicts the shipped convention.

## Required tests / validation

Extend the scaffold test harness (dirs + no-clobber READMEs; dry-run; idempotent). Confirm the AGENTS.md regen is an empty diff except the pointer line and AGENT-PLANS is byte-identical. Run `python -m pytest -q`; PASTE. Leak-clean; no em/en dashes.

## Spec / documentation sync

`GUIDING_PRINCIPLES.md` (P5), `DECISIONS.md` (pointer), `TODO.md` (future work), `.agents/docs/research/README.md` (regenerated), `AGENTS.md` (regenerated pointer). The spec itself is unchanged (this executes it).

## Open questions

- Exact wording of the one-line AGENTS.md pointer (keep it to a single line for token economy). Confirm at review.

## Validation and cross-check (verify before reporting done)

- [ ] Precheck: cite Orders 01/03/05 in executed/ and the research dir shape/INDEX/states present.
- [ ] Task 1: PASTE the scaffold test output (dirs + no-clobber READMEs; dry-run; idempotent).
- [ ] Task 2: PASTE `git diff -- AGENTS.md` showing ONLY the added pointer line; confirm AGENT-PLANS byte-identical.
- [ ] Task 3: quote the revised P5 text; confirm it no longer says never-move-research and describes cite-by-id.
- [ ] Task 4: confirm the DECISIONS entry exists, points to the spec, and lists the three revised decisions.
- [ ] Task 5: confirm the TODO note names plans/executed/ with the measured rationale.
- [ ] PASTE the full-suite summary; confirm leak-clean and no em/en dashes.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03, 05; if absent, STOP. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence (including the empty AGENTS.md diff and byte-identical AGENT-PLANS); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (scaffold/pointer/P5/DECISIONS/TODO only; edit only the existing `agents_pointer_prose`; regenerate AGENTS.md, do not hand-edit; do not add the separate aw:block edit-protection directive here). Never create or push a tag / Release / PyPI upload.
