- Id: duac3v
- Status: open
- Blocks-Release: next
- Set: finlockwait
- Priority: high
- Work-Kind: bug
- Summary: aw ipd finalize fails an item terminally (fail-gate) when the shared writer lock is momentarily held by a peer's self-commit, instead of waiting or retrying

## Workflow history
- 2026-09-26 created (aw backlog): Filed from run run-20260926T051642Z-116672 triage: 9npssm lost its finalize to lock contention from a concurrent run.

OBSERVED. Run run-20260926T051642Z-116672 (aw agy run) item 9npssm: executed and VERIFIED, pre-transition lint conforming, yet ended fail-gate with 'ipd finalize writer lock held by active PID 402458 (plan None)' (events.jsonl line 17, 05:43:32Z). A concurrent run (run-20260926T051623Z-115951, started 19s earlier in the same checkout) was finalizing/self-committing ooydp3 at that moment (commit 7865e26d at 05:43:28Z, ipd-finalized 05:47:24Z). 'plan None' identifies the holder as a commit_lock.writer_lock holder (git_commit_helper.offer_commit, used by every self-committing aw verb), which writes 'owner' but no 'plan_id'. The exact holder is NOT recorded; candidates in that window include the peer run's ooydp3 commits and an interactive `aw specs set` commit (870e193b, 05:43:42Z) in the same checkout. By 05:4x the PID was gone and the lock file is absent now.

WHY IT IS A DEFECT. Two independent causes combine: (1) ipd_lifecycle.acquire_finalize_lock does not wait at all; a live holder raises TransactionLockError immediately, although commit_lock.writer_lock already waits (default 5s) for exactly this case. Its docstring's claim that a self-commit holds the lock 'for well under a second' is also FALSE here: the lock is held across the whole pre-commit hook window, and `pre-commit run` on a single record file measured 10.6s on 2026-09-26, so even writer_lock's own 5s budget can expire and degrade to an unserialized commit. (2) runner_shared.finalize_refusal_is_retryable admits only the pre-transition and stale-receipt classes, so a transient lock refusal (retryable: false, events line 17) becomes a terminal fail-gate. Cost: a 24-minute verified turn left unintegrated, its lane now conflicting with main (agent_workflows/agy_runipd.py import block) because main moved on, and backlog tm5vnx left open. Concurrent drivers in one checkout are a supported configuration (--allow-concurrent-driver), so this recurs whenever two runs finalize close together.

FIX SHAPE (for the plan to decide). Either make acquire_finalize_lock wait with a bounded budget like writer_lock, or classify TransactionLockError as a retryable finalize refusal with backoff, or both. The lock-contention diagnostic should also name the holder's owner string when plan_id is absent, instead of printing 'plan None'.

PREVENTION, beyond the fix (triage 2026-09-26). (a) Record the holder: a refusal that says 'plan None' cannot be attributed afterwards; the lock payload's owner string, and ideally the command line, must reach the diagnostic and the run event. (b) A finalize refusal whose CAUSE is contention must never be terminal: the plan's work and bookkeeping are complete, so the correct outcome is defer-and-retry (as integrate_under_repository_lock already does for the integration lock, INTEGRATION_LOCK_TIMEOUT_SECONDS), not fail-gate. (c) Test it: two processes, one holding writer_lock across a simulated slow hook, the other finalizing, asserting the finalize completes rather than refusing.
