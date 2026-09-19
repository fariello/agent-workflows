# IPD: Wire the shape check into plan-review as a bounded repair loop with honest exhaustion

- Date: 2026-09-19
- Kind: child
- Concern: The existing orchestrator control refuses at RUN START, where the remedy is exactly what a run must not do: edit another agent's plan. So an operator is told to go fix something by hand having already queued a run, and nothing in the pipeline offers to fix the violation at the one point licensed to rewrite a plan. Spec `r07vma` R5 puts the check where repair is possible. `/plan-review` already applies in-place revisions (its Step 2.4) and already re-runs `aw ipd lint --phase review-finalize` after them, so this is one more rule at a checkpoint that exists rather than a new mechanism.
  THE LOOP'S FAILURE MODES ARE THE DESIGN, NOT AN EDGE CASE. Two tempting behaviours are both wrong when the attempts run out: passing anyway launders a violation into an approved plan, and writing `- Readiness: no-go` asserts a verdict the review did not reach. R6 requires the honest third option, and the repository has already measured why the second is dangerous: on 2026-09-06 an agent authoring a four-plan Set wrote `Readiness: go-pending-approval` into all four having run no review, and the auto-approve predicate returned True for every one. That is why `aw ipd scaffold` omits the field and `ipd_lint` refuses an unattested value (`IPD-M107`).
- Scope: The `/plan-review` consumer of child 01's shared function. IN: calling that function for a `Kind: orchestrator` plan at the review checkpoint; asking the agent to repair a reported violation and re-running the check, up to a configurable attempt budget defaulting to 2; recording each attempt so a deletion-based "fix" is visible; and leaving an exhausted loop at `to-review` with `- Readiness:` ABSENT and the findings in the round record. OUT: the grammar and the function itself (child 01); the run-side gate (child 03); migrating any orchestrator (child 04); the merged-result proof (child 05); and any change to how `/plan-review` handles non-orchestrator plans.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review/plan-review-long.md, tests/test_plan_review_orchestrator_repair.py
- Item-Dependencies: executed:dpdyed
- Status: to-review
- Set: orchtyped
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: r3xk1f
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 02 of Set `orchtyped`. Measured at HEAD `21eff5d8`: `plan-review.md` already runs `aw ipd lint --phase review-finalize` after revisions (its line 121) and already owns in-place revision (its Step 2.4), so the loop has an existing home. `runner_shared.resolve_retry_budget(None)` returns 2, which is the precedent this plan's default follows rather than inventing a number.

## Goal

Make a violating orchestrator get FIXED during review rather than merely reported at run time, by calling child 01's function at the review checkpoint, asking the agent to repair what it reports, and re-checking within a bounded budget; and make an exhausted loop say so honestly instead of passing or inventing a verdict.

READ THE SCOPE PRECISELY: this child adds no rule of its own. If its diff contains a row pattern, a status list, or a child-table scan, that is an R3 violation and the reviewer should refuse it, because child 01 owns the rule and this child owns only the call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the call and the loop

- [ ] E-01 CALL CHILD 01'S FUNCTION AT THE REVIEW CHECKPOINT, for a plan whose own first `- Kind:` bullet reads `orchestrator`, and nowhere else. READ THE KIND FROM THE PLAN'S OWN FIRST BULLET rather than by searching the file: a plan that QUOTES another plan's `- Kind: orchestrator` line in its prose would otherwise be misclassified, and that failure has already been made in this repository during this Set's own authoring (a scan matched `m7gvuz`, a `Kind: child` plan, on a quoted string, and reported it as an orchestrator carrying ten items).
  SITE THE CALL WHERE THE EXISTING POST-REVISION CHECK ALREADY RUNS, beside `aw ipd lint --phase review-finalize`, so the two structural gates are read together by an agent under load rather than one being missed.
  - Depends on: none
  - Expected outcome: an orchestrator under review is checked; a `Kind: child` plan is not; a child plan quoting an orchestrator's Kind bullet is still not.
  - Execution state: pending

- [ ] E-02 ASK THE AGENT TO REPAIR, AND RE-RUN THE CHECK, up to a configurable attempt budget whose default is 2. Follow `runner_shared.resolve_retry_budget`'s precedence shape (CLI over repository policy over default) rather than inventing a second convention, and record honestly that the middle tier is NOT implemented today (backlog `dh3us4` tracks a repository-policy home), so a configurable default here faces the same gap and must not pretend otherwise.
  THE REPAIR PROMPT MUST CARRY CHILD 01'S MESSAGE VERBATIM rather than paraphrasing it. That message is where R7's content lives: the invariant, the anti-deletion clause, and both remedies. A paraphrase is a second statement of the rule and drifts from it, which is the failure this Set exists to prevent at a different level.
  - Depends on: E-01
  - Expected outcome: a violating orchestrator is repaired and passes on a later attempt within the budget; the budget is configurable; the prompt contains child 01's message unmodified.
  - Execution state: pending

