# IPD: Record whether a gate answer actually released the lane beside the token's integrates property

- Date: 2026-09-26
- Kind: child
- Concern: THE PERSISTED GATE-ANSWER RECORD CONTRADICTS THE OUTCOME IT EXISTS TO AUDIT. `runner_shared.gate_answer_record` persists `"integrates": bool(verdict.integrates)`, a property of the answer TOKEN (only `not-mine` releases on the answer alone), and no field recording what actually happened. `runner_shared.perform_gate_answer` computes the real outcome as `release = bool(verdict.integrates) or (bool(verdict.earns_recheck) and recheck_passed is True)` and returns it only on `GateAnswerOutcome.release`, which is not persisted. Re-measured at HEAD `61ef21d8` by driving the real `perform_gate_answer` with each token and a PASSING re-run: `not-mine release True integrates True recheck_passed None`; `fixed release True integrates False recheck_passed True`; `mine release False integrates False`; `needs-human release False integrates False`. So for a verified `fixed`, the lane integrates while the durable record at `state["queue"][i]["integration_gate_answer"]` reads `integrates: False`. The docstring calls this record "THE SAFEGUARD rather than bookkeeping", the thing an auditor reads afterwards; nothing in `agent_workflows/` reads the `integrates` key (grep for `get("integrates")` / `["integrates"]` is empty).
- Scope: IN: (a) a keyword-only parameter `released: bool | None = None` on `gate_answer_record`, persisted as a new `"released"` key (None meaning "not decided by this record's producer", e.g. an interrupted follow-up); (b) `perform_gate_answer` passes `released=release`; (c) the interrupted-follow-up site in `runner_shared` that builds `GateAnswerOutcome(release=False, record=gate_answer_record(...))` passes `released=False`, so the record agrees with the outcome it is paired with; (d) the `gate_answer_record` docstring states that `integrates` is the TOKEN's property and `released` is the OUTCOME; (e) behavioral tests over all four tokens. OUT: renaming or removing `integrates` (existing `state.json` corpora and any external reader keep working); changing any release decision; changing what `attributed_away_failure_ids` or any other reader reads.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_gate_answer_record_released.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: w51mpv
- Set: gateansrec
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: nzznlm

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog w51mpv. Authored review-ready; the release/integrates contradiction was re-measured at HEAD 61ef21d8 by driving perform_gate_answer with all four tokens.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Persist, on the gate-answer record, whether the answer actually released the lane, so an auditor reading `integration_gate_answer` for a verified `fixed` sees `released: true` instead of inferring the opposite from `integrates: false`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. For each token in `runner_shared.GATE_ANSWERS` (`not-mine`, `fixed`, `mine`, `needs-human`), write `{GATE_ANSWER_KEY: {"answer": tok, "reason": "because"}}` to a temp `outcome.json` and call `runner_shared.perform_gate_answer(suite_result=<failing stub>, ask=lambda s: None, outcome_path=<file>, rerun_suite=lambda: <passing stub>, retry_budget=1)` (stubs are `types.SimpleNamespace(passing=..., failures=..., summary=...)`). Paste `tok, outcome.release, record["integrates"], record.get("released", "<absent>"), record["recheck_passed"]`.
  - Depends on: none
  - Expected outcome: `fixed` shows `release True`, `integrates False`, `released <absent>`, `recheck_passed True`; the other three show `release == integrates`.
  - Execution state: pending

### Task group 2: record the outcome

- [ ] E-02 ADD THE FIELD to `runner_shared.gate_answer_record`: a keyword-only `released: bool | None = None` parameter persisted as `"released": released if released is None else bool(released)`, placed immediately after `"integrates"` in the returned dict. Extend the docstring's contract paragraph: `integrates` is whether the TOKEN releases on the answer alone (only `not-mine`), `released` is whether THIS answer actually released the lane (it is what `GateAnswerOutcome.release` was), and `None` means the producer did not decide a release. Cite `w51mpv`. Do NOT rename or drop `integrates`.
  - Depends on: E-01
  - Expected outcome: `gate_answer_record(verdict, asked=True, ask_reason="")` carries `"released": None`; with `released=True` it carries `True`.
  - Execution state: pending

