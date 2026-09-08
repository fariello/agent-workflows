- Id: qzhfk2
- Status: graduated
- Set: specsubdirs
- Priority: medium
- Work-Kind: chore
- Summary: Should specs get lifecycle subdirs? 24 specs sit intermixed in a flat tree while carrying a real 6-state lifecycle, 16 of them terminal

## Workflow history
- 2026-09-08 graduated (aw set): DECIDED YES by maintainer ruling 2026-09-08 and graduated to the specdirs Set: wfjsp4 (Order 0), y4bdoz (01, make spec readers recursive), 1bdxcp (02, migrate and make location agree with status). THE RULING: humans and to a lesser extent agents use the HIERARCHY to see what is pending and browse what needs to happen, so a lifecycle-bearing type that does not partition on status fails the surface the hierarchy exists for. An agent recommendation to PARK was overruled, and the measurements supported the ruling. THREE MEASUREMENTS DECIDED IT: specs are the ONLY lifecycle-bearing type not partitioned (plans/backlog/prompts have 5 subdirs each, specs 0) while every FLAT type is flat because it lacks a lifecycle (roadmaps 0 of 1 files carry a Status, reviews 1 of 81, walkthroughs 2 of 17, releases a single record); the live set GREW from this item's 8 to 12 of 28 while terminal held at 16, so a flat listing is getting noisier; and finding those twelve required a scripted loop over every file. TWO THINGS THIS ITEM DID NOT KNOW, both reshaping the work: this item's cost estimate is INVERTED, since check_engine._iter_type_files is already recursive while specs._spec_files is NOT (specs.py:89), and a spec placed in a subdir made aw specs check print 'all specs conform' over ZERO files examined (proven in a throwaway repo) - a latent bug today and the reason Order 01 must precede the migration; and aw specs set does NOT move files (specs.py:498) while aw backlog set does (backlog.py:534), so without teaching the setter to relocate the invariant would be decorative. The item's counter-argument (location-must-agree-with-status becomes load-bearing) is ACCEPTED as a cost, with the severity question left open as the orchestrator's OQ-03. The instruction not to bundle the reviews question is honored: sv0sf3 is parked separately. No Blocks-Release on this item, so no plan inherits one.
- 2026-08-29 created (aw backlog): Should specs get lifecycle subdirs? 24 specs sit intermixed in a flat tree while carrying a real 6-state lifecycle, 16 of them terminal

DECIDED YES 2026-09-08 BY MAINTAINER RULING, and graduated to the `specdirs` Set: `wfjsp4` (Order 0,
orchestrator), `y4bdoz` (01, make the readers recursive), `1bdxcp` (02, migrate and make location agree
with status).

THE RULING, recorded because it resolves this item's central open question: humans and to a lesser extent
agents USE THE HIERARCHY to see what is pending and to browse what needs to happen, so a lifecycle-bearing
type that does not partition on status is failing the surface the hierarchy exists to serve. An agent
recommendation to PARK this item was overruled, and the measurements then supported the ruling rather than
the recommendation.

THREE MEASUREMENTS DECIDED IT, all at HEAD 2026-09-08. (1) SPECS ARE THE ONLY OUTLIER: across all ten
records trees, `plans` has 5 subdirs, `backlog` 5, `prompts` 5, `research` 5 (ad hoc groupings), `comms` 1,
and `specs` ZERO, while every FLAT type is flat because it has no lifecycle to partition on: `roadmaps`
carries `- Status:` on 0 of 1 files, `reviews` on 1 of 81, `walkthroughs` on 2 of 17, and `releases` is a
single record. So the flatness here is an inconsistency, not a design. (2) THE DISTRIBUTION MOVED THE WRONG
WAY for the flat tree: this item measured 24 specs with 16 terminal (8 live); HEAD has 28 specs with 16
terminal, so terminal held flat while the LIVE set grew from 8 to 12, and the signal-to-noise of a flat
listing is worsening. (3) THE COST IS REAL AND MEASURED: `ls .aw/records/specs/` prints 28 date-prefixed
filenames and reveals nothing about state, and finding the twelve live specs (6 `approved`, 2 `draft`,
1 `implementing`, 1 `to-review`, 2 `deferred`) required a scripted loop over every file.

A DEFECT THIS ITEM DID NOT KNOW ABOUT, and it inverts this item's cost estimate. The item names "the shared
recursive type scanner in check_engine.py" as part of the migration cost, implying that scanner is the work.
The opposite is true: `check_engine._iter_type_files` is ALREADY recursive (`rglob`), while
`specs._spec_files` is NOT (`glob("*.md")`, `specs.py:89`). PROVEN in a throwaway repo: a spec placed in
`.aw/records/specs/approved/` made `aw specs check` print `all specs conform` while `specs._spec_files`
returned ZERO files and `check_engine._iter_type_files` returned ONE. That is a LATENT BUG TODAY (any
subdirectory anyone creates already hides specs from their own checker) and it is why the Set has two
children: migrating first would have produced a tree whose validator reported success having read nothing.

A SECOND THING THIS ITEM DID NOT KNOW: `aw specs set` does NOT move files (`specs.py:498`) while its sibling
`aw backlog set` DOES (`backlog.py:534`, "move file to the new status dir"). Without teaching the setter to
relocate, the invariant would be decorative and the tree would drift on its very next transition. That is
Order 02's E-03.

THIS ITEM'S COUNTER-ARGUMENT IS ACCEPTED AS A COST, NOT DISMISSED: subdirs promote "location must agree with
status" from NOT APPLICABLE to LOAD-BEARING for this tree, which is the invariant that generates the
artifact/status discrepancy class for plans. The maintainer accepted that trade because it is the same one
already accepted for plans, backlog and prompts, and because the browse affordance is what the hierarchy is
for. Whether `aw check` should ERROR on a violation is deliberately left open as the orchestrator's OQ-03.

THE ITEM'S INSTRUCTION NOT TO BUNDLE THE REVIEWS QUESTION IS HONORED: `sv0sf3` is being PARKED separately,
not folded in. Its own premise is independently falsified (80 of 81 reviews are `Subject-Type: ipd`).

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
