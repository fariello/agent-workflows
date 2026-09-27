# IPD: Require plan review to prove a chosen mechanism works before resolving an open question with it

- Date: 2026-09-26
- Kind: child
- Concern: A reviewer can resolve a plan's open question by DESCRIBING a mechanism nobody has tried, and label the question `Owner: maintainer` when the reviewer made the choice, so a plan reads "approved, no open questions" while carrying an unworkable instruction that only execution discovers. Measured on plan `vtkfq8` (carrierauth-01): review measured the defect's cause (its F-6, F-7) but resolved OQ-03 as "emit a COMMENTED / inert placeholder that the gate does NOT read", which cannot work because the obligation comes from the example question's `- Status: open` (`check_engine._question_obligations`), not from a missing carrier line. The resolution even said "The executor must confirm the chosen form empirically ... if NO inert form can both suppress the obligation and stay unsatisfying, that is a genuine conflict", so the reviewer knew feasibility was unproven and still marked it resolved. Run `run-20260926T051642Z-116672` spent a 13m, 762k-token turn to learn it (item `vtkfq8`, `fail-verify`, deferred question `06-vtkfq8-DQ1`), and the maintainer had to re-rule OQ-03 (commit `35d72343`).
- Scope: IN: the plan-review workflow text (single-file `plan-review.md`, its long-form sibling `plan-review-long/03-resolve-and-finalize.md`, and the spec-review sibling `spec-review.md`, which inherits the same "resolve from evidence" step): (a) a question resolved by choosing a MECHANISM must cite a demonstration that the mechanism produces the required result, or it is not resolved; (b) where it cannot be demonstrated at review, the question stays open or becomes an explicit spike E-item with a stop condition, and the verdict states the feasibility risk; (c) `Owner: maintainer` only when the maintainer actually answered; (d) a behavioral test that the installed workflow text carries the rule. OUT: a lint rule that tries to judge whether a demonstration is real (see Deferred).
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, .aw/system/workflows/spec-review/spec-review.md, tests/test_plan_review_feasibility_rule.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: j4wz6b
- Blocks-Release: next
- Set: oqproof
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7nghg8
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED. The vtkfq8 case verified verbatim and all three insertion points confirmed at HEAD 78a40cc9. PR-002 is the self-application finding: E-01 point (3) prescribed a fallback nobody had tried, so it was RUN, inserting a Blocking: yes question into this plan flipped ipd_lint from conforming to error at all three checkpoints with IPD-Q501, and the rule now states that. PR-001: E-02's reference-or-copy conditional measured to COPY (the long form references nothing in 246 lines and duplicates the sibling Decisions rule), now mandated with a parity pointer. PR-003: E-04 split into E-04 + E-06 via aw ipd sync, clearing the IPD-Z602 advisory, with both negative controls required. PR-004 records the 96xtmi text-pin exemption and the verified scope completeness; PR-005 states that no gate checks Owner. Findings and decisions D-1..D-4 in .aw/records/reviews/20260926-oqproof-01-7nghg8-require-plan-review-to-prove-a-chosen-mechanism-works-before.review.md

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog j4wz6b at the maintainer's request. Evidence re-read from plan vtkfq8's OQ-03 text, its review history, and run run-20260926T051642Z-116672's decisions-and-questions.md (06-vtkfq8-DQ1).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A plan that reaches `reviewed` with a question marked `resolved` by a chosen mechanism has evidence that the mechanism works, or else carries the uncertainty visibly (an open question or an explicit spike step) instead of hiding it inside a resolution.

THIS PLAN'S OWN ESCAPE ROUTE IS DEMONSTRATED, NOT ASSERTED, because a rule that prescribes an unproven fallback would commit the very defect it exists to stop (added at review, PR-002). E-01 point (3) tells a reviewer who cannot demonstrate a mechanism to leave the question `open` with `- Blocking: yes`. That instruction is only worth giving if such a question actually HOLDS the plan, so it was executed at review against this very plan's text: inserting one `- Blocking: yes` / `- Status: open` question turned `aw ipd lint`'s disposition from `conforming` to `error` at ALL THREE checkpoints, with the diagnostic `IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer`. The unmodified plan is `conforming` at `author`. So the fallback is mechanically load-bearing at author time and not merely advisory.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rule

