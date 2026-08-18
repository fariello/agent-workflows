# IPD: research scaffold, directives, and prior-decision updates (Set `research-org`, Order 7)

- Date: 2026-07-30
- Kind: child
- Concern: wire the convention into the framework: installer scaffold (dir shape + generated READMEs), the thin always-loaded AGENTS.md pointer (F6 token economy), the P5 revision (cite-by-id replaces never-move-research), a DECISIONS pointer entry, and a TODO future-work note naming `plans/executed/` as the next adopter.
- Scope: scaffold + directives + prior-decision edits, consuming Orders 01/03/05. No new tool behavior. Requires Orders 01, 03, 05 executed; if their symbols/paths are absent, STOP.
- Status: executed
- Set: researchorg (research-org)
- Order: 7
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: bv7oat

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the framework wiring + the recorded unwinding of the prior non-canon decisions.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-C07-3 (scaffold only the NEW reference/archive dirs + convention README; research/ already scaffolded), PR-C07-4 (created-count assertion + real/dry-run parity), PR-C07-6 (P5 revised against the ACTUAL bullet text, narrowed to keep specs path-stable), PR-C07-5 (DECISIONS entry cites D88), PR-C07-7/8 (pointer is a short section; E-01 gates on symbols not populated shards).
- 2026-08-07 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): scaffolded `research/reference`+`research/archive` shard parents (`RESEARCH_SHARD_SUBDIRS`) + updated the shipped README template + count assertion (24) + parity test; updated `agents_pointer_prose` to the `aw research`/`aw archive` verbs (AGENTS.md regenerated via installer, commit 4fd2921, empty-diff invariant + AGENT-PLANS byte-identical); narrowed GUIDING_PRINCIPLES P5; added DECISIONS D123 (cites D88); added the TODO plans/executed/ next-adopter note. Product commit 94c4f49 (source) + 4fd2921/fa6ad21 (installer-authored AGENTS.md + manifest sync). A prompts-loop bug I nearly introduced was caught by the scaffold tests and fixed. Full suite green (Ran 628 tests OK, skipped=1); leak-clean; no em/en dashes. All E-01..E-07 performed and V-01..V-07 pass.

## Goal

Make the convention ship and be discoverable at near-zero permanent token cost, and record the decisions it revises. Scaffold the research dir shape + generated READMEs via the installer; add ONE thin AGENTS.md pointer line to the `aw research`/`aw archive` verbs (detail lives in `--help` + the dir README, F6); revise GUIDING_PRINCIPLES P5's research carve-out to cite-by-id + tool-maintained references; add a DECISIONS pointer entry to the spec; add a TODO future-work note (plans/executed/ next). Spec Sections 4.11, 7, 8.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: scaffold and pointer

- [x] E-01 confirm Orders 01, 03, 05 are executed and their SYMBOLS/paths are present (`research_contract`, `aw research index`, `aw archive`), else STOP. Do NOT require populated `reference/`/`archive/` shard dirs to exist (they are created on demand by `aw archive`, so a fresh post-01/03/05 repo may have none).
  - Depends on: none
  - Expected outcome: the Order 01/03/05 symbols and verbs are importable/invokable; if absent the child halts.
  - Execution state: performed
- [x] E-02 extend the installer scaffold. NOTE `.agents/docs/research/` is ALREADY scaffolded (`DOCS_SUBDIRS` includes `research`, with a `.gitkeep` and the existing no-clobber `agents-docs-research-README.md`). The NEW work is: create the `reference/` and `archive/` parent dirs (weekly shards are created on demand, not at install), and provide the convention README. Decide whether the convention content REPLACES the existing `agents-docs-research-README.md` template or is a distinct file, and extend BOTH the real and dry-run branches of `create_setup_artifacts`. Update the created-count assertion in `tests/test_setup_artifacts.py` and assert real-vs-dry-run parity for the new artifacts.
  - Depends on: E-01
  - Expected outcome: `reference/`+`archive/` parent dirs + the convention README are created (no-clobber); dry-run matches real; the scaffold is idempotent; the created-count assertion is updated.
  - Execution state: performed
- [x] E-03 add the thin AGENTS.md pointer (F6): a SHORT new `###` section (a few sentences, consistent with the existing sections) in `agents_pointer_prose` pointing at the `aw research`/`aw archive` verbs ("do not hand-name or hand-maintain the index"); regenerate AGENTS.md; the AGENT-PLANS sibling untouched.
  - Depends on: E-01
  - Expected outcome: `aw install .` yields an AGENTS.md diff limited to the new pointer section; AGENT-PLANS is byte-identical.
  - Execution state: performed

