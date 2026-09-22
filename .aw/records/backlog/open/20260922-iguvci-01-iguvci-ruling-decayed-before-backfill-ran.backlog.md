- Id: iguvci
- Status: open
- Blocks-Release: next
- Set: iguvci
- Priority: medium
- Work-Kind: bug
- Summary: Three plans the maintainer ruled were release-blocking bugs shipped to executed/ carrying neither Work-Kind: bug nor Blocks-Release, so a recorded ruling left no trace in the corpus

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan lc4unl (planprio Order 03).

## Detail

WHAT IS WRONG. On 2026-09-12 the maintainer ruled (Ruling 2, recorded verbatim in plans `d0cbt3`,
`8u6770` and `lc4unl`) that 13 named pending plans carry specific `Priority`/`Work-Kind` values, and
(Ruling 3) that "ALL BUGS MUST BLOCK THE NEXT RELEASE". The plan that was to WRITE those values
(`lc4unl`) did not run until 2026-09-22. In the intervening ten days 12 of the 13 reached
`executed/`, where a plan is immutable by policy. The decision was therefore recorded in three
places and landed in one.

MEASURED, per id6 named by the ruling. Still live and now written: `m7gvuz` (`pending/`,
`- Status: approved`). Terminal and unwritable: `xdr83v`, `hp9rot`, `r2i1b1`, and all eleven
`runanalytics` plans (`5lxvl3`, `xbwq8n`, `bzz5e6`, `lhccjf`, `5f2h8i`, `8hald1`, `aflsz3`, `6eq3oq`,
`mm5p3v`, `ixis0c`, `9xycbh`).

THE SHARPEST CASE IS THE TWO RULED BUGS THAT SHIPPED UNGATED. `hp9rot` and `r2i1b1` were both ruled
`Work-Kind: bug`, which under Ruling 3 obliges `- Blocks-Release:`. Measured:

    $ grep -E '^- (Priority|Work-Kind|Blocks-Release):' \
        .aw/records/plans/executed/20260908-runnerbugs-01-hp9rot-*.ipd.md
    (no output)
    $ grep -E '^- (Priority|Work-Kind|Blocks-Release):' \
        .aw/records/plans/executed/20260907-orchprobe-01-r2i1b1-*.ipd.md
    (no output)

So two plans the maintainer explicitly classified as release-blocking bugs shipped carrying no
work-kind and no gate. `xdr83v` carries `- Blocks-Release: next` but no `Work-Kind` either.

WHY THIS IS A DEFECT AND NOT MERELY LATE. A ruling is only as durable as the artifact carrying it,
and here the carrier was a plan's prose rather than any enforced field, so nothing detected the decay
and nothing will detect the next one. Note what did NOT catch it: the `nobugship` rule
`check.bug-without-release-gate` fires on a LIVE `Work-Kind: bug` artifact, and these plans carry no
`Work-Kind` at all and are terminal besides, so they are invisible to it twice over. That is the
honest limit of the shipped gate (it keys on an author's classification), demonstrated on real
artifacts.

WHAT THE FIX MIGHT BE, and it is a decision rather than an obvious patch. Options: (a) accept the
loss and record it, since the affected plans are shipped and their release consequence is moot;
(b) allow a narrow, audited metadata-only amendment to a terminal plan so a recorded ruling can still
be honored, which cuts against terminal immutability and needs a spec amendment; (c) make a ruling
carry its own enforceable artifact at the moment it is recorded (for example a backlog item per
decided plan) so the decision cannot decay while a plan waits, which is the only option that prevents
recurrence rather than repairing one instance. The maintainer should choose; (c) is the one worth
designing.

WHAT ALREADY HAPPENED. `lc4unl` applied the ruling to `m7gvuz`, the single plan it could still
legitimately reach, and deferred the remaining 16 undecided plans to the maintainer rather than
self-approving a table (DEFERRED 15-lc4unl-Q1). It did NOT edit any terminal plan, and proved so.