- [x] E-01 In `.aw/system/workflows/plan-review/plan-review.md` section "3.1 Build the question set", immediately after "Resolve questions from authoritative evidence first. Cite the source.", add a subsection `#### Resolving HOW questions: demonstrate, do not describe`. It must say, in substance: (1) a question is a HOW question when its resolution chooses a MECHANISM (a code shape, a placeholder form, a flag, an algorithm) rather than a fact or a scope; (2) a HOW question may be marked `resolved` only when the resolution cites a DEMONSTRATION that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row; (3) if the reviewer cannot demonstrate it, they MUST instead either leave the question `open` (with `Blocking: yes` when execution depends on it) or convert it into a first spike E-item whose Expected outcome is the demonstration and whose stop condition names the question, and the review verdict MUST name the feasibility risk. STATE WHY THE FIRST BRANCH BITES, since a reviewer who thinks it is merely advisory will not use it: an open question carrying `- Blocking: yes` makes `aw ipd lint` report `error` with `IPD-Q501` at EVERY checkpoint including `author`, so the plan cannot reach `approved` or be dispatched until a human answers. Verified at review by inserting such a question into this plan: disposition went `conforming` -> `error` at `author`, `review-finalize` and `pre-execution` alike; (4) a resolution containing its own "confirm empirically / if no form works, stop" clause is BY DEFINITION undemonstrated and falls under (3); (5) `- Owner: maintainer` on a resolved question means the maintainer answered; a reviewer's own choice records the reviewer (or `plan author`) as owner and gets a `### Decisions` row as 3.1 already requires. Write point (5) so a HUMAN applies it, and say plainly that NO GATE CHECKS IT: the linter only verifies the `Owner` field is non-empty and not `none` (`ipd_lint`'s `has_owner`, passed to `ipd_schema.open_question_error` as a bare boolean that never sees the VALUE), so a false `Owner: maintainer` passes every mechanical check, which is exactly how F-2's measured instance survived (F-5). Cite the `vtkfq8` OQ-03 case as the measured example in one or two sentences.
  - Depends on: none
  - Expected outcome: the subsection exists in 3.1 and states all five points.
  - Execution state: performed

- [x] E-02 Mirror E-01 in `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md` section "1. Resolve open questions", after "Resolve questions already answered by authoritative evidence and cite it.". COPY the five points; do NOT write a bare cross-file reference. The conditional this item used to carry ("by REFERENCE ... if the long form already defers to it elsewhere") was RESOLVED AT REVIEW BY MEASUREMENT (PR-001) and the answer is that it does not: `03-resolve-and-finalize.md` contains exactly ONE reference to another file in its 246 lines (`Read report-template.md in full and use it exactly.`) and NO reference to `../plan-review/plan-review.md` at all, and it fully DUPLICATES the `### Decisions` rule including the `Reversible` judgement rather than pointing at it. So copying is what this file's established shape requires. Follow the parity convention the bundle already uses for exactly this case: state the rule in full, then add the pointer sentence naming the single-file form as the parity twin, as `plan-review-long.md`'s Readiness bullet does ("this is kept identical to the single-file `../plan-review/plan-review.md` per the parity note above"). That pointer is what makes a future divergence visible.
  - Depends on: E-01
  - Expected outcome: the long-form reviewer is bound by the same five points, stated in full, with a parity pointer to the single-file subsection.
  - Execution state: performed

- [x] E-03 In `.aw/system/workflows/spec-review/spec-review.md` "3.1 Build the question set", after "Resolve from authoritative evidence first and cite the source", add one short paragraph binding spec review to the same rule by reference to plan-review's new subsection (spec-review already defers shared rules to plan-review, per its "What is SHARED" table, so a reference is the correct form).
  - Depends on: E-01
  - Expected outcome: spec review references the rule; no second copy.
  - Execution state: performed

### Task group 2: test and changelog

