# IPD: Discriminate live fail-gate items by attempt failure and outcome disposition in the run summary outcome-word ladder

- Date: 2026-10-14
- Kind: child
- Concern: Run summary `Outcome:` word classification for live `fail-gate` queue items in `agent_workflows/render_stream.py`.
- Scope: Add item-level `fail-gate` producer discrimination in `agent_workflows/render_stream.py` (`outcome_class_of_item`) so `render_run_summary_table` maps nonzero-exit / crashed `fail-gate` turns to `OUTCOME_CLASS_FAILED` (`FAILED`), executed-claim-not-moved `fail-gate` turns without a gate refusal to `OUTCOME_CLASS_SUCCESS` (`COMPLETED` when work landed or `--no-self-finalize`, `STRANDED` when `work_did_not_land(item)` is true), and gate refusals awaiting a human (plus bare `fail-gate` items) to `OUTCOME_CLASS_BLOCKED` (`BLOCKED`); cover all three producers in `tests/test_outcome_word_ladder.py`; add one `Fixed:` line to `CHANGELOG.md`.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_outcome_word_ladder.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 1h98o3
- Set: 1h98o3 (fail-gate outcome-word discrimination)
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: rowilw
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008

- 2026-10-14 draft (Antigravity): created from backlog item `1h98o3`.
- 2026-10-14 to-review (Antigravity): populated findings, design for `outcome_class_of_item`, and `E-01`..`E-03` / `V-01`..`V-03` pairs.

## Goal

Restore accurate `Outcome:` header words (`FAILED`, `COMPLETED`, `STRANDED`, and `BLOCKED`) in `render_stream.render_run_summary_table` for live `fail-gate` items after `cyamvi` (commit `6b94a4d9d`) unified `reconcile_disposition`'s nonzero-exit fallback and `outcome_precedence_disposition`'s executed-claim-not-moved branch onto the canonical `"fail-gate"` status token. Discriminate the three live `"fail-gate"` producers in `agent_workflows/render_stream.py` using already-recorded item/attempt fields (`attempts[-1]["exit_code"]`, `attempts[-1]["turn_failure_kind"]`, `host_error`, `refusal_of_item(item)`, and `last_outcome["disposition"]`) rather than overloading the status token.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Item-level `fail-gate` outcome-class discriminator in `render_stream.py`

