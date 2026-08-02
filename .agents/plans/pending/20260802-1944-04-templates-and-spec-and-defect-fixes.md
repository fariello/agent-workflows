# IPD: templates + ipd-spec update + F-07/F-08/F-09 fixes (Set `ipd-structure`, Order 4)

- Date: 2026-08-02
- Kind: child
- Concern: bring the human-facing authoring surface into line with the schema: child + orchestrator templates generated-from/checked-against the Order-01 schema, `ipd-spec` updated to remove the ambiguous "near" language and adopt the exact contract, and the three confirmed defects fixed (F-07 checkbox semantics, F-08 circular lifecycle gate, F-09 blocking-question + size-assessment grammar).
- Scope: template + spec + defect-fix prose/structure, checked against the schema; no new tool logic. Requires Orders 01, 03 executed (schema + scaffold to generate/validate templates); if absent, STOP.
- Status: to-review
- Set: ipd-structure
- Order: 4
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; aligns the authored artifacts with the schema and fixes the audited defects.

## Goal

The child and orchestrator templates, and `ipd-spec`, express the EXACT contract (no "near" language), carry the `E-*`/`V-*` + state-field + structured-question + size-assessment shape, and are generated from or parity-checked against the Order-01 schema. F-07/F-08/F-09 are fixed in the template and spec. Spec Sections 4, 5, 8, 9, 11; defects from the research audit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: templates

- [ ] E-01 update `.agents/workflows/assess/templates/ipd.md` to the exact contract: canonical H2 order, execution checklist immediately after `## Goal` with `E-*` + `Expected outcome:` + `Execution state:` fields, validation immediately before the gate with `V-*` + evidence + `Result:` fields, structured `OQ-*` block, `Size assessment` block.
  - Depends on: none
  - Expected outcome: the template passes `aw ipd lint --phase author` and is parity-checked against the schema.
  - Execution state: pending
- [ ] E-02 update the orchestrator template `.agents/workflows/assess/templates/orchestrator-ipd.md` to its schema-defined canonical order and the same field grammar (gate items carry no `E-*` ids).
  - Depends on: E-01
  - Expected outcome: the orchestrator template passes `aw ipd lint` for kind `orchestrator`.
  - Execution state: pending

### Task group 2: spec + defect fixes

- [ ] E-03 update `.agents/docs/specs/20260726-1340-01-ipd-spec.md`: replace "near the top/beginning/end" with the exact placement + section-order contract; reference the schema as the source of truth; state the `E-*`/`V-*` bijection.
  - Depends on: E-01
  - Expected outcome: no "near the" placement language remains; ipd-spec matches the schema.
  - Execution state: pending
- [ ] E-04 fix F-07 (checkbox semantics: `E-* checked` = performed, not verified; `V-* pass` = evidence inspected) and F-08 (terminal transition is a POST-gate transaction, removed from the execution/validation checklists) in template + spec.
  - Depends on: E-01, E-03
  - Expected outcome: templates contain the two phase-rule reminders; no lifecycle transition appears as an `E-*`/`V-*` item.
  - Execution state: pending
- [ ] E-05 fix F-09 (blocking-question `OQ-*` grammar with `Blocking:`/`Status:`/`Owner:`/rationale; numeric size limits as `Size assessment` warnings + cohesion rationale, "close to REQUIRED" reworded) in template + spec.
  - Depends on: E-01, E-03
  - Expected outcome: template shows the OQ + size-assessment grammar; spec size language is warning-not-mandate.
  - Execution state: pending

### Task group 3: parity + tests

- [ ] E-06 add a parity test asserting the templates conform to the schema (generated-from or checked-against) so they cannot drift; run it + the full suite; paste both.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: parity test passes; suite green; templates lint clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Templates live under `.agents/workflows/assess/templates/`; `ipd-spec` at `.agents/docs/specs/20260726-1340-01-ipd-spec.md`.
- Templates are generated-from or checked-against the Order-01 schema (spec Section 3/8); prefer generation where output must be identical, parity tests where prose surrounds it.
- The current template already has `## Project conventions discovered (Step 0)` (verified) - preserve it.
- Editing the template + ipd-spec is prose/structure; these are the artifacts other IPDs are born from, so correctness here propagates.
- No em/en dashes in authored Markdown.

## Findings (drivers)

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

The parity test (E-06) + templates passing `aw ipd lint`. Run `python -m pytest -q`; paste. Grep the template + ipd-spec for residual "near the" placement language (must be none). Leak-clean; no em/en dashes.

## Spec / documentation sync

This child IS the spec/template sync. DECISIONS pointer + AGENTS.md pointer land in Order 06.

## Open questions

### OQ-01: generate templates vs parity-check them

- Blocking: no
- Status: deferred
- Owner: this child
- Resolution or deferral rationale: whether the templates are emitted by a generator from the schema or hand-maintained + parity-tested is decided here; either satisfies single-source-of-truth. Lean: parity-check (templates carry prose a pure generator would fight).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw ipd lint --phase author` on the child template = exit 0; cite the E-*/state/OQ/size blocks present.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd lint` on the orchestrator template (kind orchestrator) = exit 0.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a grep of ipd-spec showing NO "near the" placement language and the exact-order contract present.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: quote the F-07 phase-rule reminders in the template and confirm no lifecycle transition is an `E-*`/`V-*` item (F-08); cite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: quote the `OQ-*` grammar + `Size assessment` block in the template and the reworded (non-mandate) size language in the spec.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the parity-test result AND the full-suite summary; confirm templates lint clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Requires Orders 01, 03; if absent, STOP. After Order 02, this file SHOULD be linted with the real `aw ipd lint`. Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with nonempty observed evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (templates + spec + F-07/F-08/F-09 + parity test; no review wiring, no migration of existing plans). Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
