# IPD: Point the authoring and review workflow bodies at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires every shipped workflow that writes, reviews, or revises a spec, backlog item, or plan to direct the agent to the writing standard, and R-04 adds its diagram requirement. Maintainer commit `0cbfcc706` shipped the standard at `.aw/system/workflows/technical-writing/technical-writing.md` and already added a pointer to `spec/spec.md`, `spec-review/spec-review.md`, `plan-review/plan-review.md`, `plan-review-long/plan-review-long.md`, and `research-prompt/research-prompt.md`. Still missing: `ipd-lifecycle/ipd-lifecycle.md`, `advise/personas/spec-editor.md`, the plan-review step files (`p-proofread.md` still applies prompt `wcisgc` with a fallback summary), and the `plan-review-long` rubric. No body mentions the diagram requirement (requirement 12, added by Order 01 `g4719s`), and two bodies say "all eleven" requirements, which becomes wrong once requirement 12 exists. Spec `k3yx72` non-goal N5 still limits proofreading to review time.
- Scope: Add the missing pointers; add the diagram check (requirement 12) to every authoring and review body; replace the requirement count in `spec.md` and `research-prompt.md` with count-free wording; point `plan-review/steps/p-proofread.md` at the standard's "Proofreading procedure" section; amend spec `k3yx72` N5 and its two `wcisgc` rows; add an install test that every pointer resolves. EXCLUDES the generators (Order 04), runner prompts (Order 05), the standard's own text (Order 01), and splitting or restructuring any workflow.
- Scope-Paths: .aw/system/workflows/spec/spec.md, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review/steps/p-proofread.md, .aw/system/workflows/plan-review/steps/_kernel.md, .aw/system/workflows/plan-review-long/plan-review-long.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md, .aw/system/workflows/advise/personas/spec-editor.md, .aw/system/workflows/research-prompt/research-prompt.md, .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md, tests/test_workflow_bodies_writing_standard.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s, executed:3bwrfx
- Status: to-review
- Readiness: go-pending-approval
- Review-Depth: standard
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
- 2026-11-05 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261025-writestd-06-e4n4p3-point-the-authoring-and-review-workflow-bodies-at-the-writin.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every interactive and runner-driven authoring and review workflow apply the shipped writing standard, including its diagram requirement, so the standard governs writing, proofreading, review, and revision alike.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Reference form for every edit: write the standard's path RELATIVE to the edited file, as the shipped pointers already do: `../technical-writing/technical-writing.md` from a file directly under a workflow directory, `../../technical-writing/technical-writing.md` from a file one level deeper (`plan-review/steps/`, `advise/personas/`). A relative path resolves in both install layouts (`.aw/system/workflows/` and legacy `.agents/workflows/`); a hard-coded `.aw/system/...` path does not.

### Task group 1: authoring bodies

- [ ] E-01 (spec `ecmw83` R-06, `ecmw83` R-04) In `spec/spec.md`, replace "check the complete draft against all eleven numbered requirements before you present it" with "check the complete draft against every numbered requirement, including requirement 12 (diagrams), before you present it", and add "Diagrams where requirement 12 of the writing standard applies (entities and relationships, flows and lifecycles)." as the last bullet of "## Spec structure". In `advise/personas/spec-editor.md`, add to "## Questioning style" one bullet: the persona asks whether the spec needs the entity or flow diagram that requirement 12 of `../../technical-writing/technical-writing.md` calls for, and whether each existing diagram agrees with the text. In `research-prompt/research-prompt.md`, replace "all eleven numbered requirements" with "every numbered requirement".
  - Depends on: none
  - Expected outcome: no workflow body contains "eleven"; `spec.md` and `spec-editor.md` mention requirement 12; `spec-editor.md` contains a resolving pointer.
  - Execution state: pending

