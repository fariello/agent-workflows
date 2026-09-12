- Id: 3q6tcr
- Status: open
- Blocks-Release: next
- Set: 3q6tcr
- Priority: low
- Work-Kind: bug
- Summary: aw backlog set has no --work-kind or --priority setter, so reclassifying an item requires a hand edit of a gate-bearing field

## Workflow history
- 2026-09-12 created (aw backlog): aw backlog set has no --work-kind or --priority setter, so reclassifying an item requires a hand edit of a gate-bearing field

## How this was found

Hit on 2026-09-12 carrying out a maintainer ruling to reclassify backlog `59t9x5` from `chore` to `bug`.
`aw backlog set --work-kind bug` fails with `unrecognized arguments`, so the field had to be hand-edited
and the rationale recorded through a separate `--message` call.

## The gap, measured at HEAD 2026-09-12

`aw ipd set` HAS both setters and documents them as persisting across a no-op transition:

    --priority {low,medium,high,-}      Set the plan's Priority ...  Persists on a no-op transition.
    --work-kind {bug,feature,chore,security,followup,-}

`aw backlog set` has NEITHER. Its options are `--status`, `--message`, `--gate-kind`, `--gate-ref`,
`--blocks-release`, `--evidence`, plus the usual dry-run/yes/commit flags. `aw backlog new` DOES accept
`--work-kind` and `--priority`, so the vocabulary exists and is validated at creation; only mutation is
missing. The asymmetry is the defect: the same field is tool-managed on a plan and hand-managed on a
backlog item.

WHY THIS IS MORE THAN AN ERGONOMIC WART. `Work-Kind: bug` is a GATE-BEARING value under the
no-known-bugs rule (see `nobugship` Set, and `di08i9` which defaults `Blocks-Release` on a bug at
creation). A field that decides whether an item blocks a release should not be reachable only by hand
edit, because a hand edit is exactly what the tooled-mutation convention exists to prevent: it leaves no
history record of its own, it cannot be validated against the enum, and it is invisible to any check that
watches for tooled transitions. Reclassifying an item is also precisely the moment the gate changes, so
the unrecorded path is the highest-consequence one.

## Scope

1. Add `--work-kind` and `--priority` to `aw backlog set`, mirroring `aw ipd set` including the `-`
   clearing sentinel and persistence across a no-op status transition.
2. Record the reclassification in the item's `## Workflow history` automatically, as the status
   transitions already are, so a gate-changing edit carries its own provenance.
3. Consider whether a `Work-Kind` change TO `bug` should apply the same `Blocks-Release` default that
   `di08i9` gives a bug at creation. Do not assume it: that is a behavior decision, and silently gating an
   item on reclassification could surprise. Raise it rather than deciding it.

## Related

`b5sfwm` recorded a maintainer decision of no `-` clearing sentinel on either sibling verb, and noted the
plan-side one is now a defect; whoever implements this should read that decision so the two verbs do not
diverge further. `di08i9` owns the bug-defaults-to-gated behavior.
