# IPD: review structural preflight + fail-closed enforcement (Set `ipd-structure`, Order 5)

- Date: 2026-08-02
- Kind: child
- Concern: make the linter authoritative: `plan-review`, `plan-review-long`, `review-rubric`, and the execution/lifecycle workflows MUST invoke `aw ipd lint` at their checkpoints (structural preflight before semantic review; fail closed at execution and transition), instead of repeating a prose rule; and add parity tests for embedded-vs-standalone rubric/report-template content.
- Scope: review + lifecycle workflow wiring + parity tests. No new linter logic (Order 02). Requires Orders 01, 02, 04 executed (schema + linter + updated templates/spec); if absent, STOP.
- Status: to-review
- Set: ipd-structure
- Order: 5
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; closes the "reviewer approves a strong but misplaced checklist" gap by making enforcement mandatory and fail-closed.

## Goal

The authoritative workflows run the linter at their checkpoints and fail closed; a structural error is a distinct finding fixed before semantic review can pass; parity tests prevent embedded/standalone rubric+report-template drift. Spec Sections 11, 12.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: review-workflow preflight

- [ ] E-01 wire `plan-review.md` to run `aw ipd lint` (structural preflight) BEFORE semantic review, and again at `review-finalize` after edits; a structural error is a distinct finding that MUST be repaired before a passing verdict; replace any "apply the same checks" prose.
  - Depends on: none
  - Expected outcome: plan-review instructs invoking the linter (not paraphrasing it); structural failure blocks a passing verdict.
  - Execution state: pending
- [ ] E-02 mirror the same preflight + finalize wiring into `plan-review-long/03-resolve-and-finalize.md` and `review-rubric.md`, preserving single-file/multi-file parity.
  - Depends on: E-01
  - Expected outcome: both variants invoke the linter at the same checkpoints; wording parity holds.
  - Execution state: pending

### Task group 2: lifecycle fail-closed

- [ ] E-03 wire the execution/lifecycle workflow so execution fails closed if `pre-execution` lint cannot run or returns nonzero, and terminal transition fails closed on `pre-transition`, with `post-transition` verifying the completed transaction (transition performed as the post-gate transaction from Order 04).
  - Depends on: E-01
  - Expected outcome: documented fail-closed gates; a `machine preflight unavailable: bootstrap` label is the ONLY accepted exception and only during the bootstrap Set.
  - Execution state: pending

### Task group 3: parity tests

- [ ] E-04 add parity tests for any embedded-vs-standalone rubric/report-template content (single-file `plan-review` vs `plan-review-long` files), failing explicitly if a required dependency (e.g. `report-template.md`) is missing.
  - Depends on: none
  - Expected outcome: parity test passes; a deliberately-desynced fixture fails.
  - Execution state: pending
- [ ] E-05 run `python -m pytest -q` (incl. the new parity tests); paste.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Files: `.agents/workflows/plan-review/plan-review.md`, `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `.agents/workflows/plan-review-long/review-rubric.md`, and the execution/lifecycle workflow docs.
- The two review variants are kept in deliberate parity (existing convention); wiring must preserve it.
- `report-template.md` is referenced by `03-resolve-and-finalize.md` and was missing from the audit; confirm its presence and cover it with the parity/dependency check.
- Enforcement is mandatory (spec Section 12): workflows INVOKE the linter; they do not restate its checks.
- No em/en dashes in authored Markdown.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C5-1 | HIGH | Low | reviewer | integrity | Review repeats a qualitative rule instead of a structural preflight, so a misplaced checklist can be approved. | research F-10 |
| C5-2 | MEDIUM | Low | maintainer | drift | Embedded vs standalone rubric/report-template copies can drift without a parity control. | research F-11 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C5-1 | preflight + finalize wiring (single-file) | `.agents/workflows/plan-review/plan-review.md` | Low | E-01 |
| 2 | C5-1 | parity wiring (multi-file) | `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `review-rubric.md` | Low | E-02 |
| 3 | C5-1 | lifecycle fail-closed gates | execution/lifecycle workflow docs | Low | E-03 |
| 4 | C5-2 | parity tests | `tests/` | Low | E-04 |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | usability | Pre-commit/CI hook wiring is defense in depth, deferred to a follow-up. | Post-Set follow-up |
| n/a | n/a | scope | Migrating existing nonterminal plans is Order 06. | Order 06 |

## Scope check

- Over-scope: none - workflow wiring + parity tests.
- Under-scope: MUST make the linter invoked (not paraphrased) at every authoritative checkpoint, fail closed, and prevent rubric/report-template drift.

## Required tests / validation

Parity tests (E-04) + suite. Run `python -m pytest -q`; paste. Grep the review workflows to confirm they INVOKE `aw ipd lint` and no longer say "apply the same checks". Leak-clean; no em/en dashes.

## Spec / documentation sync

The review + lifecycle workflow docs are updated here. DECISIONS/AGENTS pointer in Order 06.

## Open questions

### OQ-01: bootstrap-exception wording

- Blocking: no
- Status: deferred
- Owner: this child
- Resolution or deferral rationale: the exact `machine preflight unavailable: bootstrap` label + where it is recorded in the review record is finalized here; it must end when the tool exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: quote the `plan-review.md` preflight + finalize wiring; paste a grep showing no "apply the same checks" prose remains.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: quote the matching wiring in `03-resolve-and-finalize.md` + `review-rubric.md`; confirm parity with the single-file variant.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: quote the fail-closed `pre-execution`/`pre-transition`/`post-transition` gates and the bootstrap-only exception in the lifecycle workflow.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the parity test passing on current files AND failing on a deliberately-desynced fixture; confirm missing-`report-template.md` fails explicitly.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full-suite summary (incl. parity tests), suite green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Requires Orders 01, 02, 04; if absent, STOP. This file SHOULD be linted with the real `aw ipd lint` (available after Order 02). Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with nonempty observed evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (review + lifecycle wiring + parity tests; no linter logic changes, no plan migration). Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
