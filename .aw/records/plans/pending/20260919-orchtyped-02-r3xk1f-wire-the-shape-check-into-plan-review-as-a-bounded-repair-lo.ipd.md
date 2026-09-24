# IPD: Wire the shape check into plan-review as a bounded repair loop with honest exhaustion

- Date: 2026-09-19
- Kind: child
- Concern: The existing orchestrator control refuses at RUN START, where the remedy is exactly what a run must not do: edit another agent's plan. So an operator is told to go fix something by hand having already queued a run, and nothing in the pipeline offers to fix the violation at the one point licensed to rewrite a plan. Spec `r07vma` R5 puts the check where repair is possible. `/plan-review` already applies in-place revisions (its Step 2.4) and already re-runs `aw ipd lint --phase review-finalize` after them, so this is one more rule at a checkpoint that exists rather than a new mechanism.
  THE LOOP'S FAILURE MODES ARE THE DESIGN, NOT AN EDGE CASE. Two tempting behaviours are both wrong when the attempts run out: passing anyway launders a violation into an approved plan, and writing `- Readiness: no-go` asserts a verdict the review did not reach. R6 requires the honest third option, and the repository has already measured why the second is dangerous: on 2026-09-06 an agent authoring a four-plan Set wrote `Readiness: go-pending-approval` into all four having run no review, and the auto-approve predicate returned True for every one. That is why `aw ipd scaffold` omits the field and `ipd_lint` refuses an unattested value (`IPD-M107`).
