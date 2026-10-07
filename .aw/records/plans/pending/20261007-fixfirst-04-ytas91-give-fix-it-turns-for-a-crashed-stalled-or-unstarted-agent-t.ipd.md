# IPD: Give fix-it turns for a crashed, stalled or unstarted agent turn and resume its own session

- Date: 2026-10-07
- Kind: child
- Concern: The turn retry can never fire. `runner_shared.TURN_RETRYABLE_DISPOSITIONS` admits only `failed-safely`, and nothing that reaches `handle_turn_failure_retry` carries that token: a nonzero exit with no outcome file is scored `fail-gate` by `reconcile_disposition` rung 5; a stall becomes `interrupted` or, on a bound kill, `fail-gate`; and a spawn failure (`DriverError`) is caught in each host's `run_queue` after `execute_item` has already raised past the retry site. So the commonest agent failures fail the item and wait for a human. Separately, an isolated correction turn always starts a FRESH session (`session_id = None` in `execute_item_core`), so the agent must rediscover its own work. Plan `p47qfu` tried to fix the first half by marking producers the predicate never sees (its F-12) and is superseded by this plan.
- Scope: Make a nonzero exit / missing outcome file, a stall or turn-limit expiry, and a spawn failure each reach a fix-it turn under the existing per-kind budget, with Order 03's message naming what happened; key the decision on a recorded failure-kind marker rather than on the disposition token; resume the failed attempt's own session for the fix-it turn when one exists; retire `p47qfu` as superseded. EXCLUDES hook and suite refusals (Order 05), scope (Order 06), detection (Order 07), changing the budget, and changing `finalize_retry_decision`.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lane_containment.py, tests/test_turn_fix_it.py, tests/test_retry_class_mapping.py, .aw/records/plans/pending/20261002-vmrhj0-01-p47qfu-make-the-turn-retry-allowlist-key-on-what-happened-not-on-wh.ipd.md, .aw/records/plans/superseded/20261002-vmrhj0-01-p47qfu-make-the-turn-retry-allowlist-key-on-what-happened-not-on-wh.ipd.md
- Item-Dependencies: executed:mcbph5
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 4
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ytas91

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When the agent crashes, stalls, or never starts, it gets a fix-it turn in its own session that says exactly that ("you exited with code N and wrote no outcome file; investigate and finish"), instead of the item failing and a human retyping the same instruction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: record what happened where it happens

- [ ] E-01 Add a `turn_failure_kind` attempt field with values `nonzero-exit`, `no-outcome`, `stall`, `turn-limit`, `spawn-failure`, written at the point the runner LEARNS it inside `execute_item_core`: rung 5 of `reconcile_disposition` when it falls back on the exit code (`nonzero-exit` when `exit_code != 0`, `no-outcome` when the outcome file is absent); the `StallTimeout` arm (`stall`); the turn-bound expiry path that today records `lane_containment.BOUND_EXPIRY_DISPOSITION` (`turn-limit`). Write nothing at a gate-refusal site.
  - Depends on: none
  - Expected outcome: driving each of the four paths with a scripted host leaves the matching `turn_failure_kind` on the attempt; a gate refusal leaves none.
  - Execution state: pending

- [ ] E-02 Move spawn-failure handling inside the retry path: catch the host spawn failure (`DriverError` raised while starting the host, and `FileNotFoundError`/`OSError` from `Popen`, which today escapes as an "unexpected failure") inside `execute_item_core` before the retry site, record `turn_failure_kind: spawn-failure`, and let `handle_turn_failure_retry` decide. Keep each host's outer `except DriverError` arm for errors that are not spawn failures.
  - Depends on: E-01
  - Expected outcome: a missing host binary yields one fix-it re-dispatch per budget unit and then a contained item failure, never a run crash.
  - Execution state: pending

### Task group 2: decide on the marker

- [ ] E-03 Change `turn_failure_is_retryable` to admit an attempt carrying a `turn_failure_kind` from E-01, under any disposition, AFTER its existing deliberate-operator-stop and refused-finalize refusals (order is load-bearing, see its docstring) and BEFORE the token allowlist. Keep the allowlist and the fail-closed tail. Return a reason naming the kind. Update `TURN_RETRY_CLASSIFICATION`'s comment to describe the two admission routes, and `tests/test_retry_class_mapping.py` only where it asserts the old single-route behavior.
  - Depends on: E-01
  - Expected outcome: `(True, <reason naming the kind>)` for each kind; a deliberate stop and a refused finalize still refuse first; a bare `fail-gate` with no kind still refuses.
  - Execution state: pending

- [ ] E-04 Build the fix-it packet for these kinds with Order 03's `build_fix_it_notice`, passing as evidence: the exit code, whether the outcome file exists, the last lines of the host's stderr/stream already captured in the run directory, the stall or turn limit that fired, and the lane's `git status --short` and new commits (the same lane-relative fields `_PRIOR_ATTEMPT_SAFE_KEYS` already allows).
  - Depends on: E-03
  - Expected outcome: the delivered correction prompt for a `no-outcome` turn contains the kind line, the exit code, "no outcome file", and the lane status.
  - Execution state: pending

