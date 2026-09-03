- Id: l670yn
- Status: done
- Set: runstale
- Priority: high
- Work-Kind: bug
- Summary: aw runs shows a dead run's item as 'running' forever (no read-time liveness check) and an interrupted driver never writes a terminal status

## Workflow history
- 2026-09-03 done (aw set): Closing done: the graduated design SHIPPED. Plan ssk6nf (From-Backlog: l670yn) is in executed/, carrying Bug A's read-time liveness projection; Bug B was cross-referenced at graduation to spec c4gd2h and plans 2ouj70/71vjbn, which already own it and are themselves executed. Found during the 2026-09-03 all-bugs-block-release audit; closed rather than gated, since gating a shipped fix would record a release blocker for finished work.
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

FORWARD LINKS (added 2026-09-02; prose only, status untouched - this item stays `graduated`).

WHAT LANDED: BUG A's plan `ssk6nf` is EXECUTED. The read-time liveness projection ships, and so does the
opt-in `aw runs repair <run-id>` verb from its E-04. Both were exercised on 2026-09-02 against a real
crashed run (`run-20260902T013603Z-1758564`, killed mid-turn by a server reboot): the board correctly
showed `abandoned?` instead of a false `running`, and `aw runs repair` reconciled it to `interrupted`.

THE BULK SWEEP THIS ITEM ANTICIPATED HAS NOW HAPPENED. `ssk6nf` deferred it with "Reconciling other runs'
stale state in bulk: the repair verb is per-run; a sweep can follow if a real need appears." The need
appeared: 40 run directories were found holding a `driver.lock` naming a DEAD pid, dating back to
2026-08-28. Repairing each individually fixed THREE genuinely stale states, and one of them was not
merely interrupted but had actually finished:
  - `97df1z`  running -> interrupted   (run-20260902T013603Z-1758564)
  - `7p9n2v`  running -> interrupted   (run-20260829T152806Z-3134751, the very run this item reported)
  - `8zgybk`  running -> executed      (run-20260829T190116Z-4092754, misreported for days)
The other 37 had nothing to repair. Zero runs now report `running` or `abandoned?`.

BUG B IS STILL OPEN AND THE SWEEP PROVES IT. `aw runs repair` fixes recorded STATE, not the lock file:
all 40 `driver.lock` files with dead PIDs are still on disk afterwards. That is exactly the write-side
defect described above (no SIGINT/SIGTERM handler, `run_lock` never unlinks), still owned by spec
`c4gd2h` and plans `2ouj70`/`71vjbn`. The accumulation rate is now measurable: 40 stale locks over five
days of driver use.

TWO NEW SIBLING ITEMS, filed 2026-09-02 in Set `runrecon`, both covering gaps this item did NOT claim:
  - `ydbhfd` (high): the viewer never reads `outcomes/<NN>-<id6>.json`, so a step whose outcome file
    records `substantially-complete` with a lane commit is still shown as an unknown-outcome guess. BUG A
    made the read path honest about not knowing; it did not make it consult the answer already on disk.
  - `sv8z1e` (medium): `aw run resume` cannot be pointed at a driver run at all, because it resolves a
    run id only to `ledger.jsonl` while the drivers write `events.jsonl`. The verb named for
    interrupted-run recovery is unusable on the runs that actually crash.

DISCOVERABILITY DEFECT worth recording here since this item is where a reader will look: `aw runs repair`
is matched as a magic first POSITIONAL argument (`run_viewer.py:2272`), not a real subparser, so
`aw runs --help` does not list it and `aw runs repair --help` prints the generic `runs` help. The verb
that resolves this whole family of symptoms is findable only by reading executed plan `ssk6nf`.
