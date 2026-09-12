- Id: nwrb0j
- Status: open
- Blocks-Release: next
- Set: nwrb0j
- Priority: medium
- Work-Kind: bug
- Summary: A non-review history record labelled with a review word is read as a review verdict, so a descope or re-check narrating no-go negates its own plan

## Workflow history
- 2026-09-12 created (aw backlog): A non-review history record labelled with a review word is read as a review verdict, so a descope or re-check narrating no-go negates its own plan

## How this was found

Hit LIVE on 2026-09-12. Recording a maintainer-ordered DESCOPE of plan `826o13`, the agent wrote the
history record with the status label `reviewed` (the plan's `- Status:` was `reviewed`, so the label
looked correct) and narrated inside it that readiness stayed `no-go`. That record then became the plan's
newest REVIEW record and its narration was parsed as a fresh NEGATIVE verdict, which broke a shipped test:

    FAILED tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::
           test_no_pending_plan_is_refused_on_a_verdict_today

Relabelling the record `re-scope` fixed it. The suite caught this one; nothing else would have.

## The defect, measured at HEAD 2026-09-12

`plan_readiness.is_review_history_entry` decides a record IS a review record by scanning its MIDDLE field
for a review word (`_REVIEW_WORDS` = {review, re-review, re-reviewed, reviewed}, or a `/plan-review`
prefix). The middle field of a history record is conventionally the plan's STATUS, not a claim about what
the record did. So any record written while the plan sits at `Status: reviewed`, and labelled accordingly,
is indistinguishable from a review's own verdict record.

    - 2026-09-11 reviewed (agent/model): <a descope, a re-check, or any other non-review act>
                 ^^^^^^^^ read as "this record states a review verdict"

`newest_verdict` consults only the NEWEST such record, so the mislabeled record SHADOWS the real review
(the `ycg597` failure) and, if its prose mentions a negative readiness, is additionally read as stating a
negative verdict itself (the `gv36a7` failure). Both fire from one mislabeling.

THE TRAP IS THAT THE CORRECT LABEL IS UNDOCUMENTED. `aw ipd set` writes the status as the label for tooled
transitions, and the plan-review workflow specifies `- <date> /plan-review (<agent/model>): <verdict>` for
a review. Nothing states what an agent should write for a legitimate non-review act that does not change
status: a descope, a readiness re-check, an OQ answer being recorded, a scope correction. `qhy3i3` E-03
independently discovered the same hazard from the re-check side and works around it by FORBIDDING verdict
tokens in a re-check entry, which treats the symptom while leaving the label ambiguous.

## Scope

1. Define and document the label vocabulary for a non-review history record, so an agent has a correct
   choice instead of defaulting to the status word. Candidates observed in use: `re-scope`,
   `readiness re-check`, plus the tooled `(aw set)` form.
2. Make the discriminator distinguish a record's ACT from the plan's STATUS. The actor field already
   separates tooled writes (`(aw set)`) from agent writes, and a genuine review record carries a verdict
   token from the closed set; either is a stronger signal than the status label.
3. Add a test that a non-review record labelled with a review word does not shadow, and is not read as,
   a review verdict.

## Related, and deliberately not merged

Three items now describe this one scanner from three angles: `ycg597` (a TOOLED line shadows a review),
`gv36a7` (an out-of-vocabulary verdict token plus a readiness-narrating fallback yields a false NEGATIVE),
and this item (a review-WORD label on a non-review act makes the record a verdict carrier at all). They
are filed separately because each has a distinct fix site, and merged reporting would hide that the
gate has three independent ways to read a verdict that nobody stated. A single plan graduating all three
would be reasonable and probably preferable; whoever takes one should read the other two.
