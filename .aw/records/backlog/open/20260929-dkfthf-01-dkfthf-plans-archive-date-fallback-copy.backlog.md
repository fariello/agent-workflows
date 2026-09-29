- Id: dkfthf
- Status: open
- Blocks-Release: next
- Set: dkfthf
- Priority: medium
- Work-Kind: bug
- Summary: plans_archive._plan_date is a second copy of the 20260101 fabricating fallback, so a plan with no usable - Date: shards to the wrong week and ages about nine months early

## Workflow history
- 2026-09-29 created (aw backlog): Filed while authoring plan 949enf (graduating j84jg3): the deferred half of that plan's fence, filed with its measurement rather than left as prose.

MEASURED WHILE AUTHORING PLAN 949enf, which fixes the SAME fabricating fallback in `plans_refs` and deliberately leaves this second copy alone (949enf OQ-02).

THE DEFECT. `plans_archive._plan_date` is its own copy of `plans_refs._plan_date`: it reads the front-matter `- Date:` ONLY, and its no-match branch returns the literal string `20260101` rather than failing or consulting the filename. Measured: `plans_archive._plan_date('- Id: abc123\n')` -> `20260101`. Fixing `plans_refs` does NOT fix this, because the two functions are separate definitions with no shared helper.

WHY IT MATTERS (this is the harm 949enf's fix does NOT reach). The fabricated date is load-bearing at TWO sites in this module. (1) SHARD PLACEMENT: `_shard_target` files a terminal plan under `_core.shard_for_date(plan_date)`, and `shard_for_date('20260101')` is `202601` against `202607` for a real July date, so the plan is shelved into the wrong weekly shard. (2) SWEEP AGE: `sweep_candidates` ages a plan through `_age_days`, so a `20260101` stamp makes an artifact look roughly nine months older than it is and become sweep-eligible early.

THE MALFORMED CASE IS WORSE THAN THE ABSENT ONE and reaches this code with nothing flagging it: the regex is anchored `^- Date:\s*(\d{8}|\d{4}-\d{2}-\d{2})\s*$`, so a real in-tree string like `- Date: 2026-07-23 (fleshed 2026-07-26 from research)` yields `20260101`, and `aw ipd lint` raises `IPD-M101` only when the field is ABSENT, so a malformed line lints clean.

THE FIX SHAPE is whatever 949enf lands in `plans_refs` (tiers: clustered filename, legacy `YYYYMMDD-HHMM-NN` filename, then front matter), applied here or shared. Deciding whether the ARCHIVE verb should consult a filename at all is the open question, and is why this was not bundled: it is a different moment (shelving a terminal plan) with a different blast radius from what a RENAME writes.
