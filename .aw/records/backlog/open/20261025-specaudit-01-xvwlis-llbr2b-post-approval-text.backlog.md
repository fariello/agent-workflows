- Id: xvwlis
- Status: open
- Set: specaudit
- Priority: low
- Work-Kind: chore
- Summary: Refresh spec llbr2b text after approval (stale 'not yet approved' and open OQ-03/05/06)

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Spec llbr2b (approved 2026-10-24) still says in Section 5.6 'THIS TABLE IS WHY THE SPEC IS NOT YET approved', and Sections 5.1, 5.5 and 5.7 list OQ-03, OQ-05 and OQ-06 as open although 5.7 says approval closes them. None of the policy engine (policy.lifecycle.allow_auto_transitions, PERMIT/REFUSE/PERMIT-WITH-ATTESTATION predicate, widened TRANSITION_AUTHORITY) is built and no plan graduates from it. Refresh the text, then author the implementing plan Set.
