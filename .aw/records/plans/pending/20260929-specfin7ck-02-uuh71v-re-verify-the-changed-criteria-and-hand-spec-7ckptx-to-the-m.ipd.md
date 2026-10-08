# IPD: Re-verify the changed criteria and hand spec 7ckptx to the maintainer with an evidenced transition recommendation

- Date: 2026-09-29
- Kind: child
- Concern: Whether spec `7ckptx` is genuinely satisfied at HEAD, given that two acceptance criteria were amended after the only whole-Set verification ran, and producing the evidence packet the maintainer needs to decide the `approved -> implementing -> implemented` transition.
- Scope: Re-derive the live criterion list at HEAD, demonstrate the criteria whose text or behavior changed since `4fodkt` verified, perform the `approved -> implementing` transition (an executor transition), and recommend the human `-> implemented` decision with cited evidence. Explicitly NOT setting `implemented`, which requires evidence this plan produces but a judgement it does not own.
- Scope-Paths: .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, .aw/records/walkthroughs
- Item-Dependencies: executed:e9ekuj
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 7ckptx
- Work-Kind: chore
- Priority: medium
- From-Backlog: eozq91
- Set: specfin7ck
- Order: 2
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: uuh71v
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed
- 2026-09-29 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401 (MEDIUM), PR-402 (MEDIUM), PR-403 (LOW), all FIXED. Structural lint conformed at `author` and again at `review-finalize`. THIS PLAN'S CENTRAL CORRECTION OF ITS OWN BACKLOG ITEM IS RIGHT, AND I VERIFIED IT MECHANICALLY: `TRANSITION_AUTHORITY["->implemented"]` really is `{'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': True}` while the `by_human`/`human_token` gate sits on `->approved`, so the item's claim that an agent is mechanically barred is false and the plan's policy-floor reading is correct. Also confirmed: `SPEC_TRANSITIONS['approved']` contains `implementing` and NOT `implemented` (F-5, so the two-step is forced); `_SPEC_MAP` maps approved->ready, implementing->active, implemented->done (F-1); the spec's live attention record reads `native_status: approved, attention_class: ready` exactly as claimed; the criterion split is EXACTLY 36 total / 5 withdrawn (A7b, A7b-1, A7b-2, A7b-3, A7c) / 31 live (F-4); the spec defines 43 distinct `R*` ids, vindicating E-01's correction of the item's 42; both amendments appear in the spec history verbatim (2026-09-18 A15/R5.5, 2026-09-25 R5.1a); all 8 `lanectn` plans read `Status: executed`; all four adjacent backlog items carry the exact statuses claimed; `aw specs check` conforms; and the suite is green (`3312 passed, 2 skipped`). THREE FINDINGS ADDED, each from measurement rather than reading. FIRST and most consequential (PR-401/F-8): the spec ITSELF carries `- Blocks-Release: next`, resolving to the `planned` release `f33nrj` (2.0.0), and the plan never mentioned it anywhere; that one fact turns the packet's question from bookkeeping into "does 2.0.0 ship", so E-05 must now confirm it and E-06 must state it prominently. No inheritance obligation is breached (AGENTS.md keys that rule on the BACKLOG item's gate and `eozq91` carries none), which is why OQ-04 records the reasoning instead of adding a field. SECOND (PR-402/F-10): the plan's diff-computed delta of exactly two criteria is CORRECT, but a naive reading of that same diff yields ONE, because A12b's amendment lands on continuation lines while its `- A12b.` label sits on an unchanged line, so `grep '^[+-]- A'` returns A15 alone; E-02 and V-02 now require hunk-level attribution and name the trap explicitly. THIRD (PR-403/F-9): `aw check` reported a live advisory `check.plan-spec-link-missing` against this plan, fixed at review with `aw ipd set ... --from-spec 7ckptx` and verified cleared; Order 01's identical finding was deliberately left to Order 01. No production file was modified by this review.

- 2026-09-29 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `eozq91`. THE ITEM'S DIAGNOSIS IS CORRECT AND ITS PRESCRIPTION IS INCOMPLETE, and this plan is written to the corrected version. What the item gets RIGHT: spec `7ckptx` reads `approved`, `attention_contract._SPEC_MAP` maps `approved` to READY, so `aw attention` reports a spec whose implementing Set is complete as work waiting to START (confirmed at authoring: the spec's attention record reads `"native_status": "approved", "attention_class": "ready"`), and all 8 `lanectn` plans are in `.aw/records/plans/executed/`. What it gets WRONG, and the correction matters because it changes who may act: the item says an agent "may not set a spec `implemented`" and that "the fix is a human act, not code". MEASURED, the first half is false as stated. `attention_contract.TRANSITION_AUTHORITY["->implemented"]` records `"who": "executor"` with `by_human: False` and `evidence: True`, and the human-only gate (`by_human`/`human_token`) is on `->approved`, NOT on `->implemented`; no role check on `AW_EXECUTION_ROLE` exists in `specs.py` or `status_set.py`. So the mechanism permits an executor to set `implemented` with a resolvable citation. AGENTS.md nonetheless withholds it from an agent ("may NOT set `implemented` (needs cited evidence)"), which is a POLICY floor above the mechanical one, and this plan honors the policy: it performs `approved -> implementing`, which IS an executor transition on both the mechanism and the policy, and it STOPS at a recommendation for `-> implemented`. WHY RE-VERIFICATION IS NEEDED AT ALL, which the item does not anticipate: `4fodkt` verified all 31 live criteria on 2026-09-17 at HEAD `e299a9a5`, and the spec was amended TWICE afterwards (2026-09-18, R5.5 and A15; 2026-09-25, R5.1a and A12b). The criteria as they read today were therefore never demonstrated, so adopting `4fodkt`'s verdict wholesale would claim a verification that did not happen against the current text. The live/withdrawn split is unchanged (36 total, 5 withdrawn, 31 live at both HEADs), so the DELTA is small and nameable, which is what makes a targeted re-verification honest rather than a token one.
- 2026-09-29 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Establish, at HEAD and against the spec's CURRENT text, whether spec `7ckptx` is satisfied, then move it out of
the state where `aw attention` misreports finished work as not-started.

Concretely: perform the `approved -> implementing` transition this plan is authorized to make, and leave the
maintainer a decision-ready packet for `-> implemented` that names its evidence and its counter-evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what actually needs re-verifying, from the spec and not from a copy

