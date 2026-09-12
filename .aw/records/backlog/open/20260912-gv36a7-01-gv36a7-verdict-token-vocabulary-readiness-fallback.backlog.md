- Id: gv36a7
- Status: open
- Blocks-Release: next
- Set: gv36a7
- Priority: medium
- Work-Kind: bug
- Summary: newest_verdict misreads a review record as NEGATIVE when its verdict token is outside VERDICTS and its prose narrates a no-go readiness

## Workflow history
- 2026-09-12 created (aw backlog): newest_verdict misreads a review record as NEGATIVE when its verdict token is outside VERDICTS and its prose narrates a no-go readiness

## How this was found

Hit LIVE on 2026-09-12 while running `/plan-review` round 3 on plan `826o13`. The review's own history
record was written as `REVIEWED - REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL; ...` and the gate then
read the plan as carrying a NEGATIVE verdict, which would have blocked the approval the review had just
cleared. Caught only because the reviewer re-ran the predicates after writing the record instead of
trusting the write. An agent that wrote that line and stopped would have left the plan silently refused.

## The defect, measured at HEAD 2026-09-12

TWO MECHANISMS COMPOSE, and neither is wrong alone.

FIRST, THE VERDICT VOCABULARY IS CLOSED AND SMALL. `plan_readiness.VERDICTS` recognizes exactly four
tokens: `APPROVE`, `APPROVE WITH REVISIONS APPLIED`, `REVIEWED - OPEN QUESTIONS`, `REJECT - NEEDS REPLAN`.
`classify_verdict` scans with `_VERDICT_SCAN_RE` and returns `(None, None)` for anything else. The
workflow prose in `.aw/system/workflows/plan-review/plan-review.md` also uses READINESS words (`GO`,
`GO - PENDING HUMAN APPROVAL`, `NO-GO`) in its own reporting vocabulary, so a reviewer composing a
history line naturally reaches for a phrase that is NOT in `VERDICTS`.

SECOND, THE FALLBACK THEN TREATS NARRATION AS A VERDICT. When `classify_verdict` finds no token,
`newest_verdict` falls through to `_NEGATIVE_READINESS_SCAN_RE` on the SAME message, on the documented
premise that a negative readiness token "is unambiguous precisely BECAUSE no verdict competes with it for
the reader's attention". That premise fails for a record that MENTIONS the readiness it moved AWAY from.
Reproduced:

    msg = 'REVIEWED - REVISIONS APPLIED; readiness advanced from no-go'
    classify_verdict(msg)                        -> (None, None)
    _NEGATIVE_READINESS_SCAN_RE.search(msg)      -> truthy
    newest_verdict(...)                          -> NEGATIVE

BLAST RADIUS IS LATENT BUT LARGE. Scanned every `.ipd.md` under `.aw/records/plans/`: 40 plans whose
NEWEST review record states NO recognized verdict token, so all 40 currently rely on the fallback rather
than on a parsed verdict. Today ZERO of those 40 are misread as negative, because none happens to mention
a negative readiness in the same line. That is luck, not a control: any of those 40 records could be
rewritten to narrate a readiness change and would flip to NEGATIVE. This item is filed at the moment the
combination was OBSERVED rather than waiting for a second occurrence.

## Scope

1. Make the fallback refuse to fire when the record states a POSITIVE outcome, or drop the readiness
   fallback entirely in favor of the structured `- Readiness:` field (which `approval_refusals` already
   consults FIRST and which is the documented machine signal).
2. Decide and record whether `VERDICTS` should recognize the readiness-style phrasings the workflow's own
   reporting vocabulary uses. If not, the workflow MUST say plainly that a history line carries a verdict
   token from the closed set and that readiness words do not belong in it.
3. Add a test that a review record narrating a readiness change is NOT read as a negative verdict.

DO NOT fix this by making the readiness fallback smarter about word order. The reliable signal already
exists as a typed field; a prose scanner competing with it is the underlying design problem, which is the
same conclusion `ycg597` reaches from a different direction.

## Related, and deliberately not merged

`ycg597` is the THIRD way this scanner misfires (a tooled `aw set` bookkeeping line shadowing a real
review record) and is filed separately because its fix is in `is_review_history_entry`, the record-KIND
discriminator, whereas this item's fix is in `classify_verdict`/the readiness fallback, the verdict-VALUE
reader. Whoever graduates either should read the other; they may well share one plan.
