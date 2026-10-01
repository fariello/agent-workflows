- Id: aaa2xx
- Status: graduated
- Graduated-To: strandhead
- Blocks-Release: next
- Set: strandhead
- Priority: medium
- Work-Kind: bug
- Summary: A stranded REVIEW prints a COMPLETED headline above its own stranded-work recovery section

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: w5uowt
- 2026-09-29 created (aw backlog): Filed by plan entv1d (Set strandexit) as its OQ-01, deferred NON-BLOCKING. MEASURED 2026-09-29: render_stream.review_integration_was_refused (added by plan i4ak5n for the review integration ladder) has exactly ONE consumer, render_stream.format_stranded_work_section, and is NOT in the outcome-word ladder in render_run_summary_table. Only the EXECUTE-shaped predicate integration_was_refused reaches the STRANDED branch. CONSEQUENCE: a review item carrying review_integrated: False prints a green COMPLETED headline DIRECTLY ABOVE a 'STRANDED WORK - NOT IN YOUR PROJECT:' section that names the branch its work is sitting on. That is a self-contradicting screen, and the COMPLETED half is the one a tired human believes. WHAT entv1d DOES AND DOES NOT FIX: entv1d makes the review shape count for the process EXIT CODE (its E-02 composes both predicates into one question, and its E-05 case (b) pins the review shape exiting nonzero), so after entv1d the machine-readable signal is honest for BOTH shapes. This item is the HUMAN-READABLE half only. WHY IT WAS DEFERRED RATHER THAN RIDDEN ALONG: the outcome-word ladder's branch precedence is load-bearing and heavily commented, and ys1dor's review measured the specific near-miss - testing the integration signal BEFORE the status would have relabelled the existing FAILED outcome for an integration-blocked item, which that review called 'a regression dressed as the feature'. Reordering that ladder needs its own fence and its own review. LIKELY FIX: add the review shape to the STRANDED branch's condition and to the COMPLETED branch's guard, keeping the branch ORDER unchanged, then extend tests/test_run_summary_table.py and tests/test_zero_dispatch_outcome.py with a review-shaped case. Verify the FAILED and BLOCKED branches still win for the statuses they own.