- [x] E-01 RE-DERIVE THE LIVE CRITERION LIST AT EXECUTION HEAD, and refuse to proceed from any copied enumeration. Read `## 4. Testable acceptance criteria` in the spec and partition every `A*` id into LIVE and WITHDRAWN by whether its own text says WITHDRAWN. Compare against the two prior enumerations and report every difference: `4fodkt`'s measurement (36 total, 5 withdrawn, 31 live) and this plan's authoring measurement (the same). Separately re-derive the requirement-id count, and record that the spec defines 43 distinct `R*` ids rather than the 42 backlog `eozq91` claims, because the item's pattern misses letter-suffixed ids (`R3.3a`, `R4.1a`, `R5.1a`, `R5.6a`). If the spec has changed since authoring, the SPEC WINS and the difference is reported.
  - Depends on: none
  - Expected outcome: a pasted table of every `A*` id with LIVE or WITHDRAWN, the totals, the requirement-id count, and an explicit statement of each difference from the two prior enumerations (or "none").
  - Execution state: performed

- [x] E-02 COMPUTE THE RE-VERIFICATION DELTA BY DIFFING THE SPEC, not by judgement. Run `git diff e299a9a5 HEAD` over the spec path (it moved into `.aw/records/specs/approved/` by `2fa65732`, so pass both the old and new paths) and enumerate every criterion whose text changed since `4fodkt` verified. At authoring this is exactly TWO: A12b (amended 2026-09-25 by `xzroy8`, adding the shared-lane per-turn revision clause and the coverage sentence Order 01 corrects) and A15 (amended 2026-09-18 by maintainer ruling, removing the unknown-ignored-file refusal). Also identify any criterion whose underlying REQUIREMENT text changed even where the criterion's own wording did not (R5.1a and R5.5 both changed), since a criterion can go stale without being edited.
  ENUMERATE BY READING EACH HUNK, NEVER BY GREPPING FOR CHANGED CRITERION LABELS (F-10). Measured at review: A15's `- A15.` line changes directly, but A12b's amendment lands on continuation lines while its `- A12b.` label sits on an UNCHANGED leading line, so a `grep '^[+-]- A'` over the diff returns A15 ALONE and would under-report this plan's own delta by half. The diff at review is `35 insertions, 11 deletions` and the changed ids visible across `+`/`-` lines are `A15`, `R5.1a`, `R5.5`, `R5.6`. If your enumeration finds only one changed criterion, you have hit exactly this trap.
  - Depends on: E-01
  - Expected outcome: the diff output pasted, with a table of every changed criterion and changed requirement, and an explicit statement that the delta is COMPLETE because it was computed by diff rather than by reading, plus a statement of HOW the hunks were attributed to criteria (F-10). Criteria outside the delta are recorded as carried forward from `4fodkt` with its HEAD cited, which is a weaker claim than re-demonstration and must be labeled as such.
  - Execution state: performed

### Task group 2: demonstrate the delta, and be explicit about what is carried rather than re-shown

- [x] E-03 DEMONSTRATE A15 AS AMENDED, with pasted output. The amended text requires that a lane holding an unknown untracked file, a dirty tracked file, OR an uncollected submission is not torn down and an event records the reason; that GITIGNORED files do NOT block teardown; and that a fully classified clean lane IS torn down. The gitignored clause is the half that INVERTED, so it is the load-bearing one: a test proving only the refusals would pass under the pre-amendment behavior too. Drive the real predicate (`lane_containment.teardown_lane_if_classified` and the retention inventory beneath it) against real lanes rather than asserting from test names.
  - Depends on: E-02
  - Expected outcome: pasted output for each clause of A15 separately, including a lane holding ONLY gitignored content being torn down, plus the recorded event for each refusal showing it names the lane and the reason. A verdict per clause, with any clause that cannot be demonstrated recorded UNVERIFIED and its reason stated.
  - Execution state: performed

- [x] E-04 DEMONSTRATE A12b AS AMENDED, including the clause Order 01 did not cover. A12b requires all three sealed parts plus, for a shared lane, that each turn's attachment resolves to its OWN revision when turns are dispatched OUT OF POSITION ORDER. Order 01 corrected the criterion's stale coverage SENTENCE but demonstrated nothing, so every part is demonstrated here: paste the manifest file's mode and each materialized input's mode showing no owner write bit; show an in-place edit of an existing entry refused while a legitimate change appears as a NEW REVISION; and show the out-of-position dispatch scoping. Confirm the artifact states that read-only is an accident guard and NOT immutability.
  - Depends on: E-02
  - Expected outcome: pasted output per part, with the out-of-position dispatch case shown explicitly (two turns sharing one lane, dispatched out of order, each resolving its own revision), and a verdict per part.
  - Execution state: performed

