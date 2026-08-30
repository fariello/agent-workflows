- Id: xd9sll
- Status: done
- Blocks-Release: next
- Set: lanesess
- Priority: high
- Work-Kind: bug
- Summary: Session reuse across lanes pins a turn to the PREVIOUS lane's worktree: session is per-set but worktrees are per-item, so lanes 2..N run in the wrong tree and stall at the external_directory gate

## Workflow history
- 2026-08-29 done (aw set): Fixed in c0e9599: an isolated lane turn now always gets a fresh session in BOTH drivers (oc_runipd.run_opencode + agy_runipd.execute_item, which also clears use_continue), and the post-turn writeback only promotes a session to the set/run keys for a non-isolated turn. 6 new tests in tests/test_lane_session_isolation.py, each proven to FAIL without the fix (reverting the launch guard reproduces '--session ses_LANE1' alongside '--dir <lane>'; reverting the agy half fails the symmetry test). Verified live: run-20260829T190308Z-4123955 lane 8zgybk worked through 7 external_directory asks with 86,276 bytes of session output, where the pre-fix run stalled at 600s with 0 bytes.
- 2026-08-29 open (aw set): status set to open
- 2026-08-29 created (aw backlog): Filed from live evidence in run-20260829T153858Z-3207626 (qcqhj7): --dir was correct but the reused session dragged 8zgybk's directory back in; trigger for qyaime's deadlock, distinct from dh0uno

ROOT CAUSE (in-tree, verified): the driver reuses ONE opencode session per SET, but allocates worktrees per ITEM. `oc_runipd.run_opencode` (oc_runipd.py:1725-1731) selects the session as `state["session_id"] or state["set_sessions"][item["setid"]] or options["session"]`, and after each turn both keys are rewritten from the observed session (oc_runipd.py:2070-2078). So lane 1 of a set mints the session, and lanes 2..N are launched with `--session <lane-1's session>`. opencode's session carries its own project/`directory` binding, which then OVERRIDES the correct `--dir`, and the turn executes with cwd pinned to the PREVIOUS lane's worktree.

OBSERVED (opencode.log, run-20260829T153858Z-3207626, qcqhj7 attempt 1):
  730690  18:06:45.410  run=e983f9f1  "creating instance" directory=.aw/worktrees/qcqhj7   <- correct lane, per --dir
  730703  18:06:46.211  run=e983f9f1  "creating instance" directory=.aw/worktrees/8zgybk   <- PREVIOUS lane pulled in
  730711  18:06:46.530  run=e983f9f1  bootstrapping        directory=.aw/worktrees/8zgybk
  730726  18:06:47.531  run=e983f9f1  tracking  cwd=.aw/worktrees/8zgybk
  730736  18:06:47.456  run=e983f9f1  loop      session.id=ses_<redacted-A>                <- 8zgybk's session
  730758  18:07:24.156  run=e983f9f1  evaluated permission=external_directory pattern=<repo-root>/* action.action=ask
  730759  18:07:24.157  run=e983f9f1  asking id=per_<redacted> permission=external_directory   <- never answered
  730762  18:07:25.253  run=e983f9f1  asking id=per_<redacted>                                  <- never answered
  events.jsonl 18:16:44        ipd-stalled  id6=qcqhj7 stall_timeout=600.0

Corroborating state: `.aw/records/runs/run-20260829T053827Z-2084502/state.json` shows ONE session id shared by all 8 wtiso items AND the tabcomp item (`set_sessions` = {tabcomp: ses_<redacted-B>, wtiso: ses_<redacted-B>}, one and the same id), i.e. the reuse is not even set-scoped in practice. The session-log files for the stalled lanes are ZERO BYTES (`sessions/03-qcqhj7-attempt-1.jsonl`, `04-rchpms-attempt-1.jsonl`), which is the reliable wedge signal.

WHY IT MATTERS (blast radius): running in the wrong lane makes every main-repo path external, so qyaime's `external_directory` gate fires with no answerer and the lane dies at the 600s StallWatchdog. Because lane 1's session is inherited by ALL later lanes of the set, ONE interrupted lane-1 finalize can doom every subsequent lane turn in the run. In run-20260829T141137Z-3037978, four consecutive lanes (qcqhj7, rchpms, 7p9n2v, 58ha43) all recorded `interrupted`.

RELATION: distinct from dh0uno (which is inner-`aw` resolving `.aw/state`/`.aw/records/runs` relative to the lane) and from qyaime (the permission deadlock itself). This item is the TRIGGER that puts a turn in the wrong tree in the first place: a session/worktree GRANULARITY mismatch (session per set vs worktree per item). Fixing qyaime's prompt paths would stop the hang; fixing this stops the wrong-lane execution that also silently corrupts which tree the work lands in.

FIX SKETCH: session identity must be keyed at the same granularity as the worktree. For an isolated (`isolate_worktree`) execute turn, do NOT reuse a session across items: either start a fresh session per lane (as the verifier turn already does via `fresh_session=True`), or key `set_sessions` by `(setid, id6)`/by worktree path so a session is never carried into a different tree. Add a guard that refuses/warns when a turn's observed `directory` != the `--dir` it was launched with, so a future carryover fails loudly instead of stalling for 600s.

REPRO: `aw oc run <set>` with `isolate_worktree` on and 2+ execute items in one set; lane 2 boots with lane 1's session and cwd, then stalls at the first main-repo path access.

TEST: (a) a set with two isolated execute lanes launches lane 2 with NO inherited session, and its observed `directory`/cwd equals its own worktree; (b) a launched turn whose observed session `directory` differs from `--dir` is detected and recorded as a failure rather than left to the stall watchdog; (c) `set_sessions` never maps two different worktrees to one session id.
