# IPD: Send back an answerable finalize refusal instead of failing the item

- Date: 2026-09-24
- Kind: child
- Concern: A FINALIZE REFUSAL THE AGENT COULD ANSWER IN ONE TURN COSTS THE RUN AN ITEM AND EVERY ITEM BEHIND IT. Measured on run `run-20260924T050407Z-3108751`: `xdvglg` performed all 6 of its E-items and all 6 of its V-items, its work was correct, and it was recorded `substantially-complete` with nothing in `main` because `aw ipd finalize` refused on two findings - a STALE begin receipt and one `Scope-Paths` entry removed without a recorded reason. Both are answerable by the agent that was still running: the removed path pointed at `tests/test_rununify_initialize_run_characterization.py`, which commit `7ebc2964` DELETED FROM `main` on 2026-09-17, one day BEFORE the `/plan-review` round that declared it, so the plan was fenced to a file that could not be edited because it did not exist. The refusal was CORRECT and the response was disproportionate: `04vf1h` and `a5wdne` then cascaded `dependency-blocked` behind it, and a human (this session) resolved it by re-issuing `begin` and writing one paragraph. THE SEND-BACK MACHINERY ALREADY EXISTS AND ALREADY EXCLUDES THESE TWO CASES ON PURPOSE: `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` lists exactly three pre-transition E/V texts, and the module's own note records why the other classes are excluded - a stale receipt is spec `25kzda` 5.5's "changed frozen requirements" and an out-of-scope mutation is "the FIRST entry on its never-retry list". That reasoning is sound for an agent that WIDENED its fence without authority. It is wrong for a REDUCTION that removes a citation to a file `main` deleted, which is the same class of stale-citation defect this repository has hit repeatedly.
- Scope: Move the two ANSWERABLE finalize-refusal classes onto the existing send-back path so the agent is asked rather than the item failed, keeping every unanswerable class exactly as it is. The test that decides is NOT "did a frozen requirement change" but "can the agent answer this in one bounded turn": a `Scope-Paths` REDUCTION and a STALE RECEIPT are answerable (justify or revert); an out-of-scope MUTATION that widened the fence without authority is not, and stays terminal. Reuses `RETRYABLE_FINALIZE_FINDING_TEXTS`, the `finalize_refused` prior-attempt key, and the frozen retry budget; adds no new packet format and no new prompt channel. IN: the retryable-finding predicate, the send-back dispatch decision, and the tests that pin both. OUT: changing what `aw ipd finalize` itself checks or refuses (Order 01 and this plan both leave the gate's own logic alone), widening the retry BUDGET, and any change to the digest's frozen region.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, tests/test_finalize_sendback.py, tests/test_finidem_double_finalize.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Set: statusvocab
- Order: 2
- Highest E allocated: 03
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 787hb4

## Workflow history
- 2026-09-24 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored as part of splitting the oversized cyamvi plan into a Set on maintainer instruction; complete enough to critique.

- 2026-09-24 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the runner ASK when the answer is one turn away. A refusal an agent can resolve should cost a turn, not an item plus everything behind it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: widen the retryable set by the answerability test

- [ ] E-01 SEPARATE THE TWO SCOPE FINDINGS, because today they are one refusal branch and only one of them is answerable. `ipd_lifecycle`'s stale branch emits a REDUCTION finding ("Scope-Paths entry REMOVED since begin (a contract reduction, never accepted as a widening)") and a REWRITE finding ("gained X but a frozen REQUIREMENT also changed") from the same code path. Give the caller a distinct finding id for the REDUCTION case, following the precedent the module already set for `FINDING_RECEIPT_STALE`: NAME the shipped string rather than mint a new one, so no emitted byte changes and the existing pins in `tests/test_finalize_sendback.py` keep passing.
  - Depends on: none
  - Expected outcome: a caller can branch on reduction-versus-rewrite without matching refusal prose; emitted findings byte-identical to HEAD.
  - Execution state: pending

- [ ] E-02 ADD THE TWO ANSWERABLE CLASSES TO THE SEND-BACK PREDICATE, AND STATE THE TEST THAT ADMITS THEM. Extend the retryable set to include the stale-receipt finding and the scope-REDUCTION finding, leaving the rewrite/widening finding terminal. Record at the predicate WHY the admission test is "answerable in one bounded turn" rather than spec 5.5's "changed frozen requirements": the measured `xdvglg` case changed a frozen requirement AND was answerable, so the spec's category does not discriminate the cases the runner actually meets. The recovery prompt already interpolates `finalize_refused` through `prior_attempt_summary`, so the agent receives the gate's exact findings with no new format.
  - Depends on: E-01
  - Expected outcome: a stale-receipt or scope-reduction refusal re-dispatches the same item in recovery mode while budget remains, and FAILS the item when budget is exhausted; a fence-widening mutation is still terminal on the first refusal.
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
  - Required evidence: paste the new finding id beside the shipped string it names, and paste the emitted findings for a reduction refusal BEFORE and AFTER, proving them byte-identical. Paste `tests/test_finalize_sendback.py` still passing unmodified in its `STALE_RECEIPT_REFUSAL` assertion.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: drive THREE refusals end to end and paste each outcome: a stale receipt (sends back), a scope REDUCTION (sends back), and a fence WIDENING with a changed frozen requirement (stays terminal on the first refusal). Paste the RENDERED recovery prompt for one send-back showing the gate's findings reached the agent, following the existing test's precedent of asserting on the prompt rather than on a flag.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste an item exhausting its send-back budget on a stale receipt and ending TERMINAL with findings preserved, plus the recorded counter showing a second identical refusal did not reset it. Paste the assertion that no send-back path reaches a member of the success bar.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

Human approval required before execution.
