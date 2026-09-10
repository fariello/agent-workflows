# IPD: Re-evaluate a stale no-go readiness whose recorded cause is gone, instead of stranding the plan

- Date: 2026-09-10
- Kind: child
- Concern: A `- Readiness: no-go` records a MOMENT, not a condition, and nothing re-evaluates it when the cause it was set for is removed, so a plan whose blocking question has been answered stays permanently unapprovable behind a refusal that has no override.
- Scope: Add a narrow, evidence-citing readiness RE-CHECK that recomputes the three `no-go` conditions the plan-review contract already defines, updates the field when all three are clear, and refuses to touch it otherwise; then run it over the nine currently-stranded plans. Does NOT re-critique a plan, does NOT approve anything, and does NOT let an agent assert a readiness it did not compute.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, tests/test_plan_readiness_recheck.py, .aw/system/workflows/plan-review/plan-review.md
- Item-Dependencies: none
- Status: to-review
- Set: rdyrecheck
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qhy3i3
- From-Backlog: none

## Workflow history
- 2026-09-10 to-review (aw set): set Item-Dependencies to none

- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from a maintainer decision taken during an `/askme` round. Asked how nine plans carrying a stale `no-go` should be handled, the maintainer chose "add a narrow re-check step, and use it on all nine" over clearing the field by hand, over a full re-review, and over leaving them. THE MAINTAINER'S OWN CHALLENGE SHAPED THE SCOPE: seeing reviews that ended "on one question alone", they asked whether the reviewer "really reviewed the rest of the doc and/or if the doc really needs a full fresh review". MEASURED, and the answer split: the reviews DID sweep the whole document (PR-001..PR-014 on `wmnmei`, PR-801..PR-810 on `kbqpkn`, PR-001..PR-008 on `4h7tt0`, PR-001..PR-009 on `5lxvl3`, plus 4 to 12 recorded decisions each, all applied in place), so a fresh critique would re-derive settled findings and is NOT warranted; but nothing re-evaluates the verdict, which is a design gap rather than a clerical one. Hence a re-check, not a re-review.

## Goal

Make a `no-go` readiness a RE-EVALUABLE claim rather than a permanent one, so that answering the question a review was blocked on actually clears the plan, and so no agent has to forge a review verdict to unstick work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: compute the verdict from conditions rather than from memory

- [ ] E-01 ADD A PURE PREDICATE THAT RECOMPUTES THE THREE `no-go` CONDITIONS AND RETURNS THEM INDIVIDUALLY, in `plan_readiness.py`, reusing the shipped predicates rather than re-deriving any of them. The plan-review contract defines `NO-GO` as exactly three conditions (`.aw/system/workflows/plan-review/plan-review.md:543-545`): "any open question, any unfixed BLOCKER/HIGH, or a `REVIEWED - OPEN QUESTIONS` / `REJECT - NEEDS REPLAN` verdict". All three are already computable in this module: `has_unresolved_blocking_question` (`:265`), `review_findings.subject_gating_blocks` (composed at `:425` in `approval_refusals`), and `newest_verdict` (`:378`).
  RETURN THE THREE SEPARATELY, NOT A BOOLEAN. The whole defect being fixed is that a verdict lost its reason; a re-check that also collapses to one bit reintroduces it one layer down. The caller must be able to say WHICH condition still holds, and the record must name it.
  DO NOT FORK `approval_refusals`. It is documented as "THE ONE PREDICATE EVERY APPROVAL SURFACE CONSUMES" with two callers (`status_set.py:561`, `specs.py:584`) and an explicit anti-fork guard test at `tests/test_review_findings_gate.py`. Compose it or factor a shared helper out of it; do not copy its logic.
  - Depends on: none
  - Expected outcome: a function returning a per-condition result (open questions, gating findings, negative verdict) with a human-readable reason string for each condition that still holds, and no new copy of any existing predicate.
  - Execution state: pending

- [ ] E-02 MAKE THE RE-CHECK REFUSE TO WRITE WHENEVER ANY CONDITION STILL HOLDS, and write only `no-go -> go-pending-approval`. This is the safety property that makes the verb something an agent may run: it can only ever move a plan to the state that still requires human approval, never to `go`, and never onto a plan whose readiness is absent or already approvable.
  IT MUST NOT INVENT A READINESS. If the field is ABSENT, refuse and say so: absence means no review recorded a signal, and minting one here would be the same forgery `AGENTS.md` forbids when it says never to hand-write a `- Readiness:`. If the value is OUT-OF-VOCAB, refuse too, matching `read_readiness`'s fail-closed contract (`ipd_schema.py:311-329`, returning None for anything outside `READINESS_VALUES`).
  - Depends on: E-01
  - Expected outcome: the verb writes at most `no-go -> go-pending-approval`; every other transition, an absent field, and a corrupt field are each refused with a message naming which condition or precondition failed.
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

