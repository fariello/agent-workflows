# IPD: Add global fix-it turn caps per artifact, per Set, and per run on top of the per-kind retry budget

- Date: 2026-10-12
- Kind: child
- Concern: The runner bounds fix-it (correction) turns only PER FAILURE KIND. Each kind keeps its own counter on the queue item (`runner_shared.TURN_RETRY_COUNT_KEY`, `FINALIZE_RETRY_COUNT_KEY`, `HOOK_FINALIZE_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY`, `MERGE_CONFLICT_RETRY_COUNT_KEY`, `ZERO_WORK_RETRY_COUNT_KEY`, `VERIFICATION_RETRY_COUNT_KEY`, `PRODUCTION_SET_RETRY_COUNT_KEY`, `REVIEW_ORCHESTRATOR_RETRY_COUNT_KEY`) and each is compared against the whole `runner_shared.frozen_retry_budget(state)` (default 2). Set `fixfirst` made many more failure kinds retryable, so one stubborn item can spend `budget x kinds` paid turns (2 x 10 = 20 with today's keys) and a Set or a run has no aggregate bound at all.
- Scope: Keep the per-kind budget unchanged. Add three GLOBAL fix-it caps, each configurable through repository policy `run.fix_it_caps` in `.aw/config/project.json` and frozen into run state at queue build: per artifact (default 20 fix-it turns across all kinds), per Set (default `max(20, 15 * members)`), per run (default `max(40, largest per-Set cap, 10 * artifacts)`). Every fix-it send-back site consults one shared predicate before spending a unit; when a cap is reached the item stops as needs-human (refusal code `fix-it-cap-reached`, `NEEDS_INPUT_KEY` set) with the cap, its limit and its spend named in the run summary and in `execution-report.md`. Amend spec `25kzda` 5.5 to state the caps. EXCLUDES: changing the per-kind default or the 0..10 bound of `--retry-budget`; a new CLI flag for the caps (OQ-02); capping FIRST attempts (only fix-it turns are capped, OQ-01); integration RE-ATTEMPTS under `--integration-retry-limit` (they spend no agent turn); the orchestrator-readiness probe's own retries (`orchestrator_readiness.review_readiness` `retry_budget=`), which are model probes, not fix-it turns; the structurally one-shot defect re-ask and carrier-verification follow-ups (see Deferred).
- Scope-Paths: agent_workflows/config.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_fix_it_global_caps.py, tests/test_config.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: 38hwvk
- Set: 38hwvk
- Order: 1
- Highest E allocated: 10
- Author: opencode
- Id: c0oysi
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed; review record .aw/records/reviews/20261012-38hwvk-01-c0oysi-add-global-fix-it-turn-caps-per-artifact-per-set-and-per-run.review.md

- 2026-10-12 to-review (opencode): authored from backlog `38hwvk` (BACKLOG-GRADUATE); review-ready.
- 2026-10-12 draft (opencode): created.

## Goal

Bound the TOTAL number of paid fix-it turns one item, one Set and one run can spend, across every failure kind, so the broadened fix-first retry policy cannot quietly multiply cost; when a cap is reached, stop the affected item as needs-human and name the cap in the run report instead of failing silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: configuration and freezing

- [ ] E-01 In `agent_workflows/config.py`, add `RUN_FIX_IT_CAPS_MEMBER = "fix_it_caps"` beside `RUN_RETRY_BUDGET_MEMBER`, a `FIX_IT_CAPS_DEFAULTS` mapping (`per_artifact: 20`, `per_set_floor: 20`, `per_set_per_member: 15`, `per_run_floor: 40`, `per_run_per_artifact: 10`), and `policy_fix_it_caps(repo_root, *, warn=None) -> dict[str, int]` reading the `fix_it_caps` object under `run` via `read_run_policy`. Each member is optional and falls back to its default. A member that is not a non-negative `int` (a `bool`, a string, a negative number) or an unknown member name falls back/is dropped AND emits one warning naming the key, the value and the file, never raising: this is the `policy_retry_budget` posture documented in the comment block above `RUN_POLICY_KEY` ("FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE"), and the reason transfers unchanged (the file is tracked and shared, so refusing would break every run in the checkout).
  - Depends on: none
  - Expected outcome: with no `run.fix_it_caps` the function returns exactly the five defaults and prints nothing; `{"run": {"fix_it_caps": {"per_artifact": 5}}}` returns 5 for that member and defaults for the rest; `{"per_artifact": -1, "bogus": 3}` returns the default 20, drops `bogus`, and emits two warnings each naming the key and value.
  - Execution state: pending

- [ ] E-02 In `runner_shared.initialize_run_core`, freeze the resolved caps PARAMETERS into `state["options"]["fix_it_caps"]` (call `config.policy_fix_it_caps(repo)` once, next to the `**freeze_run_policy_flags(args, repo=repo)` entry, so `repo` is passed exactly as the retry-budget freeze requires). Add `frozen_fix_it_caps(state) -> dict[str, int]` mirroring `frozen_retry_budget`: it reads the frozen dict and fills any absent member from `config.FIX_IT_CAPS_DEFAULTS`, so a run directory frozen before this change (no `fix_it_caps` key) resumes with the defaults rather than raising. Resume never re-reads the policy file, matching spec 5.5 "The frozen budget cannot be raised on resume".
  - Depends on: E-01
  - Expected outcome: a fresh run's `state.json` carries `options.fix_it_caps` with five integers; editing `.aw/config/project.json` and resuming leaves the frozen values unchanged; `frozen_fix_it_caps({"options": {}})` returns the defaults.
  - Execution state: pending

### Task group 2: the shared census and decision

- [ ] E-03 In `runner_shared.py`, add `FIX_IT_COUNT_KEYS: tuple[str, ...]` naming every per-kind fix-it counter key that exists at execution time (at authoring: the ten keys listed in Concern; RE-DERIVE the list at execution with `rg -n "_RETRY_COUNT_KEY: str|_RETRY_COUNT_KEY = |ZERO_WORK_RETRY_COUNT_KEY" agent_workflows/runner_shared.py`, because pending `fixfirst` plans `ytas91` and `62sdwr` may add a counter, and include any such key). Add `fix_it_turns_spent(item) -> int` summing those counters (each read with the existing never-negative, non-int-is-zero guard used by `finalize_retry_attempts`) plus the gate-answer re-run count (`perform_gate_answer` spends a resumed agent turn per re-run against `retry_budget`, so it is a fix-it turn). The gate-answer count is NOT read from `item[GATE_ANSWER_RECORD_KEY]`: `execute_item_core` OVERWRITES that record on every attempt (`item[GATE_ANSWER_RECORD_KEY] = gate_outcome.record`), so a second attempt's gate answer would erase the first attempt's re-runs from the census. Instead add a cumulative per-item counter `GATE_ANSWER_RETRY_COUNT_KEY: str = "gate_answer_retry_attempts"`, increment it in `execute_item_core` by `gate_outcome.record["recheck_attempts"]` immediately after `perform_gate_answer` returns, and include it in `FIX_IT_COUNT_KEYS`. Add `fix_it_cap_limits(item, state) -> tuple[int, int | None, int]` computing (per-artifact limit, per-Set limit or `None` when the item has no `setid`, per-run limit) from `frozen_fix_it_caps(state)` and the FROZEN queue. Count only DISPATCHABLE entries (exclude `action == "skip"` entries, which never run): Set members = dispatchable queue entries sharing the item's `setid`; per-Set = `max(per_set_floor, per_set_per_member * members)`; per-run = `max(per_run_floor, largest per-Set limit over every setid in the queue, per_run_per_artifact * dispatchable entries)`. Note the formula makes the per-run limit always at least every per-Set limit, which is the backlog's own definition and constrains how E-10 case (c) can be built.
  - Depends on: E-02
  - Expected outcome: an item carrying `turn_retry_attempts: 2`, `finalize_retry_attempts: 1` and `gate_answer_retry_attempts: 1` reports 4 spent; two successive gate answers of 1 re-run each on one item leave `gate_answer_retry_attempts: 2`; a 3-member Set in a 5-item run with defaults yields limits `(20, 45, 50)`; a 1-member Set in a 2-item run yields `(20, 20, 40)`.
  - Execution state: pending

- [ ] E-04 Add `FixItCapDecision(NamedTuple)` (`reached: bool`, `cap: str` one of `per-artifact`/`per-set`/`per-run`/`""`, `limit: int`, `spent: int`, `reason: str`) and `fix_it_cap_decision(item, state) -> FixItCapDecision`, a PURE decider (no state write, no print, the same contract as `finalize_retry_decision`). It computes the item's own spend, the Set's spend (sum over queue entries sharing `setid`) and the run's spend (sum over the queue), and reports the FIRST cap reached in the order per-artifact, per-Set, per-run, where "reached" means `spent >= limit` (so a cap of 0 refuses the first fix-it turn, mirroring spec 5.5's budget-0 rule). The reason names the cap, the limit, the spend and the `run.fix_it_caps` member that configures it. Add `FIX_IT_CAP_REFUSAL_CODE = "fix-it-cap-reached"`.
  - Depends on: E-03
  - Expected outcome: with `per_artifact: 3` and an item that has spent 3, the decision is `reached=True, cap="per-artifact", limit=3, spent=3`; with an item at 1 whose Set has spent 45 of 45, `cap="per-set"`; with nothing reached, `reached=False, cap=""`.
  - Execution state: pending

