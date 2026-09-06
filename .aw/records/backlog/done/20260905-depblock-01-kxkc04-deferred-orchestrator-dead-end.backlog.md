- Id: kxkc04
- Status: done
- Set: depblock
- Priority: high
- Work-Kind: bug
- Summary: an orchestrator deferred early can never finalize later in the same run: the deferral path writes a terminal status instead of leaving it queued

## Workflow history
- 2026-09-06 done (aw set): FIXED and PROVEN IN PRODUCTION. All four orchretire plans are executed (5942n7, ueg5cf, pgq326, 84j8d7), each carrying From-Backlog: kxkc04. The proof is a real run, not a test: run-20260906T222302Z-2985274 retired orchestrator 84j8d7 to executed in 6s for $0.00 and ZERO tokens, spending no agent turn, and the ledger now records orchestrator-finalized=1 - the FIRST successful orchestrator rollup in 100+ runs against the 28 orchestrator-deferred measured when this item was filed. The addendum's warning was also vindicated in production: the first attempt correctly REFUSED and rolled back (finalize-refused, a transient pre-commit failure) leaving 84j8d7 intact at approved, which is exactly the TERMINATE-not-retry behavior the original 'leave it queued' prescription would have hung on. Sibling nueip1 (dependency-blocked is terminal, never revisited) stays open and separate.
- 2026-09-06 graduated (aw set): Graduated into spec 77tr3o (approved by maintainer attestation) and plan Set 'orchretire': orchestrator 84j8d7, children 5942n7 (shared on-disk eligibility predicate), ueg5cf (runner-owned transition resolving the E/V + receipt gates), pgq326 (both-host dispatch wiring + AGENTS.md correction). All four carry From-Backlog: kxkc04 and From-Spec: 77tr3o; all four report aw ipd lint conforming with a full E/V bijection. An addendum was appended to this item first, because the original prescription ('leave it queued') would have HUNG the finalize-refused case: measured 0 orchestrator-finalized vs 28 orchestrator-deferred across 102 runs, so the rollup has never once worked, and rh5tt6 shows a structural refusal that must TERMINATE rather than be retried. Sibling nueip1 stays open and separate.
- 2026-09-05 created (aw backlog): an orchestrator deferred early can never finalize later in the same run: the deferral path writes a terminal status instead of leaving it queued

THE DEFECT. The orchestrator dispatch path (`oc_runipd.py:5886-5924`) tests whether every child of
the Set reached `executed`. When they have not, it writes:

    runnable["status"] = "dependency-blocked"     # oc_runipd.py:5908

and then `continue`s. The run correctly keeps going - but the orchestrator is now
`dependency-blocked`, which is in `TERMINAL_STATES` (`oc_runipd.py:249`), so it is no longer
`queued` and the selection filter (`oc_runipd.py:5812`) excludes it FOREVER.

Consequence: its children can all reach `executed` later in the very same run, and the orchestrator
will still never be finalized. The event is even named `orchestrator-deferred`
(`oc_runipd.py:5914`) - a deferral is by definition something you come back to, and nothing ever
does.

WHY IT USUALLY HIDES. `dependency_depth` (`oc_runipd.py:3250`) treats every non-orchestrator
member of the Set as a prerequisite (`oc_runipd.py:3270-3279`), and depth is the FIRST key in
`queue_sort_key` (`oc_runipd.py:3285`). So an orchestrator normally sorts AFTER its children and is
not reached until they are done. The bug only bites when the orchestrator is dispatched while
children are still outstanding - which is exactly what happens when a child is slow, or blocked, or
when the children are not in this run's queue at all.

MEASURED. Run `run-20260905T050043Z-639569`: `5e4sb6` (Set `rununify`, an Order-0 orchestrator)
was deferred at 05:00:44, ONE SECOND into a 7h40m run, and stayed `dependency-blocked` for the
entire run. Three other orchestrators in that run (`rh5tt6`, `3m0urk`, `h0zljh`) ended `queued`,
i.e. never reached, so the incident shows the failure and the normal case side by side.

