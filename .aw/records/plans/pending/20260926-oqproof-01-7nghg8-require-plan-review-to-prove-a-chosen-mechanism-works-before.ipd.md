# IPD: Require plan review to prove a chosen mechanism works before resolving an open question with it

- Date: 2026-09-26
- Kind: child
- Concern: A reviewer can resolve a plan's open question by DESCRIBING a mechanism nobody has tried, and label the question `Owner: maintainer` when the reviewer made the choice, so a plan reads "approved, no open questions" while carrying an unworkable instruction that only execution discovers. Measured on plan `vtkfq8` (carrierauth-01): review measured the defect's cause (its F-6, F-7) but resolved OQ-03 as "emit a COMMENTED / inert placeholder that the gate does NOT read", which cannot work because the obligation comes from the example question's `- Status: open` (`check_engine._question_obligations`), not from a missing carrier line. The resolution even said "The executor must confirm the chosen form empirically ... if NO inert form can both suppress the obligation and stay unsatisfying, that is a genuine conflict", so the reviewer knew feasibility was unproven and still marked it resolved. Run `run-20260926T051642Z-116672` spent a 13m, 762k-token turn to learn it (item `vtkfq8`, `fail-verify`, deferred question `06-vtkfq8-DQ1`), and the maintainer had to re-rule OQ-03 (commit `35d72343`).
- Scope: IN: the plan-review workflow text (single-file `plan-review.md`, its long-form sibling `plan-review-long/03-resolve-and-finalize.md`, and the spec-review sibling `spec-review.md`, which inherits the same "resolve from evidence" step): (a) a question resolved by choosing a MECHANISM must cite a demonstration that the mechanism produces the required result, or it is not resolved; (b) where it cannot be demonstrated at review, the question stays open or becomes an explicit spike E-item with a stop condition, and the verdict states the feasibility risk; (c) `Owner: maintainer` only when the maintainer actually answered; (d) a behavioral test that the installed workflow text carries the rule. OUT: a lint rule that tries to judge whether a demonstration is real (see Deferred).
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, .aw/system/workflows/spec-review/spec-review.md, tests/test_plan_review_feasibility_rule.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: j4wz6b
- Blocks-Release: next
- Set: oqproof
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7nghg8

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog j4wz6b at the maintainer's request. Evidence re-read from plan vtkfq8's OQ-03 text, its review history, and run run-20260926T051642Z-116672's decisions-and-questions.md (06-vtkfq8-DQ1).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A plan that reaches `reviewed` with a question marked `resolved` by a chosen mechanism has evidence that the mechanism works, or else carries the uncertainty visibly (an open question or an explicit spike step) instead of hiding it inside a resolution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rule

- [ ] E-01 In `.aw/system/workflows/plan-review/plan-review.md` section "3.1 Build the question set", immediately after "Resolve questions from authoritative evidence first. Cite the source.", add a subsection `#### Resolving HOW questions: demonstrate, do not describe`. It must say, in substance: (1) a question is a HOW question when its resolution chooses a MECHANISM (a code shape, a placeholder form, a flag, an algorithm) rather than a fact or a scope; (2) a HOW question may be marked `resolved` only when the resolution cites a DEMONSTRATION that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row; (3) if the reviewer cannot demonstrate it, they MUST instead either leave the question `open` (with `Blocking: yes` when execution depends on it) or convert it into a first spike E-item whose Expected outcome is the demonstration and whose stop condition names the question, and the review verdict MUST name the feasibility risk; (4) a resolution containing its own "confirm empirically / if no form works, stop" clause is BY DEFINITION undemonstrated and falls under (3); (5) `- Owner: maintainer` on a resolved question means the maintainer answered; a reviewer's own choice records the reviewer (or `plan author`) as owner and gets a `### Decisions` row as 3.1 already requires. Cite the `vtkfq8` OQ-03 case as the measured example in one or two sentences.
  - Depends on: none
  - Expected outcome: the subsection exists in 3.1 and states all five points.
  - Execution state: pending

- [ ] E-02 Mirror E-01 in `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md` section "1. Resolve open questions", after "Resolve questions already answered by authoritative evidence and cite it.", by REFERENCE to the single-file text rather than a second full copy if the long form already defers to it elsewhere; otherwise copy the five points verbatim so the two forms cannot disagree. Record which you did in V-02 and why.
  - Depends on: E-01
  - Expected outcome: the long-form reviewer is bound by the same rule.
  - Execution state: pending

- [ ] E-03 In `.aw/system/workflows/spec-review/spec-review.md` "3.1 Build the question set", after "Resolve from authoritative evidence first and cite the source", add one short paragraph binding spec review to the same rule by reference to plan-review's new subsection (spec-review already defers shared rules to plan-review, per its "What is SHARED" table, so a reference is the correct form).
  - Depends on: E-01
  - Expected outcome: spec review references the rule; no second copy.
  - Execution state: pending

### Task group 2: test and changelog