### Task group 3: enforcement at every send-back site

- [ ] E-05 Wire `fix_it_cap_decision` into each of the six DECIDERS so that, at the point where each would today return `retry=True`, it instead returns its own EXHAUSTED shape with the cap's reason when `fix_it_cap_decision(item, state).reached`: `finalize_retry_decision`, `turn_retry_decision`, `zero_work_retry_decision`, `verification_retry_decision`, `production_set_retry_decision`, `review_orchestrator_retry_decision`. The check runs AFTER each decider's retryable-class, idempotency and lock-contention checks AND AFTER its `used >= budget` check, i.e. immediately before the `retry=True` return, so a non-retryable class, an already-spent key and a lock contention keep today's exact outcome, and a per-kind exhaustion still wins with its own wording when both apply. Carry the cap decision on the returned tuple (add an optional `cap: FixItCapDecision | None = None` field with a default, so every existing constructor call and test stays valid).
  - Depends on: E-04
  - Expected outcome: for each decider, an item whose per-kind counter is below budget but whose artifact cap is reached returns `retry=False, exhausted=True` with a reason containing `per-artifact` and the limit; the same item with the cap not reached returns `retry=True` exactly as before.
  - Execution state: pending

- [ ] E-06 Wire the same predicate into the four INLINE send-back loops in `execute_item_core` that do not go through a decider: the merge-conflict loop (condition on `MERGE_CONFLICT_RETRY_COUNT_KEY < conflict_budget`), the hook-integration loop (`HOOK_INTEGRATION_RETRY_COUNT_KEY < hook_integ_budget`), the combined-red loop (`COMBINED_RED_RETRY_COUNT_KEY < combined_red_budget`), and the gate-answer re-run bound inside `perform_gate_answer` (`attempts >= budget`). Add `and not fix_it_cap_decision(item, state).reached` to each loop condition (for `perform_gate_answer`, pass a `cap_reached: Callable[[int], FixItCapDecision] | None` keyword defaulting to `None` so its other callers are unchanged; the function calls it with its own in-call `attempts` so far, and the caller's callable adds that in-flight spend to the census, because `GATE_ANSWER_RETRY_COUNT_KEY` is only incremented after `perform_gate_answer` returns (E-03) and a census taken inside the loop would otherwise not see re-runs already spent in this call; `fix_it_cap_decision` therefore takes an `extra_spent: int = 0` keyword added to the item's, the Set's and the run's spend), and when the loop stops BECAUSE of the cap, record the cap decision on the attempt (`attempt["fix_it_cap"] = decision._asdict()`) so E-07 can name it.
  - Depends on: E-04
  - Expected outcome: with `retry_budget: 2` and `per_artifact: 0`, a lane whose integration hits a git merge conflict receives zero merge-conflict send-backs and the attempt carries `fix_it_cap` naming `per-artifact`; with the cap not reached the loop behaves exactly as today.
  - Execution state: pending

