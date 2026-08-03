# IPD: canonical IPD schema (single source of truth) (Set `ipd-structure`, Order 1)

- Date: 2026-08-02
- Kind: child
- Concern: define ONE machine-readable schema that owns the IPD structural contract (kinds, both enumerated H2 orders, optional-section intervals, metadata-block fields incl. `auto-approved` and the `Order: 0` orchestrator exception, `E-*`/`V-*` id grammar + the allocation watermark, execution/validation field grammar + state tables, lint checkpoints, size thresholds, quarantine + legacy applicability), so the linter, tools, templates, spec, and review workflows all derive from or are checked against it and cannot drift.
- Scope: the schema module + its own validation tests ONLY. No parser, no CLI, no template edits, no migration (those are Orders 02+). Requires the specification `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` (a gpt-5.6-revised DRAFT; maintainer approval of the spec is a prerequisite to executing this Set, spec Section 18).
- Status: to-review
- Set: ipd-structure
- Order: 1
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): first child of Set `ipd-structure`; establishes the single source of truth so Orders 02 to 06 reference one definition (spec Section 3, Section 8).
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-004 (E-01 now requires the schema to enumerate the orchestrator heading order, matching the 00 file). Bootstrap manual preflight. No BLOCKER/HIGH. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: schema now owns the metadata-block contract (incl. `auto-approved` and the `Order: 0` exception), the `E-*` allocation watermark (Section 5.6), and quarantine semantics (Section 13.3); renamed `## Findings (drivers)` to `## Findings`; enumerated orchestrator order updated to the checklist-after-Goal shape. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required and the revising agent does NOT self-approve.

## Goal

Produce the authoritative, importable IPD schema and prove it with tests. Nothing consumes it behaviorally yet; this child only DEFINES it. This is the anti-drift foundation the whole Set depends on.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: schema module

- [ ] E-01 add `agent_workflows/ipd_schema.py` defining IPD kinds (`child`, `orchestrator`) and, per kind, the ordered required H2 headings + named optional-section intervals.
  - Depends on: none
  - Expected outcome: importable constants; `child` order matches spec Section 4.3 (13 headings incl. `## Project conventions discovered (Step 0)`, `## Findings` bare, `## Deferred / out of scope (with reason)`), verified against the live template; the `orchestrator` order is enumerated completely (spec Section 4.3, 12 headings) with `## Detailed Implementation Checklist (TODO)` as the H2 IMMEDIATELY AFTER `## Goal` and `## Validation and cross-check (verify before reporting the Set complete)` immediately before the gate, matching `20260802-1944-00-ipd-structure-orchestrator.md`.
  - Execution state: pending
- [ ] E-02 define the metadata-block contract (spec Section 4.4) separately from the H2 contract: required fields (`Date`, `Kind`, `Concern`, `Scope`, `Status`, `Author`), conditional `Set`+`Order`, `Approval`, and `Quarantine`/`Quarantine owner`/`Quarantine follow-up`; recognized `Status` values incl. `auto-approved` (spec Section 9.1); the `Kind: orchestrator` -> `Order: 0` and `Kind: child` -> `Order >= 1` rule; duplicate-field and unknown-field behavior; permitted path/status/kind/order combinations.
  - Depends on: E-01
  - Expected outcome: a metadata-block field spec + validator entry point returning structured errors; recognizes `auto-approved`; rejects an orchestrator `Order != 0` and a child `Order < 1`; rejects a duplicate or unknown field.
  - Execution state: pending
- [ ] E-03 define the id grammar (`E-[0-9]{2,}`, `V-[0-9]{2,}`, IPD-scoped, monotonic/stable), the `\b` reference regex, AND the allocation-watermark rules (spec Section 5.6): the `- Highest E allocated: NN` field, next-suffix = watermark + 1, watermark never decreases, watermark >= largest present `E-*` suffix.
  - Depends on: none
  - Expected outcome: compiled regexes + helpers; matches an id in a filename and in prose; rejects malformed; a watermark helper computes the next suffix from the watermark (not from the max present id) and flags a watermark below a present id.
  - Execution state: pending

### Task group 2: state model + thresholds

- [ ] E-04 encode the execution state table (`pending|performed|blocked|failed` + checkbox agreement + `Execution note:` rules) and the validation state table (`pending|pass|blocked|failed` + checkbox + observed-evidence agreement) and the E/V cross-constraints, per spec Section 5.
  - Depends on: E-01
  - Expected outcome: a state-legality function usable by the linter, covering every legal/illegal combination.
  - Execution state: pending
- [ ] E-05 encode the lint checkpoints (`author|review-finalize|pre-execution|pre-transition|post-transition`), the size thresholds (>5 task groups, >18 E leaves) + `Size assessment` grammar, the open-question grammar (`OQ-*` fields), the legacy applicability rules, AND the quarantine semantics (spec Section 13.3): the `Quarantine`/`owner`/`follow-up` field trio, quarantine as a non-passing informational disposition distinct from `pass` and `legacy/not evaluated`, and that only nonterminal plans may be quarantined.
  - Depends on: E-01, E-04
  - Expected outcome: checkpoint-to-required-state mapping + threshold/question/legacy/quarantine constants, all from this one module.
  - Execution state: pending

