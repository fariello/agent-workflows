# IPD: Build Stage 1 of the runner-driven tiered plan review and run its pilot (spec k3yx72)

- Date: 2026-10-24
- Kind: orchestrator
- Concern: Spec `k3yx72` (approved 2026-10-24, `Blocks-Release: next`) replaces the single-turn `/plan-review` with a runner-driven sequence of review checks whose number scales with the plan's review tier. Review is about half of all recorded agent cost (spec Section 1). MD-20 stages the build: Stage 1 builds only what a pilot needs (spec Section 15 Orders 01, 02, 04, a minimal 05) and runs the pilot (Order 09); Stage 2 (Orders 03, 06, 07, 08, the rest of 05) is authored only if the pilot records BUILD THE REST. None of Stage 1 exists.
- Scope: Orchestration only: sequence the five Stage 1 children below and confirm each reaches `executed`. No code, test, or record of its own. Stage 2 plans are not part of this Set's table; Order 09 files the backlog item that carries them.
- Scope-Paths: .aw/records/plans/pending/20261024-revsteps-00-tiwj2o-build-stage-1-of-the-runner-driven-tiered-plan-review-and-ru.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: 5b9f1882704e5eb6d6bd8b9d30a8f5fd6c6abe0399e495a0d17e60260e3a1bcc
- Coverage-Checked: 2026-10-25 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Set: revsteps
- Order: 0
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tiwj2o

## Workflow history
- 2026-10-25 to-review (aw set): authored review-ready: orchestrates spec k3yx72 Stage 1 across 5 children; coverage pass

- 2026-10-25 coverage pass (aw oc run): fingerprint 5b9f1882704e, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Build Stage 1 of spec `k3yx72` as five independently executable children and run the pilot whose result decides whether Stage 2 is built.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM 3bwrfx REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans 3bwrfx` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM gv3smb REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans gv3smb` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM uiyoax REACHED executed
  - Depends on: E-01, E-02
  - Expected outcome: `aw find plans uiyoax` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM is2xiv REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans is2xiv` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM kk62qt REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans kk62qt` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `3bwrfx` | `20261024-revsteps-01-3bwrfx-split-plan-review-into-step-files-with-a-section-map-round-l.ipd.md` | Step files for every check, `/plan-review` as a checklist, old-to-new section map, round layout in the reviews README, five-level recommendation strength in `/askme` (spec 4.2, 4.3, 7.1, 17.3, 17.4). | none |
| 02 | `gv3smb` | `20261024-revsteps-02-gv3smb-add-the-review-depth-field-pre-pass-tier-facts-and-run-state.ipd.md` | `- Review-Depth:` field, pre-pass tier facts, `AW-TIER:` and tier-answer parsers, run-state recorder, `review_tier` analytics field (spec 4.1 item 4, 5.2, 7.2). | none |
| 04 | `uiyoax` | `20261024-revsteps-04-uiyoax-drive-a-plan-review-as-a-tiered-sequence-of-prompts-in-one-s.ipd.md` | Opt-in `--review-mode steps` on both hosts: pre-pass, per-tier prompt lists and `review_variant`, postconditions and re-ask, structural preservation, verdict-output guard, outcomes, sessions, per-step recording, resume, children-before-orchestrator review ordering, `25kzda` amendments (spec 4 to 7, 9, 17.1). | `executed:3bwrfx`, `executed:gv3smb` |
| 05 | `is2xiv` | `20261024-revsteps-05-is2xiv-add-the-aw-review-re-review-marker-runner-triggers-and-the-b.ipd.md` | Stage 1 part of Order 05: `AW-REVIEW` marker, runner triggers, the two-pass loop and its `no-go` limit rule (spec 8). | `executed:uiyoax` |
| 09 | `kk62qt` | `20261024-revsteps-09-kk62qt-run-the-review-pilot-against-the-current-plan-review-and-rec.ipd.md` | Attended pilot: 9 fixture plans, 84 reviews, 252 blind judge runs, the MD-20 gate decision, the `complex` default, and a Stage 2 backlog item when the gate says build (spec 13, AC-17). | `executed:uiyoax`, `executed:is2xiv` |

Orders 01 and 02 have no prerequisite and may run in either order. Order 04 depends on both. Order 05 depends on 04. Order 09 depends on 04 and 05 and is `Attended: required`, so the runner holds it for an interactive session. Orders 03, 06, 07 and 08 and the Section 9.4 part of Order 05 are Stage 2 (spec MD-20) and are deliberately absent from this table.

## Completion criteria (the whole Set is done only when)

- Every review check of spec Section 4.2 exists as a step file, `/plan-review` runs them as a checklist, and the section map shows nothing was lost. Owner: `3bwrfx`.
- A plan may carry `- Review-Depth:`, and the tier, its answers, and the pre-pass facts can be computed and recorded in run state. Owner: `gv3smb`.
- `aw oc run` and `aw agy run` can review a plan as the tier's prompt sequence in one session, with postconditions, the verdict guard, outcomes, per-step recording, and resume (AC-01, AC-02, AC-07 first half, AC-08, AC-14, AC-16). Owner: `uiyoax`.
- A steps-mode review re-reviews its own material edits at most twice before the verdict (AC-03 to AC-06, AC-07 second half). Owner: `is2xiv`.
- The pilot has run and its report records the MD-20 gate decision and the `complex` default (AC-17). Owner: `kk62qt`.

## Cross-IPD validation

- Step-file names used by the runner match the files Order 01 ships: `uiyoax` V-02 lists `.aw/system/workflows/plan-review/steps/` beside the rendered prompt.
- The tier recorder and parsers built by `gv3smb` are the ones `uiyoax` calls: `uiyoax` E-15 asserts AC-08 through the real `review_tier` functions.
- The re-review loop of `is2xiv` plugs into the delegation point `uiyoax` E-06 defines, and the verdict guard covers every pass: `is2xiv` E-06 asserts AC-06 and AC-07 second half.
- The pilot uses the build all four code children produced, from one commit: `kk62qt` E-04 creates every cell from the same commit.
- Each child's `V-*` items require the output of its own test modules and of the routine gate; post-merge revalidation is the runner's merge-and-revalidate gate on each child, not work of this plan.

## Deferred / out of scope (with reason)

- Stage 2 (spec Section 15 Orders 03, 06, 07, 08, and the Section 9.4 part of 05): authored only after `kk62qt` records BUILD THE REST (spec MD-20); `kk62qt` E-09 files the backlog item.
- The sized experiment run (spec Section 13.3 stage 2): only on the maintainer's request after the pilot, in its own plan carrying OQ-10 as `Blocking: yes`.
- Spec `4iyd78` (quick pipeline) Part 2 depends on this Set's Order 09 result; it is tracked under Set `quickpipe`, not here.

## Scope check

- Over-scope: none.
- Under-scope: none. Every Stage 1 Order of spec Section 15 has a child.

## Required tests / validation

This plan runs no tests. Each child runs its own suites; `kk62qt` performs the whole-Set measurement (the pilot).

## Open questions

### OQ-01: Should Stage 2 children be pre-declared in this Set's table now?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Spec MD-20 makes Stage 2 conditional on the pilot, and an orchestrator whose table declares an unauthored row is refused retirement by `runner_shared.find_unauthored_child_rows`. Stage 2 is carried by the backlog item `kk62qt` E-09 files. Recommendation strength: strong.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans 3bwrfx` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans gv3smb` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans uiyoax` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans is2xiv` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw find plans kk62qt` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). The runner retires this orchestrator once every child is `executed`. Commit only through `aw commit tiwj2o -- <paths>`; never push.
