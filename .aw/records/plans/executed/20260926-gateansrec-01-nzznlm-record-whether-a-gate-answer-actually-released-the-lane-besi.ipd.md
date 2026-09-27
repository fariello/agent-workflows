# IPD: Record whether a gate answer actually released the lane beside the token's integrates property

- Date: 2026-09-26
- Kind: child
- Concern: THE PERSISTED GATE-ANSWER RECORD CONTRADICTS THE OUTCOME IT EXISTS TO AUDIT. `runner_shared.gate_answer_record` persists `"integrates": bool(verdict.integrates)`, a property of the answer TOKEN (only `not-mine` releases on the answer alone), and no field recording what actually happened. `runner_shared.perform_gate_answer` computes the real outcome as `release = bool(verdict.integrates) or (bool(verdict.earns_recheck) and recheck_passed is True)` and returns it only on `GateAnswerOutcome.release`, which is not persisted. Re-measured at HEAD `61ef21d8` by driving the real `perform_gate_answer` with each token and a PASSING re-run: `not-mine release True integrates True recheck_passed None`; `fixed release True integrates False recheck_passed True`; `mine release False integrates False`; `needs-human release False integrates False`. So for a verified `fixed`, the lane integrates while the durable record at `state["queue"][i]["integration_gate_answer"]` reads `integrates: False`. The docstring calls this record "THE SAFEGUARD rather than bookkeeping", the thing an auditor reads afterwards; nothing in `agent_workflows/` reads the `integrates` key (grep for `get("integrates")` / `["integrates"]` is empty).
- Scope: IN: (a) a keyword-only parameter `released: bool | None = None` on `gate_answer_record`, persisted as a new `"released"` key (None meaning "not decided by this record's producer", e.g. an interrupted follow-up); (b) `perform_gate_answer` passes `released=release`; (c) the interrupted-follow-up site in `runner_shared` that builds `GateAnswerOutcome(release=False, record=gate_answer_record(...))` passes `released=False`, so the record agrees with the outcome it is paired with; (d) the `gate_answer_record` docstring states that `integrates` is the TOKEN's property and `released` is the OUTCOME; (e) behavioral tests over all four tokens. OUT: renaming or removing `integrates` (existing `state.json` corpora and any external reader keep working); changing any release decision; changing what `attributed_away_failure_ids` or any other reader reads.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_gate_answer_record_released.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: w51mpv
- Set: gateansrec
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: nzznlm

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: nzznlm verified (set gateansrec, attempt 1).
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-005 all FIXED. Re-derived the four-token contradiction and all three edge cases by driving the real perform_gate_answer. Found and fixed: a fail-open hazard the new 'released' field makes easier to reach (guard (c) at GATE_ANSWER_RECORD_KEY: a reader keyed on the wrong field releases on two answers designed to refuse), so E-02 must warn in the docstring and V-03 must prove no gate-2 reader consults it; the plan's claim was wider than its defect (the outcome is already in events.jsonl and integration_released_by_answer, which render_stream reads), so the Goal is narrowed; E-03's interrupted-follow-up edit had no test surface, so E-05 was added; and neither edited function has ANY existing test coverage. Findings in .aw/records/reviews/20260926-gateansrec-01-nzznlm-record-whether-a-gate-answer-actually-released-the-lane-besi.review.md

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog w51mpv. Authored review-ready; the release/integrates contradiction was re-measured at HEAD 61ef21d8 by driving perform_gate_answer with all four tokens.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Persist, on the gate-answer record, whether the answer actually released the lane, so an auditor reading `integration_gate_answer` for a verified `fixed` sees `released: true` instead of inferring the opposite from `integrates: false`.

SCOPE OF THE CLAIM, narrowed at review (F-5). The release outcome is NOT unrecorded today: the run already writes an `events.jsonl` event named `integration-gate-answer-released` or `...-refused` chosen on `gate_outcome.release`, and sets `item["integration_released_by_answer"]` to the answer token, which `render_stream.integration_was_refused` reads. What this plan fixes is narrower and real: the outcome is absent from the ONE structure whose docstring declares itself "the contract a consumer codes against", so an auditor reading `integration_gate_answer` alone sees a field that reads as an outcome and says the opposite of what happened. This is an audit-legibility fix to a specific record, not the recovery of a lost fact.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [x] E-01 RE-MEASURE at the executing HEAD. For each token in `runner_shared.GATE_ANSWERS` (`not-mine`, `fixed`, `mine`, `needs-human`), write `{GATE_ANSWER_KEY: {"answer": tok, "reason": "because"}}` to a temp `outcome.json` and call `runner_shared.perform_gate_answer(suite_result=<failing stub>, ask=lambda s: None, outcome_path=<file>, rerun_suite=lambda: <passing stub>, retry_budget=1)` (stubs are `types.SimpleNamespace(passing=..., failures=..., summary=...)`). Paste `tok, outcome.release, record["integrates"], record.get("released", "<absent>"), record["recheck_passed"]`.
  - Depends on: none
  - Expected outcome: `fixed` shows `release True`, `integrates False`, `released <absent>`, `recheck_passed True`; the other three show `release == integrates`.
  - Execution state: performed

