- Id: w51mpv
- Status: graduated
- Graduated-To: gateansrec
- Set: gateansrec
- Priority: medium
- Work-Kind: chore
- Summary: The persisted gate-answer record's 'integrates' field is False for a fixed answer that DID release, so the durable record contradicts the outcome a reader is trying to audit

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan nzznlm (Set gateansrec), re-verified live at HEAD.
- 2026-09-23 created (aw backlog): MEASURED while executing plan n9na1c on 2026-09-23, by driving the real perform_gate_answer with each of the four answer tokens and a PASSING re-run for 'fixed':

    fixed | GateAnswerOutcome.release = True | record['integrates'] = False | record['recheck_passed'] = True

So for a verified 'fixed', the lane DID integrate and the durably persisted record says 'integrates': False. Both values are individually defensible - GateAnswerOutcome.release is the field the integration decision actually reads, while record['integrates'] mirrors GateAnswerVerdict.integrates, which is a property of the TOKEN before any re-run has happened - but they are persisted side by side under names that read as synonyms, and only ONE of them is the outcome.

WHY THIS MATTERS RATHER THAN BEING A NAMING QUIBBLE. Spec 25kzda Section 5.1 makes this record the thing that MAKES the attribution exception admissible at all: 'WHAT MAKES IT ADMISSIBLE IS CAPTURED EVIDENCE, NOT PROSE', and the record is what an auditor reads afterwards to check a release was warranted. An auditor reading integration_gate_answer for a 'fixed' item sees 'integrates': False on an item that integrated. The true story is recoverable - recheck_passed is True right beside it, and attempt['integration_released_by_answer'] records the release - but it requires knowing that 'integrates' means 'this token releases on its own' and not 'this answer resulted in integration'. That is exactly the kind of reader-misleads-themselves shape that produced the c74dm7 filing this plan came from, where a correct-but-narrowly-scoped statement was read as a broader one.

I HIT IT DIRECTLY: writing a control for the 'fixed' case, I asserted on record['integrates'] expecting the gate-1 release, and the test failed. The real release is on the OUTCOME, not the record. I worked around it by having the test fixture return the whole GateAnswerOutcome and assert on outcome.release, and documented the distinction in the helper's docstring so the next reader of that file does not repeat it.

NOT A BUG: no decision is made on the misleading field (the runner reads GateAnswerOutcome.release), nothing is slow, and no outcome is wrong. It is an AUDIT-LEGIBILITY defect in a record whose entire purpose is audit.

POSSIBLE FIXES, none chosen: (1) add a 'released' field recording what actually happened, leaving 'integrates' as the token property it is - most honest, purely additive, costs one key; (2) rename 'integrates' to something that cannot be read as an outcome, e.g. 'releases_on_answer_alone' - clearer but changes a persisted key, so any existing reader and any state.json corpus would need to tolerate both; (3) document it in gate_answer_record's docstring only - cheapest, and worth doing regardless, since that docstring already declares itself the contract a consumer codes against.
