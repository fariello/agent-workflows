# IPD: plan-review requires the creator to author both checklists and the reviewer to assess both

- Date: 2026-07-27
- Concern: honest reporting - the two-checklist convention only bites if plan-review enforces it: the creator must author both checklists, and the reviewer must assess both and confirm each execution item has a concrete end cross-check
- Scope: edit `plan-review` (and `plan-review-long` for parity) so its finalize step + rubric require the dual-checklist convention (from child 01) on any agent-executable plan, and add a reviewer duty to flag unsupported completion. Prose-only workflow edits + DECISIONS/CHANGELOG.
- Status: executed
- Set: ipd-dual-checklist-convention
- Order: 2
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-27, human ("All approved.") after /plan-review (APPROVE / APPROVE WITH REVISIONS APPLIED). Executing per the 00 orchestrator.

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): child 02 of the `ipd-dual-checklist-convention` Set (see the `-00-` orchestrator). Depends on child 01 defining the two-checklist structure in the template. Verified today that plan-review has NO checklist-assessment duty (grep for "checklist" in plan-review.md returned nothing).

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001. Verified plan-review has no checklist duty today and that plan-review-long uses a SEPARATE review-rubric.md with PROSE executability (no lettered section); fixed Step 2/3 + checklist/validation to reference the executability item generically (not a 'section G' in the long variant) and to target review-rubric.md. Depends on 01. <=5 steps. Readiness: GO - PENDING HUMAN APPROVAL.

- 2026-07-27 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): added the creator-authors-both + reviewer-assesses-both duty to plan-review Step 4 + rubric G, and to plan-review-long 03-resolve-and-finalize.md + review-rubric.md (parity; prose rubric, not a 'section G'). Added DECISIONS D115 + CHANGELOG. Verified both variants carry the duty; leak-clean; no em/en dashes; full suite 440 passed, 1 skipped. Path-scoped commit ac2f37e. Status: approved -> executed; moved to executed/.
## Goal

Make `/plan-review` (and its parity sibling `/plan-review-long`) enforce the dual-checklist convention: (1) the CREATOR of an agent-executable plan MUST include both a top execution checklist and an end verification/cross-check checklist (per child 01); (2) the REVIEWER MUST assess both - confirm the execution checklist covers every required action/decision/deliverable/validation, confirm the end checklist maps 1:1 and demands concrete evidence, and treat a plan that lacks either, or whose end checklist is too weak to catch a false "done", as a finding to fix in place. Add a reviewer duty at the finalize gate: do not pass a plan whose checklists could let an agent claim completion without having completed and verified every step.

Why it matters: child 01 puts the checklists in the template, but nothing makes a reviewer CHECK them; without that, the convention degrades to optional. The reviewer is the human-facing guardrail against unsupported completion, so the duty belongs in plan-review's finalize confirm-list and rubric.

## Project conventions discovered (Step 0)

