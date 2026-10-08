# IPD: Give fix-it turns for a crashed, stalled or unstarted agent turn and resume its own session

- Date: 2026-10-07
- Kind: child
- Concern: The turn retry can never fire. `runner_shared.TURN_RETRYABLE_DISPOSITIONS` admits only `failed-safely`, and nothing that reaches `handle_turn_failure_retry` carries that token. Measured at review through the real oc `execute_item` with a scripted host: a nonzero exit with no outcome file and no commits is scored `fail-verify` by the silent-turn gate (`turn_attempted_nothing`, refusal `turn-silent-refused`) and refused as "verifier refused or turn fell short"; a nonzero exit that left a lane commit is scored `fail-gate` by `reconcile_disposition` rung 5 and refused as "lifecycle gate or clean-base gate refused"; a `StallTimeout` sets `interrupted` and RETURNS from `execute_item_core` before the retry site and before `session_id` is recorded; and a missing host binary raises `FileNotFoundError` out of `execute_item`, leaving the item `running` (`oc_runipd.run_queue` catches only `DriverError`). So the commonest agent failures fail the item and wait for a human. Separately, every re-dispatch of an isolated execute item starts a FRESH session in a NEW lane: when the prior lane holds work, `worktree_lease.allocate_worktree` attempt-scopes it (measured: attempt 2 ran in `wir001_attempt2`), so the agent must rediscover its own work. Plan `p47qfu` tried to fix the first half by marking producers the predicate never sees (its F-12) and is superseded by this plan.
- Scope: Make a nonzero exit / missing outcome file, a stall or turn-limit expiry, and a spawn failure each reach a fix-it turn under the existing per-kind budget, with Order 03's message naming what happened; key the decision on a recorded failure-kind marker rather than on the disposition token; record the session id even on a stall; for the fix-it re-dispatch, run in the FAILED attempt's own lane and resume that attempt's session when one exists; retire `p47qfu` as superseded. EXCLUDES hook and suite refusals (Order 05), scope (Order 06), detection (Order 07), changing the budget, changing `finalize_retry_decision`, changing the silent-turn and zero-work verdicts themselves (`turn_attempted_nothing`, `handle_zero_work_retry`), and changing the first-dispatch fresh-session rule (`lanesess` `xd9sll`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lane_containment.py, tests/test_turn_fix_it.py, tests/test_retry_class_mapping.py, tests/test_silent_turn_observability.py, .aw/records/plans/pending/20261002-vmrhj0-01-p47qfu-make-the-turn-retry-allowlist-key-on-what-happened-not-on-wh.ipd.md, .aw/records/plans/superseded/20261002-vmrhj0-01-p47qfu-make-the-turn-retry-allowlist-key-on-what-happened-not-on-wh.ipd.md
- Item-Dependencies: executed:mcbph5
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 4
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ytas91

