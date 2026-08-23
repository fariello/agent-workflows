# IPD: IPD Right-Sizing Rubric in Review Workflows and Authoring Guidance

- Date: 2026-08-22
- Kind: child
- Concern: A passing `aw ipd lint` size check measures COUNT (>18 E-leaves / >5 groups), not conceptual density; Order-sized E-items slip through as "Size assessment: standard", degrading a real agent's context/attention/execution.
- Scope: The prose rubric in `/plan-review`, `/plan-review-long`, and the assess IPD-producing harness, plus `aw ipd scaffold` authoring guidance; NO code heuristic here (that is Order 07).
- Status: executed
- Set: highpbacklog0822
- Order: 6
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: por1hi

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog 8iy2dk (part 1 of 2); root cause was the awoptimize Set passing size lint while Orders 02/03/04 each held Order-sized E-items.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (name plan-review.md as the CANONICAL rubric home; others copy/reference to avoid 6-file drift), PR-002 (E-03 targets template TEXT not ipd_authoring.py code; fence updated), PR-003 (V-04 dry-run against a NAMED awoptimize dense exemplar), PR-004 (gave the concrete rubric text: the a/b/c/d diagnostic questions), PR-005 (Status draft->reviewed). Claims verified: no right-sizing prose currently in plan-review/-long; assess template Size/Cohesion at :84-85; thresholds in ipd_schema.py:528-538 / ipd_lint.py:620-640.
- 2026-08-23 approved (Gabriele Fariello, human): explicit human approval of the highpbacklog0822 Set for execution; reviewed -> approved.
- 2026-08-23 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-04 executed via agy/Gemini (committed 4bfc72b + 00de5d3): canonical per-E-item conceptual-density right-sizing rubric added to plan-review.md, copied to plan-review-long/, assess.md harness + IPD templates (scaffold authoring guidance), one-line ipd_authoring.py string, and the rule that a maintainer sizing question is a FINDING not a dismissal; tests/test_plan_review_parity.py. opencode independently verified: rubric present in canonical plan-review.md, 4 E performed / 4 V pass (pre-transition conforming), full suite 2035 passed 1 skipped (pytest rc=0). Closes backlog 8iy2dk part 1/2. Terminal transition to executed/.

## Goal

Add an explicit "one concern / executable-in-one-focused-pass per E-item" right-sizing judgment to the review and authoring workflows, so reviewers and authors catch conceptually-dense IPDs that a count-based lint misses, and treat a maintainer's sizing question as a finding to investigate by decomposition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Review-workflow rubric

- [x] E-01 Add a per-E-item conceptual-density right-sizing rubric check to `.aw/system/workflows/plan-review/plan-review.md` (this is the CANONICAL statement of the definition; all other locations reference or copy from it verbatim to avoid drift). The rubric asks, for each IPD and each E-item: (a) does one E-item name multiple distinct deliverables or touch multiple independent code regions/files? (b) does it bundle multiple independent test-surfaces (would it need several unrelated V-items)? (c) could it be executed and verified as two or more independent passes? (d) would a faster/weaker model lose focus/context executing it as one item? If yes to any, recommend splitting into smaller child IPDs (an UNDER-SCOPE/REPLAN-style finding) - a passing count-based size lint does NOT clear this.
  - Depends on: none
  - Expected outcome: `/plan-review` explicitly evaluates conceptual density, not just count, using the canonical rubric text.
  - Execution state: performed
  - Execution note: Added canonical conceptual-density right-sizing rubric (diagnostic questions a, b, c, d, splitting recommendation, and count lint insufficiency) to .aw/system/workflows/plan-review/plan-review.md under Engineering rubric G and Structural preflight.

- [x] E-02 Add the SAME right-sizing rubric (copied verbatim from the canonical E-01 wording, or referencing it) to `.aw/system/workflows/plan-review-long/` (its `02-review-and-revise.md` and/or `review-rubric.md`), keeping the deliberate parity the two variants already declare.
  - Depends on: none
  - Expected outcome: the long/parallel variant applies the identical right-sizing check, word-for-word aligned with plan-review.md.
  - Execution state: performed
  - Execution note: Added the matching right-sizing rubric to .aw/system/workflows/plan-review-long/review-rubric.md (Plan completeness and preflight) and .aw/system/workflows/plan-review-long/02-review-and-revise.md (Revise in place).

### Task group 2: Authoring guidance

