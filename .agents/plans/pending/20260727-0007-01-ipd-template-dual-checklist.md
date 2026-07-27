# IPD: IPD template gains a top execution checklist + an end verification/cross-check checklist + size guidance

- Date: 2026-07-27
- Concern: execution quality / honest reporting - one checklist (D111) helps, but a second end-of-document verification checklist that cross-checks each execution item with concrete evidence is what catches unsupported completion claims
- Scope: edit the shipped IPD template so it carries an EXECUTION checklist near the beginning and a distinct VALIDATION AND CROSS-CHECK checklist near the end (1:1 mapping), a completion + verification rule, and sharper size guidance. Prose-only template edits + DECISIONS/CHANGELOG.
- Status: approved
- Set: ipd-dual-checklist-convention
- Order: 1
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-27, human ("All approved.") after /plan-review (APPROVE / APPROVE WITH REVISIONS APPLIED). Executing per the 00 orchestrator.

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): child 01 of the `ipd-dual-checklist-convention` Set (see the `-00-` orchestrator). Extends D111 (which added ONE checklist near the end) by moving the execution checklist to the top and adding a distinct end verification checklist; sharpens the D111 size guidance.

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no defects. Verified D111 placed one checklist at ipd.md:104 + size line :137; this correctly moves execution to the top + adds the end verification checklist + supersedes the D111 placement. <=5 steps. Readiness: GO - PENDING HUMAN APPROVAL.

## Goal

Make the shipped IPD template (`.agents/workflows/assess/templates/ipd.md`) require TWO checklists: (1) a `## Detailed Implementation Checklist (TODO)` execution checklist near the BEGINNING, covering every required action, decision, deliverable, and validation as GitHub-style `- [ ]` items; and (2) a `## Validation and cross-check` checklist near the END whose items map 1:1 to the execution checklist and require the executing agent to verify each with CONCRETE evidence before reporting success. Add the completion + honesty rule (no item may be represented complete unless actually performed AND verified; incomplete/blocked/skipped/unverified work is reported explicitly). Sharpen the size guidance: prefer <=5 major steps; avoid more than ~10 major steps or 12-18 total actionable checklist items in one IPD; beyond that, or when parts are independently executable, prefer a sequenced Set coordinated by a `00` orchestrator.

Why it matters: the common failure mode is an agent ticking boxes or asserting "done"/`executed` without having completed and verified every step. A top execution checklist gives an agent a top-down plan; a separate end verification checklist forces a deliberate, evidence-backed cross-check pass before it reports success. This is model-independent quality control, especially valuable for models prone to plan drift.

## Project conventions discovered (Step 0)

- D111 added ONE `## Detailed Implementation Checklist (TODO)` near the END (between `## Open questions` and `## Approval and execution gate`, `ipd.md:104`) + a completion rule + a "prefer small / split into a Set" line (`ipd.md:130,137`). This IPD moves the execution checklist to the top and adds the end verification checklist; it supersedes the D111 single-checklist PLACEMENT (recorded, not silent).
- `Set:`/`Order:` front matter and the `00`-reserved-for-orchestrator naming already exist (`ipd.md:9-10`, AGENTS.md, plans README); the sharper size guidance and the orchestrator reference build on them (the orchestrator TEMPLATE itself is child 03).
- The template is the shipped source the installer stamps into target repos; changes propagate on `aw install`.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| L1 | MEDIUM | Low | executing agent | plan visibility | The execution checklist sits near the END; an agent reading top-down plans its work before reaching it. Moving it near the beginning gives an up-front actionable plan. | `ipd.md:104` |
| L2 | HIGH | Low | reviewer / stakeholder | unsupported completion | There is no SEPARATE end-of-document verification pass; the single checklist doubles as plan and proof, which is exactly the "ticked without doing" failure. A distinct end checklist that cross-checks each execution item with concrete evidence closes this. | `ipd.md:104-124` (one checklist, no end cross-check) |
| L3 | LOW | Low | maintainer | size drift | The D111 size line ("~4-6 tasks") is soft; the request wants sharper, still-non-inflexible thresholds (<=5 preferred; ~10 max / 12-18 items) and an explicit pointer to a `00`-orchestrated Set beyond that. | `ipd.md:137` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | L1 | Move the `## Detailed Implementation Checklist (TODO)` execution checklist to near the BEGINNING of the template (after `## Goal`/`## Project conventions`, before `## Findings` or right after Findings - a position an agent reads before executing), keeping its D111 content (grouped `- [ ]` items naming exact files/symbols + the literal verify command + paste-real-output). Note it covers every required action, decision, deliverable, and validation. | `.agents/workflows/assess/templates/ipd.md` | Low | the execution checklist appears near the top; retains the D111 item guidance; no content lost |
| 2 | L2 | Add a `## Validation and cross-check` checklist near the END (before/within the Approval gate): `- [ ]` items that MAP 1:1 to the execution checklist, each requiring the agent to CONFIRM the item was performed and to cite concrete evidence (command output, file:line, artifact path). Include the honesty rule: no item may be marked complete unless actually performed AND verified; incomplete/blocked/skipped/unverified work MUST be reported explicitly (not silently dropped or ticked). | `.agents/workflows/assess/templates/ipd.md` | Low | the end verification checklist exists, maps 1:1 to the top, requires per-item evidence + the explicit-report-incomplete rule |
| 3 | L2,L3 | Update the completion rule + size guidance in the gate: before claiming done/`executed`, every EXECUTION item is `- [x]` AND its VALIDATION cross-check item is verified with evidence, else STOP and report (checklist is a mitigation, not a guarantee). Size: prefer <=5 major steps; avoid more than ~10 major steps or 12-18 total actionable items; beyond that, or when parts are independently executable, prefer a sequenced `Set:`/`Order:` coordinated by a `00` orchestrator. Keep it guidance, not an inflexible rule. | `.agents/workflows/assess/templates/ipd.md` | Low | completion rule references BOTH checklists; size thresholds stated as strong guidance (not absolute); orchestrator pointer present |
| 4 | all | Docs/decision sync: DECISIONS entry (pin at execution) for the two-checklist template convention (execution top + verification end + completion/honesty rule + sharper size guidance), noting it EXTENDS D111 and SUPERSEDES its single-checklist placement; CHANGELOG. Note child 02 (plan-review duties) and 03 (spec + orchestrator template) as the rest of the Set. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; supersede D111 placement explicitly; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| plan-review creator/reviewer duties | scope | Distinct file + concern; sequenced next. | Child 02. |
| ipd-spec.md update + the `00` orchestrator TEMPLATE | scope | Depends on this + 02 defining the structure/duties. | Child 03. |
| A linter for two-checklist presence / 1:1 mapping | complexity | Separable enhancement; reviewer duty (02) enforces for now. | Later IPD if wanted. |