- [ ] E-05 STATE IN THE PLAN-REVIEW CONTRACT THAT `no-go` IS RE-EVALUABLE, and name the verb, so the next reviewer does not re-create the trap by treating the field as final. Amend `.aw/system/workflows/plan-review/plan-review.md` beside the readiness vocabulary (`:534-548`), keeping the amendment to the smallest wording that says a `no-go` recorded for a condition that is later cleared should be re-checked rather than re-reviewed, and that only a review may set `go`.
  THIS IS A DECLARED SPEC-ADJACENT EDIT: the file is in `Scope-Paths` deliberately, per the repository rule that a plan amending a governing document must declare it so the runner can announce it before the run.
  - Depends on: E-04
  - Expected outcome: the readiness section states that `no-go` is re-evaluable, names the verb, and preserves the rule that `go` requires a review plus human approval.
  - Execution state: pending

- [ ] E-06 RUN THE RE-CHECK OVER THE NINE STRANDED PLANS AND RECORD WHAT IT DECIDED FOR EACH, one line per plan, including any it REFUSES. Measured at HEAD `e71ca8b5`, the nine carrying `no-go` with no unresolved blocking question are `4h7tt0`, `5lxvl3`, `8tgg6g`, `daexj1`, `dw7i3m`, `kbqpkn`, `u06zo2`, `wmnmei`, `y9vpvv`. Re-measure the set rather than trusting this list: five had their blocking question answered on 2026-09-10 and four were already stranded before that date, so the set will have moved if any review or `/askme` round has run since.
  EXPECT REFUSALS AND DO NOT TREAT THEM AS FAILURES. `u06zo2` and `wmnmei` still carry NON-blocking open questions, and `y9vpvv` records no cause for its `no-go` at all; whether a non-blocking question is a `no-go` condition is decided by the contract wording (it says "any open question"), so at least three of the nine may legitimately stay `no-go`. Report which and why.
  - Depends on: E-05
  - Expected outcome: a per-plan table of the nine (re-measured), each row showing the three condition results and the action taken (updated or refused with the reason), and the refusals explained rather than worked around.
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
| F-1 | HIGH | A `no-go` readiness is never re-evaluated. Measured at HEAD `e71ca8b5`: of 70 pending plans carrying a `- Readiness:` field, 14 are `no-go`, and 9 of those have NO unresolved blocking question left, so their recorded cause is gone while the refusal stands. |
| F-2 | HIGH | The refusal that reads the field has no override, and says so in its own message: "This refusal has NO override: get the review's readiness changed (re-run /plan-review) rather than forcing the approval." (`plan_readiness.py:480-484`). So answering a question cannot unstick a plan by construction, and the only sanctioned remedy is a full re-review. |
| F-3 | MEDIUM | The problem predates this session and is accumulating. Four of the nine (`8tgg6g`, `dw7i3m`, `daexj1`, `u06zo2`) were stranded before 2026-09-10, and `8tgg6g` carries 16 findings, 12 decisions and zero open questions while still reading `no-go`. |
| F-4 | MEDIUM | The reviews were NOT truncated, so a fresh critique is the wrong remedy. Each swept the whole document to LOW severity with fixes applied in place (`wmnmei` PR-001..PR-014, `kbqpkn` PR-801..PR-810, `4h7tt0` PR-001..PR-008, `5lxvl3` PR-001..PR-009). "NO-GO on one question alone" describes the only UNFIXED item, not where review stopped. |
| F-5 | MEDIUM | The three `no-go` conditions are already written down and already computable, so this needs no new policy: the contract enumerates them (`plan-review.md:543-545`) and `plan_readiness.py` already composes all three inside `approval_refusals`. The gap is that nothing recomputes them after the fact. |
| F-6 | LOW | The contract's wording says "any open question", not "any blocking open question", so plans carrying non-blocking questions (`u06zo2`, `wmnmei`) may legitimately remain `no-go`. E-06 must report that rather than clearing them to make the number look better. |

## Proposed changes (ordered, validatable)

1. A per-condition readiness recomputation composed from the three shipped predicates (E-01).
2. A write path that can only clear `no-go -> go-pending-approval`, and refuses an absent or corrupt field (E-02).
3. A history entry carrying the computed evidence, provably not readable as a review verdict (E-03).
4. A dry-run-by-default CLI verb wired into the parser, inventory and completion (E-04).
5. The plan-review contract stating that `no-go` is re-evaluable and that only a review may set `go` (E-05).
6. The verb run over the re-measured stranded set, with refusals reported (E-06).

## Deferred / out of scope (with reason)

