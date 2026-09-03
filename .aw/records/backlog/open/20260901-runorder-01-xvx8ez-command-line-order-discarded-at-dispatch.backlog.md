- Id: xvx8ez
- Status: open
- Blocks-Release: next
- Set: runorder
- Priority: high
- Work-Kind: bug
- Summary: aw oc run A B silently executes B first (typed order recorded as position but sorted LAST, so setid decides alphabetically); honor the typed order AND announce any dependency-caused reordering loudly, naming both orders and the causing edge

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

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

DECIDED BY THE MAINTAINER 2026-09-01: HONOR THE TYPED ORDER. Move `position` ABOVE `setid` in
`queue_sort_key`, so an explicitly-typed list executes in the order the operator typed. The open
questions below are kept as the record of what was chosen against.

WHY THIS IS SAFE, and it is the fact that made the decision easy: `dependency_depth` is FIRST in the
key and STAYS first, so a declared `Item-Dependencies` edge always beats a typed sequence. Honoring the
operator's order therefore cannot make an unsatisfied node runnable, which is the property spec 25kzda
5.4 rule 5 exists to protect. The change moves `position` past `setid`/`order` only.

MEASURED USAGE that shaped the ruling. Two distinct patterns in the run history:
  (a) SMALL EXPLICIT LISTS the operator typed, e.g. `aw oc run m73aet 6lu3rq` (2 items, 2 Sets). The
      typed order is plainly an instruction here, and this is the case the bug broke.
  (b) LARGE SELECTOR EXPANSIONS, e.g. observed runs of 7 and 12 items spanning 5-6 Sets
      (`run-20260830T044707Z-4118154`: 12 items across detrun/findidx/gatestale/lanename/scopeattrib/
      testinvoke). There is NO meaningful typed order in this case, because the operator named a
      selector and the runner expanded it.
So honoring `position` is meaningful for (a) and a no-op in practice for (b), where `position` merely
reflects expansion order and any total order is equally defensible. That is why the simple fix was
chosen over detecting explicit-vs-expanded (which would require the runner to record HOW the queue was
built: new durable state, more surface, for no gain in case (b)).
Also measured: multi-item runs are the NORMAL mode, not an edge case (6 recent runs had 2+ items), and
11 of 26 pending plans already declare a dependency edge, so the declared-edge path is in real use.

IMPLEMENTATION NOTES for whoever executes this.
1. ONE function, `oc_runipd.queue_sort_key`. VERIFIED `agy_runipd.queue_sort_key IS` the same object
   (re-exported, not reimplemented), so one edit covers both drivers. Do NOT introduce a second copy.
2. The new key is `(dependency_depth, position, setid, order, id6)`. Note `position` is currently
   documented in that function's own docstring as "LAST and is a stable identity, never a priority" -
   that docstring becomes FALSE and must be rewritten, not left to mislead the next reader.
3. THE DOCSTRING'S UNDERLYING POINT STILL HOLDS and must be preserved: `position` is also the key for
   outcome/prompt/session filenames and this run's decision ids, so it must remain FROZEN at
   queue-build time. Making it a sort input must not make it mutable.
4. This makes the sort depend on INVOCATION order, so two runs over the same set of plans expressed
   differently will order differently. That is the intent, but the function is currently documented as
   deterministic from artifact content alone; update that claim honestly rather than silently.
5. SPEC IMPACT: spec `25kzda` 5.4 rule 4 fixes the order as "dependency depth, type rank, Set, numeric
   Order, stable ID, then canonical path" and does not mention operator order. This ruling CHANGES that
   rule, so the spec needs a corresponding amendment; do not implement a divergence from an unamended
   spec and leave the two disagreeing.
6. TESTS must cover the regression directly: two independent plans whose Sets sort OPPOSITE to the
   typed order (the real case was `runtrail` typed first but `runmixed` sorting first alphabetically),
   asserting dispatch follows the typed order. Also assert a declared edge STILL wins over typed order,
   so fixing this cannot silently break rule 5.
7. FIX THE SUMMARY TABLE TOO (see the open question below): it displayed `01 m73aet` / `02 6lu3rq`
   while execution ran 02 then 01, which is what made the inversion look like a display glitch. Once
   position drives the order these agree by construction, but confirm it rather than assuming.

ADDITIONAL MAINTAINER REQUIREMENT 2026-09-01: ANY reordering caused by DEPENDENCIES must be announced
LOUDLY, and possibly interactively. Silent reordering is the actual defect; getting the order right but
still doing it invisibly would only half-fix this.

So the fix has TWO parts, and the second is not optional:
  (A) honor the typed order (the ruling above), and
  (B) SAY SO whenever the executed order differs from the order the operator expressed, naming BOTH
      orders and WHY they differ.

WHAT "WHY" MUST NAME, because a bare "reordered" line is not actionable: the specific edge that forced
it, e.g. "6lu3rq before m73aet: 6lu3rq declares `executed:m73aet`", or for a depth tie broken by
another field, which field broke it. The operator must be able to tell a DECLARED prerequisite (correct
and expected) from a TIEBREAK (arbitrary, and the thing that bit them tonight).

MEASURED GAP: the driver announces NOTHING about ordering today. Greps for a queue/order announcement
in `oc_runipd.py` return only comments. Tonight the ONLY way to discover the inversion was to read
`events.jsonl` timestamps after the fact and compare them against `state.json` positions.

AND THE EXISTING PREVIEW WOULD NOT HAVE HELPED, which is a second defect to fix here: `--prepare-only`
already exists and prints the queue via `print_status` -> `render_run_summary_table`, but that table
renders in POSITION order, not EXECUTION order. So a pre-flight preview tonight would have shown
`01 m73aet, 02 6lu3rq` and still executed 6lu3rq first. The preview must show EXECUTION order (or show
both, explicitly labelled), or it actively misleads.

HARD CONSTRAINT ON THE INTERACTIVE PART, and it is hard-won: DO NOT prompt from anywhere a child
process can inherit. `oc_runipd.py:711-715` records that a nested `aw` seeing an inherited TTY
"believes it may prompt, and blocks on input() forever while its prompt goes into the pipe" - VERIFIED
to have WEDGED A FINALIZE FOR 1h49m (backlog `v1ex5z`, ttywedge Order 01 `g40w37`), which is why the
driver now passes `stdin=subprocess.DEVNULL` to children. Any confirmation must therefore happen in the
DRIVER, at queue-build time, BEFORE the first child is spawned, and must fall back to non-interactive
behavior when there is no TTY. An unattended overnight run must never block on a prompt: that would
turn tonight's inconvenience into a run that silently does nothing for hours.

RECOMMENDED SHAPE, to be confirmed at execution:
  * ALWAYS print the execution order at queue build, unconditionally, whether or not it was reordered.
    Cheap, and it makes the order auditable in the log rather than reconstructible from timestamps.
  * When the executed order DIFFERS from the expressed order, print a distinct WARNING naming both
    orders and the causing edge per moved item.
  * PROMPT only when (a) the order was changed, (b) the driver has a real TTY, and (c) the run was not
    started with an unattended flag. Otherwise print the warning and proceed, since refusing would
    break unattended operation for a condition that is usually legitimate.
  * Record the announcement in the run's durable state/events too, so a later reader sees it without
    the terminal scrollback. Tonight's `events.jsonl` had `ipd-started` timestamps but no ordering
    rationale.

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
