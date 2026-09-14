- Id: alw22r
- Status: open
- Set: alw22r
- Priority: medium
- Work-Kind: chore
- Summary: rununify orchestrator 5e4sb6 refuses every run on its two deliberately-unauthored child rows and needs a scope decision

## Workflow history
- 2026-09-14 created (aw backlog): Observed refusing in three separate runs on 2026-09-14. Both authored children (2r306y, 818uru) are executed; rows 03+ and last are deliberate placeholders, so this needs a human scope decision (author / re-scope / park), not a patch.

## What happens

Orchestrator `5e4sb6` (Set `rununify`, Order 00) is `Status: approved` in `pending/`, so every
`aw oc run all`-shaped selection enqueues it, and every run refuses it immediately:

    orchestrator-deferred: Set 'rununify': the orchestrator's child table declares row(s) '03+',
    'last' that resolve to no plan, so the child set is not fully authored
    reason: unauthored-child-rows

Observed in three separate runs on 2026-09-14 alone (`run-20260914T020604Z-2541564`,
`run-20260914T020813Z-2543555`, `run-20260914T023758Z-3540874`). It will refuse in every future run
too, because nothing about the refusal is transient.

## Why it is not simply a bug to patch

The two AUTHORED children are both done: `2r306y` (Order 01) and `818uru` (Order 02) are `executed`.
The unresolvable rows are `03+` and `last`, and they are placeholders BY DESIGN. The plan says so:

    The child breakdown is DELIBERATELY NOT FIXED HERE, and that is a decision rather than an
    omission. E-01's inventory determines the honest seams, and inventing child scopes before
    measuring which of the 37 drifted symbols are reconcilable would be exactly the guesswork this
    plan exists to avoid.

Row `03+` means "one child per cohesive group of class (c) DIVERGED symbols", which cannot be
enumerated until E-01's inventory is read; row `last` closes the feature-parity gaps in the direction
E-01 decided. So the refusal is the retirement gate working correctly: the Set genuinely is not fully
authored, and retiring the parent would claim work nobody has scoped.

## The decision needed (a human's, not an agent's)

Pick one. Each is defensible and they have different costs.

1. AUTHOR THE REMAINING CHILDREN from E-01's inventory, then let the Set run to completion. This is
   what the plan intends. It is also the largest piece of work: `execute_item` alone is 572 lines and
   the plan says it may need a child to itself.
2. RE-SCOPE the orchestrator's child table to the two children that exist, moving `03+`/`last` into a
   successor Set or a backlog item. The Set then retires honestly and stops occupying a queue slot
   every night. Cheapest path to a quiet queue; needs a maintainer to agree the two shipped children
   are a defensible stopping point.
3. PARK the orchestrator (`Status: parked`, or move it out of `pending/`) so it is not enqueued while
   the decision waits. Stops the nightly noise without deciding anything, and keeps the record.

Do NOT "fix" this by deleting the `03+`/`last` rows to make the gate pass: that would retire the
parent while claiming two-thirds of its declared scope was delivered. Also do not hand-author
throwaway children just to satisfy the row count, for the same reason.

## Cost of leaving it

One refused item per run, reported as `dependency-blocked` in every execution report. Cosmetic per run,
but it trains a reader to ignore `dependency-blocked`, which is the state that also means "a real
prerequisite is missing".