- [ ] E-03 PASS THE OUTCOME at both producers in `runner_shared`: in `perform_gate_answer`, add `released=release` to the `gate_answer_record(...)` call that follows the `release = ...` conjunction; at the interrupted-follow-up site (the `except (KeyboardInterrupt, StallTimeout):` block that builds `GateAnswerOutcome(release=False, record=gate_answer_record(GateAnswerVerdict("", "", "the follow-up turn was interrupted before it answered"), ...))`), add `released=False`. Grep for every other `gate_answer_record(` call and paste the list; if a third producer exists, pass the `release` value it pairs with.
  - Depends on: E-02
  - Expected outcome: E-01's probe now shows `released` equal to `outcome.release` for all four tokens.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 ADD `tests/test_gate_answer_record_released.py`, behavioral only (maintainer's 2026-09-26 ruling: no source-text pins). Drive the REAL `perform_gate_answer` as in E-01. Cases: (1) for each of the four tokens, `outcome.record["released"] == outcome.release`; (2) `fixed` with a PASSING re-run -> `released is True` and `integrates is False` (the contradiction resolved, both fields kept); (3) `fixed` with a re-run that keeps FAILING until the budget is spent -> `released is False`; (4) `fixed` with `rerun_suite=None` -> `released is False`; (5) `not-mine` -> `released is True` and `integrates is True`; (6) the record still carries every pre-existing key (`answer`, `reason`, `violation`, `usable`, `integrates`, `refuses`, `awaits_human_decision`, `asked`, `ask_reason`, `session_id`, `signal`, `failing_tests`, `recheck_attempts`, `recheck_budget`, `recheck_passed`, `recheck_summary`, `suite_baseline`), so the change is additive; (7) `gate_answer_record` called directly with no `released` argument yields `"released": None`; (8) the record round-trips through `json.dumps`/`json.loads` unchanged, since it is persisted in `state.json`.
  - Depends on: E-03
  - Expected outcome: all pass; cases (1), (2), (3), (4), (5), (7) FAIL before the change (the key is absent); (6) and (8) pass before and after (controls).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `GateAnswerOutcome.release` "is the ONLY field the integration decision reads" (its class docstring); the record is for audit. So adding a record key cannot change any release.
- `gate_answer_record`'s docstring declares itself "the contract a consumer codes against" and gives the location `state["queue"][i]["integration_gate_answer"]` in `<run_dir>/state.json`; the one in-package reader of the record, `runner_shared.attributed_away_failure_ids`, reads `answer`, `usable`, and `failing_tests` only.
- Spec `25kzda` Section 5.1 makes captured evidence the admissibility basis for the attribution exception; it does not enumerate the record keys (grep of the spec for `integrates` / `recheck_passed` finds no key list), so an additive key amends no spec.
- Precedent for additive, old-reader-safe record changes: the docstring's `suite_baseline` paragraph added a key "FOR AUDIT AND NOTHING ELSE".
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `runner_shared.gate_answer_record` | The record persists the token property `integrates` and no outcome. | returned dict: `"integrates": bool(verdict.integrates)`; no `released` key |
| F-2 | MEDIUM | `runner_shared.perform_gate_answer` | For a verified `fixed`, the outcome and the record disagree. | probe: `fixed release True integrates False recheck_passed True` |
| F-3 | INFO | readers | Nothing in the package reads `integrates` from the record. | grep for `get("integrates")` / `["integrates"]` in `agent_workflows/` is empty |
| F-4 | INFO | producers | Two call sites build the record: `perform_gate_answer` and the interrupted-follow-up handler. | `rg -n "gate_answer_record\(" agent_workflows/runner_shared.py` -> definition plus two calls |

## Proposed changes (ordered, validatable)

1. E-01 re-measures all four tokens.
2. E-02 adds the additive `released` key and the docstring contract.
3. E-03 passes the outcome at both producers.
4. E-04 adds behavioral tests over all four tokens and the edge cases.

## Deferred / out of scope (with reason)

- Renaming `integrates` to something that cannot be read as an outcome (the backlog item's option 2).
  - Carrier-Declined: it changes a persisted key, so every existing `state.json` corpus and any external reader would need to tolerate both names; the additive `released` key removes the ambiguity without that cost, and the docstring now states what `integrates` means.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/oc_runipd.py` / `agy_runipd.py` are NOT declared: both hosts reach the record through the shared `runner_shared` producers.
- Scope-Paths justification: `runner_shared.py` holds the record builder and both producers; the new test file holds E-04.

## Required tests / validation

- `tests/test_gate_answer_record_released.py` (new): eight behavioral cases, six failing before the change.
- `python3 -m pytest -o addopts="" -q tests/test_runner_shared.py` stays green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `25kzda` does not enumerate the record's keys, and the change is additive. No `.spec.md` is in `- Scope-Paths:`.
- The record's contract lives in the `gate_answer_record` docstring, which E-02 updates.

## Open questions

### OQ-01: What should `released` be for the interrupted-follow-up record?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `False`, from repository evidence: that site constructs `GateAnswerOutcome(release=False, ...)` and its comment says "An interrupted follow-up leaves the refusal STANDING, which is the fail-closed direction". The record must agree with the outcome it is paired with; `None` is reserved for a direct call where no release was decided.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the four probe lines with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `gate_answer_record` diff (signature, dict, docstring) and a direct call's `released` value with and without the argument.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the list of `gate_answer_record(` call sites, the diff at each, and the re-run probe showing `released == release` for all four tokens.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_gate_answer_record_released.py` passing with its count; the same run with E-02/E-03 temporarily reverted showing cases (1) through (5) and (7) FAILING and (6), (8) passing; `python3 -m pytest -o addopts="" -q tests/test_runner_shared.py` passing; and the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One new key, `released`, on the persisted gate-answer record, holding whether the answer actually released the lane, next to the existing `integrates` (unchanged, now documented as the token's own property). No release decision changes, and no existing key is renamed or removed.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (`gate_answer_record` and its callers) and the new `tests/test_gate_answer_record_released.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show the new cases FAILING before the change.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `w51mpv` `done` with `--evidence` citing the executed plan.
