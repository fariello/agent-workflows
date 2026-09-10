# IPD: Re-evaluate a stale no-go readiness whose recorded cause is gone, instead of stranding the plan

- Date: 2026-09-10
- Kind: child
- Concern: A `- Readiness: no-go` records a MOMENT, not a condition, and nothing re-evaluates it when the cause it was set for is removed, so a plan whose blocking question has been answered stays permanently unapprovable behind a refusal that has no override.
- Scope: Add a narrow, evidence-citing readiness RE-CHECK that recomputes the three `no-go` conditions the plan-review contract already defines, updates the field when all three are clear, and refuses to touch it otherwise; close the one-directional escalation loop so a finding whose escalated question was answered stops blocking; then run both over the currently-stranded plans and report the surviving reason per plan. Does NOT re-critique a plan, does NOT approve anything, and does NOT let an agent assert a readiness it did not compute.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/review_findings.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, tests/test_plan_readiness_recheck.py, .aw/system/workflows/plan-review/plan-review.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: rdyrecheck
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qhy3i3

## Workflow history
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review at HEAD `ce33d3c1`; REVIEWED - OPEN QUESTIONS, readiness NO-GO on OQ-01 alone; PR-001..PR-008 all FIXED in place, none deferred, none REPLAN. `aw ipd lint` CONFORMING at `--phase author` before review and at `--phase review-finalize` after every revision, so nothing here is structural. SELF-REVIEW DISCLOSURE: the same agent/model authored this plan minutes earlier, so instead of re-reading it I EXECUTED its central claim, running the shipped `approval_refusals` over all nine plans the plan promises to unstick. THAT MEASUREMENT PRODUCED BOTH BLOCKERS AND NEITHER WAS VISIBLE FROM THE PROSE. (1) PR-001: only ONE of the nine (`dw7i3m`) actually clears; the other EIGHT each carry a second, independent, still-true refusal, so the Goal, F-1 and E-06 all overstated the outcome and were rewritten to promise VISIBILITY of the surviving cause rather than cleared plans. (2) PR-002: five of those eight refusals come from typed review records that still read `OPEN` for the very findings whose escalated questions the maintainer ANSWERED on 2026-09-10 (`4h7tt0` PR-002, `kbqpkn` PR-801, `5lxvl3` PR-002, `y9vpvv` PR-904, `daexj1` PR-401), because the escalation contract defines only the path INTO a question and no path back; that is this plan's own thesis applied to the artifact the plan did not touch, so scope grew by E-07 plus `review_findings.py`. THREE SMALLER CORRECTIONS OF MY OWN AUTHORING: E-06 named the wrong plans for the non-blocking-question case (four, not two, and `y9vpvv` has BOTH causes rather than none); the suite baseline `5859 passed` was copied from a prior session's notes rather than run, so the figure is REMOVED and the executor must establish it; and `- From-Backlog: none` was a hand-written metadata field on a plan about agents hand-writing metadata, so it is gone. OQ-02 resolved at review (D-1, stay explicit); OQ-01 kept OPEN as D-2 because the contract supports both readings of whether a non-blocking question holds a plan at `no-go` and choosing the narrower one would have flattered this very verb.
- 2026-09-10 to-review (aw set): set Item-Dependencies to none

- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from a maintainer decision taken during an `/askme` round. Asked how nine plans carrying a stale `no-go` should be handled, the maintainer chose "add a narrow re-check step, and use it on all nine" over clearing the field by hand, over a full re-review, and over leaving them. THE MAINTAINER'S OWN CHALLENGE SHAPED THE SCOPE: seeing reviews that ended "on one question alone", they asked whether the reviewer "really reviewed the rest of the doc and/or if the doc really needs a full fresh review". MEASURED, and the answer split: the reviews DID sweep the whole document (PR-001..PR-014 on `wmnmei`, PR-801..PR-810 on `kbqpkn`, PR-001..PR-008 on `4h7tt0`, PR-001..PR-009 on `5lxvl3`, plus 4 to 12 recorded decisions each, all applied in place), so a fresh critique would re-derive settled findings and is NOT warranted; but nothing re-evaluates the verdict, which is a design gap rather than a clerical one. Hence a re-check, not a re-review.

