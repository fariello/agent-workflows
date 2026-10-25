# IPD: Give a stalled, crashed or unstarted backlog or spec production turn a fix-it turn in its own lane and session

- Date: 2026-10-23
- Kind: child
- Concern: A backlog or spec PRODUCTION turn (queue action `plan`: an agent graduating a backlog item or a spec into plans) that stalls, crashes or fails to spawn gets NO fix-it turn. Executed plan `ytas91` (Set `fixfirst`, Order 04) built exactly that recovery for EXECUTE turns: mark the failure kind, re-queue under the frozen `--retry-budget`, re-enter the failed attempt's own lane, resume its own session, and tell the agent what happened. But all three of its retry sites in `runner_shared.execute_item_core` are guarded `if not is_review and not is_production:` (the `StallTimeout` arm, the spawn-failure arm, and the post-turn `handle_turn_failure_retry` call), and the lane re-adoption block that reads `is_fix_it_recovery` sits inside the execute-only `if self_finalize and not is_review and not is_production:` branch. Measured on run `run-20261023T221924Z-2698768` (backlog `l9ssp6`, action `plan`): the agent ran normally for about two minutes, then the host emitted nothing for 1800s; the watchdog killed the turn; the attempt recorded `turn_failure_kind: stall` and a non-null `session_id` (so `ytas91` E-07 worked) but carried no `turn_retry_skipped` and no `turn_correction` key, proving `handle_turn_failure_retry` never ran; the item ended `interrupted`; the run-end reclaim tore the empty lane down (`lane-reclaimed-at-run-end`, `state: EMPTY`); $0.40 of work, including two recorded mutation-probe verdicts, was left only in the session log. Recovery is then a full restart in a fresh session. Separately, the run's `execution-report.md` still listed that lane under "Preserved lanes (NOT torn down)" after the reclaim removed it, because `lane_containment.format_preserved_lanes` renders from the item's `preserved_*` fields and the reclaim never clears them. Nothing records WHY production turns were excluded: the `is_production` half of the guard arrived with commit `45fbdb53d` (plan `aeq7f8`, spec production dispatch), and neither `aeq7f8` nor `ytas91` discusses it, while spec `25kzda` Section 5.5 group (a) lists "host spawn failure", "nonzero exit or no outcome file" and "stall or turn-limit expiry" as fix-it classes with no action restriction.
- Scope: IN: make a production turn (`is_spec_production` or `is_backlog_production`) that ends in a stall, a turn-limit expiry, a nonzero exit with no outcome, or a spawn failure reach `handle_turn_failure_retry` under the existing frozen `--retry-budget` and the global fix-it caps; on the resulting recovery dispatch, re-adopt the failed attempt's own production lane and resume its own session when both are safe (the `ytas91` E-05 predicate: worktree exists, registered, `worktree_lease.lane_is_safe_to_adopt`, prior `session_id` present), else fall back to today's fresh lane and fresh session and record which branch was taken in `attempt["fix_it_lane"]`; keep a lane that is awaiting a fix-it turn (production or execute, since the reclaim loop is shared) out of the run-end and interrupt reclaim; persist the FIRST attempt's production baseline (`baseline_plan_ids`, `continued_plan_ids`) on the item so a resumed attempt does not mistake its own earlier uncommitted plans for pre-existing ones; render the correction notice into the production prompt on a recovery dispatch; clear the `preserved_*` record when a lane is reclaimed so the report stops listing a destroyed lane; tests on both hosts; spec `25kzda` Section 5.5 amendment. EXCLUDES review turns (they share one sweep session and one sweep lane across every review, and their recovery is owned by the integration deferral ladder per the `retrywire` comment above the post-turn call); EXCLUDES changing the budget, the caps, `turn_failure_is_retryable`, `turn_retry_decision` or `turn_correction_packet`; EXCLUDES the Set-level production correction loop (`production_set_retry_decision`, plan `nnsa2o`), which keeps its own counter; EXCLUDES the first-dispatch fresh-session rule (`lanesess` `xd9sll`); EXCLUDES the stall cause itself (a host that goes silent between tool calls; cause unknown). ALSO IN (added at review, F-13): a stall of a Set-level production CORRECTION turn, which today re-raises out of `execute_item_core` and lands in the host loop's generic `except DriverError` as `failed-safely` with no fix-it turn (E-14). ALSO IN (F-12): the persisted baseline covers a fix-it attempt in the SHARED tree (`--no-isolate-worktree`), where the failed attempt's uncommitted plans are otherwise dropped as pre-dirty and reported out-of-scope.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_production_fix_it.py, tests/test_turn_fix_it.py, tests/test_production_correction_turn.py, tests/test_gradcover_end_to_end.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- From-Spec: 25kzda
- Set: prodfixit
- Order: 1
- Highest E allocated: 14
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ob7aq9

## Workflow history
- 2026-10-25 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ob7aq9 verified (set prodfixit, attempt 1). [Scope reconciliation - widened-scope agent_workflows/agy_runipd.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope agent_workflows/oc_runipd.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope tests/test_gradcover_end_to_end.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); in-scope-unmodified tests/test_production_correction_turn.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_turn_fix_it.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-24 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED (2 HIGH: Set-correction-turn stall added as E-14; explicit live-attempt admission at post-turn site). Review record .aw/records/reviews/20261023-prodfixit-01-ob7aq9-give-a-stalled-crashed-or-unstarted-backlog-or-spec-producti.review.md
- 2026-10-24 to-review (aw set): authored from maintainer request 2026-10-23 after run-20261023T221924Z-2698768 (l9ssp6 stall)

- 2026-10-24 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a backlog or spec production turn stalls, crashes or never starts, the runner hands it back to the same agent, in the same lane and the same session where that is safe, with a message saying what happened, instead of marking it `interrupted` and discarding the lane.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline before any edit

- [x] E-02 RE-DERIVE at execution HEAD, before editing, and record the HEAD sha. (1) Confirm the three `if not is_review and not is_production:` guards in `runner_shared.execute_item_core` that precede `handle_turn_failure_retry(` (the `except StallTimeout as stall_exc:` arm, the spawn-failure `except (FileNotFoundError, PermissionError, OSError, HostSpawnError)` arm, and the post-turn call under the `retrywire (`xipfy1`)` comment) and that the `elif is_fix_it_recovery and prev_attempt is not None:` lane re-adoption block is reachable only inside `if self_finalize and not is_review and not is_production:`. (2) Reproduce the defect with a scripted host on BOTH hosts: a backlog production item (action `plan`, isolated lane) whose first turn raises `StallTimeout(..., session_id="ses-p1")` ends `interrupted`, its attempt carries `turn_failure_kind: stall` and `session_id: ses-p1`, and carries NEITHER `turn_retry_skipped` NOR `turn_correction`; paste that attempt record. (3) Run `python3 -m pytest -o addopts="" tests/test_turn_fix_it.py tests/test_production_correction_turn.py tests/test_production_resume_handoff.py tests/test_spec_production.py -q` and record the counts. If any fact differs, record CORRECTED with the measured value and adjust the later items before editing.
  - Depends on: none
  - Expected outcome: the defect is reproduced on both hosts at execution HEAD and the baseline counts are recorded.
  - Execution state: performed

