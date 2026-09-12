- Id: 59t9x5
- Status: open
- Blocks-Release: next
- Set: 59t9x5
- Priority: medium
- Work-Kind: bug
- Summary: aw find opens every record twice: the display layer re-reads the 616 records the resolver just read, costing ~128ms of a ~530ms command an operator waits on

## Workflow history
- 2026-09-12 open (aw set): Reclassified chore -> bug and GATED on the maintainer's ruling of 2026-09-12. Basis: provably redundant work is a DEFECT, not merely an inefficiency; measured 1240 opens end to end against 620 needed, i.e. every record opened about twice. THIS IS A PRECEDENT THAT WIDENS THE GATE, recorded here because it decides more than this item: a performance defect with CORRECT OUTPUT now counts as a bug and therefore blocks a release, so known inefficiencies are release blockers. It bears directly on qmgn12 OQ-02 (whether a defect filed as chore escapes the bug gate) and answers it in the direction of closing that leak. NOTE the Work-Kind field was edited by hand because 'aw backlog set' has no --work-kind setter, unlike 'aw ipd set'; filed as its own gap.
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


## Why this qualifies as a bug and not a chore (2026-09-12)

Filed `chore` on the reasoning that `aw find` returns entirely CORRECT answers, then reclassified `bug` by
the maintainer, who set the test: inefficiency that impacts the USER EXPERIENCE is a defect; inefficiency
users cannot notice is not.

IT QUALIFIES ON THE MEASUREMENT, NOT ON THE REDUNDANCY. The doubled read is evidence of waste, but what
makes it a defect is the wait it imposes on a human:

- `aw find plans <id6>` as a user runs it: best 530.2ms, median 571.5ms over 7 runs.
- `plans_index.scan_plans` inside that command: ~128ms, about 48% of the warm in-process path.
- Removing it would leave roughly 402ms of a 530ms command.

A ~128ms reduction on an interactive command is perceptible, which is what earns the gate. Stated plainly
so the precedent is not over-read: had the same double read cost 3ms, `chore` would have been correct, and
redundancy alone would not have made it a bug.

FLOOR WORTH KNOWING for anyone who works this item: `aw --version` best 220.1ms, so interpreter start plus
import is the larger fixed cost and this item cannot take `find` below it. Do not promise a fast command;
promise the removal of a redundant ~128ms.