- [ ] E-01 In `agent_workflows/render_stream.py`, define a pure helper `outcome_class_of_item(item: Mapping[str, Any]) -> str` AFTER `DECLARED_OUTCOME_ALIAS_DIVERGENCES` (it calls `refusal_of_item`, defined later in the module, which is fine at call time). It returns `OUTCOME_CLASS_NONE` for a non-`Mapping`, and `RUN_OUTCOME_CLASS_BY_STATUS.get(item.get("status"), OUTCOME_CLASS_NONE)` for any status other than `"fail-gate"`. For `"fail-gate"` it discriminates the three live producers from recorded fields, in this order: (1) `OUTCOME_CLASS_FAILED` when the last `Mapping` entry of `item.get("attempts")` has a non-blank `str` `turn_failure_kind`, a non-`bool` `int` `exit_code != 0`, or a truthy `host_error`, or when `item.get("host_error")` is truthy, or when the recorded refusal's `.code` is in `("SPEC-PRODUCTION-FAILED", "BACKLOG-PRODUCTION-FAILED")`; (2) `OUTCOME_CLASS_BLOCKED` when any other refusal is recorded; (3) `OUTCOME_CLASS_SUCCESS` only when the last attempt RECORDS `exit_code == 0` (a non-`bool` `int`; an ABSENT exit code is not success, so zero/one-attempt fixtures without one stay `BLOCKED`), `item.get("action", "execute") == "execute"`, `not item.get("proposal_record")`, `not item.get("needs_input")`, and `item.get("last_outcome")` is a `Mapping` whose `disposition` (stripped, lowercased) is in `("executed", "completed", "substantially-complete")`; (4) otherwise `OUTCOME_CLASS_BLOCKED`. TWO TYPE TRAPS, both measured at review: `refusal_of_item` returns a frozen `@dataclass` `Refusal`, so read `refusal.code` (it has no `.get`, and `refusal.get("code")` raises `AttributeError`); and `refusal_of_item` returns `None` for any non-`dict` (`if not isinstance(item, dict): return None`), so pass `item if isinstance(item, dict) else dict(item)` or a `Mapping` input silently loses its refusal and can be misread as success. Update the two `DECLARED_OUTCOME_ALIAS_DIVERGENCES` reason strings for `failed-safely` and `substantially-complete`, and the `RULE:` comment above the table, to say the canonical `fail-gate` is BLOCKED at TOKEN level and is discriminated per item by `outcome_class_of_item` (keys and classes unchanged).
  - Depends on: none
  - Expected outcome: `render_stream.outcome_class_of_item` is importable and classifies `"fail-gate"` items into `OUTCOME_CLASS_FAILED`, `OUTCOME_CLASS_SUCCESS`, or `OUTCOME_CLASS_BLOCKED` according to recorded attempt/outcome/refusal fields while preserving `RUN_OUTCOME_CLASS_BY_STATUS["fail-gate"] == OUTCOME_CLASS_BLOCKED` as the token-level default.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/render_stream.py` `render_run_summary_table`, replace EVERY occurrence of `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` in the outcome-word ladder with `outcome_class_of_item(it)` (five at review: the `INTERRUPTED`, `FAILED`, and `BLOCKED` `any(...)` arms and the two `all(...)` success tests feeding `COMPLETED` and `NO WORK PERFORMED`), re-deriving the count at execution. Change nothing else in the ladder: its order, the `isinstance(it, Mapping)` guards, the `refusal_of_item`/`work_did_not_land`/`queue_performed_no_work` conditions, and the `STRANDED`/`PARTIAL`/`QUEUED` tail stay as they are. There is NO `all_failed` variable, NO `OUTCOME_CLASS_SKIPPED` constant and NO success-plus-skipped arm in this function; do not add any. Effect: a crashed `fail-gate` item renders `FAILED` (and, because the `FAILED` arm is `any(...)`, so does any queue containing one, including `[executed, crashed fail-gate]`); a refusal-free executed-claim `fail-gate` item renders `COMPLETED`, or `STRANDED` when `work_did_not_land(it)`; a gate-refusal or bare `fail-gate` item renders `BLOCKED`.
  - Depends on: E-01
  - Expected outcome: `render_run_summary_table` contains no remaining `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` call and derives each item's class through `outcome_class_of_item(it)`; every existing word for every non-`fail-gate` token is unchanged.
  - Execution state: pending

### Task group 2: Unit and regression tests in `tests/test_outcome_word_ladder.py`

- [ ] E-03 In `tests/test_outcome_word_ladder.py`, add tests exercising `outcome_class_of_item` and `render_run_summary_table` across all three live `"fail-gate"` producer shapes: (a) nonzero-exit / crashed turns (`exit_code != 0`, `turn_failure_kind` set, `host_error` set, and `SPEC-PRODUCTION-FAILED` / `BACKLOG-PRODUCTION-FAILED` refusal codes) rendering `Outcome: FAILED`, including a mixed `[executed, crashed fail-gate]` queue (the `FAILED` arm is `any(...)`; measured at review, `[executed, failed-safely]` already renders `FAILED`), plus a review-action `fail-gate` with `exit_code=1` rendering `FAILED`; (b) executed-claim-not-moved turns (`exit_code == 0`, no refusal, `last_outcome={"disposition": "executed"}` or `"substantially-complete"`) rendering `Outcome: COMPLETED` when `work_did_not_land` is false and `Outcome: STRANDED` when `integration_signal` is a non-landing signal (`"suite-failed"`); and (c) gate refusals awaiting a human continuing to render `Outcome: BLOCKED`: a recorded refusal with code `awaiting-human-decision` (`render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE`), a legacy flat `finalize_refusal` string over an executed claim, `proposal_record` plus `needs_input`, a `clean_base_refused` attempt, a `SPEC-PLAN-COUNT` refusal with `exit_code == 0`, an agent-recorded `last_outcome={"disposition": "blocked"}` at `exit_code == 0`, a bare `fail-gate` with `attempts=[]`, and one with `attempts=[{"number": 1}]` (no exit code). Also add one case passing a non-`dict` `Mapping` (`types.MappingProxyType`) of a refused executed-claim item and asserting `OUTCOME_CLASS_BLOCKED` (the type trap in E-01). Keep `test_case_a_word_table`, `test_case_c_alias_agreement` and `test_case_d_canonical_fail_gate` unchanged and passing: their shapes carry no `exit_code`, so they pin the token-level default; update only the module docstring's `(d)` line to say the TOKEN-level default is BLOCKED and producers are discriminated per item.
  - Depends on: E-01, E-02
  - Expected outcome: the focused modules listed under Required tests and the bare full suite pass with zero failures.
  - Execution state: pending

### Task group 3: Release notes

- [ ] E-04 Add one `Fixed:` bullet under the existing `## 2.0.0 (pending)` heading in `CHANGELOG.md` stating that the run summary's `Outcome:` word again reads `FAILED` for a turn that crashed or exited nonzero and `COMPLETED` or `STRANDED` for a turn that finished its work, instead of `BLOCKED`, which is now reserved for items waiting on a gate or a human. Add no heading, reword no neighbouring bullet, and write no em or en dashes (user-facing prose).
  - Depends on: E-03
  - Expected outcome: a single added `Fixed:` bullet in `CHANGELOG.md` with zero em/en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `RUN_OUTCOME_CLASS_BY_STATUS` in `agent_workflows/render_stream.py` (defined around `OUTCOME_CLASS_BLOCKED = "blocked"`) is the single source of truth mapping item status tokens to token-level outcome classes (`OUTCOME_CLASS_SUCCESS`, `OUTCOME_CLASS_FAILED`, `OUTCOME_CLASS_BLOCKED`, `OUTCOME_CLASS_INTERRUPTED`, `OUTCOME_CLASS_NONE`), and `tests/test_outcome_word_ladder.py` (`test_run_outcome_class_table_covers_every_declared_status_token`, `test_canonical_aliases_share_outcome_class_unless_declared`) pins that every declared status token has an entry in `RUN_OUTCOME_CLASS_BY_STATUS` and that `"fail-gate"` is listed in `DECLARED_OUTCOME_ALIAS_DIVERGENCES` alongside `"failed-safely"`, `"blocked"`, and `"substantially-complete"`.
