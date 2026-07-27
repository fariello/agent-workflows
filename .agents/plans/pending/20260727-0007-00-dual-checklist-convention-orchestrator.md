# IPD (ORCHESTRATOR): dual-checklist + creator/reviewer + size/orchestrator convention for agent-executable artifacts

- Date: 2026-07-27
- Concern: execution quality / honest reporting - make agent-executable documents (IPDs and similar) carry a top execution checklist AND an end verification/cross-check checklist, require creator and reviewer to implement and assess both, and encode strong size guidance + a defined `00` orchestrator so large work is sequenced rather than drifting
- Scope: ORCHESTRATOR for the ordered Set `ipd-dual-checklist-convention`. It defines the sequence, dependencies, completion criteria, and cross-IPD validation for the three child IPDs. It does NOT itself change files (each child does its own edits). This is a dogfood: the convention being added is used to structure its own rollout.
- Status: reviewed
- Set: ipd-dual-checklist-convention
- Order: 0
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer instruction to standardize a two-checklist + creator/reviewer + size-guidance/orchestrator convention. Because the work spans the IPD template, the plan-review workflow, the canonical ipd-spec, and an orchestrator template - and the convention itself says to sequence large work as a Set with a `00` orchestrator - it is shaped as this orchestrated Set. Builds ON D111 (the single checklist + completion rule + light split guidance) and D112 (the canonical ipd-spec + always-loaded directive), which it extends.

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-002. Verified the child sequence/deps + cross-IPD-validation are coherent; tightened the dogfood note (children already carry BOTH checklists, not an interim single one). Cross-IPD consistency holds (the two-checklist rule matches across 00/01/02/03); each child <=5 steps; D111 superseded-not-forked, D112 updated-in-place. No open questions (OQ1/OQ2 resolved by maintainer); no unfixed BLOCKER/HIGH. Readiness: GO - PENDING HUMAN APPROVAL.

## Goal

Coordinate the rollout of one convention across three child IPDs so each stays small and independently verifiable while the whole lands coherently: (01) the IPD TEMPLATE gains a top execution checklist + an end verification/cross-check checklist + the completion/verification rules + sharper size guidance; (02) PLAN-REVIEW requires the creator to implement both checklists and the reviewer to assess both (and to verify each top item has a concrete end cross-check); (03) the canonical IPD-SPEC is updated and a `00` ORCHESTRATOR TEMPLATE is added. This orchestrator states the order, the dependencies, and the cross-IPD checks that prove the convention is coherent end to end.

Why it matters: the common failure mode is an agent claiming completion without having done every step. One checklist (D111) helps; a SECOND, end-of-document verification checklist that cross-checks each top item with concrete evidence, applied by BOTH the creator and the reviewer, is the guardrail that catches unsupported completion claims. Sequencing large work behind a `00` orchestrator keeps each piece within a size an agent can execute reliably.

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260727-0007-01-ipd-template-dual-checklist.md` | IPD template: move the execution checklist to the TOP, add an end `## Validation and cross-check` checklist (1:1 with the top), completion + verification rules, sharper size guidance (<=5 preferred; ~10 max / 12-18 items -> split into a Set; use a `00` orchestrator to coordinate). | none (extends D111) |
| 02 | `20260727-0007-02-plan-review-dual-checklist-duties.md` | plan-review (+ plan-review-long parity): the CREATOR must implement both checklists; the REVIEWER must assess both and confirm each top item has a concrete end cross-check, flagging any unsupported completion. Added to Step 4 + the rubric. | 01 (the template must define the two checklists first) |
| 03 | `20260727-0007-03-ipd-spec-and-orchestrator-template.md` | Update the canonical `ipd-spec.md` (D112) to describe the two checklists + creator/reviewer duties + size thresholds + the orchestrator; add a `00` ORCHESTRATOR TEMPLATE under the workflow templates. | 01 and 02 (spec references what they define) |

## Completion criteria (the whole Set is done only when)

- 01 executed: the template has a top execution checklist and an end verification/cross-check checklist (1:1 mapping), the completion+verification rules, and the sharper size guidance; no existing required section lost.
- 02 executed: both plan-review variants require the creator to author both checklists and the reviewer to assess both + confirm per-item cross-checks; the rubric/Step-4 gate reflects it.
- 03 executed: `ipd-spec.md` describes the full convention by reference; a `00` orchestrator template exists.
- Cross-IPD validation (below) passes.
- The whole suite is green after each child and at the end; `aw check-local-leaks .` clean; no em/en dashes.

## Cross-IPD validation

