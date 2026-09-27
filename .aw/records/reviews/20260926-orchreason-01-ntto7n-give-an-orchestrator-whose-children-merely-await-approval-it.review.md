# Review findings: plan ntto7n

- Subject-Id: ntto7n
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --detail`
CONFORMED (exit 0, no advisory) before revision. No pre-review snapshot was needed: `git status
--porcelain` was empty and the lane input under `.aw/state/lane-inputs/rev-6/` is byte-identical to
the tracked plan.

THE PREMISE IS CORRECT AND I RE-DROVE IT RATHER THAN READING IT. Calling the real
`decide_orchestrator_dispatch` on the plan's own fixture reproduced its table exactly: `reviewed` ->
`terminate children-terminally-failed`, `approved` -> same, `failed-safely` -> same, `queued` ->
`reconsider children-unfinished`. The mechanism is as described: `reviewed` and `approved` are both in
`TERMINAL_STATES` and neither is in `EXECUTION_SUCCESS_STATES`, so both land in `dead`. The
operator-visibility claim holds in code (`dispatch_orchestrator_item` passes `code=decision.reason`
into `record_refusal`; `run_viewer` renders `! refused [{refusal.code}]: {refusal.reason}`), and F-4 is
right that the human remedy already leads with the approval case, so only the machine code and the
`detail` sentence mislead. This is a real, well-scoped defect and the proposed fix is the right shape.

**I WENT LOOKING FOR THE FIX BEING TOO NARROW AND FOUND EXACTLY THAT, THOUGH NOT WHERE I EXPECTED.**
Sweeping ALL 23 members of `TERMINAL_STATES` through the real function showed that `reviewed` and
`approved` are not the only never-ran statuses landing on the failure code: `blocked`,
`dependency-blocked`, `not-attempted` and `not-run` do too, and none of them means "ran and failed"
either. `executed` is the one interesting non-member (it is a terminal SUCCESS, so it strands as
`children-not-in-this-run`). The plan's Concern frames the space as binary, approval versus failure,
when it is actually three-way. I did NOT widen the plan's status set, and the reason is the deliverable
rather than the diff size: the remedies are the whole point of this change, and the four leftovers each
need a different one (run the prerequisite, clear the gate, the run ended before reaching the child).
Folding them in would yield one vague message where the plan currently produces two precise ones, which
is the very defect under repair. So the sweep is now an E-01 obligation, the four statuses are an
explicit Deferred entry with `_NOT_APPROVED_CHILD_STATUSES` named as the seam, and the gate tells the
approver plainly that the code stays coarse about four cases.

**A FINDING'S EVIDENCE MISSTATED A SET THE PLAN'S CORRECTNESS DEPENDS ON.** F-2 asserted
`EXECUTION_SUCCESS_STATES` is `{executed, substantially-complete}`; driven, it is `{"executed"}`
(`SUCCESS_STATES` is the three-member one, and `substantially-complete` is in neither). This is not
pedantry about a parenthetical. `substantially-complete` is terminal and not a success, so it lands in
`dead` and MUST keep the failure code, because it means a turn ran and under-delivered. An executor who
believed the authored cell would have read `substantially-complete` as a success that never reaches this
branch, and the natural "while I am here" widening of `_NOT_APPROVED_CHILD_STATUSES` would then have
relabelled a real under-delivery as an approval wait, in the one message an operator reads to decide
what to do next. Corrected in place with the driven values and the consequence spelled out.

**I RAISED A MEDIUM AGAINST THE STATUS SET AND THEN DISPROVED MY OWN FINDING, WHICH IS WORTH RECORDING
IN FULL.** `initial_queue_status` maps `superseded` and `not-executed` to queue status `reviewed` (its
own docstring says so). That looked serious: `children-not-approved` would then tell an operator to
`aw ipd set approved` a plan somebody deliberately retired, making the remedy actively wrong rather than
merely vague. Before writing it up I drove it, and it does not reach the branch: a retired child is not
UNFINISHED (`set_retirement_terminal_statuses()` is `{executed, not-executed, superseded}`), so
`evaluate_set_retirement(...).unfinished` comes back empty and no dead-children reason is produced at
all. A `- Status: superseded` plan sitting wrongly in `pending/` behaves the same way. What DOES reach
the branch is a plan with no `- Status:` line, which also maps to `reviewed` and IS unfinished, and for
that plan "approve it" is correct advice. So the finding downgraded from MEDIUM to LOW and became a
comment obligation plus a test case rather than a change to the status set. I kept it because the
REASONING is what a later reader needs: without it, someone re-deriving the overload will either
narrow the set wrongly or re-litigate this from scratch.

ON A CITED PATH THAT CANNOT EXIST. The plan justified keeping the old key mapped by citing
`.aw/records/runs/run-20260913T031350Z-1732436/state.json`. There is no `.aw/records/runs/` directory
here at all: `.aw/.gitignore` ignores `records/runs/`, so run records are box-local and never
committed. The requirement is correct and I verified it against the CODE instead, driving
`orchestrator_refusal_text('children-not-approved')` and getting the "THIS VERSION OF THE RUNNER DOES
NOT RECOGNIZE" fallback, which is exactly what a historical record would hit if the old key were
dropped. Left alone, an executor in a lane would read a missing cited file as a failed precondition and
go hunting outside the workspace, which the lane contract forbids. Now labelled unverifiable-by-design
in both the conventions bullet and the stop condition.

ON THE VERIFICATION, which was strong and had two specific holes. The authored E-05 is good work: it is
behavioral, it names controls, and case (8) genuinely reaches the read surface (I confirmed
`code=decision.reason` is what `record_refusal` receives, so it is not a restatement of case (1)). The
holes: nothing pinned the OUTCOME, even though the Scope explicitly promises "outcome stays
`ORCH_DISPATCH_TERMINATE` in both cases", and the `if dead:` branch's own comment records a MEASURED
201-iteration spin from getting a terminate/reconsider call wrong, so an unpinned promise there is the
expensive kind. And nothing pinned the no-`Status:` overload from F-6, which is precisely the case a
future reader would "clean up". Added as cases (9) and (10), with (9) marked a control for the outcome
while (1)/(2) change the reason. Also verified the MIXED case OQ-01 settles actually behaves as
specified (two children, one `reviewed` and one `failed-safely` -> `children-terminally-failed` with
both in `unfinished`), so that resolution is measured and not just argued.

ON THE TWO OPEN QUESTIONS, both of which I checked rather than accepted. OQ-01 (mixed set keeps the
failure code) is right and I drove the case. OQ-02 (no spec amendment) is right for the reason given: I
read `77tr3o` R-9, which requires the refusal reasons to be DISTINGUISHABLE and enumerates four FACTS,
not code strings, and grepping `.aw/records/specs/` for `children-terminally-failed` returns nothing.
Adding a finer code moves in the direction R-9 demands. F-5 also holds: the only test naming
`ORCH_REASON_DEAD_CHILDREN` uses `failed-safely`, a genuine failure, so it stays green under this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | MEDIUM | UNDER-SCOPE | A. correctness; F. honest documentation | swept all 23 `TERMINAL_STATES` through the real `decide_orchestrator_dispatch`: `blocked`, `dependency-blocked`, `not-attempted`, `not-run` all -> `terminate children-terminally-failed`; `executed` -> `children-not-in-this-run` | **FOUR OTHER NEVER-DISPATCHED STATUSES KEEP THE FAILURE CODE AND THE PLAN DOES NOT SAY SO.** The Concern frames the defect as binary (approval vs failure) when the status space is three-way: besides `reviewed`/`approved` there are four statuses that also never ran and also get told they "reached a non-success terminal state". The fix is still correct and strictly better, but an approver reading this plan would believe the naming defect is fully closed when it is closed for two of six cases. | C:Low; U:Low; S:Low; F:Medium (an operator still misread for four statuses); Overall:Low | FIXED | Recorded as F-7. NOT closed by widening the status set, deliberately: the remedies are the deliverable and each leftover needs a different one, so bundling would produce one vague message instead of two precise ones. E-01 now requires the full sweep to be pasted, a Deferred entry names the four statuses with the per-status remedy reason and points at `_NOT_APPROVED_CHILD_STATUSES` as the seam, and the gate carries a "WHAT THIS DELIBERATELY DOES NOT FIX" paragraph. |
| PR-402 | MEDIUM | IN-SCOPE | A. correctness (false evidence in a finding) | `sorted(runner_shared.EXECUTION_SUCCESS_STATES) == ['executed']`, not `{executed, substantially-complete}` as F-2 claimed; sweep: `substantially-complete` -> `terminate children-terminally-failed` | **A FINDING MISSTATED A SET THE FIX'S CORRECTNESS TURNS ON.** `substantially-complete` is terminal and NOT a success, so it lands in `dead` and must keep the FAILURE code (a turn ran and under-delivered). Believing F-2's cell, an executor would read it as a success that never reaches the branch, and the obvious widening of `_NOT_APPROVED_CHILD_STATUSES` would then relabel a real under-delivery as an approval wait, in the exact message an operator uses to decide what to do next. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-2's evidence cell corrected to the driven value, with F-8 added stating why the distinction is load-bearing rather than pedantic and what the wrong reading would have caused. |
| PR-403 | MEDIUM | UNDER-SCOPE | E. verification | the Scope promises "outcome stays `ORCH_DISPATCH_TERMINATE` in both cases" and no authored case asserts it; the `if dead:` branch's own comment records a measured 201-iteration spin from a wrong terminate/reconsider call; `initial_queue_status(None) == 'reviewed'` and that child IS unfinished | **THE PLAN'S OWN PROMISE ABOUT THE OUTCOME WAS UNPINNED, AND THE ONE LEGITIMATE `reviewed` OVERLOAD WAS UNTESTED.** Eight good behavioral cases all assert the REASON; none asserts that the outcome is still TERMINATE, which the Scope explicitly guarantees and which the branch's history shows is the expensive thing to get wrong. Separately, a child with no `- Status:` line reaches this branch as `reviewed`, and nothing pinned that, so a later reader narrowing the status set would silently drop it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 gained case (9) asserting `ORCH_DISPATCH_TERMINATE` for the new code (a control for the outcome, since the reason is what changes) and case (10) pinning the no-`Status:` child -> `children-not-approved`. Counts updated to ten cases with five failing pre-change, in E-05, Required tests and V-05. |
| PR-404 | LOW | IN-SCOPE | G. executability (an uncheckable citation) | `ls .aw/records/runs/` -> does not exist; `git check-ignore -v .aw/records/runs/x/state.json` -> `.aw/.gitignore:14:records/runs/`; `orchestrator_refusal_text('children-not-approved')` -> "THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE" | **A CONVENTIONS BULLET RESTS ON A FILE THAT CANNOT EXIST IN A CHECKOUT.** The keep-the-old-key requirement was justified by citing one run `state.json`, but run records are gitignored and box-local. The requirement is sound on the CODE, so the citation is unverifiable-by-design rather than false; left as written it reads to a lane executor as a failed precondition and invites a search outside the authorized workspace. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 added; the conventions bullet now states the requirement against the driven fallback behavior and labels the path uncommittable; the gate's stop condition explicitly says the missing path is NOT a stop and not a missing input. |
| PR-405 | LOW | IN-SCOPE | A. correctness (a reviewer's own overreach, recorded) | `initial_queue_status('superseded'\|'not-executed') == 'reviewed'`, BUT child in `superseded/` -> `evaluate_set_retirement(...).unfinished == ()` and no dead-children reason; `set_retirement_terminal_statuses() == {executed, not-executed, superseded}` | **I RAISED THE STATUS SET AS A MEDIUM AND DISPROVED IT BY DRIVING IT.** The suspicion was that `children-not-approved` could tell an operator to approve a deliberately RETIRED plan, since `superseded`/`not-executed` also map to queue status `reviewed`. Measured: a retired child is not unfinished, so it never reaches this branch. The overload that does reach it is a plan with no `- Status:` line, for which "approve it" is correct. Recorded rather than dropped because the reasoning is what stops a later reader either narrowing the set wrongly or re-litigating it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 records the suspicion, the disproof, and the surviving benign overload. E-02's comment obligation now includes both halves so the justification lives in the code, and E-05 case (10) pins the reachable case. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Four other never-dispatched statuses share the failure code (PR-401). Widen this plan's status set, or scope the plan and declare them? | SCOPE IT: keep `{reviewed, approved}`, require the full sweep as evidence, and declare the four as an explicit Deferred entry naming the extension seam. | (a) Widen `_NOT_APPROVED_CHILD_STATUSES` to all six: rejected, and this is the substantive call. The deliverable is the REMEDY TEXT, and one code covering six statuses forces one generic message ("your children did not run, check why"), which is the vagueness this plan exists to remove. `dependency-blocked` needs "run the prerequisite", `blocked` needs "clear the gate", `not-attempted`/`not-run` need "the run ended before reaching this child", and none of those is "approve it". (b) Add four more codes here: rejected, four new codes plus four remedies plus their tests is a different plan, and the approval case is the one with a measured operator cost in `swk6r8`. (c) Say nothing: rejected, the approver would believe the naming defect fully closed. | Swept all 23 `TERMINAL_STATES` through the real function and read each status's meaning at its write site (`dependency-blocked` written at dispatch on an unmet edge; `not-attempted`/`not-run` in the retry sets). `orchestrator_refusal_text`'s unknown-code fallback means a later code degrades gracefully, so the seam is safe to leave open. | yes |
| D-2 | Does `superseded`/`not-executed` mapping to queue status `reviewed` make the new remedy actively wrong (PR-405)? | NO. Keep `{reviewed, approved}` and record the disproof plus the one benign overload. | (a) Exclude retired plans by inspecting disk status in the dead branch: rejected, it would add IO and a second status source to a decision function that currently reads only the queue entry, to defend against a state proven unreachable. (b) Narrow the set to `approved` only: rejected, `reviewed` is the COMMON case (the whole defect is an unapproved child) and dropping it would gut the plan. (c) Raise it as a MEDIUM finding anyway: rejected as dishonest once driven; reporting a hazard I had disproved would have sent the executor to defend against nothing. | Drove it: child in `superseded/` or `not-executed/` -> `unfinished=()`, no dead reason; `- Status: superseded` in `pending/` -> same; `set_retirement_terminal_statuses()` includes both, which is WHY they are not unfinished. The reachable overload (no `- Status:` line) maps to `reviewed` and is unfinished, and "approve it" is right for it. | yes |
| D-3 | F-2's evidence was factually wrong (PR-402). Correct the cell quietly, or record it as a finding? | RECORD IT as F-8 with the consequence of the wrong reading. | (a) Silently fix the cell: rejected, the error had a specific failure mode (a plausible widening that mislabels `substantially-complete`), and a reader who sees only the corrected value learns nothing about why the set matters. (b) Treat it as cosmetic: rejected, `substantially-complete` means a turn ran and under-delivered, so mislabelling it an approval wait would tell an operator to approve their way past an incomplete execution. | Drove `EXECUTION_SUCCESS_STATES` (`{'executed'}`), `SUCCESS_STATES` (three members), and the sweep entry for `substantially-complete` (`children-terminally-failed`). | yes |
| D-4 | The plan cites a run `state.json` that does not exist (PR-404). Drop the requirement, find another record, or re-ground it? | RE-GROUND it on the code and label the path unverifiable-by-design. | (a) Drop the keep-the-old-key requirement: rejected outright, it is correct and load-bearing; dropping the key would make every historical record render the unknown-code fallback. (b) Cite a different run record: rejected, `.aw/.gitignore` ignores `records/runs/` so ANY such path is uncommittable and the next reader hits the same wall. (c) Leave it: rejected, a lane executor would read a missing cited file as a failed precondition and search outside the workspace, which the lane contract forbids. | `git check-ignore -v` confirms the ignore rule; `orchestrator_refusal_text('children-not-approved')` returns the DOES-NOT-RECOGNIZE fallback, which is the actual proof the key must stay mapped. | yes |

### Deferred and open

- (none) as review findings: all five were FIXED. Nothing reached Medium-High or High Remediation Risk,
  so the Fix Bar took no deferral, and nothing reached the repository's `HIGH` escalation threshold, so
  no `- Blocking: yes` question was owed.
- The PLAN carries a new Deferred entry (the four other never-dispatched statuses, D-1). That is a
  scoping decision recorded in the plan, not an unfixed review finding: the work is declared,
  justified, and given an extension seam. PR-401 is `FIXED` in the sense that the plan's blindness to
  those statuses is fixed; the statuses themselves still carry the coarse code after this plan
  executes, and the gate says so to the approver in those words.
- Both pre-existing open questions (OQ-01 mixed-set precedence, OQ-02 spec amendment) were already
  marked resolved and I verified both rather than accepting them: the mixed case was driven, and R-9
  was read in `77tr3o` (it enumerates four FACTS, no code strings, and a grep of `.aw/records/specs/`
  for the code strings returns nothing). Neither needed reopening.
- No `Reversible: no` decision was made. All four decisions are plan-text or scoping choices on an
  unexecuted plan. Note the plan itself will add a PUBLIC-ish string (a new refusal code) when it
  executes, but the code is additive, the old key stays mapped, and the unknown-code fallback means an
  older reader degrades gracefully, so even that is not a one-way door.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I did not run the suite: this
review changed no code and the plan changes none yet; E-05/V-05 own that, and I did verify that the one
existing test naming `ORCH_REASON_DEAD_CHILDREN` uses `failed-safely` and so stays green. SECOND, I
drove `decide_orchestrator_dispatch` DIRECTLY and through `evaluate_set_retirement`, but I did NOT
drive `dispatch_orchestrator_item` end-to-end on a run dir; I verified case (8)'s premise by reading
that it passes `code=decision.reason` into `record_refusal`, which makes the assertion sound but leaves
the wiring itself proven by inspection rather than execution. THIRD, my terminal-status sweep used the
single-child fixture with `action: execute`; I checked that `action` does not affect the dead
classification (all three actions give the same reason) but I did not enumerate multi-child
combinations beyond the one mixed case. FOURTH, on the four deferred statuses I established that they
currently share the failure code and read their write sites to characterize them; I did not audit every
path that can write each one, so the claim "none of them means ran-and-failed" is a reading of their
documented meaning rather than an exhaustive proof.