### Task group 2: record the outcome

- [x] E-02 ADD THE FIELD to `runner_shared.gate_answer_record`: a keyword-only `released: bool | None = None` parameter persisted as `"released": released if released is None else bool(released)`, placed immediately after `"integrates"` in the returned dict. Extend the docstring's contract paragraph: `integrates` is whether the TOKEN releases on the answer alone (only `not-mine`), `released` is whether THIS answer actually released the lane (it is what `GateAnswerOutcome.release` was), and `None` means the producer did not decide a release. Cite `w51mpv`. Do NOT rename or drop `integrates`.
  - Depends on: E-01
  - Expected outcome: `gate_answer_record(verdict, asked=True, ask_reason="")` carries `"released": None`; with `released=True` it carries `True`.
  - THE DOCSTRING MUST ALSO CARRY THE FAIL-OPEN WARNING, and this is the highest-risk sentence in the plan. `GATE_ANSWER_RECORD_KEY`'s guard (c) and `unattributed_merged_failures`'s guard list record a MEASURED fail-open hazard: a post-merge reader keyed on the wrong record field "would release on two answers designed to refuse", because `fixed` carries `release: True` beside its PRE-REPAIR `failing_tests`. `released` is exactly the field that makes that mistake easy to reach, since a reader who wants "did this integrate?" now finds a field that says yes for `fixed` too. So state plainly: `released` is FOR AUDIT AND NOTHING ELSE, it is NOT an admissibility signal, and the gate-2 attribution channel keys on the ANSWER TOKEN (`attributed_away_failure_ids` refuses anything but `not-mine`) and MUST NOT be changed to key on `released`. Use the same "WRITING IT IS NOT READING IT" framing the `suite_baseline` paragraph already uses, which is this record's established precedent for an audit-only key.
  - Execution state: performed

- [x] E-03 PASS THE OUTCOME at both producers in `runner_shared`: in `perform_gate_answer`, add `released=release` to the `gate_answer_record(...)` call that follows the `release = ...` conjunction; at the interrupted-follow-up site (the `except (KeyboardInterrupt, StallTimeout):` block that builds `GateAnswerOutcome(release=False, record=gate_answer_record(GateAnswerVerdict("", "", "the follow-up turn was interrupted before it answered"), ...))`), add `released=False`. Verified at review by `rg -n "gate_answer_record\(" agent_workflows/ tests/`: exactly the definition plus those two calls, one docstring mention, and NO test call site, so no third producer exists at this HEAD; re-run the grep and paste it, and if a third producer has appeared, pass the `release` value it pairs with.
  - Depends on: E-02
  - Expected outcome: E-01's probe now shows `released` equal to `outcome.release` for all four tokens.
  - Execution state: performed

### Task group 3: prove it