## Goal

Make a `no-go` readiness a RE-EVALUABLE claim rather than a permanent one, so that a refusal states a reason that is still TRUE, and so no agent has to forge a review verdict to unstick work.

READ THE GOAL PRECISELY, BECAUSE MEASUREMENT NARROWED IT AT REVIEW. This does NOT promise to clear the stranded plans. Measured over the nine at HEAD `ce33d3c1`, exactly ONE (`dw7i3m`) clears and EIGHT legitimately keep refusing on a condition that is still recorded and still true. The deliverable is that the STALE component of a refusal disappears so the REMAINING cause becomes visible and attributable, rather than being hidden behind a verdict nobody re-evaluates. A plan that stays `no-go` for a reason a human can now see and act on is a SUCCESS of this plan, not a failure of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: compute the verdict from conditions rather than from memory

- [ ] E-01 ADD A PURE PREDICATE THAT RECOMPUTES THE THREE `no-go` CONDITIONS AND RETURNS THEM INDIVIDUALLY, in `plan_readiness.py`, reusing the shipped predicates rather than re-deriving any of them. The three conditions are an unresolved BLOCKING open question, an unfixed gating finding, and a negative verdict. All three are already computable in this module: `has_unresolved_blocking_question` (`:265`), `review_findings.subject_gating_blocks` (composed in `approval_refusals`), and `newest_verdict` (`:378`).
  THE FIRST CONDITION IS BLOCKING-ONLY, PER THE MAINTAINER'S 2026-09-10 RULING ON OQ-01, and this is a DEPARTURE from the contract's current literal wording ("any open question", `plan-review.md:543`), which E-05 amends in the same change. Compose `has_unresolved_blocking_question`, which already tests exactly that; do NOT count every open question. Rationale recorded with the ruling: the `- Blocking:` flag exists to record which questions must stop work, so treating both kinds alike discards the distinction. MEASURED CONSEQUENCE: 43 of 104 pending plans carry ONLY non-blocking questions, so the literal reading was holding 43 plans for reasons their own authors judged non-stopping.
  STATE HOW THE OVERRIDABLE HALF IS CONSUMED, rather than inheriting a default silently. `approval_refusals` applies the STRICTER `Status != "resolved"` test for open questions and exposes `allow_open_questions` to suppress exactly that half (documented at `plan_readiness.py:433-505`). Say in code and in the report which behavior the re-check relies on, because that flag is the one part of the composed predicate whose semantics this ruling changes.
  RETURN THE THREE SEPARATELY, NOT A BOOLEAN. The whole defect being fixed is that a verdict lost its reason; a re-check that also collapses to one bit reintroduces it one layer down. The caller must be able to say WHICH condition still holds, and the record must name it.
  DO NOT FORK `approval_refusals`. It is documented as "THE ONE PREDICATE EVERY APPROVAL SURFACE CONSUMES" with two callers (`status_set.py:561`, `specs.py:584`) and an explicit anti-fork guard test at `tests/test_review_findings_gate.py`. Compose it or factor a shared helper out of it; do not copy its logic. The composition it already performs is documented as a numbered list in its docstring (`plan_readiness.py:433-455`) and performed in its body (`:474-530`); that body is what to factor from, not the `def` line.
  - Depends on: none
  - Expected outcome: a function returning a per-condition result (open questions, gating findings, negative verdict) with a human-readable reason string for each condition that still holds, and no new copy of any existing predicate.
  - Execution state: pending

