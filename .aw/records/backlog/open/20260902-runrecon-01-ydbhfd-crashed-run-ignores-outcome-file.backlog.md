- Id: ydbhfd
- Status: open
- Set: runrecon
- Priority: high
- Work-Kind: bug
- Summary: aw runs reports abandoned? for a crashed driver step whose outcome file on disk already records the real disposition: run_viewer flips running -> abandoned? on a dead lock holder without ever reading outcomes/*.json

## Workflow history
- 2026-09-02 created (aw backlog): aw runs reports abandoned? for a crashed driver step whose outcome file on disk already records the real disposition: run_viewer flips running -> abandoned? on a dead lock holder without ever reading outcomes/*.json

OBSERVED 2026-09-02 by the maintainer, after `aw oc run e32j35 97df1z` was killed by a server + network
reboot mid-run. `aw runs -l` reported:

    2 steps: 1 abandoned?, 1 partial
    | abandoned? | 20260829-fullauto-01-97df1z | execute | 1 | $19.39 | 26.65M | - | YES |

THE LABEL IS WRONG, AND THE CORRECT ANSWER WAS ALREADY ON DISK. The step wrote its outcome file
BEFORE the process died: `.aw/records/runs/run-20260902T013603Z-1758564/outcomes/02-97df1z.json`
records

    "disposition": "substantially-complete"
    "summary": "Implemented all 7 E-items of IPD 97df1z and verified all 7 V-items with pasted
                evidence; aw ipd lint --phase pre-transition reports conforming."
    "commits": ["209227d54f1fd7e34115ee9a198c74513a99567d"]
    "pushed": false

and the work is real and intact: `aw/lane/97df1z` holds exactly ONE commit (`209227d5`) with a clean
worktree, touching 7 files including a NET-NEW module `agent_workflows/plan_readiness.py` (219 lines)
plus `tests/test_agy_runipd_cli.py`. So the run is reported as abandoned while its own recorded
disposition says otherwise and its output is committed on a lane.

THE CAUSE, located exactly. `agent_workflows/run_viewer.py:766-770`:

    status = item.get("status", "queued")
    persisted_status = None
    if status == "running" and holder == HOLDER_NONE:
        persisted_status = status
        status = ABANDONED

The ONLY inputs are (a) the per-item `status` in `state.json` and (b) whether the driver lock is still
held. It never reads `outcomes/<NN>-<id6>.json`. Because the driver was killed between writing
`ipd-started` and running its finalize step, `state.json` still carries `status: running` for `97df1z`
(verified: queue entry reads `97df1z | status: running | disposition: None`), and the lock holder is
gone (`driver.lock` names `pid=1758564`, and `kill -0 1758564` reports DEAD). So the viewer takes the
dead-holder branch and guesses.

`abandoned?` with a question mark is honest about being a GUESS, and the guess is reasonable ABSENT
other evidence. The defect is that better evidence exists and is not consulted.

CORROBORATING EVIDENCE THAT THE CRASH, NOT THE STEP, IS THE PROBLEM. The driver event log
(`events.jsonl`) ends at:

    2026-09-02T02:18:09  ipd-finished       e32j35
    2026-09-02T02:18:09  ipd-started        97df1z
    2026-09-02T02:18:10  worktree-allocated 97df1z   (created, branch aw/lane/97df1z)

There is NO terminal event for `97df1z`. The reboot landed inside the turn.

SECOND, DEPENDENT SYMPTOM IN THE SAME OUTPUT (same root cause, do not file separately): the
"Artifact & Status Discrepancies" table reports both plans as Expected `partial`/`abandoned?` but Actual
`approved`. That is CORRECT reporting of a real divergence: plan status advancement happens in the
driver's finalize step, which never ran, so `e32j35` and `97df1z` both still read `- Status: approved`
in `pending/`. Fixing the reconciliation below is what makes this table stop looking like a defect.

WHAT TO FIX, not prescribed in detail. When a run`s lock holder is gone, RECONCILE from the evidence
already written rather than guessing:
1. For each queue item still marked `running` with no live holder, read
   `outcomes/<position>-<id6>.json`. If it parses and carries a `disposition`, report THAT (marked as
   recovered-from-outcome, not as if the driver had reported it cleanly), and surface the recorded
   commits so the lane work is visible.
2. Only when no outcome file exists, or it is unparseable, or it carries no disposition, fall back to
   `abandoned?`. That preserves the honest guess for the case where the step really did die before
   producing anything.
3. Consider whether the reconciliation should be a WRITE (a one-time repair of `state.json`, ideally
   via a verb such as `aw runs reconcile <run-id>`) or a READ-TIME view. A read-time view leaves
   `state.json` permanently claiming `running`, which is itself misleading to any other consumer; a
   write needs to be explicit and attributable, not silent.
4. The stale `driver.lock` (naming a dead PID) should also be cleanable by a supported verb rather than
   by hand.

RELATED GAP, filed separately: `aw run resume` is the verb whose name promises exactly this recovery,
but it cannot reconcile a driver run at all - it reads `ledger.jsonl` while the drivers write
`events.jsonl`, and its own `--help` says so. See the sibling item in Set `runrecon`.

WHY HIGH: the maintainer relies on `aw runs` to decide what to do next. A step that completed
substantially all its work, committed it to a lane, and recorded conforming lint is displayed as
abandoned, which invites either discarding good work or re-running an expensive turn ($19.39 and 26.65M
tokens for this one). Both are worse than the crash itself.
