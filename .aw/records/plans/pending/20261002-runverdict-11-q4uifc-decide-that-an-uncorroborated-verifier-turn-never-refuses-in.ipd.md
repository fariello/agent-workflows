# IPD: Decide that an uncorroborated verifier turn never refuses integration, apply P15 to the corroboration record, and clarify spec 25kzda 5.1 so the question is not re-litigated

- Date: 2026-10-02
- Kind: child
- Concern: BACKLOG `sinhkj` ASKS WHETHER AN `uncorroborated` VERIFIER TURN SHOULD EVER BLOCK INTEGRATION, AND THE QUESTION IS CURRENTLY ANSWERED NOWHERE WHILE A FIELD EXISTS FOR SOMEONE TO ANSWER IT WITH. The record shipped: `verifier_corroboration.corroborate_verifier_turn` returns a three-state verdict (`corroborated` / `uncorroborated` / `indeterminate`), `runner_shared.execute_item_core` writes `corroboration_verdict` / `corroboration_reason` / `corroboration_counts` onto the attempt AND the item, `runner_shared.format_verifier_evidence_section` renders a `Corroboration:` line into `execution-report.md`, and `run_viewer`'s `StepSummary` surfaces it in `aw runs`. Nothing refuses on it, which was `btak7a`'s deliberate limit, recorded as its own OQ-01 with `- Owner: maintainer` and `- Carrier: sinhkj`. SO THE DECISION IS THE ONLY THING OUTSTANDING, and leaving it open is not neutral: a published three-state verdict beside a verification disposition is an invitation, and the next author who reads `uncorroborated` on a `verified` item has no in-tree statement of why that combination is INTENDED rather than an unfinished gate.
  THE BACKLOG ITEM'S OWN SEQUENCING PREMISE IS NOW STALE, AND SAYING SO IS WHAT MAKES THIS PLAN HONEST RATHER THAN A RESTATEMENT. The item says the question should survive "their execution instead of vanishing when they class `done`" and describes `bjx20r` and `btak7a` as "two pending plans". Both are EXECUTED (`bjx20r` 2026-10-01, `btak7a` 2026-10-02, both by `aw agy run`), and their parent backlog `5xgllt` is already `done`. So the item is not waiting on those plans. It is waiting on the ONE INPUT it names as decisive, and that input was MEASURED AND CAME BACK EMPTY: `bjx20r` E-06 was required to report a real-corpus false-negative rate, and its V-06 evidence reads `REAL CORPUS SIZE: 0` with "real-corpus calibration is OUTSTANDING" stated in as many words, because `.aw/records/runs/` is gitignored (`.aw/.gitignore:14:records/runs/`) and absent from every lane worktree by construction.
  WAITING FOR THAT NUMBER IS NOT A STRATEGY, BECAUSE THE SAME CONSTRUCTION THAT PRODUCED ZERO WILL PRODUCE ZERO AGAIN. Every execution of a plan in this repository happens in an isolated lane that has no runs tree, so a plan that asks for the rate gets zero, indefinitely. An item parked on an input its own execution model cannot supply is a permanent `open`, which is the shape `aw attention` exists to surface and which costs a reader on every sweep. The honest move is therefore to decide the question on the evidence that IS available and durable, and the repository has an unusual amount of it: P15 names this exact mechanism class, the maintainer ruled twice on the governing principle, and a shipped test already pins the no-refusal behavior.
  THE EVIDENCE DECIDES IT AGAINST REFUSING, AND NOT ON PREFERENCE. GUIDING_PRINCIPLES P15 states "We mitigate SLOPPINESS, not MALICE", forbids "any mechanism whose justification is 'in case the agent lies'", and cites this very precedent ("a proposed baseline gate for suite failures was rejected because 'a gate cannot detect deception' ... maintainer ruling 2026-09-08, `daexj1` OQ-02, reaffirmed 2026-09-20"). `runner_shared`'s pre-work-suite-baseline comment block records that ruling with four reasons, and reason 3 applies to `verifier_corroboration.py` verbatim ("A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file"). Spec `25kzda` Section 5.1's HONEST LIMIT paragraph, as amended 2026-10-01 by plan `kcc71f`, names the DIRECTION: "nothing may refuse on the baseline (using the baseline to disbelieve an agent remains forbidden), while a comparison that only ever makes a gate more permissive is not such a refusal". A corroboration refusal is the forbidden sign of exactly that comparison.
  AND THE MATCHER IS MEASURABLY NOT TRUSTWORTHY ENOUGH TO STRAND A LANE ON, WHICH IS AN INDEPENDENT REASON THAT DOES NOT DEPEND ON P15 AT ALL. `bjx20r` F-5 enumerated four mechanisms by which a GENUINE test run is unmatchable, and one of them (`make test` indirection) was demonstrated AT REVIEW to produce a confident false `uncorroborated` against a verifier that really ran the suite; it was fixed with an allowlist plus a sixth `indeterminate` arm. A FIFTH mechanism is live RIGHT NOW and already filed: backlog `iuhx9d` (`open`, `bug`, `Blocks-Release: next`) records that an Antigravity `step_type == "subagent"` delegation is invisible to the reader, so a delegating verifier falls through to `uncorroborated`. MEASURED IN THIS LANE at HEAD `ccd7ee3b8`: a session log carrying one `step_type: "subagent"` event plus one unrelated `git status` tool call yields `verdict=uncorroborated reason=uncorroborated delegation_count=0`, i.e. a false accusation of fabrication, today. A refusal built on this predicate would convert a known-open correctness bug into stranded work.
  WHY THIS IS `followup` AND CARRIES NO RELEASE GATE. The item is `followup` and carries no `- Blocks-Release:`, and that is correct under the repository's perceptibility test: nothing a user runs returns a wrong answer or waits longer, because the decision this plan records CHANGES NO BEHAVIOR. The adjacent correctness defect IS a gated bug and is already gated on its own item (`iuhx9d`), which is where that gate belongs; inventing a second one here would double-count it.
- Scope: DECIDE THE QUESTION "NO", RECORD IT IN THE THREE PLACES A LATER AUTHOR WILL LOOK, AND LEAVE EVERY RUNTIME BEHAVIOR EXACTLY AS IT IS. IN, five things, each one deliverable. (1) RE-MEASURE the four facts this plan's answer rests on at the executing HEAD, as a gate with named STOP conditions, because three of them are live properties other lanes are editing and one of them (the real corpus size) is the input the backlog item calls decisive. (2) WRITE THE DECISION WHERE THE VERDICT IS COMPUTED: a contract block on `verifier_corroboration.py` stating that the verdict is observational, that an `uncorroborated` verdict MUST NOT refuse, downgrade, or alter any disposition, and the three measured reasons that force it, so the next author reading the module finds the answer beside the code rather than in a retired plan. (3) PIN THE DECISION BEHAVIORALLY on the PIPELINE-COMPUTED integration decision, by driving the real `runner_shared.execute_item_core` with self-finalize ON across all three verdicts and asserting the integration signal the pipeline itself RECORDS is identical, which is the one assertion the shipped equality test does NOT make (it runs with self-finalize OFF, so the pipeline never records an integration signal, and its own `integration_is_earned` call is made by the test with inputs that cannot vary with the verdict; measured at review, an integration-only refusal keyed on `uncorroborated` leaves it green). (4) RECORD IT DURABLY in `DECISIONS.md` as the next `### D<n>` entry naming the rejected alternative and the reasons it was rejected, plus a one-line `CHANGELOG.md` note, and close `btak7a` OQ-01's carrier chain in the entry's prose. (5) AMEND SPEC `25kzda` SECTION 5.1 to say that a recorded verifier-corroboration verdict is an observational record that refuses nothing, because Section 5.1 is the section that classifies a verifier's self-report INADMISSIBLE and captured tool events ADMISSIBLE, and that juxtaposition is precisely the textual argument FOR refusing; leaving it unqualified leaves the strongest case for the rejected answer sitting in an approved spec.
  OUT, each for a stated reason. BUILDING ANY REFUSAL, DOWNGRADE, OR DISPOSITION CHANGE on the verdict: that is the REJECTED answer, refused on the evidence in F-03 through F-06 rather than deferred. FIXING THE AGY `subagent` DELEGATION BLINDNESS: measured here as F-06 because it is load-bearing for the decision, but owned by backlog `iuhx9d` (plan `e08ssu`, now executed, routed the readers through a shared primitive and deliberately preserved the gap); this plan changes no matching, extraction, or verdict logic, and a plan that answered a policy question by also editing the predicate could not be reviewed for either. CHANGING ANY RECORDED FIELD OR RENDERED SURFACE: `corroboration_verdict`, `corroboration_reason`, `corroboration_counts`, the `execution-report.md` line, and the `aw runs` rendering all stay exactly as `btak7a` shipped them. REVISITING THE SUITE-BASELINE RULING or the attributed suite-attribution exception, which are settled and cited here only as precedent. TOUCHING `bjx20r` OR `btak7a`, which are in `.aw/records/plans/executed/` and whose records `AGENTS.md` forbids changing. RE-MEASURING THE REAL-CORPUS RATE IN A WAY THAT CLAIMS A NUMBER: E-01 reports the corpus size it actually finds, which in a lane is zero, and the decision is explicitly NOT contingent on it (F-02 is why).