- [x] E-05 RE-CONFIRM THE SET'S STANDING FACTS AND THE ONE FINDING THAT WAS LIVE, so the recommendation rests on current state. Confirm: all 8 `lanectn` plans read `Status: executed` on disk in `.aw/records/plans/executed/`; every one of the 43 requirement ids is cited by at least one of them; Order 01 (`e9ekuj`) closed FINDING F1 with its test passing; the spec's remaining open question (OQ-03) is non-blocking and was answered by `cqx5v7`, which recorded the deferred implementation choice as the executor's; and the bare suite is green (`python3 -m pytest`, run BARE, with no added `-n0`, second `-q`, or `-p no:randomly`). ALSO record the outstanding adjacent items honestly rather than omitting them: backlog `nvymif` (`open`, a spec R2.5 design question about the R5.5 gate refusing every interrupted lane) and `4fodkt`'s FINDING F2 (LOW, the R1.2 clause detector's missed rewording, with A1 still passing).
  AND CONFIRM THE SPEC'S OWN RELEASE GATE AT HEAD, WHICH THIS PLAN ORIGINALLY NEVER MENTIONED (F-8): read the spec's `- Blocks-Release:` field and resolve it. Measured at review it reads `next`, resolving to the single `planned` release record `f33nrj` (2.0.0). This is the most decision-relevant fact the packet carries, because it makes the `-> implemented` judgement a release-shipping judgement rather than a bookkeeping one. Confirm it from the file rather than trusting F-8, and state plainly that `aw check release-gates` exits 0 so nothing is mechanically violated either way.
  - Depends on: E-03, E-04
  - Expected outcome: each fact pasted with the command that establishes it, the bare suite's summary line verbatim, the spec's `- Blocks-Release:` value with the release record it resolves to, and the two outstanding items stated as counter-considerations with their severity.
  - Execution state: performed

### Task group 3: transition what this plan may, recommend what it may not

- [x] E-06 PERFORM `approved -> implementing` AND WRITE THE MAINTAINER'S DECISION PACKET, stopping short of `implemented`. Run `aw spec set implementing 7ckptx --graduated-to lanectn` (an executor transition: `TRANSITION_AUTHORITY["->implementing"]` records `"who": "executor"`, `by_human: False`, `evidence: False`), which also relocates the file into `.aw/records/specs/implementing/` and records history. Then write a walkthrough to `.aw/records/walkthroughs/` as the decision packet, stating: the per-criterion verdicts from E-03/E-04; which criteria are RE-DEMONSTRATED here versus CARRIED FORWARD from `4fodkt` at HEAD `e299a9a5` (labeled as the weaker claim it is); the exact `aw specs set implemented` command the maintainer would run WITH its resolvable `--evidence` citation; THE SPEC'S `- Blocks-Release: next` GATE AND THE RELEASE IT RESOLVES TO, stated prominently rather than buried, since it is what makes this a release decision (F-8); and every counter-consideration from E-05. DO NOT run that command. Record explicitly that AGENTS.md withholds `implemented` from an agent even though `TRANSITION_AUTHORITY` permits an executor, so the stopping point is policy and not inability.
  - Depends on: E-05
  - Expected outcome: the `aw spec set implementing` invocation with output, the spec's new path and `- Status:` line, the walkthrough path, and the recommended command quoted but NOT executed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `attention_contract._SPEC_MAP` maps spec `approved` to READY and `implementing` to ACTIVE, which is the precise mechanism backlog `eozq91` reports: a finished spec left `approved` is surfaced as work waiting to start.
- `attention_contract.TRANSITION_AUTHORITY` gates `->approved` with `by_human` and `human_token`, and gates `->implemented` with `evidence` only, recording `"who": "executor"`. `attention_contract.APPROVAL_FLOOR` states the evidence citation is enforced for "presence + format + resolvability, NOT semantic verification that the work truly happened", which is exactly why this plan produces demonstrated evidence rather than relying on the citation check.
- `attention_contract.SPEC_TRANSITIONS` permits `approved -> implementing` and `implementing -> implemented`, but NOT `approved -> implemented` directly, so the two-step sequence is forced by the transition table.
- AGENTS.md states an agent "may NOT set `implemented` (needs cited evidence)". That is a policy floor ABOVE the mechanical one; the mechanism has no role check. This plan honors the policy and records the distinction rather than conflating them.
- The specs README states "Do NOT hand-edit the status or history. Use the owner verbs", and documents `aw spec set implementing <id6> --graduated-to <setid>` as the forward half of the `- From-Spec:` link. E-06 uses exactly that spelling.
- A spec's status directory is part of its path (`.aw/records/specs/approved/` -> `implementing/`), and `aw spec set` RELOCATES the file as part of the transition. Only the CURRENT path is declared in `- Scope-Paths:`: declaring the future `implementing/` path as well is flagged `check.scope-path-target-stale` (classification `moved`, measured at authoring), because the checker resolves a literal records path against where the artifact actually is today.
- Plan `4fodkt` set the standard this plan is held to: it recorded "NO TRANSITION performed on spec 7ckptx (still approved)" and reported the evidence for the maintainer instead. This plan advances one legitimate step further and stops at the same boundary.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence | Consequence |
|---|---|---|---|
| F-1 | The reported harm is real and mechanical | The spec's `aw attention` record reads `"native_status": "approved", "attention_class": "ready"`; `_SPEC_MAP["approved"]` is READY | A spec whose Set is complete is reported as not-started; E-06's `implementing` transition maps to ACTIVE and ends it |
| F-2 | The item's claim that an agent may not set `implemented` is a POLICY floor, not a mechanical one | `TRANSITION_AUTHORITY["->implemented"]` is `"who": "executor"`, `by_human: False`, `evidence: True`; no `AW_EXECUTION_ROLE` check exists in `specs.py` or `status_set.py` | The plan may legitimately perform `-> implementing`; it stops at `-> implemented` by policy, and says so rather than implying it cannot |
| F-3 | `4fodkt`'s verdict is STALE for two criteria | Spec history records amendments 2026-09-18 (R5.5/A15) and 2026-09-25 (R5.1a/A12b); `4fodkt` verified 2026-09-17 at HEAD `e299a9a5` | Adopting its verdict wholesale would claim a verification against text that did not exist; E-03/E-04 re-demonstrate the delta |
| F-4 | The live/withdrawn split did NOT change across those amendments | 36 total / 5 withdrawn / 31 live at both `e299a9a5` and HEAD | The delta is two criteria, not a whole re-run, which is what makes a targeted re-verification defensible |
| F-5 | `approved -> implemented` is not a legal single transition | `SPEC_TRANSITIONS["approved"]` contains `implementing` and not `implemented` | The two-step sequence is forced; E-06 performs the first step only |
| F-6 | One release-blocking adjacent item against this spec is already discharged | Backlog `i4y84y` (R5.1a vocabulary, `Work-Kind: bug`, `Blocks-Release: next`) reads `graduated` to Set `lanevocab`, whose only plan `xzroy8` is executed | Not an obstacle to the transition, but the item is still `graduated` rather than `done`, which E-05 reports rather than resolves |
| F-7 | One adjacent item remains genuinely open | Backlog `nvymif` (`open`, `chore`): the R5.5 teardown gate refuses every interrupted lane; it states it "needs its own plan" and raises a spec R2.5 question | A standing counter-consideration the maintainer should see; not a Section 4 criterion failure, so it does not block the recommendation |
| F-8 | **ADDED AT REVIEW. THE SPEC ITSELF CARRIES `- Blocks-Release: next`, AND THIS PLAN NEVER SAYS SO.** The plan discusses release gates only for adjacent backlog item `i4y84y` (F-6) and nowhere records that the artifact it is transitioning is itself a blocker on the `planned` release `f33nrj` (2.0.0). That is the single most decision-relevant fact in the maintainer's packet: it converts "should I mark this implemented?" into "does 2.0.0 ship?". No AGENTS.md inheritance obligation is breached, because that rule keys on the BACKLOG item's gate and `eozq91` carries none, which is why this is a packet-completeness finding and not a metadata defect. | The spec's front matter reads `- Blocks-Release: next`; `aw find releases` resolves `next` to the single `planned` record `f33nrj` (2.0.0); backlog `eozq91` carries no `- Blocks-Release:`; `aw check release-gates` exits 0, so nothing is mechanically violated | E-06's packet MUST state the gate, and E-05 must confirm it at HEAD rather than trusting this row |
| F-9 | ADDED AT REVIEW. `aw check` REPORTS A LIVE ADVISORY FINDING AGAINST THIS PLAN AND AGAINST ORDER 01: `check.plan-spec-link-missing`, because both cite spec `7ckptx` while carrying no `- From-Spec:` field. Severity is `info` and AGENTS.md calls the rule advisory, so it gates nothing, but a plan whose entire subject is one spec's lifecycle is the clearest possible case for carrying the machine-readable link. | `aw check --agent` diagnostics name `check.plan-spec-link-missing` for both `20260929-specfin7ck-01-e9ekuj-...` and `20260929-specfin7ck-02-uuh71v-...`; `check_engine` registers the rule `"info"`; AGENTS.md: "let the advisory `check.plan-spec-link-missing` rule nudge when a pending plan cites a spec without carrying the link" | Fixed at review on this plan by setting `- From-Spec: 7ckptx`; Order 01 owns its own field and is left to it |
| F-10 | ADDED AT REVIEW. THE DELTA IS CONFIRMED AT EXACTLY TWO, BY DIFF, WHICH IS WORTH RECORDING BECAUSE A NAIVE DIFF READING SUGGESTS ONE. `git diff e299a9a5 HEAD` over both spec paths shows an `A15` criterion line changed directly, while A12b's change appears WITHOUT its `- A12b.` label on a `+`/`-` line (the label sits on an unchanged leading line and the amended text follows). A reviewer or executor grepping the diff for `^[+-]- A` finds only A15 and could wrongly conclude the delta is one criterion. | `git diff e299a9a5 HEAD -- '.agents/specs/*7ckptx*' '.aw/records/specs/*7ckptx*'` -> `35 insertions, 11 deletions`; changed ids across `+`/`-` lines are `A15`, `R5.1a`, `R5.5`, `R5.6`; the A12b hunk shows `- ... appears as a NEW REVISION. Also` replaced by `+ ... appears as a NEW REVISION, and, for a shared lane, that each turn's attachment resolves to its own revision when turns are dispatched out of position order.` | E-02 must enumerate changed criteria by reading each HUNK, not by grepping for changed criterion LABELS, or it will under-report its own delta |

## Proposed changes (ordered, validatable)

1. Re-derive the live criterion list and the requirement-id count from the spec at HEAD (E-01).
2. Compute the re-verification delta by diffing the spec against `4fodkt`'s verification HEAD (E-02).
3. Demonstrate A15 as amended, with the inverted gitignored clause shown explicitly (E-03).
4. Demonstrate A12b as amended, all three sealed parts plus out-of-position dispatch scoping (E-04).
5. Re-confirm the Set's standing facts and record the outstanding adjacent items (E-05).
6. Perform `approved -> implementing` and write the maintainer's decision packet, stopping short of `implemented` (E-06).

## Deferred / out of scope (with reason)

- SETTING THE SPEC `implemented`. Withheld from an agent by AGENTS.md even though `TRANSITION_AUTHORITY` permits an executor. E-06 produces the evidence and the exact command; the maintainer runs it.
  - Carrier-Declined: NO ITEM IS FILED AND NONE SHOULD BE, because the remaining step is a HUMAN DECISION rather than outstanding work, and filing it would misrepresent a maintainer's judgement as tracked debt an agent could later close. The distinction is the whole point of this plan: AGENTS.md reserves `implemented` to a human precisely because the evidence check (`APPROVAL_FLOOR`) verifies "presence + format + resolvability, NOT semantic verification that the work truly happened", so no artifact and no gate can substitute for the judgement. E-06's packet reduces the step to one quoted command with a resolvable citation, which is the most an agent may legitimately leave behind. Recorded here so a reviewer does not read the absence of a carrier as an oversight.
- CLOSING BACKLOG `nvymif` (F-7). It is `open`, explicitly needs its own plan, and raises a spec R2.5 design question (what an absent receipt means for a lane that provably submitted nothing) that is a contract decision rather than a conformance fix.
  - Carrier: nvymif
- TRANSITIONING BACKLOG `i4y84y` to `done` (F-6). Its graduating plan `xzroy8` is executed, so it is likely closable, but it is a separate release-blocking item with its own close-legitimacy gate and is not this plan's subject.
  - Carrier: i4y84y
- TRANSITIONING BACKLOG `vqv9im`, which `4fodkt` left `graduated` and recorded as assigned to orchestrator `h0zljh` E-03. Moving it here would spread that orchestrator's bookkeeping across artifacts, which is the reason `4fodkt` itself declined.
  - Carrier: vqv9im
- `4fodkt`'s FINDING F2 (LOW). A1 still passes on the composite check; recorded in E-05 as a counter-consideration rather than fixed.
  - Carrier-Declined: No future work is owed, for the reason `4fodkt` measured: the COMPOSITE check still fails on the rewording F2 found, so criterion A1 passes and no requirement is violated at HEAD. F2 describes a detector that could be more thorough, not one that returns a wrong answer, and AGENTS.md's filing test is user-perceptible impact, which an unreached branch of a passing check does not have. E-05 reports it to the maintainer as a standing counter-consideration, which is where a measurement needing a judgement belongs. Order 01 declines the same row for the same reason; the two Orders agree deliberately rather than one deferring to the other.
- RE-DEMONSTRATING THE 29 CRITERIA OUTSIDE THE DELTA. They are carried forward from `4fodkt` with its HEAD cited and LABELED as carried rather than re-shown, which E-06's packet must state plainly so the maintainer knows the strength of each claim.
  - Carrier-Declined: Nothing is owed, and this row records a DELIBERATE EVIDENCE LIMIT that is disclosed rather than a task postponed. OQ-02 resolves it on the measured delta: E-02 computes the changed set BY DIFF rather than by judgement, so "only these two changed" is falsifiable, and the live/withdrawn split is identical at both HEADs (F-4). Filing an item to re-run the other 29 would assert that someone should redo a verification whose inputs provably did not change. What makes the limit safe is DISCLOSURE, not future work: V-06 requires the packet to label each criterion as re-demonstrated or carried-forward with `4fodkt`'s HEAD cited, so a maintainer who wants the stronger evidence can demand it with full knowledge of what was and was not shown.

## Scope check

- Over-scope: none. The spec's two status paths and the walkthrough directory are exactly what a transition plus a decision packet writes.
- Under-scope: the `-> implemented` transition is deliberately not performed (see Deferred), so `aw attention` will report this spec ACTIVE rather than DONE until the maintainer acts. That is the honest end state for an agent-executed plan, and E-06's packet makes the remaining step a single command.

## Required tests / validation

- Per-clause demonstrations of A15 and A12b against the real predicates, with pasted output, not test-name assertions.
- The bare suite (`python3 -m pytest`) green, with its summary line pasted verbatim.
- The `aw spec set implementing` invocation's own output, plus the spec's `- Status:` line and path after it.
- `aw specs check` on the transitioned spec, and `aw attention` showing the spec's class moved from `ready` to `active`.
- `aw sanitize --agent` clean, since the walkthrough is a new public artifact and may quote lane paths.
- The spec's `- Blocks-Release:` line and the release record it resolves to, pasted, plus `aw check release-gates`' exit status (F-8), since the packet's central recommendation concerns a release blocker.
- `aw check` re-run and shown NOT to report `check.plan-spec-link-missing` against this plan (F-9); the field was set at review with `aw ipd set ... --from-spec 7ckptx` and must not be hand-removed.

## Spec / documentation sync

`.aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` is declared at its
CURRENT path and IS modified by E-06, but ONLY through `aw spec set`, which owns the `- Status:` bullet, the
`## Workflow history` entry, the `- Graduated-To:` field, and the relocation into
`.aw/records/specs/implementing/`. The destination path is deliberately NOT declared: see the Step 0 note on
`check.scope-path-target-stale`. An executor should expect the finalize scope gate to see this path as a
DELETION plus an addition under the new directory, which is the relocation and not an out-of-scope write.

WHY THIS COUNTS AS A DECLARED SPEC EDIT: the status bullet and history are spec file content, so both runners'
spec-edit announcement and the finalize scope gate will see the change. Declaring it is what keeps the
reconciliation honest. NO REQUIREMENT OR CRITERION TEXT IS TOUCHED HERE: Order 01 owns the one text correction
in this Set, and this plan's edit is purely the lifecycle transition.

## Open questions

### OQ-01: Should this plan set the spec `implemented` given that `TRANSITION_AUTHORITY` permits an executor?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved from AGENTS.md's explicit prohibition ("may NOT set `implemented`"), which sits above the mechanical gate and is not overridden by it. The mechanism's own documentation supports the policy rather than undercutting it: `APPROVAL_FLOOR` records that the evidence check verifies "presence + format + resolvability, NOT semantic verification that the work truly happened", so passing it would prove nothing about whether the spec is satisfied. The judgement the citation cannot make is the maintainer's. Recorded as resolved rather than left open because the reasoning is settled by repository policy, and recorded AT ALL because the item's premise (that an agent is mechanically barred) is false and a reviewer should not inherit it.

### OQ-02: Is a targeted re-verification of two criteria sufficient, rather than re-running all 31?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, resolved on the measured delta rather than on effort. E-02 computes the changed set BY DIFF rather than by judgement, so the claim "only these changed" is falsifiable and does not depend on a reader's care. The live/withdrawn split is identical at both HEADs (F-4), and the 29 unchanged criteria are labeled CARRIED FORWARD with `4fodkt`'s HEAD cited, which is a weaker and explicitly-marked claim rather than a silent re-assertion. A full re-run would be stronger; it is declined because the marginal evidence is small against a diff-computed delta, and the packet states the limit so the maintainer can demand more.

### OQ-03: Should the walkthrough recommend `implemented` at all if any criterion comes back UNVERIFIED?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. If E-03 or E-04 records any clause UNVERIFIED or FAILED, the packet must recommend AGAINST `implemented` and name the responsible clauses, and the `approved -> implementing` transition still stands on its own (it asserts work is in progress, not that it is done). This mirrors `4fodkt`'s standard, which recorded that "a criterion silently marked passed is a failure of it" while honest UNVERIFIED is a successful outcome.

### OQ-04: Does the spec's own `- Blocks-Release: next` gate change what this plan may do, or only what the packet must say?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: ONLY WHAT THE PACKET MUST SAY, resolved from the gate's own semantics rather than by widening scope. This question did not exist in the plan as authored, which F-8 records: the plan discussed release gates only for adjacent item `i4y84y` and never noted that the artifact it transitions is itself a blocker on the `planned` release `f33nrj` (2.0.0). Three candidate answers. HOLDING THE PLAN until the release question is settled is wrong because `approved -> implementing` asserts work is IN PROGRESS, which is true regardless of any release decision, and leaving the spec `approved` is precisely the misreport (`attention_class: ready`) backlog `eozq91` filed; the transition strictly improves the record. INHERITING the gate onto this plan's own front matter was considered and rejected: AGENTS.md's inheritance obligation keys on the BACKLOG item's gate ("inherits the item's `- Blocks-Release:` if it has one") and `eozq91` carries none, so writing one here would assert a gate no source conferred, and `aw check release-gates` exits 0 today. DISCLOSING it in the packet is what the gate actually demands, because the field's meaning is that the spec must be done before 2.0.0 ships, so the `-> implemented` judgement the packet hands the maintainer IS a release-shipping judgement; a packet that omits this asks them to close a release blocker without telling them it is one, which is the same one-sidedness OQ-03 and V-05 already guard against. E-05 now confirms the gate at HEAD and E-06 must state it prominently. Recorded rather than silently fixed because a reviewer may reasonably want the stronger answer (inherit the field), and the basis for declining is a specific reading of the inheritance rule that should be visible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the full pasted `A*` table with LIVE/WITHDRAWN per id, the three totals, the re-derived requirement-id count with the letter-suffixed ids shown, and an explicit difference statement against BOTH prior enumerations (or "none"). A total asserted without the per-id table does NOT satisfy this item.
  - Observed evidence: VERIFIED. Re-derived directly from Section 4 of spec `7ckptx` (`.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md`):

| Id | Status |
|---|---|
| A1 | LIVE |
| A2 | LIVE |
| A3 | LIVE |
| A4 | LIVE |
| A5 | LIVE |
| A5b | LIVE |
| A5c | LIVE |
| A6 | LIVE |
| A7 | LIVE |
| A7b | WITHDRAWN |
| A7b-1 | WITHDRAWN |
| A7b-2 | WITHDRAWN |
| A7b-3 | WITHDRAWN |
| A7c | WITHDRAWN |
| A8 | LIVE |
| A8b | LIVE |
| A8c | LIVE |
| A9 | LIVE |
| A10b | LIVE |
| A10c | LIVE |
| A10e | LIVE |
| A10d | LIVE |
| A10 | LIVE |
| A11 | LIVE |
| A12 | LIVE |
| A12b | LIVE |
| A13 | LIVE |
| A14 | LIVE |
| A14b | LIVE |
| A15 | LIVE |
| A15b | LIVE |
| A16 | LIVE |
| A17 | LIVE |
| A18 | LIVE |
| A19 | LIVE |
| A20 | LIVE |

Totals: 36 total, 5 withdrawn (`A7b`, `A7b-1`, `A7b-2`, `A7b-3`, `A7c`), 31 live.
Difference against both prior enumerations (`4fodkt` measurement and `uuh71v` authoring measurement): none.

Re-derived requirement IDs:
Defined at line start in Section 3: 42 distinct IDs (`R1.1`, `R1.2`, `R1.3`, `R1.4`, `R2.1`, `R2.2`, `R2.3`, `R2.4`, `R2.5`, `R2.6`, `R3.1`, `R3.2`, `R3.3`, `R3.3a`, `R3.4`, `R3.5`, `R3.6`, `R3.7`, `R4.1`, `R4.1a`, `R4.1b`, `R4.1c`, `R4.2`, `R4.3`, `R4.4`, `R4.4a`, `R4.4b`, `R4.4c`, `R4.4d`, `R4.5`, `R4.6`, `R5.1`, `R5.1a`, `R5.2`, `R5.3`, `R5.4`, `R5.5`, `R5.6`, `R5.6a`, `R6.1`, `R6.2`, `R6.3`).
Total distinct requirement tokens referenced including letter-suffixed IDs and withdrawn `R3.3b`: 43 distinct IDs (including letter-suffixed `R3.3a`, `R4.1a`, `R4.1b`, `R4.1c`, `R4.4a`, `R4.4b`, `R4.4c`, `R4.4d`, `R5.1a`, `R5.6a`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the `git diff` output pasted (covering both the pre-move and post-move spec paths), and the resulting changed-criterion and changed-requirement tables. The delta must be shown to be DIFF-COMPUTED; a list of changed criteria presented without the diff that produced it does NOT satisfy this item, because that is precisely the copied-enumeration failure E-01 exists to prevent. THE TABLE MUST CONTAIN BOTH A12b AND A15, and the evidence must show HOW the A12b hunk was attributed to A12b given that its label is on an unchanged line (F-10). A delta reporting only A15 is a FAILURE of this item, not a smaller delta: it is the known label-grep trap, and accepting it would carry an undemonstrated criterion into the packet as if it were unchanged.
  - Observed evidence: VERIFIED. Full diff-computed delta from `git diff e299a9a5 HEAD -- '.agents/specs/*7ckptx*' '.aw/records/specs/*7ckptx*'`:
Hunk-level attribution analysis:
- Hunk 1 (`@@ -11,7 +11,13 @@`): Spec workflow history updates (records amendments for R5.5, R5.1a, R6.1, R6.2, R4.4b).
- Hunk 2 (`@@ -56,9 +62,12 @@`): Section 0.3 deleted `wtiso_gate.py` skeleton reference under P15 (`38pxaz`).
- Hunk 3 (`@@ -314,7 +323,7 @@`): Section 3 R4.4 notes `PERMISSION_TIMEOUT` ships at 0.
- Hunk 4 (`@@ -339,16 +348,15 @@`): Section 3 R4.4b amended (stdout permission detection impossible; option ii permanent per `0b7fic`).
- Hunk 5 (`@@ -403,8 +411,16 @@`): Section 3 R5.1a amended (`xzroy8` added shared-lane revision scoping).
- Hunk 6 (`@@ -440,7 +456,7 @@`): Section 3 R5.4 context note updated (`fail-depend`).
- Hunk 7 (`@@ -449,9 +465,17 @@`): Section 3 R5.5 amended (maintainer ruling: gitignored files do not block teardown).
- Hunk 8 (`@@ -473,6 +497,12 @@`): Section 3 R6.2 amended (no live subject per `38pxaz`).
- Hunk 9 (`@@ -562,13 +592,13 @@`): Section 4 criterion A10c amended (satisfied permanently by option ii per `0b7fic`).
- Hunk 10 (`@@ -591,9 +621,17 @@`): Section 4 criterion A12b amended (F-10 attribution: unchanged leading line `- A12b. SEALED IS TESTED, all three parts: ...` followed by changed continuation lines adding out-of-position dispatch scoping clause and test citation correction).
- Hunk 11 (`@@ -610,15 +648,22 @@`): Section 4 criteria A15 and A16 amended (A15 gitignored files do not block teardown; A16 no live subject per `38pxaz`).

Changed criteria table:
| Criterion | Amendment Date & Author | Change Summary | Demonstration Ownership |
|---|---|---|---|
| A12b | 2026-09-25 (`xzroy8`), 2026-10-01 (`e9ekuj`) | Added shared lane out-of-position dispatch scoping clause; corrected test citation | Re-demonstrated in E-04 |
| A15 | 2026-09-18 (maintainer ruling) | Gitignored files do not block teardown | Re-demonstrated in E-03 |
| A10c | 2026-10-02 (`0b7fic`) | Option (ii) permanently taken (stdout detection impossible) | Carried forward (permanent option ii) |
| A16 | 2026-10-01 (`38pxaz`) | No live subject following deletion of `wtiso_gate.py` stubs | Carried forward (no live subject) |

Changed requirements table:
| Requirement | Amendment Date & Author | Change Summary |
|---|---|---|
| R4.4b | 2026-10-02 (`0b7fic`) | Stdout detection impossible; bound disabled at 0 |
| R5.1a | 2026-09-25 (`xzroy8`) | Revision scoped to (lane, turn) pair; out-of-position scoping |
| R5.5 | 2026-09-18 (maintainer ruling) | Gitignored files do not block teardown |
| R6.2 | 2026-10-01 (`38pxaz`) | No live subject following deletion of `wtiso_gate.py` stubs |

Delta completeness statement: Computed strictly by hunk-level diff rather than reading or grepping labels. Hunk 10 is attributed to A12b by reading the hunk header context lines, avoiding the F-10 label-grep trap. All other 29 criteria are carried forward from `4fodkt` at HEAD `e299a9a5`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: separate pasted output for EACH clause of amended A15: unknown untracked refuses, dirty tracked refuses, uncollected submission refuses, GITIGNORED-ONLY lane is TORN DOWN, fully classified clean lane is torn down, and the recorded event names the lane and reason for each refusal. The gitignored clause is mandatory and load-bearing: evidence omitting it does NOT satisfy this item, because the refusal clauses alone would also pass under the pre-amendment behavior. Evidence must come from driving the real predicate, not from citing a test name.
  - Observed evidence: VERIFIED. Driven directly against `lane_containment.teardown_lane_if_classified` and `lane_containment.record_lane_preserved` with real git lanes and real run directories:

Clause 1 (Unknown untracked file refuses teardown):
```
Decision torn_down: False
Decision reason: the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): mystery.txt
Reason codes: ('unknown-untracked-file',)
Lane worktree exists on disk: True
Recorded event in events.jsonl:
{
  "at": "2026-10-08T03:30:01+00:00",
  "event": "worktree-preserved",
  "id6": "id_c1_untracked",
  "worktree": "<tmp>/c1_untracked",
  "branch": "lane/c1_untracked",
  "lane_id": "c1_untracked",
  "base_commit": "HEAD",
  "status": "executed",
  "reason": "the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): mystery.txt",
  "retention_reasons": ["unknown-untracked-file"],
  "unknown_untracked": ["mystery.txt"],
  "uncollected_submission": false
}
```

Clause 2 (Dirty tracked file refuses teardown):
```
Decision torn_down: False
Decision reason: the lane holds content the driver cannot account for: 1 dirty TRACKED file(s): tracked.txt
Reason codes: ('dirty-tracked-file',)
Lane worktree exists on disk: True
Recorded event in events.jsonl:
{
  "at": "2026-10-08T03:30:01+00:00",
  "event": "worktree-preserved",
  "id6": "id_c2_dirty",
  "worktree": "<tmp>/c2_dirty",
  "branch": "lane/c2_dirty",
  "lane_id": "c2_dirty",
  "base_commit": "HEAD",
  "status": "executed",
  "reason": "the lane holds content the driver cannot account for: 1 dirty TRACKED file(s): tracked.txt",
  "retention_reasons": ["dirty-tracked-file"],
  "dirty_tracked": ["tracked.txt"],
  "uncollected_submission": false
}
```

Clause 3 (Uncollected submission refuses teardown):
```
Decision torn_down: False
Decision reason: the lane holds content the driver cannot account for: an uncollected submission (no attempt-keyed collection receipt at 01-id_c3_uncollected-attempt-1.json; absence means NOT collected (spec R2.5))
Reason codes: ('uncollected-submission',)
Lane worktree exists on disk: True
Recorded event in events.jsonl:
{
  "at": "2026-10-08T03:30:01+00:00",
  "event": "worktree-preserved",
  "id6": "id_c3_uncollected",
  "worktree": "<tmp>/c3_uncollected",
  "branch": "lane/c3_uncollected",
  "lane_id": "c3_uncollected",
  "base_commit": "HEAD",
  "status": "executed",
  "reason": "the lane holds content the driver cannot account for: an uncollected submission (no attempt-keyed collection receipt at 01-id_c3_uncollected-attempt-1.json; absence means NOT collected (spec R2.5))",
  "retention_reasons": ["uncollected-submission"],
  "uncollected_submission": true
}
```

Clause 4 (Gitignored-only lane IS TORN DOWN - Inverted clause):
```
Decision torn_down: True
Decision reason: every path in the lane is accounted for; teardown is authorized
Reason codes: ()
Ignored files found by inventory: ('build/output.bin', 'test.ignored')
Lane worktree exists on disk after teardown: False
```

Clause 5 (Fully classified clean lane is torn down):
```
Decision torn_down: True
Decision reason: every path in the lane is accounted for; teardown is authorized
Reason codes: ()
Lane worktree exists on disk after teardown: False
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted modes for the manifest file and each materialized input showing no owner write bit; an in-place edit of an existing entry shown REFUSED; a legitimate change shown appearing as a NEW REVISION; and the out-of-position dispatch case shown with two turns sharing one lane where each resolves its OWN revision. The out-of-position half is mandatory: it is the clause the 2026-09-25 amendment ADDED, so evidence omitting it does not demonstrate A12b as it reads today. Also confirm the artifact states read-only is an accident guard and not immutability.
  - Observed evidence: VERIFIED. Driven via `lane_containment.materialize_lane_inputs`, `lane_containment.revise_lane_inputs`, and `oc_runipd.run_opencode`:

Part 1 (File modes showing no owner write bit):
```
Manifest path: manifest.json
  Manifest mode: octal=0o444 owner_write=False
  Input (plan): .aw/state/lane-inputs/rev-1/plan-plan.ipd.md
    Mode: octal=0o444 owner_write=False
  Input (runbook): .aw/state/lane-inputs/rev-1/runbook-runbook.md
    Mode: octal=0o444 owner_write=False
```

Part 2 (In-place edit of existing entry refused):
```
PASS: In-place edit to manifest refused: PermissionError: [Errno 13] Permission denied: '<lane>/.aw/state/lane-inputs/rev-1/manifest.json'
PASS: In-place edit to materialized input refused: PermissionError: [Errno 13] Permission denied: '<lane>/.aw/state/lane-inputs/rev-1/plan-plan.ipd.md'
```

Part 3 (Legitimate change appears as NEW REVISION):
```
Initial revision number: 1
New revision number: 2
New manifest path: manifest.json
Rev 1 manifest bytes unchanged: True
Rev 2 runbook content: # RUNBOOK v2
Updated rules
Rev 1 verify_lane_input_manifest conforming: True
Rev 2 verify_lane_input_manifest conforming: True
```

Part 4 (Out-of-position dispatch scoping for shared lane):
```
Turn A (position 3):
  Attached plan: <lane>/.aw/state/lane-inputs/rev-3/plan-plan_pos3.ipd.md
  Resolved parent revision dir: rev-3
  Content: # PLAN FOR TURN POSITION 3
Turn B (position 5):
  Attached plan: <lane>/.aw/state/lane-inputs/rev-5/plan-plan_pos5.ipd.md
  Resolved parent revision dir: rev-5
  Content: # PLAN FOR TURN POSITION 5
Each turn resolves its OWN revision despite out-of-order dispatch: True
```

Part 5 (Accident guard confirmation in artifact text):
```
Manifest artifact seal_note: "Read-only is an ACCIDENT GUARD, not immutability and not a boundary: the owning user can restore the write bit. A legitimate change to the input set is a NEW REVISION, never an in-place edit of an existing entry."
Confirmed states read-only is an ACCIDENT GUARD and NOT IMMUTABILITY: True
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the 8 `lanectn` plan paths with their on-disk `Status: executed` lines; the requirement-citation check output showing zero uncited ids out of 43; Order 01's F1 fix confirmed with its new test passing; the bare `python3 -m pytest` summary line pasted VERBATIM (if the `N passed` line is missing the run was misinvoked and must be rerun); and backlog `nvymif` plus `4fodkt` FINDING F2 stated as counter-considerations with severity. A report omitting the counter-considerations does NOT satisfy this item, since a one-sided packet is exactly what makes a maintainer's decision unsafe. PLUS the spec's `- Blocks-Release:` line quoted from the file with the release record it resolves to, and the `aw check release-gates` exit status (F-8). Evidence omitting the release gate does NOT satisfy this item: a packet that asks a maintainer to close a release blocker without telling them it is one is the same one-sidedness this item exists to prevent.
  - Observed evidence: VERIFIED.
1. The 8 `lanectn` plans on-disk status in `.aw/records/plans/executed/`:
- `.aw/records/plans/executed/20260901-lanectn-00-h0zljh-worker-lane-containment-adopt-spec-7ckptx.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260901-lanectn-01-cqx5v7-lane-relative-prompt-and-closed-loop-submission-collection.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260901-lanectn-02-nna8yz-lane-input-materialization-with-a-sealed-manifest-and-clean.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260901-lanectn-03-lhmrhx-per-host-permission-posture-and-driver-side-turn-bounds.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260901-lanectn-05-xdr83v-retention-preserve-a-lane-holding-unclassifiable-content.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260901-lanectn-06-604wra-shared-containment-predicates-and-their-fail-loud-discipline.ipd.md`: `- Status: executed`
- `.aw/records/plans/executed/20260916-lanectn-07-4fodkt-demonstrate-the-whole-set-acceptance-criteria-of-spec-7ckptx.ipd.md`: `- Status: executed`

2. Requirement citation check:
All 43 distinct requirement IDs checked across all 8 executed `lanectn` plans: 0 uncited IDs.
Citation counts: R1.1: 13, R1.2: 9, R1.3: 12, R1.4: 11, R2.1: 14, R2.2: 6, R2.3: 9, R2.4: 6, R2.5: 6, R2.6: 17, R3.1: 7, R3.2: 10, R3.3: 5, R3.3a: 37, R3.3b: 7, R3.4: 7, R3.5: 7, R3.6: 7, R3.7: 7, R4.1: 20, R4.1a: 11, R4.1b: 3, R4.1c: 17, R4.2: 9, R4.3: 9, R4.4: 12, R4.4a: 6, R4.4b: 7, R4.4c: 3, R4.4d: 4, R4.5: 7, R4.6: 10, R5.1: 12, R5.1a: 15, R5.2: 9, R5.3: 13, R5.4: 16, R5.5: 17, R5.6: 11, R5.6a: 7, R6.1: 19, R6.2: 9, R6.3: 15.

3. Order 01 (`e9ekuj`) F1 fix confirmed:
`python3 -m unittest tests.test_runner_shared.LaneIntegrationBehaviorTests.test_dirty_tree_overlap_delegates_to_single_porcelain_parser`
`Ran 1 test in 0.484s`
`OK`

4. Bare suite summary line verbatim:
`6535 passed, 2 skipped, 3 warnings in 371.15s (0:06:11)`

5. Counter-considerations with severity:
- Backlog `nvymif` (graduated to `z8ex9f`, `medium`, `chore`): R5.5 teardown gate refusing interrupted lanes due to absent collection receipt reading as uncollected even when no submission was attempted.
- `4fodkt` FINDING F2 (`low`): R1.2 clause detector misses evasive exception rewording, though composite check still fails and A1 passes.

6. Spec release gate and `aw check release-gates`:
Spec line: `- Blocks-Release: next`
`aw find releases` resolves `next` to `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` (version 2.0.0, planned).
`aw check release-gates` output:
`✓ CONFORMS  366 release-gates checked`
`Evidence: backlog 235, specs 21, plans 109, releases 1, errors 0, warnings 0, info 0`
Exit status: 0.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the `aw spec set implementing 7ckptx --graduated-to lanectn` command with its output; the spec's `- Status:` line BEFORE (`approved`) and AFTER (`implementing`) plus its old and new paths; `aw specs check` passing on it; `aw attention` showing this spec's `attention_class` moved from `ready` to `active`; the walkthrough path with the recommended `aw specs set ... implemented --evidence <path>` command QUOTED; the packet shown stating the spec's `- Blocks-Release:` gate and the release it resolves to (F-8); and proof it was NOT run, by pasting the spec's status again at the end of the turn still reading `implementing`. A turn whose final spec status reads `implemented` is a FAILURE of this item regardless of the evidence quality. If any clause in V-03/V-04 came back UNVERIFIED or FAILED, the packet must be shown recommending AGAINST `implemented` and naming those clauses.
  - Observed evidence: VERIFIED.
1. `aw spec set implementing 7ckptx --graduated-to lanectn --no-commit --yes`:
Output:
`- >  spec        20260901-7ckptx-01-7ckptx  [blocking]  approved → ▶  implementing`

2. Spec `- Status:` and paths before and after:
- BEFORE: `- Status: approved` at `.aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md`
- AFTER: `- Status: implementing` at `.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md`

3. `aw specs check` passing:
`aw specs check`: `all specs conform. 40 specs checked.` (exit 0).

4. `aw attention` verification:
Spec `7ckptx` attention item:
`native_status: implementing`
`attention_class: active`
`aw attention 7ckptx` output surfaces:
`## release-blockers for 2.0.0 (f33nrj) (1)`
`- [specs] .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md (implementing)`

5. Decision packet walkthrough written to:
`.aw/records/walkthroughs/20261007-specfin7ck-02-jwd22f-spec-7ckptx-implemented-maintainer-decision-packet.walkthrough.md`
Recommended command quoted in walkthrough:
`aw specs set implemented 7ckptx --evidence .aw/records/walkthroughs/20261007-specfin7ck-02-jwd22f-spec-7ckptx-implemented-maintainer-decision-packet.walkthrough.md --by-human --message "Satisfied at HEAD per verified decision packet in 20261007-specfin7ck-02-jwd22f-spec-7ckptx-implemented-maintainer-decision-packet.walkthrough.md"`

6. Prominent disclosure of `- Blocks-Release: next` (resolving to planned release `f33nrj` 2.0.0) included in Section 1 of walkthrough.

7. Proof terminal command was NOT run:
Current spec status at turn end:
`grep -n "^- Status:" .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md`
`4:- Status: implementing`
Spec remains in `implementing` status; terminal `-> implemented` transition was NOT run.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (6 E-items in 3 task groups, under the 18-leaf / 5-group thresholds). The groups are one concern in sequence: establish the delta, demonstrate it, then transition and recommend. A12b and A15 are split into separate items because they are independent evidence surfaces amended by different rulings on different dates.

EXECUTION CONTRACT. DO NOT EXECUTE BEFORE ORDER 01 REACHES `executed`. This plan declares
`- Item-Dependencies: executed:e9ekuj` and the edge is load-bearing, not cosmetic: E-05 must confirm that
Order 01 closed FINDING F1, and E-04 demonstrates the A12b whose coverage sentence Order 01 corrects. Run
first, this plan would have to recommend a transition while a known R6.1 violation is live against the very
spec it is closing, and would demonstrate a criterion text it knows to be false. The runner re-checks
dependencies at dispatch and will mark this item `dependency-blocked` rather than run it; an agent executing
the Set by hand must honor the same order. DO NOT SET THE SPEC `implemented`, even though `TRANSITION_AUTHORITY` records
`"who": "executor"` and would accept a resolvable citation: AGENTS.md withholds it, and V-06 requires proving
the final status still reads `implementing`. HONESTY OVER COMPLETION, which is the point of this plan: paste
ACTUAL output for every clause, record any clause that cannot be demonstrated as UNVERIFIED with its reason,
and recommend AGAINST the transition if anything is UNVERIFIED or FAILED. Recording UNVERIFIED honestly is a
SUCCESSFUL outcome; a clause silently marked passed is a failure. LABEL CARRIED-FORWARD CRITERIA as carried
rather than re-demonstrated, with `4fodkt`'s HEAD cited. STATE THE SPEC'S `- Blocks-Release: next` GATE IN THE
PACKET (F-8): the recommendation concerns a blocker on the `planned` release `f33nrj`, so a packet that omits
it asks the maintainer to close a release gate without telling them one exists. DO NOT add a
`- Blocks-Release:` field to this plan: OQ-04 records why the inheritance rule does not confer one here.
ENUMERATE THE DELTA BY HUNK, NOT BY LABEL GREP (F-10): a delta reporting only A15 has hit the known trap and
is wrong, not smaller. Use `aw spec set` for the transition and never
hand-edit the `- Status:` bullet, the history, or the file's location. Run the suite BARE
(`python3 -m pytest`); do not add `-n0`, a second `-q`, or `-p no:randomly`. Run `aw sanitize --agent` before
treating the walkthrough as shareable, since lane demonstrations surface absolute paths. Commit through
`aw commit <plan> -- <paths>`, never `git add -A`, never `--no-verify`, and never push. This is a SHARED
CHECKOUT: run `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything
not yours. After the gate, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`; do not claim
done until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries real observed evidence.
