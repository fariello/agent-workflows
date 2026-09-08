- Id: sv8z1e
- Status: graduated
- Blocks-Release: next
- Set: runrecon
- Priority: medium
- Work-Kind: bug
- Summary: aw run resume cannot recover a crashed driver run: it resolves a run id only to ledger.jsonl while both drivers write events.jsonl, so the one verb named for interrupted-run recovery is unusable on the runs that actually crash

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan d91i3e (Set runrecon, .aw/records/plans/pending/20260908-runrecon-01-d91i3e-...ipd.md), which carries From-Backlog: sv8z1e and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done: no code is written yet. PARTIALLY OBSOLETE: ONE OF THIS ITEM'S TWO CONCRETE DEFECTS IS ALREADY FIXED AND IS NOT GRADUATED. This item's closing paragraph reports a DISCOVERABILITY DEFECT, that aw runs repair is matched as a magic first positional so aw runs --help never mentions it and aw runs repair --help prints the generic runs help, and calls it 'arguably the cheapest real fix in this whole Set'. IT LANDED IN 1273806c ('fix(runs): document aw runs repair and make its --help reach the right page') on 2026-09-02, the SAME DAY this item was written. Verified at HEAD 44d4950d: aw runs repair --help prints the dedicated REPAIR_HELP page and exits 0, and aw runs --help mentions repair three times including 'Read-only, except the opt-in repair verb'. The mechanism is a deliberate in-handler help branch (run_viewer.py:2413-2419) with the tradeoff recorded at :2307-2312. That half is DEAD; the plan does not re-implement it. WHAT SURVIVES AND IS GRADUATED, reproduced exactly against a real driver run: aw runs resume run-20260908T030601Z-1811892 prints 'error: ledger file not found for target ...', exits 2 unpiped, and mentions repair ZERO times, while that run directory holds events.jsonl, state.json, outcomes/, manifest.json, prompts/, sessions/ and no ledger.jsonl. The plan follows THIS ITEM'S OWN OPTION 4 (make the error actionable), which the item rates 'materially more attractive' than building a second resume engine now that aw runs repair ships as the de facto reconcile action. Options 1 and 2 (a second resume engine, or making the drivers emit a real ledger.jsonl) are recorded as deliberately rejected, and the e6b9kt fix is explicitly preserved: resolve_ledger_path must keep returning None for a driver run id (run_cli.py:236-239) and no ledger parser may ever see events.jsonl. ONE MEASUREMENT THAT WIDENS THE ITEM: this item frames the gap as a resume problem, but the SAME unhelpful refusal is emitted by FIVE leaves. runs show, runs status, runs verify-ledger, runs evidence and runs next all print the identical line and exit 2 on the same driver run id, and the string is duplicated four times in run_cli.py (:284, :390, :513, :629), so fixing only resume would leave four copies of the dead end; the plan consolidates them (E-01). Excluded as a DIFFERENT defect: runs decisions and runs questions fail on a missing projection path under .aw/workflow-artifacts/exec-set/, not on the ledger refusal. Also corrected: aw run resume does not exist as this item's prose implies (aw run offers start/record/cancel/finalize/as/ipd and rejects resume with an invalid-choice error); the verb is aw runs resume. POINT 3 (stale driver.lock) IS NOT GRADUATED: it belongs to repair, not to a refusal message, since repair_run already refuses while a live driver holds the run (run_viewer.py:2364, :2374-2379); if a stale lock still wedges repair, that needs its own item with a measured reproduction. ONE FIND THAT SHRINKS THE WORK: the test home and fixture already exist, tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict (:1041) is the e6b9kt regression suite and already builds a fixture driver run and pins the resolver's None (:1071-1076), the real-ledger resolution (:1078-1083) and the explicit-path hatch (:1085-1089). Note there is NO tests/test_run_cli.py. SIBLING ydbhfd (wrong FACTS) remains open and independent; it is not mine to touch and is unaffected.
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