- [x] E-03 Add the "one concern per E-item; split when an E-item names multiple deliverables/test-surfaces" guidance (the same canonical wording) to the assess IPD-producing harness (`.aw/system/workflows/assess/assess.md`) and the IPD TEMPLATES (`.aw/system/workflows/assess/templates/ipd.md`, `orchestrator-ipd.md`) - since `aw ipd scaffold` writes from those templates, editing the template text IS the scaffold authoring guidance. Do NOT modify `agent_workflows/ipd_authoring.py` scaffold CODE unless a one-line guidance string genuinely lives there rather than in the template; if it does, keep it to that one string and cite it.
  - Depends on: none
  - Expected outcome: authored/scaffolded IPDs are steered toward one-concern E-items from the start via the template text; no scaffold code refactor.
  - Execution state: performed
  - Execution note: Added one-concern-per-E-item right-sizing guidance to .aw/system/workflows/assess/assess.md (Operating mode and IPD description), .aw/system/workflows/assess/templates/ipd.md, and .aw/system/workflows/assess/templates/orchestrator-ipd.md, maintaining parity with agent_workflows/ipd_authoring.py _EXEC_INTRO.

### Task group 3: Maintainer-signal rule

- [x] E-04 Add an explicit rule to `/plan-review` and `/plan-review-long` that a maintainer's sizing/splitting question is a FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed.
  - Depends on: E-01, E-02
  - Expected outcome: reviewers treat a human sizing concern as an investigation trigger, not a lint-cleared non-issue.
  - Execution state: performed
  - Execution note: Added maintainer sizing/splitting signal rule to .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, and .aw/system/workflows/plan-review-long/review-rubric.md.

## Project conventions discovered (Step 0)

- `plan-review.md` delegates STRUCTURE to `aw ipd lint` (`plan-review.md:115-140`) and has an over-scope default and a UX-states line but NO conceptual-density/right-sizing prose.
- `plan-review-long/` (multi-file: `01-discover-and-snapshot.md`, `02-review-and-revise.md`, `03-resolve-and-finalize.md`, `review-rubric.md`) has no size/right-sizing language.
- The assess harness is `.aw/system/workflows/assess/assess.md`; child IPD template `.aw/system/workflows/assess/templates/ipd.md` already carries `Size assessment` + `Cohesion rationale` in its gate (`:82-86`).
- The count thresholds live in code (`ipd_schema.py:528-538`, `MAX_TASK_GROUPS=5`, `MAX_E_LEAVES=18`) and are enforced in `ipd_lint.py:620-640` (`check_size`). This plan changes PROSE only; the mechanical heuristic is Order 07.

## Findings

Root cause (2026-08-21): the awoptimize Set passed `aw ipd lint` as conforming with `Size assessment: standard`, yet Orders 02/03/04 each contained Order-sized E-items (append-only tamper-evident ledger; crash recovery; a 12-class evidence-validator suite); the maintainer had to ask twice before decomposition. A passing size lint measures count, not conceptual density per item. The fix is a human/agent JUDGMENT rubric in the review and authoring prose (this plan) complemented by a mechanical heuristic (Order 07).

## Proposed changes (ordered, validatable)

1. Right-sizing rubric in `/plan-review` (E-01) and `/plan-review-long` in parity (E-02).
2. One-concern-per-E-item authoring guidance in the assess harness, templates, and scaffold guidance (E-03).
3. A rule that a maintainer sizing question is a finding, not a dismissable non-issue (E-04).

## Deferred / out of scope (with reason)

- The mechanical lint heuristic flagging multi-deliverable E-items: Order 07 (code).
- Changing the numeric thresholds themselves: not needed; the gap is conceptual density, not the counts.

## Scope check

- Over-scope: none.
- Under-scope: keep the single-file and long variants in deliberate parity (the workflows state they are kept in parity), so the rubric wording matches.

## Required tests / validation

Workflow-prose change; validation is by inspection plus a dry-run: apply the new rubric to a known-dense historical IPD (e.g. an awoptimize order that bundled concerns) and confirm the rubric would flag it for splitting. Run any docs/workflow lint the repo has (e.g. `aw check` over workflows) and paste the output. No `aw ipd lint` behavior change is expected from this plan (that is Order 07).

## Spec / documentation sync

Update the IPD spec/authoring guidance references only if they enumerate the review checks. The CANONICAL "one concern / executable-in-one-focused-pass" definition lives in `plan-review.md` (E-01); plan-review-long, assess, and the templates copy it verbatim or reference it, and Order 07's mechanical heuristic MUST reuse that same definition. Naming one canonical home avoids six divergent copies drifting apart.

## Open questions

