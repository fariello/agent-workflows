- Id: l670yn
- Status: graduated
- Set: runstale
- Priority: high
- Work-Kind: bug
- Summary: aw runs shows a dead run's item as 'running' forever (no read-time liveness check) and an interrupted driver never writes a terminal status

## Workflow history
- 2026-08-29 graduated (aw set): Bug A graduated to plan ssk6nf (review-ready). Bug B cross-referenced to spec c4gd2h and plans 2ouj70/71vjbn, which already own it.
- 2026-08-29 created (aw backlog): aw runs reports a dead run's item as 'running' forever: reconcile_interrupted is called only from run_queue (resume), so no read path checks driver liveness; and an interrupted driver never writes a terminal status because it installs no SIGINT/SIGTERM handler and leaves driver.lock holding a dead PID

Observed 2026-08-29 by the maintainer on run `run-20260829T152806Z-3134751` after interrupting
`aw oc run`: the board still showed `1 running` for `wtiso-04 7p9n2v` although the driver was gone.

```
run-20260829T152806Z-3134751  [wtiso]  (8 steps: 3 blocked, 1 dependency-blocked, 3 queued, 1 running)
-    running  plan  20260828-wtiso-04-7p9n2v  [attempts: 1]
```

Verified ground truth at the same moment:

```
driver.lock -> pid=3134751 started=2026-08-29T15:28:10+00:00
ps -p 3134751 -> PID 3134751 is DEAD
flock(LOCK_EX|LOCK_NB) on driver.lock -> ACQUIRED (no live driver holds this run)
```

TWO DISTINCT DEFECTS, deliberately separated because they fail independently:

BUG A (read side; NOT covered by any existing plan). `reconcile_interrupted` (oc_runipd.py:2402)
already does the right thing (it resolves the plan, promotes a genuinely-executed item, else marks
`interrupted`), but it is called from EXACTLY ONE place: inside `run_queue` (oc_runipd.py:2474), i.e.
only on a RESUME. Every read path therefore trusts the persisted value: `run_viewer.load_run_summary`
does `item.get("status", "queued")` (run_viewer.py:225) with no liveness check. So a run interrupted by
SIGKILL, a crash, a laptop suspend, or an OOM kill shows `running` forever, and no stop protocol can
prevent that. Constraint for the fix: a READ command must not mutate state, whereas
`reconcile_interrupted` calls `save_state`, so the liveness projection has to be read-only (or an
explicit opt-in write via a repair verb).

BUG B (write side; OVERLAPS approved spec c4gd2h and plans runstop-01/runstop-06). The driver installs
NO signal handler of its own: the only `signal` references in oc_runipd.py are the grace constants
(:1627-1628) and the escalation INSIDE `terminate_process` (:1654-1666), which signals the CHILD. So
SIGINT raises KeyboardInterrupt, the process dies, and `item["status"] = "running"` (:1884) is the last
thing ever persisted; `run_lock` (:738-756) also never unlinks the lock file, which is why a dead PID
remains readable. Spec c4gd2h R1-R3 + R12-R13 and plans `2ouj70`/`71vjbn` already specify the fix
(reap, release lock, coherent ledger, SIGINT->level 1, SIGTERM->level 3). Do NOT re-specify it here:
whichever plan lands first owns it and the other must reference it (GUIDING_PRINCIPLES P8).

Also worth fixing as part of this: the ALREADY-STALE run dir on disk needs a repair path, since fixing
the code does not retroactively correct `run-20260829T152806Z-3134751`.