### Task group 2: honest exhaustion, and its record

- [ ] E-03 MAKE AN EXHAUSTED LOOP HONEST (R6): the plan stays `to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Not `no-go`, which is a verdict the review did not reach, and not a pass. Do NOT write `- Readiness:` at all in this path; absence is the correct state, it is silent, and it makes the downstream gate fail closed.
  WHY ABSENCE RATHER THAN A VALUE, measured: the auto-approve predicate reads the `- Readiness:` FIELD FIRST and falls back to parsing the workflow history only when it is ABSENT. So any value written here asserts that a review cleared the plan. On 2026-09-06 an agent wrote `go-pending-approval` into four plans having run no review and the predicate returned True for all four; `ipd_lint` now refuses an unattested value as `IPD-M107`.
  - Depends on: E-02
  - Expected outcome: after an unfixable violation, the plan reads `- Status: to-review`, carries NO `- Readiness:` line, and the round record names the finding.
  - Execution state: pending

- [ ] E-04 LOG EVERY ATTEMPT, so a repair that "succeeded" by deleting the checklist is visible in the record rather than hidden behind a passing later attempt. Record, per attempt, what the check reported and what changed. This is the only mechanism that makes the deletion failure mode auditable after the fact, and AGENTS.md records that a prohibition-only message gets complied with by deleting the checklist, so the behaviour must be assumed possible rather than trusted away.
  - Depends on: E-02
  - Expected outcome: a two-attempt repair leaves two attempt records; a repair that removed rows rather than relocating work is readable from them.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `/plan-review` ALREADY OWNS IN-PLACE REVISION (its Step 2.4) and already re-runs `aw ipd lint --phase review-finalize` after every revision, so the loop has an existing home and needs no new checkpoint.
- `plan-review` AND `plan-review-long` ARE HELD IN DELIBERATE PARITY. A change to one must land in the other, or the two bodies drift; that parity is why this plan declares both paths.
- THE ROUND STRUCTURE IS APPEND-ONLY: a re-review appends `## Round <n>` rather than editing an earlier round, because the gate reads only the CURRENT round. An attempt log must respect that.
- `runner_shared.resolve_retry_budget(None)` RETURNS 2 and implements `CLI > repository policy > default`, with the middle tier unimplemented and tracked by backlog `dh3us4`. E-02 follows its shape and inherits its honest gap.
- `- Readiness:` IS A REVIEW OUTPUT AND ABSENCE IS THE CORRECT AUTHORING STATE. `aw ipd scaffold` omits it; `ipd_lint` refuses an unattested value (`IPD-M107`); the auto-approve predicate reads the field before the history. E-03 depends on all three facts.
- READ A PLAN'S KIND FROM ITS OWN FIRST `- Kind:` BULLET. A whole-file search misclassifies a plan that quotes another's metadata, which happened during this Set's authoring.
- SUITE BARE: `python3 -m pytest`; `addopts` supplies the intended flags. Compare failing NODE IDS, not totals.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `plan-review.md`, its `review-finalize` lint invocation | The review already re-runs a structural gate after revisions, so the repair loop has a natural home; adding a separate checkpoint would create a second place an agent must remember to look. | the workflow body at HEAD `21eff5d8` |
| F-2 | HIGH | the `- Readiness:` auto-approve path | Writing any value on the exhausted path would assert a review verdict that was not reached, and the predicate reads the field BEFORE the history, so the assertion is load-bearing. Measured 2026-09-06 with four plans. | AGENTS.md's recorded incident; `ipd_lint` `IPD-M107` |
| F-3 | HIGH | `plan-review.md` and `plan-review-long.md` | The two bodies are held in deliberate parity, so a one-sided change drifts them. Both are declared. | the parity note in the workflow body |
| F-4 | MEDIUM | `runner_shared.resolve_retry_budget` | The budget precedence already exists with default 2 and an unimplemented middle tier; E-02 must follow it and must not claim the policy tier works. | signature and docstring read; backlog `dh3us4` exists |
| F-5 | MEDIUM | this Set's own authoring | A whole-file `Kind` search misclassified a `Kind: child` plan as an orchestrator because it quoted the bullet. E-01 must read the plan's OWN first bullet. | the mis-measurement made and corrected during authoring |
| F-6 | MEDIUM | AGENTS.md's orchestrator guidance | A prohibition-only message gets complied with by DELETING the checklist, which is the outcome R2 forbids. E-04's attempt log is what makes that visible after the fact. | the managed block's text |

## Proposed changes (ordered, validatable)

1. E-01 calls child 01's function for orchestrators only, keyed on the plan's own first `- Kind:` bullet.
2. E-02 adds the bounded repair loop, carrying child 01's message verbatim.
3. E-03 makes exhaustion honest: `to-review`, findings recorded, `- Readiness:` absent.
4. E-04 logs each attempt so a deletion-based repair is auditable.

## Deferred / out of scope (with reason)

