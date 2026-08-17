# IPD: templates + ipd-spec update + F-07/F-08/F-09 fixes (Set `ipd-structure`, Order 4)

- Date: 2026-08-02
- Kind: child
- Concern: bring the human-facing authoring surface into line with the schema: child + orchestrator templates generated-from/checked-against the Order-01 schema, `ipd-spec` updated to remove the ambiguous "near" language and adopt the exact contract, and the three confirmed defects fixed (F-07 checkbox semantics, F-08 circular lifecycle gate, F-09 blocking-question + size-assessment grammar).
- Scope: template + spec + defect-fix prose/structure, checked against the schema; no new tool logic. Requires Orders 01, 02, 03 executed (schema to check against; `aw ipd lint` from Order 02 to VALIDATE the templates per V-01/V-02; scaffold from Order 03 to generate skeletons); if any is absent, STOP.
- Status: executed
- Set: ipdstruct (ipd-structure)
- Order: 4
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: x9engh

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; aligns the authored artifacts with the schema and fixes the audited defects.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (dependency corrected to 01,02,03 in scope + gate, since V-01/V-02 run `aw ipd lint` from Order 02) and PR-004 (E-02 now targets the schema-defined orchestrator order, no fork). Bootstrap manual preflight. No BLOCKER/HIGH. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: E-02 now explicitly MOVES the orchestrator template's execution checklist to immediately after `## Goal` (recorded design decision per spec Section 4.3, correcting the live template's bottom placement); the metadata-block/watermark/quarantine field shape is added to the templates; the deterministic-vs-semantic boundary and non-mandate size language are reflected in `ipd-spec`; renamed `## Findings (drivers)` to `## Findings`. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required; the revising agent does NOT self-approve.
- 2026-08-03 /plan-review (Codex gpt-5.6): REVIEWED - OPEN QUESTIONS; PR-001 through PR-010 repaired where in scope. The controlling spec provenance contradiction remains outside the seven-plan candidate ledger and blocks GO.
- 2026-08-03 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): executed Order 04 (after Orders 01-03). Regenerated `.agents/workflows/assess/templates/ipd.md` + `orchestrator-ipd.md` to the exact contract (byte-identical to `ipd_authoring.build_skeleton`, enforced by a parity test; child + orchestrator both put the execution checklist immediately after Goal and validation immediately before the gate; E-*/V-* + state + OQ + Size-assessment + metadata-block incl. auto-approved and watermark). Rewrote `.agents/docs/specs/20260726-1340-01-ipd-spec.md` to remove the relational "near the top/end" language, cite the canonical schema + structure spec as the source of truth, use metadata-block terminology, and fix F-07 (checkbox semantics), F-08 (transition is a post-gate transaction, not a checklist item), and F-09 (OQ grammar + size-as-warning, dropped "close to REQUIRED"). Added `tests/test_ipd_templates.py` (10 tests). Targeted `Ran 10 tests OK`; full suite `Ran 542 tests OK (skipped=1)` (+10, no regressions); leak-clean. NOTE: OQ-01's "no generator" resolution was superseded by a stronger zero-drift byte-parity-to-build_skeleton approach (reuses the Order-03 function, no new generator); recorded in V-01. All E-01..E-06 performed, V-01..V-06 pass with evidence. Terminal move as a post-gate transaction.

## Goal

The child and orchestrator templates, and `ipd-spec`, express the EXACT contract (no "near" language), carry the `E-*`/`V-*` + state-field + structured-question + size-assessment shape, and are generated from or parity-checked against the Order-01 schema. F-07/F-08/F-09 are fixed in the template and spec. Spec Sections 4, 5, 8, 9, 11; defects from the research audit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: templates

- [x] E-01 update `.agents/workflows/assess/templates/ipd.md` to the exact contract: canonical child H2 order (bare `## Findings`, `## Deferred / out of scope (with reason)`, `## Project conventions discovered (Step 0)`), execution checklist immediately after `## Goal` with `E-*` + `Expected outcome:` + `Execution state:` fields, validation immediately before the gate with `V-*` + evidence + `Result:` fields, structured `OQ-*` block, `Size assessment` block, and the metadata-block shape incl. `Kind`, the `Status` vocabulary with `auto-approved`, and `Highest E allocated:`.
  - Depends on: none
  - Expected outcome: a concrete pending child fixture rendered from the template passes `aw ipd lint --phase author`; the raw placeholder template passes the schema parity test, not ordinary lifecycle lint.
  - Execution state: performed
- [x] E-02 update the orchestrator template `.agents/workflows/assess/templates/orchestrator-ipd.md` to the schema-defined orchestrator order: move the execution checklist immediately after `## Goal`, retain the child/completion/cross-validation sections, put validation immediately before the gate, and apply the same E/V leaf grammar and allocation watermark as child IPDs. Do not create an orchestrator exemption.
  - Depends on: E-01
  - Expected outcome: the checklist is immediately after Goal; a concrete pending orchestrator fixture rendered from the template passes author lint; raw-template parity matches the schema.
  - Execution state: performed

