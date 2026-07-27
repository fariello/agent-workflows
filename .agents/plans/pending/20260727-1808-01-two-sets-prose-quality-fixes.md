# IPD: prose-quality corrections from the re-review of the dual-checklist + untrack-artifacts Sets

- Date: 2026-07-27
- Concern: instruction effectiveness across diverse agents - a holistic re-review of the shipped prose from the two recent Sets (dual-checklist D114-D116; untrack-workflow-artifacts D117-D120) found the conventions landed well but with a few gaps that could trip a weaker model (Gemini Flash tier): a missed workflow-artifacts flip, an ambiguous commit phrase, an under-guarded destructive command, and an always-loaded pointer that names only one of the two mandatory checklists
- Scope: fix the concrete prose gaps in `release-review/README.md`, `release-review/01-current-state.md`, `tools/README.md`, the always-loaded `agents_pointer_prose` (regenerate AGENTS.md), `assess/assess.md`, `plan-review-long` (definition parity), and `00-run-protocol.md` (cosmetic). Prose + one engine template string + AGENTS.md regeneration; DECISIONS/CHANGELOG.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer-requested re-review of all *.md files touched by the two Sets, judged by "will diverse agents (Gemini 3.5/3.6 Flash, Opus 4.6-4.8, GPT 5.5-5.6) follow them faithfully with appropriate discretion?" The re-review (a full read of the core artifacts + a thorough sub-agent audit of all 15 files, top findings verified against the files) found both conventions landed cleanly (no em/en dashes; local-only default consistent; discretion well-calibrated) but surfaced the fixes below. This corrects them in place; it does not re-open the executed Set plans.

## Goal

Close the prose gaps the re-review found so the two conventions work for a WEAK model, not just a careful reader: (F1) `release-review/README.md:127` still says "Commit the section's tracked changes AND run artifacts" - a fifth un-flipped spot that literally instructs committing `workflow-artifacts/`, contradicting the local-only default; (F2) `01-current-state.md:108` "Checkpoint recorded ... and committed" reads as committing a local-only file; (F3) the always-loaded AGENTS.md directive (`agents_pointer_prose`) names only the single `## Detailed Implementation Checklist (TODO)`, so a weak model that never opens the ipd-spec will not know the end `## Validation and cross-check` checklist is ALSO mandatory; (F4) `tools/README.md`'s `git filter-repo` history-rewrite is only a soft "Note", not a consent/force-push absolute; (F5) small clarity fixes (`tools/README.md` `aw sanitize` -> add `--agent`; `assess.md:137` run-on sentence; "agent-executable plan" defined in plan-review but not in the long variant/rubric; the cosmetic duplicate "3." list marker in `00-run-protocol.md:9`).

Why it matters: F1/F3/F4 defeat the conventions' purpose for exactly the weak/fast-model case they were built for - F1 re-introduces the workflow-artifacts leak, F3 hides the mandatory second checklist from the always-loaded context, and F4 leaves a destructive force-push command under-guarded in a toolkit that otherwise forbids history rewrite without explicit approval.

## Project conventions discovered (Step 0)