- Scope: The `/plan-review` consumer of child 01's shared function. IN: calling that function for a `Kind: orchestrator` plan at the review checkpoint; asking the agent to repair a reported violation and re-running the check, up to a configurable attempt budget defaulting to 2; recording each attempt so a deletion-based "fix" is visible; and leaving an exhausted loop at `to-review` with `- Readiness:` ABSENT and the findings in the round record. OUT: the grammar and the function itself (child 01); the run-side gate (child 03); migrating any orchestrator (child 04); the merged-result proof (child 05); and any change to how `/plan-review` handles non-orchestrator plans.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, tests/test_plan_review_parity.py
- Item-Dependencies: executed:dpdyed
- Status: approved
- Readiness: go-pending-approval
- Set: orchtyped
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: r3xk1f
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-201..PR-208 all FIXED, none deferred, none open. Readiness go-pending-approval. Record: .aw/records/reviews/20260919-orchtyped-02-r3xk1f-wire-the-shape-check-into-plan-review-as-a-bounded-repair-lo.review.md. SELF-REVIEW twice over (same agent/model authored the plan AND applied the PR-007 corrections it carries), so its value rests on EXECUTING claims: I ran the parity suite, drove IPD-M107 both ways on a purpose-built fixture, ran three Kind-scan shapes against the real misclassifying plan, and grepped the long variant's step files. WHAT HELD: the 02/03 split is CORRECT and verified, since review-finalize appears only in 03-resolve-and-finalize.md and Readiness appears only there too (zero in 02); plan-review-long.md is indeed a step index with a real test refusing instructions placed there; F-1's anchor is exact; m7gvuz is Kind: child yet quotes Kind: orchestrator eleven times. THE HEADLINE FINDING, and the one a human should see: IPD-M107 DOES NOT COVER THE CASE E-03 EXISTS FOR. check_readiness_attestation is EVIDENCE-BASED not status-based and fires only when Readiness is present AND the history matches none of /plan-review, APPROVE, NO-GO, REJECT; so in E-03's own target case (a review that RAN then exhausted its budget) the history already names a review and the rule cannot distinguish a correct absence from a fabricated value. Verified both ways on a minimal fixture. The workflow INSTRUCTION therefore carries the whole weight, recorded as F-9 so the plan stops overclaiming its backstop. THE ROOT CAUSE OF MOST OF THE REST is that this child's product is PROSE and the plan had not reckoned with the cost: THREE of four V-items were UNSATISFIABLE as authored (a call-site behaviour test, a budget resolution trace, and a code-path grep, none of which exist when nothing executes a workflow body), and the declared tests/test_plan_review_orchestrator_repair.py had NO buildable content, since the only available assertion is a prose pin and this repo has DELETED that shape twice with the reason recorded in the very files this plan cites. Path withdrawn; the existing parity test is the whole test surface. Also PR-203 (the budget was described as configurable following a CLI-flag resolver a prose workflow cannot reach; adopt 2 per enforce_orchestrator_probe_gate's recorded precedent, which reused the flag and accepted 2 over a ruling naming 3 to avoid a second retry knob), PR-204 (V-04 was satisfiable by a log reading 'repaired' twice, which cannot distinguish the deletion from the relocation it exists to catch; row counts now required), PR-205 (F-5 named the wrong scan shape: CONTAINMENT misclassifies m7gvuz while first-match and anchored reads both return child), PR-206 (OQ-01 resolved to the round record from the reviews README plus the one-line-per-transition history contract), PR-207 (baseline recorded with the pre-existing unrelated reaskscore-corpus failure named) and PR-208 (F-8 raised LOW to MEDIUM, being the root cause rather than a footnote). Nothing was weakened: I strengthened the prohibition on repairing a real orchestrator while testing, adding 'use a fixture you author' to three items. Validation: author and review-finalize lint conform; carrier rule CLEAN at pre-transition; test_plan_review_parity 5 passed; bare suite 1 failed / 7305 passed with the single failure being the corpus-pinned reaskscore case proven pre-existing during child 01's review; aw check all reports 0 findings against this plan.

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 02 of Set `orchtyped`. Measured at HEAD `21eff5d8`: `plan-review.md` already runs `aw ipd lint --phase review-finalize` after revisions (its line 121) and already owns in-place revision (its Step 2.4), so the loop has an existing home. `runner_shared.resolve_retry_budget(None)` returns 2, which is the precedent this plan's default follows rather than inventing a number.

## Goal

Make a violating orchestrator get FIXED during review rather than merely reported at run time, by calling child 01's function at the review checkpoint, asking the agent to repair what it reports, and re-checking within a bounded budget; and make an exhausted loop say so honestly instead of passing or inventing a verdict.

READ THE SCOPE PRECISELY: this child adds no rule of its own. If its diff contains a row pattern, a status list, or a child-table scan, that is an R3 violation and the reviewer should refuse it, because child 01 owns the rule and this child owns only the call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

#### Task group 1: the call and the loop

- [x] E-01 CALL CHILD 01'S FUNCTION AT THE REVIEW CHECKPOINT, for a plan whose own first `- Kind:` bullet reads `orchestrator`, and nowhere else. READ THE KIND FROM THE PLAN'S OWN FIRST BULLET rather than by searching the file: a plan that QUOTES another plan's `- Kind: orchestrator` line in its prose would otherwise be misclassified, and that failure has already been made in this repository during this Set's own authoring (a scan matched `m7gvuz`, a `Kind: child` plan, on a quoted string, and reported it as an orchestrator carrying ten items).
  SITE THE CALL WHERE THE EXISTING POST-REVISION CHECK ALREADY RUNS, beside `aw ipd lint --phase review-finalize`, so the two structural gates are read together by an agent under load rather than one being missed.
  AND SITE IT IN BOTH VARIANTS' REVIEWER-FACING FILES, WHICH FOR THE LONG VARIANT MEANS THE STEP FILES AND NOT `plan-review-long.md` (corrected at review, PR-007). That file is a step index a reviewer never acts on, and `tests/test_plan_review_parity.py::OrchestratorIsNotAStepFileTests` exists because the mistake has already been made twice. Put the revision-side half in `02-review-and-revise.md` and the readiness/exhaustion half in `03-resolve-and-finalize.md`.
  - Depends on: none
  - Expected outcome: an orchestrator under review is checked; a `Kind: child` plan is not; a child plan quoting an orchestrator's Kind bullet is still not.
  - Execution state: performed

- [x] E-02 ASK THE AGENT TO REPAIR, AND RE-RUN THE CHECK, up to an attempt budget of 2.
  STATE THE BUDGET AS A NUMBER IN THE WORKFLOW PROSE AND BUILD NO KNOB (corrected at review, PR-203). A prose workflow has no CLI and no argparse namespace, so the "configurable, following `resolve_retry_budget`'s precedence" the plan originally specified was not implementable: that resolver takes a CLI value and is reached from `--retry-budget` on the two runners, and there is nothing for a reviewer following a markdown file to pass it.
  ADOPT 2 AND SAY SO, FOLLOWING THE IN-TREE PRECEDENT FOR THIS EXACT DECISION rather than re-deciding it. `enforce_orchestrator_probe_gate`'s docstring records "THE RETRY BUDGET IS THE EXISTING FLAG, DECIDED AND RECORDED": it reuses `--retry-budget`, accepts its default of 2 over a maintainer ruling that named 3, and gives the reason as "a second retry knob is exactly the re-fork this Set spends an item preventing". A review-side loop has even less reason to fork, because it has no flag surface at all. Cite `resolve_retry_budget(None) == 2` (verified at review) as the source of the number, and record that the repository-policy tier of that precedence is NOT implemented (backlog `dh3us4`), so the workflow must not describe a configurability that does not exist.
  IF A REAL KNOB IS LATER WANTED, that is a CODE change with a declared path and a test, not a sentence in a workflow body; report it rather than slipping it in here.
  THE REPAIR PROMPT MUST CARRY CHILD 01'S MESSAGE VERBATIM rather than paraphrasing it. That message is where R7's content lives: the invariant, the anti-deletion clause, and both remedies. A paraphrase is a second statement of the rule and drifts from it, which is the failure this Set exists to prevent at a different level.
  - Depends on: E-01
  - Expected outcome: a violating orchestrator is repaired and passes on a later attempt within the budget; the budget is configurable; the prompt contains child 01's message unmodified.
  - Execution state: performed

### Task group 2: honest exhaustion, and its record

- [x] E-03 MAKE AN EXHAUSTED LOOP HONEST (R6): the plan stays `to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Not `no-go`, which is a verdict the review did not reach, and not a pass. Do NOT write `- Readiness:` at all in this path; absence is the correct state, it is silent, and it makes the downstream gate fail closed.
  WHY ABSENCE RATHER THAN A VALUE, measured: the auto-approve predicate reads the `- Readiness:` FIELD FIRST and falls back to parsing the workflow history only when it is ABSENT. So any value written here asserts that a review cleared the plan. On 2026-09-06 an agent wrote `go-pending-approval` into four plans having run no review and the predicate returned True for all four; `ipd_lint` now refuses an unattested value as `IPD-M107`.
  - Depends on: E-02
  - Expected outcome: after an unfixable violation, the plan reads `- Status: to-review`, carries NO `- Readiness:` line, and the round record names the finding.
  - Execution state: performed

- [x] E-04 LOG EVERY ATTEMPT INTO THE CURRENT `## Round <n>` OF THE TYPED REVIEW RECORD (OQ-01 resolved at review, PR-206; not the plan's workflow history, which is one line per LIFECYCLE TRANSITION and whose readers treat every row as one). Keep it append-only per round so a later round cannot overwrite an earlier round's attempts. A repair that "succeeded" by deleting the checklist must be visible in the record rather than hidden behind a passing later attempt. Record, per attempt, what the check reported and what changed, INCLUDING THE ROW COUNT BEFORE AND AFTER (PR-204): deletion and relocation both make the check pass, so the log needs a fact that DIFFERS between them or it cannot serve its one purpose. This is the only mechanism that makes the deletion failure mode auditable after the fact, and AGENTS.md records that a prohibition-only message gets complied with by deleting the checklist, so the behaviour must be assumed possible rather than trusted away.
  - Depends on: E-02
  - Expected outcome: a two-attempt repair leaves two attempt records; a repair that removed rows rather than relocating work is readable from them.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `/plan-review` ALREADY OWNS IN-PLACE REVISION (its Step 2.4) and already re-runs `aw ipd lint --phase review-finalize` after every revision, so the loop has an existing home and needs no new checkpoint.
- `plan-review` AND `plan-review-long` ARE HELD IN DELIBERATE PARITY, BUT THE LONG VARIANT IS A DIRECTORY OF STEP FILES, NOT ONE BODY (corrected at review, PR-007). The originally declared path `.aw/system/workflows/plan-review-long/plan-review-long.md` EXISTS but is a step INDEX that no reviewer acts on. `tests/test_plan_review_parity.py::OrchestratorIsNotAStepFileTests` exists precisely to catch an instruction placed there, and its docstring records that this mistake "has been made twice": a directory-level parity check passes while long-form reviewers receive nothing. The reviewer-facing files are `01-discover-and-snapshot.md`, `02-review-and-revise.md` and `03-resolve-and-finalize.md`; this plan's repair loop belongs in `02` (revision) and `03` (finalize/readiness), which is what `- Scope-Paths:` now declares.
- THE PARITY TEST ALREADY EXISTS AND IS THE ONE TO EXTEND: `tests/test_plan_review_parity.py` holds a LOAD-BEARING TOKEN list compared across both variants and reports every divergence at once. Its module docstring states the rule this plan must follow: pin only tokens "something other than a human consumes" (a literal `aw ipd lint` invocation, an `aw check` rule id, a field spelling, a fixed vocabulary), and do NOT pin descriptive wording, which "is rewritten legitimately and often". So add child 01's RULE CODE to that token list; do not add a new parity test file and do not assert the refusal prose verbatim.
- THE ROUND STRUCTURE IS APPEND-ONLY: a re-review appends `## Round <n>` rather than editing an earlier round, because the gate reads only the CURRENT round. An attempt log must respect that.
- `runner_shared.resolve_retry_budget(None)` RETURNS 2 and implements `CLI > repository policy > default`, with the middle tier unimplemented and tracked by backlog `dh3us4`. E-02 follows its shape and inherits its honest gap.
- `- Readiness:` IS A REVIEW OUTPUT AND ABSENCE IS THE CORRECT AUTHORING STATE. `aw ipd scaffold` omits it; `ipd_lint` refuses an unattested value (`IPD-M107`); the auto-approve predicate reads the field before the history. E-03 depends on all three facts.
- READ A PLAN'S KIND FROM ITS OWN FIRST `- Kind:` BULLET, AND THE SHAPE THAT ACTUALLY FAILS IS A CONTAINMENT SCAN (corrected at review, PR-205). Re-measured on `m7gvuz`, which is `- Kind: child` and quotes `Kind: orchestrator` eleven times: `grep -l 'Kind: orchestrator'` MATCHES it (misclassifies), while a first-match regex `Kind:\s*(\S+)` and an anchored `^- Kind:` both correctly return `child`. `ipd_lint.parse` bounds the metadata region, so `doc.meta_fields.get("Kind")` is the safe read and returns `child` for that file. Name the containment shape when writing the instruction.
- THE LONG VARIANT'S `review-finalize` GATE LIVES IN `03`, NOT `02` (verified at review): `grep` finds `aw ipd lint --phase review-finalize` only in `03-resolve-and-finalize.md`, and `- Readiness:` appears only there too (zero occurrences in `02`). That is why E-01 splits the revision half into `02` and the readiness/exhaustion half into `03`, and it confirms the corrected `Scope-Paths` rather than merely asserting it.
- SUITE BARE: `python3 -m pytest`; `addopts` supplies the intended flags. Compare failing NODE IDS, not totals.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `plan-review.md`, its `review-finalize` lint invocation | The review already re-runs a structural gate after revisions, so the repair loop has a natural home; adding a separate checkpoint would create a second place an agent must remember to look. | the workflow body at HEAD `21eff5d8` |
| F-2 | HIGH | the `- Readiness:` auto-approve path | Writing any value on the exhausted path would assert a review verdict that was not reached, and the predicate reads the field BEFORE the history, so the assertion is load-bearing. Measured 2026-09-06 with four plans. | AGENTS.md's recorded incident; `ipd_lint` `IPD-M107` |
| F-3 | HIGH | `plan-review.md`; `.aw/system/workflows/plan-review-long/0*.md`; `tests/test_plan_review_parity.py` | The two variants are held in deliberate parity, so a one-sided change drifts them. **CORRECTED AT REVIEW (PR-007):** the long variant is a DIRECTORY of step files, and the originally declared `plan-review-long.md` is a step INDEX a reviewer never acts on. `tests/test_plan_review_parity.py::OrchestratorIsNotAStepFileTests` exists to catch exactly this and its docstring records that the mistake "has been made twice": a directory-level parity check looks green while long-form reviewers get nothing. `Scope-Paths` now names `02-review-and-revise.md` and `03-resolve-and-finalize.md`. | the parity note; the test class and its docstring; the directory listing |
| F-7 | MEDIUM | `tests/test_plan_review_parity.py` module docstring | **Added at review (PR-007).** A parity test ALREADY EXISTS and defines what may be pinned: LOAD-BEARING tokens only (a literal `aw ipd lint` invocation, an `aw check` rule id, a field spelling, a fixed vocabulary), because descriptive wording "is rewritten legitimately and often" and pinning it produced failures that "told the author nothing". So the correct change is to add child 01's RULE CODE to that token list, NOT to add a second parity test and NOT to assert the refusal prose verbatim. | the module docstring read at review |
| F-8 | MEDIUM | `/plan-review` as a delivery surface | **Added at review (PR-007), RAISED from LOW at review round 2 (PR-201/PR-202).** This child's product is PROSE an agent follows, not code a test can drive: nothing in `agent_workflows/` executes the workflow body. That is not merely a note about assurance ceiling, it is what made three of the four V-items unsatisfiable as authored (a call-site behaviour test, a budget resolution trace, and a code-path grep) and what made the declared new test file unbuildable. The run-side gate in child 03 is what actually enforces the invariant; this child makes the violation REPAIRABLE, which is valuable and is a weaker claim. | grep for a workflow-body executor returns only docstrings and CLI help; the three V-items reworked |
| F-4 | MEDIUM | `runner_shared.resolve_retry_budget` | The budget precedence already exists with default 2 and an unimplemented middle tier; E-02 must follow it and must not claim the policy tier works. | signature and docstring read; backlog `dh3us4` exists |
| F-5 | MEDIUM | this Set's own authoring | A whole-file `Kind` search misclassified a `Kind: child` plan as an orchestrator because it quoted the bullet. E-01 must read the plan's OWN first bullet. | the mis-measurement made and corrected during authoring |
| F-6 | MEDIUM | AGENTS.md's orchestrator guidance | A prohibition-only message gets complied with by DELETING the checklist, which is the outcome R2 forbids. E-04's attempt log is what makes that visible after the fact. | the managed block's text |
| F-9 | HIGH | `ipd_lint.check_readiness_attestation`; `_REVIEW_EVIDENCE_RE` | **Added at review (PR-202).** `IPD-M107` is EVIDENCE-BASED, not status-based: it fires only when `- Readiness:` is present AND the history matches none of `/plan-review`, `APPROVE`, `NO-GO`, `REJECT`. So in this plan's OWN target case - a review that ran and then exhausted its budget - the history already names a review, and `IPD-M107` CANNOT distinguish a correct absence from a fabricated value. The shipped backstop does not cover the case E-03 exists for, so the workflow INSTRUCTION carries the whole weight and must be quoted as evidence. Verified in-process both ways on a minimal fixture. | the checker body and its `not keyed on Status` comment; two lint runs at review |
| F-10 | HIGH | `tests/test_plan_review_parity.py` docstring; `tests/test_spec_review_attestation.py::WorkflowPackageTests` docstring | **Added at review (PR-201).** The declared `tests/test_plan_review_orchestrator_repair.py` had no buildable content: no code executes a workflow body, so the only available assertion is a prose pin, and this repository has DELETED that shape twice with the reason recorded ("fails on every legitimate reword and catches no defect"; "ONE table replaces eleven separate `assertIn` tests"). Declaring the file invites an executor to write exactly that to justify the declaration. Path withdrawn; the existing parity test is the whole test surface. | both module docstrings read at review; `grep` for a workflow-body executor |
| F-11 | MEDIUM | `runner_shared.resolve_retry_budget`; `enforce_orchestrator_probe_gate` docstring | **Added at review (PR-203).** "Configurable, following `resolve_retry_budget`'s CLI-over-policy-over-default precedence" is not implementable in a prose workflow: that resolver takes a CLI value from `--retry-budget`, and a markdown file an agent reads has no flag surface. V-02 as authored demanded a resolution trace no executor could produce. The precedent for the right call is in-tree and explicit: the probe gate reused the existing flag and ACCEPTED 2 over a ruling naming 3, because "a second retry knob is exactly the re-fork this Set spends an item preventing". | `resolve_retry_budget` signature and body; the probe gate's recorded decision; `resolve_retry_budget(None) == 2` verified |
| F-12 | MEDIUM | `V-04`'s original wording | **Added at review (PR-204).** "Record what the check reported and what changed" is satisfiable by a log reading "repaired" twice, which cannot distinguish a deletion from a relocation - the single distinction the log exists to make, since both make the check pass. The log format needs a discriminator; the row count is the cheapest sufficient one. | the item's own stated purpose against its stated evidence |
| F-13 | LOW | `m7gvuz`; the F-5 claim | **Added at review (PR-205).** F-5's hazard is real but mis-attributed. Re-measured: `m7gvuz` is `- Kind: child` and contains `Kind: orchestrator` ELEVEN times, so a CONTAINMENT scan (`grep -l`) misclassifies it - but a first-match regex `Kind:\s*(\S+)` and an anchored `^- Kind:` both correctly return `child`. "Read the first bullet" is the right instruction yet does not name the shape that actually fails, so an executor could satisfy the letter while leaving the hazard undescribed. | three scan shapes run against the real file at review |

## Proposed changes (ordered, validatable)

1. E-01 calls child 01's function for orchestrators only, keyed on the plan's own first `- Kind:` bullet, sited in all three reviewer-facing files (revision half in `02`, readiness half in `03`).
2. E-02 adds the repair loop with a stated default of 2 attempts, no new knob, carrying child 01's message verbatim.
3. E-03 makes exhaustion honest: `to-review`, findings recorded, `- Readiness:` absent.
4. E-04 logs each attempt into the current review round, with row counts, so a deletion-based repair is auditable.

## Deferred / out of scope (with reason)

- THE GRAMMAR, THE FUNCTION, AND THE MESSAGE TEXT: child 01 (`dpdyed`) owns all three. This child calls and renders; it does not decide.
  - Carrier-Declined: Owned by a named sibling in this Set; nothing to hand off.
- THE RUN-SIDE GATE: child 03 (`0xmk4e`). Review and run are separately reviewable consumers on purpose.
  - Carrier-Declined: Owned by a named sibling in this Set.
- MIGRATING ANY EXISTING ORCHESTRATOR: child 04 (`68uhp0`). This child must not fix the corpus as a side effect of testing, which would both hide the migration's cost and edit other agents' plans.
  - Carrier-Declined: Owned by a named sibling in this Set.
- IMPLEMENTING THE REPOSITORY-POLICY TIER of the retry budget: backlog `dh3us4` was executed by `y4adch`. E-02 inherits the gap and states it.
  - Carrier-Evidence: .aw/records/backlog/done/20260904-retrypolicy-01-dh3us4-retry-budget-repository-policy-tier.backlog.md
- ANY CHANGE TO NON-ORCHESTRATOR REVIEW BEHAVIOUR: out of scope, and E-01's `Kind` guard is what keeps it so.
  - Carrier-Declined: An explicit boundary rather than deferred work.

## Scope check

- Over-scope: none, AND THE PREVIOUSLY DECLARED NEW TEST FILE IS WITHDRAWN (PR-201). The single-file body and the long variant's two reviewer-facing STEP files are edited by E-01 through E-04 (parity, F-3), and `tests/test_plan_review_parity.py` gains the new rule code in its existing load-bearing token list. `tests/test_plan_review_orchestrator_repair.py` is NO LONGER DECLARED, because nothing in it could be built that this repository has not already deleted twice as valueless: this child's whole product is PROSE an agent reads, no code executes a workflow body, and the only mechanical property available is "does this token appear in both variants", which is exactly what the parity test already does. Declaring a file whose only possible content is a prose pin invites the executor to write one to justify the declaration.
- THE PROSE-PIN PROHIBITION IS MEASURED IN-TREE AND IS NOT A STYLE OPINION, which is why the file is withdrawn rather than left optional. `tests/test_plan_review_parity.py`'s module docstring records that its needle lists "were cut down to what is LOAD-BEARING", that descriptive wording "is rewritten legitimately and often, and pinning it produced failures that told the author nothing except that they edited prose", and that the old shape "spent one test per phrase, so a single dropped instruction produced a wall of red naming the same root cause". `tests/test_spec_review_attestation.py::WorkflowPackageTests` records the same lesson harder: "ONE table replaces eleven separate `assertIn` tests over the body and README. Those eleven were almost entirely PROSE PINS ... A git repository already records when prose changes, so such a test fails on every legitimate reword and catches no defect." An executor who adds `test_plan_review_orchestrator_repair.py` full of `assertIn` over workflow prose is re-creating what two plans deleted.
- Under-scope: if the loop needs a code-side helper (for example to render the attempt log into the round record) rather than living entirely in the workflow prose, that module must be DECLARED before editing, AND a new test file becomes legitimate at that moment, because a helper is code a test can drive. This plan assumes the loop is workflow-level because `/plan-review` is a prose workflow an agent executes (verified at review: nothing in `agent_workflows/` executes a workflow body; the only references are docstrings and CLI help), so the default expectation is no new test file. An executor who finds otherwise should amend `- Scope-Paths:` and say so rather than reconciling afterwards.

## Required tests / validation

`python3 -m pytest` BARE, in an isolated worktree, baseline measured there, compared by failing NODE ID.

BASELINE MEASURED AT REVIEW on this lane at HEAD `ccab69f1`: `1 failed, 7305 passed, 3 skipped, 2 xfailed`. The single failure is `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, it is PINNED TO THE LIVE MUTABLE PLAN CORPUS, and it is NOT THIS PLAN'S: it names three `reaskscore` plans another party is editing concurrently in this shared checkout. It was PROVEN pre-existing during child 01's review by stashing every edit and re-running the single node, which still failed. Do not touch those plans and do not report it as a regression. Re-measure your own before-baseline and compare failing NODE IDS; the criterion is AFTER minus BEFORE being EMPTY.

Beyond the suite, and note what is and is not mechanically checkable here (F-8): parity is proved by RUNNING `python3 -m pytest tests/test_plan_review_parity.py -o addopts=""` and pasting the output, and that is the ONLY executable assertion this child owns. Parity evidence comparing `plan-review.md` against `plan-review-long.md` FAILS this plan (F-3): the latter is a step index, so such a comparison can be green while long-form reviewers received no instruction at all. Show the instruction present in all three reviewer-facing files.

EVERYTHING ELSE IS A FIXTURE DEMONSTRATION OR A QUOTATION, NOT A TEST, and must be presented as such rather than dressed up as one: a violating orchestrator repaired within budget with before and after checklists; an unfixable case showing `to-review` plus an ABSENT `- Readiness:` plus the `IPD-M107` both-ways demonstration V-03 specifies; and the attempt log for a two-attempt repair beside the log for a deletion-based one. EVERY FIXTURE MUST BE ONE YOU AUTHOR. Repairing a real pending orchestrator is child 04's work and would be editing another agent's plan, which this plan's own gate forbids.

## Spec / documentation sync

The two `plan-review` workflow bodies ARE the documentation for this behaviour and are declared in `- Scope-Paths:`. No `.spec.md` is edited: spec `r07vma` R5/R6/R7 are implemented as written, not amended. Note that editing a shipped workflow changes what every future review does, which is a wide blast radius for a small diff, so the parity check (F-3) is not optional.

## Open questions

### OQ-01: Should the attempt log live in the review round record, or in the plan's own workflow history?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM REPOSITORY EVIDENCE as **the review round record** (PR-206). The authored rationale already proposed this and the reasoning holds, but it was left open when the repository in fact decides it, so the executor should not re-litigate it.
  WHAT SETTLES IT. FIRST, the round record is the DESIGNATED home for review-time detail and is already machine-read: `.aw/records/reviews/README.md` defines `## Round <n>` as append-only with the LAST round current, and defines a `### Decisions` section for exactly this class of content, namely "the judgement calls the reviewer resolved on its own authority". An attempt log is that shape of fact. SECOND, the workflow history is structurally wrong for it: `aw ipd set` writes ONE line per lifecycle transition, and a repair attempt that changed nothing is not a transition, so logging attempts there would put non-lifecycle rows into a log whose readers (`aw attention`, the lifecycle-transition check, `last_history_at`) treat every row as a lifecycle event. THIRD, the self-reporting objection the question raises is real but does not discriminate: the attempt log is authored by the reviewing agent in EITHER location, since nothing tool-written observes a prose repair loop.
  CONSEQUENCE FOR E-04: write the log into the current `## Round <n>` of the typed review record, and keep it append-only per round so a later round cannot overwrite an earlier round's attempts.
- Carrier-Declined: RESOLVED AT REVIEW, so nothing outlives this plan (PR-206, superseding the earlier self-closing note). The location is now decided from repository evidence rather than deferred to execution, E-04 carries the decision, and V-04 requires the log pasted from the round record. There is no future act for a carrier to own.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the added instruction from ALL THREE reviewer-facing files (`plan-review.md`, `02-review-and-revise.md`, `03-resolve-and-finalize.md`) and paste `python3 -m pytest tests/test_plan_review_parity.py -o addopts=""` passing, which is the parity proof. Do NOT paste a diff of `plan-review.md` against `plan-review-long.md`: that file is a step index and such a comparison can be green while long-form reviewers received nothing (F-3).
  THE THREE `Kind` CASES ARE A PROSE-CORRECTNESS CLAIM, NOT A TEST, AND MUST BE SHOWN AS WHAT THEY ARE (PR-202). Nothing executes a workflow body, so "an orchestrator is checked and a child plan is not" cannot be demonstrated by running anything. Satisfy this item by (a) quoting the instruction's exact `Kind` condition as written, and (b) demonstrating the READ it prescribes against the three real fixtures: an orchestrator (`d1u4sy` -> `orchestrator`), an ordinary child (`dpdyed` -> `child`), and `m7gvuz`, which is `- Kind: child` yet contains the string `Kind: orchestrator` ELEVEN times in its prose (re-measured at review). State plainly that this is evidence the RULE AS WRITTEN is unambiguous, not evidence that any code enforces it, because the enforcing consumer is child 03.
  AND NOTE WHAT F-5 ACTUALLY MEASURED, corrected at review: the misclassification comes from a CONTAINMENT scan (`grep -l 'Kind: orchestrator'` matches `m7gvuz`), NOT from any first-match read. A first-match regex `Kind:\s*(\S+)` and an anchored `^- Kind:` both correctly return `child`. So the instruction must forbid the containment shape specifically; saying "read the first bullet" is right but does not name the actual hazard.
  - Observed evidence: ALL THREE INSTRUCTIONS VERIFIED, PARITY SUITE GREEN (5 PASSED), THREE KIND CASES DEMONSTRATED:
    1. Added instruction from `plan-review.md`:
    ```markdown
    #### Orchestrator checklist row check and bounded repair loop (`IPD-S407`)
    Beside `review-finalize`, for any plan whose own first `- Kind:` bullet reads `orchestrator`
    (read from the plan's own first `- Kind:` bullet in front matter; never use a whole-file containment
    scan like `grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as
    `m7gvuz`), the linter validates typed child-tracking row conformance (`IPD-S407`).

    If `IPD-S407` violations are reported:
    1. **Bounded repair loop:** Ask the agent to repair the checklist rows and re-run the check, up to
       an attempt budget of 2 (default 2 per `resolve_retry_budget(None) == 2`; the repository-policy tier
       of that precedence is unimplemented, backlog `dh3us4`).
    2. **Verbatim refusal message:** The repair prompt MUST carry child 01's refusal message verbatim
       (which states the invariant, forbids satisfying it by deletion, and names both remedies: moving the
       step to a child with dependencies, or removing it if redundant).
    3. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record
       (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording
       the attempt number, what the check reported, what changed, and the row count before and after
       (`rows: N -> M`) so repair by deletion is distinguishable from relocation.
    4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with violations unresolved, the
       plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:`
       is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass);
       absence is the correct state, it is silent, and it makes downstream gates fail closed. (The
       auto-approve predicate reads `- Readiness:` first; `IPD-M107` refuses unattested values).
    ```
    2. Added instruction from `02-review-and-revise.md`:
    ```markdown
    ### Orchestrator checklist row repair loop (`IPD-S407`)

    For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the plan's own first
    `- Kind:` bullet in front matter; never use a whole-file containment scan like
    `grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as `m7gvuz`):

    1. **Verify conformance (`IPD-S407`):** Every checklist item must be a typed child-tracking row
       matching `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`.
    2. **Bounded repair loop:** If `IPD-S407` violations are reported, ask the agent to repair the
       checklist rows and re-run the check, up to an attempt budget of 2 (default 2 per
       `resolve_retry_budget(None) == 2`; the repository-policy tier of that precedence is unimplemented,
       backlog `dh3us4`).
    3. **Verbatim refusal message:** The repair prompt MUST carry child 01's refusal message verbatim
       (which states the invariant, forbids satisfying it by deletion, and names both remedies: moving the
       step to a child with dependencies, or removing it if redundant).
    4. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record
       (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording
       what the check reported, what changed, and the row count before and after (`rows: N -> M`) to
       distinguish relocation from deletion.
    ```
    3. Added instruction from `03-resolve-and-finalize.md`:
    ```markdown
    For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the plan's own first
    `- Kind:` bullet in front matter; never use a whole-file containment scan like
    `grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as `m7gvuz`),
    `review-finalize` enforces typed child-tracking row conformance (`IPD-S407`).

    **Honest exhaustion (R6):** If the orchestrator repair loop (budget of 2 attempts) exhausts with
    `IPD-S407` violations unresolved, the plan remains `- Status: to-review`, the findings are recorded
    in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this
    path (not `no-go` and not a pass); absence is legal, silent, and fails closed downstream.
    ```
    4. Parity suite execution:
    `python3 -m pytest tests/test_plan_review_parity.py -o addopts=""`
    Output:
    ```text
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1302969053
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 5 items

    tests/test_plan_review_parity.py .....                                   [100%]

    ============================== 5 passed in 0.10s ===============================
    ```
    5. The three `Kind` cases demonstration:
    Exact `Kind` condition as written: `read from the plan's own first - Kind: bullet in front matter; never use a whole-file containment scan like grep -l 'Kind: orchestrator'`
    Read demonstrated across real fixtures:
    - Orchestrator `d1u4sy` (`.aw/records/plans/pending/20260919-orchtyped-00-d1u4sy-make-an-orchestrator-checklist-a-typed-child-tracking-row-so.ipd.md`): `doc.meta_fields["Kind"] == "orchestrator"`, anchored first bullet reads `orchestrator`, containment count 1.
    - Ordinary child `dpdyed` (`.aw/records/plans/executed/20260919-orchtyped-01-dpdyed-land-the-typed-child-tracking-row-grammar-and-its-one-shared.ipd.md`): `doc.meta_fields["Kind"] == "child"`, anchored first bullet reads `child`, containment count 6.
    - Child quoting orchestrator `m7gvuz` (`.aw/records/plans/pending/20260907-orchprobe-03-m7gvuz-probe-every-queued-orchestrator-for-uncovered-work-before-th.ipd.md`): `doc.meta_fields["Kind"] == "child"`, anchored first bullet reads `child`, containment count 12.
    This demonstrates that the rule as written is unambiguous and forbids whole-file containment scans (which misclassify `m7gvuz`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a violating orchestrator's checklist BEFORE and AFTER a repair that succeeded within the budget, plus child 01's check output on each attempt. USE A FIXTURE YOU AUTHOR, never a real pending orchestrator: repairing one is child 04's work and editing another agent's plan is forbidden by this plan's own gate.
  THE BUDGET EVIDENCE IS A PROSE STATEMENT, NOT A RESOLUTION TRACE, AND THE PLAN'S ORIGINAL WORDING WAS UNSATISFIABLE (PR-203). `runner_shared.resolve_retry_budget` takes a CLI value and is reached from `--retry-budget` on the two runners; a prose workflow has no CLI and no argparse namespace, so there is no "CLI-over-default resolution" for an executor to paste here. Satisfy this item by quoting the budget sentence as written into the workflow, showing it states the default is 2 and names the unimplemented repository-policy tier (`dh3us4`). If you instead add a real knob, that is a CODE change requiring a declared path and a test, and it must be reported rather than slipped in.
  FOLLOW THE IN-TREE PRECEDENT FOR EXACTLY THIS DECISION rather than re-deciding it: `enforce_orchestrator_probe_gate`'s docstring records "THE RETRY BUDGET IS THE EXISTING FLAG, DECIDED AND RECORDED", reuses `--retry-budget`, and accepts its default of 2 over a ruling that named 3, on the stated grounds that "a second retry knob is exactly the re-fork this Set spends an item preventing". A review-side loop with no flag surface is the same trade with even less reason to fork.
  Finally paste proof the repair prompt carries child 01's message VERBATIM, by showing the prompt instructs the reviewer to render the function's message rather than restating it, since a prose prompt cannot be string-diffed against a function's output.
  - Observed evidence: FIXTURE REPAIR LOOP DEMONSTRATED, 2-ATTEMPT BUDGET AND VERBATIM PROMPT CONFIRMED:
    1. Authored fixture checklist BEFORE repair (Attempt 1):
    ```markdown
    ### Task group 1: execution
    - [ ] E-01 Execute step one in child c1aaaa
      - Depends on: none
      - Expected outcome: done
      - Execution state: pending
    - [ ] E-02 CONFIRM c2bbbb REACHED executed
      - Depends on: E-01
      - Expected outcome: done
      - Execution state: pending
    ```
    Attempt 1 check output (`orchestrator_row_conformance`):
    ```text
    Conforming: False
    Finding on row E-01 (line 24): not-a-typed-child-tracking-row
    Refusal message verbatim:
    E-01 is not a typed child-tracking row (not-a-typed-child-tracking-row): the row does not match the typed grammar exactly (it must carry no prose before or after the three fields; free prose belongs on the continuation lines). Write it as `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`. WHY: an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete having never run. DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents. FIX: two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child already covers it (which is removal for redundancy, not deletion to silence this rule). Row as written: '- [ ] E-01 Execute step one in child c1aaaa'
    ```
    2. Authored fixture checklist AFTER repair (Attempt 2):
    ```markdown
    ### Task group 1: execution
    - [ ] E-01 CONFIRM c1aaaa REACHED executed
      - Depends on: none
      - Expected outcome: c1aaaa reads - Status: executed on disk.
      - Execution state: pending
    - [ ] E-02 CONFIRM c2bbbb REACHED executed
      - Depends on: E-01
      - Expected outcome: c2bbbb reads - Status: executed on disk.
      - Execution state: pending
    ```
    Attempt 2 check output (`orchestrator_row_conformance`):
    ```text
    Conforming: True
    Findings count: 0
    ```
    3. Quoting budget sentence as written:
    `an attempt budget of 2 (default 2 per resolve_retry_budget(None) == 2; the repository-policy tier of that precedence is unimplemented, backlog dh3us4)`
    4. Proof repair prompt carries child 01's message verbatim:
    Workflow instruction: `The repair prompt MUST carry child 01's refusal message verbatim (which states the invariant, forbids satisfying it by deletion, and names both remedies: moving the step to a child with dependencies, or removing it if redundant).`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: run a deliberately unfixable case to exhaustion ON A FIXTURE PLAN YOU AUTHOR and paste its front matter afterwards, showing `- Status: to-review` and NO `- Readiness:` line at all (`grep -c '^- Readiness:'` returning 0 is the clearest form). Paste the round record showing the finding recorded.
  THERE IS NO "CODE PATH" TO GREP, so the original final clause was unsatisfiable as written (PR-202). Substitute the checks that ARE available. First paste the exhaustion instruction as written and confirm it contains no sentence directing the reviewer to write `- Readiness:` in this branch. Then demonstrate the shipped backstop on your fixture BOTH WAYS: `aw ipd lint --phase review-finalize` reports nothing about readiness when the field is ABSENT, and reports `IPD-M107` when a value is injected. That is the property R6 needs: absence is legal and silent, a fabricated value is refused.
  BE PRECISE ABOUT WHAT `IPD-M107` KEYS ON, because a careless fixture makes this evidence vacuous and this review made that mistake first. `check_readiness_attestation` is EVIDENCE-BASED, not status-based: it fires only when `- Readiness:` is present AND the plan's `## Workflow history` contains no match for `/plan-review`, `APPROVE`, `NO-GO` or `REJECT`. Its own comment explains why it is not keyed on `Status`: "a review legitimately writes the field in the SAME pass that sets `reviewed`, and `plan-review-long` can leave a plan at `to-review` with a recorded NO-GO readiness". So an exhausted-loop fixture whose history ALREADY names a review will NOT trip `IPD-M107` even with a fabricated value, and pasting that as a pass proves nothing. Verified in-process at review on a minimal fixture: with a history line naming no verdict, injecting `- Readiness: go-pending-approval` yields `IPD-M107`; removing the field clears it.
  NOTE THE RESIDUAL HOLE AND DO NOT OVERCLAIM (see F-9): because the rule keys on history evidence, a review that DID run and then exhausts its repair budget has review evidence in its own history, so `IPD-M107` cannot distinguish a correct absence from a fabricated value in that exact case. The instruction is the only control there, which is why E-03's wording carries the weight and why this item requires the instruction be quoted.
  - Observed evidence: DELIBERATELY UNFIXABLE CASE DEMONSTRATED, HONEST EXHAUSTION CONFIRMED BOTH WAYS:
    1. Exhausted fixture plan front matter:
    ```markdown
    # IPD: Fixture Exhausted Orchestrator

    - Date: 2026-09-24
    - Kind: orchestrator
    - Status: to-review
    - Set: fixture
    - Order: 0
    - Highest E allocated: 01
    - Author: test/author
    - Id: exh001
    ```
    `grep -c '^- Readiness:'` returns 0.
    2. Round record showing finding recorded:
    ```markdown
    ## Round 1
    ### Findings
    | ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
    |---|---|---|---|---|---|---|---|---|
    | PR-001 | HIGH | IN-SCOPE | IPD-S407 | line:24 | E-01 is unfixable custom task not conforming to typed child-tracking grammar | C:Low; U:Low; S:Low; F:High; Overall:High | OPEN | Repair budget (2 attempts) exhausted; plan left at to-review with - Readiness: absent |
    ```
    3. Quoting exhaustion instruction:
    `If the 2-attempt budget is exhausted with violations unresolved, the plan remains - Status: to-review, the findings are recorded in the review round, and - Readiness: is left ABSENT. Do NOT write - Readiness: at all in this path (not no-go and not a pass); absence is the correct state, it is silent, and it makes downstream gates fail closed.`
    4. Demonstration of shipped backstop both ways on fixture:
    - Case A (`- Readiness:` field ABSENT):
      `IPD-M107` diagnostics: `[]` (clean, silent).
    - Case B (`- Readiness: go-pending-approval` INJECTED without review verdict in history):
      `Diagnostic(line=0, col=0, code='IPD-M107', message="Readiness: 'go-pending-approval' is a REVIEW OUTPUT but no review verdict appears in '## Workflow history'. Do not write this field when authoring: the auto-approve gate reads it BEFORE the history, so a hand-written value asserts that a review cleared the plan when none has. Remove the line and let /plan-review write it.")`
    5. Residual hole note: `IPD-M107` keys on history evidence, so when review evidence exists in history, `IPD-M107` cannot distinguish absence from fabricated readiness; the workflow instruction carries the control.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the attempt log for a two-attempt repair ON YOUR OWN FIXTURE. Then paste the log for a repair that satisfied the check by DELETING rows rather than relocating the work, and confirm a reader can tell FROM THE LOG ALONE that rows were removed. If the log cannot distinguish those two cases, this item FAILS, because that distinction is its entire purpose.
  STATE THE ROW COUNT BEFORE AND AFTER IN THE LOG FORMAT ITSELF (strengthened at review, PR-204), because "what the check reported and what changed" as authored can be satisfied by a log that says only "repaired" twice. A deletion and a relocation both make the check pass, so the log must carry something that DIFFERS between them; the cheapest sufficient fact is the row count, since deletion lowers it and relocation does not. If you choose a different discriminator, say why it distinguishes the two cases.
  - Observed evidence: TWO-ATTEMPT AND DELETION-BASED REPAIR ATTEMPT LOGS PASTED WITH DISCRIMINATING ROW COUNTS:
    1. Attempt log for two-attempt repair (relocation / format repair, rows retained):
    ```markdown
    ### Orchestrator checklist repair log
    - **Attempt 1:** Check failed on E-01 (`not-a-typed-child-tracking-row`). Row count: 2. Refusal message returned to author.
    - **Attempt 2:** Author converted E-01 into typed tracking row `CONFIRM c1aaaa REACHED executed`. Row count: 2 -> 2 (retained). Check passed with 0 findings.
    ```
    2. Attempt log for deletion-based repair (rows removed):
    ```markdown
    ### Orchestrator checklist repair log
    - **Attempt 1:** Check failed on E-01 (`not-a-typed-child-tracking-row`). Row count: 2. Refusal message returned to author.
    - **Attempt 2:** Author deleted row E-01 instead of relocating. Row count: 2 -> 1 (row removed). Check passed with 0 findings.
    ```
    3. Reader distinction: From the log alone, `row count: 2 -> 2` vs `row count: 2 -> 1` clearly distinguishes row relocation/retention from row deletion.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 4 E-leaves in 2 groups, all inside the review workflow and its test. The rule itself is child 01's.
- Cohesion rationale: E-01 and E-02 are the call and the loop around it, which cannot be tested apart. E-03 and E-04 are the two halves of what happens when the loop does not succeed, and both exist to stop a violation being laundered into an approved plan; separating them would leave an honest status with no auditable record behind it.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. In particular this plan must NOT repair any existing orchestrator while testing, which would be editing another agent's plan and is child 04's work.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved r3xk1f --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Its `- Item-Dependencies:` refuse dispatch until `dpdyed` is executed. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
