# IPD: research scaffold, directives, and prior-decision updates (Set `research-org`, Order 7)

- Date: 2026-07-30
- Kind: child
- Concern: wire the convention into the framework: installer scaffold (dir shape + generated READMEs), the thin always-loaded AGENTS.md pointer (F6 token economy), the P5 revision (cite-by-id replaces never-move-research), a DECISIONS pointer entry, and a TODO future-work note naming `plans/executed/` as the next adopter.
- Scope: scaffold + directives + prior-decision edits, consuming Orders 01/03/05. No new tool behavior. Requires Orders 01, 03, 05 executed; if their symbols/paths are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 7
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the framework wiring + the recorded unwinding of the prior non-canon decisions.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.

## Goal

Make the convention ship and be discoverable at near-zero permanent token cost, and record the decisions it revises. Scaffold the research dir shape + generated READMEs via the installer; add ONE thin AGENTS.md pointer line to the `aw research`/`aw archive` verbs (detail lives in `--help` + the dir README, F6); revise GUIDING_PRINCIPLES P5's research carve-out to cite-by-id + tool-maintained references; add a DECISIONS pointer entry to the spec; add a TODO future-work note (plans/executed/ next). Spec Sections 4.11, 7, 8.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: scaffold and pointer

- [ ] E-01 confirm Orders 01, 03, 05 are executed and the `research/` dir shape + INDEX + states exist, else STOP.
  - Depends on: none
  - Expected outcome: the research dir shape/INDEX/states are present; if absent the child halts.
  - Execution state: pending
- [ ] E-02 add the installer scaffold: the `research/` dir shape (hot root + `reference/`, `archive/`) + generated no-clobber READMEs describing the convention (pointing to the spec), wired into the install flow like the other `.agents/docs` READMEs.
  - Depends on: E-01
  - Expected outcome: dirs + no-clobber READMEs are created; dry-run works; the scaffold is idempotent.
  - Execution state: pending
- [ ] E-03 add the thin AGENTS.md pointer (F6): ONE line in `agents_pointer_prose` pointing at the `aw research`/`aw archive` verbs ("do not hand-name or hand-maintain the index"); regenerate AGENTS.md to an empty diff; the AGENT-PLANS sibling untouched.
  - Depends on: E-01
  - Expected outcome: `aw install .` yields an empty AGENTS.md diff except the one pointer line; AGENT-PLANS is byte-identical.
  - Execution state: pending

### Task group 2: prior-decision edits and tests

- [ ] E-04 revise GUIDING_PRINCIPLES P5's research carve-out: research is cited by `<id6>` via the manifest and is freely movable; the tool maintains references; supersede the never-move-research text.
  - Depends on: E-01
  - Expected outcome: P5 no longer says never-move-research and describes cite-by-id.
  - Execution state: pending
- [ ] E-05 add a DECISIONS pointer entry (pin the number at execution) referencing the spec; note it revises the timestamp-grouping theory, P5, and the founding free-form-research stance (spec Section 8).
  - Depends on: E-01
  - Expected outcome: the entry is present, points to the spec, and lists the three revised decisions.
  - Execution state: pending
- [ ] E-06 add a TODO future-work note naming `plans/executed/` (the ~85/mo, 179-file pain) as the highest-value next adopter of the convention.
  - Depends on: E-01
  - Expected outcome: the note is present with the measured rationale.
  - Execution state: pending
- [ ] E-07 add scaffold tests (dirs + no-clobber READMEs created; dry-run; idempotent) in the existing scaffold test harness; run them plus the full suite and paste output.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: new tests pass; full suite still green; the AGENTS.md regen is an empty diff except the pointer line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Scaffold precedent: `ensure_docs_readmes`/`create_setup_artifacts` in `engine.py` write no-clobber dir READMEs and mkdir buckets; extend for the research dir shape.
- The always-loaded block is `agents_pointer_prose()` (engine.py), regenerated into AGENTS.md via the sectioned path; a refresh MUST be an empty diff and must not disturb the `AGENT-PLANS` sibling.
- P5 lives in `GUIDING_PRINCIPLES.md` (section 5, "Externalize state"); its research carve-out is the boundary bullet this Set revises.
- DECISIONS entries are short pointers to specs (e.g. D112 points at ipd-spec); keep the depth in the spec, not inline.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C7-1 | HIGH | Low | weak-agent (F6/G1) | discovery | The tools help only if agents know to use them; must be discoverable at near-zero always-loaded token cost. | spec 4.11 |
| C7-2 | MEDIUM | Low | integrity | consistency | P5 currently says "never move research"; the Set moves research, so P5 must be revised or it contradicts the convention. | spec 8, GUIDING_PRINCIPLES P5 |
| C7-3 | MEDIUM | Low | provenance | record | The revised prior decisions must be recorded (not silently contradicted). | spec 8 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 7 | Installer scaffold: research dir shape + generated no-clobber READMEs; wire into install. | `agent_workflows/engine.py`, README templates | Low | E-02 |
| 2 | 4.11 | Thin AGENTS.md pointer to the verbs; regenerate to empty diff; AGENT-PLANS untouched. | `agent_workflows/engine.py`, `AGENTS.md` | Low | E-03 |
| 3 | 8 | Revise P5 research carve-out (cite-by-id + movable + tool-maintained refs). | `GUIDING_PRINCIPLES.md` | Low | E-04 |
| 4 | 8 | DECISIONS pointer entry (pin number). | `DECISIONS.md` | Low | E-05 |
| 5 | 7 | TODO future-work note: plans/executed/ next adopter. | `TODO.md` | Low | E-06 |

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

### OQ-01: exact wording of the one-line AGENTS.md pointer

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: the AGENTS.md pointer stays a single line for token economy (pointing at the `aw research`/`aw archive` verbs). Confirm the exact wording at review; if it changes, only this child changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01/03/05 in `executed/` and confirm the research dir shape/INDEX/states are present.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the scaffold test output (dirs + no-clobber READMEs; dry-run; idempotent).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- AGENTS.md` showing ONLY the added pointer line; confirm AGENT-PLANS is byte-identical.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: quote the revised P5 text; confirm it no longer says never-move-research and describes cite-by-id.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm the DECISIONS entry exists, points to the spec, and lists the three revised decisions.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: confirm the TODO note names plans/executed/ with the measured rationale.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the full-suite summary; confirm leak-clean and no em/en dashes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03, 05; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including the empty AGENTS.md diff and byte-identical AGENT-PLANS); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (scaffold/pointer/P5/DECISIONS/TODO only; edit only the existing `agents_pointer_prose`; regenerate AGENTS.md, do not hand-edit; do not add the separate aw:block edit-protection directive here). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
