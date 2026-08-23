# IPD: IPD Right-Sizing Rubric in Review Workflows and Authoring Guidance

- Date: 2026-08-22
- Kind: child
- Concern: A passing `aw ipd lint` size check measures COUNT (>18 E-leaves / >5 groups), not conceptual density; Order-sized E-items slip through as "Size assessment: standard", degrading a real agent's context/attention/execution.
- Scope: The prose rubric in `/plan-review`, `/plan-review-long`, and the assess IPD-producing harness, plus `aw ipd scaffold` authoring guidance; NO code heuristic here (that is Order 07).
- Status: draft
- Set: highpbacklog0822
- Order: 6
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: por1hi

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog 8iy2dk (part 1 of 2); root cause was the awoptimize Set passing size lint while Orders 02/03/04 each held Order-sized E-items.

## Goal

Add an explicit "one concern / executable-in-one-focused-pass per E-item" right-sizing judgment to the review and authoring workflows, so reviewers and authors catch conceptually-dense IPDs that a count-based lint misses, and treat a maintainer's sizing question as a finding to investigate by decomposition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Review-workflow rubric

- [ ] E-01 Add a per-E-item conceptual-density right-sizing rubric check to `.aw/system/workflows/plan-review/plan-review.md`: for each IPD, judge not just the mechanical size lint but whether any single E-item or the whole plan bundles multiple independently-verifiable concerns, and recommend splitting into smaller child IPDs when so (an UNDER-SCOPE/REPLAN-style finding).
  - Depends on: none
  - Expected outcome: `/plan-review` explicitly evaluates conceptual density, not just count.
  - Execution state: pending

- [ ] E-02 Add the same right-sizing rubric to `.aw/system/workflows/plan-review-long/` (its `02-review-and-revise.md` and/or `review-rubric.md`), keeping deliberate parity with the single-file variant.
  - Depends on: none
  - Expected outcome: the long/parallel variant applies the identical right-sizing check.
  - Execution state: pending

### Task group 2: Authoring guidance

- [ ] E-03 Add "one concern per E-item; split when an E-item names multiple deliverables/test-surfaces" guidance to the assess IPD-producing harness (`.aw/system/workflows/assess/assess.md`) and the IPD templates (`.aw/system/workflows/assess/templates/ipd.md`, `orchestrator-ipd.md`), and to the `aw ipd scaffold` authoring guidance so newly-scaffolded plans are pushed toward one-concern E-items.
  - Depends on: none
  - Expected outcome: authored/scaffolded IPDs are steered toward one-concern E-items from the start.
  - Execution state: pending

### Task group 3: Maintainer-signal rule

- [ ] E-04 Add an explicit rule to `/plan-review` and `/plan-review-long` that a maintainer's sizing/splitting question is a FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed.
  - Depends on: E-01, E-02
  - Expected outcome: reviewers treat a human sizing concern as an investigation trigger, not a lint-cleared non-issue.
  - Execution state: pending

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

Update the IPD spec/authoring guidance references only if they enumerate the review checks; keep the "one concern per E-item" definition identical across plan-review, plan-review-long, assess, and scaffold guidance (Order 07 must reuse the same definition).

## Open questions

### OQ-01: Is a mechanical heuristic required for this item, or is the rubric enough?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: both are wanted; the backlog item lists the heuristic as a deliverable. This plan delivers the judgment rubric (a, d); Order 07 (`wb045s`) delivers the mechanical heuristic (b). They share one "one concern / executable-in-one-focused-pass" definition.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `plan-review.md` contains the per-E-item conceptual-density right-sizing check with a split recommendation; quote the added rubric lines.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `plan-review-long/` carries the identical right-sizing check in parity; quote the added lines and cite the file.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the assess harness, both IPD templates, and the scaffold authoring guidance state "one concern per E-item; split when multiple deliverables/test-surfaces"; quote the added lines per file.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: both review workflows state that a maintainer sizing question is a finding to investigate by decomposition; a dry-run against a known-dense IPD shows the rubric would flag it; quote the rule and describe the dry-run result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: four small prose edits around one concern (a human/agent right-sizing judgment) across the review and authoring workflows; deliberately parallel to Order 07's mechanical heuristic.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved. `Depends on: none`.
2. Scope fence: touch only `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/*`, `.aw/system/workflows/assess/assess.md`, `.aw/system/workflows/assess/templates/ipd.md` + `orchestrator-ipd.md`, and the `aw ipd scaffold` authoring-guidance text. Do NOT change `ipd_schema.py`/`ipd_lint.py` code here (that is Order 07). If the rubric seems to need a code change, STOP and report.
3. Honesty rule (hard MUST): when you report a workflow/docs lint or the dry-run result, paste the ACTUAL output; never claim a check you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. Backlog `8iy2dk` is set to `done` only after BOTH Order 06 and Order 07 are executed; do not close it from this plan alone.