- [x] E-04 Add `tests/test_plan_review_feasibility_rule.py` covering the SINGLE-FILE rule: read `.aw/system/workflows/plan-review/plan-review.md` from the repo `.aw/system/` tree (the tree the wheel force-includes, `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` `".aw/system" = "agent_workflows/_data/.aw/system"`), assert the new `####` subsection heading exists and sits INSIDE section 3.1, and assert each of the five points is present via one distinctive anchor phrase per point (the five phrases chosen in E-01 and listed once at the top of the test module). Locate the section by HEADING BOUNDARIES, not by line number: take the span from the `### 3.1 ` heading to the next `### ` heading and assert the `####` heading falls within it. Measured at review: `plan-review.md` has `### 3.1 Build the question set` followed by `### 3.2 Ask interactively`, and the file already uses `####` subsections in two places, so the heading level and the boundary method are both established.

  THIS TEST IS EXPLICITLY OUTSIDE THE SOURCE-TEXT-PIN PROHIBITION, verified at review (PR-004) rather than assumed, because the concurrent plan `96xtmi` (srcguard-01) is deleting text-pinning tests under the maintainer's 2026-09-26 ruling and a new one would be born condemned. That plan's own `- Scope:` excludes "tests that read NON-production files (specs, workflow bodies, READMEs, the test module's own file) unless the census flags them as reading `agent_workflows/*`". A workflow body is a WORKFLOW BODY, the artifact under change, and this test reads no `agent_workflows/*` source, so it is out of scope for that deletion. Cite that exemption in the test module's docstring so a future census reader does not have to re-derive it.
  - Depends on: E-01
  - Expected outcome: the test passes, and FAILS with E-01's subsection removed.
  - Execution state: performed

- [x] E-06 Extend `tests/test_plan_review_feasibility_rule.py` to the TWO SIBLING files, which are a different surface with a different assertion shape: the long form (`plan-review-long/03-resolve-and-finalize.md`) carries the five points IN FULL plus a parity pointer naming the single-file form, and `spec-review/spec-review.md` REFERENCES plan-review's subsection WITHOUT restating the five points. Assert the spec-review case in BOTH directions, since the interesting failure is a copy rather than an absence: the reference is present AND at most one of the five anchor phrases appears there (spec-review's own rule is "Anything else you find duplicated here is a defect; fix it by deleting the copy"). Split from E-04 at review (PR-003) because the lint density check flagged the combined item and because these two files' assertions can only be written after E-02 and E-03 land, while E-04's can be written after E-01.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: both sibling assertions pass; the spec-review no-copy assertion FAILS if the five points are pasted into `spec-review.md`, and the long-form assertion FAILS if only a bare reference is written there.
  - Execution state: performed

