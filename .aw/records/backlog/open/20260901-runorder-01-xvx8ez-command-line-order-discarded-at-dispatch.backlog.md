- Id: xvx8ez
- Status: open
- Set: runorder
- Priority: high
- Work-Kind: bug
- Summary: aw oc run A B silently executes B first: the operator's typed order is recorded as position but sorted LAST, so setid decides alphabetically and a documented prerequisite ordering can be inverted without warning

## Workflow history
- 2026-09-01 created (aw backlog): aw oc run A B silently executes B first: the operator's typed order is recorded as position but sorted LAST, so setid decides alphabetically and a documented prerequisite ordering can be inverted without warning

OBSERVED 2026-09-01. The maintainer ran `aw oc run m73aet 6lu3rq`, meaning "run m73aet BEFORE 6lu3rq".
The runner executed 6lu3rq FIRST. The command-line order is recorded correctly and then discarded at
dispatch.

MEASURED, from run `run-20260901T042331Z-118022`.

Queue as built (correct, order preserved):
    position 1  m73aet  set=runtrail  order=1
    position 2  6lu3rq  set=runmixed  order=1

Actual dispatch, from `events.jsonl` (inverted):
    04:23:31  ipd-started   6lu3rq
    04:44:10  ipd-finished  6lu3rq
    04:44:10  ipd-started   m73aet
    05:23:09  ipd-finished  m73aet

ROOT CAUSE, and it is a DESIGN gap rather than an implementation slip. `oc_runipd.queue_sort_key`
returns:

    (dependency_depth(id6), setid, order, id6, position)

With two independent plans in DIFFERENT Sets and no declared edges, `dependency_depth` ties at 0 and
`setid` decides ALPHABETICALLY. `"runmixed" < "runtrail"` is True, so 6lu3rq wins. `position` - the
only field that carries the operator's typed order - is the LAST tiebreaker, and the function's own
docstring says so deliberately: "`position` is LAST and is a stable identity, never a priority".

THE SPEC NEVER CONTEMPLATED OPERATOR ORDER. Spec `25kzda` 5.4 rule 4 fixes the order as "dependency
depth, type rank (`spec`, `backlog`, `ipd`, `prompt`), Set, numeric Order, stable ID, then canonical
path". Nothing in that list is the sequence the operator typed. So the runner is behaving to spec, and
the SPEC is what needs a decision - which is why this is filed as a design bug and not a patch.

WHY THIS IS A CORRECTNESS BUG, NOT A COSMETIC ONE. A silent inversion of a stated prerequisite is
indistinguishable from correct behavior until something breaks downstream. CONCRETE, from this same
session: `wlxkoz`'s review requires `m73aet` to land FIRST, because 4 of its 13 `RUN-*` codes depend on
the commit trailers `m73aet` adds. Had the maintainer run `aw oc run m73aet wlxkoz`, the runner would
have executed `wlxkoz` first, because `"runcodes" < "runtrail"`. The operator would have followed the
documented ordering requirement exactly and been silently overruled.

Note this is precisely the hazard spec 5.4 rule 5 warns about in the OTHER direction ("Set/Order is
only a deterministic tiebreaker among nodes already ready; lower Order cannot make an unsatisfied node
runnable"). The spec was careful that ordering must not FAKE a satisfied dependency; it did not
consider that ordering must not SILENTLY OVERRIDE an operator's explicit sequence.

WHAT TO SOLVE FOR, not prescribed.

1. SHOULD COMMAND-LINE ORDER BE HONORED AT ALL? Two defensible positions. (a) YES: `aw oc run A B` is
   an imperative and the operator's sequence is an INPUT, so `position` should rank ABOVE `setid`
   (though still BELOW `dependency_depth`, since a declared edge must always win over a typed
   sequence). (b) NO: ordering is derived from declared dependencies by design, and an operator who
   needs a sequence should declare an `Item-Dependencies` edge, in which case the fix is not to reorder
   but to REFUSE or WARN when a multi-item selection's typed order contradicts the computed order.
   Option (b) is more principled and option (a) is what an operator expects; the repository cannot
   decide which, because it is a UX call.
2. IF (a): where exactly does `position` go in the tuple? Above `setid` honors the typed order while
   keeping declared edges authoritative. Note this makes the sort depend on invocation order, so two
   runs over the same selection expressed differently would order differently - that is the POINT, but
   it must be stated, because the current key is documented as fully deterministic from artifact
   content alone.
3. IF (b): the warning must be LOUD and must name both orders, or it reproduces this bug with extra
   steps. "Selection will execute in a different order than you typed: <computed> vs <typed>" plus how
   to force the intent.
4. EITHER WAY, the SUMMARY TABLE should show EXECUTION order, or at least mark it. The table listed
   `01 m73aet` then `02 6lu3rq` while execution ran 02 then 01, which is what made the inversion look
   like a display glitch ("why 2/2 then 1/2?"). The table is showing `position`, which is identity, not
   sequence. Showing identity in a column a reader will read as sequence is its own small defect.
5. THE `agy` DRIVER SHARES THE FUNCTION, so ONE fix covers both. VERIFIED:
   `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` returns True (it is re-exported, not
   reimplemented). Good news, and it means the anti-fork pattern `evgi9n` had to establish is already
   in place here; do NOT introduce a second copy while fixing this.

HONEST NOTE ON SEVERITY: no work was lost or corrupted by the inversion in this run, because the two
plans were genuinely independent (zero shared Scope-Paths, verified). The severity is HIGH because the
failure mode is SILENT and because a documented prerequisite ordering exists TODAY (`m73aet` before
`wlxkoz`) that this bug would invert.

EVIDENCE. `.aw/records/runs/run-20260901T042331Z-118022/state.json` (queue with positions) and
`events.jsonl` (`ipd-started` timestamps proving the dispatch order). `oc_runipd.queue_sort_key` and
its docstring. Spec `25kzda` 5.4 rules 4-5.
