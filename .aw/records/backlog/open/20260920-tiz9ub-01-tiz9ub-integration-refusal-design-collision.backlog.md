- Id: tiz9ub
- Status: open
- Blocks-Release: next
- Set: tiz9ub
- Priority: high
- Work-Kind: bug
- Summary: Two maintainer rulings on the same integration-refusal defect produced two competing designs: approved plan daexj1 (three sentinels, 2026-09-08) versus shipped gateanswer vocabulary plus plan h5pyqa (four answers, 2026-09-19)

## Workflow history
- 2026-09-20 created (aw backlog): Filed while executing daexj1. daexj1 E-05 demands three EXACT sentinels (SAFE TO IGNORE./RETRY TESTS./UNABLE TO FIX.) as a parsing contract; a grep returns ZERO matches. The shipped equivalent is GATE_ANSWERS (not-mine/fixed/mine/needs-human) at runner_shared.py:11482-11750 from commit 2cfcf061, and its wiring is authored as h5pyqa (Set gatewire, to-review). Executing daexj1 as written would fork a second sentinel parser for one decision, which daexj1's own E-09 forbids by name. Needs a human ruling on which plan owns the escalation.
