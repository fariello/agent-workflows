# IPD: Make the five contention waits share one policy: check every 10s, report every 60s, fail after 30 minutes

- Date: 2026-09-27
- Kind: child
- Concern: Five code-only waits for something another process holds or has just changed each use their own timing, and several give up far too early: the finalize writer lock waits 120s x 4 (about 8 min) then fails the item, which stranded 7icz68, 4eecvh, 8y13kn, cnzrxb and 3rsdbj on 2026-09-27 while several runs overlapped; the integration lock polls every 1s and reports every 30s; the deferral ladder polls 10 times at 30s with a 1h staleness cap; the shared aw writer lock waits only 5s and then COMMITS UNSERIALIZED; and a setter whose commit loses the compare-and-swap race (`commit_lock.ISO_RACED`) does not retry at all and leaves its file change uncommitted. None of these involves an agent.
- Scope: IN: one shared wait helper and one policy (poll every 10s, a progress line every 60s naming what is awaited and who holds it, fail after 30 minutes; a lock whose holder is dead is taken over at once, as today) applied to all five: `ipd_lifecycle.acquire_finalize_lock` plus the runner's `finalize_with_contention_retry` re-attempts, `runner_shared.integration_lock`, the deferral ladder's `poll_for_integration_window`, `commit_lock.writer_lock` (which now fails instead of committing unserialized), and the `ISO_RACED` path in `git_commit_helper.offer_commit` (re-run the isolated commit on the new tip); outcome tests with an injected clock; one CHANGELOG line. OUT: the pre-commit hook re-stage retry in `commit_lock.commit_isolated` (stays one immediate redo, maintainer ruling 2026-09-27); the agent retry budget and its per-kind counters (unchanged, maintainer ruling 2026-09-27); `--integration-retry-limit` semantics beyond its wait timing; `run_ledger_store.writer_lock` (a different, in-run ledger lock).
- Scope-Paths: agent_workflows/contention_wait.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, agent_workflows/commit_lock.py, agent_workflows/git_commit_helper.py, tests/test_contention_wait.py, tests/test_runner_shared.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: next
- From-Backlog: ibk7bt
- Work-Kind: bug
- Priority: high
- Set: uniwait
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9bq5o4

## Workflow history
- 2026-09-27 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ibk7bt per maintainer ruling 2026-09-27: one wait policy (10s poll, 60s report, 30 min) for five code-only contention waits.

- 2026-09-27 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every code-only wait for a busy lock or a moved branch behaves the same way: it checks every 10 seconds, tells the operator every 60 seconds what it is waiting for and who holds it, and fails cleanly after 30 minutes. No item fails, and no change is left uncommitted, just because another run was briefly busy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the one policy

- [ ] E-01 Add `agent_workflows/contention_wait.py` (stdlib only): constants `POLL_SECONDS = 10.0`, `REPORT_SECONDS = 60.0`, `TIMEOUT_SECONDS = 1800.0`, and `wait_until(try_once, *, what, holder=None, timeout=TIMEOUT_SECONDS, poll=POLL_SECONDS, report_every=REPORT_SECONDS, report=None, sleep=time.sleep, now=time.monotonic) -> WaitResult` (NamedTuple `ok`, `value`, `waited`, `attempts`, `detail`). `try_once()` returns `(done: bool, value)`; `holder()` returns a short string naming who holds the resource (or None). It calls `try_once` immediately, then every `poll` seconds; every `report_every` seconds it calls `report(f"still waiting for {what}{' held by ' + holder() if holder else ''} ({int(waited)}s of {int(timeout)}s)")` (default `report` writes that line to stderr); on success returns `ok=True`; at `timeout` returns `ok=False` with a detail naming `what`, the last holder and the elapsed time. Never raises for an expected condition. The clock, sleep and report are injectable so tests never sleep.
  - Depends on: none
  - Expected outcome: one helper and one set of numbers; no call site keeps its own timing constants.
  - Execution state: pending

### Task group 2: apply it to the five waits

- [ ] E-02 FINALIZE WRITER LOCK. Make `ipd_lifecycle.acquire_finalize_lock`'s default wait use `contention_wait.wait_until` (keep its dead-holder takeover and the `timeout=0` check-once behavior for callers that pass 0); replace `FINALIZE_LOCK_WAIT_SECONDS`/`FINALIZE_LOCK_POLL_SECONDS` with the shared constants. Then remove the runner's extra loop in `runner_shared.finalize_with_contention_retry` (the `FINALIZE_LOCK_REATTEMPTS = 3` x `FINALIZE_LOCK_BACKOFF_SECONDS` re-attempts) or reduce it to a single call, because finalize itself now waits the full 30 minutes; keep the `ipd-finalize-lock-wait` event, emitted from the report callback. A lock still held after 30 minutes keeps today's terminal `lock-contention` outcome.
  - Depends on: E-01
  - Expected outcome: a finalize behind a busy peer waits up to 30 min with a line every 60 s, then fails exactly as today.
  - Execution state: pending

