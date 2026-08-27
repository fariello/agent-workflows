- Id: kjzlgw
- Status: open
- Set: runnerstop
- Priority: high
- Kind: feature
- Summary: Graceful-quit protocol for aw oc/agy run: 4 stop levels (after-call / after-set / now / now-clean) via escalating signals + aw oc run stop <run-id>, each ending in a coherent ledger+lock+worktree cleanup (no orphaned children, no stale lock, no contaminated tree)

## Workflow history
- 2026-08-27 created (aw backlog): Graceful-quit protocol for aw oc/agy run: 4 stop levels (after-call / after-set / now / now-clean) via escalating signals + aw oc run stop <run-id>, each ending in a coherent ledger+lock+worktree cleanup (no orphaned children, no stale lock, no contaminated tree)

Problem (observed 2026-08-27): `aw oc run` has NO graceful stop. SIGTERM makes the driver print "Terminated" and exit, but its child `opencode` agent is reparented to init (orphaned, still writing the tree), the `driver.lock` is left stale (holds a dead PID), and the working tree is left mid-edit. There is no way to say "wind down cleanly."

Requirement: four operator-selectable stop levels, ALL ending in a coherent stop (the difference is only how much in-flight work completes first - none is "just die"):
1. STOP-AFTER-CALL: let the in-flight IPD's agent turn finish (write outcome JSON, checkpoint ledger), do not dequeue the next item, exit clean.
2. STOP-AFTER-SET: finish the rest of THIS set's queue, then stop before any next set.
3. STOP-NOW (as-soon-as-safe): signal the running agent to abort at its next safe checkpoint; do not wait for completion; still write a coherent 'aborted' ledger state + release the lock.
4. STOP-NOW-CLEAN: hard-interrupt the agent immediately, then RECONCILE - mark the run interrupted, write `unknown_outcome` where the agent result is indeterminate, reap/verify child processes are dead, release the lock, quarantine/restore partial worktree edits.

Trigger UX: escalating signals + an out-of-band command. First SIGINT (Ctrl-C) = level 1; repeated Ctrl-C escalates 1 -> 3 -> 4 ("press again to stop harder"); SIGTERM = level 3. Plus `aw oc run stop <run-id> --after-call|--after-set|--now|--now-clean` so a second terminal can request any level remotely/scriptably. All levels MUST: reap child agent processes (no orphans reparented to init), release `driver.lock`, and leave the run ledger in a coherent terminal/interrupted state.

Mechanism: the driver POLLS a stop-request flag/signal at cooperative checkpoints (between agent turns for levels 1-2; within a turn at the next safe point for level 3); level 4 is interrupt + the reconciliation routine. NOT a raw kill.

Relations: this is the DELIBERATE counterpart to CRASH recovery - it reuses the same reconciliation routine as the active-work-lifecycle recovery design (research ud28vy: staleness/takeover, executing-reconcile-before-resume/rollback) and the run-ledger `unknown_outcome` model. Cleaner per-run worktree isolation (the missing-isolation gap seen this session) makes levels 3/4 cleanup far simpler. Related driver items: ctt412 (driver must commit through aw commit/aw finish, blocks 2.0.0), and the orchestrator-queued-before-child + uninformative-blocked-output driver defects observed this session. Feeds a future runner-lifecycle spec (stop protocol + ledger interaction + active-work recovery); decide spec-vs-IPD when picked up.

Priority high, NOT release-blocking (2.0.0 may ship with kill-only stop; this lands shortly after). Origin: user - the killed runners 'just said Terminated'; the four levels are the user's design.
