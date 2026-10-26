# IPD: Point the authoring and review workflow bodies at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires every shipped workflow that writes, reviews, or revises a spec, backlog item, or plan to direct the agent to the writing standard and to its diagram requirement. Today `spec/spec.md`, `spec-review/spec-review.md`, `plan-review` (being split into `steps/*.md` by approved plan `3bwrfx`), `plan-review-long`, `ipd-lifecycle/ipd-lifecycle.md`, and `advise/personas/spec-editor.md` do not. Spec `k3yx72` non-goal N5 says the proofreading instructions apply at review time only, which this Set changes.
- Scope: Add a read-and-follow instruction to each named body; make the reviewer bodies check diagram need (R-04) and meaning preservation; point `plan-review/steps/p-proofread.md` at the standard's proofreading section; amend spec `k3yx72` N5 and its proofreading-instructions row. EXCLUDES the generators (Order 04), runner prompts (Order 05), and splitting or restructuring any workflow.
- Scope-Paths: .aw/system/workflows/spec/spec.md, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review/steps/*.md, .aw/system/workflows/plan-review-long/plan-review-long.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md, .aw/system/workflows/advise/personas/spec-editor.md, .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md, tests/test_workflow_bodies_writing_standard.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s, executed:3bwrfx
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 6
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: e4n4p3

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every interactive and runner-driven authoring and review workflow apply the writing standard, so the standard governs writing, proofreading, review, and revision alike.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: authoring bodies

- [ ] E-01 In `spec/spec.md`, add to the protocol, before the step that writes the file, a step: read `.aw/system/workflows/standards/technical-artifact-writing.md`; write the spec per it; add the diagrams requirement 12 calls for (entities and relationships, flows and lifecycles); proofread against every numbered requirement before showing the draft. Add "Diagrams where requirement 12 applies" to the "Spec structure" list. Make the matching addition to `advise/personas/spec-editor.md` as a question the persona asks.
  - Depends on: none
  - Expected outcome: both bodies name the standard and requirement 12.
  - Execution state: pending

- [ ] E-02 In `ipd-lifecycle/ipd-lifecycle.md`, add to the authoring and revision guidance one instruction: an agent that writes or revises a plan, including a re-scope during execution, follows `.aw/system/workflows/standards/technical-artifact-writing.md`; it never rewrites recorded evidence, results, or history.
  - Depends on: none
  - Expected outcome: the body names the standard and the evidence carve-out.
  - Execution state: pending

### Task group 2: review bodies

- [ ] E-03 In `spec-review/spec-review.md`, add to the rubric a check: the spec follows `.aw/system/workflows/standards/technical-artifact-writing.md` (writing and requirement 12); the reviewer fixes writing defects in place within its authority and records a finding where a fix would change meaning or where a required diagram is missing and cannot be drawn from the text. Add the read-the-standard instruction to its preamble.
  - Depends on: none
  - Expected outcome: the rubric row exists.
  - Execution state: pending

- [ ] E-04 In `plan-review/steps/p-proofread.md` (created by `3bwrfx` E-03), replace the instruction to apply prompt `wcisgc` with: apply the "Proofreading procedure" section of `.aw/system/workflows/standards/technical-artifact-writing.md`, and check requirement 12. Replace its fallback summary of `wcisgc` with a pointer to the same shipped file, because the standard now ships and the fallback is no longer needed. Keep every other rule of that step. In `plan-review/steps/_kernel.md`, add one line naming the standard. If `3bwrfx` has not created these files (its status is not `executed`), STOP: the dependency gate should have prevented this.
  - Depends on: none
  - Expected outcome: `p-proofread.md` names the standard and no longer names `wcisgc`.
  - Execution state: pending

- [ ] E-05 In `plan-review-long/02-review-and-revise.md` and `review-rubric.md`, add the same writing-standard check as a rubric item, and name the standard in `plan-review-long.md`'s kernel. If `plan-review/plan-review.md` still carries any rubric text after `3bwrfx`, add the same one-line pointer there.
  - Depends on: none
  - Expected outcome: both plan reviewers name the standard.
  - Execution state: pending

### Task group 3: spec amendment and test

- [ ] E-06 Amend `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`: change non-goal N5 to say a writing standard applied while drafting is now specified by spec `ecmw83`; change the "Proofreading instructions" row to name the "Proofreading procedure" section of `.aw/system/workflows/standards/technical-artifact-writing.md` (with `wcisgc` as a pointer to it). Record the amendment with `aw specs note k3yx72 --message ...`.
  - Depends on: E-04
  - Expected outcome: the spec names the standard and carries the note.
  - Execution state: pending

- [ ] E-07 Create `tests/test_workflow_bodies_writing_standard.py` (marker `core`): install the toolkit into a temporary repository and assert that each installed body named in Scope-Paths (except the spec file) contains the standard's path, and that the path exists in that repository. Add a CHANGELOG entry.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the test passes.
  - Execution state: pending

- [ ] E-08 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Workflow bodies are the installed source; no generated copies to sync except command shims, which point at body paths and do not change here.
- Pending plan `3bwrfx` owns the split of `plan-review.md`; this plan edits the step files only after it executes (`- Item-Dependencies: executed:3bwrfx`).

## Findings

- `3bwrfx` E-03 tells `p-proofread.md` to cite `wcisgc` by path and carry a fallback summary because `.aw/records/` is not shipped. Order 01 of this Set ships the procedure, so E-04 here removes the fallback.

## Proposed changes (ordered, validatable)

1. Authoring bodies (E-01, E-02).
2. Review bodies (E-03 to E-05).
3. Amend `k3yx72` and test (E-06, E-07).
4. Gate and commit (E-08).

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_workflow_bodies_writing_standard.py`, `tests/test_plan_review_step_files.py`, the bare suite.

## Spec / documentation sync

Amends spec `k3yx72` (`.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`) N5 and its proofreading-instructions row, declared in Scope-Paths, because that spec would otherwise still name `wcisgc` as the procedure and exclude drafting-time writing rules.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff .aw/system/workflows/spec/spec.md .aw/system/workflows/advise/personas/spec-editor.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff .aw/system/workflows/spec-review/spec-review.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff .aw/system/workflows/plan-review/steps/` and `grep -c wcisgc .aw/system/workflows/plan-review/steps/p-proofread.md` printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff .aw/system/workflows/plan-review-long/ .aw/system/workflows/plan-review/plan-review.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff` of the spec and the `aw specs note` output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_workflow_bodies_writing_standard.py tests/test_plan_review_step_files.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit e4n4p3 -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
