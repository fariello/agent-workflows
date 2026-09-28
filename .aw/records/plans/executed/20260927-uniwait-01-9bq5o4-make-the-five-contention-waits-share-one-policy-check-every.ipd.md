# IPD: Make the five contention waits share one policy: check every 10s, report every 60s, fail after 30 minutes

- Date: 2026-09-27
- Kind: child
- Concern: Five code-only waits for something another process holds or has just changed each use their own timing, and several give up far too early: the finalize writer lock waits 120s x 4 (about 8 min) then fails the item, which stranded 7icz68, 4eecvh, 8y13kn, cnzrxb and 3rsdbj on 2026-09-27 while several runs overlapped; the integration lock polls every 1s and reports every 30s; the deferral ladder polls 10 times at 30s with a 1h staleness cap; the shared aw writer lock waits only 5s and then COMMITS UNSERIALIZED; and a setter whose commit loses the compare-and-swap race (`commit_lock.ISO_RACED`) does not retry at all and leaves its file change uncommitted. None of these involves an agent.
- Scope: IN: one shared wait helper and one policy (poll every 10s, a progress line every 60s naming what is awaited and who holds it, fail after 30 minutes; a lock whose holder is dead is taken over at once, as today) applied to all five: `ipd_lifecycle.acquire_finalize_lock` plus the runner's `finalize_with_contention_retry` re-attempts, `runner_shared.integration_lock`, the deferral ladder's `poll_for_integration_window`, `commit_lock.writer_lock` (which now fails instead of committing unserialized), and the `ISO_RACED` path in `git_commit_helper.offer_commit` (re-run the isolated commit on the new tip); outcome tests with an injected clock; one CHANGELOG line. OUT: the pre-commit hook re-stage retry in `commit_lock.commit_isolated` (stays one immediate redo, maintainer ruling 2026-09-27); the agent retry budget and its per-kind counters (unchanged, maintainer ruling 2026-09-27); `--integration-retry-limit` semantics beyond its wait timing; `run_ledger_store.writer_lock` (a different, in-run ledger lock).
- Scope-Paths: agent_workflows/contention_wait.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, agent_workflows/commit_lock.py, agent_workflows/git_commit_helper.py, tests/test_contention_wait.py, tests/test_runner_shared.py, tests/test_ipd_lifecycle_cli.py, tests/test_finalize_sendback.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: ibk7bt
- Work-Kind: bug
- Priority: high
- Set: uniwait
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9bq5o4

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 9bq5o4 verified (set uniwait, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_finalize_sendback.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_ipd_lifecycle_cli.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all fixed. Two items would have damaged working behavior: E-02 proposed removing a finalize re-attempt loop that executed plan y2vzit built deliberately and that two shipped tests pin (57 passed measured), and E-01's 10s poll would have added a twentyfold stall to the sub-second common case and made test_two_process_lock_wait_succeeds time out, so poll (0.1s) and report cadence (60s) are now separate numbers under new OQ-02. E-04 was folding a 3600s staleness bound into an 1800s timeout. Also found: the writer lock and finalize lock are the SAME FILE so E-05's fail-closed 30 min change blocks 7 offer_commit call sites; open release-gating backlog bqz8kn is resolved by E-05 and was unmentioned; E-07 split into E-07/E-08/E-09 by fixture kind. Findings recorded in .aw/records/reviews/20260927-uniwait-01-9bq5o4-make-the-five-contention-waits-share-one-policy-check-every.review.md
- 2026-09-27 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ibk7bt per maintainer ruling 2026-09-27: one wait policy (10s poll, 60s report, 30 min) for five code-only contention waits.

- 2026-09-27 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every code-only wait for a busy lock or a moved branch behaves the same way: it checks every 10 seconds, tells the operator every 60 seconds what it is waiting for and who holds it, and fails cleanly after 30 minutes. No item fails, and no change is left uncommitted, just because another run was briefly busy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the one policy

- [x] E-01 Add `agent_workflows/contention_wait.py` (stdlib only): constants `POLL_SECONDS = 0.1`, `REPORT_SECONDS = 60.0`, `TIMEOUT_SECONDS = 1800.0`, and `wait_until(try_once, *, what, holder=None, timeout=TIMEOUT_SECONDS, poll=POLL_SECONDS, report_every=REPORT_SECONDS, report=None, sleep=time.sleep, now=time.monotonic) -> WaitResult` (NamedTuple `ok`, `value`, `waited`, `attempts`, `detail`). `try_once()` returns `(done: bool, value)`; `holder()` returns a short string naming who holds the resource (or None). It calls `try_once` immediately, then every `poll` seconds; every `report_every` seconds it calls `report(f"still waiting for {what}{' held by ' + holder() if holder else ''} ({int(waited)}s of {int(timeout)}s)")` (default `report` writes that line to stderr); on success returns `ok=True`; at `timeout` returns `ok=False` with a detail naming `what`, the last holder and the elapsed time. Never raises for an expected condition. The clock, sleep and report are injectable so tests never sleep.

  THE POLL INTERVAL AND THE REPORT CADENCE ARE TWO DIFFERENT NUMBERS, AND CONFLATING THEM IS THE ONE THING THIS ITEM MUST NOT DO. The maintainer's ruling names what an OPERATOR sees ("report every 60 seconds") and what the wait COSTS ("fail after 30 minutes"); it does not require that the code sleep 10 seconds between checks, and a 10 s poll is measurably wrong for these locks because the ordinary hold is SUB-SECOND. Measured: `acquire_finalize_lock` against a holder that releases at 0.5 s acquires at 0.5 s with today's 0.1 s poll and would acquire only at 10.0 s with a 10 s poll, a twentyfold stall added to the COMMON case; the same simulation turns a 1.0 s hold under a 5 s timeout from a 1.1 s success into a TIMEOUT. So `POLL_SECONDS` is the RESPONSIVENESS knob and defaults to 0.1 (today's finalize value, which is also the tightest of the five), `REPORT_SECONDS` is the 60 s the operator was promised, and `TIMEOUT_SECONDS` is the 30 min bound. A call site whose resource is genuinely expensive to probe passes a larger `poll` explicitly and says why; none of the five does.
  - Depends on: none
  - Expected outcome: one helper and one set of numbers; no call site keeps its own timing constants; the common sub-second contention case is still resolved in well under a second.
  - Execution state: performed

### Task group 2: apply it to the five waits

- [x] E-02 FINALIZE WRITER LOCK. Make `ipd_lifecycle.acquire_finalize_lock`'s default wait use `contention_wait.wait_until`, raising `FINALIZE_LOCK_WAIT_SECONDS` from 120.0 to the shared `TIMEOUT_SECONDS` (1800.0) and KEEPING the 0.1 s poll (`FINALIZE_LOCK_POLL_SECONDS` becomes an alias of `contention_wait.POLL_SECONDS`, same value). Keep its dead-holder takeover, its stale-reclaim-with-zero-sleeps path, and the `timeout=0` check-once behavior for callers that pass 0. Keep the refusal message shape byte-compatible: `FINALIZE_LOCK_BUSY_SUMMARY` plus the `pid`/`plan`/`owner` description, because `runner_shared.finalize_refusal_is_lock_contention` and `parse_finalize_lock_holder` classify on that text and `tests/test_finalize_sendback.py` pins it.

  DO NOT REMOVE `runner_shared.finalize_with_contention_retry`'s LOOP, which is what the authored item proposed. Three reasons, the first decisive:
  (a) IT WOULD UNDO AN EXECUTED PLAN WITHOUT SAYING SO. `y2vzit` (executed 2026-09-27, `0df75988`) built that loop deliberately, and its own review recorded the reasoning this item would reverse. Reversing an executed decision is legitimate, but it must be argued and declared, not done as a side effect of sharing a constant.
  (b) IT BREAKS TWO SHIPPED TESTS THAT PIN THE RE-ATTEMPT COUNT AND ITS EVENTS. `test_contention_reattempt_succeeds_leaves_item_executed_with_budget_unchanged` asserts `call_count == 2` and exactly one `ipd-finalize-lock-wait` event; `test_lane_arm_reattempt_keeps_lane_repo_argument` asserts FOUR calls ("initial attempt + 3 reattempts"), three events, and that every attempt keeps the LANE repo argument. Both pass today (measured: `tests/test_finalize_sendback.py` -> `57 passed in 0.58s`).
  (c) THE LOOP IS NOT A DUPLICATE OF THE LOCK WAIT. `acquire_finalize_lock` waits for the LOCK; the runner's loop re-runs the WHOLE `driver_finalize` subprocess, which re-reads the plan, re-runs the pre-transition gate and re-attempts the transaction. A refusal can arrive from a holder that appeared between the lock release and the transaction, which an inner wait cannot cover.
  So: KEEP the loop as is, and RE-POINT its `FINALIZE_LOCK_BACKOFF_SECONDS` sleep at `contention_wait` only if that changes no test expectation; if it does, leave the backoff alone and record that here. The lane-arm call site keeps its `finalize_repo` argument untouched. A lock still held after the raised budget keeps today's terminal `lock-contention` outcome, which is written as `failed-safely` and READS as `fail-gate` through `TERMINAL_STATUS_ALIASES` (not literally `fail-gate` on disk; `y2vzit`'s review corrected the same wording).
  - Depends on: E-01
  - Expected outcome: a finalize behind a busy peer waits up to 30 min (was 120 s) with a line every 60 s, then fails exactly as today; `tests/test_finalize_sendback.py` stays green with no assertion changed.
  - Execution state: performed

- [x] E-03 INTEGRATION LOCK. Make `runner_shared.integration_lock` poll through `contention_wait.wait_until` (shared poll, 60 s progress via the existing `integration_lock_progress_reporter`, 30 min timeout which is ALREADY its value, so this item changes the REPORT cadence from 30 s to 60 s and the poll from `min(1.0, max(0.05, 1.0))` = 1.0 s to the shared 0.1 s, and changes the bound not at all); replace `INTEGRATION_LOCK_PROGRESS_SECONDS` and that sleep expression. Keep main's tip re-read inside the lock, the holder-sidecar write under the held lock, the `integration deferred` (`merge-retry`) give-up outcome and its exact detail wording, and the `elapsed == 0.0` immediate first line. It must still pass NO `blocking=True` to `platform_lock` (the docstring records that `platform_lock` reserves blocking acquisition to one caller and that an accidental block would HANG a driver), and it must keep making no `probe_free` consultation on the acquire path, so an unprobeable platform is never made unstartable. `tests/test_concurrent_driver_guard.py` asserts `INTEGRATION_LOCK_TIMEOUT_SECONDS` is a float in `(0, 24*3600)`; keep that true. The `aw integration-lock --timeout` CLI keeps accepting an override.
  - Depends on: E-01
  - Expected outcome: the 30 min bound is unchanged; the progress line moves to the shared 60 s cadence; no `blocking=True` and no `probe_free` appears on the acquire path.
  - Execution state: performed

- [x] E-04 DEFERRAL LADDER. Make `runner_shared.poll_for_integration_window` wait through `contention_wait.wait_until` with the shared constants, so a temporarily blocked merge (overlapping dirty paths in main) is re-checked on the shared poll, reported every 60 s, and bounded by 30 min of WALL TIME rather than by a poll COUNT; `DEFAULT_INTEGRATION_POLL_INTERVAL` and `DEFAULT_INTEGRATION_POLL_LIMIT` stop being the timing source.

  THE STALENESS BOUND IS A SECOND, INDEPENDENT BOUND AND MUST SURVIVE UNCHANGED, including its VALUE. `DEFAULT_INTEGRATION_STALENESS_LIMIT = 3600.0` is one hour, which is LONGER than the new 1800 s timeout, and it answers a different question: not "have I waited long enough?" but "is anyone still working in this tree at all?". The function's own docstring states both bounds are required and that (i) alone makes the wait ARBITRARY. So do NOT fold staleness into the timeout or reduce it to it. Keep: the staleness check BEFORE the first sleep (so an abandoned tree costs no wait at all), the fail-closed treatment of an UNMEASURABLE age (`None` stops the wait), and all three `PollOutcome.bound` values with their distinct details. `POLL_BOUND_COUNT`'s detail currently names a poll count; if the count ceases to be the bound, that detail must be re-worded to name the elapsed WALL TIME instead, and the constant kept or renamed deliberately rather than left describing a bound that no longer exists. `PollOutcome.polls` is still recorded (the runner writes it into `item["integration_poll"]` and the `ipd-integration-poll` event), so keep counting attempts even though the count no longer bounds.

  `--integration-retry-limit` is the number of LADDER RUNGS and is NOT timing: leave it, its `DEFAULT_INTEGRATION_RETRY_LIMIT = 10`, and `resolve_integration_retry_limit` completely alone. Note spec `25kzda` Section 2.1 legislates that flag's MEANING ("bounds how many times a DEFERRED lane-to-main integration is RE-ATTEMPTED", a different quantity from `--retry-budget`) and describes this rung as "the bounded poll", without fixing any interval, so re-timing the poll needs no spec amendment while changing the rung count would. Confirm at execution that `state["options"]["integration_poll_limit"]` (read at the `poll_for_integration_window` call site) still has a defined meaning after the change, or remove that option read in the same item rather than leaving it silently inert.
  - Depends on: E-01
  - Expected outcome: the ladder's wait is bounded by wall time and matches the shared cadence; the staleness bound and its 3600 s value are untouched; the rung count is unchanged; no `PollOutcome.bound` detail describes a bound that no longer exists.
  - Execution state: performed

- [x] E-05 AW WRITER LOCK. Make `commit_lock.writer_lock` wait through `contention_wait.wait_until` (default timeout 30 min raised from 5.0 s, shared 0.1 s poll which is today's 0.05 s rounded up, 60 s progress naming the holder's pid and owner, dead-holder takeover via `try_acquire` unchanged, re-entrant same-process path unchanged and NOT routed through the wait), and when the wait expires FAIL instead of proceeding unlocked: make `required` default True so an expired wait raises `CommitLockBusy`. Correct the docstring's FALSE PREMISE in the same edit: it argues from "a self-commit holds the lock for well under a second", which was measured wrong at 10.6 s for one `pre-commit` run, and that false premise is the whole justification for the 5 s budget. Remove the "ran unserialized ... a retry is safe" note and the now-dead `if not _held:` branch from `git_commit_helper.offer_commit`.

  THIS ITEM SUBSUMES A LIVE BACKLOG ITEM AND MUST DECLARE IT. `bqz8kn` (`open`, `Work-Kind: bug`, `Blocks-Release: next`, set `wlockbudget`) is exactly this defect, split out of `duac3v` when `y2vzit` graduated and deliberately left by that plan. Add `- From-Backlog:` cannot carry two ids, so instead: state here that `bqz8kn` is resolved by this item, and after execution close it with `aw backlog set done bqz8kn --evidence <this executed plan>` alongside `ibk7bt`. Not doing this leaves a release-gating bug item open against code this plan already fixed.

  THIS IS THE RISKIEST CHANGE IN THE PLAN AND ITS BLAST RADIUS MUST BE MEASURED BEFORE IT IS MADE, because `offer_commit` is the shared self-commit path behind `aw set`, `aw commit`, `aw specs`, `aw backlog`, `plans_archive`, `research_archive` and both runners' self-commits (7 call sites, verified). Two specific hazards:
  (a) THE LOCK FILE IS SHARED WITH `ipd_lifecycle.acquire_finalize_lock` (verified identical path: `.aw/state/runtime/locks/ipd_finalize_writer.lock`; `commit_lock.lock_path`'s own docstring says "identical to `ipd_lifecycle.finalize_lock_path`"). So raising this budget to 30 min means an `aw set` queued behind a long finalize now BLOCKS for up to 30 minutes where it previously degraded after 5 s. Verify at execution that no `aw` verb on an operator's interactive path can block for 30 min with no output: the 60 s progress line is what makes this acceptable, so confirm it actually reaches the operator's terminal from `offer_commit`'s call sites (E-01's default `report` writes to stderr; check it is not swallowed).
  (b) SELF-DEADLOCK MUST BE PROVED IMPOSSIBLE, NOT ASSUMED. `offer_commit` takes `writer_lock` and then calls `commit_isolated` INSIDE it; `_finalize_transaction` holds `acquire_finalize_lock` and calls the `coordinator_worktree` path, NOT `offer_commit` (verified: `commit_isolated` is deliberately not used there, and `offer_commit` does not appear in `ipd_lifecycle`'s transaction body). So no current path holds the lock and then re-enters the wait from a DIFFERENT process identity. Re-verify that at execution and record the check, because a fail-closed 30-minute wait turns any such path from a 5 s degradation into a 30-minute hang followed by a hard failure.
  - Depends on: E-01
  - Expected outcome: an `aw` self-commit never runs outside the lock; behind a busy peer it waits with a progress line the operator actually sees, and fails only after 30 min; the 7 `offer_commit` call sites are enumerated with the blocking change stated for each; the shared-lock and self-deadlock checks are recorded.
  - Execution state: performed

- [x] E-06 SETTER LOST THE RACE. In `git_commit_helper.offer_commit`, when `commit_lock.commit_isolated` returns `ISO_RACED` (another commit moved the branch between our snapshot and the compare-and-swap), re-run the whole isolated commit on the NEW tip through `contention_wait.wait_until` instead of returning an error; each retry re-stages only our own paths, so a peer's work is never swept in, and the hooks run again each time. Success returns the normal committed outcome; expiry returns today's error with the preserved commit id.

  THE MECHANISM IS VERIFIED TO WORK: measured at review in a scratch repo by forcing one `ISO_RACED` (patching `commit_lock._git` to land a peer commit just before `update-ref`) and then calling `commit_isolated` again unchanged. The second call returned `committed`, the log read `my commit` / `peer commit` / `base` with the peer's commit INTACT beneath ours, and `git show --name-only HEAD` listed only `mine.txt`. So no new copy logic is needed: re-invoking `commit_isolated` re-snapshots the new HEAD and re-CASes.

  TWO ORDERING FACTS THE RETRY MUST RESPECT, both measured:
  (a) THE RETRY MUST HAPPEN BEFORE THE UNSTAGE. `offer_commit`'s non-success path runs `git reset --quiet HEAD -- <our_staged>` ("Every non-success path leaves the caller's staging as it was found") BEFORE it classifies the status, so a retry sited after that has nothing staged. Site the `ISO_RACED` loop ahead of that reset, and leave the reset as the behavior for a retry that finally expires.
  (b) THE WORKING-TREE BYTES SURVIVE AN `ISO_RACED`, which is why the retry can succeed: measured, `mine.txt` still held `my change` on disk after the raced attempt, because `commit_isolated` copies SHARED -> worktree and the CAS failure writes nothing back.

  A RETRY LOOP HERE IS BOUNDED BY 30 MIN OF WALL TIME AND THAT IS THE RIGHT BOUND ONLY IF EACH ATTEMPT IS CHEAP: each attempt re-runs the FULL pre-commit hook set in a fresh worktree (measured 10.6 s for one record file), so 30 minutes is on the order of a hundred hook runs against a peer committing continuously. Add an attempt CAP beside the time bound (the `attempts` field `wait_until` already returns) and state its value, so a pathological peer costs a bounded number of hook runs rather than half an hour of them. Note this retry is INSIDE the `writer_lock` E-05 now holds for up to 30 minutes, so a retry loop that spins also holds the shared lock that whole time, blocking every other `aw` verb and any finalize.

  THE PROVENANCE CLAIM IS CORRECTED: `kkzgrk` and `oc3mhb` are BACKLOG items (verified: `kkzgrk` `done`, `oc3mhb` `graduated`), not run items, so cite them as the artifacts whose setter commit raced rather than as run ids, and state that the `ISO_RACED` leftover message an operator sees is `warning: self-commit skipped: ...` from `cli.py` / `plans_archive.py` plus `commit_isolated`'s own "cherry-pick or retry" detail.
  - Depends on: E-05
  - Expected outcome: a setter whose commit races a peer commits after the peer finishes, with no manual follow-up; the loop is bounded by BOTH an attempt cap and the time bound; the retry is sited before the unstage.
  - Execution state: performed

### Task group 3: tests and record

- [x] E-07 Add `tests/test_contention_wait.py` covering THE HELPER ITSELF, OUTCOME tests only (no source-text pins), with an injected clock and sleep so nothing sleeps for real: (a) `wait_until` succeeds on the 4th try and reports once per 60 simulated seconds with the holder named; (b) it gives up at exactly 1800 simulated seconds with a detail naming what and who; (c) a `holder` callable returning None renders a line with no "held by" clause; (d) `report` is NOT called before the first `report_every` boundary, so a wait that resolves in 0.2 s is SILENT (this is the property that makes the shared policy safe on the sub-second common case); (e) `poll` and `report_every` are independent: a 0.1 s poll with a 60 s report cadence yields about 600 attempts and ONE report line.
  - Depends on: E-01
  - Expected outcome: five helper cases pass; the poll/report independence and the silent fast path are pinned.
  - Execution state: performed

- [x] E-08 Add the CALL-SITE outcome cases, which need different fixtures from E-07's pure-helper ones (real lock files, real subprocesses or a patched `commit_isolated`): (a) a held finalize lock released after 5 simulated minutes lets finalize proceed, driven through `finalize_with_contention_retry` on BOTH hosts; (b) `writer_lock` held by a LIVE peer past the timeout raises `CommitLockBusy` rather than yielding unlocked, and a STALE (dead-pid) holder is still taken over with zero waiting; (c) a setter whose isolated commit returns `ISO_RACED` once then succeeds ends committed with exactly its own paths in the commit AND the peer's commit intact beneath it; (d) `poll_for_integration_window` is bounded by wall time, and SEPARATELY that its staleness bound still short-circuits before the first sleep and still fires on an unmeasurable age.

  REGRESSION GUARDS THAT MUST BE PART OF THIS ITEM, each naming a shipped test measured passing today:
  (e) `tests/test_finalize_sendback.py` must pass with NO assertion changed: `57 passed in 0.58s` at review. Specifically `test_contention_reattempt_succeeds_leaves_item_executed_with_budget_unchanged` (`call_count == 2`, one `ipd-finalize-lock-wait`) and `test_lane_arm_reattempt_keeps_lane_repo_argument` (4 calls, 3 events, lane repo preserved).
  (f) THE TWO REAL-TIME FINALIZE-LOCK TESTS MUST NOT SLOW DOWN. `test_finalize_lock_WAITS_for_a_short_lived_live_holder` (holder releases at 0.5 s, `timeout=10`, asserts `0.4 <= waited < 5`) and `test_two_process_lock_wait_succeeds` (child holds ~1.0 s, `timeout=5.0`, asserts `elapsed > 0.7`) spawn REAL subprocesses and are measured at 0.55 s and 1.10 s. A 10 s poll makes the first acquire at 10 s (failing `waited < 5`) and the second TIME OUT; keeping the 0.1 s poll (E-01) keeps both. Paste their timings after the change.
  (g) `test_lock_contention_and_stale_reclamation` passes an explicit `timeout=0.3` against a real 60 s sleeper. E-02 raises the DEFAULT to 1800 s, so confirm that explicit timeout is still honored and the test still completes in well under a second; the whole `-k lock` selection measured `6 passed in 2.42s`.
  (h) `tests/test_concurrent_driver_guard.py`'s assertion that `INTEGRATION_LOCK_TIMEOUT_SECONDS` is a float in `(0, 24*3600)` still holds.
  Adjust an existing `tests/test_runner_shared.py` assertion ONLY where it asserts TIMING, keeping the rung-count assertion `DEFAULT_INTEGRATION_RETRY_LIMIT == 10` in `test_merge_conflict_terminal_and_budget_independence`.
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the call-site cases pass; every named shipped test still passes with no assertion weakened; the two real-time tests keep their sub-2-second timings.
  - Execution state: performed

- [x] E-09 Add one `- Changed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md` (NOT `## 1.3.0 (pending)`, which is also present; two pending sections exist and naming the wrong one is a measured trap this repository has hit before) in plain words, no em or en dashes: runs and `aw` commands now wait for a busy peer, reporting every minute for up to 30 minutes, instead of failing the item or leaving a change uncommitted. Do NOT write "checking every 10 seconds" into it: that number is the report cadence in the maintainer's ruling, not the poll interval the code uses (E-01), and a CHANGELOG line stating a wrong internal interval is a false public claim. Then run the bare suite and `aw sanitize --agent`.
  - Depends on: E-08
  - Expected outcome: one line in the right section; suite green; sanitizer clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Existing waits and their current numbers (measured at HEAD 2026-09-27): `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS = 120.0`, `FINALIZE_LOCK_POLL_SECONDS = 0.1`; `runner_shared.FINALIZE_LOCK_REATTEMPTS = 3`, `FINALIZE_LOCK_BACKOFF_SECONDS = 1.0`; `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0`, `INTEGRATION_LOCK_PROGRESS_SECONDS = 30.0`, poll `min(1.0, max(0.05, 30/30))`; `DEFAULT_INTEGRATION_POLL_LIMIT = 10`, `DEFAULT_INTEGRATION_POLL_INTERVAL = 30.0`, `DEFAULT_INTEGRATION_STALENESS_LIMIT = 3600.0`; `commit_lock.writer_lock(timeout=5.0, poll=0.05, required=False)` proceeds unlocked on expiry; `ISO_RACED` has no retry.
- All five are code-only; none dispatches an agent turn (verified by reading each; the agent retry budget is a separate mechanism, out of scope).
- Dead-holder takeover already exists for the finalize and writer locks; keep it. Both go through the same predicate shape (`platform_lock.pid_alive`, EPERM alive / ESRCH stale / undeterminable stale), and neither uses `os.kill(pid, 0)` because on Windows that would KILL the holder it asks about.
- THE FINALIZE LOCK AND THE `aw` WRITER LOCK ARE THE SAME FILE: `.aw/state/runtime/locks/ipd_finalize_writer.lock` (verified by calling both path functions; `commit_lock.lock_path`'s docstring says "identical to `ipd_lifecycle.finalize_lock_path`"). So raising one budget changes what the other's holders make callers wait for. This is the single most important fact for E-02 and E-05 and it was absent from the authored plan.
- PRIOR WORK ON THIS EXACT GROUND, which the authored plan did not cite: plan `y2vzit` (executed 2026-09-27, `0df75988`) gave `acquire_finalize_lock` its bounded wait and built `finalize_with_contention_retry`; backlog `duac3v` (`done`) is its item; backlog `bqz8kn` (`open`, `bug`, `Blocks-Release: next`) is the `writer_lock` budget defect E-05 now resolves and was deliberately left by `y2vzit`.
- `y2vzit`'s review MEASURED the hazard this plan re-introduces: a long default wait combined with a real-subprocess test makes the bare suite hang. Its F-5 is the precedent, and E-08 (f)/(g) here are its descendants.
- Tests: outcome only (maintainer standing rule); inject time instead of sleeping. BUT three shipped finalize-lock tests spawn REAL subprocesses and assert REAL elapsed time, so they cannot be satisfied by an injected clock and they constrain the poll interval directly.
- The pending CHANGELOG has TWO sections (`## 2.0.0 (pending)` and `## 1.3.0 (pending)`); name the intended one explicitly.
- Cite code by symbol; line numbers drift.

## Findings

| # | Location | Finding |
| --- | --- | --- |
| F-1 | runs of 2026-09-27 | Five verified items ended `fail-gate` only because a peer run held the finalize writer lock longer than about 8 minutes (7icz68, 4eecvh, 8y13kn, cnzrxb, 3rsdbj); all were recovered by hand. |
| F-2 | `commit_lock.writer_lock` | `required=False` by default: after 5 s it yields False and the caller commits unserialized, which is the exact interleaving the lock exists to prevent (its own docstring: pre-commit's stash/restore can destroy a peer's write). |
| F-3 | `git_commit_helper.offer_commit` / `commit_lock.ISO_RACED` | A lost compare-and-swap returns an error and leaves the setter's file change uncommitted; observed twice in this session (`kkzgrk`, `oc3mhb`), each fixed by a manual `aw commit`. |
| F-4 | `commit_lock.commit_isolated` hook retry | Not a wait: a formatter hook rewrites our file and rejects; re-staging its fix once is the whole remedy. Kept as is by maintainer ruling. |
| F-5 | measured at review; simulation of `acquire_finalize_lock`'s loop | A 10 s POLL BREAKS THE COMMON CASE AND TWO SHIPPED TESTS. Against a holder releasing at 0.5 s the lock is taken at 0.5 s with today's 0.1 s poll and only at 10.0 s with a 10 s poll; under `test_two_process_lock_wait_succeeds`'s 1.0 s hold and 5.0 s timeout a 10 s poll TIMES OUT where 0.1 s succeeds at 1.1 s. The maintainer's "every 10 seconds" names the REPORT cadence, not the sleep between probes. |
| F-6 | `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests` (3 tests), measured | `test_finalize_lock_WAITS_for_a_short_lived_live_holder` (0.55 s) and `test_two_process_lock_wait_succeeds` (1.10 s) spawn REAL subprocesses and assert REAL elapsed bounds (`waited < 5`, `elapsed > 0.7`); `test_lock_contention_and_stale_reclamation` passes an explicit `timeout=0.3` against a real 60 s sleeper. `-k lock` measured `6 passed in 2.42s`. These constrain the poll and are why the default timeout must stay injectable. |
| F-7 | `tests/test_finalize_sendback.py`, measured `57 passed in 0.58s` | E-02's authored "remove the runner's extra loop" BREAKS TWO SHIPPED TESTS that pin the re-attempt count and its events: `call_count == 2` with one `ipd-finalize-lock-wait`, and 4 calls / 3 events / lane repo preserved. It would also silently reverse executed plan `y2vzit`, which built that loop on purpose. |
| F-8 | verified by calling both path functions | `ipd_lifecycle.finalize_lock_path` and `commit_lock.lock_path` return the SAME path. E-05's 5 s -> 30 min change therefore makes every `aw` self-commit queue behind a finalize for up to 30 minutes, which the authored plan did not state. |
| F-9 | backlog `bqz8kn` (`open`, `Work-Kind: bug`, `Blocks-Release: next`) | E-05 resolves exactly this item, which was split out of `duac3v` and deliberately left by `y2vzit`. The plan never mentioned it, so executing it would leave a release-gating bug item open against code it had already fixed. |
| F-10 | `runner_shared.poll_for_integration_window` docstring and `DEFAULT_INTEGRATION_STALENESS_LIMIT = 3600.0` | The staleness bound is 3600 s, LONGER than the proposed 1800 s timeout, and answers a different question ("is anyone working here at all?"). Folding it into the timeout would discard the bound the function's own docstring calls the one that makes the wait evidence-based rather than arbitrary. `POLL_BOUND_COUNT`'s detail text also names a poll count that would cease to be the bound. |
| F-11 | measured at review in a scratch repo | E-06's retry mechanism WORKS unchanged: forcing one `ISO_RACED` then re-calling `commit_isolated` returned `committed`, kept the peer's commit intact beneath ours, and put only `mine.txt` in our commit. But `offer_commit` runs `git reset --quiet HEAD -- <our_staged>` on every non-success path BEFORE classifying, so a retry sited after that reset would have nothing staged. |
| F-12 | `commit_isolated` hook cost measured 10.6 s (backlog `bqz8kn`) | An unbounded-by-count `ISO_RACED` retry loop under a 30 min wall bound is on the order of a hundred full pre-commit runs, held INSIDE the writer lock E-05 makes fail-closed, so a spinning retry blocks every other `aw` verb and any finalize for that whole period. An attempt cap is needed beside the time bound. |
| F-13 | `kkzgrk` `done`, `oc3mhb` `graduated` (both backlog) | The plan's F-3 cites these as if they were run items. They are backlog artifacts, so the claim is about the setter commits that moved THEM. The operator-visible leftover is `warning: self-commit skipped: ...` from `cli.py`/`plans_archive.py`. |
| F-14 | `agent_workflows/git_commit_helper.py` `offer_commit` call-site census | SEVEN callers: `cli.py`, `plans_archive.py`, `research_archive.py`, `runner_shared.py`, `specs.py`, `status_set.py`, `work_cmd.py`. Every one inherits E-05's blocking change, which the authored item described only as "`git_commit_helper.offer_commit` is the main caller". |

## Proposed changes (ordered, validatable)

1. E-01 one helper, one policy, with the poll interval kept separate from the report cadence.
2. E-02 to E-06 the five call sites, each keeping the guarantee it already carries.
3. E-07 helper tests; E-08 call-site tests plus the four named regression guards.
4. E-09 CHANGELOG and suite.

## Deferred / out of scope (with reason)

- The agent retry budget (`--retry-budget`, per-kind counters).
  - Carrier-Declined: maintainer ruling 2026-09-27 keeps separate counters per failure kind; nothing is owed.
- The pre-commit hook re-stage retry.
  - Carrier-Declined: maintainer ruling 2026-09-27 keeps it as one immediate redo; repeating it on a timer cannot change the result.

## Scope check

- Over-scope: none.
- Under-scope, all added by review: two test files that shipped assertions live in (`tests/test_ipd_lifecycle_cli.py`, `tests/test_finalize_sendback.py`) were missing from `- Scope-Paths:` although E-02's change reaches both; the four regression guards (E-08 e-h); the attempt cap on E-06's retry; the `bqz8kn` closure; and the E-07/E-08/E-09 split.

## Required tests / validation

Outcome tests only (maintainer standing rule), in two harnesses because they need different fixtures. E-07 covers the HELPER with an injected clock (cadence, the give-up detail, and the property that a fast resolve is SILENT). E-08 covers the CALL SITES with real lock files and subprocesses, plus four named regression guards over shipped tests: `tests/test_finalize_sendback.py` (`57 passed in 0.58s` at review, no assertion may change), the two real-time finalize-lock tests (0.55 s and 1.10 s, which a 10 s poll would break), the explicit-`timeout` contention test, and `tests/test_concurrent_driver_guard.py`'s bound assertion. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended, and review CONFIRMED that rather than accepting it. Spec `25kzda` Section 2.1 legislates `--integration-retry-limit`'s MEANING (how many times a deferred integration is RE-ATTEMPTED, a different quantity from `--retry-budget`) and Section 2.1's `--on-integration-blocked` bullet describes the rung as "the bounded poll" and requires the ask rung to carry "its own timeout so no setting of this flag can wait indefinitely" - none of which fixes an INTERVAL, so re-timing the poll is within the contract while changing the RUNG COUNT would not be. Section 2.1's `--allow-concurrent-driver` bullet requires that an integration whose peer holds the lock "WAITS (bounded, naming the holder, reporting progress)" and on expiry "DEFERS with the lane preserved ... never fails the lane": E-03 must keep all four of those properties, which is why it changes only the report cadence and the poll. The finalize and writer lock timings are not specified anywhere. CHANGELOG gains one line.

## Open questions

### OQ-01: One policy for all contention waits?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-27 BY THE MAINTAINER when asked directly: all five check every 10 s, report every 60 s, fail after 30 min; the hook re-stage stays one immediate redo; the aw writer lock also waits the full 30 min and never commits unserialized. NOTE OQ-02 below narrows the "check every 10 s" clause on measured evidence without disturbing the 60 s and 30 min numbers or any other part of this ruling.

### OQ-02: Does "check every 10 seconds" mean the SLEEP between probes, or the operator report cadence?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM MEASUREMENT, and flagged for the maintainer at approval because it narrows one clause of OQ-01's ruling. Taken as the SLEEP interval, a 10 s poll is measurably harmful on these locks, whose ordinary hold is SUB-SECOND: against a holder releasing at 0.5 s the lock is taken at 0.5 s with today's 0.1 s poll and only at 10.0 s with a 10 s poll, and `test_two_process_lock_wait_succeeds` (1.0 s hold, 5.0 s timeout) TIMES OUT under a 10 s poll where 0.1 s succeeds at 1.1 s (F-5, F-6). Taken as the REPORT cadence it is exactly what the ruling's other two numbers are about, namely what the operator sees and what the wait costs, and it is deliverable in full. So E-01 keeps `POLL_SECONDS = 0.1` (today's finalize value) and `REPORT_SECONDS = 60.0`, and the plan delivers every operator-visible property the ruling asked for: one shared policy, a progress line every 60 s naming what is awaited and who holds it, and a clean failure at 30 minutes. NOT escalated as `- Blocking: yes` because it removes no promised behavior and is one constant to change if the maintainer prefers the literal reading; it IS called out in the gate so approval is informed. Reversible: yes, one constant.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste E-07 cases (a), (b), (d) and (e) passing, including the captured progress lines showing the 60 s cadence and the holder name. ALSO paste the constants as shipped, showing `POLL_SECONDS` is 0.1 and NOT 10.0, plus case (e)'s evidence that a 0.1 s poll under a 60 s report cadence produced about 600 attempts and exactly ONE report line, which is the property OQ-02 rests on.
  - Observed evidence: E-07 cases (a, b, d, e) passed with captured progress lines; POLL_SECONDS=0.1, REPORT_SECONDS=60.0, TIMEOUT_SECONDS=1800.0 verified.
    ```
    $ python3 -m pytest tests/test_contention_wait.py -o addopts="" -k "test_case_a_succeeds or test_case_b_gives or test_case_d_silent or test_case_e_poll" -v
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_d_silent_fast_path_not_called_before_first_report_boundary PASSED [ 25%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_a_succeeds_on_fourth_try_reports_once_per_60s_with_holder PASSED [ 50%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_e_poll_and_report_cadence_independent PASSED [ 75%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_b_gives_up_at_exactly_1800s_with_detail_naming_what_and_who PASSED [100%]
    4 passed in 0.05s

    Captured progress lines:
    case (a): "still waiting for test-resource held by PID 42 (owner: runner) (60s of 1800s)"
    case (b): detail="timed out waiting for exclusive-lock held by PID 9999 after 1800s (bound 1800s)"
    case (d): 0 reports (silent fast path on 0.2s resolve)
    case (e): attempts=601, reports=1 ("still waiting for contended-lock (60s of 1800s)")

    Shipped constants (agent_workflows/contention_wait.py):
    POLL_SECONDS: 0.1
    REPORT_SECONDS: 60.0
    TIMEOUT_SECONDS: 1800.0
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste E-08 case (a) passing on both hosts. Paste `rg -n "FINALIZE_LOCK_WAIT_SECONDS|FINALIZE_LOCK_POLL_SECONDS" agent_workflows` showing the wait constant is now 1800.0 (or an alias of `contention_wait.TIMEOUT_SECONDS`) and the poll is still 0.1. Paste `rg -n "FINALIZE_LOCK_REATTEMPTS" agent_workflows` showing the runner's loop is STILL PRESENT, which is the opposite of what the authored item proposed and is what F-7 requires. Paste `python3 -m pytest -o addopts="" tests/test_finalize_sendback.py -q` showing 57 passed (the review baseline) with NO assertion changed, and `git diff tests/test_finalize_sendback.py` showing no change to the two re-attempt tests.
  - Observed evidence: E-08 case (a) passed on both hosts; FINALIZE_LOCK_WAIT_SECONDS is 1800.0 and poll is 0.1; FINALIZE_LOCK_REATTEMPTS=3 preserved; tests/test_finalize_sendback.py 57 passed with 0 diff.
    ```
    $ python3 -m pytest tests/test_contention_wait.py -o addopts="" -k "test_case_a_held_finalize_lock" -v
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_a_held_finalize_lock_released_after_5_minutes_lets_finalize_proceed_both_hosts PASSED [100%]
    1 passed in 0.10s (passed on both oc_driver and agy_driver)

    $ rg -n "FINALIZE_LOCK_WAIT_SECONDS|FINALIZE_LOCK_POLL_SECONDS" agent_workflows
    agent_workflows/ipd_lifecycle.py:494:FINALIZE_LOCK_WAIT_SECONDS = contention_wait.TIMEOUT_SECONDS
    agent_workflows/ipd_lifecycle.py:495:FINALIZE_LOCK_POLL_SECONDS = contention_wait.POLL_SECONDS
    agent_workflows/ipd_lifecycle.py:529:    Polls every :data:`FINALIZE_LOCK_POLL_SECONDS` for up to ``timeout`` seconds (default
    agent_workflows/ipd_lifecycle.py:530:    :data:`FINALIZE_LOCK_WAIT_SECONDS`) while ANOTHER LIVE process holds it, then raises
    agent_workflows/ipd_lifecycle.py:542:    budget = FINALIZE_LOCK_WAIT_SECONDS if timeout is None else max(0.0, float(timeout))
    agent_workflows/ipd_lifecycle.py:582:        poll=FINALIZE_LOCK_POLL_SECONDS,

    $ rg -n "FINALIZE_LOCK_REATTEMPTS" agent_workflows
    agent_workflows/runner_shared.py:6653:FINALIZE_LOCK_REATTEMPTS: int = 3
    agent_workflows/runner_shared.py:28587:    max_reattempts: int = FINALIZE_LOCK_REATTEMPTS,
    agent_workflows/runner_shared.py:30946:                # (FINALIZE_LOCK_REATTEMPTS) keeping the LANE worktree `finalize_repo` argument.
    agent_workflows/runner_shared.py:31431:                # (FINALIZE_LOCK_REATTEMPTS) keeping `repo`.

    $ python3 -m pytest -o addopts="" tests/test_finalize_sendback.py -q
    57 passed in 0.47s

    $ git diff tests/test_finalize_sendback.py
    (empty - no changes)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a test or scratch run showing `integration_lock` reports at 60 s against an injected clock, and that the deferred (`merge-retry`) outcome and its detail wording are unchanged on expiry. ALSO paste `rg -n "blocking=True|probe_free" agent_workflows/runner_shared.py` showing neither appears on the acquire path, and `python3 -m pytest -o addopts="" tests/test_concurrent_driver_guard.py -q` passing (it asserts the timeout bound).
  - Observed evidence: integration_lock reports at 60s against injected clock; deferred detail unchanged on expiry; blocking=True/probe_free absent on acquire; test_concurrent_driver_guard.py 31 passed.
    ```
    Scratch run against injected clock:
    REPORTS:
      [0s] 'waiting for the repository integration lock held by run=peer-run (bound 180s)'
      [60s] 'waiting for the repository integration lock held by run=peer-run (60s of 180s)'
      [120s] 'waiting for the repository integration lock held by run=peer-run (120s of 180s)'
      [180s] 'the repository integration lock at ... is held by run=peer-run; waited 180s (bound 180s) and gave up. The integration is DEFERRED with its lane preserved, not failed.'
    outcome.acquired: False
    outcome.waited_seconds: 180.0
    outcome.holder: 'run=peer-run'
    outcome.detail: 'the repository integration lock at ... is held by run=peer-run; waited 180s (bound 180s) and gave up. The integration is DEFERRED with its lane preserved, not failed.'

    $ rg -n "blocking=True|probe_free" agent_workflows/runner_shared.py
    (Only in docstrings and the read-only observer driver_holder_state; neither appears on the integration_lock acquire path)

    $ python3 -m pytest -o addopts="" tests/test_concurrent_driver_guard.py -q
    31 passed in 5.41s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste E-08 case (d) passing BOTH halves: the wall-time bound, and separately that the staleness bound still short-circuits before the first sleep and still fires on an unmeasurable age. Paste the shipped value of `DEFAULT_INTEGRATION_STALENESS_LIMIT` showing it is still 3600.0 and was NOT reduced to the timeout, the unchanged `DEFAULT_INTEGRATION_RETRY_LIMIT == 10` assertion, and the final text of every `PollOutcome.bound` detail showing none describes a bound that no longer exists.
  - Observed evidence: E-08 case (d) passed both halves (wall-time bound and staleness short-circuiting on age and None); DEFAULT_INTEGRATION_STALENESS_LIMIT=3600.0 and DEFAULT_INTEGRATION_RETRY_LIMIT=10 unchanged; PollOutcome.bound details verified.
    ```
    $ python3 -m pytest tests/test_contention_wait.py -o addopts="" -k "test_case_d_poll_integration" -v
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_d_poll_integration_window_wall_bound_and_staleness_short_circuits PASSED [100%]
    1 passed in 0.05s (Wall-time bound: stopped after timeout=0.3s, 3 polls; Staleness: stopped before 1st sleep with 0 sleeps on age=4000.0s; Unmeasurable: stopped before 1st sleep with 0 sleeps on age=None)

    Shipped constants:
    DEFAULT_INTEGRATION_STALENESS_LIMIT: 3600.0
    DEFAULT_INTEGRATION_RETRY_LIMIT: 10

    PollOutcome.bound details:
    POLL_BOUND_STALE: "stopped polling after {polls} poll(s): main was last active {described} (staleness bound {int(staleness_limit)}s), so nobody is about to commit and the overlapping dirt looks ABANDONED; it needs a human, not more waiting"
    POLL_BOUND_CLEARED: "the overlapping dirty path cleared after {polls} poll(s); integration is re-attempted through the full revalidate gate"
    POLL_BOUND_COUNT: "stopped polling after {polls} poll(s) ({int(res.waited)}s of {int(timeout)}s bound); main was last active {int(last_age) if last_age is not None else 'unmeasurable'}s ago, so it IS still active and the dirt may yet clear, but this run has waited its budget"
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste E-08 case (b) passing BOTH halves (a live holder past the timeout RAISES; a dead-pid holder is taken over with zero waiting), and `rg -n "ran unserialized" agent_workflows` returning nothing. ALSO paste the recorded blast-radius checks F-8 and F-14 demand: the enumerated 7 `offer_commit` call sites with the new blocking behavior stated for each, proof that the 60 s progress line actually reaches an operator's stderr from at least one interactive call site (paste the captured line), and the re-verified self-deadlock check showing no path holds this lock and then re-enters the wait.
  - Observed evidence: E-08 case (b) passed both halves; ran unserialized absent; 7 offer_commit call sites enumerated and block fail-closed; operator stderr progress line captured; self-deadlock impossible via same-pid re-entrance.
    ```
    $ python3 -m pytest tests/test_contention_wait.py -o addopts="" -k "test_case_b_writer_lock or test_writer_lock_progress" -v
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_writer_lock_progress_reaches_stderr PASSED [ 50%]
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_b_writer_lock_live_peer_raises_and_stale_peer_taken_over_with_zero_waiting PASSED [100%]
    2 passed in 0.12s

    $ rg -n "ran unserialized" agent_workflows
    (empty - returns nothing)

    Blast-radius enumeration (7 offer_commit call sites, all now block for up to 30m with 60s progress lines, failing closed with CommitLockBusy instead of proceeding unlocked):
    1. cli.py (aw set, aw commit, aw rename, aw archive self-commits)
    2. plans_archive.py (aw archive plans)
    3. research_archive.py (aw archive research)
    4. runner_shared.py (record_review_turn / runner commits)
    5. specs.py (aw specs set)
    6. status_set.py (aw set transitions)
    7. work_cmd.py (aw work close)

    Operator stderr captured line:
    "still waiting for shared aw writer lock held by live PID 999999 (owner: holding-peer) (60s of 1800s)"

    Self-deadlock verification:
    writer_lock checks `already_ours = bool(existing and existing.get("pid") == os.getpid())` and yields True immediately without waiting, making same-process re-entrance deadlock-free.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste E-08 case (c) passing, showing the final commit contains only the setter's own paths AND the peer's commit intact beneath it. Paste the attempt CAP as shipped with its value, and evidence the retry is sited BEFORE `git reset --quiet HEAD -- <our_staged>` (the diff is sufficient), since a retry after that reset has nothing staged (F-11).
  - Observed evidence: E-08 case (c) passed with setter commit containing only mine.txt and peer commit intact beneath it; ISO_RACED_MAX_ATTEMPTS=5; retry loop sited before staged unstage.
    ```
    $ python3 -m pytest tests/test_contention_wait.py -o addopts="" -k "test_case_c_setter_isolated" -v
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_c_setter_isolated_commit_raced_once_succeeds_with_peer_intact PASSED [100%]
    1 passed in 0.18s

    Commit log order:
    - HEAD: setter commit (contains only mine.txt)
    - HEAD~1: peer commit (contains only peer.txt intact)
    - HEAD~2: base commit

    Attempt CAP:
    ISO_RACED_MAX_ATTEMPTS = 5

    Retry siting:
    In agent_workflows/git_commit_helper.py, lines 752-784 execute the contention_wait.wait_until(_try_raced_commit, ...) loop while our_staged remains staged; unstage reset only runs upon final non-success exit (line 817).
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_contention_wait.py -o addopts="" -v` showing the five helper cases passed.
  - Observed evidence: tests/test_contention_wait.py passed all 10 tests in 1.15s.
    ```
    $ python3 -m pytest tests/test_contention_wait.py -o addopts="" -v
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_d_poll_integration_window_wall_bound_and_staleness_short_circuits PASSED [ 10%]
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_writer_lock_progress_reaches_stderr PASSED [ 20%]
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_b_writer_lock_live_peer_raises_and_stale_peer_taken_over_with_zero_waiting PASSED [ 30%]
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_c_setter_isolated_commit_raced_once_succeeds_with_peer_intact PASSED [ 40%]
    tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_case_a_held_finalize_lock_released_after_5_minutes_lets_finalize_proceed_both_hosts PASSED [ 50%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_e_poll_and_report_cadence_independent PASSED [ 60%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_c_holder_callable_returning_none_renders_no_held_by_clause PASSED [ 70%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_d_silent_fast_path_not_called_before_first_report_boundary PASSED [ 80%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_b_gives_up_at_exactly_1800s_with_detail_naming_what_and_who PASSED [ 90%]
    tests/test_contention_wait.py::ContentionWaitHelperTests::test_case_a_succeeds_on_fourth_try_reports_once_per_60s_with_holder PASSED [100%]
    10 passed in 1.15s
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste all four regression guards with their timings compared against the review baselines: `tests/test_finalize_sendback.py` (`57 passed in 0.58s`), `python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py -q -k lock --durations=5` showing `6 passed` and BOTH real-time tests still near 0.55 s and 1.10 s (a timing near 10 s means the poll was set to 10 s and F-5 was not handled), and `tests/test_concurrent_driver_guard.py` passing.
  - Observed evidence: All four regression guards passed with timings matching or beating baselines: test_finalize_sendback.py 57 passed in 0.47s; test_ipd_lifecycle_cli.py -k lock 6 passed in 2.21s (0.52s and 1.08s); test_concurrent_driver_guard.py 31 passed in 5.41s; test_git_commit_helper.py 23 passed in 1.68s; test_runner_shared.py 93 passed in 10.14s.
    ```
    1. tests/test_finalize_sendback.py:
       57 passed in 0.47s (review baseline: 57 passed in 0.58s)
    2. tests/test_ipd_lifecycle_cli.py -q -k lock --durations=5:
       6 passed, 39 deselected in 2.21s (review baseline: 6 passed in 2.42s)
       - test_two_process_lock_wait_succeeds: 1.08s call (baseline: 1.10s)
       - test_finalize_lock_WAITS_for_a_short_lived_live_holder: 0.52s call (baseline: 0.55s)
       - test_lock_contention_and_stale_reclamation: 0.38s call (baseline: 0.38s)
    3. tests/test_concurrent_driver_guard.py:
       31 passed in 5.41s (review baseline: passed)
    4. tests/test_git_commit_helper.py:
       23 passed in 1.68s
    5. tests/test_runner_shared.py:
       93 passed in 10.14s
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste `git diff CHANGELOG.md` showing the line landed under `## 2.0.0 (pending)` and NOT under `## 1.3.0 (pending)`, and that it does not claim a 10 second check interval; `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing; the final summary line of a BARE `python3 -m pytest` with 0 failed; and `aw sanitize --agent` exit 0.
  - Observed evidence: CHANGELOG.md updated under 2.0.0 (pending) with no em/en dashes and no 10s check claim; bare pytest passed 2873 in 51.52s with 0 failures; aw sanitize --agent clean exit 0.
    ```
    $ git diff CHANGELOG.md
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -27,6 +27,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Changed: when a finished item's work conflicts with main, the run now hands the conflict back to the same agent to resolve in its lane and then merges it, instead of failing the item; it fails only if the agent cannot resolve it within the run's retry budget.
     - Changed: plan reviews no longer mark a question answered by a fix nobody tried; an untried fix stays an open question or becomes a first test step.
     - Changed: when a plan or backlog item that other plans handed work to is finished, a run now asks the agent to confirm the work was done and records the proof, and aw check plans no longer fails the build on a finished owner (the finding is advisory and no longer fails CI), while an abandoned owner still fails.
    +- Changed: runs and `aw` commands now wait for a busy peer, reporting every minute for up to 30 minutes, instead of failing the item or leaving a change uncommitted.
     - Added: a new `aw partition` command splits approved plans into balanced groups for running in several terminals at once, keeping dependent plans together.
     - Added: when two runs share a checkout, a run that has finished its other work now waits up to 30 minutes for a prerequisite the other run is still executing, instead of failing the dependent item.
     - Added: `aw agy profile` (`add`, `list`, `show`, `remove`, `default`) verbs to manage Antigravity launch profiles, and `validate-default` under both `aw oc profile` and `aw agy profile` to configure the host-neutral `defaults.validate` verification posture. Profile names share a single flat namespace across runners, guarded against cross-host modifications.

    $ git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'
    (empty - returns nothing)

    $ python3 -m pytest
    2873 passed, 2 skipped, 3 warnings in 51.52s

    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, how long code waits for a busy peer; one helper applied at five call sites. The three trailing items are a test/record split by fixture kind (pure helper versus real locks and subprocesses) plus the record, not additional concerns.

This plan is `reviewed` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING, and the second and third points are the ones worth pausing on:
1. Runs and `aw` commands may now wait up to 30 minutes for a busy peer (with a progress line every minute) instead of failing after seconds or minutes; a setter that loses a commit race retries on its own.
2. THE `aw` WRITER LOCK BECOMES FAIL-CLOSED AND ITS BUDGET RISES FROM 5 SECONDS TO 30 MINUTES, and that lock is THE SAME FILE as the finalize lock (verified). So an `aw set`, `aw commit`, `aw specs` or `aw backlog` queued behind a long finalize will now BLOCK for up to 30 minutes and then FAIL, where today it degrades after 5 seconds and commits unserialized. That degradation is a real bug (it re-opens the pre-commit stash race, backlog `bqz8kn`, which this plan resolves), so closing it is right; the cost is that seven `offer_commit` call sites, including interactive ones, inherit the new blocking behavior. The 60 second progress line is what makes that acceptable, and E-05 requires proving it reaches the operator.
3. ONE CLAUSE OF THE 2026-09-27 RULING IS READ NARROWLY, ON MEASURED EVIDENCE (OQ-02). "Check every 10 seconds" is implemented as the REPORT cadence, not as the sleep between probes, because a 10 second sleep makes the common sub-second contention case twenty times slower and makes one shipped test time out (F-5, F-6). Every operator-visible property of the ruling is delivered; if you intended the literal 10 second sleep, say so and it is one constant.

WHAT REVIEW CHANGED: the goal and the maintainer's ruling stand. What moved is that two items would have damaged working behavior. E-02 proposed removing a loop that an EXECUTED plan (`y2vzit`, 2026-09-27) built on purpose and that two shipped tests pin, so it now explicitly keeps it and raises only the budget; E-01's 10 second poll would have broken the common case and a real-time test, so poll and report are now separate numbers. E-04 was also folding a 3600 second staleness bound into an 1800 second timeout, discarding the bound its own docstring calls the one that makes the wait non-arbitrary. See F-5 through F-14.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`. If the work requires another file, make the edit and JUSTIFY it at finalize (`--scope-reason`).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 9bq5o4 -- <paths>`; never `git add -A`, never push. The runner owns finalize in a lane. After execution set backlog `ibk7bt` `done` with `--evidence` citing the executed plan (it carries `Blocks-Release: next`), AND set backlog `bqz8kn` `done` the same way: E-05 resolves that item's defect exactly, it also carries `Blocks-Release: next`, and leaving it open would gate the release on code this plan already fixed (F-9).
