# IPD: review structural preflight + fail-closed enforcement (Set `ipd-structure`, Order 5)

- Date: 2026-08-02
- Kind: child
- Concern: make the linter authoritative: `plan-review`, `plan-review-long`, `review-rubric` MUST invoke `aw ipd lint` at their checkpoints (structural preflight before semantic review), and a NEW authoritative execution-and-transition workflow (`.agents/workflows/ipd-lifecycle/ipd-lifecycle.md`) MUST fail closed at `pre-execution`/`pre-transition`/`post-transition`, instead of repeating a prose rule; and add parity tests for embedded-vs-standalone rubric/report-template content. Repository fact (spec Section 12.1): no authoritative general execution/transition workflow exists today (`verify-execution` is POST-execution only), so this Order CREATES the missing path rather than editing a nonexistent file.
- Scope: review-workflow wiring + the NEW `ipd-lifecycle` workflow + parity tests. No new linter logic (Order 02). Requires Orders 01, 02, 04 executed (schema + linter + updated templates/spec); if absent, STOP.
- Status: to-review
- Set: ipd-structure
- Order: 5
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; closes the "reviewer approves a strong but misplaced checklist" gap by making enforcement mandatory and fail-closed.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no findings (deps 01,02,04 correct; invoke-not-paraphrase + fail-closed + parity coverage match spec Sections 11/12). Bootstrap manual preflight. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: the vague "execution/lifecycle workflow docs" is replaced with a NAMED, CREATED authoritative workflow `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` (+ `README.md`) that is the single entry point for beginning execution and performing the terminal transaction, with explicit `pre-execution`/`pre-transition`/`post-transition` checkpoints, fail-closed on exit 1 AND exit 2, and pre-/post-commit recovery (spec Section 12.1); the deterministic-vs-semantic boundary per checkpoint is made explicit (spec Section 10.1); renamed `## Findings (drivers)` to `## Findings`. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required; the revising agent does NOT self-approve.

## Goal

The authoritative workflows run the linter at their checkpoints and fail closed; a structural error is a distinct finding fixed before semantic review can pass; parity tests prevent embedded/standalone rubric+report-template drift. Spec Sections 11, 12.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: review-workflow preflight

- [ ] E-01 wire `plan-review.md` to run `aw ipd lint` (structural preflight) BEFORE semantic review, and again at `review-finalize` after edits; a structural error is a distinct finding that MUST be repaired before a passing verdict; replace any "apply the same checks" prose. State explicitly that a passing lint proves ONLY deterministic structure/state and that semantic adequacy (atomicity, observability, evidence sufficiency, truthful nonblocking) remains the reviewer's separate responsibility, and that `review-finalize` help text MUST NOT overclaim semantic certainty (spec Section 10.1).
  - Depends on: none
  - Expected outcome: plan-review instructs invoking the linter (not paraphrasing it); structural failure blocks a passing verdict; the deterministic-vs-semantic boundary is stated and not overclaimed.
  - Execution state: pending
- [ ] E-02 mirror the same preflight + finalize wiring into `plan-review-long/03-resolve-and-finalize.md` and `review-rubric.md`, preserving single-file/multi-file parity.
  - Depends on: E-01
  - Expected outcome: both variants invoke the linter at the same checkpoints; wording parity holds.
  - Execution state: pending

### Task group 2: lifecycle fail-closed

- [ ] E-03 CREATE the new authoritative execution-and-transition workflow `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` (+ sibling `README.md`) as the single entry point for beginning execution and performing the terminal transaction (spec Section 12.1; no such workflow exists today, `verify-execution` is POST-execution only). It MUST run `aw ipd lint --phase pre-execution FILE` at execution start (proceed only on exit 0) and `aw ipd lint --phase pre-transition FILE` before the Section 11 terminal transaction (proceed only on exit 0), then `--phase post-transition MOVED_FILE`; fail closed on BOTH exit 1 (conformance error, surfaced as a finding) and exit 2 (tool cannot run, a hard stop, never a skip); before the lifecycle commit a failure leaves the plan un-moved and recoverable; after the commit a failing `post-transition` is reported as incomplete finalization, never as success. The `machine preflight unavailable: bootstrap` label is the ONLY accepted exception and only during the bootstrap Set.
  - Depends on: E-01
  - Expected outcome: the new `ipd-lifecycle.md` exists and names the exact `pre-execution`/`pre-transition`/`post-transition` invocations, the exit-1 and exit-2 fail-closed rules, and the pre-/post-commit recovery behavior.
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

