- Id: 5ev6lh
- Status: graduated
- Set: rollupev
- Priority: medium
- Work-Kind: bug
- Summary: Runner rollup omits the E/V checkpoint for orchestrators, silently discharging real verification work unperformed

## Workflow history
- 2026-09-08 graduated (aw set): STATUS WAS STALE; already graduated. No new plan authored and none should be: the orchprobe Set already carries this item and orchestrator yeh7gc declares From-Backlog: 5ev6lh (verified). Four plans: yeh7gc (Order 0), r2i1b1 (01), 8tgg6g (02), m7gvuz (03). The Set took exactly the (c)+(d) pair this item called the pragmatic one: yeh7gc/r2i1b1 surface the discharged-unperformed items and the per-item refusal reason, m7gvuz probes every queued orchestrator pre-run, 8tgg6g caches the verdict against a content digest to bound the cost. Directions (a) and (b) were deliberately not taken. Core measurement re-verified at HEAD: 84j8d7 still sits in executed/ with 'Execution state: pending' on E-01 and 'Result: pending' on V-01, so the false completion claim is still in the record. NOT closed by this transition: whether 84j8d7 needs a corrective IPD for its unperformed E-01/V-01 remains a maintainer call, preserved in the item body and also recorded by 3v7wo6 E-02.
- 2026-09-07 created (aw backlog): Runner rollup omits the E/V checkpoint for orchestrators, silently discharging real verification work unperformed

ALREADY GRADUATED; STATUS WAS SIMPLY STALE. Recorded 2026-09-08. NO NEW PLAN WAS AUTHORED for this item
and none should be: the `orchprobe` Set already carries it, and orchestrator `yeh7gc` declares
`- From-Backlog: 5ev6lh` (verified). The Set is four plans: `yeh7gc` (Order 0, orchestrator),
`r2i1b1` (01), `8tgg6g` (02), `m7gvuz` (03). The only change made here is `open` -> `graduated`, which
is what the handoff should have recorded when the Set was authored.

HOW THE SET MAPS ONTO THIS ITEM'S CANDIDATE DIRECTIONS, so nobody re-graduates a direction already
covered. The item offered four and said "(c) and (d) are complementary and probably the pragmatic pair".
The Set took exactly that pair, plus the caching the probe needs: `yeh7gc` detects and SURFACES
orchestrator-only work the runner would discharge unperformed (direction (c)); `r2i1b1` surfaces a
per-item refusal reason AND its remedy in the run record (also (c), the "report loudly which items it
discharged" half); `m7gvuz` probes every queued orchestrator BEFORE the run (direction (d), moved to
pre-run rather than author time); `8tgg6g` caches a probe verdict against a content digest, which is what
bounds (d)'s cost. Direction (a) (machine-readable coverage) and (b) (a schema classification field) were
NOT taken, and the Set's review records why: coverage is decided per ITEM by classification at probe
time rather than by a new schema field.

THIS ITEM'S CORE MEASUREMENT IS STILL TRUE AT HEAD, so the Set is not chasing a resolved defect:
`84j8d7` still sits in `.aw/records/plans/executed/` carrying `Execution state: pending` on its E-01 and
`Result: pending` on its V-01 (verified by reading the file). The false completion claim is still in the
permanent record.

THE SECOND, SEPARATE THING THIS ITEM RECORDS IS STILL OWED AND IS NOT CLOSED BY THE SET: whether
`84j8d7` needs a CORRECTIVE IPD for its unperformed E-01/V-01. That is a maintainer call, it is preserved
in the final paragraph below, and `3v7wo6` E-02 also records it. Setting this item `graduated` does not
discharge it; `graduated` means the DESIGN is handed off, and the corrective-IPD decision is a separate
act by a human.

ORIGIN: option (c) of orchestrator `cczotj` OQ-04, resolved 2026-09-07. The maintainer chose option
(b) for THAT Set (demote the verification into child `3v7wo6`, where the checkpoint is enforced),
which is a per-Set workaround. This item is the DURABLE fix that option (c) named and that the
workaround does not deliver.

THE DEFECT. `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` deliberately skips
the pre-transition E/V checkpoint when the runner retires an orchestrator, on the premise (spec
`77tr3o` R-5 shape (b)) that an orchestrator's items are "performed by NOBODY". That premise is FALSE
for any orchestrator carrying real work, and when it is false the runner marks E-items complete and
V-items validated having never performed OR verified them.

MEASURED, TWICE. (1) Orchestrator `84j8d7` sits in `.aw/records/plans/executed/` RIGHT NOW carrying
`Execution state: pending` on its E-01 and `Result: pending` on its V-01, rollup-retired by run
`run-20260906T222606Z-2987341` (`orchestrator-finalized`, commit `52c2872a`), with its whole-Set
verification never performed. That is a false completion claim in the permanent record. (2) It had
ALREADY been warned against in its own text ("BUT DO NOT RETIRE THIS PLAN BY THE ROLLUP INSTEAD OF
PERFORMING E-01") and was retired by the rollup anyway, which is the repository's own recorded lesson
that informing an agent is necessary and not sufficient (`k1nity`).

SCALE, so the fix is not mis-sized: 46 of 130 orchestrators carry checklist items (measured
2026-09-07, per AGENTS.md). Most of those items are LEGITIMATE ORCHESTRATION (sequence the children,
confirm the ledger) and are correctly skippable, which is why a blunt "refuse to retire any
orchestrator with items" rule is WRONG and would break the common case. The distinction that matters
is whether an item is covered by a child.

CANDIDATE DIRECTIONS, none chosen: (a) make retirement REFUSE when an orchestrator's E-items are not
discharged by some child, which requires a machine-readable notion of coverage that does not exist
today; (b) classify items on the parent (orchestration versus work) and refuse only on the latter,
which needs a schema addition and would have to be lint-enforced to be real; (c) keep the omission but
have retirement REPORT loudly which items it discharged unperformed, the cheapest honest option and
strictly better than today's silence; (d) have `aw ipd lint` refuse to let an orchestrator carry an
E-item no child covers, moving the check to author time. (c) and (d) are complementary and probably
the pragmatic pair.

ALSO OWED, AND A SEPARATE DECISION: whether `84j8d7` needs a corrective IPD for its unperformed
E-01/V-01. Per AGENTS.md a plan already in `executed/` must NOT be edited in place, so the honest
route is a new corrective IPD carrying that verification. That is a maintainer call and is recorded
here so it is not lost; child `3v7wo6`'s E-02 also records it in the Set's walkthrough.