- [ ] E-02 MAKE THE RE-CHECK REFUSE TO WRITE WHENEVER ANY CONDITION STILL HOLDS, and write only `no-go -> go-pending-approval`. This is the safety property that makes the verb something an agent may run: it can only ever move a plan to the state that still requires human approval, never to `go`, and never onto a plan whose readiness is absent or already approvable.
  IT MUST NOT INVENT A READINESS. If the field is ABSENT, refuse and say so: absence means no review recorded a signal, and minting one here would be the same forgery `AGENTS.md` forbids when it says never to hand-write a `- Readiness:`. If the value is OUT-OF-VOCAB, refuse too, matching `read_readiness`'s fail-closed contract (`ipd_schema.py:311-329`, returning None for anything outside `READINESS_VALUES`).
  PIN THE WRITE TARGET WITH AN ASSERTION, NOT ONLY WITH PROSE. This is the property that makes an agent-runnable readiness writer legitimate at all, and the field is read FIRST by the auto-approve predicate, so a silent widening is the highest-consequence regression this plan could cause. Add a test asserting the written value is exactly `go-pending-approval` for EVERY input that is permitted to write, including a case constructed to request `go`, plus a case proving an ABSENT field is refused rather than minted.
  - Depends on: E-01
  - Expected outcome: the verb writes at most `no-go -> go-pending-approval`; every other transition, an absent field, and a corrupt field are each refused with a message naming which condition or precondition failed; and a test FAILS if the write target is ever widened beyond `go-pending-approval` or if an absent field is minted.
  - Execution state: pending

- [ ] E-03 RECORD THE RE-CHECK IN THE PLAN'S OWN `## Workflow history` WITH THE EVIDENCE IT COMPUTED, so the new verdict carries its basis exactly as a review's does. The entry must name the three conditions it evaluated, state that each was found clear, and cite the prior review it is re-checking (its date and its finding span), so a reader can tell a re-check from a review at a glance and can audit the claim without re-running anything.
  DO NOT WRITE A REVIEW VERDICT. The entry is a re-check, must be labelled as one, and must not contain a verdict token from the review vocabulary (`APPROVE`, `APPROVE WITH REVISIONS APPLIED`, `REVIEWED - OPEN QUESTIONS`, `REJECT - NEEDS REPLAN`), because `newest_verdict` scans history prose for exactly those tokens and would then read this entry as a review. VERIFY that by running `newest_verdict` over the amended text and asserting the returned entry is still the REVIEW's, not the re-check's.
  - Depends on: E-02
  - Expected outcome: an amended history entry naming the three conditions, their evidence, and the re-checked review; plus a demonstration that `newest_verdict` still resolves to the original review entry afterwards.
  - Execution state: pending

### Task group 2: reach it, document it, and use it

- [ ] E-04 EXPOSE IT AS A CLI VERB AND WIRE THE THREE SURFACES A NEW VERB MUST TOUCH, following the existing pattern rather than inventing one: the parser in `cli.py`, the command inventory in `command_surface.py`, and shell completion in `completion.py`. Those three are what the repository's own history shows must move together for a verb to be reachable and discoverable.
  DEFAULT TO A DRY RUN, like `aw ipd scaffold` and `aw ipd sync` already do (`--apply` to write), because this verb edits an attestation field and the preview is what lets a human check the computed reasons before anything is written.
  - Depends on: E-03
  - Expected outcome: a dry-run-by-default verb that prints the per-condition verdict for one plan or a selector, writes only under `--apply`, appears in the command inventory, and completes in the shell.
  - Execution state: pending