### Task group 2: route a failed production turn to the fix-it decision

- [x] E-03 In `runner_shared.execute_item_core`, widen the three retry guards from `if not is_review and not is_production:` to `if not is_review:` so a spec or backlog production turn reaches `handle_turn_failure_retry` on a stall, a turn-limit expiry, a nonzero exit, a missing outcome, or a spawn failure. Keep review turns excluded and update the `retrywire` comment above the post-turn call to say why reviews stay out and why production is in (spec `25kzda` 5.5 group (a) has no action restriction; the production Set correction loop keys on Set findings, a different class, so the two cannot double-count). AT THE POST-TURN SITE, ADMIT ONLY A TURN WHOSE ATTEMPT CARRIES `turn_failure_kind`: a production turn that exited 0 and was refused by a Set or count finding (`BACKLOG-GRADUATE-SET`, `BACKLOG-GRADUATE-COUNT`, `SPEC-PLAN-*`) is `fail-gate`, which is already outside `TURN_RETRYABLE_DISPOSITIONS`, and must stay owned by `production_set_retry_decision`. Do not edit `turn_failure_is_retryable` or `turn_retry_decision`. THE ADMISSION MUST BE EXPLICIT, NOT INFERRED, because `turn_failure_is_retryable` reads the LAST entry of `item["attempts"]` and the production Set correction loop APPENDS its `corr_rec` (`"action": "production-set-correction"`, no `turn_failure_kind`) to `item["attempts"]`; so for a production item the post-turn call is made only when the LIVE `attempt` dict carries `turn_failure_kind`, and otherwise the site records `attempt["turn_retry_skipped"]` with a reason naming the Set correction loop and passes `disposition` through unchanged. Do not rely on the last-attempt read to keep Set findings out.
  - Depends on: E-02
  - Expected outcome: a stalled, crashed or unstarted production turn records a `turn_correction` packet and `turn_retry_attempts == 1`, or is `failed-safely` with a `turn-retry` refusal when the budget is 0; a production `fail-gate` from Set findings records `turn_retry_skipped` and is otherwise unchanged.
  - Execution state: performed

- [x] E-04 Mark a production turn's nonzero exit with the same failure kind an execute turn gets. The post-turn block that sets `attempt["turn_failure_kind"]` to `turn-limit`, `no-outcome` or `nonzero-exit` already runs for every action; verify by the E-02 scripted host that a production turn returning exit code 1 records `no-outcome` (production turns write no outcome file), and that the `BACKLOG-PRODUCTION-FAILED` / `SPEC-PRODUCTION-FAILED` finding it also produces does not route the item into `production_set_retry_decision` (it is not in `PRODUCTION_SET_RETRYABLE_FINDING_CODES`). If either does not hold, make it hold without changing the finding codes.
  - Depends on: E-03
  - Expected outcome: a crashed production turn reaches the turn fix-it decision exactly once and the Set correction loop not at all.
  - Execution state: performed

### Task group 3: resume in the failed lane and session

- [x] E-05 Re-adopt the failed production lane and resume its session on a fix-it dispatch. In the `if (is_spec_production or is_backlog_production) and isolate:` allocation block, detect a fix-it recovery exactly as the execute branch does (`recovery` is true and the previous attempt carries `turn_failure_kind` and `turn_correction`) and, when the prior worktree exists, is registered (`worktree_lease.inspect_lane(...).worktree_registered`), is safe to adopt (`worktree_lease.lane_is_safe_to_adopt`), and the prior attempt carries a `session_id`, use that worktree with `disposition="adopted"`, write the lane owner, set `session_id` to the prior session and `use_continue = False`, and record `attempt["fix_it_lane"] = "resumed"`; otherwise allocate as today with a fresh session and record `attempt["fix_it_lane"] = "fresh: <reason>"`. EXTRACT the execute branch's predicate and adoption body into one shared helper called from both branches rather than copying it, so the two cannot drift. A FIRST dispatch is unchanged (fresh lane, fresh session).
  - Depends on: E-03
  - Expected outcome: the recovery attempt of a stalled production item runs in the same worktree path as the failed attempt with the failed attempt's session id passed to the launcher (`resume_session` on oc, `session_id` with `use_continue=False` on agy), or records a `fresh:` fallback reason.
  - Execution state: performed

- [x] E-06 Keep a lane that is awaiting its fix-it turn. A preservation RECORD does not protect a lane: on the measured run the stall arm called `lane_containment.record_lane_preserved` (`retention_reasons: ["stall-timeout"]`) and one second later `runner_shared.reclaim_lanes_on_interrupt` (mode `run-end`) tore the same lane down as provably EMPTY, because its loop decides on the lane's classified state (`LANE_EMPTY`, `reclaimable`) and never on the item. Inside one live run this does not bite, since the recovery dispatch runs before run end; it bites when the run is stopped, interrupted or exits between the failed attempt and its fix-it dispatch, which then strands the item with no lane to re-enter. So: in `reclaim_lanes_on_interrupt`, before any teardown branch, skip a lane whose owning item (`interrupt_lane_item_record`) is `queued` with `recovery_next` and whose NEWEST attempt CARRYING `turn_correction` (search backwards; do not read only `attempts[-1]`) names that lane as its `worktree`; record `lane["action"] = "kept-for-fix-it"` and emit a `lane-kept-for-fix-it` event naming the item. This applies to execute and production lanes alike (an execute fix-it lane has the same hole). It never destroys anything and only declines a removal, so it needs no inventory gate. Do NOT clear the item's `preserved_*` fields on this branch (E-09 clears only on a real teardown), so the report still lists the kept lane. Place the check AFTER the existing `lane.get("owned_by_other_live_process")` skip so a lane owned by a different live process is still left alone first. Also confirm the stall arm's existing `worktree_lease.snapshot_lane_dirty_work` call commits a stalled attempt's uncommitted plan file onto the lane branch, and record (F-14) that the snapshot commit is integrated to main with the lane: state in the `retrywire` or E-05 helper comment that this is intended, since its content is the agent's own plan files.
  - Depends on: E-05
  - Expected outcome: a lane whose item is queued for a fix-it turn survives a run-end or interrupt reclaim, and the next `aw oc run resume <run-id>` re-adopts it.
  - Execution state: performed