- [ ] E-02 (spec `ecmw83` R-06) In `ipd-lifecycle/ipd-lifecycle.md`, section "## Execute", add one paragraph after the first: when an agent writes or revises plan text during execution (for example a re-scope or a new open question), it follows `../technical-writing/technical-writing.md`; it never rewrites recorded evidence, results, or `## Workflow history` entries to improve their wording.
  - Depends on: none
  - Expected outcome: `ipd-lifecycle.md` contains a resolving pointer and the evidence carve-out.
  - Execution state: pending

### Task group 2: review bodies

- [ ] E-03 (spec `ecmw83` R-06, `ecmw83` R-04) In `spec-review/spec-review.md`, extend the existing sentence that begins "Review the writing against the technical writing standard" to also require the diagram check of requirement 12. In "## Spec rubric", add one lettered subsection after the last existing one, "Writing and diagrams": the spec follows `../technical-writing/technical-writing.md`, including requirement 12; the reviewer fixes writing defects in place within its authority and records a finding where a fix would change meaning or where a required diagram is missing and cannot be drawn from the text alone.
  - Depends on: none
  - Expected outcome: the rubric subsection exists and names requirement 12.
  - Execution state: pending

- [ ] E-04 (spec `ecmw83` R-06) In `plan-review/steps/p-proofread.md`, replace the first two paragraphs (the instruction to apply prompt `wcisgc` and its seven-heading fallback summary) with: apply the "Proofreading procedure" section of `../../technical-writing/technical-writing.md` and its numbered requirements, including requirement 12 (diagrams). Keep every later section unchanged ("Structural Preservation Constraints", "Code Citations", "Review Record Subsection"). In `plan-review/steps/_kernel.md`, add item 10 to the "Memory kernel" list: review the plan's writing against `../../technical-writing/technical-writing.md`, and preserve meaning, obligations, and recorded evidence. In `plan-review/plan-review.md`, extend the existing sentence that begins "Review the plan's writing against the technical writing standard" with "including requirement 12 (diagrams)".
  - Depends on: none
  - Expected outcome: `p-proofread.md` names the procedure section and no longer contains `wcisgc`; `_kernel.md` contains a resolving pointer.
  - Execution state: pending

- [ ] E-05 (spec `ecmw83` R-06, `ecmw83` R-04) In `plan-review-long/02-review-and-revise.md`, add to the "## Required context" list the bullet "the technical writing standard (`../technical-writing/technical-writing.md`), including requirement 12 (diagrams);". In `plan-review-long/review-rubric.md`, add a final section "## I. Writing and diagrams" with the same check as E-03, worded for a plan. In `plan-review-long/plan-review-long.md`, extend kernel item 10 with "including requirement 12 (diagrams)".
  - Depends on: none
  - Expected outcome: all three `plan-review-long` files name the standard and requirement 12.
  - Execution state: pending

### Task group 3: spec amendment, test, and changelog

- [ ] E-06 Amend `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`: (1) non-goal N5 keeps its text and gains "Amended 2026-11-05: spec `ecmw83` now specifies a writing standard applied while drafting; see `.aw/system/workflows/technical-writing/technical-writing.md`."; (2) the Section 1 "Proofreading instructions" row names the "Proofreading procedure" section of that file, with prompt `wcisgc` as a pointer to it; (3) the section-map row "(new) proofreading" names that section instead of prompt `wcisgc`. Then run `aw specs note .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md --message "N5 and the two proofreading rows amended to the shipped writing standard (plan e4n4p3, spec ecmw83)"`. Do not change the spec's status.
  - Depends on: E-04
  - Expected outcome: the three locations name the standard; the spec carries one new history line and stays `approved`.
  - Execution state: pending

- [ ] E-07 (spec `ecmw83` R-06) Create `tests/test_workflow_bodies_writing_standard.py` (marker `core`). Follow the module-fixture pattern of `tests/test_plan_review_step_files.py`: install once with `run_cli("install", "-y", ...)` into an `init_repo` target. For each of the eleven installed workflow bodies in Scope-Paths, find every backticked reference ending in `technical-writing/technical-writing.md`, resolve it relative to that body's directory, and assert that at least one reference exists and that every one resolves to an existing file. Add one CHANGELOG line under the topmost pending heading, with no em or en dash.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the test passes, and it fails when a pointer is removed from a body or points at a missing path.
  - Execution state: pending