- [ ] E-05 AMEND THE PLAN-REVIEW CONTRACT ON TWO POINTS: that a NON-BLOCKING open question does not make a plan `no-go`, and that a `no-go` is RE-EVALUABLE. Amend `.aw/system/workflows/plan-review/plan-review.md` beside the readiness vocabulary (`:533-548`).
  THE WORDING CHANGE IS NOW MANDATORY, NOT OPTIONAL, because the maintainer ruled against the text as written. `:543` currently defines `NO-GO` as "any open question, any unfixed BLOCKER/HIGH, or a `REVIEWED - OPEN QUESTIONS` / `REJECT - NEEDS REPLAN` verdict"; the first clause must become an unresolved BLOCKING open question. Leaving it unamended would put the shipped contract in direct conflict with E-01's computation, which is the drift this repository forbids. Note `:539-542` already describes `go-pending-approval` as the state for a plan that "passed review and only awaits approval", so the amendment makes the two passages agree rather than introducing a new idea.
  ALSO KEEP THE TWO RULES THAT MUST NOT LOOSEN: only a review may set `go`, and `go` still requires human approval.
  THIS IS A DECLARED SPEC-ADJACENT EDIT: the file is in `Scope-Paths` deliberately, per the repository rule that a plan amending a governing document must declare it so the runner can announce it before the run.
  - Depends on: E-04
  - Expected outcome: the readiness section defines the first `no-go` condition as an unresolved BLOCKING open question (citing the maintainer's 2026-09-10 ruling), states that `no-go` is re-evaluable, names the verb, notes the answered-finding return path, and preserves both that only a review may set `go` and that `go` requires human approval.
  - Execution state: pending

- [ ] E-07 CLOSE THE ONE-DIRECTIONAL ESCALATION LOOP, so a finding whose escalated question has been ANSWERED stops blocking. THIS IS THE SAME DEFECT THIS PLAN EXISTS TO FIX, ONE LAYER UP, and without it the re-check refuses on findings the maintainer has already settled. MEASURED at HEAD `ce33d3c1`: `4h7tt0` PR-002 (`HIGH`), `kbqpkn` PR-801 (`BLOCKER`), `5lxvl3` PR-002 (`HIGH`), `y9vpvv` PR-904 (`HIGH`) and `daexj1` PR-401 (`BLOCKER`) are ALL still `OPEN` in their typed review records, while every one of their escalated `Blocking: yes` questions is now `- Status: resolved` with the maintainer's 2026-09-10 answer recorded. `subject_gating_blocks` reads that column and blocks, since "Only decisions OTHER than `fixed` block" (`review_findings.py:851-853`).
  THE ESCALATION IS DEFINED IN ONE DIRECTION ONLY. `plan-review.md:335-341` requires an unfixed finding at or above the gate threshold to be escalated INTO the plan as a `Blocking: yes` question carrying `- Finding: <ID>`. Nothing defines the return path, so answering the question leaves the finding untouched forever.
  REPORT, THEN WRITE ONLY UNDER `--apply`, exactly like the readiness half: for each plan, match a resolved question's `- Finding: <ID>` against the review record's current-round findings, and where the question is resolved while the finding is not, report the finding as STALE and offer to mark it `fixed` by appending a NEW `## Round <n>` that cites the answered question and its date.
  DO NOT SILENTLY IGNORE A STALE FINDING INSTEAD OF RESOLVING IT. Making the re-check skip a finding whose question is resolved would clear a plan on an inference about another artifact's contents rather than on that artifact's own record, which is fail-open. Append a round; leave an audit trail.
  - Depends on: E-04
  - Expected outcome: for each of the five measured plans, the stale finding is reported with the resolved question that settles it, and under `--apply` a new round marks it `fixed`; `subject_gating_blocks` then returns empty for that plan. Nothing is written without `--apply`.
  - Execution state: pending

- [ ] E-06 RUN BOTH HALVES OVER THE STRANDED SET AND RECORD THE SURVIVING REASON PER PLAN, one row each, refusals included. THE DELIVERABLE IS THE PER-PLAN REASON, NOT A COUNT OF PLANS CLEARED. Measured at HEAD `ce33d3c1`, nine plans carry `no-go` with no unresolved BLOCKING question (`4h7tt0`, `5lxvl3`, `8tgg6g`, `daexj1`, `dw7i3m`, `kbqpkn`, `u06zo2`, `wmnmei`, `y9vpvv`), and running the shipped `approval_refusals` over them shows only ONE (`dw7i3m`) clears while EIGHT hold on a second, independent refusal. RE-MEASURE AND PRINT THE COMMAND rather than trusting any list in this plan, including this corrected one: five of the nine had their blocking question answered on 2026-09-10, four were stranded before that date, and E-07 changes the answer for five of them.
  EXPECT REFUSALS AND DO NOT TREAT THEM AS FAILURES, BUT NOTE THE MAINTAINER'S OQ-01 RULING REMOVED ONE OF THE TWO CAUSES. Under that ruling a non-blocking question no longer holds a plan at `no-go`, so the four plans previously held on that ground (`u06zo2`, `wmnmei`, `daexj1`, `y9vpvv`) are no longer held by it. The SURVIVING cause among the nine is the unresolved gating finding, on `4h7tt0`, `5lxvl3`, `8tgg6g`, `kbqpkn` and `y9vpvv`, which is exactly what E-07 closes. So the expected shape after E-07 is that most of the nine clear; RE-MEASURE and report the truth rather than either prediction, and if a plan still refuses, name the specific condition.
  - Depends on: E-07
  - Expected outcome: a re-measured per-plan table with the command that produced it, each row naming the three condition results and the action taken (updated, or refused with the specific surviving cause), plus `aw att --type plan --readiness no-go` before and after. Every refusal is explained rather than worked around.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A readiness value is an ATTESTATION owned by `/plan-review`, and `AGENTS.md` forbids an agent hand-writing one, because the auto-approve predicate reads the field FIRST and a hand-written value asserts a review that never happened. That is why this plan adds a verb that COMPUTES the field from conditions instead of a licence to edit it.
- `read_readiness` fails closed: anything outside `READINESS_VALUES` (`go`, `go-pending-approval`, `no-go`) returns None (`ipd_schema.py:311-329`), and `approval_refusals` treats an out-of-vocab field as CORRUPT with no fallback while an ABSENT field falls back to prose (`plan_readiness.py:474-495`). The re-check must preserve that asymmetry rather than smoothing it.
- The open-question half of the approval refusal IS overridable (`allow_open_questions`), but a negative verdict and a typed gating finding have NO override at all, by design, so that no flag can turn "do not build this" into "executable". This plan does not add an override; it recomputes the verdict.
- A new CLI verb must be wired in three places (`cli.py`, `command_surface.py`, `completion.py`) or it is unreachable or undiscoverable.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | A `no-go` readiness is never re-evaluated. Measured at HEAD `ce33d3c1`: of 70 pending plans carrying a `- Readiness:` field, 14 are `no-go`, and 9 of those have NO unresolved blocking question left, so the cause RECORDED IN THE HISTORY is spent while the refusal stands. Note precisely what this does and does not say: it does NOT say those nine are otherwise clean. See F-7. |
| F-7 | HIGH | Only ONE of the nine would actually clear. Running the shipped `approval_refusals` over the nine at HEAD `ce33d3c1`: `dw7i3m` yields one refusal (the readiness field itself, which the verb rewrites) and clears; the other eight each yield a SECOND independent refusal the verb must honor, five from an unresolved gating finding and four from non-blocking open questions (`y9vpvv` has both). So the verb refuses 8 of 9 on first use, correctly. This is why the Goal claims visibility of the surviving reason rather than clearing plans. |
| F-8 | HIGH | The escalation path is one-directional, and five of the eight surviving refusals come from that. A finding at or above the gate threshold is escalated into the plan as a `Blocking: yes` question (`plan-review.md:335-341`), but nothing defines the return path, so answering the question leaves the finding `OPEN` forever. Measured: `4h7tt0` PR-002, `kbqpkn` PR-801, `5lxvl3` PR-002, `y9vpvv` PR-904 and `daexj1` PR-401 are all still `OPEN` while their escalated questions are `resolved` with the maintainer's 2026-09-10 answers. E-07 closes it. |
| F-2 | HIGH | The refusal that reads the field has no override, and says so in its own message: "This refusal has NO override: get the review's readiness changed (re-run /plan-review) rather than forcing the approval." (`plan_readiness.py:480-484`). So answering a question cannot unstick a plan by construction, and the only sanctioned remedy is a full re-review. |
| F-3 | MEDIUM | The problem predates this session and is accumulating. Four of the nine (`8tgg6g`, `dw7i3m`, `daexj1`, `u06zo2`) were stranded before 2026-09-10, and `8tgg6g` carries 16 findings, 12 decisions and zero open questions while still reading `no-go`. |
| F-4 | MEDIUM | The reviews were NOT truncated, so a fresh critique is the wrong remedy. Each swept the whole document to LOW severity with fixes applied in place (`wmnmei` PR-001..PR-014, `kbqpkn` PR-801..PR-810, `4h7tt0` PR-001..PR-008, `5lxvl3` PR-001..PR-009). "NO-GO on one question alone" describes the only UNFIXED item, not where review stopped. |
| F-5 | MEDIUM | The three `no-go` conditions are already written down and already computable, so this needs no new policy: the contract enumerates them (`plan-review.md:543-545`) and `plan_readiness.py` already composes all three inside `approval_refusals`. The gap is that nothing recomputes them after the fact. |
| F-6 | MEDIUM | SPENT BY THE MAINTAINER'S 2026-09-10 RULING ON OQ-01; retained because it explains why E-05 amends the contract. As authored this read: the wording says "any open question", not "any blocking open question", so four plans (`u06zo2` OQ-03/OQ-05, `wmnmei` OQ-02, `daexj1` OQ-01, `y9vpvv` OQ-01/OQ-02) legitimately remain `no-go`. The maintainer ruled the opposite: a non-blocking question does NOT make a plan not-ready, so those four no longer hold on that ground and the WORDING is what must change. Measured scale behind the ruling: 43 of 104 pending plans carry only non-blocking questions (64 questions, 27 owned by an executor). |

## Proposed changes (ordered, validatable)

1. A per-condition readiness recomputation composed from the three shipped predicates (E-01).
2. A write path that can only clear `no-go -> go-pending-approval`, refuses an absent or corrupt field, and is pinned by a test that fails if widened (E-02).
3. A history entry carrying the computed evidence, provably not readable as a review verdict (E-03).
4. A dry-run-by-default CLI verb wired into the parser, inventory and completion (E-04).
5. The plan-review contract stating that `no-go` is re-evaluable and that only a review may set `go` (E-05).
6. The return path for an escalated finding whose question has been answered, so it stops blocking (E-07).
7. Both halves run over the re-measured stranded set, reporting the surviving cause per plan (E-06).

## Deferred / out of scope (with reason)

- CHANGING WHAT `no-go` MEANS, or adding an override to the refusal. Deferred deliberately: the refusal's lack of an override is the property that stops a flag turning "do not build this" into "executable", and this plan's whole approach is to recompute the verdict rather than to bypass it.
- CLEARING ANY READINESS BY HAND, including the nine. Out of scope by construction: if the verb refuses a plan, that plan stays `no-go` and a human or a review decides, which is the point of building a computation rather than granting an editing licence.
- BACKFILLING THE READINESS FIELD ON THE 34 PENDING PLANS THAT LACK ONE (70 of 104 carry it). Absence is a legitimate state that falls back to prose, and minting values for the rest is a separate decision.
- RE-REVIEWING ANY PLAN. Explicitly declined by the maintainer as duplicated effort, on evidence that the reviews were complete (F-4).

## Scope check

- Over-scope: none. The paths named are the two predicate modules, the three verb-wiring surfaces, one new test file, and the one contract document whose wording defines the conditions being recomputed. `review_findings.py` was ADDED at review, not for convenience but because five of the eight surviving refusals originate in the records it owns (F-8); a re-check shipped without it reports a cause the maintainer has already settled.
- Under-scope: this plan does not fix the four plans whose `no-go` is legitimate under F-6; it reports them with their specific open questions. It does not address `Readiness` absent entirely, deferred above. It does not define a general return path for every artifact type's escalated findings; E-07 closes the loop for the plan-and-review pair this plan measures, and a wider contract change is a separate decision.

## Required tests / validation

A new `tests/test_plan_readiness_recheck.py`, plus a falsification pass: every new assertion must be shown to FAIL against the pre-change code, since a test that passes both before and after proves nothing.

ESTABLISH THE SUITE BASELINE BY RUNNING IT, BEFORE THE FIRST EDIT, and paste that output as the comparison point. NO BASELINE FIGURE IS STATED IN THIS PLAN DELIBERATELY: an earlier draft carried a count copied from a prior session's notes rather than observed, which is exactly the unverified number this repository's contract forbids pasting, and a hedge like "re-measure before relying on it" does not repair it because an executor would still be comparing against fiction. Run `python3 -m pytest` bare (the configured `addopts` already supply quiet, parallel, fast-subset), record the summary line, and name any failure as pre-existing or new against that self-established baseline.

## Spec / documentation sync

`.aw/system/workflows/plan-review/plan-review.md` is amended by E-05 and is declared in `Scope-Paths` so the runner announces the edit before the run. WHY: the readiness vocabulary in that file is the contract this plan recomputes, so leaving it silent about re-evaluability would let the next reviewer re-create the trap while following the documented process correctly.

E-05 SHOULD ALSO NOTE THE RETURN PATH, because the same document defines the escalation in one direction only (`:335-341`) and that omission is what F-8 measures. State that a finding whose escalated question has been answered is stale and how it is cleared, keeping the amendment to the smallest wording that closes the loop. Do NOT widen the escalation contract itself here: E-07 implements the return path for the plan-and-review pair, and any broader obligation on other artifact types is a separate decision.

## Open questions

### OQ-01: Does a NON-blocking open question keep a plan at `no-go`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): A NON-BLOCKING OPEN QUESTION DOES NOT MAKE A PLAN NOT-READY. `no-go` is reserved for a BLOCKING open question, an unfixed gating finding, or an unsound approach. The reviewer's interim literal reading (recorded as D-2) is SUPERSEDED, and E-05 must now amend the contract wording to match rather than merely note re-evaluability.
  THE REASONING, WHICH GENERALIZES: the `- Blocking:` flag exists precisely to record which questions must stop work, so treating blocking and non-blocking questions identically discards the distinction the field was created to carry. Under the literal reading the flag had almost no consequence, which is itself evidence the reading was wrong.
  THIS DECIDES 43 PLANS, NOT ONE, WHICH IS WHY IT WAS PUT TO THE MAINTAINER WITH THE SCALE STATED. Measured at HEAD `781d70ae` across 104 pending plans: 7 carry a blocking open question, 54 carry none at all, and 43 carry ONLY non-blocking questions, 64 such questions between them, of which 27 are owned by an executor rather than the maintainer. So the literal reading was holding 43 of 104 plans at `no-go` for reasons their own authors had judged non-stopping.
  CONSEQUENCES FOR THIS PLAN, all of which narrow it usefully. FIRST, the third `no-go` condition in E-01 is now "an unresolved BLOCKING question", so E-01 should compose `plan_readiness.has_unresolved_blocking_question` directly (it already tests exactly that) rather than counting every open question. SECOND, F-6's four-plan hold list is SPENT: `u06zo2`, `wmnmei`, `daexj1` and `y9vpvv` no longer stay `no-go` on their non-blocking questions, so the only surviving cause among the nine is the gating-finding staleness E-07 closes. E-06 must re-measure rather than reuse either list. THIRD, `approval_refusals` uses the STRICTER `Status != "resolved"` rule and treats the open-question half as OVERRIDABLE (`allow_open_questions`), so the executor must state explicitly how the re-check consumes that half under this answer instead of inheriting the strict default silently.
  ACCEPTED COST, RECORDED BECAUSE THE MAINTAINER WAS SHOWN IT: a question mislabelled `Blocking: no` when it truly does block will no longer hold its plan back. The mitigation is that mislabelling is now the single point of failure and is visible in the plan itself, rather than every question silently blocking.

### OQ-02: Should the re-check be run automatically after an `/askme` answer, or stay explicit?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW (recorded as D-1 in the typed review record): STAY EXPLICIT. Resolved rather than left open because this plan's own structure already depends on the answer, so leaving it open invited an executor to re-litigate a decision the design rests on, and because every open question holds the plan at `no-go` under the contract's literal wording, which is the pathology this plan exists to reduce.
  THE BASIS IS IN THIS PLAN AND IN THE ANSWERING WORKFLOW. The gate below requires the verb to record its computed evidence, and E-04 makes dry-run the DEFAULT precisely so a human reads the computed reasons before anything is written; `.aw/system/workflows/askme/askme.md` scopes that workflow to recording an answer in the owning artifact and states it "Does NOT ... move an artifact through its lifecycle".
  TWO ALTERNATIVES WERE REJECTED. (a) Auto-run on every recorded answer: rejected because writing an attestation as a SIDE EFFECT of answering is the same shape as the defect being fixed, a field written without its conditions checked at the point of writing. (b) Auto-run in a report-only mode: rejected as strictly weaker than the explicit verb it would duplicate, since an operator must still read and act on the report.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new predicate's output for THREE fixtures: a plan with an unresolved blocking question, a plan with a typed gating finding, and a plan with a negative prose verdict. Each must report the specific condition that holds, with its reason string. THEN paste the ANTI-FORK proof: a grep showing the new code calls the existing `has_unresolved_blocking_question`, `subject_gating_blocks` and `newest_verdict` (or a helper factored from `approval_refusals`) rather than reimplementing any of them, plus `python3 -m pytest tests/test_review_findings_gate.py -o addopts=""` passing unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste FOUR refusals with their unpiped exit codes: a plan with a condition still holding, a plan whose `- Readiness:` field is ABSENT, a plan whose field is out-of-vocab (e.g. `Readiness: bogus`), and a plan already at `go-pending-approval`. Then paste the one PERMITTED case showing `no-go -> go-pending-approval` and `git diff` of the single changed line.
    THEN PASTE THE PINNING TEST AND ITS FALSIFICATION, which is the part prose cannot deliver: name the test asserting the write target is exactly `go-pending-approval` for every permitted input, run it, and then run it against a deliberately WIDENED copy of the writer (one that would emit `go`) showing it FAILS there. A test that passes against both proves nothing. Include the absent-field case in the same falsification.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the amended history entry verbatim, then paste the output of `plan_readiness.newest_verdict` over the amended text proving it still returns the REVIEW entry and not the re-check entry. Paste a grep of the new entry showing it contains none of the four review verdict tokens.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the verb run with no `--apply` showing it wrote nothing (`git status --porcelain` clean afterwards), then the same with `--apply` showing exactly one line changed. Paste the three wiring proofs: the verb in `aw --help`, its presence in the command inventory, and its appearance in generated completion output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the amended readiness section of `plan-review.md` and a `git diff` of it, showing THREE things: the first `no-go` condition now reads as an unresolved BLOCKING open question, the re-evaluability sentence added, and the `go`-requires-review-plus-approval rule intact. State the diff's line count; a near-empty diff means the edit did not land. THEN paste the CONSISTENCY PROOF: E-01's computation and the amended wording must agree on the first condition, shown by quoting both side by side, since a contract that still says "any open question" while the code tests only blocking ones is the drift this item exists to prevent.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the re-measured stranded set with the command that produced it (do not reuse this plan's list), then the per-plan table showing each of the three conditions and the action taken. Paste the resulting `aw att --type plan --readiness no-go` output before and after. Every refusal must be accompanied by the SPECIFIC surviving cause, distinguishing an unresolved gating finding from a non-blocking open question, and `y9vpvv` must show both if both still hold. State the cleared count plainly; if it is 1, say 1, and do not present a refusal as a partial success. Finally paste the bare `python3 -m pytest` summary line and compare it to the baseline this plan's validation section requires you to establish first, naming any failure as pre-existing or new.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: for ONE of the five measured plans, paste `review_findings.subject_gating_blocks(repo, '<id6>')` BEFORE the change (non-empty, naming the finding) and AFTER (empty), plus the appended `## Round <n>` showing the finding marked `fixed` with the resolved question and its date cited. Paste the resolved question's `- Finding: <ID>` line from the plan as the evidence the match was made on identity rather than on guesswork. Then paste the DRY-RUN case proving nothing was written without `--apply` (`git status --porcelain` clean afterwards). Finally paste the NEGATIVE case: a finding whose escalated question is still `open` must NOT be reported stale.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE HAZARD THAT DEFINES THIS PLAN: it builds a verb that writes an attestation field an agent is otherwise forbidden to hand-write. The prohibition is not being relaxed. What makes the verb legitimate is that it COMPUTES the value from conditions and records the evidence, and that it can only ever reach `go-pending-approval`, which still requires a human. If any change to this plan would let the verb write `go`, mint a readiness that was absent, or skip the evidence entry, that change is out of scope and must be refused.