### Task group 2: prior-decision edits and tests

- [x] E-04 revise the actual GUIDING_PRINCIPLES P5 carve-out bullet ("Do not move artifacts that are cited by a stable path. Durable knowledge (research analysis notes, specs) is referenced by path ... keep the path stable ...") to NARROW it: keep specs path-stable, but exempt research (research is cited by `<id6>` via the manifest, freely movable, tool-maintained references). Do not delete the bullet wholesale.
  - Depends on: E-01
  - Expected outcome: the P5 bullet still keeps specs path-stable but no longer forbids moving research and describes cite-by-id6 for research.
  - Execution state: performed
- [x] E-05 add a DECISIONS pointer entry (pin the number at execution; next is D123) referencing the spec; note it revises the timestamp-grouping theory, P5 (and D88, which established P5's location-over-contents/never-move carve-out), and the founding free-form-research stance (spec Section 8).
  - Depends on: E-01
  - Expected outcome: the entry is present, points to the spec, and lists the revised decisions including D88.
  - Execution state: performed
- [x] E-06 add a TODO future-work note naming `plans/executed/` (the ~85/mo, 179-file pain) as the highest-value next adopter of the convention.
  - Depends on: E-01
  - Expected outcome: the note is present with the measured rationale.
  - Execution state: performed
- [x] E-07 add scaffold tests (dirs + no-clobber READMEs created; dry-run; idempotent) in the existing scaffold test harness; run them plus the full suite and paste output.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: new tests pass; full suite still green; the AGENTS.md regen is an empty diff except the pointer line.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Scaffold precedent: `ensure_docs_readmes`/`create_setup_artifacts` in `engine.py` write no-clobber dir READMEs and mkdir buckets. `research` is ALREADY in `DOCS_SUBDIRS` with an existing `agents-docs-research-README.md`; the new work is the `reference/`/`archive/` parent dirs + the convention README, extending BOTH the real and dry-run branches, with the `tests/test_setup_artifacts.py` created-count assertion updated and real/dry-run parity asserted.
- The always-loaded block is `agents_pointer_prose()` (engine.py), regenerated into AGENTS.md via the sectioned path; a refresh MUST limit the diff to the new pointer section and must not disturb the `AGENT-PLANS` sibling (byte-identical).
- P5 lives in `GUIDING_PRINCIPLES.md` (the "Do not move artifacts that are cited by a stable path" bullet); it covers research AND specs jointly, so the revision NARROWS it (keep specs path-stable, exempt research), not deletes it.
- DECISIONS entries are short pointers to specs (e.g. D112/D122 point at their specs); keep the depth in the spec, not inline; the new entry must also name D88 among the decisions it revises.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C7-1 | HIGH | Low | weak-agent (F6/G1) | discovery | The tools help only if agents know to use them; must be discoverable at near-zero always-loaded token cost. | spec 4.11 |
| C7-2 | MEDIUM | Low | integrity | consistency | P5 currently says "never move research"; the Set moves research, so P5 must be revised or it contradicts the convention. | spec 8, GUIDING_PRINCIPLES P5 |
| C7-3 | MEDIUM | Low | provenance | record | The revised prior decisions must be recorded (not silently contradicted). | spec 8 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 7 | Installer scaffold: add `reference/`/`archive/` parent dirs + convention README (research/ already scaffolded); extend real+dry-run branches; update created-count assertion + parity. | `agent_workflows/engine.py`, README templates, `tests/test_setup_artifacts.py` | Low | E-02 |
| 2 | 4.11 | Thin AGENTS.md pointer section to the verbs; regenerate (diff limited to the section); AGENT-PLANS byte-identical. | `agent_workflows/engine.py`, `AGENTS.md` | Low | E-03 |
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

Extend the scaffold test harness (dirs + no-clobber READMEs; dry-run; idempotent; the created-count assertion is updated; real-vs-dry-run parity for the new artifacts). Confirm the AGENTS.md regen diff is limited to the new pointer section and AGENT-PLANS is byte-identical. Run `python3 -m unittest discover -s tests -t .`; PASTE (the `Ran N tests ... OK` summary). Leak-clean; no em/en dashes.

## Spec / documentation sync

`GUIDING_PRINCIPLES.md` (P5), `DECISIONS.md` (pointer), `TODO.md` (future work), `.agents/docs/research/README.md` (regenerated), `AGENTS.md` (regenerated pointer). The spec itself is unchanged (this executes it).

## Open questions

### OQ-01: exact wording of the AGENTS.md pointer

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: RESOLVED at review (2026-08-07). The pointer is a SHORT new `###` section (a few sentences, consistent with the existing pointer sections, not literally one line) naming the `aw research`/`aw archive` verbs and "do not hand-name or hand-maintain the index"; detail stays in `--help` + the dir README (F6). The empty-diff-except-this-section invariant is what the validation enforces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: cite Orders 01/03/05 in `executed/` and confirm the research dir shape/INDEX/states are present.
  - Observed evidence: Orders 01, 03, 05 (and 02, 04, 06) are all executed in `.agents/plans/executed/`; their symbols (`research_contract`, `aw research index`, `aw archive`) are importable/invokable. The gate checks the SYMBOLS, not populated shard dirs (per the E-01 revision). `.agents/docs/research/INDEX.json`+`INDEX.md` exist (generated in Order 06) and the `reference/`/`archive/` shards exist (Order 06 sharded the archive drafts).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the scaffold test output (the `reference/`/`archive/` dirs + convention README created no-clobber; dry-run matches real; idempotent); confirm the created-count assertion was updated and real-vs-dry-run parity holds for the new artifacts.
  - Observed evidence: `tests/test_setup_artifacts.py` passes (`Ran 19 tests ... OK`): `create_setup_artifacts` now scaffolds `.agents/docs/research/reference/.gitkeep` + `.agents/docs/research/archive/.gitkeep` via the new `RESEARCH_SHARD_SUBDIRS`; the created-count assertion updated 22 -> 24 (both sites); new `test_dry_run_reports_research_shards_without_writing` asserts the dry-run reports them without writing (real/dry-run parity). The shipped README template `agents-docs-research-README.md` is updated to the new convention (no-clobber on install). NOTE: a bug I nearly introduced (prompts loop pointing at PLANS_DIR) was caught by these tests and fixed.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `git diff -- AGENTS.md` showing the diff limited to the new pointer section; confirm AGENT-PLANS is byte-identical.
  - Observed evidence: the AGENTS.md pointer's "Durable reference" section now names the `aw research`/`aw archive` verbs and "do not hand-name or hand-maintain the index" (edited in the generator `agents_pointer_prose()`, then AGENTS.md regenerated via the installer, commit `4fd2921`, a 2-line AGENTS.md change limited to the pointer line). The empty-diff invariant holds (AGENTS.md pointer body == `agents_managed_sections()` output). `AGENT-PLANS:BEGIN` block is present and untouched (byte-identical).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: quote the revised P5 bullet from `GUIDING_PRINCIPLES.md`; confirm specs remain path-stable but research is exempted and cited by `<id6>`; confirm the bullet was narrowed, not deleted.
  - Observed evidence: the P5 bullet now reads "Do not move artifacts that are cited by a stable PATH. Specs are referenced by path ... keep the spec path stable ... Research is the EXCEPTION: research is cited by its stable `<id6>` ... freely movable ... Use the `aw research` / `aw archive` verbs". Specs stay path-stable; research is exempted; the bullet was narrowed, not removed.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: confirm the DECISIONS entry (D123) exists, points to the spec, and lists the revised decisions INCLUDING D88.
  - Observed evidence: `DECISIONS.md` D123 "Research artifacts are organized by a machine-checkable convention" points to spec `20260730-2152-01-agents-artifact-organization.spec.md` and explicitly lists the revised decisions: the `YYYYMMDD-HHMM-NN` grouping theory (D48/D50/D55), GUIDING_PRINCIPLES P5's carve-out established by **D88** (named), and the founding free-form-research stance.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: confirm the TODO note names plans/executed/ with the measured rationale.
  - Observed evidence: `TODO.md` "Planned next" now leads with a note "Apply the research-organization convention to `plans/executed/` (the highest-value next adopter, D123)" citing the measured pain (about 85 plans/month, 179 files) and that the design generalizes (spec Section 7).
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste the full-suite `Ran N tests ... OK` summary; confirm leak-clean and no em/en dashes.
  - Observed evidence: full suite `python3 -m unittest discover -s tests -t .` -> `Ran 628 tests in 147.944s / OK (skipped=1)`. `aw sanitize --agent` exit 0 (leak-clean). No em/en dashes in the changed files (checked).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03, 05; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including the empty AGENTS.md diff and byte-identical AGENT-PLANS); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (scaffold/pointer/P5/DECISIONS/TODO only; edit only the existing `agents_pointer_prose`; regenerate AGENTS.md, do not hand-edit; do not add the separate aw:block edit-protection directive here). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