- Plan `064awu` (`.aw/records/plans/executed/20261012-3l0dmi-01-064awu-declare-one-outcome-word-arm-per-status-token-so-canonical-f.ipd.md`) resolved the two-arm `"fail-gate"` collision in `render_run_summary_table` by assigning `"fail-gate": OUTCOME_CLASS_BLOCKED` in `RUN_OUTCOME_CLASS_BY_STATUS` and filing backlog item `1h98o3` to discriminate the live `"fail-gate"` producers using recorded item/attempt fields.
- The real ladder in `render_run_summary_table` (review 2026-10-15, HEAD `ba8709ea4`): `exit_reason` > `INTERRUPTED` (any) > `FAILED` (any) > `BLOCKED` (any) > `COMPLETED` (all success, no refusal, no `work_did_not_land`, not `queue_performed_no_work`) > `NO WORK PERFORMED` > `STRANDED` (any `work_did_not_land`) > `PARTIAL` (`completed_count > 0`) > `QUEUED`. Five `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` call sites; there is no `OUTCOME_CLASS_SKIPPED`.
- Review prototype (scratch copy under the gitignored `.aw/state/`, deleted afterwards): the E-01 helper as now specified, wired at all five sites, passed `tests/test_outcome_word_ladder.py`, `test_zero_dispatch_outcome.py`, `test_review_failure_reason.py`, `test_run_summary_table.py`, `test_run_proposal_channel.py`, `test_spec_production.py`, `test_fixfirst_end_to_end.py`, `test_suppress_narrowing.py`, `test_canonical_status_reader_sweep.py`, `test_terminal_status_vocabulary.py` (`159 passed`), and rendered crash exit 1 / exit 137 -> `FAILED`, refusal-free executed claim -> `COMPLETED`, same with `integration_signal="suite-failed"` -> `STRANDED`, same with legacy `finalize_refusal` -> `BLOCKED`, bare / clean-base / agent-`blocked` -> `BLOCKED`, `[executed, crash]` -> `FAILED`.
- Tests must exercise observable behavior (`outcome_class_of_item` and `render_run_summary_table` outputs) and never inspect source code via `inspect`, `ast`, or regex.