- The local-only workflow-artifacts default (D117/D118/D120) is otherwise consistent; F1/F2 are the two residual spots the earlier corrective (D120) did not reach (it targeted `00-run-protocol.md:248/:260`, `benchmark:167`, and the D114->D117 refs).
- The always-loaded block is `agents_pointer_prose()` in `engine.py` (the `### Authoring and executing IPDs` section, D112); it regenerates into AGENTS.md via the sectioned path (D104) - a refresh must be an EMPTY DIFF and must not disturb the `AGENT-PLANS` sibling.
- The dual-checklist section names are `## Detailed Implementation Checklist (TODO)` (execution) and `## Validation and cross-check` (verification) per D114/the ipd-spec.
- `git filter-repo` history rewrite is destructive + force-pushes; the toolkit's posture (release-review Section 9, never ad-hoc push/tag) requires explicit human approval for such actions.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| F1 | MEDIUM | Low | agent running release-review | residual leak | `README.md:127` step 7 says "Commit the section's tracked changes and run artifacts" - literally instructs committing `workflow-artifacts/`, contradicting the local-only default (`README.md:158`, `00-run-protocol.md:245-250`). A fast model that does not chase "(see commit policy)" force-adds the run tree. | `.agents/workflows/release-review/README.md:127` |
| F2 | LOW | Low | agent running release-review | ambiguity | `01-current-state.md:108` exit-gate "Checkpoint recorded in `08-checkpoints.md` and committed." reads as committing the local-only checkpoint file; the write-not-commit reconciliation lives only in `00-run-protocol.md`. | `.agents/workflows/release-review/01-current-state.md:108` |
| F3 | MEDIUM | Low | weak model (always-loaded only) | mandatory rule hidden | The always-loaded `agents_pointer_prose` directive names only `## Detailed Implementation Checklist (TODO)`; a weak model that never opens the ipd-spec will not know the end `## Validation and cross-check` checklist is mandatory too - undercutting D114-D116. | `agent_workflows/engine.py` `agents_pointer_prose` (`### Authoring and executing IPDs`); `AGENTS.md:38` |
| F4 | MEDIUM | Low | agent told to "remediate" | under-guarded destructive command | `tools/README.md` presents `git filter-repo --path workflow-artifacts/ --invert-paths` with only a soft "Note", not a consent/force-push absolute; a model could run it literally. | `tools/README.md:46-47` |
| F5 | LOW | Low | any / weak model | clarity | `tools/README.md:36` `aw sanitize .` lacks `--agent` (the sizing purpose wants machine-parseable output); `assess.md:137` buries the local-only absolute as the 4th clause of a run-on; "agent-executable plan" is defined in `plan-review.md:259` but not in `plan-review-long/03` or `review-rubric.md`; `00-run-protocol.md:9` has a cosmetic duplicate "3." list marker. | `tools/README.md:36`; `assess.md:137`; `plan-review-long/03-resolve-and-finalize.md`, `review-rubric.md`; `00-run-protocol.md:9` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | F1,F2 | release-review: `README.md:127` -> commit the section's tracked PRODUCT changes only; run artifacts are written to `workflow-artifacts/` but stay local-only (do not commit/force-add). `01-current-state.md:108` -> the section's tracked product changes are committed; the checkpoint file itself stays local-only. Consistent with `00-run-protocol.md:245-250`. | `.agents/workflows/release-review/README.md`, `.agents/workflows/release-review/01-current-state.md` | Low | neither line instructs committing run artifacts; both consistent with 00-run-protocol |
| 2 | F3 | Add BOTH checklists to the always-loaded directive: edit `agents_pointer_prose` so the `### Authoring and executing IPDs` line names the top execution checklist AND the end `## Validation and cross-check` checklist, and states the completion rule (every item verified with concrete evidence before `executed/`). Keep it to a couple of lines (lean block, D99/D100). Regenerate AGENTS.md via the sectioned path to an EMPTY DIFF; leave the `AGENT-PLANS` sibling untouched. | `agent_workflows/engine.py`, `AGENTS.md` | Low | the directive names both checklists + the completion rule; AGENTS.md reinstall is an empty diff; AGENT-PLANS untouched |
| 3 | F4 | `tools/README.md`: replace the soft filter-repo "Note" with an explicit ABSOLUTE - run only with explicit human approval; it rewrites history, changes commit SHAs, and requires coordinated force-pushing across all clones (consistent with the toolkit's never-rewrite-history-without-approval posture). | `tools/README.md` | Low | the filter-repo command carries an explicit human-approval + force-push warning, not a soft note |
| 4 | F5 | Clarity: `tools/README.md:36` `aw sanitize .` -> `aw sanitize . --agent`; `assess.md:137` split the run-on so "Commit ONLY the IPD" and "the run record is local-only; do not commit or force-add it" are distinct sentences; add the `plan-review.md:259` inline definition of "agent-executable plan" ("an IPD or similar with actionable steps") to `plan-review-long/03` and `review-rubric.md`; fix the duplicate "3." marker in `00-run-protocol.md:9`. | `tools/README.md`, `.agents/workflows/assess/assess.md`, `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `.agents/workflows/plan-review-long/review-rubric.md`, `.agents/workflows/release-review/00-run-protocol.md` | Low | each clarity item applied; no meaning changed elsewhere |
| 5 | all | DECISIONS entry (pin at execution) recording the re-review corrections (F1-F5), noting it extends D114-D120 and does not re-open the executed plans; CHANGELOG only if a user-facing statement changed materially (lean: omit - consistency corrections). | `DECISIONS.md`, (CHANGELOG.md if warranted) | Low | DECISIONS entry present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Re-opening the executed Set plans (D114-D120) | n/a | policy | Executed plans are not re-opened; this corrective is the record. | n/a |
| The "do not hand-edit inside aw:block" AGENTS.md directive | scope | Its own TODO item; this only adds the dual-checklist words to the existing directive. | Its own IPD (TODO.md). |
| Any code-logic change | n/a | scope | Findings are prose/docstring only. | n/a |

## Scope check

- Over-scope: none - targeted prose fixes + one always-loaded directive string + AGENTS.md regeneration + a DECISIONS note. No code logic, no executed-plan edits, no new feature.
- Under-scope: MUST flip the residual `README.md:127`/`01-current-state.md:108` (F1/F2); MUST add BOTH checklists to the always-loaded directive with an empty-diff AGENTS.md regen and the AGENT-PLANS sibling untouched (F3); MUST turn the filter-repo note into a consent/force-push absolute (F4); MUST apply the F5 clarity items without changing meaning elsewhere.

## Required tests / validation

- Prose + one docstring line; run `python -m pytest -q` (expect 445 passed, 1 skipped; paste actual output). Grep release-review for any remaining "commit ... run artifacts" instruction (should be none). Confirm the always-loaded directive names both checklists and AGENTS.md reinstall is an empty diff (AGENT-PLANS untouched). Confirm the filter-repo command carries the human-approval absolute. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- The five workflow/doc files, `agent_workflows/engine.py` + regenerated `AGENTS.md`, DECISIONS, (CHANGELOG if warranted).

## Open questions

- OQ1 (CHANGELOG): lean OMIT - these are consistency corrections to already-shipped conventions, not new user-facing behavior. Confirm at execution.

## Detailed Implementation Checklist (TODO)

- [ ] **Task 1: release-review F1/F2** - `README.md:127` (product-only commit; run artifacts local-only) + `01-current-state.md:108` (checkpoint file stays local-only).
- [ ] **Task 2: always-loaded dual-checklist (F3)** - `agents_pointer_prose` names BOTH checklists + completion rule; regenerate AGENTS.md to an empty diff; AGENT-PLANS sibling untouched.
- [ ] **Task 3: filter-repo absolute (F4)** - `tools/README.md` explicit human-approval + force-push warning replaces the soft note.
- [ ] **Task 4: clarity (F5)** - `aw sanitize . --agent`; split `assess.md:137`; add agent-executable-plan definition to `plan-review-long/03` + `review-rubric.md`; fix `00-run-protocol.md:9` duplicate "3.".
- [ ] **Task 5: DECISIONS (pin number)** (+ CHANGELOG only if warranted); run `python -m pytest -q` and PASTE output; leak-clean; path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [ ] Grep release-review: CONFIRM no line instructs committing run artifacts; `README.md:127` + `01-current-state.md:108` now product-only/local-only; cite the new lines.
- [ ] Open the regenerated AGENTS.md `### Authoring and executing IPDs`: CONFIRM it names BOTH `## Detailed Implementation Checklist (TODO)` and `## Validation and cross-check` + the completion rule; CONFIRM a reinstall/refresh is an EMPTY DIFF and the AGENT-PLANS sibling is byte-identical; cite.
- [ ] Open `tools/README.md`: CONFIRM the filter-repo command carries an explicit human-approval + force-push absolute (not a soft note); CONFIRM `aw sanitize . --agent`; cite.
- [ ] CONFIRM `assess.md:137` split into distinct sentences; the agent-executable-plan definition is in `plan-review-long/03` + `review-rubric.md`; `00-run-protocol.md:9` numbering fixed; cite each.
- [ ] CONFIRM DECISIONS entry present; PASTE the `pytest` summary (expect 445 passed, 1 skipped); leak-clean; no em/en dashes.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.

## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. It corrects re-review findings from the two executed Sets; it does NOT re-open those executed plans and does NOT change code logic. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (edit only the existing `agents_pointer_prose` directive; do not add the separate aw:block edit-protection directive here; regenerate AGENTS.md, do not hand-edit it). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
