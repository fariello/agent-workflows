- Id: sq1go0
- Status: open
- Set: destshadow
- Priority: low
- Work-Kind: followup
- Summary: Decide whether an argparse dest that shadows an ancestor subparsers dest should be refused at parser build rather than only caught by a test

## Workflow history
- 2026-09-29 created (aw backlog): Carries OQ-02 of plan 8kd4eo (destshadow Order 01), which deferred the question to the maintainer.

Filed as the durable carrier for `OQ-02` of plan `8kd4eo`, which is DEFERRED to the maintainer rather than
resolved. The question, stated as the maintainer must decide it: should a leaf declaring an argument whose
`dest` collides with an ancestor subparsers action's `dest` be REFUSED AT PARSER BUILD (the way a duplicate
option string now raises, since plan `76fgt1` removed the blanket `conflict_handler="resolve"`), or is a
test-time guard sufficient?

WHY IT IS A REAL QUESTION AND NOT A TODO. A build-time refusal is a change to the PUBLIC behavior of every
`aw` invocation: it converts an author-time mistake into an import-time crash for every operator, which is
the right trade for some classes and the wrong one for others. That is a maintainer judgement about risk
appetite on a shipped surface, not something repository evidence settles.

TWO MEASURED OBSTACLES, recorded so whoever takes this does not rediscover them (both from `8kd4eo`
authoring, 2026-09-29). FIRST, ANCESTRY IS NOT AVAILABLE AT THE CALL SITE: `add_parser` builds a child that
holds no reference to the subparsers action that created it, so a refusal inside `add_argument` cannot see
its ancestors. The options are a registration wrapper that threads the ancestor dests down, or a post-build
validation pass - and the latter is just the guard test running at import time on EVERY `aw` invocation,
paying a startup cost on every command to catch a mistake that only an author can make. SECOND, THE
ANALOGOUS REFUSAL FOR THE FLAG-DEFAULT SHAPE WOULD FIRE ON 29 LIVE PAIRS in the `runs` family, so it cannot
ship before plan `zwv1sa` (destshadow Order 02) lands; revisit once the tree is clean under both rules.

PRECEDENT TO WEIGH: `zy1okf` asked the same shape of question for duplicate OPTION STRINGS and the answer was
YES, refuse at build time. Plan `76fgt1` implemented it at a measured cost of one line plus a guard, having
first established that zero live collisions existed. The same "measure first, then refuse" sequence applies
here, and the measurement is already done: `8kd4eo` F-03 records zero live instances of the subcommand-shadowing
shape.
