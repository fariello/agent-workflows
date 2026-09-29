- Id: 5h8u3z
- Status: open
- Blocks-Release: next
- Set: 5h8u3z
- Priority: medium
- Work-Kind: bug
- Summary: A malformed - Date: in a plan escapes aw ipd lint entirely, because IPD-M101 fires only on an absent field, so the value that reaches the date fabricator is never flagged

## Workflow history
- 2026-09-29 created (aw backlog): Filed while authoring plan 949enf (graduating j84jg3): the lint-side half of the same defect, measured and filed because the executed k9awrq explicitly excluded rule changes and so cannot own it.

MEASURED WHILE AUTHORING PLAN 949enf, which fixes the rename-side date fabrication and deliberately excludes every checker change.

THE DEFECT. `- Date:` IS a required field (`ipd_schema.META_REQUIRED` contains `Date`), and `aw ipd lint` raises `IPD-M101` when it is ABSENT. It raises NOTHING when the field is PRESENT BUT UNPARSEABLE. Measured on a minimal plan carrying `- Date: 2026-07-23 (fleshed later)`: `aw ipd lint` output contains no `M101` and no `Date` complaint at all, while the same plan with the line DELETED yields `! IPD-M101: Date: required field missing`.

WHY THAT IS THE DANGEROUS DIRECTION. The date consumers parse with an ANCHORED regex, `^- Date:\s*(\d{8}|\d{4}-\d{2}-\d{2})\s*$`, and FABRICATE the literal `20260101` on no-match (`plans_refs._plan_date`, `plans_archive._plan_date`). So a malformed line is treated EXACTLY like an absent one by every consumer, while being invisible to the one tool that would have told the author. Measured: `2026-07-23 (fleshed 2026-07-26 from research)` -> `20260101`, and `2026-7-23` (a plausible hand-typed shape) -> `20260101`.

IT IS NOT HYPOTHETICAL: `.aw/records/plans/executed/20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` carries exactly that malformed line, and its filename now records the fabricated `20260101` instead of its real `20260723` (that casualty is filed separately as tf4jz5).

WHY k9awrq DOES NOT OWN THIS. `k9awrq` made the `IPD-*` family REACHABLE from `aw check plans`, which is a different axis; its Scope explicitly EXCLUDES "any change to lint RULES themselves" and "any change to what `aw ipd lint` reports per file". Reachability does not help when no rule fires.

THE FIX SHAPE. Either extend `IPD-M101` (or add a sibling code) to flag a required field whose VALUE does not parse, or validate `- Date:` against the same anchored pattern the consumers use, so the linter and the consumers agree on what counts as a date. Note the second, wider question this exposes and does not answer: a wrong or fabricated filename DATE is also unreported by `aw check plans` (measured: rc 0, `CONFORMS`, no date finding, on a plan whose filename says `20260101` while nothing else does).