- [ ] E-03 INTEGRATION LOCK. Make `runner_shared.integration_lock` poll through `contention_wait.wait_until` (10 s poll, 60 s progress via the existing `integration_lock_progress_reporter`, 30 min, unchanged timeout); replace `INTEGRATION_LOCK_PROGRESS_SECONDS` and the `min(1.0, max(0.05, ...))` sleep. Keep main's tip re-read inside the lock and the `integration deferred` (`merge-retry`) give-up outcome. The `aw integration-lock --timeout` CLI keeps accepting an override.
  - Depends on: E-01
  - Expected outcome: same 30 min bound, now 10 s / 60 s like the others.
  - Execution state: pending

- [ ] E-04 DEFERRAL LADDER. Make `runner_shared.poll_for_integration_window` wait through `contention_wait.wait_until` with the shared constants, so a temporarily blocked merge (overlapping dirty paths in main) is re-checked every 10 s, reported every 60 s, and given up after 30 min; replace `DEFAULT_INTEGRATION_POLL_LIMIT`/`DEFAULT_INTEGRATION_POLL_INTERVAL`/`DEFAULT_INTEGRATION_STALENESS_LIMIT` as the timing source. Keep the staleness short-circuit (an abandoned tree whose last activity is older than the timeout costs no wait) and `--integration-retry-limit` as the number of LADDER rungs, which is not timing.
  - Depends on: E-01
  - Expected outcome: the ladder's wait timing matches the other four; the rung count is unchanged.
  - Execution state: pending

