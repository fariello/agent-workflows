- Id: 5ev6lh
- Status: open
- Set: rollupev
- Priority: medium
- Work-Kind: bug
- Summary: Runner rollup omits the E/V checkpoint for orchestrators, silently discharging real verification work unperformed

## Workflow history
- 2026-09-07 created (aw backlog): Runner rollup omits the E/V checkpoint for orchestrators, silently discharging real verification work unperformed

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