- CHANGING WHAT `no-go` MEANS, or adding an override to the refusal. Deferred deliberately: the refusal's lack of an override is the property that stops a flag turning "do not build this" into "executable", and this plan's whole approach is to recompute the verdict rather than to bypass it.
- CLEARING ANY READINESS BY HAND, including the nine. Out of scope by construction: if the verb refuses a plan, that plan stays `no-go` and a human or a review decides, which is the point of building a computation rather than granting an editing licence.
- BACKFILLING THE READINESS FIELD ON THE 34 PENDING PLANS THAT LACK ONE (70 of 104 carry it). Absence is a legitimate state that falls back to prose, and minting values for the rest is a separate decision.
- RE-REVIEWING ANY PLAN. Explicitly declined by the maintainer as duplicated effort, on evidence that the reviews were complete (F-4).

## Scope check

- Over-scope: none. The five code paths named are the predicate module, the three verb-wiring surfaces, one new test file, and the one contract document whose wording defines the conditions being recomputed.
- Under-scope: this plan does not fix the four plans whose `no-go` may be legitimate under F-6; it reports them. It also does not address `Readiness` absent entirely, which is deferred above.

## Required tests / validation

A new `tests/test_plan_readiness_recheck.py`, plus a falsification pass: every new assertion must be shown to FAIL against the pre-change code, since a test that passes both before and after proves nothing. The bare suite (`python3 -m pytest`) must be run and its actual summary line pasted, compared against the baseline recorded at authoring (`5859 passed, 3 skipped, 2 xfailed`, re-measure before relying on it).

## Spec / documentation sync

`.aw/system/workflows/plan-review/plan-review.md` is amended by E-05 and is declared in `Scope-Paths` so the runner announces the edit before the run. WHY: the readiness vocabulary in that file is the contract this plan recomputes, so leaving it silent about re-evaluability would let the next reviewer re-create the trap while following the documented process correctly.

## Open questions

### OQ-01: Does a NON-blocking open question keep a plan at `no-go`?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer only if the executor concludes the contract wording should change
- Resolution or deferral rationale: THE CONTRACT WORDING SAYS "any open question" (`plan-review.md:543`), which reads as YES and is the fail-closed reading, so E-06 should apply it and report the affected plans rather than quietly clearing them. It is recorded as a question rather than settled because the same document calls `go-pending-approval` the correct state for a plan that "passed review and only awaits approval", and a plan whose only remainder is a LOW-severity non-blocking question arguably fits that description. The executor should apply the literal wording, name the plans it holds back (measured: at least `u06zo2` and `wmnmei`), and escalate ONLY if that produces an outcome the contract's own description contradicts. Non-blocking because the verb is correct and useful under either reading; the reading changes only how many of the nine clear.

### OQ-02: Should the re-check be run automatically after an `/askme` answer, or stay explicit?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVE FROM EVIDENCE AT EXECUTION TIME, and the default is EXPLICIT. This plan deliberately builds a verb a human or agent invokes, because the failure being fixed came from a field being written without its conditions being checked, and wiring an automatic write into the answer path would recreate that shape one level up. The executor should confirm the verb is idempotent and cheap enough that an explicit call costs nothing, and record that; if it is, explicit stays and this closes without a maintainer decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new predicate's output for THREE fixtures: a plan with an unresolved blocking question, a plan with a typed gating finding, and a plan with a negative prose verdict. Each must report the specific condition that holds, with its reason string. THEN paste the ANTI-FORK proof: a grep showing the new code calls the existing `has_unresolved_blocking_question`, `subject_gating_blocks` and `newest_verdict` (or a helper factored from `approval_refusals`) rather than reimplementing any of them, plus `python3 -m pytest tests/test_review_findings_gate.py -o addopts=""` passing unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste FOUR refusals with their unpiped exit codes: a plan with a condition still holding, a plan whose `- Readiness:` field is ABSENT, a plan whose field is out-of-vocab (e.g. `Readiness: bogus`), and a plan already at `go-pending-approval`. Then paste the one PERMITTED case showing `no-go -> go-pending-approval` and `git diff` of the single changed line. Prove `go` is unreachable: attempt it and paste the refusal.
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
  - Required evidence: paste the amended readiness section of `plan-review.md` and a `git diff` of it, showing the re-evaluability sentence added and the `go`-requires-review-plus-approval rule intact. State the diff's line count; a near-empty diff means the edit did not land.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the re-measured stranded set with the command that produced it (do not reuse this plan's list), then the per-plan table showing each of the three conditions and the action taken. Paste the resulting `aw att --type plan --readiness no-go` output before and after. Every refusal must be accompanied by the condition that caused it. Finally paste the bare `python3 -m pytest` summary line and name any failure as pre-existing or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE HAZARD THAT DEFINES THIS PLAN: it builds a verb that writes an attestation field an agent is otherwise forbidden to hand-write. The prohibition is not being relaxed. What makes the verb legitimate is that it COMPUTES the value from conditions and records the evidence, and that it can only ever reach `go-pending-approval`, which still requires a human. If any change to this plan would let the verb write `go`, mint a readiness that was absent, or skip the evidence entry, that change is out of scope and must be refused.
