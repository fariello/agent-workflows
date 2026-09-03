- Id: sv8z1e
- Status: open
- Blocks-Release: next
- Set: runrecon
- Priority: medium
- Work-Kind: bug
- Summary: aw run resume cannot recover a crashed driver run: it resolves a run id only to ledger.jsonl while both drivers write events.jsonl, so the one verb named for interrupted-run recovery is unusable on the runs that actually crash

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

OBSERVED 2026-09-02, while trying to recover `run-20260902T013603Z-1758564` after a server reboot killed
the driver mid-turn (see sibling item in Set `runrecon` for the crash and its evidence).

WHAT THE VERB PROMISES. `aw run resume --help`:

    Reconstruct run state purely from the ledger and report resumable steps.
    Refuses (exit 3) when a side effect was interrupted mid-flight (unknown_outcome)
    pending explicit reconciliation.

That is an exact description of the situation a crashed driver leaves behind, so it is the first verb an
operator (or an agent helping one) reaches for.

WHY IT CANNOT HELP. It reads a DIFFERENT FILE than the drivers write. Measured in the affected run
directory `.aw/records/runs/run-20260902T013603Z-1758564/`:

    decisions-and-questions.md  driver.lock  events.jsonl  execution-report.md
    manifest.json  outcomes/  prompts/  sessions/  state.json

There is NO `ledger.jsonl`. The resolver is deliberate about this, and says so in its own docstring
(`agent_workflows/run_cli.py:216-225`):

    A run ledger owns exactly ONE filename, `store.LEDGER_FILENAME` (`ledger.jsonl`). It must NEVER
    resolve a bare run id to `<...>/runs/<target>/events.jsonl`: that file exists for every real
    driver run but is the RUNNERs own event log in a different format, so claiming it made
    `aw run show <any-real-run>` parse healthy data as a ledger and report it corrupt (`e6b9kt`).

The `--help` text repeats the warning:

    NOTE: a run id resolves only to a ledger.jsonl; the drivers own events.jsonl is a different
    format.

SO THE CURRENT BEHAVIOR IS CORRECT-BY-DESIGN AND STILL LEAVES A HOLE. The narrow fix for `e6b9kt` (stop
mis-parsing `events.jsonl` AS a ledger) was right, and this item must NOT be resolved by undoing it.
The hole is that nothing else fills the gap: there is one verb named `resume`, it serves the ledger-based
run model, and the DRIVER run model (`aw oc run` / `aw agy run`, which is what the maintainer actually
runs and what actually crashes) has no resume/reconcile verb at all. The result is that a real
interrupted driver run is recoverable only by hand-reading `events.jsonl`, `state.json`, and
`outcomes/*.json`, which is what had to be done here.

CONCRETE EVIDENCE OF THE MANUAL WORK THIS FORCES. To answer "what survived the reboot?" required, by
hand: reading the tail of `events.jsonl` to find the last event was `worktree-allocated` for `97df1z`
with no terminal event; parsing `state.json` to see the queue entry still marked `running`; reading
`outcomes/02-97df1z.json` to discover the step had actually recorded `substantially-complete` with
commit `209227d5`; checking `kill -0` on the PID in `driver.lock` to confirm the holder was dead; and
`git log main..aw/lane/97df1z` plus `git -C .aw/worktrees/97df1z status --porcelain` to confirm the lane
held one clean commit. None of that is available through a verb.

WHAT TO SOLVE FOR, not prescribed:
1. Does the driver run model get its OWN verb (e.g. `aw runs resume <run-id>` / `aw runs reconcile
   <run-id>`, under the `runs` reader namespace that already understands `state.json` and `events.jsonl`),
   or do the drivers additionally emit a real `ledger.jsonl` so the existing `aw run resume` works on
   them? The second unifies the models but is a much larger change and risks re-creating the exact
   confusion `e6b9kt` fixed.
2. Whichever is chosen, the refusal semantics the existing verb already defines are the right shape and
   should be reused: report resumable steps, and REFUSE (rather than guess) when a side effect was
   interrupted mid-flight pending explicit reconciliation. A crashed driver mid-turn is precisely an
   interrupted side effect.
3. It must also handle the stale `driver.lock` (a lock naming a dead PID) explicitly, since a resume
   attempt will otherwise either trip over it or need the operator to delete it by hand.
4. Honest scope note: the two models may be deliberately separate, in which case the fix could be as
   small as making the ERROR actionable. If `aw run resume <driver-run-id>` said "this is a driver run;
   use `aw runs reconcile <id>`" instead of failing on a missing ledger, the hole would at least be
   navigable. Decide whether that is sufficient before building a second resume engine.

RELATION TO THE SIBLING ITEM: the sibling covers the DISPLAY defect (`aw runs` reporting `abandoned?`
while the outcome file records the true disposition). Fixing that gives an operator the right FACTS;
fixing this item gives them a supported ACTION. They are independent and can land in either order,
though doing the sibling first is the cheaper win.

CROSS-LINKS (added 2026-09-02, verified against the tree rather than assumed).

PRIOR ART, and this item is NOT a duplicate: `l670yn` (runstale, high, graduated) covers a dead run's
item being REPORTED as `running` forever. Its read-side half graduated to plan `ssk6nf`, now EXECUTED,
which added the read-time liveness projection and the opt-in `aw runs repair <run-id>` verb. Its
write-side half (no signal handler, `run_lock` never unlinks the lock) stays open under spec `c4gd2h`
and plans `2ouj70`/`71vjbn`.

WHY THIS ITEM SURVIVES ALL OF THAT: every one of those addresses the DRIVER run model's state. None
addresses the fact that the verb literally named `resume` belongs to a DIFFERENT run model and cannot be
pointed at a driver run at all. Confirmed after the repair sweep: `aw runs repair` fixes the recorded
STATE, and the affected run directory still has no `ledger.jsonl`, so `aw run resume <driver-run-id>`
remains unusable. The two models are still disjoint.

RELATIONSHIP TO THE SHIPPED REPAIR VERB, which narrows this item usefully: `aw runs repair` is now the
de facto reconcile action for a driver run, so the gap is no longer "there is no action" but "the action
is undiscoverable and is not the verb whose name promises it". That makes option 4 in this item (make the
error actionable) materially more attractive than building a second resume engine: `aw run resume
<driver-run-id>` should say "this is a driver run; use `aw runs repair <id>`" instead of failing on a
missing ledger.

DISCOVERABILITY DEFECT, measured while confirming the above: `aw runs repair` is not a subparser. It is
matched as a magic first positional (`run_viewer.py:2272`), so `aw runs --help` never mentions it and
`aw runs repair --help` prints the generic `runs` help. An operator or agent cannot find the one action
that fixes this without reading executed plan `ssk6nf`. That is arguably the cheapest real fix in this
whole Set.

SIBLING: `ydbhfd` (same Set) covers the wrong FACTS - the viewer ignoring `outcomes/*.json` and so
reporting a guess when the true disposition is on disk. This item covers the missing ACTION. Independent;
`ydbhfd` is the cheaper win.