- Files: `.agents/workflows/plan-review/plan-review.md`, `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `.agents/workflows/plan-review-long/review-rubric.md` (edited), and the NEW `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` + `README.md` (created; `git add` first).
- Verified 2026-08-02: there is NO authoritative general execution/transition workflow in `.agents/workflows/`; `verify-execution` is POST-execution only. This Order creates the missing path (spec Section 12.1) rather than editing a nonexistent file.
- The two review variants are kept in deliberate parity (existing convention); wiring must preserve it.
- `report-template.md` is referenced by `03-resolve-and-finalize.md` and was missing from the audit; confirm its presence and cover it with the parity/dependency check.
- Enforcement is mandatory (spec Section 12): workflows INVOKE the linter; they do not restate its checks.
- No em/en dashes in authored Markdown.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C5-1 | HIGH | Low | reviewer | integrity | Review repeats a qualitative rule instead of a structural preflight, so a misplaced checklist can be approved. | research F-10 |
| C5-2 | MEDIUM | Low | maintainer | drift | Embedded vs standalone rubric/report-template copies can drift without a parity control. | research F-11 |
| C5-3 | HIGH | Medium | automation | integrity | No authoritative general execution/transition workflow exists (`verify-execution` is post-execution only), so the fail-closed `pre-execution`/`pre-transition` gates have nowhere to live; the path must be CREATED. | spec Section 12.1 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C5-1 | preflight + finalize wiring (single-file) | `.agents/workflows/plan-review/plan-review.md` | Low | E-01 |
| 2 | C5-1 | parity wiring (multi-file) | `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `review-rubric.md` | Low | E-02 |
| 3 | C5-1, C5-3 | CREATE the authoritative `ipd-lifecycle` workflow with fail-closed gates | `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md`, `.agents/workflows/ipd-lifecycle/README.md` | Medium | E-03 |
| 4 | C5-2 | parity tests | `tests/` | Low | E-04 |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | usability | Pre-commit/CI hook wiring is defense in depth, deferred to a follow-up. | Post-Set follow-up |
| n/a | n/a | scope | Migrating existing nonterminal plans is Order 06. | Order 06 |

## Scope check

- Over-scope: none - review-workflow wiring + creating the one missing `ipd-lifecycle` workflow + parity tests.
- Under-scope: MUST make the linter invoked (not paraphrased) at every authoritative checkpoint, CREATE the authoritative `ipd-lifecycle` execution/transition workflow, fail closed on exit 1 and exit 2, and prevent rubric/report-template drift.

## Required tests / validation

Parity tests (E-04) + suite. Run `python -m pytest -q`; paste. Grep the review workflows to confirm they INVOKE `aw ipd lint` and no longer say "apply the same checks". Leak-clean; no em/en dashes.

## Spec / documentation sync

The review workflow docs are updated and the NEW `ipd-lifecycle` workflow is created here. DECISIONS/AGENTS pointer in Order 06.

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
  - Required evidence: confirm `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` was created (`git add`ed); quote its `pre-execution`/`pre-transition`/`post-transition` invocations, the exit-1 AND exit-2 fail-closed rules, the pre-/post-commit recovery behavior, and the bootstrap-only exception.
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

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` the new `ipd-lifecycle` files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (review-workflow wiring + creating the `ipd-lifecycle` workflow + parity tests; no linter logic changes, no plan migration). Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