## Findings

| # | Producer of `item["status"] = "fail-gate"` in `agent_workflows/runner_shared.py` | Pre-`6b94a4d9d` status token & `Outcome:` word | Recorded fields on `item` and `item["attempts"][-1]` | Desired `outcome_class_of_item(item)` & `Outcome:` word |
|---|---|---|---|---|
| 1 | Nonzero-exit / crashed turn in `reconcile_disposition` (Rung 2 review `exit_code != 0`, Rung 2b spec production `exit_code != 0`, Rung 5 fallback `exit_code != 0`) and `execute_item_core` post-turn recording | `"failed-safely"` -> `OUTCOME_CLASS_FAILED` -> `FAILED` | `attempts[-1]["exit_code"]` is a non-zero `int`, `attempts[-1]["turn_failure_kind"]` is `"nonzero-exit"` / `"no-outcome"` / `"turn-limit"` / `"spawn-failure"` / `"stall"`, `host_error` is set on `attempt` or `item`, or `refusal_of_item(item)["code"]` is `"SPEC-PRODUCTION-FAILED"` / `"BACKLOG-PRODUCTION-FAILED"` | `OUTCOME_CLASS_FAILED` -> `FAILED` (the `FAILED` arm is `any(...)`, so one crashed item colors the whole run, as `failed-safely` did) |
| 2 | Executed-claim-not-moved / `substantially-complete` turn in `outcome_precedence_disposition` (Rung 2 `bucket != "executed"` with `outcome["disposition"] in ("executed", "completed")`, or Rung 3 `canonical_terminal_status("substantially-complete")`) when `exit_code == 0` and no gate refusal was recorded | `"substantially-complete"` -> `OUTCOME_CLASS_SUCCESS` -> `COMPLETED` (when `not work_did_not_land(item)`, e.g. `--no-self-finalize`) or `STRANDED` (when `work_did_not_land(item)` is true, e.g. `integration_signal == "suite-failed"`) | `attempts[-1]["exit_code"] == 0` (recorded by `execute_item_core`'s `attempt.update({... "exit_code": exit_code ...})`; an ABSENT exit code does not qualify), no `turn_failure_kind`, `refusal_of_item(item) is None`, `not item.get("proposal_record")`, `not item.get("needs_input")`, and `item["last_outcome"]["disposition"] in ("executed", "completed", "substantially-complete")` | `OUTCOME_CLASS_SUCCESS` -> `COMPLETED` when `not work_did_not_land(item)`, or falls through to `STRANDED` (`STRANDED_OUTCOME`) when `work_did_not_land(item)` is true |
| 3 | Pre-dispatch or post-turn gate refusal awaiting a human (`clean_base_refused`, `scope_target_refused`, `host_capability_unavailable`, `proposal_record` / `awaiting-human-decision`, `finalize-refused`, `finalize-plan-unresolvable`, `spec-review-not-reviewed`, `review-zero-output`, `IPD-REVIEW-ORCHESTRATOR-READY`, `SPEC-PLAN-*`, `BACKLOG-GRADUATE-*`, agent-recorded `disposition in ("blocked", "fail-gate")`, or bare `fail-gate` fixtures) | `"blocked"` / `"fail-gate"` -> `OUTCOME_CLASS_BLOCKED` -> `BLOCKED` | No nonzero `exit_code`, no `turn_failure_kind`, and either `refusal_of_item(item)` is a gate refusal, `proposal_record` / `needs_input` is set, `last_outcome` is absent or has a non-success disposition, or `attempts` is empty/minimal | `OUTCOME_CLASS_BLOCKED` -> `BLOCKED` |

## Proposed changes (ordered, validatable)

1. **Add `outcome_class_of_item(item: Mapping[str, Any]) -> str` in `agent_workflows/render_stream.py` (`E-01`)**, after `DECLARED_OUTCOME_ALIAS_DIVERGENCES`; keys and classes of both tables unchanged (only the two divergence reason strings and the `RULE:` comment are reworded):
   ```python
   _PRODUCTION_FAILED_REFUSAL_CODES = ("SPEC-PRODUCTION-FAILED", "BACKLOG-PRODUCTION-FAILED")
   _CLAIMED_SUCCESS_DISPOSITIONS = ("executed", "completed", "substantially-complete")

   def outcome_class_of_item(item: Mapping[str, Any]) -> str:
       if not isinstance(item, Mapping):
           return OUTCOME_CLASS_NONE
       status = item.get("status")
       if status != "fail-gate":
           return RUN_OUTCOME_CLASS_BY_STATUS.get(status, OUTCOME_CLASS_NONE)
       attempts = item.get("attempts")
       last = next((a for a in reversed(attempts) if isinstance(a, Mapping)), None) if isinstance(attempts, list) else None
       exit_code = last.get("exit_code") if last is not None else None
       ran = isinstance(exit_code, int) and not isinstance(exit_code, bool)
       if last is not None:
           tfk = last.get("turn_failure_kind")
           if (isinstance(tfk, str) and tfk.strip()) or (ran and exit_code != 0) or last.get("host_error"):
               return OUTCOME_CLASS_FAILED
       if item.get("host_error"):
           return OUTCOME_CLASS_FAILED
       refusal = refusal_of_item(item if isinstance(item, dict) else dict(item))
       if refusal is not None:
           return OUTCOME_CLASS_FAILED if refusal.code in _PRODUCTION_FAILED_REFUSAL_CODES else OUTCOME_CLASS_BLOCKED
       lo = item.get("last_outcome")
       if (ran and exit_code == 0
               and str(item.get("action") or "execute") == "execute"
               and not item.get("proposal_record") and not item.get("needs_input")
               and isinstance(lo, Mapping)
               and str(lo.get("disposition") or "").strip().lower() in _CLAIMED_SUCCESS_DISPOSITIONS):
           return OUTCOME_CLASS_SUCCESS
       return OUTCOME_CLASS_BLOCKED
   ```
2. **Wire it into `render_run_summary_table` (`E-02`)**: replace each of the five `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` expressions with `outcome_class_of_item(it)`, leaving every other condition and the arm order untouched.
3. **Tests in `tests/test_outcome_word_ladder.py` (`E-03`)**: the producer shapes listed in E-03, asserting both `outcome_class_of_item(...)` and the rendered `Outcome:` word through the module's existing `render_run_summary_table` helpers. Expected words: crash shapes -> `FAILED`; `[executed, crash]` -> `FAILED`; refusal-free executed claim -> `COMPLETED`; with `integration_signal="suite-failed"` -> `STRANDED` (and `work_did_not_land` true); every gate-refusal / bare shape -> `BLOCKED`.
4. **`CHANGELOG.md` (`E-04`)**: one `Fixed:` bullet.

## Deferred / out of scope (with reason)

- Changing `runner_shared.reconcile_disposition` or `runner_shared.outcome_precedence_disposition` status tokens: out of scope because backlog item `1h98o3` and spec `77tr3o` intentionally keep `"fail-gate"` as the single canonical status token and require discriminating producers in `render_stream.py` from recorded item/attempt fields rather than minting or reverting status tokens.
  - Carrier-Declined: not outstanding work; the design deliberately keeps the producer tokens, so there is nothing to carry.

## Scope check

- Over-scope: none.
- Under-scope: none after review (`CHANGELOG.md` added as E-04) — all three live `"fail-gate"` producer families in `runner_shared.py` (`exit_code != 0` / turn-failure / production-crash, executed-claim-not-moved `last_outcome`, and human-gated refusals) and their interactions with `work_did_not_land` and `refusal_of_item` in `render_run_summary_table` are covered.

## Required tests / validation

- Focused test run: `python3 -m pytest -o addopts="" -v tests/test_outcome_word_ladder.py tests/test_zero_dispatch_outcome.py tests/test_review_failure_reason.py tests/test_run_summary_table.py tests/test_run_proposal_channel.py tests/test_spec_production.py tests/test_terminal_status_vocabulary.py`
- Full repository test suite: `python3 -m pytest` run BARE (no added flags), with the actual `N passed` summary line pasted.

## Spec / documentation sync

- `CHANGELOG.md` `Fixed:` bullet (E-04). No spec change: spec `77tr3o` defines `"fail-gate"` as the canonical status token for gate refusals and non-zero/unmoved reconciliation, while the run summary `Outcome:` header word is an internal rendering concern in `agent_workflows/render_stream.py` tracked by backlog item `1h98o3`.

## Open questions

### OQ-01: How should an executed-claim-not-moved `fail-gate` item be classified when `self_finalize` subsequently records a finalize gate refusal (`finalize-refused`) versus when integration fails (`integration_signal="suite-failed"`)?

- Blocking: no
- Status: resolved
- Owner: plan author (Antigravity)
- Resolution or deferral rationale: Resolved from repository evidence in `agent_workflows/runner_shared.py` (`execute_item_core`, `handle_finalize_refusal`) and `agent_workflows/render_stream.py` (`refusal_of_item`, `work_did_not_land`). When `self_finalize` refuses, `handle_finalize_refusal` records `item["finalize_refusal"]` (surfaced by `refusal_of_item(item)` with `code="finalize-refused"`), which is a genuine gate refusal awaiting human/agent remediation and therefore stays `OUTCOME_CLASS_BLOCKED` (`BLOCKED`). When `self_finalize` is skipped because the integration gate did not earn (`integration_signal="suite-failed"` or `"verifier-declined"`), no gate refusal is recorded (`refusal_of_item(item) is None`) and `work_did_not_land(item)` is true; classifying the item as `OUTCOME_CLASS_SUCCESS` (matching pre-`6b94a4d9d` `"substantially-complete"`) allows the ladder to bypass `BLOCKED` and reach the `STRANDED` arm (`elif any(work_did_not_land(it) for it in queue): outcome_str = STRANDED_OUTCOME`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/render_stream.py` showing `outcome_class_of_item(item)` defined after `DECLARED_OUTCOME_ALIAS_DIVERGENCES`, reading `refusal.code` (not `.get`), passing a `dict` to `refusal_of_item`, requiring a recorded `exit_code == 0` for success, and handling all three `"fail-gate"` producer cases (attempt failure / nonzero exit / host error / production-crash refusal code -> `OUTCOME_CLASS_FAILED`; refusal-free executed/completed/substantially-complete `last_outcome` -> `OUTCOME_CLASS_SUCCESS`; gate refusals and bare `fail-gate` -> `OUTCOME_CLASS_BLOCKED`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/render_stream.py` showing `render_run_summary_table`'s ladder calling `outcome_class_of_item(it)` at every former `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` site and no other ladder change, plus pasted `rg -n 'RUN_OUTCOME_CLASS_BY_STATUS.get\(it.get' agent_workflows/render_stream.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted verbose output of the focused test run in Required tests showing every new producer-shape test and the unchanged `test_case_a_word_table` / `test_case_c_alias_agreement` / `test_case_d_canonical_fail_gate` passing; the quoted assertions showing they check only `outcome_class_of_item` return values and the rendered `Outcome:` word (P16); and the pasted BARE `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added `Fixed:` bullet under `## 2.0.0 (pending)` and no other change, plus a pasted check confirming zero em or en dashes (`\u2013`, `\u2014`) in the added line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires `/plan-review` and explicit human approval before execution.

Execution contract: all open questions are resolved. Commit only the files named in `- Scope-Paths:`, through `aw commit rowilw -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE: an edit outside `- Scope-Paths:` that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, never silently.
