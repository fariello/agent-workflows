- Id: 59t9x5
- Status: open
- Set: 59t9x5
- Priority: medium
- Work-Kind: chore
- Summary: aw find opens every record twice: the display layer re-reads the 616 records the resolver just read (~119.6ms of a ~252ms warm find, 1240 opens end to end)

## Workflow history
- 2026-09-12 created (aw backlog): aw find opens every record twice: the display layer re-reads the 616 records the resolver just read (~119.6ms of a ~252ms warm find, 1240 opens end to end)

## Where this came from

Split out of plan `826o13` (Set `findtier`) when the maintainer resolved its OQ-03 on 2026-09-11 by
DECLINING the filename candidate filter. That plan's review measured the cost decomposition and found the
plan was optimizing the wrong layer: the filter's net prize was ~12.8ms while the display layer's re-read
is ~9x that. The filter was declined; THIS is where the cost actually is, so it is filed as its own item
rather than left as prose inside a plan that no longer does the work.

## Measured at HEAD 2026-09-12

Re-measured rather than inherited from the review (which recorded ~113.6ms; it reproduces):

- `aw find plans <id6>` in-process, warm, best of 5: 252.4ms total, of which `plans_index.scan_plans` is
  119.6ms in ONE call, about 47%.
- Opens instrumented on `pathlib.Path.open` for the whole command: 1240. The resolver alone accounts for
  620. So essentially every record is opened exactly twice.
- Cold subprocess best of 5: 487.8ms, the difference being interpreter start plus `import cli` (~115ms at
  review) which this item does not address.

Do NOT cite a standalone `plans_index.scan_plans(root)` timing as the cost: measured alone it is ~880ms
because nothing else has warmed the page cache, which overstates what `find` actually pays by ~7x. Time it
INSIDE the command, as above.

## Why this is not a trivial unification, and must not be treated as one

`selectors.py:112-120` documents that the resolver and `plans_index` DELIBERATELY DISAGREE on 24 records:
`_STATUS_RE`'s single-token `(\S+)` is called a matching-behavior CONTRACT that must not be "harmonized"
without owning the change. So merging the two readers changes which record wins some queries, which is a
matching change needing sign-off, NOT a caching cleanup. Any plan graduating this item must either
preserve that disagreement or explicitly own changing it.

The safer shape to evaluate first is passing the records the resolver ALREADY read to the display layer,
rather than making the two readers agree.

## Guardrails any implementation inherits from 826o13

- `aw find` returns matching ARTIFACTS, never references: `aw find plans wtiso` returns 3 records while a
  filename glob returns 12 (`wtisoland`, `wtisodebt`, unrelated docs). 826o13's E-01 pins this; do not
  regress it while optimizing.
- Nine records carry a declared identity ABSENT from their bounded 4096-byte header, including `25kzda`,
  a spec this repository cites constantly. Any read-avoidance scheme must still find them.