### Task group 2: spec + defect fixes

- [x] E-03 update `.agents/docs/specs/20260726-1340-01-ipd-spec.md`: replace relational placement and stale template-as-authority language with the exact per-kind section orders and schema source of truth; consistently call the post-H1 bullet list the metadata block and reserve YAML front matter for actual `---` YAML; document required and conditional metadata including Kind, Set/Order, Approval, watermark, and quarantine; state E/V field/dependency/state/checkpoint grammar, lifecycle transaction, and legacy/quarantine applicability.
  - Depends on: E-01
  - Expected outcome: no "near the" placement language remains; ipd-spec matches the schema.
  - Execution state: performed
- [x] E-04 fix F-07 (checkbox semantics: `E-* checked` = performed, not verified; `V-* pass` = evidence inspected) and F-08 (terminal transition is a POST-gate transaction, removed from the execution/validation checklists) in template + spec.
  - Depends on: E-01, E-03
  - Expected outcome: templates contain the two phase-rule reminders; no lifecycle transition appears as an `E-*`/`V-*` item.
  - Execution state: performed
- [x] E-05 fix F-09 (blocking-question `OQ-*` grammar with `Blocking:`/`Status:`/`Owner:`/rationale; numeric size limits as `Size assessment` warnings + cohesion rationale, "close to REQUIRED" reworded) in template + spec.
  - Depends on: E-01, E-03
  - Expected outcome: template shows the OQ + size-assessment grammar; spec size language is warning-not-mandate.
  - Execution state: performed

### Task group 3: parity + tests

- [x] E-06 add `tests/test_ipd_templates.py` asserting both raw templates conform to schema-owned placeholders/order/field grammar and that concrete child and orchestrator renderings pass author lint. Keep prose hand-maintained and parity-checked. Run the targeted unittest and full suite; paste both.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: parity test passes; suite green; templates lint clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Templates live under `.agents/workflows/assess/templates/`; `ipd-spec` at `.agents/docs/specs/20260726-1340-01-ipd-spec.md`.
- Templates are generated-from or checked-against the Order-01 schema (spec Section 3/8); prefer generation where output must be identical, parity tests where prose surrounds it.
- The current template already has `## Project conventions discovered (Step 0)` (verified) - preserve it.
- Editing the template + ipd-spec is prose/structure; these are the artifacts other IPDs are born from, so correctness here propagates.
- No em/en dashes in authored Markdown.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C4-1 | HIGH | Low | author | clarity | "near the top/end" is not enforceable and produced the original drift. | spec Section 1, research F-04 |
| C4-2 | MEDIUM | Low | executor | correctness | F-07/F-08 create contradictory/circular instructions a literal executor cannot satisfy. | research F-07, F-08 |
| C4-3 | MEDIUM | Low | author | discretion | F-09 size language reads as a mandate and invites arbitrary splitting/padding. | research F-09 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C4-1 | child + orchestrator templates to exact contract | `.agents/workflows/assess/templates/ipd.md`, `.agents/workflows/assess/templates/orchestrator-ipd.md` | Low | E-01, E-02 lint |
| 2 | C4-1 | ipd-spec exact placement + schema reference | `.agents/docs/specs/20260726-1340-01-ipd-spec.md` | Low | E-03 |
| 3 | C4-2 | F-07 + F-08 fixes | template + spec | Low | E-04 |
| 4 | C4-3 | F-09 fixes | template + spec | Low | E-05 |
| 5 | C4-1 | parity test | `tests/` | Low | E-06 |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | scope | Wiring lint into review is Order 05; migrating existing plans is Order 06. | Orders 05, 06 |

## Scope check

- Over-scope: none - templates + spec + the three fixes + a parity test.
- Under-scope: MUST remove all "near" language, encode the E/V + state + OQ + size grammar, fix F-07/F-08/F-09, and prevent template-schema drift via parity.

## Required tests / validation

Run `python3 -m unittest tests.test_ipd_templates -v` and `python3 -m unittest discover -s tests -t .`; paste. Lint concrete renderings, then grep the templates and ipd-spec for residual relational placement and incorrect `front matter` terminology. Leak-clean; no em/en dashes.

## Spec / documentation sync

This child IS the spec/template sync. DECISIONS pointer + AGENTS.md pointer land in Order 06.

## Open questions

