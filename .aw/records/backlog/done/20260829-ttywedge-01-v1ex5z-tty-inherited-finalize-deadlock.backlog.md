- Id: v1ex5z
- Status: done
- Blocks-Release: next
- Set: ttywedge
- Priority: high
- Work-Kind: bug
- Summary: driver-spawned aw subprocesses inherit the operator TTY, so ipd finalize sees isatty() and blocks on input() forever

## Workflow history
- 2026-09-01 done (aw set): Design shipped: plan g40w37 is executed (From-Backlog: v1ex5z). Verified on main: oc_runipd denies the child a terminal (4 stdin=subprocess.DEVNULL sites), closing the tty-inherited finalize deadlock.
- 2026-08-29 graduated (aw set): Graduated to plan g40w37.
- 2026-08-29 created (aw backlog): driver-spawned aw subprocesses inherit the operator TTY, so ipd finalize sees isatty() and blocks on input() forever (observed: finalize 8zgybk wedged 1h49m)

Observed 2026-08-29. `aw runs -L -i` reported `20260828-wtiso-01-8zgybk: location: in pending/
(expected executed/), status: file 'approved' != run 'complete'`. The run believed the item was
complete but the plan never moved. Cause: its self-finalize was WEDGED, not lost.

```
$ ps -p 3420249 -o pid,stat,wchan,etime
    PID STAT WCHAN         ELAPSED
3420249 S+   wait_woken   01:49:26      <- blocked on a read, no child process
$ ls -l /proc/3420249/fd/0
/proc/3420249/fd/0 -> /dev/pts/6        <- stdin is the OPERATOR'S TTY
```

MECHANISM. `ipd_lifecycle.run_finalize` decides interactivity as:

```python
interactive = (not (ctx.is_agent or ctx.is_json)
               and hasattr(_sys.stdin, "isatty") and _sys.stdin.isatty())
prompt = _tty_scope_prompt if interactive else None
```

(`ipd_lifecycle.py:1942-1948`, prompting at `:1864` / `:1876`.) The driver spawns finalize with
`subprocess.run(cmd, text=True, stdout=PIPE, stderr=PIPE)` (`oc_runipd.py:433-435`) which pipes stdout
and stderr but leaves **stdin INHERITED**. The child therefore sees the operator's terminal, concludes
it is interactive, and calls `input()` for a scope answer that no human will ever type, because the
output it would prompt on is captured in a pipe. Verified the wedged process carried neither `--agent`
nor `--json`, so `interactive` evaluated True.

This is the same FAMILY as backlog `qyaime` (a permission prompt deadlocking a non-interactive
`--auto` turn) but a DIFFERENT cause: qyaime is the host agent's permission prompt, this is a nested
`aw` command's own TTY prompt. Fixing one does not fix the other.

WHY IT IS WORSE THAN A HANG. The driver blocks forever holding its run lock, the item stays `running`
in the ledger, and the plan is left `approved` in `pending/` while the run reports `complete`, i.e. the
exact artifact/status discrepancy `aw runs -L -i` now surfaces. Anything downstream that waits on that
Set (here: all of wtiso-02..07) stays queued indefinitely.

FIX (two layers, both needed; defence in depth):
1. CALLER: every driver-spawned nested `aw` invocation must pass `stdin=subprocess.DEVNULL`, so an
   inherited terminal can never make a child believe it is interactive. There are SEVEN such
   invocations (`oc_runipd.py:248,317,356,417`; `agy_runipd.py:421,481,540`), and the same
   `subprocess.run(...)` shape appears 10 times without a `stdin=` argument.
2. CALLEE: `run_finalize` must not treat an inherited TTY as consent when its own output is not a
   terminal. Require `sys.stdout.isatty()` too (a piped stdout means nobody can read the prompt), and
   honour an explicit non-interactive signal (e.g. `AW_NONINTERACTIVE=1` or `CI`) so a nested call is
   fail-closed by default rather than fail-open.

Fixing only the caller leaves the callee fail-open for any other launcher; fixing only the callee
leaves the drivers relying on the callee's heuristic. Do both.

NOT FIXED IN THIS SESSION: the maintainer instructed not to touch anything currently running. PID
3420249 is still wedged and `aw oc run wtiso` (3207626) is live, so the running finalize was left
alone; the CODE fix above is safe to land because it only affects future invocations.
