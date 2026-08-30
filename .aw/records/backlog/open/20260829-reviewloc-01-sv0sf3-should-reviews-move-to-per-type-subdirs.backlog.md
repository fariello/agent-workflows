- Id: sv0sf3
- Status: open
- Set: reviewloc
- Priority: medium
- Kind: chore
- Summary: Should review artifacts move from a flat .aw/records/reviews/ to per-type .aw/records/<type>/reviews/?

## Workflow history
- 2026-08-29 created (aw backlog): Should review artifacts move from a flat .aw/records/reviews/ to per-type .aw/records/<type>/reviews/?

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
