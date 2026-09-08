- Id: 754txs
- Status: graduated
- Set: rdattest
- Priority: high
- Work-Kind: security
- Summary: the auto-approve predicate trusts a Readiness field without verifying a review produced it, so IPD-M107 is detection at the lint layer while the --full-auto promotion path remains credulous

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan 8v5pwa (Set rdattest, Order 02, .aw/records/plans/pending/20260908-rdattest-02-8v5pwa-...ipd.md), which carries From-Backlog: 754txs. NOTE ON THE GATE: this item carries NO - Blocks-Release: field, so the plan inherits none; it is Work-Kind: security at Priority: high but the maintainer did not gate it, and I did not add a gate the item does not carry. Status graduated (design handed off), NOT done. NOTHING IN THIS ITEM IS OBSOLETE. Verified 2026-09-08 at HEAD 8b4e1570 BY RUNNING IT: a fixture plan carrying '- Readiness: go' whose only history line is '- 2026-09-08 to-review (someone): authored, NO review ever happened.' yields plan_readiness.is_plan_review_approved(...) == True, exactly as this item reports. The decision order it describes is intact at plan_readiness.py:297-327 (read_readiness first at :312, return on a valid value at :313-315, refuse outright on out-of-vocab at :316-320, prose fallback ONLY when absent at :322-327). FOUR LIVE CONSUMERS confirm the blast radius is real, both hosts: oc_runipd.py:2968 and :6718, agy_runipd.py:1988 and :3988. TWO MEASUREMENTS THAT DE-RISK THE FIX AND ANSWER THIS ITEM'S OWN STATED COST. FIRST, and this is the important one: this item's honest worry is that 'a legitimate review that wrote the field but whose history line does not match the evidence pattern would newly fail closed', and it treats that as the price of the change. I MEASURED THE PRICE AND IT IS ZERO TODAY. Across every tracked plan, 65 carry a Readiness field, and the number whose auto-approve verdict would FLIP from True to False under the proposed change is 0. So the fail-closed direction costs nothing against the current corpus, which converts the main objection from a real cost into a bounded risk about FUTURE phrasings; the plan re-measures it at execution time and classifies any flip individually. SECOND, this item asks (option 2) whether the predicate should call the lint rule directly and worries about the import direction because plan_readiness is consumed by both drivers and 'whatever it imports must stay stdlib-cheap and driver-agnostic'. I verified option 2 IS SAFE: ipd_lint imports only argparse, re, pathlib, typing, plus ipd_schema and term; it names no driver module; and it does NOT import plan_readiness (the only mentions in ipd_lint.py and ipd_schema.py are comments), so there is no cycle. The anti-divergence guard tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests::test_shared_rule_modules_are_not_modified_by_the_runner forbids ipd_lint/check_engine NAMING a driver, which this change does not do. THE PLAN THEREFORE IMPLEMENTS OPTION 2 AND REJECTS OPTION 1, with the reason recorded: plan_readiness exists BECAUSE this logic was duplicated once already (its own docstring records that is_plan_review_approved and its history helper lived twice, once per driver), so re-implementing the evidence check inside it would create a second definition of 'attested' that can drift from IPD-M107 exactly as the field and the history drifted in the first place. Option 3 (the forged-field test) is graduated as the plan's E-04 and is treated as this item calls it, the real deliverable, with five separate assertions and a requirement to prove the forged case FAILS against pre-change code. The plan also preserves the three other decisions the predicate makes (out-of-vocab refusal, absent-field prose fallback, unresolved-blocking-question refusal) and the documented boundary that it does not read - Status:. This item's HONEST SCOPE note is what the plan closes: IPD-M107 blocks the EXECUTION boundary (aw ipd begin) and a corpus test polices the tree, leaving reachable only the narrower window where the predicate is consulted directly on an unlinted plan, and any future caller that does not lint first.
- 2026-09-06 created (aw backlog): the auto-approve predicate trusts a Readiness field without verifying a review produced it, so IPD-M107 is detection at the lint layer while the --full-auto promotion path remains credulous

Found 2026-09-06 while fixing the fabricated-`Readiness` incident (`IPD-M107`, same Set).

THE RESIDUAL GAP. `IPD-M107` makes an unattested `- Readiness:` a BLOCKING lint finding, which does
stop `aw ipd begin` (verified: the `pre-execution` gate refuses, no receipt written). But
`plan_readiness.is_plan_review_approved` itself is UNCHANGED and still believes the field:

    # a plan carrying a hand-written Readiness and NO review in its history
    >>> plan_readiness.is_plan_review_approved(path)
    True

So the predicate that `--full-auto` consumes to promote `reviewed -> approved` and flip an item's
queue action to `execute` will still return True for a forged field. The lint rule catches the
artifact; it does not harden the decision.

WHY THIS IS FILED SEPARATELY rather than fixed in the same pass: changing the predicate changes the
meaning of the `--full-auto` gate, which is a policy decision with a real downside in the other
direction. `plan_readiness`'s own docstring is explicit that the field is read FIRST precisely so a
review can record a machine-readable verdict, and that an out-of-vocab value is refused outright
while ABSENCE falls back to prose. Making the predicate ALSO demand history evidence would mean a
legitimate review that wrote the field but whose history line does not match the evidence pattern
would newly fail closed. That is the safe direction, but it is still a behavior change to a shipped
gate and deserves its own review rather than riding along with a lint addition.

WHAT TO DECIDE:
1. Should `is_plan_review_approved` require the SAME history evidence `IPD-M107` requires, so field
   and history must AGREE? This is the obvious fix and is fail-closed. Cost: a review that records
   readiness in an unusual phrasing stops auto-approving until its history matches.
2. Or should the predicate call the lint rule directly (one predicate, no second definition of
   "attested"), accepting the import direction that creates? Note `plan_readiness` is deliberately
   consumed by both host drivers, so whatever it imports must stay stdlib-cheap and driver-agnostic.
3. Either way, add a test asserting the predicate returns False for a forged field. That test is the
   real deliverable; the incident showed the predicate returning True four times in a row with
   nothing behind it.

HONEST SCOPE OF THE CURRENT MITIGATION, so nobody over-trusts it: `IPD-M107` blocks the EXECUTION
boundary (`aw ipd begin`), and a corpus test scans all 488 tracked plans, so a forged field cannot
reach execution or survive in the tree unnoticed. What remains reachable is the narrower window where
the predicate is consulted directly on a plan that has not yet been linted, and any future caller of
the predicate that does not lint first.