- THE GRAMMAR, THE FUNCTION, AND THE MESSAGE TEXT: child 01 (`dpdyed`) owns all three. This child calls and renders; it does not decide.
  - Carrier-Declined: Owned by a named sibling in this Set; nothing to hand off.
- THE RUN-SIDE GATE: child 03 (`0xmk4e`). Review and run are separately reviewable consumers on purpose.
  - Carrier-Declined: Owned by a named sibling in this Set.
- MIGRATING ANY EXISTING ORCHESTRATOR: child 04 (`68uhp0`). This child must not fix the corpus as a side effect of testing, which would both hide the migration's cost and edit other agents' plans.
  - Carrier-Declined: Owned by a named sibling in this Set.
- IMPLEMENTING THE REPOSITORY-POLICY TIER of the retry budget: backlog `dh3us4` owns it. E-02 inherits the gap and states it.
  - Carrier: dh3us4
- ANY CHANGE TO NON-ORCHESTRATOR REVIEW BEHAVIOUR: out of scope, and E-01's `Kind` guard is what keeps it so.
  - Carrier-Declined: An explicit boundary rather than deferred work.

## Scope check

- Over-scope: none. Both workflow bodies are edited by E-01 through E-04 (parity, F-3), and the new test file by every item.
- Under-scope: if the loop needs a code-side helper (for example to render the attempt log into the round record) rather than living entirely in the workflow prose, that module must be DECLARED before editing. This plan assumes the loop is workflow-level because `/plan-review` is a prose workflow an agent executes, and an executor who finds otherwise should amend `- Scope-Paths:` and say so rather than reconciling afterwards.

## Required tests / validation

`python3 -m pytest` BARE, in an isolated worktree, baseline measured there, compared by failing NODE ID.

Beyond the suite: a violating orchestrator repaired within budget with the before and after checklists pasted; an unfixable case showing `to-review` plus an ABSENT `- Readiness:`; the attempt log for a two-attempt repair; and the two workflow bodies diffed against each other to prove parity.

## Spec / documentation sync

The two `plan-review` workflow bodies ARE the documentation for this behaviour and are declared in `- Scope-Paths:`. No `.spec.md` is edited: spec `r07vma` R5/R6/R7 are implemented as written, not amended. Note that editing a shipped workflow changes what every future review does, which is a wide blast radius for a small diff, so the parity check (F-3) is not optional.

## Open questions

### OQ-01: Should the attempt log live in the review round record, or in the plan's own workflow history?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: NOT blocking: E-04's requirement is that the attempts be AUDITABLE, and either location satisfies it. Recorded because the two have different properties. The round record is append-only per round and is where findings already live, so an attempt log there sits beside the finding it resolves; but the round record is written by the reviewing agent, so it is self-reported. The plan's workflow history is tool-written (`aw set` / `aw ipd set`), so it is harder to misreport, but it is a lifecycle log and an attempt that changed nothing is not a lifecycle event. PROPOSED DIRECTION: the round record, because the attempt log's reader is a human or agent reading the review, and because adding non-lifecycle entries to a tool-owned history would blur what that history means.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the call site in BOTH workflow bodies, and a diff or assertion proving they are in parity. Paste three cases: an orchestrator checked, a `Kind: child` plan NOT checked, and a `Kind: child` plan that QUOTES `- Kind: orchestrator` in its prose also NOT checked. That third case is the one F-5 measured, so a validation without it is incomplete.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a violating orchestrator's checklist BEFORE and AFTER a repair that succeeded within the budget, plus the check's output on each attempt. Paste the budget's resolution showing CLI-over-default and state explicitly that the repository-policy tier is unimplemented (`dh3us4`). Paste proof the repair prompt carries child 01's message VERBATIM, by diffing the prompt text against the function's rendered message rather than by asserting they look similar.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: run a deliberately unfixable case to exhaustion and paste the plan's front matter afterwards, showing `- Status: to-review` and NO `- Readiness:` line at all (`grep -c '^- Readiness:'` returning 0 is the clearest form). Paste the round record showing the finding recorded. Confirm the code path contains no write of `- Readiness:` in this branch, by grep rather than by inspection.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the attempt log for a two-attempt repair. Then paste the log for a repair that satisfied the check by DELETING rows rather than relocating the work, and confirm a reader can tell from the log alone that rows were removed. If the log cannot distinguish those two cases, this item FAILS, because that distinction is its entire purpose.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 4 E-leaves in 2 groups, all inside the review workflow and its test. The rule itself is child 01's.
- Cohesion rationale: E-01 and E-02 are the call and the loop around it, which cannot be tested apart. E-03 and E-04 are the two halves of what happens when the loop does not succeed, and both exist to stop a violation being laundered into an approved plan; separating them would leave an honest status with no auditable record behind it.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. In particular this plan must NOT repair any existing orchestrator while testing, which would be editing another agent's plan and is child 04's work.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved r3xk1f --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Its `- Item-Dependencies:` refuse dispatch until `dpdyed` is executed. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