- [ ] E-05 AW WRITER LOCK. Make `commit_lock.writer_lock` wait through `contention_wait.wait_until` (default 30 min, 10 s poll, 60 s progress naming the holder's pid and owner, dead-holder takeover unchanged), and when the wait expires FAIL instead of proceeding unlocked: change the default so an expired wait raises the existing `required=True` error (callers that passed `required=False` explicitly, if any, are re-checked and switched; `git_commit_helper.offer_commit` is the main caller). Remove the "ran unserialized ... a retry is safe" note from `offer_commit`, since an unserialized commit can no longer happen.
  - Depends on: E-01
  - Expected outcome: an `aw` self-commit never runs outside the lock; behind a busy peer it waits with a progress line and fails only after 30 min.
  - Execution state: pending

- [ ] E-06 SETTER LOST THE RACE. In `git_commit_helper.offer_commit`, when `commit_lock.commit_isolated` returns `ISO_RACED` (another commit moved the branch between our snapshot and the compare-and-swap), re-run the whole isolated commit on the NEW tip through `contention_wait.wait_until` (10 s / 60 s / 30 min) instead of returning an error; each retry re-stages only our own paths, so a peer's work is never swept in, and the hooks run again each time. Success returns the normal committed outcome; expiry returns today's error with the preserved commit id. This removes the "self-commit skipped ... cherry-pick or retry" leftover seen twice on 2026-09-26/27 (`kkzgrk`, `oc3mhb`).
  - Depends on: E-05
  - Expected outcome: a setter whose commit races a peer commits after the peer finishes, with no manual follow-up.
  - Execution state: pending

### Task group 3: tests and record

- [ ] E-07 Add `tests/test_contention_wait.py`, OUTCOME tests only (no source-text pins), with an injected clock and sleep so nothing sleeps for real: (a) `wait_until` succeeds on the 4th try and reports once per 60 simulated seconds with the holder named; (b) it gives up at exactly 1800 simulated seconds with a detail naming what and who; (c) a held finalize lock that is released after 5 simulated minutes lets finalize proceed (both hosts through `finalize_with_contention_retry`); (d) `writer_lock` held by a live peer for longer than the timeout FAILS rather than yielding unlocked; (e) a setter whose isolated commit returns `ISO_RACED` once and then succeeds ends committed, with exactly its own paths in the commit; (f) `poll_for_integration_window` re-checks every 10 simulated seconds and stops at 30 minutes. Adjust any existing test in `tests/test_runner_shared.py` that asserts the OLD constants' VALUES only where it asserts timing (for example the ladder defaults), keeping the rung-count assertion `DEFAULT_INTEGRATION_RETRY_LIMIT == 10`. Add one `- Changed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md` in plain words, no em or en dashes: runs and `aw` commands now wait for a busy peer (checking every 10 seconds, reporting every minute, for up to 30 minutes) instead of failing or leaving a change uncommitted. Run the bare suite and `aw sanitize --agent`.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: six outcome tests pass; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Existing waits and their current numbers (measured at HEAD 2026-09-27): `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS = 120.0`, `FINALIZE_LOCK_POLL_SECONDS = 0.1`; `runner_shared.FINALIZE_LOCK_REATTEMPTS = 3`, `FINALIZE_LOCK_BACKOFF_SECONDS = 1.0`; `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0`, `INTEGRATION_LOCK_PROGRESS_SECONDS = 30.0`, poll `min(1.0, max(0.05, 30/30))`; `DEFAULT_INTEGRATION_POLL_LIMIT = 10`, `DEFAULT_INTEGRATION_POLL_INTERVAL = 30.0`, `DEFAULT_INTEGRATION_STALENESS_LIMIT = 3600.0`; `commit_lock.writer_lock(timeout=5.0, poll=0.05, required=False)` proceeds unlocked on expiry; `ISO_RACED` has no retry.
- All five are code-only; none dispatches an agent turn (verified by reading each; the agent retry budget is a separate mechanism, out of scope).
- Dead-holder takeover already exists for the finalize and writer locks; keep it.
- Tests: outcome only (maintainer standing rule); inject time instead of sleeping.
- Cite code by symbol; line numbers drift.

## Findings

| # | Location | Finding |
| --- | --- | --- |
| F-1 | runs of 2026-09-27 | Five verified items ended `fail-gate` only because a peer run held the finalize writer lock longer than about 8 minutes (7icz68, 4eecvh, 8y13kn, cnzrxb, 3rsdbj); all were recovered by hand. |
| F-2 | `commit_lock.writer_lock` | `required=False` by default: after 5 s it yields False and the caller commits unserialized, which is the exact interleaving the lock exists to prevent (its own docstring: pre-commit's stash/restore can destroy a peer's write). |
| F-3 | `git_commit_helper.offer_commit` / `commit_lock.ISO_RACED` | A lost compare-and-swap returns an error and leaves the setter's file change uncommitted; observed twice in this session (`kkzgrk`, `oc3mhb`), each fixed by a manual `aw commit`. |
| F-4 | `commit_lock.commit_isolated` hook retry | Not a wait: a formatter hook rewrites our file and rejects; re-staging its fix once is the whole remedy. Kept as is by maintainer ruling. |

## Proposed changes (ordered, validatable)

1. E-01 one helper, one policy.
2. E-02 to E-06 the five call sites.
3. E-07 outcome tests, CHANGELOG, suite.

## Deferred / out of scope (with reason)

- The agent retry budget (`--retry-budget`, per-kind counters).
  - Carrier-Declined: maintainer ruling 2026-09-27 keeps separate counters per failure kind; nothing is owed.
- The pre-commit hook re-stage retry.
  - Carrier-Declined: maintainer ruling 2026-09-27 keeps it as one immediate redo; repeating it on a timer cannot change the result.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_contention_wait.py`, six cases with an injected clock, asserting what the operator sees (progress lines, the give-up message) and what happens (finalize proceeds, writer lock fails instead of committing unlocked, a raced setter commits). Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended; spec `25kzda` does not fix these timings. CHANGELOG gains one line.

## Open questions

### OQ-01: One policy for all contention waits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-27 BY THE MAINTAINER when asked directly: all five check every 10 s, report every 60 s, fail after 30 min; the hook re-stage stays one immediate redo; the aw writer lock also waits the full 30 min and never commits unserialized.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste E-07 cases (a) and (b) passing, including the captured progress lines showing the 60 s cadence and the holder name.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste E-07 case (c) passing on both hosts, and `rg -n "FINALIZE_LOCK_WAIT_SECONDS|FINALIZE_LOCK_REATTEMPTS" agent_workflows` showing they are gone or reduced to aliases of the shared constants.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a test or scratch run showing `integration_lock` polls at 10 s and reports at 60 s against an injected clock, and that the deferred (`merge-retry`) outcome is unchanged on expiry.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste E-07 case (f) passing and the unchanged `DEFAULT_INTEGRATION_RETRY_LIMIT == 10` assertion.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste E-07 case (d) passing, and `rg -n "ran unserialized" agent_workflows` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste E-07 case (e) passing, showing the final commit contains only the setter's own paths.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_contention_wait.py -o addopts="" -v`, `git diff CHANGELOG.md` with `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing, the final summary line of a BARE `python3 -m pytest` with 0 failed, and `aw sanitize --agent` exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, how long code waits for a busy peer; one helper applied at five call sites.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: runs and `aw` commands may now wait up to 30 minutes for a busy peer (with a progress line every minute) instead of failing after seconds or minutes; the aw writer lock never commits unserialized again; a setter that loses a commit race retries on its own.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`. If the work requires another file, make the edit and JUSTIFY it at finalize (`--scope-reason`).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 9bq5o4 -- <paths>`; never `git add -A`, never push. The runner owns finalize in a lane. After execution set backlog `ibk7bt` `done` with `--evidence` citing the executed plan (it carries `Blocks-Release: next`).
