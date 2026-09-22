- Id: 0kdwm3
- Status: open
- Set: 0kdwm3
- Priority: low
- Work-Kind: followup
- Summary: Plan 65cuw0's V-03 wording requires a gitignored file to refuse lane teardown, contradicting the 2026-09-18 amendment to spec 7ckptx R5.5

## Workflow history
- 2026-09-22 created (aw backlog): Plan 65cuw0's V-03 wording requires a gitignored file to refuse lane teardown, contradicting the 2026-09-18 amendment to spec 7ckptx R5.5

FOUND 2026-09-22 while executing plan 65cuw0 (laneorph Order 01).

WHAT IS WRONG: plan 65cuw0's E-04 and V-03 both require that an interrupted merged lane whose only
unexplained content is a GITIGNORED file be PRESERVED, with reason code 'unknown-ignored-file' pasted as
evidence. Spec 7ckptx R5.5 was AMENDED on 2026-09-18 - by that plan's own declared dependency laneign
5w8g8j - to make gitignored content DISPOSABLE upon lane destruction, and
lane_containment.RETENTION_UNKNOWN_IGNORED is documented as 'NEVER EMITTED BY reason_codes NOW,
deliberately'. So the plan's requirement cannot be satisfied without forking R5.5.

WHERE: .aw/records/plans/executed/...-65cuw0-...ipd.md (E-04, V-03, and the Approval-and-execution-gate
paragraph); .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md R5.5.

MEASURED, so the contradiction is not inferred:

    MERGED lane with ignored    unexplained content -> classified=True  unknown_ignored=('build/precious.txt',) reason_codes=()
    MERGED lane with untracked  unexplained content -> classified=False unknown_untracked=('unexplained.txt',)  reason_codes=('unknown-untracked-file',)

HOW IT WAS HANDLED: the executor complied with the amended SPEC rather than the plan's letter, and
recorded the reasoning as decision 08-65cuw0-D3 with human review requested. The hazard the requirement
exists for is fully covered and pinned by two tests in tests/test_worktree_lease_merged_reclaim.py: a
merged lane holding an unaccounted UNTRACKED file is preserved (the wfamig hazard class), and a merged
lane with no collection receipt is preserved with its reason codes. No spec was edited and no existing
test was weakened.

WHY THIS ITEM EXISTS: the plan is now executed with a V-03 whose WORDING does not match what was built,
and a later reader comparing the two would reasonably conclude the plan was under-delivered. This is a
RECORD-CORRECTION follow-up: either annotate the executed plan's V-03 to cite the amendment, or - if the
maintainer prefers the pre-amendment rule on the interrupt path specifically - open a plan to amend R5.5
deliberately, which is the only legitimate route to it.

NOT A BUG: nothing behaves incorrectly; the shipped behavior matches the approved spec.
