- Id: gyw4gp
- Status: graduated
- Graduated-To: carrierauth
- Set: carriergate
- Priority: medium
- Work-Kind: chore
- Summary: A deferral whose carrier is DISCHARGED before the plan executes refuses the pre-transition gate, so an executor must hand-edit a correct row

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan xz59ai (Set carrierauth), re-verified live at HEAD.
- 2026-09-23 created (aw backlog): MEASURED while executing plan n9na1c on 2026-09-23. The plan's deferred row named '- Carrier: fuk1mr' for the baseline-subtraction work its sibling tgyfs2 owned. That was CORRECT AT AUTHORING TIME: fuk1mr was open and tgyfs2 was pending. By the time n9na1c executed, tgyfs2 had executed and fuk1mr had closed done - which is exactly what n9na1c's own '- Item-Dependencies: executed:tgyfs2' REQUIRED before it could start. 'aw ipd lint --phase pre-transition' then refused the plan: 'check.ipd-uncarried-obligation: 1 obligation(s) name no durable carrier: deferred row 1: carrier fuk1mr resolves only to a terminal/hidden artifact (done); nothing revisits it'.

THE REFUSAL IS NOT WRONG ABOUT THE END STATE. A reader pointed at a closed item would believe work is still pending when it has shipped, and the rule exists to catch exactly that. What is wrong is WHO PAYS: the plan author wrote a correct row, the row became stale through the SUCCESS of the dependency the runner itself enforced, and the cost lands on the executor as a hand-edit of a row unrelated to its own work, at the pre-transition checkpoint, where an executor under time pressure is most likely to reach for the blunt escape ('- Carrier-Declined:') rather than the honest one.

WHY THIS IS A GENERAL SHAPE AND NOT ONE PLAN'S BAD LUCK: any Set that splits complementary work across siblings and declares 'Item-Dependencies: executed:<sibling>' produces it BY CONSTRUCTION. The later plan must defer the earlier plan's scope (that is what makes them separable), must name it as a carrier (the rule requires a carrier), and must run only after that carrier is terminal (the dependency edge requires it). So the three rules compose into a guaranteed refusal for the dependent plan. Every future ordered Set will hit it.

WHAT I DID IN n9na1c, so a fix can be judged against a worked case: replaced '- Carrier: fuk1mr' with '- Carrier-Evidence: <path to the executed tgyfs2 plan>' plus a '- Carrier-Note:' recording why the field changed at execution. That is the SATISFIED escape the predicate already offers (evaluate_carrier_obligation), it resolves in-tree, and it is more honest than the original row because the obligation really is discharged. It is a hand-edit at the gate, which is the cost this item is about.

OPTIONS A FIX MIGHT TAKE, none chosen here because the design is the maintainer's call: (1) teach evaluate_carrier_obligation that a carrier resolving to a DONE backlog item or an EXECUTED plan is SATISFIED rather than uncarried, treating discharge as success and not as a dangling reference - note this weakens the rule's ability to catch a genuinely abandoned row, so it likely needs to distinguish 'terminal because finished' from 'terminal because dropped'; (2) leave the predicate alone and have 'aw ipd' offer a verb that rewrites a discharged carrier into cited evidence, so the executor is not hand-editing prose at a gate; (3) accept it as intended friction and say so in the plans README, so an executor knows the expected remedy is Carrier-Evidence and NOT Carrier-Declined. Option (3) is the cheapest and is worth doing regardless of the others, because the failure mode this item most wants to prevent is an executor reaching for Carrier-Declined on a row that has a perfectly good evidence citation available.

NOT A BUG, deliberately filed as a chore: no wrong answer is produced and nothing user-facing is slow. The gate refuses correctly on the state it sees; the defect is ergonomic and structural.