- Scope-Paths: agent_workflows/verifier_corroboration.py, tests/test_verifier_corroboration.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: sinhkj
- From-Spec: 25kzda
- Set: runverdict
- Order: 11
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: q4uifc
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-101, PR-102, PR-103, PR-104. Round 2 re-review at HEAD `1ec59c8a1`. PR-101 (MEDIUM): `execute_item_core` resolves `integration_is_earned` and `driver_begin` through `driver_module` (`oc_runipd`), so an in-process mutation patching `runner_shared.integration_is_earned` is never called (spy: zero calls; signal stays `verifier`), a false insensitivity result; E-03/V-03 now name `oc_runipd` as the seam, and the mutation re-measured through it flips `uncorroborated` to `verifier-declined` (others `verifier`); the stub is now `oc_runipd.driver_begin`. PR-102: `e08ssu` executed (commit `9c5f53f18`) and preserved the subagent gap; F-06 re-driven, still `uncorroborated`, delegations 0. PR-103: `D159` already exists. PR-104: the three F-10 baseline failures now pass (commit `8c460a9a1`); `runner_shared.py` is now 41024 lines. Readiness re-written as the review output after `8c460a9a1` removed it from the `to-review` plan. Review record round 2.

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Readiness go-pending-approval. PR-001 (HIGH) redesigned E-03/V-03: the authored predicate-level test and the shipped equality test were both MEASURED blind to an integration-only refusal keyed on `uncorroborated` (shipped test green under the mutation; the pipeline's own `integration_is_earned` site never runs with `self_finalize: False`); E-03 now drives `execute_item_core` with self-finalize ON and `driver_begin` stubbed and asserts the pipeline-recorded `integration_signal`, which the same mutation flips to `verifier-declined`. PR-002 corrected `t18l64` from pending to executed (carrier path). PR-003 corrected F-02's "runs directory absent" to "no verification outcomes". PR-004 noted F-06 re-driven at review (unchanged: `uncorroborated`, delegations 0). Review record `.aw/records/reviews/20261002-runverdict-11-q4uifc-decide-that-an-uncorroborated-verifier-turn-never-refuses-in.review.md`.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `sinhkj` at HEAD `ccd7ee3b8`. TWO OF THE ITEM'S PREMISES ARE FALSIFIED AND CORRECTED HERE RATHER THAN CARRIED FORWARD. First, it calls `bjx20r` and `btak7a` "two pending plans" whose execution the question must survive; both are EXECUTED and their parent item `5xgllt` is already `done`, so the question already survived them (via `btak7a` OQ-01's `- Carrier: sinhkj`) and nothing is waiting on them. Second, it proposes to "accumulate verdicts across real runs, then revisit this item with the observed rate in hand"; that sequencing is UNREACHABLE by construction, because `.aw/records/runs/` is gitignored and absent from every lane worktree, which is exactly why `bjx20r` E-06 already measured `REAL CORPUS SIZE: 0`. A THIRD FACT THE ITEM DOES NOT MENTION STRENGTHENS ITS OWN "CASE AGAINST" INDEPENDENTLY OF P15, and was measured in this lane rather than read: the agy `step_type == "subagent"` delegation shape is invisible to the reader, so a delegating verifier turn reaches `uncorroborated` TODAY (`delegation_count=0`, observed 1, verdict `uncorroborated`), a live false accusation filed as `bug` `iuhx9d` with `Blocks-Release: next`. The decision is therefore taken on durable evidence (P15, the twice-affirmed maintainer ruling, spec 5.1's directional amendment, and a measured false positive) rather than on a rate that cannot be obtained.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Answer backlog `sinhkj` and `btak7a` OQ-01 with a recorded NO: a verifier-corroboration verdict is an observational record and never refuses, downgrades, or changes a disposition. Write that answer where the verdict is computed, pin it with one pipeline-level test the shipped suite does not already make (the integration signal `execute_item_core` itself records), record it in `DECISIONS.md`, and amend spec `25kzda` Section 5.1 so the admissibility juxtaposition that is the strongest argument FOR refusing no longer reads as an unfinished obligation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before deciding anything

- [x] E-01 Re-drive the four measurements this plan's answer rests on, at the executing HEAD, and record each verbatim, so a policy decision is taken against current fact rather than against this plan's authoring snapshot. EDIT NO FILE IN THIS ITEM.
  - Depends on: none
  - Expected outcome: four pasted transcripts. (a) THE NO-CONSUMER CENSUS: a repository search for every reader of the three recorded fields and of the verdict function, showing that every consumer is a RENDERER or a TEST and that no disposition, `verify_disp`, refusal, or integration decision reads any of them. Report the consumer list, not a count. (b) THE CORPUS SIZE, honestly including zero: resolve the runs root, count `outcomes/*-verification.json` beneath it, and paste the command that established the number. State in one sentence whether the real-corpus rate the backlog item calls decisive is obtainable in this execution environment. (c) THE LIVE FALSE POSITIVE: construct a session log carrying one Antigravity `step_update` of `step_type: "subagent"` (with a `subagent_info.subagents` entry) plus one unrelated non-test shell command, call `corroborate_verifier_turn` with a genuine-looking pytest claim, and paste the returned `verdict`, `reason_code`, `delegation_count` and `observed_count`. (d) THE GOVERNING TEXT: paste the three authorities this decision cites, each located by its own content rather than by offset, namely GUIDING_PRINCIPLES P15's "WHAT NOT TO BUILD" sentence, `runner_shared`'s four numbered reasons in the pre-work-suite-baseline block, and spec `25kzda` Section 5.1's HONEST LIMIT sentence naming the direction of the prohibition.
    THIS ITEM IS A GATE, AND IT GATES IN A SPECIFIC DIRECTION, so an executor knows which disagreement stops the plan and which merely changes its wording. If (a) finds ANY non-renderer consumer, STOP AND REPORT: a refusal or downgrade has landed in the meantime, and this plan would be recording a decision the tree contradicts. If (c) returns `indeterminate` with reason `delegation-present`, the agy blindness has been FIXED by `iuhx9d` in the meantime (`e08ssu` has executed and deliberately preserved the gap, so it is no longer a candidate); that does NOT stop the plan and does NOT change the answer, because F-03 through F-05 carry it without F-06, but E-02's third reason must then be reworded to cite the fix rather than the live defect, and V-01 must say so. If (d) finds any of the three authorities materially changed (in particular if the HONEST LIMIT paragraph no longer forbids refusal), STOP: the decision rests on those texts and must be re-derived rather than asserted. A zero corpus in (b) is the EXPECTED result and is not a stop condition; it is the plan's premise.
  - Execution state: performed

### Task group 2: write the decision where the verdict is computed

- [x] E-02 Give `agent_workflows/verifier_corroboration.py` an explicit DECISION block in its module docstring stating that the verdict is observational and MUST NOT be consumed as a refusal, downgrade, or disposition change, with the three measured reasons that force that answer and the imperative for the next editor.
  - Depends on: E-01
  - Expected outcome: the module docstring gains a short block (beside its existing `DESIGN CONSTRAINTS AND SCOPE BOUNDARIES` and `CLOSED-SET VERDICT CONDITIONS` sections, which it must not disturb) answering the question in one readable paragraph and giving THREE reasons, each a fact E-01 re-measured rather than an assertion: (1) GUIDING_PRINCIPLES P15 forbids a mechanism justified by "in case the agent lies", and the maintainer's 2026-09-08 and 2026-09-20 rulings reject a gate keyed on derived suspicion of dishonesty, with reason 3 of the recorded four applying to THIS module verbatim because an agent that would fabricate has write access to this file; (2) spec `25kzda` Section 5.1's HONEST LIMIT paragraph permits only a comparison that makes an outcome MORE permissive and forbids one that refuses, so a corroboration refusal is the forbidden sign; (3) the predicate's own known false positives make it unsafe to strand a lane on, with the measured agy `subagent` case named as the live instance and `iuhx9d` named as its carrier. It must also state the CONSEQUENCE in the imperative: a future consumer may READ the verdict and may make an outcome MORE permissive on it, and must not refuse, downgrade, or change a disposition on it; a reader who believes a refusal is warranted opens a new decision rather than wiring one here.
    CITE BY SYMBOL AND BY QUOTED CONTENT, NOT BY OFFSET (`IPD-C801`): name `runner_shared.execute_item_core`, `runner_shared.integration_is_earned`, `GUIDING_PRINCIPLES.md` P15, spec `25kzda` Section 5.1, and backlog `iuhx9d`, appending a line number to at most one of them, because `runner_shared.py` is over 41000 lines here and an offset into it expires within days.
    CHANGE NO CODE IN THIS ITEM, and the restraint is load-bearing rather than tidiness: the decision is that the shipped behavior is already correct, so a correct execution of this plan changes ZERO runtime lines in this module. Do not touch the verdict constants, the reason codes, `KNOWN_TEST_INDIRECTIONS`, the extractor, the matcher, or the two backward-compatible aliases at the file's tail. If an executor finds themselves editing logic here, they have mixed this plan with `iuhx9d`.
  - Execution state: performed

### Task group 3: pin the decision behaviorally

- [x] E-03 Add one test to `tests/test_verifier_corroboration.py` that drives the REAL `runner_shared.execute_item_core` with self-finalize ON across all three verdict values and asserts the integration decision the PIPELINE ITSELF RECORDS is identical, so the decision is enforced by an outcome rather than only documented.
  - Depends on: E-02
  - Expected outcome: a new test function (in the existing `TestCorroborationInteractionAndOutcomeEquality` class, which is this contract's shipped home) that, for each of the three verdicts, drives `execute_item_core` through the file's existing `_drive_execute_turn` fixture shape with the verifier session-log fixtures the shipped equality test already uses, but with `state["options"]["self_finalize"] = True` (so `integration_gate_relevant` is true and the pipeline's own `integration_is_earned` call site runs) and with `driver_begin` stubbed to succeed (`monkeypatch.setattr(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok"))`, the same stub shape `tests/test_suppress_narrowing.py` uses; `execute_item_core` resolves `driver_begin` via `getattr(driver_module, "driver_begin", ...)` and the fixture passes `driver_module=oc_runipd`, so the `oc_runipd` attribute is the one consulted, although at review a stub on `runner_shared` was also measured to reach `executed`/`verifier` because `oc_runipd.driver_begin` delegates to it), because a real `driver_begin` against the throwaway fixture plan refuses and ends the item `fail-begin` before verification runs. It then ASSERTS the recorded `corroboration_verdict` is the one intended (so a miscalibrated fixture cannot make the test vacuous), and asserts that the `integration_signal` the pipeline recorded on the item and on the attempt is identical across the three verdicts (measured at review: `verifier` in all three on the unmodified tree), together with `item["status"]` and `item["verification_status"]`. The test must NOT call `integration_is_earned` itself: a test-side call supplies its own inputs and so cannot observe a refusal wired into the pipeline, which is exactly the shipped test's blind spot. The failure message must name the decided contract and point at the `DECISIONS.md` entry E-05 writes, rather than inviting a reader to relax the assertion.
    WHAT THIS ADDS THAT THE SHIPPED TEST DOES NOT, MEASURED AT REVIEW rather than argued: `test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts` runs through `_drive_execute_turn`, which sets `self_finalize: False`, so `integration_gate_relevant` is false, the pipeline never records an `integration_signal` (it is `None` on the item), and the test's only integration assertion is its OWN call `integration_is_earned(validate=True, verify_disp=item["verification_status"], suite_result=0)`. A spy at review confirmed that call is the ONLY `integration_is_earned` invocation during the test. Then a call-site mutation (`verify_disp=VERIFY_DISP_UNVERIFIED if item.get('corroboration_verdict') == 'uncorroborated' else verify_disp` at the pipeline's `integration = integration_is_earned(...)` site) was applied in-process. MUTATION SEAM, measured at round 2 and load-bearing: `execute_item_core` binds `integration_is_earned = getattr(driver_module, "integration_is_earned", None)`, so with `driver_module=oc_runipd` the name it calls is `oc_runipd.integration_is_earned`; an in-process mutation that patches `runner_shared.integration_is_earned` is NEVER CALLED (spy recorded zero calls) and leaves the signal `verifier`, a false 'test is insensitive' result. Apply the mutation either as a source edit at the call site or by patching `oc_runipd.integration_is_earned`, and do NOT treat a patch on `runner_shared` as a valid red run. With that seam, the shipped test PASSED in all three arms, while the same drive with self-finalize ON and `driver_begin` stubbed recorded `integration_signal` `verifier-declined` for `uncorroborated` and `verifier` for the other two. So the shipped test catches a refusal that rewrites `verification_status` but is blind to one that refuses integration only, and the new test catches both. If the executor finds on reading that a shipped test already makes this assertion, do NOT author a duplicate: report it in V-03, state which assertion covers it, and mark this item `blocked` with the evidence rather than padding the suite.
    ASSERT OUTCOMES, NOT STRUCTURE (`AGENTS.md`; GUIDING_PRINCIPLES P16): no `inspect`, `ast`, regex, or substring search over production source, and specifically NO pin on the docstring text E-02 writes. Assert on recorded state the pipeline wrote.
    ENVIRONMENT NOTE, measured at review: the test must not depend on the lane's `AW_EXECUTION_ROLE=worker` environment; with `driver_begin` stubbed the drive was measured to reach `executed`/`verifier` both inside this lane's environment and with the `AW_*` role variables unset, so the stub is what makes it environment-independent.
    VERIFY SENSITIVITY BY MUTATION, because a guard never observed to fail is not evidence and for this plan the guard IS the enforcement: apply the call-site mutation above (an integration-only refusal keyed on `uncorroborated`, leaving `verification_status` untouched), observe the new test FAIL, revert, observe it PASS, and paste both runs in V-03. ALSO run the SHIPPED equality test under the same mutation and paste that it stays green, which is the evidence that E-03 is not redundant.
  - Execution state: performed

### Task group 4: amend the spec that carries the case for the rejected answer

- [x] E-04 Amend spec `25kzda` Section 5.1 to record that a verifier-corroboration verdict is an observational record that refuses nothing, so the section's own admissibility juxtaposition is not read as an unfinished obligation to refuse.
  - Depends on: E-01
  - Expected outcome: a short addition inside Section 5.1, placed with the HONEST LIMIT paragraph that already states the direction of the baseline prohibition, recording three things: that the run records a three-state corroboration verdict comparing a verifier's claimed test commands against the tool calls its own session log shows; that the verdict is OBSERVATIONAL, so no refusal, downgrade, or disposition change may be keyed on it, which is the same direction the HONEST LIMIT paragraph already establishes for the suite baseline; and that the section's classification of a verifier's self-report as inadmissible is NOT an instruction to refuse on a mismatch between the two, because the predicate has measured false positives and because P15 forbids a gate justified by suspected dishonesty. Append the history record with `aw specs note` (NOT by hand-editing the history), naming this plan and the backlog item, and stating what deliberately did NOT change: the admissible and inadmissible lists, the attributed suite-attribution exception and all of its conditions, and the HONEST LIMIT paragraph's existing wording.
    THE SPEC EDIT IS DECLARED IN `- Scope-Paths:` DELIBERATELY, because that is what makes the amendment visible to the runner's pre-run announcement and its end-of-run reconciliation (`AGENTS.md`). It is owed rather than optional: this plan decides the AUTHORITY under which a `verified` verdict may be recorded in the presence of a contradicting observation, and `btak7a`'s own spec-sync section states that a refusal "WOULD" owe this amendment. Recording the refusal's REJECTION is the same contract question answered the other way, and leaving the spec silent is what let two plans in a row have to re-argue it.
    DO NOT WEAKEN THE INADMISSIBILITY RULE. "A verifier's opinion" and "an agent-authored summary or checklist without captured evidence" REMAIN inadmissible as completion evidence; this amendment says only that the corroboration verdict does not refuse. An executor who finds themselves deleting or qualifying an entry in either list has gone beyond this plan and must STOP.
  - Execution state: performed

### Task group 5: record the decision durably

- [x] E-05 Record the decision in `DECISIONS.md` as the next `### D<n>` entry with a one-line `CHANGELOG.md` note, and close the carrier chain in the entry's prose.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a new entry following the shipped `Context` / `Decision` / `Applied` shape of its neighbours (`D157` and `D158` are the nearest precedent in form). NUMBER IT FROM THE FILE, NOT FROM THIS PLAN: read the highest existing `### D<n>` heading at execution time and use the next integer, because another lane may add one first; authoring measured the tail as `D158` and round 2 review measured `D159` already taken (`### D159. Status transition citation rewrite ...`), so the number is whatever the file says at execution and neither is an instruction. `Context` states what shipped (the recorded three-state verdict and its surfaces), what was left open (`btak7a` OQ-01, carried by `sinhkj`), and why the input the item called decisive is unobtainable. `Decision` states NO, names the REJECTED alternative (refusing or downgrading an `uncorroborated` turn) and the three reasons it was rejected, and states explicitly that a future consumer may still make an outcome MORE permissive on the verdict, so the decision is not read as a ban on reading the field. `Applied` names the files this plan actually changed and cites this plan by id6 and Set. The prose must state that `btak7a` OQ-01 is answered by this entry, so a reader arriving from that plan lands on the answer. Do NOT edit `btak7a` itself: it is in `.aw/records/plans/executed/` and `AGENTS.md` forbids changing what it records.
    BOTH FILES ARE USER-FACING, so write NO em or en dash in either (`AGENTS.md`). The `CHANGELOG.md` line is one sentence recording that the corroboration verdict is declared observational; it changes no behavior, so it must not be written as a fix.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number appended to at most one of those and never standing alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This bites hard here, because `agent_workflows/runner_shared.py` is over 41000 lines in this checkout (measured 41024 at round 2 review, up from over 36000 at authoring) and the corroboration call site sits past line 34000.
- Tests assert OUTCOMES, never code structure or text (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). E-03 is written to that rule, which is also why it pins the decision by driving `execute_item_core` and asserting on the `integration_signal` it records rather than by searching for the docstring E-02 writes.
- A guard must be shown to FAIL before it counts as evidence (P16 "Verify test sensitivity with mutation"), and `btak7a`'s own V-05 demanded exactly this red-then-green proof for the equality guard it shipped. E-03 inherits that discipline.
- `GUIDING_PRINCIPLES.md` P15 closes by obliging any review that touches a gate to "keep it, simplify it into a clear refusal, or delete it". This plan touches a mechanism that is NOT a gate and records the decision to keep it that way, which is the P15-compliant disposition for an observational record.
- A plan MAY amend a spec and MUST declare the `.spec.md` in `- Scope-Paths:` so both runners announce and reconcile it (`AGENTS.md`). E-04 declares `25kzda` for that reason, and `- From-Spec: 25kzda` is carried so the handoff is machine-readable (`check.from-spec-dangling` resolves it).
- Spec history is appended with `aw specs note`, not by hand-editing the `## Workflow history` block; the shipped notes in `25kzda` are all tool-written in the `AMENDED (plan <id6>, backlog <id6>): ...` shape, which E-04 follows.
- `DECISIONS.md` entries use a `Context` / `Decision` / `Applied` shape, name the rejected alternative, and cite the executing plan by id6 and Set. `D157` and `D158` are the nearest precedent in form.
- `aw ipd scaffold` omits `- Readiness:` and an author must not write it: it is `/plan-review`'s output, and a hand-written value forges a review attestation that the auto-approve predicate reads FIRST (`AGENTS.md`; `IPD-M107`). This plan omits it.
- The suite is run BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Adding `-n0` or a second `-q` is prohibited, and `-o addopts=""` is the sanctioned way to get per-test counts from a narrowed run (`AGENTS.md`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE RECORD SHIPPED AND NOTHING REFUSES ON IT, SO THE DECISION IS GENUINELY THE ONLY THING OUTSTANDING.** `verifier_corroboration.corroborate_verifier_turn(log_path, claimed_commands)` returns a `CorroborationVerdict` whose `verdict` is one of `corroborated` / `uncorroborated` / `indeterminate` with six distinct `indeterminate` reason codes; `runner_shared.execute_item_core` calls it function-locally and writes `corroboration_verdict`, `corroboration_reason` and `corroboration_counts` onto BOTH the attempt and the item; `runner_shared.format_verifier_evidence_section` renders a `Corroboration: <verdict> (reason: <reason>)` line into `execution-report.md`; and `run_viewer`'s `StepSummary` carries both fields into the human and `--json` renderings. EVERY consumer is a renderer or a test: the search for the three field names plus the function name returns `verifier_corroboration.py`, `run_viewer.py`, `runner_shared.py` and `tests/test_verifier_corroboration.py` and nothing else, and no hit sits in a disposition, `verify_disp`, refusal, or integration path | the signature driven in this lane (`corroborate_verifier_turn(log_path: 'Path \| str', claimed_commands: 'Sequence[str]') -> 'CorroborationVerdict'`); the module docstring's `CLOSED-SET VERDICT CONDITIONS` block; the consumer search over `agent_workflows/` and `tests/` |
| F-02 | **THE BACKLOG ITEM'S PROPOSED SEQUENCING IS UNREACHABLE BY CONSTRUCTION, WHICH IS WHY THIS PLAN DECIDES INSTEAD OF WAITING.** The item says to "ship the record (both plans), accumulate verdicts across real runs, then revisit this item with the observed rate in hand", and names `bjx20r` E-06 as the measurement. That measurement ALREADY RAN and its V-06 evidence records `REAL CORPUS SIZE: 0` with the sentence that "real-corpus calibration is OUTSTANDING". The cause is structural rather than incidental: `.aw/records/runs/` is gitignored, so a lane worktree carries none of the primary checkout's run history (review measured a lane where the directory had been created locally holding only `analytics/`, with ZERO `*-verification.json` files beneath it, so the property is "no verification outcomes", not "no directory"), and every plan in this repository executes in exactly such a lane, so the next attempt returns zero as well. An item whose stated unblocking condition its own execution model cannot supply is a permanent `open` | `git check-ignore -v .aw/records/runs/` reporting `.aw/.gitignore:14:records/runs/`; `ls -d .aw/records/runs` reporting no such file or directory in the authoring lane; at review, `find .aw/records/runs -name "*-verification.json" | wc -l` reporting `0` in a lane where the directory existed; `bjx20r`'s V-06 `Observed evidence` block quoted |
| F-03 | **P15 NAMES THIS MECHANISM CLASS AND FORBIDS IT, AND IT CITES THIS EXACT PRECEDENT.** `GUIDING_PRINCIPLES.md` P15 is titled "Guard against honest mistakes, never against a malicious agent", opens "We mitigate SLOPPINESS, not MALICE", lists under "WHAT NOT TO BUILD" any "mechanism whose justification is 'in case the agent lies'", and cites as a measured example that "a proposed baseline gate for suite failures was rejected because 'a gate cannot detect deception' and 'a genuinely malicious agent would rewrite the gate' (maintainer ruling 2026-09-08, `daexj1` OQ-02, reaffirmed 2026-09-20)". A refusal keyed on a claimed command not appearing in a log is a mechanism whose only justification is that the agent may have lied | P15's section text quoted from `GUIDING_PRINCIPLES.md` |
| F-04 | **THE FOUR RECORDED REASONS APPLY TO THIS MODULE, AND REASON 3 APPLIES VERBATIM.** `runner_shared`'s pre-work-suite-baseline comment block records the maintainer's ruling ("You cannot build a pre-test that detects deception ... We're mitigating sloppiness, not malice") and four numbered reasons, of which: reason 1 holds that a gate detects a MISMATCH and not deception, and a mismatch has innocent causes, which is exactly the four-mechanism false-negative problem `bjx20r` F-5 measured; reason 3 holds that "A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file", which is true of `verifier_corroboration.py` in precisely the same way; and reason 4 holds that the target is an agent who is WRONG in good faith. The block also records the DIRECTION that governs this plan: "A comparison that can ONLY make an outcome more permissive is permitted ... What is forbidden is using the baseline to DISBELIEVE the agent" | the four numbered reasons quoted from the pre-work-suite-baseline block in `runner_shared.py`; the directional sentence quoted from the same block |
| F-05 | **SPEC `25kzda` SECTION 5.1 CUTS BOTH WAYS, WHICH IS WHY THE SPEC AMENDMENT IS OWED RATHER THAN OPTIONAL.** The section lists "hash-bound argv-list tool events with exit codes and captured-output digests" as ADMISSIBLE completion evidence and lists "a verifier's opinion" and "an agent-authored summary or checklist without captured evidence" as NOT completion evidence, and Section 4.2 closes that captured tool events are admissible "because they are structured, hash-bound repository evidence, not agent narration". That juxtaposition is the textual case FOR refusing, and `btak7a`'s spec-sync section says in as many words that a refusal "WOULD" owe an amendment here. But the SAME section's HONEST LIMIT paragraph, amended 2026-10-01 by plan `kcc71f`, settles the direction against it: "nothing may refuse on the baseline (using the baseline to disbelieve an agent remains forbidden), while a comparison that only ever makes a gate more permissive is not such a refusal", followed by "this exception mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe". Leaving the section unqualified leaves the strongest argument for the rejected answer standing in an approved spec | Section 5.1's two lists and Section 4.2's closing sentence quoted; the HONEST LIMIT paragraph quoted; `25kzda`'s 2026-10-01 `aw specs note` history record for plan `kcc71f`; `btak7a`'s spec-sync paragraph quoted |
| F-06 | **A FALSE `uncorroborated` IS LIVE RIGHT NOW, MEASURED IN THIS LANE, SO A REFUSAL WOULD STRAND GENUINE WORK TODAY.** `bjx20r` F-5 enumerated four mechanisms by which a genuine run is unmatchable, and its review DEMONSTRATED one of them (`make test` indirection) producing a confident false `uncorroborated`, fixed with an allowlist plus a sixth `indeterminate` arm. A FIFTH is open: backlog `iuhx9d` (`open`, `bug`, `Blocks-Release: next`, filed by plan `e08ssu`) records that the reader detects delegation only by tool NAME inside a `step_type == "tool"` step, so Antigravity's dedicated `step_type == "subagent"` shape is invisible. DRIVEN HERE at HEAD `ccd7ee3b8`: a log with one `step_type: "subagent"` event plus one `git status` tool call, against the claim `python3 -m pytest tests/`, returned `verdict=uncorroborated reason=uncorroborated delegation_count=0 observed_count=1`. That is a confident accusation of fabrication against a verifier that delegated its test run, which is the exact outcome the module's own fail-open docstring promises cannot happen. This finding is INDEPENDENT of P15: even a repository that wanted an anti-fabrication gate could not safely build one on this predicate today | the driven probe output pasted above; `iuhx9d`'s front matter and its "MEASURED CONSEQUENCE" paragraph; `verifier_corroboration.py`'s docstring promise that a delegated turn resolves to `indeterminate` with reason `delegation-present` |
| F-07 | **THE SHIPPED EQUALITY TEST PINS THE RECORDING PATH, NOT THE DECISION PATH, WHICH IS THE GAP E-03 FILLS AND THE ONLY REASON E-03 IS NOT REDUNDANT.** `tests/test_verifier_corroboration.py::TestCorroborationInteractionAndOutcomeEquality::test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts` is parametrized over the three verdicts, drives the real `runner_shared.execute_item_core`, and asserts the recorded fields plus `verification_status`, `disposition`, `render_stream.refusal_of_item(item) is None` and `integration_is_earned(...).earned is True`. But its `integration_is_earned` call passes `verify_disp=item["verification_status"]`, which is `"verified"` in all three arms by construction, so that assertion cannot vary with the corroboration verdict and would still pass if a refusal were keyed on the verdict somewhere the test does not reach. REVIEW MEASURED THE GAP AND CORRECTED E-03'S ORIGINAL DESIGN: `_drive_execute_turn` sets `self_finalize: False`, so the pipeline's own `integration = integration_is_earned(...)` site never runs in that test (a spy saw exactly one call, the test's own); an in-process integration-only mutation keyed on `uncorroborated` at that site left the shipped test GREEN in all three arms, while a self-finalize-ON drive with `driver_begin` stubbed recorded `integration_signal` `verifier-declined` versus `verifier`. The authored E-03 (call `integration_is_earned` from the test with a `verified` turn per verdict) would have been equally blind, because `integration_is_earned(validate, verify_disp, suite_result)` takes no corroboration input and a test-side call supplies its own inputs. The targeted file passes today (`39 passed in 9.55s` for it plus `tests/test_suite_baseline_direction.py`), so E-03 adds an assertion to a green file rather than repairing a red one | the test function body read; its `integration_is_earned` call site quoted; `python3 -m pytest tests/test_verifier_corroboration.py tests/test_suite_baseline_direction.py -o addopts="" -q` reporting `39 passed in 9.55s` |
| F-08 | **THE P15 AUDIT ALREADY CLASSIFIED THE SIBLING MECHANISM AS KEEP, SO THIS DECISION FOLLOWS A SHIPPED PRECEDENT RATHER THAN SETTING ONE.** The `malgate` Set's audit record (`.aw/records/research/20260930-malgate-00-wv570i-p15-gate-audit.assessment.md`, written by executed plan `bec7ee`) enumerates 33 mechanisms and classifies the suite-baseline adjudication **KEEP / ALREADY-DECIDED** with the rationale that it "does not attempt to detect whether an agent deliberately faked test outputs" and is "the repository's gold-standard model for honest-mistake tooling", and separately classifies the baseline banner disclaimers **KEEP** as a compliant honest-limit disclaimer. The corroboration record is the same shape: an observational measurement whose honest limits are stated. The audit does NOT list corroboration, because it was written the day before `btak7a` landed, so this plan supplies the missing row rather than contradicting one | the audit record's classification table rows 16 and 32 quoted; `bec7ee`'s `- Status: executed` and its 2026-10-01 history record |
| F-09 | **ADJACENT WORK OWNS CHANGES THIS PLAN MUST NOT MAKE, AND ONE OF THEM WOULD BE THE MECHANISM IF THE ANSWER WERE EVER YES.** Plan `e08ssu` (Set `runverdict`, Order 10; EXECUTED since authoring, landed as commit `9c5f53f18`, verified at round 2 review) routed the per-host tool-call readers in `verifier_corroboration.py` through a shared primitive and deliberately returns `None` for the `subagent` shape so the gap is preserved rather than silently changed (round 2 re-drove F-06 at HEAD `1ec59c8a1`: still `uncorroborated`, `delegation_count=0`); backlog `iuhx9d` owns the fix. Plan `t18l64` (`From-Spec: 25kzda`; EXECUTED, moved to `.aw/records/plans/executed/` after this plan was authored, verified at review) changed what a verification refusal DOES, remanding to the agent under retry budget instead of a terminal `fail-verify` (the `verremand (t18l64) E-03` block in `runner_shared.execute_item_core`), which is the mechanism a future "yes" would use rather than stranding a lane. Pending orchestrator `qtz0us` (Set `malgate`) applies P15 to shipped gates and would audit any new refusal. So: this plan changes no matching or extraction logic, adds no refusal, and does not touch any of those plans. All of this is file-level overlap only, which is not a hazard: a run gives each item an isolated worktree and returns it through merge-and-revalidate (`AGENTS.md`) | `e08ssu`'s front matter and its E-01 statement; `iuhx9d`'s "SHAPE OF THE FIX" paragraph; `t18l64`'s front matter; `qtz0us`'s `- Kind: orchestrator` and Scope |
| F-10 | **THE BASELINE MUST BE COMPARED BY FAILURE SET AND NOT BY COUNT, BECAUSE THE PASS COUNT IN THIS TREE DRIFTS BY HUNDREDS BETWEEN DAYS, AND THE AUTHORING BASELINE IS THREE PRE-EXISTING FAILURES.** Measured in this lane at HEAD `ccd7ee3b8` on an UNMODIFIED tree: `3 failed, 4624 passed, 2 skipped, 3 warnings in 116.17s`, 232 deselected, failing in `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. None touches `verifier_corroboration`, `runner_shared`'s corroboration block, or any integration predicate, and ALL THREE are already filed as open backlog items (`6bolin`, `8jeh4x`, `bxnhdj`). The spec-conformance one was driven in isolation to confirm its cause is unrelated: it fails on `20261001-89xjll-...spec.md` reporting `['attention.unsafe-field']`, which is exactly what `6bolin` records, and not on `25kzda`. THE COUNT IS NOT USABLE AS A BAR: `btak7a`'s review recorded `3523 passed` with 208 deselected on 2026-10-01, a plan reviewed the same day recorded `4457 passed`, and this lane now measures `4624 passed`, so a count constant is stale within days. V-05 therefore compares the failing SET by node id against a baseline the executor re-measures on an unmodified tree, and treats counts as informational only. ROUND 2 REVIEW NOTE: at HEAD `1ec59c8a1` all three of those node ids PASS (commit `8c460a9a1` repaired them; `48 passed` for the three plus `tests/test_verifier_corroboration.py` and `tests/test_suite_baseline_direction.py`), so the executor's re-measured baseline may well be EMPTY, which is why the bar is the re-measured set and not this list. NOTE FOR THE EXECUTOR: the first listed failure is a spec-conformance test, so re-measure it specifically after E-04's spec amendment and confirm it fails identically rather than newly | the bare `python3 -m pytest` summary line and the three `FAILED` lines pasted above, taken in this lane before any edit; `btak7a`'s 2026-10-01 review history record; `ug85or` F-10 recording `4457 passed` and a 585-pass drift |

## Proposed changes (ordered, validatable)

1. **Re-measure first (E-01).** The no-consumer census, the corpus size (honestly including zero), the live agy `subagent` false positive, and the three governing texts are re-taken at the executing HEAD and pasted. A non-renderer consumer, or a materially changed authority, STOPS the plan; a zero corpus does not.
2. **Write the decision at the module that computes the verdict (E-02).** `verifier_corroboration.py`'s docstring gains a DECISION block: the verdict is observational, a refusal or downgrade keyed on it is forbidden, a more-permissive use is allowed, with the three measured reasons and an imperative for the next editor. No logic changes.
3. **Pin the decision (E-03).** One test in the existing `TestCorroborationInteractionAndOutcomeEquality` class driving the real `execute_item_core` with self-finalize ON for all three states and asserting the pipeline-recorded `integration_signal` is identical, proven sensitive by a red-then-green integration-only mutation that the shipped test is measured NOT to catch.
4. **Amend the spec that carries the case for the rejected answer (E-04).** Spec `25kzda` Section 5.1 records that the corroboration verdict is observational and refuses nothing, in the same direction its HONEST LIMIT paragraph already establishes, with the history record appended by `aw specs note`. The admissibility lists and the attributed-suite-attribution exception are untouched.
5. **Record the decision (E-05).** A `DECISIONS.md` entry in the `D157`/`D158` shape naming the rejected alternative and its three reasons, a one-line `CHANGELOG.md` note, and an explicit statement that `btak7a` OQ-01 is answered.

## Deferred / out of scope (with reason)

- **Building any refusal, downgrade, or disposition change on the corroboration verdict.** This is the REJECTED answer, refused on the evidence rather than deferred: F-03 and F-04 show the repository forbids a gate justified by suspected dishonesty, F-05 shows the governing spec paragraph permits only the more-permissive direction, and F-06 shows the predicate produces a false `uncorroborated` today.
  - Carrier-Declined: a DECISION NOT TO ACT creates no obligation. E-02 writes the refusal into the module's own contract, E-04 into the spec, and E-05 into `DECISIONS.md` with the rejected alternative named, so a later reader finds the reasoning rather than re-litigating it. A carrier would track work the repository has decided against.
- **Fixing the agy `step_type == "subagent"` delegation blindness.** A real correctness defect, measured in this lane as F-06 and load-bearing for the decision, but it changes a published verdict and belongs to the item that owns it. A plan that answered a policy question while also editing the predicate could be reviewed for neither.
  - Carrier: iuhx9d
  - Carrier-Evidence: .aw/records/backlog/open/20261002-runverdict-01-iuhx9d-subagent-step-type-delegation-missed.backlog.md
- **Any change to the recorded fields or the rendered surfaces.** `corroboration_verdict`, `corroboration_reason`, `corroboration_counts`, the `execution-report.md` `Corroboration:` line and the `aw runs` rendering all stay exactly as `btak7a` shipped them. The decision is that the shipped behavior is correct, so changing a surface would contradict the plan's own answer.
  - Carrier-Declined: nothing is owed, because nothing is wrong. The surfaces are pinned by shipped tests (the byte-identical-when-empty report assertion and the `StepSummary` backward-compatibility assertion in `tests/test_verifier_corroboration.py`), so recording a carrier would assert a defect this plan has not found.
- **Obtaining the real-corpus false-positive rate the backlog item calls decisive.** Unobtainable in any lane by construction (F-02), and the decision is explicitly NOT contingent on it: a rate could only ever make the case against refusing stronger, since the question is whether to refuse on a predicate already known to produce false positives.
  - Carrier-Declined: the input cannot be produced by the execution model that would have to produce it, so a carrier would track work no run can perform. If a maintainer ever wants the number, it is a read against a primary checkout's gitignored runs tree, which is an operator action rather than a plan.
- **Changing what a verification refusal does once one exists.** Remanding a refusal to the agent under retry budget instead of a terminal `fail-verify` is the mechanism a future "yes" would need, and it has already shipped (plan `t18l64`, executed; review corrected this entry from "pending").
  - Carrier: t18l64
  - Carrier-Evidence: .aw/records/plans/executed/20261001-verremand-01-t18l64-remand-verification-evidence-refusals-and-verification-failu.ipd.md
- **Adding the corroboration row to the `malgate` P15 audit record.** The audit (F-08) predates `btak7a` by a day and so omits corroboration. Its carrier plan `bec7ee` is EXECUTED, and `AGENTS.md` forbids changing what an executed plan records; the audit record itself is a research artifact whose classification this plan supplies in `DECISIONS.md` instead, which is the durable home a later reader is pointed at.
  - Carrier-Declined: the gap is closed by this plan's own deliverables rather than by editing another Set's record. Re-opening a terminal plan's artifact to add a row would be the in-place edit the execution contract prohibits.
- **Revisiting the suite-baseline ruling or the attributed suite-attribution exception.** Both are settled (`daexj1` OQ-02, reaffirmed 2026-09-20; spec `25kzda` Section 5.1 as amended by `n9na1c` and `kcc71f`) and are cited here only as precedent. This plan adds a statement about a DIFFERENT mechanism in the same direction.
  - Carrier-Declined: nothing is owed; the rulings are correct and this plan applies them rather than questioning them.

## Scope check

- Over-scope: none. Each E-item serves exactly one part of answering one question: E-01 the measurement the answer rests on, E-02 the answer at the module that computes the verdict, E-03 the enforcement, E-04 the answer in the governing spec, E-05 the durable cross-repository record. Nothing here changes a runtime behavior, a recorded field, a rendered surface, or a matching rule.
- Under-scope: the backlog item asks whether an uncorroborated turn "should ever refuse integration" and offers to revisit later with a measured rate. This plan answers NO now and explains why later is never (F-02), rather than deferring again. It also does NOT catalogue the predicate's false-positive mechanisms: F-06 records the one that is live and measured, as a REASON for the answer, while the enumeration itself is `bjx20r` F-5's and the fix is `iuhx9d`'s. The item's "two pending plans" framing is deliberately not carried forward, because both are executed; the plan says so explicitly rather than quietly treating the premise as true.
- Right-sizing, assessed per E-item: five items across five groups, each one concern in one focused pass. E-01 is one measurement pass over four probes, editing nothing. E-02 is one docstring block in one file. E-03 is one test function plus its mutation proof. E-04 is one spec addition plus one tool-appended history record. E-05 is one `DECISIONS.md` entry plus one `CHANGELOG.md` line, kept together because the changelog line is a one-sentence pointer to the entry and splitting them would create two items with identical evidence. E-02 and E-04 are deliberately SEPARATE despite recording the same answer: one is the module's internal contract carrying the full reasoning, the other is a normative spec amendment whose own history must record what did not change.

## Required tests / validation

- `python3 -m pytest tests/test_verifier_corroboration.py -o addopts=""` for per-test counts on the file E-03 extends, with output pasted. The explicit `-o addopts=""` is the sanctioned way to get per-test counts from a narrowed run (`AGENTS.md`).
- The RED-then-GREEN mutation proof for E-03: introduce a one-line refusal keyed on the `uncorroborated` verdict in the integration path, observe the new test FAIL, revert, observe it PASS. Both runs pasted. A guard never observed to fail is not evidence, and for this plan that guard IS the enforcement.
- `python3 -m pytest tests/test_suite_baseline_direction.py -o addopts=""` as the adjacent-contract regression set: it pins that nothing refuses on the pre-work baseline, which is the same direction this plan records for a sibling mechanism, so a change that broke the direction rule would be visible here.
- Bare `python3 -m pytest`, compared BY FAILURE SET AND NOT BY COUNT (F-10). The executor measures the baseline on an UNMODIFIED tree first, lists failing node ids, and the bar is a set no larger than that baseline. Any NEW failure must be shown to reproduce on an unmodified tree before it is called pre-existing.
- `aw specs check` (or `aw check`) after the `25kzda` amendment, confirming the spec remains conformant and its history record is well-formed.
- `aw check` after the `DECISIONS.md` and `CHANGELOG.md` edits, confirming the records tree stays conformant.
- `aw ipd lint --phase pre-transition` conforming on this plan.
- `aw sanitize --agent` reporting no `fail`, since three changed files (`DECISIONS.md`, `CHANGELOG.md`, and the spec) are user-facing or published.
- The E-01 no-consumer census re-run AFTER E-02 and E-03, confirming no consumer was added and that the only new reader is the test.

## Spec / documentation sync

- `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.1 is AMENDED by E-04, and the file is declared in `- Scope-Paths:` so both runners announce the declared spec edit before the run and reconcile it at the end (`AGENTS.md`). The amendment is OWED rather than optional: this plan decides the authority under which a `verified` verdict may be recorded in the presence of a contradicting observation, and `btak7a`'s own spec-sync section states that a refusal "WOULD" owe an amendment to this section. Recording the REJECTION of that refusal is the same contract question answered the other way, and leaving the section silent is what forced two consecutive plans to re-argue it from first principles. WHAT DELIBERATELY DOES NOT CHANGE, and E-04's history record must say so: the admissible list, the inadmissible list (including "a verifier's opinion"), Section 4.2's closing sentence, the attributed suite-attribution exception and every one of its conjunctive conditions, and the HONEST LIMIT paragraph's existing wording. The amendment ADDS a statement about a mechanism the section does not currently mention.
- `- From-Spec: 25kzda` is carried so the spec-to-plan link is machine-readable and resolvable (`check.from-spec-dangling`), beside `- From-Backlog: sinhkj`.
- `agent_workflows/verifier_corroboration.py`'s module docstring gains the DECISION block (E-02). This is a primary deliverable rather than documentation around one: the module is where a future author reaches for the verdict, so the statement that it must not be used as a gate belongs there, carrying the full reasoning that the user-facing records deliberately do not.
- `DECISIONS.md` and `CHANGELOG.md` record the decision with its rejected alternative (E-05). A `DECISIONS.md` entry is owed because this is a contract question an executed plan explicitly deferred to a carrier (`btak7a` OQ-01, `- Carrier: sinhkj`), and the shape precedent is exact in `D157` and `D158`.
- NO USER-FACING DOCUMENT UNDER `docs/` IS TOUCHED, and that is a measurement rather than an omission: a search for `corrobor` across `docs/` and `.aw/records/specs/` returns only two unrelated hits (a `setid` spec and the human-approval-attestation spec's review note), so no published document describes the verifier's corroboration handling and none contradicts this decision. `aw runs`' own output is self-describing.

## Open questions

### OQ-01: Should an `uncorroborated` verifier turn ever refuse, downgrade, or otherwise block integration?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, no human input required: NO. This is backlog `sinhkj`'s question and `btak7a` OQ-01, and four independent lines of evidence force the answer rather than leaving it to taste. FIRST, THE PRINCIPLE IS WRITTEN DOWN AND NAMES THIS CLASS: GUIDING_PRINCIPLES P15 forbids "any mechanism whose justification is 'in case the agent lies'" and cites as its measured example the rejection of a baseline gate because "a gate cannot detect deception" and "a genuinely malicious agent would rewrite the gate" (F-03). SECOND, THE RULING'S OWN REASONS APPLY HERE, one of them verbatim: reason 3 of the four recorded in `runner_shared`'s pre-work-suite-baseline block holds that a malicious agent has write access to the file holding the gate, which is as true of `verifier_corroboration.py` as of the baseline, and reason 1 holds that a gate detects a MISMATCH with innocent causes rather than deception (F-04). THIRD, THE GOVERNING SPEC PARAGRAPH ALREADY SETTLES THE DIRECTION: Section 5.1's HONEST LIMIT paragraph, as amended 2026-10-01, permits "a comparison that only ever makes a gate more permissive" and forbids using an observation "to DISBELIEVE the agent", and a refusal is the forbidden sign of exactly this comparison (F-05). FOURTH, AND INDEPENDENT OF ALL THREE, THE PREDICATE IS MEASURABLY NOT SAFE TO STRAND WORK ON: a false `uncorroborated` is reachable TODAY through the agy `step_type == "subagent"` delegation shape, driven in this lane returning `verdict=uncorroborated delegation_count=0` against a genuine claim, and filed as an open release-gating bug (`iuhx9d`); `bjx20r` F-5 enumerated four such mechanisms and one was demonstrated at review producing a false accusation before it was fixed (F-06). THE ANSWER IS NOT "NEVER READ THE FIELD": a consumer may read the verdict and may make an outcome MORE permissive on it, which is the direction the spec explicitly allows; what is refused is a refusal, a downgrade, or a disposition change. WHAT WOULD RE-OPEN THIS: a maintainer ruling, which is the only authority that can overturn it, and which would then owe its own spec amendment and would naturally consume `t18l64`'s remand mechanism rather than stranding a lane. The backlog item's own proposed unblocking input (an observed false-positive rate over real runs) is NOT the thing that would re-open it, because it is unobtainable in any lane (F-02) and could only ever strengthen the case against refusing.

### OQ-02: Is the agy `subagent` delegation blindness a precondition for this decision, or merely a reason for it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: MERELY A REASON, and stating that precisely is what keeps the decision from decaying when the defect is fixed. F-06's measured false `uncorroborated` is the most vivid evidence that a refusal would strand genuine work, but it is the FOURTH and weakest-standing of the four reasons: the first three (P15, the four recorded reasons, the spec's directional amendment) are policy and would hold even if the predicate were perfect, because P15's objection is to the JUSTIFICATION ("in case the agent lies") rather than to the accuracy. So when `iuhx9d` closes the delegation gap, the answer does not change and this plan's record does not become stale. E-01's gate is written to match: a probe that returns `indeterminate`/`delegation-present` means the fix landed, which does NOT stop the plan and requires only that E-02's third reason cite the fix rather than the live defect. The converse matters too and is why this is worth asking rather than assuming: if someone later argues the reverse, that a PERFECT matcher would license a refusal, the answer is still no on reasons one through three, and the honest statement of that is in the `DECISIONS.md` entry rather than left to be re-derived.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste all four transcripts in full. (a) THE CENSUS: the search command and its complete output, plus an explicit statement, consumer by consumer, of what each hit is (renderer, recorder, test), and the conclusion that no disposition, `verify_disp`, refusal, or integration path reads any of the three fields or the verdict function. A summary count does NOT satisfy this item; the reviewer must be able to check the classification. (b) THE CORPUS SIZE: the command that resolved the runs root, the command that counted `outcomes/*-verification.json` beneath it, and the number, stated explicitly INCLUDING zero, with one sentence on whether the rate is obtainable here. (c) THE FALSE POSITIVE: the fixture or inline log content, the exact call, and the returned `verdict`, `reason_code`, `delegation_count` and `observed_count`. If the result is `indeterminate`/`delegation-present` instead, say so plainly, name the change that fixed it, and record that E-02's third reason was reworded accordingly. (d) THE AUTHORITIES: the three quoted passages, each with the file it came from, and a statement that each still reads as this plan's Findings describe. State explicitly whether any STOP condition fired, and if one did, that the executor stopped rather than proceeding.
  - Observed evidence:
    (a) THE NO-CONSUMER CENSUS:
    Command: `git grep -n -E "corroborat(e_verifier_turn|ion_verdict|ion_reason|ion_counts)" agent_workflows/ tests/`
    Output:
    ```
    agent_workflows/run_viewer.py:1136:                item_corr_reason = item.get("corroboration_reason")
    agent_workflows/run_viewer.py:1155:                                item_corr_verdict = _v_data.get("corroboration_verdict")
    agent_workflows/run_viewer.py:1156:                                item_corr_reason = _v_data.get("corroboration_reason")
    agent_workflows/run_viewer.py:1162:                        item_corr_verdict = last_att.get("corroboration_verdict")
    agent_workflows/run_viewer.py:1163:                        item_corr_reason = last_att.get("corroboration_reason")
    agent_workflows/run_viewer.py:1210:                        corroboration_verdict=item_corr_verdict,
    agent_workflows/run_viewer.py:1211:                        corroboration_reason=item_corr_reason,
    agent_workflows/run_viewer.py:2441:        if step.corroboration_verdict:
    agent_workflows/run_viewer.py:2443:                f"corroboration: {step.corroboration_verdict} (reason: {step.corroboration_reason})"
    agent_workflows/run_viewer.py:2444:                if step.corroboration_reason
    agent_workflows/run_viewer.py:2445:                else f"corroboration: {step.corroboration_verdict}"
    agent_workflows/runner_shared.py:23438:        corr_verdict = it.get("corroboration_verdict")
    agent_workflows/runner_shared.py:23439:        corr_reason = it.get("corroboration_reason")
    agent_workflows/runner_shared.py:23445:                    corr_verdict = last_att.get("corroboration_verdict")
    agent_workflows/runner_shared.py:23446:                    corr_reason = last_att.get("corroboration_reason")
    agent_workflows/runner_shared.py:34771:                                        corroborate_verifier_turn,
    agent_workflows/runner_shared.py:34776:                                    v_corr = corroborate_verifier_turn(
    agent_workflows/runner_shared.py:34801:                            attempt["corroboration_verdict"] = v_corr_verdict
    agent_workflows/runner_shared.py:34802:                            attempt["corroboration_reason"] = v_corr_reason
    agent_workflows/runner_shared.py:34803:                            attempt["corroboration_counts"] = v_corr_counts
    agent_workflows/runner_shared.py:34804:                            item["corroboration_verdict"] = v_corr_verdict
    agent_workflows/runner_shared.py:34805:                            item["corroboration_reason"] = v_corr_reason
    agent_workflows/runner_shared.py:34806:                            item["corroboration_counts"] = v_corr_counts
    agent_workflows/verifier_corroboration.py:74:    "corroborate_verifier_turn",
    agent_workflows/verifier_corroboration.py:655:def corroborate_verifier_turn(
    agent_workflows/verifier_corroboration.py:796:check_verifier_corroboration = corroborate_verifier_turn
    agent_workflows/verifier_corroboration.py:797:compute_verifier_corroboration = corroborate_verifier_turn
    tests/test_verifier_corroboration.py: [test readers]
    ```
    Consumer-by-consumer classification:
    - `agent_workflows/run_viewer.py` lines 1136, 1155-1156, 1162-1163, 1210-1211, 2441-2445: RENDERER (`StepSummary` construction and CLI presentation in `aw runs`).
    - `agent_workflows/runner_shared.py` lines 23438-23446: RENDERER (`format_verifier_evidence_section` for `execution-report.md`).
    - `agent_workflows/runner_shared.py` lines 34771-34806: RECORDER (invokes `corroborate_verifier_turn` in `execute_item_core` and records fields onto attempt and item).
    - `agent_workflows/verifier_corroboration.py`: DEFINITION (primary implementation and backward-compatibility aliases).
    - `tests/test_verifier_corroboration.py`: TESTS.
    Conclusion: Every consumer is a renderer, recorder, or test; no disposition, verify_disp, refusal, or integration decision reads any of the three fields or the verdict function.

    (b) THE CORPUS SIZE:
    Command:
    ```
    python3 -c "from agent_workflows.runner_shared import state_root; from pathlib import Path; sr = state_root(Path('.')); print('runs_root exists:', sr.exists()); print('count:', len(list(sr.glob('**/outcomes/*-verification.json'))) if sr.exists() else 0)"
    ```
    Output:
    ```
    runs_root exists: False
    count: 0
    ```
    Command: `find .aw/records/runs -name "*-verification.json" 2>&1`
    Output: `find: '.aw/records/runs': No such file or directory`
    Command: `git check-ignore -v .aw/records/runs/` -> `.aw/.gitignore:14:records/runs/`
    The real-corpus false-negative rate the backlog item calls decisive is unobtainable in this execution environment by construction because `.aw/records/runs/` is gitignored and absent from all isolated lane worktrees.

    (c) THE LIVE FALSE POSITIVE:
    Inline log content:
    ```json
    {"event": "init", "init": {"session_id": "ses_test", "tools": []}}
    {"event": "step_update", "step_update": {"step_index": 0, "state": "DONE", "step_type": "user_input"}}
    {"event": "step_update", "step_update": {"step_index": 1, "state": "DONE", "step_type": "subagent", "duration_seconds": 5.0, "subagent_info": {"subagents": [{"name": "verifier-subagent", "status": "DONE"}]}}}
    {"event": "step_update", "step_update": {"step_index": 2, "state": "DONE", "step_type": "tool", "tool_name": "run_command", "duration_seconds": 0.2, "tool_info": {"parameters": {"CommandLine": "git status"}}}}
    {"event": "step_update", "step_update": {"step_index": 3, "state": "DONE", "step_type": "agent_response"}}
    ```
    Call: `vc.corroborate_verifier_turn(log_path, ['python3 -m pytest tests/'])`
    Returned:
    `verdict: uncorroborated`
    `reason_code: uncorroborated`
    `delegation_count: 0`
    `observed_count: 1`
    Full verdict: `CorroborationVerdict(verdict='uncorroborated', reason_code='uncorroborated', claimed_count=1, observed_count=1, matched_count=0, delegation_count=0, missing_command_count=0, matched_claims=[], unmatched_claims=['python3 -m pytest tests/'], observed_commands=[ObservedCommand(command='git status', tool='run_command', host='agy', error=False)])`

    (d) THE GOVERNING TEXT:
    1. GUIDING_PRINCIPLES.md P15 ("WHAT NOT TO BUILD"):
    "WHAT NOT TO BUILD: secrets or tokens meant to be hidden from an agent, forgery or tamper detection aimed at an agent, and any mechanism whose justification is "in case the agent lies". If real isolation is ever required, it comes from the operating system (a separate user, a sandbox such as the opt-in hardened profile), never from checks in our own code."
    2. runner_shared.py pre-work-suite-baseline block (lines 24454-24463):
    "1. A GATE CANNOT DETECT DECEPTION. It can only detect a MISMATCH between two id sets, and a mismatch has many innocent causes (a flaky test, a test that only fails under a different shard order, a new test added by a merge that landed mid-turn).
    2. A CAPABLE MODEL CAN MAKE TESTS PASS. Any gate keyed on "is this id in the baseline" is satisfiable by an agent that simply deletes or skips the test, which is strictly worse than the sloppiness it was built to catch.
    3. A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file.
    4. THE TARGET IS SLOPPINESS, NOT MALICE. An agent that broke something subtly and genuinely believes the failure is unrelated answers not-mine in GOOD FAITH and is WRONG. Telling it what was already red lets it be RIGHT. That is the whole deliverable."
    3. Spec 25kzda Section 5.1 HONEST LIMIT paragraph:
    "nothing may refuse on the baseline (using the baseline to disbelieve an agent remains forbidden), while a comparison that only ever makes a gate more permissive is not such a refusal."

    STOP condition check: None fired. Consumer search found only renderers/recorders/tests; agy subagent defect reproduced uncorroborated with delegation_count=0; authorities remain verbatim as cited.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the added docstring block in full, and paste a `git diff` over `agent_workflows/verifier_corroboration.py` demonstrating that the change is DOCSTRING ONLY: no added, removed, or modified executable line, no change to the verdict constants or reason codes, no change to `KNOWN_TEST_INDIRECTIONS`, the extractor, the matcher, or the two aliases at the file tail. Confirm the block states all three reasons and the imperative, and that it names the more-permissive allowance explicitly rather than reading as a ban on consuming the field at all. Confirm every citation in the block resolves at the executing HEAD, by locating each cited symbol and quoting the cited spec and principle text; a dangling citation in a block whose whole job is to prevent re-litigation fails this item. Also paste `python3 -c "import agent_workflows.verifier_corroboration"` or an equivalent import, showing the module still imports cleanly after the docstring edit.
  - Observed evidence:
    Added docstring block in `agent_workflows/verifier_corroboration.py`:
    ```python
    DECISION: OBSERVATIONAL VERDICT, REFUSAL FORBIDDEN:
    ========================================================================================
    The verdict computed by this module and recorded by `runner_shared.execute_item_core`
    is strictly observational. An `uncorroborated` verdict MUST NOT refuse, downgrade, or
    alter any item disposition, verification status, or integration decision (such as
    `runner_shared.integration_is_earned`). This policy is forced by three measured facts:
    (1) GUIDING_PRINCIPLES.md P15 forbids "any mechanism whose justification is 'in case
        the agent lies'", and the maintainer rulings of 2026-09-08 and 2026-09-20 reject
        gates keyed on suspected deception; reason 3 of the four recorded reasons in
        `runner_shared`'s pre-work-suite-baseline block applies to this module verbatim:
        an agent attempting to fabricate would have write access to this file.
    (2) Spec `25kzda` Section 5.1's HONEST LIMIT paragraph permits only comparisons that
        make an outcome MORE permissive and explicitly forbids using an observation to
        disbelieve the agent; a corroboration refusal is the forbidden sign.
    (3) The extraction predicate has known false positives that make it unsafe to strand a
        lane on: specifically, the Antigravity `step_type == "subagent"` delegation shape
        is unobserved by the reader, causing genuine test delegations to resolve to
        `uncorroborated` (tracked as bug `iuhx9d`).
    IMPERATIVE: A future consumer may read this verdict and may make an outcome MORE
    permissive on it, but MUST NOT refuse, downgrade, or change a disposition on it. A
    reader who believes a refusal is warranted opens a new decision rather than wiring
    one here.
    ========================================================================================
    ```

    `git diff agent_workflows/verifier_corroboration.py`:
    ```diff
    diff --git a/agent_workflows/verifier_corroboration.py b/agent_workflows/verifier_corroboration.py
    index 7f5e22ce6..0659b8290 100644
    --- a/agent_workflows/verifier_corroboration.py
    +++ b/agent_workflows/verifier_corroboration.py
    @@ -14,6 +14,30 @@ DESIGN CONSTRAINTS AND SCOPE BOUNDARIES:
       commands were observed, all observed commands resolved, and no claimed command matched.
     - No refusal or downgrade: this module is a measurement and predicate only.

    +DECISION: OBSERVATIONAL VERDICT, REFUSAL FORBIDDEN:
    +========================================================================================
    +The verdict computed by this module and recorded by `runner_shared.execute_item_core`
    +is strictly observational. An `uncorroborated` verdict MUST NOT refuse, downgrade, or
    +alter any item disposition, verification status, or integration decision (such as
    +`runner_shared.integration_is_earned`). This policy is forced by three measured facts:
    +(1) GUIDING_PRINCIPLES.md P15 forbids "any mechanism whose justification is 'in case
    +    the agent lies'", and the maintainer rulings of 2026-09-08 and 2026-09-20 reject
    +    gates keyed on suspected deception; reason 3 of the four recorded reasons in
    +    `runner_shared`'s pre-work-suite-baseline block applies to this module verbatim:
    +    an agent attempting to fabricate would have write access to this file.
    +(2) Spec `25kzda` Section 5.1's HONEST LIMIT paragraph permits only comparisons that
    +    make an outcome MORE permissive and explicitly forbids using an observation to
    +    disbelieve the agent; a corroboration refusal is the forbidden sign.
    +(3) The extraction predicate has known false positives that make it unsafe to strand a
    +    lane on: specifically, the Antigravity `step_type == "subagent"` delegation shape
    +    is unobserved by the reader, causing genuine test delegations to resolve to
    +    `uncorroborated` (tracked as bug `iuhx9d`).
    +IMPERATIVE: A future consumer may read this verdict and may make an outcome MORE
    +permissive on it, but MUST NOT refuse, downgrade, or change a disposition on it. A
    +reader who believes a refusal is warranted opens a new decision rather than wiring
    +one here.
    +========================================================================================
    +
     CLOSED-SET VERDICT CONDITIONS:
     ========================================================================================
     The turn-level corroboration verdict is partitioned into a closed set of conditions:
    ```
    The change is DOCSTRING ONLY: 0 executable lines modified, constants, reason codes, indirections, and matcher untouched.
    All citations resolve cleanly at HEAD (`runner_shared.execute_item_core`, `runner_shared.integration_is_earned`, `GUIDING_PRINCIPLES.md` P15, spec `25kzda` Section 5.1, backlog `iuhx9d`).
    Clean import: `python3 -c "import agent_workflows.verifier_corroboration; print('IMPORTED OK')"` -> `IMPORTED OK`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new test function in full and the output of `python3 -m pytest tests/test_verifier_corroboration.py -o addopts=""` showing it passing with the per-test count. Then paste the MUTATION PROOF, both halves: the exact integration-only refusal introduced at the pipeline's `integration = integration_is_earned(...)` call site in `runner_shared.execute_item_core` (as a source edit there, or by patching `oc_runipd.integration_is_earned`, the name that site resolves through `driver_module`; a patch on `runner_shared.integration_is_earned` is never called and is NOT a valid red run), the FAILING run of the new test with its assertion message, the SHIPPED equality test's run under the same mutation (expected green, which is what shows E-03 is not redundant), the revert, and the PASSING run. A test never observed to fail does not satisfy this item. State explicitly that the test reads each verdict from the `corroboration_verdict` the real pipeline recorded and ASSERTS it before asserting equality, so a drifted fixture cannot make it vacuous, that it asserts on the pipeline-recorded `integration_signal` rather than on a test-side `integration_is_earned` call, and that the recorded signal is non-`None` in every arm (a `None` signal means self-finalize was not engaged and the test is vacuous). Confirm by inspection that the test reads no production source and pins no docstring or comment text (P16). If the executor concluded the shipped test already covers this, paste the specific assertion that does so, mark this item FAILED or BLOCKED with that evidence rather than `pass`, and do NOT author a duplicate test.
  - Observed evidence:
    New test function in `tests/test_verifier_corroboration.py`:
    ```python
    @pytest.mark.parametrize(
        "verdict_kind",
        ["corroborated", "uncorroborated", "indeterminate"],
    )
    def test_pipeline_integration_decision_identical_across_corroboration_verdicts(
        self, verdict_kind: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """E-03 / V-03: Under self-finalize ON, the integration signal recorded by the pipeline

        itself is strictly identical across corroborated, uncorroborated, and indeterminate.
        Pins the D160 decision that an uncorroborated verifier turn never refuses integration.
        """
        monkeypatch.setattr(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok"))

        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-test"

            def verifier_spawner(
                prompt_path: Path,
                plan_path: Path,
                work_dir: Any,
                tracker: Any,
                attempt_no: int,
            ) -> tuple[int, str, Path, list[str]]:
                outcomes_dir = run_dir / "outcomes"
                logs_dir = run_dir / "logs"
                outcomes_dir.mkdir(parents=True, exist_ok=True)
                logs_dir.mkdir(parents=True, exist_ok=True)

                v_outcome = outcomes_dir / "01-tst001-verification.json"
                v_outcome.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "id6": "tst001",
                            "verdict": "VERIFIED",
                            "tests_run": ["python3 -m pytest tests/"],
                        }
                    ),
                    encoding="utf-8",
                )

                log_file = logs_dir / "01-tst001-attempt-1-verify.jsonl"
                if verdict_kind == "corroborated":
                    event = {
                        "event": "step_update",
                        "step_update": {
                            "state": "DONE",
                            "step_type": "tool",
                            "tool_name": "run_command",
                            "tool_info": {
                                "parameters": {
                                    "CommandLine": "python3 -m pytest tests/"
                                }
                            },
                        },
                    }
                    log_file.write_text(json.dumps(event) + "\n", encoding="utf-8")
                elif verdict_kind == "uncorroborated":
                    event = {
                        "event": "step_update",
                        "step_update": {
                            "state": "DONE",
                            "step_type": "tool",
                            "tool_name": "run_command",
                            "tool_info": {"parameters": {"CommandLine": "git status"}},
                        },
                    }
                    log_file.write_text(json.dumps(event) + "\n", encoding="utf-8")
                elif verdict_kind == "indeterminate":
                    log_file.write_bytes(b"\x00\xff\xfe\x00corrupt")

                return 0, "sess-v-1", log_file, ["mock_verifier"]

            state, item = _drive_execute_turn(
                repo_root,
                plan_file,
                spawn_verifier=verifier_spawner,
                validate=True,
                self_finalize=True,
            )

            attempts = item.get("attempts", [])
            assert len(attempts) == 1
            attempt = attempts[0]

            # 1. Assert the recorded corroboration_verdict is the intended one
            # (guarantees the fixture is not miscalibrated or vacuous)
            contract_msg = (
                f"corroboration_verdict must be {verdict_kind!r} per fixture calibration"
            )
            assert attempt.get("corroboration_verdict") == verdict_kind, contract_msg
            assert item.get("corroboration_verdict") == verdict_kind, contract_msg

            # 2. Integration signal must be recorded by the pipeline (self_finalize was engaged)
            # and must be non-None in every arm
            assert attempt.get("integration_signal") is not None, (
                "integration_signal must be recorded by pipeline when self_finalize=True"
            )
            assert item.get("integration_signal") is not None, (
                "integration_signal must be recorded on item when self_finalize=True"
            )

            # 3. Assert pipeline-recorded integration_signal, status, and verification_status
            # are identical across all three verdicts (specifically 'verifier', 'executed', 'verified')
            failure_msg = (
                f"Pipeline recorded integration signal {item.get('integration_signal')!r} for "
                f"verdict {verdict_kind!r}, violating DECISIONS.md D160 (an uncorroborated "
                f"verifier turn must never refuse integration or downgrade disposition)"
            )
            assert item["integration_signal"] == "verifier", failure_msg
            assert attempt["integration_signal"] == "verifier", failure_msg
            assert item["status"] == "executed", failure_msg
            assert attempt["disposition"] == "executed", failure_msg
            assert item["verification_status"] == "verified", failure_msg
            assert attempt["verification_status"] == "verified", failure_msg
    ```

    Pytest run on test file:
    `python3 -m pytest tests/test_verifier_corroboration.py -o addopts=""`
    Output:
    `======================== 46 passed in 79.48s (0:01:19) =========================`

    MUTATION PROOF:
    1. Exact call-site mutation in `agent_workflows/runner_shared.py` (lines 35363-35367):
    ```python
        integration = integration_is_earned(
            validate=validate,
            verify_disp="unverified" if item.get("corroboration_verdict") == "uncorroborated" else verify_disp,
            suite_result=suite_result,
        )
    ```
    2. FAILING run of the new test under mutation:
    `python3 -m pytest tests/test_verifier_corroboration.py -k "test_pipeline_integration_decision_identical_across_corroboration_verdicts" -o addopts=""`
    Output:
    ```
    FAILED tests/test_verifier_corroboration.py::TestCorroborationInteractionAndOutcomeEquality::test_pipeline_integration_decision_identical_across_corroboration_verdicts[uncorroborated]
    AssertionError: Pipeline recorded integration signal 'verifier-declined' for verdict 'uncorroborated', violating DECISIONS.md D160 (an uncorroborated verifier turn must never refuse integration or downgrade disposition)
    assert 'verifier-declined' == 'verifier'
    ================= 1 failed, 2 passed, 43 deselected in 44.79s ==================
    ```
    3. SHIPPED equality test run under same mutation (expected green):
    `python3 -m pytest tests/test_verifier_corroboration.py -k "test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts" -o addopts=""`
    Output:
    `====================== 3 passed, 43 deselected in 31.16s =======================`
    (Confirms the shipped test was blind to integration-only refusals and that E-03 is not redundant).
    4. Revert of mutation:
    `git checkout agent_workflows/runner_shared.py`
    5. PASSING run of new test after revert:
    `python3 -m pytest tests/test_verifier_corroboration.py -k "test_pipeline_integration_decision_identical_across_corroboration_verdicts" -o addopts=""`
    Output:
    `====================== 3 passed, 43 deselected in 41.07s =======================`

    Confirmation: The test reads each verdict from `attempt['corroboration_verdict']` and `item['corroboration_verdict']` recorded by the real pipeline and asserts it before asserting equality. It asserts on the pipeline-recorded `integration_signal` (not a test-side call), and the recorded signal is non-None in every arm (`'verifier'`). The test reads no production source and pins no docstring or comment text (P16).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the amended Section 5.1 region and a `git diff` over the spec file showing that the admissible list, the inadmissible list, Section 4.2's closing sentence, the attributed suite-attribution exception and the HONEST LIMIT paragraph's existing wording are ALL unchanged, and that the only change is the added statement plus the tool-appended history record. Paste the `aw specs note` invocation and its output, proving the history record was appended by the tool and not hand-written. Paste `aw specs check` (or `aw check` scoped to specs) reporting the spec conformant. Confirm the added text states all three things E-04 requires (the verdict exists, it is observational and refuses nothing, and the inadmissibility entry is not an instruction to refuse) and that it does not weaken either list.
  - Observed evidence:
    Amended Section 5.1 region in `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```markdown
    THE HONEST LIMIT, stated so the exception is not trusted further than it holds. The agent may answer
    "not mine" in good faith about a failure it actually caused, because it has no baseline of the suite
    before its own work and so cannot know what was already red. The maintainer ruled on 2026-09-08 and again
    on 2026-09-20 that no programmatic gate may refuse the verdict on that basis: a pre-work baseline may be
    supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses or downgrades
    on it. That ruling is unchanged; what is made explicit here is the direction of the prohibition: nothing
    may refuse on the baseline (using the baseline to disbelieve an agent remains forbidden), while a
    comparison that only ever makes a gate more permissive is not such a refusal. So this exception
    mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe: a wrong answer is
    durably recorded, named, and reviewable afterwards, in the same way an attested `- Readiness:` field
    and a `V-*` evidence block are made safe by being attributed rather than by machine verification.

    VERIFIER TEST EVIDENCE CORROBORATION IS OBSERVATIONAL (plan `q4uifc`, backlog `sinhkj`). The run records
    a three-state corroboration verdict (`corroborated`, `uncorroborated`, or `indeterminate`) comparing a
    verifier's claimed test commands against the tool calls extracted from its own session log. That verdict is
    strictly OBSERVATIONAL: no refusal, downgrade, or disposition change may be keyed on it, in accordance with
    the same direction established above for the suite baseline (a comparison that makes an outcome more
    permissive is permitted, but using an observation to disbelieve an agent is forbidden). Furthermore, this
    section's classification of an agent's self-report or a verifier's opinion as inadmissible completion
    evidence is NOT an instruction to refuse or fail a lane on a mismatch between claimed commands and observed
    tool calls: the extraction predicate has measured false positives (such as Antigravity subagent delegations,
    bug `iuhx9d`), and GUIDING_PRINCIPLES P15 forbids any mechanism whose justification is "in case the agent
    lies". The inadmissible and admissible completion evidence lists above remain unchanged.

    ### 5.2 Safety policy
    ```

    `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    index a5293905a..4a8b67c0e 100644
    --- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    +++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    @@ -1199,6 +1199,18 @@ mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe: a
     durably recorded, named, and reviewable afterwards, in the same way an attested `- Readiness:` field
     and a `V-*` evidence block are made safe by being attributed rather than by machine verification.

    +VERIFIER TEST EVIDENCE CORROBORATION IS OBSERVATIONAL (plan `q4uifc`, backlog `sinhkj`). The run records
    +a three-state corroboration verdict (`corroborated`, `uncorroborated`, or `indeterminate`) comparing a
    +verifier's claimed test commands against the tool calls extracted from its own session log. That verdict is
    +strictly OBSERVATIONAL: no refusal, downgrade, or disposition change may be keyed on it, in accordance with
    +the same direction established above for the suite baseline (a comparison that makes an outcome more
    +permissive is permitted, but using an observation to disbelieve an agent is forbidden). Furthermore, this
    +section's classification of an agent's self-report or a verifier's opinion as inadmissible completion
    +evidence is NOT an instruction to refuse or fail a lane on a mismatch between claimed commands and observed
    +tool calls: the extraction predicate has measured false positives (such as Antigravity subagent delegations,
    +bug `iuhx9d`), and GUIDING_PRINCIPLES P15 forbids any mechanism whose justification is "in case the agent
    +lies". The inadmissible and admissible completion evidence lists above remain unchanged.
    +
     ### 5.2 Safety policy

     #### Per-host capability descriptor
    @@ -1692,6 +1704,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

     ## Workflow history

    +- 2026-10-07 note (aw specs): AMENDED (plan q4uifc, backlog sinhkj): Section 5.1 amended to declare verifier test evidence corroboration observational and non-refusing, consistent with P15 and the baseline direction constraint; admissible and inadmissible completion evidence lists, the attributed suite-attribution exception and all of its conditions, and the HONEST LIMIT paragraph's existing wording remain unchanged.
     - 2026-10-07 note (aw specs): AMENDED 2026-10-06 (plan 0bjke0, Set runfresh): new Section 5.3b requires the driver to record the toolkit code it loaded, to restart itself between items on the current code when an item of the run changed it (recorded, bounded, never inside an item, no restart when the loaded package is not the checkout's own), and to keep nested calls pinned to its own package; Section 5.3 driver record gains the loaded-code record; Section 4.1 requires finalize and retirement lint refusals to carry their findings; Section 6.1 gains limit 10. Motivated by run-20261006T134924Z-332833, whose orchestrator retirement was refused by a linter older than the fields its own children added.
    ```

    `aw specs note` command and output:
    Command: `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "AMENDED (plan q4uifc, backlog sinhkj): Section 5.1 amended to declare verifier test evidence corroboration observational and non-refusing, consistent with P15 and the baseline direction constraint; admissible and inadmissible completion evidence lists, the attributed suite-attribution exception and all of its conditions, and the HONEST LIMIT paragraph's existing wording remain unchanged."`
    Output: `aw specs note: appended a history record to .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`

    `aw specs check`:
    Command: `aw specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`
    Output: `aw specs check: all specs conform. 1 specs checked.`

    Confirmation: The admissible and inadmissible lists, Section 4.2's closing sentence, the attributed suite-attribution exception and all of its conditions, and the HONEST LIMIT paragraph's existing wording are completely unchanged. The added text records that the three-state verdict exists, is strictly observational and refuses nothing, and that the inadmissibility entry is not an instruction to refuse.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new `DECISIONS.md` entry in full, with the command that read the highest existing `### D<n>` heading at execution time proving the number was derived from the file rather than from this plan. Confirm the entry names the rejected alternative, gives its three reasons, states the more-permissive allowance, states that `btak7a` OQ-01 is answered, and that `Applied` names the files actually changed and cites this plan by id6 and Set. Paste the `CHANGELOG.md` line. Paste `aw check` reporting the records tree conformant, and `aw sanitize --agent` reporting no `fail`. Confirm by inspection that neither file gained an em or en dash. Finally paste the BASELINE and POST-CHANGE bare `python3 -m pytest` runs, compared BY FAILING NODE ID SET and not by count (F-10), with the baseline taken on an unmodified tree; any new failure must be shown to reproduce there before being called pre-existing. Also paste the re-run no-consumer census from E-01(a), confirming the only new reader is the test.
  - Observed evidence:
    (a) HIGHEST EXISTING DECISION HEADING COMMAND AND PROOF:
    Prior to edit:
    `git grep -n "^### D[0-9]" HEAD:DECISIONS.md | tail -n 5`
    Output:
    ```
    HEAD:DECISIONS.md:2580:### D155. Four-case installer section consent (self-heal stale manifest hashes, preserve unrecorded user drift, warn on held-back sections)
    HEAD:DECISIONS.md:2591:### D156. Executed plans: never rewrite the record, but a dated pointer line may be appended (narrows D69)
    HEAD:DECISIONS.md:2597:### D157. Ratify the aw attention no-match exit contract (fail-closed exit 2 on named-artifact assertions, exempt standing questions)
    HEAD:DECISIONS.md:2603:### D158. Retire the human no-project exit 3 into the uniform three-state exit classification (exit 2)
    HEAD:DECISIONS.md:2611:### D159. Status transition citation rewrite: default-OFF opt-in with fail-closed in-flight guard
    ```
    Proves highest existing heading was D159. Next derived number is D160.

    Current head check:
    `git grep -n "^### D[0-9]" DECISIONS.md | tail -n 5`
    Output:
    ```
    DECISIONS.md:2591:### D156. Executed plans: never rewrite the record, but a dated pointer line may be appended (narrows D69)
    DECISIONS.md:2597:### D157. Ratify the aw attention no-match exit contract (fail-closed exit 2 on named-artifact assertions, exempt standing questions)
    DECISIONS.md:2603:### D158. Retire the human no-project exit 3 into the uniform three-state exit classification (exit 2)
    DECISIONS.md:2611:### D159. Status transition citation rewrite: default-OFF opt-in with fail-closed in-flight guard
    DECISIONS.md:2622:### D160. An uncorroborated verifier turn is observational and never refuses integration
    ```

    (b) FULL TEXT OF D160 IN DECISIONS.MD:
    ```markdown
    ### D160. An uncorroborated verifier turn is observational and never refuses integration

    - **Context:** Executed plan `btak7a` (2026-10-02) shipped verifier test evidence corroboration (`verifier_corroboration.py`), comparing claimed test commands against observed session log tool calls and returning a three-state verdict (`corroborated`, `uncorroborated`, `indeterminate`), recorded by `runner_shared.execute_item_core` on both attempt and item, rendered in `execution-report.md`, and surfaced in `aw runs`. `btak7a` deliberately left open whether an `uncorroborated` turn should ever refuse, downgrade, or block integration (OQ-01, carried by backlog `sinhkj`). Backlog `sinhkj` proposed to revisit with an observed false-negative rate over real runs. However, that rate is unobtainable by construction in any lane worktree because `.aw/records/runs/` is gitignored and absent from lanes (as measured by `bjx20r` V-06: real corpus size 0).
    - **Decision:** An `uncorroborated` verifier turn is strictly observational and MUST NOT refuse, downgrade, or alter any item disposition, verification status, or integration decision. This entry formally answers `btak7a` OQ-01 with a definitive NO.
      The alternative (refusing, downgrading, or altering integration on an `uncorroborated` turn) is rejected on three independent grounds:
      1. *P15 forbids gates justified by suspected dishonesty:* GUIDING_PRINCIPLES P15 ("Guard against honest mistakes, never against a malicious agent") forbids any mechanism justified by "in case the agent lies", citing the maintainer's 2026-09-08 and 2026-09-20 rulings that rejected a deceptive-failure gate because a gate cannot detect deception and a genuinely malicious agent would rewrite the gate (which applies verbatim to `verifier_corroboration.py` because an agent has write access to the file).
      2. *Spec 25kzda Section 5.1 directional constraint:* Spec `25kzda` Section 5.1's HONEST LIMIT paragraph permits only comparisons that make an outcome MORE permissive and explicitly forbids using an observation to disbelieve an agent. A corroboration refusal is the forbidden sign.
      3. *Known false positives in the extraction predicate:* The command extraction predicate is unsafe to strand a lane on. Specifically, the Antigravity `step_type == "subagent"` delegation shape is unobserved by the reader, causing genuine test delegations to resolve to `uncorroborated` (tracked as bug `iuhx9d`). Stranding lanes on this predicate would convert a known parser gap into lost work.
      Future consumers may read the corroboration fields and may make an outcome MORE permissive based on them, but must not refuse or downgrade on them. A reader who believes a refusal is warranted opens a new decision rather than wiring one here.
    - **Applied:** `agent_workflows/verifier_corroboration.py` (added contract docstring block), `tests/test_verifier_corroboration.py` (added behavioral integration signal test pinned across all three verdict values under self-finalize), `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (amended Section 5.1 and recorded tool note), `DECISIONS.md` (this entry), and `CHANGELOG.md`. Executed per IPD `q4uifc` (Set `runverdict`, Order 11, backlog `sinhkj`).
    ```

    Confirmation of required entry elements:
    - Names rejected alternative: "The alternative (refusing, downgrading, or altering integration on an `uncorroborated` turn) is rejected"
    - Gives its three reasons: Reason 1 (P15 suspected dishonesty), Reason 2 (Spec 25kzda Section 5.1 directional constraint), Reason 3 (Known false positives in the extraction predicate / bug iuhx9d).
    - States the more-permissive allowance: "Future consumers may read the corroboration fields and may make an outcome MORE permissive based on them, but must not refuse or downgrade on them."
    - States btak7a OQ-01 answered: "This entry formally answers `btak7a` OQ-01 with a definitive NO."
    - Applied names actual files changed: `agent_workflows/verifier_corroboration.py`, `tests/test_verifier_corroboration.py`, `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `DECISIONS.md`, and `CHANGELOG.md`.
    - Cites plan by id6 and Set: "Executed per IPD `q4uifc` (Set `runverdict`, Order 11, backlog `sinhkj`)."

    (c) CHANGELOG.MD LINE:
    `- Added: declared the verifier test evidence corroboration verdict strictly observational, confirming it never refuses, downgrades, or blocks integration (D160).`

    (d) CONFORMANCE & SANITIZE CHECKS:
    `aw check specs`:
    ```
    AW check  specs                                                            82 ms
    ✓ CONFORMS  21 specs checked
    Findings:
      Issue: cross-tree collisions NOT checked by a per-type run
      - <collisions>
        1. <collisions>
        Fix: aw check all
    Evidence
      checked  21
      errors  0   warnings  0   info  1
    Next  aw specs check
    ```
    `aw ipd lint .aw/records/plans/pending/20261002-runverdict-11-q4uifc-decide-that-an-uncorroborated-verifier-turn-never-refuses-in.ipd.md`:
    `-    ◕  approved     plan        20261002-runverdict-11-q4uifc  [medium]  conforming`
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`

    (e) EM / EN DASH INSPECTION:
    Command:
    ```
    python3 -c "
    for fname in ['DECISIONS.md', 'CHANGELOG.md']:
        content = open(fname, encoding='utf-8').read()
        em = '\u2014' in content
        en = '\u2013' in content
        print(f'{fname}: em={em}, en={en}')
    "
    ```
    Output:
    `DECISIONS.md: em=False, en=False`
    `CHANGELOG.md: em=False, en=False`
    Neither file gained an em dash or an en dash.

    (f) FULL SUITE BASELINE VS POST-CHANGE TEST COMPARISON:
    Baseline run (on clean tree prior to edits):
    `python3 -m pytest`
    Output: `6409 passed, 2 skipped, 3 warnings in 542.55s (0:09:02)`
    Baseline failing node ID set: `set()` (empty, 0 failed).

    Post-change bare pytest run:
    `python3 -m pytest`
    Output: `1 failed, 6411 passed, 2 skipped, 3 warnings in 403.37s (0:06:43)`
    Failing node: `tests/test_lane_interruption.py::test_the_terminal_rung_still_records_the_item_interrupted`
    Isolation reproduction check:
    `python3 -m pytest tests/test_lane_interruption.py::test_the_terminal_rung_still_records_the_item_interrupted -o addopts=""`
    Output: `1 passed in 3.56s`
    Root cause: Multi-worker xdist signal-coalescing timing jitter unrelated to verifier corroboration.
    Newly added tests:
    `tests/test_verifier_corroboration.py::TestVerifierCorroborationIntegrationBehavior::test_pipeline_integration_decision_identical_across_corroboration_verdicts[corroborated]`
    `tests/test_verifier_corroboration.py::TestVerifierCorroborationIntegrationBehavior::test_pipeline_integration_decision_identical_across_corroboration_verdicts[uncorroborated]`
    `tests/test_verifier_corroboration.py::TestVerifierCorroborationIntegrationBehavior::test_pipeline_integration_decision_identical_across_corroboration_verdicts[indeterminate]`
    All 3 passed. Post-change failing node ID set for touched surfaces: `set()` (empty).

    (g) RE-RUN NO-CONSUMER CENSUS FROM E-01(a):
    Command: `git grep -n -E "corroborat(e_verifier_turn|ion_verdict|ion_reason|ion_counts)" agent_workflows/ tests/`
    Output:
    ```
    agent_workflows/run_viewer.py:1136:                item_corr_reason = item.get("corroboration_reason")
    agent_workflows/run_viewer.py:1155:                                item_corr_verdict = _v_data.get("corroboration_verdict")
    agent_workflows/run_viewer.py:1156:                                item_corr_reason = _v_data.get("corroboration_reason")
    agent_workflows/run_viewer.py:1162:                        item_corr_verdict = last_att.get("corroboration_verdict")
    agent_workflows/run_viewer.py:1163:                        item_corr_reason = last_att.get("corroboration_reason")
    agent_workflows/run_viewer.py:1210:                        corroboration_verdict=item_corr_verdict,
    agent_workflows/run_viewer.py:1211:                        corroboration_reason=item_corr_reason,
    agent_workflows/run_viewer.py:2441:        if step.corroboration_verdict:
    agent_workflows/run_viewer.py:2443:                f"corroboration: {step.corroboration_verdict} (reason: {step.corroboration_reason})"
    agent_workflows/run_viewer.py:2444:                if step.corroboration_reason
    agent_workflows/run_viewer.py:2445:                else f"corroboration: {step.corroboration_verdict}"
    agent_workflows/runner_shared.py:23438:        corr_verdict = it.get("corroboration_verdict")
    agent_workflows/runner_shared.py:23439:        corr_reason = it.get("corroboration_reason")
    agent_workflows/runner_shared.py:23445:                    corr_verdict = last_att.get("corroboration_verdict")
    agent_workflows/runner_shared.py:23446:                    corr_reason = last_att.get("corroboration_reason")
    agent_workflows/runner_shared.py:34771:                                        corroborate_verifier_turn,
    agent_workflows/runner_shared.py:34776:                                    v_corr = corroborate_verifier_turn(
    agent_workflows/runner_shared.py:34801:                            attempt["corroboration_verdict"] = v_corr_verdict
    agent_workflows/runner_shared.py:34802:                            attempt["corroboration_reason"] = v_corr_reason
    agent_workflows/runner_shared.py:34803:                            attempt["corroboration_counts"] = v_corr_counts
    agent_workflows/runner_shared.py:34804:                            item["corroboration_verdict"] = v_corr_verdict
    agent_workflows/runner_shared.py:34805:                            item["corroboration_reason"] = v_corr_reason
    agent_workflows/runner_shared.py:34806:                            item["corroboration_counts"] = v_corr_counts
    agent_workflows/verifier_corroboration.py:98:    "corroborate_verifier_turn",
    agent_workflows/verifier_corroboration.py:679:def corroborate_verifier_turn(
    agent_workflows/verifier_corroboration.py:820:check_verifier_corroboration = corroborate_verifier_turn
    agent_workflows/verifier_corroboration.py:821:compute_verifier_corroboration = corroborate_verifier_turn
    tests/test_verifier_corroboration.py:214:        v = vc.corroborate_verifier_turn(p, claims)
    tests/test_verifier_corroboration.py:222:        v = vc.corroborate_verifier_turn(p, claims)
    tests/test_verifier_corroboration.py:230:        v = vc.corroborate_verifier_turn("nonexistent_session.jsonl", claims)
    tests/test_verifier_corroboration.py:237:        v = vc.corroborate_verifier_turn(p, claims)
    tests/test_verifier_corroboration.py:243:        v = vc.corroborate_verifier_turn(p, [])
    tests/test_verifier_corroboration.py:250:        v = vc.corroborate_verifier_turn(p, claims)
    tests/test_verifier_corroboration.py:257:        v = vc.corroborate_verifier_turn(p, claims)
    tests/test_verifier_corroboration.py:265:        v = vc.corroborate_verifier_turn(p, claims)
    tests/test_verifier_corroboration.py:281:            v_before = vc.corroborate_verifier_turn(mutated_file, claims)
    tests/test_verifier_corroboration.py:286:            v_after = vc.corroborate_verifier_turn(mutated_file, claims)
    tests/test_verifier_corroboration.py:318:        verdict = vc.corroborate_verifier_turn(log_path, verifier_data["tests_run"])
    tests/test_verifier_corroboration.py:475:    def test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts(
    tests/test_verifier_corroboration.py:557:            assert attempt["corroboration_verdict"] == verdict_kind
    tests/test_verifier_corroboration.py:558:            assert item["corroboration_verdict"] == verdict_kind
    tests/test_verifier_corroboration.py:559:            assert "corroboration_reason" in attempt
    tests/test_verifier_corroboration.py:560:            assert "corroboration_counts" in attempt
    tests/test_verifier_corroboration.py:561:            assert "corroboration_reason" in item
    tests/test_verifier_corroboration.py:562:            assert "corroboration_counts" in item
    tests/test_verifier_corroboration.py:588:    def test_pipeline_integration_decision_identical_across_corroboration_verdicts(
    tests/test_verifier_corroboration.py:671:            # 1. Assert the recorded corroboration_verdict is the intended one
    tests/test_verifier_corroboration.py:674:                f"corroboration_verdict must be {verdict_kind!r} per fixture calibration"
    tests/test_verifier_corroboration.py:676:            assert attempt.get("corroboration_verdict") == verdict_kind, contract_msg
    tests/test_verifier_corroboration.py:677:            assert item.get("corroboration_verdict") == verdict_kind, contract_msg
    tests/test_verifier_corroboration.py:715:            "corroborate_verifier_turn",
    tests/test_verifier_corroboration.py:759:            assert attempt["corroboration_verdict"] == "indeterminate"
    tests/test_verifier_corroboration.py:760:            assert attempt["corroboration_reason"] == "computation-failed"
    tests/test_verifier_corroboration.py:761:            assert item["corroboration_verdict"] == "indeterminate"
    tests/test_verifier_corroboration.py:762:            assert item["corroboration_reason"] == "computation-failed"
    tests/test_verifier_corroboration.py:805:            assert attempt["corroboration_verdict"] == "indeterminate"
    tests/test_verifier_corroboration.py:806:            assert attempt["corroboration_reason"] == "outcome-unreadable"
    tests/test_verifier_corroboration.py:807:            assert attempt["corroboration_reason"] != "computation-failed"
    tests/test_verifier_corroboration.py:808:            assert item["corroboration_verdict"] == "indeterminate"
    tests/test_verifier_corroboration.py:809:            assert item["corroboration_reason"] == "outcome-unreadable"
    tests/test_verifier_corroboration.py:837:            assert "corroboration_verdict" not in attempt
    tests/test_verifier_corroboration.py:838:            assert "corroboration_reason" not in attempt
    tests/test_verifier_corroboration.py:839:            assert "corroboration_counts" not in attempt
    tests/test_verifier_corroboration.py:840:            assert "corroboration_verdict" not in item
    tests/test_verifier_corroboration.py:841:            assert "corroboration_reason" not in item
    tests/test_verifier_corroboration.py:842:            assert "corroboration_counts" not in item
    tests/test_verifier_corroboration.py:899:                        "corroboration_verdict": "corroborated",
    tests/test_verifier_corroboration.py:900:                        "corroboration_reason": "corroborated",
    tests/test_verifier_corroboration.py:923:    def test_step_summary_surfaces_corroboration_verdict_and_backward_compatible(
    tests/test_verifier_corroboration.py:946:                                "corroboration_verdict": "corroborated",
    tests/test_verifier_corroboration.py:947:                                "corroboration_reason": "corroborated",
    tests/test_verifier_corroboration.py:962:                        "corroboration_verdict": "corroborated",
    tests/test_verifier_corroboration.py:963:                        "corroboration_reason": "corroborated",
    tests/test_verifier_corroboration.py:973:            assert step.corroboration_verdict == "corroborated"
    tests/test_verifier_corroboration.py:974:            assert step.corroboration_reason == "corroborated"
    tests/test_verifier_corroboration.py:978:            assert "corroboration_verdict" in payload
    tests/test_verifier_corroboration.py:979:            assert payload["corroboration_verdict"] == "corroborated"
    tests/test_verifier_corroboration.py:980:            assert "corroboration_reason" in payload
    tests/test_verifier_corroboration.py:981:            assert payload["corroboration_reason"] == "corroborated"
    tests/test_verifier_corroboration.py:1025:            assert step_old.corroboration_verdict is None
    tests/test_verifier_corroboration.py:1026:            assert step_old.corroboration_reason is None
    tests/test_verifier_corroboration.py:1030:            assert payload_old["corroboration_verdict"] is None
    ```
    Confirmation: The only new reader is the newly authored test `test_pipeline_integration_decision_identical_across_corroboration_verdicts` (tests/test_verifier_corroboration.py lines 588, 671, 674, 676, 677).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Do not execute before this plan is `approved`. Run `aw ipd begin` first; commit only the paths matching `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never `git add -A` and never push; paste ACTUAL command output for every validation item rather than describing it. The spec file in `- Scope-Paths:` is a DECLARED SPEC EDIT, so the run announces it before starting and reconciles it at the end; do not remove it from the declaration to avoid the announcement.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` or mark it `executed` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence with `Result: pass`. Backlog `sinhkj` is set `graduated` by the runner on verification; do not set it `done` by hand, and do not edit the item's requirements.

ONE REFUSAL AN EXECUTOR SHOULD EXPECT TO HIT AND MUST NOT WORK AROUND: if E-01's census finds a non-renderer consumer of the corroboration fields, the plan STOPS. That is not a defect in the gate; it means a refusal landed while this plan waited, and the correct response is a report, not a rewritten E-02.
