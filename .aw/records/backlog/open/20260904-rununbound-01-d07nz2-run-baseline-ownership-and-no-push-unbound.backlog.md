- Id: d07nz2
- Status: open
- Blocks-Release: next
- Set: rununbound
- Priority: medium
- Work-Kind: feature
- Summary: RUN-BASELINE-OWNERSHIP and RUN-NO-PUSH land as names with no predicate; the machinery behind them is unbuilt

## Workflow history
- 2026-09-04 created (aw backlog): RUN-BASELINE-OWNERSHIP and RUN-NO-PUSH land as names with no predicate; the machinery behind them is unbuilt

`runcodes-01` (`wlxkoz`) records all 13 spec `25kzda` 4.2 `RUN-*` codes and marks each BOUND, UNBOUND-BY-DEPENDENCY, or UNBOUND-UNBUILT. Four land unbound, and two of those have NO owner anywhere in the tree:

- `RUN-BASELINE-OWNERSHIP` needs a path-lease overlap check. Nothing implements one.
- `RUN-NO-PUSH` needs host push-denial ENFORCEMENT. Nothing implements it, and this is the SAME unbuilt security boundary that `hostcap-01` (`mjx7ne`) escalated in its own OQ-03, where the maintainer ruled the capability may be declared `False` with a `probe_notes` entry rather than probed - deliberately NOT built.

The other two unbound codes DO have owners and are not part of this item: `RUN-COMMIT-CONTENTS` and `RUN-COMMIT-GATEWAY` wait on the commit trailers of `runtrail-01` (`m73aet`), and `RUN-HOST-CAPABILITY` waits on `hostcap-01` (`mjx7ne`).

WHY THIS IS FILED RATHER THAN FIXED: `wlxkoz` is deliberately a NAMING layer over predicates that already ship, and its own design rule is that a code honestly reporting itself unbound is safe while a code silently wired to a predicate that does not answer its question is a fail-OPEN checker. So leaving these two unbound is correct for that plan. What was missing is any record that the underlying machinery is owed.

HONEST STATUS: `open` rather than `blocked`, because neither is gated on a specific artifact - they need design, not a prerequisite. `RUN-NO-PUSH` in particular is a security-boundary design of `1o4eif` magnitude and should not be picked up casually; treat it as needing a spec-level decision first, and do NOT let a future plan bind either code to a presence-based inference, which is the fail-open pattern already rejected once for the host capabilities.
