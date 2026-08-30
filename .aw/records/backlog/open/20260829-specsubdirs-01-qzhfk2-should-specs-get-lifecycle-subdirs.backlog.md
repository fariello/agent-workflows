- Id: qzhfk2
- Status: open
- Set: specsubdirs
- Priority: medium
- Kind: chore
- Summary: Should specs get lifecycle subdirs? 24 specs sit intermixed in a flat tree while carrying a real 6-state lifecycle, 16 of them terminal

## Workflow history
- 2026-08-29 created (aw backlog): Should specs get lifecycle subdirs? 24 specs sit intermixed in a flat tree while carrying a real 6-state lifecycle, 16 of them terminal

QUESTION (not yet a decision): .aw/records/specs/ is FLAT, but specs carry a genuine lifecycle and the
statuses are in live use. Measured 2026-08-29 across 24 spec files (first '- Status:' bullet per file):

    15  implemented
     3  approved
     2  draft
     2  deferred
     1  to-review
     1  superseded

So 16 of 24 are effectively terminal ('implemented' + 'superseded') and sit intermixed with the 8 live
ones. plans/ and backlog/ both solve this with status subdirs (5 each), and the machinery already
exists: 'aw specs set' owns transitions and 'aw archive' owns deep-shelving.

FOR: browsing live vs terminal specs becomes trivial; consistent with plans/backlog; terminal specs stop
competing for attention with active ones.

AGAINST (the real cost, and why this is a question not a task): moving specs into subdirs promotes
'location must agree with status' from NOT APPLICABLE to LOAD-BEARING for this tree. That is exactly the
invariant that generates the artifact/status discrepancy table for plans, so it adds a new class of
possible inconsistency. It is also a real migration: 24 files, every path reference to them, plus
check_names and the shared recursive type scanner in check_engine.py (:307 rglob('*.md')).

RELATED, decided NO for now: releases/ (1 record, 3 possible statuses - subdirs would be ceremony) and
roadmaps/ (NO roadmap file carries a '- Status:' bullet at all, so there is no lifecycle to partition
on). prompt-library/ and walkthroughs/ are correctly flat: a library and append-only evidence, neither
has a lifecycle. Walkthroughs are still actively produced (6 in 202608) and set_records.py:11-20 still
requires a tracked walkthrough at Set checkpoints, so that tree is live, not vestigial.

DO NOT bundle this with the reviews-location question (separate item); entangling a specs migration with
a new artifact tree would make both harder to review.
