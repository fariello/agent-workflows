- Id: 754txs
- Status: open
- Set: rdattest
- Priority: high
- Work-Kind: security
- Summary: the auto-approve predicate trusts a Readiness field without verifying a review produced it, so IPD-M107 is detection at the lint layer while the --full-auto promotion path remains credulous

## Workflow history
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
