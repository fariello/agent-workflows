# IPD: update the canonical ipd-spec for the dual-checklist convention + add a 00 orchestrator template

- Date: 2026-07-27
- Concern: single-source consolidation - the canonical IPD spec (D112) and a reusable `00` orchestrator template must reflect the two-checklist + creator/reviewer + size/orchestrator convention so authors have one authoritative reference
- Scope: update `.agents/docs/specs/...-ipd-spec.md` (D112) to describe the two checklists + creator/reviewer duties + size thresholds + the orchestrator, by REFERENCE; add a `00` ORCHESTRATOR TEMPLATE under the workflow templates. Prose/template edits + DECISIONS/CHANGELOG.
- Status: executed
- Set: ipd-dual-checklist-convention
- Order: 3
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-27, human ("All approved.") after /plan-review (APPROVE / APPROVE WITH REVISIONS APPLIED). Executing per the 00 orchestrator.

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): child 03 of the `ipd-dual-checklist-convention` Set (see the `-00-` orchestrator). Depends on children 01 (template structure) and 02 (plan-review duties). Updates the D112 canonical spec IN PLACE (not a fork) and adds the missing orchestrator TEMPLATE (the `00` name is reserved but no template exists).

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no defects. Verified the D112 spec exists at the cited path and the 00-orchestrator name is reserved but has no template; this updates the spec in place + adds the template. Depends on 01+02. <=4 steps. Readiness: GO - PENDING HUMAN APPROVAL.

- 2026-07-27 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): updated ipd-spec.md in place (two checklists + completion rule + creator/reviewer duties + <=5/~10/12-18 + 00 orchestrator) and added .agents/workflows/assess/templates/orchestrator-ipd.md (sequence/deps/completion/cross-IPD validation + its own two checklists). Added DECISIONS D116 + CHANGELOG. Verified spec + template content; leak-clean; no em/en dashes; full suite 440 passed, 1 skipped. Path-scoped commit 2bd4fd7. Status: approved -> executed; moved to executed/.
## Goal

Give authors one authoritative, current reference and a reusable orchestrator template: (1) UPDATE the canonical `ipd-spec.md` (D112) to describe, by reference, the two-checklist structure (execution top + verification/cross-check end, 1:1 with concrete evidence), the completion + honesty rule, the creator/reviewer duties (child 02), and the sharper size thresholds (<=5 preferred; ~10 max / 12-18 items -> a `00`-orchestrated Set); (2) ADD a `00` ORCHESTRATOR TEMPLATE under the workflow templates that defines what an orchestrator IPD must contain: the child sequence, dependencies, completion criteria, and cross-IPD validation. Consolidate by REFERENCE (P8), not duplication.

Why it matters: children 01/02 land the mechanism in the template and the review; the spec must not go stale, and the reserved `00` orchestrator has no template so authors improvise it. One updated spec + one template make the whole convention followable from a single entry point.

## Project conventions discovered (Step 0)

