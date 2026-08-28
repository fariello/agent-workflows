- Id: kjzlgw
- Status: open
- Blocks-Release: next
- Set: runnerstop
- Priority: high
- Kind: feature
- Summary: Graceful-quit protocol for aw oc/agy run: 4 stop levels (after-call / after-set / now / now-clean) via escalating signals + aw oc run stop <run-id>, each ending in a coherent ledger+lock+worktree cleanup (no orphaned children, no stale lock, no contaminated tree)

## Workflow history
- 2026-08-28 open (aw set): status set to open
- 2026-08-27 created (aw backlog): Graceful-quit protocol for aw oc/agy run: 4 stop levels (after-call / after-set / now / now-clean) via escalating signals + aw oc run stop <run-id>, each ending in a coherent ledger+lock+worktree cleanup (no orphaned children, no stale lock, no contaminated tree)

Problem (observed 2026-08-27): `aw oc run` has NO graceful stop. SIGTERM makes the driver print "Terminated" and exit, but its child `opencode` agent is reparented to init (orphaned, still writing the tree), the `driver.lock` is left stale (holds a dead PID), and the working tree is left mid-edit. There is no way to say "wind down cleanly."

INVARIANT (applies to ALL four levels; NOT a property of any single level): every stop leaves the system COHERENT - all child agent processes reaped (no orphans reparented to init), `driver.lock` released, the run ledger in a coherent terminal/interrupted state, and partial worktree edits quarantined/restored (never left contaminating the tree). "Clean" is the guarantee, not a level. The same cleanup/reconciliation routine runs at the END of every level. The FOUR LEVELS DIFFER ON ONE AXIS ONLY: how much in-flight work is allowed to COMPLETE before that (always-clean) shutdown. None is "just die" (which is what SIGTERM does today).

1. STOP-AFTER-CALL: let the in-flight IPD's agent turn finish (write outcome JSON, checkpoint ledger), do not dequeue the next item, then clean-stop.
2. STOP-AFTER-SET: finish the rest of THIS set's queue, then clean-stop before any next set.
3. STOP-NOW (at next safe checkpoint): stop the current agent turn at its next SAFE checkpoint (do not let it finish), then clean-stop. Because it stopped at a defined point, the interrupted item's disposition is KNOWN (recorded as stopped/incomplete).
4. STOP-NOW-FORCE (immediate interrupt): interrupt the current agent turn IMMEDIATELY (not at a checkpoint), then clean-stop. Because it was interrupted mid-operation, the item's outcome may be INDETERMINATE (recorded as `unknown_outcome`, needs reconciliation before resume).

The ONLY difference between 3 and 4 is outcome CERTAINTY, not cleanliness: 3 knows where it stopped; 4 may not, so it records unknown_outcome. Both run the identical cleanup routine.

Trigger UX: escalating signals + an out-of-band command. First SIGINT (Ctrl-C) = level 1; repeated Ctrl-C escalates 1 -> 3 -> 4 ("press again to stop harder"); SIGTERM = level 3. Plus `aw oc run stop <run-id> --after-call|--after-set|--now|--now-force` so a second terminal can request any level remotely/scriptably. (Flag naming conveys HOW FORCEFULLY the turn is interrupted - never whether cleanup happens; cleanup is unconditional.)

Mechanism: the driver POLLS a stop-request flag/signal at cooperative checkpoints (between agent turns for levels 1-2; within a turn at the next safe point for level 3); level 4 is interrupt + the reconciliation routine. NOT a raw kill.

Relations: this is the DELIBERATE counterpart to CRASH recovery - it reuses the same reconciliation routine as the active-work-lifecycle recovery design (research ud28vy: staleness/takeover, executing-reconcile-before-resume/rollback) and the run-ledger `unknown_outcome` model. Cleaner per-run worktree isolation (the missing-isolation gap seen this session) makes levels 3/4 cleanup far simpler. Related driver items: ctt412 (driver must commit through aw commit/aw finish, blocks 2.0.0), and the orchestrator-queued-before-child + uninformative-blocked-output driver defects observed this session. Feeds a future runner-lifecycle spec (stop protocol + ledger interaction + active-work recovery); decide spec-vs-IPD when picked up.

Priority high, NOT release-blocking (2.0.0 may ship with kill-only stop; this lands shortly after). Origin: user - the killed runners 'just said Terminated'; the four levels are the user's design.