- [ ] E-07 Make a cap stop NEEDS-HUMAN and name the cap. Add `record_fix_it_cap_stop(item, decision, host_labels)` that calls `render_stream.record_refusal(item, code=FIX_IT_CAP_REFUSAL_CODE, reason=decision.reason, remedy=...)` (the ONE refusal writer, so the run summary's diagnostics block renders it with no new reader) and sets `item[NEEDS_INPUT_KEY] = True`, so `aggregated_run_items` maps the item to `needs_input` and the run exits 3 (spec 5.6) rather than 1. The remedy names the `run.fix_it_caps` member to raise, says to inspect the attempts with `aw runs show <run-id>` first, and states that the caps are FROZEN for this run (E-02), so raising the policy takes effect only in a NEW run; it must not suggest `resume --retry-incomplete`, which keeps the frozen caps and the item's accumulated counters and would refuse the next fix-it turn again. Call it from every exhausted path reached BECAUSE of a cap (E-05's six handlers via the decision's `cap` field, E-06's four loops via `attempt["fix_it_cap"]`), AFTER that path's own refusal write so the cap is the refusal the summary names. For the three INTEGRATION loops (merge-conflict, hook-integration, combined-red) the path's own writer is `render_stream.record_integration_refusal`, whose remedy carries the one irreversible-move warning ("the verified work is PRESERVED on branch ... Do NOT delete the branch or discard the lane"); `record_fix_it_cap_stop` therefore takes `preserved_remedy: str | None = None` and, when the item already carries a refusal, APPENDS that refusal's remedy to the cap remedy rather than discarding it, so a cap stop never hides that the lane branch must be kept; the item's terminal STATUS is whatever that path already writes (for example `TURN_RETRY_EXHAUSTED_STATUS`), so no status enters `runner_shutdown.KNOWN_ITEM_STATUSES`. Append one `fix-it-cap-reached` event to `events.jsonl` carrying `id6`, `setid`, `cap`, `limit`, `spent`. In `runner_shared.write_report`, add a `## Fix-it caps` section listing each item stopped by a cap (id6, cap, limit, spent) and the run's frozen caps; emit NOTHING when no item was stopped by a cap, so an unaffected report is byte-identical.
  - Depends on: E-05, E-06
  - Expected outcome: a run whose only item hits the artifact cap exits 3, its rendered summary contains `fix-it-cap-reached` and `per-artifact`, `execution-report.md` contains a `## Fix-it caps` section naming the item, and `events.jsonl` has exactly one `fix-it-cap-reached` event; a run with no cap hit has no such section.
  - Execution state: pending

### Task group 4: spec, changelog, tests

- [ ] E-08 Amend spec `25kzda` Section 5.5 (declared in Scope-Paths): add a paragraph after the precedence/bound paragraph titled "Global fix-it caps" stating the three caps, their defaults and formulas, that they count fix-it turns across ALL kinds (including gate-answer re-runs) and never first attempts, that they are configured by `run.fix_it_caps` with the warn-and-default posture, that they are frozen at queue build and cannot change on resume, and that a reached cap stops the item needs-human with refusal code `fix-it-cap-reached`. Amend group (b)'s "fix-it budget exhausted" bullet to read "fix-it budget exhausted, or a global fix-it cap reached (needs-human)", and the matching table row's Notes. Record it with `aw specs note <spec> --message "amendment (c0oysi): Section 5.5 adds global fix-it caps per artifact, per Set and per run (backlog 38hwvk)"`.
  - Depends on: E-07
  - Expected outcome: `git diff` of the spec shows only Section 5.5 changes plus one appended `## Workflow history` line; `aw check` reports no new finding for the spec.
  - Execution state: pending

- [ ] E-09 Add a `CHANGELOG.md` entry under the current pending release heading: an "Added:" line describing the three global fix-it caps, their defaults, the `run.fix_it_caps` policy key, and that a reached cap stops the item for a human with the cap named in the run report. User-facing prose: no em or en dashes.
  - Depends on: E-07
  - Expected outcome: one new `- Added:` line under `## 2.0.0 (pending)`; `rg -n "[\u2013\u2014]"` over the added line returns nothing.
  - Execution state: pending

- [ ] E-10 Add `tests/test_fix_it_global_caps.py` and extend `tests/test_config.py`, testing OUTCOMES only (no source introspection, no symbol censuses). Config: E-01's three cases with a captured `warn`. Unit: `fix_it_turns_spent`, `fix_it_cap_limits` and `fix_it_cap_decision` on constructed item/state dicts for each cap, for the cap-0 case and for a pre-change state with no `fix_it_caps` option. Deciders: each of the six from E-05 called directly, cap reached versus not reached, plus a non-retryable class that stays non-retryable with the cap reached. End to end on BOTH hosts (`oc_runipd`, `agy_runipd`) through `execute_item` with a scripted host in a scratch repo, reusing the fixture shape of `tests/test_hook_and_suite_fix_it.UnitHookAndSuiteFixItTests._setup_driver_fixture` (copy, do not import a private helper): (a) `retry_budget: 2`, `per_artifact: 1`, a `pre-commit` hook that refuses the finalize commit twice: exactly one hook fix-it turn is delivered, then the item stops with refusal code `fix-it-cap-reached`, `NEEDS_INPUT_KEY` true, the report section present, the event present; (b) a two-item Set with `per_set_floor: 1`, `per_set_per_member: 0`: the first item's fix-it turn spends the Set cap and the second item's first fix-it request is refused naming `per-set`; (c) the run cap: two singleton Sets with `per_set_floor: 1, per_set_per_member: 0, per_run_floor: 1, per_run_per_artifact: 0` (so each per-Set limit is 1 and the per-run limit is `max(1, 1, 0) = 1`; per-Set caps CANNOT be made larger than the per-run cap, because the per-run formula takes the largest per-Set limit): the first item's one fix-it turn spends the run cap, and the second item's first fix-it request is refused naming `per-run` (its own Set has spent 0 of 1); (a2) on an integration loop (a merge-conflict send-back with `per_artifact: 0`), the item's refusal names `fix-it-cap-reached` AND its remedy still contains the preserved-branch warning; (d) defaults with one fix-it turn: item executes, no cap section in the report.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the new module and `tests/test_config.py` pass; the existing send-back modules (`tests/test_finalize_sendback.py`, `tests/test_hook_and_suite_fix_it.py`, `tests/test_merge_conflict_sendback.py`, `tests/test_verification_sendback.py`, `tests/test_production_correction_turn.py`, `tests/test_retry_class_mapping.py`) pass unchanged; the bare suite shows no new failure against the lane baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Retry deciders DECIDE ONLY (no state write, no print); performers (`handle_turn_failure_retry`, `handle_finalize_refusal`, `handle_zero_work_retry`, `handle_verification_refusal`) spend and record. The new cap decider follows the same split (`FinalizeRetryDecision` docstring).
- Budgets are FROZEN into `state["options"]` at queue build and read back through a `frozen_*` reader, never re-resolved from `args` (`frozen_retry_budget` docstring; `initialize_run_core` comment "`repo=repo` is load-bearing").
- Repository policy under `run.*` in `.aw/config/project.json` warns and falls back on a malformed value, never refuses (`config.policy_retry_budget`, maintainer decision 2026-09-10).
- Terminal statuses are a CLOSED vocabulary (`runner_shutdown.KNOWN_ITEM_STATUSES`, `TURN_RETRY_EXHAUSTED_STATUS` docstring): reuse an existing status, never invent one.
- Refusals go through the ONE writer `render_stream.record_refusal` and are read through `refusal_of_item`, so the summary renders them with no new reader.
- Needs-human is expressed by `NEEDS_INPUT_KEY` on the queue entry, which `aggregated_run_items` maps to `needs_input` and exit 3.
- Tests drive both hosts through `execute_item` with scripted hooks and hosts in a scratch repo (`tests/test_hook_and_suite_fix_it.py` precedent); no code-pinning (AGENTS.md P16).
- A plan that changes behavior a spec describes amends the spec in the same change and declares it in `- Scope-Paths:` (AGENTS.md "A PLAN MAY AMEND A SPEC").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Every fix-it counter is compared against the WHOLE frozen budget independently, so total spend per item is `budget x kinds`. | `finalize_retry_decision`, `turn_retry_decision`, `zero_work_retry_decision`, `verification_retry_decision`, `production_set_retry_decision`, `review_orchestrator_retry_decision` each read `budget = frozen_retry_budget(state)` and compare their own counter; the inline loops in `execute_item_core` compare `MERGE_CONFLICT_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY` against `frozen_retry_budget(state)`. |
| F-02 | Ten per-kind counter keys exist today. | `rg "_RETRY_COUNT_KEY: str"` lists TURN, FINALIZE, HOOK_FINALIZE, HOOK_INTEGRATION, COMBINED_RED, MERGE_CONFLICT, VERIFICATION, PRODUCTION_SET, REVIEW_ORCHESTRATOR, plus `ZERO_WORK_RETRY_COUNT_KEY: str = "zero_work_retries"`. |
| F-03 | The gate-answer re-run spends a resumed agent turn per re-run against the same budget, recorded only on the gate-answer record. | `perform_gate_answer`: "if rerun_suite is None or attempts >= budget"; `gate_answer_record(... recheck_attempts=attempts, recheck_budget=budget ...)` under `GATE_ANSWER_RECORD_KEY`. |
| F-04 | No aggregate bound exists per Set or per run; nothing else caps dispatch. | `finalize_retry_decision` docstring: "NOTHING ELSE bounds it. `max_items_per_session` rotates the SESSION, it does not cap dispatch". |
| F-05 | Spec 5.5 is the single normative home for the correction-budget bound, so a new bound must be stated there. | Spec `25kzda` 5.5: "This section is the single normative home where the correction-budget bound and its three-tier precedence are defined". |
| F-06 | Set `fixfirst` explicitly deferred global caps to this backlog item. | `fixfirst` orchestrator `lxb1ew` Scope: "EXCLUDES, in every child: ... global fix-it caps across kinds (backlog `38hwvk`)". |
| F-08 | The gate-answer record on the item is REPLACED per attempt, not accumulated (added at review). | `execute_item_core`: `attempt[GATE_ANSWER_RECORD_KEY] = gate_outcome.record` then `item[GATE_ANSWER_RECORD_KEY] = gate_outcome.record`; `perform_gate_answer` starts `attempts = 0` on every call. Hence E-03's cumulative `GATE_ANSWER_RETRY_COUNT_KEY`. |
| F-09 | Integration refusals carry a preserved-branch remedy a cap stop must not drop (added at review). | `render_stream.record_integration_refusal` remedy: "the verified work is PRESERVED on branch {branch} ... Do NOT delete the branch or discard the lane: that is the one irreversible move here"; `render_stream.record_refusal` overwrites `item[REFUSAL_KEY]`. |
| F-07 | The orchestrator-readiness probe receives `retry_budget=frozen_retry_budget(state)` but its retries are model probes, not agent fix-it turns. | `orchestrator_readiness.review_readiness(..., retry_budget=frozen_retry_budget(state), ...)` in the retirement path; `production_checks` reads `retry_budget` for the same probe. |

## Proposed changes (ordered, validatable)

1. Policy accessor with warn-and-default posture (E-01).
2. Freeze caps into run state; resume-safe reader (E-02).
3. Census of spend and limit computation (E-03).
4. Pure cap decider (E-04).
5. Enforce in the six deciders (E-05) and the four inline loops (E-06).
6. Needs-human stop, event, and report section (E-07).
7. Spec 5.5 amendment (E-08) and changelog (E-09).
8. Behavioral tests on both hosts (E-10).

## Deferred / out of scope (with reason)

- A CLI flag for the caps (OQ-02). Repository policy satisfies "each configurable"; a flag would amend spec 2.1's grammar block and `RUN_POLICY_FLAGS`.
  - Carrier-Declined: NOT WANTED unless a reviewer or the maintainer asks; backlog `38hwvk` requires only that each cap be configurable, which `run.fix_it_caps` satisfies.
- Capping first attempts or stopping un-started Set members when the Set cap is reached (OQ-01).
  - Carrier-Declined: NOT WANTED; backlog `38hwvk` defines all three caps in fix-it turns, and a first attempt is not one.
- The one-shot follow-up turns `perform_defect_reask` ("THIS FUNCTION NEVER LOOPS; boundedness is structural") and `perform_carrier_verification` (`carrier_verification_asked`, at most one per attempt). Recorded at review so the omission is a decision rather than an oversight.
  - Carrier-Declined: NOT AN OBLIGATION; each is structurally at most one per attempt, and attempts are themselves bounded by the capped fix-it counters, so neither can multiply spend independently. They are neither counted nor refused.
- `--integration-retry-limit` re-attempts and orchestrator-readiness probe retries.
  - Carrier-Declined: NOT AN OBLIGATION; they spend no agent fix-it turn (spec 2.1 "an integration re-attempt ... spends no agent turn"; F-07), so capping them is outside the backlog item's definition.

## Scope check

- Over-scope: none. `config.py` E-01; `runner_shared.py` E-02 to E-07; `oc_runipd.py`/`agy_runipd.py` only if a host wrapper must forward `fix_it_cap` facts or `host_labels` to E-07 (declared so that need is not a scope violation); `tests/test_fix_it_global_caps.py`, `tests/test_config.py` E-10; spec E-08; `CHANGELOG.md` E-09.
- Under-scope: a counter added by a later plan is only capped if it is added to `FIX_IT_COUNT_KEYS`; E-03 re-derives the list at execution, and the constant's comment must say a new per-kind counter belongs there.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_fix_it_global_caps.py tests/test_config.py tests/test_finalize_sendback.py tests/test_hook_and_suite_fix_it.py tests/test_merge_conflict_sendback.py tests/test_verification_sendback.py tests/test_production_correction_turn.py tests/test_retry_class_mapping.py tests/test_runner_shared.py`.
- Bare `python3 -m pytest`, with the baseline re-derived in the lane before any edit.
- `aw check` and `aw ipd lint` on this plan.

## Spec / documentation sync

THIS PLAN AMENDS spec `25kzda` (approved), declared in `- Scope-Paths:`, Section 5.5 only (E-08). WHY: Section 5.5 declares itself the single normative home of the correction-budget bound (F-05), so a new aggregate bound stated only in code would make the spec silently false about how many fix-it turns a run may spend; group (b) and its table row must also name the new stop reason. `CHANGELOG.md` gets one user-facing line (E-09). No other doc names the per-kind budget's arithmetic (`docs/recovery.md` mentions only that driver runs "use their own retry substrate").

## Open questions

### OQ-01: When the per-Set or per-run cap is reached, do remaining un-started items still get their FIRST attempt?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. The backlog defines all three caps as counts of "fix-it turns" and says "the item (or the remaining Set/run work) stops as needs-human". A first attempt is not a fix-it turn and can succeed outright, so the caps refuse only further FIX-IT turns: any item (started or not) that would need one after its Set or run cap is reached stops needs-human. This is the reading that the backlog's own unit supports and the least disruptive one; if the maintainer wants a reached cap to also halt dispatch of un-started members, that is an additive change in the selection loop of `oc_runipd.run_queue`/`agy_runipd.run_queue` and can be raised at review.

### OQ-02: CLI flags for the caps, or repository policy only?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Repository policy only (`run.fix_it_caps`), frozen per run. The backlog asks that each cap be "configurable" without naming a surface; the repository already configures the per-kind budget's middle tier there (`config.policy_retry_budget`). A CLI flag would extend spec 2.1's grammar block and `RUN_POLICY_FLAGS` (whose rows must follow the grammar block's order), widening this low-priority item's public surface. Deferred as an additive follow-up if the maintainer wants it.

### OQ-03: Which "number of Set members" counts toward the per-Set cap?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The members of that Set present in THIS run's frozen queue, because the cap bounds what this run spends and only queued members can spend; an on-disk member not in the run spends nothing. The queue is frozen at build, so the number is stable across resume.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the pytest output of the `tests/test_config.py` cases for `policy_fix_it_caps` (defaults, partial override, malformed plus unknown member) and the captured warning text naming key, value and file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `options.fix_it_caps` object from a test run's `state.json`, and the test output proving a resume after a policy edit keeps the frozen values and that `frozen_fix_it_caps({"options": {}})` returns the defaults.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the test output for `fix_it_turns_spent` (4 for the mixed item including a gate-answer re-run), the test showing two successive gate answers accumulate in `gate_answer_retry_attempts` rather than overwrite, a limit computation that excludes an `action: skip` entry, and `fix_it_cap_limits` (`(20, 45, 50)` and `(20, 20, 40)`), and the final `FIX_IT_COUNT_KEYS` value with the `rg` command output used to re-derive it at execution.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the test output for `fix_it_cap_decision` returning each of `per-artifact`, `per-set`, `per-run`, the not-reached case and the cap-0 case, including one rendered `reason` string.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the test output showing each of the six deciders returns `exhausted=True` with a cap-naming reason when the cap is reached and `retry=True` when not, and that a non-retryable class is unchanged with the cap reached.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test output (produced through `execute_item_core` on both hosts, the code path E-06 edits) showing zero merge-conflict send-backs under `per_artifact: 0` with `attempt["fix_it_cap"]` naming `per-artifact`, and the unchanged loop behavior when the cap is not reached; paste the `perform_gate_answer` cap case.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: from E-10 end-to-end case (a) on both hosts (`oc_runipd.execute_item` / `agy_runipd.execute_item`, then `runner_shared.run_exit_code(state["queue"], stopped=False)` for the exit code, which is the function `run_queue` uses, then the host `write_report`), paste the run exit code 3, the rendered summary lines containing `fix-it-cap-reached` and `per-artifact`, the `## Fix-it caps` section of `execution-report.md`, the single `fix-it-cap-reached` event line from `events.jsonl`, and case (d)'s report showing no such section; paste case (a2)'s refusal `remedy` showing both the cap remedy and the preserved-branch warning.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `git diff --stat` and the Section 5.5 hunk of the spec diff, the appended workflow-history line, and `aw check` output showing no new finding for the spec.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the added `CHANGELOG.md` line and the empty output of a dash search over it.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the ACTUAL output of the targeted pytest command in Required tests (with the `N passed` line), the end-to-end cases (a) to (d) passing on both hosts, and the bare `python3 -m pytest` summary line compared with the lane baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. No `- Item-Dependencies:`: the caps compose with whatever per-kind counters exist at execution; E-03 re-derives the counter list so a counter added by pending `fixfirst` plans `ytas91` or `62sdwr` is included whichever order they land in.

Execution contract:
- All open questions are resolved; a reviewer may reopen OQ-01 or OQ-02.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