THE FIX. Do not write a terminal status for a condition that may clear. Leave the orchestrator
`queued` and let the next loop iteration re-test it - which is precisely what the loop already does
for items merely SKIPPED by the inner selection pass (`oc_runipd.py:5829-5833`), where no status is
written and the item is naturally reconsidered. The orchestrator path should behave the same way.

Reserve a terminal status for the genuinely dead case: a child that reached a non-success TERMINAL
state can never become `executed`, so THAT orchestrator really is finished and should say so. The
distinction "not ready yet" versus "can never be ready" is the same one item `nueip1` covers for
ordinary items; this is its orchestrator-specific half. Fix them together if convenient, but neither
subsumes the other: `nueip1` is about the drain-time mass-labelling path, this is about a single
write on the orchestrate branch.

GUARD AGAINST A NEW HANG. Leaving it `queued` must not let the loop spin forever re-testing an
orchestrator whose children will never finish. The drain-time path
(`oc_runipd.py:5847`, when `runnable is None`) already terminates a run whose remaining items are
unsatisfiable, so an orchestrator left queued with dead children will be labelled there. Verify that
explicitly rather than assuming it, and make sure the reported reason names the actual unfinished or
dead children.

SECOND, SEPARABLE DEFECT ON THIS PATH - "no children in queue" is reported as "unmet
dependencies" naming none. `_set_children_all_executed` (`oc_runipd.py:717-736`) returns
`(saw_child and not unfinished), unfinished`, so when the Set has NO children in this run's queue it
returns `(False, [])` under the documented "No children in-queue means nothing to gate on; treat as
not-all-done (safe)" branch. That produced `5e4sb6`'s event with `unfinished_children: []` and a
run summary reading "dependency-blocked (unmet dependencies)" while naming no dependency at all.

The safe default is CORRECT and must not change. The MESSAGE is the defect: distinguish "children
exist and are unfinished: <ids>" from "no children of Set <setid> are in this run's queue", and say
which. Note that for the second case waiting genuinely cannot help, so it IS legitimately terminal -
it should simply say so accurately instead of implying a dependency it cannot name.

Filed as one item because both defects live on the same ~40-line branch and a fix touching one should
correct the other. `5e4sb6`'s own children (`2r306y`, `818uru`) are already `executed` on main,
so that orchestrator is finalizable by hand today, independent of this fix.

---

## ADDENDUM 2026-09-06 (measured at HEAD `844d195c`, during graduation)

Three corrections and additions found while graduating this item. The original analysis above is
accurate; it is INCOMPLETE in a way that would have made a literal implementation of its prescription
introduce a new hang.

FIRST, AND MOST IMPORTANT: THIS HAS NEVER WORKED, EVER.

    $ grep -rh "orchestrator-finalized" .aw/records/runs/*/events.jsonl | wc -l
    0
    $ grep -rh "orchestrator-deferred"  .aw/records/runs/*/events.jsonl | wc -l
    28

28 deferrals across 15 distinct orchestrators (`3b4f8u`, `5e4sb6`, `88h0h8`, `bl9q3d`, `c2tvmm`,
`dh5gnl`, `e6h1p3`, `r4mbcw`, `r7xku3`, `rh5tt6`, `ryvoi5`, `u5vyye`, `y0gg8o`, `yt93ir`, `zpbx7o`);
ZERO successes in 102 runs. Every orchestrator now in `executed/` was finalized by a human or by an
agent doing manual whole-Set verification. It was born broken: the gated terminal transition landed
`99760832` (2026-08-24) and `finalize_orchestrator` was written `801dd28a` (2026-08-27), three days
later, against a gate that already refused it. So this is not a regression and not an edge case; the
feature has never once run.

SECOND: THE PRESCRIPTION ABOVE ("leave it `queued`") IS RIGHT FOR 27 OF THE 28 AND WOULD HANG THE 28TH.

There are TWO unrelated failures sharing the one `else` (`oc_runipd.py:7014`), proven by the two
reasons recorded on a single run (`run-20260905T211011Z-3780617`):

    5e4sb6 | reason: not-all-children-executed | unfinished: []
    rh5tt6 | reason: finalize-refused          | unfinished: []

