- Id: i4y84y
- Status: open
- Set: lanectn
- Priority: low
- Work-Kind: chore
- Summary: Spec 7ckptx R5.1a's manifest-revision vocabulary assumes a single-owner lane, but the review sweep lane has many

## Workflow history
- 2026-09-16 created (aw backlog): Spec 7ckptx R5.1a's manifest-revision vocabulary assumes a single-owner lane, but the review sweep lane has many

Found while executing plan ajxr5d (dirtygates Order 05), which isolated a review turn into ONE shared sweep lane serving every review of a run.

WHAT IS ACTUALLY WRONG: nothing behaves incorrectly, and that is why this is a chore rather than a bug. Spec 7ckptx R5.1a part (iii) requires that a change to a lane's input set be a NEW MANIFEST REVISION rather than an in-place edit of an existing entry. The review sweep lane now materializes one revision PER REVIEW, which satisfies that rule as written, and was in fact forced by it: a shared rev-1 meant review 2 overwrote review 1's manifest, leaving review 1's copied plan accounted for by nothing, so the spec-R5.5 teardown gate correctly refused ('2 unknown IGNORED file(s)') and a perfectly clean sweep could never retire its lane.

THE STRAIN: R5.1a was written for a lane with ONE owner, where 'revision N' means 'this turn's input set changed'. In the sweep lane consecutive revisions belong to DIFFERENT ITEMS, so the number now carries two meanings at once. A reader auditing a sweep lane's manifests sees rev-1, rev-2, rev-3 and cannot tell from the spec alone whether that is one turn revising its inputs three times or three turns each declaring their own.

WHY IT WAS NOT AMENDED IN ajxr5d: changing what that requirement MEANS is a contract change, and that plan's mandate was to isolate a review turn, not to redefine a containment requirement. The behavior is conforming and the failure mode is closed, so this is documentation precision rather than a defect.

SUGGESTED SHAPE: either state in R5.1a that a revision is scoped to the (lane, turn) pair and that a shared lane therefore holds one revision per turn, or introduce an explicit per-turn key so the two meanings are not carried by one integer.