- [x] E-05 `CHANGELOG.md` unreleased entry in plain user-facing language, no dashes: plan reviews no longer mark a question answered by a fix nobody tried; an untried fix stays an open question or becomes a first test step.
  - Depends on: E-01
  - Expected outcome: one entry.
  - Execution state: performed

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
| F-3 | MEDIUM | `plan-review.md` 3.1 | No rule distinguishes a fact question (resolve by citation) from a mechanism question (resolve only by demonstration). | 3.1 text: "Resolve questions from authoritative evidence first. Cite the source." with no mechanism case. CONFIRMED AT REVIEW: `rg 'HOW question|mechanism' plan-review.md` finds only three unrelated rubric lines ("existing canonical mechanisms", "reuse existing mechanisms", "existing mechanisms to reuse"); no rule of this kind exists. |
| F-4 | INFO (added at review, PR-002) | `ipd_lint` / `ipd_schema` | E-01 point (3)'s first branch is MECHANICALLY LOAD-BEARING, not advisory, which is what makes the fallback an honest instruction rather than a second undemonstrated mechanism. Demonstrated, not assumed. | Inserted one `- Blocking: yes` / `- Status: open` question into this plan's own text and ran the real linter: disposition `conforming` -> `error` at `author`, `review-finalize` AND `pre-execution`, diagnostic `IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer`. The `author`-onward reach is deliberate: the comment above the check records that the narrow `pre-execution`-only version was "measured insufficient on 2026-09-08". |
| F-5 | LOW (added at review, PR-005) | `ipd_lint.check` open-question rule / `ipd_schema.open_question_error` | E-01 point (5) (`Owner: maintainer` only when the maintainer answered) is REVIEWER JUDGEMENT ONLY and no gate can catch a violation, so the rule must be written to be read and applied by a human rather than relied on as enforced. The `Owner` field is free text: the linter checks only that it is non-empty and not `none` (`has_owner`), and `open_question_error` receives just that boolean, never the value. This is not a defect to fix here (an `Owner` enum would be a schema change well outside this plan), but stating it prevents a false sense of coverage. | `ipd_lint` computes `has_owner = bool(oq.get("Owner","").strip()) and ... != "none"`; `ipd_schema.open_question_error(blocking, status, has_rationale, has_owner)` takes no owner VALUE; `ipd_authoring` seeds `- Owner: none`. F-2's measured violation on `vtkfq8` therefore passed every gate. |
| F-7 | MEDIUM (added at review, PR-001) | `plan-review-long/03-resolve-and-finalize.md` | E-02's conditional ("by REFERENCE ... if the long form already defers to it elsewhere; otherwise copy") resolves to COPY, and leaving the executor to decide invited the wrong branch. That file defers to nothing: in 246 lines it carries exactly ONE cross-file reference (`Read report-template.md in full and use it exactly.`) and NO mention of `../plan-review/plan-review.md`, and it DUPLICATES the `### Decisions` rule in full including the `Reversible` judgement section. The bundle's convention for this case is state-in-full-plus-parity-pointer, as `plan-review-long.md`'s Readiness bullet shows ("this is kept identical to the single-file `../plan-review/plan-review.md` per the parity note above"). | `rg '\.\./|\.md' 03-resolve-and-finalize.md` -> one hit, line 231; `rg 'plan-review/plan-review.md' 03-resolve-and-finalize.md` -> no hits; `rg 'Decisions\|Reversible' 03-resolve-and-finalize.md` -> lines 24, 27, 36, 45, 47, 53, 65; parity language at `plan-review.md` line 17 and `plan-review-long.md` lines 7, 93. |
| F-8 | INFO (added at review, PR-004) | `tests/` and concurrent plan `96xtmi` (srcguard-01) | E-04's test would be born condemned unless it is provably outside the source-text-pin prohibition, and it IS. Plan `96xtmi` is deleting text-pinning tests under the maintainer's 2026-09-26 ruling, but its own `- Scope:` excludes "tests that read NON-production files (specs, workflow bodies, READMEs, the test module's own file) unless the census flags them as reading `agent_workflows/*`". This test reads a workflow body and no `agent_workflows/*` source, so it is exempt. Worth recording in the test's docstring so a future census reader does not re-litigate it. | `96xtmi`'s `- Scope:` line, quoted verbatim; `96xtmi` `- Status: to-review` (concurrent, not yet executed). |
| F-6 | INFO (added at review, PR-004) | scope completeness across the workflow bundle | The plan's three-file scope is COMPLETE for this rule, verified rather than assumed. The `citesym` precedent (`f9166bfb`) touched a fourth and fifth file (`verify-execution.md`, `plan-review-long/01` and `/02`), so the natural worry is an omitted sibling. None of them carries a question-resolution step: `verify-execution.md`'s only `question` hits are its GO/NO-GO prose and a corrective-plan clause, and `plan-review-long/01` and `/02` have no "resolve questions" section at all (`rg 'Resolve.*question|question set'` returns nothing in both). So `03-resolve-and-finalize.md` is the long form's only home for this rule. | `rg 'question|resolve' verify-execution.md` -> lines 154, 176 only; `rg 'Resolve.*question\|question set' 01-discover-and-snapshot.md 02-review-and-revise.md` -> no matches; `git show f9166bfb --stat` for the file list. |

## Proposed changes (ordered, validatable)

1. E-01: the rule in single-file plan-review 3.1 (F-3, F-1, F-2), with point (3)'s first branch stated as the mechanically load-bearing one (F-4) and point (5) stated as unenforced-by-design (F-5).
2. E-02: the long form, points stated IN FULL plus a parity pointer (measured: that file references nothing and duplicates the sibling Decisions rule, F-7).
3. E-03: spec-review, by reference only.
4. E-04: documentation-contract test for the single-file rule; E-06: the two sibling files, with both negative controls.
5. E-05: changelog.

## Deferred / out of scope (with reason)

- A lint rule that flags a resolved question lacking a demonstration.
  - Carrier-Declined: whether a pasted snippet actually demonstrates a mechanism is a semantic judgement, which the IPD linter is deliberately kept out of (spec `ipd-structure-and-linting` Section 7: "The linter checks the declared fields and their consistency. The semantic reviewer decides"). A text heuristic (for example flagging "confirm empirically") would be trivially evaded and would train reviewers to avoid the phrase rather than the practice. The rule lives where the judgement is made.
- Re-auditing already-reviewed plans for undemonstrated resolutions.
  - Carrier-Declined: no retroactive sweep was requested; the rule applies at the next review of any plan, and the one measured instance (`vtkfq8`) is already re-ruled.

## Scope check

- Over-scope: none.
- Under-scope: none known, and this was CHECKED AT REVIEW rather than asserted (F-6). The `citesym` precedent touched two files this plan does not (`verify-execution.md`, `plan-review-long/01` and `/02`), but none of them has a question-resolution step, so `03-resolve-and-finalize.md` is the long form's only home for this rule and the three declared workflow files are the complete set.
- Scope-Paths note: `tests/test_plan_review_feasibility_rule.py` is the only NEW file and is written by E-04 then extended by E-06; no second module is created. No `.spec.md` is in `- Scope-Paths:`, so this run declares no spec edit.