`rh5tt6`'s `all_done` was TRUE. All five `wslayout` children are `executed`. The FINALIZE ITSELF
refused, for two stacked structural reasons, both reproduced verbatim:

    $ aw ipd set executed rh5tt6 --actor "aw oc run (orchestrator rollup)" -m "..."
    refused: no begin receipt for rh5tt6   # an orchestrator is never agent-executed, so none can exist

    # after writing one with `aw ipd begin` (probe receipt deleted immediately):
    refused: pre-transition gate did NOT conform
      IPD-S404 E-01/E-02: not 'performed'   V-01/V-02: empty Observed evidence

`check_checkpoint` (`ipd_lint.py:694-725`) applies the E/V requirement UNCONDITIONALLY and
`grep -c orchestrator agent_workflows/ipd_lint.py` is 0, so the linter has no orchestrator concept.
Leaving THIS case `queued` would retry a structurally impossible finalize every loop iteration. The
fix needs a three-way outcome (retire / reconsider / terminate), not a two-way one, with
`finalize-refused` classified TERMINATE.

THIRD: TWO REQUIREMENTS THE MAINTAINER STATED THAT THIS ITEM DOES NOT CAPTURE.

1. `aw run` RENDERS THE ORCHESTRATOR NULL-AND-VOID. The orchestrator exists for the AGENT-DRIVEN path;
   the runner's own ordering, isolation and per-child merge gate supersede its coordination role. So its
   `E-*`/`V-*` items are by design performed by NOBODY under `aw run`, which is why the honesty gate and
   the rollup are in direct contradiction. Retirement must be honest about being a rollup, not claim
   those items were performed.
2. IT MUST FIRE WHEN A RUN COMPLETES THE SET'S LAST OUTSTANDING CHILD, even if that run did not run the
   others. `_set_children_all_executed` (`oc_runipd.py:751-770`) reads `state["queue"]` ONLY, so this is
   unimplementable as written. `wslayout` passed its check incidentally: child `wpu5zu` executed in an
   EARLIER run and was absent from this queue. Set completeness must be read from the PLANS TREE.

FOURTH: A COMPLETENESS CHECK OVER EXISTING MEMBERS IS UNSOUND, and this is the guard most likely to be
missed. `rununify`'s two children (`2r306y`, `818uru`) are both `executed` on disk, so a naive "every
member executed" rule would retire `5e4sb6`. That would be WRONG: `5e4sb6`'s child table declares a row
`03+` ("one child per cohesive group of diverged symbols") that was NEVER AUTHORED. The Set is genuinely
mid-flight. Note the row token is literally `03+`, so exact numeric parsing is impossible in the one
case that matters, and the check must fail closed.

FIFTH: THE AGY RUNNER HAS NO ORCHESTRATE ACTION AT ALL, verified by object identity rather than grep:
`action_for`, `finalize_orchestrator` and `_set_children_all_executed` are ALL absent from
`agy_runipd`, which calls its own `determine_action` (`:1510-1514`) at `:1783`. So
`agy.determine_action('approved')` is `'execute'` where `oc.action_for('orchestrator','approved')` is
`'orchestrate'`: `aw agy run` would AGENT-EXECUTE an orchestrator, a worse failure than oc's.

SIXTH: `AGENTS.md:42` ASSERTS THIS WORKS and instructs agents not to raise it ("Do NOT raise ...
orchestrator finalization: those are solved"). Given 0 successes in 102 runs, that instruction has been
actively suppressing reports of a live defect. The text is GENERATED from `engine.py`'s managed-block
source, so a direct edit to `AGENTS.md` is reverted on the next install.

GRADUATED 2026-09-06 into spec `77tr3o` (approved by maintainer attestation) and plan Set `orchretire`:
orchestrator `84j8d7`, children `5942n7` (shared on-disk eligibility predicate), `ueg5cf` (the
runner-owned transition resolving the E/V and receipt gates), `pgq326` (both-host dispatch wiring plus
the AGENTS.md correction). The sibling item `nueip1` remains open and separate: it owns the general
`dependency-blocked`-is-terminal defect for ORDINARY items and the all-or-nothing drain break, which
this Set deliberately excludes.