- The canonical spec is `.agents/docs/specs/20260726-1340-01-ipd-spec.md` (D112); it already references the D111 checklist + completion rule + split guidance, so this UPDATES it in place.
- Workflow templates live under `.agents/workflows/assess/templates/` (e.g. `ipd.md`); an orchestrator template fits alongside as `orchestrator-ipd.md` (confirm exact home at execution, OQ1).
- The `00`-reserved-for-orchestrator naming exists (AGENTS.md, plans README, `ipd.md:159`); the CONTENT contract for a `00` orchestrator (sequence/deps/completion/cross-IPD validation) is what this adds - the `-00-` orchestrator of THIS Set is a worked example to model it on.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| N1 | MEDIUM | Low | author / weaker model | stale single source | The D112 canonical spec would not mention the two checklists, creator/reviewer duties, or the sharper size thresholds after 01/02 land; the "single entry point" must be updated or it misleads. | `ipd-spec.md` (references only the D111 single checklist) |
| N2 | MEDIUM | Low | author | missing orchestrator template | `00` is reserved for an orchestrator plan but no TEMPLATE defines what it must contain (sequence, dependencies, completion criteria, cross-IPD validation); authors improvise. | AGENTS.md / plans README / `ipd.md:159` (name reserved, no template) |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | N1 | Update `ipd-spec.md`: describe the TWO checklists (execution near the top; `## Validation and cross-check` near the end, 1:1, concrete evidence per item), the completion + honesty rule (no item complete unless performed AND verified; report incomplete/blocked/skipped/unverified explicitly), the creator/reviewer duties (child 02), and the sharper size thresholds (<=5 preferred; ~10 max / 12-18 items -> a `00`-orchestrated Set). By REFERENCE to the template + plan-review; no divergent restatement. | `.agents/docs/specs/20260726-1340-01-ipd-spec.md` | Low | spec describes both checklists + duties + thresholds by reference; supersedes/updates the D111-only mentions; no fork |
| 2 | N2 | Add a `00` ORCHESTRATOR TEMPLATE: a template for an orchestrator IPD defining the required sections - child sequence + Order, cross-IPD dependencies, whole-Set completion criteria, cross-IPD validation, and its own two checklists. Model it on this Set's `-00-` orchestrator. | a new template (e.g. `.agents/workflows/assess/templates/orchestrator-ipd.md`) | Low | orchestrator template exists with sequence/deps/completion/cross-IPD-validation sections + the two checklists |
| 3 | all | Docs/decision sync: DECISIONS entry (pin at execution) for the spec update + orchestrator template (single-source consolidation of the dual-checklist convention; the `00` orchestrator content contract), noting it completes the `ipd-dual-checklist-convention` Set and depends on 01/02; CHANGELOG. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; Set-complete noted; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| The template structure (01) and plan-review duties (02) | scope | Owned by children 01/02; this references them. | 01/02. |
| Installer stamping the orchestrator template into target repos as a bucket README | complexity | The template is authored content; whether the installer surfaces it is a separate question. | Later IPD if wanted. |

## Scope check

- Over-scope: none - one spec update + one new template + a docs note. No template-structure change (01), no plan-review edit (02), no product code.
- Under-scope: MUST update the D112 spec IN PLACE by reference (N1, no fork/duplication); MUST add a `00` orchestrator template defining sequence/deps/completion/cross-IPD-validation + its own two checklists (N2); MUST stay consistent with the structure 01 defines and the duties 02 defines.

## Required tests / validation

- Prose/template only; no pytest delta. Validate by review + consistency: `ipd-spec.md` describes both checklists + creator/reviewer duties + size thresholds by reference (matching 01/02, no divergence); the orchestrator template exists with the required sections + its own two checklists. Run `python -m pytest -q` (no regression; paste actual output). `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `.agents/docs/specs/20260726-1340-01-ipd-spec.md`, the new orchestrator template, DECISIONS, CHANGELOG.

## Open questions

- OQ1 (orchestrator template home/name): lean `.agents/workflows/assess/templates/orchestrator-ipd.md` (beside `ipd.md`); confirm at execution. Does not change the content contract.

## Detailed Implementation Checklist (TODO)

- [x] **Task 1: Update `ipd-spec.md`** - two checklists + completion/honesty rule + creator/reviewer duties + <=5/~10/12-18 -> `00`-orchestrated Set thresholds, all by reference; supersede the D111-only mentions in place.
- [x] **Task 2: Add the `00` orchestrator template** with sections: child sequence + Order, dependencies, whole-Set completion criteria, cross-IPD validation, and its own execution + verification checklists.
- [x] **Task 3: DECISIONS (pin number) + CHANGELOG**; note Set-complete + depends on 01/02; no em/en dashes.
- [x] **Task 4: Validate + commit** - `python -m pytest -q` (paste output), leak-clean, path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [x] Open `ipd-spec.md`: CONFIRM it now describes both checklists, the completion/honesty rule, the creator/reviewer duties, and the size thresholds, by reference (quote the added lines); confirm no divergent restatement vs 01/02.
- [x] Open the new orchestrator template: CONFIRM it has sequence/Order, dependencies, whole-Set completion criteria, cross-IPD validation, and its own two checklists; cite the path.
- [x] Consistency: quote the two-checklist rule from `ipd-spec.md` and confirm it matches the template (01) and plan-review (02).
- [x] CONFIRM DECISIONS + CHANGELOG present, Set-complete noted; paste the `pytest` summary line; leak-clean; no em/en dashes.
- [x] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.

## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution. Child 03 of the `ipd-dual-checklist-convention` Set; DEPENDS ON children 01 and 02 (the spec references what they define; if their structure/duties are absent, STOP and report). Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Confirm children 01 and 02 are executed first.
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`; then, when 01-03 are all executed and cross-IPD validation passes, the `-00-` orchestrator is completed and moved too.