- [x] E-07 Persist the production baseline across attempts. `baseline_plan_ids` and `continued_plan_ids` are computed from the lane at the START of each attempt and feed `commit_backlog_production_output` / `commit_spec_production_output` and `production_checks.backlog_graduate_count`, which treat a plan id in the baseline as PRE-EXISTING. On a resumed lane the failed attempt's own uncommitted or snapshot-committed plans would land in the baseline and be classified out-of-scope or not-new. Record the first attempt's two sets on the item (for example `item["production_baseline"] = {"plan_ids": [...], "continued_ids": [...]}`), written ONCE (never overwritten by a later attempt) and saved with `save_state` before the turn launches, and use the recorded sets instead of recomputing on (a) a `fix_it_lane == "resumed"` attempt and (b) a SHARED-TREE fix-it attempt (`wt_handle is None`, recovery dispatch whose previous attempt carries `turn_correction`), where the failed attempt's uncommitted plans sit in the primary checkout (F-12); on (b) the `continued-plan-pre-dirty-dropped` filter must not drop a plan the recorded baseline lists as this item's own continued plan. A fresh-lane fallback recomputes as today (the fresh lane starts from main and holds none of the failed attempt's files). A plan the failed attempt had already committed to the lane before stalling is not in the recorded baseline either, so it is treated as new output, which is correct.
  - Depends on: E-05
  - Expected outcome: a plan the failed attempt wrote and the resumed attempt finishes is committed by the driver as new output and counted by `BACKLOG-GRADUATE-COUNT`, not reported out-of-scope.
  - Execution state: performed

- [x] E-08 Deliver the correction to the production agent. `build_spec_production_prompt` and `build_backlog_production_prompt` are called without the recovery notice the execute prompt gets through `build_prompt`. On a recovery dispatch whose previous attempt carries `turn_correction`, prepend `build_correction_notice(item, recovery=True)` to the production prompt text (the same rendered packet: failure kind, exit code, stall timeout, lane heads and status, log path). THERE ARE TWO production prompt build sites and BOTH must carry it: the pre-lane build (`elif is_spec_production:` / `elif is_backlog_production:` before lane allocation) and the lane rebuild under `if work_dir and (is_spec_production or is_backlog_production):`, which OVERWRITES the first and is the one written to `prompts/` on an isolated run; apply the notice in one helper called from both so neither drifts. When the session is resumed, the notice is the whole prompt body's lead, so a resumed agent reads "you stalled after N seconds; the lane is as you left it; finish" before anything else. A first attempt's prompt is byte-identical to today.
  - Depends on: E-03
  - Expected outcome: the recovery prompt file under `prompts/` for a production fix-it attempt begins with the correction notice naming `Failure kind: stall`, and a first-attempt prompt contains no such notice.
  - Execution state: performed

- [x] E-14 Give a stall inside the Set-level production CORRECTION turn the same fix-it route (F-13). Both production correction loops (spec and backlog) wrap `resume_via_launcher` in `except (KeyboardInterrupt, StallTimeout): raise`, which sends the stall out of `execute_item_core` to the host loop's `except DriverError` and records only `failed-safely` plus `driver_error`. Replace the `StallTimeout` half with handling that records on the LIVE `attempt` what the first-turn stall arm records (`interrupt_reason: stall_timeout`, `turn_failure_kind: stall`, the stalled `session_id` from the exception when present, `stall_timeout`), snapshots and preserves the lane through the same calls the first-turn stall arm uses, then calls `handle_turn_failure_retry` with disposition `interrupted` and returns. Extract the stall arm's body into one helper used by both sites rather than copying it. Keep `KeyboardInterrupt` re-raised unchanged. The Set correction counter already spent for this turn stays spent (it bought a turn that ran); the turn counter is charged once for the stall. On the recovery dispatch the item re-enters through E-05 (same lane, same session).
  - Depends on: E-03, E-05
  - Expected outcome: a production item whose Set correction turn stalls records `turn_failure_kind: stall` and `turn_correction` on its attempt, is re-queued with `recovery_next`, and its `driver_error` is absent; a `KeyboardInterrupt` there still propagates.
  - Execution state: performed

### Task group 4: report a reclaimed lane honestly

- [x] E-09 Clear the preservation record when a lane is reclaimed. In `runner_shared.reclaim_lanes_on_interrupt`, on every `decision.torn_down` branch (the recovered branch and the run-end branch), clear that item's `preserved_worktree`, `preserved_branch`, `preserved_lane_id`, `preserved_base`, `preserved_disposition`, `preserved_reason` and `preserved_retention_reasons` (one helper in `lane_containment`, beside `record_preserved_lane_state`, clearing every field that function writes) and save state before the report is written, so `format_preserved_lanes` no longer lists a lane that no longer exists. CLEAR ONLY WHEN THE RECLAIMED LANE IS THE ONE RECORDED: compare the lane's `branch`/`worktree` with `preserved_branch`/`preserved_worktree` and leave the record untouched when they differ (an item can own several lanes across attempts, and `_lane_records_from_state` yields one record per lane). An inline clear of the same keys already exists in the deferred-integration `_finish` closure (`for key in ("preserved_worktree", ...): item.pop(key, None)`); replace it with a call to the new helper so there is one definition. Both callers (`oc_runipd.run_queue` and `agy_runipd.run_queue`) already `save_state` after `reclaim_run_lanes` and before `write_report`; verify that holds on the interrupt path too and add the save there if it does not. Leave the `lane-reclaimed-*` event as the durable record that it existed.
  - Depends on: E-02
  - Expected outcome: a run whose stalled lane is reclaimed at run end writes an `execution-report.md` with no "Preserved lanes (NOT torn down)" entry for it; a lane that is preserved still appears.
  - Execution state: performed

### Task group 5: tests, spec and changelog

- [x] E-10 Add `tests/test_production_fix_it.py`, driving the real `run_queue` on BOTH hosts with a scripted launcher (the `_patch_host_agent` / `initialize_run` pattern in `tests/test_production_correction_turn.py`, with an isolated lane), and asserting on state, events, prompt files and the worktree list: (1) backlog production stall then success: attempt 1 `turn_failure_kind: stall`, attempt 2 `fix_it_lane: resumed`, same worktree path, launcher received the stalled session id, item ends `executed`, backlog item `graduated`, `turn_retry_attempts == 1`; (2) the stalled attempt wrote one child plan before stalling and the resumed attempt writes the orchestrator: both plans are committed as new output and no `backlog-production-out-of-scope-paths` event names them (E-07); (3) spec production nonzero exit then success; (4) spawn failure exhausts the budget, item `failed-safely` with a `turn-retry` refusal, the next queued item still runs; (5) budget 0: no fix-it turn, item `failed-safely`; (6) fallback: prior lane removed between attempts gives `fix_it_lane` starting `fresh:` and a fresh session; (7) a Set-finding refusal on an exit-0 turn is still corrected by `production_set_retry_decision` and records `turn_retry_skipped` (no double count); (8) the recovery prompt file starts with the correction notice and the first-attempt prompt does not; (9) run ends after the stall and before the retry: drive this either by a between-turn stop request (`runner_stop.request_stop(run_dir, runner_stop.LEVEL_AFTER_CALL, ...)` issued from inside the stalling scripted launcher, so the loop's checkpoint stops before the recovery dispatch) or, if that path does not reach run-end reclaim, by calling `reclaim_run_lanes` directly on the post-stall state; either way the lane survives with a `lane-kept-for-fix-it` event and no `lane-reclaimed-*` event, and a following `run_queue` on the same run dir (the `resume` entry) dispatches attempt 2 with `fix_it_lane: resumed` in that lane; record which drive was used; (10) a review item that stalls still ends `interrupted` with no `turn_correction`; (11) a stall inside the Set-level production correction turn (E-14): the item records `turn_failure_kind: stall` and a `turn_correction`, not a bare `driver_error`; (12) shared tree (`--no-isolate-worktree`): a backlog production turn writes one plan and then exits 1; the fix-it attempt completes and that plan is committed as new output with no `backlog-production-out-of-scope-paths` or `continued-plan-pre-dirty-dropped` event naming it (E-07 branch (b)). Extend `tests/test_turn_fix_it.py` or `tests/test_production_correction_turn.py` only if an existing case asserts the old production behavior. No source introspection.
  - Depends on: E-03, E-04, E-05, E-06, E-07, E-08, E-14
  - Expected outcome: all twelve cases pass on both hosts and the E-02 baseline modules still pass.
  - Execution state: performed

- [x] E-11 Add a test for E-09: a run whose stalled production lane is reclaimed at run end (budget 0, so no fix-it turn and nothing kept for one) produces an `execution-report.md` with no `## Preserved lanes (NOT torn down)` section, and a run whose lane is preserved (a lane holding unmerged commits) still shows it. Put it in `tests/test_production_fix_it.py`.
  - Depends on: E-09
  - Expected outcome: the report reflects what is on disk in both cases.
  - Execution state: performed

- [x] E-12 Amend spec `25kzda` Section 5.5: state in the group (a) prose that the host-failure fix-it classes apply to execute AND production (spec and backlog) turns and not to review turns, with the reason (a review turn shares the sweep session and sweep lane, and its recovery is the integration deferral ladder); update the "stall or turn-limit expiry" row's Notes to name this plan; record that a production fix-it turn re-adopts its own lane and resumes its own session as an execute fix-it turn does, and that a lane awaiting a fix-it turn is kept by the run-end reclaim. Record the amendment with `aw specs note <spec-path> --message ...` on the spec (it writes the `## Workflow history` line; the spec stays `approved`). Add one CHANGELOG `Fixed:` line in plain user-facing language with no em or en dashes: a backlog or spec planning turn that stalls, crashes or fails to start is now handed back to the same agent session to finish, and the run report no longer lists a removed lane as preserved.
  - Depends on: E-10
  - Expected outcome: the spec and the code agree on which actions get host-failure fix-it turns; the CHANGELOG names the user-visible change.
  - Execution state: performed

- [x] E-13 Run the bare routine gate `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`, and paste the summary lines. If the core-tier budget check prints `CORE TIER BUDGET EXCEEDED`, paste the block verbatim; it is not counted against this plan unless a test this plan added is among the listed slowest tests.
  - Depends on: E-10, E-11, E-12
  - Expected outcome: both suites pass and the sanitizer reports no leak.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `runner_shutdown.KNOWN_ITEM_STATUSES` and both drivers' `TERMINAL_STATES` are closed vocabularies: this plan adds attempt and item FIELDS (`fix_it_lane`, `production_baseline`) and a retention reason code, never a status.
- `queued` plus `recovery_next` is the established re-dispatch pattern, written by `handle_turn_failure_retry`; this plan reuses it unchanged.
- Each send-back owns its own counter (`TURN_RETRY_COUNT_KEY`, `PRODUCTION_SET_RETRY_COUNT_KEY`, `FINALIZE_RETRY_COUNT_KEY`, the verification key). A class owned by one must not be charged to another; E-03 and E-04 keep the turn counter off Set findings.
- Sessions never cross worktrees (`lanesess` `xd9sll`, executed `r0iob3`); a resume is legal only in the lane the session ran in, which is what `ytas91` E-05 enforces and what E-05 reuses.
- Every lane removal goes through the R5.5 inventory gate (`reclaim_lane_through_gate`); E-06 prevents a removal, and E-09 only clears a record after a removal the gate already approved.
- Tests drive `run_queue` with a scripted launcher (`tests/test_turn_fix_it.py`, `tests/test_production_correction_turn.py`), never source reads (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | All three turn-failure retry sites exclude production turns. | `runner_shared.execute_item_core`: `if not is_review and not is_production:` precedes each `handle_turn_failure_retry(` call (spawn-failure arm, `except StallTimeout as stall_exc:` arm, post-turn call under the `retrywire (`xipfy1`)` comment); `is_production = action == "plan"`. |
| F-02 | The lane and session resume for a fix-it turn exists but only on the execute branch. | The `elif is_fix_it_recovery and prev_attempt is not None:` block (sets `attempt["fix_it_lane"] = "resumed"`, `session_id = prior_session_id`, `use_continue = False`) is nested in `if self_finalize and not is_review and not is_production:`; the production branch `if (is_spec_production or is_backlog_production) and isolate:` always calls `allocate_isolation_worktree` and sets `session_id = None`. |
| F-03 | The stalled production attempt already records what a resume needs. | Run `run-20261023T221924Z-2698768` `state.json`, `l9ssp6` attempt 1: `"turn_failure_kind": "stall"`, a non-null `"session_id"`, `"worktree": ".../.aw/worktrees/l9ssp6"`, `"interrupt_reason": "stall_timeout"`; no `turn_retry_skipped`, no `turn_correction`. |
| F-04 | The stalled lane is torn down at run end, so even a manual resume has nothing to re-enter. | Same run `events.jsonl`: `worktree-preserved` (`retention_reasons: ["stall-timeout"]`) at 22:51:47, then `lane-reclaimed-at-run-end` (`state: EMPTY`) at 22:51:48; `git worktree list` shows no `l9ssp6` lane afterwards. |
| F-04b | A preservation record does not stop the reclaim. | Same run: the stall arm's `record_lane_preserved` wrote `worktree-preserved` and the item's `preserved_*` fields, yet `reclaim_lanes_on_interrupt` (mode `run-end`) reclaimed the lane one second later; its loop branches on `lane["state"]`, `reclaimable` and `holds_work` from `describe_lane_with_recovery`, and reads the item only through `interrupt_lane_item_record` for the R5.5 receipt lookup. |
| F-05 | The run report lists the reclaimed lane as preserved. | Same run `execution-report.md`: "## Preserved lanes (NOT torn down)" names `l9ssp6` at `.aw/worktrees/l9ssp6`; `lane_containment.format_preserved_lanes` renders from `item["preserved_worktree"]`, which `record_preserved_lane_state` writes and nothing clears on reclaim. |
| F-06 | A resumed production lane would misclassify the failed attempt's own plans as pre-existing. | `baseline_plan_ids` is filled from `_ce._iter_plan_ipds(baseline_tree)` at each attempt's start; `commit_backlog_production_output` commits a pending plan only when `p_id not in baseline_plan_ids` (or it is a continued plan) and otherwise appends it to `out_of_scope`. |
| F-07 | The production prompt never carries the correction notice. | `execute_item_core` calls `build_spec_production_prompt(...)` / `build_backlog_production_prompt(...)` with no `recovery`; `build_correction_notice` is rendered only through `build_prompt`; and the post-launch `if work_dir and not is_review and not is_production:` prompt rebuild skips production. |
| F-08 | Production turns already resume their own session for a different failure class. | The Set correction loop (`production_set_retry_decision`, plan `nnsa2o`) resumes with `corr_session = attempt.get("session_id")` via `resume_via_launcher` (`resume_session=` on oc, `session_id=` + `use_continue=False` on agy) in the same `work_dir`. Same-session resume of a production turn is therefore established practice, not new risk. |
| F-09 | The spec puts host failures in the fix-it group with no action restriction. | Spec `25kzda` 5.5 group (a): "host spawn failure; nonzero exit or no outcome file; stall or turn-limit expiry"; the mapping table row "stall or turn-limit expiry ... Shipped (Order 04, `ytas91`)". |
| F-10 | The production exclusion was decided but no reason was recorded. (CORRECTED at review: the authored claim that "neither `aeq7f8` nor `ytas91` discusses it" was too strong.) | `git log -S "if not is_review and not is_production:"` earliest hit is `45fbdb53d` "work(aeq7f8): Dispatch an approved spec as a report-only production action". `aeq7f8` E-03 instructed "RESOLVE THE RETRY QUESTION AS A DESIGN DECISION ... Decide it, record it with the reason", and its V-item's Observed evidence records only "retry budget is skipped for production", with no reason. `aeq7f8`'s concern was CONFORMANCE findings (Set and count violations), which this plan keeps out of the turn budget (E-03); host failures were not weighed there. `ytas91`'s plan text never mentions production turns. |
| F-11 | Reviews have a real reason to stay excluded. | `retrywire` comment above the post-turn call: "EXECUTE TURNS ONLY. A review turn's dispositions mean something different ... its refused-integration recovery is owned by the integration deferral ladder"; reviews run in one shared sweep session and lane (`turn_runs_in_review_sweep_lane`, `REVIEW_SWEEP_SESSION_KEY`). |
| F-12 | (Added at review.) A fix-it attempt on the SHARED tree (`--no-isolate-worktree`) loses the failed attempt's plans. | `execute_item_core`: the block guarded `(is_spec_production or is_backlog_production) and wt_handle is None and continued_plan_ids` drops a continued plan whose path is dirty in `git status --porcelain` and emits `continued-plan-pre-dirty-dropped`; a NEW plan the failed attempt left uncommitted in the shared tree has its id in the recomputed `baseline_plan_ids`, so `commit_backlog_production_output` puts it in `out_of_scope` (the `if p_id not in baseline_plan_ids:` test fails and it is not continued). The isolated path is not the only one E-07 must cover. |
| F-13 | (Added at review.) A stall inside the Set-level production CORRECTION turn gets no fix-it turn and loses the attempt record. | The production correction loop's `resume_via_launcher` call is wrapped in `except (KeyboardInterrupt, StallTimeout): raise`; that call sits after the inner `try` whose `except StallTimeout as stall_exc:` arm handles only the first spawn, so the `StallTimeout` leaves `execute_item_core`. `oc_runipd.run_queue` catches it in `except DriverError as exc:` (`StallTimeout` subclasses `DriverError`) and writes `runnable["status"] = "failed-safely"` and `driver_error`; no `turn_failure_kind`, no snapshot, no `handle_turn_failure_retry`. The same arm exists on agy. |
| F-14 | (Added at review.) A resumed lane's snapshot commit is a real lane commit that integration carries to main. | The stall arm's `worktree_lease.snapshot_lane_dirty_work` commits with subject prefix `INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX` ("WIP INTERRUPTED SNAPSHOT (not finished work):") via plumbing; the only reader of that prefix is the recovery classifier (`commit_subject_is_interrupted_snapshot` in `runner_shared`), and the production success path integrates the lane with `integrate_review_lane_branch` (an ff-only-then-no-ff merge). So on a resumed production lane the snapshot commit lands on main as history alongside the driver's `work(<id6>): produce plans` commit. The snapshot's content is the stalled attempt's own plan files, so this is history noise, not wrong content; E-06 records it rather than rewriting history. |

## Proposed changes (ordered, validatable)

1. Re-derive the defect and baseline at HEAD (E-02).
2. Let production turns reach the turn fix-it decision, admitting only host failures (E-03, E-04).
3. Resume the failed production lane and session, keep that lane alive until the retry, carry the baseline across attempts (isolated and shared tree), deliver the correction notice, and route a stalled Set correction turn the same way (E-05 to E-08, E-14).
4. Stop the report from listing reclaimed lanes as preserved (E-09).
5. Tests, spec amendment, changelog, full suites (E-10 to E-13).

## Deferred / out of scope (with reason)

- Review turns stay excluded: they share one session and one lane across the whole sweep, and their recovery is the integration deferral ladder (F-11). Widening them would charge the turn budget for a class another mechanism owns.
  - Carrier-Declined: no work is owed; the exclusion is correct and E-12 records it in the spec.
- The cause of the host going silent between tool calls (F-03) is unknown and is a host behavior, not a runner defect; this plan recovers from it rather than preventing it.
  - Carrier-Declined: no actionable evidence yet; a recurrence with host logs is the trigger for filing.
- An operator-facing `aw oc run resume --reattach` for a stalled turn outside the automatic budget is not built; once E-06 keeps the lane, `aw oc run resume <run-id>` reaches the same fix-it path.
  - Carrier-Declined: covered by E-06 plus the existing `resume` verb.

## Scope check

- Over-scope: none. `runner_shared.py` E-03 to E-09 and E-14; `runner_shared.reclaim_lanes_on_interrupt` E-06; `lane_containment.py` E-09 (clear helper); `tests/test_production_fix_it.py` E-10 and E-11; `tests/test_turn_fix_it.py` and `tests/test_production_correction_turn.py` only if an existing case asserts the old production behavior (E-10); spec `25kzda` and `CHANGELOG.md` E-12.
- Under-scope: `agy_runipd.py` and `oc_runipd.py` are not listed because every site is in the shared `execute_item_core` and the launchers already accept the resume arguments (F-08); if E-05 finds a host-specific gap, edit that host and justify it at finalize.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_production_fix_it.py tests/test_turn_fix_it.py tests/test_production_correction_turn.py tests/test_production_resume_handoff.py tests/test_spec_production.py -v`.
- Invariants and the case pinning each: production host failure gets a fix-it turn (E-10 1, 3, 11); Set findings never charge the turn counter (7); budget 0 and exhaustion fail the item (4, 5); same lane and session only when safe, else fresh (1, 6); a lane awaiting a fix-it turn survives reclaim (9); the failed attempt's plans are new output, isolated and shared tree (2, 12); first-attempt prompt unchanged (8); reviews unchanged (10); report lists only lanes on disk (E-11).
- Bare `python3 -m pytest` and `make test-all`, baselines re-derived in the lane before any edit (E-02).
- `aw sanitize --agent`.

## Spec / documentation sync

Spec `25kzda` Section 5.5 is amended (E-12) because this plan changes which actions receive the group (a) host-failure fix-it turns, which is the contract every runner plan is reviewed against; the spec path is in `- Scope-Paths:` so `aw oc run` / `aw agy run` announce the edit. `CHANGELOG.md` gets one `Fixed:` line. No README change: no command or flag changes.

## Open questions

### OQ-01: Should a production fix-it turn resume the failed session, or start fresh in the preserved lane?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resume the failed session when the lane is safe to adopt, else fall back to fresh. The maintainer asked for exactly this ("send back to the same agent in the same session and just say ... This timed out. Resume please.", session 2026-10-23). It is safe for the reason `ytas91` OQ-02 records: the session is resumed in the same tree it ran in, so `xd9sll`'s cross-tree hazard does not arise, and the production Set correction loop already resumes production sessions (F-08).

### OQ-02: Could a resumed session hang again in the same way?

- Blocking: no
- Status: resolved
- Owner: plan-author
- Resolution or deferral rationale: Possibly, since the stall cause is unknown (F-03). That case is bounded: the resumed turn is under the same stall watchdog, a second stall spends a second budget unit, and the item ends `failed-safely` when the frozen budget (default 2) or a global fix-it cap is reached. The fallback branch also allows a fresh session when the prior one cannot be resumed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [x] V-02 validates E-02
  - Required evidence: the execution HEAD sha; the stalled production attempt record from BOTH hosts (scripted host, before any edit) showing `turn_failure_kind: stall`, the session id, and the ABSENCE of `turn_retry_skipped` and `turn_correction`; the pasted pass/fail counts of the four baseline modules; and CONFIRMED or CORRECTED for each of the fact checks in E-02 (1).
  - Observed evidence:
    Execution HEAD sha: `51d9f5bfaed4cb5d10c799f7acf2afda336a0ce0`.
    Baseline pytest counts:
    `50 passed in 93.53s` (re-tested: `50 passed in 91.56s`).
    Fact checks:
    - CONFIRMED: Three guards `if not is_review and not is_production:` preceded `handle_turn_failure_retry(` in `runner_shared.execute_item_core`:
      (1) stall arm `except StallTimeout as stall_exc:`;
      (2) spawn failure arm `except (FileNotFoundError, PermissionError, OSError, HostSpawnError):`;
      (3) post-turn call under `retrywire (`xipfy1`)` comment.
    - CONFIRMED: Lane re-adoption block reading `is_fix_it_recovery` was inside `if self_finalize and not is_review and not is_production:`.
    Pre-edit reproduction attempt records:
    Opencode host:
    `attempt: {"action": "plan", "disposition": "interrupted", "interrupt_reason": "stall_timeout", "turn_failure_kind": "stall", "session_id": "ses-p1", "turn_correction": null, "turn_retry_skipped": null}`
    Antigravity host:
    `attempt: {"action": "plan", "disposition": "interrupted", "interrupt_reason": "stall_timeout", "turn_failure_kind": "stall", "session_id": "ses-p1", "turn_correction": null, "turn_retry_skipped": null}`
    Both hosts confirmed absence of `turn_retry_skipped` and `turn_correction`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the `git diff` of the three widened guards and the updated `retrywire` comment; and, from a scripted run on both hosts, the stalled production attempt now carrying `turn_correction` with `turn_retry_attempts: 1`, plus an exit-0 production turn refused by a Set finding showing `turn_retry_skipped` (whose reason names the Set correction loop), `turn_retry_attempts` absent or 0, and `production_set_retry_attempts` equal to the number of Set correction turns that ran and no larger.
  - Observed evidence:
    Widen guards git diff in `agent_workflows/runner_shared.py`:
    `if not is_review:` (in stall arm, spawn-failure arm, and post-turn retrywire).
    Updated retrywire comment explains that reviews remain excluded while production turns are admitted when `attempt.get("turn_failure_kind")` is present.
    From scripted run on both hosts (`test_e10_01`):
    Stalled attempt 1 carries `turn_correction`:
    `"turn_correction": {"attempt": 1, "kind": "correction", "of": 2, "turn_failure_kind": "stall", ...}`
    `item.get("turn_retry_attempts") == 1`.
    From scripted run on both hosts (`test_e10_07`):
    Exit-0 production turn refused by Set finding:
    `att1.get("turn_retry_skipped") == "production turn without turn_failure_kind (owned by production Set correction loop)"`
    `item.get("turn_retry_attempts", 0) == 0`
    `rs.production_set_retry_attempts(item) == 1`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: a scripted production turn on both hosts returning exit 1 with its attempt record showing `turn_failure_kind: no-outcome`, its `BACKLOG-PRODUCTION-FAILED` (or `SPEC-PRODUCTION-FAILED`) refusal, and `production_set_retry_attempts == 0` and `turn_retry_attempts == 1` on the item; plus the diff if any code change was needed (or the statement that none was).
  - Observed evidence:
    From scripted production turn on both hosts (`test_e10_12` / `test_e10_03`):
    Nonzero exit produces `turn_failure_kind: no-outcome` (due to missing outcome file on production turns), recorded refusal `BACKLOG-PRODUCTION-FAILED` (or `SPEC-PRODUCTION-FAILED`), `item.get("turn_retry_attempts") == 1`, and `production_set_retry_attempts == 0`.
    Code diff: No code change was needed for failure-kind assignment; the existing post-turn block already ran for all actions.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the `git diff` showing ONE shared adoption helper called from both the execute and the production branches; and, from a scripted stall-then-success run on both hosts, attempt 2 showing `fix_it_lane: resumed` and the same `worktree` path as attempt 1, with the launcher-recorded session argument equal to attempt 1's `session_id`; plus a first-dispatch attempt showing a fresh session (no session argument). REACHABILITY: the observation is produced by E-05's helper on the production allocation branch, driven through `run_queue` by E-10 case (1).
  - Observed evidence:
    Extracted helper `try_adopt_fix_it_lane` in `agent_workflows/runner_shared.py` (lines 40212-40356), called at line 41316 (production allocation) and line 41689 (execute allocation).
    Observed from `test_e10_01` on both hosts:
    Attempt 1 launcher received `session_arg: None` (fresh session).
    Attempt 2 launcher received `session_arg: "ses-p1"` (resumed).
    Attempt 2 record has `attempts[1]["fix_it_lane"] == "resumed"`.
    Attempt 2 worktree path matches attempt 1: `attempts[1]["worktree"] == attempts[0]["worktree"]`.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: from a scripted run on both hosts that stalls a turn and is then stopped before the fix-it dispatch: the `lane-kept-for-fix-it` event, NO `lane-reclaimed-*` event for that lane, `git worktree list` still listing it, and the lane branch log showing the snapshot commit of the stalled attempt's uncommitted plan file; then the resumed run's attempt 2 record showing `fix_it_lane: resumed` in that worktree; and a statement of which E-10 case (9) drive was used (stop request or direct `reclaim_run_lanes`). REACHABILITY: the keep branch is E-06's new check in `runner_shared.reclaim_lanes_on_interrupt`, reached at run end through `reclaim_run_lanes`.
  - Observed evidence:
    Drive used: `runner_stop.request_stop(run_dir, runner_stop.LEVEL_AFTER_CALL, requester="test")` called inside the stalling fake agent.
    Observed from `test_e10_09` on both hosts:
    - `lane-kept-for-fix-it` event recorded: `{"event": "lane-kept-for-fix-it", "id6": "bkl010", "worktree": "/tmp/.../.aw/worktrees/bkl010"}`.
    - Zero `lane-reclaimed-*` events for that worktree.
    - `git worktree list --porcelain` contains the worktree path.
    - `git log -n 2 --oneline aw/lane/bkl010` shows `WIP INTERRUPTED SNAPSHOT` commit.
    - Resumed run attempt 2: `attempts[1]["fix_it_lane"] == "resumed"` in the same worktree.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: the item's recorded `production_baseline` from a scripted run on both hosts, and the `backlog-production-output-committed` event of the resumed attempt naming BOTH the plan the stalled attempt wrote and the plan the resumed attempt wrote, with no `backlog-production-out-of-scope-paths` event naming either; and the same for the shared-tree case (E-10 case (12)): the plan committed as new output and no `continued-plan-pre-dirty-dropped` event naming it.
  - Observed evidence:
    From `test_e10_02` on both hosts:
    - Attempt 1 recorded `production_baseline` with pre-existing plan IDs before launch.
    - Attempt 2 reused `production_baseline` upon resuming.
    - `backlog-production-output-committed` event names both `chd002` (written in attempt 1) and `orc002` (written in attempt 2).
    - Zero `backlog-production-out-of-scope-paths` events emitted.
    From `test_e10_12` (shared tree `--no-isolate-worktree`):
    - Plan written in attempt 1 is committed as new output on attempt 2 fix-it completion.
    - Zero `continued-plan-pre-dirty-dropped` events emitted.
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: the first lines of the recovery prompt file under the run's `prompts/` directory for a production fix-it attempt, showing the correction notice with `Failure kind: stall`; and a first-attempt production prompt shown to contain no correction notice (pasted grep output with zero matches); and the `git diff` showing both production prompt build sites calling the one notice helper.
  - Observed evidence:
    `git diff` shows `apply_production_correction_notice` called at line 41249 (pre-lane build) and line 41728 (lane rebuild).
    From `test_e10_08` on both hosts:
    Recovery prompt `01-bkl009-exec-attempt-2.md` starts with:
    `## stall (attempt 1 of 2)`
    `Failure kind: stall`
    `Exit code: None`
    First-attempt prompt `01-bkl009-exec-attempt-1.md` grep check:
    `assertNotIn("Failure kind: stall", p1_text)`
    `assertNotIn("The previous attempt FAILED", p1_text)` - 0 matches.
  - Result: pass
- [x] V-14 validates E-14
  - Required evidence: the `git diff` of both production correction loops' stall handling and the one extracted stall helper (with the first-turn `except StallTimeout as stall_exc:` arm calling it too); and, from E-10 case (11) on both hosts, the item record showing `turn_failure_kind: stall`, a `turn_correction`, `status: queued` (or the final status after the fix-it turn) and NO `driver_error` key, plus the `ipd-turn-retry` event. REACHABILITY: the stall is raised by the scripted launcher on its Set correction call, which `resume_via_launcher` reaches inside the production correction loop; the handling is E-14's new code.
  - Observed evidence:
    `git diff` shows helper `_handle_stall_timeout` in `runner_shared.py` (lines 40164-40209).
    Called in:
    (1) `execute_item_core` first-turn stall arm (line 42426);
    (2) spec Set correction loop (line 42721);
    (3) backlog Set correction loop (line 42878).
    From `test_e10_11` on both hosts:
    Item record for attempt 1 (stalled in Set correction turn) shows:
    `"turn_failure_kind": "stall"`, `"turn_correction": {...}`, `"driver_error"` key absent, and `ipd-turn-retry` event emitted.
    Following fix-it turn executed successfully (`status: "executed"`).
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: the `git diff` of the clear helper, its call sites in `reclaim_lanes_on_interrupt`, and the `_finish` closure now calling it in place of the inline key loop; and `execution-report.md` from a scripted run whose stalled production lane is reclaimed at run end, showing no `Preserved lanes (NOT torn down)` entry for it, alongside a run with a preserved unmerged lane that still lists it.
  - Observed evidence:
    `lane_containment.clear_preserved_lane_state(item)` added to `agent_workflows/lane_containment.py` (lines 623-637).
    Called in `runner_shared.py`:
    - `reclaim_lanes_on_interrupt` line 1928 (recovered lane torn down) and line 1989 (run-end lane torn down).
    - `_finish` closure line 43763.
    Called in `oc_runipd.py` line 3499 and `agy_runipd.py` line 2992 with `save_state` on interrupt paths.
    From `test_e11` on both hosts:
    - Run with reclaimed lane: `execution-report.md` does NOT contain `Preserved lanes (NOT torn down)`.
    - Run with preserved lane (holding unmerged commits): `execution-report.md` DOES contain `Preserved lanes (NOT torn down)` listing the lane.
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: the pasted `python3 -m pytest -o addopts="" tests/test_production_fix_it.py -v` output showing all twelve E-10 cases passing on both hosts (the behavior each case pins, not a fixed test count: re-derive the collected count at execution), and the four E-02 baseline modules re-run with counts at least equal to the baseline.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_production_fix_it.py -v` output:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    collected 13 items

    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_02_stalled_attempt_child_plan_committed PASSED [  7%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_11_stall_inside_set_correction_turn PASSED [ 15%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e11_reclaimed_lane_not_in_report_preserved_lane_is PASSED [ 23%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_06_fallback_lane_removed_fresh_session PASSED [ 30%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_05_budget_zero_no_fix_it_turn PASSED [ 38%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_09_lane_kept_for_fix_it_on_run_end PASSED [ 46%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_07_set_finding_refusal_exit_0_turn_retry_skipped PASSED [ 53%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_08_recovery_prompt_has_notice_first_attempt_does_not PASSED [ 61%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_03_spec_production_nonzero_exit_then_success PASSED [ 69%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_04_spawn_failure_exhausts_budget_next_runs PASSED [ 76%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_01_backlog_production_stall_then_success PASSED [ 84%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_10_review_item_stalled_ends_interrupted_no_turn_correction PASSED [ 92%]
    tests/test_production_fix_it.py::TestProductionFixIt::test_e10_12_shared_tree_fix_it_committed_new_output PASSED [100%]
    ============================= 13 passed in 52.10s ==============================
    ```
    Baseline modules re-run:
    `tests/test_turn_fix_it.py tests/test_production_correction_turn.py tests/test_production_resume_handoff.py tests/test_spec_production.py -q`:
    `50 passed in 91.56s`.
  - Result: pass
- [x] V-11 validates E-11
  - Required evidence: the pasted `-v` output of the E-11 report test(s) passing.
  - Observed evidence:
    `tests/test_production_fix_it.py::TestProductionFixIt::test_e11_reclaimed_lane_not_in_report_preserved_lane_is PASSED [ 23%]`
  - Result: pass
- [x] V-12 validates E-12
  - Required evidence: the `git diff` of spec `25kzda` Section 5.5 and its `## Workflow history` note, and the `git diff` of the CHANGELOG `Fixed:` line; plus `git diff CHANGELOG.md | rg -n '^\+.*(\x{2014}|\x{2013})'` returning nothing (exit 1); and the `aw specs note` output.
  - Observed evidence:
    `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    - Section 5.5 group (a) prose: explains host-failure fix-it classes apply to execute and production turns, review turns excluded, production fix-it turns re-adopt lane/session when safe.
    - Table row stall or turn-limit expiry cites plan `ob7aq9`.
    - `aw specs note` command output:
      `aw specs note: appended a history record to .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`
      History line: `- 2026-10-25 note (aw specs): Section 5.5: host-failure fix-it classes apply to execute and production turns (plan ob7aq9)`
    `git diff CHANGELOG.md`:
    `+ - Fixed: a backlog or spec planning turn that stalls, crashes or fails to start is now handed back to the same agent session to finish, and the run report no longer lists a removed lane as preserved.`
    Dash check:
    `git diff CHANGELOG.md | rg -n '^\+.*(\x{2014}|\x{2013})'` returned exit code 1 (no matches).
  - Result: pass
- [x] V-13 validates E-13
  - Required evidence: the pasted final summary lines of bare `python3 -m pytest` and of `make test-all` (passed counts, no failures), any `CORE TIER BUDGET EXCEEDED` block verbatim, and the `aw sanitize --agent` result record showing `pass`.
  - Observed evidence:
    Bare `python3 -m pytest` summary:
    ```
    1833 passed, 11 warnings in 37.22s
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 37.22s exceeded budget of 30.00s.
    Host 1-minute load average: 6.00 on 12 CPUs
    Top 10 slowest core tests:
       1.   5.33s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       2.   5.22s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       3.   4.89s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       4.   3.77s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       5.   3.75s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
       6.   3.51s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       7.   2.94s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       8.   2.85s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       9.   2.37s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
      10.   1.90s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
    ===========================================================================================
    ```
    (No tests added by this plan are in the listed slowest tests).
    `make test-all`:
    `10407 passed, 5 skipped, 1 xpassed, 17 warnings in 762.86s` (with test_typecheck_gate and test_gradcover_end_to_end passing).
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6091,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. No dependency: `ytas91`, `nnsa2o` and `aeq7f8`, whose code this plan extends, are executed.

Execution contract:
- All open questions are resolved.
- Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified at finalize (`--scope-reason`).
- Tests assert observable behavior (state, events, prompt files, worktree list, report text), never production source read with `inspect`, `ast` or regex.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit ob7aq9 -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push or tag.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize ob7aq9 --actor <agent/model> --message <summary> --apply` yourself. Never `git mv` the plan to `executed/` by hand.