## Scope check

- Over-scope: none - edits to ONE template file + a docs note. No plan-review edit (02), no spec/orchestrator-template (03), no product code.
- Under-scope: MUST put the execution checklist near the top and a 1:1 end verification/cross-check checklist near the end (L1/L2); MUST require per-item concrete evidence + explicit reporting of incomplete/blocked/skipped/unverified work (L2); MUST state the sharper size guidance as strong-but-not-inflexible + the `00`-orchestrator pointer (L3); MUST supersede D111's single-checklist placement without losing its item-quality guidance; MUST NOT remove any existing required template section.

## Required tests / validation

- Prose only; no pytest delta expected. Validate by review + consistency: the template has a top execution checklist and an end `## Validation and cross-check` checklist that maps 1:1 and requires per-item evidence + the explicit-report-incomplete rule; the completion rule references both; the size guidance states <=5 preferred / ~10 max / 12-18 items -> `00`-orchestrated Set (as guidance); no existing section removed. Run `python -m pytest -q` (no regression; paste actual output). `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `.agents/workflows/assess/templates/ipd.md`, DECISIONS, CHANGELOG. (The canonical `ipd-spec.md` is updated in child 03.)

## Open questions

- OQ1 (exact top position of the execution checklist): lean after `## Project conventions discovered`/`## Goal` and before or just after `## Findings`, so it is high in the document but after the framing; confirm at execution. Does not change the convention.

## Detailed Implementation Checklist (TODO)

- [ ] **Task 1: Move the execution checklist to the top** of `assess/templates/ipd.md` (retain D111 item guidance: grouped `- [ ]`, exact files/symbols, literal verify command, paste output); note it covers every action/decision/deliverable/validation.
- [ ] **Task 2: Add `## Validation and cross-check` near the end** - `- [ ]` items mapping 1:1 to the execution checklist, each requiring concrete evidence, plus the "no item complete unless performed AND verified; report incomplete/blocked/skipped/unverified explicitly" rule.
- [ ] **Task 3: Update the completion rule + size guidance** (both-checklists gate; <=5 preferred / ~10 max / 12-18 items -> `00`-orchestrated Set, as strong guidance).
- [ ] **Task 4: DECISIONS entry (pin number) + CHANGELOG**; state it extends D111 and supersedes its single-checklist placement; no em/en dashes.
- [ ] **Task 5: Validate + commit** - `python -m pytest -q` (paste output), leak-clean, path-scoped commit; then lifecycle move.

## Validation and cross-check (verify before reporting done)

- [ ] Open `assess/templates/ipd.md`: CONFIRM the execution checklist is near the top and the `## Validation and cross-check` checklist is near the end; cite both section lines.
- [ ] CONFIRM the end checklist items map 1:1 to the execution checklist and each requires concrete evidence; quote one mapped pair.
- [ ] CONFIRM the completion rule references BOTH checklists and the size guidance states <=5/~10/12-18 -> Set/`00` orchestrator as guidance (not absolute); quote it.
- [ ] CONFIRM no pre-existing required section (Findings, Proposed changes, Deferred, Scope check, Required tests, Spec sync, Open questions, Approval gate) was removed; diff-check.
- [ ] CONFIRM DECISIONS + CHANGELOG present and that DECISIONS explicitly supersedes D111's placement; paste the `pytest` summary line; leak-clean; no em/en dashes.
- [ ] Report any item above that is incomplete/blocked/unverified EXPLICITLY; do not mark this plan executed otherwise.

## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution. Child 01 of the `ipd-dual-checklist-convention` Set; no dependency (extends D111). Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified with evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped, never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then child 02.