- plan-review Step 4 "Finalize state and commit" has a confirm-list (findings resolved, deferrals meet the bar, gate carries the execution contract, etc.) - the natural home for a "both checklists present + adequate" confirmation. `.agents/workflows/plan-review/plan-review.md` Step 4.
- The engineering rubric (section G, Plan executability) is where a "must carry the two checklists" item fits.
- `plan-review-long` shares the finalize/rubric convention by deliberate parity (workflow header), and has its own `03-resolve-and-finalize.md` + rubric; the duty must land in both.
- Child 01 defines the exact structure the reviewer assesses; this IPD references it, does not redefine it.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| M1 | HIGH | Low | reviewer / stakeholder | enforcement gap | plan-review has no duty to check that an agent-executable plan carries the checklists or that the end checklist is strong enough to catch a false completion claim; the convention is unenforced. | grep "checklist" in `plan-review.md` = none |
| M2 | MEDIUM | Low | creator | creator duty | Nothing states the CREATOR must author both checklists; the template offers them but plan-review does not require them for a plan it passes. | `plan-review.md` Step 4 confirm-list (no checklist item) |
| M3 | LOW | Low | maintainer | parity | The duty must land in BOTH variants (deliberate parity), including the long variant's rubric/finalize. | `plan-review-long/03-resolve-and-finalize.md`; long rubric |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | M1,M2 | plan-review Step 4 "Finalize state and commit": add a confirm item - for an agent-EXECUTABLE plan (an IPD or similar), CONFIRM it carries a top execution checklist AND an end verification/cross-check checklist (per the IPD template / ipd-spec), that the end checklist maps 1:1 to the execution items and demands concrete per-item evidence, and that it is specific enough to catch an agent claiming completion without doing every step. If missing/weak, ADD or strengthen it in place (a finding), like the existing execution-contract gate rule. | `.agents/workflows/plan-review/plan-review.md` | Low | Step 4 confirm-list includes the dual-checklist requirement + the reviewer-strengthens-in-place rule |
| 2 | M1 | plan-review executability rubric item (section `### G. Plan executability`, `plan-review.md:338`): add a bullet - an agent-executable plan MUST carry the two checklists (execution + verification cross-check), the verification checklist mapping 1:1 with concrete evidence per item; a weak or absent verification checklist is an UNDER-SCOPE finding. | `.agents/workflows/plan-review/plan-review.md` (rubric G) | Low | the executability rubric item names the two-checklist requirement as verifiable |
| 3 | M3 | Apply the same to `plan-review-long` for parity: its finalize step (`03-resolve-and-finalize.md`) confirm-list + its SEPARATE rubric file (`review-rubric.md`) get the identical creator/reviewer dual-checklist duty, added to whatever form each expresses executability (the long rubric uses PROSE, not lettered sections - do not assume a "section G" there). Keep the two variants in deliberate parity of REQUIREMENT even where their rubric formatting differs. | `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `.agents/workflows/plan-review-long/review-rubric.md` | Low | both variants carry the duty in their own rubric form; no divergence of requirement |
| 4 | all | Docs/decision sync: DECISIONS entry (pin at execution) for the plan-review creator/reviewer dual-checklist duty (creator authors both; reviewer assesses both + confirms per-item cross-checks + flags unsupported completion; both variants), noting it depends on child 01; CHANGELOG. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Defining the checklist STRUCTURE itself | scope | Child 01 owns the template structure; this IPD references it. | Child 01. |
| ipd-spec.md update + orchestrator template | scope | Child 03. | Child 03. |
| A linter enforcing checklist presence | complexity | Reviewer duty is the enforcement; a lint is separable. | Later IPD if wanted. |

## Scope check

- Over-scope: none - edits to the two plan-review variants' finalize + rubric + a docs note. No template redefinition (01), no spec/orchestrator (03), no product code.
- Under-scope: MUST require the CREATOR to author both checklists and the REVIEWER to assess both + confirm 1:1 concrete-evidence cross-checks + flag unsupported completion (M1/M2); MUST land in BOTH variants for parity (M3); MUST reference child 01's structure rather than redefine it; MUST let the reviewer strengthen a weak checklist in place (a finding), consistent with the existing gate rule.

## Required tests / validation

- Prose only; no pytest delta. Validate by review + consistency: both plan-review variants' finalize confirm-list + rubric G require the creator-authors-both + reviewer-assesses-both + per-item-cross-check + flag-unsupported-completion duty; the two variants match (parity); the duty references the child-01 structure (no divergent restatement). Run `python -m pytest -q` (no regression; paste actual output). `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- The two plan-review variant files (finalize + rubric), DECISIONS, CHANGELOG. (ipd-spec.md is child 03.)

## Open questions

- OQ1 (which plans the duty applies to): lean "agent-executable plans (IPDs and similar)"; a pure research/spec doc with no execution steps still benefits but the duty is scoped to plans with actionable execution. Confirm wording at execution.

## Detailed Implementation Checklist (TODO)

- [x] **Task 1: plan-review Step 4 confirm item** - dual-checklist present + 1:1 + concrete-evidence + catches-false-completion; reviewer strengthens in place if weak/absent.
- [x] **Task 2: plan-review rubric G bullet** - two-checklist requirement as a verifiable item (weak/absent = UNDER-SCOPE finding).
- [x] **Task 3: plan-review-long parity** - same confirm item in `03-resolve-and-finalize.md` + the requirement in `review-rubric.md` (prose executability, not a lettered section).
- [x] **Task 4: DECISIONS (pin number) + CHANGELOG**; depends-on-child-01 noted; no em/en dashes.
- [x] **Task 5: Validate + commit** - `python -m pytest -q` (paste output), leak-clean, path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [x] Open `plan-review.md` Step 4: CONFIRM the dual-checklist creator+reviewer confirm item is present with the "catch false completion" + strengthen-in-place wording; cite lines.
- [x] Open the plan-review rubric `### G. Plan executability` (`plan-review.md:338`): CONFIRM the two-checklist requirement bullet is present; cite lines.
- [x] Open `plan-review-long/03-resolve-and-finalize.md` + `plan-review-long/review-rubric.md`: CONFIRM the identical duty is present (parity of requirement; the long rubric is prose, not lettered); cite lines; quote one matching sentence across variants.
- [x] CONFIRM the duty REFERENCES child 01's structure (does not redefine it) and lets the reviewer strengthen a weak checklist as a finding.
- [x] CONFIRM DECISIONS + CHANGELOG present; paste the `pytest` summary line; leak-clean; no em/en dashes.
- [x] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.

## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution. Child 02 of the `ipd-dual-checklist-convention` Set; DEPENDS ON child 01 (the template must define the two checklists first; if 01's structure is absent, STOP and report). Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped, never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Confirm child 01 is executed first.
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then child 03.
