- Id: rv2ccz
- Status: open
- Blocks-Release: next
- Set: rv2ccz
- Priority: medium
- Work-Kind: bug
- Summary: plan u23gbn's V-02 demands a landed-commit-plus-refused-reconciliation state that its own E-06 correction makes impossible, so the V-item text is internally contradictory

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): plan u23gbn's V-02 demands a landed-commit-plus-refused-reconciliation state that its own E-06 correction makes impossible, so the V-item text is internally contradictory

FOUND while executing plan u23gbn (dirtygates Order 04). A DOCUMENT defect, not a code defect, filed so the contradiction is not rediscovered by whoever reviews the executed plan.

WHAT IS WRONG. u23gbn's V-02 requires evidence of "a retirement whose commit landed but whose reconciliation refused, showing the journal phase is PHASE_COMMITTED_INCOMPLETE". That state CANNOT EXIST in the ordering the same plan mandates: F-10 established that the ff-only merge must BE the branch advance, so a refusal leaves the commit unreachable from the branch and nothing is landed. The plan says so twice elsewhere, in E-06's own bullet ("a refusal leaves the commit UNREACHABLE FROM main ... so it is NOT PHASE_COMMITTED_INCOMPLETE") and in V-06's third bullet. V-02 is the stale wording, written while the CAS-then-reconcile ordering was still assumed, and review round 3 corrected its siblings without correcting it.

HOW IT WAS HANDLED at execution, since a V-item cannot simply be skipped: V-02 was answered by reporting the demand as unsatisfiable BY CONSTRUCTION with the measurement that proves it (`git merge-base --is-ancestor <landed> HEAD` nonzero on the contended arm), and by evidencing the committed-incomplete case that DOES exist in this ordering (the post-commit plans-index refresh failure, E-07). Every other part of V-02 (crash recovery, the layer docstring) was satisfied normally.

WHY IT IS WORTH A CARRIER. The next reader of the executed plan sees a V-item whose literal demand was not met, and needs the reason to be findable rather than buried in the evidence block. It is also a small process signal: a review round that corrects an ordering must sweep every V-item that quotes the old one.

WHERE: `.aw/records/plans/*/20260913-dirtygates-04-u23gbn-*.ipd.md`, V-02.