- [ ] E-04 Add `tests/test_plan_review_feasibility_rule.py` asserting on the SHIPPED workflow files (read from the repo `.aw/system/workflows/` tree, the same tree the wheel force-includes per `pyproject.toml`): the plan-review subsection heading exists inside section 3.1; each of the five points is present (assert on a distinctive phrase per point, chosen in E-01 and listed in the test); the long form carries the rule or an explicit reference to the single-file subsection; spec-review references it. This is a documentation-contract test, the kind the repo already uses for workflow text; keep it to presence of the rule, not exact wording beyond the one anchor phrase per point.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the test passes, and FAILS with E-01's subsection removed.
  - Execution state: pending

- [ ] E-05 `CHANGELOG.md` unreleased entry in plain user-facing language, no dashes: plan reviews no longer mark a question answered by a fix nobody tried; an untried fix stays an open question or becomes a first test step.
  - Depends on: E-01
  - Expected outcome: one entry.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The workflow bundle ships from the repo `.aw/system/` tree (`pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` `".aw/system" = "agent_workflows/_data/.aw/system"`), so editing that tree edits what installs.
- `/plan-review` has a single-file form (`plan-review/plan-review.md`) and a long form (`plan-review-long/*.md`); a recent change to reviewer instructions touched both plus `spec-review.md` (commit `f9166bfb`, citesym `x7i14a`), which is the precedent for keeping them in step.
- `spec-review.md` defers shared machinery to plan-review by reference and forbids restating it ("Anything else you find duplicated here is a defect").
- plan-review 3.1 already requires a `### Decisions` row for every question a reviewer resolves itself, with `Basis` and `Reversible`; E-01 adds the demonstration requirement for HOW questions on top, not a new record.
- Workflow text is AI-facing, so the no-dash rule does not apply to it; it does apply to the CHANGELOG entry (AGENTS.md execution contract).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | plan `vtkfq8` OQ-03 | Resolved with a mechanism that cannot work; the resolution itself admitted feasibility was unconfirmed. | OQ-03 text: "Emit the carrier line as a COMMENTED / inert placeholder ... The executor must confirm the chosen form empirically"; run `run-20260926T051642Z-116672` `decisions-and-questions.md` 06-vtkfq8-DQ1: "Emitting an inert / commented placeholder ... does NOT suppress the obligation because `Status: open` remains active" |
| F-2 | MEDIUM | plan `vtkfq8` OQ-03 | `Owner: maintainer` on a resolution the reviewer chose. | OQ-03 said "it is the ruled intent rather than a reviewer's invention", citing the source backlog item's candidate list, which its own text calls "CANDIDATE SHAPES (not decided here)" (backlog `dtrect`) |
| F-3 | MEDIUM | `plan-review.md` 3.1 | No rule distinguishes a fact question (resolve by citation) from a mechanism question (resolve only by demonstration). | 3.1 text: "Resolve questions from authoritative evidence first. Cite the source." with no mechanism case |

## Proposed changes (ordered, validatable)

1. E-01: the rule in single-file plan-review 3.1 (F-3, F-1, F-2).
2. E-02: the long form, kept in step.
3. E-03: spec-review, by reference.
4. E-04: documentation-contract test.
5. E-05: changelog.

## Deferred / out of scope (with reason)

- A lint rule that flags a resolved question lacking a demonstration.
  - Carrier-Declined: whether a pasted snippet actually demonstrates a mechanism is a semantic judgement, which the IPD linter is deliberately kept out of (spec `ipd-structure-and-linting` Section 7: "The linter checks the declared fields and their consistency. The semantic reviewer decides"). A text heuristic (for example flagging "confirm empirically") would be trivially evaded and would train reviewers to avoid the phrase rather than the practice. The rule lives where the judgement is made.
- Re-auditing already-reviewed plans for undemonstrated resolutions.
  - Carrier-Declined: no retroactive sweep was requested; the rule applies at the next review of any plan, and the one measured instance (`vtkfq8`) is already re-ruled.

## Scope check

- Over-scope: none.
- Under-scope: none known; the spec-review mirror (E-03) is included because it shares the same "resolve from evidence" step and would otherwise keep the gap for specs.

## Required tests / validation

- `python3 -m pytest tests/test_plan_review_feasibility_rule.py -o addopts=""`, plus the removal check in V-04.
- Bare `python3 -m pytest`.
- `python3 -m agent_workflows check all --agent`, naming pre-existing findings as pre-existing.

## Spec / documentation sync

No spec amendment: the IPD structure spec already assigns semantic judgement to the reviewer (Section 7), and this plan changes only the reviewer's instructions. The workflow files are the documentation being changed; `CHANGELOG.md` gets one entry (E-05).

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new subsection as committed, with the five points identifiable, and `grep -n` output showing it sits inside section 3.1 of `plan-review.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the long-form change and state whether it references or copies the rule, with the reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the spec-review paragraph and show it references plan-review's subsection rather than restating the five points.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing test output, then the FAILING output with E-01's subsection temporarily removed, then the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the CHANGELOG entry.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <plan> -- <paths>` limited to `- Scope-Paths:`; never push. Finalize with `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence; the plan then moves to `.aw/records/plans/executed/`. On completion close backlog `j4wz6b` through the handoff (this plan carries `From-Backlog: j4wz6b` and its `Blocks-Release: next`).
