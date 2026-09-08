- Id: sv0sf3
- Status: parked
- Set: reviewloc
- Priority: medium
- Work-Kind: chore
- Summary: Should review artifacts move from a flat .aw/records/reviews/ to per-type .aw/records/<type>/reviews/?

## Workflow history
- 2026-09-08 parked (aw set): PARKED: the deciding premise is FALSIFIED and the item's own revisit conditions were tested, not assumed. It argues 'reviews already span four record types today, so this is not a plans-only question'; measured across all 81 review files by Subject-Type, EIGHTY are ipd and exactly ONE is spec, with zero research and zero roadmaps. So per-type subdirs would create one directory of 80 and one of 1, delivering no partitioning benefit. Its revisit condition is a CONJUNCTION ('numerous AND usually browsed per-type'): numerous is true (81 versus a handful at filing), usually-browsed-per-type is false and cannot become true while 98.8 percent share one type. Its third trigger (specs gain subdirs) is now in flight via qzhfk2's specdirs Set but unexecuted, and crucially it argues AGAINST rather than for: this item's own third objection is that a non-status subdirectory beside status directories overloads the convention the tooling depends on, so once specs/approved and specs/draft exist, a specs/reviews sibling is exactly the muddying it warned about. The structural cost is unchanged: check_engine._type_dirs plus rglob walks each type recursively, so a nested reviews/ dir has every .review.md scanned AS the parent type, requiring an edit to a scanner all ten types depend on. Revival needs reviews becoming genuinely multi-type AND a demonstrated per-type browse habit; access is still by id6 or aw reviews. No Blocks-Release on this item, so no gate is affected.
- 2026-08-29 created (aw backlog): Should review artifacts move from a flat .aw/records/reviews/ to per-type .aw/records/<type>/reviews/?

PARKED 2026-09-08: THE DECIDING PREMISE IS FALSIFIED, and the item's own revisit conditions were tested
rather than assumed. NOT graduated. Nothing here is lost; the analysis stands and the item revives if its
trigger genuinely fires.

THE PREMISE THAT FAILED IS THE ONE THIS ITEM CALLS DECIDING FOR SCOPE. It states "Reviews already span four
record types today (plans, specs, research, roadmaps), so this is not a plans-only question." MEASURED at
HEAD across all 81 review files by `- Subject-Type:`: **80 are `ipd` and exactly 1 is `spec`.** Zero
research, zero roadmaps. So per-type subdirectories would create one directory holding 80 files and another
holding 1, which delivers no partitioning benefit and adds a tree level for a single outlier. This is
genuinely a plans-only question today.

THE ITEM'S OWN "REVISIT IF" CONDITIONS, TESTED ONE BY ONE. It says revisit "if reviews become numerous AND
are usually browsed per-type, or if specs gain lifecycle subdirs (qzhfk2)". (1) NUMEROUS: TRUE, 81 files
against a handful at filing. (2) USUALLY BROWSED PER-TYPE: FALSE, and it cannot become true while 98.8
percent of reviews share one type. The condition is a conjunction, so it is not met. (3) SPECS GAIN SUBDIRS:
this is now IN FLIGHT rather than done. `qzhfk2` was decided YES on 2026-09-08 and graduated to the
`specdirs` Set (`wfjsp4`/`y4bdoz`/`1bdxcp`), but none of it has executed, so the trigger has not fired yet.

WHY THAT THIRD CONDITION STILL DOES NOT ARGUE FOR ACTING NOW, and it is worth stating precisely because it
is about to change. This item's THIRD objection was that in `plans/` and `backlog/` a subdirectory MEANS
status, so a non-status `reviews/` sibling would overload a convention the tooling depends on. Once
`specdirs` executes, that objection gets STRONGER for specs too, not weaker: a `specs/reviews/` directory
would then sit beside `specs/approved/`, `specs/draft/` and the rest, which is exactly the
convention-muddying this item warned about for plans. So specs gaining subdirs makes the per-type layout
LESS attractive, not more, which is the opposite of what the revisit condition anticipated.

THE STRUCTURAL COST IS UNCHANGED AND STILL REAL: `check_engine._type_dirs` plus `rglob('*.md')` walks each
type's tree recursively and skips only README/INDEX/STATUS, so a nested `reviews/` directory has every
`.review.md` scanned AS that parent type and name-checked against that type's facet. That still requires
editing a shared scanner all ten record types depend on. Re-measured tree shapes at HEAD: NESTED are `plans`
5, `backlog` 5, `prompts` 5, `research` 5, `comms` 1; FLAT are `specs` (changing), `releases`, `roadmaps`,
`walkthroughs`, `reviews`.

WHAT WOULD ACTUALLY REVIVE THIS, stated so a future reader does not re-derive it: reviews becoming
genuinely multi-type (a meaningful count of `spec`, `research` or `roadmap` subjects, not 1 of 81), AND a
demonstrated habit of browsing them per-type rather than reaching them by id6 or `aw reviews`. Note the
flat tree's locality loss is explicitly described here as "only cheap while reviews are reached by id6 or
'aw reviews' rather than by ls", and that access pattern has not changed.

THE PREFERENCE FOR FLAT WAS ASSESSED AT 65/35 AT FILING. On this evidence it is stronger now, because the
one argument that made it close (multi-type spanning) turned out not to hold.

OPEN LAYOUT QUESTION, deliberately deferred at authoring time. The revgate Set (15zvu6 Order 01)
introduces review findings artifacts. Two layouts were weighed on 2026-08-29; the maintainer chose to
START FLAT and revisit, hence this item.

CHOSEN FOR NOW: flat '.aw/records/reviews/<clustered-name>.review.md', joined to the reviewed artifact by
the id6 in the filename, and NOT moved when the reviewed artifact moves between lifecycle dirs.

ALTERNATIVE TO RECONSIDER: '.aw/records/<type>/reviews/', i.e. locality with the reviewed artifact.

WHY FLAT WON (the deciding technical fact): check_engine._type_dirs + rglob('*.md')
(check_engine.py:307) walks each record type's tree RECURSIVELY and skips only README/INDEX/STATUS
(_SKIP_NAMES, :239). A nested reviews/ dir therefore has every .review.md scanned AS that parent type and
name-checked against that type's facet, so the per-type layout REQUIRES editing that shared scanner - code
all six record types depend on.

SECOND OBJECTION (arguably the more interesting one): in plans/ and backlog/, a subdirectory MEANS status.
Adding a non-status 'reviews/' sibling there overloads a convention the tooling depends on (location must
agree with status). research/ is the counterexample - its 5 subdirs are ad hoc groupings, not statuses -
so a reviews/ dir there would be unremarkable.

THIRD: the trees have inconsistent shapes, so nested reviews/ would sit at differing depths. Measured
2026-08-29: NESTED = plans(5), backlog(5), prompts(6), research(5), comms(2); FLAT = specs, releases,
roadmaps, walkthroughs, prompt-library.

WHY IT IS STILL WORTH REVISITING: locality is genuinely nicer for hand-inspection (a spec's review beside
the spec), a per-type layout partitions naturally instead of growing one large tree, and the flat tree's
locality loss is only cheap while reviews are reached by id6 or 'aw reviews' rather than by ls. The
preference for flat was assessed at roughly 65/35, NOT strong. Reviews already span four record types
today (plans, specs, research, roadmaps), so this is not a plans-only question.

REVISIT IF: reviews become numerous AND are usually browsed per-type, or if specs gain lifecycle subdirs
(qzhfk2) - which would make a nested specs/reviews/ a non-status sibling of status dirs, i.e. the same
convention-muddying objection raised above for plans/.
