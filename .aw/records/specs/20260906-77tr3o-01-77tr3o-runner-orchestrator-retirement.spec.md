# Spec: Runner-owned orchestrator retirement

- Date: 2026-09-06
- Status: approved
- Id: 77tr3o
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: kxkc04
- Scope: How `aw oc|agy run` retires a Set's Order-0 orchestrator once the Set's LAST outstanding child
  is executed. Covers the two deferral defects (`kxkc04`), the never-fired rollup, the E/V honesty-gate
  contradiction, the queue-vs-disk scope question, and the agy runner's missing `orchestrate` action. It
  does NOT change the agent-driven path (a human or agent running a Set by hand still executes the
  orchestrator's own `E-*`/`V-*` items), does NOT relax the receipt or scope gates for CHILD plans, and
  does NOT address the general `dependency-blocked`-is-terminal defect for ordinary items (`nueip1`).

## Workflow history

- 2026-09-06 approved (aw specs, --by-human): Maintainer directed this graduation in-session and supplied the design contract himself: the orchestrator serves the AGENT-DRIVEN path; 'aw oc|agy run' is more rigorous and renders it null-and-void; the runner must retire it as executed as a final step of Set completion so it does not linger; the status/message must make clear it was executed as that final rollup step; and it must fire even when the current run completed only the LAST outstanding child rather than all of them. He confirmed the diagnosis and answered 'Yes please' to graduating kxkc04 into a spec plus review-ready plans.
## 1. Why this exists

An Order-0 orchestrator IPD coordinates a Set: it owns the child table, the sequencing, and the
whole-Set completion criteria. Under the AGENT-DRIVEN path that is real work, and its `E-*`/`V-*` items
are executed like any other plan's.

Under `aw oc run` / `aw agy run` it is not. The runner enforces ordering (`queue_sort_key`,
`dependency_depth`), isolation (one worktree per item), and a merge-and-revalidate gate per child. Those
mechanisms SUPERSEDE the orchestrator's coordination role; the maintainer's phrasing is that `aw run`
"renders the orchestrator null-and-void". What remains is a bookkeeping obligation: once the Set's last
outstanding child is executed, the orchestrator must be retired to `executed` so it does not linger in
`pending/` forever, and its history must say plainly that it was retired as a rollup step of a runner
Set completion rather than executed by an agent.

That obligation is unmet. The code that was supposed to discharge it has never worked.

## 2. Measured current state

All measurements at HEAD `844d195c`, 2026-09-06, on the durable run records in `.aw/records/runs/`.

### 2.1 The rollup has never once succeeded

    $ grep -rh "orchestrator-finalized" .aw/records/runs/*/events.jsonl | wc -l
    0
    $ grep -rh "orchestrator-deferred"  .aw/records/runs/*/events.jsonl | wc -l
    28

28 deferrals across 15 distinct orchestrators (`3b4f8u`, `5e4sb6`, `88h0h8`, `bl9q3d`, `c2tvmm`,
`dh5gnl`, `e6h1p3`, `r4mbcw`, `r7xku3`, `rh5tt6`, `ryvoi5`, `u5vyye`, `y0gg8o`, `yt93ir`, `zpbx7o`).
Zero successes. Every orchestrator that reached `executed` on disk was finalized by a HUMAN or an agent
doing manual whole-Set verification, never by the runner.

`AGENTS.md:42` currently asserts that an orchestrator "self-finalizes once every child of its Set
reached `executed` ... so an Order-0 parent in the queue is correct and needs no human step", and
instructs agents NOT to raise orchestrator finalization as a concern. That claim is false as written and
must be corrected by whatever plan implements this spec.

### 2.2 Two distinct failures share one `else` branch

`oc_runipd.py:6993-7031` dispatches an `orchestrate` item. On any failure it takes a single `else`:

    else:
        runnable["status"] = "dependency-blocked"        # oc_runipd.py:7015
        runnable["unsatisfied_dependencies"] = unfinished

The recorded reasons from run `run-20260905T211011Z-3780617` show the two cases are unrelated:

    5e4sb6 | reason: not-all-children-executed | unfinished: []
    rh5tt6 | reason: finalize-refused          | unfinished: []

- CASE A, `not-all-children-executed` (27 of 28 events). This is what `kxkc04` describes. Because
  `dependency-blocked` is in `TERMINAL_STATES` (`oc_runipd.py:254-272`) and the selection filter admits
  only `queued` items (`oc_runipd.py:4071`, `:6919`), the orchestrator is excluded FOREVER. Its children
  can all reach `executed` later in the SAME run and nothing revisits it. The event is named
  `orchestrator-deferred`, and a deferral is by definition something you return to.
- CASE B, `finalize-refused` (1 of 28, `rh5tt6`). `all_done` was TRUE: all five `wslayout` children are
  `executed` on disk. `finalize_orchestrator` itself refused. `kxkc04` does not cover this case, and a
  fix that only implements `kxkc04`'s prescription ("leave it `queued`") would make CASE B spin forever
  re-attempting a finalize that can never pass.

### 2.3 Case B reproduced: two stacked gates, neither passable by a rollup

`finalize_orchestrator` (`oc_runipd.py:773-796`) shells out to `aw ipd set executed <id6> --actor "aw oc
run (orchestrator rollup)" -m <message>`. Reproduced verbatim:

    $ aw ipd set executed rh5tt6 --actor "aw oc run (orchestrator rollup)" -m "Orchestrator rollup: ..."
    refused: no begin receipt for rh5tt6: run `aw ipd begin` first
      (fail-closed: no receipt = no execution authority)

An orchestrator is never agent-executed, so nothing ever calls `aw ipd begin` for it, so no receipt can
exist. `aw ipd begin rh5tt6` DOES succeed if invoked (verified), which exposes the second gate:

    $ aw ipd begin rh5tt6 --actor test/probe        # receipt written
    $ aw ipd set executed rh5tt6 --actor "aw oc run (orchestrator rollup)" -m probe
    refused: pre-transition gate did NOT conform (error); plan left unmoved.
      IPD-S404 E-01: not 'performed' at pre-transition
      IPD-S404 E-02: not 'performed' at pre-transition
      IPD-S404 V-01: not 'pass' at pre-transition
      IPD-S404 V-01: empty Observed evidence at pre-transition
      IPD-S404 V-02: not 'pass' at pre-transition
      IPD-S404 V-02: empty Observed evidence at pre-transition

(The probe receipt was deleted immediately; `.aw/state/ipd-lifecycle/` carries no `rh5tt6` receipt.)

`check_checkpoint` (`ipd_lint.py:694-725`) applies the `pre-transition` E/V requirements
UNCONDITIONALLY; `grep -c orchestrator agent_workflows/ipd_lint.py` is 0, so the linter has no
orchestrator concept at all. This is the CONTRADICTION at the heart of the defect: the honesty gate
demands evidence for `E-*`/`V-*` items that, under `aw run`, are by design not performed by anyone.

### 2.4 The queue-vs-disk scope defect

`_set_children_all_executed` (`oc_runipd.py:751-770`) inspects `state["queue"]` ONLY. Two consequences:

- The maintainer's requirement is unimplementable as written. If a run completes the Set's LAST
  outstanding child while earlier children were executed in PREVIOUS runs, the queue holds one child;
  the on-disk Set holds several. A queue-scoped check cannot answer "is the SET now complete".
  `wslayout` passed its `all_done` test only incidentally: child `wpu5zu` was executed in an earlier run
  and absent from this queue, and the four present children were all `executed`.
- The "no children in queue" branch returns `(False, [])` under its documented safe default, which
  produced `5e4sb6`'s event with `unfinished_children: []` and a run summary reading
  "dependency-blocked (unmet dependencies)" while naming no dependency. The DEFAULT is correct; the
  MESSAGE is the defect.

An on-disk resolver already exists and answers the right question. `selectors.resolve(repo, 'plans',
<setid>)` returns every member of a Set across `pending/` and `executed/`, and `ipd_lint.parse` yields
each member's `Id`/`Order`/`Kind`/`Status`. Measured:

    wslayout : 5 children all executed, orchestrator rh5tt6 approved   -> SET COMPLETE
    rununify : 2 children all executed, orchestrator 5e4sb6 approved   -> SET COMPLETE ON DISK, BUT SEE 2.5
    lanectn  : 4 children executed, nna8yz + xdr83v approved           -> SET INCOMPLETE

### 2.5 A completeness check over EXISTING members is not sufficient

`rununify` shows why. On disk both its children (`2r306y`, `818uru`) are `executed`, so a naive
"every member of the Set is executed" test would retire `5e4sb6`. That would be WRONG: the
orchestrator's own child table declares a row `03+` ("one child per cohesive group of class (c)
diverged symbols") that was NEVER AUTHORED. The Set is genuinely mid-flight; its remaining children do
not exist as files yet.

So Set completeness cannot be inferred from the executed-ness of the members that happen to exist. A
retirement rule needs either an explicit declaration that the child set is fully authored, or a
conservative refusal when the orchestrator's child table names rows with no corresponding plan.

### 2.6 The agy runner has no orchestrate action at all

Measured:

    python3 -c "from agent_workflows import agy_runipd as a, oc_runipd as o; ..."
    action_for                 agy=False oc=True   same_object=False
    finalize_orchestrator      agy=False oc=True   same_object=False
    _set_children_all_executed agy=False oc=True   same_object=False

    agy.determine_action('approved')            -> 'execute'
    oc.action_for('orchestrator', 'approved')   -> 'orchestrate'

`agy_runipd.py:1783` calls its own `determine_action` (`:1510-1514`), which has no orchestrator concept.
So `aw agy run` would AGENT-EXECUTE an approved orchestrator rather than roll it up: a worse failure
than oc's, because an agent turn would be spent authoring against a plan whose whole purpose the runner
has superseded. Note `agy_runipd.py:1313` already carries a comment about `action_for` reading `kind`,
so the asymmetry is known in passing but unfixed.

## 3. Requirements

- R-1 SET COMPLETENESS IS EVALUATED ON DISK, NOT FROM THE QUEUE. The retirement decision MUST consult
  every member of the Set as it exists in the plans tree, so a run that completes only the Set's LAST
  outstanding child still retires the orchestrator. The queue remains the source of what to DISPATCH; it
  is not the source of Set membership.
- R-2 RETIREMENT IS GATED ON EVERY CHILD BEING `executed`. No other state qualifies. In particular
  `substantially-complete` does NOT (it means finalize refused, see `i452hf`), nor do `blocked`,
  `dependency-blocked`, `integration-blocked`, `merge-conflict`, `reviewed`, or `approved`.
- R-3 A SET WHOSE CHILD SET IS NOT FULLY AUTHORED MUST NOT BE RETIRED. Per 2.5. The refusal MUST name
  the reason so it is distinguishable from an unfinished-children refusal.
- R-4 THE TRANSITION MUST BE HONEST ABOUT WHAT IT IS. The terminal history entry MUST record that the
  orchestrator was RETIRED as a rollup step of a runner Set completion, name the run id, and name the
  children whose execution justified it. It MUST NOT claim the orchestrator's own `E-*`/`V-*` items were
  performed, because under `aw run` they were not.
- R-5 THE E/V PRE-TRANSITION REQUIREMENT MUST BE RESOLVED EXPLICITLY, NOT BYPASSED. Exactly one of:
  (a) the linter learns a `Kind: orchestrator` + runner-rollup exemption, applied ONLY to this
  transition; or (b) a distinct runner-owned rollup transition exists that does not route through the
  E/V checkpoint but keeps every other gate. Whichever is chosen, a CHILD plan's E/V requirement is
  unchanged, and no path may be added by which an ordinary plan reaches `executed` without evidence.
- R-6 THE RECEIPT REQUIREMENT MUST BE RESOLVED EXPLICITLY. An orchestrator has no `begin` receipt by
  construction. Either the rollup transition does not require one, or the runner mints one as part of
  the rollup. Silently reusing the child-plan receipt path is not acceptable: it is what fails today.
- R-7 A DEFERRAL THAT MAY LATER CLEAR MUST NOT BE WRITTEN AS TERMINAL. Per `kxkc04`. An orchestrator
  whose children are merely unfinished stays reconsiderable within the run, exactly as an item skipped
  by the inner selection pass already is (`oc_runipd.py:5829-5833`, no status written).
- R-8 A GENUINELY DEAD SET MUST STILL TERMINATE. If a child reached a non-success terminal state it can
  never become `executed`, so that orchestrator IS finished and must say so. Leaving it reconsiderable
  must not let the loop spin. The drain path (`oc_runipd.py:5847`) already terminates an unsatisfiable
  run; that must be VERIFIED for this case, not assumed.
- R-9 THE TWO REFUSAL REASONS MUST BE DISTINGUISHABLE IN THE RECORD. "children exist and are
  unfinished: <ids>", "no children of Set <setid> are in this run's queue", "child table declares
  unauthored rows", and "finalize refused: <reason>" are four different facts and must not share one
  message. Per 2.2 and 2.4.
- R-10 BOTH HOSTS BEHAVE IDENTICALLY. `aw agy run` must not agent-execute an orchestrator. The
  decision predicate and the retirement transition are shared code (`runner_shared.py`), not two
  copies, per the anti-re-fork discipline `2r306y`/`818uru` established.
- R-11 THE DOCUMENTED CLAIM MUST MATCH THE CODE. `AGENTS.md:42` asserts self-finalization works today.
  It must be corrected in the same change that makes it true, and must not be corrected to a NEW
  overstatement.

## 4. Deliberately out of scope

- The general `dependency-blocked`-is-terminal defect for ORDINARY items, and the all-or-nothing drain
  break. That is `nueip1`, a sibling item; the two share the same ~40-line region but neither subsumes
  the other.
- `EXECUTION_SUCCESS_STATES` accepting `substantially-complete` for an `executed:` DEPENDENCY EDGE
  (`oc_runipd.py:274`). That is a distinct dispatch defect, observed on `xdr83v`, and is not this
  spec's; R-2 only fixes what counts for RETIREMENT.
- The `aw set executed` worker-role bypass (`status_set.py` checks `worker_role_active` zero times),
  which reopens `i452hf`. Related because it is another path around a lifecycle gate, but separate.
- Retiring the four orchestrators currently stuck in `pending/` (`rh5tt6`, `h0zljh`, `5e4sb6`,
  `3m0urk`). Only `rh5tt6` is a candidate under this spec's rules; `5e4sb6` fails R-3, and `h0zljh`
  and `3m0urk` fail R-2. Doing it is a consequence of the fix, not part of the mechanism.

## 5. Open questions

- OQ-1 (R-5, for the graduating plan): linter exemption versus a separate rollup transition. Both are
  defensible. An exemption keeps ONE transition path but teaches the honesty linter a special case that
  a future reader could over-generalize. A separate transition keeps the linter pure but risks drifting
  from the gates the main path enforces. Decide with the code in front of you and state the reason. The
  binding constraint either way: no new route by which a CHILD plan reaches `executed` without
  evidence.
- OQ-2 (R-3): how "the child set is fully authored" is determined. Candidates: parse the orchestrator's
  `## Child IPDs` table and require every declared row to resolve to a plan; or require an explicit
  metadata assertion. Table parsing is fragile (`5e4sb6`'s row is literally `03+`), an explicit field
  is reliable but must be backfilled for existing orchestrators. Not blocking: a conservative refusal
  when the answer is unclear satisfies R-3.