- Consistency: the two-checklist structure named in 01 is the SAME structure plan-review assesses in 02 and the spec describes in 03 (no divergent names or rules). Read 01's template + 02's reviewer duty + 03's spec together and confirm they cannot be read as contradictory.
- No duplication/drift with D111/D112: 01 SUPERSEDES D111's single-checklist placement (recorded, not silently); 03 UPDATES the D112 spec in place rather than forking it.
- Dogfood check: each child IPD ALREADY carries the new two-checklist structure (a top `## Detailed Implementation Checklist (TODO)` + an end `## Validation and cross-check`), authored ahead of 01 to demonstrate the convention; 01 then makes that structure the template default.
- Size check: each child stays within the size guidance (<=5 major steps; well under ~10 / 12-18 items).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Retrofitting existing executed IPDs to the two-checklist structure | scope | Forward-looking template/convention change; retrofitting history adds noise. | n/a |
| A programmatic linter that a document contains both checklists / that end items map to top items | complexity | Possible (docs are tracked Markdown) but a separable enhancement; the reviewer duty (02) is the enforcement for now. | A later IPD if wanted. |
| Applying the convention to non-IPD artifacts beyond a general statement | scope | The request says apply generically; 03's spec states the general principle, but concrete non-IPD templates (e.g. prompts) are their own future work. | Per-artifact IPDs if needed. |

## Scope check

- Over-scope: none - this orchestrator only coordinates; the three children make bounded, single-concern edits.
- Under-scope: the Set MUST deliver the two checklists (01), the creator+reviewer duties (02), and the spec + orchestrator template (03), kept consistent (cross-IPD validation), superseding/updating D111/D112 rather than forking them, and applying the convention generically (not model-specific).

## Required tests / validation

- Documents/workflow-prose (01/02) + one spec + one template (03); no product-code logic. Validation is by review + consistency + the cross-IPD checks above. Run `python -m pytest -q` after each child to confirm NO regression (paste actual output). `aw check-local-leaks .` clean; no em/en dashes.

## Open questions

- OQ1 (Set vs one IPD): RESOLVED (maintainer) - a sequenced Set with this `00` orchestrator (dogfoods the convention; keeps each child manageable).
- OQ2 (two-checklist placement): RESOLVED (maintainer) - execution checklist near the TOP, a distinct verification/cross-check checklist near the END; supersedes D111's single-checklist placement (recorded in 01).

## Detailed Implementation Checklist (TODO)

This orchestrator coordinates; its "actions" are gating the children and the cross-IPD checks.

- [ ] **Child 01 executed** (template dual-checklist + rules + size guidance); its own checklist all `- [x]` and verified.
- [ ] **Child 02 executed** (plan-review creator/reviewer duties), after 01; its own checklist verified.
- [ ] **Child 03 executed** (ipd-spec update + orchestrator template), after 01 and 02; its own checklist verified.
- [ ] **Cross-IPD validation run**: the two-checklist structure is consistent across 01/02/03 (no contradiction); D111 superseded-not-forked and D112 updated-in-place; size guidance honored by each child.
- [ ] **Suite green** after the last child (`python -m pytest -q`, actual output pasted); leak-clean; no em/en dashes.

## Validation and cross-check (verify before reporting the Set complete)

Each item maps to a checklist item above; provide concrete evidence.

- [ ] 01 done: open the template and CONFIRM a top execution checklist + an end `## Validation and cross-check` checklist (1:1) + completion/verification rules + <=5/~10/12-18 size guidance are present; cite the section lines.
- [ ] 02 done: open both plan-review variants and CONFIRM the creator-authors-both + reviewer-assesses-both + per-item-cross-check duties are stated (Step 4 + rubric); cite lines.
- [ ] 03 done: open `ipd-spec.md` and the new orchestrator template and CONFIRM the convention is described by reference and a `00` orchestrator template exists; cite paths.
- [ ] Consistency: quote the two-checklist rule from 01, 02, and 03 and confirm they match (no divergent names/rules).
- [ ] Evidence, not assertion: paste the actual `pytest` summary line from the final run; do NOT mark this Set complete on any child whose own Validation checklist was not fully verified.

## Approval and execution gate

This ORCHESTRATOR is a proposal; it and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark this orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review this orchestrator + the three children (optionally `/plan-review`).
2. On human approval, execute 01 -> 02 -> 03 in order, each validated; commit path-scoped (no push).
3. Set each child's terminal `Status: executed` and `git mv` to `.agents/plans/executed/`; when all three are done and cross-IPD validation passes, do the same for this orchestrator.