### OQ-01: Is a mechanical heuristic required for this item, or is the rubric enough?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: both are wanted; the backlog item lists the heuristic as a deliverable. This plan delivers the judgment rubric (a, d); Order 07 (`wb045s`) delivers the mechanical heuristic (b). They share one "one concern / executable-in-one-focused-pass" definition.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `plan-review.md` contains the per-E-item conceptual-density right-sizing check with a split recommendation; quote the added rubric lines.
  - Observed evidence: `.aw/system/workflows/plan-review/plan-review.md:384-391` contains: "- **Right-sizing and conceptual density (per E-item):** Evaluate whether each E-item addresses exactly **one concern** and is **executable in one focused pass**. A passing count-based size check (`aw ipd lint`) measures only structural count (>18 E-leaves / >5 groups), NOT conceptual density. For each IPD and each E-item, ask: (a) Does one E-item name multiple distinct deliverables or touch multiple independent code regions/files? (b) Does it bundle multiple independent test-surfaces (would it need several unrelated V-items)? (c) Could it be executed and verified as two or more independent passes? (d) Would a faster/weaker model lose focus/context executing it as one item? If YES to any diagnostic question, recommend splitting into smaller child IPDs (an UNDER-SCOPE / REPLAN finding)—a passing count-based size lint does NOT clear this." Verified by `tests/test_plan_review_parity.py`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: `plan-review-long/` carries the identical right-sizing check in parity; quote the added lines and cite the file.
  - Observed evidence: `.aw/system/workflows/plan-review-long/review-rubric.md:25-32` contains the identical right-sizing rubric text in parity, and `02-review-and-revise.md:75` includes `- enforce per-E-item right-sizing (one concern / executable-in-one-focused-pass; split multi-deliverable items);`. Verified by `tests/test_plan_review_parity.py`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the assess harness, both IPD templates, and the scaffold authoring guidance state "one concern per E-item; split when multiple deliverables/test-surfaces"; quote the added lines per file.
  - Observed evidence: `assess.md:124-129` and `156-159` state "Enforce right-sizing: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or touches multiple independent test-surfaces." `templates/ipd.md:24` and `orchestrator-ipd.md:24` include "Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces." in parity with `agent_workflows/ipd_authoring.py:53-58`. Verified by `tests/test_ipd_templates.py` and `tests/test_plan_review_parity.py`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: both review workflows state that a maintainer sizing question is a finding to investigate by decomposition; a dry-run applying the new rubric to a NAMED dense exemplar (an awoptimize Order 02/03/04 that bundled an append-only ledger / crash recovery / a 12-class evidence-validator into single E-items, per Findings) shows the rubric would flag it for splitting; quote the rule and describe the dry-run result against that named plan.
  - Observed evidence: Rule quoted from `plan-review.md:392` and `review-rubric.md:33`: "- **Maintainer sizing signals:** A maintainer's sizing or splitting question is an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed." and `02-review-and-revise.md:23-26`. Dry-run applied against historical plan `.aw/records/plans/superseded/20260821-awoptimize-02-7qs57e-run-ledger-and-evidence-contract.ipd.md`: E-03 bundled append-only storage, sequence numbers, hash chaining / tamper evidence, crash-safe recovery, redaction hooks, and corruption refusal; E-05 bundled 12 separate validator classes. Diagnostic questions (a), (b), (c), (d) all answer YES (multiple distinct deliverables touching distinct components, separate test surfaces, independent execution passes, and model attention overload). The rubric flags them as UNDER-SCOPE / REPLAN requiring decomposition into Orders 02, 03, 04, matching the actual maintainer decomposition decision.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: four small prose edits around one concern (a human/agent right-sizing judgment) across the review and authoring workflows; deliberately parallel to Order 07's mechanical heuristic.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved. `Depends on: none`.
2. Scope fence: touch only `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/*`, `.aw/system/workflows/assess/assess.md`, and `.aw/system/workflows/assess/templates/ipd.md` + `orchestrator-ipd.md` (the template text IS the scaffold authoring guidance). Do NOT change `ipd_schema.py`/`ipd_lint.py` (Order 07) and do NOT refactor `agent_workflows/ipd_authoring.py` scaffold code (at most a single guidance string if one genuinely lives there rather than in the template). This plan is PROSE/template only; if the rubric seems to need a code change, STOP and report.
3. Honesty rule (hard MUST): when you report a workflow/docs lint or the dry-run result, paste the ACTUAL output; never claim a check you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. Backlog `8iy2dk` is set to `done` only after BOTH Order 06 and Order 07 are executed; do not close it from this plan alone.
