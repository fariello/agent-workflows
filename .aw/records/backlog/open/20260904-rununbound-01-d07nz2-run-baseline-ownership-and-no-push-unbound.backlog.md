- Id: d07nz2
- Status: open
- Blocks-Release: next
- Set: rununbound
- Priority: medium
- Work-Kind: feature
- Summary: RUN-BASELINE-OWNERSHIP and RUN-NO-PUSH land as names with no predicate; the machinery behind them is unbuilt

## Workflow history
- 2026-09-04 created (aw backlog): RUN-BASELINE-OWNERSHIP and RUN-NO-PUSH land as names with no predicate; the machinery behind them is unbuilt

PARTIALLY OBSOLETE 2026-09-08, VERIFIED IN-TREE. HALF OF THIS ITEM IS DEAD. Graduate ONLY the
`RUN-NO-PUSH` half; `RUN-BASELINE-OWNERSHIP` was BUILT after this item was written and is now BOUND.

`RUN-BASELINE-OWNERSHIP` IS BOUND, and the code says so in its own words. `run_evidence.py:1221-1223`
records: "`RUN-BASELINE-OWNERSHIP` is now BOUND, not UNBOUND-UNBUILT: the per-path lease overlap check
F3 said nobody had built ships as `worktree_lease.LeaseTable.claim` (`m2wwns`), and `dirty_within`
decides the pre-existing-dirty-path half." Verified at HEAD: `LeaseTable.claim` exists
(`worktree_lease.py:836`) and `run_evidence.dirty_within` exists (consumed by
`ipd_lifecycle.py:892-895`). The code's own tally is now "10 BOUND, 2 UNBOUND-BY-DEPENDENCY,
1 UNBOUND-UNBUILT (F3 recorded 9 / 2 / 2)" (`run_evidence.py:1231`). So this item's claim that
"nothing implements one" is FALSE at HEAD. Do not graduate it, and do not write a plan to build a
second lease-overlap check.

`RUN-NO-PUSH` SURVIVES, AND IS THE ONLY UNBOUND-UNBUILT CODE LEFT. Verified: `supports_deny_push`
defaults `False` (`host_sandbox_profile.py:204`) and is "DECLARED AND NEVER PROBED, with the reason
recorded in `probe_notes`" (`:88-95`), because it names host ENFORCEMENT that "does not exist in this
repository, so there is nothing to attempt". It fails closed, which is correct.

BUT READ THE SAME PARAGRAPH BEFORE PLANNING IT, because it forbids the obvious implementation:
"Inferring support from the presence of the driver-side `git_commit_helper.offer_commit` helper is
FORBIDDEN: a helper the driver chooses to call is not a boundary an agent cannot evade, and reporting
it as one is the same fail-OPEN inference the sandbox probes above exist to refuse." So a plan may not
bind `RUN-NO-PUSH` by detecting a helper, a config flag, or a hook's presence. It needs a real
enforcement boundary or it needs to stay honestly unbound.

CONSEQUENCE FOR THE GRADUATED PLAN'S SHAPE: this item was filed as one feature covering two codes; it
is now one code, and that code is a security-boundary design the item itself says "should not be picked
up casually" and "needs a spec-level decision first". The graduated plan is therefore a SPEC-FIRST
plan (decide what enforcement means and whether this host can offer it), not a code plan, and it must
carry the item's own prohibition on presence-based inference as a hard constraint.

`runcodes-01` (`wlxkoz`) records all 13 spec `25kzda` 4.2 `RUN-*` codes and marks each BOUND, UNBOUND-BY-DEPENDENCY, or UNBOUND-UNBUILT. Four land unbound, and two of those have NO owner anywhere in the tree:

- `RUN-BASELINE-OWNERSHIP` needs a path-lease overlap check. Nothing implements one.
- `RUN-NO-PUSH` needs host push-denial ENFORCEMENT. Nothing implements it, and this is the SAME unbuilt security boundary that `hostcap-01` (`mjx7ne`) escalated in its own OQ-03, where the maintainer ruled the capability may be declared `False` with a `probe_notes` entry rather than probed - deliberately NOT built.

The other two unbound codes DO have owners and are not part of this item: `RUN-COMMIT-CONTENTS` and `RUN-COMMIT-GATEWAY` wait on the commit trailers of `runtrail-01` (`m73aet`), and `RUN-HOST-CAPABILITY` waits on `hostcap-01` (`mjx7ne`).

WHY THIS IS FILED RATHER THAN FIXED: `wlxkoz` is deliberately a NAMING layer over predicates that already ship, and its own design rule is that a code honestly reporting itself unbound is safe while a code silently wired to a predicate that does not answer its question is a fail-OPEN checker. So leaving these two unbound is correct for that plan. What was missing is any record that the underlying machinery is owed.

HONEST STATUS: `open` rather than `blocked`, because neither is gated on a specific artifact - they need design, not a prerequisite. `RUN-NO-PUSH` in particular is a security-boundary design of `1o4eif` magnitude and should not be picked up casually; treat it as needing a spec-level decision first, and do NOT let a future plan bind either code to a presence-based inference, which is the fail-open pattern already rejected once for the host capabilities.