## Required tests / validation

- `python3 -m pytest tests/test_plan_review_feasibility_rule.py -o addopts=""`, plus the removal check in V-04 and BOTH negative controls in V-06 (a spec-review copy must fail the no-copy assertion; a bare long-form reference must fail the long-form assertion). A test whose negative control was never run is not known to be non-vacuous, which is the same standard this plan is asking reviewers to meet.
- Bare `python3 -m pytest`; do not add `-n0`, a second `-q` (it compounds into `-qq` and suppresses the `N passed` line the evidence requires), or `-p no:randomly`. Baseline measured at review on this lane: `2501 passed, 2 skipped, 3 warnings in 59.95s`. RE-DERIVE it rather than matching the number; the BAR is that the after-minus-before failing node set is empty.
- The new test module must carry NO `pytestmark = pytest.mark.slow`, or it will be excluded from the bare run by the configured `-m 'not slow'` and E-04's gate will never execute it.
- `python3 -m agent_workflows check all --agent`, naming pre-existing findings as pre-existing.

## Spec / documentation sync

No spec amendment: the IPD structure spec already assigns semantic judgement to the reviewer (Section 7), and this plan changes only the reviewer's instructions. The workflow files are the documentation being changed; `CHANGELOG.md` gets one entry (E-05).

## Open questions

### OQ-01: Should the long form carry the five points in full, or reference the single-file subsection?

- Blocking: no
- Status: resolved
- Owner: reviewer (raised and resolved at review from F-7)
- Resolution or deferral rationale: IN FULL, plus a parity pointer. Resolved BY DEMONSTRATION rather than by preference, which is the standard this plan itself is introducing: `03-resolve-and-finalize.md` defers to nothing today (one cross-file reference in 246 lines, none to `plan-review.md`) and already duplicates the sibling `### Decisions` rule including its `Reversible` section, so a bare reference would be the only one of its kind in that file and would read as an omission. The bundle's convention for a rule that must not drift is state-in-full-then-point-at-the-twin, which `plan-review-long.md`'s Readiness bullet demonstrates verbatim. E-02 was rewritten to mandate this rather than leaving the executor a conditional whose measurable answer the plan had not measured.

### OQ-02: Does E-04's documentation-contract test violate the maintainer's 2026-09-26 no-text-pinning ruling?