## Workflow history
- 2026-10-08 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. Measured through the real oc `execute_item` with a scripted host: nonzero exit with no outcome and no work ends `fail-verify` via the silent-turn gate (not rung 5's `fail-gate`), so E-01 now marks at that gate too; a crash that left a commit ends rung-5 `fail-gate`; `StallTimeout` returns before the retry site and before `session_id` is recorded, so E-01/E-07 route it to the retry site and record the id; a missing binary raises `FileNotFoundError` out of `execute_item` leaving the item `running`, so E-02 catches it at the spawn site; a re-dispatch allocates an attempt-scoped NEW lane when the prior one holds work (`wir001_attempt2`), so resuming the old session there would be the cross-tree hazard `xd9sll` exists for: E-05 now re-enters the failed lane (new E-07 for the stall half). The turn-limit bound is recorded only on `item["turn_bound_expiry"]`, not on the attempt. `tests/test_silent_turn_observability.py` pins `fail-verify` on the default budget and is now in scope. The turn-retry counter's interaction with `handle_zero_work_retry` and the verification send-back is stated. Gate contract added. Review record `.aw/records/reviews/20261007-fixfirst-04-ytas91-give-fix-it-turns-for-a-crashed-stalled-or-unstarted-agent-t.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When the agent crashes, stalls, or never starts, it gets a fix-it turn in its own lane and session that says exactly that ("you exited with code N and wrote no outcome file; investigate and finish"), instead of the item failing and a human retyping the same instruction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: record what happened where it happens

- [ ] E-01 Add a `turn_failure_kind` attempt field with values `nonzero-exit`, `no-outcome`, `stall`, `turn-limit`, `spawn-failure`, written inside `execute_item_core` at the points the runner LEARNS it, and nowhere else: (a) after the executor spawn returns, `no-outcome` when `exit_code != 0` and `recorded_outcome_path` names no file, else `nonzero-exit` when `exit_code != 0` (written BEFORE `reconcile_disposition` and the silent-turn gate run, so both of today's scorings, rung-5 `fail-gate` and silent-turn `fail-verify`, carry it); (b) `turn-limit` when `item["turn_bound_expiry"]` was set during this attempt (the only place `lane_containment.bound_expiry_reaper` records it; copy its `bound` and `timeout_seconds` onto the attempt and clear the item key so a later attempt does not inherit it); (c) `stall` in the `StallTimeout` arm. Change that arm so that, after its existing snapshot, preservation, accounting and `ipd-stalled` event, it falls through to `handle_turn_failure_retry` with the `interrupted` disposition instead of returning first (a `queued` result returns as the other arms do). Write nothing at a gate-refusal, finalize-refusal or verification-refusal site, and write nothing when `exit_code == 0`.
  - Depends on: none
  - Expected outcome: driving each path through `execute_item` with a scripted host leaves the matching `turn_failure_kind` on the attempt; an exit-0 turn and a gate refusal leave none; a stall reaches `handle_turn_failure_retry`.
  - Execution state: pending

- [ ] E-02 Bring spawn failure inside the retry path. Wrap the `spawn_executor(...)` call in `execute_item_core` so that `FileNotFoundError`/`PermissionError`/`OSError` from `subprocess.Popen` (measured: a missing binary raises `FileNotFoundError` out of `execute_item` and leaves the item `running`), and a `DriverError` raised BEFORE the child started (no `process` created; the host launchers may need a small marker such as a `DriverError` subclass `HostSpawnError` raised from the pre-`Popen` checks, for example `agy_runipd`'s "The --agy path is not executable"), are caught there: record `exit_code: None`, `turn_failure_kind: spawn-failure`, the error text (redacted) under `spawn_error`, set disposition `failed-safely`, and fall through to `handle_turn_failure_retry`. Keep each host's outer `except DriverError` arm in `run_queue` for every other `DriverError` (for example the session-drift raises), and keep `StopNowForce`/`StopAtCheckpoint`/`KeyboardInterrupt` propagation unchanged.
  - Depends on: E-01
  - Expected outcome: a missing host binary yields one fix-it re-dispatch per budget unit and then the item ends `failed-safely` with a recorded reason; the run continues to the next item and exits through the normal summary, never a traceback.
  - Execution state: pending

### Task group 2: decide on the marker

- [ ] E-03 Change `turn_failure_is_retryable` to admit an attempt (the item's last attempt) carrying a `turn_failure_kind` from E-01 under any disposition, AFTER its existing deliberate-operator-stop and refused-finalize refusals (order is load-bearing, see its docstring) and BEFORE the token allowlist, and also refuse first when the attempt carries `VERIFICATION_REFUSED_KEY` (the verification send-back owns that class and its own counter, as `finalize_refusal` is owned by finalize). Keep the allowlist and the fail-closed tail. Return a reason naming the kind. Update `TURN_RETRY_CLASSIFICATION`'s comment to describe the two admission routes, and `tests/test_retry_class_mapping.py` only where it asserts the old single-route behavior (`test_predicate_agrees_with_table` calls with `{}`, so it is expected to pass unchanged; confirm). Update `tests/test_silent_turn_observability.py` `test_silent_turn_records_refusal_and_event`, which drives a nonzero-free silent turn and asserts `fail-verify`: its fake exits 0, so it must still pass unchanged; confirm, and change nothing if it does.
  - Depends on: E-01
  - Expected outcome: `(True, <reason naming the kind>)` for each kind; a deliberate stop, a refused finalize and a verification refusal still refuse first; a bare `fail-gate` or `fail-verify` with no kind still refuses.
  - Execution state: pending

- [ ] E-04 Build the fix-it packet for these kinds with Order 03's `build_fix_it_notice` inside `turn_correction_packet`, passing as evidence: the kind; the exit code (or "the host never started" for `spawn-failure` with the redacted `spawn_error`); whether the outcome file exists; the last 40 lines of the attempt's own log (`attempt["log"]`, read by the driver, redacted by the builder, bounded); the stall or turn limit that fired and its seconds; and the lane-relative facts `_PRIOR_ATTEMPT_SAFE_KEYS` already allows (`lane_starting_head`, `lane_ending_head`, `lane_ending_status`). Add `turn_failure_kind` to `_PRIOR_ATTEMPT_SAFE_KEYS` (a fixed token, no path). Do not add the log text or `spawn_error` to that allowlist; they reach the agent only through the notice.
  - Depends on: E-03
  - Expected outcome: the delivered correction prompt for a `no-outcome` turn contains the kind line, the exit code, "no outcome file", the lane status and a log tail, and contains no absolute path.
  - Execution state: pending

### Task group 3: resume in the same lane and session

- [ ] E-05 For a fix-it re-dispatch of an isolated execute item (the attempt is a recovery attempt whose previous attempt carries a `turn_failure_kind` and a `turn_correction` packet), run in the FAILED attempt's own lane and resume its session. Today `allocate_isolation_worktree` attempt-scopes a lane that holds work (measured: attempt 2 ran in `wir001_attempt2` with a fresh session), so resuming the old session there would run it in a different tree than the one it was bound to, which is the hazard `lanesess` `xd9sll` prevents. So: re-adopt the prior attempt's worktree (`worktree`, `worktree_branch`, `worktree_lane_id`, `worktree_base`) when it still exists, is registered, and is not owned by a live process (`worktree_lease.lane_is_safe_to_adopt` or its equivalent), and only then pass the prior attempt's `session_id` as the resume id (`resume_session=` on oc, `session_id=` with `use_continue=False` on agy, the shapes `resume_via_launcher` already uses). Otherwise fall back to today's allocation and a fresh session, and record which branch was taken (`attempt["fix_it_lane"]`: `resumed` | `fresh` plus the reason). Leave a FIRST dispatch's fresh-session rule unchanged. `driver_begin` still runs for the recovery attempt; the receipt's `base_head` is main's HEAD, as today.
  - Depends on: E-04
  - Expected outcome: a scripted host records the work_dir and session id it was launched with; the fix-it turn runs in the first attempt's lane and resumes the first attempt's id; a removed lane or a missing id falls back to a fresh lane and session with the reason recorded.
  - Execution state: pending

- [ ] E-07 Record the session id on a stall. The `StallTimeout` arm is reached before `attempt["session_id"]` is set (measured: `session_id: None` on a stalled attempt), so E-05 would always fall back for the stall kind. Have the host launchers attach the session id they have already parsed to the raised `StallTimeout` (an optional `session_id` attribute; both hosts parse it from the stream before the watchdog fires) and have the arm copy it to `attempt["session_id"]`. A `StallTimeout` without the attribute leaves the field unset.
  - Depends on: E-01
  - Expected outcome: a stalled attempt whose stream carried a session id records it; the fix-it turn for that stall resumes it (E-05).
  - Execution state: pending

### Task group 4: tests and retirement

- [ ] E-06 Add `tests/test_turn_fix_it.py` driving the real `execute_item` and `run_queue` on BOTH hosts with a scripted host for: nonzero exit with no outcome and no work, then success on the fix-it turn (item executed, `turn_retry_attempts == 1`); nonzero exit that left a commit (rung-5 path), then success; stall then success; turn-limit expiry; missing host binary (budget spent, then `failed-safely`, the next queued item still runs, `run_queue` returns normally); budget 0 (no fix-it turn); deliberate stop (no fix-it turn); a verification refusal (owned by the verification send-back, not double-counted); and session plus lane resume, including the fallback. Then retire `p47qfu` with `aw ipd set superseded p47qfu -m "superseded by ytas91 (fixfirst-04): marks failures where the run learns them"` and commit both its paths. No source introspection.
  - Depends on: E-05, E-07
  - Expected outcome: the module passes; `p47qfu` is under `superseded/`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `runner_shutdown.KNOWN_ITEM_STATUSES` is closed: this plan adds attempt FIELDS, not a status.
- `queued` plus `recovery_next` is the established re-dispatch pattern (`handle_turn_failure_retry`).
- Each send-back owns its own counter (`TURN_RETRY_COUNT_KEY`, `FINALIZE_RETRY_COUNT_KEY`, the verification and zero-work keys); a class owned by one must be refused by the others, as `turn_failure_is_retryable` already does for `finalize_refusal`.
- Tests use a scripted host (`tests/test_silent_turn_observability.py` `fake_opencode`, or a patched launcher as `tests/test_oc_runipd.py` does), not source reads.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The retry allowlist has one token, and the only path that reaches the predicate never produces it. | `TURN_RETRYABLE_DISPOSITIONS` derives from the single `True` row (`failed-safely`) of `TURN_RETRY_CLASSIFICATION`; `handle_turn_failure_retry` is called only inside `execute_item_core` (plan `p47qfu` F-12). |
| F-02 | A crash is scored by two different gates depending on whether it left work. | Review demo through oc `execute_item`: no work -> `fail-verify`, refusal `turn-silent-refused`, skip reason "verifier refused or turn fell short"; a lane commit -> `fail-gate`, skip reason "lifecycle gate or clean-base gate refused". |
| F-03 | A missing binary is not a `DriverError` and escapes the run. | Review demo: `missing binary \| RAISED FileNotFoundError [Errno 2] No such file or directory \| status: running`; `oc_runipd.run_queue` `except DriverError as exc: runnable["status"] = "failed-safely"`. |
| F-04 | Isolated corrections start fresh, in a new lane when the old one holds work. | Review demo: `attempt 1 \| lane wir001`, `attempt 2 \| lane wir001_attempt2 \| resume None`; `allocate_worktree` HOLDS-WORK "-> attempt-scope"; `execute_item_core` "session_id = None / use_continue = False" under `xd9sll`. |
| F-05 | Maintainer ruling 2026-10-07: retry crashes whatever the worktree holds; the retry has the most value when there is work to salvage. | Session 2026-10-07. |
| F-06 | (review) A stall returns before the retry site and before the session id is recorded. | Review demo: `STALL status interrupted \| skipped: None \| session_id: None`; the `except StallTimeout:` arm ends in `return`. |
| F-07 | (review) The turn-limit bound is recorded on the item, not the attempt. | `lane_containment.bound_expiry_reaper._expire`: `item["turn_bound_expiry"] = record`. |

## Proposed changes (ordered, validatable)

1. Record the failure kind where it is learned, and route a stall to the retry site (E-01).
2. Bring spawn failure inside the retry path (E-02).
3. Decide on the kind (E-03).
4. Fix-it packet with real evidence (E-04).
5. Resume in the failed lane and session (E-05), with the stall's session id recorded (E-07).
6. Tests and retire `p47qfu` (E-06).

## Deferred / out of scope (with reason)

- A total cap on fix-it turns across kinds.
  - Carrier: 38hwvk

## Scope check

- Over-scope: none. `runner_shared.py` E-01 to E-05 and E-07; both hosts E-02 (spawn marker) and E-07 (stall session id); `lane_containment.py` E-01 (turn-limit record) and E-04 (allowlist); `tests/test_turn_fix_it.py` E-06; `tests/test_retry_class_mapping.py` and `tests/test_silent_turn_observability.py` E-03 (confirm-unchanged, edit only if they assert the old route); the two `p47qfu` paths E-06.
- Under-scope: a crash after the agent ran an external action is retried like any other (maintainer ruling F-05); external-action classes are Order 01 group (b).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_turn_fix_it.py tests/test_retry_class_mapping.py tests/test_silent_turn_observability.py tests/test_turn_bounds.py tests/test_oc_runipd.py tests/test_verification_sendback.py tests/test_finalize_sendback.py`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: spec `25kzda` 5.5 group (a) and the mapping table are amended by Order 01 (`tb6lw3` E-02 asks each row to name the evidence key; this plan's `turn_failure_kind` is that key for the host-failure rows).

## Open questions

### OQ-01: Does a fix-it turn after a crash risk duplicating work?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No new risk. The turn re-enters the same isolated lane and session where possible (E-05) and is shown the lane's status and commits (E-04), and the dangerous external actions are handled elsewhere (Order 01 group (b)). Maintainer ruling F-05.

### OQ-02: Should the fix-it turn resume in the failed lane, or in a fresh attempt-scoped lane with the old work pointed at?

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: The failed lane, when it is safe to adopt. Resuming a session in a different worktree than the one it ran in is the hazard `xd9sll` exists to prevent, and a fresh lane forces the agent to bring work forward by hand (`build_verify_and_continue_notice` "BRING FORWARD what is still correct INTO YOUR OWN LANE"), which is the rediscovery the Concern names. Fallback to today's behavior keeps the lane-safety rules intact. Recorded as decision D-1 in the review record.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste each scripted path's attempt record showing `turn_failure_kind` (no-outcome, nonzero-exit with work, stall, turn-limit), an exit-0 turn and a gate refusal showing none, and the stalled item reaching `handle_turn_failure_retry` (its `turn_retry_*` record).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a run with a nonexistent host binary showing the fix-it re-dispatch, then `failed-safely` with a recorded reason, the next queued item running, and `run_queue`'s normal return with no traceback.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `python3 -c` session printing `turn_failure_is_retryable` for each kind, a deliberate stop, a refused finalize, a verification refusal, and a bare `fail-gate` and `fail-verify`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the delivered correction prompt for a `no-outcome` turn, showing no absolute path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the scripted host's recorded work_dir and session ids for both attempts in the resume case, and the fallback case with `attempt["fix_it_lane"]`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the passing Required tests run with per-test counts, the bare-suite summary line, and `aw find plans p47qfu` showing `superseded/`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste a stalled attempt's record showing the session id, and the fix-it turn's launch showing it resumed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Execute only after `mcbph5` has executed (`- Item-Dependencies:`), because E-04 uses its `build_fix_it_notice`.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