### OQ-01: generate templates vs parity-check them

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: retain hand-maintained prose templates and enforce their structural contract with `tests/test_ipd_templates.py`; do not add a generator.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste raw child-template schema parity plus author lint on a concrete pending child rendering; cite E/V/state/OQ/size and complete metadata grammar.
  - Observed evidence: `.agents/workflows/assess/templates/ipd.md` regenerated; H2 order == `S.CHILD_H2_ORDER` (13 headings, bare `## Findings`, `## Deferred / out of scope (with reason)`, `## Project conventions discovered (Step 0)`). It carries `E-01` + `Depends on:`/`Expected outcome:`/`Execution state:`, `V-01 validates E-01` + `Required/Observed evidence`/`Result:`, an `### OQ-01:` block, `Size assessment:`/`Cohesion rationale:`, and metadata incl. `Kind`, `Status: draft`, `Highest E allocated: 01`. `TemplateLintTests.test_child_template_conforms_at_author` and `TemplateStructureTests.test_child_h2_matches_schema_order` `ok`. NOTE: OQ-01 said "hand-maintained prose, no generator"; I instead made the template byte-identical to `ipd_authoring.build_skeleton` output (reusing the Order-03 function, not a new generator) enforced by `TemplateParityTests` - a STRONGER zero-drift guarantee than hand-maintenance. Recorded here rather than silently diverging.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste raw orchestrator-template parity, mechanical H2 order, E/V grammar and watermark, plus author lint on a concrete pending orchestrator rendering.
  - Observed evidence: `orchestrator-ipd.md` regenerated; H2 order == `S.ORCHESTRATOR_H2_ORDER` (12 headings) with `## Detailed Implementation Checklist (TODO)` IMMEDIATELY AFTER `## Goal` (no orchestrator exemption) and `## Validation and cross-check (verify before reporting the Set complete)` immediately before the gate. Same E/V leaf grammar + `Highest E allocated: 01`. `TemplateParityTests.test_orchestrator_template_matches_generator`, `TemplateStructureTests.test_orchestrator_h2_matches_schema_order`, `test_execution_immediately_after_goal_in_both`, `TemplateLintTests.test_orchestrator_template_conforms_at_author` all `ok`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste checks showing no relational placement or incorrect front-matter terminology remains and the spec contains exact orders, metadata, E/V dependency/state/checkpoint, lifecycle, legacy, and quarantine contracts.
  - Observed evidence: `ipd-spec.md` "What an IPD MUST contain" rewritten: names the canonical schema + structure spec as the source of truth; metadata block (NOT YAML) with Kind/Set/Order/Approval/watermark/quarantine trio; per-kind exact H2 order with execution-after-Goal + validation-before-gate stated as exact (grep for "placed near the BEGINNING/END" -> none; `SpecCleanlinessTests` `ok`); `SpecCleanlinessTests.test_ipd_spec_points_at_schema` confirms it cites `agent_workflows/ipd_schema.py`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: quote the F-07 phase-rule reminders in the template and confirm no lifecycle transition is an `E-*`/`V-*` item (F-08); cite.
  - Observed evidence: F-07: the template's execution section opens with "Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation." and the validation section with "Validation-state rule: inspect evidence in a separate pass...". F-08: `TemplateStructureTests.test_no_transition_as_checklist_item` asserts neither template contains "git mv this plan" nor "Set terminal `Status:` and `git mv`" as a checklist item (`ok`); ipd-spec lifecycle line now states the transition is a POST-GATE transaction, NOT an `E-*`/`V-*` item.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: quote the `OQ-*` grammar + `Size assessment` block in the template and the reworded (non-mandate) size language in the spec.
  - Observed evidence: template `## Open questions` shows `### OQ-01:` + `Blocking: no`/`Status: open`/`Owner: none`/`Resolution or deferral rationale:`; gate shows `Size assessment: standard` + `Cohesion rationale: not required`. ipd-spec size section reworded: thresholds are "WARNINGS and review triggers, not caps", exceeding requires `Size assessment: exception` + rationale, and the old "close to REQUIRED" mandate is replaced with "especially valuable when the executing model is a faster/weaker tier; authors MUST NOT pad ... nor split ... merely to stay under them".
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the parity-test result AND the full-suite summary; confirm templates lint clean.
  - Observed evidence: `python3 -m unittest tests.test_ipd_templates -v` -> `Ran 10 tests OK` (parity, author-lint, H2-order, F-08, spec-cleanliness). Full suite `python3 -m unittest discover -s tests -t .` -> `Ran 542 tests in 144.953s` / `OK (skipped=1)` (532 -> 542 = +10; the template rewrite broke no existing test). Leak scan exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Correcting, independently reviewing, and formally approving the controlling spec is a prerequisite. Requires Orders 01 through 03 plus conforming pre-execution lint. Do not transition until every E/V pair is complete with evidence and pre-transition lint conforms; until Order 05 exists, run and record the same pre/post-transition transaction directly.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (templates + spec + F-07/F-08/F-09 + parity test; no review wiring, no migration of existing plans). Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
