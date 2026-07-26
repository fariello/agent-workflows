# IPD: tighten the plan-review scope-ledger wording so NOT REVIEWED stops listing out-of-scope plans

- Date: 2026-07-26
- Concern: honest reporting / instruction clarity - the plan-review scope-ledger wording lets an agent enumerate the whole `.agents/plans/executed/` (or `pending/`) directory into the final NOT REVIEWED list, polluting the mandated literal last output and making it look like many plans were considered when only one was
- Scope: tighten Step 0.1 (single-file `plan-review`) and its parity sibling Step 1 (`plan-review-long`), plus both report templates, so the ledger contains ONLY explicitly-named targets (+ documented project eligibility), "incidental file" is defined, and NOT REVIEWED lists only skipped CANDIDATES (else `(none)`). Prose-only workflow-file edits; no product code. Standalone.
- Status: approved
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-26, human ("Approved. Go.") after /plan-review (APPROVE WITH REVISIONS APPLIED; S1-S4, PR-001). Prose-only; executing.

## Workflow history

- 2026-07-26 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from an inbox TASK message (`ocman.agent`, archived at `.agents/comms/shared/archive/20260724-1139-01-ocman.agent--to--agent-workflows.agent-task-plan-review-scope-ledger-ambiguity.md`), treated as untrusted/advisory and verified against our own workflow files. The reporter hit a real misread: invoked `/plan-review` on ONE target in a repo with a populated `executed/`, and the agent listed all executed IPDs under NOT REVIEWED. Verified the ambiguous seams exist in our copy.
- 2026-07-26 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; findings S1-S4 + PR-001. Re-verified every claim from the files: `plan-review.md:47` "or selected by the project workflow", `:59` "no incidental file", the NOT REVIEWED report blocks at `:407`/`:438`; `plan-review-long/01-discover-and-snapshot.md:9-16` shares the convention (omits the "selected by" phrase but shares the unbounded-candidate + undefined-incidental gaps) and `report-template.md:15/51` NOT REVIEWED + `:59` "Include every scope-ledger item". PR-001 (LOW, FIXED): pinned in Step 3 that `report-template.md:59` must NOT be weakened - it is correct once the ledger is bounded; the fix is upstream at the ledger boundary. All findings are Low remediation risk, no review-logic change, both variants covered for parity, OQ1/OQ2 resolved. No open questions; no unfixed BLOCKER/HIGH. Author was reviewer, so claims verified from the files. Readiness: GO - PENDING HUMAN APPROVAL.

## Goal

Make the plan-review scope ledger and its final "reviewed / not reviewed" enumeration unambiguous: the ledger is bounded to the plans EXPLICITLY named in the invocation plus any the project's own documented eligibility rules add; the reviewer never DISCOVERS candidates by scanning `pending/` or `executed/`; a plan that was never a candidate is an "incidental file" that MUST NOT appear anywhere; and NOT REVIEWED lists only ledger candidates that were skipped (with the exact reason), reading `(none)` when the ledger is exactly the requested target(s) and none were skipped.