- [x] E-04 ADD `tests/test_gate_answer_record_released.py`, behavioral only (maintainer's 2026-09-26 ruling: no source-text pins). Drive the REAL `perform_gate_answer` as in E-01. Cases: (1) for each of the four tokens, `outcome.record["released"] == outcome.release`; (2) `fixed` with a PASSING re-run -> `released is True` and `integrates is False` (the contradiction resolved, both fields kept); (3) `fixed` with a re-run that keeps FAILING until the budget is spent -> `released is False`; (4) `fixed` with `rerun_suite=None` -> `released is False`; (5) `not-mine` -> `released is True` and `integrates is True`; (6) the record still carries every pre-existing key (`answer`, `reason`, `violation`, `usable`, `integrates`, `refuses`, `awaits_human_decision`, `asked`, `ask_reason`, `session_id`, `signal`, `failing_tests`, `recheck_attempts`, `recheck_budget`, `recheck_passed`, `recheck_summary`, `suite_baseline`), so the change is additive; (7) `gate_answer_record` called directly with no `released` argument yields `"released": None`; (8) the record round-trips through `json.dumps`/`json.loads` unchanged, since it is persisted in `state.json`.
  - Depends on: E-03
  - Expected outcome: all pass; cases (1), (2), (3), (4), (5), (7) FAIL before the change (the key is absent); (6) and (8) pass before and after (controls).
  - THE PRE-CHANGE FAILURE MODE IS AN ERROR, NOT AN ASSERTION FAILURE, and the tests must be written so that is unambiguous. Measured at review: `record["released"]` on unmodified code raises `KeyError: 'released'`. pytest counts that as a failing test, which satisfies the plan's intent, but a case written as `record.get("released") == outcome.release` would SILENTLY PASS for `mine` and `needs-human` (both `None == False` is False, so it fails) while `assert record.get("released") is outcome.release` would pass vacuously for neither; the trap is `.get()` with a default. So each of cases (1) to (5) MUST subscript (`record["released"]`) or assert the key's presence explicitly (`assert "released" in record`), never `.get("released", <default>)`.
  - CASES (6) AND (8) ARE CONTROLS THAT ALREADY PASS, verified at review: the 17-key list in case (6) is EXACTLY `gate_answer_record`'s current key set (checked by set comparison, no extras and none missing) and `json.loads(json.dumps(record)) == record` is already True. Label them in the test file as controls proving ADDITIVITY, so a reader does not mistake a green control for evidence of the fix.
  - Execution state: performed

- [x] E-05 ADD THE CASE THE PLAN'S OWN CONCERN IMPLIES BUT DID NOT COVER: the INTERRUPTED-FOLLOW-UP record E-03 touches. That site is not reachable through `perform_gate_answer`, so cases (1) to (5) cannot exercise it and E-03's second edit would ship with NO test. Call `gate_answer_record` directly with the verdict that site builds (`GateAnswerVerdict("", "", "the follow-up turn was interrupted before it answered")`, `asked=True`) plus `released=False`, and assert `record["released"] is False`. Assert alongside it that this record is distinguishable from a genuine refusal: measured at review, it carries `usable: False`, `answer: ""`, `integrates: False` AND `refuses: False` (an unusable verdict refuses nothing by the `refuses` property, since `""` is not in `GATE_ANSWERS_REFUSING`), so before this change the record's four boolean fields were ALL False and a reader could not tell "interrupted before answering" from "answered nothing". `released: False` is the field that makes the fail-closed outcome explicit, which is the whole point of E-03's second edit.
  - Depends on: E-03
  - Expected outcome: two assertions passing; both FAIL before the change (the key is absent).
  - Execution state: performed

## Project conventions discovered (Step 0)

- `GateAnswerOutcome.release` "is the ONLY field the integration decision reads" (its class docstring); the record is for audit. So adding a record key cannot change any release.
- `gate_answer_record`'s docstring declares itself "the contract a consumer codes against" and gives the location `state["queue"][i]["integration_gate_answer"]` in `<run_dir>/state.json`; the one in-package reader of the record, `runner_shared.attributed_away_failure_ids`, reads `answer`, `usable`, and `failing_tests` only.
- Spec `25kzda` (`Status: approved`) Section 5.1 makes captured evidence the admissibility basis for the attribution exception. Re-checked at review: it REQUIRES five facts by description ("the answer token, the agent's stated reason, THE FAILING TEST IDENTIFIERS THE AGENT WAS SHOWN, the session that answered, and the number and outcome of any suite re-runs") and enumerates no key names; `recheck_passed` and `released` appear nowhere in it, and its single `integrates` hit is the unrelated `--on-integration-blocked` flag. So an additive key amends no spec, and the ADDED field does not disturb any of the five required facts.
- Precedent for additive, old-reader-safe record changes: the docstring's `suite_baseline` paragraph added a key "FOR AUDIT AND NOTHING ELSE" and states "WRITING IT IS NOT READING IT". E-02's new paragraph follows that shape deliberately (see F-6).
- The record is not the only place the outcome is written: an `events.jsonl` event name and `item["integration_released_by_answer"]` both already record it, and `render_stream.integration_was_refused` reads the latter. See F-5; the defect is legibility of THIS record, not absence of the fact.
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `runner_shared.gate_answer_record` | The record persists the token property `integrates` and no outcome. | returned dict: `"integrates": bool(verdict.integrates)`; no `released` key |
| F-2 | MEDIUM | `runner_shared.perform_gate_answer` | For a verified `fixed`, the outcome and the record disagree. | probe: `fixed release True integrates False recheck_passed True` |
| F-3 | INFO | readers | Nothing in the package reads `integrates` from the record. | grep for `get("integrates")` / `["integrates"]` across `agent_workflows/` AND `tests/` returns exactly the WRITE at `gate_answer_record` and nothing else (re-verified at review; the three `tests/` hits for the bare word read `GateAnswerVerdict.integrates`, the property, never the record key) |
| F-4 | INFO | producers | Two call sites build the record: `perform_gate_answer` and the interrupted-follow-up handler. | `rg -n "gate_answer_record\(" agent_workflows/ tests/` -> the definition, one docstring mention, and exactly two calls; NO test call site |
| F-5 | MEDIUM | `runner_shared.execute_item_core` events emission, and `attempt`/`item["integration_released_by_answer"]` | FOUND AT REVIEW, AND IT NARROWS THE PLAN'S CLAIM WITHOUT REFUTING IT. The release outcome is ALREADY durably recorded twice outside this record: an `events.jsonl` line whose `event` is `integration-gate-answer-released` or `integration-gate-answer-refused` chosen on `gate_outcome.release`, and `item["integration_released_by_answer"]` (set to the ANSWER TOKEN on release), which `render_stream.integration_was_refused` actually READS to avoid reporting a landed run as stranded. So the outcome is not LOST today; what is missing is that it is absent from the ONE record the `gate_answer_record` docstring declares "the contract a consumer codes against", and an auditor reading `integration_gate_answer` alone still sees `integrates: false` on an item that integrated. That is a real audit-legibility defect and it is the defect the backlog item describes; it is NOT "the release outcome is unrecorded". The Goal and the gate are worded accordingly. | `runner_shared.py` events block selecting the event name on `gate_outcome.release`; `item["integration_released_by_answer"] = gate_outcome.record.get("answer")`; `render_stream.integration_was_refused` returning False when that key is set |
| F-6 | HIGH | `runner_shared.attributed_away_failure_ids`, `unattributed_merged_failures`, guard (c) at `GATE_ANSWER_RECORD_KEY` | THE FAIL-OPEN HAZARD THIS KEY MAKES EASIER TO REACH. Guard (c) is recorded as MEASURED: a reader keyed on the wrong field "would clear exactly the ids whose repair did not survive the merge, and would release on two answers designed to refuse", because `failing_tests` is populated for every answer and a `fixed` record carries `release: True` beside PRE-REPAIR failures. `attributed_away_failure_ids` therefore gates on the ANSWER TOKEN (`!= GATE_ANSWER_NOT_MINE` returns `()`). Adding a field literally named `released` puts a plausible-looking substitute for that token check one attribute access away, and the fail-open direction merges unverified work into main. E-02 must carry the warning IN THE DOCSTRING; nothing in this plan may change what that channel keys on. | `attributed_away_failure_ids` body: `if str(record.get("answer") or "").strip() != GATE_ANSWER_NOT_MINE: return ()`; guard (c) comment block at `GATE_ANSWER_RECORD_KEY`; spec `25kzda` 2026-09-23 amendment condition (3) |
| F-7 | INFO | `tests/` | `gate_answer_record` and `perform_gate_answer` have ZERO existing direct test coverage: the only gate tests in the repository exercise `validate_gate_answer` (`tests/test_runner_shared.py`, 11 call sites). Three test classes the module's own docstrings cite as pinning gate behavior (`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`, `::TheTwoMeasurementsAreComparable`, `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`) DO NOT EXIST anywhere in the repository, and neither file exists. PRE-EXISTING and NOT this plan's to fix, but it matters twice: E-04/E-05 are the FIRST tests of these two functions, so there is no regression net under them, and E-02 must not add a fourth citation to a nonexistent test. | `rg -l "gate_answer" tests/` -> `tests/test_runner_shared.py` only; `rg "perform_gate_answer" tests/` empty; `rg "NothingRefusesOnTheBaseline|TheExitCodeIsTheAuthorityAndNotTheList|TheTwoMeasurementsAreComparable" .` empty; `ls tests/ \| grep -i "baseline\|adjudic"` empty |

## Proposed changes (ordered, validatable)

1. E-01 re-measures all four tokens.
2. E-02 adds the additive `released` key and the docstring contract.
3. E-03 passes the outcome at both producers.
4. E-04 adds behavioral tests over all four tokens and the edge cases; E-05 covers the interrupted-follow-up producer E-03's second edit touches.

## Deferred / out of scope (with reason)

- Renaming `integrates` to something that cannot be read as an outcome (the backlog item's option 2).
  - Carrier-Declined: it changes a persisted key, so every existing `state.json` corpus and any external reader would need to tolerate both names; the additive `released` key removes the ambiguity without that cost, and the docstring now states what `integrates` means.
- The three test classes `runner_shared`'s own docstrings cite as pinning gate behavior, which DO NOT EXIST (F-7): `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`, `::TheTwoMeasurementsAreComparable`, and `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`. Neither file exists and no class by those names exists anywhere in the repository.
  - Carrier-Declined: PRE-EXISTING and orthogonal. Those citations are in paragraphs this plan does not edit (the `baseline`-reaches-no-decision paragraph and the guard (c) comment block), and writing the three missing test classes is a separate piece of work with its own scope, blast radius and approval. Recording them here is what stops E-02 from adding a FOURTH citation to a nonexistent test, which is the only way this plan could make the situation worse. A reader who wants them written should file it; this plan deliberately does not, because inventing work the maintainer has not seen is not this plan's to do and a carrier item would assert a decision nobody made.

## Scope check

- Over-scope: none. E-05 adds a test for a producer E-03 already edits, so it narrows an untested edit rather than widening scope.
- Under-scope: `agent_workflows/oc_runipd.py` / `agy_runipd.py` are NOT declared: both hosts reach the record through the shared `runner_shared` producers. Confirmed at review by the call-site grep (F-4): neither host module contains a `gate_answer_record(` call.
- Scope-Paths justification: `runner_shared.py` holds the record builder and both producers; the new test file holds E-04 and E-05.

## Required tests / validation

- `tests/test_gate_answer_record_released.py` (new): E-04's eight cases plus E-05's interrupted-follow-up case. SIX of E-04's eight and BOTH of E-05's fail before the change; cases (6) and (8) are controls that pass both before and after, and were verified at review to pass ALREADY.
- These are the FIRST direct tests of `gate_answer_record` and `perform_gate_answer` in the repository (F-7), so there is no existing regression net under either function. That raises the value of E-04/E-05 and lowers the assurance any pre-existing suite gives about this change.
- `python3 -m pytest -o addopts="" -q tests/test_runner_shared.py` stays green (measured at review on unmodified code: `93 passed in 14.51s`, so a drop below 93 is a regression rather than a flake).
- Bare `python3 -m pytest` before and after; compare failing node IDs. Neither `tests/test_runner_shared.py` nor the new file carries `pytest.mark.slow`, so both DO run in the bare suite; do not add a slow marker.

## Spec / documentation sync

- N/A for specs, re-verified at review: `25kzda` (`Status: approved`) Section 5.1 requires five facts by DESCRIPTION and names no record keys; `released` and `recheck_passed` appear nowhere in it. The change is additive and disturbs none of the five. No `.spec.md` is in `- Scope-Paths:`.
- The record's contract lives in the `gate_answer_record` docstring, which E-02 updates. That update MUST include the F-6 fail-open warning and MUST NOT cite a test that does not exist (F-7).

## Open questions

### OQ-01: What should `released` be for the interrupted-follow-up record?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `False`, from repository evidence: that site constructs `GateAnswerOutcome(release=False, ...)` and its comment says "An interrupted follow-up leaves the refusal STANDING, which is the fail-closed direction". The record must agree with the outcome it is paired with; `None` is reserved for a direct call where no release was decided. STRENGTHENED AT REVIEW with the measurement that makes it load-bearing: that record's four boolean fields are currently ALL False (`usable: False`, `answer: ""`, `integrates: False`, and `refuses: False`, because an empty answer is not in `GATE_ANSWERS_REFUSING`), so nothing in it distinguishes "interrupted before answering" from "answered nothing". `released: False` is the field that states the fail-closed outcome explicitly, which is why E-05 tests it rather than leaving E-03's second edit uncovered.

### OQ-02: Does `released` belong on the record at all, given that the outcome is already in `events.jsonl` and `integration_released_by_answer`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, resolved at review from the record's own declared contract. The `gate_answer_record` docstring states it is "the contract a consumer codes against" and gives its location as `state["queue"][i]["integration_gate_answer"]`; a consumer coding against that contract reads THAT dict, not the event stream, and finds a field named as an outcome asserting the opposite of what happened. The precedent is explicit: `suite_baseline` was added to this same record "FOR AUDIT AND NOTHING ELSE" for a fact also obtainable elsewhere, on the reasoning that an auditor must be able to ask the question from the record in front of them. What the discovery DOES change is the plan's claim, which is now narrowed in the Goal and in F-5 so nobody reads this as recovering a lost fact.
- Carrier-Declined: nothing is left outstanding. The two existing recording sites are correct and unchanged, and no consumer is asked to migrate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the four probe lines with the HEAD hash.
  - Observed evidence: PASS. Executed probe at HEAD `dd25636f4e90eea0a75fd14b557f46a71b4f3cb9`:
    ```
    HEAD: dd25636f4e90eea0a75fd14b557f46a71b4f3cb9
    not-mine release True integrates True released <absent> recheck_passed None
    fixed release True integrates False released <absent> recheck_passed True
    mine release False integrates False released <absent> recheck_passed None
    needs-human release False integrates False released <absent> recheck_passed None
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `gate_answer_record` diff (signature, dict, docstring) and a direct call's `released` value with and without the argument. The pasted DOCSTRING must visibly contain the F-6 fail-open warning: that `released` is audit-only, that it is NOT an admissibility signal, and that the gate-2 attribution channel keys on the ANSWER TOKEN and must not be repointed at it. Also confirm the docstring adds NO citation to `tests/test_suite_baseline.py` or `tests/test_suite_adjudication.py`, neither of which exists (F-7).
  - Observed evidence: PASS. `gate_answer_record` diff in `agent_workflows/runner_shared.py`:
    ```diff
    @@ -21579,6 +21579,7 @@ def gate_answer_record(
         recheck_passed: bool | None = None,
         recheck_summary: str = "",
         baseline: SuiteBaseline | None = None,
    +    released: bool | None = None,
     ) -> dict[str, Any]:
         """The NORMALIZED record persisted on the run record, beside the integration signal.

    @@ -21606,6 +21607,21 @@ def gate_answer_record(

         WRITING IT IS NOT READING IT. Nothing in this package compares `suite_baseline["failures"]` to
         `failing_tests`; a record is not a check. See `SUITE_BASELINE_SUBDIR`.
    +
    +    `released` IS gateansrec-01 (`nzznlm` / backlog `w51mpv`), AND IT IS HERE FOR AUDIT AND NOTHING ELSE.
    +    `integrates` is whether the TOKEN releases on the answer alone (only `not-mine` is True; `fixed` is
    +    False because a repair claim earns a suite re-run and only an observed passing re-run releases).
    +    `released` records whether THIS answer actually released the lane (what `GateAnswerOutcome.release`
    +    evaluated to), resolving the legibility contradiction where an auditor reading a verified `fixed`
    +    answer saw `integrates: False` on an item that integrated. `None` means the producer did not
    +    decide a release (e.g. an unadorned direct call).
    +
    +    WRITING IT IS NOT READING IT, AND IT IS NOT AN ADMISSIBILITY SIGNAL. Guard (c) at
    +    `GATE_ANSWER_RECORD_KEY` records a measured fail-open hazard: a post-merge reader keyed on
    +    an outcome field rather than the token would release on two answers designed to refuse, because
    +    `fixed` carries `release: True` beside pre-repair `failing_tests`. The gate-2 attribution channel
    +    keys strictly on the ANSWER TOKEN (`attributed_away_failure_ids` refuses anything other than
    +    `not-mine`) and MUST NOT be changed to key on `released`.
         """

         return {
    @@ -21623,6 +21639,7 @@ def gate_answer_record(
             "violation": verdict.violation,
             "usable": bool(verdict.usable),
             "integrates": bool(verdict.integrates),
    +        "released": released if released is None else bool(released),
             "refuses": bool(verdict.refuses),
             "awaits_human_decision": bool(verdict.awaits_human_decision),
             "asked": bool(asked),
    ```
    Direct call values with and without argument:
    ```
    without arg: None
    with released=True: True
    with released=False: False
    ```
    The docstring visibly contains the F-6 fail-open warning and adds NO citations to nonexistent test classes `test_suite_baseline.py` or `test_suite_adjudication.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the re-run of `rg -n "gate_answer_record\(" agent_workflows/ tests/` showing the call-site set (expected at this HEAD: the definition, one docstring mention, and exactly two calls), the diff at each of the two calls, and the re-run probe showing `released == release` for all four tokens.
  - ALSO REQUIRED, the ANTI-REGRESSION CHECK for F-6, because this is the one way this plan could do harm: paste `rg -n 'record.get\("released"\)|record\["released"\]|\.get\("released"' agent_workflows/` and show that `attributed_away_failure_ids`, `unattributed_merged_failures` and `_relative_revalidation_verdict` contain NO read of the new key, i.e. the gate-2 channel still keys on the answer token. A hit inside any of those three is a fail-open regression and must be removed, not explained.
  - Observed evidence: PASS.
    Call-site set via `rg -n "gate_answer_record\(" agent_workflows/ tests/`:
    ```
    agent_workflows/runner_shared.py:21569:def gate_answer_record(
    agent_workflows/runner_shared.py:21721:    call and the `gate_answer_record(...)` call. It is absent from every `if`, from the `release`
    agent_workflows/runner_shared.py:21811:    record = gate_answer_record(
    agent_workflows/runner_shared.py:29386:                    record=gate_answer_record(
    tests/test_gate_answer_record_released.py:129:        rec = runner_shared.gate_answer_record(verdict, asked=True, ask_reason="")
    tests/test_gate_answer_record_released.py:146:        rec_unadorned = runner_shared.gate_answer_record(
    tests/test_gate_answer_record_released.py:157:            rec = runner_shared.gate_answer_record(
    ```
    Diffs at the two production call sites:
    ```diff
    @@ -21803,6 +21820,7 @@ def perform_gate_answer(
             recheck_passed=recheck_passed,
             recheck_summary=recheck_summary,
             baseline=baseline,
    +        released=release,
         )
         return GateAnswerOutcome(
             release=release,
    @@ -29377,6 +29395,7 @@ def execute_item_core(
                             integration_signal=integration.signal,
                             failures=getattr(suite_result, "failures", ()) or (),
                             baseline=suite_baseline,
    +                        released=False,
                         ),
                     )
                 attempt[GATE_ANSWER_RECORD_KEY] = gate_outcome.record
    ```
    Re-run probe showing `released == release` for all four tokens:
    ```
    not-mine release True integrates True released True recheck_passed None
    fixed release True integrates False released True recheck_passed True
    mine release False integrates False released False recheck_passed None
    needs-human release False integrates False released False recheck_passed None
    ```
    Anti-regression check for F-6:
    `rg -n 'record.get\("released"\)|record\["released"\]|\.get\("released"' agent_workflows/`
    Exit code 1 (no hits). `attributed_away_failure_ids`, `unattributed_merged_failures`, and `_relative_revalidation_verdict` contain no read of `released`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_gate_answer_record_released.py` passing with its count; the BEFORE-CHANGE run showing cases (1) through (5) and (7) FAILING and (6), (8) passing; `python3 -m pytest -o addopts="" -q tests/test_runner_shared.py` passing with at least the 93 measured at review; and the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty).
  - HOW TO GET THE BEFORE-CHANGE RUN, prescribed because the obvious route is unsafe in a shared checkout: use a throwaway detached worktree (`git worktree add --detach <gitignored path> <base-sha>`; `.gitignore` ignores `.aw/worktrees/` and `tmp/`) and copy the new test file into it, then `git worktree remove`. Do NOT revert E-02/E-03 in place and do NOT use `git stash`: a stash moves a co-worker's uncommitted changes. If an in-place revert is used anyway, restore it in the very next command and say so in the evidence.
  - STATE THE FAILURE MODE HONESTLY: on unmodified code `record["released"]` raises `KeyError: 'released'` (measured at review), so the pre-change result is an ERROR rather than an assertion failure. pytest counts it as failing, which satisfies the bar; say which it was rather than implying a clean assertion failure.
  - Observed evidence: PASS.
    Before-change run of `tests/test_gate_answer_record_released.py` (executed directly against unmodified `runner_shared.py` prior to editing):
    Cases (1) through (5), (7), and (9) FAILED with `KeyError: 'released'` (error on absent key), while controls (6) and (8) passed:
    ```
    .FF.FFFFF                                                                [100%]
    =================================== FAILURES ===================================
    ...
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_5_not_mine_releases_and_integrates
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_2_fixed_passing_rerun_contradiction_resolved
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_3_fixed_failing_rerun_exhausted_budget
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_7_direct_call_without_released_yields_none
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_1_four_tokens_released_matches_outcome_release
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_4_fixed_rerun_suite_none
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_9_interrupted_follow_up_record
    7 failed, 2 passed in 0.17s
    ```
    All 7 failures were ERRORS due to `KeyError: 'released'`.
    After-change run:
    ```
    python3 -m pytest -o addopts="" -q tests/test_gate_answer_record_released.py
    .........                                                                [100%]
    9 passed in 0.12s
    ```
    `tests/test_runner_shared.py` run:
    ```
    python3 -m pytest -o addopts="" -q tests/test_runner_shared.py
    ........................................................................ [ 77%]
    .....................                                                    [100%]
    93 passed in 19.54s
    ```
    Bare `python3 -m pytest` before change:
    `2689 passed, 2 skipped, 3 warnings in 83.98s (0:01:23)`
    Bare `python3 -m pytest` after change:
    `2698 passed, 2 skipped, 3 warnings in 93.72s (0:01:33)`
    After-minus-before failing node-ID set: empty (0 failing before, 0 failing after; exactly 9 new tests passed).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the interrupted-follow-up case PASSING after the change and FAILING (or erroring on the absent key) before it, plus the assertion output showing that record's `usable`/`integrates`/`refuses` values so the "all four booleans were False" claim in OQ-01 is visible rather than asserted.
  - Observed evidence: PASS.
    Before change: errored with `KeyError: 'released'` on `rec["released"]` after asserting baseline record properties:
    ```
    FAILED tests/test_gate_answer_record_released.py::GateAnswerRecordReleasedTests::test_case_9_interrupted_follow_up_record
    KeyError: 'released'
    ```
    After change:
    `test_case_9_interrupted_follow_up_record` passed cleanly in the 9-passed suite.
    Assertion output showing interrupted follow-up record values (proving all four booleans were False):
    ```
    usable: False
    answer: ''
    integrates: False
    refuses: False
    released: False
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one additive key on one record, its two producers, and their tests. Assessed against the right-sizing diagnostics at review: each E-item is one focused pass, and E-05 was SPLIT OUT because E-03's second edit (the interrupted-follow-up producer) is unreachable through `perform_gate_answer` and so had no test surface inside E-04's cases.

WHAT A HUMAN IS APPROVING. One new key, `released`, on the persisted gate-answer record, holding whether the answer actually released the lane, next to the existing `integrates` (unchanged, now documented as the token's own property). No release decision changes, and no existing key is renamed or removed. Nine test cases in one new file, which are the FIRST direct tests of `gate_answer_record` and `perform_gate_answer` in this repository (F-7).

WHAT THIS IS AND IS NOT, stated because the original wording invited a wider reading (F-5). The release outcome is ALREADY recorded in `events.jsonl` and in `item["integration_released_by_answer"]`, and `render_stream` reads the latter. This fixes the LEGIBILITY of the one record that declares itself the consumer contract, where a field named as an outcome currently says the opposite of what happened. It does not recover a lost fact.

THE ONE REAL RISK, and it is a fail-open one (F-6). `runner_shared` records a MEASURED hazard at `GATE_ANSWER_RECORD_KEY` guard (c): a post-merge reader keyed on the wrong field would "release on two answers designed to refuse", because `failing_tests` is populated for every answer and a `fixed` record carries a release beside PRE-REPAIR failures. `attributed_away_failure_ids` therefore gates on the ANSWER TOKEN. A field named `released` is a plausible-looking substitute for that check, and substituting it would merge unverified work into main. E-02 must carry the warning in the docstring and V-03 must prove no reader in the gate-2 channel consults the new key.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (`gate_answer_record` and its two callers, and nothing else in that file) and the new `tests/test_gate_answer_record_released.py`. Specifically NOT in scope: `attributed_away_failure_ids`, `unattributed_merged_failures`, `_relative_revalidation_verdict`, or any other reader; the three missing test classes recorded in F-7. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 and V-05 must show the new cases FAILING before the change, and must say whether each failed by assertion or by `KeyError`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit nzznlm -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence. The terminal transition is `aw ipd finalize nzznlm --actor <agent/model> --message <summary> --apply`; OWNERSHIP IS CONDITIONAL, the RUNNER performs it in a managed lane and the executor performs it only in an unmanaged or hand-driven run, and it is never hand-rolled with `git mv`. Then close backlog `w51mpv` `done` with `--evidence` citing the executed plan.
