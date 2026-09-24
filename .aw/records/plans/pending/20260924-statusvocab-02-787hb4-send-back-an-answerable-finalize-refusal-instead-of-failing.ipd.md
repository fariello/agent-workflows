# IPD: Send back an answerable finalize refusal instead of failing the item

- Date: 2026-09-24
- Kind: child
- Concern: A FINALIZE REFUSAL THE AGENT COULD ANSWER IN ONE TURN COSTS THE RUN AN ITEM AND EVERY ITEM BEHIND IT. Measured on run `run-20260924T050407Z-3108751`: `xdvglg` performed all 6 of its E-items and all 6 of its V-items, its work was correct, and it was recorded `substantially-complete` with nothing in `main` because `aw ipd finalize` refused on two findings - a STALE begin receipt and one `Scope-Paths` entry removed without a recorded reason. Both are answerable by the agent that was still running: the removed path pointed at `tests/test_rununify_initialize_run_characterization.py`, which commit `7ebc2964` DELETED FROM `main` on 2026-09-17, one day BEFORE the `/plan-review` round that declared it, so the plan was fenced to a file that could not be edited because it did not exist. The refusal was CORRECT and the response was disproportionate: `04vf1h` and `a5wdne` then cascaded `dependency-blocked` behind it, and a human (this session) resolved it by re-issuing `begin` and writing one paragraph. THE SEND-BACK MACHINERY ALREADY EXISTS AND ALREADY EXCLUDES THESE TWO CASES ON PURPOSE: `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` lists exactly three pre-transition E/V texts, and the module's own note records why the other classes are excluded - a stale receipt is spec `25kzda` 5.5's "changed frozen requirements" and an out-of-scope mutation is "the FIRST entry on its never-retry list". That reasoning is sound for an agent that WIDENED its fence without authority. It is wrong for a REDUCTION that removes a citation to a file `main` deleted, which is the same class of stale-citation defect this repository has hit repeatedly.
- Scope: Move the two ANSWERABLE finalize-refusal classes onto the existing send-back path so the agent is asked rather than the item failed, keeping every unanswerable class exactly as it is. The test that decides is NOT "did a frozen requirement change" but "can the agent answer this in one bounded turn": a `Scope-Paths` REDUCTION and a STALE RECEIPT are answerable (justify or revert); an out-of-scope MUTATION that widened the fence without authority is not, and stays terminal. Reuses `RETRYABLE_FINALIZE_FINDING_TEXTS`, the `finalize_refused` prior-attempt key, and the frozen retry budget; adds no new packet format and no new prompt channel. IN: the retryable-finding predicate, the send-back dispatch decision, and the tests that pin both. OUT: changing what `aw ipd finalize` itself checks or refuses (Order 01 and this plan both leave the gate's own logic alone), widening the retry BUDGET, and any change to the digest's frozen region.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, tests/test_finalize_sendback.py, tests/test_finidem_double_finalize.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: reviewed
- Set: statusvocab
- Order: 2
- Highest E allocated: 03
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Readiness: go-pending-approval
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 787hb4

## Workflow history
- 2026-09-24 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED, none deferred, none open; readiness `go-pending-approval`. Record: `.aw/records/reviews/20260924-statusvocab-02-787hb4-send-back-an-answerable-finalize-refusal-instead-of-failing.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after, so nothing found was structural. DISCLOSURE: same agent and model authored this plan, so this is a SELF-REVIEW, and its value came from CALLING the predicate rather than re-reading the plan. THE DIAGNOSIS HOLDS: `xdvglg` is in `executed/` (a human finished it by hand), `04vf1h` is in `executed/`, `a5wdne` is still `pending/`, and the send-back machinery exists exactly as described. THE MECHANISM DID NOT. PR-001 (BLOCKER): E-02 said to "extend the retryable set", and `finalize_refusal_is_retryable` is not a list lookup but a conjunction scoped to ONE class - it short-circuits unless `RETRYABLE_FINALIZE_SUMMARY` appears, then locates findings by the `IPD-` prefix. The stale refusal's summary is a different sentence and NEITHER of its findings carries that prefix, so the authored change would have added two unreachable strings, passed its own expected outcome, and shipped zero behavior change while claiming the defect fixed. Measured by calling the shipped predicate on the shipped `STALE_RECEIPT_REFUSAL` fixture: False, and still False with the allowlist extended. E-02 is now a per-class-arm restructuring that dispatches on summary first and PRESERVES the every-finding conjunction within each arm, so a mixed stale-plus-rewrite message still refuses. PR-002: V-01 demanded `test_a_STALE_begin_receipt_is_NOT_retryable` keep passing, which is an `assertFalse` on the exact behavior E-02 inverts, so satisfying V-01 required E-02 to have failed; V-01 now pins the unchanged FIXTURE and the gate names which tests to rewrite versus preserve. PR-003: the reduction finding is COMPOSED with a singular/plural stem, so E-01 had no single string to name and a multi-path reduction would not have matched. PR-004: V-02 drove three refusals and omitted the missing-receipt and scope-reconciliation classes, which a too-loose new arm could newly admit; now five refusals plus a mixed message. PR-005: the gate was one sentence. Four decisions recorded (D-1 repair rather than REPLAN since diagnosis and structure survive, D-2 no spec amendment because none is declared and Order 03 owns spec edits, D-3 `runner_shared.py` overlap with Order 01 is not a hazard since items are worktree-isolated, D-4 the gitignored run directory is absent and its claims were corroborated by proxy). OQ-01 stays open at `Blocking: no`. NOTE FOR APPROVAL: this is a POLICY change that makes two terminal classes retryable, and if the maintainer reads it as contradicting spec `25kzda` 5.5 rather than refining it, the work needs a plan that declares the spec path.
- 2026-09-24 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-001..PR-005 all FIXED, none deferred, none open. PR-001 (BLOCKER): the plan's central mechanism could not have worked. finalize_refusal_is_retryable is a conjunction scoped to ONE class, not a list lookup: it short-circuits unless RETRYABLE_FINALIZE_SUMMARY is present, then locates findings by the IPD- prefix. The stale refusal carries a different summary and its findings have no IPD- prefix, so extending RETRYABLE_FINALIZE_FINDING_TEXTS adds unreachable strings. Measured by calling the shipped predicate on the shipped STALE_RECEIPT_REFUSAL fixture: False before and after. E-02 is now a per-class-arm restructuring preserving the every-finding conjunction within each arm. PR-002: V-01 demanded a test keep passing that asserts the exact behavior E-02 inverts. PR-003: the reduction finding is composed with a singular/plural stem, so there is no single string to name. PR-004: V-02 omitted the missing-receipt and scope-reconciliation classes that must stay terminal. PR-005: the gate was one sentence. Record: .aw/records/reviews/20260924-statusvocab-02-787hb4-send-back-an-answerable-finalize-refusal-instead-of-failing.review.md. Readiness go-pending-approval.
- 2026-09-24 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored as part of splitting the oversized cyamvi plan into a Set on maintainer instruction; complete enough to critique.

- 2026-09-24 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the runner ASK when the answer is one turn away. A refusal an agent can resolve should cost a turn, not an item plus everything behind it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: widen the retryable set by the answerability test

- [ ] E-01 SEPARATE THE TWO SCOPE FINDINGS, because today they are one refusal branch and only one of them is answerable. `ipd_lifecycle`'s stale branch emits a REDUCTION finding ("Scope-Paths entry REMOVED since begin (a contract reduction, never accepted as a widening)") and a REWRITE finding ("gained X but a frozen REQUIREMENT also changed") from the same code path. Give the caller a distinct finding id for the REDUCTION case, following the precedent the module already set for `FINDING_RECEIPT_STALE`: NAME the shipped string rather than mint a new one, so no emitted byte changes. The precedent is verified and its reasoning is recorded at that constant, which is a SENTENCE rather than a token like its two `receipt-*` siblings precisely so the stale branch's emitted findings stay identical. NOTE THE REDUCTION SENTENCE IS COMPOSED, NOT CONSTANT: the branch builds it with a singular/plural stem (`"Scope-Paths entr" + ("ies" if len(removed) > 1 else "y")`) and appends the removed paths, so the id E-01 introduces must name the INVARIANT PREFIX both spellings share and must not assume one fixed string. Pin both the singular and plural spellings against it.
  - Depends on: none
  - Expected outcome: a caller can branch on reduction-versus-rewrite without matching refusal prose; emitted findings byte-identical to HEAD, with both the singular and plural reduction spellings matching the new id.
  - Execution state: pending

- [ ] E-02 ADMIT THE TWO ANSWERABLE CLASSES BY RESTRUCTURING THE PREDICATE INTO PER-CLASS ARMS, NOT BY EXTENDING ONE LIST. Record at the predicate WHY the admission test is "answerable in one bounded turn" rather than spec 5.5's "changed frozen requirements": the measured `xdvglg` case changed a frozen requirement AND was answerable, so the spec's category does not discriminate the cases the runner actually meets. The recovery prompt already interpolates `finalize_refused` through `prior_attempt_summary`, so the agent receives the gate's exact findings with no new format.

  THE AUTHORED APPROACH CANNOT WORK AND THE REASON IS STRUCTURAL (corrected at review, PR-001; measured, not reasoned). `finalize_refusal_is_retryable` is a TWO-PART conjunction over ONE class: it returns False unless `RETRYABLE_FINALIZE_SUMMARY` (`"pre-transition gate did NOT conform"`) appears in the message, and only then reads finding lines, which it locates by the `IPD-` prefix. Both halves exclude the two new classes before any allowlist is consulted:
    * the STALE refusal's summary is `"the begin receipt for <id> is STALE: the plan content changed since begin; re-run \`aw ipd begin\`."`, which does not contain the required summary, so the function short-circuits at the second `if`;
    * the stale branch's findings are `FINDING_RECEIPT_STALE` (`"plan content digest no longer matches the receipt"`) and the REDUCTION sentence, NEITHER of which starts with `IPD-`, so `finding_lines` is EMPTY and the "refuse to guess" branch returns False even if the summary matched.
  Verified by calling the shipped predicate on the shipped fixture: `finalize_refusal_is_retryable(STALE_RECEIPT_REFUSAL)` is False, and stays False with the finding text added to `RETRYABLE_FINALIZE_FINDING_TEXTS`, because control never reaches that comparison.

  SO THE DELIVERABLE IS A PREDICATE THAT DISPATCHES ON SUMMARY FIRST, THEN APPLIES THAT CLASS'S OWN RULE. Keep the existing pre-transition arm EXACTLY as it is (same summary, same `IPD-`-prefixed allowlist, same every-finding-must-match conjunction, same fail-closed defaults), and add one arm per newly answerable class, each keyed on its own summary and its own finding ids from E-01. PRESERVE THE EVERY-FINDING CONJUNCTION WITHIN EACH ARM: the stale arm must admit a message whose findings are the stale id ALONE or the stale id PLUS the reduction id, and must REFUSE one that also carries the rewrite/widening finding, since that is the mixed-message case the existing `test_a_MIXED_message_is_NOT_retryable` exists to prevent and it is exactly how a never-retry class would ride along. Branch on the E-01 finding ids, never on refusal prose beyond the summary token each arm is keyed to.
  - Depends on: E-01
  - Expected outcome: a stale-receipt or scope-reduction refusal re-dispatches the same item in recovery mode while budget remains, and FAILS the item when budget is exhausted; a fence-widening mutation, a MISSING receipt, and a scope-reconciliation (out-of-scope mutation) refusal are all still terminal on the first refusal; the pre-transition arm's behavior is byte-for-byte unchanged.
  - Execution state: pending

- [ ] E-03 PROVE THE SEND-BACK CANNOT LOOP OR LAUNDER A REFUSAL, which is the risk this plan introduces and must bound. The budget is already frozen and already counted (`send_back_retries_consumed`), so the loop terminates; what needs pinning is that an item exhausting its budget on a stale receipt ends TERMINAL and is never reported as success, and that a second identical refusal does not reset the counter. Assert against the recorded state, not against a flag.
  - Depends on: E-02
  - Expected outcome: budget exhaustion yields a terminal item with the gate's findings preserved; no path reaches a success state through a send-back.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SEND-BACK IS BUILT AND MUST NOT BE REINVENTED. `runner_shared` records: "`finalize_refused` is already an allowlisted prior-attempt key (`lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`) and `prior_attempt_summary` is already interpolated into the recovery prompt", so "this section only sets the flag". This plan adds findings to a predicate; it adds no channel.
- THE TRIGGER IS MATCHED ON PROSE, DELIBERATELY, and the reason is recorded: `IPD-S404` is the code for EVERY checkpoint diagnostic, and `finalize_precheck` returns the same `(1, message)` shape for a missing receipt, a stale receipt and a scope refusal, while the driver keeps only exit code plus combined output, so "the structure is lost at the subprocess boundary". The strings are pinned by a test so a wording change breaks loudly. E-01 follows that constraint rather than fighting it.
- A RENAME OR RE-ID IN THIS MODULE NAMES THE SHIPPED STRING INSTEAD OF REPLACING IT. `FINDING_RECEIPT_STALE` is "a sentence rather than a token like its two siblings" precisely so the stale branch's behavior stays unchanged and its existing pin keeps holding. E-01 is the same move for the reduction finding.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-01 THE MEASURED CASE WAS ANSWERABLE AND WAS FAILED. `xdvglg`: 6/6 E-items, 6/6 V-items, work correct, refused on a stale receipt plus one removed scope path, recorded `substantially-complete`, nothing in `main`, two siblings cascaded `dependency-blocked`. Resolved by hand with one `aw ipd begin` and one recorded paragraph. The cost of the current response is therefore measurable and the cost of the send-back is one turn.
- F-02 THE REMOVED PATH WAS A STALE CITATION, NOT A RE-FENCING. `tests/test_rununify_initialize_run_characterization.py` was deleted from `main` by `7ebc2964` on 2026-09-17; the `/plan-review` round that declared it as a ninth affected path ran 2026-09-18. The plan was fenced to a file that did not exist, so the reduction was the only correct action available to the executing agent, and the gate refused it for lacking an explanation the agent was never asked for.
- F-03 THE EXISTING EXCLUSION IS REASONED, WHICH IS WHY THIS PLAN NARROWS IT RATHER THAN DELETING IT. The module states a trigger keyed on the finding CODE or the exit status "would retry two classes the spec explicitly forbids retrying". That remains true of the fence-WIDENING class, which this plan leaves terminal. Only the reduction and the stale receipt move, and each moves with its own finding id from E-01.
- F-05 THE PREDICATE IS A ONE-CLASS CONJUNCTION, NOT A LIST, AND THIS PLAN'S ORIGINAL APPROACH COULD NOT HAVE WORKED (added at review, PR-001). `finalize_refusal_is_retryable` gates on `RETRYABLE_FINALIZE_SUMMARY` BEFORE reading any finding, and then locates findings by the `IPD-` prefix. The stale branch's summary is a different sentence and its findings carry no `IPD-` prefix, so extending `RETRYABLE_FINALIZE_FINDING_TEXTS` alone leaves the function returning False with the new entries never compared. Measured by calling the shipped predicate on the shipped `STALE_RECEIPT_REFUSAL` fixture. E-02 is therefore a per-class-arm restructuring, and the every-finding conjunction is preserved WITHIN each arm so a mixed message still refuses.
- F-06 ONE EXISTING TEST ASSERTS THE BEHAVIOR THIS PLAN INVERTS, and it must be rewritten rather than preserved (added at review, PR-002). `test_a_STALE_begin_receipt_is_NOT_retryable` is an `assertFalse` on exactly the case E-02 admits. Its four siblings pin classes that stay terminal and must pass unmodified, which is the stronger signal that the restructuring did not over-admit.
- F-04 THE DIGEST HAS ALREADY BEEN NARROWED TWICE, which is context for why this plan does not touch it. `receipt_is_current`'s own history records that the original whole-file digest "refused every self-finalizing run" and was narrowed to the frozen region, and a later change added the additive-widening substitution test. A gate needing a third narrowing is a candidate for a different response to its own finding, which is what this plan supplies, rather than a fourth boundary adjustment.

## Proposed changes (ordered, validatable)

1. E-01 give the scope-REDUCTION finding its own id, naming the shipped string.
2. E-02 admit the stale-receipt and reduction findings to the send-back, by the answerability test.
3. E-03 pin termination and non-laundering at budget exhaustion.

## Deferred / out of scope (with reason)

- Changing what `aw ipd finalize` checks, including the digest's frozen region: this plan changes the RESPONSE to a finding, not the finding. Order 01 leaves the gate alone for the same reason.
- Widening the retry budget: the budget is frozen per run and its size is a separate policy question; this plan spends the existing budget on two more classes.
- Making the fence-widening class retryable: deliberately terminal, per spec `25kzda` 5.5's never-retry list, and F-03 records that the reasoning still holds for that class.

## Scope check

Two finding classes move from terminal to retryable, on a predicate that already exists, spending a budget that already exists, through a prompt channel that already exists. One new finding id is introduced by naming a shipped string. No gate logic changes.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Baseline to beat, re-derive at execution rather than trusting this number: `8850 passed, 5 skipped, 2 xfailed` measured on `main` `a631a1f6` at authoring. Gate on NO NEW failures. Paste ACTUAL output for every `V-*`.

## Spec / documentation sync

NO SPEC IS AMENDED. Spec `25kzda` 5.5's never-retry list is NOT changed by this plan: the list governs the fence-widening class, which stays terminal. What changes is which SHIPPED FINDINGS the runner maps onto that list, and the module already records that the spec's `IPD-EXEC-*` codes "grep to zero files", so the runner keys on the enforcer's real output rather than on the spec's unbound names. If a reviewer judges that admitting a stale receipt contradicts 5.5 rather than refining it, that is a spec amendment and belongs to a plan that declares the spec path; this plan does not, and says so here rather than editing a contract silently.

## Open questions

- [ ] OQ-01 Does admitting a STALE RECEIPT to the send-back contradict spec `25kzda` 5.5, or refine it? Blocking: no. RECOMMENDATION: refine, and record the reasoning at the predicate. 5.5 permits the spend on "missing or stale validation evidence", and a stale receipt on a plan whose evidence was just written is the same situation seen from the other side. If a reviewer disagrees this becomes a spec amendment and a declared spec path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new finding id beside the shipped string it names, and paste the emitted findings for a reduction refusal BEFORE and AFTER, proving them byte-identical. Paste the `STALE_RECEIPT_REFUSAL` and `SCOPE_REFUSAL` module constants in `tests/test_finalize_sendback.py` UNCHANGED, since E-01 must not alter any emitted byte.
  - DO NOT ASSERT THAT `test_a_STALE_begin_receipt_is_NOT_retryable` STILL PASSES (corrected at review, PR-002). That test asserts `assertFalse(finalize_refusal_is_retryable(STALE_RECEIPT_REFUSAL))`, which is the exact behavior E-02 INVERTS, so it MUST be rewritten by E-02 and cannot be cited as an unchanged pin. What stays true, and is what this item pins instead, is that the FIXTURE STRING is unchanged: E-01 changes no emitted byte, so `STALE_RECEIPT_REFUSAL`'s text is identical and only the assertion's polarity moves, in E-02, with the answerability reason recorded at the test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: drive FIVE refusals end to end and paste each outcome. SENDS BACK: a stale receipt, and a scope REDUCTION. STAYS TERMINAL ON THE FIRST REFUSAL: a fence WIDENING with a changed frozen requirement, a MISSING begin receipt (`MISSING_RECEIPT_REFUSAL`), and a scope-reconciliation refusal (`SCOPE_REFUSAL`, spec 5.5's first never-retry entry). The last two are required because PR-001's restructuring touches the predicate's dispatch and a per-class arm keyed on the wrong summary could admit them; their existing `assertFalse` tests must still pass UNMODIFIED, which is the pin V-01 cannot supply. ALSO paste a MIXED stale-plus-rewrite message proven NOT retryable, since the every-finding conjunction is what stops a never-retry class riding along. Paste the RENDERED recovery prompt for one send-back showing the gate's findings reached the agent, following the existing test's precedent of asserting on the prompt rather than on a flag.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste an item exhausting its send-back budget on a stale receipt and ending TERMINAL with findings preserved, plus the recorded counter showing a second identical refusal did not reset it. Paste the assertion that no send-back path reaches a member of the success bar.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Human approval required before execution. WHAT A HUMAN IS ACTUALLY APPROVING, stated plainly because it is a policy change and not only a code change: two refusal classes that are terminal today become RETRYABLE, spending the existing per-run correction budget. Spec `25kzda` 5.5 names a stale receipt as "changed frozen requirements", and this plan argues that category does not discriminate the cases the runner meets (the measured `xdvglg` case changed a frozen requirement AND was answerable in one turn). The fence-WIDENING class, a MISSING receipt, and out-of-scope mutation all stay terminal.

OPEN QUESTIONS: OQ-01 is the only one and is `Blocking: no`, with a recorded recommendation (refine 5.5 rather than contradict it). An executor must NOT re-decide it mid-run. IF A REVIEWER OR THE MAINTAINER JUDGES IT A CONTRADICTION RATHER THAN A REFINEMENT, this plan does not declare a spec path and therefore may not amend the spec: that becomes a separate plan declaring `25kzda`, per the `Spec / documentation sync` section. Order 03 (`9x7otz`) is the only child of this Set licensed to amend a spec, so an undeclared spec edit from here is a defect that both runners will report at run end.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS: `- Scope-Paths:` names two modules and three test files. It is a DECLARATION, not a stop order: an out-of-scope edit that is genuinely required must be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a `--scope-ack`. Do not halt over a scope question. DO halt for a genuinely unsafe condition (an unresolvable concurrent-edit conflict, or a prerequisite whose symbols are absent). Note `runner_shared.py` is among the most contended files in this repository and sibling Order 01 declares it too; the two are independent (Order 01 touches the status vocabulary, this plan touches the finalize-retry predicate) and the runner isolates each item in its own worktree, so overlap is not a hazard to stop over.

HONESTY RULE (hard MUST): run the suite BARE as `python3 -m pytest` and paste the ACTUAL summary line; do not add `-n0`, a second `-q`, or `-p no:randomly`. Re-derive the baseline at execution rather than trusting the authored `8850 passed, 5 skipped, 2 xfailed`, and gate on NO NEW failures. Every `V-*` above demands pasted evidence and may not be marked complete from the matching `E-*` checkmark or from memory. V-01 through V-03 each name specific artifacts to paste; a claim of success without them does not satisfy these gates.

TESTS THIS PLAN MUST REWRITE RATHER THAN PRESERVE, named here so an executor does not read a red test as a regression: `tests/test_finalize_sendback.py::TheRetryTriggerIsAPositiveAllowlist::test_a_STALE_begin_receipt_is_NOT_retryable` asserts the exact behavior E-02 inverts and MUST be rewritten with the answerability reason recorded at the test. Its siblings `test_a_missing_begin_receipt_is_NOT_retryable`, `test_a_scope_reconciliation_refusal_is_NOT_retryable`, `test_a_MIXED_message_is_NOT_retryable`, and `test_an_empty_or_summary_only_message_is_NOT_retryable` must all still pass UNMODIFIED; if one of those goes red, the predicate restructuring is wrong, not the test.

COMMIT DISCIPLINE: commit only the declared paths, path-scoped, through `aw commit`; never `git add -A`, never `-a`, and never push. This is a shared checkout, so run `git diff --cached --name-only` before each commit and unstage anything that is not yours.

LIFECYCLE TRANSITION: this plan is `- Kind: child`, so the transition is owned unconditionally but its PERFORMER depends on the path. Under `aw oc run`/`aw agy run` the runner performs finalize; do not hand-roll a `git mv` to `executed/` on any path. Executed by hand, the executor runs `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