- Blocking: no
- Status: resolved
- Owner: reviewer (raised and resolved at review from F-8)
- Resolution or deferral rationale: No, and the exemption is explicit rather than inferred. The concurrent plan `96xtmi` (srcguard-01) that implements that ruling scopes itself OUT of "tests that read NON-production files (specs, workflow bodies, READMEs, the test module's own file) unless the census flags them as reading `agent_workflows/*`". E-04 reads a workflow body, which is the artifact this plan changes, and reads no `agent_workflows/*` source, so it is exempt by that plan's own words. The test is also asserting a DOCUMENTED CONTRACT (does the shipped reviewer instruction contain the rule) rather than pinning production code shape, which is the distinction the ruling draws. E-04 now cites this in the test module's docstring so a future census reader does not re-litigate it. RESIDUAL RISK, stated honestly: `96xtmi` is `to-review`, not executed, so its scope wording could still change; if it does, this test is the kind of thing its census should reclassify deliberately rather than silently.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new subsection as committed, with the five points identifiable, and `rg -n '^#{3,4} '` output over `plan-review.md` showing the new `####` heading's line number falls BETWEEN `### 3.1 Build the question set` and the next `### ` heading (at review those were `### 3.1` and `### 3.2 Ask interactively`; re-derive both, since line numbers move). Also paste the five anchor phrases you chose, as a list, since E-04's test asserts on exactly those strings and a mismatch between the prose and the test is the likeliest way this pair silently rots.
  - Observed evidence: verified; committed subsection in plan-review.md with 5 points, correct heading boundaries at line 274, and 5 distinctive anchor phrases.
    Committed subsection in `.aw/system/workflows/plan-review/plan-review.md`:
    ```markdown
    #### Resolving HOW questions: demonstrate, do not describe

    1. A question is a HOW question when its resolution chooses a mechanism rather than a fact or a scope (such as a code shape, a placeholder form, a flag, an algorithm).
    2. A HOW question may be marked `resolved` only when the resolution cites a demonstration that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row.
    3. If the reviewer cannot demonstrate it, they MUST instead either leave the question `open` (with `Blocking: yes` when execution depends on it) or convert it into a first spike E-item whose Expected outcome is the demonstration and whose stop condition names the question, and the review verdict MUST name the feasibility risk. State why the first branch bites: an open question carrying `- Blocking: yes` makes `aw ipd lint` report `error` with `IPD-Q501` at every checkpoint including `author`, so the plan cannot reach `approved` or be dispatched until a human answers (`IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer`). Verified at review by inserting such a question into this plan: disposition went `conforming` -> `error` at `author`, `review-finalize` and `pre-execution` alike.
    4. A resolution containing its own "confirm empirically / if no form works, stop" clause is by definition undemonstrated and falls under (3).
    5. `- Owner: maintainer` on a resolved question means the maintainer answered; a reviewer's own choice records the reviewer (or `plan author`) as owner and gets a `### Decisions` row as 3.1 already requires. Write this so a human applies it: no gate checks it. The linter only verifies the `Owner` field is non-empty and not `none` (`ipd_lint`'s `has_owner`, passed to `ipd_schema.open_question_error` as a bare boolean that never sees the value), so a false `Owner: maintainer` passes every mechanical check. Measured example: plan `vtkfq8` OQ-03 resolved a carrier requirement with an inert placeholder and labelled it `Owner: maintainer`, which passed mechanical checks but failed execution because `- Status: open` was what enforced the obligation.
    ```

    Heading boundary check (`rg -n '^#{3,4} ' .aw/system/workflows/plan-review/plan-review.md`):
    ```text
    264:### 3.1 Build the question set
    274:#### Resolving HOW questions: demonstrate, do not describe
    308:#### Reversible or not, and what that obliges
    331:### 3.2 Ask interactively
    ```
    The new heading at line 274 falls between `### 3.1 Build the question set` (line 264) and `### 3.2 Ask interactively` (line 331).

    The five anchor phrases chosen and tested:
    1. `chooses a mechanism rather than a fact or a scope`
    2. `cites a demonstration that the mechanism produces the required outcome`
    3. `IPD-Q501: OQ-01: BLOCKING question is still 'open'`
    4. `confirm empirically / if no form works, stop`
    5. `false \`Owner: maintainer\` passes every mechanical check`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the long-form change and state whether it references or copies the rule, with the reason.
  - Observed evidence: verified; committed subsection in 03-resolve-and-finalize.md copying the 5 points in full with parity pointer per PR-001.
    Committed subsection in `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`:
    ```markdown
    ### Resolving HOW questions: demonstrate, do not describe

    1. A question is a HOW question when its resolution chooses a mechanism rather than a fact or a scope (such as a code shape, a placeholder form, a flag, an algorithm).
    2. A HOW question may be marked `resolved` only when the resolution cites a demonstration that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row.
    3. If the reviewer cannot demonstrate it, they MUST instead either leave the question `open` (with `Blocking: yes` when execution depends on it) or convert it into a first spike E-item whose Expected outcome is the demonstration and whose stop condition names the question, and the review verdict MUST name the feasibility risk. State why the first branch bites: an open question carrying `- Blocking: yes` makes `aw ipd lint` report `error` with `IPD-Q501` at every checkpoint including `author`, so the plan cannot reach `approved` or be dispatched until a human answers (`IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer`). Verified at review by inserting such a question into this plan: disposition went `conforming` -> `error` at `author`, `review-finalize` and `pre-execution` alike.
    4. A resolution containing its own "confirm empirically / if no form works, stop" clause is by definition undemonstrated and falls under (3).
    5. `- Owner: maintainer` on a resolved question means the maintainer answered; a reviewer's own choice records the reviewer (or `plan author`) as owner and gets a `### Decisions` row as 3.1 already requires. Write this so a human applies it: no gate checks it. The linter only verifies the `Owner` field is non-empty and not `none` (`ipd_lint`'s `has_owner`, passed to `ipd_schema.open_question_error` as a bare boolean that never sees the value), so a false `Owner: maintainer` passes every mechanical check. Measured example: plan `vtkfq8` OQ-03 resolved a carrier requirement with an inert placeholder and labelled it `Owner: maintainer`, which passed mechanical checks but failed execution because `- Status: open` was what enforced the obligation.

    This rule is kept identical to the single-file `../plan-review/plan-review.md` per the parity note in `plan-review-long.md`.
    ```
    The change COPIES the five points in full plus adds a parity pointer to `../plan-review/plan-review.md`. Reason: PR-001 measured that `03-resolve-and-finalize.md` references nothing externally in 246 lines (except report-template.md) and fully duplicates the sibling Decisions rule rather than pointing at it; copying with a parity pointer matches established conventions across the long form (such as the Readiness bullet in `plan-review-long.md`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the spec-review paragraph and show it references plan-review's subsection rather than restating the five points.
  - Observed evidence: verified; committed paragraph in spec-review.md referencing plan-review.md section 3.1 with 0 duplicated anchor phrases.
    Committed paragraph in `.aw/system/workflows/spec-review/spec-review.md` (section 3.1):
    ```markdown
    For any question resolved by choosing a mechanism, follow `../plan-review/plan-review.md` section 3.1 ("Resolving HOW questions: demonstrate, do not describe"). That rule is shared and is deliberately not restated here: an unproven fix may not be marked resolved.
    ```
    This references `../plan-review/plan-review.md` section 3.1 by heading and contains 0 of the 5 anchor phrases, following spec-review's shared rule convention without duplicating text.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the passing test output, then the FAILING output with E-01's subsection temporarily removed, then the bare `python3 -m pytest` summary line.
  - Observed evidence: verified; test_single_file_plan_review_feasibility_rule passes, fails when subsection is removed, bare suite passes (2661 passed).
    Passing test output:
    ```text
    $ python3 -m pytest tests/test_plan_review_feasibility_rule.py -k test_single_file_plan_review_feasibility_rule -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2649480892
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items / 2 deselected / 1 selected

    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_single_file_plan_review_feasibility_rule PASSED [100%]

    NOTE: 2 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    ======================= 1 passed, 2 deselected in 0.07s ========================
    ```

    Failing output with E-01 subsection temporarily removed:
    ```text
    $ python3 -m pytest tests/test_plan_review_feasibility_rule.py -k test_single_file_plan_review_feasibility_rule -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2187252898
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items / 2 deselected / 1 selected

    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_single_file_plan_review_feasibility_rule FAILED [100%]

    =================================== FAILURES ===================================
    _ TestPlanReviewFeasibilityRule.test_single_file_plan_review_feasibility_rule __

    self = <tests.test_plan_review_feasibility_rule.TestPlanReviewFeasibilityRule testMethod=test_single_file_plan_review_feasibility_rule>

        def test_single_file_plan_review_feasibility_rule(self) -> None:
            ...
            subheading = "#### Resolving HOW questions: demonstrate, do not describe"
    >       self.assertIn(
                subheading,
                section_31,
                f"Subsection heading '{subheading}' not found inside section 3.1 of {PLAN_REVIEW_FILE}",
            )
    E       AssertionError: '#### Resolving HOW questions: demonstrate, do not describe' not found in ...
    =========================== short test summary info ============================
    FAILED tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_single_file_plan_review_feasibility_rule
    ======================= 1 failed, 2 deselected in 0.11s ========================
    ```

    Bare `python3 -m pytest` summary line:
    `2661 passed, 2 skipped, 3 warnings in 54.63s`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the CHANGELOG entry.
  - Observed evidence: verified; CHANGELOG.md unreleased entry committed under 2.0.0 (pending) with no em or en dashes.
    Committed entry in `CHANGELOG.md` under `## 2.0.0 (pending)`:
    ```markdown
    - Changed: plan reviews no longer mark a question answered by a fix nobody tried; an untried fix stays an open question or becomes a first test step.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_plan_review_feasibility_rule.py -o addopts="" -v` showing the two sibling cases PASSING by name. Then paste BOTH negative controls, each as actual failing output, because each guards a different mistake: (a) with the five anchor phrases pasted into `spec-review.md`, the no-copy assertion FAILS (guards against a duplicate that would drift); (b) with the long form's five points replaced by a bare cross-file reference, the long-form assertion FAILS (guards against the shape PR-001 showed that file does not use). Restore the tree after each control and paste a final passing run. State explicitly that the long form carries the points IN FULL plus a parity pointer, and quote the pointer sentence as committed.
  - Observed evidence: verified; all 3 tests pass, negative control (a) fails on copied anchor phrases, negative control (b) fails on bare reference, restored green.
    Passing test output:
    ```text
    $ python3 -m pytest tests/test_plan_review_feasibility_rule.py -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=479508634
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_single_file_plan_review_feasibility_rule PASSED [ 33%]
    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_spec_review_feasibility_rule_reference PASSED [ 66%]
    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_long_form_plan_review_feasibility_rule PASSED [100%]

    ============================== 3 passed in 0.06s ===============================
    ```

    Negative control (a) (anchor phrases pasted into `spec-review.md`):
    ```text
    $ python3 -m pytest tests/test_plan_review_feasibility_rule.py -k test_spec_review_feasibility_rule_reference -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=1505936370
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items / 2 deselected / 1 selected

    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_spec_review_feasibility_rule_reference FAILED [100%]

    =================================== FAILURES ===================================
    __ TestPlanReviewFeasibilityRule.test_spec_review_feasibility_rule_reference ___
    ...
    E       AssertionError: 5 not less than or equal to 1 : spec-review.md duplicates the feasibility rule (5 phrases found: ['chooses a mechanism rather than a fact or a scope', 'cites a demonstration that the mechanism produces the required outcome', "IPD-Q501: OQ-01: BLOCKING question is still 'open'", 'confirm empirically / if no form works, stop', 'false `Owner: maintainer` passes every mechanical check']). It must reference the rule, not copy it.
    =========================== short test summary info ============================
    FAILED tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_spec_review_feasibility_rule_reference
    ======================= 1 failed, 2 deselected in 0.10s ========================
    ```

    Negative control (b) (bare reference in `03-resolve-and-finalize.md`):
    ```text
    $ python3 -m pytest tests/test_plan_review_feasibility_rule.py -k test_long_form_plan_review_feasibility_rule -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=662445680
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items / 2 deselected / 1 selected

    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_long_form_plan_review_feasibility_rule FAILED [100%]

    =================================== FAILURES ===================================
    __ TestPlanReviewFeasibilityRule.test_long_form_plan_review_feasibility_rule ___
    ...
    E           AssertionError: 'chooses a mechanism rather than a fact or a scope' not found in ...
    =========================== short test summary info ============================
    FAILED tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_long_form_plan_review_feasibility_rule
    ======================= 1 failed, 2 deselected in 0.11s ========================
    ```

    Tree restored after each negative control and final run verified passing: `3 passed in 0.06s`.
    The long form carries the points IN FULL plus a parity pointer.
    Quoted pointer sentence as committed:
    `This rule is kept identical to the single-file ../plan-review/plan-review.md per the parity note in plan-review-long.md.`
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING (added at review). A change to the REVIEWER'S OWN INSTRUCTIONS, in three workflow files plus one new test and one changelog line. After it, a reviewer may not mark a question `resolved` by naming a mechanism nobody tried: it must cite a demonstration, or the question stays open (which mechanically blocks the plan) or becomes a first spike step, and the verdict must name the feasibility risk. The measured cost of not having this rule was one 13-minute, 762k-token turn plus a human round trip on plan `vtkfq8`. No production code changes. Two things a human should know about the limits: point (5) about `Owner:` is reviewer judgement that NO gate can check (F-5), and no lint rule is added to judge whether a pasted demonstration is genuine (deliberately, see Deferred).