### Task group 3: resume the session

- [ ] E-05 For a fix-it re-dispatch of an isolated execute item, resume the failed attempt's own `session_id` in the same lane worktree (the merge-conflict send-back already does this with `resume_session`), falling back to a fresh session when the id is absent or the host refuses it. Leave a first dispatch's fresh-session rule (`lanesess` `xd9sll`) unchanged: the resumed session is the one bound to THIS lane, so the cross-tree hazard that rule prevents does not arise.
  - Depends on: E-04
  - Expected outcome: a scripted host records the session id it was resumed with; the fix-it turn resumes the first attempt's id; a missing id falls back to fresh.
  - Execution state: pending

### Task group 4: tests and retirement

- [ ] E-06 Add `tests/test_turn_fix_it.py` driving the real runner on both hosts with a scripted host for: nonzero exit with no outcome then success on the fix-it turn (item executed, one correction spent); stall then success; missing host binary (budget spent, then contained failure, run continues); budget 0 (no fix-it turn); deliberate stop (no fix-it turn); and session resume. Then retire `p47qfu` with `aw ipd set superseded p47qfu -m "superseded by ytas91 (fixfirst-04): marks failures where the run learns them"`.
  - Depends on: E-05
  - Expected outcome: the module passes; `p47qfu` is under `superseded/`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `runner_shutdown.KNOWN_ITEM_STATUSES` is closed: this plan adds an attempt FIELD, not a status.
- `queued` plus `recovery_next` is the established re-dispatch pattern (`handle_turn_failure_retry`).
- Tests use a scripted host binary (`tests/test_silent_turn_observability.py` `fake_opencode`), not source reads.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The retry allowlist has one token, and the only path that reaches the predicate never produces it. | `TURN_RETRYABLE_DISPOSITIONS == frozenset({'failed-safely'})`; `handle_turn_failure_retry` is called only inside `execute_item_core` after `reconcile_disposition` (plan `p47qfu` F-12). |
| F-02 | Rung 5 returns `fail-gate` on a nonzero exit, the token gate refusals also use. | `reconcile_disposition` docstring "5. Exit code fallback: fail-verify if exit 0, fail-gate otherwise." |
| F-03 | Spawn failure is caught outside the retry site; a missing binary is not a `DriverError` at all. | `oc_runipd` `except DriverError as exc: runnable["status"] = "failed-safely"` in `run_queue`; `Popen` `FileNotFoundError` reaches `main`'s "unexpected failure" (survey 2026-10-07). |
| F-04 | Isolated corrections start a fresh session; only the merge-conflict send-back resumes. | `execute_item_core`: "session_id = None / use_continue = False" under lanesess `xd9sll`; send-back passes `resume_session: conflict_session`. |
| F-05 | Maintainer ruling 2026-10-07: retry crashes whatever the worktree holds; the retry has the most value when there is work to salvage. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Record the failure kind where it is learned (E-01).
2. Bring spawn failure inside the retry path (E-02).
3. Decide on the kind (E-03).
4. Fix-it packet with real evidence (E-04).
5. Resume the attempt's session (E-05).
6. Tests and retire `p47qfu` (E-06).

## Deferred / out of scope (with reason)

- A total cap on fix-it turns across kinds.
  - Carrier: 38hwvk

## Scope check

- Over-scope: none. `runner_shared.py` E-01 to E-05; both hosts E-02 and E-05; `lane_containment.py` E-01 (turn-limit path) and E-04 (allowlisted fields); tests E-03 and E-06; the two `p47qfu` paths E-06.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_turn_fix_it.py tests/test_retry_class_mapping.py tests/test_silent_turn_observability.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: spec `25kzda` 5.5 group (a) and the mapping table are amended by Order 01.

## Open questions

### OQ-01: Does a fix-it turn after a crash risk duplicating work?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No new risk. The turn resumes in the same isolated lane and is shown the lane's status and commits (E-04), and the dangerous external actions are handled elsewhere (Order 01 group (b)). Maintainer ruling F-05.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste each scripted path's attempt record showing `turn_failure_kind`, and a gate refusal's showing none.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a run with a nonexistent host binary showing the fix-it re-dispatch, then the contained failure, and a run exit code that is not a crash.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `python3 -c` session printing `turn_failure_is_retryable` for each kind, a deliberate stop, a refused finalize and a bare `fail-gate`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the delivered correction prompt for a `no-outcome` turn.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the scripted host's recorded session ids for both attempts, and the fallback case.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the passing module runs with per-test counts, the bare-suite summary line, and `aw find plans p47qfu` showing `superseded/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
