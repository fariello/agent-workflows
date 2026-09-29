- Id: t1gbwg
- Status: open
- Set: backlogtrans
- Priority: medium
- Work-Kind: chore
- Summary: Give backlog items a transition table so an illegal backlog status move fails closed like a spec or plan move

## Workflow history
- 2026-09-29 created (aw backlog): Give backlog items a transition table so an illegal backlog status move fails closed like a spec or plan move

Split out of plan nvsz19 (Set ipdsetback), which closes the same hole for PLANS. MEASURED 2026-09-29: neither backlog set code path validates a transition. status_set.validate_transition_allowed only vocabulary-checks a backlog target (plus requiring --gate-kind/--gate-ref for ->blocked), and the forked backlog.run_set only checks 'new_status not in STATUSES'. There is no BACKLOG_TRANSITIONS constant anywhere in the package, so any backlog status may move to any other, including done -> open or graduated -> open.

CONTRAST WITH THE TWO TYPES THAT DO GATE: specs consult the shared attention_contract.SPEC_TRANSITIONS table via attention_contract.transition_allowed from BOTH spellings, and plans will consult ipd_lifecycle.validate_transition once nvsz19 lands.

WHY IT IS SEPARATE AND NOT FOLDED INTO nvsz19: plans already HAVE a correct predicate that the setter merely fails to call, so that fix is a delegation. Backlog has no predicate and no defined status order at all, so this needs the vocabulary DESIGNED first (which moves are legal, whether a reopen of a done item is legitimate, how the existing release-gate close rules in evaluate_blocking_close compose with it). That is a design decision, not a wiring fix.

NOT FILED AS A BUG because no measured harm is recorded yet: unlike the plan case (where an illegal move relocates a committed record between disposition directories), backlog items are not moved between lifecycle directories by status alone. Reclassify if a concrete falsification is measured.