- [ ] E-08 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Workflow bodies are the installed source; command shims point at body paths and do not change here.
- Executed plan `3bwrfx` split `plan-review.md` into `steps/*.md` (`.aw/records/plans/executed/20261024-revsteps-01-3bwrfx-...`), so the `executed:3bwrfx` edge is satisfied.
- Shipped pointers use the relative form (`.aw/system/workflows/spec/spec.md` "Write the spec to the technical writing standard"); the managed `AGENTS.md` pointer uses the layout's root (`engine.agents_pointer_prose`, `agent_workflows/engine.py:1501`).
- Tests exercise behavior (GUIDING_PRINCIPLES P16). E-07 asserts that every delivered pointer resolves in an installed repository, which is a link-integrity outcome, following `tests/test_technical_writing_delivery.py` (which asserts the installed `AGENTS.md` names the standard).

## Findings

- Commit `0cbfcc706` already added a standard pointer to `spec.md`, `spec-review.md`, `plan-review.md`, `plan-review-long.md`, and `research-prompt.md`. This plan adds only what is missing and does not duplicate those lines.
- `.aw/system/workflows/spec/spec.md` "all eleven numbered requirements before you present it" and `.aw/system/workflows/research-prompt/research-prompt.md` "check it against all eleven numbered requirements" fix a count. Order 01 (`g4719s` E-02) adds requirement 12 and fixes the count only inside the standard, so E-01 removes the count here.
- `p-proofread.md` applies `wcisgc` and carries a fallback summary because `.aw/records/` is not shipped. After Order 01 the procedure ships inside the standard, so E-04 removes the fallback.
- Spec `k3yx72` names `wcisgc` in two rows (Section 1 table, section map) and limits writing rules to review time (N5). E-06 amends all three.

## Proposed changes (ordered, validatable)

1. Authoring bodies (E-01, E-02).
2. Review bodies (E-03 to E-05).
3. Amend `k3yx72`, test, changelog (E-06, E-07).
4. Gate and commit (E-08).

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none. `research-prompt.md` is outside R-06's list but is added because its requirement count would become wrong (E-01).

## Required tests / validation

`tests/test_workflow_bodies_writing_standard.py`, `tests/test_plan_review_step_files.py`, `tests/test_technical_writing_delivery.py`, the bare suite.

## Spec / documentation sync

Amends approved spec `k3yx72` (N5 and its two `wcisgc` rows), declared in Scope-Paths, because that spec would otherwise still name `wcisgc` as the procedure and exclude drafting-time writing rules, contradicting spec `ecmw83` and the shipped standard.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff` of `spec/spec.md`, `advise/personas/spec-editor.md`, and `research-prompt/research-prompt.md`, and `grep -rn eleven .aw/system/workflows --include=*.md` printing no line outside `technical-writing/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` showing the paragraph under "## Execute".
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff .aw/system/workflows/spec-review/spec-review.md` showing the new rubric subsection.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff .aw/system/workflows/plan-review/`, and `grep -c wcisgc .aw/system/workflows/plan-review/steps/p-proofread.md` printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff .aw/system/workflows/plan-review-long/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff` of the `k3yx72` spec, the `aw specs note` output, and `grep -n -- '- Status:' <spec>` showing `approved`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_workflow_bodies_writing_standard.py tests/test_plan_review_step_files.py tests/test_technical_writing_delivery.py` with every test PASSED; then the run of the new test after temporarily deleting the pointer line from `ipd-lifecycle.md` showing FAILED, and the restored PASSED run; and `git diff --stat CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved, and only after Order 01 `g4719s` is `executed` (its edge enforces this; it adds requirement 12 and the "Proofreading procedure" section this plan points to). Before editing any spec or plan, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit e4n4p3 -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize e4n4p3` itself.
