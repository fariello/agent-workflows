- Id: i2fjf8
- Status: open
- Set: runghostid
- Priority: medium
- Work-Kind: bug
- Summary: aw oc run on a no-op selector (e.g. a to-review orchestrator with no runnable children) prints a resume hint for a run-id it never persisted (no run dir written), so the run appears to have started and be resumable when it did not exist

## Workflow history
- 2026-08-28 created (aw backlog): aw oc run on a no-op selector (e.g. a to-review orchestrator with no runnable children) prints a resume hint for a run-id it never persisted (no run dir written), so the run appears to have started and be resumable when it did not exist

Observed 2026-08-28: `aw oc run 20260827-driverfin-00-yt93ir` (naming only the Order-00 orchestrator, whose children are `reviewed` not `approved` and were not in the queue) printed:
```
Run ID: run-20260828T162652Z-4172854
State directory: .../records/runs/run-20260828T162652Z-4172854
--- OpenCode Session Continuity ---
No OpenCode session was captured for this run.
To resume this run:
  runipd resume ... run-20260828T162652Z-4172854
```
But `.aw/records/runs/run-20260828T162652Z-4172854/` does NOT exist on disk - the run built no queue / persisted no state, yet the continuity banner announced a Run ID + State directory + a `resume` command for it. `aw run resume run-20260828T162652Z-4172854` would then fail (no ledger).

Two coupled defects:
1. The runner emits the Run ID + State-directory + resume-hint banner even when it produced NO durable run (nothing runnable -> no run dir written). The banner should only print for a run that was actually persisted.
2. A no-op run should report clearly WHY nothing ran (e.g. "orchestrator yt93ir deferred: children not executed; no runnable items - did you mean to include the children or pass --full-auto?") instead of a misleading continuity banner.

Note: an EARLIER whole-set run of driverfin (run-20260828T160352Z-668489) worked correctly - it deferred the orchestrator (`orchestrator-deferred`, not-all-children-executed) and reviewed the children - so the queue/dispatch logic is fine; this is specifically the empty/no-op-run reporting path. Origin: filed after /assess documentation, per user instruction to capture it separately from the docs IPD. Related runner items: ctt412 (self-finalize), kjzlgw (graceful-quit), driverfin (self-finalize+isolation).