### Task group 3: tests

- [ ] E-06 add `tests/test_ipd_schema.py` covering both heading orders, metadata-block validation (incl. `auto-approved`, the `Order: 0` orchestrator exception, duplicate/unknown field), id grammar + watermark rules (next-suffix from watermark, watermark-below-present-id error), both state tables (legal + illegal), thresholds, question grammar, quarantine fields, and legacy rules.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: table-driven tests; all pass.
  - Execution state: pending
- [ ] E-07 run `python -m pytest tests/test_ipd_schema.py -q` then the full suite; paste both.
  - Depends on: E-06
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec source: `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` Sections 3, 4.2-4.4, 5 (incl. 5.6 watermark), 6.2, 8, 9, 13 (incl. 13.3 quarantine).
- The live child template H2 order is at `.agents/workflows/assess/templates/ipd.md` (verified 2026-08-02 to include `## Project conventions discovered (Step 0)`, bare `## Findings`, `## Deferred / out of scope (with reason)`); re-confirm at execution before encoding. The orchestrator template currently places its execution checklist near the bottom; the schema encodes the CORRECTED order (checklist immediately after `## Goal`) which Order 04 applies to the template.
- Package layout: modules live in `agent_workflows/`; tests in `tests/` with table-driven style (see `tests/test_installer.py`).
- Maintainer scope caveat (spec header): the schema is a PROPORTIONATE single-source-of-truth (a constants/spec module + parity tests), NOT a heavyweight schema-engine; keep it light.
- House rule: no em/en dashes in authored Markdown.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C1-1 | HIGH | Low | architect | consistency | Without one schema, the linter/tools/templates/spec/review will fork the structural contract and drift (the exact parity risk the research named). | spec Section 3, Section 8 |
| C1-2 | MEDIUM | Low | implementer | correctness | Two independent linters would accept different documents without a complete state table. | spec Section 5, change-rationale Section 4 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C1-1 | schema module (kinds, both H2 orders, metadata block, ids + watermark) | `agent_workflows/ipd_schema.py` | Low | E-01..E-03 tests |
| 2 | C1-2 | state tables + checkpoints + thresholds + question/legacy/quarantine rules | `agent_workflows/ipd_schema.py` | Low | E-04, E-05 tests |
| 3 | C1-1 | tests | `tests/test_ipd_schema.py` | Low | E-06, E-07 |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | scope | Parser/linter/tools/templates consume this schema; not built here. | Orders 02 to 06 |

## Scope check

- Over-scope: none - a schema module + its tests.
- Under-scope: MUST define both H2 orders, the metadata block (incl. `auto-approved` and the `Order: 0` exception), id grammar + allocation watermark, both state tables, checkpoints, thresholds, question + quarantine + legacy rules as importable, tested primitives.

## Required tests / validation

`tests/test_ipd_schema.py` (E-06). Run `python -m pytest tests/test_ipd_schema.py -q` then `python -m pytest -q`; paste both. Leak-clean; no em/en dashes.

## Spec / documentation sync

None beyond code + tests in this child; the spec is the authority. Templates/`ipd-spec` are updated in Order 04 (from this schema).

## Open questions

### OQ-01: canonical-schema file path and format

- Blocking: no
- Status: deferred
- Owner: this child's discovery step
- Resolution or deferral rationale: whether the schema is a Python constants module vs a data file (JSON/TOML) + loader is chosen here after confirming repo conventions; the spec fixes the CONTENT, not the container. Lean: a Python module for 3.9-safety and zero new deps.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `ipd_schema.py` importable; test asserts `child` H2 order equals the live `ipd.md` order (incl. Step 0, bare `## Findings`) AND the `orchestrator` order has the execution checklist immediately after `## Goal`; paste the assertion output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: metadata-block validator rejects a missing `Kind:`/bad `Status:`, accepts `auto-approved`, rejects an orchestrator `Order != 0` and a child `Order < 1`, and rejects a duplicate/unknown field, each with a precise message; paste test output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: id regex matches `E-01`/`V-12` in a filename and in prose, rejects `E-1`/`X-01`; watermark helper returns next suffix = `Highest E allocated + 1` (not max present id) and flags a watermark below a present id; paste test output.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: state-legality function accepts every legal execution+validation combo and rejects each illegal one from spec Section 5; paste the table-test output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: checkpoint map, thresholds (>5 groups / >18 leaves), `OQ-*` grammar, legacy rules, and the quarantine field trio + non-passing-informational disposition present and tested; paste output.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: `tests/test_ipd_schema.py` exists and is table-driven; paste the collected test count.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `pytest tests/test_ipd_schema.py -q` result AND the full-suite summary line (new tests pass, suite green).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Bootstrap: this file is hand-authored to the new shape and reviewed with a manual preflight labeled "machine preflight unavailable: bootstrap" (spec Section 12), since `aw ipd lint` does not exist until Order 02. Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with nonempty observed evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (schema + its tests only; no parser/CLI/template/migration). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
