# IPD: Make finalize wait for a briefly held writer lock and retry a lock refusal instead of failing the item

- Date: 2026-09-26
- Kind: child
- Concern: A VERIFIED, conforming plan is failed terminally (`fail-gate`) because another process held the shared writer lock for a few seconds at the instant its finalize ran. Measured in run `run-20260926T051642Z-116672`: item `9npssm` executed, verified, linted `conforming` at `pre-transition`, and still ended `fail-gate` with `ipd finalize writer lock held by active PID 402458 (plan None)` (`events.jsonl` line 17, `retryable: false`). Two causes combine: `ipd_lifecycle.acquire_finalize_lock` never waits (a live holder raises `TransactionLockError` at once), and `runner_shared.finalize_refusal_is_retryable` admits no lock class, so the refusal is terminal. The same lock file backs `commit_lock.writer_lock`, which DOES wait (default 5s) and whose holders keep it across a whole `pre-commit` run (measured 10.6s for one record file), so contention in a shared checkout with concurrent drivers is routine, not exotic.
- Scope: IN: (a) a bounded wait inside `acquire_finalize_lock` before it refuses; (b) a distinct, machine-recognizable lock-contention refusal and its classification as retryable-without-an-agent-turn in the runner, deferred and re-attempted rather than sent back to the agent or failed; (c) naming the holder's `owner` in the refusal when `plan_id` is absent; (d) tests for all three. OUT: changing `commit_lock.writer_lock`'s own 5s budget or its docstring's hold-time claim (see Deferred), and the integration lock, which already waits.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_ipd_lifecycle_cli.py, tests/test_finalize_sendback.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: duac3v
- Blocks-Release: next
- Set: finlockwait
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: y2vzit

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog duac3v at the maintainer's request ("We need the wait-and-retry for that step too"). Mechanism reproduced from the run record and the code: acquire_finalize_lock raises on any live holder with no wait, and finalize_refusal_is_retryable has no lock arm.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A finalize that meets a briefly held writer lock waits for it, and if the lock is still held after the wait, the runner re-attempts the finalize later in the same run instead of failing a verified item. A genuinely stuck lock still ends in a clear refusal that names its holder.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the lock waits

- [ ] E-01 Give `ipd_lifecycle.acquire_finalize_lock` a bounded wait: poll the lock (same liveness test, same stale-reclaim path) until it is free or a budget expires, and only then raise `TransactionLockError`. Default budget `FINALIZE_LOCK_WAIT_SECONDS = 120.0` as a module constant, injectable (`timeout`, `sleep`, `now`) so tests run in milliseconds. Keep the three existing call sites (`_early_recovery_result` path, the retirement path, and the main finalize path) calling the same function so they all gain the wait.
  - Depends on: none
  - Expected outcome: a holder that releases within the budget no longer causes a refusal; a holder that outlives it still raises, after the budget, with the existing diagnostic.
  - WHY 120s: `pre-commit` holds the lock for its whole run (measured 10.6s on one record file, and a finalize commit runs the full hook set), so writer_lock's 5s is known to be too short for this lock; 120s absorbs several back-to-back peer commits while staying far below the 1800s the integration lock allows, because a finalize, unlike an integration, never needs to wait for a suite.
  - Execution state: pending

- [ ] E-02 Name the holder. When the lock payload has no `plan_id` (a `commit_lock.writer_lock` holder writes `owner` instead), the refusal must print that `owner` string rather than `plan None`, and must carry a stable prefix the runner can classify: `ipd finalize writer lock held by active PID <pid> (<plan <id> | owner <owner>>)` followed by the existing remedy text. Add the prefix as a module constant `FINALIZE_LOCK_BUSY_SUMMARY` so the runner imports it rather than copying the string.
  - Depends on: E-01
  - Expected outcome: a contention refusal caused by an `offer_commit` holder names `owner git_commit_helper.offer_commit`.
  - Execution state: pending

### Task group 2: the runner re-attempts instead of failing