Execute only after explicit human approval (`Status: approved`).

SCOPE FENCE, a DECLARATION for reconciliation and NOT a stop directive: the `- Scope-Paths:` list, i.e. the three workflow files, the one new test module, and `CHANGELOG.md`. If an edit outside it proves genuinely necessary, MAKE it and justify it at finalize with `--scope-reason` per out-of-scope path, plus `--scope-ack` per declared-but-unmodified path. Note two paths that are deliberately NOT in the fence and were checked at review: `verify-execution.md` and `plan-review-long/01`-`/02` carry no question-resolution step (F-6), so touching them would be over-scope.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`. V-04's removal check and BOTH of V-06's negative controls must show REAL failing output, not a described expectation: a documentation test whose negative control was never run is exactly the undemonstrated mechanism this plan exists to forbid, and shipping one here would be self-refuting. Restore the tree after each control.

Commit through `aw commit 7nghg8 -- <paths>` limited to `- Scope-Paths:`; never `git add -A`, never push. Finalize only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence; the plan then moves to `.aw/records/plans/executed/`. Ownership of that transition is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs the finalize transaction, so the executing agent does NOT invoke it; for a hand-run execution outside a runner, the executor runs `aw ipd finalize` itself. On completion close backlog `j4wz6b` through the handoff (this plan carries `From-Backlog: j4wz6b` and its `Blocks-Release: next`).