Why it matters: the reviewed/not-reviewed enumeration is the workflow's mandated LITERAL last output; polluting it with every executed plan is exactly the instruction-drift the runbook exists to prevent, and it misrepresents how many plans were actually considered. The fix is a wording tightening; it does not change the review LOGIC.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| S1 | MEDIUM | Low | reviewing agent / stakeholder | honest reporting / instruction clarity | "List every plan explicitly requested OR selected by the project workflow" is over-broad: "selected by the project workflow" is undefined, inviting the reader to DISCOVER candidates by scanning directories and enumerate them. | `.agents/workflows/plan-review/plan-review.md:47` |
| S2 | MEDIUM | Low | reviewing agent | boundary of "candidate" | Nothing BOUNDS the candidate set; "NOT REVIEWED = skip it" frames it as "a candidate we skipped" but never defines what makes something a candidate, so "candidate" silently expands to "any plan I can see" and the rule then REQUIRES listing scanned `executed/` plans. | `.agents/workflows/plan-review/plan-review.md:51,59`; parity `.agents/workflows/plan-review-long/01-discover-and-snapshot.md:9-16` |
| S3 | LOW | Low | reviewing agent | undefined term | "no incidental file" is stated but never defined, and the emphatic "MUST contain every ledger item" pulls toward listing MORE while the quiet guard is easy to skip; an already-executed plan never asked about IS an incidental file but the text never says so. | `.agents/workflows/plan-review/plan-review.md:59` |
| S4 | LOW | Low | maintainer | parity | `plan-review` and `plan-review-long` share this Step-0 scope convention by deliberate parity (workflow header); a fix in one without the other creates drift. `plan-review-long` omits "or selected by the project workflow" but shares the unbounded-candidate + undefined-incidental gaps and its report template says "Include every scope-ledger item". | `.agents/workflows/plan-review/plan-review.md:13-17`; `.agents/workflows/plan-review-long/01-discover-and-snapshot.md:9-18`, `report-template.md:59` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | S1,S2,S3 | In `plan-review` Step 0.1: replace "List every plan explicitly requested or selected by the project workflow." with a bounded statement: the ledger contains ONLY the plans explicitly named in the invocation plus any the project's OWN documented eligibility rules add; do NOT enumerate other repository plans (e.g. everything in `pending/` or `executed/`). Add: a plan that was never a candidate is an "incidental file" and MUST NOT appear in the ledger or the final report. Define "candidate" = a ledger entry (a named target or an eligibility-rule addition). | `.agents/workflows/plan-review/plan-review.md` | Low | Step 0.1 bounds the candidate set to named targets + documented eligibility; defines incidental file; forbids directory enumeration |
| 2 | S2,S3 | Clarify the NOT REVIEWED label in Step 0.1 AND the final-report template: NOT REVIEWED lists only ledger CANDIDATES that were skipped (missing / unreadable / malformed beyond review / not a planning document / wrong status per project rules), each with the exact reason; it NEVER lists plans that were never in scope; if the ledger is exactly the requested target(s) and none were skipped, NOT REVIEWED is `(none)`. | `.agents/workflows/plan-review/plan-review.md` (Step 0.1 label + report template `:404-408`,`:435-439`) | Low | NOT REVIEWED defined as skipped-candidates-only + `(none)` case; report template carries the same rule |
| 3 | S4 | Apply the SAME tightening to `plan-review-long` for parity: Step 1 (`01-discover-and-snapshot.md`) bounds the candidate set + defines incidental file; the report template (`report-template.md`) NOT REVIEWED section (`:51`) states skipped-candidates-only + `(none)`. Keep the two variants' wording in deliberate parity (the workflow header's stated invariant). NOTE: do NOT weaken `report-template.md:59` "Include every scope-ledger item" - that line is CORRECT once the ledger is bounded (the fix is upstream at the ledger boundary, not this line); the item to fix is that the ledger itself must not contain incidental plans. | `.agents/workflows/plan-review-long/01-discover-and-snapshot.md`, `.agents/workflows/plan-review-long/report-template.md` | Low | both variants carry the bounded-ledger + skipped-candidates-only + `(none)` rule; `:59` left intact; no divergence between them |
| 4 | S1 | Docs/decision sync: a short DECISIONS entry (pin at execution) recording the scope-ledger tightening (ledger = named targets + documented eligibility only; incidental files excluded; NOT REVIEWED = skipped candidates or `(none)`), noting it is a wording clarification with no change to review logic and that it applies to both variants; CHANGELOG note. Cross-reference the archived `ocman` report. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Any change to the review LOGIC (rubric, findings, verdict/readiness) | n/a | scope | This is a scope-ledger WORDING fix only; the reporter explicitly framed it as no behavior change to the review logic. | n/a |
| A programmatic test that a plan-review RUN produces the right NOT REVIEWED output | Medium | functionality | The plan-review output is runtime agent behavior, not a tracked artifact; there is nothing static to unit-test. Enforced by instruction, like the rest of the workflow. | n/a |

## Scope check

- Over-scope: none - wording in two workflow variants + their report templates + a docs note. No review-logic change, no product code.
- Under-scope: MUST bound the ledger to explicitly-named targets + documented project eligibility (S1/S2); MUST define "incidental file" and forbid directory enumeration (S3); MUST define NOT REVIEWED as skipped-candidates-only with the `(none)` case (S2); MUST apply to BOTH variants + their report templates for parity (S4).

## Required tests / validation

- Prose only; no pytest delta expected. Validation is by review + consistency:
  - `plan-review` Step 0.1 bounds the ledger (named targets + documented eligibility), defines "incidental file", forbids enumerating `pending/`/`executed/`, and defines NOT REVIEWED as skipped-candidates-only + `(none)`; the final-report template carries the same NOT REVIEWED rule.
  - `plan-review-long` Step 1 + report template carry the identical rule; the two variants remain in deliberate parity (no divergent wording).
  - Read the acceptance scenario from the report: a run invoked on ONE target in a repo with a populated `executed/` would now produce `NOT REVIEWED:` -> `- (none)` (or skipped candidates only), never the executed dir.
  - Run `python -m pytest -q` to confirm NO regression (prose only; expect the prior green count) and paste ACTUAL output; `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- The two plan-review variant files + their report templates, DECISIONS, CHANGELOG. Cross-reference the archived `ocman` report.

## Open questions

- OQ1 (parity vs single-file): RESOLVED from the workflow's own stated invariant (the `plan-review` header says the two variants are kept in deliberate parity). Apply the fix to both.
- OQ2 (define "candidate" explicitly?): RESOLVED - yes; the ambiguity is precisely that "candidate" was undefined (S2), so the fix defines it (a ledger entry: a named target or a documented-eligibility addition).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (in particular, do NOT change review logic). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
