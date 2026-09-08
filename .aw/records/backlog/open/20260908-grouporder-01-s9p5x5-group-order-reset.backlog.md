- Id: s9p5x5
- Status: open
- Blocks-Release: next
- Set: grouporder
- Priority: high
- Work-Kind: bug
- Summary: aw group plans --set X --rename without --order silently renumbers every named plan from Order 0, demoting a child to the orchestrator-reserved slot and producing an IPD-M104 violation aw check cannot see

## Workflow history
- 2026-09-08 created (aw backlog): aw group plans --set X --rename without --order silently renumbers every named plan from Order 0, demoting a child to the orchestrator-reserved slot and producing an IPD-M104 violation aw check cannot see

DISCOVERED 2026-09-08 while graduating backlog `sjsoqq`, and filed late: it was recorded only in the
PROSE of four artifacts (`sjsoqq`'s body, and findings on plans `yku4ga`, `drzbs9`, `dw7i3m`), each saying
it was "reported separately" when no durable carrier existed. That is exactly the failure
`durablecapture`/`rnkqrc` exists to prevent, so this item is the correction as well as the defect.

REPRODUCED DETERMINISTICALLY IN A THROWAWAY REPOSITORY, not inferred from the live tree. Scaffold an
orchestrator at Order 0 and two children at Orders 1 and 2, then regroup ONE child without `--order`:

    $ aw ipd scaffold --kind orchestrator --title "Probe parent" --set probeset --order 0 --apply
    $ aw ipd scaffold --kind child --title "Probe child one" --set probeset --order 1 --apply
    $ aw ipd scaffold --kind child --title "Probe child two" --set probeset --order 2 --apply
    $ aw group plans 6sqcqe --set newset --rename --apply
    renamed .../20260908-probeset-01-6sqcqe-probe-child-one.ipd.md
         -> .../20260908-newset-00-6sqcqe-probe-child-one.ipd.md

The child's `- Order:` became `0` and its FILENAME slot became `00`, which the naming grammar reserves
for an orchestrator (`NN` with `00` reserved for the parent, `01+` for children). No warning, exit 0.

ROOT CAUSE, exact and small. `plans_refs.run_set_assign` reads the flag and substitutes ZERO when it is
absent, rather than preserving each plan's existing Order:

    start = getattr(args, "order", None)                      # plans_refs.py:432
    plans, err = plan_set_assign(..., start_order=start if start is not None else 0, ...)   # :437

`plan_set_assign` then assigns `order = start_order + i` per named plan (`:225`), so with no `--order`
the FIRST named plan always lands on 0 and the rest renumber from there. The default is
`start_order: int = 0` in the signature (`:212`), so the sentinel is indistinguishable from a deliberate
`--order 0`.

WHY THIS IS WORSE THAN A COSMETIC RENUMBER, and the reason it is `high` rather than `medium`:

1. IT PRODUCES A LINT VIOLATION THE REPO-WIDE SWEEP CANNOT SEE. Measured on the probe: `aw ipd lint`
   reports `error IPD-M104: Order: child Order must be an integer >= 1`, while `aw check plans` in the
   same tree reports `errors 0 warnings 0`. So the tool writes a state that only a per-file verb can
   detect. That reachability gap is separately tracked as `q0h9ls` (graduated to plan `k9awrq`), and
   this defect is a concrete instance of why it matters: a repair verb can commit a violation.
2. IT SILENTLY BREAKS SET SEMANTICS. Order `00` means orchestrator. A child sitting there makes the Set
   claim two parents, which is what the `orchprobe` Set (`5ev6lh`) exists to reason about.
3. IT FIRES ON THE REPAIR PATH. `aw group ... --set <new>` is the exact command the setid-collision
   refusal RECOMMENDS as its recovery (spec `4w7d6s` I4, and the planned refusal message in
   `setidhard` Order 03). So an operator following the tool's own advice corrupts Orders while fixing a
   collision.

OBSERVED LIVE, BEFORE the throwaway reproduction: regrouping the four `setiduniq` plans to `setidhard`
put ALL FOUR at Order `00`, including three children, in one command. Recovered by re-running with
explicit `--order 1|2|3`, so no bad state was committed; the graduated `setidhard` Set is correct on disk.

WHAT TO DECIDE, not prescribed here:

- SHOULD THE DEFAULT PRESERVE each plan's existing Order rather than renumber? That is the obvious fix
  and it needs a distinguishable sentinel, since `start_order=0` currently cannot be told from an
  explicit `--order 0`.
- OR SHOULD A MULTI-PLAN CALL still renumber sequentially (which is a legitimate use: assembling a Set
  from scattered plans) while a SINGLE-plan call preserves? If so, say it in `--help`, because today the
  flag's absence means something the flag's documentation does not mention.
- SHOULD THE VERB REFUSE to place a `Kind: child` at Order 0 at all, regardless of the flag? That is the
  fail-closed option and would catch an explicit `--order 0` mistake too. Note `aw ipd lint` already
  knows this rule (`IPD-M104`), so the predicate exists and is not consulted at the write site: the same
  shape as `sjsoqq`'s setid-collision-at-creation gap.
- DOES `aw rename` SHARE THE DEFECT? It goes through the same rename machinery and was NOT tested here.
  Check before assuming it is clean.

RELATED. `q0h9ls`/`k9awrq` (the `aw check` lint-reachability gap this defect hides behind). `sjsoqq`/
`setidhard` (whose Order 03 will make this verb the recommended recovery for a collision refusal, so a
fix should land before or with it). `rnkqrc` (`durablecapture`), whose whole subject is an IPD naming a
defect with no durable carrier, which is how this one was nearly lost.