- [ ] E-03 In `runner_shared`, classify a finalize refusal whose message contains `ipd_lifecycle.FINALIZE_LOCK_BUSY_SUMMARY` (and no `IPD-` finding lines) as LOCK CONTENTION: a third outcome of `finalize_retry_decision`, distinct from the agent send-back. It re-attempts the SAME `driver_finalize` call (no agent turn, no prompt, no correction budget spent), a bounded number of times (`FINALIZE_LOCK_REATTEMPTS = 3`) with a short backoff, and only if every re-attempt still meets contention does the item end `fail-gate` with a reason saying the lock was busy and naming the holder.
  - Depends on: E-02
  - Expected outcome: a transient lock refusal ends `executed` once the lock frees; the agent is never re-dispatched for it; the correction budget counter (`FINALIZE_RETRY_COUNT_KEY`) is unchanged.
  - WHY NOT THE AGENT SEND-BACK: the send-back exists to let an agent fix its bookkeeping. Lock contention has nothing for an agent to fix, so sending it back would spend a paid turn and a budget unit on a no-op, and a budget of 0 would still fail the item.
  - WHY THIS IS NOT ON SPEC `25kzda` 5.5's NEVER-RETRY LIST: that list names "overlapping ownership or lease conflict", which is about two actors owning the same PATHS. This refusal is raised BEFORE the transaction starts, with nothing mutated (the lock is acquired before `_finalize_transaction`), so it is a transient precondition, the same class as the integration lock that `integrate_under_repository_lock` already waits on and defers. The executor MUST confirm the "nothing mutated" claim by reading `acquire_finalize_lock`'s call sites and record it in V-03.
  - Execution state: pending

- [ ] E-04 Record it. Each contention re-attempt appends an `ipd-finalize-lock-wait` event (id6, attempt number, holder pid and owner); the final `ipd-finalize-refused` event for an exhausted contention carries `retryable: true`, `retry_scheduled: false`, and a `cause: "lock-contention"` field, so a reader can tell it apart from a gate refusal without parsing prose.
  - Depends on: E-03
  - Expected outcome: `events.jsonl` distinguishes a lock wait from a gate refusal by field, not by message text.
  - Execution state: pending

### Task group 3: tests and changelog

- [ ] E-05 Tests. In `tests/test_ipd_lifecycle_cli.py`, extend `test_lock_contention_and_stale_reclamation`'s class with: a holder that releases mid-wait (injected clock) -> acquire succeeds; a holder that outlives the budget -> raises with the owner named; the stale-reclaim case still reclaims immediately without waiting. In `tests/test_finalize_sendback.py`, add: a lock-busy message is classified as contention and NOT as the agent send-back; a mixed message (lock-busy plus an `IPD-` finding) is NOT treated as contention; a contention re-attempt that succeeds leaves the item `executed` with the budget counter unchanged; exhausted contention ends `fail-gate` with `cause: lock-contention`. Add one TWO-PROCESS test: a child process holds the real lock file for ~1s, the parent calls `acquire_finalize_lock` with a 5s budget and must succeed.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: all new tests pass and each FAILS against the pre-change code (show it by reverting the hunk).
  - Execution state: pending

- [ ] E-06 Add a `CHANGELOG.md` entry under the unreleased section, in plain user-facing language with no dashes: a run no longer fails a finished item just because another command was briefly committing in the same checkout.
  - Depends on: E-03
  - Expected outcome: one entry, user-facing wording.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The finalize lock file is SHARED with `commit_lock.writer_lock` (`commit_lock._LOCK_RELPATH` comment: "The lock file is SHARED with `ipd_lifecycle.finalize_lock_path`"), so every self-committing `aw` verb (`git_commit_helper.offer_commit`) contends with finalize.
- `commit_lock.writer_lock` holds the lock across the whole `pre-commit` window by design (its "MEASURED HARM (2026-09-06)" comment), so its hold time is the hook run time, not "well under a second".
- The runner's finalize runs as a SUBPROCESS (`runner_shared.driver_finalize` -> `aw ipd finalize ... --apply`), so the in-process wait of E-01 lives in `ipd_lifecycle`, and the runner sees only the return code and message; hence E-02's stable prefix.
- The runner's existing refusal handling is `runner_shared.handle_finalize_refusal` -> `finalize_retry_decision` -> `finalize_refusal_is_retryable`, a positive allowlist of `IPD-` finding texts (`tests/test_finalize_sendback.py::TheRetryTriggerIsAPositiveAllowlist`). E-03 adds a separate arm; it must not widen the send-back allowlist.
- The integration lock is the precedent for "wait, then defer, never fail on a lock": `runner_shared.integrate_under_repository_lock`, `INTEGRATION_LOCK_TIMEOUT_SECONDS`.
- Tests run bare (`python3 -m pytest`); narrowed runs use `-o addopts=""` (AGENTS.md).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.acquire_finalize_lock` | No wait at all: a live holder raises immediately. | the function body: `if alive: raise TransactionLockError(...)`, no loop |
| F-2 | HIGH | `runner_shared.finalize_refusal_is_retryable` | No lock arm: only `RETRYABLE_FINALIZE_SUMMARY` and `RETRYABLE_STALE_RECEIPT_SUMMARY` are admitted, so a lock refusal is terminal. | run `run-20260926T051642Z-116672` `events.jsonl` line 17: `"retryable": false` |
| F-3 | MEDIUM | refusal text | `(plan None)` when the holder is a `writer_lock` holder, so the holder cannot be identified afterwards. | same event; `commit_lock.try_acquire` writes `owner`, not `plan_id` |
| F-4 | MEDIUM | `commit_lock.writer_lock` docstring | Claims a self-commit holds the lock "for well under a second"; measured 10.6s for `pre-commit run` on one file. | `time pre-commit run --files <one review record>` -> `real 0m10.576s` (2026-09-26) |

## Proposed changes (ordered, validatable)

1. E-01: bounded wait in `acquire_finalize_lock` (F-1).
2. E-02: stable refusal prefix naming the holder (F-3).
3. E-03: runner re-attempts a contention refusal without an agent turn (F-2).
4. E-04: events distinguish contention from gate refusals.
5. E-05: unit, classification and two-process tests.
6. E-06: changelog.

## Deferred / out of scope (with reason)

- Raising `commit_lock.writer_lock`'s own 5s default and correcting its docstring (F-4).
  - Carrier: duac3v
- A general "who holds which lock" status verb.
  - Carrier-Declined: E-02 puts the holder in the one message a human reads when this bites; a separate verb is not needed to close this defect.

## Scope check

- Over-scope: none. Every item traces to F-1..F-3 or to their verification.
- Under-scope: F-4 is deliberately deferred to its carrier `duac3v`, because changing a budget used by every `aw` verb is a separate behavior change with its own trade-off (a longer wait makes a stuck lock slower to surface).

## Required tests / validation

- `python3 -m pytest tests/test_ipd_lifecycle_cli.py tests/test_finalize_sendback.py -o addopts=""` with the new tests, plus a revert of each hunk showing the new tests fail.
- Bare `python3 -m pytest`.
- `python3 -m agent_workflows check all --agent`, naming pre-existing findings as pre-existing.

## Spec / documentation sync

No spec amendment. Spec `25kzda` 5.5 lists the retryable and never-retryable classes; this plan's contention refusal is argued in E-03 to be neither a lease conflict nor a mutation, and the runner defers it without spending retry budget, which 5.5 does not govern. If `/plan-review` disagrees that 5.5 is silent here, the fix is to amend 5.5 in this plan (adding it to `- Scope-Paths:`), not to drop the re-attempt. `CHANGELOG.md` is updated (E-06).

## Open questions

### OQ-01: Is 120 seconds the right finalize lock wait?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence: holders keep the lock for a full `pre-commit` run (measured 10.6s for one file; a finalize commit's hook run is longer), and several agents commit in this checkout concurrently, so a budget must cover a short queue of such holders. 120s does, while a genuinely stuck holder still surfaces within two minutes, and E-03's re-attempts extend coverage without an unbounded wait. Reversible: one constant.
- Carrier-Declined: resolved with evidence; nothing remains owed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `acquire_finalize_lock` and the passing output of the release-mid-wait and outlives-budget tests; show the release-mid-wait test FAILS with the wait reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a refusal message produced by the test with an `owner`-only payload, showing `owner git_commit_helper.offer_commit` and the `FINALIZE_LOCK_BUSY_SUMMARY` prefix, and the grep showing the runner imports the constant rather than copying the string.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the classification tests (contention vs send-back vs mixed), the re-attempt-succeeds test showing `executed` with `FINALIZE_RETRY_COUNT_KEY` unchanged, and the exhausted case ending `fail-gate`. Paste the three `acquire_finalize_lock` call sites with the lines showing nothing is mutated before the lock is taken.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `ipd-finalize-lock-wait` and exhausted `ipd-finalize-refused` event dicts from a test, showing `cause: "lock-contention"`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the two-process test's passing output and the full bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the CHANGELOG entry.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <plan> -- <paths>` limited to `- Scope-Paths:`; never push. Finalize with `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence; the plan then moves to `.aw/records/plans/executed/`.
